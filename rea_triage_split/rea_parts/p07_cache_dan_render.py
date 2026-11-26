# rea_triage bagian 07/47: cache_dan_render (baris asli 2402-3639). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# Cache hasil per SHA-256 (23 Nov 2026). Triase berkas besar bisa makan belasan detik padahal hasilnya selalu sama untuk isi yang sama.
# Aturan keamanan / kebenaran:
#   - berkas SELALU dibuka dulu lewat _open_regular (FIFO / perangkat / folder / symlink tetap ditolak); cache tidak pernah melewati cek itu;
#   - kunci = SHA-256 ISI berkas (nama berkas tidak ikut; nama dipasang ulang saat cache terpakai) + tag (fuzzy / RE Lab);
#   - entri hanya dipakai bila sidik jari KODE (mtime + ukuran rea_triage.py), VERSION, dan daftar REA_KNOWN_HASHES sama dengan saat disimpan,
#     jadi mengedit kode atau daftar hash otomatis membuat cache lama tidak terpakai;
#   - hanya JSON (tidak pernah pickle), dibaca dengan validasi; rusak / kedaluwarsa / tidak cocok = diabaikan, hitung ulang;
#   - entri disimpan HANYA bila hasil dibaca-balik dari JSON menghasilkan laporan yang identik (render 4 mode, kartu, IOC), jadi cache tidak
#     pernah mengubah keluaran; bila tidak identik, tidak disimpan;
#   - gagal menulis / membaca cache tidak pernah menggagalkan triase (best-effort); tulis atomik (berkas sementara + os.replace);
#   - hanya berkas bernama <sha256>-<tag>.json di folder cache yang pernah dibaca / dihapus / dipangkas (REA_CACHE_DIR salah arah tidak berbahaya).
# Pengaturan: env REA_CACHE=0 (matikan), REA_CACHE_DIR=FOLDER (default: rea-reports/.cache di samping berkas ini), CLI --no-cache / --cache-info /
# --cache-clear, API {"action": "triage", "nocache": true} untuk memaksa hitung ulang dan {"action": "cache"} untuk info.
# ---------------------------------------------------------------------------

CACHE_FORMAT = 1
CACHE_MAX_FILES = 500                    # jumlah entri maksimum; yang paling lama tak terpakai dibuang dulu
CACHE_MAX_BYTES = 128 * 1024 * 1024      # total ukuran maksimum folder cache
CACHE_MAX_ENTRY = 8 * 1024 * 1024        # satu entri lebih besar dari ini tidak disimpan
CACHE_TTL_DAYS = 30.0                    # entri lebih tua dari ini tidak dipakai (laporan memuat perbandingan dengan waktu sekarang)
_CACHE_STATE: dict = {"pruned": 0.0, "code": None}
_CACHE_NAME = re.compile(r"[0-9a-f]{64}-(?:t0|t1|re)\.json")
_CACHE_TMP = re.compile(r"[0-9a-f]{64}-(?:t0|t1|re)\.json\.[0-9a-f]{12}\.tmp")


def _cache_dir():
    """Folder cache, atau None bila dimatikan (REA_CACHE=0 / off / false / no)."""
    if os.environ.get("REA_CACHE", "").strip().lower() in ("0", "off", "false", "no", "tidak"):
        return None
    d = os.environ.get("REA_CACHE_DIR", "").strip()
    return Path(d) if d else Path(__file__).resolve().parent / "rea-reports" / ".cache"


def _cache_stamp() -> dict:
    """Sidik jari yang harus sama agar entri boleh dipakai: format cache, VERSION, kode modul ini, dan berkas REA_KNOWN_HASHES."""
    code = _CACHE_STATE["code"]
    if code is None:
        try:
            code = hashlib.sha256(_code_bytes()).hexdigest()[:32]   # hash ISI kode (bukan mtime + ukuran)
        except OSError:
            code = "?"
        _CACHE_STATE["code"] = code
    known = ""
    kp = os.environ.get("REA_KNOWN_HASHES", "")
    if kp:
        try:
            st = os.stat(kp)
            known = "%s:%d:%d" % (kp, st.st_mtime_ns, st.st_size)
        except OSError:
            known = kp + ":-"
    return {"fmt": CACHE_FORMAT, "ver": VERSION, "code": code, "known": known}


def _sha256_of(f, size: int) -> str | None:
    """SHA-256 dari paling banyak `size` byte pertama (sama dengan yang dihitung _hash_file). Posisi baca dikembalikan ke 0."""
    h = hashlib.sha256()
    try:
        f.seek(0)
        left = size
        while left > 0:
            chunk = f.read(min(1024 * 1024, left))
            if not chunk:
                break
            h.update(chunk)
            left -= len(chunk)
        f.seek(0)
    except OSError:
        return None
    return h.hexdigest()


_CACHE_KEY: dict = {"k": None}


def _cache_key() -> bytes | None:
    """Kunci HMAC cache: env REA_CACHE_KEY, atau berkas ~/.rea_cache_key (dibuat 0600). Sengaja DI LUAR folder cache, supaya
    penulis folder cache tidak otomatis bisa memalsukan entri. None = tak ada kunci (cache dimatikan, aman)."""
    if _CACHE_KEY["k"] is not None:
        return _CACHE_KEY["k"] or None
    key = b""
    try:
        e = os.environ.get("REA_CACHE_KEY", "").strip()
        if e:
            key = hashlib.sha256(e.encode("utf-8")).digest()
        else:
            kp = Path.home() / ".rea_cache_key"
            try:   # v104: tolak symlink / non-berkas / milik pengguna lain / terbuka untuk grup-dunia; kunci semacam itu tak dipercaya
                fk, _ksz = _open_regular(kp, follow=False)
                with fk:
                    st_ = os.fstat(fk.fileno())
                    if (os.name == "nt" or (st_.st_uid == os.getuid() and not st_.st_mode & 0o077)) and st_.st_size <= 4096:
                        key = fk.read(64)
            except FileNotFoundError:
                pass
            except OSError:
                key = b""
                raise
            if len(key) < 32:
                key = os.urandom(32)
                try:   # simpan hanya bila tujuan bukan symlink dan ACL/izin bisa dikunci; kalau tidak, kunci hanya hidup di memori (cache lama tak dipakai)
                    if not kp.is_symlink():
                        _write_atomic_nofollow(kp, key, 0o600)
                        if not _secure_key_file(kp):
                            kp.unlink()
                except OSError:
                    pass
    except Exception:
        key = b""
    _CACHE_KEY["k"] = key
    return key or None


def _cache_mac(text: str) -> str:
    import hmac
    k = _cache_key()
    return hmac.new(k, text.encode("utf-8"), hashlib.sha256).hexdigest() if k else ""


def _cache_path(sha: str, tag: str):
    d = _cache_dir()
    if d is None or not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
        return None
    return d / ("%s-%s.json" % (sha, tag))


def _cache_load(sha: str, tag: str):
    """Isi (dict) bila entri ada dan sah; selain itu None. Tidak pernah melempar."""
    p = _cache_path(sha, tag)
    if p is None:
        return None
    try:
        # Buka lewat _open_regular(follow=False): symlink ditolak (O_NOFOLLOW), FIFO / perangkat (mis. /dev/zero) / folder ditolak dari
        # fstat pada handle yang sama (tanpa celah TOCTOU, tidak pernah menggantung). Baca paling banyak CACHE_MAX_ENTRY + 1 byte.
        f_, fsz = _open_regular(p, follow=False)
        with f_:
            if fsz > CACHE_MAX_ENTRY:
                return None
            raw_ = f_.read(CACHE_MAX_ENTRY + 1)
        if len(raw_) > CACHE_MAX_ENTRY:
            return None
        wrap = json.loads(raw_.decode("utf-8"))
        import hmac
        if not isinstance(wrap, dict) or not isinstance(wrap.get("body"), str) or not isinstance(wrap.get("mac"), str):
            return None
        good_mac = _cache_mac(wrap["body"])
        if not good_mac or not hmac.compare_digest(good_mac, wrap["mac"]):
            return None             # entri dipalsukan / dibuat tanpa kunci ini: abaikan, hitung ulang
        obj = json.loads(wrap["body"])
        if (not isinstance(obj, dict) or obj.get("stamp") != _cache_stamp() or obj.get("sha256") != sha or obj.get("tag") != tag
                or not isinstance(obj.get("data"), dict) or time.time() - float(obj.get("ts", 0)) > CACHE_TTL_DAYS * 86400):
            return None
        data = obj["data"]
        if tag != "re" and (data.get("sha256") != sha or not isinstance(data.get("ind"), dict) or "kind" not in data or "score" not in data):
            return None
        try:
            os.utime(p, None)          # tandai baru dipakai (untuk pemangkasan LRU)
        except OSError:
            pass
        return data
    except Exception:
        return None


