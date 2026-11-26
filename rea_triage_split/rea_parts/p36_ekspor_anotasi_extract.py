# rea_triage bagian 36/47: ekspor_anotasi_extract (baris asli 16083-16567). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.15 (roadmap v2, Tier B: ekspor anotasi + diff fungsi; OPSIONAL dan ADITIF; keluaran triase lain TIDAK berubah):
#   1. export_annotations(path, fmt): skrip anotasi dari RE Lab (nama fungsi sub_*, komentar string yang dirujuk kode, komentar panggilan API,
#      teknik anti-analisis, kandidat loop dekripsi) untuk Ghidra (.py), IDA (.py), atau x64dbg (database .json). Berkas dibuat TANPA menjalankan
#      sampel; skrip Ghidra / IDA menggeser alamat otomatis bila image base di alat berbeda. Teks dari sampel disisipkan hanya sebagai literal JSON
#      yang di-escape (tidak pernah sebagai kode). Batas: ANN_MAX_FUNCS / ANN_MAX_CMTS.
#   2. func_diff(a, b): perbandingan fungsi antar-dua biner (nama bukan sub_*, set API, string, ukuran, jumlah callee) -> sama / berubah / baru / hilang.
#      Pencocokan: nama ekspor / simbol, lalu kemiripan fitur (Jaccard + rasio ukuran), lalu (ukuran, callee) unik. Batas waktu FDIFF_TIME.
#   CLI: --export FILE ghidra|ida|x64dbg [OUT], --funcdiff A B. API: export (butuh outdir), funcdiff.
#   Batasan: kemiripan hanya statis dari fitur RE Lab (bukan perbandingan instruksi); fungsi tanpa API / string dicocokkan hanya lewat ukuran.
# ---------------------------------------------------------------------------

ANN_MAX_FUNCS = 20000
ANN_MAX_CMTS = 30000
FDIFF_TIME = 6.0
FDIFF_MAX_FUNCS = 4000


def _ann_txt(s, n: int = 110) -> str:
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(s))[:n]


def _relab_ctx(path):
    f, size = _open_regular(path)
    with f:
        d = f.read(MAX_SCAN)
    info, ctx, err = _relab_multi(d, size)
    return info, ctx, err


