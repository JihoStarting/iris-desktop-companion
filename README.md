<p align="center">
  <img src="docs/img/iris-launcher-logo.png" alt="Logo IRIS" width="280">
</p>

# IRIS: AI Companion Desktop Overlay

> *A desktop AI companion overlay for Windows + WSL2: VRM avatar, VOICEVOX voice, and a Hermes Agent bridge that can do real tasks on your computer. Documentation is in Indonesian.*

![License](https://img.shields.io/badge/license-All%20rights%20reserved-red)
![Electron](https://img.shields.io/badge/Electron-overlay-47848F)
![Python](https://img.shields.io/badge/Python-FastAPI-3776AB)
![Platform](https://img.shields.io/badge/platform-Windows%20%2B%20WSL2-0078D6)

IRIS adalah teman AI yang tinggal di desktop. Wajahnya avatar 3D (VRM) yang melayang di atas aplikasi lain, suaranya dari VOICEVOX, dan tangannya adalah **Hermes Agent** yang bisa mengerjakan tugas nyata di komputer (membuka folder, mencari file, menjalankan perintah, mencari di web).

Proyek ini dibuat sebagai proyek pribadi dan masih terus dikembangkan.

---

## Status

- Hermes Agent dipasang: 28 September 2026
- Overlay mulai dikembangkan: 28 Oktober 2026
- Dipublikasikan di GitHub: 5 November 2026
- Versi terbaru: v1.0.0 (peluncur `IrisLauncher.exe`)
- Status: aktif dikembangkan sebagai proyek pribadi
- Terakhir diperbarui: 8 November 2026 (agen Hermes kini berjalan di sandbox Docker dan setiap tindakan berisiko meminta persetujuan lewat kartu di overlay; tombol Stop menghentikan agen Hermes; status server di peluncur dicek lewat `/ping`; VOICEVOX bisa berjalan di GPU; jeda sambung ulang WebSocket bertahap; perbaikan path berspasi; lihat [Keamanan](#keamanan) dan [Status pengujian](#status-pengujian))

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
- [Bicara lewat mikrofon](#bicara-lewat-mikrofon)
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
- Klip gerak VRMA buatan sendiri (4 klip kecil: `angguk`, `geleng`, `miring`, `tunduk`; hanya punggung, dada, leher, dan kepala, tanpa lengan) yang diputar lewat gerbang emosi. Klip tari dan lengan belum ada
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
- Suara per emosi lewat VOICEVOX: kecepatan, nada, dan intonasi menyesuaikan emosi kalimat, lip-sync berbasis mora, dan cache suara lokal. Mesin VOICEVOX bisa berjalan di Windows dengan GPU (DirectML) atau CPU, dipilih di Pengaturan peluncur
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
- **Bicara lewat mikrofon** (STT, opsional) dengan faster-whisper. Model, bahasa, dan kosakata bantu bisa disetel lewat `.env`; ucapan yang diawali kata kerja aksi (mis. "Cek ...", "Cari ...") tetap dijalankan sebagai tugas walau Whisper menambahkan tanda tanya, dan jawaban singkat seperti "iya" atau "lanjut aja" setelah Iris menawarkan `/agen` menjalankan tugasnya. Lihat [Bicara lewat mikrofon](#bicara-lewat-mikrofon)
- **Mode belajar bahasa Jepang** (`/belajar`): Iris memberi kalimat Jepang, kamu menebak arti atau mengulang ucapannya, lalu dikoreksi. Ada opsi menyerah untuk melihat jawaban
- **Perintah aplikasi lokal** (`/lokal`): membuka aplikasi dari daftar putih yang ditetapkan di `main.js`

### Agen dan memori

- **Jembatan Hermes Agent** (`/agen`, `/agent`, `/h`): memberi tugas ke agen di WSL, lengkap dengan indikator "sedang memproses" berhitung detik, heartbeat, tombol Stop (menghentikan agen di Hermes bila `HERMES_STREAM=1`), dan batas waktu
- **Konfirmasi tugas berbahaya**: tugas `/agen` yang berbau hapus, pindah, timpa, atau format file ditahan dulu dan muncul kartu "Iris mau menjalankan ini. Lanjut?" dengan tombol Jalankan dan Batal
- **Persetujuan tindakan agen**: bila Hermes menandai sebuah perintah berisiko, overlay menampilkan kartu izin dengan tombol **Izinkan sekali** atau **Tolak**. Tanpa jawaban, koneksi putus, atau Stop berarti ditolak; pilihan "selalu" dan "sesi" tidak pernah ditawarkan
- **Sandbox Docker**: terminal agen berjalan di kontainer yang hanya bisa menulis ke satu folder kerja. Tugas dengan path di luar folder itu ditolak sebelum dikirim, dan Iris memeriksa disk sendiri lalu menambahkan baris `[Verifikasi Iris]` pada hasil (karena laporan agen tidak selalu benar)
- Kartu **Hasil tugas** dengan tombol Salin. Path WSL di laporan otomatis diubah menjadi path Windows, termasuk folder berspasi (`C:\Users\<user>\...`)
- Hermes menerima konteks 10 pesan terakhir hanya bila tugas merujuk ke percakapan, dan tahu folder Windows lewat `HERMES_WIN_HOME`
- Iris dilarang mengaku bisa membuat, mengubah, atau menghapus file di obrolan biasa; ia menyuruh memakai `/agen`. Laporan agen disampaikan netral dan bersumber
- **Memori ringan**: `/ingat`, `/memori`, `/lupa` (maksimal 40 hal, 200 karakter per hal). Isi yang mirip rahasia ditolak
- **Riwayat obrolan persisten**: 20 pesan terakhir, kedaluwarsa 3 hari, gambar tidak pernah disimpan, pasangan pesan berisi kata rahasia tidak ditulis
- **Mini-browser** multi-akun (`/chrome`), lihat [bagiannya](#mini-browser-chrome)

### Infrastruktur

- `IrisLauncher.exe`: peluncur satu klik dengan indikator hijau per layanan. Menutup peluncur ikut mematikan semua layanan (bisa dimatikan di Pengaturan), dan menu **Keluar** di overlay bisa mematikan semuanya lewat peluncur
- Kotak **Mesin suara VOICEVOX** (GPU atau CPU) di Pengaturan peluncur; bila folder `vv-engine` tidak ada, peluncur memakai unit `voicevox` di WSL (CPU)
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
| VOICEVOX Engine | Berjalan di port `50021` (opsional, tanpa ini Iris menjawab lewat teks saja). Peluncur menjalankan `vv-engine\run.exe` (build DirectML, mis. versi 0.25.2) dengan GPU yang mendukung DirectX 12; tanpa folder itu ia memakai unit `voicevox` di WSL (CPU). Folder `vv-engine` tidak ada di repositori, letakkan sendiri di folder proyek |
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

Lalu buka `.env` dan isi dengan nilai milikmu sendiri. **`COMPANION_TOKEN` wajib diisi** (minimal 16 karakter); server langsung berhenti dengan pesan `[FATAL]` kalau kosong. Buat tokennya dengan:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Jangan pernah meng-commit file `.env`.**

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

### Opsional (`IRIS_*`)

| Variabel | Fungsi |
|---|---|
| `COMPANION_ALLOW_NO_TOKEN=1` | **Khusus pengembangan**: izinkan server jalan tanpa token (mis. untuk `dev/test_client.html`). Jangan dipakai untuk pemakaian sehari-hari |
| `AGENT_CONFIRM_ALWAYS=1` | Tetap tampilkan kartu konfirmasi Iris walau gerbang persetujuan Hermes aktif (jaring cadangan) |
| `AGENT_APPROVAL=0` | Matikan kartu izin Hermes (semua izin ditolak otomatis) |
| `AGENT_APPROVAL_TTL` | Batas menunggu klik kartu izin (detik, bawaan 120, maksimal 280) |
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
| `IRIS_HEALTH_CONNECT` | Batas sambung (detik, bawaan 1,5) per layanan saat `/health` memeriksa VOICEVOX, 9Router, dan Hermes |

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

Cek kesehatan layanan di `http://127.0.0.1:8765/health`. Untuk sekadar memastikan server hidup (tanpa memeriksa layanan lain), buka `http://127.0.0.1:8765/ping`; jawabannya `{"ok":true}`.

> Karena `COMPANION_TOKEN` wajib, halaman `http://127.0.0.1:8765` di browser tidak bisa dipakai untuk chat (browser tidak dapat mengirim header token). Gunakan overlay Electron. Halaman tes `dev/test_client.html` hanya tersedia bila kamu sengaja menjalankan server dengan `COMPANION_ALLOW_NO_TOKEN=1` dan token kosong.

### Lewat peluncur

`IrisLauncher.exe` menjalankan WSL, layanan pendukung, server, dan overlay sekaligus. Bangun sendiri dengan `IrisLauncher-src\build.bat` (memakai `csc.exe` bawaan Windows, tanpa memasang apa pun), atau unduh dari tab Releases bila tersedia.

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

## Mini-browser `/chrome`

Panel browser kecil di samping karakter dengan **sepuluh slot akun** yang masing-masing punya sesi login terpisah. Panel berjalan di proses terpisah dan tanpa akses ke fungsi Electron.

| Perintah | Fungsi |
|---|---|
| `/chrome 1` sampai `/chrome 10` | Ganti ke akun nomor itu dan buka link awalnya |
| `/chrome` | Buka akun terakhir |
| `/chrome <nama>` | Sama, memakai nama akun |
| `/chrome 3 https://situs.com` | Akun 3 dengan alamat lain |
| `/chrome tutup` | Tutup panel dan buang prosesnya |
| `/chrome daftar` atau `/akun` | Tampilkan semua slot |
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
- **Skill kustom** (40+): mis. `deep-research`, `academic-writer`, `excalidraw`, `oss-forensics`, `laptop-storage-analyzer`, dan `isi-form-otomatis`. Skill dimuat per tugas

Laporan Hermes ditampilkan apa adanya di kartu "Hasil tugas". Iris menyampaikannya secara netral dan bersumber, dan hanya menyatakan berhasil bila laporan Hermes jelas menyatakannya.

> **Catatan Hermes di Docker.** Setelah `systemctl --user restart hermes-gateway`, tunggu `http://127.0.0.1:8642/health` menjawab (bisa puluhan detik) sebelum mengirim `/agen`; tugas yang terlalu cepat gagal dengan "Hermes tidak aktif" atau `runtime_draining`. Kontainer sandbox berhenti sendiri setelah 300 detik tanpa aktivitas.

> **Tombol Stop.** Dengan `HERMES_STREAM=1`, Iris memanggil `POST /v1/runs/{id}/stop` di Hermes sebelum menutup koneksi. Diuji 7 November 2026: Hermes menjawab HTTP 200 `stopping`, status tugas `cancelled`, dan file baru berhenti terbentuk. Berhentinya tidak seketika (satu langkah yang sedang berjalan bisa selesai dulu), dan kegagalan memanggil stop hanya dicatat di terminal tanpa mengganggu pembatalan di sisi Iris. Dengan `HERMES_STREAM=0` (bawaan), Stop hanya memutus koneksi dan agen di Hermes tetap berjalan (terukur 7 November 2026). Periksa dengan [`scripts/cek-stop-hermes.py`](scripts/cek-stop-hermes.py), atau ukur perilaku tanpa stop dengan [`scripts/cek-cancel-hermes.py`](scripts/cek-cancel-hermes.py) (jalankan dari folder proyek, mis. `.\.venv\Scripts\python.exe scripts\cek-stop-hermes.py`; `cek-cancel-hermes.py` punya opsi `--skip-health`).

---

## Keamanan

IRIS dirancang untuk berjalan lokal dan memberi agen akses ke komputermu, jadi beberapa pengaman dipasang:

- Server hanya mendengar di `127.0.0.1`.
- **`COMPANION_TOKEN` wajib** (minimal 16 karakter). Koneksi `/ws` dilindungi token lewat header `X-Iris-Token` (kode penolakan 1008), plus pengecekan `Origin`. Server menolak start bila token kosong atau terlalu pendek; satu-satunya pengecualian adalah `COMPANION_ALLOW_NO_TOKEN=1` untuk pengembangan. Karena agen bisa menjalankan perintah di komputermu, jangan pakai pengecualian itu untuk pemakaian sehari-hari
- Perintah `/agen` yang berpotensi berbahaya (hapus, pindah, timpa, format file) meminta konfirmasi dulu. Daftar kata pemicu bisa disetel, `/health` menampilkan `agent_confirm`, dan konfirmasi sekali pakai kedaluwarsa dalam 120 detik. Batasnya: pemeriksaan ini hanya membaca teks permintaanmu, bukan tindakan yang dipilih agen, jadi ini jaring pengaman untuk salah ketik dan salah paham
- **Persetujuan tindakan agen.** Perintah yang ditandai Hermes menunggu klik **Izinkan sekali** atau **Tolak** di overlay. Sistemnya gagal-aman (tanpa jawaban = tolak), hanya `once` dan `deny` yang pernah dikirim ke Hermes, dan mode persetujuan Hermes diset `manual`. Perintah yang tidak ditandai detektor Hermes tidak menghasilkan kartu
- **Sandbox Docker** (8 November 2026). Terminal agen berjalan di kontainer; yang bisa ditulis hanya satu folder kerja dan home sandbox, sedangkan drive dan folder lain di komputermu tidak terlihat. Dengan `HERMES_SANDBOX=1`, Iris menolak tugas dengan path di luar sandbox. Batasnya: agen tetap bisa menghapus atau mengubah isi folder kerjanya, dan jaringan kontainer aktif, jadi isi yang terbaca di sana tetap bisa dikirim keluar bila agen terkena injeksi
- **Laporan agen tidak selalu benar.** Agen pernah melaporkan "berhasil dihapus" padahal tidak ada tindakan sama sekali. Jangan percaya laporan begitu saja; cek dengan `dir` atau `ls`. Iris menambah `[Verifikasi Iris]` hanya untuk path di folder kerja agen
- **Injeksi prompt dari isi web.** Isi halaman diperlakukan sebagai data, bukan perintah (aturan di prompt agen dan pembersih di `iris_web.py`). Perlindungan ini bergantung pada kepatuhan model dan baru lulus 2 uji, jadi jangan menganggapnya pagar teknis
- Kunci API dan token tidak pernah ditulis di dokumen atau chat; bila ada yang bocor, ganti dan restart layanan terkait. Jangan beri `sudo` tanpa password di WSL
- Semua jendela menolak navigasi, jendela baru, dan `<webview>`
- Memori dan riwayat menolak menyimpan isi yang mirip rahasia (kata sandi dan sejenisnya)
- Panel mini-browser berjalan terisolasi (sandbox, tanpa preload, tanpa akses kamera, mikrofon, atau notifikasi, navigasi hanya ke `https://`)
- Jembatan baca-saja mati secara bawaan dan berlapis (lihat [bagiannya](#jembatan-baca-saja-untuk-hermes))
- Fitur yang menyentuh privasi (duduk di jendela lain) **mati secara bawaan**
- Log terminal hanya mencatat panjang dan sidik token, bukan isinya, dan URL dipotong sampai path. Endpoint `/health` tidak bertoken, jadi hanya menampilkan `ws_token` sebagai "aktif" atau "KOSONG", tanpa panjang atau sidik
- DevTools tidak tersedia di versi rilis (aplikasi yang dipaketkan)

Hal yang perlu kamu jaga sendiri:

- Riwayat obrolan dan memori tersimpan polos di disk. Jangan taruh folder proyek di drive yang tersinkron ke cloud
- Log server memuat teks chat

Berkas sensitif tidak pernah masuk repositori: `.env`, riwayat percakapan, memori, log, arsip, dan folder `vv-engine/` dikecualikan lewat `.gitignore`.

Menemukan celah keamanan? Mohon jangan buka issue publik; hubungi pemilik repositori secara langsung.

---

## Status pengujian

Fitur di bawah sudah ditulis tetapi **belum lulus uji penuh di PC**. Anggap eksperimental sampai ada konfirmasi.

| Area | Catatan |
|---|---|
| Terjemah layar | Belum diuji end-to-end |
| Bicara lewat mikrofon: penyetelan 6 Nov (model, kosakata bantu, perintah suara) | Perbaikan perilaku diuji dengan kalimat dari tangkapan layar; pemilik melaporkan tidak ada masalah. Akurasi tetap bergantung pada model dan mikrofon |
| Mini-browser, fase 4 (pil akun, hemat RAM, tab diparkir) | Belum dites di Electron asli |
| Tugas `/agen` ringan terasa lambat | Penyebab belum dipastikan |
| Sambung ulang WebSocket bertahap (jeda 2, 4, 8, maksimal 15 detik) | Diuji 1 kali (server dimatikan sekitar 12 detik, overlay tersambung lagi dan riwayat dipulihkan tanpa dibuka ulang) |
| VOICEVOX di GPU (DirectML) | Mesin naik dan mendeteksi GPU (RTX 4060 Laptop, DirectML OK, `/version` 0.25.2). Lulus 8 November 2026 lewat perbandingan latensi (kalimat sekitar 75 karakter, `audio_query` + `synthesis`, mesin yang sama): GPU 720, 483, 601 ms lawan CPU 2939 (pemanasan), 1972, 2003, 1899 ms, jadi sekitar 3,6 kali lebih cepat. Baris perintah mesin yang melayani port 50021 memuat `--use_gpu`. Batas: penghitung `GPU Engine` per proses tidak bisa dijadikan bukti di mesin ini, dan pengukuran satu kalimat saja |
| Batas tunggu stop Hermes di peluncur | Lulus 8 November 2026: chip Hermes dimatikan (4 detik) dan dinyalakan lagi (12 detik) tanpa tampak gagal; batas stop systemd 75 detik |
| Status server di peluncur lewat `/ping` | Lulus 8 November 2026: chip server tetap Hidup saat Hermes dimatikan, dan `/ping` menjawab 2 sampai 15 ms (`/health` sekitar 2 detik saat ada layanan mati). Sisa kecil: log start masih menulis "menunggu /health" |
| Persetujuan tindakan agen dan sandbox Docker | Izinkan sekali dan Tolak terbukti di Hermes sungguhan, satu uji per kasus; `rm` file tunggal di sandbox kini juga diuji sekali (8 November 2026: satu kartu Hermes, Izinkan sekali menghapus, Tolak menjaga file). Tes otomatis memakai Hermes palsu (28 dan 26 tes lulus) |
| Perlindungan injeksi prompt | Lulus 2 uji (`curl` dan file lokal), belum dengan halaman web sungguhan |
| Tombol kartu izin yang aktif setelah 0,7 detik (cegah klik ganda) dan peringkasan hasil agen yang lebih tepat (v72) | Peringkasan hasil agen lulus 8 November 2026 (resep dirangkum, peringatan injeksi disampaikan). Tombol kartu: Tolak dan Izinkan sekali berfungsi; efek jeda 0,7 detik terhadap klik ganda belum terbukti dari log |
| Jembatan baca-saja untuk Hermes | Kode ada, belum dites; belum ada skill Hermes yang memakainya |
| Bubble dengan lampiran dekat tepi atas layar | Belum dites |

Yang sudah lulus uji antara lain: jembatan Hermes (termasuk path Windows di kartu hasil), konfirmasi `/agen` berbahaya, token `/ws`, ganti baju, tema, fun fact, alarm dan jam, mood, seret file dan lampiran gambar, ekspor, pilihan bernomor, pil status koneksi, dan peluncur, termasuk menutup peluncur dan menu Keluar yang mematikan semua layanan (`--stop-all`, dilaporkan pemilik berfungsi), serta perbaikan v46 sampai v50 (jaga UI tetap di layar, panel pindah sisi, rambut dan bayangan setengah badan; dilaporkan pemilik sudah beres), serta pikiran batin (dilaporkan pemilik aman). Dari 7 November 2026: pembatalan tugas yang benar-benar menghentikan agen Hermes (HTTP 200 `stopping`, status `cancelled`) dan konversi path berspasi (`tests/test_path_berspasi.py`, 13 dari 13 tes proyek lulus).

---

## Rencana

Ide yang sudah disetujui atau dicatat, **belum ada kodenya**:

- Skill Hermes `cek-elearning` dan skill yang memakai jembatan baca-saja
- Memori otomatis ringan (ringkasan fakta baru yang kamu setujui dulu sebelum disimpan)
- Auto-start bersama Windows dan skrip setup untuk PC baru
- Mini-browser fase 5b dan 5c (Hermes beraksi dengan konfirmasi dan batas domain)
- Menari mengikuti musik dan perintah `/nari` (butuh klip `.vrma` lengan)
- Angin dari kecepatan kursor (`/angin`)
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
├── vv-engine/               # engine VOICEVOX (tidak ada di repositori, letakkan sendiri)
├── scripts/
│   ├── buat_klip_vrma.py    # skrip pembuat klip animasi VRMA
│   ├── cek-cancel-hermes.py # skrip ukur pembatalan tugas Hermes (tanpa stop)
│   └── cek-stop-hermes.py   # skrip uji tombol Stop menghentikan agen Hermes
├── dev/
│   └── test_client.html     # halaman tes koneksi (hanya untuk pengembangan, tanpa token)
├── tests/                   # tes otomatis (mis. test_path_berspasi.py)
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
    ├── idle_loop.vrma       # animasi idle
    └── clips.json           # daftar klip gerak (opsional)
```

Klip gerak sederhana bisa dibuat sendiri dengan `python scripts\buat_klip_vrma.py` dari folder proyek; skrip ini menulis `.vrma` dan `clips.json` ke `assets/animations/`.

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
| Model gambar timeout | Kurangi jumlah gambar yang dikirim atau naikkan `NINEROUTER_VISION_READ_TIMEOUT` |
| Tombol Salin gambar gagal | Restart Iris. Handler mencoba tiga cara berurutan, termasuk lewat PowerShell |
| Pintasan bisu tidak bekerja | Kombinasinya mungkin dipakai aplikasi lain. Terminal mencetak pintasan yang terdaftar; paksa sendiri lewat `IRIS_MUTE_KEY` |
| Menu Keluar hanya menutup overlay | Overlay tidak dijalankan lewat peluncur (mis. `npm start`), atau peluncurnya belum versi terbaru. Bangun ulang `IrisLauncher.exe` dan mulai dari peluncur |
| Whisper salah dengar nama atau perintah (mis. "agen" jadi "akun") | Naikkan `IRIS_STT_MODEL` (`small` atau `medium`), tambahkan kata itu ke `IRIS_STT_PROMPT`, dan dekatkan mikrofon. Lihat [Bicara lewat mikrofon](#bicara-lewat-mikrofon) |
| Peluncur gagal di langkah WSL | Jalankan `iris-doctor.ps1` dan lihat log di `iris-start.log` |
| Suara VOICEVOX lambat atau GPU tidak terpakai | Cek kotak **Mesin suara VOICEVOX** di Pengaturan peluncur, dan cari `DirectML (device_id=0): OK` di `iris-voicevox.err.log`. Bila unit `voicevox` di WSL masih aktif, matikan: `wsl -d Ubuntu -- systemctl --user disable --now voicevox` |
| Server baru langsung mati dengan `Errno 10048` | Server lama masih memegang port 8765. Cek `Get-NetTCPConnection -LocalPort 8765 -State Listen`, matikan prosesnya (atau lewat peluncur), lalu start ulang |
| Agen melapor "berhasil" tetapi file atau folder tidak berubah | Laporan agen tidak selalu benar, dan di sandbox path di luar folder kerja tidak terjangkau. Cek langsung dengan `dir`, dan kirim path penuh pada `/agen` |
| `/agen` ditolak dengan pesan path di luar sandbox | `HERMES_SANDBOX=1` aktif: hanya folder kerja agen yang bisa disentuh. Letakkan berkasnya di sana, atau matikan sandbox sadar akan risikonya |
| Tugas agen menggantung tanpa kartu izin | Pastikan `HERMES_STREAM=1` dan `approvals.mode` Hermes `manual`; restart server dan buka ulang overlay |
| Stop tidak menghentikan agen Hermes | Pastikan `HERMES_STREAM=1` di `.env`, restart server, dan buka ulang overlay. Satu langkah yang sedang berjalan bisa selesai dulu. Me-restart `hermes-gateway` di tengah tugas memunculkan "Server disconnected"; itu bukan hasil tombol Stop |
| Chip Hermes tampak gagal mati | Hermes bisa butuh sampai sekitar 70 detik untuk berhenti; peluncur menunggu 75 detik. Kalau tetap tampak gagal, cek `systemctl --user status hermes-gateway` di WSL. Peluncur lama (sebelum build ulang 8 November) hanya menunggu sekitar 12 detik, jadi bangun ulang `IrisLauncher.exe` |
| Chip server.py tampak Mati padahal server jalan, atau server tidak bisa dinyalakan saat Hermes mati | Peluncur lama menilai server lewat `/health`, yang melambat saat Hermes mati. Perbarui `server.py`, bangun ulang `IrisLauncher.exe` (peluncur kini memakai `/ping`), lalu cek `http://127.0.0.1:8765/ping`. Bila masih salah, lihat di Task Manager apakah `python.exe` benar-benar hilang |

Untuk diagnosis lebih lanjut, jalankan overlay dengan `npm start`, buka DevTools dengan `Ctrl+Alt+D`, dan cek tab Console (DevTools tidak tersedia di versi rilis).

---

## Dokumentasi

- [`docs/QUICKSTART.md`](docs/QUICKSTART.md): panduan mulai cepat dari nol sampai Iris menjawab

---

## Lisensi

Repositori ini dapat dilihat publik, tetapi **hak cipta dilindungi (All rights reserved)**: kode tidak boleh disalin, dimodifikasi, disebarkan, atau dipakai ulang tanpa izin tertulis, lihat [LICENSE](LICENSE). Aset pihak ketiga (model, suara, gambar karakter) mengikuti lisensi masing-masing pembuatnya.

Dibuat oleh KangJiho.
