# rea_triage bagian 35/47: api_json (baris asli 15423-16082). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- API JSON untuk Iris / Hermes -----------------

# ---------------------------------------------------------------------------
# v99.14 (OPSIONAL dan ADITIF; triase, skor, dan keluaran di atas TIDAK berubah). Tiga kemampuan yang sebelumnya tidak ada:
#   1. sig_check(path, online=False): pemeriksaan tanda tangan Authenticode PENUH: tanda tangan PKCS#7 diverifikasi dengan kunci sertifikat
#      penanda, messageDigest, hash isi berkas, rantai sertifikat (tiap tautan diverifikasi kriptografis), akar di penyimpanan tepercaya,
#      masa berlaku, EKU code signing, dan (hanya bila online=True) pencabutan lewat CRL. Butuh paket `cryptography`; tanpa itu hanya
#      pemeriksaan integritas hash yang berjalan.
#      Penyimpanan akar: env REA_CA_BUNDLE (berkas PEM) > penyimpanan ROOT Windows (ssl.enum_certificates) > tidak ada. Sengaja TIDAK memakai
#      certifi: itu akar TLS Mozilla, bukan akar code signing Microsoft, jadi hasilnya menyesatkan.
#      Cap waktu (countersignature) hanya dideteksi keberadaannya, TIDAK diverifikasi.
#   2. reputation(target, online=False): reputasi hash di VirusTotal (env REA_VT_KEY). Yang dikirim HANYA hash SHA-256, tidak pernah berkas.
#   3. unpack_7z(path, outdir): membongkar kemasan yang dipahami 7-Zip (NSIS, SFX 7-Zip, dan lain-lain) lewat alat `7zz` / `7z` / `7za` / `7zr`
#      dengan pembatasan sumber daya; hanya berkas biasa yang disalin keluar (tautan simbolik dan berkas khusus dibuang).
# Akses jaringan (CRL, VirusTotal) selalu opt-in: CLI butuh --online; lewat API butuh "online": true DAN env REA_ONLINE=1 yang diatur operator,
# supaya agen tidak bisa menyalakannya sendiri. URL CRL berasal dari berkas yang dianalisis (tidak tepercaya): hanya http, alamat harus publik,
# tanpa pengalihan, ukuran dibatasi.
# ---------------------------------------------------------------------------

_OID_NAMES = {"1.2.840.113549.1.7.2": "signedData", "1.2.840.113549.1.9.4": "messageDigest", "1.2.840.113549.1.9.6": "counterSignature",
              "1.3.6.1.4.1.311.3.3.1": "msTimestamp", "1.3.6.1.5.5.7.3.3": "codeSigning"}
_SIG_HASH = {"1.2.840.113549.2.5": "md5", "1.3.14.3.2.26": "sha1", "2.16.840.1.101.3.4.2.1": "sha256", "2.16.840.1.101.3.4.2.2": "sha384",
             "2.16.840.1.101.3.4.2.3": "sha512"}
_SIG_RSA = {"1.2.840.113549.1.1.1": None, "1.2.840.113549.1.1.5": "sha1", "1.2.840.113549.1.1.11": "sha256", "1.2.840.113549.1.1.12": "sha384",
            "1.2.840.113549.1.1.13": "sha512"}
_SIG_EC = {"1.2.840.10045.4.1": "sha1", "1.2.840.10045.4.3.2": "sha256", "1.2.840.10045.4.3.3": "sha384", "1.2.840.10045.4.3.4": "sha512"}
SIG_MAX_FILE = 256 * 1024 * 1024
_REV_MAX_FETCH = 4


def _der_tlv(b: bytes, pos: int) -> tuple[int, int, int]:
    """(tag, awal_isi, akhir) elemen DER di pos. ValueError bila tak sah / keluar batas."""
    if pos < 0 or pos + 2 > len(b):
        raise ValueError("DER terpotong")
    tag, ln, p = b[pos], b[pos + 1], pos + 2
    if ln & 0x80:
        n = ln & 0x7F
        if n == 0 or n > 4 or p + n > len(b):
            raise ValueError("panjang DER tidak sah")
        ln, p = int.from_bytes(b[p:p + n], "big"), p + n
    if p + ln > len(b):
        raise ValueError("elemen DER keluar batas")
    return tag, p, p + ln


def _der_kids(b: bytes, start: int, end: int) -> list[tuple[int, int, int, int]]:
    """Anak-anak elemen: [(tag, awal_elemen, awal_isi, akhir)]."""
    out, pos = [], start
    while pos < end:
        tag, vs, ve = _der_tlv(b, pos)
        if ve > end:
            raise ValueError("anak DER keluar batas")
        out.append((tag, pos, vs, ve))
        pos = ve
        if len(out) > 1024:
            raise ValueError("terlalu banyak elemen DER")
    return out


