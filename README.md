<p align="center">
  <img src="docs/img/iris-launcher-logo.png" alt="Logo IRIS" width="260">
</p>

<h1 align="center">IRIS</h1>

<p align="center">
  <strong>Teman AI di desktop: avatar 3D, suara Jepang, dan agen yang benar-benar bisa bekerja di komputermu.</strong><br>
  <em>A desktop AI companion overlay for Windows + WSL2: VRM avatar, VOICEVOX voice, and a Hermes Agent bridge that can do real tasks on your computer. Documentation is in Indonesian.</em>
</p>

<p align="center">
  <img alt="Versi" src="https://img.shields.io/badge/versi-v1.3.1-blue">
  <img alt="Status" src="https://img.shields.io/badge/status-aktif%20dikembangkan-brightgreen">
  <img alt="Electron" src="https://img.shields.io/badge/Electron-overlay-47848F">
  <img alt="Python" src="https://img.shields.io/badge/Python-FastAPI-3776AB">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%2B%20WSL2-0078D6">
  <img alt="Lisensi" src="https://img.shields.io/badge/lisensi-All%20rights%20reserved-red">
</p>

<p align="center">
  <a href="#mulai-cepat">Mulai cepat</a> ·
  <a href="#fitur">Fitur</a> ·
  <a href="#arsitektur">Arsitektur</a> ·
  <a href="#perintah-chat">Perintah</a> ·
  <a href="#keamanan">Keamanan</a> ·
  <a href="#pemecahan-masalah">Pemecahan masalah</a>
</p>

---

IRIS adalah teman AI yang tinggal di desktop. Wajahnya avatar 3D (VRM) yang melayang di atas aplikasi lain, suaranya dari VOICEVOX, dan tangannya adalah **Hermes Agent** yang mengerjakan tugas nyata di komputer: membuka folder, mencari file, menjalankan perintah, dan mencari di web.

Proyek ini dibuat sebagai proyek pribadi dan masih terus dikembangkan.

## Sorotan

| Keunggulan | Keterangan |
|---|---|
| **Avatar hidup** | Model VRM dalam jendela transparan: ekspresi, mood, ganti baju, tema musiman, dan 9 klip gerak |
| **Suara per emosi** | VOICEVOX dengan nada dan kecepatan yang mengikuti emosi, lip-sync, dan mesin GPU (DirectML) |
| **Agen yang aman** | Tugas `/agen` berjalan di sandbox Docker tanpa jaringan, dengan kartu izin **Izinkan sekali / Tolak** di overlay |
| **Terjemah layar** | OCR Jepang atau Inggris, diterjemahkan ke Indonesia dan digambar di atas teks asli |
| **Bedah file statis** | `/rea` membedah exe, dll, apk, jar, dan firmware tanpa menjalankannya |
| **Mini-browser** | Panel browser dengan sepuluh akun terpisah, dan jembatan baca-saja untuk Hermes |
| **Belajar** | Mode belajar Jepang, kuis kana, dan game teka-teki |
| **Satu klik** | `IrisLauncher.exe` menyalakan semua layanan berurutan dan aman dijalankan berulang |

## Status

