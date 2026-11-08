const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('companion', {
  setIgnoreMouse: (ignore) => ipcRenderer.send('set-ignore-mouse', ignore),
  quit: () => ipcRenderer.send('quit'),
  // Panel chat dibuka / ditutup: main.js memanjangkan / memendekkan jendela
  setChatOpen: (open) => ipcRenderer.send('chat-open', !!open),
  // v47: jendela menempel di tepi kiri layar? -> {left}. Dipakai index.html untuk memindah menu / popover ke kanan karakter
  winSide: () => ipcRenderer.invoke('win-side'),
  // v48: panel /chrome pindah ke kanan karakter ('right') atau kembali ke kiri ('left'); renderer mengunci / melepas lebar #root supaya karakter tidak melompat
  onWebSide: (cb) => { ipcRenderer.on('web-side', (_e, s) => cb(s)); },
  // v32: kotak chat dipanjangkan / dipendekkan (tombol di kepala panel). Mengembalikan tambahan tinggi (px) yang berhasil dipakai; 0 = tidak ada ruang
  setChatBig: (on) => ipcRenderer.invoke('chat-big', !!on),
  // Kursor global dari main.js: {x, y} relatif terhadap pojok kiri atas jendela (px)
  onCursor: (cb) => { ipcRenderer.on('cursor', (_e, p) => cb(p)); },
  // Hotkey global / menu tray "Buka chat"
  onOpenChat: (cb) => { ipcRenderer.on('open-chat', () => cb()); },
  // Screenshot layar: tombol kamera memanggil captureScreen(); hotkey / tray mengirim event 'screenshot'
  // v23: captureScreen({quiet, maxSide, quality}) untuk pemotretan otomatis (/pantau); getIdle() = detik sejak input terakhir
  captureScreen: (opts) => ipcRenderer.invoke('capture-screen', opts),
  getIdle: () => ipcRenderer.invoke('idle-time'),
  onScreenshot: (cb) => { ipcRenderer.on('screenshot', (_e, url) => cb(url)); },
  // v6: isi clipboard (teks / gambar) dan aksi global ('clipboard', 'mute', 'menu') dari hotkey atau tray
  readClipboard: () => ipcRenderer.invoke('read-clipboard'),
  // v16: salin gambar ke clipboard lewat main.js
  copyImage: (url) => ipcRenderer.invoke('copy-image', url),
  // v24: buka gambar di jendela besar terpisah (bisa zoom dan geser)
  openImage: (url) => ipcRenderer.invoke('open-image', url),
  onAction: (cb) => { ipcRenderer.on('action', (_e, name) => cb(name)); },
  // v15: menit aktif terus-menerus (dari waktu diam sistem; tidak membaca isi layar atau judul jendela), dikirim main.js tiap menit
  onActivity: (cb) => { ipcRenderer.on('activity', (_e, min) => cb(min)); },
  // v9: simpan ekspor percakapan (HTML) ke Downloads dan tampilkan di Explorer
  saveHtml: (name, html) => ipcRenderer.invoke('save-html', { name, html }),
  revealFile: (p) => ipcRenderer.invoke('reveal-file', p),
  // v35: perintah suara lokal tanpa LLM (handler 'local-cmd' ada di main.js)
  localCmd: (c) => ipcRenderer.invoke('local-cmd', c),
  // v19: seret karakter langsung (main.js menggerakkan jendela mengikuti kursor sampai dimatikan) dan saklar selalu-di-atas
  dragWindow: (on) => ipcRenderer.send('drag-window', !!on),
  setAlwaysOnTop: (on) => ipcRenderer.send('set-top', !!on),
  // v21: sembunyi di tepi layar. peek(true) = sembunyi, peek(false) = muncul; onPeek menerima {out, edge, error}
  peek: (on) => ipcRenderer.send('peek', !!on),
  onPeek: (cb) => { ipcRenderer.on('peek-state', (_e, s) => cb(s)); },
  // v22: duduk di tepi atas jendela lain. setSit(true) = izinkan membaca POSISI dan UKURAN jendela (bukan judul atau isinya); onSit menerima {on}
  setSit: (on, now) => ipcRenderer.send('set-sit', !!on, !!now),
  sitDebug: () => ipcRenderer.invoke('sit-debug'),   // /duduk cek: laporan kenapa Iris mau atau tidak mau duduk
  onSit: (cb) => { ipcRenderer.on('sit-state', (_e, s) => cb(s)); },
  // v22: kecepatan jendela saat diseret (-1..1, kanan positif) untuk ayunan badan
  onDragVel: (cb) => { ipcRenderer.on('drag-vel', (_e, v) => cb(v)); },
  // v23: diseret keras ke pojok layar: {corner: 'tl'|'tr'|'bl'|'br', power: 0..1}
  onHit: (cb) => { ipcRenderer.on('corner-hit', (_e, d) => cb(d)); },
  // v43: denyut render tiap sekitar 5 detik; main.js memuat ulang halaman kalau denyut berhenti (render macet)
  pulse: () => ipcRenderer.send('render-pulse'),
  // /chrome: mini-browser multi-akun. Satu pintu: main.js yang mengurai perintah ('chrome 2', 'akun tambah ...') dan mengembalikan {ok, msg}
  webPanel: (line) => ipcRenderer.invoke('web-panel', String(line || '')),
  // Fase 4: pil akun. onWebState menerima {open, slot, nama, akun:[{slot,nama}|null x5], reason}; webState() = keadaan sekarang (setelah halaman dimuat ulang);
  // webQuality(nama) memberi tahu main.js tingkat kualitas gambar, 'hemat' menutup panel web
  onWebState: (cb) => { ipcRenderer.on('web-state', (_e, s) => cb(s)); },
  webState: () => ipcRenderer.invoke('web-state'),
  webQuality: (name) => ipcRenderer.send('web-quality', String(name || '')),
  // pegangan ubah ukuran panel /chrome: true = mulai (main.js membaca kursor), false = selesai
  webGrip: (on) => ipcRenderer.send('web-grip', !!on),
  // v80: status layanan -> main.js mewarnai ikon tray. s = {worst: 'ok'|'warn'|'down'|'off', svc: {voicevox, ninerouter, hermes}}
  setHealth: (s) => ipcRenderer.send('health-state', s),
  // v80: tawaran aksi saat teks disalin (bawaan mati). setClipWatch(true) = main.js memeriksa teks clipboard tiap ~1,5 dtk; onClipOffer menerima teksnya
  setClipWatch: (on) => ipcRenderer.send('clip-watch', !!on),
  onClipOffer: (cb) => { ipcRenderer.on('clip-offer', (_e, t) => cb(t)); },
  // v80: simpan konfigurasi (JSON) ke Downloads; revealFile tetap dipakai untuk menampilkannya
  saveConfig: (name, json) => ipcRenderer.invoke('save-config', { name, json }),
  // v81: teks halaman yang sedang terbuka di panel /chrome (untuk /rangkum halaman); hanya atas perintah pengguna. {ok, url, host, title, text, truncated} atau {ok:false, error}
  webPageText: () => ipcRenderer.invoke('web-page-text'),
});
