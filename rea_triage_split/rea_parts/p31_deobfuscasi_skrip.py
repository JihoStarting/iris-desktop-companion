# rea_triage bagian 31/47: deobfuscasi_skrip (baris asli 12901-13745). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------- v99.20 [A2]: deobfuscation skrip berlapis (PowerShell / VBScript / JavaScript), statis -----------------------
# Teks skrip TIDAK PERNAH dijalankan: hanya ditulis ulang oleh transformasi string murni (regex + aritmetika bilangan bulat kecil).
# Tahap 1 (inline, diulang sampai stabil): sambung string ('a'+'b', "a" & "b", .concat), format -f, .Replace / -replace / Replace() / .split().join(),
#   -join / .join / [string]::Join, balik string ('..'[-1..-n], .split('').reverse().join('')), [char]N / Chr() / fromCharCode (juga aritmetika + / -),
#   daftar |%{[char]$_} / -bxor, indeks string ($env:ComSpec[4,15,25], $ShellId[1], $pshome[4]), FromBase64String(..) dalam GetString / atob / unescape,
#   escape \xNN / \uNNNN, tanda backtick PowerShell, variabel konstanta yang hanya diisi sekali (termasuk di dalam "string $var").
# Tahap 2 (bongkar pembungkus, tiap hasil menjadi lapisan baru): -EncodedCommand, FromBase64String + Deflate/Gzip(/XOR -bxor), iex / Invoke-Expression /
#   [scriptblock]::Create dengan string literal, eval / new Function / Execute / ExecuteGlobal, JS packer (Dean Edwards).
# Tahap 3: lapisan dibatasi (DSO_MAX_LAYERS dalam, DSO_MAX_NODES total), waktu (DSO_TIME), ukuran teks (DSO_MAX_TEXT). Kunci baru rep["deobf"] (None bila tidak ada
#   yang terbuka), baris "Deobfuscation skrip" di laporan, skor kecil bila isi terbuka memuat pola unduh / eksekusi; CLI `--deobf FILE [--json] [--raw] [--full]`;
#   aksi API {"action": "deobf", "path": ...}; fungsi deobfuscate(data), deobf_text(path).
# Batasan: bukan interpreter. Variabel yang diubah di banyak tempat / lewat loop, fungsi dekode buatan sendiri (string-array + rotasi gaya obfuscator.io),
#   Microsoft Script Encoder (#@~^ .vbe / .jse), AES / RC4 di skrip, dan nilai yang hanya diketahui saat jalan TIDAK dibongkar. Hasil adalah petunjuk.

DSO_TIME = 3.0
DSO_MAX_TEXT = 2 * 1024 * 1024
DSO_MAX_LAYERS = 6
DSO_MAX_NODES = 12
DSO_MAX_PASS = 24
_DSO_RX: dict = {}


def _dso_rx(p: str, flags: int = 0):
    k = (p, flags)
    r = _DSO_RX.get(k)
    if r is None:
        r = _DSO_RX[k] = re.compile(p, flags)
    return r


def _dso_S(lang: str) -> str:
    """Regex satu string literal 'aman' (tanpa interpolasi $ pada "..." PowerShell). Tanpa grup penangkap."""
    if lang == "powershell":
        return r"""(?:'(?:[^'\r\n]|'')*'|"(?:[^"\r\n`$]|`[^\r\n]|"")*")"""
    if lang == "vbscript":
        return r'"(?:[^"\r\n]|"")*"'
    return r"""(?:'(?:[^'\\\r\n]|\\.)*'|"(?:[^"\\\r\n]|\\.)*")"""


def _dso_Sfull(lang: str) -> str:
    if lang == "powershell":
        return r"""'(?:[^'\r\n]|'')*'|"(?:[^"\r\n`]|`[^\r\n]|"")*\""""
    return _dso_S(lang)


_DSO_PSESC = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
_DSO_JSESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v"}


def _dso_unq(tok: str, lang: str) -> str:
    q, b = tok[0], tok[1:-1]
    if lang == "powershell":
        if q == "'":
            return b.replace("''", "'")
        return re.sub(r"`(.)", lambda m: _DSO_PSESC.get(m.group(1), m.group(1)), b.replace('""', '"'))
    if lang == "vbscript":
        return b.replace('""', '"')

    def esc(m):
        g = m.group(1)
        try:
            if g[0] == "x" and len(g) == 3:
                return chr(int(g[1:], 16))
            if g[0] == "u":
                return chr(int(g[1:].strip("{}"), 16))
            if g.isdigit() and all(c in "01234567" for c in g):
                return chr(int(g, 8))
        except (ValueError, OverflowError):
            return m.group(0)
        return _DSO_JSESC.get(g, g)
    return re.sub(r"\\(x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]{1,6}\}|u[0-9a-fA-F]{4}|[0-3]?[0-7]{1,2}|.)", esc, b)


def _dso_q(s: str, lang: str):
    """Bungkus teks sebagai literal; None bila tidak bisa direpresentasikan (dibiarkan apa adanya oleh pemanggil)."""
    if len(s) > 400000 or any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        return None
    if lang == "javascript":
        out = []
        for c in s:
            o = ord(c)
            out.append("\\\\" if c == "\\" else '\\"' if c == '"' else "\\n" if c == "\n" else "\\r" if c == "\r" else "\\t" if c == "\t"
                       else "\\x%02x" % o if o < 32 or o == 127 else c)
        return '"' + "".join(out) + '"'
    if lang == "vbscript":
        if "\r" in s or "\n" in s or "\0" in s:
            return None
        return '"' + s.replace('"', '""') + '"'
    if any(ord(c) < 32 and c != "\t" for c in s):
        t = s.replace("`", "``").replace('"', '`"').replace("$", "`$").replace("\n", "`n").replace("\r", "`r").replace("\t", "`t").replace("\0", "`0")
        return None if any(ord(c) < 32 for c in t) else '"' + t + '"'
    return "'" + s.replace("'", "''") + "'"


_DSO_NUM = r"(?:0[xX][0-9a-fA-F]+|&[hH][0-9a-fA-F]+|\d{1,7})"


def _dso_num(s: str) -> int:
    s = s.strip()
    return int(s[2:], 16) if s[:2].lower() in ("0x", "&h") else int(s)