| Item | Keterangan |
|---|---|
| Hermes Agent dipasang | 28 September 2026 |
| Overlay mulai dikembangkan | 28 Oktober 2026 |
| Dipublikasikan di GitHub | 5 November 2026 |
| Versi terbaru | v1.3.1 (peluncur `IrisLauncher.exe`) |
| Terakhir diperbarui | 22 November 2026 (v102.1: perbaikan isi ulang `/tekateki` di `iris_games.py` dan penutupan celah dunder-lewat-string di `approval_policy.py`; lulus uji di sandbox, belum dites di PC); sebelumnya 20 November 2026 (v99.1 sampai v102: Asset Explorer `rea_assets.py`, izin otomatis baca-saja `approval_policy.py`, audit keamanan server v102; sinkron dengan kode yang diunggah 20 November, belum dites di PC); sebelumnya 19 November 2026 (peluncur v1.3.1: perbaikan biner Electron dan Doctor; v101: perbaikan keamanan dan kerapian dari tinjauan kode 19 November; sinkron dengan catatan kerja sampai 19 November), lihat [Riwayat pembaruan](#riwayat-pembaruan) |

> **Tentang status uji.** Sebagian fitur sudah lulus uji di PC pengembang, sebagian lain baru ditulis dan belum diuji penuh. Fitur yang belum terbukti ditandai *(eksperimental)* di bawah, dan daftar lengkapnya ada di [Status pengujian](#status-pengujian).

## Daftar isi

- [Mulai cepat](#mulai-cepat): [Prasyarat](#prasyarat), [Instalasi](#instalasi), [Menjalankan](#menjalankan)
- [Fitur](#fitur)
- [Arsitektur](#arsitektur) dan [Teknologi](#teknologi)
- [Konfigurasi](#konfigurasi)
- [Peluncur, cek kesehatan, dan layanan](#peluncur-cek-kesehatan-dan-layanan)
- Referensi pemakaian: [Perintah chat](#perintah-chat), [Pintasan keyboard](#pintasan-keyboard)
- Panduan fitur: [Bicara lewat mikrofon](#bicara-lewat-mikrofon), [Terjemah layar](#terjemah-layar-ocr), [`/rea`](#membedah-file-dengan-rea), [Animasi VRMA](#animasi-klip-vrma), [Mini-browser](#mini-browser-chrome), [Jembatan baca-saja](#jembatan-baca-saja-untuk-hermes)
- [Kemampuan Hermes Agent](#kemampuan-hermes-agent)
- [Keamanan](#keamanan)
- [Status pengujian](#status-pengujian) dan [Rencana](#rencana)
- [Struktur proyek](#struktur-proyek), [Aset](#aset)
- [Pemecahan masalah](#pemecahan-masalah)
- [Dokumentasi](#dokumentasi), [Riwayat pembaruan](#riwayat-pembaruan), [Lisensi](#lisensi)

---

## Mulai cepat

Ringkasnya: pasang dependensi, isi `.env` (terutama `COMPANION_TOKEN`), jalankan server dan overlay, atau cukup pakai peluncur. Rinciannya ada di tiga bagian berikut; panduan langkah demi langkah ada di [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

### Prasyarat

| Kebutuhan | Keterangan |
|---|---|
| Windows 10/11 | Overlay berjalan di Windows |
| Node.js 18+ | Untuk Electron |
| Python 3.11+ | Untuk `server.py` |
| VOICEVOX Engine | Berjalan di port `50021` (opsional, tanpa ini Iris menjawab lewat teks saja). Peluncur menjalankan `vv-engine\run.exe` (build DirectML, mis. versi 0.25.2) dengan GPU yang mendukung DirectX 12; tanpa folder itu ia memakai unit `voicevox` di WSL (CPU). Folder `vv-engine` tidak ada di repositori, letakkan sendiri di folder proyek |
| 9Router atau endpoint LLM kompatibel OpenAI | Berjalan di `localhost:20128` secara bawaan |
| WSL2 + Hermes Agent | Opsional, hanya untuk fitur `/agen` |
| faster-whisper | Opsional, hanya untuk bicara lewat mikrofon |

Disarankan RAM 16 GB jika Hermes dan model lokal dijalankan bersamaan. Batas memori WSL di proyek ini diset 4 GB lewat `.wslconfig`.

### Instalasi

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

Lalu buka `.env` dan isi dengan nilai milikmu sendiri. **`COMPANION_TOKEN` wajib diisi** (minimal 16 karakter); server langsung berhenti dengan pesan `[FATAL]` kalau kosong. Buat tokennya dengan:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Jangan pernah meng-commit file `.env`.**

Panduan langkah demi langkah: [docs/QUICKSTART.md](docs/QUICKSTART.md)

### Menjalankan

#### Cara manual

Buka dua terminal di folder proyek.

**Terminal 1: server**

```powershell
.\.venv\Scripts\python.exe server.py
```

**Terminal 2: overlay**

```powershell
npm start
```

Cek kesehatan layanan di `http://127.0.0.1:8765/health`. Untuk sekadar memastikan server hidup (tanpa memeriksa layanan lain), buka `http://127.0.0.1:8765/ping`; jawabannya `{"ok":true}`.

> Karena `COMPANION_TOKEN` wajib, halaman `http://127.0.0.1:8765` di browser tidak bisa dipakai untuk chat (browser tidak dapat mengirim header token). Gunakan overlay Electron. Halaman tes `dev/test_client.html` hanya tersedia bila kamu sengaja menjalankan server dengan `COMPANION_ALLOW_NO_TOKEN=1` dan token kosong.

#### Lewat peluncur

`IrisLauncher.exe` menjalankan WSL, layanan pendukung, server, dan overlay sekaligus. Bangun sendiri dengan `IrisLauncher-src\build.bat` (memakai `csc.exe` bawaan Windows, tanpa memasang apa pun), atau unduh dari tab Releases bila tersedia.

---

## Fitur

### Avatar dan tampilan

- Avatar VRM 3D dalam jendela Electron transparan yang selalu di atas, dengan klik tembus di area kosong
- Gerak natural: ekspresi dengan pegas teredam dan crossfade, bernapas, berkedip asimetris, dan tatapan tenang mengikuti kursor. Kepala bergerak mengikuti energi suara, dan pose `think` ditahan selama agen bekerja
- **Mood** yang bertahan antarhari (`/mood`): skor tersimpan dan memengaruhi ekspresi, ambang ngambek, sapaan, dan nada bicara
- **Kustomisasi:** ganti baju (maid bawaan, gaun pesta prom, seragam sekolah; bisa berganti otomatis menurut situasi dan musim), tema warna Iris, empat musim, dan Otomatis dengan efek jatuh musiman (`/tema`), tampilan tubuh penuh atau setengah badan (`/badan`), bayangan siluet HD per keadaan (`/bayangan`), dan kualitas gambar adaptif `auto`, `tinggi`, `normal`, `hemat` (`/kualitas`)
- **Bubble** di atas kepala: teks Indonesia, kalimat Jepang berlabel 日本語, garis aksen sesuai emosi, bisa digulir, tidak keluar jendela, dan bergeser menjauhi menu atau popover yang terbuka
- **Pikiran batin:** kadang satu baris bisikan hati kecil dan miring di atas bubble (tidak disuarakan dan tidak masuk riwayat). Saklar di Pengaturan
- **Klip gerak VRMA** (9 klip): dipicu oleh emosi, frasa ucapan, sentuhan, dan gerak idle. Lihat [Animasi klip VRMA](#animasi-klip-vrma)
- Seluruh UI dijaga di dalam layar; jendela yang dilepas jauh dari tepi meluncur balik ke area kerja

### Interaksi dengan karakter

- **Seret karakter** langsung atau lewat tombol grip di bar. Keduanya punya saklar sendiri, dan satu selalu tersisa supaya Iris tidak terkunci (`/angkat`)
- Pose **diangkat** (badan berayun seperti bandul, reaksi bersuara) serta reaksi sakit saat menabrak sisi atau pojok layar
- **Sembunyi di tepi layar dan mengintip** (`/sembunyi`): dilepas dekat tepi, Iris bersembunyi, lalu muncul lagi saat kursor menempel atau diklik
- **Duduk di tepi atas jendela lain** (`/duduk`). Bawaan mati karena menyentuh privasi; yang dibaca hanya posisi dan ukuran jendela, bukan judul, nama proses, atau isinya
- **Colek dan elus:** colek berkali-kali dibalas "geli", gumaman, lalu ngambek 10 detik; tahan klik kiri di kepala untuk mengelus. Klik bagian tubuh dibalas suara berbeda-beda
- **Menu aksi cepat** lewat klik kanan karakter, dan ikon tray untuk pengaturan
- Bar input auto-sembunyi dengan garis petunjuk hijau yang "bernapas" (merah saat server mati, cyan saat agen bekerja)
- **Mode fokus:** karakter dan bubble hilang, hanya garis tipis tersisa, dan klik tembus. Sejak 12 November 2026 mode ini juga diberitahukan ke `main.js` lewat `setQuiet` di `preload.js` *(eksperimental)*
- **Tidur otomatis** saat tidak ada aktivitas (bawaan 5 menit); bangun saat kursor bergerak atau diklik

### Obrolan dan suara

- Obrolan dengan persona Iris (gaya santai, campuran Indonesia dan Jepang) dan sapaan menurut waktu
- **Suara per emosi lewat VOICEVOX:** kecepatan, nada, dan intonasi menyesuaikan emosi, lip-sync berbasis mora, dan cache suara lokal. Mesin berjalan di Windows dengan GPU (DirectML) atau CPU, dipilih di Pengaturan peluncur
- Reaksi lokal (colek, sapaan, timer, dan sebagainya) bersuara tanpa memanggil model, dan pesan galat ikut dibacakan
- **Pemeriksa bagian Jepang** (`jp_speakable()`, 12 November 2026) *(eksperimental)*: kalimat "Jepang" dari model yang ternyata tanpa kana atau kanji, atau bercampur kata Indonesia, diperbaiki sekali lewat model; bila tetap gagal, kalimat tampil tanpa suara dan VOICEVOX tidak dipanggil. Biayanya satu panggilan model tambahan per baris bermasalah
- **Fun fact** acak bersuara (`/funfact`): dari 30 fakta bawaan atau dibuat model sesuai topik. Fakta buatan model diperiksa lagi (istilah baku Indonesia wajib, kalimat Inggris atau janggal disaring, lalu diverifikasi sekali lagi; `FUNFACT_VERIFY`, bawaan aktif)
- **Alarm, jam, timer, Pomodoro, dan pengingat istirahat**
- **Statistik fokus** (`/statistik`): sesi Pomodoro "Fokus" yang selesai penuh dicatat per hari (hanya jumlah sesi dan menit, lokal, maksimal 120 hari), dengan laporan 7 hari berisi batang, total, rata-rata, dan rantai hari berturut-turut
- **Sapaan sesuai waktu** (`/sapa`, bawaan mati): satu kalimat tetap per slot waktu, sekali sehari, tanpa memanggil model, dengan jarak minimal 90 menit. Tidak muncul saat mode fokus, tidur, merekam, suara dibisukan, chat terbuka, atau terjemah berjalan
- **Panel chat** dengan riwayat, tombol Hapus, "Mode jelaskan", tombol memanjangkan kotak, dan popup **Salin link**. Ucapan otomatis tercatat sebagai kotak sendiri dengan tombol salin, suka, dan tidak suka; tombol putar ulang suara pada ucapan otomatis *(eksperimental)*
- **Ekspor percakapan** ke satu berkas HTML mandiri di Downloads (`/ekspor`)
- **Pilihan bernomor:** `/baju`, `/tema`, `/alarm`, dan `/lokal daftar` menampilkan daftar, lalu cukup ketik angkanya
- Pil status koneksi `V 9 H` (VOICEVOX, 9Router, Hermes) dan titik bar hijau, kuning, atau merah (`/status`)

### Penglihatan, input, dan belajar

- **Lampiran gambar** lewat tempel (`Ctrl+V`), tombol klip, atau seret berkas; thumbnail bisa diklik, dengan penampil besar (zoom, Salin gambar, Simpan)
- **Screenshot layar** langsung jadi lampiran (tombol kamera, pintasan, atau tray)
- **Terjemah layar:** teks Jepang atau Inggris dikenali lewat OCR, diterjemahkan ke Indonesia, lalu digambar menimpa teks asli. Lihat [Terjemah layar](#terjemah-layar-ocr)
- **Tawaran aksi saat menyalin** (`/tawar`, bawaan mati): popup Terjemah, Rangkum, atau Perbaiki. Teks yang mirip kata sandi, token, atau nomor kartu tidak pernah ditawarkan
- **`/rangkum`:** merangkum halaman `/chrome`, sebuah link, atau sebuah file. **`/clip`:** menanyakan isi clipboard. **`/pantau`:** komentar layar otomatis (ditandai 👁)
- **Bicara lewat mikrofon** (STT opsional, faster-whisper). Lihat [Bicara lewat mikrofon](#bicara-lewat-mikrofon)
- **Belajar bahasa Jepang:** `/belajar` (Iris memberi kalimat Jepang, kamu menebak arti atau mengulang ucapannya, lalu dikoreksi) dan `/kana` (kuis kana yang diperiksa lokal tanpa model; Hepburn dan Kunrei diterima, dengan opsi `hira`, `kata`, `campur`, `lengkap`, `kombinasi`; tanda panjang ー dan っ kecil belum ada)
- **Game teka-teki** (`/tekateki`, 12 November 2026) *(eksperimental)*: teka-teki Indonesia, Jepang, atau campuran dengan petunjuk (`/petunjuk`) dan menyerah (`/menyerah`). Poin 3 dikurangi jumlah petunjuk (minimal 1) dengan hitungan beruntun, dan ronde kedaluwarsa setelah 600 detik. Bank bawaan di `data/tekateki.json`, tambahan dibuat model (maksimal 200 tersimpan). Sejak v102.1 `tekateki_state.json` menyimpan semua id yang pernah muncul (`dimainkan`), terpisah dari jendela anti-ulang 30 id (`riwayat`), sehingga pembuatan teka-teki baru otomatis ikut jalan walau bank lebih dari 32 butir; berkas simpanan lama dimigrasi sendiri. Tanpa `iris_games.py` server tetap jalan tanpa `/tekateki`
- **Perintah aplikasi lokal** (`/lokal`): membuka aplikasi dari daftar putih di `main.js`

### Agen dan memori

- **Jembatan Hermes Agent** (`/agen`, `/agent`, `/h`): memberi tugas ke agen di WSL, lengkap dengan indikator "sedang memproses", heartbeat, tombol Stop (menghentikan agen di Hermes bila `HERMES_STREAM=1`), dan batas waktu
- **Dua lapis pengaman tindakan:** tugas `/agen` berbau hapus, pindah, timpa, atau format file ditahan dulu dengan kartu "Iris mau menjalankan ini. Lanjut?"; perintah yang ditandai Hermes menampilkan kartu izin **Izinkan sekali** atau **Tolak** (tanpa jawaban, koneksi putus, atau Stop berarti ditolak; pilihan "selalu" dan "sesi" tidak pernah ditawarkan). Penolakan disampaikan Iris sebagai keputusanmu (baris `[Catatan Iris]`), bukan kegagalan agen
- **Sandbox Docker:** terminal agen berjalan di kontainer tanpa jaringan yang hanya bisa menulis ke folder kerja. Tugas dengan path di luar folder kerja ditolak sebelum dikirim, dan Iris memeriksa disk sendiri lalu menambahkan baris `[Verifikasi Iris]` karena laporan agen tidak selalu benar. Lihat [Keamanan](#keamanan)
- **Bedah file** (`/rea`): analisis statis file atau folder dengan mode `cepat`, standar, dan `dalam`. Lihat [Membedah file dengan `/rea`](#membedah-file-dengan-rea)
- Kartu **Hasil tugas** dengan tombol Salin; path WSL di laporan otomatis menjadi path Windows (`C:\Users\<user>\...`), termasuk folder berspasi. Hermes menerima konteks 10 pesan terakhir hanya bila tugas merujuk ke percakapan
- Iris dilarang mengaku bisa membuat, mengubah, atau menghapus file di obrolan biasa, dan menyuruh memakai `/agen`. Laporan agen disampaikan netral dan bersumber
- **Memori ringan:** `/ingat`, `/memori`, `/lupa` (maksimal 40 hal, 200 karakter per hal; isi yang mirip rahasia ditolak)
- **Riwayat obrolan persisten:** 20 pesan terakhir, kedaluwarsa 3 hari, gambar tidak pernah disimpan, pasangan pesan berisi kata rahasia tidak ditulis
- **Mini-browser multi-akun** (`/chrome`). Lihat [bagiannya](#mini-browser-chrome)

### Infrastruktur

- `IrisLauncher.exe`: peluncur satu klik dengan indikator hijau per layanan. Menutup peluncur ikut mematikan semua layanan (bisa dimatikan di Pengaturan), dan menu **Keluar** di overlay bisa mematikan semuanya lewat peluncur
- Kotak **Mesin suara VOICEVOX** (GPU atau CPU) di Pengaturan peluncur; bila folder `vv-engine` tidak ada, peluncur memakai unit `voicevox` di WSL (CPU)
- **Ikon tray berwarna** (hijau semua aktif, kuning ada yang bermasalah, merah tidak merespons, abu server tidak terhubung) dengan petunjuk perbaikan satu baris di menu tray
- **Ekspor dan impor konfigurasi** pengaturan overlay (`/config ekspor`, `/config impor`)
- `iris-doctor.ps1` (cek kesehatan), `iris-start.ps1` dan `iris-stop.ps1` (start dan stop berurutan, aman dijalankan berulang), dan `9router.service` (9Router sebagai layanan systemd di WSL)
- `.wslconfig` dengan batas memori WSL 4 GB dan `networkingMode=mirrored` (supaya WSL menjangkau VOICEVOX di Windows lewat `localhost`)

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
| `iris_translate_img.py` | OCR dan penggambar ulang terjemahan layar (winocr atau Tesseract) |
| `rea_triage.py` | Triase statis file untuk `/rea` (hash, jenis, header, impor, string, IOC, indikasi kemampuan, skor heuristik, draf YARA); hanya pustaka standar Python. Versi saat ini v98 (v97 menambah Mach-O, metadata .NET, CTPH, dan perburuan XOR/ADD/ROL; v98 menambah RE Lab untuk PE x86/x64) |
| `rea_extract.py` | Penjelajah container untuk `/rea`: ZIP, TAR/gz, GZIP, ISO 9660, ISO PSP (impor malas, opsional; belum diperiksa) |
| `rea_binary.py` | Binary Workbench: hex view, data inspector, pencarian, perbandingan, dan patch berundo (impor malas, opsional; belum diperiksa) |
| `iris_games.py` | Game teka-teki `/tekateki` (opsional) |

---

## Teknologi

- **Frontend:** Electron, three.js, `@pixiv/three-vrm`
- **Backend:** Python, FastAPI, WebSocket
- **Suara:** VOICEVOX (TTS), faster-whisper (STT, opsional)
- **LLM:** 9Router (endpoint OpenAI-compatible)
- **Agen:** Hermes Agent di WSL2
- **Peluncur:** `IrisLauncher` (C# dan PowerShell, kode di [`IrisLauncher-src/`](IrisLauncher-src/))

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
| `COMPANION_HOST` | Alamat server overlay. Selain `127.0.0.1` / `localhost`, server mencetak peringatan karena terbuka ke jaringan (v101) | `127.0.0.1` |
| `COMPANION_ALLOWED_HOSTS` | Nama host tambahan yang diterima di header `Host` (pisahkan dengan koma). Penjaga ini melawan DNS rebinding (v102); `COMPANION_HOST` yang bukan loopback otomatis diizinkan | kosong |
| `COMPANION_PORT` | Port server overlay | `8765` |
| `COMPANION_USER_NAME` | Nama panggilan pengguna | `Rover` |
| `COMPANION_TOKEN` | Token autentikasi `/ws`. **Wajib**, minimal 16 karakter; server tidak mau jalan tanpanya (lihat [Keamanan](#keamanan)) | kosong (wajib diisi) |

### Hermes

| Variabel | Fungsi | Bawaan |
|---|---|---|
| `HERMES_URL` | Alamat API server Hermes | `http://127.0.0.1:8642/v1` |
| `HERMES_API_KEY` | Kunci API Hermes (harus sama dengan `API_SERVER_KEY` di Hermes) | kosong |
| `HERMES_TIMEOUT` | Batas waktu tugas agen (detik) | `900` |
| `HERMES_STREAM` | `1` memakai respons stream. **Disarankan `1`**: dengan ini tombol Stop memanggil `POST /v1/runs/{id}/stop` di Hermes sebelum koneksi ditutup | `0` (isi `1` di `.env`) |
| `HERMES_WIN_HOME` | Folder user Windows dilihat dari WSL (wajib diisi per PC) | `/mnt/c/Users/<user>` |
| `HERMES_SANDBOX` | `1` bila terminal Hermes memakai sandbox Docker: path di luar folder kerja ditolak di Iris, path dipetakan dua arah, dan hasil diverifikasi ke disk | kosong (isi `1` bila sandbox dipakai) |
| `REA_STAGE` | `0` mematikan penyalinan otomatis file ke folder kerja agen untuk `/rea` (aktif hanya bila `HERMES_SANDBOX=1`) | `1` |
| `REA_STAGE_MAX_MB` | Batas ukuran file (atau total folder) yang disalin untuk `/rea` | `300` |
| `REA_DIR_MAX_FILES` | Batas jumlah berkas saat folder dikemas jadi zip untuk `/rea` | `3000` |
| `REA_KEEP_DAYS` | Berkas di `rea-input` yang lebih tua dari ini dihapus otomatis (`0` = jangan hapus) | `7` |
| `REA_MAX_CHARS` | Batas karakter kartu hasil `/rea` (tugas `/agen` biasa tetap lebih pendek, 3000) | `9000` |
| `REA_REPORT_DIR` | Folder laporan penuh `/rea` | `rea-reports` di samping `server.py` |
| `REA_CARVE` | `1` mengekstrak payload yang tertanam (PE polos, base64, XOR) ke `rea-input\carved`. **Bawaan mati** karena hasil ekstraksi bisa memicu Windows Defender | `0` |
| `REA_RAW_ONLY` | `0` mengembalikan ceritaan ulang oleh Iris; bawaan hasil `/rea` hanya tampil sebagai kartu mentah | `1` |
| `REA_PLUGINS` | Folder plugin parser untuk Asset Explorer. Plugin adalah kode yang dijalankan, jadi hanya dimuat lewat variabel ini atau `--plugins`, tidak pernah lewat permintaan API agen | kosong |

### Opsional (`IRIS_*`)

| Variabel | Fungsi |
|---|---|
| `COMPANION_ALLOW_NO_TOKEN=1` | **Khusus pengembangan**: izinkan server jalan tanpa token (mis. untuk `dev/test_client.html`). Jangan dipakai untuk pemakaian sehari-hari |
| `AGENT_CONFIRM_ALWAYS=1` | Tetap tampilkan kartu konfirmasi Iris walau gerbang persetujuan Hermes aktif (jaring cadangan) |
| `AGENT_APPROVAL=0` | Matikan kartu izin Hermes (semua izin ditolak otomatis) |
| `AGENT_APPROVAL_TTL` | Batas menunggu klik kartu izin (detik, bawaan 120, maksimal 280) |
| `AGENT_APPROVAL_CMD_MAX` | Panjang maksimal perintah yang ditampilkan di kartu izin (bawaan 2000). Perintah lebih panjang ditolak otomatis, tidak dipotong (v102) |
| `AGENT_APPROVAL_AUTO=readonly` | **Opt-in, bawaan mati.** Izinkan otomatis perintah yang terbukti hanya membaca; selebihnya tetap tampil sebagai kartu. Butuh `approval_policy.py` (lihat [Keamanan](#keamanan)) |
| `AGENT_APPROVAL_AUTO_ROOT` / `AGENT_APPROVAL_AUTO_SCRATCH` | Akar sandbox (bawaan `/workspace`) dan folder sementara tempat perintah boleh menulis (bawaan `/tmp`) untuk pemeriksaan di atas |
| `IRIS_MAX_AUX_TASKS` | Batas tugas pendamping per koneksi `/ws` (bawaan 64, v102) |
| `IRIS_VOICE_STYLE=0` | Matikan gaya suara per emosi |
| `IRIS_THOUGHTS=0` | Matikan pikiran batin dari sisi server |
| `IRIS_HISTORY=0` | Matikan riwayat obrolan persisten |
| `IRIS_HISTORY_DAYS` | Lama riwayat disimpan (bawaan 3 hari) |
| `IRIS_HISTORY_FILE`, `IRIS_MEMORY_FILE` | Ganti lokasi berkas riwayat dan memori |
| `IRIS_SAVE_SCREEN=0` | Jangan sertakan screenshot terakhir ke Hermes |
| `IRIS_MUTE_KEY` | Paksa kombinasi pintasan bisu sendiri |
| `IRIS_STT_MODEL`, `IRIS_STT_LANG`, `IRIS_STT_DEVICE`, `IRIS_STT_COMPUTE` | Pengaturan faster-whisper (lihat [Bicara lewat mikrofon](#bicara-lewat-mikrofon)) |
| `IRIS_STT_PROMPT` | Kosakata bantu untuk Whisper (nama dan istilah khusus, dipisah koma) supaya tidak salah dengar |
| `IRIS_NEWTAB_URL` | Halaman awal mini-browser untuk akun tanpa link |
| `IRIS_WEB_BRIDGE=1` | Nyalakan jembatan baca-saja (butuh `COMPANION_TOKEN`) |
| `IRIS_BRIDGE_HOST`, `IRIS_BRIDGE_PORT` | Alamat jembatan baca-saja (port bawaan 8767) |
| `IRIS_PEEK_CUT` | Seberapa banyak karakter terlihat saat mengintip |
| `IRIS_TL_MULTIPASS=0` | Matikan OCR pass cadangan pada terjemah layar |
| `IRIS_TL_MAX_BLOCKS` | Batas blok teks per terjemah layar (bawaan 120) |
| `IRIS_TL_MAX_PIXELS` | Batas piksel gambar yang diterima terjemah layar (bawaan 40 juta; v101). Gambar lebih besar ditolak sebelum dimuat ke memori |
| `IRIS_TL_FONT_JP` | Font Jepang untuk menggambar hasil (bawaan Meiryo, Yu Gothic, atau Noto CJK) |
| `IRIS_TL_DEBUG=1` | Simpan `iris_tl_debug.png` dan `iris_tl_debug.json` (kotak hijau diterjemahkan, merah tidak) |
| `IRIS_TL_VOICE=0` | Iris tidak bicara saat terjemah layar |
| `FUNFACT_VERIFY` | `0` mematikan verifikasi kedua fun fact buatan model (bawaan `1`; verifikasi yang timeout atau galat tetap memakai fakta) |
| `FUNFACT_TIMEOUT` | Batas total waktu pembuatan fun fact (detik, maksimal 48) |
| `GAME_MODEL` | Model untuk teka-teki buatan model (kosong = `NINEROUTER_MODEL`) |
| `GAME_AUTOGEN=0` | Matikan pembuatan teka-teki otomatis oleh model |
| `IRIS_WEB_KEEP` | Jumlah tab `/chrome` yang tetap hidup (1 sampai 10, bawaan 3; yang paling lama tidak dipakai dibuang dulu; 1 = satu akun hidup) |
| `IRIS_LAUNCHER_EXE` | Diisi otomatis oleh peluncur. Bila ada, menu **Keluar** menawarkan "matikan semua" lewat `IrisLauncher.exe --stop-all`; tanpanya Keluar hanya menutup overlay |
| `IRIS_SIT_FALL` | Jarak jatuh maksimum dari udara ke tepi atas jendela di bawahnya untuk `/duduk` (bawaan 700) |
| `IRIS_SIT_BAR` | Ruang kosong di bawah karakter dalam jendela, dipakai menebak posisi dasar karakter saat dilepas (bawaan 74) |
| `IRIS_HIT_SPEED` | Ambang kecepatan seret untuk reaksi saat menabrak pojok layar (bawaan 650) |
| `IRIS_EDGE_SPEED` | Ambang kecepatan seret untuk reaksi saat menabrak sisi layar (bawaan 900) |
| `IRIS_HEALTH_CONNECT` | Batas sambung (detik, bawaan 1,5) per layanan saat `/health` memeriksa VOICEVOX, 9Router, dan Hermes |

Cara membuat token ada di bagian [Instalasi](#instalasi).

---

## Peluncur, cek kesehatan, dan layanan

| Berkas | Fungsi |
|---|---|
| `IrisLauncher.exe` | Antarmuka Start, Stop, dan Doctor dengan indikator hijau per layanan (WSL, VOICEVOX, 9Router, Hermes, server, overlay) |
| `iris-start.ps1` | Menyalakan WSL, lalu hanya layanan yang belum menjawab (VOICEVOX, 9Router, Hermes) secara paralel, lalu `server.py` dan overlay. Idempoten dan tidak membuat server atau overlay kedua. VOICEVOX dijalankan dari `vv-engine\run.exe` di Windows (GPU; diulang tanpa GPU bila gagal, atau kembali ke unit WSL bila folder tidak ada). Log mesin: `iris-voicevox.out.log` dan `iris-voicevox.err.log` |
| `iris-stop.ps1` | Menghentikan overlay dan server (opsi untuk menghentikan layanan lain dan sesi penjaga WSL). Mesin VOICEVOX Windows hanya dimatikan bila `run.exe` berasal dari folder `vv-engine` proyek ini |
| `iris-doctor.ps1` | Memeriksa folder proyek, `.venv`, Electron, `.env`, port, status WSL dan Hermes, `.wslconfig`, ruang disk, dan RAM. Tiap baris `OK`, `WARN`, atau `GAGAL` disertai cara memperbaiki; `WARN` juga muncul bila unit `voicevox` di WSL masih aktif (bisa merebut port 50021). Nilai token tidak pernah dicetak |
| `iris-hermes.ps1`, `iris-service.ps1` | Pembungkus untuk Hermes dan layanan WSL |
| `9router.service` | Layanan systemd pengguna di WSL untuk 9Router |

**Cara peluncur menilai server hidup**

- Peluncur, `iris-start.ps1`, dan `iris-service.ps1` memakai `GET /ping`, bukan `/health`. `/health` ikut memeriksa VOICEVOX, 9Router, dan Hermes, jadi melambat saat salah satunya mati dan bisa membuat server yang masih hidup tampak mati. Server lama tanpa `/ping` tetap dikenali (balasan 404 dihitung hidup).
- `/health` tetap dipakai pil status di overlay, `/status`, dan `iris-doctor.ps1`. Batas sambung per layanan di `/health` 1,5 detik (ubah lewat `IRIS_HEALTH_CONNECT`).

**Mesin suara VOICEVOX (GPU)**

- Di Pengaturan peluncur ada kotak **Mesin suara VOICEVOX** untuk memilih GPU atau CPU (disimpan sebagai `vvgpu` di `settings.ini`). Chip VOICEVOX menyalakan atau mematikan mesin Windows tanpa membangunkan WSL.
- Letakkan folder `vv-engine` (engine VOICEVOX build DirectML) di folder proyek. Folder ini dan `iris-voicevox.*.log` tidak ikut repositori.
- Matikan unit lama di WSL supaya tidak merebut port: `wsl -d Ubuntu -- systemctl --user disable --now voicevox`.
- Setelah Start, pemilik port harus `run` (mesin Windows), bukan `wslrelay`: `Get-Process -Id (Get-NetTCPConnection -LocalPort 50021 -State Listen).OwningProcess`.

**Menutup peluncur dan menu Keluar**

- Saat jendela peluncur ditutup dan masih ada layanan yang hidup, muncul pilihan: **Ya** (matikan semua lalu tutup), **Tidak** (tutup peluncur saja, layanan tetap hidup), atau **Batal**. Yang dimatikan mengikuti pilihan Stop di Pengaturan (semuanya termasuk WSL, atau hanya overlay dan `server.py`).
- Di Pengaturan ada kotak centang untuk mematikan perilaku ini, dan satu lagi untuk melewati pertanyaan konfirmasi.
- Menu **Keluar** (tray dan klik kanan karakter) bertanya apakah semua layanan ikut dimatikan. Pilihan "Matikan semua" memanggil `IrisLauncher.exe --stop-all`, baik peluncurnya sedang terbuka maupun tidak. Pilihan ini hanya muncul bila overlay dijalankan lewat peluncur; kalau overlay dijalankan dengan `npm start`, Keluar hanya menutup overlay.
- `Ctrl+Alt+Q` tetap keluar darurat yang hanya menutup overlay.

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
| `/rea [cepat\|dalam] <path> [fokus]` (alias `/reverse`) | Bedah file atau folder secara statis lewat Hermes; `cepat` hanya triase lokal tanpa Hermes. Lihat [Membedah file dengan `/rea`](#membedah-file-dengan-rea) |
| `/rea xref <path> <API, string, atau alamat>` dan `/rea disasm <path> [entry\|0xAlamat] [baris]` | Alat RE Lab lokal untuk PE x86 / x64, tanpa Hermes (v99). Seret file apa pun (bukan gambar) ke overlay = `/rea cepat` |
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
| `/statistik [reset]` (alias `/stat`, `/stats`) | Statistik sesi Pomodoro 7 hari terakhir; `reset` menghapus catatan |
| `/sapa [nyala\|mati\|sekarang]` | Sapaan sesuai waktu (bawaan mati); `sekarang` memaksa satu sapaan untuk slot saat ini tanpa mencatatnya |
| `/funfact [sekarang\|10-30\|20\|mati\|nyala]` (alias `/ff`, `/tahukah`) | Atur fun fact acak; `/funfact topik <topik>`, `/funfact bawaan`, `/funfact model` |
| `/fokus` | Mode fokus (karakter dan bubble hilang) |
| `/bisu` | Matikan suara |
| `/tidur` | Iris tidur |

### Layar dan belajar

| Perintah | Fungsi |
|---|---|
| `/layar [tanya]` | Ambil screenshot lalu bertanya |
| `/terjemah [auto\|ja\|en\|teks]` (alias `/tl`, `/translate`) | Pilih area layar dengan menyeret, lalu terjemahkan teks di area itu; tanpa argumen memakai pilihan bahasa di menu. Tambahan: `ulang` (pakai lagi area terakhir), `penuh` (seluruh layar), `teks` (balasan teks saja), `tutup` (lepas terjemahan yang menempel), `tempel nyala\|mati`. Lihat [Terjemah layar](#terjemah-layar-ocr) |
| `/rangkum [halaman] [fokus]` | Rangkum halaman yang terbuka di `/chrome` |
| `/rangkum <link> [fokus]` | Rangkum sebuah link lewat Hermes (link lokal dan jaringan pribadi ditolak) |
| `/rangkum <path penuh> [fokus]` | Rangkum sebuah file lewat Hermes (path berspasi diapit tanda kutip; di sandbox praktis hanya folder kerja agen) |
| `/tawar [nyala\|mati]` | Tawaran aksi saat menyalin teks (bawaan mati) |
| `/clip` | Tanya isi clipboard |
| `/pantau` | Komentar layar otomatis (ditandai 👁) |
| `/belajar [topik]` | Mode belajar bahasa Jepang, mis. `/belajar makanan` |
| `/kana [hira\|kata\|campur] [lengkap] [kombinasi]` | Kuis kana lokal; `stop` atau `/kana stop` mengakhiri |
| `/tekateki [id\|jp\|campur]` (alias `/riddle`, `/nazonazo`) | Mulai game teka-teki; `/tekateki lewati`, `/tekateki skor`, `/tekateki stop` |
| `/petunjuk` (alias `/hint`, `/clue`) | Minta petunjuk pada ronde berjalan |
| `/menyerah` (alias `/nyerah`, `/giveup`) | Menyerah dan lihat jawabannya |
| `/skip` | Lewati teka-teki ini (sama dengan `/tekateki lewati`) dan mulai yang baru |

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
| `/config ekspor` / `/config impor` | Simpan atau muat pengaturan overlay (berkas `Iris-config_<tanggal>.json` di Downloads) |
| `/help` | Daftar perintah di aplikasi |

---

## Pintasan keyboard

| Pintasan | Fungsi |
|---|---|
| `Ctrl+Alt+C` | Buka chat |
| `Ctrl+Alt+S` | Screenshot layar |
| `Ctrl+Alt+T` | Terjemahkan layar (pilih area dengan menyeret) |
| `Ctrl+Alt+Y` | Ulangi terjemah di area terakhir yang dipilih, tanpa menyeret lagi (v99) |
| `Ctrl+Alt+V` | Tanya isi clipboard |
| `Ctrl+Alt+G` | Bicara lewat mikrofon (tekan lagi untuk berhenti, otomatis berhenti setelah 30 detik) |
| `Ctrl+Alt+H` | Tampilkan atau sembunyikan Iris |
| `Ctrl+Alt+B` | Bisukan suara dari sisi overlay (cadangan: `Ctrl+Alt+M`, `Ctrl+Shift+Alt+M`, atau `IRIS_MUTE_KEY`) |
| `Ctrl+Alt+W` | Buka atau tutup mini-browser |
| `Ctrl+Alt+Q` | Keluar darurat (hanya overlay; layanan lain tidak ikut dimatikan) |
| `Ctrl+Alt+D` | Buka DevTools overlay (hanya saat pengembangan, tidak ada di versi rilis) |
| `Ctrl+V` | Tempel gambar dari clipboard sebagai lampiran |

Klik kanan pada karakter untuk menu aksi cepat, dan gunakan ikon tray untuk pengaturan. Menu **Keluar** di tray dan di klik kanan menutup overlay, dan bila overlay dijalankan lewat peluncur bisa sekaligus mematikan semua layanan.

---

## Bicara lewat mikrofon

Opsional; butuh `pip install faster-whisper`. Klik ikon mik atau tekan `Ctrl+Alt+G`, ucapkan satu kalimat, lalu klik lagi (otomatis berhenti setelah 30 detik). Iris diam saat rekaman mulai supaya suaranya sendiri tidak ikut terekam. Pengenalan pertama lambat karena model diunduh dulu.

| Variabel | Pilihan | Catatan |
|---|---|---|
| `IRIS_STT_MODEL` | `tiny`, `base` (bawaan), `small`, `medium` | Makin besar makin akurat tetapi makin lambat dan berat. `medium` sekitar 1,5 GB; kembalikan ke `small` bila terlalu lambat atau RAM sesak |
| `IRIS_STT_LANG` | `id` (bawaan), `ja`, kosong | Kosong = deteksi otomatis. Bahasa dikunci agar tidak salah deteksi |
| `IRIS_STT_DEVICE` | `cpu` (bawaan) | |
| `IRIS_STT_COMPUTE` | `int8` (bawaan) | |
| `IRIS_STT_PROMPT` | teks bebas | Nama dan istilah yang sering salah dengar (mis. nama aplikasi). Server juga menambahkan kata bantu bawaan seperti "agen", "agent", dan "carikan" |

Tips akurasi: pakai model lebih besar, isi `IRIS_STT_PROMPT`, dan dekatkan mikrofon atau kurangi bising. Server memakai `vad_filter` dan tidak membawa teks sebelumnya ke pengenalan berikutnya untuk mengurangi kata karangan.

Perintah suara:

- Kalimat yang diawali kata kerja aksi (mis. "Cek brand ... itu apa?") dijalankan sebagai tugas walau Whisper menambahkan tanda tanya sendiri. Pertanyaan biasa tetap jadi obrolan.
- Setelah Iris menawarkan `/agen` (mis. "Mau /agen buat cari info?"), ucapan "iya", "boleh", atau "lanjut aja" menjalankan tugas dengan ucapanmu sebelumnya sebagai topik. Tawaran berlaku sekitar 5 menit; "ya" saja tanpa tawaran tidak memicu apa pun.

Batas: Whisper tetap bisa salah dengar total pada suara pelan atau bising, dan perintah yang salah dengar total tidak tertangkap. Cek hasil teksnya di chat (ditandai 🎤).

---

## Terjemah layar (OCR)

Tekan `Ctrl+Alt+T`, klik "Terjemah layar" di menu, atau ketik `/terjemah`. Sejak v90 alurnya seperti Snipping Tool: Iris menyembunyikan diri sebentar, layar tempat kursor berada difoto, lalu kamu menyeret kotak di atas area yang mau diterjemahkan (Esc atau klik kanan = batal). Hanya area itu yang dibaca dengan OCR, diterjemahkan ke Indonesia, digambar di atas teks asli, dan dibuka di penampil besar (zoom dan geser). `/terjemah penuh` memotret seluruh layar seperti cara lama.

- **Bahasa sumber:** pil **Auto / Jepang / Inggris** di bawah item menu "Terjemah layar". Auto mencoba Jepang dulu, lalu Inggris bila tidak ada huruf Jepang. Auto tidak menerjemahkan dua bahasa sekaligus. `/terjemah en`, `/terjemah ja`, atau `/terjemah auto` menimpa pilihan untuk satu kali jalan. Tujuan selalu Indonesia.
- **OCR Inggris di Windows** butuh paket bahasa OCR Inggris (Settings, Language and region, English, Language options, OCR).
- Teks yang sudah berbahasa Indonesia, nama, kode, dan URL dibiarkan. Blok yang terlewat diminta ulang ke model sampai 2 putaran.
- Tombol berhenti (kotak) membatalkan OCR, terjemahan, dan suara.
- **Area kecil diperbesar otomatis (v99).** Potongan kecil (mis. satu baris subtitle) diperbesar sebelum OCR, sampai sisi terpanjangnya sekitar 900 px dan sisi terpendeknya sekitar 120 px, maksimal 4 kali dan tidak lebih dari 6 juta piksel; selisih di bawah 1,25 kali dibiarkan. Hanya gambar yang dikirim ke OCR yang diperbesar; tampilannya di layar tetap seukuran area asli.
- **Terjemahan menempel di atas area (v99).** Hasil dari area yang dipilih ditampilkan di jendela kecil tanpa bingkai tepat di atas area aslinya, tanpa mengambil fokus. Klik (kiri atau kanan) pada gambar itu menutupnya; ia juga menutup sendiri setelah 3 menit, dan `/terjemah tutup` menutupnya dari chat. Jendela ditutup sebelum pemotretan berikutnya, jadi tidak ikut terfoto. `/terjemah tempel mati` mengembalikan perilaku lama (penampil besar saja); `nyala` menghidupkannya lagi (bawaan nyala). Ini satu kali tempel, bukan subtitle langsung: teks yang berubah tidak diterjemahkan ulang sampai kamu menjalankan perintah lagi.
- **Ulangi area terakhir (v99).** `Ctrl+Alt+Y` atau `/terjemah ulang [en|ja|auto]` memakai lagi kotak terakhir (layar yang sama) dan memfotonya baru, jadi dialog yang berganti tinggal diterjemahkan lagi. Ditolak dengan pesan jelas bila belum ada area, layarnya sudah tidak ada, atau resolusinya berubah. Kotak hanya diingat selama Iris berjalan.
- **Suara:** Iris mengucapkan kalimat pembuka selagi OCR berjalan dan kalimat penutup sesudah hasil tampil (semua blok, sebagian, atau gagal). Matikan dengan `IRIS_TL_VOICE=0`.
- **Penyaring sampah OCR:** serpihan ikon dan gambar yang terbaca sebagai `0000` atau huruf acak dibuang dan jumlahnya dilaporkan, supaya model tidak mengarang kalimat dari sampah.
- **Pertanyaan lanjutan:** Iris menyimpan daftar terjemahan (maksimal 1800 karakter) sebagai konteks, jadi pertanyaan seperti "isi terjemahan itu apa" dijawab dari teks yang terbaca, dan teks yang gagal dibaca tidak boleh dikarang. Baru ditulis, belum terbukti dengan model sungguhan.
- Batas: terjemahan yang menempel memakai ukuran area asli, jadi teks Indonesia yang lebih panjang bisa tampil lebih kecil dari aslinya; game fullscreen eksklusif tidak bisa difoto dan jendela tempelan bisa tidak terlihat di atasnya; tombol kecil, teks putih di atas gradasi, dan huruf sangat kecil masih bisa salah baca atau terlewat; halaman sangat padat dibatasi `IRIS_TL_MAX_BLOCKS` blok. Gunakan `IRIS_TL_DEBUG=1` untuk melihat blok mana yang diproses. Uji nyata terakhir pada halaman wiki Jepang menerjemahkan 42 dari 62 blok; paragraf pembuka yang besar masih tertinggal.

---

## Membedah file dengan `/rea`

`/rea` menyuruh Hermes membedah satu file atau folder (exe, dll, apk, jar, firmware, js) secara **statis** dengan skill `reverse-engineer-anything`. File tidak pernah dijalankan, dan isi file diperlakukan sebagai data, bukan perintah. Contoh:

```
/rea "C:\Users\<user>\Downloads\setup.exe" cari URL yang dihubungi
/rea cepat C:\Users\<user>\Downloads\app.dll
/rea dalam D:\kerja\firmware.bin
```

Path berspasi boleh diketik tanpa kutip; kata setelah path menjadi fokus analisis. Syaratnya `HERMES_SANDBOX=1`: file di luar folder kerja agen **disalin** (bukan dipindah) ke `rea-input` di dalam folder kerja, lalu path di tugas diganti dengan path salinan.

| Mode | Perintah | Cara kerja |
|---|---|---|
| Cepat | `/rea cepat <path>` | Hanya triase lokal Python, **tanpa Hermes**, hasil dalam hitungan detik. File dibaca langsung (hanya-baca) tanpa disalin, jadi path jaringan (UNC) ditolak |
| Standar | `/rea <path> [fokus]` | Hermes dibekali **fakta terukur** dari triase dan diminta tidak menghitung ulang |
| Dalam | `/rea dalam <path> [fokus]` | Seperti standar, ditambah permintaan dekompilasi atau disassembly fungsi penting, alur logika, algoritma, protokol, dan dekode string |

Alias mode: `quick`, `fast`, `standard`, `deep`.

- **Triase lokal** (`rea_triage.py`, fitur di bawah sampai v94; v97 menambah Mach-O penuh, metadata .NET, CTPH, perburuan XOR/ADD/ROL satu byte, detail kemasan, dan pengelompokan keluarga sampel di mode folder; v98 menambah RE Lab untuk PE x86/x64, lihat butir berikutnya; tanpa model dan tanpa menjalankan file): hash (SHA-256, SHA-1, MD5), jenis file (PE, ELF, ZIP/APK/JAR/OOXML, DEX, WASM, Mach-O, PDF, OLE2, RTF, LNK, skrip PowerShell/JS/VBS/BAT), entropi, dan indikasi kemampuan dari nama API persis (injeksi, anti-debug, jaringan, persistensi, kripto, `ptrace`, `dlopen`, `execve`, dan sejenisnya) dengan pemetaan perkiraan ke ATT&CK. **PE:** arsitektur, subsystem, timestamp, ASLR/DEP/CFG, .NET, tanda tangan (CN penandatangan dibaca dari blob; keabsahan tanda tangan tidak diperiksa), bagian beserta entropi dan flag, import, delay-import, export, resource dan info versi, Rich header, checksum header, imphash, dan overlay (blob tanda tangan tidak dihitung sebagai overlay). **ELF:** header, section, segmen, status stripped, impor dinamis, pustaka `NEEDED`, dan ekspor. **Arsip dan dokumen:** isi zip/APK/JAR/OOXML (izin Android, `Main-Class`, berkas tertanam, zip-slip, relasi eksternal, makro), PDF (JavaScript, `OpenAction`, `Launch`, nama berobfuskasi, data setelah EOF), OLE2 (makro, pemicu otomatis, Equation Editor), dan skrip (obfuskasi, unduh-eksekusi). **String dan IOC:** string ASCII dan UTF-16 (URL, kandidat IP, email, kunci registry, path Windows, kandidat kredensial yang disamarkan), IOC dalam bentuk defang, hasil dekode base64, PE tertanam (polos atau XOR satu byte), dan konstanta kripto (AES, SHA, MD5, CRC32, ChaCha/Salsa, Blowfish, tabel Base64). **Keluaran:** skor heuristik beralasan (tiap alasan menyebut buktinya), penanda pembuat atau pengemas dengan saran langkah lanjut, dan draf YARA. Pemindaian dibatasi 32 MB pertama.
- **RE Lab (v98, eksperimental, hanya PE x86 / x64):** analisis tingkat fungsi tanpa menjalankan file dan tanpa model, hanya di `rea_triage.py`. **Penemuan fungsi** lewat entry point, ekspor, target `CALL` relatif, dan prolog khas. **Peta panggilan API** per fungsi (`CALL [IAT]`, thunk `JMP [IAT]`, impor biasa dan delay-import) beserta jumlah caller dan callee. **Xref string** (ASCII atau UTF-16LE) ke fungsi pemakainya, dengan label untuk string menarik (URL, registry, perintah, nama alat analisis / VM, kredensial). **Peringkat fungsi menarik** menurut kelompok kemampuan (injeksi proses, jaringan / C2, eksekusi proses, kripto, persistensi, anti-debug, dan lain-lain). **Anti-analisis tingkat instruksi** (akses PEB / TEB, RDTSC, `INT 2D`, syscall langsung, Heaven's Gate), **API hashing** ror13 untuk 106 API Windows umum (dilaporkan bila minimal 2 konstanta cocok), stack string, dan pengenalan stub entry point. Tiap alasan skor menyebut buktinya. Tersedia lewat `rea_api` (aksi `re`, `xref`, `disasm`), CLI (`--re`, `--xref`, `--disasm`), dan sejak v99 lewat `/rea xref` dan `/rea disasm` di overlay (lihat butir berikutnya); `capstone` hanya perlu untuk `--disasm`. Baris "RE Lab" kini ikut di keluaran `/rea cepat` dan laporan standar untuk PE x86 / x64.
- **`/rea xref` dan `/rea disasm` (v99, hanya PE x86 / x64, tanpa Hermes):** `/rea xref <path> <nama API | potongan string | alamat fungsi>` menampilkan fungsi mana yang memakai API atau string itu; `/rea disasm <path> [entry | 0xAlamat | rva:0x... | off:0x...] [jumlah baris]` menampilkan disassembly (bawaan `entry`, 40 baris, maksimal 400). Tanpa pustaka `capstone` hasilnya tampilan hex. Keduanya lokal, hanya baca, dan hasilnya jadi kartu dengan laporan penuh di `rea-reports`. Argumen divalidasi di `index.html` dan sekali lagi di `server.py`; keluarannya dibersihkan dari karakter kontrol dan pengecoh arah teks, dan catatan riwayat Iris hanya menyebut bahwa alat dijalankan, tanpa string atau alamat dari sampel. Contoh: `/rea xref "Z:\Folder Saya\app.exe" VirtualAllocEx`, `/rea disasm "Z:\app.exe" 0x401000 60`. Di server, tugas bentuk `REA lokal xref|disasm: <path> ||| <argumen>` yang tidak valid ditolak, tidak diteruskan ke Hermes.
- **Seret-lepas file (v99):** file atau folder yang bukan gambar, diseret ke overlay, dijalankan sebagai `/rea cepat "<path>"`; hanya yang pertama bila banyak (sisanya diberi tahu), dan gambar tetap jadi lampiran. Path dibaca lewat `webUtils.getPathForFile` di `preload.js`. Hanya jalan saat jendela menerima mouse (chat terbuka, atau kursor di atas karakter atau menu); jendela yang sedang tembus-klik tidak menerima seretan, dan ini belum diuji di Electron asli.
- **Asset Explorer (v99.0, `rea_assets.py`, eksperimental):** membuka *isi* berkas non-exe tanpa menjalankannya dan tanpa model, hanya pustaka standar, dan hasil ditulis ke folder keluaran terpisah. Format: model 3D dan animasi (glTF/GLB, OBJ, STL, PLY, FBX, COLLADA, BVH), gambar (PNG, JPEG, GIF, BMP, TGA, DDS, WebP, ICO), audio (WAV, OGG, FLAC, MP3, MIDI), arsip dan paket game (Quake PAK, WAD, Unreal `.pak` v1 sampai v9 tanpa enkripsi, ZIP/APK/JAR, TAR, GZIP), dan SQLite. Aksinya: ringkasan isi, ekstraksi (mesh jadi `.obj`, tekstur jadi `.png`, tabel jadi `.csv`), dan *carving* berkas yang tertanam di berkas apa pun. Dipanggil lewat CLI `rea_triage.py` (`--assets`, `--assets-extract`, `--assets-carve`, `--formats`) atau aksi `rea_api`; di kode yang diunggah belum ada perintah chat khusus untuknya. Yang belum bisa dibuka (dilaporkan jelas, bukan ditebak): paket terenkripsi atau berformat sendiri, aset Unity/Unreal yang terserialisasi, dan tekstur BC4 sampai BC7 / ASTC. Parser tambahan bisa ditulis sebagai plugin (contoh: `example_plugin.py`). Belum dites di PC.
- **Akurasi:** jawaban agen berformat terstruktur (ringkasan, arsitektur, perilaku beserta bukti, IOC, risiko, yang tidak pasti, langkah lanjut), dan klaim penting wajib menyebut bukti dengan label `TERBUKTI` atau `DUGAAN`. Kartu hasil menaruh triase di atas dan tafsiran agen di bawah.
- **Folder:** `/rea <folder>` mengemas folder (tanpa symlink atau junction Windows) jadi satu zip di `rea-input`. Triase folder berperingkat dan menandai duplikat. Folder kosong atau terlalu besar ditolak dengan pesan jelas.
- **Pengerasan (v94):** isi sampel diperlakukan sebagai data tidak tepercaya. Teks triase (URL, nama, hasil dekode, info versi) dibungkus penanda `<<<DATA_SAMPEL_TIDAK_DIPERCAYA_...>>>` di tugas agen, dengan instruksi melaporkan, bukan menuruti; penanda palsu di dalam sampel dinetralkan dan karakter kontrol dibuang. Keluaran laporan disanitasi (karakter kontrol dan pembalik arah teks diganti `?`). Regex triase dibatasi supaya file besar berisi huruf berurutan tidak membuat triase macet (ReDoS pada versi lama). Riwayat Iris untuk `/rea` hanya memuat hash, jenis, dan skor, tanpa string dari sampel. Kartu hasil bisa memuat baris "Peringatan: sampel berisi instruksi yang diabaikan." bila agen menemukan teks mirip perintah di dalam sampel.
- **Ekstraksi payload (opsional):** dengan `REA_CARVE=1`, payload tertanam disalin ke `rea-input\carved`. Bawaan mati karena bisa memicu Windows Defender.
- **Laporan:** bagian skor dan PERHATIAN tidak lagi terpotong di kartu `/rea cepat` (versi muat-anggaran), sedangkan berkas laporan memuat versi penuh. Kartu hasil memuat sampai `REA_MAX_CHARS` karakter; laporan penuh ditulis ke `rea-reports/rea-<tanggal>-<jam>.md` dan path-nya ditempel di akhir kartu. Hasil tampil sebagai kartu mentah tanpa ceritaan ulang oleh Iris.
- **Pembersihan:** setiap `/rea` yang menyalin file menghapus berkas lama di `rea-input`, termasuk subfolder `carved` (lebih dari `REA_KEEP_DAYS`). Triase tetap berjalan walau `HERMES_SANDBOX=0` (file tidak disalin dan tidak ada carve di lokasi sumber).

> **Anggap hasilnya petunjuk, bukan temuan.** Triase murni statis: tanpa dekompilasi, emulasi, atau jaringan, dan "indikasi kemampuan" hanya petunjuk dari nama API (program sah juga memakainya; IP bisa saja nomor versi). Laporan agen pernah memuat klaim yang saling bertentangan pada file yang diuji. Verifikasi dengan sumber atau hash (mis. VirusTotal) sebelum menyimpulkan. Laporan berisi analisis berkas pribadimu, jadi jangan masukkan `rea-reports/` ke repositori.

Batas: tidak ada dekompilasi, emulasi, atau parsing resource DEX; deteksi XOR hanya satu byte pada 4 MB pertama; imphash varian Iris bisa berbeda dari `pefile`; konstanta kripto ikut memicu aturan "string ransomware + API kripto", jadi installer sah yang memakai AES bisa bernilai lebih tinggi; VBA terkompresi di OLE2 bisa menyembunyikan sebagian pola makro; arsip 7z dan RAR hanya dikenali jenisnya; file di atas 32 MB hanya dipindai bagian awalnya; sandbox tanpa jaringan membuat alat yang perlu unduhan gagal; seret-lepas ke overlay baru ada sejak v99 dan belum diuji di PC. RE Lab (v98) hanya untuk PE x86 / x64: penemuan fungsinya heuristik tanpa graf alir kontrol, fungsi yang hanya dipanggil lewat pointer atau vtable bisa terlewat, dan PE berkemasan (mis. UPX) memberi hasil minim karena kode aslinya belum terbuka. Status uji ada di [Status pengujian](#status-pengujian).

---

## Animasi klip VRMA

Selain gerak prosedural (napas, kedip, tatapan), Iris memutar klip `.vrma` dari folder `assets/animations/`. Daftar klip dan tag-nya dibaca dari `assets/animations/clips.json` saat overlay dimuat; `idle_loop.vrma` tetap menjadi animasi dasar.

**Klip yang ada** (durasi diukur dari berkas)

| Klip | Durasi | Menggerakkan | Tag emosi (`clips.json`) |
|---|---|---|---|
| `angguk` | 1,5 dtk | kepala, leher | `happy`, `neutral`, `idle` |
| `geleng` | 1,7 dtk | kepala, leher | `angry`, `sad` |
| `miring` | 2,2 dtk | kepala, leher | `surprised`, `shy`, `neutral`, `happy`, `idle` |
| `tunduk` | 2,6 dtk | kepala, punggung, dada | `sad`, `shy`, `neutral`, `idle` |
| `hormat` | 3,2 dtk | seluruh badan | `sad` |
| `melambai` | 3,6 dtk | badan atas, lengan | `happy` |
| `tari_ceria` | 9 dtk | seluruh badan | kosong (hanya lewat frasa, timer, sentuhan) |
| `dagu` | 10 dtk | badan atas, lengan | kosong (pose berpikir) |
| `duduk_iris` | 17 dtk | seluruh badan, kaki | kosong, tidak pernah acak; belum terhubung ke `/duduk` |

**Kapan klip diputar**

- **Saat kalimat mulai diucapkan.** Frasa dicek dulu (contoh: "halo" → `melambai`, "maaf" → `hormat`, "terima kasih" → `tunduk`, "hore" atau "berhasil" → `tari_ceria`, "jangan" atau "salah" → `geleng`, "iya" atau "oke" → `angguk`, "mungkin" atau "sebentar ya" → `dagu`, beserta padanan Jepangnya). Bila tidak ada frasa yang cocok, gerbang emosi memilih klip yang tagnya sama dengan emosi kalimat; peluang bergerak per kalimat 0,8 (netral) sampai 1 (kaget). Kalimat galat tidak memicu klip.
- **Saat diam.** Klip bertag `idle` diputar tiap 4 sampai 10 detik. Butuh saklar **Gerakan acak** di Pengaturan menyala.
- **Interaksi.** Sentuh kepala atau badan (`miring`, `tunduk`), sentuh lengan (`angguk`, `miring`), sentuh tangan (`melambai`, `angguk`), klik acak pada karakter, timer selesai (`tari_ceria`), tugas agen mulai (`dagu`), dan sapaan saat Iris muncul (`melambai`).
- **Jeda.** Minimal 1,5 detik antar klip, dan klip bertanda `big` paling cepat tiap 20 detik. Klip yang sama tidak diulang berturut-turut. Klip yang sedang jalan tidak disela.

**Format `clips.json`**

```json
{
 "angguk": { "file": "angguk.vrma", "emo": ["happy", "neutral", "idle"], "big": false, "speed": 1, "fi": 0.35, "fo": 0.45 }
}
```

| Kunci | Arti |
|---|---|
| `file` | nama berkas di `assets/animations/` |
| `emo` | emosi yang boleh memicunya: `happy`, `sad`, `angry`, `surprised`, `shy`, `neutral`, dan `idle` (gerak saat diam). Emosi tambahan ikut induknya: `tease`, `smug`, `excited` → `happy`; `worried` → `sad`; `confused` → `surprised`; `sleepy` → `neutral`. Kosong = hanya lewat frasa, sentuhan, atau `playClip('nama')` |
| `big` | klip besar, dibatasi jedanya (20 detik) |
| `speed` | kecepatan putar |
| `fi`, `fo` | detik masuk dan keluar (crossfade) |
| `auto` | opsional: `false` mematikan tag otomatis, `true` menggabungkan tag otomatis dengan `emo` |

Aturan tag: entri yang sudah punya `emo` dipakai **apa adanya**. Entri tanpa `emo` (atau dengan `"auto": true`) memakai tag otomatis berdasarkan nama berkas (daftar `CLIP_AUTO` di `index.html`). Berkas bernama `angguk`, `dagu`, `geleng`, `hormat`, `melambai`, `miring`, `tari_ceria`, atau `tunduk` yang belum ada di `clips.json` ikut dimuat otomatis (matikan dengan `CLIP_DISCOVER = false`). `duduk_iris` dan `idle_loop` tidak pernah masuk pilihan acak. Nama yang dipakai kode punya alias: `mikir` → `dagu`, `greet` → `melambai`, `cheer` → `tari_ceria`.

**Menyetel di `index.html`:** `GATE` (peluang dan jeda), `IDLE_MIN` dan `IDLE_VAR` (jeda idle), `PHRASES` dan `PHRASE_CFG` (frasa pemicu), `TOUCH_CLIP` (klip untuk sentuhan). Uji di konsol (`Ctrl+Alt+D`): `clips()` daftar klip yang termuat, `playClip('tari_ceria')`, `phraseTest('hore')`. Saat dimuat, konsol mencetak "Klip VRMA aksi siap" beserta tag tiap klip, dan menyebut berkas yang gagal dimuat.

> **Catatan.** Entri di `clips.json` yang berkasnya tidak ada tetap dicoba dimuat dan mencatat galat 404 di konsol; hapus entrinya. Perubahan 11 November 2026 lolos `node --check` dan belum diuji di overlay.

---

## Mini-browser `/chrome`

Panel browser kecil di samping karakter dengan **sepuluh slot akun** yang masing-masing punya sesi login terpisah. Panel berjalan di proses terpisah dan tanpa akses ke fungsi Electron.

| Perintah | Fungsi |
|---|---|
| `/chrome 1` sampai `/chrome 10` | Ganti ke akun nomor itu dan buka link awalnya |
| `/chrome` | Buka akun terakhir |
| `/chrome <nama>` | Sama, memakai nama akun |
| `/chrome 3 https://situs.com` | Akun 3 dengan alamat lain |
| `/chrome sembunyi` | Sembunyikan panel, tab tiap akun tetap hidup (juga `Ctrl+Alt+W` dan tombol ➖) |
| `/chrome tutup` | Tutup panel dan buang semua tab (hemat RAM) |
| `/chrome reset` | Buang semua tab; semua pil kembali ke link awal (login tetap tersimpan) |
| `/chrome besar`, `kecil`, `ukuran` | Ukuran panel (besar = 640x720; `ukuran` bolak-balik). Ukuran bebas: tahan tombol ⤡ di pojok panel lalu geser |
| `/chrome ke <alamat\|kata>` | Buka alamat di panel yang terbuka (kata biasa = cari di Google) |
| `/chrome <alamat>` | Buka alamat itu di akun terakhir |
| `/chrome daftar` atau `/akun` | Tampilkan semua slot |
| `/chrome mundur`, `maju`, `muat`, `beranda` | Navigasi (juga `Alt+←`, `Alt+→`, `F5`) |
| `/chrome ram` | RAM dan CPU renderer panel, GPU, dan total proses |
| `/chrome elemen` | Daftar elemen yang terlihat (uji jembatan baca-saja) |
| `/chrome jembatan` | Status jembatan baca-saja |
| `/akun nama <nomor\|nama> <nama baru>` | Ganti nama akun (login tetap tersimpan) |
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

Hermes Agent berjalan di WSL2 dan menjadi "tangan" Iris lewat `/agen`.

| Area | Kemampuan |
|---|---|
| Terminal dan sistem | Perintah bash di WSL dan PowerShell di Windows, proses latar, cron |
| File dan disk | Baca, tulis, cari isi file, analisis penggunaan disk |
| Kode | Menulis dan menyunting kode, menjalankan build dan tes, operasi git |
| Browser | Mengendalikan Chrome lewat Chrome DevTools Protocol |
| Web dan riset | Pencarian web (backend Exa), ekstraksi halaman, pencarian paper di ArXiv, riset multi-sudut |
| Dokumen dan media | PDF, Word, Excel, PowerPoint, transkrip YouTube, analisis gambar |
| Data | SQLite, JSON, CSV, Airtable |
| Integrasi | Telegram, Notion, Google Workspace |
| Skill kustom (40+) | Mis. `deep-research`, `academic-writer`, `excalidraw`, `oss-forensics`, `laptop-storage-analyzer`, dan `isi-form-otomatis`; dimuat per tugas |

Laporan Hermes ditampilkan apa adanya di kartu "Hasil tugas". Iris menyampaikannya secara netral dan bersumber, dan hanya menyatakan berhasil bila laporan Hermes jelas menyatakannya.

> **Catatan Hermes di Docker.** Setelah `systemctl --user restart hermes-gateway`, tunggu `http://127.0.0.1:8642/health` menjawab (bisa puluhan detik) sebelum mengirim `/agen`; tugas yang terlalu cepat gagal dengan "Hermes tidak aktif" atau `runtime_draining`. Kontainer dibuat saat tugas pertama dan bisa berhenti sendiri setelah jeda (bawaan 300 detik; satu pengamatan 10 November 2026 menunjukkan kontainer masih hidup setelah 31 menit, jadi jangan mengandalkan angka ini). **Setelah mengubah `docker_volumes`, restart gateway lalu hapus kontainer lama** (`docker ps`, lalu `docker rm -f <nama>`): mount baru tidak berlaku untuk kontainer yang sudah ada.

> **Tombol Stop.** Dengan `HERMES_STREAM=1`, Iris memanggil `POST /v1/runs/{id}/stop` di Hermes sebelum menutup koneksi. Diuji 7 November 2026: Hermes menjawab HTTP 200 `stopping`, status tugas `cancelled`, dan file baru berhenti terbentuk. Berhentinya tidak seketika (satu langkah yang sedang berjalan bisa selesai dulu), dan kegagalan memanggil stop hanya dicatat di terminal tanpa mengganggu pembatalan di sisi Iris. Dengan `HERMES_STREAM=0` (bawaan), Stop hanya memutus koneksi dan agen di Hermes tetap berjalan (terukur 7 November 2026). Periksa dengan [`scripts/cek-stop-hermes.py`](scripts/cek-stop-hermes.py), atau ukur perilaku tanpa stop dengan [`scripts/cek-cancel-hermes.py`](scripts/cek-cancel-hermes.py) (jalankan dari folder proyek, mis. `.\.venv\Scripts\python.exe scripts\cek-stop-hermes.py`; `cek-cancel-hermes.py` punya opsi `--skip-health`).

---

## Keamanan

IRIS berjalan lokal dan memberi agen akses ke komputermu, jadi pengamannya berlapis. Prinsipnya: **jangan mengandalkan satu pagar saja**. Kartu konfirmasi dan detektor berbasis pola punya celah, karena itu terminal agen dikurung di sandbox.

### Akses dan autentikasi

- Server hanya mendengar di `127.0.0.1`.
- **`COMPANION_TOKEN` wajib** (minimal 16 karakter). Koneksi `/ws` dilindungi token lewat header `X-Iris-Token` (kode penolakan 1008) plus pengecekan `Origin`. Server menolak start bila token kosong atau terlalu pendek; satu-satunya pengecualian adalah `COMPANION_ALLOW_NO_TOKEN=1` untuk pengembangan. Karena agen bisa menjalankan perintah di komputermu, jangan pakai pengecualian itu untuk pemakaian sehari-hari.
- Kunci API dan token tidak pernah ditulis di dokumen atau chat; bila ada yang bocor, ganti dan restart layanan terkait. Jangan beri `sudo` tanpa password di WSL.
- Log terminal hanya mencatat panjang dan sidik token, bukan isinya, dan URL dipotong sampai path. Endpoint `/health` tidak bertoken, jadi hanya menampilkan `ws_token` sebagai "aktif" atau "KOSONG".
- **Pengerasan server v102 (audit keamanan).** (1) Penjaga header `Host` melawan DNS rebinding: halaman web luar yang mengarahkan domainnya ke `127.0.0.1` tidak lagi menjangkau `/health` dan `/ws`. (2) Tanpa `COMPANION_TOKEN`, koneksi ditolak kecuali `COMPANION_ALLOW_NO_TOKEN=1`; dulu pemeriksaan ini hanya ada di `__main__`, sehingga `uvicorn server:app` melewatinya. (3) `/health` tanpa token yang benar hanya memberi status ringkas, di-cache 3 detik. (4) Kartu izin Hermes tidak lagi memotong perintah (pemotongan bisa menyembunyikan ekor perintah berbahaya); perintah lebih panjang dari `AGENT_APPROVAL_CMD_MAX` ditolak, dan karakter kontrol serta pembalik arah teks diganti penanda terlihat. (5) Path sandbox dinormalisasi sebelum dibandingkan, dan folder `rea-input` atau tujuan salinan yang berupa symlink atau junction ditolak. (6) Catatan hasil agen yang memuat kata rahasia tidak ditulis ke `iris-history.json`, dan izin berkasnya dibatasi. (7) Catatan tugas lama dan teks OCR layar yang dikirim ke Hermes dibungkus penanda data tidak tepercaya. (8) JSON rusak di `/ws` tidak mematikan koneksi, ukuran audio STT dicek sebelum didekode, dan kata pemicu konfirmasi `/agen` dinormalisasi NFKC. Belum dites di PC.

### Kendali tindakan agen

- **Konfirmasi tugas berbahaya.** Perintah `/agen` yang berpotensi berbahaya (hapus, pindah, timpa, format file) meminta konfirmasi dulu; daftar kata pemicu bisa disetel, `/health` menampilkan `agent_confirm`, dan konfirmasi sekali pakai kedaluwarsa dalam 120 detik. Batasnya: pemeriksaan ini hanya membaca teks permintaanmu, bukan tindakan yang dipilih agen, jadi ini jaring pengaman untuk salah ketik dan salah paham.
- **Persetujuan tindakan agen.** Perintah yang ditandai Hermes menunggu klik **Izinkan sekali** atau **Tolak** di overlay. Sistemnya gagal-aman (tanpa jawaban = tolak), hanya `once` dan `deny` yang pernah dikirim ke Hermes, dan mode persetujuan Hermes diset `manual`. Detektor Hermes berbasis pola dan punya celah: pada uji 9 November 2026, `rm` dengan path berkutip lolos tanpa kartu.
- **Izin otomatis baca-saja (v99.1, opt-in, bawaan mati).** Dengan `AGENT_APPROVAL_AUTO=readonly`, `approval_policy.py` memeriksa perintah yang diminta Hermes dan hanya meloloskan yang *terbukti* membaca; apa pun yang tidak bisa dibuktikan tetap tampil sebagai kartu Izinkan / Tolak (gagal-aman). Pemeriksaannya statis: bentuk shell sederhana (`|`, `||`, `&&`, `2>&1`; tanpa `;`, `&`, backtick, `$(...)`, pengalihan keluaran), tiap segmen harus `cd` di dalam sandbox, alat baca saja (`objdump`, `strings`, `file`, `sha256sum`, `hexdump`, `head`, `tail`, `grep`, `cat`, `ls`, dan sejenisnya), atau Python (`-c` atau heredoc) yang lolos pemeriksaan AST: impor dari daftar putih (mis. `struct`, `re`, `hashlib`, `pefile`), `open()` hanya mode baca dengan path literal, tanpa `exec`/`eval`/`getattr`/atribut dunder, tanpa `os`/`subprocess`/`socket`. Menulis hanya ke `/tmp` lewat `dd`, `cp`, dan `mkdir`. **Batas:** ini mengurangi risiko, bukan menghapusnya, karena pemeriksaan statis tidak bisa menjamin 100%; itu sebabnya bawaannya mati. Bila `approval_policy.py` tidak ada, server mencetak peringatan dan semua izin tetap lewat kartu. **v102.1 (22 November 2026):** ditemukan dan ditutup celah yang meloloskan akses atribut dunder lewat string (mis. `operator.attrgetter('__class__')`) dan `sys._getframe()`; modul `operator` kini tidak ada di daftar impor, atribut berawalan satu garis bawah ditolak, dan string literal yang memuat `__` ditolak. Belum dites di PC.
- **Sandbox Docker** (8 November 2026). Terminal agen berjalan di kontainer; yang bisa ditulis hanya folder kerja (bawaan satu folder) dan home sandbox, sedangkan drive dan folder lain tidak terlihat. Dengan `HERMES_SANDBOX=1`, Iris menolak tugas dengan path di luar sandbox. Jaringan kontainer dimatikan (`docker_network: false`; terbukti 8 November 2026: `network=none`, DNS gagal dari dalam kontainer), jadi isi folder kerja tidak bisa dikirim keluar lewat terminal agen.
  - **Batas:** agen tetap bisa menghapus atau mengubah isi folder kerjanya, dan alat web bawaan Hermes berjalan di luar kontainer sehingga masih bisa membuka situs.
  - **Menambah folder kerja melonggarkan kurungan.** Contoh: Downloads dipasang sebagai volume kedua di `docker_volumes` (10 November 2026): mount aktif dan baca terbukti, tetapi penghapusan di sana belum terbukti melewati kartu persetujuan (belum diuji dengan nama berspasi). Bila perlu, pasang subfolder khusus alih-alih seluruh Downloads, hindari wildcard, dan cek hasilnya dengan `dir`. Folder tambahan belum dipetakan di Iris, jadi `/agen` di overlay tetap menolak path-nya; gunakan Hermes langsung (mis. lewat Telegram) dengan path kontainer.
- **Laporan agen tidak selalu benar.** Agen pernah melaporkan "berhasil dihapus" padahal tidak ada tindakan sama sekali. Cek dengan `dir` atau `ls`; Iris menambah `[Verifikasi Iris]` hanya untuk path di folder kerja agen.

### Isi tidak tepercaya (injeksi prompt)

- **Isi web.** Halaman diperlakukan sebagai data, bukan perintah (aturan di prompt agen dan pembersih di `iris_web.py`). Perlindungan ini bergantung pada kepatuhan model dan baru lulus 2 uji, jadi jangan menganggapnya pagar teknis.
- **`/rea`.** Isi file diperlakukan sebagai data tidak tepercaya. Audit kode 10 November 2026 menemukan dan menutup tujuh celah di jalur ini: ReDoS di triase, injeksi prompt lewat string sampel, catatan riwayat yang memuat string sampel, keluaran laporan tanpa sanitasi, junction Windows pada pengemasan folder, peringatan overlay palsu pada file bertanda tangan, dan triase yang terlewat saat sandbox mati. Perlindungan dari injeksi belum diuji dengan sampel injeksi di PC asli.
- **Pembersihan `iris_web.py`** (12 November 2026; diperluas di v101, 19 November 2026) mencakup semua kolom teks tingkat atas (`title`, `url`, `host`, `account`, dan kolom lain) pada semua jenis respons, termasuk `shot`. Elemen halaman dibangun ulang hanya dari kunci yang diizinkan (`n`, `tag`, `text`, `type`, `href`, `name`, `password`, `x`, `y`); kunci lain dibuang dan `href` ikut dipindai. Daftar elemen dibingkai `elements_begin` / `elements_end` bernonce. Klien membatasi ukuran balasan (30 MB) dan tidak mengikuti pengalihan HTTP. Daftar pola injeksi ditambah (lupakan instruksi, instruksi baru, minta dirahasiakan dari pengguna, blob base64 panjang). Batasnya: pembersihan hanya ada di klien, jadi agen yang memanggil jembatan langsung (mis. `curl` dengan token) melewatinya, dan pemindaian pola hanyalah heuristik. Lolos uji kecil di sandbox, belum dites di PC.

### Isolasi dan privasi

- Semua jendela menolak navigasi, jendela baru, dan `<webview>`. DevTools tidak tersedia di versi rilis.
- Panel mini-browser berjalan terisolasi (sandbox, tanpa preload, tanpa akses kamera, mikrofon, atau notifikasi, navigasi hanya ke `https://`).
- Jembatan baca-saja mati secara bawaan dan berlapis (lihat [bagiannya](#jembatan-baca-saja-untuk-hermes)).
- Fitur yang menyentuh privasi (duduk di jendela lain) **mati secara bawaan**.
- Memori dan riwayat menolak menyimpan isi yang mirip rahasia (kata sandi, token, `sk-...`, dan angka 13 sampai 19 digit seperti nomor kartu atau NIK). Sejak v91 angka yang lebih pendek (tanggal seperti `12-03-2001`, nomor HP 12 digit) tidak lagi ditolak, jadi nomor HP bisa tersimpan di memori kalau kamu menyuruhnya.
- **Daftar putih `app://` (v91, 19 November 2026).** Halaman overlay hanya boleh membaca `/index.html`, `/favicon.ico`, isi `/assets/`, serta `/node_modules/three/` dan `/node_modules/@pixiv/`. `.env`, `server.py`, `iris-history.json`, `iris-memory.json`, dan berkas lain di folder proyek dijawab 403; segmen berawalan titik atau bertanda `:` juga ditolak, dan percobaan `..`, `%2e%2e`, serta `%2F` diuji ditolak. Berkas sah yang ikut tertolak dicetak sekali per path di terminal Electron (`app:// ditolak (di luar daftar putih)`). Baru diuji dengan harness terpisah, belum di PC.
- **Jendela tempelan terjemahan (v99)** tanpa preload, tanpa jaringan (CSP hanya gambar `data:`), hanya menerima gambar PNG atau JPEG berbasis `data:` dari overlay lewat IPC yang memeriksa pengirimnya, dan tetap di dalam satu layar.
- **Pengerasan v101 (19 November 2026).** (1) IPC yang menyentuh clipboard, berkas, atau program (`read-clipboard`, `copy-image`, `open-image`, `save-html`, `save-config`, `reveal-file`, `local-cmd`) kini menolak pemanggil selain jendela overlay. (2) Izin `media` hanya untuk mikrofon: permintaan video (kamera) ditolak. (3) Jendela pilih area, tempelan terjemahan, dan penampil gambar memakai sesi terpisah `iris-aux` yang menolak semua izin dan tidak ikut disuntiki `X-Iris-Token`. (4) Nama berkas ekspor tidak boleh nama perangkat Windows (`CON`, `NUL`, `COM1`, dst.) atau berakhir titik / spasi, ekspor dibatasi 50 MB, dan penulisan memakai flag `wx` sehingga tidak pernah menimpa berkas yang ada. (5) `reveal-file` membandingkan folder tanpa membedakan huruf besar / kecil di Windows. (6) Sisa berkas penampil gambar di folder `iris-view` yang lebih tua dari satu jam dibersihkan saat start. (7) Terjemah layar menolak gambar di atas `IRIS_TL_MAX_PIXELS` sebelum memuatnya. (8) `server.py` mencetak peringatan bila `COMPANION_HOST` bukan loopback. Belum dites di PC.
- Berkas sensitif tidak pernah masuk repositori: `.env`, riwayat percakapan, memori, log, arsip, dan folder `vv-engine/` dikecualikan lewat `.gitignore`.

### Yang perlu kamu jaga sendiri

- Riwayat obrolan dan memori tersimpan polos di disk. Jangan taruh folder proyek di drive yang tersinkron ke cloud.
- Log server memuat teks chat, jadi jangan dibagikan sembarangan.

**Melaporkan celah keamanan:** mohon jangan buka issue publik; hubungi pemilik repositori secara langsung.

---

## Status pengujian

Legenda: **Lulus** = dicoba dan berfungsi di PC pengembang · **Sebagian** = ada bukti, tetapi ada bagian yang belum terbukti · **Belum diuji** = ditulis dan lolos pemeriksaan sintaks atau uji di lingkungan penulis kode, belum dicoba di overlay. Fitur bertanda **Belum diuji** sebaiknya dianggap eksperimental.

### Belum lulus uji penuh

| Area | Status | Catatan |
|---|---|---|
| Terjemah layar (OCR): Jepang, Inggris, Auto, suara, pratinjau besar, tombol berhenti | Sebagian | Jepang terbukti membaik lewat screenshot nyata (8 November 2026): 42 dari 62 blok diterjemahkan tanpa teks sampah "0000"; paragraf pembuka besar masih Jepang dan ada potongan yang menumpuk. Pil bahasa di menu lulus. Mode Inggris dan Auto baru diuji dengan OCR dan model palsu; suara pembuka dan penutup, penampil besar, tombol berhenti, font Jepang, dan penyaring sampah belum dilaporkan dari overlay. Teks merah, tebal, dan tombol kecil masih terlewat |
| Jawaban Iris soal isi terjemahan (tidak boleh mengarang) | Belum diuji | Belum terbukti dengan model sungguhan; pernah mengarang isi halaman |
| `/rangkum`: bacaan halaman dan injeksi (v81) | Sebagian | Lulus di overlay. Hanya teks DOM utama yang terbaca (PDF viewer, iframe, dan konten malas tidak); perilaku model terhadap injeksi di halaman belum terbukti |
| Tombol putar suara pada ucapan otomatis (v89) | Belum diuji | Uji: `/sapa sekarang`, `/funfact`, `/jam`, buka chat, lalu klik ikon speaker di kotaknya |
| Mini-browser fase 4 (pil akun, hemat RAM, tab diparkir) | Belum diuji | Belum dites di Electron asli |
| Jembatan baca-saja untuk Hermes | Belum diuji | Kode ada; belum ada skill Hermes yang memakainya |
| Tugas `/agen` ringan terasa lambat | Terbuka | Penyebab belum dipastikan |
| Bubble dengan lampiran dekat tepi atas layar | Belum diuji | |
| `/rea` v82 dan v83 (bedah satu file lewat Hermes, hasil kartu mentah) | Sebagian | Alur ujung ke ujung berjalan di overlay (10 November 2026): laporan keluar sekitar 4,5 menit untuk file 496 KB, penyebab lambat belum diketahui. Laporan agen memuat klaim yang saling bertentangan, jadi anggap petunjuk. Kartu mentah (v83) belum diuji di server asli |
| `/rea` v91 sampai v93 (triase lokal, mode `cepat` / standar / `dalam`, folder, laporan penuh, carve, draf YARA) | Belum diuji | Lolos `py_compile`, `node --check`, dan tes fungsi di lingkungan penulis kode. Belum diuji di overlay dengan Hermes asli; tampilan kartu 9000 karakter, kecepatan `/rea cepat` pada file besar, dan pengiriman `/rea cepat <folder>` dari `index.html` belum diverifikasi |
| `/rea` v94 (ReDoS dan injeksi prompt ditutup; impor ELF, PDF, OLE2, RTF, LNK, skrip, delay-import, overlay, checksum PE, konstanta kripto, ATT&CK) | Belum diuji | Lolos uji sandbox: ReDoS lama vs baru diukur (file 3 MB: macet lebih dari 120 detik jadi 0,8 detik), sampel sintetis, PE asli, ELF `/bin/ls`, `--json` valid, folder dengan symlink loop. `server.py` baru diimpor dengan stub. Belum diuji di PC dengan Hermes; parsing delay-import belum bertemu sampel nyata; skor tetap petunjuk, bukan vonis |
| `/rea` v95 sampai v97 (`rea_extract.py`, `rea_binary.py`, penguatan triase) | Belum diuji | Sintaks dan uji asap lulus di lingkungan penulis kode; `rea_extract.py` dan `rea_binary.py` belum diperiksa. Penomoran v95 sampai v97 di kode berbeda dari spesifikasi REA |
| `/rea` v98 "RE Lab" (peta panggilan API per fungsi, xref string, anti-analisis, API hashing, stack string; hanya PE x86 / x64) | Belum diuji | Lolos `py_compile` dan uji sandbox di lingkungan penulis kode: 4 PE asli (251 sampai 302 fungsi, skor tetap rendah) dan PE sintetis (rantai injeksi, syscall langsung, API hashing, dan stack string terdeteksi). Belum diuji di overlay dengan Hermes asli, belum pada malware nyata, dan tanpa korpus regresi. Jalur `capstone` untuk `--disasm` baru dijalankan sekali pada PE asli (`w64.exe`) di lingkungan penulis kode pada 19 November 2026. Sambungan ke `/rea` ada sejak v99 (baris di bawah); dampak baris RE Lab pada batas `REA_MAX_CHARS` belum diukur |
| `/rea xref` dan `/rea disasm` (v99) serta seret-lepas file ke overlay | Belum diuji | Lolos `py_compile` dan `node --check`. Di lingkungan penulis kode: `rea_api` xref dan disasm pada PE asli (`w64.exe`, jalur hex dan jalur `capstone`), `handle_agent_task` dijalankan dengan stub (hasil jadi kartu, catatan riwayat tanpa isi sampel, path UNC, file tidak ada, dan argumen salah ditolak tanpa sampai ke Hermes), serta pengurai perintah di `index.html` dengan stub. Belum diuji di overlay, belum di Windows dengan path nyata, dan jendela yang tembus-klik belum terbukti menerima seretan |
| Terjemah layar pilih area (v90), area kecil diperbesar, terjemahan menempel, dan ulangi area terakhir (v99) | Belum diuji | Lolos `node --check`. Rumus perbesaran, filter gambar tempelan, dan alur `/terjemah ulang`, `tutup`, `tempel`, serta jalur gagal-tempel ke penampil besar diuji dengan stub; jendela pilih area, jendela tempelan, `Ctrl+Alt+Y`, ketepatan posisi di layar berskala DPI lain atau banyak monitor, dan hasil OCR pada area yang diperbesar belum diuji di Electron asli |
| Perbaikan 13 November (v91): daftar putih `app://`, `_SECRET_RE`, regex fakta game, CSS chip | Belum diuji | Lolos `node --check`, `ast.parse`, dan harness terpisah untuk daftar putih dan kedua regex. Belum dijalankan di PC; bila ada berkas sah yang tertolak, terminal Electron mencetak barisnya. Fakta game yang sudah salah di `iris-history.json` tidak dibersihkan otomatis: hapus kunci `facts` di berkas itu |
| Pengerasan dan perbaikan v101 (19 November 2026): pemeriksaan pengirim IPC, mikrofon saja, sesi `iris-aux`, nama berkas aman, `iris_web.py` (`shot`, allowlist elemen, batas balasan), batas piksel terjemah layar, tebakan negatif dan deteksi bocor jawaban di `/tekateki`, peringatan `COMPANION_HOST` | Belum diuji | Lolos `node --check` dan `ast.parse`. Di sandbox lulus: `harden()` (kolom `shot`, allowlist elemen, nonce, href `javascript:`), `cocok()` (`bukan api`, `ga mungkin api`, `api atau air`, `tidak api`, `not api` ditolak; `api`, `koin logam`, `coin` tetap benar), `parse_teka()` ("Kecil tapi bisa membakar hutan" untuk `api` kini lolos, "sapunya" untuk `sapu` ditolak), dan `decode_data_url()` (gambar 49 juta piksel ditolak). Belum dites di PC: mikrofon tetap berfungsi, ekspor percakapan dan konfigurasi, jendela pilih area, tempelan, dan penampil gambar di sesi `iris-aux`, serta tombol salin / buka gambar |
| Folder kerja tambahan (Downloads) di sandbox | Sebagian | 10 November 2026: mount aktif (`RW: true`) dan baca terbukti lewat Telegram; hapus satu file umpan terlihat berhasil di Explorer, tetapi kartu persetujuan, `Test-Path`, uji Tolak, dan path berspasi belum dilaporkan |
| Perlindungan injeksi prompt | Sebagian | Lulus 2 uji (`curl` dan file lokal); belum dengan halaman web sungguhan |
| Persetujuan tindakan agen dan sandbox Docker | Sebagian | Izinkan sekali dan Tolak terbukti di Hermes sungguhan, satu uji per kasus (termasuk `rm` file tunggal, 8 November 2026). Tes otomatis memakai Hermes palsu (28 dan 26 tes lulus) |
| Tombol kartu izin aktif setelah 0,7 detik (cegah klik ganda) | Sebagian | Tolak dan Izinkan sekali berfungsi; efek jeda terhadap klik ganda belum terbukti dari log. Peringkasan hasil agen lebih tepat (v72) lulus 8 November 2026 |
| Backend Docker tanpa jaringan dan WSL `mirrored` | Sebagian | Terbukti 9 November 2026: hapus file di luar folder kerja tidak berefek, dan Iris kembali melaporkan VOICEVOX, 9Router, dan Hermes aktif. Satu uji per kasus; suara lewat terminal agen belum diuji |
| Klip VRMA lebih sering dipakai (11 November 2026) | Belum diuji | Lolos `node --check` dan pemeriksaan isi berkas `.vrma`. Belum dilihat di overlay: seberapa sering klip terasa pas, peralihan klip seluruh badan dari idle, dan klip yang bertumpuk dengan gerak prosedural |
| Game teka-teki `/tekateki` (12 November 2026) | Belum diuji | Di-push ke `main`; audit statis menunjukkan sambungan ke `server.py` dan `index.html` cocok. Belum dicoba di overlay (suara dan klip). Sejak v102.1 ada `tests/test_iris_games_isi_ulang.py` (5 tes isi ulang, riwayat, dan migrasi, lulus di sandbox); tes untuk `cocok()` dan `parse_teka()` belum ada |
| Perbaikan audit 12 November 2026 (Mode fokus `setQuiet`, pembersihan `iris_web.py`, `jp_speakable()`) | Belum diuji | Lolos uji statis dan uji kecil di sandbox. Belum dites di PC: keluar dari Mode fokus, jawaban panjang berbahasa Indonesia (cek log dan suara), dan `iris_web.py text` pada halaman berjudul pola injeksi |

### Sudah lulus

| Area | Bukti |
|---|---|
| Jembatan Hermes (termasuk path Windows di kartu hasil), konfirmasi `/agen` berbahaya, token `/ws` | Lulus di PC |
| Ganti baju, tema, fun fact, alarm dan jam, mood, seret file dan lampiran gambar, ekspor, pilihan bernomor, pil status koneksi | Lulus di PC |
| Peluncur, termasuk menutup peluncur dan menu Keluar yang mematikan semua layanan (`--stop-all`) | Dilaporkan pemilik berfungsi |
| Perbaikan v46 sampai v50 (UI tetap di layar, panel pindah sisi, rambut dan bayangan setengah badan) dan pikiran batin | Dilaporkan pemilik beres dan aman |
| VOICEVOX di GPU (DirectML) | 8 November 2026: GPU 720, 483, 601 ms lawan CPU 2939 (pemanasan), 1972, 2003, 1899 ms untuk kalimat sekitar 75 karakter, sekitar 3,6 kali lebih cepat; baris perintah mesin di port 50021 memuat `--use_gpu`. Batas: penghitung `GPU Engine` per proses tidak bisa jadi bukti di mesin ini, dan hanya satu kalimat yang diukur |
| Batas tunggu stop Hermes di peluncur | 8 November 2026: chip Hermes dimatikan (4 detik) dan dinyalakan lagi (12 detik) tanpa tampak gagal; batas stop systemd 75 detik |
| Status server di peluncur lewat `/ping` | 8 November 2026: chip server tetap Hidup saat Hermes dimatikan; `/ping` menjawab 2 sampai 15 ms (`/health` sekitar 2 detik saat ada layanan mati). Sisa kecil: log start masih menulis "menunggu /health" |
| Sambung ulang WebSocket bertahap (jeda 2, 4, 8, maksimal 15 detik) | Diuji 1 kali: server dimatikan sekitar 12 detik, overlay tersambung lagi dan riwayat dipulihkan |
| Ikon tray berwarna, ekspor/impor konfigurasi, tawaran aksi saat menyalin, `/statistik`, `/kana`, `/sapa`, bubble menghindari menu, reaksi Iris di riwayat chat | Lulus di overlay (8 November 2026 malam; sebagian dilaporkan pemilik tanpa tangkapan layar rinci) |
| Pesan Iris saat Tolak ditekan | 8 November 2026, model sungguhan: tidak lagi menyebut "gagal" |
| Bicara lewat mikrofon: penyetelan 6 November | Diuji dengan kalimat dari tangkapan layar; pemilik melaporkan tidak ada masalah. Akurasi tetap bergantung pada model dan mikrofon |
| Pembatalan tugas yang menghentikan agen Hermes, dan konversi path berspasi | 7 November 2026: HTTP 200 `stopping`, status `cancelled`; `tests/test_path_berspasi.py`, 13 dari 13 tes proyek lulus |

---

## Rencana

Ide yang sudah disetujui atau dicatat, **belum ada kodenya**.

**Dekat**

- Perluasan yang sudah dicatat: statistik fokus lebih rinci (jam fokus mingguan, `/timer` biasa ikut dihitung) dan kana lanjutan (tanda panjang ー dan っ kecil)
- `/rea`: pemetaan folder kerja tambahan (mis. Downloads) di `/agen` overlay (seret-lepas file ke overlay sudah ada sejak v99, belum diuji)
- REA v95 sampai v100: sebagian sudah ada kodenya dengan penomoran yang berbeda dari spesifikasi (v95 `rea_extract.py`, v96 `rea_binary.py`, v97 penguatan triase, v98 RE Lab untuk PE x86 / x64; lihat [Membedah file dengan `/rea`](#membedah-file-dengan-rea)). Belum dikerjakan: pengelola image PSP (baca, ekstrak, ganti file, rebuild ISO), parser arsip game berbasis plugin, dan penjelajah aset Unreal (PAK, IoStore). Format baru baru diberi label *Supported* setelah lulus fixture dan tes regresi; kunci enkripsi hanya dari pengguna yang berhak, tanpa bypass DRM
- RE Lab: perluasan ke ELF x86-64 (PLT dan xref string), deteksi loop dekripsi XOR / RC4, dan penamaan fungsi lewat tanda tangan pustaka umum
- Menghubungkan `duduk_iris.vrma` ke `/duduk`; menari mengikuti musik dan perintah `/nari` (klip `tari_ceria.vrma` sudah ada, yang belum ada deteksi musik dan perintahnya)

**Menengah**

- Skill Hermes `cek-elearning` dan skill yang memakai jembatan baca-saja; mini-browser fase 5b dan 5c (Hermes beraksi dengan konfirmasi dan batas domain)
- Memori otomatis ringan (ringkasan fakta baru yang kamu setujui dulu sebelum disimpan)
- Auto-start bersama Windows dan skrip setup untuk PC baru
- Angin dari kecepatan kursor (`/angin`), `/catat` dan `/todo`, jurnal mood harian, dan mode jangan ganggu otomatis saat game atau aplikasi layar penuh

**Menunggu keputusan atau ditunda**

- Terjemah langsung (subtitle) di area layar tertentu, reaksi ke suara sistem, pencarian file bahasa alami (butuh keputusan akses folder untuk agen), dan pengingat berbasis aplikasi aktif (bentrok dengan prinsip privasi)
- Pencarian catatan (`/cari`, `/indeks`): ditunda
- Alternatif TTS dan LLM selain VOICEVOX dan 9Router, wake word dan mode hands-free, serta dukungan Live2D, macOS, dan Linux

---

## Struktur proyek

```
.
├── main.js                  # proses utama Electron (jendela, tray, IPC)
├── preload.js               # jembatan aman antara renderer dan main
├── index.html               # tampilan overlay: avatar, bubble, input
├── server.py                # backend FastAPI + WebSocket
├── iris_web.py              # CLI untuk membaca panel mini-browser (dipakai agen)
├── iris_translate_img.py    # OCR dan penggambar terjemahan layar
├── rea_triage.py            # triase statis file untuk /rea, v99.1
├── rea_assets.py            # Asset Explorer: isi model 3D, tekstur, audio, arsip, SQLite untuk /rea (opsional, v99.0)
├── approval_policy.py       # izin otomatis khusus perintah baca-saja (opsional, bawaan mati, v99.1)
├── example_plugin.py        # contoh plugin parser untuk Asset Explorer (format DEMO)
├── rea_extract.py           # penjelajah container untuk /rea (opsional)
├── rea_binary.py            # hex view, compare, patch berundo untuk /rea (opsional)
├── iris_games.py            # game teka-teki /tekateki (opsional)
├── data/                    # tekateki.json (bank bawaan); tekateki_dinamis.json dan tekateki_state.json dibuat saat dipakai
├── rea-reports/             # laporan /rea (dibuat saat dipakai; jangan di-commit)
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
├── vv-engine/               # engine VOICEVOX (tidak ada di repositori, letakkan sendiri)
├── scripts/
│   ├── buat_klip_vrma.py    # skrip pembuat klip animasi VRMA
│   ├── cek-cancel-hermes.py # skrip ukur pembatalan tugas Hermes (tanpa stop)
│   └── cek-stop-hermes.py   # skrip uji tombol Stop menghentikan agen Hermes
├── dev/
│   └── test_client.html     # halaman tes koneksi (hanya untuk pengembangan, tanpa token)
├── tests/                   # tes otomatis (mis. test_path_berspasi.py, test_approval_gate.py, test_iris_games_isi_ulang.py)
└── docs/
    ├── QUICKSTART.md        # panduan mulai cepat
    └── img/                 # logo
```

---

## Aset

Aset (model VRM, animasi VRMA, suara) **tidak disertakan** dalam repositori karena ukuran dan lisensi. Letakkan sendiri di folder `assets/`:

```
assets/
├── iris.vrm                 # model utama
├── Iris_winter.vrm          # model baju (opsional)
└── animations/
    ├── idle_loop.vrma       # animasi idle dasar
    ├── clips.json           # daftar klip gerak dan tag emosi (opsional)
    ├── angguk.vrma, geleng.vrma, miring.vrma, tunduk.vrma           # klip kecil
    └── dagu.vrma, melambai.vrma, hormat.vrma, tari_ceria.vrma, duduk_iris.vrma   # klip seluruh badan
```

Klip gerak sederhana bisa dibuat sendiri dengan `python scripts\buat_klip_vrma.py` dari folder proyek; skrip ini menulis `.vrma` dan `clips.json` ke `assets/animations/`. Skrip itu dapat menimpa `clips.json`, jadi cadangkan dulu bila kamu sudah menyetel tag sendiri. Klip seluruh badan (`dagu`, `melambai`, `hormat`, `tari_ceria`, `duduk_iris`) bukan hasil skrip itu; pastikan kamu punya hak pakainya sebelum mempublikasikannya.

Pastikan kamu memiliki hak pakai atas model dan aset yang kamu gunakan.

---

## Pemecahan masalah

| Gejala | Kemungkinan penyebab dan solusi |
|---|---|
| Iris tidak bersuara, terminal penuh `VOICEVOX gagal` | VOICEVOX belum berjalan. Nyalakan lewat chip VOICEVOX di peluncur, atau jalankan `vv-engine\run.exe` sendiri di port 50021. Cek pemilik port: `Get-Process -Id (Get-NetTCPConnection -LocalPort 50021 -State Listen).OwningProcess` (`run` = mesin Windows, `wslrelay` = unit WSL yang aktif) |
| Balasan `401 Missing API key` | `NINEROUTER_API_KEY` kosong. Isi di `.env` lalu restart server |
| Server langsung berhenti dengan `[FATAL] COMPANION_TOKEN wajib diisi` | Isi `COMPANION_TOKEN` (minimal 16 karakter) di `.env`, lalu start ulang. Hanya untuk pengembangan: `COMPANION_ALLOW_NO_TOKEN=1` |
| Overlay tidak tersambung, log `/ws ditolak` | Token server dan overlay berbeda (mis. ada dua `.env` dengan token berbeda). Cek sidik token di terminal server dan terminal Electron, lalu restart keduanya |
| Halaman `127.0.0.1:8765` menampilkan "Server Iris aktif" saja | Normal bila `COMPANION_TOKEN` aktif. Gunakan overlay Electron |
| `/agen` membalas HTTP 503 atau tidak merespons | Pastikan API server Hermes aktif di `127.0.0.1:8642` dan `HERMES_API_KEY` sama dengan `API_SERVER_KEY` |
| File hasil agen "tidak ada" di Download | Hermes berjalan di WSL, jadi `~/Downloads` miliknya adalah folder Linux. Atur `HERMES_WIN_HOME` agar menunjuk ke folder Windows |
| Perubahan `.env` tidak terbaca | Server hanya membaca `.env` saat start. Restart server dan overlay |
| Karakter menghilang sesekali | Pemulihan WebGL otomatis dan watchdog sudah dipasang. Coba `/kualitas hemat`, lalu lihat terminal Electron (`Renderer mati`, `WebGL context hilang`) |
| Iris lag atau RAM penuh | `/kualitas hemat`, tutup tab browser yang tidak dipakai, dan cek batas memori WSL di `.wslconfig`. `/chrome ram` menampilkan pemakaian panel |
| Terjemah layar banyak teks tak ikut, atau muncul teks aneh | Pastikan paket bahasa OCR sumber terpasang, pilih bahasa manual di menu (bukan Auto), lalu jalankan dengan `IRIS_TL_DEBUG=1` dan lihat `iris_tl_debug.png`. Setelah mengganti `server.py` atau `iris_translate_img.py`, restart server (bukan hanya overlay) |
| Terjemah layar menjawab "Gambar tidak bisa dibaca" dengan keterangan piksel melebihi batas | Gambar lebih besar dari `IRIS_TL_MAX_PIXELS` (bawaan 40 juta piksel, kira-kira tiga layar 4K). Pilih area yang lebih kecil, atau naikkan nilainya di `.env` bila RAM cukup |
| Ekspor percakapan atau konfigurasi tersimpan dengan awalan `_` pada nama | Nama yang kamu beri sama dengan nama perangkat Windows (`CON`, `NUL`, `COM1`, dst.), jadi Iris menambahkan `_` di depannya (v101) |
| Model gambar timeout | Kurangi jumlah gambar yang dikirim atau naikkan `NINEROUTER_VISION_READ_TIMEOUT` |
| Tombol Salin gambar gagal | Restart Iris. Handler mencoba tiga cara berurutan, termasuk lewat PowerShell |
| Pintasan bisu tidak bekerja | Kombinasinya mungkin dipakai aplikasi lain. Terminal mencetak pintasan yang terdaftar; paksa sendiri lewat `IRIS_MUTE_KEY` |
| Menu Keluar hanya menutup overlay | Overlay tidak dijalankan lewat peluncur (mis. `npm start`), atau peluncurnya belum versi terbaru. Bangun ulang `IrisLauncher.exe` dan mulai dari peluncur |
| Whisper salah dengar nama atau perintah (mis. "agen" jadi "akun") | Naikkan `IRIS_STT_MODEL` (`small` atau `medium`), tambahkan kata itu ke `IRIS_STT_PROMPT`, dan dekatkan mikrofon. Lihat [Bicara lewat mikrofon](#bicara-lewat-mikrofon) |
| Peluncur gagal di langkah WSL | Jalankan `iris-doctor.ps1` dan lihat log di `iris-start.log` |
| Suara VOICEVOX lambat atau GPU tidak terpakai | Cek kotak **Mesin suara VOICEVOX** di Pengaturan peluncur, dan cari `DirectML (device_id=0): OK` di `iris-voicevox.err.log`. Bila unit `voicevox` di WSL masih aktif, matikan: `wsl -d Ubuntu -- systemctl --user disable --now voicevox` |
| Server baru langsung mati dengan `Errno 10048` | Server lama masih memegang port 8765. Cek `Get-NetTCPConnection -LocalPort 8765 -State Listen`, matikan prosesnya (atau lewat peluncur), lalu start ulang |
| Agen melapor "berhasil" tetapi file atau folder tidak berubah | Laporan agen tidak selalu benar, dan di sandbox path di luar folder kerja tidak terjangkau. Cek langsung dengan `dir`, dan kirim path penuh pada `/agen` |
| `/agen` ditolak dengan pesan path di luar sandbox | `HERMES_SANDBOX=1` aktif: hanya folder kerja bawaan agen yang bisa disentuh lewat `/agen`. Letakkan berkasnya di sana (atau pakai `/rea`, yang menyalinnya otomatis), atau matikan sandbox sadar akan risikonya. Folder tambahan di `docker_volumes` Hermes belum dipetakan di Iris |
| Iris melapor VOICEVOX, 9Router, atau Hermes "offline" padahal hidup | Dua penyebab yang pernah terbukti (9 November 2026): WSL mode NAT tidak menjangkau `localhost` Windows (atur `networkingMode=mirrored` di `.wslconfig`, lalu `wsl --shutdown`), dan cek status lewat `curl` dari terminal agen di sandbox tanpa jaringan selalu gagal (`000`). Lihat status lewat pil V 9 H atau `/status`, bukan dari terminal agen |
| `/rea` lambat atau menolak | Mode standar dan `dalam` memakai Hermes dan bisa memakan beberapa menit; pakai `/rea cepat` untuk triase tanpa Hermes. Penyalinan hanya jalan bila `HERMES_SANDBOX=1`; folder kosong, terlalu besar, atau path jaringan (UNC) ditolak dengan pesan jelas. Tanpa `rea_triage.py` di folder `server.py`, triase mati dan mode `cepat` ditolak. Windows Defender memberi peringatan setelah `/rea`: kemungkinan `REA_CARVE=1` mengekstrak payload tertanam ke `rea-input\carved`; matikan atau hapus folder itu |
| Tugas agen menggantung tanpa kartu izin | Pastikan `HERMES_STREAM=1` dan `approvals.mode` Hermes `manual`; restart server dan buka ulang overlay |
| Stop tidak menghentikan agen Hermes | Pastikan `HERMES_STREAM=1` di `.env`, restart server, dan buka ulang overlay. Satu langkah yang sedang berjalan bisa selesai dulu. Me-restart `hermes-gateway` di tengah tugas memunculkan "Server disconnected"; itu bukan hasil tombol Stop |
| Chip Hermes tampak gagal mati | Hermes bisa butuh sampai sekitar 70 detik untuk berhenti; peluncur menunggu 75 detik. Kalau tetap tampak gagal, cek `systemctl --user status hermes-gateway` di WSL. Peluncur lama (sebelum build ulang 8 November) hanya menunggu sekitar 12 detik, jadi bangun ulang `IrisLauncher.exe` |
| Chip server.py tampak Mati padahal server jalan, atau server tidak bisa dinyalakan saat Hermes mati | Peluncur lama menilai server lewat `/health`, yang melambat saat Hermes mati. Perbarui `server.py`, bangun ulang `IrisLauncher.exe` (peluncur kini memakai `/ping`), lalu cek `http://127.0.0.1:8765/ping`. Bila masih salah, lihat di Task Manager apakah `python.exe` benar-benar hilang |
| Klip gerak jarang main, atau konsol penuh galat 404 klip | Cek saklar **Gerakan acak** di Pengaturan (mati = tanpa klip acak). Hapus entri `clips.json` yang berkasnya tidak ada. Lihat baris "Klip VRMA aksi siap" di konsol untuk klip dan tag yang benar-benar termuat; `idle` hanya ada di klip yang bertag itu. Lihat [Animasi klip VRMA](#animasi-klip-vrma) |

Untuk diagnosis lebih lanjut, jalankan overlay dengan `npm start`, buka DevTools dengan `Ctrl+Alt+D`, dan cek tab Console (DevTools tidak tersedia di versi rilis).

---

## Dokumentasi

- [`docs/QUICKSTART.md`](docs/QUICKSTART.md): panduan mulai cepat dari nol sampai Iris menjawab

---

## Riwayat pembaruan

| Tanggal | Perubahan |
|---|---|
| **22 November 2026 (v102.1)** | `iris_games.py`: pemicu isi ulang dan pemilihan teka-teki kini memakai daftar `dimainkan` (semua id yang pernah muncul), bukan jendela `riwayat` 30 id, sehingga pembuatan otomatis tidak lagi macet pada bank lebih dari 32 teka-teki; berkas simpanan lama dimigrasi. Tes baru `tests/test_iris_games_isi_ulang.py` (5 tes; versi lama gagal semuanya). `approval_policy.py`: celah dunder-lewat-string (`operator.attrgetter`, `sys._getframe`, `str.format` berisi `__`) ditutup. Lulus uji di sandbox, belum dites di PC |
| **20 November 2026** | Sinkron dengan kode yang diunggah. `rea_triage.py` v99.1 (gabungan v98.6 dan v99.0, semua tambahan aditif) dan berkas baru `rea_assets.py` (v99.0, Asset Explorer: isi model 3D, animasi, tekstur, audio, arsip, SQLite, dan carving); `approval_policy.py` (v99.1, izin otomatis baca-saja, opt-in, bawaan mati) dan `example_plugin.py` (contoh plugin parser). `server.py` v99.2 dan v99.3 (ringkasan analisis Hermes ikut ke catatan Iris; blok fakta triase tidak dipindai sebagai path sandbox) dan v102 (audit keamanan: penjaga `Host`, token wajib di jalur `uvicorn`, kartu izin tanpa pemotongan, symlink, penyaringan rahasia di riwayat, dan lainnya; lihat [Keamanan](#keamanan)). Belum dites di PC |
| **19 November 2026 (peluncur v1.3.1)** | `iris-update.ps1`: setelah `npm update`, biner Electron (`node_modules\electron\dist\electron.exe`) yang hilang dideteksi dan diunduh ulang lewat `install.js` (fungsi `Repair-Electron`); `npm update` kadang mengganti paket tanpa mengunduh biner dan tetap mengembalikan kode 0. Cek update untuk Overlay kini menampilkan "update" bila biner hilang. `iris-doctor.ps1`: saran perbaikan biner Electron diperjelas; server Iris yang belum jalan dan drive yang bukan drive sistem, proyek, WSL, atau node kini dilaporkan sebagai INFO, bukan WARN (drive yang dipakai Iris tetap WARN atau GAGAL bila menipis). Hanya skrip `.ps1` yang berubah dan skrip tertanam di exe, jadi bangun ulang `IrisLauncher.exe` dengan `build.bat` (versi yang tampil di exe tetap 1.3). Doctor sudah dicoba di PC (0 WARN); `Repair-Electron` belum diuji dengan electron.exe yang sengaja dihapus. |
| **19 November 2026 (v101)** | Tinjauan kode `main.js`, `preload.js`, `iris_web.py`, `iris_games.py`, `iris_translate_img.py`, dan `server.py` menghasilkan pengerasan: pemeriksaan pengirim IPC, izin mikrofon saja, sesi terpisah untuk jendela bantu, nama berkas aman dan penulisan `wx`, pembersihan `iris_web.py` untuk `shot` dan elemen, batas piksel terjemah layar, `/tekateki` menolak tebakan negatif dan pilihan ganda serta tidak lagi salah menolak teka-teki karena substring, peringatan `COMPANION_HOST`, dan komentar `preload.js` (10 slot akun) dikoreksi. Belum dites di PC |
| **19 November 2026 (lanjutan)** | Terjemah layar: pilih area dengan menyeret (v90) dan, sebagai v99, area kecil diperbesar otomatis, hasil ditempel di atas area asli, dan ulangi area terakhir (`Ctrl+Alt+Y`, `/terjemah ulang`); `/rea xref` dan `/rea disasm` tersambung ke `server.py` lewat `rea_api`; seret-lepas file ke overlay = `/rea cepat`. Perbaikan v91 dari tinjauan 13 November: daftar putih `app://` di `main.js`, `_SECRET_RE` hanya menolak 13 sampai 19 digit, regex fakta game tidak lagi menangkap `Tujuan: pahami`, dan CSS chip `#webpill` benar-benar berlaku. Berkas berubah: `main.js`, `preload.js`, `index.html`, `server.py` (`rea_triage.py` tetap v98). Belum dites di PC. Catatan penomoran: "v91" di kode dipakai dua kali (`/rea` triase lokal dan perbaikan keamanan ini), dan nomor v99 diambil sebagai nomor berikutnya setelah v98 |
| **19 November 2026** | `rea_triage.py` v98 "RE Lab" untuk PE x86 / x64: peta panggilan API per fungsi, xref string, peringkat fungsi menarik, anti-analisis tingkat instruksi, API hashing, dan stack string (aksi `re`, `xref`, `disasm`); status v95 sampai v97 dicatat dari kode yang diunggah. Belum dites di PC |
| **12 November 2026** | Game teka-teki `/tekateki`; `rea_triage.py` v95 sampai v97 (berkas baru `rea_extract.py` dan `rea_binary.py`); audit kode dengan tiga perbaikan: Mode fokus memberi tahu `main.js` lewat `setQuiet` di `preload.js`, pembersihan `iris_web.py` kini mencakup `title`, `url`, `host`, dan `name`, serta kalimat Jepang yang sebenarnya bukan Jepang diperbaiki atau tampil tanpa suara (`jp_speakable()`). Belum dites di PC |
| **11 November 2026** | Klip gerak VRMA dipakai jauh lebih sering: tag emosi, frasa ucapan, sentuhan, dan gerak idle memakai klip, dan lima klip seluruh badan ditambahkan; lihat [Animasi klip VRMA](#animasi-klip-vrma) |
| **10 November 2026 siang** | `/rea` v94: celah ReDoS dan injeksi prompt lewat isi sampel ditutup, triase lokal diperluas ke ELF, PDF, OLE2, RTF, LNK, dan skrip |
| **10 November 2026** | Perintah `/rea` untuk membedah file secara statis lewat Hermes, dengan triase lokal tanpa model; folder kerja agen bisa ditambah (mis. Downloads); terminal agen kembali di sandbox Docker tanpa jaringan |
| **8 November 2026** | Statistik fokus `/statistik`, kuis kana `/kana`, sapaan sesuai waktu `/sapa`; tombol putar suara pada ucapan otomatis; bubble menghindari menu yang terbuka; penolakan lewat kartu izin tidak lagi disampaikan Iris sebagai "gagal" |
| **Sebelum 8 November 2026** | Agen Hermes di sandbox Docker dengan persetujuan lewat kartu di overlay; tombol Stop menghentikan agen Hermes; status server di peluncur lewat `/ping`; VOICEVOX di GPU; jeda sambung ulang WebSocket bertahap; perbaikan path berspasi; terjemah layar OCR Jepang/Inggris dengan suara dan pratinjau besar; ikon tray berwarna; tawaran aksi saat menyalin; ekspor/impor konfigurasi; `/rangkum`. Lihat [Keamanan](#keamanan) dan [Status pengujian](#status-pengujian) |

---

## Lisensi

Repositori ini dapat dilihat publik, tetapi **hak cipta dilindungi (All rights reserved)**: kode tidak boleh disalin, dimodifikasi, disebarkan, atau dipakai ulang tanpa izin tertulis, lihat [LICENSE](LICENSE). Aset pihak ketiga (model, suara, gambar karakter) mengikuti lisensi masing-masing pembuatnya.

---

<p align="center">
  Dibuat oleh <strong>KangJiho</strong>
</p>
