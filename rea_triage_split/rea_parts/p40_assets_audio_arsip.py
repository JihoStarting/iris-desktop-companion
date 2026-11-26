# rea_triage bagian 40/47: assets_audio_arsip (baris asli 18368-19264). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def _wav_inspect(d, p):
    pos, fmt, data_len, extra = 12, None, 0, []
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        if t == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", d, pos + 8)
        elif t == b"data":
            data_len = min(ln, len(d) - pos - 8)
        elif t in (b"LIST", b"smpl", b"cue ", b"bext", b"id3 "):
            extra.append(t.decode("latin-1").strip())
        pos += 8 + ln + (ln & 1)
    if not fmt:
        return {"lines": ["WAV tanpa chunk fmt (rusak)"]}
    tag, ch, sr, br, ba, bits = fmt
    dur = data_len / br if br else 0
    names = {1: "PCM", 3: "float", 2: "MS-ADPCM", 17: "IMA-ADPCM", 85: "MP3", 0xFFFE: "extensible"}
    return {"lines": ["WAV %s, %d kanal, %d Hz, %d-bit, durasi %.2f dtk" % (names.get(tag, "tag %d" % tag), ch, sr, bits, dur)] + (["chunk lain: " + ", ".join(extra)] if extra else [])}


register("WAV", "audio", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WAVE", _wav_inspect, None, 14, "WAV (RIFF)")


def _ogg_inspect(d, p):
    n = len(d)
    ln = d[26]
    first = bytes(d[27 + ln:27 + ln + 64])
    rate = ch = 0
    kind = "?"
    pre = 0
    if first[:7] == b"\x01vorbis":
        kind, ch, rate = "Vorbis", first[11], _u32(first, 12)
    elif first[:8] == b"OpusHead":
        kind, ch, rate, pre = "Opus", first[9], 48000, struct.unpack_from("<H", first, 10)[0]
    elif first[:5] == b"\x7fFLAC":
        kind = "FLAC-dalam-Ogg"
    elif first[:8] == b"\x80theora" or first[:7] == b"\x80theora":
        kind = "Theora (video)"
    last = bytes(d).rfind(b"OggS", max(0, n - 70000))
    dur = 0.0
    if last >= 0 and rate:
        gp = struct.unpack_from("<q", d, last + 6)[0]
        dur = max(0, gp - pre) / rate
    return {"lines": ["OGG %s, %d kanal, %d Hz, durasi ~%.2f dtk" % (kind, ch, rate, dur)]}


register("OGG", "audio", lambda d, e: d[:4] == b"OggS" and len(d) > 40, _ogg_inspect, None, 14, "Ogg (Vorbis / Opus)")


def _flac_inspect(d, p):
    v = int.from_bytes(d[18:26], "big")
    rate, ch, bps, total = v >> 44, ((v >> 41) & 7) + 1, ((v >> 36) & 31) + 1, v & ((1 << 36) - 1)
    return {"lines": ["FLAC %d Hz, %d kanal, %d-bit, durasi %.2f dtk" % (rate, ch, bps, total / rate if rate else 0)]}


register("FLAC", "audio", lambda d, e: d[:4] == b"fLaC" and len(d) > 42, _flac_inspect, None, 14, "FLAC")

_MP3_BR = {1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0], 2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]}
_MP3_SR = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}


def _mp3_start(d):
    pos = 0
    if d[:3] == b"ID3" and len(d) > 10:
        pos = 10 + ((d[6] & 0x7F) << 21 | (d[7] & 0x7F) << 14 | (d[8] & 0x7F) << 7 | (d[9] & 0x7F))
    for i in range(pos, min(len(d) - 4, pos + 65536)):
        if d[i] == 0xFF and (d[i + 1] & 0xE0) == 0xE0 and (d[i + 1] >> 1) & 3 == 1 and (d[i + 1] >> 3) & 3 != 1 and (d[i + 2] >> 4) != 15 and ((d[i + 2] >> 2) & 3) != 3:
            return pos, i
    return pos, -1


def _mp3_detect(d, e):
    if d[:3] == b"ID3":
        return True
    return e == ".mp3" and _mp3_start(d)[1] >= 0


def _mp3_inspect(d, p):
    tag, i = _mp3_start(d)
    if i < 0:
        return {"lines": ["MP3 (ID3 ada, frame audio tidak ditemukan)"]}
    ver = (d[i + 1] >> 3) & 3
    br = _MP3_BR[1 if ver == 3 else 2][d[i + 2] >> 4]
    sr = _MP3_SR[ver][(d[i + 2] >> 2) & 3]
    ch = 1 if (d[i + 3] >> 6) == 3 else 2
    dur = (len(d) - i) * 8 / (br * 1000) if br else 0
    return {"lines": ["MP3 MPEG%s Layer III, %d kbps, %d Hz, %d kanal, durasi ~%.1f dtk (perkiraan CBR)%s" % (
        "1" if ver == 3 else "2", br, sr, ch, dur, ", ID3v2 %d byte" % tag if tag else "")]}


register("MP3", "audio", _mp3_detect, _mp3_inspect, None, 45, "MP3")


def _midi_inspect(d, p):
    fmt, nt, div = struct.unpack_from(">HHH", d, 8)
    return {"lines": ["MIDI format %d, %d track, %s" % (fmt, nt, "%d tick/beat" % div if not div & 0x8000 else "waktu SMPTE")]}


