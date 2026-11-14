# Haganai Portable: patch teks Inggris (README + laporan progres)

by: KangJiho · Terakhir diperbarui: 2026-10-16 (setelah batch 15 diterapkan; batch 16 dibuat; build v12 dibuat)

Dokumen ini menggabungkan daftar skrip, aturan kerja, hasil kalibrasi, dan status terbaru. Sumber angka: keluaran terminal `csv_tools.py fix` dan `pipeline.py` yang kamu tempel.

---

## 1. Ringkasan

Menerjemahkan **Boku wa Tomodachi ga Sukunai Portable (PSP, ULJS00459)** ke bahasa Inggris dengan mengedit `RES.DAT` langsung.

1. Teks Jepang diekstrak ke CSV (satu baris = satu dialog, narasi, atau pilihan).
2. Terjemahan Inggris ditulis di kolom `english_text`.
3. `pipeline.py` menyuntikkan teks Inggris ke `RES.DAT` (wrap dan padding otomatis).
4. `seekmap_rebuild.py` membuat `first.dat` yang cocok dengan `RES.DAT` baru.
5. Tes di PPSSPP.

Masalah utama: **kotak teks hanya muat 2 baris**, sedangkan banyak terjemahan Inggris jadi 3 atau 4 baris sehingga baris ke-3 terpotong. Solusinya memendekkan terjemahan batch demi batch (`fixes_batchN.csv`).

---

## 2. Folder

| Folder | Isi |
|---|---|
| `D:\Reverse engginering\project haganai\scripts tools` | semua skrip `.py` dan CSV kerja. **Semua perintah dijalankan dari sini** |
| `D:\Reverse engginering\project haganai\script_output\translate dialogue` | CSV sumber terjemahan |
| `D:\Reverse engginering\project haganai\data ekstrak` | game asli: `RES.DAT`, `first.dat`, `EBOOT.BIN` |

---

## 3. Inventaris data

### 3.1 CSV utama (yang diedit dan di-build)

| File | Isi |
|---|---|
| `FULL_dialogue_wrap_fixed.csv` | 15.257 baris dialog ber-speaker |
| `FULL_remaining_wrap_fixed.csv` | 7.465 baris: narasi 5.817, scene title 673, banter 610, choice 365 |
| `FULL_dialogue_wrap.csv`, `FULL_remaining_wrap.csv`, `FULL_remaining_short.csv` | versi sebelum `fixed` (cadangan) |
| `haganai_dialogue_EN_v2.csv`, `haganai_remaining_EN_full_v2.csv` | CSV sumber terjemahan (belum di-wrap, tanpa `\n`) |

### 3.2 Tambalan pemendekan (`fixes_*.csv`, kolom `type,scene,ref,speaker,jp,english_new,lines,cut`)

| File | Baris | Status |
|---|---|---|
| `fixes_2baris_0011ess0.csv` | 24 | diterapkan |
| `fixes_batch01.csv` | 51 | diterapkan (0011ess0 + 0012ess0) |
| `fixes_batch1.csv` | 24 | diterapkan |
| `fixes_batch2.csv` | 100 | diterapkan |
| `fixes_batch4_narasi.csv` | 100 | diterapkan |
| `fixes_batch5.csv` | 40 | diterapkan |
| `fixes_batch6.csv` | 60 | diterapkan |
| `fixes_batch7.csv` | 80 | diterapkan |
| `fixes_batch8.csv` | 100 | diterapkan (sisa 5.453) |
| `fixes_batch9.csv` | 150 | diterapkan (sisa 5.303) |
| `fixes_batch10.csv` | 100 | diterapkan (sisa 5.203) |
| `fixes_batch11.csv` | 100 | diterapkan (sisa 5.103) |
| `fixes_batch12.csv` | 100 | diterapkan (lebar ketat 35/37, sisa 5.741) |
| `fixes_batch13.csv` | 100 | diterapkan (sisa 5.641) |
| `fixes_batch14.csv` | 100 | diterapkan (sisa 5.541) |
| `fixes_batch15.csv` | 100 | diterapkan (sisa 5.441) |
| `fixes_batch16.csv` | 100 | **dibuat; dry-run bersih (sisa 5.341), belum dikonfirmasi diterapkan di terminal** |
| **Total diterapkan** | **1.329** | dengan batch 16 menjadi 1.429 |

