# rea_triage bagian 30/47: dekoder_string (baris asli 12606-12900). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- dekoder skrip / string tersandi -----------------------

_PS_ENC = re.compile(r"(?i)\s-(?:e|ec|en|enc|enco|encod|encode|encoded|encodedc\w*)\s+['\"]?([A-Za-z0-9+/]{16,}={0,2})")
_B64_CALL = re.compile(r"(?i)frombase64string\(\s*['\"]([A-Za-z0-9+/]{16,}={0,2})['\"]\s*\)")
_CHAR_PS = re.compile(r"(?i)(?:\[char\]\s*\(?\s*\d{2,3}\s*\)?\s*\+?\s*){5,}")
_CHAR_VB = re.compile(r"(?i)(?:chrw?\(\s*\d{2,3}\s*\)\s*&?\s*){5,}")
_CHAR_JS = re.compile(r"(?i)fromcharcode\(\s*((?:\d{2,3}\s*,\s*){4,}\d{2,3})\s*\)")
_HEX_ESC = re.compile(r"(?:\\x[0-9a-fA-F]{2}){8,}")


def _printable(t: str) -> bool:
    return len(t) >= 6 and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9


def _decode_scripts(strs: list[str]) -> list[dict]:
    """Dekode PowerShell -EncodedCommand, FromBase64String('..'), rangkaian [char] / Chr() / fromCharCode, dan \\xNN. Hanya teks; tidak dijalankan."""
    full = "\n".join(s[:4000] for s in strs)[:8 * 1024 * 1024]
    out: list[dict] = []

    def add(kind, text):
        t = text.strip()
        if _printable(t) and all(x["text"] != t[:600] for x in out) and len(out) < 12:
            out.append({"kind": kind, "text": t[:600]})

    for m in list(_PS_ENC.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        for enc in ("utf-16le", "utf-8"):
            t = raw.decode(enc, "ignore")
            if _printable(t):
                add("PowerShell -EncodedCommand", t)
                break
    for m in list(_B64_CALL.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        t = raw.decode("utf-16le", "ignore") if raw[1:2] == b"\x00" else raw.decode("utf-8", "ignore")
        add("FromBase64String", t)
    for rx, kind in ((_CHAR_PS, "rangkaian [char]"), (_CHAR_VB, "rangkaian Chr()")):
        for m in list(rx.finditer(full))[:4]:
            codes = [int(x) for x in re.findall(r"\d{2,3}", m.group(0))]
            if all(32 <= c < 127 or c in (9, 10, 13) for c in codes):
                add(kind, "".join(chr(c) for c in codes))
    for m in list(_CHAR_JS.finditer(full))[:4]:
        codes = [int(x) for x in re.findall(r"\d+", m.group(1))]
        if all(32 <= c < 127 for c in codes):
            add("fromCharCode", "".join(chr(c) for c in codes))
    for m in list(_HEX_ESC.finditer(full))[:4]:
        try:
            add("escape \\xNN", bytes(int(x, 16) for x in re.findall(r"\\x([0-9a-fA-F]{2})", m.group(0))).decode("latin-1"))
        except ValueError:
            pass
    return out


def _script_enrich(rep: dict, strs: list[str]) -> None:
    try:
        dec = _decode_scripts(strs)
    except Exception as e:
        dec = []
        rep["warn"].append("dekoder skrip gagal: %s" % type(e).__name__)
    rep["decoded"] = dec
    if dec:
        ind = rep["ind"]
        for x in dec:   # URL di dalam teks hasil dekode ikut jadi IOC
            for u in _URL.findall(x["text"]):
                u = u.rstrip(".,;)")
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
        rep["warn"].append("string tersandi berhasil didekode (%d): %s" % (len(dec), ", ".join(sorted({x["kind"] for x in dec}))))


def _render_decoded(rep: dict, a, compact: bool, defang: bool) -> None:
    for x in (rep.get("decoded") or [])[: (2 if compact else 8)]:
        a("Hasil dekode (%s): %s" % (x["kind"], _df(_clean(x["text"])[:240 if compact else 400], defang)))


# ----------------------- v99.9 [C2]: dekoder multi-layer otomatis -----------------------
# Pipeline statis: (hex | base64) -> (gzip | zlib | deflate mentah) -> XOR satu-byte, maksimal CHAIN_MAX_LAYERS lapis, pada blok
# mencurigakan di string skrip (PowerShell / VBScript / JS), resource PE, dan resource terkelola .NET. Tidak ada yang dijalankan.
# Rantai hanya dilaporkan bila ujungnya dikenali (PE / ELF / ZIP / dokumen / teks nyata), jadi data acak tidak menghasilkan laporan palsu.

CHAIN_MAX_LAYERS = 3
CHAIN_MAX_OUT = 8 * 1024 * 1024      # batas hasil dekompresi per lapis (anti zip-bomb)
CHAIN_TIME = 2.0                     # detik untuk seluruh pemindaian lapisan
CHAIN_MAX_SRC = 24                   # jumlah blok sumber yang dicoba
_CHAIN_B64 = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}\Z")
_CHAIN_HEX = re.compile(r"(?:[0-9A-Fa-f]{2}){16,}\Z")
_CHAIN_SKIP_RES = frozenset({"ICON", "CURSOR", "BITMAP", "MENU", "DIALOG", "STRING", "ACCELERATOR", "MESSAGETABLE", "GROUP_CURSOR", "GROUP_ICON", "VERSION", "MANIFEST"})
_CHAIN_MAGIC = ((b"\x7fELF", "ELF"), (b"PK\x03\x04", "ZIP"), (b"7z\xbc\xaf\x27\x1c", "7z"), (b"Rar!", "RAR"), (b"MSCF", "CAB"),
                (b"%PDF-", "PDF"), (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "OLE2"), (b"{\\rtf", "RTF"))


def _chain_label(b: bytes) -> str | None:
    """Jenis data bila diawali tanda tangan format yang dikenal (PE harus punya penunjuk 'PE\\0\\0' yang sah)."""
    h = bytes(b[:8])
    if h[:2] == b"MZ":
        if len(b) >= 0x40:
            o = struct.unpack_from("<I", b, 0x3C)[0]
            if o < len(b) - 4 and bytes(b[o:o + 4]) == b"PE\x00\x00":
                return "PE/MZ"
        return None
    for magic, name in _CHAIN_MAGIC:
        if h.startswith(magic):
            return name
    return None


def _chain_text(b: bytes) -> str | None:
    """Teks bila isinya terbaca (UTF-8 atau UTF-16LE); None untuk data biner / acak / hampir konstan (mis. nol yang di-XOR)."""
    s = bytes(b[:4096])
    if len(s) < 8:
        return None
    u16 = s[1::2].count(0) > 0.9 * (len(s) // 2)
    t = s.decode("utf-16le" if u16 else "utf-8", "ignore").lstrip("\ufeff")
    if not u16 and len(t.encode("utf-8")) < 0.97 * len(s) - 4:
        return None
    if len(t) < 6 or len(set(t)) < 8 or max(collections.Counter(t).values()) > 0.45 * len(t):
        return None
    if sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) < 0.95 or sum(c.isalpha() for c in t) < 6:
        return None
    return bytes(b[:CHAIN_MAX_OUT]).decode("utf-16le" if u16 else "utf-8", "ignore").lstrip("\ufeff")


def _chain_known(b: bytes) -> bool:
    return bool(_chain_label(b)) or _chain_text(b) is not None


def _t_decode_text(b: bytes):
    """Lapis hex / base64 dari teks (ASCII atau UTF-16LE). Mengembalikan (nama, byte) atau None."""
    t = _chain_text(b)
    if t is None:
        return None
    c = re.sub(r"\s+", "", t)
    if len(c) > CHAIN_MAX_OUT * 2:
        return None
    if _CHAIN_HEX.match(c):
        try:
            return "hex", bytes.fromhex(c)
        except ValueError:
            return None
    if _CHAIN_B64.match(c) and len(c) % 4 != 1:
        try:
            raw = base64.b64decode(c + "=" * (-len(c) % 4))
        except Exception:
            return None
        return ("base64", raw) if len(raw) >= 16 else None
    return None


def _t_inflate(b: bytes):
    """Lapis gzip / zlib / deflate mentah, dengan batas ukuran hasil. Deflate mentah hanya diterima bila hasilnya dikenali."""
    if len(b) < 12:
        return None
    if b[:2] == b"\x1f\x8b":
        cand = (("gzip", 31),)
    elif b[0] == 0x78 and b[1] in (0x01, 0x5E, 0x9C, 0xDA):
        cand = (("zlib", 15),)
    else:
        cand = (("deflate", -15),)
    for name, wb in cand:
        try:
            out = zlib.decompressobj(wb).decompress(bytes(b[:CHAIN_MAX_OUT]), CHAIN_MAX_OUT)
        except Exception:
            continue
        if len(out) >= 8 and (name != "deflate" or _chain_known(out)):
            return name, out
    return None


def _t_xor1(b: bytes):
    """Lapis XOR satu-byte: kunci dipilih bila hasilnya dikenali (format / teks nyata). Data yang sudah dikenali tidak di-XOR lagi."""
    if len(b) < 32 or _chain_known(b):
        return None
    head = bytes(b[:512])
    if len(set(head)) < 4:
        return None
    for k in range(1, 256):
        t = head.translate(_xor_table("XOR", k))
        if _chain_label(t) or t[:2] == b"\x1f\x8b" or (t[0] == 0x78 and t[1] in (0x01, 0x5E, 0x9C, 0xDA)) or _chain_text(t) is not None:
            return "XOR 0x%02X" % k, bytes(b[:CHAIN_MAX_OUT]).translate(_xor_table("XOR", k))
    return None


def _chain_walk(data: bytes, src: str, deadline: float, min_steps: int) -> list[dict]:
    """Cari rantai dekode terpanjang dari `data`. Hasil: daftar {src, steps, kind, size, sha256, preview, urls}."""
    found: list[dict] = []

    def rec(b: bytes, steps: list[str], depth: int) -> None:
        if time.monotonic() > deadline or len(found) >= 3 or depth >= CHAIN_MAX_LAYERS:
            return
        for tf in (_t_decode_text, _t_inflate, _t_xor1):
            r = tf(b)
            if not r:
                continue
            name, nb = r
            st = steps + [name]
            lab = _chain_label(nb)
            txt = None if lab else _chain_text(nb)
            before = len(found)
            if depth + 1 < CHAIN_MAX_LAYERS:
                if txt:   # blob base64 / hex di dalam teks hasil dekode (mis. skrip PowerShell berlapis)
                    blobs = [m_ for m_ in _B64_CALL.findall(txt)[:2]] + [m_ for m_ in _B64.findall(txt)[:2]]
                    for bl in blobs:
                        rec(bl.encode("ascii", "ignore"), st, depth + 1)
                else:
                    rec(nb, st, depth + 1)
            if len(found) > before:
                return                       # rantai yang lebih dalam menang
            if (lab or txt) and len(st) >= min_steps:
                urls = [u.rstrip(".,;)") for u in _URL.findall(txt or "")][:5] if txt else []
                found.append({"src": src, "steps": st, "kind": lab or "teks", "size": len(nb), "sha256": hashlib.sha256(bytes(nb)).hexdigest(),
                              "preview": _clean((txt or "")[:160]) if txt else "", "urls": urls})
                return

    rec(bytes(data), [], 0)
    return found


def _layers_scan(d: bytes, strs: list[str], pe: dict | None, dn: dict | None) -> list[dict]:
    deadline = time.monotonic() + CHAIN_TIME
    out: list[dict] = []
    seen: set[str] = set()
    n_src = 0

    def take(res):
        for x in res:
            key = x["sha256"] + "|".join(x["steps"])
            if key not in seen and len(out) < 8:
                seen.add(key)
                out.append(x)

    # 1) resource PE dan resource terkelola .NET: satu lapis saja sudah janggal (resource sah tidak di-XOR / di-deflate mentah)
    leaves = []
    for x in (pe.get("res", []) if pe else []):
        if x["type"] not in _CHAIN_SKIP_RES and not (x.get("fmt") and x.get("fmt_ok")) and x["size"] >= 32:
            leaves.append(("resource %s/%s" % (x["type"], x["name"]), x["off"], x["size"]))
    for x in (dn.get("mres", []) if dn else []):
        if x["size"] >= 32 and not (x.get("fmt") and x.get("fmt_ok")):
            leaves.append(("resource .NET @0x%X" % x["off"], x["off"], x["size"]))
    for src, off, size in leaves:
        if n_src >= CHAIN_MAX_SRC or time.monotonic() > deadline:
            break
        n_src += 1
        take(_chain_walk(d[off:off + min(size, CHAIN_MAX_OUT)], src, deadline, 1))
    # 2) blob base64 / argumen FromBase64String / -EncodedCommand di string: satu base64 polos sudah dilaporkan _decode_b64, jadi minimal dua lapis
    cands: list[str] = []
    full = "\n".join(s[:200000] for s in strs[:4000])[:8 * 1024 * 1024]
    for rx in (_PS_ENC, _B64_CALL):
        cands += [m.group(1) for m in itertools.islice(rx.finditer(full), 6)]
    cands += [m.group(0) for m in itertools.islice(_B64.finditer(full), 12)]
    for c in _uniq(cands, CHAIN_MAX_SRC):
        if n_src >= CHAIN_MAX_SRC or time.monotonic() > deadline:
            break
        n_src += 1
        take(_chain_walk(c.encode("ascii", "ignore"), "string base64", deadline, 2))
    return out


def _layers_enrich(rep: dict, d: bytes, strs: list[str]) -> None:
    try:
        lay = _layers_scan(d, strs, rep.get("pe"), rep.get("dotnet"))
    except Exception as e:
        lay = []
        rep["warn"].append("dekoder berlapis gagal: %s" % type(e).__name__)
    rep["layers"] = lay
    if lay:
        ind = rep["ind"]
        for x in lay:
            for u in x["urls"]:
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
        x = next((y for y in lay if y["kind"] not in ("teks",)), lay[0])
        rep["warn"].append("data berlapis berhasil dibuka (%d): %s -> %s (%s)" % (len(lay), " -> ".join(x["steps"]), x["kind"], x["src"]))


def _score_layers(rep: dict, add) -> None:
    lay = rep.get("layers") or []
    if any(x["kind"] in ("PE/MZ", "ELF") for x in lay):
        add(3, "executable tersembunyi di balik lapisan dekode (%s)" % " -> ".join(next(x for x in lay if x["kind"] in ("PE/MZ", "ELF"))["steps"]))
    elif any(x["kind"] in ("ZIP", "7z", "RAR", "CAB", "OLE2") for x in lay):
        add(2, "arsip / dokumen tersembunyi di balik lapisan dekode")
    elif any(len(x["steps"]) >= 2 for x in lay):
        add(1, "teks tersembunyi di balik beberapa lapis dekode")


def _render_layers(rep: dict, a, compact: bool, defang: bool) -> None:
    for x in (rep.get("layers") or [])[: (2 if compact else 6)]:
        a("Dekode berlapis (%s): %s => %s %s, sha256 %s...%s" % (x["src"], " -> ".join(x["steps"]), x["kind"], _human(x["size"]), x["sha256"][:16],
                                                               (" | " + _df(x["preview"][:100 if compact else 160], defang)) if x["preview"] else ""))