def _ann_collect(path) -> dict:
    info, ctx, err = _relab_ctx(path)
    if not ctx:
        return {"error": (err or "tidak bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64, serta ELF / Mach-O AArch64"}
    F = ctx["F"]
    funcs = [(va, fo["name"]) for va, fo in sorted(F.items())][:ANN_MAX_FUNCS]
    cm: dict[int, list[str]] = {}

    def add(va, t):
        if len(cm) < ANN_MAX_CMTS or va in cm:
            lst = cm.setdefault(int(va), [])
            if t not in lst and len(lst) < 3:
                lst.append(t)
    for api, vs in ctx["sites"].items():
        for va, _fs in vs:
            add(va, "API: " + _ann_txt(api, 60))
    for e in ctx["sref"].values():
        if e["funcs"]:
            add(e["va"], "string(%s): %s" % (e["kind"], _ann_txt(e["text"])))
    for a in info.get("anti", []):
        try:
            add(int(a["first"], 16), "anti-analisis: " + _ann_txt(a["technique"], 60))
        except (ValueError, KeyError):
            pass
    for x in (info.get("cfg") or {}).get("decrypt_loops", []):
        try:
            add(int(x["head"], 16), "kandidat loop dekripsi (%s)" % "/".join(x["ops"]))
        except (ValueError, KeyError):
            pass
    return {"base": int(info["image_base"], 16), "arch": info["arch"], "funcs": funcs, "cmts": sorted((va, " | ".join(t)) for va, t in cm.items())}


_ANN_GHIDRA = '''# Dibuat oleh rea_triage.py v%(ver)s (analisis statis; sampel tidak dijalankan). Jalankan dari Script Manager Ghidra (Jython / PyGhidra).
# Sumber: %(src)s | %(arch)s
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit
IMAGE_BASE = %(base)s
FUNCS = %(funcs)s
CMTS = %(cmts)s
delta = currentProgram.getImageBase().getOffset() - IMAGE_BASE
fm = currentProgram.getFunctionManager()
lst = currentProgram.getListing()
nf = nc = 0
for va, name in FUNCS:
    a = toAddr(va + delta)
    try:
        f = fm.getFunctionAt(a)
        if f is None:
            f = createFunction(a, name)
        elif f.getName().startswith("FUN_"):
            f.setName(name, SourceType.USER_DEFINED)
        nf += 1
    except Exception as e:
        pass
for va, text in CMTS:
    try:
        lst.setComment(toAddr(va + delta), CodeUnit.EOL_COMMENT, text)
        nc += 1
    except Exception as e:
        pass
print("rea_triage: %%d fungsi, %%d komentar" %% (nf, nc))
'''
_ANN_IDA = '''# Dibuat oleh rea_triage.py v%(ver)s (analisis statis; sampel tidak dijalankan). Jalankan lewat File > Script file di IDA (IDAPython 7+).
# Sumber: %(src)s | %(arch)s
import idc, idaapi, ida_funcs
IMAGE_BASE = %(base)s
FUNCS = %(funcs)s
CMTS = %(cmts)s
delta = idaapi.get_imagebase() - IMAGE_BASE
nf = nc = 0
for va, name in FUNCS:
    ea = va + delta
    try:
        if ida_funcs.get_func(ea) is None:
            ida_funcs.add_func(ea)
        if idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK):
            nf += 1
    except Exception:
        pass
for va, text in CMTS:
    try:
        if idc.set_cmt(va + delta, text, 0):
            nc += 1
    except Exception:
        pass
print("rea_triage: %%d fungsi, %%d komentar" %% (nf, nc))
'''


def export_annotations(path, fmt: str = "ghidra", out=None) -> dict:
    """Skrip anotasi Ghidra / IDA / x64dbg dari RE Lab. Mengembalikan {"ok", "fmt", "content", "functions", "comments", "path"?}. Tidak pernah melempar."""
    try:
        fmt = str(fmt).lower()
        if fmt not in ("ghidra", "ida", "x64dbg"):
            return {"ok": False, "error": "format harus ghidra, ida, atau x64dbg"}
        a = _ann_collect(path)
        if "error" in a:
            return {"ok": False, "error": a["error"]}
        name = os.path.basename(str(path))
        if fmt == "x64dbg":
            mod = name.lower()
            rva = lambda va: "0x%X" % max(0, va - a["base"])
            content = json.dumps({"labels": [{"module": mod, "address": rva(v), "manual": True, "text": n} for v, n in a["funcs"]],
                                  "comments": [{"module": mod, "address": rva(v), "manual": True, "text": t} for v, t in a["cmts"]]}, indent=1)
        else:
            tpl = _ANN_GHIDRA if fmt == "ghidra" else _ANN_IDA
            lit = lambda o: json.dumps(o, ensure_ascii=True, separators=(",", ":"))
            content = tpl % {"ver": VERSION, "src": _ann_txt(name, 80), "arch": _ann_txt(a["arch"], 60), "base": "0x%X" % a["base"],
                             "funcs": lit([[v, n] for v, n in a["funcs"]]), "cmts": lit([[v, t] for v, t in a["cmts"]])}
        r = {"ok": True, "fmt": fmt, "content": content, "functions": len(a["funcs"]), "comments": len(a["cmts"])}
        if out:
            p = Path(out)
            if p.is_dir() or str(out).endswith(("/", "\\")):
                p = Path(out) / (name + ".rea." + ("json" if fmt == "x64dbg" else "py"))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8", newline="\n")
            r["path"] = str(p)
        return r
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def export_text(path, fmt: str = "ghidra", out=None) -> str:
    r = export_annotations(path, fmt, out)
    if not r["ok"]:
        return "EKSPOR gagal: " + r["error"]
    return "EKSPOR %s: %d fungsi, %d komentar%s" % (r["fmt"], r["functions"], r["comments"], (" -> " + r["path"]) if r.get("path") else
                                                  "\n(tambahkan OUT untuk menyimpan; tanpa itu isi berkas tidak ditulis)")


def _fd_sigs(path) -> dict:
    info, ctx, err = _relab_ctx(path)
    if not ctx:
        raise ValueError((err or "tidak bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64, serta ELF / Mach-O AArch64")
    out = {}
    for va, fo in list(ctx["F"].items())[:FDIFF_MAX_FUNCS * 4]:
        if va in ctx["thunks"]:
            continue
        feats = frozenset(["a:" + k for k in fo["apis"]] + ["s:" + _ann_txt(x, 60).lower() for x in fo["strings"]])
        out[va] = {"va": va, "name": fo["name"], "size": fo["size"], "nc": len(fo["callees"]), "feats": feats}
        if len(out) >= FDIFF_MAX_FUNCS:
            break
    return out


def _fd_score(x: dict, y: dict) -> float:
    u = len(x["feats"] | y["feats"])
    j = len(x["feats"] & y["feats"]) / u if u else (1.0 if x["nc"] == y["nc"] else 0.0)
    sz = min(x["size"], y["size"]) / max(x["size"], y["size"], 1)
    return round(0.7 * j + 0.3 * sz, 3)


def func_diff(path_a, path_b) -> dict:
    """Diff fungsi antar-dua biner (statis). Tidak pernah melempar. Lihat komentar v99.15 untuk metode dan batasan."""
    try:
        A, B = _fd_sigs(path_a), _fd_sigs(path_b)
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:140])}
    t0 = time.monotonic()
    pairs: list[tuple[int, int, float, str]] = []
    ua, ub = set(A), set(B)
    named = {}
    for vb, y in B.items():
        if not y["name"].startswith("sub_"):
            named.setdefault(y["name"], vb)
    for va, x in A.items():
        if not x["name"].startswith("sub_") and x["name"] in named and named[x["name"]] in ub:
            vb = named[x["name"]]
            pairs.append((va, vb, _fd_score(x, B[vb]), "nama"))
            ua.discard(va)
            ub.discard(vb)
    ea: dict[tuple, list] = {}
    eb: dict[tuple, list] = {}
    for va in ua:
        if A[va]["feats"]:
            ea.setdefault((A[va]["feats"], A[va]["size"], A[va]["nc"]), []).append(va)
    for vb in ub:
        if B[vb]["feats"]:
            eb.setdefault((B[vb]["feats"], B[vb]["size"], B[vb]["nc"]), []).append(vb)
    for k, la in ea.items():   # tanda tangan persis sama (fitur + ukuran + callee): pasangkan menurut urutan alamat
        for va, vb in zip(sorted(la), sorted(eb.get(k, []))):
            pairs.append((va, vb, 1.0, "fitur"))
            ua.discard(va)
            ub.discard(vb)
    inv: dict[str, list[int]] = {}
    for vb in ub:
        for ft in B[vb]["feats"]:
            inv.setdefault(ft, []).append(vb)
    cand = []
    partial = False
    for va in ua:
        if time.monotonic() - t0 > FDIFF_TIME:
            partial = True
            break
        seen: dict[int, int] = {}
        for ft in A[va]["feats"]:
            lst = inv.get(ft, ())
            if len(lst) <= 60:
                for vb in lst:
                    seen[vb] = seen.get(vb, 0) + 1
        for vb in sorted(seen, key=lambda k: -seen[k])[:8]:
            cand.append((_fd_score(A[va], B[vb]), va, vb))
    for sc, va, vb in sorted(cand, key=lambda c: (-c[0], c[1], c[2])):
        if sc >= 0.6 and va in ua and vb in ub:
            pairs.append((va, vb, sc, "fitur"))
            ua.discard(va)
            ub.discard(vb)
    ga: dict[tuple, list] = {}
    gb: dict[tuple, list] = {}
    for va in ua:
        if not A[va]["feats"]:
            ga.setdefault((A[va]["size"], A[va]["nc"]), []).append(va)
    for vb in ub:
        if not B[vb]["feats"]:
            gb.setdefault((B[vb]["size"], B[vb]["nc"]), []).append(vb)
    for k, la in ga.items():   # fungsi tanpa API / string: cocok hanya bila jumlah per (ukuran, callee) sama; urut menurut alamat
        lb = gb.get(k, [])
        if len(la) == len(lb):
            for va, vb in zip(sorted(la), sorted(lb)):
                pairs.append((va, vb, _fd_score(A[va], B[vb]), "ukuran"))
                ua.discard(va)
                ub.discard(vb)
    same = [p for p in pairs if p[2] >= 0.999 and A[p[0]]["size"] == B[p[1]]["size"]]
    chg = sorted([p for p in pairs if p not in same], key=lambda p: (p[2], p[0]))
    row = lambda S, v: {"va": "0x%X" % v, "name": _clean(S[v]["name"]), "size": S[v]["size"]}
    return {"ok": True, "partial": partial, "a": {"funcs": len(A)}, "b": {"funcs": len(B)}, "identical": len(same), "weak": sum(1 for p in same if p[3] == "ukuran"),
            "changed": [{"a": row(A, p[0]), "b": row(B, p[1]), "sim": p[2], "by": p[3]} for p in chg],
            "removed": [row(A, v) for v in sorted(ua)], "added": [row(B, v) for v in sorted(ub)]}


