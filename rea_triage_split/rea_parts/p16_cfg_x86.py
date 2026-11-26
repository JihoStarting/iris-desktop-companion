# rea_triage bagian 16/47: cfg_x86 (baris asli 5426-6371). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.13 [S3]: CFG, blok dasar, kompleksitas siklomatik, loop (RE Lab x86 / x64) ------------
# Decoder PANJANG instruksi x86 / x86-64 murni Python (tanpa capstone) + penelusuran rekursif dari awal fungsi: blok dasar, sisi (JMP / Jcc / LOOP /
# fall-through), kompleksitas siklomatik (E - N + 2), loop alami (sisi balik), kandidat loop dekripsi (XOR / ADD / SUB / ROL / ROR / SHL / SHR ke memori
# di dalam loop kecil), dan kandidat control-flow flattening (satu blok dispatcher menerima banyak sisi balik). Statis murni; hanya pustaka standar.
# Batasan: lompatan tak langsung (jump table) dihitung sebagai sisi keluar bernama "switch" dan targetnya tidak diselesaikan; kode yang tidak bisa
# didecode menghentikan jalur itu saja (fungsi ditandai tidak lengkap); hasil adalah PETUNJUK. Kunci baru info["cfg"] (RE Lab), aditif.

CFG_TIME = 4.0                  # detik untuk seluruh analisis CFG satu berkas
CFG_MAX_FUNCS = 600             # fungsi yang dianalisis (yang teratas di peringkat + yang terbesar)
CFG_MAX_INSNS = 1_500_000       # total instruksi yang didecode
CFG_MAX_FUNC_INSNS = 40_000     # satu fungsi lebih panjang dari ini dipotong
CFG_MAX_LOOPS = 40              # loop yang dicatat per fungsi

(_M_NONE, _M_MODRM, _M_MODRM_I8, _M_MODRM_IZ, _M_I8, _M_IZ, _M_J8, _M_JMP8, _M_CALL, _M_JMP32, _M_RET, _M_RETI, _M_MOFFS, _M_ENTER,
 _M_G3_8, _M_G3_V, _M_FF, _M_LOOP, _M_MOVI, _M_INV, _M_HALT, _M_ESC, _M_PFX, _M_X, _M_FARPTR) = range(25)
(_K_NORM, _K_JMP, _K_JCC, _K_CALL, _K_RET, _K_JMPI, _K_CALLI, _K_HALT, _K_LOOP) = range(9)
_PFX_LEG = frozenset((0x66, 0x67, 0xF0, 0xF2, 0xF3, 0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65))
_ARITH_GRP = ("add", "or", "adc", "sbb", "and", "sub", "xor", "cmp")


def _mk_x1(is64: bool) -> list:
    t = [_M_NONE] * 256
    for op in range(0x40):
        lo = op & 7
        t[op] = _M_MODRM if lo < 4 else (_M_I8 if lo == 4 else (_M_IZ if lo == 5 else (_M_INV if is64 else _M_NONE)))
    t[0x0F] = _M_ESC
    for p in (0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65, 0x66, 0x67, 0xF0, 0xF2, 0xF3):
        t[p] = _M_PFX
    for op in range(0x40, 0x50):
        t[op] = _M_PFX if is64 else _M_NONE
    t[0x60] = t[0x61] = _M_INV if is64 else _M_NONE
    t[0x62] = _M_X
    t[0x63] = _M_MODRM
    t[0x68], t[0x69], t[0x6A], t[0x6B] = _M_IZ, _M_MODRM_IZ, _M_I8, _M_MODRM_I8
    for op in range(0x70, 0x80):
        t[op] = _M_J8
    t[0x80], t[0x81], t[0x82], t[0x83] = _M_MODRM_I8, _M_MODRM_IZ, (_M_INV if is64 else _M_MODRM_I8), _M_MODRM_I8
    for op in range(0x84, 0x90):
        t[op] = _M_MODRM
    t[0x9A] = _M_INV if is64 else _M_FARPTR
    for op in range(0xA0, 0xA4):
        t[op] = _M_MOFFS
    t[0xA8], t[0xA9] = _M_I8, _M_IZ
    for op in range(0xB0, 0xB8):
        t[op] = _M_I8
    for op in range(0xB8, 0xC0):
        t[op] = _M_MOVI
    t[0xC0] = t[0xC1] = _M_MODRM_I8
    t[0xC2], t[0xC3] = _M_RETI, _M_RET
    t[0xC4] = t[0xC5] = _M_X
    t[0xC6], t[0xC7], t[0xC8] = _M_MODRM_I8, _M_MODRM_IZ, _M_ENTER
    t[0xCA], t[0xCB], t[0xCC], t[0xCD] = _M_RETI, _M_RET, _M_HALT, _M_I8
    t[0xCE] = _M_INV if is64 else _M_NONE
    t[0xCF] = _M_RET
    for op in range(0xD0, 0xD4):
        t[op] = _M_MODRM
    t[0xD4] = t[0xD5] = _M_INV if is64 else _M_I8
    t[0xD6] = _M_INV if is64 else _M_NONE
    for op in range(0xD8, 0xE0):
        t[op] = _M_MODRM
    for op in range(0xE0, 0xE4):
        t[op] = _M_LOOP
    for op in range(0xE4, 0xE8):
        t[op] = _M_I8
    t[0xE8], t[0xE9] = _M_CALL, _M_JMP32
    t[0xEA] = _M_INV if is64 else _M_FARPTR
    t[0xEB] = _M_JMP8
    t[0xF4] = _M_HALT
    t[0xF6], t[0xF7], t[0xFE], t[0xFF] = _M_G3_8, _M_G3_V, _M_MODRM, _M_FF
    return t


_X1_32, _X1_64 = _mk_x1(False), _mk_x1(True)
_X2_NONE = frozenset((0x05, 0x06, 0x07, 0x08, 0x09, 0x0E, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x37, 0x77, 0xA0, 0xA1, 0xA2, 0xA8, 0xA9, 0xAA,
                      0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF))
