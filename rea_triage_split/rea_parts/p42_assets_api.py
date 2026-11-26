# rea_triage bagian 42/47: assets_api (baris asli 20763-20990). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
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


def assets_text(path, max_chars: int = 0, dict_path=None, aes_key=None, aes_file=None) -> str:
    """v99: ringkasan ISI berkas non-exe (model 3D, animasi, tekstur, audio, arsip, SQLite ...). Gagal -> pesan, tidak melempar."""
    mod = _assets_mod()
    if mod is None:
        return "Asset Explorer (rea_assets.py) tidak ditemukan di folder yang sama; fitur isi berkas tidak tersedia."
    try:
        zd = _zstd_load_dict(dict_path) if dict_path else None         # v99.53: dictionary Zstd untuk .zst / .tar.zst / Unreal pak
        ak = _aes_resolve(aes_key, aes_file)                           # v99.54: kunci AES-256 untuk Unreal pak terenkripsi (tidak pernah dicetak)
        with _zstd_dict_scope(zd), _aes_key_scope(ak):
            return mod.describe_text(path, max_chars=max_chars)
    except Exception as e:
        return "ASSETS gagal (%s: %s)." % (type(e).__name__, str(e)[:120])


def assets_extract(path, outdir, pattern=None, convert: bool = True, dict_path=None, aes_key=None, aes_file=None) -> dict:
    """v99: keluarkan isi berkas ke outdir (mesh -> .obj, animasi -> .json / .csv, tekstur -> .png, entri arsip, tabel -> .csv). Mengembalikan manifest."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    try:
        zd = _zstd_load_dict(dict_path) if dict_path else None
    except (ValueError, OSError) as e:
        return {"status": "error", "code": "bad_dictionary", "message": "dictionary tidak bisa dibaca: %s" % _as_clean(e, 160)}
    try:
        ak = _aes_resolve(aes_key, aes_file)                           # v99.54
    except (ValueError, OSError) as e:
        return {"status": "error", "code": "bad_aes_key", "message": "kunci AES tidak bisa dibaca: %s" % _as_clean(e, 160)}
    with _zstd_dict_scope(zd), _aes_key_scope(ak):
        return mod.extract(path, outdir, pattern=pattern, convert=convert)


def assets_carve(path, outdir=None) -> dict:
    """v99: cari (dan bila outdir diberikan, potong) berkas yang tertanam di dalam berkas apa pun."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    return mod.carve(path, outdir)


def hex_text(path, offset=0, length: int = 256, encoding: str = "ascii") -> str:
    """Tampilan hex hanya-baca (v96, rea_binary.py). Gagal -> pesan, tidak melempar."""
    rea_binary = _binary_mod()
    r = rea_binary.hex_view(path, offset, length, encoding=encoding)
    return r["text"] if r.get("status") == "success" else "HEX gagal: %s" % r.get("message", r.get("code"))


def compare_text(path_a, path_b) -> str:
    """Ringkasan perbandingan dua berkas / dua folder (v96)."""
    rea_binary = _binary_mod()
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



