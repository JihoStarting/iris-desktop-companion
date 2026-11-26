# rea_triage bagian 34/47: relab_arm64 (baris asli 14419-15422). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.23 (roadmap v2, Tier A butir 4, tahap 2a: RE Lab AArch64; aditif): decoder AArch64 KECIL (hanya instruksi yang dibutuhkan, bukan disassembler
# penuh) di atas _arm_layout(): BL / B (peta panggilan), ADRP + ADD / ADR / LDR literal (xref string), ADRP + LDR [GOT] (+ BR) (thunk / stub PLT
# ELF), stub __stubs Mach-O, SVC (syscall langsung; MOVZ x8 / x16 diteruskan ke nomor syscall), penemuan fungsi (entry, ekspor, target BL,
# prolog STP x29, x30). Menghasilkan info / ctx dengan kunci yang sama seperti _re_lab, jadi xref_text, ekspor anotasi, funcdiff, dan re_lab_path
# ikut bekerja lewat _relab_multi(). API hashing ARM ada sejak v99.41 (info["api_hashes"]); TIDAK ada CFG / emulasi / stack string untuk ARM (info["cfg"] / info["emu"] tidak ada);
# cfg_text / emu_text / disasm tetap hanya x86 / x64. ARM 32-bit (A32 / Thumb) belum didecode. Statis murni, hanya pustaka standar.
# Batasan: ADRP + ADD dilacak dalam jendela 12 instruksi tanpa analisis aliran (register yang ditimpa di antaranya bisa memberi xref palsu yang
# lalu disaring karena targetnya harus string terbaca); BLR / BR ke register tak diselesaikan; kode PAC (autia / braa) tidak diselesaikan.
# ---------------------------------------------------------------------------
_A64_SYS = {"linux": {117: "ptrace", 221: "execve", 220: "clone", 222: "mmap", 226: "mprotect", 63: "read", 64: "write", 56: "openat", 93: "exit", 281: "execveat", 167: "prctl", 270: "process_vm_writev"},
            "macho": {26: "ptrace", 59: "execve", 202: "sysctl", 5: "open", 197: "mmap", 74: "mprotect", 1: "exit", 340: "proc_info"}}
A64_WINDOW = 12


def _a64_s(v: int, bits: int) -> int:
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


def _a64_entry_stub(d: bytes, L: dict) -> dict:
    off = L.get("entry_off")
    if off is None:
        return {"hex": "", "note": "entry point tidak ada di berkas (dipetakan ke luar data mentah)"}
    b = d[off:off + 16]
    note = ""
    if len(b) >= 8 and (struct.unpack_from("<I", b, 0)[0] & 0xFFFFFF3F) == 0xD503241F:
        note = "diawali BTI (kompilator modern, jalur normal)"
    elif len(b) >= 4 and (struct.unpack_from("<I", b, 0)[0] & 0xFC000000) == 0x14000000:
        note = "langsung B ke rutin lain (CRT / protektor / entry tersembunyi)"
    return {"hex": " ".join("%02X" % x for x in b), "note": note}


def _arm_regions(L: dict, secva: int, n: int) -> list[tuple[int, int, str]]:
    """v99.29: pecah bagian kode [secva, secva + n) menjadi wilayah (awal, akhir, 'a' A32 | 't' Thumb | 'd' data), dalam offset byte.
    Prioritas: simbol pemetaan ELF ($a / $t / $d); tanpa itu: simbol fungsi (bit 0 = Thumb) + entry; tanpa simbol sama sekali: mode entry."""
    th = L.get("thumb") or set()
    marks = sorted(set(L.get("modes") or ()))
    if not marks:
        mk = {(va, "t" if va in th else "a") for va in (L.get("exports") or {})}
        ent = L.get("entry_va")
        if ent:
            mk.add((ent, "t" if ent in th else "a"))
        marks = sorted(mk)
    cur = "a"
    if not marks and L.get("entry_va") in th:
        cur = "t"
    idx = bisect.bisect_right([m[0] for m in marks], secva) - 1
    if idx >= 0:
        cur = marks[idx][1]
    out, lo = [], 0
    for va, kind in marks[idx + 1:]:
        if va >= secva + n:
            break
        if kind != cur:
            if va - secva > lo:
                out.append((lo, va - secva, cur))
            lo, cur = va - secva, kind
    out.append((lo, n, cur))
    fixed = []
    for a, b, k in out:
        if k == "a":
            a += (-(secva + a)) % 4
            b -= (b - a) % 4 if b > a else 0
        elif k == "t":
            a += (secva + a) & 1
        if b - a >= (4 if k == "a" else 2):
            fixed.append((a, b, k))
    return fixed


def _arm_slot(reloc, va_off, d: bytes, va: int, size: int) -> int | None:
    """v99.43: nilai kata `size` byte (4 / 8) di VA `va`: dari tabel relokasi ELF (RELATIVE / ABS) bila ada, kalau tidak dari berkas; None bila tak terbaca."""
    if reloc:
        v = reloc.get(va)
        if v is not None:
            return v & (0xFFFFFFFF if size == 4 else 0xFFFFFFFFFFFFFFFF)
    o = va_off(va)
    if o is None or o + size > len(d):
        return None
    return struct.unpack_from("<Q" if size == 8 else "<I", d, o)[0]


def _arm_lit(ctx: dict, pc: int, lit: int) -> int | None:
    """Literal pool: nilai di alamat `lit` = slot GOT / pointer string / lainnya. Mengembalikan nilai kata itu (None bila tak terbaca)."""
    val = _arm_slot(ctx.get("reloc"), ctx["va_off"], ctx["d"], lit, 4)
    if val is None:
        return None
    if lit in ctx["iat"]:
        ctx["sites"].append((pc, ctx["iat"][lit], "ptr"))
    elif val in ctx["iat"]:
        ctx["sites"].append((pc, ctx["iat"][val], "ptr"))
    elif not ctx["in_code"](val):
        ctx["strrefs"].append((pc, val))
    return val


# v99.42 (roadmap v8, Tier A butir 4, TAHAP 2d-2e-1): BLR / BLX / BX / BR register ARM. Register yang berisi konstanta alamat (ADRP+ADD, ADR, MOVZ+MOVK,
# MOVW+MOVT, LDR literal, LDR dari slot data terisi, MOV register) dilacak dalam jendela kecil; saat dipakai oleh cabang-register, targetnya masuk ke
# `edges` (sama seperti BL) sehingga ikut penemuan fungsi, peta panggilan, dan stub / thunk API. Heuristik: tanpa analisis aliran penuh.
def _arm_indirect(ctx: dict, pc: int, val: int, arm32: bool, kind: str) -> None:
    """Catat target cabang-register yang sudah diketahui. kind 'blr' (panggilan) | 'br' (tail call: hanya bila di luar +-0x400 byte atau thunk, seperti B)."""
    tgt = (val & 0xFFFFFFFE) if arm32 else val
    if tgt in ctx["thunks"]:
        ok = True
    elif ctx["in_code"](tgt):
        ok = kind != "br" or tgt < pc - 0x400 or tgt > pc + 0x400
    else:
        ok = False
    if ok and len(ctx["indirect"]) < 100000:
        ctx["edges"].append((pc, tgt))
        ctx["indirect"].append((pc, tgt))


