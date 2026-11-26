"""Bandingkan disassembler Thumb / Thumb-2 bawaan (_thumb_dis) dengan capstone. Pakai: python test_thumb_vs_capstone.py [jumlah] [seed]"""
import importlib.util, random, re, sys, collections
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)
import capstone
cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
PC = 0x400000
def nums(s):
    s = s.lower().replace("#", "").replace(",", " , ")
    s = re.sub(r"(-?)0x([0-9a-f]+)", lambda m: str(((-1 if m.group(1) else 1) * int(m.group(2), 16)) & 0xFFFFFFFF), s)
    s = re.sub(r"-(\d+)", lambda m: str((-int(m.group(1))) & 0xFFFFFFFF), s)
    return re.sub(r"\s+", "", s)
def main(n=300000, seed=1):
    rnd = random.Random(seed); bad = collections.Counter(); ex = {}; known = 0; fp = collections.Counter(); fpx = {}
    for _ in range(n):
        h1 = rnd.getrandbits(16); h2 = rnd.getrandbits(16)
        if rnd.random() < 0.5: h1 = (h1 & 0x07FF) | rnd.choice((0xE800, 0xF000, 0xF800))
        r = rt._thumb_dis(h1, h2, PC)
        m, o = r[0], r[1]
        if m == ".word" or m.startswith("."): continue
        known += 1
        code = h1.to_bytes(2, "little") + h2.to_bytes(2, "little")
        c = None
        for i in cs.disasm(code, PC): c = i; break
        ours = (m + " " + o).strip()
        if c is None: fp[m] += 1; fpx.setdefault(m, (h1, h2, ours)); continue
        if nums(ours) != nums(c.mnemonic + " " + c.op_str):
            k = (m, c.mnemonic); bad[k] += 1; ex.setdefault(k, (h1, h2, ours, c.mnemonic + " " + c.op_str))
    print("dikenali: %d  tak-valid-di-capstone: %d  beda teks: %d" % (known, sum(fp.values()), sum(bad.values())))
    for k, v in bad.most_common(40): print("%5d %04x %04x ours=%-34s cs=%s" % ((v,) + ex[k]))
    for k, v in fp.most_common(15): print("FP %5d %-8s %04x %04x %s" % ((v, k) + fpx[k]))
if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300000, int(sys.argv[2]) if len(sys.argv) > 2 else 1)
