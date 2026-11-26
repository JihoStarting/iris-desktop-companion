# rea_triage bagian 25/47: disasm_a64 (baris asli 10189-10965). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.40 [A1]: disassembler AArch64 murni Python (tahap 2d-2c-2b-3b-2) -----------------------
# Dipakai `--disasm` / disasm_text untuk ELF / Mach-O / berkas mentah arm64 bila capstone TIDAK terpasang (capstone, bila ada, tetap didahulukan).
# Statis, tanpa dependensi. Himpunan umum: cabang (B / BL / B.cond / CBZ / TBZ / BR / BLR / RET / PAC), SVC / BRK, hint (NOP / PACIASP / BTI ..), barrier,
# MRS / MSR; data processing imediat (ADR / ADRP, ADD / SUB, logika bitmask, MOVZ / MOVN / MOVK, bitfield + alias, EXTR); register (logika, ADD / SUB
# bergeser dan extended, ADC / SBC, CCMP, CSEL + alias, DIV / MUL / MADD / SMULL.., geser variabel, RBIT / REV / CLZ); load / store (imm, unscaled, pra / pasca-indeks,
# register-offset, literal, pair, exclusive / acquire-release, CAS, atomik LSE) untuk register umum + FP / SIMD skalar (b h s d q); FP skalar (FADD.., FCMP, FCVT,
# SCVTF / FCVTZS, FMOV, FMADD, FCSEL). Sisanya `.word` (NEON vektor, SVE, fmov imediat, fixed-point, PAC data, CRC, MTE, sistem lain).
# Format keluaran meniru capstone. BELUM dibandingkan dengan capstone pada sampel acak (jalankan test_a64_vs_capstone.py di mesin yang punya capstone).

