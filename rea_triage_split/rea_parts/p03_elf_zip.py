# rea_triage bagian 03/47: elf_zip (baris asli 805-1049). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# ELF, ZIP / APK / JAR
# ---------------------------------------------------------------------------


def _parse_elf(d: bytes) -> dict | None:
    if len(d) < 52 or d[:4] != b"\x7fELF":
        return None
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    etype, mach = struct.unpack_from(en + "HH", d, 16)
    out: dict = {"bits": 64 if is64 else 32, "endian": "little" if en == "<" else "big",
                 "type": _ELF_TYPE.get(etype, str(etype)), "arch": _ELF_MACHINE.get(mach, str(mach)),
                 "sections": [], "stripped": None, "interp": "", "wx": [], "exec_stack": False, "nsec": 0, "nseg": 0, "budget_hit": False}
    try:
        if is64:
            phoff, shoff = struct.unpack_from(en + "QQ", d, 32)
            phentsz, phnum, shentsz, shnum, shstrndx = struct.unpack_from(en + "HHHHH", d, 54)
        else:
            phoff, shoff = struct.unpack_from(en + "II", d, 28)
            phentsz, phnum, shentsz, shnum, shstrndx = struct.unpack_from(en + "HHHHH", d, 42)
        out["nseg"], out["nsec"] = phnum, shnum
        for i in range(min(phnum, 64)):
            o = phoff + i * phentsz
            if o + (56 if is64 else 32) > len(d):
                break
            if is64:
                pt, pf, poff, _va, _pa, fsz, _msz, _al = struct.unpack_from(en + "IIQQQQQQ", d, o)
            else:
                pt, poff, _va, _pa, fsz, _msz, pf, _al = struct.unpack_from(en + "IIIIIIII", d, o)
            if pt == 3 and poff < len(d):
                out["interp"] = d[poff:poff + min(fsz, 128)].split(b"\0")[0].decode("latin-1", "replace")
            if pt == 0x6474E551 and pf & 1:
                out["exec_stack"] = True
            if pt == 1 and pf & 2 and pf & 1:
                out["wx"].append("segmen LOAD#%d" % i)
        if shoff and shnum and shentsz >= (64 if is64 else 40):
            hdrs = []
            for i in range(min(shnum, 96)):
                o = shoff + i * shentsz
                if o + (64 if is64 else 40) > len(d):
                    break
                v = struct.unpack_from(en + ("IIQQQQIIQQ" if is64 else "IIIIIIIIII"), d, o)
                hdrs.append((v[0], v[1], v[2], v[4], v[5]))   # nama, tipe, flag, offset, ukuran
            strtab = b""
            if shstrndx < len(hdrs):
                so_, ssz = hdrs[shstrndx][3], hdrs[shstrndx][4]
                strtab = d[so_:so_ + min(ssz, 65536)]
            ent_left = ENT_BUDGET
            for nm, st, fl, off, sz in hdrs:
                e = strtab.find(b"\0", nm)
                name = strtab[nm:(len(strtab) if e == -1 else e)].decode("latin-1", "replace") if nm < len(strtab) else ""
                raw = d[off:off + min(sz, SEC_ENT_SAMPLE)] if st != 8 and off < len(d) else b""
                if len(raw) > ent_left:
                    raw, out["budget_hit"] = b"", True
                ent_left -= len(raw)
                out["sections"].append({"name": name, "size": sz, "ent": _entropy(raw) if raw else 0.0,
                                        "flags": ("W" if fl & 1 else "-") + ("A" if fl & 2 else "-") + ("X" if fl & 4 else "-")})
            out["stripped"] = ".symtab" not in {x["name"] for x in out["sections"]}
            for x in out["sections"]:
                if x["flags"][0] == "W" and x["flags"][2] == "X":
                    out["wx"].append(x["name"] or "?")
    except (struct.error, IndexError, ValueError):
        pass
    return out


_PERM_RE = re.compile(rb"android\.permission\.[A-Z_]+")
_PERM_RE16 = re.compile(rb"(?:a\x00n\x00d\x00r\x00o\x00i\x00d\x00\.\x00p\x00e\x00r\x00m\x00i\x00s\x00s\x00i\x00o\x00n\x00\.\x00)(?:[A-Z_]\x00)+")


_SCAN_EXT = (".dex", ".class", ".js", ".ps1", ".vbs", ".bat", ".cmd", ".sh", ".py", ".xml", ".json", ".txt", ".cfg", ".ini",
             ".html", ".htm", ".hta", ".bin", ".so", ".properties")
_PRIO_EXT = (".dex", ".class", "vbaproject.bin", ".js", ".ps1", ".vbs", ".bat", ".sh", ".hta")
_REL_TARGET = re.compile(rb'Target="((?:https?|file|ftp)://[^"]{4,300})"[^>]*TargetMode="External"|TargetMode="External"[^>]*Target="((?:https?|file|ftp)://[^"]{4,300})"', re.I)


