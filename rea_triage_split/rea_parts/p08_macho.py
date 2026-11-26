# rea_triage bagian 08/47: macho (baris asli 3640-3872). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v97: Mach-O, metadata .NET, CTPH (hash fuzzy), perburuan XOR / ADD / ROL, detail kemasan, keluarga sampel,
#      laporan Markdown, dan API JSON untuk Iris / Hermes. Semuanya hanya-baca, pustaka standar, file tidak dijalankan.
# ---------------------------------------------------------------------------

VERSION = "99.65"
AUTHOR = "KangJiho"

# nama impor Mach-O (garis bawah depan sudah dibuang) yang menandai manipulasi proses lain
EXACT_CAPS["injeksi / manipulasi proses"] = EXACT_CAPS["injeksi / manipulasi proses"] | {"task_for_pid", "mach_vm_write", "mach_vm_protect", "thread_create_running"}
STR_CAPS["macOS: persistensi / manipulasi sistem"] = ["launchagents", "launchdaemons", "com.apple.quarantine", "osascript", "dyld_insert_libraries", "tccutil", "security find-generic-password"]
ATTACK["macOS: persistensi / manipulasi sistem"] = "T1543.001 Launch Agent / T1574.006 Dynamic Linker Hijacking / T1553.001 Gatekeeper Bypass"

# ----------------------------- Mach-O ---------------------------------------

_MACHO_CPU = {7: "x86", 0x01000007: "x86-64", 12: "ARM", 0x0100000C: "ARM64", 0x0200000C: "ARM64_32", 18: "PowerPC", 0x01000012: "PowerPC64"}
_MACHO_FT = {1: "object (.o)", 2: "executable", 3: "fvmlib", 4: "core dump", 5: "preload", 6: "dylib", 7: "dylinker", 8: "bundle", 9: "dylib stub", 10: "dSYM", 11: "kext"}
_MACHO_PLAT = {1: "macOS", 2: "iOS", 3: "tvOS", 4: "watchOS", 5: "bridgeOS", 6: "Mac Catalyst", 7: "iOS Simulator", 8: "tvOS Simulator", 9: "watchOS Simulator", 10: "DriverKit"}


def _macho_cstr(d: bytes, off: int, lim: int) -> str:
    if off < 0 or off >= len(d):
        return ""
    stop = min(len(d), off + max(0, lim))
    e = d.find(b"\0", off, stop)
    return d[off:e if e >= 0 else stop].decode("utf-8", "replace")


_ENT_RISKY = {
    "com.apple.security.cs.allow-unsigned-executable-memory": "izinkan memori eksekusi tak bertanda tangan",
    "com.apple.security.cs.allow-jit": "izinkan JIT",
    "com.apple.security.cs.disable-library-validation": "muat dylib tanpa validasi tanda tangan (rawan dylib hijacking)",
    "com.apple.security.cs.allow-dyld-environment-variables": "izinkan DYLD_* (injeksi dylib)",
    "com.apple.security.cs.disable-executable-page-protection": "matikan proteksi halaman eksekusi",
    "com.apple.security.get-task-allow": "proses boleh di-debug / task_for_pid",
    "com.apple.security.cs.debugger": "boleh men-debug proses lain",
    "task_for_pid-allow": "boleh task_for_pid ke proses lain",
    "com.apple.private.tcc.allow": "bypass izin privasi (TCC), entitlement privat Apple",
    "com.apple.rootless.install": "boleh menulis area SIP",
    "com.apple.security.app-sandbox": None,   # sandbox aktif = mitigasi, bukan risiko
}
_ENT_KV = re.compile(r"<key>([^<]{1,160})</key>\s*(<true\s*/>|<false\s*/>|<string>([^<]{0,120})</string>|<array>|<dict>|<integer>(\d{1,12})</integer>)")


