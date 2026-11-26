"""Bandingkan disassembler AArch64 bawaan (_a64_dis) dengan capstone. Pakai: python test_a64_vs_capstone.py [jumlah] [seed]"""
import importlib.util, random, re, sys, collections
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)
import capstone
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
PC = 0x400000

def _nums(s, mask):
    s = s.lower().replace("#", "").replace(",", " , ")
    s = re.sub(r"(-?)0x([0-9a-f]+)", lambda m: str(((-1 if m.group(1) else 1) * int(m.group(2), 16)) & mask), s)
    s = re.sub(r"-(\d+)", lambda m: str((-int(m.group(1))) & mask), s)
    s = re.sub(r"(?<![0-9a-fx])0+(?![0-9a-fx.])", "0", s)               # capstone mencetak nol 64-bit sebagai 0000000000000000
    return re.sub(r"\s+", "", s)

def same(a, b):
    """Nilai imediat dibandingkan mod 2^64, atau mod 2^32 (capstone mencetak imm W bertanda dan imm pasca-indeks tak bertanda)."""
    return _nums(a, 0xFFFFFFFFFFFFFFFF) == _nums(b, 0xFFFFFFFFFFFFFFFF) or _nums(a, 0xFFFFFFFF) == _nums(b, 0xFFFFFFFF)

def ours(w):
    m, o, t = rt._a64_dis(w, PC)
    return m, o, (m + " " + o).strip()

def theirs(w):
    for i in cs.disasm(w.to_bytes(4, "little"), PC):
        return i.mnemonic, i.op_str, (i.mnemonic + " " + i.op_str).strip()
    return None

def main(n=300000, seed=1, force=None):
    """force=(mask, nilai): bit di mask dipaksa ke nilai, supaya kata acak jatuh di daerah encoding tertentu (mis. Advanced SIMD)."""
    rnd = random.Random(seed)
    bad = collections.Counter(); ex = {}; known = 0; falsepos = 0; fp_ex = {}
    for _ in range(n):
        w = rnd.getrandbits(32)
        if force: w = (w & ~force[0] & 0xFFFFFFFF) | force[1]
        m, o, t = ours(w)
        if m == ".word": continue
        known += 1
        c = theirs(w)
        if c is None:
            if m.startswith("ldtr") and ours(w)[2].split(", [")[0].split()[-1][1:] == ours(w)[2].split("[x")[1].split(",")[0].rstrip("]"):
                continue                                                   # ldtr dengan Rt == Rn: sah menurut ARM ARM, capstone menolak
            falsepos += 1; fp_ex.setdefault(m, w); continue
        if m in ("prfm", "prfum") and c[1].startswith(", "):                  # prfop cadangan: capstone mencetak kosong, kita #n
            continue
        if m in ("mrs", "msr") and re.search(r"s\d_\d_c\d+_c\d+_\d", t):    # nama register sistem: capstone memakai tabel nama
            continue
        if m in ("mrs", "msr"):                                               # nama register sistem: tabel nama berbeda, bukan salah decode
            continue
        if m.startswith(("ldtr",)) and re.match(r"\w+ ([wx])(\d+), \[x(\d+)", t) and re.match(r"\w+ [wx](\d+), \[x(\d+)", t).group(1) == re.match(r"\w+ [wx](\d+), \[x(\d+)", t).group(2):
            continue                                                       # ldtr dengan Rt == Rn: sah menurut ARM ARM, capstone menolak
        if m == "bfxil" and re.search(r", [wx]zr,", t) and c[0] == "bfc":   # alias setara: BFM dengan sumber xzr
            continue
        if m in ("sxtl", "sxtl2", "uxtl", "uxtl2") and c[0] == m.replace("xtl", "shll") and c[1].endswith(", #0"):   # alias pilihan ARM ARM: sxtl == sshll #0
            continue
        if not same(t, c[2]):
            key = (m, c[0]); bad[key] += 1; ex.setdefault(key, (w, t, c[2]))
    print("kata dikenali: %d  tak-valid-di-capstone: %d  beda teks: %d" % (known, falsepos, sum(bad.values())))
    for (a, b), k in bad.most_common(60):
        w, t, c = ex[(a, b)]
        print("%5d  %08x  ours=%-38s cs=%s" % (k, w, t, c))
    for m, w in list(fp_ex.items())[:30]: print("FP %-8s %08x ours=%s" % (m, w, ours(w)[2]))
    return sum(bad.values()), falsepos

REGIONS = {"vektor": (0x9E000000, 0x0E000000), "skalar": (0xDF000000, 0x5E000000), "ldst": (0xBE000000, 0x0C000000), "indexed": (0x9F000000, 0x0F000000)}
if __name__ == "__main__":
    reg = sys.argv[3] if len(sys.argv) > 3 else None          # opsional: vektor | skalar | ldst | indexed
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300000, int(sys.argv[2]) if len(sys.argv) > 2 else 1, REGIONS[reg] if reg else None)
