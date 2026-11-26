# rea_triage bagian 48/48: disasm_a64_neon. Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.59 [A1]: disassembler AArch64 bawaan, tambahan Advanced SIMD (NEON) + AES/SHA + ld/st struktur -----------------------
# Dipanggil dari `_a64_dis` untuk kata yang sebelumnya menjadi `.word`. Murni stdlib. Dipetakan dari ARM ARM (C4.1.x); BELUM dibandingkan dengan capstone
# di lingkungan pembuatnya (capstone tidak ada di sana): jalankan `test_a64_vs_capstone.py` di PC yang punya capstone.
_NEON_T = {(0, 0): "8b", (0, 1): "16b", (1, 0): "4h", (1, 1): "8h", (2, 0): "2s", (2, 1): "4s", (3, 0): "1d", (3, 1): "2d"}
_NEON_EL = ("b", "h", "s", "d")
_NEON_I3 = {   # opcode -> (nama U=0, nama U=1, ukuran elemen yang sah)
    0x00: ("shadd", "uhadd", (0, 1, 2)), 0x01: ("sqadd", "uqadd", (0, 1, 2, 3)), 0x02: ("srhadd", "urhadd", (0, 1, 2)),
    0x04: ("shsub", "uhsub", (0, 1, 2)), 0x05: ("sqsub", "uqsub", (0, 1, 2, 3)), 0x06: ("cmgt", "cmhi", (0, 1, 2, 3)),
    0x07: ("cmge", "cmhs", (0, 1, 2, 3)), 0x08: ("sshl", "ushl", (0, 1, 2, 3)), 0x09: ("sqshl", "uqshl", (0, 1, 2, 3)),
    0x0A: ("srshl", "urshl", (0, 1, 2, 3)), 0x0B: ("sqrshl", "uqrshl", (0, 1, 2, 3)), 0x0C: ("smax", "umax", (0, 1, 2)),
    0x0D: ("smin", "umin", (0, 1, 2)), 0x0E: ("sabd", "uabd", (0, 1, 2)), 0x0F: ("saba", "uaba", (0, 1, 2)),
    0x10: ("add", "sub", (0, 1, 2, 3)), 0x11: ("cmtst", "cmeq", (0, 1, 2, 3)), 0x12: ("mla", "mls", (0, 1, 2)),
    0x13: ("mul", "pmul", (0, 1, 2)), 0x14: ("smaxp", "umaxp", (0, 1, 2)), 0x15: ("sminp", "uminp", (0, 1, 2)),
    0x16: ("sqdmulh", "sqrdmulh", (1, 2)), 0x17: ("addp", None, (0, 1, 2, 3)),
}
_NEON_F3 = {   # (opcode, U, bit23) -> nama
    (0x18, 0, 0): "fmaxnm", (0x18, 0, 1): "fminnm", (0x18, 1, 0): "fmaxnmp", (0x18, 1, 1): "fminnmp", (0x19, 0, 0): "fmla", (0x19, 0, 1): "fmls",
    (0x1A, 0, 0): "fadd", (0x1A, 0, 1): "fsub", (0x1A, 1, 0): "faddp", (0x1A, 1, 1): "fabd", (0x1B, 0, 0): "fmulx", (0x1B, 1, 0): "fmul",
    (0x1C, 0, 0): "fcmeq", (0x1C, 1, 0): "fcmge", (0x1C, 1, 1): "fcmgt", (0x1D, 1, 0): "facge", (0x1D, 1, 1): "facgt",
    (0x1E, 0, 0): "fmax", (0x1E, 0, 1): "fmin", (0x1E, 1, 0): "fmaxp", (0x1E, 1, 1): "fminp", (0x1F, 0, 0): "frecps", (0x1F, 0, 1): "frsqrts", (0x1F, 1, 0): "fdiv",
}
_NEON_D3 = (("saddl", "uaddl"), ("saddw", "uaddw"), ("ssubl", "usubl"), ("ssubw", "usubw"), ("addhn", "raddhn"), ("sabal", "uabal"), ("subhn", "rsubhn"),
            ("sabdl", "uabdl"), ("smlal", "umlal"), ("sqdmlal", None), ("smlsl", "umlsl"), ("sqdmlsl", None), ("smull", "umull"), ("sqdmull", None), ("pmull", None))
_NEON_F2 = {   # (opcode, U, bit23) -> nama (dua-register FP, bentuk T sz,Q)
    (0x0C, 0, 1): "fcmgt", (0x0C, 1, 1): "fcmge", (0x0D, 0, 1): "fcmeq", (0x0D, 1, 1): "fcmle", (0x0E, 0, 1): "fcmlt", (0x0F, 0, 1): "fabs", (0x0F, 1, 1): "fneg",
    (0x18, 0, 0): "frintn", (0x18, 0, 1): "frintp", (0x18, 1, 0): "frinta", (0x19, 0, 0): "frintm", (0x19, 0, 1): "frintz", (0x19, 1, 0): "frintx", (0x19, 1, 1): "frinti",
    (0x1A, 0, 0): "fcvtns", (0x1A, 0, 1): "fcvtps", (0x1A, 1, 0): "fcvtnu", (0x1A, 1, 1): "fcvtpu", (0x1B, 0, 0): "fcvtms", (0x1B, 0, 1): "fcvtzs",
    (0x1B, 1, 0): "fcvtmu", (0x1B, 1, 1): "fcvtzu", (0x1C, 0, 0): "fcvtas", (0x1C, 1, 0): "fcvtau", (0x1D, 0, 0): "scvtf", (0x1D, 1, 0): "ucvtf",
    (0x1D, 0, 1): "frecpe", (0x1D, 1, 1): "frsqrte", (0x1F, 1, 1): "fsqrt",
}


def _neon_v(n: int, t: str) -> str:
    return "v%d.%s" % (n, t)


