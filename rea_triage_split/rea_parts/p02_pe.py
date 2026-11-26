# rea_triage bagian 02/47: pe (baris asli 412-804). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# PE
# ---------------------------------------------------------------------------


_RES_TYPES = {1: "CURSOR", 2: "BITMAP", 3: "ICON", 4: "MENU", 5: "DIALOG", 6: "STRING", 9: "ACCELERATOR", 10: "RCDATA", 11: "MESSAGETABLE",
              12: "GROUP_CURSOR", 14: "GROUP_ICON", 16: "VERSION", 24: "MANIFEST"}
_VER_KEYS = ("CompanyName", "FileDescription", "FileVersion", "InternalName", "OriginalFilename", "ProductName")


def _res_entries(d: bytes, off):
    if off is None or off < 0 or off + 16 > len(d):
        return []
    nn, ni = struct.unpack_from("<HH", d, off + 12)
    out = []
    for i in range(min(nn + ni, 64)):
        o = off + 16 + 8 * i
        if o + 8 > len(d):
            break
        name, tgt = struct.unpack_from("<II", d, o)
        out.append((name, tgt & 0x7FFFFFFF, bool(tgt & 0x80000000)))
    return out


def _parse_resources(d: bytes, base, rva2off) -> tuple[list[dict], dict]:
    """Jelajahi direktori resource PE (tipe -> nama -> bahasa). Hanya membaca; tidak mengekstrak apa pun."""
    leaves: list[dict] = []
    ver: dict = {}

    def nm(n):
        if n & 0x80000000:
            o = base + (n & 0x7FFFFFFF)
            if o + 2 <= len(d):
                ln = struct.unpack_from("<H", d, o)[0]
                return d[o + 2:o + 2 + 2 * min(ln, 64)].decode("utf-16le", "replace")
            return "?"
        return n

    for tn, toff, tdir in _res_entries(d, base):
        if not tdir:
            continue
        tname = nm(tn)
        tlabel = _RES_TYPES.get(tname, str(tname)) if isinstance(tname, int) else "'%s'" % tname
        for nn_, noff, ndir in _res_entries(d, base + toff)[:32]:
            if not ndir:
                continue
            for _ln, loff, ldir in _res_entries(d, base + noff)[:4]:
                if ldir or base + loff + 16 > len(d):
                    continue
                rva, size, _cp, _r = struct.unpack_from("<IIII", d, base + loff)
                fo = rva2off(rva)
                if fo is None or fo >= len(d):
                    continue
                data = d[fo:fo + min(size, 1 << 20)]
                leaf = {"type": tlabel, "name": str(nm(nn_)), "size": size, "ent": _entropy(data[:65536]), "mz": data[:2] == b"MZ", "off": fo}
                fmt, fmt_ok = _res_format(d, fo, size)
                if fmt:
                    leaf["fmt"], leaf["fmt_ok"] = fmt, fmt_ok
                leaves.append(leaf)
                if tname == 16 and not ver:
                    txt = d[fo:fo + min(size, 16384)].decode("utf-16le", "ignore")
                    for k in _VER_KEYS:
                        m = re.search(k + r"\x00+([^\x00]{1,120})", txt)
                        if m:
                            ver[k] = m.group(1).strip()
                    quads = sorted(set(re.findall(r"(?<![\d.])\d{1,5}(?:\.\d{1,5}){3}(?![\d.])", txt)))
                    if quads:
                        leaf["vquads"] = quads[:8]   # nomor versi berbentuk a.b.c.d (bukan IP): dipakai menyaring kandidat IP
                if len(leaves) >= 200:
                    return leaves, ver
    return leaves, ver


