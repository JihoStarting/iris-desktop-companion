# Roadmap Pendamping AI Desktop (2D/3D)

**by: KangJiho**

**Dimulai:** 28 Okt 2026 (folder proyek overlay dibuat)

Target: karakter AI yang tampil sebagai overlay di desktop (jendela transparan, selalu di depan), punya bubble chat, bersuara, dan bisa merespons apa yang ada di layar.

**Terakhir diperbarui:** 30 Okt 2026. Posisi sekarang: Fase 1, 2, dan 3 (jalur VRM) selesai, dan overlay tampil di desktop dengan avatar, suara, bubble, ekspresi, kedip, lip-sync moras, dan animasi idle `.vrma`. Sesi terakhir menambahkan hal berikut, yang baru dicek sintaksnya dan **belum dites di Electron**: click-through per piksel, kursor dan hotkey global, ikon tray, single-instance, posisi jendela tersimpan, klik per bagian tubuh, dan lampiran gambar di overlay. **Analisis gambar belum berfungsi penuh karena `server.py` belum diubah untuk menerima field `images`.** Berikutnya: tes visual dan fungsional semua itu, ubah `server.py` untuk vision, lalu Fase 5 sisa (push-to-talk dan STT).

---

## Stack

| Bagian | Teknologi | Status |
|---|---|---|
| Otak (LLM) | 9Router (endpoint OpenAI-compatible) | Sudah ada |
| Suara (TTS) | VOICEVOX headless, 四国めたん (Shikoku Metan) speaker ID 2 | Sudah ada |
| Backend | Python (FastAPI + websockets) | Selesai dan lolos semua uji Fase 1 |
| Frontend / overlay | Electron (jendela transparan) | Jalan |
| Avatar | VRM (`three` + `@pixiv/three-vrm`), model `assets/iris.vrm` | Jalan: idle, ekspresi. 13 gerakan prosedural jalan tapi dinilai creepy, perlu diperbaiki |
| STT (opsional) | faster-whisper | Belum |
| Screen awareness (opsional) | mss + model vision | Belum |
| Analisis gambar lampiran | Lampiran di overlay (tempel, 📎, seret) + model vision lewat 9Router | Overlay ditulis (belum dites), backend belum |

## Lingkungan kerja (Windows + WSL)

- **Electron wajib dijalankan di Windows**, bukan di WSL. Transparansi, always-on-top, dan click-through lewat WSLg tidak bisa diandalkan.
- **Backend Python disarankan jalan di Python Windows.** `mss` (screenshot, Fase 6) dan mic (Fase 5) tidak bisa menangkap layar/mic Windows dari dalam WSL. Satu lingkungan juga berarti semua layanan cukup lewat `localhost`.
- Kalau tetap memakai backend di WSL: server di `127.0.0.1:8765` bisa dibuka dari Windows lewat `localhost`. Tapi VOICEVOX dan 9Router yang jalan di Windows tidak terjangkau dari WSL2 mode default. Solusinya, buat `C:\Users\<nama>\.wslconfig`:
  ```
  [wsl2]
  networkingMode=mirrored
  ```
  lalu `wsl --shutdown` (butuh Windows 11 22H2+). Alternatif: isi `VOICEVOX_URL` dan `NINEROUTER_URL` dengan IP host Windows.

## Arsitektur

```
Mic/teks -> Python backend -> 9Router (LLM) -> teks balasan
                                    |
                          VOICEVOX (speaker 2) -> wav
                                    |  WebSocket
               Electron (jendela transparan): avatar + bubble + putar audio
```

Format pesan WebSocket (backend -> frontend), sesuai `server.py` saat ini:

```json
{
  "type": "segment",
  "text": "teks Indonesia untuk bubble",
  "jp": "teks Jepang yang diucapkan",
  "audio": "<wav base64 atau null>",
  "moras": [{"vowel": "a", "start": 0.00, "end": 0.12}],
  "emotion": "happy"
}
```

Tipe pesan lain dari backend: `{"type": "error", "message": "..."}` dan `{"type": "done", "interrupted": false}`.

Pesan dari frontend ke backend: `{"type": "user", "text": "..."}`, `{"type": "cancel"}` (hentikan balasan), `{"type": "reset"}` (hapus riwayat).

