# rea_triage bagian 29/47: dotnet_il (baris asli 11917-12605). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.12 [S1b]: tabel metadata .NET (#~) + pemindaian IL ----------------------------------
# Mengurai stream `#~` (ECMA-335): TypeDef / MethodDef / MemberRef / TypeRef / ImplMap (P/Invoke) / ModuleRef / AssemblyRef /
# ManifestResource, lalu memindai badan IL tiap metode (opcode call / callvirt / newobj / ldftn) untuk memetakan siapa memanggil
# siapa: metode internal, API .NET sensitif (Process.Start, Assembly.Load, WebClient, Convert.FromBase64String ...), dan P/Invoke
# (dll!fungsi). Statis murni: tidak ada kode yang dijalankan; hanya pustaka standar. Hasil adalah PETUNJUK: pemanggilan lewat
# refleksi / delegate dinamis / IL terenkripsi (obfuskator) tidak terlihat, dan IL yang tidak valid menghentikan pemindaian
# metode itu saja. Kunci baru rep["dotnet_il"]; triase lama tidak berubah.

NETIL_TIME = 4.0                 # detik untuk seluruh analisis IL satu berkas; sisanya dilaporkan sebagai terpotong
NETIL_MAX_METHODS = 80_000       # metode berbadan yang dipindai
NETIL_MAX_BODY = 1 << 20         # satu badan IL lebih panjang dari ini dilewati
NETIL_MAX_BYTES = 64 << 20       # total byte IL yang dipindai
NETIL_MAX_ROWS = 1_000_000       # baris per tabel; lebih dari ini dianggap metadata rusak / dibuat-buat
NETIL_MAX_CALLS = 60             # pemanggilan sensitif yang dilaporkan

_NT_CODED = {   # nama: (jumlah bit tag, tabel per tag); -1 = tag tidak dipakai
    "ResolutionScope": (2, (0, 26, 35, 1)),
    "TypeDefOrRef": (2, (2, 1, 27)),
    "MemberRefParent": (3, (2, 1, 26, 6, 27)),
    "HasConstant": (2, (4, 8, 23)),
    "HasCustomAttribute": (5, (6, 4, 1, 2, 8, 9, 10, 0, 14, 23, 20, 17, 26, 27, 32, 35, 38, 39, 40, 42, 44, 43)),
    "CustomAttributeType": (3, (-1, -1, 6, 10, -1)),
    "HasFieldMarshal": (1, (4, 8)),
    "HasDeclSecurity": (2, (2, 6, 32)),
    "HasSemantics": (1, (20, 23)),
    "MethodDefOrRef": (1, (6, 10)),
    "MemberForwarded": (1, (4, 6)),
    "Implementation": (2, (38, 35, 39)),
    "TypeOrMethodDef": (1, (2, 6)),
}
# skema kolom per tabel: int = byte tetap; "S" / "G" / "B" = indeks heap #Strings / #GUID / #Blob; ("T", n) = indeks ke tabel n;
# ("C", nama) = indeks berkode
_NT_SCHEMA = {
    0: (2, "S", "G", "G", "G"), 1: (("C", "ResolutionScope"), "S", "S"), 2: (4, "S", "S", ("C", "TypeDefOrRef"), ("T", 4), ("T", 6)),
    3: (("T", 4),), 4: (2, "S", "B"), 5: (("T", 6),), 6: (4, 2, 2, "S", "B", ("T", 8)), 7: (("T", 8),), 8: (2, 2, "S"),
    9: (("T", 2), ("C", "TypeDefOrRef")), 10: (("C", "MemberRefParent"), "S", "B"), 11: (2, ("C", "HasConstant"), "B"),
    12: (("C", "HasCustomAttribute"), ("C", "CustomAttributeType"), "B"), 13: (("C", "HasFieldMarshal"), "B"),
    14: (2, ("C", "HasDeclSecurity"), "B"), 15: (2, 4, ("T", 2)), 16: (4, ("T", 4)), 17: ("B",), 18: (("T", 2), ("T", 20)),
    19: (("T", 20),), 20: (2, "S", ("C", "TypeDefOrRef")), 21: (("T", 2), ("T", 23)), 22: (("T", 23),), 23: (2, "S", "B"),
    24: (2, ("T", 6), ("C", "HasSemantics")), 25: (("T", 2), ("C", "MethodDefOrRef"), ("C", "MethodDefOrRef")), 26: ("S",),
    27: ("B",), 28: (2, ("C", "MemberForwarded"), "S", ("T", 26)), 29: (4, ("T", 4)), 30: (4, 4), 31: (4,),
    32: (4, 2, 2, 2, 2, 4, "B", "S", "S"), 33: (4,), 34: (4, 4, 4), 35: (2, 2, 2, 2, 4, "B", "S", "S", "B"), 36: (4, ("T", 35)),
    37: (4, 4, 4, ("T", 35)), 38: (4, "S", "B"), 39: (4, 4, "S", "S", ("C", "Implementation")),
    40: (4, 4, "S", ("C", "Implementation")), 41: (("T", 2), ("T", 2)), 42: (2, 2, ("C", "TypeOrMethodDef"), "S"),
    43: (("C", "MethodDefOrRef"), "B"), 44: (("T", 42), ("C", "TypeDefOrRef")),
}

