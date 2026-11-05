const { app, BrowserWindow, WebContentsView, ipcMain, screen, globalShortcut, session, protocol, net, Tray, Menu, nativeImage, desktopCapturer, clipboard, shell, powerMonitor } = require('electron');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { spawn } = require('child_process');
const os = require('os');

// Audio dari server harus bisa diputar tanpa klik dulu
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

// Origin yang diizinkan server.py (halaman tes yang berhasil dibuka dari sini)
const SERVER_ORIGIN = 'http://localhost:8765';

// v28: token /ws. Server menolak koneksi tanpa header X-Iris-Token yang sama dengan COMPANION_TOKEN. Token dibaca di sini (proses utama),
// dari environment atau dari ~/.env (kalau tidak ada, .env di folder ini; urutan sama dengan server.py), lalu ditempel ke header
// handshake WebSocket di bawah. Halaman overlay (renderer) tidak pernah melihatnya, dan nilainya tidak pernah dicetak.
function readEnvFileVar(file, name) {
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch { return ''; }
  let val = '';
  for (const line of text.split(/\r?\n/)) {
    const m = /^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/.exec(line);
    if (!m || m[1] !== name) continue;
    let v = m[2].trim();
    if (v.length >= 2 && ((v[0] === '"' && v[v.length - 1] === '"') || (v[0] === "'" && v[v.length - 1] === "'"))) v = v.slice(1, -1);
    else v = v.replace(/\s+#.*$/, '').trim();
    val = v;   // kalau ada beberapa baris, yang terakhir menang (seperti python-dotenv)
  }
  return val;
}
let COMPANION_TOKEN_SRC = '';   // v39b: asal token (untuk diagnosa)
function loadCompanionToken() {
  const fromEnv = (process.env.COMPANION_TOKEN || '').trim();
  if (fromEnv) { COMPANION_TOKEN_SRC = 'variabel environment COMPANION_TOKEN'; return fromEnv; }
  const file = [path.join(os.homedir(), '.env'), path.join(__dirname, '.env')].find((f) => fs.existsSync(f));
  COMPANION_TOKEN_SRC = file || '(tidak ada file .env di ' + os.homedir() + ' maupun ' + __dirname + ')';
  return file ? readEnvFileVar(file, 'COMPANION_TOKEN') : '';
}
const COMPANION_TOKEN = loadCompanionToken();
// v39b: sidik 6 hex (SHA-256) supaya bisa dicocokkan dengan baris "Token /ws server" di terminal server.py, tanpa mencetak isi token
const tokenFp = (v) => require('crypto').createHash('sha256').update(v, 'utf8').digest('hex').slice(0, 6);
console.log(COMPANION_TOKEN
  ? `Token /ws: terbaca (${COMPANION_TOKEN.length} karakter, sidik ${tokenFp(COMPANION_TOKEN)}) dari ${COMPANION_TOKEN_SRC}; Electron berjalan di ${process.platform}`
  : `Token /ws: tidak ada (COMPANION_TOKEN kosong; dicari di ${COMPANION_TOKEN_SRC}; Electron di ${process.platform}). Server harus tanpa token juga, atau koneksi ditolak.`);

const BASE_W = 440;    // lebar jendela lama: padding kiri 12 + ruang kiri + karakter 320 + padding kanan 12
const RIGHT_PAD = 200; // v31c: ruang kosong tambahan di KANAN karakter (tembus klik) supaya bubble bisa muncul di samping kepala saat karakter di pojok kiri layar. Samakan dengan --rpad di index.html
const WIN_W = BASE_W + RIGHT_PAD;
const WIN_H = 620; // lebih tinggi dari sebelumnya (560) untuk ruang avatar
const CHAT_EXTRA = 220; // v32: tinggi tambahan maksimum saat kotak chat dipanjangkan (dibatasi ruang di atas jendela)
const CHAT_GROW = 160; // tinggi tambahan saat panel chat dibuka (panel 150 + jarak 10); samakan dengan #log di index.html
const TRAY_ICON = path.join(__dirname, 'assets', 'tray.png');

// Protokol app:// supaya halaman bisa fetch model .vrm dan memuat modul ES
// (fetch ke file:// diblokir Chromium). Harus didaftarkan sebelum app ready.
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true },
  },
]);

// Hanya satu salinan overlay (dua salinan = pintasan global bentrok dan karakter dobel).
// Pola dari AIRI (single-instance guard).
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) app.quit();

let win = null;
let tray = null;
let saveTimer = null;
let chatExtra = 0;  // v32: tambahan tinggi (di luar CHAT_GROW) saat kotak chat dipanjangkan; v35b: ke bawah, ikut masuk ke chatGrow saja (chatShift tidak berubah)
let chatGrow = 0;   // tambahan tinggi jendela yang sedang aktif (0 = chat tertutup)
let chatShift = 0;  // seberapa jauh jendela digeser ke atas saat memanjang

/* ---------- /chrome: mini-browser multi-akun (fase 1 sampai 3 di iris-03-roadmap-mini-browser.md) ----------
   Panel web = WebContentsView terpisah (proses sendiri, TANPA preload dan nodeIntegration, sandbox) di sebelah kiri karakter.
   Saat dibuka, jendela overlay melebar ke kiri sebesar panel (tepi kanan tetap, jadi karakter tidak bergeser); ditutup = kembali.
   Tiap akun punya partisi persist:<nama>: login tersimpan dan tidak tercampur. Hanya satu akun hidup: ganti akun = tab lama ditutup
   dan prosesnya dibuang, lalu link awal akun baru dimuat. Link hanya https (atau http untuk localhost). Izin kamera/mikrofon/notifikasi ditolak.
   Konfigurasi: iris-accounts.json di folder userData (dibuat otomatis; dicetak di terminal), sepuluh slot. */
