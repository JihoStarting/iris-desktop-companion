# rea_triage bagian 32/47: ikon_yara_elf (baris asli 13746-14078). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- hash ikon PE -----------------------


def _icon_hash(d: bytes, pe: dict | None) -> dict | None:
    """MD5 data ikon terbesar + hash gabungan semua ikon: pengelompokan sampel yang memakai ikon sama (mis. ikon dokumen palsu)."""
    if not pe or pe.get("broken"):
        return None
    icons = [x for x in pe.get("res", []) if x.get("type") == "ICON" and x.get("size", 0) > 0]
    if not icons:
        return None
    hs = []
    for x in icons[:48]:
        blob = d[x["off"]:x["off"] + min(x["size"], 1 << 20)]
        if blob:
            hs.append((x["size"], hashlib.md5(blob).hexdigest()))
    if not hs:
        return None
    hs.sort(reverse=True)
    return {"main": hs[0][1], "all": hashlib.md5("".join(h for _s, h in sorted(hs, key=lambda t: t[1])).encode()).hexdigest(), "n": len(hs)}


# ----------------------- YARA opsional -----------------------


def yara_scan(path, rules, max_matches: int = 30) -> dict:
    """Jalankan aturan YARA milikmu (berkas .yar / .yara, atau folder berisi itu) pada berkas. Butuh `pip install yara-python`."""
    try:
        try:
            import yara
        except ImportError:
            return {"ok": False, "error": "pustaka opsional 'yara-python' belum terpasang (pip install yara-python)"}
        rp = Path(str(rules)).expanduser()
        if rp.is_dir():
            cand = sorted(x for x in rp.rglob("*") if x.suffix.lower() in (".yar", ".yara"))[:500]
            files = {"r%d" % i: str(p) for i, p in enumerate(cand)}
        elif rp.is_file():
            files = {"r0": str(rp)}
        else:
            return {"ok": False, "error": "berkas / folder aturan tidak ditemukan"}
        if not files:
            return {"ok": False, "error": "tidak ada berkas .yar / .yara di folder aturan"}
        f, size = _open_regular(path)
        f.close()
        rs = yara.compile(filepaths=files)
        ms = rs.match(filepath=str(Path(str(path)).resolve()), timeout=30)
        out = []
        for m in ms[:max_matches]:
            strs = []
            for sm in getattr(m, "strings", [])[:6]:
                ident = getattr(sm, "identifier", None) or (sm[1] if isinstance(sm, tuple) else "?")
                inst = getattr(sm, "instances", None)
                offs = [hex(i.offset) for i in inst[:3]] if inst else [hex(sm[0])] if isinstance(sm, tuple) else []
                strs.append("%s@%s" % (ident, ",".join(offs)))
            out.append({"rule": m.rule, "tags": list(m.tags), "desc": str(m.meta.get("description", ""))[:120], "strings": strs})
        return {"ok": True, "n_rules": len(files), "matches": out}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def yara_text(path, rules) -> str:
    r = yara_scan(path, rules)
    if not r["ok"]:
        return "YARA gagal: " + _clean(r["error"])
    if not r["matches"]:
        return "YARA: tidak ada aturan yang cocok (%d berkas aturan diperiksa)." % r["n_rules"]
    L = ["YARA: %d aturan cocok" % len(r["matches"])]
    for m in r["matches"]:
        L.append("   - %s%s%s%s" % (_clean(m["rule"]), (" [" + ",".join(m["tags"]) + "]") if m["tags"] else "",
                                    (" | " + _clean(m["desc"])) if m["desc"] else "", (" | " + ", ".join(m["strings"])) if m["strings"] else ""))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# v98.4: RE Lab untuk ELF x86 / x86-64 (little-endian). Memakai mesin RE Lab yang sama: peta panggilan API (PLT / GOT -> nama impor),
