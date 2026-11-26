# rea_triage bagian 24/47: disasm_thumb (baris asli 9654-10188). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.39 [A1]: disassembler Thumb / Thumb-2 murni Python (tahap 2d-2c-2b-3b-1) -----------------------
# Dipakai `--disasm` / disasm_text untuk ELF / Mach-O ARM 32-bit (wilayah Thumb) dan arch=thumb bila capstone TIDAK terpasang (capstone tetap didahulukan).
# Statis, tanpa dependensi. Thumb 16-bit: seluruh himpunan umum; Thumb-2 32-bit: B / B<c>.W / BL / BLX, data processing (imediat termodifikasi,
# imediat biasa, register bergeser), LDR / STR (imm12, imm8, register, literal), LDM / STM / PUSH / POP, LDRD / STRD, TBB / TBH, MUL / MLA / MLS /
# UMULL.. / SDIV / UDIV, CLZ / REV / RBIT / UXT / SXT, geser register, NOP / DMB / DSB / ISB; sisanya `.short` / `.word` (VFP / NEON / koprosesor /
# atomik / sistem). Blok IT diikuti (akhiran kondisi + flag narrow). Format keluaran meniru capstone; diuji terhadap capstone 5.0.7.

_T_ALU = ("and", "eor", "lsl", "lsr", "asr", "adc", "sbc", "ror", "tst", "rsb", "cmp", "cmn", "orr", "mul", "bic", "mvn")
_T_BARRIER = {15: "sy", 14: "st", 11: "ish", 10: "ishst", 7: "nsh", 6: "nshst", 3: "osh", 2: "oshst"}


def _t_sx(v: int, bits: int) -> int:
    return v - (1 << bits) if v >> (bits - 1) else v


def _t_expand_imm(imm12: int):
    """ThumbExpandImm (12 bit -> 32 bit); None bila pola tak valid (byte nol pada bentuk berulang)."""
    if imm12 >> 10 == 0:
        b, m = imm12 & 0xFF, (imm12 >> 8) & 3
        if m == 0:
            return b
        if not b:
            return None
        return (b | b << 16) if m == 1 else ((b << 8) | (b << 24)) if m == 2 else (b | b << 8 | b << 16 | b << 24)
    v, r = 0x80 | (imm12 & 0x7F), imm12 >> 7
    return ((v >> r) | (v << (32 - r))) & 0xFFFFFFFF


def _t_shop(typ: int, imm5: int) -> str:
    if typ == 0:
        return ", lsl #%d" % imm5 if imm5 else ""
    if typ == 3 and imm5 == 0:
        return ", rrx"
    return ", %s #%d" % (_A32_SH[typ], imm5 or 32)


def _t_simm(v: int) -> str:
    """Imediat bertanda gaya Thumb-2 capstone: negatif selalu heksadesimal ('#-0x7')."""
    return "#-0x%x" % -v if v < 0 else _a32_imm(v)


def _t_mem(rn: int, off: int, mode: str = "o", negz: bool = False) -> str:
    """Operand memori imediat: mode 'o' offset, 'p' pra-indeks (!), 'q' pasca-indeks. off bertanda; negz = bit U nol dengan offset 0 ('#-0')."""
    R = _A32_REG
    if mode == "q":
        return "[%s], %s" % (R[rn], "#-0" if negz else _a32_simm(off))
    s = (", " + ("#-0x0" if negz else _t_simm(off))) if (off or mode == "p" or negz) else ""
    return "[%s%s]%s" % (R[rn], s, "!" if mode == "p" else "")