register("MIDI", "audio", lambda d, e: d[:8] == b"MThd\x00\x00\x00\x06" and len(d) >= 14, _midi_inspect, None, 14, "Standard MIDI")


# ---------------------------------------------------------------------------
# Arsip / paket game (pola umum: daftar entri + pembaca)
# ---------------------------------------------------------------------------

class _Arc:
    def __init__(self, entries, read, notes=None, close=None, kind=""):
        self.entries, self.read, self.notes, self.close, self.kind = entries, read, notes or [], close, kind


def _arc_inspect_factory(lister):
    def inspect(d, p):
        a = lister(d, p)
        try:
            ents = a.entries
            tot = sum(e.get("size", 0) for e in ents)
            ext = collections.Counter((os.path.splitext(e["name"])[1].lower() or "(tanpa ekstensi)") for e in ents)
            L = ["%s: %d entri, total %s" % (a.kind, len(ents), _as_human(tot))]
            if ext:
                L.append("jenis: " + ", ".join("%s x%d" % kv for kv in ext.most_common(10)))
            L += a.notes
            for e in ents[:25]:
                L.append("  %s  %s%s" % (_as_clean(e["name"], 90), _as_human(e.get("size", 0)), "  [terenkripsi]" if e.get("enc") else ""))
            if len(ents) > 25:
                L.append("  ... +%d entri lagi (ekstrak untuk daftar lengkap di manifest)" % (len(ents) - 25))
            return {"lines": L, "extract": "semua entri (filter dengan pola, mis. *.dds); tekstur / model di dalamnya ikut dikonversi bila convert=True",
                    "entries": [{"name": e["name"], "size": e.get("size", 0)} for e in ents[:2000]]}
        finally:
            if a.close:
                a.close()
    return inspect


def _arc_extract_factory(lister):
    def extract(d, p, out, opts):
        a = lister(d, p)
        pat = (opts.get("pattern") or "").lower()
        try:
            for e in a.entries:
                nm = e["name"]
                if pat and not fnmatch.fnmatch(nm.lower(), pat) and not fnmatch.fnmatch(os.path.basename(nm).lower(), pat):
                    continue
                if e.get("enc") and not (a.kind == "Unreal PAK" and _AES_KEY_CTX.get() is not None):   # v99.54: pak terenkripsi dibaca bila kunci AES diberikan
                    out.skipped.append({"path": nm, "reason": "terenkripsi (butuh kunci)"})
                    continue
                if e.get("size", 0) > MAX_OUT_FILE:
                    out.skipped.append({"path": nm, "reason": "terlalu besar"})
                    continue
                try:
                    data = a.read(e)
                except Exception as ex:
                    out.errors.append("%s: %s" % (_as_clean(nm, 80), _as_clean(ex, 100)))
                    continue
                out.write(nm, data, "archive-entry")
        finally:
            if a.close:
                a.close()
    return extract


def _add_archive(name, detect, lister, about, priority=30):
    register(name, "archive", detect, _arc_inspect_factory(lister), _arc_extract_factory(lister), priority, about)


def _cstr(b) -> str:
    return bytes(b).split(b"\x00")[0].decode("latin-1")


# --- Quake PAK ---
def _qpak(d, p):
    off, ln = struct.unpack_from("<II", d, 4)
    if ln % 64 or off + ln > len(d) or ln // 64 > MAX_ENTRIES:
        raise ValueError("direktori PAK tidak valid")
    ents = []
    for i in range(ln // 64):
        nm = _cstr(d[off + 64 * i:off + 64 * i + 56])
        o, s = struct.unpack_from("<II", d, off + 64 * i + 56)
        if o + s > len(d):
            continue
        ents.append({"name": nm, "off": o, "size": s})
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), kind="Quake PAK")


_add_archive("Quake-PAK", lambda d, e: d[:4] == b"PACK" and len(d) >= 12 and _u32(d, 8) % 64 == 0, _qpak, "paket Quake / Quake II (PACK)")


# --- WAD ---
def _wad(d, p):
    m = bytes(d[:4])
    n, off = struct.unpack_from("<II", d, 4)
    if n > MAX_ENTRIES:
        raise ValueError("terlalu banyak lump")
    ents, notes = [], []
    if m in (b"IWAD", b"PWAD"):
        for i in range(n):
            o, s = struct.unpack_from("<ii", d, off + 16 * i)
            ents.append({"name": _cstr(d[off + 16 * i + 8:off + 16 * i + 16]), "off": o, "size": s})
        kind = "Doom WAD (%s)" % m.decode()
    else:
        for i in range(n):
            o, ds, s, t, c = struct.unpack_from("<iiiBB", d, off + 32 * i)
            ents.append({"name": _cstr(d[off + 32 * i + 16:off + 32 * i + 32]), "off": o, "size": s, "dsize": ds, "type": t, "comp": c,
                         "enc": c != 0})
        kind = "%s (Quake / Half-Life)" % m.decode()
        notes.append("lump tekstur (type 0x43) belum dikonversi ke gambar" if any(e.get("type") == 0x43 for e in ents) else "")
        notes = [x for x in notes if x]
    ents = [e for e in ents if 0 <= e["off"] and e["size"] >= 0 and e["off"] + e.get("dsize", e["size"]) <= len(d)]
    seen = collections.Counter()
    for e in ents:     # nama lump boleh kembar: bedakan
        seen[e["name"]] += 1
        if seen[e["name"]] > 1:
            e["name"] = "%s_%d" % (e["name"], seen[e["name"]])
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), notes, kind=kind)


