"""rea_triage.py - triase statis lokal untuk perintah /rea (Iris v99.1, kumulatif dengan v99.0, v98.6, v97, v96, v95, v94, v93, v92, v91).  by: KangJiho

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

v98 (RE Lab, khusus reverse engineering PE x86 / x64; semua aditif, tetap statis dan hanya pustaka standar):
    - penemuan fungsi (entry + ekspor + target CALL + prolog) dan PETA PANGGILAN API per fungsi (CALL [IAT], thunk JMP, pointer IAT);
    - xref string (LEA RIP-relatif / PUSH imm32) -> fungsi mana memakai string apa; peringkat fungsi menarik per kelompok kemampuan;
    - anti-analisis tingkat instruksi: PEB / TEB, RDTSC, CPUID, INT 2D, SIDT, syscall langsung (SysWhispers / Hell's Gate), Heaven's Gate;
    - API hashing (ror13 block_api; tabel hash dihitung saat runtime), stack string, stub entry point;
    - re_lab_path(path), re_text(path), xref_text(path, query), disasm_text(path, at, count) (disassembler memakai capstone bila terpasang);
    - v98.1: disasm juga untuk ELF, Mach-O (tipis / fat) dan berkas mentah / shellcode (x86 x64 arm thumb arm64 mips ppc riscv ...), arch= memaksa arsitektur;
    - v98.2: aturan kemampuan berbasis API dari mandiant/capa-rules (subset, tingkat berkas, petunjuk saja); unpack UPX opsional (`--unpack FILE OUTDIR`, aksi API `unpack`, butuh alat `upx`);
    - v98.3: APK lebih dalam (AndroidManifest biner: paket / SDK / komponen / aksi intent; DEX: metode API sensitif + dugaan obfuskasi), dekoder skrip
      (PowerShell -EncodedCommand, FromBase64String, [char] / Chr() / fromCharCode, \\xNN), hash ikon PE, `--yarascan FILE RULES` (butuh yara-python);
    - v98.4: RE Lab juga untuk ELF x86 / x86-64 (peta PLT / GOT -> nama impor, nama fungsi dari .symtab / .dynsym, xref string, peringkat fungsi);
    - aksi API baru: re, xref, disasm; CLI: --re FILE | --xref FILE QUERY | --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N].

v98.5 (akurasi triase PE; mengurangi alarm palsu, tanpa mengubah API):
    - OriginalFilename dibandingkan tanpa ekstensi (launcher == launcher.exe);
    - 'persistensi' tidak lagi cocok dengan GetStartupInfo; kecocokan kemampuan dipisah: tabel import / string khas (kuat) vs nama API
      yang hanya muncul sebagai teks (lemah, tidak ikut skor kecuali API injeksi);
    - blok PKCS#7 tanda tangan Authenticode dikecualikan dari ekstraksi string / IOC (header dan byte sisa tetap dipindai; byte sisa
      yang tak berstruktur diberi peringatan); kandidat IP yang sama dengan nomor versi file dibuang;
    - resource PNG / JPEG / ZIP yang strukturnya utuh tidak lagi ditandai 'payload terenkripsi' dan tidak ikut skor / wilayah entropi tinggi
      (magic palsu atau data tambahan setelah IEND tetap ditandai);
    - baris 'Faktor penyeimbang' di laporan PE (hal lazim pada file sah; bukan jaminan aman).

v98.6 (integritas, kalibrasi, derau; API lama tidak berubah, semua tambahan aditif):
    - integritas tanda tangan Authenticode: hash Authenticode dihitung ulang (sha256 / sha1 / md5 sesuai blob) dan dibandingkan dengan digest
      di SpcIndirectDataContent. Tidak cocok = file diubah setelah ditandatangani (+3). Rantai sertifikat dan pencabutan TETAP tidak diperiksa;
      CN penandatangan dibandingkan dengan CompanyName (hanya informasi);
    - daftar hash lokal (env REA_KNOWN_HASHES): berkas teks, satu baris `HEX [good|bad|note] [label]`; 'bad' menambah skor, 'good' masuk faktor penyeimbang;
    - peredam derau CRT: IsDebuggerPresent / GetProcAddress / LoadLibrary / CreateFile pada PE native dilipat di 'Indikasi kemampuan' dan tidak
      masuk pemetaan ATT&CK bila itu satu-satunya bukti kemampuan tsb (HANYA tampilan: skor tidak berubah, kalibrasi skor lewat rea_calibrate.py);
    - entropi bagian .rsrc dihitung tanpa resource PNG / JPEG / ZIP yang utuh (ditandai * di baris Bagian);
    - XOR kunci berulang 2-16 byte untuk stub DOS (known-plaintext; RC4 tidak bisa diburu tanpa kunci), dan resource terkelola .NET
      (ManifestResource lewat header CLR: MZ di dalam resource, blob berentropi tinggi);
    - mode kartu: render(rep, card=True) / triage_text(..., card=True) / `--card` / rea_api {"card": true}: skor, alasan, penyeimbang, PERHATIAN dulu;
      rincian import dan string dilipat. Alat kalibrasi bobot: rea_calibrate.py; tes: tests/test_rea_triage.py.

v99.0 (Asset Explorer; modul baru rea_assets.py, impor malas seperti rea_extract / rea_binary; triase PE di atas TIDAK berubah):
    REA tidak lagi terbatas pada .exe: model 3D (glTF/GLB, OBJ, STL, PLY, FBX, COLLADA), animasi (glTF, FBX, BVH), tekstur (DDS, TGA, BMP, PNG, ...),
    audio, arsip / paket game (Quake PAK, WAD, Unreal .pak v1-v9, ZIP / APK / JAR, TAR / GZIP), SQLite, dan carving berkas tertanam di berkas apa pun.
    - assets_text(path) -> str ; assets_extract(path, outdir, pattern=None, convert=True) -> dict ; assets_carve(path, outdir=None) -> dict
    - aksi API baru: assets, assets_extract, assets_carve, formats; CLI: --assets FILE | --assets-extract OUTDIR FILE [pola] | --assets-carve FILE [OUTDIR] | --formats
    - plugin parser buatan sendiri: env REA_PLUGINS=FOLDER atau CLI --plugins FOLDER (sengaja TIDAK bisa diminta lewat API agen, karena plugin = kode).

NOTICE: _CAPA_RULES diturunkan dari aturan mandiant/capa-rules (c) Mandiant / Google, lisensi Apache-2.0
(https://github.com/mandiant/capa-rules). Hanya nama aturan, ATT&CK, dan daftar API yang dipakai ulang; telah diubah bentuk dan disaring.

v99.1 (gabungan v98.6 + v99.0; tidak ada perilaku lama yang berubah, semua tambahan aditif):
    - triase PE / ELF / Mach-O dari v98.6 (integritas Authenticode, daftar hash lokal, peredam derau CRT, XOR kunci berulang,
      resource terkelola .NET, mode kartu) DIPERTAHANKAN penuh, ditambah jembatan Asset Explorer dari v99.0;
    - kolom 'Jenis' kini mengenali format aset umum (PNG, JPEG, GIF, DDS, GLB, SQLite, WAV, OGG, Quake PAK, WAD) sehingga tidak lagi
      jatuh ke 'biner tak dikenal'; berkas non-exe diberi petunjuk memakai `--assets FILE` bila rea_assets.py tersedia;
    - teks bantuan CLI memuat semua opsi (--card, --assets, --assets-extract, --assets-carve, --formats, --plugins).

v99.2 (22 Nov 2026): rea_assets.py DIGABUNG ke berkas ini (bagian "rea_assets.py ... DIGABUNG", tepat sebelum assets_text); perilaku tidak berubah, VERSION tetap "99.1".
    Berkas rea_assets.py tidak dipakai lagi. CLI mandiri `python rea_assets.py ...` diganti opsi --assets / --assets-extract / --assets-carve / --formats / --plugins di sini.

NOTICE: _CAPA_RULES diturunkan dari aturan mandiant/capa-rules (c) Mandiant / Google, lisensi Apache-2.0
(https://github.com/mandiant/capa-rules). Hanya nama aturan, ATT&CK, dan daftar API yang dipakai ulang; telah diubah bentuk dan disaring.
"""
from __future__ import annotations

import base64
import bisect
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
                leaf = {"type": tlabel, "name": str(nm(nn_)), "size": size, "ent": _entropy(data[:65536]), "mz": data[:2] == b"MZ", "off": fo}
                fmt, fmt_ok = _res_format(d, fo, size)
                if fmt:
                    leaf["fmt"], leaf["fmt_ok"] = fmt, fmt_ok
                leaves.append(leaf)
                if tname == 16 and not ver:
                    txt = d[fo:fo + min(size, 16384)].decode("utf-16le", "ignore")
                    for k in _VER_KEYS:
                        m = re.search(k + r"\x00+([^\x00]{1,120})", txt)
                        if m:
                            ver[k] = m.group(1).strip()
                    quads = sorted(set(re.findall(r"(?<![\d.])\d{1,5}(?:\.\d{1,5}){3}(?![\d.])", txt)))
                    if quads:
                        leaf["vquads"] = quads[:8]   # nomor versi berbentuk a.b.c.d (bukan IP): dipakai menyaring kandidat IP
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


def _res_format(d: bytes, fo: int, size: int) -> tuple[str, bool]:
    """Kenali resource terkompres yang wajar tampak acak (PNG / JPEG / ZIP) dari magic number, lalu cek kerangka dasarnya.
    Mengembalikan (format, utuh). utuh=False bila magic cocok tetapi kerangka tidak masuk akal (mis. data tambahan setelah IEND),
    supaya awalan PNG palsu di depan payload tidak lolos."""
    if size < 12 or fo < 0 or fo + 16 > len(d):
        return "", False
    end = min(fo + size, len(d))
    head = d[fo:fo + 16]
    mv = memoryview(d)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        tail = bytes(mv[max(fo, end - 32):end]).rstrip(b"\x00")
        return "PNG", head[12:16] == b"IHDR" and tail.endswith(b"IEND\xaeB`\x82")
    if head[:3] == b"\xff\xd8\xff":
        tail = bytes(mv[max(fo, end - 64):end]).rstrip(b"\x00")
        return "JPEG", tail.endswith(b"\xff\xd9")
    if head[:4] == b"PK\x03\x04":
        tail = bytes(mv[max(fo, end - 65557):end])
        return "ZIP", b"PK\x05\x06" in tail
    return "", False


def _cert_spans(d: bytes, off: int, size: int) -> tuple[list[tuple[int, int]], int]:
    """Rentang struktur PKCS#7 (DER) di tabel sertifikat Authenticode, plus jumlah byte TAK BERSTRUKTUR setelah struktur itu (di luar
    padding nol). Hanya struktur DER yang dikecualikan dari ekstraksi string / IOC: header dan byte sisa tetap dipindai, karena data
    bisa diselipkan di tabel sertifikat tanpa merusak tanda tangan. Bila struktur tidak terbaca, hasil kosong (tidak ada yang dikecualikan)."""
    spans: list[tuple[int, int]] = []
    extra, pos, end = 0, off, min(off + size, len(d))
    while pos + 16 <= end:
        dw = struct.unpack_from("<I", d, pos)[0]
        if dw < 16 or pos + dw > end:
            return spans, extra
        s0 = pos + 8
        if d[s0] != 0x30:   # PKCS#7 SignedData selalu diawali SEQUENCE
            return spans, extra
        b = d[s0 + 1]
        if b & 0x80:
            n = b & 0x7F
            if n == 0 or n > 4 or s0 + 2 + n > pos + dw:
                return spans, extra
            hdr, ln = 2 + n, int.from_bytes(d[s0 + 2:s0 + 2 + n], "big")
        else:
            hdr, ln = 2, b
        if s0 + hdr + ln > pos + dw:
            return spans, extra
        spans.append((s0, s0 + hdr + ln))
        extra += len(d[s0 + hdr + ln:pos + dw].rstrip(b"\x00"))
        pos += (dw + 7) & ~7
    if spans and pos < end:
        extra += len(d[pos:end].rstrip(b"\x00"))
    return spans, extra


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
    try:   # v98.6: entropi bagian resource dihitung tanpa PNG / JPEG / ZIP utuh (ikon PNG membuat .rsrc tampak 'terenkripsi')
        skip_rs = [(x["off"], x["off"] + x["size"]) for x in res if x.get("fmt") and x.get("fmt_ok")]
        if skip_rs and len(dirs) > 2 and dirs[2][0]:
            rs_ = next((s for s in secs if s["va"] <= dirs[2][0] < s["va"] + max(s["vsize"], s["rsize"])), None)
            if rs_ and rs_["ent"] > 7.0 and rs_["rptr"] < len(d):
                a_, b_ = rs_["rptr"], rs_["rptr"] + min(rs_["rsize"], SEC_ENT_SAMPLE)
                rest_ = _mask_block(d, a_, b_, _merge_spans(skip_rs, len(d)))
                masked_ = (min(b_, len(d)) - a_) - len(rest_)
                if masked_ > 0:
                    rs_["ent_raw"], rs_["masked"] = rs_["ent"], masked_
                    rs_["ent"] = _entropy(rest_) if len(rest_) >= 1024 else 0.0
    except (struct.error, IndexError, ValueError, OverflowError):
        pass
    rich = None
    try:
        rich = _rich_header(d, pe_off)
    except (struct.error, IndexError, ValueError):
        pass
    signers: list[str] = []
    cert_spans: list[tuple[int, int]] = []
    cert_extra = 0
    if len(dirs) > 4 and dirs[4][0] and dirs[4][1]:
        try:
            signers = _signers(d, dirs[4][0], dirs[4][1])
        except Exception:
            pass
        try:
            cert_spans, cert_extra = _cert_spans(d, dirs[4][0], dirs[4][1])
        except Exception:
            cert_spans, cert_extra = [], 0
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
        "res": res, "ver": ver, "rich": rich, "signers": signers, "cert_spans": cert_spans, "cert_extra": cert_extra,
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
            _apk_deep(z, names, low, out)
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
        elif any(x.get("fmt") and not x.get("fmt_ok") for x in pe.get("res", [])):
            add(1, "resource berawalan PNG / JPEG / ZIP tetapi kerangkanya tidak utuh")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not x.get("fmt") for x in pe.get("res", [])):
            add(1, "resource besar berentropi tinggi (bukan PNG / JPEG / ZIP)")
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
    _score_v98(rep, add)
    _score_v986(rep, add)
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
        "secrets": secrets, "pem": bool(_PEM.search(blob)),
        "b64": sum(1 for _ in _B64.finditer(full)), "b64d": _decode_b64(full), "pdb": _uniq(_PDB.findall(blob), 3),
        "caps": caps, "caps_weak": caps_weak, "n_strings": len(strs),
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


# ---------------------------------------------------------------------------
# v98.6: integritas Authenticode, daftar hash lokal, peredam CRT, XOR kunci berulang, resource .NET
# ---------------------------------------------------------------------------

_OID_SPC_INDIRECT = bytes.fromhex("060a2b060104018237020104")
_AC_ALGS = (   # (OID DER lengkap dengan tag + panjang, nama hashlib, ukuran digest)
    (bytes.fromhex("0609608648016503040201"), "sha256", 32),
    (bytes.fromhex("0609608648016503040202"), "sha384", 48),
    (bytes.fromhex("0609608648016503040203"), "sha512", 64),
    (bytes.fromhex("06052b0e03021a"), "sha1", 20),
    (bytes.fromhex("06082a864886f70d0205"), "md5", 16),
)


def _ac_digests(blob: bytes) -> list[tuple[str, bytes]]:
    """Semua (algoritma, digest) dari SpcIndirectDataContent di blob PKCS#7 (tanda tangan ganda / bersarang menghasilkan lebih dari satu)."""
    out: list[tuple[str, bytes]] = []
    pos = blob.find(_OID_SPC_INDIRECT)
    n = 0
    while pos != -1 and n < 8:
        win = blob[pos:pos + 768]
        best = None
        for oid, name, dsz in _AC_ALGS:
            i = win.find(oid)
            while i != -1:
                j = i + len(oid)
                if win[j:j + 2] == b"\x05\x00":
                    j += 2
                if win[j:j + 2] == bytes([4, dsz]) and j + 2 + dsz <= len(win):
                    if best is None or i < best[0]:
                        best = (i, name, win[j + 2:j + 2 + dsz])
                    break
                i = win.find(oid, i + 1)
        if best:
            out.append((best[1], best[2]))
        pos = blob.find(_OID_SPC_INDIRECT, pos + 1)
        n += 1
    return out


def _authenticode_hash(d: bytes, size: int, pe: dict, alg: str) -> str | None:
    """Hash Authenticode sesuai spesifikasi Microsoft: seluruh berkas KECUALI field CheckSum, entri Certificate Table di data directory, dan
    isi tabel sertifikat. None bila berkas tidak utuh di memori atau tabel section tidak masuk akal."""
    if len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    ck = o + 64
    cdir = o + (112 if is64 else 96) + 8 * 4
    hsz = struct.unpack_from("<I", d, o + 60)[0]
    if cdir + 8 > len(d) or hsz > len(d) or hsz < cdir + 8:
        return None
    c_off, c_sz = struct.unpack_from("<II", d, cdir)
    h = hashlib.new(alg)
    h.update(d[:ck])
    h.update(d[ck + 4:cdir])
    h.update(d[cdir + 8:hsz])
    pos = hsz
    for s in sorted((x for x in pe["sections"] if x["rsize"]), key=lambda x: x["rptr"]):
        a, b = s["rptr"], s["rptr"] + s["rsize"]
        if a < pos or b > len(d):
            return None   # bagian tumpang-tindih / keluar berkas: jangan menebak
        h.update(d[a:b])
        pos = b
    if c_off and c_sz and c_off >= pos:
        h.update(d[pos:c_off])
        h.update(d[c_off + c_sz:])
    else:
        h.update(d[pos:])
    return h.hexdigest()


def _authenticode_check(d: bytes, size: int, pe: dict) -> dict | None:
    """Integritas (BUKAN keabsahan) tanda tangan: digest di blob vs hash isi berkas. match True / False; None bila tidak berlaku.
    Tidak memeriksa rantai sertifikat, masa berlaku, atau pencabutan: itu butuh Get-AuthenticodeSignature / signtool."""
    if not pe.get("signed") or len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    c_off, c_sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 4)
    if c_off + 8 > len(d) or c_sz < 8:
        return None
    end = min(c_off + c_sz, len(d))
    cands: list[tuple[str, bytes]] = []
    pos = c_off
    while pos + 8 <= end and len(cands) < 8:
        dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
        if dw < 8 or pos + dw > end:
            break
        if typ == 2:
            cands += _ac_digests(d[pos + 8:pos + dw])
        pos += (dw + 7) & ~7
    if not cands:
        return None
    cache: dict[str, str | None] = {}
    first = None
    for alg, dig in cands:
        if alg not in cache:
            cache[alg] = _authenticode_hash(d, size, pe, alg)
        comp = cache[alg]
        if comp is None:
            return None
        if first is None:
            first = (alg, dig.hex(), comp)
        if comp == dig.hex():
            return {"alg": alg, "signed": dig.hex(), "computed": comp, "match": True}
    return {"alg": first[0], "signed": first[1], "computed": first[2], "match": False}


_CO_STOP = frozenset({"corporation", "company", "limited", "software", "technologies", "technology", "group", "holdings", "international",
                      "systems", "solutions", "services", "global", "foundation"})


def _signer_vs_company(pe: dict):
    """True / False: apakah nama penandatangan (CN) memuat kata dari CompanyName. None bila salah satunya tidak ada. Hanya informasi."""
    sg, comp = pe.get("signers") or [], (pe.get("ver") or {}).get("CompanyName", "")
    tok = lambda s: {t for t in re.findall(r"[a-z0-9]{4,}", s.lower())} - _CO_STOP
    a, b = tok(comp), set().union(*(tok(s) for s in sg)) if sg else set()
    if not a or not b:
        return None
    return bool(a & b)


_KNOWN_CACHE: dict = {"key": None, "map": {}}


def _known_hashes() -> dict[str, tuple[str, str]]:
    """Daftar hash lokal dari berkas teks di env REA_KNOWN_HASHES. Satu baris: HEX [good|bad|note] [label]. '#' = komentar.
    HEX boleh md5 / sha1 / sha256. Hasil di-cache menurut mtime."""
    p = os.environ.get("REA_KNOWN_HASHES", "")
    if not p:
        return {}
    try:
        st = os.stat(p)
    except OSError:
        return {}
    key = (p, st.st_mtime_ns, st.st_size)
    if _KNOWN_CACHE["key"] == key:
        return _KNOWN_CACHE["map"]
    m: dict[str, tuple[str, str]] = {}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(8 * 1024 * 1024)
        for ln in txt.splitlines()[:200000]:
            ln = ln.split("#", 1)[0].strip()
            if not ln:
                continue
            parts = ln.split(None, 2)
            h = parts[0].lower()
            if len(h) not in (32, 40, 64) or not re.fullmatch(r"[0-9a-f]+", h):
                continue
            tag, label = "note", ""
            if len(parts) > 1:
                if parts[1].lower() in ("good", "bad", "note"):
                    tag, label = parts[1].lower(), (parts[2] if len(parts) > 2 else "")
                else:
                    label = " ".join(parts[1:])
            m[h] = (tag, label[:120])
    except OSError:
        return {}
    _KNOWN_CACHE["key"], _KNOWN_CACHE["map"] = key, m
    return m


def _known_lookup(rep: dict) -> dict | None:
    km = _known_hashes()
    if not km:
        return None
    for k in ("sha256", "sha1", "md5"):
        hit = km.get(rep.get(k, ""))
        if hit:
            return {"tag": hit[0], "label": hit[1], "by": k}
    return None


# API yang ada di hampir semua program MSVC / CRT (bukan indikasi niat). Hanya PE native yang dilipat; .NET P/Invoke tetap dilaporkan.
_CRT_COMMON = frozenset({"isdebuggerpresent", "getprocaddress", "loadlibrary", "createfile"})


def _crt_fold_ok(rep: dict) -> bool:
    pe = rep.get("pe")
    return bool(pe and not pe.get("broken") and not pe.get("dotnet"))


def _score_v986(rep: dict, add) -> None:
    ac = rep.get("authenticode")
    if ac and ac.get("match") is False:
        add(3, "digest Authenticode tidak cocok dengan isi file (diubah setelah ditandatangani)")
    kn = rep.get("known")
    if kn and kn["tag"] == "bad":
        add(10, "hash cocok daftar lokal 'bad'%s" % ((": " + kn["label"]) if kn["label"] else ""))
    xm = rep.get("xor_multi") or []
    if xm:
        add(3 if any(x["mz"] for x in xm) else 2, "stub DOS terenkode XOR kunci berulang%s" % (" (PE tersembunyi)" if any(x["mz"] for x in xm) else ""))
    dn = rep.get("dotnet")
    emb = rep.get("emb") or {}
    if dn and dn.get("mres"):
        if any(x["mz"] for x in dn["mres"]) and not (emb.get("plain") or emb.get("xor")):
            add(3, "executable (MZ) di dalam resource terkelola .NET")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")) for x in dn["mres"]):
            add(1, "resource terkelola .NET berentropi tinggi (bukan PNG / JPEG / ZIP utuh)")


def _render_v986(rep: dict, a, compact: bool, defang: bool) -> None:
    pe = rep.get("pe")
    ac = rep.get("authenticode")
    if ac:
        if ac["match"]:
            a("Integritas tanda tangan: digest %s di blob COCOK dengan hash isi file (berkas utuh sejak ditandatangani). Rantai sertifikat dan pencabutan TIDAK diperiksa." % ac["alg"])
        else:
            a("Integritas tanda tangan: digest %s di blob %s... TIDAK sama dengan hash isi file %s...: berkas diubah setelah ditandatangani." % (ac["alg"], ac["signed"][:16], ac["computed"][:16]))
    if pe and not pe.get("broken") and pe.get("signers"):
        sm = rep.get("signer_match")
        if sm is False:
            a("Penandatangan vs CompanyName: tidak ada kata yang sama (%s vs %s). Hanya informasi; perusahaan induk / penerbit lain juga lazim." % (", ".join(pe["signers"][:2]), (pe.get("ver") or {}).get("CompanyName", "?")))
        elif sm:
            a("Penandatangan vs CompanyName: sejalan.")
    dn = rep.get("dotnet")
    if dn and dn.get("mres"):
        tot = sum(x["size"] for x in dn["mres"])
        a("Resource .NET: %d blob terkelola (%s)%s" % (len(dn["mres"]), _human(tot), ("; MZ di dalam: " + ", ".join("0x%X" % x["off"] for x in dn["mres"] if x["mz"])) if any(x["mz"] for x in dn["mres"]) else ""))
        if not compact:
            for x in sorted(dn["mres"], key=lambda x: -x["size"])[:4]:
                a("   - off 0x%X %s ent %.2f%s%s" % (x["off"], _human(x["size"]), x["ent"], " .resources" if x.get("rsrc") else "", " MZ" if x["mz"] else ""))
    for x in (rep.get("xor_multi") or [])[: (1 if compact else 3)]:
        a("Perburuan XOR kunci berulang: periode %d byte, kunci %s, stub DOS di offset 0x%X%s" % (x["k"], x["key"], x["off"], " | MZ terkonfirmasi di 0x%X" % x["mz_off"] if x["mz"] else ""))


def _fold_caps(rep: dict) -> tuple[list[tuple[str, list[str], list[str]]], list[tuple[str, list[str]]], set[str]]:
    """Pisahkan nama kemampuan (tampil) dari nama umum CRT (dilipat). -> (baris, terlipat, kemampuan yang seluruhnya CRT)."""
    ind = rep["ind"]
    fold_on = _crt_fold_ok(rep)
    rows, folded, crt_only = [], [], set()
    for cap, hit in ind["caps"].items():
        keep = [h for h in hit if not (fold_on and h.lower() in _CRT_COMMON)]
        fold = [h for h in hit if fold_on and h.lower() in _CRT_COMMON]
        if fold:
            folded.append((cap, fold))
        if keep:
            rows.append((cap, keep, fold))
        else:
            crt_only.add(cap)
    return rows, folded, crt_only