def _cache_store(sha: str, tag: str, data: dict, verify) -> bool:
    """Simpan `data` bila verify(hasil-baca-balik) benar. Tidak pernah melempar. True bila tersimpan."""
    p = _cache_path(sha, tag)
    if p is None:
        return False
    tmp = None
    try:
        text = json.dumps({"stamp": _cache_stamp(), "sha256": sha, "tag": tag, "ts": time.time(), "data": data},
                          ensure_ascii=False, default=str, separators=(",", ":"))
        if len(text) > CACHE_MAX_ENTRY or not verify(json.loads(text)["data"]):
            return False
        mac = _cache_mac(text)
        if not mac:
            return False            # tanpa kunci tidak menyimpan
        text = json.dumps({"mac": mac, "body": text}, ensure_ascii=False, separators=(",", ":"))
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name("%s.%s.tmp" % (p.name, os.urandom(6).hex()))   # unik per panggilan: aman untuk beberapa thread / proses
        fd_ = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0), 0o600)   # v104
        with os.fdopen(fd_, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, p)
        tmp = None
        _cache_prune()
        return True
    except Exception:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return False


def _cache_prune(force: bool = False) -> None:
    """Buang entri kedaluwarsa, lalu yang paling lama tak terpakai bila melebihi batas jumlah / ukuran. Paling sering sekali per menit."""
    now = time.time()
    if not force and now - _CACHE_STATE["pruned"] < 60:
        return
    _CACHE_STATE["pruned"] = now
    d = _cache_dir()
    if d is None:
        return
    ents = []
    try:
        for e in os.scandir(d):
            if not e.is_file(follow_symlinks=False):
                continue
            st = e.stat(follow_symlinks=False)
            if _CACHE_TMP.fullmatch(e.name):
                if now - st.st_mtime > 3600:
                    os.unlink(e.path)
            elif _CACHE_NAME.fullmatch(e.name):
                ents.append((st.st_mtime, st.st_size, e.path))
        ents.sort()
        n, total = len(ents), sum(x[1] for x in ents)
        for mt, sz, path in ents:
            if now - mt > CACHE_TTL_DAYS * 86400 or n > CACHE_MAX_FILES or total > CACHE_MAX_BYTES:
                os.unlink(path)
                n, total = n - 1, total - sz
            else:
                break
    except OSError:
        pass


def cache_info() -> dict:
    """Ringkasan folder cache: aktif / tidak, lokasi, jumlah entri, total byte, umur entri tertua (hari)."""
    d = _cache_dir()
    info: dict = {"enabled": d is not None, "dir": str(d) if d else "", "files": 0, "bytes": 0, "oldest_days": 0.0,
                  "max_files": CACHE_MAX_FILES, "max_bytes": CACHE_MAX_BYTES, "ttl_days": CACHE_TTL_DAYS}
    if d is None:
        return info
    now, oldest = time.time(), 0.0
    try:
        for e in os.scandir(d):
            if e.is_file(follow_symlinks=False) and _CACHE_NAME.fullmatch(e.name):
                st = e.stat(follow_symlinks=False)
                info["files"] += 1
                info["bytes"] += st.st_size
                oldest = max(oldest, now - st.st_mtime)
    except OSError:
        pass
    info["oldest_days"] = round(oldest / 86400, 1)
    return info


def cache_clear() -> int:
    """Hapus semua entri cache (hanya berkas bernama <sha256>-<tag>.json dan sisa .tmp-nya). Mengembalikan jumlah yang dihapus."""
    d = _cache_dir()
    n = 0
    if d is None:
        return 0
    try:
        for e in os.scandir(d):
            if e.is_file(follow_symlinks=False) and (_CACHE_NAME.fullmatch(e.name) or _CACHE_TMP.fullmatch(e.name)):
                try:
                    os.unlink(e.path)
                    n += 1
                except OSError:
                    pass
    except OSError:
        pass
    return n


def cache_text() -> str:
    i = cache_info()
    if not i["enabled"]:
        return "Cache triase: MATI (REA_CACHE=0)."
    return "Cache triase: aktif | %s | %d entri, %s | tertua %.1f hari | batas %d entri / %s / %.0f hari" % (
        i["dir"], i["files"], _human(i["bytes"]), i["oldest_days"], i["max_files"], _human(i["max_bytes"]), i["ttl_days"])


def _verify_triage(rep: dict, back: dict) -> bool:
    """Laporan dari hasil baca-balik JSON harus identik di semua mode keluaran; kalau tidak, jangan di-cache."""
    try:
        for compact in (False, True):
            for defang in (True, False):
                if render(rep, compact=compact, defang=defang) != render(back, compact=compact, defang=defang):
                    return False
        if render(rep, card=True) != render(back, card=True):
            return False
        return json.dumps(iocs(rep), sort_keys=True, default=str) == json.dumps(iocs(back), sort_keys=True, default=str)
    except Exception:
        return False


def _verify_relab(info: dict, back: dict) -> bool:
    try:
        for compact in (False, True):
            for defang in (True, False):
                a: list[str] = []
                b: list[str] = []
                _render_v98({"relab": info}, a.append, compact, defang)
                _render_v98({"relab": back}, b.append, compact, defang)
                if a != b:
                    return False
        return True
    except Exception:
        return False


def triage(path, follow_links: bool = True, fuzzy: bool = True, use_cache: bool = True) -> dict:
    """Triase penuh. Hasil ber-cache per SHA-256 isi berkas (lihat blok cache di atas); rep["cached"] = True bila diambil dari cache.
    use_cache=False memaksa hitung ulang (dan memperbarui cache)."""
    p = Path(path)
    f, size = _open_regular(p, follow_links)
    with f:
        tag = "t1" if fuzzy else "t0"
        sha, hashes = None, None
        if _cache_dir() is not None:   # v104: satu lintasan membaca (sha256 + sha1 + md5) dipakai untuk kunci cache DAN laporan; sebelumnya dua lintasan penuh saat cache miss
            try:
                f.seek(0)
                hashes = _hash_file(f, size)
                f.seek(0)
                sha = hashes["sha256"]
            except OSError:
                sha, hashes = None, None
        if sha and use_cache:
            hit = _cache_load(sha, tag)
            if hit is not None:
                hit["name"] = p.name
                hit["cached"] = True
                return hit
        rep = _triage_open(p, f, size, fuzzy, hashes)
        if sha:
            _cache_store(rep.get("sha256") or sha, tag, rep, lambda back: _verify_triage(rep, back))
        rep["cached"] = False
        return rep


def _common_dll(n: str) -> bool:
    n = n.lower()
    return n in _COMMON_DLLS or n.startswith(("api-ms-win-", "vcruntime", "msvcp"))


_COMMON_DLLS = frozenset({"kernel32.dll", "user32.dll", "gdi32.dll", "advapi32.dll", "shell32.dll", "shlwapi.dll", "ole32.dll", "oleaut32.dll",
                          "comctl32.dll", "comdlg32.dll", "crypt32.dll", "msvcrt.dll", "ucrtbase.dll", "version.dll", "winmm.dll", "imm32.dll",
                          "uxtheme.dll", "dwmapi.dll", "ws2_32.dll", "bcrypt.dll", "secur32.dll", "setupapi.dll", "rpcrt4.dll"})


def _balance(rep: dict) -> list[str]:
    """Fakta terukur yang lazim pada file sah. Hanya INFORMASI untuk pembaca skor: tidak mengurangi skor dan BUKAN jaminan aman
    (malware juga bisa bertanda tangan atau berinfo versi palsu)."""
    out: list[str] = []
    kn = rep.get("known")
    if kn and kn["tag"] == "good":
        out.append("hash ada di daftar lokal 'good'%s" % ((": " + kn["label"]) if kn["label"] else ""))
    pe = rep.get("pe")
    if not pe or pe.get("broken"):
        return out
    ver = pe.get("ver") or {}
    if all(ver.get(k) for k in ("CompanyName", "FileDescription", "FileVersion", "ProductName")):
        out.append("info versi lengkap")
    ac_ = rep.get("authenticode")
    if pe.get("signed") and pe.get("cert_extra", 0) <= 16 and not (ac_ and ac_.get("match") is False):
        if ac_ and ac_.get("match"):
            out.append("digest Authenticode cocok dengan isi file (rantai sertifikat dan pencabutan belum diverifikasi)")
        else:
            out.append("ada tanda tangan Authenticode (keabsahan belum diverifikasi)")
    note = ((rep.get("relab") or {}).get("entry_stub") or {}).get("note", "")
    if (pe.get("entry_sec") or "").lower() in (".text", "text", ".code", "code") and ("jalur normal" in note or "kompilator biasa" in note):
        out.append("entry normal: bagian %s, %s" % (pe["entry_sec"], note.split(" (")[0]))
    imps = pe.get("imports") or {}
    n_imp = sum(len(v) for v in imps.values())
    if imps and n_imp >= 8 and all(_common_dll(k) for k in imps) and not _cap_strong(rep["ind"], "injeksi / manipulasi proses"):
        out.append("import %d fungsi dari %d DLL sistem umum, tanpa API injeksi" % (n_imp, len(imps)))
    if pe.get("aslr") and pe.get("dep"):
        out.append("ASLR + DEP aktif")
    if not pe.get("overlay") and not any(x["flags"][1:] == "WX" for x in pe["sections"]):
        out.append("tanpa overlay dan tanpa bagian W+X")
    ck = rep.get("checksum")
    if ck and ck[2]:
        out.append("checksum header PE cocok")
    return out