def func_diff_text(path_a, path_b, max_items: int = 15) -> str:
    r = func_diff(path_a, path_b)
    if not r["ok"]:
        return "FUNCDIFF gagal: " + r["error"]
    L = ["FUNCDIFF: A %d fungsi, B %d fungsi | sama %d (%d hanya dari ukuran), berubah %d, hilang di B %d, baru di B %d%s" % (
        r["a"]["funcs"], r["b"]["funcs"], r["identical"], r["weak"], len(r["changed"]), len(r["removed"]), len(r["added"]),
        " | TERPOTONG (batas waktu)" if r["partial"] else "")]
    for c in r["changed"][:max_items]:
        L.append("   berubah (%.2f, %s): %s %s (%dB) -> %s %s (%dB)" % (c["sim"], c["by"], c["a"]["name"], c["a"]["va"], c["a"]["size"], c["b"]["name"], c["b"]["va"], c["b"]["size"]))
    for k, lab in (("removed", "hilang"), ("added", "baru")):
        for x in r[k][:max_items // 3 or 1]:
            L.append("   %s: %s %s (%dB)" % (lab, x["name"], x["va"], x["size"]))
    return "\n".join(L)


_API_ACTIONS = ("export", "funcdiff", "sigcheck", "reputation", "unpack7z", "capabilities", "cache", "triage", "json", "ioc", "yara", "md", "similar", "hex", "compare", "list", "extract", "dir", "ctph", "re", "xref", "disasm", "unpack", "yarascan", "assets", "assets_extract", "assets_carve", "formats", "dex", "dotnet", "cfg", "emu", "config", "deobf", "unity", "unity_extract", "unzstd")


_DEFAULT_ROOTS: list = []     # diisi pemanggil tepercaya (server.py) lewat set_default_roots(); dipakai bila env REA_ROOTS kosong


def set_default_roots(roots) -> list:
    """Akar bawaan untuk rea_api bila env REA_ROOTS kosong. Dipanggil server.py saat start supaya pembatas aktif tanpa bergantung pada .env.
    Env REA_ROOTS yang diisi manual tetap menang. Daftar kosong / None = tanpa batas bawaan. Mengembalikan daftar akar yang berlaku."""
    _DEFAULT_ROOTS[:] = [str(x) for x in (roots or []) if str(x).strip()]
    return _roots()


def _roots() -> list:
    """Akar yang berlaku: env REA_ROOTS (dipisah os.pathsep) kalau diisi, kalau tidak akar bawaan dari set_default_roots()."""
    env = [x for x in os.environ.get("REA_ROOTS", "").split(os.pathsep) if x.strip()]
    return env or list(_DEFAULT_ROOTS)


def _api_aes_files(v):
    """v99.55: `aes_file` API: satu berkas atau daftar berkas kunci, tiap path lewat pembatas path; kosong -> None."""
    if not v:
        return None
    return [_api_path(x) for x in v] if isinstance(v, (list, tuple)) else _api_path(v)


def _api_path(p) -> Path:
    """Jika REA_ROOTS / akar bawaan ada, hanya path di bawah akar itu yang boleh dibaca / ditulis. Pesan galat seragam untuk semua aksi."""
    pp = Path(str(p)).expanduser().resolve()
    roots = _roots()
    if roots and not any(pp == Path(r).resolve() or Path(r).resolve() in pp.parents for r in roots):
        raise PermissionError("path di luar REA_ROOTS: %s (hanya boleh di bawah: %s)" % (pp.name[:80], "; ".join(Path(r).name or str(r) for r in roots)[:160]))
    return pp


def _api_outdir(p) -> Path:
    """Seperti _api_path, tetapi untuk TUJUAN TULIS (outdir). Fail-closed: tanpa REA_ROOTS / akar bawaan, agen tidak boleh menulis ke mana pun."""
    if not _roots():
        raise PermissionError("penulisan lewat API ditolak: REA_ROOTS / set_default_roots() belum diatur (outdir harus berada di bawah akar yang diizinkan)")
    return _api_path(p)


def rea_api(request) -> dict:
    """Satu pintu JSON untuk agen. request: dict atau string JSON, contoh {"action": "triage", "path": "x.exe", "compact": true}.
    Selalu mengembalikan dict {"ok": bool, ...}; tidak pernah melempar. Aksi: lihat _API_ACTIONS."""
    try:
        req = json.loads(request) if isinstance(request, (str, bytes)) else dict(request)
        act = str(req.get("action", "")).lower()
        mc = max(0, int(req.get("max_chars", 12000)))
        trim = lambda t: t if not mc or len(t) <= mc else t[:mc - 30] + "\n[...dipangkas supaya muat...]"
        if act == "capabilities":
            return {"ok": True, "version": VERSION, "actions": list(_API_ACTIONS), "rea_extract": _extract_mod() is not None,
                    "rea_binary": _has_binary(), "rea_assets": _assets_mod() is not None, "roots_restricted": bool(_roots()),
                    "cache": _cache_dir() is not None, "sigcheck_crypto": importlib.util.find_spec("cryptography") is not None,
                    "optional_deps": {m_: importlib.util.find_spec(m_) is not None for m_ in ("PIL", "texture2ddecoder", "lz4", "lief", "capstone", "UnityPy")},
                    "online_enabled": os.environ.get("REA_ONLINE", "").strip() == "1", "vt_key_set": bool(os.environ.get("REA_VT_KEY", "").strip()),
                    "sevenzip": any(__import__("shutil").which(x) for x in ("7zz", "7z", "7za", "7zr")), "zstd_pure": True}
        if act == "cache":
            return {"ok": True, "action": act, "info": cache_info()}
        if act == "triage":
            p = _api_path(req["path"])
            if p.is_dir():
                return {"ok": True, "action": act, "text": trim(triage_dir_text(str(p), defang=bool(req.get("defang", True))))}
            rep = triage(p, use_cache=not req.get("nocache"))
            return {"ok": True, "action": act, "cached": bool(rep.get("cached")), "score": rep["score"], "level": rep["level"], "sha256": rep["sha256"], "kind": rep["kind"],
                    "text": trim(render(rep, compact=bool(req.get("compact", False)), defang=bool(req.get("defang", True)), max_chars=mc, card=bool(req.get("card", False))))}
        if act in ("json", "ioc"):
            return {"ok": True, "action": act, "data": json.loads(triage_json(_api_path(req["path"]), ioc_only=act == "ioc"))}
        if act == "yara":
            return {"ok": True, "action": act, "text": yara_draft(triage(_api_path(req["path"]), fuzzy=False))}
        if act == "md":
            return {"ok": True, "action": act, "text": trim(triage_md(_api_path(req["path"]), defang=bool(req.get("defang", True))))}
        if act == "ctph":
            data, _sz = _read_sample(_api_path(req["path"]))
            return {"ok": True, "action": act, "ctph": ctph(data), "sample": len(data)}
        if act == "similar":
            return {"ok": True, "action": act, "data": similarity(_api_path(req["a"]), _api_path(req["b"]))}
        if act == "hex":
            return {"ok": True, "action": act, "text": trim(hex_text(_api_path(req["path"]), int(req.get("offset", 0)), int(req.get("length", 256))))}
        if act == "compare":
            return {"ok": True, "action": act, "text": trim(compare_text(_api_path(req["a"]), _api_path(req["b"])))}
        if act == "list":
            return {"ok": True, "action": act, "text": trim(container_text(_api_path(req["path"]), max_chars=mc, dict_path=_api_path(req["dict"]) if req.get("dict") else None))}
        if act == "extract":
            m = container_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), pattern=req.get("pattern"), scan=bool(req.get("scan", False)), dict_path=_api_path(req["dict"]) if req.get("dict") else None)
            return {"ok": m.get("status") == "success", "action": act, "manifest": m}
        if act == "re":
            p = _api_path(req["path"])
            return {"ok": True, "action": act, "data": re_lab_path(p), "text": trim(re_text(p, defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "xref":
            return {"ok": True, "action": act, "text": trim(xref_text(_api_path(req["path"]), str(req["query"])))}
        if act == "disasm":
            return {"ok": True, "action": act, "text": trim(disasm_text(_api_path(req["path"]), req.get("at", "entry"), int(req.get("count", 40)), req.get("arch")))}
        if act == "unpack":
            return {"ok": True, "action": act, "text": trim(unpack_text(_api_path(req["path"]), _api_outdir(req["outdir"])))}
        if act == "yarascan":
            return {"ok": True, "action": act, "text": trim(yara_text(_api_path(req["path"]), _api_path(req["rules"])))}
        if act == "dir":
            return {"ok": True, "action": act, "text": trim(triage_dir_text(str(_api_path(req["path"])), defang=bool(req.get("defang", True))))}
        if act == "emu":
            return {"ok": True, "action": act, "text": trim(emu_text(_api_path(req["path"]), req.get("at"), defang=bool(req.get("defang", True))))}
        if act == "deobf":
            return {"ok": True, "action": act, "text": trim(deobf_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), full=bool(req.get("full", False))))}
        if act == "config":
            if req.get("json"):
                return {"ok": True, "action": act, **extract_config(_api_path(req["path"]), keys=req.get("keys"), reveal=bool(req.get("reveal", False)))}
            return {"ok": True, "action": act, "text": trim(config_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), keys=req.get("keys")))}
        if act == "cfg":
            return {"ok": True, "action": act, "text": trim(cfg_text(_api_path(req["path"]), req.get("at")))}
        if act == "dotnet":
            return {"ok": True, "action": act, "text": trim(net_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "dex":
            return {"ok": True, "action": act, "text": trim(dex_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "assets":
            return {"ok": True, "action": act, "text": trim(assets_text(_api_path(req["path"]), max_chars=mc, dict_path=_api_path(req["dict"]) if req.get("dict") else None, aes_key=req.get("aes"), aes_file=_api_aes_files(req.get("aes_file"))))}
        if act == "unity":
            return {"ok": True, "action": act, "data": unity_info(_api_path(req["path"])), "text": trim(unity_text(_api_path(req["path"])))}
        if act == "unity_extract":
            m = unity_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), types=req.get("types"), name=req.get("name"), flip=bool(req.get("flip", True)))
            return {"ok": m.get("status") in ("success", "partial"), "action": act, "manifest": m}
        if act == "unzstd":
            p_ = _api_path(req["path"])
            op_ = None
            if req.get("outdir"):
                op_ = _api_outdir(req["outdir"]) / (p_.stem if p_.suffix.lower() == ".zst" else p_.name + ".out")
            r_ = unzstd(p_, op_, max_out=req.get("max_out"), force=bool(req.get("force", False)), dict_path=_api_path(req["dict"]) if req.get("dict") else None)
            return {"ok": bool(r_.get("ok")), "action": act, "data": r_, "text": trim(unzstd_text(p_, None))}
        if act == "assets_extract":
            m = assets_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), pattern=req.get("pattern"), convert=bool(req.get("convert", True)), dict_path=_api_path(req["dict"]) if req.get("dict") else None, aes_key=req.get("aes"), aes_file=_api_aes_files(req.get("aes_file")))
            return {"ok": m.get("status") in ("success", "partial"), "action": act, "manifest": m}
        if act == "assets_carve":
            od = _api_outdir(req["outdir"]) if req.get("outdir") else None
            m = assets_carve(_api_path(req["path"]), od)
            return {"ok": m.get("status") == "success", "action": act, "result": m}
        if act == "export":
            r = export_annotations(_api_path(req["path"]), req.get("fmt", "ghidra"), _api_outdir(req["outdir"]) if req.get("outdir") else None)
            r.pop("content", None)
            return {"ok": bool(r.get("ok")), "action": act, "result": r}
        if act == "funcdiff":
            return {"ok": True, "action": act, "text": trim(func_diff_text(_api_path(req["path"]), _api_path(req["path2"]))), "data": func_diff(_api_path(req["path"]), _api_path(req["path2"]))}
        if act == "sigcheck":
            notes: list = []
            r = sig_check(_api_path(req["path"]), online=_api_online(req, notes))
            if isinstance(r.get("notes"), list):
                r["notes"].extend(notes)
            txt = sig_text(_api_path(req["path"]), online=_api_online(req)) if r.get("ok") else "TANDA TANGAN: " + r.get("error", "gagal")
            return {"ok": bool(r.get("ok")), "action": act, "data": r, "text": trim(txt + ("".join("\nCatatan: " + n for n in notes)))}
        if act == "reputation":
            notes = []
            tgt = str(req["target"]).strip()
            tgt = tgt if re.fullmatch(r"[0-9a-fA-F]{64}", tgt) else str(_api_path(tgt))
            on = _api_online(req, notes)
            r = reputation(tgt, online=on)
            return {"ok": bool(r.get("ok")), "action": act, "data": r, "text": trim(reputation_text(tgt, online=on) + ("".join("\nCatatan: " + n for n in notes)))}
        if act == "unpack7z":
            return {"ok": True, "action": act, "text": trim(unpack_7z_text(_api_path(req["path"]), _api_outdir(req["outdir"])))}
        if act == "formats":
            mod = _assets_mod()
            return {"ok": mod is not None, "action": act, "formats": mod.formats() if mod else []}
        return {"ok": False, "error": "aksi tidak dikenal: %s" % act[:40], "actions": list(_API_ACTIONS)}
    except PermissionError as e:
        return {"ok": False, "error": str(e)[:200]}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def _has_binary() -> bool:
    return True   # Binary Workbench sudah digabung ke berkas ini (23 Nov 2026)


