# rea_triage bagian 21/47: emu_thumb (baris asli 8452-9252). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.37 (roadmap v2, Tier A butir 4, tahap 2d-2c-2b-2b: emulasi mikro ARM 32-bit Thumb / Thumb-2; aditif): _thumb_emu_func() / _t_step() mengemulasi satu fungsi Thumb
# memakai pembantu A32 (_a32_shift / _a32_xfer / _blk / _a32_wr) dan _emu_collect() yang sama. PC Thumb = alamat + 4 (pembantu A32 dipanggil dengan pc - 4).
# 16-bit: geser imm, ADD / SUB (reg, imm3, imm8), MOV / CMP imm8, ALU 010000 (AND ... MVN), MOV / ADD / CMP register tinggi, BX / BLX, LDR literal, LDR / STR
# (reg, imm5, SP, half, signed), ADR, ADD Rd, SP, PUSH / POP, LDM / STM, ADD / SUB SP, UXT / SXT, REV, CBZ / CBNZ, IT, B, B<c>, SVC. 32-bit: MOVW / MOVT, ADDW / SUBW, UBFX,
# data processing (imm berekspansi, register bergeser), LDR / STR single (imm12, imm8 pre / post, reg, literal), LDM / STM / PUSH.W / POP.W, MUL / MLA, geser register,
# UXT / SXT.W, B.W, B<c>.W, BL / BLX imm, hint. Blok IT: kondisi per instruksi (kondisi tak tentu dijalankan di salinan lalu digabung). Flag narrow hanya di luar IT.
# TBB / TBH, VFP / NEON, LDREX / STREX, LDRD / STRD tidak didukung (jalur berhenti). Statis murni, hanya pustaka standar.
# ---------------------------------------------------------------------------
class _EmuStT(_EmuSt):
    """_EmuSt + sisa kondisi blok IT (daftar kode kondisi untuk instruksi berikutnya)."""
    __slots__ = ("it",)

    def __init__(self, d, L, am, lo, hi, nreg, pc):
        _EmuSt.__init__(self, d, L, am, lo, hi, nreg, pc)
        self.it = []

    def fork(self, pc):
        s = _EmuStT.__new__(_EmuStT)
        s.rv, s.rk, s.fl, s.ov, s.nw = self.rv[:], self.rk[:], self.fl[:], dict(self.ov), self.nw
        s.pc, s.steps, s.ops, s.am, s.d, s.L, s.lo, s.hi, s.unres = pc, self.steps, set(self.ops), self.am, self.d, self.L, self.lo, self.hi, self.unres
        s.it = []
        return s


_T_LOGIC = frozenset((0, 1, 8, 9, 12, 13, 14, 15, 16))
_T_BAD = ("s", "instruksi tak didukung", "?")


def _t_alu(st, opc: int, a, v2, c2, setf: bool, ops_ok: bool = True):
    """ALU Thumb (penomoran opcode A32; 16 = ORN). Mengembalikan hasil (None bila tak diketahui) dan mengatur flag bila setf."""
    if opc in _T_LOGIC:
        if v2 is None or (opc not in (13, 15) and a is None):
            res = None
        else:
            if opc in (0, 8):
                res = a & v2
            elif opc in (1, 9):
                res = a ^ v2
            elif opc == 12:
                res = a | v2
            elif opc == 13:
                res = v2
            elif opc == 14:
                res = a & ~v2 & _M32
            elif opc == 15:
                res = ~v2 & _M32
            else:
                res = (a | ~v2) & _M32
            if ops_ok and opc == 1:
                st.ops.add("xor")
            elif opc == 15:
                st.ops.add("not")
        if setf:
            st.fl = [None, None, c2, st.fl[3]] if res is None else [res >> 31, int(res == 0), c2, st.fl[3]]
        return res
    x, y = (v2, a) if opc in (3, 7) else (a, v2)
    sub = opc in (2, 3, 6, 7, 10)
    cin = st.fl[2] if opc in (5, 6, 7) else (1 if sub else 0)
    if x is None or y is None or cin is None:
        if setf:
            st.fl = [None] * 4
        return None
    yy = (~y) & _M32 if sub else y
    tot = x + yy + cin
    res = tot & _M32
    if setf:
        st.fl = [res >> 31, int(res == 0), tot >> 32, ((x ^ res) & (yy ^ res)) >> 31 & 1]
    if opc == 3 and v2 == 0:
        st.ops.add("neg")
    return res


def _t_nz(st, res, c) -> None:
    st.fl = [None, None, c, st.fl[3]] if res is None else [res >> 31, int(res == 0), c, st.fl[3]]


def _t_expand(imm12: int, cin):
    """ThumbExpandImm_C -> (nilai, carry)."""
    if imm12 >> 10 == 0:
        b = imm12 & 0xFF
        return (b, (b << 16) | b, (b << 24) | (b << 8), b * 0x01010101)[(imm12 >> 8) & 3], cin
    u, r = 0x80 | (imm12 & 0x7F), (imm12 >> 7) & 31
    v = ((u >> r) | (u << (32 - r))) & _M32
    return v, v >> 31


def _t_regs_ret(rn: int):
    return "s", "ret" if rn == 13 else "br register", "pop pc"