def _thumb_dis(h1: int, h2: int | None, pc: int, itc: int | None = None):
    """Satu instruksi Thumb / Thumb-2 -> (mnemonik, operand, target, ukuran). h2 = halfword kedua (None bila tak ada). itc = indeks kondisi bila di dalam blok IT.
    Target = alamat percabangan langsung (atau None). Tak dikenal -> ('.short' / '.word', ...)."""
    R = _A32_REG
    in_it = itc is not None
    cc = _A32_CC[itc] if in_it else ""
    sn = "" if in_it else "s"                                    # flag narrow: hanya di luar blok IT
    if (h1 >> 11) in (0x1D, 0x1E, 0x1F):
        if h2 is None:
            return ".short", "0x%04x" % h1, None, 2
        r = _t32_dis(h1, h2, pc, in_it, cc)
        if r is None:
            return ".word", "0x%04x%04x" % (h1, h2), None, 4
        return r[0], r[1], r[2], 4
    r = _t16_dis(h1, pc, in_it, cc, sn)
    if r is None:
        return ".short", "0x%04x" % h1, None, 2
    return r[0], r[1], r[2], 2


def _t16_dis(h: int, pc: int, in_it: bool, cc: str, sn: str):
    R = _A32_REG
    top = h >> 11
    rd, rm3, rn3 = h & 7, (h >> 3) & 7, (h >> 6) & 7
    if top < 3:                                                   # geser imediat
        imm = (h >> 6) & 31
        if top == 0:
            if imm == 0:
                return "mov" + sn + cc, "%s, %s" % (R[rd], R[rm3]), None
            return "lsl" + sn + cc, "%s, %s, %s" % (R[rd], R[rm3], _a32_imm(imm)), None
        return ("lsr", "asr")[top - 1] + sn + cc, "%s, %s, %s" % (R[rd], R[rm3], _a32_imm(imm or 32)), None
    if top == 3:                                                  # add / sub register / imm3
        nm = "sub" if (h >> 9) & 1 else "add"
        v = ("#%d" % rn3 if rn3 < 10 else "#0x%x" % rn3) if (h >> 10) & 1 else R[rn3]
        return nm + sn + cc, "%s, %s, %s" % (R[rd], R[rm3], v), None
    if top < 8:                                                   # mov / cmp / add / sub imm8
        op, rdn, imm = top & 3, (h >> 8) & 7, h & 0xFF
        nm = ("mov", "cmp", "add", "sub")[op]
        return nm + ("" if op == 1 else sn) + cc, "%s, %s" % (R[rdn], _a32_imm(imm)), None
    if top == 8:
        if (h >> 10) == 0x10:                                     # ALU
            op = (h >> 6) & 15
            nm = _T_ALU[op]
            sx = "" if op in (8, 10, 11) else sn
            if op == 9:
                return "rsb" + sx + cc, "%s, %s, #0" % (R[rd], R[rm3]), None
            if op == 13:
                return "mul" + sx + cc, "%s, %s, %s" % (R[rd], R[rm3], R[rd]), None
            return nm + sx + cc, "%s, %s" % (R[rd], R[rm3]), None
        op = (h >> 8) & 3                                         # hi register / BX / BLX
        rm = (h >> 3) & 15
        rdh = (h & 7) | ((h >> 4) & 8)
        if op == 3:
            if h & 7 not in (0, 7):
                return None
            return ("blx" if (h >> 7) & 1 else "bx") + ("ns" if h & 7 else "") + cc, R[rm], None
        if op == 0:
            if rm == 13:
                return "add" + cc, "%s, sp, %s" % (R[rdh], R[rdh]), None
            return "add" + cc, "%s, %s" % (R[rdh], R[rm]), None
        if op == 1:
            return "cmp" + cc, "%s, %s" % (R[rdh], R[rm]), None
        return "mov" + cc, "%s, %s" % (R[rdh], R[rm]), None
    if top == 9:                                                  # LDR literal
        return "ldr" + cc, "%s, [pc, #%s]" % (R[(h >> 8) & 7], _a32_imm((h & 0xFF) * 4)[1:]), None
    if (h >> 12) == 5:                                            # load / store register
        op = (h >> 9) & 7
        nm = ("str", "strh", "strb", "ldrsb", "ldr", "ldrh", "ldrb", "ldrsh")[op]
        return nm + cc, "%s, [%s, %s]" % (R[rd], R[rm3], R[rn3]), None
    if (h >> 13) == 3:                                            # load / store imm5 (word / byte)
        b, ld, imm = (h >> 12) & 1, (h >> 11) & 1, (h >> 6) & 31
        nm = ("ldr" if ld else "str") + ("b" if b else "")
        off = imm if b else imm * 4
        return nm + cc, "%s, %s" % (R[rd], _t_mem(rm3, off)), None
    if top in (16, 17):                                           # halfword imm5
        off = ((h >> 6) & 31) * 2
        return ("ldrh" if top & 1 else "strh") + cc, "%s, %s" % (R[rd], _t_mem(rm3, off)), None
    if top in (18, 19):                                           # SP-relative
        return ("ldr" if top & 1 else "str") + cc, "%s, %s" % (R[(h >> 8) & 7], _t_mem(13, (h & 0xFF) * 4)), None
    if top in (20, 21):                                           # ADR / ADD Rd, SP, #imm
        rdd, imm = (h >> 8) & 7, (h & 0xFF) * 4
        if top == 20:
            return "adr" + cc, "%s, %s" % (R[rdd], _a32_imm(imm)), None
        return "add" + cc, "%s, sp, %s" % (R[rdd], _a32_imm(imm)), None
    if top in (22, 23):                                           # misc 16-bit
        hi = (h >> 8) & 15
        if hi == 0:
            return ("sub" if (h >> 7) & 1 else "add") + cc, "sp, %s" % _a32_imm((h & 0x7F) * 4), None
        if hi == 2:
            return ("sxth", "sxtb", "uxth", "uxtb")[(h >> 6) & 3] + cc, "%s, %s" % (R[rd], R[rm3]), None
        if (h & 0xF500) == 0xB100:
            if in_it:
                return None
            t = (pc + 4 + (((h >> 9) & 1) << 6 | ((h >> 3) & 31) << 1)) & 0xFFFFFFFF
            return ("cbnz" if (h >> 11) & 1 else "cbz") + cc, "%s, #0x%x" % (R[rd], t), t
        if (h & 0xF600) == 0xB400:
            m = h & 0xFF
            if not m and not (h & 0x100):
                return None
            lst = [R[i] for i in range(8) if m >> i & 1]
            if h & 0x100:
                lst.append("pc" if (h >> 11) & 1 else "lr")
            return ("pop" if (h >> 11) & 1 else "push") + cc, "{" + ", ".join(lst) + "}", None
        if (h & 0xFFC0) in (0xBA00, 0xBA40, 0xBAC0):
            return {0xBA00: "rev", 0xBA40: "rev16", 0xBAC0: "revsh"}[h & 0xFFC0] + cc, "%s, %s" % (R[rd], R[rm3]), None
        if (h & 0xFF00) == 0xBE00:
            return "bkpt", _a32_imm(h & 0xFF), None
        if (h & 0xFF00) == 0xBF00:
            if h & 15:
                return None                                       # IT: ditangani pemanggil (_thumb_it)
            k = (h >> 4) & 15
            nm = {0: "nop", 1: "yield", 2: "wfe", 3: "wfi", 4: "sev"}.get(k)
            return (nm + cc, "", None) if nm else ("hint" + cc, _a32_imm(k), None)
        if (h & 0xFFE8) == 0xB660:
            return ("cpsid" if (h >> 4) & 1 else "cpsie"), ("".join(c_ for c_, b_ in (("a", 4), ("i", 2), ("f", 1)) if h & b_) or "none"), None
        return None
    if top in (24, 25):                                           # LDM / STM
        rn, m = (h >> 8) & 7, h & 0xFF
        if not m:
            return None
        ld = (h >> 11) & 1
        wb = "" if (ld and (m >> rn) & 1) else "!"
        return ("ldm" if ld else "stm") + cc, "%s%s, {%s}" % (R[rn], wb, ", ".join(R[i] for i in range(8) if m >> i & 1)), None
    if top in (26, 27):                                           # B<c> / UDF / SVC
        c = (h >> 8) & 15
        if c == 15:
            return "svc" + cc, _a32_imm(h & 0xFF), None
        if c == 14:
            return None
        if in_it:
            return None
        t = (pc + 4 + _t_sx(h & 0xFF, 8) * 2) & 0xFFFFFFFF
        return "b" + _A32_CC[c], "#0x%x" % t, t
    if top == 28:                                                 # B
        t = (pc + 4 + _t_sx(h & 0x7FF, 11) * 2) & 0xFFFFFFFF
        return "b" + cc, "#0x%x" % t, t
    return None


