# rea_triage bagian 04/47: string_indikator (baris asli 1050-1561). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# String dan indikator
# ---------------------------------------------------------------------------

_ASCII = re.compile(rb"[\x20-\x7e]{6,}")
_UTF16 = re.compile(rb"(?:[\x20-\x7e]\x00){6,}")
_URL = re.compile(r"(?:https?|ftp|wss?)://[^\s\"'<>\\^`{}|]{4,200}", re.I)
_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_MAIL = re.compile(r"[A-Za-z0-9._%+-]{2,64}@[A-Za-z0-9-]{2,63}\.[A-Za-z.]{2,24}")
_REG = re.compile(r"(?:HKEY_[A-Z_]+|HKLM|HKCU)\\[^\x00\r\n\"]{3,120}|Software\\Microsoft\\Windows\\CurrentVersion\\[A-Za-z\\]{2,60}", re.I)
_WPATH = re.compile(r"\b[A-Za-z]:\\(?:[^\x00-\x1f\"<>|*?\\]{1,60}\\){0,6}[^\x00-\x1f\"<>|*?\\]{1,60}")
_SECRET = re.compile(r"(?i)(?:api[_-]?key|secret|passw(?:or)?d|token|bearer|private[_ ]key|authorization)\s*[:=]\s*['\"]?([A-Za-z0-9_\-+/=.]{8,})")
_PEM = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")
_B64 = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{60,}={0,2}(?![A-Za-z0-9+/=])")

