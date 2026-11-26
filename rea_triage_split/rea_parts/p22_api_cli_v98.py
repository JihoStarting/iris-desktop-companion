# rea_triage bagian 22/47: api_cli_v98 (baris asli 9253-9415). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- API / CLI v98 --------------------------------


def re_lab_path(path) -> dict:
    """Analisis RE Lab langsung dari path (tanpa hash / triase penuh). Mengembalikan dict (atau {'error': ...})."""
    try:
        f, size = _open_regular(path)
        with f:
            sha = _sha256_of(f, size) if _cache_dir() is not None else None
            if sha:
                hit = _cache_load(sha, "re")
                if hit is not None:
                    return hit
            d = f.read(MAX_SCAN)
        info, _c, err = _relab_multi(d, size)
        if info and sha:
            _cache_store(sha, "re", info, lambda back: _verify_relab(info, back))
        return info or {"error": (err or "tidak ada bagian kode yang bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64, serta ELF / Mach-O AArch64"}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def re_text(path, defang: bool = True, compact: bool = False) -> str:
    r = re_lab_path(path)
    if "error" in r:
        return "RE Lab gagal: " + r["error"]
    L: list[str] = []
    _render_v98({"relab": r}, L.append, compact, defang)
    return "\n".join(L)


def xref_text(path, query: str, max_items: int = 40) -> str:
    """Cari xref: nama API (mis. 'VirtualAlloc'), potongan string, atau VA fungsi. Menunjukkan fungsi pemanggil / pemakai."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        info, ctx, err = _relab_multi(d, size)
        if not ctx:
            return "XREF gagal: %s." % (err or "tidak bisa dianalisis")
        q = str(query).strip()
        ql = q.lower()
        out = []
        for api, vs in ctx["sites"].items():
            if ql in api.lower():
                out.append("API %s: %d lokasi" % (api, len(vs)))
                for va, fs in vs[:max_items]:
                    out.append("   0x%X dalam %s" % (va, ctx["F"][fs]["name"] if fs in ctx["F"] else "?"))
        for e in ctx["sref"].values():
            if ql in e["text"].lower():
                out.append("string 0x%X (%s): %s" % (e["va"], e["kind"], _clean(e["text"])[:100]))
                for fs in sorted(e["funcs"])[:max_items]:
                    out.append("   dipakai oleh %s (0x%X)" % (ctx["F"][fs]["name"], fs))
        try:
            tv = int(q, 0)
            fobj_ = ctx["F"].get(tv)
            if fobj_:
                out.append("fungsi %s 0x%X: %d caller" % (fobj_["name"], tv, fobj_["callers"]))
                for c, fo in ctx["F"].items():
                    if tv in fo["callees"]:
                        out.append("   dipanggil dari %s (0x%X)" % (fo["name"], c))
        except ValueError:
            pass
        return "\n".join(out[:max_items * 3]) if out else "XREF: tidak ada hasil untuk '%s'." % _clean(q)[:60]
    except Exception as e:
        return "XREF gagal: %s: %s" % (type(e).__name__, str(e)[:120])


_CS_ARCHS = {   # nama -> (atribut ARCH, [atribut MODE], label)
    "x86": ("CS_ARCH_X86", ["CS_MODE_32"], "x86"), "x64": ("CS_ARCH_X86", ["CS_MODE_64"], "x64"),
    "arm": ("CS_ARCH_ARM", ["CS_MODE_ARM"], "ARM"), "armbe": ("CS_ARCH_ARM", ["CS_MODE_ARM", "CS_MODE_BIG_ENDIAN"], "ARM BE"),
    "thumb": ("CS_ARCH_ARM", ["CS_MODE_THUMB"], "Thumb"),
    "arm64": ("CS_ARCH_ARM64", ["CS_MODE_ARM"], "AArch64"),
    "mips": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_BIG_ENDIAN"], "MIPS32 BE"), "mipsel": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_LITTLE_ENDIAN"], "MIPS32 LE"),
    "mips64": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_BIG_ENDIAN"], "MIPS64 BE"), "mips64el": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_LITTLE_ENDIAN"], "MIPS64 LE"),
    "ppc": ("CS_ARCH_PPC", ["CS_MODE_32", "CS_MODE_BIG_ENDIAN"], "PowerPC32"), "ppc64": ("CS_ARCH_PPC", ["CS_MODE_64", "CS_MODE_BIG_ENDIAN"], "PowerPC64"),
    "riscv32": ("CS_ARCH_RISCV", ["CS_MODE_RISCV32"], "RISC-V 32"), "riscv64": ("CS_ARCH_RISCV", ["CS_MODE_RISCV64"], "RISC-V 64"),
    "sparc": ("CS_ARCH_SPARC", ["CS_MODE_BIG_ENDIAN"], "SPARC"),
}
_ELF_TO_ARCH = {3: "x86", 62: "x64", 40: "arm", 183: "arm64", 8: "mips", 20: "ppc", 243: "riscv64"}
_MACHO_TO_ARCH = {7: "x86", 0x01000007: "x64", 12: "arm", 0x0100000C: "arm64", 18: "ppc", 0x01000012: "ppc64"}


def _gen_elf_map(d: bytes):
    """ELF -> (arsitektur, entry VA, [(vaddr, offset, filesz)]) atau None."""
    if len(d) < 52 or d[:4] != b"\x7fELF":
        return None
    is64, en = d[4] == 2, ("<" if d[5] == 1 else ">")
    mach = struct.unpack_from(en + "H", d, 18)[0]
    if is64:
        entry, phoff = struct.unpack_from(en + "QQ", d, 24)
        phentsz, phnum = struct.unpack_from(en + "HH", d, 54)
    else:
        entry, phoff = struct.unpack_from(en + "II", d, 24)[0], struct.unpack_from(en + "I", d, 28)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 42)
    segs = []
    for i in range(min(phnum, 128)):
        o = phoff + i * phentsz
        if o + (56 if is64 else 32) > len(d):
            break
        if is64:
            pt, pf, poff, va, _pa, fsz, _m, _a = struct.unpack_from(en + "IIQQQQQQ", d, o)
        else:
            pt, poff, va, _pa, fsz, _m, pf, _a = struct.unpack_from(en + "IIIIIIII", d, o)
        if pt == 1 and fsz:
            segs.append((va, poff, fsz))
    arch = _ELF_TO_ARCH.get(mach, "")
    if arch == "arm" and en == ">":
        arch = "armbe"
    elif arch == "mips":
        arch = ("mips64" if is64 else "mips") if en == ">" else ("mips64el" if is64 else "mipsel")
    elif arch == "ppc" and is64:
        arch = "ppc64"
    elif arch == "riscv64" and not is64:
        arch = "riscv32"
    return arch, entry, segs, "ELF"


def _gen_macho_map(d: bytes):
    """Mach-O tipis / fat (irisan pertama) -> (arsitektur, entry VA, [(vmaddr, fileoff, filesize)]) atau None."""
    base = 0
    if d[:4] in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None
        base = struct.unpack_from(">I", d, 16)[0] if d[3] == 0xBE else struct.unpack_from(">Q", d, 16)[0]
    m = d[base:base + 4]
    if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        e = "<"
    elif m in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
        e = ">"
    else:
        return None
    is64 = 0xCF in (m[0], m[3])
    cpu, _sub, _ft, ncmds, szcmds, _fl = struct.unpack_from(e + "IIIIII", d, base + 4)
    off = base + (32 if is64 else 28)
    end = min(len(d), off + szcmds)
    segs, text_va, entry_off = [], None, None
    for _ in range(min(ncmds, 600)):
        if off + 8 > end:
            break
        cmd, csz = struct.unpack_from(e + "II", d, off)
        if csz < 8 or off + csz > end:
            break
        if cmd in (0x1, 0x19) and csz >= (72 if cmd == 0x19 else 56):
            fmt = e + ("16sQQQQ" if cmd == 0x19 else "16sIIII")
            nm, va, _vsz, fo, fsz = struct.unpack_from(fmt, d, off + 8)
            if fsz:
                segs.append((va, base + fo, fsz))
            if nm.startswith(b"__TEXT"):
                text_va = va
        elif cmd == 0x80000028 and csz >= 16:
            entry_off = struct.unpack_from(e + "Q", d, off + 8)[0]
        off += csz
    entry = 0
    if entry_off is not None and text_va is not None:
        entry = text_va + entry_off
    elif segs:
        entry = segs[0][0]
    arch = _MACHO_TO_ARCH.get(cpu, "")
    return arch, entry, segs, "Mach-O"


