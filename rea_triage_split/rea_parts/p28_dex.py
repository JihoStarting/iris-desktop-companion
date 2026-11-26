# rea_triage bagian 28/47: dex (baris asli 11306-11916). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.11 [S1]: analisis bytecode Dalvik (DEX) ---------------------------------------------
# Membaca INSTRUKSI di code_item setiap metode, bukan hanya tabel method_ids: argumen konstan yang sampai ke API sensitif
# (nomor SMS, perintah shell, nama transformasi Cipher, URL), string yang dirakit lewat StringBuilder, kunci / IV hard-coded
# (fill-array-data), Base64 konstan, dan rantai panggilan dari komponen manifest ke pemanggil API sensitif. Pelacakan nilai
# bersifat lurus per-blok (dibuang di target lompatan / handler), jadi hasilnya PETUNJUK, bukan bukti; pemanggilan virtual
# dan refleksi tidak diselesaikan. Statis murni: tidak ada kode yang dijalankan. Hanya pustaka standar.

DEX_CODE_TIME = 6.0              # detik untuk seluruh analisis bytecode satu berkas / APK; sisanya dilaporkan sebagai terpotong
DEX_CODE_MAX_INSNS = 8_000_000   # unit 16-bit yang diurai per DEX
DEX_CODE_MAX_UNITS = 200_000     # satu metode lebih panjang dari ini dilewati
DEX_CODE_MAX_EDGES = 400_000     # sisi graf panggilan yang disimpan
DEX_CODE_MAX_CALLS = 60          # pemanggilan berargumen konstan yang dilaporkan
DEX_CODE_MAX_FILES = 8           # classes*.dex yang dianalisis per APK

_DEX_EXTRA_API = {   # tambahan khusus analisis bytecode (tidak mengubah _DEX_API / dex_info["hits"] yang lama)
    "jaringan / URL": ("Ljava/net/URL;-><init>", "Ljava/net/URL;->openConnection", "Ljava/net/Socket;-><init>",
                       "Lorg/apache/http/client/methods/HttpGet;-><init>", "Lorg/apache/http/client/methods/HttpPost;-><init>"),
    "pustaka native": ("Ljava/lang/System;->loadLibrary", "Ljava/lang/System;->load"),
    "hash / IV / sandi": ("Ljava/security/MessageDigest;->getInstance", "Ljavax/crypto/spec/IvParameterSpec;-><init>", "Ljavax/crypto/spec/PBEKeySpec;-><init>"),
    "sembunyikan komponen": ("PackageManager;->setComponentEnabledSetting",),
}
_DEX_ALLAPI = dict(_DEX_API)
_DEX_ALLAPI.update(_DEX_EXTRA_API)
# paket pustaka populer: kelasnya dilewati (hemat waktu) dan tidak dianggap kode aplikasi di graf panggilan
_DEX_LIB_PREFIX = ("Landroidx/", "Landroid/support/", "Lkotlin/", "Lkotlinx/", "Lcom/google/android/gms/", "Lcom/google/firebase/",
                   "Lcom/google/android/material/", "Lcom/squareup/", "Lokhttp3/", "Lokio/", "Lcom/bumptech/", "Lcom/facebook/",
                   "Lio/reactivex/", "Lorg/jetbrains/")
_DEX_FW_PREFIX = _DEX_LIB_PREFIX + ("Landroid/", "Ljava/", "Ljavax/", "Ldalvik/", "Lorg/json/", "Lorg/apache/", "Lorg/w3c/", "Lorg/xml/")


def _dex_len_table() -> list:
    """Panjang instruksi Dalvik (unit 16-bit) per opcode; opcode tak terpakai dihitung 1 supaya penelusuran tidak macet."""
    t = [1] * 256
    for lo, hi in ((0x2D, 0x3D), (0x44, 0x6D), (0x90, 0xAF), (0xD0, 0xE2)):
        for i in range(lo, hi + 1):
            t[i] = 2
    for i in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1A, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x29, 0xFE, 0xFF):
        t[i] = 2
    for i in (0x03, 0x06, 0x09, 0x14, 0x17, 0x1B, 0x24, 0x25, 0x26, 0x2A, 0x2B, 0x2C, 0xFC, 0xFD):
        t[i] = 3
    for i in list(range(0x6E, 0x73)) + list(range(0x74, 0x79)):
        t[i] = 3
    t[0x18] = 5
    t[0xFA] = t[0xFB] = 4
    return t