Batch 10 sampai 12 ditulis dari `next_all.csv` (baris terparah dulu, `cut` terbesar). Batch 13 sampai 16 ditulis dari worklist yang dibuat ulang tiap kali dengan lebar ketat (`fix --worklist ... --width 35 --nwidth 37`), jadi sinkron dengan CSV terbaru. Semua teks di batch itu sudah diperiksa muat 2 baris pada lebar ketat (dialog 35, narasi 37) dan memakai `’`.

Format kolom `batch01` berbeda (`sumber,scene,id,english_text`); `batch1` sampai `batch7` hanya `type,scene,ref,english_new`. Batch 10 ke atas memakai `type,scene,ref,speaker,jp,english_new,lines,cut`.

### 3.3 Choice

| File | Baris | Keterangan |
|---|---|---|
| `choice_full.csv` | 818 | semua entri choice 37 instruksi yang di-skip (kolom `status`) |
| `choice_todo.csv` | 29 | choice yang `english_text`-nya kosong |
| `choice_todo_terisi.csv` | 29 | terjemahan 29 entri tadi; **sudah digabung** (`fill-todo`: 29 terisi, 0 tidak cocok) |
| `choice_fixes (1).csv` | 209 | usulan pendek (maks 22 kolom); **sudah diterapkan** (209/209) |
| `choice_fixes_todo.csv` | 20 | pendekan 20 choice dari `choice_todo_terisi` yang > 22 kolom; **sudah diterapkan** (20/20) |
| `choice_long.csv`, `choice_pendek.csv`, `choice_unik.csv`, `choice_terlalu_panjang.csv` | | daftar kerja lama |

### 3.4 Teks > 2 baris (overflow)

| Titik waktu | Total | Dialog | Narasi |
|---|---|---|---|
| laporan awal (2026-10-15) | 5.636 | 3.491 | 2.145 |
| setelah batch 8 | 5.453 | 3.387 | 2.066 |
| setelah batch 9 | 5.303 | 3.294 | 2.009 |
| setelah batch 11 (lebar bawaan 37/39) | 5.103 | 3.181 | 1.922 |
| setelah batch 11 (**lebar ketat 35/37**) | 5.841 | | |
| setelah batch 12 (ketat) | 5.741 | 3.610 | 2.131 |
| setelah batch 13 (ketat) | 5.641 | 3.553 | 2.088 |
| setelah batch 14 (ketat) | 5.541 | 3.484 | 2.057 |
| setelah batch 15 (ketat) | **5.441** | **3.420** | **2.021** |
| setelah batch 16 (ketat, dry-run) | 5.341 | 3.359 | 1.982 |

**Mulai batch 12, semua angka diukur dengan lebar ketat (`--width 35 --nwidth 37`).** Angka lama (sampai batch 11) memakai lebar bawaan `csv_tools.py` (37 dan 39), jadi tidak sebanding. Perintah `fix` tanpa opsi lebar memakai bawaan itu; selalu tambahkan `--width 35 --nwidth 37`.

`next_all.csv` lama (5.453 baris, dibuat setelah batch 8) sudah usang. Buat ulang tiap batch dengan:
```
python csv_tools.py fix --worklist next_all.csv --limit 0 --max-lines 2 --width 35 --nwidth 37 FULL_dialogue_wrap_fixed.csv FULL_remaining_wrap_fixed.csv
```
(terakhir ditulis: 5.641 baris, setelah batch 13).

### 3.5 Hasil tes kalibrasi (boleh diarsipkan)

`dlg_ruler*.csv`, `rem_ruler.csv`, `dlg_lines.csv`, `rem_lines.csv`, `dlg_2baris.csv`, `rem_2baris.csv`, `TEST_*_0011ess0.csv`, `skip_ruler.csv`, `skip_test.csv`.

