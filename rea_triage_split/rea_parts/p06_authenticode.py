# rea_triage bagian 06/47: authenticode (baris asli 2018-2401). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v98.6: integritas Authenticode, daftar hash lokal, peredam CRT, XOR kunci berulang, resource .NET
# ---------------------------------------------------------------------------

_OID_SPC_INDIRECT = bytes.fromhex("060a2b060104018237020104")
_AC_ALGS = (   # (OID DER lengkap dengan tag + panjang, nama hashlib, ukuran digest)
    (bytes.fromhex("0609608648016503040201"), "sha256", 32),
    (bytes.fromhex("0609608648016503040202"), "sha384", 48),
    (bytes.fromhex("0609608648016503040203"), "sha512", 64),
    (bytes.fromhex("06052b0e03021a"), "sha1", 20),
    (bytes.fromhex("06082a864886f70d0205"), "md5", 16),
)


_OID_NESTED_SIG = bytes.fromhex("060a2b060104018237020401")   # 1.3.6.1.4.1.311.2.4.1 (szOID_NESTED_SIGNATURE)


def _ac_tlv(d, pos: int, end: int):
    """v104: satu TLV DER dengan batas ketat: (tag, awal_isi, akhir_isi) atau None. Panjang tak-tentu / tag tinggi / keluar batas = None."""
    if pos + 2 > end:
        return None
    if d[pos] & 0x1F == 0x1F:
        return None
    b0 = d[pos + 1]
    if b0 < 0x80:
        cs, ln = pos + 2, b0
    else:
        n = b0 & 0x7F
        if n == 0 or n > 4 or pos + 2 + n > end:
            return None
        cs, ln = pos + 2 + n, int.from_bytes(d[pos + 2:pos + 2 + n], "big")
    ce = cs + ln
    if ce > end:
        return None
    return d[pos], cs, ce


def _ac_kids(d, cs: int, ce: int, limit: int = 64):
    """Anak-anak TLV di rentang [cs, ce): [(tag, isi_awal, isi_akhir, tlv_awal)], atau None bila tidak persis habis (sisa byte = tidak sah)."""
    out, p = [], cs
    while p < ce:
        if len(out) >= limit:
            return None
        t = _ac_tlv(d, p, ce)
        if t is None:
            return None
        out.append((t[0], t[1], t[2], p))
        p = t[2]
    return out


def _ac_primary(blob: bytes):
    """v104: digest dari SpcIndirectDataContent di posisi STRUKTURAL yang benar (ContentInfo > [0] > SignedData > encapContentInfo >
    [0] > SpcIndirectDataContent > DigestInfo) lewat parser DER ketat, bukan pencarian byte mentah OID. Mengembalikan (algoritma, digest,
    daftar_signerInfo) atau None bila struktur tidak sah / tidak lengkap."""
    top = _ac_tlv(blob, 0, len(blob))
    if not top or top[0] != 0x30:
        return None
    ci = _ac_kids(blob, top[1], top[2], 4)
    if not ci or len(ci) != 2 or blob[ci[0][3]:ci[0][2]] != bytes.fromhex("06092a864886f70d010702") or ci[1][0] != 0xA0:
        return None   # bukan ContentInfo signedData (1.2.840.113549.1.7.2)
    sd_t = _ac_tlv(blob, ci[1][1], ci[1][2])
    if not sd_t or sd_t[0] != 0x30:
        return None
    sd = _ac_kids(blob, sd_t[1], sd_t[2], 16)
    if not sd or len(sd) < 4 or sd[2][0] != 0x30:
        return None
    enc = _ac_kids(blob, sd[2][1], sd[2][2], 4)
    if not enc or len(enc) != 2 or blob[enc[0][3]:enc[0][2]] != _OID_SPC_INDIRECT or enc[1][0] != 0xA0:
        return None
    spc_t = _ac_tlv(blob, enc[1][1], enc[1][2])
    if not spc_t or spc_t[0] != 0x30:
        return None
    spc = _ac_kids(blob, spc_t[1], spc_t[2], 4)
    if not spc or len(spc) != 2 or spc[1][0] != 0x30:
        return None
    di = _ac_kids(blob, spc[1][1], spc[1][2], 4)
    if not di or len(di) != 2 or di[0][0] != 0x30 or di[1][0] != 0x04:
        return None
    ai = _ac_kids(blob, di[0][1], di[0][2], 4)
    if not ai or ai[0][0] != 0x06 or (len(ai) == 2 and (ai[1][0] != 0x05 or ai[1][1] != ai[1][2])) or len(ai) > 2:
        return None
    oid_tlv = blob[ai[0][3]:ai[0][2]]
    dig = blob[di[1][1]:di[1][2]]
    for oid, name, dsz in _AC_ALGS:
        if oid_tlv == oid:
            return (name, dig, sd[-1]) if len(dig) == dsz and sd[-1][0] == 0x31 else None
    return None