# ---------------------------------------------------------------------------
# v95: jembatan ke mesin ekstraksi (rea_extract.py). Impor malas: triase tetap jalan walau modul itu tidak ada.
# ---------------------------------------------------------------------------


def _extract_mod():
    """Mesin ekstraksi container (dulu rea_extract.py, digabung 23 Nov 2026); fasad dari bagian bawah berkas ini."""
    return _EX_API


def container_text(path, max_chars: int = 0, dict_path=None) -> str:
    """Daftar isi container (ZIP/TAR/GZIP/ISO/PSP ISO), hanya-baca. Gagal -> pesan, tidak melempar. dict_path (v99.52): dictionary Zstd untuk .zst / .tar.zst."""
    mod = _extract_mod()
    if mod is None:
        return "Mesin ekstraksi (rea_extract.py) tidak ditemukan di folder yang sama; fitur isi container tidak tersedia."
    try:
        zd = _zstd_load_dict(dict_path) if dict_path else None
        return mod.describe_container_text(path, max_chars=max_chars, zstd_dict=zd)
    except Exception as e:
        return "CONTAINER gagal dibaca (%s: %s)." % (type(e).__name__, str(e)[:120])


def container_extract(path, outdir, pattern=None, scan: bool = False, dict_path=None) -> dict:
    """Ekstraksi selektif ke workspace outdir (extracted/, manifests/, logs/). Mengembalikan manifest (dict). dict_path (v99.52): dictionary Zstd untuk .zst / .tar.zst."""
    mod = _extract_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_extract.py tidak ditemukan"}
    try:
        zd = _zstd_load_dict(dict_path) if dict_path else None
    except (ValueError, OSError) as e:
        return {"status": "error", "code": "bad_dictionary", "message": "dictionary tidak bisa dibaca: %s" % _as_clean(e, 160)}
    r = mod.open_container(path, zstd_dict=zd)
    if r.get("status") != "success":
        return r
    try:
        return mod.extract_selected(r["container_id"], {"pattern": pattern} if pattern else None, outdir, scan=scan)
    finally:
        mod.close_container(r["container_id"])