def _der_oid(b: bytes, vs: int, ve: int) -> str:
    raw = b[vs:ve]
    if not raw:
        return ""
    parts = [str(raw[0] // 40), str(raw[0] % 40)]
    v = 0
    for x in raw[1:]:
        v = (v << 7) | (x & 0x7F)
        if not x & 0x80:
            parts.append(str(v))
            v = 0
    return ".".join(parts)


def _p7_parse(blob: bytes) -> dict:
    """Urai PKCS#7 / CMS SignedData: sertifikat (DER mentah), konten, dan SignerInfo. ValueError bila bukan SignedData yang utuh."""
    tag, vs, ve = _der_tlv(blob, 0)
    if tag != 0x30:
        raise ValueError("bukan SEQUENCE")
    top = _der_kids(blob, vs, ve)
    if len(top) < 2 or top[0][0] != 0x06 or _der_oid(blob, top[0][2], top[0][3]) != "1.2.840.113549.1.7.2" or top[1][0] != 0xA0:
        raise ValueError("bukan ContentInfo signedData")
    sd = _der_kids(blob, top[1][2], top[1][3])
    if not sd or sd[0][0] != 0x30:
        raise ValueError("SignedData tidak ada")
    parts = _der_kids(blob, sd[0][2], sd[0][3])
    if len(parts) < 4:
        raise ValueError("SignedData terlalu pendek")
    out: dict = {"certs": [], "content": None, "signers": []}
    enc = _der_kids(blob, parts[2][2], parts[2][3])          # EncapsulatedContentInfo
    if len(enc) > 1 and enc[1][0] == 0xA0:
        inner = _der_kids(blob, enc[1][2], enc[1][3])
        if inner:
            out["content"] = bytes(blob[inner[0][2]:inner[0][3]])   # NILAI elemen (tanpa tag + panjang), dasar messageDigest
    for t, off, vs2, ve2 in parts[3:]:
        if t == 0xA0:
            for ct, coff, _cvs, cve in _der_kids(blob, vs2, ve2):
                if ct == 0x30 and len(out["certs"]) < 32:
                    out["certs"].append(bytes(blob[coff:cve]))
    si_set = parts[-1]
    if si_set[0] != 0x31:
        raise ValueError("SignerInfos tidak ada")
    for st, soff, svs, sve in _der_kids(blob, si_set[2], si_set[3])[:4]:
        if st != 0x30:
            continue
        k = _der_kids(blob, svs, sve)
        if len(k) < 5:
            continue
        si: dict = {"issuer": None, "serial": None, "digest_oid": "", "attrs": None, "attrs_raw": None, "sig_oid": "", "sig": b"", "unsigned": False}
        sid = k[1]
        if sid[0] == 0x30:
            sk = _der_kids(blob, sid[2], sid[3])
            if len(sk) >= 2:
                si["issuer"] = bytes(blob[sk[0][1]:sk[0][3]])
                si["serial"] = int.from_bytes(blob[sk[1][2]:sk[1][3]], "big", signed=True)
        dk = _der_kids(blob, k[2][2], k[2][3])
        si["digest_oid"] = _der_oid(blob, dk[0][2], dk[0][3]) if dk else ""
        i = 3
        if k[i][0] == 0xA0:
            si["attrs_raw"] = bytes([0x31]) + bytes(blob[k[i][1] + 1:k[i][3]])     # SET OF: tag 0xA0 diganti 0x31 untuk verifikasi
            si["attrs"] = _der_kids(blob, k[i][2], k[i][3])
            si["_blob"] = blob
            i += 1
        sk2 = _der_kids(blob, k[i][2], k[i][3])
        si["sig_oid"] = _der_oid(blob, sk2[0][2], sk2[0][3]) if sk2 else ""
        if i + 1 < len(k) and k[i + 1][0] == 0x04:
            si["sig"] = bytes(blob[k[i + 1][2]:k[i + 1][3]])
        si["unsigned"] = any(x[0] == 0xA1 for x in k[i + 2:])
        out["signers"].append(si)
    return out


def _si_message_digest(si: dict) -> bytes | None:
    blob = si.get("_blob")
    for _t, off, vs, ve in si.get("attrs") or []:
        kids = _der_kids(blob, vs, ve)
        if len(kids) >= 2 and _der_oid(blob, kids[0][2], kids[0][3]) == "1.2.840.113549.1.9.4":
            vals = _der_kids(blob, kids[1][2], kids[1][3])
            if vals and vals[0][0] == 0x04:
                return bytes(blob[vals[0][2]:vals[0][3]])
    return None


def _si_has_timestamp(si: dict) -> bool:
    return bool(si.get("unsigned"))


def _trust_store() -> tuple[list, str]:
    """(daftar sertifikat akar, sumber). REA_CA_BUNDLE (PEM) > ROOT Windows > kosong. Tidak pernah memakai certifi (akar TLS, bukan code signing)."""
    from cryptography import x509
    p = os.environ.get("REA_CA_BUNDLE", "").strip()
    if p:
        try:
            with open(p, "rb") as fh:
                pem = fh.read(8 * 1024 * 1024)
            return list(x509.load_pem_x509_certificates(pem)), "REA_CA_BUNDLE"
        except Exception as e:
            return [], "REA_CA_BUNDLE gagal dibaca (%s)" % type(e).__name__
    try:
        import ssl
        out = []
        for der, enc, trust in ssl.enum_certificates("ROOT"):     # hanya ada di Windows
            if enc != "x509_asn" or (trust is not True and "1.3.6.1.5.5.7.3.3" not in (trust or ())):
                continue
            try:
                out.append(x509.load_der_x509_certificate(der))
            except Exception:
                continue
        return out, "penyimpanan ROOT Windows"
    except (AttributeError, ImportError, OSError):
        return [], "tidak ada"


def _cert_dates(c):
    nb = getattr(c, "not_valid_before_utc", None) or c.not_valid_before.replace(tzinfo=_dt.timezone.utc)
    na = getattr(c, "not_valid_after_utc", None) or c.not_valid_after.replace(tzinfo=_dt.timezone.utc)
    return nb, na


def _cn(name) -> str:
    try:
        from cryptography.x509.oid import NameOID
        v = name.get_attributes_for_oid(NameOID.COMMON_NAME)
        if v:
            return _clean(str(v[0].value))[:80]
        v = name.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        return _clean(str(v[0].value))[:80] if v else _clean(name.rfc4514_string())[:80]
    except Exception:
        return "?"


def _issued_by(cert, issuer) -> bool:
    try:
        cert.verify_directly_issued_by(issuer)
        return True
    except Exception:
        return False


def _rev_fetch(url: str, timeout: int = 8, cap: int = 8 * 1024 * 1024) -> bytes:
    """Ambil CRL. URL berasal dari berkas yang dianalisis (TIDAK tepercaya): hanya http, semua alamat hasil DNS harus publik (anti-SSRF),
    koneksi langsung ke IP itu (anti DNS-rebinding), tanpa pengalihan, ukuran dibatasi."""
    import http.client
    import ipaddress
    import socket
    from urllib.parse import urlsplit
    u = urlsplit(url)
    if u.scheme != "http" or not u.hostname:
        raise ValueError("hanya URL http")
    port = u.port or 80
    addrs = [i[4][0] for i in socket.getaddrinfo(u.hostname, port, type=socket.SOCK_STREAM)]
    if not addrs or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addrs):
        raise ValueError("alamat tujuan bukan alamat publik")
    conn = http.client.HTTPConnection(addrs[0], port, timeout=timeout)
    try:
        conn.request("GET", (u.path or "/") + (("?" + u.query) if u.query else ""), headers={"Host": u.netloc, "User-Agent": "rea-triage", "Accept": "*/*"})
        r = conn.getresponse()
        if r.status != 200:
            raise ValueError("HTTP %d" % r.status)
        data = r.read(cap + 1)
    finally:
        conn.close()
    if len(data) > cap:
        raise ValueError("CRL terlalu besar")
    return data


def _revocation(chain: list) -> dict:
    """Cek pencabutan tiap sertifikat non-akar lewat CRL penerbitnya. Hasil per sertifikat: 'dicabut' / 'tidak dicabut' / 'tidak diketahui'."""
    from cryptography import x509
    res: list[dict] = []
    fetched = 0
    for i, c in enumerate(chain[:-1] if len(chain) > 1 else chain):
        item = {"subject": _cn(c.subject), "status": "tidak diketahui", "why": ""}
        res.append(item)
        issuer = chain[i + 1] if i + 1 < len(chain) else None
        try:
            dps = c.extensions.get_extension_for_class(x509.CRLDistributionPoints).value
        except Exception:
            item["why"] = "tidak ada CRL distribution point"
            continue
        urls = [g.value for dp in dps for g in (dp.full_name or []) if isinstance(g, x509.UniformResourceIdentifier) and g.value.lower().startswith("http://")]
        if not urls or issuer is None:
            item["why"] = "tidak ada URL CRL http" if not urls else "penerbit tidak ada di rantai"
            continue
        if fetched >= _REV_MAX_FETCH:
            item["why"] = "batas jumlah pengambilan CRL tercapai"
            continue
        fetched += 1
        try:
            data = _rev_fetch(urls[0])
            crl = x509.load_pem_x509_crl(data) if data.lstrip()[:5] == b"-----" else x509.load_der_x509_crl(data)
            if not crl.is_signature_valid(issuer.public_key()):
                item["why"] = "tanda tangan CRL tidak cocok dengan penerbit"
                continue
            nu = getattr(crl, "next_update_utc", None) or (crl.next_update.replace(tzinfo=_dt.timezone.utc) if crl.next_update else None)
            hit = crl.get_revoked_certificate_by_serial_number(c.serial_number)
            if hit is not None:
                item["status"], item["why"] = "dicabut", "ada di CRL"
            else:
                item["status"] = "tidak dicabut"
                item["why"] = "tidak ada di CRL" + (" (CRL sudah kedaluwarsa)" if nu and nu < _dt.datetime.now(_dt.timezone.utc) else "")
        except Exception as e:
            item["why"] = "CRL gagal diambil / dibaca: %s" % _clean(str(e))[:80]
    return {"checked": res, "revoked": any(x["status"] == "dicabut" for x in res), "all_known": bool(res) and all(x["status"] != "tidak diketahui" for x in res)}


def _verify_signer(si: dict, content: bytes | None, certs: list) -> dict:
    """Verifikasi satu SignerInfo: cocokkan sertifikat penanda, messageDigest vs hash konten, lalu tanda tangan atas signedAttrs."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
    r: dict = {"cert": None, "sig_ok": None, "digest_ok": None, "alg": "", "weak": False, "error": ""}
    cert = None
    for c in certs:
        if si.get("serial") is not None and c.serial_number == si["serial"] and (si.get("issuer") is None or c.issuer.public_bytes() == si["issuer"]):
            cert = c
            break
    if cert is None:
        cert = next((c for c in certs if si.get("serial") is not None and c.serial_number == si["serial"]), None)
    if cert is None:
        r["error"] = "sertifikat penanda tidak ada di tanda tangan"
        return r
    r["cert"] = cert
    hname = _SIG_HASH.get(si["digest_oid"]) or _SIG_RSA.get(si["sig_oid"]) or _SIG_EC.get(si["sig_oid"])
    if hname not in ("md5", "sha1", "sha256", "sha384", "sha512"):
        r["error"] = "algoritma hash tidak dikenal (%s)" % (si["digest_oid"] or "?")
        return r
    r["alg"], r["weak"] = hname, hname in ("md5", "sha1")
    hobj = {"md5": hashes.MD5, "sha1": hashes.SHA1, "sha256": hashes.SHA256, "sha384": hashes.SHA384, "sha512": hashes.SHA512}[hname]()
    if si.get("attrs_raw") is not None:
        md = _si_message_digest(si)
        if content is not None and md is not None:
            r["digest_ok"] = hashlib.new(hname, content).digest() == md
        signed = si["attrs_raw"]
    else:
        signed = content
        if signed is None:
            r["error"] = "tidak ada signedAttrs dan konten tidak tertanam"
            return r
    try:
        pub = cert.public_key()
        if isinstance(pub, rsa.RSAPublicKey) and si["sig_oid"] in _SIG_RSA:
            pub.verify(si["sig"], signed, padding.PKCS1v15(), hobj)
            r["sig_ok"] = True
        elif isinstance(pub, ec.EllipticCurvePublicKey) and si["sig_oid"] in _SIG_EC:
            pub.verify(si["sig"], signed, ec.ECDSA(hobj))
            r["sig_ok"] = True
        else:
            r["error"] = "jenis tanda tangan tidak didukung (%s)" % (si["sig_oid"] or "?")
    except Exception as e:
        r["sig_ok"] = False
        r["error"] = "tanda tangan tidak cocok (%s)" % type(e).__name__
    return r


def sig_check(path, online: bool = False) -> dict:
    """Pemeriksaan tanda tangan Authenticode penuh. Tidak pernah melempar. Lihat komentar v99.14 untuk cakupan dan batasannya."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(min(size, SIG_MAX_FILE))
        pe = _parse_pe(d, size) if d[:2] == b"MZ" else None
        if not pe or pe.get("broken"):
            return {"ok": False, "error": "bukan PE yang bisa diurai"}
        if not pe.get("signed"):
            return {"ok": False, "error": "berkas tidak memiliki tanda tangan Authenticode"}
        out: dict = {"ok": True, "name": Path(str(path)).name, "notes": [], "signatures": [], "online": bool(online), "crypto": True}
        integ = _authenticode_check(d, size, pe) if len(d) == size else None
        out["file_hash"] = integ
        if len(d) != size:
            out["notes"].append("berkas lebih besar dari %d MB: hash isi tidak dihitung ulang" % (SIG_MAX_FILE >> 20))
        try:
            import cryptography  # noqa: F401
            from cryptography import x509
        except ImportError:
            out["crypto"] = False
            out["verdict"] = "TIDAK LENGKAP: paket 'cryptography' tidak terpasang (pip install cryptography); hanya integritas hash isi berkas yang diperiksa"
            return out
        pe_off = struct.unpack_from("<I", d, 0x3C)[0]
        o = pe_off + 24
        is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
        c_off, c_sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 32)
        end, pos, blobs = min(c_off + c_sz, len(d)), c_off, []
        while pos + 8 <= end and len(blobs) < 4:
            dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
            if dw < 8 or pos + dw > end:
                break
            if typ == 2:
                blobs.append(bytes(d[pos + 8:pos + dw]))
            pos += (dw + 7) & ~7
        if not blobs:
            out["ok"] = False
            out["error"] = "tabel sertifikat tidak berisi blob PKCS#7"
            return out
        store, src = _trust_store()
        out["trust_source"] = src
        now = _dt.datetime.now(_dt.timezone.utc)
        for blob in blobs:
            try:
                p7 = _p7_parse(blob)
            except ValueError as e:
                out["signatures"].append({"error": "PKCS#7 tidak terbaca: %s" % _clean(str(e))[:80]})
                continue
            certs = []
            for raw in p7["certs"]:
                try:
                    certs.append(x509.load_der_x509_certificate(raw))
                except Exception:
                    continue
            for si in p7["signers"]:
                v = _verify_signer(si, p7["content"], certs)
                sig: dict = {"alg": v["alg"], "weak_hash": v["weak"], "sig_ok": v["sig_ok"], "digest_ok": v["digest_ok"], "error": v["error"],
                             "timestamp": _si_has_timestamp(si), "chain": [], "links_ok": None, "trusted": None, "root": "", "eku_code_signing": None,
                             "expired": None, "revocation": None}
                leaf = v["cert"]
                if leaf is not None:
                    chain, seen = [leaf], {leaf.fingerprint(hashes_sha256())}
                    cur = leaf
                    for _ in range(8):
                        if _issued_by(cur, cur):
                            break
                        nxt = next((c for c in certs if c.fingerprint(hashes_sha256()) not in seen and _issued_by(cur, c)), None)
                        if nxt is None:
                            nxt = next((c for c in store if c.fingerprint(hashes_sha256()) not in seen and _issued_by(cur, c)), None)
                        if nxt is None:
                            break
                        chain.append(nxt)
                        seen.add(nxt.fingerprint(hashes_sha256()))
                        cur = nxt
                    top = chain[-1]
                    self_issued = _issued_by(top, top)
                    sig["links_ok"] = self_issued or len(chain) > 1
                    sig["complete"] = self_issued
                    fp = top.fingerprint(hashes_sha256())
                    if store:
                        sig["trusted"] = bool(self_issued and any(c.fingerprint(hashes_sha256()) == fp for c in store)) or bool(
                            not self_issued and any(_issued_by(top, c) for c in store))
                    sig["root"] = _cn(top.subject)
                    for c in chain:
                        nb, na = _cert_dates(c)
                        sig["chain"].append({"subject": _cn(c.subject), "issuer": _cn(c.issuer), "not_before": nb.strftime("%Y-%m-%d"),
                                             "not_after": na.strftime("%Y-%m-%d"), "alg": getattr(getattr(c, "signature_hash_algorithm", None), "name", "?")})
                    nb, na = _cert_dates(leaf)
                    sig["expired"] = not (nb <= now <= na)
                    try:
                        from cryptography.x509.oid import ExtendedKeyUsageOID
                        eku = leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
                        sig["eku_code_signing"] = ExtendedKeyUsageOID.CODE_SIGNING in eku
                    except Exception:
                        sig["eku_code_signing"] = False
                    if online:
                        sig["revocation"] = _revocation(chain)
                out["signatures"].append(sig)
        out["verdict"] = _sig_verdict(out, bool(store))
        return out
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:120])}