_X2_I8 = frozenset((0x70, 0x71, 0x72, 0x73, 0xA4, 0xAC, 0xBA, 0xC2, 0xC4, 0xC5, 0xC6, 0x0F))
_X2_BAD = frozenset((0x04, 0x0A, 0x0C, 0x24, 0x25, 0x26, 0x27, 0x36, 0x39, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0xA6, 0xA7))


def _modrm_len(b: bytes, j: int, addr16: bool) -> int:
    """Panjang ModRM + SIB + disp; j = indeks byte ModRM. -1 bila terpotong."""
    if j >= len(b):
        return -1
    m = b[j]
    mod, rm = m >> 6, m & 7
    if addr16:
        return 1 + ((2 if rm == 6 else 0) if mod == 0 else (1 if mod == 1 else (2 if mod == 2 else 0)))
    n = 1
    if mod != 3 and rm == 4:
        if j + 1 >= len(b):
            return -1
        n += 1
        if mod == 0 and (b[j + 1] & 7) == 5:
            n += 4
    if mod == 0:
        if rm == 5:
            n += 4
    elif mod == 1:
        n += 1
    elif mod == 2:
        n += 4
    return n


def _x86_dec(b: bytes, i: int, is64: bool):
    """Satu instruksi di b[i:] -> (panjang, jenis, rel, bendera, mnemonik) atau None.
    bendera: 1 = operasi aritmetika / rotasi / geser, 2 = operan memori, 4 = menulis ke memori."""
    n0, nb = i, len(b)
    opsz16 = addr = False
    cnt = 0
    while i < nb and cnt < 14 and b[i] in _PFX_LEG:
        if b[i] == 0x66:
            opsz16 = True
        elif b[i] == 0x67:
            addr = True
        i += 1
        cnt += 1
    if i >= nb:
        return None
    rexw, rex = False, 0
    if is64 and 0x40 <= b[i] <= 0x4F:
        rex = b[i]
        rexw = bool(b[i] & 8)
        i += 1
        if i >= nb:
            return None
        if 0x40 <= b[i] <= 0x4F or b[i] in _PFX_LEG:      # REX tidak persis di depan opcode: CPU mengabaikannya; dihitung sebagai 1 instruksi sendiri
            return i - n0, _K_NORM, 0, 0, ""
    op = b[i]
    i += 1
    cls = (_X1_64 if is64 else _X1_32)[op]
    addr16 = addr and not is64
    izs = 2 if opsz16 else 4
    kind, rel, flags, mn = _K_NORM, 0, 0, ""

    def modrm(i_):
        k = _modrm_len(b, i_, addr16)
        return k

    if cls == _M_INV or cls == _M_PFX:
        return None
    if cls == _M_NONE:
        if op in (0xAA, 0xAB, 0xA4, 0xA5):
            flags = 4
    elif cls == _M_ESC:
        if i >= nb:
            return None
        op2 = b[i]
        i += 1
        if op2 in _X2_BAD:
            return None
        if op2 == 0x0B:
            kind = _K_HALT
        elif 0x80 <= op2 <= 0x8F:
            if i + 4 > nb:
                return None
            rel, kind, i = struct.unpack_from("<i", b, i)[0], _K_JCC, i + 4
        elif op2 in _X2_NONE:
            pass
        else:
            if op2 in (0x38, 0x3A):
                if i >= nb:
                    return None
                i += 1
            m0 = i
            k = modrm(i)
            if k < 0:
                return None
            i += k
            if op2 == 0x3A or op2 in _X2_I8:
                i += 1
            mod = b[m0] >> 6
            if mod != 3 and op2 != 0x1F and op2 != 0x18:
                flags |= 2
            if op2 in (0xA4, 0xA5, 0xAC, 0xAD):
                flags |= 1
                mn = "shd"
            elif op2 == 0xEF:
                if not (mod == 3 and ((b[m0] >> 3) & 7) | ((rex >> 2) & 1) << 3 == (b[m0] & 7) | (rex & 1) << 3):   # pxor reg,reg = nol-kan register, bukan dekripsi
                    flags |= 1
                    mn = "xor"
    elif cls in (_M_MODRM, _M_MODRM_I8, _M_MODRM_IZ, _M_G3_8, _M_G3_V, _M_FF):
        m0 = i
        k = modrm(i)
        if k < 0:
            return None
        i += k
        m = b[m0]
        mod, reg = m >> 6, (m >> 3) & 7
        if cls == _M_MODRM_I8 or (cls == _M_G3_8 and reg < 2):
            i += 1
        elif cls == _M_MODRM_IZ or (cls == _M_G3_V and reg < 2):
            i += izs
        if cls == _M_FF:
            if reg in (2, 3):
                kind = _K_CALLI
            elif reg in (4, 5):
                kind = _K_JMPI
        if mod != 3 and op != 0x8D:
            flags |= 2
        mem = mod != 3
        if op < 0x40 and (op & 7) < 6 and (op >> 3) != 7:
            flags |= 1
            mn = _ARITH_GRP[op >> 3]
            if op in (0x30, 0x31, 0x32, 0x33) and mod == 3 and (reg | ((rex >> 2) & 1) << 3) == ((m & 7) | (rex & 1) << 3):
                flags, mn = flags & ~1, ""     # xor reg,reg = nol-kan register, bukan operasi dekripsi
            if mem and (op & 2) == 0:
                flags |= 4
        elif op in (0x80, 0x81, 0x83) and reg != 7:
            flags |= 1
            mn = _ARITH_GRP[reg]
            if mem:
                flags |= 4
        elif op in (0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3) and reg in (0, 1, 4, 5):
            flags |= 1
            mn = ("rol", "ror", "", "", "shl", "shr")[reg]
            if mem:
                flags |= 4
        elif op in (0x88, 0x89, 0xC6, 0xC7) and mem:
            flags |= 4
    elif cls == _M_I8 or cls == _M_IZ:
        i += 1 if cls == _M_I8 else izs
        if op < 0x40 and (op & 7) in (4, 5) and (op >> 3) != 7:      # op AL / eAX, imm
            flags, mn = 1, _ARITH_GRP[op >> 3]
    elif cls == _M_J8 or cls == _M_JMP8 or cls == _M_LOOP:
        if i >= nb:
            return None
        rel = b[i] - 256 if b[i] >= 128 else b[i]
        kind = _K_JCC if cls == _M_J8 else (_K_JMP if cls == _M_JMP8 else _K_LOOP)
        i += 1
    elif cls == _M_CALL or cls == _M_JMP32:
        if i + 4 > nb:
            return None
        rel = struct.unpack_from("<i", b, i)[0]
        kind = _K_CALL if cls == _M_CALL else _K_JMP
        i += 4
    elif cls == _M_RET:
        kind = _K_RET
    elif cls == _M_RETI:
        kind = _K_RET
        i += 2
    elif cls == _M_HALT:
        kind = _K_HALT
    elif cls == _M_MOFFS:
        i += (8 if is64 else 4) if not (addr and not is64) else 2
        if op in (0xA2, 0xA3):
            flags = 6
        else:
            flags = 2
    elif cls == _M_ENTER:
        i += 3
    elif cls == _M_MOVI:
        i += 8 if (rexw and is64) else izs
    elif cls == _M_FARPTR:
        i += 6 if not opsz16 else 4
    elif cls == _M_X:       # VEX / EVEX (atau LES / LDS / BOUND pada mode 32-bit)
        if not is64 and (i >= nb or b[i] < 0xC0):
            k = modrm(i)
            if k < 0:
                return None
            i += k
            flags |= 2
        elif op == 0xC5:
            if i + 2 > nb:
                return None
            o2 = b[i + 1]
            i += 2
            if o2 != 0x77:
                k = modrm(i)
                if k < 0:
                    return None
                i += k + (1 if (o2 in _X2_I8 and o2 != 0x0F) else 0)
        elif op == 0xC4:
            if i + 3 > nb:
                return None
            mp, o2 = b[i] & 0x1F, b[i + 2]
            i += 3
            if not (mp == 1 and o2 == 0x77):
                k = modrm(i)
                if k < 0:
                    return None
                i += k + (1 if (mp == 3 or (mp == 1 and o2 in _X2_I8 and o2 != 0x0F)) else 0)
        else:               # EVEX 62
            if i + 4 > nb:
                return None
            mp, o2 = b[i] & 7, b[i + 3]
            i += 4
            k = modrm(i)
            if k < 0:
                return None
            i += k + (1 if (mp == 3 or (mp == 1 and o2 in _X2_I8 and o2 != 0x0F)) else 0)
    n = i - n0
    if n > 15 or i > nb:
        return None
    return n, kind, rel, flags, mn