### 3.6 Laporan skip tiap build

Terbaru: 37 baris, dua penyebab:

| Alasan | Jumlah | Artinya |
|---|---|---|
| `jumlah pilihan beda` | 10 | semua `0000Index` inst#101 sampai 110. Menu pemilih scene (debug), isinya nama scene. **Aman diabaikan** |
| `ada english_text kosong` | 27 | choice yang punya baris kosong. **Seharusnya sudah hilang** karena `fill-todo` dijalankan (lihat 5.2); `skip_v12.csv` belum diperiksa |

### 3.7 Dump dan catatan analisis

- `dump_choice.txt`, `dump_fail.txt`, `dump_scene.txt`: dump byte instruksi choice (opcode 103).
- `index_preview.txt`: isi `0000Index`. Entri terakhir inst#110 = 戻る/Back; sisanya nama scene seperti `0048ess2`, `_omake_kob`.

---

## 4. Skrip

| File | Isi |
|---|---|
| `pipeline.py` | build: `python pipeline.py RES.DAT dialogue.csv remaining.csv OUT.DAT [opsi]` |
| `csv_tools.py` | `fix`, `short`, `choice-fixes`, `choice-short`, `choice-gaps`, `choice-missing`, `fill-todo`, `long-choices`, `encoding`, `verify-length` |
| `dump.py` | `obj`, `inst`, `hex`, `tree`, `entry`, `scan`, `find`, `text`, `gpda-entry`, `seekmap-pos` |
| `calibrate.py` | `ruler`, `ruler2`, `apos`, `apos-test`, `lines` |
| `tests.py` | tes keamanan (identity rebuild, seekmap, dll) |
| `extract.py` | ekstraksi awal dan cek dialog |
| `seekmap_rebuild.py` | membuat `first.dat` baru |

Skrip lepas buatan Claude (`apply_short.py`, `fill_todo.py`, `choice_gaps.py`, `shorten_pass.py`) fungsinya sudah tercakup `csv_tools.py`; boleh diarsipkan.

### Struktur data game

```
RES.DAT (GPDA) -> script.dat (GPDA, 674 entri) -> "_<stem>.dat" (GPDA)
   -> entri 0 (GPDA) -> "*.obj.gz" -> .obj.bin
```

- Container GPDA: semua entri di-pad ke kelipatan 2048, termasuk yang terakhir.
- Opcode 100 = dialog/narasi (dialog kuncinya `file + offset`; narasi `scene + inst_index`).
- Opcode 103 = choice/menu (`scene + inst_index + str_index`). Format: header 10 byte, lalu tiap entri `target(u32), len(u32), teks UTF-16LE, flag(u32)`; `flag=1` diikuti ekstensi.
- Pengaman: file yang gagal parse atau verify tidak dipatch (Jepang asli utuh), alasannya masuk laporan skip.

---

## 5. Status progres (2026-10-16)

### 5.1 Dialog dan narasi (batas 2 baris)

| Hal | Status |
|---|---|
| Sisa > 2 baris (setelah batch 15, lebar ketat) | **5.441** (dialog 3.420, narasi 2.021) |
| Tambalan diterapkan | 1.329 baris; batch 16 menunggu |
| Scene title (673) dan banter (610) | tidak dipatch (format belum di-reverse), tetap Jepang |
| Laju | 100 teks per batch, jadi sekitar 53 batch lagi bila terus begini. Bisa dinaikkan ke 200 per batch kalau tes game lolos |

### 5.2 Choice

| Hal | Status |
|---|---|
| Total baris choice | 365 (336 asli + 29 hasil `choice-missing`) |
| Choice > 38 kolom | 0 |
| 29 choice kosong | **selesai.** `fill-todo` sudah dijalankan; keluaran `fix` sekarang `kosong 0` |
| `choice_fixes (1).csv` (209) dan `choice_fixes_todo.csv` (20) | **sudah diterapkan** (batas 22 kolom); `choice masih > 38 kolom: 0` |
| 10 instruksi `0000Index` | diabaikan, menu debug |