def _t16(st, h: int, pc: int, setf: bool):
    pcx = pc - 4
    t5 = h >> 11
    rd = h & 7
    if t5 < 3:                                                                  # LSL / LSR / ASR imm
        vm, imm = _a32_rd(st, (h >> 3) & 7, pcx), (h >> 6) & 31
        if vm is None:
            res = c = None
        else:
            res, c = _a32_shift(vm, t5, imm, st.fl[2], False)
            if imm:
                st.ops.add(("shl", "shr", "shr")[t5])
        _a32_wr(st, rd, res)
        if setf:
            _t_nz(st, res, c)
        return "n", 0, "shift"
    if t5 == 3:                                                                 # ADD / SUB reg, imm3
        a = _a32_rd(st, (h >> 3) & 7, pcx)
        b = _a32_rd(st, (h >> 6) & 7, pcx) if not (h & 0x0400) else (h >> 6) & 7
        _a32_wr(st, rd, _t_alu(st, 2 if h & 0x0200 else 4, a, b, None, setf, False))
        return "n", 0, "addsub"
    if 4 <= t5 <= 7:                                                            # MOV / CMP / ADD / SUB imm8
        k, rdn, imm = t5 & 3, (h >> 8) & 7, h & 0xFF
        opc = (13, 10, 4, 2)[k]
        res = _t_alu(st, opc, _a32_rd(st, rdn, pcx), imm, st.fl[2], setf or k == 1, False)
        if k != 1:
            _a32_wr(st, rdn, res)
        return "n", 0, "imm8"
    top6 = h >> 10
    if top6 == 0x10:                                                            # ALU register
        op, rm = (h >> 6) & 15, (h >> 3) & 7
        a, b = _a32_rd(st, rd, pcx), _a32_rd(st, rm, pcx)
        if op in (2, 3, 4, 7):                                                  # LSL / LSR / ASR / ROR register
            if a is None or b is None:
                res = c = None
            else:
                typ = {2: 0, 3: 1, 4: 2, 7: 3}[op]
                res, c = _a32_shift(a, typ, b & 0xFF, st.fl[2], True)
                if b & 0xFF:
                    st.ops.add(("shl", "shr", "shr", "ror")[typ])
            _a32_wr(st, rd, res)
            if setf:
                _t_nz(st, res, c)
            return "n", 0, "shiftreg"
        if op == 13:                                                            # MUL
            res = None if a is None or b is None else (a * b) & _M32
            _a32_wr(st, rd, res)
            if setf:
                _t_nz(st, res, st.fl[2])
            return "n", 0, "mul"
        amap = {0: 0, 1: 1, 5: 5, 6: 6, 8: 8, 9: 3, 10: 10, 11: 11, 12: 12, 14: 14, 15: 15}
        opc = amap[op]
        if opc == 3:
            res = _t_alu(st, 3, b, 0, st.fl[2], setf)
        elif opc == 15:
            res = _t_alu(st, 15, None, b, st.fl[2], setf)
        else:
            res = _t_alu(st, opc, a, b, st.fl[2], setf or opc in (8, 10, 11), opc != 1 or rd != rm)
        if opc not in (8, 10, 11):
            _a32_wr(st, rd, res)
        return "n", 0, "alu"
    if top6 == 0x11:                                                            # register tinggi
        op, rm = (h >> 8) & 3, (h >> 3) & 15
        rdn = (h & 7) | ((h >> 4) & 8)
        if op == 3:
            if h & 0x80:
                _a32_clobber(st)
                return "n", 0, "blx"
            return ("s", "ret", "bx lr") if rm == 14 else ("s", "br register", "bx")
        if op == 1:
            _t_alu(st, 10, _a32_rd(st, rdn, pcx), _a32_rd(st, rm, pcx), None, True, False)
            return "n", 0, "cmp"
        if rdn == 15:
            return ("s", "ret", "mov pc") if op == 2 and rm == 14 else ("s", "br register", "br")
        v = _a32_rd(st, rm, pcx)
        if op == 0:
            a = _a32_rd(st, rdn, pcx)
            v = None if a is None or v is None else (a + v) & _M32
        _a32_wr(st, rdn, v)
        return "n", 0, "hi"
    if t5 == 9:                                                                 # LDR literal
        return _a32_xfer(st, pcx, 15, (h >> 8) & 7, ((pc + 4) & ~3) + (h & 0xFF) * 4, 0, 1, 1, 0, 1, 4, False)
    top4 = h >> 12
    if top4 == 5:                                                               # LDR / STR register
        op = (h >> 9) & 7
        off = _a32_rd(st, (h >> 6) & 7, pcx)
        size, L, sg = ((4, 0, 0), (2, 0, 0), (1, 0, 0), (1, 1, 1), (4, 1, 0), (2, 1, 0), (1, 1, 0), (2, 1, 1))[op]
        return _a32_xfer(st, pcx, (h >> 3) & 7, rd, _a32_rd(st, (h >> 3) & 7, pcx), off, 1, 1, 0, L, size, bool(sg))
    if top4 in (6, 7, 8):                                                       # LDR / STR imm5 (word, byte, half)
        rn, imm, L = (h >> 3) & 7, (h >> 6) & 31, (h >> 11) & 1
        size = 4 if top4 == 6 else (1 if top4 == 7 else 2)
        return _a32_xfer(st, pcx, rn, rd, _a32_rd(st, rn, pcx), imm * size, 1, 1, 0, L, size, False)
    if top4 == 9:                                                               # LDR / STR sp
        rt = (h >> 8) & 7
        return _a32_xfer(st, pcx, 13, rt, _a32_rd(st, 13, pcx), (h & 0xFF) * 4, 1, 1, 0, (h >> 11) & 1, 4, False)
    if top4 == 10:                                                              # ADR / ADD Rd, sp
        rdd, imm = (h >> 8) & 7, (h & 0xFF) * 4
        if h & 0x0800:
            b = _a32_rd(st, 13, pcx)
            _a32_wr(st, rdd, None if b is None else b + imm)
        else:
            _a32_wr(st, rdd, ((pc + 4) & ~3) + imm)
        return "n", 0, "adr"
    if top4 == 11:
        if (h & 0xFF00) == 0xB000:                                              # ADD / SUB sp, #imm7 * 4
            b = _a32_rd(st, 13, pcx)
            imm = (h & 0x7F) * 4
            _a32_wr(st, 13, None if b is None else (b - imm if h & 0x80 else b + imm))
            return "n", 0, "addsp"
        if (h & 0xFE00) == 0xB400 or (h & 0xFE00) == 0xBC00:                    # PUSH / POP
            pop = bool(h & 0x0800)
            regs = [i for i in range(8) if h >> i & 1] + ([15 if pop else 14] if h & 0x100 else [])
            if not regs:
                return _T_BAD
            return _blk(st, pcx, 13, regs, 1 if pop else 0, 0 if pop else 1, 1, int(pop))
        if (h & 0xFF00) == 0xBF00:
            return "n", 0, "nop/hint"
        if (h & 0xFF00) == 0xB200:                                              # SXTH / SXTB / UXTH / UXTB
            v = _a32_rd(st, (h >> 3) & 7, pcx)
            k = (h >> 6) & 3
            if v is not None:
                v &= 0xFFFF if k in (0, 2) else 0xFF
                if k == 0 and v >> 15:
                    v |= 0xFFFF0000
                elif k == 1 and v >> 7:
                    v |= 0xFFFFFF00
            _a32_wr(st, rd, v)
            return "n", 0, "ext"
        if (h & 0xFFC0) == 0xBA00:                                              # REV
            v = _a32_rd(st, (h >> 3) & 7, pcx)
            _a32_wr(st, rd, None if v is None else int.from_bytes(v.to_bytes(4, "little"), "big"))
            return "n", 0, "rev"
        return _T_BAD
    if top4 == 12:                                                              # LDM / STM
        rn, regs, L = (h >> 8) & 7, [i for i in range(8) if h >> i & 1], (h >> 11) & 1
        if not regs:
            return _T_BAD
        return _blk(st, pcx, rn, regs, 1, 0, 0 if (L and rn in regs) else 1, L)
    if (h >> 8) == 0xDF:
        st.rk[0] = 0
        return "n", 0, "svc"
    return _T_BAD