# nama fungsi dari .symtab / .dynsym bila ada, xref string, anti-analisis, peringkat fungsi. Statis, hanya pustaka standar.
# ---------------------------------------------------------------------------

_RE_GROUPS["injeksi proses"][0].update({"process_vm_writev", "process_vm_readv"})
_RE_GROUPS["jaringan / C2"][0].update({"bind", "listen", "accept", "sendto", "recvfrom", "inet_addr", "inet_pton", "curl_easy_perform", "curl_easy_setopt", "gethostbyaddr"})
_RE_GROUPS["eksekusi proses"][0].update({"execve", "execv", "execvp", "execl", "execlp", "execle", "popen", "posix_spawn", "posix_spawnp"})
_RE_GROUPS["kripto / enkripsi"][0].update({"evp_encryptinit_ex", "evp_cipherinit_ex", "evp_encryptupdate", "evp_decryptupdate", "aes_set_encrypt_key", "aes_encrypt", "aes_cbc_encrypt"})
_RE_GROUPS["enumerasi berkas"][0].update({"opendir", "readdir", "scandir", "ftw", "nftw", "glob"})
_RE_GROUPS["resolusi API dinamis"][0].update({"dlopen", "dlsym"})
_RE_GROUPS["alokasi / unpack memori"][0].update({"mmap", "mprotect", "mremap"})
_RE_GROUPS["token / hak istimewa"][0].update({"setuid", "setgid", "seteuid", "setresuid", "setresgid", "capset"})
_RE_GROUPS["anti-debug / anti-VM"][0].update({"ptrace", "prctl"})
_RE_GROUPS["ptrace (anti-debug / injeksi ELF)"] = ({"ptrace"}, 1, 3, "T1622 / T1055.008")
_RE_INTR = re.compile(_RE_INTR.pattern + r"|/bin/(?:ba|da|z)?sh\b|/etc/(?:passwd|shadow)|/proc/self|/dev/tcp|crontab|authorized_keys|ld_preload|\.ssh/|/tmp/\.", re.I)


