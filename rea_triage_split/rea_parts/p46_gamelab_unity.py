# rea_triage bagian 46/47: gamelab_unity (baris asli 24042-24933). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# =========================================================================== #
# GRUP: unity (UnityFS / SerializedFile)
# =========================================================================== #
# --------------------------------------------------------------------------- #
# Konstanta
# --------------------------------------------------------------------------- #
_COMMON_LIST = (
    "AABB AnimationClip AnimationCurve AnimationState Array Base BitField bitset bool char ColorRGBA "
    "Component data deque double dynamic_array FastPropertyName first float Font GameObject "
    "Generic_Mono GradientNEW GUID GUIStyle int list long_long map Matrix4x4f MdFour MonoBehaviour "
    "MonoScript m_ByteSize m_Curve m_EditorClassIdentifier m_EditorHideFlags m_Enabled m_ExtensionPtr "
    "m_GameObject m_Index m_IsArray m_IsStatic m_MetaFlag m_Name m_ObjectHideFlags m_PrefabInternal "
    "m_PrefabParentObject m_Script m_StaticEditorFlags m_Type m_Version Object pair PPtr<Component> "
    "PPtr<GameObject> PPtr<Material> PPtr<MonoBehaviour> PPtr<MonoScript> PPtr<Object> PPtr<Prefab> "
    "PPtr<Sprite> PPtr<TextAsset> PPtr<Texture> PPtr<Texture2D> PPtr<Transform> Prefab Quaternionf "
    "Rectf RectInt RectOffset second set short size SInt16 SInt32 SInt64 SInt8 staticvector string "
    "TextAsset TextMesh Texture Texture2D Transform TypelessData UInt16 UInt32 UInt64 UInt8 "
    "unsigned_int unsigned_long_long unsigned_short vector Vector2f Vector3f Vector4f "
    "m_ScriptingClassIdentifier Gradient Type* int2_storage int3_storage BoundsInt "
    "m_CorrespondingSourceObject m_PrefabInstance m_PrefabAsset FileSize Hash128"
).split()
COMMON = {}
_gl_o = 0
for _s in _COMMON_LIST:
    _s = _s.replace("_", " ") if _s in ("Generic_Mono", "long_long", "unsigned_int",
                                        "unsigned_long_long", "unsigned_short") else _s
    COMMON[_gl_o] = _s
    _gl_o += len(_s) + 1

CLASS_IDS = {
    1: "GameObject", 4: "Transform", 20: "Camera", 21: "Material", 23: "MeshRenderer",
    28: "Texture2D", 33: "MeshFilter", 43: "Mesh", 48: "Shader", 49: "TextAsset",
    74: "AnimationClip", 82: "AudioSource", 83: "AudioClip", 90: "Avatar",
    91: "AnimatorController", 95: "Animator", 111: "Animation", 114: "MonoBehaviour",
    115: "MonoScript", 128: "Font", 137: "SkinnedMeshRenderer", 142: "AssetBundle",
    150: "PreloadData", 198: "ParticleSystem", 213: "Sprite", 224: "RectTransform",
    687078895: "SpriteAtlas",
}

PRIMS = {
    "SInt8": "b", "UInt8": "B", "char": "B", "bool": "?", "short": "h", "SInt16": "h",
    "UInt16": "H", "unsigned short": "H", "int": "i", "SInt32": "i", "UInt32": "I",
    "unsigned int": "I", "Type*": "I", "long long": "q", "SInt64": "q", "UInt64": "Q",
    "unsigned long long": "Q", "FileSize": "Q", "float": "f", "double": "d",
}


# --------------------------------------------------------------------------- #
# Reader biner
# --------------------------------------------------------------------------- #
class Reader:
    def __init__(self, data, endian=">", pos=0):
        self.d = data
        self.e = endian
        self.pos = pos

    def _u(self, fmt, n):
        v = struct.unpack_from(self.e + fmt, self.d, self.pos)[0]
        self.pos += n
        return v

    def u8(self): return self._u("B", 1)
    def i8(self): return self._u("b", 1)
    def u16(self): return self._u("H", 2)
    def i16(self): return self._u("h", 2)
    def u32(self): return self._u("I", 4)
    def i32(self): return self._u("i", 4)
    def u64(self): return self._u("Q", 8)
    def i64(self): return self._u("q", 8)
    def f32(self): return self._u("f", 4)

    def bytes(self, n):
        b = self.d[self.pos:self.pos + n]
        if len(b) != n:
            raise EOFError("data kurang")
        self.pos += n
        return b

    def cstr(self):
        end = self.d.index(b"\x00", self.pos)
        s = self.d[self.pos:end].decode("utf-8", "replace")
        self.pos = end + 1
        return s

    def align(self, n=4):
        self.pos += (-self.pos) % n


