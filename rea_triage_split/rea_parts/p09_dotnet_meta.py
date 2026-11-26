# rea_triage bagian 09/47: dotnet_meta (baris asli 3873-4000). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- .NET metadata --------------------------------

_NET_STD_STREAMS = {"#~", "#-", "#Strings", "#US", "#GUID", "#Blob"}
_NET_CAPS = {
    "injeksi / manipulasi proses": {"VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "SetThreadContext", "QueueUserAPC", "NtWriteVirtualMemory"},
    "kripto": {"CreateDecryptor", "CreateEncryptor", "RijndaelManaged", "AesManaged", "AesCryptoServiceProvider", "TripleDESCryptoServiceProvider", "RSACryptoServiceProvider", "DESCryptoServiceProvider"},
    "muat kode dinamis": {"GetDelegateForFunctionPointer", "DefineDynamicAssembly", "LoadModule", "VirtualProtect", "VirtualAlloc", "GetProcAddress", "LoadLibrary"},
    "penyadap input / layar": {"SetWindowsHookEx", "GetAsyncKeyState", "GetKeyboardState", "CopyFromScreen", "GetForegroundWindow"},
    "anti-debug / anti-analisis": {"IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess"},
    "jaringan": {"DownloadString", "DownloadFile", "DownloadData", "UploadString", "UploadFile", "UploadValues", "TcpClient", "TcpListener"},
    "eksekusi proses / shell": {"ProcessStartInfo", "ShellExecute", "WinExec"},
}


def _dotnet_info(d: bytes, pe: dict) -> dict | None:
    """Metadata CLR: versi runtime, daftar stream, nama dari heap #Strings, string pengguna dari #US, dugaan obfuskasi."""
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    if nrva <= 14:
        return None
    rva, _sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 14)

    def r2o(x: int):
        for s in pe["sections"]:
            if s["va"] <= x < s["va"] + max(s["vsize"], s["rsize"]):
                return s["rptr"] + x - s["va"]
        return None

    co = r2o(rva)
    if co is None or co + 24 > len(d):
        return None
    _cb, _ma, _mi, mrva, _msz, cflags, etok = struct.unpack_from("<IHHIIII", d, co)
    mo = r2o(mrva)
    if mo is None or mo + 20 > len(d) or d[mo:mo + 4] != b"BSJB":
        return None
    vlen = struct.unpack_from("<I", d, mo + 12)[0]
    if vlen > 255 or mo + 16 + vlen + 4 > len(d):
        return None
    runtime = d[mo + 16:mo + 16 + vlen].split(b"\0")[0].decode("ascii", "replace")
    p = mo + 16 + vlen
    _fl, nstreams = struct.unpack_from("<HH", d, p)
    p += 4
    streams: dict[str, tuple[int, int]] = {}
    for _ in range(min(nstreams, 16)):
        if p + 9 > len(d):
            break
        so, ssz = struct.unpack_from("<II", d, p)
        e = d.find(b"\0", p + 8, p + 40)
        if e < 0:
            break
        nm = d[p + 8:e].decode("ascii", "replace")
        streams[nm] = (mo + so, ssz)
        p += 8 + ((len(nm) + 1 + 3) & ~3)
    names: list[str] = []
    st = streams.get("#Strings")
    if st and st[0] < len(d):
        heap = d[st[0]:st[0] + min(st[1], 4 * 1024 * 1024)]
        names = _uniq((x.decode("utf-8", "replace") for x in heap.split(b"\0") if x), 6000)
    us: list[str] = []
    ust = streams.get("#US")
    if ust and ust[0] < len(d):
        heap = d[ust[0]:ust[0] + min(ust[1], 4 * 1024 * 1024)]
        i = 1
        while i < len(heap) and len(us) < 3000:
            b0 = heap[i]
            if b0 < 0x80:
                ln, i = b0, i + 1
            elif b0 & 0xC0 == 0x80 and i + 1 < len(heap):
                ln, i = ((b0 & 0x3F) << 8) | heap[i + 1], i + 2
            elif b0 & 0xE0 == 0xC0 and i + 3 < len(heap):
                ln, i = ((b0 & 0x1F) << 24) | (heap[i + 1] << 16) | (heap[i + 2] << 8) | heap[i + 3], i + 4
            else:
                break
            if ln == 0:
                continue
            raw = heap[i:i + max(0, ln - 1)]
            i += ln
            s = raw.decode("utf-16le", "ignore")
            if len(s) >= 4 and sum(ch.isprintable() for ch in s) >= 0.9 * len(s):
                us.append(s[:300])
    obf: list[str] = []
    odd = [n_ for n_ in streams if n_ not in _NET_STD_STREAMS]
    if odd:
        obf.append("stream metadata tidak baku: " + ", ".join(odd[:3]))
    if len(names) >= 40:
        short = sum(1 for n_ in names if len(n_) <= 2)
        weird = sum(1 for n_ in names if any(ord(ch) > 126 or ord(ch) < 32 for ch in n_))
        if short / len(names) > 0.35:
            obf.append("%d%% nama tipe / anggota hanya 1-2 karakter (pola penggantian nama obfuskator)" % (100 * short // len(names)))
        if weird / len(names) > 0.2:
            obf.append("%d%% nama berisi karakter non-ASCII / kontrol (pola obfuskator)" % (100 * weird // len(names)))
    mres: list[dict] = []   # v98.6: resource terkelola dari header CLR (tiap blob: uint32 panjang + data; tanpa nama, nama ada di tabel metadata)
    try:
        rrva, rsz = struct.unpack_from("<II", d, co + 24)
        ro = r2o(rrva) if rrva and rsz else None
        if ro is not None:
            end, pos = min(ro + rsz, len(d)), ro
            while pos + 4 <= end and len(mres) < 64:
                ln = 0
                for cand in (pos, (pos + 3) & ~3, (pos + 7) & ~7):   # sebagian penghasil menyelaraskan blob; coba beberapa
                    if cand + 4 <= end:
                        v_ = struct.unpack_from("<I", d, cand)[0]
                        if 0 < v_ <= end - cand - 4:
                            pos, ln = cand + 4, v_
                            break
                if not ln:
                    break
                blob_ = d[pos:pos + min(ln, 1 << 20)]
                fmt_, ok_ = _res_format(d, pos, ln)
                mres.append({"off": pos, "size": ln, "ent": _entropy(blob_[:65536]), "mz": blob_[:2] == b"MZ", "rsrc": blob_[:4] == b"\xce\xca\xef\xbe",
                             "fmt": fmt_, "fmt_ok": ok_})
                pos += ln
    except (struct.error, IndexError, ValueError):
        pass
    return {"runtime": runtime, "streams": [(k, v[1]) for k, v in streams.items()], "ilonly": bool(cflags & 1), "strong": bool(cflags & 8),
            "entry_token": etok, "names": names, "us": us, "obf": obf, "n_names": len(names), "mres": mres}


def _net_caps(names: list[str]) -> dict[str, list[str]]:
    have = set(names)
    out = {cap: sorted(have & keys)[:6] for cap, keys in _NET_CAPS.items() if have & keys}
    if {"Assembly", "Load", "Invoke"} <= have:
        out.setdefault("muat kode dinamis", []).append("Assembly.Load + Invoke")
    return out