def _thumb16_writes(h: int) -> tuple:
    """v99.48: register r0-r7 / r8-r12 yang DITULIS instruksi Thumb 16-bit h (untuk membatalkan konstanta yang dilacak). ADDS / SUBS imm, LDR literal, ADR, MOV hi dan BX / BLX ditangani pemanggil."""
    t = h >> 11
    if t in (0, 1, 2, 3, 4):                                  # geser imm, ADD / SUB (reg / imm3), MOVS imm8
        return (h & 7,) if t != 4 else ((h >> 8) & 7,)
    if t in (6, 7):                                           # ADDS / SUBS imm8 (nilai digeser pemanggil)
        return ((h >> 8) & 7,)
    if (h >> 10) == 0x10:                                     # ALU 0x40xx: TST (8), CMP (10), CMN (11) tidak menulis
        return () if ((h >> 6) & 15) in (8, 10, 11) else (h & 7,)
    if (h >> 8) == 0x44:                                      # ADD Rdn, Rm (register tinggi)
        return (((h >> 4) & 8) | (h & 7),)
    top = h >> 12
    if top == 5:                                              # load / store offset register
        return (h & 7,) if ((h >> 9) & 7) in (3, 4, 5, 6, 7) else ()
    if top in (6, 7, 8):                                      # LDR / LDRB / LDRH imm (bit 11 = load)
        return (h & 7,) if h & 0x800 else ()
    if (h & 0xF800) in (0x9800, 0xA800):                      # LDR Rt, [sp, #imm] / ADD Rd, SP, #imm
        return ((h >> 8) & 7,)
    if (h & 0xFF00) in (0xB200, 0xBA00):   # SXTH / SXTB / UXTH / UXTB, REV / REV16 / REVSH
        return (h & 7,)
    if (h & 0xFE00) == 0xBC00:                                # POP {r0-r7 [, pc]}
        return tuple(r for r in range(8) if (h >> r) & 1)
    if (h & 0xF800) == 0xC800:                                # LDMIA Rn!, {list}
        return tuple(r for r in range(8) if (h >> r) & 1) + (((h >> 8) & 7),)
    if (h & 0xF800) == 0xC000:                                # STMIA Rn!, {list}: hanya writeback Rn
        return ((h >> 8) & 7,)
    return ()


def _thumb32_writes(h: int, h2: int):
    """v99.48: register yang DITULIS instruksi Thumb-2 32-bit (h, h2) selain yang ditangani _thumb_scan; None = tidak diketahui (hapus semua)."""
    if (h & 0xFE00) == 0xE800:                                # LDM / STM / LDRD / STRD / TBB / exclusive / POP.W
        return None
    if (h & 0xF800) == 0xF000:                                # imm termodifikasi / biasa, cabang / misc (MRS)
        return ((h2 >> 8) & 15,)
    if (h & 0xFE00) == 0xEA00:                                # data processing register bergeser
        return ((h2 >> 8) & 15,)
    if (h & 0xFE00) == 0xF800:                                # load / store tunggal
        wb = not (h & 0x80) and bool(h2 & 0x800) and bool(h2 & 0x100)
        out = []
        if h & 0x10:
            out.append((h2 >> 12) & 15)
        if wb:
            out.append(h & 15)
        return tuple(out)
    if (h & 0xFE00) == 0xFA00:                                # shift register / extend / perkalian / pembagian
        return ((h2 >> 8) & 15, (h2 >> 12) & 15)
    if (h & 0xFC00) in (0xEC00, 0xFC00):                      # koprosesor / VFP (VMOV Rt, MRC, LDC writeback)
        return ((h2 >> 12) & 15, h & 15)
    return None


def _thumb_scan(code: bytes, va0: int, ctx: dict) -> None:
    """v99.29 [2d-2c-2a]: Thumb / Thumb-2 KECIL (bukan disassembler penuh): BL / BLX / B.W / B, LDR literal (16 + 32-bit), ADR, SVC + MOV r7, PUSH {.., lr}. PC Thumb = alamat + 4."""
    n = len(code) // 2
    hws = struct.unpack("<%dH" % n, code[:n * 2])
    edges, sites, thunks = ctx["edges"], ctx["sites"], ctx["thunks"]
    cv = ctx.setdefault("cv", {})                  # v99.42: reg -> (nilai konstan, indeks halfword)
    ctx.setdefault("indirect", [])
    imm_r7 = None
    j = 0

    def tail(pc, tgt):
        if tgt in thunks or not ctx["in_code"](tgt) or tgt < pc - 0x400 or tgt > pc + 0x400:
            edges.append((pc, tgt))
    while j < n:
        h, pc = hws[j], va0 + j * 2
        if (h >> 11) in (0x1D, 0x1E, 0x1F) and j + 1 < n:                 # instruksi 32-bit
            h2 = hws[j + 1]
            if (h & 0xF800) == 0xF000 and (h2 & 0xC000) in (0x8000, 0xC000) and (h2 & 0x1000 or (h2 & 0xC000) == 0xC000):
                S = (h >> 10) & 1
                i1, i2 = (~((h2 >> 13) ^ S)) & 1, (~((h2 >> 11) ^ S)) & 1
                off = _a64_s((S << 24) | (i1 << 23) | (i2 << 22) | ((h & 0x3FF) << 12) | ((h2 & 0x7FF) << 1), 25)
                if (h2 & 0xD000) == 0x9000:                                  # B.W (T4)
                    tail(pc, pc + 4 + off)
                elif (h2 & 0xC000) == 0xC000:                                # BL (bit12 = 1) / BLX imm (bit12 = 0, target A32)
                    edges.append((pc, (pc + 4 + off) if h2 & 0x1000 else (((pc + 4) & ~3) + off)))
                    for r_ in (0, 1, 2, 3, 12, 14):
                        cv.pop(r_, None)
            elif (h & 0xFF7F) == 0xF85F and (h2 >> 12) != 15:                # LDR.W Rt, [pc, #+-imm12]
                v_ = _arm_lit(ctx, pc, ((pc + 4) & ~3) + ((h2 & 0xFFF) if (h >> 7) & 1 else -(h2 & 0xFFF)))
                if v_ is not None:
                    cv[h2 >> 12] = (v_, j)
            elif (h & 0xFBF0) in (0xF240, 0xF2C0) and not (h2 & 0x8000):     # MOVW / MOVT (Thumb-2)
                rd_ = (h2 >> 8) & 15
                imm_ = ((h & 0xF) << 12) | (((h >> 10) & 1) << 11) | (((h2 >> 12) & 7) << 8) | (h2 & 0xFF)
                if (h & 0xFBF0) == 0xF240:
                    cv[rd_] = (imm_, j)
                else:
                    e_ = cv.get(rd_)
                    if e_ and j - e_[1] <= 12:
                        cv[rd_] = ((imm_ << 16) | (e_[0] & 0xFFFF), j)
                    else:
                        cv.pop(rd_, None)
            elif h == 0xE92D and (h2 & 0x4000):                              # PUSH.W {..., lr}
                ctx["prolog"].append(pc)
            else:                                                            # v99.48: register yang ditulis instruksi lain membatalkan konstantanya
                w_ = _thumb32_writes(h, h2)
                if w_ is None:
                    cv.clear()
                else:
                    for r_ in w_:
                        cv.pop(r_, None)
            j += 2
            continue
        t_ = h >> 11
        if t_ in (6, 7) or (h & 0xFC00) == 0x1C00:                           # v99.48: ADDS / SUBS imm: konstanta ikut bergeser (adr + adds #1 + bx)
            if t_ in (6, 7):
                rd_ = rn_ = (h >> 8) & 7
                imm_, sub_ = h & 0xFF, t_ == 7
            else:
                rd_, rn_, imm_, sub_ = h & 7, (h >> 3) & 7, (h >> 6) & 7, bool(h & 0x200)
            e_ = cv.get(rn_)
            cv.pop(rd_, None)
            if e_:
                cv[rd_] = ((e_[0] - imm_ if sub_ else e_[0] + imm_) & 0xFFFFFFFF, j)
            j += 1
            continue
        if (h & 0xFF00) != 0x4600:                                           # MOV Rd, Rm ditangani cabang di bawah
            for r_ in _thumb16_writes(h):
                cv.pop(r_, None)
        if (h & 0xF800) == 0x4800:                                           # LDR Rt, [pc, #imm8 * 4]
            v_ = _arm_lit(ctx, pc, ((pc + 4) & ~3) + (h & 0xFF) * 4)
            if v_ is not None:
                cv[(h >> 8) & 7] = (v_, j)
        elif (h & 0xF800) == 0xA000:                                         # ADR / ADD Rd, pc, #imm8 * 4
            ctx["strrefs"].append((pc, ((pc + 4) & ~3) + (h & 0xFF) * 4))
            cv[(h >> 8) & 7] = (((pc + 4) & ~3) + (h & 0xFF) * 4, j)
        elif (h & 0xFF87) in (0x4780, 0x4700):                               # BLX Rm / BX Rm (register)
            e_ = cv.get((h >> 3) & 15)
            blx_ = (h & 0xFF87) == 0x4780
            if e_ and j - e_[1] <= 12:
                _arm_indirect(ctx, pc, e_[0], True, "blr" if blx_ else "br")
            if blx_:
                for r_ in (0, 1, 2, 3, 12, 14):
                    cv.pop(r_, None)
            else:
                cv.clear()
        elif (h & 0xFF00) == 0x4600:                                         # MOV Rd, Rm (register tinggi)
            e_ = cv.get((h >> 3) & 15)
            rd_ = ((h >> 4) & 8) | (h & 7)
            if e_:
                cv[rd_] = (e_[0], j)
            else:
                cv.pop(rd_, None)
        elif (h & 0xF800) == 0xE000:                                         # B (T2)
            tail(pc, pc + 4 + (_a64_s(h & 0x7FF, 11) << 1))
        elif h in (0xDF00, 0xDF80):                                          # SVC
            nm = _A32_SYS.get(imm_r7[0]) if imm_r7 and j - imm_r7[1] <= 8 else None
            ctx["anti"].setdefault("SVC langsung (tanpa libc)", []).append(pc)
            if nm:
                ctx["svc_calls"].setdefault(nm, []).append(pc)
                sites.append((pc, nm, "svc"))
        elif (h & 0xFF00) == 0x2700:                                         # MOVS r7, #imm8
            imm_r7 = (h & 0xFF, j)
        elif (h & 0xFE00) == 0xB400 and h & 0x100:                           # PUSH {..., lr}
            prev = hws[j - 1] if j else 0
            if j == 0 or prev in (0, 0x4770, 0xBF00, 0x46C0) or (prev & 0xFF00) == 0xBD00 or (prev & 0xF800) == 0xE000:
                ctx["prolog"].append(pc)
        j += 1