def _cfg_func(d: bytes, L: dict, start: int, end: int, is64: bool, want_blocks: bool = False) -> dict | None:
    """CFG satu fungsi [start, end). None bila awal fungsi tidak bisa dibaca."""
    if L.get("arch") == "arm64":
        return _a64_cfg_func(d, L, start, end, want_blocks)
    if L.get("arch") == "arm":
        return _arm32_cfg_func(d, L, start, end, want_blocks)      # v99.30: A32 / Thumb; tidak pernah memakai decoder x86
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    code = d[off0:off0 + (end - start)]
    insns: dict = {}
    leaders = {start}
    work = [start]
    incomplete = trunc = False
    n_i = 0
    while work and not trunc:
        va = work.pop()
        while start <= va < end and va not in insns:
            r = _x86_dec(code, va - start, is64)
            if r is None:
                incomplete = True
                break
            n_i += 1
            if n_i > CFG_MAX_FUNC_INSNS:
                trunc = incomplete = True
                break
            insns[va] = r
            n, kind, rel = r[0], r[1], r[2]
            nxt = va + n
            if kind == _K_JMP:
                t = nxt + rel
                if start <= t < end:
                    leaders.add(t)
                    work.append(t)
                break
            if kind in (_K_JCC, _K_LOOP):
                t = nxt + rel
                if start <= t < end:
                    leaders.add(t)
                    work.append(t)
                leaders.add(nxt)
                va = nxt
                continue
            if kind in (_K_RET, _K_HALT, _K_JMPI):
                break
            va = nxt
    return _cfg_build(start, insns, leaders, incomplete, trunc, want_blocks)


def _a64_brk(w: int) -> tuple[str, int]:
    """v99.27: cabang-register AArch64 termasuk varian PAC (arm64e / -mbranch-protection). -> (jenis, Rn); jenis 'ret' | 'br' | 'blr' | ''."""
    m = w & 0xFFFFFC1F
    if m == 0xD65F0000:
        return "ret", (w >> 5) & 31
    if m == 0xD61F0000 or m in (0xD61F081F, 0xD61F0C1F) or (w & 0xFFFFF800) == 0xD71F0800:        # BR / BRAAZ / BRABZ / BRAA / BRAB
        return "br", (w >> 5) & 31
    if m == 0xD63F0000 or m in (0xD63F081F, 0xD63F0C1F) or (w & 0xFFFFF800) == 0xD73F0800:        # BLR / BLRAAZ / BLRABZ / BLRAA / BLRAB
        return "blr", (w >> 5) & 31
    if w in (0xD65F0BFF, 0xD65F0FFF):                                                              # RETAA / RETAB
        return "ret", 30
    return "", 0


