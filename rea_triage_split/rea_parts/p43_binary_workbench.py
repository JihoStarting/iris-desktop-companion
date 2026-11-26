# rea_triage bagian 43/47: binary_workbench (baris asli 20991-21817). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ======================================================================================================
# rea_binary.py (Binary Workbench v96) dan rea_extract.py (mesin ekstraksi container v95) DIGABUNG ke berkas ini pada 23 Nov 2026
# (tanpa ubah perilaku, VERSION tetap), sama seperti rea_assets.py. Nama yang bentrok diberi awalan _bn_ (rea_binary) atau _ex_ (rea_extract):
# VERSION, _clean, _err, main, dan (khusus rea_extract) MAX_ENTRIES, _RESERVED, _entropy, _human, _open_regular, _safe_rel, extract, formats.
# Akses dari bagian lain lewat _binary_mod() / _extract_mod() (fasad: nama aslinya tetap bisa dipakai, mis. mod.hex_view, mod.open_container).
# CLI asli tersedia lewat:  python rea_triage.py --bin <hex|inspect|search|compare|patch|undo|history|restore> ...
#                           python rea_triage.py --ex  <list|extract|formats> ...
# ======================================================================================================

# ---------------------------------------------------------------------------------------------------
# Binary Workbench (dulu rea_binary.py)
# ---------------------------------------------------------------------------------------------------
_BN_DOC = """rea_binary.py - Binary Workbench untuk REA (v96; jembatan tipis ada di rea_triage.py: hex_text, compare_text).

Hanya pustaka standar. TIDAK menjalankan apa pun dari berkas. Semua fungsi tidak melempar: galat dikembalikan sebagai
    {"status": "error", "code": "...", "message": "..."}
dan keberhasilan sebagai {"status": "success", ...}.

Kontrak yang dipakai rea_triage.py (jangan diubah tanpa mengubah pemanggilnya):
    hex_view(path, offset=0, length=256, encoding="ascii") -> {"status", "text", ...}
    compare_files(a, b) -> {"status", "a", "b", "size_a", "size_b", "size_delta", "identical", "sha256_a", "sha256_b",
                            "differing_bytes", "changed_ranges": [{"offset", "length"}], "truncated", "first_diff",
                            "extra_bytes": {"length", "in"} | None}
    compare_dirs(a, b)  -> {"status", "added", "removed", "changed", "unchanged_count", ...}

Tambahan (aditif):
    inspect_at(path, offset)  / inspect_text(...)   inspektor data: int / float / waktu / GUID / IPv4 di satu offset
    search(path, pattern, mode="auto", ...) / search_text(...)   cari hex (dengan ??), teks, UTF-16, regex
    patch(path, offset, data, expect=None, dry_run=False)        timpa byte di tempat (panjang tetap) + jurnal undo
    undo(path, id=None, force=False) / history(path) / restore_original(path)

Patch: HANYA menimpa (tidak menambah / menghapus byte). Sebelum patch pertama, salinan asli disimpan di `<berkas>.rea_orig`
(kecuali backup=False atau berkas > 1 GiB) dan tiap patch dicatat di `<berkas>.rea_undo.json`.

CLI:  python rea_binary.py hex FILE [OFFSET [LEN]] | inspect FILE OFFSET | search FILE PATTERN [--mode hex|text|utf16|regex] [-i]
      | compare A B | patch FILE OFFSET HEX [--expect HEX] [--dry-run] | undo FILE [ID] | history FILE | restore FILE
"""


import hashlib
import json
import math
import os
import re
import shutil
import stat
import struct
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_bn_VERSION = "96.0"

MAX_HEX = 1 << 20              # byte maksimum per tampilan hex
MAX_RANGES = 200               # rentang perbedaan yang dicatat saat compare
MAX_HITS = 500                 # hasil pencarian maksimum
SEARCH_CHUNK = 4 * 1024 * 1024
SEARCH_OVERLAP = 4096          # panjang kecocokan maksimum yang dijamin tidak terpotong antar-potongan
SEARCH_TIME = 30.0             # detik
COMPARE_CHUNK = 1024 * 1024
MAX_DIR_FILES = 100_000
MAX_PATCH = 1024 * 1024
MAX_BACKUP = 1024 ** 3
MAX_JOURNAL = 2000
HASH_LIMIT = 64 * 1024 * 1024  # hash seluruh berkas setelah patch hanya bila <= ini


# ---------------------------------------------------------------------------------------------------
# Dasar
# ---------------------------------------------------------------------------------------------------

def _bn_err(code: str, message, **kw) -> dict:
    d = {"status": "error", "code": code, "message": _bn_clean(message, 300)}
    d.update(kw)
    return d


