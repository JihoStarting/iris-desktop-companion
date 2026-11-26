"""test_zstd_window.py (v99.63): offset ke dictionary harus <= ukuran window. Frame dirakit tangan (tanpa kompresor): tabel bawaan, satu sequence."""
import importlib.util, sys
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)

def frame(wd, off, lit=b"X", ml_code=1):
    tll, tof, tml = rt._zstd_def_table("ll"), rt._zstd_def_table("of"), rt._zstd_def_table("ml")
    ov = off + 3; oc = ov.bit_length() - 1
    sl, so, sm = tll[0].index(1), tof[0].index(oc), tml[0].index(ml_code)
    v = ((((sl << tof[3]) | so) << tml[3]) | sm) << oc | (ov - (1 << oc))
    nb = tll[3] + tof[3] + tml[3] + oc
    v |= 1 << nb
    stream = v.to_bytes((nb + 8) // 8, "little")
    blk = bytes([(len(lit) << 3)]) + lit + b"\x01\x00" + stream
    bh = 1 | (2 << 1) | (len(blk) << 3)
    return b"\x28\xb5\x2f\xfd" + b"\x00" + bytes([wd]) + bh.to_bytes(3, "little") + blk

dic = bytes((i * 7 + i // 13) & 255 for i in range(2000))
bad = 0
def chk(name, ok):
    global bad
    print(("ok   " if ok else "BEDA ") + name); bad += not ok
r = rt._zstd_decompress(frame(0x08, 1500), dictionary=dic)                 # window 2048 >= 1500
chk("offset dalam window -> terdekode", r == b"X" + dic[2001 - 1500:2001 - 1500 + 4])
try:
    rt._zstd_decompress(frame(0x00, 1500), dictionary=dic); chk("offset > window ditolak", False)   # window 1024 < 1500
except ValueError as e:
    chk("offset > window ditolak (ValueError)", "window" in str(e))
r = rt._zstd_decompress(frame(0x00, 900), dictionary=dic)                   # 900 <= 1024, masih ke dictionary
chk("offset 900 <= window 1024 -> terdekode", r == b"X" + dic[2001 - 900:2001 - 900 + 4])
sys.exit(1 if bad else 0)
