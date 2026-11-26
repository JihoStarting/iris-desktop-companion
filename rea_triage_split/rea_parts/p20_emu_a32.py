# rea_triage bagian 20/47: emu_a32 (baris asli 8073-8451). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.36 (roadmap v2, Tier A butir 4, tahap 2d-2c-2b-2a: emulasi mikro ARM 32-bit mode A32; aditif): _a32_emu_func() / _a32_step() mengemulasi satu fungsi A32
# (r0-r15, flag NZCV, memori overlay yang sama dengan emulator x86 / AArch64; hasil dikumpulkan _emu_collect() yang sama). Himpunan instruksi kecil: data
# processing (AND/EOR/SUB/RSB/ADD/ADC/SBC/RSC/TST/TEQ/CMP/CMN/ORR/MOV/BIC/MVN; operand imm berotasi, register bergeser imm / register), MOVW / MOVT, MUL / MLA,
# LDR / STR / LDRB / STRB (imm, register bergeser, pre/post, literal pc), LDRH / STRH / LDRSB / LDRSH, LDM / STM (push / pop), B / B<c> / BL / BLX / BX, SVC,
# eksekusi bersyarat (cond tak tentu dijalankan di salinan lalu digabung: register / memori yang berubah menjadi tidak diketahui). BL / BLX / SVC dilangkahi
# (r0-r3, r12, lr tak diketahui). Thumb / Thumb-2, VFP / NEON, LDREX / STREX, LDRD / STRD tidak didukung (jalur berhenti). Statis murni, hanya pustaka standar.
# ---------------------------------------------------------------------------
_M32 = 0xFFFFFFFF


def _a32_rd(st, n: int, pc: int):
    if n == 15:
        return (pc + 8) & _M32
    return _emu_rg(st, n)


def _a32_wr(st, n: int, v) -> None:
    if v is None:
        st.rv[n], st.rk[n] = 0, 0
    else:
        st.rv[n], st.rk[n] = v & _M32, _M32


def _a32_clobber(st) -> None:
    for r_ in (0, 1, 2, 3, 12, 14):
        st.rk[r_] = 0
    st.fl = [None] * 4


def _a32_shift(v: int, typ: int, amt: int, cin, by_reg: bool):
    """Geser operand A32 -> (nilai, carry); carry bisa None bila cin tak diketahui."""
    if by_reg:
        if amt == 0:
            return v, cin
    elif amt == 0:
        if typ == 0:
            return v, cin
        if typ == 3:                                       # RRX
            if cin is None:
                return None, None
            return (v >> 1) | (cin << 31), v & 1
        amt = 32
    if typ == 0:
        if amt < 32:
            return (v << amt) & _M32, (v >> (32 - amt)) & 1
        return 0, (v & 1) if amt == 32 else 0
    if typ == 1:
        if amt < 32:
            return v >> amt, (v >> (amt - 1)) & 1
        return 0, (v >> 31) if amt == 32 else 0
    if typ == 2:
        if amt >= 32:
            return (_M32 if v >> 31 else 0), v >> 31
        sv = v - (1 << 32) if v >> 31 else v
        return (sv >> amt) & _M32, (v >> (amt - 1)) & 1
    amt &= 31
    if amt == 0:
        return v, v >> 31
    return ((v >> amt) | (v << (32 - amt))) & _M32, (v >> (amt - 1)) & 1


def _a32_op2(st, w: int, pc: int):
    """Operand kedua data processing -> (nilai | None, carry | None)."""
    if w & 0x02000000:
        rot = ((w >> 8) & 15) * 2
        imm = w & 0xFF
        v = ((imm >> rot) | (imm << (32 - rot))) & _M32 if rot else imm
        return v, ((v >> 31) if rot else st.fl[2])
    rm, typ = w & 15, (w >> 5) & 3
    if w & 0x10:
        rs = (w >> 8) & 15
        if rs == 15:
            raise ValueError("rs=pc")
        a = _a32_rd(st, rs, pc)
        amt = None if a is None else a & 0xFF
        vm = ((pc + 12) & _M32) if rm == 15 else _a32_rd(st, rm, pc)
        by = True
    else:
        amt, vm, by = (w >> 7) & 31, _a32_rd(st, rm, pc), False
    if vm is None or amt is None:
        return None, None
    v, c = _a32_shift(vm, typ, amt, st.fl[2], by)
    if v is not None and (amt or by):
        st.ops.add(("shl", "shr", "shr", "ror")[typ])
    return v, c


