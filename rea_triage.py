"""rea_triage.py - triase statis lokal untuk perintah /rea (Iris v96, kumulatif dengan v95, v94, v93, v92, v91).

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

v95: modul triase ini TIDAK berubah perilakunya. Ekstraksi / penjelajahan container dipisah ke rea_extract.py
(ZIP, TAR/gz, GZIP, ISO 9660, ISO PSP). Fungsi tipis di bawah hanya meneruskan ke sana (impor malas, opsional):
    container_text(path, max_chars=0) -> str      daftar isi ringkas untuk laporan / Hermes
    container_extract(path, outdir, pattern=None, scan=False) -> dict   ekstraksi selektif + manifest

v96: Binary Workbench dipisah ke rea_binary.py (hex view, data inspector, pencarian, compare, patch dengan undo).
    hex_text(path, offset=0, length=256) -> str ; compare_text(a, b) -> str   (jembatan tipis, impor malas)
"""
from __future__ import annotations

import base64
import collections
import os
import time
import datetime as _dt
import hashlib
import json
import math
import re
import array
import stat
import struct
import sys
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


_RES_TYPES = {1: "CURSOR", 2: "BITMAP", 3: "ICON", 4: "MENU", 5: "DIALOG", 6: "STRING", 9: "ACCELERATOR", 10: "RCDATA", 11: "MESSAGETABLE",
              12: "GROUP_CURSOR", 14: "GROUP_ICON", 16: "VERSION", 24: "MANIFEST"}
_VER_KEYS = ("CompanyName", "FileDescription", "FileVersion", "InternalName", "OriginalFilename", "ProductName")


def _res_entries(d: bytes, off):
    if off is None or off < 0 or off + 16 > len(d):
        return []
    nn, ni = struct.unpack_from("<HH", d, off + 12)
    out = []
    for i in range(min(nn + ni, 64)):
        o = off + 16 + 8 * i
        if o + 8 > len(d):
            break
        name, tgt = struct.unpack_from("<II", d, o)
        out.append((name, tgt & 0x7FFFFFFF, bool(tgt & 0x80000000)))
    return out


def _parse_resources(d: bytes, base, rva2off) -> tuple[list[dict], dict]:
    """Jelajahi direktori resource PE (tipe -> nama -> bahasa). Hanya membaca; tidak mengekstrak apa pun."""
    leaves: list[dict] = []
    ver: dict = {}

    def nm(n):
        if n & 0x80000000:
            o = base + (n & 0x7FFFFFFF)
            if o + 2 <= len(d):
                ln = struct.unpack_from("<H", d, o)[0]
                return d[o + 2:o + 2 + 2 * min(ln, 64)].decode("utf-16le", "replace")
            return "?"
        return n

    for tn, toff, tdir in _res_entries(d, base):
        if not tdir:
            continue
        tname = nm(tn)
        tlabel = _RES_TYPES.get(tname, str(tname)) if isinstance(tname, int) else "'%s'" % tname
        for nn_, noff, ndir in _res_entries(d, base + toff)[:32]:
            if not ndir:
                continue
            for _ln, loff, ldir in _res_entries(d, base + noff)[:4]:
                if ldir or base + loff + 16 > len(d):
                    continue
                rva, size, _cp, _r = struct.unpack_from("<IIII", d, base + loff)
                fo = rva2off(rva)
                if fo is None or fo >= len(d):
                    continue
                data = d[fo:fo + min(size, 1 << 20)]
                leaves.append({"type": tlabel, "name": str(nm(nn_)), "size": size, "ent": _entropy(data[:65536]), "mz": data[:2] == b"MZ", "off": fo})
                if tname == 16 and not ver:
                    txt = d[fo:fo + min(size, 16384)].decode("utf-16le", "ignore")
                    for k in _VER_KEYS:
                        m = re.search(k + r"\x00+([^\x00]{1,120})", txt)
                        if m:
                            ver[k] = m.group(1).strip()
                if len(leaves) >= 200:
                    return leaves, ver
    return leaves, ver