def _triage_open(p: Path, f, size: int, fuzzy: bool = True, hashes: dict | None = None) -> dict:
    rep: dict = {"name": p.name, "size": size, "warn": []}
    rep.update(dict(hashes) if hashes else _hash_file(f, size))   # v104: hash dari pemanggil (triage) dipakai ulang, tidak membaca ulang berkas
    f.seek(0)
    d = f.read(MAX_SCAN)
    rep["truncated"] = size > len(d)
    rep["entropy"] = _entropy(d[:ENT_SAMPLE])

    api_names: set[str] = set()
    pe = elf = zp = None
    try:
        pe = _parse_pe(d, size)
    except Exception as e:   # parser tidak boleh menjatuhkan /rea
        rep["warn"].append("parser PE gagal: %s" % type(e).__name__)
    if pe is None:
        try:
            elf = _parse_elf(d)
        except Exception:
            elf = None
    if pe is None and elf is None:
        try:
            zp = _parse_zip(f, size)
        except Exception as e:
            rep["warn"].append("parser ZIP gagal: %s" % type(e).__name__)
    mo = None
    if pe is None and elf is None and zp is None:   # v97: Mach-O (tipis / universal)
        try:
            mo = _parse_macho(d)
        except Exception as e:
            rep["warn"].append("parser Mach-O gagal: %s" % type(e).__name__)

    head = d[:16]
    if pe and not pe.get("broken"):
        kind = "PE%s %s (%s)" % ("32+" if pe["bits"] == 64 else "32", "DLL" if pe["dll"] else "executable", pe["subsys"])
        kind += ", " + pe["arch"] + (", .NET (managed)" if pe["dotnet"] else ", native")
        for fns in pe["imports"].values():
            api_names.update(fns)
        api_names.update(pe["exports"])
        for fns_ in (pe.get("delay_imports") or {}).values():
            api_names.update(fns_)
    elif pe:
        kind = "MZ/DOS (%s)" % pe["broken"]
    elif elf:
        kind = "ELF%d %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"])
    elif zp:
        kind = zp["kind"]
    elif mo:
        kind = "Mach-O%s (%s, %d-bit, %s)" % (" universal" if len(mo["fat"]) > 1 else "", mo["arch"], mo["bits"], mo["type"])
    elif head[:4] in (b"\xca\xfe\xba\xbe",):
        kind = "Java class atau Mach-O fat binary"
    elif head[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce"):
        kind = "Mach-O"
    elif head[:4] == b"dex\n":
        kind = "Android DEX"
    elif head[:4] == b"\0asm":
        kind = "WebAssembly"
    elif head[:6] == b"7z\xbc\xaf\x27\x1c":
        kind = "arsip 7-Zip (isi tidak diurai di sini)"
    elif head[:4] == b"Rar!":
        kind = "arsip RAR (isi tidak diurai di sini)"
    elif head[:2] == b"\x1f\x8b":
        kind = "gzip"
    elif head[:4] == b"%PDF":
        kind = "PDF"
    elif head[:2] == b"#!":
        kind = "skrip dengan shebang"
    elif head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        kind = "OLE2 (dokumen Office lama / MSI)"
    elif head[:5] == b"{\\rtf":
        kind = "RTF"
    elif head[:4] == b"L\0\0\0" and d[4:20] == b"\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46":
        kind = "Shortcut Windows (.lnk)"
    elif head[:8] == b"\x89PNG\r\n\x1a\n":
        kind = "gambar PNG"
    elif head[:3] == b"\xff\xd8\xff":
        kind = "gambar JPEG"
    elif head[:6] in (b"GIF87a", b"GIF89a"):
        kind = "gambar GIF"
    elif head[:4] == b"DDS ":
        kind = "tekstur DDS"
    elif head[:4] == b"glTF" and d[4:8] == b"\x02\x00\x00\x00":
        kind = "model 3D glTF biner (GLB)"
    elif head[:16] == b"SQLite format 3\x00":
        kind = "database SQLite"
    elif head[:4] == b"RIFF" and d[8:12] == b"WAVE":
        kind = "audio WAV (RIFF)"
    elif head[:4] == b"OggS":
        kind = "audio OGG"
    elif head[:4] in (b"IWAD", b"PWAD"):
        kind = "paket game WAD"
    elif head[:4] == b"PACK" and len(d) >= 12 and 12 <= struct.unpack_from("<I", d, 4)[0] <= size and struct.unpack_from("<I", d, 8)[0] % 64 == 0:
        kind = "paket game Quake PAK"
    else:
        txt = sum(1 for b in d[:4096] if 9 <= b <= 13 or 32 <= b <= 126)
        kind = "teks / skrip" if d[:4096] and txt / len(d[:4096]) > 0.95 else "biner tak dikenal (tanpa magic number umum)"
    rep["kind"] = kind
    rep["pe"], rep["elf"], rep["zip"], rep["macho"] = pe, elf, zp, mo
    if mo:
        api_names.update(mo["imports"])
    if elf:   # v94: ELF dulu tanpa impor sama sekali
        try:
            ei = _elf_imports(d)
        except Exception:
            ei = {"needed": [], "imports": [], "exports": []}
        elf["dyn"] = ei
        api_names.update(ei["imports"])
        try:
            elf["hard"] = _elf_hardening(d, elf)   # v99.3 [B3]; kunci baru, aditif
        except Exception:
            elf["hard"] = None
    rep["com"] = None
    if pe is not None and not pe.get("broken"):
        try:
            cm = _com_artifacts(d, api_names)   # v99.6 [A3]; kunci baru, aditif
            rep["com"] = cm
            for g in cm["groups"]:
                if g["group"] in _COM_NOTE_GROUPS:
                    rep["warn"].append("COM: %s (%s)%s" % (g["group"], ", ".join(g["names"][:2]), (" - " + g["note"]) if g["note"] else ""))
        except Exception as e:
            rep["warn"].append("pemindai COM gagal: %s" % type(e).__name__)
    rep["docs"] = None
    if pe is None and elf is None and zp is None and mo is None:
        try:
            rep["docs"] = _parse_docs(d, kind)
        except Exception as e:
            rep["warn"].append("parser dokumen gagal: %s" % type(e).__name__)

    rep["dotnet"] = None
    if pe and not pe.get("broken") and pe.get("dotnet"):   # v97: metadata .NET
        try:
            rep["dotnet"] = _dotnet_info(d, pe)
        except Exception as e:
            rep["warn"].append("parser metadata .NET gagal: %s" % type(e).__name__)
    cs_ = (pe.get("cert_spans") or []) if (pe and not pe.get("broken")) else []
    if cs_:   # blok PKCS#7 tanda tangan tidak ikut diekstraksi: isinya URL CRL / OCSP penerbit + sisa byte, bukan IOC file ini
        strs, pos_ = [], 0
        for a_, b_ in cs_:
            strs += _strings(d[pos_:a_])
            pos_ = b_
        strs += _strings(d[pos_:])
    else:
        strs = _strings(d)
    if rep["dotnet"]:
        strs += rep["dotnet"]["us"]
    if zp:
        blob = zp.pop("_blob", b"")
        if blob:
            strs += _strings(blob)
    vq_: set = set()
    if pe and not pe.get("broken"):
        for x_ in pe.get("res", []):
            vq_.update(x_.get("vquads", ()))
    rep["ind"] = _indicators(strs, api_names, vq_)
    if rep["dotnet"]:
        for cap_, hit_ in _net_caps(rep["dotnet"]["names"]).items():
            rep["ind"]["caps"][cap_] = list(dict.fromkeys(rep["ind"]["caps"].get(cap_, []) + hit_))[:8]
            if cap_ in rep["ind"]["caps_weak"]:   # nama yang kini terbukti dari metadata .NET tidak lagi lemah
                rep["ind"]["caps_weak"][cap_] = [n_ for n_ in rep["ind"]["caps_weak"][cap_] if n_ not in hit_]

    w = rep["warn"]
    if pe and pe.get("pwarn"):
        w.extend(pe["pwarn"])
    if (pe and pe.get("budget_hit")) or (elf and elf.get("budget_hit")):
        w.append("batas kerja entropi / hash bagian tercapai (header bagian tumpang-tindih atau dibuat-buat); sebagian nilai dikosongkan")
    if rep["entropy"] > 7.2 and not zp:   # arsip zip wajar berentropi tinggi
        w.append("entropi tinggi (%.2f): terkompres, terenkripsi, atau dikemas (packer)" % rep["entropy"])
    if pe and not pe.get("broken"):
        names = [s["name"].lower() for s in pe["sections"]]
        hit = [n for n in names if n in _PACKERS]
        if hit:
            w.append("nama bagian khas packer: " + ", ".join(hit))
        for s in pe["sections"]:
            if s["flags"] == "RWX" or (s["flags"][1:] == "WX"):
                w.append("bagian %s dapat ditulis DAN dieksekusi (W+X)" % s["name"])
            if s["ent"] > 7.2 and s["rsize"] > 4096:
                w.append("bagian %s berentropi %.2f (kemungkinan data terkompres/terenkripsi)" % (s["name"], s["ent"]))
        if not pe["dotnet"] and sum(len(v) for v in pe["imports"].values()) < 8 and size > 50000:
            w.append("import sangat sedikit untuk file sebesar ini (ciri packer atau resolusi API dinamis)")
        if not pe["signed"]:
            w.append("tidak ada tanda tangan digital Authenticode")
        elif pe.get("cert_extra", 0) > 16:
            w.append("tabel sertifikat Authenticode memuat %s byte tak berstruktur setelah blok PKCS#7 (data bisa diselipkan di sana tanpa merusak tanda tangan)" % _human(pe["cert_extra"]))
        if pe["ts"] == 0:
            w.append("timestamp kompilasi 0 (build reproducible atau dihapus)")
        elif pe["ts"] > _dt.datetime.now(_dt.timezone.utc).timestamp() + 86400:
            w.append("timestamp kompilasi di masa depan (dipalsukan atau jam salah)")
        if not pe["aslr"] and pe["bits"] == 32 and not pe["dll"]:
            w.append("ASLR tidak aktif")
        if pe["overlay"] > 65536:
            w.append("ada data tambahan (overlay) %s setelah bagian terakhir" % _human(pe["overlay"]))
    if zp:
        w.extend(zp["warn"])
    if rep["ind"]["pem"]:
        w.append("ada blok PRIVATE KEY tertanam")
    if rep["ind"]["secrets"] or rep["ind"].get("secrets_typed"):
        w.append("kandidat kredensial tertanam (nilai disamarkan di laporan)")
    nt_ = rep["ind"].get("net") or {}
    if nt_.get("pipes_flag"):
        w.append("named pipe bernama mirip alat pasca-eksploitasi / eksekusi jarak jauh: " + "; ".join(nt_["pipes_flag"][:3]))
    if nt_.get("certs"):
        w.append("%d sertifikat PEM tertanam (bisa pinning C2, MITM, atau bundel CA)" % nt_["certs"])
    if nt_.get("dns"):
        w.append("label DNS panjang ter-encode (kandidat DNS tunneling / DGA): " + ", ".join(nt_["dns"][:2]))

    # --- tambahan v92: struktur lanjutan, PE tertanam, penanda pembuat / pengemas, skor
    rep["emb"] = _embedded(d, bool(pe and not pe.get("broken"))) if not zp else {"plain": [], "xor": []}
    rep["overlay"], rep["checksum"], rep["crypto"] = None, None, []
    rep["authenticode"], rep["signer_match"], rep["xor_multi"] = None, None, []
    try:
        rep["known"] = _known_lookup(rep)
    except Exception:
        rep["known"] = None
    try:
        if pe and not pe.get("broken"):
            rep["overlay"] = _overlay_info(d, pe)
            rep["checksum"] = _pe_checksum_check(d, size)
            rep["authenticode"] = _authenticode_check(d, size, pe)
            rep["signer_match"] = _signer_vs_company(pe)
        rep["crypto"] = _crypto_consts(d)
    except Exception as e:
        w.append("analisis tambahan gagal: %s" % type(e).__name__)
    if rep["crypto"]:
        cp_ = rep["ind"]["caps"].setdefault("kripto", [])
        for nm_ in rep["crypto"]:
            if not nm_.startswith("tabel Base64") and nm_ not in cp_:
                cp_.append(nm_)
        if cp_:
            rep["ind"]["caps"]["kripto"] = cp_[:8]
        else:
            rep["ind"]["caps"].pop("kripto", None)
    ov_ = rep["overlay"]
    if ov_ and ov_["type"] != "data":
        w.append("overlay berisi %s di offset 0x%X (%s)" % (ov_["type"], ov_["off"], _human(ov_["size"])))
    ck_ = rep["checksum"]
    if ck_ and not ck_[2]:
        w.append("checksum header PE tidak cocok (tersimpan 0x%X, hitungan 0x%X): file diubah setelah build atau alat tidak memperbarui checksum" % (ck_[0], ck_[1]))
    ac_ = rep.get("authenticode")
    if ac_ and ac_.get("match") is False:
        w.append("tanda tangan Authenticode: digest %s di blob (%s...) beda dari hash isi file (%s...): file diubah setelah ditandatangani (atau penandatangan memakai cara hash khusus)" % (ac_["alg"], ac_["signed"][:16], ac_["computed"][:16]))
    for _n, t_ in ((rep.get("docs") or {}).get("score") or [])[:6]:
        w.append("dokumen: " + t_)
    skip_: list = []
    if pe and not pe.get("broken"):   # resource PNG / JPEG / ZIP utuh dan blok PKCS#7 memang tampak acak: jangan dihitung
        skip_ = [(x["off"], x["off"] + x["size"]) for x in pe.get("res", []) if x.get("fmt") and x.get("fmt_ok")] + list(pe.get("cert_spans") or [])
    rep["regions"] = _entropy_regions(d, skip_) if not zp else []
    rep["regions_masked"] = sum(b_ - a_ for a_, b_ in _merge_spans(skip_, len(d))) if skip_ else 0
    rep["tools"] = _toolchain(d, pe)
    if pe and not pe.get("broken"):
        if pe["entry"] and not pe["entry_sec"]:
            w.append("entry point (RVA 0x%X) tidak berada di bagian mana pun (ciri packer atau file rusak)" % pe["entry"])
        elif pe["entry_sec"] and pe["entry_sec"].lower() not in (".text", "text", ".code", "code", ".itext") and not pe["dotnet"]:
            w.append("entry point berada di bagian '%s', bukan bagian kode lazim" % pe["entry_sec"])
        if pe["tls"]:
            w.append("ada TLS callback: kode bisa jalan sebelum entry point (dipakai anti-debug, juga kompiler sah)")
        for x in pe.get("res", []):
            if x["mz"]:
                w.append("resource %s/%s berisi executable (MZ, %s) di offset 0x%X" % (x["type"], x["name"], _human(x["size"]), x["off"]))
            elif x.get("fmt") and not x.get("fmt_ok"):
                w.append("resource %s/%s berawalan %s tetapi kerangkanya tidak utuh (%s, entropi %.2f): bisa data tambahan / payload yang disamarkan" % (x["type"], x["name"], x["fmt"], _human(x["size"]), x["ent"]))
            elif x.get("fmt"):
                continue   # PNG / JPEG / ZIP utuh: tampak acak karena terkompres, bukan payload terenkripsi
            elif x["ent"] > 7.2 and x["size"] > 16384:
                w.append("resource %s/%s berentropi %.2f (%s): kemungkinan payload terenkripsi / terkompres" % (x["type"], x["name"], x["ent"], _human(x["size"])))
        for s_ in pe["sections"]:
            if s_["rsize"] == 0 and s_["vsize"] > 65536 and "X" in s_["flags"]:
                w.append("bagian %s: ukuran file 0 tetapi memori %s dan dapat dieksekusi (ruang untuk kode hasil unpack)" % (s_["name"], _human(s_["vsize"])))
    if elf:
        if elf["exec_stack"]:
            w.append("ELF: stack dapat dieksekusi (PT_GNU_STACK memuat flag X)")
        if elf["wx"]:
            w.append("ELF: ada " + ", ".join(elf["wx"][:3]) + " yang dapat ditulis DAN dieksekusi")
        if elf["nsec"] == 0 and elf["type"] != "relocatable (.o)":
            w.append("ELF tanpa tabel section (dihapus; umum pada kemasan UPX atau obfuskasi)")
        for x in elf["sections"]:
            if x["ent"] > 7.2 and x["size"] > 4096:
                w.append("ELF: section %s berentropi %.2f" % (x["name"] or "?", x["ent"]))
    if rep["emb"]["plain"]:
        w.append("PE tertanam polos di offset " + ", ".join("0x%X" % o for o in rep["emb"]["plain"][:5]))
    if rep["emb"]["xor"]:
        w.append("penanda DOS stub terenkode XOR (kunci 0x%02X di offset 0x%X): kemungkinan PE tersembunyi" % rep["emb"]["xor"][0])
    for kind_, info_ in rep["ind"]["b64d"]:
        if kind_ in ("PE/MZ", "ELF"):
            w.append(info_)
            break
    if rep["regions"] and not (pe and not pe.get("broken") and any(x["ent"] > 7.2 for x in pe["sections"])):
        a_, b_ = rep["regions"][0]
        w.append("wilayah berentropi tinggi di offset 0x%X-0x%X (%s)" % (a_, b_, _human(b_ - a_)))
    _v97_enrich(d, size, rep, fuzzy, f)
    _v98_enrich(d, rep)
    _capa_enrich(rep, api_names)
    _script_enrich(rep, strs)
    _layers_enrich(rep, d, strs)   # v99.9 [C2]; kunci baru rep["layers"], aditif
    _dso_enrich(rep, d, strs)      # v99.20 [A2]; kunci baru rep["deobf"], aditif
    _dexraw_enrich(rep, d)         # v99.11 [S1]; kunci baru rep["dex_code"], aditif
    _netil_enrich(rep, d)          # v99.12 [S1b]; kunci baru rep["dotnet_il"], aditif
    rep["icon"] = _icon_hash(d, pe)
    pts, level, why = _score(rep)
    rep["score"], rep["level"], rep["why"] = pts, level, why
    try:
        rep["balance"] = _balance(rep)
    except Exception:
        rep["balance"] = []
    return rep


_EXEC_EXTS = (".exe", ".dll", ".sys", ".scr", ".ocx", ".cpl", ".drv", ".efi")


def _bare_name(n: str) -> str:
    """Nama file untuk perbandingan dengan OriginalFilename: huruf kecil, tanpa awalan hash salinan rea-input, tanpa ekstensi executable."""
    n = re.sub(r"^[0-9a-f]{6}_", "", n.strip().lower())
    for e in _EXEC_EXTS:
        if n.endswith(e):
            return n[: -len(e)]
    return n


def _render(rep: dict, compact: bool = False, defang: bool = True, imp_detail: bool = True) -> str:
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("TRIASE LOKAL (dihitung Iris langsung dari bytes file; bukan klaim agen)")
    a("File   : %s | %s (%s B)" % (rep["name"], _human(rep["size"]), format(rep["size"], ",")))
    a("SHA-256: " + rep["sha256"])
    if not compact:
        a("SHA-1  : " + rep["sha1"])
    a("MD5    : " + rep["md5"])
    a("Jenis  : " + rep["kind"])
    kn_ = rep.get("known")
    if kn_:
        a("Daftar hash lokal (%s): %s%s" % (kn_["by"], {"good": "DIKENAL SAH", "bad": "DIKENAL JAHAT", "note": "catatan"}[kn_["tag"]], (" - " + kn_["label"]) if kn_["label"] else ""))
    if "score" in rep:
        a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis; installer / alat sah juga bisa bernilai tinggi." % (rep["score"], rep["level"]))
        for x in rep["why"][: (4 if compact else 20)]:
            a("   * " + x)
    if rep.get("balance"):
        a("Faktor penyeimbang (lazim pada file sah; BUKAN jaminan aman, tidak mengurangi skor): " + "; ".join(rep["balance"]))
    for label, hint in rep.get("tools", []):
        a("Terdeteksi: %s -> langkah lanjut (saran): %s" % (label, hint))
    a("Entropi: %.2f / 8.00%s" % (rep["entropy"], " (sampel %s pertama)" % _human(ENT_SAMPLE) if rep["size"] > ENT_SAMPLE else ""))
    if rep.get("truncated"):
        a("Catatan: file %s; string dan header dipindai dari %s pertama saja." % (_human(rep["size"]), _human(MAX_SCAN)))

    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    if pe and not pe.get("broken"):
        a("PE     : %s %s | entry RVA 0x%X | compile %s | tanda tangan: %s | overlay: %s" % (
            pe["arch"], pe["subsys"], pe["entry"], pe["stamp"], "ada" if pe["signed"] else "tidak ada", _human(pe["overlay"])))
        a("Proteksi: ASLR %s, DEP %s, CFG %s" % tuple("ya" if x else "tidak" for x in (pe["aslr"], pe["dep"], pe["cfg"])))
        a("Entry  : bagian %s%s%s" % (pe["entry_sec"] or "(di luar semua bagian)", " | TLS callback ada" if pe["tls"] else "", " | delay-import ada" if pe["delay"] else ""))
        if pe.get("imphash") and not compact:
            a("Imphash: %s%s" % (pe["imphash"], " (ada %d impor ordinal; bisa beda dari pefile)" % pe["ord_imports"] if pe["ord_imports"] else ""))
        secs = pe["sections"][: (8 if compact else 20)]
        a("Bagian : " + "; ".join("%s %s ent %.1f%s raw %s" % (s["name"] or "?", s["flags"], s["ent"], "*" if s.get("masked") else "", _human(s["rsize"])) for s in secs))
        for s in secs:
            if s.get("masked"):
                a("   * entropi %s dihitung tanpa %s resource PNG / JPEG / ZIP utuh (mentah %.2f)" % (s["name"] or "?", _human(s["masked"]), s["ent_raw"]))
        if not compact:
            a("MD5 bagian: " + "; ".join("%s=%s" % (s["name"] or "?", s["md5"]) for s in secs if s.get("md5")))
        ver = pe.get("ver") or {}
        if ver:
            orig = ver.get("OriginalFilename", "")
            diff_ = bool(orig) and _bare_name(orig) != _bare_name(rep["name"])   # tanpa ekstensi: launcher == launcher.exe
            a("Versi  : " + "; ".join("%s=%s" % (k, v) for k, v in ver.items()) + (" | nama file BERBEDA dari OriginalFilename" if diff_ else ""))
        if pe.get("signers"):
            a("Tanda tangan: CN di blob sertifikat: %s (hanya dibaca, keabsahan TIDAK diverifikasi)" % ", ".join(pe["signers"][:4]))
        if pe.get("rich") and not compact:
            a("Rich   : hash %s, %d entri alat build (varian Iris)" % (pe["rich"]["hash"], pe["rich"]["n"]))
        resl = pe.get("res") or []
        if resl:
            grp: dict = {}
            for x in resl:
                g = grp.setdefault(x["type"], [0, 0, 0.0])
                g[0] += 1
                g[1] += x["size"]
                g[2] = max(g[2], x["ent"])
            top = sorted(grp.items(), key=lambda kv: -kv[1][1])[: (3 if compact else 8)]
            a("Resource: %d entri; " % len(resl) + "; ".join("%s x%d (%s, ent maks %.1f)" % (k, g[0], _human(g[1]), g[2]) for k, g in top))
            fm_: dict = {}
            for x in resl:
                if x.get("fmt") and x.get("fmt_ok"):
                    fm_[x["fmt"]] = fm_.get(x["fmt"], 0) + 1
            if fm_:
                a("   terkompres wajar (kerangka utuh, tidak dianggap payload): " + ", ".join("%s x%d" % kv for kv in fm_.items()))
        imps = pe["imports"]
        if imps:
            tot = sum(len(v) for v in imps.values())
            lim = 8 if compact else 30
            a("Import : %d DLL, %d fungsi: " % (len(imps), tot) + ", ".join("%s(%d)" % (k, len(v)) for k, v in list(imps.items())[:lim]))
            if not compact and imp_detail:
                for k, v in list(imps.items())[:30]:
                    a("   %s: %s" % (k, ", ".join(v[:40]) + (" …" if len(v) > 40 else "")))
        if pe["exports"]:
            a("Export : %d nama: %s" % (len(pe["exports"]), ", ".join(pe["exports"][: (10 if compact else 60)])))
        if pe.get("delay_imports"):
            di = pe["delay_imports"]
            a("Delay-import: %d DLL, %d fungsi: %s" % (len(di), sum(len(v) for v in di.values()), ", ".join("%s(%d)" % (k, len(v)) for k, v in list(di.items())[:8])))
        ov = rep.get("overlay")
        if ov:
            a("Overlay: %s di offset 0x%X, entropi %.2f, jenis %s%s" % (_human(ov["size"]), ov["off"], ov["ent"], ov["type"], (", sha256 " + ov["sha256"]) if ov.get("sha256") else ""))
        ck = rep.get("checksum")
        if ck and not ck[2]:
            a("Checksum header PE: tersimpan 0x%X, hitungan 0x%X (TIDAK cocok)" % (ck[0], ck[1]))
    elif pe:
        a("PE     : " + pe["broken"])
    if elf:
        a("ELF    : %d-bit %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"]))
        a("ELF+   : interpreter %s | %s | %d segmen, %d section | stack %s" % (
            elf["interp"] or "-", {True: "stripped (tanpa .symtab)", False: "ada simbol (.symtab)", None: "tabel section tak terbaca"}[elf["stripped"]],
            elf["nseg"], elf["nsec"], "dapat dieksekusi" if elf["exec_stack"] else "NX"))
        hd = elf.get("hard")
        if hd:
            a("ELF mitigasi: PIE %s | RELRO %s | NX %s | canary %s | FORTIFY %s%s" % (
                hd["pie"], hd["relro"], hd["nx"], "ada" if hd["canary"] else "tidak terdeteksi",
                ("%d fungsi *_chk" % hd["fortify"]) if hd["fortify"] else "tidak terdeteksi",
                (" | " + "; ".join(hd["rpath"])) if hd["rpath"] else ""))
        if elf["sections"]:
            a("Section: " + "; ".join("%s %s ent %.1f %s" % (x["name"] or "?", x["flags"], x["ent"], _human(x["size"])) for x in elf["sections"][: (8 if compact else 20)] if x["name"]))
    dyn = elf.get("dyn") if elf else None
    if dyn:
        if dyn["needed"]:
            a("ELF NEEDED (%d): %s" % (len(dyn["needed"]), ", ".join(dyn["needed"][:20])))
        if dyn["imports"]:
            a("ELF impor (%d): %s" % (len(dyn["imports"]), ", ".join(dyn["imports"][: (12 if compact else 60)])))
        if dyn["exports"] and not compact:
            a("ELF ekspor (%d): %s" % (len(dyn["exports"]), ", ".join(dyn["exports"][:40])))
    dc = rep.get("docs")
    if dc:
        a("Dokumen: " + dc["fmt"])
        for x in dc["info"][: (4 if compact else 14)]:
            a("   - " + x)
    if rep.get("crypto"):
        a("Konstanta algoritma terdeteksi (petunjuk, BUKAN bukti pemakaian): " + ", ".join(rep["crypto"]))
    if zp:
        a("Arsip  : %s, %d entri, %s tak terkompresi (rasio %.1fx)" % (zp["kind"], zp["n"], _human(zp["unc"]), zp.get("ratio", 0)))
        if zp.get("main"):
            a("Main-Class: " + zp["main"])
        if zp.get("dex"):
            a("DEX    : %d berkas classes*.dex" % zp["dex"])
        if zp.get("perms"):
            a("Izin Android (%d): %s" % (len(zp["perms"]), ", ".join(p.replace("android.permission.", "") for p in zp["perms"][: (10 if compact else 40)])))
        _render_apk(zp, a, compact, defang)
        if zp.get("nested"):
            a("Berkas tertanam menarik: " + ", ".join(zp["nested"][: (6 if compact else 25)]))
        risky = _risky_perms(zp.get("perms", []))
        if risky:
            a("Izin Android berisiko (%d): %s" % (len(risky), ", ".join(risky[: (4 if compact else 14)])))
        if zp.get("ext_rels"):
            a("Relasi eksternal dokumen: " + " | ".join(_df(x, defang) for x in zp["ext_rels"][:5]))
        if not compact:
            a("Isi (50 pertama): " + ", ".join(zp["names"]))

    ind = rep["ind"]
    if ind["caps"]:
        a("Indikasi kemampuan (petunjuk dari nama API/string, BUKAN bukti perilaku; installer sah juga memakainya):")
        rows_, folded_, crt_only_ = _fold_caps(rep)
        for cap, keep, _f in rows_:
            a("   - " + _cap_text(ind, cap, keep))
        if folded_:
            a("   (umum pada program MSVC / CRT, bukan indikasi niat: " + "; ".join("%s: %s" % (c_, ", ".join(h_)) for c_, h_ in folded_) + ")")
        if ind.get("caps_weak"):
            a("   (lemah = nama API hanya muncul sebagai teks, mis. dari runtime / tabel nama; tidak ikut skor, kecuali nama API injeksi)")
        if not compact:
            tt = [ATTACK[c] for c in ind["caps"] if c in ATTACK and _cap_strong(ind, c) and c not in crt_only_]
            if tt:
                a("Pemetaan ATT&CK (perkiraan dari petunjuk di atas, BUKAN bukti perilaku): " + "; ".join(tt))
    lim = 5 if compact else 25
    for label, key in (("URL", "urls"), ("Kandidat IP (bisa nomor versi)", "ips"), ("Email", "emails"), ("Kunci registry", "reg"), ("Path Windows", "paths")):
        if ind[key]:
            a("%s (%d): %s" % (label, len(ind[key]), " | ".join(_df(x, defang) if key in ("urls", "ips", "emails") else x for x in ind[key][:lim])))
    if ind["secrets"]:
        a("Kandidat kredensial tertanam (disamarkan): " + ", ".join(ind["secrets"]))
    nt = ind.get("net") or {}
    if any(nt.get(k) for k in ("ua", "http", "hosts", "hdrs", "dns", "proxy", "pipes", "certs")):
        lim_ = 3 if compact else 8
        if nt.get("ua"):
            a("User-Agent tertanam (%d): %s" % (len(nt["ua"]), " | ".join(nt["ua"][:lim_])))
        if nt.get("http"):
            a("Permintaan HTTP mentah: " + " | ".join(nt["http"][:lim_]))
        if nt.get("hosts"):
            a("Header Host: " + ", ".join(_df(x, defang) for x in nt["hosts"][:lim_]))
        if nt.get("hdrs") and not compact:
            a("Header HTTP lain: " + " | ".join(nt["hdrs"]))
        if nt.get("dns"):
            a("Label DNS ter-encode (kandidat): " + ", ".join(_df(x, defang) for x in nt["dns"][:lim_]))
        if nt.get("proxy"):
            a("Konfigurasi proxy: " + " | ".join(_df(x, defang) if "://" in x else x for x in nt["proxy"][:lim_]))
        if nt.get("pipes"):
            a("Named pipe (%d): %s" % (len(nt["pipes"]), ", ".join(nt["pipes"][:lim_])))
        if nt.get("certs"):
            a("Sertifikat PEM tertanam: %d" % nt["certs"])
    if ind.get("secrets_typed"):
        a("Rahasia berformat khusus (disamarkan): " + " | ".join(ind["secrets_typed"][:5 if compact else 12]))
    if ind.get("pdb"):
        a("Jejak PDB (nama proyek / path build pembuat): " + " | ".join(ind["pdb"]))
    if ind["b64"]:
        a("String mirip base64 panjang: %d%s" % (ind["b64"], " (%d berhasil didekode di bawah)" % len(ind["b64d"]) if ind.get("b64d") else " (tidak ada yang berupa executable / teks terbaca)"))
        for k_, v_ in ind.get("b64d", [])[: (3 if compact else 8)]:
            a("   - %s: %s" % (k_, _df(v_, defang) if k_ == "teks" else v_))
    emb = rep.get("emb") or {}
    if emb.get("plain"):
        a("PE tertanam polos di offset: " + ", ".join("0x%X" % o for o in emb["plain"]))
    if emb.get("xor"):
        a("Dugaan PE di-XOR: " + ", ".join("kunci 0x%02X @0x%X" % x for x in emb["xor"]))
    if rep.get("regions") and not compact:
        a("Wilayah berentropi tinggi (>7,2): " + ", ".join("0x%X-0x%X (%s)" % (x, y, _human(y - x)) for x, y in rep["regions"][:6])
          + (" [dihitung tanpa %s resource PNG / JPEG / ZIP utuh dan blok tanda tangan]" % _human(rep["regions_masked"]) if rep.get("regions_masked") else ""))
    _render_v986(rep, a, compact, defang)
    _render_v97(rep, a, compact, defang)
    _render_v98(rep, a, compact, defang)
    _render_capa(rep, a, compact)
    _render_decoded(rep, a, compact, defang)
    _render_layers(rep, a, compact, defang)
    _render_dso(rep, a, compact, defang)
    _render_dexcode(rep.get("dex_code"), a, compact, defang)
    _render_netil(rep.get("dotnet_il"), a, compact, defang)
    if rep.get("icon"):
        a("Ikon   : md5 utama %s (%d ikon; gabungan %s)" % (rep["icon"]["main"], rep["icon"]["n"], rep["icon"]["all"][:12]))
    a("String terbaca: %d" % ind["n_strings"])
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][: (6 if compact else 20)]:
            a("   ! " + x)
    _ah = _assets_hint(rep)
    if _ah:
        a(_ah)
    a("Batas triase: hasil di atas murni pembacaan statis; tanpa dekompilasi, tanpa emulasi sistem (hanya emulasi mikro statis terbatas pada RE Lab), tanpa jaringan, file tidak dijalankan.")
    return "\n".join(L)


