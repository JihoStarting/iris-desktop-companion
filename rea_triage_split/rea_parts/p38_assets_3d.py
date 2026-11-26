# rea_triage bagian 38/47: assets_3d (baris asli 16904-17856). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
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
                polys, cur = [], []
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
    return {"lines": L, "extract": "geometri (triangles / polylist) -> .obj; kurva animasi (sampler / channel) -> animations/*.csv + animations.json"}


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
    try:
        _dae_anim_export(r, out)
    except Exception as e:
        out.errors.append("animasi: %s" % _as_clean(e, 100))


DAE_ANIM_MAX_VALUES = 2_000_000   # total angka kurva animasi yang diekspor per berkas
DAE_ANIM_MAX_CHANNELS = 2000


def _dae_anim_export(r, out) -> None:
    """v99.16: kurva animasi COLLADA (sampler / channel) -> animations/NNN_<target>.csv (satu per channel) + animations/animations.json (semua channel).
    Hanya kunci waktu + nilai mentah (stride 1 = skalar, 16 = matriks 4x4); interpolasi ikut jika ada. Tidak ada evaluasi / retargeting."""
    srcs = {}
    for e in r.iter():
        if _tag(e) != "source" or not e.get("id"):
            continue
        fa = next((x for x in e.iter() if _tag(x) in ("float_array", "Name_array", "IDREF_array")), None)
        if fa is None:
            continue
        ac = next((x for x in e.iter() if _tag(x) == "accessor"), None)
        try:
            st = max(1, int(ac.get("stride", 1))) if ac is not None else 1
        except ValueError:
            st = 1
        srcs[e.get("id")] = (_tag(fa), (fa.text or "").split(), st)
    chans = []
    for an in [e for e in r.iter() if _tag(e) == "animation"]:
        samp = {}
        for sm in [e for e in an if _tag(e) == "sampler"]:
            samp[sm.get("id")] = {i.get("semantic"): (i.get("source") or "")[1:] for i in sm if _tag(i) == "input"}
        for ch in [e for e in an if _tag(e) == "channel"]:
            sid = (ch.get("source") or "")[1:]
            if sid in samp:
                chans.append((ch.get("target") or "?", samp[sid], an.get("name") or an.get("id") or "anim"))
    if not chans:
        return
    total = 0
    js = []
    for i, (target, inp, an_name) in enumerate(chans[:DAE_ANIM_MAX_CHANNELS]):
        try:
            ti, vo = srcs.get(inp.get("INPUT")), srcs.get(inp.get("OUTPUT"))
            if not ti or not vo or ti[0] != "float_array" or vo[0] != "float_array":
                raise ValueError("sampler tanpa INPUT / OUTPUT float_array")
            times = [float(x) for x in ti[1]]
            st = vo[2]
            n = len(times)
            vals = [float(x) for x in vo[1]]
            if n == 0 or len(vals) < n * st:
                raise ValueError("jumlah nilai tidak cocok (%d kunci, stride %d, %d nilai)" % (n, st, len(vals)))
            total += n * (st + 1)
            if total > DAE_ANIM_MAX_VALUES:
                out.errors.append("animasi: batas %d angka tercapai; channel sisanya dilewati" % DAE_ANIM_MAX_VALUES)
                break
            it = srcs.get(inp.get("INTERPOLATION"))
            interp = it[1] if it and it[0] == "Name_array" and len(it[1]) == n else None
            cols = ["time_s"] + (["value"] if st == 1 else ["m%d" % k for k in range(st)] if st == 16 else ["v%d" % k for k in range(st)])
            rows = [("%.6g" % times[k],) + tuple("%.6g" % x for x in vals[k * st:(k + 1) * st]) + ((_as_clean(interp[k], 16),) if interp else ()) for k in range(n)]
            if interp:
                cols.append("interp")
            nm = _obj_name(target.replace("/", "_"), "channel")
            out.write_text("animations/%03d_%s.csv" % (i, nm), _csv_text(rows, cols), "animation", "%d kunci, stride %d" % (n, st))
            js.append({"animation": _as_clean(an_name, 60), "target": _as_clean(target, 120), "stride": st, "times": times[:n],
                       "values": [vals[k * st:(k + 1) * st] for k in range(n)], "interpolation": interp})
        except Exception as e:
            out.errors.append("animasi %s: %s" % (_as_clean(target, 50), _as_clean(e, 100)))
    if js:
        out.write_text("animations/animations.json", json.dumps({"source": "COLLADA", "channels": js}, separators=(",", ":")), "animation", "%d channel" % len(js))


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