def render_card(rep: dict, defang: bool = True) -> str:
    """Kartu ringkas: skor, alasan, faktor penyeimbang, PERHATIAN dulu; rincian (import, string, bagian) dilipat jadi hitungan."""
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("KARTU TRIASE | %s | %s | %s" % (rep["name"], _human(rep["size"]), rep["kind"]))
    kn = rep.get("known")
    if kn:
        a("Daftar hash lokal (%s): %s%s" % (kn["by"], {"good": "DIKENAL SAH", "bad": "DIKENAL JAHAT", "note": "catatan"}[kn["tag"]], (" - " + kn["label"]) if kn["label"] else ""))
    a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis." % (rep["score"], rep["level"]))
    for x in rep["why"][:8]:
        a("   * " + x)
    if len(rep["why"]) > 8:
        a("   (+%d alasan lain di laporan penuh)" % (len(rep["why"]) - 8))
    if rep.get("balance"):
        a("Penyeimbang (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + "; ".join(rep["balance"][:5]))
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][:6]:
            a("   ! " + x)
        if len(rep["warn"]) > 6:
            a("   (+%d peringatan lain di laporan penuh)" % (len(rep["warn"]) - 6))
    ind = rep["ind"]
    rows, folded, _co = _fold_caps(rep)
    if rows:
        a("Kemampuan (petunjuk): " + "; ".join(_cap_text(ind, cap, keep) for cap, keep, _f in rows[:5]))
    bits = ["SHA-256 " + rep["sha256"], "entropi %.2f" % rep["entropy"]]
    a(" | ".join(bits))
    pe = rep.get("pe")
    cnt: list[str] = []
    if pe and not pe.get("broken"):
        cnt.append("import %d fungsi / %d DLL" % (sum(len(v) for v in pe["imports"].values()), len(pe["imports"])))
        cnt.append("%d bagian" % len(pe["sections"]))
    for lab, key in (("URL", "urls"), ("IP", "ips"), ("email", "emails"), ("registry", "reg"), ("path", "paths")):
        if ind[key]:
            cnt.append("%d %s" % (len(ind[key]), lab))
    cnt.append("%d string" % ind["n_strings"])
    a("Dilipat: " + ", ".join(cnt) + ". Minta laporan penuh untuk rincian.")
    _ah = _assets_hint(rep)
    if _ah:
        a(_ah)
    if ind["urls"]:
        a("URL teratas: " + " | ".join(_df(u, defang) for u in ind["urls"][:3]))
    return "\n".join(L)



def triage(path, follow_links: bool = True, fuzzy: bool = True) -> dict:
    p = Path(path)
    f, size = _open_regular(p, follow_links)
    with f:
        return _triage_open(p, f, size, fuzzy)


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
    if rep["ind"]["secrets"]:
        w.append("kandidat kredensial tertanam (nilai disamarkan di laporan)")

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
    _v97_enrich(d, size, rep, fuzzy)
    _v98_enrich(d, rep)
    _capa_enrich(rep, api_names)
    _script_enrich(rep, strs)
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
        _render_apk(zp, a, compact)
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
    a("Batas triase: hasil di atas murni pembacaan statis; tanpa dekompilasi, tanpa emulasi, tanpa jaringan, file tidak dijalankan.")
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


# ---------------------------------------------------------------------------
# v97: Mach-O, metadata .NET, CTPH (hash fuzzy), perburuan XOR / ADD / ROL, detail kemasan, keluarga sampel,
#      laporan Markdown, dan API JSON untuk Iris / Hermes. Semuanya hanya-baca, pustaka standar, file tidak dijalankan.
# ---------------------------------------------------------------------------

VERSION = "99.1"
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


_XOR_CRIB = b"This program cannot be run in DOS mode"