def _ac_nested(blob: bytes, depth: int = 0):
    """Tanda tangan bersarang (unauthenticatedAttributes SignerInfo, OID 1.3.6.1.4.1.311.2.4.1). TIDAK ditandatangani oleh tanda tangan
    utama, jadi penyerang bebas menaruh digest apa pun di sini: hasilnya hanya informasi, tidak pernah menentukan "match"."""
    out: list[tuple[str, bytes]] = []
    if depth >= 2:
        return out
    p = _ac_primary(blob)
    if not p:
        return out
    top = _ac_tlv(blob, 0, len(blob))
    sd_t = _ac_tlv(blob, _ac_kids(blob, top[1], top[2], 4)[1][1], _ac_kids(blob, top[1], top[2], 4)[1][2])
    sd = _ac_kids(blob, sd_t[1], sd_t[2], 16)
    sis = _ac_kids(blob, sd[-1][1], sd[-1][2], 8) or []
    for si in sis:
        kids = _ac_kids(blob, si[1], si[2], 16) or []
        for k in kids:
            if k[0] != 0xA1:
                continue
            for at in (_ac_kids(blob, k[1], k[2], 16) or []):
                parts = _ac_kids(blob, at[1], at[2], 4) or []
                if len(parts) == 2 and blob[parts[0][3]:parts[0][2]] == _OID_NESTED_SIG and parts[1][0] == 0x31:
                    for ci in (_ac_kids(blob, parts[1][1], parts[1][2], 4) or []):
                        sub = blob[ci[3]:ci[2]]
                        pr = _ac_primary(sub)
                        if pr and len(out) < 8:
                            out.append((pr[0], pr[1]))
                            out += _ac_nested(sub, depth + 1)[: max(0, 8 - len(out))]
    return out


def _ac_digests(blob: bytes) -> list[tuple[str, bytes]]:
    """v104: [(algoritma, digest)]: elemen PERTAMA = digest tanda tangan utama (satu-satunya yang boleh menentukan "match"); sisanya
    tanda tangan bersarang (informasi). Daftar kosong bila struktur PKCS#7 tidak bisa diurai ketat."""
    p = _ac_primary(blob)
    if not p:
        return []
    return [(p[0], p[1])] + _ac_nested(blob)


def _authenticode_hash(d: bytes, size: int, pe: dict, alg: str) -> str | None:
    """Hash Authenticode sesuai spesifikasi Microsoft: seluruh berkas KECUALI field CheckSum, entri Certificate Table di data directory, dan
    isi tabel sertifikat. None bila berkas tidak utuh di memori atau tabel section tidak masuk akal."""
    if len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    ck = o + 64
    cdir = o + (112 if is64 else 96) + 8 * 4
    hsz = struct.unpack_from("<I", d, o + 60)[0]
    if cdir + 8 > len(d) or hsz > len(d) or hsz < cdir + 8:
        return None
    c_off, c_sz = struct.unpack_from("<II", d, cdir)
    h = hashlib.new(alg)
    h.update(d[:ck])
    h.update(d[ck + 4:cdir])
    h.update(d[cdir + 8:hsz])
    pos = hsz
    for s in sorted((x for x in pe["sections"] if x["rsize"]), key=lambda x: x["rptr"]):
        a, b = s["rptr"], s["rptr"] + s["rsize"]
        if a < pos or b > len(d):
            return None   # bagian tumpang-tindih / keluar berkas: jangan menebak
        h.update(d[a:b])
        pos = b
    if c_off and c_sz and c_off >= pos:
        h.update(d[pos:c_off])
        h.update(d[c_off + c_sz:])
    else:
        h.update(d[pos:])
    return h.hexdigest()