def hashes_sha256():
    from cryptography.hazmat.primitives import hashes
    return hashes.SHA256()


def _sig_verdict(out: dict, have_store: bool) -> str:
    sigs = [s for s in out["signatures"] if "alg" in s]
    if not sigs:
        return "TIDAK VALID: tanda tangan tidak bisa diurai"
    fh = out.get("file_hash")
    bad: list[str] = []
    soft: list[str] = []
    incomplete: list[str] = []      # hal yang HARUS terbukti agar boleh disebut VALID, tetapi tidak bisa dipastikan
    s = sigs[0]
    if s.get("sig_ok") is not True:
        bad.append("tanda tangan PKCS#7 tidak terverifikasi (%s)" % (s.get("error") or "gagal"))
    if s.get("digest_ok") is False:
        bad.append("messageDigest tidak cocok dengan konten yang ditandatangani")
    elif s.get("digest_ok") is None:
        incomplete.append("messageDigest tidak bisa diperiksa")
    if fh is None:
        incomplete.append("hash isi berkas tidak bisa dibandingkan dengan digest yang ditandatangani (berkas terlalu besar, tabel section janggal, atau digest tidak terbaca)")
    elif not fh.get("match"):
        bad.append("isi berkas berubah setelah ditandatangani (hash tidak cocok)")
    if s.get("links_ok") is False:
        bad.append("rantai sertifikat tidak tersambung")
    elif s.get("links_ok") and not s.get("complete"):
        soft.append("rantai tidak sampai akar (penerbit tidak ditemukan di tanda tangan maupun penyimpanan)")
    if not have_store:
        incomplete.append("akar tepercaya tidak bisa diverifikasi (set REA_CA_BUNDLE, atau jalankan di Windows); tanpa itu sertifikat buatan sendiri juga tampak sah")
    elif s.get("trusted") is False:
        bad.append("akar rantai TIDAK ada di penyimpanan tepercaya")
    if s.get("eku_code_signing") is False:
        bad.append("sertifikat penanda tidak punya EKU code signing")
    if s.get("expired"):
        (soft if s.get("timestamp") else bad).append("sertifikat penanda di luar masa berlaku" + (" (ada cap waktu; cap waktu tidak diverifikasi)" if s.get("timestamp") else ""))
    if s.get("weak_hash"):
        soft.append("hash lemah (%s)" % s.get("alg"))
    rv = s.get("revocation")
    if rv is None:
        soft.append("pencabutan tidak diperiksa (butuh --online)")
    elif rv.get("revoked"):
        bad.append("sertifikat DICABUT menurut CRL")
    elif not rv.get("all_known"):
        soft.append("status pencabutan sebagian tidak diketahui")
    if bad:
        return "TIDAK VALID: " + "; ".join(bad)
    if incomplete:
        return "TIDAK LENGKAP (belum bisa disebut valid): " + "; ".join(incomplete + soft)
    return "VALID secara kriptografis" + (" (dengan catatan: " + "; ".join(soft) + ")" if soft else "")