_add_archive("WAD", lambda d, e: len(d) >= 12 and bytes(d[:4]) in (b"IWAD", b"PWAD", b"WAD2", b"WAD3"), _wad, "WAD (Doom / Quake / Half-Life)")


# --- LZ4 (blok mentah, tanpa pembungkus frame) ---
def _lz4_block(src, usize: int) -> bytes:
    """Dekompresi satu blok LZ4 mentah ke paling banyak `usize` byte (hasil harus tepat usize). Murni Python; keluaran dibatasi
    (blok berbahaya tidak bisa mengembang melebihi usize). ValueError bila rusak / terpotong / melebihi ukuran."""
    if usize < 0 or usize > MAX_OUT_FILE:
        raise ValueError("ukuran keluaran LZ4 tidak wajar")
    s = bytes(src)
    n = len(s)
    out = bytearray()
    i = 0
    try:
        while i < n:
            tok = s[i]
            i += 1
            ll = tok >> 4
            if ll == 15:
                while True:
                    b = s[i]
                    i += 1
                    ll += b
                    if b != 255:
                        break
            if len(out) + ll > usize:
                raise ValueError("LZ4: literal melebihi ukuran")
            out += s[i:i + ll]
            if i + ll > n:
                raise ValueError("LZ4: literal terpotong")
            i += ll
            if i >= n:
                break
            off = s[i] | (s[i + 1] << 8)
            i += 2
            if off == 0 or off > len(out):
                raise ValueError("LZ4: offset tidak sah")
            ml = tok & 15
            if ml == 15:
                while True:
                    b = s[i]
                    i += 1
                    ml += b
                    if b != 255:
                        break
            ml += 4
            if len(out) + ml > usize:
                raise ValueError("LZ4: salinan melebihi ukuran")
            st = len(out) - off
            if off >= ml:
                out += out[st:st + ml]
            else:
                pat = bytes(out[st:])
                out += (pat * (ml // off + 1))[:ml]
    except IndexError:
        raise ValueError("LZ4: data terpotong") from None
    if len(out) != usize:
        raise ValueError("LZ4: ukuran hasil %d, diharapkan %d" % (len(out), usize))
    return bytes(out)


# --- Unreal .pak (v1-v11, tanpa enkripsi) ---
_UPAK_MAGIC = 0x5A6F12E1


def _fstr(d, pos):
    n = struct.unpack_from("<i", d, pos)[0]
    pos += 4
    if n < 0:
        n = -n
        s = bytes(d[pos:pos + 2 * n]).decode("utf-16-le", "replace").rstrip("\x00")
        return s, pos + 2 * n
    s = bytes(d[pos:pos + n]).decode("utf-8", "replace").rstrip("\x00")
    return s, pos + n


def _upak_entry(d, pos, ver):
    st = pos
    off, size, usize, comp = struct.unpack_from("<QQQI", d, pos)
    pos += 28
    if ver == 1:
        pos += 8
    pos += 20
    blocks, enc, bsize = [], 0, 0
    if ver >= 3:
        if comp:
            nb = _u32(d, pos)
            pos += 4
            if nb > 1_000_000:
                raise ValueError("jumlah blok kompresi tidak wajar")
            for _ in range(nb):
                blocks.append(struct.unpack_from("<QQ", d, pos))
                pos += 16
        enc, bsize = d[pos], _u32(d, pos + 1)
        pos += 5
    return {"off": off, "csize": size, "size": usize if comp else size, "usize": usize, "comp": comp, "blocks": blocks, "enc": bool(enc), "bsize": bsize,
            "hdr": pos - st}, pos


def _upak_decode(blob, p):
    """Entri terenkode (indeks UE 4.26+, v10 / v11) pada blob[p:] -> (entri, posisi_berikut). Offset blok relatif terhadap awal entri."""
    v = struct.unpack_from("<I", blob, p)[0]
    p += 4
    comp, enc, nb = (v >> 23) & 0x3F, bool(v & (1 << 22)), (v >> 6) & 0xFFFF
    bs = v & 0x3F
    if bs == 0x3F:
        bs = struct.unpack_from("<I", blob, p)[0]
        p += 4
    else:
        bs <<= 11

    def rd(flag):
        nonlocal p
        if v & flag:
            x = struct.unpack_from("<I", blob, p)[0]
            p += 4
        else:
            x = struct.unpack_from("<Q", blob, p)[0]
            p += 8
        return x
    off = rd(1 << 31)
    usize = rd(1 << 30)
    size = rd(1 << 29) if comp else usize
    hdr = 48 + 5 + ((4 + 16 * nb) if comp else 0)
    blocks = []
    if nb:
        if nb == 1 and not enc:
            blocks = [(hdr, hdr + size)]
        else:
            cur = hdr
            for _ in range(nb):
                sz = struct.unpack_from("<I", blob, p)[0]
                p += 4
                blocks.append((cur, cur + sz))
                cur += ((sz + 15) & ~15) if enc else sz
    return {"off": off, "csize": size, "size": usize, "usize": usize, "comp": comp, "blocks": blocks, "enc": enc, "bsize": bs, "hdr": hdr}, p


def _upak_v10(d, ioff, ver, ix=None, aes=None):
    """Indeks utama v10 / v11: mount point, entri terenkode + tak-terenkode, nama dari indeks direktori penuh (bila ada).
    Mengembalikan (mount, entri, catatan). v99.54: `ix` = indeks primer yang sudah didekripsi (posisi 0; None = baca dari `d` di `ioff`),
    `aes` = kunci untuk mendekripsi indeks direktori penuh (hanya bila indeks terenkripsi)."""
    if ix is not None:
        d_, pos = ix, 0
    else:
        d_, pos = d, ioff
    mount, pos = _fstr(d_, pos)
    cnt = _u32(d_, pos)
    pos += 4
    if cnt > MAX_ENTRIES:
        raise ValueError("terlalu banyak entri PAK")
    pos += 8   # path hash seed
    has_ph = _u32(d_, pos)
    pos += 4
    if has_ph:
        pos += 8 + 8 + 20
    has_fd = _u32(d_, pos)
    pos += 4
    fd_off = fd_sz = 0
    if has_fd:
        fd_off, fd_sz = struct.unpack_from("<qq", d_, pos)
        pos += 8 + 8 + 20
    en = _u32(d_, pos)
    pos += 4
    if pos + en > len(d_):
        raise ValueError("blob entri terenkode melewati batas berkas")
    blob = bytes(d_[pos:pos + en])
    pos += en
    nn = _u32(d_, pos)
    pos += 4
    nonenc = []
    for _ in range(min(nn, MAX_ENTRIES)):
        e, pos = _upak_entry(d_, pos, ver)
        nonenc.append(e)
    pre = mount.replace("../../../", "")
    ents, notes = [], []
    if has_fd and 0 <= fd_off and fd_off + fd_sz <= len(d):
        if aes is not None:                                   # v99.54: indeks direktori penuh ikut terenkripsi bila indeks terenkripsi
            fb, p = _aes_ecb(aes, bytes(d[fd_off:fd_off + (fd_sz & ~15)]), True), 0
        else:
            fb, p = d, fd_off
        nd = _u32(fb, p)
        p += 4
        for _ in range(min(nd, MAX_ENTRIES)):
            dn, p = _fstr(fb, p)
            nf = _u32(fb, p)
            p += 4
            for _ in range(min(nf, MAX_ENTRIES)):
                fn, p = _fstr(fb, p)
                eo = struct.unpack_from("<i", fb, p)[0]
                p += 4
                try:
                    e = dict(_upak_decode(blob, eo)[0]) if eo >= 0 else dict(nonenc[-(eo + 1)])
                except (struct.error, IndexError):
                    continue
                e["name"] = pre + dn.lstrip("/") + fn
                ents.append(e)
                if len(ents) >= MAX_ENTRIES:
                    break
            if len(ents) >= MAX_ENTRIES:
                break
    else:
        notes.append("indeks direktori penuh tidak ada: nama berkas tidak bisa dipulihkan (hanya hash path); entri diberi nama entry_NNNNNN")
        p = 0
        while p < len(blob) and len(ents) < MAX_ENTRIES:
            try:
                e, p = _upak_decode(blob, p)
            except struct.error:
                break
            e["name"] = "%sentry_%06d" % (pre, len(ents))
            ents.append(e)
        for e in nonenc:
            e = dict(e)
            e["name"] = "%sentry_%06d" % (pre, len(ents))
            ents.append(e)
    return mount, ents, notes


def _upak_raw(d, p):
    zdict = _ZSTD_DICT_CTX.get()                                        # v99.53: ditangkap saat pak dibuka (read() bisa dipanggil lewat closure)
    keys = _aes_keyset(_AES_KEY_CTX.get())                              # v99.54 / v99.55: daftar [(guid | None, kunci AES-256)] atau None
    n = len(d)
    tail_start = max(0, n - 512)
    tail = bytes(d[tail_start:])
    magic = struct.pack("<I", _UPAK_MAGIC)
    k = tail.rfind(magic)
    found = None
    while k >= 0:
        a = tail_start + k
        if a + 44 <= n:
            ver, ioff, isz = _u32(d, a + 4), _u64(d, a + 8), _u64(d, a + 16)
            if 1 <= ver <= 11 and ioff + isz <= n:
                found = (a, ver, ioff, isz)
                break
        k = tail.rfind(magic, 0, k)
    if not found:
        raise ValueError("footer Unreal PAK tidak ditemukan")
    a, ver, ioff, isz = found
    idx_enc = ver >= 4 and bool(d[a - 1])
    pak_guid = None                                                     # v99.55: GUID kunci enkripsi di footer (v7+), urutan A B C D; nol -> None
    if ver >= 7 and a >= 17:
        pak_guid = _aes_guid_norm("%08X%08X%08X%08X" % struct.unpack_from("<4I", d, a - 17))
    if idx_enc and not keys:
        raise ValueError("indeks PAK terenkripsi (butuh kunci AES%s; berikan lewat --aes [GUID:]KUNCI)" % ("; GUID pak %s" % pak_guid if pak_guid else ""))
    aes, ix, sel = None, None, ""
    if idx_enc:                                                         # v99.54: dekripsi indeks primer (ECB, dibulatkan ke kelipatan 16)
        ilen = (isz + 15) & ~15
        if ioff + ilen > n:
            ilen = isz & ~15
        if ilen <= 0 or ioff + ilen > n:
            raise ValueError("indeks PAK terenkripsi terpotong")
        iblob = bytes(d[ioff:ioff + ilen])
        cands = _aes_candidates(keys, pak_guid)
        for lab_, k_ in cands:                                          # v99.55: kunci dipilih lewat GUID; mount point yang wajar membuktikan kunci benar
            ix_ = _aes_ecb(k_, iblob, True)
            m_ = struct.unpack_from("<i", ix_, 0)[0]
            if (-4096 <= m_ <= 4096) and not (m_ > 0 and (4 + m_ > len(ix_) or any(c < 32 for c in ix_[4:3 + m_]) or ix_[3 + m_] != 0)) and not (m_ < 0 and 4 - 2 * m_ > len(ix_)):
                aes, ix, sel = k_, ix_, lab_
                break
        if ix is None:
            raise ValueError("kunci AES salah: indeks PAK tidak bisa dibaca setelah dekripsi (dicoba %d kunci%s)" % (len(cands), "; GUID pak %s" % pak_guid if pak_guid else ""))
    names = [""]
    rem = n - (a + 44) - (1 if ver == 9 else 0)
    if ver >= 8 and rem > 0:
        base = a + 44 + (1 if ver == 9 else 0)
        names += [_cstr(d[base + 32 * i:base + 32 * i + 32]) for i in range(rem // 32)]
    v10notes = []
    if ver >= 10:
        mount, ents, v10notes = _upak_v10(d, ioff, ver, ix=ix, aes=aes if idx_enc else None)
    else:
        d_, pos = (ix, 0) if ix is not None else (d, ioff)
        mount, pos = _fstr(d_, pos)
        cnt = _u32(d_, pos)
        pos += 4
        if cnt > MAX_ENTRIES:
            raise ValueError("terlalu banyak entri PAK")
        ents = []
        for _ in range(cnt):
            nm, pos = _fstr(d_, pos)
            e, pos = _upak_entry(d_, pos, ver)
            e["name"] = (mount.replace("../../../", "") + nm) if mount else nm
            ents.append(e)

    def read1(e, akey):
        enc = e["enc"]
        base = e["off"]

        def raw(lo, hi):                                                # v99.54: byte tersimpan lo..hi; terenkripsi -> baca sejajar 16, dekripsi, potong ke hi - lo
            if not enc:
                return bytes(d[lo:hi])
            if hi <= lo:
                return b""
            al = (hi - lo + 15) & ~15
            if lo < 0 or lo + al > n:
                raise ValueError("data terenkripsi terpotong")
            return _aes_ecb(akey, bytes(d[lo:lo + al]), True)[:hi - lo]
        if e["comp"] == 0:
            return raw(base + e["hdr"], base + e["hdr"] + e["csize"])
        meth = names[e["comp"]] if ver >= 8 and e["comp"] < len(names) else ("Zlib" if e["comp"] == 1 else "kode %d" % e["comp"])
        ml_ = meth.lower()
        lz4 = ml_.startswith("lz4")
        zst = ml_.startswith("zstd")                      # v99.32: tiap blok = satu frame Zstd utuh (dekoder murni Python v99.31)
        if not (lz4 or zst or ml_.startswith("zlib")):
            raise ValueError("kompresi %s belum didukung (zlib, LZ4, dan Zstd saja%s)" % (meth, "; Oodle butuh pustaka proprietary" if ml_.startswith("oodle") else ""))

        def run():
            out = bytearray()
            for s, en in e["blocks"]:
                lo, hi = (base + s, base + en) if ver >= 5 else (s, en)
                if zst:
                    chunk = _zstd_decompress(raw(lo, hi), max_out=min(MAX_OUT_FILE - len(out), max(e["bsize"] or e["usize"], 1) * 2 + 65536), dictionary=zdict)
                    if len(out) + len(chunk) > MAX_OUT_FILE:
                        raise ValueError("terlalu besar")
                    out += chunk
                    continue
                if lz4:
                    chunk = _lz4_block(raw(lo, hi), min(e["bsize"] or e["usize"], e["usize"] - len(out)))
                    if len(out) + len(chunk) > MAX_OUT_FILE:
                        raise ValueError("terlalu besar")
                    out += chunk
                    continue
                dobj = zlib.decompressobj()   # v103.2: dibatasi; zlib.decompress() tanpa batas bisa mengembang jadi GB dalam satu blok
                chunk = dobj.decompress(raw(lo, hi), MAX_OUT_FILE + 1 - len(out))
                if dobj.unconsumed_tail or len(out) + len(chunk) > MAX_OUT_FILE:
                    raise ValueError("terlalu besar")
                if not dobj.eof:
                    raise ValueError("blok zlib tidak lengkap")
                out += chunk
            return bytes(out[:e["usize"]])
        if not enc:
            return run()
        try:                                                            # v99.54: kunci salah -> sampah -> galat dekompresi; beri petunjuk yang jelas
            return run()
        except (ValueError, zlib.error, IndexError, struct.error, OverflowError) as ex_:
            if any(k in str(ex_) for k in ("terpotong", "terlalu besar", "melewati batas waktu")):
                raise
            raise ValueError("gagal mendekompres entri terenkripsi (kunci AES salah?)") from None
    proven = [aes]                                                      # v99.56: kunci terbukti (indeks terenkripsi membuktikan kunci; selain itu dari isi entri)

    def read(e):
        if not e["enc"]:
            return read1(e, None)
        if not keys:
            raise ValueError("terenkripsi (butuh kunci AES%s; berikan lewat --aes [GUID:]KUNCI)" % ("; GUID pak %s" % pak_guid if pak_guid else ""))
        if proven[0] is not None:
            return read1(e, proven[0])
        cands = [k_ for _, k_ in _aes_candidates(keys, pak_guid)]
        if len(cands) == 1:
            return read1(e, cands[0])
        first_err, fallback = None, None                                # v99.56: indeks polos + banyak kunci: coba tiap kandidat, pilih yang isinya terbukti
        for k_ in cands:
            try:
                out = read1(e, k_)
            except ValueError as ex_:
                if any(w in str(ex_) for w in ("terpotong", "terlalu besar", "melewati batas waktu")):
                    raise
                first_err = first_err or ex_
                continue
            if e["comp"] != 0 or _aes_plain_ok(out):                    # dekompresi sukses (ukuran benar) / plaintext masuk akal = bukti
                proven[0] = k_
                return out
            if fallback is None:
                fallback = (k_, out)
        if fallback is not None:                                        # tak bisa dibuktikan (isi biner acak / terlalu pendek): perilaku v99.55
            _aes_pick_data(keys, pak_guid)                              # beberapa kunci tanpa GUID cocok -> ValueError lama
            return fallback[1]
        raise first_err or ValueError("gagal mendekompres entri terenkripsi (kunci AES salah?)")
    aes_notes = (["GUID kunci enkripsi pak: %s" % pak_guid] if pak_guid else []) + (["dekripsi AES-256 (ECB) aktif%s%s; indeks polos + banyak kunci: kunci dipilih dari isi entri (dekompresi berhasil / plaintext masuk akal; v99.56)" % (
        " untuk indeks dan entri" if idx_enc else " untuk entri terenkripsi", " (kunci dipilih: %s)" % sel if sel else "")] if keys else [])
    return _Arc(ents, read, ["PERHATIAN: parser Unreal PAK ini baru diuji dengan berkas sintetis; bila hasil aneh, kirim contoh .pak kecil untuk diverifikasi.",
                               "mount point: %s | versi PAK: %d" % (_as_clean(mount, 60), ver)] + aes_notes + v10notes, kind="Unreal PAK")


_UPAK_BAD = (struct.error, IndexError, OverflowError, MemoryError, zlib.error, UnicodeError, KeyError, TypeError)


def _upak(d, p):
    """Pembungkus _upak_raw (v99.33): indeks / footer / entri PAK rusak selalu menjadi ValueError (bukan struct.error / IndexError dll.),
    baik saat membuka maupun saat membaca entri."""
    try:
        arc = _upak_raw(d, p)
    except ValueError:
        raise
    except _UPAK_BAD as ex:
        raise ValueError("indeks Unreal PAK rusak atau terpotong (%s)" % type(ex).__name__) from None
    raw_read = arc.read

    def safe_read(e):
        try:
            return raw_read(e)
        except ValueError:
            raise
        except _UPAK_BAD as ex:
            raise ValueError("entri Unreal PAK rusak atau terpotong (%s)" % type(ex).__name__) from None
    arc.read = safe_read
    return arc


def _upak_detect(d, e):
    n = len(d)
    return n > 60 and struct.pack("<I", _UPAK_MAGIC) in bytes(d[max(0, n - 512):])


_add_archive("Unreal-PAK", _upak_detect, _upak, "Unreal Engine .pak (v1-v11; zlib, LZ4, Zstd; enkripsi AES-256 dengan --aes)", 28)


# --- ZIP ---
def _zip(d, p):
    if _zip_cd_bytes(p) > MAX_ZIP_CD:   # v104
        raise ValueError("direktori pusat ZIP terlalu besar")
    zf = zipfile.ZipFile(p)
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        zf.close()
        raise ValueError("terlalu banyak entri ZIP")
    ents = [{"name": i.filename, "size": i.file_size, "csize": i.compress_size, "info": i, "enc": bool(i.flag_bits & 1)} for i in infos if not i.is_dir()]
    names = {e["name"] for e in ents}
    kind = "ZIP"
    notes = []
    if "AndroidManifest.xml" in names:
        kind = "APK (Android)"
    elif "[Content_Types].xml" in names:
        kind = "OOXML (docx / xlsx / pptx)"
        notes.append("media tertanam ada di word/media/, xl/media/, ppt/media/")
    elif "META-INF/MANIFEST.MF" in names:
        kind = "JAR"
    elif "mimetype" in names:
        kind = "ODF / EPUB"
    elif "AndroidManifest.xml" not in names and any(n.endswith(".uasset") or n.endswith(".pak") for n in names):
        kind = "ZIP (berisi aset Unreal)"

    def read(e):
        with zf.open(e["info"]) as f:
            data = f.read(MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc(ents, read, notes, zf.close, kind)


_add_archive("ZIP", lambda d, e: d[:4] in (b"PK\x03\x04", b"PK\x05\x06") and len(d) >= 22, _zip, "ZIP, APK, JAR, OOXML, ODF, EPUB", 30)


# --- TAR / GZIP ---
def _is_tar_raw(d): return len(d) > 512 and bytes(d[257:262]) == b"ustar"


def _gz_head(d):
    try:
        return zlib.decompressobj(31).decompress(bytes(d[:4096]), 1024)
    except zlib.error:
        return b""


def _tar(d, p):
    tf = tarfile.open(p, "r:*")
    ents = []
    for m in tf:
        if m.isfile():
            ents.append({"name": m.name, "size": m.size, "m": m})
            if len(ents) > MAX_ENTRIES:
                tf.close()
                raise ValueError("terlalu banyak entri TAR")

    def read(e):
        if e["size"] > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return tf.extractfile(e["m"]).read(MAX_OUT_FILE + 1)
    return _Arc(ents, read, close=tf.close, kind="TAR")


_add_archive("TAR", lambda d, e: _is_tar_raw(d) or (d[:2] == b"\x1f\x8b" and bytes(_gz_head(d))[257:262] == b"ustar") or (d[:3] == b"BZh" and e in (".tbz", ".tbz2", ".bz2") and e != ".bz2") or (d[:6] == b"\xfd7zXZ\x00" and e == ".txz"),
             _tar, "TAR (+ .tar.gz / .tgz)", 29)


def _gzip(d, p):
    flg = d[3]
    pos = 10
    name = ""
    if flg & 4:
        pos += 2 + _u16(d, pos)
    if flg & 8:
        end = bytes(d[pos:pos + 300]).find(b"\x00")
        name = bytes(d[pos:pos + end]).decode("latin-1") if end >= 0 else ""
    isz = _u32(d, len(d) - 4)
    nm = name or (p.stem if p.suffix.lower() == ".gz" else p.name + ".out")

    def read(e):
        data = zlib.decompressobj(31).decompress(bytes(d), MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc([{"name": nm, "size": isz}], read, ["ukuran asli dari trailer (modulo 4 GB)"], kind="GZIP")


_add_archive("GZIP", lambda d, e: d[:3] == b"\x1f\x8b\x08" and len(d) > 18, _gzip, "GZIP satu berkas", 35)


# --- Unity AssetBundle (UnityFS): daftar node + ekstraksi (LZMA / LZ4 / LZ4HC); isi SerializedFile TIDAK diurai ---
def _unity_decomp(src: bytes, ctype: int, usize: int) -> bytes:
    if usize > MAX_OUT_FILE:
        raise ValueError("ukuran blok Unity terlalu besar")
    if ctype == 0:
        out = bytes(src[:usize])
    elif ctype == 1:
        try:
            import lzma
        except ImportError:
            raise ValueError("modul lzma tidak tersedia di Python ini (blok LZMA tidak bisa dibuka)") from None
        if len(src) < 6:
            raise ValueError("blok LZMA terlalu pendek")
        pr = src[0]
        dsz = struct.unpack_from("<I", src, 1)[0]
        if pr >= 9 * 5 * 5 or dsz > 256 * 1024 * 1024:
            raise ValueError("properti LZMA tidak wajar")
        flt = [{"id": lzma.FILTER_LZMA1, "dict_size": max(dsz, 4096), "lc": pr % 9, "lp": (pr // 9) % 5, "pb": pr // 45}]
        try:
            out = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=flt).decompress(bytes(src[5:]), max_length=usize)
        except lzma.LZMAError as e:
            raise ValueError("LZMA rusak: %s" % e) from None
    elif ctype in (2, 3):
        out = _lz4_block(src, usize)
    else:
        raise ValueError("jenis kompresi Unity %d tidak dikenal" % ctype)
    if len(out) != usize:
        raise ValueError("ukuran hasil dekompresi tidak cocok (%d, diharapkan %d)" % (len(out), usize))
    return out


def _unityfs(d, p):
    if len(d) < 48:
        raise ValueError("berkas UnityFS terlalu pendek")
    pos = 8
    ver = _b32(d, pos)
    pos += 4

    def cs():
        nonlocal pos
        end = bytes(d[pos:pos + 256]).find(b"\x00")
        if end < 0:
            raise ValueError("header UnityFS rusak")
        s = bytes(d[pos:pos + end]).decode("latin-1")
        pos += end + 1
        return s
    uver, rev = cs(), cs()
    size, cbi, ubi, flags = struct.unpack_from(">qIII", d, pos)
    pos += 20
    if cbi > 64 * 1024 * 1024 or ubi > 64 * 1024 * 1024:
        raise ValueError("blok info UnityFS tidak wajar")
    m = re.match(r"(\d+)\.(\d+)", uver)
    if ver >= 7:
        pos = (pos + 15) & ~15
    elif m and (int(m[1]), int(m[2])) >= (2019, 4):   # format 6 pada Unity 2019.4+: padding opsional
        pad = (16 - pos % 16) % 16
        if not any(bytes(d[pos:pos + pad])):
            pos += pad
    if flags & 0x80:   # blok info di akhir berkas
        info_off, data_off = len(d) - cbi, pos
    else:
        info_off, data_off = pos, pos + cbi
    if flags & 0x200:
        data_off = (data_off + 15) & ~15
    if info_off < 0 or info_off + cbi > len(d):
        raise ValueError("blok info UnityFS di luar berkas")
    info = _unity_decomp(bytes(d[info_off:info_off + cbi]), flags & 0x3F, ubi)
    q = 16   # hash
    nb = struct.unpack_from(">I", info, q)[0]
    q += 4
    if nb > MAX_ENTRIES:
        raise ValueError("terlalu banyak blok Unity")
    blocks, cpos, upos = [], data_off, 0
    for _ in range(nb):
        us, cz, fl = struct.unpack_from(">IIH", info, q)
        q += 10
        if cpos + cz > len(d):
            raise ValueError("blok data Unity melewati batas berkas")
        blocks.append((upos, us, cpos, cz, fl & 0x3F))
        upos += us
        cpos += cz
    nn = struct.unpack_from(">I", info, q)[0]
    q += 4
    if nn > MAX_ENTRIES:
        raise ValueError("terlalu banyak node Unity")
    ents = []
    for _ in range(nn):
        off, sz, nf = struct.unpack_from(">qqI", info, q)
        q += 20
        end = info.index(b"\x00", q)
        nm = info[q:end].decode("utf-8", "replace")
        q = end + 1
        if off < 0 or sz < 0 or off + sz > upos:
            continue
        ents.append({"name": nm or "node_%d" % len(ents), "off": off, "size": sz, "nflags": nf})
    starts = [b[0] for b in blocks]
    cache: dict = {}

    def read(e):
        if e["size"] > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        buf = bytearray()
        lo, hi = e["off"], e["off"] + e["size"]
        i = max(0, bisect.bisect_right(starts, lo) - 1)
        while i < len(blocks) and blocks[i][0] < hi:
            us_, usz, cp, cz, ct = blocks[i]
            if i not in cache:
                if len(cache) >= 4:
                    cache.pop(next(iter(cache)))
                cache[i] = _unity_decomp(bytes(d[cp:cp + cz]), ct, usz)
            blk = cache[i]
            buf += blk[max(lo, us_) - us_:min(hi, us_ + usz) - us_]
            i += 1
        if len(buf) != e["size"]:
            raise ValueError("data node tidak lengkap")
        return bytes(buf)
    return _Arc(ents, read, ["Unity %s (revisi %s), format UnityFS v%d; node diekstrak apa adanya (SerializedFile 'CAB-*' dan aliran .resS)." % (_as_clean(uver, 30), _as_clean(rev, 30), ver),
                             ] + _unityfs_objects_note(p), kind="Unity AssetBundle")


register("UnityFS", "archive", lambda d, e: bytes(d[:8]) == b"UnityFS\x00", _arc_inspect_factory(_unityfs), lambda d, p, out, opts: _unityfs_extract(d, p, out, opts), 20,
         "Unity AssetBundle (UnityFS; LZMA / LZ4 / LZ4HC); objek Texture2D / Mesh / AnimationClip / TextAsset didekode (v99.21)")


# --- deteksi-saja: 7z, RAR ---
register("7z", "archive", lambda d, e: d[:6] == b"7z\xbc\xaf\x27\x1c",
         lambda d, p: {"lines": ["7-Zip, versi %d.%d. Ekstrak dengan 7-Zip lalu arahkan REA ke folder hasil." % (d[6], d[7])]}, None, 20, "7z (deteksi saja)")
register("RAR", "archive", lambda d, e: d[:6] == b"Rar!\x1a\x07",
         lambda d, p: {"lines": ["RAR %s. Ekstrak dengan unrar / 7-Zip lalu arahkan REA ke folder hasil." % ("v5" if d[6] == 1 else "v4")]}, None, 20, "RAR (deteksi saja)")


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

def _sql_open(p: Path):
    uri = "file:%s?mode=ro&immutable=1" % urllib.parse.quote(str(p.resolve()))
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=ON")
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    return con


def _sql_tables(con):
    return [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 500")]


def _sql_inspect(d, p):
    ps = struct.unpack_from(">H", d, 16)[0] or 65536
    con = _sql_open(p)
    try:
        L = ["SQLite: halaman %d byte x %d" % (ps, _b32(d, 28))]
        for t in _sql_tables(con)[:60]:
            q = '"%s"' % t.replace('"', '""')
            n = con.execute("SELECT COUNT(*) FROM %s" % q).fetchone()[0]
            cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % q)]
            L.append("  tabel %s: %d baris [%s]" % (_as_clean(t, 40), n, ", ".join(_as_clean(c, 20) for c in cols[:10])))
        return {"lines": L, "extract": "tiap tabel -> .csv"}
    finally:
        con.close()


def _sql_extract(d, p, out, opts):
    con = _sql_open(p)
    try:
        for t in _sql_tables(con):
            q = '"%s"' % t.replace('"', '""')
            cur = con.execute("SELECT * FROM %s LIMIT 2000000" % q)
            cols = [c[0] for c in cur.description]
            rows = []
            for r in cur:
                rows.append(["base64:" + base64.b64encode(v).decode() if isinstance(v, (bytes, bytearray)) and len(v) <= 65536 else
                             "<blob %d byte>" % len(v) if isinstance(v, (bytes, bytearray)) else v for v in r])
            out.write_text("tables/%s.csv" % _obj_name(t, "table"), _csv_text(rows, cols), "table", "%d baris" % len(rows))
    finally:
        con.close()


register("SQLite", "database", lambda d, e: d[:16] == b"SQLite format 3\x00", _sql_inspect, _sql_extract, 12, "database SQLite")