def _bn_clean(s, n: int = 200) -> str:
    """Buang karakter kontrol / pemisah baris (anti injeksi ke laporan)."""
    return "".join(c if c.isprintable() else "?" for c in str(s))[:n]


class _NotRegular(OSError):
    pass


def _fail(e: BaseException) -> dict:
    if isinstance(e, FileNotFoundError):
        return _bn_err("not_found", "berkas tidak ditemukan: %s" % _bn_clean(getattr(e, "filename", "") or "", 120))
    if isinstance(e, IsADirectoryError):
        return _bn_err("is_directory", "path adalah folder, bukan berkas")
    if isinstance(e, PermissionError):
        return _bn_err("permission", "tidak punya izin: %s" % _bn_clean(getattr(e, "filename", "") or "", 120))
    if isinstance(e, _NotRegular):
        return _bn_err("not_regular", str(e))
    if isinstance(e, OSError):
        return _bn_err("io_error", "%s: %s" % (type(e).__name__, e))
    return _bn_err("failed", "%s: %s" % (type(e).__name__, e))


class _Src:
    """Berkas dibuka SEKALI, lalu fstat: hanya berkas biasa (tolak FIFO / perangkat / folder) tanpa celah TOCTOU."""

    def __init__(self, path, write: bool = False):
        flags = (os.O_RDWR if write else os.O_RDONLY) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(str(Path(str(path)).expanduser()), flags)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise _NotRegular("bukan berkas biasa (FIFO / perangkat / folder ditolak)")
            self.fh = os.fdopen(fd, "r+b" if write else "rb")
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        self.size = st.st_size

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0:
            return b""
        self.fh.seek(off)
        return self.fh.read(n)

    def close(self):
        try:
            self.fh.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def _to_int(v, name: str = "nilai") -> int:
    if isinstance(v, bool):
        raise ValueError("%s tidak valid" % name)
    if isinstance(v, int):
        return v
    try:
        return int(str(v).strip(), 0)
    except ValueError:
        raise ValueError("%s bukan bilangan bulat: %r" % (name, str(v)[:40]))


def _norm_offset(off, size: int) -> int:
    o = _to_int(off, "offset")
    return max(0, size + o) if o < 0 else o     # offset negatif = dihitung dari akhir berkas


def _parse_hex(s, allow_wild: bool = False):
    """'4D 5A 90', '4d5a90', '0x4D,0x5A', '4D ?? 00' -> list[int | None] (None = wildcard)."""
    t = re.sub(r"0x", " ", str(s), flags=re.I)
    toks = [x for x in re.split(r"[\s,;:-]+", t) if x]
    if len(toks) == 1 and re.fullmatch(r"(?:[0-9A-Fa-f]{2}|\?\?)+", toks[0]) and len(toks[0]) > 2:
        toks = re.findall(r"[0-9A-Fa-f]{2}|\?\?", toks[0])
    out = []
    for tk in toks:
        if tk in ("?", "??"):
            if not allow_wild:
                raise ValueError("wildcard ?? tidak boleh di sini")
            out.append(None)
        elif re.fullmatch(r"[0-9A-Fa-f]{1,2}", tk):
            out.append(int(tk, 16))
        else:
            raise ValueError("token hex tidak valid: %r" % tk[:20])
    if not out:
        raise ValueError("pola hex kosong")
    return out