Untuk analisis gambar, pesan `user` boleh membawa field `images` (maksimal 4 data URL JPEG, sisi terpanjang 1280 px): `{"type": "user", "text": "...", "images": ["data:image/jpeg;base64,..."]}`. Tanpa gambar, field itu tidak ada dan pesannya sama seperti sebelumnya. Backend perlu mengubahnya menjadi pesan multimodal OpenAI-compatible (`content` berisi `text` dan `image_url`).

---

## Fase 0: Persiapan

- [ ] VOICEVOX jalan di `127.0.0.1:50021`
- [ ] Tes `audio_query` dan `synthesis` dengan `speaker=2`, hasilkan `test.wav`
- [ ] Catat base URL, nama model/combo, dan API key 9Router
- [ ] Tes satu request chat completion ke 9Router
- [ ] Install Node.js (LTS) dan Python 3.10+
- [x] Putuskan avatar: **VRM** (dipilih)

## Fase 1: Backend Python

- [x] Buat proyek: `server.py`, `requirements.txt`, `test_client.html`
- [x] Fungsi chat ke 9Router dengan streaming
- [x] Pecah balasan per baris/kalimat
- [x] Fungsi TTS: `audio_query` lalu `synthesis` (speaker 2)
- [x] Server WebSocket yang mengirim `{text, jp, audio, moras, emotion}` per kalimat
- [x] Kalimat pertama langsung dikirim tanpa menunggu balasan selesai (pembaca LLM dan sintesis suara berjalan paralel)
- [x] Cek Origin WebSocket (halaman web lain tidak bisa ikut menyambung)
- [x] Balasan bisa diinterupsi (`cancel`, pesan baru, `reset`, klien putus)
- [x] Pembersihan keluaran LLM (`<think>`, code fence)
- [x] **Uji:** buka `http://127.0.0.1:8765`, ketik teks, dengar suara
- [x] **Uji:** matikan VOICEVOX di tengah jalan, server tidak boleh crash
- [x] **Uji:** tekan Stop saat Metan bicara, balasan berhenti

**Format balasan LLM (diterapkan lewat system prompt):** satu baris per kalimat,

```
[emosi] kalimat Jepang ||| terjemahan Indonesia
```

VOICEVOX hanya membaca bahasa Jepang, jadi bagian Jepang diucapkan dan bagian Indonesia tampil di bubble. Emosi valid: `neutral, happy, sad, angry, surprised, shy`. Baris yang tidak sesuai format tetap tampil di bubble tanpa suara.

## Fase 2: Overlay Electron

- [x] Inisialisasi proyek Electron (di Windows, bukan WSL)
- [x] Jendela `transparent: true`, `frame: false`, `alwaysOnTop: true` (terlihat di atas jendela Steam)
- [x] Click-through di area kosong (`setIgnoreMouseEvents(true, { forward: true })`), nonaktifkan saat kursor di atas karakter (diuji di atas jendela Steam, aman)
- [x] Posisi default di pojok kanan bawah layar
- [x] Jendela bisa dipindah: seret tombol ✥ di bar bawah (memakai `-webkit-app-region: drag`, tanpa perubahan `main.js`)
- [x] Koneksi WebSocket ke backend (logika sama dengan `test_client.html`)
- [x] Putar audio yang diterima (antrian berurutan) (suara Metan keluar dari overlay, aman)
- [x] Click-through per piksel (`sampleHit()` di `index.html`): alpha piksel di bawah kursor dibaca lewat `readPixels` tepat setelah render, jadi area transparan di sekitar karakter tembus klik (sebelumnya seluruh kotak `#char` menghalangi). Saklar `PIXEL_HIT = false` mengembalikan perilaku lama. Hover juga dihitung dari kursor global (`probeAt()`), bukan hanya `mousemove`. Ditulis, belum dites
- [x] Hanya satu salinan overlay (`requestSingleInstanceLock`), jendela tampil lewat `showInactive()` supaya tidak merebut fokus dari game, dan posisi jendela diingat antar sesi (`overlay-state.json` di folder userData; dipakai hanya kalau masih di dalam layar). Ditulis, belum dites

## Fase 3: Avatar

