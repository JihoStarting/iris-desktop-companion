# rea_triage bagian 44/47: mesin_ekstraksi (baris asli 21818-23246). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------------------------------
# Mesin ekstraksi container (dulu rea_extract.py)
# ---------------------------------------------------------------------------------------------------
_EX_DOC = """rea_extract.py - mesin ekstraksi / penjelajahan container untuk REA (v95; dipanggil lewat jembatan tipis di rea_triage.py).

Hanya pustaka standar. TIDAK menjalankan apa pun dari berkas; container hanya dibaca, hasil selalu ditulis ke workspace terpisah.
Format: ZIP (termasuk APK / JAR / SFX), TAR (+ gz / bz2 / xz / zst), GZIP / BZIP2 / XZ / ZSTD tunggal, ISO 9660 (Joliet / Rock Ridge, sektor 2048 / raw 2352),
ISO PSP (UMD: membaca PSP_GAME/PARAM.SFO) dan CSO PSP (zlib per blok) yang berisi ISO. ZSO (LZ4) dan 7z / RAR belum didukung (dilaporkan jelas).

Kontrak yang dipakai rea_triage.py (jangan diubah tanpa mengubah pemanggilnya):
    open_container(path)  -> {"status": "success", "container_id", "format", ...} | {"status": "error", "code", "message"}
    close_container(container_id)
    extract_selected(container_id, selector, outdir, scan=False) -> manifest dict
          selector: None | {"pattern": "*.dll;*.exe" | "re:...", "paths": [...], "exclude": "...", "max_size": N, "max_entries": N}
          pola TANPA wildcard (* ? [) dicocokkan sebagai potongan nama (huruf besar / kecil diabaikan)
          manifest: status success | partial | error, entries_extracted / entries_skipped / entries_failed, manifest_path, files, skipped, errors ...
    describe_container_text(path, max_chars=0) -> str

Tambahan (aditif): list_entries(cid), describe_container(path), extract(path, outdir, pattern=None, scan=False), formats().

Workspace keluaran (outdir): extracted/ (isi), manifests/manifest.json (tidak menimpa; manifest_2.json dst), logs/extract.log.

Pengerasan: path entri dinetralkan (zip-slip, '..', path absolut, huruf drive, nama perangkat Windows, karakter ilegal), tidak menimpa berkas,
tautan simbolik / berkas khusus TIDAK diekstrak, berkas terenkripsi dilewati, batas jumlah entri / ukuran per berkas / total / rasio kompresi (zip bomb),
berkas dibuka sekali dengan fstat (tolak FIFO / perangkat / folder), keluaran dibersihkan dari baris baru. Container di dalam container TIDAK diekstrak otomatis.

CLI:  python rea_extract.py list FILE | extract FILE OUTDIR [pola] [--scan] | formats
"""


import bz2
import fnmatch
import gzip
import hashlib
import io
import json
import lzma
import math
import os
import re
import secrets
import stat
import struct
import sys
import tarfile
import threading
import time
import zipfile
import zlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ex_VERSION = "95.0"

_ex_MAX_ENTRIES = 200_000
MAX_ENTRY_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 ** 3
MAX_RATIO = 200                       # byte keluar per byte terkompresi ...
RATIO_FLOOR = 64 * 1024 * 1024        # ... baru dianggap mencurigakan setelah melewati ini
COPY_CHUNK = 1024 * 1024
LIST_TIME = 60.0                      # detik untuk membuat daftar entri (tar.gz besar)
MAX_LIST_ROWS = 200
MAX_OPEN = 16
MAX_DIR_BYTES = 16 * 1024 * 1024      # satu direktori ISO
MAX_DEPTH = 64
SOURCE_HASH_LIMIT = 2 * 1024 ** 3

_EXEC_EXT = {".exe", ".dll", ".scr", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".hta", ".lnk", ".msi", ".jar",
             ".sh", ".elf", ".so", ".pif", ".cpl", ".sys", ".apk", ".dex", ".py", ".pyc"}
_ARCHIVE_TYPES = {"ZIP", "GZIP", "BZIP2", "XZ", "ZSTD", "7z", "RAR", "TAR", "ISO 9660", "CAB", "OLE / Office lama"}
_ex_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}


class ContainerError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _Limit(Exception):
    pass


# ---------------------------------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------------------------------

def _ex_clean(s, n: int = 200) -> str:
    """Buang karakter kontrol / pemisah baris (anti injeksi ke laporan)."""
    return "".join(c if c.isprintable() else "?" for c in str(s))[:n]


def _ex_human(n) -> str:
    if n is None or n < 0:
        return "?"
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%d %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f GB" % n


def _ex_err(code: str, message, **kw) -> dict:
    d = {"status": "error", "code": code, "message": _ex_clean(message, 300)}
    d.update(kw)
    return d


def _ts(t):
    try:
        return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds") if t else None
    except (OverflowError, OSError, ValueError):
        return None


def _ex_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values())


def _ex_safe_rel(path: str):
    """Netralkan path entri jadi path relatif aman. Mengembalikan (rel, unsafe: bool). unsafe = ada '..', path absolut, atau huruf drive."""
    raw = str(path).replace("\\", "/")
    unsafe = raw.startswith("/") or bool(re.match(r"^[A-Za-z]:", raw)) or any(p == ".." for p in raw.split("/"))
    parts = []
    for part in raw.split("/"):
        if part in ("", ".", ".."):
            continue
        part = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]", "_", part).rstrip(". ")
        if not part:
            part = "_"
        if part.split(".")[0].upper() in _ex_RESERVED:
            part = "_" + part
        if len(part) > 120:
            stem, dot, ext = part.rpartition(".")
            part = (stem[:100] + "." + ext[:15]) if dot and len(ext) <= 15 else part[:120]
        parts.append(part)
    parts = parts[-MAX_DEPTH:]
    rel = "/".join(parts) or "unnamed"
    return rel[-240:], unsafe


