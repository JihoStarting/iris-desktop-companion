# rea_triage bagian 45/47: gamelab_pak_re (baris asli 23247-24041). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ===================================================================================================
# GAMELAB (digabung dari gamelab.py): pak (UnrealPak) | re (ELF/Mach-O ARM) | unity (UnityFS/SerializedFile)
# Dependensi opsional dimuat lazy hanya saat grupnya dipakai: lief+capstone (re), lz4/pillow/texture2ddecoder/UnityPy (unity).
# ===================================================================================================
import argparse
import bisect
import collections
import json
import lzma
import math
import os
import re
import struct
import subprocess
import sys
import uuid
import base64

try:
    import lz4.block as lz4block
except ImportError:
    lz4block = None

lief = None   # dimuat lazy oleh _init_re()
cs = None


def _init_re():
    global lief, cs
    try:
        import lief as _lief
    except ImportError:
        sys.exit("Grup 're' butuh LIEF: pip install lief")
    lief = _lief
    try:
        import capstone as _cs
        cs = _cs
    except ImportError:
        cs = None
    try:
        lief.logging.set_level(lief.logging.LEVEL.ERROR)
    except Exception:
        pass


RE_DOC = '\nre_lab.py - RE Lab untuk ELF dan Mach-O (ARM / ARM64 / Thumb)\n\nDependensi:  pip install lief capstone\n\nSubcommand:\n  triage   ringkasan cepat: format, arsitektur, proteksi, lib, indikator anti-debug/hook\n  sections daftar section/segment + entropi (deteksi packed/encrypted)\n  symbols  daftar simbol (filter --grep, --imports, --exports)\n  strings  string ASCII/UTF-16LE + alamat virtual\n  funcs    penemuan fungsi (simbol + heuristik prolog untuk binary stripped)\n  disasm   disassemble per alamat / simbol (ARM, Thumb, ARM64)\n  xrefs    cross-reference BL/B ke alamat/simbol, dan ref string via ADRP+ADD (ARM64)\n  objc     (Mach-O) class/selector Objective-C dari section __objc_*\n  jni      (ELF) fungsi JNI: JNI_OnLoad dan Java_* + RegisterNatives\n  carve    dump byte dari range alamat virtual ke file\n\nContoh:\n  python re_lab.py triage libgame.so\n  python re_lab.py disasm libgame.so --sym Java_com_x_Native_init --count 40\n  python re_lab.py xrefs  libgame.so --str "license"\n  python re_lab.py funcs  GameApp --slice 0 --limit 50\n'
UNITY_DOC = '\nunity_parser.py - Parser UnityFS bundle + SerializedFile (mandiri, berbasis TypeTree)\n\nDependensi : pip install lz4\nOpsional   : pip install pillow texture2ddecoder   (ekspor PNG + dekode DXT/BC/ETC/ASTC/PVRTC)\n             pip install UnityPy                    (fallback TypeTree untuk file yang TypeTree-nya di-strip)\n\nFitur\n  - Bundle UnityFS (LZ4 / LZ4HC / LZMA / tanpa kompresi), blocks-info di awal atau di akhir\n  - SerializedFile v13-v22+ (header, TypeTree blob, object table, externals, ref types)\n  - Pembaca TypeTree generik -> dict Python (semua class yang TypeTree-nya ada)\n  - Ekstraktor: Texture2D -> PNG, Mesh -> OBJ, AnimationClip -> JSON, TextAsset -> file mentah\n  - Resource eksternal (.resS / StreamingInfo) di dalam bundle maupun sebelah file .assets\n\nPerintah\n  info     FILE                     ringkasan bundle / serialized file\n  ls       FILE [--type T]          daftar object (path_id, class, nama, ukuran)\n  dump     FILE --id PATH_ID        dump TypeTree object sebagai JSON\n  extract  FILE -o DIR [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX]\n  unpack   FILE -o DIR              tulis semua node bundle hasil dekompresi\n\nBatasan (jujur)\n  - Bundle terenkripsi/custom (UnityCN, header dimodifikasi) tidak didukung.\n  - Build rilis sering membuang TypeTree; pakai --fallback (butuh UnityPy) atau\n    cocokkan dengan TypeTree dari tooling lain.\n  - Mesh terkompresi (m_MeshCompression != 0) dan tekstur swizzle konsol belum didukung.\n  - Animasi mecanim di-dump sebagai keyframe mentah + binding (bukan retarget penuh).\n'
PAK_DOC = '\npakbuild.py - Pembuat pak Unreal (Oodle/Zstd + enkripsi AES-256) lewat UnrealPak\n\nSubcommand:\n  gen-key   buat key AES-256 + GUID -> Crypto.json dan Crypto.json.ini.snippet\n  filelist  buat filelist.txt dari folder Saved/Cooked/<Platform>/<Project>\n  build     jalankan UnrealPak: kompres + enkripsi\n  list      daftar isi pak (butuh Crypto.json bila terenkripsi)\n\nContoh:\n  python pakbuild.py gen-key --out Crypto.json\n  python pakbuild.py filelist --cooked D:/P/Saved/Cooked/Windows/MyGame --project MyGame\n  python pakbuild.py build --unrealpak "C:/UE_5.4/Engine/Binaries/Win64/UnrealPak.exe" \\\n        --out MyDLC.pak --format Oodle --keys Crypto.json\n'