def _macho_codesig(d: bytes, base: int, dataoff: int, size: int) -> dict:
    """v99.3 [B3]: baca SuperBlob LC_CODE_SIGNATURE (big-endian): flag CodeDirectory (hardened runtime / ad-hoc) dan entitlements XML."""
    out: dict = {"runtime": False, "adhoc": False, "keys": [], "risky": [], "sandbox": False, "has_ent": False}
    st = base + dataoff
    if dataoff <= 0 or size < 12 or st + 12 > len(d) or d[st:st + 4] != b"\xfa\xde\x0c\xc0":
        return out
    n = struct.unpack_from(">I", d, st + 8)[0]
    end = min(len(d), st + min(size, 1 << 22))
    for i in range(min(n, 16)):
        p = st + 12 + i * 8
        if p + 8 > end:
            break
        bo = struct.unpack_from(">I", d, p + 4)[0]
        b0 = st + bo
        if b0 + 8 > end:
            continue
        magic, blen = struct.unpack_from(">II", d, b0)
        if magic == 0xFADE0C02 and b0 + 16 <= end:   # CodeDirectory
            cf = struct.unpack_from(">I", d, b0 + 12)[0]
            out["adhoc"], out["runtime"] = bool(cf & 0x2), bool(cf & 0x10000)
        elif magic == 0xFADE7171:   # entitlements (XML plist)
            out["has_ent"] = True
            xml = d[b0 + 8:b0 + min(blen, 65536)].decode("utf-8", "replace")
            for m in _ENT_KV.finditer(xml):
                k, v = m.group(1), m.group(2)
                val = "true" if v.startswith("<true") else "false" if v.startswith("<false") else (m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) else "..."))
                if len(out["keys"]) < 40:
                    out["keys"].append("%s=%s" % (k, val))
                if k == "com.apple.security.app-sandbox" and val == "true":
                    out["sandbox"] = True
                elif k in _ENT_RISKY and _ENT_RISKY[k] and val != "false":
                    out["risky"].append("%s (%s)" % (k, _ENT_RISKY[k]))
                elif k.startswith("com.apple.private.") and val != "false" and len(out["risky"]) < 12:
                    out["risky"].append("%s (entitlement privat Apple)" % k)
    out["risky"] = out["risky"][:12]
    return out