# kemampuan -> nama API / kata kunci (cocokkan dengan nama import atau string). Kehadiran = petunjuk, BUKAN vonis.
CAPS = {
    "injeksi / manipulasi proses": ["VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "QueueUserAPC", "SetThreadContext", "NtWriteVirtualMemory", "RtlCreateUserThread"],
    "anti-debug / anti-analisis": ["IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess", "OutputDebugString", "NtSetInformationThread", "GetTickCount64"],
    "jaringan": ["InternetOpen", "InternetConnect", "HttpSendRequest", "URLDownloadToFile", "WinHttpOpen", "WSAStartup", "WSASocket", "getaddrinfo", "gethostbyname", "InternetReadFile", "HttpClient", "WebClient", "TcpClient"],
    "persistensi": ["RegSetValueEx", "RegCreateKeyEx", "CreateService", "OpenSCManager", "schtasks", "CurrentVersion\\Run"],
    "kripto": ["CryptEncrypt", "CryptDecrypt", "CryptAcquireContext", "BCryptEncrypt", "BCryptDecrypt", "CryptGenKey", "AES", "RijndaelManaged"],
    "penyadap input / layar": ["SetWindowsHookEx", "GetAsyncKeyState", "GetKeyboardState", "GetClipboardData", "BitBlt", "GetDC"],
    "eksekusi proses / shell": ["CreateProcess", "ShellExecute", "WinExec", "system(", "cmd.exe", "powershell", "Process.Start"],
    "hak akses": ["AdjustTokenPrivileges", "OpenProcessToken", "LookupPrivilegeValue", "SeDebugPrivilege", "ImpersonateLoggedOnUser"],
    "muat kode dinamis": ["LoadLibrary", "GetProcAddress", "LdrLoadDll", "Assembly.Load", "Reflection", "VirtualProtect", "VirtualAlloc"],
    "berkas / penghapusan": ["DeleteFile", "MoveFileEx", "SHFileOperation", "RemoveDirectory", "CreateFile"],
}
# kemampuan yang hanya dicocokkan dari string (huruf kecil, cocok sebagian). Tetap PETUNJUK, bukan vonis.
STR_CAPS = {
    "LOLBin / unduh-eksekusi": ["mshta", "regsvr32", "rundll32", "certutil", "bitsadmin", "wscript", "cscript", "msbuild", "installutil", "forfiles"],
    "pencurian kredensial / dompet": ["lsass.exe", "sekurlsa", "mimikatz", "login data", "logins.json", "wallet.dat", "cookies.sqlite", "key4.db", "electrum", "metamask"],
    "penghapus jejak / perusak pemulihan": ["vssadmin", "delete shadows", "wevtutil", "bcdedit", "wbadmin", "cipher /w"],
    "deteksi VM / sandbox": ["vboxguest", "vboxservice", "vmtoolsd", "sbiedll", "sandboxie", "wine_get_unix_file_name", "\\\\.\\pipe\\cuckoo"],
    "PowerShell berbahaya / obfuskasi": ["frombase64string", "-encodedcommand", "invoke-expression", "downloadstring", "downloadfile", "iex(", "-windowstyle hidden", "executionpolicy bypass", "-noprofile"],
    "bypass keamanan": ["amsiscanbuffer", "amsi.dll", "etweventwrite", "disableantispyware", "set-mppreference"],
    "penambang kripto": ["stratum+tcp", "xmrig", "cryptonight", "randomx"],
    "string ala ransomware": ["your files have been encrypted", "decrypt your files", ".onion", "ransom"],
}

# (label, penanda huruf kecil di bytes mentah, saran langkah lanjut). Saran = petunjuk alur kerja, bukan temuan.
_TOOLCHAIN = [
    ("PyInstaller", [b"pyinstaller", b"_meipass", b"pyi-runtime", b"pyiboot", b"pyi-windows-manifest-filename", b"pyi_rth_"], "ekstrak arsip PyInstaller (pyinstxtractor), lalu dekompilasi .pyc"),
    ("Nuitka", [b"nuitka", b"__nuitka_"], "Python dikompilasi ke C: andalkan string, modul, dan analisis native"),
    ("Go", [b"go build id", b"go.buildid", b"runtime.gopanic", b"\xff go buildinf:"], "biner Go: pulihkan nama fungsi dari pclntab (GoReSym / Ghidra)"),
    ("Rust", [b"/rustc/", b"rust_panic", b"core::panicking", b".cargo/registry", b".cargo\\registry"], "biner Rust: nama fungsi ter-mangle, cari path crate di string"),
    ("AutoIt", [b"autoit v3", b"au3!ea06", b"this is a compiled autoit"], "skrip AutoIt terkompilasi: ekstrak dengan alat dekompilasi AutoIt"),
    ("NSIS installer", [b"nullsoft install system", b"nsis error"], "installer NSIS: ekstrak dengan 7-Zip, baca skrip .nsi"),
    ("Inno Setup", [b"inno setup setup data"], "installer Inno Setup: ekstrak dengan innoextract"),
    ("UPX", [b"upx!"], "kemasan UPX: unpack dengan `upx -d` (file tidak perlu dijalankan)"),
    ("Electron / asar", [b"electron.asar", b"app.asar", b"electron/js2c"], "aplikasi Electron: ekstrak app.asar, baca JavaScript"),
    ("Obfuscator .NET", [b"confuserex", b"eazfuscator", b"smartassembly", b".net reactor", b"dotfuscator", b"babelobfuscator", b"agile.net", b"cryptoobfuscator", b"dnguard", b"ilprotector"], "kode .NET diobfuskasi: deobfuskasi dulu (de4dot) sebelum dekompilasi"),
    ("Delphi / Borland", [b"borland", b"embarcadero"], "biner Delphi: pakai IDR / Ghidra dengan signature Delphi"),
    ("Visual Basic 6", [b"msvbvm60"], "VB6: analisis P-Code atau native dengan decompiler VB"),
    ("PyArmor", [b"pyarmor", b"pytransform", b"__pyarmor__"], "Python dilindungi PyArmor: bytecode terenkripsi; cari runtime pytransform / pyarmor_runtime dan analisis di sana"),
    ("cx_Freeze", [b"cx_freeze"], "bundel cx_Freeze: modul Python ada di library.zip di samping exe"),
    ("py2exe", [b"py2exe"], "bundel py2exe: arsip Python di resource / library.zip, lalu dekompilasi .pyc"),
    ("PyOxidizer", [b"pyoxidizer"], "bundel PyOxidizer: modul Python tertanam di biner"),
    ("Themida / WinLicense", [b"themida", b"winlicense", b"oreans technologies"], "pelindung Themida / WinLicense (VM + anti-debug): unpack statis sulit; andalkan analisis dinamis di lingkungan terisolasi"),
    ("VMProtect", [b"vmprotect"], "kode diproteksi VMProtect (virtualisasi): fungsi dilindungi menjadi bytecode VM"),
    ("Enigma Protector", [b"the enigma protector"], "pelindung Enigma: cek bagian .enigma1 / .enigma2"),
    ("WiX Burn bootstrapper", [b".wixburn"], "bootstrapper WiX: ekstrak dengan `dark.exe -x` atau 7-Zip"),
    ("Bun (compile)", [b"$bunfs", b"~bun"], "JavaScript dikompilasi Bun: sumber tertanam di bagian akhir berkas"),
    ("Node pkg / nexe", [b"pkg/prelude/bootstrap.js", b"nexe~~sentinel"], "aplikasi Node terbungkus (pkg / nexe): ekstrak JavaScript dari payload di akhir berkas"),
]

_ANDROID_RISK = {
    "SEND_SMS": "kirim SMS", "READ_SMS": "baca SMS", "RECEIVE_SMS": "tangkap SMS",
    "BIND_ACCESSIBILITY_SERVICE": "layanan aksesibilitas (sering disalahgunakan)", "REQUEST_INSTALL_PACKAGES": "memasang APK lain",
    "SYSTEM_ALERT_WINDOW": "tampil di atas aplikasi lain", "BIND_DEVICE_ADMIN": "admin perangkat",
    "READ_CALL_LOG": "baca log panggilan", "RECORD_AUDIO": "rekam audio", "READ_CONTACTS": "baca kontak",
    "MANAGE_EXTERNAL_STORAGE": "akses semua berkas", "RECEIVE_BOOT_COMPLETED": "jalan otomatis saat boot",
    "READ_PHONE_NUMBERS": "baca nomor telepon", "CALL_PHONE": "melakukan panggilan",
}

_PDB = re.compile(r"[A-Za-z]:\\[^\x00\r\n\"<>|*?]{3,200}\.pdb", re.I)
_PACKERS = ("upx0", "upx1", ".upx", ".themida", ".vmp0", ".vmp1", ".aspack", ".adata", ".petite", ".nsp0", ".mpress1", "mpress", ".enigma1", ".winlice", ".boom", ".vmp2", "pec1", "pec2", ".packed", "upx2", ".yp", ".perplex", ".rmnet", ".kkrunchy", ".vmp3", "pecompact2", ".enigma2", ".mpress2", ".nsp2", ".pebundle", ".svkp", ".neolit", ".shrink1", ".shrink2", ".aspack2")


def _strings(d: bytes) -> list[str]:
    out = [m.decode("ascii", "ignore") for m in _ASCII.findall(d)]
    out += [m.decode("utf-16le", "ignore") for m in _UTF16.findall(d)]
    return out


def _uniq(seq, limit):
    seen, res = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            res.append(x)
            if len(res) >= limit:
                break
    return res


def _mask(s: str) -> str:
    return s[:4] + "…(%d krt)" % len(s) if len(s) > 6 else "…"


# v99.3 [C3]: pemindai rahasia berformat khusus. Hanya pola dengan awalan / bentuk yang khas (bukan tebakan entropi), jadi
# alarm palsu rendah. Nilai TIDAK pernah ditulis utuh ke laporan: selalu disamarkan lewat _mask (URI database: sandi diganti ***).
_SECRET_PATS = (
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{50,255})\b")),
    ("Telegram bot token", re.compile(r"(?<![\w:])\d{8,10}:AA[A-Za-z0-9_\-]{33}(?![\w\-])")),
    ("Discord webhook", re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d{17,20}/[A-Za-z0-9_\-]{60,}")),
    ("Slack webhook", re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Stripe secret key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{24,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
)
_DB_URI = re.compile(r"\b(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|amqps?|mssql|sqlserver)://([^\s:@/\"'<>]{1,64}):([^\s@/\"'<>]{1,128})@([^\s/\"'<>?]{1,100})", re.I)


# v99.3+ [C1]: artefak jaringan statis (hanya teks yang tertanam; tidak ada koneksi apa pun dibuat)
_UA_HDR = re.compile(r"(?i)User-Agent:[ \t]*([^\r\n\x00]{4,200})")
_UA_STR = re.compile(r"\b(?:Mozilla/\d\.\d \([^)\r\n]{4,160}\)[^\r\n\x00]{0,100}|[A-Za-z][A-Za-z0-9_.\-]{2,30}/\d{1,3}(?:\.\d{1,4}){1,3} \((?:compatible|Windows|Linux|Macintosh|X11)[^)\r\n]{0,120}\))")
_HTTP_REQ = re.compile(r"\b(GET|POST|PUT|HEAD|DELETE|OPTIONS|PATCH|CONNECT) ((?:/|https?://)[^\s\"'<>]{0,200}) HTTP/1\.[01]")
_HTTP_HOST = re.compile(r"(?i)\bHost:[ \t]*([A-Za-z0-9.\-]{3,100}(?::\d{2,5})?)")
_HTTP_HDR = re.compile(r"(?im)^(Cookie|Authorization|Proxy-Authorization|X-Forwarded-For|Content-Type|Referer):[ \t]*([^\r\n\x00]{0,60})")
_DNS_ENC = re.compile(r"(?<![a-z0-9\-])((?:[a-z2-7]{32,63}|[0-9a-f]{32,63})\.(?:[a-z0-9\-]{2,40}\.)+[a-z]{2,10})(?![a-z0-9\-])", re.I)
_CERT_PEM = re.compile(r"-----BEGIN (?:TRUSTED |X509 )?CERTIFICATE-----")
_PROXY = re.compile(r"(?i)\b(?:socks[45][ah]?|https?)://(?:[^\s:@/\"'<>]{1,40}:[^\s@/\"'<>]{1,40}@)?[A-Za-z0-9.\-]{3,100}:(?:1080|3128|8080|8888|9050|8118|\d{4,5})\b")
_PROXY_KEY = re.compile(r"(?i)\b(ProxyServer|ProxyEnable|ProxyOverride|AutoConfigURL|http_proxy|https_proxy|all_proxy|socks_proxy|Proxy-Authorization|WINHTTP_OPTION_PROXY)\b")
_PIPE = re.compile(r"\\\\(?:\.|[A-Za-z0-9_\-]{1,30})\\pipe\\([^\s\x00\"'<>|*?\\]{1,80})")
_PIPE_C2 = (
    (re.compile(r"(?i)^msagent_[0-9a-f]{2}$"), "pola default Cobalt Strike (SMB beacon)"),
    (re.compile(r"(?i)^MSSE-\d{2,5}-server$"), "pola default Cobalt Strike"),
    (re.compile(r"(?i)^postex_[0-9a-f]{4}$"), "pola Cobalt Strike (post-ex)"),
    (re.compile(r"(?i)^status_[0-9a-f]{2,4}$"), "pola Cobalt Strike"),
    (re.compile(r"(?i)^(?:win)?(?:mojo|crashpad_)\.\d+\.\d+"), "mirip pipe Chromium (dipakai juga sebagai kamuflase)"),
    (re.compile(r"(?i)^(?:PSEXESVC|paexec|remcom|csexec)"), "alat eksekusi jarak jauh (PsExec dan sejenis)"),
    (re.compile(r"(?i)^(?:svcctl|atsvc|samr|lsarpc|srvsvc|netlogon)$"), "pipe RPC Windows (lazim; relevan bila dipakai langsung)"),
)


def _net_artifacts(blob: str) -> dict:
    """Artefak jaringan statis dari string: User-Agent, permintaan / header HTTP mentah, DNS ter-encode, sertifikat PEM, proxy, named pipe."""
    ua = _uniq([m.strip() for m in _UA_HDR.findall(blob)] + [m.strip() for m in _UA_STR.findall(blob)], 8)
    http = _uniq(("%s %s" % (m, u[:120]) for m, u in _HTTP_REQ.findall(blob)), 8)
    hosts = _uniq((h.rstrip(".") for h in _HTTP_HOST.findall(blob)), 8)
    hdrs = _uniq(("%s: %s" % (k.title(), "***" if k.lower() in ("cookie", "authorization", "proxy-authorization") else v.strip()) for k, v in _HTTP_HDR.findall(blob)), 6)
    dns = []
    if "." in blob:
        for m in _DNS_ENC.finditer(blob[:4 * 1024 * 1024]):
            lab = m.group(1)
            if len(set(lab.split(".")[0].lower())) >= 8:   # label berentropi rendah (aaaa...) bukan data ter-encode
                dns.append(lab[:90])
            if len(dns) >= 8:
                break
    px = []
    for m in _PROXY.finditer(blob):
        v = re.sub(r"//[^/@\s]+:[^/@\s]+@", "//***:***@", m.group(0))[:120]
        if v.lower().startswith("socks") or re.search(r":(?:1080|3128|8080|8888|9050|8118)$", v):
            px.append(v)
    proxy = _uniq(px + [k.group(1) for k in _PROXY_KEY.finditer(blob)], 8)
    pipes, flagged = [], []
    for nm in _PIPE.findall(blob):
        pipes.append(nm)
        for rx, why in _PIPE_C2:
            if rx.match(nm):
                flagged.append("%s (%s)" % (nm, why))
                break
    return {"ua": ua, "http": http, "hosts": hosts, "hdrs": hdrs, "dns": _uniq(dns, 8), "certs": len(_CERT_PEM.findall(blob)),
            "proxy": proxy, "pipes": _uniq(pipes, 10), "pipes_flag": _uniq(flagged, 6)}


def _scan_secrets(blob: str, limit: int = 12) -> list[str]:
    """Daftar 'jenis: nilai-tersamar'. Contoh dokumentasi (EXAMPLE) dan placeholder sandi dibuang."""
    out: list[str] = []
    for name, rx in _SECRET_PATS:
        for m in rx.finditer(blob):
            v = m.group(0)
            if "EXAMPLE" in v.upper():
                continue
            out.append("%s: %s" % (name, _mask(v)))
            if len(out) >= limit * 3:
                break
    for m in _DB_URI.finditer(blob):
        scheme, user, pw, host = m.groups()
        if pw.strip("*xX$<>{}%") == "" or pw.lower() in ("password", "pass", "changeme", "example", "secret"):
            continue   # placeholder
        out.append("URI database: %s://%s:***@%s (sandi %d krt)" % (scheme.lower(), _mask(user) if len(user) > 6 else user, host, len(pw)))
    return _uniq(out, limit)


def _risky_perms(perms: list[str]) -> list[str]:
    out = []
    for pm in perms:
        k = pm.replace("android.permission.", "")
        if k in _ANDROID_RISK:
            out.append("%s (%s)" % (k, _ANDROID_RISK[k]))
    return out


def _decode_b64(blob: str) -> list[list[str]]:
    """Dekode string base64 panjang dan beri tahu isinya (PE tertanam, teks, arsip). Hanya hasil nyata yang dilaporkan."""
    out: list[list[str]] = []
    for mm in itertools.islice(_B64.finditer(blob), 60):
        m = mm.group(0)
        est = len(m) * 3 // 4                      # ukuran hasil dekode (perkiraan); hanya awalnya yang didekode
        seg = m[:8192]
        if len(m) > 8192:
            seg = seg[:len(seg) - len(seg) % 4]
        try:
            raw = base64.b64decode(seg + "=" * (-len(seg) % 4))
        except Exception:
            continue
        if len(raw) < 24:
            continue
        if raw[:2] == b"MZ":
            out.append(["PE/MZ", "executable tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:4] == b"\x7fELF":
            out.append(["ELF", "executable ELF tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:2] == b"PK":
            out.append(["ZIP", "arsip zip tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:2] == b"\x1f\x8b":
            out.append(["GZIP", "data gzip tertanam dalam base64 (%s)" % _human(est)])
        else:
            txt = ""
            if raw[1::2].count(0) > 0.9 * (len(raw) // 2):
                txt = raw.decode("utf-16le", "ignore")
            else:
                try:
                    txt = raw.decode("utf-8")
                except UnicodeDecodeError:
                    txt = ""
            seg = txt[:400]
            if seg and sum(1 for c in seg if c.isprintable() or c in "\r\n\t") / len(seg) > 0.93 and sum(c.isalpha() for c in seg) > 10:
                out.append(["teks", seg[:100].replace("\n", " ").replace("\r", " ")])
        if len(out) >= 8:
            break
    return out


def _embedded(d: bytes, main_is_pe: bool) -> dict:
    """PE tertanam (polos atau di-XOR satu byte) di dalam file. Hanya lokasi, tidak mengekstrak."""
    res: dict = {"plain": [], "xor": []}
    try:
        pos, n = 0, 0
        while n < 300:
            pos = d.find(b"PE\0\0", pos + 1)
            if pos == -1:
                break
            n += 1
            mz = d.rfind(b"MZ", max(0, pos - 1024), pos)
            if mz > 0 and mz + 0x40 <= len(d) and struct.unpack_from("<I", d, mz + 0x3C)[0] == pos - mz:
                res["plain"].append(mz)
        res["plain"] = res["plain"][:8]
        stub = b"This program cannot be run"
        head = d[: 4 * 1024 * 1024]
        for k in range(1, 256):
            needle = bytes(b ^ k for b in stub)
            at = head.find(needle)
            if at != -1:
                res["xor"].append((k, at))
                if len(res["xor"]) >= 3:
                    break
    except (struct.error, ValueError):
        pass
    return res


def _merge_spans(spans, limit: int) -> list[tuple[int, int]]:
    """Gabungkan rentang (awal, akhir) yang tumpang-tindih, dipotong ke [0, limit)."""
    cl = sorted((max(0, a), min(b, limit)) for a, b in (spans or []))
    out: list[list[int]] = []
    for a, b in cl:
        if a >= b:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _mask_block(d: bytes, a: int, b: int, spans: list[tuple[int, int]]) -> bytes:
    """Isi d[a:b] tanpa byte yang masuk rentang 'spans' (sudah terurut dan digabung)."""
    pos, parts = a, []
    for s0, e0 in spans:
        if e0 <= a:
            continue
        if s0 >= b:
            break
        if s0 > pos:
            parts.append(d[pos:s0])
        pos = max(pos, e0)
        if pos >= b:
            break
    if pos < b:
        parts.append(d[pos:b])
    return b"".join(parts)


def _entropy_regions(d: bytes, skip=None) -> list[tuple[int, int]]:
    """Rentang berentropi tinggi (>7,2) dalam blok; membantu menemukan payload terenkripsi / data kemasan.
    skip: rentang (awal, akhir) yang memang tampak acak karena terkompres (resource PNG / JPEG / ZIP utuh, blok PKCS#7 tanda tangan);
    byte di dalamnya tidak ikut dihitung."""
    d = d[: 16 * 1024 * 1024]
    if len(d) < 32768:
        return []
    spans = _merge_spans(skip, len(d))
    bs = max(65536, len(d) // 64)
    regs: list[list[int]] = []
    for off in range(0, len(d), bs):
        blen = min(bs, len(d) - off)
        blk = _mask_block(d, off, off + blen, spans) if spans else d[off:off + blen]
        if len(blk) >= 4096 and _entropy(blk) > 7.2:
            end = off + blen
            if regs and regs[-1][1] == off:
                regs[-1][1] = end
            else:
                regs.append([off, end])
    return [(a, b) for a, b in regs if b - a >= 32768][:10]


def _toolchain(d: bytes, pe: dict | None) -> list[tuple[str, str]]:
    dl = d[: 16 * 1024 * 1024].lower()
    out = []
    for label, marks, hint in _TOOLCHAIN:
        if any(m in dl for m in marks):
            out.append((label, hint))
    if pe and not pe.get("broken") and pe.get("dotnet") and not any(x[0] == "Obfuscator .NET" for x in out):
        out.append((".NET (managed)", "dekompilasi langsung dengan ILSpy / dnSpy (kode terkelola, hasil biasanya mudah dibaca)"))
    return out


def _score(rep: dict) -> tuple[int, str, list[str]]:
    """Skor heuristik dari fakta terukur. BUKAN vonis: tiap alasan menyebut buktinya, dan file sah juga bisa terkena."""
    pts, why = 0, []

    def add(n: int, t: str) -> None:
        nonlocal pts
        pts += n
        why.append("%s (+%d)" % (t, n))

    ind = rep["ind"]
    caps = {c: v for c, v in ((c, _cap_strong(ind, c)) for c in ind["caps"]) if v}   # hanya yang berbukti kuat ikut skor
    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    for cap, n, txt in (("injeksi / manipulasi proses", 3, "API injeksi proses"), ("pencurian kredensial / dompet", 3, "string pencurian kredensial / dompet"),
                        ("penambang kripto", 3, "string penambang kripto"), ("penghapus jejak / perusak pemulihan", 3, "perintah penghapus salinan bayangan / log"),
                        ("bypass keamanan", 2, "string bypass AMSI / antivirus"), ("PowerShell berbahaya / obfuskasi", 2, "pola PowerShell terenkode / unduh"),
                        ("penyadap input / layar", 2, "API penyadap papan ketik / layar")):
        if cap in caps:
            add(n, txt)
    if "injeksi / manipulasi proses" not in caps and "injeksi / manipulasi proses" in ind["caps"]:
        add(2, "nama API injeksi proses hanya sebagai string (kemungkinan resolusi API dinamis)")
    if "string ala ransomware" in caps and "kripto" in caps:
        add(3, "string ala ransomware ditambah API kripto")
    if len(caps.get("anti-debug / anti-analisis", [])) >= 2:
        add(1, "beberapa API anti-debug")
    for cap, txt in (("deteksi VM / sandbox", "string deteksi VM / sandbox"), ("persistensi", "API / string persistensi"), ("LOLBin / unduh-eksekusi", "pemakaian LOLBin")):
        if cap in caps:
            add(1, txt)
    if "jaringan" in caps and "eksekusi proses / shell" in caps:
        add(1, "API jaringan dan eksekusi proses sekaligus")
    if ind["pem"]:
        add(1, "kunci privat tertanam")
    if ind["secrets"] or ind.get("secrets_typed"):
        add(1, "kandidat kredensial tertanam")
    emb = rep.get("emb") or {}
    if emb.get("plain") or emb.get("xor"):
        add(3, "PE tertanam di dalam file")
    if any(x[0] in ("PE", "PE/MZ", "ELF") for x in ind.get("b64d", [])):
        add(3, "executable tersembunyi di dalam base64")
    for label, _h in rep.get("tools", []):
        if label in ("UPX", "Obfuscator .NET"):
            add(2, "ditandai %s" % label)
    if pe and not pe.get("broken"):
        if any(n_.lower() in _PACKERS for n_ in (x["name"] for x in pe["sections"])):
            add(2, "nama bagian khas packer")
        if any(x["flags"][1:] == "WX" for x in pe["sections"]):
            add(2, "bagian W+X")
        if any(x["ent"] > 7.2 and x["rsize"] > 4096 for x in pe["sections"]):
            add(1, "bagian berentropi tinggi")
        if not pe["dotnet"] and sum(len(v) for v in pe["imports"].values()) < 8 and rep["size"] > 50000:
            add(2, "import sangat sedikit untuk ukuran file")
        if pe["entry"] and not pe["entry_sec"]:
            add(2, "entry point di luar semua bagian")
        elif pe["entry_sec"] and pe["entry_sec"].lower() not in (".text", "text", ".code", "code", ".itext") and not pe["dotnet"]:
            add(1, "entry point di bagian '%s'" % pe["entry_sec"])
        if pe["tls"]:
            add(1, "ada TLS callback (jalan sebelum entry point)")
        if any(x["mz"] for x in pe.get("res", [])):
            add(3, "executable (MZ) di dalam resource")
        elif any(x.get("fmt") and not x.get("fmt_ok") for x in pe.get("res", [])):
            add(1, "resource berawalan PNG / JPEG / ZIP tetapi kerangkanya tidak utuh")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not x.get("fmt") for x in pe.get("res", [])):
            add(1, "resource besar berentropi tinggi (bukan PNG / JPEG / ZIP)")
        if pe["ts"] > time.time() + 86400:
            add(1, "timestamp kompilasi di masa depan")
    if zp:
        if len(_risky_perms(zp.get("perms", []))) >= 3:
            add(2, "banyak izin Android berisiko")
        if zp.get("ext_rels"):
            add(2, "relasi eksternal dalam dokumen")
        if "makro VBA" in zp["kind"]:
            add(2, "makro VBA")
        if any("terenkripsi" in w_ for w_ in zp["warn"]):
            add(1, "entri arsip terenkripsi")
        if any("zip-slip" in w_ for w_ in zp["warn"]):
            add(2, "path traversal dalam arsip")
    if elf:
        if elf["exec_stack"]:
            add(1, "stack dapat dieksekusi")
        if elf["wx"]:
            add(1, "segmen / bagian W+X")
        if elf["nsec"] == 0 and elf["type"] != "relocatable (.o)":
            add(1, "tabel section dihapus (umum pada kemasan)")
    dc = rep.get("docs")
    if dc:
        for n_, t_ in dc.get("score", []):
            add(n_, t_)
    ov = rep.get("overlay")
    if ov and ov.get("type") == "PE/MZ":
        add(2, "executable di dalam overlay")
    _score_v97(rep, add)
    _score_v98(rep, add)
    _score_v986(rep, add)
    _score_layers(rep, add)
    _score_dso(rep, add)
    level = "TINGGI" if pts >= 7 else "SEDANG" if pts >= 4 else "RENDAH" if pts >= 1 else "TANPA TANDA"
    return pts, level, why


def _df(x: str, on: bool) -> str:
    """defang: hxxp dan [.] supaya IOC tidak bisa terklik tak sengaja."""
    if not on:
        return x
    return x.replace("http", "hxxp").replace("ftp://", "fxp://").replace("ws://", "wxs://").replace("wss://", "wxss://").replace(".", "[.]").replace("@", "[@]")


# kata kunci CAPS yang MEMANG berupa string / nama kelas / nama hak (bukan nama API Win32): kecocokan dari string sudah menjadi bukti
# utama, jadi tidak dianggap lemah. Nama API Win32 yang hanya muncul sebagai teks (tabel nama runtime, daftar string) dianggap lemah.
_STR_NATIVE_KEYS = frozenset({"schtasks", "CurrentVersion\\Run", "system(", "cmd.exe", "powershell", "Assembly.Load", "Reflection",
                              "Process.Start", "HttpClient", "WebClient", "TcpClient", "RijndaelManaged", "SeDebugPrivilege"})


def _cap_strong(ind: dict, cap: str) -> list[str]:
    """Nama pemicu kemampuan 'cap' yang punya bukti kuat (tabel import / string khas), tanpa yang hanya muncul sebagai teks."""
    weak = set((ind.get("caps_weak") or {}).get(cap, ()))
    return [n for n in ind["caps"].get(cap, []) if n not in weak]


def _cap_text(ind: dict, cap: str, hit: list[str]) -> str:
    weak = set((ind.get("caps_weak") or {}).get(cap, ()))
    st, wk = [h for h in hit if h not in weak], [h for h in hit if h in weak]
    if st and wk:
        return "%s: %s | hanya string (lemah): %s" % (cap, ", ".join(st), ", ".join(wk))
    if wk:
        return "%s [hanya string, lemah]: %s" % (cap, ", ".join(wk))
    return "%s: %s" % (cap, ", ".join(st))


def _indicators(strs: list[str], api_names: set[str], ver_quads=()) -> dict:
    # v94: string sangat panjang dipotong 1500 karakter untuk regex lain (cegah ReDoS dari sampel buatan); base64 memakai blob penuh
    full = "\n".join(strs)[:24 * 1024 * 1024]
    blob = "\n".join(s[:1500] for s in strs)[:16 * 1024 * 1024]
    urls = _uniq((u.rstrip(".,;)") for u in _URL.findall(blob)), 25)
    ips = []
    for ip in _IP.findall(blob):
        o = [int(x) for x in ip.split(".")]
        if any(x > 255 for x in o) or o[0] == 0 or (o[2] == 0 and o[3] == 0):
            continue   # buang yang jelas nomor versi
        if ip in ver_quads:
            continue   # sama persis dengan nomor versi di resource VERSION file ini
        ips.append(ip)
    secrets = _uniq((_mask(m) for m in _SECRET.findall(blob)), 8)
    secrets_typed = _scan_secrets(blob)   # v99.3 [C3]; kunci baru, kunci lama "secrets" tidak berubah
    try:
        net = _net_artifacts(blob)   # v99.5 [C1]
    except Exception:
        net = {}
    caps: dict[str, list[str]] = {}
    caps_weak: dict[str, list[str]] = {}
    low_blob = blob.lower()
    api_low = [a.lower() for a in api_names]
    for cap, keys in CAPS.items():
        strong, weak = [], []
        for k in keys:
            kl = k.lower()
            if any(kl in a for a in api_low):
                strong.append(k)
            elif len(k) > 7 and kl in low_blob:
                (strong if k in _STR_NATIVE_KEYS else weak).append(k)
        if strong or weak:
            lst = (strong + weak)[:6]
            caps[cap] = lst
            w_ = [x for x in lst if x in weak]
            if w_:
                caps_weak[cap] = w_
    for cap, keys in STR_CAPS.items():
        hit = [k for k in keys if k in low_blob]
        if hit:
            caps[cap] = hit[:6]
    names_l = {a.lower() for a in api_names}   # v94: nama impor persis (ELF / CRT): hanya cocok utuh supaya tidak salah-deteksi
    for cap, exact in EXACT_CAPS.items():
        hit = [k for k in sorted(exact) if k in names_l]
        if hit:
            caps[cap] = list(dict.fromkeys(caps.get(cap, []) + hit))[:6]
    return {
        "urls": urls, "ips": _uniq(ips, 15), "emails": _uniq(_MAIL.findall(blob), 10),
        "reg": _uniq(_REG.findall(blob), 12), "paths": _uniq(_WPATH.findall(blob), 12),
        "secrets": secrets, "secrets_typed": secrets_typed, "net": net, "pem": bool(_PEM.search(blob)),
        "b64": sum(1 for _ in _B64.finditer(full)), "b64d": _decode_b64(full), "pdb": _uniq(_PDB.findall(blob), 3),
        "caps": caps, "caps_weak": caps_weak, "n_strings": len(strs),
    }