# --------------------------------------------------------------------------- #
# Dekompresi
# --------------------------------------------------------------------------- #
def lzma_unity(data, usize):
    props = data[0]
    dict_size = struct.unpack_from("<I", data, 1)[0]
    lc = props % 9
    props //= 9
    lp, pb = props % 5, props // 5
    flt = [{"id": lzma.FILTER_LZMA1, "dict_size": dict_size, "lc": lc, "lp": lp, "pb": pb}]
    return lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=flt).decompress(data[5:], max_length=usize)


def decompress(data, mode, usize):
    # v99.21: memakai _unity_decomp (Asset Explorer): batas ukuran, LZ4 murni Python tanpa paket lz4, tanpa sys.exit di dalam pustaka.
    return _unity_decomp(data, mode, usize)


# --------------------------------------------------------------------------- #
# UnityFS
# --------------------------------------------------------------------------- #
class Bundle:
    def __init__(self, data):
        r = Reader(data, ">")
        self.signature = r.cstr()
        if self.signature != "UnityFS":
            raise ValueError(f"Signature {self.signature!r} tidak didukung (hanya UnityFS)")
        self.version = r.u32()
        self.player_version = r.cstr()
        self.revision = r.cstr()
        self.size = r.i64()
        csize, usize, self.flags = r.u32(), r.u32(), r.u32()
        if self.version >= 7:
            r.align(16)
        if self.flags & 0x80:  # blocks info di akhir file
            save = r.pos
            r.pos = len(data) - csize
            raw = r.bytes(csize)
            r.pos = save
        else:
            raw = r.bytes(csize)
        if csize > 64 * 1024 * 1024 or usize > 64 * 1024 * 1024:
            raise ValueError("blok info UnityFS tidak wajar")
        info = decompress(raw, self.flags & 0x3F, usize)
        if self.flags & 0x200:
            r.align(16)

        ir = Reader(info, ">")
        ir.bytes(16)  # hash
        nb = ir.i32()
        if nb < 0 or nb > MAX_ENTRIES:
            raise ValueError("jumlah blok Unity tidak wajar")
        blocks = [(ir.u32(), ir.u32(), ir.u16()) for _ in range(nb)]
        nn = ir.i32()
        if nn < 0 or nn > MAX_ENTRIES:
            raise ValueError("jumlah node Unity tidak wajar")
        nodes = []
        for _ in range(nn):
            off, sz, fl = ir.i64(), ir.i64(), ir.u32()
            nodes.append((off, sz, fl, ir.cstr()))
        if sum(b[0] for b in blocks) > UNITY_MAX_BLOB:
            raise ValueError("isi bundle Unity terlalu besar untuk dibuka di memori (batas %d MB)" % (UNITY_MAX_BLOB >> 20))

        out = bytearray()
        for u, c, fl in blocks:
            out += decompress(r.bytes(c), fl & 0x3F, u)
        self.blob = bytes(out)
        self.nodes = [dict(path=p, offset=o, size=s, flags=f) for o, s, f, p in nodes]

    def node_data(self, n):
        return self.blob[n["offset"]:n["offset"] + n["size"]]

    def find(self, basename):
        for n in self.nodes:
            if os.path.basename(n["path"]) == basename:
                return n
        return None


# --------------------------------------------------------------------------- #
# TypeTree
# --------------------------------------------------------------------------- #
class TNode:
    __slots__ = ("level", "type", "name", "is_array", "byte_size", "index", "meta", "ref_hash")


def parse_typetree_blob(r, version):
    count = r.i32()
    buf_size = r.i32()
    raw = []
    for _ in range(count):
        r.u16()  # node version
        level, flags = r.u8(), r.u8()
        t_off, n_off = r.u32(), r.u32()
        bsize, idx, meta = r.i32(), r.i32(), r.i32()
        ref = r.u64() if version >= 19 else 0
        raw.append((level, flags, t_off, n_off, bsize, idx, meta, ref))
    buf = r.bytes(buf_size)

    def gs(off):
        if off & 0x80000000:
            return COMMON.get(off & 0x7FFFFFFF, f"?{off & 0x7FFFFFFF}")
        end = buf.index(b"\x00", off)
        return buf[off:end].decode("utf-8", "replace")

    nodes = []
    for level, flags, t_off, n_off, bsize, idx, meta, ref in raw:
        n = TNode()
        n.level, n.is_array = level, bool(flags & 1)
        n.type, n.name = gs(t_off), gs(n_off)
        n.byte_size, n.index, n.meta, n.ref_hash = bsize, idx, meta, ref
        nodes.append(n)
    ends = [len(nodes)] * len(nodes)
    for i, n in enumerate(nodes):
        j = i + 1
        while j < len(nodes) and nodes[j].level > n.level:
            j += 1
        ends[i] = j
    return nodes, ends