def _neon_fpimm(n: int) -> str:
    a, b, cd, e = (n >> 7) & 1, (n >> 6) & 1, (n >> 4) & 3, n & 15
    v = (16 + e) / 16.0 * 2.0 ** ((((b ^ 1) << 2) | cd) - 3)
    return "#%.8f" % (-v if a else v)


def _neon_three_same(w: int):
    q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 11) & 31
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    if op == 3:                                                                # logica bitwise
        t = "16b" if q else "8b"
        nm = (("and", "bic", "orr", "orn"), ("eor", "bsl", "bit", "bif"))[u][size]
        if nm == "orr" and rn == rm:
            return "mov", "%s, %s" % (_neon_v(rd, t), _neon_v(rn, t)), None
        return nm, "%s, %s, %s" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t)), None
    if op < 0x18:
        ent = _NEON_I3.get(op)
        if not ent:
            return None
        nm = ent[u]
        if nm is None or size not in ent[2] or (size == 3 and not q):
            return None
        if op == 0x13 and u and size != 0:                                    # PMUL hanya byte
            return None
        t = _NEON_T[(size, q)]
        return nm, "%s, %s, %s" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t)), None
    if (size & 1) == 0 and ((op == 0x1D and not u) or (op == 0x19 and u)):     # v99.65: FMLAL / FMLSL (U = 0), FMLAL2 / FMLSL2 (U = 1); FP16 melebar ke FP32
        nm = (("fmlal", "fmlsl"), ("fmlal2", "fmlsl2"))[u][size >> 1]
        return nm, "%s, %s, %s" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "4h" if q else "2h"), _neon_v(rm, "4h" if q else "2h")), None
    nm = _NEON_F3.get((op, u, size >> 1))
    if not nm or ((size & 1) and not q):
        return None
    t = _NEON_T[(2 + (size & 1), q)]
    return nm, "%s, %s, %s" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t)), None


def _neon_three_diff(w: int):
    q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 12) & 15
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    if op > 14:
        return None
    nm = _NEON_D3[op][u]
    if nm is None:
        return None
    if op == 14:                                                               # PMULL (8h <- 8b) atau PMULL 1q <- 1d (kripto)
        if size == 0:
            ta, tb = "8h", ("16b" if q else "8b")
        elif size == 3:
            ta, tb = "1q", ("2d" if q else "1d")
        else:
            return None
        return nm + ("2" if q else ""), "%s, %s, %s" % (_neon_v(rd, ta), _neon_v(rn, tb), _neon_v(rm, tb)), None
    if size == 3 or (op in (9, 11, 13) and size == 0):
        return None
    ta, tb = _NEON_T[(size + 1, 1)], _NEON_T[(size, q)]
    nm += "2" if q else ""
    if op in (4, 6):                                                           # addhn / subhn: tujuan sempit, sumber lebar
        return nm, "%s, %s, %s" % (_neon_v(rd, tb), _neon_v(rn, ta), _neon_v(rm, ta)), None
    if op in (1, 3):                                                           # saddw / ssubw
        return nm, "%s, %s, %s" % (_neon_v(rd, ta), _neon_v(rn, ta), _neon_v(rm, tb)), None
    return nm, "%s, %s, %s" % (_neon_v(rd, ta), _neon_v(rn, tb), _neon_v(rm, tb)), None


def _neon_two_misc(w: int):
    q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 12) & 31
    rd, rn = w & 31, (w >> 5) & 31
    t = _NEON_T[(size, q)]
    d, s = _neon_v(rd, t), _neon_v(rn, t)
    if op >= 0x16 or (op in (0x0C, 0x0D, 0x0E, 0x0F) and size >> 1):
        b23, sz = size >> 1, size & 1
        if op == 0x16 and not b23:                                              # FCVTN / FCVTXN
            if u:
                if not sz:
                    return None
                return "fcvtxn" + ("2" if q else ""), "%s, %s" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "2d")), None
            dst, src = (("8h" if q else "4h"), "4s") if not sz else (("4s" if q else "2s"), "2d")
            return "fcvtn" + ("2" if q else ""), "%s, %s" % (_neon_v(rd, dst), _neon_v(rn, src)), None
        if op == 0x17 and not b23 and not u:                                    # FCVTL
            dst, src = ("4s", "8h" if q else "4h") if not sz else ("2d", "4s" if q else "2s")
            return "fcvtl" + ("2" if q else ""), "%s, %s" % (_neon_v(rd, dst), _neon_v(rn, src)), None
        nm = _NEON_F2.get((op, u, b23))
        if nm is None or (sz and not q):
            return None
        tt = _NEON_T[(2 + sz, q)]
        extra = ", #0.0" if op in (0x0C, 0x0D, 0x0E) else ""
        return nm, "%s, %s%s" % (_neon_v(rd, tt), _neon_v(rn, tt), extra), None
    if op in (0x12, 0x14):                                                     # XTN / SQXTUN / SQXTN / UQXTN
        if size == 3:
            return None
        nm = ("xtn", "sqxtun") if op == 0x12 else ("sqxtn", "uqxtn")
        return nm[u] + ("2" if q else ""), "%s, %s" % (_neon_v(rd, t), _neon_v(rn, _NEON_T[(size + 1, 1)])), None
    if op == 0x13 and u:                                                       # SHLL / SHLL2
        if size == 3:
            return None
        return "shll" + ("2" if q else ""), "%s, %s, #%d" % (_neon_v(rd, _NEON_T[(size + 1, 1)]), s, 8 << size), None
    if op in (2, 6) and size < 3:                                              # SADDLP / UADDLP / SADALP / UADALP
        nm = (("saddlp", "uaddlp"), ("sadalp", "uadalp"))[op == 6][u]
        return nm, "%s, %s" % (_neon_v(rd, _NEON_T[(size + 1, q)]), s), None
    zero = {(8, 0): "cmgt", (8, 1): "cmge", (9, 0): "cmeq", (9, 1): "cmle", (10, 0): "cmlt"}.get((op, u))
    if zero:
        if size == 3 and not q:
            return None
        return zero, "%s, %s, #0" % (d, s), None
    if op == 5:
        if not u:
            return ("cnt", "%s, %s" % (d, s), None) if size == 0 else None
        if size == 0:
            return "mvn", "%s, %s" % (d, s), None
        return ("rbit", "%s, %s" % (_neon_v(rd, "16b" if q else "8b"), _neon_v(rn, "16b" if q else "8b")), None) if size == 1 else None   # v99.65: arrangement selalu 8b / 16b (sebelumnya .4h / .8h)
    nm = {(0, 0): "rev64", (0, 1): "rev32", (1, 0): "rev16", (3, 0): "suqadd", (3, 1): "usqadd", (4, 0): "cls", (4, 1): "clz",
          (7, 0): "sqabs", (7, 1): "sqneg", (11, 0): "abs", (11, 1): "neg"}.get((op, u))
    if nm is None:
        return None
    lim = {"rev64": 2, "rev32": 1, "rev16": 0, "cls": 2, "clz": 2}.get(nm, 3)
    if size > lim or (size == 3 and not q):
        return None
    return nm, "%s, %s" % (d, s), None