def sig_text(path, online: bool = False) -> str:
    r = sig_check(path, online=online)
    if not r.get("ok"):
        return "TANDA TANGAN: " + r.get("error", "gagal")
    L = ["TANDA TANGAN (v99.14) %s" % r["name"], "Putusan: %s" % r["verdict"]]
    fh = r.get("file_hash")
    if fh:
        L.append("Hash isi berkas: %s (%s)" % ("COCOK" if fh["match"] else "TIDAK COCOK", fh["alg"]))
    L.append("Akar tepercaya: %s" % r.get("trust_source", "?"))
    for i, s in enumerate(r["signatures"], 1):
        if "alg" not in s:
            L.append("Tanda tangan %d: %s" % (i, s.get("error", "?")))
            continue
        L.append("Tanda tangan %d: PKCS#7 %s | messageDigest %s | hash %s%s | cap waktu: %s" % (
            i, {True: "sah", False: "GAGAL", None: "tak diperiksa"}[s["sig_ok"]], {True: "cocok", False: "TIDAK cocok", None: "tak diperiksa"}[s["digest_ok"]],
            s["alg"] or "?", " (lemah)" if s["weak_hash"] else "", "ada (tidak diverifikasi)" if s["timestamp"] else "tidak ada"))
        for j, c in enumerate(s["chain"]):
            L.append("   %s%s  <- %s  [%s s/d %s]" % ("  " * j, c["subject"], c["issuer"], c["not_before"], c["not_after"]))
        if s["chain"]:
            L.append("   Akar: %s | tersambung: %s | di penyimpanan: %s | EKU code signing: %s" % (
                s["root"], {True: "ya", False: "TIDAK", None: "?"}[s["links_ok"]], {True: "ya", False: "TIDAK", None: "tak diperiksa"}[s["trusted"]],
                {True: "ya", False: "TIDAK", None: "?"}[s["eku_code_signing"]]))
        if s.get("revocation"):
            for x in s["revocation"]["checked"]:
                L.append("   Pencabutan %s: %s (%s)" % (x["subject"], x["status"], x["why"]))
    for n in r.get("notes", []):
        L.append("Catatan: " + n)
    L.append("Batas: cap waktu tidak diverifikasi; kebijakan Windows (WinVerifyTrust, kebijakan penerbit, daftar cabut khusus) tidak ditiru.")
    return "\n".join(L)