const WEB_W = 420, WEB_H = 520, WEB_MARGIN = 12;
// v52: ukuran panel bisa dibesarkan (/chrome besar | kecil | ukuran, atau tombol di bilah alamat). Besar = lebih lebar (jendela melebar) dan lebih tinggi (jendela memanjang ke ATAS, dibatasi ruang di atas jendela).
const WEB_W_BIG = 640, WEB_H_BIG = 720;
let webBig = false, webExtraH = 0;   // webExtraH = tinggi tambahan jendela yang sedang dipakai panel besar
const WEB_W_MIN = 320, WEB_W_MAX = 1000, WEB_H_MIN = 320, WEB_H_MAX = 1100;
let webWc = WEB_W, webHc = WEB_H;   // ukuran panel sekarang (bisa ditarik bebas lewat pegangan ⤡, atau besar / kecil)
const webW = () => webWc;
const webH = () => webHc;
const WEB_TB = 40;   // fase 4e: bilah alat (34 px + celah 6 px) di atas panel; digambar oleh index.html (#webbar), samakan dengan --webh di sana
const ACCT_SLOTS = 10;   // jumlah slot akun (berkas lama yang hanya berisi 5 akun otomatis dilengkapi slot kosong)
const ACCOUNTS_FILE = () => path.join(app.getPath('userData'), 'iris-accounts.json');
const ACCT_DEFAULT = { akun: [
  { nama: 'kuliah', link: null },
  { nama: 'google', link: null, partisi: 'persist:fase0' },   // memakai login hasil uji fase 0
  null, null, null,
] };
let webPanel = null, webAcct = null, webLast = 1, webExtra = 0, webHover = false, lastIgnoreReq = true;
const WEB_OFF_X = -(WEB_W_MAX + WEB_MARGIN);   // di luar tepi kiri jendela (terpotong): posisi awal / akhir animasi
let webX = WEB_MARGIN, webAnimIv = null, webClosing = false, webOpenT = null;
// v48: sisi panel /chrome. 'left' = di kiri karakter (jendela melebar ke kiri); 'right' = di kanan karakter (jendela melebar ke kanan), dipakai kalau tidak ada ruang di kiri (Iris mentok kiri layar)
let webSide = 'left';
const WEB_RIGHT_X = 440;   // x panel di mode kanan = BASE_W (tepi kanan karakter 428 + jarak 12)
const webHome = () => (webSide === 'right' ? WEB_RIGHT_X : WEB_MARGIN);
const webOff = () => { try { return webSide === 'right' ? win.getContentBounds().width : -(webWc + WEB_MARGIN + 8); } catch { return WEB_OFF_X; } };   // tepat di luar tepi jendela (jarak tempuh = lebar panel, bukan lebar maksimum)
const webLeftExtra = () => (webSide === 'left' ? webExtra : 0);   // lebar tambahan yang menggeser pojok kiri jendela
const WEB_SETTLE = 220;   // ms jeda antara mengubah lebar jendela dan membuat / membuang panel
const webSessions = new Set();
const webPopups = new Set();   // popup login Google yang sedang terbuka (jendela anak panel)
// Tab akun yang sudah dibuka tetap hidup (disembunyikan, bukan dibuang) supaya kembali ke halaman terakhir, tidak ke link awal.
// Batas jumlah tab hidup (termasuk yang tampil) = IRIS_WEB_KEEP, bawaan 3; yang paling lama tidak dipakai dibuang dulu. 1 = perilaku lama (satu akun hidup).
const WEB_KEEP = Math.max(1, Math.min(10, parseInt(process.env.IRIS_WEB_KEEP || '3', 10) || 3));
const webParked = new Map();   // partisi -> { view, acct }; urutan Map = yang paling lama tidak dipakai di depan
const isWebPanel = (wc) => !!wc && webSessions.size > 0 && webSessions.has(wc.session);
function webPanelUrlOk(u) {
  try {
    const x = new URL(u);
    if (x.protocol === 'https:') return true;
    return x.protocol === 'http:' && ['localhost', '127.0.0.1', '[::1]'].includes(x.hostname);
  } catch { return false; }
}
const normUrl = (u) => (/^[a-z][a-z0-9+.-]*:\/\//i.test(u) ? u : 'https://' + u);
// Halaman "tab baru": link awal akun yang belum punya link. Electron tidak punya halaman tab baru bawaan, jadi dipakai halaman pencarian. Ganti lewat environment IRIS_NEWTAB_URL.
const NEWTAB_URL = (() => { const u = (process.env.IRIS_NEWTAB_URL || '').trim(); return u && webPanelUrlOk(normUrl(u)) ? normUrl(u) : 'https://www.google.com/'; })();
const shortUrl = (u) => { try { const x = new URL(u); return x.origin + x.pathname; } catch { return String(u || '').slice(0, 80); } };   // tanpa query: bisa berisi token
function webSessionFor(part) {
  const ss = session.fromPartition(part);
  if (!webSessions.has(ss)) {
    webSessions.add(ss);
    ss.setPermissionRequestHandler((_wc, _perm, cb) => cb(false));
    ss.setPermissionCheckHandler(() => false);
  }
  return ss;
}
function saveAccounts(list) {
  const akun = list.map((a) => (a ? Object.assign({ nama: a.nama, link: a.link || null }, a.partisi !== 'persist:' + a.nama ? { partisi: a.partisi } : {}) : null));
  fs.writeFileSync(ACCOUNTS_FILE(), JSON.stringify({ akun }, null, 2));
}
function loadAccounts() {
  let j;
  try { j = JSON.parse(fs.readFileSync(ACCOUNTS_FILE(), 'utf8')); }
  catch (e) {
    if (e && e.code === 'ENOENT') {
      j = JSON.parse(JSON.stringify(ACCT_DEFAULT));
      try { fs.writeFileSync(ACCOUNTS_FILE(), JSON.stringify(j, null, 2)); console.log('Akun mini-browser dibuat di ' + ACCOUNTS_FILE()); } catch { /* abaikan */ }
    } else return { error: 'iris-accounts.json rusak (' + ACCOUNTS_FILE() + '): ' + (e && e.message) };
  }
  const out = [];
  for (let i = 0; i < ACCT_SLOTS; i++) {
    const a = Array.isArray(j.akun) ? j.akun[i] : null;
    if (a && typeof a.nama === 'string' && /^[a-z0-9_-]{1,20}$/.test(a.nama)) {
      const part = (typeof a.partisi === 'string' && /^persist:[a-z0-9_-]{1,40}$/.test(a.partisi)) ? a.partisi : 'persist:' + a.nama;
      out.push({ slot: i + 1, nama: a.nama, link: (typeof a.link === 'string' && webPanelUrlOk(a.link)) ? a.link : null, partisi: part });
    } else out.push(null);
  }
  return { akun: out };
}
function akunList(list) {
  return 'Akun mini-browser (/chrome <nomor|nama>):\n' + list.map((a, i) => (i + 1) + '. ' + (a ? a.nama + '  ' + (a.link ? shortUrl(a.link) : '(halaman tab baru)') + (webAcct && webAcct.partisi === a.partisi ? '  ← terbuka' : '') : '(kosong)')).join('\n');
}

function appTotals() {
  const ms = app.getAppMetrics();
  const mb = (m) => Math.round((m.memory.workingSetSize || 0) / 1024);
  const gpu = ms.filter((m) => m.type === 'GPU');
  return { ms, mb, total: ms.reduce((x, m) => x + mb(m), 0), gpuMb: gpu.reduce((x, m) => x + mb(m), 0), gpuCpu: gpu.reduce((x, m) => x + (m.cpu.percentCPUUsage || 0), 0) };
}
function webRamText() {
  const t = appTotals();
    let panel = '(tertutup)';
    if (webPanel && !webPanel.webContents.isDestroyed()) {
      const m = t.ms.find((q) => q.pid === webPanel.webContents.getOSProcessId());
      panel = m ? t.mb(m) + ' MB, CPU ' + (m.cpu.percentCPUUsage || 0).toFixed(1) + '%' : '?';
    }
  const hid = webParked.size ? ' (+' + webParked.size + ' tab tersembunyi)' : '';
  return `renderer panel ${panel}${hid} | GPU ${t.gpuMb} MB, CPU ${t.gpuCpu.toFixed(1)}% | total semua proses ${t.total} MB`;
}
function logWebMetrics(tag) {
  try { console.log('Chrome [' + tag + ']: ' + webRamText()); } catch (e) { console.warn('Chrome: metrik gagal:', e && e.message); }
}

// Klik: area panel harus menangkap klik walau renderer overlay minta tembus klik. main.js yang tahu posisi kursor, jadi main.js memutuskan.
function applyIgnore() {
  if (!win || win.isDestroyed()) return;
  if (webHover || webGripIv || !lastIgnoreReq) win.setIgnoreMouseEvents(false);   // v52c: selama pegangan ubah ukuran ditahan, jendela TIDAK boleh tembus klik (kursor sering mendahului pegangan, lalu seretan terputus)
  else win.setIgnoreMouseEvents(true, { forward: true });
}
function syncWebIgnore() {
  if (!webPanel || !win || win.isDestroyed()) return;
  const p = screen.getCursorScreenPoint(), b = win.getContentBounds(), r = webPanel.getBounds();
  const inside = p.x >= b.x + r.x && p.x < b.x + r.x + r.width && p.y >= b.y + r.y - WEB_TB && p.y < b.y + r.y + r.height;
  if (inside === webHover) return;
  webHover = inside;
  applyIgnore();
}
function layoutWebPanel() {
  if (!webPanel || !win || win.isDestroyed()) return;
  const cb = win.getContentBounds();
  const h = Math.max(200, Math.min(webH(), cb.height - 2 * WEB_MARGIN - WEB_TB));
  webPanel.setBounds({ x: webX, y: Math.max(WEB_MARGIN, cb.height - WEB_MARGIN - h), width: webW(), height: h });
}
// Animasi panel: meluncur dari tepi kiri jendela (ease-out) saat muncul dan keluar lagi ke kiri saat hilang. Ukuran panel tetap, hanya x yang berubah (tanpa reflow halaman).
const easeOutQuart = (k) => 1 - Math.pow(1 - k, 4);
// Panel /chrome: masuk meluncur dari kiri dengan sedikit melewati tujuan lalu mengendap (easeOutBack), sambil naik dari bawah;
// keluar menarik diri sedikit ke arah karakter dulu (easeInBack), baru menyapu ke kiri sambil turun.
const easeOutBack = (k) => { const c = 0.9, x = k - 1; return 1 + (c + 1) * x * x * x + c * x * x; };
const easeInBack = (k) => { const c = 0.9; return (c + 1) * k * k * k - c * k * k; };
const WEB_SWOOP = 34;   // px naik / turun yang menyertai luncuran; samakan dengan translateY di #webbar (index.html)
const easeInOutCubic = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
function animateWebX(to, ms, done, ease, dy0, dy1) {
  if (webAnimIv) { clearInterval(webAnimIv); webAnimIv = null; }
  const from = webX, t0 = Date.now(), fn = ease || easeOutQuart;
  let r = null;
  try { const cb = win.getContentBounds(), h = Math.max(200, Math.min(webH(), cb.height - 2 * WEB_MARGIN - WEB_TB)); r = { y: Math.max(WEB_MARGIN, cb.height - WEB_MARGIN - h), h }; } catch { /* abaikan */ }
  webAnimIv = setInterval(() => {
    const k = Math.min(1, (Date.now() - t0) / ms);
    webX = Math.round(from + (to - from) * fn(k));
    try {
      if (!webPanel || webPanel.webContents.isDestroyed()) { clearInterval(webAnimIv); webAnimIv = null; return; }
      if (r) { const p = fn(k), dy = Math.round((dy0 || 0) + ((dy1 || 0) - (dy0 || 0)) * p); webPanel.setBounds({ x: webX, y: r.y + dy, width: webW(), height: r.h }); } else layoutWebPanel();   // batas dihitung sekali: tanpa panggilan berat tiap frame
    } catch { /* abaikan */ }
    if (k >= 1) { clearInterval(webAnimIv); webAnimIv = null; try { syncWebIgnore(); } catch { /* abaikan */ } if (done) done(); }
  }, 16);
}
// v54: panel /chrome TUMBUH dari pojok bawah yang menghadap karakter (pojok kanan-bawah kalau panel di kiri karakter, pojok kiri-bawah kalau di kanan) dan mengecil ke pojok itu lagi saat hilang.
// Hanya ukuran dan posisi panel yang berubah (WebContentsView tidak bisa transparan). Bingkai pertama dipasang langsung supaya tidak ada kedipan ukuran penuh.
const easeOutCubic = (k) => 1 - Math.pow(1 - k, 3);
const easeInCubic = (k) => k * k * k;
const WEB_GROW_MIN = 0.06;   // skala awal / akhir (6 persen dari ukuran penuh)
function animateWebGrow(grow, ms, done, ease) {
  if (webAnimIv) { clearInterval(webAnimIv); webAnimIv = null; }
  let g = null;
  try {
    const cb = win.getContentBounds(), h = Math.max(200, Math.min(webH(), cb.height - 2 * WEB_MARGIN - WEB_TB)), w = webW(), fx = webHome();
    const y = Math.max(WEB_MARGIN, cb.height - WEB_MARGIN - h);
    g = { w, h, fx, bottom: y + h, anchorX: webSide === 'right' ? fx : fx + w };
  } catch { /* abaikan */ }
  if (!g) { layoutWebPanel(); if (done) done(); return; }
  webX = g.fx;
  const t0 = Date.now(), fn = ease || (grow ? easeOutCubic : easeInCubic);
  const frame = (k) => {
    const e = fn(k), s = Math.max(WEB_GROW_MIN, grow ? e : 1 - e);
    const ww = Math.max(2, Math.round(g.w * s)), hh = Math.max(2, Math.round(g.h * s));
    const x = webSide === 'right' ? g.fx : g.anchorX - ww;
    webPanel.setBounds({ x, y: g.bottom - hh, width: ww, height: hh });
  };
  try { frame(0); } catch { /* abaikan */ }
  webAnimIv = setInterval(() => {
    const k = Math.min(1, (Date.now() - t0) / ms);
    try {
      if (!webPanel || webPanel.webContents.isDestroyed()) { clearInterval(webAnimIv); webAnimIv = null; return; }
      if (k >= 1 && grow) layoutWebPanel(); else frame(k);   // akhir buka: ukuran penuh persis
    } catch { /* abaikan */ }
    if (k >= 1) { clearInterval(webAnimIv); webAnimIv = null; try { syncWebIgnore(); } catch { /* abaikan */ } if (done) done(); }
  }, 16);
}
function webWiden() {
  if (webExtra || !win || win.isDestroyed()) return;
  sitRelease('instant'); peekShow(true);   // tidak boleh sedang duduk atau bersembunyi di tepi layar
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea;
  const extra = webW() + WEB_MARGIN;
  // v48: ruang di kiri cukup = panel di kiri (seperti biasa). Tidak cukup (Iris mentok kiri layar) tapi di kanan muat = panel pindah ke KANAN karakter.
  const roomL = b.x - wa.x >= extra, roomR = b.x + WEB_RIGHT_X + webW() + WEB_MARGIN <= wa.x + wa.width;
  webSide = (!roomL && roomR) ? 'right' : 'left';
  // v52: panel besar = jendela juga memanjang ke atas (bagian bawah tetap, karakter tidak bergeser), sebatas ruang di atas jendela
  const addH = Math.max(0, Math.min(webHc - WEB_H, b.y - wa.y));
  webExtraH = addH;
  const nb = webSide === 'right' ? { x: b.x, y: b.y - addH, width: b.width + extra, height: b.height + addH } : { x: b.x - extra, y: b.y - addH, width: b.width + extra, height: b.height + addH };
  const t = clampToWork(nb, wa, true);   // v46/v48: panel tidak boleh keluar layar
  webExtra = extra;
  if (webSide === 'right') {
    // renderer mengunci lebar #root ke lebar jendela lama dulu (kelas webright), baru jendela melebar ke kanan: karakter tidak melompat
    try { if (!win.webContents.isDestroyed()) win.webContents.send('web-side', 'right'); } catch { /* abaikan */ }
    setTimeout(() => { if (win && !win.isDestroyed() && webExtra) win.setBounds({ x: t.x, y: t.y, width: nb.width, height: nb.height }); }, 50);
  } else {
    win.setBounds({ x: t.x, y: t.y, width: nb.width, height: nb.height });
  }
}
function webNarrow() {
  if (!webExtra || !win || win.isDestroyed()) { webExtra = 0; return; }
  const b = win.getBounds(), ex = webExtra, eh = webExtraH;
  webExtra = 0; webExtraH = 0;
  if (peek.out && peek.home) { const h = peek.home; peek.home = { x: webSide === 'right' ? h.x : h.x + ex, y: h.y + eh, width: h.width - ex, height: h.height - eh }; }   // v52b: posisi asal ikut menyempit
  win.setBounds({ x: webSide === 'right' ? b.x : b.x + ex, y: b.y + eh, width: b.width - ex, height: b.height - eh });
  if (webSide === 'right') {   // jendela sudah kembali sempit; baru lepas kunci lebar #root
    webSide = 'left';
    try { if (!win.webContents.isDestroyed()) win.webContents.send('web-side', 'left'); } catch { /* abaikan */ }
  }
}
// v52: besarkan / kecilkan panel. Panel tertutup = hanya mengingat pilihan (dipakai saat dibuka). Panel terbuka = jendela melebar / menyempit di sisi panel dan memanjang ke atas / memendek.
function setWebSize(w, h) {
  w = Math.round(Math.max(WEB_W_MIN, Math.min(WEB_W_MAX, w))); h = Math.round(Math.max(WEB_H_MIN, Math.min(WEB_H_MAX, h)));
  if (webExtra && webPanel) peekShow(true);   // v52b: mengubah ukuran panel = muncul dulu dari tepi
  webIdleNarrow();   // panel tertutup tapi jendela masih lebar: sempitkan dulu, ukuran baru berlaku saat dibuka
  if (!win || win.isDestroyed() || !webPanel || !webExtra || webClosing) { webWc = w; webHc = h; webBig = w > WEB_W || h > WEB_H; sendWebState(); return { ok: true, w, h }; }
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea;
  let dw = w - webWc;
  if (dw > 0) {   // melebar hanya sebatas ruang layar di sisi panel (karakter tidak digeser)
    const room = webSide === 'right' ? wa.x + wa.width - (b.x + b.width) : b.x - wa.x;
    dw = Math.max(0, Math.min(dw, room));
  }
  const wantH = Math.max(0, h - WEB_H), newAddH = Math.max(0, Math.min(wantH, webExtraH + (b.y - wa.y)));   // memanjang ke ATAS sebatas ruang di atas jendela
  const hEff = h > WEB_H ? WEB_H + newAddH : h;
  const dAdd = newAddH - webExtraH;
  if (!dw && !dAdd && hEff === webHc) return { ok: true, w: webWc, h: webHc };
  webWc += dw; webHc = hEff; webExtra += dw; webExtraH = newAddH; webBig = webWc > WEB_W || webHc > WEB_H;
  win.setBounds({ x: webSide === 'right' ? b.x : b.x - dw, y: b.y - dAdd, width: b.width + dw, height: b.height + dAdd });
  try { layoutWebPanel(); } catch { /* abaikan */ }
  sendWebState();
  return { ok: true, w: webWc, h: webHc };
}
// Jendela dibiarkan LEBAR setelah panel ditutup / disembunyikan: buka lagi tidak mengubah ukuran jendela, jadi karakter tidak berkedip.
// Jendela baru disempitkan (sekali) ketika ada hal lain yang memerlukannya: diseret, bersembunyi di tepi, duduk, atau ukuran panel diubah.
const webIdleWide = () => !!webExtra && !webPanel && !webClosing && !webOpenT;
function webIdleNarrow() { if (!webIdleWide()) return false; webNarrow(); applyIgnore(); return true; }
// v52: besarkan / kecilkan panel (preset). Panel tertutup = hanya mengingat pilihan (dipakai saat dibuka).
function webResize(big) {
  big = !!big;
  if (big === webBig && (big ? webWc === WEB_W_BIG && webHc === WEB_H_BIG : webWc === WEB_W && webHc === WEB_H)) return { ok: true, msg: big ? 'Panel sudah besar.' : 'Panel sudah kecil.' };
  const r = setWebSize(big ? WEB_W_BIG : WEB_W, big ? WEB_H_BIG : WEB_H);
  console.log('Chrome: panel ' + (big ? 'besar' : 'kecil') + ' (' + r.w + 'x' + r.h + ')');
  return { ok: true, msg: webPanel ? undefined : 'Ukuran panel: ' + (big ? 'besar' : 'kecil') + ' (berlaku saat panel dibuka).' };
}
// Pegangan ⤡ di pojok luar bilah: selama ditahan, ukuran panel mengikuti kursor. Sisi dalam (dekat karakter) dan bawah panel tetap.
let webGripIv = null;
let webGripSafe = null;
function webGrip(on) {
  const was = !!webGripIv;
  if (webGripIv) { clearInterval(webGripIv); webGripIv = null; }
  if (webGripSafe) { clearTimeout(webGripSafe); webGripSafe = null; }
  if (was) { try { applyIgnore(); } catch { /* abaikan */ } }   // v52c: seretan selesai: kembalikan aturan tembus klik biasa
  if (!on || !win || win.isDestroyed() || !webPanel || !webExtra || webClosing) return;
  const cb0 = win.getContentBounds();
  const left = webSide === 'left';
  const anchorX = left ? cb0.x + webX + webWc : cb0.x + webX;   // tepi panel yang tidak bergerak
  const bottom = cb0.y + cb0.height - WEB_MARGIN;
  webGripIv = setInterval(() => {
    if (!win || win.isDestroyed() || !webPanel) { clearInterval(webGripIv); webGripIv = null; return; }
    const c = screen.getCursorScreenPoint();
    setWebSize(left ? anchorX - c.x : c.x - anchorX, bottom - c.y - WEB_TB);
  }, 24);
  try { applyIgnore(); } catch { /* abaikan */ }   // v52c: tangkap klik dari sekarang
  webGripSafe = setTimeout(() => webGrip(false), 120000);   // jaring pengaman: mouseup hilang = berhenti sendiri
}
ipcMain.on('web-grip', (_e, on) => webGrip(!!on));
// v63: renderer memberi tahu mode fokus nyala / mati (dipakai clampToWork supaya garis fokus bisa dipindah sampai ke atas layar)
let quietMode = false;
// v64: cadangan tanpa preload: baca kelas 'quiet' langsung dari halaman overlay tiap 300 ms (preload.js lama tidak punya setQuiet)
setInterval(() => {
  try {
    if (!win || win.isDestroyed() || win.webContents.isDestroyed()) return;
    win.webContents.executeJavaScript("document.getElementById('root').classList.contains('quiet')").then((q) => { quietMode = !!q; }).catch(() => {});
  } catch { /* abaikan */ }
}, 300);
ipcMain.on('set-quiet', (e, on) => {
  if (!win || win.isDestroyed() || e.sender !== win.webContents) return;
  quietMode = !!on;
  if (!quietMode) { try { settleOnScreen(); } catch { /* abaikan */ } }   // keluar dari mode fokus: jendela ditarik kembali ke batas normal
});
function destroyWebView(v, a) {
  try { if (a) webSessionFor(a.partisi).flushStorageData(); } catch { /* abaikan */ }
  try { if (win && !win.isDestroyed()) win.contentView.removeChildView(v); } catch { /* abaikan */ }
  try { if (!v.webContents.isDestroyed()) v.webContents.close(); } catch { /* abaikan */ }   // proses renderer dibuang
}
// Simpan tab aktif: dilepas dari jendela dan disenyapkan, tapi prosesnya tetap hidup. Kelebihan dari WEB_KEEP dibuang (yang terlama).
function parkWebView(full) {
  for (const cw of [...webPopups]) { try { if (!cw.isDestroyed()) cw.close(); } catch { /* abaikan */ } }
  if (!webPanel) return;
  const v = webPanel, a = webAcct; webPanel = null;
  try { if (win && !win.isDestroyed()) win.contentView.removeChildView(v); } catch { /* abaikan */ }
  if (v.__dead || v.webContents.isDestroyed() || !a) { destroyWebView(v, a); return; }
  try { v.webContents.setAudioMuted(true); } catch { /* abaikan */ }
  webParked.delete(a.partisi); webParked.set(a.partisi, { view: v, acct: a });
  while (webParked.size > (full ? WEB_KEEP : WEB_KEEP - 1)) {   // full = tidak ada tab aktif lagi (tutup panel)
   
    const k = webParked.keys().next().value, p = webParked.get(k); webParked.delete(k);
    destroyWebView(p.view, p.acct);
  }
}
function dropParked(partisi) {
  const p = webParked.get(partisi); if (!p) return;
  webParked.delete(partisi); destroyWebView(p.view, p.acct);
}
// Tutup semuanya: tab aktif dan semua tab tersembunyi (RAM turun penuh).
function disposeWebView() {
  for (const cw of [...webPopups]) { try { if (!cw.isDestroyed()) cw.close(); } catch { /* abaikan */ } }
  for (const p of [...webParked.values()]) destroyWebView(p.view, p.acct);
  webParked.clear();
  if (!webPanel) return;
  const v = webPanel; webPanel = null;
  destroyWebView(v, webAcct);
}
// Fase 4: keadaan panel dikirim ke renderer untuk pil akun di dock (nomor + nama akun aktif, chip akun lain, tombol tutup).
function webNavInfo() {
  if (!webPanel || webPanel.webContents.isDestroyed()) return null;
  const wc = webPanel.webContents, h = wc.navigationHistory;
  let host = ''; try { host = new URL(wc.getURL()).hostname; } catch { /* abaikan */ }
  return { host, url: String(wc.getURL() || '').slice(0, 2000), title: String(wc.getTitle() || '').slice(0, 90), back: h ? h.canGoBack() : wc.canGoBack(), fwd: h ? h.canGoForward() : wc.canGoForward(), loading: wc.isLoading() };
}
let webStateT = null;
function sendWebStateSoon() { if (webStateT) return; webStateT = setTimeout(() => { webStateT = null; sendWebState(); }, 60); }   // peristiwa navigasi datang beruntun: digabung
function webStateObj(reason) {
  const L = loadAccounts();
  return { open: !!webPanel, closing: !!webClosing, nav: webNavInfo(), slot: webAcct ? webAcct.slot : 0, nama: webAcct ? webAcct.nama : '', hidup: [...webParked.values()].map((p) => p.acct.slot), akun: (L.akun || []).map((a) => (a ? { slot: a.slot, nama: a.nama } : null)), reason: reason || null, side: webSide, big: webBig, w: webW(), h: webH() };
}
function sendWebState(reason) {
  try { if (win && !win.isDestroyed() && !win.webContents.isDestroyed()) win.webContents.send('web-state', webStateObj(reason)); } catch { /* abaikan */ }
}
function closeWebPanel(reason, now) {
  if (webOpenT) { clearTimeout(webOpenT); webOpenT = null; }   // ditutup sebelum panel sempat dibuat
  if (!webPanel && !webExtra) return;
  if (webPanel && !webClosing && !now) {   // luncurkan keluar dulu, baru dibuang
    webClosing = true; sendWebState();   // bilah alat dan pil langsung ikut keluar
    animateWebGrow(false, 300, () => { webClosing = false; closeWebPanel(reason, true); });   // v54: mengecil ke pojok dekat karakter
    return;
  }
  if (webClosing) return;
  if (reason === 'sembunyi') parkWebView(true); else disposeWebView();   // sembunyi: tab tetap hidup (parkir); tutup / hemat / reset membuang semua
  webAcct = null; webHover = false; webX = webHome();
  applyIgnore();
  sendWebState(reason);
  // jendela sengaja TIDAK disempitkan di sini (lihat webIdleWide): buka lagi = tanpa perubahan ukuran jendela
  console.log('Chrome: panel ditutup' + (reason ? ' (' + reason + ')' : '') + '.');
  setTimeout(() => logWebMetrics('+5 dtk setelah tutup'), 5000);
}
function openWebPanel(acct, target, reuse) {
  if (!win || win.isDestroyed()) return;
  if (webOpenT) { clearTimeout(webOpenT); webOpenT = null; }
  // Akun yang sama sudah tampil: tidak dimuat ulang (alamat eksplisit tetap dimuat; /chrome beranda untuk kembali ke link awal)
  if (webPanel && !webClosing && webAcct && webAcct.partisi === acct.partisi) {
    webAcct = acct;
    if (!reuse) webPanel.webContents.loadURL(target).catch(() => {});
    try { webPanel.webContents.focus(); } catch { /* abaikan */ }
    sendWebState();
    return;
  }
  const switching = !!webPanel;
  if (!switching) logWebMetrics('sebelum buka');
  // Akun ini pernah dibuka dan masih hidup? Pakai lagi tab-nya, halamannya masih seperti terakhir.
  let existing = null;
  const p = webParked.get(acct.partisi);
  if (p) { webParked.delete(acct.partisi); if (p.view.__dead || p.view.webContents.isDestroyed()) destroyWebView(p.view, p.acct); else existing = p.view; }
  parkWebView();   // ganti akun: tab lama disembunyikan (bukan dibuang)
  const fresh = !webExtra;
  webWiden();
  // Jendela transparan yang berubah ukuran dan proses renderer baru yang lahir pada saat yang sama membuat karakter berkedip: dipisah, jendela dulu, panel menyusul.
  if (fresh) { webOpenT = setTimeout(() => { webOpenT = null; buildWebView(acct, reuse ? (existing ? null : target) : target, false, existing); }, WEB_SETTLE); return; }
  buildWebView(acct, reuse ? (existing ? null : target) : target, switching, existing);
}
function buildWebView(acct, target, switching, existing) {
  if (!win || win.isDestroyed()) return;
  const ss = webSessionFor(acct.partisi);
  if (webAnimIv) { clearInterval(webAnimIv); webAnimIv = null; }
  webClosing = false;
  webX = webHome();   // ganti akun: langsung di tempat; buka baru: tumbuh dari pojok dekat karakter (v54)
  webPanel = existing || new WebContentsView({ webPreferences: { session: ss, contextIsolation: true, nodeIntegration: false, sandbox: true } });
  const view = webPanel;
  webAcct = acct; webLast = acct.slot;
  const wc = webPanel.webContents;
  if (!existing) {
    webPanel.setBackgroundColor('#ffffff');
    try { if (typeof webPanel.setBorderRadius === 'function') webPanel.setBorderRadius(14); } catch { /* abaikan */ }   // fase 4e: sudut membulat
  } else { try { wc.setAudioMuted(false); } catch { /* abaikan */ } }
  win.contentView.addChildView(webPanel);
  if (switching) layoutWebPanel(); else animateWebGrow(true, 420, null);   // v54
  if (!existing) {   // tab baru: pasang penjaga dan pendengar sekali; tab yang dipakai lagi sudah punya
  wc.setWindowOpenHandler(({ url: u }) => {
    // Popup masuk dengan Google ("Continue with Google" di situs lain) HARUS tetap jendela anak yang punya window.opener, kalau tidak halaman menggantung di accounts.google.com/gsi/transform.
    // Hanya https://accounts.google.com, sesi partisi akun yang sama, tanpa preload dan nodeIntegration. Popup lain dimuat di panel yang sama seperti sebelumnya.
    let host = ''; try { host = new URL(u).hostname; } catch { /* abaikan */ }
    if (host === 'accounts.google.com' && new URL(u).protocol === 'https:') {
      return { action: 'allow', overrideBrowserWindowOptions: { parent: win, width: 480, height: 680, autoHideMenuBar: true, title: 'Masuk dengan Google', webPreferences: { session: ss, contextIsolation: true, nodeIntegration: false, sandbox: true } } };
    }
    if (webPanelUrlOk(u)) wc.loadURL(u).catch(() => {}); else console.warn('Chrome: jendela baru ditolak:', shortUrl(u));
    return { action: 'deny' };   // popup lain dimuat di panel yang sama
  });
  wc.on('did-create-window', (cw) => {   // popup login Google: dijaga sama ketat dengan panel, dan ikut ditutup bersama panel
    webPopups.add(cw);
    cw.on('closed', () => webPopups.delete(cw));
    const cwc = cw.webContents;
    cwc.setWindowOpenHandler(() => ({ action: 'deny' }));
    const g = (label) => (e, nu) => { if (!webPanelUrlOk(nu)) { e.preventDefault(); console.warn('Chrome popup:', label, 'ditolak:', shortUrl(nu)); } };
    cwc.on('will-navigate', g('navigasi')); cwc.on('will-redirect', g('redirect'));
    cwc.on('will-attach-webview', (e) => e.preventDefault());
    console.log('Chrome: popup login Google dibuka');
  });
  const guard = (label) => (e, u) => { if (!webPanelUrlOk(u)) { e.preventDefault(); console.warn('Chrome:', label, 'ditolak:', shortUrl(u)); } };
  wc.on('will-navigate', guard('navigasi'));
  wc.on('will-redirect', guard('redirect'));
  wc.on('will-attach-webview', (e) => e.preventDefault());
  wc.on('before-input-event', (e, input) => {
    if (input.type !== 'keyDown') return;
    if (input.alt && !input.control && !input.meta) {
      if (input.key === 'ArrowLeft') { e.preventDefault(); webNav('back'); }
      else if (input.key === 'ArrowRight') { e.preventDefault(); webNav('forward'); }
    } else if (input.key === 'F5' || (input.control && !input.alt && !input.shift && (input.key === 'r' || input.key === 'R'))) { e.preventDefault(); webNav('reload'); }
  });
  for (const ev of ['did-navigate', 'did-navigate-in-page', 'page-title-updated', 'did-start-loading', 'did-stop-loading']) wc.on(ev, sendWebStateSoon);   // bilah alat: alamat, judul, tombol mundur/maju, status memuat
  wc.on('did-finish-load', () => console.log('Chrome [' + acct.nama + ']: dimuat', shortUrl(wc.getURL()), '| judul:', wc.getTitle()));
  wc.on('did-fail-load', (_e, code, desc, u, isMain) => { if (isMain && code !== -3) console.warn('Chrome: gagal memuat', code, desc, shortUrl(u)); });
  wc.on('render-process-gone', (_e, d) => { view.__dead = true; console.warn('Chrome: renderer panel mati:', d && d.reason); });
  }
  if (target) wc.loadURL(target).catch((e) => console.warn('Chrome: loadURL galat:', e && e.message));
  try { win.focus(); wc.focus(); } catch { /* abaikan */ }
  syncWebIgnore();
  sendWebState();
  console.log('Chrome: akun ' + acct.slot + ' (' + acct.nama + ') ' + (existing ? 'dilanjutkan di ' + shortUrl(wc.getURL()) : 'dibuka di ' + shortUrl(target)));
  setTimeout(() => logWebMetrics('+10 dtk'), 10000);
}

// Navigasi panel (panel tidak punya tombol): /chrome mundur|maju|muat|beranda, Alt+Panah kiri/kanan, F5 atau Ctrl+R, dan tombol mundur/maju mouse.
const WEB_NAVS = { mundur: 'back', back: 'back', kembali: 'back', maju: 'forward', forward: 'forward', muat: 'reload', reload: 'reload', beranda: 'home', home: 'home' };
const WEB_RESERVED = new Set(['sembunyi', 'hide', 'reset', 'tutup', 'close', 'daftar', 'list', 'ram', 'baca', 'elemen', 'jembatan', 'semua', 'baru', 'perintah', 'bantuan', 'help', 'ke', 'go', 'besar', 'kecil', 'ukuran', ...Object.keys(WEB_NAVS)]);
function webNav(action) {
  if (!webPanel || webPanel.webContents.isDestroyed()) return false;
  const wc = webPanel.webContents, h = wc.navigationHistory;
  if (action === 'back') { if (h ? h.canGoBack() : wc.canGoBack()) { if (h) h.goBack(); else wc.goBack(); return true; } return false; }
  if (action === 'forward') { if (h ? h.canGoForward() : wc.canGoForward()) { if (h) h.goForward(); else wc.goForward(); return true; } return false; }
  if (action === 'reload') { wc.reload(); return true; }
  if (action === 'home') { wc.loadURL((webAcct && webAcct.link) || NEWTAB_URL).catch(() => {}); return true; }
  return false;
}
/* ---------- v51: Fase 5a, Hermes BACA SAJA ----------
   Pembacaan halaman panel /chrome untuk Hermes lewat jembatan HTTP lokal. Hanya MEMBACA: teks halaman, daftar elemen yang bisa diklik, dan screenshot panel.
   Tidak ada klik, ketik, atau navigasi (itu fase 5b). Yang disentuh hanya webContents panel web, bukan jendela overlay.
   Aturan keamanan:
   - Mati secara bawaan. Nyala hanya kalau IRIS_WEB_BRIDGE=1 DAN COMPANION_TOKEN terisi (token yang sama dengan /ws; tanpa token jembatan tidak mau jalan).
   - Mendengar hanya di 127.0.0.1 (port IRIS_BRIDGE_PORT, bawaan 8767); header Host harus 127.0.0.1 atau localhost; permintaan dengan header Origin (dari halaman web) ditolak; hanya GET; token dibandingkan timing-safe.
   - Isi isian formulir TIDAK PERNAH dikirim (elemen hanya melaporkan ada atau tidaknya, bukan isinya); URL hanya asal + path (tanpa query dan hash, yang sering memuat token).
   - Semua hasil bertanda untrusted:true: isi halaman adalah DATA, bukan perintah untuk Hermes.
   - Batas laju 30 permintaan per 10 detik; tiap permintaan dicatat di terminal (tanpa token dan tanpa isi). */
const WEB_READ_MAX = 20000;
const withTimeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('waktu habis')), ms))]);
function webReadReady() {
  if (!webPanel || webPanel.webContents.isDestroyed() || webClosing) throw new Error('panel /chrome belum terbuka');
  return webPanel.webContents;
}
function safeUrl(u) { try { const x = new URL(u); return x.origin + x.pathname; } catch { return ''; } }
function webReadState() {
  const wc = webReadReady();
  let host = ''; try { host = new URL(wc.getURL()).hostname; } catch { /* abaikan */ }
  return { untrusted: true, source: 'web-panel', akun: webAcct ? { slot: webAcct.slot, nama: webAcct.nama } : null, url: safeUrl(wc.getURL()), host, title: String(wc.getTitle() || '').slice(0, 200), loading: wc.isLoading() };
}
async function webReadText(max) {
  const wc = webReadReady();
  const n = Math.max(200, Math.min(WEB_READ_MAX, Number(max) || 8000));
  const t = await withTimeout(wc.executeJavaScript('(function(){try{var b=document.body;return b?String(b.innerText||""):""}catch(e){return ""}})()'), 5000);
  const text = (typeof t === 'string' ? t : '').replace(/\n{3,}/g, '\n\n').trim();
  return { ...webReadState(), text: text.slice(0, n), chars: text.length, truncated: text.length > n };
}
const WEB_ELEMS_JS = `(function(){try{
var out=[],q=document.querySelectorAll('a[href],button,input,select,textarea,[role=button],[role=link],[contenteditable=true]');
for(var i=0;i<q.length&&out.length<120;i++){var e=q[i];
var r=e.getBoundingClientRect(); if(!r.width||!r.height)continue;
var st=getComputedStyle(e); if(st.visibility==='hidden'||st.display==='none')continue;
var tag=e.tagName.toLowerCase(), type=(e.getAttribute('type')||'').toLowerCase();
var t=String(e.innerText||e.getAttribute('aria-label')||e.getAttribute('title')||e.getAttribute('placeholder')||e.getAttribute('name')||'').replace(/\\s+/g,' ').trim().slice(0,80);
var o={n:out.length+1,tag:tag,text:t};
if(type)o.type=type;
if(tag==='a'){var h=String(e.href||'');if(/^https?:/i.test(h)){try{var u=new URL(h);o.href=u.origin+u.pathname}catch(x){}}}
if(tag==='input'||tag==='textarea'||tag==='select'){o.name=String(e.getAttribute('name')||'').slice(0,40);o.password=(type==='password');}
o.x=Math.round(r.left+r.width/2);o.y=Math.round(r.top+r.height/2);
out.push(o);}
return out}catch(e){return []}})()`;
async function webReadElements() {
  const wc = webReadReady();
  const arr = await withTimeout(wc.executeJavaScript(WEB_ELEMS_JS), 5000);
  const clean = (Array.isArray(arr) ? arr : []).slice(0, 120).map((o, i) => ({
    n: i + 1, tag: String((o && o.tag) || '').slice(0, 12), text: String((o && o.text) || '').slice(0, 80),
    ...(o && o.type ? { type: String(o.type).slice(0, 20) } : {}), ...(o && o.href ? { href: String(o.href).slice(0, 200) } : {}),
    ...(o && o.name ? { name: String(o.name).slice(0, 40) } : {}), ...(o && o.tag && /^(input|textarea|select)$/.test(o.tag) ? { password: !!o.password } : {}),
    x: Number(o && o.x) || 0, y: Number(o && o.y) || 0,
  }));
  return { ...webReadState(), count: clean.length, elements: clean };
}
async function webReadShot() {
  const wc = webReadReady();
  const img = await withTimeout(wc.capturePage(), 5000);
  if (!img || img.isEmpty()) throw new Error('gambar kosong');
  const r = img.getSize().width > 1000 ? img.resize({ width: 1000 }) : img;
  return { ...webReadState(), mime: 'image/jpeg', image_base64: r.toJPEG(70).toString('base64') };
}
const BRIDGE_PORT = Number(process.env.IRIS_BRIDGE_PORT) || 8767;
let bridgeSrv = null, bridgeInfo = 'mati';
const bridgeHits = [];
const sha256 = (v) => require('crypto').createHash('sha256').update(String(v), 'utf8').digest();
function startWebBridge() {
  if (bridgeSrv) return;
  if (process.env.IRIS_WEB_BRIDGE !== '1') { bridgeInfo = 'mati (nyalakan dengan IRIS_WEB_BRIDGE=1)'; console.log('Jembatan Chrome (Hermes baca saja): ' + bridgeInfo); return; }
  if (!COMPANION_TOKEN) { bridgeInfo = 'TIDAK dinyalakan: COMPANION_TOKEN kosong (jembatan wajib bertoken)'; console.warn('Jembatan Chrome: ' + bridgeInfo); return; }
  const tokenHash = sha256(COMPANION_TOKEN);
  bridgeSrv = require('http').createServer(async (req, res) => {
    let route = '?', code = 500, akun = '';
    const send = (c, obj) => { code = c; const b = JSON.stringify(obj); res.writeHead(c, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'Content-Length': Buffer.byteLength(b) }); res.end(b); };
    try {
      const u = new URL(req.url, 'http://127.0.0.1');
      route = u.pathname;
      const host = String(req.headers.host || '').toLowerCase();
      if (host !== '127.0.0.1:' + BRIDGE_PORT && host !== 'localhost:' + BRIDGE_PORT) return send(403, { error: 'host ditolak' });
      if (req.headers.origin) return send(403, { error: 'permintaan dari halaman web ditolak' });
      if (req.method !== 'GET') return send(405, { error: 'hanya GET (baca saja)' });
      if (!require('crypto').timingSafeEqual(sha256(req.headers['x-iris-token'] || ''), tokenHash)) return send(401, { error: 'token salah atau tidak ada' });
      const now = Date.now();
      while (bridgeHits.length && now - bridgeHits[0] > 10000) bridgeHits.shift();
      if (bridgeHits.length >= 30) return send(429, { error: 'terlalu sering' });
      bridgeHits.push(now);
      akun = webAcct ? webAcct.nama : '';
      if (route === '/web/state') return send(200, webReadState());
      if (route === '/web/text') return send(200, await webReadText(u.searchParams.get('max')));
      if (route === '/web/elements') return send(200, await webReadElements());
      if (route === '/web/shot') return send(200, await webReadShot());
      return send(404, { error: 'rute tidak ada', rute: ['/web/state', '/web/text?max=N', '/web/elements', '/web/shot'] });
    } catch (e) {
      const m = String((e && e.message) || e);
      return send(/belum terbuka/.test(m) ? 503 : 500, { error: m });
    } finally {
      console.log('Jembatan Chrome: GET ' + route + ' -> ' + code + (akun ? ' (akun ' + akun + ')' : ''));
    }
  });
  bridgeSrv.on('error', (e) => { bridgeInfo = 'galat: ' + (e && e.message); console.warn('Jembatan Chrome: ' + bridgeInfo); bridgeSrv = null; });
  bridgeSrv.listen(BRIDGE_PORT, '127.0.0.1', () => { bridgeInfo = 'nyala di 127.0.0.1:' + BRIDGE_PORT + ' (baca saja, bertoken)'; console.log('Jembatan Chrome: ' + bridgeInfo); });
}
const CHROME_HELP = [
  'Perintah mini-browser (/chrome dan /akun):',
  '',
  'Buka dan tutup',
  '/chrome                  buka akun terakhir di link awalnya',
  '/chrome 1..10            ganti ke akun nomor itu (akun lama ditutup)',
  '/chrome <nama>           sama, pakai nama akun (mis. /chrome kuliah)',
  '/chrome 3 <alamat>       akun 3 tapi buka alamat lain (link awal tidak berubah)',
  '/chrome <alamat>         akun terakhir, buka alamat itu',
  '/chrome sembunyi         sembunyikan panel, tab tiap akun tetap hidup (halaman terakhir dipertahankan, maks ' + WEB_KEEP + ' akun); tombol ➖ dan Ctrl+Alt+W sama',
  '/chrome tutup            tutup panel dan buang semua tab (hemat RAM)',
  '/chrome reset            buang SEMUA tab: semua pil kembali ke link awal (login tetap tersimpan)',
  '/chrome besar | kecil    ukuran panel (besar = 640x720, jendela ikut melebar dan memanjang ke atas); /chrome ukuran = bolak-balik',
  'Ukuran bebas: tahan tombol ⤡ di pojok luar bilah atas panel lalu geser (batas: ruang layar)',
  '',
  'Navigasi',
  '/chrome mundur | maju | muat | beranda',
  '/chrome ke <alamat|kata>  buka alamat di panel yang sedang terbuka (kata biasa = cari di Google); sama dengan mengetik di kolom alamat',
  'Kolom alamat di bilah atas panel: klik = tampil alamat lengkap dan terpilih (Ctrl+C salin), tempel alamat lalu Enter = buka, Esc = batal',
  'Pintasan: Alt+Panah kiri/kanan = mundur/maju, F5 atau Ctrl+R = muat ulang, Ctrl+Alt+W = buka/sembunyikan',
  '',
  'Atur akun',
  '/akun                    daftar 5 slot (sama dengan /chrome daftar)',
  '/akun tambah <nama> [link]   buat akun di slot kosong; login cukup sekali',
  '/akun nama <nomor|nama> <nama baru>   ganti nama akun (login tetap tersimpan)',
  '/akun link <nomor> <https://...>   ganti link awal akun',
  '/akun link <nomor> baru  kembalikan ke halaman tab baru',
  '/akun link semua baru    semua akun kembali ke tab baru',
  '/akun hapus <nama>       hapus akun beserta sesi loginnya',
  '',
  'Info dan uji',
  '/chrome daftar           lihat slot akun dan link awalnya',
  '/chrome ram              pemakaian RAM, CPU, dan GPU panel',
  '/chrome baca             uji baca teks halaman (tanpa Hermes)',
  '/chrome elemen           uji daftar elemen yang terlihat',
  '/chrome jembatan         status jembatan Hermes (baca saja)',
  '/chrome perintah         daftar ini',
].join('\n');
function chromeCommand(t, list) {
  const a0 = (t[0] || '').toLowerCase();
  if (a0 === 'perintah' || a0 === 'bantuan' || a0 === 'help' || a0 === '?') return { ok: true, msg: CHROME_HELP };
  if (WEB_NAVS[a0]) {
    if (!webPanel) return { ok: false, msg: 'Panel belum dibuka. Ketik /chrome dulu.' };
    const act = WEB_NAVS[a0];
    return webNav(act) ? { ok: true } : { ok: false, msg: act === 'back' ? 'Tidak ada halaman sebelumnya.' : 'Tidak ada halaman berikutnya.' };
  }
  if (a0 === 'ke' || a0 === 'go') {   // alamat atau kata pencarian di panel yang sudah terbuka (tanpa membuat ulang panel)
    if (!webPanel || webPanel.webContents.isDestroyed()) return { ok: false, msg: 'Panel belum dibuka. Ketik /chrome dulu.' };
    const q = t.slice(1).join(' ').trim();
    if (!q) return { ok: false, msg: 'Format: /chrome ke <alamat atau kata pencarian>' };
    const looksUrl = /^[a-z][a-z0-9+.-]*:\/\//i.test(q) || (!/\s/.test(q) && (q.includes('.') || /^localhost(:\d+)?(\/|$)/i.test(q)));
    const target = looksUrl ? normUrl(q) : 'https://www.google.com/search?q=' + encodeURIComponent(q);
    if (!webPanelUrlOk(target)) return { ok: false, msg: 'Alamat ditolak: hanya https:// (atau http:// untuk localhost).' };
    webPanel.webContents.loadURL(target).catch(() => {});
    try { webPanel.webContents.focus(); } catch { /* abaikan */ }
    return { ok: true };
  }
  if (a0 === 'reset') {
    const msg = 'Reset: semua tab dibuang, semua akun kembali ke link awal.';
    if (webPanel || webExtra) { closeWebPanel('reset'); return { ok: true, msg }; }
    disposeWebView(); sendWebState('reset');
    return { ok: true, msg };
  }
  if (a0 === 'sembunyi' || a0 === 'hide') { if (!webPanel) return { ok: false, msg: 'Panel belum dibuka.' }; closeWebPanel('sembunyi'); return { ok: true }; }
  if (a0 === 'tutup' || a0 === 'close') { closeWebPanel(); return { ok: true }; }
  if (a0 === 'besar') return webResize(true);   // v52
  if (a0 === 'kecil') return webResize(false);
  if (a0 === 'ukuran') return webResize(!webBig);
  if (a0 === 'daftar' || a0 === 'list') return { ok: true, msg: akunList(list) };
  // v51: uji lokal bacaan 5a tanpa Hermes (hasil hanya tampil di chat; teks halaman adalah data, bukan perintah)
  if (a0 === 'jembatan') return { ok: true, msg: 'Jembatan Hermes (baca saja): ' + bridgeInfo + '.' };
  if (a0 === 'baca') return webReadText(1200).then((r) => ({ ok: true, msg: 'Halaman ' + (r.host || '?') + ' | ' + (r.title || '(tanpa judul)') + ' | ' + r.chars + ' karakter' + (r.akun ? ' | akun ' + r.akun.nama : '') + '\n' + r.text.slice(0, 600) })).catch((e) => ({ ok: false, msg: 'Gagal membaca: ' + (e && e.message) }));
  if (a0 === 'elemen') return webReadElements().then((r) => ({ ok: true, msg: r.count + ' elemen terlihat di ' + (r.host || '?') + (r.count ? ':\n' + r.elements.slice(0, 15).map((o) => o.n + '. ' + o.tag + (o.type ? '[' + o.type + ']' : '') + ' ' + (o.text || o.name || '')).join('\n') + (r.count > 15 ? '\n... (' + (r.count - 15) + ' lagi lewat jembatan)' : '') : '') })).catch((e) => ({ ok: false, msg: 'Gagal membaca: ' + (e && e.message) }));
  if (a0 === 'ram') { try { return { ok: true, msg: 'Chrome: ' + webRamText() + (webAcct ? ' (akun ' + webAcct.slot + ' ' + webAcct.nama + ')' : '') }; } catch (e) { return { ok: false, msg: 'Metrik gagal: ' + (e && e.message) }; } }
  let acct = null, custom = null;
  if (!a0) { acct = list[webLast - 1] || list.find(Boolean) || null; }
  else if (/^\d+$/.test(a0)) {
    const n = parseInt(a0, 10);
    if (n < 1 || n > ACCT_SLOTS) return { ok: false, msg: 'Nomor akun 1 sampai ' + ACCT_SLOTS + '.' };
    acct = list[n - 1];
    if (!acct) return { ok: false, msg: 'Slot ' + n + ' kosong. Buat dengan: /akun tambah <nama> <link awal>' };
    custom = t[1] || null;
  } else if (/^https?:\/\//i.test(a0) || a0.includes('.')) {
    acct = list[webLast - 1] || list.find(Boolean) || null; custom = t[0];   // /chrome <alamat>: akun terakhir, alamat lain
  } else {
    acct = list.find((a) => a && a.nama === a0) || null;
    if (!acct) return { ok: false, msg: 'Akun "' + a0 + '" tidak ada. Ketik /chrome daftar untuk akun, atau /chrome perintah untuk daftar perintah.' };
    custom = t[1] || null;
  }
  if (!acct) return { ok: false, msg: 'Belum ada akun. Buat dengan: /akun tambah <nama> <link awal>' };
  const target = custom ? normUrl(custom) : (acct.link || NEWTAB_URL);
  if (!webPanelUrlOk(target)) return { ok: false, msg: 'Alamat ditolak: hanya https:// (atau http:// untuk localhost).' };
  if (!win || win.isDestroyed()) return { ok: false, msg: 'Jendela overlay tidak tersedia.' };
  openWebPanel(acct, target, !custom);   // tanpa alamat eksplisit: lanjutkan tab yang masih hidup
  return { ok: true };
}
function akunCommand(t, list) {
  const sub = (t.shift() || '').toLowerCase();
  if (!sub || sub === 'daftar' || sub === 'list') return { ok: true, msg: akunList(list) };
  if (sub === 'tambah') {
    const nama = (t[0] || '').toLowerCase();
    if (!/^[a-z0-9_-]{1,20}$/.test(nama)) return { ok: false, msg: 'Format: /akun tambah <nama> [link]  (nama: huruf kecil, angka, - atau _, maksimal 20)' };
    if (WEB_RESERVED.has(nama)) return { ok: false, msg: 'Nama "' + nama + '" dipakai sebagai perintah; pilih nama lain.' };
    if (list.some((a) => a && a.nama === nama)) return { ok: false, msg: 'Nama "' + nama + '" sudah dipakai.' };
    const idx = list.findIndex((a) => !a);
    if (idx < 0) return { ok: false, msg: 'Semua ' + ACCT_SLOTS + ' slot penuh. Hapus satu dulu: /akun hapus <nama>' };
    let link = null;
    if (t[1]) { link = normUrl(t[1]); if (!webPanelUrlOk(link)) return { ok: false, msg: 'Link ditolak: hanya https:// (atau http:// untuk localhost).' }; }
    list[idx] = { slot: idx + 1, nama, link, partisi: 'persist:' + nama };
    saveAccounts(list);
    return { ok: true, msg: 'Akun "' + nama + '" dibuat di slot ' + (idx + 1) + (link ? '' : ' (mulai di halaman tab baru; atur link awal dengan /akun link ' + (idx + 1) + ' https://...)') + '. Buka dengan /chrome ' + (idx + 1) + ', login cukup sekali.' };
  }
  if (sub === 'link') {
    const q = (t[0] || '').toLowerCase(), url = t[1] || '';
    const targets = q === 'semua' ? list.filter(Boolean) : [list[parseInt(q, 10) - 1]].filter(Boolean);
    const fmt = { ok: false, msg: 'Format: /akun link <nomor|semua> <https://...|baru>   (baru = kembali ke halaman tab baru)' };
    if (!targets.length || !url) return fmt;
    if (url.toLowerCase() === 'baru') {
      targets.forEach((a) => { a.link = null; }); saveAccounts(list);
      return { ok: true, msg: 'Link awal ' + targets.map((a) => a.nama).join(', ') + ' kembali ke halaman tab baru.' };
    }
    if (q === 'semua') return fmt;
    const link = normUrl(url);
    if (!webPanelUrlOk(link)) return { ok: false, msg: 'Link ditolak: hanya https:// (atau http:// untuk localhost).' };
    targets[0].link = link; saveAccounts(list);
    return { ok: true, msg: 'Link awal akun ' + targets[0].nama + ': ' + shortUrl(link) };
  }
  if (sub === 'nama' || sub === 'ganti' || sub === 'rename') {   // ganti nama saja; partisi (sesi login) tidak berubah
    const q = (t[0] || '').toLowerCase(), baru = (t[1] || '').toLowerCase();
    const idx = /^\d+$/.test(q) ? parseInt(q, 10) - 1 : list.findIndex((a) => a && a.nama === q);
    const acct = list[idx];
    if (!acct || !baru) return { ok: false, msg: 'Format: /akun nama <nomor|nama> <nama baru>' };
    if (!/^[a-z0-9_-]{1,20}$/.test(baru)) return { ok: false, msg: 'Nama baru: huruf kecil, angka, - atau _, maksimal 20.' };
    if (WEB_RESERVED.has(baru)) return { ok: false, msg: 'Nama "' + baru + '" dipakai sebagai perintah; pilih nama lain.' };
    if (list.some((a) => a && a !== acct && a.nama === baru)) return { ok: false, msg: 'Nama "' + baru + '" sudah dipakai.' };
    const lama = acct.nama;
    acct.nama = baru;   // acct.partisi tetap: saveAccounts menulisnya ke berkas kalau tidak sama dengan persist:<nama baru>
    saveAccounts(list);
    if (webAcct && webAcct.partisi === acct.partisi) webAcct.nama = baru;
    return { ok: true, msg: 'Akun "' + lama + '" sekarang bernama "' + baru + '" (slot ' + (idx + 1) + '). Login tetap tersimpan.' };
  }
  if (sub === 'hapus') {
    const q = (t[0] || '').toLowerCase();
    const idx = /^\d+$/.test(q) ? parseInt(q, 10) - 1 : list.findIndex((a) => a && a.nama === q);
    const acct = list[idx];
    if (!acct) return { ok: false, msg: 'Format: /akun hapus <nama>  (akun tidak ditemukan)' };
    if (webAcct && webAcct.partisi === acct.partisi) closeWebPanel();
    dropParked(acct.partisi);
    try { session.fromPartition(acct.partisi).clearStorageData().catch(() => {}); } catch { /* abaikan */ }   // sesi login ikut dihapus
    list[idx] = null; saveAccounts(list);
    return { ok: true, msg: 'Akun "' + acct.nama + '" dihapus beserta sesi loginnya.' };
  }
  return { ok: false, msg: 'Format: /akun [daftar|tambah <nama> [link]|nama <nomor|nama> <baru>|link <nomor|semua> <url|baru>|hapus <nama>]' };
}
function webPanelCommand(line) {
  const t = String(line || '').trim().split(/\s+/).filter(Boolean);
  const verb = (t.shift() || '').toLowerCase();
  const L = loadAccounts();
  if (L.error) return { ok: false, msg: L.error };
  if (verb === 'akun') { const r = akunCommand(t, L.akun); if (webPanel) sendWebState(); return r; }
  return chromeCommand(t, L.akun);
}
const toggleWebPanel = () => { if (webPanel) closeWebPanel('sembunyi'); else { const r = webPanelCommand('chrome'); if (r && !r.ok) console.warn('Chrome:', r.msg); } };