def _macho_thin(d: bytes, base: int = 0) -> dict | None:
    if base < 0 or base + 28 > len(d):
        return None
    m = d[base:base + 4]
    if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        e = "<"
    elif m in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
        e = ">"
    else:
        return None
    is64 = m[0] == 0xCF or m[3] == 0xCF
    hsz = 32 if is64 else 28
    if base + hsz > len(d):
        return None
    cpu, _sub, ft, ncmds, szcmds, flags = struct.unpack_from(e + "IIIIII", d, base + 4)
    info: dict = {"bits": 64 if is64 else 32, "endian": "little" if e == "<" else "big", "arch": _MACHO_CPU.get(cpu, "cpu 0x%X" % cpu),
                  "type": _MACHO_FT.get(ft, str(ft)), "ncmds": ncmds, "pie": bool(flags & 0x200000), "segments": [], "sections": [], "dylibs": [],
                  "weak": [], "rpaths": [], "entry": "", "signed": False, "encrypted": False, "uuid": "", "platform": "", "imports": [],
                  "exports": [], "nsyms": 0, "warn": [], "fat": [], "sig": None}
    off = base + hsz
    end = min(len(d), off + szcmds)
    symtab = None
    ent_left = ENT_BUDGET
    for _ in range(min(ncmds, 600)):
        if off + 8 > end:
            break
        cmd, csz = struct.unpack_from(e + "II", d, off)
        if csz < 8 or off + csz > end:
            break
        c = cmd & 0x7FFFFFFF
        if c in (0x1, 0x19):
            fmt, need, sec_sz = (e + "16sQQQQiiII", 72, 80) if c == 0x19 else (e + "16sIIIIiiII", 56, 68)
            if csz >= need:
                nm, _va, vsz, fo, fsz, _mp, ip, ns, _fl = struct.unpack_from(fmt, d, off + 8)
                sname = nm.split(b"\0")[0].decode("ascii", "replace")
                raw = d[base + fo:base + fo + min(fsz, SEC_ENT_SAMPLE)] if fo < len(d) else b""
                ent = 0.0
                if raw and len(raw) <= ent_left:
                    ent = _entropy(raw)
                    ent_left -= len(raw)
                info["segments"].append({"name": sname, "vsize": vsz, "fsize": fsz, "prot": "".join(ch if ip & b else "-" for ch, b in (("R", 1), ("W", 2), ("X", 4))), "ent": ent})
                for i in range(min(ns, 64)):
                    p = off + need + i * sec_sz
                    if p + 32 > off + csz:
                        break
                    info["sections"].append("%s,%s" % (sname, d[p:p + 16].split(b"\0")[0].decode("ascii", "replace")))
        elif c in (0xC, 0x18, 0x1F, 0x23, 0x20) and csz >= 24:
            noff = struct.unpack_from(e + "I", d, off + 8)[0]
            nm_ = _macho_cstr(d, off + noff, csz - noff) if noff < csz else ""
            (info["weak"] if c == 0x18 else info["dylibs"]).append(nm_)
        elif c == 0x1C and csz >= 12:
            noff = struct.unpack_from(e + "I", d, off + 8)[0]
            info["rpaths"].append(_macho_cstr(d, off + noff, csz - noff) if noff < csz else "")
        elif c == 0x28 and csz >= 16:
            info["entry"] = "LC_MAIN +0x%X" % struct.unpack_from(e + "Q", d, off + 8)[0]
        elif c == 0x5:
            info["entry"] = info["entry"] or "LC_UNIXTHREAD"
        elif c == 0x1D:
            info["signed"] = True
            if csz >= 16:
                try:
                    info["sig"] = _macho_codesig(d, base, *struct.unpack_from(e + "II", d, off + 8))
                except (struct.error, IndexError):
                    info["sig"] = None
        elif c in (0x21, 0x2C) and csz >= 20:
            info["encrypted"] = struct.unpack_from(e + "I", d, off + 16)[0] != 0
        elif c == 0x1B and csz >= 24:
            info["uuid"] = d[off + 8:off + 24].hex()
        elif c == 0x2 and csz >= 24:
            symtab = struct.unpack_from(e + "IIII", d, off + 8)
        elif c == 0x32 and csz >= 12:
            info["platform"] = _MACHO_PLAT.get(struct.unpack_from(e + "I", d, off + 8)[0], "")
        elif c == 0x24:
            info["platform"] = info["platform"] or "macOS"
        elif c == 0x25:
            info["platform"] = info["platform"] or "iOS"
        off += csz
    if symtab:
        so, ns, sto, stsz = symtab
        esz = 16 if is64 else 12
        info["nsyms"] = ns
        imp, exp_ = [], []
        for i in range(min(ns, 50000)):
            p = base + so + i * esz
            if p + esz > len(d):
                break
            strx, nt, _nsect, _ndesc = struct.unpack_from(e + "IBBH", d, p)
            if nt & 0xE0 or not nt & 1 or strx >= stsz:
                continue    # simbol debug (STAB) atau bukan eksternal
            nm_ = _macho_cstr(d, base + sto + strx, min(200, stsz - strx))
            nm_ = nm_[1:] if nm_.startswith("_") else nm_
            if not nm_:
                continue
            if nt & 0x0E == 0 and len(imp) < 1500:
                imp.append(nm_)
            elif nt & 0x0E == 0x0E and len(exp_) < 300:
                exp_.append(nm_)
        info["imports"], info["exports"] = imp, exp_
    w = info["warn"]
    if info["encrypted"]:
        w.append("Mach-O: segmen terenkripsi (cryptid=1, mis. FairPlay App Store); isi kode tidak bisa dibaca sebelum didekripsi")
    if not info["signed"] and info["type"] in ("executable", "dylib", "bundle"):
        w.append("Mach-O: tidak ada LC_CODE_SIGNATURE (tanda tangan dihapus atau belum diberikan)")
    for s in info["segments"]:
        if s["prot"][1:] == "WX":
            w.append("Mach-O: segmen %s dapat ditulis DAN dieksekusi (W+X)" % s["name"])
        if s["ent"] > 7.2 and s["fsize"] > 16384 and s["name"] != "__LINKEDIT":
            w.append("Mach-O: segmen %s berentropi %.2f (terkompres / terenkripsi / dikemas)" % (s["name"], s["ent"]))
    sg = info.get("sig")
    if sg:
        if sg["risky"]:
            w.append("Mach-O: entitlements berisiko: " + "; ".join(sg["risky"][:4]))
        if sg["adhoc"]:
            w.append("Mach-O: tanda tangan ad-hoc (tanpa identitas pengembang)")
        if info["type"] == "executable" and not sg["runtime"] and not sg["adhoc"]:
            w.append("Mach-O: hardened runtime tidak aktif")
    if any(r.startswith(("@loader_path", "@executable_path", ".")) for r in info["rpaths"]) and info["weak"]:
        w.append("Mach-O: RPATH relatif ditambah dylib lemah (kandidat dylib hijacking)")
    return info


def _parse_macho(d: bytes) -> dict | None:
    """Mach-O tipis atau fat / universal. Fat: irisan pertama yang terurai dipakai, daftar arsitektur lain disimpan di ['fat']."""
    if len(d) < 28:
        return None
    m = d[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None   # berkas class Java memakai magic yang sama; angka versinya selalu >= 45
        f64 = m[3] == 0xBF
        esz = 32 if f64 else 20
        slices = []
        for i in range(n):
            p = 8 + i * esz
            if p + esz > len(d):
                break
            if f64:
                cpu, _s, off, size, _a, _r = struct.unpack_from(">IIQQII", d, p)
            else:
                cpu, _s, off, size, _a = struct.unpack_from(">IIIII", d, p)
            slices.append((_MACHO_CPU.get(cpu, "cpu 0x%X" % cpu), off, size))
        for _arch, off, _size in slices:
            r = _macho_thin(d, off)
            if r:
                r["fat"] = [(a_, o_, s_) for a_, o_, s_ in slices]
                return r
        return None
    return _macho_thin(d, 0)