def _neon_across(w: int):
    q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 12) & 31
    rd, rn = w & 31, (w >> 5) & 31
    if op in (0x0C, 0x0F):
        if not u or not q or (size & 1):
            return None
        nm = {(0x0C, 0): "fmaxnmv", (0x0C, 2): "fminnmv", (0x0F, 0): "fmaxv", (0x0F, 2): "fminv"}.get((op, size & 2))
        return (nm, "s%d, %s" % (rd, _neon_v(rn, "4s")), None) if nm else None
    nm = {(3, 0): "saddlv", (3, 1): "uaddlv", (0x0A, 0): "smaxv", (0x0A, 1): "umaxv", (0x1A, 0): "sminv", (0x1A, 1): "uminv", (0x1B, 0): "addv"}.get((op, u))
    if nm is None or size == 3 or (size == 2 and not q):
        return None
    t = _NEON_T[(size, q)]
    dst = "bhsd"[size + 1] if nm in ("saddlv", "uaddlv") else "bhsd"[size]
    return nm, "%s%d, %s" % (dst, rd, _neon_v(rn, t)), None


def _neon_copy(w: int):
    q, op, imm5, imm4 = (w >> 30) & 1, (w >> 29) & 1, (w >> 16) & 31, (w >> 11) & 15
    rd, rn = w & 31, (w >> 5) & 31
    if not imm5:
        return None
    k = (imm5 & -imm5).bit_length() - 1                                        # 0 b, 1 h, 2 s, 3 d
    if k > 3:
        return None
    idx = imm5 >> (k + 1)
    el = _NEON_EL[k]
    if op:                                                                     # INS (elemen)
        if not q:
            return None
        return "mov", "v%d.%s[%d], v%d.%s[%d]" % (rd, el, idx, rn, el, imm4 >> k), None
    if imm4 == 0:                                                              # DUP (elemen)
        if k == 3 and not q:
            return None
        return "dup", "%s, v%d.%s[%d]" % (_neon_v(rd, _NEON_T[(k, q)]), rn, el, idx), None
    if imm4 == 1:                                                              # DUP (umum)
        if k == 3 and not q:
            return None
        return "dup", "%s, %s" % (_neon_v(rd, _NEON_T[(k, q)]), _a64_r(rn, 1 if k == 3 else 0)), None
    if imm4 == 3:                                                              # INS (umum)
        if not q:
            return None
        return "mov", "v%d.%s[%d], %s" % (rd, el, idx, _a64_r(rn, 1 if k == 3 else 0)), None
    if imm4 == 5:                                                              # SMOV
        if k == 3 or (k == 2 and not q):
            return None
        return "smov", "%s, v%d.%s[%d]" % (_a64_r(rd, q), rn, el, idx), None
    if imm4 == 7:                                                              # UMOV
        if (k == 3) != bool(q):
            return None
        return ("mov" if k >= 2 else "umov"), "%s, v%d.%s[%d]" % (_a64_r(rd, q), rn, el, idx), None
    return None


def _neon_modimm(w: int):
    q, op, cmode = (w >> 30) & 1, (w >> 29) & 1, (w >> 12) & 15
    rd = w & 31
    imm = (((w >> 16) & 7) << 5) | ((w >> 5) & 31)
    t32, t16, t8 = ("4s" if q else "2s"), ("8h" if q else "4h"), ("16b" if q else "8b")
    if cmode < 8:
        sh = 8 * (cmode >> 1)
        t = _neon_v(rd, t32)
        nm = (("movi", "orr"), ("mvni", "bic"))[op][cmode & 1]
        return nm, "%s, %s%s" % (t, _a32_imm(imm), (", lsl #%d" % sh) if sh else ""), None
    if cmode < 12:
        sh = 8 * ((cmode >> 1) & 1)
        t = _neon_v(rd, t16)
        nm = (("movi", "orr"), ("mvni", "bic"))[op][cmode & 1]
        return nm, "%s, %s%s" % (t, _a32_imm(imm), (", lsl #%d" % sh) if sh else ""), None
    if cmode < 14:
        return ("mvni" if op else "movi"), "%s, %s, msl #%d" % (_neon_v(rd, t32), _a32_imm(imm), 8 if cmode == 12 else 16), None
    if cmode == 14:
        if not op:
            return "movi", "%s, %s" % (_neon_v(rd, t8), _a32_imm(imm)), None
        v = 0
        for i in range(8):
            if (imm >> i) & 1:
                v |= 0xFF << (8 * i)
        return "movi", ("v%d.2d, #0x%x" if q else "d%d, #0x%x") % (rd, v), None
    if not op:
        return "fmov", "%s, %s" % (_neon_v(rd, t32), _neon_fpimm(imm)), None
    if not q:
        return None
    return "fmov", "%s, %s" % (_neon_v(rd, "2d"), _neon_fpimm(imm)), None


