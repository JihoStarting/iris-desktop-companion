"""Uji perbaikan v99.58 pada _a64_dis (tanpa capstone). Pakai: python test_a64_v9958.py"""
import importlib.util, sys
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)
PC = 0x400000
V = [  # (kata, teks yang diharapkan "mnemonik operand"; None = .word)
    (0x38c0c8fd, "ldtrsb w29, [x7, #0xc]"), (0xb8579b0f, "ldtr w15, [x24, #-0x87]"), (0xb80599e9, "sttr w9, [x15, #0x59]"),
    (0x7883fb1e, "ldtrsh x30, [x24, #0x3f]"), (0x380208a9, "sttrb w9, [x5, #0x20]"), (0xb89ed8b9, "ldtrsw x25, [x5, #-0x13]"),
    (0x7844082b, "ldtrh w11, [x1, #0x40]"), (0x780dabba, "sttrh w26, [x29, #0xda]"),
    (0x7c081bb7, None), (0x7c5c483d, None),                                   # V=1 nonprivilegiado tak ada
    (0x2b20ed94, "adds w20, w12, w0, sxtx #3"), (0x0b3fe940, "add w0, w10, wzr, sxtx #2"), (0x4b2fe095, "sub w21, w4, w15, sxtx"),
    (0x6b2c635f, "cmp w26, w12, uxtx"), (0x2b2ef2ff, "cmn w23, w14, sxtx #4"),
    (0xa8b3b3de, None), (0xa8ef8120, None), (0xac690e43, None), (0x69eeec3b, None),   # pasangan: writeback Rn==Rt, Rt==Rt2
    (0x785f8eb5, None), (0x384eddce, None), (0x78d85d8c, None),                        # imm9 writeback Rn==Rt
    (0xc87f0240, None),                                                                 # ldxp Rt==Rt2
]
bad = 0
for w, exp in V:
    m, o, _ = rt._a64_dis(w, PC)
    got = None if m == ".word" else (m + " " + o).strip()
    if got != exp:
        bad += 1; print("BEDA %08x: dapat %r, harap %r" % (w, got, exp))
# kata sah tetap sah (tanpa writeback konflik / Rn == sp)
OK = [(0xb85544ca, "ldr w10, [x6], #-0xac"), (0xa9bf7bfd, "stp x29, x30, [sp, #-0x10]!"), (0xa8c17bfd, "ldp x29, x30, [sp], #0x10"),
      (0xf9400000, "ldr x0, [x0]"), (0xf8408c01, "ldr x1, [x0, #8]!")]
for w, exp in OK:
    m, o, _ = rt._a64_dis(w, PC); got = (m + " " + o).strip()
    if got != exp: bad += 1; print("BEDA %08x: dapat %r, harap %r" % (w, got, exp))
print("a64 v99.58: %d cek, %d beda" % (len(V) + len(OK), bad)); sys.exit(1 if bad else 0)
