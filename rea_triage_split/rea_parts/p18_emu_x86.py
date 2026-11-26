# rea_triage bagian 18/47: emu_x86 (baris asli 6919-7620). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.18 [S2]: micro-emulation instruksi terbatas (RE Lab x86 / x64) -----------------------
# Emulator register + memori kecil, murni Python, STATIS (sampel tidak pernah dijalankan; hanya byte di berkas yang ditafsirkan). Tujuan: mendekode string
# yang disusun / diobfuskasi di stack (mov imm + xor / add / sub / rol / ror / not / neg berantai) dan buffer yang didekripsi di tempat oleh loop kecil, yang
# tidak terlihat oleh pemindai pola byte. Himpunan instruksi sengaja kecil: mov / movzx / movsx / lea / ALU / shift & rotate / inc / dec / not / neg / imul /
# push / pop / leave / jmp / jcc / loop / call (dilangkahi). Nilai yang tidak diketahui dilacak per bit (None); cabang yang kondisinya tidak diketahui
# di-fork (EMU_MAX_FORKS). Memori: berkas (baca) + lapisan tulis (overlay) + stack sintetis; tulisan ke alamat tak diketahui dihitung, tidak dipakai.
# Batasan: call tidak diikuti (reg volatil dianggap tak diketahui), tidak ada API / syscall / SSE / string-op (rep movs / stos), jump table tak diselesaikan,
# paritas (jp / jnp) tidak dimodelkan. Hasil adalah PETUNJUK. Kunci baru info["emu"] (RE Lab), aditif; skor tidak berubah.

EMU_TIME = 3.0                  # detik untuk seluruh emulasi satu berkas
EMU_MAX_FUNCS = 400             # fungsi yang diemulasi
EMU_MAX_STEPS = 50_000          # langkah per jalur
EMU_MAX_TOTAL = 2_000_000       # langkah total per berkas
EMU_MAX_FORKS = 16              # fork cabang tak-diketahui per fungsi
EMU_MAX_FINALS = 24             # jalur akhir yang diperiksa per fungsi
EMU_MAX_WRITES = 65_536         # byte tulisan per jalur
EMU_MAX_RESULTS = 40            # string + buffer yang dilaporkan

_M64 = (1 << 64) - 1
_MK = {8: 0xFF, 16: 0xFFFF, 32: 0xFFFFFFFF, 64: _M64}
_EMU_RX_A = re.compile(rb"[\x20-\x7e]{5,}")
_EMU_RX_W = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")
_EMU_STRONG = frozenset(("xor", "rol", "ror", "not", "neg"))
_EMU_SHIFT = {0: "rol", 1: "ror", 4: "shl", 5: "shr", 6: "shl", 7: "sar"}
_EMU_R64 = ("rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi") + tuple("r%d" % i for i in range(8, 16))
_EMU_R32 = ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi") + tuple("r%dd" % i for i in range(8, 16))
_EMU_R16 = ("ax", "cx", "dx", "bx", "sp", "bp", "si", "di") + tuple("r%dw" % i for i in range(8, 16))
_EMU_R8 = ("al", "cl", "dl", "bl", "spl", "bpl", "sil", "dil") + tuple("r%db" % i for i in range(8, 16))
_EMU_R8H = ("ah", "ch", "dh", "bh")
_EMU_CC = ("o", "no", "b", "ae", "e", "ne", "be", "a", "s", "ns", "p", "np", "l", "ge", "le", "g")


