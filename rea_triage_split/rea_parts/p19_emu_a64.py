# rea_triage bagian 19/47: emu_a64 (baris asli 7621-8072). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.25 (roadmap v2, Tier A butir 4, tahap 2c: emulasi mikro AArch64; aditif): _a64_emu_func() mengemulasi satu fungsi AArch64 (X0-X30, SP, NZCV, memori
# overlay yang sama dengan emulator x86) untuk mendekode string / buffer yang dibangun lewat MOVZ / MOVK / ALU / geser / EOR / load-store / STP; hasilnya
# dikumpulkan oleh _emu_collect() yang sama. Himpunan instruksi kecil: MOVZ/MOVK/MOVN, ADD/SUB (imm, reg bergeser, flag), AND/ORR/EOR/ANDS (imm, reg),
# UBFM/SBFM (lsl/lsr/asr/ubfx/uxt/sxt), EXTR (ror), LSLV/LSRV/ASRV/RORV, MADD/MSUB, CSEL/CSINC/CSINV/CSNEG, ADR/ADRP, LDR/STR (imm, imm9, pre/post, reg,
# literal), LDP/STP, B / B.cond / CBZ / CBNZ / TBZ / TBNZ. BL / BLR dilangkahi (x0-x18 dan x30 jadi tidak diketahui), RET / BR menghentikan jalur.
# SIMD / FP / atomik / PAC tidak didukung (jalur berhenti). Statis murni, hanya pustaka standar.
# ---------------------------------------------------------------------------
_A64_COND = ("eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al", "al")