_DEX_LEN = _dex_len_table()
# opcode yang menulis register tujuan (selain yang ditangani khusus): 4 = nibble rendah byte tinggi, 8 = byte tinggi, 16 = unit berikutnya
_DEX_DEST: dict[int, int] = {}
for _r, _m in (((0x04, 0x04), 4), ((0x20, 0x21), 4), ((0x23, 0x23), 4), ((0x52, 0x58), 4), ((0x7B, 0x8F), 4), ((0xB0, 0xD7), 4),
               ((0x05, 0x05), 8), ((0x0A, 0x0B), 8), ((0x0D, 0x0D), 8), ((0x16, 0x19), 8), ((0x2D, 0x31), 8), ((0x44, 0x4A), 8),
               ((0x60, 0x66), 8), ((0x90, 0xAF), 8), ((0xD8, 0xE2), 8), ((0xFE, 0xFF), 8), ((0x06, 0x06), 16)):
    for _o in range(_r[0], _r[1] + 1):
        _DEX_DEST[_o] = _m
_DEX_ENDS = frozenset((0x0E, 0x0F, 0x10, 0x11, 0x27, 0x28, 0x29, 0x2A))   # return / throw / goto: setelahnya hanya terjangkau lewat lompatan


def _dex_payload_len(u, pc: int, n: int) -> int:
    """Panjang (unit) payload semu packed-switch / sparse-switch / fill-array-data di u[pc]."""
    try:
        ident = u[pc]
        if ident == 0x100:
            return u[pc + 1] * 2 + 4
        if ident == 0x200:
            return u[pc + 1] * 4 + 2
        if ident == 0x300:
            return ((u[pc + 2] | (u[pc + 3] << 16)) * u[pc + 1] + 1) // 2 + 4
    except IndexError:
        pass
    return 1


def _dex_s32(lo: int, hi: int) -> int:
    v = lo | (hi << 16)
    return v - (1 << 32) if v & 0x80000000 else v


def _dex_targets(u, n: int) -> set:
    """Alamat (unit) yang menjadi tujuan lompatan: di sana nilai register yang dilacak dibuang."""
    t: set = set()
    pc = 0
    while pc < n:
        w = u[pc]
        op = w & 0xFF
        if op == 0 and w in (0x100, 0x200, 0x300):
            pc += _dex_payload_len(u, pc, n)
            continue
        if 0x32 <= op <= 0x3D:
            if pc + 1 < n:
                o = u[pc + 1]
                t.add(pc + (o - 65536 if o & 0x8000 else o))
        elif op == 0x28:
            o = w >> 8
            t.add(pc + (o - 256 if o & 0x80 else o))
        elif op == 0x29:
            if pc + 1 < n:
                o = u[pc + 1]
                t.add(pc + (o - 65536 if o & 0x8000 else o))
        elif op == 0x2A:
            if pc + 2 < n:
                t.add(pc + _dex_s32(u[pc + 1], u[pc + 2]))
        elif op in (0x2B, 0x2C) and pc + 2 < n:
            pp = pc + _dex_s32(u[pc + 1], u[pc + 2])
            try:
                if 0 <= pp < n - 1:
                    sz = min(u[pp + 1], 4096)
                    if u[pp] == 0x100:
                        base = pp + 4
                    elif u[pp] == 0x200:
                        base = pp + 2 + 2 * sz
                    else:
                        base = -1
                    if base > 0:
                        for i in range(sz):
                            t.add(pc + _dex_s32(u[base + 2 * i], u[base + 2 * i + 1]))
            except IndexError:
                pass
        pc += _DEX_LEN[op]
    return t


def _dex_pretty(cls: str, name: str = "") -> str:
    """'Lcom/x/Y;' + 'm' -> 'com.x.Y.m'."""
    c = cls[1:-1].replace("/", ".") if cls.startswith("L") and cls.endswith(";") else cls
    return "%s.%s" % (c, name) if name else c


def _dex_valtext(v) -> str:
    """Teks nilai untuk perakitan StringBuilder; yang tak diketahui jadi {?}."""
    if v is None:
        return "{?}"
    k = v[0]
    if k == "s":
        return v[1]
    if k == "i":
        return str(v[1])
    if k == "sb":
        return "".join(v[1])
    return "{?}"