# ukuran operand opcode CIL: -1 = opcode tidak valid; -2 = switch
_IL1 = [-1] * 256
_IL2: dict = {}
for _o in range(0x00, 0x0E):
    _IL1[_o] = 0
for _o in (0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x1F):
    _IL1[_o] = 1
for _o in (0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x25, 0x26, 0x2A):
    _IL1[_o] = 0
for _o in (0x20, 0x22, 0x27, 0x28, 0x29):
    _IL1[_o] = 4
_IL1[0x21] = _IL1[0x23] = 8
for _o in range(0x2B, 0x38):
    _IL1[_o] = 1
for _o in range(0x38, 0x45):
    _IL1[_o] = 4
_IL1[0x45] = -2
for _o in range(0x46, 0x6F):
    _IL1[_o] = 0
for _o in (0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x79, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x8C, 0x8D, 0x8F, 0xA3, 0xA4, 0xA5,
           0xC2, 0xC6, 0xD0, 0xDD):
    _IL1[_o] = 4
for _o in (0x76, 0x7A, 0x8E, 0xC3, 0xDC, 0xDF, 0xE0):
    _IL1[_o] = 0
for _o in range(0x82, 0x8C):
    _IL1[_o] = 0
for _o in range(0x90, 0xA3):
    _IL1[_o] = 0
for _o in range(0xB3, 0xBB):
    _IL1[_o] = 0
for _o in range(0xD1, 0xDC):
    _IL1[_o] = 0
_IL1[0xDE] = 1
for _o, _s in ((0x00, 0), (0x01, 0), (0x02, 0), (0x03, 0), (0x04, 0), (0x05, 0), (0x06, 4), (0x07, 4), (0x09, 2), (0x0A, 2), (0x0B, 2),
               (0x0C, 2), (0x0D, 2), (0x0E, 2), (0x0F, 0), (0x11, 0), (0x12, 1), (0x13, 0), (0x14, 0), (0x15, 4), (0x16, 4), (0x17, 0),
               (0x18, 0), (0x19, 1), (0x1A, 0), (0x1C, 4), (0x1D, 0), (0x1E, 0)):
    _IL2[_o] = _s