def _dso_arith(s: str):
    """Hanya bilangan bulat dengan + dan -; None bila bentuknya lain."""
    m = _dso_rx(r"(%s)((?:\s*[+\-]\s*%s)*)" % (_DSO_NUM, _DSO_NUM)).fullmatch(s.strip())
    if not m:
        return None
    v = _dso_num(m.group(1))
    for op, n in _dso_rx(r"([+\-])\s*(%s)" % _DSO_NUM).findall(m.group(2)):
        v = v + _dso_num(n) if op == "+" else v - _dso_num(n)
    return v


def _dso_chr(code, lang: str):
    if code is None or not 0 <= code < 0x110000 or 0xD800 <= code <= 0xDFFF:
        return None
    return _dso_q(chr(code), lang)


def _dso_lits(s: str, lang: str) -> list[str]:
    return [_dso_unq(t, lang) for t in _dso_rx(_dso_S(lang)).findall(s)]


def _dso_sub_outside(text: str, lang: str, rx, fn) -> str:
    """Seperti rx.sub, tetapi hanya di luar string literal; fn(m) -> pengganti atau None (lewati)."""
    spans = [(m.start(), m.end()) for m in _dso_rx(_dso_Sfull(lang)).finditer(text)]
    starts = [a for a, _ in spans]
    out, last = [], 0
    for m in rx.finditer(text):
        i = bisect.bisect_right(starts, m.start()) - 1
        if i >= 0 and spans[i][0] <= m.start() < spans[i][1]:
            continue
        r = fn(m)
        if r is None or m.start() < last:
            continue
        out.append(text[last:m.start()])
        out.append(r)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


# --- transformasi inline: tiap fungsi (text, lang) -> text (sama bila tidak ada perubahan) ---

def _dso_t_jsesc(text: str, lang: str) -> str:
    if lang != "javascript" or "\\" not in text:
        return text

    def f(m):
        tok = m.group(0)
        if not _dso_rx(r"\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F{])").search(tok):
            return tok
        q = _dso_q(_dso_unq(tok, lang), lang)
        return q if q is not None else tok
    return _dso_rx(_dso_S(lang)).sub(f, text)


def _dso_t_ticks(text: str, lang: str) -> str:
    if lang != "powershell" or "`" not in text:
        return text
    return _dso_sub_outside(text, lang, _dso_rx(r"`(?=[^\s`])"), lambda m: "")


def _dso_t_chars(text: str, lang: str) -> str:
    low = text.lower()
    if lang == "powershell" and "[char" in low:
        LIST = r"(%s(?:\s*,\s*%s)*)" % (_DSO_NUM, _DSO_NUM)
        text = _dso_rx(r"(?i)\[char\[\]\]\s*\(\s*%s\s*\)" % LIST).sub(
            lambda m: _dso_q("".join(chr(_dso_num(x)) for x in m.group(1).split(",") if 0 <= _dso_num(x) < 0x110000 and not 0xD800 <= _dso_num(x) <= 0xDFFF), lang) or m.group(0), text)
        core = r"%s\s*\|\s*(?:%%|foreach(?:-object)?)\s*\{\s*\[char\]\s*\(?\s*\$_\s*(?:-bxor\s*(%s)\s*)?\)?\s*\}" % (LIST, _DSO_NUM)

        def piped(m):
            x = _dso_num(m.group(2)) if m.group(2) else 0
            try:
                return _dso_q("".join(chr(_dso_num(v) ^ x) for v in m.group(1).split(",")), lang) or m.group(0)
            except (ValueError, OverflowError):
                return m.group(0)
        text = _dso_rx("(?i)" + core).sub(piped, text)
        text = _dso_rx(r"(?i)\[char\]\s*(?:\(\s*([0-9a-fx+\-\s]{1,40}?)\s*\)|(%s)(?![\w.]))" % _DSO_NUM).sub(
            lambda m: _dso_chr(_dso_arith(m.group(1) or m.group(2)), lang) or m.group(0), text)
    elif lang == "vbscript" and "chr" in low:
        text = _dso_rx(r"(?i)\bchrw?\$?\(\s*([^()]{1,40}?)\s*\)").sub(lambda m: _dso_chr(_dso_arith(m.group(1)), lang) or m.group(0), text)
    elif lang == "javascript" and "fromc" in low:
        def f(m):
            codes = [_dso_arith(x) for x in m.group(1).split(",")]
            if not codes or any(c is None or not 0 <= c < 0x110000 or 0xD800 <= c <= 0xDFFF for c in codes):
                return m.group(0)
            return _dso_q("".join(chr(c) for c in codes), lang) or m.group(0)
        text = _dso_rx(r"(?i)String\s*\.\s*fromCharCode\s*\(\s*([^()]{1,8000}?)\s*\)").sub(f, text)
    return text


