"""test_a64_vtable.py (v99.64): BLR register lewat vtable / objek (penerusan store -> load + baca slot vtable) di ELF AArch64 sintetis (non-PIE, nilai slot di berkas)."""
import importlib.util, struct, sys
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)

TEXT, DATA = 0x401000, 0x402000
def adrp(rd, pc, tgt):
    imm = ((tgt & ~0xFFF) - (pc & ~0xFFF)) >> 12
    return 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7FFFF) << 5) | rd
def add(rd, rn, imm): return 0x91000000 | (imm << 10) | (rn << 5) | rd
def stx(rt_, rn, off): return 0xF9000000 | ((off // 8) << 10) | (rn << 5) | rt_
def ldx(rt_, rn, off): return 0xF9400000 | ((off // 8) << 10) | (rn << 5) | rt_
def blr(rn): return 0xD63F0000 | (rn << 5)
def movx(rd, rm): return 0xAA0003E0 | (rm << 16) | rd
def bl(pc, tgt): return 0x94000000 | (((tgt - pc) >> 2) & 0x3FFFFFF)
RET, PRO = 0xD65F03C0, 0xA9BF7BFD

def build(funcs):
    """funcs: {va: [kata]} -> ELF64 AArch64 non-PIE; data: vtable di DATA (slot 0 / 8 / 16 = F1 / F2 / F3)."""
    text = bytearray(0x400)
    for va, ws in funcs.items():
        for i, w in enumerate(ws): struct.pack_into("<I", text, va - TEXT + 4 * i, w)
    data = struct.pack("<3Q", F1, F2, F3) + b"\0" * 0xE8
    ph = lambda fl, off, va, sz: struct.pack("<IIQQQQQQ", 1, fl, off, va, va, sz, sz, 0x1000)
    shstr = b"\0.text\0.data\0.shstrtab\0"
    body = bytearray(0x1000) + text + bytearray(0x1000 - len(text)) + data
    shoff = len(body) + len(shstr)
    sh = lambda nm, ty, fl, va, off, sz: struct.pack("<IIQQQQIIQQ", nm, ty, fl, va, off, sz, 0, 0, 8, 0)
    sec = sh(0, 0, 0, 0, 0, 0) + sh(1, 1, 6, TEXT, 0x1000, len(text)) + sh(7, 1, 3, DATA, 0x2000, len(data)) + sh(13, 3, 0, 0, len(body), len(shstr))
    eh = b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\0" * 8 + struct.pack("<HHIQQQIHHHHHH", 2, 183, 1, TEXT, 64, shoff, 0, 64, 56, 2, 64, 4, 3)
    ph_ = ph(5, 0x1000, TEXT, len(text)) + ph(6, 0x2000, DATA, len(data))
    out = bytearray(eh + ph_); out += b"\0" * (0x1000 - len(out)); out += text + bytearray(0x1000 - len(text)) + data + shstr + sec
    return bytes(out)

F1, F2, F3 = 0x401300, 0x401340, 0x401380
POS1, POS2, NEG_A, NEG_B, NEG_C, NEG_D = 0x401000, 0x401040, 0x401080, 0x4010C0, 0x401100, 0x401140
def vt(base, reg, extra=0):                                                 # adrp + add reg -> &vtable (+ extra); adrp ada di indeks 1
    return [adrp(reg, base + 4, DATA), add(reg, reg, extra)]
funcs = {
    POS1: [PRO] + vt(POS1, 10) + [stx(10, 0, 0), ldx(8, 0, 0), ldx(9, 8, 8), blr(9), RET],                                  # slot 8 -> F2
    POS2: [PRO] + vt(POS2, 10, 8) + [stx(10, 0, 0), ldx(8, 0, 0), ldx(8, 8, 8), blr(8), RET],                              # vptr = vtable+8, [vptr+8] -> F3 (register sama)
    NEG_A: [PRO] + vt(NEG_A, 10) + [stx(10, 0, 0), movx(0, 1), ldx(8, 0, 0), ldx(9, 8, 16), blr(9), RET],                  # x0 diganti: tak boleh
    NEG_B: [PRO] + vt(NEG_B, 10) + [stx(10, 0, 0), bl(NEG_B + 16, F1), ldx(8, 0, 0), ldx(9, 8, 16), blr(9), RET],           # setelah BL: tak boleh
    NEG_C: [PRO, ldx(8, 0, 0), ldx(9, 8, 16), blr(9), RET],                                                                # vptr tak diketahui
    NEG_D: [PRO] + vt(NEG_D, 8) + [ldx(8, 0, 0), ldx(9, 8, 16), blr(9), RET],                                              # x8 sempat = &vtable lalu ditimpa LDR: nilai ADRP lama tak boleh dipakai
    F1: [RET], F2: [RET], F3: [RET],
}
d = build(funcs)
bad = 0
def chk(name, ok):
    global bad
    print(("ok   " if ok else "BEDA ") + name); bad += not ok
rec = []; orig = rt._arm_indirect
def hook(ctx, pc, val, arm32, kind):
    rec.append((pc, val)); return orig(ctx, pc, val, arm32, kind)
rt._arm_indirect = hook
info = rt._relab_multi(d, len(d))[0]
chk("layout dan analisis berjalan", info is not None)
got = {}
for pc, val in rec:
    got.setdefault(pc & ~0x3F, set()).add(val)
chk("POS1: store vptr -> load -> slot vtable -> BLR = F2", got.get(POS1) == {F2})
chk("POS2: vptr + offset, register sama (ldr x8,[x8,#8]) -> F3", got.get(POS2) == {F3})
chk("NEG_A: register dasar ditimpa -> tidak diselesaikan", NEG_A not in got)
chk("NEG_B: BL antara store dan load -> tidak diselesaikan", NEG_B not in got)
chk("NEG_C: vptr tak diketahui -> tidak diselesaikan", NEG_C not in got)
chk("NEG_D: ADRP lama tidak bocor setelah LDR menimpa -> tidak diselesaikan", NEG_D not in got)
import random
rnd = random.Random(3); exc = 0
for _ in range(300):
    b = bytearray(d)
    for _k in range(rnd.randint(1, 40)): b[rnd.randrange(0x1000, 0x1200)] = rnd.getrandbits(8)
    try: rt._relab_multi(bytes(b), len(b))
    except Exception as e:
        exc += 1; print("GALAT", repr(e))
chk("fuzz 300 ELF rusak tanpa galat", exc == 0)
sys.exit(1 if bad else 0)