def _thumb_it(h: int):
    """Halfword IT -> (mnemonik, operand, [indeks kondisi tiap instruksi]) atau None."""
    if (h & 0xFF00) != 0xBF00 or not h & 15:
        return None
    fc, mask = (h >> 4) & 15, h & 15
    if fc == 15:
        return None
    cnt = 4 - ((mask & -mask).bit_length() - 1)
    letters, conds = "", [fc]
    for k in range(1, cnt):
        same = ((mask >> (4 - k)) & 1) == (fc & 1)
        letters += "t" if same else "e"
        conds.append(fc if same else fc ^ 1)
    if fc == 14 and "e" in letters:
        return None
    return "it" + letters, _A32_CC[fc] or "al", conds


def _t32_dis(h1: int, h2: int, pc: int, in_it: bool, cc: str):
    R = _A32_REG
    sn = "" if in_it else "s"
    op1 = (h1 >> 11) & 3
    if op1 == 2 and (h2 & 0x8000):                                # cabang + kontrol misc
        return _t32_branch(h1, h2, pc, in_it, cc)
    if op1 == 2:                                                  # imediat (termodifikasi / biasa)
        if not (h1 & 0x0200):
            return _t32_modimm(h1, h2, in_it, cc)
        return _t32_plainimm(h1, h2, in_it, cc)
    if op1 == 1:
        op2 = (h1 >> 4) & 0x7F
        if op2 & 0x60 == 0x00 and not op2 & 4:
            return _t32_ldstm(h1, h2, cc)
        if op2 & 0x64 == 0x04:
            return _t32_dualtb(h1, h2, cc)
        if op2 & 0x60 == 0x20:
            return _t32_shreg(h1, h2, in_it, cc)
        return None
    # op1 == 3
    op2 = (h1 >> 4) & 0x7F
    if op2 & 0x71 == 0x00 or (op2 & 0x67 in (0x01, 0x03, 0x05)):
        return _t32_ldst(h1, h2, cc)
    if op2 & 0x70 == 0x20:
        return _t32_dpreg(h1, h2, in_it, cc)
    if op2 & 0x78 == 0x30:
        return _t32_mul(h1, h2, cc)
    if op2 & 0x78 == 0x38:
        return _t32_lmul(h1, h2, cc)
    return None


