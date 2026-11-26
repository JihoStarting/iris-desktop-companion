# rea_triage bagian 39/47: assets_gambar (baris asli 17857-18367). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# Gambar
# ---------------------------------------------------------------------------

def _png_encode(w: int, h: int, rgba) -> bytes:
    """RGBA 8-bit -> PNG. rgba: bytes / bytearray panjang w*h*4."""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")


_PNG_CT = {0: "grayscale", 2: "RGB", 3: "palet", 4: "grayscale+alfa", 6: "RGBA"}


def _png_walk(d):
    pos, chunks = 8, []
    while pos + 12 <= len(d) and len(chunks) < 100_000:
        ln = _b32(d, pos)
        typ = bytes(d[pos + 4:pos + 8])
        chunks.append((typ, pos + 8, ln))
        pos += 12 + ln
        if typ == b"IEND":
            break
    return chunks, pos


def _png_inspect(d, p):
    w, h, bd, ct, _, _, il = struct.unpack_from(">IIBBBBB", d, 16)
    chunks, end = _png_walk(d)
    names = collections.Counter(c[0] for c in chunks)
    L = ["PNG %dx%d, %d-bit %s%s" % (w, h, bd, _PNG_CT.get(ct, "?"), ", interlaced" if il else "")]
    if names[b"acTL"]:
        o = next(c[1] for c in chunks if c[0] == b"acTL")
        L.append("APNG animasi: %d frame, ulang %s" % (_b32(d, o), _b32(d, o + 4) or "tanpa batas"))
    txt = []
    for t, o, ln in chunks:
        if t == b"tEXt" and len(txt) < 6:
            k = bytes(d[o:o + min(ln, 80)]).split(b"\x00")[0]
            txt.append(_as_clean(k, 30))
    if txt:
        L.append("teks metadata: " + ", ".join(txt))
    if names[b"eXIf"]:
        L.append("memuat EXIF")
    if end < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah IEND (kemungkinan data tersembunyi / arsip tertanam)" % (len(d) - end))
    return {"lines": L}


register("PNG", "image", lambda d, e: d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 33, _png_inspect, None, 15, "PNG / APNG")


def _jpeg_inspect(d, p):
    pos, L, info = 2, [], {}
    while pos + 4 <= len(d) and d[pos] == 0xFF:
        m = d[pos + 1]
        if m == 0xFF:
            pos += 1; continue
        if m == 0xD9 or m == 0xDA:
            break
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        ln = struct.unpack_from(">H", d, pos + 2)[0]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            prec, h, w, nc = struct.unpack_from(">BHHB", d, pos + 4)
            info.update(w=w, h=h, comps=nc, prog=m in (0xC2, 0xC6, 0xCA, 0xCE), prec=prec)
        elif m == 0xE1 and bytes(d[pos + 4:pos + 10]) == b"Exif\x00\x00":
            info["exif"] = True
        elif m == 0xE0 and bytes(d[pos + 4:pos + 9]) == b"JFIF\x00":
            info["jfif"] = True
        elif m == 0xFE:
            info["comment"] = _as_clean(d[pos + 4:pos + 2 + ln], 80)
        pos += 2 + ln
    L.append("JPEG %sx%s, %s komponen, %s%s%s" % (info.get("w", "?"), info.get("h", "?"), info.get("comps", "?"), "progresif" if info.get("prog") else "baseline",
                                              ", EXIF" if info.get("exif") else "", ", JFIF" if info.get("jfif") else ""))
    if info.get("comment"):
        L.append("komentar: " + info["comment"])
    ln = _jpeg_len(d, 0)
    if ln and ln < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah EOI" % (len(d) - ln))
    return {"lines": L}


def _jpeg_len(d, start):
    pos, n = start + 2, len(d)
    while pos + 4 <= n:
        if d[pos] != 0xFF:
            return None
        m = d[pos + 1]
        if m == 0xD9:
            return pos + 2 - start
        if m == 0xFF:
            pos += 1; continue
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        pos += 2 + struct.unpack_from(">H", d, pos + 2)[0]
        if m == 0xDA:
            p = pos
            while True:
                i = d.find(b"\xff", p)
                if i < 0 or i + 1 >= n:
                    return None
                nb = d[i + 1]
                if nb == 0 or 0xD0 <= nb <= 0xD7:
                    p = i + 2; continue
                pos = i
                break
    return None


