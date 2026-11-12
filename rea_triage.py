"""rea_triage.py - triase statis lokal untuk perintah /rea (Iris v97, kumulatif dengan v96, v95, v94, v93, v92, v91).  by: KangJiho

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

v97 (lebih bertenaga; API lama tidak berubah, semua tambahan bersifat aditif):
    - Mach-O penuh (tipis + universal): arsitektur, platform, load command, dylib / RPATH, segmen + entropi, tanda tangan, enkripsi, UUID,
      simbol impor / ekspor (ikut dipetakan ke kemampuan + ATT&CK);
    - metadata .NET: versi runtime, stream, nama dari #Strings, string pengguna #US (masuk ke IOC), kemampuan dari nama P/Invoke / kripto,
      dugaan obfuskasi;
    - CTPH (hash fuzzy gaya ssdeep): ctph(data), ctph_compare(x, y), similarity(a, b), similar_text(a, b);
    - perburuan satu-byte XOR / ADD / ROL untuk URL, stub DOS, dan nama API tersembunyi;
    - detail kemasan: PyInstaller (versi Python + skrip masuk dari TOC), UPX, NSIS, Inno Setup, Go, Rust, AutoIt, SFX 7-Zip, PyArmor;
    - triage_dir mengelompokkan keluarga sampel (imphash, rich header, UUID Mach-O, opsional CTPH dengan fuzzy=True);
    - triage_md(path): laporan Markdown; rea_api(request): satu pintu JSON untuk Iris / Hermes (opsi pembatas path: env REA_ROOTS).

v96.1 (pengerasan): berkas dibuka sekali dengan fstat (tolak FIFO / perangkat / folder, tanpa TOCTOU); batas kerja entropi / MD5
    per bagian (header bagian tumpang-tindih tidak bisa memakan CPU); ZIP dibaca dengan batas dekompresi dan jumlah entri;
    keluaran dibersihkan dari baris baru / pemisah baris (anti injeksi laporan); perbaikan nama impor PE bila RVA tak terpetakan.
"""
from __future__ import annotations

import base64
import collections
import os
import time
import datetime as _dt
import hashlib
import itertools
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
ENT_BUDGET = 32 * 1024 * 1024        # total byte yang boleh dihitung entropinya lewat semua bagian PE / ELF
MD5_BUDGET = 256 * 1024 * 1024       # total byte yang boleh di-MD5 lewat semua bagian PE
MAX_ZIP_ENTRIES = 100_000            # lebih dari ini: arsip tidak diurai (cegah kehabisan memori)

# ---------------------------------------------------------------------------
# Dasar
# ---------------------------------------------------------------------------


