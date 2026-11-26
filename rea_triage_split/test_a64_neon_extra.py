"""test_a64_neon_extra.py (v99.65): FCMLA / FCADD / FP16 indexed / i8mm / bf16 dibandingkan dengan capstone secara EKSHAUSTIF di dua kelas encoding
(tiga-sama-extra dan indexed): semua Q, U, size, op, L, M, H dan beberapa nilai Rd / Rn / Rm. Butuh `pip install capstone`.
Kata yang capstone tolak harus tetap .word di sini, dan sebaliknya."""
import importlib.util, sys, itertools, re
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)
import capstone
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
PC = 0x400000
def norm(s):
    s = s.lower().replace("#", "")
    s = re.sub(r"0x([0-9a-f]+)", lambda m: str(int(m.group(1), 16)), s)
    return re.sub(r"\s+", "", s)
def theirs(w):
    for i in cs.disasm(w.to_bytes(4, "little"), PC): return (i.mnemonic + " " + i.op_str).strip()
def ours(w):
    m, o, t = rt._a64_dis(w, PC)
    return None if m == ".word" else (m + " " + o).strip()
regs = [(1, 2, 3), (0, 31, 0), (31, 17, 29), (5, 9, 31)]
EXTRA = {"fcmla", "fcadd", "usdot", "smmla", "ummla", "usmmla", "bfdot", "bfmmla", "bfmlalb", "bfmlalt", "sudot", "fmlal", "fmlsl", "fmlal2", "fmlsl2"}
bad = n = both = miss_ours = extra_ours = 0
shown = 0
def check(w, only):
    global bad, n, both, miss_ours, extra_ours, shown
    n += 1
    a, b = ours(w), theirs(w)
    if b is not None and b.split()[0] not in only and not (a is None):
        pass
    if a is None and b is None: return
    if b is not None and b.split()[0] not in only and a is None: return          # di luar lingkup tahap ini
    if a is not None and b is None:
        extra_ours += 1; bad += 1
        if shown < 12: print("KELEBIHAN %08x ours=%s" % (w, a)); shown += 1
    elif a is not None and norm(a) != norm(b):
        bad += 1
        if shown < 12: print("BEDA %08x ours=%s cs=%s" % (w, a, b)); shown += 1
    elif a is None:
        miss_ours += 1; bad += 1
        if shown < 12: print("TERLEWAT %08x cs=%s" % (w, b)); shown += 1
    else: both += 1
# kelas tiga-sama-extra: 0 Q U 01110 size 0 Rm 1 op4 1 Rn Rd
for q, u, size, op in itertools.product((0, 1), (0, 1), range(4), range(16)):
    for rd, rn, rm in regs:
        check((q << 30) | (u << 29) | (0b01110 << 24) | (size << 22) | (rm << 16) | (1 << 15) | (op << 11) | (1 << 10) | (rn << 5) | rd, EXTRA)
# kelas tiga-sama (non-extra): 0 Q U 01110 size 1 Rm op5 1 Rn Rd, hanya opcode FMLAL (0x19 / 0x1D)
for q, u, size, op in itertools.product((0, 1), (0, 1), range(4), (0x19, 0x1D)):
    for rd, rn, rm in regs:
        check((q << 30) | (u << 29) | (0b01110 << 24) | (size << 22) | (1 << 21) | (rm << 16) | (op << 11) | (1 << 10) | (rn << 5) | rd, {"fmlal", "fmlsl", "fmlal2", "fmlsl2"})
# kelas indexed: 0 Q U 01111 size L M Rm op4 H 0 Rn Rd
for q, u, size, l, m, h, op in itertools.product((0, 1), (0, 1), range(4), (0, 1), (0, 1), (0, 1), range(16)):
    for rd, rn, rm in regs:
        check((q << 30) | (u << 29) | (0b01111 << 24) | (size << 22) | (l << 21) | (m << 20) | ((rm & 15) << 16) | (op << 12) | (h << 11) | (rn << 5) | rd,
              EXTRA | {"fmla", "fmls", "fmul", "fmulx"})
print("kata: %d  sama: %d  beda: %d (kelebihan %d, terlewat %d)" % (n, both, bad, extra_ours, miss_ours))
sys.exit(1 if bad else 0)