# =========================================================================== #
# GRUP: pak (Unreal pak builder)
# =========================================================================== #

CPP_H = r'''#pragma once
#include "CoreMinimal.h"

class FPakKeyLoader
{
public:
    // Daftarkan key AES (base64) lalu mount pak. Mengembalikan true jika berhasil.
    static bool RegisterKeyAndMount(const FGuid& KeyGuid, const FString& Base64Key,
                                    const FString& PakPath, int32 PakOrder = 100);
};
'''

CPP_CPP = r'''#include "PakKeyLoader.h"
#include "Misc/CoreDelegates.h"
#include "Misc/AES.h"
#include "Misc/Base64.h"

bool FPakKeyLoader::RegisterKeyAndMount(const FGuid& KeyGuid, const FString& Base64Key,
                                        const FString& PakPath, int32 PakOrder)
{
    TArray<uint8> KeyBytes;
    if (!FBase64::Decode(Base64Key, KeyBytes) || KeyBytes.Num() != 32)
    {
        UE_LOG(LogTemp, Error, TEXT("Key AES tidak valid (harus 32 byte)."));
        return false;
    }

    FAES::FAESKey Key;
    FMemory::Memcpy(Key.Key, KeyBytes.GetData(), 32);
    FCoreDelegates::GetRegisterEncryptionKeyMulticastDelegate().Broadcast(KeyGuid, Key);

    if (!FCoreDelegates::MountPak.IsBound())
    {
        UE_LOG(LogTemp, Error, TEXT("Delegate MountPak belum terikat."));
        return false;
    }
    return FCoreDelegates::MountPak.Execute(PakPath, PakOrder) != nullptr;
}
'''


def cmd_emitcpp(a):
    os.makedirs(a.out, exist_ok=True)
    for name, txt in (("PakKeyLoader.h", CPP_H), ("PakKeyLoader.cpp", CPP_CPP)):
        with open(os.path.join(a.out, name), "w", newline="\n") as f:
            f.write(txt)
        print(os.path.join(a.out, name))


def cmd_genkey(a):
    key = base64.b64encode(os.urandom(32)).decode()
    guid = str(uuid.uuid4()).upper()
    with open(a.out, "w") as f:
        json.dump({"EncryptionKey": {"Name": a.name, "Guid": guid, "Key": key}}, f, indent=2)
    ini = a.out + ".ini.snippet"
    with open(ini, "w") as f:
        f.write("[/Script/CryptoKeys.CryptoKeysSettings]\n"
                "bEnablePakIndexEncryption=True\nbEnablePakIniEncryption=True\n"
                "bEnablePakUAssetEncryption=True\nbEnablePakFullAssetEncryption=False\n"
                f"bDataCryptoRequired=True\nEncryptionKey={key}\n")
    print(f"Guid: {guid}\nKey tersimpan di {a.out} dan {ini}")
    print("JANGAN commit file key ke repo publik.")


def cmd_filelist(a):
    root = os.path.abspath(a.cooked)
    exts = tuple(e.strip().lower() for e in a.ext.split(",")) if a.ext else None
    n = 0
    with open(a.out, "w") as f:
        for dp, _, files in os.walk(root):
            for fn in sorted(files):
                if exts and not fn.lower().endswith(exts):
                    continue
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                f.write(f'"{full}" "../../../{a.project}/{rel}"\n')
                n += 1
    print(f"{n} file -> {a.out}")


def _exe(a):
    exe = a.unrealpak or os.environ.get("UNREALPAK")
    if not exe:
        sys.exit("Tentukan --unrealpak atau set env UNREALPAK")
    return exe