def read_value(r, nodes, ends, i):
    """Baca satu node TypeTree (rekursif) menjadi nilai Python."""
    n = nodes[i]
    t = n.type
    e = r.e
    fmt = PRIMS.get(t)
    if fmt:
        sz = struct.calcsize(fmt)
        v = struct.unpack_from(e + fmt, r.d, r.pos)[0]
        r.pos += sz
    elif t == "string":
        ln = r.i32()
        v = r.bytes(ln).decode("utf-8", "surrogateescape")
    elif t == "TypelessData":
        ln = r.i32()
        v = r.bytes(ln)
    elif n.is_array and t == "Array":
        size = r.i32()
        if size < 0 or size > len(r.d):
            raise ValueError("ukuran array TypeTree tidak wajar")
        di = i + 2
        dn = nodes[di]
        pf = PRIMS.get(dn.type)
        if dn.type in ("UInt8", "char", "SInt8") and not (dn.meta & 0x4000):
            v = r.bytes(size)
        elif pf and not (dn.meta & 0x4000):
            sz = struct.calcsize(pf)
            v = list(struct.unpack_from(f"{e}{size}{pf}", r.d, r.pos))
            r.pos += sz * size
        else:
            v = [read_value(r, nodes, ends, di) for _ in range(size)]
    else:
        v = {}
        j = i + 1
        end = ends[i]
        kids = []
        while j < end:
            kids.append(j)
            j = ends[j]
        for k in kids:
            v[nodes[k].name] = read_value(r, nodes, ends, k)
        if len(kids) == 1 and nodes[kids[0]].type == "Array":
            v = v[nodes[kids[0]].name]
    if n.meta & 0x4000:
        r.align(4)
    return v


# --------------------------------------------------------------------------- #
# SerializedFile
# --------------------------------------------------------------------------- #
class TypeInfo:
    pass


class ObjInfo:
    def __init__(self):
        self.path_id = self.byte_start = self.byte_size = self.type_id = self.class_id = 0
        self.type = None