/* ---------- posisi jendela: diingat antar sesi ---------- */
function stateFile() { return path.join(app.getPath('userData'), 'overlay-state.json'); }

function cornerPos(display) {
  const wa = (display || screen.getPrimaryDisplay()).workArea;
  return { x: wa.x + wa.width - BASE_W - webLeftExtra(), y: wa.y + wa.height - WIN_H };   // v31c: pad kanan boleh keluar layar, karakter tetap menempel di tepi
}

function loadSavedPos() {
  try {
    const s = JSON.parse(fs.readFileSync(stateFile(), 'utf8'));
    if (!Number.isFinite(s.x) || !Number.isFinite(s.y)) return null;
    // pakai posisi tersimpan hanya kalau minimal separuh jendela masih ada di dalam sebuah layar
    // (monitor bisa dicabut / resolusi berubah)
    const a = screen.getDisplayMatching({ x: s.x, y: s.y, width: WIN_W, height: WIN_H }).workArea;
    const ix = Math.min(s.x + BASE_W, a.x + a.width) - Math.max(s.x, a.x);
    const iy = Math.min(s.y + WIN_H, a.y + a.height) - Math.max(s.y, a.y);
    if (ix >= BASE_W / 2 && iy >= WIN_H / 2) return clampToWork({ x: s.x, y: s.y, width: WIN_W, height: WIN_H }, a);   // v46: ditarik masuk ke dalam area kerja
  } catch { /* belum ada file / rusak: pakai pojok kanan bawah */ }
  return null;
}