def _zip_entry_count(f, size: int, info: dict | None = None) -> int:
    """Perkiraan jumlah entri dari EOCD / ZIP64 TANPA memuat direktori pusat (ZIP berjuta entri bisa menghabiskan RAM). -1 bila tak terbaca."""
    try:
        tail = min(size, 65535 + 22 + 20)
        f.seek(size - tail)
        buf = f.read(tail)
        i = buf.rfind(b"PK\x05\x06")
        if i < 0 or i + 22 > len(buf):
            return -1
        total = struct.unpack_from("<H", buf, i + 10)[0]
        cd_size = struct.unpack_from("<I", buf, i + 12)[0]
        cd_off = struct.unpack_from("<I", buf, i + 16)[0]
        eocd_off = size - tail + i   # posisi EOCD di berkas
        if (total == 0xFFFF or cd_size == 0xFFFFFFFF) and i >= 20 and buf[i - 20:i - 16] == b"PK\x06\x07":
            z64 = struct.unpack_from("<Q", buf, i - 12)[0]
            if z64 + 56 <= size:
                f.seek(z64)
                rec = f.read(56)
                if len(rec) == 56 and rec[:4] == b"PK\x06\x06":
                    total = struct.unpack_from("<Q", rec, 32)[0]
                    cd_size = struct.unpack_from("<Q", rec, 40)[0]
                    cd_off = struct.unpack_from("<Q", rec, 48)[0]
                    eocd_off = z64
        est = max(total, 0 if cd_size == 0xFFFFFFFF else cd_size // 46)   # 46 = ukuran minimum satu entri direktori pusat
        if cd_size == 0xFFFFFFFF:
            # v103: ukuran direktori pusat tak terpecahkan (EOCD palsu / rekaman ZIP64 rusak): zipfile akan membaca sampai akhir berkas
            # dan mengurai semua entri di situ, walau "total" bilang 1. Batasi dengan jarak direktori pusat -> EOCD.
            span = eocd_off - cd_off if 0 <= cd_off <= eocd_off else size
            est = max(est, span // 46)
        if info is not None:   # v104: ukuran direktori pusat yang akan dibaca zipfile (bila tak terpecahkan: rentang sampai EOCD)
            info["cd_bytes"] = (cd_size if cd_size != 0xFFFFFFFF else (eocd_off - cd_off if 0 <= cd_off <= eocd_off else size))
        return est
    except (OSError, struct.error):
        return -1


def _zip_cd_bytes(src) -> int:
    """v104: ukuran direktori pusat ZIP (byte) TANPA memuatnya; 0 bila tak terbaca. src = path atau file object (posisi dipulihkan)."""
    info: dict = {}
    try:
        if hasattr(src, "read"):
            pos = src.tell()
            try:
                src.seek(0, 2)
                _zip_entry_count(src, src.tell(), info)
            finally:
                src.seek(pos)
        else:
            with open(src, "rb") as f:
                f.seek(0, 2)
                _zip_entry_count(f, f.tell(), info)
    except (OSError, ValueError, TypeError):
        return 0
    return int(info.get("cd_bytes", 0))


def _zread(z, member, limit: int) -> bytes:
    """Baca paling banyak `limit` byte HASIL dekompresi. z.read() tanpa batas rentan zip bomb (1 MB terkompres bisa jadi GB)."""
    with z.open(member) as m:
        return m.read(max(0, limit))


def _zlast(z, low: list[str], name: str):
    """ZipInfo entri TERAKHIR bernama `name` (low = nama berhuruf kecil, urutan sama dengan z.infolist()). zipfile Python dan parser Android /
    Java memakai entri terakhir bila nama ganda; index() mengambil yang pertama, sehingga penyerang bisa menaruh manifest jinak di depan."""
    return z.infolist()[len(low) - 1 - low[::-1].index(name)]


def _parse_zip(src, size: int | None = None) -> dict | None:
    """src: path ATAU file object biner (yang sama dengan yang dibaca triase, supaya tidak dibuka ulang lewat nama)."""
    if not hasattr(src, "read"):
        f_, sz_ = _open_regular(src)
        with f_:
            return _parse_zip(f_, sz_)
    if size is None:
        src.seek(0, 2)
        size = src.tell()
    if not zipfile.is_zipfile(src):
        return None
    out: dict = {"names": [], "n": 0, "unc": 0, "kind": "ZIP", "warn": [], "perms": [], "dex": 0, "nested": [], "ext_rels": [], "_blob": b""}
    _zi: dict = {}
    cnt = _zip_entry_count(src, size, _zi)
    if cnt > MAX_ZIP_ENTRIES:
        out["n"] = cnt
        out["warn"].append("jumlah entri arsip tidak wajar (~%d): tidak diurai (cegah kehabisan memori)" % cnt)
        return out
    if _zi.get("cd_bytes", 0) > MAX_ZIP_CD:   # v104: batasi byte direktori pusat, bukan hanya jumlah entri
        out["n"] = max(cnt, 0)
        out["warn"].append("direktori pusat ZIP terlalu besar (%d byte > %d): tidak diurai (cegah kehabisan memori)" % (_zi["cd_bytes"], MAX_ZIP_CD))
        return out
    with zipfile.ZipFile(src) as z:
        infos = z.infolist()
        out["n"] = len(infos)
        names = [i.filename for i in infos]
        out["names"] = names[:50]
        out["unc"] = sum(i.file_size for i in infos)
        comp = sum(i.compress_size for i in infos) or 1
        out["ratio"] = out["unc"] / comp
        if any(i.flag_bits & 1 for i in infos):
            out["warn"].append("ada entri terenkripsi (kata sandi)")
        if any(n.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", n) or ".." in n.replace("\\", "/").split("/") for n in names):
            out["warn"].append("nama entri berpola path traversal (zip-slip)")
        if out["ratio"] > 200:
            out["warn"].append("rasio kompresi %.0fx (kemungkinan zip bomb)" % out["ratio"])
        low = [n.lower() for n in names]
        for key_ in ("androidmanifest.xml", "meta-inf/manifest.mf"):
            if low.count(key_) > 1:
                out["warn"].append("entri '%s' muncul %d kali di arsip (pola evasion: parser berbeda memilih entri berbeda; yang dianalisis di sini adalah yang TERAKHIR)" % (key_, low.count(key_)))
        if "androidmanifest.xml" in low:
            out["kind"] = "APK (Android)"
            out["dex"] = sum(1 for n in low if re.fullmatch(r"classes\d*\.dex", n))
            try:
                mf = _zread(z, _zlast(z, low, "androidmanifest.xml"), 400000)
                perms = {m.decode() for m in _PERM_RE.findall(mf)}
                perms |= {m.decode("utf-16le", "ignore") for m in _PERM_RE16.findall(mf)}
                out["perms"] = sorted(perms)[:60]
            except Exception:
                pass
            _apk_deep(z, names, low, out)
        elif "meta-inf/manifest.mf" in low:
            out["kind"] = "JAR/WAR (Java)"
            try:
                mf = _zread(z, _zlast(z, low, "meta-inf/manifest.mf"), 4096).decode("utf-8", "replace")
                m = re.search(r"Main-Class:\s*(\S+)", mf)
                out["main"] = m.group(1) if m else ""
            except Exception:
                pass
        elif any(n.endswith(".class") for n in low):
            out["kind"] = "JAR (Java, tanpa manifest)"
        elif "[content_types].xml" in low:
            out["kind"] = "Paket OOXML (docx/xlsx/pptx)" + (" DENGAN makro VBA" if any("vbaproject.bin" in n for n in low) else "")
        out["nested"] = [n for n in names if n.lower().endswith((".exe", ".dll", ".jar", ".apk", ".so", ".dex", ".bat", ".ps1", ".vbs", ".js", ".scr", ".sh", ".hta", ".lnk"))][:25]
        out["nested"] += [n for n in names if "/embeddings/" in n.lower() and n not in out["nested"]][:10]

        # relasi eksternal OOXML (template injection / konten jarak jauh)
        for i in infos:
            if i.filename.lower().endswith(".rels") and i.file_size < 400000 and not i.flag_bits & 1:
                try:
                    for m in _REL_TARGET.findall(_zread(z, i, 200000)):
                        t = (m[0] or m[1]).decode("latin-1", "replace")
                        if t not in out["ext_rels"]:
                            out["ext_rels"].append(t)
                except Exception:
                    pass
        out["ext_rels"] = out["ext_rels"][:10]
        if out["ext_rels"]:
            out["warn"].append("relasi eksternal di dalam dokumen (%d): bisa konten jarak jauh / template injection" % len(out["ext_rels"]))

        # isi anggota yang layak dipindai (dex, class, skrip, makro) ikut jadi bahan string / indikator
        budget = 24 * 1024 * 1024
        chunks = []
        pri = sorted(infos, key=lambda i: (0 if i.filename.lower().endswith(_PRIO_EXT) else 1, i.file_size))
        for i in pri:
            fn = i.filename.lower()
            if i.is_dir() or i.flag_bits & 1 or budget <= 0:
                continue
            if not (fn.endswith(_SCAN_EXT) or "vbaproject.bin" in fn) or i.file_size > 12 * 1024 * 1024:
                continue
            try:
                data = _zread(z, i, min(12 * 1024 * 1024, budget))
            except Exception:
                continue
            budget -= len(data)
            chunks.append(data)
        out["_blob"] = b"\n".join(chunks)
    return out


