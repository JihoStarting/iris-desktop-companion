# rea_triage bagian 05/47: utama (baris asli 1562-2017). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# Utama
# ---------------------------------------------------------------------------


def _clean(s: str) -> str:
    """v94: buang karakter kontrol dan pengecoh arah teks (RLO dll.) dari keluaran; string dari sampel tidak dipercaya.
    v96.1: baris baru ikut dibuang, supaya nama bagian / entri ZIP / versi bisa menyisipkan baris laporan palsu."""
    return _CTRL_RE.sub("?", s)


_CTRL_RE = re.compile("[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028-\u202e\u2066-\u2069\ufeff]")   # termasuk \n \r \t, U+2028/2029


def _is_reparse(p) -> bool:
    try:
        st = os.lstat(p)
    except OSError:
        return True
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


# kemampuan dari nama impor PERSIS (ELF / CRT); nama pendek tidak dicocokkan sebagian supaya tidak salah-deteksi
EXACT_CAPS = {
    "eksekusi proses / shell": {"system", "popen", "execve", "execv", "execvp", "execl", "execlp", "posix_spawn", "fork", "vfork"},
    "injeksi / manipulasi proses": {"process_vm_writev", "process_vm_readv"},
    "anti-debug / anti-analisis": {"ptrace"},
    "muat kode dinamis": {"dlopen", "dlsym", "mprotect"},
    "hak akses": {"setuid", "setgid", "seteuid", "setresuid", "prctl", "capset"},
    "jaringan": {"socket", "connect", "bind", "listen", "accept", "sendto", "recvfrom", "curl_easy_perform"},
}
STR_CAPS.update({
    "Java / Android: muat kode dinamis": ["dexclassloader", "pathclassloader", "runtime;->exec", "inmemorydexclassloader"],
    "Android: SMS / identitas perangkat": ["sendtextmessage", "sendmultiparttextmessage", "getdeviceid", "getsubscriberid", "getline1number"],
    "Android: aksesibilitas / overlay": ["performglobalaction", "type_application_overlay", "accessibilityservice"],
})
ATTACK = {
    "injeksi / manipulasi proses": "T1055 Process Injection",
    "anti-debug / anti-analisis": "T1622 Debugger Evasion",
    "deteksi VM / sandbox": "T1497 Virtualization/Sandbox Evasion",
    "persistensi": "T1547 / T1543 / T1053 (persistensi)",
    "penyadap input / layar": "T1056 Input Capture / T1113 Screen Capture",
    "pencurian kredensial / dompet": "T1555 / T1003 Credential Access",
    "penghapus jejak / perusak pemulihan": "T1490 Inhibit System Recovery / T1070 Indicator Removal",
    "PowerShell berbahaya / obfuskasi": "T1059.001 PowerShell / T1027 Obfuscation",
    "LOLBin / unduh-eksekusi": "T1218 System Binary Proxy Execution",
    "bypass keamanan": "T1562 Impair Defenses",
    "penambang kripto": "T1496 Resource Hijacking",
    "string ala ransomware": "T1486 Data Encrypted for Impact",
    "hak akses": "T1134 Access Token Manipulation",
    "muat kode dinamis": "T1129 Shared Modules / T1620 Reflective Code Loading",
    "eksekusi proses / shell": "T1059 Command and Scripting Interpreter",
    "kripto": "T1027 / T1573 (kripto / enkripsi)",
    "jaringan": "T1071 Application Layer Protocol",
}