def _a32_dp(st, w: int, pc: int):
    opc, S, rn, rd = (w >> 21) & 15, (w >> 20) & 1, (w >> 16) & 15, (w >> 12) & 15
    test = 8 <= opc <= 11
    if rd == 15 and not test:                              # tulis ke pc: kembali / lompat register
        return ("s", "ret", "ret") if (opc == 13 and not S and (w & 0x02000FFF) == 14) or (S and opc == 2 and rn == 14) else ("s", "br register", "br")
    v2, c2 = _a32_op2(st, w, pc)
    a = None if opc in (13, 15) else _a32_rd(st, rn, pc)
    setf = bool(S) or test
    if opc in (0, 1, 8, 9, 12, 13, 14, 15):                # logika
        if v2 is None or (opc not in (13, 15) and a is None):
            res = None
        else:
            res = {0: lambda: a & v2, 8: lambda: a & v2, 1: lambda: a ^ v2, 9: lambda: a ^ v2, 12: lambda: a | v2,
                   13: lambda: v2, 14: lambda: a & ~v2 & _M32, 15: lambda: ~v2 & _M32}[opc]()
            if opc == 1 and (w & 0x02000000 or (w & 15) != rn or (w & 0xFF0)):      # eor rX, rX, rX (nol) bukan operasi dekode
                st.ops.add("xor")
            elif opc == 15:
                st.ops.add("not")
        if setf:
            st.fl = [None, None, c2, st.fl[3]] if res is None else [res >> 31, int(res == 0), c2, st.fl[3]]
    else:                                                   # aritmetika
        x, y = (v2, a) if opc in (3, 7) else (a, v2)
        sub = opc in (2, 3, 6, 7, 10)
        if opc in (5, 6, 7):
            cin = st.fl[2]
        else:
            cin = 1 if sub else 0
        if x is None or y is None or cin is None:
            res = None
            if setf:
                st.fl = [None] * 4
        else:
            yy = (~y) & _M32 if sub else y
            tot = x + yy + cin
            res = tot & _M32
            if setf:
                st.fl = [res >> 31, int(res == 0), tot >> 32, ((x ^ res) & (yy ^ res)) >> 31 & 1]
            if rn not in (13, 15):
                if opc == 3 and v2 == 0 and not (w & 0x10):
                    st.ops.add("neg")
                elif opc in (4, 2):
                    st.ops.add("add" if opc == 4 else "sub")
    if not test:
        _a32_wr(st, rd, res)
    return "n", 0, "dp%d" % opc


def _a32_xfer(st, pc: int, rn: int, rd: int, base, off, P: int, U: int, W: int, L: int, size: int, signed: bool):
    if base is None or off is None:
        ea = nb = None
    else:
        nb = (base + off if U else base - off) & _M32
        ea = nb if P else base
    wb = (not P or bool(W)) and rn != 15
    if wb:
        _a32_wr(st, rn, nb)
    if L:
        v = None if ea is None else st.read(ea, size)
        if signed and v is not None and v >> (size * 8 - 1):
            v -= 1 << (size * 8)
        if rd == 15:
            return "s", "ret" if rn == 13 else "br register", "ldr pc"
        _a32_wr(st, rd, v)
        return "n", 0, "ldr"
    v = _a32_rd(st, rd, pc)
    if ea is None:
        st.unres += 1
    else:
        st.write(ea, size, None if v is None else v & ((1 << (size * 8)) - 1))
    return "n", 0, "str"


def _a32_mem(st, w: int, pc: int):
    P, U, B, W, L = (w >> 24) & 1, (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 20) & 1
    rn, rd = (w >> 16) & 15, (w >> 12) & 15
    if w & 0x02000000:
        vm = _a32_rd(st, w & 15, pc)
        off = None if vm is None else _a32_shift(vm, (w >> 5) & 3, (w >> 7) & 31, st.fl[2], False)[0]
    else:
        off = w & 0xFFF
    return _a32_xfer(st, pc, rn, rd, _a32_rd(st, rn, pc), off, P, U, W, L, 1 if B else 4, False)


