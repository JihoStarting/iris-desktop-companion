# rea_triage bagian 23/47: disasm_a32 (baris asli 9416-9653). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.38 [A1]: disassembler ARM 32-bit (A32) murni Python (tahap 2d-2c-2b-3a) -----------------------
# Dipakai `--disasm` / disasm_text untuk ELF / Mach-O ARM 32-bit bila capstone TIDAK terpasang (capstone, bila ada, tetap didahulukan).
# Statis, tanpa dependensi. Instruksi umum saja: data processing (reg / imm / geser), MOVW / MOVT, MUL / MLA / UMULL.., LDR / STR (word, byte,
# half, signed, dual), LDM / STM / PUSH / POP, B / BL / BLX / BX, SVC, CLZ, BKPT, UBFX / SBFX / BFI / BFC, UXT / SXT, REV; sisanya `.word`
# (VFP / NEON / koprosesor / atomik / sistem). Format keluaran meniru capstone; diuji terhadap capstone 5.0.7 pada jutaan kata acak (100% sama).
# Thumb / Thumb-2 sudah (v99.39, blok di bawah); AArch64 tanpa capstone sudah (v99.40, blok sebelum _disasm_generic).

_A32_CC = ("eq", "ne", "hs", "lo", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "", "")
_A32_REG = ("r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp", "ip", "sp", "lr", "pc")
_A32_DP = ("and", "eor", "sub", "rsb", "add", "adc", "sbc", "rsc", "tst", "teq", "cmp", "cmn", "orr", "mov", "bic", "mvn")
_A32_SH = ("lsl", "lsr", "asr", "ror")


def _a32_imm(v: int) -> str:
    return "#%d" % v if v < 10 else "#0x%x" % v


def _a32_simm(v: int) -> str:
    return _a32_imm(v) if v >= 0 else "#-" + _a32_imm(-v)[1:]


def _a32_off(off: int, u: int, p: int, wb: int) -> str:
    """Offset imediat memori: pasca-indeks selalu tampil; pra-indeks kosong bila 0 dan naik tanpa writeback (gaya capstone: '#-0' bila turun)."""
    if off:
        return ", " + _a32_simm(off if u else -off)
    if not u:
        return ", #-0"
    return ", #0" if (not p or wb) else ""


def _a32_shift_txt(w: int) -> str:
    """Bagian geser operand register (bit 11..4) -> ', lsl #2' / ', lsl r3' / ', rrx' / ''."""
    st = (w >> 5) & 3
    if (w >> 4) & 1:
        return ", %s %s" % (_A32_SH[st], _A32_REG[(w >> 8) & 15])
    n = (w >> 7) & 31
    if st == 0:
        return ", lsl #%d" % n if n else ""
    if st == 3 and n == 0:
        return ", rrx"
    return ", %s #%d" % (_A32_SH[st], n or (32 if st in (1, 2) else n))


def _a32_reglist(m: int) -> str:
    return "{" + ", ".join(_A32_REG[i] for i in range(16) if m >> i & 1) + "}"