# (grup, tipe lengkap, metode | None = semua metode tipe itu); nama grup sejalan dengan _NET_CAPS
_NETIL_API = (
    ("eksekusi proses / shell", "System.Diagnostics.Process", ("Start",)),
    ("muat kode dinamis", "System.Reflection.Assembly", ("Load", "LoadFrom", "LoadFile", "UnsafeLoadFrom", "ReflectionOnlyLoad")),
    ("muat kode dinamis", "System.AppDomain", ("Load",)),
    ("muat kode dinamis", "System.Reflection.MethodBase", ("Invoke",)),
    ("muat kode dinamis", "System.Reflection.MethodInfo", ("Invoke",)),
    ("muat kode dinamis", "System.Activator", ("CreateInstance",)),
    ("muat kode dinamis", "System.Runtime.InteropServices.Marshal", ("GetDelegateForFunctionPointer", "GetFunctionPointerForDelegate")),
    ("muat kode dinamis", "System.Reflection.Emit.AssemblyBuilder", None),
    ("muat kode dinamis", "System.Reflection.Emit.ILGenerator", None),
    ("jaringan", "System.Net.WebClient", ("DownloadString", "DownloadData", "DownloadFile", "UploadData", "UploadString", "UploadFile", "OpenRead")),
    ("jaringan", "System.Net.Http.HttpClient", ("GetAsync", "PostAsync", "GetStringAsync", "GetByteArrayAsync", "GetStreamAsync", "SendAsync")),
    ("jaringan", "System.Net.WebRequest", ("Create", "GetResponse")),
    ("jaringan", "System.Net.HttpWebRequest", ("GetResponse", "GetRequestStream")),
    ("jaringan", "System.Net.Sockets.TcpClient", (".ctor", "Connect", "ConnectAsync")),
    ("jaringan", "System.Net.Sockets.Socket", ("Connect", "ConnectAsync")),
    ("dekode / kripto", "System.Convert", ("FromBase64String",)),
    ("dekode / kripto", "System.IO.Compression.GZipStream", (".ctor",)),
    ("dekode / kripto", "System.IO.Compression.DeflateStream", (".ctor",)),
    ("dekode / kripto", "System.Security.Cryptography.ICryptoTransform", ("TransformFinalBlock",)),
    ("dekode / kripto", "System.Security.Cryptography.SymmetricAlgorithm", ("CreateDecryptor", "CreateEncryptor")),
    ("persistensi / registri", "Microsoft.Win32.RegistryKey", ("SetValue", "CreateSubKey")),
    ("persistensi / registri", "Microsoft.Win32.Registry", ("SetValue",)),
    ("berkas", "System.IO.File", ("WriteAllBytes", "Delete")),
    ("penyadap input / layar", "System.Drawing.Graphics", ("CopyFromScreen",)),
    ("penyadap input / layar", "System.Windows.Forms.Clipboard", ("GetText", "GetDataObject")),
    ("anti-debug / anti-analisis", "System.Diagnostics.Debugger", ("get_IsAttached", "IsLogging")),
    ("anti-debug / anti-analisis", "System.Management.ManagementObjectSearcher", (".ctor",)),
)
_NETIL_API_IDX: dict = {}
for _g, _t, _ms in _NETIL_API:
    _NETIL_API_IDX.setdefault(_t, []).append((_g, _ms))
# grup yang menghasilkan peringatan (bukan sekadar daftar)
_NETIL_WARN_GROUPS = {"muat kode dinamis", "eksekusi proses / shell"}


def _net_clr(d: bytes, pe: dict):
    """Cari stream metadata CLR. -> (streams {nama: (offset berkas, ukuran)}, r2o, entry_token) atau None."""
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
    _cb, _ma, _mi, mrva, _msz, _cf, etok = struct.unpack_from("<IHHIIII", d, co)
    mo = r2o(mrva)
    if mo is None or mo + 20 > len(d) or d[mo:mo + 4] != b"BSJB":
        return None
    vlen = struct.unpack_from("<I", d, mo + 12)[0]
    if vlen > 255 or mo + 16 + vlen + 4 > len(d):
        return None
    p = mo + 16 + vlen
    nstreams = struct.unpack_from("<H", d, p + 2)[0]
    p += 4
    streams: dict = {}
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
    return streams, r2o, etok