def _t32(st, h1: int, h2: int, pc: int):
    pcx = pc - 4
    if (h1 & 0xF800) == 0xF000 and not h2 & 0x8000:
        if not h1 & 0x0200:                                                     # data processing, imm berekspansi
            return _t_dp32(st, h1, h2, pc, True)
        imm12 = ((h1 >> 10) & 1) << 11 | ((h2 >> 12) & 7) << 8 | (h2 & 0xFF)
        rd, rn = (h2 >> 8) & 15, h1 & 15
        if (h1 & 0xFBF0) in (0xF240, 0xF2C0):                                   # MOVW / MOVT
            imm16 = (h1 & 15) << 12 | imm12
            if rd == 15:
                return _T_BAD
            if h1 & 0x0080:
                old = _a32_rd(st, rd, pcx)
                _a32_wr(st, rd, None if old is None else (old & 0xFFFF) | (imm16 << 16))
            else:
                _a32_wr(st, rd, imm16)
            return "n", 0, "movw/t"
        if (h1 & 0xFBF0) in (0xF200, 0xF2A0) and rd != 15:                      # ADDW / SUBW (rn = pc: ADR)
            b = (pc + 4) & ~3 if rn == 15 else _a32_rd(st, rn, pcx)
            _a32_wr(st, rd, None if b is None else (b - imm12 if h1 & 0x0080 else b + imm12))
            return "n", 0, "addw"
        if (h1 & 0xFBF0) == 0xF3C0 and rd != 15:                                # UBFX
            v, lsb, wd = _a32_rd(st, rn, pcx), ((h2 >> 12) & 7) << 2 | ((h2 >> 6) & 3), (h2 & 31) + 1
            if lsb + wd > 32:
                return _T_BAD
            _a32_wr(st, rd, None if v is None else (v >> lsb) & ((1 << wd) - 1))
            return "n", 0, "ubfx"
        return _T_BAD
    if (h1 & 0xFE00) == 0xEA00 and not h2 & 0x8000:                             # data processing, register bergeser
        return _t_dp32(st, h1, h2, pc, False)
    if (h1 & 0xFE00) == 0xE800:
        if (h1 & 0xFFF0) == 0xE8D0 and (h2 & 0xFFE0) == 0xF000:
            return "s", "br register", "tbb"
        if h1 & 0x0040 or (h1 >> 7) & 3 not in (1, 2):
            return _T_BAD                                                       # LDRD / STRD / LDREX / SRS / RFE
        rn, L = h1 & 15, (h1 >> 4) & 1
        regs = [i for i in range(16) if h2 >> i & 1]
        if not regs or rn == 15 or (h2 & 0x2000):
            return _T_BAD
        ia = ((h1 >> 7) & 3) == 1
        return _blk(st, pcx, rn, regs, int(ia), int(not ia), (h1 >> 5) & 1 if not (L and rn in regs) else 0, L)
    if (h1 & 0xFE00) == 0xF800:                                                 # LDR / STR single
        S, U7, sc, L, rn, rt = (h1 >> 8) & 1, (h1 >> 7) & 1, (h1 >> 5) & 3, (h1 >> 4) & 1, h1 & 15, (h2 >> 12) & 15
        size = {0: 1, 1: 2, 2: 4}.get(sc)
        if size is None or (S and (not L or size == 4)):
            return _T_BAD
        if L and rt == 15 and size != 4:
            return "n", 0, "pld"
        if not L and rt == 15:
            return _T_BAD
        if rn == 15:
            if not L:
                return _T_BAD
            return _a32_xfer(st, pcx, 15, rt, (pc + 4) & ~3, h2 & 0xFFF, 1, U7, 0, 1, size, bool(S))
        if U7:
            P, U, W, off = 1, 1, 0, h2 & 0xFFF
        elif h2 & 0x0800:
            P, U, W, off = (h2 >> 10) & 1, (h2 >> 9) & 1, (h2 >> 8) & 1, h2 & 0xFF
            if (h2 & 0x0F00) == 0x0E00 or (not P and not W):
                return _T_BAD
        elif (h2 & 0x07C0) == 0:
            P, U, W = 1, 1, 0
            vm = _a32_rd(st, h2 & 15, pcx)
            off = None if vm is None else (vm << ((h2 >> 4) & 3)) & _M32
        else:
            return _T_BAD
        return _a32_xfer(st, pcx, rn, rt, _a32_rd(st, rn, pcx), off, P, U, W, L, size, bool(S))
    if (h1 & 0xFFF0) == 0xFB00 and not h2 & 0x00F0:                             # MUL / MLA
        rd, ra, rm, rn = (h2 >> 8) & 15, (h2 >> 12) & 15, h2 & 15, h1 & 15
        a, b = _a32_rd(st, rn, pcx), _a32_rd(st, rm, pcx)
        acc = 0 if ra == 15 else _a32_rd(st, ra, pcx)
        _a32_wr(st, rd, None if a is None or b is None or acc is None else (a * b + acc) & _M32)
        return "n", 0, "mul"
    if (h1 & 0xFF80) == 0xFA00 and (h2 & 0xF0F0) == 0xF000:                    # geser register
        typ, S, rn, rd, rm = (h1 >> 5) & 3, (h1 >> 4) & 1, h1 & 15, (h2 >> 8) & 15, h2 & 15
        a, b = _a32_rd(st, rn, pcx), _a32_rd(st, rm, pcx)
        if a is None or b is None:
            res = c = None
        else:
            res, c = _a32_shift(a, typ, b & 0xFF, st.fl[2], True)
            if b & 0xFF:
                st.ops.add(("shl", "shr", "shr", "ror")[typ])
        _a32_wr(st, rd, res)
        if S:
            _t_nz(st, res, c)
        return "n", 0, "shift.w"
    if (h1 & 0xFF8F) == 0xFA0F and (h2 & 0xF0C0) == 0xF080:                    # SXTH / UXTH / SXTB / UXTB .W
        k = (h1 >> 4) & 7
        if k not in (0, 1, 4, 5):
            return _T_BAD
        v = _a32_rd(st, h2 & 15, pcx)
        if v is not None:
            rot = ((h2 >> 4) & 3) * 8
            v = ((v >> rot) | (v << (32 - rot))) & _M32 if rot else v
            v &= 0xFFFF if k < 4 else 0xFF
            if k == 0 and v >> 15:
                v |= 0xFFFF0000
            elif k == 4 and v >> 7:
                v |= 0xFFFFFF00
        _a32_wr(st, (h2 >> 8) & 15, v)
        return "n", 0, "ext.w"
    if (h1 & 0xF800) == 0xF000 and h2 & 0x8000:                                 # hint / barrier
        if h1 == 0xF3AF or h1 == 0xF3BF:
            return "n", 0, "nop.w"
    return _T_BAD


