# rea_triage bagian 15/47: relab_x86 (baris asli 4843-5425). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v98 "RE Lab": bantuan reverse engineering statis untuk PE x86 / x64 (hanya-baca, pustaka standar, file tidak dijalankan).
#   - penemuan fungsi (entry + ekspor + target CALL + prolog) dan penamaan sub_XXXXXXXX;
#   - PETA PANGGILAN API per fungsi: CALL [IAT], thunk JMP [IAT], pointer IAT yang dimuat ke register;
#   - xref string: LEA [RIP+rel] (x64), PUSH / MOV imm32 (x86) -> fungsi mana yang memakai string apa;
#   - peringkat fungsi menarik berdasarkan kelompok kemampuan (injeksi, C2, kripto, persistensi, anti-debug, ...);
#   - anti-analisis tingkat instruksi: akses PEB / TEB, RDTSC, CPUID, INT 2D, SIDT / SLDT / STR, syscall langsung (SysWhispers /
#     Hell's Gate), Heaven's Gate, API hashing (ror13 gaya Metasploit block_api, tabel dihitung saat runtime);
#   - stack string (MOV byte / dword ke stack yang menyusun teks);
#   - stub entry point; disassembler OPSIONAL lewat capstone bila terpasang (tanpa capstone: tampilan hex).
# API baru: re_lab_path(path) -> dict, re_text(path), xref_text(path, query), disasm_text(path, at, count).
# ---------------------------------------------------------------------------
RELAB_MAX_CODE = 24 * 1024 * 1024    # total byte kode yang dipindai
RELAB_TIME = 8.0                     # detik; lewat dari ini analisis berhenti sebagian dan diberi catatan
RELAB_TOP = 12                       # fungsi menarik yang ditampilkan

_RE_X86 = {"x86", "x64"}


def _relab_hash_table() -> dict[int, str]:
    """Hash API gaya Metasploit block_api (modul + fungsi) dan ror13 fungsi-saja, dihitung saat runtime."""
    def ror(v, n):
        return ((v >> n) | (v << (32 - n))) & 0xFFFFFFFF

    def mod_h(name):
        h = 0
        for c in name.upper().encode("utf-16le") + b"\0\0":
            h = (ror(h, 13) + c) & 0xFFFFFFFF
        return h

    def fn_h(name):
        h = 0
        for c in name.encode() + b"\0":
            h = (ror(h, 13) + c) & 0xFFFFFFFF
        return h

    apis = {
        "kernel32.dll": "LoadLibraryA LoadLibraryW GetProcAddress VirtualAlloc VirtualAllocEx VirtualProtect VirtualFree WinExec ExitProcess ExitThread "
                        "CreateProcessA CreateProcessW CreateThread CreateRemoteThread WriteProcessMemory ReadProcessMemory OpenProcess "
                        "WaitForSingleObject CreateFileA CreateFileW WriteFile ReadFile CloseHandle GetModuleHandleA CreateNamedPipeA "
                        "ConnectNamedPipe Sleep GetTickCount TerminateProcess CreateToolhelp32Snapshot Process32First Process32Next "
                        "CreatePipe SetThreadContext GetThreadContext ResumeThread SuspendThread LocalAlloc HeapAlloc GlobalAlloc "
                        "WinExec GetComputerNameA GetVersionExA DeleteFileA MoveFileA CopyFileA FindFirstFileA FindNextFileA".split(),
        "ntdll.dll": "NtAllocateVirtualMemory NtProtectVirtualMemory NtWriteVirtualMemory NtCreateThreadEx NtQueueApcThread RtlMoveMemory "
                     "NtMapViewOfSection NtUnmapViewOfSection NtQueryInformationProcess LdrLoadDll LdrGetProcedureAddress RtlCreateUserThread".split(),
        "wininet.dll": "InternetOpenA InternetOpenW InternetConnectA InternetConnectW HttpOpenRequestA HttpSendRequestA InternetReadFile "
                       "InternetSetOptionA InternetOpenUrlA InternetCloseHandle".split(),
        "ws2_32.dll": "WSAStartup WSASocketA WSASocketW connect send recv closesocket socket bind listen accept gethostbyname getaddrinfo".split(),
        "advapi32.dll": "RegSetValueExA RegCreateKeyExA RegOpenKeyExA CreateServiceA OpenSCManagerA StartServiceA CryptAcquireContextA "
                        "OpenProcessToken AdjustTokenPrivileges LookupPrivilegeValueA".split(),
        "user32.dll": "MessageBoxA GetAsyncKeyState SetWindowsHookExA FindWindowA".split(),
        "winhttp.dll": "WinHttpOpen WinHttpConnect WinHttpOpenRequest WinHttpSendRequest WinHttpReceiveResponse WinHttpReadData".split(),
        "urlmon.dll": ["URLDownloadToFileA", "URLDownloadToFileW"],
        "shell32.dll": ["ShellExecuteA", "ShellExecuteW"],
    }
    tab: dict[int, str] = {}
    for dll, names in apis.items():
        mh = mod_h(dll)
        for n in names:
            tab[(mh + fn_h(n)) & 0xFFFFFFFF] = "%s!%s (block_api)" % (dll.rsplit(".", 1)[0], n)
            tab.setdefault(fn_h(n), "%s (ror13)" % n)
    return tab