def _neon_shift_imm(w: int):
    q, u, immh, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 19) & 15, (w >> 11) & 31
    rd, rn = w & 31, (w >> 5) & 31
    immhb = (w >> 16) & 0x7F
    hb = immh.bit_length() - 1
    es = 8 << hb
    right, left = 2 * es - immhb, immhb - es
    R = {0x00: ("sshr", "ushr"), 0x02: ("ssra", "usra"), 0x04: ("srshr", "urshr"), 0x06: ("srsra", "ursra"), 0x08: (None, "sri")}
    L = {0x0A: ("shl", "sli"), 0x0C: (None, "sqshlu"), 0x0E: ("sqshl", "uqshl")}
    if op in R or op in L:
        nm = (R.get(op) or L[op])[u]
        if nm is None or (hb == 3 and not q):
            return None
        t = _NEON_T[(hb, q)]
        return nm, "%s, %s, #%d" % (_neon_v(rd, t), _neon_v(rn, t), right if op in R else left), None
    if op in (0x10, 0x11, 0x12, 0x13):                                         # (R)SHRN, SQ(R)SHRUN, SQ(R)SHRN, UQ(R)SHRN
        if hb > 2:
            return None
        nm = {0x10: ("shrn", "sqshrun"), 0x11: ("rshrn", "sqrshrun"), 0x12: ("sqshrn", "uqshrn"), 0x13: ("sqrshrn", "uqrshrn")}[op][u]
        return nm + ("2" if q else ""), "%s, %s, #%d" % (_neon_v(rd, _NEON_T[(hb, q)]), _neon_v(rn, _NEON_T[(hb + 1, 1)]), right), None
    if op == 0x14:                                                             # SSHLL / USHLL (SXTL / UXTL bila geser 0)
        if hb > 2:
            return None
        sf = "2" if q else ""
        dst, src = _neon_v(rd, _NEON_T[(hb + 1, 1)]), _neon_v(rn, _NEON_T[(hb, q)])
        if left == 0:
            return ("sxtl", "uxtl")[u] + sf, "%s, %s" % (dst, src), None
        return ("sshll", "ushll")[u] + sf, "%s, %s, #%d" % (dst, src, left), None
    if op in (0x1C, 0x1F):                                                     # SCVTF/UCVTF / FCVTZS/FCVTZU fixed-point
        if hb not in (2, 3) or (hb == 3 and not q):
            return None
        nm = (("scvtf", "ucvtf") if op == 0x1C else ("fcvtzs", "fcvtzu"))[u]
        t = _NEON_T[(hb, q)]
        return nm, "%s, %s, #%d" % (_neon_v(rd, t), _neon_v(rn, t), right), None
    return None


def _neon_indexed(w: int):
    q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 12) & 15
    l, m, h = (w >> 21) & 1, (w >> 20) & 1, (w >> 11) & 1
    rd, rn, rm4 = w & 31, (w >> 5) & 31, (w >> 16) & 15
    if size == 2 and (op, u) in ((0, 0), (4, 0), (8, 1), (12, 1)):             # v99.65: FMLAL / FMLSL / FMLAL2 / FMLSL2 (indexed); Rm 4 bit, indeks H:L:M
        nm = {(0, 0): "fmlal", (4, 0): "fmlsl", (8, 1): "fmlal2", (12, 1): "fmlsl2"}[(op, u)]
        return nm, "%s, %s, v%d.h[%d]" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "4h" if q else "2h"), rm4, (h << 2) | (l << 1) | m), None
    if size == 0 and op in (1, 5, 9):                                          # v99.65: FP16 indexed (FMLA / FMLS / FMUL / FMULX); Rm 4 bit, indeks H:L:M
        nm = {(1, 0): "fmla", (5, 0): "fmls", (9, 0): "fmul", (9, 1): "fmulx"}.get((op, u))
        if nm is None:
            return None
        t = "8h" if q else "4h"
        return nm, "%s, %s, v%d.h[%d]" % (_neon_v(rd, t), _neon_v(rn, t), rm4, (h << 2) | (l << 1) | m), None
    if op == 15 and not u and size in (0, 1, 2, 3):                            # v99.65: SUDOT / BFDOT / USDOT (indexed, Rm = M:Rm, indeks H:L) dan BFMLALB / T (indexed)
        rm5, i2 = (m << 4) | rm4, (h << 1) | l
        if size == 0:
            return "sudot", "%s, %s, v%d.4b[%d]" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "16b" if q else "8b"), rm5, i2), None
        if size == 1:
            return "bfdot", "%s, %s, v%d.2h[%d]" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "8h" if q else "4h"), rm5, i2), None
        if size == 2:
            return "usdot", "%s, %s, v%d.4b[%d]" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "16b" if q else "8b"), rm5, i2), None
        return ("bfmlalt" if q else "bfmlalb"), "v%d.4s, v%d.8h, v%d.h[%d]" % (rd, rn, rm4, (h << 2) | (l << 1) | m), None
    if u and op in (1, 3, 5, 7) and size in (1, 2):                            # v99.65: FCMLA (indexed); op = 0 rr 1; size 2 (s) size 2: Q = 1 dan L = 0; size 1 Q = 0 hanya H = 0
        if size == 2 and (not q or l):
            return None
        if size == 1 and not q and h:                                          # 4h: hanya 2 pasangan kompleks, indeks H:L harus <= 1
            return None
        rot = ((op >> 1) & 3) * 90
        t = _NEON_T[(size, q)]
        if size == 1:
            return "fcmla", "%s, %s, v%d.h[%d], #%d" % (_neon_v(rd, t), _neon_v(rn, t), (m << 4) | rm4, (h << 1) | l, rot), None
        return "fcmla", "%s, %s, v%d.s[%d], #%d" % (_neon_v(rd, t), _neon_v(rn, t), (m << 4) | rm4, h, rot), None
    if size == 1:
        rm, idx, el = rm4, (h << 2) | (l << 1) | m, "h"
    elif size == 2:
        rm, idx, el = (m << 4) | rm4, (h << 1) | l, "s"
    elif size == 3:
        rm, idx, el = (m << 4) | rm4, h, "d"
        if l:
            return None
    else:
        return None
    if op in (1, 5, 9):                                                        # FMLA / FMLS / FMUL / FMULX (size 10 = s, 11 = d)
        if size == 1 or (size == 3 and not q):
            return None
        nm = {(1, 0): "fmla", (5, 0): "fmls", (9, 0): "fmul", (9, 1): "fmulx"}.get((op, u))
        if nm is None:
            return None
        t = _NEON_T[(size, q)]
        return nm, "%s, %s, v%d.%s[%d]" % (_neon_v(rd, t), _neon_v(rn, t), rm, el, idx), None
    if op == 14 and size == 2:                                                 # SDOT / UDOT (indexed)
        return ("udot" if u else "sdot"), "%s, %s, v%d.4b[%d]" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "16b" if q else "8b"), rm, idx), None
    if op in (0, 4, 8, 12, 13, 15) and size != 3:                              # MLA / MLS / MUL / SQDMULH / SQRDMULH / SQRDMLAH / SQRDMLSH
        if op in (13, 15) and u and size not in (1, 2):
            return None
        nm = {(0, 1): "mla", (4, 1): "mls", (8, 0): "mul", (12, 0): "sqdmulh", (13, 0): "sqrdmulh", (13, 1): "sqrdmlah", (15, 1): "sqrdmlsh"}.get((op, u))
        if nm is None:
            return None
        t = _NEON_T[(size, q)]
        return nm, "%s, %s, v%d.%s[%d]" % (_neon_v(rd, t), _neon_v(rn, t), rm, el, idx), None
    if op in (2, 3, 6, 7, 10, 11) and size != 3:                               # long: SMLAL .. SQDMULL
        nm = {(2, 0): "smlal", (2, 1): "umlal", (6, 0): "smlsl", (6, 1): "umlsl", (10, 0): "smull", (10, 1): "umull",
              (3, 0): "sqdmlal", (7, 0): "sqdmlsl", (11, 0): "sqdmull"}.get((op, u))
        if nm is None:
            return None
        return nm + ("2" if q else ""), "%s, %s, v%d.%s[%d]" % (_neon_v(rd, _NEON_T[(size + 1, 1)]), _neon_v(rn, _NEON_T[(size, q)]), rm, el, idx), None
    return None