def _run(cmd):
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    sys.exit(subprocess.call(cmd))


def cmd_build(a):
    cmd = [_exe(a), a.out, f"-create={a.filelist}"]
    if a.format.lower() != "none":
        cmd += ["-compress", f"-compressionformats={a.format}"]
    if not a.no_encrypt:
        if not a.keys:
            sys.exit("Enkripsi butuh --keys Crypto.json (atau pakai --no-encrypt)")
        cmd += [f"-cryptokeys={a.keys}", "-encrypt", "-encryptindex"]
    _run(cmd)


def cmd_list(a):
    cmd = [_exe(a), a.pak, "-List"]
    if a.keys:
        cmd.append(f"-cryptokeys={a.keys}")
    _run(cmd)


def main_pak():
    p = argparse.ArgumentParser(description="Unreal pak builder",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=PAK_DOC)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("gen-key"); s.set_defaults(fn=cmd_genkey)
    s.add_argument("--out", default="Crypto.json"); s.add_argument("--name", default="MyKey")
    s = sp.add_parser("filelist"); s.set_defaults(fn=cmd_filelist)
    s.add_argument("--cooked", required=True); s.add_argument("--project", required=True)
    s.add_argument("--out", default="filelist.txt")
    s.add_argument("--ext", help="filter ekstensi, mis. .uasset,.uexp,.umap,.ubulk")
    s = sp.add_parser("build"); s.set_defaults(fn=cmd_build)
    s.add_argument("--unrealpak"); s.add_argument("--out", required=True)
    s.add_argument("--filelist", default="filelist.txt")
    s.add_argument("--format", default="Oodle", help="Oodle | Zstd | Zlib | LZ4 | none")
    s.add_argument("--keys"); s.add_argument("--no-encrypt", action="store_true")
    s = sp.add_parser("emit-cpp"); s.set_defaults(fn=cmd_emitcpp)
    s.add_argument("--out", default="UnrealLoader")
    s = sp.add_parser("list"); s.set_defaults(fn=cmd_list)
    s.add_argument("pak"); s.add_argument("--unrealpak"); s.add_argument("--keys")
    a = p.parse_args()
    a.fn(a)