def render(rep: dict, compact: bool = False, defang: bool = True, max_chars: int = 0, card: bool = False) -> str:
    """Seperti dulu, plus anggaran panjang: bila melebihi max_chars, buang rincian impor per-DLL dulu, lalu pakai mode ringkas,
    terakhir pangkas bagian tengah. Skor dan PERHATIAN tidak ikut terbuang lebih dulu."""
    if card:
        txt = render_card(rep, defang)
        return txt if not max_chars or len(txt) <= max_chars else txt[:max_chars - 30] + "\n[...dipangkas supaya muat...]"
    txt = _render(rep, compact, defang)
    if not max_chars or len(txt) <= max_chars:
        return txt
    if not compact:
        txt = _render(rep, False, defang, imp_detail=False)
        if len(txt) <= max_chars:
            return txt
    txt = _render(rep, True, defang)
    if len(txt) <= max_chars:
        return txt
    head = int(max_chars * 0.6)
    tail = max(0, max_chars - head - 40)
    return txt[:head] + "\n[...dipangkas supaya muat...]\n" + (txt[-tail:] if tail else "")


def triage_text(path, compact: bool = False, defang: bool = True, max_chars: int = 0, card: bool = False) -> str:
    try:
        return render(triage(path), compact=compact, defang=defang, max_chars=max_chars, card=card)
    except Exception as e:
        return "TRIASE LOKAL gagal (%s: %s). Lanjutkan tanpa data ini." % (type(e).__name__, str(e)[:120])