def _neon_ldst(w: int):
    q, l = (w >> 30) & 1, (w >> 22) & 1
    rt, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    post = (w >> 23) & 1
    size = (w >> 10) & 3
    base = _a64_r(rn, 1, True)

    def lst(n, t, idx=None):
        s = "{" + ", ".join("v%d.%s" % ((rt + i) & 31, t) for i in range(n)) + "}"
        return s + ("[%d]" % idx if idx is not None else "")

    def mem(nbytes):
        if not post:
            return "[%s]" % base
        return "[%s], %s" % (base, ("#%d" % nbytes) if rm == 31 else _a64_r(rm, 1))

    if not (w >> 24) & 1:                                                      # banyak struktur
        if (w >> 21) & 1 or (not post and rm):
            return None
        op = (w >> 12) & 15
        ent = {0: (4, 4), 2: (1, 4), 4: (3, 3), 6: (1, 3), 7: (1, 1), 8: (2, 2), 10: (1, 2)}.get(op)
        if not ent:
            return None
        selem, nreg = ent
        if size == 3 and not q and selem > 1:
            return None
        t = _NEON_T[(size, q)]
        return ("ld%d" if l else "st%d") % selem, "%s, %s" % (lst(nreg, t), mem(nreg * (16 if q else 8))), None
    if not post and rm:
        return None
    r, op, s = (w >> 21) & 1, (w >> 13) & 7, (w >> 12) & 1
    selem = (((op & 1) << 1) | r) + 1
    if op >= 6:                                                                # LDnR
        if not l or s:
            return None
        t = _NEON_T[(size, q)]
        return "ld%dr" % selem, "%s, %s" % (lst(selem, t), mem(selem << size)), None
    base_t = op >> 1
    if base_t == 0:
        idx, el, es = (q << 3) | (s << 2) | size, "b", 1
    elif base_t == 1:
        if size & 1:
            return None
        idx, el, es = (q << 2) | (s << 1) | (size >> 1), "h", 2
    else:
        if size == 0:
            idx, el, es = (q << 1) | s, "s", 4
        elif size == 1 and not s:
            idx, el, es = q, "d", 8
        else:
            return None
    return ("ld%d" if l else "st%d") % selem, "%s, %s" % (lst(selem, el, idx), mem(selem * es)), None