def _t32_branch(h1: int, h2: int, pc: int, in_it: bool, cc: str):
    typ = (h2 >> 12) & 5
    S = (h1 >> 10) & 1
    J1, J2 = (h2 >> 13) & 1, (h2 >> 11) & 1
    if typ == 0:                                                  # B<c>.W atau misc kontrol
        if ((h1 >> 7) & 7) != 7:
            if in_it:
                return None
            c = (h1 >> 6) & 15
            off = _t_sx(S << 20 | J2 << 19 | J1 << 18 | (h1 & 0x3F) << 12 | (h2 & 0x7FF) << 1, 21)
            t = (pc + 4 + off) & 0xFFFFFFFF
            return "b" + _A32_CC[c] + ".w", "#0x%x" % t, t
        if h1 == 0xF3AF and not (h2 & 0xFF00 ^ 0x8000):
            nm = {0: "nop", 1: "yield", 2: "wfe", 3: "wfi", 4: "sev"}.get(h2 & 0xFF)
            return (nm + cc + ".w", "", None) if nm else None
        if h1 == 0xF3BF and (h2 & 0xFF00) == 0x8F00:
            nm = {0x40: "dsb", 0x50: "dmb", 0x60: "isb"}.get(h2 & 0xF0)
            opt = _T_BARRIER.get(h2 & 15)
            if nm and opt:
                return nm + cc, opt, None
        return None
    I1, I2 = (~(J1 ^ S)) & 1, (~(J2 ^ S)) & 1
    if typ == 5 or typ == 1:                                      # B.W (typ 1) / BL (typ 5)
        off = _t_sx(S << 24 | I1 << 23 | I2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1, 25)
        t = (pc + 4 + off) & 0xFFFFFFFF
        if typ == 1:
            return "b" + cc + ".w", "#0x%x" % t, t
        return "bl" + cc, "#0x%x" % t, t
    if typ == 4:                                                  # BLX imm
        if h2 & 1:
            return None
        off = _t_sx(S << 24 | I1 << 23 | I2 << 22 | (h1 & 0x3FF) << 12 | ((h2 >> 1) & 0x3FF) << 2, 25)
        t = ((pc + 4) & ~3) + off & 0xFFFFFFFF
        return "blx" + cc, "#0x%x" % t, t
    return None