_A64_CC = ("eq", "ne", "hs", "lo", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al", "nv")
_A64_SH = ("lsl", "lsr", "asr", "ror")
_A64_EXT = ("uxtb", "uxth", "uxtw", "uxtx", "sxtb", "sxth", "sxtw", "sxtx")
_A64_BAR = {1: "oshld", 2: "oshst", 3: "osh", 5: "nshld", 6: "nshst", 7: "nsh", 9: "ishld", 10: "ishst", 11: "ish", 13: "ld", 14: "st", 15: "sy"}
_A64_HINT = {0: "nop", 1: "yield", 2: "wfe", 3: "wfi", 4: "sev", 5: "sevl", 7: "xpaclri", 24: "paciaz", 25: "paciasp", 26: "pacibz", 27: "pacibsp",
             28: "autiaz", 29: "autiasp", 30: "autibz", 31: "autibsp", 32: "bti", 34: "bti c", 36: "bti j", 38: "bti jc"}
_A64_SYSREG = {(3, 3, 13, 0, 2): "tpidr_el0", (3, 3, 13, 0, 3): "tpidrro_el0", (3, 3, 4, 2, 0): "nzcv", (3, 3, 4, 2, 1): "daif", (3, 3, 4, 4, 0): "fpcr",
               (3, 3, 4, 4, 1): "fpsr", (3, 3, 14, 0, 2): "cntvct_el0", (3, 3, 14, 0, 0): "cntfrq_el0", (3, 0, 0, 0, 0): "midr_el1", (3, 0, 4, 2, 2): "currentel",
               (3, 0, 13, 0, 4): "tpidr_el1", (3, 0, 0, 0, 5): "mpidr_el1", (3, 3, 0, 0, 1): "ctr_el0", (3, 3, 0, 0, 7): "dczid_el0"}
_A64_M64 = 0xFFFFFFFFFFFFFFFF


def _a64_r(n: int, sf: int, sp: bool = False) -> str:
    if n == 31:
        return ("sp" if sf else "wsp") if sp else ("xzr" if sf else "wzr")
    return ("x%d" if sf else "w%d") % n


def _a64_bitmask_dis(sf: int, N: int, immr: int, imms: int):
    """DecodeBitMasks (imediat logika) -> nilai atau None bila tak sah."""
    if sf == 0 and N == 1:
        return None
    comb = (N << 6) | ((~imms) & 0x3F)
    if comb == 0:
        return None
    ln = comb.bit_length() - 1
    if ln < 1:
        return None
    esz = 1 << ln
    lev = esz - 1
    S, R = imms & lev, immr & lev
    if S == lev:
        return None
    el = (1 << (S + 1)) - 1
    el = ((el >> R) | (el << (esz - R))) & ((1 << esz) - 1)
    out = 0
    for i in range(0, 64 if sf else 32, esz):
        out |= el << i
    return out


def _a64_sx(v: int, bits: int) -> int:
    return v - (1 << bits) if v >> (bits - 1) else v


def _a64_tgt(t: int) -> str:
    return "#0x%x" % (t & _A64_M64)


def _a64_mem(rn: int, off: int, mode: str = "off", show0: bool = False) -> str:
    b = _a64_r(rn, 1, True)
    if mode == "post":
        return "[%s], %s" % (b, _a32_simm(off))
    if mode == "pre":
        return "[%s, %s]!" % (b, _a32_simm(off))
    return "[%s, %s]" % (b, _a32_simm(off)) if (off or show0) else "[%s]" % b


def _a64_prf(n: int) -> str:
    t, g, p = (n >> 3) & 3, (n >> 1) & 3, n & 1
    if t < 3 and g < 3:
        return "p%s%s%s" % (("ld", "li", "st")[t], "l%d" % (g + 1), ("keep", "strm")[p])
    return "#%d" % n


def _a64_ldst_class(size: int, V: int, opc: int, unscaled: bool):
    """(mnemonik, huruf register / sf, skala, jenis) atau None. jenis: 'g' umum, 'f' FP / SIMD, 'p' prefetch."""
    u = "u" if unscaled else ""
    if V:
        if opc in (0, 1):
            st = opc == 0
            reg = "bhsd"[size]
            sc = size
        elif size == 0:
            st = opc == 2
            reg, sc = "q", 4
        else:
            return None
        return (("st" if st else "ld") + ("ur" if unscaled else "r"), reg, sc, "f")
    if size == 3 and opc == 2:
        return ("prfum" if unscaled else "prfm", "x", 3, "p")
    sfx = ("b", "h", "", "")[size]
    if opc == 0:
        return ("st" + ("ur" if unscaled else "r") + sfx, "x" if size == 3 else "w", size, "g")
    if opc == 1:
        return ("ld" + ("ur" if unscaled else "r") + sfx, "x" if size == 3 else "w", size, "g")
    if size == 3 or (opc == 3 and size == 2):
        return None
    if size == 2:
        return ("ld" + ("ur" if unscaled else "r") + "sw", "x", 2, "g")
    return ("ld" + ("ur" if unscaled else "r") + "s" + sfx, "x" if opc == 2 else "w", size, "g")


def _a64_rt(n: int, kind: str) -> str:
    if kind in ("x", "w"):
        return _a64_r(n, 1 if kind == "x" else 0)
    return "%s%d" % (kind, n)


def _a64_dis(w: int, pc: int):
    """Satu kata AArch64 -> (mnemonik, operand, target). Target = alamat percabangan langsung (atau None). Tak dikenal -> ('.word', '0x...', None)."""
    bad = (".word", "0x%08x" % w, None)
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    sf = (w >> 31) & 1
    R = _a64_r
    top = w & 0x1C000000
    # ---------------------------------------------------------------- cabang / sistem
    if top == 0x14000000:
        if (w & 0x7C000000) == 0x14000000:                                     # B / BL
            t = (pc + _a64_sx(w & 0x3FFFFFF, 26) * 4) & _A64_M64
            return ("bl" if sf else "b"), _a64_tgt(t), t
        if (w & 0x7E000000) == 0x34000000:                                     # CBZ / CBNZ
            t = (pc + _a64_sx((w >> 5) & 0x7FFFF, 19) * 4) & _A64_M64
            return ("cbnz" if (w >> 24) & 1 else "cbz"), "%s, %s" % (R(rd, sf), _a64_tgt(t)), t
        if (w & 0x7E000000) == 0x36000000:                                     # TBZ / TBNZ
            bit = (sf << 5) | ((w >> 19) & 31)
            t = (pc + _a64_sx((w >> 5) & 0x3FFF, 14) * 4) & _A64_M64
            return ("tbnz" if (w >> 24) & 1 else "tbz"), "%s, %s, %s" % (R(rd, sf), _a32_imm(bit), _a64_tgt(t)), t
        if (w & 0xFF000010) == 0x54000000:                                     # B.cond
            t = (pc + _a64_sx((w >> 5) & 0x7FFFF, 19) * 4) & _A64_M64
            return "b." + _A64_CC[w & 15], _a64_tgt(t), t
        if (w & 0xFF000000) == 0xD4000000:                                     # SVC / HVC / SMC / BRK / HLT
            opc, ll, i16 = (w >> 21) & 7, w & 3, (w >> 5) & 0xFFFF
            if (w >> 2) & 7:
                return bad
            nm = {(0, 1): "svc", (0, 2): "hvc", (0, 3): "smc", (1, 0): "brk", (2, 0): "hlt"}.get((opc, ll))
            return (nm, _a32_imm(i16), None) if nm else bad
        if (w & 0xFFFFF01F) == 0xD503201F:                                     # hint
            h = (w >> 5) & 0x7F
            return (_A64_HINT[h], "", None) if h in _A64_HINT else ("hint", _a32_imm(h), None)
        if (w & 0xFFFFF01F) == 0xD503301F:                                     # clrex / dsb / dmb / isb
            crm, op2 = (w >> 8) & 15, (w >> 5) & 7
            if op2 == 2:
                return "clrex", ("" if crm == 15 else _a32_imm(crm)), None
            if op2 == 6:
                return "isb", ("" if crm == 15 else _a32_imm(crm)), None
            if op2 in (4, 5):
                return ("dsb" if op2 == 4 else "dmb"), (_A64_BAR.get(crm) or _a32_imm(crm)) if crm != 0 else "#0", None
            return bad
        if (w & 0xFFF00000) in (0xD5300000, 0xD5100000):                       # MRS / MSR (register)
            key = (2 + ((w >> 19) & 1), (w >> 16) & 7, (w >> 12) & 15, (w >> 8) & 15, (w >> 5) & 7)
            nm = _A64_SYSREG.get(key) or "s%d_%d_c%d_c%d_%d" % key
            if (w >> 21) & 1:
                return "mrs", "%s, %s" % (R(rd, 1), nm), None
            return "msr", "%s, %s" % (nm, R(rd, 1)), None
        if (w & 0xFE000000) == 0xD6000000:                                     # BR / BLR / RET / ERET / PAC
            opc, op2, op3, op4 = (w >> 21) & 15, (w >> 16) & 31, (w >> 10) & 63, w & 31
            if op2 != 31:
                return bad
            if op3 == 0 and op4 == 0 and opc in (0, 1, 2):
                if opc == 2:
                    return "ret", ("" if rn == 30 else R(rn, 1)), None
                return ("br", "blr")[opc], R(rn, 1), None
            if op3 == 0 and op4 == 0 and opc == 4 and rn == 31:
                return "eret", "", None
            if op3 in (2, 3):
                k = "a" if op3 == 2 else "b"
                if opc == 2 and rn == 31 and op4 == 31:
                    return "ret" + "a" + k, "", None
                if opc == 4 and rn == 31 and op4 == 31:
                    return "ereta" + k, "", None
                if opc in (0, 1) and op4 == 31:
                    return ("br", "blr")[opc] + "a" + k + "z", R(rn, 1), None
                if opc in (8, 9):
                    return ("br", "blr")[opc - 8] + "a" + k, "%s, %s" % (R(rn, 1), R(op4, 1, True)), None
            return bad
        return bad
    # ---------------------------------------------------------------- data processing imediat
    if top == 0x10000000:
        if (w & 0x1F000000) == 0x10000000:                                     # ADR / ADRP
            imm = _a64_sx((((w >> 5) & 0x7FFFF) << 2) | ((w >> 29) & 3), 21)
            if sf:
                t = (((pc & ~0xFFF) + (imm << 12))) & _A64_M64
                return "adrp", "%s, %s" % (R(rd, 1), _a64_tgt(t)), None
            t = (pc + imm) & _A64_M64
            return "adr", "%s, %s" % (R(rd, 1), _a64_tgt(t)), None
        if (w & 0x1F000000) == 0x11000000:                                     # ADD / SUB imediat
            op, S, sh, imm = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 10) & 0xFFF
            if sh > 1:
                return bad
            if not op and not S and not sh and not imm and (rd == 31 or rn == 31):
                return "mov", "%s, %s" % (R(rd, sf, True), R(rn, sf, True)), None
            im = _a32_imm(imm) + (", lsl #12" if sh else "")
            if S and rd == 31:
                return ("cmp" if op else "cmn"), "%s, %s" % (R(rn, sf, True), im), None
            return ("sub" if op else "add") + ("s" if S else ""), "%s, %s, %s" % (R(rd, sf, not S), R(rn, sf, True), im), None
        if (w & 0x1F800000) == 0x12000000:                                     # AND / ORR / EOR / ANDS imediat
            opc = (w >> 29) & 3
            v = _a64_bitmask_dis(sf, (w >> 22) & 1, (w >> 16) & 0x3F, (w >> 10) & 0x3F)
            if v is None:
                return bad
            if opc == 3 and rd == 31:
                return "tst", "%s, %s" % (R(rn, sf), _a32_imm(v)), None
            if opc == 1 and rn == 31:
                return "mov", "%s, %s" % (R(rd, sf, True), _a32_imm(v)), None
            return ("and", "orr", "eor", "ands")[opc], "%s, %s, %s" % (R(rd, sf, opc != 3), R(rn, sf), _a32_imm(v)), None
        if (w & 0x1F800000) == 0x12800000:                                     # MOVN / MOVZ / MOVK
            opc, hw, i16 = (w >> 29) & 3, (w >> 21) & 3, (w >> 5) & 0xFFFF
            if opc == 1 or (not sf and hw > 1):
                return bad
            sh = 16 * hw
            mask = _A64_M64 if sf else 0xFFFFFFFF
            if opc == 3:
                return "movk", "%s, %s%s" % (R(rd, sf), _a32_imm(i16), (", lsl #%d" % sh) if sh else ""), None
            if i16 == 0 and hw:
                return ("movn" if opc == 0 else "movz"), "%s, #0, lsl #%d" % (R(rd, sf), sh), None
            v = ((i16 << sh) if opc == 2 else ~(i16 << sh)) & mask
            if opc == 0:
                v = _a64_sx(v, 64 if sf else 32)
                return "mov", "%s, %s" % (R(rd, sf), _a32_simm(v)), None
            return "mov", "%s, %s" % (R(rd, sf), _a32_imm(v)), None
        if (w & 0x1F800000) == 0x13000000:                                     # SBFM / BFM / UBFM
            opc, N, immr, imms = (w >> 29) & 3, (w >> 22) & 1, (w >> 16) & 0x3F, (w >> 10) & 0x3F
            sz = 64 if sf else 32
            if opc == 3 or N != sf or immr >= sz or imms >= sz:
                return bad
            if opc == 0:                                                       # SBFM
                if immr == 0 and imms in (7, 15):
                    return ("sxtb" if imms == 7 else "sxth"), "%s, %s" % (R(rd, sf), R(rn, 0)), None
                if immr == 0 and imms == 31 and sf:
                    return "sxtw", "%s, %s" % (R(rd, 1), R(rn, 0)), None
                if imms == sz - 1:
                    return "asr", "%s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(immr)), None
                if imms >= immr:
                    return "sbfx", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(immr), _a32_imm(imms - immr + 1)), None
                return "sbfiz", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(sz - immr), _a32_imm(imms + 1)), None
            if opc == 2:                                                       # UBFM
                if not sf and immr == 0 and imms in (7, 15):
                    return ("uxtb" if imms == 7 else "uxth"), "%s, %s" % (R(rd, 0), R(rn, 0)), None
                if imms == sz - 1:
                    return "lsr", "%s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(immr)), None
                if imms + 1 == immr:
                    return "lsl", "%s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(sz - 1 - imms)), None
                if imms >= immr:
                    return "ubfx", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(immr), _a32_imm(imms - immr + 1)), None
                return "ubfiz", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(sz - immr), _a32_imm(imms + 1)), None
            if imms >= immr:                                                   # BFM
                return "bfxil", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(immr), _a32_imm(imms - immr + 1)), None
            if rn == 31:
                return "bfc", "%s, %s, %s" % (R(rd, sf), _a32_imm(sz - immr), _a32_imm(imms + 1)), None
            return "bfi", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(sz - immr), _a32_imm(imms + 1)), None
        if (w & 0x1F800000) == 0x13800000:                                     # EXTR
            imms = (w >> 10) & 0x3F
            if ((w >> 29) & 3) or ((w >> 21) & 1) or ((w >> 22) & 1) != sf or (not sf and imms > 31):
                return bad
            if rn == rm:
                return "ror", "%s, %s, %s" % (R(rd, sf), R(rn, sf), _a32_imm(imms)), None
            return "extr", "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf), _a32_imm(imms)), None
        return bad
    # ---------------------------------------------------------------- load / store
    if (w & 0xBE000000) == 0x0C000000:                                         # v99.59: ld1..ld4 / st1..st4 (struktur Advanced SIMD)
        return _a64_neon(w) or bad
    if (w & 0x0A000000) == 0x08000000:
        return _a64_ldst(w, pc, bad)
    # ---------------------------------------------------------------- data processing register
    if (w & 0x0E000000) == 0x0A000000:
        return _a64_dpreg(w, bad)
    # ---------------------------------------------------------------- FP skalar
    if (w & 0x9E000000) == 0x0E000000 or (w & 0xDE000000) == 0x5E000000 or (w & 0xFF000000) == 0xCE000000:         # v99.59: Advanced SIMD vektor + AES / SHA
        return _a64_neon(w) or bad
    if (w & 0x0E000000) == 0x0E000000:
        return _a64_fp(w, bad)
    return bad