# =========================================================================== #
# GRUP: re (ELF / Mach-O ARM)
# =========================================================================== #
# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #
class Target:
    def __init__(self, path, slice_idx=None):
        self.path = path
        with open(path, "rb") as f:
            self.raw = f.read()
        self.fmt = None
        self.bin = None
        self.arch = "other"
        self.thumb_default = False
        self._load(slice_idx)
        self._sym_cache = None

    def _load(self, slice_idx):
        if lief.is_elf(self.path):
            self.fmt = "elf"
            self.bin = lief.ELF.parse(self.path)
            m = str(self.bin.header.machine_type).upper()
            if "AARCH64" in m:
                self.arch = "arm64"
            elif "ARM" in m:
                self.arch = "arm"
        elif lief.is_macho(self.path):
            self.fmt = "macho"
            fat = lief.MachO.parse(self.path)
            bins = list(fat)
            if not bins:
                sys.exit("Mach-O kosong")
            self.slices = bins
            if slice_idx is None:
                slice_idx = 0
                for i, b in enumerate(bins):  # prefer arm64
                    if "ARM64" in str(b.header.cpu_type).upper():
                        slice_idx = i
                        break
            if len(bins) > 1:
                print(f"[i] Fat binary: {len(bins)} slice, pakai slice {slice_idx}",
                      file=sys.stderr)
            self.bin = bins[slice_idx]
            c = str(self.bin.header.cpu_type).upper()
            if "ARM64" in c:
                self.arch = "arm64"
            elif "ARM" in c:
                self.arch = "arm"
            # raw offset slice -> hanya untuk strings; fat offset ditangani LIEF
        else:
            sys.exit("Bukan ELF atau Mach-O")

    # ----- sections -----
    def sections(self):
        out = []
        for s in self.bin.sections:
            if self.fmt == "macho":
                name = f"{s.segment_name},{s.name}"
            else:
                name = s.name
            out.append((name, s.virtual_address, s.offset, s.size, s))
        return out

    def is_exec(self, name, sec):
        if self.fmt == "macho":
            return name.endswith(("__text", "__stubs", "__stub_helper", "__auth_stubs"))
        try:
            return lief.ELF.Section.FLAGS.EXECINSTR in sec.flags_list
        except Exception:
            return name in (".text", ".plt", ".init", ".fini")

    def sec_bytes(self, sec):
        return bytes(sec.content)

    # ----- memory -----
    def read_va(self, va, size):
        try:
            return bytes(self.bin.get_content_from_virtual_address(va, size))
        except Exception:
            return b""

    def va_of_offset(self, off):
        try:
            return self.bin.offset_to_virtual_address(off)
        except Exception:
            return None

    # ----- symbols -----
    def symbols(self):
        """list of dict(name, addr, size, thumb, func, imported, exported)"""
        if self._sym_cache is not None:
            return self._sym_cache
        seen, out = set(), []
        for s in self.bin.symbols:
            name = s.name
            val = s.value
            if not name:
                continue
            thumb = False
            func = True
            imported = exported = False
            if self.fmt == "elf":
                func = str(s.type).upper().endswith("FUNC")
                imported = bool(getattr(s, "imported", False))
                exported = bool(getattr(s, "exported", False))
                if self.arch == "arm" and (val & 1) and func:
                    thumb, val = True, val & ~1
            else:
                imported = val == 0
                exported = bool(getattr(s, "is_external", False)) and val != 0
            key = (name, val)
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(name=name, addr=val, size=getattr(s, "size", 0) or 0,
                            thumb=thumb, func=func, imported=imported, exported=exported))
        self._sym_cache = out
        return out

    def sym_index(self):
        syms = sorted((s for s in self.symbols() if s["addr"] and s["func"]),
                      key=lambda x: x["addr"])
        return syms, [s["addr"] for s in syms]

    def name_at(self, addr):
        syms, addrs = self.sym_index()
        i = bisect.bisect_right(addrs, addr) - 1
        if i >= 0:
            s = syms[i]
            d = addr - s["addr"]
            if d == 0:
                return s["name"]
            if (s["size"] and d < s["size"]) or (not s["size"] and d < 0x400):
                return f"{s['name']}+0x{d:x}"
        return None

    def resolve(self, ref):
        """ref bisa nama simbol atau alamat hex. Return (addr, thumb)"""
        try:
            return int(ref, 0) & ~1 if self.arch == "arm" else int(ref, 0), \
                (self.arch == "arm" and bool(int(ref, 0) & 1))
        except ValueError:
            pass
        for s in self.symbols():
            if s["name"] == ref and s["addr"]:
                return s["addr"], s["thumb"]
        sys.exit(f"Simbol tidak ditemukan: {ref}")

    # ----- capstone -----
    def md(self, thumb=False):
        if cs is None:
            sys.exit("Butuh capstone: pip install capstone")
        if self.arch == "arm64":
            md = cs.Cs(cs.CS_ARCH_ARM64, cs.CS_MODE_ARM)
        elif self.arch == "arm":
            md = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB if thumb else cs.CS_MODE_ARM)
        else:
            sys.exit(f"Arsitektur non-ARM tidak didukung untuk disasm "
                     f"({self.arch})")
        md.detail = False
        return md


# --------------------------------------------------------------------------- #
# Util
# --------------------------------------------------------------------------- #
def entropy(data):
    if not data:
        return 0.0
    c = collections.Counter(data)
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def hexs(n):
    return f"0x{n:x}"


def extract_strings(data, minlen=5, utf16=False):
    if utf16:
        pat = re.compile(rb"(?:[\x20-\x7e]\x00){%d,}" % minlen)
    else:
        pat = re.compile(rb"[\x20-\x7e]{%d,}" % minlen)
    for m in pat.finditer(data):
        txt = m.group().decode("utf-16le" if utf16 else "ascii", "replace")
        yield m.start(), txt


def target_of(insn_text):
    m = re.search(r"#(0x[0-9a-fA-F]+)", insn_text)
    return int(m.group(1), 16) if m else None


def disasm_range(t, addr, size, thumb=False):
    data = t.read_va(addr, size)
    if not data:
        return []
    return list(t.md(thumb).disasm(data, addr))


def exec_sections(t):
    return [(n, va, off, sz, s) for n, va, off, sz, s in t.sections()
            if sz and t.is_exec(n, s)]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
