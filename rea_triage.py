"""rea_triage.py - triase statis lokal untuk perintah /rea (Iris v91).

Dihitung langsung di PC oleh Python (hanya pustaka standar), TANPA LLM dan TANPA menjalankan file:
hash, jenis file, entropi, header PE / ELF / ZIP (APK, JAR), import / export, bagian (section), string menarik,
indikasi kemampuan, dan tanda-tanda packer. Hasilnya dipakai dua cara:
  1. mode `/rea cepat`: langsung jadi laporan (hitungan detik, tanpa Hermes, akurat karena murni hitungan);
  2. mode standar / dalam: disisipkan ke tugas Hermes sebagai FAKTA TERUKUR, supaya agen tidak perlu menebak
     dan tidak bisa mengarang hal dasar (hash, format, import).

API:
    triage(path) -> dict
    render(rep, compact=False) -> str
    triage_text(path, compact=False) -> str
"""
from __future__ import annotations

import collections
import datetime as _dt
import hashlib
import math
import re
import struct
import zipfile
from pathlib import Path

MAX_SCAN = 32 * 1024 * 1024          # byte yang dipindai untuk string / parsing (file lebih besar: awal file saja)
ENT_SAMPLE = 4 * 1024 * 1024         # sampel untuk entropi keseluruhan
SEC_ENT_SAMPLE = 1 * 1024 * 1024     # sampel per bagian PE

# ---------------------------------------------------------------------------
# Dasar
# ---------------------------------------------------------------------------