**Jalur VRM (3D), dipakai**
- [x] Siapkan model `.vrm` (`assets/iris.vrm`, cek lisensinya sebelum publikasi)
- [x] Render dengan `three` + `@pixiv/three-vrm` (kamera diatur lewat objek `CAM` di `index.html`)
- [x] Animasi idle: napas, kedip, gerak kepala kecil
- [x] Ekspresi: happy, sad, angry, surprised, shy, neutral
- [x] Pose lengan turun dengan kalibrasi arah otomatis (`calibrateArms()`), tidak perlu lagi membalik tanda `ARM_DOWN` manual
- [x] Gerakan prosedural: `wave`, `cheer`, `nod`, `shake`, `think`, `shy`, `giggle`, `bow`, `sway`, `lookAround`, `surprise`, `stretch`, `huff`
  - dipicu otomatis saat Iris bicara (dipilih dari tag `emotion`), acak tiap 9 sampai 18 detik saat diam, dan saat karakter diklik
  - VRM sendiri tidak menyimpan animasi, jadi gerakan dibuat lewat kode. Gerakan baru: tambahkan satu entri di objek `GEST` dan daftar `GEST_BY_EMO`
- [x] Kamera otomatis (`fitCamera()`, parameter `CAM.auto`, `CAM.headroom`, `CAM.bottom`): framing dihitung dari tinggi model supaya kepala dan tangan terangkat muat. Angkatan lengan `wave`, `cheer`, `stretch` juga dikurangi (tangan sebelumnya terpotong di atas frame)
- [ ] **Perbaiki gerakan prosedural: hasil tes dinilai creepy semua** (lihat "Masalah diketahui" di bawah)
- [x] Mata dan kepala mengikuti kursor (`updateGaze()`): berfungsi di dalam jendela overlay. Kursor di luar jendela: `main.js` mengirim `screen.getCursorScreenPoint()` tiap 40 ms (hanya saat posisi berubah) lewat IPC, `preload.js` mengeksposnya sebagai `onCursor`, dan `index.html` menerimanya (ditulis, belum dites)
- [x] Muat file animasi `.vrma` (VRM Animation) lewat `@pixiv/three-vrm-animation` (`loadIdleVRMA()`, paket 3.5.5 terpasang). Kode ditulis, belum dites visual
- [x] Klik per bagian tubuh (`buildColliders()`, `pickPart()`, `touchReact()` di `index.html`): bola tak terlihat di kepala, badan, lengan, dan tangan, lalu raycast saat klik. Kepala memberi `shy`, badan `surprised`, lengan dan tangan `happy`; klik di bagian opak lain tetap memicu gerakan acak. Cek posisi bola dengan `showColliders()` di konsol (Ctrl+Alt+D). Ditulis, belum dites

### Masalah diketahui: gerakan prosedural terlihat creepy (dicatat 30 Okt 2026)

**Status 30 Okt 2026:** gerakan sudah ditulis ulang (v2) di `index.html`, belum dites visual. Perubahan: `ARM_MIN` sebagai pagar supaya lengan tidak pernah terentang atau terangkat, gerakan lengan dibuat kecil dan ditekuk ke depan, `wave` dihapus dari gerakan acak saat diam, gerakan acak lebih jarang (14 sampai 28 detik), transisi lebih lambat, dan mata ikut bergerak kecil (`updateGaze()`). Tes lewat konsol (Ctrl+Alt+D): `testAll()` memutar semua gerakan satu per satu, `play('nama')` memutar satu gerakan. Centang usulan di bawah setelah hasilnya dinilai natural.

Gejala dari screenshot tes sebelum perbaikan (kamera sudah auto-fit, framing aman):
- Kedua lengan terentang lurus ke samping seperti pose T. Lengan kanan tampak seperti lembaran datar atau sayap karena kain lengan baju ikut membentang.
- Kedua lengan lurus ke atas hampir vertikal (mirip `cheer`/`stretch`), kaku dan siku tidak menekuk.
- Pose lengan setengah terentang di sela gerakan.