SUSPICIOUS_IMPORTS = {
    "ptrace": "anti-debug", "fork": "anti-debug/child", "prctl": "anti-debug/seccomp",
    "dlopen": "dynamic load", "dlsym": "dynamic resolve", "mprotect": "memory patch",
    "mmap": "memory map", "syscall": "raw syscall", "inotify_add_watch": "file watch",
    "sysctl": "anti-debug (macOS/iOS)", "task_get_exception_ports": "anti-debug (iOS)",
    "dladdr": "hook check", "_dyld_image_count": "dylib enumeration (jailbreak/hook check)",
    "_dyld_get_image_name": "dylib enumeration", "SecTaskCopyValueForEntitlement": "entitlement check",
    "RegisterNatives": "JNI dynamic registration", "__system_property_get": "device check",
}
SUSPICIOUS_STRINGS = [
    "frida", "xposed", "substrate", "cydia", "magisk", "/proc/self/maps",
    "TracerPid", "/system/bin/su", "libhook", "gum-js", "re.frida", "Jailbreak",
    "/Applications/Cydia.app", "/usr/sbin/sshd", "DYLD_INSERT_LIBRARIES",
]


def cmd_triage(t, a):
    b = t.bin
    print(f"File      : {t.path}")
    print(f"Format    : {t.fmt.upper()}   Arch: {t.arch}")
    imports = {s["name"] for s in t.symbols() if s["imported"]}
    flags = []

    if t.fmt == "elf":
        h = b.header
        print(f"Type      : {h.file_type}   Entry: {hexs(h.entrypoint)}")
        print(f"PIE       : {getattr(b, 'is_pie', '?')}   NX: {getattr(b, 'has_nx', '?')}")
        print(f"Stripped  : {b.get_section('.symtab') is None}")
        print(f"Canary    : {'__stack_chk_fail' in imports}")
        try:
            print(f"Needed    : {', '.join(b.libraries)}")
        except Exception:
            pass
        try:
            print(f"Interp    : {b.interpreter}")
        except Exception:
            pass
        has_text_rel = any("TEXTREL" in str(e.tag) for e in b.dynamic_entries)
        if has_text_rel:
            flags.append("TEXTREL (relokasi di code segment)")
    else:
        h = b.header
        print(f"Filetype  : {h.file_type}   Flags: {[str(f).split('.')[-1] for f in h.flags_list]}")
        print(f"PIE       : {getattr(b, 'is_pie', '?')}   NX: {getattr(b, 'has_nx', '?')}")
        print(f"Dylibs    : {', '.join(d.name for d in b.libraries)}")
        print(f"CodeSign  : {b.has_code_signature}")
        if getattr(b, "has_encryption_info", False):
            ei = b.encryption_info
            state = "TERENKRIPSI (FairPlay) - butuh dump terdekripsi" if ei.crypt_id else "tidak terenkripsi"
            print(f"CryptID   : {ei.crypt_id} -> {state}")
            if ei.crypt_id:
                flags.append("Binary FairPlay-encrypted; analisis statis terbatas")
        print(f"Canary    : {'___stack_chk_fail' in imports}")

    # entropi
    print("\nEntropi section (>7.2 = kemungkinan packed/encrypted):")
    for n, va, off, sz, s in t.sections():
        if sz < 256:
            continue
        e = entropy(t.sec_bytes(s))
        mark = "  <-- tinggi" if e > 7.2 else ""
        print(f"  {n:<28} {hexs(va):>12} {sz:>10}  H={e:.2f}{mark}")
        if e > 7.2 and t.is_exec(n, s):
            flags.append(f"Section kode {n} berentropi tinggi (packed/encrypted?)")

    # import mencurigakan
    hits = [(i, SUSPICIOUS_IMPORTS[i.lstrip('_')] if i.lstrip('_') in SUSPICIOUS_IMPORTS
             else SUSPICIOUS_IMPORTS[i]) for i in imports
            if i in SUSPICIOUS_IMPORTS or i.lstrip("_") in SUSPICIOUS_IMPORTS]
    if hits:
        print("\nImport menarik:")
        for n, why in sorted(hits):
            print(f"  {n:<36} {why}")

    # string indikator
    found = collections.defaultdict(list)
    for off, s in extract_strings(t.raw, 4):
        for k in SUSPICIOUS_STRINGS:
            if k.lower() in s.lower():
                found[k].append(s)
    if found:
        print("\nString indikator deteksi root/jailbreak/hook:")
        for k, v in found.items():
            print(f"  {k:<28} x{len(v)}  contoh: {v[0][:60]!r}")

    if t.fmt == "elf":
        jni = [s["name"] for s in t.symbols() if s["name"].startswith("Java_") or s["name"] == "JNI_OnLoad"]
        if jni:
            print(f"\nJNI: {len(jni)} entri (jalankan: jni)")
    if t.fmt == "macho":
        print("\nTip: jalankan 'objc' untuk class/selector Objective-C.")
    if flags:
        print("\nCatatan:")
        for f in flags:
            print(f"  - {f}")