def _elf_relr_decode(d: bytes, off: int, size: int, is64: bool, r2o, base: int, reloc: dict, cap: int = 400000) -> int:
    """v99.44: dekode tabel DT_RELR (relokasi RELATIVE terkompresi) pada d[off:off+size]. Entri genap = alamat slot (lalu slot berikutnya
    di +kata); entri ganjil = bitmap (bit 1..W-1 -> slot di alamat_sekarang + (i-1)*kata, lalu alamat_sekarang += (W-1)*kata).
    Nilai slot dibaca dari berkas (addend implisit, bias muat 0) dan disimpan di reloc[VA slot]. Batas: cap entri peta, ukuran tabel.
    Mengembalikan jumlah slot baru. Entri bitmap sebelum alamat pertama (rusak) diabaikan."""
    ws = 8 if is64 else 4
    fmt = "<Q" if is64 else "<I"
    mask = (1 << (8 * ws)) - 1
    if off is None or off < 0 or off >= len(d) or size <= 0:
        return 0
    size = min(size, len(d) - off, ws * 400000)
    n0 = len(reloc)
    where = None
    bits = 8 * ws - 1

    def put(va):
        if len(reloc) >= cap or va < base:
            return
        so = r2o(va - base)
        if so is None or so + ws > len(d):
            return
        reloc[va] = struct.unpack_from(fmt, d, so)[0] & mask

    for k in range(size // ws):
        if len(reloc) >= cap:
            break
        e = struct.unpack_from(fmt, d, off + k * ws)[0]
        if e & 1 == 0:
            where = e
            put(where)
            where += ws
        elif where is not None:
            for i in range(bits):
                if (e >> (i + 1)) & 1:
                    put(where + i * ws)
            where += bits * ws
    return len(reloc) - n0


def _elf_layout(d: bytes, arm: bool = False) -> dict | None:
    """Peta alamat ELF untuk RE Lab: segmen LOAD, bagian eksekusi, impor (slot GOT -> nama), simbol fungsi. None bila bukan x86 / x86-64 LE
    (arm=True: ARM 32-bit atau AArch64 LE; v99.22, menambah kunci arch / fmt / thumb)."""
    if len(d) < 64 or d[:4] != b"\x7fELF" or d[5] != 1 or d[4] not in (1, 2):
        return None
    is64 = d[4] == 2
    mach = struct.unpack_from("<H", d, 18)[0]
    if arm:
        if mach not in (40, 183) or (mach == 183) != is64:
            return None
    elif mach not in (3, 62) or (mach == 62) != is64:
        return None
    rel_ok = ((21, 22) if mach == 40 else (1025, 1026)) if arm else (6, 7)
    thumb: set[int] = set()
    modes: list[tuple[int, str]] = []       # v99.29: simbol pemetaan ARM ($a / $t / $d) -> (alamat, 'a' | 't' | 'd')
    try:
        if is64:
            entry, phoff, shoff = struct.unpack_from("<QQQ", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 54)
        else:
            entry, phoff, shoff = struct.unpack_from("<III", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 42)
            if arm and mach == 40 and entry & 1:               # v99.29: e_entry ganjil = entry Thumb
                thumb.add(entry & ~1)
                entry &= ~1
        segs = []
        dyn_seg = None
        for i in range(min(phnum, 128)):
            o = phoff + i * phentsz
            if o + (56 if is64 else 32) > len(d):
                break
            if is64:
                pt, pf, poff, va, _pa, fsz, msz, _al = struct.unpack_from("<IIQQQQQQ", d, o)
            else:
                pt, poff, va, _pa, fsz, msz, pf, _al = struct.unpack_from("<IIIIIIII", d, o)
            if pt == 1 and msz:
                segs.append((va, poff, fsz, msz, pf))
            elif pt == 2 and arm:
                dyn_seg = (poff, fsz)                          # v99.44: PT_DYNAMIC (untuk DT_RELR tanpa section header)
        if not segs:
            return None
        base = min(x[0] for x in segs) & ~0xFFF
        size_img = max(x[0] + x[3] for x in segs) - base

        def r2o(rva):
            va = rva + base
            for sv, so, sf, _sm, _pf in segs:
                if sv <= va < sv + sf:
                    o = so + (va - sv)
                    return o if o < len(d) else None
            return None

        sh = []
        if shoff and shnum and shentsz >= (64 if is64 else 40):
            for i in range(min(shnum, 4096)):
                o = shoff + i * shentsz
                if o + (64 if is64 else 40) > len(d):
                    break
                v = struct.unpack_from("<IIQQQQIIQQ" if is64 else "<IIIIIIIIII", d, o)
                sh.append({"name": v[0], "type": v[1], "flags": v[2], "addr": v[3], "off": v[4], "size": v[5], "link": v[6], "info": v[7], "entsz": v[9]})

        def cstr(o, lim=200):
            if o is None or o >= len(d):
                return ""
            e = d.find(b"\0", o, o + lim)
            return d[o:(e if e != -1 else o + lim)].decode("latin-1", "replace")

        shs_off = sh[shstr]["off"] if shstr < len(sh) else 0
        for x in sh:
            x["nm"] = cstr(shs_off + x["name"], 64) if shs_off else ""

        def symtab(si):
            """(nama, nilai, ukuran, tipe, bind, shndx) untuk tabel simbol bagian ke-si."""
            t = sh[si]
            st = sh[t["link"]] if t["link"] < len(sh) else None
            esz = 24 if is64 else 16
            out = []
            if not st:
                return out
            for k in range(min(t["size"] // esz, 60000)):
                o = t["off"] + k * esz
                if o + esz > len(d):
                    break
                if is64:
                    nm, info, _ot, shndx, val, sz = struct.unpack_from("<IBBHQQ", d, o)
                else:
                    nm, val, sz, info, _ot, shndx = struct.unpack_from("<IIIBBH", d, o)
                out.append((cstr(st["off"] + nm), val, sz, info & 0xF, info >> 4, shndx))
            return out
        exports: dict[int, str] = {}
        symcache: dict[int, list] = {}
        for si, t in enumerate(sh):
            if t["type"] in (2, 11):
                symcache[si] = symtab(si)
                for nm, val, _sz, typ, _bd, shndx in symcache[si]:
                    if arm and mach == 40 and typ == 0 and shndx and nm[:2] in ("$a", "$t", "$d") and (len(nm) == 2 or nm[2] == ".") and len(modes) < 200000:
                        modes.append((val & ~1, nm[1]))
                    if typ == 2 and shndx != 0 and val and nm and len(exports) < 30000:
                        if arm and mach == 40:
                            if val & 1:
                                thumb.add(val & ~1)   # simbol Thumb: bit 0 menandai mode, alamat sebenarnya genap
                            exports.setdefault(val & ~1, nm)
                        else:
                            exports.setdefault(val, nm)
        iat: dict[int, str] = {}
        reloc: dict[int, int] = {}          # v99.43: ARM / AArch64: VA slot -> nilai setelah relokasi (R_*_RELATIVE, R_*_ABS dengan simbol terdefinisi)
        rel_rel, rel_abs = ((23, 2) if mach == 40 else (1027, 257)) if arm else (0, 0)
        wmask = 0xFFFFFFFFFFFFFFFF if is64 else 0xFFFFFFFF
        n_symrel = 0
        rel_irel = (160 if mach == 40 else 1032) if arm else 0
        irel: dict[int, int] = {}           # v99.56: VA slot -> VA resolver (R_*_IRELATIVE)
        for t in sh:
            if t["type"] not in (4, 9) or (t["link"] not in symcache and not arm):
                continue
            rs = (24 if is64 else 12) if t["type"] == 4 else (16 if is64 else 8)
            syms = symcache.get(t["link"], [])
            for k in range(min(t["size"] // rs, 200000 if arm else 40000)):
                o = t["off"] + k * rs
                if o + rs > len(d):
                    break
                if is64:
                    roff, rinfo = struct.unpack_from("<QQ", d, o)
                    rsym, rtyp = rinfo >> 32, rinfo & 0xFFFFFFFF
                else:
                    roff, rinfo = struct.unpack_from("<II", d, o)
                    rsym, rtyp = rinfo >> 8, rinfo & 0xFF
                if arm and rtyp in (rel_rel, rel_abs) and len(reloc) < 400000:
                    if t["type"] == 4:
                        add_ = struct.unpack_from("<q" if is64 else "<i", d, o + (16 if is64 else 8))[0]
                    else:                                                   # REL: addend implisit di slot (nilai berkas)
                        so_ = r2o(roff - base) if roff >= base else None
                        add_ = struct.unpack_from("<Q" if is64 else "<I", d, so_)[0] if so_ is not None and so_ + (8 if is64 else 4) <= len(d) else None
                    if add_ is not None:
                        if rtyp == rel_rel and rsym == 0:
                            reloc[roff] = add_ & wmask
                        elif rtyp == rel_abs and 0 < rsym < len(syms) and syms[rsym][5] != 0 and syms[rsym][1]:
                            reloc[roff] = (syms[rsym][1] + add_) & wmask
                if arm and rtyp == rel_irel and rsym == 0 and len(irel) < 4096:                   # v99.56: IRELATIVE: slot diisi hasil resolver (alamat resolver = addend / nilai di slot)
                    if t["type"] == 4:
                        ra_ = struct.unpack_from("<q" if is64 else "<i", d, o + (16 if is64 else 8))[0]
                    else:
                        so_ = r2o(roff - base) if roff >= base else None
                        ra_ = struct.unpack_from("<Q" if is64 else "<I", d, so_)[0] if so_ is not None and so_ + (8 if is64 else 4) <= len(d) else 0
                    if ra_ > 0:
                        irel[roff] = ra_ & wmask
                if arm and rtyp in rel_ok and 0 < rsym < len(syms) and len(reloc) < 400000:     # v99.46: GLOB_DAT / JUMP_SLOT ke simbol terdefinisi
                    _nm0, sval, _sz0, sty, _bd0, sshn = syms[rsym]
                    if sshn != 0 and sval and sty in (0, 1, 2) and roff not in reloc:
                        sadd = struct.unpack_from("<q" if is64 else "<i", d, o + (16 if is64 else 8))[0] if t["type"] == 4 else 0
                        reloc[roff] = (sval + sadd) & wmask
                        n_symrel += 1
                if rtyp in rel_ok and 0 < rsym < len(syms):
                    nm, _v, _sz, _ty, _bd, shndx = syms[rsym]
                    nm = nm.split("@")[0]
                    if shndx == 0 and nm and not nm.startswith(("_ITM_", "__gmon_start__", "__libc_start_main", "__cxa_finalize", "__stack_chk", "__cxa_atexit")):
                        iat[roff] = nm
        n_relr = 0
        if arm:                                                     # v99.44: DT_RELR (relokasi RELATIVE terkompresi)
            relr_found = False
            for t in sh:
                if t["type"] in (19, 0x6FFFFF00) and t["off"] < len(d):
                    relr_found = True
                    n_relr += _elf_relr_decode(d, t["off"], t["size"], is64, r2o, base, reloc)
            if not relr_found and dyn_seg and dyn_seg[0] < len(d):
                dsz = 16 if is64 else 8
                rtab = rsz_ = 0
                for k in range(min(dyn_seg[1] // dsz, 1024)):
                    o = dyn_seg[0] + k * dsz
                    if o + dsz > len(d):
                        break
                    tag, val = struct.unpack_from("<qQ" if is64 else "<iI", d, o)
                    if tag == 0:
                        break
                    if tag in (36, 0x6FFFE000):
                        rtab = val
                    elif tag in (35, 0x6FFFE001):
                        rsz_ = val
                if rtab and rsz_ and rtab >= base:
                    n_relr += _elf_relr_decode(d, r2o(rtab - base), rsz_, is64, r2o, base, reloc)
        secs, xsecs = [], []
        for x in sh:
            if x["flags"] & 2 and x["addr"] and x["size"]:
                rsz = 0 if x["type"] == 8 else x["size"]
                sec = {"name": x["nm"] or "?", "va": x["addr"] - base, "vsize": x["size"], "rsize": rsz, "rptr": x["off"],
                       "flags": ("R" if True else "-") + ("W" if x["flags"] & 1 else "-") + ("X" if x["flags"] & 4 else "-")}
                secs.append(sec)
                if x["flags"] & 4 and x["type"] == 1 and x["off"] < len(d):
                    xsecs.append(sec)
        if not xsecs:   # tanpa section header: pakai segmen LOAD yang dapat dieksekusi
            for sv, so, sf, sm, pf in segs:
                if pf & 1 and sf and so < len(d):
                    sec = {"name": "LOAD_X", "va": sv - base, "vsize": sm, "rsize": sf, "rptr": so, "flags": "R-X"}
                    secs.append(sec)
                    xsecs.append(sec)
        if not xsecs:
            return None
        return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "exports": exports, "r2o": r2o,
                "entry_va": entry if entry else 0, "entry_off": r2o(entry - base) if entry and entry >= base else None, "stripped": not any(t["type"] == 2 for t in sh),
                "arch": ("arm64" if mach == 183 else "arm") if arm else ("x64" if is64 else "x86"), "fmt": "ELF", "thumb": thumb, "stubs": {}, "modes": modes,
                **({"reloc": reloc, "n_relr": n_relr, "n_symrel": n_symrel, "irel": irel} if arm else {})}
    except (struct.error, IndexError, OverflowError):
        return None