def _t_dp32(st, h1: int, h2: int, pc: int, imm_form: bool):
    pcx = pc - 4
    op4, S, rn, rd = (h1 >> 5) & 15, (h1 >> 4) & 1, h1 & 15, (h2 >> 8) & 15
    zi = False
    if imm_form:
        v2, c2 = _t_expand(((h1 >> 10) & 1) << 11 | ((h2 >> 12) & 7) << 8 | (h2 & 0xFF), st.fl[2])
    else:
        rm, typ, amt = h2 & 15, (h2 >> 4) & 3, ((h2 >> 12) & 7) << 2 | ((h2 >> 6) & 3)
        vm = _a32_rd(st, rm, pcx)
        if vm is None:
            v2 = c2 = None
        else:
            v2, c2 = _a32_shift(vm, typ, amt, st.fl[2], False)
            if amt:
                st.ops.add(("shl", "shr", "shr", "ror")[typ])
        zi = op4 == 4 and rn == rm and not amt
    tab = {0: 0, 1: 14, 2: 12, 3: 16, 4: 1, 8: 4, 10: 5, 11: 6, 13: 2, 14: 3}
    if op4 not in tab:
        return _T_BAD
    opc, test = tab[op4], False
    if rd == 15:
        if not S or op4 not in (0, 4, 8, 13):
            return _T_BAD
        opc, test = {0: 8, 4: 9, 8: 11, 13: 10}[op4], True
    if op4 in (2, 3) and rn == 15:
        opc, a = (13 if op4 == 2 else 15), None
    else:
        a = _a32_rd(st, rn, pcx)
    res = _t_alu(st, opc, a, v2, c2, bool(S) or test, not zi)
    if not test:
        _a32_wr(st, rd, res)
    return "n", 0, "dp32"


def _t_branch(h1: int, h2: int, pc: int, n: int):
    """-> (jenis, target, cond): 'b' tanpa syarat, 'bc' bersyarat, 'bl' panggilan, None bila bukan cabang."""
    if n == 2:
        if (h1 >> 11) == 0x1C:
            return "b", pc + 4 + (_a64_s(h1 & 0x7FF, 11) << 1), 14
        if (h1 >> 12) == 13 and ((h1 >> 8) & 15) < 14:
            return "bc", pc + 4 + (_a64_s(h1 & 0xFF, 8) << 1), (h1 >> 8) & 15
        return None, 0, 0
    if (h1 & 0xF800) != 0xF000 or not h2 & 0x8000:
        return None, 0, 0
    S, J1, J2 = (h1 >> 10) & 1, (h2 >> 13) & 1, (h2 >> 11) & 1
    if (h2 & 0xD000) == 0x8000 and ((h1 >> 6) & 15) < 14:                       # B<c>.W (T3)
        off = _a64_s(S << 20 | J2 << 19 | J1 << 18 | (h1 & 0x3F) << 12 | (h2 & 0x7FF) << 1, 21)
        return "bc", pc + 4 + off, (h1 >> 6) & 15
    if (h2 & 0xC000) == 0xC000 or (h2 & 0xD000) == 0x9000:
        i1, i2 = (~(J1 ^ S)) & 1, (~(J2 ^ S)) & 1
        off = _a64_s(S << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1, 25)
        return ("bl" if h2 & 0x4000 else "b"), pc + 4 + off, 14
    return None, 0, 0