_A32_SYS = {1: "exit", 2: "fork", 3: "read", 4: "write", 5: "open", 11: "execve", 26: "ptrace", 37: "kill", 90: "mmap", 120: "clone", 125: "mprotect",
            192: "mmap2", 281: "socket", 283: "connect", 322: "openat"}


def _a32_rot(w: int) -> int:
    """Operand-2 immediate A32 (imm8 diputar kanan 2 * rot)."""
    r = ((w >> 8) & 15) * 2
    v = w & 0xFF
    return ((v >> r) | (v << (32 - r))) & 0xFFFFFFFF if r else v


_A32_CALLER = (0, 1, 2, 3, 12, 14)


def _a32_writes(w: int) -> frozenset:
    """v99.49: register r0-r15 yang DITULIS satu kata A32 (cond != 0xF). Superset aman: kelebihan hanya membatalkan konstanta yang dilacak, tidak pernah
    menambah. Cakupan: data processing (TST / TEQ / CMP / CMN tidak menulis), MOVW / MOVT, MSR, perkalian / SWP / exclusive, load / store halfword / dual /
    signed (LDRD menulis Rt dan Rt+1; STR* hanya writeback), LDR / STR word / byte (pra / pasca-indeks writeback), media, LDM / STM (daftar + writeback),
    BL, LDC / STC / VLDM (writeback), MRRC / MRC / VMOV core <- VFP, SVC (r0). Instruksi tak dikenal: {Rd, Rn} (superset)."""
    c = (w >> 25) & 7
    rd, rn = (w >> 12) & 15, (w >> 16) & 15
    wb = not (w >> 24) & 1 or bool((w >> 21) & 1)                    # pasca-indeks atau W: Rn ditulis
    if c == 0 and (w & 0x90) == 0x90:                                # perkalian / swap / exclusive (SH = 0) atau halfword / dual load-store
        sh = (w >> 5) & 3
        if sh == 0:
            out = {rd, rn}
        else:
            out = set()
            if (w >> 20) & 1:
                out.add(rd)
            elif sh == 2:                                            # LDRD
                out.update((rd, (rd + 1) & 15))
            if wb:
                out.add(rn)
        return frozenset(out)
    if c < 2:
        if (w & 0x0FB00000) == 0x03000000:                           # MOVW / MOVT
            return frozenset((rd,))
        if (w & 0x0FB00000) == 0x03200000:                           # MSR imm
            return frozenset()
        if (w & 0x01900000) == 0x01100000:                           # TST / TEQ / CMP / CMN (S = 1): hanya flag
            return frozenset()
        if (w & 0x01900000) == 0x01000000:                           # ruang misc (S = 0): MRS, MSR, CLZ, QADD, SMLAxy, BX / BLX, BKPT ...
            if (w & 0x0FFFFFC0) == 0x012FFF00 or (w & 0x0FB0FFF0) == 0x0120F000:   # BX / BXJ / BLX Rm dan MSR reg: bidang Rd / Rn berisi SBO 0xF, tidak menulis
                return frozenset()
            return frozenset((rd, rn))
        return frozenset((rd,))                                      # data processing biasa
    if c in (2, 3):
        if c == 3 and (w >> 4) & 1:                                  # instruksi media (UBFX, SMLAD, REV, USAD8 ...)
            return frozenset((rd, rn))
        out = set()
        if (w >> 20) & 1:
            out.add(rd)
        if wb:
            out.add(rn)
        return frozenset(out)
    if c == 4:                                                       # LDM / STM
        out = set()
        if (w >> 20) & 1:
            out.update(r for r in range(16) if (w >> r) & 1)
        if (w >> 21) & 1:
            out.add(rn)
        return frozenset(out)
    if c == 5:                                                       # B / BL
        return frozenset(_A32_CALLER) if (w >> 24) & 1 else frozenset()
    if c == 6:                                                       # koprosesor load / store, MCRR / MRRC
        if (w & 0x0FE00000) == 0x0C400000:
            return frozenset((rd, rn))
        return frozenset((rn,)) if wb else frozenset()
    if (w >> 24) & 1:                                                # SVC: nilai kembali di r0
        return frozenset((0,))
    return frozenset((rd,)) if (w & 0x10) and (w >> 20) & 1 else frozenset()   # MRC / VMOV core <- VFP menulis Rt


_A32_IMMOPS = {0: lambda a, b: a & b, 1: lambda a, b: a ^ b, 2: lambda a, b: a - b, 4: lambda a, b: a + b, 12: lambda a, b: a | b, 14: lambda a, b: a & ~b}