_T_DP_NAME = {0: "and", 1: "bic", 2: "orr", 3: "orn", 4: "eor", 8: "add", 10: "adc", 11: "sbc", 13: "sub", 14: "rsb"}
_T_DP_CMP = {0: "tst", 4: "teq", 8: "cmn", 13: "cmp"}
_T_W_IMM = frozenset((8, 13, 14))                 # akhiran .w pada bentuk imediat (add / sub / rsb / mov); cmp / tst / teq / cmn selalu
_T_W_REG = frozenset((0, 1, 2, 4, 8, 10, 11, 13))    # bentuk register (kecuali orn / rsb); mvn / mov selalu


def _t32_dp(op: int, S: int, rn: int, rd: int, o2: str, in_it: bool, cc: str, form: str, v=None):
    """Susunan umum data processing 32-bit: tst / teq / cmn / cmp, mov / mvn, atau 3-operand. form 'imm' (v = nilai) atau 'reg' (o2 = teks)."""
    R = _A32_REG
    sx = "s" if S else ""
    if form == "imm":
        cmpf = op in _T_DP_CMP and rd == 15 and S
        sg = cmpf or (op == 2 and rn == 15) or (op in (3, 8, 10, 11, 13, 14) and not (op == 3 and rn == 15))
        o2 = _a32_simm(v - (1 << 32) if (v >> 31 and sg) else v)
    if op in _T_DP_CMP and rd == 15 and S:
        return _T_DP_CMP[op] + cc + ".w", "%s, %s" % (R[rn], o2), None
    nm = _T_DP_NAME.get(op)
    if nm is None:
        return None
    if op in (2, 3) and rn == 15:
        w = ".w" if (op == 2 or form == "reg") else ""
        return ("mov" if op == 2 else "mvn") + sx + cc + w, "%s, %s" % (R[rd], o2), None
    if op in _T_DP_CMP and rd == 15:
        return None
    w = ".w" if op in (_T_W_IMM if form == "imm" else _T_W_REG) else ""
    return nm + sx + cc + w, "%s, %s, %s" % (R[rd], R[rn], o2), None


def _t32_modimm(h1: int, h2: int, in_it: bool, cc: str):
    op, S, rn = (h1 >> 5) & 15, (h1 >> 4) & 1, h1 & 15
    rd = (h2 >> 8) & 15
    imm12 = ((h1 >> 10) & 1) << 11 | ((h2 >> 12) & 7) << 8 | (h2 & 0xFF)
    v = _t_expand_imm(imm12)
    if v is None:
        return None
    return _t32_dp(op, S, rn, rd, "", in_it, cc, "imm", v)


def _t32_shreg(h1: int, h2: int, in_it: bool, cc: str):
    if h2 & 0x8000:
        return None
    op, S, rn = (h1 >> 5) & 15, (h1 >> 4) & 1, h1 & 15
    rd, rm, typ = (h2 >> 8) & 15, h2 & 15, (h2 >> 4) & 3
    imm5 = ((h2 >> 12) & 7) << 2 | ((h2 >> 6) & 3)
    R = _A32_REG
    if op == 2 and rn == 15:                                       # mov / geser / rrx
        sx = "s" if S else ""
        if typ == 0 and not imm5:
            return "mov" + sx + cc + ".w", "%s, %s" % (R[rd], R[rm]), None
        if typ == 3 and not imm5:
            return "rrx" + sx + cc, "%s, %s" % (R[rd], R[rm]), None
        return _A32_SH[typ] + sx + cc + ".w", "%s, %s, %s" % (R[rd], R[rm], _a32_imm(imm5 or 32)), None
    return _t32_dp(op, S, rn, rd, R[rm] + _t_shop(typ, imm5), in_it, cc, "reg")