def cmd_sections(t, a):
    print(f"{'NAMA':<30}{'VA':>14}{'OFFSET':>12}{'SIZE':>12}  {'ENT':>5}  X")
    for n, va, off, sz, s in t.sections():
        e = entropy(t.sec_bytes(s)) if sz else 0
        print(f"{n:<30}{hexs(va):>14}{hexs(off):>12}{hexs(sz):>12}  {e:5.2f}  "
              f"{'x' if t.is_exec(n, s) else ''}")
    if t.fmt == "elf":
        print("\nSegments:")
        for sg in t.bin.segments:
            print(f"  {str(sg.type).split('.')[-1]:<14} va={hexs(sg.virtual_address):<12} "
                  f"off={hexs(sg.file_offset):<10} filesz={hexs(sg.physical_size):<10} "
                  f"memsz={hexs(sg.virtual_size):<10} flags={sg.flags}")
    else:
        print("\nSegments:")
        for sg in t.bin.segments:
            print(f"  {sg.name:<14} va={hexs(sg.virtual_address):<12} "
                  f"off={hexs(sg.file_offset):<10} size={hexs(sg.virtual_size)}")


def cmd_symbols(t, a):
    n = 0
    for s in sorted(t.symbols(), key=lambda x: x["addr"]):
        if a.imports and not s["imported"]:
            continue
        if a.exports and not s["exported"]:
            continue
        if a.grep and not re.search(a.grep, s["name"], re.I):
            continue
        tag = "I" if s["imported"] else ("E" if s["exported"] else " ")
        th = "T" if s["thumb"] else " "
        print(f"{hexs(s['addr']):>12} {s['size']:>6} {tag}{th} {s['name']}")
        n += 1
        if a.limit and n >= a.limit:
            break
    print(f"-- {n} simbol", file=sys.stderr)


def cmd_strings(t, a):
    n = 0
    for off, s in extract_strings(t.raw if t.fmt == "elf" else t.raw, a.min, a.utf16):
        if a.grep and not re.search(a.grep, s, re.I):
            continue
        va = t.va_of_offset(off)
        print(f"{hexs(va) if va is not None else '-':>12}  {hexs(off):>10}  {s}")
        n += 1
        if a.limit and n >= a.limit:
            break


def find_prologues(t, sec_name, va, data):
    """Heuristik fungsi pada binary stripped."""
    md = t.md(thumb=False)
    funcs = []
    if t.arch == "arm64":
        prev = None
        for i in md.disasm(data, va):
            op = i.op_str.replace(" ", "")
            if i.mnemonic == "stp" and op.startswith("x29,x30,[sp"):
                funcs.append(i.address)
            elif i.mnemonic == "sub" and op.startswith("sp,sp,#") and prev is None:
                pass
            elif i.mnemonic in ("paciasp", "bti"):
                funcs.append(i.address)
            prev = i
    else:  # ARM32: push {..., lr}
        for i in md.disasm(data, va):
            if i.mnemonic in ("push", "stmdb") and "lr" in i.op_str:
                funcs.append(i.address)
    return funcs


def cmd_funcs(t, a):
    known = {}
    for s in t.symbols():
        if s["func"] and s["addr"] and not s["imported"]:
            known[s["addr"]] = s["name"]
    print(f"[i] {len(known)} fungsi dari simbol", file=sys.stderr)
    guessed = {}
    if a.heuristic or not known:
        for n, va, off, sz, s in exec_sections(t):
            if n.endswith(("stubs", "plt")) or "stub" in n:
                continue
            for f in find_prologues(t, n, va, t.sec_bytes(s)):
                if f not in known:
                    guessed[f] = f"sub_{f:x}"
        print(f"[i] {len(guessed)} kandidat dari heuristik prolog", file=sys.stderr)
    allf = sorted({**known, **guessed}.items())
    for k, (addr, name) in enumerate(allf):
        if a.limit and k >= a.limit:
            break
        print(f"{hexs(addr):>12}  {name}")


