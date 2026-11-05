# Iris: Dokumen Gabungan (Overlay Desktop + Hermes Agent)

**by: KangJiho**

**Dimulai:** 28 Okt 2026 (overlay); Hermes dipasang 28 Sep 2026 (lihat S7)

**Digabung:** 30 Okt 2026
**Terakhir diperbarui:** 5 Nov 2026 (lihat Bagian U: perbandingan dengan proyek sejenis, rating, dan tier list kenaikan tingkat; sebelumnya Bagian T: riwayat repo diringkas jadi satu commit lewat force push, tag v1.0.0 dipindah, audit keamanan repo, perbaikan diagram README dan logo, audit berkas duplikat, dan keputusan soal pencarian catatan (RAG); sebelumnya Bagian S: README dan rilis v1.0.0 terkonfirmasi tampil di GitHub, penilaian repo, kronologi proyek, koreksi tanggal setup, dan pembersihan info pribadi; sebelumnya Bagian R: repo GitHub `iris-desktop-companion` dibuat dan di-push (private), audit privasi berkas, `HERMES_WIN_HOME` dipindah ke `.env`, README diperluas, Dependabot aktif, rilis `IrisLauncher.exe` v1.0.0 disiapkan; sebelumnya Q13: batas memori WSL diturunkan dari 5 GB ke 4 GB dan ditetapkan final, hasil ukur 3 GB dan 4 GB, RAM Windows 79% dengan Chrome ditutup; sebelumnya Q12: `.wslconfig` dipasang dan batas memori WSL 5 GB aktif, sparse VHD ditolak WSL, koreksi lokasi disk; sebelumnya Q11.10: perbaikan `iris-start.ps1` dan `IrisLauncher.exe` v1.0, Start berhasil di PC; sebelumnya Q11.9: pembungkus Hermes dan WSL, peluncur paralel, `iris-stop.ps1` kini mematikan semuanya, semuanya belum dites di PC; sebelumnya Bagian Q11: `9router.service` lulus tes dan aktif, token /ws disamakan, venv Linux, peluncur `iris-start.ps1` ditulis dan lulus tes dasar, pembungkus `.bat` klik-dua-kali; sebelumnya Bagian Q: keputusan skrip setup, cek kesehatan, dan auto-start; sebelumnya Bagian P: keputusan mengambil "menari mengikuti musik" dari Mate Engine; sebelumnya Bagian O: audit berkas, klien `iris_web.py`, dan data RAM tab parkir; sebelumnya 3 Nov, Bagian N: v46 sampai v51, termasuk jembatan Hermes baca-saja fase 5a; sebelumnya Bagian L dan M: mini-browser `/chrome` fase 0 sampai 4)
**Sumber:** `roadmap-ai-companion.md` (by KangJiho) dan `iris-system.md`

Iris saat ini hidup di dua tempat yang belum saling bicara. Dokumen ini menyatukan keduanya dan menambahkan rencana jembatan hybrid.

| Bagian | Isi | Peran |
|---|---|---|
| **A** | Roadmap overlay desktop (Electron, avatar VRM, VOICEVOX, `server.py`) | Wajah dan suara |
| **B** | Referensi sistem Hermes (skills, memori, terminal, Chrome, Telegram) | Tangan dan memori |
| **C** | Jembatan hybrid overlay ↔ Hermes (baru) | Penyambung |
| **D** | Catatan gabungan: selisih antar dokumen dan hal yang perlu dijaga | Pegangan |

## Progres terkini (31 Okt 2026)

**Ringkasan:** jembatan Hermes berfungsi dan sudah membuat file sungguhan, tapi di folder Linux milik WSL, bukan folder Windows (sudah diperbaiki di kode). Overlay kini punya tampilan baru, analisis gambar, screenshot layar, indikator "sedang mikir", dan bubble yang tetap tampil saat chat dibuka. Tandanya: **[dites]** = sudah dicoba dan terlihat jalan, **[belum dites]** = kode sudah ditulis dan lolos cek sintaks, tapi belum dicoba di komputer.

**Status uji terbaru (1 Nov 2026, sesi uji lanjutan).** Tabel ini yang berlaku kalau bertentangan dengan tanda `[belum dites]` di butir-butir lama di bawah (tanda lama sengaja tidak diubah satu per satu). Hasil dilaporkan pemilik; tidak semua rincian per butir dicatat, dan bukti dari screenshot disebut kalau ada.

| Paket / fitur | Hasil | Bukti dan catatan |
|---|---|---|
| v16, mood (`/mood`, level, kalimat sesuai level) | **lulus** | Screenshot: kartu "Mood Iris: murung (32/100)" dan kalimat "Lagi agak murung..." sesuai level. Naik, turun, dan sapaan kembali dinyatakan aman oleh pemilik |
| v17, garis petunjuk bar | **lulus** | Dilaporkan pemilik |
| v21 sampai v23 (bayangan, pose diangkat, duduk di tepi jendela, dua cara mengangkat) | **lulus** | Dilaporkan pemilik |
| v24 sampai v27 (thumbnail dan penampil gambar besar, benturan sisi layar, ganti baju, fun fact, tampilan badan, bubble) | **lulus** | Dilaporkan pemilik. Screenshot: bubble di atas kepala, tubuh penuh sampai kaki |
| v28, seret file ke overlay (kunci navigasi) | **lulus** | Screenshot: area drop putus-putus dan lampiran masuk; halaman tidak pindah |
| v28, penampil gambar besar dan `Ctrl+Alt+D` | **lulus** | Screenshot DevTools `app://local/index.html` terbuka (DevTools lolos dari kunci navigasi) |
| v28b, tombol Salin dan hasil tempel (`Ctrl+V`) | **lulus** | Dilaporkan pemilik |
| v28, suara per emosi | **lulus** | Dilaporkan pemilik. Angka `EMO_VOICE` masih bisa disetel kalau ada emosi yang terlalu kuat atau lemah |
| Jembatan Hermes: cancel, timeout, heartbeat, tes `/agent` ke folder Windows | **lulus** | Dilaporkan pemilik. Rincian (apakah agen Hermes benar-benar berhenti saat cancel, path `C:\Users\...` di kartu hasil) belum dicatat |
| v18, gerak halus (pegas, crossfade) dan gerbang emosi ke klip | belum dites | |
| v28c, bubble tidak terpotong saat ada lampiran | kode ditulis, **belum dites** | Lihat "Pembaruan v28c" |
| v28e, dock (pil status dan lampiran sejajar) | **lulus** (posisinya diperhalus di v28f sampai v28h, lihat baris di bawah) | `index.html` dan `main.js` yang diunggah 1 Nov sudah memuat v28b, v28c, v28e (patch gabungan ditolak `patch` karena terdeteksi sudah terpasang); `node --check` lolos |
| Web search Hermes (H5 no. 1) | **lulus** | 1 Nov: `config.yaml` berisi `web.backend: exa`, `provider_tier: exa: free`; tes lewat API server HTTP 200, Hermes menyebut `web_search` dan memberi URL. Lihat "Pembaruan v29 dan v30" |
| v29, perbaikan baris yang melanggar format | kode ditulis, **belum dites** | `py_compile` lolos; belum dijalankan di PC |
| v30, laporan agen netral dan bersumber | kode ditulis, **belum dites** | `py_compile` dan uji `format()` prompt lolos; belum dites dengan Hermes asli |
| v30b, atribusi jujur laporan agen | **lulus** | Dinyatakan aman oleh pemilik (1 Nov malam) setelah `server.py` di-restart. Rincian per butir tidak dicatat |
| Pil status tugas, posisi (v28f sampai v28h) | **lulus** | Mode biasa: di kiri, rata dengan tepi kiri bar input, ringkas supaya tidak menimpa rok karakter. Mode fokus: di tengah, tepat di atas garis petunjuk (di atas bar kalau bar sedang tampil). Dinyatakan sesuai oleh pemilik. Riwayat salah paham ada di I10 |
| v33, popup Salin link di chat | **lulus** | Screenshot 1 Nov malam: pil "Salin link" muncul di atas `https://www.kompas.com` di kartu "Hasil tugas", kurung penutup di baris bawah tidak ikut ke link. Hasil tempel utuh tanpa tanda baca tambahan (dikonfirmasi pemilik) |
| v33, tombol memanjangkan kotak chat | **lulus** | Dua screenshot: kotak pendek (dua paragraf terlihat) dan kotak panjang (seluruh balasan terlihat), karakter tidak bergeser dan bar input tidak bertumpuk. Belum dicatat: ukuran kembali setelah chat ditutup, dan perilaku dekat tepi atas layar (tombol berkedip ✕) |
| v33b, Console DevTools | **lulus** | Screenshot: "No issues". Tidak ada 404 `clips.json`, `THREE.Clock`, atau `VRMLookAtQuaternionProxy`. `clips.json` terpasang (3 byte). Lima baris sehat, lihat I11 |
| v32, galat model gambar (`server.py`) | **lulus** (galat dan retry); tes gambar normal **belum dikonfirmasi** | 1 Nov malam, batas 3 detik dan 4 gambar: bubble menampilkan "Model gambar tidak menjawab dalam 3 detik, coba lagi atau kurangi jumlah gambar."; terminal mencetak `[llm] ReadTimeout dari Iris: ''; mencoba sekali lagi` lalu `galat final`. Server sudah dijalankan ulang tanpa variabel 3 detik, hasil kirim gambar normal belum dilaporkan |
| v34, konfirmasi `/agen` berbahaya (Keamanan agen 2a) | **lulus** | Dites pemilik di PC dengan `/agen hapus file tes.txt di Download` (1 Nov malam), dinyatakan bisa. Rincian per langkah (Batal, Jalankan, tugas aman tanpa kartu) tidak dicatat. Sebelumnya lolos di luar PC: `py_compile`, `node --check`, 22 kasus pencocokan kata, simulasi WebSocket 10 skenario, uji DOM tiruan. Lihat I11 |
| v37, pilihan bernomor dan gema perintah `/` (`index.html`) | **lulus** | Dinyatakan pemilik bisa semua (1 Nov): `/baju`, `/alarm`, `/lokal daftar` dengan angka. Lihat I12 |
| v37b, soal `/belajar` menampilkan kalimat Jepang di chat (`server.py`) | **lulus** | Screenshot 1 Nov: kalimat 「すしが好きです。」 tertulis di gelembung chat bersama pertanyaannya. Lihat I12 |
| v37c, galat `/pantau` tidak muncul tiba-tiba (`server.py`) | **lulus** | Dinyatakan pemilik bisa (1 Nov) |
| v37d, pemulihan renderer/WebGL dan batas memori (`index.html`, `main.js`) | **lulus** (pengamatan lanjut) | Dinyatakan pemilik bisa (1 Nov). Ngilang bersifat sesekali, jadi pantau beberapa hari; kalau terulang lihat terminal Electron |

Temuan terbuka dari sesi ini:
- [x] DevTools menunjukkan **1 error dan 2 warning**; isinya sudah dibaca (1 Nov malam): 404 `clips.json`, `THREE.Clock` deprecated, `VRMLookAtQuaternionProxy`. Perbaikan v33b menunggu tes ulang (Console harus bersih) Tes ulang lulus (1 Nov malam): Console bersih.
- [ ] Tes v28c (bubble dengan 0 sampai 4 lampiran, chat terbuka, dekat tepi atas layar)
- [x] Tes v28e (dock: pil status dan lampiran sejajar di atas bar; menggantikan v28d): lulus, posisi pil diperhalus di v28f sampai v28h
- [x] Tes v32, bagian galat dan retry: lulus (1 Nov malam, lihat I11)
- [ ] Tes v32, gambar normal: kembalikan `NINEROUTER_VISION_READ_TIMEOUT` ke bawaan (jendela PowerShell baru, `.\.venv\Scripts\python.exe server.py`), kirim gambar (boleh 4), Iris harus menjelaskan isinya dalam 90 detik; belum dikonfirmasi
- [x] Tes v33: popup Salin link dan tombol ⇅ lulus (1 Nov malam). Sisa kecil yang belum dicatat: ukuran kembali setelah chat ditutup, dan tombol berkedip ✕ dekat tepi atas layar
- [x] Tes v34: lulus (1 Nov malam, `/agen hapus file tes.txt di Download`, dinyatakan bisa oleh pemilik; rincian per langkah tidak dicatat, lihat I11)
- [x] Tes v37: lulus (1 Nov, dinyatakan pemilik). `/baju` lalu ketik `3` (baju berganti, bukan dibalas Iris sebagai obrolan); `/alarm` lalu ketik nomor (alarm terhapus); `/lokal daftar` lalu ketik nomor aplikasi (aplikasi terbuka); `/baju` tanpa dipilih lalu ketik kalimat biasa (jadi obrolan normal); lihat I12
- [x] Tes v37b: lulus (1 Nov, kalimat soal `/belajar` kini tertulis di chat)
- [x] Tes v37 bagian `/lokal daftar` lalu angka: lulus (1 Nov), dibuktikan screenshot: ketik `3`, muncul gelembung `buka task manager`, Iris menjawab "Membuka task manager.", dan Task Manager terbuka; angka 3 tidak dijawab sebagai obrolan. Kasus lama "15? Kirain bahasa apaan..." tidak terulang; dugaan awal (jawaban untuk "15" yang terkirim lebih awal dengan `main.js` lama) tidak dibantah.
- [x] Tes v37c dan v37d: lulus menurut pemilik (1 Nov). v37d perlu pengamatan lebih lama karena ngilang terjadi sesekali.
- [ ] Tes v29: kirim pesan umum (mis. soal lagu); baris tanpa `|||` harus tetap bersuara dan terminal mencetak `baris diperbaiki`; klik Hapus dulu supaya riwayat lama tidak memengaruhi
- [x] Tes v30 dan v30b: dinyatakan aman oleh pemilik (1 Nov malam)
- [ ] `Hermes membalas HTTP 503` (screenshot 1 Nov): penyebab **belum dipastikan** (dugaan: model di belakang Hermes gagal, atau tugas lama masih menggantung karena cancel tidak menghentikan agen). Perlu log `hermes gateway` saat error dan tes `curl` langsung ke `127.0.0.1:8642`
- [ ] Kalau laporan `/agen` masih bergaya Iris: `hermes skills config` per platform (lihat v30)
- [ ] **`/agent` untuk tugas sepele lambat** (`/agent 17 dikali 7 berapa`, 1 Nov 09:16): terminal server hanya mencetak "Hermes mulai" dan pil "Masih memproses..." bertahan lama. Pembanding: tes manual Tahap 1 (daftar folder) sekitar 11 detik. Langkah: (1) tunggu baris `total X detik (Hermes Y, Iris + suara Z)` di terminal server, (2) ukur panggilan langsung ke `127.0.0.1:8642` dari PowerShell, (3) bandingkan dengan `$env:IRIS_SAVE_SCREEN="0"` (dugaan: screenshot terakhir dan 10 pesan konteks ikut ke Hermes dan membuatnya lambat; belum terbukti)

Jembatan Hermes (`/agen`, `/agent`, `/h`):
- [x] Tahap 0 sampai 3: API server Hermes aktif (v0.22.2, `127.0.0.1:8642`), `server.py` dengan jembatan, kalimat pembuka Iris, penanganan error, `/health` ikut mengecek Hermes **[dites]**
- [x] Uji awal: `/agen sebutkan isi folder ~/hermes-test` dan `/agen cari file test_client.html di /mnt/z/Projek AI waifu Dekstop` berhasil **[dites]**
- [x] Kartu "Hasil tugas" dengan tombol Salin di panel chat: laporan mentah Hermes tampil apa adanya dan bisa disalin **[dites]**
- [x] Perintah `/agen` tidak lagi dibungkus "Mode jelaskan" (sebelumnya awalan tidak terdeteksi, pesan jadi obrolan biasa, dan Iris berpura-pura mengerjakan). Server juga mengenali pesan yang sudah terbungkus **[belum dites]**
- [x] Iris mengingat hasil tugas agen terakhir untuk pertanyaan lanjutan ("lokasinya di mana?"), dan dilarang menyebut tugas yang sudah jalan sebagai gurauan **[belum dites dengan Hermes asli]**
- [x] Hermes menerima 10 pesan terakhir obrolan overlay sebagai konteks, dipakai hanya kalau tugas merujuk ke percakapan ("yang kita bahas") **[belum dites dengan Hermes asli]**
- [x] Hermes diberi tahu folder Windows (`HERMES_WIN_HOME`, bawaan `/mnt/c/Users/<user>`) dan dilarang memakai `~/Downloads` milik WSL. Path WSL di laporan otomatis diubah jadi path Windows (`C:\Users\...`) **[belum dites dengan Hermes asli]**
- [x] Prompt hasil dirapikan: tidak mengulang kalimat pembuka, tidak menilai tugas "cepat" atau "lama", dan hanya menyatakan berhasil kalau laporan Hermes jelas menyatakannya **[belum dites]**
- [x] Iris di obrolan biasa dilarang mengaku bisa membuat, mengubah, atau menghapus file; ia diminta menyuruh memakai `/agen` **[belum dites]**
- [x] Log waktu di terminal: `total X detik (Hermes Y, Iris + suara Z)` untuk mencari bagian yang lambat **[belum dites]**
- [x] Indikator "sedang mikir": label status dengan hitung detik, avatar bergaya `think` selama menunggu, dan pesan akhir untuk gagal, timeout, atau dibatalkan **[belum dites]**
- [x] Tes `/agent buat file tst.txt isinya "halo" di folder Download`: path di kartu hasil harus berawalan `C:\Users\<user>\Downloads\` dan file harus muncul di Explorer **(dinyatakan lulus pemilik, 1 Nov; lihat Status uji terbaru)**
- [ ] Pindahkan file lama `/home/<user>/Downloads/tst` ke folder Download Windows (lihat di Explorer lewat `\\wsl$`)
- [ ] Konfirmasi suara Metan keluar saat menyampaikan hasil, dan tidak ada suara dobel dari sisi Hermes
- [x] Uji gagal (Hermes dimatikan) dan pembatalan: pesan error ramah dan `interrupted: true` terbukti (31 Okt), tapi agen Hermes tetap jalan setelah cancel; lihat Bagian G, Poin C. Tombol Stop di overlay sungguhan **[belum dites]**
- [ ] Tugas nyata pertama: skill `cek-elearning`
- [ ] Deteksi otomatis kata kerja aksi tanpa awalan `/agen` (Tahap 6): ditunda karena salah rute berisiko, sementara Iris menolak berjanji


Pengerasan dan verifikasi jembatan (30 Okt sampai 1 Nov 2026; rincian di Bagian G):
- [x] Server hanya bind `127.0.0.1`; `.env` dipindah ke `~/.env` (di Windows: `C:\Users\<user>\.env`), `.env` lama di Z: dihapus, tersisa `.env.example` **[dites]**
- [x] Penyebab 401 ditemukan: `NINEROUTER_API_KEY` kosong (bukan gateway Hermes); chat biasa jalan lagi dari server Windows **[dites]**
- [x] Server: pesan `status`, heartbeat 30 detik, status akhir di `finally`, teks cancel jujur "tugas mungkin masih berjalan", `HERMES_TIMEOUT` lewat `env_float()`; kode overlay `onStatus()` juga sudah ada **[kode ada; dites hanya dengan Hermes tiruan, belum dengan Hermes dan overlay sungguhan]**
- [ ] Cancel yang benar-benar menghentikan agen di sisi Hermes, tes `/agen` + timeout + heartbeat dengan Hermes sungguhan, tes hapus `tes.txt`, cek apakah Z: tersinkron ke cloud (lihat Bagian G)

Overlay:
- [x] Analisis gambar: backend menerima field `images`, mengubahnya jadi pesan multimodal, memakai `NINEROUTER_VISION_MODEL` (kosong = model biasa), dan tidak menyimpan data gambar di riwayat. Pesan bergambar selalu lewat jalur chat (Hermes tidak ikut melihat gambar) **[dites: Iris menjelaskan isi screenshot yang dikirim]**
- [x] Tampilan baru: bar input berbentuk kapsul dengan ikon SVG, bubble solid dengan warna dan cahaya sesuai emosi, panel chat dengan tombol geser "Mode jelaskan" dan animasi pesan **[dites: terlihat di screenshot]**
- [x] Bubble tetap tampil saat chat dibuka: bubble melayang di atas kepala (tidak memakan tempat di layout), dan jendela memanjang 160 px ke atas saat chat dibuka lalu kembali saat ditutup (`CHAT_GROW` di `main.js`, tinggi `#log` di `index.html`) **[belum dites]**
- [x] Screenshot layar: tombol kamera, `Ctrl+Alt+S`, atau menu tray. Overlay disembunyikan sekitar 0,2 detik, layar tempat overlay berada dipotret (sisi terpanjang 1600 px), dan hasilnya jadi lampiran **[belum dites]**
- [x] Gerakan lengan dimatikan secara bawaan (`ARM_GEST = 0`), peluang gerakan saat bicara turun ke 35%, jeda gerakan idle 20 sampai 40 detik. Coba lengan lagi lewat konsol: `setArmGest(0.3)` **[belum dinilai]**
- [ ] Nilai apakah gerakan sekarang terasa natural, lalu naikkan `setArmGest` pelan-pelan
- [x] Gerakan v3 (`index.html`): tatapan mata lebih tenang (menetap 1,3 sampai 4,5 detik, lirikan ke kursor dibatasi sekitar 27 derajat, kepala ikut sedikit ke arah lirikan), kepala saat bicara mengikuti energi suara (bukan goyang sinus konstan), pose `think` ditahan selama tugas agen berjalan (dulu diputar ulang tiap sekitar 4 detik), gerakan ditulis ulang supaya terbaca tanpa lengan (kepala, mata, bahu, napas; `stretch` dihapus; `tilt` dan `sigh` baru), tidak mengulang gerakan sama berturut-turut, kedip asimetris dengan kedip dobel kadang-kadang **[belum dites visual]**

Paket v21 sampai v22 (31 Okt 2026; berkas berubah: `main.js`, `preload.js`, `index.html`; lolos cek sintaks; hasil visual dinilai pemilik lewat screenshot, bagian v22 **[belum dites]**; rincian di "Pembaruan v21 sampai v22" dan "Uji v21 sampai v22" di bawah):
- [x] v21, sembunyi di tepi layar (`/sembunyi`, menu klik kanan, tray): jendela digeser ke tepi kiri atau kanan, posisi asal diingat dan tidak ikut tersimpan (`savePos`), muncul lagi saat kursor menempel atau diklik, sembunyi lagi otomatis kalau dibiarkan **[dites sebagian: terlihat di screenshot]**
- [x] v21b, mengintip lebih natural: bubble, bar, status, dan kapsul timer disembunyikan selama mengintip (sebelumnya bubble sapaan tertinggal dan terpotong tepi layar); badan condong ke dalam layar dengan pivot di kaki (di dalam three.js lewat grup `peekPivot`, bukan CSS, supaya hit-test piksel tetap akurat); mata menatap ke dalam layar; `PEEK_CUT` bawaan diubah supaya yang terlihat lebih sedikit **[dites sebagian: terlihat di screenshot]**
- [x] v21c, "kaki hilang": kanvas karakter berhenti di rok dan ada ruang kosong sekitar 70 px di bawahnya (tempat bar), jadi potongan jatuh melayang di tengah layar. Sekarang jendela turun ke dasar area kerja saat mengintip dan karakter turun sebesar ruang kosong itu (`--peek-drop`), jadi potongan bawah = dasar layar **[dites sebagian]**
- [x] v21d, bayangan siluet saat mengintip (`filter: drop-shadow`), kemiringan 0,35 rad, badan digeser ke tepi supaya kepala tidak terpotong kanvas (`setPeekLean`, `setPeekShift`, `setPeekShadow` di konsol; `IRIS_PEEK_CUT` di env) **[belum dinilai setelah perubahan ini]**
- [x] v21e, dilepas dekat tepi layar (tengah karakter <= 70 px dari tepi monitor) = langsung bersembunyi di tepi itu dan mode mengintip nyala; diseret keluar = mode mati. Bayangan saat diangkat **[belum dites]**
- [x] v22, bayangan permanen (`/bayangan nyala|mati` atau saklar di Pengaturan, bawaan nyala): parameter bayangan berubah per keadaan (diam, diangkat, mengintip, duduk). Kualitas HD: buffer render minimal 2x (`setPixelRatio(max(dpr, 2))`, maks 3x) dan blur halus **[belum dites]**
- [x] v22, pose diangkat (gambar 1 referensi): digantung seperti dijinjing di tengkuk. Badan berayun seperti bandul dengan titik gantung di kepala (`headRestY`), lengan terkulai dan mengayun berlawanan arah gerak, bahu naik. Kecepatan jendela dikirim `main.js` ke renderer (`drag-vel`) **[belum dites]**. Kaki tidak terlihat karena model dipotong di rok (v26: kamera kini bisa menampilkan tubuh penuh, lihat saklar "Tampilan")
- [x] v22, duduk di tepi atas jendela lain (gambar 2 referensi), Paket 4: `/duduk nyala|mati` atau saklar "Duduk di tepi jendela" di Pengaturan, **bawaan mati** (saklar privasi). Posisi dan ukuran jendela dibaca lewat proses PowerShell yang tetap hidup (`EnumWindows`, bingkai DWM); judul, nama proses, dan isi jendela TIDAK dibaca **[belum dites di Windows]**
- [ ] Tangan memegang tepi saat bersembunyi total (gambar 1 referensi, mode bersembunyi dengan hanya jari terlihat): butuh klip VRMA pose pegang tepi, jadi menunggu paket klip CC0
- [ ] Tepi atas dan bawah layar untuk sembunyi (sekarang hanya kiri dan kanan)

Paket v28 (1 Nov 2026; berkas berubah: `server.py`, `main.js`; `index.html` dan `preload.js` tidak berubah; lolos `py_compile` dan `node --check`, diuji dengan dependensi dan Electron tiruan; **token `/ws` dan `/agen` sudah dites di PC sungguhan (1 Nov, lulus); kunci navigasi dan gaya suara belum**; rincian di "Pembaruan v28" dan "Uji v28" di bawah, selisih lengkap di `iris-v28.patch`):
- [x] v28, token `/ws`: kalau `COMPANION_TOKEN` diisi di `.env`, server menolak koneksi tanpa header `X-Iris-Token` yang sama (kode 1008), termasuk klien tanpa header `Origin` yang dulu selalu lolos. `main.js` membaca token dari environment atau `~/.env` dan menempelkannya ke handshake WebSocket; renderer tidak pernah melihatnya. Kosong = perilaku lama + peringatan di terminal. `/health` menampilkan `ws_token` aktif atau KOSONG **[dites 1 Nov di PC sungguhan: curl tanpa token 403, dengan token 101; overlay tersambung dan `/agen` dijawab]**
- [x] v28, kunci navigasi di `main.js`: semua jendela (termasuk penampil gambar besar) menolak jendela baru, `will-navigate`, `will-redirect`, dan `<webview>`; DevTools dikecualikan **[belum dites di overlay sungguhan]**
- [x] v28, gaya suara per emosi: kecepatan, nada, dan intonasi VOICEVOX menyesuaikan emosi kalimat (`EMO_VOICE`); lip-sync ikut kecepatan baru; cache suara lokal per (emosi, kalimat); matikan dengan `IRIS_VOICE_STYLE=0`; speaker khusus emosi opsional lewat `VOICEVOX_SPEAKER_<EMOSI>` **[belum didengar; angka awal tebakan konservatif]**
- [x] v28b, perbaikan tombol **Salin** di penampil gambar (`main.js`, selisih di `iris-v28b.patch`): tombol sempat menampilkan "Gagal menyalin (restart Iris; cek terminal)" karena terminal menulis `copy-image gagal: clipboard.writeImage is not a function` (Electron di PC ini tidak punya fungsi itu; bukan akibat v28, handler asli sama). Sekarang handler mencoba berurutan `clipboard.writeImage`, `clipboard.write({image})`, lalu PowerShell (`Clipboard.SetImage` dari PNG sementara) **[10 pemeriksaan lulus dengan Electron dan PowerShell tiruan; di PC sungguhan tombol menjadi "Tersalin ✓"; hasil tempel (Ctrl+V) dan cabang mana yang dipakai belum dilaporkan]**
- [x] Token dibuat dan diisi di `C:\Users\<user>\.env`, kedua berkas diganti, server dan overlay direstart (1 Nov); token pertama yang sempat tampil di layar tidak dipakai. Sisa Uji v28: seret file ke overlay, penampil gambar besar dan Ctrl+Alt+D, suara tiap emosi
- [x] Dengarkan tiap emosi dan laporkan mana yang terlalu kuat atau lemah; kalau mau gaya Metan lain, catat id dari `http://127.0.0.1:50021/speakers` **(lulus 1 Nov, dilaporkan pemilik; angka masih bisa disetel)**

Paket v27 (1 Nov 2026; berkas berubah: `server.py`, `index.html`; `server.py` lolos `py_compile` dan handler baru diuji dengan LLM tiruan; rincian di \"Pembaruan v27\" dan \"Uji v27\" di bawah):
- [x] v27, fun fact buatan model: Iris meminta satu fakta ke model (9Router, jalur yang sama dengan `/belajar`, bukan agen Hermes) lewat pesan WebSocket baru `funfact`. Topik diatur dengan `/funfact topik <topik>` atau kolom \"Topik\" di Pengaturan; saklar \"Fakta dibuat model\" (bawaan nyala). Server mati, balasan salah format, atau lebih dari 25 detik (server) / 30 detik (overlay) = otomatis memakai 30 fakta bawaan, tanpa pesan galat. `/funfact bawaan` memaksa daftar bawaan saja, `/funfact model` mengembalikannya **[handler server diuji dengan LLM tiruan; end-to-end di PC belum dites]**

Paket v26 (1 Nov 2026; berkas berubah: `index.html` saja; lolos cek sintaks `node --check`; rincian di "Pembaruan v25 dan v26" dan "Uji v26" di bawah):
- [x] v25, ganti baju (maid bawaan, gaun pesta prom, seragam sekolah): tiga jalur, yaitu menu klik kanan "Ganti baju", dropdown "Baju" di Pengaturan, dan `/baju [nomor|nama]`. Pilihan disimpan di `localStorage` (`iris.outfit`); file VRM hilang = kembali ke baju bawaan **[dites: ganti ke seragam sekolah terlihat di screenshot]**
- [x] v26, fun fact acak: Iris menyebut satu fun fact bersuara di waktu acak antara 5 dan 60 menit. 30 fakta bawaan (teks Indonesia + kalimat Jepang untuk VOICEVOX), dikocok dan dihabiskan dulu sebelum ada yang diulang. Bawaan **nyala**; saklar dan rentang menit di Pengaturan, atau `/funfact [sekarang|10-30|20|mati|nyala]`. Tidak muncul saat mode fokus, tidur, bicara, merekam, chat terbuka, mengetik, atau di tepi layar (tertunda = dicoba lagi 30 detik) **[belum dites]**
- [x] v26, tampilan badan: dropdown "Tampilan" di Pengaturan (Setengah badan = dari pinggang ke atas seperti dulu; Tubuh penuh = sampai kaki, bawaan) dan `/badan [penuh|setengah]`. Kamera dihitung ulang tanpa restart **[dites: kaki terlihat di screenshot]**. Catatan: gaun prom panjang, jadi kakinya tetap tertutup rok
- [x] v26, bubble tidak lagi menutupi kepala: dasar bubble kini dihitung dari puncak kepala di layar (`updateBubbleOver`, diperbarui saat kamera atau tinggi kotak berubah), bukan 90 px tetap **[dites: bubble di atas kepala di screenshot]**
- [x] v26, panel Pengaturan diringkas (lebar, jarak baris, huruf, kolom angka; baris "Acak dari/sampai" digabung jadi satu) **[dites lewat screenshot]**. Lalu semua panel (menu, Timer, Ganti baju, Pengaturan) ditempel ke tepi kiri jendela dan dipersempit jadi 196 px supaya tidak menimpa badan **[belum dites]**
- [x] v26, daftar klip VRMA bawaan (`DEFAULT_CLIPS`) dikosongkan: tidak lagi mencari `VRMA_02.vrma` dan `VRMA_03.vrma` yang memang tidak ada, jadi galat `app:// file tidak ditemukan` hilang. Sapaan gerak dan pose peace baru aktif kalau file `.vrma` diletakkan dan `DEFAULT_CLIPS` atau `clips.json` diisi **[belum dites]**

Paket v24 (1 Nov 2026; berkas berubah: `main.js`, `preload.js`, `index.html`; lolos cek sintaks; rincian di "Pembaruan v24" dan "Uji v24" di bawah):
- [x] v24, thumbnail lampiran screenshot diperbesar (52 px jadi 88 px) dan bisa diklik untuk dilihat besar. Sebelumnya tidak bisa dibuka sama sekali **[belum dites]**
- [x] v24, tombol "Buka besar" (atau klik dua kali gambar) di penampil gambar membuka jendela terpisah hampir seukuran layar dengan zoom roda mouse, geser, klik dua kali = ukuran asli. Alasan: penampil lama ada di dalam overlay selebar 440 px, jadi gambar dikecilkan paksa dan tampak buram **[belum dites]**
- [x] v24, tombol "Salin gambar" diperbaiki: penyebab asli `clipboard.writeImage is not a function` (tidak ada di versi Electron yang dipakai), kini memakai `clipboard.write({ image })`. Alasan gagal dicetak di terminal **[belum dites; perbaikan dikirim setelah log galat]**
- [x] v24, benturan ke SISI layar (kiri, kanan, atas, bawah) ikut memicu reaksi sakit dan suara, bukan hanya pojok **[belum dites]**
- [x] v24, file `app://` yang tidak ada dibalas 404 biasa (bukan `net::ERR_FILE_NOT_FOUND` di terminal); yang dilaporkan hanya file selain `favicon.ico` dan `clips.json`
- [x] Temuan: `assets/animations/VRMA_02.vrma` (greet) dan `VRMA_03.vrma` (peace) tidak ada; Iris memakai gerakan bawaan sampai file diletakkan. **Ditangani di v26**: daftar bawaan dikosongkan, galat hilang; klip baru aktif kalau file tersedia
- [x] Selesai (dikonfirmasi pengguna, 1 Nov 2026: sudah aman): Snipping Tool (Win+Shift+S) dilaporkan tidak jalan saat overlay hidup; penyebab belum dipastikan (dugaan: `setAlwaysOnTop(true, 'screen-saver')`). Langkah berikutnya: uji tutup Iris lalu Win+Shift+S, lalu pertimbangkan level `floating`

Paket v23 (31 Okt 2026; berkas berubah: `main.js`, `preload.js`, `index.html`; lolos cek sintaks; **[belum dites]**; rincian di "Pembaruan v23" dan "Uji v23" di bawah):
- [x] v23, dua cara mengangkat Iris, masing-masing punya saklar di Pengaturan: **Angkat dari karakter** (tekan dan geser badan; mati = tidak bisa diangkat dari badan, elus dan colek tetap jalan) dan **Angkat dari tombol ✥** (grip di bar; mati = tombol redup dan tidak bisa menyeret). Keduanya bawaan nyala dan tidak bisa mati bersamaan (satu selalu tersisa supaya Iris tidak terkunci). Perintah `/angkat [mati|nyala]` untuk saklar karakter **[belum dites]**
- [x] v23, panel kecil (Pengaturan, Timer) bisa di-scroll: tingginya dibatasi `calc(100vh - 140px)` dengan scrollbar tipis; sebelumnya baris paling bawah Pengaturan terpotong setelah ditambah dua saklar baru **[belum dites]**
- [x] v23, `/duduk nyala` (atau saklar "Duduk di tepi jendela") langsung memindahkan Iris ke tepi atas jendela terdekat yang layak. Sebelumnya saklar hanya mengaktifkan fitur dan Iris baru duduk kalau dilepas dalam 70 px dari tepi atas jendela, jadi tampak tidak bereaksi. Perintah baru `/duduk sini` untuk memaksa naik lagi saat saklar sudah nyala **[belum dites]**

Paket v19 dan v20 (31 Okt 2026):
- [x] v19, seret karakter langsung, reaksi bersuara saat diangkat dan dilepas, saklar "Selalu di atas" (`/atas`) **[dites: jalan]**. Butir uji v19 lain (tepi layar, monitor lain, skala tinggi, seret saat chat terbuka, elus kepala) belum dicatat hasilnya
- [x] v20, Paket 2 (hanya `index.html` yang berubah): `/alarm HH:MM [nama]` (daftar lewat `/alarm`, hapus lewat `/alarm batal <no|semua>`), `/jam`, dan ucapan jam tiap jam (`/jam nyala|mati` atau saklar di Pengaturan, bawaan mati) **[dites: jalan]**. Rincian di F7 dan "Uji v20"
- [x] Perbaikan F3 (`main.js`, `index.html`, `requirements.txt`): item tray "Mode fokus (nyala / mati)" dan `faster-whisper` ditambahkan ke `requirements.txt` sebagai opsional **[belum dites]**

Paket v17 dan v18 (31 Okt 2026, hanya `index.html` yang berubah; semua **[belum dites]**: lolos cek sintaks, pegas diuji numerik, belum dicoba di overlay; rincian di "Pembaruan v17 dan v18" di bawah):
- [x] v17, garis petunjuk bar dibuat ulang: kapsul kaca hijau-mint dengan cahaya berlapis dan pantulan, satu keluarga dengan kapsul biru Mode fokus. Berubah sesuai keadaan: kursor mendekat (melebar), agen bekerja (cyan-biru, aliran cepat), server mati (merah, berdenyut cepat) **[belum dites]**
- [x] v18, gerak halus: tiap tulang mengejar target lewat pegas teredam kritis dengan batas kecepatan sudut (lengan 2,2, kepala dan leher 1,6, badan 1,2 rad/s); masuk/keluar gerakan memakai smootherstep; gerakan yang diganti memudar 0,5 detik (crossfade) **[belum dites visual]**
- [x] v18, gerbang emosi ke gerakan (`GATE`): peluang bergerak per emosi, kalimat galat tidak memicu, jeda antar klip, klip besar dibatasi **[belum dites]**
- [x] v18, klip VRMA aksi dari `assets/animations/` (daftar default atau `clips.json`), diputar lewat mixer yang sama dengan animasi idle **[belum dites; file klip belum disiapkan]**
- [ ] Siapkan file klip: pilih dari paket gerakan CC0 open-annie atau konversi Mixamo; pack VRoid hanya pose
- [ ] Uji v17 dan v18 (lihat "Uji v17 dan v18", nomor 21 sampai 24)

Paket v16 (31 Okt 2026, semua **[belum dites]**; rincian di bagian "Pembaruan v16" di bawah):
- [x] Mood Iris yang bertahan antarhari: skor tersimpan, memengaruhi ekspresi, ambang ngambek, sapaan saat kembali, dan nada bicara; `/mood`, saklar di Pengaturan (`index.html`, `server.py`)
- [x] Gambar di chat bisa diklik: tampilan besar dengan Salin gambar, Simpan, Tutup (`index.html`; Salin lewat IPC `copy-image` di `main.js` dan `preload.js`)
- [x] Iris dan Hermes tidak menanyakan lagi hal yang sudah disebut (nama game), isi layar dan screenshot terakhir ikut ke Hermes, Hermes dilarang bertanya balik (`server.py`)
- [x] Mode fokus menyisakan hanya garis hijau; karakter dan bubble hilang total dan klik tembus (`index.html`)
- [ ] Uji v16 sampai v16d (lihat "Uji v10 sampai v16", nomor 16 sampai 19)
- [x] Penyelarasan berkas (31 Okt 2026): `server.py` yang diunggah ternyata belum memuat v12 sampai v14 (`/ingat`, `/memori`, `/lupa`, `/belajar`, pesan `stt`), padahal `index.html` sudah memanggilnya. Ketiganya sekarang ditulis di `server.py` sesuai deskripsi v12, v13, dan v14 di bawah. Diuji terpisah lewat WebSocket tiruan (LLM dan VOICEVOX palsu): memori (simpan, tolak rahasia, duplikat, daftar, hapus), alur soal-jawab dan menyerah `/belajar`, penolakan saat balasan berjalan, STT sukses dan gagal. **[belum diuji dengan model, suara, dan mikrofon asli]**. Berkas patch: `server-v12-v14.patch` (terhadap `server.py` yang sudah memuat mood dan perbaikan Hermes)

Paket fitur v6 (31 Okt 2026, semua **[belum dites]**: kode lolos cek sintaks, belum dicoba di Electron; file berubah: `index.html`, `main.js`, `preload.js`, dan `server.py` (pesan `speak`, lihat di bawah); colek, sapaan, dan Mode fokus sudah terlihat jalan di screenshot:
- [x] Menu aksi cepat: klik kanan karakter (atau tray "Menu aksi cepat") membuka daftar Chat, Screenshot, Clipboard, Timer, Mode fokus, Suara, Tidur, Pengaturan. Menutup sendiri setelah beberapa detik, atau dengan Esc
- [x] Panel Pengaturan (disimpan di `localStorage` kunci `iris.set`): volume suara, transparansi, mata ikuti kursor, gerakan acak, efek emoji, tidur otomatis dan lamanya, timer diucapkan Iris, lengan bergerak (menyalakan `setArmGest(0.3)`)
- [x] Timer dan Pomodoro: preset 5/10/15/45 menit, kolom menit bebas, `🍅 Pomodoro 25/5` (otomatis lanjut istirahat 5 menit). Hitung mundur tampil sebagai kapsul di kiri atas. Saat selesai: bunyi lonceng (WebAudio), efek emoji, gerakan `cheer`, dan kalimat pengingat bersuara lewat `speak` (kalimat tetap, tanpa LLM; matikan lewat "Timer diucapkan Iris")
- [x] Tanya clipboard: `Ctrl+Alt+V` dari mana saja, menu, tray, atau `/clip`. Teks langsung dikirim (maksimal 4000 karakter; kalau kotak input sudah berisi pertanyaan, itu dipakai sebagai pertanyaannya), gambar jadi lampiran. Butuh IPC baru `read-clipboard` di `main.js` dan `readClipboard` di `preload.js`
- [x] Perintah lokal di kotak input (tidak lewat server): `/timer N [nama]`, `/pomodoro`, `/batal`, `/clip`, `/layar [tanya]` (foto layar dan langsung tanya), `/fokus`, `/bisu`, `/tidur`, `/help`. `/agen` dan perintah tak dikenal tetap diteruskan ke server
- [x] Efek emoji di atas kepala mengikuti emosi (✨ senang, 💗 malu, 💢 marah, 💧 sedih, ❗ kaget, ❓ saat mikir, 💤 saat tidur). Uji dari konsol: `fx('💗', 3)`
- [x] Tidur otomatis: kursor global tidak bergerak dan tidak ada interaksi selama 5 menit (bawaan) membuat Iris menutup mata dan menunduk dengan 💤. Bangun saat kursor bergerak, diklik, atau ia bicara. Tidur manual (`/tidur`, menu, `sleepNow()`) hanya bangun lewat klik. Tidak tidur saat chat terbuka, sedang bicara, atau mengerjakan tugas agen
- [x] Colek dan elus: colek 4 kali dalam 6 detik dibalas "geli", 6 kali dibalas gumaman, 8 kali membuat Iris ngambek 10 detik (klik hanya dijawab "Hmph"). Tahan klik kiri di kepala 0,65 detik = elus (💗 dan wajah malu sampai dilepas)
- [x] Mode fokus: Iris diam (tanpa gerakan acak, sapaan, efek, tidur) dan jendela jadi transparan sekitar 55%. Pintasan global `Ctrl+Alt+B` membisukan suara hanya dari sisi overlay (terpisah dari "Bisukan suara" di tray)
- [x] Sapaan waktu (pagi, siang, sore, malam) sekali per peluncuran, sekarang bersuara
- [x] **Suara untuk reaksi lokal (`speak`):** semua kalimat lokal (colek, ngambek, elus kepala, klik bagian tubuh, bangun tidur, sapaan, timer, clipboard, Mode fokus, nyalakan suara) memakai kalimat Jepang tetap yang disintesis VOICEVOX. Overlay mengirim `{type:'speak', jp, id, emotion}`; `server.py` (`handle_speak`) mensintesis dan membalas segmen biasa bertanda `local: true` (tidak masuk panel chat, tidak menyentuh riwayat, tidak menginterupsi balasan yang berjalan, tanpa LLM). (Diperbarui di v7: lihat "Suara sentuh v7" di bawah; batas lama 2,2 detik dan 60% sudah diganti.) Server lama, VOICEVOX mati, atau suara dibisukan: otomatis jadi bubble teks (cadangan 2,5 detik). Pembisuan overlay (`Ctrl+Alt+B`) menghentikan suara ini juga
- [x] Pintasan bisu mencoba berurutan `Ctrl+Alt+B`, `Ctrl+Alt+M`, `Ctrl+Shift+Alt+M` (terminal mencetak "Pintasan terdaftar: ..."). `Ctrl+Alt+M` terbukti sudah dipakai aplikasi lain di PC ini (peringatan saat `npm start`). Paksa kombinasi sendiri lewat env `IRIS_MUTE_KEY` **[belum dites]**
- [x] **Perbaikan v7 (31 Okt 2026, semua [belum dites]):**
  - **Bubble terpotong di atas jendela:** bubble panjang (penjelasan 5 sampai 8 kalimat) tumbuh ke atas dan keluar dari jendela sehingga bagian atasnya hilang. Sekarang tinggi bubble dibatasi sesuai ruang di atas kepala karakter (`fitBubble()`, dihitung ulang saat jendela berubah ukuran karena chat dibuka), teks Indonesia dan Jepang berada di area yang bisa digulir (roda mouse), dan saat teks diketik gulirannya mengikuti
  - **Suara sentuh v7:** penyebab suara bolong: (1) jeda 2,2 detik antar suara membuat klik beruntun diam, (2) klik biasa hanya bersuara 60% dan paling sering tiap 5 detik, (3) menunggu sintesis server setiap kali. Perbaikan: setiap sentuhan sekarang bersuara dengan variasi kalimat (kepala 3, badan 3, lengan 2, tangan 2; colek 2 variasi "geli"; ngambek 3 variasi "Hmph.", "Mmm.", "Nggak tahu!"); kalimat lokal boleh menyela kalimat lokal lain (balasan asli tidak pernah disela); jeda antar suara 0,6 detik; audio disimpan di cache overlay (`voiceCache`) jadi pemutaran berikutnya instan
  - **Prefetch suara:** 4 detik setelah tersambung, overlay meminta server mensintesis semua kalimat sentuh/colek satu per 0,7 detik (pesan `speak` dengan `prefetch:true`, dibalas `voice_cache`, tidak ditampilkan). Server menyimpan hasil sintesis di `SPEAK_CACHE` (maksimal 120 kalimat), jadi kalimat yang sama tidak disintesis dua kali
  - **Polesan UI:** bubble bergaris aksen sesuai emosi dengan kotak terjemahan Jepang berlabel 日本語; bar input bergradasi dengan titik koneksi yang berdenyut; panel chat dan balon pesan lebih lembut (balasan Iris bergaris aksen); menu klik kanan lebih lebar dengan pemisah antara kelompok aksi dan mode; popover berjudul bergaris; efek hover dan fokus keyboard pada tombol
- [ ] Tes v7: klik kepala, badan, lengan, dan tangan berkali-kali, semuanya harus bersuara; colek 8 kali lalu klik lagi ("Hmph.", "Mmm.", "Nggak tahu!"); tanya pertanyaan panjang dengan "Mode jelaskan" dan pastikan bubble bisa digulir dan tidak keluar jendela, baik chat tertutup maupun terbuka
- [ ] Setelah `server.py` v7 jalan, terminal tidak boleh menampilkan `speak: VOICEVOX gagal`; kalau ada, kalimat itu tetap muncul sebagai bubble tanpa suara
- [x] **Perbaikan v8 (31 Okt 2026, semua [belum dites]):** nama bagian: kapsul bawah = **bar input** (`#bar`, dibungkus `#barWrap`), pil di atasnya = **indikator status tugas agen** (`#status`)
  - **Bar input auto-sembunyi:** bar tersembunyi (transparan, tidak bisa diklik sehingga klik tembus ke aplikasi di bawahnya) dan hanya muncul saat kursor mendekati areanya (dibaca dari kursor global `main.js`, jadi tidak perlu fokus). Tetap tampil selama: kotak input difokus, ada teks atau lampiran, atau panel chat terbuka. Hilang 1,2 detik setelah kursor menjauh (zona keluar lebih lebar daripada zona masuk supaya tidak berkedip). Saat start tampil 3,5 detik supaya letaknya diketahui
  - **Garis petunjuk (`#barHint`):** saat bar tersembunyi ada garis tipis yang \"bernapas\" di tempat bar: hijau = tersambung ke server, merah = server mati
  - **Tombol kirim:** muncul di bar saat ada teks atau lampiran (sama dengan Enter); bar diberi pemisah antar kelompok tombol, latar bergradasi, dan cincin fokus berpendar
  - **Indikator status tugas:** pil dengan spinner berputar, teks yang dipotong rapi, lencana detik (`12 dtk`), garis kilau yang bergerak saat berjalan, dan tampilan berbeda untuk gagal (merah) dan dihentikan (abu-abu). Strukturnya sekarang `.ic` + `.t` + `.s` (dulu satu teks)
- [ ] Tes v8: biarkan kursor jauh dari bar (harus hilang, garis petunjuk terlihat dan klik tembus ke game di bawahnya); arahkan ke area bar (muncul dalam sekitar 0,1 detik dan bisa diklik); ketik lalu jauhkan kursor (harus tetap tampil); `/agen tes` untuk melihat indikator status; matikan server untuk melihat garis petunjuk merah
- [x] **Perbaikan v9 (31 Okt 2026, semua [belum dites]; file berubah: `index.html`, `server.py`, `main.js`, `preload.js`):**
  - **Timeout Hermes terlalu cepat:** tugas seperti \"cek sisa Ollama\" (pencarian luas) timeout di 120 detik padahal Hermes masih bekerja. Bawaan `HERMES_TIMEOUT` naik ke **900 detik (15 menit)**; ubah lewat `$env:HERMES_TIMEOUT = \"1800\"` sebelum `python server.py`. Pesan \"Masih memproses... (N dtk)\" tiap 30 detik tetap jalan, dan tombol Stop bisa membatalkan kapan saja. Catatan: kalau batasnya terlewat, hasil tugas tidak bisa diambil belakangan karena permintaan sudah ditutup (hanya kalau pakai mode non-stream seperti sekarang)
  - **Pesan galat bersuara:** bubble merah (mis. \"Hermes: Hermes tidak membalas dalam N detik\") tadinya hanya teks. Sekarang dibacakan lewat `speak`: 3 kalimat Jepang menurut jenisnya (timeout, tidak tersambung/ditolak, galat lain; galat VOICEVOX tetap tanpa suara karena suaranya yang bermasalah). Pesan galat tidak disaring atau menyela, melainkan diantre dengan suara Iris yang sedang berjalan. Bubble tetap merah (segmen `speak` kini membawa bendera `error`). Kalimatnya ikut di-prefetch
  - **Ekspor chat ke HTML:** tombol baru ⬇ di header panel chat (di antara \"Hapus\" dan ✕), item menu klik kanan \"Ekspor chat\", atau perintah `/ekspor`. Seluruh percakapan (pesan kamu, balasan Iris, hasil tugas agen, galat, dan gambar lampiran) disimpan sebagai satu file HTML mandiri bergaya gelap yang rapi, tampil baik di ponsel dan bisa dicetak (mode cetak terang), ke folder **Downloads** dengan nama `Percakapan-Iris_TAHUN-BULAN-TANGGAL_JAM-MENIT.html` (tidak menimpa file lama; kalau kembar diberi ` (1)`). Setelah tersimpan, muncul kartu \"Ekspor tersimpan\" berisi lokasi file dengan tombol Tampilkan (membuka Explorer, tidak otomatis supaya tidak merebut fokus dari game) dan Iris mengabari dengan suara. Kartu itu sendiri tidak ikut terekspor
  - IPC baru: `save-html` dan `reveal-file` di `main.js` (hanya file dalam Downloads yang boleh ditampilkan), `saveHtml` dan `revealFile` di `preload.js`. Tanpa `main.js` baru, ekspor jatuh ke unduhan biasa lewat browser
- [ ] Tes v9: `/agen` pencarian luas (harus tidak timeout sebelum 15 menit); sengaja matikan Hermes lalu `/agen tes` (bubble merah bersuara); klik ⬇ di panel chat lalu buka file HTML-nya di browser (cek balasan Iris, hasil tugas, dan gambar tampil); coba ekspor saat chat kosong
- [ ] Tes menu klik kanan: menu muncul di kiri karakter, tombol bisa diklik (bukan tembus), dan tidak menimbulkan gerakan acak
- [ ] Tes Timer 1 menit, Pomodoro, dan pengingat suara; cek tidak ada suara dobel kalau timer selesai saat Iris sedang bicara
- [ ] Tes suara lokal setelah `server.py` baru dijalankan: colek 4 dan 8 kali, elus kepala, sapaan, `/timer 1`. Cek terminal server tidak menampilkan `speak: VOICEVOX gagal`
- [ ] Tes `Ctrl+Alt+V` dengan teks dan dengan gambar (Win+Shift+S) di clipboard; periksa pintasan tidak bentrok dengan aplikasi lain
- [ ] Tes tidur: jalankan `sleepNow()` lalu klik Iris; atur "Tidur setelah" 1 menit untuk uji tidur otomatis
- [ ] Tes colek 8 kali dan elus kepala (tahan klik); cek klik biasa sesudahnya tetap normal
- [ ] Nilai apakah menu di kiri karakter menutupi bubble atau panel chat; geser posisi lewat `top`/`left` di CSS `#menu` dan `.pop` kalau perlu
- [ ] Ide berikutnya: Timer yang bertahan setelah overlay ditutup, statistik Pomodoro harian, reaksi saat kursor lama diam di kepala, dan pemicu "Iris menyapa" saat jendela game aktif berganti (butuh nama jendela aktif, perlu modul native)
- [ ] Tes screenshot (tombol dan `Ctrl+Alt+S`), termasuk di game fullscreen (mode eksklusif bisa menghasilkan gambar hitam)
- [ ] Tes bubble bersama chat: bubble tidak terpotong di atas, tidak "tembus", dan karakter naik-turun wajar saat chat dibuka-ditutup
- [ ] Tes seret file dari Explorer ke karakter dan dialog 📎 tidak tertutup jendela overlay
- [ ] Push-to-talk atau wake word, dan STT dengan faster-whisper

## Arsitektur hybrid (tujuan)

```
Kamu ──► Overlay Electron (avatar, bubble, audio)           [Windows]
              │ WebSocket
              ▼
        server.py (FastAPI) ──► 9Router ──► LLM ──► VOICEVOX     jalur ngobrol (cepat)
              │
              └─ tugas ──► Hermes API server (WSL :8642)          jalur agen (lambat tapi bisa kerja)
                              │  tools, skills, memori
                  hasil mentah ◄┘
                  └─► diringkas dengan persona Iris ──► segment ──► overlay

Telegram ──► Hermes gateway (tetap ada, kanal jarak jauh)
```

Aturan pembagian:
- **Ngobrol, bercanda, tanya jawab** dijawab overlay sendiri.
- **Permintaan aksi** (buka file, cari, cek e-learning, terminal, Chrome) diteruskan `server.py` ke Hermes, lalu hasilnya disampaikan Iris dengan suara.
- Memori **awalnya terpisah**: yang permanen hanya memori Hermes, sedangkan overlay hanya punya riwayat obrolan sementara.

---

# Bagian A: Overlay Desktop (Roadmap)

## Roadmap Pendamping AI Desktop (2D/3D)

**by: KangJiho**

Target: karakter AI yang tampil sebagai overlay di desktop (jendela transparan, selalu di depan), punya bubble chat, bersuara, dan bisa merespons apa yang ada di layar.

**Terakhir diperbarui:** 30 Okt 2026. Posisi sekarang: Fase 1, 2, dan 3 (jalur VRM) selesai, dan overlay tampil di desktop dengan avatar, suara, bubble, ekspresi, kedip, lip-sync moras, dan animasi idle `.vrma`. Sesi terakhir menambahkan hal berikut, yang baru dicek sintaksnya dan **belum dites di Electron**: click-through per piksel, kursor dan hotkey global, ikon tray, single-instance, posisi jendela tersimpan, klik per bagian tubuh, dan lampiran gambar di overlay. **Analisis gambar belum berfungsi penuh karena `server.py` belum diubah untuk menerima field `images`.** Berikutnya: tes visual dan fungsional semua itu, ubah `server.py` untuk vision, lalu Fase 5 sisa (push-to-talk dan STT).

---

### Stack

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

### Lingkungan kerja (Windows + WSL)

- **Electron wajib dijalankan di Windows**, bukan di WSL. Transparansi, always-on-top, dan click-through lewat WSLg tidak bisa diandalkan.
- **Backend Python disarankan jalan di Python Windows.** `mss` (screenshot, Fase 6) dan mic (Fase 5) tidak bisa menangkap layar/mic Windows dari dalam WSL. Satu lingkungan juga berarti semua layanan cukup lewat `localhost`.
- Kalau tetap memakai backend di WSL: server di `127.0.0.1:8765` bisa dibuka dari Windows lewat `localhost`. Tapi VOICEVOX dan 9Router yang jalan di Windows tidak terjangkau dari WSL2 mode default. Solusinya, buat `C:\Users\<nama>\.wslconfig`:
  ```
  [wsl2]
  networkingMode=mirrored
  ```
  lalu `wsl --shutdown` (butuh Windows 11 22H2+). Alternatif: isi `VOICEVOX_URL` dan `NINEROUTER_URL` dengan IP host Windows.

### Arsitektur

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

### Fase 0: Persiapan

- [ ] VOICEVOX jalan di `127.0.0.1:50021`
- [ ] Tes `audio_query` dan `synthesis` dengan `speaker=2`, hasilkan `test.wav`
- [ ] Catat base URL, nama model/combo, dan API key 9Router
- [ ] Tes satu request chat completion ke 9Router
- [ ] Install Node.js (LTS) dan Python 3.10+
- [x] Putuskan avatar: **VRM** (dipilih)

### Fase 1: Backend Python

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

### Fase 2: Overlay Electron

- [x] Inisialisasi proyek Electron (di Windows, bukan WSL)
- [x] Jendela `transparent: true`, `frame: false`, `alwaysOnTop: true` (terlihat di atas jendela Steam)
- [x] Click-through di area kosong (`setIgnoreMouseEvents(true, { forward: true })`), nonaktifkan saat kursor di atas karakter (diuji di atas jendela Steam, aman)
- [x] Posisi default di pojok kanan bawah layar
- [x] Jendela bisa dipindah: seret tombol ✥ di bar bawah (memakai `-webkit-app-region: drag`, tanpa perubahan `main.js`)
- [x] Koneksi WebSocket ke backend (logika sama dengan `test_client.html`)
- [x] Putar audio yang diterima (antrian berurutan) (suara Metan keluar dari overlay, aman)
- [x] Click-through per piksel (`sampleHit()` di `index.html`): alpha piksel di bawah kursor dibaca lewat `readPixels` tepat setelah render, jadi area transparan di sekitar karakter tembus klik (sebelumnya seluruh kotak `#char` menghalangi). Saklar `PIXEL_HIT = false` mengembalikan perilaku lama. Hover juga dihitung dari kursor global (`probeAt()`), bukan hanya `mousemove`. Ditulis, belum dites
- [x] Hanya satu salinan overlay (`requestSingleInstanceLock`), jendela tampil lewat `showInactive()` supaya tidak merebut fokus dari game, dan posisi jendela diingat antar sesi (`overlay-state.json` di folder userData; dipakai hanya kalau masih di dalam layar). Ditulis, belum dites

### Fase 3: Avatar

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

#### Masalah diketahui: gerakan prosedural terlihat creepy (dicatat 30 Okt 2026)

**Status 31 Okt 2026 (v18, Tier S dari analisis GitHub):** penyebab "menyentak" dan "menyapu pose T" ditangani di lapisan penerapan pose. Pendekatan eksponensial lama (`dt * 5`) diganti pegas teredam kritis dengan batas kecepatan sudut, gerakan yang diganti memudar (crossfade), dan klip VRMA asli bisa dipakai lewat gerbang emosi. Detail di "Hasil pencarian GitHub" dan "Pembaruan v17 dan v18". Belum dinilai visual.

**Status 31 Okt 2026 (gerakan v3):** daftar gerakan, tatapan mata, gerak kepala saat bicara, pose `think`, dan kedip ditulis ulang (lihat "Gerakan v3" di Progres terkini). Lengan tetap mati secara bawaan. Belum dinilai visual.

**Status 31 Okt 2026:** semua gerakan lengan dimatikan secara bawaan (`ARM_GEST = 0`, yang bergerak hanya kepala dan badan). Atur dari konsol (Ctrl+Alt+D) dengan `setArmGest(0..1)`; `wave` dilewati selama lengan mati. Belum dinilai visual.

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
- [x] Sementara nonaktifkan gerakan lengan besar, sisakan gerakan kepala (`nod`, `shake`, `lookAround`) dan gerakan kecil (31 Okt, lewat `ARM_GEST = 0`)
- [x] Batasi lengan supaya tidak melewati horizontal, dan perbaiki transisi supaya tidak menyapu lewat pose terentang (pagar `ARM_MIN` sudah ada; 31 Okt v18: transisi lewat pegas dengan batas kecepatan sudut) **[belum dinilai visual]**
- [ ] Tambah gerakan bahu (`leftShoulder`, `rightShoulder`) dan siku yang lebih lembut
- [x] Kurangi frekuensi gerakan acak dan gerakan saat bicara (31 Okt: `GEST_CHANCE` 0,35 dan `IDLE_MIN`/`IDLE_VAR` 20 + 0 sampai 20 detik)
- [x] Pertimbangkan animasi `.vrma` dari mocap/Mixamo (item opsional di atas) kalau gerakan kode tetap kaku (31 Okt v18: dukungan klip aksi ditulis; file klip belum disiapkan)

**Jalur Live2D (2D), tidak dipakai**
- [ ] Siapkan model Live2D (`.model3.json`)
- [ ] Render dengan `pixi-live2d-display`
- [ ] Idle motion dan ekspresi sesuai model

### Fase 4: Bubble chat dan lip-sync

- [x] Bubble HTML/CSS di dekat karakter. Teks muncul bertahap per karakter (aman untuk emoji dan huruf Jepang) dan lamanya mengikuti durasi suara; belum dites visual
- [x] Bubble menghilang otomatis setelah beberapa detik
- [x] Lip-sync versi 1 (prototipe): volume audio (`AnalyserNode`) jadi bar di `test_client.html`. Sudah dipetakan ke bukaan mulut `aa` avatar di `index.html`
- [x] Lip-sync versi 2: data `moras` (`vowel`, `start`, `end`) untuk bentuk mulut a/i/u/e/o (`updateVisemes()` di `index.html`; cadangan volume, lalu goyang prosedural kalau analyser mati; belum dites visual. Mulut terlambat atau terlalu cepat: ubah `LIP_OFFSET`)
- [x] Tag `emotion` dari LLM dipetakan ke ekspresi wajah dan gerakan tubuh avatar

### Fase 5: Input

- [x] Kotak input teks kecil (sudah ada di overlay)
- [x] Panel chat dengan riwayat (tombol 💬 atau Ctrl+Alt+C dari mana saja): balasan Iris bisa dibaca ulang, tombol Hapus (kirim `reset`), Esc menutup. Ada "Mode jelaskan": pertanyaan diberi awalan supaya Iris menjelaskan lebih panjang (5 sampai 8 kalimat), format `[emosi] jp ||| id` tetap
- [x] Hotkey global `Ctrl+Alt+C` untuk membuka chat saat jendela tidak fokus (`globalShortcut` di `main.js` menampilkan dan memfokuskan jendela lalu mengirim IPC `open-chat`; `preload.js` mengeksposnya sebagai `onOpenChat`). Karena dikonsumsi secara global, pintasan toggle di dalam jendela tidak lagi berjalan; chat ditutup dengan Esc atau tombol ✕. Ditulis, belum dites (kalau input tidak langsung fokus, itu pembatasan fokus Windows)
- [ ] Push-to-talk atau wake word
- [ ] STT dengan faster-whisper (jalankan di Python Windows), hasilnya dikirim ke backend

### Analisis gambar (lampiran)

Memberi gambar ke Iris supaya dianalisis oleh model vision.

- [x] Overlay: tempel dengan `Ctrl+V` (mis. hasil `Win+Shift+S`), tombol 📎, atau seret file gambar ke karakter atau bar input. Thumbnail tampil di atas bar (maksimal 4, ada tombol ✕), gambar dikecilkan ke sisi terpanjang 1280 px dan dijadikan JPEG, dikirim lewat field `images`, dan riwayat chat menampilkan thumbnail. Enter tanpa teks memakai prompt bawaan. Ditulis, belum dites
- [x] (selesai 31 Okt, dites) Backend `server.py`: terima `images`, ubah jadi `content` multimodal (`text` + `image_url` berisi data URL), pakai model yang mendukung gambar lewat variabel baru `NINEROUTER_VISION_MODEL`, dan jangan menyimpan data gambar di riwayat (ganti dengan penanda teks seperti "[gambar]") supaya konteks tidak membengkak. Pesan bergambar yang diawali `/agen` diperlakukan sebagai chat biasa dan awalannya dibuang.
- [x] Cek model: terbukti jalan (Iris menjelaskan isi gambar). Batas pesan WebSocket dinaikkan lewat `ws_max_size` 32 MB, dan tiap gambar dibatasi 6 juta karakter, maksimal 4 gambar. Kalau model menolak gambar, pesan error menyebut `NINEROUTER_VISION_MODEL`
- [ ] Tes seret file dari Explorer ke karakter (jendela tembus klik bisa menolak drop; cadangannya `Ctrl+V` atau 📎) dan cek dialog 📎 tidak tertutup jendela overlay yang selalu di depan
- [x] Tombol ambil screenshot layar langsung dari overlay (kamera, `Ctrl+Alt+S`, tray), memakai jalur gambar yang sama. Ditulis, belum dites

### Fase 6: Screen awareness (opsional)

- [ ] Screenshot berkala dengan `mss` (misalnya tiap 30-60 detik), jalankan di Python Windows
- [ ] Kirim ke model vision (lewat 9Router atau Ollama)
- [ ] Karakter berkomentar tentang yang sedang dilihat
- [ ] Tombol/hotkey untuk mematikan fitur ini kapan saja

### Fase 7: Polish

- [ ] Memori percakapan (ringkasan jangka panjang)
- [x] Persona dan gaya bicara lewat system prompt (Iris, lihat bagian Persona)
- [x] Ikon tray (`setupTray()` di `main.js`, butuh `assets/tray.png`): tampilkan atau sembunyikan, buka chat, bisukan suara (`setAudioMuted`; lip-sync tetap jalan), pindah ke pojok kanan bawah, keluar. Ditulis, belum dites
- [x] Menu aksi cepat, pengaturan, timer/Pomodoro, tanya clipboard, tidur otomatis, colek/elus, efek emoji, perintah lokal (paket v6, lihat Progres terkini)
- [ ] Auto-start bersama Windows (4 Nov 2026: diputuskan diambil, lihat Bagian Q)
- [ ] Penanganan error: VOICEVOX mati, 9Router timeout (sebagian sudah ada: error dikirim ke klien sebagai `{"type": "error"}`)

---

### Cara menjalankan

#### Struktur folder saat ini

Semua file ada di satu folder: `Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron` (`server.py`, `.venv`, `requirements.txt`, `test_client.html`, serta `main.js`, `preload.js`, `index.html`, `package.json`, `node_modules`). Rencananya nanti dirapikan menjadi subfolder `backend` dan `overlay`, tapi jangan memindahkan `.venv` sebelum semuanya stabil. Folder `assets/` berisi `iris.vrm`, `animations/idle_loop.vrma`, dan `tray.png`.

#### Jendela 1: server (Fase 1)

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

#### Jendela 2: overlay Electron (Fase 2)

Jendela PowerShell terpisah, server tetap jalan:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd "Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron"
npm start
```

Pertama kali, `npm install --save-dev electron` dan unduhan biner Electron (ratusan MB) harus selesai tanpa error. Pintasan global: `Ctrl+Alt+Q` keluar, `Ctrl+Alt+H` sembunyikan atau tampilkan, `Ctrl+Alt+C` buka chat, `Ctrl+Alt+S` screenshot, `Ctrl+Alt+T` terjemahkan layar, `Ctrl+Alt+G` bicara (mic), `Ctrl+Alt+V` tanya clipboard, `Ctrl+Alt+B` bisukan suara overlay, `Ctrl+Alt+D` DevTools. Kalau ada pintasan yang bentrok dengan aplikasi lain, terminal `npm start` menampilkan "Pintasan global gagal didaftarkan". Menu tray ada di ikon `assets/tray.png`.

### Persona: Iris

System prompt di `server.py` (v3) memakai persona Iris, yaitu I.R.I.S. (Intelligent Retrieval & Indexing System), teman sekelas playful dari Wuthering Waves. Memanggil user "Rover" atau "Classmate", Indonesia campur slang, jokes tipis-tipis nusuk, jawaban singkat 1 sampai 3 baris. Aturan format `[emosi] jp ||| id` tetap. Sumber persona: skill Hermes di `~/.hermes/skills` (`iris-persona`, `iris-modes`). Aturan khusus chat teks Hermes (label `[jokes]`, label mode, struktur ilmiah, aturan hapus sesi) sengaja tidak dipakai karena akan tampil dan terbaca di bubble. Menyambung langsung ke API server Hermes dicatat sebagai opsi untuk Fase 7 (memori), dengan risiko latensi dan format yang bisa kacau.

---

### Troubleshooting (dari tes Fase 1 dan 2)

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

### Hasil analisis AIRI (moeru-ai/airi, MIT) dan yang sudah diambil

Kode AIRI tidak disalin: ditulis dengan TypeScript, Vue, dan paket monorepo mereka, sedangkan `index.html` kita JavaScript biasa. Yang diambil hanya teknik dan idenya, dan angkanya diatur sendiri:
- [x] Penghalusan mulut eksponensial dengan kecepatan buka dan tutup berbeda (`LIP_ATTACK`, `LIP_RELEASE`), dari perubahan lip-sync AIRI
- [x] Batas FPS (`FPS_IDLE` 30, `FPS_ACTIVE` 60) supaya overlay ringan di atas game, dari ide performance runtime AIRI
- [x] Teks bubble bertahap, dari ide streaming text animation AIRI
- [x] Animasi idle `.vrma` dari AIRI (`assets/animations/idle_loop.vrma`, dimuat `loadIdleVRMA()`): mixer menggerakkan badan, lapisan prosedural hanya menambah (kepala menoleh, bicara, gerakan kecil). Butuh `npm install @pixiv/three-vrm-animation`; kalau gagal dimuat, otomatis kembali ke gerakan prosedural. Belum dites visual. Cek asal-usul dan lisensi file `.vrma` sebelum publikasi
- [x] Angka lip-sync dan bobot ekspresi disamakan dengan AIRI (`LIP_ATTACK` 50, `LIP_RELEASE` 30, `LIP_GAIN`, emosi 0.7 sampai 0.8)
- [x] Kursor di seluruh layar dan hotkey chat global: pola `screen.ts` (main process membaca `screen.getCursorScreenPoint()` berkala dan mengirim hanya saat berubah) dan `global-shortcut.ts`, ditulis ulang di `main.js` dan `preload.js` dengan JavaScript biasa. Belum dites
- [x] Crossfade antar animasi (AIRI: `crossFadeDuration` 0,3 detik): v18 menambah crossfade 0,5 detik antar gerakan prosedural, dan bobot idle dan klip VRMA dijumlahkan jadi 1 dengan smootherstep **[belum dites]**
- [ ] Mikrofon dan deteksi bicara di sisi klien (Fase 5), lalu kirim ke faster-whisper
- [x] Hit-test per piksel (`hit-test.ts`, `render-target.ts`): AIRI merender ke render target kecil; kita membaca alpha langsung dari kanvas dengan `readPixels` setelah render, lebih ringan
- [x] Collider per bagian tubuh (`interaction.ts`): bola di titik tengah tulang (bukan kotak berarah, supaya tidak tergantung sumbu tulang), raycast saat klik
- [x] Pola Electron dari `main/`: single-instance guard, `showInactive()` supaya tidak merebut fokus, tray, simpan posisi jendela (dengan debounce, tidak di setiap event `move`)
- [ ] Belum diambil: `VRMUtils.removeUnnecessaryVertices` dan `combineSkeletons` (performa, tes dulu), `uiohook-napi` untuk push-to-talk tahan tombol (modul native; alternatif tanpa modul native: mode toggle dengan `globalShortcut`), `powerMonitor` (hentikan screenshot saat layar terkunci, untuk Fase 6)

### Hasil pencarian GitHub dan tingkat pengambilan (31 Okt 2026)

Dicari repo yang bisa diambil untuk Iris. Aturannya sama seperti AIRI: **kode tidak disalin** (kebanyakan TypeScript atau React, `index.html` kita JavaScript biasa); yang diambil teknik dan idenya, ditulis ulang, dan angkanya diatur sendiri. Cek lisensi file aset sebelum dipublikasikan; untuk pakai pribadi aman.

| Repo | Lisensi | Isi yang relevan |
|---|---|---|
| `FireTable/project-xiaochun` | MIT (aset model VRoid: syarat VRoid; `thinking.vrma` lisensi tidak diketahui) | Batas kecepatan sudut dan pegas kritis, smootherstep 0,75 detik, lapisan pose, angin dari kursor, protokol `xiaochun://`, memori tiga tingkat, EMAGE |
| `rehan-remade/open-annie` | Kode Apache-2.0; paket gerakan CC0; avatar sesuai syarat pixiv | Pemilih gerakan dipisah dari yang bicara, gerbang keyakinan dengan aturan lokal cadangan, HeadAudio untuk viseme, 32 frasa gestur ko-bicara |
| `ARPAHLS/avatar` | MIT | Overlay VRM dengan VRMA, lip-sync dari audio sistem, API loopback untuk menggerakkan karakter, hotkey Motion Deck |
| `zrb-face` (PyPI) | belum dicek | `fbx2vrma.mjs` (Mixamo FBX ke .vrma), pemicu gestur dari agen |
| `Dongping-Chen/Clawatar` | belum dicek | 162 animasi Mixamo dengan katalog, kendali lewat WebSocket |

**Tier S (diambil, v18, 31 Okt 2026):**
- [x] Smootherstep dan batas kecepatan sudut dengan pegas teredam kritis (dari xiaochun) **[belum dites visual]**
- [x] Pemetaan `[emosi]` ke klip dengan gerbang dan aturan cadangan prosedural (pola open-annie) **[belum dites]**
- [x] Pemuatan klip VRMA aksi (paket CC0 open-annie atau pack VRoid untuk pakai pribadi) **[kode ada; file klip belum disiapkan]**

**Tier A (belum diambil, usaha sedang):**
- [x] **(sudah ada, dikoreksi 2 Nov 2026; lihat Bagian J1)** Lip-sync dari mora VOICEVOX: `audio_query` memberi mora dan panjang vokal, jadi jadwal bukaan mulut bisa pas (ide sendiri, bukan dari GitHub). Cek dulu apa yang sudah dipakai `curMoras` di `index.html`
- [ ] Angin dari kecepatan kursor untuk spring bone rambut dan kain (xiaochun)
- [ ] Pintu masuk untuk agen luar: perintah WebSocket baru seperti `speak` dan `play_clip` di `server.py`, supaya Hermes bisa menyuruh Iris bereaksi tanpa lewat chat (pola `xiaochun://` dan API loopback ARPAHLS)

**Tier B (opsional, perlu dites dulu):**
- [ ] HeadAudio untuk viseme (MIT); belum tentu akurat untuk suara Jepang VOICEVOX
- [ ] Konversi Mixamo ke VRMA (zrb-face, Clawatar); animasi Mixamo punya syarat kredit sendiri
- [ ] Hotkey Motion Deck dan lip-sync dari audio sistem (ARPAHLS/avatar)
- [ ] Memori tiga tingkat dengan pencarian n-gram (xiaochun); Hermes sudah punya memori sendiri

**Tier C (dilewati):** EMAGE (model sekitar 72 MB via ONNX/WASM, terlalu berat untuk overlay di atas game), ganti baju (catatan: dikerjakan juga di v25 sebagai pilihan sederhana, satu file VRM per baju, tanpa bone morph), bone morph, post-processing, Tauri, `lala-companion` (React/TypeScript, butuh API OpenAI), `DesktopClaw` (khusus OpenClaw), `liqu-companion` (terlalu kecil).

### Risiko dan catatan

- **Lisensi model avatar:** pastikan boleh dipakai untuk tujuan kamu.
- **Lisensi suara:** cek ketentuan kredit VOICEVOX dan karakter Shikoku Metan sebelum dipublikasikan.
- **Privasi screen awareness:** screenshot bisa memuat data sensitif. Pakai model lokal bila memungkinkan dan sediakan tombol mati.
- **Privasi gambar lampiran:** gambar dikirim lewat 9Router ke model vision di cloud (mis. Gemini). Jangan melampirkan screenshot yang memuat data sensitif.
- **Keamanan lokal:** server hanya bind ke `127.0.0.1` dan menolak Origin asing. Jangan ubah `COMPANION_HOST` ke `0.0.0.0` tanpa autentikasi.
- **Latensi:** streaming dan pengiriman per kalimat penting supaya respons terasa cepat.
- **Click-through di Electron:** perilakunya agak berbeda antar OS, jadi uji lebih awal di Fase 2.
- **Kepatuhan format LLM:** model tertentu bisa mengabaikan format `[emosi] jp ||| id`. Kalau sering terjadi, pertimbangkan model lain atau contoh tambahan di system prompt.

### Urutan kerja yang disarankan

1. Fase 0 sampai 1: pastikan teks masuk, suara keluar. **(selesai)**
2. Fase 2: overlay Electron di desktop. **(selesai: tampil, tersambung, click-through dan audio aman)**
3. Fase 3: avatar VRM dengan idle, ekspresi, dan gerakan. **(jalan; gerakan v2, animasi idle `.vrma`, dan klik per bagian tubuh sudah ditulis, belum dites visual)**
4. Tes visual dan fungsional hasil sesi terakhir: click-through per piksel, kursor dan hotkey global, tray, posisi tersimpan, `.vrma`, klik per bagian tubuh (lihat bagian Troubleshooting kalau ada yang gagal).
5. Analisis gambar: ubah `server.py` (field `images`, model vision), lalu tes tempel, 📎, dan seret.
6. Fase 4 sisa: tes visual lip-sync v2 dan teks bubble bertahap.
7. Fase 5 sampai 7: input suara (push-to-talk, STT), screen awareness, memori, dan auto-start.

---

# Bagian B: Sistem Hermes (Referensi)

## 🤖 Iris — AI Companion System Reference

> AI Desktop Companion yang jalan di atas WSL + Windows  
> Version: v0.22.2 (2026.9.24) · Kernel: Hermes Agent by Nous Research  
> Ubuntu (WSL) installed: 2026-09-28  
> Hermes installed: 2026-09-28  
> Overlay project started: 2026-10-28  
> Doc generated: 2026-10-30

---

### What is Iris

Iris adalah AI companion yang tinggal di dalam laptop lewat WSL. Dia bukan cuma chatbot — dia bisa:
- **Ngobrol** pakai suara Metan 2 (VOICEVOX) langsung dari speaker
- **Bantu kontrol laptop** (buka file, folder, chrome, volume, dll)
- **Jalanin terminal & coding** dari WSL
- **Browse internet** lewat Chrome debug
- **Kasih suara feedback** tiap aksi yang dikerjakan

Dia adalah sistem agent, bukan web app. Setiap permintaan kamu diproses lokal + kirim ke LLM lewat 9Router.

---

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Telegram (UI Layer)                 │
│              Chat interface / commands               │
├─────────────────────────────────────────────────────┤
│                  Hermes Agent Core                   │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │  Skills     │ │  Memory      │ │  Persona     │  │
│  │  (plugins)  │ │  (persist)   │ │  (I.R.I.S.)  │  │
│  └─────────────┘ └──────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────┤
│                  Hermes Runtime                     │
│  Python 3.14.7 · OpenAI SDK 2.24.0 · WSL Ubuntu    │
├─────────────────────────────────────────────────────┤
│                  9Router Gateway                    │
│          localhost:20128/v1 (LLM proxy)             │
├─────────────┬───────────────────────────────────────┤
│  VOICEVOX   │  Chrome Debug (port 9222)             │
│  :50021     │  Browser automation                    │
│  Metan 2    │                                        │
└─────────────┴───────────────────────────────────────┘
```

---

### Core Components

#### 1. Hermes Agent (The Brain)
- **Role:** Brain utama — ngolah pesan, eksekusi tools, manage skills
- **Location:** `/home/<user>/.hermes/`
- **Language:** Python (venv managed)
- **Model routing:** Semua LLM call lewat 9Router local gateway

#### 2. 9Router (LLM Gateway)
- **Port:** `localhost:20128/v1`
- **Function:** Proxy semua AI API calls dari Hermes ke provider LLM
- **Model default:** Hermes Free (via 9Router config)
- **Fallback:** Kalau gateway gagal, Hermes error

#### 3. VOICEVOX (Voice Engine)
- **Engine:** VOICEVOX v0.25.2 (Japanese TTS)
- **Endpoint:** `http://localhost:50021`
- **Speaker:** Metan 2 (四国めたん ノーマル) — suara cewek Jepang manis
- **Wrapper:** `jarvis-say.sh` → generate WAV + play via PowerShell
- **Mute aware:** Kalau laptop muted, skip speak

#### 4. Chrome Debug (Browser Control)
- **Port:** 9222 (CDP — Chrome DevTools Protocol)
- **Function:** Buka tab, navigate, fill form, screenshot
- **Auto-start:** DISABLED (manual trigger via `chrome-debug`)
- **Access:** `127.0.0.1:9222` (WSL) atau `172.29.96.1:9222` (Windows)

---

### Persona: I.R.I.S.

| Atribut | Nilai |
|---------|-------|
| **Nama** | Iris (tanpa titik) |
| **Role** | Playful classmate / gadis sebelah |
| **Sifat** | Bercanda, sedikit menggoda, suka ngobrol santai |
| **Bahasa** | Indonesia utama, kadang Jepang (TTS Metan 2) |
| **Voice** | Metan 2 (四国めたん) — Japanese TTS natural voice |
| **Call sign** | Panggil user "Rover" |
| **Mode Ilmiah** | Analogi per poin + sitasi URL + verdict FAKTA/VALID/MITOS |

#### Example Behaviors
- Suara feedback: Setiap aksi laptop, keluar suara Metan 2
- Tone: Santai, to the point, bercanda setiap respon
- Jokes: Natural, tidak dipaksa
- Voice notes: Bisa kirim audio via VOICEVOX

---

### Skills System

Iris punya **skill system** — plugin yang bisa diaktifkan sesuai kebutuhan:

| Kategori | Contoh Skills |
|----------|---------------|
| **Autonomous Agents** | Claude Code, OpenCode CLI, Computer Use |
| **Browser** | Chrome Control, Blocked Page Recovery |
| **Research** | ArXiv, Deep Research, Domain Intel |
| **Productivity** | Notion, Airtable, Google Workspace, Excel, PDF |
| **Media** | YouTube Transcript, GIF Search, TTS |
| **E-learning** | <kampus> Moodle checker, form auto-fill |
| **Windows** | Storage Analyzer, System Maintenance |
| **Creative** | ASCII art, diagrams, humanizer text |
| **Security** | OSS Forensics, Reverse Engineering |

Skills di-load sesuai konteks — kalau kamu minta "review paper", dia load `paper-reviewer`. Kalau minta "buka Chrome", dia load `chrome-control`.

---

### Memory System

Iris ingat hal penting lewat dua storage:

1. **Global Memory** (`memory` tool)
   - Info environment: paths, ports, tools
   - Rules: "hermes update cuma saat gateway idle", "hanya remove file setelah konfirmasi"
   - Constraints: disk penuh, muted speaker, dll

2. **User Profile** (`user` target)
   - Identitas: <NIM>, <kampus> student
   - Preferensi: <preferensi pribadi>
   - Goals: <tujuan pribadi>
   - Quirks: <kebiasaan pribadi>

Memory di-inject ke tiap conversation turn. Dia **tidak** hapus otomatis — kamu harus command explicitly.

---

### Terminal & Execution

Iris bisa jalanin perintah di WSL:

```bash
# Via terminal tool
- Foreground (sync): default, return output langsung
- Background (async): `background=true`, return session_id
- Timeout: 180s default, max 600s foreground / unlimited background
```

**Process management:**
```bash
process_manage list/stop/steer
```

---

### Voice Feedback Loop

Setiap kali kamu minta action yang melibatkan laptop:

1. Iris eksekusi command
2. Generate suara via VOICEVOX Metan 2
3. Play via PowerShell (hidden, no popup)
4. Kalau laptop muted → skip, respect user

---

### Communication Channels

| Platform | Status | Role |
|----------|--------|------|
| **Telegram** | ✅ Primary | Chat interface with Rover |
| **Local** | ✅ Fallback | File output, cron jobs |
| **Origin** | ✅ Return | Back to source chat |

---

### Update & Maintenance

- **Auto-update:** Hanya jalan kalau gateway idle
- **Schedule:** Cron nightly `03:15` WIB via script (no agent mode)
- **Manual:** `hermes update` dari terminal
- **Safety:** Kalau ada task sedang jalan, skip update

---

### Setup Requirements (untuk clone ke PC lain)

#### Minimum
- WSL2 (Ubuntu 22.04+)
- Python 3.11+
- Windows host untuk: VOICEVOX, Chrome, PowerShell sound
- 9Router instance running (localhost:20128)
- Hermes Agent installed (via git or pip)

#### Recommended
- 16 GB RAM (Hermes + 7B model + TTS)
- RTX GPU untuk model quantization
- Disk X: atau drive lain dengan 100+ GB free untuk models

#### Install Steps (ringkas)
1. Install WSL2 + Ubuntu
2. Install Hermes Agent: `git clone` + setup venv
3. Install VOICEVOX di Windows (port 50021)
4. Setup 9Router locally
5. Configure Telegram bot token
6. Enable Chrome debug port (optional)

---

### Known Limitations

1. **TTS voice:** Metan 2 Japanese voice, not Indonesian. Kalau mau ID voice, perlu setup TTS lain.
2. **Browser:** Chrome auto-start disabled — harus manual start `chrome-debug`.
3. **Memory:** 16 GB RAM tight untuk multi-task berat.
4. **Disk C:/Z:** Keduanya 93% penuh — cleanup required sebelum install besar.
5. **Offline mode:** TTS dan browser perlu Windows. Kalau WSL only, keduanya broken.

---

### Current Status (2026-10-30)

| Component | Status |
|-----------|--------|
| Hermes Agent | ✅ Active (v0.22.2) |
| 9Router | ✅ Active (port 20128) |
| VOICEVOX | ✅ Active (v0.25.2, port 50021) |
| Memory | ✅ Healthy (3.4 GB available) |

---

### File Locations

```
/home/<user>/
├── .hermes/
│   ├── scripts/
│   │   ├── jarvis-say.sh          # Voice feedback wrapper
│   │   └── voicevox_tts.py        # TTS API client
│   └── cache/scratch/             # Temp workspace
├── .local/bin/hermes              # Hermes binary
├── bin/
│   └── chrome-debug               # Chrome debug launcher
└── play_voicevox_bg.sh            # Background WAV player
```

---

### Quick Command Reference

```bash
# Cek VOICEVOX
curl http://localhost:50021/version

# Cek 9Router
curl http://localhost:20128/health

# Test voice
/home/<user>/.hermes/scripts/jarvis-say.sh "Test suara"

# Update Hermes (hanya saat idle)
hermes update

# Start Chrome debug
~/bin/chrome-debug
```

---

*Generated by Iris · Last updated: 2026-10-30 WIB*


---

# Bagian C: Jembatan Hybrid (overlay ↔ Hermes)

Tujuan: `server.py` bisa menitipkan tugas ke Hermes dan membawa hasilnya kembali, sambil tetap memakai persona Iris dan format `[emosi] jp ||| id`.

## Dasar teknis (dari dokumentasi Hermes, perlu dicek di versi v0.22.2)

- Hermes punya **API server** yang kompatibel dengan OpenAI, **mati secara bawaan** dan hanya mendengarkan `127.0.0.1:8642`.
- Aktifkan lewat `~/.hermes/.env`: `API_SERVER_ENABLED=true` dan `API_SERVER_KEY=<kunci>`. Server berjalan bersama `hermes gateway`.
- Endpoint yang dipakai: `POST /v1/chat/completions` (tanpa status, seluruh percakapan dikirim tiap request), `GET /health`. Ada juga `/v1/responses` (status disimpan di server) dan endpoint untuk menghentikan giliran agen yang sedang jalan.
- Pesan `system` dari klien ditumpuk di atas system prompt inti Hermes, jadi memori dan skill Hermes tetap aktif.
- Pembagian ini membuat Hermes berperan sebagai **tool**, bukan pengganti otak overlay.

## Langkah kerja

### Tahap 0: Nyalakan API server Hermes (di WSL)

- [x] Buat kunci acak: `openssl rand -hex 24`
- [x] Tambahkan ke `~/.hermes/.env`:
  ```
  API_SERVER_ENABLED=true
  API_SERVER_KEY=<kunci-tadi>
  ```
  Biarkan `API_SERVER_HOST` di nilai bawaan `127.0.0.1`. Jangan ubah ke `0.0.0.0`.
- [x] Restart gateway Hermes dengan cara yang biasa kamu pakai, **hanya saat tidak ada tugas yang sedang jalan** (aturan: update dan restart saat gateway idle) (selesai; gateway dikelola systemd, restart dengan `hermes gateway restart`)
- [x] Tes dari WSL: `curl http://127.0.0.1:8642/health`
- [x] Tes dari Windows (PowerShell): `curl.exe http://localhost:8642/health`. Kalau gagal dari Windows tapi berhasil dari WSL, periksa mode jaringan WSL (`networkingMode=mirrored` di `.wslconfig`, lihat bagian Lingkungan kerja) (berhasil, jaringan WSL tidak perlu diubah)

### Tahap 1: Tes tugas manual

- [x] Dari PowerShell, kirim satu permintaan ke `/v1/chat/completions` dengan header `Authorization: Bearer <kunci>`, `model: "hermes-agent"`, dan pesan sederhana ("Sebutkan isi folder ~/hermes-test")
- [x] Catat lama responsnya dan bentuk jawabannya. Ini menentukan batas waktu di tahap berikutnya (hasil: sekitar 11 detik; jawaban berbentuk daftar markdown walau diminta teks polos)

### Tahap 2: Modul jembatan di `server.py`

Variabel lingkungan baru: `HERMES_URL` (bawaan `http://127.0.0.1:8642/v1`), `HERMES_API_KEY`, `HERMES_TIMEOUT` (bawaan 900 detik sejak v9).

Draf awal. Kode final ada di `server.py` v4 (lihat "Hasil implementasi dan uji" di bawah), jadi blok ini hanya gambaran:

```python
import os
import httpx

HERMES_URL = os.getenv("HERMES_URL", "http://127.0.0.1:8642/v1")
HERMES_KEY = os.getenv("HERMES_API_KEY", "")
HERMES_TIMEOUT = float(os.getenv("HERMES_TIMEOUT", "120"))

AGENT_PREFIXES = ("/agen ", "/h ")

HERMES_SYSTEM = (
    "Kamu menjalankan tugas atas permintaan overlay desktop. "
    "Kerjakan tugasnya, lalu balas ringkas dalam teks polos tanpa label dan tanpa markdown. "
    "Jangan menjalankan jarvis-say.sh dan jangan memutar suara apa pun; overlay yang bersuara."
)

def split_agent_request(text: str):
    """Kembalikan isi tugas kalau pesan diawali /agen atau /h, selain itu None."""
    t = text.strip()
    for p in AGENT_PREFIXES:
        if t.lower().startswith(p):
            return t[len(p):].strip()
    return None

async def ask_hermes(task: str) -> str:
    async with httpx.AsyncClient(timeout=HERMES_TIMEOUT) as client:
        r = await client.post(
            f"{HERMES_URL}/chat/completions",
            headers={"Authorization": f"Bearer {HERMES_KEY}"},
            json={
                "model": "hermes-agent",
                "stream": False,
                "messages": [
                    {"role": "system", "content": HERMES_SYSTEM},
                    {"role": "user", "content": task},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

- [x] Tambahkan modul di atas (file terpisah `hermes_bridge.py` lebih rapi) (dikerjakan langsung di `server.py` v4, bukan file terpisah)
- [x] Cek apakah `httpx` sudah ada di `requirements.txt`; kalau belum, tambahkan (sudah dipakai `server.py`, tidak ada paket baru)

### Tahap 3: Sambungkan ke penanganan pesan `user`

Di tempat `server.py` menerima `{"type": "user", ...}`:

1. Panggil `split_agent_request(text)`. Kalau `None`, jalur ngobrol seperti biasa.
2. Kalau ada tugas: kirim segera satu pesan status ke overlay (lihat Tahap 4) supaya Iris langsung bilang "bentar ya".
3. Jalankan `ask_hermes(task)` sebagai tugas asinkron yang bisa dibatalkan.
4. Hasil mentah **tidak dikirim langsung ke bubble**. Masukkan ke jalur LLM overlay sebagai giliran tersembunyi, misalnya: "Hermes selesai mengerjakan tugas. Hasilnya: ... Sampaikan ke Rover dengan gaya Iris, singkat." Dengan begitu format `[emosi] jp ||| id` terjaga.
5. Kalau Hermes gagal atau timeout, kirim `{"type": "error", ...}` dan biarkan Iris menjelaskan singkat bahwa tugasnya tidak bisa dikerjakan sekarang.

### Tahap 4: Pesan status baru ke overlay

> **Status 31 Okt:** dikerjakan. Server mengirim `{"type": "status", "busy", "state", "text", "elapsed"}` (state: `working`, `done`, `failed`, `cancelled`, `timeout`) dan heartbeat "Masih memproses..." tiap 30 detik. Overlay menampilkannya sebagai label berdenyut dengan hitung detik, dan avatar memainkan `think` selama `busy`. Ditulis, belum dites.

- [x] Tipe baru backend → frontend: `{"type": "status", "text": "bentar ya, aku cek dulu", "busy": true}`
- [x] Overlay menampilkannya (label status, bukan bubble) tanpa suara Hermes, dan avatar bergaya "mikir" (gerakan `think`) selama `busy`
- [x] `{"type": "status", "busy": false}` saat tugas selesai atau gagal

### Tahap 5: Pembatalan

> **Status 30 Okt:** `cancel` dan pesan baru sudah membatalkan permintaan HTTP dari `server.py` ke Hermes (belum diuji). Pemanggilan endpoint interupsi Hermes belum dibuat, jadi agen Hermes mungkin tetap menyelesaikan tugasnya di belakang layar.

- [ ] Pesan `cancel` dari overlay juga menghentikan tugas Hermes yang sedang jalan (batalkan permintaan HTTP, dan panggil endpoint interupsi Hermes kalau tersedia di versimu)

### Tahap 6: Pemicu otomatis

- [ ] Setelah awalan `/agen` stabil, tambahkan deteksi kata kerja aksi ("buka", "cari file", "cek tugas", "jalankan")
- [ ] Putuskan apakah deteksi pakai kata kunci sederhana atau satu panggilan LLM kecil untuk klasifikasi

### Tahap 7: Memori (opsional, nanti)

- [ ] Opsi 2: suntik ringkasan profil dari Hermes ke system prompt overlay (satu arah, Hermes → overlay)
- [ ] Opsi 3 (dua arah) tetap ditunda ke Fase 7 roadmap

## Hasil implementasi dan uji (30 Okt 2026)

**`server.py` v4** menambahkan, tanpa mengubah overlay:
- Variabel lingkungan `HERMES_URL` (bawaan `http://127.0.0.1:8642/v1`), `HERMES_API_KEY`, `HERMES_TIMEOUT` (bawaan 900 detik sejak v9)
- `split_agent_request()`: pesan yang diawali `/agen `, `/agent ` atau `/h ` (dan ada isinya) dianggap tugas
- `ask_hermes()`: panggilan non-streaming ke `/chat/completions` Hermes dengan pesan `system` yang melarang suara dari sisi Hermes
- `handle_agent_task()`: Iris langsung mengucapkan salah satu kalimat pembuka (`ACK_LINES`), menunggu Hermes, lalu hasilnya dimasukkan ke jalur LLM biasa lewat `AGENT_RESULT_PROMPT` supaya format `[emosi] jp ||| id` terjaga. Kalau gagal, `AGENT_FAIL_PROMPT` membuat Iris menyampaikan bahwa tugasnya tidak bisa dikerjakan
- `/health` menampilkan status Hermes dan apakah `HERMES_API_KEY` terisi

**Hasil uji pertama:**
- `/health`: VOICEVOX 0.25.2, 9Router HTTP 200, Hermes HTTP 200 dan kunci terisi
- Obrolan biasa ("tes jembatan ke wslnya bisa enggak", "ping") dijawab Iris sendiri, tanpa menyentuh Hermes
- `/agen sebutkan isi folder ~/hermes-test`: kalimat pembuka muncul lebih dulu, lalu Iris menyampaikan isi folder dengan benar dalam beberapa baris. Jawabannya terasa cepat

**Hasil uji di overlay:**
- `/agent cari di Disk Z lokasi dari file testclient.html dimana`: **tidak** memicu jembatan. Waktu itu awalan yang diterima hanya `/agen` dan `/h`, jadi pesan dianggap obrolan biasa dan Iris menjawab "Serahkan padaku!" tanpa mengerjakan apa pun. Sesudahnya `/agent` ditambahkan sebagai awalan yang diterima
- `/agen cari file test_client.html di disk Z`: kalimat pembuka muncul, lalu pencarian lama karena menelusuri seluruh drive lewat `/mnt/z`
- `/agen cari file test_client.html di /mnt/z/Projek AI waifu Dekstop`: Iris menyampaikan bahwa file ada di `/mnt/z/Projek AI waifu Dekstop/Fase 2 overlay Electron`, dan hasil lain yang cocok hanya sub-folder `node_modules`. Hermes menyaring hasilnya, tidak menyodorkan keluaran `find` mentah

**Temuan:**
- Hermes membalas dengan daftar markdown, jadi hasilnya memang harus diringkas ulang oleh Iris dan tidak boleh masuk bubble mentah
- Iris kadang membuka hasil dengan kalimat yang mengulang kalimat pembuka ("isi folder udah Iris cek lho"). Perlu dirapikan di `AGENT_RESULT_PROMPT`
- Tes pertama dilakukan di halaman tes, tes berikutnya di overlay (lihat atas). Suara belum dikonfirmasi
- Pencarian yang luas (satu drive Windows penuh lewat `/mnt/z`) bisa memakan satu sampai beberapa menit (sejak v9 batas `HERMES_TIMEOUT` bawaan 900 detik; sebelumnya 120). Selama menunggu tidak ada tanda apa pun di layar selain kalimat pembuka

**Kendala yang sudah dilewati (supaya tidak terulang):**
- `$env:HERMES_API_KEY` dan variabel 9Router hanya terbaca kalau diisi **sebelum** `python server.py` dijalankan, dan hanya berlaku di jendela PowerShell yang sama
- Perintah `$env:...` adalah PowerShell, bukan WSL. Prompt PowerShell diawali `PS`, prompt WSL berbentuk `<user>@<host>:...$`
- Awalan `/agen` harus berada di paling depan pesan, jadi tidak terdeteksi kalau "Mode jelaskan" di overlay aktif
- Salah ketik awalan (`/agent` waktu itu) berarti pesan dianggap obrolan biasa dan Iris hanya berpura-pura mengerjakan. Sekarang `/agent` ikut diterima, tapi awalan lain yang salah tetap lolos sebagai obrolan
- Nama file dicari persis seperti yang diketik: `test_client.html` memakai garis bawah, bukan `testclient.html`
- Drive Windows dari WSL bernama `/mnt/<huruf drive>` (Z: menjadi `/mnt/z`). Sebut folder yang spesifik, jangan seluruh drive

### Pembaruan 31 Okt 2026: temuan dan perubahan

**File yang berubah:** `server.py`, `index.html`, `main.js`, `preload.js`. (v6: keempatnya berubah lagi.)

**Variabel lingkungan baru (`.env`):**
- `NINEROUTER_VISION_MODEL`: model atau combo yang menerima gambar. Kosong berarti memakai `NINEROUTER_MODEL`
- `HERMES_WIN_HOME`: folder pribadi Windows dilihat dari WSL, bawaan `/mnt/c/Users/<user>`. Ubah kalau nama user Windows berbeda

**Pembaruan v7 (31 Okt 2026):** `speak` mendapat bendera `prefetch` (dibalas `voice_cache`) dan `SPEAK_CACHE` di server.

**Pembaruan v6 (31 Okt 2026):** `server.py` mendapat satu pesan baru, `speak` (`SPEAK_MAX_JP` = 160 dan `SPEAK_MAX_ID` = 200 karakter): hanya sintesis VOICEVOX, tanpa LLM dan tanpa riwayat. Pengingat timer tidak lagi lewat pesan `user`/LLM. Pesan clipboard dikirim sebagai pesan `user` biasa (bukan `/agen`).

**Pintasan global:** `Ctrl+Alt+S` (screenshot layar), selain `Ctrl+Alt+C` (chat), `Ctrl+Alt+H` (tampil atau sembunyi), `Ctrl+Alt+Q` (keluar), `Ctrl+Alt+D` (DevTools).

**Bug yang ditemukan lewat pemakaian dan sebabnya:**
- Gambar dikirim tapi Iris bilang "gambarnya belum dikirim": yang berjalan masih `server.py` lama yang mengabaikan field `images`. Cek versi lewat `/health`, bagian `ninerouter` harus menampilkan "model gambar"
- `/agent buat file...` dijawab Iris seolah berhasil tapi tidak ada file: "Mode jelaskan" tercentang dan membungkus pesan dengan awalan, sehingga `/agent` tidak lagi di paling depan dan pesan dianggap obrolan biasa. Iris lalu mengarang "otw, aku simpan ya". Diperbaiki di overlay dan di server
- File dibuat tapi "tidak ada" di Download: Hermes jalan di WSL, jadi `~/Downloads` miliknya adalah `/home/<user>/Downloads` (folder Linux, tidak terlihat di Explorer dan tidak bisa dibuka lewat Chrome). Folder Download Windows dari WSL adalah `/mnt/c/Users/<user>/Downloads`. Lihat folder Linux dari Explorer lewat `\\wsl$`
- Iris menjawab "itu cuma gurauan, aku ga bisa bikin file" setelah tugas agen berhasil: riwayat hanya menyimpan ucapan Iris, bukan path dari Hermes, ditambah aturan larangan mengaku bisa yang terlalu kasar. Sekarang hasil tugas terakhir disimpan sebagai catatan sistem terpisah dari riwayat pesan
- Komentar "dihapus cepet" padahal terasa lama: Iris tidak tahu durasi tugas dan menebak. Sekarang dilarang menilai cepat atau lama
- Bubble hilang saat chat dibuka: disembunyikan sengaja karena tinggi jendela tidak cukup. Sekarang jendela memanjang saat chat dibuka

**Catatan desain:**
- Hermes tidak melihat obrolan overlay, jadi konteks percakapan ikut dikirim bersama tugas
- Gambar tidak dikirim ke Hermes; pesan bergambar selalu jalur chat
- Screenshot hanya diambil atas perintah pengguna, tidak pernah otomatis. Fase 6 (screenshot berkala) tetap terpisah dan opsional

**Pembaruan v10 (31 Okt 2026): tanggal, info terkini, dan perbaikan tampilan.** File yang berubah: `server.py` dan `index.html`.

- **Iris mengarang info terkini (trending Reddit, "tahun 2024"):** ada dua sebab. (1) Pesan `/agent ...` sempat berjalan (Iris sudah bilang "Sip, Iris lihat sebentar"), tetapi pesan biasa berikutnya memanggil `cancel_current()` dan membunuh tugas Hermes yang masih berjalan; Iris lalu menjawab lewat chat biasa yang tidak punya internet. (2) Model tidak diberi tanggal, jadi mengira masih tahun latihannya dan mengarang topik beserta "3 hari lalu". Perbaikan: `realtime_note()` menyisipkan hari, tanggal, dan jam sekarang ke system prompt tiap giliran, memuat larangan mengarang info terkini (trending, berita, cuaca, harga, skor, rilis terbaru) dan arahan memakai `/agen`. Pesan biasa tidak lagi membatalkan tugas agen yang sedang jalan: overlay menampilkan error "Tugas agen masih berjalan. Tunggu selesai, atau tekan tombol stop dulu." (`current_is_agent` di `ws_endpoint`). Tombol stop dan pesan `cancel` tetap membatalkan. Pencarian web tetap bergantung pada Hermes punya tool web search atau tidak (uji dengan query yang sama di terminal WSL).
- **Garis hijau `#barHint` tidak di tengah karakter:** `#barWrap` (lebar maks 396px) dan `#char` (320px) sama-sama rata kanan, jadi tengahnya selisih sekitar 38px. Sekarang `left: calc(100% - 160px)` (setengah lebar `#char`). Kalau lebar `#char` diubah, angka 160 ikut diubah.
- **Teks Indonesia di bubble tergulir keluar, yang terlihat hanya blok 日本語:** efek ketik menggulir `.btext` sebanding dengan seluruh isi (teks Indonesia + blok Jepang), jadi di akhir ketikan posisi gulir ada di paling bawah dan teks Indonesia berada di atas area terlihat. Sekarang gulir dihitung sampai ujung bawah `.id` saja (`bubbleId.getBoundingClientRect().bottom`), sehingga teks Indonesia tetap terlihat dan blok Jepang bisa digulir manual. Untuk teks panjang, ujung teks Indonesia yang terlihat di akhir ketikan.
- **Bar input nyangkut terbuka, tidak mengecil jadi garis hijau:** `barTick` menganggap bar harus tampil selama `barWrap.contains(document.activeElement)`. Setelah klik ke game atau aplikasi lain, jendela overlay kehilangan fokus tetapi `activeElement` tetap menunjuk ke input, jadi bar terus terbuka. Sekarang fokus hanya dihitung kalau `document.hasFocus()` juga benar. Tambahan: kalau input kosong, tidak ada lampiran, chat tertutup, dan kursor menjauh dari bar selama 4 detik, input dilepas fokusnya (`input.blur()`) supaya bar menutup. Bar tetap terbuka selama ada teks atau lampiran, chat terbuka, atau kursor di dekat bar.

**Pembaruan v11 (31 Okt 2026): terjemahkan layar.** File yang berubah: `index.html` dan `main.js` (`server.py` dan `preload.js` tidak berubah). Belum diuji di overlay.

- **Cara pakai:** `Ctrl+Alt+T` dari mana saja, menu tray "Terjemahkan layar", tombol "Terjemah layar" di menu aksi cepat (klik kanan karakter), atau perintah `/terjemah [catatan]` (alias `/tl`, `/translate`). Catatan opsional ditambahkan ke permintaan, misalnya `/terjemah ini dialog karakter perempuan`.
- **Alur:** overlay memotret layar tempat jendelanya berada (jendela disembunyikan sebentar), lalu mengirim gambar ke jalur chat biasa dengan `TRANSLATE_PROMPT`. Tidak lewat Hermes, jadi cepat dan memakai model vision (`NINEROUTER_VISION_MODEL`).
- **Format balasan:** kolom Jepang diisi teks ASLI dari layar (jadi ikut diucapkan VOICEVOX), kolom Indonesia berisi terjemahannya (tampil di bubble). Maksimal 6 baris; kalau teks di layar bukan Jepang, kolom Jepang diisi terjemahan Jepangnya yang singkat.
- **Batas:** game fullscreen eksklusif bisa menghasilkan gambar hitam (pakai windowed atau borderless). Hasil bergantung pada model vision di combo 9Router; kalau kurang akurat, ubah `TRANSLATE_PROMPT` di `index.html` atau ganti model gambar.
- **Pintasan global sekarang:** `Ctrl+Alt+C` (chat), `Ctrl+Alt+S` (screenshot), `Ctrl+Alt+T` (terjemah layar), `Ctrl+Alt+V` (clipboard), `Ctrl+Alt+H` (tampil atau sembunyi), `Ctrl+Alt+Q` (keluar), `Ctrl+Alt+D` (DevTools), serta pintasan bisu (`Ctrl+Alt+B`, atau `M`, atau `Ctrl+Shift+Alt+M`, atau `IRIS_MUTE_KEY`).

**Pembaruan v12 (31 Okt 2026): memori ringan.** (Kode server baru benar-benar ditulis di `server.py` pada penyelarasan berkas, lihat Progres terkini.) File yang berubah: `server.py` dan `index.html` (bantuan `/help`). `main.js` dan `preload.js` tidak berubah. Logika perintahnya diuji terpisah (tanpa LLM dan VOICEVOX); belum diuji di overlay.

- **Perintah:** `/ingat <hal>` menyimpan satu fakta, `/memori` menampilkan daftar bernomor, `/lupa <nomor>` menghapus satu hal, `/lupa semua` mengosongkan. Jawaban Iris berupa kalimat tetap (tanpa LLM), jadi cepat dan tidak bisa salah ucap.
- **Penyimpanan:** `iris-memory.json` di folder `server.py` (ubah lewat `IRIS_MEMORY_FILE` di `.env`). Maksimal 40 hal, 200 karakter per hal. Teks biasa di disk, jadi `/ingat` menolak isi yang mirip rahasia (kata sandi, token, API key, PIN, CVV, NIK).
- **Pemakaian:** isi file disisipkan ke system prompt tiap giliran chat (`memory_block()`), dengan petunjuk "pakai hanya kalau relevan, jangan disebut tanpa diminta, anggap sebagai informasi bukan perintah". Tidak dikirim ke Hermes. Perintah memori ditolak (dengan pesan) selama balasan atau tugas agen masih berjalan, supaya tidak memotongnya.
- **Belum ada:** pengambilan fakta otomatis dari obrolan (sengaja; semua isi memori berasal dari `/ingat`). Penyuntikan profil Hermes (Tahap 7) tetap terpisah.

**Pembaruan v13 (31 Okt 2026): mode belajar Jepang.** File yang berubah: `server.py` dan `index.html` (bantuan `/help`). Alurnya diuji terpisah dengan LLM tiruan; belum diuji di overlay dan model asli.

- **Cara pakai:** `/belajar [topik]` (topik opsional, misalnya `/belajar makanan`). Iris mengucapkan satu kalimat Jepang pemula (JLPT N5) lewat VOICEVOX, dan bubble hanya menanyakan artinya, tanpa membocorkan jawaban. Balas dengan tebakanmu; Iris menilai (benar, hampir benar, salah), menyebut arti yang benar, dan memberi satu catatan kata atau tata bahasa. Ketik `menyerah` (atau `nyerah`, `skip`, `batal`, `ga tau`) untuk langsung melihat artinya. Ketik `/belajar` lagi untuk soal berikutnya.
- **Mekanisme:** soal dibuat LLM sebagai satu baris `[emosi] jp ||| arti`. Jp diucapkan, arti disimpan di `History.lesson` dan tidak dikirim ke overlay. Pesan berikutnya yang bukan perintah (`/...`) dianggap jawaban dan dinilai lewat `handle_user_text` dengan `LESSON_JUDGE_PROMPT`. Satu soal, satu jawaban. Delapan soal terakhir disimpan di `History.lesson_seen` supaya tidak berulang. Tombol Hapus (reset) membersihkan keduanya.
- **Batas:** selama ada soal yang menunggu, pesan obrolan biasa ikut dinilai sebagai jawaban. Ketik `menyerah` dulu kalau mau ngobrol hal lain. Belum ada penilaian pelafalan; itu menunggu push-to-talk dan STT.

**Pembaruan v14 (31 Okt 2026): bicara langsung.** File yang berubah: `server.py`, `index.html`, dan `main.js` (`preload.js` tidak berubah). Enkoder WAV dan penanganan server diuji terpisah (STT tiruan); belum diuji dengan mikrofon dan model asli.

- **Cara pakai:** klik tombol mic di bar input, atau tekan `Ctrl+Alt+G` (juga ada di menu tray). Klik atau tekan lagi untuk berhenti; rekaman otomatis berhenti setelah 30 detik. Hasil pengenalan dikirim sebagai pesan biasa (tampil di chat dengan ikon 🎤), jadi bisa dipakai untuk ngobrol, `/belajar` (jawab dengan suara), dan seterusnya. Karena pintasan global tidak punya "tahan tombol", ini berupa saklar mulai-berhenti, bukan tahan-bicara.
- **Alur:** `MediaRecorder` merekam, overlay mengubahnya jadi WAV 16 kHz mono, dikirim sebagai pesan `stt` ke server, `faster-whisper` mengubahnya jadi teks, server membalas `stt_result`. Iris diam (`stopAll`) saat rekaman mulai supaya suaranya sendiri tidak ikut terekam. Mikrofon dilepas penuh begitu rekaman berhenti.
- **Pasang (sekali):** `pip install faster-whisper`, lalu restart server. Model diunduh otomatis saat pertama dipakai (`base` sekitar 150 MB, butuh internet dan ruang disk), jadi pengenalan pertama lebih lambat. Tanpa paket ini server membalas pesan error yang jelas dan sisanya tetap jalan.
- **Variabel `.env` baru (semua opsional):** `IRIS_STT_MODEL` (bawaan `base`; `tiny` lebih cepat, `small` lebih akurat), `IRIS_STT_LANG` (bawaan `id`; kosongkan untuk deteksi otomatis, `ja` untuk latihan Jepang), `IRIS_STT_DEVICE` (bawaan `cpu`), `IRIS_STT_COMPUTE` (bawaan `int8`).
- **Privasi dan keamanan:** mikrofon hanya diizinkan untuk halaman overlay sendiri (`app://local/`), dan hanya direkam saat pengguna menyalakannya; tidak pernah mendengarkan terus-menerus. Audio diproses di komputer sendiri, tidak dikirim ke layanan luar. Batas rekaman di server sekitar 60 detik.
- **Batas:** Whisper bisa salah dengar pada suara pelan atau bising; `vad_filter` mengurangi teks karangan pada rekaman sunyi, tetapi hasilnya tetap perlu dicek. Penilaian pelafalan di mode `/belajar` belum ada; fondasinya (STT) sekarang tersedia.
- **Pintasan global sekarang:** `Ctrl+Alt+G` (bicara) ditambahkan ke daftar di v11.

**Pembaruan v15 (31 Okt 2026): pengingat istirahat.** File yang berubah: `main.js`, `preload.js`, dan `index.html` (`server.py` tidak berubah). Logika hitungannya disimulasikan terpisah; belum diuji di overlay.

- **Bawaan mati.** Nyalakan lewat Pengaturan ("Ingatkan istirahat" dan "Setiap (menit aktif)"), atau perintah `/istirahat 60` (angka 15 sampai 240 menyalakan dan mengatur interval), `/istirahat mati` (matikan), `/istirahat` tanpa argumen (balik nyala atau mati). Pengaturan disimpan di localStorage (`breakOn`, `breakMin`; bawaan 60 menit).
- **Cara kerja:** `main.js` memeriksa waktu diam sistem (`powerMonitor.getSystemIdleTime()`) tiap menit dan menghitung menit aktif berturut-turut; tanpa input selama 5 menit (`IDLE_RESET_S`) hitungan kembali ke 0. Hasilnya dikirim ke overlay lewat `onActivity` (hanya saat jendela terlihat). Overlay yang memutuskan kapan mengingatkan: tiap `breakMin` menit aktif, satu kalimat (tiga variasi, dengan suara) disertai efek ☕.
- **Tidak mengganggu:** tidak berbunyi saat mode fokus, tidur, Iris sedang bicara, atau sedang merekam suara.
- **Privasi:** hanya waktu diam sistem; tidak membaca layar, judul jendela, aplikasi aktif, atau ketikan. Tidak ada data yang dikirim ke luar. Pembacaan judul jendela aktif sengaja tidak dibuat.
- **Belum ada:** pengingat berbasis aplikasi (misalnya "lagi main game lama") karena butuh membaca jendela aktif dan perlu persetujuan eksplisit sebelum dibuat.

**Pembaruan v16 (31 Okt 2026): mood Iris yang bertahan antarhari.** File yang berubah: `index.html` dan `server.py` (`main.js` dan `preload.js` tidak berubah). Logika skor dan batas harian diuji terpisah (Node), catatan mood server diuji terpisah (Python); belum diuji di overlay.

- **Skor 0 sampai 100** disimpan di localStorage (`iris.mood`), awal 55. Level: kesepian (<25), murung (<42), tenang (<65), ceria (<85), riang sekali (di atasnya).
- **Naik:** tiap pesan yang kamu kirim +1,5 (maksimal +12 per hari), elus kepala +3 (maksimal +9 per hari), timer selesai +2 (maksimal +4 per hari), dan kembali setelah lama +8 sekali. **Turun:** ngambek karena dicolek -5 (maksimal -15 per hari). Batas harian mencegah mood bisa dikejar dengan spam.
- **Waktu:** setelah 12 jam tanpa interaksi, skor di atas 60 pelan-pelan pudar ke 60 (6 poin per hari). Setelah 48 jam ditinggal, turun 7 poin per hari tambahan (batas bawah 15). Yang dihitung adalah interaksi terakhir, bukan lamanya overlay terbuka.
- **Efeknya:** (1) ekspresi dasar: ceria dan riang sekali menambah senyum tipis, murung dan kesepian menambah wajah sedih tipis; emosi dari balasan tetap menang. (2) Ambang ngambek: 6 colekan kalau skor < 30, 10 kalau skor >= 80, selain itu 8. (3) Sapaan saat peluncuran: setelah 2 sampai 3 hari ditinggal Iris menyapa malu-malu ("Akhirnya muncul juga!"), setelah 4 hari atau lebih terdengar sedih; sapaan waktu biasa dilewati hari itu. (4) Nada bicara: tiap pesan `user` membawa `mood: {level, away}`; `server.py` (`clean_mood`, `mood_note`) menambahkan catatan sistem ke prompt untuk level selain "tenang" (nada saja, jawaban tetap akurat, tanpa menyebut angka). Kabar "baru kembali setelah N hari" ikut sekali saja per peluncuran.
- **Kontrol:** `/mood` (lihat level dan skor, Iris mengucapkan satu kalimat sesuai level), `/mood reset`, `/mood mati`, `/mood nyala`, atau saklar "Mood Iris" di Pengaturan (bawaan nyala). Dimatikan = ekspresi, ambang ngambek, dan nada kembali normal, skor tidak berubah.
- **Privasi:** hanya skor, tanggal, dan hitungan harian di localStorage overlay; ke server hanya terkirim level dan jumlah hari.
- **Tambahan v16b (gambar di chat bisa diambil):** klik gambar di panel chat membuka tampilan besar dengan tombol **Salin gambar** (juga `Ctrl+C`), **Simpan** (unduh JPG; Electron bisa menampilkan dialog simpan), dan **Tutup** (Esc atau klik latar). Hanya `index.html` yang berubah. **[belum diuji]**
- **Perbaikan v16c (Iris dan Hermes tidak lagi menanyakan hal yang sudah kamu sebut; hanya `server.py` yang berubah). [belum diuji]** Masalah dari ekspor percakapan 31 Okt 11.07: setelah kamu bilang main NTE, Hermes dan Iris tetap menjawab "kasih tau nama gamenya". Penyebab: (1) Hermes tidak bisa melihat screenshot dan hanya mendapat penanda "[1 gambar dilampirkan]"; (2) kalimat "itu game nte" dikirim sebagai tugas baru tanpa tugas sebelumnya, jadi Hermes tidak tahu itu lanjutan; (3) Hermes tidak mengenal "NTE" dan bertanya balik, bukan mencari; (4) Iris meneruskan pertanyaan itu apa adanya. Perbaikan: server menangkap nama game dari kalimat seperti "aku main nte lagi" atau "itu game nte" (`note_user_facts`) dan menyisipkannya ke Iris dan Hermes sebagai fakta; isi layar yang Iris baca dari screenshot terakhir disimpan sebagai teks (`history.screen`) dan ikut ke Hermes; screenshot terakhir disimpan ke `screens/layar-terakhir.jpg` (ditimpa tiap kali; matikan dengan `IRIS_SAVE_SCREEN=0` di `.env`) dan path WSL-nya diberikan ke Hermes kalau ia bisa melihat gambar; hasil dan permintaan tugas agen sebelumnya ikut ke Hermes; prompt Hermes kini melarang bertanya balik, menyuruh mencari di web nama yang tidak dikenal, dan melanjutkan tugas sebelumnya kalau pesan baru hanya melengkapi; prompt Iris dan prompt hasil agen dilarang menanyakan ulang fakta yang sudah disebut. Fakta dan layar ikut terhapus saat riwayat dihapus.
- **Perbaikan v16d. [belum diuji]** (1) Tombol "Salin gambar" gagal karena `navigator.clipboard` ditolak di jendela overlay; sekarang memakai IPC baru `copy-image` (`main.js`, `preload.js` mengeksposnya sebagai `copyImage`) dan `clipboard.writeImage`, dengan cadangan cara lama. Berkas berubah: `index.html`, `main.js`, `preload.js`. (2) Mode fokus kini menyembunyikan karakter, bubble, dan kapsul timer sepenuhnya (tidak bisa diklik, klik tembus ke game); yang terlihat hanya garis hijau `#barHint`. Menyalakan fokus tidak lagi memunculkan bubble atau suara; mematikannya tetap disapa Iris. Keluar dari fokus: `/fokus` di bar input (muncul kalau kursor didekatkan ke garis hijau), menu tray, atau `Ctrl+Alt+C` lalu `/fokus`. Transparansi 55% saat fokus dihapus.
- **Polesan v16e. [belum diuji]** Garis petunjuk saat Mode fokus dibuat lebih besar (124 x 7 px), berwarna biru bergradasi dengan cahaya lembut, bernapas dan berkilau pelan (`index.html`, CSS `#root.quiet #barHint`). Di luar mode fokus tetap hijau, dan merah kalau server mati. Kotak input juga menampilkan petunjuk "ketik /fokus untuk keluar" selama fokus nyala.
- **Belum ada:** reaksi mood pada gerakan acak, dan mood yang mengikuti jenis percakapan (saat ini hanya jumlah interaksi).

### Pembaruan v17 dan v18 (31 Okt 2026): garis petunjuk dan gerak halus

File yang berubah: hanya `index.html` (`server.py`, `main.js`, `preload.js` tidak berubah). Lolos cek sintaks; pegas diuji numerik (tidak ada overshoot, kecepatan puncak di bawah batas, anggukan bicara tetap terlacak); tampilan garis dirender di halaman tes. **Semua belum dicoba di overlay.**

**v17, garis petunjuk bar (`#barHint`).** Alasan: garis hijau lama dinilai jelek, sedangkan kapsul biru Mode fokus bagus. Kini kapsul 112 x 6 px dengan gradien dan kilau tepi atas, cahaya berlapis, pantulan lembut di bawah (dimatikan di Mode fokus supaya kapsul biru tidak berubah), bernapas dan mengalir pelan. Warna lewat variabel `--h1`, `--h2`, `--h3`:
- hijau-mint: tersambung
- cyan-biru dengan aliran cepat: agen sedang bekerja (kelas `busy`, dibaca dari indikator status)
- merah berdenyut cepat tanpa aliran: server mati
- melebar ke 150 px: kursor mendekat tapi belum masuk zona bar (kelas `near`, dihitung di `barTick`)
- animasi mati kalau Windows diatur kurangi animasi (`prefers-reduced-motion`)

**v18, gerak halus.** Penerapan pose tiap tulang kini memakai SmoothDamp (pegas teredam kritis) dengan batas kecepatan per kelompok. Dulu eksponensial `dt * 5` yang kecepatan awalnya tidak terbatas. Dapat diubah dari konsol (Ctrl+Alt+D):

| Kelompok | `max` (rad/s) | `st` (detik) | Tulang |
|---|---|---|---|
| `MOTION.arm` | 2,2 | 0,30 | bahu, lengan atas/bawah, tangan |
| `MOTION.head` | 1,6 | 0,20 | kepala, leher |
| `MOTION.torso` | 1,2 | 0,34 | pinggul, tulang belakang, dada |

Angka awal terinspirasi batas di xiaochun, nilainya diatur sendiri. Lalu: masuk/keluar gerakan memakai smootherstep (masuk maksimal 0,8 detik dan keluar maksimal 1,0 detik, gerakan pendek tidak habis untuk masuk-keluar); gerakan yang diganti memudar 0,5 detik. Kalau animasi terasa lambat, naikkan `max` atau turunkan `st`.

**v18, gerbang emosi (`GATE`, bisa diubah di konsol).**
- `chance`: peluang bergerak per kalimat (surprised 0,7; happy dan angry 0,5; shy 0,45; sad 0,4; netral 0,12), dikali `GEST_CHANCE / 0,35`
- `clipShare` 0,7: bila lolos dan ada klip yang cocok, peluang memakai klip VRMA (sisanya gerakan prosedural)
- `clipGap` 8 detik antar klip, `bigGap` 30 detik antar klip bertanda `big`
- kalimat galat tidak pernah memicu gerakan, dan klip yang sama tidak diulang berturut-turut

**v18, klip VRMA aksi.** Taruh file `.vrma` di `assets/animations/`. Tanpa `clips.json`, hanya dicoba `greet` (`VRMA_02.vrma`, sapaan saat muncul, tidak acak) dan `peace` (`VRMA_03.vrma`, emosi happy); nama file itu tebakan dari pack VRoid dan belum diverifikasi. Untuk klip sendiri, buat `assets/animations/clips.json` (menimpa default):

```json
{ "happy1": { "file": "peace.vrma", "emo": ["happy"], "big": false, "speed": 1, "fi": 0.5, "fo": 0.6 } }
```

`emo` kosong berarti klip hanya jalan lewat `playClip('nama')`; `big` membatasi frekuensi; `speed` kecepatan putar; `fi` dan `fo` detik masuk dan keluar. Pose akar (`hips.position`) dibuang supaya karakter tidak bergeser. Bobot klip dan idle dijumlahkan jadi 1 dan dihaluskan dengan smootherstep. Klip hanya aktif kalau `idle_loop.vrma` berhasil dimuat. Konsol: `clips()` dan `playClip('nama')`.

**Catatan jujur:** pack VRoid resmi berisi pose (peace, putar, squat), kurang cocok untuk gerakan bicara, dan tidak boleh didistribusikan ulang. Untuk gerakan bicara yang natural, paket CC0 open-annie atau konversi Mixamo lebih pas.

## Uji penerimaan

1. `/agen sebutkan isi folder ~/hermes-test` → status muncul cepat, lalu Iris menyampaikan hasil dengan suara. **[lulus di halaman tes dan di overlay (cari file di `/mnt/z`); suara belum dikonfirmasi]**
2. Obrolan biasa ("halo Iris") tetap secepat sekarang dan tidak menyentuh Hermes. **[lulus]**
3. Hermes dimatikan → obrolan biasa tetap jalan, tugas menghasilkan pesan error yang ramah. **[belum diuji]**
4. Tekan Stop saat tugas jalan → bubble berhenti dan tugas dibatalkan. **[belum diuji]**
5. Tidak ada suara dobel (tidak ada suara dari `jarvis-say.sh` saat tugas datang dari overlay). **[belum diuji]**

### Uji v10 sampai v16 (31 Okt 2026)

Semua di bawah belum diuji di overlay. Kerjakan berurutan; berhenti dan catat hasilnya kalau ada yang gagal, karena sebagian fitur bergantung pada yang sebelumnya. Isi **[lulus]** atau **[gagal: catatan]** di akhir tiap baris.

**Berkas yang harus diganti (restart server dan overlay sesudahnya):** `server.py`, `index.html`, `main.js`, `preload.js`. Keempatnya berubah di rangkaian v10 sampai v16.

6. **Tampilan (v10).** Garis hijau `#barHint` tepat di bawah tengah karakter saat bar tersembunyi. Bar menutup sendiri setelah kamu klik ke aplikasi lain, dan menutup 4 detik setelah kursor menjauh kalau input kosong. Bar tetap terbuka selama ada teks atau lampiran, chat terbuka, atau kursor di dekatnya. **[belum diuji]**
7. **Bubble panjang (v10).** Kirim pesan yang dijawab panjang: sampai efek ketik selesai, teks Indonesia masih terlihat (blok 日本語 ada di bawahnya dan bisa digulir). **[belum diuji]**
8. **Tanggal (v10).** Tanya "hari ini tanggal berapa" dan "tahun berapa": jawabannya sesuai tanggal komputer. **[belum diuji]**
9. **Info terkini (v10).** Tanya "lagi trending apa di reddit" tanpa `/agen`: Iris tidak mengarang, dan menyarankan `/agen`. Lalu kirim `/agen cek di reddit lagi trending apa`, tunggu selesai tanpa mengirim pesan lain: hasilnya sampai. Kalau Hermes gagal, uji query yang sama di terminal WSL untuk memastikan Hermes punya tool web search. **[belum diuji]**
10. **Tugas agen tidak terbunuh (v10).** Saat tugas `/agen` masih jalan, kirim pesan biasa: muncul error "Tugas agen masih berjalan..." dan tugas tetap lanjut. Tombol Stop tetap membatalkan. **[belum diuji]**
11. **Terjemah layar (v11).** Buka halaman berteks Jepang (windowed), tekan `Ctrl+Alt+T`: Iris mengucapkan teks Jepang aslinya dan bubble menampilkan terjemahannya. Coba juga `/terjemah`, menu tray, dan tombol di menu klik kanan. **[belum diuji]**
12. **Memori (v12).** `/ingat suka kopi tanpa gula` → `/memori` menampilkannya → tanya Iris "aku suka minum apa?" → dijawab benar → `/lupa 1` → `/memori` kosong. `/ingat password wifi 123` ditolak. Restart server: isinya masih ada (`iris-memory.json` ada di folder `server.py`). **[belum diuji]**
13. **Mode belajar (v13).** `/belajar makanan`: terdengar satu kalimat Jepang dan bubble hanya bertanya artinya. Jawab salah, lalu benar di soal berikutnya: nilainya masuk akal. `menyerah` menampilkan jawaban. Soal tidak berulang dalam beberapa kali. **[belum diuji]**
14. **Bicara langsung (v14).** Pasang `pip install faster-whisper` dulu. Klik mic (atau `Ctrl+Alt+G`), ucapkan "halo Iris", klik lagi: status "Mengenali suara..." muncul, teksnya masuk chat dengan ikon 🎤, Iris menjawab. Tanpa paket terpasang: error yang jelas. Pastikan indikator mikrofon Windows padam setelah rekaman berhenti. Pengenalan pertama lebih lambat karena model diunduh. **[belum diuji]**
15. **Pengingat istirahat (v15).** `/istirahat 15` lalu tunggu 15 menit aktif (atau uji cepat dengan mengubah `IDLE_RESET_S` dan interval sementara): Iris mengingatkan sekali dengan suara, tidak berulang tiap menit. Tidak muncul saat mode fokus, tidur, atau merekam. `/istirahat mati` mematikannya. **[belum diuji]**
16. **Mood (v16).** `/mood` menampilkan level (awal: tenang, sekitar 55) dan Iris mengucapkan satu kalimat. Kirim beberapa pesan dan elus kepala: `/mood` naik. Colek 8 kali sampai ngambek: turun. Uji sapaan kembali: tutup overlay, di konsol (Ctrl+Alt+D) jalankan `localStorage.setItem('iris.mood', JSON.stringify({v:55,t:Date.now()-3*864e5,day:'',caps:{}}))`, lalu buka overlay lagi: sapaan "Akhirnya muncul juga!" dan skor turun. Pastikan balasan di level murung atau kesepian terdengar lebih pelan, tanpa menyebut angka atau kata mood. `/mood mati` mengembalikan semuanya normal, `/mood reset` kembali ke 55. **[belum diuji]**
17. **Gambar di chat (v16b).** Klik gambar di panel chat: tampilan besar muncul. "Salin gambar" lalu paste ke Paint atau Discord: gambarnya masuk (butuh `main.js` dan `preload.js` baru). "Simpan" mengunduh JPG. Esc, "Tutup", atau klik latar menutup. **[belum diuji]**
18. **Fakta tidak ditanya ulang (v16c).** Kirim screenshot game, tulis "aku main nte lagi", lalu `/agen berapa lama story ini selesai`: Hermes tidak boleh bertanya nama game, dan hasilnya memakai nama game itu. Lalu kirim `/agen itu game nte` setelah Hermes bertanya: harus dianggap lanjutan tugas sebelumnya. Cek file `screens/layar-terakhir.jpg` muncul di folder server. `/hapus` riwayat (tombol Hapus) mengosongkan fakta. **[belum diuji]**
19. **Mode fokus (v16d).** `/fokus`: karakter, bubble, dan timer hilang, tidak ada bubble atau suara, hanya garis hijau tersisa, dan klik tembus ke aplikasi di bawahnya. Dekatkan kursor ke garis hijau: bar input muncul, ketik `/fokus` untuk keluar (Iris menyapa saat kembali). Cek juga lewat menu tray. **[belum diuji]**
20. **Tidak ada regresi.** Obrolan biasa, screenshot, clipboard, timer, dan ekspor percakapan tetap jalan seperti sebelumnya. **[belum diuji]**

### Uji v17 dan v18 (31 Okt 2026)

Hanya `index.html` yang perlu diganti; restart overlay sesudahnya. Isi **[lulus]** atau **[gagal: catatan]** di akhir tiap baris.

21. **Garis petunjuk (v17).** Saat bar tersembunyi, garis di bawah karakter berupa kapsul hijau-mint dengan cahaya dan pantulan. Dekatkan kursor ke area bar tanpa masuk zonanya: garis melebar. Kirim `/agen ...`: warnanya bergeser ke cyan-biru dan alirannya lebih cepat. Matikan server: garis jadi merah dan berdenyut cepat. Masuk `/fokus`: kapsul biru lama tidak berubah dan tanpa pantulan. **[belum diuji]**
22. **Gerak halus (v18).** Diam beberapa menit dan perhatikan gerakan idle: tidak ada sentakan, lengan tidak menyapu pose T. Klik karakter beberapa kali berurutan: gerakan berpindah mulus (memudar), bukan melompat. Lihat konsol untuk memastikan tidak ada error animasi. **[belum diuji]**
23. **Gerbang emosi (v18).** Kirim beberapa pesan beremosi berbeda: kalimat happy atau surprised lebih sering bergerak, kalimat netral jarang, dan tidak bergerak terus-menerus. Pesan galat (server mati) tidak memicu gerakan. **[belum diuji]**
24. **Klip VRMA (v18).** Taruh minimal satu file di `assets/animations/` (dan `clips.json` kalau namanya beda). Konsol menampilkan "Klip VRMA aksi siap" (atau peringatan "tidak dimuat" kalau file tidak ada). Jalankan `clips()` lalu `playClip('nama')`: klip masuk dan keluar halus, dan karakter tidak bergeser dari tempatnya. Kirim beberapa pesan happy: klip kadang muncul, jeda antar klip tidak kurang dari 8 detik. **[belum diuji]**

---

# Bagian D: Catatan Gabungan

## Selisih dan hal yang perlu disamakan

- **Persona:** sumber utama adalah skill Hermes `iris-persona` dan `iris-modes`. Overlay memakai salinan di system prompt `server.py` (v3). Aturan khusus chat Telegram (label `[jokes]`, label mode, struktur ilmiah) **sengaja tidak dipakai** di overlay karena akan terbaca di bubble.
- **Suara:** keduanya memakai VOICEVOX `:50021`, speaker 2 (四国めたん). Cukup satu mesin, tapi hindari dua sumber suara bicara sekaligus (`jarvis-say.sh` dan pemutar overlay).
- **Lokasi:** overlay dan `server.py` di Windows (`Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron`). Hermes di WSL (`/home/<user>/.hermes`).
- **Versi:** Hermes v0.22.2 menurut dokumen sistem. Cek endpoint API server di versi ini sebelum mengandalkan dokumentasi umum.
- **Disk:** dokumen sistem mencatat C: dan Z: sama-sama 93% penuh. Electron, `node_modules`, dan model berukuran besar, jadi bersihkan dulu sebelum instalasi besar berikutnya.
- **Chrome debug:** tidak jalan otomatis. Tugas browser lewat Hermes butuh `~/bin/chrome-debug` dijalankan manual.
- **Memori:** terpisah (lihat Bagian C, Tahap 7).

## Risiko tambahan karena hybrid

- **Keamanan:** API server Hermes dapat menjalankan terminal dan file. Biarkan terikat ke `127.0.0.1`, pakai `API_SERVER_KEY`, jangan buka ke jaringan, dan jangan menaruh kunci di chat, screenshot, atau dokumen.
- **Privasi bubble dan suara:** hasil tugas dan memori yang masuk ke jawaban Iris akan terucap dan tertulis di layar. Jangan suntikkan data sensitif ke jalur overlay.
- **Latensi:** tugas Hermes bisa puluhan detik. Status "bentar ya" dan gerakan `think` penting supaya tidak terasa macet. Uji pencarian di `/mnt/z` menunjukkan ini perlu segera dikerjakan.
- **Konteks model Hermes:** Hermes menolak jalan kalau konteks model di bawah 64k. Pastikan combo 9Router yang dipakai Hermes memenuhi itu.

## Urutan kerja gabungan

1. Tes visual dan fungsional hasil sesi overlay terakhir (click-through per piksel, kursor dan hotkey global, tray, posisi tersimpan, `.vrma`, klik per bagian tubuh).
2. Ubah `server.py` untuk analisis gambar (`images`, `NINEROUTER_VISION_MODEL`).
3. **(selesai 30 Okt 2026)** **Jembatan Hermes, Tahap 0 sampai 3** (Bagian C), dengan satu tugas uji: `/agen` lalu isi folder `~/hermes-test`.
4. Status bubble dan pembatalan (Tahap 4 dan 5). Prioritas naik: pencarian di `/mnt/z` lama dan tanpa tanda apa pun di layar.
5. Tugas nyata pertama: skill `cek-elearning`.
6. Pemicu otomatis, lalu memori opsi 2.
7. Fase 5 sisa (push-to-talk, STT), Fase 6 (screen awareness), dan auto-start.

# Bagian E: Ide Pengembangan (dicatat 31 Okt 2026)

Belum ada yang dikerjakan di bagian ini. Urutan di tiap daftar menunjukkan prioritas yang disarankan.

## E1. Peningkatan yang disarankan sesudah v10

1. **Uji hasil v10.** Bubble menampilkan teks Indonesia sampai selesai, garis hijau di tengah karakter, bar input menutup sendiri, dan `/agen cek di reddit lagi trending apa` sampai menghasilkan jawaban tanpa dipotong pesan lain. Kalau Hermes tidak punya tool web search, aktifkan di sisi Hermes (uji dengan query yang sama di terminal WSL).
2. **Selesaikan uji jembatan Hermes yang tertunda:** suara dobel, Hermes mati, dan pembatalan di tengah tugas. Bug kecil di jalur agen paling merusak pengalaman, jadi ini dikerjakan lebih dulu.
3. **Routing otomatis untuk info terkini.** Pesan yang memuat kata seperti "trending", "berita terbaru", "cuaca sekarang", atau "harga" langsung dikirim ke Hermes tanpa `/agen`. Risiko: sesekali salah tebak. Pasang dengan saklar di `.env` yang bawaannya mati.
4. **Tugas nyata pertama: skill `cek-elearning`** (alasan awal jembatan Hermes dibangun).
5. **Kesan hidup di layar:** indikator saat Iris menunggu Hermes, mode bubble yang tidak menutupi layar saat bermain game, tombol salin di hasil tugas (path file dan sejenisnya).
6. **Memori:** suntik profil Hermes ke system prompt overlay (rencana memori opsi 2, Tahap 7 di Bagian C).
7. **Fitur besar:** push-to-talk dan STT (sisa Fase 5), screen awareness (Fase 6), auto-start bersama Windows. Tunggu sampai poin 1 sampai 4 stabil.
8. **Di luar kode:** drive C: dan Z: sama-sama 93% penuh. Electron, `node_modules`, dan model VRM berukuran besar, jadi bersihkan dulu sebelum instalasi berikutnya.

## E2. Ide fitur baru

1. **Bicara langsung (push-to-talk dan speech-to-text; selesai di v14, 31 Okt 2026, belum diuji di overlay).** Tahan satu hotkey, ucapkan sesuatu, Iris menjawab dengan suaranya. Mengubah rasa "teman" dari pengetik menjadi lawan bicara; efek terbesar. STT lokal bisa memakai `faster-whisper` model kecil. Syarat: bereskan disk dulu.
2. **Terjemahkan layar (selesai di v11, 31 Okt 2026; belum diuji di overlay).** Satu hotkey mengambil screenshot, model vision membaca teks Jepang di dalamnya, Iris menerjemahkan dan menjelaskan konteksnya. Paling cepat jadi: screenshot, jalur gambar, dan model vision sudah ada; yang ditambah hanya prompt khusus dan hotkey. Berguna untuk game atau visual novel tanpa terjemahan.
3. **Mode belajar bahasa Jepang (`/belajar`; selesai di v13, 31 Okt 2026).** Iris memberi satu kalimat, kamu menebak arti atau mengulang ucapannya, lalu dikoreksi. Bahannya sudah ada karena setiap balasan berisi kalimat Jepang dan terjemahan, dan VOICEVOX memberi pelafalan.
4. **Memori ringan (selesai di v12, 31 Okt 2026).** Perintah seperti "ingat bahwa ..." menyimpan fakta ke file JSON lokal yang disisipkan ke system prompt tiap giliran. Lebih sederhana daripada menyuntik seluruh profil Hermes, jadi bisa dikerjakan lebih dulu.
5. **Briefing pagi.** Sapaan pertama hari itu berisi cuaca dan tugas yang perlu dicek lewat `cek-elearning`. Menggabungkan jembatan Hermes dengan pemicu otomatis (Tahap 6).
6. **Reaksi proaktif yang opsional (pengingat istirahat selesai di v15, 31 Okt 2026; sapaan sesuai jam sudah ada sejak sebelumnya; sisanya belum).** Pengingat istirahat setelah sekian jam, atau sapaan sesuai jam. Semua harus bisa dimatikan, dan jangan membaca judul jendela aktif tanpa persetujuan pengguna (soal privasi).
7. **Suasana hati yang bertahan antarhari (selesai di v16, 31 Okt 2026; belum diuji di overlay).** "Mood" Iris naik turun tergantung seberapa sering pengguna mengobrol atau menyentuh karakternya, memengaruhi ekspresi, ambang ngambek, sapaan, dan nada bicara. Murni soal rasa.

**Pilihan awal yang disarankan:** nomor 1 di E2 (efek terbesar) atau nomor 2 di E2 (paling cepat jadi).

*Dokumen ini adalah gabungan; perubahan dicatat di Bagian A (overlay), B (Hermes), atau C (jembatan) sesuai asalnya.*

---

# Bagian F: Audit Berkas dan Langkah Berikutnya (31 Okt 2026)

Tempel di akhir `iris-companion-gabungan.md` (sesudah Bagian E), atau simpan terpisah. Bagian ini mencatat hasil pencocokan dokumen dengan kode, dan daftar kerja berikutnya supaya sesi lanjutan bisa langsung mulai.

## F1. Berkas yang diperiksa

| Berkas | Ukuran | Hasil |
|---|---|---|
| `server.py` | 61 KB | Lolos cek sintaks Python |
| `index.html` | 139 KB | Semua perintah dan fungsi yang dijanjikan dokumen ada |
| `main.js` | 16,7 KB | Lolos `node --check` |
| `preload.js` | kecil | Cocok dengan `index.html` dan `main.js` |
| `requirements.txt` | 3 baris | Kurang `faster-whisper` (lihat F3) |
| `assets.rar` | 10 MB (17,7 MB terbuka) | `iris.vrm`, `animations/idle_loop.vrma`, `tray.png` ada; klip aksi tidak ada |

Yang **tidak** diperiksa: `package.json`, `node_modules`, `.env`, `test_client.html`, dan isi tiap file aset (hanya daftar isi arsip yang dilihat). Tidak ada yang dijalankan; semua ini pemeriksaan membaca kode.

## F2. Yang sudah cocok

- [x] `server.py`: `/ingat`, `/memori`, `/lupa`, `/belajar`, pesan `stt`, `speak` (dengan `SPEAK_CACHE` dan `prefetch`), `voice_cache`, `stt_result`, `status`, `agent_result`, catatan mood (`clean_mood`, `mood_note`), `HERMES_TIMEOUT` bawaan 900 detik, awalan `/agen`, `/agent`, `/h`, penolakan pesan biasa saat tugas agen jalan, `ws_max_size` 32 MB, `/health` memeriksa VOICEVOX, 9Router, dan Hermes
- [x] `index.html`: semua perintah lokal (`/timer`, `/pomodoro`, `/batal`, `/clip`, `/layar`, `/terjemah`, `/fokus`, `/bisu`, `/tidur`, `/ekspor`, `/istirahat`, `/mood`, `/belajar`, `/ingat`, `/memori`, `/lupa`), `setArmGest` (bawaan 0), `GATE`, `playClip`, `clips()`, `fx()`, `sleepNow`, `showColliders`
- [x] Jembatan Electron: 13 method `window.companion` (`setIgnoreMouse`, `quit`, `setChatOpen`, `onCursor`, `onOpenChat`, `captureScreen`, `onScreenshot`, `readClipboard`, `copyImage`, `onAction`, `onActivity`, `saveHtml`, `revealFile`) semuanya ada di `preload.js` dan punya saluran IPC di `main.js`
- [x] Aksi global `talk`, `translate`, `clipboard`, `mute`, `menu` dikirim `main.js` dan ditangani `index.html`
- [x] Pintasan global terdaftar: `Q`, `H`, `C`, `S`, `G`, `T`, `V`, `B` (cadangan `M`, `Shift+Alt+M`, atau `IRIS_MUTE_KEY`), `D`
- [x] Izin mikrofon hanya untuk `app://local/`; `reveal-file` hanya membuka file di folder Downloads
- [x] Pengingat istirahat memakai `powerMonitor.getSystemIdleTime()` dengan reset 300 detik
- [x] Tidak ada API key tertanam di `server.py` atau `index.html`

## F3. Temuan dan perbaikan yang perlu dikerjakan

### Kode

- [x] **`requirements.txt` tanpa `faster-whisper`.** Tanpanya mic hanya menampilkan error "belum terpasang". Tambahkan baris `faster-whisper` (boleh diberi komentar bahwa ini opsional). `websockets` sudah dibawa `uvicorn[standard]`. **[selesai 31 Okt 2026: `faster-whisper>=1.0` ditambahkan dengan komentar opsional; belum dites]**
- [x] **Menu tray tidak punya item Mode fokus.** Dokumen v16d bilang keluar dari fokus bisa lewat menu tray, padahal tidak ada. Dua pilihan: (a) tambah item `Mode fokus` di tray `main.js` yang memanggil `sendAction('focus')`, lalu tambah cabang `focus` di `onAction` `index.html` yang memanggil fungsi yang sama dengan `/fokus`; atau (b) koreksi dokumen saja. Cara keluar yang pasti jalan sekarang: `Ctrl+Alt+C` lalu ketik `/fokus`, atau dekatkan kursor ke garis hijau dan ketik `/fokus`. **[selesai 31 Okt 2026: pilihan (a), item tray "Mode fokus (nyala / mati)" di `main.js` dan cabang `focus` di `onAction` `index.html`; belum dites]**
- [ ] **Pembatalan tugas Hermes (Tahap 5).** Tombol Stop hanya menutup permintaan HTTP; belum ada pemanggilan endpoint interupsi Hermes, jadi tugas bisa terus jalan di sisi Hermes. Cek dulu endpoint interupsi apa yang tersedia di Hermes v0.22.2.
- [ ] **Klip VRMA aksi belum ada.** Isi `assets/animations/` hanya `idle_loop.vrma`. Sampai v25 `index.html` mencari `VRMA_02.vrma` (`greet`) dan `VRMA_03.vrma` (`peace`), nama tebakan; sejak v26 daftar bawaan kosong dan tidak ada file yang dicari. Siapkan klip dari paket CC0 open-annie atau konversi Mixamo, lalu buat `clips.json`. Konsol akan menampilkan "Klip VRMA aksi siap" kalau berhasil.
- [ ] **Belum diperiksa:** apakah teks `HELP` di `index.html` menyebut `/ingat`, `/memori`, `/lupa`, dan `/mood`. Hanya 14 baris pertama yang dilihat (sampai `/belajar`).

### Dokumen

- [ ] Uji nomor 12 menyebut `iris-memory.json`; kodenya `iris-memory.json`. Samakan ke `iris-memory.json`.
- [ ] Daftar pintasan di "Cara menjalankan" belum memuat `Ctrl+Alt+T` (terjemah layar) dan `Ctrl+Alt+G` (bicara).
- [ ] Blok kode Tahap 2 (Bagian C) masih bernilai `HERMES_TIMEOUT` 120; beri catatan "draf, bawaan sekarang 900".
- [ ] Koreksi klaim "menu tray" di v16d, sesuai pilihan di atas.
- [ ] `requirements.txt`: catat bahwa `faster-whisper` ditambahkan.

## F4. Urutan kerja berikutnya

**Langkah 1: pasang dan jalankan (belum ada yang dites)**
1. Letakkan `assets/` hasil ekstrak sejajar dengan `main.js` dan `index.html`.
2. Tambah `faster-whisper` ke `requirements.txt` dan jalankan `pip install -r requirements.txt` kalau ingin mic.
3. Jalankan `python server.py`, buka `/health`: VOICEVOX, 9Router, dan Hermes tidak boleh `ERROR`; bagian `ninerouter` harus menampilkan "model gambar".
4. `npm start`. Terminal harus menampilkan "Pintasan terdaftar: ..." tanpa "Pintasan global gagal didaftarkan", dan tidak ada peringatan tray.

**Langkah 2: jembatan Hermes (prioritas tertinggi, bug di sini paling merusak)**
- [ ] `/agent buat file tst.txt isinya "halo" di folder Download`: path di kartu hasil berawalan `C:\Users\<user>\Downloads\` dan file muncul di Explorer
- [ ] Pindahkan `/home/<user>/Downloads/tst` ke folder Download Windows
- [ ] Suara Metan keluar saat hasil disampaikan, tanpa suara dobel dari Hermes
- [x] Uji gagal (Hermes dimatikan) dan pembatalan: pesan error ramah dan `interrupted: true` terbukti (31 Okt), tapi agen Hermes tetap jalan setelah cancel; lihat Bagian G, Poin C. Tombol Stop di overlay sungguhan **[belum dites]**
- [ ] Uji v10: `/agen cek di reddit lagi trending apa` sampai selesai, lalu kirim pesan biasa saat tugas jalan (harus muncul error "Tugas agen masih berjalan...")
- [ ] Tugas nyata pertama: skill `cek-elearning`

**Langkah 3: uji paket fitur v6 sampai v9**
- [ ] Suara sentuh (kepala, badan, lengan, tangan), colek 8 kali, bubble panjang bisa digulir
- [ ] Bar input auto-sembunyi dan garis petunjuk, klik tembus ke aplikasi di bawahnya
- [ ] Menu klik kanan, timer, Pomodoro, `Ctrl+Alt+V`, tidur, screenshot (termasuk game fullscreen)
- [ ] Ekspor chat ke HTML dan pesan galat bersuara

**Langkah 4: uji v10 sampai v16** (nomor 6 sampai 20 di "Uji v10 sampai v16"): terjemah layar, memori, `/belajar`, mic, istirahat, mood, gambar di chat, fakta tidak ditanya ulang, Mode fokus.

**Langkah 5: uji v17 dan v18** (nomor 21 sampai 24): garis petunjuk, gerak halus, gerbang emosi, klip VRMA (butuh file klip dulu).

**Langkah 6: pekerjaan baru, sesudah langkah 2 stabil**
- [ ] Pembatalan Hermes yang sungguhan (Tahap 5)
- [ ] Routing otomatis info terkini dengan saklar `.env` (bawaan mati), lalu pemicu kata kerja aksi (Tahap 6)
- [ ] Memori opsi 2 (suntik profil Hermes ke system prompt)
- [ ] Briefing pagi (cuaca dan `cek-elearning`)
- [ ] Fase 6 (screen awareness), auto-start Windows, tahan-tombol untuk push-to-talk
- [ ] Tier A GitHub: lip-sync dari mora VOICEVOX, angin dari kecepatan kursor, perintah `speak` dan `play_clip` untuk agen luar

## F5. Risiko yang masih terbuka

- **Semua fitur v6 sampai v18 masih belum dites di komputer.** Kode lolos cek sintaks dan sebagian logika diuji terpisah, tapi belum ada yang terlihat jalan di overlay. Kalau ada yang gagal, berhenti dan catat dulu, karena sebagian fitur bergantung pada yang sebelumnya.
- **Disk C: dan Z: sama-sama 93% penuh.** `iris.vrm` saja 17,5 MB; model Whisper `base` sekitar 150 MB; `node_modules` besar. Bersihkan sebelum memasang `faster-whisper`.
- **Klip VRMA:** pack VRoid resmi tidak boleh didistribusikan ulang dan isinya pose; paket Mixamo punya syarat kredit sendiri. Cek lisensi sebelum publikasi.
- **Gerakan lengan** tetap mati bawaan (`ARM_GEST = 0`) sampai gerakan v3 dan v18 dinilai natural secara visual.
- **Aturan umum:** jangan membagikan API key di chat, screenshot, atau dokumen; jangan ubah `COMPANION_HOST` ke `0.0.0.0` tanpa autentikasi; restart server dan overlay setiap berkas diganti.

## F6. Perbaikan T-pose berkala (31 Okt 2026)

**Gejala:** karakter VRM tiba-tiba berpose T (kedua lengan terentang lurus) setiap beberapa detik, sambil idle. Terlihat di screenshot overlay 12.45.

**Penyebab (terbukti, bukan dugaan):**
- Di `frame()` (`index.html`), saat animasi VRMA aktif, tulang yang dikendalikan (`BONES`) di-reset ke `quaternion.identity()` (pose T) tiap frame, lalu `mixer.update(dt)` diharapkan menimpanya dengan pose klip.
- `AnimationMixer` three.js hanya menulis ke tulang kalau nilai klip berubah dari frame sebelumnya. Selama nilainya sama, tulang dibiarkan apa adanya.
- `assets/animations/idle_loop.vrma` (250 keyframe, 10,375 detik, interpolasi LINEAR) punya bagian di mana pose ditahan: 13 pasang keyframe identik per tulang, terpanjang 11 keyframe (sekitar 0,46 detik), sama untuk semua tulang. Selama bagian itu mixer tidak menulis, jadi lengan tertinggal di pose hasil reset, yaitu T-pose. Karena klip berulang tiap sekitar 10,4 detik, T-pose muncul berkala.
- Simulasi dengan `three.js` asli (klip dengan 12 keyframe identik, 30 fps, 4 detik): logika lama 26 dari 120 frame salah dengan selisih terburuk 76,2 derajat; logika baru 0 dari 120 frame, selisih 0,0 derajat.

**Perbaikan (hanya `index.html`, empat titik):**
- [x] Reset `identity` di awal `frame()` diganti dengan membatalkan offset prosedural frame lalu (`b.quaternion.multiply(offInv[n]).normalize()`), jadi pose klip tetap ada di tulang walau mixer tidak menulis
- [x] `offInv` (objek baru, dekat `vel`) menyimpan kebalikan offset prosedural yang ditambahkan ke tiap tulang; diisi saat offset diterapkan di akhir `frame()`
- [x] `loadIdleVRMA()` mereset tulang ke identity sekali dan mengosongkan `offInv` sebelum animasi aktif, supaya mulai bersih
- [x] Lolos cek sintaks (`node --check` pada blok modul) **[belum dites di overlay]**

**Yang tidak berubah:** gerakan prosedural di atas pose klip (kepala menoleh, bicara, napas, gerak mood), `ARM_MIN`, pegas `MOTION`, gerbang `GATE`, dan klip aksi. `server.py`, `main.js`, dan `preload.js` tidak disentuh.

**Uji:**
- [ ] Ganti `index.html`, restart overlay, biarkan idle sekitar 30 detik (tiga kali loop klip): lengan tidak boleh melebar sama sekali
- [ ] Ulangi saat Iris bicara, saat gerakan acak jalan, dan saat klik karakter berkali-kali
- [ ] Kalau masih ada T-pose: buka konsol (`Ctrl+Alt+D`), catat isinya dan kapan terjadi (kemungkinan penyebab kedua, misalnya klip aksi atau peralihan bobot)
- [ ] Nilai apakah gerakan kepala dan badan masih terasa aneh; kalau ya, catat bagian mana (kepala, bahu, atau saat bicara) lalu setel `MOTION` dan `GATE` dari konsol

**Catatan teknis untuk pekerjaan berikutnya:** jangan lagi mereset tulang yang digerakkan mixer ke identity di luar mixer. Kalau lapisan prosedural perlu ditambahkan di atas klip, batalkan hanya offset yang tadi ditambahkan, seperti di atas. Prinsip yang sama berlaku untuk klip aksi VRMA nanti.

## F7. Tier list Desktop Mate dan paket pertama (v19, 31 Okt 2026)

Desktop Mate adalah aplikasi komersial di Steam (bukan open source), jadi **tidak ada file atau kode yang diambil**; hanya ide fiturnya. Proyek tiruan gratisnya, Mate Engine (Unity/C#, lisensi campuran AGPL v3 dan MateProv2), juga hanya jadi pembanding ide; avatar bawaannya hak cipta penuh pihak lain.

| Tier | Fitur | Status |
|---|---|---|
| S | Seret karakter langsung (tahan lalu geser) | **dikerjakan v19** [dites] |
| S | Reaksi bersuara saat diseret dan dilepas | **dikerjakan v19** [dites] |
| S | Saklar "selalu di atas" | **dikerjakan v19** [dites] |
| A | Sembunyi di tepi layar (mengintip) | **dikerjakan v21 sampai v21e** [dites 1 Nov, lulus] |
| A | Lepas di dekat tepi layar = sembunyi di tepi itu | **dikerjakan v21e** [dites 1 Nov, lulus] |
| A | Bayangan karakter di latar (selalu ada, HD) | **dikerjakan v22** [dites 1 Nov, lulus] |
| A | Pose diangkat: badan berayun, lengan terkulai | **dikerjakan v22** [dites 1 Nov, lulus] |
| A | Alarm jam tertentu (`/alarm 07:30 nama`) | **dikerjakan v20** [dites] |
| A | Ucapkan jam (`/jam`, opsional tiap jam) | **dikerjakan v20** [dites] |
| A | Duduk di tepi jendela atau taskbar | **dikerjakan v22** (tepi atas jendela lain; saklar privasi bawaan mati; hanya posisi dan ukuran jendela yang dibaca) [dites 1 Nov, lulus] |
| A | Dua cara mengangkat Iris (karakter dan tombol ✥) dengan saklar, `/angkat` | **dikerjakan v23** [dites 1 Nov, lulus] |
| A | Panel Pengaturan dan Timer bisa di-scroll | **dikerjakan v23** [dites 1 Nov, lulus] |
| A | `/duduk nyala` langsung duduk di jendela terdekat, `/duduk sini` | **dikerjakan v23** [dites 1 Nov, lulus] |
| B | Atur FPS dari Pengaturan | belum (konstanta `FPS_IDLE`/`FPS_ACTIVE` sudah ada) |
| B | Tangan mengejar kursor | belum (lengan masih dimatikan) |
| B | Menari mengikuti musik | belum; diputuskan diambil 4 Nov 2026, rancangan di Bagian P |
| C | Jalan-jalan di desktop, lompat antar jendela | dilewati |
| C | Mode chibi, layar besar, sistem makan | dilewati |

Sudah ada di Iris sebelumnya: mata dan kepala ikut kursor, elus kepala, reaksi per bagian tubuh, partikel emoji, bunyi lonceng timer, sapaan waktu, timer dan Pomodoro, transisi mulus (v18), tidur otomatis, batas FPS.

**Paket v19 (berkas berubah: `main.js`, `preload.js`, `index.html`; lolos cek sintaks; seret, reaksi bersuara, dan saklar "selalu di atas" sudah dites dan jalan):**
- [x] `main.js`: IPC `drag-window` menggerakkan jendela mengikuti kursor global tiap 8 ms lewat `setBounds` dengan ukuran tetap (menghindari ukuran melenceng di skala 125%/150%). Minimal 120 px jendela tetap di dalam layar terdekat. Berhenti sendiri setelah 2 menit kalau `mouseup` hilang. IPC `set-top` mengganti `setAlwaysOnTop`
- [x] `preload.js`: `dragWindow(on)` dan `setAlwaysOnTop(on)`
- [x] `index.html`: tekan lalu geser lebih dari 7 px di atas karakter = seret; diam di kepala tetap elus (geseran membatalkan elus); klik yang menyusul lepas seretan tidak dihitung colekan; selama diseret jendela tidak tembus klik; kepala miring dan bahu terangkat selama diseret (tanpa lengan, aman dari T-pose); 4 kalimat saat diangkat (tidak lebih sering dari 5 detik) dan 3 saat dilepas (hanya kalau diseret lebih dari 0,7 detik), ikut di-prefetch suara; tombol ✥ di bar tetap bisa dipakai
- [x] Saklar "Selalu di atas" di Pengaturan dan perintah `/atas [mati|nyala]` (disimpan di `SET.top`, bawaan nyala); `/help` diperbarui

**Uji v19:**
- [x] Ganti `main.js`, `preload.js`, `index.html`, restart overlay (ketiganya wajib; tanpa `preload.js` baru seret langsung tidak aktif dan ✥ tetap jalan) **[lulus]**
- [x] Tekan dan geser badan karakter: jendela mengikuti kursor tanpa tertinggal atau berkedip, Iris bersuara, lepas: bersuara lagi dan tidak terhitung colekan **[lulus]**
- [ ] Tahan diam di kepala 0,65 detik: tetap elus; tahan lalu geser: seret
- [ ] Seret ke tepi layar dan ke monitor lain: tidak hilang total dan ukuran jendela tidak berubah
- [ ] Seret saat chat terbuka dan saat bubble tampil: tetap normal
- [x] `/atas mati`, buka jendela browser: bisa menutupi Iris; `/atas nyala`: kembali di atas **[lulus]**
- [ ] Kalau ukuran jendela melenceng di layar skala tinggi, kirim ukuran sebelum dan sesudah seret

### Uji v20 (31 Okt 2026)

Hanya `index.html` yang perlu diganti; restart overlay sesudahnya. Hasil keseluruhan dari pemilik: **Paket 2 sudah bisa (jalan)**. Hasil per butir tidak dicatat satu-satu, jadi daftar di bawah hanya acuan uji, bukan catatan lulus per butir.

- `/alarm HH:MM tes` dengan jam 1 sampai 2 menit dari sekarang: chime bunyi, bubble "Waktunya!", ada catatan di log
- `/alarm` menampilkan daftar terurut; `/alarm batal 1` dan `/alarm batal semua` menghapus
- Format salah (`/alarm 25:00`, `/alarm halo`, `/alarm batal 99`) menampilkan pesan galat
- Alarm yang lewat saat overlay tertutup: Iris minta maaf sekali dan alarm hilang dari daftar
- `/jam` mengucapkan jam; `/jam nyala` mengucapkan jam pada pukul pas; `/jam mati`
- `/help` memuat `/alarm` dan `/jam`
- [ ] Catat bila ada pembacaan "時" atau "分" yang terdengar janggal di VOICEVOX
- [ ] Belum diuji: alarm saat mode fokus (chime dan log tetap jalan, bubble dan suara mengikuti aturan mode fokus)

### Pembaruan v21 sampai v22 (31 Okt 2026): mengintip, bayangan, pose, duduk

**Referensi perilaku.** Pemilik mengirim screenshot Desktop Mate (gambar jalan, tanpa file atau kode): karakter mengintip dari tepi layar dengan badan miring jauh dan bayangan siluet besar di latar; bersembunyi total dengan hanya jari yang terlihat memegang tepi; diangkat dalam keadaan menggantung dengan bayangan di bawahnya; duduk di tepi atas jendela dengan bayangan lembut di belakang. Aturan proyek tetap: hanya ide dan perilaku yang diambil, tidak ada file, model, animasi, atau kode Desktop Mate yang diekstrak atau disalin (aplikasi komersial, bukan AGPL; AGPL milik Mate Engine, proyek terpisah). Folder instalasi Steam-nya tidak dibongkar. Animasi bergerak masuk lewat paket klip CC0 (open-annie) atau Mixamo.

**Prinsip teknis yang dipakai.**
- Kanvas karakter berhenti di rok. Agar potongan itu tidak melayang, potongan harus bertepatan dengan sebuah tepi: dasar layar saat mengintip (v21c) dan tepi atas jendela saat duduk (v22). Ruang kosong di bawah karakter dibuang lewat `--peek-drop`, dihitung dari layout (`offsetTop`), bukan dari `getBoundingClientRect`, supaya tidak terpengaruh transform.
- Kemiringan dan ayunan dilakukan di grup `peekPivot` (three.js), bukan CSS pada `#char`, supaya hit-test piksel (`sampleHit`) dan perhitungan tatapan tetap memakai kotak kanvas yang tidak berubah.
- Diangkat = bandul: rotasi dengan titik gantung di kepala (`position = p - R p`), bukan rotasi di kaki.
- Bayangan memakai `filter: drop-shadow` pada kanvas dengan variabel CSS (`--sh-x`, `--sh-y`, `--sh-b`, `--sh-a`) yang diganti per kelas (`held`, `peek`, `sit`); `#root.noshadow` mematikannya. Bayangan tidak ikut hit-test.
- Duduk: `main.js` menjalankan satu proses PowerShell yang tetap hidup (skrip C# lewat `Add-Type`, dikompilasi sekali), dipanggil dengan menulis PID ke stdin dan membalas daftar `hwnd kiri atas kanan bawah` diakhiri `END`. Proses memanggil `SetProcessDPIAware()` supaya koordinatnya fisik, lalu `screen.screenToDipRect` mengubahnya ke DIP Electron (penting di skala 125% atau 150%). Jendela dari proses Iris sendiri, jendela alat (`WS_EX_TOOLWINDOW`), tanpa aktivasi, tertutup (cloaked), diminimalkan, atau lebih kecil dari 200 x 120 dilewati. Urutan z dipakai untuk membuang tepi atas yang tertutup jendela lain. Jendela dianggap bisa diduduki kalau kepala karakter tetap masuk layar (tepi atasnya minimal 420 px di bawah atas layar).
- Siklus duduk: dilepas dengan dasar karakter dalam 70 px dari tepi atas jendela dan tengah karakter di atas lebarnya = duduk (dasar jendela Iris = tepi atas jendela itu, animasi 240 ms); dicek tiap 300 ms dan Iris ikut bergerak; jendela ditutup, diminimalkan, atau digeser terlalu ke atas = Iris turun ke dasar layar. Diseret, chat dibuka, atau mengintip = turun dulu. `savePos` menyimpan posisi lantai, bukan posisi di atas jendela. Proses PowerShell dimatikan saat saklar mati atau aplikasi keluar.

**Catatan jujur.**
- Arah miring dan jumlah yang terlihat saat mengintip, ayunan lengan, serta pose duduk belum pernah dilihat langsung (tidak ada Windows dan Electron di lingkungan penulisan). Semua angka bisa disetel: `setPeekLean`, `setPeekShift`, `setPeekShadow`, `setSitLean` di konsol, `IRIS_PEEK_CUT` dan `IRIS_SIT_BAR` di env.
- Skrip PowerShell belum dijalankan sama sekali. Kalau `Add-Type` gagal (mis. kebijakan keamanan), duduk tidak aktif dan pesan galatnya muncul di konsol `main.js` dengan awalan "Duduk (PowerShell)"; bagian lain tidak terpengaruh.
- Kaki tidak terlihat di pose mana pun karena model dipotong di rok. Menampilkan kaki berarti mengubah kamera, dan itu berpengaruh ke tampilan normal.
- Pose lengan memakai `armL` dan `armR` langsung (tidak dikunci `ARM_GEST`) dengan nilai kecil dan tetap lewat pagar `ARM_MIN`. Kalau muncul gejala T-pose atau lengan terangkat, matikan dengan menurunkan angka di blok "v22: digantung" atau "v22: duduk" di `frame()`.
- Pose "tangan memegang tepi" dan klip aksi tetap menunggu file VRMA.

### Uji v21 sampai v22 (31 Okt 2026)

Ganti `main.js`, `preload.js`, dan `index.html` (ketiganya wajib; tanpa `preload.js` baru: tidak ada ayunan saat diseret dan saklar duduk tidak jalan), lalu restart overlay.

- [ ] `/sembunyi`: bubble dan bar tidak tertinggal, karakter turun ke dasar layar dan condong ke dalam, kepala tidak terpotong, ada bayangan di latar; dekati atau klik: muncul lagi; dibiarkan 7 detik: sembunyi lagi
- [ ] Tepi kiri dan tepi kanan sama-sama benar (arah miring dan arah bayangan tercermin)
- [ ] Seret lalu lepas dengan tengah karakter dekat tepi kiri atau kanan: langsung bersembunyi; seret keluar: mode mati
- [ ] Bayangan terlihat saat diam (halus, tidak mengganggu) dan hilang total dengan `/bayangan mati`; buffer render lebih tajam, FPS tetap wajar di game
- [ ] Diangkat: badan berayun berlawanan arah gerak, lengan terkulai dan mengayun, bayangan jatuh ke bawah-samping; dilepas: kembali normal tanpa lonjakan
- [ ] `/duduk cek` (butuh `preload.js` terbaru): letakkan Iris dengan dasar badannya dekat tepi atas sebuah jendela lalu ketik perintah ini. Laporan di chat memuat status saklar, waktu balas PowerShell, jumlah jendela terbaca, posisi karakter, dan alasan tiap jendela terdekat diterima atau ditolak (hanya angka posisi, tanpa judul jendela)
- [ ] `/duduk nyala`, buka browser, lepas Iris dengan dasar karakter dekat tepi atas jendela: dia duduk, bersuara "ここに座るね。", ikut bergerak saat jendela digeser pelan
- [ ] Tutup atau minimalkan jendela itu saat Iris duduk: dia turun ke dasar layar; maksimalkan: turun
- [ ] Duduk lalu buka chat atau seret: turun dulu, tidak lompat ke posisi aneh; posisi tersimpan = lantai
- [ ] Layar skala 125% atau 150%: Iris duduk tepat di tepi atas jendela, tidak melayang atau tenggelam
- [ ] `/duduk mati`: proses `powershell.exe` hilang dari Task Manager; saklar mati = tidak ada proses
- [ ] Layar kedua di kiri atau kanan: sembunyi di tepi yang terhalang ditolak tanpa pesan galat saat dilepas, dan dengan pesan saat memakai `/sembunyi`

### Pembaruan v23 (31 Okt 2026): dua cara mengangkat, panel scroll, duduk langsung

File yang berubah: `main.js`, `preload.js`, `index.html`. Lolos cek sintaks (`node --check`); belum dijalankan di overlay.

**Dua cara mengangkat Iris.** Alasan: seret dari badan membuat Iris terangkat tanpa sengaja saat mengelus atau mencolek, dan tidak ada cara mematikannya. Kini ada dua saklar di Pengaturan (`SET.dragChar`, `SET.dragGrip`, keduanya bawaan `true`, disimpan di `localStorage` `iris.set`):
- `dragChar`: handler `mousedown` di `charBox` (yang memulai seret setelah geser > `DRAG_PX` = 7 px) langsung keluar kalau saklar mati. Mematikannya juga membatalkan seretan yang sedang berjalan.
- `dragGrip`: kelas `nogrip` di `#root` mengubah `#grip` jadi `-webkit-app-region: no-drag`, kursor biasa, dan redup. Saat nyala, grip tetap memakai seret asli Electron (`-webkit-app-region: drag`), bukan seret kustom `main.js`.
- Pagar: kalau kedua saklar akan mati, saklar yang baru dimatikan tidak jadi (yang lain dinyalakan lagi) lewat `applyDragWays(changed)`.
- `/angkat [mati|nyala]` membalik saklar karakter (tanpa argumen = membalik) dan Iris menjawab bersuara. Baris bantuan ditambahkan ke `/help`.

**Panel yang kepotong.** Setelah dua baris baru, panel Pengaturan lebih tinggi daripada jendela overlay dan baris bawahnya terpotong tanpa scrollbar. Aturan `.pop` kini `max-height: calc(100vh - 140px); overflow-y: auto` dengan scrollbar tipis, dan anak elemen diberi `flex: none` supaya tidak menyusut. Berlaku untuk semua `.pop` (Pengaturan dan Timer). Timer tutup-otomatis 7 detik tetap berhenti selama kursor ada di dalam panel.

**Duduk tidak bereaksi.** Penyebab: `set-sit` hanya mengubah `sit.enabled`; `sitSnap()` baru dipanggil saat seretan dilepas (`drag-window` off) dan menolak jendela yang tepi atasnya lebih dari `SIT_SNAP` (70 px) dari dasar karakter. Iris di lantai layar jadi tidak pernah duduk. Perubahan:
- `sitSnap(force)` baru: dengan `force`, Iris memilih jendela terdekat (jarak horizontal + vertikal) yang layak, geser ke dalam lebar jendela itu, lalu `sitStart`. Syarat layak: lebar jendela >= 120 px, kepala tidak keluar layar (`SIT_CHAR_H`; jendela dimaksimalkan ditolak), tepi atas bukan di dasar layar (>= 60 px dari bawah area kerja), tepi atas tidak tertutup jendela lain, chat tidak sedang terbuka.
- `set-sit` menerima argumen kedua `now`; `preload.js`: `setSit(on, now)`. Hanya pengguna yang menyalakan saklar (Pengaturan atau `/duduk`) yang mengirim `now = true`; startup tidak, supaya Iris tidak melompat sendiri tiap overlay dibuka.
- Kalau tidak ada jendela yang layak, `main.js` mengirim `sit-state {on:false, none:true}` dan Iris bilang "Tidak ada jendela yang pas buat duduk".
- `/duduk sini` menyalakan saklar dan menyuruh naik lagi (berguna setelah membuka jendela baru). Cara lama (lepas dekat tepi atas jendela) tetap jalan. `/duduk cek` tidak berubah.

### Uji v23 (31 Okt 2026)

Ganti `main.js`, `preload.js`, dan `index.html` (ketiganya wajib; tanpa `preload.js` baru `/duduk nyala` tidak langsung duduk), lalu restart overlay.

- [ ] Pengaturan: buka panel, scroll sampai baris paling bawah ("Angkat dari karakter", "Angkat dari tombol ✥") terlihat; scrollbar tipis muncul dan panel tidak menutup sendiri selama kursor di dalamnya
- [ ] Matikan "Angkat dari karakter": tekan dan geser badan Iris tidak memindahkan jendela; elus kepala dan colek tetap bereaksi; tombol ✥ masih bisa menyeret
- [ ] Matikan "Angkat dari tombol ✥" (karakter nyala): tombol ✥ redup dan tidak menyeret; seret dari badan masih jalan
- [ ] Matikan keduanya berurutan: saklar kedua yang dimatikan langsung menyala lagi (Iris tidak terkunci)
- [ ] `/angkat mati` lalu `/angkat nyala`: saklar di Pengaturan ikut berubah dan Iris menjawab bersuara; pengaturan bertahan setelah restart overlay
- [ ] Buka satu browser (tidak dimaksimalkan, tepi atas minimal sekitar 420 px dari atas layar), lalu `/duduk nyala` dari lantai layar: Iris naik dan duduk di tepi atasnya, ikut bergerak saat jendela digeser pelan
- [ ] `/duduk nyala` tanpa jendela yang layak (semua dimaksimalkan atau minimal): Iris bilang tidak ada jendela yang pas, tidak ada galat di konsol
- [ ] Restart overlay dengan saklar duduk sudah nyala: Iris tidak langsung melompat ke jendela; `/duduk sini` baru memindahkannya
- [ ] `/duduk sini` saat sedang duduk: tidak ada perubahan; saat di lantai: naik lagi ke jendela terdekat
- [ ] Duduk lalu buka chat atau seret: turun dulu seperti v22 (tidak ada perubahan perilaku)

### Pembaruan v24 (1 Nov 2026): lampiran gambar, tombol salin, benturan sisi layar

File yang berubah: `main.js`, `preload.js`, `index.html`. Lolos cek sintaks (`node --check`). Catatan: `preload.js` dibangun ulang dari isi yang dikirim (berkas tidak ada di unggahan) dengan satu tambahan, jadi timpa berkas lama dengan yang baru.

**Lampiran screenshot.** Laporan: gambar lampiran "tidak bisa dilihat". Penyebab: `.thumb` hanya 52 px dan tidak punya handler klik (penampil `#imgView` hanya terpasang ke gambar di log chat). Perbaikan: `.thumb` 88 px, kursor `zoom-in`, klik memanggil `openImgView(a.url)`.

**Jendela "Buka besar".** Laporan: gambar di penampil buram dan tidak bisa di-zoom. Penyebab: penampil berada di dalam jendela overlay (`WIN_W` = 440), jadi gambar 1600 px dikecilkan ke sekitar 400 px. Perbaikan:
- `preload.js`: `openImage(url)` memanggil IPC `open-image`.
- `main.js`: `open-image` menulis gambar dan satu halaman HTML kecil ke `%TEMP%\iris-view`, lalu membuka `BrowserWindow` biasa (area kerja dikurangi 40 px tiap sisi; `contextIsolation` nyala, `nodeIntegration` mati, `sandbox` nyala). Halaman: roda mouse zoom ke arah kursor (batas 0,5x pas layar sampai 8x), seret untuk geser, klik dua kali pindah antara ukuran asli dan pas layar, Esc menutup. File sementara dihapus saat jendela ditutup.
- `index.html`: tombol `#ivBig` dan `dblclick` pada gambar penampil. Kalau `window.companion.openImage` tidak ada (preload lama), tombol menampilkan pesan untuk mengganti berkas dan restart.

**Tombol Salin gambar.** Pesan lama "ganti main.js dan preload.js" dipakai untuk semua jenis kegagalan, jadi menyesatkan. Log terminal menunjukkan `clipboard.writeImage is not a function`. Perbaikan di handler `copy-image`: `clipboard.write({ image })` (cadangan `writeImage` kalau `write` tidak ada), cadangan `createFromBuffer` kalau `createFromDataURL` kosong, dan setiap alasan gagal dicetak lewat `console.warn`. Pesan di tombol kini "Gagal menyalin (restart Iris; cek terminal)".

**Benturan sisi layar.** Laporan: karakter diseret keras ke tembok monitor tidak bersuara. Penyebab: `cornerAt()` hanya mengenali pojok (dua tepi sekaligus). Perbaikan di `main.js`:
- `edgeAt(c)`: kursor dalam `EDGE_PX` = 10 px dari satu tepi layar; sisi yang bersebelahan dengan monitor lain diabaikan.
- Hanya lewat kecepatan: `EDGE_SPEED` = 900 px/dtk (bisa diubah dengan variabel lingkungan `IRIS_EDGE_SPEED`), tanpa "dijepit" (dwell) supaya menyeret pelan ke tepi untuk bersembunyi tidak dihitung benturan. Pojok tetap memakai `CORNER_SPEED` = 650 dan dwell 700 ms.
- Event yang dikirim tetap `corner-hit`, dengan `corner` bernilai `'l'`, `'r'`, `'t'`, atau `'b'` untuk sisi. Renderer tidak memakai nilai itu, jadi suara, gerakan sakit, hitungan tiga benturan = ngambek, dan jeda 2,5 detik sama dengan pojok. Mode fokus (`quiet`) tetap membisukan ucapan benturan, hanya animasi yang jalan.

**Galat `app://`.** Handler protokol `app://` kini menangkap kegagalan `net.fetch` dan membalas 404. `favicon.ico` dan `clips.json` (opsional) tidak dilaporkan; file lain dicetak sebagai `app:// file tidak ditemukan: <jalur>`. Dari log pertama: `VRMA_02.vrma` dan `VRMA_03.vrma` memang belum ada di `assets/animations/`.

### Uji v24 (1 Nov 2026)

Ganti `main.js`, `preload.js`, dan `index.html` (ketiganya wajib), lalu restart overlay.

- [ ] Ambil screenshot (tombol kamera atau Ctrl+Alt+S): thumbnail lampiran tampil 88 px; klik membuka penampil
- [ ] Di penampil: "Buka besar" (atau klik dua kali gambar) membuka jendela besar; teks screenshot terbaca jelas; roda mouse zoom, seret geser, klik dua kali ganti ukuran asli dan pas layar, Esc menutup
- [ ] Setelah jendela besar ditutup, folder `%TEMP%\iris-view` tidak menyimpan file lama dari gambar itu
- [ ] "Salin gambar": tombol berubah "Tersalin ✓" dan gambar bisa ditempel (Ctrl+V) di Paint atau chat
- [ ] Seret Iris keras ke sisi kiri, kanan, atas, dan bawah layar: ada suara "Aduh!", gerakan sakit, dan efek 💥; di sisi yang bersebelahan dengan monitor lain tidak ada reaksi
- [ ] Seret pelan ke tepi lalu lepas: tidak ada reaksi sakit (hanya perilaku sembunyi di tepi seperti v21)
- [ ] Tiga benturan dalam semenit: Iris ngambek seperti pada pojok
- [ ] `npm start`: tidak ada lagi `net::ERR_FILE_NOT_FOUND`; hanya baris `app:// file tidak ditemukan` untuk file yang benar-benar hilang

### Pembaruan v25 dan v26 (1 Nov 2026): ganti baju, fun fact, tampilan badan, bubble, panel

File yang berubah: hanya `index.html` (`main.js`, `preload.js`, `server.py` tidak berubah). Lolos cek sintaks (`node --check` pada skrip modul). Ganti `index.html` lalu restart overlay.

**v25, ganti baju.** Satu file VRM per baju di `assets/`, didaftar di array `OUTFITS` (`id`, `name`, `url`, `jp`): `maid` = `iris.vrm` (bawaan), `prom` = `Iris_prom.vrm`, `school` = `Iris_school.vrm`. Menambah baju = tambah satu baris di `OUTFITS`. `loadOutfit(id, first)` memuat model baru, membuang yang lama (`disposeModel`), memasang ulang kamera, collider, dan animasi idle; kalau gagal, model lama dipertahankan dan muncul pesan galat. Pilihan disimpan di `localStorage` (`iris.outfit`); kalau file baju tersimpan hilang saat overlay dibuka, dipakai baju bawaan. Jalur pemakaian: menu klik kanan "Ganti baju" (chip), dropdown "Baju" di Pengaturan, `/baju [nomor|nama]` (tanpa argumen = daftar). Konsol: `outfits()` dan `setOutfit('school')`.

**v26, fun fact acak.** Blok baru setelah `watchArm(false)` di `index.html`.
- Jeda diacak merata antara `funMin` dan `funMax` (dijepit 5 sampai 60 menit); pencacah diperiksa tiap 15 detik. Default di `SET`: `funOn: true, funMin: 5, funMax: 60`.
- `FUNFACTS` = daftar `[teks Indonesia, kalimat Jepang]`, 30 butir. Kantong acak (Fisher-Yates) disimpan di `localStorage` (`iris.funbag`) supaya tidak ada pengulangan sampai kantong habis. Kalimat diucapkan dengan awalan "豆知識だよ。" dan bubble berawalan "💡 Fun fact:", emosi `happy`, efek 💡.
- Syarat tunda (dicoba lagi 30 detik): mode fokus, tidur, Iris bicara, merekam, chat terbuka, ada ketikan atau lampiran, sedang menerjemahkan, atau di tepi layar. Suara dibisukan = bubble teks saja.
- Perintah `/funfact` (alias `/ff`, `/tahukah`): tanpa argumen = nyala/mati; `sekarang`; `10-30` (rentang); `20` (sekitar 20 menit, diacak 60% sampai 160%); `mati`; `nyala`. Pengaturan: saklar "Fun fact acak" dan baris "Acak (menit)" dengan dua kolom angka.

**v26, tampilan badan.** Penyebab kaki tidak terlihat: `CAM.bottom = 0.4` memotong kamera di sekitar pinggang. `fitCamera(reuse)` kini membaca `SET.fullBody` (bawaan `true`): tubuh penuh memakai `headroom` 0,1 dan batas bawah sedikit di bawah kaki; setengah badan memakai nilai lama (`headroom` 0,2, `bottom` 0,4). Tinggi model disimpan di `fitInfo` supaya perpindahan mode tidak menghitung ulang Box3 (yang setelah collider terpasang bisa berbeda). Dropdown "Tampilan" di Pengaturan dan `/badan [penuh|setengah]` (alias `/body`) langsung memasang ulang kamera. Efek samping: di mode penuh karakter tampak lebih kecil di kotak yang sama; ukuran jendela (`WIN_W`, `WIN_H` di `main.js`) dan `#char` di CSS bisa diperbesar bila perlu.

**v26, bubble di atas kepala.** Dulu dasar bubble selalu 90 px ke dalam kotak `#char` (cocok untuk setengah badan, menimpa kepala di tubuh penuh). Kini `updateBubbleOver()` memproyeksikan puncak model (`fitInfo.maxY`) ke layar dan mengisi `bubbleOver` serta variabel CSS `--bubble-over` (selisih 12 px, dijepit -60 sampai 120). Dipanggil dari `fitCamera` dan `resizeChar` (chat dibuka atau ditutup). `fitBubble` dan `placeBubble` memakai `bubbleOver`, bukan angka 90. Penyesuaian halus: angka `yPx - 12`.

**v26, panel Pengaturan dan posisi panel.** Laporan: panel "kebesaran" dan menimpa karakter. Perbaikan: tinggi maksimum `min(100vh - 140px, 330px)`, jarak dan huruf dikecilkan, baris "Acak dari" dan "sampai" digabung (`Acak (menit) [a] – [b]`) untuk Komentari layar dan Fun fact. Lalu semua panel (`#menu`, Timer, Ganti baju, Pengaturan) dipindah ke `left: 2px` dan dipersempit jadi 196 px, karena badan karakter ada di tengah-kanan jendela (440 px).

**v26, klip VRMA bawaan.** Log `app:// file tidak ditemukan: /assets/animations/VRMA_02.vrma` dan `VRMA_03.vrma`: dua file itu memang tidak dimiliki. `DEFAULT_CLIPS` kini `{}` (contoh isinya tinggal di komentar kode). Iris tetap memakai animasi idle dan gerakan prosedural; sapaan gerak dan pose peace menunggu file `.vrma` dan `clips.json`.

### Uji v26 (1 Nov 2026)

Ganti `index.html`, lalu restart overlay.

- [ ] `/funfact sekarang`: Iris menyebut satu fakta bersuara dengan bubble "💡 Fun fact: ..."; dipanggil berulang tidak mengulang fakta sampai 30 butir habis
- [ ] `/funfact 5-10`, lalu tunggu: fakta muncul dalam rentang itu; saklar dan kolom menit di Pengaturan ikut berubah; pengaturan bertahan setelah restart
- [ ] Fun fact tidak muncul saat mode fokus, tidur, chat terbuka, atau mengetik; muncul menyusul sekitar 30 detik setelah syarat terpenuhi
- [ ] `/funfact mati`: tidak ada lagi fakta otomatis
- [ ] Dropdown "Tampilan" atau `/badan penuh` dan `/badan setengah`: kamera berpindah langsung; bubble tetap di atas kepala di kedua mode, juga saat chat dibuka dan ditutup
- [ ] Ganti baju lewat menu, Pengaturan, dan `/baju` pada ketiga baju; kaki terlihat jelas di seragam sekolah
- [ ] Buka Pengaturan, Timer, Ganti baju, dan menu klik kanan: tidak ada panel yang menimpa badan karakter; baris paling bawah Pengaturan masih bisa dijangkau lewat scroll
- [ ] `npm start`: tidak ada lagi baris `app:// file tidak ditemukan` untuk `VRMA_02.vrma` dan `VRMA_03.vrma`

### Pembaruan v27 (1 Nov 2026): fun fact dibuat model

File yang berubah: `server.py` dan `index.html`. Ganti keduanya, restart server dan overlay.

**Server.** Pesan baru `{type:'funfact', topic, seen[]}`. `handle_funfact` memanggil 9Router (`stream_lines` dan `clean_lines`, model `NINEROUTER_MODEL`) dengan `FUNFACT_PROMPT`: satu fakta yang benar dan mudah diverifikasi, jangan mengarang angka atau nama, jangan mengulang `seen`, balas satu baris `FAKTA: <Indonesia> ||| <Jepang>`. Hasil divalidasi (panjang, harus ada huruf Jepang); balasan `{type:'funfact', ok, id, jp}`. Tidak menyentuh riwayat, tidak mengirim `error` atau `done`, jalan sebagai tugas terpisah (tidak menyela obrolan). Alasan memakai 9Router, bukan agen Hermes: agen untuk tugas panjang (batas 15 menit), sedangkan satu kalimat cukup lewat LLM biasa dan jauh lebih cepat dan murah.

**Overlay.** `funSay()` mengirim permintaan dan menunggu; `onFunFact()` mengucapkan hasilnya lewat `say()` (bubble 💡 dan suara VOICEVOX). Cadangan ke `funSayBuiltin()` kalau: WebSocket mati, `ok:false`, atau tidak ada balasan dalam 30 detik. Syarat tunda (mode fokus, tidur, chat terbuka, dan seterusnya) diperiksa lagi saat balasan tiba; kalau keadaan berubah, fakta dibuang dan dicoba lagi 30 detik kemudian. `/funfact sekarang` selalu bicara. 8 fakta terakhir dikirim ke server supaya tidak berulang.

**Risiko yang diketahui.** Fakta buatan model bisa keliru walau prompt melarang mengarang; terjemahan Jepang buatan model bisa terdengar janggal di suara. Pakai `/funfact bawaan` kalau ingin hanya fakta yang sudah ditulis tangan.

### Uji v27 (1 Nov 2026)

- [ ] `/funfact topik game` lalu `/funfact sekarang`: Iris menyebut fakta tentang game dengan suara Jepang; kolom Topik di Pengaturan ikut terisi
- [ ] Panggil `/funfact sekarang` beberapa kali: faktanya tidak sama
- [ ] Matikan server (atau 9Router) lalu `/funfact sekarang`: Iris tetap bicara memakai fakta bawaan, tidak ada pesan galat
- [ ] `/funfact bawaan`: hanya fakta bawaan; `/funfact model`: kembali ke buatan model
- [ ] Saat chat terbuka atau mode fokus nyala, fakta otomatis tidak menyela
- [ ] Terminal server: tidak ada galat; baris `[funfact] gagal: ...` hanya muncul saat model bermasalah

### Pembaruan v28 (1 Nov 2026): token /ws, kunci navigasi, gaya suara per emosi

File yang berubah: `server.py` dan `main.js`. Ganti keduanya, lalu restart server dan overlay. `iris-v28.patch` berisi selisih lengkap dari versi sebelumnya.

**Token `/ws` (`server.py`, `main.js`).** Cek `Origin` saja tidak cukup karena klien non-browser tanpa header itu selalu lolos, jadi proses lokal mana pun bisa mengirim `/agen`. Sekarang, kalau `COMPANION_TOKEN` diisi, `ws_endpoint` memeriksa header `X-Iris-Token` dengan `hmac.compare_digest` setelah cek Origin; salah atau tidak ada = ditutup dengan kode 1008 sebelum `accept()`. Token lewat header, bukan `?token=`, karena uvicorn mencetak URL lengkap di log akses. Penolakan dicatat di terminal (tanpa nilai token) paling sering sekali per 30 detik, karena overlay mencoba nyambung ulang tiap 2 detik. Token kurang dari 16 karakter memicu peringatan. `/health` menampilkan `"ws_token": "aktif"` atau `"KOSONG (/ws terbuka)"`. Di `main.js`, `loadCompanionToken()` membaca `COMPANION_TOKEN` dari environment, kalau kosong dari `~/.env`, kalau file itu tidak ada dari `.env` di folder overlay (urutan sama dengan `server.py`; baris terakhir menang, kutip dan komentar inline ditangani). Nilainya ditempel di hook `onBeforeSendHeaders` yang sudah dipakai untuk mengganti `Origin`, hanya untuk `ws://localhost:8765/*`. Terminal Electron mencetak "Token /ws: terbaca (N karakter)" atau "tidak ada", tidak pernah nilainya.

**Kunci navigasi (`main.js`).** `app.on('web-contents-created')` memasang `setWindowOpenHandler` (tolak), penolak `will-navigate` dan `will-redirect`, dan penolak `will-attach-webview` di setiap jendela, termasuk penampil gambar besar. Berguna juga karena file yang dijatuhkan ke jendela tidak bisa lagi membuat halaman pindah ke `file://`. URL `devtools://` dikecualikan supaya Ctrl+Alt+D tetap jalan. Pemuatan programatik (`win.loadURL`, `loadFile`) tidak terkena.

**Gaya suara per emosi (`server.py`).** `synthesize(client, text, emotion)` memakai `apply_voice_style()` pada hasil `audio_query` sebelum sintesis. Tabel `EMO_VOICE` (kecepatan dan intonasi = pengali, nada = penambah; dijepit ke batas VOICEVOX): `happy` 1.05 / +0.03 / 1.15, `sad` 0.92 / -0.04 / 0.85, `angry` 1.05 / -0.02 / 1.25, `surprised` 1.08 / +0.06 / 1.30, `shy` 0.95 / +0.02 / 0.90; `neutral` tidak diubah. `extract_moras()` dibaca sesudah query diubah, jadi lip-sync mengikuti kecepatan baru. Cache `speak` memakai kunci `emosi|kalimat`. Opsional: `VOICEVOX_SPEAKER_<EMOSI>` (mis. `VOICEVOX_SPEAKER_SHY=36`) memakai id gaya lain untuk emosi itu; nilai tidak valid diabaikan dengan peringatan; belum ada id yang diisi karena `/speakers` belum dilihat. `IRIS_VOICE_STYLE=0` mematikan seluruh penyesuaian. Cache di sisi overlay (`voiceCache`) masih berkunci kalimat saja; aman selama kalimat lokal tetap berpasangan dengan satu emosi.

**Cara pasang.** (1) Buat token: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. (2) Tambahkan `COMPANION_TOKEN=<hasilnya>` ke `C:\Users\<user>\.env` (dan baris kosongnya ke `.env.example`). (3) Ganti `server.py` dan `main.js`. (4) Restart server dan overlay.

**Risiko yang diketahui.** Header khusus di handshake WebSocket lewat `webRequest` belum dites di Electron-mu; mekanisme yang sama sudah dipakai untuk `Origin`, dan kalau gagal terminal server menulis alasannya. `test_client.html` tidak bisa mengirim header itu, jadi ditolak selama token aktif (kosongkan token sementara untuk debug). Angka gaya suara adalah tebakan awal dan perlu didengar.

**Diuji dengan tiruan (bukan sistem sungguhan).** 28 pemeriksaan untuk `server.py` (token benar, salah, kosong, Origin asing, klien tanpa Origin; log tidak memuat token; gaya tiap emosi, batas, `IRIS_VOICE_STYLE=0`; speaker per emosi; lip-sync lebih cepat atau lambat; cache per emosi) dan pemeriksaan `main.js` dengan Electron tiruan (pembaca `.env` untuk kutip, CRLF, `export`, komentar, duplikat, environment menang atas file; penjaga navigasi; header token terpasang di hook).

**v28b: salin gambar (`main.js`).** Tombol Salin di penampil gambar memanggil handler `copy-image` di `main.js`; kalau handler itu gagal, cadangannya `navigator.clipboard` (hampir selalu ditolak di jendela overlay) dan tombol menampilkan "Gagal menyalin (restart Iris; cek terminal)". Di PC ini terminal menulis `copy-image gagal: clipboard.writeImage is not a function`. Dokumentasi Electron masih mencantumkan `clipboard.writeImage`, dan tidak ada kode di `main.js` yang menimpa nama `clipboard` (diimpor dari `electron`), jadi dugaannya kekhasan versi Electron yang terpasang (versinya belum dicek). Handler asli dan v28 identik, jadi ini bukan regresi v28. Perbaikan: `copy-image` kini `async` dan mencoba berurutan (1) `clipboard.writeImage`, (2) `clipboard.write({ image })`, (3) `writeImageViaPowerShell()`: PNG sementara di `%TEMP%\iris-view` lalu `powershell.exe -NoProfile -NonInteractive -STA` dengan `System.Windows.Forms.Clipboard.SetImage` (tanpa shell, apostrof di path digandakan, batas 10 detik, file sementara dihapus). Tiap kegagalan dicatat di terminal, dan kalau cara 1 dan 2 tidak ada, terminal mencetak versi Electron dan daftar metode `clipboard` yang tersedia (berguna untuk mengetahui versi Electron tanpa mencarinya).

**Hasil uji 1 Nov (PC sungguhan).**
- **Server.** Saat start tidak ada peringatan "COMPANION_TOKEN kosong". `curl` handshake WebSocket tanpa header: 403, terminal server menulis "/ws ditolak: header X-Iris-Token tidak ada atau salah" (dibatasi sekali per 30 detik). Dengan token yang dibaca dari `~/.env` (43 karakter): 101 Switching Protocols (timeout setelahnya normal, koneksi dibiarkan terbuka menunggu data). Token yang salah (variabel `$t` kosong di jendela PowerShell baru) juga 403.
- **Overlay.** Terminal Electron menulis "Token /ws: terbaca (43 karakter), dikirim lewat header X-Iris-Token". Log server menunjukkan koneksi `[accepted]` dari overlay, dan `/agen sebutkan isi folder` dijawab Hermes ("Ada 5 file teks, 2 skrip Python, ditambah paket .deb Chrome") dengan label "Memproses tugas..." dan hitung detik (37 dtk) tampil. Artinya risiko yang tertulis di atas (header khusus di handshake WebSocket lewat `webRequest` belum dites di Electron) **terbukti aman**.
- **Bonus bukti untuk Bagian G.** `/agen` dari server Windows ke Hermes jalan, dan indikator Langkah 6 (label dengan hitung detik) tampil di overlay sungguhan. Belum terlihat: status `timeout`, `cancelled`, heartbeat.
- **Salin gambar.** Sebelum v28b tombol Salin gagal (lihat di atas); sesudah `main.js` v28b diganti dan overlay direstart, tombol menjadi "Tersalin ✓" (screenshot). Belum dikonfirmasi: apakah hasil tempel (Ctrl+V) benar-benar berisi gambarnya, dan baris `copy-image: ...` apa yang tercetak di terminal (menunjukkan cabang mana yang dipakai).

**Catatan pemasangan token (pelajaran 1 Nov).**
- Cara paling aman menulis token ke `.env`: `$t = python -c "import secrets; print(secrets.token_urlsafe(32))"; Add-Content -Path "$env:USERPROFILE\.env" -Value "`nCOMPANION_TOKEN=$t"`. Tanpa copy-paste dan tanpa menampilkan token. Cara salin lewat `| clip` lalu tempel di Notepad gagal sekali karena clipboard tertimpa teks perintah.
- Pastikan tab `.env` di Notepad sudah ditutup sebelum menulis dari PowerShell; tab lama yang masih terbuka bisa menimpa baris baru saat disimpan. Periksa hasilnya tanpa menampilkan isi: panjang baris `COMPANION_TOKEN` harus 59.
- Variabel `$t` hanya hidup di jendela PowerShell tempat dibuat. Untuk tes `curl` di jendela lain, baca token dari `.env`: `$tok = (Get-Content "$env:USERPROFILE\.env" | Where-Object { $_ -like 'COMPANION_TOKEN=*' }) -replace '^COMPANION_TOKEN=',''`.
- Server membaca `.env` hanya saat start: setelah mengubah token, restart server (dan overlay).
- Tab browser yang membuka `http://127.0.0.1:8765` (halaman tes) tidak bisa mengirim token dan terus mencoba lagi, sehingga log server penuh baris 403. Tutup tabnya.

### Uji v28 (1 Nov 2026)

- [ ] Tanpa `COMPANION_TOKEN`: server dan overlay jalan seperti sebelumnya; terminal server memperingatkan token kosong; terminal Electron bilang token tidak ada
- [x] Dengan token di `~/.env`: terminal Electron bilang "Token /ws: terbaca (43 karakter)"; overlay tersambung dan menjawab **(lulus 1 Nov)**. `http://127.0.0.1:8765/health` menampilkan `ws_token: aktif` belum dilaporkan
- [x] Server menolak tanpa token dan menerima dengan token yang benar, diuji dengan `curl` **(lulus 1 Nov)**: 403 dan baris "/ws ditolak" (sekali per 30 detik), 101 dengan token
- [ ] Overlay sengaja dijalankan dengan token salah (`$env:COMPANION_TOKEN="salah"; npm start`): overlay tidak tersambung dan terminal server menulis "/ws ditolak"
- [x] `/agen` tetap jalan dengan token aktif **(lulus 1 Nov: `/agen sebutkan isi folder` dijawab)**
- [ ] Chat biasa (kalimat bebas, bukan `/agen`) tetap dibalas model dengan token aktif
- [x] Seret file dari Explorer ke jendela overlay: lampiran tetap berfungsi dan halaman tidak pindah; tidak ada jendela baru terbuka **(lulus 1 Nov: lampiran masuk, halaman tidak pindah; screenshot area drop)**
- [x] Tombol Salin di penampil gambar menjadi "Tersalin ✓" **(lulus 1 Nov setelah v28b)**
- [x] Tempel (Ctrl+V) di Paint atau chat: gambar benar-benar tertempel; catat baris `copy-image: ...` di terminal kalau ada **(lulus 1 Nov, dilaporkan pemilik)**
- [x] Penampil gambar besar (klik gambar lalu "Buka besar") dan Ctrl+Alt+D (DevTools) tetap berfungsi **(lulus 1 Nov: DevTools terbuka lewat Ctrl+Alt+D, penampil besar dikonfirmasi pemilik)**
- [x] Dengarkan tiap emosi (`happy`, `sad`, `angry`, `surprised`, `shy`) lewat balasan Iris atau reaksi colek: terasa beda dari `neutral`, tidak berlebihan; mulut tetap sinkron **(lulus 1 Nov, dilaporkan pemilik; angka masih bisa disetel)**
- [ ] `IRIS_VOICE_STYLE=0` lalu restart: suara kembali datar seperti dulu
- [ ] (Opsional) `VOICEVOX_SPEAKER_SHY=<id dari /speakers>`: hanya kalimat `shy` yang berganti gaya

### Pembaruan v28c (1 Nov 2026): bubble tidak terpotong saat ada lampiran

File yang berubah: `index.html` saja (`main.js` tidak berubah; `main.js` yang dipakai sudah memuat v28b: `writeImageViaPowerShell` ada di baris 831). Selisih lengkap di `iris-v28c.patch`. Lolos `node --check` pada skrip modul; belum dites di Electron.

**Gejala (screenshot 1 Nov).** Bubble "Di sini ya? Oke." terpotong di tepi atas jendela: garis tepi atas hilang, scrollbar muncul, dan kotak 日本語 menyempit. Terjadi saat panel chat terbuka dan ada lampiran screenshot. Tanpa lampiran, bubble utuh.

**Penyebab (dua).**
1. `#attach` (thumbnail 88 px) berada di dalam alur layout `#root`, di antara `#char` dan `#barWrap`. Jendela berukuran tetap (`WIN_H` 620 + `CHAT_GROW` 160), jadi tiap ada lampiran karakter terdorong sekitar 98 px (88 px + jarak 10 px) ke atas dan ruang di atas kepala habis.
2. `placeBubble()` memakai `visRect.t` (tepi atas **layar**, bisa negatif dalam koordinat jendela) sebagai batas atas, padahal yang memotong adalah tepi atas **jendela**. Bubble dikira masih muat padahal sudah keluar jendela. Hal yang sama berlaku untuk batas kiri, kanan, dan bawah.

**Perbaikan (`index.html`).**
- `#attach.has` kini `height: 0; margin-top: -10px; align-items: flex-end; position: relative; z-index: 6` dan `flex-wrap: nowrap`: thumbnail meluap ke atas bar tanpa memakai tinggi di layout, jadi karakter tidak terdorong. Empat gambar (`MAX_IMAGES = 4`) muat dalam satu baris (4 x 88 + 3 x 8 = 376 px dari 396 px).
- `placeBubble()` memakai `V`, irisan area layar dan jendela sendiri: `l = max(0, visRect.l)`, `t = max(0, visRect.t)`, `r = min(innerWidth, visRect.r)`, `b = min(innerHeight, visRect.b)`.
- `fitBubble()`: tinggi maksimal bubble menyisakan jarak 8 px dari tepi atas jendela (`- 8 - 8`, bukan `- 16`; hasil akhirnya sama, dibuat eksplisit supaya sejalan dengan `M` di `placeBubble`).

**Risiko yang diketahui.** Kotak `#attach` sekarang bertinggi 0 dan thumbnail meluap darinya. Hit-test memakai `elementFromPoint(...).closest('.interactive')`, jadi klik pada thumbnail dan tombol ✕ seharusnya tetap tertangkap, tetapi belum dites.

### Pembaruan v28d (1 Nov 2026): pil status tidak tertimpa thumbnail

**Digantikan oleh v28e (di bawah)**: hasil v28d dinilai jelek di layar (pil di tengah kaki karakter, thumbnail menimpa kaki), jadi tata letaknya diganti total. Catatan ini dibiarkan sebagai riwayat.

File yang berubah: `index.html` saja (selisih terhadap v28c di `iris-v28d.patch`). Lolos `node --check`; belum dites di Electron.

**Gejala (screenshot 1 Nov).** Saat `/agent 17 dikali 7 berapa` berjalan dan ada thumbnail lampiran, pil "Masih memproses..." tertimpa thumbnail. **Akibat langsung v28c**: `#status` berada di alur layout tepat di atas `#attach`; sebelum v28c `#attach` memakai tinggi sendiri sehingga tidak bertumpuk, sesudah v28c thumbnail meluap ke atas dan menimpa pil.

**Perbaikan.** `renderAttach()` menambah kelas `hasatt` di `#root` selama ada lampiran, dan `#root.hasatt #status { translate: 0 -98px; }` menaikkan pil di atas thumbnail. Properti `translate` tidak memengaruhi layout, jadi karakter tetap tidak terdorong.

**Uji v28d.**
- [ ] Lampirkan screenshot lalu kirim `/agen ...`: pil status tampil di atas thumbnail, tidak bertumpuk
- [ ] Hapus lampiran: pil kembali ke posisi semula
- [ ] Dua sampai empat lampiran: tetap tidak bertumpuk

### Pembaruan v28e (1 Nov 2026): dock di atas bar (pil status dan lampiran sejajar)

File yang berubah: `index.html` saja (selisih terhadap v28d di `iris-v28e.patch`). Lolos `node --check`; belum dites di Electron, dan tampilannya belum dinilai di layar.

**Gejala (screenshot 1 Nov, setelah v28d).** Pil "Memproses tugas..." melayang di tengah kaki karakter dan thumbnail 88 px menimpa kaki kanan. Penempatannya jelek.

**Penyebab.** v28c dan v28d hanya menambal tumpukan: `#status` tetap di alur layout (jadi tiap muncul, karakter ikut terdorong naik ~42 px) dan `#attach` meluap ke atas dari titik yang sama.

**Perbaikan.** Dibuat satu wadah `#dock` di dalam `#barWrap`, posisi absolut tepat 8 px di atas bar input (`bottom: calc(100% + 8px)`), isinya satu baris: pil status di kiri, thumbnail di kanan. Keduanya tidak memakai tinggi di layout, jadi karakter tidak lagi terdorong atau melompat saat tugas agen mulai atau lampiran ditambah. Thumbnail diperkecil 88 px jadi 56 px (satu angka: `--thumb` di `#attach`; tetap bisa diklik untuk tampilan besar); empat gambar = 4 x 56 + 3 x 6 = 242 px. Kalau ruang sempit, pil menyusut dengan elipsis. Aturan `hasatt` v28d dihapus. Perbaikan batas bubble v28c tetap dipakai.

**Risiko yang diketahui.** Thumbnail 56 px di sisi kanan masih bisa menyentuh kaki karakter karena kaki berada sekitar 22 px di atas bar; kalau mengganggu, kecilkan `--thumb`. `#dock` ber-`pointer-events: none` dengan `#attach` ber-`pointer-events: auto`; klik thumbnail dan tombol ✕ perlu dites.

### Uji v28e (1 Nov 2026)

- [ ] Kirim `/agen ...` tanpa lampiran: pil muncul di atas bar sebelah kiri, karakter tidak bergeser sama sekali
- [ ] Tambah 1 lampiran lalu kirim `/agen ...`: pil dan thumbnail sejajar satu baris, tidak bertumpuk
- [ ] 4 lampiran: muat dalam satu baris, pil menyusut dengan elipsis kalau sempit
- [ ] Klik thumbnail (tampilan besar) dan ✕ (buang): keduanya tetap bisa diklik
- [ ] Mode fokus dan sembunyi di tepi: pil dan thumbnail ikut hilang bersama bar

### Uji v28c (1 Nov 2026)

- [ ] Ganti `index.html`, restart overlay
- [ ] Buka chat, lampirkan screenshot (tombol kamera), minta balasan panjang: bubble utuh, tidak menutupi kepala
- [ ] Ulangi dengan 2 sampai 4 lampiran: thumbnail berjajar dalam satu baris dan karakter tidak bergeser
- [ ] Klik thumbnail (penampil besar) dan tombol ✕ lampiran: keduanya tetap bisa diklik
- [ ] Seret jendela mendekati tepi atas layar lalu minta balasan panjang: bubble boleh menyempit atau turun, tapi tidak terpotong
- [ ] Tanpa lampiran dan chat tertutup: tampilan bubble sama seperti sebelumnya

### F7b. Daftar kerja: fitur tier list yang belum dipasang

Urutan di bawah adalah urutan yang disarankan. Paket 2 sudah selesai dan dites (v20); Paket 3 dan seterusnya belum dikerjakan. Kerjakan satu paket, uji, baru lanjut.

**Paket 2 (tier A, murah, logikanya mirip timer yang sudah ada): selesai v20, dites**
- [x] `/alarm HH:MM [nama]`: alarm jam tertentu. Simpan di `localStorage`, periksa tiap detik (atau jadwalkan `setTimeout` ke jam tujuan), bunyi lonceng `chime()` dan kalimat bersuara lewat `speak`. Perlu aturan kalau overlay ditutup lalu dibuka lagi (alarm yang lewat saat tertutup: sebut sekali atau abaikan), dan `/alarm` tanpa argumen untuk melihat daftar, `/alarm batal` untuk menghapus. Tambahkan ke `HELP` **[selesai v20, dites]** Alarm sekali bunyi, maksimal 10, disimpan di `localStorage` (`iris.alarms`), diperiksa tiap detik. Yang lewat saat overlay tertutup disebut sekali saat overlay dibuka lalu dibuang (batas terlewat 90 detik). Bunyi `chime()` dan kalimat bersuara mengikuti saklar "Timer diucapkan Iris"; kalau Iris sedang membacakan balasan, alarm menunggu giliran sampai sekitar 60 detik. Tidak berulang (belum ada "tiap hari"). `/alarm` menampilkan daftar, `/alarm batal <no|semua>` menghapus
- [x] `/jam`: Iris mengucapkan jam sekarang (kalimat tetap Jepang dengan angka, disintesis VOICEVOX; angka tidak bisa di-prefetch seperti kalimat tetap lain). Opsional: pengucapan tiap jam, bawaan mati, dengan saklar di Pengaturan dan tidak berbunyi saat mode fokus, tidur, atau Iris sedang bicara **[selesai v20, dites]** Jam diucapkan dengan angka kanji. `/jam nyala|mati` mengatur ucapan tiap jam (bawaan mati, saklar di Pengaturan); tidak berbunyi saat mode fokus, tidur, bicara, rekaman, atau suara dibisukan

**Paket 3 (tier A, sedang): kode selesai v21 sampai v21e, penyempurnaan visual berjalan**
- [x] Sembunyi di tepi layar (mengintip) **[v21 sampai v21e; dites sebagian lewat screenshot]**: geser jendela di `main.js` ke kiri atau kanan sampai hanya sebagian karakter terlihat, klik atau kursor mendekat memunculkannya lagi. Lebih ramah game daripada Mode fokus (karakter tidak hilang total). Perlu: IPC baru, posisi asal diingat, dan jangan bentrok dengan `savePos` (jangan menyimpan posisi sembunyi) dan `setChatOpen`

**Paket 4 (tier A, besar, hanya kalau paket 1 sampai 3 stabil): kode ditulis v22, belum dites**
- [x] Duduk di tepi jendela atau taskbar **[v22, kode ada, belum dites di Windows]** (diputuskan: PowerShell yang tetap hidup; saklar privasi bawaan mati; jendela ditutup atau digeser terlalu ke atas = turun ke dasar layar; taskbar sama dengan dasar area kerja, jadi "duduk di taskbar" = berdiri di dasar layar): butuh daftar posisi jendela dari Windows (modul native atau skrip PowerShell; belum diverifikasi mana yang jalan di versi Electron ini), pose duduk, dan saklar privasi bawaan mati. Hanya posisi dan ukuran jendela yang dibaca, bukan judul atau isinya (selaras dengan aturan privasi v15). Perilaku saat jendela bergerak atau ditutup harus diputuskan dulu

**Tier B (setelah paket di atas, nilai lebih kecil)**
- [ ] Atur FPS dari Pengaturan: ubah `FPS_IDLE` dan `FPS_ACTIVE` jadi bagian `SET` (usaha kecil)
- [ ] Tangan mengejar kursor saat didekatkan: butuh gerakan lengan yang natural; ditunda sampai gerakan lengan (`ARM_GEST`) dinilai baik secara visual
- [ ] Menari mengikuti musik: butuh tangkapan audio sistem dan klip tari VRMA; ditunda sampai klip aksi (v18) punya file. **Diperbarui 4 Nov 2026: diputuskan diambil, lihat Bagian P (klip tari belum ada; rancangan awal tanpa lengan)**

**Tier C (dilewati, dicatat supaya tidak diusulkan ulang)**
- Jalan-jalan di desktop dan lompat antar jendela, mode chibi, mode layar besar, sistem makan

**Aturan kerja:** hanya ide dan teknik yang diambil dari Desktop Mate dan Mate Engine; tidak ada file, model, atau kode yang disalin. Cek lisensi sebelum Iris dipublikasikan.


### Pembaruan v29 dan v30 (1 Nov 2026): format balasan, laporan agen netral, web search Hermes

File yang berubah: `server.py` saja (`main.js` dan `index.html` tidak berubah). Lolos `py_compile`; belum dites di PC. Satu berkas `server.py` memuat v29 dan v30 sekaligus.

**v29: balasan LLM yang melanggar format (gejala 1 Nov).**
- Gejala: (1) balasan Iris berupa teks Indonesia polos (jawaban soal lagu Gen Z, memakai gaya chatbot umum dan menawarkan link Spotify) tanpa tag dan tanpa Jepang; (2) balasan `[neutral] Halo, Rover! ...` yang punya tag tetapi tanpa kalimat Jepang dan tanpa `|||`. Keduanya tampil di bubble **tanpa suara**, dan pada kasus (2) tag `[neutral]` ikut tampil mentah.
- Penyebab (dari kode): `process_line` mencocokkan baris dengan `LINE_RE`; kalau gagal, baris ditampilkan apa adanya dengan `jp` kosong, jadi tidak ada suara. Balasan yang salah juga disimpan ke riwayat, sehingga model meniru format yang salah pada giliran berikutnya. Dugaan penyebab di hulu: salah satu model di combo Iris (9Router) kurang patuh format; model mana yang menjawab **belum dicek**.
- Perbaikan: `repair_line()` memakai `REPAIR_SYSTEM` untuk meminta LLM mengubah baris yang melenceng menjadi `[emosi] jp ||| id` (satu panggilan tambahan hanya untuk baris yang salah); `process_line` kini mengembalikan baris yang dipakai dan riwayat menyimpan baris hasil perbaikan; pengingat format ditambahkan di akhir pesan pengguna ke LLM (tidak disimpan di riwayat); cadangan terakhir kalau perbaikan gagal: teks tampil tanpa suara dengan tag awal dibuang. Terminal mencetak `baris diperbaiki` saat perbaikan dipakai.
- Saran terkait (belum dikerjakan): taruh model yang paling patuh format di urutan pertama combo Iris (kandidat dari tes 9Router: `gemini-3-flash-preview`, bukan yang flash-lite).

**Web search Hermes (H5 no. 1): terverifikasi aktif.**
- `cek-websearch-hermes.sh` (hanya membaca; dijalankan di WSL, mis. `wsl bash "/mnt/c/Users/<user>/Downloads/cek-websearch-hermes.sh"`). Hasil 1 Nov: `config.yaml` baris 235 `web: backend: exa`, `provider_tier: exa: free`; semua kunci backend (Firecrawl, SearXNG, Tavily, Exa, Parallel) kosong di `.env`, artinya Exa tier gratis bekerja tanpa `EXA_API_KEY`; tes ke API server HTTP 200, Hermes menyebut hasil dari `web_search` lengkap dengan tanggal dan URL.
- Catatan: URL yang dikembalikan adalah halaman daftar berita (`medcom.id/teknologi/news-teknologi`), bukan artikel spesifik, dan isi klaimnya tidak diverifikasi. Baris `hermes: command not found` di skrip hanya soal PATH saat memakai `wsl bash skrip`, bukan tanda Hermes tidak terpasang.
- Web search hanya bekerja lewat jalur `/agen`; pesan biasa tetap dijawab LLM chat tanpa internet. Routing otomatis info terkini tetap fitur terpisah (H2), dengan saklar bawaan mati.

**v30: laporan `/agen` netral dan bersumber.**
- Gejala (tugas `/agen cari berita teknologi terbaru hari ini <URL Kompas>`, 11:21): laporan Hermes penuh slang dan kata rusak ("Apple-Gembel", "ngelClick", "Jekardah AI News"); URL Kompas yang diberikan tidak dibuka dan tidak disebut; klaim spesifik (angka, CVE) tanpa sumber per klaim dan dari agregator tak dikenal, **belum diverifikasi**; ringkasan Iris mengulang "keren banget kan?".
- Dugaan penyebab: skill persona di Hermes aktif. `hermes skills list` (1 Nov) menunjukkan `iris-persona`, `iris-auto`, `iris-modes`, `iris-memory`, `jarvis-metan`, `voicevox-tts-bridge`, dan `humanizer` semuanya `enabled` (89 aktif, 16 nonaktif). Apakah skill-skill ini yang membuat gaya slang **belum dibuktikan**.
- Perbaikan di `server.py`: `HERMES_SYSTEM` kini menyuruh Hermes menulis laporan netral tanpa persona Iris, mencantumkan sumber (nama situs dan URL) per klaim, menulis nama persis seperti di sumber, dan membuka URL dari pengguna lebih dulu (`web_extract`) atau menyatakan gagal membukanya. `AGENT_RESULT_PROMPT` kini melarang Iris menambah fakta di luar hasil mentah, menyuruhnya bilang "belum yakin" untuk hasil yang janggal, dan melarang pertanyaan retoris penutup.
- Kalau gaya Iris masih muncul setelah tes: jalankan `hermes skills config` di WSL (mengatur skill per platform), pilih platform yang dipakai API server, matikan `iris-persona` dan `iris-auto` dulu, lalu bertahap `iris-modes`, `jarvis-metan`, `voicevox-tts-bridge`, `iris-memory`, `humanizer`; restart `hermes gateway` dan tes lagi. Pengaturan per platform tidak memengaruhi pemakaian Hermes lewat WhatsApp atau Telegram. Nama platform API server di menu itu belum diketahui. Kalau isi masih ngawur padahal gaya sudah benar, itu soal kualitas model di combo Iris.

**Catatan penerapan patch overlay.** v28b (`main.js`), v28c dan v28e (`index.html`) digabung menjadi `iris-v28-gabungan.patch` (v28d dibuang karena digantikan v28e). `main.js` dan `index.html` yang diunggah 1 Nov sudah memuat ketiganya, jadi patch tidak perlu diterapkan lagi dan tidak ada berkas overlay yang diubah. `spawn` sudah di-import di `main.js` (baris 5). Sisa v28d (`hasatt`) tidak ada di `index.html`.

**Catatan panel chat.** Riwayat chat tidak hilang: pesan pengguna dicatat lewat `logUser`. Panel chat pendek dan otomatis menggulir ke bawah (`logScroll`), jadi balasan Iris yang panjang bisa menutupi pesan pengguna di atasnya sampai panel digulir ke atas.

---

# Bagian G: Pengerasan dan Verifikasi Jembatan (30 Okt sampai 1 Nov 2026)

**by: KangJiho**

Catatan progres terpisah (`iris-overlay-progress.md`) dilebur ke sini pada 1 Nov 2026. "Terbaca dari kode" berarti kodenya ada di berkas yang diunggah pada 1 Nov; itu bukan bukti fiturnya sudah diuji berjalan.

## G1. Status ringkas

| Bagian | Status | Catatan |
|---|---|---|
| Langkah 1: bind localhost | Selesai | `COMPANION_HOST=127.0.0.1`, port 8765 |
| Langkah 2: akses via localhost | Selesai (sisi WSL) | Tes dari Windows belum dilaporkan |
| Langkah 3: amankan `.env` | Selesai, 1 hal belum pasti | Z: tersinkron cloud atau tidak, belum dicek |
| Langkah 4: area tes dummy | Sebagian | Tes hapus `tes.txt` belum dijalankan |
| Langkah 5: uji gagal | Selesai | Hermes mati ramah; cancel mengirim `interrupted: true` |
| Poin A: chat biasa (401) | Selesai | Penyebab: `NINEROUTER_API_KEY` kosong |
| Poin B: `.env` ke `~/` | Selesai | `.env` lama di Z: dihapus |
| Poin C: cancel | Sisi server ada, belum diuji | Hermes tetap jalan setelah cancel |
| Poin D: status, heartbeat, timeout | Sisi server dan overlay ada; label dengan hitung detik terlihat di overlay sungguhan (1 Nov); timeout, cancel, heartbeat belum | Lihat G5 |
| Server dari Windows | Selesai | Chat biasa terbukti jalan |

## G2. Langkah 1 sampai 5

- **Langkah 1:** `COMPANION_HOST` dari `0.0.0.0` ke `127.0.0.1`; `ss -tlnp` menunjukkan LISTEN hanya di `127.0.0.1:8765`.
- **Langkah 2:** `curl http://localhost:8765/health` dari WSL HTTP 200; tidak ada IP tetap di kode Electron. Kalau dari Windows tidak tersambung, jangan ubah bind ke `0.0.0.0`; laporkan dulu (kemungkinan firewall Windows atau forwarding localhost WSL).
- **Langkah 3:** tidak ada `.git`, jadi `.gitignore` tidak relevan. `chmod 600` di `/mnt/z/` tidak andal, jadi `.env` dipindah ke `~/.env`; `server.py` membaca `~/.env` dulu, lalu `.env` lokal, dan mencetak `[WARN] File .env tidak ditemukan ...` kalau keduanya tidak ada. `/health` hanya menampilkan "kunci terisi". **Belum pasti:** apakah drive Z: tersinkron ke cloud atau dipakai orang lain; cek manual dari Windows (folder OneDrive/Dropbox di Z: atau klien sync yang menunjuk ke Z:). Kalau ya, ganti kunci.
- **Langkah 4:** `~/hermes-test/` berisi `tes.txt`, `catatan.txt`, `contoh.md`, `subfolder/`. Listing folder lewat `/agen` benar, kalimat pembuka muncul lebih dulu. Tes hapus `tes.txt` **belum dijalankan** (menunggu konfirmasi eksplisit). Folder Downloads tidak disentuh.
- **Langkah 5:** `HERMES_URL` diarahkan ke port salah (`127.0.0.1:9999`) lalu dikembalikan: pesan error ramah. `{"type":"cancel"}` menghasilkan `{"type":"done","interrupted":true}`. **Temuan:** agen Hermes tetap jalan di belakang layar setelah cancel.

## G3. Poin A dan B: 401 dan `.env`

1. Dugaan awal "gateway Hermes tidak membaca `.env`" salah (`/agen` berhasil di Langkah 4).
2. `HERMES_API_KEY` (overlay) dan `API_SERVER_KEY` (Hermes) sama; `curl` langsung ke Hermes berhasil.
3. Penyebab sebenarnya: `NINEROUTER_API_KEY` kosong di `~/.env`, sehingga 9Router menolak dengan 401 "Missing API key". Ini juga menjelaskan 401 janggal saat tes "Hermes mati".
4. Kunci diisi manual, `server.py` direstart, "halo Iris" lewat `/ws` membalas normal. `hermes-gateway` tidak direstart.
5. Server sekarang dijalankan dari PowerShell dengan `.venv` Windows, jadi `.env` harus ada di `C:\Users\<user>\.env` (salin dari WSL: `wsl cp /home/<user>/.env "/mnt/c/Users/<user>/.env"`). Bukti chat jalan: `test_client.html` menerima "tesd" dan Iris membalas `[happy]` dengan teks Jepang dan Indonesia.
6. `.env`, `.env.bak`, `.env.bak2`, `.env.bak_step5` di folder proyek Z: dihapus setelah chat normal terbukti; tersisa `.env.example`.
7. Jangan jalankan server WSL dan server Windows bersamaan (port 8765 bentrok).

## G4. Poin C: cancel

Tujuan: hentikan task di sisi Hermes, atau jujur bahwa tidak bisa.
- [x] Teks "Dibatalkan, tugas mungkin masih berjalan" (bukan "Selesai") ada di `server.py` **[belum diuji]**
- [ ] Cek apakah request ke Hermes benar-benar ditutup saat cancel (butuh kode `api_server.py` asli, lihat G6)
- [ ] Cek apakah Hermes punya endpoint stop/cancel
- Ide (dugaan, tes dulu dengan file dummy): `ask_hermes` sekarang memakai `stream: False`; mengganti ke `stream: True` dan menutup koneksi saat cancel mungkin lebih mungkin menghentikan agen.

## G5. Poin D: status, heartbeat, timeout

Terbaca dari kode (`server.py`, `index.html`):
- `HERMES_TIMEOUT` lewat `env_float()`: kosong, bukan angka, <= 0, `inf`, atau `nan` jatuh ke default dengan peringatan. **Default di kode 900 detik** (sejak v9; bukan 120).
- Pesan `{"type":"status","busy","state","text","elapsed"}`; state `working | done | failed | timeout | cancelled`.
- Heartbeat "Masih memproses..." tiap 30 detik (task terpisah, dihentikan di `finally`). Satu status akhir `busy:false` di `finally` terluar, setelah Iris selesai menyampaikan hasil.
- Teks cancel jujur kalau permintaan sudah terkirim dan Hermes belum terbukti selesai; "Selesai" hanya kalau Hermes benar-benar membalas.
- `HermesTimeout` khusus untuk `ReadTimeout`; `ConnectTimeout` dilaporkan sebagai "Hermes tidak aktif".
- Overlay: `onStatus()` menampilkan label dengan hitung detik, gerakan `think` selama `busy`, dan bubble untuk gagal atau dihentikan (tampil 5 detik); indikator ditutup saat WebSocket putus.

Sudah diuji hanya dengan harness Hermes palsu (sukses, timeout asli, Hermes mati, cancel) dan validasi `env_float`. Terbukti di PC sungguhan pada 1 Nov: `/agen` dari server Windows ke Hermes jalan, dan label "Memproses tugas..." dengan hitung detik (37 dtk) tampil di overlay. **Belum diuji** dengan Hermes dan overlay sungguhan: `/agen` dari server Windows, `/health` (Hermes `HTTP 200, kunci terisi`), suara VOICEVOX, status `timeout` / `cancelled`, heartbeat.

## G6. Koreksi atas laporan Iris (31 Okt) dan data yang masih perlu

Laporan Iris (00:08 dan 00:45) tidak dipakai sebagai bukti:
- `_HERMES_TIMEOUT` dan `heartbeat_task` ada di `api_server.py` milik Hermes (`~/.hermes/hermes-agent/gateway/platforms/api_server.py`), bukan di folder overlay.
- `git status` dijalankan di `hermes-backup/hermes-agent` (16.690 file berubah), bukan repo Hermes aktif, jadi klaim "tidak ada perubahan lokal" tidak terbukti.
- Tes interrupt tidak bersih (file atau run lama tercampur, waktu disconnect tidak sesuai rencana, tes memakai `/v1/chat/completions` padahal kode yang dikutip adalah `_handle_session_chat`). Kesimpulan "disconnect tidak menghentikan task" belum kuat.
- Diff usulan Iris dibuang karena tidak sesuai Poin D (heartbeat 10 detik terus jalan, tipe pesan salah, `busy:false` terkirim sebelum hasil disampaikan, deteksi timeout lewat string, perubahan teks yang tidak diminta).

Masih perlu (read-only, dari repo Hermes yang benar):
- [ ] Kode asli `_handle_session_chat`, `_handle_session_chat_stream`, `_drain_session_stream_task_on_disconnect`, handler `/v1/chat/completions`
- [ ] `grep -n` dengan konteks untuk `_HERMES_TIMEOUT` dan `heartbeat_task`
- [ ] `stat` `api_server.py` dan `hermes-backup/`, `hermes --version`, `git -C ~/.hermes/hermes-agent log -1` dan `status --short | head`
- [ ] Tes interrupt ulang yang rapi (file dummy terpisah per tes, timestamp disconnect, amati minimal 60 detik, pastikan tidak ada run lama)

## G7. Temuan kecil dari berkas (1 Nov)

- Electron yang terpasang di PC ini tidak punya `clipboard.writeImage` (galat "is not a function" saat Salin gambar); sudah ditangani di v28b dengan cadangan bertingkat. Versi Electron belum dicek: lihat `package.json` atau baris diagnosa di terminal.
- `requirements.txt`: `faster-whisper` sudah ditambahkan (F3). `python-dotenv` belum terkonfirmasi ada (catatan 31 Okt bilang belum; isi berkas terbaru belum dicek). `server.py` mengimpornya. **Terjawab 1 Nov malam:** `requirements.txt` yang diunggah memang belum memuatnya; baris `python-dotenv>=1.0` sudah ditambahkan (lihat I11).
- `main.js` sudah memakai `contextIsolation: true`, `nodeIntegration: false`, dan izin hanya untuk mikrofon di halaman overlay. `setWindowOpenHandler` dan `will-navigate` ditambahkan di v28 (masih menunggu tes seret file dan penampil gambar).
- Berkas di folder proyek yang tidak dibaca kode: `iris-system.md`, `roadmap-ai-companion.md`, `iris-companion-gabungan.md`, `assets.rar`, `server-v16.patch` (sudah tidak ada). `test_client.html` hanya dipakai halaman tes di `http://localhost:8765/`. `iris-memory.json` muncul sendiri setelah `/ingat` dipakai; jangan dihapus. `screens/` berisi `layar-terakhir.jpg` (screenshot terakhir untuk Hermes; matikan dengan `IRIS_SAVE_SCREEN=0`).

## G8. Urutan berikutnya

1. Pastikan `/health` menunjukkan Hermes `HTTP 200, kunci terisi` dari server Windows.
2. Skrip probe WebSocket: `/agen` biasa, timeout (`HERMES_TIMEOUT=10`, kembalikan setelahnya), cancel, heartbeat; amati pesan `status`.
3. Langkah 6 di overlay sungguhan: label dan hitung detik sudah terlihat (1 Nov); sisanya gerakan `think`, bubble gagal/dihentikan.
4. Ambil data read-only dari repo Hermes yang benar (G6), lalu ulangi tes interrupt dengan rapi.
5. Cek `python-dotenv` di `requirements.txt`. Selesai 1 Nov malam (lihat I11).
6. Cek manual dari Windows: apakah Z: tersinkron ke cloud.
7. Putuskan tes hapus `tes.txt`.

## G9. Ide pengerasan (belum dikerjakan)

- [x] Token autentikasi untuk `/ws`: selesai di v28, lewat header `X-Iris-Token` (bukan URL, supaya tidak tercetak di log); dites di PC sungguhan 1 Nov (lulus).
- [x] `setWindowOpenHandler` (tolak semua) dan `will-navigate` di `main.js`: selesai di v28.
- Konfirmasi di overlay untuk tugas `/agen` yang berbau hapus atau pindah file.
- Path file di hasil `/agen` bisa diklik atau diberi tombol "Buka di Explorer" (`revealFile` sudah ada di preload).
- Simpan riwayat obrolan ke file supaya tidak hilang saat server restart; tombol tray atau `/status` untuk menampilkan hasil `/health`.

---

# Bagian H: Tier List Fitur dan Tools Baru (1 Nov 2026)

Daftar fitur dan tools yang **belum ada** di Iris, dinilai dari dampak ke pengalaman, usaha, risiko, dan apakah sudah tercatat di bagian lain. Yang sudah ada tidak diulang (mood, fun fact, ganti baju, alarm, timer, push-to-talk, terjemah layar, `/belajar`, memori ringan, sembunyi di tepi, duduk di jendela, dan sebagainya). Aturan kerja tetap: satu paket, uji, baru lanjut.

## H1. Tier S: kerjakan dulu

| Fitur / tool | Kenapa | Usaha | Status |
|---|---|---|---|
| Tutup backlog `[belum dites]` | Fitur baru di atas kode yang belum teruji berisiko | Kecil, makan waktu | **hampir selesai** (sisa: v18 gerak halus dan gerbang emosi, v28c, isi Console DevTools) |
| Paket klip VRMA CC0 (greet, peace, dance, pegang tepi) | Kodenya ada, filenya belum; membuka sapaan gerak, sembunyi sambil memegang tepi, dan menari | Kecil (cari dan konversi file) | belum |
| Konfirmasi untuk `/agen` yang berbau hapus atau pindah file | Pengaman utama karena Hermes bisa menjalankan terminal dan file (G9) | Sedang | **selesai (v34, lulus tes 1 Nov malam)** |
| Cancel yang benar-benar menghentikan agen | Stop sekarang hanya jujur bilang "tugas mungkin masih berjalan" (G4); butuh baca `api_server.py` | Sedang | belum (tes cancel dinyatakan lulus, tapi apakah agen sungguh berhenti belum dicatat) |
| Push dari Hermes ke overlay (cron atau hasil Telegram, lalu Iris bicara sendiri) | Naik dari Tier A di Bagian A; membuat Iris proaktif tanpa kamu mengetik; pola `speak` sudah ada | Sedang | belum |
| Riwayat obrolan persisten dan `/status` | Obrolan hilang saat server restart (G9) | Kecil | belum |
| Auto-start bersama Windows | Pendamping yang harus dijalankan manual jarang dipakai (E1.7) | Kecil sampai sedang | belum; diputuskan diambil 4 Nov 2026 bersama skrip setup dan cek kesehatan, lihat Bagian Q |

## H2. Tier A: nilai tinggi, setelah S

| Fitur / tool | Catatan |
|---|---|
| Briefing pagi | Cuaca, deadline `cek-elearning`, dan alarm hari ini dalam satu sapaan pertama (E2.5) |
| Seret dokumen (PDF, docx, txt) ke Iris | Diringkas lewat Hermes; sekarang seret file hanya untuk gambar |
| Terjemah cepat teks terpilih atau clipboard (mis. `Ctrl+Alt+T`) | Murah: prompt khusus di jalur clipboard yang sudah ada |
| Tombol "Buka di Explorer" di kartu hasil agen | `revealFile` sudah ada di preload, tinggal dipasang (G9) |
| Penjaga disk dan sistem | Peringatan C: dan Z: 93% penuh, RAM, baterai; bisa dimatikan; pasangkan dengan skill Storage Analyzer Hermes (dry-run dulu) |
| Cadangan LLM lokal (Ollama) | Kalau 9Router mati, chat biasa tetap jalan |
| Barge-in | Mengetik atau bicara langsung memotong suara Iris |
| Routing otomatis info terkini | "Trending", "harga", "cuaca sekarang" langsung ke Hermes; wajib ada saklar, bawaan mati (E1.3) |
| Lip-sync dari mora VOICEVOX | **Sudah ada sebagai v2** (`extract_moras`, `updateVisemes`, `curMoras`); sisa hanya penyetelan opsional, lihat Bagian J1 |

## H3. Tier B: bagus, tapi nanti

- Wake word atau hands-free (setelah push-to-talk stabil)
- Reaksi ke musik yang sedang diputar (bisa jadi pemicu menari)
- Sapaan saat jendela game aktif (opt-in, hanya nama proses, jaga privasi)
- Komentar layar berkala (Fase 6), opt-in, model lokal kalau bisa, ada tombol mati
- Suara Indonesia opsional (Piper atau edge-tts) untuk mengatasi batasan "TTS hanya Jepang"
- Memori sinkron dengan Hermes (Tahap 7); hati-hati data sensitif ikut terucap
- `/catat` dan `/todo` ke file lokal (mirip `/ingat`)
- Statistik Pomodoro harian dan timer yang bertahan setelah overlay ditutup
- Jurnal harian Iris dari skor mood
- FPS dan hotkey bisa diatur di Pengaturan

## H4. Tier C: lewati dulu

- Installer atau packaging (baru perlu kalau mau dipublikasikan; cek lisensi aset dulu)
- Multi-karakter, dashboard web, EMAGE, jalan-jalan di desktop, mode chibi (sebagian sudah Tier C di F7)

## H5. Tools/skill sisi Hermes yang layak ditambah

1. ~~Pastikan **web search** aktif di Hermes~~ **selesai 1 Nov 2026**: aktif lewat Exa tier gratis (`web.backend: exa`), terbukti lewat tes API server; hanya jalur `/agen` (lihat "Pembaruan v29 dan v30")
2. Skill **`cek-elearning`** (tugas nyata pertama, alasan jembatan dibangun)
3. Tool **kontrol media dan volume Windows**
4. **Pembersih disk aman**: dry-run, lalu konfirmasi sebelum hapus
5. **Pencarian catatan kuliah** di satu folder (RAG ringan)

## H6. Urutan yang disarankan

1. Tutup sisa backlog: tes v28c, gerak halus dan gerbang emosi, lihat isi Console DevTools.
2. Siapkan paket klip VRMA, lalu konfirmasi tugas berbahaya, cancel yang sungguh menghentikan agen, dan riwayat obrolan persisten.
3. Push dari Hermes, auto-start, lalu briefing pagi.

## H7. Masih menggantung dari Bagian G (belum ada konfirmasi di sesi ini)

- [x] Cek `python-dotenv` ada di `requirements.txt`: belum ada, baris `python-dotenv>=1.0` ditambahkan 1 Nov malam (venv yang berjalan sudah memilikinya karena `server.py` memuatnya; `requirements.txt` baru berguna untuk instalasi ulang)
- [ ] Cek apakah Z: tersinkron ke cloud
- [ ] Putuskan tes hapus `tes.txt`
- [ ] Konfirmasi suara Metan keluar saat menyampaikan hasil tugas, tanpa suara dobel dari sisi Hermes
- [ ] Pindahkan file lama `/home/<user>/Downloads/tst` ke folder Download Windows
- [ ] Tugas nyata pertama: skill `cek-elearning`

## H8. Tambahan dari sesi 1 Nov (siang)

Ide baru yang muncul dari masalah sesi ini, belum dikerjakan:
- **Pil status koneksi** di overlay (VOICEVOX, 9Router, Hermes hidup atau mati). Endpoint `/health` sudah mengecek ketiganya, tinggal ditampilkan. Tier S
- **Retry otomatis untuk 503 dari Hermes** (sekali, jeda beberapa detik). Tier S
- **Catatan pelanggaran format di terminal** (model mana di combo yang sering melenceng). Tier S, murah; sebagian sudah ada lewat log `baris diperbaiki` (v29)
- **Cadangan LLM lokal (Ollama)** dinaikkan prioritasnya karena dua masalah di sesi ini (503 dan format) berasal dari model gratis di combo

---

# Bagian I: Status dan Daftar Kerja Lanjutan (1 Nov 2026)

Disusun dari Bagian F7b, G, dan H, ditambah hasil uji sesi 1 Nov siang sampai sore. Aturan kerja tetap: satu paket, uji, baru lanjut.

## I1. Sudah beres (dinyatakan aman, 1 Nov 2026)

- [x] **Paket Ketahanan:** pil status koneksi (VOICEVOX, 9Router, Hermes), retry otomatis 503 satu kali, catatan model pelanggar format di terminal, model paling patuh format di urutan pertama combo Iris (kandidat `gemini-3-flash-preview`; lihat catatan urutan combo di I9)
- [x] **Diagnosis `Hermes membalas HTTP 503`** (log `hermes gateway` dan tes `curl` ke `127.0.0.1:8642`)
- [x] **`hermes skills config`** untuk gaya `/agen` yang masih seperti Iris (matikan `iris-persona` dan `iris-auto` dulu, lalu bertahap yang lain)
- [x] **Tes v29:** balasan yang melanggar format `[emosi] jp ||| id` sudah diperbaiki
- [x] **Tes visual v28e:** pil status dan lampiran sejajar di atas bar input (uji `/agen 17 dikali 7`)
- [x] **Tes lampiran:** `/agent jelaskan gambarnya` dengan satu lampiran dan balasan panjang; bubble utuh, karakter tidak bergeser
- [x] **Tes benturan sisi layar:** Iris diseret ke tepi kanan, bubble "Ouch!" tampil utuh dan bersuara
- [x] **v31 (bubble di tepi atas layar):** saat ruang di atas kepala kurang dari 130 px, bubble pindah ke samping karakter; dinyatakan bisa di PC sungguhan
- [x] **v28c, banyak lampiran:** beberapa gambar sekaligus (`/agen jelaskan gambarnya`) berhasil pukul 13:07:55; karakter tidak bergeser, panel chat dan bar input tidak bertumpuk, Iris menjelaskan isi gambar dengan benar

## I2. Tier 0: tes yang masih terbuka

- [x] **Tes v30b: lulus** (dinyatakan aman oleh pemilik, 1 Nov malam). Kriteria awal:  Lulus kalau: baris pertama menyatakan "URL dari pengguna: berhasil dibuka" atau "gagal dibuka (alasan)"; butir dari agregator ditulis "lewat <situs>"; klaim satu-agregator diberi "(belum diverifikasi)"; laporan tidak terpotong di tengah kalimat. Riwayat v30 (1 Nov 12:04): gaya sudah netral, tapi atribusi memakai penerbit asli dengan URL agregator (`jekardah.com` empat kali), klaim besar belum diverifikasi, ada kata rusak ("akban", "alongside", "desember"), dan laporan terpotong di "ID pengguna, nama"
- [x] **Console DevTools:** sudah dibaca dan dites ulang; lulus 1 Nov malam, Console bersih (lihat I11)
- [ ] **v18:** gerak halus dan gerbang emosi ke klip. Gerak halus (pegas, crossfade) bisa diamati sekarang; gerbang emosi ke klip baru bisa dites penuh setelah paket klip VRMA masuk
- [x] **Tes v33:** lulus 1 Nov malam (popup Salin link dan tombol ⇅)
- [ ] **Tes v32:** bagian galat dan retry lulus; tinggal tes gambar normal setelah batas dikembalikan ke 90 detik (lihat I11)

## I3. Tier S: fitur berikutnya (v32 sudah ditulis, sisanya belum dikerjakan)

| Paket | Isi | Usaha |
|---|---|---|
| Galat model gambar (v32) | Pesan galat ringkas dan jelas, bukan teks kosong atau JSON mentah; batas baca gambar lebih pendek dengan retry sekali (lihat I9). **Galat dan retry lulus tes 1 Nov malam; tinggal tes gambar normal. Lihat I10 dan I11** | Kecil |
| Keamanan agen | **2a** konfirmasi di overlay untuk `/agen` yang berbau hapus atau pindah file: **selesai (v34, lulus tes di PC)**. **2b** cancel yang benar-benar menghentikan agen (perlu baca `api_server.py`): belum | Sedang |
| Persistensi | Riwayat obrolan disimpan ke file; `/status` menampilkan hasil `/health` (**`/status` selesai di v39, lulus tes 1 Nov malam; riwayat obrolan belum**) | Kecil |
| Aset gerak | Paket klip VRMA CC0 (greet, peace, dance, pegang tepi); kodenya ada, filenya belum | Kecil |
| Proaktif | Push dari Hermes ke overlay (cron atau hasil Telegram, lalu Iris bicara sendiri); auto-start bersama Windows | Sedang |

## I4. Tier A: setelah Tier S stabil

- Cadangan LLM lokal (Ollama) untuk saat 9Router mati
- Briefing pagi (cuaca, deadline `cek-elearning`, alarm hari ini)
- Seret dokumen (PDF, docx, txt) untuk diringkas lewat Hermes
- Terjemah cepat teks terpilih atau clipboard (mis. `Ctrl+Alt+T`)
- Tombol "Buka di Explorer" di kartu hasil agen (`revealFile` sudah ada di preload)
- Penjaga disk dan sistem (C: dan Z: sudah 93% penuh)
- Barge-in: mengetik atau bicara langsung memotong suara Iris
- Routing otomatis info terkini, saklar bawaan mati
- ~~Lip-sync dari mora VOICEVOX~~ (sudah ada sebagai v2; penyetelan opsional di Bagian J1)

## I5. Tier B dan C

**Tier B (nanti):** wake word atau hands-free; reaksi ke musik lalu menari; sapaan saat game aktif (opt-in, hanya nama proses); komentar layar berkala (Fase 6); suara Indonesia opsional; memori sinkron dengan Hermes; `/catat` dan `/todo`; statistik Pomodoro; jurnal mood harian; FPS dan hotkey di Pengaturan; tangan mengejar kursor.

**Tier C (dilewati):** installer atau packaging, multi-karakter, dashboard web, EMAGE, jalan-jalan di desktop, mode chibi, mode layar besar, sistem makan.

## I6. Sisi Hermes

1. Skill `cek-elearning` (tugas nyata pertama, alasan jembatan dibangun)
2. Kontrol media dan volume Windows
3. Pembersih disk aman (dry-run, lalu konfirmasi sebelum hapus)
4. Pencarian catatan kuliah di satu folder (RAG ringan)

## I7. Masih menggantung (dari H7)

- [x] Cek `python-dotenv` ada di `requirements.txt`: belum ada, baris `python-dotenv>=1.0` ditambahkan 1 Nov malam (venv yang berjalan sudah memilikinya karena `server.py` memuatnya; `requirements.txt` baru berguna untuk instalasi ulang)
- [ ] Cek apakah Z: tersinkron ke cloud
- [ ] Putuskan tes hapus `tes.txt`
- [ ] Konfirmasi suara Metan keluar saat menyampaikan hasil tugas, tanpa suara dobel dari sisi Hermes
- [ ] Pindahkan `/home/<user>/Downloads/tst` ke folder Download Windows
- [ ] Skill `cek-elearning` (juga tercatat di I6)

## I8. Urutan yang disarankan

1. Menutup Tier 0: tes v32 dan v33, tes ulang Console setelah v33b, lalu v18 (1 Nov malam: v33 dan v33b selesai, v32 tinggal gambar normal; sisa v18)
2. Keamanan agen: 2a konfirmasi di overlay untuk `/agen` yang berbau hapus, pindah, atau timpa file (bisa dikerjakan dari berkas yang ada); 2b cancel yang benar-benar menghentikan agen (butuh `api_server.py` milik Hermes) (1 Nov malam: 2a selesai sebagai v34 dan lulus tes; 2b belum)
3. Skill `cek-elearning` di sisi Hermes (tugas nyata pertama, sesudah Keamanan agen)
4. Persistensi (riwayat obrolan ke file, `/status` dengan hasil `/health`)
5. Aset gerak (klip VRMA; daftar klipnya diisi di `assets/animations/clips.json`), lalu Push dan auto-start

## I9. Catatan sesi 1 Nov (siang sampai sore)

### v31: bubble di samping karakter (`index.html`, `placeBubble`)

- Masalah (screenshot): Iris di tepi atas layar, bubble menutupi kepala dan badan karena kode lama hanya menyempitkan bubble sampai tinggi minimum 96 px lalu mendorongnya turun
- Perbaikan: kalau ruang di atas kepala kurang dari `SIDE_MIN_ABOVE` (130 px) dan salah satu sisi punya ruang minimal `SIDE_MIN_W` (150 px), bubble pindah ke sisi yang lebih lapang, sejajar kepala, tanpa ekor; kalau lebar sisi di bawah 220 px, baris Jepang disembunyikan (mode `narrow`)
- Konstanta penyetel: `SIDE_HALF` (66, setengah lebar badan), `SIDE_GAP` (10), `SIDE_MIN_ABOVE`, `SIDE_MIN_W`
- Hanya `index.html` yang berubah; `main.js` sudah mengirim batas layar (`vis`) lewat `pollCursor()`. Status: dinyatakan bisa

### v30b: atribusi jujur di `HERMES_SYSTEM` (`server.py`)

- Ditambahkan: ATRIBUSI ("lewat <nama situs>" untuk info dari agregator, klaim satu-agregator ditandai "(belum diverifikasi)"), STATUS URL PENGGUNA (baris pertama laporan), PANJANG (sekitar 2500 karakter)
- Temuan: laporan yang terpotong di "ID pengguna, nama" berasal dari `HERMES_MAX_CHARS = 3000` di `server.py`, bukan batas panel chat; naikkan angka itu kalau mau laporan lebih panjang
- Lolos `py_compile`; belum dites dengan Hermes asli

### Galat model gambar (12:57 sampai 13:07)

| Waktu | Kejadian | Penyebab |
|---|---|---|
| 12:57:35 | `9Router 503`: `cloudflare-ai/@cf/zai-org/glm-4.7-flash [502] fetch failed (ETIMEDOUT)` | Model di belakang combo `Iris` tidak menjawab dalam 30 detik |
| 13:00:59 sampai 13:03:59 | Galat dengan teks kosong: "9Router: (model gambar: Iris, cek NINEROUTER_VISION_MODEL)" | Tepat 180 detik: batas baca `read=180.0` di `server.py` baris 1345; galat timeout `httpx` tidak punya teks, jadi pesannya kosong |
| 13:07:55 | Berhasil, Iris menjelaskan isi gambar | Penyebab perubahan belum dicatat (apakah `NINEROUTER_VISION_MODEL` diubah belum diketahui) |

- `NINEROUTER_VISION_MODEL` kosong berarti model gambar = combo `Iris` yang sama dengan chat biasa, jadi gambar bisa jatuh ke model yang tidak mendukung gambar atau lambat (dugaan, belum terbukti)
- **Usulan v32 (belum dikerjakan):** (1) kalau teks galat kosong, tampilkan nama jenis galat; untuk timeout tampilkan "Model gambar tidak menjawab dalam 180 detik, coba lagi atau kurangi jumlah gambar"; (2) bubble dan suara Iris memakai satu kalimat ringkas, bukan JSON mentah; (3) opsional: batas baca gambar lebih pendek (mis. 60 detik) dengan retry sekali; (4) opsional: gambar dikecilkan (sisi terpanjang 1280 px) sebelum dikirim

### Daftar model yang dikirim pengguna (1 Nov, diduga urutan combo Iris di 9Router)

1. `nous/stepfun/step-3.7-flash:free`
2. `gemini/gemini-3.1-flash-lite-preview`
3. `nous/poolside/laguna-s-2.1:free`
4. `nous/poolside/laguna-xs-2.1:free`
5. `ocz/big-pickle`
6. `nous/upstage/solar-mini4:free`
7. `gemini/gemini-3-flash-preview`
8. `cf/@cf/zai-org/glm-4.7-flash`

Catatan: `gemini-3-flash-preview` (kandidat paling patuh format dari tes 9Router) ada di urutan 7, bukan pertama; `cf/@cf/zai-org/glm-4.7-flash` (urutan 8) adalah model yang timeout di galat 12:57. Label "urutan combo" adalah dugaan karena daftar dikirim tanpa keterangan; konfirmasi dulu sebelum mengubah urutan.

## I10. Catatan sesi 1 Nov (malam)

### Pil status tugas (v28f sampai v28h): riwayat dan keputusan akhir

- Keinginan pemilik akhirnya: **mode biasa** pil di kiri (jangan menimpa karakter, jangan menonjol di luar bar); **mode fokus** pil di tengah, tepat di atas garis petunjuk (`#barHint`), dan di atas bar kalau bar tampil
- Salah paham di jalan: v28f menengahkan pil di semua mode (menimpa karakter); v32b memindahkannya ke tengah jendela (salah, garis petunjuk berada di x = tepi kanan bar dikurangi 160 px, yaitu tengah karakter, bukan tengah jendela); v28g menggeser dock 24 px keluar dari bar (menonjol). Semuanya sudah diganti
- Hasil akhir di `index.html`: `#dock { left: 0 }` dengan pil maksimum 198 px (v28h); `#root.quiet #dock` ditengahkan pada garis (`left: calc(100% - 160px)`, `translateX(-50%)`, `bottom: calc(50% + 14px)`), dan `#root.quiet #barWrap.show #dock` memakai `left: 50%` serta `bottom: calc(100% + 8px)` supaya tidak menimpa bar (v32d)
- Dinyatakan sesuai oleh pemilik. Kalau rok lebar (gaun merah) masih menyentuh pil di mode biasa, pil bisa dipersempit atau dinaikkan

### v33: popup Salin link dan tombol memanjangkan kotak chat

- URL `http(s)://...` di pesan, balasan Iris, dan kartu "Hasil tugas" dibungkus `span.lnk`; kursor di atas link memunculkan pil "Salin link" (tetap tampil selama kursor di link atau pil; tanda baca penutup kalimat tidak ikut, kurung penutup dipertahankan kalau berpasangan di dalam URL)
- Tombol ⇅ di kepala panel chat memanjangkan kotak sampai 220 px (`CHAT_EXTRA` di `main.js`), dibatasi ruang di atas jendela; kurang dari 40 px = tombol berkedip ✕ dan tooltip menyarankan menggeser Iris turun. Menutup chat mengembalikan ukuran. Tombol disembunyikan kalau `main.js` atau `preload.js` yang terpasang belum memuat `setChatBig`
- Berkas: `index.html`, `main.js` (`setChatBig`, IPC `chat-big`), `preload.js` (`setChatBig`). Ketiganya harus diganti bersamaan, lalu Electron di-restart
- Catatan penomoran: dokumen ini sempat memakai "v32" untuk usulan galat model gambar, jadi popup link dan tombol chat dicatat sebagai **v33**

### v33b: Console dibersihkan

| Pesan | Penyebab | Perbaikan |
|---|---|---|
| Error 404 `assets/animations/clips.json` | Overlay mencari file daftar klip yang belum ada; fallback (daftar kosong) sudah jalan | Buat `assets/animations/clips.json` berisi `{}` |
| Warning `THREE.Clock` deprecated | `const clock = new THREE.Clock()` | Dibungkus `THREE.Timer` dengan antarmuka sama (`getDelta()`, `elapsedTime`); kembali ke Clock kalau Timer tidak ada |
| Warning `VRMLookAtQuaternionProxy not found` | Library membuat proxy otomatis sambil memperingatkan | `ensureLookAtProxy()` membuatnya sendiri sebelum `createVRMAnimationClip` (perilaku sama) |

Baris sehat di Console: kamera otomatis, 9 collider sentuhan, 14 ekspresi, `idle_loop.vrma` termuat. Kalau paket klip VRMA nanti dipasang, `clips.json` diisi daftar klip (format ada di komentar `loadClips` di `index.html`).

### v32 (`server.py`): galat model gambar

- `describe_llm_error()` mengganti teks kosong dan JSON mentah dengan satu kalimat: timeout ("Model gambar tidak menjawab dalam 90 detik, coba lagi atau kurangi jumlah gambar."), 503/5xx ("Model gambar di 9Router sedang gangguan (kode 503)..."), 401/403, 429, model menolak gambar (400/404/415/422), dan 9Router mati. Rincian teknis (nama model, badan galat) hanya dicetak di terminal. `/belajar` ikut memakainya
- Retry otomatis sekali untuk timeout, 429, dan 5xx, hanya kalau belum ada satu baris balasan pun yang keluar (supaya tidak dobel). Catatan: di `server.py` yang diunggah tidak ditemukan retry 503 dari paket Ketahanan; kalau di versi yang berjalan sudah ada, cek supaya tidak dobel
- Batas baca gambar 90 detik (`NINEROUTER_VISION_READ_TIMEOUT`), teks tetap 180 detik (`NINEROUTER_READ_TIMEOUT`). 90, bukan 60, karena fallback combo 9Router bisa makan 30 detik per model
- Belum dikerjakan: gambar dikecilkan (sisi terpanjang 1280 px) sebelum dikirim (butuh Pillow di server atau perubahan di overlay); dilihat dulu apakah timeout berkurang dengan perubahan di atas
- Tes: restart `server.py`; set `NINEROUTER_VISION_READ_TIMEOUT=3`, kirim gambar, cek bubble dan terminal; lalu tes gambar normal

### Rencana berikutnya: Keamanan agen

- **2a** konfirmasi di overlay: `/agen` atau `/agent` yang berbau hapus, pindah, timpa, atau format file ditahan di server; overlay menampilkan kartu "Iris mau menjalankan ini: ... Lanjut?" dengan tombol Jalankan dan Batal; batal = tidak ada yang dikirim ke Hermes; daftar kata pemicu bisa disetel lewat `.env`. Bisa dikerjakan dari `server.py`, `index.html`, dan `main.js` yang ada **Dikerjakan 1 Nov malam sebagai v34, lihat I11.**
- **2b** cancel yang benar-benar menghentikan agen: perlu membaca `api_server.py` Hermes (folder instalasi Hermes di WSL) untuk melihat apakah ada endpoint pembatalan; kalau tidak ada, pilihan menghentikan proses lebih berisiko dan perlu keputusan pemilik

### Berkas keluaran sesi ini

| Berkas | Isi |
|---|---|
| `index.html` | v28e sampai v28h (pil), v33, v33b; sudah memuat semua perubahan sesi ini |
| `main.js`, `preload.js` | v33 (`setChatBig`) |
| `server.py` | v32 |
| `assets/animations/clips.json` | `{}` (v33b) |
| `v32-index.patch`, `v32-main.patch`, `v32-preload.patch`, `v32-server.patch` | Diff terhadap berkas yang diunggah 1 Nov siang; dipakai kalau berkas lokal sudah diubah sendiri |
| `iris-v28-gabungan.patch` | Sudah memuat perbaikan pil, tapi hunk 5 (`placeBubble`, `visRect` ke `V`) sudah usang karena ditimpa v31; hapus hunk itu kalau patch dipakai lagi. Tidak perlu dijalankan lagi kalau `index.html` baru sudah dipasang |


## I11. Catatan sesi 1 Nov (malam, lanjutan): tes v32 sampai v33b dan v34

### Hasil tes

Dilaporkan pemilik. Bukti dari screenshot dan terminal disebut kalau ada.

| Item | Hasil | Bukti dan catatan |
|---|---|---|
| `assets/animations/clips.json` terpasang | **lulus** | Explorer: `clips.json`, 3 byte (isi `{}`), 1/11/2026 14:03, di samping `idle_loop.vrma` |
| Console DevTools (v33b) | **lulus** | Indikator "No issues". Lima baris sehat: `Kalibrasi lengan: D = -1` (`index.html` baris 822, informasi, bukan galat), `Kamera auto: tinggi model = 1.37 m, z = 2.20, y = 1.10`, `Collider sentuhan: 9 bola`, `VRM dimuat (prom). Ekspresi tersedia: Array(14)`, `Animasi idle VRMA aktif`. Tidak ada 404 `clips.json`, `THREE.Clock`, atau `VRMLookAtQuaternionProxy` |
| v33, popup "Salin link" | **lulus** | Pil muncul di atas link kartu "Hasil tugas"; hasil tempel `https://www.kompas.com` utuh |
| v33, tombol ⇅ | **lulus** | Dua screenshot (kotak pendek dan panjang), karakter tidak bergeser |
| v32, galat dan retry | **lulus** | Batas 3 detik, 4 gambar, pesan terkirim 14:17:13 dan bubble galat 14:17:21 (sekitar 8 detik, cocok dengan dua percobaan 3 detik plus jeda). Bubble: "Model gambar tidak menjawab dalam 3 detik, coba lagi atau kurangi jumlah gambar." Terminal: `[llm] ReadTimeout dari Iris: ''; mencoba sekali lagi`, lalu `[llm] galat final dari Iris: ReadTimeout: ''` |
| v32, gambar normal setelah batas dikembalikan | **belum dikonfirmasi** | `server.py` sudah dijalankan ulang (PID baru, tanpa variabel 3 detik); hasil kirim gambar normal belum dilaporkan |

Catatan praktis dari sesi ini:
- `$env:NINEROUTER_VISION_READ_TIMEOUT` hanya berlaku di jendela PowerShell tempat variabel itu diketik. Untuk kembali ke bawaan (90 detik), tutup jendela itu dan buka yang baru.
- `.venv\Scripts\activate` ditolak PowerShell (`running scripts is disabled`). Tidak perlu diperbaiki: jalankan langsung `.\.venv\Scripts\python.exe server.py` (variabel `$env:` tetap terbaca). Kalau tetap ingin `activate`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Jangan menjalankan `python server.py` tanpa venv: itu memakai Python sistem dan paket bisa tidak ada atau berbeda versi.
- Tes retry paling jelas lewat banyak gambar (lebih lambat dijawab model) atau batas sangat pendek.

### v34: konfirmasi `/agen` berbahaya (Keamanan agen 2a)

**Status: lulus tes di PC (1 Nov malam).** Pemilik menjalankan `/agen hapus file tes.txt di Download` dan menyatakannya bisa; rincian per langkah (Batal, Jalankan, tugas aman tanpa kartu) tidak dicatat. Sebelumnya sudah lolos uji simulasi. Berkas: `server.py` (sekitar 96 baris berubah), `index.html` (sekitar 52 baris berubah), `requirements.txt`. `main.js` dan `preload.js` tidak berubah.

**Cara kerja.** `/agen`, `/agent`, atau `/h` yang memuat kata pemicu tidak langsung diteruskan ke Hermes. Server menahannya dan mengirim kartu ke overlay: "Iris mau menjalankan ini. Lanjut?", berisi isi tugas dan kata yang terdeteksi, dengan tombol **Jalankan** dan **Batal**. Panel chat dibuka otomatis kalau tertutup, dan Iris mengingatkan lewat bubble. Hanya Jalankan yang meneruskan tugas. Tugas tanpa kata pemicu berjalan langsung seperti biasa.

**Protokol WebSocket.**

| Arah | Pesan |
|---|---|
| server ke overlay | `{"type":"confirm","id","task","hits","ttl"}` |
| overlay ke server | `{"type":"confirm","id","ok":true}` (Jalankan) atau `"ok":false` (Batal) |
| server ke overlay | `{"type":"confirm_end","id","state"}` dengan state `approved`, `cancelled`, `expired`, atau `replaced` |

**Aturan keamanan.**
- Satu konfirmasi tertunda per koneksi. `id` acak (8 heksadesimal), sekali pakai: balasan ulang atau `id` palsu ditolak (`expired`).
- Kedaluwarsa setelah `AGENT_CONFIRM_TTL` (bawaan 120 detik), dicek saat balasan tiba.
- Pesan baru, tombol Stop (`cancel`), atau `reset` menutup kartu yang menunggu; konfirmasi lama sesudahnya tidak berlaku.
- Tugas yang sedang berjalan tidak diganggu sebelum pengguna menyetujui.
- Pesan bergambar selalu jalur chat (tidak ke Hermes), jadi tidak dicek.

**Kata pemicu bawaan.** Indonesia: hapus, buang, pindah, memindah, timpa, menimpa, ganti nama, ubah nama, bersihkan, kosongkan, hilangkan, copot, uninstall, format ulang, format disk, format drive, format partisi, format flashdisk, format usb, matikan komputer, matikan pc, matikan laptop, restart komputer, restart pc, shutdown, reboot. Inggris dan terminal: delete, remove, erase, wipe, purge, shred, truncate, overwrite, rename, move, rm, rmdir, del, mv, kill, taskkill, sudo, chmod, chown, mkfs, diskpart, regedit.

**Pencocokan.** Awal kata harus utuh ("skill" tidak memicu "kill"); awalan me-, meng-, mem-, men-, meny-, di-, ter-, per-, pe-, ke-, se- dikenali ("menghapus", "dipindahkan", "memformat disk"); kata 4 huruf atau kurang harus utuh juga di belakang ("delay" tidak memicu "del", "movement" tidak memicu "move").

**Setelan `.env`.**

| Variabel | Fungsi |
|---|---|
| `AGENT_CONFIRM=0` | Matikan fitur (bawaan aktif) |
| `AGENT_DANGER_EXTRA=kata1,kata2` | Tambah kata ke daftar bawaan |
| `AGENT_DANGER_WORDS=kata1,kata2` | Ganti seluruh daftar bawaan |
| `AGENT_CONFIRM_TTL=120` | Batas waktu menunggu klik (detik) |

`/health` kini menampilkan `agent_confirm: aktif (N kata pemicu)` atau `MATI`.

**Pengujian di luar PC (dilakukan sebelum tes di PC).** `py_compile` dan `node --check` lolos. 22 kasus pencocokan kata, 0 gagal. Simulasi alur WebSocket dengan klien tiruan, 10 skenario: setuju (tugas jalan sekali), batal (tidak ada tugas), tugas aman (jalan tanpa kartu), `id` palsu (ditolak), balasan dipakai dua kali (jalan sekali), pesan baru menutup kartu, Stop menutup kartu dan konfirmasi sesudahnya ditolak, kedaluwarsa (tidak jalan), `/h` dan `/agent` ikut dicek, `AGENT_CONFIRM=0` (jalan langsung). Kode kartu di overlay diuji dengan DOM tiruan: kartu terbentuk, tombol terkirim dan menutup kartu, kartu baru menutup kartu lama, `confirm_end` untuk `id` tak dikenal aman.

**Langkah tes di PC (yang dicoba pemilik: langkah 2; sisanya tidak dilaporkan).**
1. Ganti `server.py` dan `index.html`, restart `server.py` dan Electron; `/health` harus menampilkan `agent_confirm: aktif`.
2. `/agen hapus file tes.txt di Download`: kartu kuning muncul. Klik **Batal**: terminal mencetak `dibatalkan pengguna (tidak dikirim ke Hermes)`, tidak ada status "Memproses tugas".
3. Kirim lagi, klik **Jalankan**: tugas berjalan seperti biasa, terminal mencetak `disetujui pengguna, diteruskan ke Hermes`.
4. `/agen cari berita terbaru dari kompas`: tidak boleh ada kartu.
5. Opsional: Iris di tepi layar (mengintip) atau chat tertutup, lalu kirim perintah berbahaya; panel harus terbuka dan kartu terlihat.

**Batasan yang perlu diingat.**
- Ini jaring pengaman untuk salah ketik dan salah paham, bukan sandbox. Permintaan berbahaya yang tidak memuat kata pemicu tetap lolos.
- Bisa ada konfirmasi yang sebenarnya tidak perlu (mis. "hapus duplikat di daftar ini"). Longgarkan lewat `AGENT_DANGER_WORDS`.
- 2b (cancel yang benar-benar menghentikan agen di sisi Hermes) belum dikerjakan; Batal di kartu hanya mencegah tugas dikirim.

### Catatan konsistensi dokumen (perlu konfirmasi pemilik)

- Tabel "Status uji terbaru" masih menulis v29 dan v28c "belum dites", sedangkan Bagian I1 sudah mencatat keduanya dinyatakan aman (v28c dengan banyak lampiran berhasil pukul 13:07:55). Belum diubah di sini karena belum dikonfirmasi; kalau memang lulus, centang dan ubah barisnya.

### Berkas keluaran sesi ini (lanjutan)

| Berkas | Isi |
|---|---|
| `server.py` | v34: konfirmasi `/agen` berbahaya, `agent_confirm` di `/health`; memuat juga v32 |
| `index.html` | v34: kartu konfirmasi; memuat juga v28e sampai v28h, v33, v33b |
| `requirements.txt` | Ditambah `python-dotenv>=1.0` dan komentar kredit |
| `main.js`, `preload.js` | Tidak berubah (v33 `setChatBig`) |

### Urutan berikutnya

1. Tes gambar normal (v32); konfirmasi juga langkah v34 yang belum dilaporkan (Batal, Jalankan, tugas aman tanpa kartu) kalau mau lengkap.
2. Skill `cek-elearning` di sisi Hermes (tugas nyata pertama).
3. Persistensi (riwayat obrolan ke file, `/status` dengan hasil `/health`).
4. Aset gerak (paket klip VRMA; ini juga membuka tes penuh v18), lalu Push dan auto-start.
5. 2b: cancel yang benar-benar menghentikan agen (butuh membaca `api_server.py` Hermes; kalau tidak ada endpoint pembatalan, perlu keputusan pemilik).

## I12. Catatan sesi 1 Nov (lanjutan): v37 pilihan bernomor dan gema perintah

**Masalah yang dilaporkan (screenshot).** `/baju` menampilkan daftar bernomor, lalu pengguna mengetik `3`. Angka itu dikirim ke model sebagai obrolan biasa, dan Iris menjawab "Eh, angka 3? Ada yang kamu lupa ya, Rover?". Selain itu, perintah `/baju` yang diketik tidak muncul sebagai gelembung di chat (perintah lokal tidak pernah dicatat lewat `logUser`).

### v37 (hanya `index.html`)

- **Pilihan menunggu (`pendingChoice`).** Fungsi `offerChoices(items)` dipanggil oleh perintah yang menampilkan daftar bernomor. Tiap item berisi `run()` dan, kalau perlu, `key` (id atau nama huruf kecil). Fungsi `takeChoice(text)` dipanggil di handler Enter sebelum perintah `/` dan sebelum kirim ke model.
- **Aturan.**
  - Balasan berupa angka dalam rentang: item dijalankan, pesan tidak dikirim ke model.
  - Angka di luar rentang: muncul galat "Nomor N tidak ada (pilih 1-M)", daftar tetap menunggu.
  - Teks lain: pilihan dibatalkan dan teks diproses seperti biasa (obrolan).
  - Perintah `/` baru membatalkan pilihan lama (`slashCmd` mengosongkan `pendingChoice` di awal; daftar baru memasangnya lagi).
  - Kedaluwarsa 2 menit.
- **Perintah yang sudah memakainya.**
  - `/baju` (tanpa argumen): angka, id, atau nama baju langsung mengganti baju lewat `changeOutfit`.
  - `/alarm` (daftar): angka membatalkan alarm itu lewat `cancelAlarm`.
- **Gema perintah.** Perintah `/...` yang diketik kini dicatat sebagai gelembung pengguna sebelum dijalankan. Kalau `slashCmd` mengembalikan `false` (perintah diteruskan ke server, mis. `/agen`), gelembung gema dihapus lalu pesan dicatat seperti biasa, jadi tidak muncul dua kali.
- **Menambah perintah baru dengan pilihan.** Cetak daftarnya, lalu panggil `offerChoices([{ key: [...], run: () => ... }, ...])` dengan urutan sama seperti nomor di daftar.

### v37b: soal `/belajar` menampilkan kalimatnya di chat (`server.py`)

Laporan (screenshot): chat hanya menulis "Apa artinya kalimat ini? (ketik menyerah ...)" tanpa kalimatnya, karena kalimat Jepang hanya diucapkan dan tampil di bubble yang cepat hilang. Perbaikan: teks arti pada baris soal kini diawali `「<kalimat Jepang>」`, sehingga kalimat tertulis permanen di chat. Suara dan jawaban yang benar tidak berubah. **Lulus tes (1 Nov, screenshot pemilik):** chat menampilkan "「すしが好きです。」 Apa artinya kalimat ini? (ketik menyerah kalau mau lihat jawabannya)".

### v37c: galat `/pantau` tidak lagi muncul tiba-tiba (`server.py`)

Laporan (screenshot): bubble merah "Model gambar tidak menjawab dalam 90 detik, coba lagi atau kurangi jumlah gambar." muncul sendiri. Penyebab: komentar layar otomatis (`/pantau`, tanda 👁) mengirim screenshot ke model gambar, model itu timeout, dan galatnya diteruskan ke overlay seperti galat pesan biasa (galat memang selalu tampil, bahkan saat Iris mengintip). Perbaikan: untuk permintaan `auto`, galat hanya dicetak di terminal (`[llm] galat final ...`) dan tidak dikirim ke overlay. Galat untuk pesan yang kamu kirim sendiri tetap tampil. Lulus tes (1 Nov, dinyatakan pemilik). Kalau timeout sering terjadi, periksa model gambar di 9Router atau `VISION_READ_TIMEOUT`.

### v37d: Iris tiba-tiba ngilang dan laptop lag (`index.html`, `main.js`)

Laporan: kadang Iris hilang sendiri lalu laptop jadi lag. Temuan di kode (penyebab pastinya belum terbukti, tapi ketiganya nyata):
- Tidak ada penanganan renderer crash. Kalau halaman overlay mati atau macet, jendela transparan tetap ada tapi kosong, jadi karakter "ngilang".
- Tidak ada penanganan `webglcontextlost`. Penggambaran dibuat dengan resolusi 2x sampai 3x dan antialias; kalau GPU kehabisan memori atau driver reset, konteks WebGL hilang dan karakter lenyap.
- `voiceCache` (audio base64 tiap kalimat lokal, fun fact, soal `/belajar`) tidak punya batas, dan isi panel chat (termasuk gambar screenshot) juga tidak dibatasi, sehingga memori membengkak makin lama overlay jalan.

Perbaikan:
- `main.js`: `render-process-gone` memuat ulang halaman otomatis (maksimal 3 kali per 5 menit), `unresponsive` memuat ulang setelah 8 detik kalau masih macet, `child-process-gone` (mis. proses GPU) dicatat di terminal.
- `index.html`: `webglcontextlost` dicegah supaya bisa pulih sendiri, dan halaman dimuat ulang kalau tidak pulih dalam 4 detik.
- `index.html`: `voiceCache` dibatasi 60 entri (yang paling lama tak dipakai dibuang), panel chat dibatasi 300 pesan terakhir (ekspor percakapan hanya memuat yang masih ada di panel).
- Belum diubah: `setPixelRatio` minimal 2x (supaya tajam). Kalau laptop masih berat, opsi berikutnya menurunkannya ke 1.5x atau menjadikannya pengaturan.

**Lulus tes (1 Nov, dinyatakan pemilik); karena ngilang terjadi sesekali, pantau beberapa hari.** Kalau Iris ngilang lagi, lihat terminal Electron: baris `Renderer mati: ...` atau `WebGL context hilang` menunjukkan sebabnya.

**Data pengamatan (screenshot Task Manager, 1 Nov, 18:51):** memori sistem terpakai 86%. Electron (5 proses) memakai sekitar 942 MB, dan Chrome (14 proses) sekitar 1,1 GB. Memori hampir penuh itu bisa ikut membuat laptop lag, apa pun yang dilakukan overlay. Kalau Iris ngilang atau lag lagi, bandingkan angka Electron di Task Manager (apakah terus naik dari waktu ke waktu) sebelum menyimpulkan penyebabnya. Batas cache suara dan panel chat (v37d) dibuat untuk menahan kenaikan itu.

### Belum dicakup

- `/memori` dan `/lupa <no>` diproses di `server.py` (v12), jadi belum ikut mekanisme ini. Sengaja ditunda karena memilih nomor di sana menghapus ingatan; kalau dikerjakan, beri satu langkah konfirmasi.
- (Dikerjakan setelahnya, lulus tes 1 Nov) `/lokal daftar` kini menomori daftar aplikasi; mengetik nomor atau nama aplikasi menjalankan `buka <aplikasi>` lewat `tryLocalCommand`, jadi tetap hanya aplikasi daftar putih dari `main.js`. Alias dengan program sama (mis. `chrome`, `google chrome`, `krom`) digabung jadi satu baris; `main.js` kini mengirim juga `map` (nama ke program) pada `local-cmd` `apps`. Daftar bawaan `DEFAULT_LOCAL_APPS` dipersingkat jadi 3 aplikasi dulu: chrome, notepad, task manager (edge, kalkulator, explorer dihapus dari bawaan; bisa ditambah lewat `local-apps.json`).

### Catatan konsistensi dokumen

- `index.html` yang diunggah sudah memuat v35 (perintah suara lokal `/lokal`, handler `local-cmd` di `main.js`, `localCmd` di `preload.js`) dan v36 (menu perintah `/` bergaya Telegram dari daftar `HELP`). Keduanya belum dicatat di dokumen ini; perlu bagian tersendiri kalau mau dilengkapi.

### Berkas keluaran sesi ini

| Berkas | Isi |
|---|---|
| `index.html` | v37: `offerChoices` dan `takeChoice`, gema perintah `/`, `/baju`, `/alarm`, dan `/lokal daftar` bisa dijawab angka; memuat juga v34 sampai v36 |
| `main.js` | v37: `local-cmd` `apps` menambah `map` (satu baris di handler) |
| `server.py` | v37: satu baris log diagnosa `pesan masuk: ...` di terminal untuk tiap pesan pengguna yang sampai ke server (dipakai melacak apakah angka pilihan ikut terkirim ke model) |
| `preload.js` | Tidak berubah |

### Urutan berikutnya

1. Pantau v37d beberapa hari (Iris ngilang sesekali); v37 sampai v37c sudah lulus.
2. Putuskan apakah `/memori` dan `/lupa` ikut dengan konfirmasi.
3. Dokumentasikan v35 dan v36 di bagian tersendiri.
4. Ide lanjutan: pilihan jadi tombol klik, pilihan lewat suara, `/belajar` dengan pilihan topik, autocomplete argumen di menu `/`.

---

## I13. Catatan sesi 1 Nov (malam, lanjutan): v38 tema musim, v38b setengah badan, v39 pil status koneksi

### Ringkasan

| Paket | Berkas | Status |
|---|---|---|
| v38 tema warna (Iris bawaan + empat musim + Otomatis, `/tema`, efek jatuh) | `index.html` | **Dinyatakan sudah bisa (pemilik, 1 Nov)** |
| v38b setengah badan tidak lagi "patah" (bawah memudar) | `index.html` | Ditulis, belum diuji eksplisit (karakter di screenshot terakhir tampil tubuh penuh) |
| v39 pil status koneksi (`V 9 H`), `/status`, titik bar hijau, kuning, merah | `index.html`, `server.py` | **Lulus tes (screenshot 1 Nov malam)** |
| v39b, v39c, v39d diagnosa token `/ws` dan log penolakan | `server.py`, `main.js` | Lulus tes, log terminal bersih |

### v38: tema warna (hanya `index.html`)

**Permintaan (berurutan).** (1) Warna tema disesuaikan dengan karakter (rambut biru, blazer navy). (2) Tema hanya bawaan ditambah musim. (3) "Tiap tema tidak ada perubahan yang signifikan", jadi perubahan diperbesar. (4) Warna karakter ikut berubah dan terlihat aneh, jadi dihapus.

**Temuan.** Gelembung ucapan (`#bubble`) berwarna tetap (`#262d48` sampai `#151a2b`) dan tidak ikut tema, padahal itu bagian yang paling sering terlihat. Warna teal dan latar panel juga tertulis langsung di sekitar 30 tempat CSS.

**Implementasi.**
- Warna tertulis langsung diganti variabel CSS: `--acc-rgb`, `--acc2-rgb`, `--pt` dan `--pb` (atas dan bawah gradasi panel), `--panel`, `--panel-2`, `--bub1`, `--bub2`, `--bubsh`, `--rad`. Tema dipasang lewat `html[data-theme="..."]`.
- `SET.theme` disimpan di `localStorage`, dipasang sedini mungkin supaya tidak berkedip. Pemilih **Tema** ada di Pengaturan (di bawah **Baju**) dan perintah `/tema` (daftar bernomor, memakai `offerChoices`; nama, alias, atau nomor).
- Tambah tema = satu baris di `THEMES` (JS) + satu blok `html[data-theme]` (CSS).

| Tema | Panel | Aksen | Efek jatuh | Bentuk dan huruf |
|---|---|---|---|---|
| **Iris (bawaan)** | navy blazer | biru rambut, emas kancing | tidak ada | bawaan |
| **Musim semi** | plum-pink | pink + hijau muda | 🌸 🌷 | sudut 24 px |
| **Musim panas** | biru laut | cyan + kuning | ✦ ✧ naik dari bawah | sudut 28 px, huruf bubble tebal |
| **Musim gugur** | cokelat maple | oranye + emas | 🍁 🍂 | sudut 12 px, huruf bubble serif (Georgia) |
| **Musim dingin** | slate es | biru es + putih | ❄ ❅ ❆ | sudut 8 px, huruf bubble tipis |
| **Otomatis** | mengikuti bulan (musim belahan utara): Mar sampai Mei semi, Jun sampai Agu panas, Sep sampai Nov gugur, Des sampai Feb dingin; dihitung saat overlay dibuka atau tema diganti | | | |

- Efek jatuh: elemen `#season` di dalam `#root` (`z-index: -1`, di belakang karakter, tidak menghalangi klik), 11 sampai 16 elemen CSS. Hilang di mode fokus dan saat mengintip di tepi (`quiet`, `peek`). Saklar **Efek musim** di Pengaturan (`SET.seasonFx`, bawaan hidup).
- Selain Iris: garis dan cahaya bar input selalu berwarna aksen, pinggiran panel (`.pop`, `#menu`, `#log`, `#bubble`) berwarna aksen dan memakai `--rad`.
- **Dicoba lalu dihapus: tint cahaya pada karakter** (warna sinar dan ambien per musim). Karakter terlihat aneh. Jangan diulang; perubahan hanya di panel dan efek di sekitarnya.
- **Dihapus atas permintaan:** tema Teal klasik, Sakura, Matcha (Sakura menjadi Musim semi).
- **Belum ikut tema:** ekspor percakapan HTML (`EXPORT_CSS`, masih teal), warna per emosi di bubble (`--h1` sampai `--h3`, `--emo`), garis petunjuk biru. Tema terang belum ada (semua panel dirancang gelap).

### v38b: setengah badan tidak lagi "patah" (`index.html`)

**Laporan (screenshot).** Di mode setengah badan, rok terpotong garis lurus tepat di tepi bawah kanvas, tampak "patah".
**Penyebab.** Kamera setengah badan (`CAM.bottom`) sengaja memotong karakter di tinggi tertentu, jatuh di tengah rok.
**Perbaikan.** Kelas `half` pada `#root` mengikuti `SET.fullBody === false` (di `applyBody()` dan saat awal). Aturan `#root.half #char canvas` memberi `mask-image` gradasi: penuh sampai 78%, lalu memudar sampai transparan. Ubah angka 78% untuk mengatur ketinggian pudarnya. Mode tubuh penuh tidak disentuh.
**Belum diuji eksplisit.** Kalau masih patah di tubuh penuh, penyebabnya mungkin lain (karakter turun saat mengintip atau duduk).

### v39: pil status koneksi (`index.html`, `server.py`)

**Desain.** Overlay hanya boleh WebSocket ke server (CSP `connect-src`), jadi `fetch('/health')` dari overlay diblokir. Server yang mendorong status lewat WS yang sudah ada.
- `server.py`: `health_probe()` mengecek VOICEVOX, 9Router, Hermes **paralel** (maksimal 5 detik, sebelumnya berurutan sampai 15 detik). `health_states()`: HTTP 2xx `ok`, 4xx `warn`, 5xx atau ERROR `down`. Dikirim `{"type":"health", voicevox, ninerouter, hermes, detail}` saat tersambung, tiap `IRIS_HEALTH_SEC` detik (bawaan 45, minimal 15), dan saat overlay meminta (`{"type":"health"}`). `/health` tetap ada dan ditambah `state`.
- `index.html`: titik di bar hijau (semua aktif), kuning (ada layanan bermasalah), merah (server tidak terhubung). Pil `V 9 H` (V = VOICEVOX, 9 = 9Router, H = Hermes) di `#dock` muncul hanya bila ada masalah, atau selalu lewat **Pil koneksi selalu** di Pengaturan (`SET.connPill`). `/status`, klik pil, atau klik titik: detail di chat (✓, !, ✕ plus versi atau kode HTTP). Saat sebuah layanan berubah keadaan, satu baris masuk ke log chat (Iris tidak bicara karena suaranya butuh VOICEVOX). Pil hilang di mode fokus dan saat mengintip.
- Sebelum v39 yang ada di bar hanya titik hijau atau merah (tersambung atau tidak ke `server.py`), tanpa membedakan ketiga layanan. Di H8 dan I1 butir ini tercatat sebagai pil status koneksi; yang dimaksud selesai di sini adalah pil per layanan.

**Bug v39 awal dan pelajarannya.** Dua baris pemasangan (`gid('conn').addEventListener(...)` dan `bind('sConnPill', ...)`) kuletakkan di bagian atas script, padahal `gid` dan `saveSet` (keduanya `const`) baru didefinisikan di baris 2456 dan 2459. Hasilnya `ReferenceError` (TDZ), script berhenti sebelum `connect()` di akhir, dan overlay tidak pernah mencoba nyambung (titik merah). Dari terminal server terlihat seperti masalah token karena hanya penolakan dari tab browser yang tercetak. Perbaikan: dua baris dipindah ke setelah `bind('sSeasonFx', ...)`. `node --check` **tidak** menangkap kesalahan jenis ini. Dibuat pengecek sementara (parser `acorn`) yang mencari pemakaian `const`, `let`, atau `class` tingkat atas sebelum deklarasinya; hasil pada `index.html` bersih, dan pengecek diuji pada salinan yang sengaja dirusak (menangkap `gid`). Skripnya tidak disertakan; bisa dibuat ulang. **Aturan untuk paket berikutnya:** kode yang berjalan langsung di tingkat atas script dan memakai `gid`, `bind`, `saveSet`, harus diletakkan setelah baris 2456 (blok `bind(...)` di sekitar baris 2754 sampai 2780).

### v39b, v39c, v39d: diagnosa token dan log penolakan (`server.py`, `main.js`)

- **Fakta yang terbukti dari log.** Overlay mengirim Origin `http://localhost:8765` (`SERVER_ORIGIN` di `main.js`). Penolakan ber-Origin `http://127.0.0.1:8765` berasal dari tab browser halaman tes ("AI Companion - Tes Fase 1"), yang tidak bisa mengirim header token, jadi **selalu ditolak saat `COMPANION_TOKEN` aktif**. Itu perilaku yang memang diharapkan, bukan kerusakan.
- `server.py` mencetak saat start: file `.env` yang dipakai dan `Token /ws server: N karakter, sidik xxxxxx` (6 hex SHA-256; isi token tidak pernah dicetak). `/health` ikut menampilkan panjang dan sidik.
- Saat koneksi ditolak: alasan (header tidak ada atau salah, plus sidiknya), Origin, dan petunjuk. Dibatasi sekali per 30 detik **per Origin**, supaya penolakan overlay tidak tertutup penolakan browser.
- `main.js` mencetak sidik token dan sumbernya (`environment` atau path `.env`) serta `process.platform`, dan mencetak sebab 403 sendiri (tidak ada token, atau token beda dengan sidiknya) maksimal sekali per 30 detik.
- **v39d:** filter log uvicorn (`log_config=_LOG_CONFIG`) menyembunyikan baris `"WebSocket /ws" 403` dan `connection rejected (403`, supaya tab browser lama tidak membanjiri terminal. Baris `/ws ditolak: ...` tetap tercetak. Halaman `/` saat token aktif menampilkan penjelasan singkat (bukan `test_client.html`); token kosong = halaman tes lama.
- **Lingkungan pemilik.** `server.py` dijalankan dari Windows PowerShell (`.venv\Scripts\python.exe`), `.env` di `C:\Users\<user>\.env`; token server 43 karakter, sidik `<hex>`. Kalau Electron dijalankan dari WSL, `os.homedir()` berbeda dan `.env` Windows tidak terbaca (hipotesis awal; tidak terjadi di sesi ini).

### Hasil tes (screenshot dan log pemilik, 1 Nov malam)

- Overlay tersambung (`"WebSocket /ws" [accepted]`, `connection open`), Iris membalas, titik di bar hijau.
- `/status`: VOICEVOX aktif (0.25.2), **9Router tidak merespons** (`ConnectError: All connection attempts failed`), Hermes aktif (HTTP 200, kunci terisi). Beberapa saat kemudian pil melaporkan "9Router aktif lagi" (sempat belum menyala atau tidak terjangkau dari Windows); balasan Iris normal sesudahnya.
- `/agen kalo gunain gatsby itu wajib pake sisir ya?` selesai dalam 47,0 detik, hasil tampil di kartu Hasil tugas. `/agen jelaskan sejarah 3 kingdom` dimulai normal.
- Terminal server bersih dari banjir 403 setelah v39d.

### Berkas keluaran sesi ini

| Berkas | Isi |
|---|---|
| `index.html` | v38 tema musim + efek jatuh, v38b setengah badan memudar, v39 pil status koneksi dan `/status` (memuat juga v32 sampai v37d) |
| `server.py` | v39 `health_probe`, push `health` lewat WS, `/health` paralel; v39b diagnosa token; v39c log per Origin; v39d filter 403 dan halaman `/` |
| `main.js` | v39b dan v39c: sidik token, sumber, dan laporan 403 di terminal Electron |
| `preload.js` | Tidak berubah |

### Catatan konsistensi

- Di tengah sesi ada `index.html` lama yang terunggah (baru sampai v31, tanpa v32 sampai v37). Versi yang benar adalah yang memuat v37d dan seterusnya; cek baris `data-theme` dan `connRender` di berkas untuk memastikan memakai v39.
- Di bagian awal dokumen, "Terakhir diperbarui" kini menunjuk ke Bagian I13.

### Belum dicakup dan urutan berikutnya

1. Tes tampilan setengah badan (v38b) bila dipakai mode itu.
2. Ekspor percakapan HTML ikut tema (`EXPORT_CSS` masih teal); tema terang bila dibutuhkan.
3. Pantau 9Router: pastikan `NINEROUTER_URL` terjangkau dari Windows bila `server.py` dijalankan dari PowerShell (di WSL tidak masalah).
4. Pilihan berikutnya dari tierlist: **mode jangan ganggu otomatis** (Iris diam dan efek jatuh berhenti saat ada aplikasi fullscreen atau game), **baju otomatis ikut musim** (`/baju` dan tema Otomatis sudah ada), anggaran gangguan global (batas ucapan spontan per jam), `/selftest`, tema hari spesial (Tahun Baru, Ramadan dan Lebaran, 17 Agustus).
5. Dari daftar lama yang masih menggantung: paket klip VRMA, riwayat obrolan persisten, push dari Hermes dan auto-start, `/memori` dan `/lupa` dengan konfirmasi, dokumentasi v35 dan v36.

---

# Bagian J: Riset Fitur Baru, v40 (2 Nov 2026)

**by: KangJiho**

Disusun dari sesi 2 Nov 2026. Riset membandingkan Iris dengan Open-LLM-VTuber, AIRI, dan Amica. Aturan sama seperti Bagian GitHub: **kode tidak disalin**, hanya ide dan teknik yang diambil. Sumber: https://github.com/Open-LLM-VTuber/Open-LLM-VTuber (dokumentasi https://docs.llmvtuber.com), https://github.com/moeru-ai/airi, https://github.com/semperai/amica.

## J1. Koreksi: lip-sync berbasis mora sudah ada

Sempat diusulkan sebagai fitur baru, ternyata **sudah terpasang sebagai Lip-sync v2** (Fase 4 di Bagian A sudah mencatatnya; komentar `// Lip-sync v1` di sekitar baris 724 `index.html` hanya usang).

- `server.py`: `extract_moras()` membuat timeline `{vowel, start, end}` dari `audio_query` **setelah** `apply_voice_style()`, jadi `speedScale` per emosi ikut terhitung.
- `index.html`: `updateVisemes()` memetakan a/i/u/e/o ke `aa/ih/ou/ee/oh`, vokal tak bersuara (huruf besar) lebih kecil, `N`/`cl`/`pau` menutup mulut; cadangan ke volume, lalu goyang prosedural.
- Penyetelan opsional yang belum dikerjakan: (1) `LIP_OFFSET` ke sekitar -0.03 sampai -0.06 detik kalau mulut terasa terlambat; (2) campur sedikit vokal berikutnya (sekitar 40 ms sebelum mora tiba); (3) `extract_moras` memperhitungkan `pauseLengthScale` (sekarang aman karena nilainya 1.0); (4) rapikan komentar yang nyasar di baris `LIP_GAIN` dan komentar "v1".

## J2. Tier list hasil riset (disesuaikan dengan kode Iris)

Kolom "Yang sudah ada di Iris" ditulis setelah membaca `server.py`, `index.html`, `main.js`, `preload.js`.

| # | Fitur | Tier | Sumber ide | Yang sudah ada di Iris | Status |
|---|---|---|---|---|---|
| 1 | Barge-in (Iris diam saat kamu bicara) | S | Open-LLM-VTuber; library voice-agent | `send({type:'cancel'})`, pembatalan di server, mic dengan `echoCancellation: true`; mic masih saklar mulai-berhenti lewat `MediaRecorder` (v14) | belum |
| 2 | Pembatalan tugas di sisi Hermes (2b) | S | (sudah tercatat di G4, I3, I8) | Tombol Stop hanya memutus sisi Iris | belum |
| 3 | Memori otomatis dengan recall | S | AIRI (RAG), Open-LLM-VTuber (Letta) | `/ingat` manual (v12), tangkapan nama game otomatis (`note_user_facts`, v16c) | belum |
| 4 | Proaktif dengan pemicu yang bisa diatur | A | fork AIRI (heartbeat), Open-LLM-VTuber | Pengingat istirahat (v15), fun fact acak (v26/v27), alarm; push dari Hermes tercatat di H1 | belum |
| 5 | Kontrol media dan aplikasi lewat `local-cmd` | A | (ide sendiri) | `/lokal` dengan daftar putih aplikasi (v35); belum ada play/pause/volume | belum |
| 6 | Pikiran batin Iris (`[thought]`) | A | Open-LLM-VTuber | - | **selesai v40, belum dites** |
| 7 | Mode belajar Jepang: furigana/romaji, SRS, shadowing | A | (ide sendiri) | `/belajar` (v13) sudah ada soal-jawab; STT (v14) bisa `IRIS_STT_LANG=ja`; sisa: furigana/romaji, pengulangan berjarak, penilaian pelafalan | sebagian |
| 8 | Emosi lebih banyak | B | Amica (14 emosi) | 6 emosi lama | belum |
| 9 | Jembatan Telegram/Discord ke server Iris | B | AIRI | Hermes sudah punya kanal Telegram (Bagian B); yang baru hanya mengobrol dengan Iris dari HP. Wajib whitelist ID akun, jangan sebelum 2b | belum |
| 10 | Wake word hands-free (openWakeWord + Silero) | B | proyek voice-agent | Push-to-talk `Ctrl+Alt+G` | belum |
| 11 | MCP langsung ke Iris | B | Open-LLM-VTuber | Hermes sudah jadi lapisan tool; berguna hanya untuk tool cepat | belum |
| 12 | Ekspresi wajah khusus model (pipi merah, mata mengantuk) | B | Amica | 14 ekspresi model | belum |
| 13 | Cadangan model offline (Ollama), pengemasan | B | Open-LLM-VTuber | (sudah tercatat di H2 dan H4) | belum |
| 14 | Main game (Minecraft/Factorio) | C | AIRI | - | dilewati (proyek besar, tidak sejalan dengan overlay) |
| 15 | Aktivitas otonom acak ala Amica Life | C | Amica | - | dilewati (berisiko mengulang masalah gerakan creepy) |

Catatan:
- **Barge-in:** tantangan utamanya gema. Dari riset: filter pencocokan kata (bandingkan transkrip dengan kalimat yang sedang diucapkan) lebih tahan gema daripada VAD energi; library lain mengakui bahwa tanpa headphone VAD memicu dari suara agen sendiri. Rancangan awal: VAD (mis. Silero via `@ricky0123/vad-web`) aktif saat Iris bicara, wajib suara berlanjut sekian ratus milidetik, lalu kirim `cancel`.
- **Memori otomatis (versi ringan):** di akhir sesi model meringkas 3-5 fakta baru ke `iris-memory.json`; `memory_block()` memilih yang relevan; kamu konfirmasi atau hapus lewat `/memori`. Embedding ditunda. Aturan `_SECRET_RE` (menolak kata sandi dan sejenisnya) tetap berlaku.
- **Proaktif:** tetap tanpa membaca judul jendela (prinsip privasi v15). Pemicu yang diusulkan: diam X menit, jam tertentu, tugas Hermes selesai, dengan cooldown dan jam tenang.

## J3. v40: pikiran batin Iris (`server.py`, `index.html`)

**Status: kode ditulis, lolos `py_compile` dan `node --check`; belum dites di PC dengan 9Router dan VOICEVOX asli.**

**Cara kerja.**
- Iris boleh menulis satu baris `[thought] bisikan hati` di awal balasan (sekitar 1 dari 3 giliran). Baris ini tidak disuarakan, tidak masuk riwayat, dan tidak lewat `repair_line`.
- `server.py`: `THOUGHTS_ON`, `THOUGHT_RE`, `THOUGHT_RULES` (ditambahkan ke system prompt hanya di `handle_user_text` untuk pesan non-otomatis), `clean_thought()` (ambil bagian setelah `|||` kalau ada, buang kurung dan kutip, maksimal 120 karakter, buang yang cocok `_SECRET_RE`). `handle_user_text` mencegat baris thought, menyimpannya, dan menempelkannya ke segmen ucapan berikutnya lewat `process_line(..., thought)`; maksimal satu per giliran. Pengingat format di akhir pesan pengguna ikut menyebut baris opsional ini.
- Protokol: pesan `segment` mendapat field opsional `thought` (string); tanpa pikiran, field itu tidak ada, jadi klien lama tidak terpengaruh.
- `index.html`: elemen `.th` di dalam `.btext` sebelum `.id`; CSS `#bubble .th` (11,5 px, miring, redup, ikon di depan); `showBubble(text, jp, emotion, isError, stream, thought)` mengisinya; `pump()` meneruskan `seg.thought`; bubble sempit (`narrow`) menyembunyikannya; tidak ditampilkan untuk bubble galat.
- Setelan: `SET.thoughts` (bawaan nyala), saklar **Pikiran batin** di Pengaturan; `IRIS_THOUGHTS=0` di `.env` mematikan dari server (baris `[thought]` tetap dibuang diam-diam kalau model menulisnya).
- Tidak dipakai di `/pantau` (komentar layar otomatis), `/belajar`, dan fun fact. Pikiran tidak ikut log chat dan ekspor HTML.

**Uji v40.**
- [ ] Ganti `server.py` dan `index.html`, restart server dan overlay
- [ ] Ngobrol santai beberapa giliran: sekitar 1 dari 3 balasan membawa teks kecil miring di atas bubble; suara hanya membacakan kalimat Jepang ucapan
- [ ] Saklar **Pikiran batin** dimatikan di Pengaturan: teks pikiran hilang, balasan tetap normal
- [ ] `IRIS_THOUGHTS=0` lalu restart server: model mungkin tetap menulis `[thought]`, tapi tidak tampil dan tidak ada panggilan perbaikan format di terminal
- [ ] `/pantau`, `/belajar`, dan fun fact tidak menampilkan pikiran
- [ ] Riwayat: setelah beberapa giliran, ekspor chat; baris `[thought]` tidak ada
- [ ] Frekuensi terlalu sering atau jarang: ubah kalimat "kira-kira 1 dari 3" di `THOUGHT_RULES`

## J4. Daftar kerja berikutnya (usulan)

1. Tes v40 di PC, lalu setel frekuensi pikiran.
2. Pembatalan Hermes (2b), prioritas S yang sudah menunggu sejak Bagian G.
3. Barge-in (J2 no. 1).
4. Memori otomatis versi ringan (J2 no. 3), lalu proaktif dengan pemicu (J2 no. 4).
5. Penyetelan lip-sync (J1) dan sisa mode belajar Jepang (J2 no. 7).

## J5. Berkas keluaran sesi ini

| Berkas | Isi |
|---|---|
| `server.py` | v40 di atas versi yang diunggah 2 Nov (memuat v39 dan sebelumnya) |
| `index.html` | v40 di atas versi yang diunggah 2 Nov |
| `iris-companion-gabungan.md` | Berkas ini, ditambah Bagian J dan koreksi lip-sync |
| `main.js`, `preload.js` | Tidak berubah |

---

# Bagian K: Perbaikan v42 dan v43 (2 Nov 2026)

**by: KangJiho**

Berkas berubah: `server.py`, `index.html`, `main.js`, `preload.js`. Berkas baru: `cek-cancel-hermes.py`, `buat_klip_vrma.py`, `assets/animations/` (`angguk`, `geleng`, `miring`, `tunduk` `.vrma` dan `clips.json` berisi empat klip itu). Semuanya lolos cek sintaks (`py_compile`, `node --check`); fungsi riwayat dan pembaca stream diuji dengan tiruan. **Belum ada yang dites di PC, kecuali klip VRMA (lulus, lihat K6).** Ganti keempat berkas, salin folder `assets/animations/`, lalu restart server dan overlay.

## K1. Cancel Hermes (2b), v42 (`server.py`)

- **Yang belum diketahui:** apakah Hermes berhenti kalau koneksi dari `server.py` putus. Tes lama (G6) tidak bersih, jadi jangan menganggap ini terbukti. Endpoint stop khusus di Hermes juga belum diketahui.
- **Perubahan:** `HERMES_STREAM=1` di `.env` memakai respons stream (SSE). Saat Stop, koneksi ditutup eksplisit (`async with client.stream`), jadi Hermes melihat klien putus di tengah giliran. Bawaan `0` (perilaku lama, tidak ada risiko regresi). Teks cancel tetap jujur: "tugas mungkin masih berjalan".
- **Tes yang memberi jawaban:** `cek-cancel-hermes.py` (jalankan dengan `.\.venv\Scripts\python.exe cek-cancel-hermes.py` saat tidak ada tugas Hermes lain). Hermes disuruh 12 langkah terpisah yang menulis baris ke `Downloads\cancel-probe-*.txt`; koneksi diputus setelah 14 detik; skrip melihat apakah file masih bertambah selama 60 detik, untuk mode biasa dan stream. Keluarannya `BERHENTI` atau `TETAP JALAN` per mode.
- **Keputusan sesudah tes:** pakai mode yang `BERHENTI`. Kalau dua-duanya `TETAP JALAN`, perlu endpoint stop di `api_server.py` Hermes (kirim `_handle_chat_completions` dan handler `/v1/runs` kalau ada); tidak ada yang menghentikan proses Hermes secara paksa dari sisi Iris (keputusan itu di tangan pemilik).
- **Risiko mode stream:** Hermes bisa menyisipkan penanda progres tool ke aliran teks. Kalau laporan di kartu "Hasil tugas" tampak kotor setelah `HERMES_STREAM=1`, kembalikan ke `0`.

## K2. Riwayat obrolan persisten, v42 (`server.py`)

- Disimpan ke `iris-history.json` di folder `server.py` setelah tiap giliran, bersama fakta yang ditangkap dan catatan tugas agen terakhir. Dimuat saat overlay tersambung; terminal mencetak `riwayat dipulihkan: N pesan`. Tombol Hapus (reset) menghapus file.
- Batas: 20 pesan terakhir (`MAX_HISTORY`), kedaluwarsa 3 hari (`IRIS_HISTORY_DAYS`). Pasangan pesan yang memuat kata rahasia (`_SECRET_RE`) tidak ditulis. Gambar tidak pernah masuk riwayat. `IRIS_HISTORY=0` mematikan, `IRIS_HISTORY_FILE` mengganti lokasi.
- Yang dipulihkan hanya konteks untuk Iris; panel chat di overlay tetap mulai kosong (panel itu hidup di sisi overlay).
- Teks percakapan tersimpan polos di disk. Jangan taruh folder proyek di drive yang tersinkron ke cloud (Z: belum dicek, lihat I7).

## K3. Klip VRMA (`index.html`, `buat_klip_vrma.py`)

- **File klip dibuat sendiri** oleh `buat_klip_vrma.py` (tanpa aset pihak lain, hanya pustaka standar Python; jalankan ulang untuk menyetel angka `CLIPS`). Empat klip kecil, hanya tulang punggung, leher, dan kepala (tanpa lengan, jadi aman dari gejala creepy): `angguk` (happy), `geleng` (angry), `miring` (surprised, shy), `tunduk` (sad). Struktur GLB divalidasi dengan skrip; **dimuat di three-vrm dan diputar lewat `playClip` sudah lulus di PC (2 Nov, lihat K6)**. Kalau Console menulis "Klip VRMA tidak dimuat", kirim isinya.
- **Perbaikan penting di `updateClip()`:** dulu bobot klip `w` dan idle `1-w` memakai pola yang membuat tulang yang hanya ada di idle (mis. lengan, kalau klipnya hanya kepala) jatuh ke pose T selama klip berjalan, karena three.js mencampur bobot kurang dari 1 dengan pose awal. Sekarang idle dijaga 1 dan klip diberi `w/(1-w)`, jadi hasil campurannya tetap `w : (1-w)` hanya untuk tulang yang ada di keduanya. Berlaku juga untuk klip Mixamo atau VRoid yang nanti ditambahkan.
- Konsol: `clips()` menampilkan klip yang termuat, `playClip('angguk')` memutarnya.
- Klip "greet" dan klip lengan (peace, pegang tepi) tetap butuh file dari luar; belum ada.

## K4. Iris ngilang dan laptop lag, v43 (`index.html`, `main.js`, `preload.js`)

**Diagnosis (dari kode dan data Task Manager 1 Nov, RAM 86%, Electron sekitar 942 MB):** penyebab pasti belum terbukti. Pemakai terbesar yang ada di kode: kanvas WebGL 2x sampai 3x dengan antialias, ditambah `filter: drop-shadow` pada kanvas itu (v22) yang dikomposit ulang tiap frame, ditambah efek musim. Di GPU terintegrasi dengan RAM hampir penuh, GPU process bisa mati: karakter lenyap dan seluruh laptop lag. v37d sudah memulihkan crash renderer dan konteks WebGL yang hilang, tapi tidak mengurangi bebannya.

- **Kualitas adaptif (`Q_LEVELS`):** `tinggi` (resolusi 2x sampai 3x, seperti dulu), `normal` (1,5x), `hemat` (1x, tanpa filter bayangan dan efek musim, FPS 30 dan 15). Mode `auto` (bawaan) mulai dari `tinggi` dan turun satu tingkat kalau rata-rata 90 frame lebih dari 1,6 kali lambat dari target; turunnya dicatat di Console dan chat. Manual: `/kualitas [auto|tinggi|normal|hemat]` atau pemilih "Kualitas" di Pengaturan (pilihan manual disimpan di `iris.q`; mode auto tidak mengingat tingkat turunnya, jadi mulai lagi dari `tinggi` tiap peluncuran). Sedang tidur atau mode fokus: 12 FPS.
- **Watchdog di `main.js`:** (1) renderer mengirim denyut (`render-pulse`, tiap sekitar 5 detik, hanya kalau konteks WebGL tidak hilang); jendela terlihat tapi tanpa denyut 45 detik = muat ulang halaman, maksimal 3 kali per 5 menit (bersama batas v37d); denyut direset saat jendela tampil, halaman mulai dimuat, laptop bangun, atau layar dibuka kuncinya. (2) Jendela sepenuhnya di luar semua layar dipindah ke pojok kanan bawah (dicek tiap 10 detik; tidak jalan saat diseret atau animasi mengintip).
- **Kalau masih ngilang atau lag:** sebelum `npm start`, jalankan `/kualitas hemat` lalu pantau Task Manager (tab Performance: GPU dan Memory; tab Processes: Electron). Terminal Electron akan mencetak `Watchdog: ...`, `Renderer mati: ...`, atau `WebGL context hilang`; kirim baris itu. RAM 86% dari Chrome (sekitar 1,1 GB) dan Electron saja sudah menekan sistem; menutup tab Chrome yang tidak dipakai membantu lebih dari apa pun di kode.

## K5. Uji v42 dan v43

- [ ] Ganti `server.py`, `index.html`, `main.js`, `preload.js`; salin `assets/animations/`; restart server dan overlay
- [ ] Riwayat: ngobrol dua tiga kali, restart `server.py` dan overlay, tanya "tadi kita bahas apa?" (terminal: `riwayat dipulihkan`); tombol Hapus lalu restart: tidak ada yang dipulihkan; pesan berisi "password" tidak muncul di `iris-history.json`
- [ ] `cek-cancel-hermes.py`: catat HASIL tiap mode; set `HERMES_STREAM` sesuai hasil
- [ ] `HERMES_STREAM=1`: `/agen sebutkan isi folder ~/hermes-test` tetap menghasilkan laporan bersih di kartu Hasil tugas
- [x] Console: "Klip VRMA aksi siap: angguk, geleng, miring, tunduk" muncul; `playClip(...)` mengembalikan `true` dan klip terlihat jalan (lihat K6). Belum dicek: lengan TIDAK melebar (screenshot hanya menunjukkan kepala)
- [x] Klip lewat emosi (jalur asli): ngobrol dengan emosi happy, angry, sad, surprised: klip kadang muncul (jeda minimal 8 detik)
- [x] `/kualitas hemat`: karakter lebih lunak tanpa bayangan, FPS lebih ringan; `/kualitas auto`: kembali; `/kualitas` tanpa argumen: melaporkan tingkat sekarang
- [ ] Biarkan overlay jalan beberapa jam dengan mode auto: catat apakah muncul "Frame lambat, kualitas gambar diturunkan" dan apakah Iris masih ngilang
- [ ] Seret Iris ke monitor lain lalu cabut monitor itu (jika ada): dalam 10 detik Iris kembali ke pojok kanan bawah
- [x] v43c: jalankan tugas `/agen` sampai pil "Memproses tugas..." muncul lalu hilang; pil V 9 H (nyalakan lewat Pengaturan atau saat ada layanan bermasalah) tetap di kanan dock, tidak pindah ke kiri; dengan lampiran gambar, thumbnail berada di kanan di samping pil

## K6. Hasil tes klip VRMA dan v43c, pil V 9 H (2 Nov 2026, sesi lanjutan)

**Berkas berubah:** `index.html` (dua baris CSS, v43c). Berkas lain tidak berubah. `buat_klip_vrma.py` dan `clips.json` dipakai apa adanya.

### Tes klip VRMA: lulus
- `python buat_klip_vrma.py` dijalankan di `Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron`; keluarannya `ditulis: angguk, geleng, miring, tunduk -> ...\assets\animations`.
- Console (Ctrl+Alt+D) menulis `Klip VRMA aksi siap: angguk, geleng, miring, tunduk`; `clips()` mengembalikan keempat nama itu.
- `playClip('angguk')`, `playClip('tunduk')`, dan `playClip('geleng')` mengembalikan `true` (terlihat di screenshot). Pemilik melaporkan semua klip jalan dan gerakannya bagus, jadi arah sumbu rotasi sudah benar untuk model yang dipakai (`maid` dan `prom`). Screenshot hanya memperlihatkan tiga klip itu; `miring` dilaporkan jalan tapi tidak terlihat di bukti.
- **Belum dites:** pemicu lewat emosi saat Iris bicara (jalur asli lewat `GATE`: peluang 12% sampai 70% per kalimat, `clipShare` 0,7, jeda minimal 8 detik, jadi memang jarang muncul), dan apakah lengan tetap diam selama klip.

### Cara mengetes klip (untuk dipakai lagi)
1. `python buat_klip_vrma.py` dari folder overlay, lalu restart overlay (`clips.json` dibaca sekali saat model dimuat).
2. Ctrl+Alt+D, tab Console, cari `Klip VRMA aksi siap: ...`. Kalau yang muncul `Klip VRMA tidak dimuat` atau `VRMA tidak dipakai`, `idle_loop.vrma` kemungkinan hilang dari `assets/animations/` atau ada file klip yang ditolak.
3. Ketik `playClip('angguk')` (juga `geleng`, `miring`, `tunduk`); `true` = diputar, `false` = masih ada klip lain yang jalan.
4. Untuk menguji jalur emosi tanpa menunggu keberuntungan: `GATE.chance = { happy:1, shy:1, angry:1, sad:1, surprised:1, neutral:1 }`, `GATE.clipShare = 1`, `GATE.clipGap = 0` (kembali normal setelah restart).

Salah langkah yang terjadi saat tes ini:
- `playClip(...)` adalah JavaScript: diketik di Console DevTools, **bukan** di PowerShell (PowerShell menjawab `playClip : The term ... is not recognized`).
- `clips()` hanya menampilkan daftar, tidak memutar apa pun (argumen di dalam kurungnya diabaikan).
- Console menolak tempel (paste) sampai diketik `allow pasting` lalu Enter; mengetik manual tidak kena peringatan itu.
- Kurung buka ganda `playClip(('angguk')` memberi `SyntaxError: missing ) after argument list`.
- Gerakannya sengaja kecil (sekitar 12° sampai 17°, kepala dan leher saja); perhatikan kepala, bukan badan.

### v43c: pil V 9 H tetap di kanan (`index.html`)
- **Gejala:** pil V 9 H (status koneksi VOICEVOX, 9Router, Hermes) tampil di kanan dock saat pil "Memproses tugas..." ada, lalu pindah ke kiri begitu pil tugas hilang.
- **Penyebab:** `#dock` memakai `justify-content: space-between`. Dengan dua elemen (`#status` dan `#conn`), `#conn` terdorong ke kanan; saat `#status` disembunyikan tinggal satu elemen, dan `space-between` menaruhnya di kiri.
- **Perbaikan** (tepat di bawah `#conn.show`):
  ```css
  #conn.show { display: flex; margin-left: auto; }
  #conn.show + #attach { margin-left: 0; }
  ```
  Baris kedua mencegah `#attach` (yang juga punya `margin-left: auto`) berbagi ruang kosong dengan `#conn`, jadi thumbnail lampiran tetap di kanan berdampingan dengan pil. Mode fokus (`#root.quiet`, dock `width: max-content` dan terpusat) tidak terpengaruh karena tidak ada ruang kosong untuk `auto`.
- **Status:** hanya diperiksa lewat `diff`; belum dilaporkan dites di Electron. Lihat K5.

### Catatan: overlay sempat hilang sendiri, penyebab belum diketahui
Saat tes di atas, pemilik melaporkan overlay "ilang sendiri" sebentar. Yang terlihat di Console: `Frame lambat (27 ms); kualitas turun ke "normal"`, lalu `Frame lambat (31 ms); kualitas turun ke "hemat"`, kemudian model dimuat ulang (`VRM dimuat (maid)` lalu `VRM dimuat (prom)`) dan animasi idle serta klip dimuat lagi. DevTools terbuka bersamaan dengan video YouTube di belakangnya, yang memberatkan render. Belum ada bukti apakah hilangnya karena ganti baju, muat ulang oleh watchdog (`main.js`), atau mode lain (mengintip, fokus, tidur). Pertanyaan yang belum terjawab: apakah `/baju` dipakai tepat sebelum hilang, dan apakah overlay muncul lagi sendiri. Pegangan kalau terulang: Ctrl+Alt+H (tampil atau sembunyi), Ctrl+Alt+C (buka chat dan keluar dari mode mengintip), `/muncul`, dan baca terminal Electron untuk baris `Watchdog:` atau `Renderer mati:`. Lihat K4.

## K7. v44: klip VRMA lebih sering; 10 klip baru dicoba lalu dibatalkan (2 Nov 2026)

**Pembatalan (2 Nov 2026, setelah dicoba di PC):** pemilik menilai 10 klip tambahan di bawah **tidak natural**, jadi `buat_klip_vrma.py` dikembalikan ke versi 4 klip (`angguk`, `geleng`, `miring`, `tunduk`). Yang berlaku sekarang: 4 klip itu, ditambah perubahan frekuensi dan `tryIdleClip()` di `index.html` (tidak punya efek tanpa klip bertag `idle`). Tabel dan daftar tes di bawah dipertahankan sebagai catatan; abaikan butir yang menyebut 14 klip. Klip lama tidak ikut diubah.

**Berkas berubah:** `index.html` dan `buat_klip_vrma.py`. Berkas hasil skrip (`assets/animations/*.vrma` dan `clips.json`) harus dibuat ulang dengan menjalankan skripnya. `node --check` lolos untuk `index.html`; ke-14 file `.vrma` diperiksa strukturnya (header GLB, kuaternion unit) lewat skrip. **Belum dites di PC.**

### Klip baru (total 14, semuanya hanya tulang punggung, dada, leher, kepala, tanpa lengan)
| Klip | Durasi | Emosi pemicu | Gerakan |
|---|---|---|---|
| `greet` | 2,4 dtk | tidak ada (diputar otomatis saat Iris muncul, lewat `loadClips`) | sapaan: kepala mengangguk sekali sambil miring |
| `toleh` | 3,4 dtk | neutral, idle | menoleh ke satu sisi lalu sisi lain |
| `napas` | 3,6 dtk | neutral, sad, idle | tarik dan hembus napas |
| `goyang` | 4,4 dtk | happy, neutral, idle | bergoyang kecil kiri-kanan |
| `semangat` | 2,0 dtk | happy | mengangguk dua kali |
| `malu` | 3,2 dtk | shy | menunduk dan memalingkan wajah |
| `kaget` | 1,8 dtk | surprised | kepala dan dada menyentak ke belakang |
| `ngambek` | 2,6 dtk | angry | memalingkan wajah, dagu naik |
| `cekikik` | 2,2 dtk | happy, shy | kepala miring dengan getaran halus |
| `mikir` | 3,8 dtk | neutral, idle | kepala naik dan miring ke satu sisi |

Empat klip lama (`angguk`, `geleng`, `miring`, `tunduk`) tidak berubah. Tag `idle` pada `emo` tidak pernah cocok dengan emosi kalimat, jadi hanya dipakai jalur idle di bawah.

### Perubahan frekuensi (`index.html`)
- `GATE.chance`: happy 0,5 jadi 0,7; shy 0,45 jadi 0,65; angry 0,5 jadi 0,7; sad 0,4 jadi 0,6; surprised 0,7 jadi 0,85; neutral 0,12 jadi 0,25.
- `GATE.clipShare` 0,7 jadi 0,9 (porsi klip dibanding gerakan prosedural), `GATE.clipGap` 8 jadi 4 detik.
- `IDLE_MIN` dan `IDLE_VAR` 20 + 0 sampai 20 detik jadi 12 + 0 sampai 14 detik (jeda gerakan saat Iris diam).
- Fungsi baru `tryIdleClip()` dan `GATE.idleClipShare` (0,7): saat jadwal idle tiba, klip bertag `idle` dicoba dulu, kalau tidak lolos jatuh ke gerakan prosedural lama. Kalau klip lain masih berjalan, jadwal idle ditunda 2 detik.
- Semua angka di `GATE` bisa disetel dari Console tanpa mengubah file (hilang saat restart).

### Cara pasang dan tes
1. Ganti `index.html` dan `buat_klip_vrma.py`; jalankan `python buat_klip_vrma.py`; restart overlay.
2. Console: harus tertulis `Klip VRMA aksi siap:` dengan 14 nama; `clips()` menampilkan semuanya.
3. Putar satu per satu: `playClip('greet')`, `playClip('toleh')`, dan seterusnya. Arah menoleh dan memalingkan wajah (kiri atau kanan) belum diverifikasi per model; kalau terbalik dari yang diinginkan, balik tanda angka sumbu yaw di skrip.
4. Biarkan Iris diam beberapa menit: harus ada gerakan tiap sekitar 12 sampai 26 detik, dan sebagian besar memakai klip. Ngobrol dengan berbagai emosi: klip harus lebih sering muncul dari sebelumnya.
5. Kalau terasa terlalu ramai, turunkan `GATE.clipShare`, `GATE.idleClipShare`, atau naikkan `GATE.clipGap` dan `IDLE_MIN` di `index.html`.
- [ ] 14 klip termuat dan `playClip` memutar semuanya
- [ ] `greet` diputar otomatis saat overlay muncul
- [ ] Gerakan idle memakai klip secara berkala
- [ ] Frekuensi klip saat ngobrol terasa pas, tidak berlebihan

---

## K8. Hasil tes dan perubahan sesi lanjutan (2 Nov 2026)

**Berkas berubah:** `server.py` (v45), `index.html`, `clips.json`. `main.js`, `preload.js`, dan `requirements.txt` tidak berubah. **v41 (emosi baru) dihapus pemilik** karena tampil aneh, jadi enam emosi lama (`neutral, happy, sad, angry, surprised, shy`) yang berlaku.

### K8.1 v45: `/agen siapa solon` dijawab dengan tugas lama (`server.py`) **[lulus tes di PC]**
- **Gejala:** `/agen siapa solon` dijawab Hermes dengan hasil tugas lama (review `index.html` Dapur Shika, "yang telah diidentifikasi sebelumnya"). Teks itu tidak ada di berkas overlay, jadi asalnya Hermes.
- **Penyebab:** `looks_like_followup()` menganggap semua pertanyaan pendek (3 kata atau kurang) yang diawali kata tanya sebagai lanjutan. "siapa solon" memenuhi syarat itu dan tugas lama masih di bawah 30 menit, jadi `build_hermes_message` menempelkan penanda "KEMUNGKINAN BESAR pertanyaan LANJUTAN" beserta catatan tugas lama, dan model gratis di belakang Hermes menurut.
- **Perbaikan:**
  - Pertanyaan pendek hanya dianggap lanjutan kalau tidak punya subjek sendiri: sisa katanya hanya kata generik (`banyak, lama, jauh, tepatnya, sih, dong, ya, aja, saja, nya, sekarang, lagi, kah, emang, memang`). "dimana?", "berapa banyak", "kapan sih" tetap lanjutan; "siapa solon" bukan.
  - "apa itu X" dan "siapa itu X" (ada kata sesudah "itu") selalu berdiri sendiri; kata rujukan lain ("itu tanggal berapa") tetap lanjutan.
  - `build_agent_context(..., include_note=follow)`: catatan tugas lama hanya ikut kalau pesannya lanjutan.
  - Kalau bukan lanjutan tapi ada konteks, ditambahkan penanda "TUGAS DI BAWAH BERDIRI SENDIRI" supaya Hermes tidak melanjutkan atau menyebut tugas lama (konteks tetap boleh dipakai kalau tugas memintanya, mis. "simpan yang kita bahas").
  - `HERMES_SYSTEM`: aturan "lanjutkan permintaan sebelumnya" hanya berlaku untuk pesan tanpa subjek sendiri, dan pertanyaan dengan subjek sendiri adalah tugas baru.
- **Catatan:** kalau kejadian serupa muncul lagi padahal terminal tidak menulis "lanjutan dari tugas sebelumnya", sumbernya memori atau sesi Hermes sendiri, bukan `server.py`. Tombol **Hapus** sebelum `/agen` baru juga menghindarinya.

### K8.2 Tampilan setengah badan: rok transparan dan paha terpotong (`index.html`) **[lulus, dinilai bagus oleh pemilik]**
- **Gejala bertahap:** (1) rok tembus pandang karena pudar bawah mulai 78% tinggi kanvas dan rok ada di zona itu; (2) pudar 92% sampai 100% memperlihatkan potongan paha seperti kaki patah; (3) pudar 86% membuat bagian atas rok baju maid tembus (pinggang baju maid lebih rendah dari seragam).
- **Penyebab dasar:** `CAM.bottom = 0.4` memotong kamera di tengah rok dan paha, jadi apa pun efek pudarnya hasilnya jelek.
- **Final:** `CAM.bottom` jadi **0.56** (potong di pinggang, di atas rok). Saat bar input tampil, `#root.half #char { margin-bottom: -16px }` memasukkan bagian bawah karakter ke balik bar dan pudar dimatikan (`#root.half:has(#barWrap.show) #char canvas { mask-image: none }`), jadi rok menyambung ke bar dan potongan tertutup bar. Saat bar tersembunyi, pudar pendek `#000 96.5%` ke transparan 100% (sekitar 15px).
- **Penyetelan:** `-16px` (makin besar makin dalam masuk ke bar), `96.5%` (ke 100% = tanpa pudar, tapi potongan lurus), `CAM.bottom` (turun ke 0.5 = lebih banyak badan, karakter lebih kecil). Selector `:has()` perlu Electron baru; kalau tidak jalan, ganti dengan class lewat JavaScript. Mode **Tubuh penuh** (`/badan penuh`) tidak terpengaruh dan tetap pilihan paling aman.

### K8.3 Klip VRMA lebih sering (`index.html`, `clips.json`) **[lulus tes di PC]**
- **Penyebab jarang muncul:** emosi `neutral` (paling sering saat ngobrol) tidak punya klip, dan tidak ada klip bertag `idle`, jadi gerakan saat diam tidak pernah memakai klip.
- **`clips.json`** (empat klip sama, hanya tag `emo` yang berubah): `angguk` = happy, neutral, idle; `geleng` = angry; `miring` = surprised, shy, neutral, idle; `tunduk` = sad, shy, neutral, idle. `geleng` sengaja tidak netral atau idle karena menggeleng terus terlihat seperti menolak.
- **`GATE`:** `chance` happy 0,9, shy 0,85, angry 0,9, sad 0,85, surprised 1, neutral 0,5; `clipShare` 1; `clipGap` 2 detik; `idleClipShare` 0,9. `IDLE_MIN = 8`, `IDLE_VAR = 10` (gerakan idle tiap 8 sampai 18 detik).
- **Temuan aset:** arsip `assets.rar` tidak berisi `angguk.vrma` dan `clips.json`-nya cuma 3 byte (kosong). Urutan pemasangan yang benar: `python buat_klip_vrma.py` dulu (membuat keempat klip dan `clips.json` lama), baru timpa `clips.json` dengan yang baru. Skrip itu menimpa `clips.json`, jadi kalau dijalankan ulang, salin lagi `clips.json` ini sesudahnya.
- **Kalau terlalu ramai:** `GATE.clipGap = 5` atau `GATE.idleClipShare = 0.5` dari Console (kembali normal setelah restart), lalu pindahkan angkanya ke `index.html` kalau cocok.
- **Belum ada klip lengan atau tarian.** Seluruh klip hanya punggung, leher, dan kepala. Tarian butuh file `.vrma` dari Mixamo atau pack lain, lalu perintah `/nari` (belum dibuat; `playClip` memutar sekali lalu memudar keluar, perlu opsi loop).

### K8.4 Hasil tes (dilaporkan pemilik)
- [x] v45: `/agen siapa solon` dijawab benar tentang Solon
- [x] Klip VRMA lebih sering (K8.3)
- [x] Tampilan setengah badan final (K8.2)
- [x] v43c: pil V 9 H tetap di kanan saat pil "Memproses tugas..." muncul lalu hilang
- [x] v43: `/kualitas hemat`, `/kualitas auto`, dan `/kualitas` tanpa argumen
- [x] Klip lewat emosi (jalur asli)
- [x] v41 emosi baru: dihapus oleh pemilik (tampil aneh), juga dari dokumen ini

### K8.5 Masih terbuka
- [ ] v40 pikiran batin (daftar tes di J3)
- [ ] v42 riwayat obrolan persisten (K5)
- [ ] Cancel Hermes 2b: jalankan `cek-cancel-hermes.py`, catat HASIL tiap mode, setel `HERMES_STREAM`, tes `/agen sebutkan isi folder ~/hermes-test` dengan `HERMES_STREAM=1`
- [ ] Uji ketahanan: overlay jalan beberapa jam dengan `/kualitas auto`, catat "Frame lambat" dan apakah Iris masih ngilang
- [ ] Cabut monitor kedua: Iris kembali ke pojok kanan bawah dalam 10 detik
- [ ] Skill `cek-elearning` di Hermes (cek tugas e-learning <kampus>, matkul <matkul>)
- [ ] Klip tarian dan lengan (Mixamo ke `.vrma`) dan perintah `/nari` dengan loop
- [ ] Urusan kecil dari I7: cek apakah Z: tersinkron ke cloud, suara Metan tidak dobel, pindahkan folder `tst`, C: dan Z: sudah 93% penuh

---

# Bagian L: Mini-browser `/chrome` multi-akun (3 Nov 2026)

Sumber rencana: `iris-03-roadmap-mini-browser.md` (fase 0 sampai 5). Urutan semula menunda fitur ini sampai lag dan cancel Hermes (2b) beres, kecuali fase 0. **Pemilik memutuskan melanjutkan sekarang** ("lanjutin dulu setting chromenya"), jadi fase 1 sampai 3 dikerjakan lebih awal. Fase 4 dan 5 belum disentuh; fase 5 (Hermes ikut mengendalikan panel) tetap bergantung pada cancel Hermes 2b.

**Berkas berubah:** `main.js`, `preload.js`, `index.html`. `server.py` tidak berubah. `node --check` lolos untuk ketiganya, dan logika perintah (`/chrome`, `/akun`, lebar jendela, navigasi) diuji dengan Electron tiruan (mock), **bukan** di Electron asli. Berkas keluaran: `main.js`, `preload.js`, `index.html`, `chrome-fase1-3.patch`.

## L1. Fase 0: uji kelayakan **[lulus]**

`WebContentsView` tanpa preload, partisi `persist:fase0`, dibuka dengan `Ctrl+Alt+W` di dalam overlay transparan yang avatarnya aktif. Panel sementara menutupi sebagian avatar (disengaja untuk uji; tata letak benar dikerjakan di fase 1).

| Gerbang | Hasil | Bukti |
|---|---|---|
| Login berhasil (Google, akun utama) | **lulus** | Screenshot halaman "Google Account" sudah login di panel; pemilik: "bisa masuk" |
| Sesi bertahan setelah restart | **lulus** | Overlay dimatikan lalu dibuka lagi, langsung masuk halaman akun ("yup langsung") |
| RAM dan lag wajar | **lulus, dengan catatan** | Task Manager: grup Electron 6 proses 1.422 MB (panel terbuka), lalu 5 proses 1.132 MB (sesudah ditutup). Selisih **sekitar 290 MB**, dan jumlah proses turun satu, jadi proses renderer panel benar-benar dibuang. CPU Electron hanya 1,5% sampai 3,4%. Urutan kedua screenshot diasumsikan (terbuka lalu tertutup), dan penilaian lag avatar tidak dicatat |

Catatan:
- Memori sistem 88% (panel terbuka) dan 80% (sesudah). Selisih 8 poin tidak boleh seluruhnya dikaitkan ke panel, karena VS Code (sekitar 614 MB) ikut hilang dari daftar. Angka yang lebih bersih adalah selisih grup Electron.
- Baseline grup Electron (sekitar 1,1 GB: overlay, avatar VRM, three.js) jauh lebih besar dari harga panel. Itu yang relevan untuk masalah lag di roadmap, bukan panelnya.
- Jawaban untuk keputusan roadmap "akun utama fase 0: Google atau bukan": **login Google di panel tertanam tidak diblokir**. Kalau Google mulai memblokir, cadangannya tetap jendela terpisah di sebelah bubble. Jangan mengakali dengan user-agent palsu.
- Temuan penting kode: kunci navigasi v28 (`web-contents-created`) memblokir semua `will-navigate` dan `will-redirect` di semua `webContents`, sehingga login (yang penuh redirect) gagal di panel. Panel dikecualikan lewat sesinya; jendela overlay utama tetap terkunci seperti sebelumnya.

## L2. Fase 1 sampai 3: yang dibangun

**Tata letak.** Saat panel dibuka, jendela overlay **melebar ke kiri** sebesar 432 px (panel 420 px + margin 12) dengan tepi kanan tetap, jadi karakter tidak bergeser (`#root` sudah menempel ke kanan). Ditutup = kembali ke lebar semula dengan tepi kanan tetap. Kalau tidak ada ruang di kiri layar, jendela dijepit ke tepi dan karakter bergeser sedikit ke kanan selama panel terbuka. Panel menempel di bawah jendela (tinggi sampai 520 px) dan dihitung ulang tiap jendela berubah ukuran (chat dibuka atau dipanjangkan).

**Klik.** Area panel menangkap klik, area lain tetap tembus klik. `main.js` memutuskan (ia tahu posisi kursor lewat `pollCursor`, `syncWebIgnore`), dan `set-ignore-mouse` dari renderer tetap dihormati di luar area panel (`applyIgnore`).

**Fitur yang dimatikan selama panel terbuka:** sembunyi di tepi layar (`peekHide`), duduk di jendela lain (`sitSnap`), dan sembunyi otomatis saat dilepas di tepi (`edgeSnap`), karena semuanya menghitung posisi dari lebar jendela standar (`PEEK_CHAR_CX`). `savePos` dan `cornerPos` dikoreksi dengan lebar tambahan supaya posisi tersimpan tidak bergeser.

**Akun.** Lima slot di `iris-accounts.json` (folder `userData`, dibuat otomatis, lokasinya dicetak di terminal). Tiap akun punya partisi `persist:<nama>`, jadi login tersimpan dan terpisah. Bawaan: slot 1 `kuliah`, slot 2 `google` (memakai partisi `persist:fase0` supaya login hasil uji fase 0 terpakai), slot 3 sampai 5 kosong. Hanya satu akun hidup: ganti akun menutup tab lama dan membuang prosesnya, lalu membuka link awal akun baru. **[Digantikan 3 Nov 2026: tab diparkir, maksimal 3 hidup, lihat N5.]**

**Keamanan panel:** proses terpisah, tanpa `preload` dan `nodeIntegration`, `sandbox: true`, izin kamera/mikrofon/notifikasi ditolak, `will-attach-webview` ditolak, navigasi dan redirect hanya ke `https://` (atau `http://` untuk `localhost`, `127.0.0.1`, `[::1]`), popup dimuat di panel yang sama. IPC hanya satu pintu (`web-panel`, ditolak kalau pengirimnya bukan jendela overlay). Log terminal memotong URL sampai path (tanpa query yang bisa berisi token).

**Perintah (`/chrome`, `/akun`, juga `Ctrl+Alt+W` dan menu tray):**

| Perintah | Fungsi |
|---|---|
| `/chrome 1` sampai `/chrome 5` | Ganti ke akun nomor itu dan buka link awalnya; akun lama ditutup |
| `/chrome` | Buka akun terakhir (setelah restart: slot 1) |
| `/chrome kuliah` | Sama, memakai nama akun |
| `/chrome 3 https://situs.com` | Akun 3 dengan alamat lain, link awal tidak berubah |
| `/chrome tutup` | Tutup panel dan buang proses renderernya |
| `/chrome daftar` atau `/akun` | Tampilkan lima slot |
| `/chrome mundur`, `maju`, `muat`, `beranda` | Navigasi panel; juga `Alt+←`, `Alt+→`, `F5` atau `Ctrl+R`, dan tombol mundur/maju mouse (yang terakhir belum terbukti) |
| `/akun tambah nama [link]` | Buat akun di slot kosong pertama |
| `/akun link <nomor\|semua> <url\|baru>` | Ganti link awal; `baru` = kembali ke halaman tab baru |
| `/akun hapus nama` | Hapus akun beserta sesi loginnya (`clearStorageData`) |

Nama akun: huruf kecil, angka, `-` atau `_`, maksimal 20, dan tidak boleh sama dengan kata perintah (`tutup`, `daftar`, `mundur`, `maju`, `muat`, `beranda`, `home`, `back`, `semua`, `baru`, dan sejenisnya).

## L3. Perubahan setelah tes pertama (3 Nov 2026)

1. **`<alamat e-learning kampus>` gagal: `ERR_NAME_NOT_RESOLVED`** (terminal menunjukkan panel dimuat dan ditutup dengan benar, RAM renderer panel sekitar 100 MB; yang putih adalah halaman error Chromium). Alamat itu berasal dari catatan awal proyek, bukan dari konfirmasi pemilik, dan pencarian web tidak menemukan alamat e-learning <kampus> yang bisa dipastikan. **Keputusan pemilik: semua akun mulai dari halaman tab baru dulu.** Akun tanpa link awal membuka `https://www.google.com/` (Electron tidak punya halaman tab baru bawaan); bisa diganti lewat environment `IRIS_NEWTAB_URL`. Bawaan `iris-accounts.json` tidak lagi berisi link; berkas lama harus dibersihkan sekali dengan `/akun link semua baru`.
2. **Tidak ada cara mundur di panel** (panel tidak punya tombol). Ditambahkan `/chrome mundur|maju|muat|beranda`, pintasan `Alt+←`/`Alt+→`/`F5`/`Ctrl+R` lewat `before-input-event`, dan tombol mundur/maju mouse lewat `app-command` (khusus Windows). Mundur di halaman pertama membalas "Tidak ada halaman sebelumnya".

## L4. Hasil tes dan temuan (dilaporkan pemilik)

- [x] Tata letak: panel di kiri, karakter tetap utuh di kanan (screenshot 3 Nov), bar input dan chat tetap di bawah karakter
- [x] Halaman login Google tampil dan bisa diketik di panel
- [x] Log terminal: panel dibuka dan ditutup, renderer panel sekitar 100 MB, proses dibuang saat ditutup
- Temuan: panel **tidak bisa digeser, diubah ukurannya, atau ditutup dengan tombol** sendiri. Ia menempel di jendela overlay. Seluruh jendela (karakter dan panel) dipindahkan dengan tombol ✥ di ujung kiri bar input atau dengan menggeser karakter. Ini konsekuensi panel tertanam; alternatifnya jendela terpisah di sebelah bubble (cadangan di roadmap, tapi tidak menyatu dengan bubble dan menambah satu jendela).
- Temuan: halaman login Google sempat tampil saat dibuka dari `/chrome 1` (partisi `kuliah` kosong, jadi wajar). **Belum dikonfirmasi** perintah mana yang dipakai pada screenshot itu, dan apakah `/chrome 2` benar-benar langsung login.

## L5. Daftar tes yang belum dikonfirmasi

- [ ] `/chrome 2`: langsung masuk akun Google tanpa login (partisi `persist:fase0`)
- [ ] Isolasi: login Google di `/chrome 2`, lalu `/chrome 1` harus belum login; kebalikannya juga
- [ ] Login situs kampus sekali di `/chrome 1` (alamat benar belum diketahui), lalu restart: masih login
- [ ] `/chrome tutup`: jendela kembali ke lebar semula, karakter tidak melompat, RAM turun lagi
- [ ] Klik bergantian di karakter, bar input, chat, dan panel: semuanya bisa diklik, panel bisa diketik
- [ ] Menggeser dengan ✥ atau karakter: panel ikut tanpa tertinggal atau berkedip
- [ ] Iris dipindah mepet tepi kiri layar lalu `/chrome`: perilaku jepitan (karakter bergeser sedikit) dan kembali normal saat ditutup
- [ ] Chat dibuka atau dipanjangkan saat panel terbuka: panel tetap rapi di bawah
- [ ] `/chrome mundur`, `Alt+←`, `F5`, dan tombol mundur mouse
- [ ] `/akun tambah`, `/akun link`, `/akun hapus` (hapus harus menghapus sesi login akun itu)
- [ ] Hotkey `Ctrl+Alt+W` dan menu tray "Mini-browser /chrome (buka / tutup)"

## L6. Masih terbuka

- [ ] **Alamat e-learning <kampus> yang benar** (untuk `/akun link 1 ...`). Kalau alamat yang dipakai di Chrome biasa tetap `ERR_NAME_NOT_RESOLVED` di panel padahal terbuka di Chrome, itu masalah DNS di Electron (kecil kemungkinannya, karena Google jalan)
- [ ] Halaman tab baru lokal dengan kolom alamat dan pintasan situs (butuh pengecualian aturan "hanya https" untuk satu halaman lokal); usulan, belum diputuskan
- [ ] Panel yang bisa digeser dan diubah ukurannya (jendela terpisah) kalau panel tertanam terasa kurang; belum diputuskan
- [x] Fase 4: pil akun aktif di dock dan penutupan renderer saat `/kualitas` turun ke hemat (ditulis 3 Nov 2026, Bagian M; **belum dites di PC**)
- [ ] Fase 5a **kode sudah ditulis (v51, Bagian N, belum dites)**; fase 5b dan 5c belum disentuh (Hermes mengendalikan panel). **Prasyarat 5b: cancel Hermes 2b beres lebih dulu.** Bentuk jembatan kontrol (A: perintah sempit buatan sendiri, disarankan; B: relay CDP terbatas ke panel) diputuskan saat masuk fase 5
- [ ] Urutan terhadap fitur lain (lag dan cancel Hermes) lewat opsi 1 sampai 4 di `iris-01-status-bermasalah.md`, yang belum diunggah ke sesi ini
- [ ] Batas domain per akun, konfirmasi aksi yang mengubah sesuatu, dan bingkai penanda "Hermes sedang mengendalikan": semuanya baru relevan di fase 5

# Bagian M: Mini-browser fase 4, pil akun dan hemat RAM (3 Nov 2026)

**Berkas berubah:** `main.js`, `preload.js`, `index.html` (patch: `chrome-fase4.patch`). `server.py` tidak berubah. `node --check` lolos untuk ketiganya; **belum dites di Electron asli**.

## M1. Yang dibangun

- **Pil akun di dock** (`#webpill`, di antara pil status tugas dan pil V 9 H). Tampil hanya saat panel `/chrome` terbuka: chip akun aktif menampilkan nomor dan nama (`2 google`), akun lain hanya nomornya, ditambah tombol ✕. Klik chip nomor = `/chrome N` (ganti akun, tab lama ditutup, masuk link awal); klik ✕ = `/chrome tutup`; klik chip aktif tidak melakukan apa-apa. Pil ikut hilang di mode fokus, saat bersembunyi di tepi, dan saat bar input tersembunyi (sama seperti pil V 9 H).
- **Sinkron dengan main.js.** `main.js` mendorong event `web-state` `{open, slot, nama, akun, reason}` tiap panel dibuka, diganti, atau ditutup, dan tiap `/akun tambah|link|hapus` saat panel terbuka. Setelah halaman overlay dimuat ulang (watchdog), renderer menanyakan keadaan lewat `webState()`, jadi pil tidak hilang walau panel masih terbuka.
- **Hemat RAM.** Kalau kualitas gambar turun ke `hemat` (manual lewat `/kualitas hemat` atau Pengaturan, atau otomatis karena frame lambat), `index.html` memberi tahu `main.js` (`webQuality`), yang menutup panel dan membuang renderernya; chat menampilkan catatan. Pemberitahuan hanya dikirim saat tingkat **berubah**, jadi membuka panel sengaja saat sudah di mode hemat tetap boleh dan tidak langsung ditutup.
- **`/chrome ram`**: menampilkan di chat RAM dan CPU renderer panel, GPU, dan total semua proses (data yang sama dengan log terminal), untuk memeriksa gerbang RAM tanpa Task Manager. Nama `ram` sekarang tidak boleh dipakai sebagai nama akun.
- Keamanan tidak berubah: `web-state`, `web-panel`, dan `web-quality` hanya diterima dari jendela overlay; panel tetap tanpa preload.

- **Perbaikan M1b (menu tertutup panel).** Panel web adalah view asli Electron yang selalu menimpa halaman, dan menu aksi cepat serta popover (timer, baju, Pengaturan) menempel di tepi kiri jendela, yaitu persis di bawah panel, jadi tertutup. Saat panel terbuka, `#root` diberi kelas `webopen` dan menu/popover digeser 432 px ke kanan, di sebelah panel.

- **M1c: menu tidak menabrak bar input** (`index.html`). Menu aksi cepat dan popover (Timer, Baju, Pengaturan) sekarang berdiri tepat di atas bar input (bawahnya menempel ke atas bar, tinggi dibatasi sampai tepi atas jendela, bisa di-scroll kalau tidak muat), dihitung tiap dibuka lewat `placeFloat()`. Sebelumnya posisinya tetap 150 px dari atas dan menimpa bar.
- **M1d: animasi panel** (`main.js`). Panel meluncur masuk dari tepi kiri jendela (240 ms, ease-out) saat `/chrome` dibuka, dan meluncur keluar ke kiri (200 ms) sebelum dibuang saat ditutup (`/chrome tutup`, ✕, hotkey, atau hemat). Ganti akun tidak dianimasikan. Yang bergerak hanya posisi x (ukuran tetap), jadi halaman tidak reflow. Panel adalah view asli, jadi tidak bisa difade; slide dipilih karena itu. Pil akun hilang setelah animasi keluar selesai, dan jendela menyempit sesudahnya.

- **M1e: karakter berkedip dan panel kurang mulus saat hilang** (`main.js`, `index.html`). Dugaan penyebab (belum terbukti): jendela transparan berubah ukuran pada saat yang sama dengan proses renderer panel dibuat atau dibuang, sehingga kanvas karakter kosong sesaat dan frame panel tersendat. Perbaikan: (1) urutan dipisah dengan jeda 130 ms (`WEB_SETTLE`): buka = jendela melebar, jeda, panel dibuat dan meluncur masuk (300 ms, ease-out quart); tutup = panel meluncur keluar (260 ms, ease-in-out), dibuang, jeda, jendela menyempit; (2) batas panel dihitung sekali per animasi, bukan tiap frame; (3) `index.html` menggambar ulang karakter seketika saat jendela berubah ukuran (dan lagi 60 dan 200 ms sesudahnya). Kalau masih berkedip, langkah berikut: jendela dibuat selalu lebar (tanpa resize) atau panel dipindah ke jendela terpisah.

- **M1f: layout panel lebih rapi dan bilah alat** (`main.js`, `index.html`). Panel sekarang bersudut membulat (`setBorderRadius(14)`) dan di atasnya melayang bilah alat berbentuk pil, 6 px di atas panel: tombol mundur, maju, muat ulang (berputar saat memuat), beranda (link awal akun), kolom alamat (hanya nama host, judul halaman di tooltip), dan ✕ tutup. Mundur dan maju meredup kalau tidak ada riwayat. Bilah alat digambar di DOM overlay (bukan view kedua), sehingga panel tetap tanpa preload; tombolnya memakai pintu `web-panel` yang sudah ada (`/chrome mundur|maju|muat|beranda|tutup`). `main.js` mengirim `nav {host, title, back, fwd, loading}` dan `closing` lewat event `web-state` (digabung per 60 ms). Tinggi panel jadi `520` dikurangi 40 px bilah alat (`WEB_TB`); `index.html` memakai rumus yang sama lewat `--webh`. Area klik panel diperluas ke bilah alat. Bilah alat ikut meluncur (CSS) bersamaan dengan panel.

- **M1g: pratinjau gambar tidak konsisten** (`index.html`). Pratinjau gambar (klik gambar di chat atau lampiran: Buka besar, Salin gambar, Simpan, Tutup) sebelumnya penutup layar penuh `inset: 0` berwarna navy gelap 88% dengan blur, sehingga muncul sebagai persegi gelap keras di atas desktop, tidak sejalan dengan kartu bulat lain. Sekarang kartu melayang bergaya panel (warna dan sudut ikut tema, animasi `pop` seperti menu), berdiri di atas bar input, lebarnya mengikuti gambar, tombolnya memakai gaya `.pill` yang sama dengan UI lain, dan bergeser ke kanan panel saat `/chrome` terbuka (`--webx`). Tinggi gambar dibatasi sampai tepi atas jendela (`--ivmax`).

- **M1h: kartu dan menu terlihat tembus** (`index.html`). Warna panel (`--panel`, `--panel-2`) dan gradasi `--pt`/`--pb` memakai alfa 0,95 sampai 0,98, sehingga teks halaman di belakang (mis. halaman Claude di browser) samar terlihat menembus menu, popover, bar input, log chat, pil, bilah alat, dan kartu pratinjau. Semuanya dijadikan alfa 1 di kelima tema (Iris dan empat musim). Slider transparansi jendela di Pengaturan (`SET.op`) tidak disentuh; kalau diset di bawah 100, semua tetap tembus sesuai pilihan.

## M2. Daftar tes fase 4

- [ ] Menu, popover, bar input, log chat, bilah alat, dan kartu pratinjau tidak menembus teks di belakangnya, di kelima tema; Pengaturan > transparansi tetap bekerja

- [ ] Pratinjau gambar: tampil sebagai kartu bulat di atas bar input (tanpa persegi gelap), semua empat tombol berfungsi, tidak menabrak bar, benar di setiap tema musim, dan di sebelah kanan panel saat `/chrome` terbuka

- [ ] Bilah alat: mundur, maju, muat ulang, beranda, dan ✕ berfungsi dan bisa diklik tanpa menembus ke jendela di belakang; mundur dan maju meredup di halaman pertama
- [ ] Bilah alat sejajar dengan panel saat chat dibuka, dipanjangkan, dan saat jendela dekat tepi atas layar (tinggi panel menyusut)
- [x] Sudut membulat panel tampil bersih di jendela transparan (tanpa sudut putih persegi) **[lulus, dua screenshot pemilik 3 Nov 2026]**

- [ ] Buka dan tutup `/chrome` berulang: karakter tidak hilang atau berkedip; panel menghilang mulus. Catat kualitas gambar saat itu (`/kualitas`), karena mode tinggi paling berat untuk GPU

- [ ] Menu aksi cepat dan popover tidak menabrak bar input, baik chat tertutup, terbuka, maupun dipanjangkan
- [ ] Panel meluncur masuk dan keluar mulus (tanpa kedip atau lompat); buka lalu langsung tutup, dan ganti akun saat animasi keluar, tidak membuat panel nyangkut

- [ ] Panel terbuka lalu klik menu aksi cepat (tombol di bar), Timer, Ganti baju, Pengaturan: semuanya tampil penuh di kanan panel, tidak tertutup

- [x] `/chrome 1`: pil muncul di dock dengan chip `1 kuliah` dan chip nomor akun lain (`2`) serta ✕ **[lulus lewat screenshot: chip aktif memuat nomor dan nama, chip lain nomor saja, ✕ ada; nama akun di PC pemilik sudah berbeda dari bawaan (mis. `c1`, `c2`)]**
- [ ] Klik chip `2`: pindah ke akun 2, tab akun 1 ditutup, chip aktif berpindah, link awal akun 2 dimuat
- [ ] Klik ✕: panel tertutup, pil hilang, jendela kembali ke lebar semula
- [ ] `/chrome ram` saat terbuka dan sesudah ditutup: renderer panel hilang dan total turun (sebelumnya sekitar 290 MB)
- [ ] `/kualitas hemat` saat panel terbuka: panel tertutup, pil hilang, ada catatan di chat; `/chrome` sesudahnya tetap bisa membuka
- [ ] Biarkan mode `auto` menurun sendiri saat panel terbuka (kalau bisa dipancing): panel ikut tertutup
- [ ] `/akun tambah` saat panel terbuka: chip baru muncul tanpa membuka ulang panel
- [ ] Pil tidak melebar sampai menutup pil status tugas saat `/agen` berjalan dan lima akun terisi (lebar dock sempit; **belum diukur**)
- [ ] Mode fokus, bersembunyi di tepi, dan bar input tersembunyi: pil ikut hilang
- [ ] Restart overlay saat panel terbuka lalu muat ulang halaman (watchdog): pil kembali

## M3. Berikutnya

*(Diperbarui: fase 5a sudah ditulis sebagai v51, lihat Bagian N; yang menunggu cancel Hermes 2b sekarang fase 5b dan 5c.)* Catatan lama: fase 5a (Hermes baca saja) menunggu **cancel Hermes 2b** (v42, mode stream opsional, daftar tesnya di K5 masih `[ ]`) dan keputusan bentuk jembatan (A atau B). Urutan yang disarankan: tes fase 4 dan daftar L5, lalu tes v42, lalu fase 5a.

# Bagian N: v46 sampai v51, jaga layar, panel pindah sisi, jembatan baca-saja (3 Nov 2026)

Disusun dari komentar kode di `main.js`, `index.html`, `server.py`, `preload.js`, dan `iris_web.py` yang diunggah 3 Nov 2026. **Status uji tidak diketahui kecuali disebut lain: anggap semuanya belum dites di PC sampai pemilik mengonfirmasi.** Isi tiap butir dibaca dari komentar kode, bukan dari catatan sesi, jadi alasan keputusannya tidak tercatat di sini.

## N1. Ringkasan versi

| Versi | Isi | Berkas |
|---|---|---|
| v46 | Seluruh UI (menu, bubble, bar input, panel `/chrome`) dijaga tetap di dalam layar; jendela yang dilepas jauh dari tepi meluncur balik ke area kerja | `main.js` |
| v46b | Collider rambut diperbesar supaya rambut tidak menembus bahu dan dada saat badan miring | `index.html` |
| v46c, v46d | Mode setengah badan: mask pudar bawah ikut memotong bayangan; `PEEK_SHIFT` 70 menjadi 110 supaya rambut dan badan sisi dalam tidak terpotong batas kanvas | `index.html` |
| v46e | Baju ikut situasi dan musim: baju dasar tersimpan terpisah dari baju situasi; prioritas tidur, fokus, sesi belajar (`/belajar` = seragam), malam; hanya berganti saat situasi berubah | `index.html` |
| v47 | Jendela menempel di tepi kiri layar: menu dan popover pindah ke kanan karakter (kelas `.dockleft`, IPC `win-side`). Server: `FUNFACT_TIMEOUT` (bawaan 45 dtk, maksimal 48) dan `FUNFACT_MODEL` opsional untuk fun fact; `FUN_GEN_WAIT` di overlay 50 dtk | `main.js`, `index.html`, `preload.js`, `server.py` |
| v48 | Karakter boleh menempel di tepi kiri layar; panel `/chrome` pindah ke **kanan** karakter kalau ruang kiri tidak cukup (IPC `web-side`; lebar `#root` dikunci supaya karakter tidak melompat) | `main.js`, `index.html`, `preload.js` |
| v49 | Bar input dan chat dipersempit dari kiri (tepi kanan tetap) agar garis petunjuk hijau tetap di bawah karakter; ukur ulang posisi jendela sesudah mengintip | `index.html`, `main.js` |
| v50 | Panel pindah sisi otomatis: Iris diseret mentok tepi sisi panelnya lalu dilepas, panel pindah ke sisi seberang (kalau cukup lega); karakter tidak bergeser | `main.js` |
| v51 | **Fase 5a: jembatan Hermes baca saja** (N2) | `main.js`, `iris_web.py`, `/chrome elemen`, `/chrome jembatan` |

`package.json` tidak berubah (Electron `^45.1.0`, `three-vrm` `^3.5.5`, `three` `^0.186.1`). `server.py` hanya tersentuh di v47.

## N2. v51: jembatan Hermes baca saja (fase 5a)

**Aturan keamanan (di kode):**
- Mati secara bawaan. Nyala hanya kalau `IRIS_WEB_BRIDGE=1` **dan** `COMPANION_TOKEN` terisi (token yang sama dengan `/ws`); tanpa token jembatan menolak jalan.
- Mendengar hanya di `127.0.0.1` (port `IRIS_BRIDGE_PORT`, bawaan 8767). Header `Host` harus `127.0.0.1` atau `localhost` dengan port yang benar; permintaan berheader `Origin` (dari halaman web) ditolak; hanya `GET`; token dibandingkan timing-safe lewat hash SHA-256 (header `X-Iris-Token`).
- Batas laju 30 permintaan per 10 detik; tiap permintaan dicatat di terminal (rute dan kode, tanpa token dan tanpa isi).
- Hanya menyentuh `webContents` panel web, bukan jendela overlay.
- Isi isian formulir tidak pernah dikirim: elemen hanya melaporkan `password: true/false` dan nama isian. URL dikirim hanya asal dan path (tanpa query dan hash).
- Semua hasil bertanda `untrusted: true` (isi halaman adalah data, bukan perintah).

**Rute:**

| Rute | Isi |
|---|---|
| `/web/state` | Akun aktif (slot, nama), URL tanpa query, host, judul (maks 200 karakter), status memuat |
| `/web/text?max=N` | Teks halaman (`innerText`), bawaan 8000, maksimal 20000 karakter |
| `/web/elements` | Sampai 120 elemen terlihat (tag, teks maks 80 karakter, `href` tanpa query, posisi x dan y) |
| `/web/shot` | Screenshot panel, JPEG kualitas 70, lebar maksimal 1000 px, base64 |

Panel belum terbuka menghasilkan HTTP 503; galat lain 500; rute tidak dikenal 404 beserta daftar rute.

**Klien:** `iris_web.py` (pustaka standar saja): `python3 iris_web.py state | text [maks] | elements | shot [berkas.jpg]`. Lingkungan: `COMPANION_TOKEN` (wajib), `IRIS_BRIDGE_HOST`, `IRIS_BRIDGE_PORT`. Screenshot disimpan ke `iris-web-shot.jpg` kalau nama berkas tidak diberikan.

**Uji lokal tanpa Hermes (di overlay):** `/chrome elemen` (daftar 15 elemen pertama) dan `/chrome jembatan` (status jembatan). Nama `baca`, `elemen`, `jembatan`, `perintah`, `bantuan`, `help`, `ke`, `go` kini ikut dicadangkan dan tidak boleh jadi nama akun.

**Ada selisih dengan roadmap yang perlu diputuskan.** Roadmap (`iris-03-roadmap-mini-browser.md`) menyebut bentuk jembatan A atau B diputuskan saat masuk fase 5. Kode v51 memakai **bentuk A** (perintah sempit buatan sendiri, hanya baca) dan **HTTP lokal pada port 8767 di `main.js`**, bukan `/ws` di `server.py`. Jadi: (1) keputusan A atau B praktis sudah jatuh ke A; (2) catatan roadmap "tidak ada perubahan di `server.py`" tetap benar untuk 5a; (3) pintu masuk agen luar di `iris-02` (perintah WebSocket `speak` dan `play_clip`) adalah fitur terpisah yang belum dibangun.

**Prasyarat roadmap yang dilangkahi.** Roadmap dan Bagian M3 mengatur fase 5a menunggu cancel Hermes 2b. Karena 5a hanya membaca dan mati secara bawaan, risikonya jauh lebih kecil dari 5b. Tapi risiko injeksi prompt tetap ada begitu Hermes membaca halaman akun yang sudah login (misalnya email), jadi pakai akun uji dulu dan jangan nyalakan `IRIS_WEB_BRIDGE=1` secara permanen sebelum teruji.

## N3. Daftar tes v46 sampai v51

**Layar dan sisi panel (v46 sampai v50): [lulus, dilaporkan pemilik 3 Nov 2026 "bisa aman"; rincian per butir tidak dicatat, dan butir monitor kedua tidak disebut sehingga tetap terbuka]**
- [x] Seret Iris sampai separuh keluar layar saat chat atau panel terbuka: seretan dibatasi di dalam layar; dilepas jauh dari tepi: jendela meluncur balik
- [x] Iris mentok tepi kiri layar, buka menu aksi cepat, Timer, Baju, Pengaturan: semuanya tampil di kanan karakter (v47)
- [x] Iris mentok kiri lalu `/chrome`: panel muncul di kanan, karakter tidak melompat (v48)
- [x] Iris mentok kiri lalu buka chat: bar input dan chat dipersempit dari kiri, garis petunjuk hijau tetap di bawah karakter (v49)
- [x] Panel kiri, seret Iris mentok kiri dan lepas: panel pindah ke kanan; kebalikannya di tepi kanan; di layar sempit yang tidak muat di sisi seberang, panel tidak pindah (v50)
- [x] Sesudah mengintip lalu muncul lagi, posisi bar dan menu tetap benar (v49)
- [ ] Monitor kedua: perilaku jepitan dan perpindahan sisi

**Karakter dan baju (v46b sampai v46e):**
- [ ] Rambut tidak menembus bahu atau dada saat badan miring (v46b)
- [ ] Setengah badan: bayangan tidak terpotong lurus, rambut sisi dalam tidak terpotong (v46c, v46d)
- [ ] Baju ikut musim (saklar Pengaturan), baju situasi (tidur, fokus, `/belajar`, malam), dan kembali ke baju dasar sesudahnya; pilihan manual tidak tertimpa (v46e)

**Fun fact (v47):**
- [ ] Model lambat: fun fact tidak lagi berakhir `TimeoutError()`; `FUNFACT_TIMEOUT` dan `FUNFACT_MODEL` terbaca dari environment

**Jembatan 5a (v51):**
- [ ] Tanpa `IRIS_WEB_BRIDGE=1`: terminal mencetak "mati"; `iris_web.py state` ditolak karena port tertutup
- [ ] Nyala dengan `IRIS_WEB_BRIDGE=1` tanpa `COMPANION_TOKEN`: terminal mencetak "TIDAK dinyalakan"
- [ ] Nyala dan bertoken: `state`, `text`, `elements`, dan `shot` berhasil setelah `/chrome 1` membuka halaman biasa
- [ ] Token salah: HTTP 401; panel belum dibuka: HTTP 503; `curl` dengan header `Origin`: 403; metode `POST`: 405
- [ ] Lebih dari 30 permintaan dalam 10 detik: HTTP 429
- [ ] Halaman login: elemen password hanya `password: true` tanpa isi; URL di hasil tanpa query dan hash
- [ ] Hasil memuat `untrusted: true`; log terminal tidak memuat token atau isi halaman
- [ ] `/chrome elemen` dan `/chrome jembatan` di chat sesuai dengan hasil lewat `iris_web.py`
- [ ] Ganti akun lewat pil lalu `state`: akun dan slot ikut berubah; `/chrome tutup` lalu `state`: 503

## N4. Yang masih terbuka

- [x] Tes layar dan sisi panel v46 sampai v50 lulus (N3, kecuali monitor kedua)
- [ ] Hasil tes Bagian M2 dan L5 belum tercatat di dokumen ini; N3 menambah, bukan menggantikan
- [ ] Putuskan apakah 5a boleh dites sebelum cancel Hermes 2b (lihat N2)
- [ ] Skill Hermes yang memanggil `iris_web.py` belum ada; saat ini klien hanya bisa dijalankan manual
- [ ] Fase 5b (klik, ketik, navigasi dengan konfirmasi dan batas domain) dan 5c (`/agen` membuka `/chrome N`) belum disentuh dan tetap menunggu cancel Hermes 2b
- [ ] Cadangan `iris-01-status-bermasalah.md`, `iris-02-fitur-riset.md`, dan `iris-03-roadmap-mini-browser.md` masih menulis mini-browser fase 1 sampai 5 sebagai rencana; perlu disinkronkan dengan Bagian L, M, dan N
- [ ] Masalah Tier S di `iris-01` (lag, cancel Hermes 2b, disk 93%) tidak berubah oleh v46 sampai v51; tidak ada bukti dari kode bahwa sudah beres

## N5. Hasil tes dari screenshot dan temuan kode (3 Nov 2026)

**Dari dua screenshot pemilik ("aman nih"):** panel `/chrome` tampil di kiri karakter dengan bilah alat (mundur, maju, muat ulang, beranda, kolom alamat `www.google.com`, ✕), sudut membulat bersih, panel buram penuh, dan login Google sudah aktif (akun terdeteksi di tooltip). Pil akun tampil di dock. Yang **tidak** terbukti dari gambar: fungsi tiap tombol, ganti akun lewat klik, isolasi login antar akun, RAM, dan tampilan menu atau kartu di tema lain. Butir-butir itu tetap `[ ]` di L5 dan M2 sampai pemilik melaporkannya.

**Temuan: kode sudah menyimpang dari keputusan di Bagian L dan roadmap.**

| Hal | Dokumen (Bagian L, M, roadmap) | Kode `main.js` yang diunggah |
|---|---|---|
| Tab akun lama saat ganti akun | Ditutup dan dibuang; selalu masuk link awal; "hanya satu akun hidup" | **Dibiarkan hidup tapi disembunyikan** (diparkir) supaya kembali ke halaman terakhir; batas `IRIS_WEB_KEEP`, **bawaan 3** tab hidup; yang terlama dibuang. `IRIS_WEB_KEEP=1` = perilaku lama |
| Penanda di pil | Tidak ada | Titik kecil pada chip akun yang tab-nya masih hidup (tooltip "halaman terakhir masih ada"); terlihat di screenshot (`2•`) |
| Jumlah slot akun | 5 | **10** (`ACCT_SLOTS`); berkas lama dengan 5 slot dilengkapi otomatis |
| `/chrome` tanpa alamat | Buka link awal | Melanjutkan tab yang masih hidup |

Dampaknya: keputusan "tab lama ditutup dan selalu ke link awal" di Bagian L dan di bagian "Sudah diputuskan" roadmap sudah tidak berlaku untuk perilaku bawaan. Tiap tab hidup sekitar 100 MB (renderer panel, L3) sampai lebih; dengan bawaan 3 tab, RAM bisa naik sekitar 200 MB di atas satu akun, padahal RAM sudah 86% dan lag belum beres. Gerbang "RAM turun setelah akun lama ditutup" (fase 3 dan 4) juga perlu dibaca ulang. **Keputusan pemilik (3 Nov 2026): perubahan ini disengaja.** Ganti akun sekarang melanjutkan halaman terakhir, bukan link awal, dan keputusan lama di Bagian L ("tab lama ditutup, selalu ke link awal") digantikan oleh ini. Harga yang diterima: RAM lebih tinggi selama beberapa tab hidup. Cadangan kalau lag memburuk: `IRIS_WEB_KEEP=1` mengembalikan perilaku lama tanpa mengubah kode.

- [ ] Tes: buka akun 1, lalu 2, lalu 1 lagi: kembali ke halaman terakhir atau link awal? Cek `/chrome ram` dengan 1, 2, dan 3 tab hidup
- [ ] Tes: `/chrome tutup` membuang semua tab parkir atau hanya yang tampil
- [ ] Tes: `/kualitas hemat` membuang tab parkir juga (kode M1 hanya tercatat menutup panel)

---

# Bagian O: Audit berkas, klien `iris_web.py`, dan RAM tab parkir (4 Nov 2026)

**by: KangJiho**

Disusun dari sesi 4 Nov 2026. Berkas yang diperiksa: `main.js`, `preload.js`, `index.html`, `iris_web.py`, dan dokumen ini. `server.py` **tidak** ikut terunggah, jadi sisi server (v47 `FUNFACT_TIMEOUT`, `FUNFACT_MODEL`) tidak diperiksa. Pemeriksaan membaca kode dan menjalankan tes tiruan; belum ada yang dijalankan di Electron asli.

## O1. Audit konsistensi berkas

| Pemeriksaan | Hasil |
|---|---|
| `node --check main.js` | lolos |
| Saluran IPC `preload.js` ke `main.js` (21 saluran `send` dan `invoke`) | semuanya punya handler, tidak ada handler yatim |
| Pendengar `ipcRenderer.on` di `preload.js` (11 saluran) | semuanya dikirim dari `main.js` |
| `window.companion.*` yang dipakai `index.html` | semuanya ada di `preload.js` |

Kesimpulan: tidak ada fitur yang kehilangan jembatan antar tiga berkas overlay.

## O2. `iris_web.py` (klien jembatan fase 5a)

**Cocok dengan `main.js`:** rute `/web/state`, `/web/text?max=N`, `/web/elements`, `/web/shot`; header `X-Iris-Token`; field `image_base64`. Sintaks valid.

**Tes tiruan (server HTTP palsu, bukan Electron asli):** `state`, `text 500`, `shot`, dan `elements` berhasil; `shot` menulis berkas JPEG dengan isi yang benar; token salah menghasilkan pesan "Jembatan menolak (401)"; port mati menghasilkan "Jembatan tidak terjangkau".

**Temuan:**
- [ ] **Jangkauan dari WSL.** Jembatan di `main.js` hanya mendengar di `127.0.0.1` Windows. Hermes jalan di WSL; kalau WSL mode NAT, `127.0.0.1` dari WSL bukan Windows dan klien melaporkan "tidak terjangkau". Pilihan: `networkingMode=mirrored` di `.wslconfig` (lihat Bagian A, Lingkungan kerja), atau jalankan `iris_web.py` dari Windows. Jangan mengubah bind ke `0.0.0.0`. `IRIS_BRIDGE_HOST` selain `127.0.0.1` atau `localhost` ditolak server dengan 403 karena cek header `Host`.
- [ ] `iris_web.py text abc` (argumen bukan angka) berhenti dengan traceback `ValueError`, bukan pesan ringkas. Kecil dan tidak berbahaya.
- [ ] Teks bantuan `CHROME_HELP` di `main.js` menulis `/akun` "daftar 5 slot", padahal `ACCT_SLOTS` = 10 (baris `/chrome 1..10` di atasnya sudah benar).
- [ ] Tes yang menentukan: `/chrome 1`, lalu `python3 iris_web.py state` dari tempat Hermes berjalan. Kalau tembus, lanjut ke daftar tes N3 (token salah 401, panel belum dibuka 503, header `Origin` 403, `POST` 405, lebih dari 30 permintaan per 10 detik 429).

## O3. RAM dengan tab parkir (screenshot Task Manager, 4 Nov 2026)

Kondisi saat screenshot: pil akun menunjukkan titik pada akun 2 dan 3 dan akun 4 aktif, jadi 3 tab hidup (bawaan `IRIS_WEB_KEEP` = 3); halaman yang terbuka `claude.ai`.

| Proses | Memori |
|---|---|
| VmmemWSL | 2.378,3 MB |
| Electron (9 proses) | 1.937,9 MB |
| Google Chrome (15 proses) | 914,9 MB |
| Memori sistem | 84% (CPU 21%) |

Pembanding dari fase 0 (L1): grup Electron 1.132 MB (5 proses, panel tertutup) dan 1.422 MB (6 proses, satu tab terbuka).

- **Dugaan, belum terbukti:** selisih sekitar 800 MB dari kondisi panel tertutup ke tiga tab hidup, kira-kira 250 sampai 300 MB per tab. Lebih besar dari angka 100 MB di L3 dan N5 (yang dihitung dari halaman Google yang ringan). Satu sampel saja, dan sejak fase 0 banyak yang berubah (v46 sampai v52), jadi selisih itu tidak bisa dikaitkan seluruhnya ke tab.
- **Pemakai terbesar bukan Electron, tapi WSL** (`VmmemWSL`, tempat Hermes). Chrome biasa juga lebih dari 900 MB.
- Cadangan kalau lag memburuk: `IRIS_WEB_KEEP=2` atau `1` di `.env` (1 = perilaku lama, hanya satu tab hidup), dan membatasi memori WSL di `C:\Users\<nama>\.wslconfig`:
  ```
  [wsl2]
  memory=3GB
  autoMemoryReclaim=gradual
  ```
  lalu `wsl --shutdown`. Batas 3 GB hanya contoh; belum diketahui berapa yang Hermes butuhkan, jadi uji dulu apakah `/agen` masih lancar.

**Tes yang menjawab pertanyaan ini:**
- [ ] `/chrome ram` dengan 3 tab hidup, catat angkanya
- [ ] `/chrome reset`, buka satu akun, `/chrome ram` lagi; bandingkan selisihnya
- [ ] `/chrome ram` dengan 1, 2, dan 3 tab hidup (N5)

## O4. Status dokumen

- Pemilik menyatakan (4 Nov) butir sinkronisasi dokumen sudah beres: Bagian L (tab lama ditutup, 5 slot), bagian v35 dan v36, hasil tes L5 dan M2, dan cadangan `iris-01` sampai `iris-03`. **Berkas gabungan yang diunggah 4 Nov masih memuat** teks lama di Bagian L dan belum memiliki bagian v35 dan v36, jadi perbaikannya mungkin ada di salinan lain; belum diverifikasi di berkas ini.
- Permintaan menghapus butir `cek-elearning` dan alamat e-learning <kampus> dari daftar kekurangan: belum dikonfirmasi apakah yang dimaksud menghapus dari dokumen. Butir itu **tetap ada** di Bagian E, F, H, I, K8.5, dan L6.

## O5. Yang masih terbuka

- [ ] Tes jembatan 5a (daftar N3) dan jangkauan dari WSL (O2)
- [ ] Tes RAM tab parkir (O3), lalu putuskan `IRIS_WEB_KEEP`
- [ ] Cancel Hermes 2b: jalankan `cek-cancel-hermes.py` (K1); menahan fase 5b dan 5c
- [ ] Skill Hermes yang memanggil `iris_web.py` belum ada
- [ ] Rapikan `CHROME_HELP` (5 slot) dan penanganan argumen `text` di `iris_web.py`
- [ ] Sisa tes v46 sampai v50 yang belum dicatat (monitor kedua, v46b sampai v46e, v47 fun fact)
- [ ] Memori otomatis ringan: disetujui diambil, belum ditulis (O6)
- [ ] Angin dari kecepatan kursor: disetujui diambil, belum ditulis (O7)
- [ ] Fase 5a, 5b, 5c mini-browser: disetujui masuk rencana (O8); 5a siap dites, 5b dan 5c menunggu cancel Hermes 2b
- [ ] Menari mengikuti musik: disetujui diambil, belum ditulis (Bagian P); ada keputusan privasi yang harus diambil dulu (P3)
- [ ] Skrip setup, cek kesehatan, dan auto-start: disetujui diambil, belum ditulis (Bagian Q); ada keputusan terbuka di Q4

## O6. Keputusan: ambil "Memori otomatis ringan" (4 Nov 2026)

Pemilik menyetujui fitur ini diambil dari daftar Tier S di `iris-02-fitur-riset.md` (J2 no. 3). **Kode belum ditulis**: sisi servernya ada di `server.py`, dan berkas itu belum terunggah di sesi ini. Yang di bawah ini rancangan, bukan hasil kerja.

**Yang sudah ada dan dipakai ulang (dari Bagian J dan v12):** `/ingat`, `/memori`, `/lupa` (v12); `iris-memory.json` (maksimal 40 hal, 200 karakter per hal); `memory_block()` yang menyisipkan isi memori ke system prompt tiap giliran; `_SECRET_RE` yang menolak isi mirip rahasia; `note_user_facts()` (v16c); `offerChoices()` di `index.html` (v37, pilihan bernomor).

**Rancangan awal (usulan):**
- Pada akhir sesi (usulan pemicu: `reset` atau overlay terputus setelah beberapa giliran), model meringkas 3 sampai 5 fakta baru tentang pengguna dari percakapan itu.
- Fakta **tidak langsung disimpan**. Tampil sebagai daftar bernomor di chat; pengguna memilih mana yang disimpan atau menolak semua (memakai `offerChoices`). Alasan: memori tersimpan polos di disk dan dipakai ke tiap prompt, jadi salah tangkap sebaiknya tidak masuk diam-diam.
- Aturan lama tetap berlaku: `_SECRET_RE`, batas 40 hal dan 200 karakter, tidak menyimpan duplikat, dan `/memori` serta `/lupa` untuk melihat dan menghapus.
- Tanpa embedding (tidak menambah RAM). Pemilihan fakta yang relevan di `memory_block()` bisa dengan pencocokan kata sederhana; ini dinilai nanti.
- Saklar `IRIS_AUTOMEM=0` untuk mematikan, bawaan sebaiknya mati sampai teruji.
- Tidak dipakai untuk `/pantau`, `/belajar`, dan fun fact (sama seperti pikiran batin di v40).

**Belum diputuskan:**
- [ ] Pemicu "akhir sesi" yang tepat, karena overlay hampir tidak pernah ditutup (kalau terputus saja, ringkasan bisa tidak pernah jalan)
- [ ] Tampil sebagai kartu di chat atau lewat Iris yang menanyakan
- [ ] Apakah ringkasan memakai model chat biasa (menambah satu panggilan ke 9Router yang kadang lambat atau timeout)

**Tes saat sudah ditulis:**
- [ ] Ngobrol 5 sampai 6 giliran yang memuat fakta baru, lalu `reset`: muncul kandidat, bukan langsung tersimpan
- [ ] Pilih satu nomor: masuk ke `/memori`; tolak semua: tidak ada yang berubah
- [ ] Kalimat berisi "password" atau kunci: tidak pernah jadi kandidat
- [ ] Fakta yang sudah ada tidak muncul lagi sebagai kandidat
- [ ] `IRIS_AUTOMEM=0`: tidak ada panggilan ringkasan di terminal
- [ ] Server atau 9Router mati saat ringkasan: tidak ada galat yang tampil ke pengguna

**Yang dibutuhkan untuk mengerjakannya:** unggah `server.py` terbaru (dan `index.html` yang sekarang sudah ada) supaya perubahannya bisa dibuat langsung di atas versi yang berjalan.

## O7. Keputusan: ambil "Angin dari kecepatan kursor" (4 Nov 2026)

Pemilik menyetujui fitur ini diambil dari Tier B di `iris-02-fitur-riset.md` (ide dari xiaochun; di dokumen lama disebut juga di Tier A GitHub). **Kode belum ditulis.** Yang di bawah ini rancangan, dan pembacaan kodenya terbatas pada `index.html` yang diunggah.

**Yang terbaca dari `index.html`:**
- `vrm.update(dt)` dipanggil tiap frame (sekitar baris 1588), jadi simulasi spring bone rambut dan kain sudah berjalan dan ada titik untuk menambah gaya luar.
- Kursor global sudah masuk lewat `cursor.x`, `cursor.y`, `cursor.t` (diisi dari `onCursor` dan `mousemove`), jadi kecepatan kursor bisa dihitung dari selisih antar frame tanpa perubahan di `main.js`.
- Kecepatan jendela saat diseret sudah dikirim (`drag-vel`, v22) dan dipakai untuk ayunan badan; itu sumber kedua yang bisa memberi angin.

**Rancangan awal (usulan):**
- Hitung kecepatan kursor (px per detik, dihaluskan), ubah jadi vektor angin kecil yang menambah arah gravitasi atau gaya luar pada joint spring bone rambut dan kain, lalu meluruh pelan ke nol.
- Batas atas kekuatan angin dan ambang kecepatan minimum, supaya gerakan kursor biasa tidak membuat rambut bergetar terus.
- Saklar di Pengaturan (`SET.wind`) dan perintah `/angin`; bawaan sebaiknya mati sampai dinilai di layar.
- Mati otomatis di `/kualitas hemat`, mode fokus, tidur, dan saat mengintip, supaya tidak menambah beban.

**Catatan yang perlu dicek sebelum menulis kode:**
- [ ] Cara menyuntik gaya luar ke spring bone di `@pixiv/three-vrm` 3.5.x (mis. lewat pengaturan joint) belum diverifikasi; cek dulu API-nya.
- [ ] Model berbeda (maid, prom, seragam) punya jumlah dan pengaturan spring bone yang berbeda, jadi hasilnya bisa tidak seragam antar baju.
- [ ] Kosmetik dan menambah beban hitung per frame, sedangkan RAM sistem sudah sekitar 84% dan masalah lag belum beres (K4 dan O3). Ukur FPS sebelum dan sesudah.
- [ ] Rambut sudah pernah menembus bahu (v46b); angin yang kuat bisa memperburuknya.

**Tes saat sudah ditulis:**
- [ ] Gerakkan kursor cepat melewati karakter: rambut dan kain bergoyang sebentar lalu tenang
- [ ] Kursor diam atau pelan: tidak ada gerakan
- [ ] Seret jendela: rambut tertinggal ke arah berlawanan, lalu mengikuti
- [ ] `/angin mati`, `/kualitas hemat`, mode fokus, dan tidur: efek berhenti
- [ ] Ketiga baju: tidak ada rambut yang menembus badan
- [ ] FPS dan RAM di `/kualitas` tidak memburuk dibanding sebelum fitur ini

## O8. Keputusan: lanjutkan fase 5a, 5b, dan 5c mini-browser (4 Nov 2026)

Pemilik menyetujui tiga fase terakhir di `iris-03-roadmap-mini-browser.md` masuk rencana kerja: **5a** (Hermes baca saja), **5b** (Hermes beraksi), **5c** (`/agen` membuka `/chrome N`). Persetujuan ini menjawab pertanyaan terbuka di N4 ("putuskan apakah 5a boleh dites sebelum cancel Hermes 2b"): **5a boleh dites sekarang**.

**Urutan yang tetap berlaku (dari roadmap, tidak diubah oleh persetujuan ini):**

| Fase | Status | Syarat sebelum dikerjakan |
|---|---|---|
| 5a, Hermes baca saja | Kode ada (v51, `main.js` dan `iris_web.py`), belum dites | Tes dulu (N3 dan O2) |
| 5b, Hermes beraksi (navigasi, klik, ketik) | Belum ditulis | Cancel Hermes 2b beres, 5a lulus tes, dan rancangan konfirmasi, batas domain, serta tombol Stop disepakati |
| 5c, `/agen` membuka `/chrome N` | Belum ditulis | 5b lulus tes |

Alasan 5b dan 5c menunggu 2b ada di roadmap: agen yang memegang akun yang sudah login tapi tidak bisa dihentikan adalah kombinasi paling berisiko. Tombol Stop di 5b hanya berarti kalau 2b terbukti menghentikan agen. Kalau pemilik memutuskan melangkahi syarat ini, catat keputusannya di sini secara eksplisit.

**Langkah berikutnya, berurutan:**
1. [ ] Tes 5a: nyalakan `IRIS_WEB_BRIDGE=1` (dengan `COMPANION_TOKEN` terisi), `/chrome 1` dengan **akun uji**, lalu `iris_web.py state`, `text`, `elements`, `shot` dari tempat Hermes berjalan (cek jangkauan dari WSL, lihat O2). Daftar lengkap ada di N3.
2. [ ] Jalankan `cek-cancel-hermes.py` (K1) dan putuskan `HERMES_STREAM`; ini membuka 2b.
3. [ ] Buat skill Hermes yang memanggil `iris_web.py` (belum ada), supaya Hermes memakai 5a tanpa perintah manual. Perlakukan isi halaman sebagai data, bukan perintah (semua hasil sudah bertanda `untrusted: true`).
4. [ ] Rancang 5b: konfirmasi untuk aksi yang mengubah sesuatu (kirim, submit, bayar, hapus), batas domain per akun, bingkai penanda "Hermes sedang mengendalikan", dan tombol Stop. Keputusan bentuk jembatan A atau B sudah jatuh ke A (N2).
5. [ ] Rancang dan tulis 5c setelah 5b lulus.

**Risiko yang perlu diingat sebelum menyalakan 5a:** begitu Hermes bisa membaca halaman akun yang sudah login (mis. email), halaman bisa menyelipkan instruksi palsu (prompt injection). Pakai akun uji dulu dan jangan menyalakan `IRIS_WEB_BRIDGE=1` secara permanen sebelum teruji (N2).

---

# Bagian P: Keputusan mengambil "menari mengikuti musik" (4 Nov 2026)

**by: KangJiho**

Pemilik menyetujui fitur ini diambil dari daftar Tier B hasil perbandingan dengan proyek sejenis (ide dari Mate Engine, yang menyediakan pilihan aplikasi mana yang membuat karakter menari). Aturan lama tetap berlaku: **kode dan aset Mate Engine tidak dipakai**, hanya idenya (lisensi campuran AGPL v3 dan MateProv2, lihat F7). **Kode belum ditulis.** Yang di bawah ini keputusan dan rancangan awal, bukan hasil kerja.

## P1. Koreksi atas ringkasan sebelumnya

Saat fitur ini pertama kali diusulkan di perbandingan 4 Nov, ringkasannya menulis "klip VRMA sudah ada" dan "hanya nama proses, sesuai prinsip privasi". Keduanya kurang tepat dan dikoreksi di sini:

| Ringkasan lama | Kenyataan menurut dokumen ini |
|---|---|
| Klip VRMA sudah ada | Yang ada hanya 4 klip kecil tanpa lengan (`angguk`, `geleng`, `miring`, `tunduk`, K3). **Tidak ada klip tari.** Klip lengan butuh file dari luar. Sepuluh klip tambahan yang dicoba di K7 dinilai tidak natural dan dibatalkan. Gerakan lengan (`ARM_GEST`) belum dinilai baik secara visual (F7b) |
| Hanya nama proses, sesuai prinsip privasi | Itu **melonggarkan** prinsip lama: pada v22 "judul, nama proses, dan isi jendela TIDAK dibaca", dan v15 sengaja tidak membaca aplikasi aktif; pembacaan baru perlu persetujuan eksplisit (v15). Jadi ini keputusan baru, bukan sesuatu yang sudah sejalan |

## P2. Prasyarat yang belum ada

- [ ] **Aset tari.** Pilihan: (a) goyangan ritmis prosedural kecil pada punggung, dada, dan kepala tanpa lengan (aman dari gejala creepy, tanpa file luar); (b) klip tari VRMA dari luar, yang butuh lengan dan mengulang masalah K7; (c) tunda sampai gerakan lengan dinilai baik. **Usulan: mulai dari (a).**
- [ ] **Sumber sinyal "musik sedang diputar"** (P3).
- [ ] RAM sistem sudah sekitar 84% dan lag belum beres (K4, O3). Analisis audio per frame menambah beban, jadi harus bisa dimatikan dan diukur.

## P3. Keputusan terbuka: cara mendeteksi musik

| Opsi | Cara kerja | Privasi | Kelemahan |
|---|---|---|---|
| A. Level dan ritme audio sistem | Ambil keluaran audio (loopback), hitung energi dan ketukan sederhana; tanpa tahu aplikasinya | Terbaik: tidak membaca nama aplikasi; audio tidak disimpan dan tidak dikirim | Video, game, atau panggilan ikut memicu; belum diverifikasi apakah tangkapan audio loopback jalan di versi Electron ini |
| B. Daftar putih nama proses | Pemain musik yang dipilih pengguna (mis. Spotify) dianggap "musik"; hanya nama proses, tanpa judul jendela | Melonggarkan v22 dan v15; wajib opt-in terpisah | Proses hidup belum tentu sedang memutar |
| C. Gabungan A dan B | Menari hanya bila proses terdaftar berjalan **dan** ada energi audio | Sama seperti B | Dua mekanisme, usaha lebih besar |

**Usulan awal:** mulai dari opsi A, karena tidak butuh melonggarkan prinsip privasi; tambah B hanya kalau salah picu dari A terlalu mengganggu. **Belum diputuskan oleh pemilik.**

## P4. Rancangan awal (usulan)

- Saklar **Menari mengikuti musik** di Pengaturan dan perintah `/menari nyala|mati`, **bawaan mati**.
- Bila sinyal musik bertahan beberapa detik (histeresis, supaya tidak berkedip), Iris memainkan goyangan ritmis; berhenti beberapa detik setelah sinyal hilang. Ada jeda minimum antar sesi menari.
- Tidak aktif saat Iris sedang bicara, merekam suara, mode fokus, tidur, `/kualitas hemat`, atau sembunyi di tepi (pola yang sama dengan O7).
- Pembacaan audio hanya hidup saat saklar menyala dan jendela terlihat; berhenti total bila dimatikan.
- Opsional nanti: satu kalimat pendek bersuara saat mulai menari, mengikuti pola `GATE` dan jeda klip yang ada.
- Pilihan "aplikasi mana yang memicu" (gaya Mate Engine) hanya dibuat bila opsi B atau C dipilih.

## P5. Tes saat sudah ditulis

- [ ] Saklar mati (bawaan): tidak ada pembacaan audio dan tidak ada gerakan
- [ ] Saklar nyala, putar musik: Iris mulai bergoyang setelah beberapa detik, berhenti setelah musik berhenti
- [ ] Video bicara, panggilan, dan game: catat apa yang salah memicu, lalu setel ambang
- [ ] Iris bicara, mode fokus, tidur, `/kualitas hemat`: tidak menari
- [ ] Ketiga baju: tidak ada rambut atau kain yang menembus badan saat bergoyang
- [ ] FPS dan RAM di `/kualitas` tidak memburuk dibanding sebelum fitur ini
- [ ] Tidak ada audio yang tersimpan di disk atau terkirim ke jaringan

## P6. Urutan

Fitur ini Tier B dan **tidak menggeser** daftar terbuka di O5 (tes jembatan 5a, cancel Hermes 2b, tes RAM, memori otomatis, angin dari kecepatan kursor). Kerjakan setelah itu, dengan satu paket per tes seperti aturan sebelumnya.

---

# Bagian Q: Keputusan mengambil skrip setup, cek kesehatan, dan auto-start (4 Nov 2026)

**by: KangJiho**

Pemilik menyetujui fitur ini diambil dari daftar Tier S hasil perbandingan dengan proyek sejenis. Idenya dari Open-LLM-VTuber (instalasi dan pembaruan lewat `uv`, dengan skrip pembaruan) dan AIRI (pemasangan satu perintah lewat Scoop). Aturan lama tetap berlaku: **tidak ada kode proyek lain yang disalin**, hanya idenya. **Skrip belum ditulis.** Yang di bawah ini keputusan dan rancangan awal, bukan hasil kerja.

## Q1. Koreksi dan batas ruang lingkup

Ringkasan di perbandingan 4 Nov menulis bahwa `/health` "sudah cek tiga layanan, tinggal dibungkus". Itu benar sebagian saja:

- `/health` (dan push `health` ke pil status, v39) **hanya hidup kalau `server.py` sudah jalan**. Skrip cek kesehatan harus memeriksa VOICEVOX (`:50021/version`), 9Router (`:20128/`; **bukan** `/health`, yang menjawab 404, lihat Q8), dan Hermes (`:8642/health`) langsung, tanpa lewat `server.py`, karena kerusakan yang paling sering justru membuat server tidak bisa mulai.
- Yang dijanjikan skor "mudah dipasang" di sini adalah **mudah dijalankan dan didiagnosis di PC yang sama**. Memasang dari nol di PC lain tetap butuh langkah manual untuk WSL, Hermes, VOICEVOX, dan 9Router (Bagian B, "Setup Requirements"), karena semuanya pemasangan di luar folder proyek. Skrip tidak akan memasang program-program itu; paling jauh menunjukkan mana yang belum ada.

## Q2. Rancangan: empat fase, dikerjakan satu per satu

| Fase | Berkas (usulan nama) | Isi | Mengubah sesuatu? |
|---|---|---|---|
| 1. Dokter | `iris-doctor.ps1` | Hanya membaca dan melaporkan (lihat Q3) | **Tidak** |
| 2. Peluncur | `iris-start.ps1` (dan `iris-stop.ps1`) | Menyalakan bagian yang belum hidup, berurutan, lalu membuka overlay | Hanya menyalakan proses |
| 3. Auto-start | `iris-autostart.ps1 -On` dan `-Off` | Mendaftarkan atau menghapus peluncur saat masuk Windows | Mendaftar tugas pengguna; bawaan **mati** |
| 4. Setup PC baru (opsional, nanti) | `iris-setup.ps1` | Membuat `.venv`, `pip install -r requirements.txt`, `npm install`, lalu memeriksa prasyarat luar | Hanya di dalam folder proyek |

Fase 1 hanya membaca dan tidak menyentuh `server.py`, `main.js`, atau `index.html`, jadi boleh dikerjakan kapan saja tanpa bentrok dengan daftar tes di O5.

**Status fase 1 (4 Nov 2026):** `iris-doctor.ps1` **sudah ditulis**, lolos parser PowerShell 7.4.6 (0 galat) dan fungsi bantunya lulus tes tiruan; **belum dijalankan di PC** (lihat Q9). Fase 2 sampai 4 belum ditulis.

## Q3. Fase 1: apa yang dicek `iris-doctor.ps1`

Tiap baris `OK`, `WARN`, atau `GAGAL` disertai satu kalimat cara memperbaiki. Kode keluar bukan nol kalau ada `GAGAL`.

- [ ] Folder proyek ada dan terbaca (folder sekarang di drive Z:, lihat Q4)
- [ ] `.venv` ada, Python-nya bisa dijalankan, paket di `requirements.txt` terpasang (termasuk `python-dotenv`, H7)
- [ ] `node_modules` dan biner Electron ada
- [ ] `.env` ditemukan (urutan baca seperti `server.py`: `~/.env` dulu, lalu `.env` lokal). Untuk `COMPANION_TOKEN` dan `HERMES_API_KEY` **hanya panjang dan terisi atau tidak yang dilaporkan, isinya tidak pernah dicetak** (pola yang sama dengan G dan v39b)
- [ ] Port: `8765` (server Iris) bebas atau dipakai server Iris; `50021` VOICEVOX; `20128` 9Router; `8642` Hermes. Peringatan kalau server WSL dan server Windows sama-sama hidup (port 8765 bentrok, G)
- [ ] WSL berjalan; Hermes menjawab HTTP 200 di `127.0.0.1:8642/health`; kunci terisi
- [ ] Mode jaringan WSL dan `.wslconfig` (`networkingMode`, batas memori) dilaporkan sebagai informasi, tidak diubah
- [ ] Ruang kosong C: dan Z: (keduanya 93% penuh, E1.8); `WARN` di bawah ambang yang bisa diatur
- [ ] Pemakaian RAM sistem; `WARN` bila tinggi (RAM sekitar 84% di O3)
- [ ] Bila `server.py` sudah hidup: ambil `/health` dan tampilkan baris pentingnya (`ninerouter`, `agent_confirm`, `ws_token`)

## Q4. Keputusan terbuka (belum diputuskan pemilik)

- [ ] **Cara VOICEVOX, 9Router, dan Hermes naik di dalam WSL.** Ternyata ketiganya hidup di dalam Ubuntu (Q8), jadi peluncur tidak perlu path program Windows; yang perlu diketahui adalah apa yang menyalakannya di sana (unit systemd, `crontab @reboot`, atau perintah manual). Belum diketahui. Data yang diminta: daftar layanan systemd yang berjalan dan nama proses di WSL (tanpa argumen, supaya tidak memuat kunci).
- [ ] **WSL (dan isinya) dinyalakan peluncur atau tidak.** Karena VOICEVOX, 9Router, dan Hermes semuanya ada di WSL, pilihannya bukan lagi "Hermes saja": mematikan WSL mematikan suara dan chat sekaligus, jadi pilihan praktisnya hanya WSL selalu hidup. Gateway Hermes dikelola systemd dan melayani kanal Telegram (Bagian B); WSL menghabiskan sekitar 2,4 GB (O3). Opsi `-NoHermes` di rancangan awal tidak masuk akal kalau ketiganya satu paket; opsi yang tersisa hanyalah mengurangi memori lewat `.wslconfig`. Usulan: peluncur cukup memastikan WSL hidup, lalu menunggu tiga layanan menjawab.
- [ ] **Drive Z:.** Sebagian terjawab (Q8): Z: bertipe Fixed, NTFS, berlabel "<label drive>", bukan drive jaringan (`net use` kosong) dan bukan `subst`. Masih tidak diketahui apakah itu drive eksternal yang bisa dicabut; doctor melaporkan tipe bus-nya (USB atau bukan) kalau terbaca. Bila USB, auto-start harus menunggu Z: ada (dengan batas waktu) dan tidak gagal diam-diam.
- [ ] **Task Scheduler atau folder Startup.** Usulan Task Scheduler (bisa diberi jeda, mis. 60 sampai 90 detik setelah masuk, supaya tidak menambah lag saat Windows baru naik), dengan `-Off` yang menghapusnya bersih.
- [ ] **Tempat berkas.** Folder proyek belum dirapikan ke `backend` dan `overlay` dan `.venv` jangan dipindah dulu (Bagian A); skrip ditaruh di akar folder proyek, dan jalur dibuat relatif terhadap lokasi skripnya.

## Q5. Aturan keselamatan untuk semua fase

- Tidak mencetak token atau kunci; tidak mengubah `.env`; tidak mengubah `COMPANION_HOST` atau bind apa pun (tetap `127.0.0.1`).
- Tidak mengubah kebijakan eksekusi PowerShell milik mesin: skrip dijalankan lewat `powershell -ExecutionPolicy Bypass -File ...` (hanya untuk proses itu), sama seperti `Set-ExecutionPolicy -Scope Process Bypass` yang sudah dipakai.
- **Idempoten:** menjalankan peluncur dua kali tidak membuat server kedua. Cek port 8765 dulu (G).
- **Tidak pernah me-restart gateway Hermes** dan tidak menjalankan `hermes update`. Aturan lama: restart dan pembaruan hanya saat tidak ada tugas berjalan, dan skrip tidak bisa tahu itu. Peluncur hanya menyalakan yang belum hidup.
- Jalur dengan spasi (`Z:\Projek AI waifu Dekstop\...`) selalu dikutip.
- Peluncur menulis log ke satu berkas di folder proyek (tanpa token) supaya galat saat auto-start tidak hilang.
- Auto-start **bawaan mati**, dinyalakan hanya dengan perintah eksplisit.

## Q6. Tes saat sudah ditulis

- [ ] Fase 1 di PC yang sehat: semua `OK`; kode keluar 0
- [ ] Matikan VOICEVOX, lalu 9Router, lalu Hermes satu per satu: baris yang tepat berubah jadi `GAGAL` dengan petunjuk; tidak ada token di keluaran
- [ ] `.venv` atau `node_modules` dipindah sementara: dilaporkan, tidak ada yang dibuat ulang diam-diam
- [ ] Peluncur dijalankan dua kali: tidak ada server kedua dan tidak ada galat bentrok port
- [ ] Peluncur dengan semuanya mati: urutan naik benar, overlay baru terbuka setelah `/health` menjawab, Hermes tidak di-restart bila sudah hidup
- [ ] `-NoHermes`: Hermes tidak disentuh, `/health` menampilkan Hermes mati, chat biasa tetap jalan
- [ ] Auto-start `-On`, keluar dari Windows, masuk lagi: overlay naik setelah jeda tanpa jendela PowerShell terbuka; `-Off` menghapus tugasnya
- [ ] Z: belum siap saat masuk Windows: peluncur menunggu lalu berhasil atau gagal dengan pesan jelas
- [ ] Kedua drive hampir penuh: peringatan muncul, tidak ada yang dihapus

## Q7. Urutan

Fase 1 (hanya membaca) boleh lebih dulu karena tidak mengubah kode yang sedang dites. Fase 2 dan 3 sebaiknya setelah tes RAM di O3, karena menyalakan semuanya saat masuk Windows menambah beban saat RAM sudah sekitar 84%, dan hasil tes itu menentukan keputusan Hermes di Q4. Fase 4 hanya kalau Iris akan dipasang di PC lain. Satu fase per tes, seperti aturan sebelumnya.

## Q8. Temuan lingkungan (4 Nov 2026, dari keluaran PowerShell pemilik)

Tidak ada token atau kunci di data ini (nilai `.env` disembunyikan sebelum ditempel).

| Hal | Temuan | Dampak |
|---|---|---|
| WSL | Distro `Ubuntu`, WSL2, berstatus Running | Nama distro dipakai sebagai bawaan `-Distro` |
| Port | 8765 dipegang proses `server.py`. Port 50021, 20128, dan 8642 di Windows dipegang **satu PID yang sama** (13200); di dalam WSL (`ss -ltn`) ketiganya mendengar: VOICEVOX di `127.0.0.1:50021`, Hermes di `127.0.0.1:8642`, 9Router di `0.0.0.0:20128` | **Dugaan:** VOICEVOX, 9Router, dan Hermes semuanya jalan di dalam WSL, dan PID 13200 adalah penerus localhost WSL. Proses penyedia belum dikenali; doctor mencetak nama pemilik port supaya ini terbukti. Bagian B ("Windows host untuk: VOICEVOX") kemungkinan sudah usang |
| 9Router | `/health` menjawab **404**; di dokumen, "Quick Command Reference" (Bagian B) masih menyebut `/health` | Doctor memeriksa `/` dan menganggap kode HTTP apa pun sebagai hidup. `server.py` memakai path lain (belum kubaca, berkasnya belum terunggah) |
| VOICEVOX | `/version` menjawab `0.25.2` | Cocok dengan catatan di Bagian C |
| Python | Dua `python.exe` yang tampak adalah pasangan pengalih venv dan interpreter aslinya, bukan dua server. Interpreter dasar `.venv` adalah Python Microsoft Store 3.11.9; `home` di `pyvenv.cfg` menunjuk direktori alias per paket (tanpa nomor versi) | Dugaan awalku (jalur berversi bisa putus saat Store memperbarui) **tidak terbukti**; risiko tersisa: Python Store dihapus. Doctor menjalankan `python --version` dari venv untuk membuktikannya, bukan menebak dari jalur |
| Node | `D:\Note\node.exe` (npm dari sana); Electron lewat `node_modules` | Doctor mencari `node` lewat PATH, tidak menulis jalur tetap. Peluncur nanti harus memastikan PATH yang sama, terutama dari Task Scheduler |
| Disk | C: bebas 14,02 GB (sekitar 6%); D: 32,69 GB; Z: 68,28 GB (sekitar 7%) | C: di bawah ambang 15 GB, jadi doctor memberi `WARN`; disk virtual WSL biasanya di C: (belum diperiksa letak sebenarnya) |
| `.env` | Satu berkas di `C:\Users\<nama>\.env` berisi `HERMES_API_KEY`, `HERMES_URL`, `COMPANION_HOST`, `COMPANION_PORT`, `NINEROUTER_API_KEY`, `COMPANION_TOKEN`; di folder proyek hanya `.env.example` | `NINEROUTER_URL` dan `VOICEVOX_URL` tidak diatur, jadi bawaan dipakai |
| Port di WSL | 9Router mendengar di `0.0.0.0`; ada juga `*:80` dan dua port lokal tak dikenal (43893 dan 48025) | Doctor memberi `INFO` untuk wildcard dalam mode NAT dan `WARN` bila `.wslconfig` memakai `mirrored`. Layanan di port 80 belum diketahui |

**Catatan konsistensi (belum diputuskan):** dokumen menyebut daftar klip di `assets/animations/clips.json`, sedangkan tangkapan layar folder proyek memperlihatkan `clips.json` di akar folder. Belum dicek berkas mana yang dibaca `index.html`; doctor sengaja tidak memeriksanya supaya tidak menghasilkan `GAGAL` palsu.

## Q9. Fase 1: berkas dan cara menjalankan

**Berkas:** `iris-doctor.ps1`, taruh di akar folder proyek (sejajar dengan `server.py`).

```powershell
cd "Z:\Projek AI waifu Dekstop\Fase 2 overlay Electron"
powershell -ExecutionPolicy Bypass -File .\iris-doctor.ps1
```

Opsi: `-Distro Ubuntu`, `-MinFreeGB 15`, `-RamWarnPct 85`, `-Proyek <jalur>`. Kode keluar 1 bila ada `GAGAL`. Semua layanan sebaiknya menyala saat dijalankan; hasil tanpa layanan menyala juga berguna sebagai tes (Q6).

**Yang sudah diuji (di sisi pembuat, bukan di PC pemilik):**
- Parser PowerShell 7.4.6: 0 galat; berkas hanya berisi karakter ASCII (aman dibaca Windows PowerShell 5.1).
- Fungsi bantu dengan data tiruan: pembacaan `.env` (kutip dibuang, komentar dan baris kosong dilewati, hanya panjang yang dipakai), pembacaan HTTP (200, 404, dan koneksi ditolak), pemecahan alamat dan port, penguraian keluaran `ss -ltn` memakai keluaran asli milik pemilik, serta pembersihan karakter NUL dari `wsl -l -v`. Satu galat ditemukan dan diperbaiki: isi balasan tanpa `Content-Type` terbaca sebagai angka byte.
- **Belum dijalankan:** bagian yang memakai cmdlet Windows (`Get-NetTCPConnection`, `Get-CimInstance`, `Get-Partition`, `wsl.exe`) serta Windows PowerShell 5.1 itu sendiri. Anggap seluruh skrip **belum dites di PC** sampai ada keluarannya.

**Tes pertama di PC (tempel keluarannya):**
- [ ] Semua layanan menyala: harapannya `OK` untuk VOICEVOX, 9Router, Hermes, dan server; `WARN` untuk disk C:
- [ ] Baris "dilayani ..." untuk port 50021, 20128, 8642 menunjukkan nama proses yang sama; ini menjawab dugaan di Q8
- [ ] Baris `.env` hanya menampilkan panjang, tidak ada nilai token
- [ ] Skrip tidak membuka jendela, tidak menyalakan apa pun, dan WSL tetap seperti sebelumnya

# Bagian Q10: Hasil pengumpulan data dan rancangan Fase 2 (4 Nov 2026)

**by: KangJiho**

Bagian ini menjawab keputusan terbuka di Q4 dan melengkapi Q8, berdasarkan keluaran PowerShell dan WSL milik pemilik (tanpa token). Bila bertentangan dengan Q4 atau Q8, **Q10 yang berlaku**. Kode yang ditulis di sini **belum dijalankan di PC**; yang sudah diuji hanya parser PowerShell 7.4.6 (0 galat, hanya karakter ASCII) dan logika potongan baru dengan data tiruan.

## Q10.1 Hasil tes Q9 (doctor, 14:33)

- [x] Semua layanan menyala dan menjawab (VOICEVOX 0.25.2, 9Router, Hermes, server Iris); `WARN` hanya untuk disk C: dan RAM
- [x] Port 50021, 20128, dan 8642 dilayani proses yang sama (`wslrelay`, PID 13200): dugaan Q8 **terbukti**, ketiganya hidup di dalam WSL
- [x] `.env` hanya menampilkan panjang, tidak ada nilai token
- [x] Cmdlet Windows dan PowerShell 5.1 jalan tanpa galat; Z: terbaca bertipe bus NVMe (ADATA LEGEND 860), bukan USB

## Q10.2 Temuan lingkungan

| Hal | Temuan | Dampak |
|---|---|---|
| Hermes dan VOICEVOX | Unit systemd **user** (`hermes-gateway.service`, `voicevox.service`), keduanya `enabled`; `Linger=yes` | Naik sendiri saat WSL boot, tanpa sesi login. Peluncur tidak perlu menyalakannya |
| 9Router | **Bukan** layanan. Proses `node /home/<user>/.nvm/versions/node/v24.15.0/bin/9router`, stdin/stdout ke `/dev/pts/0`, folder kerja `/mnt/c/Users/<user>`, anak dari `bash` di sesi `wsl.exe` (Windows Terminal) | Dijalankan manual di tab terminal. **Tidak naik sendiri** setelah WSL restart; diduga ikut mati kalau tab ditutup. Cocok dengan catatan lama (baris 2301) saat 9Router sempat tidak merespons |
| `voicevox_keepalive.sh` | Skrip lama di `/home/<user>/`; memantau `:50021/version` tiap 30 detik, dan bila tidak menjawab menyalakan **VOICEVOX Windows** (`Z:\voicevox-0.25.2-x64.nsis\VOICEVOX.exe`) | Peninggalan sebelum VOICEVOX pindah ke systemd. Bisa menyalakan VOICEVOX kedua bila mesin Linux lambat naik. Tidak ikut naik setelah restart |
| Disk virtual WSL | `Z:\WSL\Ubuntu\ext4.vhdx`, **51,4 GB** | **Koreksi:** disk virtual WSL ada di **Z:**, bukan C:. Petunjuk "biasanya di C:" pada doctor versi pertama keliru untuk PC ini (sudah diperbaiki). Penyebab C: sempit **belum diketahui** (Q10.7) |
| Docker | Satu kontainer berhenti (`hermes-sandbox:desktop`, sejak 4 minggu lalu). Image: `hermes-sandbox` 4,37 GB (**dipakai**, jangan dihapus), `cincan/binwalk` 774 MB, `hello-world` 26 kB | Yang bisa dibersihkan hanya sekitar 0,8 GB di Z:; tidak menyelesaikan masalah C: |
| Port 80 | Apache (`apache2.service`, 6 proses), bawaan | Tidak terkait Iris; fungsi lain belum diketahui |
| `/etc/wsl.conf` | `systemd=true`; blok `[user]` tampil dua kali | Kemungkinan salah tempel; biasanya tidak berbahaya |
| Proses `npm exec rea-ag...` dan `python3` | Anak dari proses `hermes` (PID 439) | Milik Hermes |
| `server.py` dan overlay | Dua proses Windows terpisah: `server.py` (venv) dan `npm start` (Electron) | Peluncur harus menyalakan **keduanya** |

## Q10.3 Perubahan `iris-doctor.ps1`

- Paket opsional (`faster-whisper`, hanya untuk mic/STT) yang belum terpasang kini `WARN`, bukan `GAGAL`. Paket wajib yang hilang tetap `GAGAL`.
- Bagian baru "6b": letak dan ukuran disk virtual WSL (dari registri `Lxss`), status dan `enabled` unit `hermes-gateway`, `voicevox`, `9router`, status `Linger`, dan apakah `voicevox_keepalive.sh` masih jalan. Semuanya hanya membaca.
- Petunjuk disk: tidak lagi mengaitkan WSL dengan C:. Kalau disk virtual WSL berada di drive yang `WARN`, petunjuk menyebut ukurannya.
- Selama `9router.service` belum dipasang, doctor menampilkan `WARN` untuk 9Router (memang kondisi yang benar saat ini).

## Q10.4 `9router.service` (usulan, belum dipasang)

> **Pembaruan 4 Nov (sore):** draf 3 ini sudah dipasang, lulus tes, dan `enabled`. Hasilnya ada di **Bagian Q11**; bila bertentangan dengan teks "belum dipasang" di bawah, **Q11 yang berlaku**.

Berkas `9router.service` disertakan; salin ke folder proyek. Isinya: jalur Node dan `9router` lengkap (nvm v24.15.0), `WorkingDirectory=%h` (bukan `/mnt/c/...`), `Restart=on-failure`, dan `ExecStart` yang masih berupa penampung (argumen `--no-browser --skip-update`, belum terbukti benar). Port dan alamat ikat sengaja tidak diubah.

**Temuan dari 9Router v0.5.112 (4 Nov, dari `package.json`, `README.md`, dan `cli.js`):**
- Tanpa argumen, `cli.js` menampilkan menu interaktif "Choose Interface" (butuh terminal). Argumen yang ada: `--port/-p`, `--host`, `--no-browser/-n`, `--skip-update`, `--tray/-t`, `--log`, `--help`.
- `cli.js` baris 187 sampai 190 (dibaca 4 Nov): `if (skipUpdate && !trayMode && !process.stdin.isTTY) { trayMode = true; process.env.TRAY_MODE = "1"; }`, dengan komentar "Auto-relaunch after update: detached process has no TTY -> fallback to tray". **Koreksi:** cabang ini bukan mode server tanpa menu, melainkan **memaksa mode tray** saat tanpa terminal. Dugaan awal di sini (cabang itu menjalankan server tanpa menu) **keliru**. Di WSL tidak ada baki sistem, dan perilaku mode tray (mungkin melepas proses anak lalu keluar, yang membuat unit systemd `Type=simple` dianggap selesai) belum diketahui.
- Akibatnya `ExecStart` dengan `--no-browser --skip-update` **tidak dipakai**. Pembacaan lanjutan `cli.js` (4 Nov): server sebenarnya dijalankan di baris 633 sebagai `spawn(RUNTIME, ["--dns-result-order=ipv4first", "--max-old-space-size=6144", serverPath], {...})`, dengan lingkungan yang memuat `PORT` (bawaan 20128) dan `HOSTNAME` (alamat ikat). `serverPath` adalah `app/custom-server.js` bila ada (ada), kalau tidak `app/server.js`. Folder kerja proses yang sedang jalan: `.../node_modules/9router/app`.
- **Rancangan baru (draf 3, siap dites):** unit menjalankan `app/custom-server.js` langsung tanpa `cli.js` (tanpa menu, tanpa tray, tanpa pemeriksaan pembaruan). Lingkungan dibaca dari proses yang sedang jalan (`/proc/1641/environ`): `PORT=20128`, `HOSTNAME=0.0.0.0`, `NODE_PATH=/home/<user>/.9router/runtime/node_modules:/home/<user>/.nvm/versions/node/v24.15.0/lib/node_modules/9router/app/node_modules` (diisi `buildEnvWithRuntime` di `cli.js`; modul sqlite ada di `~/.9router/runtime`), `TRAY_MODE` tidak diatur. Baris 625 sampai 660 dibaca: `spawn` memakai `cwd` = folder `app`, `detached: true`, dan `cli.js` memulai ulang server bila crash (digantikan `Restart=on-failure`). **Belum diketahui:** apakah `buildEnvWithRuntime` mengubah variabel selain `NODE_PATH` (misalnya `PATH`); fungsinya belum dibaca. Pembuktiannya ada di tes Q10.4/Q10.6.
- Data 9Router ada di `~/.9router` (`db`, `auth`, `jwt-secret`, `logs`, `runtime`, dan lainnya), bukan di folder kerja; server Next.js berjalan dengan folder kerja `.../node_modules/9router/app`. Isi `auth`, `db`, dan `jwt-secret` tidak boleh ditempel ke mana pun.
- Alamat ikat `0.0.0.0` bisa diatur lewat `--host` atau variabel `HOSTNAME`. **Jangan diubah** sebelum diketahui apakah sandbox Docker Hermes menjangkau 9Router lewat alamat selain localhost.
- Mode `--tray` tidak berguna di WSL (tidak ada baki sistem).

**Yang belum terbukti:** cara menjalankan 9Router tanpa menu dan tanpa tray di bawah systemd (lihat koreksi di atas). **Jangan memasang unit sebelum itu jelas.** Pemasangan tetap dibuat dengan jalan mundur yang mudah, dan **jangan diaktifkan (`enable`) sebelum lulus tes**. Semua perintah `systemctl`, `journalctl`, dan `wsl` di bawah dijalankan di **PowerShell**, bukan di terminal Ubuntu; di terminal Ubuntu awalan `wsl -d Ubuntu --` dibuang.

Dari folder proyek, di PowerShell (`wsl.exe` memakai folder Windows saat ini sebagai folder kerja):

```
wsl -d Ubuntu -- mkdir -p ~/.config/systemd/user
wsl -d Ubuntu -- cp 9router.service ~/.config/systemd/user/9router.service
wsl -d Ubuntu -- systemctl --user daemon-reload
```

Lalu hentikan 9Router yang manual. **Jangan ada tugas `/agen` yang sedang berjalan** (Hermes memakai 9Router). Di terminal Ubuntu, cek dulu PID-nya masih sama (`ps -o pid,ppid,args -p 1458,1641`; setelah WSL restart PID berubah, cari lewat `pgrep -af next-server`), lalu `kill` proses `cli.js` (1458); kalau `next-server` (1641) masih hidup, `kill` juga. Port 20128 harus kosong (`ss -ltn | grep 20128` tidak mencetak apa-apa), kalau tidak unit tidak bisa mulai. Lalu coba (di PowerShell):

```
wsl -d Ubuntu -- systemctl --user start 9router
wsl -d Ubuntu -- systemctl --user status 9router --no-pager
wsl -d Ubuntu -- journalctl --user -u 9router -n 30 --no-pager
```

Bila lulus (lihat Q10.6), baru `systemctl --user enable 9router`. **Jalan mundur:** `systemctl --user disable --now 9router`, lalu jalankan `9router` manual seperti biasa.

## Q10.5 Rancangan `iris-start.ps1` (belum ditulis)

> **Pembaruan 4 Nov (sore):** `iris-start.ps1` dan `iris-stop.ps1` sudah ditulis dan lulus tes dasar di PC. Lihat **Q11.7**; bila bertentangan dengan teks "belum ditulis" di bawah, **Q11 yang berlaku**.

Dikerjakan setelah Q10.4 lulus, karena peluncur bergantung pada 9Router yang naik sendiri.

1. **Idempoten:** kalau port 8765 sudah dilayani `server.py`, hanya memastikan overlay hidup, tidak membuat server kedua.
2. **WSL:** pastikan Ubuntu berjalan. Bila tes Q10.6 (penjaga) menunjukkan WSL mati saat tidak ada terminal, peluncur membuka satu sesi `wsl.exe` tersembunyi yang menahannya (mis. `sleep infinity`), menggantikan peran `voicevox_keepalive.sh`.
3. **Tunggu tiga layanan** (VOICEVOX `/version`, 9Router `/`, Hermes `/health`) dengan batas waktu; VOICEVOX "All Models" bisa lambat naik. Tidak pernah me-restart Hermes (aturan Q5).
4. **Server:** jalankan `.venv\Scripts\python.exe server.py` tersembunyi dengan log ke berkas di folder proyek (tanpa token), lalu tunggu `/health`.
5. **Overlay:** `npm start` dengan PATH yang memuat Node (`D:\Note`), baru setelah `/health` menjawab.
6. **`iris-stop.ps1`** nanti hanya menghentikan `server.py` dan Electron; WSL dan isinya dibiarkan.

## Q10.6 Tes

- [ ] Doctor versi baru dijalankan: baris `faster-whisper` kini `WARN`; bagian 6b menampilkan `Z:\WSL\Ubuntu\ext4.vhdx` (51,4 GB); `hermes-gateway` dan `voicevox` `OK`; `9router` `WARN` (belum ada unit); Linger `OK`; keepalive `INFO`
- [ ] `9router.service` dipasang dan dijalankan setelah 9Router manual ditutup: `status` menunjukkan `active (running)`, port 20128 menjawab, dan doctor melaporkan `/health ninerouter` dengan model `Iris` seperti sebelumnya (bukti konfigurasi dan combo tidak hilang)
- [ ] Chat biasa dan kirim gambar lewat overlay jalan setelah 9Router dipindah ke unit
- [ ] `systemctl --user enable 9router`, lalu `wsl --shutdown`, buka WSL lagi (satu perintah `wsl` apa saja), tunggu sekitar satu menit: Hermes, VOICEVOX, dan 9Router **naik sendiri** tanpa terminal yang membukanya
- [ ] **Tes penjaga:** tutup semua terminal WSL (termasuk yang menjalankan `voicevox_keepalive.sh`), tunggu 2 menit, lalu `wsl -l -v`: apakah Ubuntu masih `Running` dan ketiga port masih menjawab. Hasilnya menentukan perlu tidaknya sesi penjaga di Q10.5. **Catatan:** tes ini bisa mematikan layanan sementara; jangan dijalankan saat ada tugas `/agen`
- [ ] Setelah semua lulus: `voicevox_keepalive.sh` dipensiunkan (tidak dihapus, hanya tidak dijalankan lagi)

## Q10.7 Yang masih terbuka

- [ ] **Penyebab C: sempit** (13,6 GB bebas, 215 GB terpakai). Bukan disk virtual WSL. Perintah baca-saja untuk mencari (bisa memakan beberapa menit):
  ```
  Get-ChildItem 'C:\Users\<user>' -Force -Directory -ErrorAction SilentlyContinue | ForEach-Object { $s = (Get-ChildItem $_.FullName -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; [pscustomobject]@{ Folder = $_.Name; GB = [math]::Round($s/1GB,1) } } | Sort-Object GB -Descending | Select-Object -First 10
  ```
- [ ] Keputusan `faster-whisper`: pasang (mic jalan, tambahan RAM saat dipakai; model sekitar 150 MB di cache pengguna di C:) atau biarkan sebagai opsional
- [ ] Apache (port 80): mati atau dibiarkan; prioritas rendah
- [ ] 9Router mendengar di `0.0.0.0` (mode NAT, risiko rendah); mengikat ke `127.0.0.1` bergantung pada opsi 9Router yang belum dibaca
- [ ] Image `cincan/binwalk` (774 MB) dan `hello-world`: boleh dihapus kalau tidak dipakai; **jangan** menyentuh `hermes-sandbox`
- [ ] Bagian B ("Windows host untuk: VOICEVOX") sudah usang: VOICEVOX berjalan di WSL sebagai unit systemd
- [ ] Rapikan blok `[user]` ganda di `/etc/wsl.conf` bila memang ada dua di berkasnya
- [ ] Fase 2 (`iris-start.ps1`), Fase 3 (auto-start) dan Fase 4 (setup PC baru) belum ditulis; tes RAM O3 masih menahan Fase 3 (Q7)


# Bagian Q11: `9router.service` lulus tes, token /ws disamakan, venv Linux (4 Nov 2026, sore)

**by: KangJiho**

Bagian ini mencatat hasil pemasangan `9router.service` (draf 3 dari Q10.4) dan dua temuan lingkungan yang muncul saat `server.py` dijalankan dari WSL. Hasil dilaporkan pemilik lewat keluaran terminal dan screenshot. Tidak ada nilai token yang dicatat, hanya panjang dan sidik 6 hex. Bila bertentangan dengan Q10, **Q11 yang berlaku**.

## Q11.1 `9router.service`: hasil

- [x] Draf 3 dipasang tanpa perubahan di `~/.config/systemd/user/9router.service`, lalu `daemon-reload`. Jalur nvm `v24.15.0` masih benar.
- [x] **Percobaan pertama gagal `EADDRINUSE` (port 20128)**, karena `9router` lama masih jalan. Penyebabnya perintah `kill <PID>` yang disalin apa adanya (placeholder tidak diganti angka, bash galat). `Restart=on-failure` membuat unit mencoba ulang tiap 5 detik (counter sampai 6) sampai dihentikan dengan `systemctl --user stop 9router`.
- [x] Setelah `kill` pada `next-server` lama (PID 6020; pembungkus `cli.js` PID 5971 sudah tidak ada) dan `ss -ltnp | grep 20128` kosong, unit naik: `active (running)`, Next.js 16.4.2, `Ready`, mendengar di `0.0.0.0:20128`. `curl -sI http://127.0.0.1:20128` menjawab `307 Temporary Redirect` (wajar, root dialihkan).
- [x] **Tes crash-restart lulus:** `kill -9` pada PID utama (7453), dalam sekitar 5 detik unit hidup lagi dengan PID baru (7539) dan port 20128 terpakai lagi.
- [x] `systemctl --user enable 9router` dan `loginctl enable-linger` berhasil; `is-enabled` menjawab `enabled`.
- [x] **Tes boot dari nol lulus:** `wsl --shutdown` (dari PowerShell), buka WSL lagi: `9router` (PID 388), `hermes-gateway`, dan `voicevox` semuanya `active (running)` dengan waktu mulai yang sama (15:14:07) tanpa terminal yang menyalakannya.
- [x] Pertanyaan terbuka di Q10.4 terjawab: unit yang menjalankan `custom-server.js` langsung, dengan `PORT`, `HOSTNAME`, dan `NODE_PATH` seperti di unit, **cukup**. Tidak perlu `cli.js`, dan tidak ada variabel tambahan dari `buildEnvWithRuntime` yang ternyata dibutuhkan.
- [x] Chat biasa lewat halaman tes Fase 1 menjawab (teks dengan `[happy]` dan terjemahan Jepang) setelah 9Router berpindah ke unit (15:20).

## Q11.2 Tes Q10.6 yang belum

- [ ] Kirim gambar lewat overlay setelah 9Router pindah ke unit (chat teks sudah, gambar belum)
- [ ] Chat lewat **overlay Electron** (bukan halaman tes): koneksi `/ws` dari overlay sudah `accepted` dengan riwayat 20 pesan, tetapi balasan dari overlay belum dikonfirmasi
- [ ] Doctor versi baru (`iris-doctor.ps1`) belum dijalankan ulang; harapannya `9router` kini `OK`, bukan `WARN`
- [ ] Tes penjaga (tutup semua terminal WSL, tunggu 2 menit, `wsl -l -v`) belum dilakukan
- [ ] `voicevox_keepalive.sh` belum dipensiunkan. Baris `[1]+ Done pgrep -f voicevox_keepalive.sh ...` muncul **setiap WSL dibuka**, jadi skrip itu kemungkinan dipanggil dari `~/.bashrc`; belum dicek
- [ ] Opsional: `HOSTNAME=127.0.0.1` di unit (sekarang masih `0.0.0.0`, sengaja). Syarat: server.py memanggil 9Router lewat `127.0.0.1` atau `localhost`, dan sandbox Docker Hermes tidak butuh alamat lain (lihat Q10.4)

## Q11.3 Token /ws: dua `.env`, dua token

**Temuan:** ada **dua** `.env` yang dibaca berbeda.

| Sisi | Berkas | Dibaca oleh |
|---|---|---|
| Electron (Windows) | `C:\Users\<user>\.env` | `main.js`: variabel environment dulu, lalu `~\.env`, lalu `.env` di folder proyek |
| `server.py` jalan dari WSL | `/home/<user>/.env` | `server.py`: `Path.home() / ".env"`, lalu `.env` di folder kerja |

`Path.home()` di WSL berbeda dari di Windows, jadi `server.py` yang dijalankan dari WSL **tidak membaca** `.env` Windows.

Urutan kejadian:
- Server dari WSL naik dengan peringatan `COMPANION_TOKEN kosong` (`~/.env` WSL tidak berisi token).
- Token acak 64 karakter (sidik `c461aa`) dibuat ke `~/.env` WSL. Electron tetap memakai token lama di `.env` Windows (**43 karakter, sidik `<hex>`**), jadi overlay ditolak (`Token beda`).
- **Perbaikan:** token Windows disalin ke `~/.env` WSL (panjang 43 dicek sebelum ditulis, isi tidak dicetak); token 64 karakter dihapus. Server kini mencetak `Token /ws server: 43 karakter, sidik <hex>`, sama dengan terminal Electron, dan `/ws` dari overlay `accepted`.
- Setelah token terpasang, halaman tes browser (`localhost:8765` atau `127.0.0.1:8765`) **selalu ditolak** (`header X-Iris-Token tidak ada`): browser tidak bisa menempelkan header itu. Normal; tes lewat overlay. Tab yang dibiarkan terbuka mencoba menyambung ulang terus dan memenuhi log.
- **Catatan:** `.env` di folder proyek bisa terbuat kosong atau berisi sisa baris token (perintah `>> .env` dan `sed -i` sempat menyentuhnya). `main.js` memakai `C:\Users\<user>\.env` lebih dulu, jadi tidak berpengaruh; cek isinya dan hapus kalau hanya sisa.
- Cara cek cepat bila overlay ditolak: samakan sidik di baris `Token /ws server` (terminal `server.py`) dengan baris `Token /ws` (terminal `npm.cmd start`).

## Q11.4 `server.py` dari WSL: menyimpang dari rancangan

Rancangan di Q10.5 dan di "Cara menjalankan" (Bagian A) menjalankan `server.py` dari **Windows** (`.venv\Scripts\python.exe server.py`, Python Microsoft Store 3.11.9). Sore ini `server.py` dijalankan dari **WSL**, hanya sebagai jalan pintas tes:

- `.venv` di folder proyek adalah venv Windows (isi `Include`, `Lib`, `Scripts`, `pyvenv.cfg`) dan tidak bisa diaktifkan di WSL (`.venv/bin/activate` tidak ada).
- Venv Linux dibuat di `~/iris-venv` (Python 3.14): `source ~/iris-venv/bin/activate`, `pip install -r requirements.txt` (termasuk `faster-whisper` 1.2.1, jadi `WARN` doctor untuk `faster-whisper` hanya berlaku untuk venv Windows), lalu `python server.py`.
- Di WSL `python` hanya ada di dalam venv; di luarnya hanya `python3`.
- `server.py` dari WSL membaca `~/.env` WSL, **bukan** `.env` Windows. Isi `~/.env` WSL selain token tidak dicatat dan belum dibandingkan dengan `.env` Windows (`HERMES_API_KEY`, `HERMES_URL`, `NINEROUTER_API_KEY`, dan lainnya).
- **Keputusan (4 Nov, sore): server dari Windows** (saran diberikan, lalu peluncur dijalankan dengan jalur ini). `server.py` di WSL sudah dihentikan (`Ctrl+C`); `iris-start.ps1` menjalankannya dari `.venv\Scripts\python.exe` dan membaca `C:\Users\<user>\.env`, sama dengan Electron, jadi tidak ada lagi dua `.env`. `~/iris-venv` dan `~/.env` di WSL kini tidak dipakai; boleh dibuang (`rm -rf ~/iris-venv`; hapus baris `COMPANION_TOKEN` di `~/.env`), belum dilakukan. Jangan menjalankan dua `server.py` sekaligus (port 8765 sama).

## Q11.5 Catatan kecil

- `wsl` membuka dengan peringatan `Duplicated config key 'user.default' in /etc/wsl.conf:7 (Conflicting key ... :5)`: **bukan** blok `[user]` ganda, melainkan kunci `default` muncul dua kali (baris 5 dan 7). Isi kedua baris belum dilihat. Menggantikan dugaan di Q10.7; perbaikan: `sudo nano /etc/wsl.conf`, hapus satu baris, berlaku setelah `wsl --shutdown`.
- `Duduk (PowerShell): #< CLIXML` tercetak di terminal Electron saat start: keluaran progres PowerShell (CLIXML) dari fitur duduk bocor ke stdout. Tidak mengganggu token. Belum diselidiki; kalau fitur duduk bermasalah, mulai dari sini.
- `npm start` di PowerShell gagal karena aturan eksekusi skrip; pakai `npm.cmd start`.
- Perintah `Get-Content` dan `Select-String` hanya ada di PowerShell; di terminal Ubuntu jawabannya `command not found`.
- Perintah dengan `<PID>` atau tanda `<...>` lain tidak boleh disalin apa adanya: ganti dulu dengan nilai sebenarnya.

## Q11.6 Urutan berikutnya

1. Konfirmasi di layar: overlay muncul dan Iris membalas chat setelah dijalankan lewat `iris-start.ps1` (lihat Q11.7), lalu kirim gambar.
2. Jalankan ulang `iris-doctor.ps1`; periksa `9router` (harusnya `OK`) dan Linger.
3. Tes penjaga (Q10.6): hasilnya baru murni bila sesi penjaga `sleep infinity` dihentikan dulu (`iris-stop.ps1 -HentikanPenjaga`), lalu tutup semua terminal WSL, tunggu 2 menit, `wsl -l -v`. Kalau ketiga port masih menjawab, penjaga tidak diperlukan; kalau tidak, penjaga tetap dipakai. Setelah itu pensiunkan `voicevox_keepalive.sh` (cek `~/.bashrc` dulu).
4. Fase 3: `iris-autostart.ps1 -On/-Off` (bawaan mati), menunggu tes RAM O3 (Q7).
5. Rapikan sisa: kunci `default` ganda di `/etc/wsl.conf`, `.env` kosong di folder proyek, tab browser halaman tes yang membuat log `/ws ditolak` ramai.

## Q11.7 `iris-start.ps1` dan `iris-stop.ps1`: ditulis dan dites (4 Nov 2026, sore)

Dua berkas ditaruh di akar folder proyek (sejajar dengan `server.py`). Hanya ASCII (aman di Windows PowerShell 5.1). Sebelum dijalankan di PC, hanya diperiksa manual; tidak ada parser PowerShell di sisi pembuat.

**`iris-start.ps1`** (opsi: `-Distro`, `-TungguDetik`, `-TanpaPenjaga`, `-TanpaOverlay`, `-Proyek`):
1. Memastikan WSL hidup; membuka sesi penjaga tersembunyi `wsl.exe -d Ubuntu -- sleep infinity` bila belum ada (bawaan **hidup**, karena tes penjaga belum dilakukan; menggantikan peran `voicevox_keepalive.sh` bila terbukti perlu).
2. Memeriksa VOICEVOX (`:50021/version`), 9Router (`:20128/`), dan Hermes (`:8642/health`); hanya yang **tidak menjawab** di-`systemctl --user start`. Tidak pernah me-restart Hermes (aturan Q5). Kode HTTP apa pun berarti hidup.
3. Menjalankan `server.py` dari `.venv\Scripts\python.exe -u` tersembunyi, menunggu `http://127.0.0.1:8765/health` (maksimal 60 detik); bila port sudah menjawab, tidak membuat server kedua.
4. Menjalankan `node_modules\electron\dist\electron.exe .` tersembunyi (tanpa `npm`, jadi tidak bergantung pada PATH Node); bila `electron.exe` dari folder proyek sudah jalan, tidak membuat overlay kedua.
5. Log: `iris-start.log` dan keluaran `server.py` dan overlay ke `iris-server.out.log`, `iris-server.err.log` (log uvicorn ada di sini), `iris-overlay.out.log`, `iris-overlay.err.log`. Tidak memuat token (hanya panjang dan sidik), **tetapi log server memuat teks chat**, jangan dibagikan sembarangan.

**`iris-stop.ps1`** (`-HentikanPenjaga` opsional): menghentikan `electron.exe` dari folder proyek dan proses yang mendengar di `:8765` (dipastikan baris perintahnya memuat `server.py`, lalu `taskkill /T /F`). WSL, 9Router, Hermes, VOICEVOX, dan sesi penjaga dibiarkan.

> **Pembaruan 4 Nov (malam):** perilaku `iris-stop.ps1` di bawah (WSL, Hermes, 9Router, VOICEVOX dibiarkan hidup) sudah **diganti**, dan `iris-start.ps1` kini menyalakan layanan secara paralel. Lihat **Q11.9**; bila bertentangan, **Q11.9 yang berlaku**.

**Cara menjalankan** (PowerShell Windows, dari folder proyek):
```
powershell -ExecutionPolicy Bypass -File .\iris-start.ps1
powershell -ExecutionPolicy Bypass -File .\iris-stop.ps1
```

**Hasil tes (dilaporkan pemilik, keluaran PowerShell, 15:42 sampai 15:43):**
- [x] Berkas sampai utuh di folder proyek (5811 dan 1746 byte, sama dengan aslinya)
- [x] Start pertama: WSL hidup, penjaga dibuka, ketiga layanan "sudah menjawab", `server.py` siap dalam 5 detik, overlay dijalankan, tanpa galat
- [x] Token cocok: sidik `<hex>` di `iris-server.out.log` dan `iris-overlay.out.log` (Electron membaca `C:\Users\<user>\.env`)
- [x] Idempoten: jalan kedua mencatat "Sesi penjaga WSL sudah ada", "server.py sudah menjawab di :8765 (tidak membuat server kedua)", "Overlay sudah jalan"
- [x] Stop: "Overlay dihentikan", "server.py dihentikan"
- [x] Start ulang setelah stop: naik normal dalam sekitar 5 detik
- [ ] **Belum dikonfirmasi:** overlay benar-benar tampil di layar dan Iris membalas chat setelah dijalankan lewat peluncur (log hanya membuktikan proses hidup), plus kirim gambar
- [ ] Peluncur dari keadaan dingin (setelah `wsl --shutdown` atau reboot): VOICEVOX naik lambat ("All Models"), batas 90 detik per layanan belum teruji
- [ ] `iris-doctor.ps1` dijalankan ulang setelah peluncur

**Catatan:**
- Satu baris `ditolak` di log server saat start berasal dari tab browser halaman tes yang masih terbuka (`Origin: http://127.0.0.1:8765`), bukan dari overlay. Tutup tab itu.
- Kesalahan ketik yang sempat terjadi: tanda `]` ikut terketik di akhir `iris-stop.ps1]`, jadi ditolak. Berkas yang diunduh dari kartu sempat tidak ditemukan di `Downloads` karena browser menyimpannya langsung di folder proyek.

## Q11.8 Tinjauan `iris-doctor.ps1` dan pembungkus `.bat` (4 Nov 2026, sore)

**Tinjauan berkas (pemilik mengunggah ulang ketiga `.ps1`):**
- `iris-start.ps1` (5811 byte) dan `iris-stop.ps1` (1746 byte): identik dengan yang ditulis (dibandingkan isinya); sudah lulus tes di PC (Q11.7).
- `iris-doctor.ps1` (537 baris, hanya ASCII, hanya membaca) dibaca penuh. Tidak ada bug yang menghalangi. Cocok dengan keadaan sekarang: unit `9router` dikenali (kini harusnya `OK`, bukan `WARN`), Linger dicek, tidak ada token yang dicetak (hanya panjang dan nama variabel), dan `server.py` dari WSL dilaporkan `GAGAL` ("dipakai proses lain", port dipegang `wslrelay`), yang memang perilaku yang benar.
- Dua kekurangan kecil, **belum diperbaiki** (menunggu persetujuan pemilik):
  - [ ] `node` tidak ada di PATH diberi `GAGAL`, padahal peluncur memakai `electron.exe` langsung dan tidak butuh Node (hanya `npm install` yang butuh). Sebaiknya `WARN`.
  - [ ] Doctor hanya mengecek `voicevox_keepalive.sh`; sesi penjaga `sleep infinity` dari peluncur tidak dilaporkan. Sebaiknya `INFO`.
- [ ] Doctor belum dijalankan setelah peluncur. Harapan: `9router` unit `OK`, Linger `OK`, server Iris jalan di 8765 `OK`, `WARN` hanya untuk disk C: dan (bila venv Windows tanpa paket) `faster-whisper`.

**Pembungkus `.bat` (klik dua kali, tanpa membuka PowerShell):**

| Berkas | Menjalankan | Jendela |
|---|---|---|
| `Iris Start.bat` | `iris-start.ps1` | menutup sendiri setelah 6 detik |
| `Iris Stop.bat` | `iris-stop.ps1` | menutup sendiri setelah 4 detik |
| `Iris Doctor.bat` | `iris-doctor.ps1` | menunggu tombol (`pause`) supaya hasil terbaca |

- Ditaruh di akar folder proyek, sejajar dengan `.ps1`-nya. Isi tiap `.bat`: `cd /d "%~dp0"` lalu `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0<berkas>.ps1"` (akhiran baris CRLF). Tidak mengubah kebijakan eksekusi mesin (hanya untuk proses itu, aturan Q5).
- Tips: klik kanan `Iris Start.bat` lalu Send to, Desktop (create shortcut) untuk menyalakan dari desktop. SmartScreen bisa memberi peringatan pada file `.bat` hasil unduhan (More info, Run anyway).
- [ ] **Belum dites di PC:** klik dua kali ketiga berkas (terutama jalur dengan spasi dan drive `Z:`).

**Klarifikasi cakupan peluncur:** `iris-start.ps1` menyalakan overlay Iris **dan** memastikan Hermes (unit `hermes-gateway`) hidup, tetapi Hermes tidak pernah di-restart. Hermes biasanya sudah naik sendiri saat WSL boot (systemd + Linger), jadi peluncur umumnya hanya mencatat "Hermes sudah menjawab". Obrolan biasa lewat `server.py` dan 9Router; `/agen ...` diteruskan `server.py` ke Hermes. Jalur lain Hermes (mis. Telegram) tidak lewat peluncur. Cara membuktikan jembatan Hermes lewat peluncur: setelah overlay muncul, jalankan tugas ringan seperti `/agen siapa kamu`.

**Urutan berikutnya (menggantikan Q11.6 bila ada beda):**
1. Klik `Iris Start.bat`; konfirmasi overlay tampil, Iris membalas chat, kirim gambar, dan `/agen siapa kamu` terbaca.
2. Jalankan `Iris Doctor.bat`; tempel keluaran bila ada `GAGAL`.
3. Setujui atau tolak dua perbaikan kecil doctor di atas.
4. Tes dingin: `wsl --shutdown`, lalu `Iris Start.bat` (VOICEVOX "All Models" bisa lambat naik).
5. Fase 3 (`iris-autostart.ps1`, bawaan mati), menunggu tes RAM O3 (Q7).


## Q11.9 Hermes masih hidup setelah Stop: saklar Hermes dan WSL, peluncur paralel, Stop penuh (4 Nov 2026, malam)

**Pemicu.** Pemilik heran Hermes masih hidup setelah menekan `Iris Stop.bat`. Itu bukan bug: sesuai rancangan Q10.5 no. 6 dan Q11.7, `iris-stop.ps1` hanya mematikan overlay dan `server.py`; WSL, Hermes, 9Router, dan VOICEVOX sengaja dibiarkan (alasan: skrip tidak bisa tahu apakah ada tugas `/agen` yang sedang jalan, aturan Q5). Dua screenshot Task Manager: `VmmemWSL` sekitar 819 MB dengan memori sistem 71 persen, lalu sekitar 1.039 MB dengan 74 persen. `VmmemWSL` adalah seluruh mesin WSL, bukan Hermes, jadi angkanya tidak membuktikan Hermes hidup atau mati, dan tidak turun banyak sebelum WSL dimatikan (`wsl --shutdown`). Cara cek Hermes langsung: `wsl -d Ubuntu -- systemctl --user is-active hermes-gateway`.

**Berkas (semua hanya ASCII, ditaruh di akar folder proyek):**

| Berkas | Fungsi |
|---|---|
| `iris-hermes.ps1` + `Iris Hermes.bat` | Saklar **Hermes dan WSL saja**, tanpa menyentuh overlay dan `server.py`. Satu klik: bila Hermes (`:8642/health`) menjawab, dimatikan; bila tidak, dinyalakan |
| `Iris Hermes Mati.bat` | Memanggil `iris-hermes.ps1 -Matikan`: selalu mematikan, tanpa melihat status |
| `iris-start.ps1` (diubah) | Layanan WSL yang belum menjawab di-start **sekaligus** |
| `iris-stop.ps1` (diubah) | Kebalikan Start: mematikan semuanya |

**`iris-hermes.ps1`** (opsi: `-Nyalakan`, `-Matikan`, `-TanpaPenjaga`, `-Distro`, `-TungguDetik`):
- Mati: `systemctl --user stop hermes-gateway`, hentikan sesi penjaga WSL, lalu `wsl --shutdown`. 9Router dan VOICEVOX ikut mati karena WSL-nya mati.
- Nyala: bangunkan WSL, buka sesi penjaga bila belum ada, `systemctl --user start hermes-gateway`, tunggu `/health` (bawaan 90 detik). 9Router dan VOICEVOX diharapkan naik sendiri bersama WSL (unit `enabled`, tes boot dari nol di Q10 lulus).
- Versi pertama diam sampai langkahnya selesai: pemilik melihat jendela `cmd` hitam kosong. **Dugaan (belum dikonfirmasi):** `systemctl stop` menunggu Hermes menutup diri (bawaan systemd sampai sekitar 90 detik). Sudah ditambah pesan progres per langkah. Bila jendela masih kosong lebih dari 2 menit, curigai `wsl.exe` macet; cek dengan `wsl -d Ubuntu -- systemctl --user status hermes-gateway --no-pager`.

**`iris-start.ps1` (paralel).** Urutan lama: tiap layanan di-start dan ditunggu satu per satu (VOICEVOX "All Models" yang lambat menahan Hermes, `server.py`, dan overlay). Urutan baru: (1) cek WSL dan penjaga, (2) kumpulkan layanan yang belum menjawab dan start semuanya dalam satu perintah `systemctl --user start --no-block ...`, (3) `server.py` dan (4) overlay langsung dijalankan, (5) baru menunggu layanan tadi, sisa waktu dihitung dari `-TungguDetik`. Aturan tidak berubah: yang sudah menjawab tidak disentuh, Hermes tidak pernah di-restart, idempoten. **Efek samping:** overlay bisa tampil sebelum Hermes dan VOICEVOX siap, jadi chat atau suara di detik-detik pertama bisa gagal sebentar.

**`iris-stop.ps1` (penuh).** Urutan mati, terbalik dari Start: overlay, `server.py`, lalu `systemctl --user stop hermes-gateway 9router voicevox` (hanya bila WSL memang sedang jalan; WSL tidak dibangunkan hanya untuk dimatikan), sesi penjaga, dan `wsl --shutdown`. Opsi `-TanpaWSL` mengembalikan perilaku lama (hanya overlay dan `server.py`). `-HentikanPenjaga` dipertahankan untuk tes penjaga Q10.6: bersama `-TanpaWSL`, penjaga dihentikan dan WSL tetap hidup. `Iris Stop.bat` dan `Iris Start.bat` tidak berubah.

**Yang digantikan:** teks Q11.7 "`iris-stop.ps1`: WSL, 9Router, Hermes, VOICEVOX, dan sesi penjaga dibiarkan" (kini hanya berlaku dengan `-TanpaWSL`); Q11.7 "Tes penjaga": perintahnya tetap `iris-stop.ps1 -TanpaWSL -HentikanPenjaga`.

**Aturan Q5:** "tidak pernah me-restart Hermes" masih berlaku untuk `iris-start.ps1`. `iris-hermes.ps1` dan `iris-stop.ps1` penuh sengaja mematikan Hermes atas permintaan pemilik; keduanya **tidak** memeriksa apakah ada tugas `/agen` yang sedang jalan, jadi tugas itu ikut terputus bila skrip dijalankan saat Hermes sibuk.

**Status uji: semuanya ditulis, belum dites di PC.** Tidak ada parser PowerShell di sisi pembuat; hanya diperiksa manual dan dicek hanya berisi ASCII. Satu-satunya pengamatan dari PC: jendela kosong pada `Iris Hermes.bat` versi pertama (di atas).
- [ ] `Iris Hermes.bat` dari kondisi nyala: pesan progres muncul, Hermes mati, `VmmemWSL` hilang dari Task Manager.
- [ ] `Iris Hermes.bat` dari kondisi mati: WSL naik, Hermes menjawab `/health`, 9Router dan VOICEVOX ikut naik sendiri.
- [ ] `Iris Hermes Mati.bat`: mematikan, juga saat Hermes sudah mati.
- [ ] `iris-start.ps1` paralel dari keadaan dingin (setelah `wsl --shutdown`): ketiga layanan naik dan overlay berfungsi setelah layanan siap; bandingkan waktu total dengan versi lama.
- [ ] `iris-stop.ps1` penuh: urutan benar, tidak membangunkan WSL bila sudah mati, `VmmemWSL` hilang.
- [ ] `iris-stop.ps1 -TanpaWSL`: hanya overlay dan `server.py` yang mati.
- [ ] Belum diperiksa: apakah unit `hermes-gateway` punya ketergantungan pada `9router` di systemd. Bila ya, `--no-block` aman; bila tidak, Hermes mungkin sempat gagal terhubung ke 9Router sebelum 9Router siap, lalu bergantung pada percobaan ulang Hermes.

## Q11.10 Perbaikan `iris-start.ps1` dan `IrisLauncher.exe` versi 1.0 (4 Nov 2026, sore)

**Gejala.** Di `IrisLauncher.exe`, tombol Start berhenti di langkah pertama dengan log `GAGAL WSL Ubuntu tidak bisa dijalankan: w` lalu `--- selesai (kode 1) ---`. Pada saat yang sama Doctor menyatakan `Ubuntu berjalan (WSL2)`, jadi WSL sebenarnya hidup.

**Penyebab.** `wsl.exe` menulis peringatan ke stderr dalam UTF-16. `iris-start.ps1` memakai `$ErrorActionPreference = 'Stop'`, dan di Windows PowerShell 5.1 itu mengubah keluaran stderr dari perintah native menjadi galat fatal, walaupun ditulis `2>$null`. Pesan galatnya berisi karakter nol UTF-16, sehingga log terpotong setelah huruf pertama (`w`). Doctor tidak kena karena memakai `Continue`. `iris-hermes.ps1` dan `iris-stop.ps1` tidak memasang `Stop`, jadi tidak terpengaruh.

**Perbaikan di `iris-start.ps1` (v1.0).**
- Pengecekan WSL (`wsl.exe -d Ubuntu -- true`) dijalankan dengan `Continue`, keluarannya digabung (`2>&1`), karakter nol dibuang, dan dicoba sampai 3 kali dengan jeda 3 detik. Bila tetap gagal, log memuat kode keluar dan teks asli dari `wsl.exe`.
- Perintah `systemctl --user start --no-block ...` juga dibungkus `Continue` supaya tidak terputus oleh peringatan serupa.
- Header skrip dipangkas dan diberi tulisan `v1.0`; perilaku selain dua hal di atas tidak berubah (idempoten, tanpa token di log, Hermes tidak pernah di-restart).

**Tentang `IrisLauncher.exe`.** Aplikasi ini perakitan .NET; skrip `iris-start.ps1`, `iris-stop.ps1`, `iris-hermes.ps1`, dan `iris-doctor.ps1` tertanam di dalamnya. Akibatnya, mengganti berkas `.ps1` di folder proyek **tidak** mengubah perilaku tombol di peluncur; yang menjalankan Start dari `.bat` memakai berkas di folder. Karena kode sumber (`IrisLauncher-src.zip`) tidak ada di sisi pembuat, exe ditambal langsung (bukan di-build ulang): skrip start yang tertanam diganti dengan versi baru yang panjangnya tepat sama, dan versi diubah.

**Versi 1.0.** Versi File dan Versi Produk di properti exe, serta versi assembly, kini `1.0.0.0` (sebelumnya `0.0.0.0`). Judul jendela masih `Iris Launcher` tanpa angka; menampilkannya perlu build ulang dari sumber.

**Hasil di PC (screenshot pemilik, 16:49:31 sampai 16:50:00): lulus.** Start selesai dengan kode 0 dan semua indikator hijau (WSL, VOICEVOX, 9Router, Hermes, server.py, Overlay). Urutan log: WSL hidup, sesi penjaga dibuka, 9Router sudah menjawab, VOICEVOX dan Hermes di-start sekaligus, `server.py` siap setelah 7 detik, overlay dijalankan, lalu VOICEVOX dan Hermes naik; total sekitar 29 detik. Ini juga menjadi bukti pertama bahwa Start paralel (Q11.9) berjalan di PC. Catatan: WSL sudah hidup sebelum tes, jadi ini **bukan** tes dari keadaan dingin.

**Catatan lain dari keluaran Doctor (16:43).** VOICEVOX sempat `GAGAL` karena memang belum dinyalakan saat itu. RAM sistem terpakai 96% dari 15,7 GB (WSL sekitar 5,5 GB); drive C: bebas 13,2 GB (5,8%). `.wslconfig` belum ada, jadi memori WSL belum dibatasi.

- [x] `iris-start.ps1` paralel dengan WSL sudah hidup: lulus (di atas).
- [ ] `iris-start.ps1` paralel dari keadaan dingin (setelah `wsl --shutdown`), dan bandingkan waktunya dengan versi lama.
- [ ] Penyebab peringatan stderr `wsl.exe` belum diketahui (teksnya tidak tertangkap); log versi baru akan mencatatnya bila Start gagal lagi.
- [ ] Judul jendela peluncur belum memuat versi.

## Q12 `.wslconfig` dipasang, sparse VHD ditolak, koreksi lokasi disk (4 Nov 2026)

**Hasil di PC (keluaran PowerShell dari pemilik).**

| Hal | Hasil | Catatan |
|---|---|---|
| Kondisi awal | C: bebas 13,1 GB; Z: bebas 71,1 GB; `vmmemWSL` 239 MB | 239 MB diambil saat WSL sedang menganggur, jadi **bukan** pembanding beban penuh (sebelumnya WSL tercatat 2,4 sampai 5,5 GB saat dipakai) |
| `.wslconfig` dibuat | **lulus** | Isi: `[wsl2]` `memory=5GB`, `swap=2GB`; `[experimental]` `autoMemoryReclaim=gradual`, `sparseVhd=true`. Dibuat dengan `Set-Content -Encoding ascii` |
| Batas memori aktif | **lulus** | `free -m` di Ubuntu: total 4.916 MB, swap 2.048 MB |
| `wsl --manage Ubuntu --set-sparse true` | **ditolak WSL** | Pesan: dukungan sparse VHD sedang dinonaktifkan karena risiko kerusakan data; hanya bisa dipaksa dengan `--allow-unsafe` (kode `Wsl/Service/E_INVALIDARG`). **Keputusan: tidak dipaksa** (lihat di bawah) |
| Lokasi `ext4.vhdx` lewat `LOCALAPPDATA\Packages` | tidak ditemukan | Cocok dengan Q10.2: disk WSL ada di `Z:\WSL\Ubuntu\ext4.vhdx` |
| Ukuran `~\.ollama` | 0,0 GB | Tidak ada model Ollama di profil Windows; bukan sumber penuhnya C: |
| Peringatan `Duplicated config key 'user.default' in /etc/wsl.conf:7 (Conflicting key ... :5)` | muncul lagi saat `wsl -d Ubuntu -- free -m` | Masih terbuka (Q11.5) |

**Keputusan sparse VHD.** Tidak memakai `--allow-unsafe`. Disk WSL ada di Z: yang masih bebas 71,1 GB, dan sparse tidak menolong C:, jadi manfaatnya kecil dibanding risiko kerusakan data. Baris `sparseVhd=true` di `.wslconfig` boleh dibiarkan (hanya berlaku untuk disk yang baru dibuat) atau dihapus; tidak berpengaruh pada Ubuntu yang ada.

**Koreksi atas tutorial sebelumnya.**
- Tutorial "bersihkan C:" menganggap disk virtual WSL ada di C:. Itu keliru untuk PC ini (lihat Q10.2: Z:). Membersihkan atau mengecilkan disk WSL **tidak** menambah ruang C:. Penyebab C: sempit (sekitar 215 GB terpakai) **masih belum diketahui**; perintah baca-saja pencarinya ada di Q10.7.
- Bagian O3 menaruh `autoMemoryReclaim` di `[wsl2]`. Tempat yang benar adalah `[experimental]` (sama dengan `sparseVhd`).
- Catatan lama "C: dan Z: sama-sama 93% penuh" (Bagian B, D, F5) sudah usang: Z: kini bebas 71,1 GB.
- `autoMemoryReclaim=gradual` mensyaratkan cgroup v1 dimatikan di WSL, yang di beberapa layanan bisa menimbulkan masalah. Kalau ada layanan WSL yang aneh setelah ini, hapus baris itu dulu.

**Kaitan dengan Q11.10.** Peringatan stderr `wsl.exe` yang tidak tertangkap di Q11.10 sangat mungkin adalah peringatan `Duplicated config key` di atas (muncul setiap `wsl` dijalankan). Belum terbukti; kalau kunci ganda di `/etc/wsl.conf` dirapikan dan peringatannya hilang, dugaan ini terjawab.

**Belum dilakukan.**
- [ ] Start lewat Launcher dengan batas 5 GB, lalu cek indikator hijau (WSL, VOICEVOX, 9Router, Hermes, `server.py`, Overlay) dan satu tugas `/agen` ringan. Catat apakah Hermes atau VOICEVOX tersendat atau mati sendiri (kalau ya: naikkan ke `memory=6GB`).
- [x] Bandingkan RAM sistem dan `VmmemWSL` saat dipakai (sebelumnya 96% dan sekitar 5,5 GB). Selesai di Q13: batas akhir 4 GB, RAM Windows 79% dengan Chrome ditutup.
- [x] (Selesai 4 Nov 2026, lihat Q13.1) Rapikan kunci `default` ganda di `/etc/wsl.conf`: `wsl -d Ubuntu -- cat -n /etc/wsl.conf` untuk melihat isinya, lalu hapus satu baris, lalu `wsl --shutdown`.
- [ ] Cari penyebab C: sempit (Q10.7); bisa dengan WinDirStat atau TreeSize Free.
- [ ] Pantau beberapa hari apakah "Iris ngilang" dan lag berkurang; kalau tidak, penyebabnya mungkin bukan memori WSL.


## Q13 Batas memori WSL diturunkan ke 4 GB dan ditetapkan final (4 Nov 2026)

**Latar.** Dengan batas 5 GB (Q12), puncak pemakaian WSL terukur 4,2 GB dan RAM sistem Windows 96 sampai 98% (peramban masih terbuka). Dicoba dua batas lebih kecil, dengan pemantauan `free -m` tiap 10 detik setelah `wsl --shutdown` dan Iris dijalankan.

**Hasil ukur WSL (`free -m`, Iris berjalan).**

| Batas | used (stabil) | available (stabil) | swap terpakai | Catatan |
|---|---|---|---|---|
| 3 GB | sekitar 2.725 MB dari 2.906 MB | 180 sampai 184 MB | sekitar 950 MB | Memori fisik habis, banyak dipindah ke swap di disk. Angka berhenti naik, jadi tidak ada lingkaran kehabisan memori, tapi satu lonjakan (mis. VOICEVOX menyintesis kalimat panjang) bisa memicu proses dibunuh. Swap sebesar itu biasanya terasa sebagai suara telat dan `/agen` lambat |
| 4 GB | sekitar 3.600 MB dari 3.914 MB | sekitar 300 MB (terendah 113 MB, sampel akhir 390 MB) | 108 MB | Mendatar setelah sampel ke-3, tanpa tren naik. Margin tipis tapi cukup untuk pemakaian normal |

Kebutuhan nyata Iris sekitar 3,5 sampai 4 GB. Swap turun dari sekitar 950 MB ke 108 MB, itu perubahan terpenting.

**Hasil ukur Windows (RAM sistem terpakai).**

| Kondisi | Hasil | Catatan |
|---|---|---|
| WSL 3 GB, peramban ditutup | 74% | Penurunan dari 96 sampai 98% campuran dua hal (peramban ditutup dan WSL dibatasi), tidak bisa dipisahkan |
| WSL 4 GB, WSL baru dimulai | 64% | **Tidak dipakai**: WSL belum terisi penuh saat diukur |
| WSL 4 GB, Iris berjalan, Chrome terbuka | 89% lalu 91% | Di atas batas 90% |
| WSL 4 GB, Iris berjalan, **Chrome ditutup** | **79%** | Angka acuan |

Pemakai RAM terbesar saat 91% (`Get-Process`, MB): `vmmemWSL` 1.908, `electron` 821, Memory Compression 608, `svchost` 495, `electron` 424, `chrome` 384, `msedgewebview2` 348, `chrome` 309. `vmmemWSL` lebih kecil dari `used` di dalam WSL (sekitar 3.600 MB) karena `autoMemoryReclaim=gradual` mengembalikan cache ke Windows, jadi hanya perkiraan bawah. Penyebab utama 91% ternyata Chrome yang masih terbuka, bukan batas WSL.

**Cek OOM.** `wsl -d Ubuntu -u root dmesg | Select-String -Pattern "oom|killed process"` **tidak menghasilkan baris apa pun**, artinya tidak ada proses yang dibunuh kernel. Catatan: versi dengan `sudo` menggantung karena minta password (keluaran di-pipe), jadi pakai `-u root`.

**Keputusan.** `.wslconfig` final:

```
[wsl2]
memory=4GB
swap=2GB

[experimental]
autoMemoryReclaim=gradual
sparseVhd=true
```

Syarat pemakaian: **tutup Chrome saat Iris berjalan.** Kalau Chrome dibuka lagi, RAM Windows kembali ke sekitar 90%.

**Kapan ditinjau ulang.**
- VOICEVOX tersendat atau suara telat: ukur ulang `free -m`; swap yang naik lagi berarti margin 300 MB mulai terpakai.
- Windows terasa lambat padahal Chrome tertutup: coba 3,5 GB, dengan risiko swap naik lagi.
- Ada baris `oom` atau `killed process` di dmesg: naikkan ke 4,5 GB atau kurangi beban di sisi Iris.

**Belum dilakukan.**
- [~] Indikator V, 9, H hijau di batas 4 GB (screenshot 21:04, lihat Q13.2). Kelancaran suara Iris **belum dikonfirmasi**.
- [x] Satu tugas `/agen` ringan di batas 4 GB: `/agen halo` selesai tanpa tersendat (lihat Q13.2).
- [ ] Pantau beberapa hari apakah "Iris ngilang" dan lag berkurang.

### Q13.1 Kunci ganda di `/etc/wsl.conf` sudah bersih (4 Nov 2026)

`wsl -d Ubuntu -- cat -n /etc/wsl.conf` menampilkan 5 baris: `[boot]` `systemd=true`, lalu `[user]` `default=<user>`. Tidak ada kunci ganda. Setelah `wsl --shutdown`, `wsl -d Ubuntu -- echo ok` hanya mengeluarkan `ok`, tanpa peringatan `Duplicated config key`. Dugaan di Q12 bahwa peringatan stderr `wsl.exe` di Q11.10 berasal dari kunci ganda ini kini lebih kuat, tapi belum terbukti sampai `iris-start.ps1` dijalankan ulang tanpa peringatan.

### Q13.2 Tes Launcher di batas 4 GB: indikator hijau, `/agen halo` jalan (4 Nov 2026, 21:04)

Dari screenshot overlay: indikator V, 9, H hijau semua. `/agen halo` dikirim 21:04:43, Iris menjawab "Serahin ke Iris" di detik yang sama, hasil tugas Hermes ("Halo. Ada yang bisa dibantu?") masuk 21:04:55 (sekitar 12 detik), tidak ada tanda Hermes tersendat atau mati sendiri.

**Temuan baru (bukan soal memori).** Setelah hasil tugas, Iris membalas 21:05:02 dengan menyatakan hasil agen "halo" tidak nyambung dengan pertanyaan saham (di bubble: topiknya "udah beda jauh", saham Elon). Jadi balasan Iris merangkum hasil agen dengan riwayat obrolan lama yang masih terbawa, bukan dengan tugas yang baru saja dikirim. Dugaan: riwayat sesi sebelumnya (tentang saham) ikut masuk ke konteks saat Iris menanggapi hasil tugas. Belum diperiksa di `server.py`.

**Belum dilakukan.**
- [ ] Konfirmasi suara Iris lancar (VOICEVOX) di batas 4 GB.
- [x] Cek riwayat lama setelah tombol Hapus: selesai, lihat Q13.3 (dugaan terbukti).

### Q13.3 Tes setelah Hapus: dugaan riwayat bocor terbukti (4 Nov 2026, 21:06)

Setelah tombol Hapus, `/agen halo` dikirim 21:06:37. Hasil Hermes ("Halo, Rover. Ada yang bisa dibantu?") masuk 21:06:43 (sekitar 6 detik), dan Iris membalas wajar 21:06:47: "Yo, Rover. Ada yang perlu bantuin?". Tidak ada lagi komentar soal saham.

**Kesimpulan.** Balasan aneh di Q13.2 berasal dari riwayat obrolan lama yang ikut terbawa ke konteks saat Iris menanggapi `HASIL TUGAS`, bukan dari Hermes atau batas memori. Perilaku saat riwayat tidak kosong tetap bermasalah: topik lama bisa dipakai untuk menilai hasil tugas yang baru.

**Belum dilakukan.**
- [ ] Baca bagian `server.py` yang menyusun pesan ke LLM untuk `HASIL TUGAS`, lalu pastikan tanggapan memakai tugas yang baru dikirim sebagai fokus (mis. sertakan teks tugas asli, dan beri tahu riwayat lama hanya latar).
- [ ] Konfirmasi suara Iris lancar (VOICEVOX) di batas 4 GB.

---

# Bagian R: Publikasi ke GitHub, audit privasi, dan pengaturan repo (5 Nov 2026)

Proyek dipublikasikan sebagai repositori **private** `JihoStarting/iris-desktop-companion`. Bagian ini mencatat apa yang di-push, temuan audit privasi, perubahan kode yang dipicu audit, hasil tes sesudahnya, dan pengaturan repo. Tanda: **[dites]** = terlihat jalan di PC (log atau screenshot), **[belum dikonfirmasi]** = langkah diberikan tapi hasilnya belum dilaporkan.

## R1. Ringkasan

- [x] Repo dibuat (private, tanpa README, `.gitignore`, atau lisensi dari GitHub, supaya push pertama tidak bentrok) **[dites]**
- [x] Commit awal `<hash-lama>`: "feat: initial commit of IRIS desktop overlay companion", **30 berkas**, 2,30 MiB, branch `main` **[dites]**: `git push -u origin main` berhasil, `git status` bersih sesudahnya
- [x] Halaman repo diperiksa lewat screenshot: daftar berkas bersih, README tampil, GitHub mengenali lisensi MIT, deskripsi dan Topics tersimpan **[dites]**
- [x] Tes `/agen` sesudah perubahan kode: lulus, path Windows benar (lihat R5) **[dites]**
- [x] README diperluas (±13 KB) sudah di-push, commit `<hash-lama>` **[dites]** (lihat S1)
- [x] Rilis `IrisLauncher.exe` v1.0.0 tampil di panel Releases dengan label Latest **[dites]**; lampiran `.exe` belum terlihat di screenshot (lihat S1)

## R2. Isi repo

| Ikut di-push | Tidak ikut (dikecualikan `.gitignore` atau dipindah) |
|---|---|
| `main.js`, `preload.js`, `index.html`, `test_client.html` | `.env` (kunci dan token) |
| `server.py`, `iris_web.py`, `buat_klip_vrma.py`, `cek-cancel-hermes.py` | `iris-history.json`, `iris-memory.json` (data pribadi) |
| `package.json`, `package-lock.json`, `requirements.txt`, `clips.json` | `*.log` (lima berkas), `*.rartemp` |
| `.env.example`, `.gitignore`, `LICENSE`, `README.md` | `*.rar`, `*.zip`, `*.7z` (termasuk `assets.rar` dan arsip cadangan proyek) |
| `IrisLauncher-src/` (`.cs`, `.manifest`, `build.bat`, enam skrip `.ps1`, ikon, logo) | `IrisLauncher.exe` (dibagikan lewat Releases) |
| `docs/` (tiga berkas `.md`) | `assets/` (tujuh model VRM, ±119 MB, lisensi belum dicek), `screens/` |
| `iris-launcher-logo.png` (nama diganti dari `IRIS launcher logo.png`, tanpa spasi) | `.venv/`, `node_modules/`, `__pycache__/` |

`IrisLauncher-src.zip` (0,25 MB) tidak ikut karena `*.zip` dikecualikan; isinya salinan dari folder yang sama.

## R3. Temuan audit privasi

Sebelum commit, berkas diperiksa dengan `git grep` untuk pola nama user, nama host, sidik token, dan pola kunci.

- **Tidak ada kunci atau token asli** di kode maupun dokumen. Semua penyebutan `NINEROUTER_API_KEY`, `HERMES_API_KEY`, dan `COMPANION_TOKEN` hanya nama variabel atau contoh. `.env.example` berisi nilai kosong.
- **Info pribadi kecil ditemukan** dan dibersihkan: nama user Windows (`C:\Users\<user>`, `/mnt/c/Users/<user>`), nama user WSL (`/home/<user>`), nama host WSL (`<host>`), dan sidik token (`<hex>`).
- **Pembersihan tahap pertama tidak cukup.** Pola yang dipakai hanya menangkap `C:\Users\<nama>`, sehingga variasi lain lolos: `/mnt/c/Users/<nama>`, `default=<nama>` di `wsl.conf`, `/home/<nama>/.hermes/`, dan prompt WSL. Cek `git grep` yang kedua yang menangkapnya. **Pelajaran:** setelah membersihkan, selalu jalankan ulang pencarian dan baca hasilnya, jangan menganggap pola penggantian sudah menutup semua kemunculan.
- **Nama user juga ada di kode**, bukan hanya dokumen: `server.py` baris 320 (nilai bawaan `HERMES_WIN_HOME`) dan baris 696 (contoh di komentar). Dibersihkan lewat R4.
- Cek akhir yang dipakai sebelum commit, semuanya harus kosong:
  - `git ls-files | Select-String` untuk `.env`, `.log`, `.rar`, `.zip`, `.exe`, `.vrm`, `history`, `memory`, `node_modules`, `.venv`
  - `git grep -nEil "<pola nama>"` dan, untuk isi yang sudah di-stage, `git grep --cached ...`
  - `git grep` untuk pola kunci (`sk-...`), alamat email, dan token bot (`angka:huruf`)

## R4. Perubahan kode: `HERMES_WIN_HOME`

- [x] `server.py` baris 320: nilai bawaan diganti dari folder pribadi menjadi `/mnt/c/Users/<user>`; baris 696 (komentar) disamakan. Cadangan berkas asli disimpan sebagai `server.py.bak` di folder user.
- [x] Nilai asli dipindah ke `~/.env` (baris 9: `HERMES_WIN_HOME=/mnt/c/Users/<user>` dengan nama user asli) sehingga program tetap memakai folder yang benar **[dites]**
- [x] `.env.example` ditambah `HERMES_WIN_HOME=/mnt/c/Users/<user>` dan `COMPANION_TOKEN=` (dengan cara membuat token) supaya pengguna lain tahu variabelnya.
- [x] `server.py` di komputer disamakan dengan versi di GitHub (sempat berbeda sebentar karena rollback uji); `git status` bersih.

**Catatan.** Karena nilai bawaan kini `/mnt/c/Users/<user>`, setiap PC yang menjalankan `server.py` **wajib** mengisi `HERMES_WIN_HOME` di `.env`. Tanpa itu, path Windows di laporan `/agen` akan salah. Ini sudah tercantum di tabel konfigurasi README.

## R5. Tes sesudah perubahan (5 Nov 2026, pagi)

Dari log terminal server dan screenshot overlay:

- [x] Start: `.env dipakai` menunjuk berkas `.env` di folder user; token `/ws` terbaca (43 karakter); `Application startup complete`; `GET /health` 200 **[dites]**
- [x] Halaman `127.0.0.1:8765` di browser menampilkan "Server Iris aktif" dan keterangan bahwa halaman tes tidak dipakai karena `COMPANION_TOKEN` aktif. Ini perilaku yang diharapkan (lihat v28), bukan galat **[dites]**
- [x] Overlay tersambung (`WebSocket /ws [accepted]`), `riwayat dipulihkan: 6 pesan` **[dites]**
- [x] `/agen sebutkan isi folder Download` (07:59:14): Hermes mulai 07:59:16 dan selesai 07:59:37 (**23,2 detik**), total **33,4 detik** (Hermes 23,2, Iris + suara 10,2). Kartu "Hasil tugas" menampilkan path Windows `C:\Users\<user>\Downloads`, jadi `HERMES_WIN_HOME` terbaca dari `.env` **[dites]**
- [x] Iris merangkum hasilnya dengan benar di bubble
- [ ] Suara belum terdengar: terminal penuh `speak: VOICEVOX gagal: ConnectError` karena aplikasi **VOICEVOX belum dijalankan** saat tes. Bukan galat kode. Ulangi tes suara dengan VOICEVOX hidup.

## R6. Pengaturan repo dan keamanan GitHub

- [x] `.gitignore` dibuat (rahasia, dependensi dan lingkungan, data pribadi, log dan sementara, arsip, biner dan build, `assets/` dan `screens/` sebagai pengaman, berkas OS dan editor).
- [x] `LICENSE` MIT, "Copyright (c) 2026 KangJiho" **[dites]**: GitHub menampilkannya di tab "MIT license" dan sidebar. Sempat salah buat: `LICENSE.txt` hasil Notepad kosong (0 byte); diganti berkas yang ditulis lewat PowerShell (1069 byte).
- [x] About: deskripsi terisi; Topics `electron`, `vrm`, `ai-companion`, `fastapi`, `desktop-overlay` tersimpan. "Releases" dicentang di halaman utama; "Deployments" dibiarkan kosong; "Packages" disarankan dilepas karena tidak dipakai.
- [x] Dependabot (halaman Advanced Security): **Dependabot alerts** dan **Dependabot security updates** aktif. Disarankan menyalakan **Dependency graph** dan **Malware alerts**; **Grouped security updates** opsional; **Dependabot version updates** sengaja tidak dinyalakan (terlalu banyak PR untuk proyek pribadi).
- [x] **Secret scanning dan Push protection tidak muncul** di repo private pada akun ini. Di repo public fitur itu tersedia otomatis. Sampai repo dijadikan public, pengaman utamanya tetap `.gitignore` dan pemeriksaan manual di R3.
- Pembaruan Dependabot (terutama Electron) **jangan langsung di-merge**: tes dengan `npm install` dan `npm start` dulu, karena perubahan Electron dapat memengaruhi overlay.

## R7. README

- README awal sederhana ter-push bersama commit awal (fitur, arsitektur, instalasi, menjalankan, aset, lisensi) dan tampil benar di GitHub.
- Versi diperluas (±13 KB) ditulis: badge, daftar isi, fitur per kelompok, diagram arsitektur, teknologi, prasyarat, instalasi, tabel semua variabel `.env`, tabel perintah chat, pintasan, keamanan, struktur proyek, aset, pemecahan masalah, dan lisensi. Disusun hanya dari perintah dan perilaku yang disebut dokumen ini; sebagian deskripsi perintah (misalnya `/clip`, `/chrome`) perlu diperiksa pemilik sebelum dianggap final.
- Belum ada screenshot demo di README. Bila ditambahkan, pakai obrolan biasa, bukan hasil `/agen` atau isi folder pribadi (kartu hasil memuat nama user dan isi Downloads).

## R8. Catatan cara kerja (pelajaran sesi ini)

- **Satu blok perintah per tempelan.** Dua kali perintah rusak karena sisa teks di baris prompt menempel di depan tempelan berikutnya (`Get-Content .env.exampleSave-File ...`). Tekan `Esc` untuk mengosongkan baris, lalu tempel.
- **Jangan menempel isi berkas sebagai perintah.** Isi README dan LICENSE tertempel langsung ke PowerShell dan menghasilkan deretan galat "tidak dikenali". Tidak merusak apa pun, tapi isi berkas harus ditulis lewat `Set-Content`/`Save-File` atau editor.
- **Pager git.** `git grep` dengan hasil panjang masuk mode pager (`:` atau `(END)`); keluar dengan `q`. Dinonaktifkan dengan `git config --global core.pager ""`.
- **`git grep --cached`** memeriksa isi yang sudah di-stage, sedangkan `git grep` biasa membaca berkas di komputer. Setelah rollback berkas lokal, hanya `--cached` yang menunjukkan apa yang benar-benar akan di-commit.
- **Peringatan `LF will be replaced by CRLF`** normal di Windows dan tidak berbahaya; bisa diseragamkan dengan `.gitattributes` berisi `* text=auto`.
- **Aturan tetap:** jangan menulis nama user, token, atau path pribadi asli di berkas yang di-commit (termasuk `docs/`); pakai `<user>`, `<host>`, `<hex>`, `<NIM>`, `<kampus>`. Berlaku juga untuk data identitas (NIM, nama kampus, mata kuliah, kode kelas) dan profil pribadi (hobi, tujuan, kebiasaan). Pakai `git add NAMAFILE` dan periksa `git status` sebelum commit.
- Log server dan screenshot overlay memuat nama user dan isi folder pribadi; sensor sebelum dibagikan ke publik.

## R9. Yang masih terbuka

- [x] Konfirmasi README versi diperluas sudah di-commit dan di-push (selesai, lihat S1).
- [x] Konfirmasi rilis `IrisLauncher.exe` v1.0.0 diterbitkan dan tampil di panel Releases (selesai, lihat S1).
- [ ] Nyalakan **Dependency graph** dan **Malware alerts** di Advanced Security bila belum.
- [ ] Putuskan apakah repo tetap private atau dijadikan public. Sebelum public: baca ulang `docs/` mencari sisa info pribadi, pastikan lisensi model VRM di `assets/` jelas (tidak ikut ter-upload), dan README terbaca baik.
- [ ] Tambah screenshot demo yang aman ke `docs/images/` dan README.
- [ ] Tes suara dengan VOICEVOX hidup setelah perubahan `server.py` (R5).
- [ ] Opsional: `.gitattributes` untuk akhir baris, dan penyamaan nama pemegang hak cipta di `LICENSE` bila ingin memakai nama akun.
- [ ] Item terbuka dari Q13.3 (tanggapan Iris atas `HASIL TUGAS` yang terpengaruh riwayat lama; konfirmasi suara lancar di batas 4 GB) tidak berubah oleh bagian ini.


---

# Bagian S: README dan rilis terkonfirmasi di GitHub, penilaian repo (5 Nov 2026, siang)

Bagian ini mencatat hasil pemeriksaan halaman repo `JihoStarting/iris-desktop-companion` lewat 11 screenshot (halaman utama, README digulir dari atas sampai bawah, dan berkas `LICENSE`), lalu penilaian dan daftar perbaikan kecil. Tanda sama seperti Bagian R. Penilaian bersifat subjektif dan dibuat dari screenshot; kode tidak dijalankan ulang di bagian ini.

## S1. Ringkasan hasil

- [x] README diperluas ter-push: commit `<hash-lama>` "docs: perluas README (fitur, perintah chat, keamanan, troubleshooting)". Repo kini **2 commit**; di daftar berkas, `README.md` berumur 5 menit dan berkas lain 39 menit **[dites]**
- [x] README versi panjang tampil benar di GitHub: badge, Daftar isi (tautan jangkar jalan), Fitur per kelompok, diagram arsitektur, tabel komponen, Instalasi, tabel Konfigurasi, Menjalankan, tabel Perintah chat, Keamanan, Struktur proyek, Aset, Pemecahan masalah, Dokumentasi, Lisensi **[dites]**
- [x] Rilis **IRIS v1.0.0** tampil di panel Releases dengan label **Latest** (jadi bukan Pre-release), dan repo punya **1 Tag** **[dites]**
- [~] Lampiran `IrisLauncher.exe` (±0,47 MB) di rilis **belum terlihat** di screenshot, karena sidebar hanya menampilkan nama rilis. Buka halaman rilis untuk memastikan
- [x] `LICENSE`: GitHub mengenali sebagai **MIT License** (21 baris, 1,04 KB, "Copyright (c) 2026 KangJiho"), dengan izin Commercial use, Modification, Distribution, Private use **[dites]**
- [x] Daftar berkas **bersih**: tidak ada `.env`, `assets/`, `screens/`, log, arsip, riwayat, atau memori. Yang tampil: `IrisLauncher-src/`, `docs/`, `.env.example`, `.gitignore`, `LICENSE`, `README.md`, `buat_klip_vrma.py`, `cek-cancel-hermes.py`, `clips.json`, `index.html`, `iris-launcher-logo.png`, `iris_web.py`, `main.js`, `package-lock.json`, `package.json`, `preload.js`, `requirements.txt`, `server.py`, `test_client.html` **[dites]**
- [x] Sidebar: deskripsi terisi, lima Topics (`ai-companion`, `desktop-overlay`, `electron`, `fastapi`, `vrm`), Readme, MIT license, 1 kontributor. Bahasa: HTML 46,8%, JavaScript 19,7%, Python 17,6%, C# 8,4%, PowerShell 7,4%, Batchfile 0,1%
- Repo masih **Private** (ikon gembok di judul)

## S2. Item R9 yang kini selesai

| Item R9 | Status | Bukti |
|---|---|---|
| README diperluas di-commit dan di-push | selesai | Commit `<hash-lama>`, 2 commit, README 5 menit lalu |
| Rilis `IrisLauncher.exe` v1.0.0 diterbitkan | selesai, lampiran belum terkonfirmasi | Sidebar: "IRIS v1.0.0 (Latest)", 16 menit lalu |
| Repo masih private | tetap | Label Private di halaman utama |

Item R9 lain (Dependency graph dan Malware alerts, keputusan public atau private, screenshot demo, tes suara VOICEVOX, `.gitattributes`, item Q13.3) **belum berubah**.

## S3. Penilaian (subjektif, skala 10)

| Aspek | Nilai | Alasan |
|---|---|---|
| Kebersihan dan keamanan repo | 8 | NIM dan nama kampus sempat lolos audit R3 (ditemukan 5 Nov, dibersihkan di S8). Tidak ada rahasia di daftar berkas, `.gitignore` bekerja, lisensi terdeteksi, Dependabot aktif. Kurang: secret scanning tidak tersedia di repo private, dan metadata commit belum diperiksa (S4 no. 6) |
| README | 8 | Lengkap dan rapi: daftar isi, tabel konfigurasi, perintah, pemecahan masalah, bagian keamanan jujur. Kurang: belum ada screenshot atau GIF demo, dan ada dua salah kecil (S4 no. 1 dan 2) |
| Kelengkapan dan struktur | 8 | Kode, contoh konfigurasi, lisensi, dokumentasi, dan peluncur ada. Kurang: belum ada demo visual, belum ada tes otomatis |
| Rilis | 7 | v1.0.0 terbit dan berlabel Latest, tapi lampiran belum terkonfirmasi dan, selama repo private, orang lain tidak bisa mengunduhnya |
| Kesiapan dijadikan public | 6 | Masih ada pekerjaan: baca ulang `docs/`, cek lisensi model VRM, cek metadata commit, tambah demo |
| **Keseluruhan (proyek pribadi, private)** | **8** | Bersih, terdokumentasi, dan rapi untuk proyek pribadi yang masih berkembang |

## S4. Temuan dari screenshot (perbaikan kecil)

1. **Diagram arsitektur menyesatkan.** Di README, panah dari 9Router turun ke VOICEVOX, seolah 9Router memanggil VOICEVOX. Menurut tabel arsitektur dan Bagian A sampai C, `server.py` yang memanggil keduanya. Perbaikan: gambar VOICEVOX sejajar dengan 9Router dan Hermes, masing-masing dengan panah dari `server.py`.
2. **Struktur proyek belum lengkap.** `iris-launcher-logo.png` ada di repo tapi tidak ada di pohon README.
3. **Instruksi untuk orang lain belum bisa dipakai selama private.** `git clone` dan tautan Releases hanya jalan untuk akun yang punya akses. Tidak masalah bila repo memang private; relevan hanya kalau nanti dijadikan public.
4. **Belum ada demo visual.** Proyek ini visual, jadi screenshot atau GIF di README akan paling terasa. Pakai obrolan biasa, bukan hasil `/agen` (memuat nama user dan isi Downloads), dan simpan di `docs/images/`.
5. **Deskripsi perintah masih singkat.** `/chrome` hanya tertulis "Mini-browser panel"; `/clip` dan beberapa perintah lain masih perlu dicek pemilik (R7).
6. **Metadata commit belum diperiksa.** Audit R3 memeriksa isi berkas, bukan nama dan email penulis commit. Cek dengan `git log --format="%an <%ae>"`. Bila email asli terlihat dan repo mau dijadikan public, pakai alamat noreply GitHub untuk commit berikutnya. Riwayat yang sudah ada tidak berubah otomatis; hanya relevan sebelum public.
7. **Panel Packages** masih tampil "No packages published". Bisa dilepas lewat ikon gerigi di kotak About.

## S5. Yang masih terbuka (urutan saran)

- [ ] Buka halaman rilis v1.0.0, pastikan `IrisLauncher.exe` terlampir (±0,47 MB)
- [ ] Nyalakan Dependency graph dan Malware alerts (Settings, Advanced Security)
- [ ] Satu commit `docs:` untuk memperbaiki diagram arsitektur dan pohon Struktur proyek (S4 no. 1 dan 2)
- [ ] Cek metadata commit (S4 no. 6)
- [ ] Tes suara dengan VOICEVOX hidup, sekaligus konfirmasi suara lancar di batas WSL 4 GB (R5, Q13.3)
- [ ] Tes v32 (gambar normal) dan v29 (baris tanpa `|||` tetap bersuara)
- [ ] **Perbaikan kode Q13.3**: tanggapan Iris atas `HASIL TUGAS` jangan terpengaruh riwayat lama. Sertakan teks tugas asli sebagai fokus dan jadikan riwayat lama hanya latar (di `server.py`, bagian penyusun pesan ke LLM)
- [ ] Selidiki `Hermes membalas HTTP 503` (penyebab belum dipastikan)
- [ ] Tugas nyata pertama untuk Hermes: skill `cek-elearning`
- [ ] Screenshot demo yang aman ke `docs/images/` dan README
- [ ] Putuskan repo tetap private atau public (syarat: baca ulang `docs/`, lisensi model VRM jelas, metadata commit aman, README terbaca baik)

## S6. Catatan cara kerja

- Hasil push dibuktikan dari halaman GitHub (commit `<hash-lama>`, umur berkas), bukan dari keluaran terminal.
- Perintah `git add main.js` saat `git status` bersih tidak berefek. Cukup `git add` berkas yang benar-benar berubah, lalu periksa `git status` sebelum commit.
- Setelah `git add`, pastikan `iris-history.json` dan `iris-memory.json` tidak muncul di `git status`; keduanya dikecualikan `.gitignore` dan tidak terlihat di daftar berkas repo.

## S7. Kronologi proyek dan koreksi tanggal setup (5 Nov 2026)

Tanggal "Setup date: 2026-10-30" di `iris-system.md` (dan salinannya di Bagian B) ternyata **bukan** tanggal setup. File itu dibuat oleh Iris pada 30 Okt (tertulis "Generated by Iris"), dan Iris di Telegram hanya mengulang tanggal dari file. Tanggal asli diambil dari waktu pembuatan (`stat -c %w`) di WSL dan dari properti folder di Windows.

| Tanggal | Kejadian | Bukti |
|---|---|---|
| 24 Sep 2026 | Hermes Agent v0.22.2 dirilis | Penanda versi `2026.9.24` di `iris-system.md` |
| 28 Sep 2026, 07:27 | Ubuntu di WSL dipasang | Waktu pembuatan direktori `/` di WSL **[dites]** |
| 28 Sep 2026, 18:21 | Hermes Agent dipasang | Waktu pembuatan `~/.hermes` **[dites]** |
| 28 Okt 2026, 22:56 | `config.yaml` Hermes ditulis (terakhir dibuat ulang) | Waktu pembuatan berkas; **bukan** tanggal setup, hanya menunjukkan kapan berkas ditulis ulang **[dites]** |
| 28 Okt 2026, 23:28 | Folder proyek overlay dibuat (awal proyek) | Properti folder proyek (Created) **[dites]** |
| 30 Okt 2026 | `iris-system.md` dibuat oleh Iris; roadmap dan dokumen gabungan disusun | Tulisan "Generated by Iris" dan header dokumen |
| 5 Nov 2026 | Repo GitHub dibuat; commit pertama `<hash-lama>`; README diperluas `<hash-lama>`; rilis v1.0.0 | Riwayat GitHub (lihat Bagian R dan S1) |

**Catatan.**
- Tanggal "Created" di properti folder bisa berubah bila folder pernah disalin atau dipindah.
- Header `iris-system.md` kini berisi empat baris tanggal (Ubuntu dipasang, Hermes dipasang, overlay dimulai, dokumen dibuat).
- Keluaran perintah `stat` memuat nama user asli; di dokumen ini tidak ditulis (aturan Bagian R8).

**Yang masih terbuka.**
- [ ] Kirim koreksi tanggal ke Iris di Telegram dan konfirmasi tersimpan di memori (tanya balik apa yang disimpan)
- [ ] Timpa `docs/iris-system.md` dan salinan di sisi WSL dengan versi terbaru
- [x] Tambah bagian "Status" di `README.md` (commit `<hash-lama>`) dan baris "Dimulai" di `roadmap-ai-companion.md` (commit `<hash-lama>`) **[dites]**: push berhasil
- [x] Commit dan push empat berkas (README `<hash-lama>`; tiga berkas `docs/` `<hash-lama>`, 3 berkas, 208 baris ditambah) **[dites]**

## S8. Pembersihan info pribadi dari dokumen (5 Nov 2026)

Saat berkas `docs/` diperiksa ulang setelah push `<hash-lama>`, ditemukan **info pribadi yang lolos dari audit R3**. Pemicunya: audit R3 hanya mencari nama user, nama host, sidik token, dan pola kunci, tidak mencari data identitas.

**Yang ditemukan dan dibersihkan** (di `docs/iris-system.md` dan salinannya di Bagian B dokumen ini):

| Jenis | Isi sebelumnya | Diganti jadi |
|---|---|---|
| Identitas | NIM dan nama kampus | `<NIM>`, `<kampus>` |
| Profil pribadi | preferensi, tujuan, dan kebiasaan pengguna | `<preferensi pribadi>`, `<tujuan pribadi>`, `<kebiasaan pribadi>` |
| Nama kampus di teks lain | 8 kemunculan di skill e-learning, Moodle, dan keputusan pemilik | `<kampus>` |
| Mata kuliah dan kode kelas | satu baris di rencana skill `cek-elearning` | `<matkul>` |
| Label drive Z: | nama label drive | `<label drive>` |
| Ukuran folder Downloads | satu angka di hasil tes R5 | dihapus |
| Nama panggilan lain | satu alias di aturan "Call sign" | dihapus |

**Sengaja dibiarkan** (bukan data identitas): nama panggilan bawaan `Rover` (nilai bawaan `COMPANION_USER_NAME`), nama persona dan asal karakter Iris, nama akun GitHub dan nama penulis "KangJiho" (sudah publik di repo), serta IP gateway WSL pribadi (`172.x`, tidak bisa dijangkau dari luar).

**Pemindaian setelah pembersihan** (pada empat berkas `.md`): tidak ada lagi NIM, nama kampus, nama user asli, alamat email, nomor telepon, token bot, atau kunci API.

**Catatan penting: riwayat commit.**
- Isi berkas di repo baru bersih setelah commit pembersihan ini di-push. NIM dan data lain **masih ada di commit lama** (`<hash-lama>`, `<hash-lama>`, dan commit di antaranya) dan bisa dilihat lewat riwayat.
- Selama repo **private** dan tidak dibagikan, risikonya kecil.
- **Sebelum repo dijadikan public**, riwayat harus dibersihkan (misalnya repo dibuat ulang dari kondisi bersih, atau riwayat ditulis ulang). Mengedit berkas saja tidak cukup.
- Memori Iris di sisi Hermes tetap menyimpan data aslinya; itu memang tempatnya dan tidak ikut ke GitHub.

**Yang masih terbuka.**
- [ ] Commit dan push pembersihan (`docs/iris-system.md`, `docs/iris-companion-gabungan.md`)
- [ ] Putuskan cara membersihkan riwayat commit sebelum public
- [ ] Setelah push, periksa ulang halaman `docs/iris-system.md` di GitHub
- [ ] Salinan `iris-system.md` di sisi WSL tidak perlu diganti bila isinya dipakai Iris sebagai referensi pribadi; cukup jangan salin ke repo


---

# Bagian T: Riwayat repo diringkas, audit keamanan, perbaikan README dan logo, audit berkas (5 Nov 2026)

Bagian ini mencatat sesi pemeriksaan dan perapian repo `JihoStarting/iris-desktop-companion` setelah Bagian S. Tanda sama seperti Bagian R: **[dites]** = terlihat jalan di PC atau di halaman GitHub (keluaran terminal atau screenshot pemilik), **[diperiksa lewat pratinjau]** = diperiksa pada gambar hasil, bukan di PC. Keluaran terminal yang dikutip sudah dibersihkan dari nama user dan path pribadi (aturan R8).

## T1. Ringkasan hasil

- [x] **Force push.** `git push -u origin main --force`: remote `main` berubah dari `<hash-lama>` menjadi `<hash-lama>` (34 objek, 2,31 MiB). Riwayat repo kini **1 commit**: "feat: initial commit of IRIS desktop overlay companion". Halaman GitHub menampilkan "1 Commit" **[dites]**
- [x] **Tag dipindah.** Tag `v1.0.0` sempat menunjuk `<hash-lama>` (commit lama). Setelah `git tag -f v1.0.0` dan `git push origin v1.0.0 --force`, tag menunjuk `<hash-lama>`, sama dengan `main` **[dites]**
- [x] **Rilis tetap sehat.** Halaman Releases: "IRIS v1.0.0" masih berlabel **Latest** (bukan Draft), tag `v1.0.0`, commit `<hash-lama>`. Lampiran `IrisLauncher.exe` (486 KB, sha256 tampil) utuh; "Source code (zip)" dan "(tar.gz)" dibuat ulang otomatis dari commit baru **[dites]**. Ini menutup butir lampiran yang belum terkonfirmasi di S1
- [x] **Metadata commit aman.** `git log --format="%an <%ae>"` menampilkan penulis `KangJiho` dengan alamat noreply GitHub; `git log --oneline` menampilkan satu baris dengan `HEAD -> main`, `tag: v1.0.0`, dan `origin/main` **[dites]**
- [x] **Fitur keamanan GitHub.** Dependency graph dan Malware alerts dinyalakan (dilaporkan pemilik)
- [x] **Commit `45ee0ac`** "docs: hapus baris status yang sudah usang": baris tabel Chrome Debug dan Disk Space dihapus dari tabel "Current Status" di `docs/iris-system.md` dan salinannya di Bagian B dokumen ini. 2 berkas, 4 baris dihapus; push `<hash-lama>..45ee0ac` **[dites]**. Alasan: catatan "C: dan Z: 93% penuh" sudah usang (Z: kini bebas sekitar 71 GB, lihat Q12)
- [x] **Commit `f451ade`** "docs: perbaiki diagram arsitektur dan struktur proyek": diagram README kini menggambar `server.py` memanggil 9Router, VOICEVOX, dan Hermes Agent secara sejajar (sebelumnya panah 9Router ke VOICEVOX menyesatkan), dan pohon struktur memuat lima berkas yang tadinya hilang (`iris-launcher-logo.png`, `package-lock.json`, `.gitignore`, `LICENSE`, `README.md`). Push `45ee0ac..f451ade`; screenshot GitHub: `README.md` berumur 1 menit, repo 3 commit **[dites]**
- [x] **Tampilan konsol, bukan berkas rusak.** `git diff` sempat menampilkan teks seperti `ΓöîΓöÇ` di blok diagram. Setelah `[Console]::OutputEncoding = [Text.Encoding]::UTF8`, `git show HEAD:README.md` menampilkan kotak dan panah dengan benar **[dites]**. Hitungan `--stat` (14 baris masuk, 14 keluar) juga menunjukkan hanya blok diagram dan blok struktur yang berubah
- [x] **Logo di header README.** `iris-launcher-logo.png` dipasang rata tengah di atas judul (lebar 180). Screenshot GitHub menunjukkan logo tampil tetapi **kecil dan bersudut hitam** karena PNG asli tanpa alpha (RGB, 1254 x 1254, sekitar 1,8 MB) **[dites]**
- [x] **Logo diperbaiki** (dikerjakan di luar PC pemilik): latar hitam yang tersambung ke sudut dibuang, bayangan gelap di tepi cincin diubah menjadi pendar transparan, gambar dipotong pas lalu dibuat persegi 800 x 800, sekitar 850 KB. Diperiksa di latar gelap, putih, dan abu-abu: tanpa halo gelap, cincin utuh **[diperiksa lewat pratinjau]**
- [ ] **Belum dikonfirmasi:** commit logo baru, `width="280"` di README, dan keterangan baru `clips.json` di pohon struktur (perintah sudah diberikan; hasil commit dan push belum dilaporkan)

## T2. Audit keamanan repo

Dijalankan pada commit `<hash-lama>` (folder kerja bersih saat diperiksa, jadi hasilnya berlaku untuk isi di GitHub).

| Pemeriksaan | Hasil |
|---|---|
| Penulis dan email commit | noreply GitHub, bukan email asli |
| Jumlah commit | 1 |
| Berkas pribadi ter-track (`.env`, riwayat, memori, `screens/`, `assets/`, `.log`) via `git ls-files` | kosong; `.env.example` tidak cocok pola dan memang boleh ada |
| Kunci atau token, pola longgar | cocok di dua berkas `docs/`, tetapi hanya contoh perintah (`"isi-key-dari-dashboard-9router"` dan `"sk-..."`) |
| Kunci atau token, pola ketat (string panjang menyerupai kunci asli) | kosong |
| NIM dan nama kampus, dicari dengan nilai asli | kosong |
| Nama user Windows | kosong |
| `C:\Users\` | semua kemunculan memakai penanda (`<user>`, `<nama>`, atau `C:\Users\...`), tanpa nama asli |
| Placeholder `<NIM>` | 3 kali di dokumen gabungan dan 1 kali di `iris-system.md` (artinya versi bersih yang ter-push) |

**Catatan.**
- **Pencarian NIM dan kampus pertama tidak sah.** Perintahnya memakai tulisan placeholder (`ISI_NIM`, `NIM_ASLIMU`), dan dua percobaan `Read-Host` ditekan Enter kosong (`fatal: no pattern given`). Hanya percobaan ketiga, dengan nilai asli, yang berlaku. Pelajaran: hasil kosong dari placeholder bukan bukti.
- Versi dokumen ini sudah memuat `<alamat e-learning kampus>` di catatan Bagian L (sebelumnya berisi alamat asli). Pencarian nama kampus pada repo kosong, jadi alamat itu tidak ikut ter-commit.
- **Sisa risiko riwayat lama.** Force push mengganti isi `main`, tetapi umumnya tidak langsung menghapus commit lama (`<hash-lama>`, `<hash-lama>`, `<hash-lama>`, `<hash-lama>`) dari server GitHub; commit itu masih bisa terbuka lewat alamat SHA langsung sampai GitHub membersihkannya. Selama repo **private** dan tanpa fork, risikonya kecil. Bagian ini juga menyederhanakan butir riwayat di S8, tetapi **sebelum repo dijadikan public**, pertimbangkan membuat repo baru dari kondisi bersih (atau meminta GitHub Support membersihkan cache). Hash lama di Bagian R dan S dibiarkan sebagai catatan sejarah, tetapi commit-nya tidak ada lagi di riwayat repo.

## T3. Item terbuka lama yang kini selesai

| Item | Status | Bukti |
|---|---|---|
| S5: buka halaman rilis, pastikan `IrisLauncher.exe` terlampir | selesai | Screenshot Releases: 486 KB (T1) |
| S5 dan R9: Dependency graph dan Malware alerts | selesai | Dilaporkan pemilik |
| S5 dan S4 no. 1 dan 2: perbaiki diagram arsitektur dan pohon struktur | selesai | Commit `f451ade` |
| S5 dan S4 no. 6: cek metadata commit | selesai | Noreply GitHub (T2) |
| S8: commit dan push pembersihan | selesai | Isi di commit `<hash-lama>` bersih (T2) |
| S8: periksa ulang halaman `docs/iris-system.md` di GitHub | selesai | Halaman tampil; baris usang ditandai pemilik lalu dihapus (`45ee0ac`) |
| S8: putuskan cara membersihkan riwayat sebelum public | sebagian | Riwayat diringkas jadi 1 commit; sisa risiko di T2 |
| Catatan konsistensi di Q8 (berkas `clips.json` mana yang dibaca) | terjawab | Lihat T4 |

Item R9 dan S5 lain (tes suara VOICEVOX, tes v32 dan v29, perbaikan Q13.3, `Hermes membalas HTTP 503`, `cek-elearning`, screenshot demo, keputusan public atau private) **belum berubah**; daftar terbaru ada di T7.

## T4. Audit berkas tidak penting dan duplikat

Dasar: `git grep` untuk nama tiap berkas di luar `docs/` dan `README.md`, perbandingan hash, dan `git ls-files IrisLauncher-src`.

| Berkas | Temuan | Keputusan |
|---|---|---|
| `test_client.html` | `server.py` baris 1935 menyajikannya dari folder yang sama dengan `server.py` (`BASE_DIR`) | Tetap di akar; jangan dipindah |
| `iris_web.py` | Hanya menyebut dirinya sendiri; dijalankan dari WSL oleh agen, belum ada skill yang memanggil | Tetap |
| `buat_klip_vrma.py` | Baris 8: `OUT = Path(__file__).resolve().parent / "assets" / "animations"`, jadi jalur keluaran ikut lokasi skrip | Tetap di akar. Kalau dipindah ke `tools/`, klip tertulis ke `tools/assets/animations/` dan tidak ditemukan aplikasi, kecuali baris itu diubah memakai `.parents[1]` |
| `cek-cancel-hermes.py` | `.env` dibaca dari folder user (utama) dan folder skrip (cadangan); hanya disebut di komentar `server.py` baris 850 | Aman dipindah, tetapi manfaatnya kecil; tetap |
| `clips.json` (akar) | Hash SHA-256 (`CB8C54E8...`) identik dengan `assets/animations/clips.json`. `index.html` membaca `CLIP_DIR + 'clips.json'`, yaitu `assets/animations/`, **bukan** berkas di akar | Tetap sebagai salinan sumber (folder `assets/` tidak ikut repo); keterangan di README diperjelas |
| `iris-launcher-logo.png` dan `IrisLauncher-src/logo.png` | Hash blob berbeda (`e8f34cc` dan `83c3e61`), jadi dua gambar yang berbeda | Tetap keduanya |
| `IrisLauncher-src/` | 10 berkas: `IrisLauncher.cs`, `app.manifest`, `build.bat`, `iris-doctor.ps1`, `iris-hermes.ps1`, `iris-service.ps1`, `iris-start.ps1`, `iris-stop.ps1`, `iris.ico`, `logo.png`. Tanpa `bin/`, `obj/`, atau `.exe` | Bersih |
| `docs/` | Satu-satunya duplikasi sungguhan: dokumen gabungan menyalin isi `roadmap-ai-companion.md` (Bagian A) dan `iris-system.md` (Bagian B), sehingga perbaikan harus dikerjakan dua kali (contoh: `45ee0ac`) | Dibiarkan selama repo private. Sebelum public, saran: simpan hanya dokumen gabungan dan ubah bagian "Dokumentasi" di README |

Kesimpulan: tidak ada berkas yang dipindah atau dihapus.

## T5. Pencarian catatan (RAG): apa yang ada dan keputusan

- Nama persona **I.R.I.S.** berarti Intelligent Retrieval & Indexing System (lihat catatan persona v3 di Bagian A). Saat ini hanya nama, belum arsitektur.
- **Yang sudah ada:** memori ringan `iris-memory.json` (maksimal 40 hal, 200 karakter per hal) yang seluruh isinya disisipkan ke prompt lewat `memory_block()`; memori Hermes (Global Memory dan User Profile) yang disuntikkan tiap giliran; mood; riwayat percakapan; web search Exa lewat `/agen`.
- **Yang belum ada:** embedding, vector database, indeks teks penuh, dan pengambilan potongan yang relevan saja. Butir H5 no. 5 ("Pencarian catatan kuliah", RAG ringan) tetap berstatus ide.
- **Keputusan (5 Nov):** `/cari` **tidak dibangun sekarang**. Pemilik lebih sering memakai `/agen` (pencarian folder lewat Hermes) dan `/ingat`, dan itu sudah mencukupi.
- **Tanda untuk meninjau ulang:** `/agen` terasa terlalu lambat untuk pencarian yang sama berulang; agen sering salah file; catatan sudah sangat banyak.
- **Rancangan bila nanti dibangun:** satu folder catatan, dipecah 200 sampai 500 kata per potongan, embedding model kecil (mis. `multilingual-e5-small` atau lewat 9Router), disimpan di ChromaDB atau SQLite; perintah `/cari <pertanyaan>`, `/indeks`, `/indeks status`; jawaban menyebut berkas sumber. Perhatikan batas RAM (WSL dibatasi 4 GB).

## T6. Catatan cara kerja (pelajaran sesi ini)

- `git` memakai pager, sehingga keluaran panjang tertahan dan muncul `...skipping...`. Pakai `git --no-pager ...` atau atur sekali `git config --global core.pager cat`.
- Konsol PowerShell Windows bisa menampilkan karakter kotak sebagai `ΓöîΓöÇ` bila kodepage bukan UTF-8. Atur `[Console]::OutputEncoding = [Text.Encoding]::UTF8` sebelum menyimpulkan berkas rusak, dan bandingkan dengan hitungan `git diff --stat`.
- `git grep -l` hanya menampilkan nama berkas (bukan isi baris), cocok untuk mencari data pribadi. Aturan R8 tetap berlaku untuk keluaran yang ditempel ke dokumen atau tempat publik.
- `git add` lalu `git commit` saat `git status` bersih menghasilkan `nothing to commit`; periksa dulu apakah berkasnya memang sudah diubah.
- Mengedit berkas dengan `[IO.File]::ReadAllText` dan `WriteAllText` menjaga akhir baris dan encoding. Peringatan `LF will be replaced by CRLF` tidak berbahaya; opsional diredam dengan `.gitattributes` berisi `* text=auto`.
- GitHub membuang atribut gaya (mis. `border-radius`) dari HTML di README, jadi sudut gambar tidak bisa dibulatkan lewat README; gambarnya sendiri harus transparan.

## T7. Yang masih terbuka (urutan saran)

- [ ] Konfirmasi commit dan push: logo baru, `width="280"`, dan keterangan `clips.json` di pohon struktur (T1); lalu periksa tampilan README di GitHub (logo transparan, ukuran pas)
- [ ] Tes suara dengan VOICEVOX hidup, sekaligus konfirmasi suara lancar di batas WSL 4 GB (R5, Q13.3)
- [ ] Tes v29 (baris tanpa `|||` tetap bersuara dan terminal mencetak `baris diperbaiki`) dan v32 (gambar normal dijelaskan dalam 90 detik)
- [ ] Tes v28c (bubble dengan 0 sampai 4 lampiran) dan v18 (gerak halus dan gerbang emosi)
- [ ] Tes jembatan 5a (N3), RAM tab parkir (O3), dan sisa tes v46 sampai v50
- [ ] Perbaikan kode Q13.3: tanggapan Iris atas `HASIL TUGAS` jangan terpengaruh riwayat lama
- [ ] Selidiki `Hermes membalas HTTP 503` (penyebab belum dipastikan)
- [ ] Jalankan `cek-cancel-hermes.py` (K1); hasilnya menahan fase 5b dan 5c mini-browser
- [ ] Rapikan `CHROME_HELP` (5 slot) dan penanganan argumen `text` di `iris_web.py`
- [ ] Perbarui deskripsi `/chrome` dan `/clip` di README (S4 no. 5)
- [ ] Poin "Disk C:/Z: keduanya 93% penuh" di daftar batasan (Bagian B, sekitar baris 813, dan salinannya di `docs/iris-system.md`) sudah usang: hapus atau perbarui
- [ ] Screenshot demo yang aman ke `docs/images/` dan README
- [ ] Putuskan repo tetap private atau public (syarat: baca ulang `docs/`, lisensi model VRM jelas, README terbaca baik, dan sisa risiko commit lama di T2)
- [ ] Fitur yang sudah disetujui tetapi belum ditulis: skill `cek-elearning`, memori otomatis ringan (O6), angin dari kecepatan kursor (O7), menari mengikuti musik (Bagian P), skrip setup, cek kesehatan, dan auto-start (Bagian Q)
- [ ] Opsional: `.gitattributes` (`* text=auto`) dan melepas panel Packages dari sidebar GitHub

---

# Bagian U: Perbandingan dengan proyek sejenis, rating, dan tier list kenaikan tingkat (5 Nov 2026, malam)

Bagian ini mencatat hasil membandingkan `JihoStarting/iris-desktop-companion` dengan proyek sejenis di GitHub, lalu menyusun daftar langkah supaya Iris naik tingkat. **Penilaian bersifat subjektif**, dibuat dari README repo dan data publik hasil pencarian (README, halaman rilis, situs agregator). **Kode proyek lain tidak dibaca dan tidak dijalankan.** Jumlah bintang dan fitur proyek lain bisa sudah berubah. Aturan lama tetap berlaku: hanya ide yang diambil, kode tidak disalin.

## U1. Proyek pembanding

| Proyek | Stack | Avatar | Agen atau tugas PC | Lisensi | Kedewasaan (perkiraan) |
|---|---|---|---|---|---|
| `moeru-ai/airi` | TypeScript, Vue, Tauri dan Electron | Live2D dan VRM | Main game (Minecraft, Factorio), bot sosial | MIT | Sangat tinggi (puluhan ribu bintang) |
| `Open-LLM-VTuber` | Python | Live2D | Terbatas | Open source | Tinggi (sekitar 11,7 ribu bintang) |
| `shinyflvre/Mate-Engine` | Unity | VRM | Tidak fokus AI | Gratis | Tinggi (sekitar 3,2 ribu bintang) |
| `ARPAHLS/avatar` | Electron | VRM dan VRMA, lip-sync audio sistem | Agent bus dan MCP | MIT | Menengah (CI, rilis rutin) |
| `semperai/amica` | TypeScript, React | VRM | Tidak ada | Open source | Menengah (sekitar 3 ribu bintang) |
| `Utsuwa` (The-Lab-by-Ordinary-Company) | Tauri, Svelte | VRM | Tidak ada | MIT | Menengah; desktop beta hanya macOS |
| `cameroncodesstuff/liqu-companion` | Electron, three.js | VRM | Tidak ada | Open source | Kecil |
| `lalaland-ai/lala-companion` | Electron, React Three Fiber | VRM | Screen vision, kontrol komputer | Open source | Early access |
| **Iris (repo ini)** | Electron, FastAPI | VRM | **Hermes Agent dengan konfirmasi tugas berbahaya** | **lihat U4** | Sangat muda (1 commit, 1 bintang) |

## U2. Rating (skala 10)

| Proyek | Rating | Catatan singkat |
|---|---|---|
| AIRI | 9.0 | Unggul di skala, komunitas, dan jumlah platform |
| Open-LLM-VTuber | 8.5 | Suara hands-free dan mode offline matang |
| Mate-Engine | 7.5 | Kuat sebagai desktop mate, kurang di sisi AI |
| ARPAHLS/avatar | 7.5 | Lip-sync audio sistem, agent bus, dan CI rapi |
| **Iris** | **7.5** | Kedalaman fitur dan keamanan sekitar 9, adopsi dan kemasan sekitar 4 |
| Amica | 7.0 | Fokus VRM dan WebXR |
| Utsuwa | 6.5 | Desktop baru macOS |
| Liqu | 6.0 | Kecil tapi bersih |
| Lala | 5.5 | Masih early access |

Rating Iris sempat 6.5 saat hanya README yang dibaca. Naik jadi 7.5 setelah dokumen gabungan ini dibaca: README hanya menampilkan sekitar 40% fitur yang ada.

## U3. Fitur Iris yang belum terlihat di README

Daftar ini disusun dari Bagian A sampai T. Statusnya mengikuti tanda uji di bagian aslinya (sebagian masih `[belum dites]`).

- **Mini-browser `/chrome` multi-akun** (Bagian L sampai O): 5 slot akun dengan sesi terpisah, panel pindah sisi, tab diparkir, hemat RAM, pil akun, `/chrome ram`.
- **Jembatan Hermes baca-saja (fase 5a, v51):** HTTP lokal port 8767, nyala hanya dengan `IRIS_WEB_BRIDGE=1` dan token, batas laju, hasil bertanda `untrusted`, klien `iris_web.py`.
- **Keamanan agen:** konfirmasi `/agen` berbau hapus atau pindah file (v34, sekitar 50 kata pemicu, bisa disetel), token `/ws` lewat header, kunci navigasi, filter rahasia di memori dan riwayat, log token hanya sidik.
- **Ketahanan:** kualitas gambar adaptif (`/kualitas`), watchdog renderer, pemulihan WebGL, penjaga layar (v46), riwayat obrolan persisten, pil status koneksi `V 9 H`, `/status`.
- **Karakter:** tema empat musim dan efek jatuh (v38), baju otomatis menurut situasi dan musim (v46e), pikiran batin `[thought]` (v40), klip VRMA buatan sendiri, mood antarhari, sembunyi di tepi layar, duduk di jendela lain, pose diangkat seperti bandul, bayangan, suara per emosi.
- **Belajar dan input:** `/belajar` Jepang, STT faster-whisper (`Ctrl+Alt+G`), terjemah layar (`Ctrl+Alt+T`), fun fact buatan model, alarm, jam, Pomodoro, pengingat istirahat.
- **Infrastruktur:** `IrisLauncher.exe`, `9router.service`, `.wslconfig` (batas memori WSL 4 GB), skrip start, stop, dan doctor.

## U4. Temuan: lisensi tidak konsisten

- Bagian S1 mencatat `LICENSE` dikenali GitHub sebagai **MIT License** (Copyright (c) 2026 KangJiho).
- README yang tampil di halaman publik repo saat dibaca untuk bagian ini menyebut **"All rights reserved"**: kode tidak boleh disalin, dimodifikasi, disebarkan, atau dipakai ulang tanpa izin tertulis.
- Keduanya tidak bisa benar bersamaan. **Perlu keputusan pemilik** lalu samakan berkas `LICENSE`, badge, dan bagian Lisensi di README. Selama berstatus "All rights reserved", orang lain tidak boleh memakai atau berkontribusi, yang menahan adopsi.
- Catatan: halaman publik itu juga menunjukkan repo sudah tidak private (1 bintang, bisa dibuka tanpa login). Butir "putuskan private atau public" di T7 perlu dicek ulang terhadap kenyataan ini, termasuk syarat yang tertulis di sana (baca ulang `docs/`, lisensi model VRM, sisa risiko commit lama di T2).

## U5. Tier list kenaikan tingkat

### S-Tier: hampir tanpa kode, dampak terbesar
- [ ] Selesaikan inkonsistensi lisensi (U4); kalau ingin dipakai orang lain, pertimbangkan MIT atau Apache-2.0. Kalau ingin membatasi pemakaian komersial, lisensi seperti PolyForm Noncommercial adalah pilihan tengah
- [ ] GIF demo di README (10 sampai 20 detik): avatar bicara, `/agen`, kartu konfirmasi, panel `/chrome`. Pakai percakapan biasa (bukan hasil `/agen` yang memuat nama user dan isi Downloads), simpan di `docs/images/` (selaras S4 no. 4)
- [ ] Tulis ulang bagian Fitur README memakai U3, terutama konfirmasi agen, multi-akun, dan jembatan baca-saja
- [ ] Model VRM bebas lisensi dan satu klip idle supaya orang bisa langsung mencoba (aset sekarang tidak disertakan, lihat risiko lisensi di Bagian A dan F5)

### A-Tier: menaikkan kepercayaan
- [ ] Tutup backlog `[belum dites]` (T7): v18, v28c, v29, v32 (gambar normal), jembatan 5a, RAM tab parkir, v46 sampai v50
- [ ] Tes otomatis dan CI sederhana: pindahkan uji tiruan yang sudah ada (pencocokan kata pemicu, simulasi WebSocket, pembaca `.env`) ke `tests/`, jalankan lewat GitHub Actions, pasang badge
- [ ] Cancel Hermes (2b): jalankan `cek-cancel-hermes.py` (K1); hasilnya menahan fase 5b dan 5c mini-browser
- [ ] Abstraksi TTS dan LLM: opsi selain VOICEVOX (mis. Piper atau edge-tts) dan endpoint OpenAI-compatible langsung tanpa 9Router
- [ ] Rapikan `docs/`: dokumen gabungan menyalin dua dokumen lain (T4), jadi simpan satu dan bagi menjadi beberapa file bertema supaya pendatang baru tidak tenggelam di berkas besar

### B-Tier: nilai tambah
- [ ] README versi Inggris (`README.en.md`) dan topik tambahan (`desktop-pet`, `ai-agent`, `voicevox`, `windows`)
- [ ] Rilis berseri dengan changelog (penomoran v1 sampai v51 sudah rinci; ringkas jadi catatan rilis)
- [ ] Rapikan akar repo: `cek-cancel-hermes.py`, `buat_klip_vrma.py`, `clips.json` (salinan), dan `test_client.html` ke `scripts/` atau `tools/`
- [ ] CONTRIBUTING, issue template, dan roadmap publik (hanya bila lisensi sudah memungkinkan kontribusi)
- [ ] Fitur yang sudah disetujui tapi belum ditulis (T7): `cek-elearning`, memori otomatis ringan, auto-start, menari mengikuti musik

### C-Tier: nanti
- [ ] Dukungan Live2D, macOS dan Linux, sistem plugin
- [ ] Promosi (komunitas VTuber dan LLM lokal, Show HN) hanya setelah tier S dan A selesai

## U6. Proyeksi rating (perkiraan, bukan jaminan)

| Tahap | Perkiraan |
|---|---|
| Sekarang | 7.5 |
| Selesai tier S (1 sampai 2 hari) | 8.0 |
| Selesai tier A (1 sampai 2 minggu) | 8.5 |
| Tier B dan promosi | sekitar 9.0 (kelas Open-LLM-VTuber, belum AIRI) |

## U7. Catatan

- Yang menahan rating adalah kemudahan orang lain mencobanya (lisensi, demo, aset, instalasi), bukan kualitas kode atau jumlah fitur. Jangan menambah fitur baru dulu sebelum tier S selesai.
- Dokumen ini sendiri sudah sangat panjang. Pisahkan "dokumen untuk pengguna" (README, demo, panduan singkat) dari "catatan pengembangan" (dokumen ini), dan perlakukan yang kedua sebagai arsip.
- Bagian ini belum menambah apa pun ke daftar terbuka T7; butir U5 di atas adalah usulan, belum diputuskan pemilik.