def _authenticode_check(d: bytes, size: int, pe: dict) -> dict | None:
    """Integritas (BUKAN keabsahan) tanda tangan: digest di blob vs hash isi berkas. match True / False; None bila tidak berlaku.
    Tidak memeriksa rantai sertifikat, masa berlaku, atau pencabutan: itu butuh Get-AuthenticodeSignature / signtool."""
    if not pe.get("signed") or len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    c_off, c_sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 4)
    if c_off + 8 > len(d) or c_sz < 8:
        return None
    end = min(c_off + c_sz, len(d))
    cands: list[tuple[str, bytes]] = []
    pos = c_off
    while pos + 8 <= end:
        dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
        if dw < 8 or pos + dw > end:
            break
        if typ == 2:
            cands = _ac_digests(d[pos + 8:pos + dw])   # v104: hanya entri PKCS#7 PERTAMA; entri tambahan = tanpa wewenang (bisa disisipkan penyerang)
            break
        pos += (dw + 7) & ~7
    if not cands:
        return None
    alg, dig = cands[0]   # v104: hanya digest tanda tangan UTAMA yang menentukan; tanda tangan bersarang tidak ditandatangani tanda tangan utama
    comp = _authenticode_hash(d, size, pe, alg)
    if comp is None:
        return None
    res = {"alg": alg, "signed": dig.hex(), "computed": comp, "match": comp == dig.hex()}
    if not res["match"]:
        for a2, d2 in cands[1:]:
            c2 = comp if a2 == alg else _authenticode_hash(d, size, pe, a2)
            if c2 is not None and c2 == d2.hex():
                res["nested_only_match"] = True   # digest utama tidak cocok tetapi ada digest bersarang yang cocok: pola pemalsuan
                break
    return res


_CO_STOP = frozenset({"corporation", "company", "limited", "software", "technologies", "technology", "group", "holdings", "international",
                      "systems", "solutions", "services", "global", "foundation"})


def _signer_vs_company(pe: dict):
    """True / False: apakah nama penandatangan (CN) memuat kata dari CompanyName. None bila salah satunya tidak ada. Hanya informasi."""
    sg, comp = pe.get("signers") or [], (pe.get("ver") or {}).get("CompanyName", "")
    tok = lambda s: {t for t in re.findall(r"[a-z0-9]{4,}", s.lower())} - _CO_STOP
    a, b = tok(comp), set().union(*(tok(s) for s in sg)) if sg else set()
    if not a or not b:
        return None
    return bool(a & b)


_KNOWN_CACHE: dict = {"key": None, "map": {}}


def _known_hashes() -> dict[str, tuple[str, str]]:
    """Daftar hash lokal dari berkas teks di env REA_KNOWN_HASHES. Satu baris: HEX [good|bad|note] [label]. '#' = komentar.
    HEX boleh md5 / sha1 / sha256. Hasil di-cache menurut mtime."""
    p = os.environ.get("REA_KNOWN_HASHES", "")
    if not p:
        return {}
    try:
        st = os.stat(p)
    except OSError:
        return {}
    key = (p, st.st_mtime_ns, st.st_size)
    if _KNOWN_CACHE["key"] == key:
        return _KNOWN_CACHE["map"]
    m: dict[str, tuple[str, str]] = {}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(8 * 1024 * 1024)
        for ln in txt.splitlines()[:200000]:
            ln = ln.split("#", 1)[0].strip()
            if not ln:
                continue
            parts = ln.split(None, 2)
            h = parts[0].lower()
            if len(h) not in (32, 40, 64) or not re.fullmatch(r"[0-9a-f]+", h):
                continue
            tag, label = "note", ""
            if len(parts) > 1:
                if parts[1].lower() in ("good", "bad", "note"):
                    tag, label = parts[1].lower(), (parts[2] if len(parts) > 2 else "")
                else:
                    label = " ".join(parts[1:])
            m[h] = (tag, label[:120])
    except OSError:
        return {}
    _KNOWN_CACHE["key"], _KNOWN_CACHE["map"] = key, m
    return m