def _a32_half(st, w: int, pc: int):
    P, U, W, L = (w >> 24) & 1, (w >> 23) & 1, (w >> 21) & 1, (w >> 20) & 1
    rn, rd, sh = (w >> 16) & 15, (w >> 12) & 15, (w >> 5) & 3
    if not L and sh != 1:
        return "s", "instruksi tak didukung", "?"          # LDRD / STRD
    off = (((w >> 8) & 15) << 4) | (w & 15) if w & 0x00400000 else _a32_rd(st, w & 15, pc)
    return _a32_xfer(st, pc, rn, rd, _a32_rd(st, rn, pc), off, P, U, W, L, 1 if sh == 2 else 2, sh >= 2)


def _blk(st, pc: int, rn: int, regs: list, U: int, P: int, W: int, L: int):
    """Transfer blok (A32 LDM / STM dan Thumb PUSH / POP / LDM / STM): regs urut naik; pc untuk pembacaan r15 (nilai A32: pc + 8)."""
    n4 = 4 * len(regs)
    base = _a32_rd(st, rn, pc)
    if base is None:
        if L:
            for r in regs:
                if r != 15:
                    _a32_wr(st, r, None)
        else:
            st.unres += 1
        if W and not (L and rn in regs):
            _a32_wr(st, rn, None)
    else:
        lo = base + (4 if P else 0) if U else base - n4 + (0 if P else 4)
        nb = (base + n4 if U else base - n4) & _M32
        for k, r in enumerate(regs):
            a = (lo + 4 * k) & _M32
            if L:
                if r != 15:
                    _a32_wr(st, r, st.read(a, 4))
            else:
                st.write(a, 4, (pc + 8) & _M32 if r == 15 else _a32_rd(st, r, pc))
        if W and not (L and rn in regs):
            _a32_wr(st, rn, nb)
    if L and 15 in regs:
        return "s", "ret" if rn == 13 else "br register", "ldm pc"
    return "n", 0, "ldm" if L else "stm"


def _a32_block(st, w: int, pc: int):
    P, U, S, W, L = (w >> 24) & 1, (w >> 23) & 1, (w >> 22) & 1, (w >> 21) & 1, (w >> 20) & 1
    rn, lst = (w >> 16) & 15, w & 0xFFFF
    if S or rn == 15 or not lst:
        return "s", "instruksi tak didukung", "?"
    return _blk(st, pc, rn, [i for i in range(16) if lst >> i & 1], U, P, W, L)


def _a32_exec(st, w: int, pc: int):
    """Eksekusi satu kata A32 yang syaratnya sudah terpenuhi (bukan cabang B / BL)."""
    top = (w >> 25) & 7
    if (w & 0x0FFFFFD0) == 0x012FFF10:                     # BX / BLX register
        if w & 0x20:
            _a32_clobber(st)
            return "n", 0, "blx"
        return ("s", "ret", "bx lr") if (w & 15) == 14 else ("s", "br register", "bx")
    if (w & 0x0FFFFF00) == 0x0320F000:
        return "n", 0, "nop/hint"
    if (w & 0x0F000000) == 0x0F000000:                     # SVC: hanya r0 berubah
        st.rk[0] = 0
        return "n", 0, "svc"
    if top >= 6:
        return "s", "instruksi tak didukung", "?"          # koprosesor / VFP / NEON
    if top == 4:
        return _a32_block(st, w, pc)
    if top in (2, 3):
        if top == 3 and w & 0x10:
            return "s", "instruksi tak didukung", "?"
        return _a32_mem(st, w, pc)
    if top == 0 and (w & 0x90) == 0x90:
        if not (w & 0x60):
            if (w & 0x0FC000F0) == 0x00000090:             # MUL / MLA
                rd, ra, rs, rm = (w >> 16) & 15, (w >> 12) & 15, (w >> 8) & 15, w & 15
                a, b = _a32_rd(st, rm, pc), _a32_rd(st, rs, pc)
                acc = _a32_rd(st, ra, pc) if (w >> 21) & 1 else 0
                r = None if a is None or b is None or acc is None else (a * b + acc) & _M32
                if (w >> 20) & 1:
                    st.fl = [None, None, st.fl[2], st.fl[3]] if r is None else [r >> 31, int(r == 0), st.fl[2], st.fl[3]]
                _a32_wr(st, rd, r)
                return "n", 0, "mul"
            if (w & 0x0F8000F0) == 0x00800090:             # UMULL / SMLAL ...
                _a32_wr(st, (w >> 16) & 15, None)
                _a32_wr(st, (w >> 12) & 15, None)
                if (w >> 20) & 1:
                    st.fl = [None] * 4
                return "n", 0, "mull"
            return "s", "instruksi tak didukung", "?"      # SWP / LDREX / STREX
        return _a32_half(st, w, pc)
    if top == 1 and (w & 0x0FB00000) == 0x03000000:        # MOVW / MOVT
        rd, imm = (w >> 12) & 15, ((w >> 4) & 0xF000) | (w & 0xFFF)
        if rd == 15:
            return "s", "instruksi tak didukung", "?"
        if w & 0x00400000:
            old = _a32_rd(st, rd, pc)
            _a32_wr(st, rd, None if old is None else (old & 0xFFFF) | (imm << 16))
            return "n", 0, "movt"
        _a32_wr(st, rd, imm)
        return "n", 0, "movw"
    if (w & 0x01900000) == 0x01000000:                     # ruang misc (MRS / MSR / CLZ / QADD ...)
        return "s", "instruksi tak didukung", "?"
    return _a32_dp(st, w, pc)