# v99.6 [A3]: GUID COM (CLSID / IID) yang dikenal. (guid, nama, kelompok, catatan). Hanya yang pasti; daftar bisa diperluas lewat tuple ini.
_COM_GUIDS = (
    ("4991D34B-80A1-4291-83B6-3328366B9097", "BackgroundCopyManager (CLSID)", "BITS", ""),
    ("5CE34C0D-0DC9-4C1F-897C-DAA1B78CEE7C", "IBackgroundCopyManager (IID)", "BITS", ""),
    ("4590F811-1D3A-11D0-891F-00AA004B2E24", "WbemLocator (CLSID)", "WMI", ""),
    ("CB8555CC-9128-11D1-AD9B-00C04FD8FDFF", "WbemAdministrativeLocator (CLSID)", "WMI", ""),
    ("DC12A687-737F-11CF-884D-00AA004B2E24", "IWbemLocator (IID)", "WMI", ""),
    ("9556DC99-828C-11CF-A37E-00AA003240C7", "IWbemServices (IID)", "WMI", ""),
    ("44ACA674-E8FC-11D0-A07C-00C04FB68820", "IWbemContext (IID)", "WMI", ""),
    ("0F87369F-A4E5-4CFC-BD3E-73E6154572DD", "TaskScheduler (CLSID)", "Task Scheduler", ""),
    ("2FABA4C7-4DA9-4013-9697-20CC3FD40F85", "ITaskService (IID)", "Task Scheduler", ""),
    ("9BA05972-F6A8-11CF-A442-00A0C90A8F39", "ShellWindows (CLSID)", "DCOM Shell", "dipakai untuk eksekusi lewat objek DCOM / lateral movement"),
    ("C08AFD90-F2A1-11D1-8455-00A0C91F3880", "ShellBrowserWindow (CLSID)", "DCOM Shell", "dipakai untuk eksekusi lewat objek DCOM / lateral movement"),
    ("85CB6900-4D95-11CF-960C-0080C7F4EE85", "IShellWindows (IID)", "DCOM Shell", ""),
    ("49B2791A-B1AE-4C90-9B8E-E860BA07F889", "MMC20.Application (CLSID)", "DCOM MMC", "dipakai untuk eksekusi lewat DCOM / lateral movement"),
    ("13709620-C279-11CE-A49E-444553540000", "Shell.Application (CLSID)", "Shell", ""),
    ("72C24DD5-D70A-438B-8A42-98424B88AFB8", "WScript.Shell (CLSID)", "Script host", ""),
    ("0D43FE01-F093-11CF-8940-00A0C9054228", "Scripting.FileSystemObject (CLSID)", "Script host", ""),
    ("00000566-0000-0010-8000-00AA006D2EA4", "ADODB.Stream (CLSID)", "Script host", "umum pada dropper skrip (tulis biner dari teks)"),
    ("0E59F1D5-1FBE-11D0-8FF2-00A0D10038BC", "MSScriptControl.ScriptControl (CLSID)", "Script host", ""),
    ("2087C2F4-2CEF-4953-A8AB-66779B670495", "WinHttpRequest.5.1 (CLSID)", "Klien HTTP", ""),
    ("88D96A0A-F192-11D4-A65F-0040963251E5", "XMLHTTP 6.0 (CLSID)", "Klien HTTP", ""),
    ("0002DF01-0000-0000-C000-000000000046", "InternetExplorer.Application (CLSID)", "Otomasi IE", ""),
    ("3E5FC7F9-9A51-4367-9063-A120244FBEC7", "CMSTPLUA (CLSID)", "Elevasi COM (UAC)", "objek COM elevasi otomatis; lazim di teknik bypass UAC"),
    ("3E000D72-A845-4CD9-BD83-80C07C3B881F", "CMLUAUTIL (CLSID)", "Elevasi COM (UAC)", "objek COM elevasi otomatis; lazim di teknik bypass UAC"),
    ("6EDD6D74-C007-4E75-B76A-E5740995E24C", "ICMLuaUtil (IID)", "Elevasi COM (UAC)", "antarmuka ShellExec; lazim di teknik bypass UAC"),
    ("3AD05575-8857-4850-9277-11B85BDB8E09", "FileOperation (CLSID)", "Elevasi COM (UAC)", "IFileOperation: salin berkas ke lokasi terlindungi (teknik bypass UAC)"),
    ("947AAB5F-0A5C-4C13-B4D6-4BF7836FC9F8", "IFileOperation (IID)", "Elevasi COM (UAC)", ""),
    ("E2B3C97F-6AE1-41AC-817A-F6F92166D7DD", "NetFwPolicy2 (CLSID)", "Firewall Windows", ""),
    ("98325047-C671-4174-8D81-DEFCD3F03186", "INetFwPolicy2 (IID)", "Firewall Windows", ""),
)
_COM_NOTE_GROUPS = {"DCOM Shell", "DCOM MMC", "Elevasi COM (UAC)"}
_COM_API = ("CoCreateInstance", "CoCreateInstanceEx", "CoGetClassObject", "CoInitialize", "CoInitializeEx", "CoInitializeSecurity",
            "OleInitialize", "CLSIDFromProgID", "CLSIDFromString", "CoGetObject", "CoSetProxyBlanket", "StringFromCLSID", "DllGetClassObject")