def _t32_plainimm(h1: int, h2: int, in_it: bool, cc: str):
    R = _A32_REG
    op, rn = (h1 >> 4) & 31, h1 & 15
    rd = (h2 >> 8) & 15
    i, imm3, imm8 = (h1 >> 10) & 1, (h2 >> 12) & 7, h2 & 0xFF
    if op in (0x00, 0x0A):                                         # addw / subw
        v = i << 11 | imm3 << 8 | imm8
        return ("addw" if op == 0 else "subw") + cc, "%s, %s, %s" % (R[rd], R[rn], _a32_imm(v)), None
    if op in (0x04, 0x0C):                                         # movw / movt
        v = (h1 & 15) << 12 | i << 11 | imm3 << 8 | imm8
        return ("movw" if op == 4 else "movt") + cc, "%s, %s" % (R[rd], _a32_imm(v)), None
    lsb, w5 = imm3 << 2 | ((h2 >> 6) & 3), h2 & 31
    if i:
        return None
    if op in (0x14, 0x1C):                                         # sbfx / ubfx
        return ("sbfx" if op == 0x14 else "ubfx") + cc, "%s, %s, %s, %s" % (R[rd], R[rn], _a32_imm(lsb), _a32_imm(w5 + 1)), None
    if op == 0x16:                                                 # bfi / bfc
        if w5 < lsb or (h2 & 0x20):
            return None
        if rn == 15:
            return "bfc" + cc, "%s, %s, %s" % (R[rd], _a32_imm(lsb), _a32_imm(w5 - lsb + 1)), None
        return "bfi" + cc, "%s, %s, %s, %s" % (R[rd], R[rn], _a32_imm(lsb), _a32_imm(w5 - lsb + 1)), None
    return None


def _t32_ldstm(h1: int, h2: int, cc: str):
    R = _A32_REG
    op, W, L, rn = (h1 >> 7) & 3, (h1 >> 5) & 1, (h1 >> 4) & 1, h1 & 15
    if op not in (1, 2) or rn == 15 or (not L and (h2 & 0xA000)) or (L and (h2 & 0xC000) == 0xC000):
        return None
    lst = "{%s}" % ", ".join(R[i] for i in range(16) if h2 >> i & 1)
    if not h2 & 0xFFFF:
        return None
    if rn == 13 and W:
        if op == 1 and L:
            return "pop" + cc + ".w", lst, None
        if op == 2 and not L:
            return "push" + cc + ".w", lst, None
    nm = ("ldm" if L else "stm") + ("" if op == 1 else "db")
    return nm + cc + (".w" if op == 1 else ""), "%s%s, %s" % (R[rn], "!" if W else "", lst), None


def _t32_dualtb(h1: int, h2: int, cc: str):
    R = _A32_REG
    rn = h1 & 15
    if (h1 & 0xFFF0) == 0xE8D0 and (h2 & 0xFFE0) == 0xF000:      # TBB / TBH
        rm = h2 & 15
        if (h2 >> 4) & 1:
            return "tbh" + cc, "[%s, %s, lsl #1]" % (R[rn], R[rm]), None
        return "tbb" + cc, "[%s, %s]" % (R[rn], R[rm]), None
    P, U, W, L = (h1 >> 8) & 1, (h1 >> 7) & 1, (h1 >> 5) & 1, (h1 >> 4) & 1
    if (h1 & 0xFE40) != 0xE840:
        return None
    rt, rt2 = (h2 >> 12) & 15, (h2 >> 8) & 15
    off = (h2 & 0xFF) * 4
    if not (P or W):                                               # LDREX / STREX (T1)
        if U:
            return None
        mem = _t_mem(rn, off)
        if L:
            if rt2 != 15:
                return None
            return "ldrex" + cc, "%s, %s" % (R[rt], mem), None
        if rt == 15:
            return None
        return "strex" + cc, "%s, %s, %s" % (R[rt2], R[rt], mem), None
    off = off if U else -off
    if rn == 15:
        if not P or W or not L:
            return None
        return "ldrd" + cc, "%s, %s, [pc, %s]" % (R[rt], R[rt2], "#-0x0" if (not U and not off) else _t_simm(off)), None
    nz = not U and not off
    mem = _t_mem(rn, off, "o" if not W else "p", nz) if P else _t_mem(rn, off, "q", nz)
    return ("ldrd" if L else "strd") + cc, "%s, %s, %s" % (R[rt], R[rt2], mem), None