def _a64_ldst(w: int, pc: int, bad):
    rt, rn = w & 31, (w >> 5) & 31
    size, V = (w >> 30) & 3, (w >> 26) & 1
    if (w & 0x3F000000) == 0x08000000:                                         # exclusive / acquire-release / CAS
        o2, L, o1, o0 = (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 15) & 1
        rs, rt2 = (w >> 16) & 31, (w >> 10) & 31
        sfx = ("b", "h", "", "")[size]
        sf = 1 if size == 3 else 0
        mem = "[%s]" % _a64_r(rn, 1, True)
        if not o2 and not o1:
            if L:
                if rs != 31 or rt2 != 31:
                    return bad
                return ("ldaxr" if o0 else "ldxr") + sfx, "%s, %s" % (_a64_r(rt, sf), mem), None
            if rt2 != 31:
                return bad
            return ("stlxr" if o0 else "stxr") + sfx, "%s, %s, %s" % (_a64_r(rs, 0), _a64_r(rt, sf), mem), None
        if not o2 and o1:
            if size < 2:
                return bad
            if L:
                if rs != 31 or rt == rt2:                                      # Rt == Rt2: UNPREDICTABLE (v99.58)
                    return bad
                return ("ldaxp" if o0 else "ldxp"), "%s, %s, %s" % (_a64_r(rt, sf), _a64_r(rt2, sf), mem), None
            return ("stlxp" if o0 else "stxp"), "%s, %s, %s, %s" % (_a64_r(rs, 0), _a64_r(rt, sf), _a64_r(rt2, sf), mem), None
        if o2 and not o1:
            if rs != 31 or rt2 != 31:
                return bad
            nm = (("ldar" if o0 else "ldlar") if L else ("stlr" if o0 else "stllr")) + sfx
            return nm, "%s, %s" % (_a64_r(rt, sf), mem), None
        if rt2 != 31:                                                          # CAS
            return bad
        return "cas" + ("a" if L else "") + ("l" if o0 else "") + sfx, "%s, %s, %s" % (_a64_r(rs, sf), _a64_r(rt, sf), mem), None
    if (w & 0x3B000000) == 0x18000000:                                         # LDR literal
        opc = (w >> 30) & 3
        t = (pc + _a64_sx((w >> 5) & 0x7FFFF, 19) * 4) & _A64_M64
        if V:
            if opc == 3:
                return bad
            return "ldr", "%s, %s" % ("%s%d" % ("sdq"[opc], rt), _a64_tgt(t)), None
        if opc == 3:
            return "prfm", "%s, %s" % (_a64_prf(rt), _a64_tgt(t)), None
        return ("ldr", "ldr", "ldrsw")[opc], "%s, %s" % (_a64_r(rt, 0 if opc == 0 else 1), _a64_tgt(t)), None
    if (w & 0x3A000000) == 0x28000000:                                         # LDP / STP / LDNP / STNP / LDPSW
        opc, idx, L = (w >> 30) & 3, (w >> 23) & 3, (w >> 22) & 1
        rt2 = (w >> 10) & 31
        imm = _a64_sx((w >> 15) & 0x7F, 7)
        if V:
            if opc == 3:
                return bad
            kind, sc = "sdq"[opc], 2 + opc
        else:
            if opc == 3 or (opc == 1 and (not L or idx == 0)):
                return bad
            kind, sc = ("w", "x", "x")[opc], 3 if opc == 2 else 2
            if opc == 1:
                kind = "x"
        if L and rt == rt2:                                                    # load pair Rt == Rt2: UNPREDICTABLE (v99.58)
            return bad
        if idx in (1, 3) and not V and rn != 31 and rn in (rt, rt2):          # writeback dengan Rn == Rt / Rt2 (v99.58)
            return bad
        nm = ("ldp" if L else "stp") if idx else ("ldnp" if L else "stnp")
        if opc == 1 and not V:
            nm = "ldpsw"
        off = imm << sc
        mode = {0: "off", 1: "post", 2: "off", 3: "pre"}[idx]
        return nm, "%s, %s, %s" % (_a64_rt(rt, kind), _a64_rt(rt2, kind), _a64_mem(rn, off, mode)), None
    if (w & 0x3B000000) not in (0x38000000, 0x39000000):
        return bad
    opc = (w >> 22) & 3
    if (w & 0x3B000000) == 0x39000000:                                         # unsigned offset
        c = _a64_ldst_class(size, V, opc, False)
        if not c:
            return bad
        nm, kind, sc, jn = c
        off = ((w >> 10) & 0xFFF) << sc
        if jn == "p":
            return nm, "%s, %s" % (_a64_prf(rt), _a64_mem(rn, off)), None
        return nm, "%s, %s" % (_a64_rt(rt, kind), _a64_mem(rn, off)), None
    b21, b1110 = (w >> 21) & 1, (w >> 10) & 3
    if b21 and b1110 == 2:                                                     # register offset
        c = _a64_ldst_class(size, V, opc, False)
        if not c:
            return bad
        nm, kind, sc, jn = c
        opt, S = (w >> 13) & 7, (w >> 12) & 1
        if opt not in (2, 3, 6, 7):
            return bad
        idxr = _a64_r(rm := (w >> 16) & 31, opt & 1)
        base = _a64_r(rn, 1, True)
        if opt == 3:
            ex = (", lsl #%d" % sc) if S else ""
        else:
            ex = ", %s" % _A64_EXT[opt] + ((" #%d" % sc) if S else "")
        tgt = _a64_prf(rt) if jn == "p" else _a64_rt(rt, kind)
        return nm, "%s, [%s, %s%s]" % (tgt, base, idxr, ex), None
    if b21 and b1110 == 0:                                                     # atomik LSE
        if V:
            return bad
        A, Rr, o3, op3 = (w >> 23) & 1, (w >> 22) & 1, (w >> 15) & 1, (w >> 12) & 7
        sfx = ("b", "h", "", "")[size]
        sfv = 1 if size == 3 else 0
        al = ("a" if A else "") + ("l" if Rr else "")
        rs_ = (w >> 16) & 31
        mem = "[%s]" % _a64_r(rn, 1, True)
        if o3:
            if op3 != 0:
                return bad
            return "swp" + al + sfx, "%s, %s, %s" % (_a64_r(rs_, sfv), _a64_r(rt, sfv), mem), None
        ops = ("add", "clr", "eor", "set", "smax", "smin", "umax", "umin")
        if rt == 31 and not A:
            return "st" + ops[op3] + ("l" if Rr else "") + sfx, "%s, %s" % (_a64_r(rs_, sfv), mem), None
        return "ld" + ops[op3] + al + sfx, "%s, %s, %s" % (_a64_r(rs_, sfv), _a64_r(rt, sfv), mem), None
    if b21:
        return bad
    imm = _a64_sx((w >> 12) & 0x1FF, 9)
    if b1110 == 0:                                                             # unscaled
        c = _a64_ldst_class(size, V, opc, True)
        if not c:
            return bad
        nm, kind, sc, jn = c
        tgt = _a64_prf(rt) if jn == "p" else _a64_rt(rt, kind)
        return nm, "%s, %s" % (tgt, _a64_mem(rn, imm)), None
    if b1110 == 2:                                                             # nonprivilegiado: ldtr / sttr (v99.58; sebelumnya salah dibaca pra-indeks)
        c = _a64_ldst_class(size, V, opc, True)
        if V or not c or c[3] == "p":
            return bad
        nm, kind, sc, jn = c
        return nm.replace("ur", "tr", 1), "%s, %s" % (_a64_rt(rt, kind), _a64_mem(rn, imm)), None
    c = _a64_ldst_class(size, V, opc, False)
    if not c or c[3] == "p":
        return bad
    if not V and rn == rt and rn != 31:                                        # writeback dengan Rn == Rt: UNPREDICTABLE (v99.58)
        return bad
    nm, kind, sc, jn = c
    return nm, "%s, %s" % (_a64_rt(rt, kind), _a64_mem(rn, imm, "post" if b1110 == 1 else "pre")), None


