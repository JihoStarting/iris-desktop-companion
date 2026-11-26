# rea_triage bagian 41/47: assets_carve_zstd (baris asli 19265-20762). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# Carving: cari berkas tertanam di dalam berkas apa pun
# ---------------------------------------------------------------------------

def _len_png(d, o):
    pos, n = o + 8, len(d)
    while pos + 12 <= n:
        ln = _b32(d, pos)
        t = bytes(d[pos + 4:pos + 8])
        pos += 12 + ln
        if t == b"IEND":
            return pos - o
        if ln > n:
            return None
    return None


def _len_gif(d, o):
    try:
        return _gif_walk(d, o)["end"]
    except (ValueError, struct.error, IndexError):
        return None


def _len_riff(d, o):
    ln = _u32(d, o + 4) + 8
    return ln if 12 < ln <= len(d) - o else None


def _len_ogg(d, o):
    pos, n = o, len(d)
    while pos + 27 <= n and bytes(d[pos:pos + 4]) == b"OggS":
        ns = d[pos + 26]
        if pos + 27 + ns > n:
            return None
        size = 27 + ns + sum(d[pos + 27:pos + 27 + ns])
        eos = d[pos + 5] & 4
        pos += size
        if eos:
            return pos - o
    return None


def _len_glb(d, o):
    ln = _u32(d, o + 8)
    return ln if 20 <= ln <= len(d) - o else None


def _len_midi(d, o):
    pos, n = o + 14, len(d)
    for _ in range(_u16(d, o + 10)):
        if pos + 8 > n or bytes(d[pos:pos + 4]) != b"MTrk":
            return None
        pos += 8 + _b32(d, pos + 4)
    return pos - o if pos <= n else None


def _len_sqlite(d, o):
    ps = struct.unpack_from(">H", d, o + 16)[0] or 65536
    pg = _b32(d, o + 28)
    ln = ps * pg
    return ln if pg and ln <= len(d) - o else None


def _len_zip(d, o):
    k = bytes(d[o:o + 64 * 1024 * 1024]).find(b"PK\x05\x06")
    if k < 0 or o + k + 22 > len(d):
        return None
    return k + 22 + _u16(d, o + k + 20)


class _RX(bytes):
    """Penanda: isinya pola regex mentah (bukan literal) untuk tabel _SIGS; byte variabel boleh dipakai."""


def _leb_u32(d, pos, n):
    v = sh = 0
    for _ in range(5):
        if pos >= n:
            return None, pos
        b = d[pos]
        pos += 1
        v |= (b & 0x7F) << sh
        if not b & 0x80:
            return v, pos
        sh += 7
    return None, pos


_WASM_RANK = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 13: 6, 6: 7, 7: 8, 8: 9, 9: 10, 12: 11, 10: 12, 11: 13}   # urutan kanonik section non-custom


def _len_wasm(d, o):
    """Modul WebAssembly: telusuri section (id, ukuran LEB128) sampai urutan kanonik / batas berkas putus."""
    n, pos, secs, prev = len(d), o + 8, 0, 0
    while pos < n:
        sid = d[pos]
        if sid > 13:
            break
        sz, p2 = _leb_u32(d, pos + 1, n)
        if sz is None or p2 + sz > n:
            break
        if sid:
            if _WASM_RANK[sid] <= prev:
                break
            prev = _WASM_RANK[sid]
        pos = p2 + sz
        secs += 1
    return pos - o if secs else None


def _len_wal(d, o):
    """SQLite WAL: header 32 byte + frame (24 + ukuran halaman) selama salt frame sama dengan salt header."""
    n = len(d)
    if o + 32 > n:
        return None
    ps = _b32(d, o + 8)
    if ps < 512 or ps > 65536 or ps & (ps - 1):
        return None
    salt, fr, pos, k = bytes(d[o + 16:o + 24]), 24 + ps, o + 32, 0
    while pos + fr <= n and bytes(d[pos + 8:pos + 16]) == salt and _b32(d, pos) > 0:
        pos += fr
        k += 1
    return pos - o if k else None


def _len_pem(d, o):
    """Blok PEM: dari -----BEGIN X----- sampai -----END X----- (label harus sama), termasuk newline penutup."""
    seg = bytes(d[o:o + 262144])
    b = seg.find(b"-----", 11)
    k = seg.find(b"-----END ")
    if b < 0 or k < 0:
        return None
    e0 = seg.find(b"-----", k + 9)
    if e0 < 0 or seg[11:b] != seg[k + 9:e0]:
        return None
    e = e0 + 5
    if seg[e:e + 2] == b"\r\n":
        e += 2
    elif seg[e:e + 1] == b"\n":
        e += 1
    return e


def _len_der_cert(d, o):
    """Sertifikat X.509 DER: SEQUENCE { tbsCertificate SEQUENCE, signatureAlgorithm SEQUENCE { OID ...} ...}. Panjang dari header; strukturnya divalidasi."""
    n = len(d)
    if o + 12 > n:
        return None
    tot = 4 + ((d[o + 2] << 8) | d[o + 3])
    tbs = 4 + ((d[o + 6] << 8) | d[o + 7])
    alg = o + 4 + tbs
    if tot < 200 or o + tot > n or tbs > tot - 4 or alg + 3 > o + tot or d[alg] != 0x30 or d[alg + 2] != 0x06:
        return None
    return tot


def _len_zstd(d, o):
    """Frame Zstandard: panjang persis dari header frame + header block (raw / RLE / terkompresi), plus checksum 4 byte bila ada."""
    n, pos = len(d), o + 4
    if pos >= n:
        return None
    fd = d[pos]
    if fd & 0x08:
        return None   # bit cadangan harus 0
    single, dflag, csum = (fd >> 5) & 1, fd & 3, (fd >> 2) & 1
    pos += 1 + (0 if single else 1) + (0, 1, 2, 4)[dflag] + ((1 if single else 0), 2, 4, 8)[fd >> 6]
    for _ in range(2_000_000):
        if pos + 3 > n:
            return None
        bh = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16)
        typ, sz = (bh >> 1) & 3, bh >> 3
        if typ == 3 or sz > 131072:
            return None
        pos += 3 + (1 if typ == 1 else sz)
        if pos > n:
            return None
        if bh & 1:
            pos += 4 if csum else 0
            return pos - o if pos <= n else None
    return None


# --- Zstandard (RFC 8878): dekoder murni Python (v99.31; dictionary v99.51). Tanpa streaming; keluaran dan waktu dibatasi ---
ZSTD_TIME = 30.0                         # detik per pemanggilan _zstd_decompress
ZSTD_BLOCK_MAX = 128 * 1024              # batas ukuran blok (spesifikasi)
ZSTD_VERIFY_MAX = 64 * 1024 * 1024       # checksum xxh64 hanya diverifikasi bila keluaran <= ini (xxh64 murni Python lambat)

_ZSTD_LL_DEF = (4, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1,
                2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 1, 1, 1, 1, 1,
                -1, -1, -1, -1)
_ZSTD_ML_DEF = (1, 4, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1,
                -1, -1, -1, -1, -1)
