"""Gabungkan rea_parts/ kembali menjadi satu berkas: rea_triage_single.py (tanpa loader)."""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
loader = open(os.path.join(here, "rea_triage.py"), encoding="utf-8", newline="").read()
doc = loader.split('from __future__ import annotations', 1)[0]
names = eval(re.search(r"_PART_FILES = (\[.*?\])", loader, re.S).group(1))
out = [doc]
for n in names:
    t = open(os.path.join(here, "rea_parts", n), encoding="utf-8", newline="").read()
    out.append(t.split("\n", 1)[1])
single = "".join(out).replace("hashlib.sha256(_code_bytes()).hexdigest()[:32]", "hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()[:32]")
open(os.path.join(here, "rea_triage_single.py"), "w", encoding="utf-8", newline="").write(single)
print("ditulis rea_triage_single.py", len(single))