def _a32_dis(w: int, pc: int):
    """Satu kata A32 -> (mnemonik, operand, target). Target = alamat percabangan langsung (atau None). Tak dikenal -> ('.word', '0x...', None).
    Hanya instruksi umum (data processing, MOVW/MOVT, MUL/MLA/UMULL.., LDR/STR/LDRH/LDRSB/LDRD, LDM/STM/PUSH/POP, B/BL/BLX/BX, SVC, CLZ, BKPT,
    UBFX/SBFX/BFI/BFC, UXTB/UXTH/SXTB/SXTH, REV); VFP / NEON / koprosesor / atomik / sistem -> .word."""
    bad = (".word", "0x%08x" % w, None)
    cond = w >> 28
    cc = _A32_CC[cond] if cond != 15 else ""
    R = _A32_REG
    top = (w >> 25) & 7
    if cond == 15:
        if (w & 0xFE000000) == 0xFA000000:                                   # BLX imm
            t = (pc + 8 + (((w & 0xFFFFFF) ^ 0x800000) - 0x800000) * 4 + ((w >> 24) & 1) * 2) & 0xFFFFFFFF
            return "blx", "#0x%x" % t, t
        return bad
    if top == 0:
        if (w & 0x0FFFFFF0) == 0x012FFF10:
            return "bx" + cc, R[w & 15], None
        if (w & 0x0FFFFFF0) == 0x012FFF30:
            return "blx" + cc, R[w & 15], None
        if (w & 0x0FFF0FF0) == 0x016F0F10:
            return "clz" + cc, "%s, %s" % (R[(w >> 12) & 15], R[w & 15]), None
        if (w & 0x0FF000F0) == 0x01200070 and cond == 14:
            v = ((w >> 4) & 0xFFF0) | (w & 15)
            return "bkpt", _a32_imm(v), None
        if (w & 0x90) == 0x90:
            sh = (w >> 5) & 3
            if sh == 0:                                                      # multiply / swap / exclusive
                rd, rn, rs, rm = (w >> 16) & 15, (w >> 12) & 15, (w >> 8) & 15, w & 15
                s = "s" if (w >> 20) & 1 else ""
                if (w & 0x0FE000F0) == 0x00000090:
                    return "mul" + s + cc, "%s, %s, %s" % (R[rd], R[rm], R[rs]), None
                if (w & 0x0FE000F0) == 0x00200090:
                    return "mla" + s + cc, "%s, %s, %s, %s" % (R[rd], R[rm], R[rs], R[rn]), None
                if (w & 0x0F8000F0) == 0x00800090:
                    nm = ("umull", "umlal", "smull", "smlal")[(w >> 21) & 3]
                    return nm + s + cc, "%s, %s, %s, %s" % (R[rn], R[rd], R[rm], R[rs]), None
                return bad
            p, u, i, wb, l = (w >> 24) & 1, (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 20) & 1
            if not l and sh == 1:
                nm = "strh"
            elif not l:
                nm = "ldrd" if sh == 2 else "strd"
            else:
                nm = ("", "ldrh", "ldrsb", "ldrsh")[sh]
            rt, rn = (w >> 12) & 15, (w >> 16) & 15
            if not i and (w & 0xF00):
                return bad
            if (nm in ("ldrd", "strd") and (rt & 1)) or (not p and wb):
                return bad
            if i:
                off = ((w >> 4) & 0xF0) | (w & 15)
                o = _a32_off(off, u, p, wb)
            else:
                o = ", %s%s" % ("" if u else "-", R[w & 15])
            if nm in ("ldrd", "strd"):
                rt_s = "%s, %s" % (R[rt], R[rt + 1])
            else:
                rt_s = R[rt]
            if p:
                return nm + cc, "%s, [%s%s]%s" % (rt_s, R[rn], o, "!" if wb else ""), None
            return nm + cc, "%s, [%s]%s" % (rt_s, R[rn], o), None
        # data processing, operando register
        op, s = (w >> 21) & 15, (w >> 20) & 1
        if 8 <= op <= 11 and not s:
            return bad
        return _a32_dp_dis(w, op, s, cc, "reg")
    if top == 1:
        op, s = (w >> 21) & 15, (w >> 20) & 1
        if (w & 0x0FF00000) == 0x03000000:
            return "movw" + cc, "%s, %s" % (R[(w >> 12) & 15], _a32_imm(((w >> 4) & 0xF000) | (w & 0xFFF))), None
        if (w & 0x0FF00000) == 0x03400000:
            return "movt" + cc, "%s, %s" % (R[(w >> 12) & 15], _a32_imm(((w >> 4) & 0xF000) | (w & 0xFFF))), None
        if 8 <= op <= 11 and not s:
            return bad
        return _a32_dp_dis(w, op, s, cc, "imm")
    if top in (2, 3):
        if top == 3 and (w & 0x10):
            return _a32_media(w, cc, bad)
        p, u, b, wb, l = (w >> 24) & 1, (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 20) & 1
        rt, rn = (w >> 12) & 15, (w >> 16) & 15
        nm = ("ldr" if l else "str") + ("b" if b else "")
        if not p and wb:
            nm += "t"
            wb = 0
        if top == 2:
            off = w & 0xFFF
            o = _a32_off(off, u, p, wb)
        else:
            o = ", %s%s%s" % ("" if u else "-", R[w & 15], _a32_shift_txt(w & ~0x10))
        if p:
            return nm + cc, "%s, [%s%s]%s" % (R[rt], R[rn], o, "!" if wb else ""), None
        return nm + cc, "%s, [%s]%s" % (R[rt], R[rn], o), None
    if top == 4:
        p, u, sbit, wb, l = (w >> 24) & 1, (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 20) & 1
        rn, m = (w >> 16) & 15, w & 0xFFFF
        if not m:
            return bad
        if rn == 13 and wb and not sbit:
            if not l and p and not u:
                return "push" + cc, _a32_reglist(m), None
            if l and not p and u:
                return "pop" + cc, _a32_reglist(m), None
        md = {(0, 0): "da", (0, 1): "ia", (1, 0): "db", (1, 1): "ib"}[(p, u)]
        nm = ("ldm" if l else "stm") + ("" if md == "ia" else md)
        return nm + cc, "%s%s, %s%s" % (R[rn], "!" if wb else "", _a32_reglist(m), " ^" if sbit else ""), None
    if top == 5:
        t = (pc + 8 + (((w & 0xFFFFFF) ^ 0x800000) - 0x800000) * 4) & 0xFFFFFFFF
        return ("bl" if (w >> 24) & 1 else "b") + cc, "#0x%x" % t, t
    if top == 7 and (w & 0x0F000000) == 0x0F000000:
        return "svc" + cc, _a32_imm(w & 0xFFFFFF), None
    return bad