# --- reputasi hash (VirusTotal) ---------------------------------------------------------------------------------------------------------

def _http_get(url: str, headers: dict, timeout: int = 10, cap: int = 1024 * 1024) -> tuple[int, bytes]:
    """GET HTTPS tanpa mengikuti pengalihan. (status, isi). Dipisah supaya bisa diganti saat uji."""
    from urllib.error import HTTPError
    from urllib.request import HTTPRedirectHandler, Request, build_opener

    class _NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        with build_opener(_NoRedirect).open(Request(url, headers=headers), timeout=timeout) as r:
            return r.status, r.read(cap + 1)[:cap]
    except HTTPError as e:
        return e.code, b""


def reputation(target, online: bool = False) -> dict:
    """Reputasi SHA-256 di VirusTotal. target: hash 64 hex atau path berkas. Hanya hash yang dikirim. 'tidak dikenal' BUKAN bukti aman."""
    try:
        t = str(target).strip()
        h = t.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", t) else triage(t)["sha256"]
        if not online:
            return {"ok": False, "sha256": h, "error": "mode online belum diaktifkan (CLI: --online; API: \"online\": true dan env REA_ONLINE=1)"}
        key = os.environ.get("REA_VT_KEY", "").strip()
        if not key:
            return {"ok": False, "sha256": h, "error": "env REA_VT_KEY belum diisi"}
        code, body = _http_get("https://www.virustotal.com/api/v3/files/" + h, {"x-apikey": key, "accept": "application/json"})
        if code == 404:
            return {"ok": True, "sha256": h, "known": False}
        if code != 200:
            return {"ok": False, "sha256": h, "error": "VirusTotal membalas HTTP %d" % code}
        a = (json.loads(body.decode("utf-8", "replace")).get("data") or {}).get("attributes") or {}
        st = a.get("last_analysis_stats") or {}
        ptc = (a.get("popular_threat_classification") or {}).get("suggested_threat_label")
        return {"ok": True, "sha256": h, "known": True, "malicious": int(st.get("malicious", 0)), "suspicious": int(st.get("suspicious", 0)),
                "harmless": int(st.get("harmless", 0)), "undetected": int(st.get("undetected", 0)),
                "name": _clean(str(a.get("meaningful_name") or ""))[:80], "label": _clean(str(ptc or ""))[:60],
                "last_analysis": a.get("last_analysis_date") if isinstance(a.get("last_analysis_date"), int) else None}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:100])}