def _net_tables(d: bytes, base: int, size: int):
    """Urai header #~ dan tata letak tabel. -> {"rows", "lay", "sizes"} atau None (metadata rusak / tak didukung)."""
    end = min(base + size, len(d))
    if size < 24 or base + 24 > len(d):
        return None
    hs = d[base + 6]
    valid = struct.unpack_from("<Q", d, base + 8)[0]
    p = base + 24
    rows: dict = {}
    for t in range(64):
        if valid >> t & 1:
            if p + 4 > end:
                return None
            n = struct.unpack_from("<I", d, p)[0]
            p += 4
            if t > 44 or n > NETIL_MAX_ROWS:
                return None
            rows[t] = n
    if hs & 0x40:
        p += 4
    ssz, gsz, bsz = (4 if hs & 1 else 2), (4 if hs & 2 else 2), (4 if hs & 4 else 2)
    lay: dict = {}
    for t in sorted(rows):
        cols = []
        for c in _NT_SCHEMA[t]:
            if isinstance(c, int):
                cols.append(c)
            elif c == "S":
                cols.append(ssz)
            elif c == "G":
                cols.append(gsz)
            elif c == "B":
                cols.append(bsz)
            elif c[0] == "T":
                cols.append(4 if rows.get(c[1], 0) > 0xFFFF else 2)
            else:
                bits, tabs = _NT_CODED[c[1]]
                cols.append(4 if max(rows.get(x, 0) for x in tabs) >= (1 << (16 - bits)) else 2)
        rs = sum(cols)
        if p + rs * rows[t] > end:
            return None
        lay[t] = (p, rs, cols)
        p += rs * rows[t]
    return {"rows": rows, "lay": lay}


def _nt_rows(d: bytes, tb: dict, t: int) -> list:
    """Semua baris tabel t sebagai daftar tuple bilangan bulat (kosong bila tabel tak ada)."""
    ent = tb["lay"].get(t)
    if not ent or not tb["rows"][t]:
        return []
    off, rs, cols = ent
    fmt = "<" + "".join({1: "B", 2: "H", 4: "I"}[c] for c in cols)
    return list(struct.iter_unpack(fmt, d[off:off + rs * tb["rows"][t]]))


def _il_body(d: bytes, off: int):
    """Badan metode CIL di offset berkas off -> (kode, panjang) atau None."""
    if off < 0 or off >= len(d):
        return None
    b = d[off]
    if b & 3 == 2:
        sz, start = b >> 2, off + 1
    elif b & 3 == 3 and off + 12 <= len(d):
        hs = (struct.unpack_from("<H", d, off)[0] >> 12) * 4
        sz = struct.unpack_from("<I", d, off + 4)[0]
        start = off + hs
        if hs < 12:
            return None
    else:
        return None
    if sz <= 0 or sz > NETIL_MAX_BODY or start + sz > len(d):
        return None
    return d[start:start + sz], sz


def _il_scan(code: bytes):
    """Pindai opcode. -> (token_pemanggilan, jumlah xor, jumlah lompat mundur, ldstr) atau None bila opcode tak valid / terpotong."""
    i, n = 0, len(code)
    calls: list = []
    xors = back = lds = 0
    while i < n:
        op = code[i]
        i += 1
        if op == 0xFE:
            if i >= n:
                return None
            op2 = code[i]
            i += 1
            sz = _IL2.get(op2)
            if sz is None:
                return None
            if op2 in (0x06, 0x07) and i + 4 <= n:
                calls.append(int.from_bytes(code[i:i + 4], "little"))
            i += sz
            continue
        sz = _IL1[op]
        if sz == -1:
            return None
        if sz == -2:
            if i + 4 > n:
                return None
            i += 4 + 4 * int.from_bytes(code[i:i + 4], "little")
            continue
        if sz:
            if i + sz > n:
                return None
            if op in (0x28, 0x6F, 0x73):
                calls.append(int.from_bytes(code[i:i + 4], "little"))
            elif op == 0x72:
                lds += 1
            elif 0x2B <= op <= 0x37 or op == 0xDE:
                if code[i] >= 0x80:
                    back += 1
            elif 0x38 <= op <= 0x44 or op == 0xDD:
                if code[i + 3] >= 0x80:
                    back += 1
            i += sz
        elif op == 0x61:
            xors += 1
    if i != n:
        return None
    return calls, xors, back, lds


