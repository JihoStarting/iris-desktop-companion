# rea_triage bagian 14/47: laporan_html (baris asli 4615-4842). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v99.7 [B4]: laporan HTML tunggal offline (tanpa skrip / gaya / font / gambar dari luar; semua nilai di-escape).
# ---------------------------------------------------------------------------

_HTML_CSS = """
:root{--bg:#fff;--fg:#1d2330;--mut:#5b6577;--card:#f4f6fa;--line:#d9dee8;--acc:#2f5bd8;--hi:#c62828;--mid:#d9822b;--lo:#b59b00;--ok:#2e7d32}
@media (prefers-color-scheme:dark){:root{--bg:#12151c;--fg:#e4e8f0;--mut:#9aa4b8;--card:#1b202b;--line:#2c3446;--acc:#7da2ff;--hi:#ff6b6b;--mid:#ffa94d;--lo:#e6c94a;--ok:#6fcf7a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:18px 20px;border-bottom:1px solid var(--line)}h1{margin:0 0 4px;font-size:20px;word-break:break-all}.sub{color:var(--mut)}
nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 20px;display:flex;gap:14px;flex-wrap:wrap}
nav a{color:var(--acc);text-decoration:none}nav a:hover{text-decoration:underline}
main{padding:0 20px 40px;max-width:1200px}section{margin-top:26px}h2{font-size:16px;margin:0 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}code,pre,.mono{font:12.5px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace}code{word-break:break-all}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-weight:700;color:#fff}.TINGGI{background:var(--hi)}.SEDANG{background:var(--mid)}.RENDAH{background:var(--lo)}.TANPA{background:var(--ok)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0}.warn{border-left:4px solid var(--mid)}.bal{border-left:4px solid var(--ok)}
input[type=search]{width:100%;max-width:420px;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);margin:0 0 8px}
.pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;max-height:70vh;overflow:auto}.ln{white-space:pre-wrap;word-break:break-word}.ln.hit{background:rgba(255,200,0,.25)}
.mut{color:var(--mut)}ul{margin:4px 0;padding-left:20px}.kv td:first-child{width:160px;color:var(--mut)}
"""

_HTML_JS = """
(function(){
function flt(inp,rows,cnt){var q=inp.value.toLowerCase(),n=0;for(var i=0;i<rows.length;i++){var t=rows[i].textContent.toLowerCase();var ok=!q||t.indexOf(q)>-1;rows[i].style.display=ok?'':'none';if(ok)n++;}if(cnt)cnt.textContent=n+' / '+rows.length;}
var a=document.getElementById('q-imp');if(a){var r=document.querySelectorAll('#t-imp tbody tr'),c=document.getElementById('c-imp');a.addEventListener('input',function(){flt(a,r,c)});flt(a,r,c);}
var b=document.getElementById('q-txt');if(b){var l=document.querySelectorAll('#txt .ln'),c2=document.getElementById('c-txt');b.addEventListener('input',function(){var q=b.value.toLowerCase(),n=0;for(var i=0;i<l.length;i++){var ok=!q||l[i].textContent.toLowerCase().indexOf(q)>-1;l[i].style.display=ok?'':'none';l[i].className=(q&&ok)?'ln hit':'ln';if(ok)n++;}c2.textContent=n+' / '+l.length;});}
var s=document.getElementById('q-str');if(s){var r3=document.querySelectorAll('#ioc-list li'),c3=document.getElementById('c-str');s.addEventListener('input',function(){flt(s,r3,c3)});}
})();
"""


def _hesc(x) -> str:
    import html as _h
    return _h.escape(str(x), quote=True)


