"""test_a64_neon.py (v99.59 + skalar v99.60, dot / SHA512 v99.61): disassembler AArch64 bawaan, Advanced SIMD / AES / SHA / ld-st struktur.
Vektor di bawah ditulis tangan dari ARM ARM; BELUM dibandingkan dengan capstone (jalankan test_a64_vs_capstone.py di PC yang punya capstone)."""
import importlib.util, random, sys
from pathlib import Path
sp = importlib.util.spec_from_file_location("rt", Path(__file__).parent / "rea_triage.py")
rt = importlib.util.module_from_spec(sp); sys.modules["rt"] = rt; sp.loader.exec_module(rt)
V = {
 0x4EA11C20: "mov v0.16b, v1.16b", 0x6E221C20: "eor v0.16b, v1.16b, v2.16b", 0x4EA28420: "add v0.4s, v1.4s, v2.4s",
 0x4F000400: "movi v0.4s, #0", 0x4E284820: "aese v0.16b, v1.16b", 0x4E286820: "aesmc v0.16b, v1.16b",
 0x4E285820: "aesd v0.16b, v1.16b", 0x4E287820: "aesimc v0.16b, v1.16b",
 0x4C407000: "ld1 {v0.16b}, [x0]", 0x4C007000: "st1 {v0.16b}, [x0]", 0x4CDF7000: "ld1 {v0.16b}, [x0], #16",
 0x4E040C20: "dup v0.4s, w1", 0x6E024020: "ext v0.16b, v1.16b, v2.16b, #8", 0x4E020020: "tbl v0.16b, {v1.16b}, v2.16b",
 0x4E205820: "cnt v0.16b, v1.16b", 0x4E31B820: "addv b0, v1.16b", 0x6F380420: "ushr v0.4s, v1.4s, #8",
 0x4E083C20: "mov x0, v1.d[0]", 0x4E0C1C20: "mov v0.s[1], w1", 0x6E205820: "mvn v0.16b, v1.16b",
 0x4F00F400: "fmov v0.4s, #2.00000000", 0x0F20A400: "sxtl v0.2d, v0.2s", 0x4E21D400: "fadd v0.4s, v0.4s, v1.4s",
 0x4F801020: "fmla v0.4s, v1.4s, v0.s[0]", 0x0E20C020: "smull v0.8h, v1.8b, v0.8b",
 0x5EF1B820: "addp d0, v1.2d", 0x7E30D820: "faddp s0, v1.2s", 0x5EE28420: "add d0, d1, d2", 0x5E030420: "mov b0, v1.b[1]",
 0x4E829420: "sdot v0.4s, v1.16b, v2.16b", 0x6E829420: "udot v0.4s, v1.16b, v2.16b", 0x4F82E020: "sdot v0.4s, v1.16b, v2.4b[0]",
 0x6E828420: "sqrdmlah v0.4s, v1.4s, v2.4s", 0xCE628020: "sha512h q0, q1, v2.2d", 0xCE628420: "sha512h2 q0, q1, v2.2d",
 0xCE628820: "sha512su1 v0.2d, v1.2d, v2.2d", 0xCE628C20: "rax1 v0.2d, v1.2d, v2.2d", 0xCEC08020: "sha512su0 v0.2d, v1.2d", 0xCE0C0C20: "eor3 v0.16b, v1.16b, v12.16b, v3.16b",
 0xCEC08420: "sm4e v0.4s, v1.4s", 0xCE62C820: "sm4ekey v0.4s, v1.4s, v2.4s", 0xCE62C020: "sm3partw1 v0.4s, v1.4s, v2.4s",
 0xCE62C420: "sm3partw2 v0.4s, v1.4s, v2.4s", 0xCE420C20: "sm3ss1 v0.4s, v1.4s, v2.4s, v3.4s", 0xCE429420: "sm3tt1b v0.4s, v1.4s, v2.s[1]",
 0x5E21D820: "scvtf s0, s1", 0x5F435420: "shl d0, d1, #3", 0x5FA29020: "fmul s0, s1, v2.s[1]",
}
bad = 0
for w, exp in V.items():
    m, o, _ = rt._a64_dis(w, 0x1000)
    got = (m + " " + o).strip()
    if got != exp:
        bad += 1; print("BEDA %08x  got=%r  exp=%r" % (w, got, exp))
rnd = random.Random(7); known = 0; exc = 0
for _ in range(400000):
    w = rnd.getrandbits(32)
    try:
        m = rt._a64_dis(w, 0x1000)[0]
        known += m != ".word"
    except Exception as e:
        exc += 1
        if exc < 5: print("GALAT %08x %r" % (w, e))
print("vektor: %d  beda: %d  fuzz 400000 kata: dikenali %d, galat %d" % (len(V), bad, known, exc))
sys.exit(1 if bad or exc else 0)
