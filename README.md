<p align="center">
  <img src="docs/img/iris-launcher-logo.png" alt="Logo IRIS" width="280">
</p>

# IRIS: AI Companion Desktop Overlay

![License](https://img.shields.io/badge/license-All%20rights%20reserved-red)
![Electron](https://img.shields.io/badge/Electron-overlay-47848F)
![Python](https://img.shields.io/badge/Python-FastAPI-3776AB)
![Platform](https://img.shields.io/badge/platform-Windows%20%2B%20WSL2-0078D6)

IRIS adalah teman AI yang tinggal di desktop. Wajahnya avatar 3D (VRM) yang melayang di atas aplikasi lain, suaranya dari VOICEVOX, dan tangannya adalah **Hermes Agent** yang bisa mengerjakan tugas nyata di komputer (membuka folder, mencari file, menjalankan perintah, mencari di web).

Proyek ini dibuat sebagai proyek pribadi dan masih terus dikembangkan. Catatan pengembangan lengkap (riwayat versi, hasil uji, dan keputusan desain) ada di [`docs/iris-companion-gabungan.md`](docs/iris-companion-gabungan.md).

---

## Status

- Hermes Agent dipasang: 28 September 2026
- Overlay mulai dikembangkan: 28 Oktober 2026
- Dipublikasikan di GitHub: 5 November 2026
- Versi terbaru: v1.0.0 (peluncur `IrisLauncher.exe`)
- Status: aktif dikembangkan sebagai proyek pribadi

Sebagian fitur sudah lulus uji di PC pengembang, sebagian lain baru ditulis dan belum diuji penuh. Daftarnya ada di [Status pengujian](#status-pengujian).

---

## Daftar isi

- [Status](#status)
- [Fitur](#fitur)
- [Arsitektur](#arsitektur)
- [Teknologi](#teknologi)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Menjalankan](#menjalankan)
- [Peluncur, cek kesehatan, dan layanan](#peluncur-cek-kesehatan-dan-layanan)
- [Perintah chat](#perintah-chat)
- [Pintasan keyboard](#pintasan-keyboard)
- [Mini-browser `/chrome`](#mini-browser-chrome)
- [Jembatan baca-saja untuk Hermes](#jembatan-baca-saja-untuk-hermes)
- [Kemampuan Hermes Agent](#kemampuan-hermes-agent)
- [Keamanan](#keamanan)
- [Status pengujian](#status-pengujian)
- [Rencana](#rencana)
- [Struktur proyek](#struktur-proyek)
- [Aset](#aset)
- [Pemecahan masalah](#pemecahan-masalah)
- [Dokumentasi](#dokumentasi)
- [Lisensi](#lisensi)

---

## Fitur

### Avatar dan tampilan

- Avatar VRM 3D dalam jendela Electron transparan yang selalu di atas, dengan klik tembus di area kosong
- Ekspresi dan gerak halus (pegas teredam, crossfade), bernapas, berkedip asimetris, dan menatap kursor dengan lirikan yang tenang
- Gerak kepala saat bicara mengikuti energi suara; pose `think` ditahan selama agen bekerja
- **Mood** yang bertahan antarhari: skor tersimpan dan memengaruhi ekspresi, ambang ngambek, sapaan, dan nada bicara (`/mood`)
- **Ganti baju**: maid (bawaan), gaun pesta prom, dan seragam sekolah. Baju juga bisa berganti otomatis menurut situasi dan musim (tidur, fokus, sesi belajar, malam)
- **Tema warna**: Iris (bawaan), empat musim, dan Otomatis, lengkap dengan efek jatuh musiman (`/tema`)
- **Tampilan badan**: tubuh penuh sampai kaki atau setengah badan (`/badan`), kamera dihitung ulang tanpa restart
- Bayangan siluet yang berubah per keadaan (diam, diangkat, mengintip, duduk), render HD (`/bayangan`)
- Bubble di atas kepala dengan teks Indonesia, kalimat Jepang berlabel 日本語, dan garis aksen sesuai emosi. Bubble panjang bisa digulir dan tidak keluar jendela
- **Pikiran batin**: kadang Iris menampilkan satu baris bisikan hati berukuran kecil dan miring di atas bubble (tidak disuarakan dan tidak masuk riwayat). Saklar di Pengaturan
- Klip gerak VRMA buatan sendiri (14 klip, hanya punggung, dada, leher, dan kepala) yang diputar lewat gerbang emosi
- Kualitas gambar adaptif: `auto`, `tinggi`, `normal`, `hemat`. Mode auto turun sendiri kalau frame lambat (`/kualitas`)
- Seluruh UI (menu, bubble, bar input, panel) dijaga tetap di dalam layar; jendela yang dilepas jauh dari tepi meluncur balik ke area kerja

### Interaksi dengan karakter

- **Seret karakter** langsung, atau lewat tombol grip di bar. Keduanya punya saklar sendiri, dan satu selalu tersisa supaya Iris tidak terkunci (`/angkat`)
- Pose **diangkat**: badan berayun seperti bandul dengan titik gantung di kepala, lengan terkulai, reaksi bersuara saat diangkat dan dilepas
- Reaksi sakit dan suara saat menabrak sisi atau pojok layar
- **Sembunyi di tepi layar** dan **mengintip**: dilepas dekat tepi layar, Iris langsung bersembunyi, lalu muncul lagi saat kursor menempel atau diklik (`/sembunyi`)
- **Duduk di tepi atas jendela lain** (`/duduk`). Bawaan mati karena menyentuh privasi; yang dibaca hanya posisi dan ukuran jendela, bukan judul, nama proses, atau isinya
- **Colek dan elus**: colek berkali-kali dibalas "geli", gumaman, lalu ngambek 10 detik. Tahan klik kiri di kepala untuk mengelus
- Klik bagian tubuh (kepala, badan, lengan, tangan) dibalas suara dengan variasi kalimat
- **Menu aksi cepat** lewat klik kanan karakter, dan ikon tray untuk pengaturan
- Bar input auto-sembunyi dengan garis petunjuk hijau yang "bernapas" (merah saat server mati, cyan saat agen bekerja)
- **Mode fokus**: karakter dan bubble hilang, hanya garis petunjuk tipis yang tersisa, dan klik tembus
- **Tidur otomatis** saat tidak ada aktivitas (bawaan 5 menit), bangun saat kursor bergerak atau diklik

### Obrolan dan suara

- Obrolan dengan persona Iris (gaya santai, campuran Indonesia dan Jepang)
- Suara per emosi lewat VOICEVOX: kecepatan, nada, dan intonasi menyesuaikan emosi kalimat, lip-sync berbasis mora, dan cache suara lokal
- Reaksi lokal (colek, sapaan, timer, dan sebagainya) bersuara tanpa memanggil model
- Pesan galat ikut dibacakan (timeout, tidak tersambung, galat lain)
- Sapaan menurut waktu (pagi, siang, sore, malam)
- **Fun fact** acak bersuara di selang waktu yang bisa diatur. Diambil dari 30 fakta bawaan atau dibuat model sesuai topik (`/funfact`)
- Alarm, jam (ucapan tiap jam), timer, Pomodoro, dan pengingat istirahat
- Panel chat dengan riwayat, tombol Hapus, "Mode jelaskan", tombol memanjangkan kotak chat, dan popup **Salin link**
- **Ekspor percakapan** ke satu berkas HTML mandiri (gelap di layar, terang saat dicetak) di folder Downloads (`/ekspor`)
- **Pilihan bernomor**: perintah seperti `/baju`, `/tema`, `/alarm`, dan `/lokal daftar` menampilkan daftar, lalu cukup ketik angkanya
- Pil status koneksi `V 9 H` (VOICEVOX, 9Router, Hermes) dan titik bar hijau, kuning, atau merah (`/status`)

### Penglihatan, input, dan belajar

- Lampirkan gambar lewat tempel (`Ctrl+V`), tombol klip, atau seret berkas; thumbnail bisa diklik, ada penampil besar dengan zoom, Salin gambar, dan Simpan
- **Screenshot layar** langsung jadi lampiran (tombol kamera, pintasan, atau tray)
- **Terjemah layar**: teks Jepang di layar diucapkan dan diterjemahkan
- **Tanya clipboard**: teks atau gambar di clipboard dikirim sebagai pertanyaan
- **Komentar layar otomatis** (`/pantau`, ditandai 👁)
- **Bicara lewat mikrofon** (STT, opsional) dengan faster-whisper
- **Mode belajar bahasa Jepang** (`/belajar`): Iris memberi kalimat Jepang, kamu menebak arti atau mengulang ucapannya, lalu dikoreksi. Ada opsi menyerah untuk melihat jawaban
- **Perintah aplikasi lokal** (`/lokal`): membuka aplikasi dari daftar putih yang ditetapkan di `main.js`

### Agen dan memori

- **Jembatan Hermes Agent** (`/agen`, `/agent`, `/h`): memberi tugas ke agen di WSL, lengkap dengan indikator "sedang memproses" berhitung detik, heartbeat, tombol Stop, dan batas waktu
- **Konfirmasi tugas berbahaya**: tugas `/agen` yang berbau hapus, pindah, timpa, atau format file ditahan dulu dan muncul kartu "Iris mau menjalankan ini. Lanjut?" dengan tombol Jalankan dan Batal
- Kartu **Hasil tugas** dengan tombol Salin. Path WSL di laporan otomatis diubah menjadi path Windows (`C:\Users\<user>\...`)
- Hermes menerima konteks 10 pesan terakhir hanya bila tugas merujuk ke percakapan, dan tahu folder Windows lewat `HERMES_WIN_HOME`
- Iris dilarang mengaku bisa membuat, mengubah, atau menghapus file di obrolan biasa; ia menyuruh memakai `/agen`. Laporan agen disampaikan netral dan bersumber
- **Memori ringan**: `/ingat`, `/memori`, `/lupa` (maksimal 40 hal, 200 karakter per hal). Isi yang mirip rahasia ditolak
- **Riwayat obrolan persisten**: 20 pesan terakhir, kedaluwarsa 3 hari, gambar tidak pernah disimpan, pasangan pesan berisi kata rahasia tidak ditulis
- **Mini-browser** multi-akun (`/chrome`), lihat [bagiannya](#mini-browser-chrome)

### Infrastruktur

- `IrisLauncher.exe`: peluncur satu klik dengan indikator hijau per layanan
- `iris-doctor.ps1`: cek kesehatan seluruh sistem
- `iris-start.ps1` dan `iris-stop.ps1`: start dan stop berurutan, aman dijalankan berulang
- `9router.service`: 9Router berjalan sebagai layanan systemd di WSL
- `.wslconfig` dengan batas memori WSL 4 GB

---

## Arsitektur

```
┌──────────────────────┐      WebSocket       ┌──────────────────────┐
│  Overlay Electron    │ ───────────────────► │  server.py (FastAPI) │
│  avatar VRM, bubble, │ ◄─────────────────── │  otak + penghubung   │
│  input, pintasan     │     /ws + token      └──────────┬───────────┘
└──────────────────────┘                                 │
                                     ┌───────────────────┼───────────────────┐
                                     │ OpenAI-compat     │ HTTP (TTS)        │ HTTP API
                                     ▼                   ▼                   ▼
                             ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                             │ 9Router      │    │ VOICEVOX     │    │ Hermes Agent │
                             │ (LLM)        │    │ (suara)      │    │ (WSL2)       │
                             └──────────────┘    └──────────────┘    └──────────────┘
```

| Komponen | Peran |
|---|---|
| Electron (`main.js`, `index.html`, `preload.js`) | Wajah dan suara (overlay) |
| `server.py` (FastAPI + WebSocket) | Otak dan penghubung antar layanan |
| 9Router | Gerbang LLM dengan endpoint kompatibel OpenAI |
| VOICEVOX | Sintesis suara (TTS) |
| Hermes Agent (WSL2) | Tangan dan memori: menjalankan tugas di komputer |
| `iris_web.py` | CLI untuk membaca panel mini-browser (dipakai agen) |

---

## Teknologi

- **Frontend:** Electron, three.js, `@pixiv/three-vrm`
- **Backend:** Python, FastAPI, WebSocket
- **Suara:** VOICEVOX (TTS), faster-whisper (STT, opsional)
- **LLM:** 9Router (endpoint OpenAI-compatible)
- **Agen:** Hermes Agent di WSL2
- **Peluncur:** `IrisLauncher` (C# dan PowerShell, kode di [`IrisLauncher-src/`](IrisLauncher-src/))

---

## Prasyarat

| Kebutuhan | Keterangan |
|---|---|
| Windows 10/11 | Overlay berjalan di Windows |
| Node.js 18+ | Untuk Electron |
| Python 3.11+ | Untuk `server.py` |
| VOICEVOX | Berjalan di port `50021` (opsional, tanpa ini Iris menjawab lewat teks saja) |
| 9Router atau endpoint LLM kompatibel OpenAI | Berjalan di `localhost:20128` secara bawaan |
| WSL2 + Hermes Agent | Opsional, hanya untuk fitur `/agen` |
| faster-whisper | Opsional, hanya untuk bicara lewat mikrofon |

Disarankan RAM 16 GB jika Hermes dan model lokal dijalankan bersamaan. Batas memori WSL di proyek ini diset 4 GB lewat `.wslconfig`.

---

## Instalasi

```powershell
git clone https://github.com/JihoStarting/iris-desktop-companion.git
cd iris-desktop-companion

# Dependency Node
npm install

# Virtual environment Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Konfigurasi
copy .env.example .env
```

Kalau PowerShell menolak menjalankan `Activate.ps1` karena kebijakan eksekusi, jalankan dulu `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` di jendela yang sama. Alternatifnya, pakai `.\.venv\Scripts\python.exe` langsung tanpa aktivasi.

Lalu buka `.env` dan isi dengan nilai milikmu sendiri. **Jangan pernah meng-commit file `.env`.**

Panduan langkah demi langkah: [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## Konfigurasi

Semua pengaturan dibaca dari file `.env` (di folder proyek atau di folder user Windows; `~/.env` dibaca lebih dulu). Contoh lengkap ada di [`.env.example`](.env.example). Server dan overlay hanya membaca `.env` saat start, jadi restart keduanya setelah mengubahnya.

### Inti

| Variabel | Fungsi | Bawaan |
|---|---|---|
| `NINEROUTER_URL` | Alamat endpoint LLM | `http://localhost:20128/v1` |
| `NINEROUTER_API_KEY` | Kunci API 9Router (wajib bila "Require API key" aktif) | kosong |
| `NINEROUTER_MODEL` | Nama model atau combo | `Iris` |
| `NINEROUTER_VISION_MODEL` | Model untuk analisis gambar (kosong = model biasa) | kosong |
| `NINEROUTER_VISION_READ_TIMEOUT` | Batas waktu model gambar (detik) | bawaan server |
| `VOICEVOX_URL` | Alamat VOICEVOX | `http://127.0.0.1:50021` |
| `VOICEVOX_SPEAKER` | ID suara VOICEVOX | `2` |
| `VOICEVOX_SPEAKER_<EMOSI>` | ID suara khusus untuk satu emosi (opsional) | kosong |
| `COMPANION_HOST` | Alamat server overlay | `127.0.0.1` |
| `COMPANION_PORT` | Port server overlay | `8765` |
| `COMPANION_USER_NAME` | Nama panggilan pengguna | `Rover` |
| `COMPANION_TOKEN` | Token autentikasi `/ws`. **Isi ini** (lihat [Keamanan](#keamanan)) | kosong |

### Hermes

| Variabel | Fungsi | Bawaan |
|---|---|---|
| `HERMES_URL` | Alamat API server Hermes | `http://127.0.0.1:8642/v1` |
| `HERMES_API_KEY` | Kunci API Hermes (harus sama dengan `API_SERVER_KEY` di Hermes) | kosong |
| `HERMES_TIMEOUT` | Batas waktu tugas agen (detik) | `900` |
| `HERMES_STREAM` | `1` memakai respons stream supaya Stop memutus koneksi eksplisit | `0` |
| `HERMES_WIN_HOME` | Folder user Windows dilihat dari WSL | `/mnt/c/Users/<user>` |

### Opsional (`IRIS_*`)

| Variabel | Fungsi |
|---|---|
| `IRIS_VOICE_STYLE=0` | Matikan gaya suara per emosi |
| `IRIS_THOUGHTS=0` | Matikan pikiran batin dari sisi server |
| `IRIS_HISTORY=0` | Matikan riwayat obrolan persisten |
| `IRIS_HISTORY_DAYS` | Lama riwayat disimpan (bawaan 3 hari) |
| `IRIS_HISTORY_FILE`, `IRIS_MEMORY_FILE` | Ganti lokasi berkas riwayat dan memori |
| `IRIS_SAVE_SCREEN=0` | Jangan sertakan screenshot terakhir ke Hermes |
| `IRIS_MUTE_KEY` | Paksa kombinasi pintasan bisu sendiri |
| `IRIS_STT_MODEL`, `IRIS_STT_LANG`, `IRIS_STT_DEVICE`, `IRIS_STT_COMPUTE` | Pengaturan faster-whisper |
| `IRIS_NEWTAB_URL` | Halaman awal mini-browser untuk akun tanpa link |
| `IRIS_WEB_BRIDGE=1` | Nyalakan jembatan baca-saja (butuh `COMPANION_TOKEN`) |
| `IRIS_BRIDGE_HOST`, `IRIS_BRIDGE_PORT` | Alamat jembatan baca-saja (port bawaan 8767) |
| `IRIS_PEEK_CUT` | Seberapa banyak karakter terlihat saat mengintip |

Membuat token untuk `COMPANION_TOKEN`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Menjalankan

### Cara manual

Buka dua terminal di folder proyek.

**Terminal 1: server**

```powershell
.\.venv\Scripts\python.exe server.py
```

**Terminal 2: overlay**

```powershell
npm start
```

Cek kesehatan layanan di `http://127.0.0.1:8765/health`.

> Jika `COMPANION_TOKEN` aktif, halaman `http://127.0.0.1:8765` di browser tidak bisa dipakai untuk chat karena browser tidak dapat mengirim header token. Gunakan overlay Electron.

### Lewat peluncur

`IrisLauncher.exe` (lihat tab Releases) menjalankan WSL, layanan pendukung, server, dan overlay sekaligus.

---

## Peluncur, cek kesehatan, dan layanan

| Berkas | Fungsi |
|---|---|
| `IrisLauncher.exe` | Antarmuka Start, Stop, dan Doctor dengan indikator hijau per layanan (WSL, VOICEVOX, 9Router, Hermes, server, overlay) |
| `iris-start.ps1` | Menyalakan WSL, lalu hanya layanan yang belum menjawab (VOICEVOX, 9Router, Hermes) secara paralel, lalu `server.py` dan overlay. Idempoten dan tidak membuat server atau overlay kedua |
| `iris-stop.ps1` | Menghentikan overlay dan server (opsi untuk menghentikan layanan lain dan sesi penjaga WSL) |
| `iris-doctor.ps1` | Memeriksa folder proyek, `.venv`, Electron, `.env`, port, status WSL dan Hermes, `.wslconfig`, ruang disk, dan RAM. Tiap baris `OK`, `WARN`, atau `GAGAL` disertai cara memperbaiki. Nilai token tidak pernah dicetak |
| `iris-hermes.ps1`, `iris-service.ps1` | Pembungkus untuk Hermes dan layanan WSL |
| `9router.service` | Layanan systemd pengguna di WSL untuk 9Router |

Contoh menjalankan tanpa peluncur:

```powershell
powershell -ExecutionPolicy Bypass -File .\iris-start.ps1
powershell -ExecutionPolicy Bypass -File .\iris-stop.ps1
```

Skrip peluncur menulis log ke `iris-start.log` dan `iris-*.out/err.log`. Log tidak memuat token, tetapi **log server memuat teks chat**, jadi jangan dibagikan sembarangan.

Kode sumber peluncur ada di [`IrisLauncher-src/`](IrisLauncher-src/). Skrip `.ps1` tertanam di dalam exe, jadi mengubah berkas di folder proyek tidak mengubah perilaku tombol di peluncur sampai exe dibangun ulang.

---

## Perintah chat

Ketik di kotak input overlay. Ketik `/help` untuk daftar lengkap di aplikasi. Perintah yang tidak dikenal diteruskan ke server.

### Agen dan sistem

| Perintah | Fungsi |
|---|---|
| `/agen <tugas>` (alias `/agent`, `/h`) | Beri tugas ke Hermes Agent, misalnya `/agen sebutkan isi folder Download` |
| `/chrome`, `/akun` | Mini-browser multi-akun, lihat [bagiannya](#mini-browser-chrome) |
| `/lokal daftar` | Daftar aplikasi yang boleh dibuka; ketik nomor atau nama untuk membukanya |
| `/status` | Tampilkan hasil `/health` (VOICEVOX, 9Router, Hermes, token) |
| `/kualitas [auto\|tinggi\|normal\|hemat]` | Atur kualitas gambar; tanpa argumen melaporkan tingkat sekarang |

### Waktu dan fokus

| Perintah | Fungsi |
|---|---|
| `/timer N [nama]` | Timer N menit |
| `/pomodoro` | Sesi pomodoro 25/5 |
| `/batal` | Batalkan timer |
| `/alarm HH:MM [nama]` | Pasang alarm (`/alarm` untuk daftar, `/alarm batal <no\|semua>` untuk menghapus) |
| `/jam` | Iris mengucapkan jam (`/jam nyala` untuk tiap jam) |
| `/istirahat N` | Pengingat istirahat tiap N menit aktif (15 sampai 240; `/istirahat mati` untuk mematikan) |
| `/funfact [sekarang\|10-30\|20\|mati\|nyala]` (alias `/ff`, `/tahukah`) | Atur fun fact acak; `/funfact topik <topik>`, `/funfact bawaan`, `/funfact model` |
| `/fokus` | Mode fokus (karakter dan bubble hilang) |
| `/bisu` | Matikan suara |
| `/tidur` | Iris tidur |

### Layar dan belajar

| Perintah | Fungsi |
|---|---|
| `/layar [tanya]` | Ambil screenshot lalu bertanya |
| `/terjemah [catatan]` (alias `/tl`, `/translate`) | Terjemahkan teks di layar |
| `/clip` | Tanya isi clipboard |
| `/pantau` | Komentar layar otomatis (ditandai 👁) |
| `/belajar [topik]` | Mode belajar bahasa Jepang, mis. `/belajar makanan` |

### Memori dan penampilan

| Perintah | Fungsi |
|---|---|
| `/ingat <hal>` | Simpan sesuatu ke memori |
| `/memori` | Lihat isi memori |
| `/lupa <no>` | Hapus satu memori |
| `/mood` | Lihat suasana hati Iris |
| `/baju [nomor\|nama]` | Ganti baju |
| `/tema` | Ganti tema warna (Iris, empat musim, Otomatis) |
| `/badan [penuh\|setengah]` | Tampilan tubuh penuh atau setengah badan |
| `/bayangan [nyala\|mati]` | Bayangan karakter |
| `/angkat [nyala\|mati]` | Izinkan atau cegah mengangkat Iris dari badan |
| `/duduk [nyala\|mati\|sini]` | Iris duduk di tepi atas jendela terdekat (bawaan mati) |
| `/sembunyi` | Iris bersembunyi di tepi layar |
| `/atas [nyala\|mati]` | Selalu di atas jendela lain |
| `/ekspor` | Ekspor percakapan ke HTML |
| `/help` | Daftar perintah di aplikasi |

---

## Pintasan keyboard

| Pintasan | Fungsi |
|---|---|
| `Ctrl+Alt+C` | Buka chat |
| `Ctrl+Alt+S` | Screenshot layar |
| `Ctrl+Alt+T` | Terjemahkan layar |
| `Ctrl+Alt+V` | Tanya isi clipboard |
| `Ctrl+Alt+G` | Bicara lewat mikrofon (tekan lagi untuk berhenti, otomatis berhenti setelah 30 detik) |
| `Ctrl+Alt+H` | Tampilkan atau sembunyikan Iris |
| `Ctrl+Alt+B` | Bisukan suara dari sisi overlay (cadangan: `Ctrl+Alt+M`, `Ctrl+Shift+Alt+M`, atau `IRIS_MUTE_KEY`) |
| `Ctrl+Alt+W` | Buka atau tutup mini-browser |
| `Ctrl+Alt+Q` | Keluar |
| `Ctrl+Alt+D` | Buka DevTools overlay |
| `Ctrl+V` | Tempel gambar dari clipboard sebagai lampiran |

Klik kanan pada karakter untuk menu aksi cepat, dan gunakan ikon tray untuk pengaturan.

---

## Mini-browser `/chrome`

Panel browser kecil di samping karakter dengan **lima slot akun** yang masing-masing punya sesi login terpisah. Panel berjalan di proses terpisah dan tanpa akses ke fungsi Electron.

| Perintah | Fungsi |
|---|---|
| `/chrome 1` sampai `/chrome 5` | Ganti ke akun nomor itu dan buka link awalnya |
| `/chrome` | Buka akun terakhir |
| `/chrome <nama>` | Sama, memakai nama akun |
| `/chrome 3 https://situs.com` | Akun 3 dengan alamat lain |
| `/chrome tutup` | Tutup panel dan buang prosesnya |
| `/chrome daftar` atau `/akun` | Tampilkan lima slot |
| `/chrome mundur`, `maju`, `muat`, `beranda` | Navigasi (juga `Alt+←`, `Alt+→`, `F5`) |
| `/chrome ram` | RAM dan CPU renderer panel, GPU, dan total proses |
| `/chrome elemen` | Daftar elemen yang terlihat (uji jembatan baca-saja) |
| `/chrome jembatan` | Status jembatan baca-saja |
| `/akun tambah <nama> [link]` | Buat akun di slot kosong pertama |
| `/akun link <nomor\|semua> <url\|baru>` | Ganti link awal |
| `/akun hapus <nama>` | Hapus akun beserta sesi loginnya |

Fitur panel:

- Tab diparkir untuk hemat RAM (maksimal 3 hidup), dan panel otomatis ditutup bila kualitas gambar turun ke `hemat`
- Pil akun di dock untuk berganti akun dengan satu klik
- Bilah alat melayang (mundur, maju, muat ulang, beranda, host, tutup), sudut membulat, dan animasi meluncur masuk dan keluar
- Panel pindah ke sisi seberang otomatis bila ruang di satu sisi tidak cukup
- Menu dan popover bergeser supaya tidak tertutup panel

Nama akun: huruf kecil, angka, `-` atau `_`, maksimal 20 karakter, dan tidak boleh sama dengan kata perintah.

---

## Jembatan baca-saja untuk Hermes

Memungkinkan Hermes membaca isi panel mini-browser (tanpa mengklik atau mengisi apa pun). **Mati secara bawaan.**

- Nyala hanya kalau `IRIS_WEB_BRIDGE=1` **dan** `COMPANION_TOKEN` terisi
- Mendengar hanya di `127.0.0.1` (port bawaan 8767), hanya metode `GET`, permintaan berheader `Origin` ditolak, token dibandingkan timing-safe, batas laju 30 permintaan per 10 detik
- Isian formulir tidak pernah dikirim (hanya nama isian dan penanda apakah itu password), URL dikirim tanpa query dan hash
- Semua hasil bertanda `untrusted: true`: isi halaman adalah data, bukan perintah

| Rute | Isi |
|---|---|
| `/web/state` | Akun aktif, URL tanpa query, judul, status memuat |
| `/web/text?max=N` | Teks halaman (bawaan 8000, maksimal 20000 karakter) |
| `/web/elements` | Sampai 120 elemen terlihat (tag, teks, `href`, posisi) |
| `/web/shot` | Screenshot panel (JPEG, lebar maksimal 1000 px) |

Klien: `python3 iris_web.py state | text [maks] | elements | shot [berkas.jpg]`.

> Risiko injeksi prompt tetap ada begitu Hermes membaca halaman akun yang sudah login. Pakai akun uji dulu dan jangan nyalakan jembatan ini permanen sebelum kamu mengujinya.

---

## Kemampuan Hermes Agent

Hermes Agent berjalan di WSL2 dan menjadi "tangan" Iris lewat `/agen`. Kemampuan utamanya:

- **Terminal dan sistem:** perintah bash di WSL dan PowerShell di Windows, proses latar, cron
- **File dan disk:** baca, tulis, cari isi file, analisis penggunaan disk
- **Kode:** menulis dan menyunting kode, menjalankan build dan tes, operasi git
- **Browser:** mengendalikan Chrome lewat Chrome DevTools Protocol
- **Web dan riset:** pencarian web (backend Exa), ekstraksi halaman, pencarian paper di ArXiv, riset multi-sudut
- **Dokumen dan media:** PDF, Word, Excel, PowerPoint, transkrip YouTube, analisis gambar
- **Data:** SQLite, JSON, CSV, Airtable
- **Integrasi:** Telegram, Notion, Google Workspace
- **Skill kustom** (40+): mis. `deep-research`, `academic-writer`, `excalidraw`, `oss-forensics`, `laptop-storage-analyzer`, `cek-elearning`, dan `isi-form-otomatis`. Skill dimuat per tugas

Laporan Hermes ditampilkan apa adanya di kartu "Hasil tugas". Iris menyampaikannya secara netral dan bersumber, dan hanya menyatakan berhasil bila laporan Hermes jelas menyatakannya.

> Tombol Stop memutus koneksi dari sisi Iris, tetapi belum terbukti menghentikan agen di sisi Hermes. Pesan pembatalan tetap menyebut "tugas mungkin masih berjalan". Skrip [`scripts/cek-cancel-hermes.py`](scripts/cek-cancel-hermes.py) mengukur mode mana yang benar-benar berhenti.

---

## Keamanan

IRIS dirancang untuk berjalan lokal dan memberi agen akses ke komputermu, jadi beberapa pengaman dipasang:

- Server hanya mendengar di `127.0.0.1`.
- **Isi `COMPANION_TOKEN`.** Koneksi `/ws` dilindungi token lewat header `X-Iris-Token` (kode penolakan 1008), plus pengecekan `Origin`. Kalau token **kosong**, server tetap jalan dengan perilaku lama dan hanya mencetak peringatan di terminal. Karena agen bisa menjalankan perintah di komputermu, anggap token wajib
- Perintah `/agen` yang berpotensi berbahaya (hapus, pindah, timpa, format file) meminta konfirmasi dulu. Daftar kata pemicu bisa disetel, `/health` menampilkan `agent_confirm`, dan konfirmasi sekali pakai kedaluwarsa dalam 120 detik
- Semua jendela menolak navigasi, jendela baru, dan `<webview>`
- Memori dan riwayat menolak menyimpan isi yang mirip rahasia (kata sandi dan sejenisnya)
- Panel mini-browser berjalan terisolasi (sandbox, tanpa preload, tanpa akses kamera, mikrofon, atau notifikasi, navigasi hanya ke `https://`)
- Jembatan baca-saja mati secara bawaan dan berlapis (lihat [bagiannya](#jembatan-baca-saja-untuk-hermes))
- Fitur yang menyentuh privasi (duduk di jendela lain) **mati secara bawaan**
- Log hanya mencatat sidik token, bukan isinya, dan URL dipotong sampai path

Hal yang perlu kamu jaga sendiri:

- Riwayat obrolan dan memori tersimpan polos di disk. Jangan taruh folder proyek di drive yang tersinkron ke cloud
- Log server memuat teks chat

Berkas sensitif tidak pernah masuk repositori: `.env`, riwayat percakapan, memori, log, dan arsip dikecualikan lewat `.gitignore`.

Menemukan celah keamanan? Mohon jangan buka issue publik; hubungi pemilik repositori secara langsung.

---

## Status pengujian

Fitur di bawah sudah ditulis tetapi **belum lulus uji penuh di PC**. Anggap eksperimental sampai ada konfirmasi.

| Area | Catatan |
|---|---|
| Gerak halus (pegas, crossfade) dan gerbang emosi ke klip | Belum dites visual |
| Pikiran batin | Kode ditulis, belum dites dengan model dan suara asli |
| Terjemah layar dan bicara lewat mikrofon (STT) | Belum diuji end-to-end |
| Mini-browser, fase 4 (pil akun, hemat RAM, tab diparkir) | Belum dites di Electron asli |
| Jembatan baca-saja | Hanya diuji dengan klien tiruan |
| Perbaikan v46 sampai v50 (jaga UI tetap di layar, panel pindah sisi, rambut dan bayangan setengah badan) | Belum dites |
| Tugas `/agen` ringan terasa lambat | Penyebab belum dipastikan |
| Cancel yang benar-benar menghentikan agen | Belum terbukti |
| Bubble dengan lampiran dekat tepi atas layar | Belum dites |

Yang sudah lulus uji antara lain: jembatan Hermes (termasuk path Windows di kartu hasil), konfirmasi `/agen` berbahaya, token `/ws`, ganti baju, tema, fun fact, alarm dan jam, mood, seret file dan lampiran gambar, ekspor, pilihan bernomor, pil status koneksi, dan peluncur.

---

## Rencana

Ide yang sudah disetujui atau dicatat, **belum ada kodenya**:

- Memori otomatis ringan (ringkasan fakta baru yang kamu setujui dulu sebelum disimpan)
- Menari mengikuti musik dan perintah `/nari` (butuh klip `.vrma` lengan)
- Angin dari kecepatan kursor (`/angin`)
- Pemeriksa tugas e-learning otomatis lewat skill `cek-elearning`
- `/catat` dan `/todo`, statistik Pomodoro, jurnal mood harian
- Mode jangan ganggu otomatis saat game atau aplikasi layar penuh
- Pencarian catatan (`/cari`, `/indeks`): ditunda
- Alternatif TTS dan LLM selain VOICEVOX dan 9Router
- Wake word dan mode hands-free
- Dukungan Live2D, macOS, dan Linux

---

## Struktur proyek

```
.
├── main.js                  # proses utama Electron (jendela, tray, IPC)
├── preload.js               # jembatan aman antara renderer dan main
├── index.html               # tampilan overlay: avatar, bubble, input
├── server.py                # backend FastAPI + WebSocket
├── iris_web.py              # CLI untuk membaca panel mini-browser (dipakai agen)
├── clips.json               # daftar klip (salinan; aplikasi membaca assets/animations/clips.json)
├── requirements.txt         # dependency Python
├── package.json             # dependency Node
├── package-lock.json        # versi dependency Node yang terkunci
├── .env.example             # contoh konfigurasi
├── .gitignore               # berkas yang tidak masuk repositori
├── LICENSE                  # lisensi
├── README.md                # dokumen ini
├── .github/workflows/       # CI (cek sintaks Python)
├── IrisLauncher-src/        # kode sumber peluncur (C# dan PowerShell)
├── scripts/
│   ├── buat_klip_vrma.py    # skrip pembuat klip animasi VRMA
│   └── cek-cancel-hermes.py # skrip uji pembatalan tugas Hermes
├── dev/
│   └── test_client.html     # halaman tes koneksi (hanya untuk pengembangan, tanpa token)
├── tests/                   # tes otomatis
└── docs/
    ├── QUICKSTART.md                 # panduan mulai cepat
    ├── iris-companion-gabungan.md    # dokumen gabungan: roadmap, referensi sistem, riwayat versi, hasil uji
    └── img/                          # logo
```

---

## Aset

Aset (model VRM, animasi VRMA, suara) **tidak disertakan** dalam repositori karena ukuran dan lisensi. Letakkan sendiri di folder `assets/`:

```
assets/
├── iris.vrm                 # model utama
├── Iris_winter.vrm          # model baju (opsional)
└── animations/
    ├── idle_loop.vrma       # animasi idle
    └── clips.json           # daftar klip gerak (opsional)
```

Pastikan kamu memiliki hak pakai atas model dan aset yang kamu gunakan.

---

## Pemecahan masalah

| Gejala | Kemungkinan penyebab dan solusi |
|---|---|
| Iris tidak bersuara, terminal penuh `VOICEVOX gagal` | VOICEVOX belum berjalan. Jalankan VOICEVOX dulu (port 50021) |
| Balasan `401 Missing API key` | `NINEROUTER_API_KEY` kosong. Isi di `.env` lalu restart server |
| Overlay tidak tersambung, log `/ws ditolak` | Token server dan overlay berbeda (mis. ada dua `.env` dengan token berbeda). Cek sidik token di terminal server dan terminal Electron, lalu restart keduanya |
| Halaman `127.0.0.1:8765` menampilkan "Server Iris aktif" saja | Normal bila `COMPANION_TOKEN` aktif. Gunakan overlay Electron |
| `/agen` membalas HTTP 503 atau tidak merespons | Pastikan API server Hermes aktif di `127.0.0.1:8642` dan `HERMES_API_KEY` sama dengan `API_SERVER_KEY` |
| File hasil agen "tidak ada" di Download | Hermes berjalan di WSL, jadi `~/Downloads` miliknya adalah folder Linux. Atur `HERMES_WIN_HOME` agar menunjuk ke folder Windows |
| Perubahan `.env` tidak terbaca | Server hanya membaca `.env` saat start. Restart server dan overlay |
| Karakter menghilang sesekali | Pemulihan WebGL otomatis dan watchdog sudah dipasang. Coba `/kualitas hemat`, lalu lihat terminal Electron (`Renderer mati`, `WebGL context hilang`) |
| Iris lag atau RAM penuh | `/kualitas hemat`, tutup tab browser yang tidak dipakai, dan cek batas memori WSL di `.wslconfig`. `/chrome ram` menampilkan pemakaian panel |
| Model gambar timeout | Kurangi jumlah gambar yang dikirim atau naikkan `NINEROUTER_VISION_READ_TIMEOUT` |
| Tombol Salin gambar gagal | Restart Iris. Handler mencoba tiga cara berurutan, termasuk lewat PowerShell |
| Pintasan bisu tidak bekerja | Kombinasinya mungkin dipakai aplikasi lain. Terminal mencetak pintasan yang terdaftar; paksa sendiri lewat `IRIS_MUTE_KEY` |
| Peluncur gagal di langkah WSL | Jalankan `iris-doctor.ps1` dan lihat log di `iris-start.log` |

Untuk diagnosis lebih lanjut, buka DevTools dengan `Ctrl+Alt+D` dan cek tab Console.

---

## Dokumentasi

- [`docs/QUICKSTART.md`](docs/QUICKSTART.md): panduan mulai cepat dari nol sampai Iris menjawab
- [`docs/iris-companion-gabungan.md`](docs/iris-companion-gabungan.md): dokumen gabungan overlay dan Hermes, berisi roadmap, referensi sistem, riwayat versi, dan hasil uji

---

## Lisensi

Repositori ini dapat dilihat publik, tetapi **hak cipta dilindungi (All rights reserved)**: kode tidak boleh disalin, dimodifikasi, disebarkan, atau dipakai ulang tanpa izin tertulis, lihat [LICENSE](LICENSE). Aset pihak ketiga (model, suara, gambar karakter) mengikuti lisensi masing-masing pembuatnya.

Dibuat oleh KangJiho.