_RELAB_HASH: dict[int, str] | None = None
_RELAB_HASH_RE = None

# kelompok kemampuan per fungsi: nama -> (himpunan API huruf kecil, minimal API berbeda, bobot, ATT&CK)
_RE_GROUPS = {
    "injeksi proses": ({"virtualallocex", "writeprocessmemory", "createremotethread", "ntwritevirtualmemory", "queueuserapc", "ntqueueapcthread",
                        "setthreadcontext", "getthreadcontext", "ntmapviewofsection", "ntunmapviewofsection", "resumethread", "openprocess",
                        "rtlcreateuserthread", "ntcreatethreadex", "ntallocatevirtualmemory", "virtualprotectex", "suspendthread"}, 3, 4, "T1055"),
    "jaringan / C2": ({"internetopen", "internetopenurl", "internetconnect", "internetreadfile", "httpopenrequest", "httpsendrequest", "winhttpopen",
                       "winhttpconnect", "winhttpsendrequest", "winhttpreaddata", "wsastartup", "socket", "connect", "send", "recv", "gethostbyname",
                       "getaddrinfo", "dnsquery", "urldownloadtofile", "internetsetoption", "winhttpopenrequest"}, 2, 2, "T1071"),
    "eksekusi proses": ({"winexec", "shellexecute", "shellexecuteex", "createprocess", "createprocessasuser", "createprocesswithlogon", "system", "_wsystem"}, 1, 1, "T1059"),
    "kripto / enkripsi": ({"cryptencrypt", "cryptdecrypt", "cryptacquirecontext", "cryptgenkey", "cryptderivekey", "cryptimportkey", "cryptcreatehash",
                           "bcryptencrypt", "bcryptdecrypt", "bcryptgeneratesymmetrickey", "bcryptopenalgorithmprovider", "bcryptimportkey"}, 2, 2, "T1486"),
    "enumerasi berkas": ({"findfirstfile", "findnextfile", "findfirstfileex", "getlogicaldrives", "getdrivetype", "getlogicaldrivestrings"}, 2, 1, "T1083"),
    "persistensi": ({"regsetvalue", "regcreatekey", "regopenkey", "createservice", "openscmanager", "startservice", "changeserviceconfig", "regsetkeyvalue"}, 2, 3, "T1547 / T1543"),
    "anti-debug / anti-VM": ({"isdebuggerpresent", "checkremotedebuggerpresent", "ntqueryinformationprocess", "outputdebugstring", "ntsetinformationthread",
                              "debugactiveprocess", "ntqueryobject", "getsystemfirmwaretable", "zwqueryinformationprocess"}, 2, 3, "T1622 / T1497"),
    "penyadap input / layar": ({"getasynckeystate", "setwindowshook", "getkeyboardstate", "getforegroundwindow", "getwindowtext", "getrawinputdata",
                                "registerrawinputdevices", "bitblt", "printwindow", "getclipboarddata"}, 2, 3, "T1056 / T1113"),
    "resolusi API dinamis": ({"getprocaddress", "loadlibrary", "ldrgetprocedureaddress", "ldrloaddll", "getmodulehandle", "loadlibraryex"}, 2, 1, "T1027.007"),
    "alokasi / unpack memori": ({"virtualalloc", "virtualprotect", "ntallocatevirtualmemory", "ntprotectvirtualmemory", "virtualallocex"}, 2, 2, "T1027.002 / T1620"),
    "token / hak istimewa": ({"openprocesstoken", "adjusttokenprivileges", "lookupprivilegevalue", "duplicatetokenex", "logonuser", "impersonateloggedonuser",
                              "cryptunprotectdata", "lsaenumeratelogonsessions"}, 2, 3, "T1134 / T1555"),
}

