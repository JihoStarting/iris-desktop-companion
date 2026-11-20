"""rea_assets.py - v99.0 Asset Explorer untuk REA (jembatan ke rea_triage.py).

Tujuan: REA tidak hanya membedah .exe / .dll, tetapi bisa MEMBUKA ISI hampir semua berkas: model 3D, animasi, tekstur,
audio, arsip / paket game, database, dan data tertanam di dalam berkas lain. Hanya pustaka standar, hanya-baca terhadap
berkas sumber (hasil selalu ditulis ke folder keluaran terpisah), TANPA menjalankan apa pun dari berkas.

API (semua tidak melempar kecuali dinyatakan):
    identify(path) -> dict                        jenis berkas + kategori (deteksi lewat magic bytes, bukan ekstensi saja)
    describe(path) -> dict / describe_text(path)  ringkasan isi: mesh, animasi, tekstur, daftar entri arsip, tabel DB ...
    extract(path, outdir, pattern=None, convert=True) -> manifest dict
                                                  mengeluarkan isi: gambar / buffer dari glTF, mesh -> .obj, animasi -> .json / .csv,
                                                  tekstur DDS / TGA / BMP -> .png, entri arsip (PAK / WAD / ZIP / TAR ...), tabel SQLite -> .csv
    carve(path, outdir=None, max_items=200) -> dict   cari & potong berkas yang TERTANAM di dalam berkas apa pun (PNG, JPEG, GIF, OGG, RIFF,
                                                  GLB, SQLite, ZIP, MIDI ...) -- berguna untuk .exe / .dat / resource yang tidak punya format terdokumentasi
    formats() -> list[dict]                       daftar parser terpasang (termasuk plugin)
    load_plugins(folder) -> list[str]             muat parser tambahan (lihat bagian PLUGIN)

Format bawaan:
  3D / animasi : glTF / GLB, OBJ, STL, PLY, FBX (biner; ASCII hanya ringkasan), COLLADA (.dae), BVH
  gambar       : PNG / APNG, JPEG, GIF, BMP, TGA, DDS (DXT1/3/5 + RGBA tak terkompresi), WebP, ICO
  audio        : WAV, OGG (Vorbis / Opus), FLAC, MP3, MIDI
  arsip / game : Quake PAK, WAD (Doom / Quake / Half-Life), Unreal .pak (v1-v9, tanpa enkripsi), ZIP (APK / JAR / OOXML ...), TAR, GZIP,
                 header UnityFS / 7z / RAR (deteksi saja)
  data         : SQLite

Yang BELUM / tidak bisa dibuka langsung (dilaporkan jelas, bukan ditebak): paket terenkripsi / dikompres format sendiri, aset Unity /
Unreal yang terserialisasi (butuh parser per versi mesin), tekstur BC4-BC7 / ASTC. Untuk itu tulis plugin (di bawah).

PLUGIN (parser buatan sendiri, ala QuickBMS): buat folder berisi berkas .py, masing-masing memuat
    def register_formats(reg):
        reg("nama", "kategori", detect, inspect=None, extract=None, priority=50, about="")
  detect(d, ext) -> bool        d = isi berkas (mmap / bytes, hanya-baca), ext = ekstensi huruf kecil
  inspect(d, path) -> {"lines": [str], "info": {...}, "extract": "apa yang bisa diekstrak"}
  extract(d, path, out, opts)   out.write("sub/nama.bin", bytes, kind="...") ; opts = {"pattern": ..., "convert": bool}
Plugin adalah KODE yang dijalankan: dimuat hanya bila diminta eksplisit (--plugins FOLDER, env REA_PLUGINS, atau load_plugins()),
TIDAK pernah lewat permintaan API agen.
"""
from __future__ import annotations

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

VERSION = "99.0"
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


def _human(n: float) -> str:
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%d %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f GB" % n


def _clean(s, n=200) -> str:
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
            got.append("%s (GAGAL: %s)" % (f.name, _clean(e, 80)))
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


