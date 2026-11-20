"""approval_policy.py - izin otomatis KHUSUS untuk perintah Hermes yang terbukti hanya MEMBACA (opt-in).

Dipakai server.py (_handle_approval) bila .env berisi AGENT_APPROVAL_AUTO=readonly.
Prinsip: fail-closed. Apa pun yang tidak bisa dibuktikan aman = tetap tampil kartu Izinkan / Tolak seperti biasa.

classify(cmd) -> (True, alasan) hanya jika SELURUH perintah lolos pemeriksaan statis:
  1. Bentuk shell sederhana: kata + operator  |  ||  &&  (dan 2>&1). Ditolak: ; & ` $ ( ) { } < > ~ \\ baris baru di luar kutip.
  2. Setiap segmen salah satu dari:
       - cd <folder>                       (folder harus di bawah AGENT_APPROVAL_AUTO_ROOT, bawaan /workspace)
       - alat baca saja (objdump, strings, file, sha256sum, hexdump, head, tail, grep, cat, ls, ...)
       - python3 -c "<kode>"  atau  python3 << 'EOF' ... EOF   -> kodenya diperiksa lewat AST (lihat _py_ok)
  3. Python: hanya impor dari daftar putih (struct, re, hashlib, pefile, ...), open() hanya mode baca dengan path literal,
     tanpa exec/eval/compile/getattr/__dunder__, tanpa os/subprocess/socket/shutil, tanpa .write/.open/.system/.remove dst.
  4. Semua path harus relatif (tanpa ..) atau di bawah akar sandbox (/workspace) atau folder sementara (/tmp). Menulis HANYA ke /tmp/...,
     dan hanya lewat dd (if/of/bs/skip/count/status), cp (2 path, tanpa opsi), mkdir. Ekspansi $((angka)) diterima; $(...) dan backtick tidak.

Ini mengurangi risiko, bukan menghapusnya: pemeriksaan statis tidak bisa menjamin 100%. Karena itu bawaannya MATI.
Hanya pustaka standar.
"""
from __future__ import annotations

import ast
import os
import re

ROOT = (os.getenv("AGENT_APPROVAL_AUTO_ROOT", "/workspace").strip() or "/workspace").rstrip("/") or "/workspace"
# folder sementara di sandbox: boleh DIBACA, dan satu-satunya tempat yang boleh DITULIS (hanya lewat dd / cp / mkdir dengan bentuk ketat).
SCRATCH = (os.getenv("AGENT_APPROVAL_AUTO_SCRATCH", "/tmp").strip() or "/tmp").rstrip("/") or "/tmp"
_READ_ROOTS = (ROOT, SCRATCH)
MAX_CMD = 12000

# alat yang hanya membaca. Nilai: (flag terlarang, maks argumen posisional atau None)
_SIMPLE = {
    "objdump": (set(), None), "readelf": (set(), None), "nm": (set(), None), "strings": (set(), None),
    "file": ({"-C", "--compile"}, None), "sha256sum": (set(), None), "sha1sum": (set(), None), "md5sum": (set(), None),
    "hexdump": (set(), None), "od": (set(), None), "xxd": ({"-r", "-revert"}, 1),
    "head": (set(), None), "tail": (set(), None), "wc": (set(), None), "ls": (set(), None), "stat": (set(), None),
    "grep": (set(), None), "cut": (set(), None), "tr": (set(), None), "cat": (set(), None),
    "echo": (set(), None), "pwd": (set(), None),
}

_PY_IMPORTS = {"struct", "re", "hashlib", "binascii", "collections", "math", "itertools", "string", "base64",
               "zlib", "lzma", "bz2", "datetime", "json", "textwrap", "functools", "operator", "codecs", "sys", "pefile"}

_BAD_CALLS = {"exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr", "setattr", "delattr",
              "LZMAFile", "BZ2File", "input", "breakpoint", "help", "memoryview", "classmethod", "staticmethod", "property", "super", "type"}

_BAD_ATTRS = {
    "open", "write", "writelines", "writebytes", "system", "popen", "spawn", "spawnl", "spawnv", "exec", "execv", "execl",
    "remove", "unlink", "rename", "renames", "replace", "mkdir", "makedirs", "rmdir", "removedirs", "rmtree", "chmod", "chown",
    "symlink", "link", "truncate", "extract", "extractall", "dump", "dumps_to", "save", "to_file",
    "os", "subprocess", "socket", "shutil", "ctypes", "importlib", "builtins", "modules", "logging", "FileHandler",
    "tempfile", "urllib", "http", "requests", "multiprocessing", "threading", "signal", "pty", "pickle", "marshal", "mmap",
    "f_globals", "f_locals", "f_builtins", "gi_frame", "gi_code", "cr_frame", "tb_frame", "func_globals", "settrace",
    "setprofile", "stdin", "LZMAFile", "BZ2File",
}

_TOKEN_BAD_UNQUOTED = set("$`(){};\\<")


