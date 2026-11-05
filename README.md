<p align="center">
  <img src="iris-launcher-logo.png" alt="Logo IRIS" width="280">
</p>

# IRIS: AI Companion Desktop Overlay

![License](https://img.shields.io/badge/license-All%20rights%20reserved-red)
![Electron](https://img.shields.io/badge/Electron-overlay-47848F)
![Python](https://img.shields.io/badge/Python-FastAPI-3776AB)
![Platform](https://img.shields.io/badge/platform-Windows%20%2B%20WSL2-0078D6)

IRIS adalah teman AI yang tinggal di desktop. Wajahnya avatar 3D (VRM) yang melayang di atas aplikasi lain, suaranya dari VOICEVOX, dan tangannya adalah **Hermes Agent** yang bisa mengerjakan tugas nyata di komputer (membuka folder, mencari file, menjalankan perintah, mencari di web).

Proyek ini dibuat sebagai proyek pribadi dan masih terus dikembangkan. Catatan pengembangan lengkap (termasuk hasil uji tiap versi) ada di folder [`docs/`](docs/).

---

## Status

- Hermes Agent dipasang: 28 September 2026
- Overlay mulai dikembangkan: 28 Oktober 2026
- Dipublikasikan di GitHub: 5 November 2026
- Versi terbaru: v1.0.0 (peluncur `IrisLauncher.exe`)
- Status: aktif dikembangkan sebagai proyek pribadi

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
- [Perintah chat](#perintah-chat)
- [Pintasan keyboard](#pintasan-keyboard)
- [Keamanan](#keamanan)
- [Struktur proyek](#struktur-proyek)
- [Aset](#aset)
- [Pemecahan masalah](#pemecahan-masalah)
- [Dokumentasi](#dokumentasi)
- [Lisensi](#lisensi)

---

## Fitur

### Avatar dan tampilan
- Avatar VRM 3D dalam jendela Electron transparan yang selalu di atas
- Ekspresi dan gerak halus, bernapas, berkedip, dan menatap kursor
- Sistem mood: suasana hati Iris naik dan turun mengikuti interaksi
- Ganti baju (beberapa model VRM musiman)
- Duduk di tepi atas jendela lain, bersembunyi di tepi layar, dan tidur otomatis saat tidak ada aktivitas
- **Mode fokus**: karakter dan bubble hilang, hanya garis petunjuk tipis yang tersisa

### Obrolan dan suara
- Obrolan dengan persona Iris (gaya santai, campuran Indonesia dan Jepang)
- Suara per emosi lewat VOICEVOX, dengan bubble teks yang ikut bicara
- Fun fact, ucapan jam, alarm, timer, dan pengingat istirahat

### Penglihatan dan belajar
- Lampirkan gambar lewat tempel, tombol klip, atau seret berkas, lalu Iris menjelaskan isinya
- Ambil screenshot layar dan langsung bertanya
- Terjemah layar (teks Jepang di layar diucapkan dan diterjemahkan)
- Mode belajar bahasa Jepang dengan soal latihan

### Agen dan memori
- **Jembatan Hermes Agent** (`/agen`): memberi tugas ke agen di WSL, lengkap dengan status "sedang memproses", pembatalan, dan batas waktu
- Konfirmasi otomatis sebelum menjalankan perintah berbahaya (misalnya menghapus file)
- Kartu "Hasil tugas" dengan tombol salin, dan popup salin link
- Memori ringan (`/ingat`, `/memori`, `/lupa`) dan riwayat percakapan lokal
- Mini-browser panel (`/chrome`)

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

---

## Teknologi

- **Frontend:** Electron, three.js, `@pixiv/three-vrm`
- **Backend:** Python, FastAPI, WebSocket
- **Suara:** VOICEVOX
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
| VOICEVOX | Berjalan di port `50021` (opsional, tanpa ini Iris tidak bersuara) |
| 9Router atau endpoint LLM kompatibel OpenAI | Berjalan di `localhost:20128` secara bawaan |
| WSL2 + Hermes Agent | Opsional, hanya untuk fitur `/agen` |

Disarankan RAM 16 GB jika Hermes dan model lokal dijalankan bersamaan.

---

## Instalasi

```powershell
git clone https://github.com/JihoStarting/iris-desktop-companion.git
cd iris-desktop-companion

# Dependency Node
npm install

# Virtual environment Python
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Konfigurasi
copy .env.example .env
```

Lalu buka `.env` dan isi dengan nilai milikmu sendiri. **Jangan pernah meng-commit file `.env`.**

---

## Konfigurasi

Semua pengaturan dibaca dari file `.env` (di folder proyek atau di folder user Windows). Contoh lengkap ada di [`.env.example`](.env.example).

| Variabel | Fungsi | Bawaan |
|---|---|---|
| `NINEROUTER_URL` | Alamat endpoint LLM | `http://localhost:20128/v1` |
| `NINEROUTER_API_KEY` | Kunci API 9Router (wajib bila "Require API key" aktif) | kosong |
| `NINEROUTER_MODEL` | Nama model atau combo | `Iris` |
| `VOICEVOX_URL` | Alamat VOICEVOX | `http://127.0.0.1:50021` |
| `VOICEVOX_SPEAKER` | ID suara VOICEVOX | `2` |
| `COMPANION_HOST` | Alamat server overlay | `127.0.0.1` |
| `COMPANION_PORT` | Port server overlay | `8765` |
| `COMPANION_USER_NAME` | Nama panggilan pengguna | `Rover` |
| `COMPANION_TOKEN` | Token autentikasi `/ws` (disarankan diisi) | kosong |
| `HERMES_URL` | Alamat API server Hermes | `http://127.0.0.1:8642/v1` |
| `HERMES_API_KEY` | Kunci API Hermes (harus sama dengan `API_SERVER_KEY` di Hermes) | kosong |
| `HERMES_TIMEOUT` | Batas waktu tugas agen (detik) | `120` |
| `HERMES_WIN_HOME` | Folder user Windows dilihat dari WSL | `/mnt/c/Users/<user>` |

Membuat token untuk `COMPANION_TOKEN`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Menjalankan

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

Alternatifnya, peluncur `IrisLauncher.exe` (lihat tab Releases) menjalankan server, overlay, dan layanan pendukung sekaligus.

---

## Perintah chat

Ketik di kotak input overlay. Ketik `/help` untuk daftar lengkap di aplikasi.

### Agen
| Perintah | Fungsi |
|---|---|
| `/agen <tugas>` | Beri tugas ke Hermes Agent, misalnya `/agen sebutkan isi folder Download` |
| `/chrome` | Mini-browser panel |

### Waktu dan fokus
| Perintah | Fungsi |
|---|---|
| `/timer N [nama]` | Timer N menit |
| `/pomodoro` | Sesi pomodoro |
| `/alarm HH:MM [nama]` | Pasang alarm (`/alarm batal <no\|semua>` untuk menghapus) |
| `/jam` | Iris mengucapkan jam (`/jam nyala` untuk tiap jam) |
| `/istirahat N` | Pengingat istirahat tiap N menit aktif |
| `/fokus` | Mode fokus (karakter dan bubble hilang) |
| `/bisu` | Matikan suara |
| `/tidur` | Iris tidur |

### Layar dan belajar
| Perintah | Fungsi |
|---|---|
| `/layar [tanya]` | Ambil screenshot lalu bertanya |
| `/terjemah [catatan]` | Terjemahkan teks di layar |
| `/belajar` | Mode belajar bahasa Jepang |
| `/clip` | Ambil klip |

### Memori dan penampilan
| Perintah | Fungsi |
|---|---|
| `/ingat <hal>` | Simpan sesuatu ke memori |
| `/memori` | Lihat isi memori |
| `/lupa <no>` | Hapus satu memori |
| `/mood` | Lihat suasana hati Iris |
| `/baju` | Ganti baju (pilih dengan angka) |
| `/duduk nyala` | Iris duduk di tepi atas jendela terdekat |
| `/sembunyi` | Iris bersembunyi di tepi layar |
| `/atas [mati\|nyala]` | Selalu di atas jendela lain |
| `/ekspor` | Ekspor percakapan |

Perintah yang tidak dikenal diteruskan ke server.

---

## Pintasan keyboard

| Pintasan | Fungsi |
|---|---|
| `Ctrl+Alt+T` | Terjemahkan layar |
| `Ctrl+Alt+D` | Buka DevTools overlay |
| `Ctrl+V` | Tempel gambar dari clipboard sebagai lampiran |

Klik kanan pada karakter untuk menu aksi cepat, dan gunakan ikon tray untuk pengaturan.

---

## Keamanan

IRIS dirancang untuk berjalan lokal dan memberi agen akses ke komputermu, jadi beberapa pengaman dipasang:

- Server hanya mendengar di `127.0.0.1`.
- Koneksi `/ws` dilindungi token (`COMPANION_TOKEN`) lewat header `X-Iris-Token`, plus pengecekan `Origin`.
- Perintah `/agen` yang berpotensi berbahaya (misalnya menghapus file) meminta konfirmasi dulu.
- Memori dan riwayat menolak menyimpan isi yang mirip rahasia (kata sandi dan sejenisnya).
- Panel mini-browser berjalan terisolasi (sandbox, tanpa akses kamera, mikrofon, atau notifikasi).
- Fitur yang menyentuh privasi (misalnya duduk di jendela lain) **mati secara bawaan**.

Berkas sensitif tidak pernah masuk repositori: `.env`, riwayat percakapan, memori, log, dan arsip dikecualikan lewat `.gitignore`.

Menemukan celah keamanan? Mohon jangan buka issue publik; hubungi pemilik repositori secara langsung.

---

## Struktur proyek

```
.
├── main.js                  # proses utama Electron (jendela, tray, IPC)
├── preload.js               # jembatan aman antara renderer dan main
├── index.html               # tampilan overlay: avatar, bubble, input
├── server.py                # backend FastAPI + WebSocket
├── iris_web.py              # klien web pendukung
├── buat_klip_vrma.py        # skrip pembuat klip animasi VRMA
├── cek-cancel-hermes.py     # skrip uji pembatalan tugas Hermes
├── test_client.html         # halaman tes koneksi (tanpa token)
├── clips.json               # daftar klip (salinan; aplikasi membaca assets/animations/clips.json)
├── iris-launcher-logo.png   # logo (dipakai di header README)
├── requirements.txt         # dependency Python
├── package.json             # dependency Node
├── package-lock.json        # versi dependency Node yang terkunci
├── .env.example             # contoh konfigurasi
├── .gitignore               # berkas yang tidak masuk repositori
├── LICENSE                  # lisensi (hak cipta dilindungi, hanya untuk dilihat)
├── README.md                # dokumen ini
├── IrisLauncher-src/        # kode sumber peluncur (C# dan PowerShell)
└── docs/                    # catatan pengembangan dan referensi sistem
    ├── iris-companion-gabungan.md
    ├── iris-system.md
    └── roadmap-ai-companion.md
```

---

## Aset

Aset (model VRM, animasi VRMA, suara) **tidak disertakan** dalam repositori karena ukuran dan lisensi. Letakkan sendiri di folder `assets/`:

```
assets/
├── iris.vrm                 # model utama
├── Iris_winter.vrm          # model baju (opsional)
└── animations/
    └── idle_loop.vrma       # animasi
```

Pastikan kamu memiliki hak pakai atas model dan aset yang kamu gunakan.

---

## Pemecahan masalah

| Gejala | Kemungkinan penyebab dan solusi |
|---|---|
| Iris tidak bersuara, terminal penuh `VOICEVOX gagal` | VOICEVOX belum berjalan. Jalankan VOICEVOX dulu (port 50021) |
| Balasan `401 Missing API key` | `NINEROUTER_API_KEY` kosong. Isi di `.env` lalu restart server |
| Overlay tidak tersambung, log `/ws ditolak` | Token server dan overlay berbeda. Cek sidik token di terminal server dan terminal Electron, lalu restart keduanya |
| Halaman `127.0.0.1:8765` menampilkan "Server Iris aktif" saja | Normal bila `COMPANION_TOKEN` aktif. Gunakan overlay Electron |
| `/agen` membalas HTTP 503 atau tidak merespons | Pastikan API server Hermes aktif di `127.0.0.1:8642` dan `HERMES_API_KEY` sama dengan `API_SERVER_KEY` |
| File hasil agen "tidak ada" di Download | Hermes berjalan di WSL, jadi `~/Downloads` miliknya adalah folder Linux. Atur `HERMES_WIN_HOME` agar menunjuk ke folder Windows |
| Perubahan `.env` tidak terbaca | Server hanya membaca `.env` saat start. Restart server dan overlay |
| Karakter menghilang sesekali | Pemulihan WebGL otomatis sudah dipasang. Bila terulang, lihat terminal Electron |

Untuk diagnosis lebih lanjut, buka DevTools dengan `Ctrl+Alt+D` dan cek tab Console.

---

## Dokumentasi

Catatan pengembangan lengkap ada di folder [`docs/`](docs/):

- [`iris-companion-gabungan.md`](docs/iris-companion-gabungan.md): dokumen gabungan overlay dan Hermes, berisi roadmap, riwayat versi, dan hasil uji
- [`iris-system.md`](docs/iris-system.md): referensi sistem Hermes
- [`roadmap-ai-companion.md`](docs/roadmap-ai-companion.md): roadmap pendamping AI desktop

---

## Lisensi

Repositori ini dapat dilihat publik, tetapi **hak cipta dilindungi (All rights reserved)**: kode tidak boleh disalin, dimodifikasi, disebarkan, atau dipakai ulang tanpa izin tertulis, lihat [LICENSE](LICENSE). Aset pihak ketiga (model, suara, gambar karakter) mengikuti lisensi masing-masing pembuatnya.

Dibuat oleh KangJiho.