def _rich_header(d: bytes, pe_off: int):
    """Header 'Rich' (jejak alat build MSVC) di antara DOS stub dan header PE. Hash varian Iris: MD5 teks terang dari DanS sampai Rich."""
    end = d.find(b"Rich", 0x40, min(pe_off + 4, len(d)))
    if end == -1 or end + 8 > len(d):
        return None
    key = d[end + 4:end + 8]
    k = struct.unpack("<I", key)[0]
    pos = end - 4
    while pos >= 0x40:
        if struct.unpack_from("<I", d, pos)[0] ^ k == 0x536E6144:   # "DanS"
            clear = bytes(b ^ key[i % 4] for i, b in enumerate(d[pos:end]))
            return {"hash": hashlib.md5(clear).hexdigest(), "n": max(0, (end - pos - 16) // 8)}
        pos -= 4
    return None


def _signers(d: bytes, off: int, size: int) -> list[str]:
    """Nama umum (CN) yang terbaca dari blob sertifikat Authenticode. Keabsahan tanda tangan TIDAK diperiksa."""
    blob = d[off:off + min(size, 200000)]
    out: list[str] = []
    for m in re.finditer(rb"\x55\x04\x03([\x0c\x13\x14\x1e])", blob):
        p_ = m.end()
        if p_ >= len(blob) or blob[p_] & 0x80:
            continue
        raw = blob[p_ + 1:p_ + 1 + blob[p_]]
        t = raw.decode("utf-16be", "ignore") if m.group(1) == b"\x1e" else raw.decode("utf-8", "replace")
        if t and t not in out:
            out.append(t[:80])
    return out[:6]


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
            "md5": hashlib.md5(d[rptr:rptr + min(rsz, 16 * 1024 * 1024)]).hexdigest() if (rptr < len(d) and rsz) else "",
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

    delay_imports: dict[str, list[str]] = {}   # v94: delay-load import (dipakai untuk menyembunyikan API dari tabel impor biasa)
    try:
        if len(dirs) > 13 and dirs[13][0]:
            off = rva2off(dirs[13][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 32 <= len(d) and n < 40:
                _at, name_rva, _h, _iat, int_rva = struct.unpack_from("<IIIII", d, off)
                if not (name_rva or int_rva):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns = []
                th = rva2off(int_rva)
                k = 0
                while th is not None and th + step <= len(d) and k < 400:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(cstr((rva2off(v & 0x7FFFFFFF) or 0) + 2))
                    th += step
                    k += 1
                delay_imports[dll or "?"] = fns
                off += 32
                n += 1
    except (struct.error, IndexError):
        pass

    imph, ord_imp = "", 0
    try:
        parts = []
        for dll, fns in imports.items():
            base = dll.rsplit(".", 1)[0] if dll.rsplit(".", 1)[-1] in ("dll", "ocx", "sys") else dll
            for fn in fns:
                if fn.startswith("#"):
                    ord_imp += 1
                    fn = "ord" + fn[1:]
                parts.append("%s.%s" % (base, fn.lower()))
        if parts:
            imph = hashlib.md5(",".join(parts).encode()).hexdigest()
    except Exception:
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

    res: list[dict] = []
    ver: dict = {}
    try:
        if len(dirs) > 2 and dirs[2][0]:
            res, ver = _parse_resources(d, rva2off(dirs[2][0]), rva2off)
    except (struct.error, IndexError, ValueError, OverflowError):
        pass
    rich = None
    try:
        rich = _rich_header(d, pe_off)
    except (struct.error, IndexError, ValueError):
        pass
    signers: list[str] = []
    if len(dirs) > 4 and dirs[4][0] and dirs[4][1]:
        try:
            signers = _signers(d, dirs[4][0], dirs[4][1])
        except Exception:
            pass
    entry_sec = ""
    for s_ in secs:
        if s_["va"] <= entry < s_["va"] + max(s_["vsize"], s_["rsize"]):
            entry_sec = s_["name"]
            break
    cert = dirs[4] if len(dirs) > 4 else (0, 0)
    last_raw = max([s["rptr"] + s["rsize"] for s in secs] or [0])
    overlay = max(0, file_size - last_raw) if last_raw else 0
    if cert[0] and cert[1] and cert[0] >= last_raw:   # v94: blob Authenticode ada di akhir file; bukan overlay
        overlay = max(0, overlay - cert[1])
        if overlay < 8:
            overlay = 0
    try:
        stamp = _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "0"
    except (OverflowError, OSError, ValueError):
        stamp = "tidak valid"
    return {
        "arch": _MACHINE.get(machine, hex(machine)), "bits": 64 if is64 else 32,
        "dll": bool(chars & 0x2000), "subsys": _SUBSYS.get(subsys, str(subsys)),
        "stamp": stamp, "ts": ts, "entry": entry, "entry_sec": entry_sec, "imphash": imph, "ord_imports": ord_imp,
        "tls": bool(len(dirs) > 9 and dirs[9][0]), "delay": bool(len(dirs) > 13 and dirs[13][0]),
        "res": res, "ver": ver, "rich": rich, "signers": signers,
        "aslr": bool(dllch & 0x40), "dep": bool(dllch & 0x100), "cfg": bool(dllch & 0x4000),
        "dotnet": len(dirs) > 14 and dirs[14][0] != 0 and dirs[14][1] != 0,
        "signed": cert[0] != 0 and cert[1] != 0, "overlay": overlay, "last_raw": last_raw, "delay_imports": delay_imports,
        "sections": secs, "imports": imports, "exports": exports,
    }


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
                 "sections": [], "stripped": None, "interp": "", "wx": [], "exec_stack": False, "nsec": 0, "nseg": 0}
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
            for nm, st, fl, off, sz in hdrs:
                e = strtab.find(b"\0", nm)
                name = strtab[nm:(len(strtab) if e == -1 else e)].decode("latin-1", "replace") if nm < len(strtab) else ""
                raw = d[off:off + min(sz, SEC_ENT_SAMPLE)] if st != 8 and off < len(d) else b""
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


def _parse_zip(path: Path) -> dict | None:
    if not zipfile.is_zipfile(path):
        return None
    out: dict = {"names": [], "n": 0, "unc": 0, "kind": "ZIP", "warn": [], "perms": [], "dex": 0, "nested": [], "ext_rels": [], "_blob": b""}
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
                out["perms"] = sorted(perms)[:60]
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
        out["nested"] = [n for n in names if n.lower().endswith((".exe", ".dll", ".jar", ".apk", ".so", ".dex", ".bat", ".ps1", ".vbs", ".js", ".scr", ".sh", ".hta", ".lnk"))][:25]
        out["nested"] += [n for n in names if "/embeddings/" in n.lower() and n not in out["nested"]][:10]

        # relasi eksternal OOXML (template injection / konten jarak jauh)
        for i in infos:
            if i.filename.lower().endswith(".rels") and i.file_size < 400000 and not i.flag_bits & 1:
                try:
                    for m in _REL_TARGET.findall(z.read(i)[:200000]):
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
                data = z.read(i)[:min(12 * 1024 * 1024, budget)]
            except Exception:
                continue
            budget -= len(data)
            chunks.append(data)
        out["_blob"] = b"\n".join(chunks)
    return out


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
    "persistensi": ["RegSetValueEx", "RegCreateKeyEx", "CreateService", "OpenSCManager", "schtasks", "CurrentVersion\\Run", "StartupInfo"],
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
    ("PyInstaller", [b"pyinstaller", b"_meipass", b"pyi-runtime", b"pyiboot"], "ekstrak arsip PyInstaller (pyinstxtractor), lalu dekompilasi .pyc"),
    ("Nuitka", [b"nuitka"], "Python dikompilasi ke C: andalkan string, modul, dan analisis native"),
    ("Go", [b"go build id", b"go.buildid", b"runtime.gopanic", b"\xff go buildinf:"], "biner Go: pulihkan nama fungsi dari pclntab (GoReSym / Ghidra)"),
    ("Rust", [b"/rustc/", b"rust_panic", b"core::panicking"], "biner Rust: nama fungsi ter-mangle, cari path crate di string"),
    ("AutoIt", [b"autoit v3", b"au3!ea06", b"this is a compiled autoit"], "skrip AutoIt terkompilasi: ekstrak dengan alat dekompilasi AutoIt"),
    ("NSIS installer", [b"nullsoft install system", b"nsis error"], "installer NSIS: ekstrak dengan 7-Zip, baca skrip .nsi"),
    ("Inno Setup", [b"inno setup setup data"], "installer Inno Setup: ekstrak dengan innoextract"),
    ("UPX", [b"upx!"], "kemasan UPX: unpack dengan `upx -d` (file tidak perlu dijalankan)"),
    ("Electron / asar", [b"electron.asar", b"app.asar", b"electron/js2c"], "aplikasi Electron: ekstrak app.asar, baca JavaScript"),
    ("Obfuscator .NET", [b"confuserex", b"eazfuscator", b"smartassembly", b".net reactor", b"dotfuscator"], "kode .NET diobfuskasi: deobfuskasi dulu (de4dot) sebelum dekompilasi"),
    ("Delphi / Borland", [b"borland", b"embarcadero"], "biner Delphi: pakai IDR / Ghidra dengan signature Delphi"),
    ("Visual Basic 6", [b"msvbvm60"], "VB6: analisis P-Code atau native dengan decompiler VB"),
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
_PACKERS = ("upx0", "upx1", ".upx", ".themida", ".vmp0", ".vmp1", ".aspack", ".adata", ".petite", ".nsp0", ".mpress1", "mpress", ".enigma1", ".winlice", ".boom", ".vmp2", "pec1", "pec2", ".packed", "upx2", ".yp", ".perplex", ".rmnet", ".kkrunchy")


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
    for m in _B64.findall(blob)[:60]:
        try:
            raw = base64.b64decode(m + "=" * (-len(m) % 4))
        except Exception:
            continue
        if len(raw) < 24:
            continue
        if raw[:2] == b"MZ":
            out.append(["PE/MZ", "executable tertanam dalam base64 (%s)" % _human(len(raw))])
        elif raw[:4] == b"\x7fELF":
            out.append(["ELF", "executable ELF tertanam dalam base64 (%s)" % _human(len(raw))])
        elif raw[:2] == b"PK":
            out.append(["ZIP", "arsip zip tertanam dalam base64 (%s)" % _human(len(raw))])
        elif raw[:2] == b"\x1f\x8b":
            out.append(["GZIP", "data gzip tertanam dalam base64 (%s)" % _human(len(raw))])
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


def _entropy_regions(d: bytes) -> list[tuple[int, int]]:
    """Rentang berentropi tinggi (>7,2) dalam blok; membantu menemukan payload terenkripsi / data kemasan."""
    d = d[: 16 * 1024 * 1024]
    if len(d) < 32768:
        return []
    bs = max(65536, len(d) // 64)
    regs: list[list[int]] = []
    for off in range(0, len(d), bs):
        blk = d[off:off + bs]
        if len(blk) >= 4096 and _entropy(blk) > 7.2:
            end = off + len(blk)
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

    ind, caps = rep["ind"], rep["ind"]["caps"]
    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    for cap, n, txt in (("injeksi / manipulasi proses", 3, "API injeksi proses"), ("pencurian kredensial / dompet", 3, "string pencurian kredensial / dompet"),
                        ("penambang kripto", 3, "string penambang kripto"), ("penghapus jejak / perusak pemulihan", 3, "perintah penghapus salinan bayangan / log"),
                        ("bypass keamanan", 2, "string bypass AMSI / antivirus"), ("PowerShell berbahaya / obfuskasi", 2, "pola PowerShell terenkode / unduh"),
                        ("penyadap input / layar", 2, "API penyadap papan ketik / layar")):
        if cap in caps:
            add(n, txt)
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
    if ind["secrets"]:
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
        elif any(x["ent"] > 7.2 and x["size"] > 16384 for x in pe.get("res", [])):
            add(1, "resource besar berentropi tinggi")
        if pe["ts"] > __import__("time").time() + 86400:
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
    level = "TINGGI" if pts >= 7 else "SEDANG" if pts >= 4 else "RENDAH" if pts >= 1 else "TANPA TANDA"
    return pts, level, why


def _df(x: str, on: bool) -> str:
    """defang: hxxp dan [.] supaya IOC tidak bisa terklik tak sengaja."""
    if not on:
        return x
    return x.replace("http", "hxxp").replace("ftp://", "fxp://").replace(".", "[.]").replace("@", "[@]")


def _indicators(strs: list[str], api_names: set[str]) -> dict:
    # v94: string sangat panjang dipotong 1500 karakter untuk regex lain (cegah ReDoS dari sampel buatan); base64 memakai blob penuh
    full = "\n".join(strs)[:24 * 1024 * 1024]
    blob = "\n".join(s[:1500] for s in strs)[:16 * 1024 * 1024]
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
        "secrets": secrets, "pem": bool(_PEM.search(blob)),
        "b64": len(_B64.findall(full)), "b64d": _decode_b64(full), "pdb": _uniq(_PDB.findall(blob), 3),
        "caps": caps, "n_strings": len(strs),
    }


# ---------------------------------------------------------------------------
# Utama
# ---------------------------------------------------------------------------


def _clean(s: str) -> str:
    """v94: buang karakter kontrol dan pengecoh arah teks (RLO dll.) dari keluaran; string dari sampel tidak dipercaya."""
    return _CTRL_RE.sub("?", s)


_CTRL_RE = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")


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
        for fns_ in (pe.get("delay_imports") or {}).values():
            api_names.update(fns_)
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
    elif head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        kind = "OLE2 (dokumen Office lama / MSI)"
    elif head[:5] == b"{\\rtf":
        kind = "RTF"
    elif head[:4] == b"L\0\0\0" and d[4:20] == b"\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46":
        kind = "Shortcut Windows (.lnk)"
    else:
        txt = sum(1 for b in d[:4096] if 9 <= b <= 13 or 32 <= b <= 126)
        kind = "teks / skrip" if d[:4096] and txt / len(d[:4096]) > 0.95 else "biner tak dikenal (tanpa magic number umum)"
    rep["kind"] = kind
    rep["pe"], rep["elf"], rep["zip"] = pe, elf, zp
    if elf:   # v94: ELF dulu tanpa impor sama sekali
        try:
            ei = _elf_imports(d)
        except Exception:
            ei = {"needed": [], "imports": [], "exports": []}
        elf["dyn"] = ei
        api_names.update(ei["imports"])
    rep["docs"] = None
    if pe is None and elf is None and zp is None:
        try:
            rep["docs"] = _parse_docs(d, kind)
        except Exception as e:
            rep["warn"].append("parser dokumen gagal: %s" % type(e).__name__)

    strs = _strings(d)
    if zp:
        blob = zp.pop("_blob", b"")
        if blob:
            strs += _strings(blob)
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

    # --- tambahan v92: struktur lanjutan, PE tertanam, penanda pembuat / pengemas, skor
    rep["emb"] = _embedded(d, bool(pe and not pe.get("broken"))) if not zp else {"plain": [], "xor": []}
    rep["overlay"], rep["checksum"], rep["crypto"] = None, None, []
    try:
        if pe and not pe.get("broken"):
            rep["overlay"] = _overlay_info(d, pe)
            rep["checksum"] = _pe_checksum_check(d, size)
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
    for _n, t_ in ((rep.get("docs") or {}).get("score") or [])[:6]:
        w.append("dokumen: " + t_)
    rep["regions"] = _entropy_regions(d) if not zp else []
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
    pts, level, why = _score(rep)
    rep["score"], rep["level"], rep["why"] = pts, level, why
    return rep


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
    if "score" in rep:
        a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis; installer / alat sah juga bisa bernilai tinggi." % (rep["score"], rep["level"]))
        for x in rep["why"][: (4 if compact else 20)]:
            a("   * " + x)
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
        a("Bagian : " + "; ".join("%s %s ent %.1f raw %s" % (s["name"] or "?", s["flags"], s["ent"], _human(s["rsize"])) for s in secs))
        if not compact:
            a("MD5 bagian: " + "; ".join("%s=%s" % (s["name"] or "?", s["md5"]) for s in secs if s.get("md5")))
        ver = pe.get("ver") or {}
        if ver:
            orig = ver.get("OriginalFilename", "")
            fn_ = re.sub(r"^[0-9a-f]{6}_", "", rep["name"].lower())   # buang awalan hash salinan rea-input
            a("Versi  : " + "; ".join("%s=%s" % (k, v) for k, v in ver.items()) + (" | nama file BERBEDA dari OriginalFilename" if orig and orig.lower() != fn_ else ""))
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
        for cap, hit in ind["caps"].items():
            a("   - %s: %s" % (cap, ", ".join(hit)))
        if not compact:
            tt = [ATTACK[c] for c in ind["caps"] if c in ATTACK]
            if tt:
                a("Pemetaan ATT&CK (perkiraan dari petunjuk di atas, BUKAN bukti perilaku): " + "; ".join(tt))
    lim = 5 if compact else 25
    for label, key in (("URL", "urls"), ("Kandidat IP (bisa nomor versi)", "ips"), ("Email", "emails"), ("Kunci registry", "reg"), ("Path Windows", "paths")):
        if ind[key]:
            a("%s (%d): %s" % (label, len(ind[key]), " | ".join(_df(x, defang) if key in ("urls", "ips", "emails") else x for x in ind[key][:lim])))
    if ind["secrets"]:
        a("Kandidat kredensial tertanam (disamarkan): " + ", ".join(ind["secrets"]))
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
        a("Wilayah berentropi tinggi (>7,2): " + ", ".join("0x%X-0x%X (%s)" % (x, y, _human(y - x)) for x, y in rep["regions"][:6]))
    a("String terbaca: %d" % ind["n_strings"])
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][: (6 if compact else 20)]:
            a("   ! " + x)
    a("Batas triase: hasil di atas murni pembacaan statis; tanpa dekompilasi, tanpa emulasi, tanpa jaringan, file tidak dijalankan.")
    return "\n".join(L)


def render(rep: dict, compact: bool = False, defang: bool = True, max_chars: int = 0) -> str:
    """Seperti dulu, plus anggaran panjang: bila melebihi max_chars, buang rincian impor per-DLL dulu, lalu pakai mode ringkas,
    terakhir pangkas bagian tengah. Skor dan PERHATIAN tidak ikut terbuang lebih dulu."""
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
    return txt[:head] + "\n[...dipangkas supaya muat...]\n" + txt[-(max_chars - head - 40):]


def triage_text(path, compact: bool = False, defang: bool = True, max_chars: int = 0) -> str:
    try:
        return render(triage(path), compact=compact, defang=defang, max_chars=max_chars)
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
    with open(p, "rb") as f:
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
        for m in _B64.findall("\n".join(_strings(d)))[:60]:
            raw = base64.b64decode(m + "=" * (-len(m) % 4))
            if raw[:2] == b"MZ" and len(raw) >= 256:
                cands.append(("PE base64", raw[:_pe_extent(raw)]))
    except Exception:
        pass
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
            with open(fp, "xb") as f:
                f.write(blob)
        except FileExistsError:
            pass
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
        L.append("   - %s | %s | sha256 %s | %s | skor %s (%s)\n     %s" % (it["source"], _human(it["size"]), it["sha256"][:16] + "...",
                 it.get("kind", "?"), it.get("score", "?"), it.get("level", "?"), it["file"]))
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


def triage_dir(path, max_files: int = 300, per_file_mb: float = 200.0, time_budget: float = 90.0) -> dict:
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
            r = triage(str(fp))
        except Exception as e:
            skipped.append("%s (%s)" % (rel, type(e).__name__))
            continue
        items.append({"rel": rel, "size": r["size"], "kind": r["kind"], "score": r["score"], "level": r["level"], "sha256": r["sha256"],
                      "why": r["why"][:3], "urls": r["ind"]["urls"][:5], "ips": r["ind"]["ips"][:5]})
    by_hash: dict[str, list[str]] = {}
    for it in items:
        by_hash.setdefault(it["sha256"], []).append(it["rel"])
    return {"root": str(root), "n_total": total_n, "total_size": total_sz, "n_done": len(items), "items": items, "skipped": skipped[:10],
            "dups": [v for v in by_hash.values() if len(v) > 1][:10], "elapsed": time.monotonic() - t0}


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
    if len(cand) < 2:
        return "// Tidak cukup string unik untuk draf YARA yang layak (%d). Jangan membuat aturan dari satu string umum." % len(cand)
    esc = lambda x: x.replace("\\", "\\\\").replace('"', '\\"')
    L = ["rule %s {" % rid, "  meta:",
         '    description = "DRAF otomatis Iris rea_triage v93; WAJIB diuji terhadap file sah sebelum dipakai"',
         '    sha256 = "%s"' % rep["sha256"]]
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append('    // imphash varian Iris: %s' % pe["imphash"])
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
    if pe and not pe.get("broken"):
        out["imphash"] = pe.get("imphash", "")
        out["rich_hash"] = (pe.get("rich") or {}).get("hash", "")
        out["section_md5"] = {x["name"] or "?": x["md5"] for x in pe["sections"] if x.get("md5")}
        out["version_info"] = pe.get("ver", {})
    return out


def triage_json(path, ioc_only: bool = False) -> str:
    try:
        rep = triage(path)
        return json.dumps(iocs(rep) if ioc_only else rep, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": "%s: %s" % (type(e).__name__, str(e)[:120])}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# v95: jembatan ke mesin ekstraksi (rea_extract.py). Impor malas: triase tetap jalan walau modul itu tidak ada.
# ---------------------------------------------------------------------------


def _extract_mod():
    try:
        import rea_extract
        return rea_extract
    except ImportError:
        return None


def container_text(path, max_chars: int = 0) -> str:
    """Daftar isi container (ZIP/TAR/GZIP/ISO/PSP ISO), hanya-baca. Gagal -> pesan, tidak melempar."""
    mod = _extract_mod()
    if mod is None:
        return "Mesin ekstraksi (rea_extract.py) tidak ditemukan di folder yang sama; fitur isi container tidak tersedia."
    try:
        return mod.describe_container_text(path, max_chars=max_chars)
    except Exception as e:
        return "CONTAINER gagal dibaca (%s: %s)." % (type(e).__name__, str(e)[:120])


def container_extract(path, outdir, pattern=None, scan: bool = False) -> dict:
    """Ekstraksi selektif ke workspace outdir (extracted/, manifests/, logs/). Mengembalikan manifest (dict)."""
    mod = _extract_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_extract.py tidak ditemukan"}
    r = mod.open_container(path)
    if r.get("status") != "success":
        return r
    try:
        return mod.extract_selected(r["container_id"], {"pattern": pattern} if pattern else None, outdir, scan=scan)
    finally:
        mod.close_container(r["container_id"])


def hex_text(path, offset=0, length: int = 256, encoding: str = "ascii") -> str:
    """Tampilan hex hanya-baca (v96, rea_binary.py). Gagal -> pesan, tidak melempar."""
    try:
        import rea_binary
    except ImportError:
        return "Binary Workbench (rea_binary.py) tidak ditemukan di folder yang sama."
    r = rea_binary.hex_view(path, offset, length, encoding=encoding)
    return r["text"] if r.get("status") == "success" else "HEX gagal: %s" % r.get("message", r.get("code"))


def compare_text(path_a, path_b) -> str:
    """Ringkasan perbandingan dua berkas / dua folder (v96)."""
    try:
        import rea_binary
    except ImportError:
        return "Binary Workbench (rea_binary.py) tidak ditemukan di folder yang sama."
    pa, pb = Path(path_a), Path(path_b)
    r = rea_binary.compare_dirs(pa, pb) if pa.is_dir() else rea_binary.compare_files(pa, pb)
    if r.get("status") != "success":
        return "COMPARE gagal: %s" % r.get("message", r.get("code"))
    if "changed_ranges" in r:
        L = ["BANDINGKAN: %s vs %s" % (r["a"], r["b"]), "Ukuran : %s vs %s (selisih %+d)" % (_human(r["size_a"]), _human(r["size_b"]), r["size_delta"]),
             "Identik: %s" % ("ya" if r["identical"] else "tidak"), "SHA-256: %s... | %s..." % (r["sha256_a"][:16], r["sha256_b"][:16])]
        if not r["identical"]:
            L.append("Byte berbeda: %d dalam %d rentang%s; perbedaan pertama di offset %s" % (r["differing_bytes"], len(r["changed_ranges"]), " (dipotong)" if r["truncated"] else "", r["first_diff"]))
            L += ["   offset 0x%X panjang %d" % (x["offset"], x["length"]) for x in r["changed_ranges"][:10]]
            if r["extra_bytes"]:
                L.append("Sisa %d byte hanya ada di berkas %s" % (r["extra_bytes"]["length"], r["extra_bytes"]["in"]))
        return "\n".join(L)
    return "BANDINGKAN FOLDER: +%d baru, -%d hilang, ~%d berubah, %d sama" % (len(r["added"]), len(r["removed"]), len(r["changed"]), r["unchanged_count"])


if __name__ == "__main__":   # uji manual: python rea_triage.py <file|folder> [--compact] [--json] [--ioc] [--raw] [--yara] [--carve DIR]
    import sys
    argv = sys.argv[1:]
    cdir = None
    if "--hex" in argv:      # --hex FILE [OFFSET [LENGTH]]
        t = argv[argv.index("--hex") + 1:]
        print(hex_text(t[0], t[1] if len(t) > 1 else 0, int(t[2]) if len(t) > 2 else 256) if t else "pemakaian: --hex FILE [OFFSET [LENGTH]]")
        raise SystemExit(0)
    if "--compare" in argv:  # --compare A B
        t = argv[argv.index("--compare") + 1:]
        print(compare_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --compare A B")
        raise SystemExit(0)
    if "--list" in argv:
        print(container_text(next((x for x in argv if not x.startswith("--")), "")))
        raise SystemExit(0)
    if "--extract" in argv:
        k = argv.index("--extract")
        _out = argv[k + 1] if k + 1 < len(argv) else "rea_workspace"
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        _m = container_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, scan="--scan" in argv)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s | manifest: %s" % (_m.get("status"), _m.get("entries_extracted"), _m.get("entries_skipped"), _m.get("entries_failed"), _m.get("manifest_path")))
        raise SystemExit(0 if _m.get("status") == "success" else 1)
    if "--carve" in argv:
        k = argv.index("--carve")
        cdir = argv[k + 1] if k + 1 < len(argv) else None
        argv = argv[:k] + argv[k + 2:]
    args = [x for x in argv if not x.startswith("--")]
    flags = {x for x in argv if x.startswith("--")}
    if not args:
        print("pemakaian: python rea_triage.py <file|folder> [--compact] [--json] [--ioc] [--raw (tanpa defang)] [--yara] [--carve DIR] | --hex FILE [OFFSET [LENGTH]] | --compare A B | --list <container> | --extract OUTDIR <container> [pola] [--scan]")
    elif Path(args[0]).is_dir():
        print(triage_dir_text(args[0], defang="--raw" not in flags))
    elif "--json" in flags or "--ioc" in flags:
        print(triage_json(args[0], ioc_only="--ioc" in flags))
    elif "--yara" in flags:
        print(yara_draft(triage(args[0])))
    else:
        full, _note = triage_bundle(args[0], carve_dir=cdir) if cdir else (None, None)
        print(full if full is not None else triage_text(args[0], compact="--compact" in flags, defang="--raw" not in flags))