_ZSTD_OF_DEF = (1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1)
_ZSTD_LL_BASE = tuple(range(16)) + (16, 18, 20, 22, 24, 28, 32, 40, 48, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)
_ZSTD_LL_BITS = (0,) * 16 + (1, 1, 1, 1, 2, 2, 3, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
_ZSTD_ML_BASE = tuple(range(3, 35)) + (35, 37, 39, 41, 43, 47, 51, 59, 67, 83, 99, 131, 259, 515, 1027, 2051, 4099, 8195, 16387, 32771, 65539)
_ZSTD_ML_BITS = (0,) * 32 + (1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
_ZSTD_DEF_CACHE: dict = {}

_XXH_P1, _XXH_P2, _XXH_P3, _XXH_P4, _XXH_P5 = (11400714785074694791, 14029467366897019727, 1609587929392839161,
                                               9650029242287828579, 2870177450012600261)
_XXH_M = (1 << 64) - 1


def _xxh64(data, seed: int = 0) -> int:
    """xxHash64 murni Python (dipakai verifikasi checksum frame Zstd; hanya 32 bit rendah yang dibandingkan)."""
    M, P1, P2, P3, P4, P5 = _XXH_M, _XXH_P1, _XXH_P2, _XXH_P3, _XXH_P4, _XXH_P5
    n = len(data)
    i = 0
    if n >= 32:
        v1, v2, v3, v4 = (seed + P1 + P2) & M, (seed + P2) & M, seed & M, (seed - P1) & M
        for a, b, c, e in struct.iter_unpack("<4Q", bytes(data[:n - (n % 32)])):
            v1 = (((((v1 + a * P2) & M) << 31 | ((v1 + a * P2) & M) >> 33) & M) * P1) & M
            v2 = (((((v2 + b * P2) & M) << 31 | ((v2 + b * P2) & M) >> 33) & M) * P1) & M
            v3 = (((((v3 + c * P2) & M) << 31 | ((v3 + c * P2) & M) >> 33) & M) * P1) & M
            v4 = (((((v4 + e * P2) & M) << 31 | ((v4 + e * P2) & M) >> 33) & M) * P1) & M
        i = n - (n % 32)
        h = ((((v1 << 1) | (v1 >> 63)) + ((v2 << 7) | (v2 >> 57)) + ((v3 << 12) | (v3 >> 52)) + ((v4 << 18) | (v4 >> 46))) & M)
        for v in (v1, v2, v3, v4):
            v = (v * P2) & M
            v = (((v << 31) | (v >> 33)) & M) * P1 & M
            h = ((h ^ v) * P1 + P4) & M
    else:
        h = (seed + P5) & M
    h = (h + n) & M
    while i + 8 <= n:
        k = struct.unpack_from("<Q", data, i)[0]
        k = (k * P2) & M
        k = (((k << 31) | (k >> 33)) & M) * P1 & M
        h ^= k
        h = ((((h << 27) | (h >> 37)) & M) * P1 + P4) & M
        i += 8
    if i + 4 <= n:
        h ^= (struct.unpack_from("<I", data, i)[0] * P1) & M
        h = ((((h << 23) | (h >> 41)) & M) * P2 + P3) & M
        i += 4
    while i < n:
        h ^= (data[i] * P5) & M
        h = (((h << 11) | (h >> 53)) & M) * P1 & M
        i += 1
    h ^= h >> 33
    h = (h * P2) & M
    h ^= h >> 29
    h = (h * P3) & M
    h ^= h >> 32
    return h


def _zstd_fse_header(buf, pos: int, maxsym: int, maxlog: int):
    """Deskripsi tabel FSE (bitstream maju, LSB dulu) di buf[pos:] -> (norm, acclog, byte_terpakai). ValueError bila rusak."""
    seg = bytes(buf[pos:pos + 600])
    if not seg:
        raise ValueError("Zstd: header FSE kosong")
    v = int.from_bytes(seg, "little")
    total = len(seg) * 8
    acclog = (v & 15) + 5
    bp = 4
    if acclog > maxlog:
        raise ValueError("Zstd: accuracy log FSE terlalu besar")
    remaining = (1 << acclog) + 1
    threshold = 1 << acclog
    nb = acclog + 1
    norm: list = []
    prev0 = False
    while remaining > 1 and len(norm) <= maxsym:
        if bp > total:
            raise ValueError("Zstd: header FSE terpotong")
        if prev0:
            n0 = len(norm)
            while True:
                r = (v >> bp) & 3
                bp += 2
                n0 += r
                if r != 3:
                    break
                if bp > total:
                    raise ValueError("Zstd: header FSE terpotong")
            if n0 > maxsym + 1:
                raise ValueError("Zstd: simbol FSE melebihi batas")
            norm.extend([0] * (n0 - len(norm)))
        mx = (2 * threshold - 1) - remaining
        low = (v >> bp) & (threshold - 1)
        if low < mx:
            count = low
            bp += nb - 1
        else:
            count = (v >> bp) & (2 * threshold - 1)
            if count >= threshold:
                count -= mx
            bp += nb
        count -= 1
        remaining -= -count if count < 0 else count
        norm.append(count)
        prev0 = count == 0
        while remaining < threshold:
            nb -= 1
            threshold >>= 1
    if remaining != 1 or len(norm) > maxsym + 1 or bp > total:
        raise ValueError("Zstd: header FSE rusak")
    return norm, acclog, (bp + 7) >> 3


def _zstd_fse_table(norm, acclog: int):
    """Normalized counts -> tabel dekode (simbol[], nbBits[], baseline[]) berukuran 1 << acclog."""
    size = 1 << acclog
    high = size - 1
    nxt = [0] * len(norm)
    sym = [0] * size
    for s, c in enumerate(norm):
        if c == -1:
            sym[high] = s
            high -= 1
            nxt[s] = 1
        else:
            nxt[s] = c
    step = (size >> 1) + (size >> 3) + 3
    mask = size - 1
    pos = 0
    for s, c in enumerate(norm):
        for _ in range(c if c > 0 else 0):
            sym[pos] = s
            pos = (pos + step) & mask
            while pos > high:
                pos = (pos + step) & mask
    if pos != 0:
        raise ValueError("Zstd: tabel FSE tidak konsisten")
    nbv = [0] * size
    base = [0] * size
    for u in range(size):
        s = sym[u]
        ns = nxt[s]
        nxt[s] = ns + 1
        nbits = acclog - (ns.bit_length() - 1)
        nbv[u] = nbits
        base[u] = (ns << nbits) - size
    return sym, nbv, base


def _zstd_def_table(kind: str):
    t = _ZSTD_DEF_CACHE.get(kind)
    if t is None:
        norm, al = {"ll": (_ZSTD_LL_DEF, 6), "ml": (_ZSTD_ML_DEF, 6), "of": (_ZSTD_OF_DEF, 5)}[kind]
        t = _zstd_fse_table(list(norm), al) + (al,)
        _ZSTD_DEF_CACHE[kind] = t
    return t


class _ZRev:
    """Pembaca bitstream mundur Zstd (dari bit penanda di byte terakhir ke awal; bit pertama = MSB hasil)."""
    __slots__ = ("b", "i", "acc", "n", "left")

    def __init__(self, data):
        if not data or data[-1] == 0:
            raise ValueError("Zstd: bitstream tanpa bit penanda")
        rb = bytes(data[::-1])
        bl = rb[0].bit_length()
        self.b = rb
        self.i = 1
        self.n = bl - 1
        self.acc = rb[0] & ((1 << (bl - 1)) - 1)
        self.left = (bl - 1) + 8 * (len(rb) - 1)

    def read(self, k: int) -> int:
        if k == 0:
            return 0
        while self.n < k:
            if self.i < len(self.b):
                self.acc = (self.acc << 8) | self.b[self.i]
                self.i += 1
            else:
                self.acc <<= 8
            self.n += 8
        self.n -= k
        v = self.acc >> self.n
        self.acc &= (1 << self.n) - 1
        self.left -= k
        return v


def _zstd_huf_table(weights):
    """Bobot Huffman (tanpa simbol terakhir) -> (tabel_dekode, maxbits); entri = simbol << 4 | nbits."""
    if len(weights) > 255:
        raise ValueError("Zstd: terlalu banyak bobot Huffman")
    tot = 0
    for w in weights:
        if w > 11:
            raise ValueError("Zstd: bobot Huffman tidak sah")
        if w:
            tot += 1 << (w - 1)
    if tot == 0:
        raise ValueError("Zstd: tabel Huffman kosong")
    mb = tot.bit_length()                    # = highbit(tot) + 1
    if mb > 11:
        raise ValueError("Zstd: panjang kode Huffman melebihi 11 bit")
    rest = (1 << mb) - tot
    if rest <= 0 or rest & (rest - 1):
        raise ValueError("Zstd: bobot Huffman tidak melengkapi pohon")
    weights = list(weights) + [rest.bit_length()]
    table = [0] * (1 << mb)
    pos = 0
    for w in range(1, mb + 1):
        span = 1 << (w - 1)
        ent = mb + 1 - w
        for s, ws in enumerate(weights):
            if ws == w:
                e = (s << 4) | ent
                table[pos:pos + span] = [e] * span
                pos += span
    if pos != (1 << mb):
        raise ValueError("Zstd: tabel Huffman tidak penuh")
    return table, mb


def _zstd_huf_read(buf, pos: int, end: int):
    """Deskripsi pohon Huffman di buf[pos:end] -> (tabel, maxbits, byte_terpakai)."""
    if pos >= end:
        raise ValueError("Zstd: deskripsi Huffman terpotong")
    hb = buf[pos]
    pos += 1
    if hb >= 128:
        n = hb - 127
        nbytes = (n + 1) // 2
        if pos + nbytes > end:
            raise ValueError("Zstd: bobot Huffman langsung terpotong")
        w = []
        for i in range(n):
            byte = buf[pos + i // 2]
            w.append((byte >> 4) if i % 2 == 0 else (byte & 15))
        t, mb = _zstd_huf_table(w)
        return t, mb, 1 + nbytes
    if hb == 0 or pos + hb > end:
        raise ValueError("Zstd: bobot Huffman terkompresi terpotong")
    norm, al, used = _zstd_fse_header(buf[pos:pos + hb], 0, 255, 6)
    if used >= hb:
        raise ValueError("Zstd: bitstream bobot Huffman kosong")
    sym, nbv, base = _zstd_fse_table(norm, al)
    rd = _ZRev(buf[pos + used:pos + hb])
    s1 = rd.read(al)
    s2 = rd.read(al)
    w = []
    while True:
        w.append(sym[s1])
        s1 = base[s1] + rd.read(nbv[s1])
        if rd.left < 0:
            w.append(sym[s2])
            break
        w.append(sym[s2])
        s2 = base[s2] + rd.read(nbv[s2])
        if rd.left < 0:
            w.append(sym[s1])
            break
        if len(w) > 256:
            raise ValueError("Zstd: bobot Huffman melebihi 255")
    t, mb = _zstd_huf_table(w)
    return t, mb, 1 + hb


def _zstd_huf_stream(data, table, mb: int, count: int) -> bytes:
    """Dekode satu stream Huffman (bitstream mundur) menjadi tepat `count` byte."""
    rd = _ZRev(data)
    b, i, acc, n, left = rd.b, rd.i, rd.acc, rd.n, rd.left
    lb = len(b)
    out = bytearray(count)
    for j in range(count):
        while n < mb:
            if i < lb:
                acc = (acc << 8) | b[i]
                i += 1
            else:
                acc <<= 8
            n += 8
        e = table[acc >> (n - mb)]
        k = e & 15
        out[j] = e >> 4
        n -= k
        acc &= (1 << n) - 1
        left -= k
    if left != 0:
        raise ValueError("Zstd: stream Huffman tidak habis tepat")
    return bytes(out)


def _zstd_literals(d, pos: int, end: int, st: dict):
    """Seksi literal -> (bytes literal, pos berikutnya)."""
    if pos >= end:
        raise ValueError("Zstd: seksi literal terpotong")
    b0 = d[pos]
    typ, sf = b0 & 3, (b0 >> 2) & 3
    if typ < 2:
        if sf in (0, 2):
            size, hl = b0 >> 3, 1
        elif sf == 1:
            if pos + 2 > end:
                raise ValueError("Zstd: header literal terpotong")
            size, hl = (b0 >> 4) | (d[pos + 1] << 4), 2
        else:
            if pos + 3 > end:
                raise ValueError("Zstd: header literal terpotong")
            size, hl = (b0 >> 4) | (d[pos + 1] << 4) | (d[pos + 2] << 12), 3
        pos += hl
        if size > ZSTD_BLOCK_MAX:
            raise ValueError("Zstd: literal melebihi ukuran blok")
        if typ == 0:
            if pos + size > end:
                raise ValueError("Zstd: literal mentah terpotong")
            return bytes(d[pos:pos + size]), pos + size
        if pos + 1 > end:
            raise ValueError("Zstd: literal RLE terpotong")
        return bytes([d[pos]]) * size, pos + 1
    if sf == 0 or sf == 1:
        if pos + 3 > end:
            raise ValueError("Zstd: header literal terpotong")
        v = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16)
        regen, comp, hl = (v >> 4) & 0x3FF, (v >> 14) & 0x3FF, 3
    elif sf == 2:
        if pos + 4 > end:
            raise ValueError("Zstd: header literal terpotong")
        v = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16) | (d[pos + 3] << 24)
        regen, comp, hl = (v >> 4) & 0x3FFF, v >> 18, 4
    else:
        if pos + 5 > end:
            raise ValueError("Zstd: header literal terpotong")
        v = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16) | (d[pos + 3] << 24) | (d[pos + 4] << 32)
        regen, comp, hl = (v >> 4) & 0x3FFFF, v >> 22, 5
    pos += hl
    if regen > ZSTD_BLOCK_MAX or pos + comp > end:
        raise ValueError("Zstd: literal terkompresi di luar blok")
    stop = pos + comp
    if typ == 2:
        table, mb, used = _zstd_huf_read(d, pos, stop)
        st["huf"] = (table, mb)
        pos += used
    else:
        if not st.get("huf"):
            raise ValueError("Zstd: literal treeless tanpa tabel Huffman sebelumnya")
        table, mb = st["huf"]
    if sf == 0:
        return _zstd_huf_stream(d[pos:stop], table, mb, regen), stop
    if pos + 6 > stop:
        raise ValueError("Zstd: jump table 4 stream terpotong")
    s1, s2, s3 = struct.unpack_from("<3H", d, pos)
    pos += 6
    if pos + s1 + s2 + s3 >= stop:
        raise ValueError("Zstd: ukuran stream Huffman tidak sah")
    q = (regen + 3) // 4
    if regen < 3 * q and regen < 4:
        raise ValueError("Zstd: literal 4 stream terlalu pendek")
    r4 = regen - 3 * q
    if r4 < 0:
        raise ValueError("Zstd: ukuran literal 4 stream tidak sah")
    out = _zstd_huf_stream(d[pos:pos + s1], table, mb, q)
    pos += s1
    out += _zstd_huf_stream(d[pos:pos + s2], table, mb, q)
    pos += s2
    out += _zstd_huf_stream(d[pos:pos + s3], table, mb, q)
    pos += s3
    out += _zstd_huf_stream(d[pos:stop], table, mb, r4)
    return out, stop