def _a64_neon(w: int):
    """Satu kata Advanced SIMD / kripto AES-SHA -> (mnemonik, operand, None) atau None bila bukan / tidak dikenal."""
    if (w & 0xFFFF0C00) == 0x4E280800:                                         # AES
        nm = {4: "aese", 5: "aesd", 6: "aesmc", 7: "aesimc"}.get((w >> 12) & 31)
        return (nm, "v%d.16b, v%d.16b" % (w & 31, (w >> 5) & 31), None) if nm else None
    if (w & 0xFFE08C00) == 0x5E000000:                                         # SHA 3 register
        rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
        op = (w >> 12) & 7
        if op <= 2:
            return ("sha1c", "sha1p", "sha1m")[op], "q%d, s%d, v%d.4s" % (rd, rn, rm), None
        if op == 3:
            return "sha1su0", "v%d.4s, v%d.4s, v%d.4s" % (rd, rn, rm), None
        if op in (4, 5):
            return ("sha256h", "sha256h2")[op - 4], "q%d, q%d, v%d.4s" % (rd, rn, rm), None
        if op == 6:
            return "sha256su1", "v%d.4s, v%d.4s, v%d.4s" % (rd, rn, rm), None
        return None
    if (w & 0xFFFF0C00) == 0x5E280800:                                         # SHA 2 register
        rd, rn, op = w & 31, (w >> 5) & 31, (w >> 12) & 31
        if op == 0:
            return "sha1h", "s%d, s%d" % (rd, rn), None
        if op in (1, 2):
            return ("sha1su1", "sha256su0")[op - 1], "v%d.4s, v%d.4s" % (rd, rn), None
        return None
    if (w & 0xFF000000) == 0xCE000000:                                         # v99.61: SHA512 / EOR3 / BCAX / XAR / RAX1
        rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
        if (w & 0xFFE0FC00) == 0xCE608000:
            return "sha512h", "q%d, q%d, v%d.2d" % (rd, rn, rm), None
        if (w & 0xFFE0FC00) == 0xCE608400:
            return "sha512h2", "q%d, q%d, v%d.2d" % (rd, rn, rm), None
        if (w & 0xFFE0FC00) == 0xCE608800:
            return "sha512su1", "v%d.2d, v%d.2d, v%d.2d" % (rd, rn, rm), None
        if (w & 0xFFE0FC00) == 0xCE608C00:
            return "rax1", "v%d.2d, v%d.2d, v%d.2d" % (rd, rn, rm), None
        if (w & 0xFFFFFC00) == 0xCEC08000:
            return "sha512su0", "v%d.2d, v%d.2d" % (rd, rn), None
        if (w & 0xFFC08000) in (0xCE000000, 0xCE200000):
            nm = "eor3" if not (w >> 21) & 1 else "bcax"
            return nm, "v%d.16b, v%d.16b, v%d.16b, v%d.16b" % (rd, rn, rm, (w >> 10) & 31), None
        if (w & 0xFFFFFC00) == 0xCEC08400:                                     # v99.62: SM4E
            return "sm4e", "v%d.4s, v%d.4s" % (rd, rn), None
        if (w & 0xFFE0FC00) in (0xCE60C000, 0xCE60C400, 0xCE60C800):
            nm = {0xC000: "sm3partw1", 0xC400: "sm3partw2", 0xC800: "sm4ekey"}[w & 0xFC00]
            return nm, "v%d.4s, v%d.4s, v%d.4s" % (rd, rn, rm), None
        if (w & 0xFFE08000) == 0xCE400000:                                     # SM3SS1
            return "sm3ss1", "v%d.4s, v%d.4s, v%d.4s, v%d.4s" % (rd, rn, rm, (w >> 10) & 31), None
        if (w & 0xFFE0C000) == 0xCE408000:                                     # SM3TT1A/1B/2A/2B
            return ("sm3tt1a", "sm3tt1b", "sm3tt2a", "sm3tt2b")[(w >> 10) & 3], "v%d.4s, v%d.4s, v%d.s[%d]" % (rd, rn, rm, (w >> 12) & 3), None
        if (w & 0xFFE00000) == 0xCE800000:
            return "xar", "v%d.2d, v%d.2d, v%d.2d, #%d" % (rd, rn, rm, (w >> 10) & 63), None
        return None
    if (w & 0xDE000000) == 0x5E000000:                                         # v99.60: Advanced SIMD skalar
        return _neon_scalar(w)
    if (w & 0x9F000000) == 0x0E000000:
        b21, b10 = (w >> 21) & 1, (w >> 10) & 1
        if b21 and b10:
            return _neon_three_same(w)
        if b21 and not (w >> 10) & 3:
            return _neon_three_diff(w)
        if b21 and (w >> 10) & 3 == 2:
            if (w >> 17) & 15 == 0:
                return _neon_two_misc(w)
            if (w >> 17) & 15 == 8:
                return _neon_across(w)
            return None
        if not b21 and (w >> 15) & 1 == 0:
            q, u, op2 = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3
            rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
            if b10:
                return _neon_copy(w) if (w >> 21) & 7 == 0 else None
            if (w >> 10) & 3 == 2 and not u:                                   # ZIP / UZP / TRN
                nm = {1: "uzp1", 2: "trn1", 3: "zip1", 5: "uzp2", 6: "trn2", 7: "zip2"}.get((w >> 12) & 7)
                if not nm or (op2 == 3 and not q):
                    return None
                t = _NEON_T[(op2, q)]
                return nm, "%s, %s, %s" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t)), None
            if u and op2 == 0:                                                 # EXT (bit 10 = 0 sudah pasti di sini)
                imm4 = (w >> 11) & 15
                if not q and imm4 > 7:
                    return None
                t = "16b" if q else "8b"
                return "ext", "%s, %s, %s, #%d" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t), imm4), None
            if not u and (w >> 10) & 3 == 0 and op2 == 0:                      # TBL / TBX
                t = "16b" if q else "8b"
                n = ((w >> 13) & 3) + 1
                lst = "{" + ", ".join("v%d.16b" % ((rn + i) & 31) for i in range(n)) + "}"
                return ("tbx" if (w >> 12) & 1 else "tbl"), "%s, %s, %s" % (_neon_v(rd, t), lst, _neon_v(rm, t)), None
        if not b21 and (w >> 15) & 1 and b10:                                  # tiga sama extra: SQRDMLAH / SQRDMLSH / SDOT / UDOT
            q, u, size, op = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 11) & 15
            rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
            if op == 2 and size == 2:
                return ("udot" if u else "sdot"), "%s, %s, %s" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "16b" if q else "8b"), _neon_v(rm, "16b" if q else "8b")), None
            if op in (0, 1) and u and size in (1, 2):
                t = _NEON_T[(size, q)]
                return ("sqrdmlah", "sqrdmlsh")[op], "%s, %s, %s" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t)), None
            if u and op >= 8 and op != 13 and op != 15 and size != 0 and not (size == 3 and not q):   # v99.65: FCMLA (op 8-11) / FCADD (op 12, 14)
                t = _NEON_T[(size, q)]
                if op < 12:
                    return "fcmla", "%s, %s, %s, #%d" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t), (op & 3) * 90), None
                return "fcadd", "%s, %s, %s, #%d" % (_neon_v(rd, t), _neon_v(rn, t), _neon_v(rm, t), 270 if op == 14 else 90), None
            if size == 2 and (u, op) == (0, 3):                                                     # v99.65: USDOT (i8mm)
                return "usdot", "%s, %s, %s" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "16b" if q else "8b"), _neon_v(rm, "16b" if q else "8b")), None
            if size == 2 and q and (u, op) in ((0, 4), (0, 5), (1, 4)):                             # v99.65: SMMLA / USMMLA / UMMLA (i8mm, hanya Q = 1)
                return {(0, 4): "smmla", (0, 5): "usmmla", (1, 4): "ummla"}[(u, op)], "v%d.4s, v%d.16b, v%d.16b" % (rd, rn, rm), None
            if u and op == 15 and size == 1:                                                        # v99.65: bf16
                return "bfdot", "%s, %s, %s" % (_neon_v(rd, "4s" if q else "2s"), _neon_v(rn, "8h" if q else "4h"), _neon_v(rm, "8h" if q else "4h")), None
            if u and op == 13 and size == 1 and q:
                return "bfmmla", "v%d.4s, v%d.8h, v%d.8h" % (rd, rn, rm), None
            if u and op == 15 and size == 3:                                                        # BFMLALB (Q = 0) / BFMLALT (Q = 1)
                return ("bfmlalt" if q else "bfmlalb"), "v%d.4s, v%d.8h, v%d.8h" % (rd, rn, rm), None
        return None
    if (w & 0x9F000000) == 0x0F000000:
        if (w >> 10) & 1:
            if (w >> 23) & 1:
                return None
            if (w >> 19) & 15:
                return _neon_shift_imm(w)
            return _neon_modimm(w) if not (w >> 11) & 1 else None
        return _neon_indexed(w)
    if (w & 0xBF000000) in (0x0C000000, 0x0D000000):
        return _neon_ldst(w)
    return None