def _a64_cfg_func(d: bytes, L: dict, start: int, end: int, want_blocks: bool = False) -> dict | None:
    """CFG satu fungsi AArch64 [start, end): B / B.cond / CBZ / CBNZ / TBZ / TBNZ / RET / BR (jump table = switch) / BRK. BL dan BLR bukan akhir blok."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    n_w = min((end - start) // 4, len(d) // 4 + 1)
    code = d[off0:off0 + n_w * 4]
    n_w = len(code) // 4
    if n_w <= 0:
        return None
    words = struct.unpack("<%dI" % n_w, code[:n_w * 4])
    lim = start + n_w * 4
    insns: dict = {}
    leaders = {start}
    work = [start]
    incomplete = trunc = False
    while work and not trunc:
        va = work.pop()
        while start <= va < lim and va not in insns:
            if len(insns) >= CFG_MAX_FUNC_INSNS:
                trunc = incomplete = True
                break
            w = words[(va - start) >> 2]
            nxt = va + 4
            fl, mn, kind, tgt = 0, "", _K_NORM, None
            if (w & 0xFC000000) == 0x14000000:
                kind, tgt = _K_JMP, va + (_a64_s(w & 0x3FFFFFF, 26) << 2)
            elif (w & 0xFF000010) == 0x54000000:
                kind, tgt = _K_JCC, va + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2)
            elif (w & 0x7E000000) == 0x34000000:
                kind, tgt = _K_JCC, va + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2)
            elif (w & 0x7E000000) == 0x36000000:
                kind, tgt = _K_JCC, va + (_a64_s((w >> 5) & 0x3FFF, 14) << 2)
            elif (w & 0xFC000000) == 0x94000000:
                kind = _K_CALL
            elif _a64_brk(w)[0] == "blr":
                kind = _K_CALLI
            elif _a64_brk(w)[0] == "ret" or w in (0xD69F03E0, 0xD6BF03E0):
                kind = _K_RET
            elif _a64_brk(w)[0] == "br":
                kind = _K_JMPI
            elif (w & 0xFFE0001F) == 0xD4200000 or w == 0:
                kind = _K_HALT
            elif (w & 0x7F800000) == 0x52000000 or (w & 0x7F200000) == 0x4A000000:
                fl, mn = 1, "xor"
            elif (w & 0x7FA00000) == 0x13800000:
                fl, mn = 1, "ror"
            elif (w & 0x1F000000) == 0x11000000 or (w & 0x1F200000) == 0x0B000000:
                fl, mn = 1, "sub" if (w >> 30) & 1 else "add"
            elif (w & 0x7F800000) in (0x53000000, 0x13000000):
                immr, imms = (w >> 16) & 63, (w >> 10) & 63
                fl, mn = 1, ("shr" if imms >= immr else "shl")
            if ((w >> 25) & 5) == 4:                       # keluarga load / store
                fl |= 2
                if not (w >> 22) & 1:
                    fl |= 4
            insns[va] = (4, kind, (tgt - nxt) if tgt is not None else 0, fl, mn)
            if kind == _K_JMP:
                if tgt is not None and start <= tgt < lim:
                    leaders.add(tgt)
                    work.append(tgt)
                break
            if kind == _K_JCC:
                if start <= tgt < lim:
                    leaders.add(tgt)
                    work.append(tgt)
                leaders.add(nxt)
                va = nxt
                continue
            if kind in (_K_RET, _K_HALT, _K_JMPI):
                break
            va = nxt
    if not insns:
        return None
    return _cfg_build(start, insns, leaders, incomplete, trunc, want_blocks)


def _arm_mode_at(L: dict, va: int):
    """v99.30: mode kode ARM 32-bit di va -> ('a' | 't', batas_atas_va); None bila wilayah data ($d) atau di luar bagian kode."""
    regs = L.get("arm_regions")
    if regs is None:
        return ("t" if va in (L.get("thumb") or ()) else "a"), 1 << 62
    i = bisect.bisect_right(L["arm_region_lo"], va) - 1
    if i < 0:
        return None
    lo, hi, k = regs[i]
    return (k, hi) if lo <= va < hi and k in ("a", "t") else None


def _a32_kind(w: int, va: int) -> tuple:
    """v99.30: satu kata A32 -> (jenis, target | None, fl, mn). Target -1 = keluar fungsi (kembali / lompat bersyarat tanpa target)."""
    cond = w >> 28
    if cond == 15:
        return (_K_CALL if (w & 0xFE000000) == 0xFA000000 else _K_NORM), None, 0, ""         # BLX imm; sisanya ruang tanpa syarat (PLD dll)
    top = (w >> 25) & 7
    if top == 5:                                                                               # B / BL
        if w & 0x01000000:
            return _K_CALL, None, 0, ""
        return (_K_JMP if cond == 14 else _K_JCC), va + 8 + (_a64_s(w & 0xFFFFFF, 24) << 2), 0, ""
    ex = (_K_RET, _K_JMPI)
    def leave(k):
        return (k if cond == 14 else _K_JCC), (None if cond == 14 else -1), 0, ""
    if (w & 0x0FFFFFD0) == 0x012FFF10:                                                         # BX Rm / BLX Rm
        if w & 0x20:
            return _K_CALLI, None, 0, ""
        return leave(_K_RET if (w & 15) == 14 else _K_JMPI)
    if (w & 0x0E108000) == 0x08108000:                                                         # LDM / POP {..., pc}
        return leave(_K_RET)
    if (w & 0x0C10F000) == 0x0410F000:                                                         # LDR pc, [...]
        return leave(_K_RET if w == 0xE49DF004 else _K_JMPI)
    if top < 2 and ((w >> 12) & 15) == 15 and not (top == 0 and (w & 0x90) == 0x90):          # operasi data menulis pc
        op = (w >> 21) & 15
        if not 8 <= op <= 11:
            if (op == 13 and (w & 0xFFF) == 0x00E) or (op == 2 and ((w >> 16) & 15) == 14):    # MOV pc, lr / SUBS pc, lr, #n
                return leave(_K_RET)
            return leave(_K_JMPI)
    if (w & 0xFFF000F0) in (0xE1200070, 0xE7F000F0) or w == 0:                                 # BKPT / UDF / padding nol
        return _K_HALT, None, 0, ""
    fl, mn = 0, ""
    if top == 0 and (w & 0x90) == 0x90:                                                        # halfword / signed load-store (multiply tidak)
        if w & 0x60:
            fl = 2 | (0 if (w >> 20) & 1 else 4)
    elif top < 2:
        op = (w >> 21) & 15
        if op == 1:
            fl, mn = 1, "xor"
        elif op in (2, 3):
            fl, mn = 1, "sub"
        elif op == 4:
            fl, mn = 1, "add"
        elif op == 13 and top == 0:
            typ, sh = (w >> 5) & 3, (w >> 7) & 31
            if (w & 0x10) or sh:
                if typ == 3 and not (w & 0x10) and not sh:
                    pass
                else:
                    fl, mn = 1, ("shl", "shr", "shr", "ror")[typ]
    elif top in (2, 3) and not (top == 3 and (w & 0x10)):                                      # LDR / STR
        fl = 2 | (0 if (w >> 20) & 1 else 4)
    elif top == 4:                                                                             # LDM / STM
        fl = 2 | (0 if (w >> 20) & 1 else 4)
    return _K_NORM, None, fl, mn


def _thumb16_kind(h: int, va: int) -> tuple:
    """v99.30: satu halfword Thumb 16-bit -> (jenis, target | None, fl, mn). PC Thumb = alamat + 4."""
    pc = va + 4
    t = h >> 11
    if t == 0x1C:                                                                              # B (T2)
        return _K_JMP, pc + (_a64_s(h & 0x7FF, 11) << 1), 0, ""
    if (h >> 12) == 0xD:
        c = (h >> 8) & 15
        if c < 14:                                                                             # B<c> (T1)
            return _K_JCC, pc + (_a64_s(h & 0xFF, 8) << 1), 0, ""
        return (_K_HALT if c == 14 else _K_NORM), None, 0, ""                                  # UDF / SVC
    if (h & 0xF500) == 0xB100:                                                                 # CBZ / CBNZ
        return _K_JCC, pc + ((((h >> 9) & 1) << 6) | (((h >> 3) & 31) << 1)), 0, ""
    if (h & 0xFF00) == 0xBE00:                                                                 # BKPT
        return _K_HALT, None, 0, ""
    if (h & 0xFE00) == 0xBC00 and h & 0x100:                                                   # POP {..., pc}
        return _K_RET, None, 0, ""
    if (h & 0xFF87) == 0x4700 or (h & 0xFF87) == 0x4687:                                       # BX Rm / MOV pc, Rm
        return (_K_RET if ((h >> 3) & 15) == 14 else _K_JMPI), None, 0, ""
    if (h & 0xFF87) == 0x4487:                                                                 # ADD pc, Rm
        return _K_JMPI, None, 0, ""
    if (h & 0xFF87) == 0x4780:                                                                 # BLX Rm
        return _K_CALLI, None, 0, ""
    fl, mn = 0, ""
    hi = h >> 12
    if (h & 0xF800) == 0x1800:
        fl, mn = 1, ("sub" if h & 0x200 else "add")
    elif (h >> 13) == 0:
        if t == 0 and ((h >> 6) & 31):
            fl, mn = 1, "shl"
        elif t in (1, 2):
            fl, mn = 1, "shr"
    elif (h >> 13) == 1:
        if t == 2:
            fl, mn = 1, "add"
        elif t == 3:
            fl, mn = 1, "sub"
    elif (h & 0xFC00) == 0x4000:
        op = (h >> 6) & 15
        mn = {1: "xor", 7: "ror", 5: "add", 6: "sub", 9: "sub", 2: "shl", 3: "shr", 4: "shr"}.get(op, "")
        fl = 1 if mn else 0
    elif (h & 0xFF00) == 0x4400:
        fl, mn = 1, "add"
    elif hi == 5:
        fl = 2 | (4 if ((h >> 9) & 7) < 3 else 0)
    elif hi in (6, 7, 8, 9, 0xC) or (h & 0xF600) == 0xB400:
        fl = 2 | (0 if h & 0x800 else 4)
    elif (h & 0xF800) == 0x4800:
        fl = 2
    return _K_NORM, None, fl, mn


def _thumb32_kind(h: int, h2: int, va: int) -> tuple:
    """v99.30: satu instruksi Thumb-2 32-bit (h, h2) -> (jenis, target | None, fl, mn)."""
    pc = va + 4
    if (h & 0xF800) == 0xF000:
        if (h2 & 0xC000) == 0xC000:                                                            # BL / BLX imm
            return _K_CALL, None, 0, ""
        if (h2 & 0xD000) == 0x9000:                                                            # B.W (T4)
            S = (h >> 10) & 1
            i1, i2 = (~((h2 >> 13) ^ S)) & 1, (~((h2 >> 11) ^ S)) & 1
            return _K_JMP, pc + _a64_s((S << 24) | (i1 << 23) | (i2 << 22) | ((h & 0x3FF) << 12) | ((h2 & 0x7FF) << 1), 25), 0, ""
        if (h2 & 0xD000) == 0x8000 and ((h >> 6) & 15) < 14:                                   # B<c>.W (T3)
            S, J1, J2 = (h >> 10) & 1, (h2 >> 13) & 1, (h2 >> 11) & 1
            return _K_JCC, pc + _a64_s((S << 20) | (J2 << 19) | (J1 << 18) | ((h & 0x3F) << 12) | ((h2 & 0x7FF) << 1), 21), 0, ""
    if (h & 0xFFF0) == 0xF7F0 and (h2 & 0xF000) == 0xA000:                                     # UDF.W
        return _K_HALT, None, 0, ""
    if (h & 0xFFF0) == 0xE8D0 and (h2 & 0xFFE0) == 0xF000:                                     # TBB / TBH
        return _K_JMPI, None, 0, ""
    if (h == 0xE8BD or (h & 0xFFD0) == 0xE890) and h2 & 0x8000:                                # POP.W / LDM.W {..., pc}
        return _K_RET, None, 0, ""
    if (h & 0xFFF0) == 0xF850 and (h2 >> 12) == 15:                                            # LDR.W pc, [...]
        return (_K_RET if (h == 0xF85D and h2 == 0xFB04) else _K_JMPI), None, 0, ""
    if (h & 0xFFF0) == 0xF8D0 and (h2 >> 12) == 15:
        return _K_JMPI, None, 0, ""
    fl, mn = 0, ""
    if (h & 0xFE00) == 0xEA00:                                                                 # operasi data (register bergeser)
        op, typ = (h >> 5) & 15, (h2 >> 4) & 3
        amt = (((h2 >> 12) & 7) << 2) | ((h2 >> 6) & 3)
        if op == 4:
            fl, mn = 1, "xor"
        elif op == 8:
            fl, mn = 1, "add"
        elif op == 13:
            fl, mn = 1, "sub"
        elif op == 2 and (h & 15) == 15 and (amt or typ in (1, 2)):                            # MOV / LSL / LSR / ASR / ROR imm
            fl, mn = 1, ("shl", "shr", "shr", "ror")[typ]
    elif (h & 0xFA00) == 0xF000 and not (h2 & 0x8000):                                         # operasi data (konstanta modifikasi)
        op = (h >> 5) & 15
        mn = {4: "xor", 8: "add", 13: "sub"}.get(op, "")
        fl = 1 if mn else 0
        if not mn and (h & 0xFBF0) in (0xF200, 0xF2A0):                                        # ADDW / SUBW
            fl, mn = 1, ("add" if (h & 0xFBF0) == 0xF200 else "sub")
    elif (h & 0xFF80) == 0xFA00 and (h2 & 0xF0F0) == 0xF000:                                   # geser dengan register
        fl, mn = 1, ("shl", "shr", "shr", "ror")[(h >> 5) & 3]
    elif (h & 0xFE00) in (0xF800, 0xE800):                                                     # LDR / STR / LDM / STM / LDRD / STRD
        fl = 2 | (0 if (h >> 4) & 1 else 4)
    return _K_NORM, None, fl, mn


def _a32_cfg_func(d: bytes, L: dict, start: int, end: int, want_blocks: bool = False) -> dict | None:
    """v99.30: CFG satu fungsi A32 [start, end). Kata A32 selalu 4 byte."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start or start & 3:
        return None
    n_w = min((end - start) // 4, (len(d) - off0) // 4)
    if n_w <= 0:
        return None
    words = struct.unpack("<%dI" % n_w, d[off0:off0 + n_w * 4])
    lim = start + n_w * 4
    insns: dict = {}
    leaders = {start}
    work = [start]
    incomplete = trunc = False
    while work and not trunc:
        va = work.pop()
        while start <= va < lim and va not in insns:
            if len(insns) >= CFG_MAX_FUNC_INSNS:
                trunc = incomplete = True
                break
            kind, tgt, fl, mn = _a32_kind(words[(va - start) >> 2], va)
            nxt = va + 4
            insns[va] = (4, kind, (tgt - nxt) if tgt is not None else 0, fl, mn)
            if kind == _K_JMP:
                if tgt is not None and start <= tgt < lim and not tgt & 3:
                    leaders.add(tgt)
                    work.append(tgt)
                break
            if kind == _K_JCC:
                if start <= tgt < lim and not tgt & 3:
                    leaders.add(tgt)
                    work.append(tgt)
                leaders.add(nxt)
                va = nxt
                continue
            if kind in (_K_RET, _K_HALT, _K_JMPI):
                break
            va = nxt
    return _cfg_build(start, insns, leaders, incomplete, trunc, want_blocks)


def _thumb_cfg_func(d: bytes, L: dict, start: int, end: int, want_blocks: bool = False) -> dict | None:
    """v99.30: CFG satu fungsi Thumb / Thumb-2 [start, end). Blok IT: cabang di dalam IT bersyarat (JMP -> JCC, kembali / lompat tak langsung -> JCC keluar)."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start or start & 1:
        return None
    n_h = min((end - start) // 2, (len(d) - off0) // 2)
    if n_h <= 0:
        return None
    hws = struct.unpack("<%dH" % n_h, d[off0:off0 + n_h * 2])
    lim = start + n_h * 2
    insns: dict = {}
    leaders = {start}
    work = [start]
    incomplete = trunc = False
    while work and not trunc:
        va = work.pop()
        it_left = 0
        while start <= va < lim and va not in insns:
            if len(insns) >= CFG_MAX_FUNC_INSNS:
                trunc = incomplete = True
                break
            j = (va - start) >> 1
            h = hws[j]
            if (h >> 11) in (0x1D, 0x1E, 0x1F):
                if j + 1 >= n_h:
                    incomplete = True
                    break
                n = 4
                kind, tgt, fl, mn = _thumb32_kind(h, hws[j + 1], va)
            else:
                n = 2
                kind, tgt, fl, mn = _thumb16_kind(h, va)
            nxt = va + n
            if it_left > 0:
                it_left -= 1
                if kind == _K_JMP:
                    kind = _K_JCC
                elif kind in (_K_RET, _K_JMPI):
                    kind, tgt = _K_JCC, -1
            elif n == 2 and (h & 0xFF00) == 0xBF00 and h & 15:                                 # IT: jumlah instruksi = 4 - posisi bit terendah
                it_left = 4 - ((h & -h & 15).bit_length() - 1)
            insns[va] = (n, kind, (tgt - nxt) if tgt is not None else 0, fl, mn)
            if kind == _K_JMP:
                if tgt is not None and start <= tgt < lim and not tgt & 1:
                    leaders.add(tgt)
                    work.append(tgt)
                break
            if kind == _K_JCC:
                if start <= tgt < lim and not tgt & 1:
                    leaders.add(tgt)
                    work.append(tgt)
                leaders.add(nxt)
                va = nxt
                continue
            if kind in (_K_RET, _K_HALT, _K_JMPI):
                break
            va = nxt
    return _cfg_build(start, insns, leaders, incomplete, trunc, want_blocks)


def _arm32_cfg_func(d: bytes, L: dict, start: int, end: int, want_blocks: bool = False) -> dict | None:
    """v99.30: CFG fungsi ARM 32-bit; mode (A32 / Thumb) dari wilayah di `start`, batas atas dipotong di akhir wilayah. None bila wilayah data / tak dikenal."""
    m = _arm_mode_at(L, start)
    if m is None:
        return None
    kind, hi = m
    end = min(end, hi)
    return (_thumb_cfg_func if kind == "t" else _a32_cfg_func)(d, L, start, end, want_blocks)


def _cfg_build(start: int, insns: dict, leaders: set, incomplete: bool, trunc: bool, want_blocks: bool = False) -> dict | None:
    """Blok dasar, sisi, kompleksitas siklomatik, loop (dipakai decoder x86 dan AArch64)."""
    if not insns:
        return None
    # blok dasar
    order = sorted(insns)
    blocks: list = []                 # [va_awal, va_akhir_instruksi_terakhir]
    bidx: dict = {}
    cur = None
    for k, va in enumerate(order):
        r = insns[va]
        if cur is None or va in leaders or order[k - 1] + insns[order[k - 1]][0] != va:
            cur = [va, va]
            blocks.append(cur)
        cur[1] = va
        bidx[va] = len(blocks) - 1
        if r[1] in (_K_JMP, _K_JCC, _K_LOOP, _K_RET, _K_HALT, _K_JMPI):
            cur = None
    succ: list = [[] for _ in blocks]
    n_switch = n_exit_ext = 0
    for bi, (a, z) in enumerate(blocks):
        n, kind, rel = insns[z][0], insns[z][1], insns[z][2]
        nxt = z + n
        tg = []
        if kind == _K_JMP:
            tg = [z + n + rel]
        elif kind in (_K_JCC, _K_LOOP):
            tg = [z + n + rel, nxt]
        elif kind == _K_JMPI:
            n_switch += 1
        elif kind not in (_K_RET, _K_HALT):
            tg = [nxt]
        for t in tg:
            if t in bidx and bidx[t] != -1 and blocks[bidx[t]][0] == t:
                if bidx[t] not in succ[bi]:
                    succ[bi].append(bidx[t])
            else:
                n_exit_ext += 1
    N = len(blocks)
    E = sum(len(s) for s in succ)
    cc = E - N + 2 + n_switch
    # sisi balik (DFS iteratif)
    color = [0] * N
    back: list = []
    stack = [(0, 0)]
    color[0] = 1
    while stack:
        u, k = stack[-1]
        if k < len(succ[u]):
            stack[-1] = (u, k + 1)
            v = succ[u][k]
            if color[v] == 0:
                color[v] = 1
                stack.append((v, 0))
            elif color[v] == 1:
                back.append((u, v))
        else:
            color[u] = 2
            stack.pop()
    pred: list = [[] for _ in blocks]
    for u, ss in enumerate(succ):
        for v in ss:
            pred[v].append(u)
    loops: list = []
    for u, v in back[:CFG_MAX_LOOPS]:
        body = {v, u}
        todo = [u]
        while todo:
            x = todo.pop()
            if x == v:
                continue
            for p in pred[x]:
                if p not in body:
                    body.add(p)
                    todo.append(p)
        ni = ops = 0
        mem = store = False
        calls = 0
        mns: list = []
        for bi in body:
            a, z = blocks[bi]
            for va in order[bisect.bisect_left(order, a):bisect.bisect_right(order, z)]:
                r = insns[va]
                ni += 1
                if r[1] == _K_CALL or r[1] == _K_CALLI:
                    calls += 1
                if r[3] & 1:
                    ops += 1
                    if r[4] and r[4] not in mns:
                        mns.append(r[4])
                mem = mem or bool(r[3] & 2)
                store = store or bool(r[3] & 4)
        crypto = bool(ops and mem and store and ni <= 80 and calls <= 1 and any(m_ in ("xor", "add", "sub", "rol", "ror", "shl", "shr", "shd") for m_ in mns)
                      and any(m_ in ("xor", "rol", "ror", "shd") for m_ in mns))
        loops.append({"head": blocks[v][0], "insns": ni, "blocks": len(body), "ops": mns[:5], "crypto": crypto, "calls": calls})
    heads = collections.Counter(v for _u, v in back)
    flat = None
    if N >= 8 and heads:
        hv, hn = heads.most_common(1)[0]
        if hn >= max(6, N // 3):
            flat = {"head": blocks[hv][0], "back_edges": hn, "blocks": N}
    res = {"va": start, "blocks": N, "edges": E, "cc": max(cc, 1), "loops": loops, "insns": len(insns), "incomplete": incomplete, "switch": n_switch,
           "flat": flat, "trunc": trunc}
    if want_blocks:
        res["bl"] = [(blocks[i][0], blocks[i][1] + insns[blocks[i][1]][0], [blocks[j][0] for j in succ[i]], insns[blocks[i][1]][1]) for i in range(N)]
    return res


def _cfg_enrich(info: dict, ctx: dict, d: bytes) -> None:
    """Dipanggil di akhir _re_lab: info["cfg"] (kunci baru) + cc / blok / loop pada info["functions"]. Tidak pernah melempar."""
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
        todo = list(dict.fromkeys(top_va + [s for s, _f in sorted(F.items(), key=lambda kv: -kv[1]["size"])]))[:CFG_MAX_FUNCS]
        deadline = time.monotonic() + CFG_TIME
        done: dict = {}
        tot = bad = 0
        partial = False
        for s in todo:
            if time.monotonic() > deadline or tot > CFG_MAX_INSNS:
                partial = True
                break
            f = F.get(s)
            if not f or s in ctx["thunks"] or f["size"] < 2:
                continue
            e = s + f["size"]
            sec_end = next((b for a, b in xs if a <= s < b), e)
            r = _cfg_func(d, L, s, min(e, sec_end), is64)
            if r is None:
                bad += 1
                continue
            tot += r["insns"]
            if r["incomplete"]:
                bad += 1
            done[s] = r
        nm = lambda s: F[s]["name"] if s in F else "sub_%08X" % s
        for f in info.get("functions", []):
            try:
                r = done.get(int(f["va"], 16))
            except ValueError:
                r = None
            if r:
                f["cc"], f["blocks"], f["loops"] = r["cc"], r["blocks"], len(r["loops"])
        top = sorted(done.values(), key=lambda r: (-r["cc"], r["va"]))[:8]
        dec = []
        for s, r in sorted(done.items()):
            for lp in r["loops"]:
                if lp["crypto"] and len(dec) < 12:
                    dec.append({"func": "0x%X" % s, "name": _clean(nm(s)), "head": "0x%X" % lp["head"], "insns": lp["insns"], "ops": lp["ops"]})
        flat = [{"func": "0x%X" % s, "name": _clean(nm(s)), "head": "0x%X" % r["flat"]["head"], "back_edges": r["flat"]["back_edges"], "blocks": r["flat"]["blocks"]}
                for s, r in sorted(done.items()) if r["flat"]][:6]
        info["cfg"] = {
            "analyzed": len(done), "insns": tot, "incomplete": bad, "partial": partial, "loops": sum(len(r["loops"]) for r in done.values()),
            "switches": sum(1 for r in done.values() if r["switch"]),
            "top": [{"va": "0x%X" % r["va"], "name": _clean(nm(r["va"])), "blocks": r["blocks"], "edges": r["edges"], "cc": r["cc"], "loops": len(r["loops"]),
                     "insns": r["insns"]} for r in top],
            "decrypt_loops": dec, "flatten": flat,
        }
    except Exception as e:
        info["notes"].append("CFG gagal: %s" % type(e).__name__)


def _render_cfg(r: dict, a, compact: bool) -> None:
    c = r.get("cfg")
    if not c or not c["analyzed"]:
        return
    a("   CFG: %d fungsi / %d instruksi didecode, %d loop%s%s" % (c["analyzed"], c["insns"], c["loops"],
                                                                 (", %d fungsi tidak lengkap" % c["incomplete"]) if c["incomplete"] else "",
                                                                 " | TERPOTONG (batas waktu / ukuran)" if c["partial"] else ""))
    for x in c["decrypt_loops"][: (2 if compact else 8)]:
        a("   ! kandidat loop dekripsi: %s %s (loop @%s, %d instruksi; %s)" % (x["name"], x["func"], x["head"], x["insns"], "/".join(x["ops"])))
    for x in c["flatten"][: (1 if compact else 4)]:
        a("   ! kandidat control-flow flattening: %s %s (dispatcher @%s, %d sisi balik, %d blok)" % (x["name"], x["func"], x["head"], x["back_edges"], x["blocks"]))
    if compact:
        return
    for x in c["top"][:6]:
        a("   kompleksitas: %s %s cc=%d (%d blok, %d sisi, %d loop, %d instruksi)" % (x["name"], x["va"], x["cc"], x["blocks"], x["edges"], x["loops"], x["insns"]))


def cfg_text(path, at=None) -> str:
    """Ringkasan CFG (tanpa `at`) atau daftar blok dasar satu fungsi (at = 'entry' / 0xVA). CLI --cfg, API action 'cfg'."""
    try:
        info, ctx, err = _relab_multi(*_cfg_read(path))
    except Exception as e:
        return "CFG gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if not info:
        return "CFG: %s." % (err or "tidak ada kode yang bisa dianalisis")
    if at is None:
        L: list = []
        _render_cfg(info, L.append, False)
        return "\n".join(L) if L else "CFG: tidak ada fungsi yang bisa dianalisis."
    Lx, fl = ctx["L"], ctx["fl"]
    try:
        va = Lx["entry_va"] if str(at).lower() == "entry" else int(str(at), 0)
    except ValueError:
        return "CFG: alamat tidak valid (pakai entry atau 0xVA)."
    i = bisect.bisect_right(fl, va) - 1
    if i < 0:
        return "CFG: tidak ada fungsi yang memuat 0x%X." % va
    s = fl[i]
    xs = [(Lx["base"] + x["va"], Lx["base"] + x["va"] + max(x["vsize"], x["rsize"])) for x in Lx["xsecs"]]
    sec_end = next((b for a_, b in xs if a_ <= s < b), s)
    e = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
    r = _cfg_func(_cfg_read(path)[0], Lx, s, e, Lx["is64"], want_blocks=True)
    if not r:
        return "CFG: fungsi di 0x%X tidak bisa didecode." % s
    out = ["Fungsi 0x%X: %d blok, %d sisi, cc=%d, %d loop%s%s" % (s, r["blocks"], r["edges"], r["cc"], len(r["loops"]), ", tidak lengkap" if r["incomplete"] else "",
                                                               ", %d switch (jump table tak diselesaikan)" % r["switch"] if r["switch"] else "")]
    heads = {lp["head"]: lp for lp in r["loops"]}
    for a_, z_, ss, k in r["bl"][:200]:
        lp = heads.get(a_)
        out.append("  0x%X-0x%X -> %s%s" % (a_, z_, ", ".join("0x%X" % x for x in ss) or "(keluar)",
                                           ("  [kepala loop: %d instruksi, ops %s%s]" % (lp["insns"], "/".join(lp["ops"]) or "-", ", KANDIDAT DEKRIPSI" if lp["crypto"] else "")) if lp else ""))
    if r["flat"]:
        out.append("  ! kandidat control-flow flattening: dispatcher @0x%X, %d sisi balik" % (r["flat"]["head"], r["flat"]["back_edges"]))
    return "\n".join(out)


def _cfg_read(path):
    f_, size = _open_regular(path)
    with f_:
        return f_.read(MAX_SCAN), size