def _a32_step(st, w: int, pc: int):
    """Satu instruksi A32. (aksi, nilai, mnemonik): 'n' lanjut, 'j' lompat, 'f' fork ke nilai lalu lanjut, 's' berhenti dengan alasan nilai."""
    cond = w >> 28
    if cond == 15:
        if (w & 0xFE000000) == 0xFA000000:                 # BLX imm
            _a32_clobber(st)
            return "n", 0, "blx"
        if (w & 0xFD70F000) == 0xF550F000:                 # PLD
            return "n", 0, "pld"
        return "s", "instruksi tak didukung", "?"
    cv = True if cond == 14 else _a64_cond(st.fl, cond)
    if (w >> 25) & 7 == 5:                                 # B / BL
        if cv is False:
            return "n", 0, "b?"
        if (w >> 24) & 1:
            _a32_clobber(st)
            return "n", 0, "bl"
        t = (pc + 8 + (_a64_s(w & 0xFFFFFF, 24) << 2)) & _M32
        if t & 3:
            return "s", "instruksi tak didukung", "?"
        if cv is None:
            return "f", t, "b." + _A64_COND[cond]
        return "j", t, "b"
    if cv is False:
        return "n", 0, "skip"
    if cv is None:                                         # syarat tak tentu: jalankan di salinan, lalu gabungkan
        s2 = st.fork(pc)
        act, val, mn = _a32_exec(s2, w, pc)
        if act == "s" and val in ("ret", "br register"):
            return "n", 0, mn + "?"                        # kembali / lompat bersyarat: lanjutkan jalur jatuh-tembus
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
    return _a32_exec(st, w, pc)


def _a32_emu_func(d: bytes, L: dict, start: int, end: int, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """Emulasi satu fungsi A32 [start, end). None bila awal tidak bisa dibaca. Tidak pernah melempar karena data biner."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start or start & 3:
        return None
    n_w = min((end - start) // 4, (len(d) - off0) // 4)
    if n_w <= 0:
        return None
    words = struct.unpack("<%dI" % n_w, d[off0:off0 + n_w * 4])
    lim = start + n_w * 4
    top = 0x7FD00000
    s0 = _EmuSt(d, L, _M32, top - 0x100000, top + 0x10000, 16, start)
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
            if not (start <= pc < lim):
                stop = "keluar fungsi"
                break
            w = words[(pc - start) >> 2]
            st.steps += 1
            total += 1
            if st.nw > EMU_MAX_WRITES:
                stop = "batas tulis"
                break
            try:
                act, val, mn = _a32_step(st, w, pc)
            except (ValueError, OverflowError, IndexError, KeyError):
                act, val, mn = "s", "instruksi tak didukung", "?"
            if first and len(tr) < trace_max:
                tr.append((pc, "%08X  %s" % (w, mn), "diambil" if act == "j" else ""))
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
            st.pc = pc + 4
        if len(finals) < EMU_MAX_FINALS:
            finals.append(st)
    return {"steps": total, "forks": forks, "stop": stop, "finals": finals, "trace": tr, "timed": timed}