def _a32_scan_word(w: int, i: int, pc: int, words, ctx: dict) -> None:
    """v99.28 [2d-2c-1]: satu kata A32 (4 byte, little-endian, bukan Thumb) -> edges / sites / strrefs / thunks / anti / prolog di ctx. PC ARM = alamat + 8."""
    cond = w >> 28
    iat, thunks, edges, sites, strrefs = ctx["iat"], ctx["thunks"], ctx["edges"], ctx["sites"], ctx["strrefs"]
    cv = ctx.get("cv")                                                     # v99.42: reg -> (nilai konstan, indeks kata)
    cv0 = cv                                                               # v99.49: salinan nilai SEBELUM instruksi ini (MOVT / MOV Rd, Rm / ADD imm membaca nilai lama)
    if cv:
        if cond != 15:                                                     # v99.49: semua register yang ditulis membatalkan konstantanya (sebelumnya hanya Rd data processing / LDR)
            cv0 = dict(cv)
            ws_ = _a32_writes(w)
            for r_ in ws_:
                cv.pop(r_, None)
            if 15 in ws_ and cond == 14:                                   # MOV pc / LDM {.., pc} / SUBS pc, lr: aliran berpindah, konstanta tak berlaku lagi
                cv.clear()
        elif (w & 0x0E000000) == 0x0A000000:                               # BLX imm (cond 0xF): panggilan
            for r_ in _A32_CALLER:
                cv.pop(r_, None)
    if (w & 0x0F000000) == 0x0B000000 and cond == 14:                      # BL (hanya AL: kurangi hasil palsu dari data / literal pool di bagian kode)
        edges.append((pc, pc + 8 + (_a64_s(w & 0xFFFFFF, 24) << 2)))
        if cv:
            for r_ in (0, 1, 2, 3, 12, 14):
                cv.pop(r_, None)
    elif (w & 0x0F000000) == 0x0A000000 and cond == 14:                    # B (tail call / thunk)
        tgt = pc + 8 + (_a64_s(w & 0xFFFFFF, 24) << 2)
        if tgt in thunks or not ctx["in_code"](tgt) or tgt < pc - 0x400 or tgt > pc + 0x400:
            edges.append((pc, tgt))
    elif (w & 0x0F7F0000) == 0x051F0000 and cond == 14:                    # LDR Rt, [pc, #+-imm12] (literal pool)
        if (w >> 12) & 15 != 15:
            v_ = _arm_lit(ctx, pc, pc + 8 + (((w & 0xFFF) if (w >> 23) & 1 else -(w & 0xFFF))))
            if v_ is not None and cv is not None:
                cv[(w >> 12) & 15] = (v_, i)
    elif (w & 0xFFFFF000) == 0xE28FC000 and i + 2 < len(words):           # stub PLT ELF: add ip,pc,#a ; add ip,ip,#b ; ldr pc,[ip,#c]!
        w2, w3 = words[i + 1], words[i + 2]
        if (w2 & 0xFFFFF000) == 0xE28CC000 and (w3 & 0xFFFFF000) == 0xE5BCF000:
            slot = pc + 8 + _a32_rot(w) + _a32_rot(w2) + (w3 & 0xFFF)
            if slot in iat:
                thunks[pc] = iat[slot]
    elif w in (0xEF000000, 0xEF000080):                                     # SVC #0 (EABI) / SVC #0x80 (Mach-O); data string tidak ikut
        e = ctx["imm_r7"]
        nm = _A32_SYS.get(e[0]) if e and i - e[1] <= 8 else None
        ctx["anti"].setdefault("SVC langsung (tanpa libc)", []).append(pc)
        if nm:
            ctx["svc_calls"].setdefault(nm, []).append(pc)
            sites.append((pc, nm, "svc"))
    elif (w & 0x0FFFF000) == 0x03A07000 and not (w & 0xF00):               # MOV r7, #imm8 (nomor syscall EABI)
        ctx["imm_r7"] = (w & 0xFF, i)
    if cv is not None and cond == 14:                                      # v99.42: konstanta register + BLX / BX register
        if (w & 0x0FF00000) == 0x03000000:                                  # MOVW
            cv[(w >> 12) & 15] = (((w >> 4) & 0xF000) | (w & 0xFFF), i)
        elif (w & 0x0FF00000) == 0x03400000:                                # MOVT
            rd_ = (w >> 12) & 15
            e_ = cv0.get(rd_)
            if e_ and i - e_[1] <= 8:
                cv[rd_] = (((((w >> 4) & 0xF000) | (w & 0xFFF)) << 16) | (e_[0] & 0xFFFF), i)
        elif (w & 0x0FFF0000) == 0x028F0000:                                # ADD Rd, pc, #imm (ADR)
            cv[(w >> 12) & 15] = ((pc + 8 + _a32_rot(w)) & 0xFFFFFFFF, i)
        elif (w & 0x0FFF0000) == 0x024F0000 and (w >> 12) & 15 != 15:       # v99.50: SUB Rd, pc, #imm (ADR mundur)
            cv[(w >> 12) & 15] = ((pc + 8 - _a32_rot(w)) & 0xFFFFFFFF, i)
        elif (w & 0x0FEF0000) == 0x03A00000 and (w >> 12) & 15 != 15:       # v99.50: MOV / MVN Rd, #imm (alamat rendah non-PIE; rotasi imm8 sudah termasuk)
            cv[(w >> 12) & 15] = ((~_a32_rot(w) if w & 0x00400000 else _a32_rot(w)) & 0xFFFFFFFF, i)
        elif (w & 0x0FFF0FF0) == 0x01A00000:                                # MOV Rd, Rm
            e_ = cv0.get(w & 15)
            if e_ and (w >> 12) & 15 != 15:
                cv[(w >> 12) & 15] = (e_[0], i)
        elif (w & 0x0E000000) == 0x02000000 and ((w >> 21) & 15) in _A32_IMMOPS and (w >> 12) & 15 != 15 and cv0.get((w >> 16) & 15):
            e_ = cv0[(w >> 16) & 15]                                        # v99.49: ADD / SUB / ORR / BIC / EOR / AND #imm pada register berkonstanta menggeser nilainya (adr + orr #1 + bx)
            if i - e_[1] <= A64_WINDOW:
                cv[(w >> 12) & 15] = (_A32_IMMOPS[(w >> 21) & 15](e_[0], _a32_rot(w)) & 0xFFFFFFFF, i)
        elif (w & 0x0FFFFFD0) == 0x012FFF10 and (w & 15) != 14:             # BX Rm / BLX Rm (register; BX lr = kembali)
            e_ = cv0.get(w & 15)
            blx_ = bool(w & 0x20)
            if e_ and i - e_[1] <= A64_WINDOW:
                _arm_indirect(ctx, pc, e_[0], True, "blr" if blx_ else "br")
            if blx_:
                for r_ in (0, 1, 2, 3, 12, 14):
                    cv.pop(r_, None)
            else:
                cv.clear()
    if (w & 0xFFFF4000) == 0xE92D4000:                                      # PUSH {..., lr}
        prev = words[i - 1] if i else 0
        if i == 0 or prev in (0, 0xE320F000, 0xE1A00000, 0xE12FFF1E, 0xE49DF004) or (prev & 0x0F000000) == 0x0A000000 or (prev & 0xFFFF8000) == 0xE8BD8000:
            ctx["prolog"].append(pc)


# v99.41 (roadmap v7, Tier A butir 4, TAHAP 2d-2d-1): API hashing ARM / ARM64. Hash 32-bit dari nama API dicari di (a) kata literal sejajar 4-byte
# di bagian kode (literal pool A32 / Thumb / AArch64), dan (b) imediat yang dibangun lewat pasangan MOVW + MOVT (A32, Thumb-2) atau MOVZ + MOVK
# (AArch64, kata 32-bit). Algoritma: ror13 (block_api / fungsi-saja, Windows ARM), djb2 (= hash GNU / dl_new_hash), djb2-xor, sdbm, FNV-1 / FNV-1a,
# ELF SysV, CRC32. Nama: API Windows (dari tabel ror13 x86), libc / Linux / Android, Apple / iOS. Statis murni.
_ARM_HASH_POSIX = (
    "dlopen dlsym dlclose dladdr mmap munmap mprotect mremap madvise mlock execve execv execvp fork vfork clone ptrace prctl socket connect bind listen "
    "accept accept4 send recv sendto recvfrom sendmsg recvmsg shutdown close read write open openat unlink unlinkat rename chmod chown kill getpid getppid "
    "getuid geteuid setuid setgid system popen pclose fopen fread fwrite fclose fgets fputs malloc calloc realloc free memcpy memmove memset memcmp memchr "
    "strcpy strncpy strcat strlen strcmp strncmp strstr strchr strdup sprintf snprintf sscanf atoi getaddrinfo freeaddrinfo gethostbyname gethostname "
    "inet_addr inet_pton inet_ntoa htons ntohs setsockopt getsockopt getsockname select poll epoll_create epoll_wait pthread_create pthread_join "
    "nanosleep sleep usleep gettimeofday clock_gettime time uname getenv setenv putenv memfd_create syscall __system_property_get dup dup2 dup3 pipe "
    "waitpid wait4 ioctl access stat fstat lstat opendir readdir closedir remove mkdir rmdir chdir getcwd readlink symlink link truncate ftruncate "
    "mincore sysconf getrlimit setrlimit signal sigaction raise abort exit _exit atexit __android_log_print __cxa_atexit __stack_chk_fail "
    "JNI_OnLoad dl_iterate_phdr getauxval sched_yield sysinfo fcntl flock fsync lseek mkstemp tmpfile setuid seteuid chroot mount umount2 insmod "
    "objc_msgSend objc_getClass objc_lookUpClass sel_registerName class_getInstanceMethod method_exchangeImplementations NSClassFromString "
    "sysctl sysctlbyname posix_spawn task_for_pid mach_vm_allocate mach_vm_protect mach_vm_write mach_vm_read vm_protect vm_allocate mach_task_self "
    "_dyld_image_count _dyld_get_image_name _dyld_get_image_header dispatch_async dispatch_once SecItemCopyMatching SecItemAdd CFNetworkCopySystemProxySettings "
    "csops proc_pidinfo getpwuid fts_open ptrace_attach isatty tcgetattr"
).split()