_DSO_ENVSTR = {"env:comspec": "C:\\Windows\\system32\\cmd.exe", "shellid": "Microsoft.PowerShell", "pshome": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0"}


def _dso_t_psenv(text: str, lang: str) -> str:
    """$env:ComSpec[4,15,25], $ShellId[1], $pshome[4]: indeks ke nilai baku (asumsi jalur Windows standar)."""
    if lang != "powershell" or "[" not in text:
        return text

    def f(m):
        base = _DSO_ENVSTR[m.group(1).lower()]
        idx = [int(x) for x in m.group(2).split(",")]
        if any(i >= len(base) for i in idx):
            return m.group(0)
        return _dso_q("".join(base[i] for i in idx), lang) or m.group(0)
    return _dso_rx(r"(?i)\$(env:comspec|shellid|pshome)\s*\[\s*(\d{1,3}(?:\s*,\s*\d{1,3})*)\s*\]").sub(f, text)


def _dso_t_concat(text: str, lang: str) -> str:
    S = _dso_S(lang)
    op = r"[ \t]*(?:&|\+)[ \t]*(?:_?\r?\n[ \t]*)?" if lang == "vbscript" else r"[ \t]*\+[ \t]*(?:\r?\n[ \t]*)?"
    rx = _dso_rx(r"(?:%s)(?:%s(?:%s))+(?![ \t]*[.\[(\w$])" % (S, op, S))
    bad_pre = _dso_rx(r"(?i)-(?:f|[ci]?replace|join|split|[ci]?(?:eq|ne|like|match|contains|notlike|notmatch))$")

    def f(m):
        if lang == "powershell":
            pre = text[max(0, m.start() - 16):m.start()].rstrip()
            if pre.endswith(",") or bad_pre.search(pre) or text[m.end():m.end() + 4].lstrip(" \t").startswith(","):
                return m.group(0)
        q = _dso_q("".join(_dso_lits(m.group(0), lang)), lang)
        return q if q is not None else m.group(0)
    return rx.sub(f, text)


def _dso_t_fmt(text: str, lang: str) -> str:
    if lang != "powershell" or "-f" not in text.lower():
        return text
    S = _dso_S(lang)
    ARG = r"(?:%s|[+-]?\d{1,9})" % S
    rx = _dso_rx(r"(?i)(%s)\s*-f\s*(%s(?:\s*,\s*%s)*)(?![\w$(\[.])" % (S, ARG, ARG))

    def f(m):
        fmt = _dso_unq(m.group(1), lang)
        args = [_dso_unq(a, lang) if a[0] in "'\"" else a for a in _dso_rx(ARG).findall(m.group(2))]
        bad = []

        def sub(mm):
            if mm.group(0) == "{{":
                return "{"
            if mm.group(0) == "}}":
                return "}"
            i = int(mm.group(1))
            if i >= len(args):
                bad.append(1)
                return ""
            return args[i]
        try:
            out = _dso_rx(r"\{\{|\}\}|\{(\d+)\}").sub(sub, fmt)
        except Exception:
            return m.group(0)
        if bad or _dso_rx(r"\{\d+[,:][^{}]*\}").search(fmt):
            return m.group(0)
        return _dso_q(out, lang) or m.group(0)
    return rx.sub(f, text)


def _dso_t_replace(text: str, lang: str) -> str:
    low = text.lower()
    if "replace" not in low and "split" not in low:
        return text
    S = _dso_S(lang)
    if lang == "powershell":
        text = _dso_rx(r"(?i)(%s)\s*\.\s*replace\s*\(\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang)), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)

        def rr(m):
            pre = text[max(0, m.start() - 4):m.start()].rstrip()
            if pre.endswith("+") or pre.endswith(","):
                return m.group(0)
            rep = _dso_unq(m.group(3), lang) if m.group(3) else ""
            if "$" in rep or text[m.end():m.end() + 4].lstrip().startswith(","):
                return m.group(0)
            try:
                out = _dso_rx(_dso_unq(m.group(2), lang), re.I if m.group(0).lower().find("-creplace") < 0 else 0).sub(lambda _m: rep, _dso_unq(m.group(1), lang))
            except re.error:
                return m.group(0)
            return _dso_q(out, lang) or m.group(0)
        text = _dso_rx(r"(?i)(%s)\s*-[ci]?replace\s*(%s)(?:\s*,\s*(%s))?" % (S, S, S)).sub(rr, text)
    elif lang == "vbscript":
        text = _dso_rx(r"(?i)\bReplace\(\s*(%s)\s*,\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang)), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)
    else:
        text = _dso_rx(r"(%s)\s*\.\s*replace\s*\(\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: m.group(0) if "$" in m.group(3) or not _dso_unq(m.group(2), lang) else
            (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang), 1), lang) or m.group(0)), text)

        def rl(m):
            rep = _dso_unq(m.group(4), lang)
            if "$" in rep:
                return m.group(0)
            try:
                pat = _dso_rx(m.group(2), re.I if "i" in m.group(3) else 0)
            except re.error:
                return m.group(0)
            return _dso_q(pat.sub(lambda _m: rep, _dso_unq(m.group(1), lang), count=0 if "g" in m.group(3) else 1), lang) or m.group(0)
        text = _dso_rx(r"(%s)\s*\.\s*replace\s*\(\s*/((?:[^/\\\r\n]|\\.){1,200})/([gimsuy]*)\s*,\s*(%s)\s*\)" % (S, S)).sub(rl, text)
        text = _dso_rx(r"(%s)\s*\.\s*split\(\s*(%s)\s*\)\s*\.\s*join\(\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(3), lang).join(_dso_unq(m.group(1), lang).split(_dso_unq(m.group(2), lang))), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)
    return text


def _dso_t_join(text: str, lang: str) -> str:
    low = text.lower()
    if "join" not in low and "concat" not in low and "[-1" not in low and "][" not in low and "[" not in low:
        return text
    S = _dso_S(lang)
    LS = r"%s(?:\s*,\s*%s)*" % (S, S)
    EMPTY = r"""(?:''|"")"""

    def jn(items, sep, ln=lang):
        return _dso_q(sep.join(items), ln)

    if lang == "powershell":
        text = _dso_rx(r"(?i)(%s)\s*\[\s*-1\s*\.\.\s*-[^\]]{1,40}\]" % S).sub(lambda m: _dso_q(_dso_unq(m.group(1), lang)[::-1], lang) or m.group(0), text)

        def idx(m):
            s = _dso_unq(m.group(1), lang)
            ix = [int(x) for x in m.group(2).split(",")]
            return _dso_q("".join(s[i] for i in ix), lang) or m.group(0) if all(0 <= i < len(s) for i in ix) else m.group(0)
        text = _dso_rx(r"(?<![,\w$])(%s)\s*\[\s*(\d{1,4}(?:\s*,\s*\d{1,4})*)\s*\]" % S).sub(idx, text)
        text = _dso_rx(r"(?i)@?\(\s*(%s)\s*\)\s*-join\s*(%s)" % (LS, S)).sub(lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang)) or m.group(0), text)
        text = _dso_rx(r"(?i)-join\s*@?\(\s*(%s)\s*\)" % LS).sub(lambda m: jn(_dso_lits(m.group(1), lang), "") or m.group(0), text)
        text = _dso_rx(r"(?i)(%s)\s*-join\s*%s" % (S, EMPTY)).sub(lambda m: m.group(1), text)
        text = _dso_rx(r"(?i)-join\s*(%s)(?!\s*,)" % S).sub(lambda m: m.group(1), text)
        text = _dso_rx(r"(?i)\[string\]\s*::\s*join\s*\(\s*(%s)\s*,\s*@?\(?\s*(%s)\s*\)?\s*\)" % (S, LS)).sub(
            lambda m: jn(_dso_lits(m.group(2), lang), _dso_unq(m.group(1), lang)) or m.group(0), text)
    elif lang == "javascript":
        text = _dso_rx(r"(%s)\s*\.\s*split\(\s*(%s)\s*\)\s*\.\s*reverse\(\s*\)\s*\.\s*join\(\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: jn(_dso_unq(m.group(1), lang).split(_dso_unq(m.group(2), lang))[::-1] if _dso_unq(m.group(2), lang) else list(_dso_unq(m.group(1), lang))[::-1], _dso_unq(m.group(3), lang)) or m.group(0), text)
        text = _dso_rx(r"\[\s*(%s)\s*\]\s*\.\s*join\(\s*(%s)?\s*\)" % (LS, S)).sub(
            lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang) if m.group(2) else ",") or m.group(0), text)
        text = _dso_rx(r"(%s)\s*\.\s*concat\(\s*(%s)\s*\)" % (S, LS)).sub(
            lambda m: jn([_dso_unq(m.group(1), lang)] + _dso_lits(m.group(2), lang), "") or m.group(0), text)
    else:
        text = _dso_rx(r"(?i)\bJoin\(\s*Array\(\s*(%s)\s*\)\s*,\s*(%s)\s*\)" % (LS, S)).sub(
            lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang)) or m.group(0), text)
    return text