Catatan tampilan: gelembung di belakang pilihan lebarnya tetap (sekitar 19 karakter). Teks yang lebih panjang keluar dari gelembung tapi masih terbaca; batas keras layar sekitar 41 karakter. Screenshot tes ("Give a quick rundown", "Girls in swimsuits") menunjukkan choice muat dan terbaca.

### 5.3 Build

| Hal | Status |
|---|---|
| Build yang dites di game | v10 (apostrof, wrap, dan pilihan Inggris sudah benar; baris ke-3 hilang di scene yang sudah dipendekkan) |
| Build v11 | ada `skip_v11.csv` dan `overflow.csv` |
| **Build v12** | dibuat dengan `--max-lines 2 --width 35 --nwidth 37` dari CSV setelah batch 13 (sisa 5.641). `first_new_v12.dat` ditulis: 15.698/15.698 baris cocok, 0 mismatch, ukuran 1.052.672 byte (sama dengan `first.dat` asli, seekmap muat di slot). **Tes game v12 belum dilaporkan** |
| Rebuild `first.dat` | wajib setiap build, dan pasangan `RES` + `first.dat` harus dari build yang sama |

**Temuan tes PPSSPP (build lama, kemungkinan v11):**

| Hal | Hasil |
|---|---|
| Choice | muat dan terbaca |
| Apostrof `’` | tampil benar |
| Baris ke-3 | masih ada di teks yang belum dipendekkan (wajar) |
| **Huruf nyelip** | huruf pertama kata berikutnya muncul di ujung baris atas: "explain the **N** / eighbors Club?" dan "The **w** / ater’s cold". Berbeda dari masalah lama ("shoul / d") |

Dugaan (belum diverifikasi, `pipeline.py` belum dilihat): font proporsional, jadi baris yang banyak huruf sempit (`I`, `l`, `t`, spasi) masih punya ruang, sedangkan padding berbasis jumlah kolom tidak mengisinya penuh sehingga engine meletakkan huruf pertama kata berikutnya di sisa ruang itu. Karena itu **menurunkan `--width` tidak akan memperbaikinya**, dan menaikkannya mengembalikan "shoul / d". Arah perbaikan: (1) pad berlebih supaya engine yang melipat, perlu dites apakah baris berikutnya jadi menjorok; (2) wrap dan pad berbasis piksel memakai tabel lebar huruf dari `calibrate.py ruler`. Perlu tes v12 dulu untuk memastikan masih terjadi.

---

## 6. Cara kerja

Semua dijalankan dari `scripts tools`:

```
cd "D:\Reverse engginering\project haganai\scripts tools"
```

### 6.1 Memendekkan dialog dan narasi

```
python csv_tools.py fix --worklist next_all.csv --limit 0 --max-lines 2 --width 35 --nwidth 37 FULL_dialogue_wrap_fixed.csv FULL_remaining_wrap_fixed.csv
python csv_tools.py fix --max-lines 2 --width 35 --nwidth 37 fixes_batchN.csv FULL_dialogue_wrap_fixed.csv FULL_remaining_wrap_fixed.csv
```

Yang kedua harus menghasilkan `ditolak: 0 | tidak ketemu: 0`. Terapkan batch berurutan. Jangan menerapkan batch yang sama dua kali.

### 6.2 Build

```
python pipeline.py "D:\Reverse engginering\project haganai\data ekstrak\RES.DAT" FULL_dialogue_wrap_fixed.csv FULL_remaining_wrap_fixed.csv RES_patched_v12.DAT --max-lines 2 --width 35 --nwidth 37 --report skip_v12.csv
python seekmap_rebuild.py build RES_patched_v12.DAT "D:\Reverse engginering\project haganai\data ekstrak\first.dat" first_new_v12.dat
```

`--width 35 --nwidth 37` disarankan (lihat bagian 7). Kalau `pipeline.py` menolak opsi itu, cek bantuannya. Pasang `RES_patched_v12.DAT` dan `first_new_v12.dat` sebagai pasangan; jangan campur dengan versi lain. Jangan tes lewat save state.