def _zstd_seq_table(d, pos: int, end: int, mode: int, kind: str, st: dict, maxsym: int, maxlog: int):
    """Satu tabel FSE seksi sequences (mode 0 bawaan, 1 RLE, 2 FSE, 3 ulang) -> (tabel, pos berikutnya)."""
    if mode == 0:
        t = _zstd_def_table(kind)
        return t, pos
    if mode == 1:
        if pos >= end:
            raise ValueError("Zstd: tabel RLE terpotong")
        s = d[pos]
        if s > maxsym:
            raise ValueError("Zstd: simbol RLE di luar batas")
        return ([s], [0], [0], 0), pos + 1
    if mode == 2:
        norm, al, used = _zstd_fse_header(d[pos:end], 0, maxsym, maxlog)
        return _zstd_fse_table(norm, al) + (al,), pos + used
    t = st.get("t_" + kind)
    if t is None:
        raise ValueError("Zstd: tabel FSE 'ulang' tanpa tabel sebelumnya")
    return t, pos


def _zstd_block(d, pos: int, end: int, out: bytearray, st: dict, deadline: float) -> None:
    """Satu blok terkompresi d[pos:end] -> ditambahkan ke `out` (riwayat offset + tabel disimpan di st)."""
    lits, pos = _zstd_literals(d, pos, end, st)
    if pos >= end:
        raise ValueError("Zstd: seksi sequences hilang")
    b0 = d[pos]
    if b0 == 0:
        nseq, pos = 0, pos + 1
    elif b0 < 128:
        nseq, pos = b0, pos + 1
    elif b0 < 255:
        if pos + 2 > end:
            raise ValueError("Zstd: header sequences terpotong")
        nseq, pos = ((b0 - 128) << 8) + d[pos + 1], pos + 2
    else:
        if pos + 3 > end:
            raise ValueError("Zstd: header sequences terpotong")
        nseq, pos = d[pos + 1] + (d[pos + 2] << 8) + 0x7F00, pos + 3
    if nseq == 0:
        out += lits
        if pos != end:
            raise ValueError("Zstd: sisa byte setelah blok tanpa sequence")
        return
    if pos >= end:
        raise ValueError("Zstd: byte mode sequences hilang")
    mb = d[pos]
    pos += 1
    if mb & 3:
        raise ValueError("Zstd: bit cadangan mode sequences tidak nol")
    tll, pos = _zstd_seq_table(d, pos, end, mb >> 6, "ll", st, 35, 9)
    tof, pos = _zstd_seq_table(d, pos, end, (mb >> 4) & 3, "of", st, 31, 8)
    tml, pos = _zstd_seq_table(d, pos, end, (mb >> 2) & 3, "ml", st, 52, 9)
    st["t_ll"], st["t_of"], st["t_ml"] = tll, tof, tml
    rd = _ZRev(d[pos:end])
    lsym, lnb, lbase, lal = tll
    osym, onb, obase, oal = tof
    msym, mnb, mbase, mal = tml
    sl = rd.read(lal)
    so = rd.read(oal)
    sm = rd.read(mal)
    rep = st["rep"]
    r0, r1, r2 = rep
    li = 0
    nl = len(lits)
    read = rd.read
    for k in range(nseq):
        oc, mc, lc = osym[so], msym[sm], lsym[sl]
        if oc > 31:
            raise ValueError("Zstd: kode offset tidak sah")
        ov = (1 << oc) + read(oc)
        ml = _ZSTD_ML_BASE[mc] + read(_ZSTD_ML_BITS[mc])
        ll = _ZSTD_LL_BASE[lc] + read(_ZSTD_LL_BITS[lc])
        if ov > 3:
            off = ov - 3
            r0, r1, r2 = off, r0, r1
        elif ll == 0:
            if ov == 1:
                off = r1
                r0, r1 = r1, r0
            elif ov == 2:
                off = r2
                r0, r1, r2 = r2, r0, r1
            else:
                off = r0 - 1
                r0, r1, r2 = off, r0, r1
        else:
            if ov == 1:
                off = r0
            elif ov == 2:
                off = r1
                r0, r1 = r1, r0
            else:
                off = r2
                r0, r1, r2 = r2, r0, r1
        if off <= 0:
            raise ValueError("Zstd: offset nol")
        if ll:
            if li + ll > nl:
                raise ValueError("Zstd: sequence melebihi literal")
            out += lits[li:li + ll]
            li += ll
        n0 = len(out)
        if off > n0:
            raise ValueError("Zstd: offset melewati awal keluaran")
        dl = st.get("dict_len")
        if dl and off > n0 - dl and st.get("window") and off > st["window"]:     # v99.63: offset ke dictionary hanya sah bila <= ukuran window (RFC 8878 bagian 3.1.1.5)
            raise ValueError("Zstd: offset ke dictionary (%d) melebihi ukuran window (%d)" % (off, st["window"]))
        st0 = n0 - off
        if off >= ml:
            out += out[st0:st0 + ml]
        else:
            out += (bytes(out[st0:n0]) * (ml // off + 1))[:ml]
        if k + 1 < nseq:
            sl = lbase[sl] + read(lnb[sl])
            sm = mbase[sm] + read(mnb[sm])
            so = obase[so] + read(onb[so])
            if rd.left < 0:
                raise ValueError("Zstd: bitstream sequences habis terlalu cepat")
            if not (k & 1023) and time.time() > deadline:
                raise ValueError("Zstd: batas waktu dekompresi")
    if rd.left != 0:
        raise ValueError("Zstd: bitstream sequences tidak habis tepat")
    st["rep"] = [r0, r1, r2]
    out += lits[li:]


def _zstd_dict_parse(data) -> dict:
    """v99.51: dictionary Zstd (RFC 8878 bagian 5) -> {id, content, rep, huf, tll, tof, tml}. Berawalan magic 0xEC30A437: dictionary terformat (id, tabel Huffman +
    tiga tabel FSE offset / match / literal-length, tiga offset ulang, lalu konten). Selain itu: dictionary konten mentah (id 0, tabel bawaan, offset ulang 1 / 4 / 8)."""
    d = bytes(data)
    if len(d) < 8 or d[:4] != b"\x37\xa4\x30\xec":
        if not d:
            raise ValueError("Zstd: dictionary kosong")
        return {"id": 0, "content": d, "rep": [1, 4, 8], "huf": None, "tll": None, "tof": None, "tml": None}
    did = struct.unpack_from("<I", d, 4)[0]
    pos, n = 8, len(d)
    table, mb, used = _zstd_huf_read(d, pos, n)
    pos += used
    tabs = []
    for maxsym, maxlog in ((31, 8), (52, 9), (35, 9)):               # urutan di berkas: offset, match length, literal length
        if pos >= n:
            raise ValueError("Zstd: dictionary terpotong (tabel FSE)")
        norm, al, used = _zstd_fse_header(d, pos, maxsym, maxlog)
        tabs.append(_zstd_fse_table(norm, al) + (al,))
        pos += used
    if pos + 12 > n:
        raise ValueError("Zstd: dictionary terpotong (offset ulang)")
    rep = list(struct.unpack_from("<3I", d, pos))
    pos += 12
    content = d[pos:]
    if any(r == 0 or r > len(content) for r in rep):
        raise ValueError("Zstd: offset ulang dictionary tidak sah")
    return {"id": did, "content": content, "rep": rep, "huf": (table, mb), "tof": tabs[0], "tml": tabs[1], "tll": tabs[2]}


def _zstd_dicts(dictionary) -> dict:
    """v99.51: `dictionary` (bytes, daftar bytes, atau {id: bytes}) -> {id: hasil _zstd_dict_parse}."""
    if not dictionary:
        return {}
    items = dictionary.values() if isinstance(dictionary, dict) else ([dictionary] if isinstance(dictionary, (bytes, bytearray, memoryview)) else list(dictionary))
    out = {}
    for it in items:
        pd = it if isinstance(it, dict) else _zstd_dict_parse(it)
        out[pd["id"]] = pd
    return out


def _zstd_frame(d, pos: int, out: bytearray, max_out: int, deadline: float, verify: bool, info: dict | None = None, head: int | None = None, dicts: dict | None = None) -> int:
    """Satu frame Zstd di d[pos:] -> ditambahkan ke out; mengembalikan pos setelah frame (-1 bila berhenti dini karena `head` tercapai)."""
    n = len(d)
    if pos + 5 > n:
        raise ValueError("Zstd: frame terpotong")
    fd = d[pos + 4]
    pos += 5
    if fd & 8:
        raise ValueError("Zstd: bit cadangan header frame tidak nol")
    single, dflag, csum, fcsf = (fd >> 5) & 1, fd & 3, (fd >> 2) & 1, fd >> 6
    window = None
    if not single:
        if pos >= n:
            raise ValueError("Zstd: header frame terpotong")
        wd = d[pos]
        pos += 1
        base = 1 << (10 + (wd >> 3))
        window = base + (base >> 3) * (wd & 7)
    dsz = (0, 1, 2, 4)[dflag]
    did = int.from_bytes(d[pos:pos + dsz], "little") if dsz else 0
    pos += dsz
    fcsz = (1 if single else 0, 2, 4, 8)[fcsf]
    if pos + fcsz > n:
        raise ValueError("Zstd: header frame terpotong")
    fcs = int.from_bytes(d[pos:pos + fcsz], "little") if fcsz else None
    if fcs is not None and fcsf == 1:
        fcs += 256
    pos += fcsz
    if single:
        window = fcs
    zd = None
    if did or (dicts and 0 in dicts):                                # v99.51: dictionary dipakai bila id cocok (atau dictionary konten mentah untuk frame tanpa id)
        zd = (dicts or {}).get(did)
        if zd is None:
            raise ValueError("Zstd: frame memakai dictionary (id %d); berikan dengan dictionary= / --dict" % did)
    if fcs is not None and len(out) + fcs > max_out:
        raise ValueError("Zstd: ukuran isi frame (%d) melebihi batas keluaran" % fcs)
    if info is not None:
        info.update({"window": window, "content_size": fcs, "checksum": bool(csum), "dict_id": did})
    st = {"rep": [1, 4, 8], "huf": None}
    real_out, base_len = out, 0
    if zd is not None:                                               # v99.51: konten dictionary menjadi riwayat sebelum keluaran; offset boleh menunjuk ke sana
        st = {"rep": list(zd["rep"]), "huf": zd["huf"], "dict_len": len(zd["content"]), "window": window}
        if zd["tll"]:
            st["t_ll"], st["t_of"], st["t_ml"] = zd["tll"], zd["tof"], zd["tml"]
        out = bytearray(zd["content"])
        base_len = len(out)
        max_out = max_out - len(real_out) + base_len
        if head is not None:
            head = head - len(real_out) + base_len
    start = len(out)
    while True:
        if pos + 3 > n:
            raise ValueError("Zstd: header blok terpotong")
        bh = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16)
        pos += 3
        last, typ, size = bh & 1, (bh >> 1) & 3, bh >> 3
        if time.time() > deadline:
            raise ValueError("Zstd: batas waktu dekompresi")
        if typ == 3:
            raise ValueError("Zstd: jenis blok cadangan")
        if size > ZSTD_BLOCK_MAX:
            raise ValueError("Zstd: ukuran blok melebihi 128 KB")
        if typ == 1:
            if pos + 1 > n:
                raise ValueError("Zstd: blok RLE terpotong")
            if len(out) + size > max_out:
                raise ValueError("Zstd: keluaran melebihi batas")
            out += bytes([d[pos]]) * size
            pos += 1
        else:
            if pos + size > n:
                raise ValueError("Zstd: blok terpotong")
            if typ == 0:
                if len(out) + size > max_out:
                    raise ValueError("Zstd: keluaran melebihi batas")
                out += d[pos:pos + size]
            else:
                _zstd_block(d, pos, pos + size, out, st, deadline)
                if len(out) > max_out:
                    raise ValueError("Zstd: keluaran melebihi batas")
            pos += size
        if head is not None and len(out) >= head:
            if zd is not None:
                real_out += out[base_len:]
            return -1                                        # mode intip: cukup `head` byte pertama (tanpa checksum / cek ukuran)
        if last:
            break
    if csum:
        if pos + 4 > n:
            raise ValueError("Zstd: checksum terpotong")
        if verify and len(out) - start <= ZSTD_VERIFY_MAX:
            if (_xxh64(bytes(out[start:])) & 0xFFFFFFFF) != struct.unpack_from("<I", d, pos)[0]:
                raise ValueError("Zstd: checksum xxh64 tidak cocok")
        pos += 4
    if fcs is not None and len(out) - start != fcs:
        raise ValueError("Zstd: ukuran isi frame tidak cocok (%d, diharapkan %d)" % (len(out) - start, fcs))
    if zd is not None:
        real_out += out[base_len:]
    return pos


def _zstd_decompress(data, max_out: int | None = None, verify: bool = True, time_limit: float | None = None, info: list | None = None, head: int | None = None, dictionary=None) -> bytes:
    """Dekompresi satu atau lebih frame Zstd berurutan (frame skippable dilewati). Murni stdlib, keluaran + waktu dibatasi
    (MAX_OUT_FILE / ZSTD_TIME). ValueError bila rusak, terpotong, memakai dictionary yang tidak diberikan (v99.51: dictionary= bytes / daftar / {id: bytes}), atau melebihi batas.
    head=N: mode intip, berhenti setelah blok yang membuat keluaran >= N byte dan mengembalikan N byte pertama (tanpa cek checksum / ukuran)."""
    d = bytes(data)
    mo = MAX_OUT_FILE if max_out is None else min(int(max_out), MAX_OUT_FILE)
    deadline = time.time() + (ZSTD_TIME if time_limit is None else time_limit)
    out = bytearray()
    dicts = _zstd_dicts(dictionary)
    pos, n, frames = 0, len(d), 0
    while pos < n:
        if pos + 4 > n:
            if frames:
                break                                          # sampah di ekor setelah frame sah: abaikan
            raise ValueError("Zstd: data terlalu pendek")
        magic = struct.unpack_from("<I", d, pos)[0]
        if 0x184D2A50 <= magic <= 0x184D2A5F:
            if pos + 8 > n:
                raise ValueError("Zstd: frame skippable terpotong")
            sz = struct.unpack_from("<I", d, pos + 4)[0]
            if pos + 8 + sz > n:
                raise ValueError("Zstd: frame skippable terpotong")
            pos += 8 + sz
            continue
        if magic != 0xFD2FB528:
            if frames:
                break
            raise ValueError("Zstd: magic tidak cocok")
        fi: dict = {}
        if info is not None:
            info.append(fi)
        pos = _zstd_frame(d, pos, out, mo, deadline, verify, fi, head, dicts)
        frames += 1
        if pos < 0:
            return bytes(out[:head])
    if not frames:
        raise ValueError("Zstd: tidak ada frame")
    return bytes(out)


# --- Kontainer Zstandard (.zst / .tar.zst) + utilitas unzstd (v99.31) ---
def _zstd_arc(d, p):
    info: list = []
    zd = _ZSTD_DICT_CTX.get()                                           # v99.53: dictionary dari assets_text / assets_extract (dict_path=)
    peek = _zstd_decompress(d, head=1024, verify=False, info=info, dictionary=zd)     # intip: tidak perlu dekompres penuh hanya untuk mendaftar
    if _is_tar_raw(peek):
        data = _zstd_decompress(d, dictionary=zd)                       # .tar.zst: dekompres penuh (dibatasi MAX_OUT_FILE / ZSTD_TIME) lalu daftar TAR
        tf = tarfile.open(fileobj=io.BytesIO(data), mode="r:")
        ents = []
        for m in tf:
            if m.isfile():
                ents.append({"name": m.name, "size": m.size, "m": m})
                if len(ents) > MAX_ENTRIES:
                    tf.close()
                    raise ValueError("terlalu banyak entri TAR")

        def read_t(e):
            if e["size"] > MAX_OUT_FILE:
                raise ValueError("terlalu besar")
            return tf.extractfile(e["m"]).read(MAX_OUT_FILE + 1)
        return _Arc(ents, read_t, ["TAR di dalam Zstandard (dekoder murni Python)"], close=tf.close, kind="TAR.ZST")
    fcs = info[0].get("content_size") if info else None
    nm = p.stem if p.suffix.lower() == ".zst" else p.name + ".out"
    notes = ["dekoder Zstd murni Python"] + ([] if fcs is not None else ["ukuran isi tidak tercatat di header frame"])
    return _Arc([{"name": nm, "size": fcs or 0}], lambda e: _zstd_decompress(d, dictionary=zd), notes, kind="ZSTD")


_add_archive("ZSTD", lambda d, e: bytes(d[:4]) == b"\x28\xb5\x2f\xfd" and len(d) > 8, _zstd_arc, "Zstandard satu berkas (+ .tar.zst), dekoder murni Python", 35)


import contextlib
import contextvars

_ZSTD_DICT_CTX = contextvars.ContextVar("rea_zstd_dict", default=None)   # v99.53: dictionary Zstd untuk Asset Explorer / pembaca pak


@contextlib.contextmanager
def _zstd_dict_scope(dictionary):
    """v99.53: selama blok `with`, `_zstd_arc` dan pembaca Unreal pak memakai `dictionary` (bytes / daftar / {id: bytes}); None = tanpa."""
    tok = _ZSTD_DICT_CTX.set(dictionary)
    try:
        yield
    finally:
        _ZSTD_DICT_CTX.reset(tok)


def _zstd_load_dict(dict_path) -> bytes:
    """v99.52: baca berkas dictionary Zstd (terformat atau konten mentah), dibatasi UNPACK_MAX. ValueError / OSError bila gagal."""
    f, size = _open_regular(dict_path)
    with f:
        if size > UNPACK_MAX:
            raise ValueError("dictionary lebih besar dari batas %d MB" % (UNPACK_MAX >> 20))
        return f.read(size)


# --- AES (ECB) murni Python + kunci untuk pembaca Unreal pak terenkripsi (v99.54) ---
AES_TIME = 60.0            # batas waktu satu dekripsi / enkripsi AES murni Python (detik)
_AES_T = None


def _aes_init():
    """Tabel AES (S-box dibangkitkan, bukan ditempel) + tabel T enkripsi / dekripsi. Dibangun sekali, malas."""
    global _AES_T
    if _AES_T is not None:
        return _AES_T
    sb = [0] * 256
    p = q = 1
    while True:
        p = (p ^ ((p << 1) & 0xFF) ^ (0x1B if p & 0x80 else 0)) & 0xFF          # p *= 3
        q ^= (q << 1) & 0xFF
        q ^= (q << 2) & 0xFF
        q ^= (q << 4) & 0xFF
        if q & 0x80:
            q ^= 0x09                                                           # q /= 3
        x = q
        for r in (1, 2, 3, 4):
            x ^= ((q << r) | (q >> (8 - r))) & 0xFF
        sb[p] = x ^ 0x63
        if p == 1:
            break
    sb[0] = 0x63
    isb = [0] * 256
    for i, v in enumerate(sb):
        isb[v] = i

    def xt(a):
        return ((a << 1) ^ 0x11B) & 0xFF if a & 0x80 else (a << 1)

    def mul(a, b):
        r = 0
        while b:
            if b & 1:
                r ^= a
            a = xt(a)
            b >>= 1
        return r
    te0, td0 = [0] * 256, [0] * 256
    for i in range(256):
        s = sb[i]
        te0[i] = (mul(s, 2) << 24) | (s << 16) | (s << 8) | mul(s, 3)
        t = isb[i]
        td0[i] = (mul(t, 14) << 24) | (mul(t, 9) << 16) | (mul(t, 13) << 8) | mul(t, 11)

    def rot(tb, n):
        return [((w >> n) | (w << (32 - n))) & 0xFFFFFFFF for w in tb]
    _AES_T = (sb, isb, te0, rot(te0, 8), rot(te0, 16), rot(te0, 24), td0, rot(td0, 8), rot(td0, 16), rot(td0, 24))
    return _AES_T


def _aes_schedule(key: bytes, decrypt: bool):
    if len(key) not in (16, 24, 32):
        raise ValueError("kunci AES harus 16 / 24 / 32 byte")
    sb, isb, te0, te1, te2, te3, td0, td1, td2, td3 = _aes_init()
    nk = len(key) // 4
    nr = nk + 6
    w = list(struct.unpack(">%dI" % nk, key))
    rc = 1
    for i in range(nk, 4 * (nr + 1)):
        t = w[i - 1]
        if i % nk == 0:
            t = ((t << 8) | (t >> 24)) & 0xFFFFFFFF
            t = (sb[t >> 24] << 24) | (sb[(t >> 16) & 255] << 16) | (sb[(t >> 8) & 255] << 8) | sb[t & 255]
            t ^= rc << 24
            rc = ((rc << 1) ^ 0x11B) & 0xFF if rc & 0x80 else rc << 1
        elif nk > 6 and i % nk == 4:
            t = (sb[t >> 24] << 24) | (sb[(t >> 16) & 255] << 16) | (sb[(t >> 8) & 255] << 8) | sb[t & 255]
        w.append(w[i - nk] ^ t)
    if not decrypt:
        return nr, w
    dk = []
    for r in range(nr, -1, -1):                       # kunci putaran dibalik; InvMixColumns pada putaran tengah (inverse cipher setara)
        blk = w[4 * r:4 * r + 4]
        if 0 < r < nr:
            blk = [td0[sb[x >> 24]] ^ td1[sb[(x >> 16) & 255]] ^ td2[sb[(x >> 8) & 255]] ^ td3[sb[x & 255]] for x in blk]
        dk += blk
    return nr, dk


_AES_FAST = None


def _aes_fast(key: bytes, data: bytes, decrypt: bool):
    """Jalur cepat OPSIONAL lewat paket `cryptography` bila terpasang; None bila tidak ada / gagal (lalu dipakai jalur murni Python)."""
    global _AES_FAST
    if _AES_FAST is False:
        return None
    try:
        if _AES_FAST is None:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            _AES_FAST = (Cipher, algorithms, modes)
        Cipher, algorithms, modes = _AES_FAST
        c = Cipher(algorithms.AES(key), modes.ECB())
        o = c.decryptor() if decrypt else c.encryptor()
        return o.update(data) + o.finalize()
    except Exception:
        _AES_FAST = False if _AES_FAST is None else _AES_FAST
        return None


def _aes_ecb(key: bytes, data: bytes, decrypt: bool = True, fast: bool = True) -> bytes:
    """AES-ECB tanpa padding (panjang data kelipatan 16). Murni Python (tabel T); dibatasi waktu AES_TIME. Unreal pak memakai AES-256 ECB."""
    if len(data) % 16:
        raise ValueError("panjang data AES bukan kelipatan 16")
    if not data:
        return b""
    if fast:
        r = _aes_fast(bytes(key), bytes(data), decrypt)
        if r is not None and len(r) == len(data):
            return r
    sb, isb, te0, te1, te2, te3, td0, td1, td2, td3 = _aes_init()
    nr, rk = _aes_schedule(bytes(key), decrypt)
    out = []
    nb = len(data) // 16
    words = struct.unpack(">%dI" % (nb * 4), data)
    deadline = time.monotonic() + AES_TIME
    k0, k1, k2, k3 = rk[0], rk[1], rk[2], rk[3]
    last = 4 * nr
    for b in range(nb):
        if not b & 4095 and time.monotonic() > deadline:
            raise ValueError("AES murni Python melewati batas waktu (%d dtk); pasang paket `cryptography` untuk berkas besar" % AES_TIME)
        i = b * 4
        s0, s1, s2, s3 = words[i] ^ k0, words[i + 1] ^ k1, words[i + 2] ^ k2, words[i + 3] ^ k3
        j = 4
        if decrypt:
            while j < last:
                t0 = td0[s0 >> 24] ^ td1[(s3 >> 16) & 255] ^ td2[(s2 >> 8) & 255] ^ td3[s1 & 255] ^ rk[j]
                t1 = td0[s1 >> 24] ^ td1[(s0 >> 16) & 255] ^ td2[(s3 >> 8) & 255] ^ td3[s2 & 255] ^ rk[j + 1]
                t2 = td0[s2 >> 24] ^ td1[(s1 >> 16) & 255] ^ td2[(s0 >> 8) & 255] ^ td3[s3 & 255] ^ rk[j + 2]
                s3 = td0[s3 >> 24] ^ td1[(s2 >> 16) & 255] ^ td2[(s1 >> 8) & 255] ^ td3[s0 & 255] ^ rk[j + 3]
                s0, s1, s2 = t0, t1, t2
                j += 4
            o0 = ((isb[s0 >> 24] << 24) | (isb[(s3 >> 16) & 255] << 16) | (isb[(s2 >> 8) & 255] << 8) | isb[s1 & 255]) ^ rk[last]
            o1 = ((isb[s1 >> 24] << 24) | (isb[(s0 >> 16) & 255] << 16) | (isb[(s3 >> 8) & 255] << 8) | isb[s2 & 255]) ^ rk[last + 1]
            o2 = ((isb[s2 >> 24] << 24) | (isb[(s1 >> 16) & 255] << 16) | (isb[(s0 >> 8) & 255] << 8) | isb[s3 & 255]) ^ rk[last + 2]
            o3 = ((isb[s3 >> 24] << 24) | (isb[(s2 >> 16) & 255] << 16) | (isb[(s1 >> 8) & 255] << 8) | isb[s0 & 255]) ^ rk[last + 3]
        else:
            while j < last:
                t0 = te0[s0 >> 24] ^ te1[(s1 >> 16) & 255] ^ te2[(s2 >> 8) & 255] ^ te3[s3 & 255] ^ rk[j]
                t1 = te0[s1 >> 24] ^ te1[(s2 >> 16) & 255] ^ te2[(s3 >> 8) & 255] ^ te3[s0 & 255] ^ rk[j + 1]
                t2 = te0[s2 >> 24] ^ te1[(s3 >> 16) & 255] ^ te2[(s0 >> 8) & 255] ^ te3[s1 & 255] ^ rk[j + 2]
                s3 = te0[s3 >> 24] ^ te1[(s0 >> 16) & 255] ^ te2[(s1 >> 8) & 255] ^ te3[s2 & 255] ^ rk[j + 3]
                s0, s1, s2 = t0, t1, t2
                j += 4
            o0 = ((sb[s0 >> 24] << 24) | (sb[(s1 >> 16) & 255] << 16) | (sb[(s2 >> 8) & 255] << 8) | sb[s3 & 255]) ^ rk[last]
            o1 = ((sb[s1 >> 24] << 24) | (sb[(s2 >> 16) & 255] << 16) | (sb[(s3 >> 8) & 255] << 8) | sb[s0 & 255]) ^ rk[last + 1]
            o2 = ((sb[s2 >> 24] << 24) | (sb[(s3 >> 16) & 255] << 16) | (sb[(s0 >> 8) & 255] << 8) | sb[s1 & 255]) ^ rk[last + 2]
            o3 = ((sb[s3 >> 24] << 24) | (sb[(s0 >> 16) & 255] << 16) | (sb[(s1 >> 8) & 255] << 8) | sb[s2 & 255]) ^ rk[last + 3]
        out += (o0, o1, o2, o3)
    return struct.pack(">%dI" % len(out), *out)


_AES_KEY_CTX = contextvars.ContextVar("rea_aes_key", default=None)       # v99.54: kunci AES-256 (32 byte) untuk pembaca Unreal pak


@contextlib.contextmanager
def _aes_key_scope(key):
    """v99.54: selama blok `with`, pembaca Unreal pak (`_upak_raw`) mendekripsi indeks dan entri terenkripsi dengan `key` (32 byte); None = tanpa."""
    tok = _AES_KEY_CTX.set(key)
    try:
        yield
    finally:
        _AES_KEY_CTX.reset(tok)


_AES_KEY_HELP = "kunci AES tidak valid (harus 32 byte: hex 64 karakter, base64, 32 karakter ASCII, atau Crypto.json)"


def _aes_parse_key(src) -> bytes:
    """v99.54: kunci AES-256 dari bytes mentah (32), hex (64, boleh 0x), base64 (32 byte), teks ASCII 32 karakter, atau isi Crypto.json
    ({"EncryptionKey": {"Key": "<base64>"}} / {"Key": ...}). ValueError (tanpa memuat kunci di pesan) bila tidak valid."""
    import base64
    import binascii
    if isinstance(src, (bytes, bytearray, memoryview)):
        b = bytes(src)
        if len(b) == 32:
            return b
        try:
            src = b.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(_AES_KEY_HELP) from None
    s = str(src).strip().lstrip("\ufeff")
    if s[:1] in "{[":
        try:
            j = json.loads(s)
        except ValueError:
            raise ValueError(_AES_KEY_HELP) from None
        ek = j.get("EncryptionKey", j) if isinstance(j, dict) else None
        v = None
        if isinstance(ek, dict):
            v = ek.get("Key", ek.get("key"))
        elif isinstance(ek, str):
            v = ek
        if not isinstance(v, str):
            raise ValueError(_AES_KEY_HELP)
        s = v.strip()
    h = s[2:] if s[:2].lower() == "0x" else s
    if len(h) == 64:
        try:
            return binascii.unhexlify(h)
        except (binascii.Error, ValueError):
            pass
    try:
        r = base64.b64decode(s + "=" * (-len(s) % 4), validate=True)
        if len(r) == 32 and len(s) >= 43:
            return r
    except (binascii.Error, ValueError):
        pass
    if len(s) == 32 and s.isascii() and s.isprintable() and not all(c in "0123456789abcdefABCDEF" for c in s):
        return s.encode("ascii")
    raise ValueError(_AES_KEY_HELP)


def _aes_guid_norm(g):
    """v99.55: GUID enkripsi UE (32 digit hex; boleh bertanda hubung / kurung kurawal) -> 32 digit hex huruf besar (urutan A B C D, sama dengan footer pak);
    GUID nol -> None (kunci bawaan)."""
    h = re.sub(r"[{}\-\s]", "", str(g)).upper()
    if len(h) != 32 or any(c not in "0123456789ABCDEF" for c in h):
        raise ValueError("GUID enkripsi tidak valid (32 digit hex, boleh bertanda hubung)")
    return None if h == "0" * 32 else h


_AES_GUID_LINE = re.compile(r"^\{?([0-9A-Fa-f\-]{32,38})\}?\s*[:=]\s*(\S.*)$")


def _aes_parse_keys(src):
    """v99.55: daftar [(guid | None, kunci 32 byte)] dari satu sumber. Bentuk yang diterima: satu kunci seperti `_aes_parse_key` (guid None); `GUID:KUNCI` /
    `GUID=KUNCI`; beberapa baris (kosong, `#`, `;`, `//` dilewati); Crypto.json UnrealPak (`EncryptionKey` + `SecondaryEncryptionKeys`, tiap item `Key` + `Guid`);
    daftar JSON berisi objek serupa. ValueError (tanpa memuat kunci di pesan) bila tidak valid."""
    if isinstance(src, (bytes, bytearray, memoryview)):
        b = bytes(src)
        if len(b) == 32:
            return [(None, b)]
        try:
            src = b.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(_AES_KEY_HELP) from None
    s_ = str(src).strip().lstrip("\ufeff")
    out = []

    def add(g, k):
        gk = (_aes_guid_norm(g) if g not in (None, "") else None, _aes_parse_key(k))
        if gk not in out:
            out.append(gk)
    if s_[:1] in "{[":
        try:
            j = json.loads(s_)
        except ValueError:
            raise ValueError(_AES_KEY_HELP) from None
        objs = []
        if isinstance(j, dict):
            if "EncryptionKey" in j or "SecondaryEncryptionKeys" in j:
                ek = j.get("EncryptionKey")
                if isinstance(ek, (dict, str)):
                    objs.append(ek)
                sec = j.get("SecondaryEncryptionKeys")
                if isinstance(sec, list):
                    objs += sec
            else:
                objs.append(j)
        elif isinstance(j, list):
            objs = j
        for o in objs:
            if isinstance(o, str):
                add(None, o)
            elif isinstance(o, dict) and isinstance(o.get("Key", o.get("key")), str):
                add(o.get("Guid", o.get("guid")), o.get("Key", o.get("key")))
            else:
                raise ValueError(_AES_KEY_HELP)
    else:
        lines = [l.strip() for l in s_.splitlines()]
        lines = [l for l in lines if l and not l.startswith(("#", ";", "//"))]
        if len(lines) > 64:
            raise ValueError("terlalu banyak kunci AES (maks 64)")
        for l in lines:
            m = _AES_GUID_LINE.match(l)
            if m:
                add(m.group(1), m.group(2).strip())
            else:
                add(None, l)
    if not out:
        raise ValueError(_AES_KEY_HELP)
    return out


def _aes_resolve(aes_key=None, aes_file=None):
    """v99.54 / v99.55: daftar [(guid | None, kunci)] dari `aes_key` (teks / bytes / daftar) dan `aes_file` (berkas atau daftar berkas, tiap berkas dibatasi 1 MB).
    None bila tidak ada sumber. Banyak kunci (maks 64) dipilih per pak lewat GUID enkripsi di footer (`_aes_candidates`)."""
    out = []

    def one(v):
        for gk in _aes_parse_keys(v):
            if gk not in out:
                out.append(gk)
    for f_ in (aes_file if isinstance(aes_file, (list, tuple)) else [aes_file]):
        if f_:
            f, size = _open_regular(f_)
            with f:
                if size > (1 << 20):
                    raise ValueError("berkas kunci AES terlalu besar")
                one(f.read(size))
    for k_ in (aes_key if isinstance(aes_key, (list, tuple)) else [aes_key]):
        if k_ is not None and k_ != "":
            one(k_)
    if len(out) > 64:
        raise ValueError("terlalu banyak kunci AES (maks 64)")
    return out or None


def _aes_keyset(v):
    """v99.55: isi `_AES_KEY_CTX` -> daftar [(guid | None, kunci)] atau None. Menerima bytes 32 (v99.54), daftar tuple, atau daftar bytes."""
    if v is None:
        return None
    if isinstance(v, (bytes, bytearray, memoryview)):
        return [(None, bytes(v))]
    r = [(x if isinstance(x, tuple) else (None, bytes(x))) for x in v]
    return r or None


def _aes_candidates(keys, guid):
    """v99.55: urutan kunci yang dicoba untuk pak ber-GUID `guid` (None = nol / pak lama): GUID cocok, lalu kunci bawaan (tanpa GUID), lalu sisanya.
    Mengembalikan [(label, kunci)] tanpa duplikat."""
    out, seen = [], set()
    for lab, sel in (("GUID cocok", lambda g: guid is not None and g == guid), ("kunci bawaan (tanpa GUID)", lambda g: g is None),
                     ("GUID berbeda", lambda g: True)):
        for g, k in keys:
            if k not in seen and sel(g):
                seen.add(k)
                out.append((lab, k))
    return out


_AES_MAGICS = (b"\xc1\x83\x2a\x9e", b"\x9e\x2a\x83\xc1", b"RIFF", b"OggS", b"\x89PNG", b"DDS ", b"BM", b"\xff\xd8\xff", b"PK\x03\x04", b"\x1f\x8b", b"GIF8", b"fLaC", b"ID3", b"\x00\x01\x00\x00", b"OTTO", b"{", b"[", b"<", b"#", b"\xef\xbb\xbf")


def _aes_plain_ok(b: bytes) -> bool:
    """v99.56: apakah hasil dekripsi entri tak terkompresi tampak benar (bukan sampah)? Magic format umum (uasset / png / dds / riff / ogg / zip ...),
    teks (>= 85% byte cetak), atau biner terstruktur (>= 10% byte nol). Entropi sengaja tidak dipakai (sampah ECB dari plaintext berulang ikut berentropi rendah). Data pendek / biner acak -> False (tak terbukti, bukan terbukti salah)."""
    if len(b) < 16:
        return False
    h = b[:8]
    if any(h.startswith(m) for m in _AES_MAGICS[:12]):
        return True
    w = b[:4096]
    pr = sum(1 for c in w if 32 <= c < 127 or c in (9, 10, 13))
    if pr >= 0.85 * len(w):
        return True
    return len(w) >= 64 and w.count(0) >= 0.10 * len(w)           # data biner terstruktur (uasset, tabel, float) penuh byte nol; sampah ECB hampir tak punya


def _aes_pick_data(keys, guid):
    """v99.55: kunci untuk entri terenkripsi saat indeks pak TIDAK terenkripsi (tidak ada pemeriksaan isi): GUID cocok -> kunci bawaan -> satu-satunya kunci.
    ValueError bila ada beberapa kunci dan tak satu pun cocok."""
    c = _aes_candidates(keys, guid)
    if c and c[0][0] != "GUID berbeda":
        return c[0][1]
    if len(c) == 1:
        return c[0][1]
    raise ValueError("ada %d kunci AES tetapi tak satu pun cocok dengan GUID pak%s; berikan GUID:KUNCI" % (len(c), " " + guid if guid else " (GUID nol)"))


def unzstd(path, outpath=None, max_out=None, force: bool = False, dict_path=None) -> dict:
    """Dekompres berkas Zstandard (satu atau beberapa frame, frame skippable dilewati) dengan dekoder murni Python (v99.31). dict_path: berkas dictionary (v99.51; terformat atau konten mentah).
    Keluaran dibatasi MAX_OUT_FILE (atau max_out) dan waktu ZSTD_TIME; checksum xxh64 diverifikasi bila ada dan keluaran <= ZSTD_VERIFY_MAX.
    outpath=None: hanya ringkasan (tanpa menulis). Tidak menimpa berkas yang sudah ada kecuali force=True. Tidak pernah melempar."""
    try:
        f, size = _open_regular(path)
        with f:
            if size > UNPACK_MAX:
                return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
            raw = f.read(size)
        info: list = []
        zdict = None
        if dict_path:
            fd_, dsz_ = _open_regular(dict_path)
            with fd_:
                if dsz_ > UNPACK_MAX:
                    return {"ok": False, "error": "dictionary lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
                zdict = fd_.read(dsz_)
        t0 = time.time()
        data = _zstd_decompress(raw, max_out=max_out, info=info, dictionary=zdict)
        res = {"ok": True, "frames": len(info), "compressed": len(raw), "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
               "checksum_in_frames": bool(info) and all(i.get("checksum") for i in info), "seconds": round(time.time() - t0, 2)}
        if outpath:
            op = Path(outpath).expanduser()
            if op.exists() and not force:
                res.update({"ok": False, "error": "tujuan sudah ada (gunakan --force): %s" % op})
                return res
            op.parent.mkdir(parents=True, exist_ok=True)
            op.write_bytes(data)
            res["out"] = str(op)
        return res
    except (ValueError, OSError) as e:
        return {"ok": False, "error": _as_clean(e, 200)}


def unzstd_text(path, outpath=None, force: bool = False) -> str:
    r = unzstd(path, outpath, force=force)
    if not r.get("ok") and "size" not in r:
        return "unzstd gagal: %s" % r.get("error", "?")
    L = ["Zstandard: %d frame, %s -> %s (%.2f dtk)" % (r["frames"], _as_human(r["compressed"]), _as_human(r["size"]), r["seconds"]),
         "sha256: %s" % r["sha256"], "checksum xxh64 di frame: %s" % ("ada (diverifikasi)" if r["checksum_in_frames"] and r["size"] <= ZSTD_VERIFY_MAX else ("ada (tidak diverifikasi: keluaran besar)" if r["checksum_in_frames"] else "tidak ada"))]
    if r.get("out"):
        L.append("ditulis: %s" % r["out"])
    if not r.get("ok"):
        L.append("GAGAL: %s" % r.get("error", "?"))
    return "\n".join(L)


_CARVE_NEED_LEN = frozenset({"wasm", "sqlite-wal", "pem-cert", "pem-key", "der-cert", "zstd"})   # tanpa panjang yang valid = positif palsu, dibuang

_SIGS = [
    ("png", b"\x89PNG\r\n\x1a\n", ".png", _len_png),
    ("jpeg", b"\xff\xd8\xff", ".jpg", lambda d, o: _jpeg_len(d, o)),
    ("gif", b"GIF89a", ".gif", _len_gif), ("gif", b"GIF87a", ".gif", _len_gif),
    ("riff", b"RIFF", None, _len_riff),
    ("ogg", b"OggS\x00\x02", ".ogg", _len_ogg),
    ("glb", b"glTF\x02\x00\x00\x00", ".glb", _len_glb),
    ("midi", b"MThd\x00\x00\x00\x06", ".mid", _len_midi),
    ("sqlite", b"SQLite format 3\x00", ".sqlite", _len_sqlite),
    ("zip", b"PK\x03\x04", ".zip", _len_zip),
    ("dds", b"DDS \x7c\x00\x00\x00", ".dds", None),
    ("fbx", b"Kaydara FBX Binary  \x00\x1a\x00", ".fbx", None),
    ("flac", b"fLaC\x00\x00\x00\x22", ".flac", None),
    ("quake-pak", b"PACK", ".pak", None),
    ("unityfs", b"UnityFS\x00", ".unity3d", None),
    ("7z", b"7z\xbc\xaf\x27\x1c", ".7z", None),
    ("gzip", b"\x1f\x8b\x08", ".gz", None),
    # v99.10 [Tier C]: panjang selalu bisa dipastikan (struktur divalidasi); kandidat tanpa panjang valid dibuang (_CARVE_NEED_LEN)
    ("wasm", b"\x00asm\x01\x00\x00\x00", ".wasm", _len_wasm),
    ("sqlite-wal", b"\x37\x7f\x06\x82\x00\x2d\xe2\x18", ".sqlite-wal", _len_wal), ("sqlite-wal", b"\x37\x7f\x06\x83\x00\x2d\xe2\x18", ".sqlite-wal", _len_wal),
    ("pem-cert", b"-----BEGIN CERTIFICATE-----", ".pem", _len_pem), ("pem-cert", b"-----BEGIN X509 CERTIFICATE-----", ".pem", _len_pem),
    ("pem-key", b"-----BEGIN PRIVATE KEY-----", ".key", _len_pem), ("pem-key", b"-----BEGIN RSA PRIVATE KEY-----", ".key", _len_pem),
    ("pem-key", b"-----BEGIN EC PRIVATE KEY-----", ".key", _len_pem), ("pem-key", b"-----BEGIN OPENSSH PRIVATE KEY-----", ".key", _len_pem),
    ("pem-key", b"-----BEGIN ENCRYPTED PRIVATE KEY-----", ".key", _len_pem),
    ("der-cert", _RX(rb"\x30\x82[\x01-\x1f][\x00-\xff]\x30\x82[\x01-\x1f][\x00-\xff]\xa0\x03\x02\x01\x02\x02"), ".der", _len_der_cert),
    ("zstd", b"\x28\xb5\x2f\xfd", ".zst", _len_zstd),
]
_SIG_RE = re.compile(b"|".join(b"(%s)" % (s[1] if isinstance(s[1], _RX) else re.escape(s[1])) for s in _SIGS), re.S)
_SIG_RX = {i: re.compile(s[1], re.S) for i, s in enumerate(_SIGS) if isinstance(s[1], _RX)}


def _sig_next(d, pos: int, lim: int, cache: list):
    """Tanda tangan terdekat di [pos, lim): (offset, indeks _SIGS) atau None. Setara dengan _SIG_RE.search (yang paling awal menang;
    seri dimenangkan urutan tabel), tetapi memakai find() per tanda tangan dengan cache posisi berikutnya, jauh lebih cepat pada berkas besar."""
    best, bi = lim + 1, -1
    for i, s in enumerate(_SIGS):
        o = cache[i]
        if o < pos:
            if i in _SIG_RX:
                m = _SIG_RX[i].search(d, pos, lim)
                o = m.start() if m else lim + 1
            else:
                o = d.find(s[1], pos, lim)
                if o < 0:
                    o = lim + 1
            cache[i] = o
        if o < best:
            best, bi = o, i
    return (best, bi) if bi >= 0 else None


_RIFF_EXT = {b"WAVE": ".wav", b"WEBP": ".webp", b"AVI ": ".avi"}


def _as_carve(path, outdir=None, max_items: int = 200, min_size: int = 64) -> dict:
    """Cari tanda tangan berkas di dalam berkas apa pun. Yang panjangnya bisa dipastikan (PNG, JPEG, GIF, OGG, RIFF, GLB, MIDI, SQLite, ZIP)
    dipotong ke outdir/carved/ (v99.10: + WebAssembly, SQLite WAL, sertifikat PEM / DER, kunci PEM, Zstandard); yang lain (DDS, FBX, FLAC, PAK ...) hanya dilaporkan offsetnya."""
    try:
        out = _Out(outdir) if outdir else None
        hits = []
        with _map(path) as d:
            n = len(d)
            lim = min(n, MAX_CARVE_SCAN)
            pos = 0
            cache = [-1] * len(_SIGS)
            while len(hits) < max_items:
                nx = _sig_next(d, pos, lim, cache)
                if not nx:
                    break
                o = nx[0]
                sig = _SIGS[nx[1]]
                nm, ext, fn = sig[0], sig[2], sig[3]
                ln = None
                try:
                    ln = fn(d, o) if fn else None
                except (struct.error, IndexError, ValueError):
                    ln = None
                if nm == "riff" and ln:
                    ext = _RIFF_EXT.get(bytes(d[o + 8:o + 12]), ".riff")
                    nm = "riff/" + ext[1:]
                elif nm == "riff":
                    pos = o + 4
                    continue
                if (nm == "gzip" or nm in _CARVE_NEED_LEN) and ln is None:
                    pos = o + 3   # terlalu banyak positif palsu untuk dilaporkan tanpa panjang
                    continue
                if ln is not None and ln < min_size:
                    pos = o + 4
                    continue
                if nm == "quake-pak" and not (o + 12 <= n and _u32(d, o + 8) % 64 == 0 and 0 < _u32(d, o + 8) < n):
                    pos = o + 4
                    continue
                h = {"offset": o, "type": nm, "length": ln, "whole_file": bool(o == 0 and ln == n)}
                if out and ln and not h["whole_file"]:
                    t = out.write("carved/0x%08X%s" % (o, ext), bytes(d[o:o + ln]), "carved", nm)
                    h["file"] = out.files[-1]["path"] if t else None
                hits.append(h)
                pos = o + (ln if ln else (4 if isinstance(sig[1], _RX) else len(sig[1])))
        res = {"status": "success", "path": str(path), "hits": hits, "count": len(hits)}
        if out:
            res.update(outdir=str(out.root), skipped=out.skipped, errors=out.errors)
        return res
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def _carve_text(res: dict) -> str:
    if res.get("status") != "success":
        return "CARVE gagal: %s" % res.get("message")
    if not res["hits"]:
        return "CARVE: tidak ada tanda tangan berkas dikenal di dalam berkas ini."
    L = ["CARVE: %d tanda tangan ditemukan" % res["count"]]
    for h in res["hits"][:60]:
        L.append("  0x%08X  %-14s %s%s" % (h["offset"], h["type"], _as_human(h["length"]) if h["length"] else "(panjang tidak bisa dipastikan)",
                                          "  -> " + h["file"] if h.get("file") else ""))
    if res["count"] > 60:
        L.append("  ... +%d lagi" % (res["count"] - 60))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Cadangan: berkas tak dikenal (teks / biner)
# ---------------------------------------------------------------------------

def _fallback_inspect(d, p):
    samp = bytes(d[:1024 * 1024])
    ent = _as_entropy(samp)
    printable = sum(1 for b in samp[:65536] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(samp[:65536]))
    L = []
    if printable > 0.95 and samp:
        txt = samp[:200000].decode("utf-8", "replace")
        first = _as_clean(txt.strip().split("\n", 1)[0], 100)
        kind = "teks"
        s = txt.lstrip()[:1]
        if s in "{[":
            try:
                json.loads(bytes(d[:8 * 1024 * 1024]).decode("utf-8-sig"))
                kind = "JSON"
            except Exception:
                pass
        elif s == "<":
            kind = "XML / HTML"
        L.append("%s, %d baris, baris pertama: %s" % (kind, bytes(d[:8 * 1024 * 1024]).count(b"\n") + 1, first))
    else:
        L.append("biner tanpa format dikenal: entropi %.2f/8%s" % (ent, " (kemungkinan terkompresi / terenkripsi)" if ent > 7.5 else ""))
        res = _as_carve(p, None, max_items=12)
        if res.get("hits"):
            L.append("berkas tertanam terdeteksi:")
            L += ["  0x%08X %s%s" % (h["offset"], h["type"], " (%s)" % _as_human(h["length"]) if h["length"] else "") for h in res["hits"][:12]]
            L.append("gunakan carve / --carve untuk memotongnya keluar.")
        else:
            L.append("tidak ada tanda tangan berkas dikenal. Jika ini format game, tulis plugin atau kirim contoh untuk dibuatkan parser.")
    return {"lines": L, "extract": "tidak ada (format tidak dikenal); coba carve"}


register("unknown", "unknown", lambda d, e: True, _fallback_inspect, None, 999, "cadangan")