def _pe_extent(buf: bytes) -> int:
    pe = _parse_pe(buf, len(buf))
    if pe and not pe.get("broken") and pe["sections"]:
        return max(x["rptr"] + x["rsize"] for x in pe["sections"]) or len(buf)
    return len(buf)


def carve(path, outdir, max_items: int = 8, rep: dict | None = None) -> list[dict]:
    """Keluarkan payload tertanam (PE polos, PE di-XOR, PE di base64, PE di resource) ke outdir sebagai <sha>.bin.
    Tidak pernah menjalankan apa pun. Peringatan: antivirus bisa mengarantina hasilnya."""
    p = Path(path)
    rep = rep or triage(path)
    f, fsize = _open_regular(p)
    with f:
        if _hash_file(f, fsize)["sha256"] != rep["sha256"]:
            raise OSError("berkas berubah sejak triase; ulangi /rea")
        f.seek(0)
        d = f.read(MAX_SCAN)
    cands: list[tuple[str, bytes]] = []
    cap = 16 * 1024 * 1024
    for off in (rep.get("emb") or {}).get("plain", []):
        chunk = d[off:off + cap]
        cands.append(("PE polos @0x%X" % off, chunk[:_pe_extent(chunk)]))
    for k, at in (rep.get("emb") or {}).get("xor", []):
        start = max(0, at - 0x4E)
        dec = d[start:start + cap].translate(bytes(i ^ k for i in range(256)))
        if dec[:2] == b"MZ":
            cands.append(("PE XOR 0x%02X @0x%X" % (k, start), dec[:_pe_extent(dec)]))
    for x in ((rep.get("pe") or {}).get("res") or []):
        if x.get("mz"):
            cands.append(("resource %s/%s" % (x["type"], x["name"]), d[x["off"]:x["off"] + min(x["size"], cap)]))
    try:
        b64_iter = itertools.islice(_B64.finditer("\n".join(_strings(d))), 60)
    except Exception:
        b64_iter = ()
    for mm in b64_iter:
        try:   # per kandidat: satu kandidat base64 korup tidak boleh menghentikan pemindaian kandidat berikutnya
            m = mm.group(0)
            raw = base64.b64decode(m + "=" * (-len(m) % 4))
            if raw[:2] == b"MZ" and len(raw) >= 256:
                cands.append(("PE base64", raw[:_pe_extent(raw)]))
        except Exception:
            continue
    out: list[dict] = []
    seen: set[str] = set()
    od = Path(outdir)
    for src, blob in cands:
        if len(out) >= max_items or len(blob) < 256 or len(blob) > 64 * 1024 * 1024:
            continue
        sha = hashlib.sha256(blob).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        od.mkdir(parents=True, exist_ok=True)
        fp = od / (sha[:16] + ".bin")
        try:
            fd_ = os.open(str(fp), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0), 0o600)
            with os.fdopen(fd_, "wb") as f:
                f.write(blob)
        except FileExistsError:
            try:   # v104: berkas lama dibuka lewat _open_regular(follow=False): symlink / FIFO / perangkat ditolak, ukuran dicek sebelum dibaca
                fo_, osz_ = _open_regular(fp, follow=False)
                with fo_:
                    if osz_ != len(blob) or hashlib.sha256(fo_.read(len(blob) + 1)).hexdigest() != sha:   # beda isi: jangan klaim
                        continue
            except OSError:
                continue
        except OSError:
            continue
        item = {"file": str(fp), "sha256": sha, "size": len(blob), "source": src}
        try:
            sub = triage(str(fp))
            item["kind"], item["score"], item["level"] = sub["kind"], sub["score"], sub["level"]
        except Exception:
            pass
        out.append(item)
    return out