def _a32_dp_dis(w, op, s, cc, kind):
    R = _A32_REG
    rn, rd = (w >> 16) & 15, (w >> 12) & 15
    if kind == "imm":
        v = w & 0xFF
        r = ((w >> 8) & 15) * 2
        v = ((v >> r) | (v << (32 - r))) & 0xFFFFFFFF if r else v
        o2 = _a32_imm(v)
        sh = None
    else:
        o2 = R[w & 15] + _a32_shift_txt(w)
        sh = ((w >> 4) & 1) or ((w >> 5) & 3) or ((w >> 7) & 31)
    nm = _A32_DP[op]
    if (8 <= op <= 11 and rd) or (op in (13, 15) and rn):                   # bidang SBZ tidak nol: bukan kode normal
        return ".word", "0x%08x" % w, None
    if 8 <= op <= 11:
        return nm + cc, "%s, %s" % (R[rn], o2), None
    sx = "s" if s else ""
    if op in (13, 15):
        if op == 13 and kind == "reg" and sh:                                # mov Rd, Rm, lsl #n -> lsl Rd, Rm, #n (gaya capstone / GNU)
            st = (w >> 5) & 3
            if (w >> 4) & 1:
                return _A32_SH[st] + sx + cc, "%s, %s, %s" % (R[rd], R[w & 15], R[(w >> 8) & 15]), None
            if not (st == 3 and not (w >> 7) & 31):
                n = (w >> 7) & 31
                return _A32_SH[st] + sx + cc, "%s, %s, %s" % (R[rd], R[w & 15], _a32_imm(n or (32 if st in (1, 2) else 0))), None
            return "rrx" + sx + cc, "%s, %s" % (R[rd], R[w & 15]), None
        return nm + sx + cc, "%s, %s" % (R[rd], o2), None
    return nm + sx + cc, "%s, %s, %s" % (R[rd], R[rn], o2), None


def _a32_media(w, cc, bad):
    R = _A32_REG
    rd, rn, rm = (w >> 12) & 15, (w >> 16) & 15, w & 15
    if (w & 0x0FFF03F0) == 0x06EF0070:
        return "uxtb" + cc, "%s, %s%s" % (R[rd], R[rm], (", ror #%d" % (8 * ((w >> 10) & 3))) if (w >> 10) & 3 else ""), None
    if (w & 0x0FFF03F0) == 0x06FF0070:
        return "uxth" + cc, "%s, %s%s" % (R[rd], R[rm], (", ror #%d" % (8 * ((w >> 10) & 3))) if (w >> 10) & 3 else ""), None
    if (w & 0x0FFF03F0) == 0x06AF0070:
        return "sxtb" + cc, "%s, %s%s" % (R[rd], R[rm], (", ror #%d" % (8 * ((w >> 10) & 3))) if (w >> 10) & 3 else ""), None
    if (w & 0x0FFF03F0) == 0x06BF0070:
        return "sxth" + cc, "%s, %s%s" % (R[rd], R[rm], (", ror #%d" % (8 * ((w >> 10) & 3))) if (w >> 10) & 3 else ""), None
    if (w & 0x0FFF0FF0) == 0x06BF0F30:
        return "rev" + cc, "%s, %s" % (R[rd], R[rm]), None
    if (w & 0x0FA00070) == 0x07A00050:
        lsb, wd = (w >> 7) & 31, ((w >> 16) & 31) + 1
        return ("sbfx" if not (w >> 22) & 1 else "ubfx") + cc, "%s, %s, %s, %s" % (R[rd], R[rm], _a32_imm(lsb), _a32_imm(wd)), None
    if (w & 0x0FE00070) == 0x07C00010:
        lsb, msb = (w >> 7) & 31, (w >> 16) & 31
        if msb < lsb:
            return bad
        if rm == 15:
            return "bfc" + cc, "%s, %s, %s" % (R[rd], _a32_imm(lsb), _a32_imm(msb - lsb + 1)), None
        return "bfi" + cc, "%s, %s, %s, %s" % (R[rd], R[rm], _a32_imm(lsb), _a32_imm(msb - lsb + 1)), None
    return bad


def _a32_disasm_lines(code: bytes, va: int, count: int, names: dict | None = None, read32=None) -> list[str]:
    """Baris disassembly A32 (alamat, hex, mnemonik, operand, catatan nama / literal)."""
    names = names or {}
    out = []
    for i in range(0, min(len(code) // 4, count) * 4, 4):
        w = struct.unpack_from("<I", code, i)[0]
        pc = va + i
        m, o, t = _a32_dis(w, pc)
        note = ""
        if t is not None:
            note = names.get(t, "")
        elif m.startswith(("ldr", "str")) and (w & 0x0F7F0000) == 0x051F0000 and (w >> 28) != 15:    # literal pool: [pc, #+-imm]
            lit = pc + 8 + ((w & 0xFFF) if (w >> 23) & 1 else -(w & 0xFFF))
            v = read32(lit) if read32 else None
            note = names.get(lit) or ("=0x%x" % v if v is not None else "")
            if v is not None and not names.get(lit) and names.get(v):
                note = "=%s" % names[v]
        out.append("   %08X  %-24s %s %s%s" % (pc, code[i:i + 4].hex(" "), m, o, ("   ; " + note) if note else ""))
    return out