### 6.3 Menyelesaikan choice (SUDAH DIJALANKAN 2026-10-16; disimpan sebagai catatan)

```
python csv_tools.py fill-todo FULL_remaining_wrap_fixed.csv choice_todo_terisi.csv FULL_remaining_wrap_fixed.csv
python csv_tools.py choice-fixes "choice_fixes (1).csv" FULL_remaining_wrap_fixed.csv
python csv_tools.py choice-fixes choice_fixes_todo.csv FULL_remaining_wrap_fixed.csv
```

`fill-todo` dulu, baru dua `choice-fixes`. Hasil: 29 terisi, 209/209 dan 20/20 diperbarui, `fix` melaporkan `kosong 0`. Tiap `choice-fixes` membuat file `.bak` baru (normal).

---

## 7. Hasil kalibrasi (PPSSPP v1.20.4, scene 0011ess0)

- **Tinggi kotak: 2 baris.** Baris ke-3 jatuh di tepi bawah layar. Dikonfirmasi lewat screenshot fullscreen dan tes teks Jepang asli.
- **Teks Jepang asli tidak pernah lebih dari 2 baris.** Satu baris Jepang memuat sekitar 27 sampai 28 karakter. Teks Jepang terpanjang yang terlihat (tanpa ruby) 49 karakter untuk dialog dan 51 untuk narasi, jadi tidak ada bukti game punya mekanisme halaman kedua. Narasi 0011ess0 inst#85 (44 karakter) tampil 27 + 18 karakter di 2 baris, bukan lebih dari 2 baris.
- **Lebar baris untuk huruf biasa kira-kira 37 kolom (narasi).** Pada build lebar 39, kata "should" terbelah jadi "shoul / d". Angka 39 dari tes ruler (angka dan huruf "i") terlalu besar. Dialog ber-speaker diperkirakan 35 (belum diukur langsung).
- Fontnya tampak proporsional, jadi padding spasi hanya aman bila lebar wrap tidak melebihi kapasitas sebenarnya.
- Lebar karakter di metrik: ASCII = 1, apostrof `’` = 1,5, non-ASCII lain = 2. Apostrof ASCII `'` tampil sebagai ♠, jadi selalu pakai `’`. Karakter `é`, `①`, `…`, `π` (sekitar 17 baris) berisiko tampil sebagai ♠.
- `\n` di teks tampil sebagai ♠; engine melipat baris sendiri.

---

## 8. Aturan kerja

| Jenis | Lebar | Tinggi | Target saat menulis |
|---|---|---|---|
| Dialog | 35 kolom (ketat) | maks 2 baris | sekitar 58 karakter |
| Narasi | 37 kolom | maks 2 baris | sekitar 66 karakter |
| Choice | 22 kolom (sementara) | 1 baris | 36 adalah batas keras |

1. Hitung dulu, baru tulis. Cek dengan `csv_tools.py fix`.
2. Pendekkan, jangan paksa muat.
3. Makna tetap utuh. Boleh dibuang: pengulangan, keterangan yang jelas dari konteks. Tidak boleh: nama, angka, inti pertanyaan atau jawaban.
4. Hanya `english_text` yang diubah.
5. Choice yang bersebelahan harus tetap beda.
6. Pakai `’` (U+2019) di file batch.
7. Istilah tetap: Meat, Onii-chan, Aniki, senpai, nama karakter.

---

## 9. Pelajaran dan jebakan

