# rea_triage bagian 27/47: android_dekoder (baris asli 11114-11305). Dijalankan oleh rea_triage.py dalam namespace bersama; bukan modul mandiri.
# ---------------------------------------------------------------------------
# v98.3: Android lebih dalam (AndroidManifest.xml biner + metode DEX), dekoder skrip / string tersandi, hash ikon PE,
#        dan pemindaian YARA opsional (butuh yara-python; tanpa itu tidak ada yang berubah). Statis, hanya baca.
# ---------------------------------------------------------------------------

_AXML_COMP = ("activity", "activity-alias", "service", "receiver", "provider")


def _axml_strings(d: bytes, off: int) -> list[str]:
    """Baca string pool (RES_STRING_POOL_TYPE) di offset `off`. Batas: 20000 string."""
    _t, hs, csz, n, _ns, flags, sstart, _st = struct.unpack_from("<HHIIIIII", d, off)
    n = min(n, 20000)
    utf8 = bool(flags & 0x100)
    out = []
    base = off + sstart
    for i in range(n):
        p = off + hs + 4 * i
        if p + 4 > len(d):
            break
        o = base + struct.unpack_from("<I", d, p)[0]
        if o >= len(d):
            out.append("")
            continue
        try:
            if utf8:
                l1 = d[o]
                o += 2 if l1 & 0x80 else 1
                b1 = d[o]
                if b1 & 0x80:
                    ln = ((b1 & 0x7F) << 8) | d[o + 1]
                    o += 2
                else:
                    ln = b1
                    o += 1
                out.append(d[o:o + min(ln, 600)].decode("utf-8", "replace"))
            else:
                ln = struct.unpack_from("<H", d, o)[0]
                o += 2
                if ln & 0x8000:
                    ln = ((ln & 0x7FFF) << 16) | struct.unpack_from("<H", d, o)[0]
                    o += 2
                out.append(d[o:o + 2 * min(ln, 600)].decode("utf-16le", "replace"))
        except (IndexError, struct.error):
            out.append("")
    return out


def _axml_summary(d: bytes) -> dict | None:
    """Uraikan AndroidManifest.xml biner (AXML) menjadi ringkasan: paket, versi, SDK, komponen, aksi intent, izin."""
    if len(d) < 16 or struct.unpack_from("<H", d, 0)[0] != 0x0003:
        return None
    total = min(struct.unpack_from("<I", d, 4)[0], len(d))
    pos, strings = struct.unpack_from("<H", d, 2)[0], []
    info: dict = {"package": "", "version": "", "min_sdk": "", "target_sdk": "", "debuggable": None, "cleartext": None, "backup": None,
                  "components": {k: [] for k in _AXML_COMP}, "exported": [], "actions": [], "perms": [], "app_class": ""}
    stack: list[str] = []
    n_el = 0
    while pos + 8 <= total and n_el < 20000:
        ct, hs, csz = struct.unpack_from("<HHI", d, pos)
        if csz < 8 or pos + csz > len(d):
            break
        if ct == 0x0001:
            strings = _axml_strings(d, pos)
        elif ct == 0x0102 and csz >= 36:
            n_el += 1
            nm_i = struct.unpack_from("<I", d, pos + 20)[0]
            a_start, a_size, a_cnt = struct.unpack_from("<HHH", d, pos + 24)
            tag = strings[nm_i] if nm_i < len(strings) else "?"
            attrs = {}
            for k in range(min(a_cnt, 64)):
                ap = pos + 16 + a_start + k * (a_size or 20)
                if ap + 20 > len(d):
                    break
                _ans, an, raw, _sz, _r0, dtype, data = struct.unpack_from("<IIIHBBI", d, ap)
                key = strings[an] if an < len(strings) else "?"
                if raw != 0xFFFFFFFF and raw < len(strings):
                    val = strings[raw]
                elif dtype == 0x03 and data < len(strings):
                    val = strings[data]
                elif dtype == 0x12:
                    val = "true" if data else "false"
                elif dtype == 0x10:
                    val = str(data if data < 0x80000000 else data - (1 << 32))
                elif dtype == 0x11:
                    val = "0x%X" % data
                else:
                    val = "@0x%X" % data
                attrs[key] = val
            stack.append(tag)
            if tag == "manifest":
                info["package"] = attrs.get("package", "")
                info["version"] = "%s (%s)" % (attrs.get("versionName", "?"), attrs.get("versionCode", "?"))
            elif tag == "uses-sdk":
                info["min_sdk"], info["target_sdk"] = attrs.get("minSdkVersion", ""), attrs.get("targetSdkVersion", "")
            elif tag == "application":
                info["debuggable"] = attrs.get("debuggable")
                info["cleartext"] = attrs.get("usesCleartextTraffic")
                info["backup"] = attrs.get("allowBackup")
                info["app_class"] = attrs.get("name", "")
            elif tag in ("uses-permission", "uses-permission-sdk-23", "permission") and attrs.get("name"):
                info["perms"].append(attrs["name"])
            elif tag in _AXML_COMP:
                nm = attrs.get("name", "?")
                if len(info["components"][tag]) < 60:
                    info["components"][tag].append(nm)
                if attrs.get("exported") == "true" and len(info["exported"]) < 40:
                    info["exported"].append("%s %s" % (tag, nm))
            elif tag == "action" and attrs.get("name") and attrs["name"] not in info["actions"] and len(info["actions"]) < 60:
                info["actions"].append(attrs["name"])
        elif ct == 0x0103 and stack:
            stack.pop()
        pos += csz
    info["perms"] = sorted(set(info["perms"]))[:80]
    return info if (info["package"] or info["perms"] or any(info["components"].values())) else None


