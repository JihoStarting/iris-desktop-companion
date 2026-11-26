# rea_triage bagian 37/47: assets_dasar (baris asli 16568-16903). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
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
#   gambar       : PNG / APNG, JPEG, GIF, BMP, TGA, DDS (DXT1/3/5, BC4, BC5 + RGBA tak terkompresi), WebP, ICO
#   audio        : WAV, OGG (Vorbis / Opus), FLAC, MP3, MIDI
#   arsip / game : Quake PAK, WAD (Doom / Quake / Half-Life), Unreal .pak (v1-v11, tanpa enkripsi), ZIP (APK / JAR / OOXML ...), TAR, GZIP,
#                  UnityFS (ekstraksi node), 7z / RAR (deteksi saja)
#   data         : SQLite
#
# Yang BELUM / tidak bisa dibuka langsung (dilaporkan jelas, bukan ditebak): paket terenkripsi / dikompres format sendiri, aset Unity /
# Unreal yang terserialisasi (butuh parser per versi mesin), tekstur BC6H / BC7 / ASTC. Untuk itu tulis plugin (di bawah).
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
import csv
import fnmatch
import importlib.util
import io
import mmap
import re
import sqlite3
import tarfile
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from contextlib import contextmanager

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


# v103.2: sama dengan _CTRL_RE bagian utama: kontrol, C1, dan pengecoh arah teks (RLO dll.) dari berkas tak tepercaya
_as_ctrl_re = re.compile(r"[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")


def _as_clean(s, n=200) -> str:
    """Bersihkan teks dari berkas tak tepercaya (tanpa baris baru / karakter kontrol) sebelum masuk laporan."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8", "replace")
    return _as_ctrl_re.sub(" ", str(s))[:n]


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
        part = _as_ctrl_re.sub("_", re.sub(r'[<>:"|?*\x00-\x1f]', "_", part)).rstrip(". ") or "_"
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