# ----------------------- v99.60: Advanced SIMD skalar (01 U 11110 / 01 U 11111) -----------------------
_NEON_SI3 = {  # opcode -> (nama U=0, nama U=1, ukuran sah)
    0x01: ("sqadd", "uqadd", (0, 1, 2, 3)), 0x05: ("sqsub", "uqsub", (0, 1, 2, 3)), 0x06: ("cmgt", "cmhi", (3,)), 0x07: ("cmge", "cmhs", (3,)),
    0x08: ("sshl", "ushl", (3,)), 0x09: ("sqshl", "uqshl", (0, 1, 2, 3)), 0x0A: ("srshl", "urshl", (3,)), 0x0B: ("sqrshl", "uqrshl", (0, 1, 2, 3)),
    0x10: ("add", "sub", (3,)), 0x11: ("cmtst", "cmeq", (3,)), 0x16: ("sqdmulh", "sqrdmulh", (1, 2)),
}
_NEON_SF3 = {(0x1B, 0, 0): "fmulx", (0x1C, 0, 0): "fcmeq", (0x1C, 1, 0): "fcmge", (0x1C, 1, 1): "fcmgt", (0x1D, 1, 0): "facge", (0x1D, 1, 1): "facgt",
             (0x1A, 1, 1): "fabd", (0x1F, 0, 0): "frecps", (0x1F, 0, 1): "frsqrts"}
_NEON_SF2 = {(0x0C, 0, 1): "fcmgt", (0x0C, 1, 1): "fcmge", (0x0D, 0, 1): "fcmeq", (0x0D, 1, 1): "fcmle", (0x0E, 0, 1): "fcmlt",
             (0x1A, 0, 0): "fcvtns", (0x1A, 0, 1): "fcvtps", (0x1A, 1, 0): "fcvtnu", (0x1A, 1, 1): "fcvtpu", (0x1B, 0, 0): "fcvtms", (0x1B, 0, 1): "fcvtzs",
             (0x1B, 1, 0): "fcvtmu", (0x1B, 1, 1): "fcvtzu", (0x1C, 0, 0): "fcvtas", (0x1C, 1, 0): "fcvtau", (0x1D, 0, 0): "scvtf", (0x1D, 1, 0): "ucvtf",
             (0x1D, 0, 1): "frecpe", (0x1D, 1, 1): "frsqrte", (0x1F, 0, 1): "frecpx"}