def pretty_insn(t, i):
    line = f"{i.mnemonic:<8}{i.op_str}"
    tgt = target_of(f"{i.op_str}")
    if tgt is not None and i.mnemonic in ("bl", "blx", "b", "cbz", "cbnz", "tbz", "tbnz") \
            or (tgt is not None and i.mnemonic.startswith("b")):
        nm = t.name_at(tgt)
        if nm:
            line += f"    ; {nm}"
    return line


def cmd_disasm(t, a):
    if a.sym:
        addr, thumb = t.resolve(a.sym)
    else:
        addr, thumb = t.resolve(a.addr)
    if a.thumb:
        thumb = True
    size = a.size
    if not size:
        size = 4 * a.count
    insns = disasm_range(t, addr, size, thumb)
    if not insns:
        sys.exit("Gagal baca bytes pada alamat itu")
    nm = t.name_at(addr)
    if nm:
        print(f"{nm}:")
    for k, i in enumerate(insns):
        if a.count and not a.size and k >= a.count:
            break
        print(f"  {hexs(i.address):>10}:  {i.bytes.hex():<10}  {pretty_insn(t, i)}")


def build_xref_maps(t):
    """Return (calls: target->[caller], strrefs: addr->[site]) dari semua section exec."""
    calls = collections.defaultdict(list)
    strrefs = collections.defaultdict(list)
    for n, va, off, sz, s in exec_sections(t):
        data = t.sec_bytes(s)
        modes = [False] if t.arch == "arm64" else [False, True]
        for thumb in modes:
            md = t.md(thumb)
            pages = {}
            for i in md.disasm(data, va):
                ops = i.op_str
                tg = target_of(ops)
                if i.mnemonic in ("bl", "blx", "b") and tg is not None:
                    calls[tg].append(i.address)
                if t.arch == "arm64":
                    mm = re.match(r"(x\d+), #(0x[0-9a-f]+)$", ops)
                    if i.mnemonic == "adrp" and mm:
                        pages[mm.group(1)] = int(mm.group(2), 16)
                    elif i.mnemonic == "add":
                        mm = re.match(r"(x\d+), (x\d+), #(0x[0-9a-f]+)$", ops)
                        if mm and mm.group(2) in pages:
                            strrefs[pages[mm.group(2)] + int(mm.group(3), 16)].append(i.address)
                    elif i.mnemonic in ("ldr", "ldrb"):
                        mm = re.match(r"\w+, \[(x\d+), #(0x[0-9a-f]+)\]$", ops)
                        if mm and mm.group(1) in pages:
                            strrefs[pages[mm.group(1)] + int(mm.group(2), 16)].append(i.address)
    return calls, strrefs


def cmd_xrefs(t, a):
    calls, strrefs = build_xref_maps(t)
    if a.str:
        rx = re.compile(a.str, re.I)
        found = 0
        for off, s in extract_strings(t.raw, 4):
            if not rx.search(s):
                continue
            va = t.va_of_offset(off)
            if va is None:
                continue
            refs = strrefs.get(va, [])
            print(f"{hexs(va)}  {s[:80]!r}")
            for r in refs:
                print(f"      <- {hexs(r)}  {t.name_at(r) or ''}")
            found += 1
        if not found:
            print("Tidak ada string cocok")
        elif t.arch != "arm64":
            print("[!] Xref string (ADRP) hanya didukung ARM64", file=sys.stderr)
        return
    addr, _ = t.resolve(a.addr or a.sym)
    callers = calls.get(addr, [])
    print(f"Call/branch ke {hexs(addr)} ({t.name_at(addr) or '?'}): {len(callers)}")
    for c in sorted(callers):
        print(f"  {hexs(c):>10}  dari {t.name_at(c) or '?'}")


def cstr_list(sec):
    return [x.decode("utf-8", "replace") for x in bytes(sec.content).split(b"\x00") if x]


def cmd_objc(t, a):
    if t.fmt != "macho":
        sys.exit("Perintah objc khusus Mach-O")
    for label, name in (("Classes", "__objc_classname"), ("Selectors", "__objc_methname"),
                        ("Method types", "__objc_methtype")):
        sec = t.bin.get_section(name)
        if not sec:
            continue
        items = cstr_list(sec)
        if a.grep:
            items = [x for x in items if re.search(a.grep, x, re.I)]
        if label == "Method types" and not a.types:
            continue
        print(f"== {label} ({len(items)}) ==")
        for x in items[: a.limit or None]:
            print("  " + x)
    if hasattr(t.bin, "objc_metadata") or True:
        try:
            md = t.bin.objc_metadata
            if md:
                print("\n== objc_metadata (LIEF) ==")
                for c in md.classes:
                    print(f"  @interface {c.name}")
                    for m in c.methods:
                        print(f"     {'+' if m.is_static else '-'}[{m.name}]  imp={hexs(m.address)}")
        except Exception:
            pass