def _path_ok(p: str) -> bool:
    if not p or "\x00" in p or "\n" in p or "\r" in p:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", p) or p.startswith("~") or p.startswith("\\\\"):
        return False
    if ".." in p.split("/"):
        return False
    if p.startswith("/"):
        return any(p == r or p.startswith(r + "/") for r in _READ_ROOTS)
    return True


def _write_ok(p: str) -> bool:
    """Tujuan tulis (dd of=, cp, mkdir): hanya di dalam folder scratch, bukan folder scratch itu sendiri."""
    return _path_ok(p) and p.startswith(SCRATCH + "/") and len(p) > len(SCRATCH) + 1


def _str_const_ok(s: str) -> bool:
    """String literal di dalam kode Python: kalau tampak seperti path absolut / naik folder, harus lolos _path_ok."""
    if s.startswith("/") or s.startswith("../") or "/../" in s or s.endswith("/.."):
        return _path_ok(s) if "\n" not in s and len(s) < 400 else False
    return True


def _py_ok(code: str):
    if len(code) > MAX_CMD:
        return False, "kode terlalu panjang"
    try:
        tree = ast.parse(code)
    except Exception:
        return False, "kode python tidak terbaca"
    open_funcs: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                if node.level or not node.module:
                    return False, "impor relatif"
                mods = [node.module]
            else:
                mods = [a.name for a in node.names]
            for m in mods:
                if m.split(".")[0] not in _PY_IMPORTS:
                    return False, "impor tidak diizinkan: " + m
        elif isinstance(node, (ast.Global, ast.Nonlocal, ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            return False, "konstruksi tidak diizinkan"
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in _BAD_ATTRS:
                return False, "atribut tidak diizinkan: " + node.attr
        elif isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in _BAD_CALLS:
                return False, "nama tidak diizinkan: " + node.id
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if not _str_const_ok(node.value):
                return False, "path literal di luar sandbox"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            a = node.args
            if not a or not (isinstance(a[0], ast.Constant) and isinstance(a[0].value, str) and _path_ok(a[0].value)):
                return False, "open() harus memakai path literal di dalam sandbox"
            mode = None
            if len(a) >= 2:
                mode = a[1].value if isinstance(a[1], ast.Constant) else None
            if len(a) > 2:
                return False, "open() argumen terlalu banyak"
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = kw.value.value if isinstance(kw.value, ast.Constant) else None
                elif kw.arg in ("encoding", "errors") and isinstance(kw.value, ast.Constant):
                    pass
                else:
                    return False, "open() opsi tidak diizinkan"
            if mode is None:
                mode = "r"   # bawaan Python = baca teks
            if mode not in ("r", "rb", "rt"):
                return False, "open() hanya boleh mode baca"
            open_funcs.add(id(node.func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "open" and id(node) not in open_funcs:
            return False, "open dipakai bukan sebagai panggilan langsung"
    return True, "python baca-saja"


def _tokenize(s: str):
    """Pecah perintah shell sederhana. Mengembalikan daftar ('w', kata) / ('op', |  ||  &&) / ('r', '2>&1'), atau None bila tidak aman."""
    toks: list = []
    cur: list[str] = []
    has = False
    i, n = 0, len(s)

    def flush():
        nonlocal cur, has
        if has:
            toks.append(("w", "".join(cur)))
        cur, has = [], False

    while i < n:
        c = s[i]
        if c in " \t":
            flush(); i += 1; continue
        if c in "\r\n":
            return None
        if c == "'":
            j = s.find("'", i + 1)
            if j < 0:
                return None
            cur.append(s[i + 1:j]); has = True; i = j + 1; continue
        if c == '"':
            j, buf = i + 1, []
            while j < n and s[j] != '"':
                d = s[j]
                if d in "$`":
                    return None
                if d == "\\":
                    if j + 1 >= n:
                        return None
                    e = s[j + 1]
                    if e in '$`"\\':
                        buf.append(e); j += 2; continue
                    if e == "\n":
                        j += 2; continue
                buf.append(d); j += 1
            if j >= n:
                return None
            cur.append("".join(buf)); has = True; i = j + 1; continue
        if c == ">":
            if "".join(cur) == "2" and s.startswith(">&1", i):
                cur, has = [], False
                toks.append(("r", "2>&1")); i += 3; continue
            if "".join(cur) == "2" and s.startswith(">/dev/null", i) and s[i + 10:i + 11] in ("", " ", "\t", "&", "|"):
                cur, has = [], False
                toks.append(("r", "2>/dev/null")); i += 10; continue
            return None
        if c == "$" and s.startswith("$((", i):
            # ekspansi aritmetika murni angka (mis. $((0xc7000))): hanya digit hex, x, spasi, + - * / %. Hasilnya cuma angka, jadi diganti "0" saat validasi.
            j = s.find("))", i + 3)
            if j < 0 or not re.fullmatch(r"[0-9a-fA-FxX+\-*/% ]+", s[i + 3:j]):
                return None
            cur.append("0"); has = True; i = j + 2; continue
        if c in "|&":
            if s.startswith("||", i) or s.startswith("&&", i):
                flush(); toks.append(("op", s[i:i + 2])); i += 2; continue
            if c == "|":
                flush(); toks.append(("op", "|")); i += 1; continue
            return None
        if c in _TOKEN_BAD_UNQUOTED or (c == "~" and not has) or (c == "#" and not has):
            return None
        cur.append(c); has = True; i += 1
    flush()
    return toks


def _segment_ok(words: list):
    name = words[0]
    args = words[1:]
    if "/" in name:
        return False, "perintah dengan path"
    if name == "cd":
        if len(args) == 1 and _path_ok(args[0]):
            return True, "cd"
        return False, "cd di luar sandbox"
    if name in ("python3", "python"):
        if len(args) == 2 and args[0] == "-c":
            return _py_ok(args[1])
        if args in (["-V"], ["--version"]):
            return True, "versi python"
        return False, "python selain -c"
    if name == "dd":
        seen: set = set()
        for a in args:
            if "=" not in a:
                return False, "dd: argumen tidak dikenal"
            k, v = a.split("=", 1)
            if k in seen or k not in ("if", "of", "bs", "skip", "count", "status"):
                return False, "dd: opsi tidak diizinkan: " + k
            seen.add(k)
            if k == "if" and not (v and _path_ok(v)):
                return False, "dd: if= di luar sandbox"
            if k == "of" and not _write_ok(v):
                return False, "dd: of= harus di " + SCRATCH + "/"
            if k in ("bs", "skip", "count") and not re.fullmatch(r"[0-9]{1,12}", v):
                return False, "dd: " + k + " harus angka"
            if k == "status" and v not in ("none", "noxfer", "progress"):
                return False, "dd: status tidak valid"
        return ("if" in seen, "dd salin ke " + SCRATCH) if "if" in seen else (False, "dd tanpa if=")
    if name == "cp":
        if len(args) == 2 and not any(a.startswith("-") for a in args) and _path_ok(args[0]) and _write_ok(args[1]):
            return True, "cp ke " + SCRATCH
        return False, "cp tidak memenuhi syarat"
    if name == "mkdir":
        paths = [a for a in args if a != "-p"]
        if paths and len(paths) == len(args) - args.count("-p") and all(_write_ok(a) for a in paths) and args.count("-p") <= 1:
            return True, "mkdir di " + SCRATCH
        return False, "mkdir tidak memenuhi syarat"
    rule = _SIMPLE.get(name)
    if rule is None:
        return False, "perintah tidak ada di daftar putih: " + name
    banned, max_pos = rule
    pos = 0
    for a in args:
        if a.startswith("-") and len(a) > 1:
            if a in banned:
                return False, "opsi terlarang: " + a
            if "/" in a:
                val = a.split("=", 1)[1] if "=" in a else ""
                if not val or not _path_ok(val):
                    return False, "path dalam opsi"
        else:
            pos += 1
            if ("/" in a or "\\" in a or a.startswith(".")) and not _path_ok(a):
                return False, "path di luar sandbox: " + a[:60]
    if max_pos is not None and pos > max_pos:
        return False, "terlalu banyak argumen posisional"
    return True, name


_HERE = re.compile(
    r"\A(?:cd\s+(?P<dir>[A-Za-z0-9_./-]+)\s*&&\s*)?python3?(?:\s+-u)?(?:\s+-)?\s*<<-?\s*(?P<q>['\"])(?P<tag>[A-Za-z_][A-Za-z0-9_]*)(?P=q)"
    r"(?:\s*2>&1)?[ \t]*\n(?P<body>.*)\n(?P=tag)[ \t]*\Z", re.S)


def classify(cmd: str):
    """(True, alasan) hanya bila perintah terbukti baca-saja. Selain itu (False, alasan)."""
    if not isinstance(cmd, str):
        return False, "bukan teks"
    cmd = cmd.replace("\r\n", "\n").strip()
    if not cmd or len(cmd) > MAX_CMD or "\x00" in cmd:
        return False, "kosong / terlalu panjang"
    m = _HERE.match(cmd)
    if m:
        tag, body = m.group("tag"), m.group("body")
        for line in body.split("\n"):
            if line.strip() == tag:
                return False, "heredoc berakhir lebih awal"
        d = m.group("dir")
        if d is not None and not _path_ok(d):
            return False, "cd di luar sandbox"
        ok, why = _py_ok(body)
        return (True, "heredoc " + why) if ok else (False, why)
    toks = _tokenize(cmd)
    if not toks:
        return False, "bentuk shell tidak sederhana"
    segs: list[list[str]] = [[]]
    for kind, val in toks:
        if kind == "w":
            segs[-1].append(val)
        elif kind == "op":
            if not segs[-1]:
                return False, "operator di awal / ganda"
            segs.append([])
    if not segs[-1]:
        return False, "operator di akhir"
    reasons = []
    for sg in segs:
        ok, why = _segment_ok(sg)
        if not ok:
            return False, why
        reasons.append(why)
    return True, ", ".join(reasons)


if __name__ == "__main__":   # uji cepat: python approval_policy.py "perintah"
    import sys
    print(classify(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()))