def _t_exec(st, h1: int, h2: int, pc: int, n: int, in_it: bool):
    if n == 2:
        if (h1 & 0xF500) == 0xB100:                                                         # CBZ / CBNZ
            v = _a32_rd(st, h1 & 7, pc - 4)
            t = pc + 4 + (((h1 >> 9) & 1) << 6 | ((h1 >> 3) & 31) << 1)
            nz = (h1 >> 11) & 1
            if v is None:
                return "f", t, "cbnz" if nz else "cbz"
            return ("j", t, "cb") if (v != 0) == bool(nz) else ("n", 0, "cb")
        return _t16(st, h1, pc, not in_it)
    return _t32(st, h1, h2, pc)


def _t_step(st, h1: int, h2: int, pc: int, n: int):
    """Satu instruksi Thumb. (aksi, nilai, mnemonik) seperti _a32_step."""
    if n == 2 and (h1 & 0xFF00) == 0xBF00 and h1 & 15:                         # IT
        fc, mask = (h1 >> 4) & 15, h1 & 15
        cnt = 4 - ((mask & -mask).bit_length() - 1)
        st.it = [fc] + [fc if ((mask >> (4 - k)) & 1) == (fc & 1) else fc ^ 1 for k in range(1, cnt)]
        return "n", 0, "it"
    it_cond = st.it.pop(0) if st.it else None
    kind, tgt, cc = _t_branch(h1, h2, pc, n)
    if it_cond is not None and kind in ("b", "bc"):
        kind, cc = "bc", it_cond
    if kind == "bc" or it_cond is not None or kind == "bl":
        cond = cc if kind == "bc" else (it_cond if it_cond is not None else 14)
    else:
        cond = 14
    cv = True if cond == 14 else _a64_cond(st.fl, cond)
    if kind in ("b", "bc"):
        if cv is False:
            return "n", 0, "b?"
        if tgt & 1:
            return _T_BAD
        if cv is None:
            return "f", tgt, "b." + _A64_COND[cond]
        return "j", tgt, "b"
    if kind == "bl":
        if cv is False:
            return "n", 0, "bl?"
        _a32_clobber(st)
        return "n", 0, "bl"
    if cv is False:
        return "n", 0, "skip"
    in_it = it_cond is not None
    if cv is None:
        s2 = st.fork(pc)
        act, val, mn = _t_exec(s2, h1, h2, pc, n, True)
        if act == "s" and val in ("ret", "br register"):
            return "n", 0, mn + "?"
        if act != "n":
            return act, val, mn
        for i in range(16):
            if (s2.rv[i], s2.rk[i]) != (st.rv[i], st.rk[i]):
                st.rk[i] = 0
        if s2.fl != st.fl:
            st.fl = [None] * 4
        for k, v in s2.ov.items():
            if st.ov.get(k, -1) != v:
                st.ov[k] = None
        st.nw, st.unres, st.ops = max(st.nw, s2.nw), s2.unres, st.ops | s2.ops
        return "n", 0, mn + "?"
    return _t_exec(st, h1, h2, pc, n, in_it)