def _t32_ldst(h1: int, h2: int, cc: str):
    R = _A32_REG
    size, imm12, L, S, rn = (h1 >> 5) & 3, (h1 >> 7) & 1, (h1 >> 4) & 1, (h1 >> 8) & 1, h1 & 15
    rt = (h2 >> 12) & 15
    if (h1 & 0xFE00) != 0xF800 or size == 3 or (S and not L):
        return None
    if size == 2 and S:
        return None
    if L:
        nm = ("ldrsb" if S else "ldrb", "ldrsh" if S else "ldrh", "ldr")[size]
    else:
        nm = ("strb", "strh", "str")[size]
    if L and rt == 15 and size != 2:
        return None
    if rn == 15:                                                   # literal
        if not L:
            return None
        off = h2 & 0xFFF
        return nm + cc + ".w", "%s, [pc, %s]" % (R[rt], "#-0x0" if (not imm12 and not off) else _t_simm(off if imm12 else -off)), None
    if imm12:
        return nm + cc + ".w", "%s, %s" % (R[rt], _t_mem(rn, h2 & 0xFFF)), None
    if not (h2 & 0x0800):                                          # register offset
        if (h2 & 0x0FC0) or (h2 & 15) in (13, 15) and False:
            return None
        sh = (h2 >> 4) & 3
        return nm + cc + ".w", "%s, [%s, %s%s]" % (R[rt], R[rn], R[h2 & 15], (", lsl #%d" % sh) if sh else ""), None
    P, U, W = (h2 >> 10) & 1, (h2 >> 9) & 1, (h2 >> 8) & 1
    off = h2 & 0xFF
    if (h2 & 0xF00) == 0xE00:                                      # LDRT / STRT / .. (tak berhak)
        return nm + "t" + cc, "%s, %s" % (R[rt], _t_mem(rn, off)), None
    if not P and not W:
        return None
    nz = not U and not off
    off = off if U else -off
    return nm + cc, "%s, %s" % (R[rt], _t_mem(rn, off, ("p" if W else "o") if P else "q", nz)), None


def _t32_dpreg(h1: int, h2: int, in_it: bool, cc: str):
    R = _A32_REG
    if (h2 & 0xF000) != 0xF000:
        return None
    rn, rd, rm = h1 & 15, (h2 >> 8) & 15, h2 & 15
    op1, op2 = (h1 >> 4) & 15, (h2 >> 4) & 15
    if (h2 & 0xF0) == 0 and not op1 & 8:                          # geser register
        S = op1 & 1
        typ = (op1 >> 1) & 3
        return _A32_SH[typ] + ("s" if S else "") + cc + ".w", "%s, %s, %s" % (R[rd], R[rn], R[rm]), None
    if (op1 & 8) == 0 and (h2 & 0x80) and rn == 15 and op1 in (0, 1, 4, 5):   # extend
        rot = ((h2 >> 4) & 3) * 8
        nm = {0: "sxth", 1: "uxth", 4: "sxtb", 5: "uxtb"}[op1]
        return nm + cc + ".w", "%s, %s%s" % (R[rd], R[rm], (", ror #%d" % rot) if rot else ""), None
    if op1 == 9 and (h2 & 0xC0) == 0x80 and rn == rm:              # rev / rev16 / rbit / revsh
        nm = {0x8: "rev", 0x9: "rev16", 0xA: "rbit", 0xB: "revsh"}.get(op2)
        if nm:
            return nm + cc + ("" if nm == "rbit" else ".w"), "%s, %s" % (R[rd], R[rm]), None
    if op1 == 11 and op2 == 8 and rn == rm:
        return "clz" + cc, "%s, %s" % (R[rd], R[rm]), None
    return None