Dugaan penyebab (belum diverifikasi):
- Transisi masuk/keluar gerakan menyapu lengan lewat pose terentang (sudut `down` mendekati 0), jadi T-pose terlihat sesaat.
- Gerakan hanya memutar lengan atas dan siku. Bahu, puntiran lengan bawah, dan jari tidak ikut, jadi terlihat robotik.
- Amplitudo besar dan gerak sinus murni terlihat tidak alami. Gerakan acak tiap 9 sampai 18 detik dan klik karakter memicunya tanpa konteks.
- Bentuk lengan model (kain lengan lebar) mungkin tidak cocok dengan rotasi besar.

Usulan perbaikan (urutan kerja):
- [ ] Tes tiap gerakan satu per satu (misalnya lewat tombol debug) untuk menilai mana yang paling aneh
- [ ] Sementara nonaktifkan gerakan lengan besar, sisakan gerakan kepala (`nod`, `shake`, `lookAround`) dan gerakan kecil
- [ ] Batasi lengan supaya tidak melewati horizontal, dan perbaiki transisi supaya tidak menyapu lewat pose terentang
- [ ] Tambah gerakan bahu (`leftShoulder`, `rightShoulder`) dan siku yang lebih lembut
- [ ] Kurangi frekuensi gerakan acak dan gerakan saat bicara
- [ ] Pertimbangkan animasi `.vrma` dari mocap/Mixamo (item opsional di atas) kalau gerakan kode tetap kaku

**Jalur Live2D (2D), tidak dipakai**
- [ ] Siapkan model Live2D (`.model3.json`)
- [ ] Render dengan `pixi-live2d-display`
- [ ] Idle motion dan ekspresi sesuai model

## Fase 4: Bubble chat dan lip-sync

- [x] Bubble HTML/CSS di dekat karakter. Teks muncul bertahap per karakter (aman untuk emoji dan huruf Jepang) dan lamanya mengikuti durasi suara; belum dites visual
- [x] Bubble menghilang otomatis setelah beberapa detik
- [x] Lip-sync versi 1 (prototipe): volume audio (`AnalyserNode`) jadi bar di `test_client.html`. Sudah dipetakan ke bukaan mulut `aa` avatar di `index.html`
- [x] Lip-sync versi 2: data `moras` (`vowel`, `start`, `end`) untuk bentuk mulut a/i/u/e/o (`updateVisemes()` di `index.html`; cadangan volume, lalu goyang prosedural kalau analyser mati; belum dites visual. Mulut terlambat atau terlalu cepat: ubah `LIP_OFFSET`)
- [x] Tag `emotion` dari LLM dipetakan ke ekspresi wajah dan gerakan tubuh avatar

## Fase 5: Input

- [x] Kotak input teks kecil (sudah ada di overlay)
- [x] Panel chat dengan riwayat (tombol 💬 atau Ctrl+Alt+C dari mana saja): balasan Iris bisa dibaca ulang, tombol Hapus (kirim `reset`), Esc menutup. Ada "Mode jelaskan": pertanyaan diberi awalan supaya Iris menjelaskan lebih panjang (5 sampai 8 kalimat), format `[emosi] jp ||| id` tetap
- [x] Hotkey global `Ctrl+Alt+C` untuk membuka chat saat jendela tidak fokus (`globalShortcut` di `main.js` menampilkan dan memfokuskan jendela lalu mengirim IPC `open-chat`; `preload.js` mengeksposnya sebagai `onOpenChat`). Karena dikonsumsi secara global, pintasan toggle di dalam jendela tidak lagi berjalan; chat ditutup dengan Esc atau tombol ✕. Ditulis, belum dites (kalau input tidak langsung fokus, itu pembatasan fokus Windows)
- [ ] Push-to-talk atau wake word
- [ ] STT dengan faster-whisper (jalankan di Python Windows), hasilnya dikirim ke backend

## Analisis gambar (lampiran)

Memberi gambar ke Iris supaya dianalisis oleh model vision.