def _dso_t_b64(text: str, lang: str) -> str:
    low = text.lower()
    S = _dso_S(lang)

    def dec(b64: str):
        try:
            raw = base64.b64decode(re.sub(r"\s+", "", b64) + "=" * (-len(re.sub(r"\s+", "", b64)) % 4), validate=False)
        except Exception:
            return None
        return raw

    def okt(t: str) -> bool:
        return len(t) >= 1 and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9

    if lang == "powershell" and "getstring" in low:
        encs = {"utf8": "utf-8", "unicode": "utf-16le", "ascii": "ascii", "bigendianunicode": "utf-16be", "utf32": "utf-32le", "utf7": "utf-7", "default": "utf-8"}

        def f(m):
            raw = dec(_dso_unq(m.group(2), lang))
            if raw is None:
                return m.group(0)
            try:
                t = raw.decode(encs[m.group(1).lower()], "strict")
            except Exception:
                return m.group(0)
            return (_dso_q(t, lang) or m.group(0)) if okt(t) else m.group(0)
        text = _dso_rx(r"(?i)\[\s*(?:System\.)?Text\.Encoding\s*\]\s*::\s*(utf8|unicode|ascii|bigendianunicode|utf32|utf7|default)\s*\.\s*GetString\s*\(\s*"
                       r"\[\s*(?:System\.)?Convert\s*\]\s*::\s*FromBase64String\s*\(\s*(%s)\s*\)\s*\)" % S).sub(f, text)
    if lang == "javascript" and "atob" in low:
        def g(m):
            raw = dec(_dso_unq(m.group(1), lang))
            if raw is None:
                return m.group(0)
            t = raw.decode("latin-1")
            return (_dso_q(t, lang) or m.group(0)) if okt(t) else m.group(0)
        text = _dso_rx(r"(?:window\s*\.\s*)?atob\s*\(\s*(%s)\s*\)" % S).sub(g, text)
    if lang == "javascript" and ("unescape" in low or "decodeuri" in low):
        def h(m):
            s = _dso_unq(m.group(1), lang)
            try:
                s2 = _dso_rx(r"%u([0-9a-fA-F]{4})|%([0-9a-fA-F]{2})").sub(lambda mm: chr(int(mm.group(1) or mm.group(2), 16)), s)
            except (ValueError, OverflowError):
                return m.group(0)
            return _dso_q(s2, lang) or m.group(0)
        text = _dso_rx(r"(?:unescape|decodeURIComponent|decodeURI)\s*\(\s*(%s)\s*\)" % S).sub(h, text)
    return text


def _dso_t_alias(text: str, lang: str) -> str:
    if lang != "powershell":
        return text
    return _dso_rx(r"""(?i)[.&]\s*\(\s*(['"])(iex|invoke-expression)\1\s*\)""").sub(lambda m: m.group(2), text)


def _dso_vars_n(text: str, name: str, lang: str) -> int:
    if lang == "powershell":
        return len(_dso_rx(r"(?i)\$(?:script:|global:|local:)?%s\b\s*[-+*/%%]?=(?!=)" % re.escape(name)).findall(text))
    if lang == "vbscript":
        return len(_dso_rx(r"(?im)^[ \t]*(?:(?:Dim|Const|Set)[ \t]+)?%s[ \t]*=" % re.escape(name)).findall(text))
    return len(_dso_rx(r"(?<![\w$.])%s\s*(?:[-+*/%%&|^]|<<|>>>?)?=(?![=>])" % re.escape(name)).findall(text))