def _thumb_emu_func(d: bytes, L: dict, start: int, end: int, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """Emulasi satu fungsi Thumb / Thumb-2 [start, end). None bila awal tidak bisa dibaca. Tidak pernah melempar karena data biner."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start or start & 1:
        return None
    n_h = min((end - start) // 2, (len(d) - off0) // 2)
    if n_h <= 0:
        return None
    hws = struct.unpack("<%dH" % n_h, d[off0:off0 + n_h * 2])
    lim = start + n_h * 2
    top = 0x7FD00000
    s0 = _EmuStT(d, L, _M32, top - 0x100000, top + 0x10000, 16, start)
    s0.rv[13], s0.rk[13] = top, _M32
    work, finals, tr = [s0], [], []
    total = forks = 0
    stop = ""
    timed = False
    while work and not timed:
        st = work.pop()
        first = trace_max > 0 and not finals
        while True:
            pc = st.pc
            if st.steps >= EMU_MAX_STEPS or total >= max_total:
                stop = "batas langkah"
                break
            if not (st.steps & 255) and time.monotonic() > deadline:
                stop, timed = "batas waktu", True
                break
            if not (start <= pc < lim) or pc & 1:
                stop = "keluar fungsi"
                break
            j = (pc - start) >> 1
            h1 = hws[j]
            n = 4 if (h1 >> 11) in (0x1D, 0x1E, 0x1F) else 2
            if j + (n >> 1) > n_h:
                stop = "keluar fungsi"
                break
            h2 = hws[j + 1] if n == 4 else 0
            st.steps += 1
            total += 1
            if st.nw > EMU_MAX_WRITES:
                stop = "batas tulis"
                break
            try:
                act, val, mn = _t_step(st, h1, h2, pc, n)
            except (ValueError, OverflowError, IndexError, KeyError):
                act, val, mn = "s", "instruksi tak didukung", "?"
            if first and len(tr) < trace_max:
                tr.append((pc, ("%04X %04X  %s" % (h1, h2, mn)) if n == 4 else ("%04X       %s" % (h1, mn)), "diambil" if act == "j" else ""))
            if act == "s":
                stop = val
                break
            if act == "j":
                if not (start <= val < lim):
                    stop = "lompat keluar fungsi"
                    break
                st.pc = val
                continue
            if act == "f" and forks < EMU_MAX_FORKS and start <= val < lim and len(work) < 32:
                forks += 1
                work.append(st.fork(val))
            st.pc = pc + n
        if len(finals) < EMU_MAX_FINALS:
            finals.append(st)
    return {"steps": total, "forks": forks, "stop": stop, "finals": finals, "trace": tr, "timed": timed}


def _arm32_emu_func(d: bytes, L: dict, start: int, end: int, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """v99.36 / v99.37: emulasi fungsi ARM 32-bit; mode (A32 / Thumb) dari wilayah di `start`."""
    m = _arm_mode_at(L, start)
    if m is None:
        return None
    return (_thumb_emu_func if m[0] == "t" else _a32_emu_func)(d, L, start, min(end, m[1]), deadline, trace_max, max_total)



def _emu_runs(m: dict) -> list:
    out: list = []
    cur = None
    for a in sorted(m):
        if cur is not None and a == cur[0] + len(cur[1]):
            cur[1].append(m[a])
        else:
            if cur is not None:
                out.append(cur)
            cur = [a, bytearray([m[a]])]
    if cur is not None:
        out.append(cur)
    return out


def _emu_collect(d: bytes, L: dict, finals: list) -> tuple[list, list, int]:
    """(string, buffer, tulisan_tak_terselesaikan). string: dict kind / va / text / wide / ops; buffer: dict va / len / kind / preview."""
    strs: dict = {}
    bufs: dict = {}
    unres = 0
    for st in finals:
        unres = max(unres, st.unres)
        stk = {a: v for a, v in st.ov.items() if v is not None and st.lo <= a < st.hi}
        dat = {}
        for a, v in st.ov.items():
            if v is None or st.lo <= a < st.hi:
                continue
            off = _va_off(L, a)
            if off is None or off >= len(d) or d[off] != v:
                dat[a] = v
        ops = sorted(st.ops & _EMU_STRONG)
        for kind, m in (("stack", stk), ("data", dat)):
            for addr, bs in _emu_runs(m):
                raw = bytes(bs)
                if kind == "data" and len(raw) >= 8:
                    pr = sum(1 for x in raw if 0x20 <= x < 0x7F or x in (9, 10, 13)) / len(raw)
                    k = "PE" if raw[:2] == b"MZ" and b"PE\0\0" in raw[:0x600] else ("teks" if pr >= 0.85 else "biner")
                    if (k in ("PE", "teks") or (len(raw) >= 32 and ops)) and (addr not in bufs) and len(bufs) < 24:
                        bufs[addr] = {"va": "0x%X" % addr, "len": len(raw), "kind": k, "ops": ops,
                                      "preview": "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in raw[:48])}
                if len(raw) < 5:
                    continue
                for mt in _EMU_RX_A.finditer(raw):
                    t = mt.group().decode("ascii")
                    if sum(ch.isalnum() for ch in t) >= max(4, int(len(t) * 0.6)) and t not in strs:
                        strs[t] = {"kind": kind, "va": "0x%X" % (addr + mt.start()), "text": t, "wide": False, "ops": ops}
                for mt in _EMU_RX_W.finditer(raw):
                    t = raw[mt.start():mt.end()].decode("utf-16le")
                    if sum(ch.isalnum() for ch in t) >= max(4, int(len(t) * 0.6)) and t not in strs:
                        strs[t] = {"kind": kind, "va": "0x%X" % (addr + mt.start()), "text": t, "wide": True, "ops": ops}
    return list(strs.values()), list(bufs.values()), unres


def _emu_enrich(info: dict, ctx: dict, d: bytes) -> None:
    """Dipanggil di akhir _re_lab (setelah CFG): info["emu"] (kunci baru). Tidak pernah melempar; tidak mengubah skor."""
    try:
        L, F = ctx["L"], ctx["F"]
        is64 = L["is64"]
        xs = [(L["base"] + s["va"], L["base"] + s["va"] + max(s["vsize"], s["rsize"])) for s in L["xsecs"]]
        top_va = []
        for f in info.get("functions", []):
            try:
                top_va.append(int(f["va"], 16))
            except ValueError:
                pass
        fl = ctx["fl"]
        ends: dict = {}
        for k, s in enumerate(fl):          # semua awal fungsi yang ditemukan (F hanya memuat yang punya pemanggil / panggilan API)
            sec_end = next((b for a_, b in xs if a_ <= s < b), s)
            ends[s] = min(fl[k + 1] if k + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
        first = [L["entry_va"]] if L.get("entry_va") in ends else []
        rest = sorted((s for s in fl if s not in F), key=lambda s: s - ends[s])
        todo = list(dict.fromkeys(first + [s for s in top_va if s in ends] + [s for s, _f in sorted(F.items(), key=lambda kv: -kv[1]["size"]) if s in ends] + rest))[:EMU_MAX_FUNCS]
        deadline = time.monotonic() + EMU_TIME
        have = [x["text"] for x in info.get("stack_strings", [])]
        nm = lambda s: F[s]["name"] if s in F else ("start" if s == L.get("entry_va") else (L["exports"].get(s) or "sub_%08X" % s))
        n_an = steps = unres = 0
        partial = False
        sout: list = []
        bout: list = []
        seen: set = set()
        for s in todo:
            if time.monotonic() > deadline or steps >= EMU_MAX_TOTAL:
                partial = True
                break
            if s in ctx["thunks"] or ends[s] - s < 6:
                continue
            r = _emu_func(d, L, s, ends[s], is64, deadline, max_total=EMU_MAX_TOTAL - steps)
            if r is None:
                continue
            n_an += 1
            steps += r["steps"]
            if r["timed"]:
                partial = True
            ss, bb, u = _emu_collect(d, L, r["finals"])
            unres += u
            for x in ss:
                t = x["text"]
                plain = t.encode("utf-16le" if x["wide"] else "latin-1") in d
                if plain or t in seen or len(sout) >= EMU_MAX_RESULTS:
                    continue
                seen.add(t)
                clean = _clean(t)[:100]
                sout.append({"va": x["va"], "func": "0x%X" % s, "name": _clean(nm(s)), "text": clean, "kind": x["kind"], "wide": x["wide"], "ops": x["ops"],
                             "tag": _str_tag(t), "new": not any(clean == h or clean in h or h in clean for h in have)})
            for x in bb:
                if len(bout) < 16:
                    bout.append(dict(x, func="0x%X" % s, name=_clean(nm(s)), preview=_clean(x["preview"])))
        info["emu"] = {"analyzed": n_an, "steps": steps, "partial": partial, "unresolved_writes": unres, "strings": sout, "buffers": bout}
    except Exception as e:
        info["notes"].append("Emulasi gagal: %s" % type(e).__name__)


def _render_emu(r: dict, a, compact: bool, defang: bool) -> None:
    c = r.get("emu")
    if not c or not c["analyzed"]:
        return
    new = [x for x in c["strings"] if x["new"]]
    a("   Emulasi mikro: %d fungsi / %d langkah, %d string tersembunyi (%d baru), %d buffer dimodifikasi%s" % (
        c["analyzed"], c["steps"], len(c["strings"]), len(new), len(c["buffers"]), " | TERPOTONG (batas waktu / langkah)" if c["partial"] else ""))
    for x in (new if compact else c["strings"])[: (3 if compact else 10)]:
        a("   ! string hasil emulasi: %s [%s%s] di %s %s%s" % (_df(x["text"], defang), x["tag"], ", UTF-16" if x["wide"] else "", x["name"], x["func"],
                                                           (" | operasi: " + "/".join(x["ops"])) if x["ops"] else ""))
    for x in c["buffers"][: (2 if compact else 6)]:
        a("   ! buffer dimodifikasi emulasi (%s): %d byte @%s di %s%s | %s" % (x["kind"], x["len"], x["va"], x["name"], (" (" + "/".join(x["ops"]) + ")") if x["ops"] else "",
                                                                             _df(x["preview"], defang)))


def emu_text(path, at=None, defang: bool = True) -> str:
    """Ringkasan emulasi mikro (tanpa `at`) atau jejak + hasil satu fungsi (at = 'entry' / 0xVA). CLI --emu, API action 'emu'."""
    try:
        d, size = _cfg_read(path)
        info, ctx, err = _relab_multi(d, size)
    except Exception as e:
        return "Emulasi gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if not info:
        return "Emulasi: %s." % (err or "tidak ada kode yang bisa dianalisis")
    if at is None:
        L_: list = []
        _render_emu(info, L_.append, False, defang)
        return "\n".join(L_) if L_ else "Emulasi: tidak ada string / buffer tersembunyi yang berhasil diturunkan."
    Lx, fl = ctx["L"], ctx["fl"]
    try:
        va = Lx["entry_va"] if str(at).lower() == "entry" else int(str(at), 0)
    except ValueError:
        return "Emulasi: alamat tidak valid (pakai entry atau 0xVA)."
    i = bisect.bisect_right(fl, va) - 1
    if i < 0:
        return "Emulasi: tidak ada fungsi yang memuat 0x%X." % va
    s = fl[i]
    xs = [(Lx["base"] + x["va"], Lx["base"] + x["va"] + max(x["vsize"], x["rsize"])) for x in Lx["xsecs"]]
    sec_end = next((b for a_, b in xs if a_ <= s < b), s)
    e = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
    r = _emu_func(d, Lx, s, e, Lx["is64"], time.monotonic() + EMU_TIME, trace_max=200)
    if not r:
        return "Emulasi: fungsi di 0x%X tidak bisa dibaca." % s
    ss, bb, unres = _emu_collect(d, Lx, r["finals"])
    out = ["Fungsi 0x%X: %d langkah, %d jalur (%d fork), berhenti: %s%s" % (s, r["steps"], len(r["finals"]), r["forks"], r["stop"] or "-",
                                                                          ", %d tulisan ke alamat tak diketahui diabaikan" % unres if unres else "")]
    out += ["  0x%X  %-34s %s" % (pc, t, ("; " + nt) if nt else "") for pc, t, nt in r["trace"]]
    for x in ss[:20]:
        out.append("  string [%s%s] @%s: %s%s" % (x["kind"], ", UTF-16" if x["wide"] else "", x["va"], _df(_clean(x["text"])[:100], defang),
                                               (" | operasi: " + "/".join(x["ops"])) if x["ops"] else ""))
    for x in bb[:8]:
        out.append("  buffer dimodifikasi (%s): %d byte @%s | %s" % (x["kind"], x["len"], x["va"], _df(_clean(x["preview"]), defang)))
    return "\n".join(out)


def _v98_enrich(d: bytes, rep: dict) -> None:
    pe = rep.get("pe")
    rep["relab"] = None
    if not (pe and not pe.get("broken")) and not rep.get("elf") and not rep.get("macho"):
        return
    try:
        if pe and not pe.get("broken"):
            info, _ctx = _re_lab(d, pe)
        else:
            info, _ctx = _relab_elf(d) if rep.get("elf") else (None, None)
            if info is None:                          # v99.26: ELF / Mach-O AArch64 (x86 / x64 tidak berubah)
                info, _ctx, _err = _relab_arm(d)
    except Exception as e:
        rep["warn"].append("RE Lab gagal: %s" % type(e).__name__)
        return
    rep["relab"] = info
    if not info:
        return
    for x in info["notes"]:
        rep["warn"].append("RE Lab: " + x)
    for x in info["anti"]:
        if x["technique"].startswith(("syscall", "Heaven")):
            rep["warn"].append("RE Lab: %s (%d lokasi, pertama 0x%s)" % (x["technique"], x["count"], x["first"][2:]))
    cf_ = info.get("cfg") or {}
    for x in (cf_.get("decrypt_loops") or [])[:2]:
        rep["warn"].append("RE Lab: kandidat loop dekripsi di %s %s (%s)" % (x["name"], x["func"], "/".join(x["ops"])))
    for x in (cf_.get("flatten") or [])[:1]:
        rep["warn"].append("RE Lab: kandidat control-flow flattening di %s %s (%d sisi balik)" % (x["name"], x["func"], x["back_edges"]))
    for x in [x for x in ((info.get("emu") or {}).get("strings") or []) if x["new"] and (x["tag"] != "menarik" or x["ops"])][:3]:
        rep["warn"].append("RE Lab: emulasi mikro menurunkan string tersembunyi di %s %s: %s [%s]" % (x["name"], x["func"], _clean(x["text"])[:60], x["tag"]))
    for x in ((info.get("emu") or {}).get("buffers") or [])[:1]:
        if x["kind"] in ("PE", "teks"):
            rep["warn"].append("RE Lab: loop kecil mendekripsi buffer (%s, %d byte) di %s %s" % (x["kind"], x["len"], x["name"], x["func"]))
    if info["api_hashes"]:
        rep["warn"].append("RE Lab: konstanta API hash terdeteksi (%s): kemungkinan resolusi API tersembunyi / shellcode" % ", ".join(h["api"] for h in info["api_hashes"][:3]))


def _render_v98(rep: dict, a, compact: bool, defang: bool) -> None:
    r = rep.get("relab")
    if not r:
        return
    a("RE Lab : %s | base %s | %d fungsi, %d panggilan API terpetakan (%d slot IAT), %d string dirujuk kode" % (
        r["arch"], r["image_base"], r["n_functions"], r["n_api_sites"], r["n_iat"], r["n_strrefs"]))
    st = r["entry_stub"]
    if r["entry"]:
        a("   entry %s: %s%s" % (r["entry"], st["hex"], (" | " + st["note"]) if st["note"] else ""))
    for f in r["functions"][: (3 if compact else RELAB_TOP)]:
        a("   * %s %s (%s, caller %d, callee %d) skor %d%s%s%s" % (
            f["name"], f["va"], _human(f["size"]), f["callers"], f["callees"], f["score"],
            (" | " + "; ".join(f["tags"])) if f["tags"] else "", (" | API: " + ", ".join(x.split("!")[-1] for x in f["apis"][:8])) if f["apis"] else "",
            (" | anti: " + ", ".join(f["anti"])) if f["anti"] else ""))
        if f["strings"] and not compact:
            a("       string: " + " | ".join(_df(x, defang) for x in f["strings"][:3]))
    _render_cfg(r, a, compact)
    _render_emu(r, a, compact, defang)
    if compact:
        for x in r["anti"][:3]:
            a("   anti-analisis: %s x%d" % (x["technique"], x["count"]))
        return
    for x in r["anti"]:
        a("   anti-analisis: %s x%d (pertama %s)" % (x["technique"], x["count"], x["first"]))
    if r["api_hashes"]:
        a("   API hashing: " + ", ".join("%s @%s" % (h["api"], h["offset"]) for h in r["api_hashes"][:8]))
    if r["stack_strings"]:
        a("   stack string: " + " | ".join("%s [%s]" % (_df(x["text"], defang), x["tag"]) for x in r["stack_strings"][:8]))
    if r["string_refs"]:
        a("   string yang dirujuk kode:")
        for e in r["string_refs"][:8]:
            a("     %s [%s] %s <- %s" % (e["va"], e["tag"], _df(e["text"], defang), ", ".join(e["funcs"]) or "?"))
    if r["api_top"]:
        a("   API paling sering dipanggil: " + ", ".join("%s x%d" % (k.split("!")[-1], n) for k, n in r["api_top"][:10]))


def _score_v98(rep: dict, add) -> None:
    r = rep.get("relab")
    if not r:
        return
    keys = [x["technique"] for x in r["anti"]]
    if any(k.startswith("syscall") for k in keys):
        add(3, "syscall langsung (melewati hook API / EDR)")
    if any(k.startswith("Heaven") for k in keys):
        add(2, "Heaven's Gate (lompat ke mode 64-bit dari WoW64)")
    if r["api_hashes"]:
        add(3, "API hashing (konstanta hash API dikenal ditemukan)")
    if any("pola ransomware" in t for f in r["functions"] for t in f["tags"]):
        add(3, "satu fungsi menggabungkan kripto + enumerasi berkas")
    elif any(t in ("injeksi proses", "unduh & jalankan") for f in r["functions"] for t in f["tags"]):
        add(1, "satu fungsi merangkai API injeksi / unduh-jalankan")
    if any(x["tag"] not in ("menarik",) for x in r["stack_strings"]):
        add(2, "string sensitif disusun di stack (menghindari pencarian string)")
    n_anti = len([k for k in keys if not k.startswith(("CPUID", "ROR"))])
    if n_anti >= 3:
        add(2, "banyak teknik anti-analisis tingkat instruksi (%d)" % n_anti)