- [x] Overlay: tempel dengan `Ctrl+V` (mis. hasil `Win+Shift+S`), tombol 📎, atau seret file gambar ke karakter atau bar input. Thumbnail tampil di atas bar (maksimal 4, ada tombol ✕), gambar dikecilkan ke sisi terpanjang 1280 px dan dijadikan JPEG, dikirim lewat field `images`, dan riwayat chat menampilkan thumbnail. Enter tanpa teks memakai prompt bawaan. Ditulis, belum dites
- [ ] Backend `server.py`: terima `images`, ubah jadi `content` multimodal (`text` + `image_url` berisi data URL), pakai model yang mendukung gambar lewat variabel baru `NINEROUTER_VISION_MODEL`, dan jangan menyimpan data gambar di riwayat (ganti dengan penanda teks seperti "[gambar]") supaya konteks tidak membengkak. **Butuh file `server.py` untuk disambungkan.**
- [ ] Cek model: combo 9Router harus berisi model yang menerima gambar (Gemini flash-lite menerima; stepfun dan poolside belum tentu). Cek juga batas ukuran pesan WebSocket server
- [ ] Tes seret file dari Explorer ke karakter (jendela tembus klik bisa menolak drop; cadangannya `Ctrl+V` atau 📎) dan cek dialog 📎 tidak tertutup jendela overlay yang selalu di depan
- [ ] (opsional) Tombol ambil screenshot layar langsung dari overlay, memakai jalur gambar yang sama dengan Fase 6

## Fase 6: Screen awareness (opsional)

- [ ] Screenshot berkala dengan `mss` (misalnya tiap 30-60 detik), jalankan di Python Windows
- [ ] Kirim ke model vision (lewat 9Router atau Ollama)
- [ ] Karakter berkomentar tentang yang sedang dilihat
- [ ] Tombol/hotkey untuk mematikan fitur ini kapan saja

## Fase 7: Polish

- [ ] Memori percakapan (ringkasan jangka panjang)
- [x] Persona dan gaya bicara lewat system prompt (Iris, lihat bagian Persona)
- [x] Ikon tray (`setupTray()` di `main.js`, butuh `assets/tray.png`): tampilkan atau sembunyikan, buka chat, bisukan suara (`setAudioMuted`; lip-sync tetap jalan), pindah ke pojok kanan bawah, keluar. Ditulis, belum dites
- [ ] Auto-start bersama Windows
- [ ] Penanganan error: VOICEVOX mati, 9Router timeout (sebagian sudah ada: error dikirim ke klien sebagai `{"type": "error"}`)

---

## Cara menjalankan

### Struktur folder saat ini

Semua file ada di satu folder: `Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron` (`server.py`, `.venv`, `requirements.txt`, `test_client.html`, serta `main.js`, `preload.js`, `index.html`, `package.json`, `node_modules`). Rencananya nanti dirapikan menjadi subfolder `backend` dan `overlay`, tapi jangan memindahkan `.venv` sebelum semuanya stabil. Folder `assets/` berisi `iris.vrm`, `animations/idle_loop.vrma`, dan `tray.png`.

### Jendela 1: server (Fase 1)

Di PowerShell Windows, dari folder proyek:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# opsional, sesuaikan dengan 9Router-mu
$env:NINEROUTER_URL = "http://localhost:20128/v1"
$env:NINEROUTER_API_KEY = "isi-key-dari-dashboard-9router"   # wajib kalau 'Require API key' aktif
$env:NINEROUTER_MODEL = "nama-model-atau-combo"
# opsional: default sudah "Rover" (sesuai persona Iris)
$env:COMPANION_USER_NAME = "Rover"

python server.py
# atau, tanpa activate: .\.venv\Scripts\python.exe server.py
```

1. Buka `http://localhost:8765/health`. VOICEVOX dan 9Router tidak boleh menampilkan `ERROR`.
2. Buka `http://127.0.0.1:8765` (ketik manual di browser, jangan klik dua kali `test_client.html`), ketik "halo", dan suara Metan harus keluar kalimat demi kalimat.

Variabel lain yang bisa diubah: `VOICEVOX_URL`, `VOICEVOX_SPEAKER`, `COMPANION_HOST`, `COMPANION_PORT`.

### Jendela 2: overlay Electron (Fase 2)