def _a64_shifted(w: int, sf: int):
    sh, n = (w >> 22) & 3, (w >> 10) & 0x3F
    if not sf and n > 31:
        return None
    return "" if (sh == 0 and n == 0) else ", %s %s" % (_A64_SH[sh], _a32_imm(n))


def _a64_dpreg(w: int, bad):
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    sf = (w >> 31) & 1
    R = _a64_r
    if (w & 0x1F000000) == 0x0A000000:                                         # logika bergeser
        opc, N = (w >> 29) & 3, (w >> 21) & 1
        sh = _a64_shifted(w, sf)
        if sh is None:
            return bad
        if opc == 1 and not N and rn == 31 and not sh:
            return "mov", "%s, %s" % (R(rd, sf), R(rm, sf)), None
        if opc == 1 and N and rn == 31:
            return "mvn", "%s, %s%s" % (R(rd, sf), R(rm, sf), sh), None
        if opc == 3 and not N and rd == 31:
            return "tst", "%s, %s%s" % (R(rn, sf), R(rm, sf), sh), None
        nm = (("and", "bic"), ("orr", "orn"), ("eor", "eon"), ("ands", "bics"))[opc][N]
        return nm, "%s, %s, %s%s" % (R(rd, sf), R(rn, sf), R(rm, sf), sh), None
    if (w & 0x1F200000) == 0x0B000000:                                         # ADD / SUB bergeser
        op, S = (w >> 30) & 1, (w >> 29) & 1
        if (w >> 22) & 3 == 3:
            return bad
        sh = _a64_shifted(w, sf)
        if sh is None:
            return bad
        if S and rd == 31:
            return ("cmp" if op else "cmn"), "%s, %s%s" % (R(rn, sf), R(rm, sf), sh), None
        if op and rn == 31:
            return "neg" + ("s" if S else ""), "%s, %s%s" % (R(rd, sf), R(rm, sf), sh), None
        return ("sub" if op else "add") + ("s" if S else ""), "%s, %s, %s%s" % (R(rd, sf), R(rn, sf), R(rm, sf), sh), None
    if (w & 0x1F200000) == 0x0B200000:                                         # ADD / SUB extended
        op, S, opt, i3 = (w >> 30) & 1, (w >> 29) & 1, (w >> 13) & 7, (w >> 10) & 7
        if ((w >> 22) & 3) or i3 > 4:
            return bad
        rmr = R(rm, 1 if (sf and opt in (3, 7)) else 0)                      # sf=0: Rm selalu W (v99.58)
        if (rn == 31 or (rd == 31 and not S)) and opt == (3 if sf else 2):
            ex = (", lsl %s" % _a32_imm(i3)) if i3 else ""
        else:
            ex = ", %s" % _A64_EXT[opt] + ((" %s" % _a32_imm(i3)) if i3 else "")
        if S and rd == 31:
            return ("cmp" if op else "cmn"), "%s, %s%s" % (R(rn, sf, True), rmr, ex), None
        return ("sub" if op else "add") + ("s" if S else ""), "%s, %s, %s%s" % (R(rd, sf, not S), R(rn, sf, True), rmr, ex), None
    if (w & 0x1FE0FC00) == 0x1A000000:                                         # ADC / SBC
        op, S = (w >> 30) & 1, (w >> 29) & 1
        if op and rn == 31:
            return "ngc" + ("s" if S else ""), "%s, %s" % (R(rd, sf), R(rm, sf)), None
        return ("sbc" if op else "adc") + ("s" if S else ""), "%s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf)), None
    if (w & 0x1FE00410) == 0x1A400000 and (w >> 29) & 1:                       # CCMP / CCMN
        nm = "ccmp" if (w >> 30) & 1 else "ccmn"
        src = _a32_imm(rm) if (w >> 11) & 1 else R(rm, sf)
        return nm, "%s, %s, %s, %s" % (R(rn, sf), src, _a32_imm(w & 15), _A64_CC[(w >> 12) & 15]), None
    if (w & 0x1FE00800) == 0x1A800000 and not (w >> 29) & 1:                   # CSEL / CSINC / CSINV / CSNEG
        op, o2, cond = (w >> 30) & 1, (w >> 10) & 1, (w >> 12) & 15
        nm = (("csel", "csinc"), ("csinv", "csneg"))[op][o2]
        if cond < 14 and nm != "csel":
            inv = _A64_CC[cond ^ 1]
            if nm == "csinc" and rn == 31 and rm == 31:
                return "cset", "%s, %s" % (R(rd, sf), inv), None
            if nm == "csinv" and rn == 31 and rm == 31:
                return "csetm", "%s, %s" % (R(rd, sf), inv), None
            if rn == rm and rn != 31:
                return {"csinc": "cinc", "csinv": "cinv", "csneg": "cneg"}[nm], "%s, %s, %s" % (R(rd, sf), R(rn, sf), inv), None
        return nm, "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf), _A64_CC[cond]), None
    if (w & 0x1F000000) == 0x1B000000:                                         # MADD / MSUB / SMADDL / UMULH ..
        o0, op31, ra = (w >> 15) & 1, (w >> 21) & 7, (w >> 10) & 31
        if (w >> 29) & 3:
            return bad
        if op31 == 0:
            if ra == 31:
                return ("mneg" if o0 else "mul"), "%s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf)), None
            return ("msub" if o0 else "madd"), "%s, %s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf), R(ra, sf)), None
        if not sf:
            return bad
        if op31 in (1, 5):
            u = "u" if op31 == 5 else "s"
            if ra == 31:
                return u + ("mnegl" if o0 else "mull"), "%s, %s, %s" % (R(rd, 1), R(rn, 0), R(rm, 0)), None
            return u + ("msubl" if o0 else "maddl"), "%s, %s, %s, %s" % (R(rd, 1), R(rn, 0), R(rm, 0), R(ra, 1)), None
        if op31 in (2, 6) and not o0 and ra == 31:
            return ("smulh" if op31 == 2 else "umulh"), "%s, %s, %s" % (R(rd, 1), R(rn, 1), R(rm, 1)), None
        return bad
    if (w & 0x5FE00000) == 0x1AC00000 and not (w >> 29) & 1:                  # DIV / geser variabel
        opc = (w >> 10) & 0x3F
        nm = {2: "udiv", 3: "sdiv", 8: "lsl", 9: "lsr", 10: "asr", 11: "ror"}.get(opc)
        return (nm, "%s, %s, %s" % (R(rd, sf), R(rn, sf), R(rm, sf)), None) if nm else bad
    if (w & 0x5FE00000) == 0x5AC00000 and not (w >> 29) & 1 and rm == 0:      # RBIT / REV / CLZ / CLS
        opc = (w >> 10) & 0x3F
        if opc == 0:
            nm = "rbit"
        elif opc == 1:
            nm = "rev16"
        elif opc == 2:
            nm = "rev32" if sf else "rev"
        elif opc == 3 and sf:
            nm = "rev"
        elif opc == 4:
            nm = "clz"
        elif opc == 5:
            nm = "cls"
        else:
            return bad
        return nm, "%s, %s" % (R(rd, sf), R(rn, sf)), None
    return bad