def _carved_text(items: list[dict]) -> str:
    L = ["", "PAYLOAD DIKELUARKAN (disalin sebagai .bin, TIDAK dijalankan; antivirus bisa mengarantina berkas ini):"]
    for it in items:
        L.append("   - %s | %s | sha256 %s | %s | skor %s (%s)\n     %s" % (_clean(it["source"]), _human(it["size"]), it["sha256"][:16] + "...",
                 _clean(str(it.get("kind", "?"))), it.get("score", "?"), _clean(str(it.get("level", "?"))), _clean(it["file"])))
    L.append("   Analisis tiap berkas ini dengan /rea cepat sebelum menyimpulkan apa pun.")
    return "\n".join(L)


def triage_bundle(path, max_chars: int = 5500, carve_dir=None) -> tuple[str, str]:
    """(laporan penuh, versi muat-anggaran untuk tugas agen). Satu kali hitung; gagal -> pesan, tidak melempar."""
    try:
        r = triage(path)
        extra = ""
        if carve_dir:
            try:
                items = carve(path, carve_dir, rep=r)
                if items:
                    extra = _carved_text(items)
            except Exception as e:
                extra = "\n(Pengeluaran payload gagal: %s)" % type(e).__name__
        return render(r) + extra, render(r, max_chars=max(1000, max_chars - len(extra))) + extra
    except Exception as e:
        msg = "TRIASE LOKAL gagal (%s: %s). Lanjutkan tanpa data ini." % (type(e).__name__, str(e)[:120])
        return msg, msg