_RE_INTR = re.compile(r"(?i)https?://|ftp://|\\\\[a-z0-9_.$-]+\\|\b[a-z]:\\|\.(?:exe|dll|bat|ps1|vbs|js|sys|tmp|lnk|scr|cmd)\b|powershell|cmd(?:\.exe)?\s+/|software\\|currentversion|"
                      r"\\run\b|password|passwd|token|secret|api[_-]?key|wallet|bitcoin|\.onion|user-agent|mozilla/|%appdata%|%temp%|schtasks|reg\s+add|net\s+user|"
                      r"vssadmin|bcdedit|wevtutil|hkey_|/gate|/panel|ransom|decrypt|your files|mutex|"
                      r"\b(?:vmware|vbox|virtualbox|qemu|wireshark|procmon|procexp|x64dbg|ollydbg|fiddler|sandboxie|vmtoolsd)\b")


def _api_match(name: str, S: set) -> bool:
    n = name.split("!")[-1].lower()
    if n.startswith("zw"):
        n = "nt" + n[2:]
    if n in S:
        return True
    for suf in ("exa", "exw", "ex", "a", "w"):
        if n.endswith(suf) and n[:-len(suf)] in S:
            return True
    return False


def _api_tags(apis) -> tuple[list[str], int]:
    tags, score, have = [], 0, {}
    for g, (S, need, wt, _att) in _RE_GROUPS.items():
        n = sum(1 for a in apis if _api_match(a, S))
        have[g] = n
        if n >= need:
            tags.append(g)
            score += wt + min(n - need, 3)
    if have.get("jaringan / C2") and have.get("eksekusi proses"):
        tags.append("unduh & jalankan")
        score += 4
    if have.get("kripto / enkripsi") and have.get("enumerasi berkas"):
        tags.append("pola ransomware (kripto + enumerasi berkas)")
        score += 5
    return tags, score


def _pe_layout(d: bytes, pe: dict) -> dict | None:
    """Peta alamat PE: image base, bagian, IAT (VA slot -> 'dll!fungsi'), ekspor (VA -> nama). Mengembalikan None bila bukan x86 / x64."""
    if not pe or pe.get("broken") or pe.get("arch") not in _RE_X86:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = pe["bits"] == 64
    base = struct.unpack_from("<Q", d, o + 24)[0] if is64 else struct.unpack_from("<I", d, o + 28)[0]
    size_img = struct.unpack_from("<I", d, o + 56)[0]
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    dd = o + (112 if is64 else 96)
    dirs = [struct.unpack_from("<II", d, dd + 8 * i) for i in range(min(nrva, 16)) if dd + 8 * i + 8 <= len(d)]
    secs = pe["sections"]

    def r2o(rva):
        for s in secs:
            rel = rva - s["va"]
            if 0 <= rel < max(s["vsize"], s["rsize"]):
                return (rel + s["rptr"]) if rel < s["rsize"] and rel + s["rptr"] < len(d) else None
        return None

    def cstr(off, lim=96):
        if off is None or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    step = 8 if is64 else 4
    iat: dict[int, str] = {}

    def walk(thunk_rva, iat_rva, dll):
        off = r2o(thunk_rva)
        k = 0
        while off is not None and off + step <= len(d) and k < 2000:
            v = struct.unpack_from("<Q" if is64 else "<I", d, off)[0]
            if v == 0:
                break
            if v & (1 << (63 if is64 else 31)):
                nm = "ord%d" % (v & 0xFFFF)
            else:
                no = r2o(v & 0x7FFFFFFF)
                nm = cstr(no + 2) if no is not None else "?"
            iat[base + iat_rva + k * step] = "%s!%s" % (dll, nm or "?")
            off += step
            k += 1

    try:
        if len(dirs) > 1 and dirs[1][0]:
            off, n = r2o(dirs[1][0]), 0
            while off is not None and off + 20 <= len(d) and n < 100:
                oft, _t, _f, name_rva, ft = struct.unpack_from("<IIIII", d, off)
                if not (oft or name_rva or ft):
                    break
                dll = cstr(r2o(name_rva)).lower()
                dll = dll[:-4] if dll.endswith(".dll") else dll
                walk(oft or ft, ft, dll or "?")
                off += 20
                n += 1
        if len(dirs) > 13 and dirs[13][0]:
            off, n = r2o(dirs[13][0]), 0
            while off is not None and off + 32 <= len(d) and n < 60:
                _at, name_rva, _h, iat_r, int_r = struct.unpack_from("<IIIII", d, off)
                if not (name_rva or int_r):
                    break
                dll = cstr(r2o(name_rva)).lower()
                dll = dll[:-4] if dll.endswith(".dll") else dll
                walk(int_r, iat_r, (dll or "?") + "(delay)")
                off += 32
                n += 1
    except (struct.error, IndexError, OverflowError):
        pass

    exports: dict[int, str] = {}
    try:
        if dirs and dirs[0][0]:
            eo = r2o(dirs[0][0])
            if eo is not None and eo + 40 <= len(d):
                nfun, nnam, a_rva, n_rva, o_rva = struct.unpack_from("<IIIII", d, eo + 20)
                ao, no_, oo = r2o(a_rva), r2o(n_rva), r2o(o_rva)
                names = {}
                for i in range(min(nnam, 3000)):
                    if no_ is None or oo is None or no_ + 4 * i + 4 > len(d) or oo + 2 * i + 2 > len(d):
                        break
                    ordn = struct.unpack_from("<H", d, oo + 2 * i)[0]
                    names[ordn] = cstr(r2o(struct.unpack_from("<I", d, no_ + 4 * i)[0]))
                for i in range(min(nfun, 4000)):
                    if ao is None or ao + 4 * i + 4 > len(d):
                        break
                    fr = struct.unpack_from("<I", d, ao + 4 * i)[0]
                    if fr and not (dirs[0][0] <= fr < dirs[0][0] + dirs[0][1]):   # bukan forwarder
                        exports[base + fr] = names.get(i) or "ord%d" % i
    except (struct.error, IndexError, OverflowError):
        pass

    xsecs = [s for s in secs if "X" in s["flags"] and s["rsize"] and s["rptr"] < len(d)]
    return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "exports": exports, "r2o": r2o,
            "entry_va": base + pe["entry"] if pe["entry"] else 0, "entry_off": r2o(pe["entry"]) if pe["entry"] else None}