def _emu_dec(c: bytes, i: int, is64: bool, va: int):
    """Satu instruksi di c[i:] -> (n, op, a, b, w, x) atau None. Operand: ("i", nilai, w) | ("r", idx, w, hi8) | ("m", base, index, skala, disp, w, seg, rip)."""
    i0 = i
    try:
        osz = seg = False
        while True:
            p = c[i]
            if p == 0x66:
                osz = True
            elif p == 0x67:
                return None
            elif p in (0xF0, 0xF2, 0xF3, 0x2E, 0x3E, 0x26, 0x36):
                pass
            elif p in (0x64, 0x65):
                seg = True
            else:
                break
            i += 1
            if i - i0 > 6:
                return None
        rex = 0
        if is64 and 0x40 <= c[i] <= 0x4F:
            rex = c[i]
            i += 1
        W, Rx, Xx, Bx = bool(rex & 8), (rex >> 2) & 1, (rex >> 1) & 1, rex & 1
        ws = 64 if W else (16 if osz else 32)
        pw = 64 if is64 else (16 if osz else 32)
        op = c[i]
        i += 1

        def rg(idx, w):
            if w == 8 and not rex and 4 <= idx < 8:
                return ("r", idx - 4, 8, True)
            return ("r", idx, w, False)

        def modrm(w):
            nonlocal i
            m = c[i]
            i += 1
            mod, r3, rm = m >> 6, (m >> 3) & 7, m & 7
            regx = r3 | (Rx << 3)
            if mod == 3:
                return r3, regx, rg(rm | (Bx << 3), w)
            base = index = None
            sc, disp, rip = 1, 0, False
            if rm == 4:
                sib = c[i]
                i += 1
                sc = 1 << (sib >> 6)
                ix = ((sib >> 3) & 7) | (Xx << 3)
                index = None if ix == 4 else ix
                bs = sib & 7
                if mod == 0 and bs == 5:
                    disp = struct.unpack_from("<i", c, i)[0]
                    i += 4
                else:
                    base = bs | (Bx << 3)
            elif mod == 0 and rm == 5:
                disp = struct.unpack_from("<i", c, i)[0]
                i += 4
                rip = is64
            else:
                base = rm | (Bx << 3)
            if mod == 1:
                disp += struct.unpack_from("<b", c, i)[0]
                i += 1
            elif mod == 2:
                disp += struct.unpack_from("<i", c, i)[0]
                i += 4
            return r3, regx, ["m", base, index, sc, disp, w, seg, rip]

        def imm(sz, sg=True):
            nonlocal i
            if i + sz > len(c):
                raise IndexError
            v = int.from_bytes(c[i:i + sz], "little", signed=sg)
            i += sz
            return v

        def im(v, w):
            return ("i", v & _MK[w], w)

        def done(opn, a=None, b=None, w=0, x=0):
            n = i - i0

            def fx(o):
                if isinstance(o, list):
                    if o[7]:
                        o[4] += va + n
                        o[7] = False
                    return tuple(o)
                return o
            return (n, opn, fx(a), fx(b), w, x)

        isz = 2 if ws == 16 else 4
        if op < 0x40 and (op & 7) < 6:
            nm, lo = _ARITH_GRP[op >> 3], op & 7
            if lo == 4:
                return done(nm, rg(0, 8), im(imm(1), 8), 8)
            if lo == 5:
                return done(nm, rg(0, ws), im(imm(isz), ws), ws)
            w = 8 if lo in (0, 2) else ws
            _r3, rx, rm = modrm(w)
            ro = rg(rx, w)
            return done(nm, rm, ro, w) if lo < 2 else done(nm, ro, rm, w)
        if op in (0x80, 0x81, 0x83):
            w = 8 if op == 0x80 else ws
            r3, _rx, rm = modrm(w)
            v = imm(1) if op != 0x81 else imm(isz)
            return done(_ARITH_GRP[r3], rm, im(v, w), w)
        if op in (0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B):
            w = 8 if op in (0x84, 0x86, 0x88, 0x8A) else ws
            _r3, rx, rm = modrm(w)
            ro = rg(rx, w)
            nm = "test" if op < 0x86 else ("xchg" if op < 0x88 else "mov")
            return done(nm, ro, rm, w) if op in (0x8A, 0x8B) else done(nm, rm, ro, w)
        if op == 0x8D:
            _r3, rx, rm = modrm(ws)
            if not isinstance(rm, list):
                return None
            return done("lea", rg(rx, ws), rm, ws)
        if op == 0x63 and is64:
            _r3, rx, rm = modrm(32)
            return done("movsx", rg(rx, ws), rm, ws)
        if op == 0x90:
            return done("nop")
        if 0xB0 <= op <= 0xB7:
            return done("mov", rg((op & 7) | (Bx << 3), 8), im(imm(1), 8), 8)
        if 0xB8 <= op <= 0xBF:
            v = imm(8, False) if W else imm(isz)
            return done("mov", rg((op & 7) | (Bx << 3), ws), im(v, ws), ws)
        if op in (0xC6, 0xC7):
            w = 8 if op == 0xC6 else ws
            r3, _rx, rm = modrm(w)
            if r3 != 0:
                return None
            return done("mov", rm, im(imm(1 if op == 0xC6 else isz), w), w)
        if op in (0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3):
            w = 8 if op in (0xC0, 0xD0, 0xD2) else ws
            r3, _rx, rm = modrm(w)
            nm = _EMU_SHIFT.get(r3)
            if nm is None:
                return None
            cnt = im(imm(1, False), 8) if op in (0xC0, 0xC1) else (("i", 1, 8) if op in (0xD0, 0xD1) else rg(1, 8))
            return done(nm, rm, cnt, w)
        if op in (0xF6, 0xF7):
            w = 8 if op == 0xF6 else ws
            r3, _rx, rm = modrm(w)
            if r3 in (0, 1):
                return done("test", rm, im(imm(1 if w == 8 else isz), w), w)
            if r3 in (2, 3):
                return done("not" if r3 == 2 else "neg", rm, None, w)
            return None
        if op in (0xFE, 0xFF):
            w = 8 if op == 0xFE else ws
            r3, _rx, rm = modrm(w)
            if r3 in (0, 1):
                return done("inc" if r3 == 0 else "dec", rm, None, w)
            if op == 0xFF and r3 == 2:
                return done("calli")
            if op == 0xFF and r3 == 6:
                if isinstance(rm, list):
                    rm[5] = pw
                    return done("push", rm, None, pw)
                return done("push", ("r", rm[1], pw, False), None, pw)
            return None
        if not is64 and 0x40 <= op <= 0x4F:
            return done("inc" if op < 0x48 else "dec", rg(op & 7, ws), None, ws)
        if 0x50 <= op <= 0x57:
            return done("push", rg((op & 7) | (Bx << 3), pw), None, pw)
        if 0x58 <= op <= 0x5F:
            return done("pop", rg((op & 7) | (Bx << 3), pw), None, pw)
        if op == 0x68:
            return done("push", im(imm(isz), pw), None, pw)
        if op == 0x6A:
            return done("push", im(imm(1), pw), None, pw)
        if op in (0x69, 0x6B):
            _r3, rx, rm = modrm(ws)
            return done("imul3", rg(rx, ws), rm, ws, imm(isz) if op == 0x69 else imm(1))
        if op == 0xE8:
            return done("call", x=imm(4))
        if op == 0xE9:
            return done("jmp", x=imm(4))
        if op == 0xEB:
            return done("jmp", x=imm(1))
        if 0x70 <= op <= 0x7F:
            return done("jcc", w=op & 15, x=imm(1))
        if 0xE0 <= op <= 0xE3:
            return done(("loopne", "loope", "loop", "jcxz")[op - 0xE0], x=imm(1))
        if op in (0xC3, 0xC2, 0xCB, 0xCA):
            return done("ret")
        if op == 0xC9:
            return done("leave")
        if op in (0xF8, 0xF9, 0xFC, 0xFD):
            return done("clc" if op == 0xF8 else ("stc" if op == 0xF9 else "nop"))
        if op == 0x0F:
            o2 = c[i]
            i += 1
            if o2 in (0xB6, 0xB7, 0xBE, 0xBF):
                sw = 8 if o2 in (0xB6, 0xBE) else 16
                _r3, rx, rm = modrm(sw)
                return done("movzx" if o2 < 0xB8 else "movsx", rg(rx, ws), rm, ws)
            if o2 == 0xAF:
                _r3, rx, rm = modrm(ws)
                return done("imul2", rg(rx, ws), rm, ws)
            if 0x80 <= o2 <= 0x8F:
                return done("jcc", w=o2 & 15, x=imm(4))
            if o2 == 0x1F:
                modrm(ws)
                return done("nop")
            if 0xC8 <= o2 <= 0xCF:
                return done("bswap", rg((o2 & 7) | (Bx << 3), ws), None, ws)
            return None
        return None
    except (IndexError, struct.error):
        return None


