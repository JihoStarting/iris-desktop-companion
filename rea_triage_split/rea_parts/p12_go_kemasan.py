# rea_triage bagian 12/47: go_kemasan (baris asli 4256-4457). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- detail kemasan / installer -------------------


# ----------------------------- pemulihan nama fungsi Go (pclntab) ----------
# Murni parsing struktur tabel runtime Go (tanpa dependensi, tanpa menjalankan apa pun). Mendukung pclntab Go 1.2, 1.16, 1.18 dan 1.20+.
# Tabel dicari lewat magic + minLC + ptrSize, lalu dibuktikan dengan membaca nama fungsi pertama; kandidat palsu dibuang.

GO_MAX_FUNCS = 500_000          # batas fungsi yang dibaca (biner Go besar biasanya 5 - 50 ribu)
GO_READ_MAX = 128 << 20         # berkas Go sampai segini dibaca utuh untuk tahap ini (pindai biasa dibatasi MAX_SCAN)
GO_TIME_BUDGET = 3.0            # detik; sisanya dilaporkan sebagai terpotong
_GO_VER = {0xFFFFFFFB: "1.2", 0xFFFFFFFA: "1.16", 0xFFFFFFF0: "1.18", 0xFFFFFFF1: "1.20+"}
_GO_PCLN_RE = re.compile(rb"[\xf0\xf1\xfa\xfb]\xff\xff\xff\x00\x00[\x01\x02\x04][\x04\x08]")
_GO_NAME_OK = re.compile(rb"[\x20-\x7e\x80-\xff]{1,400}\Z")
_GO_NOTABLE_STD = ("os/exec", "net/http", "net", "syscall", "crypto/aes", "crypto/cipher", "crypto/rsa", "crypto/tls", "os/user",
                   "encoding/base64", "compress/gzip", "archive/zip", "plugin", "debug/pe", "golang.org/x/sys/windows")
_GO_NOTABLE_RE = re.compile(r"(?i)ransom|keylog|stealer|socks|ngrok|chisel|mimikatz|cobalt|sliver|merlin|beacon|implant|\bc2\b|reverse(?:shell|proxy)|persist|inject")


def _go_pkg(name: str) -> str:
    i = name.rfind("/")
    j = name.find(".", i + 1)
    return name[:j] if j > 0 else name