def _netil_analyze(d: bytes, pe: dict, dn: dict | None = None) -> dict | None:
    clr = _net_clr(d, pe)
    if not clr:
        return None
    streams, r2o, etok = clr
    ts = streams.get("#~")
    if not ts:
        return {"notes": ["stream '#-' (tabel tak terkompresi) / '#~' tidak ada: tabel metadata tidak diurai"], "types": 0, "methods": 0,
                "bodies": 0, "partial": False, "pinvoke": [], "groups": {}, "calls": [], "chains": [], "decoders": [], "resources": [],
                "assemblies": [], "refs": 0, "entry": ""}
    tb = _net_tables(d, ts[0], ts[1])
    if not tb:
        return {"notes": ["tabel metadata .NET tidak bisa diurai (rusak / disengaja merusak parser)"], "types": 0, "methods": 0, "bodies": 0,
                "partial": False, "pinvoke": [], "groups": {}, "calls": [], "chains": [], "decoders": [], "resources": [], "assemblies": [],
                "refs": 0, "entry": ""}
    deadline = time.time() + NETIL_TIME
    sb, ssz = streams.get("#Strings", (0, 0))
    scache: dict = {}

    def sname(i: int) -> str:
        v = scache.get(i)
        if v is None:
            if i >= ssz or sb + i >= len(d):
                v = ""
            else:
                e = d.find(b"\0", sb + i, min(sb + ssz, sb + i + 512))
                v = _clean(d[sb + i:e if e >= 0 else sb + i + 256].decode("utf-8", "replace"))
            scache[i] = v
        return v

    def coded(name: str, v: int):
        bits, tabs = _NT_CODED[name]
        tag = v & ((1 << bits) - 1)
        return (tabs[tag] if tag < len(tabs) else -1), v >> bits

    typeref = _nt_rows(d, tb, 1)
    typedef = _nt_rows(d, tb, 2)
    methoddef = _nt_rows(d, tb, 6)
    memberref = _nt_rows(d, tb, 10)
    modref = _nt_rows(d, tb, 26)
    implmap = _nt_rows(d, tb, 28)
    asmref = _nt_rows(d, tb, 35)
    mres = _nt_rows(d, tb, 40)
    nested = _nt_rows(d, tb, 41)
    mspec = _nt_rows(d, tb, 43)
    nmeth = len(methoddef)
    enclosing = {a: b for a, b in nested}

    def tr_full(i: int) -> str:     # TypeRef (1-berbasis)
        if not 1 <= i <= len(typeref):
            return "?"
        sc, n_, ns_ = typeref[i - 1]
        nm, ns = sname(n_), sname(ns_)
        return (ns + "." + nm) if ns else nm

    td_cache: dict = {}

    def td_full(i: int, depth: int = 0) -> str:     # TypeDef
        if not 1 <= i <= len(typedef):
            return "?"
        v = td_cache.get(i)
        if v is None:
            _fl, n_, ns_ = typedef[i - 1][:3]
            nm, ns = sname(n_), sname(ns_)
            if i in enclosing and depth < 6:
                v = td_full(enclosing[i], depth + 1) + "/" + nm
            else:
                v = (ns + "." + nm) if ns else nm
            td_cache[i] = v
        return v

    owner = [0] * (nmeth + 2)
    for i, row in enumerate(typedef):
        a = row[5]
        b = typedef[i + 1][5] if i + 1 < len(typedef) else nmeth + 1
        for m in range(a, min(b, nmeth + 1)):
            owner[m] = i + 1

    def meth_full(m: int) -> str:     # MethodDef (1-berbasis)
        if not 1 <= m <= nmeth:
            return "?"
        t = owner[m]
        return "%s::%s" % (td_full(t) if t else "?", sname(methoddef[m - 1][3]))

    pinv: dict = {}      # MethodDef -> (dll, fungsi)
    for _fl, fwd, imp, scope in implmap:
        tab, idx = coded("MemberForwarded", fwd)
        if tab == 6 and 1 <= idx <= nmeth:
            dll = sname(modref[scope - 1][0]) if 1 <= scope <= len(modref) else "?"
            pinv[idx] = (dll, sname(imp))

    tok_cache: dict = {}

    def tok_name(tok: int, depth: int = 0):
        """token -> (nama, jenis) dengan jenis 'int' (MethodDef), 'ref' (MemberRef), 'pinvoke'."""
        v = tok_cache.get(tok)
        if v is not None:
            return v
        t, i = tok >> 24, tok & 0xFFFFFF
        v = ("?", "?")
        if t == 0x06 and 1 <= i <= nmeth:
            v = (meth_full(i), "pinvoke" if i in pinv else "int")
        elif t == 0x0A and 1 <= i <= len(memberref):
            cls, n_, _sig = memberref[i - 1]
            ct, ci = coded("MemberRefParent", cls)
            if ct == 1:
                owner_ = tr_full(ci)
            elif ct == 2:
                owner_ = td_full(ci)
            elif ct == 26:
                owner_ = sname(modref[ci - 1][0]) if 1 <= ci <= len(modref) else "?"
            elif ct == 6:
                owner_ = meth_full(ci)
            else:
                owner_ = "?"
            v = ("%s::%s" % (owner_, sname(n_)), "ref")
        elif t == 0x2B and 1 <= i <= len(mspec) and depth < 2:
            mt, mi = coded("MethodDefOrRef", mspec[i - 1][0])
            v = tok_name((6 if mt == 6 else 10) << 24 | mi, depth + 1)
        tok_cache[tok] = v
        return v

    def api_group(name: str):
        t, _, m = name.rpartition("::")
        for g, ms in _NETIL_API_IDX.get(t, ()):
            if ms is None or m in ms:
                return g
        return None

    pcap: dict = {}
    for cap, keys in _NET_CAPS.items():
        for k in keys:
            pcap.setdefault(k, cap)

    adj: dict = {}          # MethodDef -> {MethodDef}
    sens: dict = {}         # MethodDef -> {grup: {callee,...}}
    fan: dict = {}
    calls: list = []
    decoders: list = []
    bodies = insns = scanned = bad = 0
    partial = False
    for m in range(1, nmeth + 1):
        if m % 64 == 0 and time.time() > deadline:
            partial = True
            break
        if bodies >= NETIL_MAX_METHODS or scanned > NETIL_MAX_BYTES:
            partial = True
            break
        rva, _impl, flags = methoddef[m - 1][:3]
        if not rva or flags & 0x400 or flags & 0x2000:    # abstract / pinvokeimpl
            continue
        off = r2o(rva)
        if off is None:
            continue
        body = _il_body(d, off)
        if not body:
            bad += 1
            continue
        code, sz = body
        scanned += sz
        res = _il_scan(code)
        if res is None:
            bad += 1
            continue
        bodies += 1
        cl, xors, back, _lds = res
        insns += len(cl)
        if xors and back and sz <= 4096 and len(decoders) < 12:
            decoders.append("%s (xor x%d, loop x%d, %d byte IL)" % (meth_full(m), xors, back, sz))
        for tok in cl:
            nm, kind = tok_name(tok)
            if kind == "int":
                callee = tok & 0xFFFFFF
                adj.setdefault(m, set()).add(callee)
                fan[callee] = fan.get(callee, 0) + 1
                continue
            if kind == "pinvoke":
                callee = tok & 0xFFFFFF
                adj.setdefault(m, set()).add(callee)
                dll, fn = pinv[callee]
                g = pcap.get(fn)
                if g:
                    sens.setdefault(m, {}).setdefault(g, set()).add("%s!%s" % (dll, fn))
                    if len(calls) < NETIL_MAX_CALLS:
                        calls.append({"group": g, "callee": "%s!%s" % (dll, fn), "caller": meth_full(m)})
                continue
            g = api_group(nm) if kind == "ref" else None
            if g:
                sens.setdefault(m, {}).setdefault(g, set()).add(nm)
                if len(calls) < NETIL_MAX_CALLS:
                    calls.append({"group": g, "callee": nm, "caller": meth_full(m)})
    groups: dict = {}
    for m, gs in sens.items():
        for g, names in gs.items():
            e = groups.setdefault(g, {"n": 0, "callers": [], "apis": []})
            e["n"] += len(names)
            if len(e["callers"]) < 4:
                e["callers"].append(meth_full(m))
            for x in sorted(names):
                if x not in e["apis"] and len(e["apis"]) < 6:
                    e["apis"].append(x)
    # rantai panggilan: dari titik masuk / Main / konstruktor modul ke metode pemanggil API sensitif
    roots: list = []
    if etok >> 24 == 0x06 and 1 <= (etok & 0xFFFFFF) <= nmeth:
        roots.append(etok & 0xFFFFFF)
    for m in range(1, nmeth + 1):
        nm = sname(methoddef[m - 1][3])
        if nm == "Main" or (nm == ".cctor" and owner[m] == 1):
            if m not in roots:
                roots.append(m)
        if len(roots) >= 8:
            break
    chains: list = []
    for r in roots:
        par = {r: 0}
        queue = [(r, 0)]
        qi = 0
        while qi < len(queue) and len(chains) < 8:
            cur, dep = queue[qi]
            qi += 1
            if cur in sens:
                path, x = [], cur
                while x:
                    path.append(meth_full(x))
                    x = par[x]
                names = sorted({a for v in sens[cur].values() for a in v})[:3]
                ch = " -> ".join(reversed(path)) + "  [%s]" % ", ".join(names)
                if ch not in chains:
                    chains.append(ch)
            if dep >= 5:
                continue
            for nx in sorted(adj.get(cur, ())):
                if nx not in par:
                    par[nx] = cur
                    queue.append((nx, dep + 1))
    notes: list = []
    for g in sorted(_NETIL_WARN_GROUPS):
        if g in groups:
            notes.append("%s: %s (di %s)" % (g, ", ".join(groups[g]["apis"][:3]), ", ".join(groups[g]["callers"][:2])))
    inj = [p for p in pinv.values() if p[1] in ("VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "SetThreadContext", "QueueUserAPC")]
    if inj:
        notes.append("P/Invoke injeksi proses: " + ", ".join(sorted({"%s!%s" % x for x in inj})[:4]))
    if bad and nmeth and bad / max(1, bad + bodies) > 0.2 and bad >= 5:
        notes.append("%d metode berbadan IL tidak valid / tak terbaca (dugaan IL dienkripsi atau obfuskasi anti-dekompiler)" % bad)
    if partial:
        notes.append("TERPOTONG (batas waktu / ukuran)")
    resources = []
    for off_, _fl, n_, impl in mres[:40]:
        itab, _ii = coded("Implementation", impl)
        resources.append("%s%s" % (sname(n_), "" if impl == 0 else " (di %s)" % ("berkas lain" if itab == 38 else "assembly lain")))
    top_fan = sorted(fan.items(), key=lambda kv: -kv[1])[:3]
    return {
        "types": len(typedef), "methods": nmeth, "bodies": bodies, "bad_bodies": bad, "partial": partial, "notes": notes,
        "entry": meth_full(etok & 0xFFFFFF) if etok >> 24 == 0x06 and 1 <= (etok & 0xFFFFFF) <= nmeth else "",
        "refs": len(memberref), "typerefs": len(typeref),
        "assemblies": _uniq((sname(r[6]) for r in asmref), 40),
        "pinvoke": [{"dll": dll, "func": fn, "method": meth_full(m)} for m, (dll, fn) in sorted(pinv.items())[:60]],
        "n_pinvoke": len(pinv), "groups": groups, "calls": calls, "chains": chains, "decoders": decoders, "resources": resources,
        "fanin": ["%s (dipanggil %dx)" % (meth_full(m), n) for m, n in top_fan if n >= 20],
    }


def _netil_enrich(rep: dict, d: bytes) -> None:
    """Dipanggil dari triage(): rep["dotnet_il"] (kunci baru, aditif) untuk PE .NET."""
    pe, dn = rep.get("pe"), rep.get("dotnet")
    if not dn or not pe or pe.get("broken"):
        return
    try:
        r = _netil_analyze(d, pe, dn)
    except Exception as e:
        rep["warn"].append("analisis IL .NET gagal: %s" % type(e).__name__)
        return
    if r and (r["types"] or r["notes"]):
        rep["dotnet_il"] = r
        for x in r["notes"][:6]:
            rep["warn"].append("IL .NET: " + x)


def _render_netil(il, a, compact: bool, defang: bool = True) -> None:
    if not il or not il.get("types"):
        return
    a(".NET IL: %d tipe / %d metode (%d badan IL diurai), %d MemberRef, %d P/Invoke%s" % (
        il["types"], il["methods"], il["bodies"], il["refs"], il.get("n_pinvoke", 0), " | TERPOTONG" if il.get("partial") else ""))
    if il.get("entry"):
        a("   titik masuk: " + _clean(il["entry"]))
    for x in il["notes"][: (3 if compact else 10)]:
        a("   ! " + _clean(x))
    for g, e in list(il["groups"].items())[: (4 if compact else 12)]:
        a("   - %s x%d: %s | dari %s" % (g, e["n"], _clean(", ".join(e["apis"][:3])), ", ".join(_clean(c) for c in e["callers"][:2])))
    if compact:
        return
    for p in il["pinvoke"][:14]:
        a("   P/Invoke: %s!%s <- %s" % (_df(_clean(p["dll"]), defang), _clean(p["func"]), _clean(p["method"])))
    for x in il["chains"][:6]:
        a("   rantai: " + _clean(x))
    for x in il["decoders"][:5]:
        a("   kandidat dekoder: " + _clean(x))
    for x in il.get("fanin", [])[:3]:
        a("   fan-in tinggi (pembantu string / dekripsi?): " + _clean(x))
    if il["resources"]:
        a("   resource terkelola: " + ", ".join(_clean(x) for x in il["resources"][:8]))
    if il["assemblies"]:
        a("   AssemblyRef: " + ", ".join(_clean(x) for x in il["assemblies"][:10]))


def net_text(path, defang: bool = True, compact: bool = False) -> str:
    """Laporan tabel metadata + IL untuk PE .NET (CLI --net, API action 'dotnet')."""
    try:
        f_, size = _open_regular(path)
        with f_:
            d = f_.read(min(size, MAX_SCAN))
        pe = _parse_pe(d, size)
        if not pe or pe.get("broken") or not pe.get("dotnet"):
            return ".NET: bukan PE .NET (tidak ada header CLR)."
        dn = _dotnet_info(d, pe)
        il = _netil_analyze(d, pe, dn)
    except Exception as e:
        return ".NET IL gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L: list = []
    _render_netil(il, L.append, compact, defang)
    if not L:
        return ".NET: tabel metadata tidak bisa dianalisis%s." % ((" (" + "; ".join(il["notes"]) + ")") if il and il.get("notes") else "")
    return "\n".join(L)


def _apk_deep(z, names: list[str], low: list[str], out: dict) -> None:
    """Dipanggil dari _parse_zip untuk APK: manifest biner dan DEX."""
    man = None
    try:
        mf = _zread(z, _zlast(z, low, "androidmanifest.xml"), 2 * 1024 * 1024)
        man = _axml_summary(mf)
        if man:
            out["manifest"] = man
            if man["perms"]:
                out["perms"] = sorted(set(out["perms"]) | set(man["perms"]))[:80]
    except Exception:
        pass
    dex = {"strings": 0, "types": 0, "methods": 0, "classes": 0, "hits": {}, "obf": False, "files": 0}
    dcode: dict = {}                     # v99.11 [S1]: bytecode Dalvik (kunci baru dex_info["code"], aditif)
    dentries = _dex_entry_classes(man)
    ddeadline = time.monotonic() + DEX_CODE_TIME
    for i, n in enumerate(low):
        if not re.fullmatch(r"classes\d*\.dex", n) or dex["files"] >= 4:
            continue
        try:
            raw = _zread(z, names[i], 40 * 1024 * 1024)
            r = _dex_scan(raw)
        except Exception:
            r, raw = None, b""
        if not r:
            continue
        try:
            cr = _dex_code(raw, dentries, ddeadline)
            if cr:
                _dex_code_merge(dcode, cr)
        except Exception as e_:
            out["warn"].append("analisis bytecode DEX gagal: %s" % type(e_).__name__)
        dex["files"] += 1
        for k in ("strings", "types", "methods", "classes"):
            dex[k] += r[k]
        dex["obf"] = dex["obf"] or r["obf"]
        for g, lst in r["hits"].items():
            cur = dex["hits"].setdefault(g, [])
            cur.extend(x for x in lst if x not in cur and len(cur) < 6)
    if dcode.get("methods"):
        dex["code"] = dcode
        for x_ in dcode["notes"][:6]:
            out["warn"].append("DEX bytecode: " + x_)
    if dex["files"]:
        out["dex_info"] = dex


def _render_apk(zp: dict, a, compact: bool, defang: bool = True) -> None:
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
        _render_dexcode(di.get("code"), a, compact, defang)