def _dso_ps_expand(body: str, defs: dict):
    out, i, n = [], 0, len(body)
    var = _dso_rx(r"\$(?:\{(\w+)\}|\(\s*\$(\w+)\s*\)|(?:script:|global:)?(\w+))")
    while i < n:
        c = body[i]
        if c == "`" and i + 1 < n:
            out.append(_DSO_PSESC.get(body[i + 1], body[i + 1]))
            i += 2
        elif c == '"' and body[i + 1:i + 2] == '"':
            out.append('"')
            i += 2
        elif c == "$":
            m = var.match(body, i)
            nm = (m.group(1) or m.group(2) or m.group(3)) if m else None
            if not nm or nm.lower() not in defs:
                return None
            out.append(defs[nm.lower()])
            i = m.end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _dso_t_vars(text: str, lang: str) -> str:
    S = _dso_S(lang)
    if lang == "powershell":
        asg = _dso_rx(r"(?im)\$(?:script:|global:|local:)?([A-Za-z_]\w*)[ \t]*=[ \t]*(%s)[ \t]*(?=;|\r?$)" % S)
    elif lang == "vbscript":
        asg = _dso_rx(r"""(?im)^[ \t]*(?:(?:Dim|Const)[ \t]+)?([A-Za-z_]\w*)[ \t]*=[ \t]*(%s)[ \t]*(?:'[^\r\n]*)?\r?$""" % S)
    else:
        asg = _dso_rx(r"""(?m)\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*(%s)\s*(?=[;,\r\n]|$)""" % S)
    defs: dict = {}
    for m in itertools.islice(asg.finditer(text), 400):
        nm = m.group(1)
        key = nm if lang == "javascript" else nm.lower()
        if key in defs or len(defs) >= 64:
            defs[key] = None
            continue
        bad = (lang == "powershell" and _dso_rx(r"(?i)(?:\$%s\s+in\b|\$%s(?:\+\+|--)|\[ref\]\s*\$%s|-(?:out)?variable\s+%s\b|param\s*\([^)]*\$%s\b)" % ((re.escape(nm),) * 5)).search(text)) or \
              (lang == "javascript" and _dso_rx(r"(?:function\s*[\w$]*\s*\([^)]*\b%s\b|(?<![\w$.])%s(?:\+\+|--))" % ((re.escape(nm),) * 2)).search(text))
        if bad or _dso_vars_n(text, nm, lang) != 1:
            defs[key] = None
            continue
        defs[key] = m.group(2)
    defs = {k: v for k, v in defs.items() if v}
    if not defs:
        return text
    if lang == "powershell":
        names = "|".join(re.escape(k) for k in sorted(defs, key=len, reverse=True))
        use = _dso_rx(r"(?i)(?<![\w$])\$(?:script:|global:|local:)?(%s)(?![\w:])(?!\s*[-+*/%%]?=(?!=))" % names)
        text = _dso_sub_outside(text, lang, use, lambda m: defs[m.group(1).lower()])
        vals = {k: _dso_unq(v, lang) for k, v in defs.items()}

        def dq(m):
            tok = m.group(0)
            if tok[0] != '"' or "$" not in tok:
                return tok
            e = _dso_ps_expand(tok[1:-1], vals)
            q = _dso_q(e, lang) if e is not None else None
            return q if q is not None else tok
        return _dso_rx(_dso_Sfull(lang)).sub(dq, text)
    names = "|".join(re.escape(k) for k in sorted(defs, key=len, reverse=True))
    if lang == "vbscript":
        use = _dso_rx(r"(?i)(?<![\w.])(%s)(?!\w)" % names)

        def fv(m):
            ls = text.rfind("\n", 0, m.start()) + 1
            pre = text[ls:m.start()]
            if _dso_rx(r"(?i)\s*(?:dim|redim|const|private|public|for|function|sub|next|set)\b").match(pre) or (not pre.strip() and _dso_rx(r"\s*=(?!=)").match(text, m.end())):
                return None
            return defs[m.group(1).lower()]
        return _dso_sub_outside(text, lang, use, fv)
    use = _dso_rx(r"(?<![\w$.])(%s)(?![\w$])(?!\s*(?:[-+*/%%&|^]|<<|>>>?)?=(?![=>]))(?!\s*:)" % names)

    def fj(m):
        if _dso_rx(r"(?:var|let|const|function)\s+$").search(text[max(0, m.start() - 12):m.start()]):
            return None
        return defs[m.group(1)]
    return _dso_sub_outside(text, lang, use, fj)


_DSO_TRANSFORMS = (("kunci / escape", _dso_t_jsesc), ("backtick", _dso_t_ticks), ("variabel", _dso_t_vars), ("karakter", _dso_t_chars), ("indeks env", _dso_t_psenv),
                   ("base64 inline", _dso_t_b64), ("sambung string", _dso_t_concat), ("format -f", _dso_t_fmt), ("replace / split", _dso_t_replace),
                   ("join / balik / indeks", _dso_t_join), ("alias iex", _dso_t_alias))


def _dso_inline(text: str, lang: str, deadline: float):
    names: list[str] = []
    for _ in range(DSO_MAX_PASS):
        before = text
        for nm, fn in _DSO_TRANSFORMS:
            if time.monotonic() > deadline:
                return text, names
            try:
                t2 = fn(text, lang)
            except (RecursionError, MemoryError):
                continue
            if t2 != text and len(t2) <= DSO_MAX_TEXT * 2:
                text = t2
                if nm not in names:
                    names.append(nm)
        if text == before:
            break
    return text, names


def _dso_lang(text: str, hint: str | None = None) -> str:
    if hint in ("powershell", "vbscript", "javascript"):
        return hint
    return max(_dso_lang_scores(text), key=lambda x: x[0])[1]


def _dso_lang_scores(text: str) -> list:
    h = text[:200000]
    ps = len(re.findall(r"(?i)\$\w+\s*=|-join\b|\[char\]|\biex\b|invoke-expression|frombase64string|\bnew-object\b|-bxor|\bwrite-host\b|\[convert\]|\[system\.", h))
    js = len(re.findall(r"(?i)\bvar\s+\w+|\bfunction\s*\w*\s*\(|fromcharcode|unescape\(|\beval\(|\batob\(|document\.|=>|\.split\(|\.join\(", h))
    vb = len(re.findall(r"(?i)\bdim\s+\w+|\bchrw?\(|wscript\.|createobject|\bexecute(?:global)?\b|^\s*set\s+\w+\s*=|\bend\s+(?:sub|function|if)\b", h, re.M))
    if re.search(r"(?i)\bpowershell(?:\.exe)?\b[^\r\n]{0,200}\s-(?:e|ec|enc|encodedcommand|nop|noprofile|w|windowstyle|command|c)\b", h):
        ps += 3
    return [(ps, "powershell"), (js, "javascript"), (vb, "vbscript")]