def _dex_valrepr(v) -> str:
    if v is None:
        return "?"
    k = v[0]
    if k in ("s", "sb"):
        return "\"%s\"" % (v[1] if k == "s" else "".join(v[1]))[:120]
    if k == "i":
        return str(v[1]) if -256 < v[1] < 256 else "0x%X" % (v[1] & 0xFFFFFFFF)
    if k == "b":
        b = v[1]
        txt = b.decode("latin-1")
        return "byte[%d] %s%s" % (len(b), b[:24].hex(), (" \"%s\"" % txt[:40]) if txt.isprintable() and len(b) >= 4 else "")
    if k == "c":
        return "class " + _dex_pretty(v[1])
    if k == "n":
        return "new " + _dex_pretty(v[1])
    return "?"


def _dex_code(d: bytes, entries=None, deadline: float | None = None) -> dict | None:
    """Analisis bytecode satu DEX. entries: himpunan deskriptor kelas komponen manifest ('Lcom/x/Y;') untuk rantai panggilan.
    Berhenti sebagian (partial=True) bila waktu / batas instruksi habis. Tidak pernah membaca di luar `d`."""
    if len(d) < 0x70 or d[:4] != b"dex\n":
        return None
    n = len(d)
    ss, so, ts, to, _ps, _po, _fs, _fo, ms, mo, cs, co = struct.unpack_from("<12I", d, 0x38)
    ss, ts, ms, cs = min(ss, 400000), min(ts, 200000), min(ms, 400000), min(cs, 100000)
    deadline = deadline or (time.monotonic() + DEX_CODE_TIME)
    LEN = _DEX_LEN
    scache: dict[int, str] = {}
    tcache: dict[int, str] = {}
    mcache: dict[int, tuple] = {}
    gcache: dict[int, tuple] = {}
    acache: dict[int, bool] = {}

    def sget(i: int, lim: int = 600) -> str:
        r = scache.get(i)
        if r is not None:
            return r
        r = ""
        if 0 <= i < ss and so + 4 * i + 4 <= n:
            o = struct.unpack_from("<I", d, so + 4 * i)[0]
            if o < n:
                _l, p = _uleb(d, o)
                e = d.find(b"\0", p, min(n, p + lim * 3))
                r = d[p:(e if e >= 0 else min(n, p + lim * 3))].decode("utf-8", "replace")[:lim]
        scache[i] = r
        return r

    def tname(i: int) -> str:
        r = tcache.get(i)
        if r is None:
            r = ""
            if 0 <= i < ts and to + 4 * i + 4 <= n:
                r = sget(struct.unpack_from("<I", d, to + 4 * i)[0])
            tcache[i] = r
        return r

    def mparts(mi: int) -> tuple:
        r = mcache.get(mi)
        if r is None:
            r = ("?", "?")
            if 0 <= mi < ms and mo + 8 * mi + 8 <= n:
                ci, _pi, ni = struct.unpack_from("<HHI", d, mo + 8 * mi)
                r = (tname(ci), sget(ni))
            mcache[mi] = r
        return r

    def groups_of(mi: int) -> tuple:
        r = gcache.get(mi)
        if r is None:
            c, nm = mparts(mi)
            full = "%s->%s" % (c, nm)
            r = tuple(g for g, keys in _DEX_ALLAPI.items() if any(k in full for k in keys))
            gcache[mi] = r
        return r

    def is_app(mi: int) -> bool:
        r = acache.get(mi)
        if r is None:
            r = not mparts(mi)[0].startswith(_DEX_FW_PREFIX)
            acache[mi] = r
        return r

    st = {"methods": 0, "insns": 0, "sites": 0, "classes": 0, "lib": 0, "partial": False}
    groups: dict[str, dict] = {}
    calls: list[dict] = []
    percall: dict[str, int] = {}
    keys: list[dict] = []
    notes: list[str] = []
    edges: dict[int, list] = {}
    nedges = 0
    sites: list[tuple] = []      # (indeks metode pemanggil, kelompok, nama callee) untuk rantai panggilan

    def note(x: str) -> None:
        if x not in notes and len(notes) < 14:
            notes.append(x)

    def walk(mi: int, code: int, cname: str, mname: str) -> None:
        nonlocal nedges
        if code + 16 > n:
            return
        nu = struct.unpack_from("<I", d, code + 12)[0]
        if nu == 0 or nu > DEX_CODE_MAX_UNITS or code + 16 + 2 * nu > n:
            return
        u = struct.unpack_from("<%dH" % nu, d, code + 16)
        st["methods"] += 1
        st["insns"] += nu
        tg = _dex_targets(u, nu)
        regs: dict[int, tuple] = {}
        last = None
        me = None            # nama pemanggil (dibuat sekali bila dibutuhkan)
        pc = 0
        while pc < nu:
            w = u[pc]
            op = w & 0xFF
            if op == 0:
                pc += _dex_payload_len(u, pc, nu) if w in (0x100, 0x200, 0x300) else 1
                continue
            ln = LEN[op]
            if pc + ln > nu:
                break
            if pc in tg:
                regs.clear()
                last = None
            if op == 0x1A or op == 0x1B:
                a = w >> 8
                idx = u[pc + 1] if op == 0x1A else (u[pc + 1] | (u[pc + 2] << 16))
                regs[a] = ("s", sget(idx))
                regs.pop(a + 1, None)
            elif op == 0x12:
                a = (w >> 8) & 0xF
                v = (w >> 12) & 0xF
                regs[a] = ("i", v - 16 if v > 7 else v)
            elif op == 0x13 or op == 0x14 or op == 0x15:
                a = w >> 8
                if op == 0x13:
                    v = u[pc + 1] - 65536 if u[pc + 1] & 0x8000 else u[pc + 1]
                elif op == 0x14:
                    v = _dex_s32(u[pc + 1], u[pc + 2])
                else:
                    v = (u[pc + 1] - 65536 if u[pc + 1] & 0x8000 else u[pc + 1]) << 16
                regs[a] = ("i", v)
            elif op in (0x01, 0x07):
                a, b = (w >> 8) & 0xF, (w >> 12) & 0xF
                if b in regs:
                    regs[a] = regs[b]
                else:
                    regs.pop(a, None)
            elif op in (0x02, 0x08) or op in (0x03, 0x09):
                a, b = (w >> 8, u[pc + 1]) if op in (0x02, 0x08) else (u[pc + 1], u[pc + 2])
                if b in regs:
                    regs[a] = regs[b]
                else:
                    regs.pop(a, None)
            elif op == 0x0C:
                a = w >> 8
                if last is not None:
                    regs[a] = last
                else:
                    regs.pop(a, None)
                last = None
            elif op == 0x1C:
                regs[w >> 8] = ("c", tname(u[pc + 1]))
            elif op == 0x22:
                t = tname(u[pc + 1])
                regs[w >> 8] = ("sb", []) if t == "Ljava/lang/StringBuilder;" else ("n", t)
            elif op == 0x26:     # fill-array-data: isi larik byte konstan (kandidat kunci / IV / blob)
                a = w >> 8
                pp = pc + _dex_s32(u[pc + 1], u[pc + 2])
                regs.pop(a, None)
                if 0 <= pp and pp + 4 <= nu and u[pp] == 0x300 and u[pp + 1] == 1:
                    cnt = min(u[pp + 2] | (u[pp + 3] << 16), 4096)
                    raw = b"".join(struct.pack("<H", x) for x in u[pp + 4:pp + 4 + (cnt + 1) // 2])[:cnt]
                    if raw:
                        regs[a] = ("b", raw)
            elif (0x6E <= op <= 0x72) or (0x74 <= op <= 0x78) or op in (0xFA, 0xFB):
                mi2 = u[pc + 1]
                if op in (0x74, 0x75, 0x76, 0x77, 0x78, 0xFB):
                    args = [u[pc + 2] + i for i in range(w >> 8)]
                else:
                    x = u[pc + 2]
                    args = [x & 0xF, (x >> 4) & 0xF, (x >> 8) & 0xF, (x >> 12) & 0xF, (w >> 8) & 0xF][:(w >> 12) & 0xF]
                cls, nm = mparts(mi2)
                static = op in (0x71, 0x77)
                vals = [regs.get(r) for r in args]
                recv = None if static or not vals else vals[0]
                argv = vals if static else vals[1:]
                res = None
                if cls == "Ljava/lang/StringBuilder;":
                    if nm == "<init>" and args and not static:
                        regs[args[0]] = ("sb", [argv[0][1]] if argv and argv[0] and argv[0][0] == "s" else [])
                    elif nm == "append" and recv and recv[0] == "sb":
                        recv[1].append(_dex_valtext(argv[0] if argv else None))
                        res = recv
                    elif nm == "toString" and recv and recv[0] == "sb":
                        res = ("s", "".join(recv[1])[:2000])
                elif cls == "Ljava/lang/String;" and nm == "getBytes" and recv and recv[0] == "s":
                    res = ("b", recv[1].encode("utf-8", "replace")[:4096])
                elif cls == "Landroid/util/Base64;" and nm == "decode" and argv and argv[0] and argv[0][0] in ("s", "b"):
                    raw = argv[0][1].encode("latin-1", "replace") if argv[0][0] == "s" else argv[0][1]
                    try:
                        res = ("b", base64.b64decode(raw + b"=" * (-len(raw) % 4), altchars=b"-_" if (b"-" in raw or b"_" in raw) else None)[:4096])
                    except Exception:
                        res = None
                gl = groups_of(mi2)
                if gl:
                    st["sites"] += 1
                    if me is None:
                        me = _dex_pretty(cname, mname)
                    callee = _dex_pretty(cls, nm)
                    known = any(v is not None for v in argv)
                    for g in gl:
                        e = groups.setdefault(g, {"n": 0, "callers": []})
                        e["n"] += 1
                        if me not in e["callers"] and len(e["callers"]) < 4:
                            e["callers"].append(me)
                    if known and len(calls) < DEX_CODE_MAX_CALLS and percall.get(gl[0], 0) < 8:
                        percall[gl[0]] = percall.get(gl[0], 0) + 1
                        calls.append({"group": gl[0], "caller": me, "callee": callee, "args": [_dex_valrepr(v) for v in argv][:6]})
                    if len(sites) < 400:
                        sites.append((mi, gl[0], callee))
                    # temuan bernilai tinggi dari argumen konstan
                    if cls == "Ljavax/crypto/spec/SecretKeySpec;" and nm == "<init>":
                        kb = next((v[1] for v in argv if v and v[0] == "b"), None)
                        al = next((v[1] for v in reversed(argv) if v and v[0] == "s"), "?")
                        if kb:
                            if len(keys) < 12:
                                keys.append({"kind": "kunci", "algo": al[:20], "len": len(kb), "hex": kb[:32].hex(), "caller": me})
                            note("kunci kripto hard-coded (%s, %d byte) di %s" % (al[:20], len(kb), me))
                    elif cls == "Ljavax/crypto/spec/IvParameterSpec;" and nm == "<init>":
                        kb = next((v[1] for v in argv if v and v[0] == "b"), None)
                        if kb and len(keys) < 12:
                            keys.append({"kind": "IV", "algo": "", "len": len(kb), "hex": kb[:32].hex(), "caller": me})
                    elif cls == "Ljavax/crypto/Cipher;" and nm == "getInstance" and argv and argv[0] and argv[0][0] == "s":
                        tr = argv[0][1].upper()
                        if "ECB" in tr or tr in ("AES", "DES", "DESEDE", "3DES") or tr.startswith("DES/"):
                            note("Cipher %s (mode ECB / bawaan = ECB atau DES lemah) di %s" % (argv[0][1][:40], me))
                    elif cls == "Ljava/lang/Runtime;" and nm == "exec" and argv and argv[0] and argv[0][0] in ("s", "sb"):
                        cmd = _dex_valtext(argv[0]).strip()
                        if re.match(r"(su|sh|/system/(?:x?bin)/su|busybox|chmod|pm install|am start|su -c)\b", cmd):
                            note("exec perintah shell \"%s\" di %s" % (cmd[:60], me))
                    elif nm == "<init>" and cls.endswith("ClassLoader;") and "dalvik" in cls:
                        pth = next((v for v in argv if v and v[0] in ("s", "sb")), None)
                        note("pemuatan kode dinamis%s di %s" % ((" dari \"%s\"" % _dex_valtext(pth)[:70]) if pth else "", me))
                if is_app(mi2) and nedges < DEX_CODE_MAX_EDGES:
                    lst = edges.setdefault(mi2, [])
                    if len(lst) < 16 and mi not in lst:
                        lst.append(mi)
                        nedges += 1
                last = res
            elif op in (0xFC, 0xFD):
                last = None
            else:
                m = _DEX_DEST.get(op)
                if m:
                    a = (w >> 8) & 0xF if m == 4 else (w >> 8 if m == 8 else u[pc + 1])
                    regs.pop(a, None)
                    regs.pop(a + 1, None)
                if op in _DEX_ENDS:
                    regs.clear()
                    last = None
            if op == 0x0D:
                regs.clear()      # awal handler pengecualian: keadaan masuk tidak diketahui
            pc += ln

    stop = False
    for ci in range(cs):
        if (ci & 15) == 0 and time.monotonic() > deadline:
            st["partial"] = True
            break
        if stop:
            break
        p = co + 32 * ci
        if p + 32 > n:
            break
        cidx, _acc, _sup, _itf, _src, _ann, cdo, _sv = struct.unpack_from("<8I", d, p)
        if not cdo or cdo >= n:
            continue
        cname = tname(cidx)
        if cname.startswith(_DEX_LIB_PREFIX):
            st["lib"] += 1
            continue
        st["classes"] += 1
        o = cdo
        sf, o = _uleb(d, o)
        inf, o = _uleb(d, o)
        dm, o = _uleb(d, o)
        vm, o = _uleb(d, o)
        if max(sf, inf, dm, vm) > 50000:
            continue
        for _ in range(sf + inf):
            _v, o = _uleb(d, o)
            _v, o = _uleb(d, o)
        for cnt in (dm, vm):
            mi = 0
            for _ in range(cnt):
                diff, o = _uleb(d, o)
                _fl, o = _uleb(d, o)
                code, o = _uleb(d, o)
                mi += diff
                if o > n:
                    break
                if code:
                    if st["insns"] > DEX_CODE_MAX_INSNS or ((st["methods"] & 63) == 0 and time.monotonic() > deadline):
                        st["partial"] = True
                        stop = True
                        break
                    walk(mi, code, cname, mparts(mi)[1])
            if stop:
                break

    # rantai panggilan: dari metode di kelas komponen manifest ke pemanggil API sensitif (maks. kedalaman 5, menurut sisi invoke statis)
    chains: list[str] = []
    if entries and sites:
        seen_chain: set = set()
        for mi, g, callee in sites:
            if len(chains) >= 12:
                break
            frontier = [(mi, (mi,))]
            visited = {mi}
            found = None
            for _depth in range(6):
                nxt = []
                for node, path in frontier:
                    if mparts(node)[0] in entries:
                        found = path
                        break
                    for c in edges.get(node, ()):
                        if c not in visited:
                            visited.add(c)
                            nxt.append((c, path + (c,)))
                if found or not nxt or len(visited) > 4000:
                    break
                frontier = nxt
            if found:
                txt = " -> ".join([_dex_pretty(*mparts(x)) for x in reversed(found)] + [callee])
                if txt not in seen_chain:
                    seen_chain.add(txt)
                    chains.append("[%s] %s" % (g, txt))
    return {"methods": st["methods"], "insns": st["insns"], "classes": st["classes"], "lib_skipped": st["lib"], "sites": st["sites"],
            "partial": st["partial"], "groups": groups, "calls": calls, "keys": keys, "notes": notes, "chains": chains}


def _dex_entry_classes(man) -> set:
    """Deskriptor kelas komponen manifest (activity / service / receiver / provider + kelas Application)."""
    out: set = set()
    if not man:
        return out
    pkg = man.get("package") or ""
    names: list = []
    for lst in (man.get("components") or {}).values():
        names.extend(lst)
    if man.get("app_class"):
        names.append(man["app_class"])
    for nm in names:
        if not nm or not isinstance(nm, str):
            continue
        if nm.startswith("."):
            nm = pkg + nm
        elif "." not in nm and pkg:
            nm = pkg + "." + nm
        out.add("L" + nm.replace(".", "/") + ";")
    return out


def _dex_code_merge(acc: dict, r: dict) -> None:
    for k in ("methods", "insns", "classes", "lib_skipped", "sites"):
        acc[k] = acc.get(k, 0) + r.get(k, 0)
    acc["partial"] = acc.get("partial", False) or r.get("partial", False)
    for g, e in r["groups"].items():
        cur = acc.setdefault("groups", {}).setdefault(g, {"n": 0, "callers": []})
        cur["n"] += e["n"]
        cur["callers"].extend(x for x in e["callers"] if x not in cur["callers"] and len(cur["callers"]) < 4)
    for k, lim in (("calls", DEX_CODE_MAX_CALLS), ("keys", 12), ("notes", 14), ("chains", 12)):
        cur = acc.setdefault(k, [])
        cur.extend(x for x in r[k] if x not in cur and len(cur) < lim)


def _render_dexcode(code, a, compact: bool, defang: bool = True) -> None:
    if not code or not code.get("methods"):
        return
    a("Bytecode DEX: %d metode / %d instruksi diurai (%d kelas aplikasi%s), %d pemanggilan API sensitif%s" % (
        code["methods"], code["insns"], code["classes"], ", %d kelas pustaka dilewati" % code["lib_skipped"] if code.get("lib_skipped") else "",
        code["sites"], " | TERPOTONG (batas waktu / ukuran)" if code.get("partial") else ""))
    for x in (code.get("notes") or [])[: (3 if compact else 14)]:
        a("   ! " + _clean(x))
    for g, e in list((code.get("groups") or {}).items())[: (4 if compact else 16)]:
        a("   - %s x%d dari %s" % (g, e["n"], ", ".join(_clean(c) for c in e["callers"][:2])))
    if compact:
        return
    for c in (code.get("calls") or [])[:14]:
        a("   > %s: %s(%s)" % (_clean(c["group"]), _clean(c["callee"]), _df(_clean(", ".join(c["args"])[:200]), defang)))
    for x in (code.get("chains") or [])[:8]:
        a("   rantai: " + _clean(x))
    for k in (code.get("keys") or [])[:6]:
        a("   %s hard-coded: %d byte %s%s | di %s" % (k["kind"], k["len"], k["hex"], (" (%s)" % _clean(k["algo"])) if k.get("algo") else "", _clean(k["caller"])))


def _dex_code_path(path) -> tuple[dict, list]:
    """Analisis bytecode untuk .dex mentah atau APK / ZIP berisi classes*.dex. Mengembalikan (agregat, catatan)."""
    f_, size = _open_regular(path)
    notes: list = []
    acc: dict = {}
    deadline = time.monotonic() + DEX_CODE_TIME
    with f_:
        head = f_.read(4)
        f_.seek(0)
        if head == b"dex\n":
            r = _dex_code(f_.read(min(size, 128 * 1024 * 1024)), None, deadline)
            if r:
                _dex_code_merge(acc, r)
            return acc, notes
        if not zipfile.is_zipfile(f_):
            return acc, ["bukan DEX / APK"]
        if _zip_cd_bytes(f_) > MAX_ZIP_CD:   # v104
            return acc, ["direktori pusat ZIP terlalu besar: tidak diurai"]
        with zipfile.ZipFile(f_) as z:
            infos = {i.filename.lower(): i for i in z.infolist()}
            entries: set = set()
            if "androidmanifest.xml" in infos:
                try:
                    entries = _dex_entry_classes(_axml_summary(_zread(z, infos["androidmanifest.xml"], 2 * 1024 * 1024)))
                except Exception:
                    pass
            nfile = 0
            for nm in sorted(infos, key=lambda s: (len(s), s)):
                if not re.fullmatch(r"classes\d*\.dex", nm):
                    continue
                if nfile >= DEX_CODE_MAX_FILES:
                    notes.append("hanya %d classes*.dex pertama dianalisis" % DEX_CODE_MAX_FILES)
                    break
                nfile += 1
                r = _dex_code(_zread(z, infos[nm], 64 * 1024 * 1024), entries, deadline)
                if r:
                    _dex_code_merge(acc, r)
            if not nfile:
                notes.append("tidak ada classes*.dex")
    return acc, notes


def dex_text(path, defang: bool = True, compact: bool = False) -> str:
    """Laporan bytecode Dalvik untuk .dex / APK (CLI --dex, API action 'dex')."""
    try:
        acc, notes = _dex_code_path(path)
    except Exception as e:
        return "DEX gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L: list = []
    _render_dexcode(acc, L.append, compact, defang)
    if not L:
        return "DEX: tidak ada metode berkode yang bisa dianalisis%s." % ((" (" + "; ".join(notes) + ")") if notes else "")
    return "\n".join(L + ["   (%s)" % x for x in notes])


def _dexraw_enrich(rep: dict, d) -> None:
    """DEX mandiri (bukan di dalam APK): hasil di rep["dex_code"]; kunci baru, aditif."""
    if d[:4] != b"dex\n":
        return
    try:
        r = _dex_code(d)
    except Exception as e:
        rep["warn"].append("analisis bytecode DEX gagal: %s" % type(e).__name__)
        return
    if r and r["methods"]:
        rep["dex_code"] = r
        for x in r["notes"][:6]:
            rep["warn"].append("DEX bytecode: " + x)