def _known_lookup(rep: dict) -> dict | None:
    km = _known_hashes()
    if not km:
        return None
    for k in ("sha256", "sha1", "md5"):
        hit = km.get(rep.get(k, ""))
        if hit:
            if hit[0] == "good" and k != "sha256":   # MD5 / SHA-1 bisa dibuat tabrakan: tidak cukup untuk label 'sah'
                return {"tag": "note", "label": ("(entri 'good' via %s tidak dipercaya; gunakan SHA-256) " % k + hit[1]).strip(), "by": k}
            return {"tag": hit[0], "label": hit[1], "by": k}
    return None


# API yang ada di hampir semua program MSVC / CRT (bukan indikasi niat). Hanya PE native yang dilipat; .NET P/Invoke tetap dilaporkan.
_CRT_COMMON = frozenset({"isdebuggerpresent", "getprocaddress", "loadlibrary", "createfile"})


def _crt_fold_ok(rep: dict) -> bool:
    pe = rep.get("pe")
    return bool(pe and not pe.get("broken") and not pe.get("dotnet"))


def _score_v986(rep: dict, add) -> None:
    ac = rep.get("authenticode")
    if ac and ac.get("match") is False:
        add(3, "digest Authenticode tidak cocok dengan isi file (diubah setelah ditandatangani)")
    kn = rep.get("known")
    if kn and kn["tag"] == "bad":
        add(10, "hash cocok daftar lokal 'bad'%s" % ((": " + kn["label"]) if kn["label"] else ""))
    xm = rep.get("xor_multi") or []
    if xm:
        add(3 if any(x["mz"] for x in xm) else 2, "stub DOS terenkode XOR kunci berulang%s" % (" (PE tersembunyi)" if any(x["mz"] for x in xm) else ""))
    dn = rep.get("dotnet")
    emb = rep.get("emb") or {}
    if dn and dn.get("mres"):
        if any(x["mz"] for x in dn["mres"]) and not (emb.get("plain") or emb.get("xor")):
            add(3, "executable (MZ) di dalam resource terkelola .NET")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")) for x in dn["mres"]):
            add(1, "resource terkelola .NET berentropi tinggi (bukan PNG / JPEG / ZIP utuh)")


def _render_v986(rep: dict, a, compact: bool, defang: bool) -> None:
    pe = rep.get("pe")
    ac = rep.get("authenticode")
    if ac:
        if ac["match"]:
            a("Integritas tanda tangan: digest %s di blob COCOK dengan hash isi file (berkas utuh sejak ditandatangani). Rantai sertifikat dan pencabutan TIDAK diperiksa." % ac["alg"])
        else:
            a("Integritas tanda tangan: digest %s di blob %s... TIDAK sama dengan hash isi file %s...: berkas diubah setelah ditandatangani." % (ac["alg"], ac["signed"][:16], ac["computed"][:16]))
    if pe and not pe.get("broken") and pe.get("signers"):
        sm = rep.get("signer_match")
        if sm is False:
            a("Penandatangan vs CompanyName: tidak ada kata yang sama (%s vs %s). Hanya informasi; perusahaan induk / penerbit lain juga lazim." % (", ".join(pe["signers"][:2]), (pe.get("ver") or {}).get("CompanyName", "?")))
        elif sm:
            a("Penandatangan vs CompanyName: sejalan.")
    dn = rep.get("dotnet")
    if dn and dn.get("mres"):
        tot = sum(x["size"] for x in dn["mres"])
        a("Resource .NET: %d blob terkelola (%s)%s" % (len(dn["mres"]), _human(tot), ("; MZ di dalam: " + ", ".join("0x%X" % x["off"] for x in dn["mres"] if x["mz"])) if any(x["mz"] for x in dn["mres"]) else ""))
        if not compact:
            for x in sorted(dn["mres"], key=lambda x: -x["size"])[:4]:
                a("   - off 0x%X %s ent %.2f%s%s" % (x["off"], _human(x["size"]), x["ent"], " .resources" if x.get("rsrc") else "", " MZ" if x["mz"] else ""))
    for x in (rep.get("xor_multi") or [])[: (1 if compact else 3)]:
        a("Perburuan XOR kunci berulang: periode %d byte, kunci %s, stub DOS di offset 0x%X%s" % (x["k"], x["key"], x["off"], " | MZ terkonfirmasi di 0x%X" % x["mz_off"] if x["mz"] else ""))


