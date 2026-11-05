# Panduan Mulai Cepat

Panduan ini membawamu dari repositori kosong sampai Iris menyapa dan menjawab dengan suara. Hermes Agent (`/agen`) dan mini-browser (`/chrome`) sengaja dipisah ke bagian akhir karena opsional.

Perkiraan waktu: 20 sampai 30 menit, di luar waktu unduh.

---

## 1. Yang harus ada dulu

| Kebutuhan | Wajib? | Catatan |
|---|---|---|
| Windows 10/11 | Ya | Overlay berjalan di Windows |
| [Node.js](https://nodejs.org) 18+ | Ya | Cek dengan `node --version` |
| [Python](https://www.python.org) 3.11+ | Ya | Cek dengan `python --version` |
| Endpoint LLM kompatibel OpenAI | Ya | Bawaannya 9Router di `http://localhost:20128/v1`. Endpoint lain boleh, asal kompatibel OpenAI |
| Model avatar `.vrm` | Ya | Lihat langkah 3 |
| [VOICEVOX](https://voicevox.hiroshiba.jp) | Opsional | Tanpa ini Iris tetap menjawab lewat teks, tapi tidak bersuara |
| WSL2 + Hermes Agent | Opsional | Hanya untuk `/agen`. Lihat bagian 8 |

RAM 16 GB disarankan bila Hermes dan model lokal dijalankan bersamaan.

---

## 2. Unduh dan pasang

Buka PowerShell:

```powershell
git clone https://github.com/JihoStarting/iris-desktop-companion.git
cd iris-desktop-companion

npm install

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
```

Tanda virtual environment aktif adalah awalan `(.venv)` di prompt. Kalau `activate` bermasalah, panggil Python-nya langsung: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

---

## 3. Siapkan aset

Repositori **tidak menyertakan** model, animasi, dan suara karena ukuran dan lisensi. Buat folder `assets/` di akar proyek:

```
assets/
├── iris.vrm                 # model utama (wajib)
└── animations/
    └── idle_loop.vrma       # animasi idle (disarankan)
```

**Model VRM (wajib).** Simpan sebagai `assets/iris.vrm`. Kamu bisa:
- membuat sendiri dengan VRoid Studio lalu mengekspornya ke `.vrm`, atau
- memakai model dari sumber lain yang lisensinya mengizinkan penggunaan seperti ini.

Periksa syarat lisensi model sebelum memakainya, terutama bila hasilnya akan dibagikan.

**Animasi idle (disarankan).** File `.vrma` yang bernama `idle_loop.vrma` membuat gerakan badan lebih halus. Kalau file ini tidak ada atau gagal dimuat, Iris kembali ke gerakan prosedural bawaan, jadi aplikasi tetap jalan.

**Baju tambahan (opsional).** Satu file VRM per baju di `assets/`, misalnya `Iris_winter.vrm`, lalu daftarkan di array `OUTFITS` pada `index.html`.

**Klip gerak tambahan (opsional).** Letakkan file `.vrma` di `assets/animations/` dan daftarkan di `assets/animations/clips.json`. Tanpa ini Iris tetap bergerak memakai animasi idle.

---

## 4. Atur `.env`

Buka `.env` dengan editor teks. Pengaturan paling penting:

```ini
NINEROUTER_URL=http://localhost:20128/v1
NINEROUTER_API_KEY=isi-kunci-api-milikmu
NINEROUTER_MODEL=nama-model-atau-combo-milikmu
COMPANION_TOKEN=isi-token-acak
```

- `NINEROUTER_API_KEY` wajib diisi bila opsi "Require API key" di 9Router aktif. Kalau kosong, balasan akan `401 Missing API key`.
- `NINEROUTER_MODEL` harus cocok dengan nama model atau combo yang ada di endpoint-mu.
- `COMPANION_TOKEN` melindungi koneksi `/ws`. Buat nilainya dengan:

  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

Daftar lengkap variabel ada di [README](../README.md#konfigurasi).

> **Jangan pernah meng-commit file `.env`.** Isinya kunci API dan token milikmu. Berkas itu sudah dikecualikan lewat `.gitignore`.

> Server hanya membaca `.env` saat start. Setiap kali kamu mengubahnya, restart server dan overlay.

---

## 5. Jalankan VOICEVOX (opsional)

Buka aplikasi VOICEVOX dan biarkan berjalan. Iris mencari VOICEVOX di `http://127.0.0.1:50021` dan memakai speaker ID `2` secara bawaan. Ubah lewat `VOICEVOX_URL` dan `VOICEVOX_SPEAKER` bila perlu.

Bila VOICEVOX tidak berjalan, terminal server akan menampilkan `VOICEVOX gagal` berulang. Itu normal tanpa VOICEVOX dan tidak menghentikan obrolan.

---

## 6. Jalankan Iris

Buka dua terminal di folder proyek.

**Terminal 1: server**

```powershell
.\.venv\Scripts\python.exe server.py
```

**Terminal 2: overlay**

```powershell
npm start
```

Cek server dengan membuka `http://127.0.0.1:8765/health` di browser. Kalau tampil status sehat, server siap.

Alternatif: peluncur `IrisLauncher.exe` (lihat tab Releases di GitHub) menjalankan server, overlay, dan layanan pendukung sekaligus.

---

## 7. Coba pertama kali

Avatar akan muncul melayang di desktop. Ketik di kotak input overlay:

1. `Halo Iris` lalu tunggu balasan teks dan suara.
2. `/help` untuk daftar perintah.
3. `/timer 1 tes` untuk mencoba timer satu menit.
4. `/layar apa yang ada di layarku?` untuk mencoba penglihatan.
5. `Ctrl+Alt+T` untuk menerjemahkan teks di layar.

Klik kanan pada karakter untuk menu aksi cepat, dan pakai ikon tray untuk pengaturan.

### Kalau ada yang tidak jalan

| Gejala | Cek ini |
|---|---|
| Overlay muncul tapi tidak membalas | Server belum jalan, atau token `/ws` berbeda. Lihat log terminal server dan Electron |
| `401 Missing API key` | Isi `NINEROUTER_API_KEY` di `.env`, lalu restart |
| Log `/ws ditolak` | Token server dan overlay berbeda. Samakan, lalu restart keduanya |
| Iris diam tanpa suara | VOICEVOX belum berjalan di port `50021` |
| Karakter tidak tampil atau berupa kotak kosong | Pastikan `assets/iris.vrm` ada. Buka DevTools dengan `Ctrl+Alt+D` dan lihat tab Console |
| `127.0.0.1:8765` hanya menampilkan "Server Iris aktif" | Normal bila `COMPANION_TOKEN` aktif. Chat lewat overlay Electron, bukan browser |

Tabel masalah yang lebih lengkap ada di [README](../README.md#pemecahan-masalah).

---

## 8. Tambahan opsional: agen Hermes (`/agen`)

Fitur ini memberi Iris akses untuk mengerjakan tugas di komputermu, jadi pasang hanya kalau kamu paham risikonya.

1. Pasang WSL2 dan Hermes Agent, lalu aktifkan API server-nya (bawaan di `127.0.0.1:8642`).
2. Di `.env`, isi:

   ```ini
   HERMES_URL=http://127.0.0.1:8642/v1
   HERMES_API_KEY=sama-dengan-API_SERVER_KEY-di-Hermes
   HERMES_WIN_HOME=/mnt/c/Users/<nama-user-windows>
   ```

   `HERMES_WIN_HOME` penting karena Hermes berjalan di WSL, sehingga `~/Downloads` miliknya adalah folder Linux, bukan folder Download di Windows.
3. Restart server dan overlay.
4. Coba perintah aman dulu: `/agen sebutkan isi folder Download`.

Pengaman yang aktif: perintah berpotensi berbahaya (misalnya menghapus file) meminta konfirmasi dulu, ada tombol batal, dan ada batas waktu (`HERMES_TIMEOUT`, bawaan 120 detik).

Bila `/agen` membalas HTTP 503 atau tidak merespons, pastikan API server Hermes aktif dan `HERMES_API_KEY` sama dengan `API_SERVER_KEY`.

---

## 9. Langkah berikutnya

- Daftar perintah dan pintasan lengkap: [README](../README.md#perintah-chat)
- Pengaman dan model keamanan: [README](../README.md#keamanan)
- Mini-browser: ketik `/chrome`

Menemukan celah keamanan? Mohon jangan buka issue publik; hubungi pemilik repositori secara langsung.
