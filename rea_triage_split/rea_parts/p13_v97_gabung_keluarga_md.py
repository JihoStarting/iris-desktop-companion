# rea_triage bagian 13/47: v97_gabung_keluarga_md (baris asli 4458-4614). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ----------------------------- penggabung v97 -------------------------------


def _v97_enrich(d: bytes, size: int, rep: dict, fuzzy: bool, f=None) -> None:
    w = rep["warn"]
    zp, mo, dn = rep.get("zip"), rep.get("macho"), rep.get("dotnet")
    if mo:
        w.extend(mo["warn"])
    if dn:
        for x in dn["obf"]:
            w.append(".NET: " + x)
    try:
        rep["pack"] = _pack_details(d, size) if not zp else []
    except Exception as e:
        rep["pack"] = []
        w.append("analisis kemasan gagal: %s" % type(e).__name__)
    try:
        rep["go"] = _go_pclntab(d, f, size) if not zp else None
    except Exception as e:
        rep["go"] = None
        w.append("pemulihan nama fungsi Go gagal: %s" % type(e).__name__)
    try:
        rep["xor"] = _xor_hunt(d) if not zp else []
    except Exception as e:
        rep["xor"] = []
        w.append("perburuan XOR gagal: %s" % type(e).__name__)
    for x in rep["xor"][:2]:
        w.append("kata kunci tersembunyi setelah dekode %s 0x%02X: %s (kemungkinan string / payload terenkode satu byte)" % (x["op"], x["key"], ", ".join(x["words"])))
    try:
        rep["xor_multi"] = _xor_multi(d) if not zp else []
    except Exception as e:
        rep["xor_multi"] = []
        w.append("perburuan XOR kunci berulang gagal: %s" % type(e).__name__)
    for x in rep["xor_multi"][:2]:
        w.append("stub DOS terenkode XOR kunci berulang %d byte (%s) di offset 0x%X%s" % (x["k"], x["key"], x["off"], "; MZ terkonfirmasi: PE tersembunyi" if x["mz"] else ""))
    for x in (dn or {}).get("mres", []):
        if x["mz"]:
            w.append("resource terkelola .NET berisi executable (MZ, %s) di offset 0x%X" % (_human(x["size"]), x["off"]))
        elif x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")):
            w.append("resource terkelola .NET berentropi %.2f (%s) di offset 0x%X: kemungkinan payload terenkripsi / terkompres" % (x["ent"], _human(x["size"]), x["off"]))
    rep["ctph"] = ""
    if fuzzy and not zp:
        try:
            rep["ctph"] = ctph(d[:CTPH_SAMPLE])
        except Exception as e:
            w.append("CTPH gagal: %s" % type(e).__name__)
    _mcfg_enrich(d, rep, (rep.get("pe") if rep.get("pe") and not rep["pe"].get("broken") else None), dn, zp)   # v99.19 [A1]; kunci baru rep["malcfg"], aditif