def _va_off(L: dict, va: int):
    """VA -> offset berkas (None bila tidak ada di berkas)."""
    if va < L["base"]:
        return None
    return L["r2o"](va - L["base"])


def _rd_str(d: bytes, off: int) -> tuple[str, str] | None:
    """Baca string ASCII / UTF-16LE terawat di offset (minimal 4 karakter)."""
    if off is None or off < 0 or off + 8 > len(d):
        return None
    j = off
    lim = min(len(d), off + 200)
    while j < lim and (0x20 <= d[j] < 0x7F or d[j] in (9, 10, 13)):
        j += 1
    if j - off >= 4 and (j >= len(d) or d[j] == 0):
        return "a", d[off:j].decode("ascii", "replace")
    j = off
    chars = []
    while j + 1 < lim and d[j + 1] == 0 and (0x20 <= d[j] < 0x7F):
        chars.append(chr(d[j]))
        j += 2
    if len(chars) >= 4:
        return "w", "".join(chars)
    return None


def _str_tag(s: str) -> str:
    if re.search(r"(?i)https?://|ftp://|\.onion|/gate|/panel", s):
        return "URL"
    if re.search(r"(?i)hkey_|software\\|currentversion|\\run\b", s):
        return "registry"
    if re.search(r"(?i)powershell|cmd(\.exe)?\s+/|schtasks|reg\s+add|net\s+user|vssadmin|bcdedit|wevtutil", s):
        return "perintah"
    if re.search(r"(?i)\b(vmware|vbox|virtualbox|qemu|wireshark|procmon|procexp|x64dbg|ollydbg|fiddler|sandboxie|vmtoolsd)\b", s):
        return "alat analisis / VM"
    if re.search(r"(?i)password|passwd|token|secret|api[_-]?key|wallet|bitcoin", s):
        return "kredensial"
    if re.search(r"(?i)ransom|decrypt|your files", s):
        return "ransomware"
    if re.search(r"(?i)\\\\[a-z0-9_.$-]+\\|\b[a-z]:\\|\.(exe|dll|bat|ps1|vbs|js|sys|tmp|lnk|scr|cmd)\b|%appdata%|%temp%", s):
        return "path / berkas"
    return "menarik"