_DEX_API = {   # kelompok -> potongan "Lkelas;->metode" (cocok sebagian pada string metode)
    "kirim / baca SMS": ("Landroid/telephony/SmsManager;->sendTextMessage", "Landroid/telephony/SmsManager;->sendMultipartTextMessage", "Landroid/telephony/SmsMessage;->createFromPdu"),
    "identitas perangkat": ("TelephonyManager;->getDeviceId", "TelephonyManager;->getImei", "TelephonyManager;->getSubscriberId", "TelephonyManager;->getLine1Number", "Settings$Secure;->getString"),
    "muat kode dinamis": ("Ldalvik/system/DexClassLoader;-><init>", "Ldalvik/system/PathClassLoader;-><init>", "Ldalvik/system/InMemoryDexClassLoader;-><init>", "Ljava/lang/ClassLoader;->loadClass"),
    "eksekusi perintah": ("Ljava/lang/Runtime;->exec", "Ljava/lang/ProcessBuilder;->start"),
    "refleksi": ("Ljava/lang/reflect/Method;->invoke", "Ljava/lang/Class;->forName", "Ljava/lang/Class;->getDeclaredMethod"),
    "kripto": ("Ljavax/crypto/Cipher;->doFinal", "Ljavax/crypto/Cipher;->getInstance", "Ljavax/crypto/spec/SecretKeySpec;-><init>"),
    "aksesibilitas / overlay": ("AccessibilityService;->performGlobalAction", "AccessibilityNodeInfo;->performAction", "WindowManager;->addView"),
    "admin perangkat": ("DevicePolicyManager;->lockNow", "DevicePolicyManager;->resetPassword", "DevicePolicyManager;->wipeData"),
    "pasang paket": ("PackageInstaller;->createSession", "PackageManager;->installPackage", "Landroid/content/Intent;->setDataAndType"),
    "rekam audio / kamera": ("Landroid/media/MediaRecorder;->start", "Landroid/media/AudioRecord;->startRecording", "Landroid/hardware/Camera;->open"),
    "lokasi": ("LocationManager;->getLastKnownLocation", "LocationManager;->requestLocationUpdates"),
    "WebView + JS": ("WebView;->addJavascriptInterface", "WebSettings;->setJavaScriptEnabled"),
    "kontak / log panggilan": ("ContentResolver;->query",),
    "anti-analisis": ("Landroid/os/Debug;->isDebuggerConnected", "Landroid/os/Build;->FINGERPRINT", "Landroid/provider/Settings$Global;->getInt"),
}


def _uleb(d: bytes, o: int) -> tuple[int, int]:
    v, sh = 0, 0
    while o < len(d) and sh < 35:
        b = d[o]
        o += 1
        v |= (b & 0x7F) << sh
        if not b & 0x80:
            break
        sh += 7
    return v, o


def _dex_scan(d: bytes) -> dict | None:
    """Ringkasan DEX: jumlah string / tipe / metode / kelas, panggilan API Android sensitif dari tabel method_ids, dugaan obfuskasi."""
    if len(d) < 0x70 or d[:4] != b"dex\n":
        return None
    ss, so, ts, to, _ps, _po, _fs, _fo, ms, mo, cs, _co = struct.unpack_from("<12I", d, 0x38)
    ss, ts, ms = min(ss, 200000), min(ts, 200000), min(ms, 300000)

    cache: dict[int, str] = {}

    def sget(i: int) -> str:
        if i in cache:
            return cache[i]
        r = ""
        if 0 <= i < ss and so + 4 * i + 4 <= len(d):
            o = struct.unpack_from("<I", d, so + 4 * i)[0]
            if o < len(d):
                n, p = _uleb(d, o)
                r = d[p:p + min(n * 3, 400)].split(b"\0")[0].decode("utf-8", "replace")
        cache[i] = r
        return r

    types = []
    for i in range(ts):
        if to + 4 * i + 4 > len(d):
            break
        types.append(sget(struct.unpack_from("<I", d, to + 4 * i)[0]))
    meths = []
    for i in range(ms):
        p = mo + 8 * i
        if p + 8 > len(d):
            break
        ci, _pi, ni = struct.unpack_from("<HHI", d, p)
        meths.append("%s->%s" % (types[ci] if ci < len(types) else "?", sget(ni)))
    hits: dict[str, list[str]] = {}
    for m in meths:
        for grp, keys in _DEX_API.items():
            if any(k in m for k in keys):
                lst = hits.setdefault(grp, [])
                if len(lst) < 6 and m not in lst:
                    lst.append(m)
    app_types = [t for t in types if t.startswith("L") and not t.startswith(("Landroid", "Ljava", "Ljavax", "Lkotlin", "Landroidx", "Lcom/google", "Lorg/", "Ldalvik"))]
    short = sum(1 for t in app_types if len(t.rstrip(";").split("/")[-1]) <= 2)
    return {"strings": ss, "types": ts, "methods": ms, "classes": cs, "hits": hits,
            "obf": bool(len(app_types) >= 20 and short / len(app_types) > 0.5), "app_types": len(app_types)}