def _entropy(b: bytes) -> float:
    if not b:
        return 0.0
    n = len(b)
    c = collections.Counter(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def _md5(data=b""):
    """MD5 untuk sidik jari (bukan keamanan): tetap jalan di Python mode FIPS."""
    try:
        return hashlib.md5(data, usedforsecurity=False)
    except TypeError:   # Python < 3.9
        return hashlib.md5(data)


def _open_regular(path, follow: bool = True):
    """Buka berkas biasa dan kembalikan (file, ukuran) dari handle yang SAMA (tanpa celah TOCTOU).
    Menolak FIFO / perangkat (mis. /dev/zero: hash tak berujung) / folder. follow=False menolak symlink di POSIX."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    if not follow:
        flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(os.fspath(path), flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("bukan berkas biasa (FIFO / perangkat / folder): %s" % os.fspath(path))
        f = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    return f, st.st_size


def _hash_file(src, size: int | None = None) -> dict:
    """src: path ATAU file object biner. Membaca paling banyak `size` byte supaya hash konsisten dengan ukuran yang dilaporkan."""
    own = not hasattr(src, "read")
    if own:
        f, fsz = _open_regular(src)
        size = fsz if size is None else size
    else:
        f = src
    h256, h1, hmd = hashlib.sha256(), hashlib.sha1(), _md5()
    try:
        left = float("inf") if size is None else size
        while left > 0:
            chunk = f.read(int(min(1024 * 1024, left)))
            if not chunk:
                break
            left -= len(chunk)
            h256.update(chunk)
            h1.update(chunk)
            hmd.update(chunk)
    finally:
        if own:
            f.close()
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
            return {"hash": _md5(clear).hexdigest(), "n": max(0, (end - pos - 16) // 8)}
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
    if o + (112 if is64 else 96) > len(d):
        return {"broken": "optional header terpotong"}
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
    ent_left, md5_left, budget_hit = ENT_BUDGET, MD5_BUDGET, False
    for i in range(min(nsec, 96)):
        p = so + 40 * i
        if p + 40 > len(d):
            break
        nm, vsz, va, rsz, rptr, _r, _l, _nr, _nl, ch = struct.unpack_from("<8sIIIIIIHHI", d, p)
        name = nm.rstrip(b"\0").decode("latin-1", "replace")
        raw = d[rptr:rptr + min(rsz, SEC_ENT_SAMPLE)] if rptr < len(d) else b""
        if len(raw) > ent_left:       # header bagian tumpang-tindih / dibuat-buat: jangan biarkan CPU habis
            raw, budget_hit = b"", True
        ent_left -= len(raw)
        md5 = ""
        if rptr < len(d) and rsz:
            n_md = min(rsz, 16 * 1024 * 1024, len(d) - rptr)
            if n_md <= md5_left:
                md5_left -= n_md
                md5 = _md5(memoryview(d)[rptr:rptr + n_md]).hexdigest()
            else:
                budget_hit = True
        secs.append({
            "name": name, "va": va, "vsize": vsz, "rptr": rptr, "rsize": rsz,
            "md5": md5,
            "flags": ("R" if ch & 0x40000000 else "-") + ("W" if ch & 0x80000000 else "-") + ("X" if ch & 0x20000000 else "-"),
            "ent": _entropy(raw) if raw else 0.0,
        })

    def rva2off(rva: int) -> int | None:
        for s in secs:
            rel = rva - s["va"]
            if 0 <= rel < max(s["vsize"], s["rsize"]):
                return (rel + s["rptr"]) if rel < s["rsize"] else None   # ekor virtual (nol) tidak ada di berkas
        if secs and rva < min(s["va"] for s in secs):
            return rva
        return None

    def cstr(off: int, lim: int = 128) -> str:
        if off is None or off < 0 or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    def hint_name(rva: int) -> str:
        fo = rva2off(rva)
        return (cstr(fo + 2) if fo is not None else "") or "?"

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
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                imports.setdefault(dll or "?", []).extend(fns)
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
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                delay_imports.setdefault(dll or "?", []).extend(fns)
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
            imph = _md5(",".join(parts).encode()).hexdigest()
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
                    nm_ = cstr(rva2off(struct.unpack_from("<I", d, no + 4 * i)[0]))
                    if nm_:
                        exports.append(nm_)
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
        "sections": secs, "imports": imports, "exports": exports, "budget_hit": budget_hit,
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


def _zip_entry_count(f, size: int) -> int:
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
        if (total == 0xFFFF or cd_size == 0xFFFFFFFF) and i >= 20 and buf[i - 20:i - 16] == b"PK\x06\x07":
            z64 = struct.unpack_from("<Q", buf, i - 12)[0]
            if z64 + 56 <= size:
                f.seek(z64)
                rec = f.read(56)
                if len(rec) == 56 and rec[:4] == b"PK\x06\x06":
                    total = struct.unpack_from("<Q", rec, 32)[0]
                    cd_size = struct.unpack_from("<Q", rec, 40)[0]
        return max(total, 0 if cd_size == 0xFFFFFFFF else cd_size // 46)   # 46 = ukuran minimum satu entri direktori pusat
    except (OSError, struct.error):
        return -1


def _zread(z, member, limit: int) -> bytes:
    """Baca paling banyak `limit` byte HASIL dekompresi. z.read() tanpa batas rentan zip bomb (1 MB terkompres bisa jadi GB)."""
    with z.open(member) as m:
        return m.read(max(0, limit))


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
    cnt = _zip_entry_count(src, size)
    if cnt > MAX_ZIP_ENTRIES:
        out["n"] = cnt
        out["warn"].append("jumlah entri arsip tidak wajar (~%d): tidak diurai (cegah kehabisan memori)" % cnt)
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
        if "androidmanifest.xml" in low:
            out["kind"] = "APK (Android)"
            out["dex"] = sum(1 for n in low if re.fullmatch(r"classes\d*\.dex", n))
            try:
                mf = _zread(z, names[low.index("androidmanifest.xml")], 400000)
                perms = {m.decode() for m in _PERM_RE.findall(mf)}
                perms |= {m.decode("utf-16le", "ignore") for m in _PERM_RE16.findall(mf)}
                out["perms"] = sorted(perms)[:60]
            except Exception:
                pass
        elif "meta-inf/manifest.mf" in low:
            out["kind"] = "JAR/WAR (Java)"
            try:
                mf = _zread(z, names[low.index("meta-inf/manifest.mf")], 4096).decode("utf-8", "replace")
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
    _score_v97(rep, add)
    level = "TINGGI" if pts >= 7 else "SEDANG" if pts >= 4 else "RENDAH" if pts >= 1 else "TANPA TANDA"
    return pts, level, why


def _df(x: str, on: bool) -> str:
    """defang: hxxp dan [.] supaya IOC tidak bisa terklik tak sengaja."""
    if not on:
        return x
    return x.replace("http", "hxxp").replace("ftp://", "fxp://").replace("ws://", "wxs://").replace("wss://", "wxss://").replace(".", "[.]").replace("@", "[@]")


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
    api_low = [a.lower() for a in api_names]
    for cap, keys in CAPS.items():
        hit = []
        for k in keys:
            kl = k.lower()
            if any(kl in a for a in api_low) or (len(k) > 7 and kl in low_blob):
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
        "b64": sum(1 for _ in _B64.finditer(full)), "b64d": _decode_b64(full), "pdb": _uniq(_PDB.findall(blob), 3),
        "caps": caps, "n_strings": len(strs),
    }


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


def triage(path, follow_links: bool = True, fuzzy: bool = True) -> dict:
    p = Path(path)
    f, size = _open_regular(p, follow_links)
    with f:
        return _triage_open(p, f, size, fuzzy)


def _triage_open(p: Path, f, size: int, fuzzy: bool = True) -> dict:
    rep: dict = {"name": p.name, "size": size, "warn": []}
    rep.update(_hash_file(f, size))
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
    strs = _strings(d)
    if rep["dotnet"]:
        strs += rep["dotnet"]["us"]
    if zp:
        blob = zp.pop("_blob", b"")
        if blob:
            strs += _strings(blob)
    rep["ind"] = _indicators(strs, api_names)
    if rep["dotnet"]:
        for cap_, hit_ in _net_caps(rep["dotnet"]["names"]).items():
            rep["ind"]["caps"][cap_] = list(dict.fromkeys(rep["ind"]["caps"].get(cap_, []) + hit_))[:8]

    w = rep["warn"]
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
    _v97_enrich(d, size, rep, fuzzy)
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
    _render_v97(rep, a, compact, defang)
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
    tail = max(0, max_chars - head - 40)
    return txt[:head] + "\n[...dipangkas supaya muat...]\n" + (txt[-tail:] if tail else "")


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
        for mm in itertools.islice(_B64.finditer("\n".join(_strings(d))), 60):
            m = mm.group(0)
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
            try:
                if hashlib.sha256(fp.read_bytes()).hexdigest() != sha:   # berkas lama bernama sama tapi isi lain: jangan klaim
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
                      "macho_uuid": (r.get("macho") or {}).get("uuid", ""), "ctph": r.get("ctph", "")})
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


def triage_json(path, ioc_only: bool = False) -> str:
    try:
        rep = triage(path)
        return json.dumps(iocs(rep) if ioc_only else rep, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": "%s: %s" % (type(e).__name__, str(e)[:120])}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# v97: Mach-O, metadata .NET, CTPH (hash fuzzy), perburuan XOR / ADD / ROL, detail kemasan, keluarga sampel,
#      laporan Markdown, dan API JSON untuk Iris / Hermes. Semuanya hanya-baca, pustaka standar, file tidak dijalankan.
# ---------------------------------------------------------------------------

VERSION = "97"
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
                  "exports": [], "nsyms": 0, "warn": [], "fat": []}
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
    return {"runtime": runtime, "streams": [(k, v[1]) for k, v in streams.items()], "ilonly": bool(cflags & 1), "strong": bool(cflags & 8),
            "entry_token": etok, "names": names, "us": us, "obf": obf, "n_names": len(names)}


def _net_caps(names: list[str]) -> dict[str, list[str]]:
    have = set(names)
    out = {cap: sorted(have & keys)[:6] for cap, keys in _NET_CAPS.items() if have & keys}
    if {"Assembly", "Load", "Invoke"} <= have:
        out.setdefault("muat kode dinamis", []).append("Assembly.Load + Invoke")
    return out


# ----------------------------- CTPH (hash fuzzy gaya ssdeep) ----------------

_B64C = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CTPH_SAMPLE = 1024 * 1024


def _spamsum(data: bytes, bs: int) -> tuple[str, str]:
    h1 = h2 = h3 = 0
    win = [0] * 7
    n = 0
    bh1 = bh2 = 0x28021967
    s1, s2 = [], []
    M = 0xFFFFFFFF
    b2 = bs * 2
    r = 0
    for c in data:
        bh1 = ((bh1 * 0x01000193) ^ c) & M
        bh2 = ((bh2 * 0x01000193) ^ c) & M
        h2 = (h2 - h1 + 7 * c) & M
        h1 = (h1 + c - win[n % 7]) & M
        win[n % 7] = c
        n += 1
        h3 = ((h3 << 5) ^ c) & M
        r = (h1 + h2 + h3) & M
        if r % bs == bs - 1 and len(s1) < 63:
            s1.append(_B64C[bh1 & 63])
            bh1 = 0x28021967
        if r % b2 == b2 - 1 and len(s2) < 31:
            s2.append(_B64C[bh2 & 63])
            bh2 = 0x28021967
    if r:
        s1.append(_B64C[bh1 & 63])
        s2.append(_B64C[bh2 & 63])
    return "".join(s1), "".join(s2)


def ctph(data: bytes) -> str:
    """Hash fuzzy (context-triggered piecewise hashing, algoritma spamsum). Format 'blok:digest1:digest2'.
    Dapat dibandingkan dengan ctph_compare(); bukan jaminan identik dengan keluaran ssdeep resmi."""
    n = len(data)
    if n < 64:
        return ""
    bs = 3
    while bs * 64 < n:
        bs *= 2
    while True:
        s1, s2 = _spamsum(data, bs)
        if bs > 3 and len(s1) < 32:
            bs //= 2
            continue
        return "%d:%s:%s" % (bs, s1, s2)


def _squeeze(s: str) -> str:
    return re.sub(r"(.)\1{3,}", r"\1\1\1", s)


def _ssd_one(a: str, b: str, bs: int) -> int:
    if len(a) < 7 or len(b) < 7:
        return 0
    if not any(a[i:i + 7] in b for i in range(len(a) - 6)):
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 2)))
        prev = cur
    score = prev[-1] * 64 // (len(a) + len(b))
    score = 100 - (100 * score // 64)
    if bs < 45:
        score = min(score, bs // 3 * min(len(a), len(b)))
    return max(0, min(100, score))


def ctph_compare(x: str, y: str) -> int:
    """Skor kemiripan 0-100 antara dua digest ctph(); 0 = tidak ada kemiripan berarti atau blok tak sebanding."""
    try:
        bx, ax1, ax2 = x.split(":", 2)
        by, ay1, ay2 = y.split(":", 2)
        bx, by = int(bx), int(by)
    except ValueError:
        return 0
    ax1, ax2, ay1, ay2 = _squeeze(ax1), _squeeze(ax2), _squeeze(ay1), _squeeze(ay2)
    if bx == by:
        if ax1 == ay1 and ax2 == ay2:
            return 100
        return max(_ssd_one(ax1, ay1, bx), _ssd_one(ax2, ay2, bx * 2))
    if bx == by * 2:
        return _ssd_one(ax1, ay2, bx)
    if by == bx * 2:
        return _ssd_one(ax2, ay1, by)
    return 0


def _read_sample(path, n: int = CTPH_SAMPLE) -> tuple[bytes, int]:
    f, size = _open_regular(path)
    with f:
        return f.read(n), size


def similarity(path_a, path_b) -> dict:
    """Bandingkan dua berkas: hash identik, skor CTPH, imphash, rich hash, irisan bagian PE (MD5), irisan string menarik."""
    da, sa = _read_sample(path_a)
    db, sb = _read_sample(path_b)
    ra, rb = triage(path_a, fuzzy=False), triage(path_b, fuzzy=False)
    ca, cb = ctph(da), ctph(db)
    out = {"a": Path(path_a).name, "b": Path(path_b).name, "size_a": sa, "size_b": sb, "identical": ra["sha256"] == rb["sha256"],
           "ctph_a": ca, "ctph_b": cb, "ctph_score": ctph_compare(ca, cb) if ca and cb else 0}
    pa, pb = ra.get("pe"), rb.get("pe")
    if pa and pb and not pa.get("broken") and not pb.get("broken"):
        out["imphash_same"] = bool(pa.get("imphash")) and pa.get("imphash") == pb.get("imphash")
        out["rich_same"] = bool((pa.get("rich") or {}).get("hash")) and (pa.get("rich") or {}).get("hash") == (pb.get("rich") or {}).get("hash")
        ma = {x["md5"] for x in pa["sections"] if x.get("md5")}
        mb = {x["md5"] for x in pb["sections"] if x.get("md5")}
        out["section_md5_shared"] = len(ma & mb)
        out["sections"] = (len(ma), len(mb))
    ua = set(ra["ind"]["urls"]) | set(ra["ind"]["ips"]) | set(ra["ind"]["pdb"])
    ub = set(rb["ind"]["urls"]) | set(rb["ind"]["ips"]) | set(rb["ind"]["pdb"])
    out["shared_iocs"] = sorted(ua & ub)[:10]
    verdict = "identik" if out["identical"] else ("sangat mirip (kemungkinan varian / keluarga sama)" if out["ctph_score"] >= 70 else
                                                   "ada kemiripan" if out["ctph_score"] >= 30 else "tidak mirip menurut CTPH")
    if not out["identical"] and (out.get("imphash_same") or out.get("rich_same") or out.get("section_md5_shared")) and out["ctph_score"] < 70:
        verdict += "; tetapi struktur PE sama (imphash / rich header / bagian), kemungkinan satu keluarga atau satu toolchain"
    out["verdict"] = verdict
    return out


def similar_text(path_a, path_b) -> str:
    try:
        r = similarity(path_a, path_b)
    except Exception as e:
        return "SIMILARITY gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L = ["KEMIRIPAN: %s vs %s" % (r["a"], r["b"]), "Ukuran : %s vs %s" % (_human(r["size_a"]), _human(r["size_b"])),
         "SHA-256 identik: %s" % ("ya" if r["identical"] else "tidak"), "CTPH   : skor %d/100 (sampel %s pertama)" % (r["ctph_score"], _human(CTPH_SAMPLE))]
    if "imphash_same" in r:
        L.append("PE     : imphash %s | rich header %s | bagian MD5 sama %d dari %d/%d" % ("sama" if r["imphash_same"] else "beda", "sama" if r["rich_same"] else "beda", r["section_md5_shared"], *r["sections"]))
    if r["shared_iocs"]:
        L.append("IOC bersama: " + " | ".join(_df(x, True) for x in r["shared_iocs"][:6]))
    L.append("Kesimpulan (petunjuk, bukan vonis): " + r["verdict"])
    return "\n".join(_clean(x) for x in L)


# ----------------------------- XOR / ADD / ROL ------------------------------

_XOR_WORDS = [b"This program cannot be run", b"https://", b"http://", b"kernel32", b"KERNEL32", b"cmd.exe", b"powershell", b"GetProcAddress", b"LoadLibrary",
              b"VirtualAlloc", b"WScript.Shell", b"/bin/sh", b"User-Agent", b"Mozilla/5.0"]
_XOR_URL = re.compile(rb"https?://[\x21-\x7e]{4,100}")
def _xor_table(op: str, key: int) -> bytes:
    if op == "XOR":
        return bytes(i ^ key for i in range(256))
    if op == "ADD":
        return bytes((i + key) & 255 for i in range(256))
    return bytes(((i << key) | (i >> (8 - key))) & 255 for i in range(256))   # ROL


def _xor_hunt(d: bytes, budget: float = 3.0) -> list[dict]:
    """Cari kata kunci (URL, stub DOS, nama API) yang baru muncul setelah dekode satu byte (XOR / ADD / ROL).
    XOR dan ADD dicari lewat selisih antar-byte (tidak bergantung pada kunci), jadi 255 kunci dicek sekali jalan, bukan satu per satu.
    Jendela: 2 MB pertama + 1 MB terakhir berkas."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []   # teks / skrip biasa: tidak ada gunanya
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    n = len(samp)
    words = [w for w in _XOR_WORDS if w not in samp]   # kata yang sudah polos di berkas tidak diburu
    t0 = time.monotonic()
    found: dict[tuple[str, int], set] = {}
    xd = (int.from_bytes(samp, "big") ^ int.from_bytes(samp[1:] + b"\0", "big")).to_bytes(n, "big")
    for w in words:
        pat = bytes(w[i] ^ w[i + 1] for i in range(len(w) - 1))
        pos, tries = xd.find(pat), 0
        while pos >= 0 and tries < 4:
            k = samp[pos] ^ w[0]
            if k and pos + len(w) <= n and bytes(b ^ k for b in samp[pos:pos + len(w)]) == w:
                found.setdefault(("XOR", k), set()).add(w)
            pos, tries = xd.find(pat, pos + 1), tries + 1
    del xd
    if time.monotonic() - t0 < budget:
        ad = bytes((b - a) & 255 for a, b in zip(samp, samp[1:]))
        for w in words:
            pat = bytes((w[i + 1] - w[i]) & 255 for i in range(len(w) - 1))
            pos, tries = ad.find(pat), 0
            while pos >= 0 and tries < 4:
                k = (w[0] - samp[pos]) & 255
                if k and pos + len(w) <= n and bytes((b + k) & 255 for b in samp[pos:pos + len(w)]) == w:
                    found.setdefault(("ADD", k), set()).add(w)
                pos, tries = ad.find(pat, pos + 1), tries + 1
        del ad
    for r in range(1, 8):
        if time.monotonic() - t0 > budget:
            break
        dec = samp.translate(_xor_table("ROL", r))
        for w in words:
            if w in dec:
                found.setdefault(("ROL", r), set()).add(w)
    res: list[dict] = []
    for (op, key), ws in found.items():
        urls = [u.decode("ascii", "replace") for u in _uniq(_XOR_URL.findall(samp.translate(_xor_table(op, key))), 3)] if any(w.startswith(b"http") for w in ws) else []
        res.append({"op": op, "key": key, "words": sorted(w.decode("ascii") for w in ws)[:4], "count": len(ws), "urls": urls})
    res.sort(key=lambda x: (-x["count"], x["op"] != "XOR", x["key"]))
    return res[:5]


# ----------------------------- detail kemasan / installer -------------------


def _pack_details(d: bytes, size: int) -> list[str]:
    out: list[str] = []
    head = d[: 16 * 1024 * 1024]
    k = head.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    if k >= 0 and k + 24 <= len(head):
        pkg, toc, tlen, pyv = struct.unpack_from(">IIII", head, k + 8)
        lib = head[k + 24:k + 88].split(b"\0")[0].decode("ascii", "ignore") if k + 88 <= len(head) else ""
        newer = "python" in lib.lower()
        pyver = ("%d.%d" % (pyv // 100, pyv % 100) if pyv >= 100 else "%d.%d" % (pyv // 10, pyv % 10)) if 20 <= pyv < 1000 else "?"
        line = "PyInstaller %s | Python %s%s | arsip %s" % ("2.1+" if newer else "2.0", pyver, " (%s)" % lib if lib else "", _human(pkg))
        if size == len(d) and 0 < tlen < 4 * 1024 * 1024:
            csz = 88 if newer else 24
            base = size - (pkg + (size - k - csz))
            p, stop = base + toc, base + toc + tlen
            kinds: collections.Counter = collections.Counter()
            scripts: list[str] = []
            while p + 18 <= min(stop, len(d)):
                elen = struct.unpack_from(">I", d, p)[0]
                if elen < 18 or p + elen > len(d):
                    break
                typ = d[p + 17:p + 18].decode("latin-1")
                nm = d[p + 18:p + elen].split(b"\0")[0].decode("utf-8", "replace")
                kinds[typ] += 1
                if typ == "s" and len(scripts) < 6:
                    scripts.append(nm)
                p += elen
            if kinds:
                line += " | %d entri" % sum(kinds.values())
            if scripts:
                line += " | skrip masuk: " + ", ".join(scripts)
        out.append(line)
    m = re.search(rb"\$Id: UPX (\d+\.\d+\w*) Copyright", head)
    if m:
        out.append("UPX %s (unpack: `upx -d`)" % m.group(1).decode("ascii"))
    i = head.find(b"\xef\xbe\xad\xdeNullsoftInst")
    if i >= 0:
        out.append("installer NSIS: header firstheader di offset 0x%X (ekstrak dengan 7-Zip)" % i)
    m = re.search(rb"Inno Setup Setup Data \(([0-9.]{3,12}[^)]{0,16})\)", head)
    if m:
        out.append("Inno Setup versi %s (ekstrak dengan innoextract)" % m.group(1).decode("ascii", "replace"))
    if head.find(b"Go build ID") >= 0 or head.find(b"runtime.gopanic") >= 0:
        m = re.search(rb"\x00(go1\.\d{1,2}(?:\.\d{1,2})?)\x00?", head)
        out.append("Go%s (pulihkan nama fungsi dari pclntab)" % (" " + m.group(1).decode("ascii") if m else ""))
    m = re.search(rb"/rustc/([0-9a-f]{40})", head)
    if m:
        out.append("Rust: kompiler commit %s" % m.group(1).decode("ascii")[:12])
    i = head.find(b"AU3!EA06")
    if i >= 0:
        out.append("AutoIt: skrip terkompilasi (AU3!EA06) di offset 0x%X" % i)
    i = head.find(b";!@Install@!UTF-8!")
    if i >= 0:
        out.append("arsip swa-ekstrak 7-Zip: blok konfigurasi di offset 0x%X (baca perintah RunProgram)" % i)
    if b"pyarmor" in head.lower():
        out.append("PyArmor: skrip Python dilindungi (pyarmor_runtime)")
    return out


# ----------------------------- penggabung v97 -------------------------------


def _v97_enrich(d: bytes, size: int, rep: dict, fuzzy: bool) -> None:
    w = rep["warn"]
    zp, mo, dn = rep.get("zip"), rep.get("macho"), rep.get("dotnet")
    if mo:
        w.extend(mo["warn"])
    if dn:
        for x in dn["obf"]:
            w.append(".NET: " + x)
    try:
        rep["pack"] = _pack_details(d, size) if not zp else []
    except Exception as e:
        rep["pack"] = []
        w.append("analisis kemasan gagal: %s" % type(e).__name__)
    try:
        rep["xor"] = _xor_hunt(d) if not zp else []
    except Exception as e:
        rep["xor"] = []
        w.append("perburuan XOR gagal: %s" % type(e).__name__)
    for x in rep["xor"][:2]:
        w.append("kata kunci tersembunyi setelah dekode %s 0x%02X: %s (kemungkinan string / payload terenkode satu byte)" % (x["op"], x["key"], ", ".join(x["words"])))
    rep["ctph"] = ""
    if fuzzy and not zp:
        try:
            rep["ctph"] = ctph(d[:CTPH_SAMPLE])
        except Exception as e:
            w.append("CTPH gagal: %s" % type(e).__name__)


def _render_v97(rep: dict, a, compact: bool, defang: bool) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        a("Mach-O : %s %s-bit %s, %s%s | entry: %s | tanda tangan: %s | PIE: %s%s" % (
            mo["arch"], mo["bits"], mo["type"], mo["endian"] + "-endian", (" | " + mo["platform"]) if mo["platform"] else "",
            mo["entry"] or "-", "ada" if mo["signed"] else "tidak ada", "ya" if mo["pie"] else "tidak", " | TERENKRIPSI" if mo["encrypted"] else ""))
        if mo["fat"] and len(mo["fat"]) > 1:
            a("   universal: " + ", ".join("%s (%s)" % (x[0], _human(x[2])) for x in mo["fat"][:6]))
        if not compact:
            if mo["dylibs"] or mo["weak"]:
                a("   dylib (%d): %s%s" % (len(mo["dylibs"]) + len(mo["weak"]), ", ".join(mo["dylibs"][:10]), (" | lemah: " + ", ".join(mo["weak"][:4])) if mo["weak"] else ""))
            if mo["rpaths"]:
                a("   RPATH: " + ", ".join(mo["rpaths"][:4]))
            if mo["segments"]:
                a("   segmen: " + ", ".join("%s %s %.1f" % (s["name"], s["prot"], s["ent"]) for s in mo["segments"][:8]))
            if mo["imports"]:
                a("   simbol impor (%d): %s" % (len(mo["imports"]), ", ".join(mo["imports"][:25])))
            if mo["uuid"]:
                a("   UUID: " + mo["uuid"])
    if dn:
        a(".NET   : runtime %s | %s%s | %d nama di #Strings | %d string pengguna (#US)" % (
            dn["runtime"], "IL murni" if dn["ilonly"] else "campuran (ada native)", ", strong-name" if dn["strong"] else "", dn["n_names"], len(dn["us"])))
        if not compact:
            a("   stream: " + ", ".join("%s (%s)" % (n, _human(s)) for n, s in dn["streams"][:8]))
            hot = [u for u in dn["us"] if re.search(r"(?i)https?://|\\\\|\.exe|\.dll|powershell|cmd|\.onion|password|token|key", u)][:8]
            if hot:
                a("   string pengguna menarik: " + " | ".join(_df(x, defang) for x in hot))
    for line in rep.get("pack") or []:
        a("Kemasan: " + line)
    for x in (rep.get("xor") or [])[: (1 if compact else 4)]:
        a("Perburuan satu-byte: %s kunci 0x%02X -> %s%s" % (x["op"], x["key"], ", ".join(x["words"]), (" | URL: " + " | ".join(_df(u, defang) for u in x["urls"])) if x["urls"] else ""))
    if rep.get("ctph") and not compact:
        a("CTPH   : %s%s" % (rep["ctph"], " (sampel %s pertama)" % _human(CTPH_SAMPLE) if rep["size"] > CTPH_SAMPLE else ""))


def _score_v97(rep: dict, add) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        if any(s["prot"][1:] == "WX" for s in mo["segments"]):
            add(1, "segmen Mach-O W+X")
        if any(s["ent"] > 7.2 and s["fsize"] > 16384 and s["name"] != "__LINKEDIT" for s in mo["segments"]) and not mo["encrypted"]:
            add(1, "segmen Mach-O berentropi tinggi")
    if dn and dn["obf"]:
        add(2, "metadata .NET menunjukkan obfuskasi")
    x = rep.get("xor") or []
    if x:
        strong = any(w_ in ("This program cannot be run", "https://", "http://", "powershell", "cmd.exe") for r_ in x for w_ in r_["words"])
        add(3 if strong else 1, "kata kunci tersembunyi di balik dekode satu-byte")


# ----------------------------- keluarga sampel (folder) ---------------------


def _families(items: list[dict], fuzzy: bool) -> list[dict]:
    fam: list[dict] = []
    for key, label in (("imphash", "imphash sama"), ("rich", "rich header sama"), ("macho_uuid", "UUID Mach-O sama")):
        g: dict[str, list[str]] = {}
        for it in items:
            if it.get(key):
                g.setdefault(it[key], []).append(it["rel"])
        fam += [{"basis": label, "members": v} for v in g.values() if len(v) > 1]
    if fuzzy:
        cand = [it for it in items if it.get("ctph")][:150]
        seen: set[int] = set()
        for i, x in enumerate(cand):
            if i in seen:
                continue
            grp = [x["rel"]]
            for j in range(i + 1, len(cand)):
                if j not in seen and cand[j]["sha256"] != x["sha256"] and ctph_compare(x["ctph"], cand[j]["ctph"]) >= 70:
                    grp.append(cand[j]["rel"])
                    seen.add(j)
            if len(grp) > 1:
                fam.append({"basis": "CTPH >= 70", "members": grp})
    return fam[:12]


# ----------------------------- laporan Markdown -----------------------------


def triage_md(path, defang: bool = True) -> str:
    """Laporan Markdown siap simpan / tempel: ringkasan, skor, kemampuan, IOC, draf YARA. Hanya-baca."""
    try:
        rep = triage(path)
    except Exception as e:
        return "# Triase gagal\n\n`%s: %s`" % (type(e).__name__, str(e)[:120])
    ind = rep["ind"]
    L = ["# Laporan Triase REA v%s: %s" % (VERSION, _clean(rep["name"])), "",
         "| Hal | Nilai |", "|---|---|", "| Jenis | %s |" % _clean(rep["kind"]).replace("|", "/"), "| Ukuran | %s |" % _human(rep["size"]),
         "| SHA-256 | `%s` |" % rep["sha256"], "| SHA-1 | `%s` |" % rep["sha1"], "| MD5 | `%s` |" % rep["md5"],
         "| Entropi | %.2f / 8.00 |" % rep["entropy"]]
    if rep.get("ctph"):
        L.append("| CTPH | `%s` |" % rep["ctph"])
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append("| imphash | `%s` |" % pe["imphash"])
    L += ["", "## Skor heuristik: %d (%s)" % (rep["score"], rep["level"]), "", "_Petunjuk dari fakta terukur, bukan vonis._", ""]
    L += ["- " + _clean(x) for x in rep["why"]] or ["- tidak ada tanda"]
    if ind["caps"]:
        L += ["", "## Indikasi kemampuan", ""]
        for cap, hit in ind["caps"].items():
            L.append("- **%s**: %s%s" % (cap, ", ".join(_clean(h) for h in hit), (" (%s)" % ATTACK[cap]) if cap in ATTACK else ""))
    if rep["warn"]:
        L += ["", "## Perhatian", ""] + ["- " + _clean(x) for x in rep["warn"][:25]]
    for lab, key in (("URL", "urls"), ("IP kandidat", "ips"), ("Email", "emails"), ("Registry", "reg")):
        if ind[key]:
            L += ["", "## %s" % lab, ""] + ["- `%s`" % _clean(_df(x, defang)) for x in ind[key][:25]]
    if rep.get("pack"):
        L += ["", "## Kemasan / toolchain", ""] + ["- " + _clean(x) for x in rep["pack"]]
    for label, hint in rep.get("tools", []):
        L.append("- %s: %s" % (_clean(label), _clean(hint)))
    L += ["", "## Draf YARA (WAJIB diuji terhadap file sah)", "", "```yara", yara_draft(rep), "```", "",
          "---", "REA v%s | by: %s | dihitung statis dari bytes file, tanpa menjalankannya." % (VERSION, AUTHOR)]
    return "\n".join(L)


# ----------------------------- API JSON untuk Iris / Hermes -----------------

_API_ACTIONS = ("capabilities", "triage", "json", "ioc", "yara", "md", "similar", "hex", "compare", "list", "extract", "dir", "ctph")


def _api_path(p) -> Path:
    """Jika REA_ROOTS (dipisah os.pathsep) diisi, hanya path di bawah akar itu yang boleh dibaca / ditulis."""
    pp = Path(str(p)).expanduser().resolve()
    roots = [x for x in os.environ.get("REA_ROOTS", "").split(os.pathsep) if x]
    if roots and not any(pp == Path(r).resolve() or Path(r).resolve() in pp.parents for r in roots):
        raise PermissionError("path di luar REA_ROOTS: %s" % pp.name)
    return pp


def rea_api(request) -> dict:
    """Satu pintu JSON untuk agen. request: dict atau string JSON, contoh {"action": "triage", "path": "x.exe", "compact": true}.
    Selalu mengembalikan dict {"ok": bool, ...}; tidak pernah melempar. Aksi: lihat _API_ACTIONS."""
    try:
        req = json.loads(request) if isinstance(request, (str, bytes)) else dict(request)
        act = str(req.get("action", "")).lower()
        mc = max(0, int(req.get("max_chars", 12000)))
        trim = lambda t: t if not mc or len(t) <= mc else t[:mc - 30] + "\n[...dipangkas supaya muat...]"
        if act == "capabilities":
            return {"ok": True, "version": VERSION, "actions": list(_API_ACTIONS), "rea_extract": _extract_mod() is not None,
                    "rea_binary": _has_binary(), "roots_restricted": bool(os.environ.get("REA_ROOTS"))}
        if act == "triage":
            p = _api_path(req["path"])
            if p.is_dir():
                return {"ok": True, "action": act, "text": trim(triage_dir_text(str(p), defang=bool(req.get("defang", True))))}
            rep = triage(p)
            return {"ok": True, "action": act, "score": rep["score"], "level": rep["level"], "sha256": rep["sha256"], "kind": rep["kind"],
                    "text": trim(render(rep, compact=bool(req.get("compact", False)), defang=bool(req.get("defang", True)), max_chars=mc))}
        if act in ("json", "ioc"):
            return {"ok": True, "action": act, "data": json.loads(triage_json(_api_path(req["path"]), ioc_only=act == "ioc"))}
        if act == "yara":
            return {"ok": True, "action": act, "text": yara_draft(triage(_api_path(req["path"]), fuzzy=False))}
        if act == "md":
            return {"ok": True, "action": act, "text": trim(triage_md(_api_path(req["path"]), defang=bool(req.get("defang", True))))}
        if act == "ctph":
            data, _sz = _read_sample(_api_path(req["path"]))
            return {"ok": True, "action": act, "ctph": ctph(data), "sample": len(data)}
        if act == "similar":
            return {"ok": True, "action": act, "data": similarity(_api_path(req["a"]), _api_path(req["b"]))}
        if act == "hex":
            return {"ok": True, "action": act, "text": trim(hex_text(_api_path(req["path"]), int(req.get("offset", 0)), int(req.get("length", 256))))}
        if act == "compare":
            return {"ok": True, "action": act, "text": trim(compare_text(_api_path(req["a"]), _api_path(req["b"])))}
        if act == "list":
            return {"ok": True, "action": act, "text": trim(container_text(_api_path(req["path"]), max_chars=mc))}
        if act == "extract":
            m = container_extract(_api_path(req["path"]), _api_path(req["outdir"]), pattern=req.get("pattern"), scan=bool(req.get("scan", False)))
            return {"ok": m.get("status") == "success", "action": act, "manifest": m}
        if act == "dir":
            return {"ok": True, "action": act, "text": trim(triage_dir_text(str(_api_path(req["path"])), defang=bool(req.get("defang", True))))}
        return {"ok": False, "error": "aksi tidak dikenal: %s" % act[:40], "actions": list(_API_ACTIONS)}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def _has_binary() -> bool:
    try:
        import rea_binary  # noqa: F401
        return True
    except ImportError:
        return False


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
    if "--api" in argv:      # --api '{"action": "triage", "path": "x.exe"}'  (JSON satu baris untuk agen)
        t = argv[argv.index("--api") + 1:]
        print(json.dumps(rea_api(t[0] if t else "{}"), ensure_ascii=False, indent=2, default=str))
        raise SystemExit(0)
    if "--similar" in argv:  # --similar A B
        t = argv[argv.index("--similar") + 1:]
        print(similar_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --similar A B")
        raise SystemExit(0)
    if "--md" in argv:       # --md FILE  -> laporan Markdown
        t = argv[argv.index("--md") + 1:]
        print(triage_md(t[0]) if t else "pemakaian: --md FILE")
        raise SystemExit(0)
    if "--ctph" in argv:     # --ctph FILE
        t = argv[argv.index("--ctph") + 1:]
        print(ctph(_read_sample(t[0])[0]) if t else "pemakaian: --ctph FILE")
        raise SystemExit(0)
    if "--hex" in argv:      # --hex FILE [OFFSET [LENGTH]]
        t = argv[argv.index("--hex") + 1:]
        print(hex_text(t[0], int(t[1], 0) if len(t) > 1 else 0, int(t[2], 0) if len(t) > 2 else 256) if t else "pemakaian: --hex FILE [OFFSET [LENGTH]]")
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
        print("pemakaian: python rea_triage.py <file|folder> [--compact] [--json] [--ioc] [--raw (tanpa defang)] [--yara] [--carve DIR] | --hex FILE [OFFSET [LENGTH]] | --compare A B | --list <container> | --extract OUTDIR <container> [pola] [--scan] | --similar A B | --md FILE | --ctph FILE | --api JSON")
    elif Path(args[0]).is_dir():
        print(triage_dir_text(args[0], defang="--raw" not in flags))
    elif "--json" in flags or "--ioc" in flags:
        print(triage_json(args[0], ioc_only="--ioc" in flags))
    elif "--yara" in flags:
        print(yara_draft(triage(args[0])))
    else:
        full, _note = triage_bundle(args[0], carve_dir=cdir) if cdir else (None, None)
        print(full if full is not None else triage_text(args[0], compact="--compact" in flags, defang="--raw" not in flags))