def _stack_strings(code: bytes, secva: int) -> list[tuple[int, str]]:
    """Gabungkan MOV byte / dword imm ke stack yang berurutan menjadi teks (teknik penyembunyi string)."""
    pats = [(re.compile(rb"\xC6\x45(.)([\x20-\x7e])", re.S), "b", 4), (re.compile(rb"\xC6\x44\x24(.)([\x20-\x7e])", re.S), "b", 5),
            (re.compile(rb"\xC6\x85(.{4})([\x20-\x7e])", re.S), "B", 7), (re.compile(rb"\xC7\x45(.)([\x20-\x7e]{4})", re.S), "b", 7),
            (re.compile(rb"\xC7\x44\x24(.)([\x20-\x7e]{4})", re.S), "b", 8)]
    out: list[tuple[int, str]] = []
    for rx, dk, ilen in pats:
        grp: list = []   # [pos_awal, pos_akhir, disp_berikut, teks]

        def flush():
            if grp and len(grp[3]) >= 5 and sum(c.isalnum() for c in grp[3]) >= max(4, int(len(grp[3]) * 0.6)):
                out.append((secva + grp[0], grp[3]))
            grp.clear()
        for m in rx.finditer(code):
            disp = struct.unpack("b" if dk == "b" else "<i", m.group(1))[0]
            ch = m.group(2).decode("ascii")
            if grp and m.start() - grp[1] <= 10 and disp == grp[2]:
                grp[1], grp[2], grp[3] = m.end(), disp + len(ch), grp[3] + ch
            else:
                flush()
                grp.extend([m.start(), m.end(), disp + len(ch), ch])
        flush()
    mv = re.compile(rb"\x48[\xB8-\xBF]([\x20-\x7e]{8})")
    cur: list = []
    for m in mv.finditer(code):
        ch = m.group(1).decode("ascii")
        if cur and m.start() - cur[1] <= 14:
            cur[1], cur[2] = m.end(), cur[2] + ch
        else:
            if cur and len(cur[2]) >= 12 and sum(c.isalnum() for c in cur[2]) >= int(len(cur[2]) * 0.6):
                out.append((secva + cur[0], cur[2]))
            cur = [m.start(), m.end(), ch]
    if cur and len(cur[2]) >= 12 and sum(c.isalnum() for c in cur[2]) >= int(len(cur[2]) * 0.6):
        out.append((secva + cur[0], cur[2]))
    return out


def _entry_stub(d: bytes, L: dict) -> dict:
    off = L["entry_off"]
    if off is None:
        return {"hex": "", "note": "entry point tidak ada di berkas (dipetakan ke luar data mentah)"}
    b = d[off:off + 24]
    note = ""
    if b[:2] == b"\x60\xBE":
        note = "PUSHAD + MOV ESI: pola stub pengepak klasik (UPX / sejenisnya)"
    elif b[:5] == b"\xE8\x00\x00\x00\x00":
        note = "CALL $+5 (get-PC): pola shellcode / loader / pengepak"
    elif b[:4] == b"\x48\x83\xEC\x28" and b[4:5] == b"\xE8":
        note = "awal CRT MSVC x64 (jalur normal)"
    elif b[:3] == b"\x55\x8B\xEC" or b[:5] == b"\x8B\xFF\x55\x8B\xEC":
        note = "bingkai standar x86 (kompilator biasa)"
    elif b[:6] == b"\xf3\x0f\x1e\xfa\x31\xed" or b[:2] == b"\x31\xed":
        note = "awal _start glibc / musl x86-64 (jalur normal)"
    elif b[:1] == b"\xE9":
        note = "langsung JMP ke rutin lain (CRT / protektor / entry tersembunyi)"
    elif b[:2] == b"\x31\xC0" or b[:2] == b"\x33\xC0":
        note = "diawali XOR reg,reg (bisa shellcode / kode buatan tangan)"
    return {"hex": " ".join("%02X" % x for x in b[:16]), "note": note}