class SerializedFile:
    def __init__(self, data, name="", container=None):
        self.data, self.name, self.container = data, name, container
        r = Reader(data, ">")
        meta_size, file_size, self.version, data_offset = r.u32(), r.u32(), r.u32(), r.u32()
        self.endian = ">"
        if self.version >= 9:
            self.endian = ">" if r.u8() else "<"
            r.bytes(3)
        else:
            raise ValueError("SerializedFile < v9 tidak didukung")
        if self.version >= 22:
            meta_size, file_size, data_offset = r.u32(), r.i64(), r.i64()
            r.i64()
        self.data_offset = data_offset
        r.e = self.endian
        self.unity_version = r.cstr() if self.version >= 7 else ""
        self.platform = r.i32() if self.version >= 8 else 0
        self.has_typetree = bool(r.u8()) if self.version >= 13 else True
        if self.version < 13:
            raise ValueError("SerializedFile < v13 tidak didukung")

        self.types = [self._read_type(r, False) for _ in range(r.i32())]

        big_id = self.version >= 14
        self.objects = {}
        for _ in range(r.i32()):
            o = ObjInfo()
            if big_id:
                r.align(4)
                o.path_id = r.i64()
            else:
                o.path_id = r.i32()
            o.byte_start = r.i64() if self.version >= 22 else r.u32()
            o.byte_size = r.u32()
            o.type_id = r.i32()
            if self.version < 16:
                o.class_id = r.u16()
                o.type = next((t for t in self.types if t.class_id == o.type_id), None)
            else:
                o.type = self.types[o.type_id]
                o.class_id = o.type.class_id
            if self.version < 11:
                r.u16()
            if 11 <= self.version < 17:
                r.i16()
            if 15 <= self.version < 17:
                r.u8()
            self.objects[o.path_id] = o

        if self.version >= 11:
            for _ in range(r.i32()):
                r.i32()
                if self.version < 14:
                    r.i32()
                else:
                    r.align(4)
                    r.i64()
        self.externals = []
        for _ in range(r.i32()):
            if self.version >= 6:
                r.cstr()
            if self.version >= 5:
                r.bytes(16)
            r.i32()
            self.externals.append(r.cstr())
        if self.version >= 20:
            self.ref_types = [self._read_type(r, True) for _ in range(r.i32())]

    def _read_type(self, r, is_ref):
        t = TypeInfo()
        t.class_id = r.i32()
        if self.version >= 16:
            r.u8()  # stripped
        script_idx = r.i16() if self.version >= 17 else -1
        t.nodes = t.ends = None
        if self.version >= 13:
            if (is_ref and script_idx >= 0) or (self.version < 16 and t.class_id < 0) or \
                    (self.version >= 16 and t.class_id == 114):
                r.bytes(16)
            r.bytes(16)
        if self.has_typetree:
            if self.version < 12 and self.version != 10:
                raise ValueError("TypeTree legacy tidak didukung")
            t.nodes, t.ends = parse_typetree_blob(r, self.version)
            if self.version >= 21:
                if is_ref:
                    r.cstr(); r.cstr(); r.cstr()
                else:
                    for _ in range(r.i32()):
                        r.i32()
        return t

    # ---- akses object ----
    def class_name(self, o):
        if o.type and o.type.nodes:
            return o.type.nodes[0].type
        return CLASS_IDS.get(o.class_id, f"Class{o.class_id}")

    def read(self, o):
        """Baca object -> dict. Fallback ke UnityPy jika TypeTree tidak ada."""
        if o.type and o.type.nodes:
            r = Reader(self.data, self.endian, self.data_offset + o.byte_start)
            return read_value(r, o.type.nodes, o.type.ends, 0)
        if self.container and self.container.fallback:
            d = self.container.unitypy_tree(self, o)
            if d is not None:
                return d
        raise RuntimeError(f"TypeTree tidak ada untuk {self.class_name(o)} (path_id={o.path_id}); "
                           f"coba --fallback (butuh UnityPy)")

    def peek_name(self, o):
        if not (o.type and o.type.nodes):
            return ""
        try:
            nodes, ends = o.type.nodes, o.type.ends
            r = Reader(self.data, self.endian, self.data_offset + o.byte_start)
            j, end = 1, ends[0]
            while j < end:
                if nodes[j].name == "m_Name":
                    return read_value(r, nodes, ends, j)
                read_value(r, nodes, ends, j)
                j = ends[j]
        except Exception:
            pass
        return ""


# --------------------------------------------------------------------------- #
# Container: bundle atau file serialized tunggal
# --------------------------------------------------------------------------- #
class Container:
    def __init__(self, path, fallback=False):
        self.path = path
        self.fallback = fallback
        self._up = None
        with open(path, "rb") as f:
            data = f.read()
        self.bundle = None
        self.files = []
        if data[:7] == b"UnityFS":
            self.bundle = Bundle(data)
            for n in self.bundle.nodes:
                if n["flags"] & 4:
                    sf = SerializedFile(self.bundle.node_data(n), os.path.basename(n["path"]), self)
                    self.files.append(sf)
        elif data[:5] in (b"Unity", b"Unity") and data[:8] != b"UnityFS\x00":
            raise ValueError("Format UnityWeb/UnityRaw/UnityArchive tidak didukung")
        else:
            self.files.append(SerializedFile(data, os.path.basename(path), self))

    def resource(self, stream_path, offset, size):
        base = os.path.basename(stream_path)
        if self.bundle:
            n = self.bundle.find(base)
            if n:
                return self.bundle.node_data(n)[offset:offset + size]
        p = os.path.join(os.path.dirname(os.path.abspath(self.path)), base)
        if os.path.exists(p):
            with open(p, "rb") as f:
                f.seek(offset)
                return f.read(size)
        raise FileNotFoundError(f"Resource {stream_path} tidak ditemukan")

    def unitypy_tree(self, sf, o):
        try:
            import UnityPy
        except ImportError:
            return None
        if self._up is None:
            self._up = UnityPy.load(self.path)
        for ob in self._up.objects:
            if ob.path_id == o.path_id and getattr(ob.assets_file, "name", "") in (sf.name, ""):
                try:
                    return ob.read_typetree()
                except Exception:
                    return None
        return None

    def all_objects(self):
        for sf in self.files:
            for o in sf.objects.values():
                yield sf, o


def to_bytes(x):
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, list):
        return bytes(x)
    return b""


def safe_name(s, fallback):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s or "").strip()
    return s or fallback


# --------------------------------------------------------------------------- #
# Texture2D
# --------------------------------------------------------------------------- #
ASTC = {48: (4, 4), 49: (5, 5), 50: (6, 6), 51: (8, 8), 52: (10, 10), 53: (12, 12),
        54: (4, 4), 55: (5, 5), 56: (6, 6), 57: (8, 8), 58: (10, 10), 59: (12, 12)}