def _entropy(b) -> float:
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
    L.append("glTF %s | generator: %s" % (_clean(ast.get("version", "?")), _clean(ast.get("generator", "-"), 80)))
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
            L.append("  mesh[%d] %s: %d primitif, %d vertex, ~%d segitiga" % (mi, _clean(m.get("name", "-"), 40), len(m.get("primitives", [])), v, t))
    L.append("total: %d vertex, ~%d segitiga" % (tv, tt))
    for i, im in enumerate(g("images")[:10]):
        src = "bufferView" if "bufferView" in im else ("data URI" if str(im.get("uri", "")).startswith("data:") else _clean(im.get("uri", "?"), 60))
        L.append("  gambar[%d] %s (%s)" % (i, _clean(im.get("mimeType", "?"), 20), src))
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
            i, _clean(an.get("name", "-"), 40), len(an.get("channels", [])), ", ".join("%s x%d" % kv for kv in paths.items()), dur))
    if j.get("extensionsUsed"):
        L.append("ekstensi dipakai: " + ", ".join(_clean(x, 40) for x in j["extensionsUsed"][:12]))
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
            out.errors.append("gambar[%d]: %s" % (i, _clean(e, 100)))
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
            out.errors.append("mesh[%d]: %s" % (mi, _clean(e, 100)))
    # animasi
    nodes = j.get("nodes", []) or []
    nname = lambda i: _clean((nodes[i].get("name") if 0 <= (i if i is not None else -1) < len(nodes) else None) or "node%s" % i, 60)
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
            out.errors.append("animasi[%d]: %s" % (ai, _clean(e, 100)))


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
            mtl.append(_clean(t[1], 60))
        if k in (b"o", b"g") and len(t) > 1 and len(groups) < 10:
            groups.append(_clean(t[1], 40))
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
        hd = _clean(bytes(d[:80]).rstrip(b"\x00 "), 80)
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
            comments.append(_clean(" ".join(t[1:]), 80))
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
    L = ["PLY (%s): " % fmt + ", ".join("%s x%d [%s]" % (_clean(e["name"], 20), e["count"], ", ".join(_clean(x[0], 14) for x in e["props"][:8])) for e in elems)]
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
    return _clean(s.split("\x00\x01")[0] or "unnamed", 60)


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
        L.append("tipe Model: " + ", ".join("%s x%d" % (_clean(k, 20), v) for k, v in models.most_common(8)))
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
                out.errors.append("geometri %s: %s" % (_fbx_cname(o), _clean(e, 100)))
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
            out.errors.append("curve: %s" % _clean(e, 100))
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
        L.append("sumbu atas: %s | unit: %s" % (_clean(ax or "?", 8), _clean(un.get("meter", "?") if un is not None else "?", 12)))
    imgs = [(e.text or "").strip() for e in r.iter() if _tag(e) == "init_from" and (e.text or "").strip()][:8]
    if imgs:
        L.append("gambar dirujuk: " + ", ".join(_clean(i, 50) for i in imgs))
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
            out.errors.append("geometri %s: %s" % (_clean(geom.get("id"), 40), _clean(e, 100)))


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
            cur = _clean(t[1], 40); joints.append(cur)
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
            txt.append(_clean(k, 30))
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
            info["comment"] = _clean(d[pos + 4:pos + 2 + ln], 80)
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
        L.append("  %dx%d, %d-bit, %s" % (w, h, _u16(d, 12 + 16 * i), _human(_u32(d, 14 + 16 * i))))
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
            L = ["%s: %d entri, total %s" % (a.kind, len(ents), _human(tot))]
            if ext:
                L.append("jenis: " + ", ".join("%s x%d" % kv for kv in ext.most_common(10)))
            L += a.notes
            for e in ents[:25]:
                L.append("  %s  %s%s" % (_clean(e["name"], 90), _human(e.get("size", 0)), "  [terenkripsi]" if e.get("enc") else ""))
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
                    out.errors.append("%s: %s" % (_clean(nm, 80), _clean(ex, 100)))
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
                               "mount point: %s | versi PAK: %d" % (_clean(mount, 60), ver)], kind="Unreal PAK")


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
        strs.append(_clean(d[pos:pos + end], 40)); pos += end + 1
    size, cbi, ubi, flags = struct.unpack_from(">qIII", d, pos)
    comp = {0: "tanpa kompresi", 1: "LZMA", 2: "LZ4", 3: "LZ4HC"}.get(flags & 0x3F, "?")
    return {"lines": ["Unity AssetBundle (UnityFS): versi Unity %s, revisi %s, %s, kompresi blok info: %s" % (strs[0] if strs else "?", strs[1] if len(strs) > 1 else "?", _human(size), comp),
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
            L.append("  tabel %s: %d baris [%s]" % (_clean(t, 40), n, ", ".join(_clean(c, 20) for c in cols[:10])))
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


def carve(path, outdir=None, max_items: int = 200, min_size: int = 64) -> dict:
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
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _clean(e, 150))}


def _carve_text(res: dict) -> str:
    if res.get("status") != "success":
        return "CARVE gagal: %s" % res.get("message")
    if not res["hits"]:
        return "CARVE: tidak ada tanda tangan berkas dikenal di dalam berkas ini."
    L = ["CARVE: %d tanda tangan ditemukan" % res["count"]]
    for h in res["hits"][:60]:
        L.append("  0x%08X  %-14s %s%s" % (h["offset"], h["type"], _human(h["length"]) if h["length"] else "(panjang tidak bisa dipastikan)",
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
    ent = _entropy(samp)
    printable = sum(1 for b in samp[:65536] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(samp[:65536]))
    L = []
    if printable > 0.95 and samp:
        txt = samp[:200000].decode("utf-8", "replace")
        first = _clean(txt.strip().split("\n", 1)[0], 100)
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
        res = carve(p, None, max_items=12)
        if res.get("hits"):
            L.append("berkas tertanam terdeteksi:")
            L += ["  0x%08X %s%s" % (h["offset"], h["type"], " (%s)" % _human(h["length"]) if h["length"] else "") for h in res["hits"][:12]]
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
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _clean(e, 150))}