class _EmuSt:
    """Satu jalur emulasi: register (nilai + bit-diketahui), flag, overlay memori."""
    __slots__ = ("rv", "rk", "fl", "ov", "nw", "pc", "steps", "ops", "am", "d", "L", "lo", "hi", "unres")

    def __init__(self, d, L, am, lo, hi, nreg, pc):
        self.rv, self.rk, self.fl, self.ov, self.nw = [0] * nreg, [0] * nreg, [None] * 4, {}, 0
        self.pc, self.steps, self.ops, self.am, self.d, self.L, self.lo, self.hi, self.unres = pc, 0, set(), am, d, L, lo, hi, 0

    def fork(self, pc):
        s = _EmuSt.__new__(_EmuSt)
        s.rv, s.rk, s.fl, s.ov, s.nw = self.rv[:], self.rk[:], self.fl[:], dict(self.ov), self.nw
        s.pc, s.steps, s.ops, s.am, s.d, s.L, s.lo, s.hi, s.unres = pc, self.steps, set(self.ops), self.am, self.d, self.L, self.lo, self.hi, self.unres
        return s

    def rb(self, a):
        v = self.ov.get(a, -1)
        if v != -1:
            return v
        if self.lo <= a < self.hi:
            return None
        off = _va_off(self.L, a)
        if off is None or off >= len(self.d):
            return None
        return self.d[off]

    def read(self, a, n):
        v = 0
        for k in range(n):
            b = self.rb((a + k) & self.am)
            if b is None:
                return None
            v |= b << (8 * k)
        return v

    def write(self, a, n, val):
        if self.nw > EMU_MAX_WRITES:
            return
        for k in range(n):
            self.ov[(a + k) & self.am] = None if val is None else (val >> (8 * k)) & 0xFF
        self.nw += n