def _rich_header(d: bytes, pe_off: int):
    """Header 'Rich' (jejak alat build MSVC) di antara DOS stub dan header PE. Hash varian Iris: MD5 teks terang dari DanS sampai Rich."""
    end = d.find(b"Rich", 0x40, min(pe_off + 4, len(d)))
    if end == -1 or end + 8 > len(d):
        return None
    key = d[end + 4:end + 8]
    k = struct.unpack("<I", key)[0]
    pos = end - 4
    while pos >= 0x40:
        if struct.unpack_from("<I", d, pos)[0] ^ k == 0x536E6144:   # "DanS"
            clear = bytes(b ^ key[i % 4] for i, b in enumerate(d[pos:end]))
            return {"hash": _md5(clear).hexdigest(), "n": max(0, (end - pos - 16) // 8)}
        pos -= 4
    return None


def _res_format(d: bytes, fo: int, size: int) -> tuple[str, bool]:
    """Kenali resource terkompres yang wajar tampak acak (PNG / JPEG / ZIP) dari magic number, lalu cek kerangka dasarnya.
    Mengembalikan (format, utuh). utuh=False bila magic cocok tetapi kerangka tidak masuk akal (mis. data tambahan setelah IEND),
    supaya awalan PNG palsu di depan payload tidak lolos."""
    if size < 12 or fo < 0 or fo + 16 > len(d):
        return "", False
    end = min(fo + size, len(d))
    head = d[fo:fo + 16]
    mv = memoryview(d)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        tail = bytes(mv[max(fo, end - 32):end]).rstrip(b"\x00")
        return "PNG", head[12:16] == b"IHDR" and tail.endswith(b"IEND\xaeB`\x82")
    if head[:3] == b"\xff\xd8\xff":
        tail = bytes(mv[max(fo, end - 64):end]).rstrip(b"\x00")
        return "JPEG", tail.endswith(b"\xff\xd9")
    if head[:4] == b"PK\x03\x04":
        tail = bytes(mv[max(fo, end - 65557):end])
        return "ZIP", b"PK\x05\x06" in tail
    return "", False


def _cert_spans(d: bytes, off: int, size: int) -> tuple[list[tuple[int, int]], int]:
    """Rentang struktur PKCS#7 (DER) di tabel sertifikat Authenticode, plus jumlah byte TAK BERSTRUKTUR di tabel itu (di luar padding nol).
    Hanya struktur DER dari entri WIN_CERTIFICATE PKCS#7 (wCertificateType == 2) PERTAMA yang dikecualikan dari ekstraksi string / IOC: itu
    satu-satunya entri yang diperiksa _authenticode_check (digest-nya dibandingkan dengan hash berkas). Entri kedua dan seterusnya, entri
    bertipe lain, header entri, dan byte sisa TIDAK dikecualikan dan dihitung sebagai byte tak berstruktur (cert_extra), karena data bisa
    diselipkan di sana tanpa merusak tanda tangan utama. Bila struktur tidak terbaca, byte sisanya dihitung sebagai tak berstruktur."""
    spans: list[tuple[int, int]] = []
    extra, pos, end = 0, off, min(off + size, len(d))
    got = False   # sudah ada entri PKCS#7 pertama yang dikecualikan
    while pos + 8 <= end:
        dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
        if dw < 8 or pos + dw > end:
            break   # entri rusak: sisa tabel dihitung di bawah
        if not got and typ == 2 and dw >= 16 and d[pos + 8] == 0x30:   # PKCS#7 SignedData selalu diawali SEQUENCE
            s0, b = pos + 8, d[pos + 9]
            ok = True
            if b & 0x80:
                n = b & 0x7F
                if n == 0 or n > 4 or s0 + 2 + n > pos + dw:
                    ok = False
                else:
                    hdr, ln = 2 + n, int.from_bytes(d[s0 + 2:s0 + 2 + n], "big")
            else:
                hdr, ln = 2, b
            if ok and s0 + hdr + ln <= pos + dw:
                spans.append((s0, s0 + hdr + ln))
                extra += len(d[s0 + hdr + ln:pos + dw].rstrip(b"\x00"))
                got = True
                pos += (dw + 7) & ~7
                continue
        # entri bukan PKCS#7 pertama (atau DER-nya tak terbaca): seluruh isinya tak berstruktur
        extra += len(d[pos + 8:pos + dw].rstrip(b"\x00"))
        pos += (dw + 7) & ~7
    if pos < end:
        extra += len(d[pos:end].rstrip(b"\x00"))
    return spans, extra


def _signers(d: bytes, off: int, size: int) -> list[str]:
    """Nama umum (CN) yang terbaca dari blob sertifikat Authenticode. Keabsahan tanda tangan TIDAK diperiksa."""
    blob = d[off:off + min(size, 200000)]
    out: list[str] = []
    for m in re.finditer(rb"\x55\x04\x03([\x0c\x13\x14\x1e])", blob):
        p_ = m.end()
        if p_ >= len(blob) or blob[p_] & 0x80:
            continue
        raw = blob[p_ + 1:p_ + 1 + blob[p_]]
        t = raw.decode("utf-16be", "ignore") if m.group(1) == b"\x1e" else raw.decode("utf-8", "replace")
        if t and t not in out:
            out.append(t[:80])
    return out[:6]


def _parse_pe(d: bytes, file_size: int) -> dict | None:
    if len(d) < 0x40 or d[:2] != b"MZ":
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    if pe_off + 24 > len(d) or d[pe_off:pe_off + 4] != b"PE\0\0":
        return {"broken": "header MZ ada tetapi tanda PE tidak ditemukan (DOS stub saja, rusak, atau dikemas)"}
    machine, nsec, ts, _p, _n, optsz, chars = struct.unpack_from("<HHIIIHH", d, pe_off + 4)
    o = pe_off + 24
    if o + 96 > len(d):
        return {"broken": "optional header terpotong"}
    magic = struct.unpack_from("<H", d, o)[0]
    is64 = magic == 0x20B
    if o + (112 if is64 else 96) > len(d):
        return {"broken": "optional header terpotong"}
    entry = struct.unpack_from("<I", d, o + 16)[0]
    subsys, dllch = struct.unpack_from("<HH", d, o + 68)
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    dd_off = o + (112 if is64 else 96)
    pwarn: list[str] = []   # kegagalan parse sebagian; masuk rep["warn"] supaya "tidak ada temuan" tidak tampak seperti "bersih"
    dirs = []
    for i in range(min(nrva, 16)):
        if dd_off + 8 * i + 8 > len(d):
            break
        dirs.append(struct.unpack_from("<II", d, dd_off + 8 * i))

    secs = []
    so = o + optsz
    ent_left, md5_left, budget_hit = ENT_BUDGET, MD5_BUDGET, False
    for i in range(min(nsec, 96)):
        p = so + 40 * i
        if p + 40 > len(d):
            break
        nm, vsz, va, rsz, rptr, _r, _l, _nr, _nl, ch = struct.unpack_from("<8sIIIIIIHHI", d, p)
        name = nm.rstrip(b"\0").decode("latin-1", "replace")
        raw = d[rptr:rptr + min(rsz, SEC_ENT_SAMPLE)] if rptr < len(d) else b""
        if len(raw) > ent_left:       # header bagian tumpang-tindih / dibuat-buat: jangan biarkan CPU habis
            raw, budget_hit = b"", True
        ent_left -= len(raw)
        md5 = ""
        if rptr < len(d) and rsz:
            n_md = min(rsz, 16 * 1024 * 1024, len(d) - rptr)
            if n_md <= md5_left:
                md5_left -= n_md
                md5 = _md5(memoryview(d)[rptr:rptr + n_md]).hexdigest()
            else:
                budget_hit = True
        secs.append({
            "name": name, "va": va, "vsize": vsz, "rptr": rptr, "rsize": rsz,
            "md5": md5,
            "flags": ("R" if ch & 0x40000000 else "-") + ("W" if ch & 0x80000000 else "-") + ("X" if ch & 0x20000000 else "-"),
            "ent": _entropy(raw) if raw else 0.0,
        })

    def rva2off(rva: int) -> int | None:
        for s in secs:
            rel = rva - s["va"]
            if 0 <= rel < max(s["vsize"], s["rsize"]):
                return (rel + s["rptr"]) if rel < s["rsize"] else None   # ekor virtual (nol) tidak ada di berkas
        if secs and rva < min(s["va"] for s in secs):
            return rva
        return None

    def cstr(off: int, lim: int = 128) -> str:
        if off is None or off < 0 or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    def hint_name(rva: int) -> str:
        fo = rva2off(rva)
        return (cstr(fo + 2) if fo is not None else "") or "?"

    imports: dict[str, list[str]] = {}
    try:
        if len(dirs) > 1 and dirs[1][0]:
            off = rva2off(dirs[1][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 20 <= len(d) and n < 60:
                oft, _t, _f, name_rva, ft = struct.unpack_from("<IIIII", d, off)
                if not (oft or name_rva or ft):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns: list[str] = []
                th = rva2off(oft or ft)
                k = 0
                while th is not None and th + step <= len(d) and k < 600:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                imports.setdefault(dll or "?", []).extend(fns)
                off += 20
                n += 1
    except (struct.error, IndexError):
        pwarn.append("tabel import terpotong / rusak: daftar import mungkin tidak lengkap")

    delay_imports: dict[str, list[str]] = {}   # v94: delay-load import (dipakai untuk menyembunyikan API dari tabel impor biasa)
    try:
        if len(dirs) > 13 and dirs[13][0]:
            off = rva2off(dirs[13][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 32 <= len(d) and n < 40:
                _at, name_rva, _h, _iat, int_rva = struct.unpack_from("<IIIII", d, off)
                if not (name_rva or int_rva):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns = []
                th = rva2off(int_rva)
                k = 0
                while th is not None and th + step <= len(d) and k < 400:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                delay_imports.setdefault(dll or "?", []).extend(fns)
                off += 32
                n += 1
    except (struct.error, IndexError):
        pwarn.append("tabel delay-import terpotong / rusak: daftar mungkin tidak lengkap")

    imph, ord_imp = "", 0
    try:
        parts = []
        for dll, fns in imports.items():
            base = dll.rsplit(".", 1)[0] if dll.rsplit(".", 1)[-1] in ("dll", "ocx", "sys") else dll
            for fn in fns:
                if fn.startswith("#"):
                    ord_imp += 1
                    fn = "ord" + fn[1:]
                parts.append("%s.%s" % (base, fn.lower()))
        if parts:
            imph = _md5(",".join(parts).encode()).hexdigest()
    except Exception:
        pass

    exports: list[str] = []
    try:
        if dirs and dirs[0][0]:
            eo = rva2off(dirs[0][0])
            if eo is not None and eo + 40 <= len(d):
                nnames = struct.unpack_from("<I", d, eo + 24)[0]
                names_rva = struct.unpack_from("<I", d, eo + 32)[0]
                no = rva2off(names_rva)
                for i in range(min(nnames, 80)):
                    if no is None or no + 4 * i + 4 > len(d):
                        break
                    nm_ = cstr(rva2off(struct.unpack_from("<I", d, no + 4 * i)[0]))
                    if nm_:
                        exports.append(nm_)
    except (struct.error, IndexError):
        pwarn.append("tabel ekspor terpotong / rusak: daftar ekspor mungkin tidak lengkap")

    res: list[dict] = []
    ver: dict = {}
    try:
        if len(dirs) > 2 and dirs[2][0]:
            res, ver = _parse_resources(d, rva2off(dirs[2][0]), rva2off)
    except (struct.error, IndexError, ValueError, OverflowError):
        pwarn.append("direktori resource rusak / tidak bisa diurai: resource tidak diperiksa (bisa disengaja untuk menghindari analisis)")
    try:   # v98.6: entropi bagian resource dihitung tanpa PNG / JPEG / ZIP utuh (ikon PNG membuat .rsrc tampak 'terenkripsi')
        skip_rs = [(x["off"], x["off"] + x["size"]) for x in res if x.get("fmt") and x.get("fmt_ok")]
        if skip_rs and len(dirs) > 2 and dirs[2][0]:
            rs_ = next((s for s in secs if s["va"] <= dirs[2][0] < s["va"] + max(s["vsize"], s["rsize"])), None)
            if rs_ and rs_["ent"] > 7.0 and rs_["rptr"] < len(d):
                a_, b_ = rs_["rptr"], rs_["rptr"] + min(rs_["rsize"], SEC_ENT_SAMPLE)
                rest_ = _mask_block(d, a_, b_, _merge_spans(skip_rs, len(d)))
                masked_ = (min(b_, len(d)) - a_) - len(rest_)
                if masked_ > 0:
                    rs_["ent_raw"], rs_["masked"] = rs_["ent"], masked_
                    rs_["ent"] = _entropy(rest_) if len(rest_) >= 1024 else 0.0
    except (struct.error, IndexError, ValueError, OverflowError):
        pass
    rich = None
    try:
        rich = _rich_header(d, pe_off)
    except (struct.error, IndexError, ValueError):
        pass
    signers: list[str] = []
    cert_spans: list[tuple[int, int]] = []
    cert_extra = 0
    if len(dirs) > 4 and dirs[4][0] and dirs[4][1]:
        try:
            signers = _signers(d, dirs[4][0], dirs[4][1])
        except Exception:
            pwarn.append("blok tanda tangan Authenticode ada tetapi tidak bisa diurai: penandatangan tidak diketahui")
        try:
            cert_spans, cert_extra = _cert_spans(d, dirs[4][0], dirs[4][1])
        except Exception:
            cert_spans, cert_extra = [], 0
    entry_sec = ""
    for s_ in secs:
        if s_["va"] <= entry < s_["va"] + max(s_["vsize"], s_["rsize"]):
            entry_sec = s_["name"]
            break
    cert = dirs[4] if len(dirs) > 4 else (0, 0)
    last_raw = max([s["rptr"] + s["rsize"] for s in secs] or [0])
    overlay = max(0, file_size - last_raw) if last_raw else 0
    if cert[0] and cert[1] and cert[0] >= last_raw:   # v94: blob Authenticode ada di akhir file; bukan overlay
        overlay = max(0, overlay - cert[1])
        if overlay < 8:
            overlay = 0
    try:
        stamp = _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "0"
    except (OverflowError, OSError, ValueError):
        stamp = "tidak valid"
    return {
        "arch": _MACHINE.get(machine, hex(machine)), "bits": 64 if is64 else 32,
        "dll": bool(chars & 0x2000), "subsys": _SUBSYS.get(subsys, str(subsys)),
        "stamp": stamp, "ts": ts, "entry": entry, "entry_sec": entry_sec, "imphash": imph, "ord_imports": ord_imp,
        "tls": bool(len(dirs) > 9 and dirs[9][0]), "delay": bool(len(dirs) > 13 and dirs[13][0]),
        "res": res, "ver": ver, "rich": rich, "signers": signers, "cert_spans": cert_spans, "cert_extra": cert_extra,
        "aslr": bool(dllch & 0x40), "dep": bool(dllch & 0x100), "cfg": bool(dllch & 0x4000),
        "dotnet": len(dirs) > 14 and dirs[14][0] != 0 and dirs[14][1] != 0,
        "signed": cert[0] != 0 and cert[1] != 0, "overlay": overlay, "last_raw": last_raw, "delay_imports": delay_imports,
        "sections": secs, "imports": imports, "exports": exports, "budget_hit": budget_hit, "pwarn": pwarn,
    }