def _t32_mul(h1: int, h2: int, cc: str):
    R = _A32_REG
    op1, op2 = (h1 >> 4) & 7, (h2 >> 4) & 3
    if op1 or (h2 & 0xC0):
        return None
    rn, ra, rd, rm = h1 & 15, (h2 >> 12) & 15, (h2 >> 8) & 15, h2 & 15
    if op2 == 0:
        if ra == 15:
            return "mul" + cc, "%s, %s, %s" % (R[rd], R[rn], R[rm]), None
        return "mla" + cc, "%s, %s, %s, %s" % (R[rd], R[rn], R[rm], R[ra]), None
    if op2 == 1:
        return "mls" + cc, "%s, %s, %s, %s" % (R[rd], R[rn], R[rm], R[ra]), None
    return None


def _t32_lmul(h1: int, h2: int, cc: str):
    R = _A32_REG
    op1, op2 = (h1 >> 4) & 7, (h2 >> 4) & 15
    rn, rlo, rhi, rm = h1 & 15, (h2 >> 12) & 15, (h2 >> 8) & 15, h2 & 15
    if op2 == 15 and op1 in (1, 3):
        if rlo != 15:
            return None
        return ("sdiv" if op1 == 1 else "udiv") + cc, "%s, %s, %s" % (R[rhi], R[rn], R[rm]), None
    nm = {(0, 0): "smull", (2, 0): "umull", (4, 0): "smlal", (6, 0): "umlal"}.get((op1, op2))
    if nm:
        return nm + cc, "%s, %s, %s, %s" % (R[rlo], R[rhi], R[rn], R[rm]), None
    return None


def _thumb_disasm_lines(code: bytes, va: int, count: int, names: dict | None = None, read32=None) -> list[str]:
    """Baris disassembly Thumb / Thumb-2 (alamat, hex, mnemonik, operand, catatan nama / literal). Blok IT diikuti."""
    names = names or {}
    out, i, it = [], 0, []
    n = len(code)
    while i + 2 <= n and len(out) < count:
        h1 = struct.unpack_from("<H", code, i)[0]
        h2 = struct.unpack_from("<H", code, i + 2)[0] if (h1 >> 11) in (0x1D, 0x1E, 0x1F) and i + 4 <= n else None
        pc = va + i
        itx = _thumb_it(h1)                                         # IT baru selalu menggantikan blok yang berjalan
        if itx:
            m, o, t, sz = itx[0], itx[1], None, 2
            it = list(itx[2])
        else:
            itc = it.pop(0) if it else None
            m, o, t, sz = _thumb_dis(h1, h2, pc, itc)
        note = ""
        if t is not None:
            note = names.get(t, "")
        elif m.startswith(("ldr", "adr")) and ("[pc," in o or m.startswith("adr")):
            if sz == 2:
                imm = (h1 & 0xFF) * 4
                lit = ((pc + 4) & ~3) + imm
            else:
                imm = h2 & 0xFFF
                lit = ((pc + 4) & ~3) + (imm if (h1 >> 7) & 1 else -imm)
            if m.startswith("ldr"):
                v = read32(lit) if read32 else None
                note = names.get(lit) or ("=0x%x" % v if v is not None else "")
                if v is not None and not names.get(lit) and names.get(v):
                    note = "=%s" % names[v]
            else:
                note = names.get(lit, "") or "=0x%x" % lit
        out.append("   %08X  %-24s %s %s%s" % (pc, code[i:i + sz].hex(" "), m, o, ("   ; " + note) if note else ""))
        i += sz
    return out