def reputation_text(target, online: bool = False) -> str:
    r = reputation(target, online=online)
    if not r.get("ok"):
        return "REPUTASI: %s%s" % (r.get("error", "gagal"), (" (sha256 %s)" % r["sha256"]) if r.get("sha256") else "")
    if not r["known"]:
        return "REPUTASI VirusTotal: hash %s tidak dikenal. Ini BUKAN bukti berkas aman (bisa sampel baru / tidak pernah diunggah)." % r["sha256"]
    tot = r["malicious"] + r["suspicious"] + r["harmless"] + r["undetected"]
    when = _dt.datetime.fromtimestamp(r["last_analysis"], _dt.timezone.utc).strftime("%Y-%m-%d") if r.get("last_analysis") else "?"
    return ("REPUTASI VirusTotal (sha256 %s): %d jahat, %d mencurigakan, %d tidak terdeteksi / %d bersih dari %d mesin (analisis terakhir %s)%s%s\n"
            "Catatan: hasil layanan luar, TIDAK ikut skor REA; hanya hash yang dikirim." % (
                r["sha256"], r["malicious"], r["suspicious"], r["undetected"], r["harmless"], tot, when,
                (" | nama: " + r["name"]) if r["name"] else "", (" | label: " + r["label"]) if r["label"] else ""))