def _entropy(b: bytes) -> float:
    if not b:
        return 0.0
    n = len(b)
    c = collections.Counter(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def _hash_file(path: Path) -> dict:
    h256, h1, hmd = hashlib.sha256(), hashlib.sha1(), hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h256.update(chunk)
            h1.update(chunk)
            hmd.update(chunk)
    return {"sha256": h256.hexdigest(), "sha1": h1.hexdigest(), "md5": hmd.hexdigest()}


def _human(n: int) -> str:
    x = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if x < 1024 or u == "GB":
            return ("%d %s" % (x, u)) if u == "B" else ("%.1f %s" % (x, u))
        x /= 1024
    return "%d B" % n


_MACHINE = {0x14c: "x86", 0x8664: "x64", 0x1c0: "ARM", 0xaa64: "ARM64", 0x1c4: "ARMv7 Thumb", 0x200: "IA-64", 0x0: "tak dikenal"}
_SUBSYS = {1: "Native", 2: "GUI", 3: "Console", 5: "OS/2", 7: "POSIX", 9: "WinCE", 10: "EFI app", 11: "EFI boot driver", 12: "EFI runtime", 14: "Xbox"}
_ELF_MACHINE = {3: "x86", 8: "MIPS", 20: "PowerPC", 40: "ARM", 62: "x86-64", 183: "AArch64", 243: "RISC-V", 94: "Xtensa"}
_ELF_TYPE = {1: "relocatable (.o)", 2: "executable", 3: "shared object / PIE", 4: "core dump"}

# ---------------------------------------------------------------------------
# PE
# ---------------------------------------------------------------------------


def _parse_pe(d: bytes, file_size: int) -> dict | None:
    if len(d) < 0x40 or d[:2] != b"MZ":
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    if pe_off + 24 > len(d) or d[pe_off:pe_off + 4] != b"PE\0\0":
        return {"broken": "header MZ ada tetapi tanda PE tidak ditemukan (DOS stub saja, rusak, atau dikemas)"}
    machine, nsec, ts, _p, _n, optsz, chars = struct.unpack_from("<HHIIIHH", d, pe_off + 4)
    o = pe_off + 24
    if o + 96 > len(d):
        return {"broken": "optional header terpotong"}
    magic = struct.unpack_from("<H", d, o)[0]
    is64 = magic == 0x20B
    entry = struct.unpack_from("<I", d, o + 16)[0]
    subsys, dllch = struct.unpack_from("<HH", d, o + 68)
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    dd_off = o + (112 if is64 else 96)
    dirs = []
    for i in range(min(nrva, 16)):
        if dd_off + 8 * i + 8 > len(d):
            break
        dirs.append(struct.unpack_from("<II", d, dd_off + 8 * i))

    secs = []
    so = o + optsz
    for i in range(min(nsec, 96)):
        p = so + 40 * i
        if p + 40 > len(d):
            break
        nm, vsz, va, rsz, rptr, _r, _l, _nr, _nl, ch = struct.unpack_from("<8sIIIIIIHHI", d, p)
        name = nm.rstrip(b"\0").decode("latin-1", "replace")
        raw = d[rptr:rptr + min(rsz, SEC_ENT_SAMPLE)] if rptr < len(d) else b""
        secs.append({
            "name": name, "va": va, "vsize": vsz, "rptr": rptr, "rsize": rsz,
            "flags": ("R" if ch & 0x40000000 else "-") + ("W" if ch & 0x80000000 else "-") + ("X" if ch & 0x20000000 else "-"),
            "ent": _entropy(raw) if raw else 0.0,
        })

    def rva2off(rva: int) -> int | None:
        for s in secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rsize"]):
                return rva - s["va"] + s["rptr"]
        if secs and rva < min(s["va"] for s in secs):
            return rva
        return None

    def cstr(off: int, lim: int = 128) -> str:
        if off is None or off < 0 or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    imports: dict[str, list[str]] = {}
    try:
        if len(dirs) > 1 and dirs[1][0]:
            off = rva2off(dirs[1][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 20 <= len(d) and n < 60:
                oft, _t, _f, name_rva, ft = struct.unpack_from("<IIIII", d, off)
                if not (oft or name_rva or ft):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns: list[str] = []
                th = rva2off(oft or ft)
                k = 0
                while th is not None and th + step <= len(d) and k < 600:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(cstr((rva2off(v & 0x7FFFFFFF) or 0) + 2))
                    th += step
                    k += 1
                imports[dll or "?"] = fns
                off += 20
                n += 1
    except (struct.error, IndexError):
        pass

    exports: list[str] = []
    try:
        if dirs and dirs[0][0]:
            eo = rva2off(dirs[0][0])
            if eo is not None and eo + 40 <= len(d):
                nnames = struct.unpack_from("<I", d, eo + 24)[0]
                names_rva = struct.unpack_from("<I", d, eo + 32)[0]
                no = rva2off(names_rva)
                for i in range(min(nnames, 80)):
                    if no is None or no + 4 * i + 4 > len(d):
                        break
                    exports.append(cstr(rva2off(struct.unpack_from("<I", d, no + 4 * i)[0])))
    except (struct.error, IndexError):
        pass

    cert = dirs[4] if len(dirs) > 4 else (0, 0)
    last_raw = max([s["rptr"] + s["rsize"] for s in secs] or [0])
    overlay = max(0, file_size - last_raw) if last_raw else 0
    try:
        stamp = _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "0"
    except (OverflowError, OSError, ValueError):
        stamp = "tidak valid"
    return {
        "arch": _MACHINE.get(machine, hex(machine)), "bits": 64 if is64 else 32,
        "dll": bool(chars & 0x2000), "subsys": _SUBSYS.get(subsys, str(subsys)),
        "stamp": stamp, "ts": ts, "entry": entry,
        "aslr": bool(dllch & 0x40), "dep": bool(dllch & 0x100), "cfg": bool(dllch & 0x4000),
        "dotnet": len(dirs) > 14 and dirs[14][0] != 0 and dirs[14][1] != 0,
        "signed": cert[0] != 0 and cert[1] != 0, "overlay": overlay,
        "sections": secs, "imports": imports, "exports": exports,
    }


# ---------------------------------------------------------------------------
# ELF, ZIP / APK / JAR
# ---------------------------------------------------------------------------


def _parse_elf(d: bytes) -> dict | None:
    if len(d) < 20 or d[:4] != b"\x7fELF":
        return None
    bits = 64 if d[4] == 2 else 32
    en = "<" if d[5] == 1 else ">"
    etype, mach = struct.unpack_from(en + "HH", d, 16)
    return {"bits": bits, "endian": "little" if en == "<" else "big",
            "type": _ELF_TYPE.get(etype, str(etype)), "arch": _ELF_MACHINE.get(mach, str(mach))}


_PERM_RE = re.compile(rb"android\.permission\.[A-Z_]+")
_PERM_RE16 = re.compile(rb"(?:a\x00n\x00d\x00r\x00o\x00i\x00d\x00\.\x00p\x00e\x00r\x00m\x00i\x00s\x00s\x00i\x00o\x00n\x00\.\x00)(?:[A-Z_]\x00)+")


def _parse_zip(path: Path) -> dict | None:
    if not zipfile.is_zipfile(path):
        return None
    out: dict = {"names": [], "n": 0, "unc": 0, "kind": "ZIP", "warn": [], "perms": [], "dex": 0, "nested": []}
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        out["n"] = len(infos)
        names = [i.filename for i in infos]
        out["names"] = names[:50]
        out["unc"] = sum(i.file_size for i in infos)
        comp = sum(i.compress_size for i in infos) or 1
        out["ratio"] = out["unc"] / comp
        if any(i.flag_bits & 1 for i in infos):
            out["warn"].append("ada entri terenkripsi (kata sandi)")
        if any(n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") for n in names):
            out["warn"].append("nama entri berpola path traversal (zip-slip)")
        if out["ratio"] > 200:
            out["warn"].append("rasio kompresi %.0fx (kemungkinan zip bomb)" % out["ratio"])
        low = [n.lower() for n in names]
        if "androidmanifest.xml" in low:
            out["kind"] = "APK (Android)"
            out["dex"] = sum(1 for n in low if re.fullmatch(r"classes\d*\.dex", n))
            try:
                mf = z.read("AndroidManifest.xml")[:400000]
                perms = {m.decode() for m in _PERM_RE.findall(mf)}
                perms |= {m.decode("utf-16le", "ignore") for m in _PERM_RE16.findall(mf)}
                out["perms"] = sorted(perms)[:40]
            except Exception:
                pass
        elif "meta-inf/manifest.mf" in low:
            out["kind"] = "JAR/WAR (Java)"
            try:
                mf = z.read(names[low.index("meta-inf/manifest.mf")])[:4096].decode("utf-8", "replace")
                m = re.search(r"Main-Class:\s*(\S+)", mf)
                out["main"] = m.group(1) if m else ""
            except Exception:
                pass
        elif any(n.endswith(".class") for n in low):
            out["kind"] = "JAR (Java, tanpa manifest)"
        elif "[content_types].xml" in low:
            out["kind"] = "Paket OOXML (docx/xlsx/pptx)" + (" DENGAN makro VBA" if any("vbaproject.bin" in n for n in low) else "")
        out["nested"] = [n for n in names if n.lower().endswith((".exe", ".dll", ".jar", ".apk", ".so", ".dex", ".bat", ".ps1", ".vbs", ".js", ".scr", ".sh"))][:25]
    return out


# ---------------------------------------------------------------------------
# String dan indikator
# ---------------------------------------------------------------------------

_ASCII = re.compile(rb"[\x20-\x7e]{6,}")
_UTF16 = re.compile(rb"(?:[\x20-\x7e]\x00){6,}")
_URL = re.compile(r"(?:https?|ftp|wss?)://[^\s\"'<>\\^`{}|]{4,200}", re.I)
_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_MAIL = re.compile(r"[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9-]{2,}\.[A-Za-z.]{2,}")
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
    "persistensi": ["RegSetValueEx", "RegCreateKeyEx", "CreateService", "OpenSCManager", "schtasks", "CurrentVersion\\Run", "StartupInfo"],
    "kripto": ["CryptEncrypt", "CryptDecrypt", "CryptAcquireContext", "BCryptEncrypt", "BCryptDecrypt", "CryptGenKey", "AES", "RijndaelManaged"],
    "penyadap input / layar": ["SetWindowsHookEx", "GetAsyncKeyState", "GetKeyboardState", "GetClipboardData", "BitBlt", "GetDC"],
    "eksekusi proses / shell": ["CreateProcess", "ShellExecute", "WinExec", "system(", "cmd.exe", "powershell", "Process.Start"],
    "hak akses": ["AdjustTokenPrivileges", "OpenProcessToken", "LookupPrivilegeValue", "SeDebugPrivilege", "ImpersonateLoggedOnUser"],
    "muat kode dinamis": ["LoadLibrary", "GetProcAddress", "LdrLoadDll", "Assembly.Load", "Reflection", "VirtualProtect", "VirtualAlloc"],
    "berkas / penghapusan": ["DeleteFile", "MoveFileEx", "SHFileOperation", "RemoveDirectory", "CreateFile"],
}
_PACKERS = ("upx0", "upx1", ".upx", ".themida", ".vmp0", ".vmp1", ".aspack", ".adata", ".petite", ".nsp0", ".mpress1", "mpress", ".enigma1", ".winlice", ".boom")


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


def _indicators(strs: list[str], api_names: set[str]) -> dict:
    blob = "\n".join(strs)
    urls = _uniq((u.rstrip(".,;)") for u in _URL.findall(blob)), 25)
    ips = []
    for ip in _IP.findall(blob):
        o = [int(x) for x in ip.split(".")]
        if any(x > 255 for x in o) or o[0] == 0 or (o[2] == 0 and o[3] == 0):
            continue   # buang yang jelas nomor versi
        ips.append(ip)
    secrets = _uniq((_mask(m) for m in _SECRET.findall(blob)), 8)
    caps: dict[str, list[str]] = {}
    low_blob = blob.lower()
    for cap, keys in CAPS.items():
        hit = []
        for k in keys:
            if any(k.lower() in a.lower() for a in api_names) or (len(k) > 7 and k.lower() in low_blob):
                hit.append(k)
        if hit:
            caps[cap] = hit[:6]
    return {
        "urls": urls, "ips": _uniq(ips, 15), "emails": _uniq(_MAIL.findall(blob), 10),
        "reg": _uniq(_REG.findall(blob), 12), "paths": _uniq(_WPATH.findall(blob), 12),
        "secrets": secrets, "pem": bool(_PEM.search(blob)),
        "b64": len(_B64.findall(blob)), "caps": caps, "n_strings": len(strs),
    }


# ---------------------------------------------------------------------------
# Utama
# ---------------------------------------------------------------------------


def triage(path) -> dict:
    p = Path(path)
    size = p.stat().st_size
    rep: dict = {"name": p.name, "size": size, "warn": []}
    rep.update(_hash_file(p))
    with open(p, "rb") as f:
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
            zp = _parse_zip(p)
        except Exception as e:
            rep["warn"].append("parser ZIP gagal: %s" % type(e).__name__)

    head = d[:16]
    if pe and not pe.get("broken"):
        kind = "PE%s %s (%s)" % ("32+" if pe["bits"] == 64 else "32", "DLL" if pe["dll"] else "executable", pe["subsys"])
        kind += ", " + pe["arch"] + (", .NET (managed)" if pe["dotnet"] else ", native")
        for fns in pe["imports"].values():
            api_names.update(fns)
        api_names.update(pe["exports"])
    elif pe:
        kind = "MZ/DOS (%s)" % pe["broken"]
    elif elf:
        kind = "ELF%d %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"])
    elif zp:
        kind = zp["kind"]
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
    else:
        txt = sum(1 for b in d[:4096] if 9 <= b <= 13 or 32 <= b <= 126)
        kind = "teks / skrip" if d[:4096] and txt / len(d[:4096]) > 0.95 else "biner tak dikenal (tanpa magic number umum)"
    rep["kind"] = kind
    rep["pe"], rep["elf"], rep["zip"] = pe, elf, zp

    strs = _strings(d)
    rep["ind"] = _indicators(strs, api_names)

    w = rep["warn"]
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
    if rep["ind"]["secrets"]:
        w.append("kandidat kredensial tertanam (nilai disamarkan di laporan)")
    return rep


def render(rep: dict, compact: bool = False) -> str:
    L: list[str] = []
    a = L.append
    a("TRIASE LOKAL (dihitung Iris langsung dari bytes file; bukan klaim agen)")
    a("File   : %s | %s (%s B)" % (rep["name"], _human(rep["size"]), format(rep["size"], ",")))
    a("SHA-256: " + rep["sha256"])
    if not compact:
        a("SHA-1  : " + rep["sha1"])
    a("MD5    : " + rep["md5"])
    a("Jenis  : " + rep["kind"])
    a("Entropi: %.2f / 8.00%s" % (rep["entropy"], " (sampel %s pertama)" % _human(ENT_SAMPLE) if rep["size"] > ENT_SAMPLE else ""))
    if rep.get("truncated"):
        a("Catatan: file %s; string dan header dipindai dari %s pertama saja." % (_human(rep["size"]), _human(MAX_SCAN)))

    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    if pe and not pe.get("broken"):
        a("PE     : %s %s | entry RVA 0x%X | compile %s | tanda tangan: %s | overlay: %s" % (
            pe["arch"], pe["subsys"], pe["entry"], pe["stamp"], "ada" if pe["signed"] else "tidak ada", _human(pe["overlay"])))
        a("Proteksi: ASLR %s, DEP %s, CFG %s" % tuple("ya" if x else "tidak" for x in (pe["aslr"], pe["dep"], pe["cfg"])))
        secs = pe["sections"][: (8 if compact else 20)]
        a("Bagian : " + "; ".join("%s %s ent %.1f raw %s" % (s["name"] or "?", s["flags"], s["ent"], _human(s["rsize"])) for s in secs))
        imps = pe["imports"]
        if imps:
            tot = sum(len(v) for v in imps.values())
            lim = 8 if compact else 30
            a("Import : %d DLL, %d fungsi: " % (len(imps), tot) + ", ".join("%s(%d)" % (k, len(v)) for k, v in list(imps.items())[:lim]))
            if not compact:
                for k, v in list(imps.items())[:30]:
                    a("   %s: %s" % (k, ", ".join(v[:40]) + (" …" if len(v) > 40 else "")))
        if pe["exports"]:
            a("Export : %d nama: %s" % (len(pe["exports"]), ", ".join(pe["exports"][: (10 if compact else 60)])))
    elif pe:
        a("PE     : " + pe["broken"])
    if elf:
        a("ELF    : %d-bit %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"]))
    if zp:
        a("Arsip  : %s, %d entri, %s tak terkompresi (rasio %.1fx)" % (zp["kind"], zp["n"], _human(zp["unc"]), zp.get("ratio", 0)))
        if zp.get("main"):
            a("Main-Class: " + zp["main"])
        if zp.get("dex"):
            a("DEX    : %d berkas classes*.dex" % zp["dex"])
        if zp.get("perms"):
            a("Izin Android (%d): %s" % (len(zp["perms"]), ", ".join(p.replace("android.permission.", "") for p in zp["perms"][: (10 if compact else 40)])))
        if zp.get("nested"):
            a("Berkas tertanam menarik: " + ", ".join(zp["nested"][: (6 if compact else 25)]))
        if not compact:
            a("Isi (50 pertama): " + ", ".join(zp["names"]))

    ind = rep["ind"]
    if ind["caps"]:
        a("Indikasi kemampuan (petunjuk dari nama API/string, BUKAN bukti perilaku; installer sah juga memakainya):")
        for cap, hit in ind["caps"].items():
            a("   - %s: %s" % (cap, ", ".join(hit)))
    lim = 5 if compact else 25
    for label, key in (("URL", "urls"), ("Kandidat IP (bisa nomor versi)", "ips"), ("Email", "emails"), ("Kunci registry", "reg"), ("Path Windows", "paths")):
        if ind[key]:
            a("%s (%d): %s" % (label, len(ind[key]), " | ".join(ind[key][:lim])))
    if ind["secrets"]:
        a("Kandidat kredensial tertanam (disamarkan): " + ", ".join(ind["secrets"]))
    if ind["b64"]:
        a("String mirip base64 panjang: %d (kemungkinan data terenkode, perlu didekode)" % ind["b64"])
    a("String terbaca: %d" % ind["n_strings"])
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][: (6 if compact else 20)]:
            a("   ! " + x)
    a("Batas triase: hasil di atas murni pembacaan statis; tanpa dekompilasi, tanpa emulasi, tanpa jaringan, file tidak dijalankan.")
    return "\n".join(L)


def triage_text(path, compact: bool = False) -> str:
    try:
        return render(triage(path), compact=compact)
    except Exception as e:
        return "TRIASE LOKAL gagal (%s: %s). Lanjutkan tanpa data ini." % (type(e).__name__, str(e)[:120])


if __name__ == "__main__":   # uji manual: python rea_triage.py <file>
    import sys
    print(triage_text(sys.argv[1]) if len(sys.argv) > 1 else "pemakaian: python rea_triage.py <file>")