function savePos() {
  if (!win || win.isDestroyed()) return;
  let b = (peek.out && peek.home) ? peek.home : win.getBounds();   // v21: saat bersembunyi simpan posisi ASAL, bukan posisi di tepi layar
  if (sit.on) { const wa = screen.getDisplayMatching(b).workArea; b = { x: b.x, y: wa.y + wa.height - b.height }; }   // v22: saat duduk simpan posisi lantai, bukan posisi di atas jendela lain
  // simpan posisi saat chat tertutup, supaya buka-tutup chat tidak menggeser posisi tersimpan
  try { fs.writeFileSync(stateFile(), JSON.stringify({ x: b.x + webLeftExtra(), y: b.y + chatShift })); } catch { /* abaikan */ }
}

/* ---------- tampil / sembunyi (tanpa merebut fokus dari game) ---------- */
function showWin() { if (win && !win.isDestroyed() && !win.isVisible()) win.showInactive(); }
function toggleWin() {
  if (!win || win.isDestroyed()) return;
  if (win.isVisible()) win.hide(); else win.showInactive();
}

// Pengguna sengaja membuka chat, jadi di sini fokus boleh diambil
function openChatFromHotkey() {
  if (!win || win.isDestroyed()) return;
  peekShow();
  if (!win.isVisible()) win.show(); else win.focus();
  win.webContents.send('open-chat');
}

/* ---------- screenshot layar ----------
   Hanya dijalankan atas perintah pengguna (tombol kamera, Ctrl+Alt+S, atau menu tray); hasilnya hanya dikirim ke overlay.
   Overlay disembunyikan sebentar supaya Iris sendiri tidak ikut terfoto. Layar yang diambil = layar tempat overlay berada.
   Catatan: game fullscreen eksklusif bisa menghasilkan gambar hitam (pakai mode windowed / borderless). */
const SHOT_MAX_SIDE = 1600;
// opts.quiet = pemotretan otomatis (/pantau): tidak mengambil fokus saat overlay ditampilkan lagi, dan dibatalkan kalau overlay sedang disembunyikan pengguna.
// opts.maxSide / opts.quality = gambar lebih kecil untuk pemotretan otomatis (hemat token dan bandwidth).
async function captureScreenDataURL(opts = {}) {
  const alive = () => win && !win.isDestroyed();
  const wasVisible = alive() && win.isVisible();
  if (opts.quiet && !wasVisible) return null;   // Iris disembunyikan = pengguna tidak mau dilihat; jangan memotret diam-diam
  const maxSide = Math.max(512, Math.min(SHOT_MAX_SIDE, Number(opts.maxSide) || SHOT_MAX_SIDE));
  const quality = Math.max(40, Math.min(90, Number(opts.quality) || 85));
  try {
    const display = alive() ? screen.getDisplayMatching(win.getBounds()) : screen.getPrimaryDisplay();
    if (wasVisible) { win.hide(); await new Promise((r) => setTimeout(r, 200)); }
    const k = Math.min(1, maxSide / Math.max(display.size.width, display.size.height));
    const size = { width: Math.max(1, Math.round(display.size.width * k)), height: Math.max(1, Math.round(display.size.height * k)) };
    const sources = await desktopCapturer.getSources({ types: ['screen'], thumbnailSize: size, fetchWindowIcons: false });
    const src = sources.find((x) => x.display_id === String(display.id)) || sources[0];
    if (!src || src.thumbnail.isEmpty()) return null;
    return 'data:image/jpeg;base64,' + src.thumbnail.toJPEG(quality).toString('base64');
  } catch (e) {
    console.warn('Screenshot gagal:', e.message || e);
    return null;
  } finally {
    if (wasVisible && alive()) { if (opts.quiet) win.showInactive(); else win.show(); }
  }
}

// Dari hotkey / tray: ambil layar lalu serahkan ke overlay sebagai lampiran
async function screenshotFromHotkey() {
  const url = await captureScreenDataURL();
  if (!win || win.isDestroyed()) return;
  if (!win.isVisible()) win.show();
  win.focus();
  win.webContents.send('screenshot', url);
}

// Aksi global (hotkey / tray) -> renderer: 'clipboard' (tanya isi clipboard), 'mute' (bisukan lokal), 'menu' (menu aksi cepat)
function sendAction(name) {
  if (!win || win.isDestroyed()) return;
  if (!win.isVisible()) win.showInactive();
  if (name === 'menu') peekShow();   // menu aksi cepat butuh karakter terlihat penuh
  win.webContents.send('action', name);
}