def describe(path) -> dict:
    try:
        p = Path(str(path))
        with _map(p) as d:
            f = _detect(d, _ext(p))
            rep = {"status": "success", "path": str(p), "name": _clean(p.name, 120), "size": len(d), "sha256": _sha256(d),
                   "format": f.name if f else "unknown", "category": f.category if f else "unknown", "lines": [], "can_extract": bool(f and f.extract)}
            if f and f.inspect:
                try:
                    r = f.inspect(d, p) or {}
                    rep["lines"] = [_clean(x, 400) for x in r.get("lines", [])]
                    rep["extract_hint"] = r.get("extract", "")
                    if "entries" in r:
                        rep["entries"] = r["entries"]
                except Exception as e:
                    rep["lines"] = ["%s: gagal dibaca (%s: %s)" % (f.name, type(e).__name__, _clean(e, 150))]
                    rep["parse_error"] = True
            return rep
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _clean(e, 150))}


def describe_text(path, max_chars: int = 0) -> str:
    r = describe(path)
    if r.get("status") != "success":
        return "ASSETS gagal: %s" % r.get("message")
    L = ["ASSET EXPLORER (REA v%s)" % VERSION,
         "Berkas : %s | %s | SHA-256 %s..." % (r["name"], _human(r["size"]), r["sha256"][:16]),
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
            out.errors.append("konversi %s: %s" % (_clean(f["path"], 60), _clean(e, 90)))
        for sf in sub.files:
            sf = dict(sf)
            sf["path"] = (Path("_converted") / Path(f["path"]).with_suffix("") / sf["path"]).as_posix()
            sf["note"] = ("hasil konversi dari %s" % f["path"] + (" | " + sf["note"] if sf["note"] else ""))
            out.files.append(sf)
            out.total += sf["size"]
        out.errors += ["%s: %s" % (_clean(f["path"], 50), e) for e in sub.errors]
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
                out.errors.append("%s: %s" % (type(e).__name__, _clean(e, 160)))
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
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _clean(e, 150))}


def extract_text(path, outdir, pattern=None, convert: bool = True) -> str:
    m = extract(path, outdir, pattern, convert)
    if m.get("status") == "error":
        return "EKSTRAK gagal: %s" % m.get("message")
    L = ["EKSTRAK %s: %d berkas ke %s (dilewati %d, galat %d%s)" % (m["format"], m["entries_extracted"], m["outdir"], m["entries_skipped"], m["entries_failed"],
                                                                 ", %d hasil konversi" % m["converted_items"] if m["converted_items"] else "")]
    for f in m["files"][:30]:
        L.append("  %s  %s%s" % (f["path"], _human(f["size"]), "  (%s)" % f["note"] if f["note"] else ""))
    if m["entries_extracted"] > 30:
        L.append("  ... +%d lagi (lihat manifest.json)" % (m["entries_extracted"] - 30))
    L += ["  dilewati: %s (%s)" % (s["path"], s["reason"]) for s in m["skipped"][:5]]
    L += ["  galat: %s" % e for e in m["errors"][:5]]
    return "\n".join(L)


def _init_plugins():
    pf = os.environ.get("REA_PLUGINS", "")
    if pf:
        load_plugins(pf)


_init_plugins()


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--plugins" in argv:
        k = argv.index("--plugins")
        print("plugin:", ", ".join(load_plugins(argv[k + 1])) or "(tidak ada)", file=sys.stderr)
        argv = argv[:k] + argv[k + 2:]
    if "--formats" in argv:
        for f in formats():
            print("%-12s %-10s inspect=%s extract=%s%s  %s" % (f["name"], f["category"], "ya" if f["inspect"] else "-", "ya" if f["extract"] else "-", " [plugin]" if f["plugin"] else "", f["about"]))
    elif "--extract" in argv:
        k = argv.index("--extract")
        out = argv[k + 1] if k + 1 < len(argv) else "rea_assets_out"
        rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        print(extract_text(rest[0], out, rest[1] if len(rest) > 1 else None, convert="--no-convert" not in argv) if rest else "pemakaian: --extract OUTDIR FILE [pola] [--no-convert]")
    elif "--carve" in argv:
        k = argv.index("--carve")
        rest = [x for i, x in enumerate(argv) if i != k and not x.startswith("--")]
        print(_carve_text(carve(rest[0], rest[1] if len(rest) > 1 else None)) if rest else "pemakaian: --carve FILE [OUTDIR]")
    elif "--json" in argv:
        print(json.dumps(describe(next(x for x in argv if not x.startswith("--"))), ensure_ascii=False, indent=1, default=str))
    else:
        a = [x for x in argv if not x.startswith("--")]
        print(describe_text(a[0]) if a else "pemakaian: python rea_assets.py FILE | --extract OUTDIR FILE [pola] | --carve FILE [OUTDIR] | --formats [--plugins DIR]")