def triage_html(path, defang: bool = True, rep: dict | None = None) -> str:
    """Laporan HTML mandiri: ringkasan + skor, bagian / segmen, impor (bisa difilter), IOC dan artefak, kemampuan, perhatian, dan laporan teks penuh
    yang bisa dicari. Tanpa sumber luar. Hanya-baca; file sampel tidak dijalankan."""
    rep = rep or triage(path)
    E = _hesc
    ind = rep.get("ind") or {}
    pe, elf, mo = rep.get("pe"), rep.get("elf"), rep.get("macho")
    lvl = str(rep.get("level", ""))
    badge = lvl.split()[0] if lvl else "RENDAH"
    out: list[str] = []
    w = out.append

    def table(head, rows, cls=""):
        t = ["<div class=\"wrap\"><table%s><thead><tr>%s</tr></thead><tbody>" % ((" " + cls) if cls else "", "".join("<th>%s</th>" % E(h) for h in head))]
        for r_ in rows:
            t.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r_))
        t.append("</tbody></table></div>")
        return "".join(t)

    w("<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    w("<title>REA v%s - %s</title><style>%s</style></head><body>" % (E(VERSION), E(rep["name"]), _HTML_CSS))
    w("<header><h1>%s</h1><div class=\"sub\">%s &middot; %s &middot; REA v%s</div></header>" % (E(rep["name"]), E(rep["kind"]), E(_human(rep["size"])), E(VERSION)))
    nav = [("ringkasan", "Ringkasan"), ("bagian", "Bagian"), ("impor", "Impor"), ("ioc", "IOC &amp; artefak"), ("kemampuan", "Kemampuan"), ("teks", "Laporan teks")]
    w("<nav>%s</nav><main>" % "".join("<a href=\"#%s\">%s</a>" % (a_, b_) for a_, b_ in nav))

    # --- ringkasan
    w("<section id=\"ringkasan\"><h2>Ringkasan</h2>")
    w("<p><span class=\"badge %s\">%s</span> &nbsp; skor heuristik <b>%s</b> <span class=\"mut\">(petunjuk dari fakta terukur, bukan vonis)</span></p>" % (E(badge), E(lvl), E(rep["score"])))
    kv = [("SHA-256", rep["sha256"]), ("SHA-1", rep["sha1"]), ("MD5", rep["md5"]), ("Entropi", "%.2f / 8.00" % rep["entropy"])]
    if rep.get("ctph"):
        kv.append(("CTPH", rep["ctph"]))
    if pe and not pe.get("broken"):
        kv += [("Arsitektur PE", "%s, subsystem %s" % (pe.get("arch"), pe.get("subsys"))), ("Entry point", pe.get("entry")), ("Cap waktu", pe.get("stamp")), ("imphash", pe.get("imphash") or "-")]
    if elf:
        hd = elf.get("hard")
        kv.append(("ELF", "%d-bit %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"])))
        if hd:
            kv.append(("Mitigasi ELF", "PIE %s | RELRO %s | NX %s | canary %s | FORTIFY %s" % (hd["pie"], hd["relro"], hd["nx"], "ada" if hd["canary"] else "-", hd["fortify"] or "-")))
    if mo:
        kv.append(("Mach-O", "%s %s-bit %s" % (mo["arch"], mo["bits"], mo["type"])))
    w("<div class=\"wrap\"><table class=\"kv\"><tbody>%s</tbody></table></div>" % "".join("<tr><td>%s</td><td><code>%s</code></td></tr>" % (E(k), E(v)) for k, v in kv))
    if rep.get("why"):
        w("<div class=\"card\"><b>Alasan skor</b><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["why"]))
    if rep.get("balance"):
        w("<div class=\"card bal\"><b>Faktor penyeimbang</b> <span class=\"mut\">(lazim pada file sah; bukan jaminan aman)</span><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["balance"]))
    if rep.get("warn"):
        w("<div class=\"card warn\"><b>Perhatian</b><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["warn"][:40]))
    w("</section>")

    # --- bagian
    w("<section id=\"bagian\"><h2>Bagian / segmen</h2>")
    if pe and not pe.get("broken") and pe.get("sections"):
        w(table(["Nama", "VA", "Ukuran virtual", "Ukuran file", "Flag", "Entropi", "MD5"],
                [["<code>%s</code>" % E(x["name"]), "0x%X" % x["va"], E(_human(x["vsize"])), E(_human(x["rsize"])), E(x["flags"]), "%.2f" % x["ent"], "<code>%s</code>" % E(x.get("md5", ""))] for x in pe["sections"]]))
    elif elf and elf.get("sections"):
        w(table(["Nama", "Ukuran", "Flag", "Entropi"], [["<code>%s</code>" % E(x["name"] or "?"), E(_human(x["size"])), E(x["flags"]), "%.2f" % x["ent"]] for x in elf["sections"][:60] if x["name"]]))
    elif mo and mo.get("segments"):
        w(table(["Segmen", "Proteksi", "Ukuran file", "Entropi"], [["<code>%s</code>" % E(x["name"]), E(x["prot"]), E(_human(x["fsize"])), "%.2f" % x["ent"]] for x in mo["segments"]]))
    else:
        w("<p class=\"mut\">Tidak ada tabel bagian untuk jenis berkas ini.</p>")
    w("</section>")

    # --- impor
    rows: list[list[str]] = []
    if pe and not pe.get("broken") and pe.get("imports"):
        for dll, fns in pe["imports"].items():
            for f_ in (fns if isinstance(fns, (list, tuple)) else [fns]):
                rows.append([E(dll), "<code>%s</code>" % E(f_[0] if isinstance(f_, (list, tuple)) and f_ else f_)])
    elif elf and elf.get("dyn") and elf["dyn"].get("imports"):
        lib = ", ".join(elf["dyn"].get("needed", [])[:6]) or "(dinamis)"
        rows = [[E(lib), "<code>%s</code>" % E(x)] for x in elf["dyn"]["imports"]]
    elif mo and mo.get("imports"):
        rows = [[E("Mach-O"), "<code>%s</code>" % E(x)] for x in mo["imports"]]
    w("<section id=\"impor\"><h2>Impor (<span id=\"c-imp\">%d</span>)</h2>" % len(rows))
    if rows:
        w("<input type=\"search\" id=\"q-imp\" placeholder=\"Filter: nama DLL atau fungsi...\">")
        w(table(["Pustaka", "Fungsi"], rows[:6000], "id=\"t-imp\""))
        if len(rows) > 6000:
            w("<p class=\"mut\">Dipotong: 6000 dari %d baris.</p>" % len(rows))
    else:
        w("<p class=\"mut\">Tidak ada impor terbaca.</p>")
    w("</section>")

    # --- IOC & artefak
    items: list[tuple[str, str]] = []
    for lab, key, dfg in (("URL", "urls", True), ("IP kandidat", "ips", True), ("Email", "emails", True), ("Registry", "reg", False), ("Path", "paths", False)):
        for x in ind.get(key, []) or []:
            items.append((lab, _df(x, defang) if dfg else x))
    for x in ind.get("secrets", []) or []:
        items.append(("Kredensial (disamarkan)", x))
    for x in ind.get("secrets_typed", []) or []:
        items.append(("Rahasia berformat (disamarkan)", x))
    nt = ind.get("net") or {}
    for lab, key in (("User-Agent", "ua"), ("HTTP", "http"), ("Host", "hosts"), ("Header", "hdrs"), ("DNS ter-encode", "dns"), ("Proxy", "proxy"), ("Named pipe", "pipes")):
        for x in nt.get(key, []) or []:
            items.append((lab, _df(x, defang) if key in ("hosts", "dns") else x))
    if nt.get("certs"):
        items.append(("Sertifikat PEM", "%d tertanam" % nt["certs"]))
    for x in ind.get("pdb", []) or []:
        items.append(("Jejak PDB", x))
    cm = rep.get("com")
    if cm:
        for g in cm.get("groups", []):
            items.append(("Objek COM", "%s: %s" % (g["group"], ", ".join(g["names"]))))
    w("<section id=\"ioc\"><h2>IOC &amp; artefak (<span id=\"c-str\">%d</span>)</h2>" % len(items))
    if items:
        w("<input type=\"search\" id=\"q-str\" placeholder=\"Cari IOC / artefak...\"><ul id=\"ioc-list\" class=\"mono\">%s</ul>" % "".join("<li><b>%s</b>: <code>%s</code></li>" % (E(a_), E(_clean(b_))) for a_, b_ in items[:600]))
    else:
        w("<p class=\"mut\">Tidak ada IOC terdeteksi.</p>")
    w("</section>")

    # --- kemampuan
    caps = ind.get("caps") or {}
    w("<section id=\"kemampuan\"><h2>Indikasi kemampuan</h2>")
    if caps:
        w("<ul>%s</ul>" % "".join("<li>%s%s</li>" % (E(_clean(_cap_text(ind, c_, h_))), (" <span class=\"mut\">(%s)</span>" % E(ATTACK[c_])) if c_ in ATTACK and _cap_strong(ind, c_) else "") for c_, h_ in caps.items()))
        w("<p class=\"mut\">Petunjuk dari nama API / string, bukan bukti perilaku.</p>")
    else:
        w("<p class=\"mut\">Tidak ada indikasi.</p>")
    w("</section>")

    # --- teks penuh
    txt = _render(rep, False, defang)
    lines = txt.splitlines()[:4000]
    w("<section id=\"teks\"><h2>Laporan teks penuh (<span id=\"c-txt\">%d</span>)</h2><input type=\"search\" id=\"q-txt\" placeholder=\"Cari di laporan...\">" % len(lines))
    w("<div class=\"pre mono\" id=\"txt\">%s</div></section>" % "".join("<div class=\"ln\">%s</div>" % E(x) for x in lines))
    w("</main><script>%s</script></body></html>" % _HTML_JS)
    return "".join(out)


def triage_html_file(path, out=None, defang: bool = True) -> str:
    """Tulis laporan HTML ke `out` (bawaan: <nama>.rea.html di folder kerja); kembalikan path-nya."""
    rep = triage(path)
    target = Path(out) if out else Path.cwd() / (Path(path).name + ".rea.html")
    _write_atomic_nofollow(target, triage_html(path, defang, rep=rep).encode("utf-8"), 0o644)   # v104: tidak menulis lewat symlink
    return str(target)


def triage_md(path, defang: bool = True) -> str:
    """Laporan Markdown siap simpan / tempel: ringkasan, skor, kemampuan, IOC, draf YARA. Hanya-baca."""
    try:
        rep = triage(path)
    except Exception as e:
        return "# Triase gagal\n\n`%s: %s`" % (type(e).__name__, str(e)[:120])
    ind = rep["ind"]
    L = ["# Laporan Triase REA v%s: %s" % (VERSION, _clean(rep["name"])), "",
         "| Hal | Nilai |", "|---|---|", "| Jenis | %s |" % _clean(rep["kind"]).replace("|", "/"), "| Ukuran | %s |" % _human(rep["size"]),
         "| SHA-256 | `%s` |" % rep["sha256"], "| SHA-1 | `%s` |" % rep["sha1"], "| MD5 | `%s` |" % rep["md5"],
         "| Entropi | %.2f / 8.00 |" % rep["entropy"]]
    if rep.get("ctph"):
        L.append("| CTPH | `%s` |" % rep["ctph"])
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append("| imphash | `%s` |" % pe["imphash"])
    L += ["", "## Skor heuristik: %d (%s)" % (rep["score"], rep["level"]), "", "_Petunjuk dari fakta terukur, bukan vonis._", ""]
    L += ["- " + _clean(x) for x in rep["why"]] or ["- tidak ada tanda"]
    if rep.get("balance"):
        L += ["", "**Faktor penyeimbang** (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + _clean("; ".join(rep["balance"]))]
    if ind["caps"]:
        L += ["", "## Indikasi kemampuan", ""]
        for cap, hit in ind["caps"].items():
            L.append("- **%s**%s" % (_clean(_cap_text(ind, cap, hit)), (" (%s)" % ATTACK[cap]) if cap in ATTACK and _cap_strong(ind, cap) else ""))
    if rep["warn"]:
        L += ["", "## Perhatian", ""] + ["- " + _clean(x) for x in rep["warn"][:25]]
    for lab, key in (("URL", "urls"), ("IP kandidat", "ips"), ("Email", "emails"), ("Registry", "reg")):
        if ind[key]:
            L += ["", "## %s" % lab, ""] + ["- `%s`" % _clean(_df(x, defang)) for x in ind[key][:25]]
    if rep.get("pack"):
        L += ["", "## Kemasan / toolchain", ""] + ["- " + _clean(x) for x in rep["pack"]]
    go = rep.get("go")
    if go:
        L += ["", "## Fungsi Go (pclntab %s)" % _clean(go["ver"]), "", "- %d fungsi, %d paket, %d fungsi paket `main`%s" % (go["nfunc"], go["n_pkgs"], go["n_main"], " (dipotong)" if go["truncated"] else "")]
        L += ["- `%s`" % _clean(x["name"]) for x in go["main"][:30]]
        if go["third"]:
            L.append("- paket pihak ketiga: " + ", ".join("`%s` (%d)" % (_clean(p), c) for p, c in go["third"][:10]))
    for label, hint in rep.get("tools", []):
        L.append("- %s: %s" % (_clean(label), _clean(hint)))
    rl = rep.get("relab")
    if rl:
        L += ["", "## RE Lab", "", "%s, base %s: %d fungsi, %d panggilan API terpetakan, %d string dirujuk kode." % (rl["arch"], rl["image_base"], rl["n_functions"], rl["n_api_sites"], rl["n_strrefs"]), ""]
        if rl["functions"]:
            L += ["| Fungsi | VA | Ukuran | Skor | Kemampuan | API |", "|---|---|---|---|---|---|"]
            for f in rl["functions"][:10]:
                L.append("| %s | %s | %s | %d | %s | %s |" % (_clean(f["name"]).replace("|", "/"), f["va"], _human(f["size"]), f["score"], "; ".join(f["tags"]) or "-", ", ".join(x.split("!")[-1] for x in f["apis"][:6]) or "-"))
        L += ["- anti-analisis: %s x%d" % (_clean(x["technique"]), x["count"]) for x in rl["anti"]]
        L += ["- stack string: `%s` [%s]" % (_clean(x["text"]), x["tag"]) for x in rl["stack_strings"][:6]]
        L += ["- API hash: %s" % ", ".join(h["api"] for h in rl["api_hashes"][:6])] if rl["api_hashes"] else []
    L += ["", "## Draf YARA (WAJIB diuji terhadap file sah)", "", "```yara", yara_draft(rep), "```", "",
          "---", "REA v%s | by: %s | dihitung statis dari bytes file, tanpa menjalankannya." % (VERSION, AUTHOR)]
    return "\n".join(L)


