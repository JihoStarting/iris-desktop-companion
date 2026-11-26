# rea_triage bagian 47/47: gamelab_dispatcher (baris asli 24934-25466). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# =========================================================================== #
# Dispatcher gamelab (dulu gamelab.py; kini bagian rea_triage.py)
# =========================================================================== #
_GL_GROUPS = {"pak": main_pak, "re": main_re, "unity": main_unity}
_GL_USAGE = '\nrea_triage.py --gamelab - toolkit game dalam SATU file\n\n  python rea_triage.py --gamelab pak   <subcommand> ...   Unreal pak: Oodle/Zstd + AES-256 (UnrealPak)\n  python rea_triage.py --gamelab re    <binary> <cmd> ... analisis ELF/Mach-O ARM/ARM64\n  python rea_triage.py --gamelab unity <file> <cmd> ...   parser UnityFS / SerializedFile\n\nBantuan per grup:\n  python rea_triage.py --gamelab pak -h\n  python rea_triage.py --gamelab re x.so triage -h\n  python rea_triage.py --gamelab unity bundle -h\n\nDependensi (dimuat hanya saat grupnya dipakai):\n  pak    : tidak ada (butuh UnrealPak.exe dari Unreal Engine)\n  re     : pip install lief capstone\n  unity  : pip install lz4   (opsional: pillow texture2ddecoder UnityPy)\n'