TEX_BLOCK8 = {10: "bc1", 26: "bc4", 34: "etc1", 45: "etc2", 41: "eac_r", 42: "eac_r_signed"}
TEX_BLOCK16 = {12: "bc3", 27: "bc5", 25: "bc7", 24: "bc6h", 47: "etc2a8", 43: "eac_rg",
               44: "eac_rg_signed"}
TEX_UNCOMP = {1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 7: 2, 13: 2, 14: 4, 62: 2, 63: 1}


def decode_texture(d, container):
    w, h, fmt = d["m_Width"], d["m_Height"], d["m_TextureFormat"]
    img = to_bytes(d.get("image data"))
    sd = d.get("m_StreamData") or {}
    if not img and sd.get("size"):
        img = container.resource(sd["path"], sd["offset"], sd["size"])
    if not img:
        raise ValueError("data gambar kosong")
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Butuh Pillow: pip install pillow")

    if fmt in TEX_UNCOMP:
        img = img[:w * h * TEX_UNCOMP[fmt]]
        if fmt == 1 or fmt == 63:
            im = Image.frombytes("L", (w, h), img)
        elif fmt == 3:
            im = Image.frombytes("RGB", (w, h), img, "raw", "RGB")
        elif fmt == 4:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "RGBA")
        elif fmt == 5:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "ARGB")
        elif fmt == 14:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "BGRA")
        elif fmt == 7:
            px = struct.unpack(f"<{w * h}H", img)
            out = bytearray()
            for p in px:
                out += bytes(((p >> 11) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31))
            im = Image.frombytes("RGB", (w, h), bytes(out))
        elif fmt in (2, 13):
            px = struct.unpack(f"<{w * h}H", img)
            out = bytearray()
            for p in px:
                n = [(p >> s) & 15 for s in (12, 8, 4, 0)]
                a, r_, g, b = n if fmt == 2 else (n[3], n[0], n[1], n[2])
                out += bytes((r_ * 17, g * 17, b * 17, a * 17))
            im = Image.frombytes("RGBA", (w, h), bytes(out))
        elif fmt == 62:
            im = Image.frombytes("LA", (w, h), img)
        return im.transpose(Image.FLIP_TOP_BOTTOM)

    try:
        import texture2ddecoder as t2d
    except ImportError:
        raise RuntimeError("Format terkompresi butuh: pip install texture2ddecoder")
    if fmt in (28, 29, 64, 65):
        if not hasattr(t2d, "unpack_crunch"):
            raise RuntimeError("Crunch tidak didukung versi texture2ddecoder ini")
        raw = t2d.unpack_crunch(img)
        fmt = {28: 10, 29: 12, 64: 34, 65: 47}[fmt]
        img = raw
    if fmt in TEX_BLOCK8:
        img = img[:((w + 3) // 4) * ((h + 3) // 4) * 8]
        bgra = getattr(t2d, "decode_" + TEX_BLOCK8[fmt])(img, w, h)
    elif fmt in TEX_BLOCK16:
        img = img[:((w + 3) // 4) * ((h + 3) // 4) * 16]
        bgra = getattr(t2d, "decode_" + TEX_BLOCK16[fmt])(img, w, h)
    elif fmt in ASTC:
        bw, bh = ASTC[fmt]
        img = img[:((w + bw - 1) // bw) * ((h + bh - 1) // bh) * 16]
        bgra = t2d.decode_astc(img, w, h, bw, bh)
    elif fmt in (30, 31, 32, 33):
        bgra = t2d.decode_pvrtc(img, w, h, fmt in (30, 31))
    else:
        raise RuntimeError(f"TextureFormat {fmt} belum didukung")
    im = Image.frombytes("RGBA", (w, h), bytes(bgra), "raw", "BGRA")
    return im.transpose(Image.FLIP_TOP_BOTTOM)


# --------------------------------------------------------------------------- #
# Mesh
# --------------------------------------------------------------------------- #
# format channel (Unity 2019+): (ukuran, kode struct, pembagi normalisasi)
FMT_NEW = {0: (4, "f", 0), 1: (2, "e", 0), 2: (1, "B", 255.0), 3: (1, "b", 127.0),
           4: (2, "H", 65535.0), 5: (2, "h", 32767.0), 6: (1, "B", 0), 7: (1, "b", 0),
           8: (2, "H", 0), 9: (2, "h", 0), 10: (4, "I", 0), 11: (4, "i", 0)}
FMT_OLD = {0: (4, "f", 0), 1: (2, "e", 0), 2: (1, "B", 255.0), 3: (1, "B", 0), 4: (4, "i", 0)}


def version_tuple(s):
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def decode_mesh(d, uver):
    if d.get("m_MeshCompression", 0):
        raise RuntimeError("Mesh terkompresi belum didukung")
    vd = d.get("m_VertexData")
    if not vd or "m_Channels" not in vd:
        raise RuntimeError("Layout mesh pra-2017 belum didukung")
    count = vd["m_VertexCount"]
    chans = vd["m_Channels"]
    vdata = to_bytes(vd.get("m_DataSize"))
    new = uver >= (2018, 0, 0)
    fmts = FMT_NEW if uver >= (2017, 4, 0) else FMT_OLD
    names = {0: "pos", 1: "normal", 2: "tangent", 3: "color", 4: "uv0", 5: "uv1", 6: "uv2", 7: "uv3",
             8: "uv4", 9: "uv5", 10: "uv6", 11: "uv7", 12: "weights", 13: "bones"} if new else \
        {0: "pos", 1: "normal", 2: "color", 3: "uv0", 4: "uv1", 5: "tangent"}

    # stride & offset tiap stream
    streams = {}
    for c in chans:
        dim = c["dimension"] & 0xF
        if dim:
            streams.setdefault(c["stream"], []).append((c, dim))
    stride, soff, off = {}, {}, 0
    for s in sorted(streams):
        stride[s] = sum(dim * fmts[c["format"]][0] for c, dim in streams[s])
        soff[s] = off
        off += stride[s] * count
        off += (-off) % 16

    out = {}
    for ci, c in enumerate(chans):
        dim = c["dimension"] & 0xF
        if not dim:
            continue
        size, code, norm = fmts[c["format"]]
        fmtstr = "<" + code * dim
        base = soff[c["stream"]] + c["offset"]
        st = stride[c["stream"]]
        rows = []
        for v in range(count):
            vals = struct.unpack_from(fmtstr, vdata, base + v * st)
            if norm:
                vals = tuple(max(x / norm, -1.0) for x in vals)
            rows.append(vals)
        out[names.get(ci, f"ch{ci}")] = rows

    ib = to_bytes(d.get("m_IndexBuffer"))
    use32 = d.get("m_IndexFormat", 0 if d.get("m_Use16BitIndices", 1) else 1) == 1
    isz = 4 if use32 else 2
    idx = struct.unpack(f"<{len(ib) // isz}{'I' if use32 else 'H'}", ib[:len(ib) // isz * isz])

    subs = []
    for sm in d.get("m_SubMeshes", []):
        first = sm["firstByte"] // isz
        seg = idx[first:first + sm["indexCount"]]
        base = sm.get("baseVertex", 0)
        topo = sm.get("topology", 0)
        tris = []
        if topo == 0:
            tris = [(seg[i] + base, seg[i + 1] + base, seg[i + 2] + base)
                    for i in range(0, len(seg) - 2, 3)]
        elif topo == 1:
            for i in range(len(seg) - 2):
                a, b, c = seg[i], seg[i + 1], seg[i + 2]
                if a == b or b == c or a == c:
                    continue
                tris.append((a + base, b + base, c + base) if i % 2 == 0 else (a + base, c + base, b + base))
        elif topo == 2:
            for i in range(0, len(seg) - 3, 4):
                a, b, c, e = (x + base for x in seg[i:i + 4])
                tris += [(a, b, c), (a, c, e)]
        subs.append(tris)
    return out, subs


def mesh_to_obj(name, attrs, subs, flip=True):
    L = [f"# exported by unity_parser.py", f"o {name}"]
    sx = -1.0 if flip else 1.0
    for p in attrs.get("pos", []):
        L.append(f"v {sx * p[0]:.6f} {p[1]:.6f} {p[2]:.6f}")
    for uv in attrs.get("uv0", []):
        L.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")
    for n in attrs.get("normal", []):
        L.append(f"vn {sx * n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
    has_uv, has_n = "uv0" in attrs, "normal" in attrs
    for si, tris in enumerate(subs):
        L.append(f"g submesh_{si}")
        for a, b, c in tris:
            if flip:
                b, c = c, b
            def ref(i):
                i += 1
                if has_uv and has_n:
                    return f"{i}/{i}/{i}"
                if has_uv:
                    return f"{i}/{i}"
                if has_n:
                    return f"{i}//{i}"
                return str(i)
            L.append(f"f {ref(a)} {ref(b)} {ref(c)}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# AnimationClip
# --------------------------------------------------------------------------- #
ATTR_TRANSFORM = {1: "position", 2: "rotation", 3: "scale", 4: "euler"}


def curve_keys(c):
    return [[k.get("time"), k.get("value"), k.get("inSlope"), k.get("outSlope")]
            for k in (c.get("m_Curve") or [])]


def avatar_paths(container):
    m = {}
    for sf, o in container.all_objects():
        if sf.class_name(o) == "Avatar":
            try:
                for pair in sf.read(o).get("m_TOS", []):
                    m[pair["first"]] = pair["second"]
            except Exception:
                pass
    return m


def decode_animation(d, tos):
    res = {"name": d.get("m_Name"), "sample_rate": d.get("m_SampleRate"),
           "legacy": d.get("m_Legacy"), "wrap_mode": d.get("m_WrapMode")}
    legacy = {}
    for key in ("m_RotationCurves", "m_PositionCurves", "m_ScaleCurves", "m_EulerCurves"):
        if d.get(key):
            legacy[key[2:-6].lower()] = [{"path": c.get("path"), "keys": curve_keys(c.get("curve", {}))}
                                         for c in d[key]]
    if d.get("m_FloatCurves"):
        legacy["float"] = [{"path": c.get("path"), "attribute": c.get("attribute"),
                            "class_id": c.get("classID"), "keys": curve_keys(c.get("curve", {}))}
                           for c in d["m_FloatCurves"]]
    if legacy:
        res["legacy_curves"] = legacy

    mc = d.get("m_MuscleClip")
    if mc:
        clip = mc.get("m_Clip", {})
        res["stop_time"] = mc.get("m_StopTime")
        binds = (d.get("m_ClipBindingConstant") or clip.get("m_Binding") or {}).get("genericBindings", [])
        labels, last, comp = [], None, 0
        for b in binds:
            key = (b.get("path"), b.get("attribute"), b.get("typeID"))
            comp = comp + 1 if key == last else 0
            last = key
            path = tos.get(b.get("path"), f"#{b.get('path')}")
            if b.get("typeID") == 4:
                an = ATTR_TRANSFORM.get(b.get("attribute"), f"attr{b.get('attribute')}")
                labels.append(f"{path}:{an}.{'xyzw'[comp % 4]}")
            else:
                labels.append(f"{path}:type{b.get('typeID')}/attr{b.get('attribute')}#{comp}")
        res["bindings"] = labels

        sc = clip.get("m_StreamedClip", {})
        data = sc.get("data") or []
        streamed = []
        if data:
            buf = struct.pack(f"<{len(data)}I", *data)
            pos = 0
            while pos + 8 <= len(buf):
                t, n = struct.unpack_from("<fi", buf, pos)
                pos += 8
                if math.isinf(t) or n < 0 or pos + n * 20 > len(buf):
                    break
                for _ in range(n):
                    idx, c0, c1, c2, c3 = struct.unpack_from("<i4f", buf, pos)
                    pos += 20
                    streamed.append({"time": t, "curve": idx,
                                     "label": labels[idx] if 0 <= idx < len(labels) else None,
                                     "value": c3, "out_slope": c2})
        res["streamed_keys"] = streamed
        sc_count = sc.get("curveCount", 0)

        dc = clip.get("m_DenseClip", {})
        if dc.get("m_CurveCount"):
            arr, cc = dc.get("m_SampleArray", []), dc["m_CurveCount"]
            res["dense"] = {"frames": dc.get("m_FrameCount"), "sample_rate": dc.get("m_SampleRate"),
                            "begin_time": dc.get("m_BeginTime"),
                            "curves": [{"curve": sc_count + k,
                                        "label": labels[sc_count + k] if sc_count + k < len(labels) else None,
                                        "samples": arr[k::cc]} for k in range(cc)]}
        cst = clip.get("m_ConstantClip", {}).get("data", [])
        if cst:
            base = sc_count + dc.get("m_CurveCount", 0)
            res["constant"] = [{"curve": base + k,
                                "label": labels[base + k] if base + k < len(labels) else None,
                                "value": v} for k, v in enumerate(cst)]
    return res


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def jdump(x, **kw):
    def default(o):
        if isinstance(o, (bytes, bytearray)):
            return f"<bytes {len(o)}>"
        return str(o)
    return json.dumps(x, indent=2, default=default, **kw)


def cmd_info(c, a):
    if c.bundle:
        b = c.bundle
        print(f"UnityFS v{b.version}  player={b.player_version}  revision={b.revision}")
        print(f"flags=0x{b.flags:x} compression={b.flags & 0x3F}  decompressed={len(b.blob)} bytes")
        for n in b.nodes:
            print(f"  node {n['path']:<48} size={n['size']:>10} flags={n['flags']}")
    for sf in c.files:
        print(f"\nSerializedFile {sf.name}: v{sf.version} unity={sf.unity_version} "
              f"platform={sf.platform} typetree={sf.has_typetree} objects={len(sf.objects)}")
        counts = {}
        for o in sf.objects.values():
            k = sf.class_name(o)
            counts[k] = counts.get(k, 0) + 1
        for k, v in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {k:<24} {v}")
        if sf.externals:
            print("  externals:", ", ".join(sf.externals))


def cmd_ls(c, a):
    for sf, o in c.all_objects():
        cn = sf.class_name(o)
        if a.type and cn != a.type:
            continue
        print(f"{sf.name[:20]:<20} {o.path_id:>20} {cn:<20} {o.byte_size:>10}  {sf.peek_name(o)}")


def cmd_dump(c, a):
    for sf, o in c.all_objects():
        if o.path_id == a.id:
            print(jdump(sf.read(o)))
            return
    sys.exit("path_id tidak ditemukan")


def cmd_unpack(c, a):
    if not c.bundle:
        sys.exit("Bukan bundle")
    os.makedirs(a.out, exist_ok=True)
    for n in c.bundle.nodes:
        p = os.path.join(a.out, safe_name(os.path.basename(n["path"]), "node"))
        with open(p, "wb") as f:
            f.write(c.bundle.node_data(n))
        print(p)


def cmd_extract(c, a):
    want = {t.strip() for t in a.types.split(",")}
    rx = re.compile(a.name, re.I) if a.name else None
    os.makedirs(a.out, exist_ok=True)
    tos = None
    n_ok = n_fail = 0
    for sf, o in c.all_objects():
        cn = sf.class_name(o)
        if cn not in want:
            continue
        name = sf.peek_name(o)
        if rx and not rx.search(name or ""):
            continue
        base = f"{safe_name(name, cn)}_{o.path_id}"
        try:
            d = sf.read(o)
            name = d.get("m_Name") or name
            base = f"{safe_name(name, cn)}_{o.path_id}"
            if cn == "Texture2D":
                p = os.path.join(a.out, base + ".png")
                decode_texture(d, c).save(p)
            elif cn == "Mesh":
                attrs, subs = decode_mesh(d, version_tuple(sf.unity_version))
                p = os.path.join(a.out, base + ".obj")
                with open(p, "w") as f:
                    f.write(mesh_to_obj(name, attrs, subs, not a.no_flip))
            elif cn == "AnimationClip":
                if tos is None:
                    tos = avatar_paths(c)
                p = os.path.join(a.out, base + ".anim.json")
                with open(p, "w") as f:
                    f.write(jdump(decode_animation(d, tos)))
            elif cn == "TextAsset":
                p = os.path.join(a.out, base + ".bytes")
                with open(p, "wb") as f:
                    f.write(d.get("m_Script", "").encode("utf-8", "surrogateescape"))
            else:
                p = os.path.join(a.out, base + ".json")
                with open(p, "w") as f:
                    f.write(jdump(d))
            print(f"[ok]   {cn:<14} {p}")
            n_ok += 1
        except Exception as e:
            print(f"[gagal] {cn:<14} {base}: {e}", file=sys.stderr)
            n_fail += 1
    print(f"selesai: {n_ok} ok, {n_fail} gagal", file=sys.stderr)


def main_unity():
    p = argparse.ArgumentParser(description="Parser Unity bundle/SerializedFile",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=UNITY_DOC)
    p.add_argument("file")
    p.add_argument("--fallback", action="store_true", help="pakai UnityPy bila TypeTree tidak ada")
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("info").set_defaults(fn=cmd_info)
    s = sp.add_parser("ls"); s.set_defaults(fn=cmd_ls); s.add_argument("--type")
    s = sp.add_parser("dump"); s.set_defaults(fn=cmd_dump); s.add_argument("--id", type=int, required=True)
    s = sp.add_parser("unpack"); s.set_defaults(fn=cmd_unpack); s.add_argument("-o", "--out", required=True)
    s = sp.add_parser("extract"); s.set_defaults(fn=cmd_extract)
    s.add_argument("-o", "--out", required=True)
    s.add_argument("--types", default="Texture2D,Mesh,AnimationClip,TextAsset")
    s.add_argument("--name"); s.add_argument("--no-flip", action="store_true")
    a = p.parse_args()
    c = Container(a.file, a.fallback)
    a.fn(c, a)




# =========================================================================== #
# Dispatcher
# =========================================================================== #


