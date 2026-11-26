# rea_triage bagian 01/47: dasar (baris asli 265-411). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
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
MAX_ZIP_CD = 32 * 1024 * 1024        # v104: ukuran DIREKTORI PUSAT maksimal; jumlah entri saja tidak cukup (nama + extra + komentar bisa ~64 KB per entri = puluhan GB)

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


def _write_atomic_nofollow(path, data: bytes, mode: int = 0o644) -> None:
    """v104: tulis berkas lewat berkas sementara unik (O_EXCL|O_NOFOLLOW) lalu os.replace atomik. Tidak pernah menulis lewat symlink di
    tujuan (replace mengganti link itu sendiri); tujuan yang berupa direktori ditolak."""
    path = Path(os.fspath(path))
    if path.is_dir() and not path.is_symlink():
        raise IsADirectoryError(str(path))
    tmp = path.with_name(".%s.%s.tmp" % (path.name, os.urandom(6).hex()))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(str(tmp), flags, mode)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(str(tmp), str(path))
    except BaseException:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
        raise


def _secure_key_file(kp) -> bool:
    """v104: berkas kunci hanya boleh dibaca pemiliknya. POSIX: chmod 0600 sudah cukup. Windows: mode 0o600 TIDAK mengunci ACL, jadi
    warisan ACL dilepas dan hanya pengguna sekarang yang diberi akses (icacls); gagal = False (kunci tidak disimpan)."""
    if os.name != "nt":
        return True
    try:
        import subprocess
        user = os.environ.get("USERNAME", "")
        if not user:
            return False
        dom = os.environ.get("USERDOMAIN", "")
        if dom:   # DOMAIN\\USER: tanpa domain, nama pendek bisa gagal / salah terurai pada akun domain atau akun Microsoft
            user = "%s\\%s" % (dom, user)
        r_ = subprocess.run(["icacls", str(kp), "/inheritance:r", "/grant:r", "%s:F" % user],
                            capture_output=True, timeout=10)
        return r_.returncode == 0
    except Exception:
        return False


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