_A64_FPL = ("s", "d", None, "h")


def _a64_fp(w: int, bad):
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    ft = (w >> 22) & 3
    if (w & 0xFF000000) == 0x1F000000:                                         # FMADD / FMSUB / FNMADD / FNMSUB
        L = _A64_FPL[ft]
        if not L:
            return bad
        o1, o0, ra = (w >> 21) & 1, (w >> 15) & 1, (w >> 10) & 31
        nm = (("fmadd", "fmsub"), ("fnmadd", "fnmsub"))[o1][o0]
        return nm, "%s%d, %s%d, %s%d, %s%d" % (L, rd, L, rn, L, rm, L, ra), None
    if (w & 0x7F200000) != 0x1E200000:
        return bad
    L = _A64_FPL[ft]
    if (w & 0x7F20FC00) == 0x1E200000:                                         # FP <-> integer
        sf = (w >> 31) & 1
        rmode, opc = (w >> 19) & 3, (w >> 16) & 7
        if not L:
            return bad
        fr, gr = "%s%d" % (L, rn), _a64_r(rd, sf)
        if rmode == 0 and opc in (2, 3):
            return ("scvtf" if opc == 2 else "ucvtf"), "%s%d, %s" % (L, rd, _a64_r(rn, sf)), None
        if rmode == 0 and opc in (0, 1, 4, 5):
            return ("fcvtns", "fcvtnu", None, None, "fcvtas", "fcvtau")[opc], "%s, %s" % (gr, fr), None
        if rmode == 0 and opc in (6, 7):
            if (L == "s" and sf) or (L == "d" and not sf) or L == "h":
                return bad
            if opc == 6:
                return "fmov", "%s, %s" % (gr, fr), None
            return "fmov", "%s%d, %s" % (L, rd, _a64_r(rn, sf)), None
        if opc in (0, 1) and rmode in (1, 2, 3):
            nm = {1: ("fcvtps", "fcvtpu"), 2: ("fcvtms", "fcvtmu"), 3: ("fcvtzs", "fcvtzu")}[rmode][opc]
            return nm, "%s, %s" % (gr, fr), None
        return bad
    if not L:
        return bad
    if (w & 0xFF20FC07) == 0x1E202000:                                         # FCMP / FCMPE
        o = (w >> 3) & 3
        nm = "fcmpe" if o & 2 else "fcmp"
        if o & 1:
            return (nm, "%s%d, #0.0" % (L, rn), None) if rm == 0 else bad
        return nm, "%s%d, %s%d" % (L, rn, L, rm), None
    if (w & 0xFF200C00) == 0x1E200C00:                                         # FCSEL
        return "fcsel", "%s%d, %s%d, %s%d, %s" % (L, rd, L, rn, L, rm, _A64_CC[(w >> 12) & 15]), None
    if (w & 0xFF200C00) == 0x1E200800:                                         # 2 sumber
        nm = ("fmul", "fdiv", "fadd", "fsub", "fmax", "fmin", "fmaxnm", "fminnm", "fnmul")
        o = (w >> 12) & 15
        if o >= len(nm):
            return bad
        return nm[o], "%s%d, %s%d, %s%d" % (L, rd, L, rn, L, rm), None
    if (w & 0xFF207C00) == 0x1E204000:                                         # 1 sumber
        o = (w >> 15) & 0x3F
        if o in (4, 5, 7):
            dst = {4: "s", 5: "d", 7: "h"}[o]
            return (("fcvt", "%s%d, %s%d" % (dst, rd, L, rn), None) if dst != L else bad)
        nm = {0: "fmov", 1: "fabs", 2: "fneg", 3: "fsqrt", 8: "frintn", 9: "frintp", 10: "frintm", 11: "frintz", 12: "frinta", 14: "frintx", 15: "frinti"}.get(o)
        return (nm, "%s%d, %s%d" % (L, rd, L, rn), None) if nm else bad
    return bad