def _dso_to_text(data) -> str:
    b = bytes(data[:DSO_MAX_TEXT * 2])
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", "ignore")
    if len(b) >= 8 and b[1::2].count(0) > 0.9 * (len(b) // 2):
        return b.decode("utf-16le", "ignore")
    return b.decode("utf-8", "replace").lstrip("\ufeff")


def _dso_text_ok(t: str, minlen: int = 4) -> bool:
    return len(t) >= minlen and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9


def _dso_b64raw(b64: str):
    c = re.sub(r"\s+", "", b64)
    if len(c) < 16 or len(c) % 4 == 1:
        return None
    try:
        return base64.b64decode(c + "=" * (-len(c) % 4))
    except Exception:
        return None


def _dso_blob(raw: bytes, keys: list, deadline: float):
    """base64 -> [gzip / zlib / deflate / XOR] sampai dikenali. -> (langkah, teks | None, label | None, byte) atau None."""
    steps = ["base64"]
    b = bytes(raw)
    for _ in range(3):
        if time.monotonic() > deadline:
            return None
        lab = _chain_label(b)
        if lab or _chain_text(b) is not None:
            return steps, (None if lab else _chain_text(b)), lab, b
        r = _t_inflate(b)
        if r:
            steps.append(r[0])
            b = r[1]
            continue
        hit = None
        for k in keys:
            t = b[:512].translate(_xor_table("XOR", k))
            if _chain_label(t) or t[:2] == b"\x1f\x8b" or (t[0] == 0x78 and t[1] in (0x01, 0x5E, 0x9C, 0xDA)) or _chain_text(t) is not None:
                hit = k
                break
        if hit is None:
            return None
        steps.append("XOR 0x%02X" % hit)
        b = bytes(b[:CHAIN_MAX_OUT]).translate(_xor_table("XOR", hit))
    lab = _chain_label(b)
    if lab or _chain_text(b) is not None:
        return steps, (None if lab else _chain_text(b)), lab, b
    return None


def _dso_js_packer(text: str):
    S = _dso_S("javascript")
    m = _dso_rx(r"(?s)eval\s*\(\s*function\s*\(\s*p\s*,\s*a\s*,\s*c\s*,\s*k\s*,\s*e\s*,\s*[dr]\s*\)\s*\{.{0,3000}?\}\s*\(\s*(%s)\s*,\s*(\d{1,3})\s*,\s*(\d{1,6})\s*,\s*(%s)\s*\.\s*split\(\s*(%s)\s*\)" % (S, S, S)).search(text)
    if not m:
        return None
    p, a, c = _dso_unq(m.group(1), "javascript"), int(m.group(2)), int(m.group(3))
    k = _dso_unq(m.group(4), "javascript").split(_dso_unq(m.group(5), "javascript"))
    if not 2 <= a <= 62 or c > 200000:
        return None
    digs = "0123456789abcdefghijklmnopqrstuvwxyz"

    def enc(n: int) -> str:
        r = "" if n < a else enc(n // a)
        n %= a
        return r + (chr(n + 29) if n > 35 else digs[n])
    d = {}
    for i in range(min(c, len(k))):
        d[enc(i)] = k[i] or enc(i)
    out = _dso_rx(r"\b\w+\b").sub(lambda mm: d.get(mm.group(0), mm.group(0)), p)
    return out if _dso_text_ok(out, 8) else None


def _dso_payloads(text: str, lang: str, deadline: float) -> list:
    """Pembungkus yang bisa dibuka dari `text` (sudah melewati tahap inline). -> [(via, payload str | bytes, binary, lang)]."""
    out: list = []

    def add(via, pay, binary=False, plang=None):
        if len(out) < 8:
            out.append((via, pay, binary, plang or lang))

    def code_like(t: str) -> bool:
        return _dso_text_ok(t, 4) and bool(re.search(r"[\s;(|$=]", t)) and bool(re.search(r"[A-Za-z]{3}", t)) and sum(c.isalnum() for c in t) >= 0.4 * len(t)

    S = _dso_S(lang)
    for m in itertools.islice(_PS_ENC.finditer(text), 4):
        raw = _dso_b64raw(m.group(1))
        if raw is None:
            continue
        for enc in ("utf-16le", "utf-8"):
            t = raw.decode(enc, "ignore")
            if _dso_text_ok(t, 6):
                add("-EncodedCommand", t, False, "powershell")
                break
    if lang == "powershell":
        pat = (r"(?is)(?:\b(?:iex|invoke-expression)\b|\[\s*scriptblock\s*\]\s*::\s*create|\.\s*invokecommand\s*\.\s*invokescript)\s*\(?\s*(%s)" % S,
               r"(?is)(%s)\s*\)?\s*\|\s*(?:iex|invoke-expression)\b" % S)
        for rx in pat:
            for m in itertools.islice(_dso_rx(rx).finditer(text), 4):
                t = _dso_unq(m.group(1), lang)
                if code_like(t):
                    add("iex / Invoke-Expression (string literal)", t, False, "powershell")
        if _dso_rx(r"(?i)deflatestream|gzipstream|io\.compression|-bxor|assembly\s*\]\s*::\s*load").search(text):
            keys = [_dso_num(x) & 0xFF for x in _dso_rx(r"(?i)-bxor\s*(%s)" % _DSO_NUM).findall(text)]
            nums = {n.lower(): _dso_num(v) & 0xFF for n, v in _dso_rx(r"(?i)\$(\w+)\s*=\s*(%s)\s*(?=[;\r\n]|$)" % _DSO_NUM).findall(text)}
            for n in _dso_rx(r"(?i)-bxor\s*\$(\w+)").findall(text):
                if n.lower() in nums:
                    keys.append(nums[n.lower()])
            keys = [k for k in dict.fromkeys(keys) if 1 <= k < 256]
            for m in itertools.islice(_dso_rx(r"(?i)FromBase64String\s*\(\s*(%s)\s*\)" % S).finditer(text), 4):
                raw = _dso_b64raw(_dso_unq(m.group(1), lang))
                r = _dso_blob(raw, keys, deadline) if raw is not None and len(raw) >= 16 else None
                if r and len(r[0]) >= 2:
                    steps, t, lab, b = r
                    via = " > ".join(steps)
                    if lab:
                        add(via + " (%s)" % lab, bytes(b), True)
                    elif t:
                        add(via, t[:DSO_MAX_TEXT], False, _dso_lang(t))
    elif lang == "javascript":
        for rx in (r"\beval\s*\(\s*(%s)" % S, r"\bnew\s+Function\s*\(\s*(?:%s\s*,\s*)*(%s)\s*\)" % (S, S), r"\bset(?:Timeout|Interval)\s*\(\s*(%s)" % S, r"document\s*\.\s*write(?:ln)?\s*\(\s*(%s)" % S):
            for m in itertools.islice(_dso_rx(rx).finditer(text), 4):
                t = _dso_unq(m.group(1), lang)
                if code_like(t) and len(t) >= 8 and (not rx.startswith("document") or "<script" in t.lower()):
                    add("eval / Function / setTimeout (string literal)" if not rx.startswith("document") else "document.write (HTML / script)", t, False, "javascript")
        pk = _dso_js_packer(text)
        if pk:
            add("JS packer (Dean Edwards)", pk, False, "javascript")
    else:
        for m in itertools.islice(_dso_rx(r"(?i)\b(?:Execute|ExecuteGlobal|Eval)\b\s*\(?\s*(%s)" % S).finditer(text), 4):
            t = _dso_unq(m.group(1), lang)
            if code_like(t):
                add("Execute / ExecuteGlobal / Eval (string literal)", t, False, "vbscript")
    return out


_DSO_CALLS = _dso_rx(r"(?i)\b(DownloadString|DownloadFile|DownloadData|Invoke-WebRequest|Invoke-RestMethod|Net\.WebClient|Start-BitsTransfer|bitsadmin|certutil|"
                     r"Invoke-Expression|IEX|Start-Process|Add-Type|VirtualAlloc|Reflection\.Assembly|AssemblyLoad|WScript\.Shell|Shell\.Application|ADODB\.Stream|"
                     r"XMLHTTP|ServerXMLHTTP|WinHttp\.WinHttpRequest|MSXML2|ActiveXObject|Scripting\.FileSystemObject|regsvr32|mshta|rundll32|schtasks|wmic|"
                     r"amsiInitFailed|AmsiUtils|-WindowStyle\s+Hidden|-ExecutionPolicy\s+Bypass|-NoProfile|powershell(?:\.exe)?|cmd(?:\.exe)?\s+/c)\b")
_DSO_STRONG = frozenset({"downloadstring", "downloadfile", "downloaddata", "invoke-webrequest", "invoke-restmethod", "net.webclient", "start-bitstransfer", "bitsadmin", "certutil",
                         "virtualalloc", "reflection.assembly", "assemblyload", "adodb.stream", "xmlhttp", "serverxmlhttp", "winhttp.winhttprequest", "amsiinitfailed", "amsiutils",
                         "regsvr32", "mshta", "rundll32", "wscript.shell", "shell.application"})


def _dso_looks_text(b: bytes) -> bool:
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return True
    s = bytes(b[:8192])
    if len(s) >= 8 and s[1::2].count(0) > 0.9 * (len(s) // 2):
        return True
    if not s or s.count(0):
        return False
    t = s.decode("utf-8", "ignore")
    ctl = sum(1 for c in t if ord(c) < 32 and c not in "\r\n\t")
    return len(t.encode("utf-8")) >= 0.97 * len(s) and ctl <= 0.02 * len(t)


def deobfuscate(data, lang: str | None = None) -> dict | None:
    """Deobfuscation statis satu skrip (bytes / str). -> dict {lang, layers, leaves, changed, calls, urls, truncated} atau None bila kosong.
    Tiap lapisan: {n, parent, via, lang, steps, kind, size, sha256, preview, text}. Tidak pernah menjalankan skrip."""
    deadline = time.monotonic() + DSO_TIME
    text = (data if isinstance(data, str) else _dso_to_text(data))[:DSO_MAX_TEXT]
    if not text.strip():
        return None
    nodes = [{"n": 0, "parent": -1, "via": "asli", "lang": _dso_lang(text, lang), "raw": text, "depth": 0, "binary": False, "kind": "teks"}]
    seen = {hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()}
    trunc, qi = False, 0
    while qi < len(nodes):
        nd = nodes[qi]
        qi += 1
        if nd["binary"]:
            continue
        if time.monotonic() > deadline:
            trunc = True
            nd["text"], nd["steps"] = nd["raw"], []
            continue
        nd["text"], nd["steps"] = _dso_inline(nd["raw"], nd["lang"], deadline)
        if nd["depth"] >= DSO_MAX_LAYERS:
            continue
        try:
            pays = _dso_payloads(nd["text"], nd["lang"], deadline)
        except (RecursionError, MemoryError):
            pays = []
        for via, pay, binary, plang in pays:
            if len(nodes) >= DSO_MAX_NODES:
                trunc = True
                break
            key = hashlib.sha256(pay if binary else pay.encode("utf-8", "ignore")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            ch = {"n": len(nodes), "parent": nd["n"], "via": via, "lang": plang, "depth": nd["depth"] + 1, "binary": binary}
            if binary:
                ch.update({"kind": _chain_label(pay) or "biner", "text": "", "steps": [], "size": len(pay), "sha": key})
            else:
                ch.update({"kind": "teks", "raw": pay[:DSO_MAX_TEXT]})
            nodes.append(ch)
    kids = {n["parent"] for n in nodes}
    layers = []
    for nd in nodes:
        t = nd.get("text", "")
        layers.append({"n": nd["n"], "parent": nd["parent"], "via": nd["via"], "lang": nd["lang"], "steps": nd.get("steps", []), "kind": nd["kind"],
                       "size": nd.get("size", len(t)), "sha256": nd.get("sha") or hashlib.sha256(t.encode("utf-8", "ignore")).hexdigest(), "preview": _clean(t[:200]), "text": t})
    leaves = [n["n"] for n in nodes if n["n"] not in kids]
    changed = len(nodes) > 1 or bool(nodes[0].get("steps")) and nodes[0]["text"] != nodes[0]["raw"]
    blob = "\n".join(n.get("text", "") for n in nodes)[:DSO_MAX_TEXT]
    calls = _uniq((m.group(1) for m in _DSO_CALLS.finditer(blob)), 12)
    urls = _uniq((u.rstrip(".,;)'\"") for u in _URL.findall(blob)), 10)
    return {"lang": nodes[0]["lang"], "layers": layers, "leaves": leaves, "changed": changed, "calls": calls, "urls": urls, "truncated": trunc}


def _dso_summary(r: dict) -> dict:
    """Bentuk ringkas untuk rep["deobf"] (JSON-aman, kecil)."""
    lv = [l for l in r["layers"] if l["n"] in r["leaves"]]
    return {"lang": r["lang"], "truncated": r["truncated"], "calls": r["calls"], "urls": r["urls"],
            "layers": [{k: l[k] for k in ("n", "parent", "via", "lang", "steps", "kind", "size", "sha256", "preview")} for l in r["layers"]],
            "leaves": r["leaves"], "final": [l["text"][:1500] for l in lv if l["text"]][:2]}


_DSO_OBF = frozenset({"backtick", "karakter", "indeks env", "base64 inline", "format -f", "replace / split", "join / balik / indeks", "alias iex"})
_DSO_TRIG = _dso_rx(r"(?i)frombase64string|\s-e(?:nc|ncodedcommand)?\s+[A-Za-z0-9+/]{16}|\biex\b|invoke-expression|fromcharcode|\beval\s*\(|unescape\s*\(|atob\s*\(|\[char\]|\bchrw?\s*\(|"
                    r"\bexecute(?:global)?\b|-join|\s-f\s*['\"]|\.replace\s*\(|`[A-Za-z]|-bxor|getstring|function\s*\(\s*p\s*,\s*a\s*,\s*c|\.split\s*\(")


def _dso_enrich(rep: dict, d, strs: list[str]) -> None:
    """Dipanggil dari _triage_open: kunci baru rep["deobf"] (None bila tidak ada hasil bermakna). Aditif; tidak pernah melempar."""
    rep["deobf"] = None
    try:
        srcs: list = []
        if len(d) <= DSO_MAX_TEXT * 2 and _dso_looks_text(d):
            srcs.append(d)
        else:
            srcs = [s for s in strs if len(s) >= 200 and _DSO_TRIG.search(s)][:3]
        for src in srcs:
            probe = src if isinstance(src, str) else _dso_to_text(src)
            if not _DSO_TRIG.search(probe[:DSO_MAX_TEXT]):
                continue
            head = probe[:200]
            if head.startswith("#!") and not re.search(r"(?i)pwsh|powershell|node|cscript|wscript", head.split("\n", 1)[0]):
                continue   # skrip shell / perl / python / ruby: bukan sasaran modul ini
            if max(_dso_lang_scores(probe[:200000]), key=lambda x: x[0])[0] < 2:
                continue
            if len(re.findall(r"(?m)^(?:import [\w.]+|from [\w.]+ import |def \w+\(.*\):|class \w+.*:)", probe[:60000])) >= 2:
                continue   # sumber Python
            r = deobfuscate(probe)
            if not r or not r["changed"]:
                continue
            obf = {s_ for l in r["layers"] for s_ in l["steps"]} & _DSO_OBF   # sambung string / variabel saja lazim di skrip sah
            strong = any(c.lower() in _DSO_STRONG for c in r["calls"])
            if len(r["layers"]) < 2 and not (len(obf) >= 2 or (obf and strong)):
                continue
            rep["deobf"] = _dso_summary(r)
            ind = rep["ind"]
            for u in r["urls"]:
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
            rep["warn"].append("skrip tersamar berhasil dibuka (%d lapisan, %s): %s" % (len(r["layers"]), r["lang"], " -> ".join(l["via"] for l in r["layers"][1:4]) or ", ".join(r["layers"][0]["steps"][:4])))
            return
    except Exception as e:
        rep["warn"].append("deobfuscation skrip gagal: %s" % type(e).__name__)


def _score_dso(rep: dict, add) -> None:
    x = rep.get("deobf")
    if not x:
        return
    strong = [c for c in x["calls"] if c.lower() in _DSO_STRONG]
    if strong:
        add(2, "isi skrip yang terbuka memuat pola unduh / eksekusi (%s)" % ", ".join(strong[:3]))
    elif len(x["layers"]) >= 3:
        add(1, "skrip dibungkus beberapa lapis (%d)" % len(x["layers"]))


def _render_dso(rep: dict, a, compact: bool, defang: bool) -> None:
    x = rep.get("deobf")
    if not x:
        return
    a("Deobfuscation skrip (%s, %d lapisan%s): %s" % (x["lang"], len(x["layers"]), ", TERPOTONG" if x["truncated"] else "",
                                                    " -> ".join(l["via"] + (" [%s]" % ", ".join(l["steps"][:3]) if l["steps"] else "") for l in x["layers"][:5])))
    if x["calls"]:
        a("   alat / pola di isi yang terbuka: %s" % ", ".join(_clean(c) for c in x["calls"][:(5 if compact else 12)]))
    for t in x["final"][:(1 if compact else 2)]:
        a("   hasil akhir: %s" % _df(_clean(t)[:(160 if compact else 360)], defang))


def deobf_text(path, defang: bool = True, full: bool = False) -> str:
    """Teks deobfuscation satu skrip. CLI --deobf, API action 'deobf'."""
    try:
        f, size = _open_regular(path)
        with f:
            data = f.read(DSO_MAX_TEXT * 2)
    except Exception as e:
        return "Deobfuscation gagal (%s: %s)." % (type(e).__name__, str(e)[:100])
    r = deobfuscate(data)
    if not r:
        return "Deobfuscation: berkas kosong."
    L_ = ["Deobfuscation skrip: %s | bahasa %s | %d lapisan%s" % (_clean(os.path.basename(os.fspath(path))), r["lang"], len(r["layers"]), " | TERPOTONG (batas waktu / lapisan)" if r["truncated"] else "")]
    if not r["changed"]:
        L_.append("Tidak ada lapisan penyamaran yang berhasil dibuka (bukan berarti bersih: pola di luar jangkauan, mis. string-array obfuscator.io, Script Encoder #@~^, AES / RC4).")
    for l in r["layers"]:
        if l["kind"] != "teks":
            L_.append(" [%d] <- [%d] %s: %s %s, sha256 %s..." % (l["n"], l["parent"], l["via"], l["kind"], _human(l["size"]), l["sha256"][:16]))
            continue
        L_.append(" [%d]%s %s (%s, %s)%s" % (l["n"], (" <- [%d]" % l["parent"]) if l["parent"] >= 0 else "", l["via"], l["lang"], _human(l["size"]),
                                            (" | transformasi: " + ", ".join(l["steps"])) if l["steps"] else ""))
        if l["n"] in r["leaves"] or full:
            body = l["text"] if full else l["text"][:1500]
            L_.append("     " + _df("\n     ".join(_clean(x) for x in body.splitlines()[:60]), defang) + ("   ..." if not full and len(l["text"]) > 1500 else ""))
    if r["calls"]:
        L_.append("Alat / pola: " + ", ".join(_clean(c) for c in r["calls"]))
    if r["urls"]:
        L_.append("URL: " + ", ".join(_df(_clean(u), defang) for u in r["urls"]))
    return "\n".join(L_)