def _fold_caps(rep: dict) -> tuple[list[tuple[str, list[str], list[str]]], list[tuple[str, list[str]]], set[str]]:
    """Pisahkan nama kemampuan (tampil) dari nama umum CRT (dilipat). -> (baris, terlipat, kemampuan yang seluruhnya CRT)."""
    ind = rep["ind"]
    fold_on = _crt_fold_ok(rep)
    rows, folded, crt_only = [], [], set()
    for cap, hit in ind["caps"].items():
        keep = [h for h in hit if not (fold_on and h.lower() in _CRT_COMMON)]
        fold = [h for h in hit if fold_on and h.lower() in _CRT_COMMON]
        if fold:
            folded.append((cap, fold))
        if keep:
            rows.append((cap, keep, fold))
        else:
            crt_only.add(cap)
    return rows, folded, crt_only


def render_card(rep: dict, defang: bool = True) -> str:
    """Kartu ringkas: skor, alasan, faktor penyeimbang, PERHATIAN dulu; rincian (import, string, bagian) dilipat jadi hitungan."""
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("KARTU TRIASE | %s | %s | %s" % (rep["name"], _human(rep["size"]), rep["kind"]))
    kn = rep.get("known")
    if kn:
        a("Daftar hash lokal (%s): %s%s" % (kn["by"], {"good": "DIKENAL SAH", "bad": "DIKENAL JAHAT", "note": "catatan"}[kn["tag"]], (" - " + kn["label"]) if kn["label"] else ""))
    a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis." % (rep["score"], rep["level"]))
    for x in rep["why"][:8]:
        a("   * " + x)
    if len(rep["why"]) > 8:
        a("   (+%d alasan lain di laporan penuh)" % (len(rep["why"]) - 8))
    if rep.get("balance"):
        a("Penyeimbang (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + "; ".join(rep["balance"][:5]))
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][:6]:
            a("   ! " + x)
        if len(rep["warn"]) > 6:
            a("   (+%d peringatan lain di laporan penuh)" % (len(rep["warn"]) - 6))
    ind = rep["ind"]
    rows, folded, _co = _fold_caps(rep)
    if rows:
        a("Kemampuan (petunjuk): " + "; ".join(_cap_text(ind, cap, keep) for cap, keep, _f in rows[:5]))
    bits = ["SHA-256 " + rep["sha256"], "entropi %.2f" % rep["entropy"]]
    a(" | ".join(bits))
    pe = rep.get("pe")
    cnt: list[str] = []
    if pe and not pe.get("broken"):
        cnt.append("import %d fungsi / %d DLL" % (sum(len(v) for v in pe["imports"].values()), len(pe["imports"])))
        cnt.append("%d bagian" % len(pe["sections"]))
    for lab, key in (("URL", "urls"), ("IP", "ips"), ("email", "emails"), ("registry", "reg"), ("path", "paths")):
        if ind[key]:
            cnt.append("%d %s" % (len(ind[key]), lab))
    cnt.append("%d string" % ind["n_strings"])
    a("Dilipat: " + ", ".join(cnt) + ". Minta laporan penuh untuk rincian.")
    _ah = _assets_hint(rep)
    if _ah:
        a(_ah)
    if ind["urls"]:
        a("URL teratas: " + " | ".join(_df(u, defang) for u in ind["urls"][:3]))
    return "\n".join(L)