def _neon_scalar(w: int):
    """Advanced SIMD skalar -> (mnemonik, operand, None) atau None."""
    u, size, rd, rn, rm = (w >> 29) & 1, (w >> 22) & 3, w & 31, (w >> 5) & 31, (w >> 16) & 31
    L = "bhsd"
    if (w >> 24) & 1 == 0:
        op = (w >> 12) & 31 if (w >> 21) & 1 else None
        b21, lo = (w >> 21) & 1, (w >> 10) & 3
        if not b21:
            if not u and (w >> 10) & 1 and not (w >> 15) & 1 and (w >> 21) & 7 == 0 and (w >> 11) & 15 == 0:   # DUP skalar (alias MOV)
                imm5 = (w >> 16) & 31
                k = (imm5 & -imm5).bit_length() - 1 if imm5 else 9
                if k > 3:
                    return None
                return "mov", "%s%d, v%d.%s[%d]" % (L[k], rd, rn, _NEON_EL[k], imm5 >> (k + 1)), None
            return None
        if lo & 1:                                                             # tiga sama
            op = (w >> 11) & 31
            if op < 0x18:
                ent = _NEON_SI3.get(op)
                nm = ent[u] if ent else None
                if not nm or size not in ent[2]:
                    return None
                return nm, "%s%d, %s%d, %s%d" % (L[size], rd, L[size], rn, L[size], rm), None
            nm = _NEON_SF3.get((op, u, size >> 1))
            if not nm:
                return None
            c = L[2 + (size & 1)]
            return nm, "%s%d, %s%d, %s%d" % (c, rd, c, rn, c, rm), None
        if lo == 2:
            sub = (w >> 17) & 15
            op = (w >> 12) & 31
            if sub == 0:                                                       # dua-register misc
                if op in (0x12, 0x14):                                         # SQXTUN / SQXTN / UQXTN
                    if size == 3 or (op == 0x12 and not u):
                        return None
                    nm = "sqxtun" if op == 0x12 else ("sqxtn", "uqxtn")[u]
                    return nm, "%s%d, %s%d" % (L[size], rd, L[size + 1], rn), None
                if op == 0x16 and u and not size >> 1:                         # FCVTXN
                    return ("fcvtxn", "s%d, d%d" % (rd, rn), None) if size & 1 else None
                if op in (0x0C, 0x0D, 0x0E, 0x1A, 0x1B, 0x1C, 0x1D, 0x1F) and (op >= 0x1A or size >> 1):
                    nm = _NEON_SF2.get((op, u, size >> 1))
                    if not nm:
                        return None
                    c = L[2 + (size & 1)]
                    return nm, "%s%d, %s%d%s" % (c, rd, c, rn, ", #0.0" if op in (0x0C, 0x0D, 0x0E) else ""), None
                z = {(8, 0): "cmgt", (8, 1): "cmge", (9, 0): "cmeq", (9, 1): "cmle", (10, 0): "cmlt"}.get((op, u))
                if z:
                    return (z, "d%d, d%d, #0" % (rd, rn), None) if size == 3 else None
                if op == 0x0B:
                    return (("abs", "neg")[u], "d%d, d%d" % (rd, rn), None) if size == 3 else None
                nm = {(3, 0): "suqadd", (3, 1): "usqadd", (7, 0): "sqabs", (7, 1): "sqneg"}.get((op, u))
                return (nm, "%s%d, %s%d" % (L[size], rd, L[size], rn), None) if nm else None
            if sub == 8:                                                       # berpasangan
                op = (w >> 12) & 31
                if not u and op == 0x1B and size == 3:
                    return "addp", "d%d, v%d.2d" % (rd, rn), None
                nm = {(0x0C, 0): "fmaxnmp", (0x0C, 2): "fminnmp", (0x0D, 0): "faddp", (0x0F, 0): "fmaxp", (0x0F, 2): "fminp"}.get((op, size & 2))
                if u and nm:
                    return nm, ("d%d, v%d.2d" if size & 1 else "s%d, v%d.2s") % (rd, rn), None
            return None
        return None
    # ---- 01 U 11111: shift imm / indexed
    if (w >> 10) & 1:
        immh, op = (w >> 19) & 15, (w >> 11) & 31
        if (w >> 23) & 1 or not immh:
            return None
        immhb, hb = (w >> 16) & 0x7F, immh.bit_length() - 1
        es = 8 << hb
        right, left = 2 * es - immhb, immhb - es
        d_only = {0x00: ("sshr", "ushr"), 0x02: ("ssra", "usra"), 0x04: ("srshr", "urshr"), 0x06: ("srsra", "ursra"), 0x08: (None, "sri")}
        if op in d_only:
            nm = d_only[op][u]
            return (nm, "d%d, d%d, #%d" % (rd, rn, right), None) if nm and hb == 3 else None
        if op == 0x0A:
            nm = ("shl", "sli")[u]
            return (nm, "d%d, d%d, #%d" % (rd, rn, left), None) if hb == 3 else None
        if op in (0x0C, 0x0E):
            nm = {(0x0C, 1): "sqshlu", (0x0E, 0): "sqshl", (0x0E, 1): "uqshl"}.get((op, u))
            return (nm, "%s%d, %s%d, #%d" % (L[hb], rd, L[hb], rn, left), None) if nm else None
        if op in (0x10, 0x11, 0x12, 0x13) and hb <= 2:
            nm = {0x10: (None, "sqshrun"), 0x11: (None, "sqrshrun"), 0x12: ("sqshrn", "uqshrn"), 0x13: ("sqrshrn", "uqrshrn")}[op][u]
            return (nm, "%s%d, %s%d, #%d" % (L[hb], rd, L[hb + 1], rn, right), None) if nm else None
        if op in (0x1C, 0x1F) and hb in (2, 3):
            nm = (("scvtf", "ucvtf") if op == 0x1C else ("fcvtzs", "fcvtzu"))[u]
            return nm, "%s%d, %s%d, #%d" % (L[hb], rd, L[hb], rn, right), None
        return None
    op, l, m, h = (w >> 12) & 15, (w >> 21) & 1, (w >> 20) & 1, (w >> 11) & 1
    rm4 = (w >> 16) & 15
    if size == 1:
        rmm, idx, el = rm4, (h << 2) | (l << 1) | m, "h"
    elif size == 2:
        rmm, idx, el = (m << 4) | rm4, (h << 1) | l, "s"
    elif size == 3 and not l:
        rmm, idx, el = (m << 4) | rm4, h, "d"
    else:
        return None
    if op in (1, 5, 9) and size >= 2:
        nm = {(1, 0): "fmla", (5, 0): "fmls", (9, 0): "fmul", (9, 1): "fmulx"}.get((op, u))
        return (nm, "%s%d, %s%d, v%d.%s[%d]" % (el, rd, el, rn, rmm, el, idx), None) if nm else None
    if not u and size in (1, 2):
        nm = {0x0C: "sqdmulh", 0x0D: "sqrdmulh"}.get(op)
        if nm:
            return nm, "%s%d, %s%d, v%d.%s[%d]" % (el, rd, el, rn, rmm, el, idx), None
        nm = {3: "sqdmlal", 7: "sqdmlsl", 11: "sqdmull"}.get(op)
        if nm:
            return nm, "%s%d, %s%d, v%d.%s[%d]" % ("sd"[size - 1], rd, el, rn, rmm, el, idx), None
    return None