- Jalankan dari folder `scripts tools`. `FileNotFoundError` pada CSV berarti file belum ada di folder itu.
- Placeholder `<...>` di contoh perintah bukan nama file; PowerShell menolak tanda `<`.
- Terapkan batch berurutan; `tidak ketemu` > 0 berarti ada batch sebelumnya yang belum diterapkan.
- Pasangan `RES` + `first.dat` harus dari build yang sama.
- Kata terbelah di tengah ("shoul / d") berarti lebar wrap lebih besar dari kapasitas engine; turunkan `--width` dan `--nwidth`.
- Jangan menebak batas baris dari satu screenshot di jendela non-16:9.
- Teks yang sama sering muncul di beberapa baris (`ref` berbeda); satu terjemahan dipakai untuk semuanya.
- `csv_tools.py fix` tanpa `--width 35 --nwidth 37` memakai lebar bawaan 37/39 dan memberi angka yang lebih kecil (menyesatkan). Selalu sertakan opsi lebar.
- `FileNotFoundError` untuk `fixes_batchN.csv` hanya berarti file belum ada di folder `scripts tools`; bukan error isi batch.
- Huruf pertama kata berikutnya nyelip di ujung baris atas ("the N / eighbors") berbeda dari kata terbelah di tengah; lihat 5.3.
- Terjemahan lama punya beberapa kutip ganda tidak berpasangan (mis. `0083mar0 0x5D73` aslinya salah arti: "prefers girls over" padahal Jepangnya 女よりも; `a490ed11` inst#499 dan `omake_sen` inst#13 punya `"` yatim). Batch 14 dan 16 sudah membersihkannya.

---

## 10. Rencana dan gerbang build

### Rencana

1. ~~Konfirmasi batch 12 diterapkan, jalankan 6.3, build v12~~ selesai (batch 12 sampai 15 diterapkan, choice beres, v12 dibuild). **Berikutnya: tes v12 di PPSSPP** (mulai game baru, tanpa save state; kalimat uji: "Southern islands vary, but picture an eternal summer paradise.", "The odd-eyed blonde is Hasegawa Kobato, my sister. I’m Kodaka.", "Don’t get carried away, brat, or no more potato chips."). Cek: huruf nyelip, kata terbelah, baris ke-3, baris kedua menjorok.
1b. Kirim `pipeline.py` (dan `calibrate.py`, `dlg_ruler.csv`/`rem_ruler.csv` bila ada) supaya masalah padding/huruf nyelip bisa dianalisis dan hitungan wrap bisa diverifikasi (sekarang wrap diperiksa dengan `pipeline.py` tiruan yang cocok dengan keluaran terminalmu sampai batch 15).
2. Terapkan batch 16, lalu lanjut memendekkan batch demi batch (sisa 5.441 sebelum batch 16). Prioritaskan scene yang paling sering dimainkan. Batch dibuat 100 baris per balasan karena batas panjang tulisan dan agar kualitas terjaga; tidak perlu digabung jadi satu file karena hasilnya sudah ada di `FULL_*_fixed.csv`. Simpan file `fixes_batch*.csv` sebagai catatan dan salin `FULL_*_fixed.csv` ke folder lain secara berkala.
3. Strategi 3 baris: pemendekan dilanjutkan; pemecahan teks jadi dua kotak butuh reverse engineering instruksi lompat dan belum dikerjakan.
4. Putuskan nasib scene title (673) dan banter (610): reverse format opcode 700 dan 1012/1013, atau biarkan Jepang.
5. Tentukan batas pilihan (22, 30, atau 38) lewat screenshot. Tes awal: pilihan 22 kolom muat; pilihan yang lebih panjang keluar dari gelembung tapi terbaca.
6. Arsipkan file tes dan skrip lepas.

### Gerbang sebelum build dianggap beres

- [ ] Dialog > 2 baris: 0 (sekarang 3.420, lebar ketat, setelah batch 15)
- [ ] Narasi > 2 baris: 0 (sekarang 2.021)
- [x] Choice kosong: 0
- [x] Choice > 22 kolom: 0 (209 dan 20 pendekan diterapkan; belum diverifikasi ulang dengan `long-choices --max 22`)
- [ ] Tes v12: tidak ada huruf nyelip dan tidak ada kata terbelah
- [ ] Screenshot PPSSPP 3 sampai 5 sampel terparah tidak terpotong dan tidak ada kata terbelah
- [ ] `first.dat` di-rebuild dan dipasang sepasang dengan `RES.DAT` build yang sama