def _go_parse_at(d: bytes, off: int, deadline: float):
    """Satu kandidat pclntab di offset berkas `off`. Mengembalikan dict atau None. Tidak pernah membaca di luar `d`."""
    n = len(d)
    if off + 8 > n:
        return None
    magic = struct.unpack_from("<I", d, off)[0]
    ver = _GO_VER.get(magic)
    ps = d[off + 7]
    if ver is None or ps not in (4, 8) or d[off + 6] not in (1, 2, 4):
        return None
    fmt = "<I" if ps == 4 else "<Q"
    hdr = {0xFFFFFFFB: 8 + ps, 0xFFFFFFFA: 8 + 7 * ps}.get(magic, 8 + 8 * ps)
    if off + hdr > n:
        return None

    def rd(o: int) -> int:
        return struct.unpack_from(fmt, d, o)[0]
    nfunc = rd(off + 8)
    if not 0 < nfunc <= GO_MAX_FUNCS * 4:
        return None
    text = 0
    if magic == 0xFFFFFFFB:
        tab, wide, fn_base = off + 8 + ps, True, off
    else:
        if magic == 0xFFFFFFFA:
            fn_base, pcln, wide = off + rd(off + 8 + 2 * ps), rd(off + 8 + 6 * ps), True
        else:
            text, fn_base, pcln, wide = rd(off + 8 + 2 * ps), off + rd(off + 8 + 3 * ps), rd(off + 8 + 7 * ps), False
            fn_base = off + rd(off + 8 + 3 * ps)
        tab = off + pcln
        if pcln > n or fn_base > n:
            return None
    esz = 2 * ps if wide else 8
    if tab + esz * min(nfunc, 4) > n:
        return None

    def name_at(i: int):
        p = tab + i * esz
        if p + esz > n:
            return None
        if wide:
            pc, fo = rd(p), rd(p + ps)
            fp = (off + fo) if magic == 0xFFFFFFFB else (tab + fo)
            if fp + ps + 4 > n:
                return None
            nm = struct.unpack_from("<i", d, fp + ps)[0]
        else:
            eo, fo = struct.unpack_from("<II", d, p)
            pc = text + eo
            fp = tab + fo
            if fp + 8 > n:
                return None
            nm = struct.unpack_from("<i", d, fp + 4)[0]
        q = fn_base + nm if magic != 0xFFFFFFFB else off + nm
        if nm < 0 or q >= n:
            return None
        e = d.find(b"\0", q, min(n, q + 401))
        if e <= q:
            return None
        raw = d[q:e]
        if not _GO_NAME_OK.match(raw):
            return None
        return pc, raw.decode("utf-8", "replace")

    probe = [name_at(i) for i in range(min(nfunc, 12))]
    if sum(1 for x in probe if x) < max(3, len(probe) * 3 // 4):
        return None
    names: list = []
    truncated = nfunc > GO_MAX_FUNCS
    for i in range(min(nfunc, GO_MAX_FUNCS)):
        if (i & 1023) == 0 and time.monotonic() > deadline:
            truncated = True
            break
        r = name_at(i)
        if r:
            names.append(r)
    if len(names) < 3:
        return None
    return {"ver": ver, "bits": ps * 8, "off": off, "nfunc": nfunc, "names": names, "truncated": truncated}


def _go_pclntab(d: bytes, f=None, size: int | None = None):
    """Pulihkan daftar fungsi biner Go dari pclntab. None bila bukan biner Go / tabel tidak ditemukan. Hanya membaca; tidak dijalankan.
    Biner Go sering > MAX_SCAN (tabel nama ada di ujung berkas): kalau `f` dan `size` diberikan dan berkas <= GO_READ_MAX, dibaca utuh untuk tahap ini saja."""
    if not (d.find(b"runtime.gopanic") >= 0 or d.find(b"go.buildid") >= 0 or d.find(b"Go build ID") >= 0 or d.find(b"\xff Go buildinf:") >= 0):
        return None
    partial = bool(size and len(d) < size)
    if partial and f is not None and size <= GO_READ_MAX:
        try:
            f.seek(0)
            full = f.read(size)
            if len(full) == size:
                d, partial = full, False
        except (OSError, MemoryError):
            pass
    deadline = time.monotonic() + GO_TIME_BUDGET
    best = None
    for k, m in enumerate(_GO_PCLN_RE.finditer(d)):
        if k >= 64 or time.monotonic() > deadline:
            break
        try:
            r = _go_parse_at(d, m.start(), deadline)
        except (struct.error, ValueError, OverflowError, MemoryError):
            r = None
        if r and (best is None or len(r["names"]) > len(best["names"])):
            best = r
    if not best:
        return None
    pk: collections.Counter = collections.Counter(_go_pkg(nm) for _pc, nm in best["names"])
    main = [nm for _pc, nm in best["names"] if nm == "main" or nm.startswith("main.")]
    third = [(p, c) for p, c in pk.most_common() if "." in p.split("/")[0] and p != "main"]
    std = {p for p in pk if p != "main" and "." not in p.split("/")[0]}
    notable_std = [p for p in _GO_NOTABLE_STD if p in pk or p in std]
    flagged = sorted({p for p in pk if _GO_NOTABLE_RE.search(p)})[:12]
    entry = {x[1]: x[0] for x in reversed(best["names"])}
    return {"ver": best["ver"], "bits": best["bits"], "off": best["off"], "nfunc": best["nfunc"], "read": len(best["names"]),
            "truncated": best["truncated"], "partial_scan": partial, "n_pkgs": len(pk), "n_main": len(main),
            "main": [{"name": nm[:160], "addr": entry.get(nm, 0)} for nm in main[:60]],
            "third": [[p[:120], c] for p, c in third[:15]], "std": notable_std[:12], "flagged": flagged}


def _pack_details(d: bytes, size: int) -> list[str]:
    out: list[str] = []
    head = d[: 16 * 1024 * 1024]
    k = head.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    if k >= 0 and k + 24 <= len(head):
        pkg, toc, tlen, pyv = struct.unpack_from(">IIII", head, k + 8)
        lib = head[k + 24:k + 88].split(b"\0")[0].decode("ascii", "ignore") if k + 88 <= len(head) else ""
        newer = "python" in lib.lower()
        pyver = ("%d.%d" % (pyv // 100, pyv % 100) if pyv >= 100 else "%d.%d" % (pyv // 10, pyv % 10)) if 20 <= pyv < 1000 else "?"
        line = "PyInstaller %s | Python %s%s | arsip %s" % ("2.1+" if newer else "2.0", pyver, " (%s)" % lib if lib else "", _human(pkg))
        if size == len(d) and 0 < tlen < 4 * 1024 * 1024:
            csz = 88 if newer else 24
            base = size - (pkg + (size - k - csz))
            p, stop = base + toc, base + toc + tlen
            kinds: collections.Counter = collections.Counter()
            scripts: list[str] = []
            while p + 18 <= min(stop, len(d)):
                elen = struct.unpack_from(">I", d, p)[0]
                if elen < 18 or p + elen > len(d):
                    break
                typ = d[p + 17:p + 18].decode("latin-1")
                nm = d[p + 18:p + elen].split(b"\0")[0].decode("utf-8", "replace")
                kinds[typ] += 1
                if typ == "s" and len(scripts) < 6:
                    scripts.append(nm)
                p += elen
            if kinds:
                line += " | %d entri" % sum(kinds.values())
            if scripts:
                line += " | skrip masuk: " + ", ".join(scripts)
        out.append(line)
    m = re.search(rb"\$Id: UPX (\d+\.\d+\w*) Copyright", head)
    if m:
        out.append("UPX %s (unpack: `upx -d`)" % m.group(1).decode("ascii"))
    i = head.find(b"\xef\xbe\xad\xdeNullsoftInst")
    if i >= 0:
        out.append("installer NSIS: header firstheader di offset 0x%X (ekstrak dengan 7-Zip)" % i)
    m = re.search(rb"Inno Setup Setup Data \(([0-9.]{3,12}[^)]{0,16})\)", head)
    if m:
        out.append("Inno Setup versi %s (ekstrak dengan innoextract)" % m.group(1).decode("ascii", "replace"))
    if head.find(b"Go build ID") >= 0 or head.find(b"runtime.gopanic") >= 0:
        m = re.search(rb"\x00(go1\.\d{1,2}(?:\.\d{1,2})?)\x00?", head)
        out.append("Go%s (pulihkan nama fungsi dari pclntab)" % (" " + m.group(1).decode("ascii") if m else ""))
    m = re.search(rb"/rustc/([0-9a-f]{40})", head)
    if m:
        out.append("Rust: kompiler commit %s" % m.group(1).decode("ascii")[:12])
    i = head.find(b"AU3!EA06")
    if i >= 0:
        out.append("AutoIt: skrip terkompilasi (AU3!EA06) di offset 0x%X" % i)
    i = head.find(b";!@Install@!UTF-8!")
    if i >= 0:
        out.append("arsip swa-ekstrak 7-Zip: blok konfigurasi di offset 0x%X (baca perintah RunProgram)" % i)
    if b"pyarmor" in head.lower():
        out.append("PyArmor: skrip Python dilindungi (pyarmor_runtime)")
    return out


