# rea_triage bagian 26/47: capa_upx (baris asli 10966-11113). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v98.2: aturan kemampuan berbasis nama API, diturunkan dari mandiant/capa-rules (Apache-2.0, https://github.com/mandiant/capa-rules).
# Hanya aturan yang murni daftar API (or / and) dan punya pemetaan ATT&CK yang dipilih; aturan capa lain butuh analisis aliran kode.
# Dicocokkan di tingkat BERKAS (bukan fungsi), jadi tetap PETUNJUK. Tidak masuk skor. Atribusi: lihat NOTICE di docstring modul.
# (nama aturan, namespace, ATT&CK, operator, himpunan API huruf kecil)
# ---------------------------------------------------------------------------

_CAPA_RULES = (
    ('acquire credentials from Windows Credential Manager', 'collection', ('T1555.004',), 'or', ('credenumerate',)),
    ('get geographical location', 'collection', ('T1614',), 'or', ('getlocaleinfo', 'getlocaleinfoex', 'getusergeoid', 'getgeoinfo')),
    ('register raw input devices', 'collection/keylog', ('T1056.001',), 'or', ('registerrawinputdevices',)),
    ('log keystrokes via direct input', 'collection/keylog', ('T1056.001',), 'or', ('directinput8create', 'directinputcreateex', 'directinputcreatew', 'directinputcreatea')),
    ('log keystrokes via polling', 'collection/keylog', ('T1056.001',), 'or', ('getasynckeystate', 'getkeystate', 'getkeyboardstate', 'vkkeyscan', 'vkkeyscanex', 'getkeynametext')),
    ('get domain trust relationships', 'collection/network', ('T1482',), 'or', ('dsenumeratedomaintrusts',)),
    ('capture microphone audio', 'collection/microphone', ('T1123',), 'or', ('waveinopen', 'waveinaddbuffer', 'waveinstart')),
    ('clear Windows event logs remotely', 'anti-analysis/anti-forensic/clear-logs', ('T1070.001',), 'and', ('evtopensession', 'evtclearlog')),
    ('encrypt data using RC4 via SystemFunction033', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction033',)),
    ('encrypt data using RC4 via SystemFunction032', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction032',)),
    ('impersonate user', 'host-interaction/user', ('T1134.001',), 'or', ('logonuser',)),
    ('get UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('ntenumeratesystemenvironmentvaluesex', 'ntquerysystemenvironmentvalueex', 'ntquerysystemenvironmentvalue', 'getfirmwareenvironmentvariable', 'getfirmwareenvironmentvariableex', 'exgetfirmwareenvironmentvariable')),
    ('set UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('exsetfirmwareenvironmentvariable', 'setfirmwareenvironmentvariable', 'setfirmwareenvironmentvariableex')),
    ('switch active desktop', 'host-interaction/gui', ('T1622',), 'and', ('createdesktop', 'switchdesktop')),
    ('attach user process memory', 'host-interaction/process/inject', ('T1055',), 'and', ('kestackattachprocess', 'keunstackdetachprocess')),
    ('install driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntloaddriver', 'zwloaddriver')),
    ('unload driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntunloaddriver', 'zwunloaddriver')),
    ('delete network filter via WFP API', 'host-interaction/network/traffic/filter', ('T1565.002', 'T1562.004'), 'or', ('fwpmfilterdeletebyid0', 'fwpmfilterdeletebykey0')),
    ('shutdown system', 'host-interaction/os', ('T1529',), 'or', ('exitwindowsex', 'exitwindows', 'initiatesystemshutdownex', 'initiatesystemshutdown', 'initiateshutdown')),
)


_CAPA_SETS = [(n, ns, att, op, frozenset(apis)) for n, ns, att, op, apis in _CAPA_RULES]


def _capa_match(api_names) -> list[dict]:
    """Cocokkan nama impor dengan aturan capa bawaan. 'or': minimal satu API; 'and': semua API harus ada."""
    out = []
    names = [str(a) for a in api_names]
    if not names:
        return out
    for n, ns, att, op, S in _CAPA_SETS:
        hit = sorted({x.split("!")[-1] for x in names if _api_match(x, S)})
        if not hit:
            continue
        if op == "and" and len({h.lower() for h in hit}) < len(S):
            continue
        out.append({"name": n, "namespace": ns, "attack": list(att), "apis": hit[:6]})
    return out


def _capa_enrich(rep: dict, api_names) -> None:
    try:
        rep["capa"] = _capa_match(api_names)
    except Exception as e:
        rep["capa"] = []
        rep["warn"].append("aturan capa gagal: %s" % type(e).__name__)


def _render_capa(rep: dict, a, compact: bool) -> None:
    c = rep.get("capa")
    if not c:
        return
    a("Aturan capa (subset berbasis API, tingkat berkas; PETUNJUK, bukan bukti perilaku): %d cocok" % len(c))
    for x in c[: (3 if compact else 20)]:
        a("   - %s [%s] <- %s" % (_clean(x["name"]), ", ".join(x["attack"]), ", ".join(_clean(h) for h in x["apis"])))


# ---------------------------------------------------------------------------
# v98.2: unpack UPX statis lewat `upx -d` (opsional; hanya bila alat `upx` terpasang). Berkas TIDAK dijalankan: `upx -d` hanya
# mendekompresi. Dikerjakan pada salinan sementara dengan batas waktu dan ukuran; hasil disimpan di outdir lalu ditriase.
# ---------------------------------------------------------------------------

UNPACK_MAX = 256 * 1024 * 1024
UNPACK_TIMEOUT = 40
UNPACK_MEM = 1536 * 1024 * 1024      # batas memori proses upx (RLIMIT_AS, hanya POSIX)


def _upx_limits():
    """preexec_fn untuk POSIX: batasi memori, waktu CPU, dan ukuran berkas yang boleh ditulis upx. Pada Windows tidak ada (None);
    di sana batas ukuran hasil tetap diperiksa setelah upx selesai, dan timeout tetap berlaku."""
    if os.name != "posix":
        return None

    def _apply():
        import resource
        for lim, val in ((resource.RLIMIT_AS, UNPACK_MEM), (resource.RLIMIT_CPU, UNPACK_TIMEOUT + 5),
                         (resource.RLIMIT_FSIZE, UNPACK_MAX + (1 << 20)), (resource.RLIMIT_CORE, 0)):
            try:
                resource.setrlimit(lim, (val, val))
            except (ValueError, OSError):
                pass
    return _apply


def unpack_upx(path, outdir) -> dict:
    import shutil
    import subprocess
    import tempfile
    try:
        upx = shutil.which("upx")
        if not upx:
            return {"ok": False, "error": "alat 'upx' tidak ditemukan di PATH (pasang UPX dari https://upx.github.io lalu coba lagi)"}
        f, size = _open_regular(path)
        if size > UNPACK_MAX:
            f.close()
            return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
        out = Path(outdir).expanduser().resolve()
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.bin"
            dst = Path(td) / "out.bin"
            found, tail, left = False, b"", size
            with f, open(src, "wb") as sf:           # salin bertahap (tanpa memuat seluruh berkas), sambil mencari penanda UPX
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    left -= len(chunk)
                    sf.write(chunk)
                    if not found:
                        win = tail + chunk
                        found = b"UPX!" in win or b"UPX0" in win
                        tail = win[-3:]
            if not found:
                return {"ok": False, "error": "tidak ada penanda UPX di berkas; tidak dicoba"}
            out.mkdir(parents=True, exist_ok=True)
            r = subprocess.run([upx, "-d", "-q", "-o", str(dst), str(src)], capture_output=True, timeout=UNPACK_TIMEOUT,
                               stdin=subprocess.DEVNULL, cwd=td, env={"PATH": os.environ.get("PATH", ""), "LANG": "C"},
                               preexec_fn=_upx_limits())
            if r.returncode != 0 or not dst.exists():
                return {"ok": False, "error": "upx -d gagal: " + _clean(r.stderr.decode("latin-1", "replace"))[:200]}
            if dst.stat().st_size > UNPACK_MAX:
                return {"ok": False, "error": "hasil unpack melebihi batas %d MB; dibuang" % (UNPACK_MAX >> 20)}
            data = dst.read_bytes()
        name = "%s.unpacked" % (hashlib.sha256(data).hexdigest()[:16])
        (out / name).write_bytes(data)
        return {"ok": True, "path": str(out / name), "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "upx -d melewati batas waktu %d detik" % UNPACK_TIMEOUT}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def unpack_text(path, outdir) -> str:
    r = unpack_upx(path, outdir)
    if not r["ok"]:
        return "UNPACK gagal: " + r["error"]
    return "UNPACK UPX berhasil: %s (%s, sha256 %s)\n%s" % (r["path"], _human(r["size"]), r["sha256"], triage_text(r["path"], compact=True))