_GUID_STR = re.compile(rb"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}")
_GUID_CACHE: list = []


def _com_artifacts(d: bytes, api_names) -> dict:
    """v99.6 [A3]: objek COM dari GUID CLSID / IID (bentuk biner 16-byte, atau string {GUID} ASCII / UTF-16), plus API COM yang diimpor."""
    import uuid as _uuid
    if not _GUID_CACHE:
        for g, nm, grp, note in _COM_GUIDS:
            u = _uuid.UUID(g)
            _GUID_CACHE.append((u.bytes_le, ("{%s}" % g).encode(), ("{%s}" % g.lower()).encode(), ("{%s}" % g).encode("utf-16-le"), nm, grp, note))
    t0 = time.monotonic()
    hits: dict[str, dict] = {}
    for bin_, up, lo, u16, nm, grp, note in _GUID_CACHE:
        if time.monotonic() - t0 > 3.0:
            break
        how = "biner" if bin_ in d else "string" if (up in d or lo in d or u16 in d) else ""
        if how:
            h = hits.setdefault(grp, {"names": [], "how": set(), "note": ""})
            h["names"].append(nm)
            h["how"].add(how)
            h["note"] = h["note"] or note
    known = {x[0].lower() for x in _COM_GUIDS}
    unknown: list[str] = []
    for m in _GUID_STR.finditer(d[:8 * 1024 * 1024]):
        g = m.group(0).decode()[1:-1].lower()
        if g not in known and g not in unknown:
            unknown.append(g)
        if len(unknown) >= 6:
            break
    apis = sorted(a for a in api_names if any(a == c or a.startswith(c) for c in _COM_API))[:8]
    groups = [{"group": g, "names": v["names"][:5], "how": "+".join(sorted(v["how"])), "note": v["note"]} for g, v in hits.items()]
    return {"groups": groups, "unknown": unknown, "apis": apis}


