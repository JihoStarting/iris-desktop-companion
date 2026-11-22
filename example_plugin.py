import struct

MAX_ENTRI = 100_000   # batas wajar; header palsu tidak boleh memaksa perulangan raksasa


def _jumlah_entri(d):
    """Baca jumlah entri dari header, atau lempar ValueError bila header rusak / tidak masuk akal."""
    if len(d) < 8:
        raise ValueError("header DEMO terpotong")
    n = struct.unpack_from("<I", d, 4)[0]
    if n > MAX_ENTRI:
        raise ValueError("jumlah entri %d melebihi batas %d" % (n, MAX_ENTRI))
    return n


def register_formats(reg):
    def detect(d, ext): return len(d) >= 8 and d[:4] == b"DEMO"

    def inspect(d, p):
        try:
            n = _jumlah_entri(d)
        except ValueError as e:
            return {"lines": ["DEMO paket rusak: %s" % e], "extract": "tidak bisa"}
        return {"lines": ["DEMO paket: %d entri" % n], "extract": "semua entri"}

    def extract(d, p, out, opts):
        n = _jumlah_entri(d)
        pos = 8
        for i in range(n):
            if pos + 4 > len(d):
                raise ValueError("entri %d: data terpotong sebelum panjangnya" % i)
            ln = struct.unpack_from("<I", d, pos)[0]; pos += 4
            if ln > len(d) - pos:   # tanpa ini, entri terpotong diam-diam menghasilkan berkas pendek
                raise ValueError("entri %d: panjang %d melewati akhir data" % (i, ln))
            # Nama keluaran dibuat dari indeks, bukan dari data paket, jadi aman dari "../" dan path absolut.
            # Plugin yang memakai nama dari data paket WAJIB menyaring ".." dan path absolut dulu.
            out.write("demo/%d.bin" % i, bytes(d[pos:pos+ln]), "archive-entry"); pos += ln

    reg("DEMO", "archive", detect, inspect, extract, priority=5, about="contoh plugin")