def _a64_disasm_lines(code: bytes, va: int, count: int, names: dict | None = None, read32=None) -> list[str]:
    """Baris disassembly AArch64 (alamat, hex, mnemonik, operand, catatan nama / literal)."""
    names = names or {}
    out = []
    for i in range(0, min(len(code) // 4, count) * 4, 4):
        w = struct.unpack_from("<I", code, i)[0]
        pc = va + i
        m, o, t = _a64_dis(w, pc)
        note = ""
        if t is not None:
            note = names.get(t, "")
        elif (w & 0x3B000000) == 0x18000000 and m != ".word":                  # literal pool
            lit = (pc + _a64_sx((w >> 5) & 0x7FFFF, 19) * 4) & _A64_M64
            v = read32(lit) if read32 else None
            note = names.get(lit) or (("=0x%x" % v) if v is not None else "")
        out.append("   %08X  %-24s %s %s%s" % (pc, code[i:i + 4].hex(" "), m, o, ("   ; " + note) if note else ""))
    return out



def _disasm_generic(d: bytes, at, count: int, arch, was_pe: bool = False) -> str:
    """Disassembly di luar RE Lab PE: ELF, Mach-O, atau berkas mentah (alamat 'at' = offset berkas)."""
    fmt, entry, segs, a = "mentah", 0, [], None
    mp = None
    try:
        mp = _gen_elf_map(d) or _gen_macho_map(d)
    except (struct.error, IndexError):
        mp = None
    if mp:
        a, entry, segs, fmt = mp
    elif was_pe:
        fmt = "PE (bukan x86 / x64)"
    a = (str(arch).lower().strip() if arch else None) or a or "x64"
    if a not in _CS_ARCHS:
        return "DISASM gagal: arsitektur '%s' belum didukung. Pilihan: %s" % (_clean(a)[:20], " ".join(sorted(_CS_ARCHS)))
    s = str(at).strip().lower()
    note_raw = ""
    if s.startswith("off:"):
        off = int(s[4:], 0)
        va = next((v + (off - o) for v, o, n in segs if o <= off < o + n), off)
    elif s in ("entry", "start", ""):
        if segs:
            va = entry
        else:
            va, note_raw = 0, " (berkas mentah: mulai dari offset 0; pakai off:0x.. untuk lokasi lain)"
    else:
        va = int(s, 0)
    if a in ("arm", "thumb") and va & 1:      # v99.39: alamat ganjil (mis. e_entry Thumb) = Thumb di alamat genap
        a, va = "thumb", va & ~1
    if segs:
        off = next((o + (va - v) for v, o, n in segs if v <= va < v + n), None)
    else:
        off = va
    if off is None or off < 0 or off >= len(d):
        return "DISASM gagal: alamat 0x%X tidak berada di data berkas." % va
    count = max(1, min(int(count), 400))
    code = d[off:off + count * 16 + 16]
    try:
        import capstone
    except ImportError:
        if a in ("arm", "thumb"):           # v99.38: A32 murni Python tanpa capstone; v99.39: + Thumb / Thumb-2
            names = None
            c2 = None
            if segs:
                try:
                    _i2, c2, _e2 = _relab_arm(d)
                    if c2 and c2.get("arch") == "arm":
                        names = dict(c2["L"]["iat"])
                        for tv, tn in c2["thunks"].items():
                            names[tv] = tn.split("!")[-1] + "@plt"
                        for fv, fo in c2["F"].items():
                            names[fv] = fo["name"]
                    else:
                        c2 = None
                except Exception:
                    names, c2 = None, None
            if a == "arm" and c2:
                try:
                    md_ = _arm_mode_at(c2["L"], va)
                    if md_ and md_[0] == "t":
                        a = "thumb"        # wilayah Thumb menurut simbol pemetaan ($t) / simbol fungsi
                except Exception:
                    pass

            def _rd32(x):
                o_ = next((o + (x - v) for v, o, n in segs if v <= x < v + n), None) if segs else x
                return struct.unpack_from("<I", d, o_)[0] if o_ is not None and 0 <= o_ <= len(d) - 4 else None
            if a == "thumb":
                lines = _thumb_disasm_lines(code, va & ~1, count, names, _rd32)
                if lines:
                    return "DISASM @0x%X (%s, ARM 32-bit Thumb / Thumb-2; disassembler bawaan, pasang capstone untuk VFP / NEON / koprosesor)%s:\n%s" % (va, fmt, note_raw, "\n".join(lines))
            else:
                lines = _a32_disasm_lines(code, va & ~3, count, names, _rd32)
                if lines:
                    return "DISASM @0x%X (%s, ARM 32-bit A32; disassembler bawaan, pasang capstone untuk VFP / NEON)%s:\n%s" % (va, fmt, note_raw, "\n".join(lines))
        if a == "arm64":                    # v99.40: AArch64 murni Python tanpa capstone
            names64 = None
            if segs:
                try:
                    _i3, c3, _e3 = _relab_arm(d)
                    if c3 and c3.get("arch") == "arm64":
                        names64 = dict(c3["L"]["iat"])
                        for tv, tn in c3["thunks"].items():
                            names64[tv] = tn.split("!")[-1] + "@plt"
                        for fv, fo in c3["F"].items():
                            names64[fv] = fo["name"]
                except Exception:
                    names64 = None

            def _rd32b(x):
                o_ = next((o + (x - v) for v, o, n in segs if v <= x < v + n), None) if segs else x
                return struct.unpack_from("<I", d, o_)[0] if o_ is not None and 0 <= o_ <= len(d) - 4 else None
            lines = _a64_disasm_lines(code, va & ~3, count, names64, _rd32b)
            if lines:
                return "DISASM @0x%X (%s, AArch64; disassembler bawaan, pasang capstone untuk NEON / SVE / instruksi langka)%s:\n%s" % (va, fmt, note_raw, "\n".join(lines))
        hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
        return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
    ca, modes, label = _CS_ARCHS[a]
    if not hasattr(capstone, ca) or not all(hasattr(capstone, m_) for m_ in modes):
        return "DISASM gagal: capstone yang terpasang belum mendukung %s (coba pip install -U capstone)." % label
    mode = 0
    for m_ in modes:
        mode |= getattr(capstone, m_)
    md = capstone.Cs(getattr(capstone, ca), mode)
    lines = []
    for i in md.disasm(code, va):
        lines.append("   %08X  %-24s %s %s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str))
        if len(lines) >= count:
            break
    if not lines:
        return "DISASM @0x%X (%s, %s): tidak ada instruksi valid di sini; coba arch lain (arch=thumb / arm64 / x86 ...) atau alamat lain.\n%s" % (
            va, fmt, label, "\n".join("   %08X  %s" % (va + k, code[k:k + 16].hex(" ")) for k in range(0, min(len(code), 48), 16)))
    return "DISASM @0x%X (%s, %s)%s:\n%s" % (va, fmt, label, note_raw, "\n".join(lines))


def disasm_text(path, at="entry", count: int = 40, arch=None) -> str:
    """Disassembly dari entry / VA (0x...), 'rva:0x..', 'off:0x..'. Butuh pustaka opsional capstone; tanpa itu menampilkan hex.
    PE x86 / x64: RE Lab penuh (nama API / fungsi). ELF, Mach-O (tipis / fat), dan berkas mentah (shellcode, firmware, dump):
    disassembly generik lewat capstone. arch (opsional, memaksa arsitektur): x86 x64 arm thumb arm64 mips mips64 mipsel ppc ppc64 riscv32 riscv64 sparc."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        pe = _parse_pe(d, size)
        info, ctx, _err = _relab_any(d, size)
        if not ctx or (arch and str(arch).lower() not in ("x86", "x64")):
            return _disasm_generic(d, at, count, arch, bool(pe and not pe.get("broken")))
        L = ctx["L"]
        s = str(at).strip().lower()
        if s in ("entry", "start", ""):
            va = L["entry_va"]
        elif s.startswith("rva:"):
            va = L["base"] + int(s[4:], 0)
        elif s.startswith("off:"):
            o_ = int(s[4:], 0)
            va = next((L["base"] + x["va"] + (o_ - x["rptr"]) for x in L["secs"] if x["rptr"] <= o_ < x["rptr"] + x["rsize"]), 0)
        else:
            va = int(s, 0)
            va = va if va >= L["base"] else L["base"] + va
        off = _va_off(L, va)
        if not va or off is None:
            return "DISASM gagal: alamat tidak berada di data berkas."
        count = max(1, min(int(count), 400))
        code = d[off:off + count * 15 + 16]
        names = dict(L["iat"])
        for tv, tn in ctx["thunks"].items():
            names[tv] = tn.split("!")[-1] + "@plt"
        for fv, fo in ctx["F"].items():
            names[fv] = fo["name"]
        try:
            import capstone
        except ImportError:
            hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
            return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64 if L["is64"] else capstone.CS_MODE_32)
        lines = []
        for i in md.disasm(code, va):
            note = ""
            m = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", i.op_str)
            if m:
                t = i.address + i.size + (int(m.group(2), 16) * (1 if m.group(1) == "+" else -1))
                note = names.get(t, "")
            else:
                m = re.search(r"0x[0-9a-f]+", i.op_str)
                if m and i.mnemonic in ("call", "jmp"):
                    note = names.get(int(m.group(0), 16), "")
                elif m and not L["is64"] and "[" in i.op_str:
                    note = names.get(int(m.group(0), 16), "")
            lines.append("   %08X  %-24s %s %s%s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str, ("   ; " + note) if note else ""))
            if len(lines) >= count:
                break
        return "DISASM @0x%X (%s%s):\n%s" % (va, "ELF " if d[:4] == b"\x7fELF" else "", "x64" if L["is64"] else "x86", "\n".join(lines))
    except Exception as e:
        return "DISASM gagal: %s: %s" % (type(e).__name__, str(e)[:120])