def _elf_hardening(d: bytes, elf: dict) -> dict:
    """v99.3 [B3]: mitigasi ELF (PIE, RELRO, NX, stack canary, FORTIFY_SOURCE, RPATH / RUNPATH). Hanya membaca header program + .dynamic.
    Hasil = petunjuk dari struktur berkas; biner statis / stripped bisa tampak 'tidak ada' padahal diaktifkan lewat cara lain."""
    out: dict = {"pie": "?", "relro": "?", "nx": "?", "canary": False, "fortify": 0, "rpath": [], "bind_now": False}
    if len(d) < 64 or d[:4] != b"\x7fELF":
        return out
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    etype = struct.unpack_from(en + "H", d, 16)[0]
    if is64:
        phoff = struct.unpack_from(en + "Q", d, 32)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 54)
    else:
        phoff = struct.unpack_from(en + "I", d, 28)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 42)
    esz = 56 if is64 else 32
    has_relro = has_stack = False
    dyn_off = dyn_sz = 0
    loads: list[tuple[int, int, int]] = []
    for i in range(min(phnum, 64)):
        o = phoff + i * phentsz
        if phentsz < esz or o + esz > len(d):
            break
        if is64:
            pt, pf, poff, pva, _pa, fsz, _msz, _al = struct.unpack_from(en + "IIQQQQQQ", d, o)
        else:
            pt, poff, pva, _pa, fsz, _msz, pf, _al = struct.unpack_from(en + "IIIIIIII", d, o)
        if pt == 1:
            loads.append((pva, poff, fsz))
        elif pt == 2:
            dyn_off, dyn_sz = poff, fsz
        elif pt == 0x6474E552:
            has_relro = True
        elif pt == 0x6474E551:
            has_stack = True
            out["nx"] = "tidak" if pf & 1 else "ya"
    if not has_stack:
        out["nx"] = "tidak pasti (tanpa PT_GNU_STACK)"
    tags: dict[int, int] = {}
    rp: list[tuple[int, int]] = []
    if dyn_off and dyn_off < len(d):
        esz_d = 16 if is64 else 8
        for k in range(min(dyn_sz // esz_d, 512)):
            o = dyn_off + k * esz_d
            if o + esz_d > len(d):
                break
            tag, val = struct.unpack_from(en + ("qQ" if is64 else "iI"), d, o)
            if tag == 0:
                break
            if tag in (15, 29):
                rp.append((tag, val))
            else:
                tags[tag] = val
    flags, flags1 = tags.get(30, 0), tags.get(0x6FFFFFFB, 0)
    out["bind_now"] = bool(24 in tags or flags & 0x8 or flags1 & 0x1)
    out["relro"] = ("full" if out["bind_now"] else "partial") if has_relro else "tidak ada"
    if etype == 2:
        out["pie"] = "tidak"
    elif etype == 3:
        out["pie"] = "ya" if (flags1 & 0x08000000 or elf.get("interp")) else "n/a (pustaka bersama)"
    if rp and 5 in tags:
        def va2off(va: int) -> int:
            for lv, lo, lsz in loads:
                if lv <= va < lv + lsz:
                    return lo + (va - lv)
            return -1
        so = va2off(tags[5])
        for tag, val in rp[:4]:
            if so >= 0 and so + val < len(d):
                e = d.find(b"\0", so + val, so + val + 256)
                txt = d[so + val:(e if e != -1 else so + val + 256)].decode("latin-1", "replace")
                out["rpath"].append(("RPATH " if tag == 15 else "RUNPATH ") + txt)
    imps = (elf.get("dyn") or {}).get("imports") or []
    base = {x.split("@")[0] for x in imps}
    out["canary"] = bool(base & {"__stack_chk_fail", "__stack_chk_guard", "__intel_security_cookie"}) or (not imps and b"__stack_chk_fail" in d)
    out["fortify"] = sum(1 for x in base if x.startswith("__") and x.endswith("_chk") and x != "__stack_chk_fail")
    return out


def _elf_imports(d: bytes) -> dict:
    """Impor dinamis ELF (.dynsym), pustaka NEEDED (.dynamic), dan simbol ekspor. Hanya membaca."""
    out: dict = {"needed": [], "imports": [], "exports": []}
    if len(d) < 64 or d[:4] != b"\x7fELF":
        return out
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    try:
        if is64:
            shoff = struct.unpack_from(en + "Q", d, 40)[0]
            shentsz, shnum = struct.unpack_from(en + "HH", d, 58)
        else:
            shoff = struct.unpack_from(en + "I", d, 32)[0]
            shentsz, shnum = struct.unpack_from(en + "HH", d, 46)
        if not shoff or not shnum or shentsz < (64 if is64 else 40):
            return out
        secs = []
        for i in range(min(shnum, 128)):
            o = shoff + i * shentsz
            if o + (64 if is64 else 40) > len(d):
                break
            if is64:
                _nm, st, _fl, _ad, off, sz, link, _inf, _al, es = struct.unpack_from(en + "IIQQQQIIQQ", d, o)
            else:
                _nm, st, _fl, _ad, off, sz, link, _inf, _al, es = struct.unpack_from(en + "IIIIIIIIII", d, o)
            secs.append((st, off, sz, link, es))

        def tab(idx: int) -> bytes:
            if idx >= len(secs):
                return b""
            return d[secs[idx][1]:secs[idx][1] + min(secs[idx][2], 1 << 22)]

        def nm_at(t: bytes, o: int) -> str:
            e = t.find(b"\0", o)
            return t[o:(e if e != -1 else o + 128)][:128].decode("latin-1", "replace")

        for st, off, sz, link, es in secs:
            if st == 11:   # SHT_DYNSYM
                t = tab(link)
                esz = es or (24 if is64 else 16)
                for k in range(min(sz // esz, 4000)):
                    o = off + k * esz
                    if o + esz > len(d):
                        break
                    if is64:
                        nm, _i, _o, shndx = struct.unpack_from(en + "IBBH", d, o)
                    else:
                        nm = struct.unpack_from(en + "I", d, o)[0]
                        shndx = struct.unpack_from(en + "H", d, o + 14)[0]
                    if nm:
                        (out["imports"] if shndx == 0 else out["exports"]).append(nm_at(t, nm))
            elif st == 6:   # SHT_DYNAMIC
                t = tab(link)
                esz = 16 if is64 else 8
                for k in range(min(sz // esz, 512)):
                    o = off + k * esz
                    if o + esz > len(d):
                        break
                    tag, val = struct.unpack_from(en + ("qQ" if is64 else "iI"), d, o)
                    if tag == 0:
                        break
                    if tag == 1:
                        out["needed"].append(nm_at(t, val))
    except (struct.error, IndexError, ValueError):
        pass
    for k_ in out:
        out[k_] = list(dict.fromkeys(out[k_]))
    return out


_OV_MAGIC = ((b"MZ", "PE/MZ"), (b"PK\x03\x04", "ZIP"), (b"7z\xbc\xaf\x27\x1c", "7z"), (b"Rar!", "RAR"), (b"MSCF", "CAB"), (b"\x1f\x8b", "gzip"))


def _overlay_info(d: bytes, pe: dict):
    """Jenis, entropi, dan hash overlay PE (data setelah bagian terakhir, di luar blob tanda tangan)."""
    ov, start = pe.get("overlay", 0), pe.get("last_raw", 0)
    if ov < 8 or start <= 0 or start >= len(d):
        return None
    seg = d[start:start + min(ov, 4 * 1024 * 1024)]
    typ = "data"
    for sig, name in _OV_MAGIC:
        if seg.startswith(sig):
            typ = name
            break
    else:
        if seg[4:20] == b"\xef\xbe\xad\xdeNullsoftInst":
            typ = "NSIS"
    sha = hashlib.sha256(d[start:start + ov]).hexdigest() if start + ov <= len(d) else ""
    return {"size": ov, "off": start, "ent": _entropy(seg[:1 << 20]), "type": typ, "sha256": sha}


def _pe_checksum_check(d: bytes, size: int):
    """(tersimpan, hitungan, cocok) untuk CheckSum header PE; None kalau tidak berlaku (0, file dipotong, terlalu besar)."""
    if len(d) != size or len(d) < 0x100 or len(d) > 32 * 1024 * 1024:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    co = pe_off + 24 + 64
    if co + 4 > len(d):
        return None
    stored = struct.unpack_from("<I", d, co)[0]
    if stored == 0:
        return None
    buf = bytearray(d)
    buf[co:co + 4] = b"\0\0\0\0"
    if len(buf) % 2:
        buf.append(0)
    a = array.array("H")
    a.frombytes(bytes(buf))
    if sys.byteorder == "big":
        a.byteswap()
    tot = sum(a)
    while tot >> 16:
        tot = (tot & 0xFFFF) + (tot >> 16)
    calc = (tot + size) & 0xFFFFFFFF
    return stored, calc, calc == stored


_CRYPTO_SIGS = (
    ("AES S-box", bytes.fromhex("637c777bf26b6fc53001672bfed7ab76")),
    ("AES S-box inversa", bytes.fromhex("52096ad53036a538bf40a39e81f3d7fb")),
    ("SHA-256 (tabel K)", bytes.fromhex("982f8a4291443771")),
    ("SHA-256 (nilai awal)", bytes.fromhex("67e6096a85ae67bb")),
    ("SHA-512 (tabel K)", bytes.fromhex("22ae28d7982f8a42")),
    ("CRC32 (tabel)", bytes.fromhex("00000000963007772c610eee")),
    ("CRC32 (polinomial 0xEDB88320)", bytes.fromhex("2083b8ed")),
    ("ChaCha20 / Salsa20", b"expand 32-byte k"),
    ("ChaCha20 / Salsa20 (kunci 16 byte)", b"expand 16-byte k"),
    ("Blowfish (P-array)", bytes.fromhex("886a3f24d308a385")),
    ("tabel Base64 standar", b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
)
_MD5_INIT = tuple(bytes.fromhex(x) for x in ("01234567", "89abcdef", "fedcba98", "76543210"))


def _crypto_consts(d: bytes) -> list[str]:
    """Konstanta algoritma kripto yang dikenal (gaya findcrypt). Petunjuk: kehadirannya tidak membuktikan dipakai."""
    h = d[: 16 * 1024 * 1024]
    out = [name for name, sig in _CRYPTO_SIGS if h.find(sig) != -1]
    if all(h.find(c) != -1 for c in _MD5_INIT):
        out.append("SHA-1 (nilai awal)" if h.find(bytes.fromhex("f0e1d2c3")) != -1 else "MD5 (nilai awal)")
    return out


_PDF_RISK = {
    "/JavaScript": (2, "JavaScript"), "/JS": (2, "JavaScript"), "/OpenAction": (1, "aksi otomatis saat dibuka (OpenAction)"),
    "/AA": (1, "aksi tambahan otomatis (AA)"), "/Launch": (3, "perintah Launch (menjalankan program)"), "/EmbeddedFile": (1, "berkas tertanam"),
    "/RichMedia": (1, "RichMedia (Flash)"), "/XFA": (1, "formulir XFA"), "/SubmitForm": (1, "SubmitForm (kirim data keluar)"),
    "/GoToR": (1, "tautan ke berkas eksternal (GoToR)"), "/URI": (0, "tautan URI"),
}


def _parse_docs(d: bytes, kind: str):
    """PDF, OLE2, RTF, LNK, dan skrip teks: indikator struktural. Semua hanya pembacaan byte; tidak ada yang dijalankan."""
    info: list[str] = []
    score: list[tuple[int, str]] = []
    low = d[: 8 * 1024 * 1024].lower()
    k = kind or ""
    if k == "PDF":
        names: collections.Counter = collections.Counter()
        obf = 0
        for m in re.finditer(rb"/[A-Za-z0-9#]{2,40}", d):
            tok = m.group(0)
            if b"#" in tok:
                dec = re.sub(rb"#([0-9A-Fa-f]{2})", lambda mm: bytes([int(mm.group(1), 16)]), tok)
                if dec != tok:
                    obf += 1
                tok = dec
            names[tok.decode("latin-1", "replace")] += 1
        info.append("objek %d, halaman %d, penanda EOF %d" % (d.count(b"endobj"), names.get("/Page", 0), d.count(b"%" + b"%EOF")))
        seen: set[str] = set()
        for key, (n, txt_) in _PDF_RISK.items():
            c = names.get(key, 0)
            if c:
                info.append("%s x%d: %s" % (key, c, txt_))
                if n and txt_ not in seen:
                    seen.add(txt_)
                    score.append((n, "PDF: " + txt_))
        if names.get("/ObjStm", 0) > 5:
            info.append("/ObjStm x%d (objek terkompres; bisa menyembunyikan aksi)" % names["/ObjStm"])
        if names.get("/Encrypt", 0):
            info.append("PDF terenkripsi (/Encrypt): isi tidak bisa dibaca statis")
        if obf:
            info.append("%d nama objek berobfuskasi dengan #xx" % obf)
            score.append((2, "nama objek PDF berobfuskasi (#xx)"))
        idx = d.rfind(b"%" + b"%EOF")
        if idx != -1 and len(d) - (idx + 5) > 1024:
            info.append("data tambahan %s setelah penanda EOF terakhir" % _human(len(d) - idx - 5))
            score.append((1, "data tambahan setelah EOF PDF"))
    elif k.startswith("OLE2"):
        marks = (("_VBA_PROJECT", "makro VBA", 2), ("Macros", "folder Macros", 0), ("WordDocument", "dokumen Word", 0), ("Workbook", "buku kerja Excel", 0),
                 ("PowerPoint Document", "presentasi PowerPoint", 0), ("ObjectPool", "objek OLE tertanam", 1), ("Ole10Native", "paket OLE tertanam (Ole10Native)", 1),
                 ("EncryptedPackage", "dokumen dienkripsi (kata sandi)", 0), ("Equation Native", "Equation Editor (pola exploit lama CVE-2017-11882)", 3))
        for key, txt_, n in marks:
            if d.find(key.encode("utf-16le"), 0, MAX_SCAN) != -1 or d.find(key.encode(), 0, MAX_SCAN) != -1:
                info.append(txt_)
                if n:
                    score.append((n, "OLE2: " + txt_))
        auto = [x.decode() for x in (b"autoopen", b"document_open", b"workbook_open", b"auto_open", b"autoexec", b"document_close", b"autoclose") if x in low]
        sus = [x.decode() for x in (b"createobject", b"wscript.shell", b"shell(", b"powershell", b"urldownloadtofile", b"xmlhttp", b"adodb.stream", b"cmd.exe", b"mshta", b"regsvr32") if x in low]
        if auto:
            info.append("pemicu otomatis makro: " + ", ".join(auto))
            score.append((2, "makro dengan pemicu otomatis"))
        if sus:
            info.append("API / perintah mencurigakan di makro: " + ", ".join(sus[:6]))
            score.append((2, "makro memanggil API / perintah mencurigakan"))
    elif k == "RTF":
        for key, n, txt_ in ((b"\\objdata", 1, "objek OLE tertanam (\\objdata)"), (b"\\objupdate", 2, "\\objupdate (memaksa objek diperbarui saat dibuka)"),
                             (b"\\objautlink", 1, "objek tertaut otomatis"), (b"\\*\\template", 2, "template eksternal"), (b"equation.3", 3, "Equation Editor (pola exploit lama)")):
            if key in low:
                info.append(txt_)
                score.append((n, "RTF: " + txt_))
        if re.search(rb"[0-9a-f]{4096,}", low):
            info.append("blok heksadesimal panjang (payload tertanam)")
            score.append((1, "RTF memuat blok heksadesimal panjang"))
    elif k.startswith("Shortcut"):
        l16 = d[: 1 << 20].decode("utf-16le", "ignore").lower()
        l8 = low[: 1 << 20]
        keys = ("powershell", "cmd.exe", "mshta", "wscript", "cscript", "rundll32", "regsvr32", "-enc", "-windowstyle hidden", "downloadstring", "http://", "https://", "certutil", "bitsadmin")
        hits = [x for x in keys if x in l16 or x.encode() in l8]
        if len(d) >= 0x18 and struct.unpack_from("<I", d, 0x14)[0] & 0x20:
            info.append("shortcut memakai argumen baris perintah")
        if hits:
            info.append("kata pada target / argumen: " + ", ".join(hits[:8]))
            score.append((2, "shortcut memanggil interpreter / pengunduh"))
        if len(d) > 8192:
            info.append("shortcut besar (%s): bisa membawa payload di dalamnya" % _human(len(d)))
            score.append((1, "shortcut berukuran besar"))
    elif k.startswith("teks") or k.startswith("skrip"):
        raw = d[: 2 * 1024 * 1024]
        txt = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
        tl = txt.lower()
        longest = max((len(x) for x in txt.splitlines()), default=0)
        ind = []
        if longest > 10000:
            ind.append("baris sangat panjang (%d karakter)" % longest)
        pats = ((r"\beval\s*\(", 3, "eval()"), (r"fromcharcode", 2, "fromCharCode"), (r"\bunescape\s*\(", 1, "unescape()"), (r"\batob\s*\(", 1, "atob()"),
                (r"frombase64string", 1, "FromBase64String"), (r"-enc(?:odedcommand)?\b", 1, "-EncodedCommand"), (r"invoke-expression|\biex\b", 2, "Invoke-Expression/iex"),
                (r"\bchr\w?\s*\(", 30, "chr() berulang"), (r"\\x[0-9a-f]{2}", 100, "escape \\xNN berulang"), (r"\w`\w", 20, "backtick di tengah kata (obfuskasi PowerShell)"),
                (r"-bxor|-join|\[char\]", 5, "operasi dekode (-bxor / -join / [char])"), (r"wscript\.shell|activexobject|createobject", 1, "objek COM untuk eksekusi"),
                (r"downloadstring|downloadfile|invoke-webrequest|xmlhttp|urldownloadtofile|bitsadmin|certutil", 1, "unduh dari jaringan"))
        for pat, lim, label in pats:
            n = len(re.findall(pat, tl))
            if n >= lim:
                ind.append("%s x%d" % (label, n))
        if ind:
            info = ind
            score.append((2 if len(ind) >= 3 else 1, "skrip dengan indikator obfuskasi / unduh-eksekusi (%d indikator)" % len(ind)))
    if not info and not score:
        return None
    return {"fmt": k, "info": info, "score": score}