def _render_v97(rep: dict, a, compact: bool, defang: bool) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        a("Mach-O : %s %s-bit %s, %s%s | entry: %s | tanda tangan: %s | PIE: %s%s" % (
            mo["arch"], mo["bits"], mo["type"], mo["endian"] + "-endian", (" | " + mo["platform"]) if mo["platform"] else "",
            mo["entry"] or "-", "ada" if mo["signed"] else "tidak ada", "ya" if mo["pie"] else "tidak", " | TERENKRIPSI" if mo["encrypted"] else ""))
        if mo["fat"] and len(mo["fat"]) > 1:
            a("   universal: " + ", ".join("%s (%s)" % (x[0], _human(x[2])) for x in mo["fat"][:6]))
        if not compact:
            if mo["dylibs"] or mo["weak"]:
                a("   dylib (%d): %s%s" % (len(mo["dylibs"]) + len(mo["weak"]), ", ".join(mo["dylibs"][:10]), (" | lemah: " + ", ".join(mo["weak"][:4])) if mo["weak"] else ""))
            sg = mo.get("sig")
            if sg:
                a("   code signing: hardened runtime %s | ad-hoc %s | sandbox %s | entitlements %s" % (
                    "ya" if sg["runtime"] else "tidak", "ya" if sg["adhoc"] else "tidak", "ya" if sg["sandbox"] else "tidak",
                    ("%d kunci" % len(sg["keys"])) if sg["has_ent"] else "tidak ada"))
                if sg["keys"]:
                    a("   entitlements: " + ", ".join(sg["keys"][:12]))
            if mo["rpaths"]:
                a("   RPATH: " + ", ".join(mo["rpaths"][:4]))
            if mo["segments"]:
                a("   segmen: " + ", ".join("%s %s %.1f" % (s["name"], s["prot"], s["ent"]) for s in mo["segments"][:8]))
            if mo["imports"]:
                a("   simbol impor (%d): %s" % (len(mo["imports"]), ", ".join(mo["imports"][:25])))
            if mo["uuid"]:
                a("   UUID: " + mo["uuid"])
    cm = rep.get("com")
    if cm and (cm["groups"] or cm["apis"]):
        a("Objek COM (dari GUID CLSID / IID): " + "; ".join("%s [%s]%s" % (g["group"], ", ".join(g["names"][:3 if compact else 5]), "" if compact else " (%s)" % g["how"]) for g in cm["groups"]) if cm["groups"] else "Objek COM: tidak ada GUID yang dikenal")
        if cm["apis"]:
            a("   API COM diimpor: " + ", ".join(cm["apis"]))
        if cm["unknown"] and not compact:
            a("   GUID lain berbentuk string (tidak ada di daftar, %d): %s" % (len(cm["unknown"]), ", ".join(cm["unknown"][:4])))
    if dn:
        a(".NET   : runtime %s | %s%s | %d nama di #Strings | %d string pengguna (#US)" % (
            dn["runtime"], "IL murni" if dn["ilonly"] else "campuran (ada native)", ", strong-name" if dn["strong"] else "", dn["n_names"], len(dn["us"])))
        if not compact:
            a("   stream: " + ", ".join("%s (%s)" % (n, _human(s)) for n, s in dn["streams"][:8]))
            hot = [u for u in dn["us"] if re.search(r"(?i)https?://|\\\\|\.exe|\.dll|powershell|cmd|\.onion|password|token|key", u)][:8]
            if hot:
                a("   string pengguna menarik: " + " | ".join(_df(x, defang) for x in hot))
    for line in rep.get("pack") or []:
        a("Kemasan: " + line)
    go = rep.get("go")
    if go:
        a("Go     : pclntab %s (%d-bit) di offset 0x%X | %d fungsi%s | %d paket | %d fungsi paket main" % (
            go["ver"], go["bits"], go["off"], go["nfunc"], (" (terbaca %d%s)" % (go["read"], "; berkas dipindai sebagian" if go.get("partial_scan") else ", dipotong")) if (go["truncated"] or go.get("partial_scan")) else "", go["n_pkgs"], go["n_main"]))
        if go["main"]:
            a("   fungsi main: " + ", ".join(_clean(x["name"]) for x in go["main"][: (6 if compact else 20)]) + (" ..." if go["n_main"] > (6 if compact else 20) else ""))
        if not compact:
            if go["third"]:
                a("   paket pihak ketiga: " + ", ".join("%s (%d)" % (_clean(p), c) for p, c in go["third"][:10]))
            if go["std"]:
                a("   paket pustaka standar yang layak dicek: " + ", ".join(_clean(x) for x in go["std"]))
            if go["flagged"]:
                a("   nama paket yang layak dicek: " + ", ".join(_clean(x) for x in go["flagged"]))
    for x in (rep.get("xor") or [])[: (1 if compact else 4)]:
        a("Perburuan satu-byte: %s kunci 0x%02X -> %s%s" % (x["op"], x["key"], ", ".join(x["words"]), (" | URL: " + " | ".join(_df(u, defang) for u in x["urls"])) if x["urls"] else ""))
    _render_mcfg(rep.get("malcfg"), a, compact, defang)   # v99.19 [A1]
    if rep.get("ctph") and not compact:
        a("CTPH   : %s%s" % (rep["ctph"], " (sampel %s pertama)" % _human(CTPH_SAMPLE) if rep["size"] > CTPH_SAMPLE else ""))


def _score_v97(rep: dict, add) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        if any(s["prot"][1:] == "WX" for s in mo["segments"]):
            add(1, "segmen Mach-O W+X")
        if any(s["ent"] > 7.2 and s["fsize"] > 16384 and s["name"] != "__LINKEDIT" for s in mo["segments"]) and not mo["encrypted"]:
            add(1, "segmen Mach-O berentropi tinggi")
    if dn and dn["obf"]:
        add(2, "metadata .NET menunjukkan obfuskasi")
    x = rep.get("xor") or []
    if x:
        strong = any(w_ in ("This program cannot be run", "https://", "http://", "powershell", "cmd.exe") for r_ in x for w_ in r_["words"])
        add(3 if strong else 1, "kata kunci tersembunyi di balik dekode satu-byte")


# ----------------------------- keluarga sampel (folder) ---------------------


def _families(items: list[dict], fuzzy: bool) -> list[dict]:
    fam: list[dict] = []
    for key, label in (("imphash", "imphash sama"), ("rich", "rich header sama"), ("macho_uuid", "UUID Mach-O sama")):
        g: dict[str, list[str]] = {}
        for it in items:
            if it.get(key):
                g.setdefault(it[key], []).append(it["rel"])
        fam += [{"basis": label, "members": v} for v in g.values() if len(v) > 1]
    if fuzzy:
        cand = [it for it in items if it.get("ctph")][:150]
        seen: set[int] = set()
        for i, x in enumerate(cand):
            if i in seen:
                continue
            grp = [x["rel"]]
            for j in range(i + 1, len(cand)):
                if j not in seen and cand[j]["sha256"] != x["sha256"] and ctph_compare(x["ctph"], cand[j]["ctph"]) >= 70:
                    grp.append(cand[j]["rel"])
                    seen.add(j)
            if len(grp) > 1:
                fam.append({"basis": "CTPH >= 70", "members": grp})
    return fam[:12]


# ----------------------------- laporan Markdown -----------------------------