def cmd_jni(t, a):
    if t.fmt != "elf":
        sys.exit("Perintah jni khusus ELF")
    syms = [s for s in t.symbols() if s["name"].startswith("Java_") or s["name"] == "JNI_OnLoad"]
    print(f"== Entri JNI statis ({len(syms)}) ==")
    for s in sorted(syms, key=lambda x: x["addr"]):
        print(f"  {hexs(s['addr']):>10}  {s['name']}")
    imports = {s["name"] for s in t.symbols() if s["imported"]}
    print("\nRegisterNatives diimpor:", "RegisterNatives" in imports or "ya (via JNIEnv vtable, offset 0x6B8 pada arm64)")
    print("Petunjuk: pada JNI_OnLoad, cari 'ldr xN, [xM, #0x6b8]' (arm64) / '#0x35c' (arm32) "
          "lalu 'blr' = panggilan RegisterNatives; tabel JNINativeMethod = {name, sig, fnPtr}.")
    rx = re.compile(rb"\(([\[BCDFIJSZL][\w/;\[]*)\)[\[BCDFIJSVZL][\w/;]*")
    sigs = {m.group().decode() for m in rx.finditer(t.raw)}
    if sigs:
        print(f"\nKandidat signature JNI di binary: {len(sigs)}")
        for s in sorted(sigs)[:40]:
            print("  " + s)


def cmd_carve(t, a):
    addr, _ = t.resolve(a.addr)
    data = t.read_va(addr, a.size)
    if not data:
        sys.exit("Gagal baca")
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"{len(data)} byte dari {hexs(addr)} -> {a.out}")


# --------------------------------------------------------------------------- #
def main_re():
    p = argparse.ArgumentParser(description="RE Lab ELF/Mach-O ARM & ARM64",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=RE_DOC)
    p.add_argument("binary")
    p.add_argument("--slice", type=int, default=None, help="indeks slice untuk fat Mach-O")
    sp = p.add_subparsers(dest="cmd", required=True)

    sp.add_parser("triage").set_defaults(fn=cmd_triage)
    sp.add_parser("sections").set_defaults(fn=cmd_sections)

    s = sp.add_parser("symbols"); s.set_defaults(fn=cmd_symbols)
    s.add_argument("--grep"); s.add_argument("--imports", action="store_true")
    s.add_argument("--exports", action="store_true"); s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("strings"); s.set_defaults(fn=cmd_strings)
    s.add_argument("--min", type=int, default=5); s.add_argument("--grep")
    s.add_argument("--utf16", action="store_true"); s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("funcs"); s.set_defaults(fn=cmd_funcs)
    s.add_argument("--heuristic", action="store_true", help="tambah deteksi prolog")
    s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("disasm"); s.set_defaults(fn=cmd_disasm)
    s.add_argument("addr", nargs="?"); s.add_argument("--sym")
    s.add_argument("--count", type=int, default=32); s.add_argument("--size", type=lambda x: int(x, 0), default=0)
    s.add_argument("--thumb", action="store_true")

    s = sp.add_parser("xrefs"); s.set_defaults(fn=cmd_xrefs)
    s.add_argument("addr", nargs="?"); s.add_argument("--sym"); s.add_argument("--str")

    s = sp.add_parser("objc"); s.set_defaults(fn=cmd_objc)
    s.add_argument("--grep"); s.add_argument("--types", action="store_true")
    s.add_argument("--limit", type=int, default=0)

    sp.add_parser("jni").set_defaults(fn=cmd_jni)

    s = sp.add_parser("carve"); s.set_defaults(fn=cmd_carve)
    s.add_argument("addr"); s.add_argument("size", type=lambda x: int(x, 0)); s.add_argument("out")

    a = p.parse_args()
    _init_re()
    t = Target(a.binary, a.slice)
    if a.cmd == "disasm" and not (a.addr or a.sym):
        sys.exit("disasm butuh alamat atau --sym")
    if a.cmd == "xrefs" and not (a.addr or a.sym or a.str):
        sys.exit("xrefs butuh alamat, --sym, atau --str")
    a.fn(t, a)