register("JPEG", "image", lambda d, e: d[:3] == b"\xff\xd8\xff", _jpeg_inspect, None, 15, "JPEG")


def _gif_walk(d, start=0):
    if bytes(d[start:start + 4]) != b"GIF8" or bytes(d[start + 5:start + 6]) != b"a":
        raise ValueError("bukan GIF")
    w, h, fl = struct.unpack_from("<HHB", d, start + 6)
    pos = start + 13
    if fl & 0x80:
        pos += 3 * (2 << (fl & 7))
    frames = delay = 0
    loops = None
    n = len(d)

    def skip_sub(p):
        while p < n:
            ln = d[p]
            p += 1
            if ln == 0:
                return p
            p += ln
        raise ValueError("GIF terpotong")
    while pos < n:
        b = d[pos]
        if b == 0x3B:
            return {"w": w, "h": h, "frames": frames, "delay_cs": delay, "loops": loops, "end": pos + 1 - start}
        if b == 0x21:
            lab = d[pos + 1]
            if lab == 0xF9 and pos + 6 <= n:
                delay += _u16(d, pos + 4)
            if lab == 0xFF and bytes(d[pos + 3:pos + 14]) == b"NETSCAPE2.0" and pos + 18 <= n:
                loops = _u16(d, pos + 16)
            pos = skip_sub(pos + 2)
        elif b == 0x2C:
            fl2 = d[pos + 9]
            pos += 10
            if fl2 & 0x80:
                pos += 3 * (2 << (fl2 & 7))
            pos = skip_sub(pos + 1)
            frames += 1
        else:
            raise ValueError("blok GIF tidak dikenal")
    raise ValueError("GIF tanpa trailer")


def _gif_inspect(d, p):
    g = _gif_walk(d)
    L = ["GIF %dx%d, %d frame%s" % (g["w"], g["h"], g["frames"], ", durasi %.2f dtk" % (g["delay_cs"] / 100) if g["frames"] > 1 else "")]
    if g["loops"] is not None:
        L.append("ulang: %s" % (g["loops"] or "tanpa batas"))
    if g["end"] < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah trailer GIF" % (len(d) - g["end"]))
    return {"lines": L}


register("GIF", "image", lambda d, e: d[:4] == b"GIF8" and d[5:6] == b"a", _gif_inspect, None, 15, "GIF (animasi)")