def _arm_hash_algos():
    def ror(v, n):
        return ((v >> n) | (v << (32 - n))) & 0xFFFFFFFF

    def h_ror13(b):
        h = 0
        for c in b + b"\0":
            h = (ror(h, 13) + c) & 0xFFFFFFFF
        return h

    def h_djb2(b):
        h = 5381
        for c in b:
            h = (h * 33 + c) & 0xFFFFFFFF
        return h

    def h_djb2x(b):
        h = 5381
        for c in b:
            h = ((h * 33) ^ c) & 0xFFFFFFFF
        return h

    def h_sdbm(b):
        h = 0
        for c in b:
            h = (c + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
        return h

    def h_fnv1a(b):
        h = 0x811C9DC5
        for c in b:
            h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
        return h

    def h_fnv1(b):
        h = 0x811C9DC5
        for c in b:
            h = ((h * 0x01000193) ^ c) & 0xFFFFFFFF
        return h

    def h_elf(b):
        h = 0
        for c in b:
            h = ((h << 4) + c) & 0xFFFFFFFF
            g = h & 0xF0000000
            if g:
                h ^= g >> 24
            h &= ~g & 0xFFFFFFFF
        return h

    def h_crc32(b):
        return zlib.crc32(b) & 0xFFFFFFFF
    return [("ror13", h_ror13), ("djb2 / GNU hash", h_djb2), ("djb2-xor", h_djb2x), ("sdbm", h_sdbm), ("FNV-1a", h_fnv1a), ("FNV-1", h_fnv1),
            ("ELF SysV", h_elf), ("CRC32", h_crc32)]


_ARM_HASH_TAB: dict[int, list[tuple[str, str]]] | None = None


def _arm_hash_table() -> dict[int, list[tuple[str, str]]]:
    """hash 32-bit -> [(algoritma, nama API)]; dibangun sekali (nama Windows diambil dari tabel ror13 x86)."""
    global _ARM_HASH_TAB
    if _ARM_HASH_TAB is not None:
        return _ARM_HASH_TAB
    names = set(_ARM_HASH_POSIX)
    for v in _relab_hash_table().values():
        if v.endswith(" (ror13)"):
            names.add(v[:-8])
    tab: dict[int, list[tuple[str, str]]] = {}
    for algo, fn in _arm_hash_algos():
        for n in sorted(names):
            tab.setdefault(fn(n.encode()), []).append((algo, n))
    # ror13 block_api (modul + fungsi) tetap memakai tabel x86 yang sudah ada
    for h, v in _relab_hash_table().items():
        if v.endswith(" (block_api)"):
            tab.setdefault(h, []).append(("ror13 block_api", v[:-12]))
    _ARM_HASH_TAB = tab
    return tab


def _arm_hash_scan(execs, L: dict, a32: bool, deadline: float) -> list[tuple[int, str, str, str]]:
    """Cari konstanta API hash ARM / ARM64 di 'execs' (va, off, bytes, nama). Mengembalikan [(va, algo, nama, cara)], tanpa saringan validitas."""
    tab = _arm_hash_table()
    hits: list[tuple[int, str, str, str]] = []
    seen: set = set()

    def add(va, val, how):
        for algo, nm in tab.get(val, ()):
            k = (va, algo, nm)
            if k not in seen:
                seen.add(k)
                hits.append((va, algo, nm, how))
    for secva, _o, code, _nm in execs:
        n4 = len(code) // 4
        words = struct.unpack("<%dI" % n4, code[:n4 * 4])
        for i, w in enumerate(words):                      # (a) kata literal sejajar 4-byte
            if w in tab:
                add(secva + i * 4, w, "literal")
            if i & 0x3FFFF == 0x3FFFF and time.monotonic() > deadline:
                return hits
        if a32:
            for lo, hi, kind in _arm_regions(L, secva, len(code)):
                seg = code[lo:hi]
                if kind == "a":                            # (b) A32: MOVW + MOVT
                    ws = struct.unpack("<%dI" % (len(seg) // 4), seg[:len(seg) // 4 * 4])
                    pend: dict[int, tuple[str, int, int]] = {}
                    for i, w in enumerate(ws):
                        if (w >> 28) == 0xF:
                            continue
                        top = w & 0x0FF00000
                        if top in (0x03000000, 0x03400000):
                            rd, imm = (w >> 12) & 15, ((w >> 4) & 0xF000) | (w & 0xFFF)
                            kd = "lo" if top == 0x03000000 else "hi"
                            e = pend.get(rd)
                            if e and e[0] != kd and i - e[2] <= 8:
                                v = (imm << 16 | e[1]) if kd == "hi" else (e[1] << 16 | imm)
                                if v in tab:
                                    add(secva + lo + i * 4, v, "movw+movt")
                                pend.pop(rd, None)
                            else:
                                pend[rd] = (kd, imm, i)
                elif kind == "t":                          # (b) Thumb-2: MOVW + MOVT
                    pend = {}
                    nh = len(seg) // 2
                    hw = struct.unpack("<%dH" % nh, seg[:nh * 2])
                    for i in range(nh - 1):
                        h1, h2 = hw[i], hw[i + 1]
                        if (h1 & 0xFBF0) in (0xF240, 0xF2C0) and not (h2 & 0x8000):
                            rd = (h2 >> 8) & 15
                            imm = ((h1 & 0xF) << 12) | (((h1 >> 10) & 1) << 11) | (((h2 >> 12) & 7) << 8) | (h2 & 0xFF)
                            kd = "lo" if (h1 & 0xFBF0) == 0xF240 else "hi"
                            e = pend.get(rd)
                            if e and e[0] != kd and i - e[2] <= 12:
                                v = (imm << 16 | e[1]) if kd == "hi" else (e[1] << 16 | imm)
                                if v in tab:
                                    add(secva + lo + i * 2, v, "movw+movt (Thumb-2)")
                                pend.pop(rd, None)
                            else:
                                pend[rd] = (kd, imm, i)
                if time.monotonic() > deadline:
                    return hits
        else:                                              # (b) AArch64: MOVZ / MOVK (hw 0 dan 1)
            pend = {}
            for i, w in enumerate(words):
                if (w & 0x7F800000) not in (0x52800000, 0x72800000):
                    continue
                hw_ = (w >> 21) & 3
                if hw_ > 1:
                    continue
                rd, imm, movk = w & 31, (w >> 5) & 0xFFFF, (w & 0x7F800000) == 0x72800000
                e = pend.get(rd)
                if not movk:                               # MOVZ memulai nilai baru
                    pend[rd] = (hw_, imm, i)
                elif e and e[0] != hw_ and i - e[2] <= 6:
                    v = (imm << 16 | e[1]) if hw_ == 1 else (e[1] << 16 | imm)
                    if v in tab:
                        add(secva + i * 4, v, "movz+movk")
                    pend.pop(rd, None)
                if i & 0x3FFFF == 0x3FFFF and time.monotonic() > deadline:
                    return hits
    return hits


def _arm_hash_filter(hits) -> list[tuple[int, str, str, str]]:
    """Saring hasil mentah: satu algoritma dengan >= 3 nama API berbeda, atau >= 2 nama berbeda dalam jarak 0x200 byte (hash 32-bit acak bisa cocok kebetulan)."""
    by: dict[str, list] = {}
    for h in hits:
        by.setdefault(h[1], []).append(h)
    keep: list[tuple[int, str, str, str]] = []
    for algo, hs in by.items():
        names = {h[2] for h in hs}
        hs.sort()
        ok = len(names) >= 3
        near: set[int] = set()
        for i, a in enumerate(hs):
            for b in hs[i + 1:]:
                if b[0] - a[0] > 0x200:
                    break
                if a[2] != b[2]:
                    near.add(a[0])
                    near.add(b[0])
        if ok:
            keep.extend(hs)
        else:
            keep.extend(h for h in hs if h[0] in near)
    keep.sort()
    return keep



def _re_lab_arm64(d: bytes, L: dict, t0: float | None = None) -> tuple[dict | None, dict | None]:
    t0 = time.monotonic() if t0 is None else t0
    base, iat, stubs = L["base"], L["iat"], L.get("stubs") or {}
    fmt = L.get("fmt", "ELF")
    notes: list[str] = []
    execs, budget = [], RELAB_MAX_CODE
    for s in L["xsecs"]:
        n = min(s["rsize"], s["vsize"] or s["rsize"], budget, len(d) - s["rptr"])
        n -= n % 4
        if n <= 0:
            continue
        budget -= n
        execs.append((base + s["va"], s["rptr"], bytes(d[s["rptr"]:s["rptr"] + n]), s["name"]))
    if not execs:
        return None, None
    if budget <= 0:
        notes.append("kode melebihi batas pindai %s; sebagian tidak dianalisis" % _human(RELAB_MAX_CODE))
    ranges = [(va, va + len(c)) for va, _o, c, _n in execs]

    def in_code(va):
        return any(a <= va < b for a, b in ranges)
    thunks: dict[int, str] = dict(stubs)
    sites: list[tuple[int, str, str]] = []
    edges: list[tuple[int, int]] = []
    strrefs: list[tuple[int, int]] = []
    anti: dict[str, list[int]] = {}
    svc_calls: dict[str, list[int]] = {}
    prolog: list[int] = []
    sysmap = _A64_SYS["macho" if fmt == "Mach-O" else "linux"]
    a32 = L.get("arch") == "arm"          # v99.28: ARM 32-bit (A32) memakai _a32_scan_word; Thumb belum
    a32ctx = {"iat": iat, "thunks": thunks, "edges": edges, "sites": sites, "strrefs": strrefs, "anti": anti, "svc_calls": svc_calls, "prolog": prolog,
              "in_code": in_code, "va_off": lambda va: _va_off(L, va), "d": d, "imm_r7": None, "cv": {}, "indirect": [], "reloc": L.get("reloc") or {}}
    stop = False
    arm_regs: list = []
    for secva, _o, code, _nm in execs:
        if stop:
            break
        words = struct.unpack("<%dI" % (len(code) // 4), code)
        if a32:
            for lo, hi, kind in _arm_regions(L, secva, len(code)):
                arm_regs.append((secva + lo, secva + hi, kind))        # v99.30: dipakai _arm_mode_at() untuk CFG
                a32ctx["imm_r7"] = None
                a32ctx["cv"].clear()
                seg = code[lo:hi]
                if kind == "t":
                    _thumb_scan(seg, secva + lo, a32ctx)
                elif kind == "a":
                    ws = struct.unpack("<%dI" % (len(seg) // 4), seg[:len(seg) // 4 * 4])
                    for i, w in enumerate(ws):
                        _a32_scan_word(w, i, secva + lo + i * 4, ws, a32ctx)
                        if i & 0xFFFF == 0xFFFF and time.monotonic() - t0 > RELAB_TIME:
                            break
                if len(edges) > 400000 or time.monotonic() - t0 > RELAB_TIME:
                    if time.monotonic() - t0 > RELAB_TIME:
                        notes.append("waktu analisis habis (%.0f dtk); hasil sebagian" % RELAB_TIME)
                    stop = True
                    break
            continue
        pg: dict[int, tuple[int, int, int]] = {}          # reg -> (nilai, indeks ADRP / ADR, VA ADRP)
        imm_r: dict[int, tuple[int, int]] = {}            # reg -> (nilai MOVZ, indeks)
        cv: dict[int, tuple[int, int]] = {}               # v99.42: reg -> (nilai konstan / alamat, indeks) untuk BLR / BR register
        mem: dict[tuple[int, int], tuple[int, int]] = {}  # v99.64: (reg dasar, offset) -> (nilai, indeks): STR Xt, [Xn, #off] yang nilainya diketahui (penerusan store -> load, mis. vptr objek)
        for i, w in enumerate(words):
            pc = secva + i * 4
            ldr_src = cv.get((w >> 5) & 31) if (w & 0xFFC00000) == 0xF9400000 else None      # v99.64: nilai Rn sebelum Rt (bisa sama dengan Rn) menimpa
            if cv or mem:                                  # tulis ke Rd / Rt membatalkan nilai register itu (MOVK dikecualikan: butuh nilai lama)
                op_ = (w >> 25) & 0xF
                if (op_ in (8, 9, 5, 13) and (w & 0x7F800000) != 0x72800000) or (op_ in (4, 6, 12, 14) and (w >> 22) & 1):
                    cv.pop(w & 31, None)
                    if mem:
                        for k_ in [k_ for k_ in mem if k_[0] == (w & 31)]:
                            del mem[k_]
            if (w & 0x9F000000) == 0x90000000:                                     # ADRP
                imm = _a64_s(((((w >> 5) & 0x7FFFF) << 2) | ((w >> 29) & 3)), 21) << 12
                pg[w & 31] = ((pc & ~0xFFF) + imm, i, pc)
            elif (w & 0x9F000000) == 0x10000000:                                   # ADR
                tgt = pc + _a64_s(((((w >> 5) & 0x7FFFF) << 2) | ((w >> 29) & 3)), 21)
                pg[w & 31] = (tgt, i, pc)
                cv[w & 31] = (tgt, i)
                strrefs.append((pc, tgt))
            elif (w & 0xFF800000) == 0x91000000:                                   # ADD Xd, Xn, #imm
                rn, rd = (w >> 5) & 31, w & 31
                e = pg.get(rn)
                if e and i - e[1] <= A64_WINDOW:
                    imm = ((w >> 10) & 0xFFF) << (12 if (w >> 22) & 1 else 0)
                    tgt = e[0] + imm
                    pg[rd] = (tgt, i, e[2])
                    cv[rd] = (tgt, i)
                    strrefs.append((pc, tgt))
            elif (w & 0xFFC00000) == 0xF9400000:                                   # LDR Xt, [Xn, #imm]
                rn, rt = (w >> 5) & 31, w & 31
                e = pg.get(rn)
                if e and i - e[1] <= A64_WINDOW:
                    tgt = e[0] + ((w >> 10) & 0xFFF) * 8
                    if tgt in iat:
                        nxt = words[i + 1:i + 4]
                        if any(_a64_brk(x)[0] in ("br", "blr") and _a64_brk(x)[1] == rt for x in nxt) and any(_a64_brk(x)[0] == "br" for x in nxt):
                            thunks[e[2]] = iat[tgt]
                            if e[1] >= 1 and (words[e[1] - 1] & 0xFFFFFF3F) == 0xD503241F:
                                thunks[e[2] - 4] = iat[tgt]                      # bti c sebelum adrp
                        else:
                            sites.append((pc, iat[tgt], "ptr"))
                    else:                                                          # v99.42 / v99.43: slot data terisi pointer kode (nilai berkas atau relokasi RELATIVE / ABS)
                        v_ = _arm_slot(L.get("reloc"), a32ctx["va_off"], d, tgt, 8)
                        if v_:
                            cv[rt] = (v_, i)
                    pg.pop(rt, None)
                else:
                    pg.pop(rt, None)                                               # v99.64: LDR ke Rt yang bukan slot ADRP menimpa Rt; nilai ADRP lama tidak boleh dipakai lagi
                off_ = ((w >> 10) & 0xFFF) * 8
                m_ = mem.get((rn, off_))
                if m_ and i - m_[1] <= A64_WINDOW:                                 # v99.64: penerusan store -> load (vptr yang baru disimpan)
                    cv[rt] = (m_[0], i)
                elif ldr_src and i - ldr_src[1] <= A64_WINDOW and (rt not in cv or cv[rt][1] != i):
                    v_ = _arm_slot(L.get("reloc"), a32ctx["va_off"], d, ldr_src[0] + off_, 8)      # v99.64: slot vtable di alamat konstan (vptr + offset)
                    if v_:
                        cv[rt] = (v_, i)
            elif (w & 0xFFC00000) == 0xF9000000:                                   # v99.64: STR Xt, [Xn, #imm]
                rn, rt = (w >> 5) & 31, w & 31
                key_ = (rn, ((w >> 10) & 0xFFF) * 8)
                e = cv.get(rt)
                if e and i - e[1] <= A64_WINDOW and len(mem) < 64:
                    mem[key_] = (e[0], i)
                else:
                    mem.pop(key_, None)
            elif (w & 0xFF000000) == 0x58000000:                                   # LDR Xt, literal
                tgt = pc + (_a64_s((w >> 5) & 0x7FFFF, 19) << 2)
                if tgt in iat:
                    sites.append((pc, iat[tgt], "ptr"))
                else:                                                              # v99.42 / v99.43: literal 64-bit berisi alamat fungsi
                    v_ = _arm_slot(L.get("reloc"), a32ctx["va_off"], d, tgt, 8)
                    if v_:
                        cv[w & 31] = (v_, i)
            elif (w & 0xFC000000) == 0x94000000:                                   # BL
                edges.append((pc, pc + (_a64_s(w & 0x3FFFFFF, 26) << 2)))
                for r_ in range(19):
                    cv.pop(r_, None)
                mem.clear()                                                        # v99.64: panggilan bisa mengubah memori
            elif (w & 0xFC000000) == 0x14000000:                                   # B (tail call / thunk)
                tgt = pc + (_a64_s(w & 0x3FFFFFF, 26) << 2)
                if tgt in thunks or (not in_code(tgt) or (tgt < pc - 0x400 or tgt > pc + 0x400)):
                    edges.append((pc, tgt))
                pg.clear()
                mem.clear()
            elif (w & 0x7F800000) == 0x52800000:                                   # MOVZ Wd / Xd
                if (w >> 21) & 3 == 0:
                    imm_r[w & 31] = ((w >> 5) & 0xFFFF, i)
                cv[w & 31] = (((w >> 5) & 0xFFFF) << (16 * ((w >> 21) & 3)), i)
            elif (w & 0x7F800000) == 0x72800000:                                   # MOVK: melengkapi nilai MOVZ sebelumnya
                e = cv.get(w & 31)
                if e and i - e[1] <= 6:
                    sh_ = 16 * ((w >> 21) & 3)
                    cv[w & 31] = ((e[0] & ~(0xFFFF << sh_)) | (((w >> 5) & 0xFFFF) << sh_), i)
            elif (w & 0xFFE0FFE0) == 0xAA0003E0:                                   # MOV Xd, Xm (ORR Xd, XZR, Xm)
                e = cv.get((w >> 16) & 31)
                if e:
                    cv[w & 31] = (e[0], i)
            elif (w & 0xFFE0001F) == 0xD4000001:                                   # SVC
                num_r = 16 if fmt == "Mach-O" else 8
                e = imm_r.get(num_r)
                nm = sysmap.get(e[0]) if e and i - e[1] <= 8 else None
                key = "SVC langsung (tanpa libc)"
                anti.setdefault(key, []).append(pc)
                if nm:
                    svc_calls.setdefault(nm, []).append(pc)
                    sites.append((pc, nm, "svc"))
            elif _a64_brk(w)[0] in ("ret", "br", "blr"):   # RET / BR / BLR (+ varian PAC)
                kd_, rn_ = _a64_brk(w)
                if kd_ != "ret":
                    e = cv.get(rn_)
                    if e and i - e[1] <= A64_WINDOW:
                        _arm_indirect(a32ctx, pc, e[0], False, kd_)             # v99.42: BLR / BR register dengan konstanta diketahui
                mem.clear()
                if kd_ == "blr":
                    for r_ in range(19):
                        cv.pop(r_, None)
                else:
                    pg.clear()
                    cv.clear()
            if (w & 0xFFC07FFF) == 0xA9807BFD or ((w & 0xFFC07FFF) == 0xA9007BFD and i >= 1 and (words[i - 1] & 0xFF8003FF) == 0xD10003FF):
                j = i - 1 if (w & 0xFFC07FFF) == 0xA9007BFD else i
                prev = words[j - 1] if j else 0
                if j == 0 or prev in (0, 0xD503201F, 0xD65F03C0, 0xD503233F, 0xD503237F, 0xD50323BF) or (prev & 0xFC000000) == 0x14000000 or _a64_brk(prev)[0] in ("ret", "br"):
                    prolog.append(secva + (j - 1 if prev in (0xD503233F, 0xD503237F) else j) * 4)     # v99.27: PACIASP / PACIBSP = awal fungsi sebenarnya
            if len(edges) > 400000:
                break
            if i & 0xFFFF == 0xFFFF and time.monotonic() - t0 > RELAB_TIME:
                notes.append("waktu analisis habis (%.0f dtk); hasil sebagian" % RELAB_TIME)
                stop = True
                break
    if a32:
        arm_regs.sort()
        L["arm_regions"], L["arm_region_lo"] = arm_regs, [r[0] for r in arm_regs]
    callee_edges = []
    for va, tgt in edges:
        if tgt in thunks:
            sites.append((va, thunks[tgt], "thunk"))
        elif in_code(tgt):
            callee_edges.append((va, tgt))
    starts: dict[int, str] = {}
    if L["entry_va"] and in_code(L["entry_va"]):
        starts[L["entry_va"]] = "entry"
    for va in L["exports"]:
        if in_code(va):
            starts.setdefault(va, "ekspor")
    tcount = collections.Counter(t for _v, t in callee_edges)
    for t in tcount:
        starts.setdefault(t, "call")
    for va in prolog[:60000]:
        starts.setdefault(va, "prolog")
    for tva in thunks:
        if in_code(tva):
            starts.setdefault(tva, "thunk")
    fl = sorted(starts)
    ends = {}
    for i, s in enumerate(fl):
        sec_end = next((b for a, b in ranges if a <= s < b), s)
        ends[s] = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)

    def func_of(va):
        i = bisect.bisect_right(fl, va) - 1
        if i < 0:
            return None
        s = fl[i]
        return s if va < ends[s] else None
    F: dict[int, dict] = {}

    def fobj(s):
        if s not in F:
            nm = L["exports"].get(s) or ("start" if starts.get(s) == "entry" else ("thunk_" + thunks[s].split("!")[-1] if s in thunks else "sub_%08X" % s))
            F[s] = {"va": s, "name": nm, "size": ends.get(s, s) - s, "how": starts.get(s, "?"), "callers": 0, "callees": set(), "apis": {}, "strings": [], "anti": set()}
        return F[s]
    for va, tgt in callee_edges:
        cs = func_of(va)
        fobj(tgt)["callers"] += 1
        if cs is not None and cs != tgt:
            fobj(cs)["callees"].add(tgt)
    api_sites: dict[str, list[tuple[int, int]]] = {}
    for va, api, kind in sites:
        fs = func_of(va)
        if fs is not None and fs in thunks and kind != "ptr":
            continue
        if fs is not None:
            F_ = fobj(fs)
            F_["apis"][api] = F_["apis"].get(api, 0) + 1
        api_sites.setdefault(api, []).append((va, fs or 0))
    sref: dict[int, dict] = {}
    seen_budget = 0
    for va, sva in strrefs:
        off = _va_off(L, sva)
        if off is None or off + 8 > len(d) or in_code(sva):
            continue
        seen_budget += 1
        if seen_budget > 40000:
            break
        r = _rd_str(d, off)
        if not r:
            continue
        e = sref.setdefault(sva, {"va": sva, "kind": r[0], "text": r[1][:140], "funcs": set()})
        fs = func_of(va)
        if fs is not None:
            e["funcs"].add(fs)
            if r[1][:140] not in fobj(fs)["strings"] and len(fobj(fs)["strings"]) < 40:
                fobj(fs)["strings"].append(e["text"])
    for key, vas in anti.items():
        for va in vas[:200]:
            fs = func_of(va)
            if fs is not None:
                fobj(fs)["anti"].add(key.split(" (")[0])
    arm_hashes: list[dict] = []                     # v99.41: API hashing ARM / ARM64 (literal + MOVW/MOVT + MOVZ/MOVK)
    try:
        for va, algo, nm, how in _arm_hash_filter(_arm_hash_scan(execs, L, a32, t0 + RELAB_TIME + 4.0))[:40]:
            fs = func_of(va)
            if fs is not None:
                fobj(fs)["anti"].add("API hashing")
            api = nm if algo == "ror13 block_api" else "%s (%s)" % (nm, algo)
            arm_hashes.append({"api": api, "offset": "0x%X" % va, "algo": algo, "how": how})
    except Exception as e:                          # pemindaian hash tidak boleh menjatuhkan RE Lab
        notes.append("pemindaian API hash ARM dilewati: %s" % type(e).__name__)
    ranked = []
    for s, f in F.items():
        tags, sc = _api_tags(list(f["apis"]))
        intr = list(dict.fromkeys(x for x in f["strings"] if _RE_INTR.search(x)))
        sc += min(len(intr), 2) + (2 if len(f["anti"]) >= 2 else len(f["anti"]))
        if "SVC langsung" in " ".join(f["anti"]) and any(a in svc_calls for a in f["apis"]):
            sc += 3
        if sc >= 2:
            ranked.append((sc, s, tags, intr))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    top = []
    for sc, s, tags, intr in ranked[:RELAB_TOP]:
        f = F[s]
        top.append({"va": "0x%X" % s, "name": f["name"], "size": f["size"], "callers": f["callers"], "callees": len(f["callees"]), "score": sc,
                    "tags": tags, "apis": sorted(f["apis"])[:14], "strings": [_clean(x)[:90] for x in list(dict.fromkeys(intr or f["strings"]))[:4]], "anti": sorted(f["anti"])})
    refs = sorted(sref.values(), key=lambda e: (0 if _RE_INTR.search(e["text"]) else 1, -len(e["funcs"]), e["va"]))
    refs_out = []
    for e in refs[:30]:
        if not _RE_INTR.search(e["text"]) and len(refs_out) >= 8:
            break
        refs_out.append({"va": "0x%X" % e["va"], "kind": e["kind"], "tag": _str_tag(e["text"]), "text": _clean(e["text"]),
                         "funcs": ["0x%X" % x for x in sorted(e["funcs"])[:4]]})
    api_top = sorted(((a, len(v)) for a, v in api_sites.items()), key=lambda x: (-x[1], x[0]))
    anti_out = [{"technique": k, "count": len(v), "first": "0x%X" % v[0]} for k, v in anti.items()]
    if L.get("encrypted"):
        notes.append("Mach-O terenkripsi (cryptid != 0): kode yang terbaca mungkin bukan kode asli; dekripsi dulu")
    if L["stripped"]:
        notes.append("tanpa tabel simbol: nama fungsi hanya dari ekspor / stub; sisanya sub_<alamat>")
    arch_label = "%s ARM64 (AArch64)%s" % (fmt, ", tanpa simbol" if L["stripped"] else "")
    if a32:
        arch_label = "%s ARM 32-bit (A32 / Thumb)%s" % (fmt, ", tanpa simbol" if L["stripped"] else "")
        notes.append("ARM 32-bit: A32 + Thumb / Thumb-2 (decoder kecil; mode dari simbol $a / $t / $d atau simbol fungsi); CFG tersedia (v99.30); emulasi mikro A32 (v99.36) dan Thumb / Thumb-2 (v99.37); disasm A32 (v99.38) dan Thumb / Thumb-2 (v99.39) bawaan tanpa capstone")
    if L.get("reloc"):
        if L.get("fmt") == "Mach-O":
            notes.append("%d pointer rebase Mach-O chained fixups dibaca (slot data terisi alamat tujuan)" % len(L["reloc"]))
        else:
            notes.append("%d relokasi RELATIVE / ABS ELF dibaca (slot data PIE terisi nilainya)" % len(L["reloc"]))
    if L.get("n_irel") or L.get("n_irel_skip"):
        notes.append("IRELATIVE (ifunc): %d slot diselesaikan lewat emulasi resolver, %d dilewati (beberapa kandidat / hasil tak diketahui)" % (L.get("n_irel", 0), L.get("n_irel_skip", 0)))
    if L.get("n_symrel"):
        notes.append("%d slot GLOB_DAT / JUMP_SLOT ke simbol lokal termasuk di atas" % L["n_symrel"])
    if L.get("n_relr"):
        notes.append("%d slot DT_RELR (relokasi RELATIVE terkompresi) termasuk di atas" % L["n_relr"])
    if a32ctx["indirect"]:
        notes.append("%d cabang-register (BLR / BLX / BX / BR) diselesaikan dari konstanta (ADRP+ADD, ADR, MOVZ+MOVK, MOVW+MOVT, literal, slot data)" % len(a32ctx["indirect"]))
    info = {
        "arch": arch_label, "image_base": "0x%X" % base, "n_functions": len(fl), "n_api_sites": len(sites), "n_iat": len(iat), "n_thunks": len(thunks),
        "n_strrefs": len(sref), "entry": "0x%X" % L["entry_va"] if L["entry_va"] else "", "entry_stub": _a64_entry_stub(d, L),
        "functions": top, "api_top": api_top[:15], "string_refs": refs_out, "stack_strings": [], "anti": anti_out, "api_hashes": arm_hashes[:12], "ror13_ops": 0, "notes": notes,
    }
    info["n_indirect"] = len(a32ctx["indirect"])        # v99.42: jumlah cabang-register yang targetnya diselesaikan (kunci aditif)
    ctx = {"L": L, "F": F, "sites": api_sites, "sref": sref, "fl": fl, "thunks": thunks, "arch": "arm" if a32 else "arm64"}
    _cfg_enrich(info, ctx, d)         # v99.23 [2b] AArch64 / v99.30 ARM 32-bit: CFG lewat _cfg_func (kunci info["cfg"], aditif)
    _emu_enrich(info, ctx, d)         # v99.25 [2c] AArch64 / v99.36 [2d-2c-2b-2a] ARM 32-bit A32: emulasi mikro lewat _emu_func (kunci info["emu"], aditif)
    return info, ctx


def _relab_arm(d: bytes, t0: float | None = None):
    L = _arm_layout(d)
    if L is None:
        return None, None, "bukan ELF / Mach-O ARM atau tanpa kode yang bisa dianalisis"
    info, ctx = _re_lab_arm64(d, L, t0)
    return info, ctx, "" if ctx else "tanpa bagian kode ARM64 yang bisa dianalisis"


def _relab_multi(d: bytes, size: int):
    """(info, ctx, galat): _relab_any (PE / ELF x86 / x64), lalu AArch64 (ELF / Mach-O) bila itu bukan x86. Jalur x86 / x64 tidak berubah."""
    info, ctx, err = _relab_any(d, size)
    if info is not None or ctx is not None:
        return info, ctx, err
    if d[:4] in (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        try:
            i2, c2, e2 = _relab_arm(d)
        except Exception:
            return info, ctx, err
        if i2 is not None:
            return i2, c2, ""
        if "ARM 32-bit" in e2:
            return info, ctx, e2
    return info, ctx, err


def _relab_elf(d: bytes, t0: float | None = None):
    L = _elf_layout(d)
    if L is None:
        return None, None
    info, ctx = _re_lab(d, None, t0, L=L, arch_label="ELF %s (%d-bit)%s" % ("x86-64" if L["is64"] else "x86", 64 if L["is64"] else 32, ", tanpa .symtab" if L["stripped"] else ""))
    if info is not None and L["stripped"]:
        info["notes"].append("ELF tanpa .symtab: nama fungsi hanya dari ekspor dinamis; sisanya sub_<alamat>")
    return info, ctx


def _relab_any(d: bytes, size: int):
    """(info, ctx, pesan_galat): PE x86 / x64 atau ELF x86 / x86-64."""
    pe = _parse_pe(d, size)
    if pe and not pe.get("broken"):
        info, ctx = _re_lab(d, pe)
        return info, ctx, "" if ctx else "PE bukan x86 / x64 atau tanpa bagian eksekusi"
    if d[:4] == b"\x7fELF":
        info, ctx = _relab_elf(d)
        return info, ctx, "" if ctx else "ELF bukan x86 / x86-64 little-endian, atau tanpa kode yang bisa dianalisis"
    return None, None, "bukan PE / ELF x86 / x64 yang valid"


