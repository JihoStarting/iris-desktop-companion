import struct
def register_formats(reg):
    def detect(d, ext): return d[:4] == b"DEMO"
    def inspect(d, p):
        n = struct.unpack_from("<I", d, 4)[0]
        return {"lines": ["DEMO paket: %d entri" % n], "extract": "semua entri"}
    def extract(d, p, out, opts):
        n = struct.unpack_from("<I", d, 4)[0]
        pos = 8
        for i in range(n):
            ln = struct.unpack_from("<I", d, pos)[0]; pos += 4
            out.write("demo/%d.bin" % i, bytes(d[pos:pos+ln]), "archive-entry"); pos += ln
    reg("DEMO", "archive", detect, inspect, extract, priority=5, about="contoh plugin")