def _as_bytes(data) -> bytes:
    """bytes apa adanya; str: 'text:...' / 'u16:...' atau hex ('90 90')."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    s = str(data)
    if s.startswith("text:"):
        return s[5:].encode("utf-8")
    if s.startswith("u16:"):
        return s[4:].encode("utf-16-le")
    return bytes(_parse_hex(s))


def _sha256_file(path) -> str:
    h = hashlib.sha256()
    with _Src(path) as s:
        pos = 0
        while True:
            b = s.read_at(pos, COMPARE_CHUNK)
            if not b:
                break
            h.update(b)
            pos += len(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------------
# Hex view
# ---------------------------------------------------------------------------------------------------

_LATIN1 = "".join(chr(i) if (0x20 <= i <= 0x7E or (0xA1 <= i <= 0xFF and i != 0xAD)) else "." for i in range(256))
_bn_ASCII = "".join(chr(i) if 0x20 <= i <= 0x7E else "." for i in range(256))


def _ebcdic_table() -> str:
    t = []
    for i in range(256):
        try:
            c = bytes([i]).decode("cp037")
        except UnicodeDecodeError:
            c = "."
        t.append(c if (0x20 <= ord(c) <= 0x7E) else ".")
    return "".join(t)


_EBCDIC = _ebcdic_table()
_ENC_ALIASES = {"ascii": "ascii", "latin1": "latin1", "latin-1": "latin1", "iso-8859-1": "latin1", "cp1252": "latin1",
                "ebcdic": "ebcdic", "cp037": "ebcdic", "utf16": "utf16", "utf-16": "utf16", "utf16le": "utf16", "utf-16le": "utf16"}


def _text_column(row: bytes, enc: str) -> str:
    if enc == "utf16":
        out = []
        for i in range(0, len(row) - 1, 2):
            u = row[i] | (row[i + 1] << 8)
            c = chr(u) if (0x20 <= u < 0xD800 or 0xE000 <= u < 0xFFFE) else "."
            out.append(c if c.isprintable() else ".")
        if len(row) % 2:
            out.append(".")
        return "".join(out)
    table = {"ascii": _bn_ASCII, "latin1": _LATIN1, "ebcdic": _EBCDIC}[enc]
    return "".join(table[b] for b in row)


def hex_view(path, offset=0, length: int = 256, encoding: str = "ascii", width: int = 16) -> dict:
    """Tampilan hex hanya-baca. offset negatif = dari akhir berkas. length dibatasi MAX_HEX."""
    try:
        enc = _ENC_ALIASES.get(str(encoding).lower())
        if enc is None:
            return _bn_err("bad_encoding", "encoding tidak didukung: %s (ascii, latin1, ebcdic, utf16)" % _bn_clean(encoding, 20))
        width = _to_int(width, "width")
        width = width if width in (8, 16, 32) else 16
        length = _to_int(length, "length")
        length = 256 if length <= 0 else min(length, MAX_HEX)
        with _Src(path) as s:
            size = s.size
            off = _norm_offset(offset, size)
            if size == 0:
                return {"status": "success", "path": str(path), "size": 0, "offset": 0, "length": 0, "eof": True, "next_offset": None,
                        "encoding": enc, "text": "HEX %s | berkas kosong (0 byte)" % _bn_clean(Path(str(path)).name, 80)}
            if off >= size:
                return _bn_err("offset_out_of_range", "offset 0x%X di luar berkas (ukuran %d byte = 0x%X)" % (off, size, size))
            data = s.read_at(off, length)
        aw = 16 if size > 0xFFFFFFFF else 8
        L = ["HEX %s | ukuran %d (0x%X) | offset 0x%X | %d byte | %s" % (_bn_clean(Path(str(path)).name, 80), size, size, off, len(data), enc)]
        for i in range(0, len(data), width):
            row = data[i:i + width]
            cells = []
            for j in range(width):
                cells.append("%02X" % row[j] if j < len(row) else "  ")
                if j % 8 == 7 and j != width - 1:
                    cells.append("")
            L.append("%0*X  %s  |%s|" % (aw, off + i, " ".join(cells), _text_column(row, enc)))
        end = off + len(data)
        return {"status": "success", "path": str(path), "size": size, "offset": off, "length": len(data), "eof": end >= size,
                "next_offset": None if end >= size else end, "encoding": enc, "text": "\n".join(L)}
    except Exception as e:
        return _fail(e)


# ---------------------------------------------------------------------------------------------------
# Inspektor data
# ---------------------------------------------------------------------------------------------------

def _fmt_time(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC"


def _plausible(dt) -> bool:
    return 1990 <= dt.year <= 2100


def inspect_at(path, offset=0) -> dict:
    """Tafsirkan byte di `offset` sebagai berbagai tipe data (little / big endian), waktu, GUID, IPv4, karakter."""
    try:
        with _Src(path) as s:
            off = _norm_offset(offset, s.size)
            if off >= s.size:
                return _bn_err("offset_out_of_range", "offset 0x%X di luar berkas (ukuran %d)" % (off, s.size))
            b = s.read_at(off, 16)
        n = len(b)
        v: dict = {}
        v["byte"] = "0x%02X  u8=%d  i8=%d  bin=%s  char=%r" % (b[0], b[0], b[0] - 256 if b[0] > 127 else b[0], format(b[0], "08b"), chr(b[0]) if 0x20 <= b[0] < 0x7F else ".")
        for size, code in ((2, "H"), (4, "I"), (8, "Q")):
            if n >= size:
                for endian, tag in (("<", "LE"), (">", "BE")):
                    u = struct.unpack_from(endian + code, b)[0]
                    i = struct.unpack_from(endian + code.lower(), b)[0]
                    v["u%d %s" % (size * 8, tag)] = "%d (0x%X)  | i%d=%d" % (u, u, size * 8, i)
        for size, code in ((4, "f"), (8, "d")):
            if n >= size:
                for endian, tag in (("<", "LE"), (">", "BE")):
                    f = struct.unpack_from(endian + code, b)[0]
                    v["f%d %s" % (size * 8, tag)] = "nan" if math.isnan(f) else ("%r" % f)
        if n >= 4:
            v["IPv4"] = ".".join(str(x) for x in b[:4])
            t = struct.unpack_from("<I", b)[0]
            try:
                dt = datetime.fromtimestamp(t, timezone.utc)
                if _plausible(dt):
                    v["Unix time32 LE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
            tb = struct.unpack_from(">I", b)[0]
            try:
                dt = datetime.fromtimestamp(tb, timezone.utc)
                if _plausible(dt):
                    v["Unix time32 BE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
            tm, dd = struct.unpack_from("<HH", b)
            sec, mi, hh = (tm & 31) * 2, (tm >> 5) & 63, tm >> 11
            da, mo, yr = dd & 31, (dd >> 5) & 15, 1980 + (dd >> 9)
            if 1 <= da <= 31 and 1 <= mo <= 12 and hh < 24 and mi < 60 and sec < 60 and 1990 <= yr <= 2100:
                v["DOS date/time"] = "%04d-%02d-%02d %02d:%02d:%02d" % (yr, mo, da, hh, mi, sec)
        if n >= 8:
            ft = struct.unpack_from("<Q", b)[0]
            try:
                dt = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ft // 10)
                if _plausible(dt):
                    v["FILETIME LE"] = _fmt_time(dt)
            except OverflowError:
                pass
            t64 = struct.unpack_from("<Q", b)[0]
            try:
                dt = datetime.fromtimestamp(t64, timezone.utc)
                if _plausible(dt):
                    v["Unix time64 LE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
        if n >= 16:
            d1, d2, d3 = struct.unpack_from("<IHH", b)
            v["GUID (mixed-endian)"] = "{%08X-%04X-%04X-%s-%s}" % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
        for ln in (4, 3, 2, 1):
            try:
                ch = b[:ln].decode("utf-8")
                if ch and ch.isprintable():
                    v["UTF-8"] = "%r (U+%04X)" % (ch[0], ord(ch[0]))
                    break
            except UnicodeDecodeError:
                continue
        if n >= 2:
            u = b[0] | (b[1] << 8)
            if 0x20 <= u < 0xD800:
                v["UTF-16 LE"] = "%r (U+%04X)" % (chr(u), u)
        return {"status": "success", "path": str(path), "offset": off, "bytes": b.hex(), "values": v}
    except Exception as e:
        return _fail(e)


def inspect_text(path, offset=0) -> str:
    r = inspect_at(path, offset)
    if r.get("status") != "success":
        return "INSPEKSI gagal: %s" % r.get("message", r.get("code"))
    L = ["INSPEKTOR DATA %s @ 0x%X | %s" % (_bn_clean(Path(str(path)).name, 80), r["offset"], " ".join(r["bytes"][i:i + 2] for i in range(0, len(r["bytes"]), 2)).upper())]
    L += ["  %-20s %s" % (k, x) for k, x in r["values"].items()]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# Pencarian
# ---------------------------------------------------------------------------------------------------

def _compile_pattern(pattern, mode: str, ignore_case: bool):
    p = str(pattern)
    m = (mode or "auto").lower()
    if m == "auto":
        low = p.lower()
        if low.startswith("hex:"):
            m, p = "hex", p[4:]
        elif low.startswith("re:"):
            m, p = "regex", p[3:]
        elif low.startswith("u16:"):
            m, p = "utf16", p[4:]
        else:
            m = "text"
    if not p:
        raise ValueError("pola kosong")
    if len(p) > 2000:
        raise ValueError("pola terlalu panjang (maks 2000 karakter)")
    flags = re.DOTALL | (re.IGNORECASE if ignore_case else 0)
    if m == "hex":
        toks = _parse_hex(p, allow_wild=True)
        rx = b"".join(b"." if t is None else re.escape(bytes([t])) for t in toks)
        return m, re.compile(rx, re.DOTALL), len(toks)
    if m == "text":
        raw = p.encode("utf-8")
        return m, re.compile(re.escape(raw), flags), len(raw)
    if m == "utf16":
        raw = p.encode("utf-16-le")
        return m, re.compile(re.escape(raw), re.DOTALL), len(raw)    # huruf besar / kecil UTF-16 tidak dilipat
    if m == "regex":
        return m, re.compile(p.encode("latin-1", "replace"), flags), 0
    raise ValueError("mode pencarian tidak dikenal: %s (auto, hex, text, utf16, regex)" % m[:20])


def search(path, pattern, mode: str = "auto", ignore_case: bool = False, start=0, end=None, max_hits: int = 200, context: int = 8) -> dict:
    """Cari pola di berkas. mode: auto (awalan 'hex:' / 're:' / 'u16:' atau teks biasa) | hex (boleh ??) | text | utf16 | regex (bytes, latin-1).
    Mode regex memakai mesin `re` Python: pola yang sangat rumit bisa lambat; ada batas waktu antar-potongan (SEARCH_TIME)."""
    try:
        m, rx, _plen = _compile_pattern(pattern, mode, ignore_case)
        max_hits = max(1, min(_to_int(max_hits, "max_hits"), MAX_HITS))
        context = max(0, min(_to_int(context, "context"), 64))
        t0 = time.time()
        hits: list = []
        truncated = timeout = False
        with _Src(path) as s:
            lo = _norm_offset(start, s.size)
            hi = s.size if end is None else min(s.size, _norm_offset(end, s.size))
            pos = lo
            while pos < hi and not truncated:
                if time.time() - t0 > SEARCH_TIME:
                    timeout = truncated = True
                    break
                chunk = s.read_at(pos, min(SEARCH_CHUNK + SEARCH_OVERLAP, hi - pos))
                more = pos + SEARCH_CHUNK < hi
                for mt in rx.finditer(chunk):
                    a = mt.start()
                    if more and a >= SEARCH_CHUNK:
                        break
                    if mt.end() == a:
                        continue
                    hits.append((pos + a, mt.end() - a))
                    if len(hits) >= max_hits:
                        truncated = True
                        break
                pos += SEARCH_CHUNK
            out = []
            for off, ln in hits:
                ctx = s.read_at(max(0, off - context), ln + 2 * context) if context else b""
                body = s.read_at(off, min(ln, 48))
                out.append({"offset": off, "length": ln, "hex": body.hex(" ").upper(), "ascii": "".join(_bn_ASCII[x] for x in body),
                            "context_ascii": "".join(_bn_ASCII[x] for x in ctx) if context else ""})
        return {"status": "success", "path": str(path), "mode": m, "pattern": _bn_clean(pattern, 120), "count": len(out), "hits": out,
                "truncated": truncated, "timeout": timeout, "range": [lo, hi], "elapsed": round(time.time() - t0, 3)}
    except (ValueError, re.error) as e:
        return _bn_err("bad_pattern", "%s" % e)
    except Exception as e:
        return _fail(e)


def search_text(path, pattern, **kw) -> str:
    r = search(path, pattern, **kw)
    if r.get("status") != "success":
        return "CARI gagal: %s" % r.get("message", r.get("code"))
    L = ["CARI %s [%s] di %s: %d hasil%s" % (r["pattern"], r["mode"], _bn_clean(Path(str(path)).name, 80), r["count"],
                                           " (DIPOTONG%s)" % (", waktu habis" if r["timeout"] else "") if r["truncated"] else "")]
    for h in r["hits"][:50]:
        L.append("  0x%08X  +%d  %s  |%s|" % (h["offset"], h["length"], h["hex"][:48], h["ascii"][:24]))
    if r["count"] > 50:
        L.append("  ... +%d hasil lain" % (r["count"] - 50))
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------------------------------

def compare_files(a, b, max_ranges: int = MAX_RANGES) -> dict:
    """Bandingkan dua berkas byte demi byte (hash dihitung dalam satu lintasan). Rentang berbeda digabung bila bersebelahan."""
    try:
        max_ranges = max(1, min(_to_int(max_ranges, "max_ranges"), 5000))
        with _Src(a) as sa, _Src(b) as sb:
            size_a, size_b = sa.size, sb.size
            common = min(size_a, size_b)
            ha, hb = hashlib.sha256(), hashlib.sha256()
            ranges: list = []
            differing = 0
            first = None
            truncated = False
            pos = 0
            open_end = -1       # akhir rentang terakhir (untuk menggabungkan rentang yang menyambung antar-potongan)
            while pos < common:
                n = min(COMPARE_CHUNK, common - pos)
                ca, cb = sa.read_at(pos, n), sb.read_at(pos, n)
                if len(ca) != len(cb) or not ca:
                    break       # berkas berubah saat dibaca
                ha.update(ca)
                hb.update(cb)
                if ca != cb:
                    i, ln = 0, len(ca)
                    while i < ln:
                        if ca[i] == cb[i]:
                            i += 1
                            continue
                        j = i
                        while j < ln and ca[j] != cb[j]:
                            j += 1
                        absolute = pos + i
                        differing += j - i
                        if first is None:
                            first = absolute
                        if ranges and open_end == absolute:
                            ranges[-1]["length"] += j - i
                        elif len(ranges) < max_ranges:
                            ranges.append({"offset": absolute, "length": j - i})
                        else:
                            truncated = True
                        open_end = absolute + (j - i)
                        i = j
                pos += len(ca)
            extra = None
            if size_a != size_b:
                longer, sl, which = (sa, size_a, "A") if size_a > size_b else (sb, size_b, "B")
                hl = ha if which == "A" else hb
                p2 = common
                while p2 < sl:
                    c = longer.read_at(p2, COMPARE_CHUNK)
                    if not c:
                        break
                    hl.update(c)
                    p2 += len(c)
                extra = {"length": abs(size_a - size_b), "in": which}
                if first is None:
                    first = common
            return {"status": "success", "a": str(a), "b": str(b), "size_a": size_a, "size_b": size_b, "size_delta": size_b - size_a,
                    "identical": size_a == size_b and differing == 0, "sha256_a": ha.hexdigest(), "sha256_b": hb.hexdigest(),
                    "differing_bytes": differing, "changed_ranges": ranges, "truncated": truncated, "first_diff": first, "extra_bytes": extra}
    except Exception as e:
        return _fail(e)


def _walk_files(root: Path) -> dict:
    """{path relatif (posix): (path, ukuran)} untuk berkas biasa; tautan simbolik dan berkas khusus dilewati."""
    out: dict = {}
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            it = list(os.scandir(d))
        except OSError:
            continue
        for e in it:
            try:
                if e.is_symlink():
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(Path(e.path))
                elif e.is_file(follow_symlinks=False):
                    out[Path(e.path).relative_to(root).as_posix()] = (e.path, e.stat(follow_symlinks=False).st_size)
                    if len(out) > MAX_DIR_FILES:
                        raise OverflowError("terlalu banyak berkas (> %d)" % MAX_DIR_FILES)
            except OSError:
                continue
    return out


def _same_content(pa: str, pb: str) -> bool:
    with _Src(pa) as x, _Src(pb) as y:
        if x.size != y.size:
            return False
        pos = 0
        while pos < x.size:
            if x.read_at(pos, COMPARE_CHUNK) != y.read_at(pos, COMPARE_CHUNK):
                return False
            pos += COMPARE_CHUNK
    return True


def compare_dirs(a, b) -> dict:
    """Bandingkan dua folder (rekursif, isi berkas dibandingkan langsung). added = hanya di B, removed = hanya di A."""
    try:
        pa, pb = Path(str(a)).expanduser(), Path(str(b)).expanduser()
        for p in (pa, pb):
            if not p.is_dir():
                return _bn_err("not_directory", "bukan folder: %s" % _bn_clean(p, 120))
        fa, fb = _walk_files(pa), _walk_files(pb)
        added = sorted(set(fb) - set(fa))
        removed = sorted(set(fa) - set(fb))
        changed, same = [], 0
        for k in sorted(set(fa) & set(fb)):
            (xa, sza), (xb, szb) = fa[k], fb[k]
            try:
                eq = sza == szb and _same_content(xa, xb)
            except OSError:
                eq = False
            if eq:
                same += 1
            else:
                changed.append({"path": k, "size_a": sza, "size_b": szb})
        return {"status": "success", "a": str(a), "b": str(b), "added": added, "removed": removed, "changed": changed, "unchanged_count": same}
    except Exception as e:
        return _fail(e)


# ---------------------------------------------------------------------------------------------------
# Patch + undo
# ---------------------------------------------------------------------------------------------------

def _journal_path(path) -> Path:
    p = Path(str(path)).expanduser()
    return p.with_name(p.name + ".rea_undo.json")


def _orig_path(path) -> Path:
    p = Path(str(path)).expanduser()
    return p.with_name(p.name + ".rea_orig")


def _load_journal(path) -> dict:
    jp = _journal_path(path)
    if jp.exists():
        try:
            j = json.loads(jp.read_text(encoding="utf-8"))
            if isinstance(j, dict) and isinstance(j.get("entries"), list):
                return j
        except (OSError, ValueError):
            raise ValueError("jurnal undo rusak: %s" % jp.name)
    return {"version": 1, "target": Path(str(path)).name, "original_sha256": None, "original_size": None, "backup": None, "entries": []}


def _save_journal(path, j: dict):
    jp = _journal_path(path)
    tmp = jp.with_name(jp.name + ".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, jp)


def _fsync_write(s: _Src, off: int, data: bytes):
    s.fh.seek(off)
    s.fh.write(data)
    s.fh.flush()
    try:
        os.fsync(s.fh.fileno())
    except OSError:
        pass


def patch(path, offset, data, expect=None, dry_run: bool = False, note: str = "", backup: bool = True) -> dict:
    """Timpa byte di `offset` (panjang tetap; tidak menambah / menghapus). data: bytes, atau str hex ('90 90') / 'text:...' / 'u16:...'.
    expect (opsional): byte lama yang diharapkan; tidak cocok -> tidak ada yang ditulis. Setiap patch dicatat di jurnal untuk undo()."""
    try:
        new = _as_bytes(data)
        if not new:
            return _bn_err("empty_patch", "data patch kosong")
        if len(new) > MAX_PATCH:
            return _bn_err("patch_too_large", "patch %d byte melebihi batas %d" % (len(new), MAX_PATCH))
        exp = _as_bytes(expect) if expect not in (None, "") else None
        with _Src(path, write=not dry_run) as s:
            off = _norm_offset(offset, s.size)
            if off + len(new) > s.size:
                return _bn_err("out_of_range", "patch 0x%X..0x%X melewati akhir berkas (%d byte); patch hanya menimpa" % (off, off + len(new), s.size))
            old = s.read_at(off, len(new))
            if exp is not None and old != exp:
                return _bn_err("expect_mismatch", "byte lama di 0x%X adalah %s, bukan %s; tidak ada yang ditulis" % (off, old.hex(" ").upper()[:60], exp.hex(" ").upper()[:60]))
            res = {"status": "success", "path": str(path), "offset": off, "length": len(new), "old_hex": old.hex(" ").upper(), "new_hex": new.hex(" ").upper(),
                   "dry_run": bool(dry_run), "unchanged": old == new}
            if dry_run or old == new:
                return res
            j = _load_journal(path)
            if len(j["entries"]) >= MAX_JOURNAL:
                return _bn_err("journal_full", "jurnal undo penuh (%d entri); pulihkan atau buang jurnal dulu" % MAX_JOURNAL)
            if not j["entries"] and j.get("original_sha256") is None:
                if backup and s.size <= MAX_BACKUP and not _orig_path(path).exists():
                    shutil.copyfile(str(Path(str(path)).expanduser()), str(_orig_path(path)))
                    j["backup"] = _orig_path(path).name
                j["original_size"] = s.size
                j["original_sha256"] = _sha256_file(path) if s.size <= HASH_LIMIT else None
            nid = max([e["id"] for e in j["entries"]] + [0]) + 1
            entry = {"id": nid, "time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "offset": off, "old": old.hex(), "new": new.hex(),
                     "note": _bn_clean(note, 120), "undone": False}
            j["entries"].append(entry)
            _save_journal(path, j)          # jurnal lebih dulu: bila crash, perubahan tetap bisa dibalik
            try:
                _fsync_write(s, off, new)
            except BaseException:
                j["entries"].pop()
                _save_journal(path, j)
                raise
        res["id"] = nid
        res["sha256_after"] = _sha256_file(path) if Path(str(path)).stat().st_size <= HASH_LIMIT else None
        res["backup"] = j.get("backup")
        return res
    except ValueError as e:
        return _bn_err("bad_argument", e)
    except Exception as e:
        return _fail(e)


def history(path) -> dict:
    try:
        if not Path(str(path)).expanduser().is_file():
            return _bn_err("not_found", "berkas tidak ditemukan")
        j = _load_journal(path)
        return {"status": "success", "path": str(path), "original_sha256": j.get("original_sha256"), "original_size": j.get("original_size"),
                "backup": j.get("backup") if _orig_path(path).exists() else None, "entries": j["entries"]}
    except Exception as e:
        return _fail(e)


def undo(path, id=None, force: bool = False) -> dict:
    """Balikkan patch terakhir yang belum di-undo (atau `id`). Byte saat ini harus sama dengan byte hasil patch (kecuali force=True)."""
    try:
        j = _load_journal(path)
        live = [e for e in j["entries"] if not e.get("undone")]
        if not live:
            return _bn_err("nothing_to_undo", "tidak ada patch yang bisa di-undo")
        if id is None:
            e = live[-1]
        else:
            tid = _to_int(id, "id")
            e = next((x for x in live if x["id"] == tid), None)
            if e is None:
                return _bn_err("no_such_patch", "patch #%d tidak ada atau sudah di-undo" % tid)
        new, old = bytes.fromhex(e["new"]), bytes.fromhex(e["old"])
        with _Src(path, write=True) as s:
            cur = s.read_at(e["offset"], len(new))
            if cur != new and not force:
                return _bn_err("changed_since", "byte di 0x%X sudah berubah sejak patch #%d (sekarang %s); pakai force untuk tetap memulihkan" % (
                    e["offset"], e["id"], cur.hex(" ").upper()[:60]))
            _fsync_write(s, e["offset"], old)
        e["undone"] = True
        e["undone_time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _save_journal(path, j)
        return {"status": "success", "path": str(path), "id": e["id"], "offset": e["offset"], "length": len(old), "restored_hex": old.hex(" ").upper(),
                "remaining": len([x for x in j["entries"] if not x.get("undone")])}
    except ValueError as e:
        return _bn_err("bad_argument", e)
    except Exception as e:
        return _fail(e)


def restore_original(path) -> dict:
    """Kembalikan berkas ke salinan asli (`.rea_orig`) dan tandai semua patch sebagai di-undo. Tidak jalan bila salinan tak ada."""
    try:
        op = _orig_path(path)
        if not op.is_file():
            return _bn_err("no_backup", "salinan asli (%s) tidak ada" % op.name)
        j = _load_journal(path)
        target = Path(str(path)).expanduser()
        tmp = target.with_name(target.name + ".rea_restore.tmp")
        shutil.copyfile(str(op), str(tmp))
        os.replace(tmp, target)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for e in j["entries"]:
            if not e.get("undone"):
                e["undone"], e["undone_time"] = True, now
        _save_journal(path, j)
        return {"status": "success", "path": str(path), "restored_from": op.name,
                "sha256": _sha256_file(path) if target.stat().st_size <= HASH_LIMIT else None, "original_sha256": j.get("original_sha256")}
    except Exception as e:
        return _fail(e)


def patch_text(r: dict) -> str:
    if r.get("status") != "success":
        return "PATCH gagal: %s" % r.get("message", r.get("code"))
    tag = "SIMULASI " if r.get("dry_run") else ""
    L = ["%sPATCH @ 0x%X (%d byte): %s -> %s%s" % (tag, r["offset"], r["length"], r["old_hex"][:60], r["new_hex"][:60], " (tidak ada perubahan)" if r.get("unchanged") else "")]
    if r.get("id"):
        L.append("  jurnal #%d | undo: undo(path)%s" % (r["id"], " | salinan asli: %s" % r["backup"] if r.get("backup") else ""))
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------

def _opt(argv: list, name: str, default=None, flag: bool = False):
    if name in argv:
        i = argv.index(name)
        if flag:
            del argv[i]
            return True
        v = argv[i + 1] if i + 1 < len(argv) else default
        del argv[i:i + 2]
        return v
    return False if flag else default


def _bn_main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_BN_DOC.split("CLI:")[1].strip() if "CLI:" in _BN_DOC else "pemakaian: lihat dokumentasi modul")
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "hex" and rest:
        enc = _opt(rest, "--encoding", "ascii")
        r = hex_view(rest[0], rest[1] if len(rest) > 1 else 0, rest[2] if len(rest) > 2 else 256, encoding=enc)
        print(r["text"] if r["status"] == "success" else "HEX gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    if cmd == "inspect" and rest:
        print(inspect_text(rest[0], rest[1] if len(rest) > 1 else 0))
        return 0
    if cmd == "search" and len(rest) > 1:
        mode, ic = _opt(rest, "--mode", "auto"), _opt(rest, "-i", flag=True)
        print(search_text(rest[0], rest[1], mode=mode, ignore_case=ic))
        return 0
    if cmd == "compare" and len(rest) > 1:
        r = compare_files(rest[0], rest[1]) if not Path(rest[0]).is_dir() else compare_dirs(rest[0], rest[1])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["status"] == "success" else 1
    if cmd == "patch" and len(rest) > 2:
        exp, dry = _opt(rest, "--expect"), _opt(rest, "--dry-run", flag=True)
        r = patch(rest[0], rest[1], rest[2], expect=exp, dry_run=dry)
        print(patch_text(r))
        return 0 if r["status"] == "success" else 1
    if cmd == "undo" and rest:
        force = _opt(rest, "--force", flag=True)
        r = undo(rest[0], rest[1] if len(rest) > 1 else None, force=force)
        print("UNDO patch #%s @ 0x%X dipulihkan (%d byte); sisa %d" % (r["id"], r["offset"], r["length"], r["remaining"]) if r["status"] == "success" else "UNDO gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    if cmd == "history" and rest:
        print(json.dumps(history(rest[0]), ensure_ascii=False, indent=1))
        return 0
    if cmd == "restore" and rest:
        r = restore_original(rest[0])
        print("PULIH dari %s" % r["restored_from"] if r["status"] == "success" else "PULIH gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    print("perintah tidak dikenal / argumen kurang; jalankan tanpa argumen untuk bantuan")
    return 1