def _a64_bitmask(n: int, imms: int, immr: int, size: int, immediate: bool):
    """DecodeBitMasks (ARM ARM): (wmask, tmask) atau None."""
    v = (n << 6) | (~imms & 0x3F)
    ln = v.bit_length() - 1
    if ln < 1:
        return None
    levels = (1 << ln) - 1
    if immediate and (imms & levels) == levels:
        return None
    s, r = imms & levels, immr & levels
    esize = 1 << ln
    if esize > size:
        return None
    em = (1 << esize) - 1
    welem = (1 << (s + 1)) - 1
    telem = (1 << (((s - r) & levels) + 1)) - 1
    welem = ((welem >> r) | (welem << (esize - r))) & em if r else welem & em
    wm = tm = 0
    for k in range(size // esize):
        wm |= welem << (k * esize)
        tm |= telem << (k * esize)
    return wm, tm


def _a64_rd(st, n: int, sf: int, zr: bool = True):
    if n == 31 and zr:
        return 0
    v = _emu_rg(st, n)
    if v is None:
        return None
    return v if sf else v & 0xFFFFFFFF


def _a64_wr(st, n: int, v, sf: int, zr: bool = True) -> None:
    if n == 31 and zr:
        return
    if v is None:
        st.rv[n], st.rk[n] = 0, 0
        return
    st.rv[n], st.rk[n] = v & (_M64 if sf else 0xFFFFFFFF), _M64


def _a64_cond(fl, cc: int):
    n_, z_, c_, v_ = fl
    base = cc >> 1
    if base == 0:
        r = z_
    elif base == 1:
        r = c_
    elif base == 2:
        r = n_
    elif base == 3:
        r = v_
    elif base == 4:
        r = None if c_ is None or z_ is None else int(c_ and not z_)
    elif base == 5:
        r = None if n_ is None or v_ is None else int(n_ == v_)
    elif base == 6:
        r = None if n_ is None or v_ is None or z_ is None else int((not z_) and n_ == v_)
    else:
        return True
    if r is None:
        return None
    r = bool(r)
    return (not r) if (cc & 1 and cc != 15) else r


def _a64_addsub(st, a: int, b: int, sub: bool, sf: int, setf: bool) -> int:
    w = 64 if sf else 32
    m = (1 << w) - 1
    if sub:
        res = (a - b) & m
        c = int(a >= b)
        v = ((a ^ b) & (a ^ res)) >> (w - 1) & 1
    else:
        res = (a + b) & m
        c = int(a + b > m)
        v = ((a ^ res) & (b ^ res)) >> (w - 1) & 1
    if setf:
        st.fl = [res >> (w - 1) & 1, int(res == 0), c, v]
    return res


def _a64_shift(v: int, typ: int, cnt: int, sf: int) -> int:
    w = 64 if sf else 32
    m = (1 << w) - 1
    cnt %= w
    if typ == 0:
        return (v << cnt) & m
    if typ == 1:
        return v >> cnt
    if typ == 2:
        sv = v - (1 << w) if v >> (w - 1) else v
        return (sv >> cnt) & m
    return ((v >> cnt) | (v << (w - cnt))) & m if cnt else v


def _a64_clobber(st) -> None:
    for r_ in range(19):
        st.rk[r_] = 0
    st.rk[30] = 0
    st.fl = [None] * 4


def _a64_step(st, w: int, pc: int):
    """Satu instruksi. (aksi, nilai, mnemonik): 'n' lanjut, 'j' lompat ke nilai, 'f' fork ke nilai lalu lanjut, 's' berhenti dengan alasan nilai."""
    sf = w >> 31
    rd, rn, rm = w & 31, (w >> 5) & 31, (w >> 16) & 31
    if (w & 0xFFFFF01F) == 0xD503201F:
        return "n", 0, "nop/hint"
    bk_ = _a64_brk(w)[0]
    if bk_ == "ret":
        return "s", "ret", "ret"
    if bk_ == "br":
        return "s", "br register", "br"
    if bk_ == "blr" or (w & 0xFC000000) == 0x94000000 or (w & 0xFFE0001F) == 0xD4000001:
        _a64_clobber(st)
        return "n", 0, "bl/blr/svc"
    if (w & 0xFC000000) == 0x14000000:
        return "j", pc + (_a64_s(w & 0x3FFFFFF, 26) << 2), "b"
    if (w & 0xFF000010) == 0x54000000:
        cv = _a64_cond(st.fl, w & 15)
        t = pc + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2)
        if cv is None:
            return "f", t, "b." + _A64_COND[w & 15]
        return ("j", t, "b." + _A64_COND[w & 15]) if cv else ("n", 0, "b." + _A64_COND[w & 15])
    if (w & 0x7E000000) == 0x34000000:
        v = _a64_rd(st, rd, sf)
        t = pc + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2)
        nz = (w >> 24) & 1
        if v is None:
            return "f", t, "cbnz" if nz else "cbz"
        return ("j", t, "cb") if (v != 0) == bool(nz) else ("n", 0, "cb")
    if (w & 0x7E000000) == 0x36000000:
        v = _a64_rd(st, rd, 1)
        t = pc + (_a64_s((w >> 5) & 0x3FFF, 14) << 2)
        bit = (sf << 5) | ((w >> 19) & 31)
        nz = (w >> 24) & 1
        if v is None:
            return "f", t, "tbnz" if nz else "tbz"
        return ("j", t, "tb") if (((v >> bit) & 1) == nz) else ("n", 0, "tb")
    if (w & 0x9F000000) == 0x90000000:
        imm = _a64_s(((((w >> 5) & 0x7FFFF) << 2) | ((w >> 29) & 3)), 21) << 12
        _a64_wr(st, rd, (pc & ~0xFFF) + imm, 1)
        return "n", 0, "adrp"
    if (w & 0x9F000000) == 0x10000000:
        _a64_wr(st, rd, pc + _a64_s(((((w >> 5) & 0x7FFFF) << 2) | ((w >> 29) & 3)), 21), 1)
        return "n", 0, "adr"
    if (w & 0x1F800000) == 0x12800000:                                  # MOVN / MOVZ / MOVK
        opc, hw, imm = (w >> 29) & 3, (w >> 21) & 3, (w >> 5) & 0xFFFF
        if opc == 1 or (not sf and hw > 1):
            return "s", "instruksi tak didukung", "?"
        pos = hw * 16
        if opc == 0:
            v = ~(imm << pos)
        elif opc == 2:
            v = imm << pos
        else:
            old = _a64_rd(st, rd, sf)
            v = None if old is None else (old & ~(0xFFFF << pos)) | (imm << pos)
        _a64_wr(st, rd, v, sf)
        return "n", 0, ("movn", "?", "movz", "movk")[opc]
    if (w & 0x1F000000) == 0x11000000:                                  # ADD / SUB imm
        sub, setf, shv = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3
        if shv > 1:
            return "s", "instruksi tak didukung", "?"
        imm = ((w >> 10) & 0xFFF) << (12 if shv else 0)
        a = _a64_rd(st, rn, sf, zr=False)
        if a is None:
            if setf:
                st.fl = [None] * 4
            _a64_wr(st, rd, None, sf, zr=bool(setf))
        else:
            r = _a64_addsub(st, a, imm, bool(sub), sf, bool(setf))
            _a64_wr(st, rd, r, sf, zr=bool(setf))
            if rn != 31 and rd != 31:
                st.ops.add("sub" if sub else "add")
        return "n", 0, ("subs" if setf else "sub") if sub else ("adds" if setf else "add")
    if (w & 0x1F200000) == 0x0B000000:                                  # ADD / SUB (reg bergeser)
        sub, setf, typ, imm6 = (w >> 30) & 1, (w >> 29) & 1, (w >> 22) & 3, (w >> 10) & 63
        if typ == 3 or (not sf and imm6 > 31):
            return "s", "instruksi tak didukung", "?"
        a, b = _a64_rd(st, rn, sf), _a64_rd(st, rm, sf)
        if a is None or b is None:
            if setf:
                st.fl = [None] * 4
            _a64_wr(st, rd, None, sf)
        else:
            r = _a64_addsub(st, a, _a64_shift(b, typ, imm6, sf), bool(sub), sf, bool(setf))
            _a64_wr(st, rd, r, sf)
            if not (rd == 31 or rn == 31):
                st.ops.add("sub" if sub else "add")
        return "n", 0, ("subs" if setf else "sub") if sub else ("adds" if setf else "add")
    if (w & 0x1F800000) == 0x12000000 or (w & 0x1F000000) == 0x0A000000:    # AND / ORR / EOR / ANDS (imm atau reg bergeser)
        opc = (w >> 29) & 3
        if (w & 0x1F800000) == 0x12000000:
            bm = _a64_bitmask((w >> 22) & 1, (w >> 10) & 63, (w >> 16) & 63, 64 if sf else 32, True)
            if bm is None or (not sf and (w >> 22) & 1):
                return "s", "instruksi tak didukung", "?"
            b = bm[0]
            zr_rd = opc != 3
            a = _a64_rd(st, rn, sf)
            bsrc = True
        else:
            typ, imm6, inv = (w >> 22) & 3, (w >> 10) & 63, (w >> 21) & 1
            if not sf and imm6 > 31:
                return "s", "instruksi tak didukung", "?"
            bv = _a64_rd(st, rm, sf)
            b = None if bv is None else _a64_shift(bv, typ, imm6, sf)
            if b is not None and inv:
                b = ~b & (_M64 if sf else 0xFFFFFFFF)
            a = _a64_rd(st, rn, sf)
            bsrc = False
            zr_rd = True
        if a is None or b is None:
            if opc == 3:
                st.fl = [None] * 4
            _a64_wr(st, rd, None, sf, zr=not (bsrc and opc != 3))
        else:
            r = (a & b, a | b, a ^ b, a & b)[opc]
            m = _M64 if sf else 0xFFFFFFFF
            if opc == 3:
                st.fl = [r >> ((64 if sf else 32) - 1) & 1, int(r == 0), 0, 0]
            _a64_wr(st, rd, r & m, sf, zr=not (bsrc and opc != 3))
            if opc == 2 and not (rn == rm and not bsrc):
                st.ops.add("xor")
            elif opc == 1 and not bsrc and rn == 31 and (w >> 21) & 1:
                st.ops.add("not")
        return "n", 0, ("and", "orr", "eor", "ands")[opc]
    if (w & 0x1F800000) == 0x13000000:                                  # SBFM / BFM / UBFM
        opc = (w >> 29) & 3
        n_ = (w >> 22) & 1
        if opc == 1 or n_ != sf:
            return "s", "instruksi tak didukung", "?"
        immr, imms, size = (w >> 16) & 63, (w >> 10) & 63, 64 if sf else 32
        bm = _a64_bitmask(n_, imms, immr, size, False)
        a = _a64_rd(st, rn, sf)
        if bm is None or a is None:
            _a64_wr(st, rd, None, sf)
            return "n", 0, "bfm?"
        wm, tm = bm
        m = (1 << size) - 1
        bot = (((a >> immr) | (a << (size - immr))) & m if immr else a) & wm
        if opc == 2:
            r = bot & tm
            if imms + 1 == immr and imms != size - 1:
                st.ops.add("shl")
            elif imms == size - 1 and immr:
                st.ops.add("shr")
        else:
            top = m if (a >> imms) & 1 else 0
            r = (top & ~tm) | (bot & tm)
        _a64_wr(st, rd, r & m, sf)
        return "n", 0, "sbfm" if opc == 0 else "ubfm"
    if (w & 0x7FA00000) == 0x13800000:                                  # EXTR
        lsb = (w >> 10) & 63
        a, b = _a64_rd(st, rn, sf), _a64_rd(st, rm, sf)
        size = 64 if sf else 32
        if a is None or b is None or (not sf and lsb > 31):
            _a64_wr(st, rd, None, sf)
        else:
            _a64_wr(st, rd, (((a << size) | b) >> lsb) & ((1 << size) - 1), sf)
            if rn == rm:
                st.ops.add("ror")
        return "n", 0, "extr"
    if (w & 0x7FE0F000) == 0x1AC02000:                                  # LSLV / LSRV / ASRV / RORV
        a, c = _a64_rd(st, rn, sf), _a64_rd(st, rm, sf)
        typ = (w >> 10) & 3
        if a is None or c is None:
            _a64_wr(st, rd, None, sf)
        else:
            _a64_wr(st, rd, _a64_shift(a, typ, c, sf), sf)
            st.ops.add(("shl", "shr", "shr", "ror")[typ])
        return "n", 0, ("lslv", "lsrv", "asrv", "rorv")[typ]
    if (w & 0x7FE08000) in (0x1B000000, 0x1B008000):                    # MADD / MSUB
        ra = (w >> 10) & 31
        a, b, c = _a64_rd(st, rn, sf), _a64_rd(st, rm, sf), _a64_rd(st, ra, sf)
        if a is None or b is None or c is None:
            _a64_wr(st, rd, None, sf)
        else:
            p = a * b
            _a64_wr(st, rd, (c - p) if (w >> 15) & 1 else (c + p), sf)
        return "n", 0, "madd/msub"
    if (w & 0x1FE00000) == 0x1A800000 and not (w >> 29) & 1:            # CSEL / CSINC / CSINV / CSNEG
        cc, op, o2 = (w >> 12) & 15, (w >> 30) & 1, (w >> 10) & 1
        a, b = _a64_rd(st, rn, sf), _a64_rd(st, rm, sf)
        cv = _a64_cond(st.fl, cc)
        m = _M64 if sf else 0xFFFFFFFF
        if cv is None or (cv and a is None) or (not cv and b is None):
            _a64_wr(st, rd, None, sf)
        elif cv:
            _a64_wr(st, rd, a, sf)
        else:
            _a64_wr(st, rd, [b, (b + 1), ~b, -b][op * 2 + o2] & m, sf)
        return "n", 0, "csel"
    ld = None
    V = (w >> 26) & 1
    if (w & 0x3B000000) == 0x39000000 and not V:                        # LDR / STR unsigned imm
        size = (w >> 30) & 3
        base = _a64_rd(st, rn, 1, zr=False)
        ad = None if base is None else (base + (((w >> 10) & 0xFFF) << size)) & _M64
        ld = (size, (w >> 22) & 3, ad, None)
    elif (w & 0x3B200000) == 0x38000000 and not V:                      # imm9: ldur / post / pre
        size, idx = (w >> 30) & 3, (w >> 10) & 3
        if idx == 2:
            return "s", "instruksi tak didukung", "?"
        base = _a64_rd(st, rn, 1, zr=False)
        off = _a64_s((w >> 12) & 0x1FF, 9)
        ad = None if base is None else (base + (0 if idx == 1 else off)) & _M64
        wb = None if base is None else (base + off) & _M64
        ld = (size, (w >> 22) & 3, ad, (wb, idx) if idx in (1, 3) else None)
    elif (w & 0x3B200C00) == 0x38200800 and not V:                      # reg offset
        size, opt, s_ = (w >> 30) & 3, (w >> 13) & 7, (w >> 12) & 1
        base, idx_ = _a64_rd(st, rn, 1, zr=False), _a64_rd(st, rm, 1)
        if opt not in (2, 3, 6, 7) or base is None or idx_ is None:
            ad = None
            if opt not in (2, 3, 6, 7):
                return "s", "instruksi tak didukung", "?"
        else:
            if opt & 1 == 0:
                idx_ &= 0xFFFFFFFF
                if opt == 6 and idx_ >> 31:
                    idx_ -= 1 << 32
            ad = (base + (idx_ << (size if s_ else 0))) & _M64
        ld = (size, (w >> 22) & 3, ad, None)
    elif (w & 0x3B000000) == 0x18000000 and not V:                      # LDR literal
        opc = (w >> 30) & 3
        if opc == 3:
            return "s", "instruksi tak didukung", "?"
        ld = (2 if opc == 0 else (3 if opc == 1 else 2), 2 if opc == 2 else 1, pc + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2), None)
    if ld is not None:
        size, opc, ad, wb = ld
        n = 1 << size
        if opc == 0:                                                     # store
            val = _a64_rd(st, rd, 1)
            if ad is None:
                st.unres += 1
            else:
                st.write(ad, n, None if val is None else val & ((1 << (8 * n)) - 1))
        else:
            if opc == 1:
                v = None if ad is None else st.read(ad, n)
                sfd = 1 if size == 3 else 0
            elif size == 3 or (opc == 3 and size == 2):
                return "s", "instruksi tak didukung", "?"
            else:
                raw = None if ad is None else st.read(ad, n)
                v = None if raw is None else (raw - (1 << (8 * n)) if raw >> (8 * n - 1) else raw)
                sfd = 1 if opc == 2 else 0
            _a64_wr(st, rd, v, sfd)
        if wb is not None:
            _a64_wr(st, rn, wb[0], 1, zr=False)
        return "n", 0, "str" if opc == 0 else "ldr"
    if (w & 0x3A000000) == 0x28000000 and not V:                        # LDP / STP
        opc, mode, L_ = (w >> 30) & 3, (w >> 23) & 3, (w >> 22) & 1
        if opc not in (0, 2) or mode == 0:
            return "s", "instruksi tak didukung", "?"
        size = 8 if opc == 2 else 4
        rt2 = (w >> 10) & 31
        off = _a64_s((w >> 15) & 0x7F, 7) * size
        base = _a64_rd(st, rn, 1, zr=False)
        ad = None if base is None else (base + (0 if mode == 1 else off)) & _M64
        sfd = 1 if opc == 2 else 0
        if L_:
            for k, r_ in enumerate((rd, rt2)):
                _a64_wr(st, r_, None if ad is None else st.read(ad + k * size, size), sfd)
        else:
            if ad is None:
                st.unres += 1
            else:
                for k, r_ in enumerate((rd, rt2)):
                    v = _a64_rd(st, r_, sfd)
                    st.write(ad + k * size, size, v)
        if mode in (1, 3):
            _a64_wr(st, rn, None if base is None else (base + off) & _M64, 1, zr=False)
        return "n", 0, "ldp" if L_ else "stp"
    return "s", "instruksi tak didukung", "?"


def _a64_emu_func(d: bytes, L: dict, start: int, end: int, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """Emulasi satu fungsi AArch64 [start, end). None bila awal tidak bisa dibaca. Tidak pernah melempar karena data biner."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    code = d[off0:off0 + ((end - start) & ~3)]
    n_w = len(code) // 4
    if n_w <= 0:
        return None
    words = struct.unpack("<%dI" % n_w, code[:n_w * 4])
    lim = start + n_w * 4
    top = 0x00007FFE00100000
    s0 = _EmuSt(d, L, _M64, top - 0x100000, top + 0x10000, 32, start)
    s0.rv[31], s0.rk[31] = top, _M64
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
                act, val, mn = _a64_step(st, w, pc)
            except (ValueError, OverflowError, IndexError):
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