def _emu_rg(st, i):
    m = st.am
    return st.rv[i] & m if (st.rk[i] & m) == m else None


def _emu_addr(st, o):
    if o[6]:
        return None
    a = o[4]
    if o[1] is not None:
        v = _emu_rg(st, o[1])
        if v is None:
            return None
        a += v
    if o[2] is not None:
        v = _emu_rg(st, o[2])
        if v is None:
            return None
        a += v * o[3]
    return a & st.am


def _emu_get(st, o):
    t = o[0]
    if t == "i":
        return o[1]
    if t == "r":
        idx, w = o[1], o[2]
        if o[3]:
            return (st.rv[idx] >> 8) & 0xFF if (st.rk[idx] & 0xFF00) == 0xFF00 else None
        m = _MK[w]
        return st.rv[idx] & m if (st.rk[idx] & m) == m else None
    a = _emu_addr(st, o)
    return None if a is None else st.read(a, o[5] // 8)


def _emu_put(st, o, val):
    if o[0] == "r":
        idx, w = o[1], o[2]
        if o[3]:
            if val is None:
                st.rk[idx] &= ~0xFF00
            else:
                st.rv[idx] = (st.rv[idx] & ~0xFF00) | ((val & 0xFF) << 8)
                st.rk[idx] |= 0xFF00
        elif w >= 32:
            if val is None:
                st.rk[idx] = 0
            else:
                st.rv[idx], st.rk[idx] = val & _MK[w], st.am
        else:
            m = _MK[w]
            if val is None:
                st.rk[idx] &= ~m
            else:
                st.rv[idx] = (st.rv[idx] & ~m) | (val & m)
                st.rk[idx] |= m
        return
    a = _emu_addr(st, o)
    if a is None:
        st.unres += 1
        return
    st.write(a, o[5] // 8, val)


def _emu_alu(st, opn, a, b, w):
    m, sg = _MK[w], 1 << (w - 1)
    c = 0
    if opn in ("adc", "sbb"):
        if st.fl[0] is None:
            st.fl = [None] * 4
            return None
        c = st.fl[0]
    if opn in ("add", "adc"):
        t = a + b + c
        r = t & m
        st.fl = [int(t > m), int(r == 0), int(bool(r & sg)), int(bool((a ^ r) & (b ^ r) & sg))]
        return r
    if opn in ("sub", "sbb", "cmp"):
        t = a - b - c
        r = t & m
        st.fl = [int(t < 0), int(r == 0), int(bool(r & sg)), int(bool((a ^ b) & (a ^ r) & sg))]
        return r
    r = (a & b) if opn in ("and", "test") else ((a | b) if opn == "or" else (a ^ b))
    st.fl = [0, int(r == 0), int(bool(r & sg)), 0]
    return r


def _emu_shift(st, opn, a, cnt, w):
    m, sg = _MK[w], 1 << (w - 1)
    c = cnt & (63 if w == 64 else 31)
    if c == 0:
        return a
    if opn == "rol":
        k = c % w
        r = ((a << k) | (a >> (w - k))) & m if k else a
        st.fl[0], st.fl[3] = r & 1, None
        return r
    if opn == "ror":
        k = c % w
        r = ((a >> k) | (a << (w - k))) & m if k else a
        st.fl[0], st.fl[3] = int(bool(r & sg)), None
        return r
    if opn == "shl":
        r = (a << c) & m
        cf = (a >> (w - c)) & 1 if c <= w else 0
        of = (int(bool(r & sg)) ^ cf) if c == 1 else None
    elif opn == "shr":
        r = a >> c if c < w else 0
        cf = (a >> (c - 1)) & 1 if c <= w else 0
        of = int(bool(a & sg)) if c == 1 else None
    else:
        sa = a - (1 << w) if a & sg else a
        r = (sa >> min(c, w)) & m
        cf = (sa >> (min(c, w) - 1)) & 1
        of = 0 if c == 1 else None
    st.fl = [cf, int(r == 0), int(bool(r & sg)), of]
    return r


def _emu_cond(fl, cc):
    cf, zf, sf, of = fl
    t = cc >> 1
    if t == 0:
        v = of
    elif t == 1:
        v = cf
    elif t == 2:
        v = zf
    elif t == 3:
        v = None if cf is None or zf is None else int(bool(cf or zf))
    elif t == 4:
        v = sf
    elif t == 5:
        v = None
    elif t == 6:
        v = None if sf is None or of is None else int(sf != of)
    else:
        v = None if zf is None or sf is None or of is None else int(bool(zf or sf != of))
    return None if v is None else (bool(v) != bool(cc & 1))


def _emu_fmt(ins, va, is64=True):
    """Teks satu instruksi hasil _emu_dec (untuk jejak --emu FILE 0xVA)."""
    n, op, a, b, w, x = ins

    def f(o):
        if o is None:
            return ""
        if o[0] == "i":
            return "0x%X" % o[1]
        if o[0] == "r":
            idx, rw = o[1], o[2]
            if o[3]:
                return _EMU_R8H[idx]
            return {64: _EMU_R64, 32: _EMU_R32, 16: _EMU_R16, 8: _EMU_R8}[rw][idx]
        parts = []
        names = _EMU_R64 if is64 else _EMU_R32
        if o[1] is not None:
            parts.append(names[o[1]])
        if o[2] is not None:
            parts.append("%s*%d" % (names[o[2]], o[3]) if o[3] != 1 else names[o[2]])
        s = "+".join(parts)
        if o[4] or not s:
            s += ("%s0x%X" % ("-" if o[4] < 0 else "+", abs(o[4]))) if s else "0x%X" % (o[4] & _M64)
        return "%s[%s]" % ({8: "byte ", 16: "word ", 32: "dword ", 64: "qword "}.get(o[5], ""), ("fs:" if o[6] else "") + s)
    if op in ("jmp", "call", "loop", "loope", "loopne", "jcxz"):
        return "%s 0x%X" % (op, va + n + x)
    if op == "jcc":
        return "j%s 0x%X" % (_EMU_CC[w], va + n + x)
    return (op + " " + ", ".join(t for t in (f(a), f(b)) if t)).strip()


def _emu_func(d: bytes, L: dict, start: int, end: int, is64: bool, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """Emulasi satu fungsi [start, end). None bila awal tidak bisa dibaca. Tidak pernah melempar karena data biner (batas sumber daya di atas)."""
    if L.get("arch") == "arm64":
        return _a64_emu_func(d, L, start, end, deadline, trace_max, max_total)
    if L.get("arch") == "arm":
        return _arm32_emu_func(d, L, start, end, deadline, trace_max, max_total)      # v99.36: A32 (Thumb belum)
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    code = d[off0:off0 + (end - start) + 15]
    am = _M64 if is64 else 0xFFFFFFFF
    top = 0x00007FFE00100000 if is64 else 0x7FD00000
    lo, hi = top - 0x100000, top + 0x10000
    nreg = 16 if is64 else 8
    volatile = (0, 1, 2, 8, 9, 10, 11) if is64 else (0, 1, 2)
    cache: dict = {}
    s0 = _EmuSt(d, L, am, lo, hi, nreg, start)
    s0.rv[4], s0.rk[4] = top, am
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
            if not (start <= pc < end):
                stop = "keluar fungsi"
                break
            ins = cache.get(pc)
            if ins is None:
                ins = cache[pc] = _emu_dec(code, pc - start, is64, pc) or False
            if not ins:
                stop = "instruksi tak didukung"
                break
            n, op, a, b, w, x = ins
            nxt = pc + n
            st.steps += 1
            total += 1
            if st.nw > EMU_MAX_WRITES:
                stop = "batas tulis"
                break
            if op == "mov":
                _emu_put(st, a, _emu_get(st, b))
            elif op in ("add", "sub", "xor", "and", "or", "cmp", "test", "adc", "sbb"):
                zero_idiom = op in ("xor", "sub") and a[0] == "r" and b[0] == "r" and a[1:] == b[1:] and not a[3]
                if zero_idiom:
                    av = bv = 0
                else:
                    av, bv = _emu_get(st, a), _emu_get(st, b)
                if av is None or bv is None:
                    st.fl = [None] * 4
                    r = None
                else:
                    r = _emu_alu(st, op, av, bv, w)
                if op not in ("cmp", "test"):
                    _emu_put(st, a, r)
                    if r is not None and not zero_idiom and op in ("xor", "add", "sub") and not (a[0] == "r" and a[1] in (4, 5)):
                        st.ops.add(op)
            elif op in ("shl", "shr", "sar", "rol", "ror"):
                av, cv = _emu_get(st, a), _emu_get(st, b)
                if av is None or cv is None:
                    st.fl = [None] * 4
                    _emu_put(st, a, None)
                else:
                    _emu_put(st, a, _emu_shift(st, op, av, cv, w))
                    st.ops.add(op)
            elif op in ("inc", "dec"):
                av = _emu_get(st, a)
                if av is None:
                    st.fl[1:] = [None] * 3
                    _emu_put(st, a, None)
                else:
                    cf = st.fl[0]
                    _emu_alu(st, "add" if op == "inc" else "sub", av, 1, w)
                    st.fl[0] = cf
                    _emu_put(st, a, (av + (1 if op == "inc" else -1)) & _MK[w])
            elif op == "not":
                av = _emu_get(st, a)
                _emu_put(st, a, None if av is None else ~av & _MK[w])
                if av is not None:
                    st.ops.add("not")
            elif op == "neg":
                av = _emu_get(st, a)
                if av is None:
                    st.fl = [None] * 4
                    _emu_put(st, a, None)
                else:
                    r = (-av) & _MK[w]
                    st.fl = [int(av != 0), int(r == 0), int(bool(r & (1 << (w - 1)))), int(av == 1 << (w - 1))]
                    _emu_put(st, a, r)
                    st.ops.add("neg")
            elif op == "lea":
                ad = _emu_addr(st, b) if not b[6] else None
                _emu_put(st, a, None if ad is None else ad & _MK[w])
            elif op in ("movzx", "movsx"):
                v = _emu_get(st, b)
                sw_ = b[2] if b[0] == "r" else b[5]       # lebar sumber: reg di indeks 2, memori di indeks 5
                if v is not None and op == "movsx" and v & (1 << (sw_ - 1)):
                    v -= 1 << sw_
                _emu_put(st, a, None if v is None else v & _MK[w])
            elif op == "xchg":
                av, bv = _emu_get(st, a), _emu_get(st, b)
                _emu_put(st, a, bv)
                _emu_put(st, b, av)
            elif op in ("imul2", "imul3"):
                v1 = _emu_get(st, a) if op == "imul2" else _emu_get(st, b)
                v2 = _emu_get(st, b) if op == "imul2" else x & _MK[w]
                st.fl = [None] * 4
                _emu_put(st, a, None if v1 is None or v2 is None else (v1 * v2) & _MK[w])
            elif op == "bswap":
                av = _emu_get(st, a)
                _emu_put(st, a, None if av is None else int.from_bytes(av.to_bytes(w // 8, "little"), "big"))
            elif op == "push":
                sp = _emu_rg(st, 4)
                if sp is None:
                    stop = "rsp tak diketahui"
                    break
                sp = (sp - w // 8) & am
                st.rv[4] = sp
                st.write(sp, w // 8, _emu_get(st, a))
            elif op == "pop":
                sp = _emu_rg(st, 4)
                if sp is None:
                    stop = "rsp tak diketahui"
                    break
                v = st.read(sp, w // 8)
                st.rv[4] = (sp + w // 8) & am
                _emu_put(st, a, v)
            elif op == "leave":
                bp = _emu_rg(st, 5)
                if bp is None:
                    stop = "rbp tak diketahui"
                    break
                sw = 8 if is64 else 4
                v = st.read(bp, sw)
                st.rv[4], st.rk[4] = (bp + sw) & am, am
                st.rv[5], st.rk[5] = (v, am) if v is not None else (0, 0)
            elif op in ("call", "calli"):
                if op == "call" and x == 0:         # call $+5: get-PC, lazim di shellcode
                    sp = _emu_rg(st, 4)
                    if sp is None:
                        stop = "rsp tak diketahui"
                        break
                    sw = 8 if is64 else 4
                    sp = (sp - sw) & am
                    st.rv[4] = sp
                    st.write(sp, sw, nxt)
                else:
                    for r_ in volatile:
                        st.rk[r_] = 0
                    st.fl = [None] * 4
            elif op == "jmp":
                t = nxt + x
                if not (start <= t < end):
                    stop = "lompat keluar fungsi"
                    break
                st.pc = t
                if trace_max and first and len(tr) < trace_max:
                    tr.append((pc, _emu_fmt(ins, pc, is64), ""))
                continue
            elif op == "jcc":
                cv = _emu_cond(st.fl, w)
                t = nxt + x
                if cv is None:
                    if forks < EMU_MAX_FORKS and start <= t < end and len(work) < 32:
                        forks += 1
                        work.append(st.fork(t))
                elif cv:
                    if not (start <= t < end):
                        stop = "lompat keluar fungsi"
                        break
                    st.pc = t
                    if trace_max and first and len(tr) < trace_max:
                        tr.append((pc, _emu_fmt(ins, pc, is64), "diambil"))
                    continue
            elif op in ("loop", "loope", "loopne", "jcxz"):
                cw = 64 if is64 else 32
                cx = _emu_rg(st, 1)
                t = nxt + x
                if cx is None:
                    if forks < EMU_MAX_FORKS and start <= t < end and len(work) < 32:
                        forks += 1
                        work.append(st.fork(t))
                else:
                    if op != "jcxz":
                        cx = (cx - 1) & _MK[cw]
                        st.rv[1], st.rk[1] = cx, am
                    z = st.fl[1]
                    if op == "jcxz":
                        take = cx == 0
                    elif op == "loop":
                        take = cx != 0
                    elif z is None:
                        take = None
                    else:
                        take = cx != 0 and (bool(z) == (op == "loope"))
                    if take is None:
                        stop = "ZF tak diketahui"
                        break
                    if take:
                        if not (start <= t < end):
                            stop = "lompat keluar fungsi"
                            break
                        st.pc = t
                        continue
            elif op == "clc":
                st.fl[0] = 0
            elif op == "stc":
                st.fl[0] = 1
            elif op == "ret":
                stop = "ret"
                break
            elif op == "nop":
                pass
            else:
                stop = "instruksi tak didukung"
                break
            if trace_max and first and len(tr) < trace_max:
                note = ""
                if a is not None and a[0] == "r" and op not in ("cmp", "test", "push", "pop"):
                    v = _emu_get(st, a)
                    note = "%s=0x%X" % (_emu_fmt((0, "", a, None, 0, 0), 0, is64), v) if v is not None else ""
                tr.append((pc, _emu_fmt(ins, pc, is64), note))
            st.pc = nxt
        if len(finals) < EMU_MAX_FINALS:
            finals.append(st)
    return {"steps": total, "forks": forks, "stop": stop, "finals": finals, "trace": tr, "timed": timed}


