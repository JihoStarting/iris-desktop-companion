# rea_triage bagian 10/47: ctph (baris asli 4001-4143). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- CTPH (hash fuzzy gaya ssdeep) ----------------

_B64C = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CTPH_SAMPLE = 1024 * 1024


def _spamsum(data: bytes, bs: int) -> tuple[str, str]:
    h1 = h2 = h3 = 0
    win = [0] * 7
    n = 0
    bh1 = bh2 = 0x28021967
    s1, s2 = [], []
    M = 0xFFFFFFFF
    b2 = bs * 2
    r = 0
    for c in data:
        bh1 = ((bh1 * 0x01000193) ^ c) & M
        bh2 = ((bh2 * 0x01000193) ^ c) & M
        h2 = (h2 - h1 + 7 * c) & M
        h1 = (h1 + c - win[n % 7]) & M
        win[n % 7] = c
        n += 1
        h3 = ((h3 << 5) ^ c) & M
        r = (h1 + h2 + h3) & M
        if r % bs == bs - 1 and len(s1) < 63:
            s1.append(_B64C[bh1 & 63])
            bh1 = 0x28021967
        if r % b2 == b2 - 1 and len(s2) < 31:
            s2.append(_B64C[bh2 & 63])
            bh2 = 0x28021967
    if r:
        s1.append(_B64C[bh1 & 63])
        s2.append(_B64C[bh2 & 63])
    return "".join(s1), "".join(s2)


def ctph(data: bytes) -> str:
    """Hash fuzzy (context-triggered piecewise hashing, algoritma spamsum). Format 'blok:digest1:digest2'.
    Dapat dibandingkan dengan ctph_compare(); bukan jaminan identik dengan keluaran ssdeep resmi."""
    n = len(data)
    if n < 64:
        return ""
    bs = 3
    while bs * 64 < n:
        bs *= 2
    while True:
        s1, s2 = _spamsum(data, bs)
        if bs > 3 and len(s1) < 32:
            bs //= 2
            continue
        return "%d:%s:%s" % (bs, s1, s2)


def _squeeze(s: str) -> str:
    return re.sub(r"(.)\1{3,}", r"\1\1\1", s)


def _ssd_one(a: str, b: str, bs: int) -> int:
    if len(a) < 7 or len(b) < 7:
        return 0
    if not any(a[i:i + 7] in b for i in range(len(a) - 6)):
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 2)))
        prev = cur
    score = prev[-1] * 64 // (len(a) + len(b))
    score = 100 - (100 * score // 64)
    if bs < 45:
        score = min(score, bs // 3 * min(len(a), len(b)))
    return max(0, min(100, score))


def ctph_compare(x: str, y: str) -> int:
    """Skor kemiripan 0-100 antara dua digest ctph(); 0 = tidak ada kemiripan berarti atau blok tak sebanding."""
    try:
        bx, ax1, ax2 = x.split(":", 2)
        by, ay1, ay2 = y.split(":", 2)
        bx, by = int(bx), int(by)
    except ValueError:
        return 0
    ax1, ax2, ay1, ay2 = _squeeze(ax1), _squeeze(ax2), _squeeze(ay1), _squeeze(ay2)
    if bx == by:
        if ax1 == ay1 and ax2 == ay2:
            return 100
        return max(_ssd_one(ax1, ay1, bx), _ssd_one(ax2, ay2, bx * 2))
    if bx == by * 2:
        return _ssd_one(ax1, ay2, bx)
    if by == bx * 2:
        return _ssd_one(ax2, ay1, by)
    return 0


def _read_sample(path, n: int = CTPH_SAMPLE) -> tuple[bytes, int]:
    f, size = _open_regular(path)
    with f:
        return f.read(n), size


def similarity(path_a, path_b) -> dict:
    """Bandingkan dua berkas: hash identik, skor CTPH, imphash, rich hash, irisan bagian PE (MD5), irisan string menarik."""
    da, sa = _read_sample(path_a)
    db, sb = _read_sample(path_b)
    ra, rb = triage(path_a, fuzzy=False), triage(path_b, fuzzy=False)
    ca, cb = ctph(da), ctph(db)
    out = {"a": Path(path_a).name, "b": Path(path_b).name, "size_a": sa, "size_b": sb, "identical": ra["sha256"] == rb["sha256"],
           "ctph_a": ca, "ctph_b": cb, "ctph_score": ctph_compare(ca, cb) if ca and cb else 0}
    pa, pb = ra.get("pe"), rb.get("pe")
    if pa and pb and not pa.get("broken") and not pb.get("broken"):
        out["imphash_same"] = bool(pa.get("imphash")) and pa.get("imphash") == pb.get("imphash")
        out["rich_same"] = bool((pa.get("rich") or {}).get("hash")) and (pa.get("rich") or {}).get("hash") == (pb.get("rich") or {}).get("hash")
        ma = {x["md5"] for x in pa["sections"] if x.get("md5")}
        mb = {x["md5"] for x in pb["sections"] if x.get("md5")}
        out["section_md5_shared"] = len(ma & mb)
        out["sections"] = (len(ma), len(mb))
    ua = set(ra["ind"]["urls"]) | set(ra["ind"]["ips"]) | set(ra["ind"]["pdb"])
    ub = set(rb["ind"]["urls"]) | set(rb["ind"]["ips"]) | set(rb["ind"]["pdb"])
    out["shared_iocs"] = sorted(ua & ub)[:10]
    verdict = "identik" if out["identical"] else ("sangat mirip (kemungkinan varian / keluarga sama)" if out["ctph_score"] >= 70 else
                                                   "ada kemiripan" if out["ctph_score"] >= 30 else "tidak mirip menurut CTPH")
    if not out["identical"] and (out.get("imphash_same") or out.get("rich_same") or out.get("section_md5_shared")) and out["ctph_score"] < 70:
        verdict += "; tetapi struktur PE sama (imphash / rich header / bagian), kemungkinan satu keluarga atau satu toolchain"
    out["verdict"] = verdict
    return out


def similar_text(path_a, path_b) -> str:
    try:
        r = similarity(path_a, path_b)
    except Exception as e:
        return "SIMILARITY gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L = ["KEMIRIPAN: %s vs %s" % (r["a"], r["b"]), "Ukuran : %s vs %s" % (_human(r["size_a"]), _human(r["size_b"])),
         "SHA-256 identik: %s" % ("ya" if r["identical"] else "tidak"), "CTPH   : skor %d/100 (sampel %s pertama)" % (r["ctph_score"], _human(CTPH_SAMPLE))]
    if "imphash_same" in r:
        L.append("PE     : imphash %s | rich header %s | bagian MD5 sama %d dari %d/%d" % ("sama" if r["imphash_same"] else "beda", "sama" if r["rich_same"] else "beda", r["section_md5_shared"], *r["sections"]))
    if r["shared_iocs"]:
        L.append("IOC bersama: " + " | ".join(_df(x, True) for x in r["shared_iocs"][:6]))
    L.append("Kesimpulan (petunjuk, bukan vonis): " + r["verdict"])
    return "\n".join(_clean(x) for x in L)