Jendela PowerShell terpisah, server tetap jalan:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd "Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron"
npm start
```

Pertama kali, `npm install --save-dev electron` dan unduhan biner Electron (ratusan MB) harus selesai tanpa error. Pintasan global: `Ctrl+Alt+Q` keluar, `Ctrl+Alt+H` sembunyikan atau tampilkan, `Ctrl+Alt+C` buka chat, `Ctrl+Alt+D` DevTools. Kalau ada pintasan yang bentrok dengan aplikasi lain, terminal `npm start` menampilkan "Pintasan global gagal didaftarkan". Menu tray ada di ikon `assets/tray.png`.

## Persona: Iris

System prompt di `server.py` (v3) memakai persona Iris, yaitu I.R.I.S. (Intelligent Retrieval & Indexing System), teman sekelas playful dari Wuthering Waves. Memanggil user "Rover" atau "Classmate", Indonesia campur slang, jokes tipis-tipis nusuk, jawaban singkat 1 sampai 3 baris. Aturan format `[emosi] jp ||| id` tetap. Sumber persona: skill Hermes di `~/.hermes/skills` (`iris-persona`, `iris-modes`). Aturan khusus chat teks Hermes (label `[jokes]`, label mode, struktur ilmiah, aturan hapus sesi) sengaja tidak dipakai karena akan tampil dan terbaca di bubble. Menyambung langsung ke API server Hermes dicatat sebagai opsi untuk Fase 7 (memori), dengan risiko latensi dan format yang bisa kacau.

---

## Troubleshooting (dari tes Fase 1 dan 2)

- **Status "terputus, mencoba lagi..." terus:** pastikan `python server.py` benar-benar hidup ("Uvicorn running...") dan buka lewat `http://127.0.0.1:8765`, alamat persis seperti yang dicetak server. Catatan: `origin_ok` di `server.py` mengizinkan Origin `null`, `file://`, `localhost`, dan `127.0.0.1`, jadi Origin bukan penyebabnya untuk klien lokal.
- **9Router 401 "Missing API key":** `NINEROUTER_API_KEY` belum diisi. Fitur "Require API key" di dashboard 9Router aktif, jadi key wajib.
- **9Router 401 "Invalid API key":** key tidak terbaca atau salah. Sintaks yang benar: `$env:NINEROUTER_API_KEY = "sk-..."` (nama variabel tetap, key di dalam tanda kutip). Cek dengan `$env:NINEROUTER_API_KEY.Length`.
- **Variabel `$env:` tidak ikut:** nilainya hanya berlaku di jendela PowerShell tempat diisi dan hanya dibaca saat `python server.py` dimulai. Restart server setelah mengubahnya, dan jangan menjalankan dua server sekaligus di port 8765.
- **Request pertama lama ("menunggu balasan..."):** combo Iris merutekan ke model di belakangnya (contoh yang tercatat: `gemini-3.5-flash-lite`) dan permintaan pertama bisa lambat. Kalau terus lambat, coba pakai model tunggal yang cepat lewat `NINEROUTER_MODEL`, atau lihat log di dashboard 9Router.
- **`/v1/models` berhasil belum berarti key valid:** uji key lewat `/v1/chat/completions`.
- **`npm` diblokir ("running scripts is disabled"):** jalankan `Set-ExecutionPolicy -Scope Process Bypass` di jendela itu, atau pakai `npm.cmd`. Harus diulang di setiap jendela PowerShell baru.
- **`npm install` salah folder:** jalankan `cd` ke folder proyek dulu. Kalau sempat jalan di `C:\Users\<nama>`, hapus `package.json`, `package-lock.json`, dan `node_modules` yang terbentuk di sana (jika memang baru dibuat).
- **Unduhan Electron terputus (`TypeError: terminated`):** ulangi `node node_modules\electron\install.js` sampai selesai. Kalau sering putus, set `$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"` lalu ulangi.
- **`.venv\Scripts\activate` tidak jalan atau `No module named 'uvicorn'`:** `cd` ke folder tempat `.venv` berada, atau panggil langsung `.\.venv\Scripts\python.exe server.py`. Tanda venv aktif adalah awalan `(.venv)` di prompt. Jika masih kurang paket: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **File unduhan bernama `index (1).html`:** ganti nama menjadi `index.html` persis, karena `main.js` memuat nama itu.
- **Tangan terpotong di atas frame saat gerakan angkat tangan:** kamera terlalu ketat. Sudah diperbaiki lewat `fitCamera()`. Kalau masih terpotong, naikkan `CAM.headroom` (misalnya 0.3). Kalau model terlalu kecil, turunkan `headroom` atau naikkan `CAM.bottom`. Konsol harus menampilkan baris "Kamera auto: ...".
- **Gerakan terlihat creepy (lengan lurus ke samping atau ke atas, kaku):** belum diperbaiki, lihat "Masalah diketahui" di bawah Fase 3.
- **Avatar berpose tangan terangkat terus:** penyebabnya tanda arah rotasi lengan terbalik untuk model tertentu. Sudah diperbaiki lewat `calibrateArms()` (mencoba kedua arah, memilih yang membuat tangan di bawah bahu). Cek konsol (Ctrl+Alt+D), harus ada baris "Kalibrasi lengan: D = ...".
- **Gerakan menekuk ke arah aneh (siku ke belakang, tangan menembus badan):** model dengan rig berbeda. Balik tanda angka `fwd` atau `elbow` pada gerakan terkait di objek `GEST`.
- **Jendela tidak bisa dipindah:** seret tombol ✥ (bukan badan karakter). Klik badan karakter sengaja dipakai untuk bereaksi (reaksi per bagian tubuh atau gerakan acak). Kalau ✥ tidak bergerak di Windows kamu, tambahkan IPC `moveBy` di `main.js`/`preload.js` (kirim file keduanya kalau perlu bantuan).
- **Karakter tidak bisa diklik, atau klik tembus ke jendela di belakangnya:** hit-test per piksel gagal membaca alpha. Ubah `PIXEL_HIT` menjadi `false` di `index.html` (kembali ke perilaku lama: seluruh kotak karakter bisa diklik) dan kirim isi konsol.
- **Ctrl+Alt+C tidak membuka chat:** pintasan dipakai aplikasi lain (terminal menampilkan \"Pintasan global gagal didaftarkan\"). Kalau chat terbuka tapi kotak input tidak fokus, itu pembatasan fokus Windows; klik kotak inputnya sekali.
- **Ikon tray tidak muncul:** `assets/tray.png` tidak ada; terminal menampilkan \"Ikon tray tidak ditemukan\". Letakkan file itu di folder `assets`.
- **Overlay tidak mau jalan dua kali:** disengaja (single-instance). Salinan kedua langsung menutup dan menampilkan salinan pertama.
- **Posisi jendela salah setelah ganti monitor:** pakai menu tray \"Pindah ke pojok kanan bawah\", atau hapus `overlay-state.json` di folder userData Electron (biasanya `%APPDATA%\\ai-companion-overlay`).
- **Bola sentuhan salah posisi atau ukuran:** ketik `showColliders()` di konsol (Ctrl+Alt+D) untuk melihatnya, lalu sesuaikan daftar `defs` di `buildColliders()`.
- **Iris menjawab gambar tanpa benar-benar melihatnya:** `server.py` belum diubah untuk membaca field `images`, jadi gambar diabaikan. Jangan tes analisis gambar sebelum itu selesai.
- **Gambar ditolak atau error dari model:** model di combo tidak mendukung gambar. Pakai model vision lewat `NINEROUTER_VISION_MODEL` (setelah backend diubah).
- **Seret file gambar ke overlay tidak berhasil:** jendela tembus klik bisa menolak drop dari Explorer. Pakai `Ctrl+V` atau tombol 📎.
- **Jangan membagikan API key** di chat, screenshot, atau file roadmap ini.

## Hasil analisis AIRI (moeru-ai/airi, MIT) dan yang sudah diambil

Kode AIRI tidak disalin: ditulis dengan TypeScript, Vue, dan paket monorepo mereka, sedangkan `index.html` kita JavaScript biasa. Yang diambil hanya teknik dan idenya, dan angkanya diatur sendiri:
- [x] Penghalusan mulut eksponensial dengan kecepatan buka dan tutup berbeda (`LIP_ATTACK`, `LIP_RELEASE`), dari perubahan lip-sync AIRI
- [x] Batas FPS (`FPS_IDLE` 30, `FPS_ACTIVE` 60) supaya overlay ringan di atas game, dari ide performance runtime AIRI
- [x] Teks bubble bertahap, dari ide streaming text animation AIRI
- [x] Animasi idle `.vrma` dari AIRI (`assets/animations/idle_loop.vrma`, dimuat `loadIdleVRMA()`): mixer menggerakkan badan, lapisan prosedural hanya menambah (kepala menoleh, bicara, gerakan kecil). Butuh `npm install @pixiv/three-vrm-animation`; kalau gagal dimuat, otomatis kembali ke gerakan prosedural. Belum dites visual. Cek asal-usul dan lisensi file `.vrma` sebelum publikasi
- [x] Angka lip-sync dan bobot ekspresi disamakan dengan AIRI (`LIP_ATTACK` 50, `LIP_RELEASE` 30, `LIP_GAIN`, emosi 0.7 sampai 0.8)
- [x] Kursor di seluruh layar dan hotkey chat global: pola `screen.ts` (main process membaca `screen.getCursorScreenPoint()` berkala dan mengirim hanya saat berubah) dan `global-shortcut.ts`, ditulis ulang di `main.js` dan `preload.js` dengan JavaScript biasa. Belum dites
- [ ] Crossfade antar animasi (AIRI: `crossFadeDuration` 0,3 detik) kalau nanti ada lebih dari satu file `.vrma`
- [ ] Mikrofon dan deteksi bicara di sisi klien (Fase 5), lalu kirim ke faster-whisper
- [x] Hit-test per piksel (`hit-test.ts`, `render-target.ts`): AIRI merender ke render target kecil; kita membaca alpha langsung dari kanvas dengan `readPixels` setelah render, lebih ringan
- [x] Collider per bagian tubuh (`interaction.ts`): bola di titik tengah tulang (bukan kotak berarah, supaya tidak tergantung sumbu tulang), raycast saat klik
- [x] Pola Electron dari `main/`: single-instance guard, `showInactive()` supaya tidak merebut fokus, tray, simpan posisi jendela (dengan debounce, tidak di setiap event `move`)
- [ ] Belum diambil: `VRMUtils.removeUnnecessaryVertices` dan `combineSkeletons` (performa, tes dulu), `uiohook-napi` untuk push-to-talk tahan tombol (modul native; alternatif tanpa modul native: mode toggle dengan `globalShortcut`), `powerMonitor` (hentikan screenshot saat layar terkunci, untuk Fase 6)

## Risiko dan catatan

- **Lisensi model avatar:** pastikan boleh dipakai untuk tujuan kamu.
- **Lisensi suara:** cek ketentuan kredit VOICEVOX dan karakter Shikoku Metan sebelum dipublikasikan.
- **Privasi screen awareness:** screenshot bisa memuat data sensitif. Pakai model lokal bila memungkinkan dan sediakan tombol mati.
- **Privasi gambar lampiran:** gambar dikirim lewat 9Router ke model vision di cloud (mis. Gemini). Jangan melampirkan screenshot yang memuat data sensitif.
- **Keamanan lokal:** server hanya bind ke `127.0.0.1` dan menolak Origin asing. Jangan ubah `COMPANION_HOST` ke `0.0.0.0` tanpa autentikasi.
- **Latensi:** streaming dan pengiriman per kalimat penting supaya respons terasa cepat.
- **Click-through di Electron:** perilakunya agak berbeda antar OS, jadi uji lebih awal di Fase 2.
- **Kepatuhan format LLM:** model tertentu bisa mengabaikan format `[emosi] jp ||| id`. Kalau sering terjadi, pertimbangkan model lain atau contoh tambahan di system prompt.

## Urutan kerja yang disarankan

1. Fase 0 sampai 1: pastikan teks masuk, suara keluar. **(selesai)**
2. Fase 2: overlay Electron di desktop. **(selesai: tampil, tersambung, click-through dan audio aman)**
3. Fase 3: avatar VRM dengan idle, ekspresi, dan gerakan. **(jalan; gerakan v2, animasi idle `.vrma`, dan klik per bagian tubuh sudah ditulis, belum dites visual)**
4. Tes visual dan fungsional hasil sesi terakhir: click-through per piksel, kursor dan hotkey global, tray, posisi tersimpan, `.vrma`, klik per bagian tubuh (lihat bagian Troubleshooting kalau ada yang gagal).
5. Analisis gambar: ubah `server.py` (field `images`, model vision), lalu tes tempel, 📎, dan seret.
6. Fase 4 sisa: tes visual lip-sync v2 dan teks bubble bertahap.
7. Fase 5 sampai 7: input suara (push-to-talk, STT), screen awareness, memori, dan auto-start.