# --- unpack lewat 7-Zip -------------------------------------------------------------------------------------------------------------------

UNPACK7_MAX_FILES = 5000
UNPACK7_MAX_TOTAL = 1024 * 1024 * 1024
UNPACK7_MEM = 3 * 1024 * 1024 * 1024


def unpack_7z(path, outdir) -> dict:
    """Bongkar kemasan yang dipahami 7-Zip (NSIS, SFX 7-Zip, 7z, dan lain-lain) ke folder sementara dengan batas sumber daya, lalu salin keluar
    HANYA berkas biasa (tautan simbolik / berkas khusus dibuang) beserta manifest SHA-256. Tidak menjalankan isi apa pun."""
    import shutil
    import subprocess
    import tempfile
    try:
        tool = next((shutil.which(x) for x in ("7zz", "7z", "7za", "7zr") if shutil.which(x)), None)
        if not tool:
            return {"ok": False, "error": "alat 7-Zip (7zz / 7z / 7za / 7zr) tidak ditemukan di PATH"}
        f, size = _open_regular(path)
        if size > UNPACK_MAX:
            f.close()
            return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
        out = Path(outdir).expanduser().resolve()
        with tempfile.TemporaryDirectory() as td:
            src, work = Path(td) / "in.bin", Path(td) / "x"
            work.mkdir()
            with f, open(src, "wb") as sf:
                shutil.copyfileobj(f, sf, 1 << 20)
            def _lim7():
                import resource
                for lim, val in ((resource.RLIMIT_AS, UNPACK7_MEM), (resource.RLIMIT_CPU, UNPACK_TIMEOUT * 3),
                                 (resource.RLIMIT_FSIZE, UNPACK7_MAX_TOTAL), (resource.RLIMIT_CORE, 0)):
                    try:
                        resource.setrlimit(lim, (val, val))
                    except (ValueError, OSError):
                        pass
            pre = _lim7 if os.name == "posix" else None
            r = subprocess.run([tool, "x", "-y", "-bd", "-o" + str(work), str(src)], capture_output=True, timeout=UNPACK_TIMEOUT * 3,
                               stdin=subprocess.DEVNULL, cwd=td, env={"PATH": os.environ.get("PATH", ""), "LANG": "C"}, preexec_fn=pre)
            if r.returncode not in (0, 1) and not any(work.iterdir()):
                return {"ok": False, "error": "7-Zip gagal (kode %d): %s" % (r.returncode, _clean((r.stderr or r.stdout).decode("utf-8", "replace"))[:160])}
            files, total, skipped = [], 0, 0
            out.mkdir(parents=True, exist_ok=True)
            for root, dirs, names in os.walk(work, followlinks=False):
                dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(root, x))]
                for n in sorted(names):
                    p = Path(root) / n
                    try:
                        st = os.lstat(p)
                    except OSError:
                        skipped += 1
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        skipped += 1
                        continue
                    if len(files) >= UNPACK7_MAX_FILES or total + st.st_size > UNPACK7_MAX_TOTAL:
                        return {"ok": False, "error": "hasil melebihi batas (%d berkas / %d MB); dibatalkan" % (UNPACK7_MAX_FILES, UNPACK7_MAX_TOTAL >> 20)}
                    rel = p.relative_to(work).as_posix()
                    safe = "/".join(re.sub(r"[^\w.\- ]", "_", c)[:100] or "_" for c in rel.split("/") if c not in ("", ".", ".."))
                    dst = (out / safe).resolve()
                    if out != dst and out not in dst.parents:
                        skipped += 1
                        continue
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    h = hashlib.sha256()
                    with open(p, "rb") as sf, open(dst, "wb") as df:
                        for chunk in iter(lambda: sf.read(1 << 20), b""):
                            h.update(chunk)
                            df.write(chunk)
                    total += st.st_size
                    files.append({"name": safe, "size": st.st_size, "sha256": h.hexdigest()})
            man = out / "manifest_7z.json"
            man.write_text(json.dumps({"source": Path(str(path)).name, "files": files, "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"ok": True, "files": files, "total": total, "skipped": skipped, "manifest": str(man), "partial": r.returncode != 0}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "7-Zip melewati batas waktu"}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:120])}


def unpack_7z_text(path, outdir) -> str:
    r = unpack_7z(path, outdir)
    if not r["ok"]:
        return "UNPACK 7-Zip gagal: " + r["error"]
    L = ["UNPACK 7-Zip: %d berkas, %s, %d dilewati (tautan / berkas khusus)%s | manifest: %s" % (
        len(r["files"]), _human(r["total"]), r["skipped"], " | SEBAGIAN (7-Zip melaporkan peringatan)" if r["partial"] else "", r["manifest"])]
    for x in r["files"][:40]:
        L.append("  %s  %s  %s" % (x["sha256"][:16], _human(x["size"]).rjust(9), x["name"]))
    if len(r["files"]) > 40:
        L.append("  ... +%d berkas lain di manifest" % (len(r["files"]) - 40))
    L.append("Berkas hasil BELUM ditriase; jalankan triase per berkas.")
    return "\n".join(L)


def _api_online(req: dict, notes: list | None = None) -> bool:
    """Online lewat API hanya bila diminta DAN operator menyalakan REA_ONLINE=1."""
    want = bool(req.get("online"))
    ok = want and os.environ.get("REA_ONLINE", "").strip() == "1"
    if want and not ok and notes is not None:
        notes.append("online diminta, tetapi REA_ONLINE=1 belum diatur operator: akses jaringan dilewati")
    return ok