def _re_lab(d: bytes, pe: dict | None, t0: float | None = None, L: dict | None = None, arch_label: str | None = None) -> tuple[dict | None, dict | None]:
    t0 = time.monotonic() if t0 is None else t0
    if L is None:
        L = _pe_layout(d, pe)
    if L is None:
        return None, None
    global _RELAB_HASH, _RELAB_HASH_RE
    base, is64, iat = L["base"], L["is64"], L["iat"]
    notes: list[str] = []
    execs, budget = [], RELAB_MAX_CODE
    for s in L["xsecs"]:
        n = min(s["rsize"], s["vsize"] or s["rsize"], budget, len(d) - s["rptr"])
        if n <= 0:
            continue
        budget -= n
        execs.append((base + s["va"], s["rptr"], bytes(d[s["rptr"]:s["rptr"] + n]), s["name"]))
    if not execs:
        return None, None
    if budget <= 0:
        notes.append("kode melebihi batas pindai %s; sebagian tidak dianalisis" % _human(RELAB_MAX_CODE))
    ranges = [(va, va + len(c)) for va, _o, c, _n in execs]

    def in_code(va):
        return any(a <= va < b for a, b in ranges)

    thunks: dict[int, str] = {}
    sites: list[tuple[int, str, str]] = []          # (va, api, jenis)
    edges: list[tuple[int, int]] = []               # (va panggilan, va target)
    strrefs: list[tuple[int, int]] = []             # (va kode, va string)
    anti: dict[str, list[int]] = {}
    sstr: list[tuple[int, str]] = []

    def hit(key, va):
        anti.setdefault(key, []).append(va)

    def reg(pat):
        return re.compile(pat, re.S)
    rx_jmpi, rx_calli = reg(rb"\xFF\x25(.{4})"), reg(rb"\xFF\x15(.{4})")
    rx_e8 = reg(rb"\xE8(.{4})")
    rx_ldp = reg(rb"[\x48\x4C]\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D](.{4})") if is64 else reg(rb"(?:\xA1|\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D])(.{4})")
    rx_lea = reg(rb"[\x48\x4C]\x8D[\x05\x0D\x15\x1D\x25\x2D\x35\x3D](.{4})") if is64 else None
    rx_push = None if is64 else reg(rb"[\x68\xB8-\xBF](.{4})")
    anti_pats = {
        "PEB / TEB dibaca langsung (BeingDebugged, NtGlobalFlag, daftar modul)": reg(
            rb"\x64\xA1\x30\x00\x00\x00|\x64\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D]\x30\x00\x00\x00|\x65[\x48\x4C]\x8B[\x04\x0C\x14\x1C\x24\x2C\x34\x3C]\x25\x60\x00\x00\x00"),
        "RDTSC / RDTSCP (pengukuran waktu)": reg(rb"\x0F\x31|\x0F\x01\xF9"),
        "CPUID (deteksi hypervisor / VM bila bit 31 ECX diperiksa)": reg(rb"\x0F\xA2"),
        "INT 2D (trik anti-debug)": reg(rb"\xCD\x2D[\x90\x40\xC3\xCC]"),
        "SIDT ke stack (deteksi VM ala Red Pill)": reg(rb"\x0F\x01\x4D.|\x0F\x01\x4C\x24."),
        "syscall langsung (stub ala SysWhispers / Hell's Gate, menghindari hook EDR)": reg(rb"\x4C\x8B\xD1\xB8.{4}.{0,14}?\x0F\x05"),
        "Heaven's Gate (pindah mode 64-bit dari proses WoW64)": reg(rb"\x6A\x33\xE8\x00\x00\x00\x00\x83\x04\x24\x05\xCB|\xEA.{4}\x33\x00"),
        "ROR 13 (kandidat API hashing)": reg(rb"\xC1[\xC8-\xCF]\x0D"),
    }
    stop = False
    for secva, _o, code, _nm in execs:
        if stop:
            break
        for m in rx_jmpi.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 6 + v) if is64 else v
            if tgt in iat:
                thunks[secva + m.start()] = iat[tgt]
                k_ = m.start()
                if k_ >= 4 and code[k_ - 4:k_] == b"\xf3\x0f\x1e\xfa":          # endbr64 + jmp [GOT] (.plt.sec / IBT)
                    thunks[secva + k_ - 4] = iat[tgt]
                elif k_ >= 1 and code[k_ - 1] == 0xF2:                           # bnd jmp [GOT]
                    thunks[secva + k_ - 1] = iat[tgt]
                    if k_ >= 5 and code[k_ - 5:k_ - 1] == b"\xf3\x0f\x1e\xfa":
                        thunks[secva + k_ - 5] = iat[tgt]
        for m in rx_calli.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 6 + v) if is64 else v
            if tgt in iat:
                sites.append((secva + m.start(), iat[tgt], "call"))
        for m in rx_ldp.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 7 + v) if is64 else v
            if tgt in iat:
                sites.append((secva + m.start(), iat[tgt], "ptr"))
        if rx_lea:
            for m in rx_lea.finditer(code):
                strrefs.append((secva + m.start(), secva + m.start() + 7 + struct.unpack("<i", m.group(1))[0]))
        else:
            for m in rx_push.finditer(code):
                v = struct.unpack("<I", m.group(1))[0]
                if base <= v < base + L["size_img"]:
                    strrefs.append((secva + m.start(), v))
        for key, rx in anti_pats.items():
            for m in rx.finditer(code):
                hit(key, secva + m.start())
                if len(anti[key]) >= 500:
                    break
        for m in rx_e8.finditer(code):
            rel = struct.unpack("<i", m.group(1))[0]
            va = secva + m.start()
            edges.append((va, va + 5 + rel))
            if len(edges) > 400000:
                break
        sstr.extend(_stack_strings(code, secva))
        if time.monotonic() - t0 > RELAB_TIME:
            notes.append("waktu analisis habis (%.0f dtk); hasil sebagian" % RELAB_TIME)
            stop = True
    # call E8 ke thunk -> panggilan API
    callee_edges = []
    for va, tgt in edges:
        if tgt in thunks:
            sites.append((va, thunks[tgt], "thunk"))
        elif in_code(tgt):
            callee_edges.append((va, tgt))
    # ---- penemuan fungsi ----
    starts: dict[int, str] = {}
    if L["entry_va"] and in_code(L["entry_va"]):
        starts[L["entry_va"]] = "entry"
    for va, nm in L["exports"].items():
        if in_code(va):
            starts.setdefault(va, "ekspor")
    tcount = collections.Counter(t for _v, t in callee_edges)
    for t in tcount:
        starts.setdefault(t, "call")
    pro = re.compile(rb"(?<=[\xCC\x90\xC3\x00])(?:\x55\x8B\xEC|\x8B\xFF\x55\x8B\xEC|\x48\x83\xEC[\x08-\x7f]|\x48\x89\x5C\x24|\x40\x53\x48\x83\xEC|\x48\x8B\xC4|\x4C\x8B\xDC|\x48\x81\xEC|\x40\x55\x48|\x48\x89\x6C\x24|\x48\x89\x74\x24)")
    for secva, _o, code, _nm in execs:
        for m in pro.finditer(code):
            if m.start() % 16 == 0:
                starts.setdefault(secva + m.start(), "prolog")
        if len(starts) > 60000:
            break
    for tva in thunks:
        starts.setdefault(tva, "thunk")
    fl = sorted(starts)
    ends = {}
    for i, s in enumerate(fl):
        sec_end = next((b for a, b in ranges if a <= s < b), s)
        ends[s] = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)

    def func_of(va):
        i = bisect.bisect_right(fl, va) - 1
        if i < 0:
            return None
        s = fl[i]
        return s if va < ends[s] else None
    F: dict[int, dict] = {}

    def fobj(s):
        if s not in F:
            nm = L["exports"].get(s) or ("start" if starts.get(s) == "entry" else ("thunk_" + thunks[s].split("!")[-1] if s in thunks else "sub_%08X" % s))
            F[s] = {"va": s, "name": nm, "size": ends.get(s, s) - s, "how": starts.get(s, "?"), "callers": 0, "callees": set(), "apis": {}, "strings": [], "anti": set()}
        return F[s]
    for va, tgt in callee_edges:
        cs = func_of(va)
        fobj(tgt)["callers"] += 1
        if cs is not None and cs != tgt:
            fobj(cs)["callees"].add(tgt)
    api_sites: dict[str, list[tuple[int, int]]] = {}
    for va, api, kind in sites:
        fs = func_of(va)
        if fs is not None and fs in thunks and kind != "ptr":
            continue
        if fs is not None:
            F_ = fobj(fs)
            F_["apis"][api] = F_["apis"].get(api, 0) + 1
        api_sites.setdefault(api, []).append((va, fs or 0))
    # ---- xref string ----
    sref: dict[int, dict] = {}
    seen_budget = 0
    for va, sva in strrefs:
        off = _va_off(L, sva)
        if off is None or off + 8 > len(d):
            continue
        if any(a <= sva < b for a, b in ranges):
            continue
        seen_budget += 1
        if seen_budget > 40000:
            break
        r = _rd_str(d, off)
        if not r:
            continue
        e = sref.setdefault(sva, {"va": sva, "kind": r[0], "text": r[1][:140], "funcs": set()})
        fs = func_of(va)
        if fs is not None:
            e["funcs"].add(fs)
            if len(fobj(fs)["strings"]) < 40:
                fobj(fs)["strings"].append(e["text"])
    # ---- API hashing ----
    if _RELAB_HASH is None:
        _RELAB_HASH = _relab_hash_table()
        _RELAB_HASH_RE = re.compile(b"|".join(re.escape(struct.pack("<I", h)) for h in _RELAB_HASH), re.S)
    hashes: dict[str, int] = {}
    scan_len = min(len(d), 8 * 1024 * 1024)
    for m in _RELAB_HASH_RE.finditer(d, 0, scan_len):
        nm = _RELAB_HASH.get(struct.unpack("<I", m.group(0))[0])
        if nm and nm not in hashes:
            hashes[nm] = m.start()
    ror_hits = len(anti.get("ROR 13 (kandidat API hashing)", []))
    hash_valid = len(hashes) >= 2
    # ---- anti-analisis -> fungsi ----
    for key, vas in anti.items():
        if key.startswith("ROR 13") and not hash_valid:
            continue
        for va in vas[:200]:
            fs = func_of(va)
            if fs is not None:
                fobj(fs)["anti"].add(key.split(" (")[0])
    # ---- peringkat ----
    ranked = []
    for s, f in F.items():
        tags, sc = _api_tags(list(f["apis"]))
        intr = [x for x in f["strings"] if _RE_INTR.search(x)]
        intr = list(dict.fromkeys(intr))
        sc += min(len(intr), 2) + (2 if len(f["anti"]) >= 2 else len(f["anti"]))
        if "syscall langsung" in " ".join(f["anti"]):
            sc += 3
        if sc >= 2:
            ranked.append((sc, s, tags, intr))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    top = []
    for sc, s, tags, intr in ranked[:RELAB_TOP]:
        f = F[s]
        top.append({"va": "0x%X" % s, "name": f["name"], "size": f["size"], "callers": f["callers"], "callees": len(f["callees"]), "score": sc,
                    "tags": tags, "apis": sorted(f["apis"])[:14], "strings": [_clean(x)[:90] for x in list(dict.fromkeys(intr or f["strings"]))[:4]], "anti": sorted(f["anti"])})
    refs = sorted(sref.values(), key=lambda e: (0 if _RE_INTR.search(e["text"]) else 1, -len(e["funcs"]), e["va"]))
    refs_out = []
    for e in refs[:30]:
        if not _RE_INTR.search(e["text"]) and len(refs_out) >= 8:
            break
        refs_out.append({"va": "0x%X" % e["va"], "kind": e["kind"], "tag": _str_tag(e["text"]), "text": _clean(e["text"]),
                         "funcs": ["0x%X" % x for x in sorted(e["funcs"])[:4]]})
    ssout = []
    for va, s in sstr:
        if not any(x["text"] == s for x in ssout):
            ssout.append({"va": "0x%X" % va, "text": _clean(s)[:100], "tag": _str_tag(s)})
        if len(ssout) >= 12:
            break
    api_top = sorted(((a, len(v)) for a, v in api_sites.items()), key=lambda x: (-x[1], x[0]))
    anti_out = []
    for key, vas in anti.items():
        if key.startswith("ROR 13") and not hash_valid:
            continue
        if key.startswith("RDTSC") and len(vas) < 2:
            continue
        if key.startswith("CPUID") and len(vas) < 1:
            continue
        anti_out.append({"technique": key, "count": len(vas), "first": "0x%X" % vas[0]})
    info = {
        "arch": arch_label or "%s (%d-bit)" % (pe["arch"], pe["bits"]), "image_base": "0x%X" % base, "n_functions": len(fl), "n_api_sites": len(sites),
        "n_iat": len(iat), "n_thunks": len(thunks), "n_strrefs": len(sref), "entry": "0x%X" % L["entry_va"] if L["entry_va"] else "", "entry_stub": _entry_stub(d, L),
        "functions": top, "api_top": api_top[:15], "string_refs": refs_out, "stack_strings": ssout, "anti": anti_out,
        "api_hashes": [{"api": k, "offset": "0x%X" % v} for k, v in list(hashes.items())[:12]] if hash_valid else [], "ror13_ops": ror_hits, "notes": notes,
    }
    ctx = {"L": L, "F": F, "sites": api_sites, "sref": sref, "fl": fl, "thunks": thunks}
    _cfg_enrich(info, ctx, d)     # v99.13 [S3]; kunci baru info["cfg"], aditif
    _emu_enrich(info, ctx, d)     # v99.18 [S2]; kunci baru info["emu"], aditif
    return info, ctx