_DIR_PRIO = (".exe", ".dll", ".sys", ".scr", ".so", ".apk", ".jar", ".dex", ".ps1", ".vbs", ".js", ".bat", ".cmd", ".hta", ".lnk",
             ".docm", ".xlsm", ".msi", ".bin", ".dat", ".elf")


def triage_dir(path, max_files: int = 300, per_file_mb: float = 200.0, time_budget: float = 90.0, fuzzy: bool = False) -> dict:
    root = Path(path)
    t0 = time.monotonic()
    found: list[Path] = []
    total_n, total_sz = 0, 0
    for dp, dn, fn in os.walk(root, followlinks=False):
        dn[:] = [x for x in dn if not _is_reparse(os.path.join(dp, x))]   # v94: junction Windows tidak dikenali is_symlink
        for f in fn:
            fp = Path(dp) / f
            try:
                if _is_reparse(fp) or not fp.is_file():
                    continue
                total_n += 1
                total_sz += fp.stat().st_size
                if total_n <= 20000:
                    found.append(fp)
            except OSError:
                continue
        if total_n > 20000:
            break

    def key(fp: Path):
        try:
            sz = fp.stat().st_size
        except OSError:
            sz = 0
        return (0 if fp.suffix.lower() in _DIR_PRIO else 1, -sz)

    found.sort(key=key)
    items: list[dict] = []
    skipped: list[str] = []
    for fp in found:
        if len(items) >= max_files or time.monotonic() - t0 > time_budget:
            skipped.append("batas %s tercapai" % ("jumlah berkas" if len(items) >= max_files else "waktu"))
            break
        rel = str(fp.relative_to(root)).replace("\\", "/")
        try:
            if fp.stat().st_size > per_file_mb * 1024 * 1024:
                skipped.append("%s (>%.0f MB)" % (rel, per_file_mb))
                continue
            if _is_reparse(fp):
                skipped.append("%s (berubah menjadi link)" % rel)
                continue
            r = triage(str(fp), follow_links=False, fuzzy=fuzzy)
        except Exception as e:
            skipped.append("%s (%s)" % (rel, type(e).__name__))
            continue
        items.append({"rel": rel, "size": r["size"], "kind": r["kind"], "score": r["score"], "level": r["level"], "sha256": r["sha256"],
                      "why": r["why"][:3], "urls": r["ind"]["urls"][:5], "ips": r["ind"]["ips"][:5],
                      "imphash": ((r.get("pe") or {}).get("imphash") or "") if not (r.get("pe") or {}).get("broken") else "",
                      "rich": ((r.get("pe") or {}).get("rich") or {}).get("hash", "") if not (r.get("pe") or {}).get("broken") else "",
                      "macho_uuid": (r.get("macho") or {}).get("uuid", ""), "ctph": r.get("ctph", ""),
                      "known": (r.get("known") or {}).get("tag", "")})
    by_hash: dict[str, list[str]] = {}
    for it in items:
        by_hash.setdefault(it["sha256"], []).append(it["rel"])
    return {"root": str(root), "n_total": total_n, "total_size": total_sz, "n_done": len(items), "items": items, "skipped": skipped[:10],
            "dups": [v for v in by_hash.values() if len(v) > 1][:10], "elapsed": time.monotonic() - t0,
            "families": _families(items, fuzzy)}