def _sniff(head: bytes) -> str:
    """Jenis berkas dari magic bytes (bukan ekstensi)."""
    h = head
    if h[:2] == b"MZ":
        if len(h) >= 0x40:
            pe = struct.unpack_from("<I", h, 0x3C)[0]
            if pe + 4 <= len(h) and h[pe:pe + 4] == b"PE\0\0":
                return "PE"
        return "PE" if len(h) < 0x40 else "DOS MZ"
    if h[:4] == b"\x7fELF":
        return "ELF"
    if h[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"):
        return "Mach-O / class"
    if h[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        return "ZIP"
    if h[:2] == b"\x1f\x8b":
        return "GZIP"
    if h[:3] == b"BZh":
        return "BZIP2"
    if h[:6] == b"\xfd7zXZ\x00":
        return "XZ"
    if h[:4] == b"\x28\xb5\x2f\xfd":
        return "ZSTD"
    if h[:6] == b"7z\xbc\xaf\x27\x1c":
        return "7z"
    if h[:4] == b"Rar!":
        return "RAR"
    if h[:4] == b"MSCF":
        return "CAB"
    if h[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "OLE / Office lama"
    if h[:5] == b"%PDF-":
        return "PDF"
    if h[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if h[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF"
    if h[:4] == b"RIFF":
        return "RIFF"
    if h[:4] == b"OggS":
        return "OGG"
    if h[:16] == b"SQLite format 3\0":
        return "SQLite"
    if h[:4] == b"\x4c\x00\x00\x00" and h[4:20] == b"\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46":
        return "LNK"
    if h[:4] == b"\x00PBP":
        return "PSP PBP"
    if h[:4] == b"~PSP":
        return "PSP PRX terenkripsi"
    if h[:4] == b"\x00PSF":
        return "PSP SFO"
    if h[:4] == b"CISO":
        return "CSO"
    if h[:4] == b"\x7fSCE":
        return "SCE"
    if h[257:262] == b"ustar":
        return "TAR"
    if h[:2] == b"#!":
        return "skrip (shebang)"
    if len(h) > 32769 and h[32769:32774] == b"CD001":
        return "ISO 9660"
    if h and all(c in b"\t\r\n\x0b\x0c" or 0x20 <= c < 0x7F or c >= 0x80 for c in h[:512]) and b"\x00" not in h[:512]:
        return "teks"
    return "data"


# ---------------------------------------------------------------------------------------------------
# Entri dan pembaca citra
# ---------------------------------------------------------------------------------------------------

class Entry:
    __slots__ = ("index", "path", "size", "packed", "kind", "mtime", "encrypted", "ref", "note")

    def __init__(self, index, path, size=0, packed=0, kind="file", mtime=None, encrypted=False, ref=None, note=""):
        self.index, self.path, self.size, self.packed, self.kind = index, path, size, packed, kind
        self.mtime, self.encrypted, self.ref, self.note = mtime, encrypted, ref, note

    def as_dict(self) -> dict:
        return {"index": self.index, "path": _ex_clean(self.path, 300), "size": self.size, "packed": self.packed, "kind": self.kind,
                "mtime": _ts(self.mtime), "encrypted": self.encrypted, "note": self.note}


class _FileImg:
    """Akses acak ke berkas yang sudah dibuka (satu fh, dikunci)."""

    def __init__(self, fh, size):
        self.fh, self.size, self.lock = fh, size, threading.Lock()

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0:
            return b""
        with self.lock:
            self.fh.seek(off)
            return self.fh.read(n)


class _CsoImg:
    """CSO / CISO PSP: indeks u32 per blok (bit 31 = blok tidak terkompresi), blok = raw deflate. Menyajikan citra ISO penuh."""

    def __init__(self, base: _FileImg):
        self.base = base
        hdr = base.read_at(0, 24)
        if len(hdr) < 24:
            raise ContainerError("corrupt", "header CSO terpotong")
        _m, hsz, total, bsz, ver, align = struct.unpack("<4sIQIBB2x", hdr)
        if ver > 1 and ver != 2:
            raise ContainerError("unsupported_format", "versi CSO %d tidak dikenal" % ver)
        if bsz < 512 or bsz > (1 << 20) or (bsz & (bsz - 1)):
            raise ContainerError("corrupt", "ukuran blok CSO tidak valid: %d" % bsz)
        if total == 0 or total > (1 << 37):
            raise ContainerError("corrupt", "ukuran total CSO tidak valid: %d" % total)
        n = (total + bsz - 1) // bsz
        raw = base.read_at(24, (n + 1) * 4)
        if len(raw) < (n + 1) * 4:
            raise ContainerError("corrupt", "indeks CSO terpotong")
        self.index = struct.unpack("<%dI" % (n + 1), raw)
        self.bsz, self.align, self.size, self.nblocks = bsz, align, total, n
        self._cache: dict = {}
        self._lock = threading.Lock()

    def _block(self, i: int) -> bytes:
        with self._lock:
            b = self._cache.get(i)
        if b is not None:
            return b
        idx, nxt = self.index[i], self.index[i + 1]
        pos, end = (idx & 0x7FFFFFFF) << self.align, (nxt & 0x7FFFFFFF) << self.align
        if end < pos or end - pos > self.bsz * 2 + 1024 or pos >= self.base.size:
            raise ContainerError("corrupt", "indeks blok CSO %d tidak masuk akal" % i)
        data = self.base.read_at(pos, end - pos)
        if idx & 0x80000000:
            b = data[:self.bsz]
        else:
            try:
                b = zlib.decompressobj(-15).decompress(data, self.bsz)
            except zlib.error as e:
                raise ContainerError("corrupt", "blok CSO %d rusak: %s" % (i, e))
        with self._lock:
            if len(self._cache) > 16:
                self._cache.clear()
            self._cache[i] = b
        return b

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0 or off >= self.size:
            return b""
        n = min(n, self.size - off)
        out = []
        while n > 0:
            i, w = divmod(off, self.bsz)
            blk = self._block(i)[w:w + n]
            if not blk:
                break
            out.append(blk)
            off += len(blk)
            n -= len(blk)
        return b"".join(out)


# ---------------------------------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------------------------------

class _Handler:
    fmt = "?"
    label = "?"
    sequential = False      # True: data hanya bisa dibaca berurutan (tar terkompresi) -> iter_data()

    def __init__(self):
        self.entries: list[Entry] = []
        self.truncated = False
        self.info: dict = {}
        self.notes: list[str] = []

    def open_entry(self, e: Entry):
        raise NotImplementedError

    def iter_data(self, wanted: set):
        raise NotImplementedError

    def close(self):
        pass


class _ZipHandler(_Handler):
    fmt, label = "zip", "ZIP"

    def __init__(self, fh, size, name):
        super().__init__()
        if _zip_cd_bytes(fh) > MAX_ZIP_CD:   # v104
            raise ContainerError("corrupt", "direktori pusat ZIP terlalu besar (> %d byte)" % MAX_ZIP_CD)
        try:
            self.zf = zipfile.ZipFile(fh)
        except (zipfile.BadZipFile, EOFError, OSError, ValueError) as e:
            raise ContainerError("corrupt", "ZIP rusak: %s" % e)
        t0 = time.time()
        for i, zi in enumerate(self.zf.infolist()):
            if i >= _ex_MAX_ENTRIES or (i % 2000 == 0 and time.time() - t0 > LIST_TIME):
                self.truncated = True
                break
            mode = (zi.external_attr >> 16) & 0xFFFF if zi.create_system == 3 else 0
            if zi.filename.endswith("/") or zi.is_dir():
                kind = "dir"
            elif stat.S_ISLNK(mode):
                kind = "symlink"
            elif mode and not stat.S_ISREG(mode) and stat.S_IFMT(mode):
                kind = "other"
            else:
                kind = "file"
            try:
                mt = datetime(*zi.date_time, tzinfo=timezone.utc).timestamp()
            except (ValueError, OverflowError):
                mt = None
            self.entries.append(Entry(i, zi.filename.rstrip("/") if kind == "dir" else zi.filename, zi.file_size, zi.compress_size, kind, mt, bool(zi.flag_bits & 0x1), zi))
        if self.zf.comment:
            self.info["comment"] = _ex_clean(self.zf.comment.decode("utf-8", "replace"), 200)
        if any(e.path.endswith(("classes.dex", "AndroidManifest.xml")) for e in self.entries):
            self.info["hint"] = "APK / paket Android: gunakan analisis APK di rea_triage untuk manifest dan DEX"
        elif any(e.path == "META-INF/MANIFEST.MF" for e in self.entries):
            self.info["hint"] = "JAR (Java)"

    def open_entry(self, e):
        return self.zf.open(e.ref)

    def close(self):
        try:
            self.zf.close()
        except Exception:
            pass


class _TarHandler(_Handler):
    fmt, label, sequential = "tar", "TAR", True

    def __init__(self, fh, size, name, mode: str = "r:*", comp: str = ""):
        super().__init__()
        self.fh = fh
        self.comp = comp
        fh.seek(0)
        try:
            tf = tarfile.open(fileobj=fh, mode=mode)
        except tarfile.TarError as e:
            raise ContainerError("not_tar", "bukan TAR: %s" % e)
        except (OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            raise ContainerError("corrupt", "arsip rusak: %s" % e)
        t0 = time.time()
        try:
            for i, m in enumerate(tf):
                if i >= _ex_MAX_ENTRIES or (i % 2000 == 0 and time.time() - t0 > LIST_TIME):
                    self.truncated = True
                    break
                kind = "dir" if m.isdir() else "file" if m.isreg() else "symlink" if (m.issym() or m.islnk()) else "other"
                self.entries.append(Entry(i, m.name, m.size if kind == "file" else 0, 0, kind, m.mtime, False, None,
                                          ("-> " + _ex_clean(m.linkname, 80)) if kind == "symlink" else ""))
        except (tarfile.TarError, OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            if not self.entries:
                raise ContainerError("corrupt", "arsip rusak: %s" % e)
            self.truncated = True
            self.notes.append("arsip terpotong / rusak setelah %d entri: %s" % (len(self.entries), _ex_clean(e, 100)))
        finally:
            tf.close()
        if comp:
            self.label = "TAR + %s" % comp
            self.fmt = "tar." + {"gzip": "gz", "bzip2": "bz2", "xz": "xz", "zstd": "zst"}.get(comp, comp)
            self.packed_total = size

    def iter_data(self, wanted: set):
        self.fh.seek(0)
        tf = tarfile.open(fileobj=self.fh, mode="r:*")
        try:
            last = max(wanted) if wanted else -1
            for i, m in enumerate(tf):
                if i > last:
                    break
                if i in wanted:
                    yield self.entries[i], tf.extractfile(m)
        finally:
            tf.close()


class _SingleHandler(_Handler):
    """GZIP / BZIP2 / XZ yang bukan tar: satu berkas di dalamnya."""

    def __init__(self, fh, size, name, comp: str, data: bytes | None = None, zdict=None):
        super().__init__()
        self.fh, self.comp, self.size_c = fh, comp, size
        self.fmt, self.label = {"gzip": ("gzip", "GZIP"), "bzip2": ("bzip2", "BZIP2"), "xz": ("xz", "XZ"), "zstd": ("zstd", "ZSTD")}[comp]
        self._zdata = data                    # v99.34: isi berkas .zst (sudah divalidasi oleh _zstd_handler)
        self._zdict = zdict                   # v99.52: dictionary Zstd (None = tanpa)
        inner, mt, usize = None, None, -1
        if comp == "zstd":
            info: list = []
            try:
                _zstd_decompress(data or b"", head=16, verify=False, info=info, dictionary=zdict)
            except ValueError as e:
                raise ContainerError("corrupt", "aliran ZSTD rusak: %s" % _ex_clean(e, 120))
            fcs = info[0].get("content_size") if info else None
            usize = fcs if fcs is not None else -1
            if fcs is None:
                self.notes.append("ukuran isi tidak tercatat di header frame Zstd")
            self.notes.append("dekoder Zstd murni Python")
        if comp == "gzip":
            hdr = self._gz_header()
            if hdr is None:
                raise ContainerError("corrupt", "header GZIP tidak valid")
            inner, mt = hdr
            if size > 22:
                fh.seek(size - 4)
                usize = struct.unpack("<I", fh.read(4))[0]
                self.notes.append("ukuran dari trailer gzip (modulo 2^32)")
        if not inner:
            stem = Path(name).name
            for suf in (".gz", ".bz2", ".xz", ".tgz", ".gzip", ".bzip2", ".zst", ".zstd"):
                if stem.lower().endswith(suf):
                    stem = stem[:-len(suf)]
                    break
            inner = stem if stem and stem != Path(name).name else (stem or "data") + ".out"
        # uji bahwa aliran memang bisa didekompresi (Zstd sudah diuji di atas dengan mode intip)
        try:
            if comp != "zstd":
                s = self.open_entry(None)
                s.read(16)
                s.close()
        except (OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            raise ContainerError("corrupt", "aliran %s rusak: %s" % (self.label, e))
        self.entries.append(Entry(0, inner, usize, size, "file", mt))

    def _gz_header(self):
        fh = self.fh
        fh.seek(0)
        h = fh.read(10)
        if len(h) < 10 or h[:2] != b"\x1f\x8b":
            return None
        flg, mt = h[3], struct.unpack("<I", h[4:8])[0]
        if flg & 4:
            xl = fh.read(2)
            if len(xl) < 2:
                return None
            fh.read(struct.unpack("<H", xl)[0])
        name = None
        if flg & 8:
            buf = b""
            while len(buf) < 512:
                c = fh.read(1)
                if not c or c == b"\0":
                    break
                buf += c
            name = buf.decode("latin-1") if buf else None
        return name, (mt or None)

    def open_entry(self, e):
        if self.comp == "zstd":
            return _ZstdStream(self._zdata, self.size_c, self._zdict)
        self.fh.seek(0)
        return {"gzip": lambda: gzip.GzipFile(fileobj=self.fh, mode="rb"), "bzip2": lambda: bz2.BZ2File(self.fh, "rb"),
                "xz": lambda: lzma.LZMAFile(self.fh, "rb")}[self.comp]()


# --- ISO 9660 / PSP -------------------------------------------------------------------------------

_ISO_LAYOUTS = ((2048, 0), (2352, 16), (2352, 24), (2336, 8))


def _find_iso_layout(img):
    for ss, doff in _ISO_LAYOUTS:
        if img.read_at(16 * ss + doff, 6) == b"\x01CD001":
            return ss, doff
    return None


def _parse_sfo(b: bytes) -> dict:
    if b[:4] != b"\x00PSF" or len(b) < 20:
        return {}
    out: dict = {}
    try:
        _v, kt, dt, n = struct.unpack_from("<4I", b, 4)
        for i in range(min(n, 256)):
            ko, fmt, ln, _mx, do = struct.unpack_from("<HHIII", b, 20 + 16 * i)
            end = b.index(b"\0", kt + ko)
            key = b[kt + ko:end].decode("ascii", "replace")
            raw = b[dt + do:dt + do + ln]
            out[key] = struct.unpack("<I", raw[:4].ljust(4, b"\0"))[0] if fmt == 0x0404 else raw.split(b"\0")[0].decode("utf-8", "replace")
    except (struct.error, ValueError):
        pass
    return out


class _ExtentStream:
    def __init__(self, h, extents):
        self.h, self.ext, self.i, self.off = h, [x for x in extents if x[1] > 0], 0, 0

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = 1 << 30
        out = []
        while n > 0 and self.i < len(self.ext):
            lba, sz = self.ext[self.i]
            rem = sz - self.off
            if rem <= 0:
                self.i += 1
                self.off = 0
                continue
            b = self.h.lread(lba * self.h.lbs + self.off, min(n, rem))
            if not b:
                raise EOFError("citra ISO terpotong di LBA %d" % lba)
            out.append(b)
            n -= len(b)
            self.off += len(b)
        return b"".join(out)

    def close(self):
        pass


class _IsoHandler(_Handler):
    fmt, label = "iso9660", "ISO 9660"

    def __init__(self, img, ss: int, doff: int, wrapper: str = ""):
        super().__init__()
        self.img, self.ss, self.doff, self.lbs = img, ss, doff, 2048
        if wrapper:
            self.info["wrapper"] = wrapper
        self._parse()

    def lread(self, lo: int, n: int) -> bytes:
        if self.ss == 2048 and self.doff == 0:
            return self.img.read_at(lo, n)
        out = []
        while n > 0:
            sec, w = divmod(lo, 2048)
            take = min(n, 2048 - w)
            b = self.img.read_at(sec * self.ss + self.doff + w, take)
            if not b:
                break
            out.append(b)
            lo += len(b)
            n -= len(b)
        return b"".join(out)

    @staticmethod
    def _date7(b: bytes):
        try:
            tz = b[6] - 256 if b[6] > 127 else b[6]
            return datetime(1900 + b[0], b[1], b[2], b[3], b[4], b[5], tzinfo=timezone(timedelta(minutes=15 * tz))).timestamp()
        except (ValueError, OverflowError, IndexError):
            return None

    def _parse(self):
        pvd = joliet = None
        for sec in range(16, 16 + 32):
            d = self.lread(sec * 2048, 2048)
            if len(d) < 2048 or d[1:6] != b"CD001":
                break
            if d[0] == 1 and pvd is None:
                pvd = d
            elif d[0] == 2 and joliet is None and d[88:91] in (b"%/@", b"%/C", b"%/E"):
                joliet = d
            elif d[0] == 255:
                break
        if pvd is None and joliet is None:
            raise ContainerError("corrupt", "descriptor volume ISO 9660 tidak ditemukan")
        vd = joliet or pvd
        use_joliet = joliet is not None
        lbs = struct.unpack_from("<H", vd, 128)[0]
        self.lbs = lbs if lbs in (512, 1024, 2048, 4096) else 2048
        if pvd is not None:
            self.info["volume_id"] = _ex_clean(pvd[40:72].decode("latin-1").strip(), 40)
            self.info["system_id"] = _ex_clean(pvd[8:40].decode("latin-1").strip(), 40)
            vs = struct.unpack_from("<I", pvd, 80)[0]
            self.info["volume_size"] = vs * self.lbs
            cd = pvd[813:827].decode("ascii", "replace")
            if cd.isdigit() and cd != "0" * 14:
                self.info["created"] = "%s-%s-%s %s:%s:%s" % (cd[0:4], cd[4:6], cd[6:8], cd[8:10], cd[10:12], cd[12:14])
        self.info["names"] = "Joliet" if use_joliet else "ISO 9660"
        root = vd[156:190]
        stack = [(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "", 0)]
        seen = set()
        t0 = time.time()
        rr_seen = False
        while stack:
            lba, dsize, prefix, depth = stack.pop()
            if lba in seen or depth > MAX_DEPTH or dsize <= 0 or dsize > MAX_DIR_BYTES:
                continue
            seen.add(lba)
            data = self.lread(lba * self.lbs, dsize)
            pos, pend, pname = 0, None, None
            while pos < len(data):
                l = data[pos]
                if l == 0:
                    pos = (pos // 2048 + 1) * 2048
                    continue
                rec = data[pos:pos + l]
                pos += l
                if l < 34 or len(rec) < l:
                    continue
                nlen = rec[32]
                fi = rec[33:33 + nlen]
                if nlen == 0 or fi in (b"\x00", b"\x01"):
                    continue
                flags = rec[25]
                elba, esz = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
                mt = self._date7(rec[18:25])
                if use_joliet:
                    name = fi.decode("utf-16-be", "replace")
                else:
                    name = fi.decode("latin-1")
                su = rec[33 + nlen + (1 if nlen % 2 == 0 else 0):]
                rr_name, is_link = self._susp(su)
                if rr_name and not use_joliet:
                    name, rr_seen = rr_name, True
                else:
                    name = re.sub(r";\d+$", "", name)
                    if len(name) > 1 and name.endswith("."):
                        name = name[:-1]
                is_dir = bool(flags & 0x02)
                if not is_dir and (flags & 0x80):        # multi-extent: kumpulkan sampai rekaman terakhir
                    pend = (pend or []) + [(elba, esz)]
                    pname = pname or name
                    continue
                if pend is not None:
                    exts, name, pend, pname = pend + [(elba, esz)], pname or name, None, None
                else:
                    exts = [(elba, esz)]
                path = prefix + name
                if is_dir:
                    self.entries.append(Entry(len(self.entries), path, 0, 0, "dir", mt))
                    stack.append((elba, esz, path + "/", depth + 1))
                else:
                    self.entries.append(Entry(len(self.entries), path, sum(x[1] for x in exts), 0, "symlink" if is_link else "file", mt, False, exts))
                if len(self.entries) >= _ex_MAX_ENTRIES or time.time() - t0 > LIST_TIME:
                    self.truncated = True
                    stack.clear()
                    break
        if rr_seen:
            self.info["names"] = "ISO 9660 + Rock Ridge"
        if not self.entries:
            self.notes.append("ISO tanpa entri berkas yang terbaca")
        self._psp()

    @staticmethod
    def _susp(su: bytes):
        """Rock Ridge: NM (nama) dan PX/SL (deteksi tautan simbolik). Mengembalikan (nama | None, tautan?)."""
        name, link, p = b"", False, 0
        while p + 4 <= len(su):
            sig, ln = su[p:p + 2], su[p + 2]
            if ln < 4 or p + ln > len(su):
                break
            body = su[p + 4:p + ln]
            if sig == b"NM" and body:
                name += body[1:]
            elif sig == b"SL":
                link = True
            elif sig == b"PX" and len(body) >= 4 and stat.S_ISLNK(struct.unpack_from("<I", body, 0)[0]):
                link = True
            p += ln
        return (name.decode("utf-8", "replace") if name else None), link

    def _psp(self):
        up = {e.path.upper(): e for e in self.entries}
        if not any(k.startswith("PSP_GAME/") or k == "PSP_GAME" for k in up):
            return
        self.fmt, self.label = "iso-psp", "ISO PSP (UMD)"
        sfo = up.get("PSP_GAME/PARAM.SFO")
        if sfo is not None and sfo.kind == "file" and 0 < sfo.size <= 65536:
            try:
                kv = _parse_sfo(_ExtentStream(self, sfo.ref).read(sfo.size))
                for k in ("TITLE", "DISC_ID", "DISC_VERSION", "APP_VER", "CATEGORY", "PSP_SYSTEM_VER", "PARENTAL_LEVEL", "REGION"):
                    if k in kv:
                        self.info["psp_" + k.lower()] = _ex_clean(kv[k], 100)
            except (EOFError, OSError, ContainerError):
                self.notes.append("PARAM.SFO tidak terbaca")
        eb = up.get("PSP_GAME/SYSDIR/EBOOT.BIN")
        if eb is not None and eb.kind == "file" and eb.size >= 4:
            try:
                magic = _ExtentStream(self, eb.ref).read(4)
                self.info["eboot"] = "terenkripsi (~PSP): tidak bisa dianalisis statis tanpa dekripsi" if magic == b"~PSP" else (
                    "ELF / PRX tidak terenkripsi" if magic == b"\x7fELF" else "PBP" if magic == b"\x00PBP" else "magic %s" % magic.hex())
            except (EOFError, OSError):
                pass

    def open_entry(self, e):
        return _ExtentStream(self, e.ref)


# ---------------------------------------------------------------------------------------------------
# Deteksi format
# ---------------------------------------------------------------------------------------------------

def _ex_open_regular(path):
    """Buka SEKALI, lalu fstat: hanya berkas biasa (tolak FIFO / perangkat / folder) tanpa celah TOCTOU."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(str(Path(str(path)).expanduser()), flags)
    except FileNotFoundError:
        raise ContainerError("not_found", "berkas tidak ditemukan: %s" % _ex_clean(path, 120))
    except IsADirectoryError:
        raise ContainerError("is_directory", "path adalah folder, bukan berkas")
    except PermissionError:
        raise ContainerError("permission", "tidak punya izin membaca: %s" % _ex_clean(path, 120))
    except OSError as e:
        raise ContainerError("io_error", "%s: %s" % (type(e).__name__, e))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ContainerError("not_regular", "bukan berkas biasa (FIFO / perangkat / folder ditolak)")
        return os.fdopen(fd, "rb"), st.st_size
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _zstd_cap(size: int) -> int:
    """Batas keluaran dekompresi Zstd: sama dengan kebijakan rasio container lain (MAX_RATIO, lantai RATIO_FLOOR), maksimum MAX_ENTRY_BYTES."""
    return min(MAX_ENTRY_BYTES, max(RATIO_FLOOR, int(size) * MAX_RATIO))


class _ZstdStream:
    """Aliran baca Zstd (v99.34): dekompres penuh di memori saat read() pertama, dibatasi _zstd_cap. Melebihi batas -> _Limit (dilewati, bukan galat)."""

    def __init__(self, data: bytes, size: int, zdict=None):
        self.data, self.cap, self.buf, self.zdict = data, _zstd_cap(size), None, zdict

    def read(self, n: int = -1) -> bytes:
        if self.buf is None:
            try:
                self.buf = io.BytesIO(_zstd_decompress(self.data, max_out=self.cap, dictionary=self.zdict))
            except ValueError as x:
                if "melebihi" in str(x):
                    raise _Limit("rasio kompresi mencurigakan atau melebihi batas ukuran (zip bomb?)") from None
                raise
            self.data = None
        return self.buf.read(-1 if n is None else n)

    def close(self):
        self.buf = self.data = None


def _zstd_handler(fh, size: int, name: str, zdict=None) -> _Handler:
    """.zst tunggal atau .tar.zst (v99.34), dekoder murni Python. zdict (v99.52): dictionary Zstd (bytes / daftar / {id: bytes})."""
    if size > MAX_ENTRY_BYTES:
        raise ContainerError("too_large", "berkas Zstd terlalu besar (%s)" % _ex_human(size))
    fh.seek(0)
    data = fh.read(MAX_ENTRY_BYTES + 1)
    try:
        peek = _zstd_decompress(data, head=1024, verify=False, dictionary=zdict)
    except ValueError as e:
        raise ContainerError("corrupt", "aliran ZSTD rusak atau tidak didukung: %s" % _ex_clean(e, 120))
    if _is_tar_raw(peek):
        try:
            raw = _zstd_decompress(data, max_out=_zstd_cap(size), dictionary=zdict)
        except ValueError as e:
            raise ContainerError("corrupt", "TAR.ZST rusak atau melebihi batas: %s" % _ex_clean(e, 120))
        return _TarHandler(io.BytesIO(raw), size, name, "r:", "zstd")
    return _SingleHandler(fh, size, name, "zstd", data=data, zdict=zdict)


def _make_handler(fh, size: int, name: str, zdict=None) -> _Handler:
    if size == 0:
        raise ContainerError("empty", "berkas kosong (0 byte)")
    base = _FileImg(fh, size)
    head = base.read_at(0, 8)
    if head[:4] == b"CISO":
        cso = _CsoImg(base)
        lay = _find_iso_layout(cso)
        if lay is None:
            raise ContainerError("unsupported_format", "CSO tidak berisi ISO 9660 yang valid")
        h = _IsoHandler(cso, lay[0], lay[1], wrapper="CSO (zlib per blok, blok %d byte, ukuran asli %s)" % (cso.bsz, _ex_human(cso.size)))
        return h
    if head[:4] == b"ZISO":
        raise ContainerError("unsupported_format", "ZSO (LZ4 PSP) belum didukung; ubah ke ISO / CSO dengan ciso / maxcso")
    lay = _find_iso_layout(base)
    if lay:
        return _IsoHandler(base, lay[0], lay[1])
    if head[:4] == b"\x28\xb5\x2f\xfd":
        return _zstd_handler(fh, size, name, zdict)
    for magic, comp, mode in ((b"\x1f\x8b", "gzip", "r:gz"), (b"BZh", "bzip2", "r:bz2"), (b"\xfd7zXZ\x00", "xz", "r:xz")):
        if head.startswith(magic):
            try:
                return _TarHandler(fh, size, name, mode, comp)
            except ContainerError as e:
                if e.code != "not_tar":
                    raise
            return _SingleHandler(fh, size, name, comp)
    if head[:2] == b"PK" or zipfile.is_zipfile(fh):
        return _ZipHandler(fh, size, name)
    try:
        return _TarHandler(fh, size, name, "r:", "")
    except ContainerError:
        pass
    if head[:6] == b"7z\xbc\xaf\x27\x1c" or head[:4] == b"Rar!":
        raise ContainerError("unsupported_format", "7z / RAR belum didukung di rea_extract (pakai `unpack7z` di rea_triage bila 7-Zip terpasang)")
    raise ContainerError("unsupported_format", "format container tidak dikenal (didukung: ZIP, TAR, GZIP, BZIP2, XZ, ZSTD, ISO 9660, ISO PSP, CSO)")


def _ex_formats() -> list:
    return [{"name": "zip", "about": "ZIP / APK / JAR / SFX, tanpa kata sandi"},
            {"name": "tar", "about": "TAR, TAR.GZ / .BZ2 / .XZ / .ZST (sekuensial)"},
            {"name": "gzip / bzip2 / xz / zstd", "about": "aliran terkompresi tunggal (Zstd: dekoder murni Python)"},
            {"name": "iso9660", "about": "ISO 9660 (Joliet, Rock Ridge, sektor 2048 / raw 2352 / 2336, multi-extent)"},
            {"name": "iso-psp", "about": "ISO UMD PSP: info PARAM.SFO / EBOOT"},
            {"name": "cso", "about": "CSO PSP (zlib per blok) berisi ISO"}]


# ---------------------------------------------------------------------------------------------------
# Registri container terbuka
# ---------------------------------------------------------------------------------------------------

class _Container:
    def __init__(self, cid, path, fh, size, handler):
        self.id, self.path, self.fh, self.size, self.h = cid, path, fh, size, handler
        self.lock = threading.RLock()
        self.t = time.time()

    def close(self):
        with self.lock:
            try:
                self.h.close()
            finally:
                try:
                    self.fh.close()
                except OSError:
                    pass


_OPEN: dict = {}
_OPEN_LOCK = threading.Lock()


def open_container(path, zstd_dict=None) -> dict:
    """Buka container (hanya-baca) dan daftar isinya. Tutup dengan close_container(). zstd_dict (v99.52): dictionary untuk .zst / .tar.zst."""
    fh = None
    try:
        fh, size = _ex_open_regular(path)
        name = Path(str(path)).name
        h = _make_handler(fh, size, name, zstd_dict)
        cid = "c" + secrets.token_hex(6)
        c = _Container(cid, Path(str(path)).expanduser(), fh, size, h)
        with _OPEN_LOCK:
            while len(_OPEN) >= MAX_OPEN:                      # buang yang tertua supaya tidak bocor
                old = min(_OPEN.values(), key=lambda x: x.t)
                _OPEN.pop(old.id, None)
                old.close()
            _OPEN[cid] = c
        files = sum(1 for e in h.entries if e.kind == "file")
        return {"status": "success", "container_id": cid, "format": h.fmt, "label": h.label, "path": str(c.path), "size": size,
                "entries": len(h.entries), "files": files, "truncated": h.truncated, "info": dict(h.info), "notes": list(h.notes)}
    except ContainerError as e:
        if fh:
            fh.close()
        return _ex_err(e.code, e)
    except Exception as e:
        if fh:
            try:
                fh.close()
            except OSError:
                pass
        return _ex_err("open_failed", "%s: %s" % (type(e).__name__, e))


def close_container(container_id) -> dict:
    with _OPEN_LOCK:
        c = _OPEN.pop(str(container_id), None)
    if c is None:
        return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
    c.close()
    return {"status": "success"}


def _get(cid):
    with _OPEN_LOCK:
        c = _OPEN.get(str(cid))
    if c:
        c.t = time.time()
    return c


def list_entries(container_id, limit: int = 0) -> dict:
    c = _get(container_id)
    if c is None:
        return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
    es = c.h.entries if limit <= 0 else c.h.entries[:limit]
    return {"status": "success", "format": c.h.fmt, "total": len(c.h.entries), "truncated": c.h.truncated, "entries": [e.as_dict() for e in es]}


# ---------------------------------------------------------------------------------------------------
# Pemilih entri
# ---------------------------------------------------------------------------------------------------

def _compile_selector(sel):
    """-> (predikat(Entry) -> bool, max_entries | None). selector: None | str (pola) | dict."""
    if sel in (None, "", {}):
        return (lambda e: True), None
    if isinstance(sel, str):
        sel = {"pattern": sel}
    if not isinstance(sel, dict):
        raise ValueError("selector harus dict / string / None")
    pats = []

    def add(spec, bucket):
        for s in re.split(r"[;,\n]", str(spec)) if not str(spec).startswith("re:") else [str(spec)]:
            s = s.strip()
            if not s:
                continue
            if s.startswith("re:"):
                if len(s) > 400:
                    raise ValueError("regex terlalu panjang")
                bucket.append(("re", re.compile(s[3:], re.I)))
            elif any(ch in s for ch in "*?["):
                bucket.append(("glob", s.lower()))
            else:
                bucket.append(("sub", s.lower()))

    inc, exc = [], []
    if sel.get("pattern"):
        add(sel["pattern"], inc)
    if sel.get("exclude"):
        add(sel["exclude"], exc)
    paths = {str(p).replace("\\", "/").strip("/").lower() for p in (sel.get("paths") or [])}
    max_size = sel.get("max_size")
    max_size = int(max_size) if max_size not in (None, "") else None
    max_entries = sel.get("max_entries")
    max_entries = int(max_entries) if max_entries not in (None, "") else None

    def hit(e, bucket):
        full = e.path.replace("\\", "/").lower()
        base = full.rsplit("/", 1)[-1]
        for kind, p in bucket:
            if kind == "re" and p.search(e.path):
                return True
            if kind == "glob" and (fnmatch.fnmatchcase(full, p) or fnmatch.fnmatchcase(base, p)):
                return True
            if kind == "sub" and p in full:
                return True
        return False

    def pred(e):
        full = e.path.replace("\\", "/").strip("/").lower()
        if paths and full not in paths:
            return False
        if inc and not hit(e, inc):
            return False
        if exc and hit(e, exc):
            return False
        if max_size is not None and e.size is not None and e.size > max_size:
            return False
        return True

    return pred, max_entries


# ---------------------------------------------------------------------------------------------------
# Ekstraksi
# ---------------------------------------------------------------------------------------------------

def _unique_path(root: Path, rel: str):
    target = (root / rel).resolve()
    if root != target and root not in target.parents:
        return None
    return target


def _sha256_stream(fh, size) -> str | None:
    if size > SOURCE_HASH_LIMIT:
        return None
    h = hashlib.sha256()
    fh.seek(0)
    while True:
        b = fh.read(COPY_CHUNK)
        if not b:
            break
        h.update(b)
    return h.hexdigest()


def _scan_flags(rel: str, typ: str, entropy: float, size: int) -> list:
    flags = []
    name = rel.rsplit("/", 1)[-1].lower()
    ext = os.path.splitext(name)[1]
    exe_type = typ in ("PE", "DOS MZ", "ELF", "Mach-O / class", "LNK", "skrip (shebang)", "PSP PRX terenkripsi")
    if exe_type:
        flags.append("berisi kode yang bisa dieksekusi (%s)" % typ)
    if exe_type and ext and ext not in _EXEC_EXT:
        flags.append("jenis %s menyamar dengan ekstensi %s" % (typ, ext))
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|gif|txt|mp3|mp4|zip|rar)\.(exe|scr|com|bat|cmd|js|vbs|lnk|pif|hta)$", name):
        flags.append("ekstensi ganda menyesatkan")
    if typ in _ARCHIVE_TYPES and typ != "TAR":
        flags.append("container bersarang (%s): belum diekstrak otomatis" % typ)
    if entropy >= 7.5 and size >= 4096 and typ not in _ARCHIVE_TYPES and typ not in ("PNG", "JPEG", "GIF", "OGG", "RIFF", "PDF"):
        flags.append("entropi tinggi %.2f (terkompresi / terenkripsi / packed?)" % entropy)
    return flags


def extract_selected(container_id, selector=None, outdir=None, scan: bool = False) -> dict:
    """Ekstraksi selektif ke workspace `outdir`. Mengembalikan manifest (dict). Tidak pernah melempar."""
    try:
        c = _get(container_id)
        if c is None:
            return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
        if not outdir:
            return _ex_err("no_outdir", "outdir wajib diisi")
        with c.lock:
            return _do_extract(c, selector, Path(str(outdir)).expanduser(), bool(scan))
    except ValueError as e:
        return _ex_err("bad_selector", e)
    except re.error as e:
        return _ex_err("bad_selector", "regex tidak valid: %s" % e)
    except Exception as e:
        return _ex_err("extract_failed", "%s: %s" % (type(e).__name__, e))


def _do_extract(c: _Container, selector, outdir: Path, scan: bool) -> dict:
    h = c.h
    pred, max_entries = _compile_selector(selector)
    outdir.mkdir(parents=True, exist_ok=True)
    root = outdir.resolve()
    ext_root, man_root, log_root = root / "extracted", root / "manifests", root / "logs"
    for d in (ext_root, man_root, log_root):
        d.mkdir(parents=True, exist_ok=True)
    ext_root = ext_root.resolve()
    log: list = []

    def L(msg):
        log.append("%s %s" % (datetime.now(timezone.utc).strftime("%H:%M:%S"), _ex_clean(msg, 300)))

    L("buka %s (%s, %d entri)" % (_ex_clean(c.path.name, 80), h.label, len(h.entries)))
    matched = [e for e in h.entries if e.kind != "dir" and pred(e)]
    notes: list = []
    if max_entries is not None and len(matched) > max_entries:
        notes.append("dibatasi max_entries=%d dari %d entri yang cocok" % (max_entries, len(matched)))
        matched = matched[:max_entries]
    files: list = []
    skipped: list = []
    errors: list = []
    warnings: list = []
    state = {"total": 0}
    todo: list = []
    for e in matched:
        if e.kind != "file":
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "%s tidak diekstrak (kebijakan keamanan)%s" % ("tautan simbolik" if e.kind == "symlink" else "berkas khusus", " " + e.note if e.note else ""), "benign": True})
        elif e.encrypted:
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "terenkripsi (kata sandi tidak didukung)", "benign": False})
        elif e.size is not None and e.size > MAX_ENTRY_BYTES:
            skipped.append({"path": _ex_clean(e.path, 200), "size": e.size, "reason": "melebihi batas ukuran per berkas (%s)" % _ex_human(MAX_ENTRY_BYTES), "benign": False})
        else:
            todo.append(e)

    used: set = set()

    def new_target(rel: str):
        t = _unique_path(ext_root, rel)
        if t is None:
            return None
        stem, suf, k = t.stem, t.suffix, 1
        while str(t).lower() in used or t.exists():
            k += 1
            t = t.with_name("%s_%d%s" % (stem, k, suf))
        used.add(str(t).lower())
        return t

    def write_one(e: Entry, stream):
        rel, unsafe = _ex_safe_rel(e.path)
        if unsafe:
            warnings.append("path berbahaya dinetralkan: %s -> %s" % (_ex_clean(e.path, 120), rel))
            L("netralkan path berbahaya: %s" % _ex_clean(e.path, 120))
        tgt = new_target(rel)
        if tgt is None:
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "path di luar workspace", "benign": False})
            return
        try:
            tgt.parent.mkdir(parents=True, exist_ok=True)
        except (FileExistsError, NotADirectoryError):
            errors.append("%s: konflik nama (induk adalah berkas)" % _ex_clean(e.path, 120))
            return
        sha, written, head = hashlib.sha256(), 0, b""
        ratio_cap = max(RATIO_FLOOR, e.packed * MAX_RATIO) if e.packed and e.packed > 0 else None
        try:
            with open(tgt, "xb") as out:
                while True:
                    b = stream.read(COPY_CHUNK)
                    if not b:
                        break
                    written += len(b)
                    if written > MAX_ENTRY_BYTES:
                        raise _Limit("melebihi batas ukuran per berkas (%s)" % _ex_human(MAX_ENTRY_BYTES))
                    if state["total"] + written > MAX_TOTAL_BYTES:
                        raise _Limit("melebihi batas total ekstraksi (%s)" % _ex_human(MAX_TOTAL_BYTES))
                    if ratio_cap and written > ratio_cap:
                        raise _Limit("rasio kompresi mencurigakan (zip bomb?)")
                    if len(head) < 1 << 20:
                        head += b[:(1 << 20) - len(head)]
                    sha.update(b)
                    out.write(b)
        except _Limit as x:
            _rm(tgt)
            skipped.append({"path": _ex_clean(e.path, 200), "reason": str(x), "benign": False})
            L("lewati %s: %s" % (_ex_clean(e.path, 100), x))
            return
        except Exception as x:
            _rm(tgt)
            errors.append("%s: %s: %s" % (_ex_clean(e.path, 120), type(x).__name__, _ex_clean(x, 120)))
            L("gagal %s: %s" % (_ex_clean(e.path, 100), type(x).__name__))
            return
        state["total"] += written
        if e.mtime:
            try:
                os.utime(tgt, (e.mtime, e.mtime))
            except (OSError, OverflowError, ValueError):
                pass
        typ = _sniff(head[:2048] if written < 32774 else head[:32800])
        rec = {"path": tgt.relative_to(root).as_posix(), "source": _ex_clean(e.path, 300), "size": written, "sha256": sha.hexdigest(), "type": typ,
               "mtime": _ts(e.mtime), "note": "path dinetralkan" if (unsafe or rel != e.path.replace("\\", "/")) else ""}
        if scan:
            rec["entropy"] = round(_ex_entropy(head[:1 << 20]), 3)
            fl = _scan_flags(rel, typ, rec["entropy"], written)
            if unsafe:
                fl.insert(0, "path traversal / absolut di dalam arsip")
            if fl:
                rec["flags"] = fl
        files.append(rec)

    if todo:
        wanted = {e.index for e in todo}
        by_index = {e.index: e for e in todo}
        if h.sequential:
            try:
                for e, stream in h.iter_data(wanted):
                    if stream is None:
                        errors.append("%s: tidak bisa dibuka" % _ex_clean(e.path, 120))
                        continue
                    try:
                        write_one(e, stream)
                    finally:
                        _close(stream)
            except Exception as x:
                errors.append("arsip berhenti di tengah jalan: %s: %s" % (type(x).__name__, _ex_clean(x, 120)))
                L("arsip berhenti: %s" % type(x).__name__)
        else:
            for e in todo:
                try:
                    stream = h.open_entry(e)
                except Exception as x:
                    errors.append("%s: %s: %s" % (_ex_clean(e.path, 120), type(x).__name__, _ex_clean(x, 120)))
                    continue
                try:
                    write_one(by_index[e.index], stream)
                finally:
                    _close(stream)

    # ---- manifest
    benign_only = all(s.get("benign") for s in skipped)
    if not matched:
        status, code, msg = "error", "no_match", "tidak ada entri berkas yang cocok dengan selector (total %d entri)" % len(h.entries)
    elif not files:
        status, code, msg = "error", "nothing_extracted", "tidak ada yang berhasil diekstrak" + (": " + errors[0] if errors else (": " + skipped[0]["reason"] if skipped else ""))
    elif errors or not benign_only:
        status, code, msg = "partial", None, None
    else:
        status, code, msg = "success", None, None
    scan_info = None
    if scan:
        by_type = Counter(f["type"] for f in files)
        scan_info = {"files_scanned": len(files), "by_type": dict(by_type.most_common()),
                     "flagged": [{"path": f["path"], "reasons": f["flags"]} for f in files if f.get("flags")]}
    man = {"status": status, "version": _ex_VERSION, "format": h.fmt, "format_label": h.label, "source": str(c.path), "source_size": c.size,
           "source_sha256": _sha256_stream(c.fh, c.size), "outdir": str(root),
           "workspace": {"extracted": str(ext_root), "manifests": str(man_root), "logs": str(log_root)},
           "time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "selector": selector if isinstance(selector, (dict, str)) else None,
           "entries_total": len(h.entries), "entries_matched": len(matched), "entries_extracted": len(files), "entries_skipped": len(skipped),
           "entries_failed": len(errors), "bytes_extracted": state["total"], "container_truncated": h.truncated,
           "container_info": dict(h.info), "files": files, "skipped": skipped, "errors": errors, "warnings": warnings + notes + list(h.notes), "scan": scan_info}
    if code:
        man["code"], man["message"] = code, msg
    L("selesai: status=%s diekstrak=%d dilewati=%d gagal=%d" % (status, len(files), len(skipped), len(errors)))
    try:
        lp = _free_name(log_root, "extract", ".log")
        lp.write_text("\n".join(log) + "\n", encoding="utf-8")
        man["log_path"] = str(lp)
        mp = _free_name(man_root, "manifest", ".json")
        man["manifest_path"] = str(mp)
        mp.write_text(json.dumps(man, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except OSError as x:
        man["warnings"].append("manifest / log tidak bisa ditulis: %s" % _ex_clean(x, 100))
        man.pop("manifest_path", None)
    return man


def _free_name(folder: Path, stem: str, suffix: str) -> Path:
    p, k = folder / (stem + suffix), 1
    while p.exists():
        k += 1
        p = folder / ("%s_%d%s" % (stem, k, suffix))
    return p


def _rm(p: Path):
    try:
        p.unlink()
    except OSError:
        pass


def _close(s):
    try:
        s.close()
    except Exception:
        pass


def _ex_extract(path, outdir, pattern=None, scan: bool = False, zstd_dict=None) -> dict:
    """Pembungkus: buka -> ekstrak -> tutup."""
    r = open_container(path, zstd_dict)
    if r.get("status") != "success":
        return r
    try:
        return extract_selected(r["container_id"], {"pattern": pattern} if pattern else None, outdir, scan=scan)
    finally:
        close_container(r["container_id"])


# ---------------------------------------------------------------------------------------------------
# Deskripsi
# ---------------------------------------------------------------------------------------------------

def _entry_flags(e: Entry) -> list:
    f = []
    rel, unsafe = _ex_safe_rel(e.path)
    if unsafe:
        f.append("PATH-BERBAHAYA")
    if e.encrypted:
        f.append("ENKRIPSI")
    if e.kind == "symlink":
        f.append("TAUTAN")
    elif e.kind == "other":
        f.append("KHUSUS")
    if e.kind == "file":
        ext = os.path.splitext(e.path.lower())[1]
        if ext in _EXEC_EXT:
            f.append("EKSEKUSI")
        if re.search(r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|gif|txt|mp3|mp4|zip|rar)\.(exe|scr|com|bat|cmd|js|vbs|lnk|pif|hta)$", e.path.lower()):
            f.append("EKSTENSI-GANDA")
        if e.packed and e.size and e.packed > 0 and e.size > 10 * 1024 * 1024 and e.size / e.packed > 1000:
            f.append("RASIO-TINGGI")
    return f


def describe_container(path, zstd_dict=None) -> dict:
    r = open_container(path, zstd_dict)
    if r.get("status") != "success":
        return r
    try:
        c = _get(r["container_id"])
        h = c.h
        files = [e for e in h.entries if e.kind == "file"]
        total = sum(e.size for e in files if e.size and e.size > 0)
        packed = sum(e.packed for e in files if e.packed)
        exts = Counter(os.path.splitext(e.path.lower())[1] or "(tanpa ekstensi)" for e in files)
        flagged = [(e, _entry_flags(e)) for e in h.entries]
        flagged = [(e, f) for e, f in flagged if f]
        return {"status": "success", "format": h.fmt, "label": h.label, "path": str(c.path), "size": c.size, "entries_total": len(h.entries),
                "files": len(files), "dirs": sum(1 for e in h.entries if e.kind == "dir"), "total_size": total, "packed_total": packed,
                "info": dict(h.info), "notes": list(h.notes), "truncated": h.truncated, "top_extensions": dict(exts.most_common(8)),
                "flagged": [{"path": _ex_clean(e.path, 200), "flags": f} for e, f in flagged[:100]],
                "entries": [e.as_dict() for e in h.entries[:MAX_LIST_ROWS]]}
    finally:
        close_container(r["container_id"])


def describe_container_text(path, max_chars: int = 0, zstd_dict=None) -> str:
    """Daftar isi ringkas untuk laporan / Hermes. Tidak melempar."""
    try:
        d = describe_container(path, zstd_dict)
        if d.get("status") != "success":
            return "CONTAINER gagal dibuka: %s" % d.get("message", d.get("code"))
        head = "CONTAINER: %s | %d entri (%d berkas, %d folder) | isi %s%s" % (
            d["label"], d["entries_total"], d["files"], d["dirs"], _ex_human(d["total_size"]),
            " (terkompresi %s, rasio %.1fx)" % (_ex_human(d["packed_total"]), d["total_size"] / d["packed_total"]) if d["packed_total"] else "")
        L = [head, "  Berkas: %s (%s)%s" % (_ex_clean(Path(str(path)).name, 100), _ex_human(d["size"]), " | DAFTAR DIPOTONG (batas entri / waktu)" if d["truncated"] else "")]
        info = d["info"]
        if info.get("wrapper"):
            L.append("  Pembungkus: %s" % info["wrapper"])
        if info.get("volume_id") or info.get("names"):
            L.append("  Volume: %s | sistem: %s | nama: %s%s" % (info.get("volume_id", "?") or "-", info.get("system_id", "?") or "-", info.get("names", "?"),
                                                                 " | dibuat %s" % info["created"] if info.get("created") else ""))
        if info.get("psp_title") or info.get("psp_disc_id"):
            L.append("  PSP: judul %s | ID %s | versi disc %s | app %s | kategori %s | firmware %s" % (
                info.get("psp_title", "?"), info.get("psp_disc_id", "?"), info.get("psp_disc_version", "?"), info.get("psp_app_ver", "?"),
                info.get("psp_category", "?"), info.get("psp_psp_system_ver", "?")))
        if info.get("eboot"):
            L.append("  EBOOT.BIN: %s" % info["eboot"])
        for k in ("hint", "comment"):
            if info.get(k):
                L.append("  %s: %s" % ("Petunjuk" if k == "hint" else "Komentar", info[k]))
        L += ["  Catatan: %s" % n for n in d["notes"]]
        if d["top_extensions"]:
            L.append("  Ekstensi: " + ", ".join("%s x%d" % (k, v) for k, v in d["top_extensions"].items()))
        if d["flagged"]:
            L.append("  PERHATIAN: %d entri mencurigakan" % len(d["flagged"]))
            L += ["    %s  [%s]" % (x["path"], ", ".join(x["flags"])) for x in d["flagged"][:12]]
            if len(d["flagged"]) > 12:
                L.append("    ... +%d lagi" % (len(d["flagged"]) - 12))
        L.append("  Isi:")
        for e in d["entries"][:80]:
            fl = _entry_flags_from_dict(e)
            L.append("   %s %10s  %s%s" % ("d" if e["kind"] == "dir" else "l" if e["kind"] == "symlink" else "-", "" if e["kind"] == "dir" else _ex_human(e["size"]),
                                          e["path"] + ("/" if e["kind"] == "dir" else ""), "  [%s]" % ", ".join(fl) if fl else ""))
        if d["entries_total"] > 80:
            L.append("   ... +%d entri lagi (gunakan extract / list_entries untuk daftar penuh)" % (d["entries_total"] - 80))
        text = "\n".join(L)
        if max_chars and len(text) > max_chars:
            text = text[:max_chars - 30] + "\n[...dipangkas supaya muat...]"
        return text
    except Exception as e:
        return "CONTAINER gagal dibaca (%s: %s)." % (type(e).__name__, _ex_clean(e, 120))


def _entry_flags_from_dict(e: dict) -> list:
    return _entry_flags(Entry(0, e["path"], e["size"], e["packed"], e["kind"], None, e["encrypted"]))


# ---------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------

def _ex_main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_EX_DOC.split("CLI:")[1].strip())
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "formats":
        for f in _ex_formats():
            print("%-18s %s" % (f["name"], f["about"]))
        return 0
    if cmd == "list" and rest:
        print(describe_container_text(rest[0]))
        return 0
    if cmd == "extract" and len(rest) >= 2:
        scan = "--scan" in rest
        pos = [x for x in rest if not x.startswith("--")]
        m = _ex_extract(pos[0], pos[1], pattern=pos[2] if len(pos) > 2 else None, scan=scan)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s | manifest: %s%s" % (m.get("status"), m.get("entries_extracted"), m.get("entries_skipped"),
                                                                            m.get("entries_failed"), m.get("manifest_path"), (" | " + m["message"]) if m.get("message") else ""))
        for f in (m.get("scan") or {}).get("flagged", [])[:20]:
            print("  PERHATIAN %s: %s" % (f["path"], "; ".join(f["reasons"])))
        return 0 if m.get("status") == "success" else 1
    print("pemakaian: python rea_extract.py list FILE | extract FILE OUTDIR [pola] [--scan] | formats")
    return 1

_BN_PUBLIC = frozenset(['COMPARE_CHUNK', 'HASH_LIMIT', 'MAX_BACKUP', 'MAX_DIR_FILES', 'MAX_HEX', 'MAX_HITS', 'MAX_JOURNAL', 'MAX_PATCH', 'MAX_RANGES', 'SEARCH_CHUNK', 'SEARCH_OVERLAP', 'SEARCH_TIME', 'VERSION', '_ASCII', '_EBCDIC', '_ENC_ALIASES', '_LATIN1', '_NotRegular', '_Src', '_as_bytes', '_clean', '_compile_pattern', '_ebcdic_table', '_err', '_fail', '_fmt_time', '_fsync_write', '_journal_path', '_load_journal', '_norm_offset', '_opt', '_orig_path', '_parse_hex', '_plausible', '_same_content', '_save_journal', '_sha256_file', '_text_column', '_to_int', '_walk_files', 'compare_dirs', 'compare_files', 'hex_view', 'history', 'inspect_at', 'inspect_text', 'main', 'patch', 'patch_text', 'restore_original', 'search', 'search_text', 'undo'])
_BN_RENAMED = {'_ASCII': '_bn_ASCII', 'VERSION': '_bn_VERSION', 'main': '_bn_main', '_err': '_bn_err', '_clean': '_bn_clean'}
_EX_PUBLIC = frozenset(['COPY_CHUNK', 'ContainerError', 'Entry', 'LIST_TIME', 'MAX_DEPTH', 'MAX_DIR_BYTES', 'MAX_ENTRIES', 'MAX_ENTRY_BYTES', 'MAX_LIST_ROWS', 'MAX_OPEN', 'MAX_RATIO', 'MAX_TOTAL_BYTES', 'RATIO_FLOOR', 'SOURCE_HASH_LIMIT', 'VERSION', '_ARCHIVE_TYPES', '_Container', '_CsoImg', '_EXEC_EXT', '_ExtentStream', '_FileImg', '_Handler', '_ISO_LAYOUTS', '_IsoHandler', '_Limit', '_OPEN', '_OPEN_LOCK', '_RESERVED', '_SingleHandler', '_TarHandler', '_ZipHandler', '_clean', '_close', '_compile_selector', '_do_extract', '_entropy', '_entry_flags', '_entry_flags_from_dict', '_err', '_find_iso_layout', '_free_name', '_get', '_human', '_make_handler', '_open_regular', '_parse_sfo', '_rm', '_safe_rel', '_scan_flags', '_sha256_stream', '_sniff', '_ts', '_unique_path', 'close_container', 'describe_container', 'describe_container_text', 'extract', 'extract_selected', 'formats', 'list_entries', 'main', 'open_container'])
_EX_RENAMED = {'extract': '_ex_extract', 'formats': '_ex_formats', '_human': '_ex_human', '_RESERVED': '_ex_RESERVED', 'main': '_ex_main', '_entropy': '_ex_entropy', '_err': '_ex_err', '_clean': '_ex_clean', 'VERSION': '_ex_VERSION', '_open_regular': '_ex_open_regular', 'MAX_ENTRIES': '_ex_MAX_ENTRIES', '_safe_rel': '_ex_safe_rel'}


class _ModAPI:
    """Fasad pengganti `import rea_binary` / `import rea_extract`: hanya nama publik modul asal yang bisa diakses (nama bentrok dipetakan ke _bn_* / _ex_*)."""
    __slots__ = ("_pub", "_ren")

    def __init__(self, pub, ren):
        object.__setattr__(self, "_pub", pub)
        object.__setattr__(self, "_ren", ren)

    def __getattr__(self, name):
        if name not in self._pub:
            raise AttributeError(name)
        return globals()[self._ren.get(name, name)]


_BN_API = _ModAPI(_BN_PUBLIC, _BN_RENAMED)
_EX_API = _ModAPI(_EX_PUBLIC, _EX_RENAMED)


def _binary_mod():
    """Binary Workbench (dulu rea_binary.py)."""
    return _BN_API