// Isi clipboard untuk fitur "Tanya clipboard": teks, atau gambar (dikecilkan dan diubah ke JPEG supaya pesan WebSocket kecil)
// v28c: di Electron Kang Jiho modul clipboard bergaya API web (writeImage tidak ada, write() minta ClipboardItem), jadi readText / readImage
// bisa gagal diam-diam dan hasilnya "clipboard kosong". Sekarang: pakai clipboard Electron kalau memang bekerja (hasil sinkron), selain itu PowerShell.
function shrinkToJpegDataUrl(img) {
  const s = img.getSize();
  const k = Math.min(1, SHOT_MAX_SIDE / Math.max(s.width, s.height));
  const r = k < 1 ? img.resize({ width: Math.max(1, Math.round(s.width * k)) }) : img;
  return 'data:image/jpeg;base64,' + r.toJPEG(85).toString('base64');
}
function readClipboardViaPowerShell() {
  return new Promise((resolve) => {
    const out = { text: '', image: null };
    let file = '';
    try {
      const dir = path.join(app.getPath('temp'), 'iris-view'); fs.mkdirSync(dir, { recursive: true });
      file = path.join(dir, 'clipread-' + Date.now() + '.png');
    } catch (e) { console.warn('Baca clipboard: folder sementara gagal:', e.message || e); resolve(out); return; }
    const lit = file.replace(/'/g, "''");
    const cmd = "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
      + "$t=[System.Windows.Forms.Clipboard]::GetText(); "
      + "Write-Output ([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($t))); "
      + "$ok=0; if ([System.Windows.Forms.Clipboard]::ContainsImage()) { $i=[System.Windows.Forms.Clipboard]::GetImage(); if ($i) { try { $i.Save('" + lit + "', [System.Drawing.Imaging.ImageFormat]::Png); $ok=1 } finally { $i.Dispose() } } } "
      + "Write-Output $ok";
    let done = false, timer = null, buf = '';
    const finish = () => {
      if (done) return; done = true; if (timer) clearTimeout(timer);
      try {
        const lines = buf.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
        const hasImg = lines.length && lines[lines.length - 1] === '1';
        const b64 = lines.length > 1 || (lines.length === 1 && lines[0] !== '1' && lines[0] !== '0') ? lines[0] : '';
        if (b64) out.text = Buffer.from(b64, 'base64').toString('utf8');
        if (hasImg && fs.existsSync(file)) {
          const img = nativeImage.createFromBuffer(fs.readFileSync(file));
          if (!img.isEmpty()) out.image = shrinkToJpegDataUrl(img);
        }
      } catch (e) { console.warn('Baca clipboard (PowerShell) gagal:', e.message || e); }
      try { fs.unlinkSync(file); } catch { /* abaikan */ }
      resolve(out);
    };
    let p;
    try { p = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-STA', '-Command', cmd], { windowsHide: true, stdio: ['ignore', 'pipe', 'ignore'] }); }
    catch (e) { console.warn('Baca clipboard: PowerShell tidak bisa dijalankan:', e.message || e); finish(); return; }
    timer = setTimeout(() => { try { p.kill(); } catch { /* abaikan */ } console.warn('Baca clipboard: PowerShell terlalu lama'); finish(); }, 10000);
    p.stdout.on('data', (d) => { buf += d.toString('utf8'); });
    p.on('error', (e) => { console.warn('Baca clipboard: PowerShell gagal:', e.message || e); finish(); });
    p.on('exit', () => finish());
  });
}
async function readClipboardPayload() {
  try {
    if (typeof clipboard.readText === 'function' && typeof clipboard.readImage === 'function') {
      const t = clipboard.readText();
      const img = clipboard.readImage();
      if (typeof t === 'string' && img && typeof img.isEmpty === 'function') {   // hasil sinkron = API Electron asli bekerja
        const out = { text: t || '', image: null };
        if (!img.isEmpty()) out.image = shrinkToJpegDataUrl(img);
        if (out.text || out.image) return out;
      }
    }
  } catch (e) { console.warn('Baca clipboard (Electron) gagal, mencoba PowerShell:', e.message || e); }
  return await readClipboardViaPowerShell();
}

function moveToCorner() {
  if (!win || win.isDestroyed()) return;
  sitRelease('keep');
  peekShow(true);
  const b = win.getBounds();
  const wa = screen.getDisplayMatching(b).workArea;
  win.setPosition(wa.x + wa.width - (b.width - RIGHT_PAD), wa.y + wa.height - b.height);   // v31c
}

// Panel chat dibuka: jendela memanjang ke atas (bagian bawah tetap), supaya bubble ucapan tetap terlihat
// dan panel chat dapat tempat sendiri. Ditutup: kembali ke ukuran semula.
function setChatOpen(open) {
  if (!win || win.isDestroyed()) return;
  if (open) { sitRelease('instant'); peekShow(true); }   // chat dibuka = muncul dulu (jendela tidak boleh memanjang di posisi tepi layar); v22: turun dari tepi jendela dulu
  const b = win.getBounds();
  if (open && !chatGrow) {
    const wa = screen.getDisplayMatching(b).workArea;
    const ny = Math.max(wa.y, b.y - CHAT_GROW);
    chatShift = b.y - ny;
    chatGrow = CHAT_GROW;
    const cx0 = clampToWork(b, wa).x;   // v46: jendela yang separuh di luar layar ditarik masuk saat chat dibuka
    win.setBounds({ x: cx0, y: ny, width: b.width, height: b.height + CHAT_GROW });
  } else if (!open && chatGrow) {
    const shift = chatShift, grow = chatGrow;
    chatShift = 0; chatGrow = 0; chatExtra = 0;   // v32: tambahan panjang chat sudah termasuk di grow
    win.setBounds({ x: b.x, y: b.y + shift, width: b.width, height: b.height - grow });
  }
}

// v32: panjangkan / pendekkan kotak chat saat chat sudah terbuka.
// v35b: jendela memanjang ke BAWAH (bagian atas tetap, jadi karakter dan bar input tidak bergeser), dibatasi ruang sampai tepi bawah area kerja (di atas taskbar).
// Mengembalikan tambahan tinggi yang dipakai (px); 0 kalau ruang di bawah kurang dari 40 px atau chat belum terbuka (index.html lalu memakai cadangan di dalam jendela).
function setChatBig(on) {
  if (!win || win.isDestroyed() || !chatGrow) return 0;
  const b = win.getBounds();
  if (on && !chatExtra) {
    const wa = screen.getDisplayMatching(b).workArea;
    const extra = Math.min(CHAT_EXTRA, Math.max(0, wa.y + wa.height - (b.y + b.height)));
    if (extra < 40) return 0;
    chatExtra = extra; chatGrow += extra;   // chatShift tidak berubah: bagian atas jendela tetap di tempatnya
    win.setBounds({ x: b.x, y: b.y, width: b.width, height: b.height + extra });
    return extra;
  }
  if (!on && chatExtra) {
    const ex = chatExtra;
    chatExtra = 0; chatGrow -= ex;
    win.setBounds({ x: b.x, y: b.y, width: b.width, height: b.height - ex });
    return 0;
  }
  return chatExtra;
}

/* ---------- v21: sembunyi di tepi layar (mengintip) ----------
   Jendela digeser ke kiri atau kanan sampai tepi layar memotong karakter di tengah badannya, jadi kepala dan separuh badan
   tetap terlihat. Jendela memakai ukuran tetap (setBounds, bukan setPosition) supaya tidak melenceng di layar berskala 125%/150%.
   - peek.home = posisi asal; savePos menyimpan posisi ASAL selama bersembunyi, jadi posisi sembunyi tidak pernah tersimpan.
   - Tepi dipilih yang terdekat dari posisi jendela. Kalau ada monitor lain di sisi itu (bagian jendela yang "tersembunyi"
     akan muncul di monitor tetangga), dipilih tepi seberang; kalau dua-duanya terhalang, ditolak (error 'no-edge').
   - Tidak bisa sembunyi saat chat terbuka atau sedang diseret; chat dibuka / diseret / pojok kanan bawah = muncul dulu. */
const PEEK_CHAR_CX = WIN_W - RIGHT_PAD - 12 - 160;   // tengah karakter di dalam jendela: padding #root (12) + setengah lebar #char (320). Samakan dengan index.html
const PEEK_CUT = Number(process.env.IRIS_PEEK_CUT) || -20;   // px; positif = lebih banyak badan terlihat, negatif = lebih sedikit
const PEEK_MS = 240;
const peek = { out: false, back: false, home: null, edge: null, anim: null, reason: null };
const rectsOverlap = (a, b) => a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

function peekNotify(error) {
  if (!win || win.isDestroyed() || win.webContents.isDestroyed()) return;
  win.webContents.send('peek-state', { out: peek.out && !peek.back, edge: peek.edge, reason: peek.reason, error: error || null });
}
function peekTarget(b, forceEdge) {
  const d = screen.getDisplayMatching(b), db = d.bounds;
  const PCX = PEEK_CHAR_CX + webLeftExtra();   // v52b: panel /chrome di kiri melebarkan jendela ke kiri, jadi tengah karakter ikut bergeser
  const nearest = (b.x + PCX) < db.x + db.width / 2 ? 'left' : 'right';   // v31c: patokan tengah karakter, bukan tengah jendela
  const others = screen.getAllDisplays().filter((o) => o.id !== d.id);
  const make = (edge) => {
    const x = edge === 'right' ? db.x + db.width - (PCX + PEEK_CUT) : db.x - (PCX - PEEK_CUT);
    const hidden = edge === 'right'
      ? { x: db.x + db.width, y: b.y, width: x + b.width - (db.x + db.width), height: b.height }
      : { x, y: b.y, width: db.x - x, height: b.height };
    const y = Math.max(d.workArea.y, d.workArea.y + d.workArea.height - b.height);   // v21c: turun ke dasar layar supaya potongan bawah karakter pas di tepi bawah (bukan melayang)
    return others.some((o) => rectsOverlap(o.bounds, hidden)) ? null : { x, y, edge };
  };
  if (forceEdge) return make(forceEdge);   // v21e: dilepas di dekat tepi: pakai tepi itu saja
  return make(nearest) || make(nearest === 'left' ? 'right' : 'left');
}
function peekAnimate(to, size, done) {
  if (peek.anim) { clearInterval(peek.anim); peek.anim = null; }
  if (!win || win.isDestroyed()) return;
  const from = win.getBounds(), t0 = Date.now();
  peek.anim = setInterval(() => {
    if (!win || win.isDestroyed()) { clearInterval(peek.anim); peek.anim = null; return; }
    const k = Math.min(1, (Date.now() - t0) / PEEK_MS), e = 1 - Math.pow(1 - k, 3);
    win.setBounds({ x: Math.round(from.x + (to.x - from.x) * e), y: Math.round(from.y + (to.y - from.y) * e), width: size.width, height: size.height });
    if (k >= 1) {
      clearInterval(peek.anim); peek.anim = null;
      const b = win.getBounds();
      if (b.width !== size.width || b.height !== size.height) win.setBounds({ x: b.x, y: b.y, width: size.width, height: size.height });
      if (done) done();
    }
  }, 8);
}
// v52b: panel /chrome terbuka SEKARANG boleh mengintip, tapi hanya ke tepi di sisi seberang panel (panel di kiri = karakter mengintip di tepi kanan, dan sebaliknya),
// supaya panel tetap terlihat penuh di layar. Panel sedang dibuka / ditutup (peralihan) tetap menolak.
const webPanelUp = () => !!webExtra && !!webPanel && !webClosing && !webOpenT;
const webFreeEdge = () => (webSide === 'right' ? 'left' : 'right');
function peekHide(reason, forceEdge) {
  if (!win || win.isDestroyed() || chatGrow || dragIv) return false;
  const panelUp = webPanelUp();
  if (webExtra && !webIdleWide() && !panelUp) return false;
  if (panelUp) {
    if (forceEdge && forceEdge !== webFreeEdge()) return false;   // tepi di sisi panel: panel akan tersembunyi, jadi tidak
    forceEdge = webFreeEdge();
  }
  webIdleNarrow();   // panel tersembunyi tapi jendela masih lebar: sempitkan dulu
  sitRelease('instant');   // v22: turun dari tepi jendela dulu
  if (peek.out && !peek.back) return true;   // sudah bersembunyi
  let home = peek.out ? peek.home : win.getBounds();   // sedang kembali: sembunyi lagi dari posisi asal yang sama
  if (!home) return false;
  if (reason === 'drop' && !peek.out) {   // v21e: posisi 'muncul' dijaga di dalam area kerja (karakter bisa saja dilepas separuh di luar layar)
    const wa = screen.getDisplayMatching(home).workArea;
    home = { x: Math.max(wa.x, Math.min(wa.x + wa.width - home.width, home.x)), y: Math.max(wa.y, Math.min(wa.y + wa.height - home.height, home.y)), width: home.width, height: home.height };
  }
  const tgt = peekTarget(home, forceEdge);
  if (!tgt) { if (reason !== 'drop') peekNotify('no-edge'); return false; }   // dilepas di dekat tepi tapi terhalang monitor lain: diam saja, tanpa pesan galat
  peek.reason = reason || null;
  peek.home = { x: home.x, y: home.y, width: home.width, height: home.height };
  peek.edge = tgt.edge; peek.out = true; peek.back = false;
  peekNotify();
  peekAnimate({ x: tgt.x, y: tgt.y }, peek.home, null);
  return true;
}
function peekShow(instant) {
  if (!win || win.isDestroyed() || !peek.out) return;
  const home = peek.home;
  const fin = () => { peek.out = false; peek.back = false; peek.home = null; peek.edge = null; };
  if (!home) { fin(); return; }
  if (peek.back && !instant) return;   // sudah dalam perjalanan kembali
  peek.back = true; peekNotify();
  if (instant) {
    if (peek.anim) { clearInterval(peek.anim); peek.anim = null; }
    win.setBounds(home); fin();
  } else peekAnimate({ x: home.x, y: home.y }, home, fin);
}

/* ---------- v22: duduk di tepi atas jendela lain ----------
   Posisi dan ukuran jendela Windows dibaca lewat proses PowerShell yang tetap hidup (EnumWindows + GetWindowRect/DWM frame).
   YANG DIBACA: hanya HWND, posisi, dan ukuran jendela yang terlihat. TIDAK membaca judul, nama proses, atau isi jendela.
   Hanya jalan kalau saklar "Duduk di tepi jendela" menyala (bawaan MATI), dan proses PowerShell dimatikan lagi saat saklar mati.
   Perilaku: dilepas dengan dasar kanvas karakter dalam SIT_SNAP px dari tepi atas jendela lain = duduk (dasar jendela Iris = tepi atas jendela itu).
   Iris ikut bergerak saat jendelanya digeser (dicek tiap SIT_POLL_MS). Jendela ditutup / diminimalkan / terlalu ke atas = Iris turun ke dasar layar.
   Diseret, chat dibuka, atau mengintip = turun dulu. Karakter setinggi ~420 px, jadi tepi atas jendela harus minimal SIT_CHAR_H px di bawah atas layar. */
const SIT_SNAP = 70, SIT_POLL_MS = 300, SIT_CHAR_H = 420;
const SIT_FALL = Number(process.env.IRIS_SIT_FALL) || 700;   // v64: jarak jatuh maksimum dari udara ke tepi atas jendela di bawahnya
const SIT_BAR = Number(process.env.IRIS_SIT_BAR) || 74;   // ruang kosong di bawah karakter di dalam jendela (tempat bar); dipakai hanya untuk menebak posisi dasar karakter saat dilepas
const sit = { enabled: false, on: false, hwnd: null, dx: 0, ps: null, ready: false, buf: '', cur: [], queue: [], timer: null, busy: false, fail: 0 };
const PS_SCRIPT = String.raw`$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class IrisWin {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int i);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("dwmapi.dll", EntryPoint = "DwmGetWindowAttribute")] public static extern int DwmInt(IntPtr h, int a, out int v, int s);
  [DllImport("dwmapi.dll", EntryPoint = "DwmGetWindowAttribute")] public static extern int DwmRect(IntPtr h, int a, out RECT v, int s);
  public static string List(uint skipPid) {
    var sb = new StringBuilder();
    EnumWindows((h, l) => {
      if (!IsWindowVisible(h) || IsIconic(h)) return true;
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (pid == skipPid) return true;
      int ex = GetWindowLong(h, -20);
      if ((ex & 0x80) != 0 || (ex & 0x08000000) != 0) return true;
      int cloaked = 0; DwmInt(h, 14, out cloaked, 4);
      if (cloaked != 0) return true;
      RECT r; if (DwmRect(h, 9, out r, 16) != 0) { if (!GetWindowRect(h, out r)) return true; }
      if (r.R - r.L < 200 || r.B - r.T < 120) return true;
      sb.Append(h.ToInt64()).Append(' ').Append(r.L).Append(' ').Append(r.T).Append(' ').Append(r.R).Append(' ').Append(r.B).Append('\n');
      return true;
    }, IntPtr.Zero);
    return sb.ToString();
  }
}
"@
[void][IrisWin]::SetProcessDPIAware()
[Console]::Out.WriteLine('ready')
while ($true) {
  $l = [Console]::In.ReadLine()
  if ($null -eq $l) { break }
  [Console]::Out.Write([IrisWin]::List([uint32]$l))
  [Console]::Out.WriteLine('END')
}
`;
function sitFlush(v) { const q = sit.queue; sit.queue = []; for (const r of q) r.resolve(v); }
function psStop() {
  const ps = sit.ps; sit.ps = null; sit.ready = false; sit.buf = ''; sit.cur = [];
  if (ps) { try { ps.stdin.end(); } catch { /* abaikan */ } try { ps.kill(); } catch { /* abaikan */ } }
  sitFlush(null);
}
function psStart() {
  if (sit.ps) return true;
  if (process.platform !== 'win32') return false;
  try {
    const enc = Buffer.from(PS_SCRIPT, 'utf16le').toString('base64');
    const ps = spawn('powershell.exe', ['-NoProfile', '-NoLogo', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', enc], { windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    ps.stdout.setEncoding('utf8');
    ps.stdout.on('data', (d) => {
      sit.buf += d;
      let i;
      while ((i = sit.buf.indexOf('\n')) >= 0) {
        const line = sit.buf.slice(0, i).replace(/\r$/, ''); sit.buf = sit.buf.slice(i + 1);
        if (line === 'ready') { sit.ready = true; continue; }
        if (line === 'END') { const rects = sitParse(sit.cur); sit.cur = []; const r = sit.queue.shift(); if (r) r.resolve(rects); continue; }
        if (line) sit.cur.push(line);
      }
    });
    ps.stderr.on('data', (d) => console.warn('Duduk (PowerShell):', String(d).slice(0, 400)));
    ps.on('error', (e) => { console.warn('Duduk: PowerShell tidak bisa dijalankan:', e.message || e); if (sit.ps === ps) { sit.ps = null; sit.ready = false; sitFlush(null); } });
    ps.on('exit', () => { if (sit.ps === ps) { sit.ps = null; sit.ready = false; sitFlush(null); } });
    sit.ps = ps;
    return true;
  } catch (e) { console.warn('Duduk: gagal memulai PowerShell:', e.message || e); return false; }
}
function sitParse(lines) {
  const out = [];
  for (const ln of lines) {
    const p = ln.split(' ');
    if (p.length !== 5) continue;
    const [id, L, T, R, B] = p.map(Number);
    if (![id, L, T, R, B].every(Number.isFinite)) continue;
    let rc = { x: L, y: T, width: R - L, height: B - T };
    try { if (process.platform === 'win32') rc = screen.screenToDipRect(win && !win.isDestroyed() ? win : null, rc); } catch { /* pakai apa adanya */ }
    out.push({ id, l: rc.x, t: rc.y, r: rc.x + rc.width, b: rc.y + rc.height, rect: rc });
  }
  return out;   // urutan = dari yang paling depan (z-order)
}
function sitRects() {
  return new Promise((resolve) => {
    if (!sit.enabled || !psStart()) { resolve(null); return; }
    const entry = { resolve: null };
    const tm = setTimeout(() => { const i = sit.queue.indexOf(entry); if (i >= 0) { psStop(); } resolve(null); }, 6000);   // pemanggilan pertama mengompilasi kode C#: bisa 1-3 detik
    entry.resolve = (v) => { clearTimeout(tm); resolve(v); };
    sit.queue.push(entry);
    try { sit.ps.stdin.write(process.pid + '\n'); } catch { psStop(); }
  });
}
// Alasan sebuah jendela TIDAK bisa diduduki (null = bisa). Dipakai sitSnap dan /duduk cek supaya keputusannya sama.
function sitReject(rects, i, cx, charBottom, wa) {
  const r = rects[i];
  if (cx < r.l + 30 || cx > r.r - 30) return 'tengah karakter di luar lebar jendela';
  if (charBottom - r.t > SIT_SNAP) return 'dasar karakter sudah di bawah tepi atas (' + Math.round(charBottom - r.t) + ' px, batas ' + SIT_SNAP + ')';   // v64
  if (r.t - charBottom > SIT_FALL) return 'tepi atas terlalu jauh di bawah (' + Math.round(r.t - charBottom) + ' px, batas ' + SIT_FALL + ')';   // v64: jatuh dari udara
  if (r.t - SIT_CHAR_H < wa.y - 40) return 'tepi atas terlalu dekat atas layar (kepala keluar layar)';
  if (rects.slice(0, i).some((o) => cx >= o.l && cx <= o.r && r.t + 2 >= o.t && r.t + 2 <= o.b)) return 'tepi atasnya tertutup jendela lain';
  return null;
}
// force = true: dipanggil saat /duduk nyala. Iris langsung naik ke tepi atas jendela terdekat yang layak (tanpa harus dilepas dekat tepi atasnya).
async function sitSnap(force) {
  if (!sit.enabled || !win || win.isDestroyed() || sit.on || (webExtra && !webIdleWide())) return false;
  webIdleNarrow();
  const rects = await sitRects();
  if (!rects || !rects.length || !win || win.isDestroyed() || !sit.enabled || sit.on) return false;
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea;
  const cx = b.x + PEEK_CHAR_CX, charBottom = b.y + b.height - SIT_BAR;
  if (force) {
    if (chatGrow) return false;   // jendela sedang memanjang untuk chat
    let best = null;
    for (let i = 0; i < rects.length; i++) {
      const r = rects[i];
      if (r.r - r.l < 120) continue;
      const tx = Math.max(r.l + 30, Math.min(r.r - 30, cx));   // geser ke dalam lebar jendela itu
      if (r.t - SIT_CHAR_H < wa.y - 40) continue;              // kepala keluar layar / dimaksimalkan
      if (r.t > wa.y + wa.height - 60) continue;               // tepi atas hampir di dasar layar
      if (rects.slice(0, i).some((o) => tx >= o.l && tx <= o.r && r.t + 2 >= o.t && r.t + 2 <= o.b)) continue;   // tepi atas tertutup jendela lain
      const d = Math.abs(tx - cx) + Math.abs(r.t - charBottom);
      if (!best || d < best.d) best = { r, tx, d };
    }
    if (!best) return false;
    sitStart(best.r, { x: Math.round(best.tx - PEEK_CHAR_CX), y: b.y, width: b.width, height: b.height });
    return true;
  }
  let best = null;   // v64: pilih tepi terdekat di bawah kaki, bukan yang pertama lolos
  for (let i = 0; i < rects.length; i++) {
    if (sitReject(rects, i, cx, charBottom, wa)) continue;
    const d = Math.abs(rects[i].t - charBottom);
    if (!best || d < best.d) best = { i, d };
  }
  if (best) { sitStart(rects[best.i], b); return true; }
  return false;
}
// /duduk cek: laporan teks (hanya angka posisi, tanpa judul jendela) untuk mencari tahu kenapa Iris tidak mau duduk
ipcMain.handle('sit-debug', async () => {
  const out = ['Duduk: saklar ' + (sit.enabled ? 'NYALA' : 'MATI') + ', sedang duduk: ' + (sit.on ? 'ya' : 'tidak') + ', platform: ' + process.platform];
  if (!sit.enabled) { out.push('Nyalakan dulu dengan /duduk nyala.'); return out.join('\n'); }
  if (!win || win.isDestroyed()) return out.join('\n');
  const t0 = Date.now(), rects = await sitRects();
  if (!rects) { out.push('PowerShell tidak membalas dalam 6 detik atau gagal mulai. Lihat konsol main.js (awalan "Duduk (PowerShell)").'); return out.join('\n'); }
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea, cx = b.x + PEEK_CHAR_CX, charBottom = b.y + b.height - SIT_BAR;
  out.push('PowerShell jalan (' + (Date.now() - t0) + ' ms), jendela terbaca: ' + rects.length);
  out.push('Karakter: tengah x=' + Math.round(cx) + ', dasar y=' + Math.round(charBottom) + ' (SIT_BAR=' + SIT_BAR + '), area kerja atas y=' + wa.y);
  const near = rects.map((r, i) => ({ r, i, d: Math.abs(charBottom - r.t) })).sort((a, c) => a.d - c.d).slice(0, 5);
  for (const { r, i } of near) {
    const why = sitReject(rects, i, cx, charBottom, wa);
    out.push('Jendela z' + i + ': kiri ' + Math.round(r.l) + ', atas ' + Math.round(r.t) + ', kanan ' + Math.round(r.r) + ' -> ' + (why ? 'ditolak: ' + why : 'BISA diduduki'));
  }
  if (!near.length) out.push('Tidak ada jendela yang memenuhi syarat dasar (terlihat, tidak diminimalkan, minimal 200 x 120).');
  return out.join('\n');
});
function sitStart(r, b) {
  peekShow(true);
  sit.on = true; sit.hwnd = r.id; sit.dx = b.x - r.l; sit.fail = 0;
  if (!win.webContents.isDestroyed()) win.webContents.send('sit-state', { on: true });
  peekAnimate({ x: b.x, y: r.t - b.height }, { width: b.width, height: b.height }, null);
  clearInterval(sit.timer); sit.timer = setInterval(sitPoll, SIT_POLL_MS);
}
async function sitPoll() {
  if (!sit.on || sit.busy || !win || win.isDestroyed() || peek.anim) return;
  sit.busy = true;
  try {
    const rects = await sitRects();
    if (!sit.on) return;
    if (!rects) { if (++sit.fail > 8) sitRelease('fall'); return; }
    sit.fail = 0;
    const r = rects.find((o) => o.id === sit.hwnd);
    if (!r) { sitRelease('fall'); return; }                              // ditutup / diminimalkan / disembunyikan
    const b = win.getBounds(), wa = screen.getDisplayMatching(r.rect).workArea;
    if (r.t - SIT_CHAR_H < wa.y - 40) { sitRelease('fall'); return; }    // digeser terlalu ke atas / dimaksimalkan
    const x = Math.max(r.l + 30 - PEEK_CHAR_CX, Math.min(r.r - 30 - PEEK_CHAR_CX, r.l + sit.dx)), y = r.t - b.height;
    if (Math.round(x) !== b.x || Math.round(y) !== b.y) win.setBounds({ x: Math.round(x), y: Math.round(y), width: b.width, height: b.height });
  } finally { sit.busy = false; }
}
// mode: 'fall' = turun ke dasar layar dengan animasi, 'instant' = langsung, 'keep' = hanya lepas status (posisi diatur pemanggil)
function sitRelease(mode) {
  if (!sit.on) { if (mode === 'fall' && !sit.enabled) psStop(); return; }
  sit.on = false; sit.hwnd = null; clearInterval(sit.timer); sit.timer = null;
  if (!sit.enabled) psStop();
  if (win && !win.isDestroyed()) {
    if (!win.webContents.isDestroyed()) win.webContents.send('sit-state', { on: false });
    if (mode !== 'keep') {
      const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea, fy = wa.y + wa.height - b.height;
      if (mode === 'instant') { if (peek.anim) { clearInterval(peek.anim); peek.anim = null; } win.setBounds({ x: b.x, y: fy, width: b.width, height: b.height }); }
      else peekAnimate({ x: b.x, y: fy }, { width: b.width, height: b.height }, null);
    }
  }
}

function setMuted(v) {
  if (win && !win.isDestroyed()) win.webContents.setAudioMuted(!!v);   // lip-sync tetap jalan, hanya keluaran suara dibisukan
}

let crashLog = [], unresponsiveNow = false;
/* v43: watchdog. (1) Denyut render dari renderer (ipc 'render-pulse', tiap ~5 dtk saat WebGL hidup). Jendela terlihat tapi tanpa denyut
   selama 45 dtk = render macet atau konteks WebGL mati: muat ulang (dibatasi 3x per 5 menit, sama dengan v37d).
   (2) Jendela sepenuhnya di luar semua layar (mis. setelah monitor dicabut atau lag saat diseret) = kembalikan ke pojok kanan bawah. */
let pulseAt = Date.now();
ipcMain.on('render-pulse', () => { pulseAt = Date.now(); });
function startWatchdog() {
  setInterval(() => {
    if (!win || win.isDestroyed()) return;
    try {
      if (win.isVisible() && !unresponsiveNow && Date.now() - pulseAt > 45000) {
        const now = Date.now(); crashLog = crashLog.filter((t) => now - t < 300000); crashLog.push(now);
        console.warn('Watchdog: tidak ada denyut render 45 dtk; ' + (crashLog.length > 3 ? 'terlalu sering, restart overlay manual.' : 'memuat ulang halaman.'));
        pulseAt = now;
        if (crashLog.length <= 3) win.webContents.reload();
        return;
      }
      const b = win.getBounds();
      const seen = screen.getAllDisplays().some((d) => {
        const w = Math.min(b.x + b.width, d.bounds.x + d.bounds.width) - Math.max(b.x, d.bounds.x);
        const h = Math.min(b.y + b.height, d.bounds.y + d.bounds.height) - Math.max(b.y, d.bounds.y);
        return w > 20 && h > 20;
      });
      if (!seen && !dragIv && !(peek && peek.anim)) {
        const c = cornerPos(); console.warn('Watchdog: jendela di luar layar; dipindah ke pojok kanan bawah.');
        win.setPosition(c.x, c.y);
      }
    } catch (e) { console.warn('Watchdog galat:', e && e.message); }
  }, 10000);
  try { powerMonitor.on('resume', () => { pulseAt = Date.now(); }); powerMonitor.on('unlock-screen', () => { pulseAt = Date.now(); }); } catch { /* abaikan */ }
}
app.on('child-process-gone', (_e, d) => console.warn('Proses anak mati:', d && d.type, d && d.reason));   // v37d: mis. GPU process
function createWindow() {
  const pos = loadSavedPos() || cornerPos();
  win = new BrowserWindow({
    width: WIN_W,
    height: WIN_H,
    x: pos.x,
    y: pos.y,
    show: false,            // ditampilkan lewat showInactive() supaya tidak mencuri fokus
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,      // overlay tidak muncul di taskbar; akses lewat tray dan hotkey
    resizable: false,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.setAlwaysOnTop(true, 'screen-saver');
  // Awalnya tembus klik; renderer mematikannya saat kursor di atas karakter (piksel opak)/bubble/input
  win.setIgnoreMouseEvents(true, { forward: true });

  let revealed = false;
  const reveal = () => {
    if (revealed || !win || win.isDestroyed()) return;
    revealed = true;
    win.showInactive();
  };
  win.once('ready-to-show', reveal);
  win.webContents.once('did-finish-load', reveal);
  setTimeout(reveal, 4000);   // jaring pengaman kalau kedua event di atas tidak datang

  win.on('move', () => { clearTimeout(saveTimer); saveTimer = setTimeout(savePos, 500); });
  win.on('resize', layoutWebPanel);
  win.on('app-command', (_e, cmd) => { if (!webPanel) return; if (cmd === 'browser-backward') webNav('back'); else if (cmd === 'browser-forward') webNav('forward'); });
  win.on('closed', () => { win = null; });
  // v37d: renderer crash / macet = karakter ngilang (jendela transparan kosong) dan laptop lag. Muat ulang otomatis, maksimal 3 kali per 5 menit.
  win.webContents.on('render-process-gone', (_e, d) => {
    console.warn('Renderer mati:', d && d.reason, d && d.exitCode);
    const now = Date.now(); crashLog = crashLog.filter((t) => now - t < 300000); crashLog.push(now);
    if (crashLog.length > 3) { console.warn('Renderer mati terlalu sering; tidak dimuat ulang otomatis. Restart overlay.'); return; }
    setTimeout(() => { if (win && !win.isDestroyed()) win.webContents.reload(); }, 1000);
  });
  win.on('unresponsive', () => {
    console.warn('Overlay tidak merespons; menunggu 8 detik lalu muat ulang jika masih macet.');
    setTimeout(() => { if (win && !win.isDestroyed() && unresponsiveNow) win.webContents.reload(); }, 8000);
    unresponsiveNow = true;
  });
  win.on('responsive', () => { unresponsiveNow = false; });
  win.on('show', () => { pulseAt = Date.now(); });
  win.webContents.on('did-start-loading', () => { pulseAt = Date.now(); });
  win.loadURL('app://local/index.html');
}

/* ---------- kursor global -> renderer (mata dan kepala mengikuti kursor di seluruh layar) ---------- */
// Dari pola screen.ts AIRI: polling berkala, kirim hanya kalau posisi berubah.
// getCursorScreenPoint dan getContentBounds sama-sama DIP, jadi selisihnya = posisi di dalam jendela (px CSS).
let lastRel = { x: NaN, y: NaN }, lastVisKey = '';
function pollCursor() {
  if (!win || win.isDestroyed() || !win.isVisible() || win.webContents.isDestroyed()) return;
  syncWebIgnore();   // /chrome: kursor di atas panel = jendela menangkap klik
  const p = screen.getCursorScreenPoint();
  const b = win.getContentBounds();
  const rel = { x: p.x - b.x, y: p.y - b.y };
  // v23: bagian jendela yang benar-benar ada di layar (koordinat jendela). Dipakai renderer supaya bubble tidak terpotong tepi layar.
  const db = screen.getDisplayMatching(b).bounds;
  const vis = { l: db.x - b.x, t: db.y - b.y, r: db.x + db.width - b.x, b: db.y + db.height - b.y };
  const vk = vis.l + ',' + vis.t + ',' + vis.r + ',' + vis.b;
  if (rel.x === lastRel.x && rel.y === lastRel.y && vk === lastVisKey) return;
  lastRel = rel; lastVisKey = vk;
  win.webContents.send('cursor', { x: rel.x, y: rel.y, vis });
}

/* ---------- menit aktif terus-menerus (untuk pengingat istirahat) ----------
   Hanya memakai waktu diam sistem (powerMonitor): tidak membaca layar, judul jendela, atau ketikan.
   Kalau tidak ada input selama IDLE_RESET_S detik, hitungan kembali ke 0. Renderer yang memutuskan kapan mengingatkan. */
const IDLE_RESET_S = 300;
let activeMin = 0;
function pollActivity() {
  if (!win || win.isDestroyed() || win.webContents.isDestroyed()) return;
  let idle = 0;
  try { idle = powerMonitor.getSystemIdleTime(); } catch { return; }
  if (idle >= IDLE_RESET_S) activeMin = 0; else activeMin += 1;
  if (win.isVisible()) win.webContents.send('activity', activeMin);
}

function setupTray() {
  if (!fs.existsSync(TRAY_ICON)) {
    console.warn('Ikon tray tidak ditemukan (' + TRAY_ICON + '), tray dilewati. Letakkan tray.png di folder assets.');
    return;
  }
  try {
    tray = new Tray(nativeImage.createFromPath(TRAY_ICON));
    tray.setToolTip('Iris');
    tray.setContextMenu(Menu.buildFromTemplate([
      { label: 'Tampilkan / sembunyikan', click: toggleWin },
      { label: 'Buka chat', click: openChatFromHotkey },
      { label: 'Ambil screenshot layar', click: screenshotFromHotkey },
      { label: 'Bicara (mulai / berhenti rekam)', click: () => sendAction('talk') },
      { label: 'Terjemahkan layar', click: () => sendAction('translate') },
      { label: 'Tanya isi clipboard', click: () => sendAction('clipboard') },
      { label: 'Menu aksi cepat', click: () => sendAction('menu') },
      { label: 'Mini-browser /chrome (buka / tutup)', click: toggleWebPanel },
      { label: 'Mode fokus (nyala / mati)', click: () => sendAction('focus') },
      { label: 'Sembunyi di tepi layar (nyala / mati)', click: () => sendAction('peek') },
      { label: 'Bisukan suara', type: 'checkbox', checked: false, click: (item) => setMuted(item.checked) },
      { label: 'Pindah ke pojok kanan bawah', click: moveToCorner },
      { type: 'separator' },
      { label: 'Keluar', click: () => app.quit() },
    ]));
    tray.on('click', toggleWin);
  } catch (e) {
    console.warn('Tray gagal dibuat:', e.message || e);
  }
}

function registerShortcut(accel, fn) {
  if (!globalShortcut.register(accel, fn)) {
    console.warn('Pintasan global gagal didaftarkan (dipakai aplikasi lain?):', accel);
  }
}

// Coba beberapa kombinasi sampai ada yang belum dipakai aplikasi lain; yang berhasil dicetak ke terminal.
function registerFirst(accels, fn) {
  for (const a of accels) {
    if (globalShortcut.register(a, fn)) { console.log('Pintasan terdaftar:', a); return a; }
  }
  console.warn('Semua pintasan gagal didaftarkan (dipakai aplikasi lain?):', accels.join(', '));
  return null;
}

// v28: kunci navigasi. Overlay menampilkan teks dari model dan Hermes, jadi tidak ada alasan jendela mana pun boleh membuka
// jendela baru, pindah ke halaman lain, atau menempelkan <webview>. Ini juga mencegah file yang dijatuhkan ke jendela membuat
// halaman berpindah ke file:// . Pemuatan programatik (win.loadURL / loadFile) tidak terkena. DevTools (Ctrl+Alt+D) dikecualikan.
app.on('web-contents-created', (_e, contents) => {
  if (isWebPanel(contents)) return;   // panel /chrome punya penjaga sendiri (openWebPanel); kunci di bawah memblokir semua navigasi
  const isDevtools = (u) => typeof u === 'string' && u.startsWith('devtools://');
  contents.setWindowOpenHandler((details) => {
    if (!isDevtools(details && details.url)) console.warn('Jendela baru ditolak:', String((details && details.url) || '').slice(0, 120));
    return isDevtools(details && details.url) ? { action: 'allow' } : { action: 'deny' };
  });
  const block = (label) => (e, url) => {
    if (isDevtools(url)) return;
    e.preventDefault();
    console.warn(label, 'ditolak:', String(url || '').slice(0, 120));
  };
  contents.on('will-navigate', block('Navigasi'));
  contents.on('will-redirect', block('Redirect'));
  contents.on('will-attach-webview', (e) => e.preventDefault());
});

app.whenReady().then(() => {
  if (!gotLock) return;

  // Layani file dari folder proyek lewat app://local/...
  protocol.handle('app', (request) => {
    const url = new URL(request.url);
    const rel = decodeURIComponent(url.pathname);
    const file = path.normalize(path.join(__dirname, rel));
    if (!file.startsWith(__dirname + path.sep)) {
      return new Response('forbidden', { status: 403 });
    }
    // File tidak ada (mis. clips.json opsional, favicon.ico): balas 404 biasa, jangan lempar error ke terminal.
    return net.fetch(pathToFileURL(file).toString()).catch(() => {
      if (!/favicon\.ico$|clips\.json$/.test(file)) console.warn('app:// file tidak ditemukan:', rel);
      return new Response('not found', { status: 404 });
    });
  });

  // Ganti Origin untuk koneksi WebSocket ke server lokal saja.
  session.defaultSession.webRequest.onBeforeSendHeaders(
    { urls: ['ws://localhost:8765/*'] },
    (details, callback) => {
      details.requestHeaders['Origin'] = SERVER_ORIGIN;
      if (COMPANION_TOKEN) details.requestHeaders['X-Iris-Token'] = COMPANION_TOKEN;   // v28
      callback({ requestHeaders: details.requestHeaders });
    }
  );

  // v39c: kalau server menolak handshake /ws (403), cetak sebab yang paling mungkin di terminal ini (maks. sekali per 30 detik)
  let lastWs403 = 0;
  const onWsDone = (d) => {
    if (d.statusCode !== 403 || Date.now() - lastWs403 < 30000) return;
    lastWs403 = Date.now();
    console.warn(COMPANION_TOKEN
      ? `Server menolak /ws (403). Token Electron: ${COMPANION_TOKEN.length} karakter, sidik ${tokenFp(COMPANION_TOKEN)}. Cocokkan dengan "Token /ws server" di terminal server.py.`
      : 'Server menolak /ws (403) karena Electron tidak punya COMPANION_TOKEN (tidak ada header X-Iris-Token). Sumber yang dicari: ' + COMPANION_TOKEN_SRC);
  };
  session.defaultSession.webRequest.onCompleted({ urls: ['ws://localhost:8765/*'] }, onWsDone);
  session.defaultSession.webRequest.onErrorOccurred({ urls: ['ws://localhost:8765/*'] }, () => {});

  // Mikrofon: hanya untuk halaman overlay sendiri (app://), dan hanya direkam saat pengguna menyalakannya (tombol mic atau Ctrl+Alt+G)
  const isOverlay = (wc) => !!wc && wc.getURL().startsWith('app://local/');
  session.defaultSession.setPermissionRequestHandler((wc, permission, callback) => callback(permission === 'media' && isOverlay(wc)));
  session.defaultSession.setPermissionCheckHandler((wc, permission) => permission === 'media' && isOverlay(wc));

  createWindow();
  setupTray();
  setInterval(pollCursor, 40);
  startWatchdog();   // v43
  setInterval(pollActivity, 60000);

  // Jalan keluar darurat karena jendela tanpa frame tidak punya tombol tutup
  registerShortcut('Control+Alt+Q', () => app.quit());
  registerShortcut('Control+Alt+W', toggleWebPanel);   // /chrome: buka akun terakhir / tutup panel
  registerShortcut('Control+Alt+H', toggleWin);
  // Buka chat dari mana saja (jendela tidak perlu fokus). Menggantikan pintasan di dalam jendela dengan kombinasi yang sama.
  registerShortcut('Control+Alt+C', openChatFromHotkey);
  // Screenshot layar -> jadi lampiran di overlay
  registerShortcut('Control+Alt+S', screenshotFromHotkey);
  // Bicara langsung: Ctrl+Alt+G memulai dan menghentikan rekaman mikrofon (pintasan global tidak punya "tahan", jadi berupa saklar)
  registerShortcut('Control+Alt+G', () => sendAction('talk'));
  // Terjemahkan teks di layar (foto layar lalu Iris menerjemahkan), dari mana saja
  registerShortcut('Control+Alt+T', () => sendAction('translate'));
  // Tanya isi clipboard (teks atau gambar) dan bisukan suara lokal, dari mana saja
  registerShortcut('Control+Alt+V', () => sendAction('clipboard'));
  // Bisukan suara overlay. Bisa dipaksa lewat environment variable IRIS_MUTE_KEY (mis. Control+Alt+J)
  registerFirst([process.env.IRIS_MUTE_KEY, 'Control+Alt+B', 'Control+Alt+M', 'Control+Shift+Alt+M'].filter(Boolean), () => sendAction('mute'));
  // Debug: buka DevTools (lihat error konsol)
  registerShortcut('Control+Alt+D', () => {
    if (win) win.webContents.openDevTools({ mode: 'detach' });
  });
});

app.on('second-instance', () => {
  if (!win || win.isDestroyed()) return;
  peekShow();
  if (!win.isVisible()) win.show();
});

ipcMain.on('set-ignore-mouse', (_e, ignore) => {
  lastIgnoreReq = !!ignore;
  if (!win) return;
  applyIgnore();   // = perilaku lama, kecuali kursor sedang di atas panel /chrome
});
ipcMain.handle('web-panel', (e, line) => {
  if (!win || win.isDestroyed() || e.sender !== win.webContents) return { ok: false, msg: 'ditolak' };
  try { return webPanelCommand(String(line || '').slice(0, 600)); } catch (err) { console.warn('Chrome: galat perintah:', err && err.message); return { ok: false, msg: 'Galat: ' + (err && err.message) }; }
});

ipcMain.handle('web-state', (e) => {
  if (!win || win.isDestroyed() || e.sender !== win.webContents) return null;
  try { return webStateObj(); } catch { return null; }
});
// Fase 4: kualitas turun ke hemat (manual atau otomatis) = panel web ditutup dan renderernya dibuang. Dikirim renderer hanya saat tingkat berubah.
ipcMain.on('web-quality', (e, level) => {
  if (!win || win.isDestroyed() || e.sender !== win.webContents) return;
  if (level === 'hemat' && webPanel) { console.log('Chrome: kualitas hemat, panel ditutup untuk menghemat RAM.'); closeWebPanel('hemat'); }
});

ipcMain.on('quit', () => app.quit());

/* ---------- v19: seret karakter langsung + saklar selalu-di-atas ----------
   Posisi jendela mengikuti kursor GLOBAL (bukan koordinat dari renderer), jadi tidak ada selisih walau jendela ikut bergerak.
   setBounds dengan ukuran tetap (bukan setPosition) supaya ukuran jendela tidak melenceng di layar dengan skala 125%/150%. */
/* v23: dipentokkan ke pojok layar = kesakitan.
   Selama diseret, kursor global dipantau: masuk zona pojok (CORNER_PX dari dua tepi layar sekaligus) dengan kecepatan >= CORNER_SPEED px/dtk
   (diukur ~150 ms sebelum masuk), atau tertahan di pojok >= CORNER_DWELL ms, mengirim event 'corner-hit' {corner, power} ke renderer.
   Pojok yang bersebelahan dengan monitor lain tidak dihitung (kursor masih bisa lewat). Jeda antar benturan: CORNER_COOLDOWN ms. */
const CORNER_PX = 16, CORNER_DWELL = 700, CORNER_COOLDOWN = 2500;
const CORNER_SPEED = Number(process.env.IRIS_HIT_SPEED) || 650;
function cornerAt(c) {
  const d = screen.getDisplayNearestPoint(c), b = d.bounds;
  const nl = c.x <= b.x + CORNER_PX, nr = c.x >= b.x + b.width - 1 - CORNER_PX;
  const nt = c.y <= b.y + CORNER_PX, nb = c.y >= b.y + b.height - 1 - CORNER_PX;
  if (!((nl || nr) && (nt || nb))) return null;
  const sx = nl ? -1 : 1, sy = nt ? -1 : 1;
  const cx = nl ? b.x : b.x + b.width, cy = nt ? b.y : b.y + b.height;
  const inside = (o, p) => p.x >= o.bounds.x && p.x < o.bounds.x + o.bounds.width && p.y >= o.bounds.y && p.y < o.bounds.y + o.bounds.height;
  const others = screen.getAllDisplays().filter((o) => o.id !== d.id);
  if (others.some((o) => inside(o, { x: cx + sx * 10, y: cy - sy * 10 }) || inside(o, { x: cx - sx * 10, y: cy + sy * 10 }))) return null;
  return (nt ? 't' : 'b') + (nl ? 'l' : 'r');
}
/* v24: benturan ke SISI layar (kiri/kanan/atas/bawah), bukan cuma pojok. Hanya lewat kecepatan (tanpa dwell),
   supaya menyeret pelan ke tepi untuk bersembunyi tidak ikut dianggap benturan. Sisi yang bersebelahan dengan monitor lain diabaikan. */
const EDGE_PX = 10;
const EDGE_SPEED = Number(process.env.IRIS_EDGE_SPEED) || 900;
function edgeAt(c) {
  const d = screen.getDisplayNearestPoint(c), b = d.bounds;
  let e = null;
  if (c.x <= b.x + EDGE_PX) e = 'l';
  else if (c.x >= b.x + b.width - 1 - EDGE_PX) e = 'r';
  else if (c.y <= b.y + EDGE_PX) e = 't';
  else if (c.y >= b.y + b.height - 1 - EDGE_PX) e = 'b';
  if (!e) return null;
  const p = e === 'l' ? { x: b.x - 10, y: c.y } : e === 'r' ? { x: b.x + b.width + 10, y: c.y }
          : e === 't' ? { x: c.x, y: b.y - 10 } : { x: c.x, y: b.y + b.height + 10 };
  const other = screen.getAllDisplays().some((o) => o.id !== d.id && p.x >= o.bounds.x && p.x < o.bounds.x + o.bounds.width && p.y >= o.bounds.y && p.y < o.bounds.y + o.bounds.height);
  return other ? null : e;
}
function makeCornerWatch() {
  const cs = []; let inZone = false, zoneAt = 0, lastHit = 0;
  return (c) => {
    const now = Date.now();
    cs.push({ x: c.x, y: c.y, t: now });
    while (cs.length && now - cs[0].t > 400) cs.shift();
    const corner = cornerAt(c);
    const edge = corner ? null : edgeAt(c);
    if (!corner && !edge) { inZone = false; return; }
    if (now - lastHit < CORNER_COOLDOWN) { inZone = true; return; }
    let power = 0;
    if (!inZone) {
      inZone = true; zoneAt = now;
      const ref = cs.find((s) => now - s.t <= 150) || cs[0];
      const speed = Math.hypot(c.x - ref.x, c.y - ref.y) / (Math.max(30, now - ref.t) / 1000);
      if (speed >= (corner ? CORNER_SPEED : EDGE_SPEED)) power = Math.min(1, speed / 2500);
    } else if (corner && now - zoneAt >= CORNER_DWELL) power = 0.25;   // dijepit di pojok
    if (power > 0) {
      lastHit = now; zoneAt = now;
      if (win && !win.isDestroyed() && !win.webContents.isDestroyed()) win.webContents.send('corner-hit', { corner: corner || edge, power });
    }
  };
}
let dragIv = null, dragStop = null;
function stopDrag() {
  if (dragIv) { clearInterval(dragIv); dragIv = null; }
  if (dragStop) { clearTimeout(dragStop); dragStop = null; }
  if (dragBounds && win && !win.isDestroyed()) {
    const b = win.getBounds();
    if (b.width !== dragBounds.width || b.height !== dragBounds.height) win.setBounds({ x: b.x, y: b.y, width: dragBounds.width, height: dragBounds.height });
  }
  dragBounds = null;
}
let dragBounds = null;
function startDrag() {
  if (!win || win.isDestroyed()) return;
  webIdleNarrow();   // jendela lebar dari panel yang tersembunyi: sempit dulu supaya karakter bisa menempel di tepi layar
  peekShow(true);   // diseret dari tepi layar: kembali ke posisi asal dulu
  sitRelease('keep');   // v22: diangkat dari tepi jendela
  if (peek.anim) { clearInterval(peek.anim); peek.anim = null; }   // v46: batalkan luncuran kembali ke layar kalau sedang berjalan
  stopDrag();
  const c0 = screen.getCursorScreenPoint();
  const b0 = win.getBounds();
  dragBounds = b0;
  const cornerCheck = makeCornerWatch();
  let lx = b0.x, lt = Date.now(), vs = 0, sent = 0;   // v22: kecepatan jendela (px/dtk, dihaluskan) dikirim ke renderer untuk ayunan badan
  dragIv = setInterval(() => {
    if (!win || win.isDestroyed()) { stopDrag(); return; }
    const c = screen.getCursorScreenPoint();
    let x = b0.x + c.x - c0.x, y = b0.y + c.y - c0.y;
    const rawX = x;
    // sisakan minimal 120 px jendela di dalam layar terdekat, supaya karakter tidak hilang di luar layar
    const wa = screen.getDisplayNearestPoint(c).workArea, keep = 120;
    x = Math.max(wa.x - (b0.width - keep), Math.min(wa.x + wa.width - keep, x));
    y = Math.max(wa.y - (b0.height - keep), Math.min(wa.y + wa.height - keep, y));
    if (webExtra) {
      const t = clampToWork({ x, y, width: b0.width, height: b0.height }, wa, true); x = t.x; y = t.y;   // v46: panel /chrome terbuka: seluruh jendela tetap di dalam layar
      if (webPanelUp()) {   // v52b: sisi seberang panel boleh melewati tepi layar sampai karakter bisa mengintip (panel tetap di dalam layar)
        if (webSide === 'left') x = Math.max(t.x, Math.min(rawX, wa.x + wa.width - (PEEK_CHAR_CX + webExtra) + EDGE_SNAP));
        else x = Math.min(t.x, Math.max(rawX, wa.x - PEEK_CHAR_CX - EDGE_SNAP));
      }
    }
    win.setBounds({ x: Math.round(x), y: Math.round(y), width: b0.width, height: b0.height });
    cornerCheck(c);
    const nt = Date.now(), dts = Math.max(0.004, (nt - lt) / 1000); vs += (((x - lx) / dts) - vs) * 0.25; lx = x; lt = nt;
    if (nt - sent > 40 && !win.webContents.isDestroyed()) { sent = nt; win.webContents.send('drag-vel', Math.max(-1, Math.min(1, vs / 1500))); }
  }, 8);
  dragStop = setTimeout(stopDrag, 120000);   // jaring pengaman: mouseup hilang = berhenti sendiri setelah 2 menit
}
/* v46: jaga seluruh UI Iris (menu, bubble, bar input, panel /chrome) tetap di dalam layar.
   Dulu jendela boleh terseret sampai tersisa 120 px di layar; kalau dilepas di situ (tidak cukup dekat tepi untuk bersembunyi),
   menu dan panel terpotong tepi layar. Sekarang: (a) saat chat atau panel /chrome terbuka, seretan dibatasi ketat di dalam layar;
   (b) saat dilepas dan TIDAK bersembunyi di tepi, jendela meluncur balik ke dalam area kerja. RIGHT_PAD (kosong, tembus klik) boleh tetap keluar layar. */
function clampToWork(b, wa, strict) {
  wa = wa || screen.getDisplayMatching(b).workArea;
  // v48: karakter boleh MENEMPEL di tepi kiri layar (ruang kosong di kiri karakter, PEEK_CHAR_CX - 160 = 108 px, boleh keluar layar, seperti RIGHT_PAD di kanan).
  // strict (panel /chrome terbuka) = seluruh jendela harus di dalam layar di sisi kiri.
  const minX = strict ? wa.x : wa.x - (PEEK_CHAR_CX - 160);
  const maxX = wa.x + wa.width - (b.width - RIGHT_PAD);
  const maxY = Math.max(wa.y, wa.y + wa.height - b.height);
  // v63: mode fokus = karakter tersembunyi, yang terlihat hanya garis kecil di dasar jendela. Dulu batas atas tetap topSlack (~90 px), jadi garis tidak bisa naik
  // di atas tengah layar dan "balik ke tengah" saat dilepas. Sekarang jendela boleh naik sampai garis (dan pil statusnya) dekat tepi atas layar.
  const minY = quietMode ? wa.y - Math.max(0, b.height - 90) : wa.y - topSlack(b.height);   // ruang kosong (tembus klik) di atas kepala karakter boleh keluar layar, jadi karakter bisa naik sampai dekat tepi atas
  return { x: Math.round(Math.max(minX, Math.min(maxX, b.x))), y: Math.round(Math.max(minY, Math.min(maxY, b.y))) };
}
/* Seberapa jauh tepi atas jendela boleh di atas tepi atas layar. Bagian paling atas jendela hanya ruang kosong untuk bubble, tapi dulu dipaku ke tepi layar sehingga
   karakter "mentok" padahal masih ada ruang. Saat panel /chrome terbuka, bilah alamatnya (menempel ke bawah jendela) tetap harus di dalam layar, jadi batasnya lebih kecil. */
const TOP_SLACK = 90;
function topSlack(h) {
  if (!webExtra) return TOP_SLACK;
  const ph = Math.max(200, Math.min(webH(), h - 2 * WEB_MARGIN - WEB_TB));
  const barTop = h - WEB_MARGIN - ph - WEB_TB;   // jarak tepi atas bilah alamat dari tepi atas jendela (sama dengan layoutWebPanel)
  return Math.max(0, Math.min(TOP_SLACK, barTop - 6));
}
function settleOnScreen() {
  if (!win || win.isDestroyed() || dragIv || sit.on || peek.out) return;
  const b = win.getBounds(), t = clampToWork(b, null, !!webExtra);
  if (t.x === b.x && t.y === b.y) return;
  peekAnimate({ x: t.x, y: t.y }, { width: b.width, height: b.height }, null);
}
/* v21e: dilepas dekat tepi layar = langsung bersembunyi di tepi itu (seperti "diarahkan ke tembok").
   Patokannya tengah karakter: kalau jaraknya ke tepi monitor <= EDGE_SNAP px (boleh sudah di luar layar), karakter menyelinap ke tepi itu. */
const EDGE_SNAP = 70;
function edgeSnap() {
  if (!win || win.isDestroyed()) return;
  webIdleNarrow();
  const panelUp = webPanelUp();
  if (webExtra && !panelUp) { settleOnScreen(); return; }   // v46: panel sedang dibuka / ditutup: pastikan tetap di dalam layar
  const b = win.getBounds(), db = screen.getDisplayMatching(b).bounds, cx = b.x + PEEK_CHAR_CX + webLeftExtra();
  let edge = cx <= db.x + EDGE_SNAP ? 'left' : cx >= db.x + db.width - EDGE_SNAP ? 'right' : null;
  if (panelUp && edge && edge !== webFreeEdge()) edge = null;   // v52b: tepi di sisi panel tidak dipakai untuk mengintip
  if (edge && peekHide('drop', edge)) return;
  settleOnScreen();   // v46: tidak bersembunyi (chat terbuka, jauh dari tepi, atau terhalang monitor lain) = kembali ke dalam layar
}
/* v50: panel /chrome pindah sisi otomatis. Iris diseret sampai mentok di tepi layar sisi panelnya dan dilepas = panel pindah ke sisi seberang
   (kiri -> kanan kalau mentok kiri, kanan -> kiri kalau mentok kanan), asal sisi seberang cukup lega. Karakter tidak bergeser di layar. */
function flipWebSide(to) {
  if (!win || win.isDestroyed() || !webExtra || webSide === to) return;
  const b = win.getBounds(), ex = webExtra;
  const nb = { x: to === 'right' ? b.x + ex : b.x - ex, y: b.y, width: b.width, height: b.height };
  webSide = to;
  const apply = () => {
    if (!win || win.isDestroyed() || !webExtra) return;
    win.setBounds(nb);
    if (webPanel) { webX = webHome(); try { layoutWebPanel(); } catch { /* abaikan */ } }
    sendWebState();
  };
  if (to === 'right') {   // kunci lebar #root dulu, baru jendela pindah
    try { if (!win.webContents.isDestroyed()) win.webContents.send('web-side', 'right'); } catch { /* abaikan */ }
    setTimeout(apply, 50);
  } else {   // jendela pindah dulu, baru kunci lebar #root dilepas
    apply();
    try { if (!win.webContents.isDestroyed()) win.webContents.send('web-side', 'left'); } catch { /* abaikan */ }
  }
}
function maybeFlipWeb() {
  if (!win || win.isDestroyed() || !webExtra || !webPanel || webClosing) return false;
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea, ex = webExtra, EDGE = 40;
  if (webSide === 'left') {
    const roomR = b.x + ex + WEB_RIGHT_X + webW() + WEB_MARGIN <= wa.x + wa.width;
    if (b.x - wa.x <= EDGE && roomR) { flipWebSide('right'); return true; }
  } else {
    const roomL = b.x - ex >= wa.x;
    if (b.x >= wa.x + wa.width - (b.width - RIGHT_PAD) - EDGE && roomL) { flipWebSide('left'); return true; }
  }
  return false;
}
ipcMain.on('drag-window', (_e, on) => {
  if (on) { startDrag(); return; }
  const was = !!dragIv; stopDrag();
  if (was && maybeFlipWeb()) return;   // v50
  if (was) sitSnap().then((ok) => { if (!ok) edgeSnap(); }).catch(() => edgeSnap());   // v22: dilepas di tepi atas jendela = duduk; kalau tidak, cek tepi layar
});
ipcMain.on('set-sit', (_e, on, now) => {
  sit.enabled = !!on;
  if (!on) { sitRelease('fall'); return; }
  if (!now) return;   // saat startup tidak langsung naik; hanya saat pengguna menyalakan /duduk
  sitSnap(true).then((ok) => {
    if (!ok && !sit.on && win && !win.isDestroyed() && !win.webContents.isDestroyed()) win.webContents.send('sit-state', { on: false, none: true });
  }).catch(() => {});
});
ipcMain.on('set-top', (_e, on) => {
  if (!win || win.isDestroyed()) return;
  if (on) win.setAlwaysOnTop(true, 'screen-saver'); else win.setAlwaysOnTop(false);
});
// v47: renderer menanyakan apakah jendela menempel di tepi kiri layar; kalau ya, menu dan popover dipindah ke KANAN karakter (bukan ketahan di kiri)
const DOCK_LEFT_PX = 60;
ipcMain.handle('win-side', () => {
  if (!win || win.isDestroyed()) return { left: false };
  const b = win.getBounds(), wa = screen.getDisplayMatching(b).workArea;
  return { left: b.x - wa.x < DOCK_LEFT_PX, off: peek.out ? 0 : Math.max(0, Math.round(wa.x - b.x)) };   // v49: saat mengintip di tepi, jendela jauh di luar layar; jangan dipakai untuk menggeser bar
});
ipcMain.on('chat-open', (_e, open) => setChatOpen(open));
ipcMain.handle('chat-big', (_e, on) => setChatBig(!!on));   // v32
ipcMain.on('peek', (_e, on) => { if (on) peekHide(); else peekShow(); });
ipcMain.handle('capture-screen', (_e, opts) => captureScreenDataURL(opts && typeof opts === 'object' ? { quiet: !!opts.quiet, maxSide: opts.maxSide, quality: opts.quality } : {}));
// v23: detik sejak input terakhir (hanya angka, dari powerMonitor); dipakai /pantau supaya tidak memotret saat pengguna sedang pergi
ipcMain.handle('idle-time', () => { try { return powerMonitor.getSystemIdleTime(); } catch { return 0; } });
ipcMain.handle('read-clipboard', () => readClipboardPayload());
// Salin gambar (data URL) ke clipboard Windows; navigator.clipboard di jendela overlay sering ditolak
// v28b: clipboard.writeImage tidak selalu ada di Electron yang terpasang (terlihat di PC Kang Jiho: "clipboard.writeImage is not a function"),
// jadi urutannya: writeImage, lalu clipboard.write({image}), lalu PowerShell (Windows Forms SetImage). Gagal semua = false, dengan sebab di terminal.
function writeImageViaPowerShell(img) {
  return new Promise((resolve) => {
    let file = '';
    try {
      const dir = path.join(app.getPath('temp'), 'iris-view'); fs.mkdirSync(dir, { recursive: true });
      file = path.join(dir, 'clip-' + Date.now() + '.png');
      fs.writeFileSync(file, img.toPNG());
    } catch (e) { console.warn('copy-image: gagal menulis PNG sementara:', e.message || e); resolve(false); return; }
    const lit = file.replace(/'/g, "''");
    const cmd = `Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $i=[System.Drawing.Image]::FromFile('${lit}'); try { [System.Windows.Forms.Clipboard]::SetImage($i) } finally { $i.Dispose() }`;
    let done = false, timer = null;
    const finish = (ok) => { if (done) return; done = true; if (timer) clearTimeout(timer); try { fs.unlinkSync(file); } catch { /* abaikan */ } resolve(ok); };
    let p;
    try { p = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-STA', '-Command', cmd], { windowsHide: true, stdio: 'ignore' }); }
    catch (e) { console.warn('copy-image: PowerShell tidak bisa dijalankan:', e.message || e); finish(false); return; }
    timer = setTimeout(() => { try { p.kill(); } catch { /* abaikan */ } console.warn('copy-image: PowerShell terlalu lama'); finish(false); }, 10000);
    p.on('error', (e) => { console.warn('copy-image: PowerShell gagal:', e.message || e); finish(false); });
    p.on('exit', (code) => { if (code !== 0) console.warn('copy-image: PowerShell keluar dengan kode', code); finish(code === 0); });
  });
}
ipcMain.handle('copy-image', async (_e, dataUrl) => {
  try {
    const m = typeof dataUrl === 'string' && /^data:image\/(png|jpe?g|webp);base64,/i.exec(dataUrl);
    if (!m || dataUrl.length > 30e6) { console.warn('copy-image: format data URL tidak dikenali'); return false; }
    let img = nativeImage.createFromDataURL(dataUrl);
    if (img.isEmpty()) img = nativeImage.createFromBuffer(Buffer.from(dataUrl.slice(m[0].length), 'base64'));   // cadangan
    if (img.isEmpty()) { console.warn('copy-image: gambar tidak bisa didekode'); return false; }
    // v28c: clipboard.write({image}) di Electron ini = API web yang mengembalikan promise dan menolak diam-diam, jadi dihapus; hanya writeImage kalau ada, selain itu langsung PowerShell
    if (typeof clipboard.writeImage === 'function') {
      try { clipboard.writeImage(img); return true; } catch (e) { console.warn('copy-image: clipboard.writeImage gagal:', e.message || e); }
    }
    const have = []; for (const k in clipboard) { if (typeof clipboard[k] === 'function') have.push(k); }
    console.warn('copy-image: Electron', process.versions.electron, '- metode clipboard yang ada:', have.join(', ') || '(tidak ada)', '; mencoba PowerShell');
    return await writeImageViaPowerShell(img);
  } catch (e) { console.warn('copy-image gagal:', e.message || e); return false; }
});

// v24: buka gambar di jendela biasa yang besar: roda mouse = zoom, seret = geser, klik dua kali = ukuran asli / pas layar
let viewSeq = 0;
ipcMain.handle('open-image', (_e, dataUrl) => {
  try {
    const m = typeof dataUrl === 'string' && /^data:image\/(png|jpe?g|webp);base64,/i.exec(dataUrl);
    if (!m || dataUrl.length > 30e6) return false;
    const ext = m[1].toLowerCase().replace('jpeg', 'jpg');
    const dir = path.join(app.getPath('temp'), 'iris-view'); fs.mkdirSync(dir, { recursive: true });
    const id = Date.now() + '-' + (viewSeq++);
    const imgFile = path.join(dir, id + '.' + ext), htmlFile = path.join(dir, id + '.html');
    fs.writeFileSync(imgFile, Buffer.from(dataUrl.slice(m[0].length), 'base64'));
    fs.writeFileSync(htmlFile, `<!doctype html><meta charset="utf-8"><title>Gambar Iris (roda = zoom, seret = geser, klik 2x = ukuran asli)</title>
<style>html,body{margin:0;height:100%;overflow:hidden;background:#0b0f1a}img{position:absolute;left:0;top:0;transform-origin:0 0;user-select:none;-webkit-user-drag:none;cursor:grab}</style>
<img id="i" src="${id}.${ext}"><script>
const im=document.getElementById('i');let s=1,x=0,y=0,fit=1;
function ap(){im.style.transform='translate('+x+'px,'+y+'px) scale('+s+')';}
function fitIt(){fit=Math.min(innerWidth/im.naturalWidth,innerHeight/im.naturalHeight,1);s=fit;x=(innerWidth-im.naturalWidth*s)/2;y=(innerHeight-im.naturalHeight*s)/2;ap();}
im.onload=fitIt;addEventListener('resize',fitIt);
addEventListener('wheel',e=>{e.preventDefault();const k=e.deltaY<0?1.15:1/1.15,ns=Math.max(fit*0.5,Math.min(8,s*k));x=e.clientX-(e.clientX-x)*(ns/s);y=e.clientY-(e.clientY-y)*(ns/s);s=ns;ap();},{passive:false});
let d=null;addEventListener('mousedown',e=>{d={x:e.clientX-x,y:e.clientY-y};im.style.cursor='grabbing';});
addEventListener('mouseup',()=>{d=null;im.style.cursor='grab';});
addEventListener('mousemove',e=>{if(d){x=e.clientX-d.x;y=e.clientY-d.y;ap();}});
addEventListener('dblclick',e=>{if(Math.abs(s-1)<0.01){fitIt();}else{x=e.clientX-(e.clientX-x)*(1/s);y=e.clientY-(e.clientY-y)*(1/s);s=1;ap();}});
addEventListener('keydown',e=>{if(e.key==='Escape')window.close();});
</script>`, 'utf8');
    const disp = screen.getDisplayMatching(win && !win.isDestroyed() ? win.getBounds() : screen.getPrimaryDisplay().bounds).workArea;
    const v = new BrowserWindow({ x: disp.x + 40, y: disp.y + 40, width: Math.max(600, disp.width - 80), height: Math.max(400, disp.height - 80), autoHideMenuBar: true, backgroundColor: '#0b0f1a', webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true } });
    v.loadFile(htmlFile);
    v.on('closed', () => { try { fs.unlinkSync(imgFile); fs.unlinkSync(htmlFile); } catch { /* abaikan */ } });
    return true;
  } catch (e) { console.warn('open-image gagal:', e.message || e); return false; }
});

// Simpan HTML hasil ekspor percakapan ke folder Downloads (nama dibersihkan, tidak menimpa file yang sudah ada)
ipcMain.handle('save-html', (_e, payload) => {
  try {
    const { name, html } = payload || {};
    const dir = app.getPath('downloads');
    const base = String(name || 'Percakapan-Iris').replace(/[\\/:*?"<>|\x00-\x1f]/g, '_').replace(/\.html?$/i, '').slice(0, 80) || 'Percakapan-Iris';
    let file = path.join(dir, base + '.html');
    for (let i = 1; fs.existsSync(file); i++) file = path.join(dir, base + ' (' + i + ').html');
    fs.writeFileSync(file, String(html || ''), 'utf8');
    return { ok: true, path: file };
  } catch (e) {
    return { ok: false, error: String((e && e.message) || e) };
  }
});
// Tampilkan file hasil ekspor di Explorer (hanya file di dalam folder Downloads)
ipcMain.handle('reveal-file', (_e, p) => {
  try {
    const file = path.normalize(String(p || ''));
    if (path.dirname(file) !== path.normalize(app.getPath('downloads')) || !fs.existsSync(file)) return false;
    shell.showItemInFolder(file);
    return true;
  } catch { return false; }
});


/* ---------- v37: perintah lokal (media, volume, buka aplikasi daftar putih) ----------
   Dipanggil dari overlay lewat IPC 'local-cmd' (preload: localCmd). Hanya tiga jenis perintah dengan parameter yang divalidasi; TIDAK ADA eksekusi perintah bebas.
   media  : tombol media Windows (playpause, next, prev, mute, volup, voldown) lewat PowerShell keybd_event, 1 sampai 20 kali
   open   : nama harus ada di daftar bawaan di bawah atau di local-apps.json (folder userData); nilainya jalur file, link http(s), atau nama program bawaan Windows
   apps   : daftar nama yang boleh dibuka */
const MEDIA_VK = { playpause: 0xB3, next: 0xB0, prev: 0xB1, mute: 0xAD, voldown: 0xAE, volup: 0xAF };
const DEFAULT_LOCAL_APPS = {   // v37: dipersingkat jadi 3 aplikasi dulu; tambah sendiri lewat local-apps.json
  'chrome': 'chrome', 'google chrome': 'chrome', 'krom': 'chrome',
  'notepad': 'notepad', 'catatan': 'notepad',
  'task manager': 'taskmgr', 'pengelola tugas': 'taskmgr',
};
const LOCAL_APPS_FILE = () => path.join(app.getPath('userData'), 'local-apps.json');
function allLocalApps() {
  const apps = Object.assign({}, DEFAULT_LOCAL_APPS);
  try {
    const j = JSON.parse(fs.readFileSync(LOCAL_APPS_FILE(), 'utf8'));
    if (j && typeof j === 'object') for (const [k, v] of Object.entries(j)) if (typeof v === 'string' && v.trim()) apps[String(k).toLowerCase().trim()] = v.trim();
  } catch { /* file belum ada atau rusak: pakai daftar bawaan */ }
  return apps;
}
function sendMediaKey(key, count) {
  return new Promise((resolve) => {
    const vk = MEDIA_VK[key];
    const n = Math.max(1, Math.min(20, parseInt(count, 10) || 1));
    if (!vk) { resolve({ ok: false, error: 'tombol media tidak dikenal' }); return; }
    const script = '$s=\'[DllImport("user32.dll")] public static extern void keybd_event(byte b, byte s, uint f, UIntPtr e);\'; ' +
      'Add-Type -MemberDefinition $s -Name K -Namespace IrisKey; ' +
      '1..' + n + ' | ForEach-Object { [IrisKey.K]::keybd_event(' + vk + ',0,0,[UIntPtr]::Zero); [IrisKey.K]::keybd_event(' + vk + ',0,2,[UIntPtr]::Zero); Start-Sleep -Milliseconds 25 }';
    const enc = Buffer.from(script, 'utf16le').toString('base64');
    let p, done = false, timer = null;
    const finish = (r) => { if (done) return; done = true; if (timer) clearTimeout(timer); resolve(r); };
    try { p = spawn('powershell.exe', ['-NoProfile', '-NoLogo', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', enc], { windowsHide: true, stdio: 'ignore' }); }
    catch (e) { finish({ ok: false, error: 'PowerShell tidak bisa dijalankan' }); return; }
    timer = setTimeout(() => { try { p.kill(); } catch { /* abaikan */ } finish({ ok: false, error: 'PowerShell terlalu lama' }); }, 8000);
    p.on('error', () => finish({ ok: false, error: 'PowerShell gagal' }));
    p.on('exit', (code) => finish(code === 0 ? { ok: true } : { ok: false, error: 'PowerShell keluar dengan kode ' + code }));
  });
}
async function openLocalApp(name) {
  const key = String(name || '').toLowerCase().trim().slice(0, 40);
  const target = key ? allLocalApps()[key] : null;
  if (!target) return { ok: false, error: 'unknown-app' };
  try {
    if (/^https?:\/\//i.test(target)) { await shell.openExternal(target); return { ok: true }; }
    if (/[\\/]/.test(target) || /\.[a-z0-9]{2,4}$/i.test(target)) {   // jalur file atau berkas
      const err = await shell.openPath(target);
      return err ? { ok: false, error: err } : { ok: true };
    }
    if (!/^[a-z0-9_.-]+$/i.test(target)) return { ok: false, error: 'nama program tidak valid di daftar' };
    return await new Promise((resolve) => {   // nama program bawaan Windows (App Paths), mis. chrome, notepad, calc
      let c;
      try { c = spawn('cmd.exe', ['/d', '/c', 'start', '', target], { windowsHide: true, detached: true, stdio: 'ignore' }); }
      catch (e) { resolve({ ok: false, error: 'tidak bisa menjalankan ' + target }); return; }
      c.on('error', () => resolve({ ok: false, error: 'tidak bisa menjalankan ' + target }));
      c.on('exit', (code) => resolve(code === 0 ? { ok: true } : { ok: false, error: target + ' tidak ditemukan di komputer ini' }));
      c.unref();
    });
  } catch (e) { return { ok: false, error: String((e && e.message) || e) }; }
}
ipcMain.handle('local-cmd', async (_e, c) => {
  try {
    if (process.platform !== 'win32') return { ok: false, error: 'hanya untuk Windows' };
    if (!c || typeof c !== 'object') return { ok: false, error: 'perintah kosong' };
    if (c.type === 'media') return await sendMediaKey(String(c.key), c.count);
    if (c.type === 'open') return await openLocalApp(String(c.name || ''));
    if (c.type === 'apps') { const all = allLocalApps(); return { ok: true, apps: Object.keys(all), map: all }; }   // v37: map = nama -> program, supaya overlay bisa mengelompokkan alias
    return { ok: false, error: 'jenis perintah tidak dikenal' };
  } catch (e) { return { ok: false, error: String((e && e.message) || e) }; }
});
app.whenReady().then(() => console.log('Daftar aplikasi untuk perintah suara tambahan: ' + LOCAL_APPS_FILE() + '  (isi: {"spotify": "C:\\\\jalur\\\\Spotify.exe", "youtube": "https://www.youtube.com"})'));

app.whenReady().then(startWebBridge);   // v51: jembatan baca saja (mati kecuali IRIS_WEB_BRIDGE=1 dan COMPANION_TOKEN terisi)
app.on('will-quit', () => {
  try { if (bridgeSrv) bridgeSrv.close(); } catch { /* abaikan */ }
  try { for (const ss of webSessions) ss.flushStorageData(); } catch { /* abaikan */ }
  clearTimeout(saveTimer);
  savePos();
  psStop();
  globalShortcut.unregisterAll();
  if (tray) { tray.destroy(); tray = null; }
});
app.on('window-all-closed', () => app.quit());
