# rea_triage bagian 33/47: arm_layout (baris asli 14079-14418). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.22 (roadmap v2, Tier A butir 4, tahap 1: peta alamat ARM / ARM64; aditif): _arm_layout() menghasilkan peta alamat untuk ELF ARM / AArch64 (LE)
# dan Mach-O ARM / ARM64 (tipis atau fat) dengan bentuk yang sama seperti _elf_layout (base, secs, xsecs, iat, exports, r2o, entry), ditambah
# arch ("arm" | "arm64"), fmt, thumb (alamat fungsi Thumb), stubs (alamat stub -> nama impor, Mach-O) dan encrypted (Mach-O, cryptid != 0).
# Murni stdlib, tidak memakai lief / capstone. Belum disambungkan ke _relab_any: decoder ARM menyusul di tahap berikut.
# ---------------------------------------------------------------------------
MACHO_ARM_CPU = {12: "arm", 0x0100000C: "arm64"}


def _macho_pick_slice(d: bytes) -> int | None:
    """Offset awal irisan Mach-O ARM / ARM64 (fat: arm64 diutamakan), atau None."""
    m = d[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None
        f64, best = m[3] == 0xBF, None
        esz = 32 if f64 else 20
        for i in range(n):
            p = 8 + i * esz
            if p + esz > len(d):
                break
            if f64:
                cpu, _s, off, _size, _a, _r = struct.unpack_from(">IIQQII", d, p)
            else:
                cpu, _s, off, _size, _a = struct.unpack_from(">IIIII", d, p)
            if cpu in MACHO_ARM_CPU and (best is None or cpu == 0x0100000C):
                best = off
        return best
    return 0 if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe") else None


def _macho_chained_binds(d: bytes, sb: int, dataoff: int, datasize: int, base: int, r2o, rebase: dict | None = None) -> dict[int, str]:
    """v99.27 [2d-2b]: slot impor dari LC_DYLD_CHAINED_FIXUPS (Mach-O iOS 15+ / macOS 12+, tanpa bind opcode / indirect symbol).
    Menelusuri rantai pointer per halaman segmen: {VA slot: nama simbol}. Format pointer: 1 / 9 / 12 (arm64e), 2 / 6 (64-bit). Lainnya dilewati. Batas ketat."""
    out: dict[int, str] = {}
    try:
        fx = sb + dataoff
        if datasize < 28 or fx + 28 > len(d):
            return out
        ver, st_off, imp_off, sym_off, n_imp, imp_fmt, _sf = struct.unpack_from("<IIIIIII", d, fx)
        if ver != 0 or n_imp > 100000 or imp_fmt not in (1, 2, 3):
            return out
        isz = {1: 4, 2: 8, 3: 16}[imp_fmt]

        def imp_name(k):
            p = fx + imp_off + k * isz
            if k >= n_imp or p + isz > len(d):
                return ""
            if imp_fmt == 3:
                v = struct.unpack_from("<Q", d, p)[0]
                no = v >> 32
            else:
                no = struct.unpack_from("<I", d, p)[0] >> 9
            q = fx + sym_off + no
            if q >= len(d) or no > datasize:
                return ""
            nm = _macho_cstr(d, q, 200)
            return nm[1:] if nm.startswith("_") else nm
        sis = fx + st_off
        seg_count = struct.unpack_from("<I", d, sis)[0]
        steps = 0
        for si in range(min(seg_count, 64)):
            so = struct.unpack_from("<I", d, sis + 4 + si * 4)[0]
            if not so:
                continue
            q = sis + so
            _sz, page_size, pfmt, seg_off, _mx, pcount = struct.unpack_from("<IHHQIH", d, q)
            if pfmt in (1, 9, 12):
                stride, bindbit, ordmask, nextbits = 8, 62, (0xFFFFFF if pfmt == 12 else 0xFFFF), 0x7FF
            elif pfmt in (2, 6):
                stride, bindbit, ordmask, nextbits = 4, 63, 0xFFFFFF, 0xFFF
            else:
                continue
            for pi in range(min(pcount, 20000)):
                ps = struct.unpack_from("<H", d, q + 22 + pi * 2)[0]
                if ps == 0xFFFF:                                   # NONE: halaman tanpa fixup
                    continue
                if ps & 0x8000:                                    # v99.47: MULTI: indeks ke daftar awal rantai (diakhiri entri ber-bit 0x8000)
                    starts_ = []
                    kx = ps & 0x7FFF
                    for _ in range(64):
                        if q + 22 + kx * 2 + 2 > len(d):
                            break
                        cs = struct.unpack_from("<H", d, q + 22 + kx * 2)[0]
                        starts_.append(cs & 0x7FFF)
                        kx += 1
                        if cs & 0x8000:
                            break
                else:
                    starts_ = [ps]
                for st_ in starts_:
                    va = base + seg_off + pi * page_size + st_
                    while steps < 400000:
                        steps += 1
                        o = r2o(va - base)
                        if o is None or o + 8 > len(d):
                            break
                        v = struct.unpack_from("<Q", d, o)[0]
                        if (v >> bindbit) & 1:
                            nm = imp_name(v & ordmask)
                            if nm:
                                out.setdefault(va, nm)
                        elif rebase is not None and len(rebase) < 400000:     # v99.45: pointer rebase -> alamat tujuan (high8 dibuang)
                            if pfmt in (2, 6):
                                tv = (v & 0xFFFFFFFFF) + (base if pfmt == 6 else 0)
                            else:
                                tv = (v & 0xFFFFFFFF) + base if (v >> 63) & 1 else (v & 0x7FFFFFFFFFF) + (base if pfmt in (9, 12) else 0)   # auth: selalu offset; non-auth: vmaddr (fmt 1) / offset (9, 12)
                            rebase[va] = tv & 0xFFFFFFFFFFFFFFFF
                        nx = (v >> 51) & nextbits
                        if not nx:
                            break
                        va += nx * stride
    except (struct.error, IndexError, OverflowError):
        pass
    return out


def _macho_layout(d: bytes) -> dict | None:
    """Peta alamat Mach-O ARM / ARM64 little-endian untuk RE Lab. None bila bukan ARM / ARM64, rusak, atau tanpa bagian kode."""
    sb = _macho_pick_slice(d)
    if sb is None or sb + 32 > len(d):
        return None
    try:
        m = d[sb:sb + 4]
        is64 = m[0] == 0xCF
        hsz = 32 if is64 else 28
        cpu, _sub, _ft, ncmds, szcmds, _fl = struct.unpack_from("<IIIIII", d, sb + 4)
        arch = MACHO_ARM_CPU.get(cpu)
        if arch is None or (arch == "arm64") != is64:
            return None
        psz = 8 if is64 else 4
        segs, secs_raw = [], []
        symtab = dysym = cfix = None
        entry_off = pc = None
        encrypted = False
        text_va = None
        off, end = sb + hsz, min(len(d), sb + hsz + szcmds)
        for _ in range(min(ncmds, 600)):
            if off + 8 > end:
                break
            cmd, csz = struct.unpack_from("<II", d, off)
            if csz < 8 or off + csz > end:
                break
            if cmd in (0x1, 0x19):
                need, ssz = (72, 80) if cmd == 0x19 else (56, 68)
                if csz >= need:
                    if cmd == 0x19:
                        nm, va, vsz, fo, fsz, _mp, ip, ns, _fg = struct.unpack_from("<16sQQQQiiII", d, off + 8)
                    else:
                        nm, va, vsz, fo, fsz, _mp, ip, ns, _fg = struct.unpack_from("<16sIIIIiiII", d, off + 8)
                    segs.append((va, sb + fo, fsz, vsz, ip))
                    if nm.startswith(b"__TEXT") and fo == 0:
                        text_va = va
                    for i in range(min(ns, 256)):
                        p = off + need + i * ssz
                        if p + ssz > off + csz:
                            break
                        if is64:
                            sn, _sg, a, sz, so, _al, _ro, _nr, fl, r1, r2 = struct.unpack_from("<16s16sQQIIIIIII", d, p)
                        else:
                            sn, _sg, a, sz, so, _al, _ro, _nr, fl, r1, r2 = struct.unpack_from("<16s16sIIIIIIIII", d, p)
                        secs_raw.append({"nm": sn.split(b"\0")[0].decode("ascii", "replace"), "addr": a, "size": sz, "off": so, "fl": fl, "r1": r1, "r2": r2, "ip": ip})
            elif cmd == 0x2 and csz >= 24:
                symtab = struct.unpack_from("<IIII", d, off + 8)
            elif cmd == 0xB and csz >= 64:
                dysym = struct.unpack_from("<II", d, off + 8 + 48)   # indirectsymoff, nindirectsyms
            elif cmd == 0x80000034 and csz >= 16 and arch == "arm64":
                cfix = struct.unpack_from("<II", d, off + 8)
            elif cmd == 0x80000028 and csz >= 16:
                entry_off = struct.unpack_from("<Q", d, off + 8)[0]
            elif cmd == 0x5 and csz >= 16:
                flav, cnt = struct.unpack_from("<II", d, off + 8)
                if arch == "arm64" and flav == 6 and csz >= 16 + 33 * 8:
                    pc = struct.unpack_from("<Q", d, off + 16 + 32 * 8)[0]
                elif arch == "arm" and flav == 1 and csz >= 16 + 16 * 4:
                    pc = struct.unpack_from("<I", d, off + 16 + 15 * 4)[0]
            elif cmd in (0x21, 0x2C) and csz >= 20:
                encrypted = struct.unpack_from("<I", d, off + 16)[0] != 0
            off += csz
        body = [x for x in segs if x[2]]
        if not body:
            return None
        base = text_va if text_va is not None else min(x[0] for x in body) & ~0xFFF
        size_img = max(x[0] + x[3] for x in body) - base

        def r2o(rva):
            va = rva + base
            for sv, so, sf, _sm, _ip in body:
                if sv <= va < sv + sf:
                    o = so + (va - sv)
                    return o if o < len(d) else None
            return None
        # tabel simbol
        syms: list[tuple[str, int, int, int, int]] = []   # (nama, n_type, n_sect, n_desc, n_value)
        if symtab:
            so_, ns, sto, stsz = symtab
            esz = 16 if is64 else 12
            for i in range(min(ns, 60000)):
                p = sb + so_ + i * esz
                if p + esz > len(d):
                    break
                if is64:
                    strx, nt, nsect, ndesc, nval = struct.unpack_from("<IBBHQ", d, p)
                else:
                    strx, nt, nsect, ndesc, nval = struct.unpack_from("<IBBHI", d, p)
                nm_ = _macho_cstr(d, sb + sto + strx, min(200, stsz - strx)) if strx < stsz else ""
                syms.append((nm_[1:] if nm_.startswith("_") else nm_, nt, nsect, ndesc, nval))
        indirect: list[int] = []
        if dysym:
            io, ni = dysym
            for i in range(min(ni, 100000)):
                p = sb + io + i * 4
                if p + 4 > len(d):
                    break
                indirect.append(struct.unpack_from("<I", d, p)[0])

        def ind_name(k):
            if 0 <= k < len(indirect):
                si = indirect[k]
                if si < len(syms) and si < 0x40000000:
                    return syms[si][0]
            return ""
        iat: dict[int, str] = {}
        stubs: dict[int, str] = {}
        secs, xsecs = [], []
        for x in secs_raw:
            typ = x["fl"] & 0xFF
            if typ in (6, 7) and x["size"]:                       # penunjuk simbol (GOT / la_symbol_ptr)
                for k in range(min(x["size"] // psz, 20000)):
                    nm_ = ind_name(x["r1"] + k)
                    if nm_:
                        iat[x["addr"] + k * psz] = nm_
            elif typ == 8 and x["r2"] and x["size"]:               # stub impor (__stubs)
                for k in range(min(x["size"] // x["r2"], 20000)):
                    nm_ = ind_name(x["r1"] + k)
                    if nm_:
                        stubs[x["addr"] + k * x["r2"]] = nm_
            zerofill = typ in (1, 0xC, 0x12)
            sec = {"name": x["nm"], "va": x["addr"] - base, "vsize": x["size"], "rsize": 0 if zerofill else x["size"], "rptr": sb + x["off"],
                   "flags": "R" + ("W" if x["ip"] & 2 else "-") + ("X" if x["ip"] & 4 else "-")}
            secs.append(sec)
            if x["fl"] & 0x80000400 and not zerofill and x["off"] and sb + x["off"] < len(d):
                xsecs.append(sec)
        if not xsecs:
            return None
        reloc_m: dict[int, int] = {}
        if cfix:                                                  # v99.27: chained fixups (iOS 15+); aditif, tidak menimpa nama dari indirect symbol
            for a_, n_ in _macho_chained_binds(d, sb, cfix[0], cfix[1], base, r2o, reloc_m).items():
                iat.setdefault(a_, n_)
        ranges = [(base + s_["va"], base + s_["va"] + s_["vsize"]) for s_ in xsecs]
        exports: dict[int, str] = {}
        thumb: set[int] = set()
        for nm_, nt, nsect, ndesc, nval in syms:
            if nt & 0xE0 or nt & 0x0E != 0x0E or not nm_ or not nsect:   # bukan simbol terdefinisi di section
                continue
            a = nval & ~1 if arch == "arm" else nval
            if any(lo <= a < hi for lo, hi in ranges) and len(exports) < 30000:
                if arch == "arm" and (ndesc & 0x8 or nval & 1):
                    thumb.add(a)
                exports.setdefault(a, nm_)
        ent = 0
        if entry_off is not None and text_va is not None:
            ent = text_va + entry_off
        elif pc:
            ent = pc & ~1 if arch == "arm" else pc
            if arch == "arm" and pc & 1:
                thumb.add(ent)
        return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "stubs": stubs, "exports": exports,
                "r2o": r2o, "entry_va": ent, "entry_off": r2o(ent - base) if ent and ent >= base else None, "stripped": not exports,
                "arch": arch, "fmt": "Mach-O", "thumb": thumb, "encrypted": encrypted, **({"reloc": reloc_m} if reloc_m else {})}
    except (struct.error, IndexError, OverflowError):
        return None


def _arm_layout(d: bytes) -> dict | None:
    """Peta alamat untuk ELF ARM / AArch64 atau Mach-O ARM / ARM64 (LE). None bila format / arsitektur lain atau berkas rusak."""
    if d[:4] == b"\x7fELF":
        L = _elf_layout(d, arm=True)
        if L and L.get("irel"):
            try:
                _arm_ifunc_resolve(d, L)
            except (struct.error, IndexError, OverflowError, ValueError, KeyError, TypeError):
                pass
        return L
    return _macho_layout(d)


IFUNC_TIME = 3.0                    # v99.56: batas waktu total emulasi resolver ifunc per berkas (detik)
IFUNC_WINDOW = 0x400                # v99.56: ukuran jendela fungsi resolver (byte)


def _arm_ifunc_resolve(d: bytes, L: dict) -> None:
    """v99.56: R_*_IRELATIVE (ifunc, glibc / bionic): nilai slot = hasil memanggil resolver. Resolver kecil diemulasi dengan emulator AArch64 / A32 yang ada;
    bila SEMUA jalur kembalinya memberi satu alamat kode yang sama, slot masuk L['reloc'] (BLR / BLX register lewat slot ikut diselesaikan v99.42).
    Beberapa kandidat (resolver bergantung hwcap) atau hasil tak diketahui -> slot dilewati dan dihitung di L['n_irel_skip']. Kunci aditif: n_irel, n_irel_skip."""
    irel = L.get("irel") or {}
    arm64 = L.get("arch") == "arm64"
    deadline = time.monotonic() + IFUNC_TIME
    reloc = L.setdefault("reloc", {})
    done: dict[int, int | None] = {}
    n_ok = n_skip = 0
    xr = [(x["va"] + L["base"], x["va"] + L["base"] + x["vsize"]) for x in L["xsecs"]]
    inx = lambda a: any(lo <= a < hi for lo, hi in xr)
    thumb = L.get("thumb") or set()
    for slot, res in list(irel.items())[:512]:
        if slot in reloc:
            continue
        if res not in done:
            tgt = None
            if time.monotonic() < deadline and inx(res) and res not in thumb and not (res & 1) and (arm64 or not res & 3):
                end = min(res + IFUNC_WINDOW, max(hi for lo, hi in xr if lo <= res < hi))
                r = (_a64_emu_func if arm64 else _a32_emu_func)(d, L, res, end, deadline)
                if r:
                    vals, ok = set(), bool(r["finals"])
                    for st in r["finals"]:
                        o_ = _va_off(L, st.pc)
                        w_ = struct.unpack_from("<I", d, o_)[0] if o_ is not None and o_ + 4 <= len(d) else 0
                        isret = (_a64_brk(w_)[0] == "ret") if arm64 else ((w_ & 0x0FFFFFFF) == 0x012FFF1E)
                        if not isret:
                            ok = False                          # jalur berakhir bukan di RET (batas / tak didukung): hasil tidak lengkap
                            break
                        reg = 0
                        if st.rk[reg] != (_M64 if arm64 else _M32):
                            ok = False
                            break
                        vals.add(st.rv[reg] & (_M64 if arm64 else _M32))
                    if ok and len(vals) == 1:
                        v_ = next(iter(vals))
                        if inx(v_ & ~1) and not (arm64 and v_ & 3):
                            tgt = v_
            done[res] = tgt
        if done[res] is None:
            n_skip += 1
        else:
            reloc[slot] = done[res]
            n_ok += 1
    L["n_irel"], L["n_irel_skip"] = n_ok, n_skip


