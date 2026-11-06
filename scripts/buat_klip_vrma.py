# by: KangJiho
"""Membuat 4 klip VRMA kecil (hanya tulang punggung, leher, kepala; tanpa lengan) ke assets/animations/ + clips.json.
Hanya pustaka standar Python. Jalankan dari folder proyek (induk scripts/):  python scripts/buat_klip_vrma.py
Klip dibuat sendiri oleh skrip ini (tidak ada aset pihak lain). Gerakannya kecil dan konservatif; ubah angka AMP di CLIPS kalau kurang/terlalu terlihat."""
import json, math, struct
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "animations"   # scripts/ -> folder proyek -> assets/animations
FPS = 30
BONES = ["hips", "spine", "chest", "neck", "head"]            # rantai induk -> anak
REST_T = {"hips": [0, 1.0, 0], "spine": [0, 0.1, 0], "chest": [0, 0.15, 0], "neck": [0, 0.2, 0], "head": [0, 0.1, 0]}


def sstep(a, b, x):                                           # smoothstep a->b
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def env(u):                                                   # masuk-tahan-keluar, kecepatan nol di ujung
    return sstep(0.0, 0.3, u) * sstep(1.0, 0.7, u)


# nama: (durasi detik, {tulang: fungsi(u) -> (rx, ry, rz) radian}, emosi dasar pemicu, pengaturan masuk/keluar)
CLIPS = {
    "angguk": (1.5, {
        "head": lambda u: (0.22 * math.sin(2 * math.pi * u) ** 2, 0, 0),
        "neck": lambda u: (0.08 * math.sin(2 * math.pi * u) ** 2, 0, 0)}, ["happy"], (0.35, 0.45)),
    "geleng": (1.7, {
        "head": lambda u: (0, 0.30 * math.sin(3 * math.pi * u) * math.sin(math.pi * u), 0),
        "neck": lambda u: (0, 0.10 * math.sin(3 * math.pi * u) * math.sin(math.pi * u), 0)}, ["angry"], (0.35, 0.45)),
    "miring": (2.2, {
        "head": lambda u: (0.04 * env(u), 0, 0.22 * env(u)),
        "neck": lambda u: (0, 0, 0.08 * env(u))}, ["surprised", "shy"], (0.4, 0.5)),
    "tunduk": (2.6, {
        "head": lambda u: (0.26 * env(u), 0, 0),
        "chest": lambda u: (0.05 * env(u), 0, 0),
        "spine": lambda u: (0.04 * env(u), 0, 0)}, ["sad"], (0.5, 0.7)),
}


def quat(rx, ry, rz):                                         # urutan XYZ, sudut kecil
    cx, sx, cy, sy, cz, sz = math.cos(rx / 2), math.sin(rx / 2), math.cos(ry / 2), math.sin(ry / 2), math.cos(rz / 2), math.sin(rz / 2)
    return (sx * cy * cz + cx * sy * sz, cx * sy * cz - sx * cy * sz, cx * cy * sz + sx * sy * cz, cx * cy * cz - sx * sy * sz)


def build(dur, tracks) -> bytes:
    n = int(round(dur * FPS)) + 1
    times = [min(dur, i / FPS) for i in range(n)]
    blob = bytearray(); views = []; accs = []; samplers = []; channels = []

    def add(data: bytes, comp_count: int, typ: str, extra=None) -> int:
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}); blob.extend(data)
        a = {"bufferView": len(views) - 1, "componentType": 5126, "count": comp_count, "type": typ}
        if extra: a.update(extra)
        accs.append(a); return len(accs) - 1

    t_acc = add(struct.pack(f"<{n}f", *times), n, "SCALAR", {"min": [times[0]], "max": [times[-1]]})
    for bone, fn in tracks.items():
        qs = []
        for t in times:
            qs += quat(*fn(t / dur))
        q_acc = add(struct.pack(f"<{n * 4}f", *qs), n, "VEC4")
        samplers.append({"input": t_acc, "output": q_acc, "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": BONES.index(bone), "path": "rotation"}})

    nodes = []
    for i, b in enumerate(BONES):
        nd = {"name": b, "translation": REST_T[b]}
        if i + 1 < len(BONES): nd["children"] = [i + 1]
        nodes.append(nd)
    doc = {"asset": {"version": "2.0", "generator": "buat_klip_vrma.py"},
           "extensionsUsed": ["VRMC_vrm_animation"],
           "extensions": {"VRMC_vrm_animation": {"specVersion": "1.0",
                          "humanoid": {"humanBones": {b: {"node": i} for i, b in enumerate(BONES)}}}},
           "scene": 0, "scenes": [{"nodes": [0]}], "nodes": nodes,
           "animations": [{"channels": channels, "samplers": samplers}],
           "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(blob)}]}
    js = json.dumps(doc, separators=(",", ":")).encode("utf-8"); js += b" " * (-len(js) % 4)
    blob += b"\0" * (-len(blob) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(blob), b"BIN\0") + bytes(blob))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = {}
    for name, (dur, tracks, emo, (fi, fo)) in CLIPS.items():
        (OUT / f"{name}.vrma").write_bytes(build(dur, tracks))
        cfg[name] = {"file": f"{name}.vrma", "emo": emo, "big": False, "speed": 1, "fi": fi, "fo": fo}
    (OUT / "clips.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    print("ditulis:", ", ".join(cfg), "->", OUT)


if __name__ == "__main__":
    main()