def _webp_inspect(d, p):
    pos, L, flags = 12, [], 0
    w = h = frames = 0
    kind = "?"
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        b = pos + 8
        if t == b"VP8X":
            flags = d[b]; w = int.from_bytes(d[b + 4:b + 7], "little") + 1; h = int.from_bytes(d[b + 7:b + 10], "little") + 1; kind = "VP8X"
        elif t == b"VP8 " and not w:
            w, h = _u16(d, b + 6) & 0x3FFF, _u16(d, b + 8) & 0x3FFF; kind = "lossy"
        elif t == b"VP8L" and not w:
            v = _u32(d, b + 1); w, h = (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1; kind = "lossless"
        elif t == b"ANMF":
            frames += 1
        pos = b + ln + (ln & 1)
    L.append("WebP %dx%d (%s)%s%s" % (w, h, kind, ", animasi %d frame" % frames if flags & 2 else "", ", alfa" if flags & 0x10 else ""))
    return {"lines": L}


register("WebP", "image", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WEBP", _webp_inspect, None, 14, "WebP")


def _ico_inspect(d, p):
    n = _u16(d, 4)
    L = ["%s: %d gambar" % ("ICO" if _u16(d, 2) == 1 else "CUR", n)]
    for i in range(min(n, 12)):
        w, h = d[6 + 16 * i] or 256, d[7 + 16 * i] or 256
        L.append("  %dx%d, %d-bit, %s" % (w, h, _u16(d, 12 + 16 * i), _as_human(_u32(d, 14 + 16 * i))))
    return {"lines": L}


register("ICO", "image", lambda d, e: len(d) >= 22 and d[:2] == b"\x00\x00" and d[2:4] in (b"\x01\x00", b"\x02\x00") and 0 < _u16(d, 4) < 256 and e in (".ico", ".cur"),
         _ico_inspect, None, 40, "ikon Windows")


# --- BMP ---

def _bmp_decode(d):
    off = _u32(d, 10)
    hs = _u32(d, 14)
    if hs < 40:
        raise ValueError("BMP header lama tidak didukung")
    w, h, planes, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
    top = h < 0
    h = abs(h)
    if w <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran BMP tidak wajar")
    if comp not in (0, 3) or bpp not in (8, 24, 32):
        raise ValueError("BMP %d-bit / kompresi %d belum didukung" % (bpp, comp))
    out = bytearray(w * h * 4)
    pal = None
    if bpp == 8:
        nc = _u32(d, 46) or 256
        pal = [bytes(d[14 + hs + 4 * i:14 + hs + 4 * i + 3]) for i in range(nc)]
    rb = ((w * bpp + 31) // 32) * 4
    for y in range(h):
        row = bytes(d[off + y * rb:off + y * rb + w * bpp // 8])
        dy = y if top else h - 1 - y
        o = dy * w * 4
        for x in range(w):
            if bpp == 24:
                b, g, r = row[3 * x:3 * x + 3]; a = 255
            elif bpp == 32:
                b, g, r, a = row[4 * x:4 * x + 4]
            else:
                b, g, r = pal[row[x]] if row[x] < len(pal) else (0, 0, 0); a = 255
            out[o:o + 4] = bytes((r, g, b, a)); o += 4
    return w, h, out


def _bmp_inspect(d, p):
    hs = _u32(d, 14)
    if hs >= 40:
        w, h, _, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
        return {"lines": ["BMP %dx%d, %d-bit, kompresi %d" % (w, abs(h), bpp, comp)], "extract": "-> .png (8 / 24 / 32-bit tak terkompresi)"}
    return {"lines": ["BMP header lama (OS/2)"]}


def _bmp_extract(d, p, out, opts):
    w, h, px = _bmp_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("BMP", "image", lambda d, e: d[:2] == b"BM" and len(d) > 30 and _u32(d, 10) < len(d) and _u32(d, 14) in (12, 40, 52, 56, 64, 108, 124),
         _bmp_inspect, _bmp_extract, 16, "bitmap Windows")


# --- TGA (tanpa magic: dideteksi dari ekstensi + header masuk akal) ---

def _tga_ok(d, e):
    if e != ".tga" or len(d) < 18:
        return False
    cm, it, bpp = d[1], d[2], d[16]
    return cm in (0, 1) and it in (1, 2, 3, 9, 10, 11) and bpp in (8, 15, 16, 24, 32)


def _tga_decode(d):
    idlen, cmt, it = d[0], d[1], d[2]
    cmstart, cmlen, cmbits = struct.unpack_from("<HHB", d, 3)
    w, h, bpp, desc = struct.unpack_from("<HHBB", d, 12)[0:2] + struct.unpack_from("<BB", d, 16)
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran TGA tidak wajar")
    pos = 18 + idlen
    pal = None
    if cmt:
        step = (cmbits + 7) // 8
        pal = [bytes(d[pos + i * step:pos + (i + 1) * step]) for i in range(cmlen)]
        pos += cmlen * step
    bytespp = (bpp + 7) // 8
    rle = it >= 9
    total = w * h * bytespp
    if rle:
        buf = bytearray()
        while len(buf) < total and pos < len(d):
            hd = d[pos]; pos += 1
            n = (hd & 0x7F) + 1
            if hd & 0x80:
                buf += bytes(d[pos:pos + bytespp]) * n; pos += bytespp
            else:
                buf += bytes(d[pos:pos + n * bytespp]); pos += n * bytespp
        raw = bytes(buf[:total])
    else:
        raw = bytes(d[pos:pos + total])
    if len(raw) < total:
        raise ValueError("data TGA terpotong")
    out = bytearray(w * h * 4)
    base = it & 7
    for i in range(w * h):
        px = raw[i * bytespp:(i + 1) * bytespp]
        if base == 1:
            c = pal[px[0] - cmstart] if cmt and 0 <= px[0] - cmstart < len(pal) else b"\0\0\0"
            b, g, r = c[0], c[1], c[2]; a = c[3] if len(c) > 3 else 255
        elif base == 3:
            r = g = b = px[0]; a = 255
        elif bpp == 24:
            b, g, r = px; a = 255
        elif bpp == 32:
            b, g, r, a = px
        else:   # 15 / 16-bit 5-5-5
            v = px[0] | (px[1] << 8)
            r, g, b = ((v >> 10) & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, (v & 31) * 255 // 31; a = 255
        out[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    if not (desc & 0x20):   # asal kiri-bawah -> balik vertikal
        rows = [out[y * w * 4:(y + 1) * w * 4] for y in range(h)][::-1]
        out = bytearray().join(rows)
    if desc & 0x10:         # asal kanan -> balik horizontal
        out = bytearray().join(bytes(b"".join(bytes(r[x * 4:x * 4 + 4]) for x in range(w - 1, -1, -1))) for r in [out[y * w * 4:(y + 1) * w * 4] for y in range(h)])
    return w, h, out


def _tga_inspect(d, p):
    w, h = _u16(d, 12), _u16(d, 14)
    return {"lines": ["TGA %dx%d, %d-bit, tipe %d%s" % (w, h, d[16], d[2], " (RLE)" if d[2] >= 9 else "")], "extract": "-> .png"}


def _tga_extract(d, p, out, opts):
    w, h, px = _tga_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("TGA", "image", _tga_ok, _tga_inspect, _tga_extract, 60, "Truevision TGA (dikenali dari ekstensi + header)")


# --- DDS ---

_DXGI = {71: "DXT1", 72: "DXT1", 74: "DXT3", 75: "DXT3", 77: "DXT5", 78: "DXT5"}
_DXGI_NAMES = {80: "BC4_UNORM", 81: "BC4_SNORM", 83: "BC5_UNORM", 84: "BC5_SNORM", 95: "BC6H_UF16", 96: "BC6H_SF16", 98: "BC7_UNORM", 99: "BC7_UNORM_SRGB",
               28: "R8G8B8A8_UNORM", 87: "B8G8R8A8_UNORM"}


def _dds_info(d):
    h, w = struct.unpack_from("<II", d, 12)
    depth, mips = struct.unpack_from("<II", d, 24)
    pfflags = _u32(d, 80)
    fcc = bytes(d[84:88])
    bits = _u32(d, 88)
    masks = struct.unpack_from("<IIII", d, 92)
    off, fmt = 128, None
    if pfflags & 4:
        fcc_s = fcc.decode("latin-1")
        if fcc_s == "DX10":
            dx = _u32(d, 128)
            off = 148
            fmt = _DXGI.get(dx) or _DXGI_NAMES.get(dx) or "DXGI_%d" % dx
        else:
            fmt = fcc_s
    else:
        fmt = "RGBA%d" % bits if pfflags & 0x41 or pfflags & 0x40 else "RGB%d" % bits
    caps2 = _u32(d, 112)
    return {"w": w, "h": h, "mips": max(1, mips), "fmt": fmt, "off": off, "bits": bits, "masks": masks, "pf": pfflags,
            "cube": bool(caps2 & 0x200), "volume": bool(caps2 & 0x200000)}


def _c565(v): return ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31


def _dxt_decode(d, off, w, h, kind):
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 8 if kind == "DXT1" else 16
    if off + bw * bh * bs > len(d):
        raise ValueError("data DDS terpotong")
    out = bytearray(w * h * 4)
    for by in range(bh):
        for bx in range(bw):
            b = bytes(d[off + (by * bw + bx) * bs:off + (by * bw + bx) * bs + bs])
            cb = b[-8:]
            c0, c1 = struct.unpack_from("<HH", cb, 0)
            r0, r1 = _c565(c0), _c565(c1)
            if c0 > c1 or kind != "DXT1":
                pal = [r0 + (255,), r1 + (255,),
                       tuple((2 * a + b2) // 3 for a, b2 in zip(r0, r1)) + (255,), tuple((a + 2 * b2) // 3 for a, b2 in zip(r0, r1)) + (255,)]
            else:
                pal = [r0 + (255,), r1 + (255,), tuple((a + b2) // 2 for a, b2 in zip(r0, r1)) + (255,), (0, 0, 0, 0)]
            idx = struct.unpack_from("<I", cb, 4)[0]
            alpha = None
            if kind == "DXT3":
                av = int.from_bytes(b[:8], "little")
                alpha = [((av >> (4 * i)) & 15) * 17 for i in range(16)]
            elif kind == "DXT5":
                a0, a1 = b[0], b[1]
                ab = int.from_bytes(b[2:8], "little")
                ap = [a0, a1] + ([(( 6 - i) * a0 + (1 + i) * a1) // 7 for i in range(6)] if a0 > a1 else [((4 - i) * a0 + (1 + i) * a1) // 5 for i in range(4)] + [0, 255])
                alpha = [ap[(ab >> (3 * i)) & 7] for i in range(16)]
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x < w and y < h:
                    r, g, bl, a = pal[(idx >> (2 * i)) & 3]
                    if alpha:
                        a = alpha[i]
                    o = (y * w + x) * 4
                    out[o:o + 4] = bytes((r, g, bl, a))
    return out


# v99.8 [A4]: BC4 (1 kanal) dan BC5 (2 kanal, umum untuk normal map). FourCC ATI1 / BC4U / BC4S dan ATI2 / BC5U / BC5S, atau DXGI 80-84.
_BC4_FMTS = {"ATI1": False, "BC4U": False, "BC4_UNORM": False, "BC4S": True, "BC4_SNORM": True}
_BC5_FMTS = {"ATI2": False, "BC5U": False, "BC5_UNORM": False, "BC5S": True, "BC5_SNORM": True}


def _bc4_block(b, signed: bool):
    """Satu blok 8-byte -> 16 nilai 0..255 (urutan baris). UNORM: 8 / 6+{0,255} nilai; SNORM: dipetakan -1..1 -> 0..255."""
    if signed:
        e0, e1 = struct.unpack_from("<bb", b, 0)
        e0, e1 = max(e0, -127), max(e1, -127)
        pal = [e0, e1] + ([((7 - k) * e0 + k * e1) / 7.0 for k in range(1, 7)] if e0 > e1 else [((5 - k) * e0 + k * e1) / 5.0 for k in range(1, 5)] + [-127, 127])
        pal = [max(0, min(255, int(round((v / 127.0 * 0.5 + 0.5) * 255)))) for v in pal]
    else:
        e0, e1 = b[0], b[1]
        pal = [e0, e1] + ([((7 - k) * e0 + k * e1 + 3) // 7 for k in range(1, 7)] if e0 > e1 else [((5 - k) * e0 + k * e1 + 2) // 5 for k in range(1, 5)] + [0, 255])
    bits = int.from_bytes(bytes(b[2:8]), "little")
    return [pal[(bits >> (3 * i)) & 7] for i in range(16)]


def _bc45_decode(d, off, w, h, two: bool, signed: bool):
    """BC4 -> abu-abu (R=G=B, A=255). BC5 -> R,G dari dua kanal; B direkonstruksi sebagai komponen Z peta normal (sqrt(1-x^2-y^2))."""
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 16 if two else 8
    if off + bw * bh * bs > len(d):
        raise ValueError("data DDS terpotong")
    out = bytearray(w * h * 4)
    for by in range(bh):
        for bx in range(bw):
            o = off + (by * bw + bx) * bs
            r = _bc4_block(d[o:o + 8], signed)
            g = _bc4_block(d[o + 8:o + 16], signed) if two else r
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x >= w or y >= h:
                    continue
                if two:
                    nx, ny = r[i] / 127.5 - 1.0, g[i] / 127.5 - 1.0
                    z = 1.0 - nx * nx - ny * ny
                    bl = int(round((math.sqrt(z) if z > 0 else 0.0) * 127.5 + 127.5))
                    px = (r[i], g[i], max(0, min(255, bl)), 255)
                else:
                    px = (r[i], r[i], r[i], 255)
                q = (y * w + x) * 4
                out[q:q + 4] = bytes(px)
    return out


def _dds_decode(d):
    i = _dds_info(d)
    w, h, off, fmt = i["w"], i["h"], i["off"], i["fmt"]
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran DDS tidak wajar")
    if i["cube"] or i["volume"]:
        raise ValueError("cubemap / tekstur volume: hanya mip pertama bidang pertama yang bisa dibaca; belum didukung")
    if fmt in ("DXT1", "DXT3", "DXT5"):
        return w, h, _dxt_decode(d, off, w, h, fmt)
    if fmt in _BC4_FMTS:
        return w, h, _bc45_decode(d, off, w, h, False, _BC4_FMTS[fmt])
    if fmt in _BC5_FMTS:
        return w, h, _bc45_decode(d, off, w, h, True, _BC5_FMTS[fmt])
    if fmt in ("R8G8B8A8_UNORM", "B8G8R8A8_UNORM") or (not (i["pf"] & 4) and i["bits"] in (24, 32)):
        bpp = 3 if (not (i["pf"] & 4) and i["bits"] == 24) else 4
        raw = bytes(d[off:off + w * h * bpp])
        if len(raw) < w * h * bpp:
            raise ValueError("data DDS terpotong")
        rm, gm, bm, am = i["masks"]
        out = bytearray(w * h * 4)
        sh = lambda m: (m & -m).bit_length() - 1 if m else None
        for px in range(w * h):
            v = int.from_bytes(raw[px * bpp:(px + 1) * bpp], "little")
            if fmt == "R8G8B8A8_UNORM":
                out[px * 4:px * 4 + 4] = raw[px * 4:px * 4 + 4]
            elif fmt == "B8G8R8A8_UNORM":
                b_, g_, r_, a_ = raw[px * 4:px * 4 + 4]; out[px * 4:px * 4 + 4] = bytes((r_, g_, b_, a_))
            else:
                g = lambda m: ((v & m) >> sh(m)) if m else 255
                out[px * 4:px * 4 + 4] = bytes((g(rm), g(gm), g(bm), g(am) if am else 255))
        return w, h, out
    raise ValueError("format DDS %s belum didukung (BC6H / BC7 / ASTC / dll butuh dekoder tambahan)" % fmt)


def _dds_inspect(d, p):
    i = _dds_info(d)
    ok = i["fmt"] in ("DXT1", "DXT3", "DXT5") or i["fmt"] in _BC4_FMTS or i["fmt"] in _BC5_FMTS or i["fmt"].startswith(("RGB", "RGBA", "R8G8B8A8", "B8G8R8A8"))
    L = ["DDS %dx%d, format %s, %d mip%s%s" % (i["w"], i["h"], i["fmt"], i["mips"], ", cubemap" if i["cube"] else "", ", volume" if i["volume"] else "")]
    if i["fmt"] in _BC5_FMTS:
        L.append("BC5 (2 kanal): biasanya peta normal; saat dikonversi R,G = kanal asli, B direkonstruksi dari X,Y")
    elif i["fmt"] in _BC4_FMTS:
        L.append("BC4 (1 kanal): dikonversi ke PNG abu-abu")
    return {"lines": L, "extract": "-> .png (mip pertama)" if ok and not (i["cube"] or i["volume"]) else "format ini belum bisa didekode ke PNG"}


def _dds_extract(d, p, out, opts):
    w, h, px = _dds_decode(d)
    f_ = _dds_info(d)["fmt"]
    note = " (BC5: B = Z hasil rekonstruksi normal map)" if f_ in _BC5_FMTS else " (BC4: abu-abu)" if f_ in _BC4_FMTS else ""
    out.write("%s.png" % _obj_name(p.stem, "texture"), _png_encode(w, h, px), "image", "%dx%d dari DDS%s" % (w, h, note))


register("DDS", "image", lambda d, e: d[:4] == b"DDS " and len(d) >= 128 and _u32(d, 4) == 124, _dds_inspect, _dds_extract, 12, "tekstur DirectDraw (game)")