def gamelab_main(argv=None) -> int:
    """Pintu masuk gamelab: gamelab_main(["pak"|"re"|"unity", ...]). CLI: rea_triage.py --gamelab GRUP ..."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(_GL_USAGE)
        return 0
    grp = argv[0]
    if grp not in _GL_GROUPS:
        sys.exit("Grup tidak dikenal: %s. Pilih: %s" % (grp, ", ".join(_GL_GROUPS)))
    _old = sys.argv
    sys.argv = ["rea_triage.py --gamelab " + grp] + argv[1:]
    try:
        _GL_GROUPS[grp]()
    finally:
        sys.argv = _old
    return 0



# ===================================================================================================
# v99.21 [roadmap v2, Tier A: SerializedFile Unity]: parser gamelab dihubungkan ke Asset Explorer, rea_api dan CLI (--unity / --unity-extract).
# Aditif. Dependensi opsional: Pillow (PNG cepat), texture2ddecoder (BC6H/BC7/ETC/ASTC/PVRTC/Crunch). Tanpa keduanya: PNG murni Python untuk
# format tak terkompresi dan DXT1 / DXT5 / BC4 / BC5. Batas: UNITY_MAX_FILE, UNITY_MAX_BLOB, UNITY_MAX_OBJECTS, UNITY_TIME, MAX_PIXELS.
# ===================================================================================================
UNITY_MAX_FILE = 1024 ** 3            # berkas bundle / serialized yang boleh dibaca
UNITY_MAX_BLOB = 1024 ** 3            # total isi bundle setelah dekompresi (disimpan di memori)
UNITY_MAX_OBJECTS = 20000             # objek yang didekode per ekstraksi
UNITY_TIME = 120.0                    # detik, seluruh dekode objek
_UNITY_DEFAULT_TYPES = ("Texture2D", "Mesh", "AnimationClip", "TextAsset")


def _unity_open(path):
    p = str(path)
    if os.path.getsize(p) > UNITY_MAX_FILE:
        raise ValueError("berkas Unity terlalu besar (batas %d MB)" % (UNITY_MAX_FILE >> 20))
    return Container(p)


def _unity_tex_fallback(d, c):
    """Tekstur -> PNG tanpa Pillow: format tak terkompresi + DXT1 / DXT5 / BC4 / BC5 (lewat dekoder DDS milik Asset Explorer)."""
    w, h, fmt = int(d["m_Width"]), int(d["m_Height"]), int(d["m_TextureFormat"])
    if w <= 0 or h <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran tekstur tidak wajar (%dx%d)" % (w, h))
    img = to_bytes(d.get("image data"))
    sd = d.get("m_StreamData") or {}
    if not img and sd.get("size"):
        img = c.resource(sd["path"], sd["offset"], sd["size"])
    if not img:
        raise ValueError("data gambar kosong")
    px = bytearray(w * h * 4)
    if fmt in TEX_UNCOMP:
        bpp = TEX_UNCOMP[fmt]
        img = bytes(img[:w * h * bpp])
        if len(img) < w * h * bpp:
            raise ValueError("data tekstur terpotong")
        for i in range(w * h):
            q = img[i * bpp:(i + 1) * bpp]
            if fmt in (1, 63):
                r_ = g = b = q[0]; a = 255
            elif fmt == 3:
                r_, g, b = q; a = 255
            elif fmt == 4:
                r_, g, b, a = q
            elif fmt == 5:
                a, r_, g, b = q
            elif fmt == 14:
                b, g, r_, a = q
            elif fmt == 62:
                r_ = g = b = q[0]; a = q[1]
            elif fmt == 7:
                v = q[0] | (q[1] << 8)
                r_, g, b, a = (v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31, 255
            else:   # 2 = ARGB4444, 13 = RGBA4444
                v = q[0] | (q[1] << 8)
                n = [(v >> s) & 15 for s in (12, 8, 4, 0)]
                a, r_, g, b = n if fmt == 2 else (n[3], n[0], n[1], n[2])
                r_, g, b, a = r_ * 17, g * 17, b * 17, a * 17
            px[i * 4:i * 4 + 4] = bytes((r_, g, b, a))
    elif fmt in (10, 12, 26, 27):
        fcc = {10: b"DXT1", 12: b"DXT5", 26: b"ATI1", 27: b"ATI2"}[fmt]
        hdr = bytearray(128)
        hdr[0:4] = b"DDS "
        struct.pack_into("<IIII", hdr, 4, 124, 0x1007, h, w)
        struct.pack_into("<II", hdr, 76, 32, 4)
        hdr[84:88] = fcc
        struct.pack_into("<I", hdr, 108, 0x1000)
        w2, h2, px = _dds_decode(bytes(hdr) + bytes(img))
    else:
        raise RuntimeError("TextureFormat %d butuh Pillow + texture2ddecoder (pip install pillow texture2ddecoder)" % fmt)
    stride = w * 4
    flipped = bytearray()
    for y in range(h - 1, -1, -1):   # Unity menyimpan baris dari bawah
        flipped += px[y * stride:(y + 1) * stride]
    return _png_encode(w, h, flipped)


def _unity_texture_png(d, c):
    """-> (bytes PNG, catatan). Pillow bila ada; format yang tidak terjangkau jatuh ke jalur murni Python."""
    w, h = int(d.get("m_Width", 0)), int(d.get("m_Height", 0))
    if w <= 0 or h <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran tekstur tidak wajar (%dx%d)" % (w, h))
    try:
        import io
        from PIL import Image  # noqa: F401
    except ImportError:
        return _unity_tex_fallback(d, c), "PNG murni Python"
    try:
        im = decode_texture(d, c)
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue(), "Pillow"
    except RuntimeError:
        return _unity_tex_fallback(d, c), "PNG murni Python"


def _unity_extract_objects(c, out, types, rx=None, t_budget=UNITY_TIME, flip=True, prefix="unity_objects"):
    """Dekode objek SerializedFile ke `out` (_Out): Texture2D -> .png, Mesh -> .obj, AnimationClip -> .anim.json, TextAsset -> .bytes, lainnya -> .json."""
    import time
    t0 = time.time()
    tos = None
    seen = 0
    done = collections.Counter()
    for sf, o in c.all_objects():
        if time.time() - t0 > t_budget:
            out.errors.append("dekode objek Unity dihentikan: melewati batas waktu %d dtk" % t_budget)
            break
        cn = sf.class_name(o)
        if cn not in types:
            continue
        if seen >= UNITY_MAX_OBJECTS:
            out.errors.append("dekode objek Unity dihentikan: melewati batas %d objek" % UNITY_MAX_OBJECTS)
            break
        name = sf.peek_name(o)
        if rx and not rx.search(name or ""):
            continue
        seen += 1
        base = "%s_%s" % (safe_name(name, cn), o.path_id)
        sub = "%s/%s/" % (prefix, cn)
        try:
            d = sf.read(o)
            name = d.get("m_Name") or name
            base = "%s_%s" % (safe_name(name, cn), o.path_id)
            if cn == "Texture2D":
                png, how = _unity_texture_png(d, c)
                out.write(sub + base + ".png", png, "unity-object", "Texture2D %sx%s format %s (%s)" % (d.get("m_Width"), d.get("m_Height"), d.get("m_TextureFormat"), how))
            elif cn == "Mesh":
                attrs, subs = decode_mesh(d, version_tuple(sf.unity_version))
                out.write_text(sub + base + ".obj", mesh_to_obj(name, attrs, subs, flip), "unity-object", "Mesh -> OBJ")
            elif cn == "AnimationClip":
                if tos is None:
                    tos = avatar_paths(c)
                out.write_text(sub + base + ".anim.json", jdump(decode_animation(d, tos)), "unity-object", "AnimationClip (keyframe mentah + binding)")
            elif cn == "TextAsset":
                out.write(sub + base + ".bytes", d.get("m_Script", "").encode("utf-8", "surrogateescape"), "unity-object", "TextAsset")
            else:
                out.write_text(sub + base + ".json", jdump(d), "unity-object", "%s (dump TypeTree)" % cn)
            done[cn] += 1
        except Exception as e:
            out.errors.append("Unity %s %s: %s" % (cn, _as_clean(base, 50), _as_clean(e, 110)))
    return dict(done)


def unity_info(path) -> dict:
    """Ringkasan bundle / SerializedFile Unity: versi, node, jumlah objek per kelas, TypeTree ada / dibuang. Tidak melempar."""
    try:
        c = _unity_open(path)
        r = {"ok": True, "path": str(path), "kind": "UnityFS" if c.bundle else "SerializedFile", "files": []}
        if c.bundle:
            b = c.bundle
            r["bundle"] = {"format_version": b.version, "player": b.player_version, "revision": b.revision, "compression": b.flags & 0x3F,
                           "size_decompressed": len(b.blob), "nodes": [{"path": n["path"], "size": n["size"], "serialized": bool(n["flags"] & 4)} for n in b.nodes[:500]]}
        for sf in c.files:
            cnt = collections.Counter(sf.class_name(o) for o in sf.objects.values())
            nt = sum(1 for o in sf.objects.values() if o.type and o.type.nodes)
            r["files"].append({"name": sf.name, "serialized_version": sf.version, "unity_version": sf.unity_version, "platform": sf.platform,
                               "objects": len(sf.objects), "classes": dict(cnt.most_common(40)), "typetree": bool(sf.has_typetree and nt),
                               "externals": sf.externals[:20]})
        return r
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _as_clean(e, 160))}


def unity_text(path, max_chars: int = 0) -> str:
    r = unity_info(path)
    if not r.get("ok"):
        return "UNITY gagal: %s" % r.get("error")
    L = ["UNITY %s: %s" % (r["kind"], os.path.basename(str(path)))]
    b = r.get("bundle")
    if b:
        L.append("  UnityFS v%s, player %s, revisi %s, kompresi %s, isi %s byte, %d node" % (b["format_version"], b["player"], b["revision"], b["compression"], b["size_decompressed"], len(b["nodes"])))
    for f in r["files"]:
        L.append("  SerializedFile %s: v%s unity %s, %d objek, TypeTree %s" % (f["name"], f["serialized_version"], f["unity_version"], f["objects"], "ada" if f["typetree"] else "TIDAK ADA (objek tidak bisa didekode; build rilis membuangnya)"))
        L.append("    kelas: " + ", ".join("%s x%d" % kv for kv in f["classes"].items()))
        if f["externals"]:
            L.append("    externals: " + ", ".join(f["externals"]))
    if not r["files"]:
        L.append("  tidak ada SerializedFile di dalamnya (node hanya data mentah / aliran .resS)")
    L.append("Ekstrak objek: --unity-extract OUTDIR FILE [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX]")
    t = "\n".join(L)
    return t if not max_chars or len(t) <= max_chars else t[:max_chars - 30] + "\n[...dipangkas...]"


def unity_extract(path, outdir, types=None, name=None, flip: bool = True) -> dict:
    """Dekode objek Unity ke outdir. Mengembalikan manifest {status, files, errors, ...}. Tidak melempar."""
    try:
        want = {t.strip() for t in (types.split(",") if isinstance(types, str) else (types or _UNITY_DEFAULT_TYPES)) if t.strip()}
        rx = re.compile(name, re.I) if name else None
        out = _Out(outdir)
        c = _unity_open(path)
        done = _unity_extract_objects(c, out, want, rx, flip=flip)
        ok = bool(out.files)
        man = {"status": ("partial" if out.errors or out.skipped else "success") if ok else "error", "format": "Unity", "source": str(path), "outdir": str(out.root),
               "entries_extracted": len(out.files), "entries_skipped": len(out.skipped), "entries_failed": len(out.errors), "by_class": done,
               "files": out.files, "skipped": out.skipped, "errors": out.errors}
        if not ok:
            man["message"] = "tidak ada objek yang berhasil didekode" + (": " + out.errors[0] if out.errors else " (TypeTree dibuang, atau tidak ada kelas yang diminta)")
        try:
            (out.root / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            man["manifest_path"] = str(out.root / "manifest.json")
        except OSError:
            pass
        return man
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 160))}


def _unityfs_objects_note(p):
    """Baris ringkasan isi SerializedFile untuk Asset Explorer (tanpa melempar; dilewati untuk berkas besar)."""
    try:
        if os.path.getsize(str(p)) > 200 * 1024 * 1024:
            return ["Ringkasan objek dilewati (berkas besar): pakai `--unity FILE`."]
        c = _unity_open(p)
        L = []
        for sf in c.files:
            cnt = collections.Counter(sf.class_name(o) for o in sf.objects.values())
            has = any(o.type and o.type.nodes for o in sf.objects.values())
            L.append("SerializedFile %s (v%s, Unity %s): %d objek [%s]%s" % (_as_clean(sf.name, 40), sf.version, _as_clean(sf.unity_version, 20), len(sf.objects),
                                                                          ", ".join("%s x%d" % kv for kv in cnt.most_common(8)), "" if has else "; TypeTree dibuang, objek tidak bisa didekode"))
        if L:
            L.append("Ekstrak (tanpa pola): Texture2D -> .png, Mesh -> .obj, AnimationClip -> .anim.json, TextAsset -> .bytes di unity_objects/. Detail: `--unity FILE`.")
        return L
    except Exception as e:
        return ["Isi SerializedFile tidak bisa diurai: %s" % _as_clean(e, 100)]


def _unityfs_extract(d, p, out, opts):
    _arc_extract_factory(_unityfs)(d, p, out, opts)
    if opts.get("convert", True) and not opts.get("pattern"):   # pola hanya memfilter node; objek didekode bila pola kosong
        try:
            c = _unity_open(p)
            _unity_extract_objects(c, out, set(_UNITY_DEFAULT_TYPES))
        except Exception as e:
            out.errors.append("Unity objek: %s" % _as_clean(e, 120))



if __name__ == "__main__":   # uji manual: python rea_triage.py <file|folder> [--compact] [--json] [--ioc] [--raw] [--yara] [--carve DIR]
    argv = sys.argv[1:]
    cdir = None
    if "--no-cache" in argv:   # satu kali jalan tanpa cache (sama dengan env REA_CACHE=0)
        os.environ["REA_CACHE"] = "0"
        argv = [x for x in argv if x != "--no-cache"]
    if "--cache-info" in argv:
        print(cache_text())
        raise SystemExit(0)
    if "--cache-clear" in argv:
        print("cache dihapus: %d berkas" % cache_clear())
        raise SystemExit(0)
    if "--api" in argv:      # --api '{"action": "triage", "path": "x.exe"}'  (JSON satu baris untuk agen)
        t = argv[argv.index("--api") + 1:]
        print(json.dumps(rea_api(t[0] if t else "{}"), ensure_ascii=False, indent=2, default=str))
        raise SystemExit(0)
    if "--gamelab" in argv:  # --gamelab pak|re|unity ...  (toolkit game: UnrealPak, RE ELF/Mach-O ARM, Unity bundle)
        raise SystemExit(gamelab_main(argv[argv.index("--gamelab") + 1:]))
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
    if "--sigcheck" in argv:   # --sigcheck FILE [--online]  (v99.14: tanda tangan Authenticode penuh)
        t = [x for x in argv[argv.index("--sigcheck") + 1:] if not x.startswith("--")]
        print(sig_text(t[0], online="--online" in argv) if t else "pemakaian: --sigcheck FILE [--online]")
        raise SystemExit(0)
    if "--vt" in argv:       # --vt FILE|SHA256 --online  (v99.14: reputasi hash VirusTotal; env REA_VT_KEY)
        t = [x for x in argv[argv.index("--vt") + 1:] if not x.startswith("--")]
        print(reputation_text(t[0], online="--online" in argv) if t else "pemakaian: --vt FILE|SHA256 --online")
        raise SystemExit(0)
    if "--unpack7z" in argv:   # --unpack7z FILE OUTDIR  (v99.14: NSIS / SFX 7-Zip / 7z lewat alat 7-Zip)
        t = [x for x in argv[argv.index("--unpack7z") + 1:] if not x.startswith("--")]
        print(unpack_7z_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --unpack7z FILE OUTDIR")
        raise SystemExit(0)
    if "--unpack" in argv:   # --unpack FILE OUTDIR
        t = argv[argv.index("--unpack") + 1:]
        print(unpack_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --unpack FILE OUTDIR")
        raise SystemExit(0)
    if "--disasm" in argv:   # --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N]
        t = argv[argv.index("--disasm") + 1:]
        print(disasm_text(t[0], t[1] if len(t) > 1 else "entry", int(t[2], 0) if len(t) > 2 else 40, t[3] if len(t) > 3 else None) if t else "pemakaian: --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N] [ARCH]")
        raise SystemExit(0)
    if "--bin" in argv:      # --bin hex|inspect|search|compare|patch|undo|history|restore ...  (CLI Binary Workbench, dulu rea_binary.py)
        raise SystemExit(_bn_main(argv[argv.index("--bin") + 1:]))
    if "--ex" in argv:       # --ex list|extract|formats ...  (CLI mesin ekstraksi container, dulu rea_extract.py)
        raise SystemExit(_ex_main(argv[argv.index("--ex") + 1:]))
    if "--similar" in argv:  # --similar A B
        t = argv[argv.index("--similar") + 1:]
        print(similar_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --similar A B")
        raise SystemExit(0)
    if "--export" in argv:   # --export FILE ghidra|ida|x64dbg [OUT]  -> skrip anotasi (v99.15)
        t = [x for x in argv[argv.index("--export") + 1:] if not x.startswith("--")]
        print(export_text(t[0], t[1], t[2] if len(t) > 2 else None) if len(t) > 1 else "pemakaian: --export FILE ghidra|ida|x64dbg [OUT]")
        raise SystemExit(0)
    if "--funcdiff" in argv:   # --funcdiff A B  -> diff fungsi antar-dua biner (v99.15)
        t = [x for x in argv[argv.index("--funcdiff") + 1:] if not x.startswith("--")]
        print(func_diff_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --funcdiff A B")
        raise SystemExit(0)
    if "--cfg" in argv:      # --cfg FILE [entry|0xVA]  -> CFG / kompleksitas fungsi (v99.13)
        t = [x for x in argv[argv.index("--cfg") + 1:] if not x.startswith("--")]
        print(cfg_text(t[0], t[1] if len(t) > 1 else None) if t else "pemakaian: --cfg FILE [entry|0xVA]")
        raise SystemExit(0)
    if "--deobf" in argv:    # --deobf FILE [--json] [--raw] [--full]  -> deobfuscation skrip berlapis PowerShell / VBS / JS (v99.20)
        t = [x for x in argv[argv.index("--deobf") + 1:argv.index("--deobf") + 2] if not x.startswith("--")]
        if not t:
            print("pemakaian: --deobf FILE [--json] [--raw] [--full]")
        elif "--json" in argv:
            _f, _sz = _open_regular(t[0])
            with _f:
                _r = deobfuscate(_f.read(DSO_MAX_TEXT * 2))
            print(json.dumps(_r, ensure_ascii=False, indent=2))
        else:
            print(deobf_text(t[0], defang="--raw" not in argv, full="--full" in argv))
        raise SystemExit(0)
    if "--config" in argv:   # --config FILE [--key STR ...] [--json] [--raw]  -> konfigurasi malware tertanam (v99.19)
        i_ = argv.index("--config")
        t = [x for x in argv[i_ + 1:i_ + 2] if not x.startswith("--")]
        ks = [argv[j + 1] for j in range(len(argv) - 1) if argv[j] == "--key"]
        if not t:
            print("pemakaian: --config FILE [--key STR ...] [--json] [--raw]")
        elif "--json" in argv:
            print(json.dumps(extract_config(t[0], keys=ks, reveal="--raw" in argv), ensure_ascii=False, indent=2))
        else:
            print(config_text(t[0], defang="--raw" not in argv, keys=ks))
        raise SystemExit(0)
    if "--emu" in argv:      # --emu FILE [entry|0xVA]  -> emulasi mikro: string / buffer tersembunyi (v99.18)
        t = [x for x in argv[argv.index("--emu") + 1:] if not x.startswith("--")]
        print(emu_text(t[0], t[1] if len(t) > 1 else None, defang="--raw" not in argv) if t else "pemakaian: --emu FILE [entry|0xVA] [--raw]")
        raise SystemExit(0)
    if "--net" in argv:      # --net FILE [--compact] [--raw]  -> tabel metadata .NET + IL (v99.12)
        t = [x for x in argv[argv.index("--net") + 1:] if not x.startswith("--")]
        print(net_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --net FILE [--compact] [--raw]")
        raise SystemExit(0)
    if "--dex" in argv:      # --dex FILE [--compact] [--raw]  -> bytecode Dalvik .dex / APK (v99.11)
        t = [x for x in argv[argv.index("--dex") + 1:] if not x.startswith("--")]
        print(dex_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --dex FILE [--compact] [--raw]")
        raise SystemExit(0)
    if "--html" in argv:     # --html FILE [OUT.html]  -> laporan HTML tunggal offline (v99.7)
        t = argv[argv.index("--html") + 1:]
        print(triage_html_file(t[0], t[1] if len(t) > 1 else None, defang="--raw" not in argv) if t else "pemakaian: --html FILE [OUT.html]")
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
    if "--unzstd" in argv:   # --unzstd FILE [OUT] [--force] [--dict DICT]  -> dekompres Zstandard dengan dekoder murni Python (v99.31; dictionary v99.51)
        _dz = None
        _av = list(argv)
        if "--dict" in _av:
            _k = _av.index("--dict")
            _dz = _av[_k + 1] if _k + 1 < len(_av) else None
            del _av[_k:_k + 2]
        t = [x for x in _av[_av.index("--unzstd") + 1:] if not x.startswith("--")]
        if not t or ("--dict" in argv and not _dz):
            print("pemakaian: --unzstd FILE [OUT] [--force] [--dict DICT]   (tanpa OUT: nama FILE tanpa .zst di folder kerja)")
            raise SystemExit(2)
        _src = Path(t[0])
        _dst = t[1] if len(t) > 1 else (_src.stem if _src.suffix.lower() == ".zst" else _src.name + ".out")
        _r = unzstd(t[0], _dst, force="--force" in argv, dict_path=_dz)
        if "frames" in _r:
            print("Zstandard: %d frame, %s -> %s (%.2f dtk)" % (_r["frames"], _as_human(_r["compressed"]), _as_human(_r["size"]), _r["seconds"]))
            print("sha256: %s" % _r["sha256"])
            if _r.get("out"):
                print("ditulis: %s" % _r["out"])
            if not _r.get("ok"):
                print("GAGAL: %s" % _r.get("error", "?"))
        else:
            print("unzstd gagal: %s" % _r.get("error", "?"))
        raise SystemExit(0 if _r.get("ok") else 1)
    if "--unity" in argv:   # --unity FILE  -> ringkasan bundle / SerializedFile Unity (v99.21)
        t = [x for x in argv[argv.index("--unity") + 1:] if not x.startswith("--")]
        print(unity_text(t[0]) if t else "pemakaian: --unity FILE")
        raise SystemExit(0)
    if "--unity-extract" in argv:   # --unity-extract OUTDIR FILE [--types T1,T2] [--name REGEX] [--no-flip]
        k = argv.index("--unity-extract")
        rest = argv[k + 1:]
        opt = {}
        for key in ("--types", "--name"):
            if key in rest:
                j = rest.index(key)
                opt[key] = rest[j + 1] if j + 1 < len(rest) else None
                del rest[j:j + 2]
        flip_ = "--no-flip" not in rest
        t = [x for x in rest if not x.startswith("--")]
        if len(t) < 2:
            print("pemakaian: --unity-extract OUTDIR FILE [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX] [--no-flip]")
            raise SystemExit(2)
        m = unity_extract(t[1], t[0], types=opt.get("--types"), name=opt.get("--name"), flip=flip_)
        print(json.dumps({k_: v for k_, v in m.items() if k_ not in ("files",)}, ensure_ascii=False, indent=1, default=str))
        raise SystemExit(0 if m.get("status") in ("success", "partial") else 1)
    _adict = None                                         # v99.53: --dict DICT untuk --assets / --assets-extract (.zst / .tar.zst / Unreal pak)
    if ("--assets" in argv or "--assets-extract" in argv) and "--dict" in argv:
        _k = argv.index("--dict")
        _adict = argv[_k + 1] if _k + 1 < len(argv) and not argv[_k + 1].startswith("--") else None
        if _adict is None:
            print("pemakaian: --dict DICT (berkas dictionary Zstd)")
            raise SystemExit(2)
        argv = argv[:_k] + argv[_k + 2:]
    _aeskey, _aesfile = [], []                            # v99.54 / v99.55: --aes [GUID:]KUNCI|BERKAS untuk --assets / --assets-extract (boleh diulang; dipilih lewat GUID pak)
    if ("--assets" in argv or "--assets-extract" in argv) and "--aes" in argv:
        while "--aes" in argv:
            _k = argv.index("--aes")
            _av_ = argv[_k + 1] if _k + 1 < len(argv) and not argv[_k + 1].startswith("--") else None
            if _av_ is None:
                print("pemakaian: --aes [GUID:]KUNCI (hex 64 / base64 / 32 karakter ASCII) atau --aes BERKAS (Crypto.json / teks); boleh diulang")
                raise SystemExit(2)
            (_aesfile if os.path.isfile(_av_) else _aeskey).append(_av_)
            argv = argv[:_k] + argv[_k + 2:]
    _aeskey, _aesfile = (_aeskey or None), (_aesfile or None)
    if "--assets" in argv:   # --assets FILE [--dict DICT] [--aes [GUID:]KUNCI|BERKAS]
        t = [x for x in argv[argv.index("--assets") + 1:] if not x.startswith("--")]
        print(assets_text(t[0], dict_path=_adict, aes_key=_aeskey, aes_file=_aesfile) if t else "pemakaian: --assets FILE [--dict DICT] [--aes [GUID:]KUNCI|BERKAS]")
        raise SystemExit(0)
    if "--assets-extract" in argv:   # --assets-extract OUTDIR FILE [pola] [--no-convert]
        k = argv.index("--assets-extract")
        _out = argv[k + 1] if k + 1 < len(argv) else "rea_assets_out"
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        if not _rest:
            print("pemakaian: --assets-extract OUTDIR FILE [pola] [--no-convert] [--dict DICT] [--aes [GUID:]KUNCI|BERKAS]")
            raise SystemExit(1)
        _m = assets_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, convert="--no-convert" not in argv, dict_path=_adict, aes_key=_aeskey, aes_file=_aesfile)
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
    _cdict = None                                         # v99.52: --dict DICT untuk --list / --extract (.zst / .tar.zst)
    if ("--list" in argv or "--extract" in argv) and "--dict" in argv:
        _k = argv.index("--dict")
        _cdict = argv[_k + 1] if _k + 1 < len(argv) and not argv[_k + 1].startswith("--") else None
        if _cdict is None:
            print("pemakaian: --dict DICT (berkas dictionary Zstd)")
            raise SystemExit(2)
        argv = argv[:_k] + argv[_k + 2:]
    if "--list" in argv:
        _lt = next((x for x in argv if not x.startswith("--")), None)
        if _lt is None:                                   # v99.35: tanpa berkas -> pemakaian (sebelumnya path kosong dibaca sebagai folder kerja)
            print("pemakaian: python rea_triage.py --list <container> [--dict DICT]")
            raise SystemExit(2)
        print(container_text(_lt, dict_path=_cdict))
        raise SystemExit(0)
    if "--extract" in argv:
        k = argv.index("--extract")
        _out = argv[k + 1] if k + 1 < len(argv) and not argv[k + 1].startswith("--") else None
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        if _out is None or not _rest:                     # v99.35: argumen kurang -> pemakaian (sebelumnya IndexError)
            print("pemakaian: python rea_triage.py --extract OUTDIR <container> [pola] [--scan] [--dict DICT]")
            raise SystemExit(2)
        _m = container_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, scan="--scan" in argv, dict_path=_cdict)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s | manifest: %s" % (_m.get("status"), _m.get("entries_extracted"), _m.get("entries_skipped"), _m.get("entries_failed"), _m.get("manifest_path")))
        if _m.get("status") != "success" and _m.get("message"):   # v99.35: alasan kegagalan ikut dicetak
            print("pesan: %s" % _m.get("message"))
        raise SystemExit(0 if _m.get("status") == "success" else 1)
    if "--carve" in argv:
        k = argv.index("--carve")
        cdir = argv[k + 1] if k + 1 < len(argv) else None
        argv = argv[:k] + argv[k + 2:]
    args = [x for x in argv if not x.startswith("--")]
    flags = {x for x in argv if x.startswith("--")}
    if not args:
        print("pemakaian: python rea_triage.py <file|folder> [--compact] [--card] [--json] [--ioc] [--raw (tanpa defang)] [--yara] [--carve DIR] | --config FILE [--key STR] | --deobf FILE [--json] [--full] | --hex FILE [OFFSET [LENGTH]] | --compare A B | --list <container> [--dict DICT] | --extract OUTDIR <container> [pola] [--scan] [--dict DICT] | --similar A B | --md FILE | --html FILE [OUT.html] | --gamelab pak|re|unity ... | --dex FILE [--compact] | --net FILE [--compact] | --cfg FILE [entry|0xVA] | --emu FILE [entry|0xVA] | --export FILE ghidra|ida|x64dbg [OUT] | --funcdiff A B | --ctph FILE | --re FILE | --xref FILE QUERY | --disasm FILE [AT [N [ARCH]]] | --unpack FILE OUTDIR | --unpack7z FILE OUTDIR | --sigcheck FILE [--online] | --vt FILE|SHA256 --online | --yarascan FILE RULES | --unzstd FILE [OUT] [--force] | --unity FILE | --unity-extract OUTDIR FILE [--types T1,T2] [--name REGEX] | --assets FILE [--dict DICT] [--aes [GUID:]KUNCI|BERKAS] | --assets-extract OUTDIR FILE [pola] [--no-convert] [--dict DICT] [--aes [GUID:]KUNCI|BERKAS] | --assets-carve FILE [OUTDIR] | --formats | --plugins FOLDER | --bin CMD ... | --ex CMD ... | --api JSON | --no-cache | --cache-info | --cache-clear")
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
