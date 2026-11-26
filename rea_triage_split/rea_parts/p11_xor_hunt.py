# rea_triage bagian 11/47: xor_hunt (baris asli 4144-4255). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- XOR / ADD / ROL ------------------------------

_XOR_WORDS = [b"This program cannot be run", b"https://", b"http://", b"kernel32", b"KERNEL32", b"cmd.exe", b"powershell", b"GetProcAddress", b"LoadLibrary",
              b"VirtualAlloc", b"WScript.Shell", b"/bin/sh", b"User-Agent", b"Mozilla/5.0"]
_XOR_URL = re.compile(rb"https?://[\x21-\x7e]{4,100}")
def _xor_table(op: str, key: int) -> bytes:
    if op == "XOR":
        return bytes(i ^ key for i in range(256))
    if op == "ADD":
        return bytes((i + key) & 255 for i in range(256))
    return bytes(((i << key) | (i >> (8 - key))) & 255 for i in range(256))   # ROL


def _xor_hunt(d: bytes, budget: float = 3.0) -> list[dict]:
    """Cari kata kunci (URL, stub DOS, nama API) yang baru muncul setelah dekode satu byte (XOR / ADD / ROL).
    XOR dan ADD dicari lewat selisih antar-byte (tidak bergantung pada kunci), jadi 255 kunci dicek sekali jalan, bukan satu per satu.
    Jendela: 2 MB pertama + 1 MB terakhir berkas."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []   # teks / skrip biasa: tidak ada gunanya
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    n = len(samp)
    words = [w for w in _XOR_WORDS if w not in samp]   # kata yang sudah polos di berkas tidak diburu
    t0 = time.monotonic()
    found: dict[tuple[str, int], set] = {}
    xd = (int.from_bytes(samp, "big") ^ int.from_bytes(samp[1:] + b"\0", "big")).to_bytes(n, "big")
    for w in words:
        pat = bytes(w[i] ^ w[i + 1] for i in range(len(w) - 1))
        pos, tries = xd.find(pat), 0
        while pos >= 0 and tries < 4:
            k = samp[pos] ^ w[0]
            if k and pos + len(w) <= n and bytes(b ^ k for b in samp[pos:pos + len(w)]) == w:
                found.setdefault(("XOR", k), set()).add(w)
            pos, tries = xd.find(pat, pos + 1), tries + 1
    del xd
    if time.monotonic() - t0 < budget:
        ad = bytes((b - a) & 255 for a, b in zip(samp, samp[1:]))
        for w in words:
            pat = bytes((w[i + 1] - w[i]) & 255 for i in range(len(w) - 1))
            pos, tries = ad.find(pat), 0
            while pos >= 0 and tries < 4:
                k = (w[0] - samp[pos]) & 255
                if k and pos + len(w) <= n and bytes((b + k) & 255 for b in samp[pos:pos + len(w)]) == w:
                    found.setdefault(("ADD", k), set()).add(w)
                pos, tries = ad.find(pat, pos + 1), tries + 1
        del ad
    for r in range(1, 8):
        if time.monotonic() - t0 > budget:
            break
        dec = samp.translate(_xor_table("ROL", r))
        for w in words:
            if w in dec:
                found.setdefault(("ROL", r), set()).add(w)
    res: list[dict] = []
    for (op, key), ws in found.items():
        urls = [u.decode("ascii", "replace") for u in _uniq(_XOR_URL.findall(samp.translate(_xor_table(op, key))), 3)] if any(w.startswith(b"http") for w in ws) else []
        res.append({"op": op, "key": key, "words": sorted(w.decode("ascii") for w in ws)[:4], "count": len(ws), "urls": urls})
    res.sort(key=lambda x: (-x["count"], x["op"] != "XOR", x["key"]))
    return res[:5]


_XOR_CRIB = b"This program cannot be run in DOS mode"


def _xor_multi(d: bytes, budget: float = 3.0) -> list[dict]:
    """XOR dengan kunci BERULANG 2-16 byte. Known-plaintext: tulisan stub DOS tetap polos di PE biasa, jadi selisih d[j] ^ d[j+k] pada stub
    terenkode kunci periode k sama persis dengan selisih teksnya sendiri, apa pun kuncinya. Dicari lewat big-int (satu XOR per k).
    RC4 / kunci tak berulang tidak bisa diburu begini tanpa kunci. Jendela: 2 MB pertama + 1 MB terakhir."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    if _XOR_CRIB in samp:
        return []
    n, crib = len(samp), _XOR_CRIB
    t0 = time.monotonic()
    x = int.from_bytes(samp, "big")
    mask = (1 << (8 * n)) - 1

    def to_off(p: int) -> int:
        return p if len(d) <= head + tail or p < head else len(d) - tail + (p - head)

    res: list[dict] = []
    seen: set[int] = set()
    for k in range(2, 17):
        if time.monotonic() - t0 > budget or len(res) >= 3:
            break
        diff = (((x << (8 * k)) & mask) ^ x).to_bytes(n, "big")
        pat = bytes(crib[i] ^ crib[i + k] for i in range(len(crib) - k))
        pos, tries = diff.find(pat), 0
        while pos >= 0 and tries < 4:
            tries += 1
            if pos + len(crib) <= n and pos not in seen:
                ks = bytes(samp[pos + i] ^ crib[i] for i in range(len(crib)))
                if all(ks[i] == ks[i % k] for i in range(len(crib))) and len(set(ks[:k])) > 1:
                    seen.add(pos)
                    # kunci disejajarkan ke awal MZ (stub DOS lazim di offset 0x4E dari MZ)
                    mz = pos - 0x4E
                    key = bytes(ks[(i - 0x4E) % k] for i in range(k))
                    ok = mz >= 0 and bytes(samp[mz + i] ^ key[i % k] for i in range(2)) == b"MZ"
                    res.append({"k": k, "key": (key if ok else ks[:k]).hex(), "off": to_off(pos), "mz": ok, "mz_off": to_off(mz) if ok else 0})
            pos = diff.find(pat, pos + 1)
    res.sort(key=lambda r: (not r["mz"], r["k"]))
    return res[:3]