def _xor_multi(d: bytes, budget: float = 3.0) -> list[dict]:
    """XOR dengan kunci BERULANG 2-16 byte. Known-plaintext: tulisan stub DOS tetap polos di PE biasa, jadi selisih d[j] ^ d[j+k] pada stub
    terenkode kunci periode k sama persis dengan selisih teksnya sendiri, apa pun kuncinya. Dicari lewat big-int (satu XOR per k).
    RC4 / kunci tak berulang tidak bisa diburu begini tanpa kunci. Jendela: 2 MB pertama + 1 MB terakhir."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    if _XOR_CRIB in samp:
        return []
    n, crib = len(samp), _XOR_CRIB
    t0 = time.monotonic()
    x = int.from_bytes(samp, "big")
    mask = (1 << (8 * n)) - 1

    def to_off(p: int) -> int:
        return p if len(d) <= head + tail or p < head else len(d) - tail + (p - head)

    res: list[dict] = []
    seen: set[int] = set()
    for k in range(2, 17):
        if time.monotonic() - t0 > budget or len(res) >= 3:
            break
        diff = (((x << (8 * k)) & mask) ^ x).to_bytes(n, "big")
        pat = bytes(crib[i] ^ crib[i + k] for i in range(len(crib) - k))
        pos, tries = diff.find(pat), 0
        while pos >= 0 and tries < 4:
            tries += 1
            if pos + len(crib) <= n and pos not in seen:
                ks = bytes(samp[pos + i] ^ crib[i] for i in range(len(crib)))
                if all(ks[i] == ks[i % k] for i in range(len(crib))) and len(set(ks[:k])) > 1:
                    seen.add(pos)
                    # kunci disejajarkan ke awal MZ (stub DOS lazim di offset 0x4E dari MZ)
                    mz = pos - 0x4E
                    key = bytes(ks[(i - 0x4E) % k] for i in range(k))
                    ok = mz >= 0 and bytes(samp[mz + i] ^ key[i % k] for i in range(2)) == b"MZ"
                    res.append({"k": k, "key": (key if ok else ks[:k]).hex(), "off": to_off(pos), "mz": ok, "mz_off": to_off(mz) if ok else 0})
            pos = diff.find(pat, pos + 1)
    res.sort(key=lambda r: (not r["mz"], r["k"]))
    return res[:3]


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
    try:
        rep["xor_multi"] = _xor_multi(d) if not zp else []
    except Exception as e:
        rep["xor_multi"] = []
        w.append("perburuan XOR kunci berulang gagal: %s" % type(e).__name__)
    for x in rep["xor_multi"][:2]:
        w.append("stub DOS terenkode XOR kunci berulang %d byte (%s) di offset 0x%X%s" % (x["k"], x["key"], x["off"], "; MZ terkonfirmasi: PE tersembunyi" if x["mz"] else ""))
    for x in (dn or {}).get("mres", []):
        if x["mz"]:
            w.append("resource terkelola .NET berisi executable (MZ, %s) di offset 0x%X" % (_human(x["size"]), x["off"]))
        elif x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")):
            w.append("resource terkelola .NET berentropi %.2f (%s) di offset 0x%X: kemungkinan payload terenkripsi / terkompres" % (x["ent"], _human(x["size"]), x["off"]))
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
    if rep.get("balance"):
        L += ["", "**Faktor penyeimbang** (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + _clean("; ".join(rep["balance"]))]
    if ind["caps"]:
        L += ["", "## Indikasi kemampuan", ""]
        for cap, hit in ind["caps"].items():
            L.append("- **%s**%s" % (_clean(_cap_text(ind, cap, hit)), (" (%s)" % ATTACK[cap]) if cap in ATTACK and _cap_strong(ind, cap) else ""))
    if rep["warn"]:
        L += ["", "## Perhatian", ""] + ["- " + _clean(x) for x in rep["warn"][:25]]
    for lab, key in (("URL", "urls"), ("IP kandidat", "ips"), ("Email", "emails"), ("Registry", "reg")):
        if ind[key]:
            L += ["", "## %s" % lab, ""] + ["- `%s`" % _clean(_df(x, defang)) for x in ind[key][:25]]
    if rep.get("pack"):
        L += ["", "## Kemasan / toolchain", ""] + ["- " + _clean(x) for x in rep["pack"]]
    for label, hint in rep.get("tools", []):
        L.append("- %s: %s" % (_clean(label), _clean(hint)))
    rl = rep.get("relab")
    if rl:
        L += ["", "## RE Lab", "", "%s, base %s: %d fungsi, %d panggilan API terpetakan, %d string dirujuk kode." % (rl["arch"], rl["image_base"], rl["n_functions"], rl["n_api_sites"], rl["n_strrefs"]), ""]
        if rl["functions"]:
            L += ["| Fungsi | VA | Ukuran | Skor | Kemampuan | API |", "|---|---|---|---|---|---|"]
            for f in rl["functions"][:10]:
                L.append("| %s | %s | %s | %d | %s | %s |" % (_clean(f["name"]).replace("|", "/"), f["va"], _human(f["size"]), f["score"], "; ".join(f["tags"]) or "-", ", ".join(x.split("!")[-1] for x in f["apis"][:6]) or "-"))
        L += ["- anti-analisis: %s x%d" % (_clean(x["technique"]), x["count"]) for x in rl["anti"]]
        L += ["- stack string: `%s` [%s]" % (_clean(x["text"]), x["tag"]) for x in rl["stack_strings"][:6]]
        L += ["- API hash: %s" % ", ".join(h["api"] for h in rl["api_hashes"][:6])] if rl["api_hashes"] else []
    L += ["", "## Draf YARA (WAJIB diuji terhadap file sah)", "", "```yara", yara_draft(rep), "```", "",
          "---", "REA v%s | by: %s | dihitung statis dari bytes file, tanpa menjalankannya." % (VERSION, AUTHOR)]
    return "\n".join(L)


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
    return info, ctx


def _v98_enrich(d: bytes, rep: dict) -> None:
    pe = rep.get("pe")
    rep["relab"] = None
    if not (pe and not pe.get("broken")) and not rep.get("elf"):
        return
    try:
        info, _ctx = _re_lab(d, pe) if (pe and not pe.get("broken")) else _relab_elf(d)
    except Exception as e:
        rep["warn"].append("RE Lab gagal: %s" % type(e).__name__)
        return
    rep["relab"] = info
    if not info:
        return
    for x in info["notes"]:
        rep["warn"].append("RE Lab: " + x)
    for x in info["anti"]:
        if x["technique"].startswith(("syscall", "Heaven")):
            rep["warn"].append("RE Lab: %s (%d lokasi, pertama 0x%s)" % (x["technique"], x["count"], x["first"][2:]))
    if info["api_hashes"]:
        rep["warn"].append("RE Lab: konstanta API hash terdeteksi (%s): kemungkinan resolusi API tersembunyi / shellcode" % ", ".join(h["api"] for h in info["api_hashes"][:3]))


def _render_v98(rep: dict, a, compact: bool, defang: bool) -> None:
    r = rep.get("relab")
    if not r:
        return
    a("RE Lab : %s | base %s | %d fungsi, %d panggilan API terpetakan (%d slot IAT), %d string dirujuk kode" % (
        r["arch"], r["image_base"], r["n_functions"], r["n_api_sites"], r["n_iat"], r["n_strrefs"]))
    st = r["entry_stub"]
    if r["entry"]:
        a("   entry %s: %s%s" % (r["entry"], st["hex"], (" | " + st["note"]) if st["note"] else ""))
    for f in r["functions"][: (3 if compact else RELAB_TOP)]:
        a("   * %s %s (%s, caller %d, callee %d) skor %d%s%s%s" % (
            f["name"], f["va"], _human(f["size"]), f["callers"], f["callees"], f["score"],
            (" | " + "; ".join(f["tags"])) if f["tags"] else "", (" | API: " + ", ".join(x.split("!")[-1] for x in f["apis"][:8])) if f["apis"] else "",
            (" | anti: " + ", ".join(f["anti"])) if f["anti"] else ""))
        if f["strings"] and not compact:
            a("       string: " + " | ".join(_df(x, defang) for x in f["strings"][:3]))
    if compact:
        for x in r["anti"][:3]:
            a("   anti-analisis: %s x%d" % (x["technique"], x["count"]))
        return
    for x in r["anti"]:
        a("   anti-analisis: %s x%d (pertama %s)" % (x["technique"], x["count"], x["first"]))
    if r["api_hashes"]:
        a("   API hashing: " + ", ".join("%s @%s" % (h["api"], h["offset"]) for h in r["api_hashes"][:8]))
    if r["stack_strings"]:
        a("   stack string: " + " | ".join("%s [%s]" % (_df(x["text"], defang), x["tag"]) for x in r["stack_strings"][:8]))
    if r["string_refs"]:
        a("   string yang dirujuk kode:")
        for e in r["string_refs"][:8]:
            a("     %s [%s] %s <- %s" % (e["va"], e["tag"], _df(e["text"], defang), ", ".join(e["funcs"]) or "?"))
    if r["api_top"]:
        a("   API paling sering dipanggil: " + ", ".join("%s x%d" % (k.split("!")[-1], n) for k, n in r["api_top"][:10]))


def _score_v98(rep: dict, add) -> None:
    r = rep.get("relab")
    if not r:
        return
    keys = [x["technique"] for x in r["anti"]]
    if any(k.startswith("syscall") for k in keys):
        add(3, "syscall langsung (melewati hook API / EDR)")
    if any(k.startswith("Heaven") for k in keys):
        add(2, "Heaven's Gate (lompat ke mode 64-bit dari WoW64)")
    if r["api_hashes"]:
        add(3, "API hashing (konstanta hash API dikenal ditemukan)")
    if any("pola ransomware" in t for f in r["functions"] for t in f["tags"]):
        add(3, "satu fungsi menggabungkan kripto + enumerasi berkas")
    elif any(t in ("injeksi proses", "unduh & jalankan") for f in r["functions"] for t in f["tags"]):
        add(1, "satu fungsi merangkai API injeksi / unduh-jalankan")
    if any(x["tag"] not in ("menarik",) for x in r["stack_strings"]):
        add(2, "string sensitif disusun di stack (menghindari pencarian string)")
    n_anti = len([k for k in keys if not k.startswith(("CPUID", "ROR"))])
    if n_anti >= 3:
        add(2, "banyak teknik anti-analisis tingkat instruksi (%d)" % n_anti)


# ----------------------------- API / CLI v98 --------------------------------


def re_lab_path(path) -> dict:
    """Analisis RE Lab langsung dari path (tanpa hash / triase penuh). Mengembalikan dict (atau {'error': ...})."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        info, _c, err = _relab_any(d, size)
        return info or {"error": (err or "tidak ada bagian kode yang bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64"}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def re_text(path, defang: bool = True, compact: bool = False) -> str:
    r = re_lab_path(path)
    if "error" in r:
        return "RE Lab gagal: " + r["error"]
    L: list[str] = []
    _render_v98({"relab": r}, L.append, compact, defang)
    return "\n".join(L)


def xref_text(path, query: str, max_items: int = 40) -> str:
    """Cari xref: nama API (mis. 'VirtualAlloc'), potongan string, atau VA fungsi. Menunjukkan fungsi pemanggil / pemakai."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        info, ctx, err = _relab_any(d, size)
        if not ctx:
            return "XREF gagal: %s." % (err or "tidak bisa dianalisis")
        q = str(query).strip()
        ql = q.lower()
        out = []
        for api, vs in ctx["sites"].items():
            if ql in api.lower():
                out.append("API %s: %d lokasi" % (api, len(vs)))
                for va, fs in vs[:max_items]:
                    out.append("   0x%X dalam %s" % (va, ctx["F"][fs]["name"] if fs in ctx["F"] else "?"))
        for e in ctx["sref"].values():
            if ql in e["text"].lower():
                out.append("string 0x%X (%s): %s" % (e["va"], e["kind"], _clean(e["text"])[:100]))
                for fs in sorted(e["funcs"])[:max_items]:
                    out.append("   dipakai oleh %s (0x%X)" % (ctx["F"][fs]["name"], fs))
        try:
            tv = int(q, 0)
            fobj_ = ctx["F"].get(tv)
            if fobj_:
                out.append("fungsi %s 0x%X: %d caller" % (fobj_["name"], tv, fobj_["callers"]))
                for c, fo in ctx["F"].items():
                    if tv in fo["callees"]:
                        out.append("   dipanggil dari %s (0x%X)" % (fo["name"], c))
        except ValueError:
            pass
        return "\n".join(out[:max_items * 3]) if out else "XREF: tidak ada hasil untuk '%s'." % _clean(q)[:60]
    except Exception as e:
        return "XREF gagal: %s: %s" % (type(e).__name__, str(e)[:120])


_CS_ARCHS = {   # nama -> (atribut ARCH, [atribut MODE], label)
    "x86": ("CS_ARCH_X86", ["CS_MODE_32"], "x86"), "x64": ("CS_ARCH_X86", ["CS_MODE_64"], "x64"),
    "arm": ("CS_ARCH_ARM", ["CS_MODE_ARM"], "ARM"), "armbe": ("CS_ARCH_ARM", ["CS_MODE_ARM", "CS_MODE_BIG_ENDIAN"], "ARM BE"),
    "thumb": ("CS_ARCH_ARM", ["CS_MODE_THUMB"], "Thumb"),
    "arm64": ("CS_ARCH_ARM64", ["CS_MODE_ARM"], "AArch64"),
    "mips": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_BIG_ENDIAN"], "MIPS32 BE"), "mipsel": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_LITTLE_ENDIAN"], "MIPS32 LE"),
    "mips64": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_BIG_ENDIAN"], "MIPS64 BE"), "mips64el": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_LITTLE_ENDIAN"], "MIPS64 LE"),
    "ppc": ("CS_ARCH_PPC", ["CS_MODE_32", "CS_MODE_BIG_ENDIAN"], "PowerPC32"), "ppc64": ("CS_ARCH_PPC", ["CS_MODE_64", "CS_MODE_BIG_ENDIAN"], "PowerPC64"),
    "riscv32": ("CS_ARCH_RISCV", ["CS_MODE_RISCV32"], "RISC-V 32"), "riscv64": ("CS_ARCH_RISCV", ["CS_MODE_RISCV64"], "RISC-V 64"),
    "sparc": ("CS_ARCH_SPARC", ["CS_MODE_BIG_ENDIAN"], "SPARC"),
}
_ELF_TO_ARCH = {3: "x86", 62: "x64", 40: "arm", 183: "arm64", 8: "mips", 20: "ppc", 243: "riscv64"}
_MACHO_TO_ARCH = {7: "x86", 0x01000007: "x64", 12: "arm", 0x0100000C: "arm64", 18: "ppc", 0x01000012: "ppc64"}


def _gen_elf_map(d: bytes):
    """ELF -> (arsitektur, entry VA, [(vaddr, offset, filesz)]) atau None."""
    if len(d) < 52 or d[:4] != b"\x7fELF":
        return None
    is64, en = d[4] == 2, ("<" if d[5] == 1 else ">")
    mach = struct.unpack_from(en + "H", d, 18)[0]
    if is64:
        entry, phoff = struct.unpack_from(en + "QQ", d, 24)
        phentsz, phnum = struct.unpack_from(en + "HH", d, 54)
    else:
        entry, phoff = struct.unpack_from(en + "II", d, 24)[0], struct.unpack_from(en + "I", d, 28)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 42)
    segs = []
    for i in range(min(phnum, 128)):
        o = phoff + i * phentsz
        if o + (56 if is64 else 32) > len(d):
            break
        if is64:
            pt, pf, poff, va, _pa, fsz, _m, _a = struct.unpack_from(en + "IIQQQQQQ", d, o)
        else:
            pt, poff, va, _pa, fsz, _m, pf, _a = struct.unpack_from(en + "IIIIIIII", d, o)
        if pt == 1 and fsz:
            segs.append((va, poff, fsz))
    arch = _ELF_TO_ARCH.get(mach, "")
    if arch == "arm" and en == ">":
        arch = "armbe"
    elif arch == "mips":
        arch = ("mips64" if is64 else "mips") if en == ">" else ("mips64el" if is64 else "mipsel")
    elif arch == "ppc" and is64:
        arch = "ppc64"
    elif arch == "riscv64" and not is64:
        arch = "riscv32"
    return arch, entry, segs, "ELF"


def _gen_macho_map(d: bytes):
    """Mach-O tipis / fat (irisan pertama) -> (arsitektur, entry VA, [(vmaddr, fileoff, filesize)]) atau None."""
    base = 0
    if d[:4] in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None
        base = struct.unpack_from(">I", d, 16)[0] if d[3] == 0xBE else struct.unpack_from(">Q", d, 16)[0]
    m = d[base:base + 4]
    if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        e = "<"
    elif m in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
        e = ">"
    else:
        return None
    is64 = 0xCF in (m[0], m[3])
    cpu, _sub, _ft, ncmds, szcmds, _fl = struct.unpack_from(e + "IIIIII", d, base + 4)
    off, end = base + (32 if is64 else 28), min(len(d), base + (32 if is64 else 28) + 0)
    end = min(len(d), off + szcmds)
    segs, text_va, entry_off, first_text = [], None, None, None
    for _ in range(min(ncmds, 600)):
        if off + 8 > end:
            break
        cmd, csz = struct.unpack_from(e + "II", d, off)
        if csz < 8 or off + csz > end:
            break
        if cmd in (0x1, 0x19) and csz >= (72 if cmd == 0x19 else 56):
            fmt = e + ("16sQQQQ" if cmd == 0x19 else "16sIIII")
            nm, va, _vsz, fo, fsz = struct.unpack_from(fmt, d, off + 8)
            if fsz:
                segs.append((va, base + fo, fsz))
            if nm.startswith(b"__TEXT"):
                text_va = va
        elif cmd == 0x80000028 and csz >= 16:
            entry_off = struct.unpack_from(e + "Q", d, off + 8)[0]
        off += csz
    entry = 0
    if entry_off is not None and text_va is not None:
        entry = text_va + entry_off
    elif segs:
        entry = segs[0][0]
    arch = _MACHO_TO_ARCH.get(cpu, "")
    return arch, entry, segs, "Mach-O"


def _disasm_generic(d: bytes, at, count: int, arch, was_pe: bool = False) -> str:
    """Disassembly di luar RE Lab PE: ELF, Mach-O, atau berkas mentah (alamat 'at' = offset berkas)."""
    fmt, entry, segs, a = "mentah", 0, [], None
    mp = None
    try:
        mp = _gen_elf_map(d) or _gen_macho_map(d)
    except (struct.error, IndexError):
        mp = None
    if mp:
        a, entry, segs, fmt = mp
    elif was_pe:
        fmt = "PE (bukan x86 / x64)"
    a = (str(arch).lower().strip() if arch else None) or a or "x64"
    if a not in _CS_ARCHS:
        return "DISASM gagal: arsitektur '%s' belum didukung. Pilihan: %s" % (_clean(a)[:20], " ".join(sorted(_CS_ARCHS)))
    s = str(at).strip().lower()
    note_raw = ""
    if s.startswith("off:"):
        off = int(s[4:], 0)
        va = next((v + (off - o) for v, o, n in segs if o <= off < o + n), off)
    elif s in ("entry", "start", ""):
        if segs:
            va = entry
        else:
            va, note_raw = 0, " (berkas mentah: mulai dari offset 0; pakai off:0x.. untuk lokasi lain)"
    else:
        va = int(s, 0)
    if segs:
        off = next((o + (va - v) for v, o, n in segs if v <= va < v + n), None)
    else:
        off = va
    if off is None or off < 0 or off >= len(d):
        return "DISASM gagal: alamat 0x%X tidak berada di data berkas." % va
    count = max(1, min(int(count), 400))
    code = d[off:off + count * 16 + 16]
    try:
        import capstone
    except ImportError:
        hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
        return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
    ca, modes, label = _CS_ARCHS[a]
    if not hasattr(capstone, ca) or not all(hasattr(capstone, m_) for m_ in modes):
        return "DISASM gagal: capstone yang terpasang belum mendukung %s (coba pip install -U capstone)." % label
    mode = 0
    for m_ in modes:
        mode |= getattr(capstone, m_)
    md = capstone.Cs(getattr(capstone, ca), mode)
    lines = []
    for i in md.disasm(code, va):
        lines.append("   %08X  %-24s %s %s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str))
        if len(lines) >= count:
            break
    if not lines:
        return "DISASM @0x%X (%s, %s): tidak ada instruksi valid di sini; coba arch lain (arch=thumb / arm64 / x86 ...) atau alamat lain.\n%s" % (
            va, fmt, label, "\n".join("   %08X  %s" % (va + k, code[k:k + 16].hex(" ")) for k in range(0, min(len(code), 48), 16)))
    return "DISASM @0x%X (%s, %s)%s:\n%s" % (va, fmt, label, note_raw, "\n".join(lines))


def disasm_text(path, at="entry", count: int = 40, arch=None) -> str:
    """Disassembly dari entry / VA (0x...), 'rva:0x..', 'off:0x..'. Butuh pustaka opsional capstone; tanpa itu menampilkan hex.
    PE x86 / x64: RE Lab penuh (nama API / fungsi). ELF, Mach-O (tipis / fat), dan berkas mentah (shellcode, firmware, dump):
    disassembly generik lewat capstone. arch (opsional, memaksa arsitektur): x86 x64 arm thumb arm64 mips mips64 mipsel ppc ppc64 riscv32 riscv64 sparc."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        pe = _parse_pe(d, size)
        info, ctx, _err = _relab_any(d, size)
        if not ctx or (arch and str(arch).lower() not in ("x86", "x64")):
            return _disasm_generic(d, at, count, arch, bool(pe and not pe.get("broken")))
        L = ctx["L"]
        s = str(at).strip().lower()
        if s in ("entry", "start", ""):
            va = L["entry_va"]
        elif s.startswith("rva:"):
            va = L["base"] + int(s[4:], 0)
        elif s.startswith("off:"):
            o_ = int(s[4:], 0)
            va = next((L["base"] + x["va"] + (o_ - x["rptr"]) for x in L["secs"] if x["rptr"] <= o_ < x["rptr"] + x["rsize"]), 0)
        else:
            va = int(s, 0)
            va = va if va >= L["base"] else L["base"] + va
        off = _va_off(L, va)
        if not va or off is None:
            return "DISASM gagal: alamat tidak berada di data berkas."
        count = max(1, min(int(count), 400))
        code = d[off:off + count * 15 + 16]
        names = dict(L["iat"])
        for tv, tn in ctx["thunks"].items():
            names[tv] = tn.split("!")[-1] + "@plt"
        for fv, fo in ctx["F"].items():
            names[fv] = fo["name"]
        try:
            import capstone
        except ImportError:
            hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
            return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64 if L["is64"] else capstone.CS_MODE_32)
        lines = []
        for i in md.disasm(code, va):
            note = ""
            m = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", i.op_str)
            if m:
                t = i.address + i.size + (int(m.group(2), 16) * (1 if m.group(1) == "+" else -1))
                note = names.get(t, "")
            else:
                m = re.search(r"0x[0-9a-f]+", i.op_str)
                if m and i.mnemonic in ("call", "jmp"):
                    note = names.get(int(m.group(0), 16), "")
                elif m and not L["is64"] and "[" in i.op_str:
                    note = names.get(int(m.group(0), 16), "")
            lines.append("   %08X  %-24s %s %s%s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str, ("   ; " + note) if note else ""))
            if len(lines) >= count:
                break
        return "DISASM @0x%X (%s%s):\n%s" % (va, "ELF " if d[:4] == b"\x7fELF" else "", "x64" if L["is64"] else "x86", "\n".join(lines))
    except Exception as e:
        return "DISASM gagal: %s: %s" % (type(e).__name__, str(e)[:120])


# ---------------------------------------------------------------------------
# v98.2: aturan kemampuan berbasis nama API, diturunkan dari mandiant/capa-rules (Apache-2.0, https://github.com/mandiant/capa-rules).
# Hanya aturan yang murni daftar API (or / and) dan punya pemetaan ATT&CK yang dipilih; aturan capa lain butuh analisis aliran kode.
# Dicocokkan di tingkat BERKAS (bukan fungsi), jadi tetap PETUNJUK. Tidak masuk skor. Atribusi: lihat NOTICE di docstring modul.
# (nama aturan, namespace, ATT&CK, operator, himpunan API huruf kecil)
# ---------------------------------------------------------------------------

_CAPA_RULES = (
    ('acquire credentials from Windows Credential Manager', 'collection', ('T1555.004',), 'or', ('credenumerate',)),
    ('get geographical location', 'collection', ('T1614',), 'or', ('getlocaleinfo', 'getlocaleinfoex', 'getusergeoid', 'getgeoinfo')),
    ('register raw input devices', 'collection/keylog', ('T1056.001',), 'or', ('registerrawinputdevices',)),
    ('log keystrokes via direct input', 'collection/keylog', ('T1056.001',), 'or', ('directinput8create', 'directinputcreateex', 'directinputcreatew', 'directinputcreatea')),
    ('log keystrokes via polling', 'collection/keylog', ('T1056.001',), 'or', ('getasynckeystate', 'getkeystate', 'getkeyboardstate', 'vkkeyscan', 'vkkeyscanex', 'getkeynametext')),
    ('get domain trust relationships', 'collection/network', ('T1482',), 'or', ('dsenumeratedomaintrusts',)),
    ('capture microphone audio', 'collection/microphone', ('T1123',), 'or', ('waveinopen', 'waveinaddbuffer', 'waveinstart')),
    ('clear Windows event logs remotely', 'anti-analysis/anti-forensic/clear-logs', ('T1070.001',), 'and', ('evtopensession', 'evtclearlog')),
    ('encrypt data using RC4 via SystemFunction033', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction033',)),
    ('encrypt data using RC4 via SystemFunction032', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction032',)),
    ('impersonate user', 'host-interaction/user', ('T1134.001',), 'or', ('logonuser',)),
    ('get UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('ntenumeratesystemenvironmentvaluesex', 'ntquerysystemenvironmentvalueex', 'ntquerysystemenvironmentvalue', 'getfirmwareenvironmentvariable', 'getfirmwareenvironmentvariableex', 'exgetfirmwareenvironmentvariable')),
    ('set UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('exsetfirmwareenvironmentvariable', 'setfirmwareenvironmentvariable', 'setfirmwareenvironmentvariableex')),
    ('switch active desktop', 'host-interaction/gui', ('T1622',), 'and', ('createdesktop', 'switchdesktop')),
    ('attach user process memory', 'host-interaction/process/inject', ('T1055',), 'and', ('kestackattachprocess', 'keunstackdetachprocess')),
    ('install driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntloaddriver', 'zwloaddriver')),
    ('unload driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntunloaddriver', 'zwunloaddriver')),
    ('delete network filter via WFP API', 'host-interaction/network/traffic/filter', ('T1565.002', 'T1562.004'), 'or', ('fwpmfilterdeletebyid0', 'fwpmfilterdeletebykey0')),
    ('shutdown system', 'host-interaction/os', ('T1529',), 'or', ('exitwindowsex', 'exitwindows', 'initiatesystemshutdownex', 'initiatesystemshutdown', 'initiateshutdown')),
)


_CAPA_SETS = [(n, ns, att, op, frozenset(apis)) for n, ns, att, op, apis in _CAPA_RULES]


def _capa_match(api_names) -> list[dict]:
    """Cocokkan nama impor dengan aturan capa bawaan. 'or': minimal satu API; 'and': semua API harus ada."""
    out = []
    names = [str(a) for a in api_names]
    if not names:
        return out
    for n, ns, att, op, S in _CAPA_SETS:
        hit = sorted({x.split("!")[-1] for x in names if _api_match(x, S)})
        if not hit:
            continue
        if op == "and" and len({h.lower() for h in hit}) < len(S):
            continue
        out.append({"name": n, "namespace": ns, "attack": list(att), "apis": hit[:6]})
    return out


def _capa_enrich(rep: dict, api_names) -> None:
    try:
        rep["capa"] = _capa_match(api_names)
    except Exception as e:
        rep["capa"] = []
        rep["warn"].append("aturan capa gagal: %s" % type(e).__name__)


def _render_capa(rep: dict, a, compact: bool) -> None:
    c = rep.get("capa")
    if not c:
        return
    a("Aturan capa (subset berbasis API, tingkat berkas; PETUNJUK, bukan bukti perilaku): %d cocok" % len(c))
    for x in c[: (3 if compact else 20)]:
        a("   - %s [%s] <- %s" % (_clean(x["name"]), ", ".join(x["attack"]), ", ".join(_clean(h) for h in x["apis"])))


# ---------------------------------------------------------------------------
# v98.2: unpack UPX statis lewat `upx -d` (opsional; hanya bila alat `upx` terpasang). Berkas TIDAK dijalankan: `upx -d` hanya
# mendekompresi. Dikerjakan pada salinan sementara dengan batas waktu dan ukuran; hasil disimpan di outdir lalu ditriase.
# ---------------------------------------------------------------------------

UNPACK_MAX = 256 * 1024 * 1024
UNPACK_TIMEOUT = 40


def unpack_upx(path, outdir) -> dict:
    import shutil
    import subprocess
    import tempfile
    try:
        upx = shutil.which("upx")
        if not upx:
            return {"ok": False, "error": "alat 'upx' tidak ditemukan di PATH (pasang UPX dari https://upx.github.io lalu coba lagi)"}
        f, size = _open_regular(path)
        if size > UNPACK_MAX:
            f.close()
            return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
        with f:
            head = f.read(size)
        if b"UPX!" not in head and b"UPX0" not in head:
            return {"ok": False, "error": "tidak ada penanda UPX di berkas; tidak dicoba"}
        out = Path(outdir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.bin"
            dst = Path(td) / "out.bin"
            src.write_bytes(head)
            r = subprocess.run([upx, "-d", "-q", "-o", str(dst), str(src)], capture_output=True, timeout=UNPACK_TIMEOUT)
            if r.returncode != 0 or not dst.exists():
                return {"ok": False, "error": "upx -d gagal: " + _clean(r.stderr.decode("latin-1", "replace"))[:200]}
            if dst.stat().st_size > UNPACK_MAX:
                return {"ok": False, "error": "hasil unpack melebihi batas %d MB; dibuang" % (UNPACK_MAX >> 20)}
            data = dst.read_bytes()
        name = "%s.unpacked" % (hashlib.sha256(data).hexdigest()[:16])
        (out / name).write_bytes(data)
        return {"ok": True, "path": str(out / name), "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "upx -d melewati batas waktu %d detik" % UNPACK_TIMEOUT}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def unpack_text(path, outdir) -> str:
    r = unpack_upx(path, outdir)
    if not r["ok"]:
        return "UNPACK gagal: " + r["error"]
    return "UNPACK UPX berhasil: %s (%s, sha256 %s)\n%s" % (r["path"], _human(r["size"]), r["sha256"], triage_text(r["path"], compact=True))


# ---------------------------------------------------------------------------
# v98.3: Android lebih dalam (AndroidManifest.xml biner + metode DEX), dekoder skrip / string tersandi, hash ikon PE,
#        dan pemindaian YARA opsional (butuh yara-python; tanpa itu tidak ada yang berubah). Statis, hanya baca.
# ---------------------------------------------------------------------------

_AXML_COMP = ("activity", "activity-alias", "service", "receiver", "provider")


def _axml_strings(d: bytes, off: int) -> list[str]:
    """Baca string pool (RES_STRING_POOL_TYPE) di offset `off`. Batas: 20000 string."""
    _t, hs, csz, n, _ns, flags, sstart, _st = struct.unpack_from("<HHIIIIII", d, off)
    n = min(n, 20000)
    utf8 = bool(flags & 0x100)
    out = []
    base = off + sstart
    for i in range(n):
        p = off + hs + 4 * i
        if p + 4 > len(d):
            break
        o = base + struct.unpack_from("<I", d, p)[0]
        if o >= len(d):
            out.append("")
            continue
        try:
            if utf8:
                l1 = d[o]
                o += 2 if l1 & 0x80 else 1
                b1 = d[o]
                if b1 & 0x80:
                    ln = ((b1 & 0x7F) << 8) | d[o + 1]
                    o += 2
                else:
                    ln = b1
                    o += 1
                out.append(d[o:o + min(ln, 600)].decode("utf-8", "replace"))
            else:
                ln = struct.unpack_from("<H", d, o)[0]
                o += 2
                if ln & 0x8000:
                    ln = ((ln & 0x7FFF) << 16) | struct.unpack_from("<H", d, o)[0]
                    o += 2
                out.append(d[o:o + 2 * min(ln, 600)].decode("utf-16le", "replace"))
        except (IndexError, struct.error):
            out.append("")
    return out


def _axml_summary(d: bytes) -> dict | None:
    """Uraikan AndroidManifest.xml biner (AXML) menjadi ringkasan: paket, versi, SDK, komponen, aksi intent, izin."""
    if len(d) < 16 or struct.unpack_from("<H", d, 0)[0] != 0x0003:
        return None
    total = min(struct.unpack_from("<I", d, 4)[0], len(d))
    pos, strings = struct.unpack_from("<H", d, 2)[0], []
    info: dict = {"package": "", "version": "", "min_sdk": "", "target_sdk": "", "debuggable": None, "cleartext": None, "backup": None,
                  "components": {k: [] for k in _AXML_COMP}, "exported": [], "actions": [], "perms": [], "app_class": ""}
    stack: list[str] = []
    cur_comp = None
    n_el = 0
    while pos + 8 <= total and n_el < 20000:
        ct, hs, csz = struct.unpack_from("<HHI", d, pos)
        if csz < 8 or pos + csz > len(d):
            break
        if ct == 0x0001:
            strings = _axml_strings(d, pos)
        elif ct == 0x0102 and csz >= 36:
            n_el += 1
            nm_i = struct.unpack_from("<I", d, pos + 20)[0]
            a_start, a_size, a_cnt = struct.unpack_from("<HHH", d, pos + 24)
            tag = strings[nm_i] if nm_i < len(strings) else "?"
            attrs = {}
            for k in range(min(a_cnt, 64)):
                ap = pos + 16 + a_start + k * (a_size or 20)
                if ap + 20 > len(d):
                    break
                _ans, an, raw, _sz, _r0, dtype, data = struct.unpack_from("<IIIHBBI", d, ap)
                key = strings[an] if an < len(strings) else "?"
                if raw != 0xFFFFFFFF and raw < len(strings):
                    val = strings[raw]
                elif dtype == 0x03 and data < len(strings):
                    val = strings[data]
                elif dtype == 0x12:
                    val = "true" if data else "false"
                elif dtype == 0x10:
                    val = str(data if data < 0x80000000 else data - (1 << 32))
                elif dtype == 0x11:
                    val = "0x%X" % data
                else:
                    val = "@0x%X" % data
                attrs[key] = val
            stack.append(tag)
            if tag == "manifest":
                info["package"] = attrs.get("package", "")
                info["version"] = "%s (%s)" % (attrs.get("versionName", "?"), attrs.get("versionCode", "?"))
            elif tag == "uses-sdk":
                info["min_sdk"], info["target_sdk"] = attrs.get("minSdkVersion", ""), attrs.get("targetSdkVersion", "")
            elif tag == "application":
                info["debuggable"] = attrs.get("debuggable")
                info["cleartext"] = attrs.get("usesCleartextTraffic")
                info["backup"] = attrs.get("allowBackup")
                info["app_class"] = attrs.get("name", "")
            elif tag in ("uses-permission", "uses-permission-sdk-23", "permission") and attrs.get("name"):
                info["perms"].append(attrs["name"])
            elif tag in _AXML_COMP:
                nm = attrs.get("name", "?")
                if len(info["components"][tag]) < 60:
                    info["components"][tag].append(nm)
                cur_comp = nm
                if attrs.get("exported") == "true" and len(info["exported"]) < 40:
                    info["exported"].append("%s %s" % (tag, nm))
            elif tag == "action" and attrs.get("name") and attrs["name"] not in info["actions"] and len(info["actions"]) < 60:
                info["actions"].append(attrs["name"])
        elif ct == 0x0103 and stack:
            if stack.pop() in _AXML_COMP:
                cur_comp = None
        pos += csz
    info["perms"] = sorted(set(info["perms"]))[:80]
    return info if (info["package"] or info["perms"] or any(info["components"].values())) else None


_DEX_API = {   # kelompok -> potongan "Lkelas;->metode" (cocok sebagian pada string metode)
    "kirim / baca SMS": ("Landroid/telephony/SmsManager;->sendTextMessage", "Landroid/telephony/SmsManager;->sendMultipartTextMessage", "Landroid/telephony/SmsMessage;->createFromPdu"),
    "identitas perangkat": ("TelephonyManager;->getDeviceId", "TelephonyManager;->getImei", "TelephonyManager;->getSubscriberId", "TelephonyManager;->getLine1Number", "Settings$Secure;->getString"),
    "muat kode dinamis": ("Ldalvik/system/DexClassLoader;-><init>", "Ldalvik/system/PathClassLoader;-><init>", "Ldalvik/system/InMemoryDexClassLoader;-><init>", "Ljava/lang/ClassLoader;->loadClass"),
    "eksekusi perintah": ("Ljava/lang/Runtime;->exec", "Ljava/lang/ProcessBuilder;->start"),
    "refleksi": ("Ljava/lang/reflect/Method;->invoke", "Ljava/lang/Class;->forName", "Ljava/lang/Class;->getDeclaredMethod"),
    "kripto": ("Ljavax/crypto/Cipher;->doFinal", "Ljavax/crypto/Cipher;->getInstance", "Ljavax/crypto/spec/SecretKeySpec;-><init>"),
    "aksesibilitas / overlay": ("AccessibilityService;->performGlobalAction", "AccessibilityNodeInfo;->performAction", "WindowManager;->addView"),
    "admin perangkat": ("DevicePolicyManager;->lockNow", "DevicePolicyManager;->resetPassword", "DevicePolicyManager;->wipeData"),
    "pasang paket": ("PackageInstaller;->createSession", "PackageManager;->installPackage", "Landroid/content/Intent;->setDataAndType"),
    "rekam audio / kamera": ("Landroid/media/MediaRecorder;->start", "Landroid/media/AudioRecord;->startRecording", "Landroid/hardware/Camera;->open"),
    "lokasi": ("LocationManager;->getLastKnownLocation", "LocationManager;->requestLocationUpdates"),
    "WebView + JS": ("WebView;->addJavascriptInterface", "WebSettings;->setJavaScriptEnabled"),
    "kontak / log panggilan": ("ContentResolver;->query",),
    "anti-analisis": ("Landroid/os/Debug;->isDebuggerConnected", "Landroid/os/Build;->FINGERPRINT", "Landroid/provider/Settings$Global;->getInt"),
}


def _uleb(d: bytes, o: int) -> tuple[int, int]:
    v, sh = 0, 0
    while o < len(d) and sh < 35:
        b = d[o]
        o += 1
        v |= (b & 0x7F) << sh
        if not b & 0x80:
            break
        sh += 7
    return v, o


def _dex_scan(d: bytes) -> dict | None:
    """Ringkasan DEX: jumlah string / tipe / metode / kelas, panggilan API Android sensitif dari tabel method_ids, dugaan obfuskasi."""
    if len(d) < 0x70 or d[:4] != b"dex\n":
        return None
    ss, so, ts, to, _ps, _po, _fs, _fo, ms, mo, cs, _co = struct.unpack_from("<12I", d, 0x38)
    ss, ts, ms = min(ss, 200000), min(ts, 200000), min(ms, 300000)

    cache: dict[int, str] = {}

    def sget(i: int) -> str:
        if i in cache:
            return cache[i]
        r = ""
        if 0 <= i < ss and so + 4 * i + 4 <= len(d):
            o = struct.unpack_from("<I", d, so + 4 * i)[0]
            if o < len(d):
                n, p = _uleb(d, o)
                r = d[p:p + min(n * 3, 400)].split(b"\0")[0].decode("utf-8", "replace")
        cache[i] = r
        return r

    types = []
    for i in range(ts):
        if to + 4 * i + 4 > len(d):
            break
        types.append(sget(struct.unpack_from("<I", d, to + 4 * i)[0]))
    meths = []
    for i in range(ms):
        p = mo + 8 * i
        if p + 8 > len(d):
            break
        ci, _pi, ni = struct.unpack_from("<HHI", d, p)
        meths.append("%s->%s" % (types[ci] if ci < len(types) else "?", sget(ni)))
    hits: dict[str, list[str]] = {}
    for m in meths:
        for grp, keys in _DEX_API.items():
            if any(k in m for k in keys):
                lst = hits.setdefault(grp, [])
                if len(lst) < 6 and m not in lst:
                    lst.append(m)
    app_types = [t for t in types if t.startswith("L") and not t.startswith(("Landroid", "Ljava", "Ljavax", "Lkotlin", "Landroidx", "Lcom/google", "Lorg/", "Ldalvik"))]
    short = sum(1 for t in app_types if len(t.rstrip(";").split("/")[-1]) <= 2)
    return {"strings": ss, "types": ts, "methods": ms, "classes": cs, "hits": hits,
            "obf": bool(len(app_types) >= 20 and short / len(app_types) > 0.5), "app_types": len(app_types)}


def _apk_deep(z, names: list[str], low: list[str], out: dict) -> None:
    """Dipanggil dari _parse_zip untuk APK: manifest biner dan DEX."""
    try:
        mf = _zread(z, names[low.index("androidmanifest.xml")], 2 * 1024 * 1024)
        man = _axml_summary(mf)
        if man:
            out["manifest"] = man
            if man["perms"]:
                out["perms"] = sorted(set(out["perms"]) | set(man["perms"]))[:80]
    except Exception:
        pass
    dex = {"strings": 0, "types": 0, "methods": 0, "classes": 0, "hits": {}, "obf": False, "files": 0}
    for i, n in enumerate(low):
        if not re.fullmatch(r"classes\d*\.dex", n) or dex["files"] >= 4:
            continue
        try:
            r = _dex_scan(_zread(z, names[i], 40 * 1024 * 1024))
        except Exception:
            r = None
        if not r:
            continue
        dex["files"] += 1
        for k in ("strings", "types", "methods", "classes"):
            dex[k] += r[k]
        dex["obf"] = dex["obf"] or r["obf"]
        for g, lst in r["hits"].items():
            cur = dex["hits"].setdefault(g, [])
            cur.extend(x for x in lst if x not in cur and len(cur) < 6)
    if dex["files"]:
        out["dex_info"] = dex


def _render_apk(zp: dict, a, compact: bool) -> None:
    m = zp.get("manifest")
    if m:
        a("Manifest: paket %s | versi %s | SDK min %s / target %s%s%s%s" % (
            _clean(m["package"]) or "?", _clean(m["version"]), m["min_sdk"] or "?", m["target_sdk"] or "?",
            " | DEBUGGABLE" if m["debuggable"] == "true" else "", " | cleartext HTTP" if m["cleartext"] == "true" else "",
            " | allowBackup" if m["backup"] == "true" else ""))
        cnt = {k: len(v) for k, v in m["components"].items() if v}
        if cnt:
            a("   komponen: " + ", ".join("%s %d" % (k, v) for k, v in cnt.items()))
        if not compact:
            for k in ("service", "receiver"):
                if m["components"][k]:
                    a("   %s: %s" % (k, ", ".join(_clean(x) for x in m["components"][k][:8])))
        if m["exported"] and not compact:
            a("   diekspor (exported=true): " + ", ".join(_clean(x) for x in m["exported"][:8]))
        acts = [x for x in m["actions"] if any(t in x for t in ("BOOT_COMPLETED", "SMS_RECEIVED", "PACKAGE_ADDED", "NEW_OUTGOING_CALL", "USER_PRESENT", "DEVICE_ADMIN", "ACCESSIBILITY", "PHONE_STATE", "QUICKBOOT"))]
        if acts:
            a("   aksi intent sensitif: " + ", ".join(_clean(x).replace("android.intent.action.", "") for x in acts[:8]))
    di = zp.get("dex_info")
    if di:
        a("DEX    : %d berkas, %d kelas, %d metode, %d string%s" % (di["files"], di["classes"], di["methods"], di["strings"], " | nama kelas pendek (dugaan obfuskasi ProGuard/R8 atau lain)" if di["obf"] else ""))
        for g, lst in list(di["hits"].items())[: (4 if compact else 20)]:
            a("   - %s: %s" % (g, ", ".join(_clean(x).replace("Landroid/", "") for x in lst[:3])))


# ----------------------- dekoder skrip / string tersandi -----------------------

_PS_ENC = re.compile(r"(?i)\s-(?:e|ec|en|enc|enco|encod|encode|encoded|encodedc\w*)\s+['\"]?([A-Za-z0-9+/]{16,}={0,2})")
_B64_CALL = re.compile(r"(?i)frombase64string\(\s*['\"]([A-Za-z0-9+/]{16,}={0,2})['\"]\s*\)")
_CHAR_PS = re.compile(r"(?i)(?:\[char\]\s*\(?\s*\d{2,3}\s*\)?\s*\+?\s*){5,}")
_CHAR_VB = re.compile(r"(?i)(?:chrw?\(\s*\d{2,3}\s*\)\s*&?\s*){5,}")
_CHAR_JS = re.compile(r"(?i)fromcharcode\(\s*((?:\d{2,3}\s*,\s*){4,}\d{2,3})\s*\)")
_HEX_ESC = re.compile(r"(?:\\x[0-9a-fA-F]{2}){8,}")


def _printable(t: str) -> bool:
    return len(t) >= 6 and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9


def _decode_scripts(strs: list[str]) -> list[dict]:
    """Dekode PowerShell -EncodedCommand, FromBase64String('..'), rangkaian [char] / Chr() / fromCharCode, dan \\xNN. Hanya teks; tidak dijalankan."""
    full = "\n".join(s[:4000] for s in strs)[:8 * 1024 * 1024]
    out: list[dict] = []

    def add(kind, text):
        t = text.strip()
        if _printable(t) and all(x["text"] != t[:600] for x in out) and len(out) < 12:
            out.append({"kind": kind, "text": t[:600]})

    for m in list(_PS_ENC.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        for enc in ("utf-16le", "utf-8"):
            t = raw.decode(enc, "ignore")
            if _printable(t):
                add("PowerShell -EncodedCommand", t)
                break
    for m in list(_B64_CALL.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        t = raw.decode("utf-16le", "ignore") if raw[1:2] == b"\x00" else raw.decode("utf-8", "ignore")
        add("FromBase64String", t)
    for rx, kind in ((_CHAR_PS, "rangkaian [char]"), (_CHAR_VB, "rangkaian Chr()")):
        for m in list(rx.finditer(full))[:4]:
            codes = [int(x) for x in re.findall(r"\d{2,3}", m.group(0))]
            if all(32 <= c < 127 or c in (9, 10, 13) for c in codes):
                add(kind, "".join(chr(c) for c in codes))
    for m in list(_CHAR_JS.finditer(full))[:4]:
        codes = [int(x) for x in re.findall(r"\d+", m.group(1))]
        if all(32 <= c < 127 for c in codes):
            add("fromCharCode", "".join(chr(c) for c in codes))
    for m in list(_HEX_ESC.finditer(full))[:4]:
        try:
            add("escape \\xNN", bytes(int(x, 16) for x in re.findall(r"\\x([0-9a-fA-F]{2})", m.group(0))).decode("latin-1"))
        except ValueError:
            pass
    return out


def _script_enrich(rep: dict, strs: list[str]) -> None:
    try:
        dec = _decode_scripts(strs)
    except Exception as e:
        dec = []
        rep["warn"].append("dekoder skrip gagal: %s" % type(e).__name__)
    rep["decoded"] = dec
    if dec:
        ind = rep["ind"]
        for x in dec:   # URL di dalam teks hasil dekode ikut jadi IOC
            for u in _URL.findall(x["text"]):
                u = u.rstrip(".,;)")
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
        rep["warn"].append("string tersandi berhasil didekode (%d): %s" % (len(dec), ", ".join(sorted({x["kind"] for x in dec}))))


def _render_decoded(rep: dict, a, compact: bool, defang: bool) -> None:
    for x in (rep.get("decoded") or [])[: (2 if compact else 8)]:
        a("Hasil dekode (%s): %s" % (x["kind"], _df(_clean(x["text"])[:240 if compact else 400], defang)))


# ----------------------- hash ikon PE -----------------------


def _icon_hash(d: bytes, pe: dict | None) -> dict | None:
    """MD5 data ikon terbesar + hash gabungan semua ikon: pengelompokan sampel yang memakai ikon sama (mis. ikon dokumen palsu)."""
    if not pe or pe.get("broken"):
        return None
    icons = [x for x in pe.get("res", []) if x.get("type") == "ICON" and x.get("size", 0) > 0]
    if not icons:
        return None
    hs = []
    for x in icons[:48]:
        blob = d[x["off"]:x["off"] + min(x["size"], 1 << 20)]
        if blob:
            hs.append((x["size"], hashlib.md5(blob).hexdigest()))
    if not hs:
        return None
    hs.sort(reverse=True)
    return {"main": hs[0][1], "all": hashlib.md5("".join(h for _s, h in sorted(hs, key=lambda t: t[1])).encode()).hexdigest(), "n": len(hs)}


# ----------------------- YARA opsional -----------------------


def yara_scan(path, rules, max_matches: int = 30) -> dict:
    """Jalankan aturan YARA milikmu (berkas .yar / .yara, atau folder berisi itu) pada berkas. Butuh `pip install yara-python`."""
    try:
        try:
            import yara
        except ImportError:
            return {"ok": False, "error": "pustaka opsional 'yara-python' belum terpasang (pip install yara-python)"}
        rp = Path(str(rules)).expanduser()
        if rp.is_dir():
            cand = sorted(x for x in rp.rglob("*") if x.suffix.lower() in (".yar", ".yara"))[:500]
            files = {"r%d" % i: str(p) for i, p in enumerate(cand)}
        elif rp.is_file():
            files = {"r0": str(rp)}
        else:
            return {"ok": False, "error": "berkas / folder aturan tidak ditemukan"}
        if not files:
            return {"ok": False, "error": "tidak ada berkas .yar / .yara di folder aturan"}
        f, size = _open_regular(path)
        f.close()
        rs = yara.compile(filepaths=files)
        ms = rs.match(filepath=str(Path(str(path)).resolve()), timeout=30)
        out = []
        for m in ms[:max_matches]:
            strs = []
            for sm in getattr(m, "strings", [])[:6]:
                ident = getattr(sm, "identifier", None) or (sm[1] if isinstance(sm, tuple) else "?")
                inst = getattr(sm, "instances", None)
                offs = [hex(i.offset) for i in inst[:3]] if inst else [hex(sm[0])] if isinstance(sm, tuple) else []
                strs.append("%s@%s" % (ident, ",".join(offs)))
            out.append({"rule": m.rule, "tags": list(m.tags), "desc": str(m.meta.get("description", ""))[:120], "strings": strs})
        return {"ok": True, "n_rules": len(files), "matches": out}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def yara_text(path, rules) -> str:
    r = yara_scan(path, rules)
    if not r["ok"]:
        return "YARA gagal: " + _clean(r["error"])
    if not r["matches"]:
        return "YARA: tidak ada aturan yang cocok (%d berkas aturan diperiksa)." % r["n_rules"]
    L = ["YARA: %d aturan cocok" % len(r["matches"])]
    for m in r["matches"]:
        L.append("   - %s%s%s%s" % (_clean(m["rule"]), (" [" + ",".join(m["tags"]) + "]") if m["tags"] else "",
                                    (" | " + _clean(m["desc"])) if m["desc"] else "", (" | " + ", ".join(m["strings"])) if m["strings"] else ""))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# v98.4: RE Lab untuk ELF x86 / x86-64 (little-endian). Memakai mesin RE Lab yang sama: peta panggilan API (PLT / GOT -> nama impor),
# nama fungsi dari .symtab / .dynsym bila ada, xref string, anti-analisis, peringkat fungsi. Statis, hanya pustaka standar.
# ---------------------------------------------------------------------------

_RE_GROUPS["injeksi proses"][0].update({"process_vm_writev", "process_vm_readv"})
_RE_GROUPS["jaringan / C2"][0].update({"bind", "listen", "accept", "sendto", "recvfrom", "inet_addr", "inet_pton", "curl_easy_perform", "curl_easy_setopt", "gethostbyaddr"})
_RE_GROUPS["eksekusi proses"][0].update({"execve", "execv", "execvp", "execl", "execlp", "execle", "popen", "posix_spawn", "posix_spawnp"})
_RE_GROUPS["kripto / enkripsi"][0].update({"evp_encryptinit_ex", "evp_cipherinit_ex", "evp_encryptupdate", "evp_decryptupdate", "aes_set_encrypt_key", "aes_encrypt", "aes_cbc_encrypt"})
_RE_GROUPS["enumerasi berkas"][0].update({"opendir", "readdir", "scandir", "ftw", "nftw", "glob"})
_RE_GROUPS["resolusi API dinamis"][0].update({"dlopen", "dlsym"})
_RE_GROUPS["alokasi / unpack memori"][0].update({"mmap", "mprotect", "mremap"})
_RE_GROUPS["token / hak istimewa"][0].update({"setuid", "setgid", "seteuid", "setresuid", "setresgid", "capset"})
_RE_GROUPS["anti-debug / anti-VM"][0].update({"ptrace", "prctl"})
_RE_GROUPS["ptrace (anti-debug / injeksi ELF)"] = ({"ptrace"}, 1, 3, "T1622 / T1055.008")
_RE_INTR = re.compile(_RE_INTR.pattern + r"|/bin/(?:ba|da|z)?sh\b|/etc/(?:passwd|shadow)|/proc/self|/dev/tcp|crontab|authorized_keys|ld_preload|\.ssh/|/tmp/\.", re.I)


def _elf_layout(d: bytes) -> dict | None:
    """Peta alamat ELF untuk RE Lab: segmen LOAD, bagian eksekusi, impor (slot GOT -> nama), simbol fungsi. None bila bukan x86 / x86-64 LE."""
    if len(d) < 64 or d[:4] != b"\x7fELF" or d[5] != 1 or d[4] not in (1, 2):
        return None
    is64 = d[4] == 2
    mach = struct.unpack_from("<H", d, 18)[0]
    if mach not in (3, 62) or (mach == 62) != is64:
        return None
    try:
        if is64:
            entry, phoff, shoff = struct.unpack_from("<QQQ", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 54)
        else:
            entry, phoff, shoff = struct.unpack_from("<III", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 42)
        segs = []
        for i in range(min(phnum, 128)):
            o = phoff + i * phentsz
            if o + (56 if is64 else 32) > len(d):
                break
            if is64:
                pt, pf, poff, va, _pa, fsz, msz, _al = struct.unpack_from("<IIQQQQQQ", d, o)
            else:
                pt, poff, va, _pa, fsz, msz, pf, _al = struct.unpack_from("<IIIIIIII", d, o)
            if pt == 1 and msz:
                segs.append((va, poff, fsz, msz, pf))
        if not segs:
            return None
        base = min(x[0] for x in segs) & ~0xFFF
        size_img = max(x[0] + x[3] for x in segs) - base

        def r2o(rva):
            va = rva + base
            for sv, so, sf, _sm, _pf in segs:
                if sv <= va < sv + sf:
                    o = so + (va - sv)
                    return o if o < len(d) else None
            return None

        sh = []
        if shoff and shnum and shentsz >= (64 if is64 else 40):
            for i in range(min(shnum, 4096)):
                o = shoff + i * shentsz
                if o + (64 if is64 else 40) > len(d):
                    break
                v = struct.unpack_from("<IIQQQQIIQQ" if is64 else "<IIIIIIIIII", d, o)
                sh.append({"name": v[0], "type": v[1], "flags": v[2], "addr": v[3], "off": v[4], "size": v[5], "link": v[6], "info": v[7], "entsz": v[9]})

        def cstr(o, lim=200):
            if o is None or o >= len(d):
                return ""
            e = d.find(b"\0", o, o + lim)
            return d[o:(e if e != -1 else o + lim)].decode("latin-1", "replace")

        shs_off = sh[shstr]["off"] if shstr < len(sh) else 0
        for x in sh:
            x["nm"] = cstr(shs_off + x["name"], 64) if shs_off else ""

        def symtab(si):
            """(nama, nilai, ukuran, tipe, bind, shndx) untuk tabel simbol bagian ke-si."""
            t = sh[si]
            st = sh[t["link"]] if t["link"] < len(sh) else None
            esz = 24 if is64 else 16
            out = []
            if not st:
                return out
            for k in range(min(t["size"] // esz, 60000)):
                o = t["off"] + k * esz
                if o + esz > len(d):
                    break
                if is64:
                    nm, info, _ot, shndx, val, sz = struct.unpack_from("<IBBHQQ", d, o)
                else:
                    nm, val, sz, info, _ot, shndx = struct.unpack_from("<IIIBBH", d, o)
                out.append((cstr(st["off"] + nm), val, sz, info & 0xF, info >> 4, shndx))
            return out
        exports: dict[int, str] = {}
        symcache: dict[int, list] = {}
        for si, t in enumerate(sh):
            if t["type"] in (2, 11):
                symcache[si] = symtab(si)
                for nm, val, _sz, typ, _bd, shndx in symcache[si]:
                    if typ == 2 and shndx != 0 and val and nm and len(exports) < 30000:
                        exports.setdefault(val, nm)
        iat: dict[int, str] = {}
        for t in sh:
            if t["type"] not in (4, 9) or t["link"] not in symcache:
                continue
            rs = (24 if is64 else 12) if t["type"] == 4 else (16 if is64 else 8)
            syms = symcache[t["link"]]
            for k in range(min(t["size"] // rs, 40000)):
                o = t["off"] + k * rs
                if o + rs > len(d):
                    break
                if is64:
                    roff, rinfo = struct.unpack_from("<QQ", d, o)
                    rsym, rtyp = rinfo >> 32, rinfo & 0xFFFFFFFF
                else:
                    roff, rinfo = struct.unpack_from("<II", d, o)
                    rsym, rtyp = rinfo >> 8, rinfo & 0xFF
                if rtyp in (6, 7) and 0 < rsym < len(syms):
                    nm, _v, _sz, _ty, _bd, shndx = syms[rsym]
                    nm = nm.split("@")[0]
                    if shndx == 0 and nm and not nm.startswith(("_ITM_", "__gmon_start__", "__libc_start_main", "__cxa_finalize", "__stack_chk", "__cxa_atexit")):
                        iat[roff] = nm
        secs, xsecs = [], []
        for x in sh:
            if x["flags"] & 2 and x["addr"] and x["size"]:
                rsz = 0 if x["type"] == 8 else x["size"]
                sec = {"name": x["nm"] or "?", "va": x["addr"] - base, "vsize": x["size"], "rsize": rsz, "rptr": x["off"],
                       "flags": ("R" if True else "-") + ("W" if x["flags"] & 1 else "-") + ("X" if x["flags"] & 4 else "-")}
                secs.append(sec)
                if x["flags"] & 4 and x["type"] == 1 and x["off"] < len(d):
                    xsecs.append(sec)
        if not xsecs:   # tanpa section header: pakai segmen LOAD yang dapat dieksekusi
            for sv, so, sf, sm, pf in segs:
                if pf & 1 and sf and so < len(d):
                    sec = {"name": "LOAD_X", "va": sv - base, "vsize": sm, "rsize": sf, "rptr": so, "flags": "R-X"}
                    secs.append(sec)
                    xsecs.append(sec)
        if not xsecs:
            return None
        return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "exports": exports, "r2o": r2o,
                "entry_va": entry if entry else 0, "entry_off": r2o(entry - base) if entry and entry >= base else None, "stripped": not any(t["type"] == 2 for t in sh)}
    except (struct.error, IndexError, OverflowError):
        return None


def _relab_elf(d: bytes, t0: float | None = None):
    L = _elf_layout(d)
    if L is None:
        return None, None
    info, ctx = _re_lab(d, None, t0, L=L, arch_label="ELF %s (%d-bit)%s" % ("x86-64" if L["is64"] else "x86", 64 if L["is64"] else 32, ", tanpa .symtab" if L["stripped"] else ""))
    if info is not None and L["stripped"]:
        info["notes"].append("ELF tanpa .symtab: nama fungsi hanya dari ekspor dinamis; sisanya sub_<alamat>")
    return info, ctx


def _relab_any(d: bytes, size: int):
    """(info, ctx, pesan_galat): PE x86 / x64 atau ELF x86 / x86-64."""
    pe = _parse_pe(d, size)
    if pe and not pe.get("broken"):
        info, ctx = _re_lab(d, pe)
        return info, ctx, "" if ctx else "PE bukan x86 / x64 atau tanpa bagian eksekusi"
    if d[:4] == b"\x7fELF":
        info, ctx = _relab_elf(d)
        return info, ctx, "" if ctx else "ELF bukan x86 / x86-64 little-endian, atau tanpa kode yang bisa dianalisis"
    return None, None, "bukan PE / ELF x86 / x64 yang valid"


# ----------------------------- API JSON untuk Iris / Hermes -----------------

_API_ACTIONS = ("capabilities", "triage", "json", "ioc", "yara", "md", "similar", "hex", "compare", "list", "extract", "dir", "ctph", "re", "xref", "disasm", "unpack", "yarascan", "assets", "assets_extract", "assets_carve", "formats")


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
                    "rea_binary": _has_binary(), "rea_assets": _assets_mod() is not None, "roots_restricted": bool(os.environ.get("REA_ROOTS"))}
        if act == "triage":
            p = _api_path(req["path"])
            if p.is_dir():
                return {"ok": True, "action": act, "text": trim(triage_dir_text(str(p), defang=bool(req.get("defang", True))))}
            rep = triage(p)
            return {"ok": True, "action": act, "score": rep["score"], "level": rep["level"], "sha256": rep["sha256"], "kind": rep["kind"],
                    "text": trim(render(rep, compact=bool(req.get("compact", False)), defang=bool(req.get("defang", True)), max_chars=mc, card=bool(req.get("card", False))))}
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
        if act == "re":
            p = _api_path(req["path"])
            return {"ok": True, "action": act, "data": re_lab_path(p), "text": trim(re_text(p, defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "xref":
            return {"ok": True, "action": act, "text": trim(xref_text(_api_path(req["path"]), str(req["query"])))}
        if act == "disasm":
            return {"ok": True, "action": act, "text": trim(disasm_text(_api_path(req["path"]), req.get("at", "entry"), int(req.get("count", 40)), req.get("arch")))}
        if act == "unpack":
            return {"ok": True, "action": act, "text": trim(unpack_text(_api_path(req["path"]), _api_path(req["outdir"])))}
        if act == "yarascan":
            return {"ok": True, "action": act, "text": trim(yara_text(_api_path(req["path"]), _api_path(req["rules"])))}
        if act == "dir":
            return {"ok": True, "action": act, "text": trim(triage_dir_text(str(_api_path(req["path"])), defang=bool(req.get("defang", True))))}
        if act == "assets":
            return {"ok": True, "action": act, "text": trim(assets_text(_api_path(req["path"]), max_chars=mc))}
        if act == "assets_extract":
            m = assets_extract(_api_path(req["path"]), _api_path(req["outdir"]), pattern=req.get("pattern"), convert=bool(req.get("convert", True)))
            return {"ok": m.get("status") in ("success", "partial"), "action": act, "manifest": m}
        if act == "assets_carve":
            od = _api_path(req["outdir"]) if req.get("outdir") else None
            m = assets_carve(_api_path(req["path"]), od)
            return {"ok": m.get("status") == "success", "action": act, "result": m}
        if act == "formats":
            mod = _assets_mod()
            return {"ok": mod is not None, "action": act, "formats": mod.formats() if mod else []}
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


# ======================================================================================================
# rea_assets.py (Asset Explorer v99.0) DIGABUNG ke berkas ini pada 22 Nov 2026 (v99.2, tanpa ubah perilaku).
# Nama yang bentrok dengan rea_triage diberi awalan _as_ (VERSION, _clean, _entropy, _human, carve). Akses dari luar bagian ini
# lewat _assets_mod() (fasad: nama aslinya tetap bisa dipakai, mis. mod.carve). Plugin (REA_PLUGINS) dimuat malas saat _assets_mod() pertama dipanggil.
# Dokumentasi asli modul:
# rea_assets.py - v99.0 Asset Explorer untuk REA (jembatan ke rea_triage.py).
#
# Tujuan: REA tidak hanya membedah .exe / .dll, tetapi bisa MEMBUKA ISI hampir semua berkas: model 3D, animasi, tekstur,
# audio, arsip / paket game, database, dan data tertanam di dalam berkas lain. Hanya pustaka standar, hanya-baca terhadap
# berkas sumber (hasil selalu ditulis ke folder keluaran terpisah), TANPA menjalankan apa pun dari berkas.
#
# API (semua tidak melempar kecuali dinyatakan):
#     identify(path) -> dict                        jenis berkas + kategori (deteksi lewat magic bytes, bukan ekstensi saja)
#     describe(path) -> dict / describe_text(path)  ringkasan isi: mesh, animasi, tekstur, daftar entri arsip, tabel DB ...
#     extract(path, outdir, pattern=None, convert=True) -> manifest dict
#                                                   mengeluarkan isi: gambar / buffer dari glTF, mesh -> .obj, animasi -> .json / .csv,
#                                                   tekstur DDS / TGA / BMP -> .png, entri arsip (PAK / WAD / ZIP / TAR ...), tabel SQLite -> .csv
#     carve(path, outdir=None, max_items=200) -> dict   cari & potong berkas yang TERTANAM di dalam berkas apa pun (PNG, JPEG, GIF, OGG, RIFF,
#                                                   GLB, SQLite, ZIP, MIDI ...) -- berguna untuk .exe / .dat / resource yang tidak punya format terdokumentasi
#     formats() -> list[dict]                       daftar parser terpasang (termasuk plugin)
#     load_plugins(folder) -> list[str]             muat parser tambahan (lihat bagian PLUGIN)
#
# Format bawaan:
#   3D / animasi : glTF / GLB, OBJ, STL, PLY, FBX (biner; ASCII hanya ringkasan), COLLADA (.dae), BVH
#   gambar       : PNG / APNG, JPEG, GIF, BMP, TGA, DDS (DXT1/3/5 + RGBA tak terkompresi), WebP, ICO
#   audio        : WAV, OGG (Vorbis / Opus), FLAC, MP3, MIDI
#   arsip / game : Quake PAK, WAD (Doom / Quake / Half-Life), Unreal .pak (v1-v9, tanpa enkripsi), ZIP (APK / JAR / OOXML ...), TAR, GZIP,
#                  header UnityFS / 7z / RAR (deteksi saja)
#   data         : SQLite
#
# Yang BELUM / tidak bisa dibuka langsung (dilaporkan jelas, bukan ditebak): paket terenkripsi / dikompres format sendiri, aset Unity /
# Unreal yang terserialisasi (butuh parser per versi mesin), tekstur BC4-BC7 / ASTC. Untuk itu tulis plugin (di bawah).
#
# PLUGIN (parser buatan sendiri, ala QuickBMS): buat folder berisi berkas .py, masing-masing memuat
#     def register_formats(reg):
#         reg("nama", "kategori", detect, inspect=None, extract=None, priority=50, about="")
#   detect(d, ext) -> bool        d = isi berkas (mmap / bytes, hanya-baca), ext = ekstensi huruf kecil
#   inspect(d, path) -> {"lines": [str], "info": {...}, "extract": "apa yang bisa diekstrak"}
#   extract(d, path, out, opts)   out.write("sub/nama.bin", bytes, kind="...") ; opts = {"pattern": ..., "convert": bool}
# Plugin adalah KODE yang dijalankan: dimuat hanya bila diminta eksplisit (--plugins FOLDER, env REA_PLUGINS, atau load_plugins()),
# TIDAK pernah lewat permintaan API agen.
#
# ======================================================================================================
import array
import base64
import collections
import csv
import fnmatch
import gzip
import hashlib
import importlib.util
import io
import json
import math
import mmap
import os
import re
import sqlite3
import stat
import struct
import sys
import tarfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import zlib
from contextlib import contextmanager
from pathlib import Path

_as_VERSION = "99.0"
MAX_OUT_FILE = 512 * 1024 * 1024      # satu berkas keluaran
MAX_OUT_TOTAL = 4 * 1024 ** 3         # total keluaran satu ekstraksi
MAX_ENTRIES = 200_000                 # entri arsip
MAX_PIXELS = 64 * 1024 * 1024         # piksel maksimum saat dekode tekstur
MAX_XML = 64 * 1024 * 1024
MAX_ACCESSOR = 5_000_000
MAX_CARVE_SCAN = 1024 * 1024 * 1024


def _u16(d, o): return struct.unpack_from("<H", d, o)[0]
def _u32(d, o): return struct.unpack_from("<I", d, o)[0]
def _u64(d, o): return struct.unpack_from("<Q", d, o)[0]
def _b32(d, o): return struct.unpack_from(">I", d, o)[0]


def _as_human(n: float) -> str:
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%d %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f GB" % n


def _as_clean(s, n=200) -> str:
    """Bersihkan teks dari berkas tak tepercaya (tanpa baris baru / karakter kontrol) sebelum masuk laporan."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8", "replace")
    return re.sub(r"[\x00-\x1f\x7f\u2028\u2029]", " ", str(s))[:n]


# ---------------------------------------------------------------------------
# Buka berkas (hanya berkas biasa, dipetakan ke memori hanya-baca) dan tulis keluaran dengan aman
# ---------------------------------------------------------------------------

@contextmanager
def _map(path):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(os.fspath(path), flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("bukan berkas biasa (FIFO / perangkat / folder): %s" % Path(path).name)
        f = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    try:
        if st.st_size == 0:
            yield b""
        else:
            m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                yield m
            finally:
                m.close()
    finally:
        f.close()


_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}


def _safe_rel(name) -> str:
    """Nama entri dari berkas tak tepercaya -> path relatif aman (tanpa '..', drive, karakter terlarang)."""
    s = str(name).replace("\\", "/").replace("\x00", "")
    parts = []
    for part in s.split("/"):
        part = part.strip()
        if part in ("", ".", ".."):
            continue
        part = re.sub(r'[<>:"|?*\x00-\x1f]', "_", part).rstrip(". ") or "_"
        if part.split(".")[0].upper() in _RESERVED:
            part = "_" + part
        parts.append(part[:120])
    return "/".join(parts) or "unnamed"


class _Out:
    """Penulis keluaran: semua path dipaksa tetap di bawah outdir, tidak menimpa berkas, batas ukuran, manifest."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.files: list[dict] = []
        self.skipped: list[dict] = []
        self.errors: list[str] = []
        self.total = 0

    def write(self, rel, data, kind: str = "", note: str = ""):
        rel = _safe_rel(rel)
        if len(data) > MAX_OUT_FILE or self.total + len(data) > MAX_OUT_TOTAL:
            self.skipped.append({"path": rel, "size": len(data), "reason": "melebihi batas ukuran keluaran"})
            return None
        target = (self.root / rel).resolve()
        if self.root not in target.parents:
            self.skipped.append({"path": rel, "size": len(data), "reason": "path di luar folder keluaran"})
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        stem, suf, k = target.stem, target.suffix, 1
        while True:
            try:
                with open(target, "xb") as fh:
                    fh.write(data)
                break
            except FileExistsError:
                k += 1
                target = target.with_name("%s_%d%s" % (stem, k, suf))
        self.total += len(data)
        self.files.append({"path": target.relative_to(self.root).as_posix(), "size": len(data), "kind": kind, "note": note,
                           "sha256": hashlib.sha256(data).hexdigest()})
        return target

    def write_text(self, rel, text, kind="", note=""):
        return self.write(rel, text.encode("utf-8"), kind, note)


# ---------------------------------------------------------------------------
# Registri parser
# ---------------------------------------------------------------------------

class _Fmt:
    __slots__ = ("name", "category", "detect", "inspect", "extract", "priority", "about", "plugin")

    def __init__(self, name, category, detect, inspect, extract, priority, about, plugin=False):
        self.name, self.category, self.detect, self.inspect, self.extract = name, category, detect, inspect, extract
        self.priority, self.about, self.plugin = priority, about, plugin


_FORMATS: list[_Fmt] = []
_LOADED_PLUGINS: set[str] = set()


def register(name, category, detect, inspect=None, extract=None, priority: int = 50, about: str = "", _plugin: bool = False):
    _FORMATS[:] = [f for f in _FORMATS if f.name != name]
    _FORMATS.append(_Fmt(name, category, detect, inspect, extract, priority, about, _plugin))
    _FORMATS.sort(key=lambda f: f.priority)


def formats() -> list[dict]:
    return [{"name": f.name, "category": f.category, "inspect": f.inspect is not None, "extract": f.extract is not None,
             "plugin": f.plugin, "about": f.about} for f in _FORMATS]


def load_plugins(folder) -> list[str]:
    """Muat semua *.py di folder; tiap berkas boleh mendefinisikan register_formats(reg). Mengembalikan nama plugin yang termuat.
    Ini MENJALANKAN kode di folder itu: arahkan hanya ke folder yang Anda percaya."""
    got = []
    p = Path(folder).expanduser().resolve()
    if not p.is_dir():
        return got
    for f in sorted(p.glob("*.py")):
        key = str(f)
        if key in _LOADED_PLUGINS:
            continue
        spec = importlib.util.spec_from_file_location("rea_plugin_" + re.sub(r"\W", "_", f.stem), f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            fn = getattr(mod, "register_formats", None)
            if fn:
                fn(lambda name, category, detect, inspect=None, extract=None, priority=50, about="": register(
                    name, category, detect, inspect, extract, priority, about, _plugin=True))
                got.append(f.name)
                _LOADED_PLUGINS.add(key)
        except Exception as e:   # plugin rusak tidak boleh menjatuhkan REA
            got.append("%s (GAGAL: %s)" % (f.name, _as_clean(e, 80)))
    return got


def _detect(d, ext: str) -> _Fmt | None:
    for f in _FORMATS:
        try:
            if f.detect(d, ext):
                return f
        except Exception:
            continue
    return None


def _sha256(d) -> str:
    h = hashlib.sha256()
    n = len(d)
    for i in range(0, n, 8 * 1024 * 1024):
        h.update(d[i:i + 8 * 1024 * 1024])
    return h.hexdigest()


def _as_entropy(b) -> float:
    if not b:
        return 0.0
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in collections.Counter(b).values())


# ---------------------------------------------------------------------------
# OBJ writer bersama
# ---------------------------------------------------------------------------

def _obj_name(s, fallback="mesh") -> str:
    s = re.sub(r"[^\w.\-]+", "_", str(s or "")).strip("._")
    return s[:60] or fallback


class _ObjBuilder:
    def __init__(self):
        self.lines: list[str] = []
        self.nv = self.nvt = self.nvn = 0
        self.faces = 0

    def group(self, name):
        self.lines.append("o %s" % _obj_name(name))

    def add(self, pos, uv=None, nrm=None, tris=(), polys=()):
        """pos: list (x,y,z); uv: list (u,v) atau None; nrm: list (x,y,z) atau None; tris: list (a,b,c) 0-based; polys: list list indeks."""
        b0, t0, n0 = self.nv, self.nvt, self.nvn
        self.lines += ["v %.7g %.7g %.7g" % (p[0], p[1], p[2]) for p in pos]
        if uv:
            self.lines += ["vt %.7g %.7g" % (u[0], u[1]) for u in uv]
        if nrm:
            self.lines += ["vn %.7g %.7g %.7g" % (n[0], n[1], n[2]) for n in nrm]

        def corner(i):
            a = b0 + i + 1
            if uv and nrm:
                return "%d/%d/%d" % (a, t0 + i + 1, n0 + i + 1)
            if uv:
                return "%d/%d" % (a, t0 + i + 1)
            if nrm:
                return "%d//%d" % (a, n0 + i + 1)
            return str(a)
        for t in tris:
            self.lines.append("f %s %s %s" % (corner(t[0]), corner(t[1]), corner(t[2])))
        for pl in polys:
            self.lines.append("f " + " ".join(corner(i) for i in pl))
        self.faces += len(tris) + len(polys)
        self.nv += len(pos)
        self.nvt += len(uv) if uv else 0
        self.nvn += len(nrm) if nrm else 0

    def add_raw(self, pos, uvs, nrms, faces):
        """Untuk sumber yang indeks UV / normalnya terpisah: faces = list list (vi, vti|None, vni|None) 0-based."""
        b0, t0, n0 = self.nv, self.nvt, self.nvn
        self.lines += ["v %.7g %.7g %.7g" % (p[0], p[1], p[2]) for p in pos]
        self.lines += ["vt %.7g %.7g" % (u[0], u[1]) for u in uvs]
        self.lines += ["vn %.7g %.7g %.7g" % (n[0], n[1], n[2]) for n in nrms]
        for f in faces:
            parts = []
            for vi, ti, ni in f:
                s = str(b0 + vi + 1)
                if ti is not None and ni is not None:
                    s += "/%d/%d" % (t0 + ti + 1, n0 + ni + 1)
                elif ti is not None:
                    s += "/%d" % (t0 + ti + 1)
                elif ni is not None:
                    s += "//%d" % (n0 + ni + 1)
                parts.append(s)
            self.lines.append("f " + " ".join(parts))
        self.faces += len(faces)
        self.nv += len(pos)
        self.nvt += len(uvs)
        self.nvn += len(nrms)

    def text(self, header="") -> str:
        return ("# %s\n" % header if header else "") + "\n".join(self.lines) + "\n"


def _csv_text(rows, header) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# glTF / GLB
# ---------------------------------------------------------------------------

_CT = {5120: ("b", 1, 127.0), 5121: ("B", 1, 255.0), 5122: ("h", 2, 32767.0), 5123: ("H", 2, 65535.0), 5125: ("I", 4, 1.0), 5126: ("f", 4, 1.0)}
_NT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def _is_glb(d, ext): return d[:4] == b"glTF" and len(d) >= 20
def _is_gltf(d, ext):
    return ext == ".gltf" and d[:1024].lstrip()[:1] == b"{"


def _gltf_load(d, p: Path):
    """-> (json, blok BIN GLB atau None). Melempar ValueError bila rusak."""
    binchunk = None
    if d[:4] == b"glTF":
        ver, total = struct.unpack_from("<II", d, 4)
        if ver != 2:
            raise ValueError("GLB versi %d tidak didukung (hanya 2)" % ver)
        pos, js = 12, None
        end = min(total, len(d))
        while pos + 8 <= end:
            ln, typ = struct.unpack_from("<I4s", d, pos)
            body = d[pos + 8:pos + 8 + ln]
            if typ == b"JSON":
                js = bytes(body)
            elif typ == b"BIN\x00" and binchunk is None:
                binchunk = bytes(body)
            pos += 8 + ln + ((4 - ln % 4) % 4)
        if js is None:
            raise ValueError("GLB tanpa chunk JSON")
    else:
        js = bytes(d)
    j = json.loads(js.decode("utf-8-sig"))
    if not isinstance(j, dict):
        raise ValueError("glTF bukan objek JSON")
    return j, binchunk


def _data_uri(uri: str):
    head, _, body = uri.partition(",")
    if ";base64" in head:
        return base64.b64decode(body + "=" * (-len(body) % 4))
    return urllib.parse.unquote_to_bytes(body)


def _external(p: Path, uri: str, cap=MAX_OUT_FILE):
    """Baca berkas eksternal (mis. .bin / .png di sebelah .gltf) hanya bila tetap di dalam folder yang sama."""
    base = p.resolve().parent
    q = (base / urllib.parse.unquote(uri)).resolve()
    if base != q and base not in q.parents:
        return None
    try:
        with open(q, "rb") as f:
            return f.read(cap)
    except OSError:
        return None


def _gltf_bufs(j, binchunk, p: Path):
    out = []
    for b in j.get("buffers", []) or []:
        uri = b.get("uri")
        try:
            if uri is None:
                out.append(binchunk or b"")
            elif uri.startswith("data:"):
                out.append(_data_uri(uri))
            else:
                out.append(_external(p, uri) or b"")
        except Exception:
            out.append(b"")
    return out


def _gltf_acc(j, bufs, idx):
    a = j["accessors"][idx]
    ct = a["componentType"]
    fc, sz, norm = _CT[ct]
    n, nc = int(a["count"]), _NT[a["type"]]
    if n > MAX_ACCESSOR:
        raise ValueError("accessor terlalu besar (%d)" % n)
    if "bufferView" not in a:
        return [tuple([0] * nc)] * n
    bv = j["bufferViews"][a["bufferView"]]
    buf = bufs[bv["buffer"]]
    off = int(bv.get("byteOffset", 0)) + int(a.get("byteOffset", 0))
    S = struct.Struct("<" + fc * nc)
    stride = int(bv.get("byteStride") or S.size)
    if n and off + stride * (n - 1) + S.size > len(buf):
        raise ValueError("accessor melewati batas buffer")
    rows = [S.unpack_from(buf, off + i * stride) for i in range(n)]
    if a.get("normalized") and ct != 5126:
        lo = -1.0 if fc in "bh" else 0.0
        rows = [tuple(max(lo, v / norm) for v in r) for r in rows]
    return rows


def _gltf_prim_tris(j, bufs, prim):
    mode = prim.get("mode", 4)
    pa = prim.get("attributes", {})
    if "POSITION" not in pa:
        return None
    nvert = j["accessors"][pa["POSITION"]]["count"]
    idx = [r[0] for r in _gltf_acc(j, bufs, prim["indices"])] if "indices" in prim else list(range(nvert))
    if mode == 4:
        return [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    if mode == 5:
        return [((idx[i], idx[i + 1], idx[i + 2]) if i % 2 == 0 else (idx[i + 1], idx[i], idx[i + 2])) for i in range(len(idx) - 2)]
    if mode == 6:
        return [(idx[0], idx[i], idx[i + 1]) for i in range(1, len(idx) - 1)]
    return None


def _gltf_inspect(d, p):
    j, binc = _gltf_load(d, p)
    g = lambda k: j.get(k) or []
    L = []
    ast = j.get("asset", {})
    L.append("glTF %s | generator: %s" % (_as_clean(ast.get("version", "?")), _as_clean(ast.get("generator", "-"), 80)))
    nodes, meshes = g("nodes"), g("meshes")
    L.append("scene: %d | node: %d | mesh: %d | material: %d | tekstur: %d | gambar: %d | skin: %d | kamera: %d | animasi: %d" % (
        len(g("scenes")), len(nodes), len(meshes), len(g("materials")), len(g("textures")), len(g("images")), len(g("skins")),
        len(g("cameras")), len(g("animations"))))
    tv = tt = 0
    for mi, m in enumerate(meshes[:200]):
        v = t = 0
        for pr in m.get("primitives", []):
            try:
                v += j["accessors"][pr["attributes"]["POSITION"]]["count"]
                t += (j["accessors"][pr["indices"]]["count"] if "indices" in pr else j["accessors"][pr["attributes"]["POSITION"]]["count"]) // 3
            except (KeyError, IndexError, TypeError):
                pass
        tv, tt = tv + v, tt + t
        if mi < 12:
            L.append("  mesh[%d] %s: %d primitif, %d vertex, ~%d segitiga" % (mi, _as_clean(m.get("name", "-"), 40), len(m.get("primitives", [])), v, t))
    L.append("total: %d vertex, ~%d segitiga" % (tv, tt))
    for i, im in enumerate(g("images")[:10]):
        src = "bufferView" if "bufferView" in im else ("data URI" if str(im.get("uri", "")).startswith("data:") else _as_clean(im.get("uri", "?"), 60))
        L.append("  gambar[%d] %s (%s)" % (i, _as_clean(im.get("mimeType", "?"), 20), src))
    for i, sk in enumerate(g("skins")[:5]):
        L.append("  skin[%d]: %d joint" % (i, len(sk.get("joints", []))))
    for i, an in enumerate(g("animations")[:20]):
        dur = 0.0
        paths = collections.Counter()
        for c in an.get("channels", []):
            paths[c.get("target", {}).get("path", "?")] += 1
            try:
                s = an["samplers"][c["sampler"]]
                mx = j["accessors"][s["input"]].get("max")
                if mx:
                    dur = max(dur, float(mx[0]))
            except (KeyError, IndexError, TypeError, ValueError):
                pass
        L.append("  animasi[%d] %s: %d channel (%s), durasi %.2f dtk" % (
            i, _as_clean(an.get("name", "-"), 40), len(an.get("channels", [])), ", ".join("%s x%d" % kv for kv in paths.items()), dur))
    if j.get("extensionsUsed"):
        L.append("ekstensi dipakai: " + ", ".join(_as_clean(x, 40) for x in j["extensionsUsed"][:12]))
    if "KHR_draco_mesh_compression" in (j.get("extensionsRequired") or []) or "EXT_meshopt_compression" in (j.get("extensionsRequired") or []):
        L.append("PERINGATAN: mesh terkompresi (Draco / meshopt): ekspor OBJ tidak tersedia, gambar & animasi tetap bisa diekstrak.")
    return {"lines": L, "extract": "gambar tertanam, mesh -> .obj (tanpa transformasi node), animasi -> .json + .csv, scene.gltf.json"}


def _gltf_extract(d, p, out: _Out, opts):
    j, binc = _gltf_load(d, p)
    bufs = _gltf_bufs(j, binc, p)
    out.write_text("scene.gltf.json", json.dumps(j, ensure_ascii=False, indent=1), "json", "JSON glTF")
    # gambar
    for i, im in enumerate(j.get("images", []) or []):
        try:
            if "bufferView" in im:
                bv = j["bufferViews"][im["bufferView"]]
                off = int(bv.get("byteOffset", 0))
                data = bytes(bufs[bv["buffer"]][off:off + int(bv["byteLength"])])
            elif str(im.get("uri", "")).startswith("data:"):
                data = _data_uri(im["uri"])
            elif im.get("uri"):
                data = _external(p, im["uri"])
                if data is None:
                    out.skipped.append({"path": im["uri"], "reason": "berkas eksternal tidak ada / di luar folder"})
                    continue
            else:
                continue
            mt = im.get("mimeType", "")
            ext = ".png" if "png" in mt or data[:4] == b"\x89PNG" else ".jpg" if "jp" in mt or data[:2] == b"\xff\xd8" else ".bin"
            out.write("images/%s%s" % (_obj_name(im.get("name") or "image%d" % i), ext), data, "image")
        except Exception as e:
            out.errors.append("gambar[%d]: %s" % (i, _as_clean(e, 100)))
    # mesh
    for mi, m in enumerate(j.get("meshes", []) or []):
        try:
            ob = _ObjBuilder()
            for pi, pr in enumerate(m.get("primitives", [])):
                tris = _gltf_prim_tris(j, bufs, pr)
                if tris is None:
                    continue
                pa = pr["attributes"]
                pos = _gltf_acc(j, bufs, pa["POSITION"])
                uv = [(u[0], 1.0 - u[1]) for u in _gltf_acc(j, bufs, pa["TEXCOORD_0"])] if "TEXCOORD_0" in pa else None
                nrm = _gltf_acc(j, bufs, pa["NORMAL"]) if "NORMAL" in pa else None
                ob.group("%s_p%d" % (m.get("name") or "mesh%d" % mi, pi))
                ob.add(pos, uv, nrm, tris)
            if ob.faces:
                out.write_text("models/%s.obj" % _obj_name(m.get("name") or "mesh%d" % mi, "mesh%d" % mi),
                               ob.text("diekspor REA dari glTF mesh[%d]; tanpa transformasi node" % mi), "model3d",
                               "%d vertex, %d segitiga" % (ob.nv, ob.faces))
        except Exception as e:
            out.errors.append("mesh[%d]: %s" % (mi, _as_clean(e, 100)))
    # animasi
    nodes = j.get("nodes", []) or []
    nname = lambda i: _as_clean((nodes[i].get("name") if 0 <= (i if i is not None else -1) < len(nodes) else None) or "node%s" % i, 60)
    for ai, an in enumerate(j.get("animations", []) or []):
        try:
            chans, rows, width = [], [], 1
            for c in an.get("channels", []):
                s = an["samplers"][c["sampler"]]
                times = [r[0] for r in _gltf_acc(j, bufs, s["input"])]
                vals = _gltf_acc(j, bufs, s["output"])
                tg = c.get("target", {})
                nm, path = nname(tg.get("node")), tg.get("path", "?")
                interp = s.get("interpolation", "LINEAR")
                chans.append({"node": nm, "node_index": tg.get("node"), "path": path, "interpolation": interp,
                              "times": times, "values": [list(v) for v in vals]})
                if vals:
                    width = max(width, len(vals[0]))
                per = (len(vals) // len(times)) if times else 1
                for k, v in enumerate(vals):
                    rows.append((times[k // per] if per and k // per < len(times) else "", nm, path, interp, *v))
            base = "animations/%s" % _obj_name(an.get("name") or "anim%d" % ai, "anim%d" % ai)
            out.write_text(base + ".json", json.dumps({"name": an.get("name"), "channels": chans}, ensure_ascii=False), "animation",
                           "%d channel" % len(chans))
            out.write_text(base + ".csv", _csv_text(rows, ["time", "node", "path", "interpolation"] + ["v%d" % i for i in range(width)]), "animation",
                           "CUBICSPLINE: tiap kunci = 3 baris (in-tangent, nilai, out-tangent)" if any(c["interpolation"] == "CUBICSPLINE" for c in chans) else "")
        except Exception as e:
            out.errors.append("animasi[%d]: %s" % (ai, _as_clean(e, 100)))


register("glTF/GLB", "model3d", lambda d, e: _is_glb(d, e) or _is_gltf(d, e), _gltf_inspect, _gltf_extract, 10,
         "model 3D + animasi + tekstur tertanam")


# ---------------------------------------------------------------------------
# OBJ / STL / PLY
# ---------------------------------------------------------------------------

def _is_obj(d, e):
    if e != ".obj":
        return False
    head = bytes(d[:4096])
    return bool(re.search(rb"^(v|vt|vn|f|o|g|mtllib)\s", head, re.M))


def _obj_inspect(d, p):
    cnt = collections.Counter()
    mtl, groups = [], []
    for ln in bytes(d[:256 * 1024 * 1024]).split(b"\n"):
        t = ln.split(None, 1)
        if not t:
            continue
        k = t[0]
        if k in (b"v", b"vt", b"vn", b"vp", b"f", b"l", b"p", b"o", b"g", b"usemtl", b"s"):
            cnt[k.decode()] += 1
        if k == b"mtllib" and len(t) > 1 and len(mtl) < 5:
            mtl.append(_as_clean(t[1], 60))
        if k in (b"o", b"g") and len(t) > 1 and len(groups) < 10:
            groups.append(_as_clean(t[1], 40))
    L = ["Wavefront OBJ: %d vertex, %d UV, %d normal, %d face, %d objek, %d grup, %d pemakaian material" % (
        cnt["v"], cnt["vt"], cnt["vn"], cnt["f"], cnt["o"], cnt["g"], cnt["usemtl"])]
    if mtl:
        L.append("pustaka material: " + ", ".join(mtl))
    if groups:
        L.append("objek / grup: " + ", ".join(groups))
    return {"lines": L, "extract": "(sudah berupa OBJ; tidak ada yang perlu dikonversi)"}


register("OBJ", "model3d", _is_obj, _obj_inspect, None, 20, "Wavefront OBJ (teks)")


def _stl_kind(d):
    n = len(d)
    if n >= 84 and 84 + 50 * _u32(d, 80) == n:
        return "binary"
    head = bytes(d[:2048]).lstrip().lower()
    if head.startswith(b"solid") and b"facet" in bytes(d[:4096]).lower():
        return "ascii"
    return None


def _stl_tris(d):
    k = _stl_kind(d)
    if k == "binary":
        n = _u32(d, 80)
        if n > 20_000_000:
            raise ValueError("STL terlalu besar")
        S = struct.Struct("<12fH")
        return [S.unpack_from(d, 84 + 50 * i)[3:12] for i in range(n)]
    txt = bytes(d[:512 * 1024 * 1024]).decode("latin-1")
    vs = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)
    vs = [(float(a), float(b), float(c)) for a, b, c in vs]
    return [tuple(x for v in vs[i:i + 3] for x in v) for i in range(0, len(vs) - 2, 3)]


def _stl_inspect(d, p):
    k = _stl_kind(d)
    tris = _stl_tris(d)
    if not tris:
        return {"lines": ["STL (%s): kosong" % k]}
    xs = [t[i] for t in tris for i in (0, 3, 6)]
    ys = [t[i] for t in tris for i in (1, 4, 7)]
    zs = [t[i] for t in tris for i in (2, 5, 8)]
    L = ["STL %s: %d segitiga" % (k, len(tris)),
         "kotak batas: x[%.4g..%.4g] y[%.4g..%.4g] z[%.4g..%.4g]" % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))]
    if k == "binary":
        hd = _as_clean(bytes(d[:80]).rstrip(b"\x00 "), 80)
        if hd:
            L.append("header: " + hd)
    return {"lines": L, "extract": "-> .obj (vertex kembar digabung)"}


def _stl_extract(d, p, out, opts):
    tris = _stl_tris(d)
    index, pos, faces = {}, [], []
    for t in tris:
        f = []
        for i in (0, 3, 6):
            v = (t[i], t[i + 1], t[i + 2])
            if v not in index:
                index[v] = len(pos)
                pos.append(v)
            f.append(index[v])
        faces.append(tuple(f))
    ob = _ObjBuilder()
    ob.group(p.stem)
    ob.add(pos, None, None, faces)
    out.write_text("%s.obj" % _obj_name(p.stem, "model"), ob.text("diekspor REA dari STL"), "model3d", "%d vertex, %d segitiga" % (len(pos), len(faces)))


register("STL", "model3d", lambda d, e: _stl_kind(d) is not None if len(d) >= 84 or e == ".stl" else False, _stl_inspect, _stl_extract, 25,
         "model 3D segitiga (cetak 3D)")


_PLY_T = {"char": "b", "int8": "b", "uchar": "B", "uint8": "B", "short": "h", "int16": "h", "ushort": "H", "uint16": "H",
          "int": "i", "int32": "i", "uint": "I", "uint32": "I", "float": "f", "float32": "f", "double": "d", "float64": "d"}


def _ply_header(d):
    end = bytes(d[:65536]).find(b"end_header")
    if end < 0:
        raise ValueError("header PLY tidak lengkap")
    nl = bytes(d[end:end + 20])
    m = re.match(rb"end_header\r?\n", nl)
    if not m:
        raise ValueError("end_header tidak diikuti baris baru")
    body = end + m.end()
    lines = bytes(d[:end]).decode("latin-1").splitlines()
    if not lines or lines[0].strip() != "ply":
        raise ValueError("bukan PLY")
    fmt, elems, comments = None, [], []
    for ln in lines[1:]:
        t = ln.split()
        if not t:
            continue
        if t[0] == "format":
            fmt = t[1]
        elif t[0] == "comment":
            comments.append(_as_clean(" ".join(t[1:]), 80))
        elif t[0] == "element":
            elems.append({"name": t[1], "count": int(t[2]), "props": []})
        elif t[0] == "property" and elems:
            if t[1] == "list":
                elems[-1]["props"].append((t[4], "list", t[2], t[3]))
            else:
                elems[-1]["props"].append((t[2], "scalar", t[1], None))
    if fmt not in ("ascii", "binary_little_endian", "binary_big_endian"):
        raise ValueError("format PLY tidak dikenal")
    return fmt, elems, body, comments


def _ply_read(d):
    fmt, elems, pos, _ = _ply_header(d)
    data = {}
    if fmt == "ascii":
        toks = bytes(d[pos:]).split()
        ti = 0
        for el in elems:
            if el["count"] > 20_000_000:
                raise ValueError("elemen PLY terlalu besar")
            rows = []
            for _ in range(el["count"]):
                row = {}
                for name, kind, t1, t2 in el["props"]:
                    if kind == "list":
                        n = int(toks[ti]); ti += 1
                        row[name] = [float(x) if _PLY_T[t2] in "fd" else int(x) for x in toks[ti:ti + n]]
                        ti += n
                    else:
                        x = toks[ti]; ti += 1
                        row[name] = float(x) if _PLY_T[t1] in "fd" else int(x)
                rows.append(row)
            data[el["name"]] = rows
        return data
    e = "<" if fmt == "binary_little_endian" else ">"
    for el in elems:
        if el["count"] > 20_000_000:
            raise ValueError("elemen PLY terlalu besar")
        rows = []
        if all(k == "scalar" for _, k, _, _ in el["props"]):
            S = struct.Struct(e + "".join(_PLY_T[t1] for _, _, t1, _ in el["props"]))
            names = [n for n, _, _, _ in el["props"]]
            need = S.size * el["count"]
            if pos + need > len(d):
                raise ValueError("data PLY terpotong")
            for tup in S.iter_unpack(bytes(d[pos:pos + need])):
                rows.append(dict(zip(names, tup)))
            pos += need
        else:
            for _ in range(el["count"]):
                row = {}
                for name, kind, t1, t2 in el["props"]:
                    if kind == "list":
                        c = struct.unpack_from(e + _PLY_T[t1], d, pos)[0]
                        pos += struct.calcsize(_PLY_T[t1])
                        fc = _PLY_T[t2]
                        row[name] = list(struct.unpack_from("%s%d%s" % (e, c, fc), d, pos))
                        pos += c * struct.calcsize(fc)
                    else:
                        fc = _PLY_T[t1]
                        row[name] = struct.unpack_from(e + fc, d, pos)[0]
                        pos += struct.calcsize(fc)
                rows.append(row)
        data[el["name"]] = rows
    return data


def _ply_inspect(d, p):
    fmt, elems, _, comments = _ply_header(d)
    L = ["PLY (%s): " % fmt + ", ".join("%s x%d [%s]" % (_as_clean(e["name"], 20), e["count"], ", ".join(_as_clean(x[0], 14) for x in e["props"][:8])) for e in elems)]
    if comments:
        L.append("komentar: " + "; ".join(comments[:3]))
    return {"lines": L, "extract": "-> .obj (vertex + face; warna per-vertex tidak ikut)"}


def _ply_extract(d, p, out, opts):
    data = _ply_read(d)
    vs = data.get("vertex", [])
    pos = [(v.get("x", 0.0), v.get("y", 0.0), v.get("z", 0.0)) for v in vs]
    nrm = [(v["nx"], v["ny"], v["nz"]) for v in vs] if vs and "nx" in vs[0] else None
    uv = None
    for a, b in (("s", "t"), ("u", "v"), ("texture_u", "texture_v")):
        if vs and a in vs[0] and b in vs[0]:
            uv = [(v[a], v[b]) for v in vs]
            break
    polys = []
    for f in data.get("face", []):
        ix = f.get("vertex_indices") or f.get("vertex_index") or []
        if len(ix) >= 3:
            polys.append([int(i) for i in ix])
    ob = _ObjBuilder()
    ob.group(p.stem)
    ob.add(pos, uv, nrm, (), polys)
    out.write_text("%s.obj" % _obj_name(p.stem, "model"), ob.text("diekspor REA dari PLY"), "model3d", "%d vertex, %d face" % (len(pos), len(polys)))


register("PLY", "model3d", lambda d, e: d[:4] == b"ply\n" or d[:5] == b"ply\r\n", _ply_inspect, _ply_extract, 25, "Stanford PLY (mesh / point cloud)")


# ---------------------------------------------------------------------------
# FBX (biner) - model, rangka, animasi, tekstur tertanam
# ---------------------------------------------------------------------------

_FBX_MAGIC = b"Kaydara FBX Binary  \x00\x1a\x00"
_FBX_TICKS = 46186158000.0          # tick FBX per detik
_ARR = {ord("f"): ("f", 4), ord("d"): ("d", 8), ord("l"): ("q", 8), ord("i"): ("i", 4), ord("b"): ("B", 1)}


def _fbx_props(d, pos, n):
    props = []
    for _ in range(n):
        t = d[pos]
        pos += 1
        if t == 0x59:   # Y
            v = struct.unpack_from("<h", d, pos)[0]; pos += 2
        elif t == 0x43:   # C
            v = d[pos]; pos += 1
        elif t == 0x49:   # I
            v = struct.unpack_from("<i", d, pos)[0]; pos += 4
        elif t == 0x46:   # F
            v = struct.unpack_from("<f", d, pos)[0]; pos += 4
        elif t == 0x44:   # D
            v = struct.unpack_from("<d", d, pos)[0]; pos += 8
        elif t == 0x4C:   # L
            v = struct.unpack_from("<q", d, pos)[0]; pos += 8
        elif t in _ARR:
            al, enc, cl = struct.unpack_from("<III", d, pos)
            pos += 12
            code, isz = _ARR[t]
            want = al * isz
            if want > MAX_OUT_FILE:
                raise ValueError("array FBX terlalu besar")
            raw = bytes(d[pos:pos + cl])
            pos += cl
            if enc == 1:
                raw = zlib.decompressobj().decompress(raw, want + 1)
            if len(raw) != want:
                raise ValueError("panjang array FBX tidak cocok")
            if code == "B":
                v = raw
            else:
                v = array.array(code)
                v.frombytes(raw)
                if sys.byteorder == "big":
                    v.byteswap()
        elif t in (0x53, 0x52):   # S / R
            ln = _u32(d, pos); pos += 4
            raw = bytes(d[pos:pos + ln]); pos += ln
            v = raw.decode("utf-8", "replace") if t == 0x53 else raw
        else:
            raise ValueError("tipe properti FBX tidak dikenal: %r" % t)
        props.append(v)
    return props


def _fbx_parse(d, node_cap=3_000_000):
    ver = _u32(d, 23)
    big = ver >= 7500
    cnt = [0]

    def node(pos, depth):
        if big:
            end, npr, pl = struct.unpack_from("<QQQ", d, pos); pos += 24
        else:
            end, npr, pl = struct.unpack_from("<III", d, pos); pos += 12
        nl = d[pos]; pos += 1
        if end == 0:
            return None, pos
        if depth > 48 or end > len(d):
            raise ValueError("struktur FBX tidak wajar")
        cnt[0] += 1
        if cnt[0] > node_cap:
            raise ValueError("terlalu banyak node FBX")
        name = bytes(d[pos:pos + nl]).decode("latin-1")
        pos += nl
        pstart = pos
        props = _fbx_props(d, pstart, npr)
        pos = pstart + pl      # panjang daftar properti dipercaya dari header
        kids = []
        while pos < end:
            ch, pos = node(pos, depth + 1)
            if ch is not None:
                kids.append(ch)
        return (name, props, kids), end

    tops, pos = [], 27
    while pos + (25 if big else 13) <= len(d):
        n, pos = node(pos, 0)
        if n is None:
            break
        tops.append(n)
    return ver, tops


def _fbx_child(n, name):
    for c in n[2]:
        if c[0] == name:
            return c
    return None


def _fbx_cname(n) -> str:
    s = n[1][1] if len(n[1]) > 1 and isinstance(n[1][1], str) else ""
    return _as_clean(s.split("\x00\x01")[0] or "unnamed", 60)


def _fbx_objects(tops):
    ob = next((t for t in tops if t[0] == "Objects"), None)
    return ob[2] if ob else []


def _is_fbx_bin(d, e): return d[:23] == _FBX_MAGIC


def _is_fbx_ascii(d, e): return d[:12] == b"; FBX " or (e == ".fbx" and b"FBXHeaderExtension" in bytes(d[:512]))


def _fbx_inspect(d, p):
    ver, tops = _fbx_parse(d)
    objs = _fbx_objects(tops)
    kinds = collections.Counter(o[0] for o in objs)
    models = collections.Counter((o[1][2] if len(o[1]) > 2 and isinstance(o[1][2], str) else "?") for o in objs if o[0] == "Model")
    L = ["FBX biner versi %d | objek: %s" % (ver, ", ".join("%s x%d" % kv for kv in kinds.most_common(14)))]
    if models:
        L.append("tipe Model: " + ", ".join("%s x%d" % (_as_clean(k, 20), v) for k, v in models.most_common(8)))
    nv = nf = 0
    for o in objs:
        if o[0] == "Geometry":
            v = _fbx_child(o, "Vertices")
            pv = _fbx_child(o, "PolygonVertexIndex")
            if v and v[1]:
                nv += len(v[1][0]) // 3
            if pv and pv[1]:
                nf += sum(1 for x in pv[1][0] if x < 0)
    if nv:
        L.append("geometri: %d vertex, %d poligon" % (nv, nf))
    bones = [_fbx_cname(o) for o in objs if o[0] == "Model" and len(o[1]) > 2 and o[1][2] == "LimbNode"]
    if bones:
        L.append("rangka: %d tulang (%s%s)" % (len(bones), ", ".join(bones[:8]), ", ..." if len(bones) > 8 else ""))
    curves = [o for o in objs if o[0] == "AnimationCurve"]
    if curves:
        keys, tmax = 0, 0
        for c in curves:
            kt = _fbx_child(c, "KeyTime")
            if kt and kt[1] and len(kt[1][0]):
                keys += len(kt[1][0]); tmax = max(tmax, max(kt[1][0]))
        L.append("animasi: %d stack, %d layer, %d curve, %d kunci, durasi ~%.2f dtk" % (
            kinds["AnimationStack"], kinds["AnimationLayer"], len(curves), keys, tmax / _FBX_TICKS))
    emb = 0
    for o in objs:
        if o[0] == "Video":
            c = _fbx_child(o, "Content")
            if c and c[1] and isinstance(c[1][0], (bytes, bytearray)) and len(c[1][0]) > 0:
                emb += 1
    if kinds["Texture"] or kinds["Video"]:
        L.append("tekstur: %d referensi, %d gambar tertanam" % (kinds["Texture"], emb))
    return {"lines": L, "extract": "geometri -> .obj (+UV / normal ByPolygonVertex), animasi -> .csv per curve, gambar tertanam"}


def _fbx_extract(d, p, out, opts):
    ver, tops = _fbx_parse(d)
    objs = _fbx_objects(tops)
    byid = {o[1][0]: o for o in objs if o[1] and isinstance(o[1][0], int)}
    for o in objs:
        if o[0] == "Geometry":
            try:
                vn, pv = _fbx_child(o, "Vertices"), _fbx_child(o, "PolygonVertexIndex")
                if not vn or not pv or not vn[1] or not pv[1]:
                    continue
                vv, pi = vn[1][0], pv[1][0]
                pos = [(vv[i], vv[i + 1], vv[i + 2]) for i in range(0, len(vv) - 2, 3)]
                polys, cur, ccount = [], [], 0
                for k, ix in enumerate(pi):
                    cur.append((ix if ix >= 0 else ~ix, k))
                    if ix < 0:
                        polys.append(cur)
                        cur = []

                def layer(lname, dname, iname):
                    le = _fbx_child(o, lname)
                    if not le:
                        return None, None
                    mt = _fbx_child(le, "MappingInformationType")
                    dd = _fbx_child(le, dname)
                    ii = _fbx_child(le, iname)
                    if not dd or not dd[1] or not mt or "ByPolygonVertex" not in str(mt[1][:1]):
                        return None, None
                    return dd[1][0], (ii[1][0] if ii and ii[1] else None)
                uvd, uvi = layer("LayerElementUV", "UV", "UVIndex")
                nmd, _ = layer("LayerElementNormal", "Normals", "NormalsIndex")
                uvs = [(uvd[i], uvd[i + 1]) for i in range(0, len(uvd) - 1, 2)] if uvd is not None else []
                nms = [(nmd[i], nmd[i + 1], nmd[i + 2]) for i in range(0, len(nmd) - 2, 3)] if nmd is not None else []
                faces = []
                for pl in polys:
                    f = []
                    for vi, k in pl:
                        ti = (uvi[k] if uvi is not None and k < len(uvi) else k) if uvs else None
                        if ti is not None and ti >= len(uvs):
                            ti = None
                        ni = k if nms and k < len(nms) else None
                        f.append((vi, ti, ni))
                    if len(f) >= 3:
                        faces.append(f)
                ob = _ObjBuilder()
                ob.group(_fbx_cname(o))
                ob.add_raw(pos, uvs, nms, faces)
                out.write_text("models/%s.obj" % _obj_name(_fbx_cname(o), "geometry"), ob.text("diekspor REA dari FBX"), "model3d",
                               "%d vertex, %d poligon" % (len(pos), len(faces)))
            except Exception as e:
                out.errors.append("geometri %s: %s" % (_fbx_cname(o), _as_clean(e, 100)))
        elif o[0] == "Video":
            c = _fbx_child(o, "Content")
            if c and c[1] and isinstance(c[1][0], (bytes, bytearray)) and len(c[1][0]) > 0:
                fn = _fbx_child(o, "RelativeFilename") or _fbx_child(o, "Filename")
                nm = os.path.basename(str(fn[1][0]).replace("\\", "/")) if fn and fn[1] else _fbx_cname(o)
                out.write("images/" + (nm or "video"), bytes(c[1][0]), "image", "tekstur tertanam FBX")
    # animasi: curve -> curvenode -> model lewat tabel Connections
    conn = next((t for t in tops if t[0] == "Connections"), None)
    parent = collections.defaultdict(list)
    if conn:
        for c in conn[2]:
            if c[0] == "C" and len(c[1]) >= 3 and c[1][0] in ("OO", "OP"):
                parent[c[1][1]].append((c[1][2], c[1][3] if len(c[1]) > 3 else ""))
    rows_by_node = collections.defaultdict(list)
    for o in objs:
        if o[0] != "AnimationCurve":
            continue
        try:
            kt, kv = _fbx_child(o, "KeyTime"), _fbx_child(o, "KeyValueFloat")
            if not kt or not kv or not kt[1] or not kv[1]:
                continue
            axis, node_name, prop = "?", "?", "?"
            for pid, pname in parent.get(o[1][0], []):
                cn = byid.get(pid)
                if cn and cn[0] == "AnimationCurveNode":
                    axis = str(pname).replace("d|", "")
                    for mid, mprop in parent.get(pid, []):
                        m = byid.get(mid)
                        if m and m[0] == "Model":
                            node_name, prop = _fbx_cname(m), str(mprop)
            for t, v in zip(kt[1][0], kv[1][0]):
                rows_by_node[node_name].append((node_name, prop, axis, "%.6f" % (t / _FBX_TICKS), "%.7g" % v))
        except Exception as e:
            out.errors.append("curve: %s" % _as_clean(e, 100))
    for nm, rows in rows_by_node.items():
        out.write_text("animations/%s.csv" % _obj_name(nm, "node"), _csv_text(rows, ["node", "property", "axis", "time_s", "value"]), "animation",
                       "%d sampel" % len(rows))


register("FBX", "model3d", _is_fbx_bin, _fbx_inspect, _fbx_extract, 10, "Autodesk FBX biner: mesh, rangka, animasi, tekstur")


def _fbx_ascii_inspect(d, p):
    txt = bytes(d[:64 * 1024 * 1024]).decode("latin-1")
    c = {k: len(re.findall(r"^\s*%s:" % k, txt, re.M)) for k in ("Model", "Geometry", "Material", "Texture", "AnimationStack", "AnimationCurve", "Deformer")}
    return {"lines": ["FBX ASCII: " + ", ".join("%s x%d" % kv for kv in c.items() if kv[1]), "ekstraksi untuk FBX ASCII belum ada; konversi ke FBX biner / glTF dulu."]}


register("FBX-ASCII", "model3d", _is_fbx_ascii, _fbx_ascii_inspect, None, 11, "FBX teks (hanya ringkasan)")


# ---------------------------------------------------------------------------
# COLLADA (.dae)
# ---------------------------------------------------------------------------

def _tag(e): return e.tag.rsplit("}", 1)[-1]


def _is_dae(d, e):
    return e == ".dae" or (b"<COLLADA" in bytes(d[:2048]))


def _dae_root(d):
    if len(d) > MAX_XML:
        raise ValueError("XML terlalu besar")
    raw = bytes(d)
    if b"<!ENTITY" in raw or b"<!DOCTYPE" in raw[:4096] and b"[" in raw[:4096].split(b"<!DOCTYPE", 1)[1][:2000]:
        raise ValueError("XML berisi DTD / entity (ditolak demi keamanan)")
    return ET.fromstring(raw)


def _dae_floats(e):
    return [float(x) for x in (e.text or "").split()]


def _dae_inspect(d, p):
    r = _dae_root(d)
    c = collections.Counter(_tag(e) for e in r.iter())
    L = ["COLLADA: %d geometri, %d controller (skin), %d animasi, %d gambar, %d material, %d node" % (
        c["geometry"], c["controller"], c["animation"], c["image"], c["material"], c["node"])]
    ax = next((e.text for e in r.iter() if _tag(e) == "up_axis"), None)
    un = next((e for e in r.iter() if _tag(e) == "unit"), None)
    if ax or un is not None:
        L.append("sumbu atas: %s | unit: %s" % (_as_clean(ax or "?", 8), _as_clean(un.get("meter", "?") if un is not None else "?", 12)))
    imgs = [(e.text or "").strip() for e in r.iter() if _tag(e) == "init_from" and (e.text or "").strip()][:8]
    if imgs:
        L.append("gambar dirujuk: " + ", ".join(_as_clean(i, 50) for i in imgs))
    return {"lines": L, "extract": "geometri (triangles / polylist) -> .obj; animasi belum diekspor (hanya dihitung)"}


def _dae_extract(d, p, out, opts):
    r = _dae_root(d)
    for geom in [e for e in r.iter() if _tag(e) == "geometry"]:
        mesh = next((e for e in geom if _tag(e) == "mesh"), None)
        if mesh is None:
            continue
        try:
            src = {}
            for s in mesh:
                if _tag(s) == "source":
                    fa = next((e for e in s.iter() if _tag(e) == "float_array"), None)
                    ac = next((e for e in s.iter() if _tag(e) == "accessor"), None)
                    if fa is not None:
                        src[s.get("id")] = (_dae_floats(fa), int(ac.get("stride", 3)) if ac is not None else 3)
            vmap = {}
            for v in mesh:
                if _tag(v) == "vertices":
                    for i in v:
                        if _tag(i) == "input" and i.get("semantic") == "POSITION":
                            vmap[v.get("id")] = i.get("source", "")[1:]
            chunk = lambda fl, st: [tuple(fl[i:i + st]) for i in range(0, len(fl) - st + 1, st)]
            ob = _ObjBuilder()
            ob.group(geom.get("name") or geom.get("id"))
            pos = uvs = nrm = None
            faces = []
            for prim in mesh:
                if _tag(prim) not in ("triangles", "polylist", "polygons"):
                    continue
                inputs = [i for i in prim if _tag(i) == "input"]
                stride = max(int(i.get("offset", 0)) for i in inputs) + 1 if inputs else 0
                off = {}
                for i in inputs:
                    sem, o, sid = i.get("semantic"), int(i.get("offset", 0)), i.get("source", "")[1:]
                    if sem == "VERTEX":
                        fl, st = src[vmap[sid]]; pos = chunk(fl, st); off["v"] = o
                    elif sem == "NORMAL" and "n" not in off:
                        fl, st = src[sid]; nrm = chunk(fl, st); off["n"] = o
                    elif sem == "TEXCOORD" and "t" not in off:
                        fl, st = src[sid]; uvs = [(a[0], a[1]) for a in chunk(fl, st)]; off["t"] = o
                ps = [[int(x) for x in (e.text or "").split()] for e in prim if _tag(e) == "p"]
                if "v" not in off or not ps:
                    continue
                if _tag(prim) == "triangles":
                    vc = [3] * int(prim.get("count", 0)); flat = ps[0]
                elif _tag(prim) == "polylist":
                    vcn = next((e for e in prim if _tag(e) == "vcount"), None)
                    vc = [int(x) for x in (vcn.text or "").split()]; flat = ps[0]
                else:
                    vc, flat = [], []
                    for pp in ps:
                        vc.append(len(pp) // stride); flat += pp
                k = 0
                for n in vc:
                    f = []
                    for _ in range(n):
                        row = flat[k * stride:(k + 1) * stride]; k += 1
                        f.append((row[off["v"]], row[off["t"]] if "t" in off else None, row[off["n"]] if "n" in off else None))
                    if len(f) >= 3:
                        faces.append(f)
            if pos and faces:
                ob.add_raw(pos, uvs or [], nrm or [], faces)
                out.write_text("models/%s.obj" % _obj_name(geom.get("name") or geom.get("id"), "geometry"), ob.text("diekspor REA dari COLLADA"),
                               "model3d", "%d vertex, %d face" % (len(pos), len(faces)))
        except Exception as e:
            out.errors.append("geometri %s: %s" % (_as_clean(geom.get("id"), 40), _as_clean(e, 100)))


register("COLLADA", "model3d", _is_dae, _dae_inspect, _dae_extract, 30, "COLLADA .dae (XML)")


# ---------------------------------------------------------------------------
# BVH (motion capture)
# ---------------------------------------------------------------------------

def _is_bvh(d, e): return bytes(d[:16]).lstrip().startswith(b"HIERARCHY")


def _bvh_parse(d):
    txt = bytes(d[:512 * 1024 * 1024]).decode("latin-1")
    hi, _, mo = txt.partition("MOTION")
    if not mo:
        raise ValueError("BVH tanpa bagian MOTION")
    cols, joints = [], []
    cur = None
    for ln in hi.splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] in ("ROOT", "JOINT") and len(t) > 1:
            cur = _as_clean(t[1], 40); joints.append(cur)
        elif t[0] == "End":
            cur = None
        elif t[0] == "CHANNELS" and cur:
            n = int(t[1])
            cols += ["%s.%s" % (cur, c) for c in t[2:2 + n]]
    lines = mo.strip().splitlines()
    frames = int(lines[0].split(":")[1])
    ft = float(lines[1].split(":")[1])
    data = [[float(x) for x in ln.split()] for ln in lines[2:2 + frames] if ln.strip()]
    return joints, cols, frames, ft, data


def _bvh_inspect(d, p):
    joints, cols, frames, ft, data = _bvh_parse(d)
    return {"lines": ["BVH: %d joint, %d kanal, %d frame @ %.1f fps (durasi %.2f dtk)" % (len(joints), len(cols), frames, 1 / ft if ft else 0, frames * ft),
                      "joint: " + ", ".join(joints[:12]) + (", ..." if len(joints) > 12 else "")], "extract": "-> .csv (satu kolom per kanal)"}


def _bvh_extract(d, p, out, opts):
    joints, cols, frames, ft, data = _bvh_parse(d)
    rows = [("%d" % i, "%.5f" % (i * ft)) + tuple("%.6g" % x for x in r) for i, r in enumerate(data)]
    out.write_text("%s.csv" % _obj_name(p.stem, "motion"), _csv_text(rows, ["frame", "time_s"] + cols), "animation", "%d frame" % len(rows))


register("BVH", "animation", _is_bvh, _bvh_inspect, _bvh_extract, 20, "motion capture BVH")


# ---------------------------------------------------------------------------
# Gambar
# ---------------------------------------------------------------------------

def _png_encode(w: int, h: int, rgba) -> bytes:
    """RGBA 8-bit -> PNG. rgba: bytes / bytearray panjang w*h*4."""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")


_PNG_CT = {0: "grayscale", 2: "RGB", 3: "palet", 4: "grayscale+alfa", 6: "RGBA"}


def _png_walk(d):
    pos, chunks = 8, []
    while pos + 12 <= len(d) and len(chunks) < 100_000:
        ln = _b32(d, pos)
        typ = bytes(d[pos + 4:pos + 8])
        chunks.append((typ, pos + 8, ln))
        pos += 12 + ln
        if typ == b"IEND":
            break
    return chunks, pos


def _png_inspect(d, p):
    w, h, bd, ct, _, _, il = struct.unpack_from(">IIBBBBB", d, 16)
    chunks, end = _png_walk(d)
    names = collections.Counter(c[0] for c in chunks)
    L = ["PNG %dx%d, %d-bit %s%s" % (w, h, bd, _PNG_CT.get(ct, "?"), ", interlaced" if il else "")]
    if names[b"acTL"]:
        o = next(c[1] for c in chunks if c[0] == b"acTL")
        L.append("APNG animasi: %d frame, ulang %s" % (_b32(d, o), _b32(d, o + 4) or "tanpa batas"))
    txt = []
    for t, o, ln in chunks:
        if t == b"tEXt" and len(txt) < 6:
            k = bytes(d[o:o + min(ln, 80)]).split(b"\x00")[0]
            txt.append(_as_clean(k, 30))
    if txt:
        L.append("teks metadata: " + ", ".join(txt))
    if names[b"eXIf"]:
        L.append("memuat EXIF")
    if end < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah IEND (kemungkinan data tersembunyi / arsip tertanam)" % (len(d) - end))
    return {"lines": L}


register("PNG", "image", lambda d, e: d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 33, _png_inspect, None, 15, "PNG / APNG")


def _jpeg_inspect(d, p):
    pos, L, info = 2, [], {}
    while pos + 4 <= len(d) and d[pos] == 0xFF:
        m = d[pos + 1]
        if m == 0xFF:
            pos += 1; continue
        if m == 0xD9 or m == 0xDA:
            break
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        ln = struct.unpack_from(">H", d, pos + 2)[0]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            prec, h, w, nc = struct.unpack_from(">BHHB", d, pos + 4)
            info.update(w=w, h=h, comps=nc, prog=m in (0xC2, 0xC6, 0xCA, 0xCE), prec=prec)
        elif m == 0xE1 and bytes(d[pos + 4:pos + 10]) == b"Exif\x00\x00":
            info["exif"] = True
        elif m == 0xE0 and bytes(d[pos + 4:pos + 9]) == b"JFIF\x00":
            info["jfif"] = True
        elif m == 0xFE:
            info["comment"] = _as_clean(d[pos + 4:pos + 2 + ln], 80)
        pos += 2 + ln
    L.append("JPEG %sx%s, %s komponen, %s%s%s" % (info.get("w", "?"), info.get("h", "?"), info.get("comps", "?"), "progresif" if info.get("prog") else "baseline",
                                              ", EXIF" if info.get("exif") else "", ", JFIF" if info.get("jfif") else ""))
    if info.get("comment"):
        L.append("komentar: " + info["comment"])
    ln = _jpeg_len(d, 0)
    if ln and ln < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah EOI" % (len(d) - ln))
    return {"lines": L}


def _jpeg_len(d, start):
    pos, n = start + 2, len(d)
    while pos + 4 <= n:
        if d[pos] != 0xFF:
            return None
        m = d[pos + 1]
        if m == 0xD9:
            return pos + 2 - start
        if m == 0xFF:
            pos += 1; continue
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        pos += 2 + struct.unpack_from(">H", d, pos + 2)[0]
        if m == 0xDA:
            p = pos
            while True:
                i = d.find(b"\xff", p)
                if i < 0 or i + 1 >= n:
                    return None
                nb = d[i + 1]
                if nb == 0 or 0xD0 <= nb <= 0xD7:
                    p = i + 2; continue
                pos = i
                break
    return None


register("JPEG", "image", lambda d, e: d[:3] == b"\xff\xd8\xff", _jpeg_inspect, None, 15, "JPEG")


def _gif_walk(d, start=0):
    if bytes(d[start:start + 4]) != b"GIF8" or bytes(d[start + 5:start + 6]) != b"a":
        raise ValueError("bukan GIF")
    w, h, fl = struct.unpack_from("<HHB", d, start + 6)
    pos = start + 13
    if fl & 0x80:
        pos += 3 * (2 << (fl & 7))
    frames = delay = 0
    loops = None
    n = len(d)

    def skip_sub(p):
        while p < n:
            ln = d[p]
            p += 1
            if ln == 0:
                return p
            p += ln
        raise ValueError("GIF terpotong")
    while pos < n:
        b = d[pos]
        if b == 0x3B:
            return {"w": w, "h": h, "frames": frames, "delay_cs": delay, "loops": loops, "end": pos + 1 - start}
        if b == 0x21:
            lab = d[pos + 1]
            if lab == 0xF9 and pos + 6 <= n:
                delay += _u16(d, pos + 4)
            if lab == 0xFF and bytes(d[pos + 3:pos + 14]) == b"NETSCAPE2.0" and pos + 18 <= n:
                loops = _u16(d, pos + 16)
            pos = skip_sub(pos + 2)
        elif b == 0x2C:
            fl2 = d[pos + 9]
            pos += 10
            if fl2 & 0x80:
                pos += 3 * (2 << (fl2 & 7))
            pos = skip_sub(pos + 1)
            frames += 1
        else:
            raise ValueError("blok GIF tidak dikenal")
    raise ValueError("GIF tanpa trailer")


def _gif_inspect(d, p):
    g = _gif_walk(d)
    L = ["GIF %dx%d, %d frame%s" % (g["w"], g["h"], g["frames"], ", durasi %.2f dtk" % (g["delay_cs"] / 100) if g["frames"] > 1 else "")]
    if g["loops"] is not None:
        L.append("ulang: %s" % (g["loops"] or "tanpa batas"))
    if g["end"] < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah trailer GIF" % (len(d) - g["end"]))
    return {"lines": L}


register("GIF", "image", lambda d, e: d[:4] == b"GIF8" and d[5:6] == b"a", _gif_inspect, None, 15, "GIF (animasi)")


def _webp_inspect(d, p):
    pos, L, flags = 12, [], 0
    w = h = frames = 0
    kind = "?"
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        b = pos + 8
        if t == b"VP8X":
            flags = d[b]; w = int.from_bytes(d[b + 4:b + 7], "little") + 1; h = int.from_bytes(d[b + 7:b + 10], "little") + 1; kind = "VP8X"
        elif t == b"VP8 " and not w:
            w, h = _u16(d, b + 6) & 0x3FFF, _u16(d, b + 8) & 0x3FFF; kind = "lossy"
        elif t == b"VP8L" and not w:
            v = _u32(d, b + 1); w, h = (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1; kind = "lossless"
        elif t == b"ANMF":
            frames += 1
        pos = b + ln + (ln & 1)
    L.append("WebP %dx%d (%s)%s%s" % (w, h, kind, ", animasi %d frame" % frames if flags & 2 else "", ", alfa" if flags & 0x10 else ""))
    return {"lines": L}


register("WebP", "image", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WEBP", _webp_inspect, None, 14, "WebP")


def _ico_inspect(d, p):
    n = _u16(d, 4)
    L = ["%s: %d gambar" % ("ICO" if _u16(d, 2) == 1 else "CUR", n)]
    for i in range(min(n, 12)):
        w, h = d[6 + 16 * i] or 256, d[7 + 16 * i] or 256
        L.append("  %dx%d, %d-bit, %s" % (w, h, _u16(d, 12 + 16 * i), _as_human(_u32(d, 14 + 16 * i))))
    return {"lines": L}


register("ICO", "image", lambda d, e: len(d) >= 22 and d[:2] == b"\x00\x00" and d[2:4] in (b"\x01\x00", b"\x02\x00") and 0 < _u16(d, 4) < 256 and e in (".ico", ".cur"),
         _ico_inspect, None, 40, "ikon Windows")


# --- BMP ---

def _bmp_decode(d):
    off = _u32(d, 10)
    hs = _u32(d, 14)
    if hs < 40:
        raise ValueError("BMP header lama tidak didukung")
    w, h, planes, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
    top = h < 0
    h = abs(h)
    if w <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran BMP tidak wajar")
    if comp not in (0, 3) or bpp not in (8, 24, 32):
        raise ValueError("BMP %d-bit / kompresi %d belum didukung" % (bpp, comp))
    out = bytearray(w * h * 4)
    pal = None
    if bpp == 8:
        nc = _u32(d, 46) or 256
        pal = [bytes(d[14 + hs + 4 * i:14 + hs + 4 * i + 3]) for i in range(nc)]
    rb = ((w * bpp + 31) // 32) * 4
    for y in range(h):
        row = bytes(d[off + y * rb:off + y * rb + w * bpp // 8])
        dy = y if top else h - 1 - y
        o = dy * w * 4
        for x in range(w):
            if bpp == 24:
                b, g, r = row[3 * x:3 * x + 3]; a = 255
            elif bpp == 32:
                b, g, r, a = row[4 * x:4 * x + 4]
            else:
                b, g, r = pal[row[x]] if row[x] < len(pal) else (0, 0, 0); a = 255
            out[o:o + 4] = bytes((r, g, b, a)); o += 4
    return w, h, out


def _bmp_inspect(d, p):
    hs = _u32(d, 14)
    if hs >= 40:
        w, h, _, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
        return {"lines": ["BMP %dx%d, %d-bit, kompresi %d" % (w, abs(h), bpp, comp)], "extract": "-> .png (8 / 24 / 32-bit tak terkompresi)"}
    return {"lines": ["BMP header lama (OS/2)"]}


def _bmp_extract(d, p, out, opts):
    w, h, px = _bmp_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("BMP", "image", lambda d, e: d[:2] == b"BM" and len(d) > 30 and _u32(d, 10) < len(d) and _u32(d, 14) in (12, 40, 52, 56, 64, 108, 124),
         _bmp_inspect, _bmp_extract, 16, "bitmap Windows")


# --- TGA (tanpa magic: dideteksi dari ekstensi + header masuk akal) ---

def _tga_ok(d, e):
    if e != ".tga" or len(d) < 18:
        return False
    cm, it, bpp = d[1], d[2], d[16]
    return cm in (0, 1) and it in (1, 2, 3, 9, 10, 11) and bpp in (8, 15, 16, 24, 32)


def _tga_decode(d):
    idlen, cmt, it = d[0], d[1], d[2]
    cmstart, cmlen, cmbits = struct.unpack_from("<HHB", d, 3)
    w, h, bpp, desc = struct.unpack_from("<HHBB", d, 12)[0:2] + struct.unpack_from("<BB", d, 16)
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran TGA tidak wajar")
    pos = 18 + idlen
    pal = None
    if cmt:
        step = (cmbits + 7) // 8
        pal = [bytes(d[pos + i * step:pos + (i + 1) * step]) for i in range(cmlen)]
        pos += cmlen * step
    bytespp = (bpp + 7) // 8
    rle = it >= 9
    total = w * h * bytespp
    if rle:
        buf = bytearray()
        while len(buf) < total and pos < len(d):
            hd = d[pos]; pos += 1
            n = (hd & 0x7F) + 1
            if hd & 0x80:
                buf += bytes(d[pos:pos + bytespp]) * n; pos += bytespp
            else:
                buf += bytes(d[pos:pos + n * bytespp]); pos += n * bytespp
        raw = bytes(buf[:total])
    else:
        raw = bytes(d[pos:pos + total])
    if len(raw) < total:
        raise ValueError("data TGA terpotong")
    out = bytearray(w * h * 4)
    base = it & 7
    for i in range(w * h):
        px = raw[i * bytespp:(i + 1) * bytespp]
        if base == 1:
            c = pal[px[0] - cmstart] if cmt and 0 <= px[0] - cmstart < len(pal) else b"\0\0\0"
            b, g, r = c[0], c[1], c[2]; a = c[3] if len(c) > 3 else 255
        elif base == 3:
            r = g = b = px[0]; a = 255
        elif bpp == 24:
            b, g, r = px; a = 255
        elif bpp == 32:
            b, g, r, a = px
        else:   # 15 / 16-bit 5-5-5
            v = px[0] | (px[1] << 8)
            r, g, b = ((v >> 10) & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, (v & 31) * 255 // 31; a = 255
        out[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    if not (desc & 0x20):   # asal kiri-bawah -> balik vertikal
        rows = [out[y * w * 4:(y + 1) * w * 4] for y in range(h)][::-1]
        out = bytearray().join(rows)
    if desc & 0x10:         # asal kanan -> balik horizontal
        out = bytearray().join(bytes(b"".join(bytes(r[x * 4:x * 4 + 4]) for x in range(w - 1, -1, -1))) for r in [out[y * w * 4:(y + 1) * w * 4] for y in range(h)])
    return w, h, out


def _tga_inspect(d, p):
    w, h = _u16(d, 12), _u16(d, 14)
    return {"lines": ["TGA %dx%d, %d-bit, tipe %d%s" % (w, h, d[16], d[2], " (RLE)" if d[2] >= 9 else "")], "extract": "-> .png"}


def _tga_extract(d, p, out, opts):
    w, h, px = _tga_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("TGA", "image", _tga_ok, _tga_inspect, _tga_extract, 60, "Truevision TGA (dikenali dari ekstensi + header)")


# --- DDS ---

_DXGI = {71: "DXT1", 72: "DXT1", 74: "DXT3", 75: "DXT3", 77: "DXT5", 78: "DXT5"}
_DXGI_NAMES = {80: "BC4_UNORM", 81: "BC4_SNORM", 83: "BC5_UNORM", 84: "BC5_SNORM", 95: "BC6H_UF16", 96: "BC6H_SF16", 98: "BC7_UNORM", 99: "BC7_UNORM_SRGB",
               28: "R8G8B8A8_UNORM", 87: "B8G8R8A8_UNORM"}


def _dds_info(d):
    h, w = struct.unpack_from("<II", d, 12)
    depth, mips = struct.unpack_from("<II", d, 24)
    pfflags = _u32(d, 80)
    fcc = bytes(d[84:88])
    bits = _u32(d, 88)
    masks = struct.unpack_from("<IIII", d, 92)
    off, fmt = 128, None
    if pfflags & 4:
        fcc_s = fcc.decode("latin-1")
        if fcc_s == "DX10":
            dx = _u32(d, 128)
            off = 148
            fmt = _DXGI.get(dx) or _DXGI_NAMES.get(dx) or "DXGI_%d" % dx
        else:
            fmt = fcc_s
    else:
        fmt = "RGBA%d" % bits if pfflags & 0x41 or pfflags & 0x40 else "RGB%d" % bits
    caps2 = _u32(d, 112)
    return {"w": w, "h": h, "mips": max(1, mips), "fmt": fmt, "off": off, "bits": bits, "masks": masks, "pf": pfflags,
            "cube": bool(caps2 & 0x200), "volume": bool(caps2 & 0x200000)}


def _c565(v): return ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31


def _dxt_decode(d, off, w, h, kind):
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 8 if kind == "DXT1" else 16
    if off + bw * bh * bs > len(d):
        raise ValueError("data DDS terpotong")
    out = bytearray(w * h * 4)
    for by in range(bh):
        for bx in range(bw):
            b = bytes(d[off + (by * bw + bx) * bs:off + (by * bw + bx) * bs + bs])
            cb = b[-8:]
            c0, c1 = struct.unpack_from("<HH", cb, 0)
            r0, r1 = _c565(c0), _c565(c1)
            if c0 > c1 or kind != "DXT1":
                pal = [r0 + (255,), r1 + (255,),
                       tuple((2 * a + b2) // 3 for a, b2 in zip(r0, r1)) + (255,), tuple((a + 2 * b2) // 3 for a, b2 in zip(r0, r1)) + (255,)]
            else:
                pal = [r0 + (255,), r1 + (255,), tuple((a + b2) // 2 for a, b2 in zip(r0, r1)) + (255,), (0, 0, 0, 0)]
            idx = struct.unpack_from("<I", cb, 4)[0]
            alpha = None
            if kind == "DXT3":
                av = int.from_bytes(b[:8], "little")
                alpha = [((av >> (4 * i)) & 15) * 17 for i in range(16)]
            elif kind == "DXT5":
                a0, a1 = b[0], b[1]
                ab = int.from_bytes(b[2:8], "little")
                ap = [a0, a1] + ([(( 6 - i) * a0 + (1 + i) * a1) // 7 for i in range(6)] if a0 > a1 else [((4 - i) * a0 + (1 + i) * a1) // 5 for i in range(4)] + [0, 255])
                alpha = [ap[(ab >> (3 * i)) & 7] for i in range(16)]
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x < w and y < h:
                    r, g, bl, a = pal[(idx >> (2 * i)) & 3]
                    if alpha:
                        a = alpha[i]
                    o = (y * w + x) * 4
                    out[o:o + 4] = bytes((r, g, bl, a))
    return out


def _dds_decode(d):
    i = _dds_info(d)
    w, h, off, fmt = i["w"], i["h"], i["off"], i["fmt"]
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran DDS tidak wajar")
    if i["cube"] or i["volume"]:
        raise ValueError("cubemap / tekstur volume: hanya mip pertama bidang pertama yang bisa dibaca; belum didukung")
    if fmt in ("DXT1", "DXT3", "DXT5"):
        return w, h, _dxt_decode(d, off, w, h, fmt)
    if fmt in ("R8G8B8A8_UNORM", "B8G8R8A8_UNORM") or (not (i["pf"] & 4) and i["bits"] in (24, 32)):
        bpp = 3 if (not (i["pf"] & 4) and i["bits"] == 24) else 4
        raw = bytes(d[off:off + w * h * bpp])
        if len(raw) < w * h * bpp:
            raise ValueError("data DDS terpotong")
        rm, gm, bm, am = i["masks"]
        out = bytearray(w * h * 4)
        sh = lambda m: (m & -m).bit_length() - 1 if m else None
        for px in range(w * h):
            v = int.from_bytes(raw[px * bpp:(px + 1) * bpp], "little")
            if fmt == "R8G8B8A8_UNORM":
                out[px * 4:px * 4 + 4] = raw[px * 4:px * 4 + 4]
            elif fmt == "B8G8R8A8_UNORM":
                b_, g_, r_, a_ = raw[px * 4:px * 4 + 4]; out[px * 4:px * 4 + 4] = bytes((r_, g_, b_, a_))
            else:
                g = lambda m: ((v & m) >> sh(m)) if m else 255
                out[px * 4:px * 4 + 4] = bytes((g(rm), g(gm), g(bm), g(am) if am else 255))
        return w, h, out
    raise ValueError("format DDS %s belum didukung (BC4-BC7 / ASTC / dll butuh dekoder tambahan)" % fmt)


def _dds_inspect(d, p):
    i = _dds_info(d)
    ok = i["fmt"] in ("DXT1", "DXT3", "DXT5") or i["fmt"].startswith(("RGB", "RGBA", "R8G8B8A8", "B8G8R8A8"))
    L = ["DDS %dx%d, format %s, %d mip%s%s" % (i["w"], i["h"], i["fmt"], i["mips"], ", cubemap" if i["cube"] else "", ", volume" if i["volume"] else "")]
    return {"lines": L, "extract": "-> .png (mip pertama)" if ok and not (i["cube"] or i["volume"]) else "format ini belum bisa didekode ke PNG"}


def _dds_extract(d, p, out, opts):
    w, h, px = _dds_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "texture"), _png_encode(w, h, px), "image", "%dx%d dari DDS" % (w, h))


register("DDS", "image", lambda d, e: d[:4] == b"DDS " and len(d) >= 128 and _u32(d, 4) == 124, _dds_inspect, _dds_extract, 12, "tekstur DirectDraw (game)")


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def _wav_inspect(d, p):
    pos, fmt, data_len, extra = 12, None, 0, []
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        if t == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", d, pos + 8)
        elif t == b"data":
            data_len = min(ln, len(d) - pos - 8)
        elif t in (b"LIST", b"smpl", b"cue ", b"bext", b"id3 "):
            extra.append(t.decode("latin-1").strip())
        pos += 8 + ln + (ln & 1)
    if not fmt:
        return {"lines": ["WAV tanpa chunk fmt (rusak)"]}
    tag, ch, sr, br, ba, bits = fmt
    dur = data_len / br if br else 0
    names = {1: "PCM", 3: "float", 2: "MS-ADPCM", 17: "IMA-ADPCM", 85: "MP3", 0xFFFE: "extensible"}
    return {"lines": ["WAV %s, %d kanal, %d Hz, %d-bit, durasi %.2f dtk" % (names.get(tag, "tag %d" % tag), ch, sr, bits, dur)] + (["chunk lain: " + ", ".join(extra)] if extra else [])}


register("WAV", "audio", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WAVE", _wav_inspect, None, 14, "WAV (RIFF)")


def _ogg_inspect(d, p):
    n = len(d)
    ln = d[26]
    first = bytes(d[27 + ln:27 + ln + 64])
    ser = _u32(d, 14)
    rate = ch = 0
    kind = "?"
    pre = 0
    if first[:7] == b"\x01vorbis":
        kind, ch, rate = "Vorbis", first[11], _u32(first, 12)
    elif first[:8] == b"OpusHead":
        kind, ch, rate, pre = "Opus", first[9], 48000, struct.unpack_from("<H", first, 10)[0]
    elif first[:5] == b"\x7fFLAC":
        kind = "FLAC-dalam-Ogg"
    elif first[:8] == b"\x80theora" or first[:7] == b"\x80theora":
        kind = "Theora (video)"
    last = bytes(d).rfind(b"OggS", max(0, n - 70000))
    dur = 0.0
    if last >= 0 and rate:
        gp = struct.unpack_from("<q", d, last + 6)[0]
        dur = max(0, gp - pre) / rate
    return {"lines": ["OGG %s, %d kanal, %d Hz, durasi ~%.2f dtk" % (kind, ch, rate, dur)]}


register("OGG", "audio", lambda d, e: d[:4] == b"OggS" and len(d) > 40, _ogg_inspect, None, 14, "Ogg (Vorbis / Opus)")


def _flac_inspect(d, p):
    v = int.from_bytes(d[18:26], "big")
    rate, ch, bps, total = v >> 44, ((v >> 41) & 7) + 1, ((v >> 36) & 31) + 1, v & ((1 << 36) - 1)
    return {"lines": ["FLAC %d Hz, %d kanal, %d-bit, durasi %.2f dtk" % (rate, ch, bps, total / rate if rate else 0)]}


register("FLAC", "audio", lambda d, e: d[:4] == b"fLaC" and len(d) > 42, _flac_inspect, None, 14, "FLAC")

_MP3_BR = {1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0], 2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]}
_MP3_SR = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}


def _mp3_start(d):
    pos = 0
    if d[:3] == b"ID3" and len(d) > 10:
        pos = 10 + ((d[6] & 0x7F) << 21 | (d[7] & 0x7F) << 14 | (d[8] & 0x7F) << 7 | (d[9] & 0x7F))
    for i in range(pos, min(len(d) - 4, pos + 65536)):
        if d[i] == 0xFF and (d[i + 1] & 0xE0) == 0xE0 and (d[i + 1] >> 1) & 3 == 1 and (d[i + 1] >> 3) & 3 != 1 and (d[i + 2] >> 4) != 15 and ((d[i + 2] >> 2) & 3) != 3:
            return pos, i
    return pos, -1


def _mp3_detect(d, e):
    if d[:3] == b"ID3":
        return True
    return e == ".mp3" and _mp3_start(d)[1] >= 0


def _mp3_inspect(d, p):
    tag, i = _mp3_start(d)
    if i < 0:
        return {"lines": ["MP3 (ID3 ada, frame audio tidak ditemukan)"]}
    ver = (d[i + 1] >> 3) & 3
    br = _MP3_BR[1 if ver == 3 else 2][d[i + 2] >> 4]
    sr = _MP3_SR[ver][(d[i + 2] >> 2) & 3]
    ch = 1 if (d[i + 3] >> 6) == 3 else 2
    dur = (len(d) - i) * 8 / (br * 1000) if br else 0
    return {"lines": ["MP3 MPEG%s Layer III, %d kbps, %d Hz, %d kanal, durasi ~%.1f dtk (perkiraan CBR)%s" % (
        "1" if ver == 3 else "2", br, sr, ch, dur, ", ID3v2 %d byte" % tag if tag else "")]}


register("MP3", "audio", _mp3_detect, _mp3_inspect, None, 45, "MP3")


def _midi_inspect(d, p):
    fmt, nt, div = struct.unpack_from(">HHH", d, 8)
    return {"lines": ["MIDI format %d, %d track, %s" % (fmt, nt, "%d tick/beat" % div if not div & 0x8000 else "waktu SMPTE")]}


register("MIDI", "audio", lambda d, e: d[:8] == b"MThd\x00\x00\x00\x06" and len(d) >= 14, _midi_inspect, None, 14, "Standard MIDI")


# ---------------------------------------------------------------------------
# Arsip / paket game (pola umum: daftar entri + pembaca)
# ---------------------------------------------------------------------------

class _Arc:
    def __init__(self, entries, read, notes=None, close=None, kind=""):
        self.entries, self.read, self.notes, self.close, self.kind = entries, read, notes or [], close, kind


def _arc_inspect_factory(lister):
    def inspect(d, p):
        a = lister(d, p)
        try:
            ents = a.entries
            tot = sum(e.get("size", 0) for e in ents)
            ext = collections.Counter((os.path.splitext(e["name"])[1].lower() or "(tanpa ekstensi)") for e in ents)
            L = ["%s: %d entri, total %s" % (a.kind, len(ents), _as_human(tot))]
            if ext:
                L.append("jenis: " + ", ".join("%s x%d" % kv for kv in ext.most_common(10)))
            L += a.notes
            for e in ents[:25]:
                L.append("  %s  %s%s" % (_as_clean(e["name"], 90), _as_human(e.get("size", 0)), "  [terenkripsi]" if e.get("enc") else ""))
            if len(ents) > 25:
                L.append("  ... +%d entri lagi (ekstrak untuk daftar lengkap di manifest)" % (len(ents) - 25))
            return {"lines": L, "extract": "semua entri (filter dengan pola, mis. *.dds); tekstur / model di dalamnya ikut dikonversi bila convert=True",
                    "entries": [{"name": e["name"], "size": e.get("size", 0)} for e in ents[:2000]]}
        finally:
            if a.close:
                a.close()
    return inspect


def _arc_extract_factory(lister):
    def extract(d, p, out, opts):
        a = lister(d, p)
        pat = (opts.get("pattern") or "").lower()
        try:
            for e in a.entries:
                nm = e["name"]
                if pat and not fnmatch.fnmatch(nm.lower(), pat) and not fnmatch.fnmatch(os.path.basename(nm).lower(), pat):
                    continue
                if e.get("enc"):
                    out.skipped.append({"path": nm, "reason": "terenkripsi (butuh kunci)"})
                    continue
                if e.get("size", 0) > MAX_OUT_FILE:
                    out.skipped.append({"path": nm, "reason": "terlalu besar"})
                    continue
                try:
                    data = a.read(e)
                except Exception as ex:
                    out.errors.append("%s: %s" % (_as_clean(nm, 80), _as_clean(ex, 100)))
                    continue
                out.write(nm, data, "archive-entry")
        finally:
            if a.close:
                a.close()
    return extract


def _add_archive(name, detect, lister, about, priority=30):
    register(name, "archive", detect, _arc_inspect_factory(lister), _arc_extract_factory(lister), priority, about)


def _cstr(b) -> str:
    return bytes(b).split(b"\x00")[0].decode("latin-1")


# --- Quake PAK ---
def _qpak(d, p):
    off, ln = struct.unpack_from("<II", d, 4)
    if ln % 64 or off + ln > len(d) or ln // 64 > MAX_ENTRIES:
        raise ValueError("direktori PAK tidak valid")
    ents = []
    for i in range(ln // 64):
        nm = _cstr(d[off + 64 * i:off + 64 * i + 56])
        o, s = struct.unpack_from("<II", d, off + 64 * i + 56)
        if o + s > len(d):
            continue
        ents.append({"name": nm, "off": o, "size": s})
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), kind="Quake PAK")


_add_archive("Quake-PAK", lambda d, e: d[:4] == b"PACK" and len(d) >= 12 and _u32(d, 8) % 64 == 0, _qpak, "paket Quake / Quake II (PACK)")


# --- WAD ---
def _wad(d, p):
    m = bytes(d[:4])
    n, off = struct.unpack_from("<II", d, 4)
    if n > MAX_ENTRIES:
        raise ValueError("terlalu banyak lump")
    ents, notes = [], []
    if m in (b"IWAD", b"PWAD"):
        for i in range(n):
            o, s = struct.unpack_from("<ii", d, off + 16 * i)
            ents.append({"name": _cstr(d[off + 16 * i + 8:off + 16 * i + 16]), "off": o, "size": s})
        kind = "Doom WAD (%s)" % m.decode()
    else:
        for i in range(n):
            o, ds, s, t, c = struct.unpack_from("<iiiBB", d, off + 32 * i)
            ents.append({"name": _cstr(d[off + 32 * i + 16:off + 32 * i + 32]), "off": o, "size": s, "dsize": ds, "type": t, "comp": c,
                         "enc": c != 0})
        kind = "%s (Quake / Half-Life)" % m.decode()
        notes.append("lump tekstur (type 0x43) belum dikonversi ke gambar" if any(e.get("type") == 0x43 for e in ents) else "")
        notes = [x for x in notes if x]
    ents = [e for e in ents if 0 <= e["off"] and e["size"] >= 0 and e["off"] + e.get("dsize", e["size"]) <= len(d)]
    seen = collections.Counter()
    for e in ents:     # nama lump boleh kembar: bedakan
        seen[e["name"]] += 1
        if seen[e["name"]] > 1:
            e["name"] = "%s_%d" % (e["name"], seen[e["name"]])
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), notes, kind=kind)


_add_archive("WAD", lambda d, e: len(d) >= 12 and bytes(d[:4]) in (b"IWAD", b"PWAD", b"WAD2", b"WAD3"), _wad, "WAD (Doom / Quake / Half-Life)")


# --- Unreal .pak (v1-v9, tanpa enkripsi) ---
_UPAK_MAGIC = 0x5A6F12E1


def _fstr(d, pos):
    n = struct.unpack_from("<i", d, pos)[0]
    pos += 4
    if n < 0:
        n = -n
        s = bytes(d[pos:pos + 2 * n]).decode("utf-16-le", "replace").rstrip("\x00")
        return s, pos + 2 * n
    s = bytes(d[pos:pos + n]).decode("utf-8", "replace").rstrip("\x00")
    return s, pos + n


def _upak_entry(d, pos, ver):
    st = pos
    off, size, usize, comp = struct.unpack_from("<QQQI", d, pos)
    pos += 28
    if ver == 1:
        pos += 8
    pos += 20
    blocks, enc, bsize = [], 0, 0
    if ver >= 3:
        if comp:
            nb = _u32(d, pos)
            pos += 4
            if nb > 1_000_000:
                raise ValueError("jumlah blok kompresi tidak wajar")
            for _ in range(nb):
                blocks.append(struct.unpack_from("<QQ", d, pos))
                pos += 16
        enc, bsize = d[pos], _u32(d, pos + 1)
        pos += 5
    return {"off": off, "csize": size, "size": usize if comp else size, "usize": usize, "comp": comp, "blocks": blocks, "enc": bool(enc), "bsize": bsize,
            "hdr": pos - st}, pos


def _upak(d, p):
    n = len(d)
    tail_start = max(0, n - 512)
    tail = bytes(d[tail_start:])
    magic = struct.pack("<I", _UPAK_MAGIC)
    k = tail.rfind(magic)
    found = None
    while k >= 0:
        a = tail_start + k
        if a + 44 <= n:
            ver, ioff, isz = _u32(d, a + 4), _u64(d, a + 8), _u64(d, a + 16)
            if 1 <= ver <= 11 and ioff + isz <= n:
                found = (a, ver, ioff, isz)
                break
        k = tail.rfind(magic, 0, k)
    if not found:
        raise ValueError("footer Unreal PAK tidak ditemukan")
    a, ver, ioff, isz = found
    if ver >= 10:
        raise ValueError("Unreal PAK versi %d (indeks path-hash UE 4.26+) belum didukung; versi 1-9 saja" % ver)
    if ver >= 4 and d[a - 1]:
        raise ValueError("indeks PAK terenkripsi (butuh kunci AES)")
    names = [""]
    rem = n - (a + 44) - (1 if ver == 9 else 0)
    if ver >= 8 and rem > 0:
        base = a + 44 + (1 if ver == 9 else 0)
        names += [_cstr(d[base + 32 * i:base + 32 * i + 32]) for i in range(rem // 32)]
    pos = ioff
    mount, pos = _fstr(d, pos)
    cnt = _u32(d, pos)
    pos += 4
    if cnt > MAX_ENTRIES:
        raise ValueError("terlalu banyak entri PAK")
    ents = []
    for _ in range(cnt):
        nm, pos = _fstr(d, pos)
        e, pos = _upak_entry(d, pos, ver)
        e["name"] = (mount.replace("../../../", "") + nm) if mount else nm
        ents.append(e)

    def read(e):
        if e["enc"]:
            raise ValueError("terenkripsi (butuh kunci AES)")
        base = e["off"]
        if e["comp"] == 0:
            return bytes(d[base + e["hdr"]:base + e["hdr"] + e["csize"]])
        meth = names[e["comp"]] if ver >= 8 and e["comp"] < len(names) else ("Zlib" if e["comp"] == 1 else "kode %d" % e["comp"])
        if not meth.lower().startswith("zlib"):
            raise ValueError("kompresi %s belum didukung (zlib saja)" % meth)
        out = bytearray()
        for s, en in e["blocks"]:
            lo, hi = (base + s, base + en) if ver >= 5 else (s, en)
            out += zlib.decompress(bytes(d[lo:hi]))
            if len(out) > MAX_OUT_FILE:
                raise ValueError("terlalu besar")
        return bytes(out[:e["usize"]])
    return _Arc(ents, read, ["PERHATIAN: parser Unreal PAK ini baru diuji dengan berkas sintetis; bila hasil aneh, kirim contoh .pak kecil untuk diverifikasi.",
                               "mount point: %s | versi PAK: %d" % (_as_clean(mount, 60), ver)], kind="Unreal PAK")


def _upak_detect(d, e):
    n = len(d)
    return n > 60 and struct.pack("<I", _UPAK_MAGIC) in bytes(d[max(0, n - 512):])


_add_archive("Unreal-PAK", _upak_detect, _upak, "Unreal Engine .pak (v1-v9, tanpa enkripsi)", 28)


# --- ZIP ---
def _zip(d, p):
    zf = zipfile.ZipFile(p)
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        zf.close()
        raise ValueError("terlalu banyak entri ZIP")
    ents = [{"name": i.filename, "size": i.file_size, "csize": i.compress_size, "info": i, "enc": bool(i.flag_bits & 1)} for i in infos if not i.is_dir()]
    names = {e["name"] for e in ents}
    kind = "ZIP"
    notes = []
    if "AndroidManifest.xml" in names:
        kind = "APK (Android)"
    elif "[Content_Types].xml" in names:
        kind = "OOXML (docx / xlsx / pptx)"
        notes.append("media tertanam ada di word/media/, xl/media/, ppt/media/")
    elif "META-INF/MANIFEST.MF" in names:
        kind = "JAR"
    elif "mimetype" in names:
        kind = "ODF / EPUB"
    elif "AndroidManifest.xml" not in names and any(n.endswith(".uasset") or n.endswith(".pak") for n in names):
        kind = "ZIP (berisi aset Unreal)"

    def read(e):
        with zf.open(e["info"]) as f:
            data = f.read(MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc(ents, read, notes, zf.close, kind)


_add_archive("ZIP", lambda d, e: d[:4] in (b"PK\x03\x04", b"PK\x05\x06") and len(d) >= 22, _zip, "ZIP, APK, JAR, OOXML, ODF, EPUB", 30)


# --- TAR / GZIP ---
def _is_tar_raw(d): return len(d) > 512 and bytes(d[257:262]) == b"ustar"


def _gz_head(d):
    try:
        return zlib.decompressobj(31).decompress(bytes(d[:4096]), 1024)
    except zlib.error:
        return b""


def _tar(d, p):
    tf = tarfile.open(p, "r:*")
    ents = []
    for m in tf:
        if m.isfile():
            ents.append({"name": m.name, "size": m.size, "m": m})
            if len(ents) > MAX_ENTRIES:
                tf.close()
                raise ValueError("terlalu banyak entri TAR")

    def read(e):
        if e["size"] > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return tf.extractfile(e["m"]).read(MAX_OUT_FILE + 1)
    return _Arc(ents, read, close=tf.close, kind="TAR")


_add_archive("TAR", lambda d, e: _is_tar_raw(d) or (d[:2] == b"\x1f\x8b" and bytes(_gz_head(d))[257:262] == b"ustar") or (d[:3] == b"BZh" and e in (".tbz", ".tbz2", ".bz2") and e != ".bz2") or (d[:6] == b"\xfd7zXZ\x00" and e == ".txz"),
             _tar, "TAR (+ .tar.gz / .tgz)", 29)


def _gzip(d, p):
    flg = d[3]
    pos = 10
    name = ""
    if flg & 4:
        pos += 2 + _u16(d, pos)
    if flg & 8:
        end = bytes(d[pos:pos + 300]).find(b"\x00")
        name = bytes(d[pos:pos + end]).decode("latin-1") if end >= 0 else ""
    isz = _u32(d, len(d) - 4)
    nm = name or (p.stem if p.suffix.lower() == ".gz" else p.name + ".out")

    def read(e):
        data = zlib.decompressobj(31).decompress(bytes(d), MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc([{"name": nm, "size": isz}], read, ["ukuran asli dari trailer (modulo 4 GB)"], kind="GZIP")


_add_archive("GZIP", lambda d, e: d[:3] == b"\x1f\x8b\x08" and len(d) > 18, _gzip, "GZIP satu berkas", 35)


# --- deteksi-saja: UnityFS, 7z, RAR ---
def _unity_inspect(d, p):
    pos = 8
    strs = []
    for _ in range(2):
        end = bytes(d[pos:pos + 128]).find(b"\x00")
        strs.append(_as_clean(d[pos:pos + end], 40)); pos += end + 1
    size, cbi, ubi, flags = struct.unpack_from(">qIII", d, pos)
    comp = {0: "tanpa kompresi", 1: "LZMA", 2: "LZ4", 3: "LZ4HC"}.get(flags & 0x3F, "?")
    return {"lines": ["Unity AssetBundle (UnityFS): versi Unity %s, revisi %s, %s, kompresi blok info: %s" % (strs[0] if strs else "?", strs[1] if len(strs) > 1 else "?", _as_human(size), comp),
                      "Isi (SerializedFile: mesh, animasi, tekstur) butuh dekompresi %s + parser per versi Unity; belum ada di REA. Pakai plugin atau alat khusus lalu arahkan REA ke hasilnya." % comp]}


register("UnityFS", "archive", lambda d, e: d[:8] == b"UnityFS\x00", _unity_inspect, None, 20, "Unity AssetBundle (deteksi saja)")
register("7z", "archive", lambda d, e: d[:6] == b"7z\xbc\xaf\x27\x1c",
         lambda d, p: {"lines": ["7-Zip, versi %d.%d. Ekstrak dengan 7-Zip lalu arahkan REA ke folder hasil." % (d[6], d[7])]}, None, 20, "7z (deteksi saja)")
register("RAR", "archive", lambda d, e: d[:6] == b"Rar!\x1a\x07",
         lambda d, p: {"lines": ["RAR %s. Ekstrak dengan unrar / 7-Zip lalu arahkan REA ke folder hasil." % ("v5" if d[6] == 1 else "v4")]}, None, 20, "RAR (deteksi saja)")


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

def _sql_open(p: Path):
    uri = "file:%s?mode=ro&immutable=1" % urllib.parse.quote(str(p.resolve()))
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=ON")
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    return con


def _sql_tables(con):
    return [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 500")]


def _sql_inspect(d, p):
    ps = struct.unpack_from(">H", d, 16)[0] or 65536
    con = _sql_open(p)
    try:
        L = ["SQLite: halaman %d byte x %d" % (ps, _b32(d, 28))]
        for t in _sql_tables(con)[:60]:
            q = '"%s"' % t.replace('"', '""')
            n = con.execute("SELECT COUNT(*) FROM %s" % q).fetchone()[0]
            cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % q)]
            L.append("  tabel %s: %d baris [%s]" % (_as_clean(t, 40), n, ", ".join(_as_clean(c, 20) for c in cols[:10])))
        return {"lines": L, "extract": "tiap tabel -> .csv"}
    finally:
        con.close()


def _sql_extract(d, p, out, opts):
    con = _sql_open(p)
    try:
        for t in _sql_tables(con):
            q = '"%s"' % t.replace('"', '""')
            cur = con.execute("SELECT * FROM %s LIMIT 2000000" % q)
            cols = [c[0] for c in cur.description]
            rows = []
            for r in cur:
                rows.append(["base64:" + base64.b64encode(v).decode() if isinstance(v, (bytes, bytearray)) and len(v) <= 65536 else
                             "<blob %d byte>" % len(v) if isinstance(v, (bytes, bytearray)) else v for v in r])
            out.write_text("tables/%s.csv" % _obj_name(t, "table"), _csv_text(rows, cols), "table", "%d baris" % len(rows))
    finally:
        con.close()


register("SQLite", "database", lambda d, e: d[:16] == b"SQLite format 3\x00", _sql_inspect, _sql_extract, 12, "database SQLite")


# ---------------------------------------------------------------------------
# Carving: cari berkas tertanam di dalam berkas apa pun
# ---------------------------------------------------------------------------

def _len_png(d, o):
    pos, n = o + 8, len(d)
    while pos + 12 <= n:
        ln = _b32(d, pos)
        t = bytes(d[pos + 4:pos + 8])
        pos += 12 + ln
        if t == b"IEND":
            return pos - o
        if ln > n:
            return None
    return None


def _len_gif(d, o):
    try:
        return _gif_walk(d, o)["end"]
    except (ValueError, struct.error, IndexError):
        return None


def _len_riff(d, o):
    ln = _u32(d, o + 4) + 8
    return ln if 12 < ln <= len(d) - o else None


def _len_ogg(d, o):
    pos, n = o, len(d)
    while pos + 27 <= n and bytes(d[pos:pos + 4]) == b"OggS":
        ns = d[pos + 26]
        if pos + 27 + ns > n:
            return None
        size = 27 + ns + sum(d[pos + 27:pos + 27 + ns])
        eos = d[pos + 5] & 4
        pos += size
        if eos:
            return pos - o
    return None


def _len_glb(d, o):
    ln = _u32(d, o + 8)
    return ln if 20 <= ln <= len(d) - o else None


def _len_midi(d, o):
    pos, n = o + 14, len(d)
    for _ in range(_u16(d, o + 10)):
        if pos + 8 > n or bytes(d[pos:pos + 4]) != b"MTrk":
            return None
        pos += 8 + _b32(d, pos + 4)
    return pos - o if pos <= n else None


def _len_sqlite(d, o):
    ps = struct.unpack_from(">H", d, o + 16)[0] or 65536
    pg = _b32(d, o + 28)
    ln = ps * pg
    return ln if pg and ln <= len(d) - o else None


def _len_zip(d, o):
    k = bytes(d[o:o + 64 * 1024 * 1024]).find(b"PK\x05\x06")
    if k < 0 or o + k + 22 > len(d):
        return None
    return k + 22 + _u16(d, o + k + 20)


_SIGS = [
    ("png", b"\x89PNG\r\n\x1a\n", ".png", _len_png),
    ("jpeg", b"\xff\xd8\xff", ".jpg", lambda d, o: _jpeg_len(d, o)),
    ("gif", b"GIF89a", ".gif", _len_gif), ("gif", b"GIF87a", ".gif", _len_gif),
    ("riff", b"RIFF", None, _len_riff),
    ("ogg", b"OggS\x00\x02", ".ogg", _len_ogg),
    ("glb", b"glTF\x02\x00\x00\x00", ".glb", _len_glb),
    ("midi", b"MThd\x00\x00\x00\x06", ".mid", _len_midi),
    ("sqlite", b"SQLite format 3\x00", ".sqlite", _len_sqlite),
    ("zip", b"PK\x03\x04", ".zip", _len_zip),
    ("dds", b"DDS \x7c\x00\x00\x00", ".dds", None),
    ("fbx", b"Kaydara FBX Binary  \x00\x1a\x00", ".fbx", None),
    ("flac", b"fLaC\x00\x00\x00\x22", ".flac", None),
    ("quake-pak", b"PACK", ".pak", None),
    ("unityfs", b"UnityFS\x00", ".unity3d", None),
    ("7z", b"7z\xbc\xaf\x27\x1c", ".7z", None),
    ("gzip", b"\x1f\x8b\x08", ".gz", None),
]
_SIG_RE = re.compile(b"|".join(b"(%s)" % re.escape(s[1]) for s in _SIGS), re.S)
_RIFF_EXT = {b"WAVE": ".wav", b"WEBP": ".webp", b"AVI ": ".avi"}


def _as_carve(path, outdir=None, max_items: int = 200, min_size: int = 64) -> dict:
    """Cari tanda tangan berkas di dalam berkas apa pun. Yang panjangnya bisa dipastikan (PNG, JPEG, GIF, OGG, RIFF, GLB, MIDI, SQLite, ZIP)
    dipotong ke outdir/carved/; yang lain (DDS, FBX, FLAC, PAK ...) hanya dilaporkan offsetnya."""
    try:
        out = _Out(outdir) if outdir else None
        hits = []
        with _map(path) as d:
            n = len(d)
            lim = min(n, MAX_CARVE_SCAN)
            pos = 0
            while len(hits) < max_items:
                m = _SIG_RE.search(d, pos, lim)
                if not m:
                    break
                o = m.start()
                sig = _SIGS[m.lastindex - 1]
                nm, ext, fn = sig[0], sig[2], sig[3]
                ln = None
                try:
                    ln = fn(d, o) if fn else None
                except (struct.error, IndexError, ValueError):
                    ln = None
                if nm == "riff" and ln:
                    ext = _RIFF_EXT.get(bytes(d[o + 8:o + 12]), ".riff")
                    nm = "riff/" + ext[1:]
                elif nm == "riff":
                    pos = o + 4
                    continue
                if nm == "gzip" and (ln is None):
                    pos = o + 3   # terlalu banyak positif palsu untuk dilaporkan tanpa panjang
                    continue
                if ln is not None and ln < min_size:
                    pos = o + 4
                    continue
                if nm == "quake-pak" and not (o + 12 <= n and _u32(d, o + 8) % 64 == 0 and 0 < _u32(d, o + 8) < n):
                    pos = o + 4
                    continue
                h = {"offset": o, "type": nm, "length": ln, "whole_file": bool(o == 0 and ln == n)}
                if out and ln and not h["whole_file"]:
                    t = out.write("carved/0x%08X%s" % (o, ext), bytes(d[o:o + ln]), "carved", nm)
                    h["file"] = out.files[-1]["path"] if t else None
                hits.append(h)
                pos = o + (ln if ln else len(sig[1]))
        res = {"status": "success", "path": str(path), "hits": hits, "count": len(hits)}
        if out:
            res.update(outdir=str(out.root), skipped=out.skipped, errors=out.errors)
        return res
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def _carve_text(res: dict) -> str:
    if res.get("status") != "success":
        return "CARVE gagal: %s" % res.get("message")
    if not res["hits"]:
        return "CARVE: tidak ada tanda tangan berkas dikenal di dalam berkas ini."
    L = ["CARVE: %d tanda tangan ditemukan" % res["count"]]
    for h in res["hits"][:60]:
        L.append("  0x%08X  %-14s %s%s" % (h["offset"], h["type"], _as_human(h["length"]) if h["length"] else "(panjang tidak bisa dipastikan)",
                                          "  -> " + h["file"] if h.get("file") else ""))
    if res["count"] > 60:
        L.append("  ... +%d lagi" % (res["count"] - 60))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Cadangan: berkas tak dikenal (teks / biner)
# ---------------------------------------------------------------------------

def _fallback_inspect(d, p):
    n = len(d)
    samp = bytes(d[:1024 * 1024])
    ent = _as_entropy(samp)
    printable = sum(1 for b in samp[:65536] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(samp[:65536]))
    L = []
    if printable > 0.95 and samp:
        txt = samp[:200000].decode("utf-8", "replace")
        first = _as_clean(txt.strip().split("\n", 1)[0], 100)
        kind = "teks"
        s = txt.lstrip()[:1]
        if s in "{[":
            try:
                json.loads(bytes(d[:8 * 1024 * 1024]).decode("utf-8-sig"))
                kind = "JSON"
            except Exception:
                pass
        elif s == "<":
            kind = "XML / HTML"
        L.append("%s, %d baris, baris pertama: %s" % (kind, bytes(d[:8 * 1024 * 1024]).count(b"\n") + 1, first))
    else:
        L.append("biner tanpa format dikenal: entropi %.2f/8%s" % (ent, " (kemungkinan terkompresi / terenkripsi)" if ent > 7.5 else ""))
        res = _as_carve(p, None, max_items=12)
        if res.get("hits"):
            L.append("berkas tertanam terdeteksi:")
            L += ["  0x%08X %s%s" % (h["offset"], h["type"], " (%s)" % _as_human(h["length"]) if h["length"] else "") for h in res["hits"][:12]]
            L.append("gunakan carve / --carve untuk memotongnya keluar.")
        else:
            L.append("tidak ada tanda tangan berkas dikenal. Jika ini format game, tulis plugin atau kirim contoh untuk dibuatkan parser.")
    return {"lines": L, "extract": "tidak ada (format tidak dikenal); coba carve"}


register("unknown", "unknown", lambda d, e: True, _fallback_inspect, None, 999, "cadangan")


# ---------------------------------------------------------------------------
# API publik
# ---------------------------------------------------------------------------

def _ext(path) -> str:
    return Path(str(path)).suffix.lower()


def identify(path) -> dict:
    try:
        with _map(path) as d:
            f = _detect(d, _ext(path))
            return {"status": "success", "format": f.name if f else "unknown", "category": f.category if f else "unknown", "size": len(d),
                    "can_extract": bool(f and f.extract)}
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def describe(path) -> dict:
    try:
        p = Path(str(path))
        with _map(p) as d:
            f = _detect(d, _ext(p))
            rep = {"status": "success", "path": str(p), "name": _as_clean(p.name, 120), "size": len(d), "sha256": _sha256(d),
                   "format": f.name if f else "unknown", "category": f.category if f else "unknown", "lines": [], "can_extract": bool(f and f.extract)}
            if f and f.inspect:
                try:
                    r = f.inspect(d, p) or {}
                    rep["lines"] = [_as_clean(x, 400) for x in r.get("lines", [])]
                    rep["extract_hint"] = r.get("extract", "")
                    if "entries" in r:
                        rep["entries"] = r["entries"]
                except Exception as e:
                    rep["lines"] = ["%s: gagal dibaca (%s: %s)" % (f.name, type(e).__name__, _as_clean(e, 150))]
                    rep["parse_error"] = True
            return rep
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def describe_text(path, max_chars: int = 0) -> str:
    r = describe(path)
    if r.get("status") != "success":
        return "ASSETS gagal: %s" % r.get("message")
    L = ["ASSET EXPLORER (REA v%s)" % _as_VERSION,
         "Berkas : %s | %s | SHA-256 %s..." % (r["name"], _as_human(r["size"]), r["sha256"][:16]),
         "Format : %s (%s)" % (r["format"], r["category"])] + r["lines"]
    if r.get("extract_hint"):
        L.append("Bisa diekstrak: %s" % r["extract_hint"])
    t = "\n".join(L)
    return t if not max_chars or len(t) <= max_chars else t[:max_chars - 30] + "\n[...dipangkas...]"


_CONVERTIBLE = {".dds", ".tga", ".bmp", ".glb", ".gltf", ".fbx", ".stl", ".ply", ".dae", ".bvh"}


def _convert_tree(out: _Out, t_budget: float = 120.0):
    import time
    t0 = time.time()
    todo = [f for f in list(out.files) if f.get("kind") == "archive-entry" and _ext(f["path"]) in _CONVERTIBLE][:2000]
    done = 0
    for f in todo:
        if time.time() - t0 > t_budget:
            out.errors.append("konversi dihentikan: melewati batas waktu %d dtk" % t_budget)
            break
        src = out.root / f["path"]
        sub = _Out(out.root / "_converted" / Path(f["path"]).with_suffix("").as_posix())
        try:
            with _map(src) as d:
                fm = _detect(d, _ext(src))
                if fm and fm.extract:
                    fm.extract(d, src, sub, {})
        except Exception as e:
            out.errors.append("konversi %s: %s" % (_as_clean(f["path"], 60), _as_clean(e, 90)))
        for sf in sub.files:
            sf = dict(sf)
            sf["path"] = (Path("_converted") / Path(f["path"]).with_suffix("") / sf["path"]).as_posix()
            sf["note"] = ("hasil konversi dari %s" % f["path"] + (" | " + sf["note"] if sf["note"] else ""))
            out.files.append(sf)
            out.total += sf["size"]
        out.errors += ["%s: %s" % (_as_clean(f["path"], 50), e) for e in sub.errors]
        done += 1
    return done


def extract(path, outdir, pattern=None, convert: bool = True) -> dict:
    """Keluarkan isi berkas ke outdir. Mengembalikan manifest; status 'success' | 'partial' | 'error'."""
    try:
        p = Path(str(path))
        with _map(p) as d:
            f = _detect(d, _ext(p))
            if not f or not f.extract:
                return {"status": "error", "code": "no_extractor", "format": f.name if f else "unknown",
                        "message": "tidak ada pengekstrak untuk format %s%s" % (f.name if f else "tak dikenal", "; coba carve()" if not f or f.category == "unknown" else "")}
            out = _Out(outdir)
            opts = {"pattern": pattern, "convert": bool(convert)}
            try:
                f.extract(d, p, out, opts)
            except Exception as e:
                out.errors.append("%s: %s" % (type(e).__name__, _as_clean(e, 160)))
            converted = _convert_tree(out) if convert and f.category == "archive" else 0
            ok = bool(out.files)
            man = {"status": ("partial" if out.errors or out.skipped else "success") if ok else "error", "format": f.name, "source": str(p), "outdir": str(out.root),
                   "entries_extracted": len(out.files), "entries_skipped": len(out.skipped), "entries_failed": len(out.errors), "converted_items": converted,
                   "files": out.files, "skipped": out.skipped, "errors": out.errors}
            if not ok:
                man["message"] = "tidak ada yang berhasil diekstrak" + (": " + out.errors[0] if out.errors else "")
            try:
                (out.root / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
                man["manifest_path"] = str(out.root / "manifest.json")
            except OSError:
                pass
            return man
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def extract_text(path, outdir, pattern=None, convert: bool = True) -> str:
    m = extract(path, outdir, pattern, convert)
    if m.get("status") == "error":
        return "EKSTRAK gagal: %s" % m.get("message")
    L = ["EKSTRAK %s: %d berkas ke %s (dilewati %d, galat %d%s)" % (m["format"], m["entries_extracted"], m["outdir"], m["entries_skipped"], m["entries_failed"],
                                                                 ", %d hasil konversi" % m["converted_items"] if m["converted_items"] else "")]
    for f in m["files"][:30]:
        L.append("  %s  %s%s" % (f["path"], _as_human(f["size"]), "  (%s)" % f["note"] if f["note"] else ""))
    if m["entries_extracted"] > 30:
        L.append("  ... +%d lagi (lihat manifest.json)" % (m["entries_extracted"] - 30))
    L += ["  dilewati: %s (%s)" % (s["path"], s["reason"]) for s in m["skipped"][:5]]
    L += ["  galat: %s" % e for e in m["errors"][:5]]
    return "\n".join(L)


def _init_plugins():
    pf = os.environ.get("REA_PLUGINS", "")
    if pf:
        load_plugins(pf)


_AS_RENAMED = {'VERSION': '_as_VERSION', '_clean': '_as_clean', '_entropy': '_as_entropy', '_human': '_as_human', 'carve': '_as_carve'}
_AS_PUBLIC = frozenset(['MAX_ACCESSOR', 'MAX_CARVE_SCAN', 'MAX_ENTRIES', 'MAX_OUT_FILE', 'MAX_OUT_TOTAL', 'MAX_PIXELS', 'MAX_XML', 'VERSION', '_ARR', '_Arc', '_CONVERTIBLE', '_CT', '_DXGI', '_DXGI_NAMES', '_FBX_MAGIC', '_FBX_TICKS', '_FORMATS', '_Fmt', '_LOADED_PLUGINS', '_MP3_BR', '_MP3_SR', '_NT', '_ObjBuilder', '_Out', '_PLY_T', '_PNG_CT', '_RESERVED', '_RIFF_EXT', '_SIGS', '_SIG_RE', '_UPAK_MAGIC', '_add_archive', '_arc_extract_factory', '_arc_inspect_factory', '_b32', '_bmp_decode', '_bmp_extract', '_bmp_inspect', '_bvh_extract', '_bvh_inspect', '_bvh_parse', '_c565', '_carve_text', '_clean', '_convert_tree', '_cstr', '_csv_text', '_dae_extract', '_dae_floats', '_dae_inspect', '_dae_root', '_data_uri', '_dds_decode', '_dds_extract', '_dds_info', '_dds_inspect', '_detect', '_dxt_decode', '_entropy', '_ext', '_external', '_fallback_inspect', '_fbx_ascii_inspect', '_fbx_child', '_fbx_cname', '_fbx_extract', '_fbx_inspect', '_fbx_objects', '_fbx_parse', '_fbx_props', '_flac_inspect', '_fstr', '_gif_inspect', '_gif_walk', '_gltf_acc', '_gltf_bufs', '_gltf_extract', '_gltf_inspect', '_gltf_load', '_gltf_prim_tris', '_gz_head', '_gzip', '_human', '_ico_inspect', '_init_plugins', '_is_bvh', '_is_dae', '_is_fbx_ascii', '_is_fbx_bin', '_is_glb', '_is_gltf', '_is_obj', '_is_tar_raw', '_jpeg_inspect', '_jpeg_len', '_len_gif', '_len_glb', '_len_midi', '_len_ogg', '_len_png', '_len_riff', '_len_sqlite', '_len_zip', '_map', '_midi_inspect', '_mp3_detect', '_mp3_inspect', '_mp3_start', '_obj_inspect', '_obj_name', '_ogg_inspect', '_ply_extract', '_ply_header', '_ply_inspect', '_ply_read', '_png_encode', '_png_inspect', '_png_walk', '_qpak', '_safe_rel', '_sha256', '_sql_extract', '_sql_inspect', '_sql_open', '_sql_tables', '_stl_extract', '_stl_inspect', '_stl_kind', '_stl_tris', '_tag', '_tar', '_tga_decode', '_tga_extract', '_tga_inspect', '_tga_ok', '_u16', '_u32', '_u64', '_unity_inspect', '_upak', '_upak_detect', '_upak_entry', '_wad', '_wav_inspect', '_webp_inspect', '_zip', 'carve', 'describe', 'describe_text', 'extract', 'extract_text', 'formats', 'i', 'identify', 'load_plugins', 'register'])
_AS_API = None


class _AssetsAPI:
    """Fasad pengganti `import rea_assets`: hanya nama publik bagian Asset Explorer yang bisa diakses (nama bentrok dipetakan ke _as_*)."""
    __slots__ = ()

    def __getattr__(self, name):
        if name not in _AS_PUBLIC:
            raise AttributeError(name)
        return globals()[_AS_RENAMED.get(name, name)]


def _assets_mod():
    """Asset Explorer (dulu rea_assets.py). Plugin REA_PLUGINS dimuat malas di pemanggilan pertama, seperti saat modul itu diimpor."""
    global _AS_API
    if _AS_API is None:
        _init_plugins()
        _AS_API = _AssetsAPI()
    return _AS_API


def assets_text(path, max_chars: int = 0) -> str:
    """v99: ringkasan ISI berkas non-exe (model 3D, animasi, tekstur, audio, arsip, SQLite ...). Gagal -> pesan, tidak melempar."""
    mod = _assets_mod()
    if mod is None:
        return "Asset Explorer (rea_assets.py) tidak ditemukan di folder yang sama; fitur isi berkas tidak tersedia."
    try:
        return mod.describe_text(path, max_chars=max_chars)
    except Exception as e:
        return "ASSETS gagal (%s: %s)." % (type(e).__name__, str(e)[:120])


def assets_extract(path, outdir, pattern=None, convert: bool = True) -> dict:
    """v99: keluarkan isi berkas ke outdir (mesh -> .obj, animasi -> .json / .csv, tekstur -> .png, entri arsip, tabel -> .csv). Mengembalikan manifest."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    return mod.extract(path, outdir, pattern=pattern, convert=convert)


def assets_carve(path, outdir=None) -> dict:
    """v99: cari (dan bila outdir diberikan, potong) berkas yang tertanam di dalam berkas apa pun."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    return mod.carve(path, outdir)


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
    if "--re" in argv:       # --re FILE [--compact]
        t = [x for x in argv[argv.index("--re") + 1:] if not x.startswith("--")]
        print(re_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --re FILE")
        raise SystemExit(0)
    if "--xref" in argv:     # --xref FILE QUERY
        t = argv[argv.index("--xref") + 1:]
        print(xref_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --xref FILE QUERY (nama API, potongan string, atau VA fungsi)")
        raise SystemExit(0)
    if "--yarascan" in argv:   # --yarascan FILE RULES
        t = argv[argv.index("--yarascan") + 1:]
        print(yara_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --yarascan FILE RULES(.yar atau folder)")
        raise SystemExit(0)
    if "--unpack" in argv:   # --unpack FILE OUTDIR
        t = argv[argv.index("--unpack") + 1:]
        print(unpack_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --unpack FILE OUTDIR")
        raise SystemExit(0)
    if "--disasm" in argv:   # --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N]
        t = argv[argv.index("--disasm") + 1:]
        print(disasm_text(t[0], t[1] if len(t) > 1 else "entry", int(t[2], 0) if len(t) > 2 else 40, t[3] if len(t) > 3 else None) if t else "pemakaian: --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N] [ARCH]")
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
    if "--plugins" in argv:  # --plugins FOLDER (muat parser buatan sendiri; menjalankan kode di folder itu)
        _k = argv.index("--plugins")
        _m = _assets_mod()
        if _m is not None and _k + 1 < len(argv):
            print("plugin:", ", ".join(_m.load_plugins(argv[_k + 1])) or "(tidak ada)", file=sys.stderr)
        argv = argv[:_k] + argv[_k + 2:]
    if "--formats" in argv:   # daftar parser Asset Explorer
        _m = _assets_mod()
        for _f in (_m.formats() if _m else []):
            print("%-12s %-10s inspect=%s extract=%s%s  %s" % (_f["name"], _f["category"], "ya" if _f["inspect"] else "-", "ya" if _f["extract"] else "-", " [plugin]" if _f["plugin"] else "", _f["about"]))
        raise SystemExit(0)
    if "--assets" in argv:   # --assets FILE
        t = [x for x in argv[argv.index("--assets") + 1:] if not x.startswith("--")]
        print(assets_text(t[0]) if t else "pemakaian: --assets FILE")
        raise SystemExit(0)
    if "--assets-extract" in argv:   # --assets-extract OUTDIR FILE [pola] [--no-convert]
        k = argv.index("--assets-extract")
        _out = argv[k + 1] if k + 1 < len(argv) else "rea_assets_out"
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        if not _rest:
            print("pemakaian: --assets-extract OUTDIR FILE [pola] [--no-convert]")
            raise SystemExit(1)
        _m = assets_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, convert="--no-convert" not in argv)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s konversi=%s | manifest: %s%s" % (_m.get("status"), _m.get("entries_extracted"), _m.get("entries_skipped"), _m.get("entries_failed"),
              _m.get("converted_items"), _m.get("manifest_path"), (" | " + _m["message"]) if _m.get("message") else ""))
        raise SystemExit(0 if _m.get("status") in ("success", "partial") else 1)
    if "--assets-carve" in argv:   # --assets-carve FILE [OUTDIR]
        t = [x for x in argv[argv.index("--assets-carve") + 1:] if not x.startswith("--")]
        _m = _assets_mod()
        if not t or _m is None:
            print("pemakaian: --assets-carve FILE [OUTDIR]")
        else:
            print(getattr(_m, "_carve_text", lambda r: json.dumps(r, ensure_ascii=False, indent=2, default=str))(assets_carve(t[0], t[1] if len(t) > 1 else None)))
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
        print("pemakaian: python rea_triage.py <file|folder> [--compact] [--card] [--json] [--ioc] [--raw (tanpa defang)] [--yara] [--carve DIR] | --hex FILE [OFFSET [LENGTH]] | --compare A B | --list <container> | --extract OUTDIR <container> [pola] [--scan] | --similar A B | --md FILE | --ctph FILE | --re FILE | --xref FILE QUERY | --disasm FILE [AT [N [ARCH]]] | --unpack FILE OUTDIR | --yarascan FILE RULES | --assets FILE | --assets-extract OUTDIR FILE [pola] [--no-convert] | --assets-carve FILE [OUTDIR] | --formats | --plugins FOLDER | --api JSON")
    elif Path(args[0]).is_dir():
        print(triage_dir_text(args[0], defang="--raw" not in flags))
    elif "--card" in flags and not ({"--json", "--ioc", "--yara"} & flags):
        print(triage_text(args[0], defang="--raw" not in flags, card=True))
    elif "--json" in flags or "--ioc" in flags:
        print(triage_json(args[0], ioc_only="--ioc" in flags))
    elif "--yara" in flags:
        print(yara_draft(triage(args[0])))
    else:
        full, _note = triage_bundle(args[0], carve_dir=cdir) if cdir else (None, None)
        print(full if full is not None else triage_text(args[0], compact="--compact" in flags, defang="--raw" not in flags))