def render_dir(sm: dict, defang: bool = True, top: int = 15) -> str:
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("TRIASE FOLDER (dihitung Iris dari bytes; tiap berkas dibaca hanya-baca, tidak dijalankan)")
    a("Folder : %s | %d berkas, %s | dipindai %d dalam %.1f detik" % (sm["root"], sm["n_total"], _human(sm["total_size"]), sm["n_done"], sm["elapsed"]))
    kinds = collections.Counter(re.split(r"[,(]", it["kind"])[0].strip() for it in sm["items"])
    a("Jenis  : " + ", ".join("%s x%d" % kv for kv in kinds.most_common(8)))
    ranked = sorted(sm["items"], key=lambda it: (-it["score"], -it["size"]))
    if ranked:
        if ranked[0]["score"] > 0:
            a("Peringkat skor heuristik (petunjuk, BUKAN vonis):")
        for it in ranked[:top]:
            if it["score"] == 0:
                break
            a("   [%s %d] %s | %s | %s | sha256 %s..." % (it["level"], it["score"], it["rel"], re.split(r"[,(]", it["kind"])[0].strip(), _human(it["size"]), it["sha256"][:12]))
            if it["why"]:
                a("        " + "; ".join(it["why"]))
        if ranked[0]["score"] == 0:
            a("   Tidak ada berkas dengan tanda mencurigakan. Terbesar: " + ", ".join("%s (%s)" % (it["rel"], _human(it["size"])) for it in sorted(ranked, key=lambda x: -x["size"])[:5]))
    if sm["dups"]:
        a("Duplikat identik: " + " | ".join(" = ".join(g[:3]) for g in sm["dups"][:5]))
    for fm in sm.get("families", [])[:6]:
        a("Keluarga (%s): %s" % (fm["basis"], " | ".join(fm["members"][:4]) + (" ..." if len(fm["members"]) > 4 else "")))
    urls = _uniq((u for it in sm["items"] for u in it["urls"]), 12)
    ips = _uniq((u for it in sm["items"] for u in it["ips"]), 10)
    if urls:
        a("URL gabungan (%d): %s" % (len(urls), " | ".join(_df(u, defang) for u in urls[:8])))
    if ips:
        a("Kandidat IP gabungan: " + " | ".join(_df(u, defang) for u in ips[:8]))
    if sm["skipped"]:
        a("Dilewati: " + "; ".join(sm["skipped"][:5]))
    a("Langkah berikut: jalankan /rea cepat pada berkas peringkat teratas untuk rinciannya.")
    return "\n".join(L)


def triage_dir_text(path, max_chars: int = 0, defang: bool = True) -> str:
    try:
        txt = render_dir(triage_dir(path), defang=defang)
    except Exception as e:
        return "TRIASE FOLDER gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if max_chars and len(txt) > max_chars:
        txt = txt[: max_chars - 30] + "\n[...dipangkas supaya muat...]"
    return txt


def yara_draft(rep: dict, name: str = "") -> str:
    """Draf aturan YARA dari string unik berkas ini. WAJIB diuji terhadap file sah sebelum dipakai; bisa salah-deteksi."""
    ind = rep["ind"]
    cand = list(ind["urls"][:4]) + list(ind.get("pdb", [])[:2]) + list(ind["emails"][:2]) + list(ind["reg"][:2])
    for cap in ("penambang kripto", "pencurian kredensial / dompet", "string ala ransomware", "penghapus jejak / perusak pemulihan"):
        cand += ind["caps"].get(cap, [])[:3]
    cand = _uniq([c for c in cand if 6 <= len(c) <= 200], 10)
    rid = re.sub(r"[^A-Za-z0-9_]", "_", name or ("rea_" + rep["sha256"][:12]))
    if not rid or rid[0].isdigit():
        rid = "r_" + rid
    if len(cand) < 2:
        return "// Tidak cukup string unik untuk draf YARA yang layak (%d). Jangan membuat aturan dari satu string umum." % len(cand)
    def esc(x):   # v104: backslash, kutip, dan SEMUA karakter kontrol (\x00-\x1f, \x7f) di-escape; baris baru mentah merusak / menyisipkan baris aturan
        out_ = []
        for ch in str(x):
            o = ord(ch)
            if ch == "\\":
                out_.append("\\\\")
            elif ch == '"':
                out_.append('\\"')
            elif ch == "\n":
                out_.append("\\n")
            elif ch == "\t":
                out_.append("\\t")
            elif ch == "\r":
                out_.append("\\r")
            elif o < 0x20 or o == 0x7F:   # YARA hanya mengenal \xNN (tanpa \u); karakter non-ASCII lain aman ditulis apa adanya (UTF-8)
                out_.append("\\x%02X" % o)
            else:
                out_.append(ch)
        return "".join(out_)
    L = ["rule %s {" % rid, "  meta:",
         '    description = "DRAF otomatis Iris rea_triage v93; WAJIB diuji terhadap file sah sebelum dipakai"',
         '    sha256 = "%s"' % rep["sha256"]]
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append('    // imphash varian Iris: %s' % re.sub(r"[^0-9A-Za-z]", "", str(pe["imphash"]))[:64])   # v104: berasal dari berkas; baris baru tidak boleh lolos dari komentar
    L.append("  strings:")
    for i, c in enumerate(cand, 1):
        L.append('    $s%d = "%s" ascii wide nocase' % (i, esc(c)))
    magic = "uint16(0) == 0x5A4D and " if (pe and not pe.get("broken")) else ("uint32(0) == 0x464C457F and " if rep.get("elf") else "")
    need = "all of them" if len(cand) <= 2 else "%d of them" % min(3, len(cand))
    L += ["  condition:", "    %sfilesize < %d and %s" % (magic, max(rep["size"] * 2, 4096), need), "}"]
    return "\n".join(L)


def iocs(rep: dict) -> dict:
    """Indikator siap pakai (tanpa defang) untuk disalin ke blocklist, YARA, atau laporan."""
    ind, pe = rep["ind"], rep.get("pe")
    out = {"sha256": rep["sha256"], "sha1": rep["sha1"], "md5": rep["md5"], "urls": ind["urls"], "ips": ind["ips"],
           "emails": ind["emails"], "registry": ind["reg"], "pdb": ind.get("pdb", [])}
    out["ctph"] = rep.get("ctph", "")
    out["xor_urls"] = _uniq((u for x in rep.get("xor") or [] for u in x["urls"]), 10)
    if rep.get("macho"):
        out["macho_uuid"] = rep["macho"]["uuid"]
    if pe and not pe.get("broken"):
        out["imphash"] = pe.get("imphash", "")
        out["rich_hash"] = (pe.get("rich") or {}).get("hash", "")
        out["section_md5"] = {x["name"] or "?": x["md5"] for x in pe["sections"] if x.get("md5")}
        out["version_info"] = pe.get("ver", {})
    return out


_ASSET_KIND_PREFIX = ("biner tak dikenal", "gzip", "ZIP", "gambar", "tekstur", "model 3D", "database", "audio", "paket game")


def _assets_hint(rep: dict) -> str:
    """Petunjuk (bukan temuan): berkas non-executable yang isinya bisa dijelajahi Asset Explorer (rea_assets.py), bila modul itu ada."""
    if rep.get("pe") or rep.get("elf") or rep.get("macho"):
        return ""
    if not str(rep.get("kind", "")).startswith(_ASSET_KIND_PREFIX):
        return ""
    if _assets_mod() is None:
        return ""
    return "Asset Explorer tersedia untuk jenis ini: `python rea_triage.py --assets FILE` (isi) | `--assets-extract OUTDIR FILE` (ekstrak) | `--assets-carve FILE` (berkas tertanam)"


def triage_json(path, ioc_only: bool = False) -> str:
    try:
        rep = triage(path)
        return json.dumps(iocs(rep) if ioc_only else rep, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": "%s: %s" % (type(e).__name__, str(e)[:120])}, ensure_ascii=False)


