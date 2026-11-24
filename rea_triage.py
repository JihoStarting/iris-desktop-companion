"""rea_triage.py - triase statis lokal untuk perintah /rea (Iris v99.22, kumulatif dengan v99.21, v99.20, v99.19, v99.18, v99.17, v99.16, v99.15, v99.14, v99.13, v99.12, v99.11, v99.10, v99.9, v99.8, v99.7, v99.6, v99.5, v99.4, v99.3, v99.1, v99.0, v98.6, v97, v96, v95, v94, v93, v92, v91).  by: KangJiho

Dihitung langsung di PC oleh Python (hanya pustaka standar), TANPA LLM dan TANPA menjalankan file:
hash, jenis file, entropi, header PE / ELF / ZIP (APK, JAR), import / export, bagian (section), string menarik,
indikasi kemampuan, dan tanda-tanda packer. Hasilnya dipakai dua cara:
  1. mode `/rea cepat`: langsung jadi laporan (hitungan detik, tanpa Hermes, akurat karena murni hitungan);
  2. mode standar / dalam: disisipkan ke tugas Hermes sebagai FAKTA TERUKUR, supaya agen tidak perlu menebak
     dan tidak bisa mengarang hal dasar (hash, format, import).

API:
    triage(path) -> dict
    render(rep, compact=False) -> str
    triage_text(path, compact=False) -> str

Penggabungan modul (23 Nov 2026, VERSION tetap): rea_extract.py (v95) dan rea_binary.py (v96) kini menjadi bagian berkas ini, seperti rea_assets.py;
    berkas terpisahnya tidak diperlukan lagi (lihat bagian "rea_binary.py ... rea_extract.py DIGABUNG" di dekat akhir berkas). CLI lewat --bin / --ex.

v95: modul triase ini TIDAK berubah perilakunya. Ekstraksi / penjelajahan container dipisah ke rea_extract.py
(ZIP, TAR/gz, GZIP, ISO 9660, ISO PSP). Fungsi tipis di bawah hanya meneruskan ke sana (impor malas, opsional):
    container_text(path, max_chars=0) -> str      daftar isi ringkas untuk laporan / Hermes
    container_extract(path, outdir, pattern=None, scan=False) -> dict   ekstraksi selektif + manifest

v96: Binary Workbench dipisah ke rea_binary.py (hex view, data inspector, pencarian, compare, patch dengan undo).
    hex_text(path, offset=0, length=256) -> str ; compare_text(a, b) -> str   (jembatan tipis, impor malas)

v97 (lebih bertenaga; API lama tidak berubah, semua tambahan bersifat aditif):
    - Mach-O penuh (tipis + universal): arsitektur, platform, load command, dylib / RPATH, segmen + entropi, tanda tangan, enkripsi, UUID,
      simbol impor / ekspor (ikut dipetakan ke kemampuan + ATT&CK);
    - metadata .NET: versi runtime, stream, nama dari #Strings, string pengguna #US (masuk ke IOC), kemampuan dari nama P/Invoke / kripto,
      dugaan obfuskasi;
    - CTPH (hash fuzzy gaya ssdeep): ctph(data), ctph_compare(x, y), similarity(a, b), similar_text(a, b);
    - perburuan satu-byte XOR / ADD / ROL untuk URL, stub DOS, dan nama API tersembunyi;
    - detail kemasan: PyInstaller (versi Python + skrip masuk dari TOC), UPX, NSIS, Inno Setup, Go, Rust, AutoIt, SFX 7-Zip, PyArmor;
    - triage_dir mengelompokkan keluarga sampel (imphash, rich header, UUID Mach-O, opsional CTPH dengan fuzzy=True);
    - triage_md(path): laporan Markdown; rea_api(request): satu pintu JSON untuk Iris / Hermes (pembatas path: env REA_ROOTS, atau akar bawaan dari set_default_roots() yang dipasang server.py).

v96.1 (pengerasan): berkas dibuka sekali dengan fstat (tolak FIFO / perangkat / folder, tanpa TOCTOU); batas kerja entropi / MD5
    per bagian (header bagian tumpang-tindih tidak bisa memakan CPU); ZIP dibaca dengan batas dekompresi dan jumlah entri;
    keluaran dibersihkan dari baris baru / pemisah baris (anti injeksi laporan); perbaikan nama impor PE bila RVA tak terpetakan.

v98 (RE Lab, khusus reverse engineering PE x86 / x64; semua aditif, tetap statis dan hanya pustaka standar):
    - penemuan fungsi (entry + ekspor + target CALL + prolog) dan PETA PANGGILAN API per fungsi (CALL [IAT], thunk JMP, pointer IAT);
    - xref string (LEA RIP-relatif / PUSH imm32) -> fungsi mana memakai string apa; peringkat fungsi menarik per kelompok kemampuan;
    - anti-analisis tingkat instruksi: PEB / TEB, RDTSC, CPUID, INT 2D, SIDT, syscall langsung (SysWhispers / Hell's Gate), Heaven's Gate;
    - API hashing (ror13 block_api; tabel hash dihitung saat runtime), stack string, stub entry point;
    - re_lab_path(path), re_text(path), xref_text(path, query), disasm_text(path, at, count) (disassembler memakai capstone bila terpasang);
    - v98.1: disasm juga untuk ELF, Mach-O (tipis / fat) dan berkas mentah / shellcode (x86 x64 arm thumb arm64 mips ppc riscv ...), arch= memaksa arsitektur;
    - v98.2: aturan kemampuan berbasis API dari mandiant/capa-rules (subset, tingkat berkas, petunjuk saja); unpack UPX opsional (`--unpack FILE OUTDIR`, aksi API `unpack`, butuh alat `upx`);
    - v98.3: APK lebih dalam (AndroidManifest biner: paket / SDK / komponen / aksi intent; DEX: metode API sensitif + dugaan obfuskasi), dekoder skrip
      (PowerShell -EncodedCommand, FromBase64String, [char] / Chr() / fromCharCode, \\xNN), hash ikon PE, `--yarascan FILE RULES` (butuh yara-python);
    - v98.4: RE Lab juga untuk ELF x86 / x86-64 (peta PLT / GOT -> nama impor, nama fungsi dari .symtab / .dynsym, xref string, peringkat fungsi);
    - aksi API baru: re, xref, disasm; CLI: --re FILE | --xref FILE QUERY | --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N].

v98.5 (akurasi triase PE; mengurangi alarm palsu, tanpa mengubah API):
    - OriginalFilename dibandingkan tanpa ekstensi (launcher == launcher.exe);
    - 'persistensi' tidak lagi cocok dengan GetStartupInfo; kecocokan kemampuan dipisah: tabel import / string khas (kuat) vs nama API
      yang hanya muncul sebagai teks (lemah, tidak ikut skor kecuali API injeksi);
    - blok PKCS#7 tanda tangan Authenticode dikecualikan dari ekstraksi string / IOC (header dan byte sisa tetap dipindai; byte sisa
      yang tak berstruktur diberi peringatan); kandidat IP yang sama dengan nomor versi file dibuang;
    - resource PNG / JPEG / ZIP yang strukturnya utuh tidak lagi ditandai 'payload terenkripsi' dan tidak ikut skor / wilayah entropi tinggi
      (magic palsu atau data tambahan setelah IEND tetap ditandai);
    - baris 'Faktor penyeimbang' di laporan PE (hal lazim pada file sah; bukan jaminan aman).

v98.6 (integritas, kalibrasi, derau; API lama tidak berubah, semua tambahan aditif):
    - integritas tanda tangan Authenticode: hash Authenticode dihitung ulang (sha256 / sha1 / md5 sesuai blob) dan dibandingkan dengan digest
      di SpcIndirectDataContent. Tidak cocok = file diubah setelah ditandatangani (+3). Rantai sertifikat dan pencabutan TETAP tidak diperiksa;
      CN penandatangan dibandingkan dengan CompanyName (hanya informasi);
    - daftar hash lokal (env REA_KNOWN_HASHES): berkas teks, satu baris `HEX [good|bad|note] [label]`; 'bad' menambah skor, 'good' masuk faktor penyeimbang;
    - peredam derau CRT: IsDebuggerPresent / GetProcAddress / LoadLibrary / CreateFile pada PE native dilipat di 'Indikasi kemampuan' dan tidak
      masuk pemetaan ATT&CK bila itu satu-satunya bukti kemampuan tsb (HANYA tampilan: skor tidak berubah, kalibrasi skor lewat rea_calibrate.py);
    - entropi bagian .rsrc dihitung tanpa resource PNG / JPEG / ZIP yang utuh (ditandai * di baris Bagian);
    - XOR kunci berulang 2-16 byte untuk stub DOS (known-plaintext; RC4 tidak bisa diburu tanpa kunci), dan resource terkelola .NET
      (ManifestResource lewat header CLR: MZ di dalam resource, blob berentropi tinggi);
    - mode kartu: render(rep, card=True) / triage_text(..., card=True) / `--card` / rea_api {"card": true}: skor, alasan, penyeimbang, PERHATIAN dulu;
      rincian import dan string dilipat. Alat kalibrasi bobot: rea_calibrate.py; tes: tests/test_rea_triage.py.

v99.0 (Asset Explorer; modul baru rea_assets.py, impor malas seperti rea_extract / rea_binary; triase PE di atas TIDAK berubah):
    REA tidak lagi terbatas pada .exe: model 3D (glTF/GLB, OBJ, STL, PLY, FBX, COLLADA), animasi (glTF, FBX, BVH), tekstur (DDS, TGA, BMP, PNG, ...),
    audio, arsip / paket game (Quake PAK, WAD, Unreal .pak v1-v11, ZIP / APK / JAR, TAR / GZIP), SQLite, dan carving berkas tertanam di berkas apa pun.
    - assets_text(path) -> str ; assets_extract(path, outdir, pattern=None, convert=True) -> dict ; assets_carve(path, outdir=None) -> dict
    - aksi API baru: assets, assets_extract, assets_carve, formats; CLI: --assets FILE | --assets-extract OUTDIR FILE [pola] | --assets-carve FILE [OUTDIR] | --formats
    - plugin parser buatan sendiri: env REA_PLUGINS=FOLDER atau CLI --plugins FOLDER (sengaja TIDAK bisa diminta lewat API agen, karena plugin = kode).

v99.12 (roadmap v2, Tier S butir 1b: tabel metadata .NET + IL; aditif; by: KangJiho): mengurai stream `#~` (ECMA-335: TypeDef, MethodDef, MemberRef, TypeRef, ImplMap, ModuleRef, AssemblyRef,
    ManifestResource, NestedClass, MethodSpec) lalu memindai badan IL tiap metode (call / callvirt / newobj / ldftn) untuk memetakan relasi kelas -> metode -> panggilan.
    - P/Invoke presisi dari ImplMap (dll!fungsi <- Tipe::Metode); API .NET sensitif (Process.Start, Assembly.Load, WebClient, Convert.FromBase64String, Registry ...) dikelompokkan
      per metode pemanggil; rantai panggilan statis dari titik masuk / Main / .cctor modul ke pemanggil API sensitif (kedalaman <= 5);
    - nama resource terkelola (ManifestResource), AssemblyRef, kandidat dekoder (xor + loop), metode fan-in tinggi (pembantu string / dekripsi obfuskator), badan IL tak valid (IL dienkripsi);
    - kunci baru rep["dotnet_il"]; peringatan "IL .NET: ..."; CLI `--net FILE [--compact] [--raw]`, aksi API {"action": "dotnet", "path": ...}, fungsi net_text(path). Triase lama dan skor tidak berubah.
    - batas sumber daya: NETIL_TIME (4 dtk), NETIL_MAX_METHODS, NETIL_MAX_BODY, NETIL_MAX_BYTES, NETIL_MAX_ROWS; hasil ditandai TERPOTONG bila batas tercapai.
    - batasan: refleksi / delegate / pemanggilan lewat interface yang dibongkar saat runtime tidak terlihat; hanya `#~` (tanpa `#-`); hasil adalah petunjuk, bukan bukti.

v99.13 (roadmap v2, Tier S butir 3: CFG + kompleksitas fungsi; aditif; by: KangJiho): RE Lab (PE / ELF x86 / x86-64) kini punya decoder panjang instruksi murni Python (tanpa capstone)
    dan penelusuran rekursif dari awal fungsi: blok dasar, sisi (JMP / Jcc / LOOP / fall-through), kompleksitas siklomatik (E - N + 2), loop alami (sisi balik).
    - kandidat loop dekripsi: loop kecil yang menulis ke memori dengan XOR / ROL / ROR / SHD / ADD / SUB; kandidat control-flow flattening: satu blok dispatcher dengan banyak sisi balik;
    - kunci baru info["cfg"] (relab) dan kunci cc / blocks / loops pada info["functions"]; baris "CFG:" di laporan; peringatan RE Lab untuk loop dekripsi / flattening;
    - CLI `--cfg FILE [entry|0xVA]` (tanpa alamat: ringkasan; dengan alamat: daftar blok dasar + sisi + kepala loop), aksi API {"action": "cfg", "path": ..., "at": ...}, fungsi cfg_text(path, at);
    - batas sumber daya: CFG_TIME (4 dtk), CFG_MAX_FUNCS, CFG_MAX_INSNS, CFG_MAX_FUNC_INSNS, CFG_MAX_LOOPS; hasil ditandai TERPOTONG bila batas tercapai. Skor tidak berubah.
    - batasan: jump table (JMP tak langsung) tidak diselesaikan (dihitung +1 pada cc); kode tak terdecode menghentikan jalur itu (fungsi ditandai tidak lengkap); hanya x86 / x86-64.

NOTICE: _CAPA_RULES diturunkan dari aturan mandiant/capa-rules (c) Mandiant / Google, lisensi Apache-2.0
(https://github.com/mandiant/capa-rules). Hanya nama aturan, ATT&CK, dan daftar API yang dipakai ulang; telah diubah bentuk dan disaring.

v99.22 (roadmap v2, Tier A butir 4 'RE Lab Mach-O / ARM', TAHAP 1 dari beberapa; aditif; by: KangJiho): peta alamat ELF ARM / AArch64 dan Mach-O ARM / ARM64 (tipis + fat; arm64 diutamakan)
      lewat _arm_layout() / _macho_layout() dan _elf_layout(d, arm=True): segmen, bagian kode, slot impor (GOT / la_symbol_ptr), stub Mach-O, simbol fungsi, penanda Thumb, entry, cryptid.
      Murni stdlib. BELUM disambungkan ke _relab_any / triage() / rea_api (decoder ARM64 menyusul di tahap 2), jadi keluaran yang ada tidak berubah. Jalur x86 / x64 tidak berubah (diuji identik pada ELF nyata).
      Diuji dengan ELF dan Mach-O sintetis buatan sendiri serta 12.000 berkas rusak acak; belum diuji pada biner ARM nyata.
v99.21 (roadmap v2, Tier A: SerializedFile Unity; aditif; by: KangJiho): parser Unity dari gamelab (SerializedFile v13-v22, TypeTree, Texture2D / Mesh / AnimationClip / TextAsset) kini terhubung ke inti.
      Asset Explorer: `--assets` pada UnityFS menampilkan objek per kelas; `--assets-extract` (tanpa pola, convert=True) menulis objek ke unity_objects/<Kelas>/ (PNG / OBJ / anim.json / bytes) di samping node mentah.
      Baru: unity_info / unity_text / unity_extract, CLI `--unity FILE` dan `--unity-extract OUTDIR FILE [--types ..] [--name REGEX] [--no-flip]`, aksi API {"action": "unity" | "unity_extract", ...},
      capabilities melaporkan optional_deps. Dekompresi gamelab kini lewat _unity_decomp (LZ4 murni Python, tanpa paket lz4, tanpa sys.exit di pustaka); batas UNITY_MAX_FILE / UNITY_MAX_BLOB / UNITY_MAX_OBJECTS / UNITY_TIME,
      jumlah blok / node dan ukuran array TypeTree dibatasi. Tekstur: Pillow bila ada, jatuh ke PNG murni Python untuk format tak terkompresi + DXT1 / DXT5 / BC4 / BC5 (format lain butuh texture2ddecoder).
      Batasan: build rilis tanpa TypeTree (objek tidak bisa didekode), bundle UnityCN / terenkripsi, mesh terkompresi, tekstur swizzle konsol, UnityWeb / UnityRaw. Diuji dengan bundle sintetis (TextAsset, Texture2D RGBA32 / DXT1;
      LZMA / LZ4 / tanpa kompresi); jalur Mesh dan AnimationClip belum diuji ulang; verifikasi dengan satu bundle asli kecil. Skor triase tidak berubah.
v99.20 (roadmap v2, Tier A butir 2: deobfuscation skrip berlapis; aditif; by: KangJiho): PowerShell / VBScript / JavaScript dibongkar secara STATIS (skrip tidak dijalankan).
      Inline: sambung string, -f, .Replace / -replace / Replace() / .split().join(), -join / .join, balik string, [char] / Chr() / fromCharCode, |%{[char]$_ -bxor N}, indeks $env:ComSpec / $ShellId / $pshome,
      FromBase64String dalam GetString / atob / unescape, escape \\xNN / \\uNNNN, backtick, variabel konstan (termasuk di dalam "string $var"). Pembungkus: -EncodedCommand, FromBase64String + Deflate / Gzip (+ XOR -bxor),
      iex / Invoke-Expression / [scriptblock]::Create, eval / new Function / Execute, JS packer (Dean Edwards); tiap hasil menjadi lapisan baru (DSO_MAX_LAYERS, DSO_MAX_NODES, DSO_TIME, DSO_MAX_TEXT).
      Kunci baru rep["deobf"] (None bila tidak ada), baris "Deobfuscation skrip" di laporan, skor +2 bila isi terbuka memuat pola unduh / eksekusi; CLI `--deobf FILE [--json] [--raw] [--full]`;
      aksi API {"action": "deobf", "path": ...}; fungsi deobfuscate(data), deobf_text(path).
      Batasan: bukan interpreter; string-array + rotasi gaya obfuscator.io, Microsoft Script Encoder (#@~^), AES / RC4 di skrip, dan nilai yang baru diketahui saat jalan tidak dibongkar. Diuji dengan skrip sintetis; verifikasi dengan sampel nyata.
v99.19 (roadmap v2, Tier A butir 1: Malware Config Extractor otomatis; aditif; by: KangJiho): ekstraktor statis konfigurasi tertanam (C2, mutex, kunci RC4 / XOR, campaign ID, user-agent, token bot).
      Sumber: berkas apa adanya, overlay PE, resource PE, resource terkelola .NET, wilayah berentropi tinggi, berkas mentah kecil. Pola: blok TLV beacon Cobalt Strike (XOR 0x2E / 0x69),
      token Telegram, webhook Discord, mutex Global\\ / Local\\, URL dead-drop, objek JSON / baris kunci=nilai konfigurasi. Dekode: satu-byte (XOR / ADD / ROL), XOR kunci berulang, RC4
      (kunci kandidat dari string di sekitar wilayah, kunci pengguna, atau kunci di awal blob gaya Remcos), base64, zlib / gzip, bertingkat sampai 2 lapis; hanya dekode yang menghasilkan butir yang disimpan.
      Kunci baru rep["malcfg"] (None bila kosong), baris "Konfigurasi malware" di laporan, peringatan; CLI `--config FILE [--key STR ...] [--json] [--raw]`; aksi API {"action": "config", "path": ..., "keys": [...]};
      fungsi extract_config(path), config_text(path). Token / webhook disamarkan (sha256 untuk pivot) kecuali reveal=True. Skor TIDAK berubah.
      Batas sumber daya: MCFG_TIME (4 dtk), MCFG_MAX_BLOBS, MCFG_MAX_BLOB, MCFG_MAX_KEYS, MCFG_MAX_ITEMS, MCFG_DEC_MAX, MCFG_MAX_DEPTH; hasil ditandai TERPOTONG bila batas tercapai.
      Batasan: tanpa AES / RSA, string .NET terenkripsi per-obfuskator tidak dibongkar, keluarga selain Cobalt Strike hanya lewat pola umum; hasil adalah petunjuk. Diuji dengan data sintetis; verifikasi dengan sampel nyata.
v99.18 (roadmap v2, Tier S butir 2: micro-emulation instruksi terbatas; aditif; by: KangJiho): emulator register + memori kecil murni Python untuk RE Lab (PE / ELF x86 / x86-64), STATIS (sampel tidak dijalankan).
      Mendekode string yang disusun / diobfuskasi di stack (mov imm + xor / add / sub / rol / ror / not / neg berantai) dan buffer yang didekripsi di tempat oleh loop kecil (XOR dst, kunci; ROL / ROR; dll).
      Nilai tak diketahui dilacak per bit; cabang berkondisi tak diketahui di-fork; call dilangkahi (kecuali get-PC `call $+5`). String yang sudah ada polos di berkas dibuang (bukan tersembunyi).
      Kunci baru info["emu"] (strings / buffers / analyzed / steps / partial), baris "Emulasi mikro" di laporan, peringatan RE Lab; CLI `--emu FILE [entry|0xVA]` (dengan alamat: jejak instruksi + hasil),
      aksi API {"action": "emu", "path": ..., "at": ...}, fungsi emu_text(path, at). Skor TIDAK berubah.
      Batas sumber daya: EMU_TIME (3 dtk), EMU_MAX_FUNCS, EMU_MAX_STEPS, EMU_MAX_TOTAL, EMU_MAX_FORKS, EMU_MAX_WRITES; hasil ditandai TERPOTONG bila batas tercapai.
      Batasan: tanpa API / syscall / SSE / string-op (rep movs / stos), jump table tak diselesaikan, paritas (jp) tak dimodelkan; kunci / data dari argumen atau heap tak diketahui, jadi dekripsi yang bergantung
      padanya tidak terdekode. Hasil adalah petunjuk, bukan bukti.
v99.17 (roadmap v2, Tier A: arsip game modern; aditif): Asset Explorer membuka UnityFS (daftar + ekstraksi node: LZMA / LZ4 / LZ4HC, blok info di awal / akhir, format 6-8;
      SerializedFile TIDAK diurai) dan Unreal .pak v10 / v11 (indeks path-hash UE 4.26+: entri terenkode, nama dari indeks direktori penuh; zlib dan LZ4). Dekoder LZ4 blok mentah
      murni Python (_lz4_block, keluaran dibatasi). Tanpa enkripsi (AES / UnityCN ditolak jelas). Diuji dengan berkas sintetis; kirim contoh asli kecil untuk verifikasi.
v99.16 (roadmap v2, Tier B: kurva animasi COLLADA; aditif): Asset Explorer mengekspor animasi COLLADA (.dae) ke animations/NNN_<target>.csv (satu per channel: kunci waktu + nilai
      mentah, stride 1 / 16 / lain, kolom interpolasi bila ada) dan animations/animations.json. Batas DAE_ANIM_MAX_VALUES / DAE_ANIM_MAX_CHANNELS; tanpa evaluasi atau retargeting.
v99.15 (roadmap v2, Tier B + C; aditif): export_annotations / --export FILE ghidra|ida|x64dbg [OUT] (skrip anotasi dari RE Lab), func_diff / --funcdiff A B (diff fungsi
      antar-dua biner), API export / funcdiff; sidik jari toolchain / packer diperluas (PyArmor, cx_Freeze, py2exe, PyOxidizer, Themida, VMProtect, Enigma, WiX Burn,
      Bun, Node pkg / nexe, obfuscator .NET tambahan, penanda Rust / Nuitka / PyInstaller, nama bagian packer). Lihat komentar "v99.15" di dekat _API_ACTIONS.
v99.14 (keamanan + alat tambahan; GABUNGAN rea_triage_security.patch ke v99.13; aditif, kunci lama tidak berubah): peringatan parse sebagian PE masuk rep["warn"],
      sig_check (Authenticode penuh), reputation (hash VirusTotal, opt-in), unpack_7z; API: sigcheck / reputation / unpack7z; CLI: --sigcheck, --vt, --unpack7z.
      Blok ini dulu berlabel "v99.10" di patch; diganti v99.14 karena v99.10 sudah dipakai untuk signature carving.
v99.1 (gabungan v98.6 + v99.0; tidak ada perilaku lama yang berubah, semua tambahan aditif):
    - triase PE / ELF / Mach-O dari v98.6 (integritas Authenticode, daftar hash lokal, peredam derau CRT, XOR kunci berulang,
      resource terkelola .NET, mode kartu) DIPERTAHANKAN penuh, ditambah jembatan Asset Explorer dari v99.0;
    - kolom 'Jenis' kini mengenali format aset umum (PNG, JPEG, GIF, DDS, GLB, SQLite, WAV, OGG, Quake PAK, WAD) sehingga tidak lagi
      jatuh ke 'biner tak dikenal'; berkas non-exe diberi petunjuk memakai `--assets FILE` bila rea_assets.py tersedia;
    - teks bantuan CLI memuat semua opsi (--card, --assets, --assets-extract, --assets-carve, --formats, --plugins).

v99.2 (22 Nov 2026): rea_assets.py DIGABUNG ke berkas ini (bagian "rea_assets.py ... DIGABUNG", tepat sebelum assets_text); perilaku tidak berubah, VERSION tetap "99.1".
    Berkas rea_assets.py tidak dipakai lagi. CLI mandiri `python rea_assets.py ...` diganti opsi --assets / --assets-extract / --assets-carve / --formats / --plugins di sini.

Cache hasil (23 Nov 2026): triage() dan re_lab_path() menyimpan hasilnya per SHA-256 isi berkas di rea-reports/.cache (JSON), jadi /rea cepat
    atau /rea dalam ulang pada sampel yang sama tidak menghitung ulang. Otomatis tidak terpakai bila kode ini, VERSION, atau daftar
    REA_KNOWN_HASHES berubah. env REA_CACHE=0 | REA_CACHE_DIR; CLI --no-cache | --cache-info | --cache-clear;
    API {"action": "triage", "nocache": true} dan {"action": "cache"}; triage(path, use_cache=False). Aturan: blok "Cache hasil per SHA-256".

v99.3 (roadmap [C3] Secret Scanner; aditif, kunci lama tidak berubah):
    - pemindai rahasia berformat khusus: AWS access key (AKIA / ASIA ...), token GitHub (ghp_ / github_pat_ ...), token bot Telegram, webhook
      Discord / Slack, token Slack, kunci API Google, kunci Stripe live, JWT, dan URI database berkredensial (postgres / mysql / mongodb /
      redis / amqp / mssql). Hasil di ind["secrets_typed"] ("jenis: nilai-tersamar"); nilai tidak pernah ditulis utuh. Contoh dokumentasi
      (mengandung EXAMPLE) dan sandi placeholder dibuang. Ikut ke skor / peringatan seperti "kandidat kredensial" yang lama.

v99.4 (roadmap [B3] mitigasi ELF / Mach-O; aditif):
    - ELF: elf["hard"] = PIE, RELRO (partial / full), NX (PT_GNU_STACK), stack canary (__stack_chk_fail), FORTIFY_SOURCE (jumlah impor *_chk),
      RPATH / RUNPATH dari .dynamic; baris "ELF mitigasi" di laporan. Biner statis / stripped bisa tampak kurang: ini petunjuk, bukan vonis.
    - Mach-O: mo["sig"] dari SuperBlob LC_CODE_SIGNATURE: hardened runtime, ad-hoc, sandbox, kunci entitlements (XML) dan entitlements berisiko
      (allow-jit, disable-library-validation, allow-dyld-environment-variables, get-task-allow, task_for_pid-allow, com.apple.private.*).

v99.5 (roadmap [C1] artefak jaringan statis; aditif): ind["net"] = User-Agent (header dan string Mozilla/...), permintaan + header HTTP mentah
    (nilai Cookie / Authorization disamarkan), label DNS ter-encode (base32 / hex panjang), sertifikat PEM tertanam, konfigurasi proxy
    (socks / port umum, kunci ProxyServer dll.), dan named pipe (\\\\.\\pipe\\...; pola Cobalt Strike / PsExec diberi tanda). Hanya teks; tidak ada koneksi.

v99.6 (roadmap [A3] pemetaan objek COM; aditif): rep["com"] = kelompok objek COM yang dikenal dari GUID CLSID / IID di PE (biner 16-byte atau string
    {GUID} ASCII / UTF-16): BITS, WMI, Task Scheduler, DCOM (ShellWindows / ShellBrowserWindow / MMC20), host skrip (WScript.Shell, FSO, ADODB.Stream),
    klien HTTP, otomasi IE, elevasi COM / bypass UAC (CMSTPLUA, CMLUAUTIL, IFileOperation), firewall; plus API COM yang diimpor dan GUID string lain
    di luar daftar. Peringatan hanya untuk DCOM dan elevasi COM. GUID ada di tuple _COM_GUIDS (mudah ditambah). Petunjuk, bukan bukti pemakaian.

v99.7 (roadmap [B4] laporan HTML interaktif; aditif): triage_html(path, defang=True) -> str dan triage_html_file(path, out=None) -> path; CLI `--html FILE [OUT.html]`
    (bawaan: <nama>.rea.html di folder kerja; --raw mematikan defang). Satu file mandiri tanpa sumber luar: navigasi antar-bagian, tabel bagian / segmen, tabel impor
    dengan filter, IOC + artefak (URL, rahasia disamarkan, jaringan, COM) dengan pencarian, kemampuan, dan laporan teks penuh yang bisa dicari. Semua nilai di-escape
    (nama / string sampel tidak bisa menyuntik HTML); mengikuti tema terang / gelap peramban. Tidak mengubah triage() maupun rea_api().

v99.8 (roadmap [A4] BC4 / BC5; aditif): Asset Explorer mendekode tekstur DDS BC4 (ATI1 / BC4U / BC4S, DXGI 80 / 81) ke PNG abu-abu dan BC5 (ATI2 / BC5U / BC5S, DXGI 83 / 84)
    ke PNG dua kanal; pada BC5 kanal B direkonstruksi sebagai Z peta normal (dicatat di manifest). Hanya mip pertama; BC6H / BC7 / ASTC masih belum.

v99.9 (roadmap [C2] dekoder multi-layer; aditif): rep["layers"] = rantai dekode otomatis (hex / base64 -> gzip / zlib / deflate mentah -> XOR satu-byte), maksimal 3 lapis,
    pada string skrip (blob base64, FromBase64String, -EncodedCommand), resource PE, dan resource terkelola .NET; blob base64 di dalam teks hasil dekode ikut diikuti.
    Rantai hanya dilaporkan bila ujungnya dikenali (PE / ELF / ZIP / OLE2 / PDF / teks nyata); batas CHAIN_TIME, CHAIN_MAX_OUT (anti zip-bomb). Executable di ujung rantai +3 skor.
    Belum: XOR kunci berulang dan RC4 di dalam rantai (butuh kunci / known-plaintext).

v99.10 (roadmap v2, Tier C: signature carving; aditif): `--assets-carve` / assets_carve kini juga memotong modul WebAssembly (.wasm, section divalidasi urutan kanonik),
    SQLite WAL (salt frame = salt header), sertifikat X.509 PEM dan DER (struktur TBS + signatureAlgorithm divalidasi), kunci privat PEM (label BEGIN = END), dan frame Zstandard
    (panjang persis dari header block). Hanya kandidat dengan panjang valid yang dilaporkan (_CARVE_NEED_LEN), jadi magic yang kebetulan muncul tidak jadi positif palsu.

v99.11 (roadmap v2, Tier S butir 1: analisis bytecode Dalvik; aditif; by: KangJiho): modul DEX membaca INSTRUKSI di code_item tiap metode `classes*.dex`, bukan hanya tabel method_ids.
    - pelacakan nilai lurus per-blok (const-string, const, move, fill-array-data, StringBuilder.append / toString, String.getBytes, Base64.decode) sampai ke argumen
      API sensitif: nomor SMS, perintah Runtime.exec, nama transformasi Cipher (ECB / bawaan = lemah), kunci SecretKeySpec / IV hard-coded, jalur DexClassLoader, URL;
    - rantai panggilan statis dari kelas komponen manifest (activity / service / receiver / provider / Application) ke pemanggil API sensitif (sisi invoke, kedalaman <= 5);
    - kunci baru: dex_info["code"] (APK) dan rep["dex_code"] (DEX mentah); peringatan "DEX bytecode: ..." untuk kunci hard-coded, exec shell, pemuatan kode dinamis;
      CLI `--dex FILE [--compact] [--raw]`, aksi API {"action": "dex", "path": ...}, fungsi dex_text(path). Triase lama tidak berubah.
    - batas sumber daya: DEX_CODE_TIME (6 dtk per APK), DEX_CODE_MAX_INSNS, DEX_CODE_MAX_UNITS, DEX_CODE_MAX_EDGES, DEX_CODE_MAX_FILES; paket pustaka populer dilewati; hasil ditandai TERPOTONG bila batas tercapai.
    - batasan: pemanggilan virtual / antarmuka, refleksi, dan nilai yang masuk lewat percabangan tidak diselesaikan; hasil adalah petunjuk, bukan bukti.

NOTICE: _CAPA_RULES diturunkan dari aturan mandiant/capa-rules (c) Mandiant / Google, lisensi Apache-2.0
(https://github.com/mandiant/capa-rules). Hanya nama aturan, ATT&CK, dan daftar API yang dipakai ulang; telah diubah bentuk dan disaring.
"""
from __future__ import annotations

import base64
import bisect
import collections
import os
import time
import datetime as _dt
import hashlib
import itertools
import json
import math
import re
import array
import stat
import struct
import sys
import zipfile
from pathlib import Path

MAX_SCAN = 32 * 1024 * 1024          # byte yang dipindai untuk string / parsing (file lebih besar: awal file saja)
ENT_SAMPLE = 4 * 1024 * 1024         # sampel untuk entropi keseluruhan
SEC_ENT_SAMPLE = 1 * 1024 * 1024     # sampel per bagian PE
ENT_BUDGET = 32 * 1024 * 1024        # total byte yang boleh dihitung entropinya lewat semua bagian PE / ELF
MD5_BUDGET = 256 * 1024 * 1024       # total byte yang boleh di-MD5 lewat semua bagian PE
MAX_ZIP_ENTRIES = 100_000            # lebih dari ini: arsip tidak diurai (cegah kehabisan memori)

# ---------------------------------------------------------------------------
# Dasar
# ---------------------------------------------------------------------------


def _entropy(b: bytes) -> float:
    if not b:
        return 0.0
    n = len(b)
    c = collections.Counter(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def _md5(data=b""):
    """MD5 untuk sidik jari (bukan keamanan): tetap jalan di Python mode FIPS."""
    try:
        return hashlib.md5(data, usedforsecurity=False)
    except TypeError:   # Python < 3.9
        return hashlib.md5(data)


def _open_regular(path, follow: bool = True):
    """Buka berkas biasa dan kembalikan (file, ukuran) dari handle yang SAMA (tanpa celah TOCTOU).
    Menolak FIFO / perangkat (mis. /dev/zero: hash tak berujung) / folder. follow=False menolak symlink di POSIX."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    if not follow:
        flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(os.fspath(path), flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("bukan berkas biasa (FIFO / perangkat / folder): %s" % os.fspath(path))
        f = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    return f, st.st_size


def _hash_file(src, size: int | None = None) -> dict:
    """src: path ATAU file object biner. Membaca paling banyak `size` byte supaya hash konsisten dengan ukuran yang dilaporkan."""
    own = not hasattr(src, "read")
    if own:
        f, fsz = _open_regular(src)
        size = fsz if size is None else size
    else:
        f = src
    h256, h1, hmd = hashlib.sha256(), hashlib.sha1(), _md5()
    try:
        left = float("inf") if size is None else size
        while left > 0:
            chunk = f.read(int(min(1024 * 1024, left)))
            if not chunk:
                break
            left -= len(chunk)
            h256.update(chunk)
            h1.update(chunk)
            hmd.update(chunk)
    finally:
        if own:
            f.close()
    return {"sha256": h256.hexdigest(), "sha1": h1.hexdigest(), "md5": hmd.hexdigest()}


def _human(n: int) -> str:
    x = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if x < 1024 or u == "GB":
            return ("%d %s" % (x, u)) if u == "B" else ("%.1f %s" % (x, u))
        x /= 1024
    return "%d B" % n


_MACHINE = {0x14c: "x86", 0x8664: "x64", 0x1c0: "ARM", 0xaa64: "ARM64", 0x1c4: "ARMv7 Thumb", 0x200: "IA-64", 0x0: "tak dikenal"}
_SUBSYS = {1: "Native", 2: "GUI", 3: "Console", 5: "OS/2", 7: "POSIX", 9: "WinCE", 10: "EFI app", 11: "EFI boot driver", 12: "EFI runtime", 14: "Xbox"}
_ELF_MACHINE = {3: "x86", 8: "MIPS", 20: "PowerPC", 40: "ARM", 62: "x86-64", 183: "AArch64", 243: "RISC-V", 94: "Xtensa"}
_ELF_TYPE = {1: "relocatable (.o)", 2: "executable", 3: "shared object / PIE", 4: "core dump"}

# ---------------------------------------------------------------------------
# PE
# ---------------------------------------------------------------------------


_RES_TYPES = {1: "CURSOR", 2: "BITMAP", 3: "ICON", 4: "MENU", 5: "DIALOG", 6: "STRING", 9: "ACCELERATOR", 10: "RCDATA", 11: "MESSAGETABLE",
              12: "GROUP_CURSOR", 14: "GROUP_ICON", 16: "VERSION", 24: "MANIFEST"}
_VER_KEYS = ("CompanyName", "FileDescription", "FileVersion", "InternalName", "OriginalFilename", "ProductName")


def _res_entries(d: bytes, off):
    if off is None or off < 0 or off + 16 > len(d):
        return []
    nn, ni = struct.unpack_from("<HH", d, off + 12)
    out = []
    for i in range(min(nn + ni, 64)):
        o = off + 16 + 8 * i
        if o + 8 > len(d):
            break
        name, tgt = struct.unpack_from("<II", d, o)
        out.append((name, tgt & 0x7FFFFFFF, bool(tgt & 0x80000000)))
    return out


def _parse_resources(d: bytes, base, rva2off) -> tuple[list[dict], dict]:
    """Jelajahi direktori resource PE (tipe -> nama -> bahasa). Hanya membaca; tidak mengekstrak apa pun."""
    leaves: list[dict] = []
    ver: dict = {}

    def nm(n):
        if n & 0x80000000:
            o = base + (n & 0x7FFFFFFF)
            if o + 2 <= len(d):
                ln = struct.unpack_from("<H", d, o)[0]
                return d[o + 2:o + 2 + 2 * min(ln, 64)].decode("utf-16le", "replace")
            return "?"
        return n

    for tn, toff, tdir in _res_entries(d, base):
        if not tdir:
            continue
        tname = nm(tn)
        tlabel = _RES_TYPES.get(tname, str(tname)) if isinstance(tname, int) else "'%s'" % tname
        for nn_, noff, ndir in _res_entries(d, base + toff)[:32]:
            if not ndir:
                continue
            for _ln, loff, ldir in _res_entries(d, base + noff)[:4]:
                if ldir or base + loff + 16 > len(d):
                    continue
                rva, size, _cp, _r = struct.unpack_from("<IIII", d, base + loff)
                fo = rva2off(rva)
                if fo is None or fo >= len(d):
                    continue
                data = d[fo:fo + min(size, 1 << 20)]
                leaf = {"type": tlabel, "name": str(nm(nn_)), "size": size, "ent": _entropy(data[:65536]), "mz": data[:2] == b"MZ", "off": fo}
                fmt, fmt_ok = _res_format(d, fo, size)
                if fmt:
                    leaf["fmt"], leaf["fmt_ok"] = fmt, fmt_ok
                leaves.append(leaf)
                if tname == 16 and not ver:
                    txt = d[fo:fo + min(size, 16384)].decode("utf-16le", "ignore")
                    for k in _VER_KEYS:
                        m = re.search(k + r"\x00+([^\x00]{1,120})", txt)
                        if m:
                            ver[k] = m.group(1).strip()
                    quads = sorted(set(re.findall(r"(?<![\d.])\d{1,5}(?:\.\d{1,5}){3}(?![\d.])", txt)))
                    if quads:
                        leaf["vquads"] = quads[:8]   # nomor versi berbentuk a.b.c.d (bukan IP): dipakai menyaring kandidat IP
                if len(leaves) >= 200:
                    return leaves, ver
    return leaves, ver


def _rich_header(d: bytes, pe_off: int):
    """Header 'Rich' (jejak alat build MSVC) di antara DOS stub dan header PE. Hash varian Iris: MD5 teks terang dari DanS sampai Rich."""
    end = d.find(b"Rich", 0x40, min(pe_off + 4, len(d)))
    if end == -1 or end + 8 > len(d):
        return None
    key = d[end + 4:end + 8]
    k = struct.unpack("<I", key)[0]
    pos = end - 4
    while pos >= 0x40:
        if struct.unpack_from("<I", d, pos)[0] ^ k == 0x536E6144:   # "DanS"
            clear = bytes(b ^ key[i % 4] for i, b in enumerate(d[pos:end]))
            return {"hash": _md5(clear).hexdigest(), "n": max(0, (end - pos - 16) // 8)}
        pos -= 4
    return None


def _res_format(d: bytes, fo: int, size: int) -> tuple[str, bool]:
    """Kenali resource terkompres yang wajar tampak acak (PNG / JPEG / ZIP) dari magic number, lalu cek kerangka dasarnya.
    Mengembalikan (format, utuh). utuh=False bila magic cocok tetapi kerangka tidak masuk akal (mis. data tambahan setelah IEND),
    supaya awalan PNG palsu di depan payload tidak lolos."""
    if size < 12 or fo < 0 or fo + 16 > len(d):
        return "", False
    end = min(fo + size, len(d))
    head = d[fo:fo + 16]
    mv = memoryview(d)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        tail = bytes(mv[max(fo, end - 32):end]).rstrip(b"\x00")
        return "PNG", head[12:16] == b"IHDR" and tail.endswith(b"IEND\xaeB`\x82")
    if head[:3] == b"\xff\xd8\xff":
        tail = bytes(mv[max(fo, end - 64):end]).rstrip(b"\x00")
        return "JPEG", tail.endswith(b"\xff\xd9")
    if head[:4] == b"PK\x03\x04":
        tail = bytes(mv[max(fo, end - 65557):end])
        return "ZIP", b"PK\x05\x06" in tail
    return "", False


def _cert_spans(d: bytes, off: int, size: int) -> tuple[list[tuple[int, int]], int]:
    """Rentang struktur PKCS#7 (DER) di tabel sertifikat Authenticode, plus jumlah byte TAK BERSTRUKTUR setelah struktur itu (di luar
    padding nol). Hanya struktur DER yang dikecualikan dari ekstraksi string / IOC: header dan byte sisa tetap dipindai, karena data
    bisa diselipkan di tabel sertifikat tanpa merusak tanda tangan. Bila struktur tidak terbaca, hasil kosong (tidak ada yang dikecualikan)."""
    spans: list[tuple[int, int]] = []
    extra, pos, end = 0, off, min(off + size, len(d))
    while pos + 16 <= end:
        dw = struct.unpack_from("<I", d, pos)[0]
        if dw < 16 or pos + dw > end:
            return spans, extra
        s0 = pos + 8
        if d[s0] != 0x30:   # PKCS#7 SignedData selalu diawali SEQUENCE
            return spans, extra
        b = d[s0 + 1]
        if b & 0x80:
            n = b & 0x7F
            if n == 0 or n > 4 or s0 + 2 + n > pos + dw:
                return spans, extra
            hdr, ln = 2 + n, int.from_bytes(d[s0 + 2:s0 + 2 + n], "big")
        else:
            hdr, ln = 2, b
        if s0 + hdr + ln > pos + dw:
            return spans, extra
        spans.append((s0, s0 + hdr + ln))
        extra += len(d[s0 + hdr + ln:pos + dw].rstrip(b"\x00"))
        pos += (dw + 7) & ~7
    if spans and pos < end:
        extra += len(d[pos:end].rstrip(b"\x00"))
    return spans, extra


def _signers(d: bytes, off: int, size: int) -> list[str]:
    """Nama umum (CN) yang terbaca dari blob sertifikat Authenticode. Keabsahan tanda tangan TIDAK diperiksa."""
    blob = d[off:off + min(size, 200000)]
    out: list[str] = []
    for m in re.finditer(rb"\x55\x04\x03([\x0c\x13\x14\x1e])", blob):
        p_ = m.end()
        if p_ >= len(blob) or blob[p_] & 0x80:
            continue
        raw = blob[p_ + 1:p_ + 1 + blob[p_]]
        t = raw.decode("utf-16be", "ignore") if m.group(1) == b"\x1e" else raw.decode("utf-8", "replace")
        if t and t not in out:
            out.append(t[:80])
    return out[:6]


def _parse_pe(d: bytes, file_size: int) -> dict | None:
    if len(d) < 0x40 or d[:2] != b"MZ":
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    if pe_off + 24 > len(d) or d[pe_off:pe_off + 4] != b"PE\0\0":
        return {"broken": "header MZ ada tetapi tanda PE tidak ditemukan (DOS stub saja, rusak, atau dikemas)"}
    machine, nsec, ts, _p, _n, optsz, chars = struct.unpack_from("<HHIIIHH", d, pe_off + 4)
    o = pe_off + 24
    if o + 96 > len(d):
        return {"broken": "optional header terpotong"}
    magic = struct.unpack_from("<H", d, o)[0]
    is64 = magic == 0x20B
    if o + (112 if is64 else 96) > len(d):
        return {"broken": "optional header terpotong"}
    entry = struct.unpack_from("<I", d, o + 16)[0]
    subsys, dllch = struct.unpack_from("<HH", d, o + 68)
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    dd_off = o + (112 if is64 else 96)
    pwarn: list[str] = []   # kegagalan parse sebagian; masuk rep["warn"] supaya "tidak ada temuan" tidak tampak seperti "bersih"
    dirs = []
    for i in range(min(nrva, 16)):
        if dd_off + 8 * i + 8 > len(d):
            break
        dirs.append(struct.unpack_from("<II", d, dd_off + 8 * i))

    secs = []
    so = o + optsz
    ent_left, md5_left, budget_hit = ENT_BUDGET, MD5_BUDGET, False
    for i in range(min(nsec, 96)):
        p = so + 40 * i
        if p + 40 > len(d):
            break
        nm, vsz, va, rsz, rptr, _r, _l, _nr, _nl, ch = struct.unpack_from("<8sIIIIIIHHI", d, p)
        name = nm.rstrip(b"\0").decode("latin-1", "replace")
        raw = d[rptr:rptr + min(rsz, SEC_ENT_SAMPLE)] if rptr < len(d) else b""
        if len(raw) > ent_left:       # header bagian tumpang-tindih / dibuat-buat: jangan biarkan CPU habis
            raw, budget_hit = b"", True
        ent_left -= len(raw)
        md5 = ""
        if rptr < len(d) and rsz:
            n_md = min(rsz, 16 * 1024 * 1024, len(d) - rptr)
            if n_md <= md5_left:
                md5_left -= n_md
                md5 = _md5(memoryview(d)[rptr:rptr + n_md]).hexdigest()
            else:
                budget_hit = True
        secs.append({
            "name": name, "va": va, "vsize": vsz, "rptr": rptr, "rsize": rsz,
            "md5": md5,
            "flags": ("R" if ch & 0x40000000 else "-") + ("W" if ch & 0x80000000 else "-") + ("X" if ch & 0x20000000 else "-"),
            "ent": _entropy(raw) if raw else 0.0,
        })

    def rva2off(rva: int) -> int | None:
        for s in secs:
            rel = rva - s["va"]
            if 0 <= rel < max(s["vsize"], s["rsize"]):
                return (rel + s["rptr"]) if rel < s["rsize"] else None   # ekor virtual (nol) tidak ada di berkas
        if secs and rva < min(s["va"] for s in secs):
            return rva
        return None

    def cstr(off: int, lim: int = 128) -> str:
        if off is None or off < 0 or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    def hint_name(rva: int) -> str:
        fo = rva2off(rva)
        return (cstr(fo + 2) if fo is not None else "") or "?"

    imports: dict[str, list[str]] = {}
    try:
        if len(dirs) > 1 and dirs[1][0]:
            off = rva2off(dirs[1][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 20 <= len(d) and n < 60:
                oft, _t, _f, name_rva, ft = struct.unpack_from("<IIIII", d, off)
                if not (oft or name_rva or ft):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns: list[str] = []
                th = rva2off(oft or ft)
                k = 0
                while th is not None and th + step <= len(d) and k < 600:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                imports.setdefault(dll or "?", []).extend(fns)
                off += 20
                n += 1
    except (struct.error, IndexError):
        pwarn.append("tabel import terpotong / rusak: daftar import mungkin tidak lengkap")

    delay_imports: dict[str, list[str]] = {}   # v94: delay-load import (dipakai untuk menyembunyikan API dari tabel impor biasa)
    try:
        if len(dirs) > 13 and dirs[13][0]:
            off = rva2off(dirs[13][0])
            step = 8 if is64 else 4
            n = 0
            while off is not None and off + 32 <= len(d) and n < 40:
                _at, name_rva, _h, _iat, int_rva = struct.unpack_from("<IIIII", d, off)
                if not (name_rva or int_rva):
                    break
                dll = cstr(rva2off(name_rva)).lower()
                fns = []
                th = rva2off(int_rva)
                k = 0
                while th is not None and th + step <= len(d) and k < 400:
                    v = struct.unpack_from("<Q" if is64 else "<I", d, th)[0]
                    if v == 0:
                        break
                    if v & (1 << (63 if is64 else 31)):
                        fns.append("#%d" % (v & 0xFFFF))
                    else:
                        fns.append(hint_name(v & 0x7FFFFFFF))
                    th += step
                    k += 1
                delay_imports.setdefault(dll or "?", []).extend(fns)
                off += 32
                n += 1
    except (struct.error, IndexError):
        pwarn.append("tabel delay-import terpotong / rusak: daftar mungkin tidak lengkap")

    imph, ord_imp = "", 0
    try:
        parts = []
        for dll, fns in imports.items():
            base = dll.rsplit(".", 1)[0] if dll.rsplit(".", 1)[-1] in ("dll", "ocx", "sys") else dll
            for fn in fns:
                if fn.startswith("#"):
                    ord_imp += 1
                    fn = "ord" + fn[1:]
                parts.append("%s.%s" % (base, fn.lower()))
        if parts:
            imph = _md5(",".join(parts).encode()).hexdigest()
    except Exception:
        pass

    exports: list[str] = []
    try:
        if dirs and dirs[0][0]:
            eo = rva2off(dirs[0][0])
            if eo is not None and eo + 40 <= len(d):
                nnames = struct.unpack_from("<I", d, eo + 24)[0]
                names_rva = struct.unpack_from("<I", d, eo + 32)[0]
                no = rva2off(names_rva)
                for i in range(min(nnames, 80)):
                    if no is None or no + 4 * i + 4 > len(d):
                        break
                    nm_ = cstr(rva2off(struct.unpack_from("<I", d, no + 4 * i)[0]))
                    if nm_:
                        exports.append(nm_)
    except (struct.error, IndexError):
        pwarn.append("tabel ekspor terpotong / rusak: daftar ekspor mungkin tidak lengkap")

    res: list[dict] = []
    ver: dict = {}
    try:
        if len(dirs) > 2 and dirs[2][0]:
            res, ver = _parse_resources(d, rva2off(dirs[2][0]), rva2off)
    except (struct.error, IndexError, ValueError, OverflowError):
        pwarn.append("direktori resource rusak / tidak bisa diurai: resource tidak diperiksa (bisa disengaja untuk menghindari analisis)")
    try:   # v98.6: entropi bagian resource dihitung tanpa PNG / JPEG / ZIP utuh (ikon PNG membuat .rsrc tampak 'terenkripsi')
        skip_rs = [(x["off"], x["off"] + x["size"]) for x in res if x.get("fmt") and x.get("fmt_ok")]
        if skip_rs and len(dirs) > 2 and dirs[2][0]:
            rs_ = next((s for s in secs if s["va"] <= dirs[2][0] < s["va"] + max(s["vsize"], s["rsize"])), None)
            if rs_ and rs_["ent"] > 7.0 and rs_["rptr"] < len(d):
                a_, b_ = rs_["rptr"], rs_["rptr"] + min(rs_["rsize"], SEC_ENT_SAMPLE)
                rest_ = _mask_block(d, a_, b_, _merge_spans(skip_rs, len(d)))
                masked_ = (min(b_, len(d)) - a_) - len(rest_)
                if masked_ > 0:
                    rs_["ent_raw"], rs_["masked"] = rs_["ent"], masked_
                    rs_["ent"] = _entropy(rest_) if len(rest_) >= 1024 else 0.0
    except (struct.error, IndexError, ValueError, OverflowError):
        pass
    rich = None
    try:
        rich = _rich_header(d, pe_off)
    except (struct.error, IndexError, ValueError):
        pass
    signers: list[str] = []
    cert_spans: list[tuple[int, int]] = []
    cert_extra = 0
    if len(dirs) > 4 and dirs[4][0] and dirs[4][1]:
        try:
            signers = _signers(d, dirs[4][0], dirs[4][1])
        except Exception:
            pwarn.append("blok tanda tangan Authenticode ada tetapi tidak bisa diurai: penandatangan tidak diketahui")
        try:
            cert_spans, cert_extra = _cert_spans(d, dirs[4][0], dirs[4][1])
        except Exception:
            cert_spans, cert_extra = [], 0
    entry_sec = ""
    for s_ in secs:
        if s_["va"] <= entry < s_["va"] + max(s_["vsize"], s_["rsize"]):
            entry_sec = s_["name"]
            break
    cert = dirs[4] if len(dirs) > 4 else (0, 0)
    last_raw = max([s["rptr"] + s["rsize"] for s in secs] or [0])
    overlay = max(0, file_size - last_raw) if last_raw else 0
    if cert[0] and cert[1] and cert[0] >= last_raw:   # v94: blob Authenticode ada di akhir file; bukan overlay
        overlay = max(0, overlay - cert[1])
        if overlay < 8:
            overlay = 0
    try:
        stamp = _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "0"
    except (OverflowError, OSError, ValueError):
        stamp = "tidak valid"
    return {
        "arch": _MACHINE.get(machine, hex(machine)), "bits": 64 if is64 else 32,
        "dll": bool(chars & 0x2000), "subsys": _SUBSYS.get(subsys, str(subsys)),
        "stamp": stamp, "ts": ts, "entry": entry, "entry_sec": entry_sec, "imphash": imph, "ord_imports": ord_imp,
        "tls": bool(len(dirs) > 9 and dirs[9][0]), "delay": bool(len(dirs) > 13 and dirs[13][0]),
        "res": res, "ver": ver, "rich": rich, "signers": signers, "cert_spans": cert_spans, "cert_extra": cert_extra,
        "aslr": bool(dllch & 0x40), "dep": bool(dllch & 0x100), "cfg": bool(dllch & 0x4000),
        "dotnet": len(dirs) > 14 and dirs[14][0] != 0 and dirs[14][1] != 0,
        "signed": cert[0] != 0 and cert[1] != 0, "overlay": overlay, "last_raw": last_raw, "delay_imports": delay_imports,
        "sections": secs, "imports": imports, "exports": exports, "budget_hit": budget_hit, "pwarn": pwarn,
    }


# ---------------------------------------------------------------------------
# ELF, ZIP / APK / JAR
# ---------------------------------------------------------------------------


def _parse_elf(d: bytes) -> dict | None:
    if len(d) < 52 or d[:4] != b"\x7fELF":
        return None
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    etype, mach = struct.unpack_from(en + "HH", d, 16)
    out: dict = {"bits": 64 if is64 else 32, "endian": "little" if en == "<" else "big",
                 "type": _ELF_TYPE.get(etype, str(etype)), "arch": _ELF_MACHINE.get(mach, str(mach)),
                 "sections": [], "stripped": None, "interp": "", "wx": [], "exec_stack": False, "nsec": 0, "nseg": 0, "budget_hit": False}
    try:
        if is64:
            phoff, shoff = struct.unpack_from(en + "QQ", d, 32)
            phentsz, phnum, shentsz, shnum, shstrndx = struct.unpack_from(en + "HHHHH", d, 54)
        else:
            phoff, shoff = struct.unpack_from(en + "II", d, 28)
            phentsz, phnum, shentsz, shnum, shstrndx = struct.unpack_from(en + "HHHHH", d, 42)
        out["nseg"], out["nsec"] = phnum, shnum
        for i in range(min(phnum, 64)):
            o = phoff + i * phentsz
            if o + (56 if is64 else 32) > len(d):
                break
            if is64:
                pt, pf, poff, _va, _pa, fsz, _msz, _al = struct.unpack_from(en + "IIQQQQQQ", d, o)
            else:
                pt, poff, _va, _pa, fsz, _msz, pf, _al = struct.unpack_from(en + "IIIIIIII", d, o)
            if pt == 3 and poff < len(d):
                out["interp"] = d[poff:poff + min(fsz, 128)].split(b"\0")[0].decode("latin-1", "replace")
            if pt == 0x6474E551 and pf & 1:
                out["exec_stack"] = True
            if pt == 1 and pf & 2 and pf & 1:
                out["wx"].append("segmen LOAD#%d" % i)
        if shoff and shnum and shentsz >= (64 if is64 else 40):
            hdrs = []
            for i in range(min(shnum, 96)):
                o = shoff + i * shentsz
                if o + (64 if is64 else 40) > len(d):
                    break
                v = struct.unpack_from(en + ("IIQQQQIIQQ" if is64 else "IIIIIIIIII"), d, o)
                hdrs.append((v[0], v[1], v[2], v[4], v[5]))   # nama, tipe, flag, offset, ukuran
            strtab = b""
            if shstrndx < len(hdrs):
                so_, ssz = hdrs[shstrndx][3], hdrs[shstrndx][4]
                strtab = d[so_:so_ + min(ssz, 65536)]
            ent_left = ENT_BUDGET
            for nm, st, fl, off, sz in hdrs:
                e = strtab.find(b"\0", nm)
                name = strtab[nm:(len(strtab) if e == -1 else e)].decode("latin-1", "replace") if nm < len(strtab) else ""
                raw = d[off:off + min(sz, SEC_ENT_SAMPLE)] if st != 8 and off < len(d) else b""
                if len(raw) > ent_left:
                    raw, out["budget_hit"] = b"", True
                ent_left -= len(raw)
                out["sections"].append({"name": name, "size": sz, "ent": _entropy(raw) if raw else 0.0,
                                        "flags": ("W" if fl & 1 else "-") + ("A" if fl & 2 else "-") + ("X" if fl & 4 else "-")})
            out["stripped"] = ".symtab" not in {x["name"] for x in out["sections"]}
            for x in out["sections"]:
                if x["flags"][0] == "W" and x["flags"][2] == "X":
                    out["wx"].append(x["name"] or "?")
    except (struct.error, IndexError, ValueError):
        pass
    return out


_PERM_RE = re.compile(rb"android\.permission\.[A-Z_]+")
_PERM_RE16 = re.compile(rb"(?:a\x00n\x00d\x00r\x00o\x00i\x00d\x00\.\x00p\x00e\x00r\x00m\x00i\x00s\x00s\x00i\x00o\x00n\x00\.\x00)(?:[A-Z_]\x00)+")


_SCAN_EXT = (".dex", ".class", ".js", ".ps1", ".vbs", ".bat", ".cmd", ".sh", ".py", ".xml", ".json", ".txt", ".cfg", ".ini",
             ".html", ".htm", ".hta", ".bin", ".so", ".properties")
_PRIO_EXT = (".dex", ".class", "vbaproject.bin", ".js", ".ps1", ".vbs", ".bat", ".sh", ".hta")
_REL_TARGET = re.compile(rb'Target="((?:https?|file|ftp)://[^"]{4,300})"[^>]*TargetMode="External"|TargetMode="External"[^>]*Target="((?:https?|file|ftp)://[^"]{4,300})"', re.I)


def _zip_entry_count(f, size: int) -> int:
    """Perkiraan jumlah entri dari EOCD / ZIP64 TANPA memuat direktori pusat (ZIP berjuta entri bisa menghabiskan RAM). -1 bila tak terbaca."""
    try:
        tail = min(size, 65535 + 22 + 20)
        f.seek(size - tail)
        buf = f.read(tail)
        i = buf.rfind(b"PK\x05\x06")
        if i < 0 or i + 22 > len(buf):
            return -1
        total = struct.unpack_from("<H", buf, i + 10)[0]
        cd_size = struct.unpack_from("<I", buf, i + 12)[0]
        if (total == 0xFFFF or cd_size == 0xFFFFFFFF) and i >= 20 and buf[i - 20:i - 16] == b"PK\x06\x07":
            z64 = struct.unpack_from("<Q", buf, i - 12)[0]
            if z64 + 56 <= size:
                f.seek(z64)
                rec = f.read(56)
                if len(rec) == 56 and rec[:4] == b"PK\x06\x06":
                    total = struct.unpack_from("<Q", rec, 32)[0]
                    cd_size = struct.unpack_from("<Q", rec, 40)[0]
        return max(total, 0 if cd_size == 0xFFFFFFFF else cd_size // 46)   # 46 = ukuran minimum satu entri direktori pusat
    except (OSError, struct.error):
        return -1


def _zread(z, member, limit: int) -> bytes:
    """Baca paling banyak `limit` byte HASIL dekompresi. z.read() tanpa batas rentan zip bomb (1 MB terkompres bisa jadi GB)."""
    with z.open(member) as m:
        return m.read(max(0, limit))


def _parse_zip(src, size: int | None = None) -> dict | None:
    """src: path ATAU file object biner (yang sama dengan yang dibaca triase, supaya tidak dibuka ulang lewat nama)."""
    if not hasattr(src, "read"):
        f_, sz_ = _open_regular(src)
        with f_:
            return _parse_zip(f_, sz_)
    if size is None:
        src.seek(0, 2)
        size = src.tell()
    if not zipfile.is_zipfile(src):
        return None
    out: dict = {"names": [], "n": 0, "unc": 0, "kind": "ZIP", "warn": [], "perms": [], "dex": 0, "nested": [], "ext_rels": [], "_blob": b""}
    cnt = _zip_entry_count(src, size)
    if cnt > MAX_ZIP_ENTRIES:
        out["n"] = cnt
        out["warn"].append("jumlah entri arsip tidak wajar (~%d): tidak diurai (cegah kehabisan memori)" % cnt)
        return out
    with zipfile.ZipFile(src) as z:
        infos = z.infolist()
        out["n"] = len(infos)
        names = [i.filename for i in infos]
        out["names"] = names[:50]
        out["unc"] = sum(i.file_size for i in infos)
        comp = sum(i.compress_size for i in infos) or 1
        out["ratio"] = out["unc"] / comp
        if any(i.flag_bits & 1 for i in infos):
            out["warn"].append("ada entri terenkripsi (kata sandi)")
        if any(n.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", n) or ".." in n.replace("\\", "/").split("/") for n in names):
            out["warn"].append("nama entri berpola path traversal (zip-slip)")
        if out["ratio"] > 200:
            out["warn"].append("rasio kompresi %.0fx (kemungkinan zip bomb)" % out["ratio"])
        low = [n.lower() for n in names]
        if "androidmanifest.xml" in low:
            out["kind"] = "APK (Android)"
            out["dex"] = sum(1 for n in low if re.fullmatch(r"classes\d*\.dex", n))
            try:
                mf = _zread(z, names[low.index("androidmanifest.xml")], 400000)
                perms = {m.decode() for m in _PERM_RE.findall(mf)}
                perms |= {m.decode("utf-16le", "ignore") for m in _PERM_RE16.findall(mf)}
                out["perms"] = sorted(perms)[:60]
            except Exception:
                pass
            _apk_deep(z, names, low, out)
        elif "meta-inf/manifest.mf" in low:
            out["kind"] = "JAR/WAR (Java)"
            try:
                mf = _zread(z, names[low.index("meta-inf/manifest.mf")], 4096).decode("utf-8", "replace")
                m = re.search(r"Main-Class:\s*(\S+)", mf)
                out["main"] = m.group(1) if m else ""
            except Exception:
                pass
        elif any(n.endswith(".class") for n in low):
            out["kind"] = "JAR (Java, tanpa manifest)"
        elif "[content_types].xml" in low:
            out["kind"] = "Paket OOXML (docx/xlsx/pptx)" + (" DENGAN makro VBA" if any("vbaproject.bin" in n for n in low) else "")
        out["nested"] = [n for n in names if n.lower().endswith((".exe", ".dll", ".jar", ".apk", ".so", ".dex", ".bat", ".ps1", ".vbs", ".js", ".scr", ".sh", ".hta", ".lnk"))][:25]
        out["nested"] += [n for n in names if "/embeddings/" in n.lower() and n not in out["nested"]][:10]

        # relasi eksternal OOXML (template injection / konten jarak jauh)
        for i in infos:
            if i.filename.lower().endswith(".rels") and i.file_size < 400000 and not i.flag_bits & 1:
                try:
                    for m in _REL_TARGET.findall(_zread(z, i, 200000)):
                        t = (m[0] or m[1]).decode("latin-1", "replace")
                        if t not in out["ext_rels"]:
                            out["ext_rels"].append(t)
                except Exception:
                    pass
        out["ext_rels"] = out["ext_rels"][:10]
        if out["ext_rels"]:
            out["warn"].append("relasi eksternal di dalam dokumen (%d): bisa konten jarak jauh / template injection" % len(out["ext_rels"]))

        # isi anggota yang layak dipindai (dex, class, skrip, makro) ikut jadi bahan string / indikator
        budget = 24 * 1024 * 1024
        chunks = []
        pri = sorted(infos, key=lambda i: (0 if i.filename.lower().endswith(_PRIO_EXT) else 1, i.file_size))
        for i in pri:
            fn = i.filename.lower()
            if i.is_dir() or i.flag_bits & 1 or budget <= 0:
                continue
            if not (fn.endswith(_SCAN_EXT) or "vbaproject.bin" in fn) or i.file_size > 12 * 1024 * 1024:
                continue
            try:
                data = _zread(z, i, min(12 * 1024 * 1024, budget))
            except Exception:
                continue
            budget -= len(data)
            chunks.append(data)
        out["_blob"] = b"\n".join(chunks)
    return out


# ---------------------------------------------------------------------------
# String dan indikator
# ---------------------------------------------------------------------------

_ASCII = re.compile(rb"[\x20-\x7e]{6,}")
_UTF16 = re.compile(rb"(?:[\x20-\x7e]\x00){6,}")
_URL = re.compile(r"(?:https?|ftp|wss?)://[^\s\"'<>\\^`{}|]{4,200}", re.I)
_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_MAIL = re.compile(r"[A-Za-z0-9._%+-]{2,64}@[A-Za-z0-9-]{2,63}\.[A-Za-z.]{2,24}")
_REG = re.compile(r"(?:HKEY_[A-Z_]+|HKLM|HKCU)\\[^\x00\r\n\"]{3,120}|Software\\Microsoft\\Windows\\CurrentVersion\\[A-Za-z\\]{2,60}", re.I)
_WPATH = re.compile(r"\b[A-Za-z]:\\(?:[^\x00-\x1f\"<>|*?\\]{1,60}\\){0,6}[^\x00-\x1f\"<>|*?\\]{1,60}")
_SECRET = re.compile(r"(?i)(?:api[_-]?key|secret|passw(?:or)?d|token|bearer|private[_ ]key|authorization)\s*[:=]\s*['\"]?([A-Za-z0-9_\-+/=.]{8,})")
_PEM = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")
_B64 = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{60,}={0,2}(?![A-Za-z0-9+/=])")

# kemampuan -> nama API / kata kunci (cocokkan dengan nama import atau string). Kehadiran = petunjuk, BUKAN vonis.
CAPS = {
    "injeksi / manipulasi proses": ["VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "QueueUserAPC", "SetThreadContext", "NtWriteVirtualMemory", "RtlCreateUserThread"],
    "anti-debug / anti-analisis": ["IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess", "OutputDebugString", "NtSetInformationThread", "GetTickCount64"],
    "jaringan": ["InternetOpen", "InternetConnect", "HttpSendRequest", "URLDownloadToFile", "WinHttpOpen", "WSAStartup", "WSASocket", "getaddrinfo", "gethostbyname", "InternetReadFile", "HttpClient", "WebClient", "TcpClient"],
    "persistensi": ["RegSetValueEx", "RegCreateKeyEx", "CreateService", "OpenSCManager", "schtasks", "CurrentVersion\\Run"],
    "kripto": ["CryptEncrypt", "CryptDecrypt", "CryptAcquireContext", "BCryptEncrypt", "BCryptDecrypt", "CryptGenKey", "AES", "RijndaelManaged"],
    "penyadap input / layar": ["SetWindowsHookEx", "GetAsyncKeyState", "GetKeyboardState", "GetClipboardData", "BitBlt", "GetDC"],
    "eksekusi proses / shell": ["CreateProcess", "ShellExecute", "WinExec", "system(", "cmd.exe", "powershell", "Process.Start"],
    "hak akses": ["AdjustTokenPrivileges", "OpenProcessToken", "LookupPrivilegeValue", "SeDebugPrivilege", "ImpersonateLoggedOnUser"],
    "muat kode dinamis": ["LoadLibrary", "GetProcAddress", "LdrLoadDll", "Assembly.Load", "Reflection", "VirtualProtect", "VirtualAlloc"],
    "berkas / penghapusan": ["DeleteFile", "MoveFileEx", "SHFileOperation", "RemoveDirectory", "CreateFile"],
}
# kemampuan yang hanya dicocokkan dari string (huruf kecil, cocok sebagian). Tetap PETUNJUK, bukan vonis.
STR_CAPS = {
    "LOLBin / unduh-eksekusi": ["mshta", "regsvr32", "rundll32", "certutil", "bitsadmin", "wscript", "cscript", "msbuild", "installutil", "forfiles"],
    "pencurian kredensial / dompet": ["lsass.exe", "sekurlsa", "mimikatz", "login data", "logins.json", "wallet.dat", "cookies.sqlite", "key4.db", "electrum", "metamask"],
    "penghapus jejak / perusak pemulihan": ["vssadmin", "delete shadows", "wevtutil", "bcdedit", "wbadmin", "cipher /w"],
    "deteksi VM / sandbox": ["vboxguest", "vboxservice", "vmtoolsd", "sbiedll", "sandboxie", "wine_get_unix_file_name", "\\\\.\\pipe\\cuckoo"],
    "PowerShell berbahaya / obfuskasi": ["frombase64string", "-encodedcommand", "invoke-expression", "downloadstring", "downloadfile", "iex(", "-windowstyle hidden", "executionpolicy bypass", "-noprofile"],
    "bypass keamanan": ["amsiscanbuffer", "amsi.dll", "etweventwrite", "disableantispyware", "set-mppreference"],
    "penambang kripto": ["stratum+tcp", "xmrig", "cryptonight", "randomx"],
    "string ala ransomware": ["your files have been encrypted", "decrypt your files", ".onion", "ransom"],
}

# (label, penanda huruf kecil di bytes mentah, saran langkah lanjut). Saran = petunjuk alur kerja, bukan temuan.
_TOOLCHAIN = [
    ("PyInstaller", [b"pyinstaller", b"_meipass", b"pyi-runtime", b"pyiboot", b"pyi-windows-manifest-filename", b"pyi_rth_"], "ekstrak arsip PyInstaller (pyinstxtractor), lalu dekompilasi .pyc"),
    ("Nuitka", [b"nuitka", b"__nuitka_"], "Python dikompilasi ke C: andalkan string, modul, dan analisis native"),
    ("Go", [b"go build id", b"go.buildid", b"runtime.gopanic", b"\xff go buildinf:"], "biner Go: pulihkan nama fungsi dari pclntab (GoReSym / Ghidra)"),
    ("Rust", [b"/rustc/", b"rust_panic", b"core::panicking", b".cargo/registry", b".cargo\\registry"], "biner Rust: nama fungsi ter-mangle, cari path crate di string"),
    ("AutoIt", [b"autoit v3", b"au3!ea06", b"this is a compiled autoit"], "skrip AutoIt terkompilasi: ekstrak dengan alat dekompilasi AutoIt"),
    ("NSIS installer", [b"nullsoft install system", b"nsis error"], "installer NSIS: ekstrak dengan 7-Zip, baca skrip .nsi"),
    ("Inno Setup", [b"inno setup setup data"], "installer Inno Setup: ekstrak dengan innoextract"),
    ("UPX", [b"upx!"], "kemasan UPX: unpack dengan `upx -d` (file tidak perlu dijalankan)"),
    ("Electron / asar", [b"electron.asar", b"app.asar", b"electron/js2c"], "aplikasi Electron: ekstrak app.asar, baca JavaScript"),
    ("Obfuscator .NET", [b"confuserex", b"eazfuscator", b"smartassembly", b".net reactor", b"dotfuscator", b"babelobfuscator", b"agile.net", b"cryptoobfuscator", b"dnguard", b"ilprotector"], "kode .NET diobfuskasi: deobfuskasi dulu (de4dot) sebelum dekompilasi"),
    ("Delphi / Borland", [b"borland", b"embarcadero"], "biner Delphi: pakai IDR / Ghidra dengan signature Delphi"),
    ("Visual Basic 6", [b"msvbvm60"], "VB6: analisis P-Code atau native dengan decompiler VB"),
    ("PyArmor", [b"pyarmor", b"pytransform", b"__pyarmor__"], "Python dilindungi PyArmor: bytecode terenkripsi; cari runtime pytransform / pyarmor_runtime dan analisis di sana"),
    ("cx_Freeze", [b"cx_freeze"], "bundel cx_Freeze: modul Python ada di library.zip di samping exe"),
    ("py2exe", [b"py2exe"], "bundel py2exe: arsip Python di resource / library.zip, lalu dekompilasi .pyc"),
    ("PyOxidizer", [b"pyoxidizer"], "bundel PyOxidizer: modul Python tertanam di biner"),
    ("Themida / WinLicense", [b"themida", b"winlicense", b"oreans technologies"], "pelindung Themida / WinLicense (VM + anti-debug): unpack statis sulit; andalkan analisis dinamis di lingkungan terisolasi"),
    ("VMProtect", [b"vmprotect"], "kode diproteksi VMProtect (virtualisasi): fungsi dilindungi menjadi bytecode VM"),
    ("Enigma Protector", [b"the enigma protector"], "pelindung Enigma: cek bagian .enigma1 / .enigma2"),
    ("WiX Burn bootstrapper", [b".wixburn"], "bootstrapper WiX: ekstrak dengan `dark.exe -x` atau 7-Zip"),
    ("Bun (compile)", [b"$bunfs", b"~bun"], "JavaScript dikompilasi Bun: sumber tertanam di bagian akhir berkas"),
    ("Node pkg / nexe", [b"pkg/prelude/bootstrap.js", b"nexe~~sentinel"], "aplikasi Node terbungkus (pkg / nexe): ekstrak JavaScript dari payload di akhir berkas"),
]

_ANDROID_RISK = {
    "SEND_SMS": "kirim SMS", "READ_SMS": "baca SMS", "RECEIVE_SMS": "tangkap SMS",
    "BIND_ACCESSIBILITY_SERVICE": "layanan aksesibilitas (sering disalahgunakan)", "REQUEST_INSTALL_PACKAGES": "memasang APK lain",
    "SYSTEM_ALERT_WINDOW": "tampil di atas aplikasi lain", "BIND_DEVICE_ADMIN": "admin perangkat",
    "READ_CALL_LOG": "baca log panggilan", "RECORD_AUDIO": "rekam audio", "READ_CONTACTS": "baca kontak",
    "MANAGE_EXTERNAL_STORAGE": "akses semua berkas", "RECEIVE_BOOT_COMPLETED": "jalan otomatis saat boot",
    "READ_PHONE_NUMBERS": "baca nomor telepon", "CALL_PHONE": "melakukan panggilan",
}

_PDB = re.compile(r"[A-Za-z]:\\[^\x00\r\n\"<>|*?]{3,200}\.pdb", re.I)
_PACKERS = ("upx0", "upx1", ".upx", ".themida", ".vmp0", ".vmp1", ".aspack", ".adata", ".petite", ".nsp0", ".mpress1", "mpress", ".enigma1", ".winlice", ".boom", ".vmp2", "pec1", "pec2", ".packed", "upx2", ".yp", ".perplex", ".rmnet", ".kkrunchy", ".vmp3", "pecompact2", ".enigma2", ".mpress2", ".nsp2", ".pebundle", ".svkp", ".neolit", ".shrink1", ".shrink2", ".aspack2")


def _strings(d: bytes) -> list[str]:
    out = [m.decode("ascii", "ignore") for m in _ASCII.findall(d)]
    out += [m.decode("utf-16le", "ignore") for m in _UTF16.findall(d)]
    return out


def _uniq(seq, limit):
    seen, res = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            res.append(x)
            if len(res) >= limit:
                break
    return res


def _mask(s: str) -> str:
    return s[:4] + "…(%d krt)" % len(s) if len(s) > 6 else "…"


# v99.3 [C3]: pemindai rahasia berformat khusus. Hanya pola dengan awalan / bentuk yang khas (bukan tebakan entropi), jadi
# alarm palsu rendah. Nilai TIDAK pernah ditulis utuh ke laporan: selalu disamarkan lewat _mask (URI database: sandi diganti ***).
_SECRET_PATS = (
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|ANPA|ANVA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{50,255})\b")),
    ("Telegram bot token", re.compile(r"(?<![\w:])\d{8,10}:AA[A-Za-z0-9_\-]{33}(?![\w\-])")),
    ("Discord webhook", re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d{17,20}/[A-Za-z0-9_\-]{60,}")),
    ("Slack webhook", re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{20,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Stripe secret key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{24,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
)
_DB_URI = re.compile(r"\b(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|amqps?|mssql|sqlserver)://([^\s:@/\"'<>]{1,64}):([^\s@/\"'<>]{1,128})@([^\s/\"'<>?]{1,100})", re.I)


# v99.3+ [C1]: artefak jaringan statis (hanya teks yang tertanam; tidak ada koneksi apa pun dibuat)
_UA_HDR = re.compile(r"(?i)User-Agent:[ \t]*([^\r\n\x00]{4,200})")
_UA_STR = re.compile(r"\b(?:Mozilla/\d\.\d \([^)\r\n]{4,160}\)[^\r\n\x00]{0,100}|[A-Za-z][A-Za-z0-9_.\-]{2,30}/\d{1,3}(?:\.\d{1,4}){1,3} \((?:compatible|Windows|Linux|Macintosh|X11)[^)\r\n]{0,120}\))")
_HTTP_REQ = re.compile(r"\b(GET|POST|PUT|HEAD|DELETE|OPTIONS|PATCH|CONNECT) ((?:/|https?://)[^\s\"'<>]{0,200}) HTTP/1\.[01]")
_HTTP_HOST = re.compile(r"(?i)\bHost:[ \t]*([A-Za-z0-9.\-]{3,100}(?::\d{2,5})?)")
_HTTP_HDR = re.compile(r"(?im)^(Cookie|Authorization|Proxy-Authorization|X-Forwarded-For|Content-Type|Referer):[ \t]*([^\r\n\x00]{0,60})")
_DNS_ENC = re.compile(r"(?<![a-z0-9\-])((?:[a-z2-7]{32,63}|[0-9a-f]{32,63})\.(?:[a-z0-9\-]{2,40}\.)+[a-z]{2,10})(?![a-z0-9\-])", re.I)
_CERT_PEM = re.compile(r"-----BEGIN (?:TRUSTED |X509 )?CERTIFICATE-----")
_PROXY = re.compile(r"(?i)\b(?:socks[45][ah]?|https?)://(?:[^\s:@/\"'<>]{1,40}:[^\s@/\"'<>]{1,40}@)?[A-Za-z0-9.\-]{3,100}:(?:1080|3128|8080|8888|9050|8118|\d{4,5})\b")
_PROXY_KEY = re.compile(r"(?i)\b(ProxyServer|ProxyEnable|ProxyOverride|AutoConfigURL|http_proxy|https_proxy|all_proxy|socks_proxy|Proxy-Authorization|WINHTTP_OPTION_PROXY)\b")
_PIPE = re.compile(r"\\\\(?:\.|[A-Za-z0-9_\-]{1,30})\\pipe\\([^\s\x00\"'<>|*?\\]{1,80})")
_PIPE_C2 = (
    (re.compile(r"(?i)^msagent_[0-9a-f]{2}$"), "pola default Cobalt Strike (SMB beacon)"),
    (re.compile(r"(?i)^MSSE-\d{2,5}-server$"), "pola default Cobalt Strike"),
    (re.compile(r"(?i)^postex_[0-9a-f]{4}$"), "pola Cobalt Strike (post-ex)"),
    (re.compile(r"(?i)^status_[0-9a-f]{2,4}$"), "pola Cobalt Strike"),
    (re.compile(r"(?i)^(?:win)?(?:mojo|crashpad_)\.\d+\.\d+"), "mirip pipe Chromium (dipakai juga sebagai kamuflase)"),
    (re.compile(r"(?i)^(?:PSEXESVC|paexec|remcom|csexec)"), "alat eksekusi jarak jauh (PsExec dan sejenis)"),
    (re.compile(r"(?i)^(?:svcctl|atsvc|samr|lsarpc|srvsvc|netlogon)$"), "pipe RPC Windows (lazim; relevan bila dipakai langsung)"),
)


def _net_artifacts(blob: str) -> dict:
    """Artefak jaringan statis dari string: User-Agent, permintaan / header HTTP mentah, DNS ter-encode, sertifikat PEM, proxy, named pipe."""
    ua = _uniq([m.strip() for m in _UA_HDR.findall(blob)] + [m.strip() for m in _UA_STR.findall(blob)], 8)
    http = _uniq(("%s %s" % (m, u[:120]) for m, u in _HTTP_REQ.findall(blob)), 8)
    hosts = _uniq((h.rstrip(".") for h in _HTTP_HOST.findall(blob)), 8)
    hdrs = _uniq(("%s: %s" % (k.title(), "***" if k.lower() in ("cookie", "authorization", "proxy-authorization") else v.strip()) for k, v in _HTTP_HDR.findall(blob)), 6)
    dns = []
    if "." in blob:
        for m in _DNS_ENC.finditer(blob[:4 * 1024 * 1024]):
            lab = m.group(1)
            if len(set(lab.split(".")[0].lower())) >= 8:   # label berentropi rendah (aaaa...) bukan data ter-encode
                dns.append(lab[:90])
            if len(dns) >= 8:
                break
    px = []
    for m in _PROXY.finditer(blob):
        v = re.sub(r"//[^/@\s]+:[^/@\s]+@", "//***:***@", m.group(0))[:120]
        if v.lower().startswith("socks") or re.search(r":(?:1080|3128|8080|8888|9050|8118)$", v):
            px.append(v)
    proxy = _uniq(px + [k.group(1) for k in _PROXY_KEY.finditer(blob)], 8)
    pipes, flagged = [], []
    for nm in _PIPE.findall(blob):
        pipes.append(nm)
        for rx, why in _PIPE_C2:
            if rx.match(nm):
                flagged.append("%s (%s)" % (nm, why))
                break
    return {"ua": ua, "http": http, "hosts": hosts, "hdrs": hdrs, "dns": _uniq(dns, 8), "certs": len(_CERT_PEM.findall(blob)),
            "proxy": proxy, "pipes": _uniq(pipes, 10), "pipes_flag": _uniq(flagged, 6)}


def _scan_secrets(blob: str, limit: int = 12) -> list[str]:
    """Daftar 'jenis: nilai-tersamar'. Contoh dokumentasi (EXAMPLE) dan placeholder sandi dibuang."""
    out: list[str] = []
    for name, rx in _SECRET_PATS:
        for m in rx.finditer(blob):
            v = m.group(0)
            if "EXAMPLE" in v.upper():
                continue
            out.append("%s: %s" % (name, _mask(v)))
            if len(out) >= limit * 3:
                break
    for m in _DB_URI.finditer(blob):
        scheme, user, pw, host = m.groups()
        if pw.strip("*xX$<>{}%") == "" or pw.lower() in ("password", "pass", "changeme", "example", "secret"):
            continue   # placeholder
        out.append("URI database: %s://%s:***@%s (sandi %d krt)" % (scheme.lower(), _mask(user) if len(user) > 6 else user, host, len(pw)))
    return _uniq(out, limit)


def _risky_perms(perms: list[str]) -> list[str]:
    out = []
    for pm in perms:
        k = pm.replace("android.permission.", "")
        if k in _ANDROID_RISK:
            out.append("%s (%s)" % (k, _ANDROID_RISK[k]))
    return out


def _decode_b64(blob: str) -> list[list[str]]:
    """Dekode string base64 panjang dan beri tahu isinya (PE tertanam, teks, arsip). Hanya hasil nyata yang dilaporkan."""
    out: list[list[str]] = []
    for mm in itertools.islice(_B64.finditer(blob), 60):
        m = mm.group(0)
        est = len(m) * 3 // 4                      # ukuran hasil dekode (perkiraan); hanya awalnya yang didekode
        seg = m[:8192]
        if len(m) > 8192:
            seg = seg[:len(seg) - len(seg) % 4]
        try:
            raw = base64.b64decode(seg + "=" * (-len(seg) % 4))
        except Exception:
            continue
        if len(raw) < 24:
            continue
        if raw[:2] == b"MZ":
            out.append(["PE/MZ", "executable tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:4] == b"\x7fELF":
            out.append(["ELF", "executable ELF tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:2] == b"PK":
            out.append(["ZIP", "arsip zip tertanam dalam base64 (%s)" % _human(est)])
        elif raw[:2] == b"\x1f\x8b":
            out.append(["GZIP", "data gzip tertanam dalam base64 (%s)" % _human(est)])
        else:
            txt = ""
            if raw[1::2].count(0) > 0.9 * (len(raw) // 2):
                txt = raw.decode("utf-16le", "ignore")
            else:
                try:
                    txt = raw.decode("utf-8")
                except UnicodeDecodeError:
                    txt = ""
            seg = txt[:400]
            if seg and sum(1 for c in seg if c.isprintable() or c in "\r\n\t") / len(seg) > 0.93 and sum(c.isalpha() for c in seg) > 10:
                out.append(["teks", seg[:100].replace("\n", " ").replace("\r", " ")])
        if len(out) >= 8:
            break
    return out


def _embedded(d: bytes, main_is_pe: bool) -> dict:
    """PE tertanam (polos atau di-XOR satu byte) di dalam file. Hanya lokasi, tidak mengekstrak."""
    res: dict = {"plain": [], "xor": []}
    try:
        pos, n = 0, 0
        while n < 300:
            pos = d.find(b"PE\0\0", pos + 1)
            if pos == -1:
                break
            n += 1
            mz = d.rfind(b"MZ", max(0, pos - 1024), pos)
            if mz > 0 and mz + 0x40 <= len(d) and struct.unpack_from("<I", d, mz + 0x3C)[0] == pos - mz:
                res["plain"].append(mz)
        res["plain"] = res["plain"][:8]
        stub = b"This program cannot be run"
        head = d[: 4 * 1024 * 1024]
        for k in range(1, 256):
            needle = bytes(b ^ k for b in stub)
            at = head.find(needle)
            if at != -1:
                res["xor"].append((k, at))
                if len(res["xor"]) >= 3:
                    break
    except (struct.error, ValueError):
        pass
    return res


def _merge_spans(spans, limit: int) -> list[tuple[int, int]]:
    """Gabungkan rentang (awal, akhir) yang tumpang-tindih, dipotong ke [0, limit)."""
    cl = sorted((max(0, a), min(b, limit)) for a, b in (spans or []))
    out: list[list[int]] = []
    for a, b in cl:
        if a >= b:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _mask_block(d: bytes, a: int, b: int, spans: list[tuple[int, int]]) -> bytes:
    """Isi d[a:b] tanpa byte yang masuk rentang 'spans' (sudah terurut dan digabung)."""
    pos, parts = a, []
    for s0, e0 in spans:
        if e0 <= a:
            continue
        if s0 >= b:
            break
        if s0 > pos:
            parts.append(d[pos:s0])
        pos = max(pos, e0)
        if pos >= b:
            break
    if pos < b:
        parts.append(d[pos:b])
    return b"".join(parts)


def _entropy_regions(d: bytes, skip=None) -> list[tuple[int, int]]:
    """Rentang berentropi tinggi (>7,2) dalam blok; membantu menemukan payload terenkripsi / data kemasan.
    skip: rentang (awal, akhir) yang memang tampak acak karena terkompres (resource PNG / JPEG / ZIP utuh, blok PKCS#7 tanda tangan);
    byte di dalamnya tidak ikut dihitung."""
    d = d[: 16 * 1024 * 1024]
    if len(d) < 32768:
        return []
    spans = _merge_spans(skip, len(d))
    bs = max(65536, len(d) // 64)
    regs: list[list[int]] = []
    for off in range(0, len(d), bs):
        blen = min(bs, len(d) - off)
        blk = _mask_block(d, off, off + blen, spans) if spans else d[off:off + blen]
        if len(blk) >= 4096 and _entropy(blk) > 7.2:
            end = off + blen
            if regs and regs[-1][1] == off:
                regs[-1][1] = end
            else:
                regs.append([off, end])
    return [(a, b) for a, b in regs if b - a >= 32768][:10]


def _toolchain(d: bytes, pe: dict | None) -> list[tuple[str, str]]:
    dl = d[: 16 * 1024 * 1024].lower()
    out = []
    for label, marks, hint in _TOOLCHAIN:
        if any(m in dl for m in marks):
            out.append((label, hint))
    if pe and not pe.get("broken") and pe.get("dotnet") and not any(x[0] == "Obfuscator .NET" for x in out):
        out.append((".NET (managed)", "dekompilasi langsung dengan ILSpy / dnSpy (kode terkelola, hasil biasanya mudah dibaca)"))
    return out


def _score(rep: dict) -> tuple[int, str, list[str]]:
    """Skor heuristik dari fakta terukur. BUKAN vonis: tiap alasan menyebut buktinya, dan file sah juga bisa terkena."""
    pts, why = 0, []

    def add(n: int, t: str) -> None:
        nonlocal pts
        pts += n
        why.append("%s (+%d)" % (t, n))

    ind = rep["ind"]
    caps = {c: v for c, v in ((c, _cap_strong(ind, c)) for c in ind["caps"]) if v}   # hanya yang berbukti kuat ikut skor
    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    for cap, n, txt in (("injeksi / manipulasi proses", 3, "API injeksi proses"), ("pencurian kredensial / dompet", 3, "string pencurian kredensial / dompet"),
                        ("penambang kripto", 3, "string penambang kripto"), ("penghapus jejak / perusak pemulihan", 3, "perintah penghapus salinan bayangan / log"),
                        ("bypass keamanan", 2, "string bypass AMSI / antivirus"), ("PowerShell berbahaya / obfuskasi", 2, "pola PowerShell terenkode / unduh"),
                        ("penyadap input / layar", 2, "API penyadap papan ketik / layar")):
        if cap in caps:
            add(n, txt)
    if "injeksi / manipulasi proses" not in caps and "injeksi / manipulasi proses" in ind["caps"]:
        add(2, "nama API injeksi proses hanya sebagai string (kemungkinan resolusi API dinamis)")
    if "string ala ransomware" in caps and "kripto" in caps:
        add(3, "string ala ransomware ditambah API kripto")
    if len(caps.get("anti-debug / anti-analisis", [])) >= 2:
        add(1, "beberapa API anti-debug")
    for cap, txt in (("deteksi VM / sandbox", "string deteksi VM / sandbox"), ("persistensi", "API / string persistensi"), ("LOLBin / unduh-eksekusi", "pemakaian LOLBin")):
        if cap in caps:
            add(1, txt)
    if "jaringan" in caps and "eksekusi proses / shell" in caps:
        add(1, "API jaringan dan eksekusi proses sekaligus")
    if ind["pem"]:
        add(1, "kunci privat tertanam")
    if ind["secrets"] or ind.get("secrets_typed"):
        add(1, "kandidat kredensial tertanam")
    emb = rep.get("emb") or {}
    if emb.get("plain") or emb.get("xor"):
        add(3, "PE tertanam di dalam file")
    if any(x[0] in ("PE", "PE/MZ", "ELF") for x in ind.get("b64d", [])):
        add(3, "executable tersembunyi di dalam base64")
    for label, _h in rep.get("tools", []):
        if label in ("UPX", "Obfuscator .NET"):
            add(2, "ditandai %s" % label)
    if pe and not pe.get("broken"):
        if any(n_.lower() in _PACKERS for n_ in (x["name"] for x in pe["sections"])):
            add(2, "nama bagian khas packer")
        if any(x["flags"][1:] == "WX" for x in pe["sections"]):
            add(2, "bagian W+X")
        if any(x["ent"] > 7.2 and x["rsize"] > 4096 for x in pe["sections"]):
            add(1, "bagian berentropi tinggi")
        if not pe["dotnet"] and sum(len(v) for v in pe["imports"].values()) < 8 and rep["size"] > 50000:
            add(2, "import sangat sedikit untuk ukuran file")
        if pe["entry"] and not pe["entry_sec"]:
            add(2, "entry point di luar semua bagian")
        elif pe["entry_sec"] and pe["entry_sec"].lower() not in (".text", "text", ".code", "code", ".itext") and not pe["dotnet"]:
            add(1, "entry point di bagian '%s'" % pe["entry_sec"])
        if pe["tls"]:
            add(1, "ada TLS callback (jalan sebelum entry point)")
        if any(x["mz"] for x in pe.get("res", [])):
            add(3, "executable (MZ) di dalam resource")
        elif any(x.get("fmt") and not x.get("fmt_ok") for x in pe.get("res", [])):
            add(1, "resource berawalan PNG / JPEG / ZIP tetapi kerangkanya tidak utuh")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not x.get("fmt") for x in pe.get("res", [])):
            add(1, "resource besar berentropi tinggi (bukan PNG / JPEG / ZIP)")
        if pe["ts"] > time.time() + 86400:
            add(1, "timestamp kompilasi di masa depan")
    if zp:
        if len(_risky_perms(zp.get("perms", []))) >= 3:
            add(2, "banyak izin Android berisiko")
        if zp.get("ext_rels"):
            add(2, "relasi eksternal dalam dokumen")
        if "makro VBA" in zp["kind"]:
            add(2, "makro VBA")
        if any("terenkripsi" in w_ for w_ in zp["warn"]):
            add(1, "entri arsip terenkripsi")
        if any("zip-slip" in w_ for w_ in zp["warn"]):
            add(2, "path traversal dalam arsip")
    if elf:
        if elf["exec_stack"]:
            add(1, "stack dapat dieksekusi")
        if elf["wx"]:
            add(1, "segmen / bagian W+X")
        if elf["nsec"] == 0 and elf["type"] != "relocatable (.o)":
            add(1, "tabel section dihapus (umum pada kemasan)")
    dc = rep.get("docs")
    if dc:
        for n_, t_ in dc.get("score", []):
            add(n_, t_)
    ov = rep.get("overlay")
    if ov and ov.get("type") == "PE/MZ":
        add(2, "executable di dalam overlay")
    _score_v97(rep, add)
    _score_v98(rep, add)
    _score_v986(rep, add)
    _score_layers(rep, add)
    _score_dso(rep, add)
    level = "TINGGI" if pts >= 7 else "SEDANG" if pts >= 4 else "RENDAH" if pts >= 1 else "TANPA TANDA"
    return pts, level, why


def _df(x: str, on: bool) -> str:
    """defang: hxxp dan [.] supaya IOC tidak bisa terklik tak sengaja."""
    if not on:
        return x
    return x.replace("http", "hxxp").replace("ftp://", "fxp://").replace("ws://", "wxs://").replace("wss://", "wxss://").replace(".", "[.]").replace("@", "[@]")


# kata kunci CAPS yang MEMANG berupa string / nama kelas / nama hak (bukan nama API Win32): kecocokan dari string sudah menjadi bukti
# utama, jadi tidak dianggap lemah. Nama API Win32 yang hanya muncul sebagai teks (tabel nama runtime, daftar string) dianggap lemah.
_STR_NATIVE_KEYS = frozenset({"schtasks", "CurrentVersion\\Run", "system(", "cmd.exe", "powershell", "Assembly.Load", "Reflection",
                              "Process.Start", "HttpClient", "WebClient", "TcpClient", "RijndaelManaged", "SeDebugPrivilege"})


def _cap_strong(ind: dict, cap: str) -> list[str]:
    """Nama pemicu kemampuan 'cap' yang punya bukti kuat (tabel import / string khas), tanpa yang hanya muncul sebagai teks."""
    weak = set((ind.get("caps_weak") or {}).get(cap, ()))
    return [n for n in ind["caps"].get(cap, []) if n not in weak]


def _cap_text(ind: dict, cap: str, hit: list[str]) -> str:
    weak = set((ind.get("caps_weak") or {}).get(cap, ()))
    st, wk = [h for h in hit if h not in weak], [h for h in hit if h in weak]
    if st and wk:
        return "%s: %s | hanya string (lemah): %s" % (cap, ", ".join(st), ", ".join(wk))
    if wk:
        return "%s [hanya string, lemah]: %s" % (cap, ", ".join(wk))
    return "%s: %s" % (cap, ", ".join(st))


def _indicators(strs: list[str], api_names: set[str], ver_quads=()) -> dict:
    # v94: string sangat panjang dipotong 1500 karakter untuk regex lain (cegah ReDoS dari sampel buatan); base64 memakai blob penuh
    full = "\n".join(strs)[:24 * 1024 * 1024]
    blob = "\n".join(s[:1500] for s in strs)[:16 * 1024 * 1024]
    urls = _uniq((u.rstrip(".,;)") for u in _URL.findall(blob)), 25)
    ips = []
    for ip in _IP.findall(blob):
        o = [int(x) for x in ip.split(".")]
        if any(x > 255 for x in o) or o[0] == 0 or (o[2] == 0 and o[3] == 0):
            continue   # buang yang jelas nomor versi
        if ip in ver_quads:
            continue   # sama persis dengan nomor versi di resource VERSION file ini
        ips.append(ip)
    secrets = _uniq((_mask(m) for m in _SECRET.findall(blob)), 8)
    secrets_typed = _scan_secrets(blob)   # v99.3 [C3]; kunci baru, kunci lama "secrets" tidak berubah
    try:
        net = _net_artifacts(blob)   # v99.5 [C1]
    except Exception:
        net = {}
    caps: dict[str, list[str]] = {}
    caps_weak: dict[str, list[str]] = {}
    low_blob = blob.lower()
    api_low = [a.lower() for a in api_names]
    for cap, keys in CAPS.items():
        strong, weak = [], []
        for k in keys:
            kl = k.lower()
            if any(kl in a for a in api_low):
                strong.append(k)
            elif len(k) > 7 and kl in low_blob:
                (strong if k in _STR_NATIVE_KEYS else weak).append(k)
        if strong or weak:
            lst = (strong + weak)[:6]
            caps[cap] = lst
            w_ = [x for x in lst if x in weak]
            if w_:
                caps_weak[cap] = w_
    for cap, keys in STR_CAPS.items():
        hit = [k for k in keys if k in low_blob]
        if hit:
            caps[cap] = hit[:6]
    names_l = {a.lower() for a in api_names}   # v94: nama impor persis (ELF / CRT): hanya cocok utuh supaya tidak salah-deteksi
    for cap, exact in EXACT_CAPS.items():
        hit = [k for k in sorted(exact) if k in names_l]
        if hit:
            caps[cap] = list(dict.fromkeys(caps.get(cap, []) + hit))[:6]
    return {
        "urls": urls, "ips": _uniq(ips, 15), "emails": _uniq(_MAIL.findall(blob), 10),
        "reg": _uniq(_REG.findall(blob), 12), "paths": _uniq(_WPATH.findall(blob), 12),
        "secrets": secrets, "secrets_typed": secrets_typed, "net": net, "pem": bool(_PEM.search(blob)),
        "b64": sum(1 for _ in _B64.finditer(full)), "b64d": _decode_b64(full), "pdb": _uniq(_PDB.findall(blob), 3),
        "caps": caps, "caps_weak": caps_weak, "n_strings": len(strs),
    }


# ---------------------------------------------------------------------------
# Utama
# ---------------------------------------------------------------------------


def _clean(s: str) -> str:
    """v94: buang karakter kontrol dan pengecoh arah teks (RLO dll.) dari keluaran; string dari sampel tidak dipercaya.
    v96.1: baris baru ikut dibuang, supaya nama bagian / entri ZIP / versi bisa menyisipkan baris laporan palsu."""
    return _CTRL_RE.sub("?", s)


_CTRL_RE = re.compile("[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028-\u202e\u2066-\u2069\ufeff]")   # termasuk \n \r \t, U+2028/2029


def _is_reparse(p) -> bool:
    try:
        st = os.lstat(p)
    except OSError:
        return True
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & 0x400)


# kemampuan dari nama impor PERSIS (ELF / CRT); nama pendek tidak dicocokkan sebagian supaya tidak salah-deteksi
EXACT_CAPS = {
    "eksekusi proses / shell": {"system", "popen", "execve", "execv", "execvp", "execl", "execlp", "posix_spawn", "fork", "vfork"},
    "injeksi / manipulasi proses": {"process_vm_writev", "process_vm_readv"},
    "anti-debug / anti-analisis": {"ptrace"},
    "muat kode dinamis": {"dlopen", "dlsym", "mprotect"},
    "hak akses": {"setuid", "setgid", "seteuid", "setresuid", "prctl", "capset"},
    "jaringan": {"socket", "connect", "bind", "listen", "accept", "sendto", "recvfrom", "curl_easy_perform"},
}
STR_CAPS.update({
    "Java / Android: muat kode dinamis": ["dexclassloader", "pathclassloader", "runtime;->exec", "inmemorydexclassloader"],
    "Android: SMS / identitas perangkat": ["sendtextmessage", "sendmultiparttextmessage", "getdeviceid", "getsubscriberid", "getline1number"],
    "Android: aksesibilitas / overlay": ["performglobalaction", "type_application_overlay", "accessibilityservice"],
})
ATTACK = {
    "injeksi / manipulasi proses": "T1055 Process Injection",
    "anti-debug / anti-analisis": "T1622 Debugger Evasion",
    "deteksi VM / sandbox": "T1497 Virtualization/Sandbox Evasion",
    "persistensi": "T1547 / T1543 / T1053 (persistensi)",
    "penyadap input / layar": "T1056 Input Capture / T1113 Screen Capture",
    "pencurian kredensial / dompet": "T1555 / T1003 Credential Access",
    "penghapus jejak / perusak pemulihan": "T1490 Inhibit System Recovery / T1070 Indicator Removal",
    "PowerShell berbahaya / obfuskasi": "T1059.001 PowerShell / T1027 Obfuscation",
    "LOLBin / unduh-eksekusi": "T1218 System Binary Proxy Execution",
    "bypass keamanan": "T1562 Impair Defenses",
    "penambang kripto": "T1496 Resource Hijacking",
    "string ala ransomware": "T1486 Data Encrypted for Impact",
    "hak akses": "T1134 Access Token Manipulation",
    "muat kode dinamis": "T1129 Shared Modules / T1620 Reflective Code Loading",
    "eksekusi proses / shell": "T1059 Command and Scripting Interpreter",
    "kripto": "T1027 / T1573 (kripto / enkripsi)",
    "jaringan": "T1071 Application Layer Protocol",
}


# v99.6 [A3]: GUID COM (CLSID / IID) yang dikenal. (guid, nama, kelompok, catatan). Hanya yang pasti; daftar bisa diperluas lewat tuple ini.
_COM_GUIDS = (
    ("4991D34B-80A1-4291-83B6-3328366B9097", "BackgroundCopyManager (CLSID)", "BITS", ""),
    ("5CE34C0D-0DC9-4C1F-897C-DAA1B78CEE7C", "IBackgroundCopyManager (IID)", "BITS", ""),
    ("4590F811-1D3A-11D0-891F-00AA004B2E24", "WbemLocator (CLSID)", "WMI", ""),
    ("CB8555CC-9128-11D1-AD9B-00C04FD8FDFF", "WbemAdministrativeLocator (CLSID)", "WMI", ""),
    ("DC12A687-737F-11CF-884D-00AA004B2E24", "IWbemLocator (IID)", "WMI", ""),
    ("9556DC99-828C-11CF-A37E-00AA003240C7", "IWbemServices (IID)", "WMI", ""),
    ("44ACA674-E8FC-11D0-A07C-00C04FB68820", "IWbemContext (IID)", "WMI", ""),
    ("0F87369F-A4E5-4CFC-BD3E-73E6154572DD", "TaskScheduler (CLSID)", "Task Scheduler", ""),
    ("2FABA4C7-4DA9-4013-9697-20CC3FD40F85", "ITaskService (IID)", "Task Scheduler", ""),
    ("9BA05972-F6A8-11CF-A442-00A0C90A8F39", "ShellWindows (CLSID)", "DCOM Shell", "dipakai untuk eksekusi lewat objek DCOM / lateral movement"),
    ("C08AFD90-F2A1-11D1-8455-00A0C91F3880", "ShellBrowserWindow (CLSID)", "DCOM Shell", "dipakai untuk eksekusi lewat objek DCOM / lateral movement"),
    ("85CB6900-4D95-11CF-960C-0080C7F4EE85", "IShellWindows (IID)", "DCOM Shell", ""),
    ("49B2791A-B1AE-4C90-9B8E-E860BA07F889", "MMC20.Application (CLSID)", "DCOM MMC", "dipakai untuk eksekusi lewat DCOM / lateral movement"),
    ("13709620-C279-11CE-A49E-444553540000", "Shell.Application (CLSID)", "Shell", ""),
    ("72C24DD5-D70A-438B-8A42-98424B88AFB8", "WScript.Shell (CLSID)", "Script host", ""),
    ("0D43FE01-F093-11CF-8940-00A0C9054228", "Scripting.FileSystemObject (CLSID)", "Script host", ""),
    ("00000566-0000-0010-8000-00AA006D2EA4", "ADODB.Stream (CLSID)", "Script host", "umum pada dropper skrip (tulis biner dari teks)"),
    ("0E59F1D5-1FBE-11D0-8FF2-00A0D10038BC", "MSScriptControl.ScriptControl (CLSID)", "Script host", ""),
    ("2087C2F4-2CEF-4953-A8AB-66779B670495", "WinHttpRequest.5.1 (CLSID)", "Klien HTTP", ""),
    ("88D96A0A-F192-11D4-A65F-0040963251E5", "XMLHTTP 6.0 (CLSID)", "Klien HTTP", ""),
    ("0002DF01-0000-0000-C000-000000000046", "InternetExplorer.Application (CLSID)", "Otomasi IE", ""),
    ("3E5FC7F9-9A51-4367-9063-A120244FBEC7", "CMSTPLUA (CLSID)", "Elevasi COM (UAC)", "objek COM elevasi otomatis; lazim di teknik bypass UAC"),
    ("3E000D72-A845-4CD9-BD83-80C07C3B881F", "CMLUAUTIL (CLSID)", "Elevasi COM (UAC)", "objek COM elevasi otomatis; lazim di teknik bypass UAC"),
    ("6EDD6D74-C007-4E75-B76A-E5740995E24C", "ICMLuaUtil (IID)", "Elevasi COM (UAC)", "antarmuka ShellExec; lazim di teknik bypass UAC"),
    ("3AD05575-8857-4850-9277-11B85BDB8E09", "FileOperation (CLSID)", "Elevasi COM (UAC)", "IFileOperation: salin berkas ke lokasi terlindungi (teknik bypass UAC)"),
    ("947AAB5F-0A5C-4C13-B4D6-4BF7836FC9F8", "IFileOperation (IID)", "Elevasi COM (UAC)", ""),
    ("E2B3C97F-6AE1-41AC-817A-F6F92166D7DD", "NetFwPolicy2 (CLSID)", "Firewall Windows", ""),
    ("98325047-C671-4174-8D81-DEFCD3F03186", "INetFwPolicy2 (IID)", "Firewall Windows", ""),
)
_COM_NOTE_GROUPS = {"DCOM Shell", "DCOM MMC", "Elevasi COM (UAC)"}
_COM_API = ("CoCreateInstance", "CoCreateInstanceEx", "CoGetClassObject", "CoInitialize", "CoInitializeEx", "CoInitializeSecurity",
            "OleInitialize", "CLSIDFromProgID", "CLSIDFromString", "CoGetObject", "CoSetProxyBlanket", "StringFromCLSID", "DllGetClassObject")
_GUID_STR = re.compile(rb"\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}")
_GUID_CACHE: list = []


def _com_artifacts(d: bytes, api_names) -> dict:
    """v99.6 [A3]: objek COM dari GUID CLSID / IID (bentuk biner 16-byte, atau string {GUID} ASCII / UTF-16), plus API COM yang diimpor."""
    import uuid as _uuid
    if not _GUID_CACHE:
        for g, nm, grp, note in _COM_GUIDS:
            u = _uuid.UUID(g)
            _GUID_CACHE.append((u.bytes_le, ("{%s}" % g).encode(), ("{%s}" % g.lower()).encode(), ("{%s}" % g).encode("utf-16-le"), nm, grp, note))
    t0 = time.monotonic()
    hits: dict[str, dict] = {}
    for bin_, up, lo, u16, nm, grp, note in _GUID_CACHE:
        if time.monotonic() - t0 > 3.0:
            break
        how = "biner" if bin_ in d else "string" if (up in d or lo in d or u16 in d) else ""
        if how:
            h = hits.setdefault(grp, {"names": [], "how": set(), "note": ""})
            h["names"].append(nm)
            h["how"].add(how)
            h["note"] = h["note"] or note
    known = {x[0].lower() for x in _COM_GUIDS}
    unknown: list[str] = []
    for m in _GUID_STR.finditer(d[:8 * 1024 * 1024]):
        g = m.group(0).decode()[1:-1].lower()
        if g not in known and g not in unknown:
            unknown.append(g)
        if len(unknown) >= 6:
            break
    apis = sorted(a for a in api_names if any(a == c or a.startswith(c) for c in _COM_API))[:8]
    groups = [{"group": g, "names": v["names"][:5], "how": "+".join(sorted(v["how"])), "note": v["note"]} for g, v in hits.items()]
    return {"groups": groups, "unknown": unknown, "apis": apis}


def _elf_hardening(d: bytes, elf: dict) -> dict:
    """v99.3 [B3]: mitigasi ELF (PIE, RELRO, NX, stack canary, FORTIFY_SOURCE, RPATH / RUNPATH). Hanya membaca header program + .dynamic.
    Hasil = petunjuk dari struktur berkas; biner statis / stripped bisa tampak 'tidak ada' padahal diaktifkan lewat cara lain."""
    out: dict = {"pie": "?", "relro": "?", "nx": "?", "canary": False, "fortify": 0, "rpath": [], "bind_now": False}
    if len(d) < 64 or d[:4] != b"\x7fELF":
        return out
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    etype = struct.unpack_from(en + "H", d, 16)[0]
    if is64:
        phoff = struct.unpack_from(en + "Q", d, 32)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 54)
    else:
        phoff = struct.unpack_from(en + "I", d, 28)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 42)
    esz = 56 if is64 else 32
    has_relro = has_stack = False
    dyn_off = dyn_sz = 0
    loads: list[tuple[int, int, int]] = []
    for i in range(min(phnum, 64)):
        o = phoff + i * phentsz
        if phentsz < esz or o + esz > len(d):
            break
        if is64:
            pt, pf, poff, pva, _pa, fsz, _msz, _al = struct.unpack_from(en + "IIQQQQQQ", d, o)
        else:
            pt, poff, pva, _pa, fsz, _msz, pf, _al = struct.unpack_from(en + "IIIIIIII", d, o)
        if pt == 1:
            loads.append((pva, poff, fsz))
        elif pt == 2:
            dyn_off, dyn_sz = poff, fsz
        elif pt == 0x6474E552:
            has_relro = True
        elif pt == 0x6474E551:
            has_stack = True
            out["nx"] = "tidak" if pf & 1 else "ya"
    if not has_stack:
        out["nx"] = "tidak pasti (tanpa PT_GNU_STACK)"
    tags: dict[int, int] = {}
    rp: list[tuple[int, int]] = []
    if dyn_off and dyn_off < len(d):
        esz_d = 16 if is64 else 8
        for k in range(min(dyn_sz // esz_d, 512)):
            o = dyn_off + k * esz_d
            if o + esz_d > len(d):
                break
            tag, val = struct.unpack_from(en + ("qQ" if is64 else "iI"), d, o)
            if tag == 0:
                break
            if tag in (15, 29):
                rp.append((tag, val))
            else:
                tags[tag] = val
    flags, flags1 = tags.get(30, 0), tags.get(0x6FFFFFFB, 0)
    out["bind_now"] = bool(24 in tags or flags & 0x8 or flags1 & 0x1)
    out["relro"] = ("full" if out["bind_now"] else "partial") if has_relro else "tidak ada"
    if etype == 2:
        out["pie"] = "tidak"
    elif etype == 3:
        out["pie"] = "ya" if (flags1 & 0x08000000 or elf.get("interp")) else "n/a (pustaka bersama)"
    if rp and 5 in tags:
        def va2off(va: int) -> int:
            for lv, lo, lsz in loads:
                if lv <= va < lv + lsz:
                    return lo + (va - lv)
            return -1
        so = va2off(tags[5])
        for tag, val in rp[:4]:
            if so >= 0 and so + val < len(d):
                e = d.find(b"\0", so + val, so + val + 256)
                txt = d[so + val:(e if e != -1 else so + val + 256)].decode("latin-1", "replace")
                out["rpath"].append(("RPATH " if tag == 15 else "RUNPATH ") + txt)
    imps = (elf.get("dyn") or {}).get("imports") or []
    base = {x.split("@")[0] for x in imps}
    out["canary"] = bool(base & {"__stack_chk_fail", "__stack_chk_guard", "__intel_security_cookie"}) or (not imps and b"__stack_chk_fail" in d)
    out["fortify"] = sum(1 for x in base if x.startswith("__") and x.endswith("_chk") and x != "__stack_chk_fail")
    return out


def _elf_imports(d: bytes) -> dict:
    """Impor dinamis ELF (.dynsym), pustaka NEEDED (.dynamic), dan simbol ekspor. Hanya membaca."""
    out: dict = {"needed": [], "imports": [], "exports": []}
    if len(d) < 64 or d[:4] != b"\x7fELF":
        return out
    is64 = d[4] == 2
    en = "<" if d[5] == 1 else ">"
    try:
        if is64:
            shoff = struct.unpack_from(en + "Q", d, 40)[0]
            shentsz, shnum = struct.unpack_from(en + "HH", d, 58)
        else:
            shoff = struct.unpack_from(en + "I", d, 32)[0]
            shentsz, shnum = struct.unpack_from(en + "HH", d, 46)
        if not shoff or not shnum or shentsz < (64 if is64 else 40):
            return out
        secs = []
        for i in range(min(shnum, 128)):
            o = shoff + i * shentsz
            if o + (64 if is64 else 40) > len(d):
                break
            if is64:
                _nm, st, _fl, _ad, off, sz, link, _inf, _al, es = struct.unpack_from(en + "IIQQQQIIQQ", d, o)
            else:
                _nm, st, _fl, _ad, off, sz, link, _inf, _al, es = struct.unpack_from(en + "IIIIIIIIII", d, o)
            secs.append((st, off, sz, link, es))

        def tab(idx: int) -> bytes:
            if idx >= len(secs):
                return b""
            return d[secs[idx][1]:secs[idx][1] + min(secs[idx][2], 1 << 22)]

        def nm_at(t: bytes, o: int) -> str:
            e = t.find(b"\0", o)
            return t[o:(e if e != -1 else o + 128)][:128].decode("latin-1", "replace")

        for st, off, sz, link, es in secs:
            if st == 11:   # SHT_DYNSYM
                t = tab(link)
                esz = es or (24 if is64 else 16)
                for k in range(min(sz // esz, 4000)):
                    o = off + k * esz
                    if o + esz > len(d):
                        break
                    if is64:
                        nm, _i, _o, shndx = struct.unpack_from(en + "IBBH", d, o)
                    else:
                        nm = struct.unpack_from(en + "I", d, o)[0]
                        shndx = struct.unpack_from(en + "H", d, o + 14)[0]
                    if nm:
                        (out["imports"] if shndx == 0 else out["exports"]).append(nm_at(t, nm))
            elif st == 6:   # SHT_DYNAMIC
                t = tab(link)
                esz = 16 if is64 else 8
                for k in range(min(sz // esz, 512)):
                    o = off + k * esz
                    if o + esz > len(d):
                        break
                    tag, val = struct.unpack_from(en + ("qQ" if is64 else "iI"), d, o)
                    if tag == 0:
                        break
                    if tag == 1:
                        out["needed"].append(nm_at(t, val))
    except (struct.error, IndexError, ValueError):
        pass
    for k_ in out:
        out[k_] = list(dict.fromkeys(out[k_]))
    return out


_OV_MAGIC = ((b"MZ", "PE/MZ"), (b"PK\x03\x04", "ZIP"), (b"7z\xbc\xaf\x27\x1c", "7z"), (b"Rar!", "RAR"), (b"MSCF", "CAB"), (b"\x1f\x8b", "gzip"))


def _overlay_info(d: bytes, pe: dict):
    """Jenis, entropi, dan hash overlay PE (data setelah bagian terakhir, di luar blob tanda tangan)."""
    ov, start = pe.get("overlay", 0), pe.get("last_raw", 0)
    if ov < 8 or start <= 0 or start >= len(d):
        return None
    seg = d[start:start + min(ov, 4 * 1024 * 1024)]
    typ = "data"
    for sig, name in _OV_MAGIC:
        if seg.startswith(sig):
            typ = name
            break
    else:
        if seg[4:20] == b"\xef\xbe\xad\xdeNullsoftInst":
            typ = "NSIS"
    sha = hashlib.sha256(d[start:start + ov]).hexdigest() if start + ov <= len(d) else ""
    return {"size": ov, "off": start, "ent": _entropy(seg[:1 << 20]), "type": typ, "sha256": sha}


def _pe_checksum_check(d: bytes, size: int):
    """(tersimpan, hitungan, cocok) untuk CheckSum header PE; None kalau tidak berlaku (0, file dipotong, terlalu besar)."""
    if len(d) != size or len(d) < 0x100 or len(d) > 32 * 1024 * 1024:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    co = pe_off + 24 + 64
    if co + 4 > len(d):
        return None
    stored = struct.unpack_from("<I", d, co)[0]
    if stored == 0:
        return None
    buf = bytearray(d)
    buf[co:co + 4] = b"\0\0\0\0"
    if len(buf) % 2:
        buf.append(0)
    a = array.array("H")
    a.frombytes(bytes(buf))
    if sys.byteorder == "big":
        a.byteswap()
    tot = sum(a)
    while tot >> 16:
        tot = (tot & 0xFFFF) + (tot >> 16)
    calc = (tot + size) & 0xFFFFFFFF
    return stored, calc, calc == stored


_CRYPTO_SIGS = (
    ("AES S-box", bytes.fromhex("637c777bf26b6fc53001672bfed7ab76")),
    ("AES S-box inversa", bytes.fromhex("52096ad53036a538bf40a39e81f3d7fb")),
    ("SHA-256 (tabel K)", bytes.fromhex("982f8a4291443771")),
    ("SHA-256 (nilai awal)", bytes.fromhex("67e6096a85ae67bb")),
    ("SHA-512 (tabel K)", bytes.fromhex("22ae28d7982f8a42")),
    ("CRC32 (tabel)", bytes.fromhex("00000000963007772c610eee")),
    ("CRC32 (polinomial 0xEDB88320)", bytes.fromhex("2083b8ed")),
    ("ChaCha20 / Salsa20", b"expand 32-byte k"),
    ("ChaCha20 / Salsa20 (kunci 16 byte)", b"expand 16-byte k"),
    ("Blowfish (P-array)", bytes.fromhex("886a3f24d308a385")),
    ("tabel Base64 standar", b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
)
_MD5_INIT = tuple(bytes.fromhex(x) for x in ("01234567", "89abcdef", "fedcba98", "76543210"))


def _crypto_consts(d: bytes) -> list[str]:
    """Konstanta algoritma kripto yang dikenal (gaya findcrypt). Petunjuk: kehadirannya tidak membuktikan dipakai."""
    h = d[: 16 * 1024 * 1024]
    out = [name for name, sig in _CRYPTO_SIGS if h.find(sig) != -1]
    if all(h.find(c) != -1 for c in _MD5_INIT):
        out.append("SHA-1 (nilai awal)" if h.find(bytes.fromhex("f0e1d2c3")) != -1 else "MD5 (nilai awal)")
    return out


_PDF_RISK = {
    "/JavaScript": (2, "JavaScript"), "/JS": (2, "JavaScript"), "/OpenAction": (1, "aksi otomatis saat dibuka (OpenAction)"),
    "/AA": (1, "aksi tambahan otomatis (AA)"), "/Launch": (3, "perintah Launch (menjalankan program)"), "/EmbeddedFile": (1, "berkas tertanam"),
    "/RichMedia": (1, "RichMedia (Flash)"), "/XFA": (1, "formulir XFA"), "/SubmitForm": (1, "SubmitForm (kirim data keluar)"),
    "/GoToR": (1, "tautan ke berkas eksternal (GoToR)"), "/URI": (0, "tautan URI"),
}


def _parse_docs(d: bytes, kind: str):
    """PDF, OLE2, RTF, LNK, dan skrip teks: indikator struktural. Semua hanya pembacaan byte; tidak ada yang dijalankan."""
    info: list[str] = []
    score: list[tuple[int, str]] = []
    low = d[: 8 * 1024 * 1024].lower()
    k = kind or ""
    if k == "PDF":
        names: collections.Counter = collections.Counter()
        obf = 0
        for m in re.finditer(rb"/[A-Za-z0-9#]{2,40}", d):
            tok = m.group(0)
            if b"#" in tok:
                dec = re.sub(rb"#([0-9A-Fa-f]{2})", lambda mm: bytes([int(mm.group(1), 16)]), tok)
                if dec != tok:
                    obf += 1
                tok = dec
            names[tok.decode("latin-1", "replace")] += 1
        info.append("objek %d, halaman %d, penanda EOF %d" % (d.count(b"endobj"), names.get("/Page", 0), d.count(b"%" + b"%EOF")))
        seen: set[str] = set()
        for key, (n, txt_) in _PDF_RISK.items():
            c = names.get(key, 0)
            if c:
                info.append("%s x%d: %s" % (key, c, txt_))
                if n and txt_ not in seen:
                    seen.add(txt_)
                    score.append((n, "PDF: " + txt_))
        if names.get("/ObjStm", 0) > 5:
            info.append("/ObjStm x%d (objek terkompres; bisa menyembunyikan aksi)" % names["/ObjStm"])
        if names.get("/Encrypt", 0):
            info.append("PDF terenkripsi (/Encrypt): isi tidak bisa dibaca statis")
        if obf:
            info.append("%d nama objek berobfuskasi dengan #xx" % obf)
            score.append((2, "nama objek PDF berobfuskasi (#xx)"))
        idx = d.rfind(b"%" + b"%EOF")
        if idx != -1 and len(d) - (idx + 5) > 1024:
            info.append("data tambahan %s setelah penanda EOF terakhir" % _human(len(d) - idx - 5))
            score.append((1, "data tambahan setelah EOF PDF"))
    elif k.startswith("OLE2"):
        marks = (("_VBA_PROJECT", "makro VBA", 2), ("Macros", "folder Macros", 0), ("WordDocument", "dokumen Word", 0), ("Workbook", "buku kerja Excel", 0),
                 ("PowerPoint Document", "presentasi PowerPoint", 0), ("ObjectPool", "objek OLE tertanam", 1), ("Ole10Native", "paket OLE tertanam (Ole10Native)", 1),
                 ("EncryptedPackage", "dokumen dienkripsi (kata sandi)", 0), ("Equation Native", "Equation Editor (pola exploit lama CVE-2017-11882)", 3))
        for key, txt_, n in marks:
            if d.find(key.encode("utf-16le"), 0, MAX_SCAN) != -1 or d.find(key.encode(), 0, MAX_SCAN) != -1:
                info.append(txt_)
                if n:
                    score.append((n, "OLE2: " + txt_))
        auto = [x.decode() for x in (b"autoopen", b"document_open", b"workbook_open", b"auto_open", b"autoexec", b"document_close", b"autoclose") if x in low]
        sus = [x.decode() for x in (b"createobject", b"wscript.shell", b"shell(", b"powershell", b"urldownloadtofile", b"xmlhttp", b"adodb.stream", b"cmd.exe", b"mshta", b"regsvr32") if x in low]
        if auto:
            info.append("pemicu otomatis makro: " + ", ".join(auto))
            score.append((2, "makro dengan pemicu otomatis"))
        if sus:
            info.append("API / perintah mencurigakan di makro: " + ", ".join(sus[:6]))
            score.append((2, "makro memanggil API / perintah mencurigakan"))
    elif k == "RTF":
        for key, n, txt_ in ((b"\\objdata", 1, "objek OLE tertanam (\\objdata)"), (b"\\objupdate", 2, "\\objupdate (memaksa objek diperbarui saat dibuka)"),
                             (b"\\objautlink", 1, "objek tertaut otomatis"), (b"\\*\\template", 2, "template eksternal"), (b"equation.3", 3, "Equation Editor (pola exploit lama)")):
            if key in low:
                info.append(txt_)
                score.append((n, "RTF: " + txt_))
        if re.search(rb"[0-9a-f]{4096,}", low):
            info.append("blok heksadesimal panjang (payload tertanam)")
            score.append((1, "RTF memuat blok heksadesimal panjang"))
    elif k.startswith("Shortcut"):
        l16 = d[: 1 << 20].decode("utf-16le", "ignore").lower()
        l8 = low[: 1 << 20]
        keys = ("powershell", "cmd.exe", "mshta", "wscript", "cscript", "rundll32", "regsvr32", "-enc", "-windowstyle hidden", "downloadstring", "http://", "https://", "certutil", "bitsadmin")
        hits = [x for x in keys if x in l16 or x.encode() in l8]
        if len(d) >= 0x18 and struct.unpack_from("<I", d, 0x14)[0] & 0x20:
            info.append("shortcut memakai argumen baris perintah")
        if hits:
            info.append("kata pada target / argumen: " + ", ".join(hits[:8]))
            score.append((2, "shortcut memanggil interpreter / pengunduh"))
        if len(d) > 8192:
            info.append("shortcut besar (%s): bisa membawa payload di dalamnya" % _human(len(d)))
            score.append((1, "shortcut berukuran besar"))
    elif k.startswith("teks") or k.startswith("skrip"):
        raw = d[: 2 * 1024 * 1024]
        txt = raw.decode("utf-16", "ignore") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "ignore")
        tl = txt.lower()
        longest = max((len(x) for x in txt.splitlines()), default=0)
        ind = []
        if longest > 10000:
            ind.append("baris sangat panjang (%d karakter)" % longest)
        pats = ((r"\beval\s*\(", 3, "eval()"), (r"fromcharcode", 2, "fromCharCode"), (r"\bunescape\s*\(", 1, "unescape()"), (r"\batob\s*\(", 1, "atob()"),
                (r"frombase64string", 1, "FromBase64String"), (r"-enc(?:odedcommand)?\b", 1, "-EncodedCommand"), (r"invoke-expression|\biex\b", 2, "Invoke-Expression/iex"),
                (r"\bchr\w?\s*\(", 30, "chr() berulang"), (r"\\x[0-9a-f]{2}", 100, "escape \\xNN berulang"), (r"\w`\w", 20, "backtick di tengah kata (obfuskasi PowerShell)"),
                (r"-bxor|-join|\[char\]", 5, "operasi dekode (-bxor / -join / [char])"), (r"wscript\.shell|activexobject|createobject", 1, "objek COM untuk eksekusi"),
                (r"downloadstring|downloadfile|invoke-webrequest|xmlhttp|urldownloadtofile|bitsadmin|certutil", 1, "unduh dari jaringan"))
        for pat, lim, label in pats:
            n = len(re.findall(pat, tl))
            if n >= lim:
                ind.append("%s x%d" % (label, n))
        if ind:
            info = ind
            score.append((2 if len(ind) >= 3 else 1, "skrip dengan indikator obfuskasi / unduh-eksekusi (%d indikator)" % len(ind)))
    if not info and not score:
        return None
    return {"fmt": k, "info": info, "score": score}


# ---------------------------------------------------------------------------
# v98.6: integritas Authenticode, daftar hash lokal, peredam CRT, XOR kunci berulang, resource .NET
# ---------------------------------------------------------------------------

_OID_SPC_INDIRECT = bytes.fromhex("060a2b060104018237020104")
_AC_ALGS = (   # (OID DER lengkap dengan tag + panjang, nama hashlib, ukuran digest)
    (bytes.fromhex("0609608648016503040201"), "sha256", 32),
    (bytes.fromhex("0609608648016503040202"), "sha384", 48),
    (bytes.fromhex("0609608648016503040203"), "sha512", 64),
    (bytes.fromhex("06052b0e03021a"), "sha1", 20),
    (bytes.fromhex("06082a864886f70d0205"), "md5", 16),
)


def _ac_digests(blob: bytes) -> list[tuple[str, bytes]]:
    """Semua (algoritma, digest) dari SpcIndirectDataContent di blob PKCS#7 (tanda tangan ganda / bersarang menghasilkan lebih dari satu)."""
    out: list[tuple[str, bytes]] = []
    pos = blob.find(_OID_SPC_INDIRECT)
    n = 0
    while pos != -1 and n < 8:
        win = blob[pos:pos + 768]
        best = None
        for oid, name, dsz in _AC_ALGS:
            i = win.find(oid)
            while i != -1:
                j = i + len(oid)
                if win[j:j + 2] == b"\x05\x00":
                    j += 2
                if win[j:j + 2] == bytes([4, dsz]) and j + 2 + dsz <= len(win):
                    if best is None or i < best[0]:
                        best = (i, name, win[j + 2:j + 2 + dsz])
                    break
                i = win.find(oid, i + 1)
        if best:
            out.append((best[1], best[2]))
        pos = blob.find(_OID_SPC_INDIRECT, pos + 1)
        n += 1
    return out


def _authenticode_hash(d: bytes, size: int, pe: dict, alg: str) -> str | None:
    """Hash Authenticode sesuai spesifikasi Microsoft: seluruh berkas KECUALI field CheckSum, entri Certificate Table di data directory, dan
    isi tabel sertifikat. None bila berkas tidak utuh di memori atau tabel section tidak masuk akal."""
    if len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    ck = o + 64
    cdir = o + (112 if is64 else 96) + 8 * 4
    hsz = struct.unpack_from("<I", d, o + 60)[0]
    if cdir + 8 > len(d) or hsz > len(d) or hsz < cdir + 8:
        return None
    c_off, c_sz = struct.unpack_from("<II", d, cdir)
    h = hashlib.new(alg)
    h.update(d[:ck])
    h.update(d[ck + 4:cdir])
    h.update(d[cdir + 8:hsz])
    pos = hsz
    for s in sorted((x for x in pe["sections"] if x["rsize"]), key=lambda x: x["rptr"]):
        a, b = s["rptr"], s["rptr"] + s["rsize"]
        if a < pos or b > len(d):
            return None   # bagian tumpang-tindih / keluar berkas: jangan menebak
        h.update(d[a:b])
        pos = b
    if c_off and c_sz and c_off >= pos:
        h.update(d[pos:c_off])
        h.update(d[c_off + c_sz:])
    else:
        h.update(d[pos:])
    return h.hexdigest()


def _authenticode_check(d: bytes, size: int, pe: dict) -> dict | None:
    """Integritas (BUKAN keabsahan) tanda tangan: digest di blob vs hash isi berkas. match True / False; None bila tidak berlaku.
    Tidak memeriksa rantai sertifikat, masa berlaku, atau pencabutan: itu butuh Get-AuthenticodeSignature / signtool."""
    if not pe.get("signed") or len(d) != size:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    c_off, c_sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 4)
    if c_off + 8 > len(d) or c_sz < 8:
        return None
    end = min(c_off + c_sz, len(d))
    cands: list[tuple[str, bytes]] = []
    pos = c_off
    while pos + 8 <= end and len(cands) < 8:
        dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
        if dw < 8 or pos + dw > end:
            break
        if typ == 2:
            cands += _ac_digests(d[pos + 8:pos + dw])
        pos += (dw + 7) & ~7
    if not cands:
        return None
    cache: dict[str, str | None] = {}
    first = None
    for alg, dig in cands:
        if alg not in cache:
            cache[alg] = _authenticode_hash(d, size, pe, alg)
        comp = cache[alg]
        if comp is None:
            return None
        if first is None:
            first = (alg, dig.hex(), comp)
        if comp == dig.hex():
            return {"alg": alg, "signed": dig.hex(), "computed": comp, "match": True}
    return {"alg": first[0], "signed": first[1], "computed": first[2], "match": False}


_CO_STOP = frozenset({"corporation", "company", "limited", "software", "technologies", "technology", "group", "holdings", "international",
                      "systems", "solutions", "services", "global", "foundation"})


def _signer_vs_company(pe: dict):
    """True / False: apakah nama penandatangan (CN) memuat kata dari CompanyName. None bila salah satunya tidak ada. Hanya informasi."""
    sg, comp = pe.get("signers") or [], (pe.get("ver") or {}).get("CompanyName", "")
    tok = lambda s: {t for t in re.findall(r"[a-z0-9]{4,}", s.lower())} - _CO_STOP
    a, b = tok(comp), set().union(*(tok(s) for s in sg)) if sg else set()
    if not a or not b:
        return None
    return bool(a & b)


_KNOWN_CACHE: dict = {"key": None, "map": {}}


def _known_hashes() -> dict[str, tuple[str, str]]:
    """Daftar hash lokal dari berkas teks di env REA_KNOWN_HASHES. Satu baris: HEX [good|bad|note] [label]. '#' = komentar.
    HEX boleh md5 / sha1 / sha256. Hasil di-cache menurut mtime."""
    p = os.environ.get("REA_KNOWN_HASHES", "")
    if not p:
        return {}
    try:
        st = os.stat(p)
    except OSError:
        return {}
    key = (p, st.st_mtime_ns, st.st_size)
    if _KNOWN_CACHE["key"] == key:
        return _KNOWN_CACHE["map"]
    m: dict[str, tuple[str, str]] = {}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            txt = fh.read(8 * 1024 * 1024)
        for ln in txt.splitlines()[:200000]:
            ln = ln.split("#", 1)[0].strip()
            if not ln:
                continue
            parts = ln.split(None, 2)
            h = parts[0].lower()
            if len(h) not in (32, 40, 64) or not re.fullmatch(r"[0-9a-f]+", h):
                continue
            tag, label = "note", ""
            if len(parts) > 1:
                if parts[1].lower() in ("good", "bad", "note"):
                    tag, label = parts[1].lower(), (parts[2] if len(parts) > 2 else "")
                else:
                    label = " ".join(parts[1:])
            m[h] = (tag, label[:120])
    except OSError:
        return {}
    _KNOWN_CACHE["key"], _KNOWN_CACHE["map"] = key, m
    return m


def _known_lookup(rep: dict) -> dict | None:
    km = _known_hashes()
    if not km:
        return None
    for k in ("sha256", "sha1", "md5"):
        hit = km.get(rep.get(k, ""))
        if hit:
            if hit[0] == "good" and k != "sha256":   # MD5 / SHA-1 bisa dibuat tabrakan: tidak cukup untuk label 'sah'
                return {"tag": "note", "label": ("(entri 'good' via %s tidak dipercaya; gunakan SHA-256) " % k + hit[1]).strip(), "by": k}
            return {"tag": hit[0], "label": hit[1], "by": k}
    return None


# API yang ada di hampir semua program MSVC / CRT (bukan indikasi niat). Hanya PE native yang dilipat; .NET P/Invoke tetap dilaporkan.
_CRT_COMMON = frozenset({"isdebuggerpresent", "getprocaddress", "loadlibrary", "createfile"})


def _crt_fold_ok(rep: dict) -> bool:
    pe = rep.get("pe")
    return bool(pe and not pe.get("broken") and not pe.get("dotnet"))


def _score_v986(rep: dict, add) -> None:
    ac = rep.get("authenticode")
    if ac and ac.get("match") is False:
        add(3, "digest Authenticode tidak cocok dengan isi file (diubah setelah ditandatangani)")
    kn = rep.get("known")
    if kn and kn["tag"] == "bad":
        add(10, "hash cocok daftar lokal 'bad'%s" % ((": " + kn["label"]) if kn["label"] else ""))
    xm = rep.get("xor_multi") or []
    if xm:
        add(3 if any(x["mz"] for x in xm) else 2, "stub DOS terenkode XOR kunci berulang%s" % (" (PE tersembunyi)" if any(x["mz"] for x in xm) else ""))
    dn = rep.get("dotnet")
    emb = rep.get("emb") or {}
    if dn and dn.get("mres"):
        if any(x["mz"] for x in dn["mres"]) and not (emb.get("plain") or emb.get("xor")):
            add(3, "executable (MZ) di dalam resource terkelola .NET")
        elif any(x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")) for x in dn["mres"]):
            add(1, "resource terkelola .NET berentropi tinggi (bukan PNG / JPEG / ZIP utuh)")


def _render_v986(rep: dict, a, compact: bool, defang: bool) -> None:
    pe = rep.get("pe")
    ac = rep.get("authenticode")
    if ac:
        if ac["match"]:
            a("Integritas tanda tangan: digest %s di blob COCOK dengan hash isi file (berkas utuh sejak ditandatangani). Rantai sertifikat dan pencabutan TIDAK diperiksa." % ac["alg"])
        else:
            a("Integritas tanda tangan: digest %s di blob %s... TIDAK sama dengan hash isi file %s...: berkas diubah setelah ditandatangani." % (ac["alg"], ac["signed"][:16], ac["computed"][:16]))
    if pe and not pe.get("broken") and pe.get("signers"):
        sm = rep.get("signer_match")
        if sm is False:
            a("Penandatangan vs CompanyName: tidak ada kata yang sama (%s vs %s). Hanya informasi; perusahaan induk / penerbit lain juga lazim." % (", ".join(pe["signers"][:2]), (pe.get("ver") or {}).get("CompanyName", "?")))
        elif sm:
            a("Penandatangan vs CompanyName: sejalan.")
    dn = rep.get("dotnet")
    if dn and dn.get("mres"):
        tot = sum(x["size"] for x in dn["mres"])
        a("Resource .NET: %d blob terkelola (%s)%s" % (len(dn["mres"]), _human(tot), ("; MZ di dalam: " + ", ".join("0x%X" % x["off"] for x in dn["mres"] if x["mz"])) if any(x["mz"] for x in dn["mres"]) else ""))
        if not compact:
            for x in sorted(dn["mres"], key=lambda x: -x["size"])[:4]:
                a("   - off 0x%X %s ent %.2f%s%s" % (x["off"], _human(x["size"]), x["ent"], " .resources" if x.get("rsrc") else "", " MZ" if x["mz"] else ""))
    for x in (rep.get("xor_multi") or [])[: (1 if compact else 3)]:
        a("Perburuan XOR kunci berulang: periode %d byte, kunci %s, stub DOS di offset 0x%X%s" % (x["k"], x["key"], x["off"], " | MZ terkonfirmasi di 0x%X" % x["mz_off"] if x["mz"] else ""))


def _fold_caps(rep: dict) -> tuple[list[tuple[str, list[str], list[str]]], list[tuple[str, list[str]]], set[str]]:
    """Pisahkan nama kemampuan (tampil) dari nama umum CRT (dilipat). -> (baris, terlipat, kemampuan yang seluruhnya CRT)."""
    ind = rep["ind"]
    fold_on = _crt_fold_ok(rep)
    rows, folded, crt_only = [], [], set()
    for cap, hit in ind["caps"].items():
        keep = [h for h in hit if not (fold_on and h.lower() in _CRT_COMMON)]
        fold = [h for h in hit if fold_on and h.lower() in _CRT_COMMON]
        if fold:
            folded.append((cap, fold))
        if keep:
            rows.append((cap, keep, fold))
        else:
            crt_only.add(cap)
    return rows, folded, crt_only


def render_card(rep: dict, defang: bool = True) -> str:
    """Kartu ringkas: skor, alasan, faktor penyeimbang, PERHATIAN dulu; rincian (import, string, bagian) dilipat jadi hitungan."""
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("KARTU TRIASE | %s | %s | %s" % (rep["name"], _human(rep["size"]), rep["kind"]))
    kn = rep.get("known")
    if kn:
        a("Daftar hash lokal (%s): %s%s" % (kn["by"], {"good": "DIKENAL SAH", "bad": "DIKENAL JAHAT", "note": "catatan"}[kn["tag"]], (" - " + kn["label"]) if kn["label"] else ""))
    a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis." % (rep["score"], rep["level"]))
    for x in rep["why"][:8]:
        a("   * " + x)
    if len(rep["why"]) > 8:
        a("   (+%d alasan lain di laporan penuh)" % (len(rep["why"]) - 8))
    if rep.get("balance"):
        a("Penyeimbang (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + "; ".join(rep["balance"][:5]))
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][:6]:
            a("   ! " + x)
        if len(rep["warn"]) > 6:
            a("   (+%d peringatan lain di laporan penuh)" % (len(rep["warn"]) - 6))
    ind = rep["ind"]
    rows, folded, _co = _fold_caps(rep)
    if rows:
        a("Kemampuan (petunjuk): " + "; ".join(_cap_text(ind, cap, keep) for cap, keep, _f in rows[:5]))
    bits = ["SHA-256 " + rep["sha256"], "entropi %.2f" % rep["entropy"]]
    a(" | ".join(bits))
    pe = rep.get("pe")
    cnt: list[str] = []
    if pe and not pe.get("broken"):
        cnt.append("import %d fungsi / %d DLL" % (sum(len(v) for v in pe["imports"].values()), len(pe["imports"])))
        cnt.append("%d bagian" % len(pe["sections"]))
    for lab, key in (("URL", "urls"), ("IP", "ips"), ("email", "emails"), ("registry", "reg"), ("path", "paths")):
        if ind[key]:
            cnt.append("%d %s" % (len(ind[key]), lab))
    cnt.append("%d string" % ind["n_strings"])
    a("Dilipat: " + ", ".join(cnt) + ". Minta laporan penuh untuk rincian.")
    _ah = _assets_hint(rep)
    if _ah:
        a(_ah)
    if ind["urls"]:
        a("URL teratas: " + " | ".join(_df(u, defang) for u in ind["urls"][:3]))
    return "\n".join(L)



# ---------------------------------------------------------------------------
# Cache hasil per SHA-256 (23 Nov 2026). Triase berkas besar bisa makan belasan detik padahal hasilnya selalu sama untuk isi yang sama.
# Aturan keamanan / kebenaran:
#   - berkas SELALU dibuka dulu lewat _open_regular (FIFO / perangkat / folder / symlink tetap ditolak); cache tidak pernah melewati cek itu;
#   - kunci = SHA-256 ISI berkas (nama berkas tidak ikut; nama dipasang ulang saat cache terpakai) + tag (fuzzy / RE Lab);
#   - entri hanya dipakai bila sidik jari KODE (mtime + ukuran rea_triage.py), VERSION, dan daftar REA_KNOWN_HASHES sama dengan saat disimpan,
#     jadi mengedit kode atau daftar hash otomatis membuat cache lama tidak terpakai;
#   - hanya JSON (tidak pernah pickle), dibaca dengan validasi; rusak / kedaluwarsa / tidak cocok = diabaikan, hitung ulang;
#   - entri disimpan HANYA bila hasil dibaca-balik dari JSON menghasilkan laporan yang identik (render 4 mode, kartu, IOC), jadi cache tidak
#     pernah mengubah keluaran; bila tidak identik, tidak disimpan;
#   - gagal menulis / membaca cache tidak pernah menggagalkan triase (best-effort); tulis atomik (berkas sementara + os.replace);
#   - hanya berkas bernama <sha256>-<tag>.json di folder cache yang pernah dibaca / dihapus / dipangkas (REA_CACHE_DIR salah arah tidak berbahaya).
# Pengaturan: env REA_CACHE=0 (matikan), REA_CACHE_DIR=FOLDER (default: rea-reports/.cache di samping berkas ini), CLI --no-cache / --cache-info /
# --cache-clear, API {"action": "triage", "nocache": true} untuk memaksa hitung ulang dan {"action": "cache"} untuk info.
# ---------------------------------------------------------------------------

CACHE_FORMAT = 1
CACHE_MAX_FILES = 500                    # jumlah entri maksimum; yang paling lama tak terpakai dibuang dulu
CACHE_MAX_BYTES = 128 * 1024 * 1024      # total ukuran maksimum folder cache
CACHE_MAX_ENTRY = 8 * 1024 * 1024        # satu entri lebih besar dari ini tidak disimpan
CACHE_TTL_DAYS = 30.0                    # entri lebih tua dari ini tidak dipakai (laporan memuat perbandingan dengan waktu sekarang)
_CACHE_STATE: dict = {"pruned": 0.0, "code": None}
_CACHE_NAME = re.compile(r"[0-9a-f]{64}-(?:t0|t1|re)\.json")
_CACHE_TMP = re.compile(r"[0-9a-f]{64}-(?:t0|t1|re)\.json\.[0-9a-f]{12}\.tmp")


def _cache_dir():
    """Folder cache, atau None bila dimatikan (REA_CACHE=0 / off / false / no)."""
    if os.environ.get("REA_CACHE", "").strip().lower() in ("0", "off", "false", "no", "tidak"):
        return None
    d = os.environ.get("REA_CACHE_DIR", "").strip()
    return Path(d) if d else Path(__file__).resolve().parent / "rea-reports" / ".cache"


def _cache_stamp() -> dict:
    """Sidik jari yang harus sama agar entri boleh dipakai: format cache, VERSION, kode modul ini, dan berkas REA_KNOWN_HASHES."""
    code = _CACHE_STATE["code"]
    if code is None:
        try:
            code = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()[:32]   # hash ISI kode (bukan mtime + ukuran)
        except OSError:
            code = "?"
        _CACHE_STATE["code"] = code
    known = ""
    kp = os.environ.get("REA_KNOWN_HASHES", "")
    if kp:
        try:
            st = os.stat(kp)
            known = "%s:%d:%d" % (kp, st.st_mtime_ns, st.st_size)
        except OSError:
            known = kp + ":-"
    return {"fmt": CACHE_FORMAT, "ver": VERSION, "code": code, "known": known}


def _sha256_of(f, size: int) -> str | None:
    """SHA-256 dari paling banyak `size` byte pertama (sama dengan yang dihitung _hash_file). Posisi baca dikembalikan ke 0."""
    h = hashlib.sha256()
    try:
        f.seek(0)
        left = size
        while left > 0:
            chunk = f.read(min(1024 * 1024, left))
            if not chunk:
                break
            h.update(chunk)
            left -= len(chunk)
        f.seek(0)
    except OSError:
        return None
    return h.hexdigest()


_CACHE_KEY: dict = {"k": None}


def _cache_key() -> bytes | None:
    """Kunci HMAC cache: env REA_CACHE_KEY, atau berkas ~/.rea_cache_key (dibuat 0600). Sengaja DI LUAR folder cache, supaya
    penulis folder cache tidak otomatis bisa memalsukan entri. None = tak ada kunci (cache dimatikan, aman)."""
    if _CACHE_KEY["k"] is not None:
        return _CACHE_KEY["k"] or None
    key = b""
    try:
        e = os.environ.get("REA_CACHE_KEY", "").strip()
        if e:
            key = hashlib.sha256(e.encode("utf-8")).digest()
        else:
            kp = Path.home() / ".rea_cache_key"
            if kp.is_file():
                key = kp.read_bytes()[:64]
            if len(key) < 32:
                key = os.urandom(32)
                fd = os.open(str(kp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "wb") as fh:
                    fh.write(key)
    except Exception:
        key = b""
    _CACHE_KEY["k"] = key
    return key or None


def _cache_mac(text: str) -> str:
    import hmac
    k = _cache_key()
    return hmac.new(k, text.encode("utf-8"), hashlib.sha256).hexdigest() if k else ""


def _cache_path(sha: str, tag: str):
    d = _cache_dir()
    if d is None or not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
        return None
    return d / ("%s-%s.json" % (sha, tag))


def _cache_load(sha: str, tag: str):
    """Isi (dict) bila entri ada dan sah; selain itu None. Tidak pernah melempar."""
    p = _cache_path(sha, tag)
    if p is None:
        return None
    try:
        if p.stat().st_size > CACHE_MAX_ENTRY:
            return None
        with open(p, "r", encoding="utf-8") as fh:
            wrap = json.load(fh)
        import hmac
        if not isinstance(wrap, dict) or not isinstance(wrap.get("body"), str) or not isinstance(wrap.get("mac"), str):
            return None
        good_mac = _cache_mac(wrap["body"])
        if not good_mac or not hmac.compare_digest(good_mac, wrap["mac"]):
            return None             # entri dipalsukan / dibuat tanpa kunci ini: abaikan, hitung ulang
        obj = json.loads(wrap["body"])
        if (not isinstance(obj, dict) or obj.get("stamp") != _cache_stamp() or obj.get("sha256") != sha or obj.get("tag") != tag
                or not isinstance(obj.get("data"), dict) or time.time() - float(obj.get("ts", 0)) > CACHE_TTL_DAYS * 86400):
            return None
        data = obj["data"]
        if tag != "re" and (data.get("sha256") != sha or not isinstance(data.get("ind"), dict) or "kind" not in data or "score" not in data):
            return None
        try:
            os.utime(p, None)          # tandai baru dipakai (untuk pemangkasan LRU)
        except OSError:
            pass
        return data
    except Exception:
        return None


def _cache_store(sha: str, tag: str, data: dict, verify) -> bool:
    """Simpan `data` bila verify(hasil-baca-balik) benar. Tidak pernah melempar. True bila tersimpan."""
    p = _cache_path(sha, tag)
    if p is None:
        return False
    tmp = None
    try:
        text = json.dumps({"stamp": _cache_stamp(), "sha256": sha, "tag": tag, "ts": time.time(), "data": data},
                          ensure_ascii=False, default=str, separators=(",", ":"))
        if len(text) > CACHE_MAX_ENTRY or not verify(json.loads(text)["data"]):
            return False
        mac = _cache_mac(text)
        if not mac:
            return False            # tanpa kunci tidak menyimpan
        text = json.dumps({"mac": mac, "body": text}, ensure_ascii=False, separators=(",", ":"))
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name("%s.%s.tmp" % (p.name, os.urandom(6).hex()))   # unik per panggilan: aman untuk beberapa thread / proses
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, p)
        tmp = None
        _cache_prune()
        return True
    except Exception:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return False


def _cache_prune(force: bool = False) -> None:
    """Buang entri kedaluwarsa, lalu yang paling lama tak terpakai bila melebihi batas jumlah / ukuran. Paling sering sekali per menit."""
    now = time.time()
    if not force and now - _CACHE_STATE["pruned"] < 60:
        return
    _CACHE_STATE["pruned"] = now
    d = _cache_dir()
    if d is None:
        return
    ents = []
    try:
        for e in os.scandir(d):
            if not e.is_file(follow_symlinks=False):
                continue
            st = e.stat(follow_symlinks=False)
            if _CACHE_TMP.fullmatch(e.name):
                if now - st.st_mtime > 3600:
                    os.unlink(e.path)
            elif _CACHE_NAME.fullmatch(e.name):
                ents.append((st.st_mtime, st.st_size, e.path))
        ents.sort()
        n, total = len(ents), sum(x[1] for x in ents)
        for mt, sz, path in ents:
            if now - mt > CACHE_TTL_DAYS * 86400 or n > CACHE_MAX_FILES or total > CACHE_MAX_BYTES:
                os.unlink(path)
                n, total = n - 1, total - sz
            else:
                break
    except OSError:
        pass


def cache_info() -> dict:
    """Ringkasan folder cache: aktif / tidak, lokasi, jumlah entri, total byte, umur entri tertua (hari)."""
    d = _cache_dir()
    info: dict = {"enabled": d is not None, "dir": str(d) if d else "", "files": 0, "bytes": 0, "oldest_days": 0.0,
                  "max_files": CACHE_MAX_FILES, "max_bytes": CACHE_MAX_BYTES, "ttl_days": CACHE_TTL_DAYS}
    if d is None:
        return info
    now, oldest = time.time(), 0.0
    try:
        for e in os.scandir(d):
            if e.is_file(follow_symlinks=False) and _CACHE_NAME.fullmatch(e.name):
                st = e.stat(follow_symlinks=False)
                info["files"] += 1
                info["bytes"] += st.st_size
                oldest = max(oldest, now - st.st_mtime)
    except OSError:
        pass
    info["oldest_days"] = round(oldest / 86400, 1)
    return info


def cache_clear() -> int:
    """Hapus semua entri cache (hanya berkas bernama <sha256>-<tag>.json dan sisa .tmp-nya). Mengembalikan jumlah yang dihapus."""
    d = _cache_dir()
    n = 0
    if d is None:
        return 0
    try:
        for e in os.scandir(d):
            if e.is_file(follow_symlinks=False) and (_CACHE_NAME.fullmatch(e.name) or _CACHE_TMP.fullmatch(e.name)):
                try:
                    os.unlink(e.path)
                    n += 1
                except OSError:
                    pass
    except OSError:
        pass
    return n


def cache_text() -> str:
    i = cache_info()
    if not i["enabled"]:
        return "Cache triase: MATI (REA_CACHE=0)."
    return "Cache triase: aktif | %s | %d entri, %s | tertua %.1f hari | batas %d entri / %s / %.0f hari" % (
        i["dir"], i["files"], _human(i["bytes"]), i["oldest_days"], i["max_files"], _human(i["max_bytes"]), i["ttl_days"])


def _verify_triage(rep: dict, back: dict) -> bool:
    """Laporan dari hasil baca-balik JSON harus identik di semua mode keluaran; kalau tidak, jangan di-cache."""
    try:
        for compact in (False, True):
            for defang in (True, False):
                if render(rep, compact=compact, defang=defang) != render(back, compact=compact, defang=defang):
                    return False
        if render(rep, card=True) != render(back, card=True):
            return False
        return json.dumps(iocs(rep), sort_keys=True, default=str) == json.dumps(iocs(back), sort_keys=True, default=str)
    except Exception:
        return False


def _verify_relab(info: dict, back: dict) -> bool:
    try:
        for compact in (False, True):
            for defang in (True, False):
                a: list[str] = []
                b: list[str] = []
                _render_v98({"relab": info}, a.append, compact, defang)
                _render_v98({"relab": back}, b.append, compact, defang)
                if a != b:
                    return False
        return True
    except Exception:
        return False


def triage(path, follow_links: bool = True, fuzzy: bool = True, use_cache: bool = True) -> dict:
    """Triase penuh. Hasil ber-cache per SHA-256 isi berkas (lihat blok cache di atas); rep["cached"] = True bila diambil dari cache.
    use_cache=False memaksa hitung ulang (dan memperbarui cache)."""
    p = Path(path)
    f, size = _open_regular(p, follow_links)
    with f:
        tag = "t1" if fuzzy else "t0"
        sha = _sha256_of(f, size) if _cache_dir() is not None else None
        if sha and use_cache:
            hit = _cache_load(sha, tag)
            if hit is not None:
                hit["name"] = p.name
                hit["cached"] = True
                return hit
        rep = _triage_open(p, f, size, fuzzy)
        if sha:
            _cache_store(rep.get("sha256") or sha, tag, rep, lambda back: _verify_triage(rep, back))
        rep["cached"] = False
        return rep


def _common_dll(n: str) -> bool:
    n = n.lower()
    return n in _COMMON_DLLS or n.startswith(("api-ms-win-", "vcruntime", "msvcp"))


_COMMON_DLLS = frozenset({"kernel32.dll", "user32.dll", "gdi32.dll", "advapi32.dll", "shell32.dll", "shlwapi.dll", "ole32.dll", "oleaut32.dll",
                          "comctl32.dll", "comdlg32.dll", "crypt32.dll", "msvcrt.dll", "ucrtbase.dll", "version.dll", "winmm.dll", "imm32.dll",
                          "uxtheme.dll", "dwmapi.dll", "ws2_32.dll", "bcrypt.dll", "secur32.dll", "setupapi.dll", "rpcrt4.dll"})


def _balance(rep: dict) -> list[str]:
    """Fakta terukur yang lazim pada file sah. Hanya INFORMASI untuk pembaca skor: tidak mengurangi skor dan BUKAN jaminan aman
    (malware juga bisa bertanda tangan atau berinfo versi palsu)."""
    out: list[str] = []
    kn = rep.get("known")
    if kn and kn["tag"] == "good":
        out.append("hash ada di daftar lokal 'good'%s" % ((": " + kn["label"]) if kn["label"] else ""))
    pe = rep.get("pe")
    if not pe or pe.get("broken"):
        return out
    ver = pe.get("ver") or {}
    if all(ver.get(k) for k in ("CompanyName", "FileDescription", "FileVersion", "ProductName")):
        out.append("info versi lengkap")
    ac_ = rep.get("authenticode")
    if pe.get("signed") and pe.get("cert_extra", 0) <= 16 and not (ac_ and ac_.get("match") is False):
        if ac_ and ac_.get("match"):
            out.append("digest Authenticode cocok dengan isi file (rantai sertifikat dan pencabutan belum diverifikasi)")
        else:
            out.append("ada tanda tangan Authenticode (keabsahan belum diverifikasi)")
    note = ((rep.get("relab") or {}).get("entry_stub") or {}).get("note", "")
    if (pe.get("entry_sec") or "").lower() in (".text", "text", ".code", "code") and ("jalur normal" in note or "kompilator biasa" in note):
        out.append("entry normal: bagian %s, %s" % (pe["entry_sec"], note.split(" (")[0]))
    imps = pe.get("imports") or {}
    n_imp = sum(len(v) for v in imps.values())
    if imps and n_imp >= 8 and all(_common_dll(k) for k in imps) and not _cap_strong(rep["ind"], "injeksi / manipulasi proses"):
        out.append("import %d fungsi dari %d DLL sistem umum, tanpa API injeksi" % (n_imp, len(imps)))
    if pe.get("aslr") and pe.get("dep"):
        out.append("ASLR + DEP aktif")
    if not pe.get("overlay") and not any(x["flags"][1:] == "WX" for x in pe["sections"]):
        out.append("tanpa overlay dan tanpa bagian W+X")
    ck = rep.get("checksum")
    if ck and ck[2]:
        out.append("checksum header PE cocok")
    return out


def _triage_open(p: Path, f, size: int, fuzzy: bool = True) -> dict:
    rep: dict = {"name": p.name, "size": size, "warn": []}
    rep.update(_hash_file(f, size))
    f.seek(0)
    d = f.read(MAX_SCAN)
    rep["truncated"] = size > len(d)
    rep["entropy"] = _entropy(d[:ENT_SAMPLE])

    api_names: set[str] = set()
    pe = elf = zp = None
    try:
        pe = _parse_pe(d, size)
    except Exception as e:   # parser tidak boleh menjatuhkan /rea
        rep["warn"].append("parser PE gagal: %s" % type(e).__name__)
    if pe is None:
        try:
            elf = _parse_elf(d)
        except Exception:
            elf = None
    if pe is None and elf is None:
        try:
            zp = _parse_zip(f, size)
        except Exception as e:
            rep["warn"].append("parser ZIP gagal: %s" % type(e).__name__)
    mo = None
    if pe is None and elf is None and zp is None:   # v97: Mach-O (tipis / universal)
        try:
            mo = _parse_macho(d)
        except Exception as e:
            rep["warn"].append("parser Mach-O gagal: %s" % type(e).__name__)

    head = d[:16]
    if pe and not pe.get("broken"):
        kind = "PE%s %s (%s)" % ("32+" if pe["bits"] == 64 else "32", "DLL" if pe["dll"] else "executable", pe["subsys"])
        kind += ", " + pe["arch"] + (", .NET (managed)" if pe["dotnet"] else ", native")
        for fns in pe["imports"].values():
            api_names.update(fns)
        api_names.update(pe["exports"])
        for fns_ in (pe.get("delay_imports") or {}).values():
            api_names.update(fns_)
    elif pe:
        kind = "MZ/DOS (%s)" % pe["broken"]
    elif elf:
        kind = "ELF%d %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"])
    elif zp:
        kind = zp["kind"]
    elif mo:
        kind = "Mach-O%s (%s, %d-bit, %s)" % (" universal" if len(mo["fat"]) > 1 else "", mo["arch"], mo["bits"], mo["type"])
    elif head[:4] in (b"\xca\xfe\xba\xbe",):
        kind = "Java class atau Mach-O fat binary"
    elif head[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce"):
        kind = "Mach-O"
    elif head[:4] == b"dex\n":
        kind = "Android DEX"
    elif head[:4] == b"\0asm":
        kind = "WebAssembly"
    elif head[:6] == b"7z\xbc\xaf\x27\x1c":
        kind = "arsip 7-Zip (isi tidak diurai di sini)"
    elif head[:4] == b"Rar!":
        kind = "arsip RAR (isi tidak diurai di sini)"
    elif head[:2] == b"\x1f\x8b":
        kind = "gzip"
    elif head[:4] == b"%PDF":
        kind = "PDF"
    elif head[:2] == b"#!":
        kind = "skrip dengan shebang"
    elif head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        kind = "OLE2 (dokumen Office lama / MSI)"
    elif head[:5] == b"{\\rtf":
        kind = "RTF"
    elif head[:4] == b"L\0\0\0" and d[4:20] == b"\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46":
        kind = "Shortcut Windows (.lnk)"
    elif head[:8] == b"\x89PNG\r\n\x1a\n":
        kind = "gambar PNG"
    elif head[:3] == b"\xff\xd8\xff":
        kind = "gambar JPEG"
    elif head[:6] in (b"GIF87a", b"GIF89a"):
        kind = "gambar GIF"
    elif head[:4] == b"DDS ":
        kind = "tekstur DDS"
    elif head[:4] == b"glTF" and d[4:8] == b"\x02\x00\x00\x00":
        kind = "model 3D glTF biner (GLB)"
    elif head[:16] == b"SQLite format 3\x00":
        kind = "database SQLite"
    elif head[:4] == b"RIFF" and d[8:12] == b"WAVE":
        kind = "audio WAV (RIFF)"
    elif head[:4] == b"OggS":
        kind = "audio OGG"
    elif head[:4] in (b"IWAD", b"PWAD"):
        kind = "paket game WAD"
    elif head[:4] == b"PACK" and len(d) >= 12 and 12 <= struct.unpack_from("<I", d, 4)[0] <= size and struct.unpack_from("<I", d, 8)[0] % 64 == 0:
        kind = "paket game Quake PAK"
    else:
        txt = sum(1 for b in d[:4096] if 9 <= b <= 13 or 32 <= b <= 126)
        kind = "teks / skrip" if d[:4096] and txt / len(d[:4096]) > 0.95 else "biner tak dikenal (tanpa magic number umum)"
    rep["kind"] = kind
    rep["pe"], rep["elf"], rep["zip"], rep["macho"] = pe, elf, zp, mo
    if mo:
        api_names.update(mo["imports"])
    if elf:   # v94: ELF dulu tanpa impor sama sekali
        try:
            ei = _elf_imports(d)
        except Exception:
            ei = {"needed": [], "imports": [], "exports": []}
        elf["dyn"] = ei
        api_names.update(ei["imports"])
        try:
            elf["hard"] = _elf_hardening(d, elf)   # v99.3 [B3]; kunci baru, aditif
        except Exception:
            elf["hard"] = None
    rep["com"] = None
    if pe is not None and not pe.get("broken"):
        try:
            cm = _com_artifacts(d, api_names)   # v99.6 [A3]; kunci baru, aditif
            rep["com"] = cm
            for g in cm["groups"]:
                if g["group"] in _COM_NOTE_GROUPS:
                    rep["warn"].append("COM: %s (%s)%s" % (g["group"], ", ".join(g["names"][:2]), (" - " + g["note"]) if g["note"] else ""))
        except Exception as e:
            rep["warn"].append("pemindai COM gagal: %s" % type(e).__name__)
    rep["docs"] = None
    if pe is None and elf is None and zp is None and mo is None:
        try:
            rep["docs"] = _parse_docs(d, kind)
        except Exception as e:
            rep["warn"].append("parser dokumen gagal: %s" % type(e).__name__)

    rep["dotnet"] = None
    if pe and not pe.get("broken") and pe.get("dotnet"):   # v97: metadata .NET
        try:
            rep["dotnet"] = _dotnet_info(d, pe)
        except Exception as e:
            rep["warn"].append("parser metadata .NET gagal: %s" % type(e).__name__)
    cs_ = (pe.get("cert_spans") or []) if (pe and not pe.get("broken")) else []
    if cs_:   # blok PKCS#7 tanda tangan tidak ikut diekstraksi: isinya URL CRL / OCSP penerbit + sisa byte, bukan IOC file ini
        strs, pos_ = [], 0
        for a_, b_ in cs_:
            strs += _strings(d[pos_:a_])
            pos_ = b_
        strs += _strings(d[pos_:])
    else:
        strs = _strings(d)
    if rep["dotnet"]:
        strs += rep["dotnet"]["us"]
    if zp:
        blob = zp.pop("_blob", b"")
        if blob:
            strs += _strings(blob)
    vq_: set = set()
    if pe and not pe.get("broken"):
        for x_ in pe.get("res", []):
            vq_.update(x_.get("vquads", ()))
    rep["ind"] = _indicators(strs, api_names, vq_)
    if rep["dotnet"]:
        for cap_, hit_ in _net_caps(rep["dotnet"]["names"]).items():
            rep["ind"]["caps"][cap_] = list(dict.fromkeys(rep["ind"]["caps"].get(cap_, []) + hit_))[:8]
            if cap_ in rep["ind"]["caps_weak"]:   # nama yang kini terbukti dari metadata .NET tidak lagi lemah
                rep["ind"]["caps_weak"][cap_] = [n_ for n_ in rep["ind"]["caps_weak"][cap_] if n_ not in hit_]

    w = rep["warn"]
    if pe and pe.get("pwarn"):
        w.extend(pe["pwarn"])
    if (pe and pe.get("budget_hit")) or (elf and elf.get("budget_hit")):
        w.append("batas kerja entropi / hash bagian tercapai (header bagian tumpang-tindih atau dibuat-buat); sebagian nilai dikosongkan")
    if rep["entropy"] > 7.2 and not zp:   # arsip zip wajar berentropi tinggi
        w.append("entropi tinggi (%.2f): terkompres, terenkripsi, atau dikemas (packer)" % rep["entropy"])
    if pe and not pe.get("broken"):
        names = [s["name"].lower() for s in pe["sections"]]
        hit = [n for n in names if n in _PACKERS]
        if hit:
            w.append("nama bagian khas packer: " + ", ".join(hit))
        for s in pe["sections"]:
            if s["flags"] == "RWX" or (s["flags"][1:] == "WX"):
                w.append("bagian %s dapat ditulis DAN dieksekusi (W+X)" % s["name"])
            if s["ent"] > 7.2 and s["rsize"] > 4096:
                w.append("bagian %s berentropi %.2f (kemungkinan data terkompres/terenkripsi)" % (s["name"], s["ent"]))
        if not pe["dotnet"] and sum(len(v) for v in pe["imports"].values()) < 8 and size > 50000:
            w.append("import sangat sedikit untuk file sebesar ini (ciri packer atau resolusi API dinamis)")
        if not pe["signed"]:
            w.append("tidak ada tanda tangan digital Authenticode")
        elif pe.get("cert_extra", 0) > 16:
            w.append("tabel sertifikat Authenticode memuat %s byte tak berstruktur setelah blok PKCS#7 (data bisa diselipkan di sana tanpa merusak tanda tangan)" % _human(pe["cert_extra"]))
        if pe["ts"] == 0:
            w.append("timestamp kompilasi 0 (build reproducible atau dihapus)")
        elif pe["ts"] > _dt.datetime.now(_dt.timezone.utc).timestamp() + 86400:
            w.append("timestamp kompilasi di masa depan (dipalsukan atau jam salah)")
        if not pe["aslr"] and pe["bits"] == 32 and not pe["dll"]:
            w.append("ASLR tidak aktif")
        if pe["overlay"] > 65536:
            w.append("ada data tambahan (overlay) %s setelah bagian terakhir" % _human(pe["overlay"]))
    if zp:
        w.extend(zp["warn"])
    if rep["ind"]["pem"]:
        w.append("ada blok PRIVATE KEY tertanam")
    if rep["ind"]["secrets"] or rep["ind"].get("secrets_typed"):
        w.append("kandidat kredensial tertanam (nilai disamarkan di laporan)")
    nt_ = rep["ind"].get("net") or {}
    if nt_.get("pipes_flag"):
        w.append("named pipe bernama mirip alat pasca-eksploitasi / eksekusi jarak jauh: " + "; ".join(nt_["pipes_flag"][:3]))
    if nt_.get("certs"):
        w.append("%d sertifikat PEM tertanam (bisa pinning C2, MITM, atau bundel CA)" % nt_["certs"])
    if nt_.get("dns"):
        w.append("label DNS panjang ter-encode (kandidat DNS tunneling / DGA): " + ", ".join(nt_["dns"][:2]))

    # --- tambahan v92: struktur lanjutan, PE tertanam, penanda pembuat / pengemas, skor
    rep["emb"] = _embedded(d, bool(pe and not pe.get("broken"))) if not zp else {"plain": [], "xor": []}
    rep["overlay"], rep["checksum"], rep["crypto"] = None, None, []
    rep["authenticode"], rep["signer_match"], rep["xor_multi"] = None, None, []
    try:
        rep["known"] = _known_lookup(rep)
    except Exception:
        rep["known"] = None
    try:
        if pe and not pe.get("broken"):
            rep["overlay"] = _overlay_info(d, pe)
            rep["checksum"] = _pe_checksum_check(d, size)
            rep["authenticode"] = _authenticode_check(d, size, pe)
            rep["signer_match"] = _signer_vs_company(pe)
        rep["crypto"] = _crypto_consts(d)
    except Exception as e:
        w.append("analisis tambahan gagal: %s" % type(e).__name__)
    if rep["crypto"]:
        cp_ = rep["ind"]["caps"].setdefault("kripto", [])
        for nm_ in rep["crypto"]:
            if not nm_.startswith("tabel Base64") and nm_ not in cp_:
                cp_.append(nm_)
        if cp_:
            rep["ind"]["caps"]["kripto"] = cp_[:8]
        else:
            rep["ind"]["caps"].pop("kripto", None)
    ov_ = rep["overlay"]
    if ov_ and ov_["type"] != "data":
        w.append("overlay berisi %s di offset 0x%X (%s)" % (ov_["type"], ov_["off"], _human(ov_["size"])))
    ck_ = rep["checksum"]
    if ck_ and not ck_[2]:
        w.append("checksum header PE tidak cocok (tersimpan 0x%X, hitungan 0x%X): file diubah setelah build atau alat tidak memperbarui checksum" % (ck_[0], ck_[1]))
    ac_ = rep.get("authenticode")
    if ac_ and ac_.get("match") is False:
        w.append("tanda tangan Authenticode: digest %s di blob (%s...) beda dari hash isi file (%s...): file diubah setelah ditandatangani (atau penandatangan memakai cara hash khusus)" % (ac_["alg"], ac_["signed"][:16], ac_["computed"][:16]))
    for _n, t_ in ((rep.get("docs") or {}).get("score") or [])[:6]:
        w.append("dokumen: " + t_)
    skip_: list = []
    if pe and not pe.get("broken"):   # resource PNG / JPEG / ZIP utuh dan blok PKCS#7 memang tampak acak: jangan dihitung
        skip_ = [(x["off"], x["off"] + x["size"]) for x in pe.get("res", []) if x.get("fmt") and x.get("fmt_ok")] + list(pe.get("cert_spans") or [])
    rep["regions"] = _entropy_regions(d, skip_) if not zp else []
    rep["regions_masked"] = sum(b_ - a_ for a_, b_ in _merge_spans(skip_, len(d))) if skip_ else 0
    rep["tools"] = _toolchain(d, pe)
    if pe and not pe.get("broken"):
        if pe["entry"] and not pe["entry_sec"]:
            w.append("entry point (RVA 0x%X) tidak berada di bagian mana pun (ciri packer atau file rusak)" % pe["entry"])
        elif pe["entry_sec"] and pe["entry_sec"].lower() not in (".text", "text", ".code", "code", ".itext") and not pe["dotnet"]:
            w.append("entry point berada di bagian '%s', bukan bagian kode lazim" % pe["entry_sec"])
        if pe["tls"]:
            w.append("ada TLS callback: kode bisa jalan sebelum entry point (dipakai anti-debug, juga kompiler sah)")
        for x in pe.get("res", []):
            if x["mz"]:
                w.append("resource %s/%s berisi executable (MZ, %s) di offset 0x%X" % (x["type"], x["name"], _human(x["size"]), x["off"]))
            elif x.get("fmt") and not x.get("fmt_ok"):
                w.append("resource %s/%s berawalan %s tetapi kerangkanya tidak utuh (%s, entropi %.2f): bisa data tambahan / payload yang disamarkan" % (x["type"], x["name"], x["fmt"], _human(x["size"]), x["ent"]))
            elif x.get("fmt"):
                continue   # PNG / JPEG / ZIP utuh: tampak acak karena terkompres, bukan payload terenkripsi
            elif x["ent"] > 7.2 and x["size"] > 16384:
                w.append("resource %s/%s berentropi %.2f (%s): kemungkinan payload terenkripsi / terkompres" % (x["type"], x["name"], x["ent"], _human(x["size"])))
        for s_ in pe["sections"]:
            if s_["rsize"] == 0 and s_["vsize"] > 65536 and "X" in s_["flags"]:
                w.append("bagian %s: ukuran file 0 tetapi memori %s dan dapat dieksekusi (ruang untuk kode hasil unpack)" % (s_["name"], _human(s_["vsize"])))
    if elf:
        if elf["exec_stack"]:
            w.append("ELF: stack dapat dieksekusi (PT_GNU_STACK memuat flag X)")
        if elf["wx"]:
            w.append("ELF: ada " + ", ".join(elf["wx"][:3]) + " yang dapat ditulis DAN dieksekusi")
        if elf["nsec"] == 0 and elf["type"] != "relocatable (.o)":
            w.append("ELF tanpa tabel section (dihapus; umum pada kemasan UPX atau obfuskasi)")
        for x in elf["sections"]:
            if x["ent"] > 7.2 and x["size"] > 4096:
                w.append("ELF: section %s berentropi %.2f" % (x["name"] or "?", x["ent"]))
    if rep["emb"]["plain"]:
        w.append("PE tertanam polos di offset " + ", ".join("0x%X" % o for o in rep["emb"]["plain"][:5]))
    if rep["emb"]["xor"]:
        w.append("penanda DOS stub terenkode XOR (kunci 0x%02X di offset 0x%X): kemungkinan PE tersembunyi" % rep["emb"]["xor"][0])
    for kind_, info_ in rep["ind"]["b64d"]:
        if kind_ in ("PE/MZ", "ELF"):
            w.append(info_)
            break
    if rep["regions"] and not (pe and not pe.get("broken") and any(x["ent"] > 7.2 for x in pe["sections"])):
        a_, b_ = rep["regions"][0]
        w.append("wilayah berentropi tinggi di offset 0x%X-0x%X (%s)" % (a_, b_, _human(b_ - a_)))
    _v97_enrich(d, size, rep, fuzzy, f)
    _v98_enrich(d, rep)
    _capa_enrich(rep, api_names)
    _script_enrich(rep, strs)
    _layers_enrich(rep, d, strs)   # v99.9 [C2]; kunci baru rep["layers"], aditif
    _dso_enrich(rep, d, strs)      # v99.20 [A2]; kunci baru rep["deobf"], aditif
    _dexraw_enrich(rep, d)         # v99.11 [S1]; kunci baru rep["dex_code"], aditif
    _netil_enrich(rep, d)          # v99.12 [S1b]; kunci baru rep["dotnet_il"], aditif
    rep["icon"] = _icon_hash(d, pe)
    pts, level, why = _score(rep)
    rep["score"], rep["level"], rep["why"] = pts, level, why
    try:
        rep["balance"] = _balance(rep)
    except Exception:
        rep["balance"] = []
    return rep


_EXEC_EXTS = (".exe", ".dll", ".sys", ".scr", ".ocx", ".cpl", ".drv", ".efi")


def _bare_name(n: str) -> str:
    """Nama file untuk perbandingan dengan OriginalFilename: huruf kecil, tanpa awalan hash salinan rea-input, tanpa ekstensi executable."""
    n = re.sub(r"^[0-9a-f]{6}_", "", n.strip().lower())
    for e in _EXEC_EXTS:
        if n.endswith(e):
            return n[: -len(e)]
    return n


def _render(rep: dict, compact: bool = False, defang: bool = True, imp_detail: bool = True) -> str:
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("TRIASE LOKAL (dihitung Iris langsung dari bytes file; bukan klaim agen)")
    a("File   : %s | %s (%s B)" % (rep["name"], _human(rep["size"]), format(rep["size"], ",")))
    a("SHA-256: " + rep["sha256"])
    if not compact:
        a("SHA-1  : " + rep["sha1"])
    a("MD5    : " + rep["md5"])
    a("Jenis  : " + rep["kind"])
    kn_ = rep.get("known")
    if kn_:
        a("Daftar hash lokal (%s): %s%s" % (kn_["by"], {"good": "DIKENAL SAH", "bad": "DIKENAL JAHAT", "note": "catatan"}[kn_["tag"]], (" - " + kn_["label"]) if kn_["label"] else ""))
    if "score" in rep:
        a("Skor heuristik: %d (%s). Petunjuk dari fakta terukur, BUKAN vonis; installer / alat sah juga bisa bernilai tinggi." % (rep["score"], rep["level"]))
        for x in rep["why"][: (4 if compact else 20)]:
            a("   * " + x)
    if rep.get("balance"):
        a("Faktor penyeimbang (lazim pada file sah; BUKAN jaminan aman, tidak mengurangi skor): " + "; ".join(rep["balance"]))
    for label, hint in rep.get("tools", []):
        a("Terdeteksi: %s -> langkah lanjut (saran): %s" % (label, hint))
    a("Entropi: %.2f / 8.00%s" % (rep["entropy"], " (sampel %s pertama)" % _human(ENT_SAMPLE) if rep["size"] > ENT_SAMPLE else ""))
    if rep.get("truncated"):
        a("Catatan: file %s; string dan header dipindai dari %s pertama saja." % (_human(rep["size"]), _human(MAX_SCAN)))

    pe, elf, zp = rep.get("pe"), rep.get("elf"), rep.get("zip")
    if pe and not pe.get("broken"):
        a("PE     : %s %s | entry RVA 0x%X | compile %s | tanda tangan: %s | overlay: %s" % (
            pe["arch"], pe["subsys"], pe["entry"], pe["stamp"], "ada" if pe["signed"] else "tidak ada", _human(pe["overlay"])))
        a("Proteksi: ASLR %s, DEP %s, CFG %s" % tuple("ya" if x else "tidak" for x in (pe["aslr"], pe["dep"], pe["cfg"])))
        a("Entry  : bagian %s%s%s" % (pe["entry_sec"] or "(di luar semua bagian)", " | TLS callback ada" if pe["tls"] else "", " | delay-import ada" if pe["delay"] else ""))
        if pe.get("imphash") and not compact:
            a("Imphash: %s%s" % (pe["imphash"], " (ada %d impor ordinal; bisa beda dari pefile)" % pe["ord_imports"] if pe["ord_imports"] else ""))
        secs = pe["sections"][: (8 if compact else 20)]
        a("Bagian : " + "; ".join("%s %s ent %.1f%s raw %s" % (s["name"] or "?", s["flags"], s["ent"], "*" if s.get("masked") else "", _human(s["rsize"])) for s in secs))
        for s in secs:
            if s.get("masked"):
                a("   * entropi %s dihitung tanpa %s resource PNG / JPEG / ZIP utuh (mentah %.2f)" % (s["name"] or "?", _human(s["masked"]), s["ent_raw"]))
        if not compact:
            a("MD5 bagian: " + "; ".join("%s=%s" % (s["name"] or "?", s["md5"]) for s in secs if s.get("md5")))
        ver = pe.get("ver") or {}
        if ver:
            orig = ver.get("OriginalFilename", "")
            diff_ = bool(orig) and _bare_name(orig) != _bare_name(rep["name"])   # tanpa ekstensi: launcher == launcher.exe
            a("Versi  : " + "; ".join("%s=%s" % (k, v) for k, v in ver.items()) + (" | nama file BERBEDA dari OriginalFilename" if diff_ else ""))
        if pe.get("signers"):
            a("Tanda tangan: CN di blob sertifikat: %s (hanya dibaca, keabsahan TIDAK diverifikasi)" % ", ".join(pe["signers"][:4]))
        if pe.get("rich") and not compact:
            a("Rich   : hash %s, %d entri alat build (varian Iris)" % (pe["rich"]["hash"], pe["rich"]["n"]))
        resl = pe.get("res") or []
        if resl:
            grp: dict = {}
            for x in resl:
                g = grp.setdefault(x["type"], [0, 0, 0.0])
                g[0] += 1
                g[1] += x["size"]
                g[2] = max(g[2], x["ent"])
            top = sorted(grp.items(), key=lambda kv: -kv[1][1])[: (3 if compact else 8)]
            a("Resource: %d entri; " % len(resl) + "; ".join("%s x%d (%s, ent maks %.1f)" % (k, g[0], _human(g[1]), g[2]) for k, g in top))
            fm_: dict = {}
            for x in resl:
                if x.get("fmt") and x.get("fmt_ok"):
                    fm_[x["fmt"]] = fm_.get(x["fmt"], 0) + 1
            if fm_:
                a("   terkompres wajar (kerangka utuh, tidak dianggap payload): " + ", ".join("%s x%d" % kv for kv in fm_.items()))
        imps = pe["imports"]
        if imps:
            tot = sum(len(v) for v in imps.values())
            lim = 8 if compact else 30
            a("Import : %d DLL, %d fungsi: " % (len(imps), tot) + ", ".join("%s(%d)" % (k, len(v)) for k, v in list(imps.items())[:lim]))
            if not compact and imp_detail:
                for k, v in list(imps.items())[:30]:
                    a("   %s: %s" % (k, ", ".join(v[:40]) + (" …" if len(v) > 40 else "")))
        if pe["exports"]:
            a("Export : %d nama: %s" % (len(pe["exports"]), ", ".join(pe["exports"][: (10 if compact else 60)])))
        if pe.get("delay_imports"):
            di = pe["delay_imports"]
            a("Delay-import: %d DLL, %d fungsi: %s" % (len(di), sum(len(v) for v in di.values()), ", ".join("%s(%d)" % (k, len(v)) for k, v in list(di.items())[:8])))
        ov = rep.get("overlay")
        if ov:
            a("Overlay: %s di offset 0x%X, entropi %.2f, jenis %s%s" % (_human(ov["size"]), ov["off"], ov["ent"], ov["type"], (", sha256 " + ov["sha256"]) if ov.get("sha256") else ""))
        ck = rep.get("checksum")
        if ck and not ck[2]:
            a("Checksum header PE: tersimpan 0x%X, hitungan 0x%X (TIDAK cocok)" % (ck[0], ck[1]))
    elif pe:
        a("PE     : " + pe["broken"])
    if elf:
        a("ELF    : %d-bit %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"]))
        a("ELF+   : interpreter %s | %s | %d segmen, %d section | stack %s" % (
            elf["interp"] or "-", {True: "stripped (tanpa .symtab)", False: "ada simbol (.symtab)", None: "tabel section tak terbaca"}[elf["stripped"]],
            elf["nseg"], elf["nsec"], "dapat dieksekusi" if elf["exec_stack"] else "NX"))
        hd = elf.get("hard")
        if hd:
            a("ELF mitigasi: PIE %s | RELRO %s | NX %s | canary %s | FORTIFY %s%s" % (
                hd["pie"], hd["relro"], hd["nx"], "ada" if hd["canary"] else "tidak terdeteksi",
                ("%d fungsi *_chk" % hd["fortify"]) if hd["fortify"] else "tidak terdeteksi",
                (" | " + "; ".join(hd["rpath"])) if hd["rpath"] else ""))
        if elf["sections"]:
            a("Section: " + "; ".join("%s %s ent %.1f %s" % (x["name"] or "?", x["flags"], x["ent"], _human(x["size"])) for x in elf["sections"][: (8 if compact else 20)] if x["name"]))
    dyn = elf.get("dyn") if elf else None
    if dyn:
        if dyn["needed"]:
            a("ELF NEEDED (%d): %s" % (len(dyn["needed"]), ", ".join(dyn["needed"][:20])))
        if dyn["imports"]:
            a("ELF impor (%d): %s" % (len(dyn["imports"]), ", ".join(dyn["imports"][: (12 if compact else 60)])))
        if dyn["exports"] and not compact:
            a("ELF ekspor (%d): %s" % (len(dyn["exports"]), ", ".join(dyn["exports"][:40])))
    dc = rep.get("docs")
    if dc:
        a("Dokumen: " + dc["fmt"])
        for x in dc["info"][: (4 if compact else 14)]:
            a("   - " + x)
    if rep.get("crypto"):
        a("Konstanta algoritma terdeteksi (petunjuk, BUKAN bukti pemakaian): " + ", ".join(rep["crypto"]))
    if zp:
        a("Arsip  : %s, %d entri, %s tak terkompresi (rasio %.1fx)" % (zp["kind"], zp["n"], _human(zp["unc"]), zp.get("ratio", 0)))
        if zp.get("main"):
            a("Main-Class: " + zp["main"])
        if zp.get("dex"):
            a("DEX    : %d berkas classes*.dex" % zp["dex"])
        if zp.get("perms"):
            a("Izin Android (%d): %s" % (len(zp["perms"]), ", ".join(p.replace("android.permission.", "") for p in zp["perms"][: (10 if compact else 40)])))
        _render_apk(zp, a, compact, defang)
        if zp.get("nested"):
            a("Berkas tertanam menarik: " + ", ".join(zp["nested"][: (6 if compact else 25)]))
        risky = _risky_perms(zp.get("perms", []))
        if risky:
            a("Izin Android berisiko (%d): %s" % (len(risky), ", ".join(risky[: (4 if compact else 14)])))
        if zp.get("ext_rels"):
            a("Relasi eksternal dokumen: " + " | ".join(_df(x, defang) for x in zp["ext_rels"][:5]))
        if not compact:
            a("Isi (50 pertama): " + ", ".join(zp["names"]))

    ind = rep["ind"]
    if ind["caps"]:
        a("Indikasi kemampuan (petunjuk dari nama API/string, BUKAN bukti perilaku; installer sah juga memakainya):")
        rows_, folded_, crt_only_ = _fold_caps(rep)
        for cap, keep, _f in rows_:
            a("   - " + _cap_text(ind, cap, keep))
        if folded_:
            a("   (umum pada program MSVC / CRT, bukan indikasi niat: " + "; ".join("%s: %s" % (c_, ", ".join(h_)) for c_, h_ in folded_) + ")")
        if ind.get("caps_weak"):
            a("   (lemah = nama API hanya muncul sebagai teks, mis. dari runtime / tabel nama; tidak ikut skor, kecuali nama API injeksi)")
        if not compact:
            tt = [ATTACK[c] for c in ind["caps"] if c in ATTACK and _cap_strong(ind, c) and c not in crt_only_]
            if tt:
                a("Pemetaan ATT&CK (perkiraan dari petunjuk di atas, BUKAN bukti perilaku): " + "; ".join(tt))
    lim = 5 if compact else 25
    for label, key in (("URL", "urls"), ("Kandidat IP (bisa nomor versi)", "ips"), ("Email", "emails"), ("Kunci registry", "reg"), ("Path Windows", "paths")):
        if ind[key]:
            a("%s (%d): %s" % (label, len(ind[key]), " | ".join(_df(x, defang) if key in ("urls", "ips", "emails") else x for x in ind[key][:lim])))
    if ind["secrets"]:
        a("Kandidat kredensial tertanam (disamarkan): " + ", ".join(ind["secrets"]))
    nt = ind.get("net") or {}
    if any(nt.get(k) for k in ("ua", "http", "hosts", "hdrs", "dns", "proxy", "pipes", "certs")):
        lim_ = 3 if compact else 8
        if nt.get("ua"):
            a("User-Agent tertanam (%d): %s" % (len(nt["ua"]), " | ".join(nt["ua"][:lim_])))
        if nt.get("http"):
            a("Permintaan HTTP mentah: " + " | ".join(nt["http"][:lim_]))
        if nt.get("hosts"):
            a("Header Host: " + ", ".join(_df(x, defang) for x in nt["hosts"][:lim_]))
        if nt.get("hdrs") and not compact:
            a("Header HTTP lain: " + " | ".join(nt["hdrs"]))
        if nt.get("dns"):
            a("Label DNS ter-encode (kandidat): " + ", ".join(_df(x, defang) for x in nt["dns"][:lim_]))
        if nt.get("proxy"):
            a("Konfigurasi proxy: " + " | ".join(_df(x, defang) if "://" in x else x for x in nt["proxy"][:lim_]))
        if nt.get("pipes"):
            a("Named pipe (%d): %s" % (len(nt["pipes"]), ", ".join(nt["pipes"][:lim_])))
        if nt.get("certs"):
            a("Sertifikat PEM tertanam: %d" % nt["certs"])
    if ind.get("secrets_typed"):
        a("Rahasia berformat khusus (disamarkan): " + " | ".join(ind["secrets_typed"][:5 if compact else 12]))
    if ind.get("pdb"):
        a("Jejak PDB (nama proyek / path build pembuat): " + " | ".join(ind["pdb"]))
    if ind["b64"]:
        a("String mirip base64 panjang: %d%s" % (ind["b64"], " (%d berhasil didekode di bawah)" % len(ind["b64d"]) if ind.get("b64d") else " (tidak ada yang berupa executable / teks terbaca)"))
        for k_, v_ in ind.get("b64d", [])[: (3 if compact else 8)]:
            a("   - %s: %s" % (k_, _df(v_, defang) if k_ == "teks" else v_))
    emb = rep.get("emb") or {}
    if emb.get("plain"):
        a("PE tertanam polos di offset: " + ", ".join("0x%X" % o for o in emb["plain"]))
    if emb.get("xor"):
        a("Dugaan PE di-XOR: " + ", ".join("kunci 0x%02X @0x%X" % x for x in emb["xor"]))
    if rep.get("regions") and not compact:
        a("Wilayah berentropi tinggi (>7,2): " + ", ".join("0x%X-0x%X (%s)" % (x, y, _human(y - x)) for x, y in rep["regions"][:6])
          + (" [dihitung tanpa %s resource PNG / JPEG / ZIP utuh dan blok tanda tangan]" % _human(rep["regions_masked"]) if rep.get("regions_masked") else ""))
    _render_v986(rep, a, compact, defang)
    _render_v97(rep, a, compact, defang)
    _render_v98(rep, a, compact, defang)
    _render_capa(rep, a, compact)
    _render_decoded(rep, a, compact, defang)
    _render_layers(rep, a, compact, defang)
    _render_dso(rep, a, compact, defang)
    _render_dexcode(rep.get("dex_code"), a, compact, defang)
    _render_netil(rep.get("dotnet_il"), a, compact, defang)
    if rep.get("icon"):
        a("Ikon   : md5 utama %s (%d ikon; gabungan %s)" % (rep["icon"]["main"], rep["icon"]["n"], rep["icon"]["all"][:12]))
    a("String terbaca: %d" % ind["n_strings"])
    if rep["warn"]:
        a("PERHATIAN:")
        for x in rep["warn"][: (6 if compact else 20)]:
            a("   ! " + x)
    _ah = _assets_hint(rep)
    if _ah:
        a(_ah)
    a("Batas triase: hasil di atas murni pembacaan statis; tanpa dekompilasi, tanpa emulasi sistem (hanya emulasi mikro statis terbatas pada RE Lab), tanpa jaringan, file tidak dijalankan.")
    return "\n".join(L)


def render(rep: dict, compact: bool = False, defang: bool = True, max_chars: int = 0, card: bool = False) -> str:
    """Seperti dulu, plus anggaran panjang: bila melebihi max_chars, buang rincian impor per-DLL dulu, lalu pakai mode ringkas,
    terakhir pangkas bagian tengah. Skor dan PERHATIAN tidak ikut terbuang lebih dulu."""
    if card:
        txt = render_card(rep, defang)
        return txt if not max_chars or len(txt) <= max_chars else txt[:max_chars - 30] + "\n[...dipangkas supaya muat...]"
    txt = _render(rep, compact, defang)
    if not max_chars or len(txt) <= max_chars:
        return txt
    if not compact:
        txt = _render(rep, False, defang, imp_detail=False)
        if len(txt) <= max_chars:
            return txt
    txt = _render(rep, True, defang)
    if len(txt) <= max_chars:
        return txt
    head = int(max_chars * 0.6)
    tail = max(0, max_chars - head - 40)
    return txt[:head] + "\n[...dipangkas supaya muat...]\n" + (txt[-tail:] if tail else "")


def triage_text(path, compact: bool = False, defang: bool = True, max_chars: int = 0, card: bool = False) -> str:
    try:
        return render(triage(path), compact=compact, defang=defang, max_chars=max_chars, card=card)
    except Exception as e:
        return "TRIASE LOKAL gagal (%s: %s). Lanjutkan tanpa data ini." % (type(e).__name__, str(e)[:120])


def _pe_extent(buf: bytes) -> int:
    pe = _parse_pe(buf, len(buf))
    if pe and not pe.get("broken") and pe["sections"]:
        return max(x["rptr"] + x["rsize"] for x in pe["sections"]) or len(buf)
    return len(buf)


def carve(path, outdir, max_items: int = 8, rep: dict | None = None) -> list[dict]:
    """Keluarkan payload tertanam (PE polos, PE di-XOR, PE di base64, PE di resource) ke outdir sebagai <sha>.bin.
    Tidak pernah menjalankan apa pun. Peringatan: antivirus bisa mengarantina hasilnya."""
    p = Path(path)
    rep = rep or triage(path)
    f, fsize = _open_regular(p)
    with f:
        if _hash_file(f, fsize)["sha256"] != rep["sha256"]:
            raise OSError("berkas berubah sejak triase; ulangi /rea")
        f.seek(0)
        d = f.read(MAX_SCAN)
    cands: list[tuple[str, bytes]] = []
    cap = 16 * 1024 * 1024
    for off in (rep.get("emb") or {}).get("plain", []):
        chunk = d[off:off + cap]
        cands.append(("PE polos @0x%X" % off, chunk[:_pe_extent(chunk)]))
    for k, at in (rep.get("emb") or {}).get("xor", []):
        start = max(0, at - 0x4E)
        dec = d[start:start + cap].translate(bytes(i ^ k for i in range(256)))
        if dec[:2] == b"MZ":
            cands.append(("PE XOR 0x%02X @0x%X" % (k, start), dec[:_pe_extent(dec)]))
    for x in ((rep.get("pe") or {}).get("res") or []):
        if x.get("mz"):
            cands.append(("resource %s/%s" % (x["type"], x["name"]), d[x["off"]:x["off"] + min(x["size"], cap)]))
    try:
        for mm in itertools.islice(_B64.finditer("\n".join(_strings(d))), 60):
            m = mm.group(0)
            raw = base64.b64decode(m + "=" * (-len(m) % 4))
            if raw[:2] == b"MZ" and len(raw) >= 256:
                cands.append(("PE base64", raw[:_pe_extent(raw)]))
    except Exception:
        pass
    out: list[dict] = []
    seen: set[str] = set()
    od = Path(outdir)
    for src, blob in cands:
        if len(out) >= max_items or len(blob) < 256 or len(blob) > 64 * 1024 * 1024:
            continue
        sha = hashlib.sha256(blob).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        od.mkdir(parents=True, exist_ok=True)
        fp = od / (sha[:16] + ".bin")
        try:
            with open(fp, "xb") as f:
                f.write(blob)
        except FileExistsError:
            try:
                if hashlib.sha256(fp.read_bytes()).hexdigest() != sha:   # berkas lama bernama sama tapi isi lain: jangan klaim
                    continue
            except OSError:
                continue
        except OSError:
            continue
        item = {"file": str(fp), "sha256": sha, "size": len(blob), "source": src}
        try:
            sub = triage(str(fp))
            item["kind"], item["score"], item["level"] = sub["kind"], sub["score"], sub["level"]
        except Exception:
            pass
        out.append(item)
    return out


def _carved_text(items: list[dict]) -> str:
    L = ["", "PAYLOAD DIKELUARKAN (disalin sebagai .bin, TIDAK dijalankan; antivirus bisa mengarantina berkas ini):"]
    for it in items:
        L.append("   - %s | %s | sha256 %s | %s | skor %s (%s)\n     %s" % (_clean(it["source"]), _human(it["size"]), it["sha256"][:16] + "...",
                 _clean(str(it.get("kind", "?"))), it.get("score", "?"), _clean(str(it.get("level", "?"))), _clean(it["file"])))
    L.append("   Analisis tiap berkas ini dengan /rea cepat sebelum menyimpulkan apa pun.")
    return "\n".join(L)


def triage_bundle(path, max_chars: int = 5500, carve_dir=None) -> tuple[str, str]:
    """(laporan penuh, versi muat-anggaran untuk tugas agen). Satu kali hitung; gagal -> pesan, tidak melempar."""
    try:
        r = triage(path)
        extra = ""
        if carve_dir:
            try:
                items = carve(path, carve_dir, rep=r)
                if items:
                    extra = _carved_text(items)
            except Exception as e:
                extra = "\n(Pengeluaran payload gagal: %s)" % type(e).__name__
        return render(r) + extra, render(r, max_chars=max(1000, max_chars - len(extra))) + extra
    except Exception as e:
        msg = "TRIASE LOKAL gagal (%s: %s). Lanjutkan tanpa data ini." % (type(e).__name__, str(e)[:120])
        return msg, msg


_DIR_PRIO = (".exe", ".dll", ".sys", ".scr", ".so", ".apk", ".jar", ".dex", ".ps1", ".vbs", ".js", ".bat", ".cmd", ".hta", ".lnk",
             ".docm", ".xlsm", ".msi", ".bin", ".dat", ".elf")


def triage_dir(path, max_files: int = 300, per_file_mb: float = 200.0, time_budget: float = 90.0, fuzzy: bool = False) -> dict:
    root = Path(path)
    t0 = time.monotonic()
    found: list[Path] = []
    total_n, total_sz = 0, 0
    for dp, dn, fn in os.walk(root, followlinks=False):
        dn[:] = [x for x in dn if not _is_reparse(os.path.join(dp, x))]   # v94: junction Windows tidak dikenali is_symlink
        for f in fn:
            fp = Path(dp) / f
            try:
                if _is_reparse(fp) or not fp.is_file():
                    continue
                total_n += 1
                total_sz += fp.stat().st_size
                if total_n <= 20000:
                    found.append(fp)
            except OSError:
                continue
        if total_n > 20000:
            break

    def key(fp: Path):
        try:
            sz = fp.stat().st_size
        except OSError:
            sz = 0
        return (0 if fp.suffix.lower() in _DIR_PRIO else 1, -sz)

    found.sort(key=key)
    items: list[dict] = []
    skipped: list[str] = []
    for fp in found:
        if len(items) >= max_files or time.monotonic() - t0 > time_budget:
            skipped.append("batas %s tercapai" % ("jumlah berkas" if len(items) >= max_files else "waktu"))
            break
        rel = str(fp.relative_to(root)).replace("\\", "/")
        try:
            if fp.stat().st_size > per_file_mb * 1024 * 1024:
                skipped.append("%s (>%.0f MB)" % (rel, per_file_mb))
                continue
            if _is_reparse(fp):
                skipped.append("%s (berubah menjadi link)" % rel)
                continue
            r = triage(str(fp), follow_links=False, fuzzy=fuzzy)
        except Exception as e:
            skipped.append("%s (%s)" % (rel, type(e).__name__))
            continue
        items.append({"rel": rel, "size": r["size"], "kind": r["kind"], "score": r["score"], "level": r["level"], "sha256": r["sha256"],
                      "why": r["why"][:3], "urls": r["ind"]["urls"][:5], "ips": r["ind"]["ips"][:5],
                      "imphash": ((r.get("pe") or {}).get("imphash") or "") if not (r.get("pe") or {}).get("broken") else "",
                      "rich": ((r.get("pe") or {}).get("rich") or {}).get("hash", "") if not (r.get("pe") or {}).get("broken") else "",
                      "macho_uuid": (r.get("macho") or {}).get("uuid", ""), "ctph": r.get("ctph", ""),
                      "known": (r.get("known") or {}).get("tag", "")})
    by_hash: dict[str, list[str]] = {}
    for it in items:
        by_hash.setdefault(it["sha256"], []).append(it["rel"])
    return {"root": str(root), "n_total": total_n, "total_size": total_sz, "n_done": len(items), "items": items, "skipped": skipped[:10],
            "dups": [v for v in by_hash.values() if len(v) > 1][:10], "elapsed": time.monotonic() - t0,
            "families": _families(items, fuzzy)}


def render_dir(sm: dict, defang: bool = True, top: int = 15) -> str:
    L: list[str] = []
    a = lambda s_: L.append(_clean(s_))
    a("TRIASE FOLDER (dihitung Iris dari bytes; tiap berkas dibaca hanya-baca, tidak dijalankan)")
    a("Folder : %s | %d berkas, %s | dipindai %d dalam %.1f detik" % (sm["root"], sm["n_total"], _human(sm["total_size"]), sm["n_done"], sm["elapsed"]))
    kinds = collections.Counter(re.split(r"[,(]", it["kind"])[0].strip() for it in sm["items"])
    a("Jenis  : " + ", ".join("%s x%d" % kv for kv in kinds.most_common(8)))
    ranked = sorted(sm["items"], key=lambda it: (-it["score"], -it["size"]))
    if ranked:
        if ranked[0]["score"] > 0:
            a("Peringkat skor heuristik (petunjuk, BUKAN vonis):")
        for it in ranked[:top]:
            if it["score"] == 0:
                break
            a("   [%s %d] %s | %s | %s | sha256 %s..." % (it["level"], it["score"], it["rel"], re.split(r"[,(]", it["kind"])[0].strip(), _human(it["size"]), it["sha256"][:12]))
            if it["why"]:
                a("        " + "; ".join(it["why"]))
        if ranked[0]["score"] == 0:
            a("   Tidak ada berkas dengan tanda mencurigakan. Terbesar: " + ", ".join("%s (%s)" % (it["rel"], _human(it["size"])) for it in sorted(ranked, key=lambda x: -x["size"])[:5]))
    if sm["dups"]:
        a("Duplikat identik: " + " | ".join(" = ".join(g[:3]) for g in sm["dups"][:5]))
    for fm in sm.get("families", [])[:6]:
        a("Keluarga (%s): %s" % (fm["basis"], " | ".join(fm["members"][:4]) + (" ..." if len(fm["members"]) > 4 else "")))
    urls = _uniq((u for it in sm["items"] for u in it["urls"]), 12)
    ips = _uniq((u for it in sm["items"] for u in it["ips"]), 10)
    if urls:
        a("URL gabungan (%d): %s" % (len(urls), " | ".join(_df(u, defang) for u in urls[:8])))
    if ips:
        a("Kandidat IP gabungan: " + " | ".join(_df(u, defang) for u in ips[:8]))
    if sm["skipped"]:
        a("Dilewati: " + "; ".join(sm["skipped"][:5]))
    a("Langkah berikut: jalankan /rea cepat pada berkas peringkat teratas untuk rinciannya.")
    return "\n".join(L)


def triage_dir_text(path, max_chars: int = 0, defang: bool = True) -> str:
    try:
        txt = render_dir(triage_dir(path), defang=defang)
    except Exception as e:
        return "TRIASE FOLDER gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if max_chars and len(txt) > max_chars:
        txt = txt[: max_chars - 30] + "\n[...dipangkas supaya muat...]"
    return txt


def yara_draft(rep: dict, name: str = "") -> str:
    """Draf aturan YARA dari string unik berkas ini. WAJIB diuji terhadap file sah sebelum dipakai; bisa salah-deteksi."""
    ind = rep["ind"]
    cand = list(ind["urls"][:4]) + list(ind.get("pdb", [])[:2]) + list(ind["emails"][:2]) + list(ind["reg"][:2])
    for cap in ("penambang kripto", "pencurian kredensial / dompet", "string ala ransomware", "penghapus jejak / perusak pemulihan"):
        cand += ind["caps"].get(cap, [])[:3]
    cand = _uniq([c for c in cand if 6 <= len(c) <= 200], 10)
    rid = re.sub(r"[^A-Za-z0-9_]", "_", name or ("rea_" + rep["sha256"][:12]))
    if not rid or rid[0].isdigit():
        rid = "r_" + rid
    if len(cand) < 2:
        return "// Tidak cukup string unik untuk draf YARA yang layak (%d). Jangan membuat aturan dari satu string umum." % len(cand)
    esc = lambda x: x.replace("\\", "\\\\").replace('"', '\\"')
    L = ["rule %s {" % rid, "  meta:",
         '    description = "DRAF otomatis Iris rea_triage v93; WAJIB diuji terhadap file sah sebelum dipakai"',
         '    sha256 = "%s"' % rep["sha256"]]
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append('    // imphash varian Iris: %s' % pe["imphash"])
    L.append("  strings:")
    for i, c in enumerate(cand, 1):
        L.append('    $s%d = "%s" ascii wide nocase' % (i, esc(c)))
    magic = "uint16(0) == 0x5A4D and " if (pe and not pe.get("broken")) else ("uint32(0) == 0x464C457F and " if rep.get("elf") else "")
    need = "all of them" if len(cand) <= 2 else "%d of them" % min(3, len(cand))
    L += ["  condition:", "    %sfilesize < %d and %s" % (magic, max(rep["size"] * 2, 4096), need), "}"]
    return "\n".join(L)


def iocs(rep: dict) -> dict:
    """Indikator siap pakai (tanpa defang) untuk disalin ke blocklist, YARA, atau laporan."""
    ind, pe = rep["ind"], rep.get("pe")
    out = {"sha256": rep["sha256"], "sha1": rep["sha1"], "md5": rep["md5"], "urls": ind["urls"], "ips": ind["ips"],
           "emails": ind["emails"], "registry": ind["reg"], "pdb": ind.get("pdb", [])}
    out["ctph"] = rep.get("ctph", "")
    out["xor_urls"] = _uniq((u for x in rep.get("xor") or [] for u in x["urls"]), 10)
    if rep.get("macho"):
        out["macho_uuid"] = rep["macho"]["uuid"]
    if pe and not pe.get("broken"):
        out["imphash"] = pe.get("imphash", "")
        out["rich_hash"] = (pe.get("rich") or {}).get("hash", "")
        out["section_md5"] = {x["name"] or "?": x["md5"] for x in pe["sections"] if x.get("md5")}
        out["version_info"] = pe.get("ver", {})
    return out


_ASSET_KIND_PREFIX = ("biner tak dikenal", "gzip", "ZIP", "gambar", "tekstur", "model 3D", "database", "audio", "paket game")


def _assets_hint(rep: dict) -> str:
    """Petunjuk (bukan temuan): berkas non-executable yang isinya bisa dijelajahi Asset Explorer (rea_assets.py), bila modul itu ada."""
    if rep.get("pe") or rep.get("elf") or rep.get("macho"):
        return ""
    if not str(rep.get("kind", "")).startswith(_ASSET_KIND_PREFIX):
        return ""
    if _assets_mod() is None:
        return ""
    return "Asset Explorer tersedia untuk jenis ini: `python rea_triage.py --assets FILE` (isi) | `--assets-extract OUTDIR FILE` (ekstrak) | `--assets-carve FILE` (berkas tertanam)"


def triage_json(path, ioc_only: bool = False) -> str:
    try:
        rep = triage(path)
        return json.dumps(iocs(rep) if ioc_only else rep, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": "%s: %s" % (type(e).__name__, str(e)[:120])}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# v97: Mach-O, metadata .NET, CTPH (hash fuzzy), perburuan XOR / ADD / ROL, detail kemasan, keluarga sampel,
#      laporan Markdown, dan API JSON untuk Iris / Hermes. Semuanya hanya-baca, pustaka standar, file tidak dijalankan.
# ---------------------------------------------------------------------------

VERSION = "99.22"
AUTHOR = "KangJiho"

# nama impor Mach-O (garis bawah depan sudah dibuang) yang menandai manipulasi proses lain
EXACT_CAPS["injeksi / manipulasi proses"] = EXACT_CAPS["injeksi / manipulasi proses"] | {"task_for_pid", "mach_vm_write", "mach_vm_protect", "thread_create_running"}
STR_CAPS["macOS: persistensi / manipulasi sistem"] = ["launchagents", "launchdaemons", "com.apple.quarantine", "osascript", "dyld_insert_libraries", "tccutil", "security find-generic-password"]
ATTACK["macOS: persistensi / manipulasi sistem"] = "T1543.001 Launch Agent / T1574.006 Dynamic Linker Hijacking / T1553.001 Gatekeeper Bypass"

# ----------------------------- Mach-O ---------------------------------------

_MACHO_CPU = {7: "x86", 0x01000007: "x86-64", 12: "ARM", 0x0100000C: "ARM64", 0x0200000C: "ARM64_32", 18: "PowerPC", 0x01000012: "PowerPC64"}
_MACHO_FT = {1: "object (.o)", 2: "executable", 3: "fvmlib", 4: "core dump", 5: "preload", 6: "dylib", 7: "dylinker", 8: "bundle", 9: "dylib stub", 10: "dSYM", 11: "kext"}
_MACHO_PLAT = {1: "macOS", 2: "iOS", 3: "tvOS", 4: "watchOS", 5: "bridgeOS", 6: "Mac Catalyst", 7: "iOS Simulator", 8: "tvOS Simulator", 9: "watchOS Simulator", 10: "DriverKit"}


def _macho_cstr(d: bytes, off: int, lim: int) -> str:
    if off < 0 or off >= len(d):
        return ""
    stop = min(len(d), off + max(0, lim))
    e = d.find(b"\0", off, stop)
    return d[off:e if e >= 0 else stop].decode("utf-8", "replace")


_ENT_RISKY = {
    "com.apple.security.cs.allow-unsigned-executable-memory": "izinkan memori eksekusi tak bertanda tangan",
    "com.apple.security.cs.allow-jit": "izinkan JIT",
    "com.apple.security.cs.disable-library-validation": "muat dylib tanpa validasi tanda tangan (rawan dylib hijacking)",
    "com.apple.security.cs.allow-dyld-environment-variables": "izinkan DYLD_* (injeksi dylib)",
    "com.apple.security.cs.disable-executable-page-protection": "matikan proteksi halaman eksekusi",
    "com.apple.security.get-task-allow": "proses boleh di-debug / task_for_pid",
    "com.apple.security.cs.debugger": "boleh men-debug proses lain",
    "task_for_pid-allow": "boleh task_for_pid ke proses lain",
    "com.apple.private.tcc.allow": "bypass izin privasi (TCC), entitlement privat Apple",
    "com.apple.rootless.install": "boleh menulis area SIP",
    "com.apple.security.app-sandbox": None,   # sandbox aktif = mitigasi, bukan risiko
}
_ENT_KV = re.compile(r"<key>([^<]{1,160})</key>\s*(<true\s*/>|<false\s*/>|<string>([^<]{0,120})</string>|<array>|<dict>|<integer>(\d{1,12})</integer>)")


def _macho_codesig(d: bytes, base: int, dataoff: int, size: int) -> dict:
    """v99.3 [B3]: baca SuperBlob LC_CODE_SIGNATURE (big-endian): flag CodeDirectory (hardened runtime / ad-hoc) dan entitlements XML."""
    out: dict = {"runtime": False, "adhoc": False, "keys": [], "risky": [], "sandbox": False, "has_ent": False}
    st = base + dataoff
    if dataoff <= 0 or size < 12 or st + 12 > len(d) or d[st:st + 4] != b"\xfa\xde\x0c\xc0":
        return out
    n = struct.unpack_from(">I", d, st + 8)[0]
    end = min(len(d), st + min(size, 1 << 22))
    for i in range(min(n, 16)):
        p = st + 12 + i * 8
        if p + 8 > end:
            break
        bo = struct.unpack_from(">I", d, p + 4)[0]
        b0 = st + bo
        if b0 + 8 > end:
            continue
        magic, blen = struct.unpack_from(">II", d, b0)
        if magic == 0xFADE0C02 and b0 + 16 <= end:   # CodeDirectory
            cf = struct.unpack_from(">I", d, b0 + 12)[0]
            out["adhoc"], out["runtime"] = bool(cf & 0x2), bool(cf & 0x10000)
        elif magic == 0xFADE7171:   # entitlements (XML plist)
            out["has_ent"] = True
            xml = d[b0 + 8:b0 + min(blen, 65536)].decode("utf-8", "replace")
            for m in _ENT_KV.finditer(xml):
                k, v = m.group(1), m.group(2)
                val = "true" if v.startswith("<true") else "false" if v.startswith("<false") else (m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) else "..."))
                if len(out["keys"]) < 40:
                    out["keys"].append("%s=%s" % (k, val))
                if k == "com.apple.security.app-sandbox" and val == "true":
                    out["sandbox"] = True
                elif k in _ENT_RISKY and _ENT_RISKY[k] and val != "false":
                    out["risky"].append("%s (%s)" % (k, _ENT_RISKY[k]))
                elif k.startswith("com.apple.private.") and val != "false" and len(out["risky"]) < 12:
                    out["risky"].append("%s (entitlement privat Apple)" % k)
    out["risky"] = out["risky"][:12]
    return out


def _macho_thin(d: bytes, base: int = 0) -> dict | None:
    if base < 0 or base + 28 > len(d):
        return None
    m = d[base:base + 4]
    if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        e = "<"
    elif m in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
        e = ">"
    else:
        return None
    is64 = m[0] == 0xCF or m[3] == 0xCF
    hsz = 32 if is64 else 28
    if base + hsz > len(d):
        return None
    cpu, _sub, ft, ncmds, szcmds, flags = struct.unpack_from(e + "IIIIII", d, base + 4)
    info: dict = {"bits": 64 if is64 else 32, "endian": "little" if e == "<" else "big", "arch": _MACHO_CPU.get(cpu, "cpu 0x%X" % cpu),
                  "type": _MACHO_FT.get(ft, str(ft)), "ncmds": ncmds, "pie": bool(flags & 0x200000), "segments": [], "sections": [], "dylibs": [],
                  "weak": [], "rpaths": [], "entry": "", "signed": False, "encrypted": False, "uuid": "", "platform": "", "imports": [],
                  "exports": [], "nsyms": 0, "warn": [], "fat": [], "sig": None}
    off = base + hsz
    end = min(len(d), off + szcmds)
    symtab = None
    ent_left = ENT_BUDGET
    for _ in range(min(ncmds, 600)):
        if off + 8 > end:
            break
        cmd, csz = struct.unpack_from(e + "II", d, off)
        if csz < 8 or off + csz > end:
            break
        c = cmd & 0x7FFFFFFF
        if c in (0x1, 0x19):
            fmt, need, sec_sz = (e + "16sQQQQiiII", 72, 80) if c == 0x19 else (e + "16sIIIIiiII", 56, 68)
            if csz >= need:
                nm, _va, vsz, fo, fsz, _mp, ip, ns, _fl = struct.unpack_from(fmt, d, off + 8)
                sname = nm.split(b"\0")[0].decode("ascii", "replace")
                raw = d[base + fo:base + fo + min(fsz, SEC_ENT_SAMPLE)] if fo < len(d) else b""
                ent = 0.0
                if raw and len(raw) <= ent_left:
                    ent = _entropy(raw)
                    ent_left -= len(raw)
                info["segments"].append({"name": sname, "vsize": vsz, "fsize": fsz, "prot": "".join(ch if ip & b else "-" for ch, b in (("R", 1), ("W", 2), ("X", 4))), "ent": ent})
                for i in range(min(ns, 64)):
                    p = off + need + i * sec_sz
                    if p + 32 > off + csz:
                        break
                    info["sections"].append("%s,%s" % (sname, d[p:p + 16].split(b"\0")[0].decode("ascii", "replace")))
        elif c in (0xC, 0x18, 0x1F, 0x23, 0x20) and csz >= 24:
            noff = struct.unpack_from(e + "I", d, off + 8)[0]
            nm_ = _macho_cstr(d, off + noff, csz - noff) if noff < csz else ""
            (info["weak"] if c == 0x18 else info["dylibs"]).append(nm_)
        elif c == 0x1C and csz >= 12:
            noff = struct.unpack_from(e + "I", d, off + 8)[0]
            info["rpaths"].append(_macho_cstr(d, off + noff, csz - noff) if noff < csz else "")
        elif c == 0x28 and csz >= 16:
            info["entry"] = "LC_MAIN +0x%X" % struct.unpack_from(e + "Q", d, off + 8)[0]
        elif c == 0x5:
            info["entry"] = info["entry"] or "LC_UNIXTHREAD"
        elif c == 0x1D:
            info["signed"] = True
            if csz >= 16:
                try:
                    info["sig"] = _macho_codesig(d, base, *struct.unpack_from(e + "II", d, off + 8))
                except (struct.error, IndexError):
                    info["sig"] = None
        elif c in (0x21, 0x2C) and csz >= 20:
            info["encrypted"] = struct.unpack_from(e + "I", d, off + 16)[0] != 0
        elif c == 0x1B and csz >= 24:
            info["uuid"] = d[off + 8:off + 24].hex()
        elif c == 0x2 and csz >= 24:
            symtab = struct.unpack_from(e + "IIII", d, off + 8)
        elif c == 0x32 and csz >= 12:
            info["platform"] = _MACHO_PLAT.get(struct.unpack_from(e + "I", d, off + 8)[0], "")
        elif c == 0x24:
            info["platform"] = info["platform"] or "macOS"
        elif c == 0x25:
            info["platform"] = info["platform"] or "iOS"
        off += csz
    if symtab:
        so, ns, sto, stsz = symtab
        esz = 16 if is64 else 12
        info["nsyms"] = ns
        imp, exp_ = [], []
        for i in range(min(ns, 50000)):
            p = base + so + i * esz
            if p + esz > len(d):
                break
            strx, nt, _nsect, _ndesc = struct.unpack_from(e + "IBBH", d, p)
            if nt & 0xE0 or not nt & 1 or strx >= stsz:
                continue    # simbol debug (STAB) atau bukan eksternal
            nm_ = _macho_cstr(d, base + sto + strx, min(200, stsz - strx))
            nm_ = nm_[1:] if nm_.startswith("_") else nm_
            if not nm_:
                continue
            if nt & 0x0E == 0 and len(imp) < 1500:
                imp.append(nm_)
            elif nt & 0x0E == 0x0E and len(exp_) < 300:
                exp_.append(nm_)
        info["imports"], info["exports"] = imp, exp_
    w = info["warn"]
    if info["encrypted"]:
        w.append("Mach-O: segmen terenkripsi (cryptid=1, mis. FairPlay App Store); isi kode tidak bisa dibaca sebelum didekripsi")
    if not info["signed"] and info["type"] in ("executable", "dylib", "bundle"):
        w.append("Mach-O: tidak ada LC_CODE_SIGNATURE (tanda tangan dihapus atau belum diberikan)")
    for s in info["segments"]:
        if s["prot"][1:] == "WX":
            w.append("Mach-O: segmen %s dapat ditulis DAN dieksekusi (W+X)" % s["name"])
        if s["ent"] > 7.2 and s["fsize"] > 16384 and s["name"] != "__LINKEDIT":
            w.append("Mach-O: segmen %s berentropi %.2f (terkompres / terenkripsi / dikemas)" % (s["name"], s["ent"]))
    sg = info.get("sig")
    if sg:
        if sg["risky"]:
            w.append("Mach-O: entitlements berisiko: " + "; ".join(sg["risky"][:4]))
        if sg["adhoc"]:
            w.append("Mach-O: tanda tangan ad-hoc (tanpa identitas pengembang)")
        if info["type"] == "executable" and not sg["runtime"] and not sg["adhoc"]:
            w.append("Mach-O: hardened runtime tidak aktif")
    if any(r.startswith(("@loader_path", "@executable_path", ".")) for r in info["rpaths"]) and info["weak"]:
        w.append("Mach-O: RPATH relatif ditambah dylib lemah (kandidat dylib hijacking)")
    return info


def _parse_macho(d: bytes) -> dict | None:
    """Mach-O tipis atau fat / universal. Fat: irisan pertama yang terurai dipakai, daftar arsitektur lain disimpan di ['fat']."""
    if len(d) < 28:
        return None
    m = d[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None   # berkas class Java memakai magic yang sama; angka versinya selalu >= 45
        f64 = m[3] == 0xBF
        esz = 32 if f64 else 20
        slices = []
        for i in range(n):
            p = 8 + i * esz
            if p + esz > len(d):
                break
            if f64:
                cpu, _s, off, size, _a, _r = struct.unpack_from(">IIQQII", d, p)
            else:
                cpu, _s, off, size, _a = struct.unpack_from(">IIIII", d, p)
            slices.append((_MACHO_CPU.get(cpu, "cpu 0x%X" % cpu), off, size))
        for _arch, off, _size in slices:
            r = _macho_thin(d, off)
            if r:
                r["fat"] = [(a_, o_, s_) for a_, o_, s_ in slices]
                return r
        return None
    return _macho_thin(d, 0)


# ----------------------------- .NET metadata --------------------------------

_NET_STD_STREAMS = {"#~", "#-", "#Strings", "#US", "#GUID", "#Blob"}
_NET_CAPS = {
    "injeksi / manipulasi proses": {"VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "SetThreadContext", "QueueUserAPC", "NtWriteVirtualMemory"},
    "kripto": {"CreateDecryptor", "CreateEncryptor", "RijndaelManaged", "AesManaged", "AesCryptoServiceProvider", "TripleDESCryptoServiceProvider", "RSACryptoServiceProvider", "DESCryptoServiceProvider"},
    "muat kode dinamis": {"GetDelegateForFunctionPointer", "DefineDynamicAssembly", "LoadModule", "VirtualProtect", "VirtualAlloc", "GetProcAddress", "LoadLibrary"},
    "penyadap input / layar": {"SetWindowsHookEx", "GetAsyncKeyState", "GetKeyboardState", "CopyFromScreen", "GetForegroundWindow"},
    "anti-debug / anti-analisis": {"IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess"},
    "jaringan": {"DownloadString", "DownloadFile", "DownloadData", "UploadString", "UploadFile", "UploadValues", "TcpClient", "TcpListener"},
    "eksekusi proses / shell": {"ProcessStartInfo", "ShellExecute", "WinExec"},
}


def _dotnet_info(d: bytes, pe: dict) -> dict | None:
    """Metadata CLR: versi runtime, daftar stream, nama dari heap #Strings, string pengguna dari #US, dugaan obfuskasi."""
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    if nrva <= 14:
        return None
    rva, _sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 14)

    def r2o(x: int):
        for s in pe["sections"]:
            if s["va"] <= x < s["va"] + max(s["vsize"], s["rsize"]):
                return s["rptr"] + x - s["va"]
        return None

    co = r2o(rva)
    if co is None or co + 24 > len(d):
        return None
    _cb, _ma, _mi, mrva, _msz, cflags, etok = struct.unpack_from("<IHHIIII", d, co)
    mo = r2o(mrva)
    if mo is None or mo + 20 > len(d) or d[mo:mo + 4] != b"BSJB":
        return None
    vlen = struct.unpack_from("<I", d, mo + 12)[0]
    if vlen > 255 or mo + 16 + vlen + 4 > len(d):
        return None
    runtime = d[mo + 16:mo + 16 + vlen].split(b"\0")[0].decode("ascii", "replace")
    p = mo + 16 + vlen
    _fl, nstreams = struct.unpack_from("<HH", d, p)
    p += 4
    streams: dict[str, tuple[int, int]] = {}
    for _ in range(min(nstreams, 16)):
        if p + 9 > len(d):
            break
        so, ssz = struct.unpack_from("<II", d, p)
        e = d.find(b"\0", p + 8, p + 40)
        if e < 0:
            break
        nm = d[p + 8:e].decode("ascii", "replace")
        streams[nm] = (mo + so, ssz)
        p += 8 + ((len(nm) + 1 + 3) & ~3)
    names: list[str] = []
    st = streams.get("#Strings")
    if st and st[0] < len(d):
        heap = d[st[0]:st[0] + min(st[1], 4 * 1024 * 1024)]
        names = _uniq((x.decode("utf-8", "replace") for x in heap.split(b"\0") if x), 6000)
    us: list[str] = []
    ust = streams.get("#US")
    if ust and ust[0] < len(d):
        heap = d[ust[0]:ust[0] + min(ust[1], 4 * 1024 * 1024)]
        i = 1
        while i < len(heap) and len(us) < 3000:
            b0 = heap[i]
            if b0 < 0x80:
                ln, i = b0, i + 1
            elif b0 & 0xC0 == 0x80 and i + 1 < len(heap):
                ln, i = ((b0 & 0x3F) << 8) | heap[i + 1], i + 2
            elif b0 & 0xE0 == 0xC0 and i + 3 < len(heap):
                ln, i = ((b0 & 0x1F) << 24) | (heap[i + 1] << 16) | (heap[i + 2] << 8) | heap[i + 3], i + 4
            else:
                break
            if ln == 0:
                continue
            raw = heap[i:i + max(0, ln - 1)]
            i += ln
            s = raw.decode("utf-16le", "ignore")
            if len(s) >= 4 and sum(ch.isprintable() for ch in s) >= 0.9 * len(s):
                us.append(s[:300])
    obf: list[str] = []
    odd = [n_ for n_ in streams if n_ not in _NET_STD_STREAMS]
    if odd:
        obf.append("stream metadata tidak baku: " + ", ".join(odd[:3]))
    if len(names) >= 40:
        short = sum(1 for n_ in names if len(n_) <= 2)
        weird = sum(1 for n_ in names if any(ord(ch) > 126 or ord(ch) < 32 for ch in n_))
        if short / len(names) > 0.35:
            obf.append("%d%% nama tipe / anggota hanya 1-2 karakter (pola penggantian nama obfuskator)" % (100 * short // len(names)))
        if weird / len(names) > 0.2:
            obf.append("%d%% nama berisi karakter non-ASCII / kontrol (pola obfuskator)" % (100 * weird // len(names)))
    mres: list[dict] = []   # v98.6: resource terkelola dari header CLR (tiap blob: uint32 panjang + data; tanpa nama, nama ada di tabel metadata)
    try:
        rrva, rsz = struct.unpack_from("<II", d, co + 24)
        ro = r2o(rrva) if rrva and rsz else None
        if ro is not None:
            end, pos = min(ro + rsz, len(d)), ro
            while pos + 4 <= end and len(mres) < 64:
                ln = 0
                for cand in (pos, (pos + 3) & ~3, (pos + 7) & ~7):   # sebagian penghasil menyelaraskan blob; coba beberapa
                    if cand + 4 <= end:
                        v_ = struct.unpack_from("<I", d, cand)[0]
                        if 0 < v_ <= end - cand - 4:
                            pos, ln = cand + 4, v_
                            break
                if not ln:
                    break
                blob_ = d[pos:pos + min(ln, 1 << 20)]
                fmt_, ok_ = _res_format(d, pos, ln)
                mres.append({"off": pos, "size": ln, "ent": _entropy(blob_[:65536]), "mz": blob_[:2] == b"MZ", "rsrc": blob_[:4] == b"\xce\xca\xef\xbe",
                             "fmt": fmt_, "fmt_ok": ok_})
                pos += ln
    except (struct.error, IndexError, ValueError):
        pass
    return {"runtime": runtime, "streams": [(k, v[1]) for k, v in streams.items()], "ilonly": bool(cflags & 1), "strong": bool(cflags & 8),
            "entry_token": etok, "names": names, "us": us, "obf": obf, "n_names": len(names), "mres": mres}


def _net_caps(names: list[str]) -> dict[str, list[str]]:
    have = set(names)
    out = {cap: sorted(have & keys)[:6] for cap, keys in _NET_CAPS.items() if have & keys}
    if {"Assembly", "Load", "Invoke"} <= have:
        out.setdefault("muat kode dinamis", []).append("Assembly.Load + Invoke")
    return out


# ----------------------------- CTPH (hash fuzzy gaya ssdeep) ----------------

_B64C = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CTPH_SAMPLE = 1024 * 1024


def _spamsum(data: bytes, bs: int) -> tuple[str, str]:
    h1 = h2 = h3 = 0
    win = [0] * 7
    n = 0
    bh1 = bh2 = 0x28021967
    s1, s2 = [], []
    M = 0xFFFFFFFF
    b2 = bs * 2
    r = 0
    for c in data:
        bh1 = ((bh1 * 0x01000193) ^ c) & M
        bh2 = ((bh2 * 0x01000193) ^ c) & M
        h2 = (h2 - h1 + 7 * c) & M
        h1 = (h1 + c - win[n % 7]) & M
        win[n % 7] = c
        n += 1
        h3 = ((h3 << 5) ^ c) & M
        r = (h1 + h2 + h3) & M
        if r % bs == bs - 1 and len(s1) < 63:
            s1.append(_B64C[bh1 & 63])
            bh1 = 0x28021967
        if r % b2 == b2 - 1 and len(s2) < 31:
            s2.append(_B64C[bh2 & 63])
            bh2 = 0x28021967
    if r:
        s1.append(_B64C[bh1 & 63])
        s2.append(_B64C[bh2 & 63])
    return "".join(s1), "".join(s2)


def ctph(data: bytes) -> str:
    """Hash fuzzy (context-triggered piecewise hashing, algoritma spamsum). Format 'blok:digest1:digest2'.
    Dapat dibandingkan dengan ctph_compare(); bukan jaminan identik dengan keluaran ssdeep resmi."""
    n = len(data)
    if n < 64:
        return ""
    bs = 3
    while bs * 64 < n:
        bs *= 2
    while True:
        s1, s2 = _spamsum(data, bs)
        if bs > 3 and len(s1) < 32:
            bs //= 2
            continue
        return "%d:%s:%s" % (bs, s1, s2)


def _squeeze(s: str) -> str:
    return re.sub(r"(.)\1{3,}", r"\1\1\1", s)


def _ssd_one(a: str, b: str, bs: int) -> int:
    if len(a) < 7 or len(b) < 7:
        return 0
    if not any(a[i:i + 7] in b for i in range(len(a) - 6)):
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 2)))
        prev = cur
    score = prev[-1] * 64 // (len(a) + len(b))
    score = 100 - (100 * score // 64)
    if bs < 45:
        score = min(score, bs // 3 * min(len(a), len(b)))
    return max(0, min(100, score))


def ctph_compare(x: str, y: str) -> int:
    """Skor kemiripan 0-100 antara dua digest ctph(); 0 = tidak ada kemiripan berarti atau blok tak sebanding."""
    try:
        bx, ax1, ax2 = x.split(":", 2)
        by, ay1, ay2 = y.split(":", 2)
        bx, by = int(bx), int(by)
    except ValueError:
        return 0
    ax1, ax2, ay1, ay2 = _squeeze(ax1), _squeeze(ax2), _squeeze(ay1), _squeeze(ay2)
    if bx == by:
        if ax1 == ay1 and ax2 == ay2:
            return 100
        return max(_ssd_one(ax1, ay1, bx), _ssd_one(ax2, ay2, bx * 2))
    if bx == by * 2:
        return _ssd_one(ax1, ay2, bx)
    if by == bx * 2:
        return _ssd_one(ax2, ay1, by)
    return 0


def _read_sample(path, n: int = CTPH_SAMPLE) -> tuple[bytes, int]:
    f, size = _open_regular(path)
    with f:
        return f.read(n), size


def similarity(path_a, path_b) -> dict:
    """Bandingkan dua berkas: hash identik, skor CTPH, imphash, rich hash, irisan bagian PE (MD5), irisan string menarik."""
    da, sa = _read_sample(path_a)
    db, sb = _read_sample(path_b)
    ra, rb = triage(path_a, fuzzy=False), triage(path_b, fuzzy=False)
    ca, cb = ctph(da), ctph(db)
    out = {"a": Path(path_a).name, "b": Path(path_b).name, "size_a": sa, "size_b": sb, "identical": ra["sha256"] == rb["sha256"],
           "ctph_a": ca, "ctph_b": cb, "ctph_score": ctph_compare(ca, cb) if ca and cb else 0}
    pa, pb = ra.get("pe"), rb.get("pe")
    if pa and pb and not pa.get("broken") and not pb.get("broken"):
        out["imphash_same"] = bool(pa.get("imphash")) and pa.get("imphash") == pb.get("imphash")
        out["rich_same"] = bool((pa.get("rich") or {}).get("hash")) and (pa.get("rich") or {}).get("hash") == (pb.get("rich") or {}).get("hash")
        ma = {x["md5"] for x in pa["sections"] if x.get("md5")}
        mb = {x["md5"] for x in pb["sections"] if x.get("md5")}
        out["section_md5_shared"] = len(ma & mb)
        out["sections"] = (len(ma), len(mb))
    ua = set(ra["ind"]["urls"]) | set(ra["ind"]["ips"]) | set(ra["ind"]["pdb"])
    ub = set(rb["ind"]["urls"]) | set(rb["ind"]["ips"]) | set(rb["ind"]["pdb"])
    out["shared_iocs"] = sorted(ua & ub)[:10]
    verdict = "identik" if out["identical"] else ("sangat mirip (kemungkinan varian / keluarga sama)" if out["ctph_score"] >= 70 else
                                                   "ada kemiripan" if out["ctph_score"] >= 30 else "tidak mirip menurut CTPH")
    if not out["identical"] and (out.get("imphash_same") or out.get("rich_same") or out.get("section_md5_shared")) and out["ctph_score"] < 70:
        verdict += "; tetapi struktur PE sama (imphash / rich header / bagian), kemungkinan satu keluarga atau satu toolchain"
    out["verdict"] = verdict
    return out


def similar_text(path_a, path_b) -> str:
    try:
        r = similarity(path_a, path_b)
    except Exception as e:
        return "SIMILARITY gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L = ["KEMIRIPAN: %s vs %s" % (r["a"], r["b"]), "Ukuran : %s vs %s" % (_human(r["size_a"]), _human(r["size_b"])),
         "SHA-256 identik: %s" % ("ya" if r["identical"] else "tidak"), "CTPH   : skor %d/100 (sampel %s pertama)" % (r["ctph_score"], _human(CTPH_SAMPLE))]
    if "imphash_same" in r:
        L.append("PE     : imphash %s | rich header %s | bagian MD5 sama %d dari %d/%d" % ("sama" if r["imphash_same"] else "beda", "sama" if r["rich_same"] else "beda", r["section_md5_shared"], *r["sections"]))
    if r["shared_iocs"]:
        L.append("IOC bersama: " + " | ".join(_df(x, True) for x in r["shared_iocs"][:6]))
    L.append("Kesimpulan (petunjuk, bukan vonis): " + r["verdict"])
    return "\n".join(_clean(x) for x in L)


# ----------------------------- XOR / ADD / ROL ------------------------------

_XOR_WORDS = [b"This program cannot be run", b"https://", b"http://", b"kernel32", b"KERNEL32", b"cmd.exe", b"powershell", b"GetProcAddress", b"LoadLibrary",
              b"VirtualAlloc", b"WScript.Shell", b"/bin/sh", b"User-Agent", b"Mozilla/5.0"]
_XOR_URL = re.compile(rb"https?://[\x21-\x7e]{4,100}")
def _xor_table(op: str, key: int) -> bytes:
    if op == "XOR":
        return bytes(i ^ key for i in range(256))
    if op == "ADD":
        return bytes((i + key) & 255 for i in range(256))
    return bytes(((i << key) | (i >> (8 - key))) & 255 for i in range(256))   # ROL


def _xor_hunt(d: bytes, budget: float = 3.0) -> list[dict]:
    """Cari kata kunci (URL, stub DOS, nama API) yang baru muncul setelah dekode satu byte (XOR / ADD / ROL).
    XOR dan ADD dicari lewat selisih antar-byte (tidak bergantung pada kunci), jadi 255 kunci dicek sekali jalan, bukan satu per satu.
    Jendela: 2 MB pertama + 1 MB terakhir berkas."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []   # teks / skrip biasa: tidak ada gunanya
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    n = len(samp)
    words = [w for w in _XOR_WORDS if w not in samp]   # kata yang sudah polos di berkas tidak diburu
    t0 = time.monotonic()
    found: dict[tuple[str, int], set] = {}
    xd = (int.from_bytes(samp, "big") ^ int.from_bytes(samp[1:] + b"\0", "big")).to_bytes(n, "big")
    for w in words:
        pat = bytes(w[i] ^ w[i + 1] for i in range(len(w) - 1))
        pos, tries = xd.find(pat), 0
        while pos >= 0 and tries < 4:
            k = samp[pos] ^ w[0]
            if k and pos + len(w) <= n and bytes(b ^ k for b in samp[pos:pos + len(w)]) == w:
                found.setdefault(("XOR", k), set()).add(w)
            pos, tries = xd.find(pat, pos + 1), tries + 1
    del xd
    if time.monotonic() - t0 < budget:
        ad = bytes((b - a) & 255 for a, b in zip(samp, samp[1:]))
        for w in words:
            pat = bytes((w[i + 1] - w[i]) & 255 for i in range(len(w) - 1))
            pos, tries = ad.find(pat), 0
            while pos >= 0 and tries < 4:
                k = (w[0] - samp[pos]) & 255
                if k and pos + len(w) <= n and bytes((b + k) & 255 for b in samp[pos:pos + len(w)]) == w:
                    found.setdefault(("ADD", k), set()).add(w)
                pos, tries = ad.find(pat, pos + 1), tries + 1
        del ad
    for r in range(1, 8):
        if time.monotonic() - t0 > budget:
            break
        dec = samp.translate(_xor_table("ROL", r))
        for w in words:
            if w in dec:
                found.setdefault(("ROL", r), set()).add(w)
    res: list[dict] = []
    for (op, key), ws in found.items():
        urls = [u.decode("ascii", "replace") for u in _uniq(_XOR_URL.findall(samp.translate(_xor_table(op, key))), 3)] if any(w.startswith(b"http") for w in ws) else []
        res.append({"op": op, "key": key, "words": sorted(w.decode("ascii") for w in ws)[:4], "count": len(ws), "urls": urls})
    res.sort(key=lambda x: (-x["count"], x["op"] != "XOR", x["key"]))
    return res[:5]


_XOR_CRIB = b"This program cannot be run in DOS mode"


def _xor_multi(d: bytes, budget: float = 3.0) -> list[dict]:
    """XOR dengan kunci BERULANG 2-16 byte. Known-plaintext: tulisan stub DOS tetap polos di PE biasa, jadi selisih d[j] ^ d[j+k] pada stub
    terenkode kunci periode k sama persis dengan selisih teksnya sendiri, apa pun kuncinya. Dicari lewat big-int (satu XOR per k).
    RC4 / kunci tak berulang tidak bisa diburu begini tanpa kunci. Jendela: 2 MB pertama + 1 MB terakhir."""
    if len(d) < 512:
        return []
    probe = d[:4096]
    if sum(1 for b in probe if 9 <= b <= 13 or 32 <= b <= 126) / len(probe) > 0.97:
        return []
    head, tail = 2 << 20, 1 << 20
    samp = d if len(d) <= head + tail else d[:head] + d[-tail:]
    if _XOR_CRIB in samp:
        return []
    n, crib = len(samp), _XOR_CRIB
    t0 = time.monotonic()
    x = int.from_bytes(samp, "big")
    mask = (1 << (8 * n)) - 1

    def to_off(p: int) -> int:
        return p if len(d) <= head + tail or p < head else len(d) - tail + (p - head)

    res: list[dict] = []
    seen: set[int] = set()
    for k in range(2, 17):
        if time.monotonic() - t0 > budget or len(res) >= 3:
            break
        diff = (((x << (8 * k)) & mask) ^ x).to_bytes(n, "big")
        pat = bytes(crib[i] ^ crib[i + k] for i in range(len(crib) - k))
        pos, tries = diff.find(pat), 0
        while pos >= 0 and tries < 4:
            tries += 1
            if pos + len(crib) <= n and pos not in seen:
                ks = bytes(samp[pos + i] ^ crib[i] for i in range(len(crib)))
                if all(ks[i] == ks[i % k] for i in range(len(crib))) and len(set(ks[:k])) > 1:
                    seen.add(pos)
                    # kunci disejajarkan ke awal MZ (stub DOS lazim di offset 0x4E dari MZ)
                    mz = pos - 0x4E
                    key = bytes(ks[(i - 0x4E) % k] for i in range(k))
                    ok = mz >= 0 and bytes(samp[mz + i] ^ key[i % k] for i in range(2)) == b"MZ"
                    res.append({"k": k, "key": (key if ok else ks[:k]).hex(), "off": to_off(pos), "mz": ok, "mz_off": to_off(mz) if ok else 0})
            pos = diff.find(pat, pos + 1)
    res.sort(key=lambda r: (not r["mz"], r["k"]))
    return res[:3]


# ----------------------------- detail kemasan / installer -------------------


# ----------------------------- pemulihan nama fungsi Go (pclntab) ----------
# Murni parsing struktur tabel runtime Go (tanpa dependensi, tanpa menjalankan apa pun). Mendukung pclntab Go 1.2, 1.16, 1.18 dan 1.20+.
# Tabel dicari lewat magic + minLC + ptrSize, lalu dibuktikan dengan membaca nama fungsi pertama; kandidat palsu dibuang.

GO_MAX_FUNCS = 500_000          # batas fungsi yang dibaca (biner Go besar biasanya 5 - 50 ribu)
GO_READ_MAX = 128 << 20         # berkas Go sampai segini dibaca utuh untuk tahap ini (pindai biasa dibatasi MAX_SCAN)
GO_TIME_BUDGET = 3.0            # detik; sisanya dilaporkan sebagai terpotong
_GO_VER = {0xFFFFFFFB: "1.2", 0xFFFFFFFA: "1.16", 0xFFFFFFF0: "1.18", 0xFFFFFFF1: "1.20+"}
_GO_PCLN_RE = re.compile(rb"[\xf0\xf1\xfa\xfb]\xff\xff\xff\x00\x00[\x01\x02\x04][\x04\x08]")
_GO_NAME_OK = re.compile(rb"[\x20-\x7e\x80-\xff]{1,400}\Z")
_GO_NOTABLE_STD = ("os/exec", "net/http", "net", "syscall", "crypto/aes", "crypto/cipher", "crypto/rsa", "crypto/tls", "os/user",
                   "encoding/base64", "compress/gzip", "archive/zip", "plugin", "debug/pe", "golang.org/x/sys/windows")
_GO_NOTABLE_RE = re.compile(r"(?i)ransom|keylog|stealer|socks|ngrok|chisel|mimikatz|cobalt|sliver|merlin|beacon|implant|\bc2\b|reverse(?:shell|proxy)|persist|inject")


def _go_pkg(name: str) -> str:
    i = name.rfind("/")
    j = name.find(".", i + 1)
    return name[:j] if j > 0 else name


def _go_parse_at(d: bytes, off: int, deadline: float):
    """Satu kandidat pclntab di offset berkas `off`. Mengembalikan dict atau None. Tidak pernah membaca di luar `d`."""
    n = len(d)
    if off + 8 > n:
        return None
    magic = struct.unpack_from("<I", d, off)[0]
    ver = _GO_VER.get(magic)
    ps = d[off + 7]
    if ver is None or ps not in (4, 8) or d[off + 6] not in (1, 2, 4):
        return None
    fmt = "<I" if ps == 4 else "<Q"
    hdr = {0xFFFFFFFB: 8 + ps, 0xFFFFFFFA: 8 + 7 * ps}.get(magic, 8 + 8 * ps)
    if off + hdr > n:
        return None

    def rd(o: int) -> int:
        return struct.unpack_from(fmt, d, o)[0]
    nfunc = rd(off + 8)
    if not 0 < nfunc <= GO_MAX_FUNCS * 4:
        return None
    text = 0
    if magic == 0xFFFFFFFB:
        tab, wide, fn_base = off + 8 + ps, True, off
    else:
        if magic == 0xFFFFFFFA:
            fn_base, pcln, wide = off + rd(off + 8 + 2 * ps), rd(off + 8 + 6 * ps), True
        else:
            text, fn_base, pcln, wide = rd(off + 8 + 2 * ps), off + rd(off + 8 + 3 * ps), rd(off + 8 + 7 * ps), False
            fn_base = off + rd(off + 8 + 3 * ps)
        tab = off + pcln
        if pcln > n or fn_base > n:
            return None
    esz = 2 * ps if wide else 8
    if tab + esz * min(nfunc, 4) > n:
        return None

    def name_at(i: int):
        p = tab + i * esz
        if p + esz > n:
            return None
        if wide:
            pc, fo = rd(p), rd(p + ps)
            fp = (off + fo) if magic == 0xFFFFFFFB else (tab + fo)
            if fp + ps + 4 > n:
                return None
            nm = struct.unpack_from("<i", d, fp + ps)[0]
        else:
            eo, fo = struct.unpack_from("<II", d, p)
            pc = text + eo
            fp = tab + fo
            if fp + 8 > n:
                return None
            nm = struct.unpack_from("<i", d, fp + 4)[0]
        q = fn_base + nm if magic != 0xFFFFFFFB else off + nm
        if nm < 0 or q >= n:
            return None
        e = d.find(b"\0", q, min(n, q + 401))
        if e <= q:
            return None
        raw = d[q:e]
        if not _GO_NAME_OK.match(raw):
            return None
        return pc, raw.decode("utf-8", "replace")

    probe = [name_at(i) for i in range(min(nfunc, 12))]
    if sum(1 for x in probe if x) < max(3, len(probe) * 3 // 4):
        return None
    names: list = []
    truncated = nfunc > GO_MAX_FUNCS
    for i in range(min(nfunc, GO_MAX_FUNCS)):
        if (i & 1023) == 0 and time.monotonic() > deadline:
            truncated = True
            break
        r = name_at(i)
        if r:
            names.append(r)
    if len(names) < 3:
        return None
    return {"ver": ver, "bits": ps * 8, "off": off, "nfunc": nfunc, "names": names, "truncated": truncated}


def _go_pclntab(d: bytes, f=None, size: int | None = None):
    """Pulihkan daftar fungsi biner Go dari pclntab. None bila bukan biner Go / tabel tidak ditemukan. Hanya membaca; tidak dijalankan.
    Biner Go sering > MAX_SCAN (tabel nama ada di ujung berkas): kalau `f` dan `size` diberikan dan berkas <= GO_READ_MAX, dibaca utuh untuk tahap ini saja."""
    if not (d.find(b"runtime.gopanic") >= 0 or d.find(b"go.buildid") >= 0 or d.find(b"Go build ID") >= 0 or d.find(b"\xff Go buildinf:") >= 0):
        return None
    partial = bool(size and len(d) < size)
    if partial and f is not None and size <= GO_READ_MAX:
        try:
            f.seek(0)
            full = f.read(size)
            if len(full) == size:
                d, partial = full, False
        except (OSError, MemoryError):
            pass
    deadline = time.monotonic() + GO_TIME_BUDGET
    best = None
    for k, m in enumerate(_GO_PCLN_RE.finditer(d)):
        if k >= 64 or time.monotonic() > deadline:
            break
        try:
            r = _go_parse_at(d, m.start(), deadline)
        except (struct.error, ValueError, OverflowError, MemoryError):
            r = None
        if r and (best is None or len(r["names"]) > len(best["names"])):
            best = r
    if not best:
        return None
    pk: collections.Counter = collections.Counter(_go_pkg(nm) for _pc, nm in best["names"])
    main = [nm for _pc, nm in best["names"] if nm == "main" or nm.startswith("main.")]
    third = [(p, c) for p, c in pk.most_common() if "." in p.split("/")[0] and p != "main"]
    std = {p for p in pk if p != "main" and "." not in p.split("/")[0]}
    notable_std = [p for p in _GO_NOTABLE_STD if p in pk or p in std]
    flagged = sorted({p for p in pk if _GO_NOTABLE_RE.search(p)})[:12]
    entry = {x[1]: x[0] for x in reversed(best["names"])}
    return {"ver": best["ver"], "bits": best["bits"], "off": best["off"], "nfunc": best["nfunc"], "read": len(best["names"]),
            "truncated": best["truncated"], "partial_scan": partial, "n_pkgs": len(pk), "n_main": len(main),
            "main": [{"name": nm[:160], "addr": entry.get(nm, 0)} for nm in main[:60]],
            "third": [[p[:120], c] for p, c in third[:15]], "std": notable_std[:12], "flagged": flagged}


def _pack_details(d: bytes, size: int) -> list[str]:
    out: list[str] = []
    head = d[: 16 * 1024 * 1024]
    k = head.rfind(b"MEI\x0c\x0b\x0a\x0b\x0e")
    if k >= 0 and k + 24 <= len(head):
        pkg, toc, tlen, pyv = struct.unpack_from(">IIII", head, k + 8)
        lib = head[k + 24:k + 88].split(b"\0")[0].decode("ascii", "ignore") if k + 88 <= len(head) else ""
        newer = "python" in lib.lower()
        pyver = ("%d.%d" % (pyv // 100, pyv % 100) if pyv >= 100 else "%d.%d" % (pyv // 10, pyv % 10)) if 20 <= pyv < 1000 else "?"
        line = "PyInstaller %s | Python %s%s | arsip %s" % ("2.1+" if newer else "2.0", pyver, " (%s)" % lib if lib else "", _human(pkg))
        if size == len(d) and 0 < tlen < 4 * 1024 * 1024:
            csz = 88 if newer else 24
            base = size - (pkg + (size - k - csz))
            p, stop = base + toc, base + toc + tlen
            kinds: collections.Counter = collections.Counter()
            scripts: list[str] = []
            while p + 18 <= min(stop, len(d)):
                elen = struct.unpack_from(">I", d, p)[0]
                if elen < 18 or p + elen > len(d):
                    break
                typ = d[p + 17:p + 18].decode("latin-1")
                nm = d[p + 18:p + elen].split(b"\0")[0].decode("utf-8", "replace")
                kinds[typ] += 1
                if typ == "s" and len(scripts) < 6:
                    scripts.append(nm)
                p += elen
            if kinds:
                line += " | %d entri" % sum(kinds.values())
            if scripts:
                line += " | skrip masuk: " + ", ".join(scripts)
        out.append(line)
    m = re.search(rb"\$Id: UPX (\d+\.\d+\w*) Copyright", head)
    if m:
        out.append("UPX %s (unpack: `upx -d`)" % m.group(1).decode("ascii"))
    i = head.find(b"\xef\xbe\xad\xdeNullsoftInst")
    if i >= 0:
        out.append("installer NSIS: header firstheader di offset 0x%X (ekstrak dengan 7-Zip)" % i)
    m = re.search(rb"Inno Setup Setup Data \(([0-9.]{3,12}[^)]{0,16})\)", head)
    if m:
        out.append("Inno Setup versi %s (ekstrak dengan innoextract)" % m.group(1).decode("ascii", "replace"))
    if head.find(b"Go build ID") >= 0 or head.find(b"runtime.gopanic") >= 0:
        m = re.search(rb"\x00(go1\.\d{1,2}(?:\.\d{1,2})?)\x00?", head)
        out.append("Go%s (pulihkan nama fungsi dari pclntab)" % (" " + m.group(1).decode("ascii") if m else ""))
    m = re.search(rb"/rustc/([0-9a-f]{40})", head)
    if m:
        out.append("Rust: kompiler commit %s" % m.group(1).decode("ascii")[:12])
    i = head.find(b"AU3!EA06")
    if i >= 0:
        out.append("AutoIt: skrip terkompilasi (AU3!EA06) di offset 0x%X" % i)
    i = head.find(b";!@Install@!UTF-8!")
    if i >= 0:
        out.append("arsip swa-ekstrak 7-Zip: blok konfigurasi di offset 0x%X (baca perintah RunProgram)" % i)
    if b"pyarmor" in head.lower():
        out.append("PyArmor: skrip Python dilindungi (pyarmor_runtime)")
    return out


# ----------------------------- penggabung v97 -------------------------------


def _v97_enrich(d: bytes, size: int, rep: dict, fuzzy: bool, f=None) -> None:
    w = rep["warn"]
    zp, mo, dn = rep.get("zip"), rep.get("macho"), rep.get("dotnet")
    if mo:
        w.extend(mo["warn"])
    if dn:
        for x in dn["obf"]:
            w.append(".NET: " + x)
    try:
        rep["pack"] = _pack_details(d, size) if not zp else []
    except Exception as e:
        rep["pack"] = []
        w.append("analisis kemasan gagal: %s" % type(e).__name__)
    try:
        rep["go"] = _go_pclntab(d, f, size) if not zp else None
    except Exception as e:
        rep["go"] = None
        w.append("pemulihan nama fungsi Go gagal: %s" % type(e).__name__)
    try:
        rep["xor"] = _xor_hunt(d) if not zp else []
    except Exception as e:
        rep["xor"] = []
        w.append("perburuan XOR gagal: %s" % type(e).__name__)
    for x in rep["xor"][:2]:
        w.append("kata kunci tersembunyi setelah dekode %s 0x%02X: %s (kemungkinan string / payload terenkode satu byte)" % (x["op"], x["key"], ", ".join(x["words"])))
    try:
        rep["xor_multi"] = _xor_multi(d) if not zp else []
    except Exception as e:
        rep["xor_multi"] = []
        w.append("perburuan XOR kunci berulang gagal: %s" % type(e).__name__)
    for x in rep["xor_multi"][:2]:
        w.append("stub DOS terenkode XOR kunci berulang %d byte (%s) di offset 0x%X%s" % (x["k"], x["key"], x["off"], "; MZ terkonfirmasi: PE tersembunyi" if x["mz"] else ""))
    for x in (dn or {}).get("mres", []):
        if x["mz"]:
            w.append("resource terkelola .NET berisi executable (MZ, %s) di offset 0x%X" % (_human(x["size"]), x["off"]))
        elif x["ent"] > 7.2 and x["size"] > 16384 and not (x.get("fmt") and x.get("fmt_ok")):
            w.append("resource terkelola .NET berentropi %.2f (%s) di offset 0x%X: kemungkinan payload terenkripsi / terkompres" % (x["ent"], _human(x["size"]), x["off"]))
    rep["ctph"] = ""
    if fuzzy and not zp:
        try:
            rep["ctph"] = ctph(d[:CTPH_SAMPLE])
        except Exception as e:
            w.append("CTPH gagal: %s" % type(e).__name__)
    _mcfg_enrich(d, rep, (rep.get("pe") if rep.get("pe") and not rep["pe"].get("broken") else None), dn, zp)   # v99.19 [A1]; kunci baru rep["malcfg"], aditif


def _render_v97(rep: dict, a, compact: bool, defang: bool) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        a("Mach-O : %s %s-bit %s, %s%s | entry: %s | tanda tangan: %s | PIE: %s%s" % (
            mo["arch"], mo["bits"], mo["type"], mo["endian"] + "-endian", (" | " + mo["platform"]) if mo["platform"] else "",
            mo["entry"] or "-", "ada" if mo["signed"] else "tidak ada", "ya" if mo["pie"] else "tidak", " | TERENKRIPSI" if mo["encrypted"] else ""))
        if mo["fat"] and len(mo["fat"]) > 1:
            a("   universal: " + ", ".join("%s (%s)" % (x[0], _human(x[2])) for x in mo["fat"][:6]))
        if not compact:
            if mo["dylibs"] or mo["weak"]:
                a("   dylib (%d): %s%s" % (len(mo["dylibs"]) + len(mo["weak"]), ", ".join(mo["dylibs"][:10]), (" | lemah: " + ", ".join(mo["weak"][:4])) if mo["weak"] else ""))
            sg = mo.get("sig")
            if sg:
                a("   code signing: hardened runtime %s | ad-hoc %s | sandbox %s | entitlements %s" % (
                    "ya" if sg["runtime"] else "tidak", "ya" if sg["adhoc"] else "tidak", "ya" if sg["sandbox"] else "tidak",
                    ("%d kunci" % len(sg["keys"])) if sg["has_ent"] else "tidak ada"))
                if sg["keys"]:
                    a("   entitlements: " + ", ".join(sg["keys"][:12]))
            if mo["rpaths"]:
                a("   RPATH: " + ", ".join(mo["rpaths"][:4]))
            if mo["segments"]:
                a("   segmen: " + ", ".join("%s %s %.1f" % (s["name"], s["prot"], s["ent"]) for s in mo["segments"][:8]))
            if mo["imports"]:
                a("   simbol impor (%d): %s" % (len(mo["imports"]), ", ".join(mo["imports"][:25])))
            if mo["uuid"]:
                a("   UUID: " + mo["uuid"])
    cm = rep.get("com")
    if cm and (cm["groups"] or cm["apis"]):
        a("Objek COM (dari GUID CLSID / IID): " + "; ".join("%s [%s]%s" % (g["group"], ", ".join(g["names"][:3 if compact else 5]), "" if compact else " (%s)" % g["how"]) for g in cm["groups"]) if cm["groups"] else "Objek COM: tidak ada GUID yang dikenal")
        if cm["apis"]:
            a("   API COM diimpor: " + ", ".join(cm["apis"]))
        if cm["unknown"] and not compact:
            a("   GUID lain berbentuk string (tidak ada di daftar, %d): %s" % (len(cm["unknown"]), ", ".join(cm["unknown"][:4])))
    if dn:
        a(".NET   : runtime %s | %s%s | %d nama di #Strings | %d string pengguna (#US)" % (
            dn["runtime"], "IL murni" if dn["ilonly"] else "campuran (ada native)", ", strong-name" if dn["strong"] else "", dn["n_names"], len(dn["us"])))
        if not compact:
            a("   stream: " + ", ".join("%s (%s)" % (n, _human(s)) for n, s in dn["streams"][:8]))
            hot = [u for u in dn["us"] if re.search(r"(?i)https?://|\\\\|\.exe|\.dll|powershell|cmd|\.onion|password|token|key", u)][:8]
            if hot:
                a("   string pengguna menarik: " + " | ".join(_df(x, defang) for x in hot))
    for line in rep.get("pack") or []:
        a("Kemasan: " + line)
    go = rep.get("go")
    if go:
        a("Go     : pclntab %s (%d-bit) di offset 0x%X | %d fungsi%s | %d paket | %d fungsi paket main" % (
            go["ver"], go["bits"], go["off"], go["nfunc"], (" (terbaca %d%s)" % (go["read"], "; berkas dipindai sebagian" if go.get("partial_scan") else ", dipotong")) if (go["truncated"] or go.get("partial_scan")) else "", go["n_pkgs"], go["n_main"]))
        if go["main"]:
            a("   fungsi main: " + ", ".join(_clean(x["name"]) for x in go["main"][: (6 if compact else 20)]) + (" ..." if go["n_main"] > (6 if compact else 20) else ""))
        if not compact:
            if go["third"]:
                a("   paket pihak ketiga: " + ", ".join("%s (%d)" % (_clean(p), c) for p, c in go["third"][:10]))
            if go["std"]:
                a("   paket pustaka standar yang layak dicek: " + ", ".join(_clean(x) for x in go["std"]))
            if go["flagged"]:
                a("   nama paket yang layak dicek: " + ", ".join(_clean(x) for x in go["flagged"]))
    for x in (rep.get("xor") or [])[: (1 if compact else 4)]:
        a("Perburuan satu-byte: %s kunci 0x%02X -> %s%s" % (x["op"], x["key"], ", ".join(x["words"]), (" | URL: " + " | ".join(_df(u, defang) for u in x["urls"])) if x["urls"] else ""))
    _render_mcfg(rep.get("malcfg"), a, compact, defang)   # v99.19 [A1]
    if rep.get("ctph") and not compact:
        a("CTPH   : %s%s" % (rep["ctph"], " (sampel %s pertama)" % _human(CTPH_SAMPLE) if rep["size"] > CTPH_SAMPLE else ""))


def _score_v97(rep: dict, add) -> None:
    mo, dn = rep.get("macho"), rep.get("dotnet")
    if mo:
        if any(s["prot"][1:] == "WX" for s in mo["segments"]):
            add(1, "segmen Mach-O W+X")
        if any(s["ent"] > 7.2 and s["fsize"] > 16384 and s["name"] != "__LINKEDIT" for s in mo["segments"]) and not mo["encrypted"]:
            add(1, "segmen Mach-O berentropi tinggi")
    if dn and dn["obf"]:
        add(2, "metadata .NET menunjukkan obfuskasi")
    x = rep.get("xor") or []
    if x:
        strong = any(w_ in ("This program cannot be run", "https://", "http://", "powershell", "cmd.exe") for r_ in x for w_ in r_["words"])
        add(3 if strong else 1, "kata kunci tersembunyi di balik dekode satu-byte")


# ----------------------------- keluarga sampel (folder) ---------------------


def _families(items: list[dict], fuzzy: bool) -> list[dict]:
    fam: list[dict] = []
    for key, label in (("imphash", "imphash sama"), ("rich", "rich header sama"), ("macho_uuid", "UUID Mach-O sama")):
        g: dict[str, list[str]] = {}
        for it in items:
            if it.get(key):
                g.setdefault(it[key], []).append(it["rel"])
        fam += [{"basis": label, "members": v} for v in g.values() if len(v) > 1]
    if fuzzy:
        cand = [it for it in items if it.get("ctph")][:150]
        seen: set[int] = set()
        for i, x in enumerate(cand):
            if i in seen:
                continue
            grp = [x["rel"]]
            for j in range(i + 1, len(cand)):
                if j not in seen and cand[j]["sha256"] != x["sha256"] and ctph_compare(x["ctph"], cand[j]["ctph"]) >= 70:
                    grp.append(cand[j]["rel"])
                    seen.add(j)
            if len(grp) > 1:
                fam.append({"basis": "CTPH >= 70", "members": grp})
    return fam[:12]


# ----------------------------- laporan Markdown -----------------------------


# ---------------------------------------------------------------------------
# v99.7 [B4]: laporan HTML tunggal offline (tanpa skrip / gaya / font / gambar dari luar; semua nilai di-escape).
# ---------------------------------------------------------------------------

_HTML_CSS = """
:root{--bg:#fff;--fg:#1d2330;--mut:#5b6577;--card:#f4f6fa;--line:#d9dee8;--acc:#2f5bd8;--hi:#c62828;--mid:#d9822b;--lo:#b59b00;--ok:#2e7d32}
@media (prefers-color-scheme:dark){:root{--bg:#12151c;--fg:#e4e8f0;--mut:#9aa4b8;--card:#1b202b;--line:#2c3446;--acc:#7da2ff;--hi:#ff6b6b;--mid:#ffa94d;--lo:#e6c94a;--ok:#6fcf7a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:18px 20px;border-bottom:1px solid var(--line)}h1{margin:0 0 4px;font-size:20px;word-break:break-all}.sub{color:var(--mut)}
nav{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 20px;display:flex;gap:14px;flex-wrap:wrap}
nav a{color:var(--acc);text-decoration:none}nav a:hover{text-decoration:underline}
main{padding:0 20px 40px;max-width:1200px}section{margin-top:26px}h2{font-size:16px;margin:0 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--mut);font-weight:600}
.wrap{overflow-x:auto}code,pre,.mono{font:12.5px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace}code{word-break:break-all}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-weight:700;color:#fff}.TINGGI{background:var(--hi)}.SEDANG{background:var(--mid)}.RENDAH{background:var(--lo)}.TANPA{background:var(--ok)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0}.warn{border-left:4px solid var(--mid)}.bal{border-left:4px solid var(--ok)}
input[type=search]{width:100%;max-width:420px;padding:7px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);margin:0 0 8px}
.pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;max-height:70vh;overflow:auto}.ln{white-space:pre-wrap;word-break:break-word}.ln.hit{background:rgba(255,200,0,.25)}
.mut{color:var(--mut)}ul{margin:4px 0;padding-left:20px}.kv td:first-child{width:160px;color:var(--mut)}
"""

_HTML_JS = """
(function(){
function flt(inp,rows,cnt){var q=inp.value.toLowerCase(),n=0;for(var i=0;i<rows.length;i++){var t=rows[i].textContent.toLowerCase();var ok=!q||t.indexOf(q)>-1;rows[i].style.display=ok?'':'none';if(ok)n++;}if(cnt)cnt.textContent=n+' / '+rows.length;}
var a=document.getElementById('q-imp');if(a){var r=document.querySelectorAll('#t-imp tbody tr'),c=document.getElementById('c-imp');a.addEventListener('input',function(){flt(a,r,c)});flt(a,r,c);}
var b=document.getElementById('q-txt');if(b){var l=document.querySelectorAll('#txt .ln'),c2=document.getElementById('c-txt');b.addEventListener('input',function(){var q=b.value.toLowerCase(),n=0;for(var i=0;i<l.length;i++){var ok=!q||l[i].textContent.toLowerCase().indexOf(q)>-1;l[i].style.display=ok?'':'none';l[i].className=(q&&ok)?'ln hit':'ln';if(ok)n++;}c2.textContent=n+' / '+l.length;});}
var s=document.getElementById('q-str');if(s){var r3=document.querySelectorAll('#ioc-list li'),c3=document.getElementById('c-str');s.addEventListener('input',function(){flt(s,r3,c3)});}
})();
"""


def _hesc(x) -> str:
    import html as _h
    return _h.escape(str(x), quote=True)


def triage_html(path, defang: bool = True, rep: dict | None = None) -> str:
    """Laporan HTML mandiri: ringkasan + skor, bagian / segmen, impor (bisa difilter), IOC dan artefak, kemampuan, perhatian, dan laporan teks penuh
    yang bisa dicari. Tanpa sumber luar. Hanya-baca; file sampel tidak dijalankan."""
    rep = rep or triage(path)
    E = _hesc
    ind = rep.get("ind") or {}
    pe, elf, mo = rep.get("pe"), rep.get("elf"), rep.get("macho")
    lvl = str(rep.get("level", ""))
    badge = lvl.split()[0] if lvl else "RENDAH"
    out: list[str] = []
    w = out.append

    def table(head, rows, cls=""):
        t = ["<div class=\"wrap\"><table%s><thead><tr>%s</tr></thead><tbody>" % ((" " + cls) if cls else "", "".join("<th>%s</th>" % E(h) for h in head))]
        for r_ in rows:
            t.append("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r_))
        t.append("</tbody></table></div>")
        return "".join(t)

    w("<!doctype html><html lang=\"id\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    w("<title>REA v%s - %s</title><style>%s</style></head><body>" % (E(VERSION), E(rep["name"]), _HTML_CSS))
    w("<header><h1>%s</h1><div class=\"sub\">%s &middot; %s &middot; REA v%s</div></header>" % (E(rep["name"]), E(rep["kind"]), E(_human(rep["size"])), E(VERSION)))
    nav = [("ringkasan", "Ringkasan"), ("bagian", "Bagian"), ("impor", "Impor"), ("ioc", "IOC &amp; artefak"), ("kemampuan", "Kemampuan"), ("teks", "Laporan teks")]
    w("<nav>%s</nav><main>" % "".join("<a href=\"#%s\">%s</a>" % (a_, b_) for a_, b_ in nav))

    # --- ringkasan
    w("<section id=\"ringkasan\"><h2>Ringkasan</h2>")
    w("<p><span class=\"badge %s\">%s</span> &nbsp; skor heuristik <b>%s</b> <span class=\"mut\">(petunjuk dari fakta terukur, bukan vonis)</span></p>" % (E(badge), E(lvl), E(rep["score"])))
    kv = [("SHA-256", rep["sha256"]), ("SHA-1", rep["sha1"]), ("MD5", rep["md5"]), ("Entropi", "%.2f / 8.00" % rep["entropy"])]
    if rep.get("ctph"):
        kv.append(("CTPH", rep["ctph"]))
    if pe and not pe.get("broken"):
        kv += [("Arsitektur PE", "%s, subsystem %s" % (pe.get("arch"), pe.get("subsys"))), ("Entry point", pe.get("entry")), ("Cap waktu", pe.get("stamp")), ("imphash", pe.get("imphash") or "-")]
    if elf:
        hd = elf.get("hard")
        kv.append(("ELF", "%d-bit %s, %s, %s" % (elf["bits"], elf["endian"], elf["type"], elf["arch"])))
        if hd:
            kv.append(("Mitigasi ELF", "PIE %s | RELRO %s | NX %s | canary %s | FORTIFY %s" % (hd["pie"], hd["relro"], hd["nx"], "ada" if hd["canary"] else "-", hd["fortify"] or "-")))
    if mo:
        kv.append(("Mach-O", "%s %s-bit %s" % (mo["arch"], mo["bits"], mo["type"])))
    w("<div class=\"wrap\"><table class=\"kv\"><tbody>%s</tbody></table></div>" % "".join("<tr><td>%s</td><td><code>%s</code></td></tr>" % (E(k), E(v)) for k, v in kv))
    if rep.get("why"):
        w("<div class=\"card\"><b>Alasan skor</b><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["why"]))
    if rep.get("balance"):
        w("<div class=\"card bal\"><b>Faktor penyeimbang</b> <span class=\"mut\">(lazim pada file sah; bukan jaminan aman)</span><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["balance"]))
    if rep.get("warn"):
        w("<div class=\"card warn\"><b>Perhatian</b><ul>%s</ul></div>" % "".join("<li>%s</li>" % E(_clean(x)) for x in rep["warn"][:40]))
    w("</section>")

    # --- bagian
    w("<section id=\"bagian\"><h2>Bagian / segmen</h2>")
    if pe and not pe.get("broken") and pe.get("sections"):
        w(table(["Nama", "VA", "Ukuran virtual", "Ukuran file", "Flag", "Entropi", "MD5"],
                [["<code>%s</code>" % E(x["name"]), "0x%X" % x["va"], E(_human(x["vsize"])), E(_human(x["rsize"])), E(x["flags"]), "%.2f" % x["ent"], "<code>%s</code>" % E(x.get("md5", ""))] for x in pe["sections"]]))
    elif elf and elf.get("sections"):
        w(table(["Nama", "Ukuran", "Flag", "Entropi"], [["<code>%s</code>" % E(x["name"] or "?"), E(_human(x["size"])), E(x["flags"]), "%.2f" % x["ent"]] for x in elf["sections"][:60] if x["name"]]))
    elif mo and mo.get("segments"):
        w(table(["Segmen", "Proteksi", "Ukuran file", "Entropi"], [["<code>%s</code>" % E(x["name"]), E(x["prot"]), E(_human(x["fsize"])), "%.2f" % x["ent"]] for x in mo["segments"]]))
    else:
        w("<p class=\"mut\">Tidak ada tabel bagian untuk jenis berkas ini.</p>")
    w("</section>")

    # --- impor
    rows: list[list[str]] = []
    if pe and not pe.get("broken") and pe.get("imports"):
        for dll, fns in pe["imports"].items():
            for f_ in (fns if isinstance(fns, (list, tuple)) else [fns]):
                rows.append([E(dll), "<code>%s</code>" % E(f_[0] if isinstance(f_, (list, tuple)) and f_ else f_)])
    elif elf and elf.get("dyn") and elf["dyn"].get("imports"):
        lib = ", ".join(elf["dyn"].get("needed", [])[:6]) or "(dinamis)"
        rows = [[E(lib), "<code>%s</code>" % E(x)] for x in elf["dyn"]["imports"]]
    elif mo and mo.get("imports"):
        rows = [[E("Mach-O"), "<code>%s</code>" % E(x)] for x in mo["imports"]]
    w("<section id=\"impor\"><h2>Impor (<span id=\"c-imp\">%d</span>)</h2>" % len(rows))
    if rows:
        w("<input type=\"search\" id=\"q-imp\" placeholder=\"Filter: nama DLL atau fungsi...\">")
        w(table(["Pustaka", "Fungsi"], rows[:6000], "id=\"t-imp\""))
        if len(rows) > 6000:
            w("<p class=\"mut\">Dipotong: 6000 dari %d baris.</p>" % len(rows))
    else:
        w("<p class=\"mut\">Tidak ada impor terbaca.</p>")
    w("</section>")

    # --- IOC & artefak
    items: list[tuple[str, str]] = []
    for lab, key, dfg in (("URL", "urls", True), ("IP kandidat", "ips", True), ("Email", "emails", True), ("Registry", "reg", False), ("Path", "paths", False)):
        for x in ind.get(key, []) or []:
            items.append((lab, _df(x, defang) if dfg else x))
    for x in ind.get("secrets", []) or []:
        items.append(("Kredensial (disamarkan)", x))
    for x in ind.get("secrets_typed", []) or []:
        items.append(("Rahasia berformat (disamarkan)", x))
    nt = ind.get("net") or {}
    for lab, key in (("User-Agent", "ua"), ("HTTP", "http"), ("Host", "hosts"), ("Header", "hdrs"), ("DNS ter-encode", "dns"), ("Proxy", "proxy"), ("Named pipe", "pipes")):
        for x in nt.get(key, []) or []:
            items.append((lab, _df(x, defang) if key in ("hosts", "dns") else x))
    if nt.get("certs"):
        items.append(("Sertifikat PEM", "%d tertanam" % nt["certs"]))
    for x in ind.get("pdb", []) or []:
        items.append(("Jejak PDB", x))
    cm = rep.get("com")
    if cm:
        for g in cm.get("groups", []):
            items.append(("Objek COM", "%s: %s" % (g["group"], ", ".join(g["names"]))))
    w("<section id=\"ioc\"><h2>IOC &amp; artefak (<span id=\"c-str\">%d</span>)</h2>" % len(items))
    if items:
        w("<input type=\"search\" id=\"q-str\" placeholder=\"Cari IOC / artefak...\"><ul id=\"ioc-list\" class=\"mono\">%s</ul>" % "".join("<li><b>%s</b>: <code>%s</code></li>" % (E(a_), E(_clean(b_))) for a_, b_ in items[:600]))
    else:
        w("<p class=\"mut\">Tidak ada IOC terdeteksi.</p>")
    w("</section>")

    # --- kemampuan
    caps = ind.get("caps") or {}
    w("<section id=\"kemampuan\"><h2>Indikasi kemampuan</h2>")
    if caps:
        w("<ul>%s</ul>" % "".join("<li>%s%s</li>" % (E(_clean(_cap_text(ind, c_, h_))), (" <span class=\"mut\">(%s)</span>" % E(ATTACK[c_])) if c_ in ATTACK and _cap_strong(ind, c_) else "") for c_, h_ in caps.items()))
        w("<p class=\"mut\">Petunjuk dari nama API / string, bukan bukti perilaku.</p>")
    else:
        w("<p class=\"mut\">Tidak ada indikasi.</p>")
    w("</section>")

    # --- teks penuh
    txt = _render(rep, False, defang)
    lines = txt.splitlines()[:4000]
    w("<section id=\"teks\"><h2>Laporan teks penuh (<span id=\"c-txt\">%d</span>)</h2><input type=\"search\" id=\"q-txt\" placeholder=\"Cari di laporan...\">" % len(lines))
    w("<div class=\"pre mono\" id=\"txt\">%s</div></section>" % "".join("<div class=\"ln\">%s</div>" % E(x) for x in lines))
    w("</main><script>%s</script></body></html>" % _HTML_JS)
    return "".join(out)


def triage_html_file(path, out=None, defang: bool = True) -> str:
    """Tulis laporan HTML ke `out` (bawaan: <nama>.rea.html di folder kerja); kembalikan path-nya."""
    rep = triage(path)
    target = Path(out) if out else Path.cwd() / (Path(path).name + ".rea.html")
    target.write_text(triage_html(path, defang, rep=rep), encoding="utf-8")
    return str(target)


def triage_md(path, defang: bool = True) -> str:
    """Laporan Markdown siap simpan / tempel: ringkasan, skor, kemampuan, IOC, draf YARA. Hanya-baca."""
    try:
        rep = triage(path)
    except Exception as e:
        return "# Triase gagal\n\n`%s: %s`" % (type(e).__name__, str(e)[:120])
    ind = rep["ind"]
    L = ["# Laporan Triase REA v%s: %s" % (VERSION, _clean(rep["name"])), "",
         "| Hal | Nilai |", "|---|---|", "| Jenis | %s |" % _clean(rep["kind"]).replace("|", "/"), "| Ukuran | %s |" % _human(rep["size"]),
         "| SHA-256 | `%s` |" % rep["sha256"], "| SHA-1 | `%s` |" % rep["sha1"], "| MD5 | `%s` |" % rep["md5"],
         "| Entropi | %.2f / 8.00 |" % rep["entropy"]]
    if rep.get("ctph"):
        L.append("| CTPH | `%s` |" % rep["ctph"])
    pe = rep.get("pe")
    if pe and not pe.get("broken") and pe.get("imphash"):
        L.append("| imphash | `%s` |" % pe["imphash"])
    L += ["", "## Skor heuristik: %d (%s)" % (rep["score"], rep["level"]), "", "_Petunjuk dari fakta terukur, bukan vonis._", ""]
    L += ["- " + _clean(x) for x in rep["why"]] or ["- tidak ada tanda"]
    if rep.get("balance"):
        L += ["", "**Faktor penyeimbang** (lazim pada file sah; bukan jaminan aman, tidak mengurangi skor): " + _clean("; ".join(rep["balance"]))]
    if ind["caps"]:
        L += ["", "## Indikasi kemampuan", ""]
        for cap, hit in ind["caps"].items():
            L.append("- **%s**%s" % (_clean(_cap_text(ind, cap, hit)), (" (%s)" % ATTACK[cap]) if cap in ATTACK and _cap_strong(ind, cap) else ""))
    if rep["warn"]:
        L += ["", "## Perhatian", ""] + ["- " + _clean(x) for x in rep["warn"][:25]]
    for lab, key in (("URL", "urls"), ("IP kandidat", "ips"), ("Email", "emails"), ("Registry", "reg")):
        if ind[key]:
            L += ["", "## %s" % lab, ""] + ["- `%s`" % _clean(_df(x, defang)) for x in ind[key][:25]]
    if rep.get("pack"):
        L += ["", "## Kemasan / toolchain", ""] + ["- " + _clean(x) for x in rep["pack"]]
    go = rep.get("go")
    if go:
        L += ["", "## Fungsi Go (pclntab %s)" % _clean(go["ver"]), "", "- %d fungsi, %d paket, %d fungsi paket `main`%s" % (go["nfunc"], go["n_pkgs"], go["n_main"], " (dipotong)" if go["truncated"] else "")]
        L += ["- `%s`" % _clean(x["name"]) for x in go["main"][:30]]
        if go["third"]:
            L.append("- paket pihak ketiga: " + ", ".join("`%s` (%d)" % (_clean(p), c) for p, c in go["third"][:10]))
    for label, hint in rep.get("tools", []):
        L.append("- %s: %s" % (_clean(label), _clean(hint)))
    rl = rep.get("relab")
    if rl:
        L += ["", "## RE Lab", "", "%s, base %s: %d fungsi, %d panggilan API terpetakan, %d string dirujuk kode." % (rl["arch"], rl["image_base"], rl["n_functions"], rl["n_api_sites"], rl["n_strrefs"]), ""]
        if rl["functions"]:
            L += ["| Fungsi | VA | Ukuran | Skor | Kemampuan | API |", "|---|---|---|---|---|---|"]
            for f in rl["functions"][:10]:
                L.append("| %s | %s | %s | %d | %s | %s |" % (_clean(f["name"]).replace("|", "/"), f["va"], _human(f["size"]), f["score"], "; ".join(f["tags"]) or "-", ", ".join(x.split("!")[-1] for x in f["apis"][:6]) or "-"))
        L += ["- anti-analisis: %s x%d" % (_clean(x["technique"]), x["count"]) for x in rl["anti"]]
        L += ["- stack string: `%s` [%s]" % (_clean(x["text"]), x["tag"]) for x in rl["stack_strings"][:6]]
        L += ["- API hash: %s" % ", ".join(h["api"] for h in rl["api_hashes"][:6])] if rl["api_hashes"] else []
    L += ["", "## Draf YARA (WAJIB diuji terhadap file sah)", "", "```yara", yara_draft(rep), "```", "",
          "---", "REA v%s | by: %s | dihitung statis dari bytes file, tanpa menjalankannya." % (VERSION, AUTHOR)]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# v98 "RE Lab": bantuan reverse engineering statis untuk PE x86 / x64 (hanya-baca, pustaka standar, file tidak dijalankan).
#   - penemuan fungsi (entry + ekspor + target CALL + prolog) dan penamaan sub_XXXXXXXX;
#   - PETA PANGGILAN API per fungsi: CALL [IAT], thunk JMP [IAT], pointer IAT yang dimuat ke register;
#   - xref string: LEA [RIP+rel] (x64), PUSH / MOV imm32 (x86) -> fungsi mana yang memakai string apa;
#   - peringkat fungsi menarik berdasarkan kelompok kemampuan (injeksi, C2, kripto, persistensi, anti-debug, ...);
#   - anti-analisis tingkat instruksi: akses PEB / TEB, RDTSC, CPUID, INT 2D, SIDT / SLDT / STR, syscall langsung (SysWhispers /
#     Hell's Gate), Heaven's Gate, API hashing (ror13 gaya Metasploit block_api, tabel dihitung saat runtime);
#   - stack string (MOV byte / dword ke stack yang menyusun teks);
#   - stub entry point; disassembler OPSIONAL lewat capstone bila terpasang (tanpa capstone: tampilan hex).
# API baru: re_lab_path(path) -> dict, re_text(path), xref_text(path, query), disasm_text(path, at, count).
# ---------------------------------------------------------------------------
RELAB_MAX_CODE = 24 * 1024 * 1024    # total byte kode yang dipindai
RELAB_TIME = 8.0                     # detik; lewat dari ini analisis berhenti sebagian dan diberi catatan
RELAB_TOP = 12                       # fungsi menarik yang ditampilkan

_RE_X86 = {"x86", "x64"}


def _relab_hash_table() -> dict[int, str]:
    """Hash API gaya Metasploit block_api (modul + fungsi) dan ror13 fungsi-saja, dihitung saat runtime."""
    def ror(v, n):
        return ((v >> n) | (v << (32 - n))) & 0xFFFFFFFF

    def mod_h(name):
        h = 0
        for c in name.upper().encode("utf-16le") + b"\0\0":
            h = (ror(h, 13) + c) & 0xFFFFFFFF
        return h

    def fn_h(name):
        h = 0
        for c in name.encode() + b"\0":
            h = (ror(h, 13) + c) & 0xFFFFFFFF
        return h

    apis = {
        "kernel32.dll": "LoadLibraryA LoadLibraryW GetProcAddress VirtualAlloc VirtualAllocEx VirtualProtect VirtualFree WinExec ExitProcess ExitThread "
                        "CreateProcessA CreateProcessW CreateThread CreateRemoteThread WriteProcessMemory ReadProcessMemory OpenProcess "
                        "WaitForSingleObject CreateFileA CreateFileW WriteFile ReadFile CloseHandle GetModuleHandleA CreateNamedPipeA "
                        "ConnectNamedPipe Sleep GetTickCount TerminateProcess CreateToolhelp32Snapshot Process32First Process32Next "
                        "CreatePipe SetThreadContext GetThreadContext ResumeThread SuspendThread LocalAlloc HeapAlloc GlobalAlloc "
                        "WinExec GetComputerNameA GetVersionExA DeleteFileA MoveFileA CopyFileA FindFirstFileA FindNextFileA".split(),
        "ntdll.dll": "NtAllocateVirtualMemory NtProtectVirtualMemory NtWriteVirtualMemory NtCreateThreadEx NtQueueApcThread RtlMoveMemory "
                     "NtMapViewOfSection NtUnmapViewOfSection NtQueryInformationProcess LdrLoadDll LdrGetProcedureAddress RtlCreateUserThread".split(),
        "wininet.dll": "InternetOpenA InternetOpenW InternetConnectA InternetConnectW HttpOpenRequestA HttpSendRequestA InternetReadFile "
                       "InternetSetOptionA InternetOpenUrlA InternetCloseHandle".split(),
        "ws2_32.dll": "WSAStartup WSASocketA WSASocketW connect send recv closesocket socket bind listen accept gethostbyname getaddrinfo".split(),
        "advapi32.dll": "RegSetValueExA RegCreateKeyExA RegOpenKeyExA CreateServiceA OpenSCManagerA StartServiceA CryptAcquireContextA "
                        "OpenProcessToken AdjustTokenPrivileges LookupPrivilegeValueA".split(),
        "user32.dll": "MessageBoxA GetAsyncKeyState SetWindowsHookExA FindWindowA".split(),
        "winhttp.dll": "WinHttpOpen WinHttpConnect WinHttpOpenRequest WinHttpSendRequest WinHttpReceiveResponse WinHttpReadData".split(),
        "urlmon.dll": ["URLDownloadToFileA", "URLDownloadToFileW"],
        "shell32.dll": ["ShellExecuteA", "ShellExecuteW"],
    }
    tab: dict[int, str] = {}
    for dll, names in apis.items():
        mh = mod_h(dll)
        for n in names:
            tab[(mh + fn_h(n)) & 0xFFFFFFFF] = "%s!%s (block_api)" % (dll.rsplit(".", 1)[0], n)
            tab.setdefault(fn_h(n), "%s (ror13)" % n)
    return tab


_RELAB_HASH: dict[int, str] | None = None
_RELAB_HASH_RE = None

# kelompok kemampuan per fungsi: nama -> (himpunan API huruf kecil, minimal API berbeda, bobot, ATT&CK)
_RE_GROUPS = {
    "injeksi proses": ({"virtualallocex", "writeprocessmemory", "createremotethread", "ntwritevirtualmemory", "queueuserapc", "ntqueueapcthread",
                        "setthreadcontext", "getthreadcontext", "ntmapviewofsection", "ntunmapviewofsection", "resumethread", "openprocess",
                        "rtlcreateuserthread", "ntcreatethreadex", "ntallocatevirtualmemory", "virtualprotectex", "suspendthread"}, 3, 4, "T1055"),
    "jaringan / C2": ({"internetopen", "internetopenurl", "internetconnect", "internetreadfile", "httpopenrequest", "httpsendrequest", "winhttpopen",
                       "winhttpconnect", "winhttpsendrequest", "winhttpreaddata", "wsastartup", "socket", "connect", "send", "recv", "gethostbyname",
                       "getaddrinfo", "dnsquery", "urldownloadtofile", "internetsetoption", "winhttpopenrequest"}, 2, 2, "T1071"),
    "eksekusi proses": ({"winexec", "shellexecute", "shellexecuteex", "createprocess", "createprocessasuser", "createprocesswithlogon", "system", "_wsystem"}, 1, 1, "T1059"),
    "kripto / enkripsi": ({"cryptencrypt", "cryptdecrypt", "cryptacquirecontext", "cryptgenkey", "cryptderivekey", "cryptimportkey", "cryptcreatehash",
                           "bcryptencrypt", "bcryptdecrypt", "bcryptgeneratesymmetrickey", "bcryptopenalgorithmprovider", "bcryptimportkey"}, 2, 2, "T1486"),
    "enumerasi berkas": ({"findfirstfile", "findnextfile", "findfirstfileex", "getlogicaldrives", "getdrivetype", "getlogicaldrivestrings"}, 2, 1, "T1083"),
    "persistensi": ({"regsetvalue", "regcreatekey", "regopenkey", "createservice", "openscmanager", "startservice", "changeserviceconfig", "regsetkeyvalue"}, 2, 3, "T1547 / T1543"),
    "anti-debug / anti-VM": ({"isdebuggerpresent", "checkremotedebuggerpresent", "ntqueryinformationprocess", "outputdebugstring", "ntsetinformationthread",
                              "debugactiveprocess", "ntqueryobject", "getsystemfirmwaretable", "zwqueryinformationprocess"}, 2, 3, "T1622 / T1497"),
    "penyadap input / layar": ({"getasynckeystate", "setwindowshook", "getkeyboardstate", "getforegroundwindow", "getwindowtext", "getrawinputdata",
                                "registerrawinputdevices", "bitblt", "printwindow", "getclipboarddata"}, 2, 3, "T1056 / T1113"),
    "resolusi API dinamis": ({"getprocaddress", "loadlibrary", "ldrgetprocedureaddress", "ldrloaddll", "getmodulehandle", "loadlibraryex"}, 2, 1, "T1027.007"),
    "alokasi / unpack memori": ({"virtualalloc", "virtualprotect", "ntallocatevirtualmemory", "ntprotectvirtualmemory", "virtualallocex"}, 2, 2, "T1027.002 / T1620"),
    "token / hak istimewa": ({"openprocesstoken", "adjusttokenprivileges", "lookupprivilegevalue", "duplicatetokenex", "logonuser", "impersonateloggedonuser",
                              "cryptunprotectdata", "lsaenumeratelogonsessions"}, 2, 3, "T1134 / T1555"),
}

_RE_INTR = re.compile(r"(?i)https?://|ftp://|\\\\[a-z0-9_.$-]+\\|\b[a-z]:\\|\.(?:exe|dll|bat|ps1|vbs|js|sys|tmp|lnk|scr|cmd)\b|powershell|cmd(?:\.exe)?\s+/|software\\|currentversion|"
                      r"\\run\b|password|passwd|token|secret|api[_-]?key|wallet|bitcoin|\.onion|user-agent|mozilla/|%appdata%|%temp%|schtasks|reg\s+add|net\s+user|"
                      r"vssadmin|bcdedit|wevtutil|hkey_|/gate|/panel|ransom|decrypt|your files|mutex|"
                      r"\b(?:vmware|vbox|virtualbox|qemu|wireshark|procmon|procexp|x64dbg|ollydbg|fiddler|sandboxie|vmtoolsd)\b")


def _api_match(name: str, S: set) -> bool:
    n = name.split("!")[-1].lower()
    if n.startswith("zw"):
        n = "nt" + n[2:]
    if n in S:
        return True
    for suf in ("exa", "exw", "ex", "a", "w"):
        if n.endswith(suf) and n[:-len(suf)] in S:
            return True
    return False


def _api_tags(apis) -> tuple[list[str], int]:
    tags, score, have = [], 0, {}
    for g, (S, need, wt, _att) in _RE_GROUPS.items():
        n = sum(1 for a in apis if _api_match(a, S))
        have[g] = n
        if n >= need:
            tags.append(g)
            score += wt + min(n - need, 3)
    if have.get("jaringan / C2") and have.get("eksekusi proses"):
        tags.append("unduh & jalankan")
        score += 4
    if have.get("kripto / enkripsi") and have.get("enumerasi berkas"):
        tags.append("pola ransomware (kripto + enumerasi berkas)")
        score += 5
    return tags, score


def _pe_layout(d: bytes, pe: dict) -> dict | None:
    """Peta alamat PE: image base, bagian, IAT (VA slot -> 'dll!fungsi'), ekspor (VA -> nama). Mengembalikan None bila bukan x86 / x64."""
    if not pe or pe.get("broken") or pe.get("arch") not in _RE_X86:
        return None
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = pe["bits"] == 64
    base = struct.unpack_from("<Q", d, o + 24)[0] if is64 else struct.unpack_from("<I", d, o + 28)[0]
    size_img = struct.unpack_from("<I", d, o + 56)[0]
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    dd = o + (112 if is64 else 96)
    dirs = [struct.unpack_from("<II", d, dd + 8 * i) for i in range(min(nrva, 16)) if dd + 8 * i + 8 <= len(d)]
    secs = pe["sections"]

    def r2o(rva):
        for s in secs:
            rel = rva - s["va"]
            if 0 <= rel < max(s["vsize"], s["rsize"]):
                return (rel + s["rptr"]) if rel < s["rsize"] and rel + s["rptr"] < len(d) else None
        return None

    def cstr(off, lim=96):
        if off is None or off >= len(d):
            return ""
        e = d.find(b"\0", off, off + lim)
        return d[off:(e if e != -1 else off + lim)].decode("latin-1", "replace")

    step = 8 if is64 else 4
    iat: dict[int, str] = {}

    def walk(thunk_rva, iat_rva, dll):
        off = r2o(thunk_rva)
        k = 0
        while off is not None and off + step <= len(d) and k < 2000:
            v = struct.unpack_from("<Q" if is64 else "<I", d, off)[0]
            if v == 0:
                break
            if v & (1 << (63 if is64 else 31)):
                nm = "ord%d" % (v & 0xFFFF)
            else:
                no = r2o(v & 0x7FFFFFFF)
                nm = cstr(no + 2) if no is not None else "?"
            iat[base + iat_rva + k * step] = "%s!%s" % (dll, nm or "?")
            off += step
            k += 1

    try:
        if len(dirs) > 1 and dirs[1][0]:
            off, n = r2o(dirs[1][0]), 0
            while off is not None and off + 20 <= len(d) and n < 100:
                oft, _t, _f, name_rva, ft = struct.unpack_from("<IIIII", d, off)
                if not (oft or name_rva or ft):
                    break
                dll = cstr(r2o(name_rva)).lower()
                dll = dll[:-4] if dll.endswith(".dll") else dll
                walk(oft or ft, ft, dll or "?")
                off += 20
                n += 1
        if len(dirs) > 13 and dirs[13][0]:
            off, n = r2o(dirs[13][0]), 0
            while off is not None and off + 32 <= len(d) and n < 60:
                _at, name_rva, _h, iat_r, int_r = struct.unpack_from("<IIIII", d, off)
                if not (name_rva or int_r):
                    break
                dll = cstr(r2o(name_rva)).lower()
                dll = dll[:-4] if dll.endswith(".dll") else dll
                walk(int_r, iat_r, (dll or "?") + "(delay)")
                off += 32
                n += 1
    except (struct.error, IndexError, OverflowError):
        pass

    exports: dict[int, str] = {}
    try:
        if dirs and dirs[0][0]:
            eo = r2o(dirs[0][0])
            if eo is not None and eo + 40 <= len(d):
                nfun, nnam, a_rva, n_rva, o_rva = struct.unpack_from("<IIIII", d, eo + 20)
                ao, no_, oo = r2o(a_rva), r2o(n_rva), r2o(o_rva)
                names = {}
                for i in range(min(nnam, 3000)):
                    if no_ is None or oo is None or no_ + 4 * i + 4 > len(d) or oo + 2 * i + 2 > len(d):
                        break
                    ordn = struct.unpack_from("<H", d, oo + 2 * i)[0]
                    names[ordn] = cstr(r2o(struct.unpack_from("<I", d, no_ + 4 * i)[0]))
                for i in range(min(nfun, 4000)):
                    if ao is None or ao + 4 * i + 4 > len(d):
                        break
                    fr = struct.unpack_from("<I", d, ao + 4 * i)[0]
                    if fr and not (dirs[0][0] <= fr < dirs[0][0] + dirs[0][1]):   # bukan forwarder
                        exports[base + fr] = names.get(i) or "ord%d" % i
    except (struct.error, IndexError, OverflowError):
        pass

    xsecs = [s for s in secs if "X" in s["flags"] and s["rsize"] and s["rptr"] < len(d)]
    return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "exports": exports, "r2o": r2o,
            "entry_va": base + pe["entry"] if pe["entry"] else 0, "entry_off": r2o(pe["entry"]) if pe["entry"] else None}


def _va_off(L: dict, va: int):
    """VA -> offset berkas (None bila tidak ada di berkas)."""
    if va < L["base"]:
        return None
    return L["r2o"](va - L["base"])


def _rd_str(d: bytes, off: int) -> tuple[str, str] | None:
    """Baca string ASCII / UTF-16LE terawat di offset (minimal 4 karakter)."""
    if off is None or off < 0 or off + 8 > len(d):
        return None
    j = off
    lim = min(len(d), off + 200)
    while j < lim and (0x20 <= d[j] < 0x7F or d[j] in (9, 10, 13)):
        j += 1
    if j - off >= 4 and (j >= len(d) or d[j] == 0):
        return "a", d[off:j].decode("ascii", "replace")
    j = off
    chars = []
    while j + 1 < lim and d[j + 1] == 0 and (0x20 <= d[j] < 0x7F):
        chars.append(chr(d[j]))
        j += 2
    if len(chars) >= 4:
        return "w", "".join(chars)
    return None


def _str_tag(s: str) -> str:
    if re.search(r"(?i)https?://|ftp://|\.onion|/gate|/panel", s):
        return "URL"
    if re.search(r"(?i)hkey_|software\\|currentversion|\\run\b", s):
        return "registry"
    if re.search(r"(?i)powershell|cmd(\.exe)?\s+/|schtasks|reg\s+add|net\s+user|vssadmin|bcdedit|wevtutil", s):
        return "perintah"
    if re.search(r"(?i)\b(vmware|vbox|virtualbox|qemu|wireshark|procmon|procexp|x64dbg|ollydbg|fiddler|sandboxie|vmtoolsd)\b", s):
        return "alat analisis / VM"
    if re.search(r"(?i)password|passwd|token|secret|api[_-]?key|wallet|bitcoin", s):
        return "kredensial"
    if re.search(r"(?i)ransom|decrypt|your files", s):
        return "ransomware"
    if re.search(r"(?i)\\\\[a-z0-9_.$-]+\\|\b[a-z]:\\|\.(exe|dll|bat|ps1|vbs|js|sys|tmp|lnk|scr|cmd)\b|%appdata%|%temp%", s):
        return "path / berkas"
    return "menarik"


def _stack_strings(code: bytes, secva: int) -> list[tuple[int, str]]:
    """Gabungkan MOV byte / dword imm ke stack yang berurutan menjadi teks (teknik penyembunyi string)."""
    pats = [(re.compile(rb"\xC6\x45(.)([\x20-\x7e])", re.S), "b", 4), (re.compile(rb"\xC6\x44\x24(.)([\x20-\x7e])", re.S), "b", 5),
            (re.compile(rb"\xC6\x85(.{4})([\x20-\x7e])", re.S), "B", 7), (re.compile(rb"\xC7\x45(.)([\x20-\x7e]{4})", re.S), "b", 7),
            (re.compile(rb"\xC7\x44\x24(.)([\x20-\x7e]{4})", re.S), "b", 8)]
    out: list[tuple[int, str]] = []
    for rx, dk, ilen in pats:
        grp: list = []   # [pos_awal, pos_akhir, disp_berikut, teks]

        def flush():
            if grp and len(grp[3]) >= 5 and sum(c.isalnum() for c in grp[3]) >= max(4, int(len(grp[3]) * 0.6)):
                out.append((secva + grp[0], grp[3]))
            grp.clear()
        for m in rx.finditer(code):
            disp = struct.unpack("b" if dk == "b" else "<i", m.group(1))[0]
            ch = m.group(2).decode("ascii")
            if grp and m.start() - grp[1] <= 10 and disp == grp[2]:
                grp[1], grp[2], grp[3] = m.end(), disp + len(ch), grp[3] + ch
            else:
                flush()
                grp.extend([m.start(), m.end(), disp + len(ch), ch])
        flush()
    mv = re.compile(rb"\x48[\xB8-\xBF]([\x20-\x7e]{8})")
    cur: list = []
    for m in mv.finditer(code):
        ch = m.group(1).decode("ascii")
        if cur and m.start() - cur[1] <= 14:
            cur[1], cur[2] = m.end(), cur[2] + ch
        else:
            if cur and len(cur[2]) >= 12 and sum(c.isalnum() for c in cur[2]) >= int(len(cur[2]) * 0.6):
                out.append((secva + cur[0], cur[2]))
            cur = [m.start(), m.end(), ch]
    if cur and len(cur[2]) >= 12 and sum(c.isalnum() for c in cur[2]) >= int(len(cur[2]) * 0.6):
        out.append((secva + cur[0], cur[2]))
    return out


def _entry_stub(d: bytes, L: dict) -> dict:
    off = L["entry_off"]
    if off is None:
        return {"hex": "", "note": "entry point tidak ada di berkas (dipetakan ke luar data mentah)"}
    b = d[off:off + 24]
    note = ""
    if b[:2] == b"\x60\xBE":
        note = "PUSHAD + MOV ESI: pola stub pengepak klasik (UPX / sejenisnya)"
    elif b[:5] == b"\xE8\x00\x00\x00\x00":
        note = "CALL $+5 (get-PC): pola shellcode / loader / pengepak"
    elif b[:4] == b"\x48\x83\xEC\x28" and b[4:5] == b"\xE8":
        note = "awal CRT MSVC x64 (jalur normal)"
    elif b[:3] == b"\x55\x8B\xEC" or b[:5] == b"\x8B\xFF\x55\x8B\xEC":
        note = "bingkai standar x86 (kompilator biasa)"
    elif b[:6] == b"\xf3\x0f\x1e\xfa\x31\xed" or b[:2] == b"\x31\xed":
        note = "awal _start glibc / musl x86-64 (jalur normal)"
    elif b[:1] == b"\xE9":
        note = "langsung JMP ke rutin lain (CRT / protektor / entry tersembunyi)"
    elif b[:2] == b"\x31\xC0" or b[:2] == b"\x33\xC0":
        note = "diawali XOR reg,reg (bisa shellcode / kode buatan tangan)"
    return {"hex": " ".join("%02X" % x for x in b[:16]), "note": note}


def _re_lab(d: bytes, pe: dict | None, t0: float | None = None, L: dict | None = None, arch_label: str | None = None) -> tuple[dict | None, dict | None]:
    t0 = time.monotonic() if t0 is None else t0
    if L is None:
        L = _pe_layout(d, pe)
    if L is None:
        return None, None
    global _RELAB_HASH, _RELAB_HASH_RE
    base, is64, iat = L["base"], L["is64"], L["iat"]
    notes: list[str] = []
    execs, budget = [], RELAB_MAX_CODE
    for s in L["xsecs"]:
        n = min(s["rsize"], s["vsize"] or s["rsize"], budget, len(d) - s["rptr"])
        if n <= 0:
            continue
        budget -= n
        execs.append((base + s["va"], s["rptr"], bytes(d[s["rptr"]:s["rptr"] + n]), s["name"]))
    if not execs:
        return None, None
    if budget <= 0:
        notes.append("kode melebihi batas pindai %s; sebagian tidak dianalisis" % _human(RELAB_MAX_CODE))
    ranges = [(va, va + len(c)) for va, _o, c, _n in execs]

    def in_code(va):
        return any(a <= va < b for a, b in ranges)

    thunks: dict[int, str] = {}
    sites: list[tuple[int, str, str]] = []          # (va, api, jenis)
    edges: list[tuple[int, int]] = []               # (va panggilan, va target)
    strrefs: list[tuple[int, int]] = []             # (va kode, va string)
    anti: dict[str, list[int]] = {}
    sstr: list[tuple[int, str]] = []

    def hit(key, va):
        anti.setdefault(key, []).append(va)

    def reg(pat):
        return re.compile(pat, re.S)
    rx_jmpi, rx_calli = reg(rb"\xFF\x25(.{4})"), reg(rb"\xFF\x15(.{4})")
    rx_e8 = reg(rb"\xE8(.{4})")
    rx_ldp = reg(rb"[\x48\x4C]\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D](.{4})") if is64 else reg(rb"(?:\xA1|\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D])(.{4})")
    rx_lea = reg(rb"[\x48\x4C]\x8D[\x05\x0D\x15\x1D\x25\x2D\x35\x3D](.{4})") if is64 else None
    rx_push = None if is64 else reg(rb"[\x68\xB8-\xBF](.{4})")
    anti_pats = {
        "PEB / TEB dibaca langsung (BeingDebugged, NtGlobalFlag, daftar modul)": reg(
            rb"\x64\xA1\x30\x00\x00\x00|\x64\x8B[\x05\x0D\x15\x1D\x25\x2D\x35\x3D]\x30\x00\x00\x00|\x65[\x48\x4C]\x8B[\x04\x0C\x14\x1C\x24\x2C\x34\x3C]\x25\x60\x00\x00\x00"),
        "RDTSC / RDTSCP (pengukuran waktu)": reg(rb"\x0F\x31|\x0F\x01\xF9"),
        "CPUID (deteksi hypervisor / VM bila bit 31 ECX diperiksa)": reg(rb"\x0F\xA2"),
        "INT 2D (trik anti-debug)": reg(rb"\xCD\x2D[\x90\x40\xC3\xCC]"),
        "SIDT ke stack (deteksi VM ala Red Pill)": reg(rb"\x0F\x01\x4D.|\x0F\x01\x4C\x24."),
        "syscall langsung (stub ala SysWhispers / Hell's Gate, menghindari hook EDR)": reg(rb"\x4C\x8B\xD1\xB8.{4}.{0,14}?\x0F\x05"),
        "Heaven's Gate (pindah mode 64-bit dari proses WoW64)": reg(rb"\x6A\x33\xE8\x00\x00\x00\x00\x83\x04\x24\x05\xCB|\xEA.{4}\x33\x00"),
        "ROR 13 (kandidat API hashing)": reg(rb"\xC1[\xC8-\xCF]\x0D"),
    }
    stop = False
    for secva, _o, code, _nm in execs:
        if stop:
            break
        for m in rx_jmpi.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 6 + v) if is64 else v
            if tgt in iat:
                thunks[secva + m.start()] = iat[tgt]
                k_ = m.start()
                if k_ >= 4 and code[k_ - 4:k_] == b"\xf3\x0f\x1e\xfa":          # endbr64 + jmp [GOT] (.plt.sec / IBT)
                    thunks[secva + k_ - 4] = iat[tgt]
                elif k_ >= 1 and code[k_ - 1] == 0xF2:                           # bnd jmp [GOT]
                    thunks[secva + k_ - 1] = iat[tgt]
                    if k_ >= 5 and code[k_ - 5:k_ - 1] == b"\xf3\x0f\x1e\xfa":
                        thunks[secva + k_ - 5] = iat[tgt]
        for m in rx_calli.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 6 + v) if is64 else v
            if tgt in iat:
                sites.append((secva + m.start(), iat[tgt], "call"))
        for m in rx_ldp.finditer(code):
            v = struct.unpack("<i" if is64 else "<I", m.group(1))[0]
            tgt = (secva + m.start() + 7 + v) if is64 else v
            if tgt in iat:
                sites.append((secva + m.start(), iat[tgt], "ptr"))
        if rx_lea:
            for m in rx_lea.finditer(code):
                strrefs.append((secva + m.start(), secva + m.start() + 7 + struct.unpack("<i", m.group(1))[0]))
        else:
            for m in rx_push.finditer(code):
                v = struct.unpack("<I", m.group(1))[0]
                if base <= v < base + L["size_img"]:
                    strrefs.append((secva + m.start(), v))
        for key, rx in anti_pats.items():
            for m in rx.finditer(code):
                hit(key, secva + m.start())
                if len(anti[key]) >= 500:
                    break
        for m in rx_e8.finditer(code):
            rel = struct.unpack("<i", m.group(1))[0]
            va = secva + m.start()
            edges.append((va, va + 5 + rel))
            if len(edges) > 400000:
                break
        sstr.extend(_stack_strings(code, secva))
        if time.monotonic() - t0 > RELAB_TIME:
            notes.append("waktu analisis habis (%.0f dtk); hasil sebagian" % RELAB_TIME)
            stop = True
    # call E8 ke thunk -> panggilan API
    callee_edges = []
    for va, tgt in edges:
        if tgt in thunks:
            sites.append((va, thunks[tgt], "thunk"))
        elif in_code(tgt):
            callee_edges.append((va, tgt))
    # ---- penemuan fungsi ----
    starts: dict[int, str] = {}
    if L["entry_va"] and in_code(L["entry_va"]):
        starts[L["entry_va"]] = "entry"
    for va, nm in L["exports"].items():
        if in_code(va):
            starts.setdefault(va, "ekspor")
    tcount = collections.Counter(t for _v, t in callee_edges)
    for t in tcount:
        starts.setdefault(t, "call")
    pro = re.compile(rb"(?<=[\xCC\x90\xC3\x00])(?:\x55\x8B\xEC|\x8B\xFF\x55\x8B\xEC|\x48\x83\xEC[\x08-\x7f]|\x48\x89\x5C\x24|\x40\x53\x48\x83\xEC|\x48\x8B\xC4|\x4C\x8B\xDC|\x48\x81\xEC|\x40\x55\x48|\x48\x89\x6C\x24|\x48\x89\x74\x24)")
    for secva, _o, code, _nm in execs:
        for m in pro.finditer(code):
            if m.start() % 16 == 0:
                starts.setdefault(secva + m.start(), "prolog")
        if len(starts) > 60000:
            break
    for tva in thunks:
        starts.setdefault(tva, "thunk")
    fl = sorted(starts)
    ends = {}
    for i, s in enumerate(fl):
        sec_end = next((b for a, b in ranges if a <= s < b), s)
        ends[s] = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)

    def func_of(va):
        i = bisect.bisect_right(fl, va) - 1
        if i < 0:
            return None
        s = fl[i]
        return s if va < ends[s] else None
    F: dict[int, dict] = {}

    def fobj(s):
        if s not in F:
            nm = L["exports"].get(s) or ("start" if starts.get(s) == "entry" else ("thunk_" + thunks[s].split("!")[-1] if s in thunks else "sub_%08X" % s))
            F[s] = {"va": s, "name": nm, "size": ends.get(s, s) - s, "how": starts.get(s, "?"), "callers": 0, "callees": set(), "apis": {}, "strings": [], "anti": set()}
        return F[s]
    for va, tgt in callee_edges:
        cs = func_of(va)
        fobj(tgt)["callers"] += 1
        if cs is not None and cs != tgt:
            fobj(cs)["callees"].add(tgt)
    api_sites: dict[str, list[tuple[int, int]]] = {}
    for va, api, kind in sites:
        fs = func_of(va)
        if fs is not None and fs in thunks and kind != "ptr":
            continue
        if fs is not None:
            F_ = fobj(fs)
            F_["apis"][api] = F_["apis"].get(api, 0) + 1
        api_sites.setdefault(api, []).append((va, fs or 0))
    # ---- xref string ----
    sref: dict[int, dict] = {}
    seen_budget = 0
    for va, sva in strrefs:
        off = _va_off(L, sva)
        if off is None or off + 8 > len(d):
            continue
        if any(a <= sva < b for a, b in ranges):
            continue
        seen_budget += 1
        if seen_budget > 40000:
            break
        r = _rd_str(d, off)
        if not r:
            continue
        e = sref.setdefault(sva, {"va": sva, "kind": r[0], "text": r[1][:140], "funcs": set()})
        fs = func_of(va)
        if fs is not None:
            e["funcs"].add(fs)
            if len(fobj(fs)["strings"]) < 40:
                fobj(fs)["strings"].append(e["text"])
    # ---- API hashing ----
    if _RELAB_HASH is None:
        _RELAB_HASH = _relab_hash_table()
        _RELAB_HASH_RE = re.compile(b"|".join(re.escape(struct.pack("<I", h)) for h in _RELAB_HASH), re.S)
    hashes: dict[str, int] = {}
    scan_len = min(len(d), 8 * 1024 * 1024)
    for m in _RELAB_HASH_RE.finditer(d, 0, scan_len):
        nm = _RELAB_HASH.get(struct.unpack("<I", m.group(0))[0])
        if nm and nm not in hashes:
            hashes[nm] = m.start()
    ror_hits = len(anti.get("ROR 13 (kandidat API hashing)", []))
    hash_valid = len(hashes) >= 2
    # ---- anti-analisis -> fungsi ----
    for key, vas in anti.items():
        if key.startswith("ROR 13") and not hash_valid:
            continue
        for va in vas[:200]:
            fs = func_of(va)
            if fs is not None:
                fobj(fs)["anti"].add(key.split(" (")[0])
    # ---- peringkat ----
    ranked = []
    for s, f in F.items():
        tags, sc = _api_tags(list(f["apis"]))
        intr = [x for x in f["strings"] if _RE_INTR.search(x)]
        intr = list(dict.fromkeys(intr))
        sc += min(len(intr), 2) + (2 if len(f["anti"]) >= 2 else len(f["anti"]))
        if "syscall langsung" in " ".join(f["anti"]):
            sc += 3
        if sc >= 2:
            ranked.append((sc, s, tags, intr))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    top = []
    for sc, s, tags, intr in ranked[:RELAB_TOP]:
        f = F[s]
        top.append({"va": "0x%X" % s, "name": f["name"], "size": f["size"], "callers": f["callers"], "callees": len(f["callees"]), "score": sc,
                    "tags": tags, "apis": sorted(f["apis"])[:14], "strings": [_clean(x)[:90] for x in list(dict.fromkeys(intr or f["strings"]))[:4]], "anti": sorted(f["anti"])})
    refs = sorted(sref.values(), key=lambda e: (0 if _RE_INTR.search(e["text"]) else 1, -len(e["funcs"]), e["va"]))
    refs_out = []
    for e in refs[:30]:
        if not _RE_INTR.search(e["text"]) and len(refs_out) >= 8:
            break
        refs_out.append({"va": "0x%X" % e["va"], "kind": e["kind"], "tag": _str_tag(e["text"]), "text": _clean(e["text"]),
                         "funcs": ["0x%X" % x for x in sorted(e["funcs"])[:4]]})
    ssout = []
    for va, s in sstr:
        if not any(x["text"] == s for x in ssout):
            ssout.append({"va": "0x%X" % va, "text": _clean(s)[:100], "tag": _str_tag(s)})
        if len(ssout) >= 12:
            break
    api_top = sorted(((a, len(v)) for a, v in api_sites.items()), key=lambda x: (-x[1], x[0]))
    anti_out = []
    for key, vas in anti.items():
        if key.startswith("ROR 13") and not hash_valid:
            continue
        if key.startswith("RDTSC") and len(vas) < 2:
            continue
        if key.startswith("CPUID") and len(vas) < 1:
            continue
        anti_out.append({"technique": key, "count": len(vas), "first": "0x%X" % vas[0]})
    info = {
        "arch": arch_label or "%s (%d-bit)" % (pe["arch"], pe["bits"]), "image_base": "0x%X" % base, "n_functions": len(fl), "n_api_sites": len(sites),
        "n_iat": len(iat), "n_thunks": len(thunks), "n_strrefs": len(sref), "entry": "0x%X" % L["entry_va"] if L["entry_va"] else "", "entry_stub": _entry_stub(d, L),
        "functions": top, "api_top": api_top[:15], "string_refs": refs_out, "stack_strings": ssout, "anti": anti_out,
        "api_hashes": [{"api": k, "offset": "0x%X" % v} for k, v in list(hashes.items())[:12]] if hash_valid else [], "ror13_ops": ror_hits, "notes": notes,
    }
    ctx = {"L": L, "F": F, "sites": api_sites, "sref": sref, "fl": fl, "thunks": thunks}
    _cfg_enrich(info, ctx, d)     # v99.13 [S3]; kunci baru info["cfg"], aditif
    _emu_enrich(info, ctx, d)     # v99.18 [S2]; kunci baru info["emu"], aditif
    return info, ctx


# ----------------------- v99.13 [S3]: CFG, blok dasar, kompleksitas siklomatik, loop (RE Lab x86 / x64) ------------
# Decoder PANJANG instruksi x86 / x86-64 murni Python (tanpa capstone) + penelusuran rekursif dari awal fungsi: blok dasar, sisi (JMP / Jcc / LOOP /
# fall-through), kompleksitas siklomatik (E - N + 2), loop alami (sisi balik), kandidat loop dekripsi (XOR / ADD / SUB / ROL / ROR / SHL / SHR ke memori
# di dalam loop kecil), dan kandidat control-flow flattening (satu blok dispatcher menerima banyak sisi balik). Statis murni; hanya pustaka standar.
# Batasan: lompatan tak langsung (jump table) dihitung sebagai sisi keluar bernama "switch" dan targetnya tidak diselesaikan; kode yang tidak bisa
# didecode menghentikan jalur itu saja (fungsi ditandai tidak lengkap); hasil adalah PETUNJUK. Kunci baru info["cfg"] (RE Lab), aditif.

CFG_TIME = 4.0                  # detik untuk seluruh analisis CFG satu berkas
CFG_MAX_FUNCS = 600             # fungsi yang dianalisis (yang teratas di peringkat + yang terbesar)
CFG_MAX_INSNS = 1_500_000       # total instruksi yang didecode
CFG_MAX_FUNC_INSNS = 40_000     # satu fungsi lebih panjang dari ini dipotong
CFG_MAX_LOOPS = 40              # loop yang dicatat per fungsi

(_M_NONE, _M_MODRM, _M_MODRM_I8, _M_MODRM_IZ, _M_I8, _M_IZ, _M_J8, _M_JMP8, _M_CALL, _M_JMP32, _M_RET, _M_RETI, _M_MOFFS, _M_ENTER,
 _M_G3_8, _M_G3_V, _M_FF, _M_LOOP, _M_MOVI, _M_INV, _M_HALT, _M_ESC, _M_PFX, _M_X, _M_FARPTR) = range(25)
(_K_NORM, _K_JMP, _K_JCC, _K_CALL, _K_RET, _K_JMPI, _K_CALLI, _K_HALT, _K_LOOP) = range(9)
_PFX_LEG = frozenset((0x66, 0x67, 0xF0, 0xF2, 0xF3, 0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65))
_ARITH_GRP = ("add", "or", "adc", "sbb", "and", "sub", "xor", "cmp")


def _mk_x1(is64: bool) -> list:
    t = [_M_NONE] * 256
    for op in range(0x40):
        lo = op & 7
        t[op] = _M_MODRM if lo < 4 else (_M_I8 if lo == 4 else (_M_IZ if lo == 5 else (_M_INV if is64 else _M_NONE)))
    t[0x0F] = _M_ESC
    for p in (0x26, 0x2E, 0x36, 0x3E, 0x64, 0x65, 0x66, 0x67, 0xF0, 0xF2, 0xF3):
        t[p] = _M_PFX
    for op in range(0x40, 0x50):
        t[op] = _M_PFX if is64 else _M_NONE
    t[0x60] = t[0x61] = _M_INV if is64 else _M_NONE
    t[0x62] = _M_X
    t[0x63] = _M_MODRM
    t[0x68], t[0x69], t[0x6A], t[0x6B] = _M_IZ, _M_MODRM_IZ, _M_I8, _M_MODRM_I8
    for op in range(0x70, 0x80):
        t[op] = _M_J8
    t[0x80], t[0x81], t[0x82], t[0x83] = _M_MODRM_I8, _M_MODRM_IZ, (_M_INV if is64 else _M_MODRM_I8), _M_MODRM_I8
    for op in range(0x84, 0x90):
        t[op] = _M_MODRM
    t[0x9A] = _M_INV if is64 else _M_FARPTR
    for op in range(0xA0, 0xA4):
        t[op] = _M_MOFFS
    t[0xA8], t[0xA9] = _M_I8, _M_IZ
    for op in range(0xB0, 0xB8):
        t[op] = _M_I8
    for op in range(0xB8, 0xC0):
        t[op] = _M_MOVI
    t[0xC0] = t[0xC1] = _M_MODRM_I8
    t[0xC2], t[0xC3] = _M_RETI, _M_RET
    t[0xC4] = t[0xC5] = _M_X
    t[0xC6], t[0xC7], t[0xC8] = _M_MODRM_I8, _M_MODRM_IZ, _M_ENTER
    t[0xCA], t[0xCB], t[0xCC], t[0xCD] = _M_RETI, _M_RET, _M_HALT, _M_I8
    t[0xCE] = _M_INV if is64 else _M_NONE
    t[0xCF] = _M_RET
    for op in range(0xD0, 0xD4):
        t[op] = _M_MODRM
    t[0xD4] = t[0xD5] = _M_INV if is64 else _M_I8
    t[0xD6] = _M_INV if is64 else _M_NONE
    for op in range(0xD8, 0xE0):
        t[op] = _M_MODRM
    for op in range(0xE0, 0xE4):
        t[op] = _M_LOOP
    for op in range(0xE4, 0xE8):
        t[op] = _M_I8
    t[0xE8], t[0xE9] = _M_CALL, _M_JMP32
    t[0xEA] = _M_INV if is64 else _M_FARPTR
    t[0xEB] = _M_JMP8
    t[0xF4] = _M_HALT
    t[0xF6], t[0xF7], t[0xFE], t[0xFF] = _M_G3_8, _M_G3_V, _M_MODRM, _M_FF
    return t


_X1_32, _X1_64 = _mk_x1(False), _mk_x1(True)
_X2_NONE = frozenset((0x05, 0x06, 0x07, 0x08, 0x09, 0x0E, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x37, 0x77, 0xA0, 0xA1, 0xA2, 0xA8, 0xA9, 0xAA,
                      0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0xCE, 0xCF))
_X2_I8 = frozenset((0x70, 0x71, 0x72, 0x73, 0xA4, 0xAC, 0xBA, 0xC2, 0xC4, 0xC5, 0xC6, 0x0F))
_X2_BAD = frozenset((0x04, 0x0A, 0x0C, 0x24, 0x25, 0x26, 0x27, 0x36, 0x39, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0xA6, 0xA7))


def _modrm_len(b: bytes, j: int, addr16: bool) -> int:
    """Panjang ModRM + SIB + disp; j = indeks byte ModRM. -1 bila terpotong."""
    if j >= len(b):
        return -1
    m = b[j]
    mod, rm = m >> 6, m & 7
    if addr16:
        return 1 + ((2 if rm == 6 else 0) if mod == 0 else (1 if mod == 1 else (2 if mod == 2 else 0)))
    n = 1
    if mod != 3 and rm == 4:
        if j + 1 >= len(b):
            return -1
        n += 1
        if mod == 0 and (b[j + 1] & 7) == 5:
            n += 4
    if mod == 0:
        if rm == 5:
            n += 4
    elif mod == 1:
        n += 1
    elif mod == 2:
        n += 4
    return n


def _x86_dec(b: bytes, i: int, is64: bool):
    """Satu instruksi di b[i:] -> (panjang, jenis, rel, bendera, mnemonik) atau None.
    bendera: 1 = operasi aritmetika / rotasi / geser, 2 = operan memori, 4 = menulis ke memori."""
    n0, nb = i, len(b)
    opsz16 = addr = False
    cnt = 0
    while i < nb and cnt < 14 and b[i] in _PFX_LEG:
        if b[i] == 0x66:
            opsz16 = True
        elif b[i] == 0x67:
            addr = True
        i += 1
        cnt += 1
    if i >= nb:
        return None
    rexw, rex = False, 0
    if is64 and 0x40 <= b[i] <= 0x4F:
        rex = b[i]
        rexw = bool(b[i] & 8)
        i += 1
        if i >= nb:
            return None
        if 0x40 <= b[i] <= 0x4F or b[i] in _PFX_LEG:      # REX tidak persis di depan opcode: CPU mengabaikannya; dihitung sebagai 1 instruksi sendiri
            return i - n0, _K_NORM, 0, 0, ""
    op = b[i]
    i += 1
    cls = (_X1_64 if is64 else _X1_32)[op]
    addr16 = addr and not is64
    izs = 2 if opsz16 else 4
    kind, rel, flags, mn = _K_NORM, 0, 0, ""

    def modrm(i_):
        k = _modrm_len(b, i_, addr16)
        return k

    if cls == _M_INV or cls == _M_PFX:
        return None
    if cls == _M_NONE:
        if op in (0xAA, 0xAB, 0xA4, 0xA5):
            flags = 4
    elif cls == _M_ESC:
        if i >= nb:
            return None
        op2 = b[i]
        i += 1
        if op2 in _X2_BAD:
            return None
        if op2 == 0x0B:
            kind = _K_HALT
        elif 0x80 <= op2 <= 0x8F:
            if i + 4 > nb:
                return None
            rel, kind, i = struct.unpack_from("<i", b, i)[0], _K_JCC, i + 4
        elif op2 in _X2_NONE:
            pass
        else:
            if op2 in (0x38, 0x3A):
                if i >= nb:
                    return None
                i += 1
            m0 = i
            k = modrm(i)
            if k < 0:
                return None
            i += k
            if op2 == 0x3A or op2 in _X2_I8:
                i += 1
            mod = b[m0] >> 6
            if mod != 3 and op2 != 0x1F and op2 != 0x18:
                flags |= 2
            if op2 in (0xA4, 0xA5, 0xAC, 0xAD):
                flags |= 1
                mn = "shd"
            elif op2 == 0xEF:
                if not (mod == 3 and ((b[m0] >> 3) & 7) | ((rex >> 2) & 1) << 3 == (b[m0] & 7) | (rex & 1) << 3):   # pxor reg,reg = nol-kan register, bukan dekripsi
                    flags |= 1
                    mn = "xor"
    elif cls in (_M_MODRM, _M_MODRM_I8, _M_MODRM_IZ, _M_G3_8, _M_G3_V, _M_FF):
        m0 = i
        k = modrm(i)
        if k < 0:
            return None
        i += k
        m = b[m0]
        mod, reg = m >> 6, (m >> 3) & 7
        if cls == _M_MODRM_I8 or (cls == _M_G3_8 and reg < 2):
            i += 1
        elif cls == _M_MODRM_IZ or (cls == _M_G3_V and reg < 2):
            i += izs
        if cls == _M_FF:
            if reg in (2, 3):
                kind = _K_CALLI
            elif reg in (4, 5):
                kind = _K_JMPI
        if mod != 3 and op != 0x8D:
            flags |= 2
        mem = mod != 3
        if op < 0x40 and (op & 7) < 6 and (op >> 3) != 7:
            flags |= 1
            mn = _ARITH_GRP[op >> 3]
            if op in (0x30, 0x31, 0x32, 0x33) and mod == 3 and (reg | ((rex >> 2) & 1) << 3) == ((m & 7) | (rex & 1) << 3):
                flags, mn = flags & ~1, ""     # xor reg,reg = nol-kan register, bukan operasi dekripsi
            if mem and (op & 2) == 0:
                flags |= 4
        elif op in (0x80, 0x81, 0x83) and reg != 7:
            flags |= 1
            mn = _ARITH_GRP[reg]
            if mem:
                flags |= 4
        elif op in (0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3) and reg in (0, 1, 4, 5):
            flags |= 1
            mn = ("rol", "ror", "", "", "shl", "shr")[reg]
            if mem:
                flags |= 4
        elif op in (0x88, 0x89, 0xC6, 0xC7) and mem:
            flags |= 4
    elif cls == _M_I8 or cls == _M_IZ:
        i += 1 if cls == _M_I8 else izs
        if op < 0x40 and (op & 7) in (4, 5) and (op >> 3) != 7:      # op AL / eAX, imm
            flags, mn = 1, _ARITH_GRP[op >> 3]
    elif cls == _M_J8 or cls == _M_JMP8 or cls == _M_LOOP:
        if i >= nb:
            return None
        rel = b[i] - 256 if b[i] >= 128 else b[i]
        kind = _K_JCC if cls == _M_J8 else (_K_JMP if cls == _M_JMP8 else _K_LOOP)
        i += 1
    elif cls == _M_CALL or cls == _M_JMP32:
        if i + 4 > nb:
            return None
        rel = struct.unpack_from("<i", b, i)[0]
        kind = _K_CALL if cls == _M_CALL else _K_JMP
        i += 4
    elif cls == _M_RET:
        kind = _K_RET
    elif cls == _M_RETI:
        kind = _K_RET
        i += 2
    elif cls == _M_HALT:
        kind = _K_HALT
    elif cls == _M_MOFFS:
        i += (8 if is64 else 4) if not (addr and not is64) else 2
        if op in (0xA2, 0xA3):
            flags = 6
        else:
            flags = 2
    elif cls == _M_ENTER:
        i += 3
    elif cls == _M_MOVI:
        i += 8 if (rexw and is64) else izs
    elif cls == _M_FARPTR:
        i += 6 if not opsz16 else 4
    elif cls == _M_X:       # VEX / EVEX (atau LES / LDS / BOUND pada mode 32-bit)
        if not is64 and (i >= nb or b[i] < 0xC0):
            k = modrm(i)
            if k < 0:
                return None
            i += k
            flags |= 2
        elif op == 0xC5:
            if i + 2 > nb:
                return None
            o2 = b[i + 1]
            i += 2
            if o2 != 0x77:
                k = modrm(i)
                if k < 0:
                    return None
                i += k + (1 if (o2 in _X2_I8 and o2 != 0x0F) else 0)
        elif op == 0xC4:
            if i + 3 > nb:
                return None
            mp, o2 = b[i] & 0x1F, b[i + 2]
            i += 3
            if not (mp == 1 and o2 == 0x77):
                k = modrm(i)
                if k < 0:
                    return None
                i += k + (1 if (mp == 3 or (mp == 1 and o2 in _X2_I8 and o2 != 0x0F)) else 0)
        else:               # EVEX 62
            if i + 4 > nb:
                return None
            mp, o2 = b[i] & 7, b[i + 3]
            i += 4
            k = modrm(i)
            if k < 0:
                return None
            i += k + (1 if (mp == 3 or (mp == 1 and o2 in _X2_I8 and o2 != 0x0F)) else 0)
    n = i - n0
    if n > 15 or i > nb:
        return None
    return n, kind, rel, flags, mn


def _cfg_func(d: bytes, L: dict, start: int, end: int, is64: bool, want_blocks: bool = False) -> dict | None:
    """CFG satu fungsi [start, end). None bila awal fungsi tidak bisa dibaca."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    code = d[off0:off0 + (end - start)]
    insns: dict = {}
    leaders = {start}
    work = [start]
    incomplete = trunc = False
    n_i = 0
    while work and not trunc:
        va = work.pop()
        while start <= va < end and va not in insns:
            r = _x86_dec(code, va - start, is64)
            if r is None:
                incomplete = True
                break
            n_i += 1
            if n_i > CFG_MAX_FUNC_INSNS:
                trunc = incomplete = True
                break
            insns[va] = r
            n, kind, rel = r[0], r[1], r[2]
            nxt = va + n
            if kind == _K_JMP:
                t = nxt + rel
                if start <= t < end:
                    leaders.add(t)
                    work.append(t)
                break
            if kind in (_K_JCC, _K_LOOP):
                t = nxt + rel
                if start <= t < end:
                    leaders.add(t)
                    work.append(t)
                leaders.add(nxt)
                va = nxt
                continue
            if kind in (_K_RET, _K_HALT, _K_JMPI):
                break
            va = nxt
    if not insns:
        return None
    # blok dasar
    order = sorted(insns)
    blocks: list = []                 # [va_awal, va_akhir_instruksi_terakhir]
    bidx: dict = {}
    cur = None
    for k, va in enumerate(order):
        r = insns[va]
        if cur is None or va in leaders or order[k - 1] + insns[order[k - 1]][0] != va:
            cur = [va, va]
            blocks.append(cur)
        cur[1] = va
        bidx[va] = len(blocks) - 1
        if r[1] in (_K_JMP, _K_JCC, _K_LOOP, _K_RET, _K_HALT, _K_JMPI):
            cur = None
    succ: list = [[] for _ in blocks]
    n_switch = n_exit_ext = 0
    for bi, (a, z) in enumerate(blocks):
        n, kind, rel = insns[z][0], insns[z][1], insns[z][2]
        nxt = z + n
        tg = []
        if kind == _K_JMP:
            tg = [z + n + rel]
        elif kind in (_K_JCC, _K_LOOP):
            tg = [z + n + rel, nxt]
        elif kind == _K_JMPI:
            n_switch += 1
        elif kind not in (_K_RET, _K_HALT):
            tg = [nxt]
        for t in tg:
            if t in bidx and bidx[t] != -1 and blocks[bidx[t]][0] == t:
                if bidx[t] not in succ[bi]:
                    succ[bi].append(bidx[t])
            else:
                n_exit_ext += 1
    N = len(blocks)
    E = sum(len(s) for s in succ)
    cc = E - N + 2 + n_switch
    # sisi balik (DFS iteratif)
    color = [0] * N
    back: list = []
    stack = [(0, 0)]
    color[0] = 1
    while stack:
        u, k = stack[-1]
        if k < len(succ[u]):
            stack[-1] = (u, k + 1)
            v = succ[u][k]
            if color[v] == 0:
                color[v] = 1
                stack.append((v, 0))
            elif color[v] == 1:
                back.append((u, v))
        else:
            color[u] = 2
            stack.pop()
    pred: list = [[] for _ in blocks]
    for u, ss in enumerate(succ):
        for v in ss:
            pred[v].append(u)
    loops: list = []
    for u, v in back[:CFG_MAX_LOOPS]:
        body = {v, u}
        todo = [u]
        while todo:
            x = todo.pop()
            if x == v:
                continue
            for p in pred[x]:
                if p not in body:
                    body.add(p)
                    todo.append(p)
        ni = ops = 0
        mem = store = False
        calls = 0
        mns: list = []
        for bi in body:
            a, z = blocks[bi]
            for va in order[bisect.bisect_left(order, a):bisect.bisect_right(order, z)]:
                r = insns[va]
                ni += 1
                if r[1] == _K_CALL or r[1] == _K_CALLI:
                    calls += 1
                if r[3] & 1:
                    ops += 1
                    if r[4] and r[4] not in mns:
                        mns.append(r[4])
                mem = mem or bool(r[3] & 2)
                store = store or bool(r[3] & 4)
        crypto = bool(ops and mem and store and ni <= 80 and calls <= 1 and any(m_ in ("xor", "add", "sub", "rol", "ror", "shl", "shr", "shd") for m_ in mns)
                      and any(m_ in ("xor", "rol", "ror", "shd") for m_ in mns))
        loops.append({"head": blocks[v][0], "insns": ni, "blocks": len(body), "ops": mns[:5], "crypto": crypto, "calls": calls})
    heads = collections.Counter(v for _u, v in back)
    flat = None
    if N >= 8 and heads:
        hv, hn = heads.most_common(1)[0]
        if hn >= max(6, N // 3):
            flat = {"head": blocks[hv][0], "back_edges": hn, "blocks": N}
    res = {"va": start, "blocks": N, "edges": E, "cc": max(cc, 1), "loops": loops, "insns": len(insns), "incomplete": incomplete, "switch": n_switch,
           "flat": flat, "trunc": trunc}
    if want_blocks:
        res["bl"] = [(blocks[i][0], blocks[i][1] + insns[blocks[i][1]][0], [blocks[j][0] for j in succ[i]], insns[blocks[i][1]][1]) for i in range(N)]
    return res


def _cfg_enrich(info: dict, ctx: dict, d: bytes) -> None:
    """Dipanggil di akhir _re_lab: info["cfg"] (kunci baru) + cc / blok / loop pada info["functions"]. Tidak pernah melempar."""
    try:
        L, F = ctx["L"], ctx["F"]
        is64 = L["is64"]
        xs = [(L["base"] + s["va"], L["base"] + s["va"] + max(s["vsize"], s["rsize"])) for s in L["xsecs"]]
        top_va = []
        for f in info.get("functions", []):
            try:
                top_va.append(int(f["va"], 16))
            except ValueError:
                pass
        todo = list(dict.fromkeys(top_va + [s for s, _f in sorted(F.items(), key=lambda kv: -kv[1]["size"])]))[:CFG_MAX_FUNCS]
        deadline = time.monotonic() + CFG_TIME
        done: dict = {}
        tot = bad = 0
        partial = False
        for s in todo:
            if time.monotonic() > deadline or tot > CFG_MAX_INSNS:
                partial = True
                break
            f = F.get(s)
            if not f or s in ctx["thunks"] or f["size"] < 2:
                continue
            e = s + f["size"]
            sec_end = next((b for a, b in xs if a <= s < b), e)
            r = _cfg_func(d, L, s, min(e, sec_end), is64)
            if r is None:
                bad += 1
                continue
            tot += r["insns"]
            if r["incomplete"]:
                bad += 1
            done[s] = r
        nm = lambda s: F[s]["name"] if s in F else "sub_%08X" % s
        for f in info.get("functions", []):
            try:
                r = done.get(int(f["va"], 16))
            except ValueError:
                r = None
            if r:
                f["cc"], f["blocks"], f["loops"] = r["cc"], r["blocks"], len(r["loops"])
        top = sorted(done.values(), key=lambda r: (-r["cc"], r["va"]))[:8]
        dec = []
        for s, r in sorted(done.items()):
            for lp in r["loops"]:
                if lp["crypto"] and len(dec) < 12:
                    dec.append({"func": "0x%X" % s, "name": _clean(nm(s)), "head": "0x%X" % lp["head"], "insns": lp["insns"], "ops": lp["ops"]})
        flat = [{"func": "0x%X" % s, "name": _clean(nm(s)), "head": "0x%X" % r["flat"]["head"], "back_edges": r["flat"]["back_edges"], "blocks": r["flat"]["blocks"]}
                for s, r in sorted(done.items()) if r["flat"]][:6]
        info["cfg"] = {
            "analyzed": len(done), "insns": tot, "incomplete": bad, "partial": partial, "loops": sum(len(r["loops"]) for r in done.values()),
            "switches": sum(1 for r in done.values() if r["switch"]),
            "top": [{"va": "0x%X" % r["va"], "name": _clean(nm(r["va"])), "blocks": r["blocks"], "edges": r["edges"], "cc": r["cc"], "loops": len(r["loops"]),
                     "insns": r["insns"]} for r in top],
            "decrypt_loops": dec, "flatten": flat,
        }
    except Exception as e:
        info["notes"].append("CFG gagal: %s" % type(e).__name__)


def _render_cfg(r: dict, a, compact: bool) -> None:
    c = r.get("cfg")
    if not c or not c["analyzed"]:
        return
    a("   CFG: %d fungsi / %d instruksi didecode, %d loop%s%s" % (c["analyzed"], c["insns"], c["loops"],
                                                                 (", %d fungsi tidak lengkap" % c["incomplete"]) if c["incomplete"] else "",
                                                                 " | TERPOTONG (batas waktu / ukuran)" if c["partial"] else ""))
    for x in c["decrypt_loops"][: (2 if compact else 8)]:
        a("   ! kandidat loop dekripsi: %s %s (loop @%s, %d instruksi; %s)" % (x["name"], x["func"], x["head"], x["insns"], "/".join(x["ops"])))
    for x in c["flatten"][: (1 if compact else 4)]:
        a("   ! kandidat control-flow flattening: %s %s (dispatcher @%s, %d sisi balik, %d blok)" % (x["name"], x["func"], x["head"], x["back_edges"], x["blocks"]))
    if compact:
        return
    for x in c["top"][:6]:
        a("   kompleksitas: %s %s cc=%d (%d blok, %d sisi, %d loop, %d instruksi)" % (x["name"], x["va"], x["cc"], x["blocks"], x["edges"], x["loops"], x["insns"]))


def cfg_text(path, at=None) -> str:
    """Ringkasan CFG (tanpa `at`) atau daftar blok dasar satu fungsi (at = 'entry' / 0xVA). CLI --cfg, API action 'cfg'."""
    try:
        info, ctx, err = _relab_any(*_cfg_read(path))
    except Exception as e:
        return "CFG gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if not info:
        return "CFG: %s." % (err or "tidak ada kode yang bisa dianalisis")
    if at is None:
        L: list = []
        _render_cfg(info, L.append, False)
        return "\n".join(L) if L else "CFG: tidak ada fungsi yang bisa dianalisis."
    Lx, fl = ctx["L"], ctx["fl"]
    try:
        va = Lx["entry_va"] if str(at).lower() == "entry" else int(str(at), 0)
    except ValueError:
        return "CFG: alamat tidak valid (pakai entry atau 0xVA)."
    i = bisect.bisect_right(fl, va) - 1
    if i < 0:
        return "CFG: tidak ada fungsi yang memuat 0x%X." % va
    s = fl[i]
    xs = [(Lx["base"] + x["va"], Lx["base"] + x["va"] + max(x["vsize"], x["rsize"])) for x in Lx["xsecs"]]
    sec_end = next((b for a_, b in xs if a_ <= s < b), s)
    e = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
    r = _cfg_func(_cfg_read(path)[0], Lx, s, e, Lx["is64"], want_blocks=True)
    if not r:
        return "CFG: fungsi di 0x%X tidak bisa didecode." % s
    out = ["Fungsi 0x%X: %d blok, %d sisi, cc=%d, %d loop%s%s" % (s, r["blocks"], r["edges"], r["cc"], len(r["loops"]), ", tidak lengkap" if r["incomplete"] else "",
                                                               ", %d switch (jump table tak diselesaikan)" % r["switch"] if r["switch"] else "")]
    heads = {lp["head"]: lp for lp in r["loops"]}
    for a_, z_, ss, k in r["bl"][:200]:
        lp = heads.get(a_)
        out.append("  0x%X-0x%X -> %s%s" % (a_, z_, ", ".join("0x%X" % x for x in ss) or "(keluar)",
                                           ("  [kepala loop: %d instruksi, ops %s%s]" % (lp["insns"], "/".join(lp["ops"]) or "-", ", KANDIDAT DEKRIPSI" if lp["crypto"] else "")) if lp else ""))
    if r["flat"]:
        out.append("  ! kandidat control-flow flattening: dispatcher @0x%X, %d sisi balik" % (r["flat"]["head"], r["flat"]["back_edges"]))
    return "\n".join(out)


def _cfg_read(path):
    f_, size = _open_regular(path)
    with f_:
        return f_.read(MAX_SCAN), size


# ----------------------- v99.19 [A1]: Malware Config Extractor otomatis (statis) -----------------------
# Mengambil konfigurasi tertanam (C2, mutex, kunci RC4 / XOR, campaign ID, user-agent, token bot) dari berkas, overlay PE, resource PE, resource terkelola
# .NET, dan wilayah berentropi tinggi. STATIS murni (sampel tidak dijalankan), hanya pustaka standar. Tiga lapis:
#   1) pola struktur: blok TLV beacon Cobalt Strike (XOR 0x2E / 0x69), token bot Telegram, webhook Discord, mutex Global\ / Local\, URL dead-drop,
#      objek JSON konfigurasi (kunci c2 / host / port / mutex / key / campaign / user_agent ...);
#   2) dekode wilayah terenkode: satu-byte (XOR / ADD / ROL), XOR kunci berulang, RC4, base64, zlib / gzip; kunci kandidat diambil dari string di sekitar
#      wilayah (plus kunci yang diberikan pengguna, plus kunci di awal blob gaya Remcos: byte pertama = panjang kunci). Dekode hanya diterima bila
#      keluarannya memuat butir konfigurasi; tebakan yang tidak menghasilkan apa-apa dibuang;
#   3) hasil perburuan XOR yang sudah ada (rep["xor"], rep["xor_multi"]) dipakai ulang untuk mendekode seluruh berkas.
# Kunci baru rep["malcfg"] (None bila tidak ada), baris "Konfigurasi malware" di laporan, peringatan; CLI `--config FILE [--key STR ...] [--json] [--raw]`;
# aksi API {"action": "config", "path": ..., "keys": [...]}; fungsi extract_config(path), config_text(path). Skor TIDAK berubah (aditif).
# Batasan: tanpa AES / RSA (kunci tidak bisa ditebak dari string); konfigurasi .NET yang dienkripsi per-string oleh obfuskator tidak dibongkar (butuh
# eksekusi / emulasi IL); format keluarga lain hanya tertangkap lewat pola umum. Hasil adalah PETUNJUK, bukan bukti keluarga; verifikasi dengan sampel nyata.

MCFG_TIME = 4.0                  # detik untuk seluruh ekstraksi satu berkas
MCFG_MAX_BLOBS = 12              # wilayah kandidat terenkode yang dicoba didekode
MCFG_MAX_BLOB = 2 << 20          # byte per wilayah yang dibaca
MCFG_MAX_KEYS = 300              # kandidat kunci (string sekitar wilayah) per wilayah
MCFG_MAX_ITEMS = 60              # butir konfigurasi yang dilaporkan
MCFG_DEC_MAX = 512 * 1024        # byte hasil dekode yang dipindai
MCFG_MAX_DEPTH = 2               # lapis dekode bertingkat (mis. base64 -> RC4)

_CS_PAT = {k: bytes(b ^ k for b in b"\x00\x01\x00\x01\x00\x02") for k in (0x2E, 0x69)}
_CS_FIELDS = {1: "beacon_type", 2: "port", 3: "sleep_ms", 4: "max_get_size", 5: "jitter", 7: "public_key", 8: "c2_server", 9: "user_agent", 10: "post_uri",
              26: "get_verb", 27: "post_verb", 29: "spawn_x86", 30: "spawn_x64", 32: "proxy", 37: "watermark", 40: "kill_date"}
_CS_STR = frozenset((8, 9, 10, 26, 27, 29, 30, 32))
_CS_BTYPE = {0: "HTTP", 1: "Hybrid HTTP+DNS", 2: "SMB", 4: "TCP", 8: "HTTPS", 16: "TCP bind"}

_MCFG_TG = re.compile(rb"(?<![\w:])\d{8,10}:AA[\w-]{33}(?![\w-])")
_MCFG_DISCORD = re.compile(rb"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d{17,20}/[\w-]{60,80}")
_MCFG_MUTEX = re.compile(rb"(?:Global|Local)\\[A-Za-z0-9_\-{}.]{4,64}")
_MCFG_MUTEX_SKIP = re.compile(r"^(?:MSCTF|CTF\.|SM0:|RasPbFile|windows_shell|ZonesCounterMutex|ZoneAttributeCacheCounterMutex|CPSharedMemory|BaseNamedObjects)", re.I)
_MCFG_DEAD = re.compile(rb"https?://(?:pastebin\.com/raw/|paste\.ee/r/|api\.telegram\.org/bot|transfer\.sh/|ipfs\.io/ipfs/|cdn\.discordapp\.com/attachments/)[\x21-\x7e]{3,160}", re.I)
_MCFG_DEAD_GH = re.compile(rb"https?://(?:raw|gist)\.githubusercontent\.com/[\x21-\x7e]{3,160}", re.I)   # terlalu umum di berkas polos (skema JSON, dokumentasi): hanya dari hasil dekode
_MCFG_URL = re.compile(rb"(?:https?|ftp|wss?)://[\x21-\x7e]{4,200}", re.I)
_MCFG_IPPORT = re.compile(rb"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d):\d{2,5}(?!\d)")
_MCFG_HOSTPORT = re.compile(rb"(?<![A-Za-z0-9.\-])[a-z0-9][a-z0-9\-]{1,40}(?:\.[a-z0-9\-]{1,40}){0,3}\.(?:com|net|org|info|biz|xyz|top|ru|cn|io|me|cc|tk|su|pw|club|online|site|dev|app|cloud):\d{2,5}(?!\d)", re.I)
_MCFG_KV = re.compile(r"(?m)^[ \t]*\"?([A-Za-z_][\w.\-& ]{0,30}?)\"?[ \t]*[=:][ \t]*\"?([^\r\n\"]{1,200}?)\"?[ \t]*,?[ \t]*$")
_MCFG_KEYSTR = re.compile(rb"[\x21-\x7e]{4,32}")
_MCFG_KEYSKIP = re.compile(rb"[\\/:*?<>|]|^\.|\.(?:dll|exe|sys|pdb|c|h|cpp|txt)$", re.I)
_MCFG_COMMON_KEYS = (b"key", b"password", b"admin", b"secret", b"123456", b"12345678")
_MCFG_TXT = bytes(range(48, 58)) + bytes(range(65, 91)) + bytes(range(97, 123)) + b" .:/-_=,;@\x00\r\n"   # huruf, angka, tanda baca umum (+ NUL, CR, LF)
_MCFG_B64 = re.compile(rb"[A-Za-z0-9+/=\r\n]{24,}")

# nama kunci konfigurasi -> jenis butir
_MCFG_NAMES = {
    "c2": "c2", "c&c": "c2", "cnc": "c2", "host": "c2", "hosts": "c2", "server": "c2", "servers": "c2", "domain": "c2", "domains": "c2", "url": "c2", "urls": "c2",
    "gate": "c2", "panel": "c2", "ip": "c2", "address": "c2", "remote": "c2", "callback": "c2", "c2_server": "c2", "c2_url": "c2", "server_url": "c2", "host_name": "c2",
    "port": "port", "ports": "port",
    "mutex": "mutex", "mtx": "mutex", "mutex_name": "mutex", "mutexname": "mutex",
    "key": "key", "aes_key": "key", "aeskey": "key", "rc4_key": "key", "rc4key": "key", "xor_key": "key", "xorkey": "key", "password": "key", "pass": "key",
    "secret": "key", "salt": "key", "encryption_key": "key",
    "campaign": "campaign", "campaign_id": "campaign", "campaignid": "campaign", "bot_id": "campaign", "botid": "campaign", "build": "campaign", "build_id": "campaign",
    "buildid": "campaign", "group": "campaign", "tag": "campaign", "affiliate": "campaign", "affiliate_id": "campaign", "botnet": "campaign",
    "user_agent": "user_agent", "useragent": "user_agent", "ua": "user_agent",
    "interval": "timing", "delay": "timing", "sleep": "timing", "timeout": "timing", "beacon_interval": "timing", "jitter": "timing",
    "install_path": "install", "install_name": "install", "install_dir": "install", "startup": "install", "persistence": "install", "filename": "install",
    "token": "token", "bot_token": "token", "webhook": "token", "chat_id": "token",
}
_MCFG_STRONG = frozenset(("c2", "token", "key", "mutex", "campaign"))


class _McfgCtx:
    """Penampung hasil + anggaran waktu satu ekstraksi."""

    def __init__(self, d: bytes, reveal: bool = False):
        self.d, self.reveal = d, reveal
        self.deadline = time.monotonic() + MCFG_TIME
        self.items: list = []
        self.seen: set = set()
        self.fam: list = []
        self.blobs = 0
        self.keys_tried = 0
        self.partial = False

    def left(self) -> bool:
        if time.monotonic() > self.deadline:
            self.partial = True
            return False
        return True

    def add(self, kind: str, value: str, how: str, src: str, conf: str = "sedang") -> bool:
        value = value.strip()
        if not value or (kind, value) in self.seen:
            return False
        if len(self.items) >= MCFG_MAX_ITEMS:
            self.partial = True
            return False
        if kind in ("url", "ip:port", "host:port") and how and value.encode("latin-1", "ignore") in self.d:
            return False           # sudah polos di berkas: sudah tampil sebagai IOC biasa, bukan hasil dekode
        self.seen.add((kind, value))
        it = {"kind": kind, "value": value, "how": how or "polos", "src": src, "conf": conf}
        if kind in ("token", "webhook") and not self.reveal:   # rahasia berformat khusus: tidak ditulis utuh (cf. _mask); sha256 untuk pivot
            it["sha256"] = hashlib.sha256(value.encode("latin-1", "ignore")).hexdigest()[:16]
            it["value"] = _mcfg_hide(kind, value)
        self.items.append(it)
        return True


def _mcfg_hide(kind: str, v: str) -> str:
    if kind == "webhook":
        m = re.match(r"(https://[^/]+/api/webhooks/\d+/)", v)
        return (m.group(1) if m else v[:24]) + "…(%d krt)" % len(v)
    a, _, b = v.partition(":")
    return a + ":" + _mask(b) if b else _mask(v)


def _mcfg_ratio(b: bytes) -> float:
    if not b:
        return 0.0
    return sum(1 for c in b if 9 <= c <= 13 or 32 <= c <= 126) / len(b)


def _mcfg_ratio2(b: bytes) -> float:
    """Seperti _mcfg_ratio tetapi NUL dan pemisah 0x1c-0x1f dihitung teks (blob konfigurasi gaya Remcos memakai pemisah kontrol / padding NUL)."""
    if not b:
        return 0.0
    return sum(1 for c in b if c == 0 or 9 <= c <= 13 or 28 <= c <= 126) / len(b)


def _mcfg_rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    kl = len(key)
    for i in range(256):
        j = (j + S[i] + key[i % kl]) & 255
        S[i], S[j] = S[j], S[i]
    out = bytearray(len(data))
    i = j = 0
    for n, c in enumerate(data):
        i = (i + 1) & 255
        si = S[i]
        j = (j + si) & 255
        sj = S[j]
        S[i], S[j] = sj, si
        out[n] = c ^ S[(si + sj) & 255]
    return bytes(out)


def _mcfg_rxor(data: bytes, key: bytes) -> bytes:
    n = len(data)
    if not n or not key:
        return data
    kk = (key * (n // len(key) + 1))[:n]
    return (int.from_bytes(data, "big") ^ int.from_bytes(kk, "big")).to_bytes(n, "big")


def _mcfg_kshow(k: bytes) -> str:
    return "'%s'" % k.decode("latin-1") if _mcfg_ratio(k) == 1.0 and all(32 < c < 127 for c in k) else k.hex()


def _mcfg_cs_parse(b: bytes):
    """Blok TLV konfigurasi beacon Cobalt Strike (sudah di-XOR): id(2) tipe(2) panjang(2) nilai, big-endian. Tipe 1 = short, 2 = int, 3 = blob / string."""
    if len(b) < 24 or b[:6] != b"\x00\x01\x00\x01\x00\x02":
        return None
    p, items = 0, {}
    while p + 6 <= len(b) and len(items) < 90:
        fid, typ, ln = struct.unpack_from(">HHH", b, p)
        p += 6
        if fid == 0:
            break
        if typ not in (1, 2, 3) or (typ == 1 and ln != 2) or (typ == 2 and ln != 4) or p + ln > len(b):
            return None if len(items) < 6 else items
        items[fid] = (typ, b[p:p + ln])
        p += ln
    return items if len(items) >= 6 and 1 in items and 2 in items else None


def _mcfg_cs_emit(items: dict, how: str, src: str, ctx: _McfgCtx) -> None:
    if "Cobalt Strike beacon" not in ctx.fam:
        ctx.fam.append("Cobalt Strike beacon")
    for fid, (typ, v) in items.items():
        name = _CS_FIELDS.get(fid)
        if not name:
            continue
        if fid in _CS_STR:
            s = v.split(b"\0", 1)[0].decode("latin-1", "replace")
            if not s:
                continue
            kind = {8: "c2", 9: "user_agent", 10: "uri", 32: "proxy"}.get(fid, "cs:" + name)
            ctx.add(kind, s, how, src, "tinggi")
        elif fid == 7:
            ctx.add("key", "sha256 kunci publik RSA: " + hashlib.sha256(v).hexdigest()[:32], how, src, "tinggi")
        elif typ == 1 or typ == 2:
            n = int.from_bytes(v, "big")
            if fid == 1:
                ctx.add("cs:beacon_type", "%d (%s)" % (n, _CS_BTYPE.get(n, "?")), how, src, "tinggi")
            elif fid == 2:
                ctx.add("port", str(n), how, src, "tinggi")
            elif fid == 37:
                ctx.add("campaign", "watermark %d" % n, how, src, "tinggi")
            elif fid in (3, 5, 4):
                ctx.add("timing", "%s=%d" % (name, n), how, src, "tinggi")
            else:
                ctx.add("cs:" + name, str(n), how, src, "tinggi")


def _mcfg_views(buf: bytes) -> list:
    """buf + versi ASCII dari string UTF-16LE (None bila tidak ada)."""
    vs = [buf]
    if b"\x00" in buf[:65536] or len(buf) < 65536:
        parts = [m.group()[::2] for m in itertools.islice(_UTF16.finditer(buf), 20000)]
        if parts:
            vs.append(b"\n".join(parts)[:4 << 20])
    return vs


def _mcfg_pairs(obj, out: list, depth: int = 0) -> None:
    if depth > 4 or len(out) > 400:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                if isinstance(v, list) and v and all(isinstance(x, (str, int)) for x in v):
                    out.append((str(k), ",".join(str(x) for x in v[:8])))
                else:
                    _mcfg_pairs(v, out, depth + 1)
            elif v is not None and not isinstance(v, bool):
                out.append((str(k), str(v)))
    elif isinstance(obj, list):
        for x in obj[:20]:
            _mcfg_pairs(x, out, depth + 1)


def _mcfg_accept(pairs: list):
    """Pasangan (nama, nilai) -> daftar (jenis, nilai) bila membentuk konfigurasi (>= 3 nama konfigurasi berbeda, atau 2 dengan satu jenis kuat)."""
    got, names = [], set()
    for k, v in pairs:
        kn = re.sub(r"[\s\-]+", "_", k.strip().lower())
        kind = _MCFG_NAMES.get(kn)
        v = v.strip()
        if not kind or not v or len(v) > 200:
            continue
        names.add(kn)
        got.append((kind, k.strip() + "=" + v))
    kinds = {_MCFG_NAMES[n] for n in names}
    if len(names) >= 3 and kinds & _MCFG_STRONG or len(names) >= 2 and kinds & {"c2", "token", "key"} and len(kinds) >= 2:
        return got[:24]
    return None


def _mcfg_extract(buf: bytes, how: str, src: str, ctx: _McfgCtx, plain: bool) -> int:
    """Jalankan pengekstrak pola pada satu penyangga. plain=True: berkas asli (hanya pola spesifik, tanpa URL / ip:port umum yang sudah jadi IOC)."""
    n0 = len(ctx.items)
    if not buf:
        return 0
    # 1) Cobalt Strike
    for key, pat in _CS_PAT.items():
        pos, tries = buf.find(pat), 0
        while pos >= 0 and tries < 6 and ctx.left():
            tries += 1
            items = _mcfg_cs_parse(buf[pos:pos + 4096].translate(_xor_table("XOR", key)))
            if items:
                _mcfg_cs_emit(items, ((how + " > ") if how else "") + "XOR 0x%02X" % key, "%s @0x%X" % (src, pos), ctx)
                break
            pos = buf.find(pat, pos + 1)
    if not ctx.left():
        return len(ctx.items) - n0
    # 2) pola spesifik (ASCII dan UTF-16LE)
    for v in _mcfg_views(buf):
        for m in itertools.islice(_MCFG_TG.finditer(v), 8):
            ctx.add("token", "Telegram bot " + m.group().decode("ascii"), how, src, "sedang")
        for m in itertools.islice(_MCFG_DISCORD.finditer(v), 8):
            ctx.add("webhook", m.group().decode("ascii"), how, src, "sedang")
        for m in itertools.islice(_MCFG_MUTEX.finditer(v), 12):
            s = m.group().decode("ascii")
            if not _MCFG_MUTEX_SKIP.match(s.split("\\", 1)[1]):
                ctx.add("mutex", s, how, src, "sedang")
        for m in itertools.islice(_MCFG_DEAD.finditer(v), 8):
            ctx.add("dead-drop", m.group().decode("ascii").rstrip(".,;)\"'"), how, src, "sedang")
        if not plain:
            for m in itertools.islice(_MCFG_DEAD_GH.finditer(v), 8):
                ctx.add("dead-drop", m.group().decode("ascii").rstrip(".,;)\"'"), how, src, "sedang")
            for m in itertools.islice(_MCFG_URL.finditer(v), 12):
                ctx.add("url", m.group().decode("ascii").rstrip(".,;)\"'"), how, src, "sedang")
            for m in itertools.islice(_MCFG_IPPORT.finditer(v), 12):
                ctx.add("ip:port", m.group().decode("ascii"), how, src, "sedang")
            for m in itertools.islice(_MCFG_HOSTPORT.finditer(v), 12):
                ctx.add("host:port", m.group().decode("ascii").lower(), how, src, "sedang")
        if not ctx.left():
            return len(ctx.items) - n0
        # 3) objek JSON konfigurasi
        i, tries = v.find(b'{"'), 0
        while i >= 0 and tries < 40 and ctx.left():
            tries += 1
            try:
                obj, end = json.JSONDecoder().raw_decode(v[i:i + 16384].decode("utf-8", "ignore"))
            except ValueError:
                i = v.find(b'{"', i + 2)
                continue
            if isinstance(obj, dict) and len(obj) >= 2:
                pr: list = []
                _mcfg_pairs(obj, pr)
                acc = _mcfg_accept(pr)
                if acc:
                    for kind, val in acc:
                        ctx.add("cfg:" + kind, val, how, src, "rendah" if plain else "sedang")
                i = v.find(b'{"', i + max(end, 2))
            else:
                i = v.find(b'{"', i + 2)
    # 4) baris kunci=nilai (hanya wilayah / hasil dekode yang berbentuk teks)
    if not plain and len(buf) <= (2 << 20) and _mcfg_ratio(buf[:4096]) >= 0.7:
        pr = [(m.group(1), m.group(2)) for m in itertools.islice(_MCFG_KV.finditer(buf.decode("latin-1")), 400)]
        acc = _mcfg_accept(pr)
        if acc:
            for kind, val in acc:
                ctx.add("cfg:" + kind, val, how, src, "sedang")
    return len(ctx.items) - n0


def _mcfg_keys(d: bytes, near: int, extra: list) -> list:
    """Kandidat kunci: dari pengguna, umum, lalu string pendek di sekitar wilayah (urut jarak)."""
    out: list = []
    seen: set = set()
    for k in list(extra) + list(_MCFG_COMMON_KEYS):
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    lo = max(0, near - 0x4000)
    win = d[lo:min(len(d), near + 0x1000)]
    cand = []
    for m in itertools.islice(_MCFG_KEYSTR.finditer(win), 6000):
        s = m.group()
        if s in seen or _MCFG_KEYSKIP.search(s):
            continue
        seen.add(s)
        cand.append((abs(lo + m.start() - near), s))
    cand.sort()
    out += [s for _x, s in cand[:MCFG_MAX_KEYS]]
    return out


def _mcfg_decoders(blob: bytes, ctx: _McfgCtx, keys: list):
    """Hasilkan (cara, byte) untuk kandidat dekode satu wilayah. Kunci dipilih dari kepala blob (murah); kandidat baru dipakai bila memuat butir konfigurasi."""
    import zlib
    head = blob[:64]
    if len(head) < 24:
        return
    if _mcfg_ratio(blob[:256]) >= 0.9:        # sudah teks: hanya lapis base64 yang masuk akal
        if _MCFG_B64.fullmatch(blob[:200].strip() + b"") or _MCFG_B64.match(blob[:200]):
            try:
                dec = base64.b64decode(b"".join(blob.split())[:MCFG_DEC_MAX * 2], validate=False)
                if len(dec) >= 16:
                    yield "base64", dec[:MCFG_DEC_MAX]
            except Exception:
                pass
        return
    if len(set(head)) < 8:
        return
    h2 = head[:2]
    try:
        if h2 == b"\x1f\x8b":
            yield "gzip", zlib.decompressobj(31).decompress(blob[:MCFG_DEC_MAX], MCFG_DEC_MAX)
        elif h2 in (b"\x78\x9c", b"\x78\x01", b"\x78\xda", b"\x78\x5e"):
            yield "zlib", zlib.decompressobj(15).decompress(blob[:MCFG_DEC_MAX], MCFG_DEC_MAX)
    except Exception:
        pass
    cands = []      # satu-byte: semua kunci yang lolos probe diperingkat menurut kemiripan teks (kunci kecil juga menghasilkan ASCII tercetak)
    for op, rng in (("XOR", range(1, 256)), ("ADD", range(1, 256)), ("ROL", range(1, 8))):
        for k in rng:
            t = _xor_table(op, k)
            h = head.translate(t)
            if _mcfg_ratio2(h) >= 0.9 and len(set(h)) >= 8:
                sc = 1.0 - len(h.translate(None, _MCFG_TXT)) / len(h)
                if sc >= 0.85:
                    cands.append((-sc, op, k, t))
    cands.sort(key=lambda x: x[:3])
    for _sc, op, k, t in cands[:4]:
        yield (("%s 0x%02X" % (op, k)) if op != "ROL" else "ROL %d" % k), blob[:MCFG_DEC_MAX].translate(t)
    # kunci di awal blob (gaya Remcos): byte pertama = panjang kunci, lalu kunci, lalu data RC4
    n0 = blob[0]
    if 1 <= n0 <= 64 and len(blob) > n0 + 24:
        pk = blob[1:1 + n0]
        dd = blob[1 + n0:1 + n0 + MCFG_DEC_MAX]
        h = _mcfg_rc4(pk, dd[:48])
        if _mcfg_ratio2(h) >= 0.85 and len(set(h)) >= 8:
            yield "RC4 kunci di awal blob (%s)" % _mcfg_kshow(pk), _mcfg_rc4(pk, dd)
    n = 0
    for kb in keys:
        n += 1
        ctx.keys_tried += 1
        if n % 32 == 0 and not ctx.left():
            return
        if len(kb) >= 2:
            h = _mcfg_rxor(head[:48], kb)
            if _mcfg_ratio2(h) >= 0.85 and len(set(h)) >= 8:
                yield "XOR kunci berulang %s" % _mcfg_kshow(kb), _mcfg_rxor(blob[:MCFG_DEC_MAX], kb)
        h = _mcfg_rc4(kb, head[:48])
        if _mcfg_ratio2(h) >= 0.85 and len(set(h)) >= 8:
            yield "RC4 kunci %s" % _mcfg_kshow(kb), _mcfg_rc4(kb, blob[:MCFG_DEC_MAX])


def _mcfg_process(buf: bytes, how: str, src: str, ctx: _McfgCtx, keys: list, depth: int, plain: bool = False) -> int:
    """Ekstrak dari buf; bila depth < MCFG_MAX_DEPTH coba dekode bertingkat dan ekstrak hasilnya (hanya yang menghasilkan butir yang disimpan)."""
    n = _mcfg_extract(buf, how, src, ctx, plain or not how)   # wilayah yang belum didekode = data apa adanya: hanya pola spesifik
    if depth >= MCFG_MAX_DEPTH or plain or not ctx.left():
        return n
    for how2, dec in _mcfg_decoders(buf, ctx, keys):
        if not dec:
            continue
        label = (how + " > " if how else "") + how2
        m = _mcfg_process(dec, label, src, ctx, keys, depth + 1)
        n += m
        if m and "SETTINGS" in src and how2.startswith("RC4 kunci di awal"):
            if "mirip Remcos (blob SETTINGS + RC4 kunci di awal)" not in ctx.fam:
                ctx.fam.append("mirip Remcos (blob SETTINGS + RC4 kunci di awal)")
        if not ctx.left():
            break
    return n


def _mcfg_blobs(d: bytes, pe, dn, regions, raw_file: bool) -> list:
    """Wilayah kandidat terenkode: (label, offset, panjang)."""
    cand: list = []
    if pe and not pe.get("broken"):
        ov, st = pe.get("overlay", 0), pe.get("last_raw", 0)
        if ov >= 32 and 0 < st < len(d):
            cand.append(("overlay", st, ov))
        for x in pe.get("res", []) or []:
            if x.get("size", 0) >= 32 and 0 < x.get("off", 0) < len(d) and not (x.get("fmt") and x.get("fmt_ok")):
                cand.append(("resource %s/%s" % (x.get("type"), x.get("name")), x["off"], x["size"]))
    for x in (dn or {}).get("mres", []) or []:
        if x.get("size", 0) >= 32 and 0 < x.get("off", 0) < len(d):
            cand.append(("resource .NET", x["off"], x["size"]))
    for a, b in regions or []:
        if b - a >= 64:
            cand.append(("wilayah berentropi tinggi", a, b - a))
    if raw_file and len(d) >= 32:
        cand.append(("berkas", 0, len(d)))
    out, seen = [], set()
    for lab, off, ln in cand:
        if off in seen or off >= len(d):
            continue
        seen.add(off)
        out.append((lab, off, min(ln, MCFG_MAX_BLOB, len(d) - off)))
        if len(out) >= MCFG_MAX_BLOBS:
            break
    return out


def _mcfg_run(d: bytes, pe, dn, xor, xor_multi, regions, raw_file: bool, user_keys: list, reveal: bool) -> dict | None:
    ctx = _McfgCtx(d, reveal)
    _mcfg_process(d, "", "berkas", ctx, [], MCFG_MAX_DEPTH, plain=True)           # pola spesifik pada berkas apa adanya
    for x in (xor or [])[:2]:                                                        # perburuan satu-byte yang sudah ada: dekode seluruh berkas
        if not ctx.left():
            break
        try:
            _mcfg_process(d.translate(_xor_table(x["op"], x["key"])), "%s 0x%02X seluruh berkas" % (x["op"], x["key"]), "berkas", ctx, [], MCFG_MAX_DEPTH)
        except Exception:
            pass
    for x in (xor_multi or [])[:2]:                                                  # XOR kunci berulang dengan MZ terkonfirmasi: PE tersembunyi
        if not ctx.left() or not x.get("mz"):
            continue
        try:
            kb = bytes.fromhex(x["key"])
            off = x["mz_off"]
            _mcfg_process(_mcfg_rxor(d[off:off + MCFG_MAX_BLOB * 4], kb), "XOR kunci berulang %s" % x["key"], "PE tersembunyi @0x%X" % off, ctx, [], MCFG_MAX_DEPTH)
        except Exception:
            pass
    for lab, off, ln in _mcfg_blobs(d, pe, dn, regions, raw_file):
        if not ctx.left():
            break
        ctx.blobs += 1
        keys = _mcfg_keys(d, off, user_keys)
        _mcfg_process(d[off:off + ln], "", "%s @0x%X" % (lab, off), ctx, keys, 0)
    if not ctx.items:
        return None
    return {"families": ctx.fam, "items": ctx.items, "blobs": ctx.blobs, "keys_tried": ctx.keys_tried, "partial": ctx.partial}


def _mcfg_enrich(d: bytes, rep: dict, pe, dn, zp) -> None:
    """Dipanggil dari _v97_enrich: rep["malcfg"] (kunci baru). Tidak pernah melempar; tidak mengubah skor."""
    rep["malcfg"] = None
    if zp:
        return
    try:
        raw = not pe and not rep.get("elf") and not rep.get("macho") and len(d) <= MCFG_MAX_BLOB and d[:2] != b"PK"
        rep["malcfg"] = _mcfg_run(d, pe, dn, rep.get("xor"), rep.get("xor_multi"), rep.get("regions"), raw, [], False)
    except Exception as e:
        rep["warn"].append("ekstraksi konfigurasi malware gagal: %s" % type(e).__name__)
        return
    mc = rep["malcfg"]
    if mc:
        fam = ", ".join(mc["families"]) if mc["families"] else "tanpa keluarga dikenal"
        rep["warn"].append("konfigurasi tertanam terekstrak (%s, %d butir): lihat baris Konfigurasi malware" % (fam, len(mc["items"])))


def _render_mcfg(mc: dict, a, compact: bool, defang: bool) -> None:
    if not mc:
        return
    fam = ", ".join(mc["families"]) if mc["families"] else "tanpa keluarga dikenal"
    a("Konfigurasi malware (ekstraktor statis; PETUNJUK, verifikasi dengan sampel / alat khusus): %s | %d butir%s" % (fam, len(mc["items"]), " | TERPOTONG (batas waktu / jumlah)" if mc.get("partial") else ""))
    lim = 6 if compact else MCFG_MAX_ITEMS
    for it in mc["items"][:lim]:
        v = it["value"]
        if it["kind"] in ("c2", "url", "uri", "dead-drop", "webhook", "ip:port", "host:port"):
            v = _df(v, defang)
        a("   - %s: %s  [%s; %s; %s]%s" % (it["kind"], v, it["how"], it["src"], it["conf"], (" sha256:" + it["sha256"]) if it.get("sha256") else ""))
    if len(mc["items"]) > lim:
        a("   ... +%d butir lagi (lihat --config FILE)" % (len(mc["items"]) - lim))


def extract_config(path, keys=None, reveal: bool = False) -> dict:
    """Ekstraksi konfigurasi malware satu berkas. keys: daftar kunci (str / bytes) yang dicoba untuk RC4 / XOR. reveal=True: token / webhook ditulis utuh.
    -> {"ok": True, "config": {...} | None, "kind": ...}; tidak melempar."""
    try:
        d, size = _cfg_read(path)
        pe = _parse_pe(d, size) if d[:2] == b"MZ" else None
        if pe and pe.get("broken"):
            pe = None
        dn = _dotnet_info(d, pe) if pe and pe.get("dotnet") else None
        zp = d[:2] == b"PK"
        if zp:
            return {"ok": True, "config": None, "kind": "arsip", "note": "arsip ZIP: ekstrak dulu (--unpack / --assets-extract), lalu jalankan pada isinya"}
        elf, mo = d[:4] == b"\x7fELF", d[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe")
        uk = [k.encode("latin-1", "replace") if isinstance(k, str) else bytes(k) for k in (keys or []) if k]
        try:
            xor = _xor_hunt(d)
        except Exception:
            xor = []
        try:
            xm = _xor_multi(d)
        except Exception:
            xm = []
        skip = [(x["off"], x["off"] + x["size"]) for x in (pe or {}).get("res", []) if x.get("fmt") and x.get("fmt_ok")] + list((pe or {}).get("cert_spans") or [])
        regions = _entropy_regions(d, skip)
        raw = not pe and not elf and not mo and len(d) <= MCFG_MAX_BLOB
        mc = _mcfg_run(d, pe, dn, xor, xm, regions, raw, uk, reveal)
        return {"ok": True, "config": mc, "kind": "PE" if pe else "ELF" if elf else "Mach-O" if mo else "berkas mentah", "size": size}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def config_text(path, defang: bool = True, keys=None) -> str:
    """Teks ekstraksi konfigurasi malware. CLI --config, API action 'config'."""
    r = extract_config(path, keys=keys)
    if not r.get("ok"):
        return "Ekstraksi konfigurasi gagal (%s)." % r.get("error")
    if r.get("note"):
        return "Konfigurasi: " + r["note"] + "."
    if not r.get("config"):
        return "Konfigurasi: tidak ada konfigurasi tertanam yang berhasil diekstrak (%s). Tidak berarti bersih: AES / RSA, string .NET terenkripsi, atau kunci yang tidak ada di berkas tidak terjangkau (coba --key STR)." % r.get("kind")
    L_: list = []
    _render_mcfg(r["config"], L_.append, False, defang)
    return "\n".join(L_)


# ----------------------- v99.18 [S2]: micro-emulation instruksi terbatas (RE Lab x86 / x64) -----------------------
# Emulator register + memori kecil, murni Python, STATIS (sampel tidak pernah dijalankan; hanya byte di berkas yang ditafsirkan). Tujuan: mendekode string
# yang disusun / diobfuskasi di stack (mov imm + xor / add / sub / rol / ror / not / neg berantai) dan buffer yang didekripsi di tempat oleh loop kecil, yang
# tidak terlihat oleh pemindai pola byte. Himpunan instruksi sengaja kecil: mov / movzx / movsx / lea / ALU / shift & rotate / inc / dec / not / neg / imul /
# push / pop / leave / jmp / jcc / loop / call (dilangkahi). Nilai yang tidak diketahui dilacak per bit (None); cabang yang kondisinya tidak diketahui
# di-fork (EMU_MAX_FORKS). Memori: berkas (baca) + lapisan tulis (overlay) + stack sintetis; tulisan ke alamat tak diketahui dihitung, tidak dipakai.
# Batasan: call tidak diikuti (reg volatil dianggap tak diketahui), tidak ada API / syscall / SSE / string-op (rep movs / stos), jump table tak diselesaikan,
# paritas (jp / jnp) tidak dimodelkan. Hasil adalah PETUNJUK. Kunci baru info["emu"] (RE Lab), aditif; skor tidak berubah.

EMU_TIME = 3.0                  # detik untuk seluruh emulasi satu berkas
EMU_MAX_FUNCS = 400             # fungsi yang diemulasi
EMU_MAX_STEPS = 50_000          # langkah per jalur
EMU_MAX_TOTAL = 2_000_000       # langkah total per berkas
EMU_MAX_FORKS = 16              # fork cabang tak-diketahui per fungsi
EMU_MAX_FINALS = 24             # jalur akhir yang diperiksa per fungsi
EMU_MAX_WRITES = 65_536         # byte tulisan per jalur
EMU_MAX_RESULTS = 40            # string + buffer yang dilaporkan

_M64 = (1 << 64) - 1
_MK = {8: 0xFF, 16: 0xFFFF, 32: 0xFFFFFFFF, 64: _M64}
_EMU_RX_A = re.compile(rb"[\x20-\x7e]{5,}")
_EMU_RX_W = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")
_EMU_STRONG = frozenset(("xor", "rol", "ror", "not", "neg"))
_EMU_SHIFT = {0: "rol", 1: "ror", 4: "shl", 5: "shr", 6: "shl", 7: "sar"}
_EMU_R64 = ("rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi") + tuple("r%d" % i for i in range(8, 16))
_EMU_R32 = ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi") + tuple("r%dd" % i for i in range(8, 16))
_EMU_R16 = ("ax", "cx", "dx", "bx", "sp", "bp", "si", "di") + tuple("r%dw" % i for i in range(8, 16))
_EMU_R8 = ("al", "cl", "dl", "bl", "spl", "bpl", "sil", "dil") + tuple("r%db" % i for i in range(8, 16))
_EMU_R8H = ("ah", "ch", "dh", "bh")
_EMU_CC = ("o", "no", "b", "ae", "e", "ne", "be", "a", "s", "ns", "p", "np", "l", "ge", "le", "g")


def _emu_dec(c: bytes, i: int, is64: bool, va: int):
    """Satu instruksi di c[i:] -> (n, op, a, b, w, x) atau None. Operand: ("i", nilai, w) | ("r", idx, w, hi8) | ("m", base, index, skala, disp, w, seg, rip)."""
    i0 = i
    try:
        osz = seg = False
        while True:
            p = c[i]
            if p == 0x66:
                osz = True
            elif p == 0x67:
                return None
            elif p in (0xF0, 0xF2, 0xF3, 0x2E, 0x3E, 0x26, 0x36):
                pass
            elif p in (0x64, 0x65):
                seg = True
            else:
                break
            i += 1
            if i - i0 > 6:
                return None
        rex = 0
        if is64 and 0x40 <= c[i] <= 0x4F:
            rex = c[i]
            i += 1
        W, Rx, Xx, Bx = bool(rex & 8), (rex >> 2) & 1, (rex >> 1) & 1, rex & 1
        ws = 64 if W else (16 if osz else 32)
        pw = 64 if is64 else (16 if osz else 32)
        op = c[i]
        i += 1

        def rg(idx, w):
            if w == 8 and not rex and 4 <= idx < 8:
                return ("r", idx - 4, 8, True)
            return ("r", idx, w, False)

        def modrm(w):
            nonlocal i
            m = c[i]
            i += 1
            mod, r3, rm = m >> 6, (m >> 3) & 7, m & 7
            regx = r3 | (Rx << 3)
            if mod == 3:
                return r3, regx, rg(rm | (Bx << 3), w)
            base = index = None
            sc, disp, rip = 1, 0, False
            if rm == 4:
                sib = c[i]
                i += 1
                sc = 1 << (sib >> 6)
                ix = ((sib >> 3) & 7) | (Xx << 3)
                index = None if ix == 4 else ix
                bs = sib & 7
                if mod == 0 and bs == 5:
                    disp = struct.unpack_from("<i", c, i)[0]
                    i += 4
                else:
                    base = bs | (Bx << 3)
            elif mod == 0 and rm == 5:
                disp = struct.unpack_from("<i", c, i)[0]
                i += 4
                rip = is64
            else:
                base = rm | (Bx << 3)
            if mod == 1:
                disp += struct.unpack_from("<b", c, i)[0]
                i += 1
            elif mod == 2:
                disp += struct.unpack_from("<i", c, i)[0]
                i += 4
            return r3, regx, ["m", base, index, sc, disp, w, seg, rip]

        def imm(sz, sg=True):
            nonlocal i
            if i + sz > len(c):
                raise IndexError
            v = int.from_bytes(c[i:i + sz], "little", signed=sg)
            i += sz
            return v

        def im(v, w):
            return ("i", v & _MK[w], w)

        def done(opn, a=None, b=None, w=0, x=0):
            n = i - i0

            def fx(o):
                if isinstance(o, list):
                    if o[7]:
                        o[4] += va + n
                        o[7] = False
                    return tuple(o)
                return o
            return (n, opn, fx(a), fx(b), w, x)

        isz = 2 if ws == 16 else 4
        if op < 0x40 and (op & 7) < 6:
            nm, lo = _ARITH_GRP[op >> 3], op & 7
            if lo == 4:
                return done(nm, rg(0, 8), im(imm(1), 8), 8)
            if lo == 5:
                return done(nm, rg(0, ws), im(imm(isz), ws), ws)
            w = 8 if lo in (0, 2) else ws
            _r3, rx, rm = modrm(w)
            ro = rg(rx, w)
            return done(nm, rm, ro, w) if lo < 2 else done(nm, ro, rm, w)
        if op in (0x80, 0x81, 0x83):
            w = 8 if op == 0x80 else ws
            r3, _rx, rm = modrm(w)
            v = imm(1) if op != 0x81 else imm(isz)
            return done(_ARITH_GRP[r3], rm, im(v, w), w)
        if op in (0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B):
            w = 8 if op in (0x84, 0x86, 0x88, 0x8A) else ws
            _r3, rx, rm = modrm(w)
            ro = rg(rx, w)
            nm = "test" if op < 0x86 else ("xchg" if op < 0x88 else "mov")
            return done(nm, ro, rm, w) if op in (0x8A, 0x8B) else done(nm, rm, ro, w)
        if op == 0x8D:
            _r3, rx, rm = modrm(ws)
            if not isinstance(rm, list):
                return None
            return done("lea", rg(rx, ws), rm, ws)
        if op == 0x63 and is64:
            _r3, rx, rm = modrm(32)
            return done("movsx", rg(rx, ws), rm, ws)
        if op == 0x90:
            return done("nop")
        if 0xB0 <= op <= 0xB7:
            return done("mov", rg((op & 7) | (Bx << 3), 8), im(imm(1), 8), 8)
        if 0xB8 <= op <= 0xBF:
            v = imm(8, False) if W else imm(isz)
            return done("mov", rg((op & 7) | (Bx << 3), ws), im(v, ws), ws)
        if op in (0xC6, 0xC7):
            w = 8 if op == 0xC6 else ws
            r3, _rx, rm = modrm(w)
            if r3 != 0:
                return None
            return done("mov", rm, im(imm(1 if op == 0xC6 else isz), w), w)
        if op in (0xC0, 0xC1, 0xD0, 0xD1, 0xD2, 0xD3):
            w = 8 if op in (0xC0, 0xD0, 0xD2) else ws
            r3, _rx, rm = modrm(w)
            nm = _EMU_SHIFT.get(r3)
            if nm is None:
                return None
            cnt = im(imm(1, False), 8) if op in (0xC0, 0xC1) else (("i", 1, 8) if op in (0xD0, 0xD1) else rg(1, 8))
            return done(nm, rm, cnt, w)
        if op in (0xF6, 0xF7):
            w = 8 if op == 0xF6 else ws
            r3, _rx, rm = modrm(w)
            if r3 in (0, 1):
                return done("test", rm, im(imm(1 if w == 8 else isz), w), w)
            if r3 in (2, 3):
                return done("not" if r3 == 2 else "neg", rm, None, w)
            return None
        if op in (0xFE, 0xFF):
            w = 8 if op == 0xFE else ws
            r3, _rx, rm = modrm(w)
            if r3 in (0, 1):
                return done("inc" if r3 == 0 else "dec", rm, None, w)
            if op == 0xFF and r3 == 2:
                return done("calli")
            if op == 0xFF and r3 == 6:
                if isinstance(rm, list):
                    rm[5] = pw
                    return done("push", rm, None, pw)
                return done("push", ("r", rm[1], pw, False), None, pw)
            return None
        if not is64 and 0x40 <= op <= 0x4F:
            return done("inc" if op < 0x48 else "dec", rg(op & 7, ws), None, ws)
        if 0x50 <= op <= 0x57:
            return done("push", rg((op & 7) | (Bx << 3), pw), None, pw)
        if 0x58 <= op <= 0x5F:
            return done("pop", rg((op & 7) | (Bx << 3), pw), None, pw)
        if op == 0x68:
            return done("push", im(imm(isz), pw), None, pw)
        if op == 0x6A:
            return done("push", im(imm(1), pw), None, pw)
        if op in (0x69, 0x6B):
            _r3, rx, rm = modrm(ws)
            return done("imul3", rg(rx, ws), rm, ws, imm(isz) if op == 0x69 else imm(1))
        if op == 0xE8:
            return done("call", x=imm(4))
        if op == 0xE9:
            return done("jmp", x=imm(4))
        if op == 0xEB:
            return done("jmp", x=imm(1))
        if 0x70 <= op <= 0x7F:
            return done("jcc", w=op & 15, x=imm(1))
        if 0xE0 <= op <= 0xE3:
            return done(("loopne", "loope", "loop", "jcxz")[op - 0xE0], x=imm(1))
        if op in (0xC3, 0xC2, 0xCB, 0xCA):
            return done("ret")
        if op == 0xC9:
            return done("leave")
        if op in (0xF8, 0xF9, 0xFC, 0xFD):
            return done("clc" if op == 0xF8 else ("stc" if op == 0xF9 else "nop"))
        if op == 0x0F:
            o2 = c[i]
            i += 1
            if o2 in (0xB6, 0xB7, 0xBE, 0xBF):
                sw = 8 if o2 in (0xB6, 0xBE) else 16
                _r3, rx, rm = modrm(sw)
                return done("movzx" if o2 < 0xB8 else "movsx", rg(rx, ws), rm, ws)
            if o2 == 0xAF:
                _r3, rx, rm = modrm(ws)
                return done("imul2", rg(rx, ws), rm, ws)
            if 0x80 <= o2 <= 0x8F:
                return done("jcc", w=o2 & 15, x=imm(4))
            if o2 == 0x1F:
                modrm(ws)
                return done("nop")
            if 0xC8 <= o2 <= 0xCF:
                return done("bswap", rg((o2 & 7) | (Bx << 3), ws), None, ws)
            return None
        return None
    except (IndexError, struct.error):
        return None


class _EmuSt:
    """Satu jalur emulasi: register (nilai + bit-diketahui), flag, overlay memori."""
    __slots__ = ("rv", "rk", "fl", "ov", "nw", "pc", "steps", "ops", "am", "d", "L", "lo", "hi", "unres")

    def __init__(self, d, L, am, lo, hi, nreg, pc):
        self.rv, self.rk, self.fl, self.ov, self.nw = [0] * nreg, [0] * nreg, [None] * 4, {}, 0
        self.pc, self.steps, self.ops, self.am, self.d, self.L, self.lo, self.hi, self.unres = pc, 0, set(), am, d, L, lo, hi, 0

    def fork(self, pc):
        s = _EmuSt.__new__(_EmuSt)
        s.rv, s.rk, s.fl, s.ov, s.nw = self.rv[:], self.rk[:], self.fl[:], dict(self.ov), self.nw
        s.pc, s.steps, s.ops, s.am, s.d, s.L, s.lo, s.hi, s.unres = pc, self.steps, set(self.ops), self.am, self.d, self.L, self.lo, self.hi, self.unres
        return s

    def rb(self, a):
        v = self.ov.get(a, -1)
        if v != -1:
            return v
        if self.lo <= a < self.hi:
            return None
        off = _va_off(self.L, a)
        if off is None or off >= len(self.d):
            return None
        return self.d[off]

    def read(self, a, n):
        v = 0
        for k in range(n):
            b = self.rb((a + k) & self.am)
            if b is None:
                return None
            v |= b << (8 * k)
        return v

    def write(self, a, n, val):
        if self.nw > EMU_MAX_WRITES:
            return
        for k in range(n):
            self.ov[(a + k) & self.am] = None if val is None else (val >> (8 * k)) & 0xFF
        self.nw += n


def _emu_rg(st, i):
    m = st.am
    return st.rv[i] & m if (st.rk[i] & m) == m else None


def _emu_addr(st, o):
    if o[6]:
        return None
    a = o[4]
    if o[1] is not None:
        v = _emu_rg(st, o[1])
        if v is None:
            return None
        a += v
    if o[2] is not None:
        v = _emu_rg(st, o[2])
        if v is None:
            return None
        a += v * o[3]
    return a & st.am


def _emu_get(st, o):
    t = o[0]
    if t == "i":
        return o[1]
    if t == "r":
        idx, w = o[1], o[2]
        if o[3]:
            return (st.rv[idx] >> 8) & 0xFF if (st.rk[idx] & 0xFF00) == 0xFF00 else None
        m = _MK[w]
        return st.rv[idx] & m if (st.rk[idx] & m) == m else None
    a = _emu_addr(st, o)
    return None if a is None else st.read(a, o[5] // 8)


def _emu_put(st, o, val):
    if o[0] == "r":
        idx, w = o[1], o[2]
        if o[3]:
            if val is None:
                st.rk[idx] &= ~0xFF00
            else:
                st.rv[idx] = (st.rv[idx] & ~0xFF00) | ((val & 0xFF) << 8)
                st.rk[idx] |= 0xFF00
        elif w >= 32:
            if val is None:
                st.rk[idx] = 0
            else:
                st.rv[idx], st.rk[idx] = val & _MK[w], st.am
        else:
            m = _MK[w]
            if val is None:
                st.rk[idx] &= ~m
            else:
                st.rv[idx] = (st.rv[idx] & ~m) | (val & m)
                st.rk[idx] |= m
        return
    a = _emu_addr(st, o)
    if a is None:
        st.unres += 1
        return
    st.write(a, o[5] // 8, val)


def _emu_alu(st, opn, a, b, w):
    m, sg = _MK[w], 1 << (w - 1)
    c = 0
    if opn in ("adc", "sbb"):
        if st.fl[0] is None:
            st.fl = [None] * 4
            return None
        c = st.fl[0]
    if opn in ("add", "adc"):
        t = a + b + c
        r = t & m
        st.fl = [int(t > m), int(r == 0), int(bool(r & sg)), int(bool((a ^ r) & (b ^ r) & sg))]
        return r
    if opn in ("sub", "sbb", "cmp"):
        t = a - b - c
        r = t & m
        st.fl = [int(t < 0), int(r == 0), int(bool(r & sg)), int(bool((a ^ b) & (a ^ r) & sg))]
        return r
    r = (a & b) if opn in ("and", "test") else ((a | b) if opn == "or" else (a ^ b))
    st.fl = [0, int(r == 0), int(bool(r & sg)), 0]
    return r


def _emu_shift(st, opn, a, cnt, w):
    m, sg = _MK[w], 1 << (w - 1)
    c = cnt & (63 if w == 64 else 31)
    if c == 0:
        return a
    if opn == "rol":
        k = c % w
        r = ((a << k) | (a >> (w - k))) & m if k else a
        st.fl[0], st.fl[3] = r & 1, None
        return r
    if opn == "ror":
        k = c % w
        r = ((a >> k) | (a << (w - k))) & m if k else a
        st.fl[0], st.fl[3] = int(bool(r & sg)), None
        return r
    if opn == "shl":
        r = (a << c) & m
        cf = (a >> (w - c)) & 1 if c <= w else 0
        of = (int(bool(r & sg)) ^ cf) if c == 1 else None
    elif opn == "shr":
        r = a >> c if c < w else 0
        cf = (a >> (c - 1)) & 1 if c <= w else 0
        of = int(bool(a & sg)) if c == 1 else None
    else:
        sa = a - (1 << w) if a & sg else a
        r = (sa >> min(c, w)) & m
        cf = (sa >> (min(c, w) - 1)) & 1
        of = 0 if c == 1 else None
    st.fl = [cf, int(r == 0), int(bool(r & sg)), of]
    return r


def _emu_cond(fl, cc):
    cf, zf, sf, of = fl
    t = cc >> 1
    if t == 0:
        v = of
    elif t == 1:
        v = cf
    elif t == 2:
        v = zf
    elif t == 3:
        v = None if cf is None or zf is None else int(bool(cf or zf))
    elif t == 4:
        v = sf
    elif t == 5:
        v = None
    elif t == 6:
        v = None if sf is None or of is None else int(sf != of)
    else:
        v = None if zf is None or sf is None or of is None else int(bool(zf or sf != of))
    return None if v is None else (bool(v) != bool(cc & 1))


def _emu_fmt(ins, va, is64=True):
    """Teks satu instruksi hasil _emu_dec (untuk jejak --emu FILE 0xVA)."""
    n, op, a, b, w, x = ins

    def f(o):
        if o is None:
            return ""
        if o[0] == "i":
            return "0x%X" % o[1]
        if o[0] == "r":
            idx, rw = o[1], o[2]
            if o[3]:
                return _EMU_R8H[idx]
            return {64: _EMU_R64, 32: _EMU_R32, 16: _EMU_R16, 8: _EMU_R8}[rw][idx]
        parts = []
        names = _EMU_R64 if is64 else _EMU_R32
        if o[1] is not None:
            parts.append(names[o[1]])
        if o[2] is not None:
            parts.append("%s*%d" % (names[o[2]], o[3]) if o[3] != 1 else names[o[2]])
        s = "+".join(parts)
        if o[4] or not s:
            s += ("%s0x%X" % ("-" if o[4] < 0 else "+", abs(o[4]))) if s else "0x%X" % (o[4] & _M64)
        return "%s[%s]" % ({8: "byte ", 16: "word ", 32: "dword ", 64: "qword "}.get(o[5], ""), ("fs:" if o[6] else "") + s)
    if op in ("jmp", "call", "loop", "loope", "loopne", "jcxz"):
        return "%s 0x%X" % (op, va + n + x)
    if op == "jcc":
        return "j%s 0x%X" % (_EMU_CC[w], va + n + x)
    return (op + " " + ", ".join(t for t in (f(a), f(b)) if t)).strip()


def _emu_func(d: bytes, L: dict, start: int, end: int, is64: bool, deadline: float, trace_max: int = 0, max_total: int = EMU_MAX_TOTAL) -> dict | None:
    """Emulasi satu fungsi [start, end). None bila awal tidak bisa dibaca. Tidak pernah melempar karena data biner (batas sumber daya di atas)."""
    off0 = _va_off(L, start)
    if off0 is None or end <= start:
        return None
    code = d[off0:off0 + (end - start) + 15]
    am = _M64 if is64 else 0xFFFFFFFF
    top = 0x00007FFE00100000 if is64 else 0x7FD00000
    lo, hi = top - 0x100000, top + 0x10000
    nreg = 16 if is64 else 8
    volatile = (0, 1, 2, 8, 9, 10, 11) if is64 else (0, 1, 2)
    cache: dict = {}
    s0 = _EmuSt(d, L, am, lo, hi, nreg, start)
    s0.rv[4], s0.rk[4] = top, am
    work, finals, tr = [s0], [], []
    total = forks = 0
    stop = ""
    timed = False
    while work and not timed:
        st = work.pop()
        first = trace_max > 0 and not finals
        while True:
            pc = st.pc
            if st.steps >= EMU_MAX_STEPS or total >= max_total:
                stop = "batas langkah"
                break
            if not (st.steps & 255) and time.monotonic() > deadline:
                stop, timed = "batas waktu", True
                break
            if not (start <= pc < end):
                stop = "keluar fungsi"
                break
            ins = cache.get(pc)
            if ins is None:
                ins = cache[pc] = _emu_dec(code, pc - start, is64, pc) or False
            if not ins:
                stop = "instruksi tak didukung"
                break
            n, op, a, b, w, x = ins
            nxt = pc + n
            st.steps += 1
            total += 1
            if st.nw > EMU_MAX_WRITES:
                stop = "batas tulis"
                break
            if op == "mov":
                _emu_put(st, a, _emu_get(st, b))
            elif op in ("add", "sub", "xor", "and", "or", "cmp", "test", "adc", "sbb"):
                zero_idiom = op in ("xor", "sub") and a[0] == "r" and b[0] == "r" and a[1:] == b[1:] and not a[3]
                if zero_idiom:
                    av = bv = 0
                else:
                    av, bv = _emu_get(st, a), _emu_get(st, b)
                if av is None or bv is None:
                    st.fl = [None] * 4
                    r = None
                else:
                    r = _emu_alu(st, op, av, bv, w)
                if op not in ("cmp", "test"):
                    _emu_put(st, a, r)
                    if r is not None and not zero_idiom and op in ("xor", "add", "sub") and not (a[0] == "r" and a[1] in (4, 5)):
                        st.ops.add(op)
            elif op in ("shl", "shr", "sar", "rol", "ror"):
                av, cv = _emu_get(st, a), _emu_get(st, b)
                if av is None or cv is None:
                    st.fl = [None] * 4
                    _emu_put(st, a, None)
                else:
                    _emu_put(st, a, _emu_shift(st, op, av, cv, w))
                    st.ops.add(op)
            elif op in ("inc", "dec"):
                av = _emu_get(st, a)
                if av is None:
                    st.fl[1:] = [None] * 3
                    _emu_put(st, a, None)
                else:
                    cf = st.fl[0]
                    _emu_alu(st, "add" if op == "inc" else "sub", av, 1, w)
                    st.fl[0] = cf
                    _emu_put(st, a, (av + (1 if op == "inc" else -1)) & _MK[w])
            elif op == "not":
                av = _emu_get(st, a)
                _emu_put(st, a, None if av is None else ~av & _MK[w])
                if av is not None:
                    st.ops.add("not")
            elif op == "neg":
                av = _emu_get(st, a)
                if av is None:
                    st.fl = [None] * 4
                    _emu_put(st, a, None)
                else:
                    r = (-av) & _MK[w]
                    st.fl = [int(av != 0), int(r == 0), int(bool(r & (1 << (w - 1)))), int(av == 1 << (w - 1))]
                    _emu_put(st, a, r)
                    st.ops.add("neg")
            elif op == "lea":
                ad = _emu_addr(st, b) if not b[6] else None
                _emu_put(st, a, None if ad is None else ad & _MK[w])
            elif op in ("movzx", "movsx"):
                v = _emu_get(st, b)
                sw_ = b[2] if b[0] == "r" else b[5]       # lebar sumber: reg di indeks 2, memori di indeks 5
                if v is not None and op == "movsx" and v & (1 << (sw_ - 1)):
                    v -= 1 << sw_
                _emu_put(st, a, None if v is None else v & _MK[w])
            elif op == "xchg":
                av, bv = _emu_get(st, a), _emu_get(st, b)
                _emu_put(st, a, bv)
                _emu_put(st, b, av)
            elif op in ("imul2", "imul3"):
                v1 = _emu_get(st, a) if op == "imul2" else _emu_get(st, b)
                v2 = _emu_get(st, b) if op == "imul2" else x & _MK[w]
                st.fl = [None] * 4
                _emu_put(st, a, None if v1 is None or v2 is None else (v1 * v2) & _MK[w])
            elif op == "bswap":
                av = _emu_get(st, a)
                _emu_put(st, a, None if av is None else int.from_bytes(av.to_bytes(w // 8, "little"), "big"))
            elif op == "push":
                sp = _emu_rg(st, 4)
                if sp is None:
                    stop = "rsp tak diketahui"
                    break
                sp = (sp - w // 8) & am
                st.rv[4] = sp
                st.write(sp, w // 8, _emu_get(st, a))
            elif op == "pop":
                sp = _emu_rg(st, 4)
                if sp is None:
                    stop = "rsp tak diketahui"
                    break
                v = st.read(sp, w // 8)
                st.rv[4] = (sp + w // 8) & am
                _emu_put(st, a, v)
            elif op == "leave":
                bp = _emu_rg(st, 5)
                if bp is None:
                    stop = "rbp tak diketahui"
                    break
                sw = 8 if is64 else 4
                v = st.read(bp, sw)
                st.rv[4], st.rk[4] = (bp + sw) & am, am
                st.rv[5], st.rk[5] = (v, am) if v is not None else (0, 0)
            elif op in ("call", "calli"):
                if op == "call" and x == 0:         # call $+5: get-PC, lazim di shellcode
                    sp = _emu_rg(st, 4)
                    if sp is None:
                        stop = "rsp tak diketahui"
                        break
                    sw = 8 if is64 else 4
                    sp = (sp - sw) & am
                    st.rv[4] = sp
                    st.write(sp, sw, nxt)
                else:
                    for r_ in volatile:
                        st.rk[r_] = 0
                    st.fl = [None] * 4
            elif op == "jmp":
                t = nxt + x
                if not (start <= t < end):
                    stop = "lompat keluar fungsi"
                    break
                st.pc = t
                if trace_max and first and len(tr) < trace_max:
                    tr.append((pc, _emu_fmt(ins, pc, is64), ""))
                continue
            elif op == "jcc":
                cv = _emu_cond(st.fl, w)
                t = nxt + x
                if cv is None:
                    if forks < EMU_MAX_FORKS and start <= t < end and len(work) < 32:
                        forks += 1
                        work.append(st.fork(t))
                elif cv:
                    if not (start <= t < end):
                        stop = "lompat keluar fungsi"
                        break
                    st.pc = t
                    if trace_max and first and len(tr) < trace_max:
                        tr.append((pc, _emu_fmt(ins, pc, is64), "diambil"))
                    continue
            elif op in ("loop", "loope", "loopne", "jcxz"):
                cw = 64 if is64 else 32
                cx = _emu_rg(st, 1)
                t = nxt + x
                if cx is None:
                    if forks < EMU_MAX_FORKS and start <= t < end and len(work) < 32:
                        forks += 1
                        work.append(st.fork(t))
                else:
                    if op != "jcxz":
                        cx = (cx - 1) & _MK[cw]
                        st.rv[1], st.rk[1] = cx, am
                    z = st.fl[1]
                    if op == "jcxz":
                        take = cx == 0
                    elif op == "loop":
                        take = cx != 0
                    elif z is None:
                        take = None
                    else:
                        take = cx != 0 and (bool(z) == (op == "loope"))
                    if take is None:
                        stop = "ZF tak diketahui"
                        break
                    if take:
                        if not (start <= t < end):
                            stop = "lompat keluar fungsi"
                            break
                        st.pc = t
                        continue
            elif op == "clc":
                st.fl[0] = 0
            elif op == "stc":
                st.fl[0] = 1
            elif op == "ret":
                stop = "ret"
                break
            elif op == "nop":
                pass
            else:
                stop = "instruksi tak didukung"
                break
            if trace_max and first and len(tr) < trace_max:
                note = ""
                if a is not None and a[0] == "r" and op not in ("cmp", "test", "push", "pop"):
                    v = _emu_get(st, a)
                    note = "%s=0x%X" % (_emu_fmt((0, "", a, None, 0, 0), 0, is64), v) if v is not None else ""
                tr.append((pc, _emu_fmt(ins, pc, is64), note))
            st.pc = nxt
        if len(finals) < EMU_MAX_FINALS:
            finals.append(st)
    return {"steps": total, "forks": forks, "stop": stop, "finals": finals, "trace": tr, "timed": timed}


def _emu_runs(m: dict) -> list:
    out: list = []
    cur = None
    for a in sorted(m):
        if cur is not None and a == cur[0] + len(cur[1]):
            cur[1].append(m[a])
        else:
            if cur is not None:
                out.append(cur)
            cur = [a, bytearray([m[a]])]
    if cur is not None:
        out.append(cur)
    return out


def _emu_collect(d: bytes, L: dict, finals: list) -> tuple[list, list, int]:
    """(string, buffer, tulisan_tak_terselesaikan). string: dict kind / va / text / wide / ops; buffer: dict va / len / kind / preview."""
    strs: dict = {}
    bufs: dict = {}
    unres = 0
    for st in finals:
        unres = max(unres, st.unres)
        stk = {a: v for a, v in st.ov.items() if v is not None and st.lo <= a < st.hi}
        dat = {}
        for a, v in st.ov.items():
            if v is None or st.lo <= a < st.hi:
                continue
            off = _va_off(L, a)
            if off is None or off >= len(d) or d[off] != v:
                dat[a] = v
        ops = sorted(st.ops & _EMU_STRONG)
        for kind, m in (("stack", stk), ("data", dat)):
            for addr, bs in _emu_runs(m):
                raw = bytes(bs)
                if kind == "data" and len(raw) >= 8:
                    pr = sum(1 for x in raw if 0x20 <= x < 0x7F or x in (9, 10, 13)) / len(raw)
                    k = "PE" if raw[:2] == b"MZ" and b"PE\0\0" in raw[:0x600] else ("teks" if pr >= 0.85 else "biner")
                    if (k in ("PE", "teks") or (len(raw) >= 32 and ops)) and (addr not in bufs) and len(bufs) < 24:
                        bufs[addr] = {"va": "0x%X" % addr, "len": len(raw), "kind": k, "ops": ops,
                                      "preview": "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in raw[:48])}
                if len(raw) < 5:
                    continue
                for mt in _EMU_RX_A.finditer(raw):
                    t = mt.group().decode("ascii")
                    if sum(ch.isalnum() for ch in t) >= max(4, int(len(t) * 0.6)) and t not in strs:
                        strs[t] = {"kind": kind, "va": "0x%X" % (addr + mt.start()), "text": t, "wide": False, "ops": ops}
                for mt in _EMU_RX_W.finditer(raw):
                    t = raw[mt.start():mt.end()].decode("utf-16le")
                    if sum(ch.isalnum() for ch in t) >= max(4, int(len(t) * 0.6)) and t not in strs:
                        strs[t] = {"kind": kind, "va": "0x%X" % (addr + mt.start()), "text": t, "wide": True, "ops": ops}
    return list(strs.values()), list(bufs.values()), unres


def _emu_enrich(info: dict, ctx: dict, d: bytes) -> None:
    """Dipanggil di akhir _re_lab (setelah CFG): info["emu"] (kunci baru). Tidak pernah melempar; tidak mengubah skor."""
    try:
        L, F = ctx["L"], ctx["F"]
        is64 = L["is64"]
        xs = [(L["base"] + s["va"], L["base"] + s["va"] + max(s["vsize"], s["rsize"])) for s in L["xsecs"]]
        top_va = []
        for f in info.get("functions", []):
            try:
                top_va.append(int(f["va"], 16))
            except ValueError:
                pass
        fl = ctx["fl"]
        ends: dict = {}
        for k, s in enumerate(fl):          # semua awal fungsi yang ditemukan (F hanya memuat yang punya pemanggil / panggilan API)
            sec_end = next((b for a_, b in xs if a_ <= s < b), s)
            ends[s] = min(fl[k + 1] if k + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
        first = [L["entry_va"]] if L.get("entry_va") in ends else []
        rest = sorted((s for s in fl if s not in F), key=lambda s: s - ends[s])
        todo = list(dict.fromkeys(first + [s for s in top_va if s in ends] + [s for s, _f in sorted(F.items(), key=lambda kv: -kv[1]["size"]) if s in ends] + rest))[:EMU_MAX_FUNCS]
        deadline = time.monotonic() + EMU_TIME
        have = [x["text"] for x in info.get("stack_strings", [])]
        nm = lambda s: F[s]["name"] if s in F else ("start" if s == L.get("entry_va") else (L["exports"].get(s) or "sub_%08X" % s))
        n_an = steps = unres = 0
        partial = False
        sout: list = []
        bout: list = []
        seen: set = set()
        for s in todo:
            if time.monotonic() > deadline or steps >= EMU_MAX_TOTAL:
                partial = True
                break
            if s in ctx["thunks"] or ends[s] - s < 6:
                continue
            r = _emu_func(d, L, s, ends[s], is64, deadline, max_total=EMU_MAX_TOTAL - steps)
            if r is None:
                continue
            n_an += 1
            steps += r["steps"]
            if r["timed"]:
                partial = True
            ss, bb, u = _emu_collect(d, L, r["finals"])
            unres += u
            for x in ss:
                t = x["text"]
                plain = t.encode("utf-16le" if x["wide"] else "latin-1") in d
                if plain or t in seen or len(sout) >= EMU_MAX_RESULTS:
                    continue
                seen.add(t)
                clean = _clean(t)[:100]
                sout.append({"va": x["va"], "func": "0x%X" % s, "name": _clean(nm(s)), "text": clean, "kind": x["kind"], "wide": x["wide"], "ops": x["ops"],
                             "tag": _str_tag(t), "new": not any(clean == h or clean in h or h in clean for h in have)})
            for x in bb:
                if len(bout) < 16:
                    bout.append(dict(x, func="0x%X" % s, name=_clean(nm(s)), preview=_clean(x["preview"])))
        info["emu"] = {"analyzed": n_an, "steps": steps, "partial": partial, "unresolved_writes": unres, "strings": sout, "buffers": bout}
    except Exception as e:
        info["notes"].append("Emulasi gagal: %s" % type(e).__name__)


def _render_emu(r: dict, a, compact: bool, defang: bool) -> None:
    c = r.get("emu")
    if not c or not c["analyzed"]:
        return
    new = [x for x in c["strings"] if x["new"]]
    a("   Emulasi mikro: %d fungsi / %d langkah, %d string tersembunyi (%d baru), %d buffer dimodifikasi%s" % (
        c["analyzed"], c["steps"], len(c["strings"]), len(new), len(c["buffers"]), " | TERPOTONG (batas waktu / langkah)" if c["partial"] else ""))
    for x in (new if compact else c["strings"])[: (3 if compact else 10)]:
        a("   ! string hasil emulasi: %s [%s%s] di %s %s%s" % (_df(x["text"], defang), x["tag"], ", UTF-16" if x["wide"] else "", x["name"], x["func"],
                                                           (" | operasi: " + "/".join(x["ops"])) if x["ops"] else ""))
    for x in c["buffers"][: (2 if compact else 6)]:
        a("   ! buffer dimodifikasi emulasi (%s): %d byte @%s di %s%s | %s" % (x["kind"], x["len"], x["va"], x["name"], (" (" + "/".join(x["ops"]) + ")") if x["ops"] else "",
                                                                             _df(x["preview"], defang)))


def emu_text(path, at=None, defang: bool = True) -> str:
    """Ringkasan emulasi mikro (tanpa `at`) atau jejak + hasil satu fungsi (at = 'entry' / 0xVA). CLI --emu, API action 'emu'."""
    try:
        d, size = _cfg_read(path)
        info, ctx, err = _relab_any(d, size)
    except Exception as e:
        return "Emulasi gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    if not info:
        return "Emulasi: %s." % (err or "tidak ada kode yang bisa dianalisis")
    if at is None:
        L_: list = []
        _render_emu(info, L_.append, False, defang)
        return "\n".join(L_) if L_ else "Emulasi: tidak ada string / buffer tersembunyi yang berhasil diturunkan."
    Lx, fl = ctx["L"], ctx["fl"]
    try:
        va = Lx["entry_va"] if str(at).lower() == "entry" else int(str(at), 0)
    except ValueError:
        return "Emulasi: alamat tidak valid (pakai entry atau 0xVA)."
    i = bisect.bisect_right(fl, va) - 1
    if i < 0:
        return "Emulasi: tidak ada fungsi yang memuat 0x%X." % va
    s = fl[i]
    xs = [(Lx["base"] + x["va"], Lx["base"] + x["va"] + max(x["vsize"], x["rsize"])) for x in Lx["xsecs"]]
    sec_end = next((b for a_, b in xs if a_ <= s < b), s)
    e = min(fl[i + 1] if i + 1 < len(fl) else sec_end, sec_end, s + 0x10000)
    r = _emu_func(d, Lx, s, e, Lx["is64"], time.monotonic() + EMU_TIME, trace_max=200)
    if not r:
        return "Emulasi: fungsi di 0x%X tidak bisa dibaca." % s
    ss, bb, unres = _emu_collect(d, Lx, r["finals"])
    out = ["Fungsi 0x%X: %d langkah, %d jalur (%d fork), berhenti: %s%s" % (s, r["steps"], len(r["finals"]), r["forks"], r["stop"] or "-",
                                                                          ", %d tulisan ke alamat tak diketahui diabaikan" % unres if unres else "")]
    out += ["  0x%X  %-34s %s" % (pc, t, ("; " + nt) if nt else "") for pc, t, nt in r["trace"]]
    for x in ss[:20]:
        out.append("  string [%s%s] @%s: %s%s" % (x["kind"], ", UTF-16" if x["wide"] else "", x["va"], _df(_clean(x["text"])[:100], defang),
                                               (" | operasi: " + "/".join(x["ops"])) if x["ops"] else ""))
    for x in bb[:8]:
        out.append("  buffer dimodifikasi (%s): %d byte @%s | %s" % (x["kind"], x["len"], x["va"], _df(_clean(x["preview"]), defang)))
    return "\n".join(out)


def _v98_enrich(d: bytes, rep: dict) -> None:
    pe = rep.get("pe")
    rep["relab"] = None
    if not (pe and not pe.get("broken")) and not rep.get("elf"):
        return
    try:
        info, _ctx = _re_lab(d, pe) if (pe and not pe.get("broken")) else _relab_elf(d)
    except Exception as e:
        rep["warn"].append("RE Lab gagal: %s" % type(e).__name__)
        return
    rep["relab"] = info
    if not info:
        return
    for x in info["notes"]:
        rep["warn"].append("RE Lab: " + x)
    for x in info["anti"]:
        if x["technique"].startswith(("syscall", "Heaven")):
            rep["warn"].append("RE Lab: %s (%d lokasi, pertama 0x%s)" % (x["technique"], x["count"], x["first"][2:]))
    cf_ = info.get("cfg") or {}
    for x in (cf_.get("decrypt_loops") or [])[:2]:
        rep["warn"].append("RE Lab: kandidat loop dekripsi di %s %s (%s)" % (x["name"], x["func"], "/".join(x["ops"])))
    for x in (cf_.get("flatten") or [])[:1]:
        rep["warn"].append("RE Lab: kandidat control-flow flattening di %s %s (%d sisi balik)" % (x["name"], x["func"], x["back_edges"]))
    for x in [x for x in ((info.get("emu") or {}).get("strings") or []) if x["new"] and (x["tag"] != "menarik" or x["ops"])][:3]:
        rep["warn"].append("RE Lab: emulasi mikro menurunkan string tersembunyi di %s %s: %s [%s]" % (x["name"], x["func"], _clean(x["text"])[:60], x["tag"]))
    for x in ((info.get("emu") or {}).get("buffers") or [])[:1]:
        if x["kind"] in ("PE", "teks"):
            rep["warn"].append("RE Lab: loop kecil mendekripsi buffer (%s, %d byte) di %s %s" % (x["kind"], x["len"], x["name"], x["func"]))
    if info["api_hashes"]:
        rep["warn"].append("RE Lab: konstanta API hash terdeteksi (%s): kemungkinan resolusi API tersembunyi / shellcode" % ", ".join(h["api"] for h in info["api_hashes"][:3]))


def _render_v98(rep: dict, a, compact: bool, defang: bool) -> None:
    r = rep.get("relab")
    if not r:
        return
    a("RE Lab : %s | base %s | %d fungsi, %d panggilan API terpetakan (%d slot IAT), %d string dirujuk kode" % (
        r["arch"], r["image_base"], r["n_functions"], r["n_api_sites"], r["n_iat"], r["n_strrefs"]))
    st = r["entry_stub"]
    if r["entry"]:
        a("   entry %s: %s%s" % (r["entry"], st["hex"], (" | " + st["note"]) if st["note"] else ""))
    for f in r["functions"][: (3 if compact else RELAB_TOP)]:
        a("   * %s %s (%s, caller %d, callee %d) skor %d%s%s%s" % (
            f["name"], f["va"], _human(f["size"]), f["callers"], f["callees"], f["score"],
            (" | " + "; ".join(f["tags"])) if f["tags"] else "", (" | API: " + ", ".join(x.split("!")[-1] for x in f["apis"][:8])) if f["apis"] else "",
            (" | anti: " + ", ".join(f["anti"])) if f["anti"] else ""))
        if f["strings"] and not compact:
            a("       string: " + " | ".join(_df(x, defang) for x in f["strings"][:3]))
    _render_cfg(r, a, compact)
    _render_emu(r, a, compact, defang)
    if compact:
        for x in r["anti"][:3]:
            a("   anti-analisis: %s x%d" % (x["technique"], x["count"]))
        return
    for x in r["anti"]:
        a("   anti-analisis: %s x%d (pertama %s)" % (x["technique"], x["count"], x["first"]))
    if r["api_hashes"]:
        a("   API hashing: " + ", ".join("%s @%s" % (h["api"], h["offset"]) for h in r["api_hashes"][:8]))
    if r["stack_strings"]:
        a("   stack string: " + " | ".join("%s [%s]" % (_df(x["text"], defang), x["tag"]) for x in r["stack_strings"][:8]))
    if r["string_refs"]:
        a("   string yang dirujuk kode:")
        for e in r["string_refs"][:8]:
            a("     %s [%s] %s <- %s" % (e["va"], e["tag"], _df(e["text"], defang), ", ".join(e["funcs"]) or "?"))
    if r["api_top"]:
        a("   API paling sering dipanggil: " + ", ".join("%s x%d" % (k.split("!")[-1], n) for k, n in r["api_top"][:10]))


def _score_v98(rep: dict, add) -> None:
    r = rep.get("relab")
    if not r:
        return
    keys = [x["technique"] for x in r["anti"]]
    if any(k.startswith("syscall") for k in keys):
        add(3, "syscall langsung (melewati hook API / EDR)")
    if any(k.startswith("Heaven") for k in keys):
        add(2, "Heaven's Gate (lompat ke mode 64-bit dari WoW64)")
    if r["api_hashes"]:
        add(3, "API hashing (konstanta hash API dikenal ditemukan)")
    if any("pola ransomware" in t for f in r["functions"] for t in f["tags"]):
        add(3, "satu fungsi menggabungkan kripto + enumerasi berkas")
    elif any(t in ("injeksi proses", "unduh & jalankan") for f in r["functions"] for t in f["tags"]):
        add(1, "satu fungsi merangkai API injeksi / unduh-jalankan")
    if any(x["tag"] not in ("menarik",) for x in r["stack_strings"]):
        add(2, "string sensitif disusun di stack (menghindari pencarian string)")
    n_anti = len([k for k in keys if not k.startswith(("CPUID", "ROR"))])
    if n_anti >= 3:
        add(2, "banyak teknik anti-analisis tingkat instruksi (%d)" % n_anti)


# ----------------------------- API / CLI v98 --------------------------------


def re_lab_path(path) -> dict:
    """Analisis RE Lab langsung dari path (tanpa hash / triase penuh). Mengembalikan dict (atau {'error': ...})."""
    try:
        f, size = _open_regular(path)
        with f:
            sha = _sha256_of(f, size) if _cache_dir() is not None else None
            if sha:
                hit = _cache_load(sha, "re")
                if hit is not None:
                    return hit
            d = f.read(MAX_SCAN)
        info, _c, err = _relab_any(d, size)
        if info and sha:
            _cache_store(sha, "re", info, lambda back: _verify_relab(info, back))
        return info or {"error": (err or "tidak ada bagian kode yang bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64"}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def re_text(path, defang: bool = True, compact: bool = False) -> str:
    r = re_lab_path(path)
    if "error" in r:
        return "RE Lab gagal: " + r["error"]
    L: list[str] = []
    _render_v98({"relab": r}, L.append, compact, defang)
    return "\n".join(L)


def xref_text(path, query: str, max_items: int = 40) -> str:
    """Cari xref: nama API (mis. 'VirtualAlloc'), potongan string, atau VA fungsi. Menunjukkan fungsi pemanggil / pemakai."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        info, ctx, err = _relab_any(d, size)
        if not ctx:
            return "XREF gagal: %s." % (err or "tidak bisa dianalisis")
        q = str(query).strip()
        ql = q.lower()
        out = []
        for api, vs in ctx["sites"].items():
            if ql in api.lower():
                out.append("API %s: %d lokasi" % (api, len(vs)))
                for va, fs in vs[:max_items]:
                    out.append("   0x%X dalam %s" % (va, ctx["F"][fs]["name"] if fs in ctx["F"] else "?"))
        for e in ctx["sref"].values():
            if ql in e["text"].lower():
                out.append("string 0x%X (%s): %s" % (e["va"], e["kind"], _clean(e["text"])[:100]))
                for fs in sorted(e["funcs"])[:max_items]:
                    out.append("   dipakai oleh %s (0x%X)" % (ctx["F"][fs]["name"], fs))
        try:
            tv = int(q, 0)
            fobj_ = ctx["F"].get(tv)
            if fobj_:
                out.append("fungsi %s 0x%X: %d caller" % (fobj_["name"], tv, fobj_["callers"]))
                for c, fo in ctx["F"].items():
                    if tv in fo["callees"]:
                        out.append("   dipanggil dari %s (0x%X)" % (fo["name"], c))
        except ValueError:
            pass
        return "\n".join(out[:max_items * 3]) if out else "XREF: tidak ada hasil untuk '%s'." % _clean(q)[:60]
    except Exception as e:
        return "XREF gagal: %s: %s" % (type(e).__name__, str(e)[:120])


_CS_ARCHS = {   # nama -> (atribut ARCH, [atribut MODE], label)
    "x86": ("CS_ARCH_X86", ["CS_MODE_32"], "x86"), "x64": ("CS_ARCH_X86", ["CS_MODE_64"], "x64"),
    "arm": ("CS_ARCH_ARM", ["CS_MODE_ARM"], "ARM"), "armbe": ("CS_ARCH_ARM", ["CS_MODE_ARM", "CS_MODE_BIG_ENDIAN"], "ARM BE"),
    "thumb": ("CS_ARCH_ARM", ["CS_MODE_THUMB"], "Thumb"),
    "arm64": ("CS_ARCH_ARM64", ["CS_MODE_ARM"], "AArch64"),
    "mips": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_BIG_ENDIAN"], "MIPS32 BE"), "mipsel": ("CS_ARCH_MIPS", ["CS_MODE_MIPS32", "CS_MODE_LITTLE_ENDIAN"], "MIPS32 LE"),
    "mips64": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_BIG_ENDIAN"], "MIPS64 BE"), "mips64el": ("CS_ARCH_MIPS", ["CS_MODE_MIPS64", "CS_MODE_LITTLE_ENDIAN"], "MIPS64 LE"),
    "ppc": ("CS_ARCH_PPC", ["CS_MODE_32", "CS_MODE_BIG_ENDIAN"], "PowerPC32"), "ppc64": ("CS_ARCH_PPC", ["CS_MODE_64", "CS_MODE_BIG_ENDIAN"], "PowerPC64"),
    "riscv32": ("CS_ARCH_RISCV", ["CS_MODE_RISCV32"], "RISC-V 32"), "riscv64": ("CS_ARCH_RISCV", ["CS_MODE_RISCV64"], "RISC-V 64"),
    "sparc": ("CS_ARCH_SPARC", ["CS_MODE_BIG_ENDIAN"], "SPARC"),
}
_ELF_TO_ARCH = {3: "x86", 62: "x64", 40: "arm", 183: "arm64", 8: "mips", 20: "ppc", 243: "riscv64"}
_MACHO_TO_ARCH = {7: "x86", 0x01000007: "x64", 12: "arm", 0x0100000C: "arm64", 18: "ppc", 0x01000012: "ppc64"}


def _gen_elf_map(d: bytes):
    """ELF -> (arsitektur, entry VA, [(vaddr, offset, filesz)]) atau None."""
    if len(d) < 52 or d[:4] != b"\x7fELF":
        return None
    is64, en = d[4] == 2, ("<" if d[5] == 1 else ">")
    mach = struct.unpack_from(en + "H", d, 18)[0]
    if is64:
        entry, phoff = struct.unpack_from(en + "QQ", d, 24)
        phentsz, phnum = struct.unpack_from(en + "HH", d, 54)
    else:
        entry, phoff = struct.unpack_from(en + "II", d, 24)[0], struct.unpack_from(en + "I", d, 28)[0]
        phentsz, phnum = struct.unpack_from(en + "HH", d, 42)
    segs = []
    for i in range(min(phnum, 128)):
        o = phoff + i * phentsz
        if o + (56 if is64 else 32) > len(d):
            break
        if is64:
            pt, pf, poff, va, _pa, fsz, _m, _a = struct.unpack_from(en + "IIQQQQQQ", d, o)
        else:
            pt, poff, va, _pa, fsz, _m, pf, _a = struct.unpack_from(en + "IIIIIIII", d, o)
        if pt == 1 and fsz:
            segs.append((va, poff, fsz))
    arch = _ELF_TO_ARCH.get(mach, "")
    if arch == "arm" and en == ">":
        arch = "armbe"
    elif arch == "mips":
        arch = ("mips64" if is64 else "mips") if en == ">" else ("mips64el" if is64 else "mipsel")
    elif arch == "ppc" and is64:
        arch = "ppc64"
    elif arch == "riscv64" and not is64:
        arch = "riscv32"
    return arch, entry, segs, "ELF"


def _gen_macho_map(d: bytes):
    """Mach-O tipis / fat (irisan pertama) -> (arsitektur, entry VA, [(vmaddr, fileoff, filesize)]) atau None."""
    base = 0
    if d[:4] in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None
        base = struct.unpack_from(">I", d, 16)[0] if d[3] == 0xBE else struct.unpack_from(">Q", d, 16)[0]
    m = d[base:base + 4]
    if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe"):
        e = "<"
    elif m in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
        e = ">"
    else:
        return None
    is64 = 0xCF in (m[0], m[3])
    cpu, _sub, _ft, ncmds, szcmds, _fl = struct.unpack_from(e + "IIIIII", d, base + 4)
    off = base + (32 if is64 else 28)
    end = min(len(d), off + szcmds)
    segs, text_va, entry_off = [], None, None
    for _ in range(min(ncmds, 600)):
        if off + 8 > end:
            break
        cmd, csz = struct.unpack_from(e + "II", d, off)
        if csz < 8 or off + csz > end:
            break
        if cmd in (0x1, 0x19) and csz >= (72 if cmd == 0x19 else 56):
            fmt = e + ("16sQQQQ" if cmd == 0x19 else "16sIIII")
            nm, va, _vsz, fo, fsz = struct.unpack_from(fmt, d, off + 8)
            if fsz:
                segs.append((va, base + fo, fsz))
            if nm.startswith(b"__TEXT"):
                text_va = va
        elif cmd == 0x80000028 and csz >= 16:
            entry_off = struct.unpack_from(e + "Q", d, off + 8)[0]
        off += csz
    entry = 0
    if entry_off is not None and text_va is not None:
        entry = text_va + entry_off
    elif segs:
        entry = segs[0][0]
    arch = _MACHO_TO_ARCH.get(cpu, "")
    return arch, entry, segs, "Mach-O"


def _disasm_generic(d: bytes, at, count: int, arch, was_pe: bool = False) -> str:
    """Disassembly di luar RE Lab PE: ELF, Mach-O, atau berkas mentah (alamat 'at' = offset berkas)."""
    fmt, entry, segs, a = "mentah", 0, [], None
    mp = None
    try:
        mp = _gen_elf_map(d) or _gen_macho_map(d)
    except (struct.error, IndexError):
        mp = None
    if mp:
        a, entry, segs, fmt = mp
    elif was_pe:
        fmt = "PE (bukan x86 / x64)"
    a = (str(arch).lower().strip() if arch else None) or a or "x64"
    if a not in _CS_ARCHS:
        return "DISASM gagal: arsitektur '%s' belum didukung. Pilihan: %s" % (_clean(a)[:20], " ".join(sorted(_CS_ARCHS)))
    s = str(at).strip().lower()
    note_raw = ""
    if s.startswith("off:"):
        off = int(s[4:], 0)
        va = next((v + (off - o) for v, o, n in segs if o <= off < o + n), off)
    elif s in ("entry", "start", ""):
        if segs:
            va = entry
        else:
            va, note_raw = 0, " (berkas mentah: mulai dari offset 0; pakai off:0x.. untuk lokasi lain)"
    else:
        va = int(s, 0)
    if segs:
        off = next((o + (va - v) for v, o, n in segs if v <= va < v + n), None)
    else:
        off = va
    if off is None or off < 0 or off >= len(d):
        return "DISASM gagal: alamat 0x%X tidak berada di data berkas." % va
    count = max(1, min(int(count), 400))
    code = d[off:off + count * 16 + 16]
    try:
        import capstone
    except ImportError:
        hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
        return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
    ca, modes, label = _CS_ARCHS[a]
    if not hasattr(capstone, ca) or not all(hasattr(capstone, m_) for m_ in modes):
        return "DISASM gagal: capstone yang terpasang belum mendukung %s (coba pip install -U capstone)." % label
    mode = 0
    for m_ in modes:
        mode |= getattr(capstone, m_)
    md = capstone.Cs(getattr(capstone, ca), mode)
    lines = []
    for i in md.disasm(code, va):
        lines.append("   %08X  %-24s %s %s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str))
        if len(lines) >= count:
            break
    if not lines:
        return "DISASM @0x%X (%s, %s): tidak ada instruksi valid di sini; coba arch lain (arch=thumb / arm64 / x86 ...) atau alamat lain.\n%s" % (
            va, fmt, label, "\n".join("   %08X  %s" % (va + k, code[k:k + 16].hex(" ")) for k in range(0, min(len(code), 48), 16)))
    return "DISASM @0x%X (%s, %s)%s:\n%s" % (va, fmt, label, note_raw, "\n".join(lines))


def disasm_text(path, at="entry", count: int = 40, arch=None) -> str:
    """Disassembly dari entry / VA (0x...), 'rva:0x..', 'off:0x..'. Butuh pustaka opsional capstone; tanpa itu menampilkan hex.
    PE x86 / x64: RE Lab penuh (nama API / fungsi). ELF, Mach-O (tipis / fat), dan berkas mentah (shellcode, firmware, dump):
    disassembly generik lewat capstone. arch (opsional, memaksa arsitektur): x86 x64 arm thumb arm64 mips mips64 mipsel ppc ppc64 riscv32 riscv64 sparc."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(MAX_SCAN)
        pe = _parse_pe(d, size)
        info, ctx, _err = _relab_any(d, size)
        if not ctx or (arch and str(arch).lower() not in ("x86", "x64")):
            return _disasm_generic(d, at, count, arch, bool(pe and not pe.get("broken")))
        L = ctx["L"]
        s = str(at).strip().lower()
        if s in ("entry", "start", ""):
            va = L["entry_va"]
        elif s.startswith("rva:"):
            va = L["base"] + int(s[4:], 0)
        elif s.startswith("off:"):
            o_ = int(s[4:], 0)
            va = next((L["base"] + x["va"] + (o_ - x["rptr"]) for x in L["secs"] if x["rptr"] <= o_ < x["rptr"] + x["rsize"]), 0)
        else:
            va = int(s, 0)
            va = va if va >= L["base"] else L["base"] + va
        off = _va_off(L, va)
        if not va or off is None:
            return "DISASM gagal: alamat tidak berada di data berkas."
        count = max(1, min(int(count), 400))
        code = d[off:off + count * 15 + 16]
        names = dict(L["iat"])
        for tv, tn in ctx["thunks"].items():
            names[tv] = tn.split("!")[-1] + "@plt"
        for fv, fo in ctx["F"].items():
            names[fv] = fo["name"]
        try:
            import capstone
        except ImportError:
            hexs = "\n".join("   %08X  %s" % (va + i, code[i:i + 16].hex(" ")) for i in range(0, min(len(code), 96), 16))
            return "Disassembler memerlukan pustaka opsional 'capstone' (pip install capstone). Tampilan hex pada 0x%X:\n%s" % (va, hexs)
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64 if L["is64"] else capstone.CS_MODE_32)
        lines = []
        for i in md.disasm(code, va):
            note = ""
            m = re.search(r"\[rip ([+-]) (0x[0-9a-f]+)\]", i.op_str)
            if m:
                t = i.address + i.size + (int(m.group(2), 16) * (1 if m.group(1) == "+" else -1))
                note = names.get(t, "")
            else:
                m = re.search(r"0x[0-9a-f]+", i.op_str)
                if m and i.mnemonic in ("call", "jmp"):
                    note = names.get(int(m.group(0), 16), "")
                elif m and not L["is64"] and "[" in i.op_str:
                    note = names.get(int(m.group(0), 16), "")
            lines.append("   %08X  %-24s %s %s%s" % (i.address, i.bytes.hex(" "), i.mnemonic, i.op_str, ("   ; " + note) if note else ""))
            if len(lines) >= count:
                break
        return "DISASM @0x%X (%s%s):\n%s" % (va, "ELF " if d[:4] == b"\x7fELF" else "", "x64" if L["is64"] else "x86", "\n".join(lines))
    except Exception as e:
        return "DISASM gagal: %s: %s" % (type(e).__name__, str(e)[:120])


# ---------------------------------------------------------------------------
# v98.2: aturan kemampuan berbasis nama API, diturunkan dari mandiant/capa-rules (Apache-2.0, https://github.com/mandiant/capa-rules).
# Hanya aturan yang murni daftar API (or / and) dan punya pemetaan ATT&CK yang dipilih; aturan capa lain butuh analisis aliran kode.
# Dicocokkan di tingkat BERKAS (bukan fungsi), jadi tetap PETUNJUK. Tidak masuk skor. Atribusi: lihat NOTICE di docstring modul.
# (nama aturan, namespace, ATT&CK, operator, himpunan API huruf kecil)
# ---------------------------------------------------------------------------

_CAPA_RULES = (
    ('acquire credentials from Windows Credential Manager', 'collection', ('T1555.004',), 'or', ('credenumerate',)),
    ('get geographical location', 'collection', ('T1614',), 'or', ('getlocaleinfo', 'getlocaleinfoex', 'getusergeoid', 'getgeoinfo')),
    ('register raw input devices', 'collection/keylog', ('T1056.001',), 'or', ('registerrawinputdevices',)),
    ('log keystrokes via direct input', 'collection/keylog', ('T1056.001',), 'or', ('directinput8create', 'directinputcreateex', 'directinputcreatew', 'directinputcreatea')),
    ('log keystrokes via polling', 'collection/keylog', ('T1056.001',), 'or', ('getasynckeystate', 'getkeystate', 'getkeyboardstate', 'vkkeyscan', 'vkkeyscanex', 'getkeynametext')),
    ('get domain trust relationships', 'collection/network', ('T1482',), 'or', ('dsenumeratedomaintrusts',)),
    ('capture microphone audio', 'collection/microphone', ('T1123',), 'or', ('waveinopen', 'waveinaddbuffer', 'waveinstart')),
    ('clear Windows event logs remotely', 'anti-analysis/anti-forensic/clear-logs', ('T1070.001',), 'and', ('evtopensession', 'evtclearlog')),
    ('encrypt data using RC4 via SystemFunction033', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction033',)),
    ('encrypt data using RC4 via SystemFunction032', 'data-manipulation/encryption/rc4', ('T1027',), 'or', ('systemfunction032',)),
    ('impersonate user', 'host-interaction/user', ('T1134.001',), 'or', ('logonuser',)),
    ('get UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('ntenumeratesystemenvironmentvaluesex', 'ntquerysystemenvironmentvalueex', 'ntquerysystemenvironmentvalue', 'getfirmwareenvironmentvariable', 'getfirmwareenvironmentvariableex', 'exgetfirmwareenvironmentvariable')),
    ('set UEFI variable', 'host-interaction/bootloader', ('T1542.001',), 'or', ('exsetfirmwareenvironmentvariable', 'setfirmwareenvironmentvariable', 'setfirmwareenvironmentvariableex')),
    ('switch active desktop', 'host-interaction/gui', ('T1622',), 'and', ('createdesktop', 'switchdesktop')),
    ('attach user process memory', 'host-interaction/process/inject', ('T1055',), 'and', ('kestackattachprocess', 'keunstackdetachprocess')),
    ('install driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntloaddriver', 'zwloaddriver')),
    ('unload driver', 'host-interaction/driver', ('T1543.003',), 'or', ('ntunloaddriver', 'zwunloaddriver')),
    ('delete network filter via WFP API', 'host-interaction/network/traffic/filter', ('T1565.002', 'T1562.004'), 'or', ('fwpmfilterdeletebyid0', 'fwpmfilterdeletebykey0')),
    ('shutdown system', 'host-interaction/os', ('T1529',), 'or', ('exitwindowsex', 'exitwindows', 'initiatesystemshutdownex', 'initiatesystemshutdown', 'initiateshutdown')),
)


_CAPA_SETS = [(n, ns, att, op, frozenset(apis)) for n, ns, att, op, apis in _CAPA_RULES]


def _capa_match(api_names) -> list[dict]:
    """Cocokkan nama impor dengan aturan capa bawaan. 'or': minimal satu API; 'and': semua API harus ada."""
    out = []
    names = [str(a) for a in api_names]
    if not names:
        return out
    for n, ns, att, op, S in _CAPA_SETS:
        hit = sorted({x.split("!")[-1] for x in names if _api_match(x, S)})
        if not hit:
            continue
        if op == "and" and len({h.lower() for h in hit}) < len(S):
            continue
        out.append({"name": n, "namespace": ns, "attack": list(att), "apis": hit[:6]})
    return out


def _capa_enrich(rep: dict, api_names) -> None:
    try:
        rep["capa"] = _capa_match(api_names)
    except Exception as e:
        rep["capa"] = []
        rep["warn"].append("aturan capa gagal: %s" % type(e).__name__)


def _render_capa(rep: dict, a, compact: bool) -> None:
    c = rep.get("capa")
    if not c:
        return
    a("Aturan capa (subset berbasis API, tingkat berkas; PETUNJUK, bukan bukti perilaku): %d cocok" % len(c))
    for x in c[: (3 if compact else 20)]:
        a("   - %s [%s] <- %s" % (_clean(x["name"]), ", ".join(x["attack"]), ", ".join(_clean(h) for h in x["apis"])))


# ---------------------------------------------------------------------------
# v98.2: unpack UPX statis lewat `upx -d` (opsional; hanya bila alat `upx` terpasang). Berkas TIDAK dijalankan: `upx -d` hanya
# mendekompresi. Dikerjakan pada salinan sementara dengan batas waktu dan ukuran; hasil disimpan di outdir lalu ditriase.
# ---------------------------------------------------------------------------

UNPACK_MAX = 256 * 1024 * 1024
UNPACK_TIMEOUT = 40
UNPACK_MEM = 1536 * 1024 * 1024      # batas memori proses upx (RLIMIT_AS, hanya POSIX)


def _upx_limits():
    """preexec_fn untuk POSIX: batasi memori, waktu CPU, dan ukuran berkas yang boleh ditulis upx. Pada Windows tidak ada (None);
    di sana batas ukuran hasil tetap diperiksa setelah upx selesai, dan timeout tetap berlaku."""
    if os.name != "posix":
        return None

    def _apply():
        import resource
        for lim, val in ((resource.RLIMIT_AS, UNPACK_MEM), (resource.RLIMIT_CPU, UNPACK_TIMEOUT + 5),
                         (resource.RLIMIT_FSIZE, UNPACK_MAX + (1 << 20)), (resource.RLIMIT_CORE, 0)):
            try:
                resource.setrlimit(lim, (val, val))
            except (ValueError, OSError):
                pass
    return _apply


def unpack_upx(path, outdir) -> dict:
    import shutil
    import subprocess
    import tempfile
    try:
        upx = shutil.which("upx")
        if not upx:
            return {"ok": False, "error": "alat 'upx' tidak ditemukan di PATH (pasang UPX dari https://upx.github.io lalu coba lagi)"}
        f, size = _open_regular(path)
        if size > UNPACK_MAX:
            f.close()
            return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
        out = Path(outdir).expanduser().resolve()
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in.bin"
            dst = Path(td) / "out.bin"
            found, tail, left = False, b"", size
            with f, open(src, "wb") as sf:           # salin bertahap (tanpa memuat seluruh berkas), sambil mencari penanda UPX
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    left -= len(chunk)
                    sf.write(chunk)
                    if not found:
                        win = tail + chunk
                        found = b"UPX!" in win or b"UPX0" in win
                        tail = win[-3:]
            if not found:
                return {"ok": False, "error": "tidak ada penanda UPX di berkas; tidak dicoba"}
            out.mkdir(parents=True, exist_ok=True)
            r = subprocess.run([upx, "-d", "-q", "-o", str(dst), str(src)], capture_output=True, timeout=UNPACK_TIMEOUT,
                               stdin=subprocess.DEVNULL, cwd=td, env={"PATH": os.environ.get("PATH", ""), "LANG": "C"},
                               preexec_fn=_upx_limits())
            if r.returncode != 0 or not dst.exists():
                return {"ok": False, "error": "upx -d gagal: " + _clean(r.stderr.decode("latin-1", "replace"))[:200]}
            if dst.stat().st_size > UNPACK_MAX:
                return {"ok": False, "error": "hasil unpack melebihi batas %d MB; dibuang" % (UNPACK_MAX >> 20)}
            data = dst.read_bytes()
        name = "%s.unpacked" % (hashlib.sha256(data).hexdigest()[:16])
        (out / name).write_bytes(data)
        return {"ok": True, "path": str(out / name), "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "upx -d melewati batas waktu %d detik" % UNPACK_TIMEOUT}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def unpack_text(path, outdir) -> str:
    r = unpack_upx(path, outdir)
    if not r["ok"]:
        return "UNPACK gagal: " + r["error"]
    return "UNPACK UPX berhasil: %s (%s, sha256 %s)\n%s" % (r["path"], _human(r["size"]), r["sha256"], triage_text(r["path"], compact=True))


# ---------------------------------------------------------------------------
# v98.3: Android lebih dalam (AndroidManifest.xml biner + metode DEX), dekoder skrip / string tersandi, hash ikon PE,
#        dan pemindaian YARA opsional (butuh yara-python; tanpa itu tidak ada yang berubah). Statis, hanya baca.
# ---------------------------------------------------------------------------

_AXML_COMP = ("activity", "activity-alias", "service", "receiver", "provider")


def _axml_strings(d: bytes, off: int) -> list[str]:
    """Baca string pool (RES_STRING_POOL_TYPE) di offset `off`. Batas: 20000 string."""
    _t, hs, csz, n, _ns, flags, sstart, _st = struct.unpack_from("<HHIIIIII", d, off)
    n = min(n, 20000)
    utf8 = bool(flags & 0x100)
    out = []
    base = off + sstart
    for i in range(n):
        p = off + hs + 4 * i
        if p + 4 > len(d):
            break
        o = base + struct.unpack_from("<I", d, p)[0]
        if o >= len(d):
            out.append("")
            continue
        try:
            if utf8:
                l1 = d[o]
                o += 2 if l1 & 0x80 else 1
                b1 = d[o]
                if b1 & 0x80:
                    ln = ((b1 & 0x7F) << 8) | d[o + 1]
                    o += 2
                else:
                    ln = b1
                    o += 1
                out.append(d[o:o + min(ln, 600)].decode("utf-8", "replace"))
            else:
                ln = struct.unpack_from("<H", d, o)[0]
                o += 2
                if ln & 0x8000:
                    ln = ((ln & 0x7FFF) << 16) | struct.unpack_from("<H", d, o)[0]
                    o += 2
                out.append(d[o:o + 2 * min(ln, 600)].decode("utf-16le", "replace"))
        except (IndexError, struct.error):
            out.append("")
    return out


def _axml_summary(d: bytes) -> dict | None:
    """Uraikan AndroidManifest.xml biner (AXML) menjadi ringkasan: paket, versi, SDK, komponen, aksi intent, izin."""
    if len(d) < 16 or struct.unpack_from("<H", d, 0)[0] != 0x0003:
        return None
    total = min(struct.unpack_from("<I", d, 4)[0], len(d))
    pos, strings = struct.unpack_from("<H", d, 2)[0], []
    info: dict = {"package": "", "version": "", "min_sdk": "", "target_sdk": "", "debuggable": None, "cleartext": None, "backup": None,
                  "components": {k: [] for k in _AXML_COMP}, "exported": [], "actions": [], "perms": [], "app_class": ""}
    stack: list[str] = []
    n_el = 0
    while pos + 8 <= total and n_el < 20000:
        ct, hs, csz = struct.unpack_from("<HHI", d, pos)
        if csz < 8 or pos + csz > len(d):
            break
        if ct == 0x0001:
            strings = _axml_strings(d, pos)
        elif ct == 0x0102 and csz >= 36:
            n_el += 1
            nm_i = struct.unpack_from("<I", d, pos + 20)[0]
            a_start, a_size, a_cnt = struct.unpack_from("<HHH", d, pos + 24)
            tag = strings[nm_i] if nm_i < len(strings) else "?"
            attrs = {}
            for k in range(min(a_cnt, 64)):
                ap = pos + 16 + a_start + k * (a_size or 20)
                if ap + 20 > len(d):
                    break
                _ans, an, raw, _sz, _r0, dtype, data = struct.unpack_from("<IIIHBBI", d, ap)
                key = strings[an] if an < len(strings) else "?"
                if raw != 0xFFFFFFFF and raw < len(strings):
                    val = strings[raw]
                elif dtype == 0x03 and data < len(strings):
                    val = strings[data]
                elif dtype == 0x12:
                    val = "true" if data else "false"
                elif dtype == 0x10:
                    val = str(data if data < 0x80000000 else data - (1 << 32))
                elif dtype == 0x11:
                    val = "0x%X" % data
                else:
                    val = "@0x%X" % data
                attrs[key] = val
            stack.append(tag)
            if tag == "manifest":
                info["package"] = attrs.get("package", "")
                info["version"] = "%s (%s)" % (attrs.get("versionName", "?"), attrs.get("versionCode", "?"))
            elif tag == "uses-sdk":
                info["min_sdk"], info["target_sdk"] = attrs.get("minSdkVersion", ""), attrs.get("targetSdkVersion", "")
            elif tag == "application":
                info["debuggable"] = attrs.get("debuggable")
                info["cleartext"] = attrs.get("usesCleartextTraffic")
                info["backup"] = attrs.get("allowBackup")
                info["app_class"] = attrs.get("name", "")
            elif tag in ("uses-permission", "uses-permission-sdk-23", "permission") and attrs.get("name"):
                info["perms"].append(attrs["name"])
            elif tag in _AXML_COMP:
                nm = attrs.get("name", "?")
                if len(info["components"][tag]) < 60:
                    info["components"][tag].append(nm)
                if attrs.get("exported") == "true" and len(info["exported"]) < 40:
                    info["exported"].append("%s %s" % (tag, nm))
            elif tag == "action" and attrs.get("name") and attrs["name"] not in info["actions"] and len(info["actions"]) < 60:
                info["actions"].append(attrs["name"])
        elif ct == 0x0103 and stack:
            stack.pop()
        pos += csz
    info["perms"] = sorted(set(info["perms"]))[:80]
    return info if (info["package"] or info["perms"] or any(info["components"].values())) else None


_DEX_API = {   # kelompok -> potongan "Lkelas;->metode" (cocok sebagian pada string metode)
    "kirim / baca SMS": ("Landroid/telephony/SmsManager;->sendTextMessage", "Landroid/telephony/SmsManager;->sendMultipartTextMessage", "Landroid/telephony/SmsMessage;->createFromPdu"),
    "identitas perangkat": ("TelephonyManager;->getDeviceId", "TelephonyManager;->getImei", "TelephonyManager;->getSubscriberId", "TelephonyManager;->getLine1Number", "Settings$Secure;->getString"),
    "muat kode dinamis": ("Ldalvik/system/DexClassLoader;-><init>", "Ldalvik/system/PathClassLoader;-><init>", "Ldalvik/system/InMemoryDexClassLoader;-><init>", "Ljava/lang/ClassLoader;->loadClass"),
    "eksekusi perintah": ("Ljava/lang/Runtime;->exec", "Ljava/lang/ProcessBuilder;->start"),
    "refleksi": ("Ljava/lang/reflect/Method;->invoke", "Ljava/lang/Class;->forName", "Ljava/lang/Class;->getDeclaredMethod"),
    "kripto": ("Ljavax/crypto/Cipher;->doFinal", "Ljavax/crypto/Cipher;->getInstance", "Ljavax/crypto/spec/SecretKeySpec;-><init>"),
    "aksesibilitas / overlay": ("AccessibilityService;->performGlobalAction", "AccessibilityNodeInfo;->performAction", "WindowManager;->addView"),
    "admin perangkat": ("DevicePolicyManager;->lockNow", "DevicePolicyManager;->resetPassword", "DevicePolicyManager;->wipeData"),
    "pasang paket": ("PackageInstaller;->createSession", "PackageManager;->installPackage", "Landroid/content/Intent;->setDataAndType"),
    "rekam audio / kamera": ("Landroid/media/MediaRecorder;->start", "Landroid/media/AudioRecord;->startRecording", "Landroid/hardware/Camera;->open"),
    "lokasi": ("LocationManager;->getLastKnownLocation", "LocationManager;->requestLocationUpdates"),
    "WebView + JS": ("WebView;->addJavascriptInterface", "WebSettings;->setJavaScriptEnabled"),
    "kontak / log panggilan": ("ContentResolver;->query",),
    "anti-analisis": ("Landroid/os/Debug;->isDebuggerConnected", "Landroid/os/Build;->FINGERPRINT", "Landroid/provider/Settings$Global;->getInt"),
}


def _uleb(d: bytes, o: int) -> tuple[int, int]:
    v, sh = 0, 0
    while o < len(d) and sh < 35:
        b = d[o]
        o += 1
        v |= (b & 0x7F) << sh
        if not b & 0x80:
            break
        sh += 7
    return v, o


def _dex_scan(d: bytes) -> dict | None:
    """Ringkasan DEX: jumlah string / tipe / metode / kelas, panggilan API Android sensitif dari tabel method_ids, dugaan obfuskasi."""
    if len(d) < 0x70 or d[:4] != b"dex\n":
        return None
    ss, so, ts, to, _ps, _po, _fs, _fo, ms, mo, cs, _co = struct.unpack_from("<12I", d, 0x38)
    ss, ts, ms = min(ss, 200000), min(ts, 200000), min(ms, 300000)

    cache: dict[int, str] = {}

    def sget(i: int) -> str:
        if i in cache:
            return cache[i]
        r = ""
        if 0 <= i < ss and so + 4 * i + 4 <= len(d):
            o = struct.unpack_from("<I", d, so + 4 * i)[0]
            if o < len(d):
                n, p = _uleb(d, o)
                r = d[p:p + min(n * 3, 400)].split(b"\0")[0].decode("utf-8", "replace")
        cache[i] = r
        return r

    types = []
    for i in range(ts):
        if to + 4 * i + 4 > len(d):
            break
        types.append(sget(struct.unpack_from("<I", d, to + 4 * i)[0]))
    meths = []
    for i in range(ms):
        p = mo + 8 * i
        if p + 8 > len(d):
            break
        ci, _pi, ni = struct.unpack_from("<HHI", d, p)
        meths.append("%s->%s" % (types[ci] if ci < len(types) else "?", sget(ni)))
    hits: dict[str, list[str]] = {}
    for m in meths:
        for grp, keys in _DEX_API.items():
            if any(k in m for k in keys):
                lst = hits.setdefault(grp, [])
                if len(lst) < 6 and m not in lst:
                    lst.append(m)
    app_types = [t for t in types if t.startswith("L") and not t.startswith(("Landroid", "Ljava", "Ljavax", "Lkotlin", "Landroidx", "Lcom/google", "Lorg/", "Ldalvik"))]
    short = sum(1 for t in app_types if len(t.rstrip(";").split("/")[-1]) <= 2)
    return {"strings": ss, "types": ts, "methods": ms, "classes": cs, "hits": hits,
            "obf": bool(len(app_types) >= 20 and short / len(app_types) > 0.5), "app_types": len(app_types)}


# ----------------------- v99.11 [S1]: analisis bytecode Dalvik (DEX) ---------------------------------------------
# Membaca INSTRUKSI di code_item setiap metode, bukan hanya tabel method_ids: argumen konstan yang sampai ke API sensitif
# (nomor SMS, perintah shell, nama transformasi Cipher, URL), string yang dirakit lewat StringBuilder, kunci / IV hard-coded
# (fill-array-data), Base64 konstan, dan rantai panggilan dari komponen manifest ke pemanggil API sensitif. Pelacakan nilai
# bersifat lurus per-blok (dibuang di target lompatan / handler), jadi hasilnya PETUNJUK, bukan bukti; pemanggilan virtual
# dan refleksi tidak diselesaikan. Statis murni: tidak ada kode yang dijalankan. Hanya pustaka standar.

DEX_CODE_TIME = 6.0              # detik untuk seluruh analisis bytecode satu berkas / APK; sisanya dilaporkan sebagai terpotong
DEX_CODE_MAX_INSNS = 8_000_000   # unit 16-bit yang diurai per DEX
DEX_CODE_MAX_UNITS = 200_000     # satu metode lebih panjang dari ini dilewati
DEX_CODE_MAX_EDGES = 400_000     # sisi graf panggilan yang disimpan
DEX_CODE_MAX_CALLS = 60          # pemanggilan berargumen konstan yang dilaporkan
DEX_CODE_MAX_FILES = 8           # classes*.dex yang dianalisis per APK

_DEX_EXTRA_API = {   # tambahan khusus analisis bytecode (tidak mengubah _DEX_API / dex_info["hits"] yang lama)
    "jaringan / URL": ("Ljava/net/URL;-><init>", "Ljava/net/URL;->openConnection", "Ljava/net/Socket;-><init>",
                       "Lorg/apache/http/client/methods/HttpGet;-><init>", "Lorg/apache/http/client/methods/HttpPost;-><init>"),
    "pustaka native": ("Ljava/lang/System;->loadLibrary", "Ljava/lang/System;->load"),
    "hash / IV / sandi": ("Ljava/security/MessageDigest;->getInstance", "Ljavax/crypto/spec/IvParameterSpec;-><init>", "Ljavax/crypto/spec/PBEKeySpec;-><init>"),
    "sembunyikan komponen": ("PackageManager;->setComponentEnabledSetting",),
}
_DEX_ALLAPI = dict(_DEX_API)
_DEX_ALLAPI.update(_DEX_EXTRA_API)
# paket pustaka populer: kelasnya dilewati (hemat waktu) dan tidak dianggap kode aplikasi di graf panggilan
_DEX_LIB_PREFIX = ("Landroidx/", "Landroid/support/", "Lkotlin/", "Lkotlinx/", "Lcom/google/android/gms/", "Lcom/google/firebase/",
                   "Lcom/google/android/material/", "Lcom/squareup/", "Lokhttp3/", "Lokio/", "Lcom/bumptech/", "Lcom/facebook/",
                   "Lio/reactivex/", "Lorg/jetbrains/")
_DEX_FW_PREFIX = _DEX_LIB_PREFIX + ("Landroid/", "Ljava/", "Ljavax/", "Ldalvik/", "Lorg/json/", "Lorg/apache/", "Lorg/w3c/", "Lorg/xml/")


def _dex_len_table() -> list:
    """Panjang instruksi Dalvik (unit 16-bit) per opcode; opcode tak terpakai dihitung 1 supaya penelusuran tidak macet."""
    t = [1] * 256
    for lo, hi in ((0x2D, 0x3D), (0x44, 0x6D), (0x90, 0xAF), (0xD0, 0xE2)):
        for i in range(lo, hi + 1):
            t[i] = 2
    for i in (0x02, 0x05, 0x08, 0x13, 0x15, 0x16, 0x19, 0x1A, 0x1C, 0x1F, 0x20, 0x22, 0x23, 0x29, 0xFE, 0xFF):
        t[i] = 2
    for i in (0x03, 0x06, 0x09, 0x14, 0x17, 0x1B, 0x24, 0x25, 0x26, 0x2A, 0x2B, 0x2C, 0xFC, 0xFD):
        t[i] = 3
    for i in list(range(0x6E, 0x73)) + list(range(0x74, 0x79)):
        t[i] = 3
    t[0x18] = 5
    t[0xFA] = t[0xFB] = 4
    return t


_DEX_LEN = _dex_len_table()
# opcode yang menulis register tujuan (selain yang ditangani khusus): 4 = nibble rendah byte tinggi, 8 = byte tinggi, 16 = unit berikutnya
_DEX_DEST: dict[int, int] = {}
for _r, _m in (((0x04, 0x04), 4), ((0x20, 0x21), 4), ((0x23, 0x23), 4), ((0x52, 0x58), 4), ((0x7B, 0x8F), 4), ((0xB0, 0xD7), 4),
               ((0x05, 0x05), 8), ((0x0A, 0x0B), 8), ((0x0D, 0x0D), 8), ((0x16, 0x19), 8), ((0x2D, 0x31), 8), ((0x44, 0x4A), 8),
               ((0x60, 0x66), 8), ((0x90, 0xAF), 8), ((0xD8, 0xE2), 8), ((0xFE, 0xFF), 8), ((0x06, 0x06), 16)):
    for _o in range(_r[0], _r[1] + 1):
        _DEX_DEST[_o] = _m
_DEX_ENDS = frozenset((0x0E, 0x0F, 0x10, 0x11, 0x27, 0x28, 0x29, 0x2A))   # return / throw / goto: setelahnya hanya terjangkau lewat lompatan


def _dex_payload_len(u, pc: int, n: int) -> int:
    """Panjang (unit) payload semu packed-switch / sparse-switch / fill-array-data di u[pc]."""
    try:
        ident = u[pc]
        if ident == 0x100:
            return u[pc + 1] * 2 + 4
        if ident == 0x200:
            return u[pc + 1] * 4 + 2
        if ident == 0x300:
            return ((u[pc + 2] | (u[pc + 3] << 16)) * u[pc + 1] + 1) // 2 + 4
    except IndexError:
        pass
    return 1


def _dex_s32(lo: int, hi: int) -> int:
    v = lo | (hi << 16)
    return v - (1 << 32) if v & 0x80000000 else v


def _dex_targets(u, n: int) -> set:
    """Alamat (unit) yang menjadi tujuan lompatan: di sana nilai register yang dilacak dibuang."""
    t: set = set()
    pc = 0
    while pc < n:
        w = u[pc]
        op = w & 0xFF
        if op == 0 and w in (0x100, 0x200, 0x300):
            pc += _dex_payload_len(u, pc, n)
            continue
        if 0x32 <= op <= 0x3D:
            if pc + 1 < n:
                o = u[pc + 1]
                t.add(pc + (o - 65536 if o & 0x8000 else o))
        elif op == 0x28:
            o = w >> 8
            t.add(pc + (o - 256 if o & 0x80 else o))
        elif op == 0x29:
            if pc + 1 < n:
                o = u[pc + 1]
                t.add(pc + (o - 65536 if o & 0x8000 else o))
        elif op == 0x2A:
            if pc + 2 < n:
                t.add(pc + _dex_s32(u[pc + 1], u[pc + 2]))
        elif op in (0x2B, 0x2C) and pc + 2 < n:
            pp = pc + _dex_s32(u[pc + 1], u[pc + 2])
            try:
                if 0 <= pp < n - 1:
                    sz = min(u[pp + 1], 4096)
                    if u[pp] == 0x100:
                        base = pp + 4
                    elif u[pp] == 0x200:
                        base = pp + 2 + 2 * sz
                    else:
                        base = -1
                    if base > 0:
                        for i in range(sz):
                            t.add(pc + _dex_s32(u[base + 2 * i], u[base + 2 * i + 1]))
            except IndexError:
                pass
        pc += _DEX_LEN[op]
    return t


def _dex_pretty(cls: str, name: str = "") -> str:
    """'Lcom/x/Y;' + 'm' -> 'com.x.Y.m'."""
    c = cls[1:-1].replace("/", ".") if cls.startswith("L") and cls.endswith(";") else cls
    return "%s.%s" % (c, name) if name else c


def _dex_valtext(v) -> str:
    """Teks nilai untuk perakitan StringBuilder; yang tak diketahui jadi {?}."""
    if v is None:
        return "{?}"
    k = v[0]
    if k == "s":
        return v[1]
    if k == "i":
        return str(v[1])
    if k == "sb":
        return "".join(v[1])
    return "{?}"


def _dex_valrepr(v) -> str:
    if v is None:
        return "?"
    k = v[0]
    if k in ("s", "sb"):
        return "\"%s\"" % (v[1] if k == "s" else "".join(v[1]))[:120]
    if k == "i":
        return str(v[1]) if -256 < v[1] < 256 else "0x%X" % (v[1] & 0xFFFFFFFF)
    if k == "b":
        b = v[1]
        txt = b.decode("latin-1")
        return "byte[%d] %s%s" % (len(b), b[:24].hex(), (" \"%s\"" % txt[:40]) if txt.isprintable() and len(b) >= 4 else "")
    if k == "c":
        return "class " + _dex_pretty(v[1])
    if k == "n":
        return "new " + _dex_pretty(v[1])
    return "?"


def _dex_code(d: bytes, entries=None, deadline: float | None = None) -> dict | None:
    """Analisis bytecode satu DEX. entries: himpunan deskriptor kelas komponen manifest ('Lcom/x/Y;') untuk rantai panggilan.
    Berhenti sebagian (partial=True) bila waktu / batas instruksi habis. Tidak pernah membaca di luar `d`."""
    if len(d) < 0x70 or d[:4] != b"dex\n":
        return None
    n = len(d)
    ss, so, ts, to, _ps, _po, _fs, _fo, ms, mo, cs, co = struct.unpack_from("<12I", d, 0x38)
    ss, ts, ms, cs = min(ss, 400000), min(ts, 200000), min(ms, 400000), min(cs, 100000)
    deadline = deadline or (time.monotonic() + DEX_CODE_TIME)
    LEN = _DEX_LEN
    scache: dict[int, str] = {}
    tcache: dict[int, str] = {}
    mcache: dict[int, tuple] = {}
    gcache: dict[int, tuple] = {}
    acache: dict[int, bool] = {}

    def sget(i: int, lim: int = 600) -> str:
        r = scache.get(i)
        if r is not None:
            return r
        r = ""
        if 0 <= i < ss and so + 4 * i + 4 <= n:
            o = struct.unpack_from("<I", d, so + 4 * i)[0]
            if o < n:
                _l, p = _uleb(d, o)
                e = d.find(b"\0", p, min(n, p + lim * 3))
                r = d[p:(e if e >= 0 else min(n, p + lim * 3))].decode("utf-8", "replace")[:lim]
        scache[i] = r
        return r

    def tname(i: int) -> str:
        r = tcache.get(i)
        if r is None:
            r = ""
            if 0 <= i < ts and to + 4 * i + 4 <= n:
                r = sget(struct.unpack_from("<I", d, to + 4 * i)[0])
            tcache[i] = r
        return r

    def mparts(mi: int) -> tuple:
        r = mcache.get(mi)
        if r is None:
            r = ("?", "?")
            if 0 <= mi < ms and mo + 8 * mi + 8 <= n:
                ci, _pi, ni = struct.unpack_from("<HHI", d, mo + 8 * mi)
                r = (tname(ci), sget(ni))
            mcache[mi] = r
        return r

    def groups_of(mi: int) -> tuple:
        r = gcache.get(mi)
        if r is None:
            c, nm = mparts(mi)
            full = "%s->%s" % (c, nm)
            r = tuple(g for g, keys in _DEX_ALLAPI.items() if any(k in full for k in keys))
            gcache[mi] = r
        return r

    def is_app(mi: int) -> bool:
        r = acache.get(mi)
        if r is None:
            r = not mparts(mi)[0].startswith(_DEX_FW_PREFIX)
            acache[mi] = r
        return r

    st = {"methods": 0, "insns": 0, "sites": 0, "classes": 0, "lib": 0, "partial": False}
    groups: dict[str, dict] = {}
    calls: list[dict] = []
    percall: dict[str, int] = {}
    keys: list[dict] = []
    notes: list[str] = []
    edges: dict[int, list] = {}
    nedges = 0
    sites: list[tuple] = []      # (indeks metode pemanggil, kelompok, nama callee) untuk rantai panggilan

    def note(x: str) -> None:
        if x not in notes and len(notes) < 14:
            notes.append(x)

    def walk(mi: int, code: int, cname: str, mname: str) -> None:
        nonlocal nedges
        if code + 16 > n:
            return
        nu = struct.unpack_from("<I", d, code + 12)[0]
        if nu == 0 or nu > DEX_CODE_MAX_UNITS or code + 16 + 2 * nu > n:
            return
        u = struct.unpack_from("<%dH" % nu, d, code + 16)
        st["methods"] += 1
        st["insns"] += nu
        tg = _dex_targets(u, nu)
        regs: dict[int, tuple] = {}
        last = None
        me = None            # nama pemanggil (dibuat sekali bila dibutuhkan)
        pc = 0
        while pc < nu:
            w = u[pc]
            op = w & 0xFF
            if op == 0:
                pc += _dex_payload_len(u, pc, nu) if w in (0x100, 0x200, 0x300) else 1
                continue
            ln = LEN[op]
            if pc + ln > nu:
                break
            if pc in tg:
                regs.clear()
                last = None
            if op == 0x1A or op == 0x1B:
                a = w >> 8
                idx = u[pc + 1] if op == 0x1A else (u[pc + 1] | (u[pc + 2] << 16))
                regs[a] = ("s", sget(idx))
                regs.pop(a + 1, None)
            elif op == 0x12:
                a = (w >> 8) & 0xF
                v = (w >> 12) & 0xF
                regs[a] = ("i", v - 16 if v > 7 else v)
            elif op == 0x13 or op == 0x14 or op == 0x15:
                a = w >> 8
                if op == 0x13:
                    v = u[pc + 1] - 65536 if u[pc + 1] & 0x8000 else u[pc + 1]
                elif op == 0x14:
                    v = _dex_s32(u[pc + 1], u[pc + 2])
                else:
                    v = (u[pc + 1] - 65536 if u[pc + 1] & 0x8000 else u[pc + 1]) << 16
                regs[a] = ("i", v)
            elif op in (0x01, 0x07):
                a, b = (w >> 8) & 0xF, (w >> 12) & 0xF
                if b in regs:
                    regs[a] = regs[b]
                else:
                    regs.pop(a, None)
            elif op in (0x02, 0x08) or op in (0x03, 0x09):
                a, b = (w >> 8, u[pc + 1]) if op in (0x02, 0x08) else (u[pc + 1], u[pc + 2])
                if b in regs:
                    regs[a] = regs[b]
                else:
                    regs.pop(a, None)
            elif op == 0x0C:
                a = w >> 8
                if last is not None:
                    regs[a] = last
                else:
                    regs.pop(a, None)
                last = None
            elif op == 0x1C:
                regs[w >> 8] = ("c", tname(u[pc + 1]))
            elif op == 0x22:
                t = tname(u[pc + 1])
                regs[w >> 8] = ("sb", []) if t == "Ljava/lang/StringBuilder;" else ("n", t)
            elif op == 0x26:     # fill-array-data: isi larik byte konstan (kandidat kunci / IV / blob)
                a = w >> 8
                pp = pc + _dex_s32(u[pc + 1], u[pc + 2])
                regs.pop(a, None)
                if 0 <= pp and pp + 4 <= nu and u[pp] == 0x300 and u[pp + 1] == 1:
                    cnt = min(u[pp + 2] | (u[pp + 3] << 16), 4096)
                    raw = b"".join(struct.pack("<H", x) for x in u[pp + 4:pp + 4 + (cnt + 1) // 2])[:cnt]
                    if raw:
                        regs[a] = ("b", raw)
            elif (0x6E <= op <= 0x72) or (0x74 <= op <= 0x78) or op in (0xFA, 0xFB):
                mi2 = u[pc + 1]
                if op in (0x74, 0x75, 0x76, 0x77, 0x78, 0xFB):
                    args = [u[pc + 2] + i for i in range(w >> 8)]
                else:
                    x = u[pc + 2]
                    args = [x & 0xF, (x >> 4) & 0xF, (x >> 8) & 0xF, (x >> 12) & 0xF, (w >> 8) & 0xF][:(w >> 12) & 0xF]
                cls, nm = mparts(mi2)
                static = op in (0x71, 0x77)
                vals = [regs.get(r) for r in args]
                recv = None if static or not vals else vals[0]
                argv = vals if static else vals[1:]
                res = None
                if cls == "Ljava/lang/StringBuilder;":
                    if nm == "<init>" and args and not static:
                        regs[args[0]] = ("sb", [argv[0][1]] if argv and argv[0] and argv[0][0] == "s" else [])
                    elif nm == "append" and recv and recv[0] == "sb":
                        recv[1].append(_dex_valtext(argv[0] if argv else None))
                        res = recv
                    elif nm == "toString" and recv and recv[0] == "sb":
                        res = ("s", "".join(recv[1])[:2000])
                elif cls == "Ljava/lang/String;" and nm == "getBytes" and recv and recv[0] == "s":
                    res = ("b", recv[1].encode("utf-8", "replace")[:4096])
                elif cls == "Landroid/util/Base64;" and nm == "decode" and argv and argv[0] and argv[0][0] in ("s", "b"):
                    raw = argv[0][1].encode("latin-1", "replace") if argv[0][0] == "s" else argv[0][1]
                    try:
                        res = ("b", base64.b64decode(raw + b"=" * (-len(raw) % 4), altchars=b"-_" if (b"-" in raw or b"_" in raw) else None)[:4096])
                    except Exception:
                        res = None
                gl = groups_of(mi2)
                if gl:
                    st["sites"] += 1
                    if me is None:
                        me = _dex_pretty(cname, mname)
                    callee = _dex_pretty(cls, nm)
                    known = any(v is not None for v in argv)
                    for g in gl:
                        e = groups.setdefault(g, {"n": 0, "callers": []})
                        e["n"] += 1
                        if me not in e["callers"] and len(e["callers"]) < 4:
                            e["callers"].append(me)
                    if known and len(calls) < DEX_CODE_MAX_CALLS and percall.get(gl[0], 0) < 8:
                        percall[gl[0]] = percall.get(gl[0], 0) + 1
                        calls.append({"group": gl[0], "caller": me, "callee": callee, "args": [_dex_valrepr(v) for v in argv][:6]})
                    if len(sites) < 400:
                        sites.append((mi, gl[0], callee))
                    # temuan bernilai tinggi dari argumen konstan
                    if cls == "Ljavax/crypto/spec/SecretKeySpec;" and nm == "<init>":
                        kb = next((v[1] for v in argv if v and v[0] == "b"), None)
                        al = next((v[1] for v in reversed(argv) if v and v[0] == "s"), "?")
                        if kb:
                            if len(keys) < 12:
                                keys.append({"kind": "kunci", "algo": al[:20], "len": len(kb), "hex": kb[:32].hex(), "caller": me})
                            note("kunci kripto hard-coded (%s, %d byte) di %s" % (al[:20], len(kb), me))
                    elif cls == "Ljavax/crypto/spec/IvParameterSpec;" and nm == "<init>":
                        kb = next((v[1] for v in argv if v and v[0] == "b"), None)
                        if kb and len(keys) < 12:
                            keys.append({"kind": "IV", "algo": "", "len": len(kb), "hex": kb[:32].hex(), "caller": me})
                    elif cls == "Ljavax/crypto/Cipher;" and nm == "getInstance" and argv and argv[0] and argv[0][0] == "s":
                        tr = argv[0][1].upper()
                        if "ECB" in tr or tr in ("AES", "DES", "DESEDE", "3DES") or tr.startswith("DES/"):
                            note("Cipher %s (mode ECB / bawaan = ECB atau DES lemah) di %s" % (argv[0][1][:40], me))
                    elif cls == "Ljava/lang/Runtime;" and nm == "exec" and argv and argv[0] and argv[0][0] in ("s", "sb"):
                        cmd = _dex_valtext(argv[0]).strip()
                        if re.match(r"(su|sh|/system/(?:x?bin)/su|busybox|chmod|pm install|am start|su -c)\b", cmd):
                            note("exec perintah shell \"%s\" di %s" % (cmd[:60], me))
                    elif nm == "<init>" and cls.endswith("ClassLoader;") and "dalvik" in cls:
                        pth = next((v for v in argv if v and v[0] in ("s", "sb")), None)
                        note("pemuatan kode dinamis%s di %s" % ((" dari \"%s\"" % _dex_valtext(pth)[:70]) if pth else "", me))
                if is_app(mi2) and nedges < DEX_CODE_MAX_EDGES:
                    lst = edges.setdefault(mi2, [])
                    if len(lst) < 16 and mi not in lst:
                        lst.append(mi)
                        nedges += 1
                last = res
            elif op in (0xFC, 0xFD):
                last = None
            else:
                m = _DEX_DEST.get(op)
                if m:
                    a = (w >> 8) & 0xF if m == 4 else (w >> 8 if m == 8 else u[pc + 1])
                    regs.pop(a, None)
                    regs.pop(a + 1, None)
                if op in _DEX_ENDS:
                    regs.clear()
                    last = None
            if op == 0x0D:
                regs.clear()      # awal handler pengecualian: keadaan masuk tidak diketahui
            pc += ln

    stop = False
    for ci in range(cs):
        if (ci & 15) == 0 and time.monotonic() > deadline:
            st["partial"] = True
            break
        if stop:
            break
        p = co + 32 * ci
        if p + 32 > n:
            break
        cidx, _acc, _sup, _itf, _src, _ann, cdo, _sv = struct.unpack_from("<8I", d, p)
        if not cdo or cdo >= n:
            continue
        cname = tname(cidx)
        if cname.startswith(_DEX_LIB_PREFIX):
            st["lib"] += 1
            continue
        st["classes"] += 1
        o = cdo
        sf, o = _uleb(d, o)
        inf, o = _uleb(d, o)
        dm, o = _uleb(d, o)
        vm, o = _uleb(d, o)
        if max(sf, inf, dm, vm) > 50000:
            continue
        for _ in range(sf + inf):
            _v, o = _uleb(d, o)
            _v, o = _uleb(d, o)
        for cnt in (dm, vm):
            mi = 0
            for _ in range(cnt):
                diff, o = _uleb(d, o)
                _fl, o = _uleb(d, o)
                code, o = _uleb(d, o)
                mi += diff
                if o > n:
                    break
                if code:
                    if st["insns"] > DEX_CODE_MAX_INSNS or ((st["methods"] & 63) == 0 and time.monotonic() > deadline):
                        st["partial"] = True
                        stop = True
                        break
                    walk(mi, code, cname, mparts(mi)[1])
            if stop:
                break

    # rantai panggilan: dari metode di kelas komponen manifest ke pemanggil API sensitif (maks. kedalaman 5, menurut sisi invoke statis)
    chains: list[str] = []
    if entries and sites:
        seen_chain: set = set()
        for mi, g, callee in sites:
            if len(chains) >= 12:
                break
            frontier = [(mi, (mi,))]
            visited = {mi}
            found = None
            for _depth in range(6):
                nxt = []
                for node, path in frontier:
                    if mparts(node)[0] in entries:
                        found = path
                        break
                    for c in edges.get(node, ()):
                        if c not in visited:
                            visited.add(c)
                            nxt.append((c, path + (c,)))
                if found or not nxt or len(visited) > 4000:
                    break
                frontier = nxt
            if found:
                txt = " -> ".join([_dex_pretty(*mparts(x)) for x in reversed(found)] + [callee])
                if txt not in seen_chain:
                    seen_chain.add(txt)
                    chains.append("[%s] %s" % (g, txt))
    return {"methods": st["methods"], "insns": st["insns"], "classes": st["classes"], "lib_skipped": st["lib"], "sites": st["sites"],
            "partial": st["partial"], "groups": groups, "calls": calls, "keys": keys, "notes": notes, "chains": chains}


def _dex_entry_classes(man) -> set:
    """Deskriptor kelas komponen manifest (activity / service / receiver / provider + kelas Application)."""
    out: set = set()
    if not man:
        return out
    pkg = man.get("package") or ""
    names: list = []
    for lst in (man.get("components") or {}).values():
        names.extend(lst)
    if man.get("app_class"):
        names.append(man["app_class"])
    for nm in names:
        if not nm or not isinstance(nm, str):
            continue
        if nm.startswith("."):
            nm = pkg + nm
        elif "." not in nm and pkg:
            nm = pkg + "." + nm
        out.add("L" + nm.replace(".", "/") + ";")
    return out


def _dex_code_merge(acc: dict, r: dict) -> None:
    for k in ("methods", "insns", "classes", "lib_skipped", "sites"):
        acc[k] = acc.get(k, 0) + r.get(k, 0)
    acc["partial"] = acc.get("partial", False) or r.get("partial", False)
    for g, e in r["groups"].items():
        cur = acc.setdefault("groups", {}).setdefault(g, {"n": 0, "callers": []})
        cur["n"] += e["n"]
        cur["callers"].extend(x for x in e["callers"] if x not in cur["callers"] and len(cur["callers"]) < 4)
    for k, lim in (("calls", DEX_CODE_MAX_CALLS), ("keys", 12), ("notes", 14), ("chains", 12)):
        cur = acc.setdefault(k, [])
        cur.extend(x for x in r[k] if x not in cur and len(cur) < lim)


def _render_dexcode(code, a, compact: bool, defang: bool = True) -> None:
    if not code or not code.get("methods"):
        return
    a("Bytecode DEX: %d metode / %d instruksi diurai (%d kelas aplikasi%s), %d pemanggilan API sensitif%s" % (
        code["methods"], code["insns"], code["classes"], ", %d kelas pustaka dilewati" % code["lib_skipped"] if code.get("lib_skipped") else "",
        code["sites"], " | TERPOTONG (batas waktu / ukuran)" if code.get("partial") else ""))
    for x in (code.get("notes") or [])[: (3 if compact else 14)]:
        a("   ! " + _clean(x))
    for g, e in list((code.get("groups") or {}).items())[: (4 if compact else 16)]:
        a("   - %s x%d dari %s" % (g, e["n"], ", ".join(_clean(c) for c in e["callers"][:2])))
    if compact:
        return
    for c in (code.get("calls") or [])[:14]:
        a("   > %s: %s(%s)" % (_clean(c["group"]), _clean(c["callee"]), _df(_clean(", ".join(c["args"])[:200]), defang)))
    for x in (code.get("chains") or [])[:8]:
        a("   rantai: " + _clean(x))
    for k in (code.get("keys") or [])[:6]:
        a("   %s hard-coded: %d byte %s%s | di %s" % (k["kind"], k["len"], k["hex"], (" (%s)" % _clean(k["algo"])) if k.get("algo") else "", _clean(k["caller"])))


def _dex_code_path(path) -> tuple[dict, list]:
    """Analisis bytecode untuk .dex mentah atau APK / ZIP berisi classes*.dex. Mengembalikan (agregat, catatan)."""
    f_, size = _open_regular(path)
    notes: list = []
    acc: dict = {}
    deadline = time.monotonic() + DEX_CODE_TIME
    with f_:
        head = f_.read(4)
        f_.seek(0)
        if head == b"dex\n":
            r = _dex_code(f_.read(min(size, 128 * 1024 * 1024)), None, deadline)
            if r:
                _dex_code_merge(acc, r)
            return acc, notes
        if not zipfile.is_zipfile(f_):
            return acc, ["bukan DEX / APK"]
        with zipfile.ZipFile(f_) as z:
            infos = {i.filename.lower(): i for i in z.infolist()}
            entries: set = set()
            if "androidmanifest.xml" in infos:
                try:
                    entries = _dex_entry_classes(_axml_summary(_zread(z, infos["androidmanifest.xml"], 2 * 1024 * 1024)))
                except Exception:
                    pass
            nfile = 0
            for nm in sorted(infos, key=lambda s: (len(s), s)):
                if not re.fullmatch(r"classes\d*\.dex", nm):
                    continue
                if nfile >= DEX_CODE_MAX_FILES:
                    notes.append("hanya %d classes*.dex pertama dianalisis" % DEX_CODE_MAX_FILES)
                    break
                nfile += 1
                r = _dex_code(_zread(z, infos[nm], 64 * 1024 * 1024), entries, deadline)
                if r:
                    _dex_code_merge(acc, r)
            if not nfile:
                notes.append("tidak ada classes*.dex")
    return acc, notes


def dex_text(path, defang: bool = True, compact: bool = False) -> str:
    """Laporan bytecode Dalvik untuk .dex / APK (CLI --dex, API action 'dex')."""
    try:
        acc, notes = _dex_code_path(path)
    except Exception as e:
        return "DEX gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L: list = []
    _render_dexcode(acc, L.append, compact, defang)
    if not L:
        return "DEX: tidak ada metode berkode yang bisa dianalisis%s." % ((" (" + "; ".join(notes) + ")") if notes else "")
    return "\n".join(L + ["   (%s)" % x for x in notes])


def _dexraw_enrich(rep: dict, d) -> None:
    """DEX mandiri (bukan di dalam APK): hasil di rep["dex_code"]; kunci baru, aditif."""
    if d[:4] != b"dex\n":
        return
    try:
        r = _dex_code(d)
    except Exception as e:
        rep["warn"].append("analisis bytecode DEX gagal: %s" % type(e).__name__)
        return
    if r and r["methods"]:
        rep["dex_code"] = r
        for x in r["notes"][:6]:
            rep["warn"].append("DEX bytecode: " + x)


# ----------------------- v99.12 [S1b]: tabel metadata .NET (#~) + pemindaian IL ----------------------------------
# Mengurai stream `#~` (ECMA-335): TypeDef / MethodDef / MemberRef / TypeRef / ImplMap (P/Invoke) / ModuleRef / AssemblyRef /
# ManifestResource, lalu memindai badan IL tiap metode (opcode call / callvirt / newobj / ldftn) untuk memetakan siapa memanggil
# siapa: metode internal, API .NET sensitif (Process.Start, Assembly.Load, WebClient, Convert.FromBase64String ...), dan P/Invoke
# (dll!fungsi). Statis murni: tidak ada kode yang dijalankan; hanya pustaka standar. Hasil adalah PETUNJUK: pemanggilan lewat
# refleksi / delegate dinamis / IL terenkripsi (obfuskator) tidak terlihat, dan IL yang tidak valid menghentikan pemindaian
# metode itu saja. Kunci baru rep["dotnet_il"]; triase lama tidak berubah.

NETIL_TIME = 4.0                 # detik untuk seluruh analisis IL satu berkas; sisanya dilaporkan sebagai terpotong
NETIL_MAX_METHODS = 80_000       # metode berbadan yang dipindai
NETIL_MAX_BODY = 1 << 20         # satu badan IL lebih panjang dari ini dilewati
NETIL_MAX_BYTES = 64 << 20       # total byte IL yang dipindai
NETIL_MAX_ROWS = 1_000_000       # baris per tabel; lebih dari ini dianggap metadata rusak / dibuat-buat
NETIL_MAX_CALLS = 60             # pemanggilan sensitif yang dilaporkan

_NT_CODED = {   # nama: (jumlah bit tag, tabel per tag); -1 = tag tidak dipakai
    "ResolutionScope": (2, (0, 26, 35, 1)),
    "TypeDefOrRef": (2, (2, 1, 27)),
    "MemberRefParent": (3, (2, 1, 26, 6, 27)),
    "HasConstant": (2, (4, 8, 23)),
    "HasCustomAttribute": (5, (6, 4, 1, 2, 8, 9, 10, 0, 14, 23, 20, 17, 26, 27, 32, 35, 38, 39, 40, 42, 44, 43)),
    "CustomAttributeType": (3, (-1, -1, 6, 10, -1)),
    "HasFieldMarshal": (1, (4, 8)),
    "HasDeclSecurity": (2, (2, 6, 32)),
    "HasSemantics": (1, (20, 23)),
    "MethodDefOrRef": (1, (6, 10)),
    "MemberForwarded": (1, (4, 6)),
    "Implementation": (2, (38, 35, 39)),
    "TypeOrMethodDef": (1, (2, 6)),
}
# skema kolom per tabel: int = byte tetap; "S" / "G" / "B" = indeks heap #Strings / #GUID / #Blob; ("T", n) = indeks ke tabel n;
# ("C", nama) = indeks berkode
_NT_SCHEMA = {
    0: (2, "S", "G", "G", "G"), 1: (("C", "ResolutionScope"), "S", "S"), 2: (4, "S", "S", ("C", "TypeDefOrRef"), ("T", 4), ("T", 6)),
    3: (("T", 4),), 4: (2, "S", "B"), 5: (("T", 6),), 6: (4, 2, 2, "S", "B", ("T", 8)), 7: (("T", 8),), 8: (2, 2, "S"),
    9: (("T", 2), ("C", "TypeDefOrRef")), 10: (("C", "MemberRefParent"), "S", "B"), 11: (2, ("C", "HasConstant"), "B"),
    12: (("C", "HasCustomAttribute"), ("C", "CustomAttributeType"), "B"), 13: (("C", "HasFieldMarshal"), "B"),
    14: (2, ("C", "HasDeclSecurity"), "B"), 15: (2, 4, ("T", 2)), 16: (4, ("T", 4)), 17: ("B",), 18: (("T", 2), ("T", 20)),
    19: (("T", 20),), 20: (2, "S", ("C", "TypeDefOrRef")), 21: (("T", 2), ("T", 23)), 22: (("T", 23),), 23: (2, "S", "B"),
    24: (2, ("T", 6), ("C", "HasSemantics")), 25: (("T", 2), ("C", "MethodDefOrRef"), ("C", "MethodDefOrRef")), 26: ("S",),
    27: ("B",), 28: (2, ("C", "MemberForwarded"), "S", ("T", 26)), 29: (4, ("T", 4)), 30: (4, 4), 31: (4,),
    32: (4, 2, 2, 2, 2, 4, "B", "S", "S"), 33: (4,), 34: (4, 4, 4), 35: (2, 2, 2, 2, 4, "B", "S", "S", "B"), 36: (4, ("T", 35)),
    37: (4, 4, 4, ("T", 35)), 38: (4, "S", "B"), 39: (4, 4, "S", "S", ("C", "Implementation")),
    40: (4, 4, "S", ("C", "Implementation")), 41: (("T", 2), ("T", 2)), 42: (2, 2, ("C", "TypeOrMethodDef"), "S"),
    43: (("C", "MethodDefOrRef"), "B"), 44: (("T", 42), ("C", "TypeDefOrRef")),
}

# ukuran operand opcode CIL: -1 = opcode tidak valid; -2 = switch
_IL1 = [-1] * 256
_IL2: dict = {}
for _o in range(0x00, 0x0E):
    _IL1[_o] = 0
for _o in (0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x1F):
    _IL1[_o] = 1
for _o in (0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x25, 0x26, 0x2A):
    _IL1[_o] = 0
for _o in (0x20, 0x22, 0x27, 0x28, 0x29):
    _IL1[_o] = 4
_IL1[0x21] = _IL1[0x23] = 8
for _o in range(0x2B, 0x38):
    _IL1[_o] = 1
for _o in range(0x38, 0x45):
    _IL1[_o] = 4
_IL1[0x45] = -2
for _o in range(0x46, 0x6F):
    _IL1[_o] = 0
for _o in (0x6F, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x79, 0x7B, 0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x8C, 0x8D, 0x8F, 0xA3, 0xA4, 0xA5,
           0xC2, 0xC6, 0xD0, 0xDD):
    _IL1[_o] = 4
for _o in (0x76, 0x7A, 0x8E, 0xC3, 0xDC, 0xDF, 0xE0):
    _IL1[_o] = 0
for _o in range(0x82, 0x8C):
    _IL1[_o] = 0
for _o in range(0x90, 0xA3):
    _IL1[_o] = 0
for _o in range(0xB3, 0xBB):
    _IL1[_o] = 0
for _o in range(0xD1, 0xDC):
    _IL1[_o] = 0
_IL1[0xDE] = 1
for _o, _s in ((0x00, 0), (0x01, 0), (0x02, 0), (0x03, 0), (0x04, 0), (0x05, 0), (0x06, 4), (0x07, 4), (0x09, 2), (0x0A, 2), (0x0B, 2),
               (0x0C, 2), (0x0D, 2), (0x0E, 2), (0x0F, 0), (0x11, 0), (0x12, 1), (0x13, 0), (0x14, 0), (0x15, 4), (0x16, 4), (0x17, 0),
               (0x18, 0), (0x19, 1), (0x1A, 0), (0x1C, 4), (0x1D, 0), (0x1E, 0)):
    _IL2[_o] = _s

# (grup, tipe lengkap, metode | None = semua metode tipe itu); nama grup sejalan dengan _NET_CAPS
_NETIL_API = (
    ("eksekusi proses / shell", "System.Diagnostics.Process", ("Start",)),
    ("muat kode dinamis", "System.Reflection.Assembly", ("Load", "LoadFrom", "LoadFile", "UnsafeLoadFrom", "ReflectionOnlyLoad")),
    ("muat kode dinamis", "System.AppDomain", ("Load",)),
    ("muat kode dinamis", "System.Reflection.MethodBase", ("Invoke",)),
    ("muat kode dinamis", "System.Reflection.MethodInfo", ("Invoke",)),
    ("muat kode dinamis", "System.Activator", ("CreateInstance",)),
    ("muat kode dinamis", "System.Runtime.InteropServices.Marshal", ("GetDelegateForFunctionPointer", "GetFunctionPointerForDelegate")),
    ("muat kode dinamis", "System.Reflection.Emit.AssemblyBuilder", None),
    ("muat kode dinamis", "System.Reflection.Emit.ILGenerator", None),
    ("jaringan", "System.Net.WebClient", ("DownloadString", "DownloadData", "DownloadFile", "UploadData", "UploadString", "UploadFile", "OpenRead")),
    ("jaringan", "System.Net.Http.HttpClient", ("GetAsync", "PostAsync", "GetStringAsync", "GetByteArrayAsync", "GetStreamAsync", "SendAsync")),
    ("jaringan", "System.Net.WebRequest", ("Create", "GetResponse")),
    ("jaringan", "System.Net.HttpWebRequest", ("GetResponse", "GetRequestStream")),
    ("jaringan", "System.Net.Sockets.TcpClient", (".ctor", "Connect", "ConnectAsync")),
    ("jaringan", "System.Net.Sockets.Socket", ("Connect", "ConnectAsync")),
    ("dekode / kripto", "System.Convert", ("FromBase64String",)),
    ("dekode / kripto", "System.IO.Compression.GZipStream", (".ctor",)),
    ("dekode / kripto", "System.IO.Compression.DeflateStream", (".ctor",)),
    ("dekode / kripto", "System.Security.Cryptography.ICryptoTransform", ("TransformFinalBlock",)),
    ("dekode / kripto", "System.Security.Cryptography.SymmetricAlgorithm", ("CreateDecryptor", "CreateEncryptor")),
    ("persistensi / registri", "Microsoft.Win32.RegistryKey", ("SetValue", "CreateSubKey")),
    ("persistensi / registri", "Microsoft.Win32.Registry", ("SetValue",)),
    ("berkas", "System.IO.File", ("WriteAllBytes", "Delete")),
    ("penyadap input / layar", "System.Drawing.Graphics", ("CopyFromScreen",)),
    ("penyadap input / layar", "System.Windows.Forms.Clipboard", ("GetText", "GetDataObject")),
    ("anti-debug / anti-analisis", "System.Diagnostics.Debugger", ("get_IsAttached", "IsLogging")),
    ("anti-debug / anti-analisis", "System.Management.ManagementObjectSearcher", (".ctor",)),
)
_NETIL_API_IDX: dict = {}
for _g, _t, _ms in _NETIL_API:
    _NETIL_API_IDX.setdefault(_t, []).append((_g, _ms))
# grup yang menghasilkan peringatan (bukan sekadar daftar)
_NETIL_WARN_GROUPS = {"muat kode dinamis", "eksekusi proses / shell"}


def _net_clr(d: bytes, pe: dict):
    """Cari stream metadata CLR. -> (streams {nama: (offset berkas, ukuran)}, r2o, entry_token) atau None."""
    pe_off = struct.unpack_from("<I", d, 0x3C)[0]
    o = pe_off + 24
    is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
    nrva = struct.unpack_from("<I", d, o + (108 if is64 else 92))[0]
    if nrva <= 14:
        return None
    rva, _sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 8 * 14)

    def r2o(x: int):
        for s in pe["sections"]:
            if s["va"] <= x < s["va"] + max(s["vsize"], s["rsize"]):
                return s["rptr"] + x - s["va"]
        return None

    co = r2o(rva)
    if co is None or co + 24 > len(d):
        return None
    _cb, _ma, _mi, mrva, _msz, _cf, etok = struct.unpack_from("<IHHIIII", d, co)
    mo = r2o(mrva)
    if mo is None or mo + 20 > len(d) or d[mo:mo + 4] != b"BSJB":
        return None
    vlen = struct.unpack_from("<I", d, mo + 12)[0]
    if vlen > 255 or mo + 16 + vlen + 4 > len(d):
        return None
    p = mo + 16 + vlen
    nstreams = struct.unpack_from("<H", d, p + 2)[0]
    p += 4
    streams: dict = {}
    for _ in range(min(nstreams, 16)):
        if p + 9 > len(d):
            break
        so, ssz = struct.unpack_from("<II", d, p)
        e = d.find(b"\0", p + 8, p + 40)
        if e < 0:
            break
        nm = d[p + 8:e].decode("ascii", "replace")
        streams[nm] = (mo + so, ssz)
        p += 8 + ((len(nm) + 1 + 3) & ~3)
    return streams, r2o, etok


def _net_tables(d: bytes, base: int, size: int):
    """Urai header #~ dan tata letak tabel. -> {"rows", "lay", "sizes"} atau None (metadata rusak / tak didukung)."""
    end = min(base + size, len(d))
    if size < 24 or base + 24 > len(d):
        return None
    hs = d[base + 6]
    valid = struct.unpack_from("<Q", d, base + 8)[0]
    p = base + 24
    rows: dict = {}
    for t in range(64):
        if valid >> t & 1:
            if p + 4 > end:
                return None
            n = struct.unpack_from("<I", d, p)[0]
            p += 4
            if t > 44 or n > NETIL_MAX_ROWS:
                return None
            rows[t] = n
    if hs & 0x40:
        p += 4
    ssz, gsz, bsz = (4 if hs & 1 else 2), (4 if hs & 2 else 2), (4 if hs & 4 else 2)
    lay: dict = {}
    for t in sorted(rows):
        cols = []
        for c in _NT_SCHEMA[t]:
            if isinstance(c, int):
                cols.append(c)
            elif c == "S":
                cols.append(ssz)
            elif c == "G":
                cols.append(gsz)
            elif c == "B":
                cols.append(bsz)
            elif c[0] == "T":
                cols.append(4 if rows.get(c[1], 0) > 0xFFFF else 2)
            else:
                bits, tabs = _NT_CODED[c[1]]
                cols.append(4 if max(rows.get(x, 0) for x in tabs) >= (1 << (16 - bits)) else 2)
        rs = sum(cols)
        if p + rs * rows[t] > end:
            return None
        lay[t] = (p, rs, cols)
        p += rs * rows[t]
    return {"rows": rows, "lay": lay}


def _nt_rows(d: bytes, tb: dict, t: int) -> list:
    """Semua baris tabel t sebagai daftar tuple bilangan bulat (kosong bila tabel tak ada)."""
    ent = tb["lay"].get(t)
    if not ent or not tb["rows"][t]:
        return []
    off, rs, cols = ent
    fmt = "<" + "".join({1: "B", 2: "H", 4: "I"}[c] for c in cols)
    return list(struct.iter_unpack(fmt, d[off:off + rs * tb["rows"][t]]))


def _il_body(d: bytes, off: int):
    """Badan metode CIL di offset berkas off -> (kode, panjang) atau None."""
    if off < 0 or off >= len(d):
        return None
    b = d[off]
    if b & 3 == 2:
        sz, start = b >> 2, off + 1
    elif b & 3 == 3 and off + 12 <= len(d):
        hs = (struct.unpack_from("<H", d, off)[0] >> 12) * 4
        sz = struct.unpack_from("<I", d, off + 4)[0]
        start = off + hs
        if hs < 12:
            return None
    else:
        return None
    if sz <= 0 or sz > NETIL_MAX_BODY or start + sz > len(d):
        return None
    return d[start:start + sz], sz


def _il_scan(code: bytes):
    """Pindai opcode. -> (token_pemanggilan, jumlah xor, jumlah lompat mundur, ldstr) atau None bila opcode tak valid / terpotong."""
    i, n = 0, len(code)
    calls: list = []
    xors = back = lds = 0
    while i < n:
        op = code[i]
        i += 1
        if op == 0xFE:
            if i >= n:
                return None
            op2 = code[i]
            i += 1
            sz = _IL2.get(op2)
            if sz is None:
                return None
            if op2 in (0x06, 0x07) and i + 4 <= n:
                calls.append(int.from_bytes(code[i:i + 4], "little"))
            i += sz
            continue
        sz = _IL1[op]
        if sz == -1:
            return None
        if sz == -2:
            if i + 4 > n:
                return None
            i += 4 + 4 * int.from_bytes(code[i:i + 4], "little")
            continue
        if sz:
            if i + sz > n:
                return None
            if op in (0x28, 0x6F, 0x73):
                calls.append(int.from_bytes(code[i:i + 4], "little"))
            elif op == 0x72:
                lds += 1
            elif 0x2B <= op <= 0x37 or op == 0xDE:
                if code[i] >= 0x80:
                    back += 1
            elif 0x38 <= op <= 0x44 or op == 0xDD:
                if code[i + 3] >= 0x80:
                    back += 1
            i += sz
        elif op == 0x61:
            xors += 1
    if i != n:
        return None
    return calls, xors, back, lds


def _netil_analyze(d: bytes, pe: dict, dn: dict | None = None) -> dict | None:
    clr = _net_clr(d, pe)
    if not clr:
        return None
    streams, r2o, etok = clr
    ts = streams.get("#~")
    if not ts:
        return {"notes": ["stream '#-' (tabel tak terkompresi) / '#~' tidak ada: tabel metadata tidak diurai"], "types": 0, "methods": 0,
                "bodies": 0, "partial": False, "pinvoke": [], "groups": {}, "calls": [], "chains": [], "decoders": [], "resources": [],
                "assemblies": [], "refs": 0, "entry": ""}
    tb = _net_tables(d, ts[0], ts[1])
    if not tb:
        return {"notes": ["tabel metadata .NET tidak bisa diurai (rusak / disengaja merusak parser)"], "types": 0, "methods": 0, "bodies": 0,
                "partial": False, "pinvoke": [], "groups": {}, "calls": [], "chains": [], "decoders": [], "resources": [], "assemblies": [],
                "refs": 0, "entry": ""}
    deadline = time.time() + NETIL_TIME
    sb, ssz = streams.get("#Strings", (0, 0))
    scache: dict = {}

    def sname(i: int) -> str:
        v = scache.get(i)
        if v is None:
            if i >= ssz or sb + i >= len(d):
                v = ""
            else:
                e = d.find(b"\0", sb + i, min(sb + ssz, sb + i + 512))
                v = _clean(d[sb + i:e if e >= 0 else sb + i + 256].decode("utf-8", "replace"))
            scache[i] = v
        return v

    def coded(name: str, v: int):
        bits, tabs = _NT_CODED[name]
        tag = v & ((1 << bits) - 1)
        return (tabs[tag] if tag < len(tabs) else -1), v >> bits

    typeref = _nt_rows(d, tb, 1)
    typedef = _nt_rows(d, tb, 2)
    methoddef = _nt_rows(d, tb, 6)
    memberref = _nt_rows(d, tb, 10)
    modref = _nt_rows(d, tb, 26)
    implmap = _nt_rows(d, tb, 28)
    asmref = _nt_rows(d, tb, 35)
    mres = _nt_rows(d, tb, 40)
    nested = _nt_rows(d, tb, 41)
    mspec = _nt_rows(d, tb, 43)
    nmeth = len(methoddef)
    enclosing = {a: b for a, b in nested}

    def tr_full(i: int) -> str:     # TypeRef (1-berbasis)
        if not 1 <= i <= len(typeref):
            return "?"
        sc, n_, ns_ = typeref[i - 1]
        nm, ns = sname(n_), sname(ns_)
        return (ns + "." + nm) if ns else nm

    td_cache: dict = {}

    def td_full(i: int, depth: int = 0) -> str:     # TypeDef
        if not 1 <= i <= len(typedef):
            return "?"
        v = td_cache.get(i)
        if v is None:
            _fl, n_, ns_ = typedef[i - 1][:3]
            nm, ns = sname(n_), sname(ns_)
            if i in enclosing and depth < 6:
                v = td_full(enclosing[i], depth + 1) + "/" + nm
            else:
                v = (ns + "." + nm) if ns else nm
            td_cache[i] = v
        return v

    owner = [0] * (nmeth + 2)
    for i, row in enumerate(typedef):
        a = row[5]
        b = typedef[i + 1][5] if i + 1 < len(typedef) else nmeth + 1
        for m in range(a, min(b, nmeth + 1)):
            owner[m] = i + 1

    def meth_full(m: int) -> str:     # MethodDef (1-berbasis)
        if not 1 <= m <= nmeth:
            return "?"
        t = owner[m]
        return "%s::%s" % (td_full(t) if t else "?", sname(methoddef[m - 1][3]))

    pinv: dict = {}      # MethodDef -> (dll, fungsi)
    for _fl, fwd, imp, scope in implmap:
        tab, idx = coded("MemberForwarded", fwd)
        if tab == 6 and 1 <= idx <= nmeth:
            dll = sname(modref[scope - 1][0]) if 1 <= scope <= len(modref) else "?"
            pinv[idx] = (dll, sname(imp))

    tok_cache: dict = {}

    def tok_name(tok: int, depth: int = 0):
        """token -> (nama, jenis) dengan jenis 'int' (MethodDef), 'ref' (MemberRef), 'pinvoke'."""
        v = tok_cache.get(tok)
        if v is not None:
            return v
        t, i = tok >> 24, tok & 0xFFFFFF
        v = ("?", "?")
        if t == 0x06 and 1 <= i <= nmeth:
            v = (meth_full(i), "pinvoke" if i in pinv else "int")
        elif t == 0x0A and 1 <= i <= len(memberref):
            cls, n_, _sig = memberref[i - 1]
            ct, ci = coded("MemberRefParent", cls)
            if ct == 1:
                owner_ = tr_full(ci)
            elif ct == 2:
                owner_ = td_full(ci)
            elif ct == 26:
                owner_ = sname(modref[ci - 1][0]) if 1 <= ci <= len(modref) else "?"
            elif ct == 6:
                owner_ = meth_full(ci)
            else:
                owner_ = "?"
            v = ("%s::%s" % (owner_, sname(n_)), "ref")
        elif t == 0x2B and 1 <= i <= len(mspec) and depth < 2:
            mt, mi = coded("MethodDefOrRef", mspec[i - 1][0])
            v = tok_name((6 if mt == 6 else 10) << 24 | mi, depth + 1)
        tok_cache[tok] = v
        return v

    def api_group(name: str):
        t, _, m = name.rpartition("::")
        for g, ms in _NETIL_API_IDX.get(t, ()):
            if ms is None or m in ms:
                return g
        return None

    pcap: dict = {}
    for cap, keys in _NET_CAPS.items():
        for k in keys:
            pcap.setdefault(k, cap)

    adj: dict = {}          # MethodDef -> {MethodDef}
    sens: dict = {}         # MethodDef -> {grup: {callee,...}}
    fan: dict = {}
    calls: list = []
    decoders: list = []
    bodies = insns = scanned = bad = 0
    partial = False
    for m in range(1, nmeth + 1):
        if m % 64 == 0 and time.time() > deadline:
            partial = True
            break
        if bodies >= NETIL_MAX_METHODS or scanned > NETIL_MAX_BYTES:
            partial = True
            break
        rva, _impl, flags = methoddef[m - 1][:3]
        if not rva or flags & 0x400 or flags & 0x2000:    # abstract / pinvokeimpl
            continue
        off = r2o(rva)
        if off is None:
            continue
        body = _il_body(d, off)
        if not body:
            bad += 1
            continue
        code, sz = body
        scanned += sz
        res = _il_scan(code)
        if res is None:
            bad += 1
            continue
        bodies += 1
        cl, xors, back, _lds = res
        insns += len(cl)
        if xors and back and sz <= 4096 and len(decoders) < 12:
            decoders.append("%s (xor x%d, loop x%d, %d byte IL)" % (meth_full(m), xors, back, sz))
        for tok in cl:
            nm, kind = tok_name(tok)
            if kind == "int":
                callee = tok & 0xFFFFFF
                adj.setdefault(m, set()).add(callee)
                fan[callee] = fan.get(callee, 0) + 1
                continue
            if kind == "pinvoke":
                callee = tok & 0xFFFFFF
                adj.setdefault(m, set()).add(callee)
                dll, fn = pinv[callee]
                g = pcap.get(fn)
                if g:
                    sens.setdefault(m, {}).setdefault(g, set()).add("%s!%s" % (dll, fn))
                    if len(calls) < NETIL_MAX_CALLS:
                        calls.append({"group": g, "callee": "%s!%s" % (dll, fn), "caller": meth_full(m)})
                continue
            g = api_group(nm) if kind == "ref" else None
            if g:
                sens.setdefault(m, {}).setdefault(g, set()).add(nm)
                if len(calls) < NETIL_MAX_CALLS:
                    calls.append({"group": g, "callee": nm, "caller": meth_full(m)})
    groups: dict = {}
    for m, gs in sens.items():
        for g, names in gs.items():
            e = groups.setdefault(g, {"n": 0, "callers": [], "apis": []})
            e["n"] += len(names)
            if len(e["callers"]) < 4:
                e["callers"].append(meth_full(m))
            for x in sorted(names):
                if x not in e["apis"] and len(e["apis"]) < 6:
                    e["apis"].append(x)
    # rantai panggilan: dari titik masuk / Main / konstruktor modul ke metode pemanggil API sensitif
    roots: list = []
    if etok >> 24 == 0x06 and 1 <= (etok & 0xFFFFFF) <= nmeth:
        roots.append(etok & 0xFFFFFF)
    for m in range(1, nmeth + 1):
        nm = sname(methoddef[m - 1][3])
        if nm == "Main" or (nm == ".cctor" and owner[m] == 1):
            if m not in roots:
                roots.append(m)
        if len(roots) >= 8:
            break
    chains: list = []
    for r in roots:
        par = {r: 0}
        queue = [(r, 0)]
        qi = 0
        while qi < len(queue) and len(chains) < 8:
            cur, dep = queue[qi]
            qi += 1
            if cur in sens:
                path, x = [], cur
                while x:
                    path.append(meth_full(x))
                    x = par[x]
                names = sorted({a for v in sens[cur].values() for a in v})[:3]
                ch = " -> ".join(reversed(path)) + "  [%s]" % ", ".join(names)
                if ch not in chains:
                    chains.append(ch)
            if dep >= 5:
                continue
            for nx in sorted(adj.get(cur, ())):
                if nx not in par:
                    par[nx] = cur
                    queue.append((nx, dep + 1))
    notes: list = []
    for g in sorted(_NETIL_WARN_GROUPS):
        if g in groups:
            notes.append("%s: %s (di %s)" % (g, ", ".join(groups[g]["apis"][:3]), ", ".join(groups[g]["callers"][:2])))
    inj = [p for p in pinv.values() if p[1] in ("VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "NtUnmapViewOfSection", "SetThreadContext", "QueueUserAPC")]
    if inj:
        notes.append("P/Invoke injeksi proses: " + ", ".join(sorted({"%s!%s" % x for x in inj})[:4]))
    if bad and nmeth and bad / max(1, bad + bodies) > 0.2 and bad >= 5:
        notes.append("%d metode berbadan IL tidak valid / tak terbaca (dugaan IL dienkripsi atau obfuskasi anti-dekompiler)" % bad)
    if partial:
        notes.append("TERPOTONG (batas waktu / ukuran)")
    resources = []
    for off_, _fl, n_, impl in mres[:40]:
        itab, _ii = coded("Implementation", impl)
        resources.append("%s%s" % (sname(n_), "" if impl == 0 else " (di %s)" % ("berkas lain" if itab == 38 else "assembly lain")))
    top_fan = sorted(fan.items(), key=lambda kv: -kv[1])[:3]
    return {
        "types": len(typedef), "methods": nmeth, "bodies": bodies, "bad_bodies": bad, "partial": partial, "notes": notes,
        "entry": meth_full(etok & 0xFFFFFF) if etok >> 24 == 0x06 and 1 <= (etok & 0xFFFFFF) <= nmeth else "",
        "refs": len(memberref), "typerefs": len(typeref),
        "assemblies": _uniq((sname(r[6]) for r in asmref), 40),
        "pinvoke": [{"dll": dll, "func": fn, "method": meth_full(m)} for m, (dll, fn) in sorted(pinv.items())[:60]],
        "n_pinvoke": len(pinv), "groups": groups, "calls": calls, "chains": chains, "decoders": decoders, "resources": resources,
        "fanin": ["%s (dipanggil %dx)" % (meth_full(m), n) for m, n in top_fan if n >= 20],
    }


def _netil_enrich(rep: dict, d: bytes) -> None:
    """Dipanggil dari triage(): rep["dotnet_il"] (kunci baru, aditif) untuk PE .NET."""
    pe, dn = rep.get("pe"), rep.get("dotnet")
    if not dn or not pe or pe.get("broken"):
        return
    try:
        r = _netil_analyze(d, pe, dn)
    except Exception as e:
        rep["warn"].append("analisis IL .NET gagal: %s" % type(e).__name__)
        return
    if r and (r["types"] or r["notes"]):
        rep["dotnet_il"] = r
        for x in r["notes"][:6]:
            rep["warn"].append("IL .NET: " + x)


def _render_netil(il, a, compact: bool, defang: bool = True) -> None:
    if not il or not il.get("types"):
        return
    a(".NET IL: %d tipe / %d metode (%d badan IL diurai), %d MemberRef, %d P/Invoke%s" % (
        il["types"], il["methods"], il["bodies"], il["refs"], il.get("n_pinvoke", 0), " | TERPOTONG" if il.get("partial") else ""))
    if il.get("entry"):
        a("   titik masuk: " + _clean(il["entry"]))
    for x in il["notes"][: (3 if compact else 10)]:
        a("   ! " + _clean(x))
    for g, e in list(il["groups"].items())[: (4 if compact else 12)]:
        a("   - %s x%d: %s | dari %s" % (g, e["n"], _clean(", ".join(e["apis"][:3])), ", ".join(_clean(c) for c in e["callers"][:2])))
    if compact:
        return
    for p in il["pinvoke"][:14]:
        a("   P/Invoke: %s!%s <- %s" % (_df(_clean(p["dll"]), defang), _clean(p["func"]), _clean(p["method"])))
    for x in il["chains"][:6]:
        a("   rantai: " + _clean(x))
    for x in il["decoders"][:5]:
        a("   kandidat dekoder: " + _clean(x))
    for x in il.get("fanin", [])[:3]:
        a("   fan-in tinggi (pembantu string / dekripsi?): " + _clean(x))
    if il["resources"]:
        a("   resource terkelola: " + ", ".join(_clean(x) for x in il["resources"][:8]))
    if il["assemblies"]:
        a("   AssemblyRef: " + ", ".join(_clean(x) for x in il["assemblies"][:10]))


def net_text(path, defang: bool = True, compact: bool = False) -> str:
    """Laporan tabel metadata + IL untuk PE .NET (CLI --net, API action 'dotnet')."""
    try:
        f_, size = _open_regular(path)
        with f_:
            d = f_.read(min(size, MAX_SCAN))
        pe = _parse_pe(d, size)
        if not pe or pe.get("broken") or not pe.get("dotnet"):
            return ".NET: bukan PE .NET (tidak ada header CLR)."
        dn = _dotnet_info(d, pe)
        il = _netil_analyze(d, pe, dn)
    except Exception as e:
        return ".NET IL gagal (%s: %s)." % (type(e).__name__, str(e)[:120])
    L: list = []
    _render_netil(il, L.append, compact, defang)
    if not L:
        return ".NET: tabel metadata tidak bisa dianalisis%s." % ((" (" + "; ".join(il["notes"]) + ")") if il and il.get("notes") else "")
    return "\n".join(L)


def _apk_deep(z, names: list[str], low: list[str], out: dict) -> None:
    """Dipanggil dari _parse_zip untuk APK: manifest biner dan DEX."""
    man = None
    try:
        mf = _zread(z, names[low.index("androidmanifest.xml")], 2 * 1024 * 1024)
        man = _axml_summary(mf)
        if man:
            out["manifest"] = man
            if man["perms"]:
                out["perms"] = sorted(set(out["perms"]) | set(man["perms"]))[:80]
    except Exception:
        pass
    dex = {"strings": 0, "types": 0, "methods": 0, "classes": 0, "hits": {}, "obf": False, "files": 0}
    dcode: dict = {}                     # v99.11 [S1]: bytecode Dalvik (kunci baru dex_info["code"], aditif)
    dentries = _dex_entry_classes(man)
    ddeadline = time.monotonic() + DEX_CODE_TIME
    for i, n in enumerate(low):
        if not re.fullmatch(r"classes\d*\.dex", n) or dex["files"] >= 4:
            continue
        try:
            raw = _zread(z, names[i], 40 * 1024 * 1024)
            r = _dex_scan(raw)
        except Exception:
            r, raw = None, b""
        if not r:
            continue
        try:
            cr = _dex_code(raw, dentries, ddeadline)
            if cr:
                _dex_code_merge(dcode, cr)
        except Exception as e_:
            out["warn"].append("analisis bytecode DEX gagal: %s" % type(e_).__name__)
        dex["files"] += 1
        for k in ("strings", "types", "methods", "classes"):
            dex[k] += r[k]
        dex["obf"] = dex["obf"] or r["obf"]
        for g, lst in r["hits"].items():
            cur = dex["hits"].setdefault(g, [])
            cur.extend(x for x in lst if x not in cur and len(cur) < 6)
    if dcode.get("methods"):
        dex["code"] = dcode
        for x_ in dcode["notes"][:6]:
            out["warn"].append("DEX bytecode: " + x_)
    if dex["files"]:
        out["dex_info"] = dex


def _render_apk(zp: dict, a, compact: bool, defang: bool = True) -> None:
    m = zp.get("manifest")
    if m:
        a("Manifest: paket %s | versi %s | SDK min %s / target %s%s%s%s" % (
            _clean(m["package"]) or "?", _clean(m["version"]), m["min_sdk"] or "?", m["target_sdk"] or "?",
            " | DEBUGGABLE" if m["debuggable"] == "true" else "", " | cleartext HTTP" if m["cleartext"] == "true" else "",
            " | allowBackup" if m["backup"] == "true" else ""))
        cnt = {k: len(v) for k, v in m["components"].items() if v}
        if cnt:
            a("   komponen: " + ", ".join("%s %d" % (k, v) for k, v in cnt.items()))
        if not compact:
            for k in ("service", "receiver"):
                if m["components"][k]:
                    a("   %s: %s" % (k, ", ".join(_clean(x) for x in m["components"][k][:8])))
        if m["exported"] and not compact:
            a("   diekspor (exported=true): " + ", ".join(_clean(x) for x in m["exported"][:8]))
        acts = [x for x in m["actions"] if any(t in x for t in ("BOOT_COMPLETED", "SMS_RECEIVED", "PACKAGE_ADDED", "NEW_OUTGOING_CALL", "USER_PRESENT", "DEVICE_ADMIN", "ACCESSIBILITY", "PHONE_STATE", "QUICKBOOT"))]
        if acts:
            a("   aksi intent sensitif: " + ", ".join(_clean(x).replace("android.intent.action.", "") for x in acts[:8]))
    di = zp.get("dex_info")
    if di:
        a("DEX    : %d berkas, %d kelas, %d metode, %d string%s" % (di["files"], di["classes"], di["methods"], di["strings"], " | nama kelas pendek (dugaan obfuskasi ProGuard/R8 atau lain)" if di["obf"] else ""))
        for g, lst in list(di["hits"].items())[: (4 if compact else 20)]:
            a("   - %s: %s" % (g, ", ".join(_clean(x).replace("Landroid/", "") for x in lst[:3])))
        _render_dexcode(di.get("code"), a, compact, defang)


# ----------------------- dekoder skrip / string tersandi -----------------------

_PS_ENC = re.compile(r"(?i)\s-(?:e|ec|en|enc|enco|encod|encode|encoded|encodedc\w*)\s+['\"]?([A-Za-z0-9+/]{16,}={0,2})")
_B64_CALL = re.compile(r"(?i)frombase64string\(\s*['\"]([A-Za-z0-9+/]{16,}={0,2})['\"]\s*\)")
_CHAR_PS = re.compile(r"(?i)(?:\[char\]\s*\(?\s*\d{2,3}\s*\)?\s*\+?\s*){5,}")
_CHAR_VB = re.compile(r"(?i)(?:chrw?\(\s*\d{2,3}\s*\)\s*&?\s*){5,}")
_CHAR_JS = re.compile(r"(?i)fromcharcode\(\s*((?:\d{2,3}\s*,\s*){4,}\d{2,3})\s*\)")
_HEX_ESC = re.compile(r"(?:\\x[0-9a-fA-F]{2}){8,}")


def _printable(t: str) -> bool:
    return len(t) >= 6 and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9


def _decode_scripts(strs: list[str]) -> list[dict]:
    """Dekode PowerShell -EncodedCommand, FromBase64String('..'), rangkaian [char] / Chr() / fromCharCode, dan \\xNN. Hanya teks; tidak dijalankan."""
    full = "\n".join(s[:4000] for s in strs)[:8 * 1024 * 1024]
    out: list[dict] = []

    def add(kind, text):
        t = text.strip()
        if _printable(t) and all(x["text"] != t[:600] for x in out) and len(out) < 12:
            out.append({"kind": kind, "text": t[:600]})

    for m in list(_PS_ENC.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        for enc in ("utf-16le", "utf-8"):
            t = raw.decode(enc, "ignore")
            if _printable(t):
                add("PowerShell -EncodedCommand", t)
                break
    for m in list(_B64_CALL.finditer(full))[:6]:
        try:
            raw = base64.b64decode(m.group(1) + "=" * (-len(m.group(1)) % 4))
        except Exception:
            continue
        t = raw.decode("utf-16le", "ignore") if raw[1:2] == b"\x00" else raw.decode("utf-8", "ignore")
        add("FromBase64String", t)
    for rx, kind in ((_CHAR_PS, "rangkaian [char]"), (_CHAR_VB, "rangkaian Chr()")):
        for m in list(rx.finditer(full))[:4]:
            codes = [int(x) for x in re.findall(r"\d{2,3}", m.group(0))]
            if all(32 <= c < 127 or c in (9, 10, 13) for c in codes):
                add(kind, "".join(chr(c) for c in codes))
    for m in list(_CHAR_JS.finditer(full))[:4]:
        codes = [int(x) for x in re.findall(r"\d+", m.group(1))]
        if all(32 <= c < 127 for c in codes):
            add("fromCharCode", "".join(chr(c) for c in codes))
    for m in list(_HEX_ESC.finditer(full))[:4]:
        try:
            add("escape \\xNN", bytes(int(x, 16) for x in re.findall(r"\\x([0-9a-fA-F]{2})", m.group(0))).decode("latin-1"))
        except ValueError:
            pass
    return out


def _script_enrich(rep: dict, strs: list[str]) -> None:
    try:
        dec = _decode_scripts(strs)
    except Exception as e:
        dec = []
        rep["warn"].append("dekoder skrip gagal: %s" % type(e).__name__)
    rep["decoded"] = dec
    if dec:
        ind = rep["ind"]
        for x in dec:   # URL di dalam teks hasil dekode ikut jadi IOC
            for u in _URL.findall(x["text"]):
                u = u.rstrip(".,;)")
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
        rep["warn"].append("string tersandi berhasil didekode (%d): %s" % (len(dec), ", ".join(sorted({x["kind"] for x in dec}))))


def _render_decoded(rep: dict, a, compact: bool, defang: bool) -> None:
    for x in (rep.get("decoded") or [])[: (2 if compact else 8)]:
        a("Hasil dekode (%s): %s" % (x["kind"], _df(_clean(x["text"])[:240 if compact else 400], defang)))


# ----------------------- v99.9 [C2]: dekoder multi-layer otomatis -----------------------
# Pipeline statis: (hex | base64) -> (gzip | zlib | deflate mentah) -> XOR satu-byte, maksimal CHAIN_MAX_LAYERS lapis, pada blok
# mencurigakan di string skrip (PowerShell / VBScript / JS), resource PE, dan resource terkelola .NET. Tidak ada yang dijalankan.
# Rantai hanya dilaporkan bila ujungnya dikenali (PE / ELF / ZIP / dokumen / teks nyata), jadi data acak tidak menghasilkan laporan palsu.

CHAIN_MAX_LAYERS = 3
CHAIN_MAX_OUT = 8 * 1024 * 1024      # batas hasil dekompresi per lapis (anti zip-bomb)
CHAIN_TIME = 2.0                     # detik untuk seluruh pemindaian lapisan
CHAIN_MAX_SRC = 24                   # jumlah blok sumber yang dicoba
_CHAIN_B64 = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}\Z")
_CHAIN_HEX = re.compile(r"(?:[0-9A-Fa-f]{2}){16,}\Z")
_CHAIN_SKIP_RES = frozenset({"ICON", "CURSOR", "BITMAP", "MENU", "DIALOG", "STRING", "ACCELERATOR", "MESSAGETABLE", "GROUP_CURSOR", "GROUP_ICON", "VERSION", "MANIFEST"})
_CHAIN_MAGIC = ((b"\x7fELF", "ELF"), (b"PK\x03\x04", "ZIP"), (b"7z\xbc\xaf\x27\x1c", "7z"), (b"Rar!", "RAR"), (b"MSCF", "CAB"),
                (b"%PDF-", "PDF"), (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "OLE2"), (b"{\\rtf", "RTF"))


def _chain_label(b: bytes) -> str | None:
    """Jenis data bila diawali tanda tangan format yang dikenal (PE harus punya penunjuk 'PE\\0\\0' yang sah)."""
    h = bytes(b[:8])
    if h[:2] == b"MZ":
        if len(b) >= 0x40:
            o = struct.unpack_from("<I", b, 0x3C)[0]
            if o < len(b) - 4 and bytes(b[o:o + 4]) == b"PE\x00\x00":
                return "PE/MZ"
        return None
    for magic, name in _CHAIN_MAGIC:
        if h.startswith(magic):
            return name
    return None


def _chain_text(b: bytes) -> str | None:
    """Teks bila isinya terbaca (UTF-8 atau UTF-16LE); None untuk data biner / acak / hampir konstan (mis. nol yang di-XOR)."""
    s = bytes(b[:4096])
    if len(s) < 8:
        return None
    u16 = s[1::2].count(0) > 0.9 * (len(s) // 2)
    t = s.decode("utf-16le" if u16 else "utf-8", "ignore").lstrip("\ufeff")
    if not u16 and len(t.encode("utf-8")) < 0.97 * len(s) - 4:
        return None
    if len(t) < 6 or len(set(t)) < 8 or max(collections.Counter(t).values()) > 0.45 * len(t):
        return None
    if sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) < 0.95 or sum(c.isalpha() for c in t) < 6:
        return None
    return bytes(b[:CHAIN_MAX_OUT]).decode("utf-16le" if u16 else "utf-8", "ignore").lstrip("\ufeff")


def _chain_known(b: bytes) -> bool:
    return bool(_chain_label(b)) or _chain_text(b) is not None


def _t_decode_text(b: bytes):
    """Lapis hex / base64 dari teks (ASCII atau UTF-16LE). Mengembalikan (nama, byte) atau None."""
    t = _chain_text(b)
    if t is None:
        return None
    c = re.sub(r"\s+", "", t)
    if len(c) > CHAIN_MAX_OUT * 2:
        return None
    if _CHAIN_HEX.match(c):
        try:
            return "hex", bytes.fromhex(c)
        except ValueError:
            return None
    if _CHAIN_B64.match(c) and len(c) % 4 != 1:
        try:
            raw = base64.b64decode(c + "=" * (-len(c) % 4))
        except Exception:
            return None
        return ("base64", raw) if len(raw) >= 16 else None
    return None


def _t_inflate(b: bytes):
    """Lapis gzip / zlib / deflate mentah, dengan batas ukuran hasil. Deflate mentah hanya diterima bila hasilnya dikenali."""
    if len(b) < 12:
        return None
    if b[:2] == b"\x1f\x8b":
        cand = (("gzip", 31),)
    elif b[0] == 0x78 and b[1] in (0x01, 0x5E, 0x9C, 0xDA):
        cand = (("zlib", 15),)
    else:
        cand = (("deflate", -15),)
    for name, wb in cand:
        try:
            out = zlib.decompressobj(wb).decompress(bytes(b[:CHAIN_MAX_OUT]), CHAIN_MAX_OUT)
        except Exception:
            continue
        if len(out) >= 8 and (name != "deflate" or _chain_known(out)):
            return name, out
    return None


def _t_xor1(b: bytes):
    """Lapis XOR satu-byte: kunci dipilih bila hasilnya dikenali (format / teks nyata). Data yang sudah dikenali tidak di-XOR lagi."""
    if len(b) < 32 or _chain_known(b):
        return None
    head = bytes(b[:512])
    if len(set(head)) < 4:
        return None
    for k in range(1, 256):
        t = head.translate(_xor_table("XOR", k))
        if _chain_label(t) or t[:2] == b"\x1f\x8b" or (t[0] == 0x78 and t[1] in (0x01, 0x5E, 0x9C, 0xDA)) or _chain_text(t) is not None:
            return "XOR 0x%02X" % k, bytes(b[:CHAIN_MAX_OUT]).translate(_xor_table("XOR", k))
    return None


def _chain_walk(data: bytes, src: str, deadline: float, min_steps: int) -> list[dict]:
    """Cari rantai dekode terpanjang dari `data`. Hasil: daftar {src, steps, kind, size, sha256, preview, urls}."""
    found: list[dict] = []

    def rec(b: bytes, steps: list[str], depth: int) -> None:
        if time.monotonic() > deadline or len(found) >= 3 or depth >= CHAIN_MAX_LAYERS:
            return
        for tf in (_t_decode_text, _t_inflate, _t_xor1):
            r = tf(b)
            if not r:
                continue
            name, nb = r
            st = steps + [name]
            lab = _chain_label(nb)
            txt = None if lab else _chain_text(nb)
            before = len(found)
            if depth + 1 < CHAIN_MAX_LAYERS:
                if txt:   # blob base64 / hex di dalam teks hasil dekode (mis. skrip PowerShell berlapis)
                    blobs = [m_ for m_ in _B64_CALL.findall(txt)[:2]] + [m_ for m_ in _B64.findall(txt)[:2]]
                    for bl in blobs:
                        rec(bl.encode("ascii", "ignore"), st, depth + 1)
                else:
                    rec(nb, st, depth + 1)
            if len(found) > before:
                return                       # rantai yang lebih dalam menang
            if (lab or txt) and len(st) >= min_steps:
                urls = [u.rstrip(".,;)") for u in _URL.findall(txt or "")][:5] if txt else []
                found.append({"src": src, "steps": st, "kind": lab or "teks", "size": len(nb), "sha256": hashlib.sha256(bytes(nb)).hexdigest(),
                              "preview": _clean((txt or "")[:160]) if txt else "", "urls": urls})
                return

    rec(bytes(data), [], 0)
    return found


def _layers_scan(d: bytes, strs: list[str], pe: dict | None, dn: dict | None) -> list[dict]:
    deadline = time.monotonic() + CHAIN_TIME
    out: list[dict] = []
    seen: set[str] = set()
    n_src = 0

    def take(res):
        for x in res:
            key = x["sha256"] + "|".join(x["steps"])
            if key not in seen and len(out) < 8:
                seen.add(key)
                out.append(x)

    # 1) resource PE dan resource terkelola .NET: satu lapis saja sudah janggal (resource sah tidak di-XOR / di-deflate mentah)
    leaves = []
    for x in (pe.get("res", []) if pe else []):
        if x["type"] not in _CHAIN_SKIP_RES and not (x.get("fmt") and x.get("fmt_ok")) and x["size"] >= 32:
            leaves.append(("resource %s/%s" % (x["type"], x["name"]), x["off"], x["size"]))
    for x in (dn.get("mres", []) if dn else []):
        if x["size"] >= 32 and not (x.get("fmt") and x.get("fmt_ok")):
            leaves.append(("resource .NET @0x%X" % x["off"], x["off"], x["size"]))
    for src, off, size in leaves:
        if n_src >= CHAIN_MAX_SRC or time.monotonic() > deadline:
            break
        n_src += 1
        take(_chain_walk(d[off:off + min(size, CHAIN_MAX_OUT)], src, deadline, 1))
    # 2) blob base64 / argumen FromBase64String / -EncodedCommand di string: satu base64 polos sudah dilaporkan _decode_b64, jadi minimal dua lapis
    cands: list[str] = []
    full = "\n".join(s[:200000] for s in strs[:4000])[:8 * 1024 * 1024]
    for rx in (_PS_ENC, _B64_CALL):
        cands += [m.group(1) for m in itertools.islice(rx.finditer(full), 6)]
    cands += [m.group(0) for m in itertools.islice(_B64.finditer(full), 12)]
    for c in _uniq(cands, CHAIN_MAX_SRC):
        if n_src >= CHAIN_MAX_SRC or time.monotonic() > deadline:
            break
        n_src += 1
        take(_chain_walk(c.encode("ascii", "ignore"), "string base64", deadline, 2))
    return out


def _layers_enrich(rep: dict, d: bytes, strs: list[str]) -> None:
    try:
        lay = _layers_scan(d, strs, rep.get("pe"), rep.get("dotnet"))
    except Exception as e:
        lay = []
        rep["warn"].append("dekoder berlapis gagal: %s" % type(e).__name__)
    rep["layers"] = lay
    if lay:
        ind = rep["ind"]
        for x in lay:
            for u in x["urls"]:
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
        x = next((y for y in lay if y["kind"] not in ("teks",)), lay[0])
        rep["warn"].append("data berlapis berhasil dibuka (%d): %s -> %s (%s)" % (len(lay), " -> ".join(x["steps"]), x["kind"], x["src"]))


def _score_layers(rep: dict, add) -> None:
    lay = rep.get("layers") or []
    if any(x["kind"] in ("PE/MZ", "ELF") for x in lay):
        add(3, "executable tersembunyi di balik lapisan dekode (%s)" % " -> ".join(next(x for x in lay if x["kind"] in ("PE/MZ", "ELF"))["steps"]))
    elif any(x["kind"] in ("ZIP", "7z", "RAR", "CAB", "OLE2") for x in lay):
        add(2, "arsip / dokumen tersembunyi di balik lapisan dekode")
    elif any(len(x["steps"]) >= 2 for x in lay):
        add(1, "teks tersembunyi di balik beberapa lapis dekode")


def _render_layers(rep: dict, a, compact: bool, defang: bool) -> None:
    for x in (rep.get("layers") or [])[: (2 if compact else 6)]:
        a("Dekode berlapis (%s): %s => %s %s, sha256 %s...%s" % (x["src"], " -> ".join(x["steps"]), x["kind"], _human(x["size"]), x["sha256"][:16],
                                                               (" | " + _df(x["preview"][:100 if compact else 160], defang)) if x["preview"] else ""))


# ----------------------- v99.20 [A2]: deobfuscation skrip berlapis (PowerShell / VBScript / JavaScript), statis -----------------------
# Teks skrip TIDAK PERNAH dijalankan: hanya ditulis ulang oleh transformasi string murni (regex + aritmetika bilangan bulat kecil).
# Tahap 1 (inline, diulang sampai stabil): sambung string ('a'+'b', "a" & "b", .concat), format -f, .Replace / -replace / Replace() / .split().join(),
#   -join / .join / [string]::Join, balik string ('..'[-1..-n], .split('').reverse().join('')), [char]N / Chr() / fromCharCode (juga aritmetika + / -),
#   daftar |%{[char]$_} / -bxor, indeks string ($env:ComSpec[4,15,25], $ShellId[1], $pshome[4]), FromBase64String(..) dalam GetString / atob / unescape,
#   escape \xNN / \uNNNN, tanda backtick PowerShell, variabel konstanta yang hanya diisi sekali (termasuk di dalam "string $var").
# Tahap 2 (bongkar pembungkus, tiap hasil menjadi lapisan baru): -EncodedCommand, FromBase64String + Deflate/Gzip(/XOR -bxor), iex / Invoke-Expression /
#   [scriptblock]::Create dengan string literal, eval / new Function / Execute / ExecuteGlobal, JS packer (Dean Edwards).
# Tahap 3: lapisan dibatasi (DSO_MAX_LAYERS dalam, DSO_MAX_NODES total), waktu (DSO_TIME), ukuran teks (DSO_MAX_TEXT). Kunci baru rep["deobf"] (None bila tidak ada
#   yang terbuka), baris "Deobfuscation skrip" di laporan, skor kecil bila isi terbuka memuat pola unduh / eksekusi; CLI `--deobf FILE [--json] [--raw] [--full]`;
#   aksi API {"action": "deobf", "path": ...}; fungsi deobfuscate(data), deobf_text(path).
# Batasan: bukan interpreter. Variabel yang diubah di banyak tempat / lewat loop, fungsi dekode buatan sendiri (string-array + rotasi gaya obfuscator.io),
#   Microsoft Script Encoder (#@~^ .vbe / .jse), AES / RC4 di skrip, dan nilai yang hanya diketahui saat jalan TIDAK dibongkar. Hasil adalah petunjuk.

DSO_TIME = 3.0
DSO_MAX_TEXT = 2 * 1024 * 1024
DSO_MAX_LAYERS = 6
DSO_MAX_NODES = 12
DSO_MAX_PASS = 24
_DSO_RX: dict = {}


def _dso_rx(p: str, flags: int = 0):
    k = (p, flags)
    r = _DSO_RX.get(k)
    if r is None:
        r = _DSO_RX[k] = re.compile(p, flags)
    return r


def _dso_S(lang: str) -> str:
    """Regex satu string literal 'aman' (tanpa interpolasi $ pada "..." PowerShell). Tanpa grup penangkap."""
    if lang == "powershell":
        return r"""(?:'(?:[^'\r\n]|'')*'|"(?:[^"\r\n`$]|`[^\r\n]|"")*")"""
    if lang == "vbscript":
        return r'"(?:[^"\r\n]|"")*"'
    return r"""(?:'(?:[^'\\\r\n]|\\.)*'|"(?:[^"\\\r\n]|\\.)*")"""


def _dso_Sfull(lang: str) -> str:
    if lang == "powershell":
        return r"""'(?:[^'\r\n]|'')*'|"(?:[^"\r\n`]|`[^\r\n]|"")*\""""
    return _dso_S(lang)


_DSO_PSESC = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
_DSO_JSESC = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v"}


def _dso_unq(tok: str, lang: str) -> str:
    q, b = tok[0], tok[1:-1]
    if lang == "powershell":
        if q == "'":
            return b.replace("''", "'")
        return re.sub(r"`(.)", lambda m: _DSO_PSESC.get(m.group(1), m.group(1)), b.replace('""', '"'))
    if lang == "vbscript":
        return b.replace('""', '"')

    def esc(m):
        g = m.group(1)
        try:
            if g[0] == "x" and len(g) == 3:
                return chr(int(g[1:], 16))
            if g[0] == "u":
                return chr(int(g[1:].strip("{}"), 16))
            if g.isdigit() and all(c in "01234567" for c in g):
                return chr(int(g, 8))
        except (ValueError, OverflowError):
            return m.group(0)
        return _DSO_JSESC.get(g, g)
    return re.sub(r"\\(x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]{1,6}\}|u[0-9a-fA-F]{4}|[0-3]?[0-7]{1,2}|.)", esc, b)


def _dso_q(s: str, lang: str):
    """Bungkus teks sebagai literal; None bila tidak bisa direpresentasikan (dibiarkan apa adanya oleh pemanggil)."""
    if len(s) > 400000 or any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        return None
    if lang == "javascript":
        out = []
        for c in s:
            o = ord(c)
            out.append("\\\\" if c == "\\" else '\\"' if c == '"' else "\\n" if c == "\n" else "\\r" if c == "\r" else "\\t" if c == "\t"
                       else "\\x%02x" % o if o < 32 or o == 127 else c)
        return '"' + "".join(out) + '"'
    if lang == "vbscript":
        if "\r" in s or "\n" in s or "\0" in s:
            return None
        return '"' + s.replace('"', '""') + '"'
    if any(ord(c) < 32 and c != "\t" for c in s):
        t = s.replace("`", "``").replace('"', '`"').replace("$", "`$").replace("\n", "`n").replace("\r", "`r").replace("\t", "`t").replace("\0", "`0")
        return None if any(ord(c) < 32 for c in t) else '"' + t + '"'
    return "'" + s.replace("'", "''") + "'"


_DSO_NUM = r"(?:0[xX][0-9a-fA-F]+|&[hH][0-9a-fA-F]+|\d{1,7})"


def _dso_num(s: str) -> int:
    s = s.strip()
    return int(s[2:], 16) if s[:2].lower() in ("0x", "&h") else int(s)


def _dso_arith(s: str):
    """Hanya bilangan bulat dengan + dan -; None bila bentuknya lain."""
    m = _dso_rx(r"(%s)((?:\s*[+\-]\s*%s)*)" % (_DSO_NUM, _DSO_NUM)).fullmatch(s.strip())
    if not m:
        return None
    v = _dso_num(m.group(1))
    for op, n in _dso_rx(r"([+\-])\s*(%s)" % _DSO_NUM).findall(m.group(2)):
        v = v + _dso_num(n) if op == "+" else v - _dso_num(n)
    return v


def _dso_chr(code, lang: str):
    if code is None or not 0 <= code < 0x110000 or 0xD800 <= code <= 0xDFFF:
        return None
    return _dso_q(chr(code), lang)


def _dso_lits(s: str, lang: str) -> list[str]:
    return [_dso_unq(t, lang) for t in _dso_rx(_dso_S(lang)).findall(s)]


def _dso_sub_outside(text: str, lang: str, rx, fn) -> str:
    """Seperti rx.sub, tetapi hanya di luar string literal; fn(m) -> pengganti atau None (lewati)."""
    spans = [(m.start(), m.end()) for m in _dso_rx(_dso_Sfull(lang)).finditer(text)]
    starts = [a for a, _ in spans]
    out, last = [], 0
    for m in rx.finditer(text):
        i = bisect.bisect_right(starts, m.start()) - 1
        if i >= 0 and spans[i][0] <= m.start() < spans[i][1]:
            continue
        r = fn(m)
        if r is None or m.start() < last:
            continue
        out.append(text[last:m.start()])
        out.append(r)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


# --- transformasi inline: tiap fungsi (text, lang) -> text (sama bila tidak ada perubahan) ---

def _dso_t_jsesc(text: str, lang: str) -> str:
    if lang != "javascript" or "\\" not in text:
        return text

    def f(m):
        tok = m.group(0)
        if not _dso_rx(r"\\(?:x[0-9a-fA-F]{2}|u[0-9a-fA-F{])").search(tok):
            return tok
        q = _dso_q(_dso_unq(tok, lang), lang)
        return q if q is not None else tok
    return _dso_rx(_dso_S(lang)).sub(f, text)


def _dso_t_ticks(text: str, lang: str) -> str:
    if lang != "powershell" or "`" not in text:
        return text
    return _dso_sub_outside(text, lang, _dso_rx(r"`(?=[^\s`])"), lambda m: "")


def _dso_t_chars(text: str, lang: str) -> str:
    low = text.lower()
    if lang == "powershell" and "[char" in low:
        LIST = r"(%s(?:\s*,\s*%s)*)" % (_DSO_NUM, _DSO_NUM)
        text = _dso_rx(r"(?i)\[char\[\]\]\s*\(\s*%s\s*\)" % LIST).sub(
            lambda m: _dso_q("".join(chr(_dso_num(x)) for x in m.group(1).split(",") if 0 <= _dso_num(x) < 0x110000 and not 0xD800 <= _dso_num(x) <= 0xDFFF), lang) or m.group(0), text)
        core = r"%s\s*\|\s*(?:%%|foreach(?:-object)?)\s*\{\s*\[char\]\s*\(?\s*\$_\s*(?:-bxor\s*(%s)\s*)?\)?\s*\}" % (LIST, _DSO_NUM)

        def piped(m):
            x = _dso_num(m.group(2)) if m.group(2) else 0
            try:
                return _dso_q("".join(chr(_dso_num(v) ^ x) for v in m.group(1).split(",")), lang) or m.group(0)
            except (ValueError, OverflowError):
                return m.group(0)
        text = _dso_rx("(?i)" + core).sub(piped, text)
        text = _dso_rx(r"(?i)\[char\]\s*(?:\(\s*([0-9a-fx+\-\s]{1,40}?)\s*\)|(%s)(?![\w.]))" % _DSO_NUM).sub(
            lambda m: _dso_chr(_dso_arith(m.group(1) or m.group(2)), lang) or m.group(0), text)
    elif lang == "vbscript" and "chr" in low:
        text = _dso_rx(r"(?i)\bchrw?\$?\(\s*([^()]{1,40}?)\s*\)").sub(lambda m: _dso_chr(_dso_arith(m.group(1)), lang) or m.group(0), text)
    elif lang == "javascript" and "fromc" in low:
        def f(m):
            codes = [_dso_arith(x) for x in m.group(1).split(",")]
            if not codes or any(c is None or not 0 <= c < 0x110000 or 0xD800 <= c <= 0xDFFF for c in codes):
                return m.group(0)
            return _dso_q("".join(chr(c) for c in codes), lang) or m.group(0)
        text = _dso_rx(r"(?i)String\s*\.\s*fromCharCode\s*\(\s*([^()]{1,8000}?)\s*\)").sub(f, text)
    return text


_DSO_ENVSTR = {"env:comspec": "C:\\Windows\\system32\\cmd.exe", "shellid": "Microsoft.PowerShell", "pshome": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0"}


def _dso_t_psenv(text: str, lang: str) -> str:
    """$env:ComSpec[4,15,25], $ShellId[1], $pshome[4]: indeks ke nilai baku (asumsi jalur Windows standar)."""
    if lang != "powershell" or "[" not in text:
        return text

    def f(m):
        base = _DSO_ENVSTR[m.group(1).lower()]
        idx = [int(x) for x in m.group(2).split(",")]
        if any(i >= len(base) for i in idx):
            return m.group(0)
        return _dso_q("".join(base[i] for i in idx), lang) or m.group(0)
    return _dso_rx(r"(?i)\$(env:comspec|shellid|pshome)\s*\[\s*(\d{1,3}(?:\s*,\s*\d{1,3})*)\s*\]").sub(f, text)


def _dso_t_concat(text: str, lang: str) -> str:
    S = _dso_S(lang)
    op = r"[ \t]*(?:&|\+)[ \t]*(?:_?\r?\n[ \t]*)?" if lang == "vbscript" else r"[ \t]*\+[ \t]*(?:\r?\n[ \t]*)?"
    rx = _dso_rx(r"(?:%s)(?:%s(?:%s))+(?![ \t]*[.\[(\w$])" % (S, op, S))
    bad_pre = _dso_rx(r"(?i)-(?:f|[ci]?replace|join|split|[ci]?(?:eq|ne|like|match|contains|notlike|notmatch))$")

    def f(m):
        if lang == "powershell":
            pre = text[max(0, m.start() - 16):m.start()].rstrip()
            if pre.endswith(",") or bad_pre.search(pre) or text[m.end():m.end() + 4].lstrip(" \t").startswith(","):
                return m.group(0)
        q = _dso_q("".join(_dso_lits(m.group(0), lang)), lang)
        return q if q is not None else m.group(0)
    return rx.sub(f, text)


def _dso_t_fmt(text: str, lang: str) -> str:
    if lang != "powershell" or "-f" not in text.lower():
        return text
    S = _dso_S(lang)
    ARG = r"(?:%s|[+-]?\d{1,9})" % S
    rx = _dso_rx(r"(?i)(%s)\s*-f\s*(%s(?:\s*,\s*%s)*)(?![\w$(\[.])" % (S, ARG, ARG))

    def f(m):
        fmt = _dso_unq(m.group(1), lang)
        args = [_dso_unq(a, lang) if a[0] in "'\"" else a for a in _dso_rx(ARG).findall(m.group(2))]
        bad = []

        def sub(mm):
            if mm.group(0) == "{{":
                return "{"
            if mm.group(0) == "}}":
                return "}"
            i = int(mm.group(1))
            if i >= len(args):
                bad.append(1)
                return ""
            return args[i]
        try:
            out = _dso_rx(r"\{\{|\}\}|\{(\d+)\}").sub(sub, fmt)
        except Exception:
            return m.group(0)
        if bad or _dso_rx(r"\{\d+[,:][^{}]*\}").search(fmt):
            return m.group(0)
        return _dso_q(out, lang) or m.group(0)
    return rx.sub(f, text)


def _dso_t_replace(text: str, lang: str) -> str:
    low = text.lower()
    if "replace" not in low and "split" not in low:
        return text
    S = _dso_S(lang)
    if lang == "powershell":
        text = _dso_rx(r"(?i)(%s)\s*\.\s*replace\s*\(\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang)), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)

        def rr(m):
            pre = text[max(0, m.start() - 4):m.start()].rstrip()
            if pre.endswith("+") or pre.endswith(","):
                return m.group(0)
            rep = _dso_unq(m.group(3), lang) if m.group(3) else ""
            if "$" in rep or text[m.end():m.end() + 4].lstrip().startswith(","):
                return m.group(0)
            try:
                out = _dso_rx(_dso_unq(m.group(2), lang), re.I if m.group(0).lower().find("-creplace") < 0 else 0).sub(lambda _m: rep, _dso_unq(m.group(1), lang))
            except re.error:
                return m.group(0)
            return _dso_q(out, lang) or m.group(0)
        text = _dso_rx(r"(?i)(%s)\s*-[ci]?replace\s*(%s)(?:\s*,\s*(%s))?" % (S, S, S)).sub(rr, text)
    elif lang == "vbscript":
        text = _dso_rx(r"(?i)\bReplace\(\s*(%s)\s*,\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang)), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)
    else:
        text = _dso_rx(r"(%s)\s*\.\s*replace\s*\(\s*(%s)\s*,\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: m.group(0) if "$" in m.group(3) or not _dso_unq(m.group(2), lang) else
            (_dso_q(_dso_unq(m.group(1), lang).replace(_dso_unq(m.group(2), lang), _dso_unq(m.group(3), lang), 1), lang) or m.group(0)), text)

        def rl(m):
            rep = _dso_unq(m.group(4), lang)
            if "$" in rep:
                return m.group(0)
            try:
                pat = _dso_rx(m.group(2), re.I if "i" in m.group(3) else 0)
            except re.error:
                return m.group(0)
            return _dso_q(pat.sub(lambda _m: rep, _dso_unq(m.group(1), lang), count=0 if "g" in m.group(3) else 1), lang) or m.group(0)
        text = _dso_rx(r"(%s)\s*\.\s*replace\s*\(\s*/((?:[^/\\\r\n]|\\.){1,200})/([gimsuy]*)\s*,\s*(%s)\s*\)" % (S, S)).sub(rl, text)
        text = _dso_rx(r"(%s)\s*\.\s*split\(\s*(%s)\s*\)\s*\.\s*join\(\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: (_dso_q(_dso_unq(m.group(3), lang).join(_dso_unq(m.group(1), lang).split(_dso_unq(m.group(2), lang))), lang) or m.group(0)) if _dso_unq(m.group(2), lang) else m.group(0), text)
    return text


def _dso_t_join(text: str, lang: str) -> str:
    low = text.lower()
    if "join" not in low and "concat" not in low and "[-1" not in low and "][" not in low and "[" not in low:
        return text
    S = _dso_S(lang)
    LS = r"%s(?:\s*,\s*%s)*" % (S, S)
    EMPTY = r"""(?:''|"")"""

    def jn(items, sep, ln=lang):
        return _dso_q(sep.join(items), ln)

    if lang == "powershell":
        text = _dso_rx(r"(?i)(%s)\s*\[\s*-1\s*\.\.\s*-[^\]]{1,40}\]" % S).sub(lambda m: _dso_q(_dso_unq(m.group(1), lang)[::-1], lang) or m.group(0), text)

        def idx(m):
            s = _dso_unq(m.group(1), lang)
            ix = [int(x) for x in m.group(2).split(",")]
            return _dso_q("".join(s[i] for i in ix), lang) or m.group(0) if all(0 <= i < len(s) for i in ix) else m.group(0)
        text = _dso_rx(r"(?<![,\w$])(%s)\s*\[\s*(\d{1,4}(?:\s*,\s*\d{1,4})*)\s*\]" % S).sub(idx, text)
        text = _dso_rx(r"(?i)@?\(\s*(%s)\s*\)\s*-join\s*(%s)" % (LS, S)).sub(lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang)) or m.group(0), text)
        text = _dso_rx(r"(?i)-join\s*@?\(\s*(%s)\s*\)" % LS).sub(lambda m: jn(_dso_lits(m.group(1), lang), "") or m.group(0), text)
        text = _dso_rx(r"(?i)(%s)\s*-join\s*%s" % (S, EMPTY)).sub(lambda m: m.group(1), text)
        text = _dso_rx(r"(?i)-join\s*(%s)(?!\s*,)" % S).sub(lambda m: m.group(1), text)
        text = _dso_rx(r"(?i)\[string\]\s*::\s*join\s*\(\s*(%s)\s*,\s*@?\(?\s*(%s)\s*\)?\s*\)" % (S, LS)).sub(
            lambda m: jn(_dso_lits(m.group(2), lang), _dso_unq(m.group(1), lang)) or m.group(0), text)
    elif lang == "javascript":
        text = _dso_rx(r"(%s)\s*\.\s*split\(\s*(%s)\s*\)\s*\.\s*reverse\(\s*\)\s*\.\s*join\(\s*(%s)\s*\)" % (S, S, S)).sub(
            lambda m: jn(_dso_unq(m.group(1), lang).split(_dso_unq(m.group(2), lang))[::-1] if _dso_unq(m.group(2), lang) else list(_dso_unq(m.group(1), lang))[::-1], _dso_unq(m.group(3), lang)) or m.group(0), text)
        text = _dso_rx(r"\[\s*(%s)\s*\]\s*\.\s*join\(\s*(%s)?\s*\)" % (LS, S)).sub(
            lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang) if m.group(2) else ",") or m.group(0), text)
        text = _dso_rx(r"(%s)\s*\.\s*concat\(\s*(%s)\s*\)" % (S, LS)).sub(
            lambda m: jn([_dso_unq(m.group(1), lang)] + _dso_lits(m.group(2), lang), "") or m.group(0), text)
    else:
        text = _dso_rx(r"(?i)\bJoin\(\s*Array\(\s*(%s)\s*\)\s*,\s*(%s)\s*\)" % (LS, S)).sub(
            lambda m: jn(_dso_lits(m.group(1), lang), _dso_unq(m.group(2), lang)) or m.group(0), text)
    return text


def _dso_t_b64(text: str, lang: str) -> str:
    low = text.lower()
    S = _dso_S(lang)

    def dec(b64: str):
        try:
            raw = base64.b64decode(re.sub(r"\s+", "", b64) + "=" * (-len(re.sub(r"\s+", "", b64)) % 4), validate=False)
        except Exception:
            return None
        return raw

    def okt(t: str) -> bool:
        return len(t) >= 1 and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9

    if lang == "powershell" and "getstring" in low:
        encs = {"utf8": "utf-8", "unicode": "utf-16le", "ascii": "ascii", "bigendianunicode": "utf-16be", "utf32": "utf-32le", "utf7": "utf-7", "default": "utf-8"}

        def f(m):
            raw = dec(_dso_unq(m.group(2), lang))
            if raw is None:
                return m.group(0)
            try:
                t = raw.decode(encs[m.group(1).lower()], "strict")
            except Exception:
                return m.group(0)
            return (_dso_q(t, lang) or m.group(0)) if okt(t) else m.group(0)
        text = _dso_rx(r"(?i)\[\s*(?:System\.)?Text\.Encoding\s*\]\s*::\s*(utf8|unicode|ascii|bigendianunicode|utf32|utf7|default)\s*\.\s*GetString\s*\(\s*"
                       r"\[\s*(?:System\.)?Convert\s*\]\s*::\s*FromBase64String\s*\(\s*(%s)\s*\)\s*\)" % S).sub(f, text)
    if lang == "javascript" and "atob" in low:
        def g(m):
            raw = dec(_dso_unq(m.group(1), lang))
            if raw is None:
                return m.group(0)
            t = raw.decode("latin-1")
            return (_dso_q(t, lang) or m.group(0)) if okt(t) else m.group(0)
        text = _dso_rx(r"(?:window\s*\.\s*)?atob\s*\(\s*(%s)\s*\)" % S).sub(g, text)
    if lang == "javascript" and ("unescape" in low or "decodeuri" in low):
        def h(m):
            s = _dso_unq(m.group(1), lang)
            try:
                s2 = _dso_rx(r"%u([0-9a-fA-F]{4})|%([0-9a-fA-F]{2})").sub(lambda mm: chr(int(mm.group(1) or mm.group(2), 16)), s)
            except (ValueError, OverflowError):
                return m.group(0)
            return _dso_q(s2, lang) or m.group(0)
        text = _dso_rx(r"(?:unescape|decodeURIComponent|decodeURI)\s*\(\s*(%s)\s*\)" % S).sub(h, text)
    return text


def _dso_t_alias(text: str, lang: str) -> str:
    if lang != "powershell":
        return text
    return _dso_rx(r"""(?i)[.&]\s*\(\s*(['"])(iex|invoke-expression)\1\s*\)""").sub(lambda m: m.group(2), text)


def _dso_vars_n(text: str, name: str, lang: str) -> int:
    if lang == "powershell":
        return len(_dso_rx(r"(?i)\$(?:script:|global:|local:)?%s\b\s*[-+*/%%]?=(?!=)" % re.escape(name)).findall(text))
    if lang == "vbscript":
        return len(_dso_rx(r"(?im)^[ \t]*(?:(?:Dim|Const|Set)[ \t]+)?%s[ \t]*=" % re.escape(name)).findall(text))
    return len(_dso_rx(r"(?<![\w$.])%s\s*(?:[-+*/%%&|^]|<<|>>>?)?=(?![=>])" % re.escape(name)).findall(text))


def _dso_ps_expand(body: str, defs: dict):
    out, i, n = [], 0, len(body)
    var = _dso_rx(r"\$(?:\{(\w+)\}|\(\s*\$(\w+)\s*\)|(?:script:|global:)?(\w+))")
    while i < n:
        c = body[i]
        if c == "`" and i + 1 < n:
            out.append(_DSO_PSESC.get(body[i + 1], body[i + 1]))
            i += 2
        elif c == '"' and body[i + 1:i + 2] == '"':
            out.append('"')
            i += 2
        elif c == "$":
            m = var.match(body, i)
            nm = (m.group(1) or m.group(2) or m.group(3)) if m else None
            if not nm or nm.lower() not in defs:
                return None
            out.append(defs[nm.lower()])
            i = m.end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _dso_t_vars(text: str, lang: str) -> str:
    S = _dso_S(lang)
    if lang == "powershell":
        asg = _dso_rx(r"(?im)\$(?:script:|global:|local:)?([A-Za-z_]\w*)[ \t]*=[ \t]*(%s)[ \t]*(?=;|\r?$)" % S)
    elif lang == "vbscript":
        asg = _dso_rx(r"""(?im)^[ \t]*(?:(?:Dim|Const)[ \t]+)?([A-Za-z_]\w*)[ \t]*=[ \t]*(%s)[ \t]*(?:'[^\r\n]*)?\r?$""" % S)
    else:
        asg = _dso_rx(r"""(?m)\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*(%s)\s*(?=[;,\r\n]|$)""" % S)
    defs: dict = {}
    for m in itertools.islice(asg.finditer(text), 400):
        nm = m.group(1)
        key = nm if lang == "javascript" else nm.lower()
        if key in defs or len(defs) >= 64:
            defs[key] = None
            continue
        bad = (lang == "powershell" and _dso_rx(r"(?i)(?:\$%s\s+in\b|\$%s(?:\+\+|--)|\[ref\]\s*\$%s|-(?:out)?variable\s+%s\b|param\s*\([^)]*\$%s\b)" % ((re.escape(nm),) * 5)).search(text)) or \
              (lang == "javascript" and _dso_rx(r"(?:function\s*[\w$]*\s*\([^)]*\b%s\b|(?<![\w$.])%s(?:\+\+|--))" % ((re.escape(nm),) * 2)).search(text))
        if bad or _dso_vars_n(text, nm, lang) != 1:
            defs[key] = None
            continue
        defs[key] = m.group(2)
    defs = {k: v for k, v in defs.items() if v}
    if not defs:
        return text
    if lang == "powershell":
        names = "|".join(re.escape(k) for k in sorted(defs, key=len, reverse=True))
        use = _dso_rx(r"(?i)(?<![\w$])\$(?:script:|global:|local:)?(%s)(?![\w:])(?!\s*[-+*/%%]?=(?!=))" % names)
        text = _dso_sub_outside(text, lang, use, lambda m: defs[m.group(1).lower()])
        vals = {k: _dso_unq(v, lang) for k, v in defs.items()}

        def dq(m):
            tok = m.group(0)
            if tok[0] != '"' or "$" not in tok:
                return tok
            e = _dso_ps_expand(tok[1:-1], vals)
            q = _dso_q(e, lang) if e is not None else None
            return q if q is not None else tok
        return _dso_rx(_dso_Sfull(lang)).sub(dq, text)
    names = "|".join(re.escape(k) for k in sorted(defs, key=len, reverse=True))
    if lang == "vbscript":
        use = _dso_rx(r"(?i)(?<![\w.])(%s)(?!\w)" % names)

        def fv(m):
            ls = text.rfind("\n", 0, m.start()) + 1
            pre = text[ls:m.start()]
            if _dso_rx(r"(?i)\s*(?:dim|redim|const|private|public|for|function|sub|next|set)\b").match(pre) or (not pre.strip() and _dso_rx(r"\s*=(?!=)").match(text, m.end())):
                return None
            return defs[m.group(1).lower()]
        return _dso_sub_outside(text, lang, use, fv)
    use = _dso_rx(r"(?<![\w$.])(%s)(?![\w$])(?!\s*(?:[-+*/%%&|^]|<<|>>>?)?=(?![=>]))(?!\s*:)" % names)

    def fj(m):
        if _dso_rx(r"(?:var|let|const|function)\s+$").search(text[max(0, m.start() - 12):m.start()]):
            return None
        return defs[m.group(1)]
    return _dso_sub_outside(text, lang, use, fj)


_DSO_TRANSFORMS = (("kunci / escape", _dso_t_jsesc), ("backtick", _dso_t_ticks), ("variabel", _dso_t_vars), ("karakter", _dso_t_chars), ("indeks env", _dso_t_psenv),
                   ("base64 inline", _dso_t_b64), ("sambung string", _dso_t_concat), ("format -f", _dso_t_fmt), ("replace / split", _dso_t_replace),
                   ("join / balik / indeks", _dso_t_join), ("alias iex", _dso_t_alias))


def _dso_inline(text: str, lang: str, deadline: float):
    names: list[str] = []
    for _ in range(DSO_MAX_PASS):
        before = text
        for nm, fn in _DSO_TRANSFORMS:
            if time.monotonic() > deadline:
                return text, names
            try:
                t2 = fn(text, lang)
            except (RecursionError, MemoryError):
                continue
            if t2 != text and len(t2) <= DSO_MAX_TEXT * 2:
                text = t2
                if nm not in names:
                    names.append(nm)
        if text == before:
            break
    return text, names


def _dso_lang(text: str, hint: str | None = None) -> str:
    if hint in ("powershell", "vbscript", "javascript"):
        return hint
    return max(_dso_lang_scores(text), key=lambda x: x[0])[1]


def _dso_lang_scores(text: str) -> list:
    h = text[:200000]
    ps = len(re.findall(r"(?i)\$\w+\s*=|-join\b|\[char\]|\biex\b|invoke-expression|frombase64string|\bnew-object\b|-bxor|\bwrite-host\b|\[convert\]|\[system\.", h))
    js = len(re.findall(r"(?i)\bvar\s+\w+|\bfunction\s*\w*\s*\(|fromcharcode|unescape\(|\beval\(|\batob\(|document\.|=>|\.split\(|\.join\(", h))
    vb = len(re.findall(r"(?i)\bdim\s+\w+|\bchrw?\(|wscript\.|createobject|\bexecute(?:global)?\b|^\s*set\s+\w+\s*=|\bend\s+(?:sub|function|if)\b", h, re.M))
    if re.search(r"(?i)\bpowershell(?:\.exe)?\b[^\r\n]{0,200}\s-(?:e|ec|enc|encodedcommand|nop|noprofile|w|windowstyle|command|c)\b", h):
        ps += 3
    return [(ps, "powershell"), (js, "javascript"), (vb, "vbscript")]


def _dso_to_text(data) -> str:
    b = bytes(data[:DSO_MAX_TEXT * 2])
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16", "ignore")
    if len(b) >= 8 and b[1::2].count(0) > 0.9 * (len(b) // 2):
        return b.decode("utf-16le", "ignore")
    return b.decode("utf-8", "replace").lstrip("\ufeff")


def _dso_text_ok(t: str, minlen: int = 4) -> bool:
    return len(t) >= minlen and sum(1 for c in t if c.isprintable() or c in "\r\n\t") / len(t) >= 0.9


def _dso_b64raw(b64: str):
    c = re.sub(r"\s+", "", b64)
    if len(c) < 16 or len(c) % 4 == 1:
        return None
    try:
        return base64.b64decode(c + "=" * (-len(c) % 4))
    except Exception:
        return None


def _dso_blob(raw: bytes, keys: list, deadline: float):
    """base64 -> [gzip / zlib / deflate / XOR] sampai dikenali. -> (langkah, teks | None, label | None, byte) atau None."""
    steps = ["base64"]
    b = bytes(raw)
    for _ in range(3):
        if time.monotonic() > deadline:
            return None
        lab = _chain_label(b)
        if lab or _chain_text(b) is not None:
            return steps, (None if lab else _chain_text(b)), lab, b
        r = _t_inflate(b)
        if r:
            steps.append(r[0])
            b = r[1]
            continue
        hit = None
        for k in keys:
            t = b[:512].translate(_xor_table("XOR", k))
            if _chain_label(t) or t[:2] == b"\x1f\x8b" or (t[0] == 0x78 and t[1] in (0x01, 0x5E, 0x9C, 0xDA)) or _chain_text(t) is not None:
                hit = k
                break
        if hit is None:
            return None
        steps.append("XOR 0x%02X" % hit)
        b = bytes(b[:CHAIN_MAX_OUT]).translate(_xor_table("XOR", hit))
    lab = _chain_label(b)
    if lab or _chain_text(b) is not None:
        return steps, (None if lab else _chain_text(b)), lab, b
    return None


def _dso_js_packer(text: str):
    S = _dso_S("javascript")
    m = _dso_rx(r"(?s)eval\s*\(\s*function\s*\(\s*p\s*,\s*a\s*,\s*c\s*,\s*k\s*,\s*e\s*,\s*[dr]\s*\)\s*\{.{0,3000}?\}\s*\(\s*(%s)\s*,\s*(\d{1,3})\s*,\s*(\d{1,6})\s*,\s*(%s)\s*\.\s*split\(\s*(%s)\s*\)" % (S, S, S)).search(text)
    if not m:
        return None
    p, a, c = _dso_unq(m.group(1), "javascript"), int(m.group(2)), int(m.group(3))
    k = _dso_unq(m.group(4), "javascript").split(_dso_unq(m.group(5), "javascript"))
    if not 2 <= a <= 62 or c > 200000:
        return None
    digs = "0123456789abcdefghijklmnopqrstuvwxyz"

    def enc(n: int) -> str:
        r = "" if n < a else enc(n // a)
        n %= a
        return r + (chr(n + 29) if n > 35 else digs[n])
    d = {}
    for i in range(min(c, len(k))):
        d[enc(i)] = k[i] or enc(i)
    out = _dso_rx(r"\b\w+\b").sub(lambda mm: d.get(mm.group(0), mm.group(0)), p)
    return out if _dso_text_ok(out, 8) else None


def _dso_payloads(text: str, lang: str, deadline: float) -> list:
    """Pembungkus yang bisa dibuka dari `text` (sudah melewati tahap inline). -> [(via, payload str | bytes, binary, lang)]."""
    out: list = []

    def add(via, pay, binary=False, plang=None):
        if len(out) < 8:
            out.append((via, pay, binary, plang or lang))

    def code_like(t: str) -> bool:
        return _dso_text_ok(t, 4) and bool(re.search(r"[\s;(|$=]", t)) and bool(re.search(r"[A-Za-z]{3}", t)) and sum(c.isalnum() for c in t) >= 0.4 * len(t)

    S = _dso_S(lang)
    for m in itertools.islice(_PS_ENC.finditer(text), 4):
        raw = _dso_b64raw(m.group(1))
        if raw is None:
            continue
        for enc in ("utf-16le", "utf-8"):
            t = raw.decode(enc, "ignore")
            if _dso_text_ok(t, 6):
                add("-EncodedCommand", t, False, "powershell")
                break
    if lang == "powershell":
        pat = (r"(?is)(?:\b(?:iex|invoke-expression)\b|\[\s*scriptblock\s*\]\s*::\s*create|\.\s*invokecommand\s*\.\s*invokescript)\s*\(?\s*(%s)" % S,
               r"(?is)(%s)\s*\)?\s*\|\s*(?:iex|invoke-expression)\b" % S)
        for rx in pat:
            for m in itertools.islice(_dso_rx(rx).finditer(text), 4):
                t = _dso_unq(m.group(1), lang)
                if code_like(t):
                    add("iex / Invoke-Expression (string literal)", t, False, "powershell")
        if _dso_rx(r"(?i)deflatestream|gzipstream|io\.compression|-bxor|assembly\s*\]\s*::\s*load").search(text):
            keys = [_dso_num(x) & 0xFF for x in _dso_rx(r"(?i)-bxor\s*(%s)" % _DSO_NUM).findall(text)]
            nums = {n.lower(): _dso_num(v) & 0xFF for n, v in _dso_rx(r"(?i)\$(\w+)\s*=\s*(%s)\s*(?=[;\r\n]|$)" % _DSO_NUM).findall(text)}
            for n in _dso_rx(r"(?i)-bxor\s*\$(\w+)").findall(text):
                if n.lower() in nums:
                    keys.append(nums[n.lower()])
            keys = [k for k in dict.fromkeys(keys) if 1 <= k < 256]
            for m in itertools.islice(_dso_rx(r"(?i)FromBase64String\s*\(\s*(%s)\s*\)" % S).finditer(text), 4):
                raw = _dso_b64raw(_dso_unq(m.group(1), lang))
                r = _dso_blob(raw, keys, deadline) if raw is not None and len(raw) >= 16 else None
                if r and len(r[0]) >= 2:
                    steps, t, lab, b = r
                    via = " > ".join(steps)
                    if lab:
                        add(via + " (%s)" % lab, bytes(b), True)
                    elif t:
                        add(via, t[:DSO_MAX_TEXT], False, _dso_lang(t))
    elif lang == "javascript":
        for rx in (r"\beval\s*\(\s*(%s)" % S, r"\bnew\s+Function\s*\(\s*(?:%s\s*,\s*)*(%s)\s*\)" % (S, S), r"\bset(?:Timeout|Interval)\s*\(\s*(%s)" % S, r"document\s*\.\s*write(?:ln)?\s*\(\s*(%s)" % S):
            for m in itertools.islice(_dso_rx(rx).finditer(text), 4):
                t = _dso_unq(m.group(1), lang)
                if code_like(t) and len(t) >= 8 and (not rx.startswith("document") or "<script" in t.lower()):
                    add("eval / Function / setTimeout (string literal)" if not rx.startswith("document") else "document.write (HTML / script)", t, False, "javascript")
        pk = _dso_js_packer(text)
        if pk:
            add("JS packer (Dean Edwards)", pk, False, "javascript")
    else:
        for m in itertools.islice(_dso_rx(r"(?i)\b(?:Execute|ExecuteGlobal|Eval)\b\s*\(?\s*(%s)" % S).finditer(text), 4):
            t = _dso_unq(m.group(1), lang)
            if code_like(t):
                add("Execute / ExecuteGlobal / Eval (string literal)", t, False, "vbscript")
    return out


_DSO_CALLS = _dso_rx(r"(?i)\b(DownloadString|DownloadFile|DownloadData|Invoke-WebRequest|Invoke-RestMethod|Net\.WebClient|Start-BitsTransfer|bitsadmin|certutil|"
                     r"Invoke-Expression|IEX|Start-Process|Add-Type|VirtualAlloc|Reflection\.Assembly|AssemblyLoad|WScript\.Shell|Shell\.Application|ADODB\.Stream|"
                     r"XMLHTTP|ServerXMLHTTP|WinHttp\.WinHttpRequest|MSXML2|ActiveXObject|Scripting\.FileSystemObject|regsvr32|mshta|rundll32|schtasks|wmic|"
                     r"amsiInitFailed|AmsiUtils|-WindowStyle\s+Hidden|-ExecutionPolicy\s+Bypass|-NoProfile|powershell(?:\.exe)?|cmd(?:\.exe)?\s+/c)\b")
_DSO_STRONG = frozenset({"downloadstring", "downloadfile", "downloaddata", "invoke-webrequest", "invoke-restmethod", "net.webclient", "start-bitstransfer", "bitsadmin", "certutil",
                         "virtualalloc", "reflection.assembly", "assemblyload", "adodb.stream", "xmlhttp", "serverxmlhttp", "winhttp.winhttprequest", "amsiinitfailed", "amsiutils",
                         "regsvr32", "mshta", "rundll32", "wscript.shell", "shell.application"})


def _dso_looks_text(b: bytes) -> bool:
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return True
    s = bytes(b[:8192])
    if len(s) >= 8 and s[1::2].count(0) > 0.9 * (len(s) // 2):
        return True
    if not s or s.count(0):
        return False
    t = s.decode("utf-8", "ignore")
    ctl = sum(1 for c in t if ord(c) < 32 and c not in "\r\n\t")
    return len(t.encode("utf-8")) >= 0.97 * len(s) and ctl <= 0.02 * len(t)


def deobfuscate(data, lang: str | None = None) -> dict | None:
    """Deobfuscation statis satu skrip (bytes / str). -> dict {lang, layers, leaves, changed, calls, urls, truncated} atau None bila kosong.
    Tiap lapisan: {n, parent, via, lang, steps, kind, size, sha256, preview, text}. Tidak pernah menjalankan skrip."""
    deadline = time.monotonic() + DSO_TIME
    text = (data if isinstance(data, str) else _dso_to_text(data))[:DSO_MAX_TEXT]
    if not text.strip():
        return None
    nodes = [{"n": 0, "parent": -1, "via": "asli", "lang": _dso_lang(text, lang), "raw": text, "depth": 0, "binary": False, "kind": "teks"}]
    seen = {hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()}
    trunc, qi = False, 0
    while qi < len(nodes):
        nd = nodes[qi]
        qi += 1
        if nd["binary"]:
            continue
        if time.monotonic() > deadline:
            trunc = True
            nd["text"], nd["steps"] = nd["raw"], []
            continue
        nd["text"], nd["steps"] = _dso_inline(nd["raw"], nd["lang"], deadline)
        if nd["depth"] >= DSO_MAX_LAYERS:
            continue
        try:
            pays = _dso_payloads(nd["text"], nd["lang"], deadline)
        except (RecursionError, MemoryError):
            pays = []
        for via, pay, binary, plang in pays:
            if len(nodes) >= DSO_MAX_NODES:
                trunc = True
                break
            key = hashlib.sha256(pay if binary else pay.encode("utf-8", "ignore")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            ch = {"n": len(nodes), "parent": nd["n"], "via": via, "lang": plang, "depth": nd["depth"] + 1, "binary": binary}
            if binary:
                ch.update({"kind": _chain_label(pay) or "biner", "text": "", "steps": [], "size": len(pay), "sha": key})
            else:
                ch.update({"kind": "teks", "raw": pay[:DSO_MAX_TEXT]})
            nodes.append(ch)
    kids = {n["parent"] for n in nodes}
    layers = []
    for nd in nodes:
        t = nd.get("text", "")
        layers.append({"n": nd["n"], "parent": nd["parent"], "via": nd["via"], "lang": nd["lang"], "steps": nd.get("steps", []), "kind": nd["kind"],
                       "size": nd.get("size", len(t)), "sha256": nd.get("sha") or hashlib.sha256(t.encode("utf-8", "ignore")).hexdigest(), "preview": _clean(t[:200]), "text": t})
    leaves = [n["n"] for n in nodes if n["n"] not in kids]
    changed = len(nodes) > 1 or bool(nodes[0].get("steps")) and nodes[0]["text"] != nodes[0]["raw"]
    blob = "\n".join(n.get("text", "") for n in nodes)[:DSO_MAX_TEXT]
    calls = _uniq((m.group(1) for m in _DSO_CALLS.finditer(blob)), 12)
    urls = _uniq((u.rstrip(".,;)'\"") for u in _URL.findall(blob)), 10)
    return {"lang": nodes[0]["lang"], "layers": layers, "leaves": leaves, "changed": changed, "calls": calls, "urls": urls, "truncated": trunc}


def _dso_summary(r: dict) -> dict:
    """Bentuk ringkas untuk rep["deobf"] (JSON-aman, kecil)."""
    lv = [l for l in r["layers"] if l["n"] in r["leaves"]]
    return {"lang": r["lang"], "truncated": r["truncated"], "calls": r["calls"], "urls": r["urls"],
            "layers": [{k: l[k] for k in ("n", "parent", "via", "lang", "steps", "kind", "size", "sha256", "preview")} for l in r["layers"]],
            "leaves": r["leaves"], "final": [l["text"][:1500] for l in lv if l["text"]][:2]}


_DSO_OBF = frozenset({"backtick", "karakter", "indeks env", "base64 inline", "format -f", "replace / split", "join / balik / indeks", "alias iex"})
_DSO_TRIG = _dso_rx(r"(?i)frombase64string|\s-e(?:nc|ncodedcommand)?\s+[A-Za-z0-9+/]{16}|\biex\b|invoke-expression|fromcharcode|\beval\s*\(|unescape\s*\(|atob\s*\(|\[char\]|\bchrw?\s*\(|"
                    r"\bexecute(?:global)?\b|-join|\s-f\s*['\"]|\.replace\s*\(|`[A-Za-z]|-bxor|getstring|function\s*\(\s*p\s*,\s*a\s*,\s*c|\.split\s*\(")


def _dso_enrich(rep: dict, d, strs: list[str]) -> None:
    """Dipanggil dari _triage_open: kunci baru rep["deobf"] (None bila tidak ada hasil bermakna). Aditif; tidak pernah melempar."""
    rep["deobf"] = None
    try:
        srcs: list = []
        if len(d) <= DSO_MAX_TEXT * 2 and _dso_looks_text(d):
            srcs.append(d)
        else:
            srcs = [s for s in strs if len(s) >= 200 and _DSO_TRIG.search(s)][:3]
        for src in srcs:
            probe = src if isinstance(src, str) else _dso_to_text(src)
            if not _DSO_TRIG.search(probe[:DSO_MAX_TEXT]):
                continue
            head = probe[:200]
            if head.startswith("#!") and not re.search(r"(?i)pwsh|powershell|node|cscript|wscript", head.split("\n", 1)[0]):
                continue   # skrip shell / perl / python / ruby: bukan sasaran modul ini
            if max(_dso_lang_scores(probe[:200000]), key=lambda x: x[0])[0] < 2:
                continue
            if len(re.findall(r"(?m)^(?:import [\w.]+|from [\w.]+ import |def \w+\(.*\):|class \w+.*:)", probe[:60000])) >= 2:
                continue   # sumber Python
            r = deobfuscate(probe)
            if not r or not r["changed"]:
                continue
            obf = {s_ for l in r["layers"] for s_ in l["steps"]} & _DSO_OBF   # sambung string / variabel saja lazim di skrip sah
            strong = any(c.lower() in _DSO_STRONG for c in r["calls"])
            if len(r["layers"]) < 2 and not (len(obf) >= 2 or (obf and strong)):
                continue
            rep["deobf"] = _dso_summary(r)
            ind = rep["ind"]
            for u in r["urls"]:
                if u not in ind["urls"] and len(ind["urls"]) < 40:
                    ind["urls"].append(u)
            rep["warn"].append("skrip tersamar berhasil dibuka (%d lapisan, %s): %s" % (len(r["layers"]), r["lang"], " -> ".join(l["via"] for l in r["layers"][1:4]) or ", ".join(r["layers"][0]["steps"][:4])))
            return
    except Exception as e:
        rep["warn"].append("deobfuscation skrip gagal: %s" % type(e).__name__)


def _score_dso(rep: dict, add) -> None:
    x = rep.get("deobf")
    if not x:
        return
    strong = [c for c in x["calls"] if c.lower() in _DSO_STRONG]
    if strong:
        add(2, "isi skrip yang terbuka memuat pola unduh / eksekusi (%s)" % ", ".join(strong[:3]))
    elif len(x["layers"]) >= 3:
        add(1, "skrip dibungkus beberapa lapis (%d)" % len(x["layers"]))


def _render_dso(rep: dict, a, compact: bool, defang: bool) -> None:
    x = rep.get("deobf")
    if not x:
        return
    a("Deobfuscation skrip (%s, %d lapisan%s): %s" % (x["lang"], len(x["layers"]), ", TERPOTONG" if x["truncated"] else "",
                                                    " -> ".join(l["via"] + (" [%s]" % ", ".join(l["steps"][:3]) if l["steps"] else "") for l in x["layers"][:5])))
    if x["calls"]:
        a("   alat / pola di isi yang terbuka: %s" % ", ".join(_clean(c) for c in x["calls"][:(5 if compact else 12)]))
    for t in x["final"][:(1 if compact else 2)]:
        a("   hasil akhir: %s" % _df(_clean(t)[:(160 if compact else 360)], defang))


def deobf_text(path, defang: bool = True, full: bool = False) -> str:
    """Teks deobfuscation satu skrip. CLI --deobf, API action 'deobf'."""
    try:
        f, size = _open_regular(path)
        with f:
            data = f.read(DSO_MAX_TEXT * 2)
    except Exception as e:
        return "Deobfuscation gagal (%s: %s)." % (type(e).__name__, str(e)[:100])
    r = deobfuscate(data)
    if not r:
        return "Deobfuscation: berkas kosong."
    L_ = ["Deobfuscation skrip: %s | bahasa %s | %d lapisan%s" % (_clean(os.path.basename(os.fspath(path))), r["lang"], len(r["layers"]), " | TERPOTONG (batas waktu / lapisan)" if r["truncated"] else "")]
    if not r["changed"]:
        L_.append("Tidak ada lapisan penyamaran yang berhasil dibuka (bukan berarti bersih: pola di luar jangkauan, mis. string-array obfuscator.io, Script Encoder #@~^, AES / RC4).")
    for l in r["layers"]:
        if l["kind"] != "teks":
            L_.append(" [%d] <- [%d] %s: %s %s, sha256 %s..." % (l["n"], l["parent"], l["via"], l["kind"], _human(l["size"]), l["sha256"][:16]))
            continue
        L_.append(" [%d]%s %s (%s, %s)%s" % (l["n"], (" <- [%d]" % l["parent"]) if l["parent"] >= 0 else "", l["via"], l["lang"], _human(l["size"]),
                                            (" | transformasi: " + ", ".join(l["steps"])) if l["steps"] else ""))
        if l["n"] in r["leaves"] or full:
            body = l["text"] if full else l["text"][:1500]
            L_.append("     " + _df("\n     ".join(_clean(x) for x in body.splitlines()[:60]), defang) + ("   ..." if not full and len(l["text"]) > 1500 else ""))
    if r["calls"]:
        L_.append("Alat / pola: " + ", ".join(_clean(c) for c in r["calls"]))
    if r["urls"]:
        L_.append("URL: " + ", ".join(_df(_clean(u), defang) for u in r["urls"]))
    return "\n".join(L_)



# ----------------------- hash ikon PE -----------------------


def _icon_hash(d: bytes, pe: dict | None) -> dict | None:
    """MD5 data ikon terbesar + hash gabungan semua ikon: pengelompokan sampel yang memakai ikon sama (mis. ikon dokumen palsu)."""
    if not pe or pe.get("broken"):
        return None
    icons = [x for x in pe.get("res", []) if x.get("type") == "ICON" and x.get("size", 0) > 0]
    if not icons:
        return None
    hs = []
    for x in icons[:48]:
        blob = d[x["off"]:x["off"] + min(x["size"], 1 << 20)]
        if blob:
            hs.append((x["size"], hashlib.md5(blob).hexdigest()))
    if not hs:
        return None
    hs.sort(reverse=True)
    return {"main": hs[0][1], "all": hashlib.md5("".join(h for _s, h in sorted(hs, key=lambda t: t[1])).encode()).hexdigest(), "n": len(hs)}


# ----------------------- YARA opsional -----------------------


def yara_scan(path, rules, max_matches: int = 30) -> dict:
    """Jalankan aturan YARA milikmu (berkas .yar / .yara, atau folder berisi itu) pada berkas. Butuh `pip install yara-python`."""
    try:
        try:
            import yara
        except ImportError:
            return {"ok": False, "error": "pustaka opsional 'yara-python' belum terpasang (pip install yara-python)"}
        rp = Path(str(rules)).expanduser()
        if rp.is_dir():
            cand = sorted(x for x in rp.rglob("*") if x.suffix.lower() in (".yar", ".yara"))[:500]
            files = {"r%d" % i: str(p) for i, p in enumerate(cand)}
        elif rp.is_file():
            files = {"r0": str(rp)}
        else:
            return {"ok": False, "error": "berkas / folder aturan tidak ditemukan"}
        if not files:
            return {"ok": False, "error": "tidak ada berkas .yar / .yara di folder aturan"}
        f, size = _open_regular(path)
        f.close()
        rs = yara.compile(filepaths=files)
        ms = rs.match(filepath=str(Path(str(path)).resolve()), timeout=30)
        out = []
        for m in ms[:max_matches]:
            strs = []
            for sm in getattr(m, "strings", [])[:6]:
                ident = getattr(sm, "identifier", None) or (sm[1] if isinstance(sm, tuple) else "?")
                inst = getattr(sm, "instances", None)
                offs = [hex(i.offset) for i in inst[:3]] if inst else [hex(sm[0])] if isinstance(sm, tuple) else []
                strs.append("%s@%s" % (ident, ",".join(offs)))
            out.append({"rule": m.rule, "tags": list(m.tags), "desc": str(m.meta.get("description", ""))[:120], "strings": strs})
        return {"ok": True, "n_rules": len(files), "matches": out}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def yara_text(path, rules) -> str:
    r = yara_scan(path, rules)
    if not r["ok"]:
        return "YARA gagal: " + _clean(r["error"])
    if not r["matches"]:
        return "YARA: tidak ada aturan yang cocok (%d berkas aturan diperiksa)." % r["n_rules"]
    L = ["YARA: %d aturan cocok" % len(r["matches"])]
    for m in r["matches"]:
        L.append("   - %s%s%s%s" % (_clean(m["rule"]), (" [" + ",".join(m["tags"]) + "]") if m["tags"] else "",
                                    (" | " + _clean(m["desc"])) if m["desc"] else "", (" | " + ", ".join(m["strings"])) if m["strings"] else ""))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# v98.4: RE Lab untuk ELF x86 / x86-64 (little-endian). Memakai mesin RE Lab yang sama: peta panggilan API (PLT / GOT -> nama impor),
# nama fungsi dari .symtab / .dynsym bila ada, xref string, anti-analisis, peringkat fungsi. Statis, hanya pustaka standar.
# ---------------------------------------------------------------------------

_RE_GROUPS["injeksi proses"][0].update({"process_vm_writev", "process_vm_readv"})
_RE_GROUPS["jaringan / C2"][0].update({"bind", "listen", "accept", "sendto", "recvfrom", "inet_addr", "inet_pton", "curl_easy_perform", "curl_easy_setopt", "gethostbyaddr"})
_RE_GROUPS["eksekusi proses"][0].update({"execve", "execv", "execvp", "execl", "execlp", "execle", "popen", "posix_spawn", "posix_spawnp"})
_RE_GROUPS["kripto / enkripsi"][0].update({"evp_encryptinit_ex", "evp_cipherinit_ex", "evp_encryptupdate", "evp_decryptupdate", "aes_set_encrypt_key", "aes_encrypt", "aes_cbc_encrypt"})
_RE_GROUPS["enumerasi berkas"][0].update({"opendir", "readdir", "scandir", "ftw", "nftw", "glob"})
_RE_GROUPS["resolusi API dinamis"][0].update({"dlopen", "dlsym"})
_RE_GROUPS["alokasi / unpack memori"][0].update({"mmap", "mprotect", "mremap"})
_RE_GROUPS["token / hak istimewa"][0].update({"setuid", "setgid", "seteuid", "setresuid", "setresgid", "capset"})
_RE_GROUPS["anti-debug / anti-VM"][0].update({"ptrace", "prctl"})
_RE_GROUPS["ptrace (anti-debug / injeksi ELF)"] = ({"ptrace"}, 1, 3, "T1622 / T1055.008")
_RE_INTR = re.compile(_RE_INTR.pattern + r"|/bin/(?:ba|da|z)?sh\b|/etc/(?:passwd|shadow)|/proc/self|/dev/tcp|crontab|authorized_keys|ld_preload|\.ssh/|/tmp/\.", re.I)


def _elf_layout(d: bytes, arm: bool = False) -> dict | None:
    """Peta alamat ELF untuk RE Lab: segmen LOAD, bagian eksekusi, impor (slot GOT -> nama), simbol fungsi. None bila bukan x86 / x86-64 LE
    (arm=True: ARM 32-bit atau AArch64 LE; v99.22, menambah kunci arch / fmt / thumb)."""
    if len(d) < 64 or d[:4] != b"\x7fELF" or d[5] != 1 or d[4] not in (1, 2):
        return None
    is64 = d[4] == 2
    mach = struct.unpack_from("<H", d, 18)[0]
    if arm:
        if mach not in (40, 183) or (mach == 183) != is64:
            return None
    elif mach not in (3, 62) or (mach == 62) != is64:
        return None
    rel_ok = ((21, 22) if mach == 40 else (1025, 1026)) if arm else (6, 7)
    thumb: set[int] = set()
    try:
        if is64:
            entry, phoff, shoff = struct.unpack_from("<QQQ", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 54)
        else:
            entry, phoff, shoff = struct.unpack_from("<III", d, 24)
            phentsz, phnum, shentsz, shnum, shstr = struct.unpack_from("<HHHHH", d, 42)
        segs = []
        for i in range(min(phnum, 128)):
            o = phoff + i * phentsz
            if o + (56 if is64 else 32) > len(d):
                break
            if is64:
                pt, pf, poff, va, _pa, fsz, msz, _al = struct.unpack_from("<IIQQQQQQ", d, o)
            else:
                pt, poff, va, _pa, fsz, msz, pf, _al = struct.unpack_from("<IIIIIIII", d, o)
            if pt == 1 and msz:
                segs.append((va, poff, fsz, msz, pf))
        if not segs:
            return None
        base = min(x[0] for x in segs) & ~0xFFF
        size_img = max(x[0] + x[3] for x in segs) - base

        def r2o(rva):
            va = rva + base
            for sv, so, sf, _sm, _pf in segs:
                if sv <= va < sv + sf:
                    o = so + (va - sv)
                    return o if o < len(d) else None
            return None

        sh = []
        if shoff and shnum and shentsz >= (64 if is64 else 40):
            for i in range(min(shnum, 4096)):
                o = shoff + i * shentsz
                if o + (64 if is64 else 40) > len(d):
                    break
                v = struct.unpack_from("<IIQQQQIIQQ" if is64 else "<IIIIIIIIII", d, o)
                sh.append({"name": v[0], "type": v[1], "flags": v[2], "addr": v[3], "off": v[4], "size": v[5], "link": v[6], "info": v[7], "entsz": v[9]})

        def cstr(o, lim=200):
            if o is None or o >= len(d):
                return ""
            e = d.find(b"\0", o, o + lim)
            return d[o:(e if e != -1 else o + lim)].decode("latin-1", "replace")

        shs_off = sh[shstr]["off"] if shstr < len(sh) else 0
        for x in sh:
            x["nm"] = cstr(shs_off + x["name"], 64) if shs_off else ""

        def symtab(si):
            """(nama, nilai, ukuran, tipe, bind, shndx) untuk tabel simbol bagian ke-si."""
            t = sh[si]
            st = sh[t["link"]] if t["link"] < len(sh) else None
            esz = 24 if is64 else 16
            out = []
            if not st:
                return out
            for k in range(min(t["size"] // esz, 60000)):
                o = t["off"] + k * esz
                if o + esz > len(d):
                    break
                if is64:
                    nm, info, _ot, shndx, val, sz = struct.unpack_from("<IBBHQQ", d, o)
                else:
                    nm, val, sz, info, _ot, shndx = struct.unpack_from("<IIIBBH", d, o)
                out.append((cstr(st["off"] + nm), val, sz, info & 0xF, info >> 4, shndx))
            return out
        exports: dict[int, str] = {}
        symcache: dict[int, list] = {}
        for si, t in enumerate(sh):
            if t["type"] in (2, 11):
                symcache[si] = symtab(si)
                for nm, val, _sz, typ, _bd, shndx in symcache[si]:
                    if typ == 2 and shndx != 0 and val and nm and len(exports) < 30000:
                        if arm and mach == 40:
                            if val & 1:
                                thumb.add(val & ~1)   # simbol Thumb: bit 0 menandai mode, alamat sebenarnya genap
                            exports.setdefault(val & ~1, nm)
                        else:
                            exports.setdefault(val, nm)
        iat: dict[int, str] = {}
        for t in sh:
            if t["type"] not in (4, 9) or t["link"] not in symcache:
                continue
            rs = (24 if is64 else 12) if t["type"] == 4 else (16 if is64 else 8)
            syms = symcache[t["link"]]
            for k in range(min(t["size"] // rs, 40000)):
                o = t["off"] + k * rs
                if o + rs > len(d):
                    break
                if is64:
                    roff, rinfo = struct.unpack_from("<QQ", d, o)
                    rsym, rtyp = rinfo >> 32, rinfo & 0xFFFFFFFF
                else:
                    roff, rinfo = struct.unpack_from("<II", d, o)
                    rsym, rtyp = rinfo >> 8, rinfo & 0xFF
                if rtyp in rel_ok and 0 < rsym < len(syms):
                    nm, _v, _sz, _ty, _bd, shndx = syms[rsym]
                    nm = nm.split("@")[0]
                    if shndx == 0 and nm and not nm.startswith(("_ITM_", "__gmon_start__", "__libc_start_main", "__cxa_finalize", "__stack_chk", "__cxa_atexit")):
                        iat[roff] = nm
        secs, xsecs = [], []
        for x in sh:
            if x["flags"] & 2 and x["addr"] and x["size"]:
                rsz = 0 if x["type"] == 8 else x["size"]
                sec = {"name": x["nm"] or "?", "va": x["addr"] - base, "vsize": x["size"], "rsize": rsz, "rptr": x["off"],
                       "flags": ("R" if True else "-") + ("W" if x["flags"] & 1 else "-") + ("X" if x["flags"] & 4 else "-")}
                secs.append(sec)
                if x["flags"] & 4 and x["type"] == 1 and x["off"] < len(d):
                    xsecs.append(sec)
        if not xsecs:   # tanpa section header: pakai segmen LOAD yang dapat dieksekusi
            for sv, so, sf, sm, pf in segs:
                if pf & 1 and sf and so < len(d):
                    sec = {"name": "LOAD_X", "va": sv - base, "vsize": sm, "rsize": sf, "rptr": so, "flags": "R-X"}
                    secs.append(sec)
                    xsecs.append(sec)
        if not xsecs:
            return None
        return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "exports": exports, "r2o": r2o,
                "entry_va": entry if entry else 0, "entry_off": r2o(entry - base) if entry and entry >= base else None, "stripped": not any(t["type"] == 2 for t in sh),
                "arch": ("arm64" if mach == 183 else "arm") if arm else ("x64" if is64 else "x86"), "fmt": "ELF", "thumb": thumb, "stubs": {}}
    except (struct.error, IndexError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# v99.22 (roadmap v2, Tier A butir 4, tahap 1: peta alamat ARM / ARM64; aditif): _arm_layout() menghasilkan peta alamat untuk ELF ARM / AArch64 (LE)
# dan Mach-O ARM / ARM64 (tipis atau fat) dengan bentuk yang sama seperti _elf_layout (base, secs, xsecs, iat, exports, r2o, entry), ditambah
# arch ("arm" | "arm64"), fmt, thumb (alamat fungsi Thumb), stubs (alamat stub -> nama impor, Mach-O) dan encrypted (Mach-O, cryptid != 0).
# Murni stdlib, tidak memakai lief / capstone. Belum disambungkan ke _relab_any: decoder ARM menyusul di tahap berikut.
# ---------------------------------------------------------------------------
MACHO_ARM_CPU = {12: "arm", 0x0100000C: "arm64"}


def _macho_pick_slice(d: bytes) -> int | None:
    """Offset awal irisan Mach-O ARM / ARM64 (fat: arm64 diutamakan), atau None."""
    m = d[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"):
        n = struct.unpack_from(">I", d, 4)[0]
        if not 1 <= n <= 16:
            return None
        f64, best = m[3] == 0xBF, None
        esz = 32 if f64 else 20
        for i in range(n):
            p = 8 + i * esz
            if p + esz > len(d):
                break
            if f64:
                cpu, _s, off, _size, _a, _r = struct.unpack_from(">IIQQII", d, p)
            else:
                cpu, _s, off, _size, _a = struct.unpack_from(">IIIII", d, p)
            if cpu in MACHO_ARM_CPU and (best is None or cpu == 0x0100000C):
                best = off
        return best
    return 0 if m in (b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe") else None


def _macho_layout(d: bytes) -> dict | None:
    """Peta alamat Mach-O ARM / ARM64 little-endian untuk RE Lab. None bila bukan ARM / ARM64, rusak, atau tanpa bagian kode."""
    sb = _macho_pick_slice(d)
    if sb is None or sb + 32 > len(d):
        return None
    try:
        m = d[sb:sb + 4]
        is64 = m[0] == 0xCF
        hsz = 32 if is64 else 28
        cpu, _sub, _ft, ncmds, szcmds, _fl = struct.unpack_from("<IIIIII", d, sb + 4)
        arch = MACHO_ARM_CPU.get(cpu)
        if arch is None or (arch == "arm64") != is64:
            return None
        psz = 8 if is64 else 4
        segs, secs_raw = [], []
        symtab = dysym = None
        entry_off = pc = None
        encrypted = False
        text_va = None
        off, end = sb + hsz, min(len(d), sb + hsz + szcmds)
        for _ in range(min(ncmds, 600)):
            if off + 8 > end:
                break
            cmd, csz = struct.unpack_from("<II", d, off)
            if csz < 8 or off + csz > end:
                break
            if cmd in (0x1, 0x19):
                need, ssz = (72, 80) if cmd == 0x19 else (56, 68)
                if csz >= need:
                    if cmd == 0x19:
                        nm, va, vsz, fo, fsz, _mp, ip, ns, _fg = struct.unpack_from("<16sQQQQiiII", d, off + 8)
                    else:
                        nm, va, vsz, fo, fsz, _mp, ip, ns, _fg = struct.unpack_from("<16sIIIIiiII", d, off + 8)
                    segs.append((va, sb + fo, fsz, vsz, ip))
                    if nm.startswith(b"__TEXT") and fo == 0:
                        text_va = va
                    for i in range(min(ns, 256)):
                        p = off + need + i * ssz
                        if p + ssz > off + csz:
                            break
                        if is64:
                            sn, _sg, a, sz, so, _al, _ro, _nr, fl, r1, r2 = struct.unpack_from("<16s16sQQIIIIIII", d, p)
                        else:
                            sn, _sg, a, sz, so, _al, _ro, _nr, fl, r1, r2 = struct.unpack_from("<16s16sIIIIIIIII", d, p)
                        secs_raw.append({"nm": sn.split(b"\0")[0].decode("ascii", "replace"), "addr": a, "size": sz, "off": so, "fl": fl, "r1": r1, "r2": r2, "ip": ip})
            elif cmd == 0x2 and csz >= 24:
                symtab = struct.unpack_from("<IIII", d, off + 8)
            elif cmd == 0xB and csz >= 64:
                dysym = struct.unpack_from("<II", d, off + 8 + 48)   # indirectsymoff, nindirectsyms
            elif cmd == 0x80000028 and csz >= 16:
                entry_off = struct.unpack_from("<Q", d, off + 8)[0]
            elif cmd == 0x5 and csz >= 16:
                flav, cnt = struct.unpack_from("<II", d, off + 8)
                if arch == "arm64" and flav == 6 and csz >= 16 + 33 * 8:
                    pc = struct.unpack_from("<Q", d, off + 16 + 32 * 8)[0]
                elif arch == "arm" and flav == 1 and csz >= 16 + 16 * 4:
                    pc = struct.unpack_from("<I", d, off + 16 + 15 * 4)[0]
            elif cmd in (0x21, 0x2C) and csz >= 20:
                encrypted = struct.unpack_from("<I", d, off + 16)[0] != 0
            off += csz
        body = [x for x in segs if x[2]]
        if not body:
            return None
        base = text_va if text_va is not None else min(x[0] for x in body) & ~0xFFF
        size_img = max(x[0] + x[3] for x in body) - base

        def r2o(rva):
            va = rva + base
            for sv, so, sf, _sm, _ip in body:
                if sv <= va < sv + sf:
                    o = so + (va - sv)
                    return o if o < len(d) else None
            return None
        # tabel simbol
        syms: list[tuple[str, int, int, int, int]] = []   # (nama, n_type, n_sect, n_desc, n_value)
        if symtab:
            so_, ns, sto, stsz = symtab
            esz = 16 if is64 else 12
            for i in range(min(ns, 60000)):
                p = sb + so_ + i * esz
                if p + esz > len(d):
                    break
                if is64:
                    strx, nt, nsect, ndesc, nval = struct.unpack_from("<IBBHQ", d, p)
                else:
                    strx, nt, nsect, ndesc, nval = struct.unpack_from("<IBBHI", d, p)
                nm_ = _macho_cstr(d, sb + sto + strx, min(200, stsz - strx)) if strx < stsz else ""
                syms.append((nm_[1:] if nm_.startswith("_") else nm_, nt, nsect, ndesc, nval))
        indirect: list[int] = []
        if dysym:
            io, ni = dysym
            for i in range(min(ni, 100000)):
                p = sb + io + i * 4
                if p + 4 > len(d):
                    break
                indirect.append(struct.unpack_from("<I", d, p)[0])

        def ind_name(k):
            if 0 <= k < len(indirect):
                si = indirect[k]
                if si < len(syms) and si < 0x40000000:
                    return syms[si][0]
            return ""
        iat: dict[int, str] = {}
        stubs: dict[int, str] = {}
        secs, xsecs = [], []
        for x in secs_raw:
            typ = x["fl"] & 0xFF
            if typ in (6, 7) and x["size"]:                       # penunjuk simbol (GOT / la_symbol_ptr)
                for k in range(min(x["size"] // psz, 20000)):
                    nm_ = ind_name(x["r1"] + k)
                    if nm_:
                        iat[x["addr"] + k * psz] = nm_
            elif typ == 8 and x["r2"] and x["size"]:               # stub impor (__stubs)
                for k in range(min(x["size"] // x["r2"], 20000)):
                    nm_ = ind_name(x["r1"] + k)
                    if nm_:
                        stubs[x["addr"] + k * x["r2"]] = nm_
            zerofill = typ in (1, 0xC, 0x12)
            sec = {"name": x["nm"], "va": x["addr"] - base, "vsize": x["size"], "rsize": 0 if zerofill else x["size"], "rptr": sb + x["off"],
                   "flags": "R" + ("W" if x["ip"] & 2 else "-") + ("X" if x["ip"] & 4 else "-")}
            secs.append(sec)
            if x["fl"] & 0x80000400 and not zerofill and x["off"] and sb + x["off"] < len(d):
                xsecs.append(sec)
        if not xsecs:
            return None
        ranges = [(base + s_["va"], base + s_["va"] + s_["vsize"]) for s_ in xsecs]
        exports: dict[int, str] = {}
        thumb: set[int] = set()
        for nm_, nt, nsect, ndesc, nval in syms:
            if nt & 0xE0 or nt & 0x0E != 0x0E or not nm_ or not nsect:   # bukan simbol terdefinisi di section
                continue
            a = nval & ~1 if arch == "arm" else nval
            if any(lo <= a < hi for lo, hi in ranges) and len(exports) < 30000:
                if arch == "arm" and (ndesc & 0x8 or nval & 1):
                    thumb.add(a)
                exports.setdefault(a, nm_)
        ent = 0
        if entry_off is not None and text_va is not None:
            ent = text_va + entry_off
        elif pc:
            ent = pc & ~1 if arch == "arm" else pc
            if arch == "arm" and pc & 1:
                thumb.add(ent)
        return {"base": base, "is64": is64, "size_img": size_img, "secs": secs, "xsecs": xsecs, "iat": iat, "stubs": stubs, "exports": exports,
                "r2o": r2o, "entry_va": ent, "entry_off": r2o(ent - base) if ent and ent >= base else None, "stripped": not exports,
                "arch": arch, "fmt": "Mach-O", "thumb": thumb, "encrypted": encrypted}
    except (struct.error, IndexError, OverflowError):
        return None


def _arm_layout(d: bytes) -> dict | None:
    """Peta alamat untuk ELF ARM / AArch64 atau Mach-O ARM / ARM64 (LE). None bila format / arsitektur lain atau berkas rusak."""
    if d[:4] == b"\x7fELF":
        return _elf_layout(d, arm=True)
    return _macho_layout(d)


def _relab_elf(d: bytes, t0: float | None = None):
    L = _elf_layout(d)
    if L is None:
        return None, None
    info, ctx = _re_lab(d, None, t0, L=L, arch_label="ELF %s (%d-bit)%s" % ("x86-64" if L["is64"] else "x86", 64 if L["is64"] else 32, ", tanpa .symtab" if L["stripped"] else ""))
    if info is not None and L["stripped"]:
        info["notes"].append("ELF tanpa .symtab: nama fungsi hanya dari ekspor dinamis; sisanya sub_<alamat>")
    return info, ctx


def _relab_any(d: bytes, size: int):
    """(info, ctx, pesan_galat): PE x86 / x64 atau ELF x86 / x86-64."""
    pe = _parse_pe(d, size)
    if pe and not pe.get("broken"):
        info, ctx = _re_lab(d, pe)
        return info, ctx, "" if ctx else "PE bukan x86 / x64 atau tanpa bagian eksekusi"
    if d[:4] == b"\x7fELF":
        info, ctx = _relab_elf(d)
        return info, ctx, "" if ctx else "ELF bukan x86 / x86-64 little-endian, atau tanpa kode yang bisa dianalisis"
    return None, None, "bukan PE / ELF x86 / x64 yang valid"


# ----------------------------- API JSON untuk Iris / Hermes -----------------

# ---------------------------------------------------------------------------
# v99.14 (OPSIONAL dan ADITIF; triase, skor, dan keluaran di atas TIDAK berubah). Tiga kemampuan yang sebelumnya tidak ada:
#   1. sig_check(path, online=False): pemeriksaan tanda tangan Authenticode PENUH: tanda tangan PKCS#7 diverifikasi dengan kunci sertifikat
#      penanda, messageDigest, hash isi berkas, rantai sertifikat (tiap tautan diverifikasi kriptografis), akar di penyimpanan tepercaya,
#      masa berlaku, EKU code signing, dan (hanya bila online=True) pencabutan lewat CRL. Butuh paket `cryptography`; tanpa itu hanya
#      pemeriksaan integritas hash yang berjalan.
#      Penyimpanan akar: env REA_CA_BUNDLE (berkas PEM) > penyimpanan ROOT Windows (ssl.enum_certificates) > tidak ada. Sengaja TIDAK memakai
#      certifi: itu akar TLS Mozilla, bukan akar code signing Microsoft, jadi hasilnya menyesatkan.
#      Cap waktu (countersignature) hanya dideteksi keberadaannya, TIDAK diverifikasi.
#   2. reputation(target, online=False): reputasi hash di VirusTotal (env REA_VT_KEY). Yang dikirim HANYA hash SHA-256, tidak pernah berkas.
#   3. unpack_7z(path, outdir): membongkar kemasan yang dipahami 7-Zip (NSIS, SFX 7-Zip, dan lain-lain) lewat alat `7zz` / `7z` / `7za` / `7zr`
#      dengan pembatasan sumber daya; hanya berkas biasa yang disalin keluar (tautan simbolik dan berkas khusus dibuang).
# Akses jaringan (CRL, VirusTotal) selalu opt-in: CLI butuh --online; lewat API butuh "online": true DAN env REA_ONLINE=1 yang diatur operator,
# supaya agen tidak bisa menyalakannya sendiri. URL CRL berasal dari berkas yang dianalisis (tidak tepercaya): hanya http, alamat harus publik,
# tanpa pengalihan, ukuran dibatasi.
# ---------------------------------------------------------------------------

_OID_NAMES = {"1.2.840.113549.1.7.2": "signedData", "1.2.840.113549.1.9.4": "messageDigest", "1.2.840.113549.1.9.6": "counterSignature",
              "1.3.6.1.4.1.311.3.3.1": "msTimestamp", "1.3.6.1.5.5.7.3.3": "codeSigning"}
_SIG_HASH = {"1.2.840.113549.2.5": "md5", "1.3.14.3.2.26": "sha1", "2.16.840.1.101.3.4.2.1": "sha256", "2.16.840.1.101.3.4.2.2": "sha384",
             "2.16.840.1.101.3.4.2.3": "sha512"}
_SIG_RSA = {"1.2.840.113549.1.1.1": None, "1.2.840.113549.1.1.5": "sha1", "1.2.840.113549.1.1.11": "sha256", "1.2.840.113549.1.1.12": "sha384",
            "1.2.840.113549.1.1.13": "sha512"}
_SIG_EC = {"1.2.840.10045.4.1": "sha1", "1.2.840.10045.4.3.2": "sha256", "1.2.840.10045.4.3.3": "sha384", "1.2.840.10045.4.3.4": "sha512"}
SIG_MAX_FILE = 256 * 1024 * 1024
_REV_MAX_FETCH = 4


def _der_tlv(b: bytes, pos: int) -> tuple[int, int, int]:
    """(tag, awal_isi, akhir) elemen DER di pos. ValueError bila tak sah / keluar batas."""
    if pos < 0 or pos + 2 > len(b):
        raise ValueError("DER terpotong")
    tag, ln, p = b[pos], b[pos + 1], pos + 2
    if ln & 0x80:
        n = ln & 0x7F
        if n == 0 or n > 4 or p + n > len(b):
            raise ValueError("panjang DER tidak sah")
        ln, p = int.from_bytes(b[p:p + n], "big"), p + n
    if p + ln > len(b):
        raise ValueError("elemen DER keluar batas")
    return tag, p, p + ln


def _der_kids(b: bytes, start: int, end: int) -> list[tuple[int, int, int, int]]:
    """Anak-anak elemen: [(tag, awal_elemen, awal_isi, akhir)]."""
    out, pos = [], start
    while pos < end:
        tag, vs, ve = _der_tlv(b, pos)
        if ve > end:
            raise ValueError("anak DER keluar batas")
        out.append((tag, pos, vs, ve))
        pos = ve
        if len(out) > 1024:
            raise ValueError("terlalu banyak elemen DER")
    return out


def _der_oid(b: bytes, vs: int, ve: int) -> str:
    raw = b[vs:ve]
    if not raw:
        return ""
    parts = [str(raw[0] // 40), str(raw[0] % 40)]
    v = 0
    for x in raw[1:]:
        v = (v << 7) | (x & 0x7F)
        if not x & 0x80:
            parts.append(str(v))
            v = 0
    return ".".join(parts)


def _p7_parse(blob: bytes) -> dict:
    """Urai PKCS#7 / CMS SignedData: sertifikat (DER mentah), konten, dan SignerInfo. ValueError bila bukan SignedData yang utuh."""
    tag, vs, ve = _der_tlv(blob, 0)
    if tag != 0x30:
        raise ValueError("bukan SEQUENCE")
    top = _der_kids(blob, vs, ve)
    if len(top) < 2 or top[0][0] != 0x06 or _der_oid(blob, top[0][2], top[0][3]) != "1.2.840.113549.1.7.2" or top[1][0] != 0xA0:
        raise ValueError("bukan ContentInfo signedData")
    sd = _der_kids(blob, top[1][2], top[1][3])
    if not sd or sd[0][0] != 0x30:
        raise ValueError("SignedData tidak ada")
    parts = _der_kids(blob, sd[0][2], sd[0][3])
    if len(parts) < 4:
        raise ValueError("SignedData terlalu pendek")
    out: dict = {"certs": [], "content": None, "signers": []}
    enc = _der_kids(blob, parts[2][2], parts[2][3])          # EncapsulatedContentInfo
    if len(enc) > 1 and enc[1][0] == 0xA0:
        inner = _der_kids(blob, enc[1][2], enc[1][3])
        if inner:
            out["content"] = bytes(blob[inner[0][2]:inner[0][3]])   # NILAI elemen (tanpa tag + panjang), dasar messageDigest
    for t, off, vs2, ve2 in parts[3:]:
        if t == 0xA0:
            for ct, coff, _cvs, cve in _der_kids(blob, vs2, ve2):
                if ct == 0x30 and len(out["certs"]) < 32:
                    out["certs"].append(bytes(blob[coff:cve]))
    si_set = parts[-1]
    if si_set[0] != 0x31:
        raise ValueError("SignerInfos tidak ada")
    for st, soff, svs, sve in _der_kids(blob, si_set[2], si_set[3])[:4]:
        if st != 0x30:
            continue
        k = _der_kids(blob, svs, sve)
        if len(k) < 5:
            continue
        si: dict = {"issuer": None, "serial": None, "digest_oid": "", "attrs": None, "attrs_raw": None, "sig_oid": "", "sig": b"", "unsigned": False}
        sid = k[1]
        if sid[0] == 0x30:
            sk = _der_kids(blob, sid[2], sid[3])
            if len(sk) >= 2:
                si["issuer"] = bytes(blob[sk[0][1]:sk[0][3]])
                si["serial"] = int.from_bytes(blob[sk[1][2]:sk[1][3]], "big", signed=True)
        dk = _der_kids(blob, k[2][2], k[2][3])
        si["digest_oid"] = _der_oid(blob, dk[0][2], dk[0][3]) if dk else ""
        i = 3
        if k[i][0] == 0xA0:
            si["attrs_raw"] = bytes([0x31]) + bytes(blob[k[i][1] + 1:k[i][3]])     # SET OF: tag 0xA0 diganti 0x31 untuk verifikasi
            si["attrs"] = _der_kids(blob, k[i][2], k[i][3])
            si["_blob"] = blob
            i += 1
        sk2 = _der_kids(blob, k[i][2], k[i][3])
        si["sig_oid"] = _der_oid(blob, sk2[0][2], sk2[0][3]) if sk2 else ""
        if i + 1 < len(k) and k[i + 1][0] == 0x04:
            si["sig"] = bytes(blob[k[i + 1][2]:k[i + 1][3]])
        si["unsigned"] = any(x[0] == 0xA1 for x in k[i + 2:])
        out["signers"].append(si)
    return out


def _si_message_digest(si: dict) -> bytes | None:
    blob = si.get("_blob")
    for _t, off, vs, ve in si.get("attrs") or []:
        kids = _der_kids(blob, vs, ve)
        if len(kids) >= 2 and _der_oid(blob, kids[0][2], kids[0][3]) == "1.2.840.113549.1.9.4":
            vals = _der_kids(blob, kids[1][2], kids[1][3])
            if vals and vals[0][0] == 0x04:
                return bytes(blob[vals[0][2]:vals[0][3]])
    return None


def _si_has_timestamp(si: dict) -> bool:
    return bool(si.get("unsigned"))


def _trust_store() -> tuple[list, str]:
    """(daftar sertifikat akar, sumber). REA_CA_BUNDLE (PEM) > ROOT Windows > kosong. Tidak pernah memakai certifi (akar TLS, bukan code signing)."""
    from cryptography import x509
    p = os.environ.get("REA_CA_BUNDLE", "").strip()
    if p:
        try:
            with open(p, "rb") as fh:
                pem = fh.read(8 * 1024 * 1024)
            return list(x509.load_pem_x509_certificates(pem)), "REA_CA_BUNDLE"
        except Exception as e:
            return [], "REA_CA_BUNDLE gagal dibaca (%s)" % type(e).__name__
    try:
        import ssl
        out = []
        for der, enc, trust in ssl.enum_certificates("ROOT"):     # hanya ada di Windows
            if enc != "x509_asn" or (trust is not True and "1.3.6.1.5.5.7.3.3" not in (trust or ())):
                continue
            try:
                out.append(x509.load_der_x509_certificate(der))
            except Exception:
                continue
        return out, "penyimpanan ROOT Windows"
    except (AttributeError, ImportError, OSError):
        return [], "tidak ada"


def _cert_dates(c):
    nb = getattr(c, "not_valid_before_utc", None) or c.not_valid_before.replace(tzinfo=_dt.timezone.utc)
    na = getattr(c, "not_valid_after_utc", None) or c.not_valid_after.replace(tzinfo=_dt.timezone.utc)
    return nb, na


def _cn(name) -> str:
    try:
        from cryptography.x509.oid import NameOID
        v = name.get_attributes_for_oid(NameOID.COMMON_NAME)
        if v:
            return _clean(str(v[0].value))[:80]
        v = name.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        return _clean(str(v[0].value))[:80] if v else _clean(name.rfc4514_string())[:80]
    except Exception:
        return "?"


def _issued_by(cert, issuer) -> bool:
    try:
        cert.verify_directly_issued_by(issuer)
        return True
    except Exception:
        return False


def _rev_fetch(url: str, timeout: int = 8, cap: int = 8 * 1024 * 1024) -> bytes:
    """Ambil CRL. URL berasal dari berkas yang dianalisis (TIDAK tepercaya): hanya http, semua alamat hasil DNS harus publik (anti-SSRF),
    koneksi langsung ke IP itu (anti DNS-rebinding), tanpa pengalihan, ukuran dibatasi."""
    import http.client
    import ipaddress
    import socket
    from urllib.parse import urlsplit
    u = urlsplit(url)
    if u.scheme != "http" or not u.hostname:
        raise ValueError("hanya URL http")
    port = u.port or 80
    addrs = [i[4][0] for i in socket.getaddrinfo(u.hostname, port, type=socket.SOCK_STREAM)]
    if not addrs or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addrs):
        raise ValueError("alamat tujuan bukan alamat publik")
    conn = http.client.HTTPConnection(addrs[0], port, timeout=timeout)
    try:
        conn.request("GET", (u.path or "/") + (("?" + u.query) if u.query else ""), headers={"Host": u.netloc, "User-Agent": "rea-triage", "Accept": "*/*"})
        r = conn.getresponse()
        if r.status != 200:
            raise ValueError("HTTP %d" % r.status)
        data = r.read(cap + 1)
    finally:
        conn.close()
    if len(data) > cap:
        raise ValueError("CRL terlalu besar")
    return data


def _revocation(chain: list) -> dict:
    """Cek pencabutan tiap sertifikat non-akar lewat CRL penerbitnya. Hasil per sertifikat: 'dicabut' / 'tidak dicabut' / 'tidak diketahui'."""
    from cryptography import x509
    res: list[dict] = []
    fetched = 0
    for i, c in enumerate(chain[:-1] if len(chain) > 1 else chain):
        item = {"subject": _cn(c.subject), "status": "tidak diketahui", "why": ""}
        res.append(item)
        issuer = chain[i + 1] if i + 1 < len(chain) else None
        try:
            dps = c.extensions.get_extension_for_class(x509.CRLDistributionPoints).value
        except Exception:
            item["why"] = "tidak ada CRL distribution point"
            continue
        urls = [g.value for dp in dps for g in (dp.full_name or []) if isinstance(g, x509.UniformResourceIdentifier) and g.value.lower().startswith("http://")]
        if not urls or issuer is None:
            item["why"] = "tidak ada URL CRL http" if not urls else "penerbit tidak ada di rantai"
            continue
        if fetched >= _REV_MAX_FETCH:
            item["why"] = "batas jumlah pengambilan CRL tercapai"
            continue
        fetched += 1
        try:
            data = _rev_fetch(urls[0])
            crl = x509.load_pem_x509_crl(data) if data.lstrip()[:5] == b"-----" else x509.load_der_x509_crl(data)
            if not crl.is_signature_valid(issuer.public_key()):
                item["why"] = "tanda tangan CRL tidak cocok dengan penerbit"
                continue
            nu = getattr(crl, "next_update_utc", None) or (crl.next_update.replace(tzinfo=_dt.timezone.utc) if crl.next_update else None)
            hit = crl.get_revoked_certificate_by_serial_number(c.serial_number)
            if hit is not None:
                item["status"], item["why"] = "dicabut", "ada di CRL"
            else:
                item["status"] = "tidak dicabut"
                item["why"] = "tidak ada di CRL" + (" (CRL sudah kedaluwarsa)" if nu and nu < _dt.datetime.now(_dt.timezone.utc) else "")
        except Exception as e:
            item["why"] = "CRL gagal diambil / dibaca: %s" % _clean(str(e))[:80]
    return {"checked": res, "revoked": any(x["status"] == "dicabut" for x in res), "all_known": bool(res) and all(x["status"] != "tidak diketahui" for x in res)}


def _verify_signer(si: dict, content: bytes | None, certs: list) -> dict:
    """Verifikasi satu SignerInfo: cocokkan sertifikat penanda, messageDigest vs hash konten, lalu tanda tangan atas signedAttrs."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
    r: dict = {"cert": None, "sig_ok": None, "digest_ok": None, "alg": "", "weak": False, "error": ""}
    cert = None
    for c in certs:
        if si.get("serial") is not None and c.serial_number == si["serial"] and (si.get("issuer") is None or c.issuer.public_bytes() == si["issuer"]):
            cert = c
            break
    if cert is None:
        cert = next((c for c in certs if si.get("serial") is not None and c.serial_number == si["serial"]), None)
    if cert is None:
        r["error"] = "sertifikat penanda tidak ada di tanda tangan"
        return r
    r["cert"] = cert
    hname = _SIG_HASH.get(si["digest_oid"]) or _SIG_RSA.get(si["sig_oid"]) or _SIG_EC.get(si["sig_oid"])
    if hname not in ("md5", "sha1", "sha256", "sha384", "sha512"):
        r["error"] = "algoritma hash tidak dikenal (%s)" % (si["digest_oid"] or "?")
        return r
    r["alg"], r["weak"] = hname, hname in ("md5", "sha1")
    hobj = {"md5": hashes.MD5, "sha1": hashes.SHA1, "sha256": hashes.SHA256, "sha384": hashes.SHA384, "sha512": hashes.SHA512}[hname]()
    if si.get("attrs_raw") is not None:
        md = _si_message_digest(si)
        if content is not None and md is not None:
            r["digest_ok"] = hashlib.new(hname, content).digest() == md
        signed = si["attrs_raw"]
    else:
        signed = content
        if signed is None:
            r["error"] = "tidak ada signedAttrs dan konten tidak tertanam"
            return r
    try:
        pub = cert.public_key()
        if isinstance(pub, rsa.RSAPublicKey) and si["sig_oid"] in _SIG_RSA:
            pub.verify(si["sig"], signed, padding.PKCS1v15(), hobj)
            r["sig_ok"] = True
        elif isinstance(pub, ec.EllipticCurvePublicKey) and si["sig_oid"] in _SIG_EC:
            pub.verify(si["sig"], signed, ec.ECDSA(hobj))
            r["sig_ok"] = True
        else:
            r["error"] = "jenis tanda tangan tidak didukung (%s)" % (si["sig_oid"] or "?")
    except Exception as e:
        r["sig_ok"] = False
        r["error"] = "tanda tangan tidak cocok (%s)" % type(e).__name__
    return r


def sig_check(path, online: bool = False) -> dict:
    """Pemeriksaan tanda tangan Authenticode penuh. Tidak pernah melempar. Lihat komentar v99.14 untuk cakupan dan batasannya."""
    try:
        f, size = _open_regular(path)
        with f:
            d = f.read(min(size, SIG_MAX_FILE))
        pe = _parse_pe(d, size) if d[:2] == b"MZ" else None
        if not pe or pe.get("broken"):
            return {"ok": False, "error": "bukan PE yang bisa diurai"}
        if not pe.get("signed"):
            return {"ok": False, "error": "berkas tidak memiliki tanda tangan Authenticode"}
        out: dict = {"ok": True, "name": Path(str(path)).name, "notes": [], "signatures": [], "online": bool(online), "crypto": True}
        integ = _authenticode_check(d, size, pe) if len(d) == size else None
        out["file_hash"] = integ
        if len(d) != size:
            out["notes"].append("berkas lebih besar dari %d MB: hash isi tidak dihitung ulang" % (SIG_MAX_FILE >> 20))
        try:
            import cryptography  # noqa: F401
            from cryptography import x509
        except ImportError:
            out["crypto"] = False
            out["verdict"] = "TIDAK LENGKAP: paket 'cryptography' tidak terpasang (pip install cryptography); hanya integritas hash isi berkas yang diperiksa"
            return out
        pe_off = struct.unpack_from("<I", d, 0x3C)[0]
        o = pe_off + 24
        is64 = struct.unpack_from("<H", d, o)[0] == 0x20B
        c_off, c_sz = struct.unpack_from("<II", d, o + (112 if is64 else 96) + 32)
        end, pos, blobs = min(c_off + c_sz, len(d)), c_off, []
        while pos + 8 <= end and len(blobs) < 4:
            dw, _rev, typ = struct.unpack_from("<IHH", d, pos)
            if dw < 8 or pos + dw > end:
                break
            if typ == 2:
                blobs.append(bytes(d[pos + 8:pos + dw]))
            pos += (dw + 7) & ~7
        if not blobs:
            out["ok"] = False
            out["error"] = "tabel sertifikat tidak berisi blob PKCS#7"
            return out
        store, src = _trust_store()
        out["trust_source"] = src
        now = _dt.datetime.now(_dt.timezone.utc)
        for blob in blobs:
            try:
                p7 = _p7_parse(blob)
            except ValueError as e:
                out["signatures"].append({"error": "PKCS#7 tidak terbaca: %s" % _clean(str(e))[:80]})
                continue
            certs = []
            for raw in p7["certs"]:
                try:
                    certs.append(x509.load_der_x509_certificate(raw))
                except Exception:
                    continue
            for si in p7["signers"]:
                v = _verify_signer(si, p7["content"], certs)
                sig: dict = {"alg": v["alg"], "weak_hash": v["weak"], "sig_ok": v["sig_ok"], "digest_ok": v["digest_ok"], "error": v["error"],
                             "timestamp": _si_has_timestamp(si), "chain": [], "links_ok": None, "trusted": None, "root": "", "eku_code_signing": None,
                             "expired": None, "revocation": None}
                leaf = v["cert"]
                if leaf is not None:
                    chain, seen = [leaf], {leaf.fingerprint(hashes_sha256())}
                    cur = leaf
                    for _ in range(8):
                        if _issued_by(cur, cur):
                            break
                        nxt = next((c for c in certs if c.fingerprint(hashes_sha256()) not in seen and _issued_by(cur, c)), None)
                        if nxt is None:
                            nxt = next((c for c in store if c.fingerprint(hashes_sha256()) not in seen and _issued_by(cur, c)), None)
                        if nxt is None:
                            break
                        chain.append(nxt)
                        seen.add(nxt.fingerprint(hashes_sha256()))
                        cur = nxt
                    top = chain[-1]
                    self_issued = _issued_by(top, top)
                    sig["links_ok"] = self_issued or len(chain) > 1
                    sig["complete"] = self_issued
                    fp = top.fingerprint(hashes_sha256())
                    if store:
                        sig["trusted"] = bool(self_issued and any(c.fingerprint(hashes_sha256()) == fp for c in store)) or bool(
                            not self_issued and any(_issued_by(top, c) for c in store))
                    sig["root"] = _cn(top.subject)
                    for c in chain:
                        nb, na = _cert_dates(c)
                        sig["chain"].append({"subject": _cn(c.subject), "issuer": _cn(c.issuer), "not_before": nb.strftime("%Y-%m-%d"),
                                             "not_after": na.strftime("%Y-%m-%d"), "alg": getattr(getattr(c, "signature_hash_algorithm", None), "name", "?")})
                    nb, na = _cert_dates(leaf)
                    sig["expired"] = not (nb <= now <= na)
                    try:
                        from cryptography.x509.oid import ExtendedKeyUsageOID
                        eku = leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
                        sig["eku_code_signing"] = ExtendedKeyUsageOID.CODE_SIGNING in eku
                    except Exception:
                        sig["eku_code_signing"] = False
                    if online:
                        sig["revocation"] = _revocation(chain)
                out["signatures"].append(sig)
        out["verdict"] = _sig_verdict(out, bool(store))
        return out
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:120])}


def hashes_sha256():
    from cryptography.hazmat.primitives import hashes
    return hashes.SHA256()


def _sig_verdict(out: dict, have_store: bool) -> str:
    sigs = [s for s in out["signatures"] if "alg" in s]
    if not sigs:
        return "TIDAK VALID: tanda tangan tidak bisa diurai"
    fh = out.get("file_hash")
    bad: list[str] = []
    soft: list[str] = []
    incomplete: list[str] = []      # hal yang HARUS terbukti agar boleh disebut VALID, tetapi tidak bisa dipastikan
    s = sigs[0]
    if s.get("sig_ok") is not True:
        bad.append("tanda tangan PKCS#7 tidak terverifikasi (%s)" % (s.get("error") or "gagal"))
    if s.get("digest_ok") is False:
        bad.append("messageDigest tidak cocok dengan konten yang ditandatangani")
    elif s.get("digest_ok") is None:
        incomplete.append("messageDigest tidak bisa diperiksa")
    if fh is None:
        incomplete.append("hash isi berkas tidak bisa dibandingkan dengan digest yang ditandatangani (berkas terlalu besar, tabel section janggal, atau digest tidak terbaca)")
    elif not fh.get("match"):
        bad.append("isi berkas berubah setelah ditandatangani (hash tidak cocok)")
    if s.get("links_ok") is False:
        bad.append("rantai sertifikat tidak tersambung")
    elif s.get("links_ok") and not s.get("complete"):
        soft.append("rantai tidak sampai akar (penerbit tidak ditemukan di tanda tangan maupun penyimpanan)")
    if not have_store:
        incomplete.append("akar tepercaya tidak bisa diverifikasi (set REA_CA_BUNDLE, atau jalankan di Windows); tanpa itu sertifikat buatan sendiri juga tampak sah")
    elif s.get("trusted") is False:
        bad.append("akar rantai TIDAK ada di penyimpanan tepercaya")
    if s.get("eku_code_signing") is False:
        bad.append("sertifikat penanda tidak punya EKU code signing")
    if s.get("expired"):
        (soft if s.get("timestamp") else bad).append("sertifikat penanda di luar masa berlaku" + (" (ada cap waktu; cap waktu tidak diverifikasi)" if s.get("timestamp") else ""))
    if s.get("weak_hash"):
        soft.append("hash lemah (%s)" % s.get("alg"))
    rv = s.get("revocation")
    if rv is None:
        soft.append("pencabutan tidak diperiksa (butuh --online)")
    elif rv.get("revoked"):
        bad.append("sertifikat DICABUT menurut CRL")
    elif not rv.get("all_known"):
        soft.append("status pencabutan sebagian tidak diketahui")
    if bad:
        return "TIDAK VALID: " + "; ".join(bad)
    if incomplete:
        return "TIDAK LENGKAP (belum bisa disebut valid): " + "; ".join(incomplete + soft)
    return "VALID secara kriptografis" + (" (dengan catatan: " + "; ".join(soft) + ")" if soft else "")


def sig_text(path, online: bool = False) -> str:
    r = sig_check(path, online=online)
    if not r.get("ok"):
        return "TANDA TANGAN: " + r.get("error", "gagal")
    L = ["TANDA TANGAN (v99.14) %s" % r["name"], "Putusan: %s" % r["verdict"]]
    fh = r.get("file_hash")
    if fh:
        L.append("Hash isi berkas: %s (%s)" % ("COCOK" if fh["match"] else "TIDAK COCOK", fh["alg"]))
    L.append("Akar tepercaya: %s" % r.get("trust_source", "?"))
    for i, s in enumerate(r["signatures"], 1):
        if "alg" not in s:
            L.append("Tanda tangan %d: %s" % (i, s.get("error", "?")))
            continue
        L.append("Tanda tangan %d: PKCS#7 %s | messageDigest %s | hash %s%s | cap waktu: %s" % (
            i, {True: "sah", False: "GAGAL", None: "tak diperiksa"}[s["sig_ok"]], {True: "cocok", False: "TIDAK cocok", None: "tak diperiksa"}[s["digest_ok"]],
            s["alg"] or "?", " (lemah)" if s["weak_hash"] else "", "ada (tidak diverifikasi)" if s["timestamp"] else "tidak ada"))
        for j, c in enumerate(s["chain"]):
            L.append("   %s%s  <- %s  [%s s/d %s]" % ("  " * j, c["subject"], c["issuer"], c["not_before"], c["not_after"]))
        if s["chain"]:
            L.append("   Akar: %s | tersambung: %s | di penyimpanan: %s | EKU code signing: %s" % (
                s["root"], {True: "ya", False: "TIDAK", None: "?"}[s["links_ok"]], {True: "ya", False: "TIDAK", None: "tak diperiksa"}[s["trusted"]],
                {True: "ya", False: "TIDAK", None: "?"}[s["eku_code_signing"]]))
        if s.get("revocation"):
            for x in s["revocation"]["checked"]:
                L.append("   Pencabutan %s: %s (%s)" % (x["subject"], x["status"], x["why"]))
    for n in r.get("notes", []):
        L.append("Catatan: " + n)
    L.append("Batas: cap waktu tidak diverifikasi; kebijakan Windows (WinVerifyTrust, kebijakan penerbit, daftar cabut khusus) tidak ditiru.")
    return "\n".join(L)


# --- reputasi hash (VirusTotal) ---------------------------------------------------------------------------------------------------------

def _http_get(url: str, headers: dict, timeout: int = 10, cap: int = 1024 * 1024) -> tuple[int, bytes]:
    """GET HTTPS tanpa mengikuti pengalihan. (status, isi). Dipisah supaya bisa diganti saat uji."""
    from urllib.error import HTTPError
    from urllib.request import HTTPRedirectHandler, Request, build_opener

    class _NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        with build_opener(_NoRedirect).open(Request(url, headers=headers), timeout=timeout) as r:
            return r.status, r.read(cap + 1)[:cap]
    except HTTPError as e:
        return e.code, b""


def reputation(target, online: bool = False) -> dict:
    """Reputasi SHA-256 di VirusTotal. target: hash 64 hex atau path berkas. Hanya hash yang dikirim. 'tidak dikenal' BUKAN bukti aman."""
    try:
        t = str(target).strip()
        h = t.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", t) else triage(t)["sha256"]
        if not online:
            return {"ok": False, "sha256": h, "error": "mode online belum diaktifkan (CLI: --online; API: \"online\": true dan env REA_ONLINE=1)"}
        key = os.environ.get("REA_VT_KEY", "").strip()
        if not key:
            return {"ok": False, "sha256": h, "error": "env REA_VT_KEY belum diisi"}
        code, body = _http_get("https://www.virustotal.com/api/v3/files/" + h, {"x-apikey": key, "accept": "application/json"})
        if code == 404:
            return {"ok": True, "sha256": h, "known": False}
        if code != 200:
            return {"ok": False, "sha256": h, "error": "VirusTotal membalas HTTP %d" % code}
        a = (json.loads(body.decode("utf-8", "replace")).get("data") or {}).get("attributes") or {}
        st = a.get("last_analysis_stats") or {}
        ptc = (a.get("popular_threat_classification") or {}).get("suggested_threat_label")
        return {"ok": True, "sha256": h, "known": True, "malicious": int(st.get("malicious", 0)), "suspicious": int(st.get("suspicious", 0)),
                "harmless": int(st.get("harmless", 0)), "undetected": int(st.get("undetected", 0)),
                "name": _clean(str(a.get("meaningful_name") or ""))[:80], "label": _clean(str(ptc or ""))[:60],
                "last_analysis": a.get("last_analysis_date") if isinstance(a.get("last_analysis_date"), int) else None}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:100])}


def reputation_text(target, online: bool = False) -> str:
    r = reputation(target, online=online)
    if not r.get("ok"):
        return "REPUTASI: %s%s" % (r.get("error", "gagal"), (" (sha256 %s)" % r["sha256"]) if r.get("sha256") else "")
    if not r["known"]:
        return "REPUTASI VirusTotal: hash %s tidak dikenal. Ini BUKAN bukti berkas aman (bisa sampel baru / tidak pernah diunggah)." % r["sha256"]
    tot = r["malicious"] + r["suspicious"] + r["harmless"] + r["undetected"]
    when = _dt.datetime.fromtimestamp(r["last_analysis"], _dt.timezone.utc).strftime("%Y-%m-%d") if r.get("last_analysis") else "?"
    return ("REPUTASI VirusTotal (sha256 %s): %d jahat, %d mencurigakan, %d tidak terdeteksi / %d bersih dari %d mesin (analisis terakhir %s)%s%s\n"
            "Catatan: hasil layanan luar, TIDAK ikut skor REA; hanya hash yang dikirim." % (
                r["sha256"], r["malicious"], r["suspicious"], r["undetected"], r["harmless"], tot, when,
                (" | nama: " + r["name"]) if r["name"] else "", (" | label: " + r["label"]) if r["label"] else ""))


# --- unpack lewat 7-Zip -------------------------------------------------------------------------------------------------------------------

UNPACK7_MAX_FILES = 5000
UNPACK7_MAX_TOTAL = 1024 * 1024 * 1024
UNPACK7_MEM = 3 * 1024 * 1024 * 1024


def unpack_7z(path, outdir) -> dict:
    """Bongkar kemasan yang dipahami 7-Zip (NSIS, SFX 7-Zip, 7z, dan lain-lain) ke folder sementara dengan batas sumber daya, lalu salin keluar
    HANYA berkas biasa (tautan simbolik / berkas khusus dibuang) beserta manifest SHA-256. Tidak menjalankan isi apa pun."""
    import shutil
    import subprocess
    import tempfile
    try:
        tool = next((shutil.which(x) for x in ("7zz", "7z", "7za", "7zr") if shutil.which(x)), None)
        if not tool:
            return {"ok": False, "error": "alat 7-Zip (7zz / 7z / 7za / 7zr) tidak ditemukan di PATH"}
        f, size = _open_regular(path)
        if size > UNPACK_MAX:
            f.close()
            return {"ok": False, "error": "berkas lebih besar dari batas %d MB" % (UNPACK_MAX >> 20)}
        out = Path(outdir).expanduser().resolve()
        with tempfile.TemporaryDirectory() as td:
            src, work = Path(td) / "in.bin", Path(td) / "x"
            work.mkdir()
            with f, open(src, "wb") as sf:
                shutil.copyfileobj(f, sf, 1 << 20)
            def _lim7():
                import resource
                for lim, val in ((resource.RLIMIT_AS, UNPACK7_MEM), (resource.RLIMIT_CPU, UNPACK_TIMEOUT * 3),
                                 (resource.RLIMIT_FSIZE, UNPACK7_MAX_TOTAL), (resource.RLIMIT_CORE, 0)):
                    try:
                        resource.setrlimit(lim, (val, val))
                    except (ValueError, OSError):
                        pass
            pre = _lim7 if os.name == "posix" else None
            r = subprocess.run([tool, "x", "-y", "-bd", "-o" + str(work), str(src)], capture_output=True, timeout=UNPACK_TIMEOUT * 3,
                               stdin=subprocess.DEVNULL, cwd=td, env={"PATH": os.environ.get("PATH", ""), "LANG": "C"}, preexec_fn=pre)
            if r.returncode not in (0, 1) and not any(work.iterdir()):
                return {"ok": False, "error": "7-Zip gagal (kode %d): %s" % (r.returncode, _clean((r.stderr or r.stdout).decode("utf-8", "replace"))[:160])}
            files, total, skipped = [], 0, 0
            out.mkdir(parents=True, exist_ok=True)
            for root, dirs, names in os.walk(work, followlinks=False):
                dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(root, x))]
                for n in sorted(names):
                    p = Path(root) / n
                    try:
                        st = os.lstat(p)
                    except OSError:
                        skipped += 1
                        continue
                    if not stat.S_ISREG(st.st_mode):
                        skipped += 1
                        continue
                    if len(files) >= UNPACK7_MAX_FILES or total + st.st_size > UNPACK7_MAX_TOTAL:
                        return {"ok": False, "error": "hasil melebihi batas (%d berkas / %d MB); dibatalkan" % (UNPACK7_MAX_FILES, UNPACK7_MAX_TOTAL >> 20)}
                    rel = p.relative_to(work).as_posix()
                    safe = "/".join(re.sub(r"[^\w.\- ]", "_", c)[:100] or "_" for c in rel.split("/") if c not in ("", ".", ".."))
                    dst = (out / safe).resolve()
                    if out != dst and out not in dst.parents:
                        skipped += 1
                        continue
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    h = hashlib.sha256()
                    with open(p, "rb") as sf, open(dst, "wb") as df:
                        for chunk in iter(lambda: sf.read(1 << 20), b""):
                            h.update(chunk)
                            df.write(chunk)
                    total += st.st_size
                    files.append({"name": safe, "size": st.st_size, "sha256": h.hexdigest()})
            man = out / "manifest_7z.json"
            man.write_text(json.dumps({"source": Path(str(path)).name, "files": files, "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"ok": True, "files": files, "total": total, "skipped": skipped, "manifest": str(man), "partial": r.returncode != 0}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "7-Zip melewati batas waktu"}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _clean(str(e))[:120])}


def unpack_7z_text(path, outdir) -> str:
    r = unpack_7z(path, outdir)
    if not r["ok"]:
        return "UNPACK 7-Zip gagal: " + r["error"]
    L = ["UNPACK 7-Zip: %d berkas, %s, %d dilewati (tautan / berkas khusus)%s | manifest: %s" % (
        len(r["files"]), _human(r["total"]), r["skipped"], " | SEBAGIAN (7-Zip melaporkan peringatan)" if r["partial"] else "", r["manifest"])]
    for x in r["files"][:40]:
        L.append("  %s  %s  %s" % (x["sha256"][:16], _human(x["size"]).rjust(9), x["name"]))
    if len(r["files"]) > 40:
        L.append("  ... +%d berkas lain di manifest" % (len(r["files"]) - 40))
    L.append("Berkas hasil BELUM ditriase; jalankan triase per berkas.")
    return "\n".join(L)


def _api_online(req: dict, notes: list | None = None) -> bool:
    """Online lewat API hanya bila diminta DAN operator menyalakan REA_ONLINE=1."""
    want = bool(req.get("online"))
    ok = want and os.environ.get("REA_ONLINE", "").strip() == "1"
    if want and not ok and notes is not None:
        notes.append("online diminta, tetapi REA_ONLINE=1 belum diatur operator: akses jaringan dilewati")
    return ok


# ---------------------------------------------------------------------------
# v99.15 (roadmap v2, Tier B: ekspor anotasi + diff fungsi; OPSIONAL dan ADITIF; keluaran triase lain TIDAK berubah):
#   1. export_annotations(path, fmt): skrip anotasi dari RE Lab (nama fungsi sub_*, komentar string yang dirujuk kode, komentar panggilan API,
#      teknik anti-analisis, kandidat loop dekripsi) untuk Ghidra (.py), IDA (.py), atau x64dbg (database .json). Berkas dibuat TANPA menjalankan
#      sampel; skrip Ghidra / IDA menggeser alamat otomatis bila image base di alat berbeda. Teks dari sampel disisipkan hanya sebagai literal JSON
#      yang di-escape (tidak pernah sebagai kode). Batas: ANN_MAX_FUNCS / ANN_MAX_CMTS.
#   2. func_diff(a, b): perbandingan fungsi antar-dua biner (nama bukan sub_*, set API, string, ukuran, jumlah callee) -> sama / berubah / baru / hilang.
#      Pencocokan: nama ekspor / simbol, lalu kemiripan fitur (Jaccard + rasio ukuran), lalu (ukuran, callee) unik. Batas waktu FDIFF_TIME.
#   CLI: --export FILE ghidra|ida|x64dbg [OUT], --funcdiff A B. API: export (butuh outdir), funcdiff.
#   Batasan: kemiripan hanya statis dari fitur RE Lab (bukan perbandingan instruksi); fungsi tanpa API / string dicocokkan hanya lewat ukuran.
# ---------------------------------------------------------------------------

ANN_MAX_FUNCS = 20000
ANN_MAX_CMTS = 30000
FDIFF_TIME = 6.0
FDIFF_MAX_FUNCS = 4000


def _ann_txt(s, n: int = 110) -> str:
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(s))[:n]


def _relab_ctx(path):
    f, size = _open_regular(path)
    with f:
        d = f.read(MAX_SCAN)
    info, ctx, err = _relab_any(d, size)
    return info, ctx, err


def _ann_collect(path) -> dict:
    info, ctx, err = _relab_ctx(path)
    if not ctx:
        return {"error": (err or "tidak bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64"}
    F = ctx["F"]
    funcs = [(va, fo["name"]) for va, fo in sorted(F.items())][:ANN_MAX_FUNCS]
    cm: dict[int, list[str]] = {}

    def add(va, t):
        if len(cm) < ANN_MAX_CMTS or va in cm:
            lst = cm.setdefault(int(va), [])
            if t not in lst and len(lst) < 3:
                lst.append(t)
    for api, vs in ctx["sites"].items():
        for va, _fs in vs:
            add(va, "API: " + _ann_txt(api, 60))
    for e in ctx["sref"].values():
        if e["funcs"]:
            add(e["va"], "string(%s): %s" % (e["kind"], _ann_txt(e["text"])))
    for a in info.get("anti", []):
        try:
            add(int(a["first"], 16), "anti-analisis: " + _ann_txt(a["technique"], 60))
        except (ValueError, KeyError):
            pass
    for x in (info.get("cfg") or {}).get("decrypt_loops", []):
        try:
            add(int(x["head"], 16), "kandidat loop dekripsi (%s)" % "/".join(x["ops"]))
        except (ValueError, KeyError):
            pass
    return {"base": int(info["image_base"], 16), "arch": info["arch"], "funcs": funcs, "cmts": sorted((va, " | ".join(t)) for va, t in cm.items())}


_ANN_GHIDRA = '''# Dibuat oleh rea_triage.py v%(ver)s (analisis statis; sampel tidak dijalankan). Jalankan dari Script Manager Ghidra (Jython / PyGhidra).
# Sumber: %(src)s | %(arch)s
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit
IMAGE_BASE = %(base)s
FUNCS = %(funcs)s
CMTS = %(cmts)s
delta = currentProgram.getImageBase().getOffset() - IMAGE_BASE
fm = currentProgram.getFunctionManager()
lst = currentProgram.getListing()
nf = nc = 0
for va, name in FUNCS:
    a = toAddr(va + delta)
    try:
        f = fm.getFunctionAt(a)
        if f is None:
            f = createFunction(a, name)
        elif f.getName().startswith("FUN_"):
            f.setName(name, SourceType.USER_DEFINED)
        nf += 1
    except Exception as e:
        pass
for va, text in CMTS:
    try:
        lst.setComment(toAddr(va + delta), CodeUnit.EOL_COMMENT, text)
        nc += 1
    except Exception as e:
        pass
print("rea_triage: %%d fungsi, %%d komentar" %% (nf, nc))
'''
_ANN_IDA = '''# Dibuat oleh rea_triage.py v%(ver)s (analisis statis; sampel tidak dijalankan). Jalankan lewat File > Script file di IDA (IDAPython 7+).
# Sumber: %(src)s | %(arch)s
import idc, idaapi, ida_funcs
IMAGE_BASE = %(base)s
FUNCS = %(funcs)s
CMTS = %(cmts)s
delta = idaapi.get_imagebase() - IMAGE_BASE
nf = nc = 0
for va, name in FUNCS:
    ea = va + delta
    try:
        if ida_funcs.get_func(ea) is None:
            ida_funcs.add_func(ea)
        if idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK):
            nf += 1
    except Exception:
        pass
for va, text in CMTS:
    try:
        if idc.set_cmt(va + delta, text, 0):
            nc += 1
    except Exception:
        pass
print("rea_triage: %%d fungsi, %%d komentar" %% (nf, nc))
'''


def export_annotations(path, fmt: str = "ghidra", out=None) -> dict:
    """Skrip anotasi Ghidra / IDA / x64dbg dari RE Lab. Mengembalikan {"ok", "fmt", "content", "functions", "comments", "path"?}. Tidak pernah melempar."""
    try:
        fmt = str(fmt).lower()
        if fmt not in ("ghidra", "ida", "x64dbg"):
            return {"ok": False, "error": "format harus ghidra, ida, atau x64dbg"}
        a = _ann_collect(path)
        if "error" in a:
            return {"ok": False, "error": a["error"]}
        name = os.path.basename(str(path))
        if fmt == "x64dbg":
            mod = name.lower()
            rva = lambda va: "0x%X" % max(0, va - a["base"])
            content = json.dumps({"labels": [{"module": mod, "address": rva(v), "manual": True, "text": n} for v, n in a["funcs"]],
                                  "comments": [{"module": mod, "address": rva(v), "manual": True, "text": t} for v, t in a["cmts"]]}, indent=1)
        else:
            tpl = _ANN_GHIDRA if fmt == "ghidra" else _ANN_IDA
            lit = lambda o: json.dumps(o, ensure_ascii=True, separators=(",", ":"))
            content = tpl % {"ver": VERSION, "src": _ann_txt(name, 80), "arch": _ann_txt(a["arch"], 60), "base": "0x%X" % a["base"],
                             "funcs": lit([[v, n] for v, n in a["funcs"]]), "cmts": lit([[v, t] for v, t in a["cmts"]])}
        r = {"ok": True, "fmt": fmt, "content": content, "functions": len(a["funcs"]), "comments": len(a["cmts"])}
        if out:
            p = Path(out)
            if p.is_dir() or str(out).endswith(("/", "\\")):
                p = Path(out) / (name + ".rea." + ("json" if fmt == "x64dbg" else "py"))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8", newline="\n")
            r["path"] = str(p)
        return r
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120])}


def export_text(path, fmt: str = "ghidra", out=None) -> str:
    r = export_annotations(path, fmt, out)
    if not r["ok"]:
        return "EKSPOR gagal: " + r["error"]
    return "EKSPOR %s: %d fungsi, %d komentar%s" % (r["fmt"], r["functions"], r["comments"], (" -> " + r["path"]) if r.get("path") else
                                                  "\n(tambahkan OUT untuk menyimpan; tanpa itu isi berkas tidak ditulis)")


def _fd_sigs(path) -> dict:
    info, ctx, err = _relab_ctx(path)
    if not ctx:
        raise ValueError((err or "tidak bisa dianalisis") + "; RE Lab mendukung PE dan ELF x86 / x64")
    out = {}
    for va, fo in list(ctx["F"].items())[:FDIFF_MAX_FUNCS * 4]:
        if va in ctx["thunks"]:
            continue
        feats = frozenset(["a:" + k for k in fo["apis"]] + ["s:" + _ann_txt(x, 60).lower() for x in fo["strings"]])
        out[va] = {"va": va, "name": fo["name"], "size": fo["size"], "nc": len(fo["callees"]), "feats": feats}
        if len(out) >= FDIFF_MAX_FUNCS:
            break
    return out


def _fd_score(x: dict, y: dict) -> float:
    u = len(x["feats"] | y["feats"])
    j = len(x["feats"] & y["feats"]) / u if u else (1.0 if x["nc"] == y["nc"] else 0.0)
    sz = min(x["size"], y["size"]) / max(x["size"], y["size"], 1)
    return round(0.7 * j + 0.3 * sz, 3)


def func_diff(path_a, path_b) -> dict:
    """Diff fungsi antar-dua biner (statis). Tidak pernah melempar. Lihat komentar v99.15 untuk metode dan batasan."""
    try:
        A, B = _fd_sigs(path_a), _fd_sigs(path_b)
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:140])}
    t0 = time.monotonic()
    pairs: list[tuple[int, int, float, str]] = []
    ua, ub = set(A), set(B)
    named = {}
    for vb, y in B.items():
        if not y["name"].startswith("sub_"):
            named.setdefault(y["name"], vb)
    for va, x in A.items():
        if not x["name"].startswith("sub_") and x["name"] in named and named[x["name"]] in ub:
            vb = named[x["name"]]
            pairs.append((va, vb, _fd_score(x, B[vb]), "nama"))
            ua.discard(va)
            ub.discard(vb)
    ea: dict[tuple, list] = {}
    eb: dict[tuple, list] = {}
    for va in ua:
        if A[va]["feats"]:
            ea.setdefault((A[va]["feats"], A[va]["size"], A[va]["nc"]), []).append(va)
    for vb in ub:
        if B[vb]["feats"]:
            eb.setdefault((B[vb]["feats"], B[vb]["size"], B[vb]["nc"]), []).append(vb)
    for k, la in ea.items():   # tanda tangan persis sama (fitur + ukuran + callee): pasangkan menurut urutan alamat
        for va, vb in zip(sorted(la), sorted(eb.get(k, []))):
            pairs.append((va, vb, 1.0, "fitur"))
            ua.discard(va)
            ub.discard(vb)
    inv: dict[str, list[int]] = {}
    for vb in ub:
        for ft in B[vb]["feats"]:
            inv.setdefault(ft, []).append(vb)
    cand = []
    partial = False
    for va in ua:
        if time.monotonic() - t0 > FDIFF_TIME:
            partial = True
            break
        seen: dict[int, int] = {}
        for ft in A[va]["feats"]:
            lst = inv.get(ft, ())
            if len(lst) <= 60:
                for vb in lst:
                    seen[vb] = seen.get(vb, 0) + 1
        for vb in sorted(seen, key=lambda k: -seen[k])[:8]:
            cand.append((_fd_score(A[va], B[vb]), va, vb))
    for sc, va, vb in sorted(cand, key=lambda c: (-c[0], c[1], c[2])):
        if sc >= 0.6 and va in ua and vb in ub:
            pairs.append((va, vb, sc, "fitur"))
            ua.discard(va)
            ub.discard(vb)
    ga: dict[tuple, list] = {}
    gb: dict[tuple, list] = {}
    for va in ua:
        if not A[va]["feats"]:
            ga.setdefault((A[va]["size"], A[va]["nc"]), []).append(va)
    for vb in ub:
        if not B[vb]["feats"]:
            gb.setdefault((B[vb]["size"], B[vb]["nc"]), []).append(vb)
    for k, la in ga.items():   # fungsi tanpa API / string: cocok hanya bila jumlah per (ukuran, callee) sama; urut menurut alamat
        lb = gb.get(k, [])
        if len(la) == len(lb):
            for va, vb in zip(sorted(la), sorted(lb)):
                pairs.append((va, vb, _fd_score(A[va], B[vb]), "ukuran"))
                ua.discard(va)
                ub.discard(vb)
    same = [p for p in pairs if p[2] >= 0.999 and A[p[0]]["size"] == B[p[1]]["size"]]
    chg = sorted([p for p in pairs if p not in same], key=lambda p: (p[2], p[0]))
    row = lambda S, v: {"va": "0x%X" % v, "name": _clean(S[v]["name"]), "size": S[v]["size"]}
    return {"ok": True, "partial": partial, "a": {"funcs": len(A)}, "b": {"funcs": len(B)}, "identical": len(same), "weak": sum(1 for p in same if p[3] == "ukuran"),
            "changed": [{"a": row(A, p[0]), "b": row(B, p[1]), "sim": p[2], "by": p[3]} for p in chg],
            "removed": [row(A, v) for v in sorted(ua)], "added": [row(B, v) for v in sorted(ub)]}


def func_diff_text(path_a, path_b, max_items: int = 15) -> str:
    r = func_diff(path_a, path_b)
    if not r["ok"]:
        return "FUNCDIFF gagal: " + r["error"]
    L = ["FUNCDIFF: A %d fungsi, B %d fungsi | sama %d (%d hanya dari ukuran), berubah %d, hilang di B %d, baru di B %d%s" % (
        r["a"]["funcs"], r["b"]["funcs"], r["identical"], r["weak"], len(r["changed"]), len(r["removed"]), len(r["added"]),
        " | TERPOTONG (batas waktu)" if r["partial"] else "")]
    for c in r["changed"][:max_items]:
        L.append("   berubah (%.2f, %s): %s %s (%dB) -> %s %s (%dB)" % (c["sim"], c["by"], c["a"]["name"], c["a"]["va"], c["a"]["size"], c["b"]["name"], c["b"]["va"], c["b"]["size"]))
    for k, lab in (("removed", "hilang"), ("added", "baru")):
        for x in r[k][:max_items // 3 or 1]:
            L.append("   %s: %s %s (%dB)" % (lab, x["name"], x["va"], x["size"]))
    return "\n".join(L)


_API_ACTIONS = ("export", "funcdiff", "sigcheck", "reputation", "unpack7z", "capabilities", "cache", "triage", "json", "ioc", "yara", "md", "similar", "hex", "compare", "list", "extract", "dir", "ctph", "re", "xref", "disasm", "unpack", "yarascan", "assets", "assets_extract", "assets_carve", "formats", "dex", "dotnet", "cfg", "emu", "config", "deobf", "unity", "unity_extract")


_DEFAULT_ROOTS: list = []     # diisi pemanggil tepercaya (server.py) lewat set_default_roots(); dipakai bila env REA_ROOTS kosong


def set_default_roots(roots) -> list:
    """Akar bawaan untuk rea_api bila env REA_ROOTS kosong. Dipanggil server.py saat start supaya pembatas aktif tanpa bergantung pada .env.
    Env REA_ROOTS yang diisi manual tetap menang. Daftar kosong / None = tanpa batas bawaan. Mengembalikan daftar akar yang berlaku."""
    _DEFAULT_ROOTS[:] = [str(x) for x in (roots or []) if str(x).strip()]
    return _roots()


def _roots() -> list:
    """Akar yang berlaku: env REA_ROOTS (dipisah os.pathsep) kalau diisi, kalau tidak akar bawaan dari set_default_roots()."""
    env = [x for x in os.environ.get("REA_ROOTS", "").split(os.pathsep) if x.strip()]
    return env or list(_DEFAULT_ROOTS)


def _api_path(p) -> Path:
    """Jika REA_ROOTS / akar bawaan ada, hanya path di bawah akar itu yang boleh dibaca / ditulis. Pesan galat seragam untuk semua aksi."""
    pp = Path(str(p)).expanduser().resolve()
    roots = _roots()
    if roots and not any(pp == Path(r).resolve() or Path(r).resolve() in pp.parents for r in roots):
        raise PermissionError("path di luar REA_ROOTS: %s (hanya boleh di bawah: %s)" % (pp.name[:80], "; ".join(Path(r).name or str(r) for r in roots)[:160]))
    return pp


def _api_outdir(p) -> Path:
    """Seperti _api_path, tetapi untuk TUJUAN TULIS (outdir). Fail-closed: tanpa REA_ROOTS / akar bawaan, agen tidak boleh menulis ke mana pun."""
    if not _roots():
        raise PermissionError("penulisan lewat API ditolak: REA_ROOTS / set_default_roots() belum diatur (outdir harus berada di bawah akar yang diizinkan)")
    return _api_path(p)


def rea_api(request) -> dict:
    """Satu pintu JSON untuk agen. request: dict atau string JSON, contoh {"action": "triage", "path": "x.exe", "compact": true}.
    Selalu mengembalikan dict {"ok": bool, ...}; tidak pernah melempar. Aksi: lihat _API_ACTIONS."""
    try:
        req = json.loads(request) if isinstance(request, (str, bytes)) else dict(request)
        act = str(req.get("action", "")).lower()
        mc = max(0, int(req.get("max_chars", 12000)))
        trim = lambda t: t if not mc or len(t) <= mc else t[:mc - 30] + "\n[...dipangkas supaya muat...]"
        if act == "capabilities":
            return {"ok": True, "version": VERSION, "actions": list(_API_ACTIONS), "rea_extract": _extract_mod() is not None,
                    "rea_binary": _has_binary(), "rea_assets": _assets_mod() is not None, "roots_restricted": bool(_roots()),
                    "cache": _cache_dir() is not None, "sigcheck_crypto": importlib.util.find_spec("cryptography") is not None,
                    "optional_deps": {m_: importlib.util.find_spec(m_) is not None for m_ in ("PIL", "texture2ddecoder", "lz4", "lief", "capstone", "UnityPy")},
                    "online_enabled": os.environ.get("REA_ONLINE", "").strip() == "1", "vt_key_set": bool(os.environ.get("REA_VT_KEY", "").strip()),
                    "sevenzip": any(__import__("shutil").which(x) for x in ("7zz", "7z", "7za", "7zr"))}
        if act == "cache":
            return {"ok": True, "action": act, "info": cache_info()}
        if act == "triage":
            p = _api_path(req["path"])
            if p.is_dir():
                return {"ok": True, "action": act, "text": trim(triage_dir_text(str(p), defang=bool(req.get("defang", True))))}
            rep = triage(p, use_cache=not req.get("nocache"))
            return {"ok": True, "action": act, "cached": bool(rep.get("cached")), "score": rep["score"], "level": rep["level"], "sha256": rep["sha256"], "kind": rep["kind"],
                    "text": trim(render(rep, compact=bool(req.get("compact", False)), defang=bool(req.get("defang", True)), max_chars=mc, card=bool(req.get("card", False))))}
        if act in ("json", "ioc"):
            return {"ok": True, "action": act, "data": json.loads(triage_json(_api_path(req["path"]), ioc_only=act == "ioc"))}
        if act == "yara":
            return {"ok": True, "action": act, "text": yara_draft(triage(_api_path(req["path"]), fuzzy=False))}
        if act == "md":
            return {"ok": True, "action": act, "text": trim(triage_md(_api_path(req["path"]), defang=bool(req.get("defang", True))))}
        if act == "ctph":
            data, _sz = _read_sample(_api_path(req["path"]))
            return {"ok": True, "action": act, "ctph": ctph(data), "sample": len(data)}
        if act == "similar":
            return {"ok": True, "action": act, "data": similarity(_api_path(req["a"]), _api_path(req["b"]))}
        if act == "hex":
            return {"ok": True, "action": act, "text": trim(hex_text(_api_path(req["path"]), int(req.get("offset", 0)), int(req.get("length", 256))))}
        if act == "compare":
            return {"ok": True, "action": act, "text": trim(compare_text(_api_path(req["a"]), _api_path(req["b"])))}
        if act == "list":
            return {"ok": True, "action": act, "text": trim(container_text(_api_path(req["path"]), max_chars=mc))}
        if act == "extract":
            m = container_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), pattern=req.get("pattern"), scan=bool(req.get("scan", False)))
            return {"ok": m.get("status") == "success", "action": act, "manifest": m}
        if act == "re":
            p = _api_path(req["path"])
            return {"ok": True, "action": act, "data": re_lab_path(p), "text": trim(re_text(p, defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "xref":
            return {"ok": True, "action": act, "text": trim(xref_text(_api_path(req["path"]), str(req["query"])))}
        if act == "disasm":
            return {"ok": True, "action": act, "text": trim(disasm_text(_api_path(req["path"]), req.get("at", "entry"), int(req.get("count", 40)), req.get("arch")))}
        if act == "unpack":
            return {"ok": True, "action": act, "text": trim(unpack_text(_api_path(req["path"]), _api_outdir(req["outdir"])))}
        if act == "yarascan":
            return {"ok": True, "action": act, "text": trim(yara_text(_api_path(req["path"]), _api_path(req["rules"])))}
        if act == "dir":
            return {"ok": True, "action": act, "text": trim(triage_dir_text(str(_api_path(req["path"])), defang=bool(req.get("defang", True))))}
        if act == "emu":
            return {"ok": True, "action": act, "text": trim(emu_text(_api_path(req["path"]), req.get("at"), defang=bool(req.get("defang", True))))}
        if act == "deobf":
            return {"ok": True, "action": act, "text": trim(deobf_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), full=bool(req.get("full", False))))}
        if act == "config":
            if req.get("json"):
                return {"ok": True, "action": act, **extract_config(_api_path(req["path"]), keys=req.get("keys"), reveal=bool(req.get("reveal", False)))}
            return {"ok": True, "action": act, "text": trim(config_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), keys=req.get("keys")))}
        if act == "cfg":
            return {"ok": True, "action": act, "text": trim(cfg_text(_api_path(req["path"]), req.get("at")))}
        if act == "dotnet":
            return {"ok": True, "action": act, "text": trim(net_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "dex":
            return {"ok": True, "action": act, "text": trim(dex_text(_api_path(req["path"]), defang=bool(req.get("defang", True)), compact=bool(req.get("compact", False))))}
        if act == "assets":
            return {"ok": True, "action": act, "text": trim(assets_text(_api_path(req["path"]), max_chars=mc))}
        if act == "unity":
            return {"ok": True, "action": act, "data": unity_info(_api_path(req["path"])), "text": trim(unity_text(_api_path(req["path"])))}
        if act == "unity_extract":
            m = unity_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), types=req.get("types"), name=req.get("name"), flip=bool(req.get("flip", True)))
            return {"ok": m.get("status") in ("success", "partial"), "action": act, "manifest": m}
        if act == "assets_extract":
            m = assets_extract(_api_path(req["path"]), _api_outdir(req["outdir"]), pattern=req.get("pattern"), convert=bool(req.get("convert", True)))
            return {"ok": m.get("status") in ("success", "partial"), "action": act, "manifest": m}
        if act == "assets_carve":
            od = _api_outdir(req["outdir"]) if req.get("outdir") else None
            m = assets_carve(_api_path(req["path"]), od)
            return {"ok": m.get("status") == "success", "action": act, "result": m}
        if act == "export":
            r = export_annotations(_api_path(req["path"]), req.get("fmt", "ghidra"), _api_outdir(req["outdir"]) if req.get("outdir") else None)
            r.pop("content", None)
            return {"ok": bool(r.get("ok")), "action": act, "result": r}
        if act == "funcdiff":
            return {"ok": True, "action": act, "text": trim(func_diff_text(_api_path(req["path"]), _api_path(req["path2"]))), "data": func_diff(_api_path(req["path"]), _api_path(req["path2"]))}
        if act == "sigcheck":
            notes: list = []
            r = sig_check(_api_path(req["path"]), online=_api_online(req, notes))
            if isinstance(r.get("notes"), list):
                r["notes"].extend(notes)
            txt = sig_text(_api_path(req["path"]), online=_api_online(req)) if r.get("ok") else "TANDA TANGAN: " + r.get("error", "gagal")
            return {"ok": bool(r.get("ok")), "action": act, "data": r, "text": trim(txt + ("".join("\nCatatan: " + n for n in notes)))}
        if act == "reputation":
            notes = []
            tgt = str(req["target"]).strip()
            tgt = tgt if re.fullmatch(r"[0-9a-fA-F]{64}", tgt) else str(_api_path(tgt))
            on = _api_online(req, notes)
            r = reputation(tgt, online=on)
            return {"ok": bool(r.get("ok")), "action": act, "data": r, "text": trim(reputation_text(tgt, online=on) + ("".join("\nCatatan: " + n for n in notes)))}
        if act == "unpack7z":
            return {"ok": True, "action": act, "text": trim(unpack_7z_text(_api_path(req["path"]), _api_outdir(req["outdir"])))}
        if act == "formats":
            mod = _assets_mod()
            return {"ok": mod is not None, "action": act, "formats": mod.formats() if mod else []}
        return {"ok": False, "error": "aksi tidak dikenal: %s" % act[:40], "actions": list(_API_ACTIONS)}
    except PermissionError as e:
        return {"ok": False, "error": str(e)[:200]}
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160])}


def _has_binary() -> bool:
    return True   # Binary Workbench sudah digabung ke berkas ini (23 Nov 2026)


# ---------------------------------------------------------------------------
# v95: jembatan ke mesin ekstraksi (rea_extract.py). Impor malas: triase tetap jalan walau modul itu tidak ada.
# ---------------------------------------------------------------------------


def _extract_mod():
    """Mesin ekstraksi container (dulu rea_extract.py, digabung 23 Nov 2026); fasad dari bagian bawah berkas ini."""
    return _EX_API


def container_text(path, max_chars: int = 0) -> str:
    """Daftar isi container (ZIP/TAR/GZIP/ISO/PSP ISO), hanya-baca. Gagal -> pesan, tidak melempar."""
    mod = _extract_mod()
    if mod is None:
        return "Mesin ekstraksi (rea_extract.py) tidak ditemukan di folder yang sama; fitur isi container tidak tersedia."
    try:
        return mod.describe_container_text(path, max_chars=max_chars)
    except Exception as e:
        return "CONTAINER gagal dibaca (%s: %s)." % (type(e).__name__, str(e)[:120])


def container_extract(path, outdir, pattern=None, scan: bool = False) -> dict:
    """Ekstraksi selektif ke workspace outdir (extracted/, manifests/, logs/). Mengembalikan manifest (dict)."""
    mod = _extract_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_extract.py tidak ditemukan"}
    r = mod.open_container(path)
    if r.get("status") != "success":
        return r
    try:
        return mod.extract_selected(r["container_id"], {"pattern": pattern} if pattern else None, outdir, scan=scan)
    finally:
        mod.close_container(r["container_id"])


# ======================================================================================================
# rea_assets.py (Asset Explorer v99.0) DIGABUNG ke berkas ini pada 22 Nov 2026 (v99.2, tanpa ubah perilaku).
# Nama yang bentrok dengan rea_triage diberi awalan _as_ (VERSION, _clean, _entropy, _human, carve). Akses dari luar bagian ini
# lewat _assets_mod() (fasad: nama aslinya tetap bisa dipakai, mis. mod.carve). Plugin (REA_PLUGINS) dimuat malas saat _assets_mod() pertama dipanggil.
# Dokumentasi asli modul:
# rea_assets.py - v99.0 Asset Explorer untuk REA (jembatan ke rea_triage.py).
#
# Tujuan: REA tidak hanya membedah .exe / .dll, tetapi bisa MEMBUKA ISI hampir semua berkas: model 3D, animasi, tekstur,
# audio, arsip / paket game, database, dan data tertanam di dalam berkas lain. Hanya pustaka standar, hanya-baca terhadap
# berkas sumber (hasil selalu ditulis ke folder keluaran terpisah), TANPA menjalankan apa pun dari berkas.
#
# API (semua tidak melempar kecuali dinyatakan):
#     identify(path) -> dict                        jenis berkas + kategori (deteksi lewat magic bytes, bukan ekstensi saja)
#     describe(path) -> dict / describe_text(path)  ringkasan isi: mesh, animasi, tekstur, daftar entri arsip, tabel DB ...
#     extract(path, outdir, pattern=None, convert=True) -> manifest dict
#                                                   mengeluarkan isi: gambar / buffer dari glTF, mesh -> .obj, animasi -> .json / .csv,
#                                                   tekstur DDS / TGA / BMP -> .png, entri arsip (PAK / WAD / ZIP / TAR ...), tabel SQLite -> .csv
#     carve(path, outdir=None, max_items=200) -> dict   cari & potong berkas yang TERTANAM di dalam berkas apa pun (PNG, JPEG, GIF, OGG, RIFF,
#                                                   GLB, SQLite, ZIP, MIDI ...) -- berguna untuk .exe / .dat / resource yang tidak punya format terdokumentasi
#     formats() -> list[dict]                       daftar parser terpasang (termasuk plugin)
#     load_plugins(folder) -> list[str]             muat parser tambahan (lihat bagian PLUGIN)
#
# Format bawaan:
#   3D / animasi : glTF / GLB, OBJ, STL, PLY, FBX (biner; ASCII hanya ringkasan), COLLADA (.dae), BVH
#   gambar       : PNG / APNG, JPEG, GIF, BMP, TGA, DDS (DXT1/3/5, BC4, BC5 + RGBA tak terkompresi), WebP, ICO
#   audio        : WAV, OGG (Vorbis / Opus), FLAC, MP3, MIDI
#   arsip / game : Quake PAK, WAD (Doom / Quake / Half-Life), Unreal .pak (v1-v11, tanpa enkripsi), ZIP (APK / JAR / OOXML ...), TAR, GZIP,
#                  UnityFS (ekstraksi node), 7z / RAR (deteksi saja)
#   data         : SQLite
#
# Yang BELUM / tidak bisa dibuka langsung (dilaporkan jelas, bukan ditebak): paket terenkripsi / dikompres format sendiri, aset Unity /
# Unreal yang terserialisasi (butuh parser per versi mesin), tekstur BC6H / BC7 / ASTC. Untuk itu tulis plugin (di bawah).
#
# PLUGIN (parser buatan sendiri, ala QuickBMS): buat folder berisi berkas .py, masing-masing memuat
#     def register_formats(reg):
#         reg("nama", "kategori", detect, inspect=None, extract=None, priority=50, about="")
#   detect(d, ext) -> bool        d = isi berkas (mmap / bytes, hanya-baca), ext = ekstensi huruf kecil
#   inspect(d, path) -> {"lines": [str], "info": {...}, "extract": "apa yang bisa diekstrak"}
#   extract(d, path, out, opts)   out.write("sub/nama.bin", bytes, kind="...") ; opts = {"pattern": ..., "convert": bool}
# Plugin adalah KODE yang dijalankan: dimuat hanya bila diminta eksplisit (--plugins FOLDER, env REA_PLUGINS, atau load_plugins()),
# TIDAK pernah lewat permintaan API agen.
#
# ======================================================================================================
import csv
import fnmatch
import importlib.util
import io
import mmap
import re
import sqlite3
import tarfile
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from contextlib import contextmanager

_as_VERSION = "99.0"
MAX_OUT_FILE = 512 * 1024 * 1024      # satu berkas keluaran
MAX_OUT_TOTAL = 4 * 1024 ** 3         # total keluaran satu ekstraksi
MAX_ENTRIES = 200_000                 # entri arsip
MAX_PIXELS = 64 * 1024 * 1024         # piksel maksimum saat dekode tekstur
MAX_XML = 64 * 1024 * 1024
MAX_ACCESSOR = 5_000_000
MAX_CARVE_SCAN = 1024 * 1024 * 1024


def _u16(d, o): return struct.unpack_from("<H", d, o)[0]
def _u32(d, o): return struct.unpack_from("<I", d, o)[0]
def _u64(d, o): return struct.unpack_from("<Q", d, o)[0]
def _b32(d, o): return struct.unpack_from(">I", d, o)[0]


def _as_human(n: float) -> str:
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%d %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f GB" % n


# v103.2: sama dengan _CTRL_RE bagian utama: kontrol, C1, dan pengecoh arah teks (RLO dll.) dari berkas tak tepercaya
_as_ctrl_re = re.compile(r"[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028-\u202e\u2060-\u2064\u2066-\u2069\ufeff]")


def _as_clean(s, n=200) -> str:
    """Bersihkan teks dari berkas tak tepercaya (tanpa baris baru / karakter kontrol) sebelum masuk laporan."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8", "replace")
    return _as_ctrl_re.sub(" ", str(s))[:n]


# ---------------------------------------------------------------------------
# Buka berkas (hanya berkas biasa, dipetakan ke memori hanya-baca) dan tulis keluaran dengan aman
# ---------------------------------------------------------------------------

@contextmanager
def _map(path):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(os.fspath(path), flags)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("bukan berkas biasa (FIFO / perangkat / folder): %s" % Path(path).name)
        f = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    try:
        if st.st_size == 0:
            yield b""
        else:
            m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                yield m
            finally:
                m.close()
    finally:
        f.close()


_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}


def _safe_rel(name) -> str:
    """Nama entri dari berkas tak tepercaya -> path relatif aman (tanpa '..', drive, karakter terlarang)."""
    s = str(name).replace("\\", "/").replace("\x00", "")
    parts = []
    for part in s.split("/"):
        part = part.strip()
        if part in ("", ".", ".."):
            continue
        part = _as_ctrl_re.sub("_", re.sub(r'[<>:"|?*\x00-\x1f]', "_", part)).rstrip(". ") or "_"
        if part.split(".")[0].upper() in _RESERVED:
            part = "_" + part
        parts.append(part[:120])
    return "/".join(parts) or "unnamed"


class _Out:
    """Penulis keluaran: semua path dipaksa tetap di bawah outdir, tidak menimpa berkas, batas ukuran, manifest."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.files: list[dict] = []
        self.skipped: list[dict] = []
        self.errors: list[str] = []
        self.total = 0

    def write(self, rel, data, kind: str = "", note: str = ""):
        rel = _safe_rel(rel)
        if len(data) > MAX_OUT_FILE or self.total + len(data) > MAX_OUT_TOTAL:
            self.skipped.append({"path": rel, "size": len(data), "reason": "melebihi batas ukuran keluaran"})
            return None
        target = (self.root / rel).resolve()
        if self.root not in target.parents:
            self.skipped.append({"path": rel, "size": len(data), "reason": "path di luar folder keluaran"})
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        stem, suf, k = target.stem, target.suffix, 1
        while True:
            try:
                with open(target, "xb") as fh:
                    fh.write(data)
                break
            except FileExistsError:
                k += 1
                target = target.with_name("%s_%d%s" % (stem, k, suf))
        self.total += len(data)
        self.files.append({"path": target.relative_to(self.root).as_posix(), "size": len(data), "kind": kind, "note": note,
                           "sha256": hashlib.sha256(data).hexdigest()})
        return target

    def write_text(self, rel, text, kind="", note=""):
        return self.write(rel, text.encode("utf-8"), kind, note)


# ---------------------------------------------------------------------------
# Registri parser
# ---------------------------------------------------------------------------

class _Fmt:
    __slots__ = ("name", "category", "detect", "inspect", "extract", "priority", "about", "plugin")

    def __init__(self, name, category, detect, inspect, extract, priority, about, plugin=False):
        self.name, self.category, self.detect, self.inspect, self.extract = name, category, detect, inspect, extract
        self.priority, self.about, self.plugin = priority, about, plugin


_FORMATS: list[_Fmt] = []
_LOADED_PLUGINS: set[str] = set()


def register(name, category, detect, inspect=None, extract=None, priority: int = 50, about: str = "", _plugin: bool = False):
    _FORMATS[:] = [f for f in _FORMATS if f.name != name]
    _FORMATS.append(_Fmt(name, category, detect, inspect, extract, priority, about, _plugin))
    _FORMATS.sort(key=lambda f: f.priority)


def formats() -> list[dict]:
    return [{"name": f.name, "category": f.category, "inspect": f.inspect is not None, "extract": f.extract is not None,
             "plugin": f.plugin, "about": f.about} for f in _FORMATS]


def load_plugins(folder) -> list[str]:
    """Muat semua *.py di folder; tiap berkas boleh mendefinisikan register_formats(reg). Mengembalikan nama plugin yang termuat.
    Ini MENJALANKAN kode di folder itu: arahkan hanya ke folder yang Anda percaya."""
    got = []
    p = Path(folder).expanduser().resolve()
    if not p.is_dir():
        return got
    for f in sorted(p.glob("*.py")):
        key = str(f)
        if key in _LOADED_PLUGINS:
            continue
        spec = importlib.util.spec_from_file_location("rea_plugin_" + re.sub(r"\W", "_", f.stem), f)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            fn = getattr(mod, "register_formats", None)
            if fn:
                fn(lambda name, category, detect, inspect=None, extract=None, priority=50, about="": register(
                    name, category, detect, inspect, extract, priority, about, _plugin=True))
                got.append(f.name)
                _LOADED_PLUGINS.add(key)
        except Exception as e:   # plugin rusak tidak boleh menjatuhkan REA
            got.append("%s (GAGAL: %s)" % (f.name, _as_clean(e, 80)))
    return got


def _detect(d, ext: str) -> _Fmt | None:
    for f in _FORMATS:
        try:
            if f.detect(d, ext):
                return f
        except Exception:
            continue
    return None


def _sha256(d) -> str:
    h = hashlib.sha256()
    n = len(d)
    for i in range(0, n, 8 * 1024 * 1024):
        h.update(d[i:i + 8 * 1024 * 1024])
    return h.hexdigest()


def _as_entropy(b) -> float:
    if not b:
        return 0.0
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in collections.Counter(b).values())


# ---------------------------------------------------------------------------
# OBJ writer bersama
# ---------------------------------------------------------------------------

def _obj_name(s, fallback="mesh") -> str:
    s = re.sub(r"[^\w.\-]+", "_", str(s or "")).strip("._")
    return s[:60] or fallback


class _ObjBuilder:
    def __init__(self):
        self.lines: list[str] = []
        self.nv = self.nvt = self.nvn = 0
        self.faces = 0

    def group(self, name):
        self.lines.append("o %s" % _obj_name(name))

    def add(self, pos, uv=None, nrm=None, tris=(), polys=()):
        """pos: list (x,y,z); uv: list (u,v) atau None; nrm: list (x,y,z) atau None; tris: list (a,b,c) 0-based; polys: list list indeks."""
        b0, t0, n0 = self.nv, self.nvt, self.nvn
        self.lines += ["v %.7g %.7g %.7g" % (p[0], p[1], p[2]) for p in pos]
        if uv:
            self.lines += ["vt %.7g %.7g" % (u[0], u[1]) for u in uv]
        if nrm:
            self.lines += ["vn %.7g %.7g %.7g" % (n[0], n[1], n[2]) for n in nrm]

        def corner(i):
            a = b0 + i + 1
            if uv and nrm:
                return "%d/%d/%d" % (a, t0 + i + 1, n0 + i + 1)
            if uv:
                return "%d/%d" % (a, t0 + i + 1)
            if nrm:
                return "%d//%d" % (a, n0 + i + 1)
            return str(a)
        for t in tris:
            self.lines.append("f %s %s %s" % (corner(t[0]), corner(t[1]), corner(t[2])))
        for pl in polys:
            self.lines.append("f " + " ".join(corner(i) for i in pl))
        self.faces += len(tris) + len(polys)
        self.nv += len(pos)
        self.nvt += len(uv) if uv else 0
        self.nvn += len(nrm) if nrm else 0

    def add_raw(self, pos, uvs, nrms, faces):
        """Untuk sumber yang indeks UV / normalnya terpisah: faces = list list (vi, vti|None, vni|None) 0-based."""
        b0, t0, n0 = self.nv, self.nvt, self.nvn
        self.lines += ["v %.7g %.7g %.7g" % (p[0], p[1], p[2]) for p in pos]
        self.lines += ["vt %.7g %.7g" % (u[0], u[1]) for u in uvs]
        self.lines += ["vn %.7g %.7g %.7g" % (n[0], n[1], n[2]) for n in nrms]
        for f in faces:
            parts = []
            for vi, ti, ni in f:
                s = str(b0 + vi + 1)
                if ti is not None and ni is not None:
                    s += "/%d/%d" % (t0 + ti + 1, n0 + ni + 1)
                elif ti is not None:
                    s += "/%d" % (t0 + ti + 1)
                elif ni is not None:
                    s += "//%d" % (n0 + ni + 1)
                parts.append(s)
            self.lines.append("f " + " ".join(parts))
        self.faces += len(faces)
        self.nv += len(pos)
        self.nvt += len(uvs)
        self.nvn += len(nrms)

    def text(self, header="") -> str:
        return ("# %s\n" % header if header else "") + "\n".join(self.lines) + "\n"


def _csv_text(rows, header) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# glTF / GLB
# ---------------------------------------------------------------------------

_CT = {5120: ("b", 1, 127.0), 5121: ("B", 1, 255.0), 5122: ("h", 2, 32767.0), 5123: ("H", 2, 65535.0), 5125: ("I", 4, 1.0), 5126: ("f", 4, 1.0)}
_NT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def _is_glb(d, ext): return d[:4] == b"glTF" and len(d) >= 20
def _is_gltf(d, ext):
    return ext == ".gltf" and d[:1024].lstrip()[:1] == b"{"


def _gltf_load(d, p: Path):
    """-> (json, blok BIN GLB atau None). Melempar ValueError bila rusak."""
    binchunk = None
    if d[:4] == b"glTF":
        ver, total = struct.unpack_from("<II", d, 4)
        if ver != 2:
            raise ValueError("GLB versi %d tidak didukung (hanya 2)" % ver)
        pos, js = 12, None
        end = min(total, len(d))
        while pos + 8 <= end:
            ln, typ = struct.unpack_from("<I4s", d, pos)
            body = d[pos + 8:pos + 8 + ln]
            if typ == b"JSON":
                js = bytes(body)
            elif typ == b"BIN\x00" and binchunk is None:
                binchunk = bytes(body)
            pos += 8 + ln + ((4 - ln % 4) % 4)
        if js is None:
            raise ValueError("GLB tanpa chunk JSON")
    else:
        js = bytes(d)
    j = json.loads(js.decode("utf-8-sig"))
    if not isinstance(j, dict):
        raise ValueError("glTF bukan objek JSON")
    return j, binchunk


def _data_uri(uri: str):
    head, _, body = uri.partition(",")
    if ";base64" in head:
        return base64.b64decode(body + "=" * (-len(body) % 4))
    return urllib.parse.unquote_to_bytes(body)


def _external(p: Path, uri: str, cap=MAX_OUT_FILE):
    """Baca berkas eksternal (mis. .bin / .png di sebelah .gltf) hanya bila tetap di dalam folder yang sama."""
    base = p.resolve().parent
    q = (base / urllib.parse.unquote(uri)).resolve()
    if base != q and base not in q.parents:
        return None
    try:
        with open(q, "rb") as f:
            return f.read(cap)
    except OSError:
        return None


def _gltf_bufs(j, binchunk, p: Path):
    out = []
    for b in j.get("buffers", []) or []:
        uri = b.get("uri")
        try:
            if uri is None:
                out.append(binchunk or b"")
            elif uri.startswith("data:"):
                out.append(_data_uri(uri))
            else:
                out.append(_external(p, uri) or b"")
        except Exception:
            out.append(b"")
    return out


def _gltf_acc(j, bufs, idx):
    a = j["accessors"][idx]
    ct = a["componentType"]
    fc, sz, norm = _CT[ct]
    n, nc = int(a["count"]), _NT[a["type"]]
    if n > MAX_ACCESSOR:
        raise ValueError("accessor terlalu besar (%d)" % n)
    if "bufferView" not in a:
        return [tuple([0] * nc)] * n
    bv = j["bufferViews"][a["bufferView"]]
    buf = bufs[bv["buffer"]]
    off = int(bv.get("byteOffset", 0)) + int(a.get("byteOffset", 0))
    S = struct.Struct("<" + fc * nc)
    stride = int(bv.get("byteStride") or S.size)
    if n and off + stride * (n - 1) + S.size > len(buf):
        raise ValueError("accessor melewati batas buffer")
    rows = [S.unpack_from(buf, off + i * stride) for i in range(n)]
    if a.get("normalized") and ct != 5126:
        lo = -1.0 if fc in "bh" else 0.0
        rows = [tuple(max(lo, v / norm) for v in r) for r in rows]
    return rows


def _gltf_prim_tris(j, bufs, prim):
    mode = prim.get("mode", 4)
    pa = prim.get("attributes", {})
    if "POSITION" not in pa:
        return None
    nvert = j["accessors"][pa["POSITION"]]["count"]
    idx = [r[0] for r in _gltf_acc(j, bufs, prim["indices"])] if "indices" in prim else list(range(nvert))
    if mode == 4:
        return [(idx[i], idx[i + 1], idx[i + 2]) for i in range(0, len(idx) - 2, 3)]
    if mode == 5:
        return [((idx[i], idx[i + 1], idx[i + 2]) if i % 2 == 0 else (idx[i + 1], idx[i], idx[i + 2])) for i in range(len(idx) - 2)]
    if mode == 6:
        return [(idx[0], idx[i], idx[i + 1]) for i in range(1, len(idx) - 1)]
    return None


def _gltf_inspect(d, p):
    j, binc = _gltf_load(d, p)
    g = lambda k: j.get(k) or []
    L = []
    ast = j.get("asset", {})
    L.append("glTF %s | generator: %s" % (_as_clean(ast.get("version", "?")), _as_clean(ast.get("generator", "-"), 80)))
    nodes, meshes = g("nodes"), g("meshes")
    L.append("scene: %d | node: %d | mesh: %d | material: %d | tekstur: %d | gambar: %d | skin: %d | kamera: %d | animasi: %d" % (
        len(g("scenes")), len(nodes), len(meshes), len(g("materials")), len(g("textures")), len(g("images")), len(g("skins")),
        len(g("cameras")), len(g("animations"))))
    tv = tt = 0
    for mi, m in enumerate(meshes[:200]):
        v = t = 0
        for pr in m.get("primitives", []):
            try:
                v += j["accessors"][pr["attributes"]["POSITION"]]["count"]
                t += (j["accessors"][pr["indices"]]["count"] if "indices" in pr else j["accessors"][pr["attributes"]["POSITION"]]["count"]) // 3
            except (KeyError, IndexError, TypeError):
                pass
        tv, tt = tv + v, tt + t
        if mi < 12:
            L.append("  mesh[%d] %s: %d primitif, %d vertex, ~%d segitiga" % (mi, _as_clean(m.get("name", "-"), 40), len(m.get("primitives", [])), v, t))
    L.append("total: %d vertex, ~%d segitiga" % (tv, tt))
    for i, im in enumerate(g("images")[:10]):
        src = "bufferView" if "bufferView" in im else ("data URI" if str(im.get("uri", "")).startswith("data:") else _as_clean(im.get("uri", "?"), 60))
        L.append("  gambar[%d] %s (%s)" % (i, _as_clean(im.get("mimeType", "?"), 20), src))
    for i, sk in enumerate(g("skins")[:5]):
        L.append("  skin[%d]: %d joint" % (i, len(sk.get("joints", []))))
    for i, an in enumerate(g("animations")[:20]):
        dur = 0.0
        paths = collections.Counter()
        for c in an.get("channels", []):
            paths[c.get("target", {}).get("path", "?")] += 1
            try:
                s = an["samplers"][c["sampler"]]
                mx = j["accessors"][s["input"]].get("max")
                if mx:
                    dur = max(dur, float(mx[0]))
            except (KeyError, IndexError, TypeError, ValueError):
                pass
        L.append("  animasi[%d] %s: %d channel (%s), durasi %.2f dtk" % (
            i, _as_clean(an.get("name", "-"), 40), len(an.get("channels", [])), ", ".join("%s x%d" % kv for kv in paths.items()), dur))
    if j.get("extensionsUsed"):
        L.append("ekstensi dipakai: " + ", ".join(_as_clean(x, 40) for x in j["extensionsUsed"][:12]))
    if "KHR_draco_mesh_compression" in (j.get("extensionsRequired") or []) or "EXT_meshopt_compression" in (j.get("extensionsRequired") or []):
        L.append("PERINGATAN: mesh terkompresi (Draco / meshopt): ekspor OBJ tidak tersedia, gambar & animasi tetap bisa diekstrak.")
    return {"lines": L, "extract": "gambar tertanam, mesh -> .obj (tanpa transformasi node), animasi -> .json + .csv, scene.gltf.json"}


def _gltf_extract(d, p, out: _Out, opts):
    j, binc = _gltf_load(d, p)
    bufs = _gltf_bufs(j, binc, p)
    out.write_text("scene.gltf.json", json.dumps(j, ensure_ascii=False, indent=1), "json", "JSON glTF")
    # gambar
    for i, im in enumerate(j.get("images", []) or []):
        try:
            if "bufferView" in im:
                bv = j["bufferViews"][im["bufferView"]]
                off = int(bv.get("byteOffset", 0))
                data = bytes(bufs[bv["buffer"]][off:off + int(bv["byteLength"])])
            elif str(im.get("uri", "")).startswith("data:"):
                data = _data_uri(im["uri"])
            elif im.get("uri"):
                data = _external(p, im["uri"])
                if data is None:
                    out.skipped.append({"path": im["uri"], "reason": "berkas eksternal tidak ada / di luar folder"})
                    continue
            else:
                continue
            mt = im.get("mimeType", "")
            ext = ".png" if "png" in mt or data[:4] == b"\x89PNG" else ".jpg" if "jp" in mt or data[:2] == b"\xff\xd8" else ".bin"
            out.write("images/%s%s" % (_obj_name(im.get("name") or "image%d" % i), ext), data, "image")
        except Exception as e:
            out.errors.append("gambar[%d]: %s" % (i, _as_clean(e, 100)))
    # mesh
    for mi, m in enumerate(j.get("meshes", []) or []):
        try:
            ob = _ObjBuilder()
            for pi, pr in enumerate(m.get("primitives", [])):
                tris = _gltf_prim_tris(j, bufs, pr)
                if tris is None:
                    continue
                pa = pr["attributes"]
                pos = _gltf_acc(j, bufs, pa["POSITION"])
                uv = [(u[0], 1.0 - u[1]) for u in _gltf_acc(j, bufs, pa["TEXCOORD_0"])] if "TEXCOORD_0" in pa else None
                nrm = _gltf_acc(j, bufs, pa["NORMAL"]) if "NORMAL" in pa else None
                ob.group("%s_p%d" % (m.get("name") or "mesh%d" % mi, pi))
                ob.add(pos, uv, nrm, tris)
            if ob.faces:
                out.write_text("models/%s.obj" % _obj_name(m.get("name") or "mesh%d" % mi, "mesh%d" % mi),
                               ob.text("diekspor REA dari glTF mesh[%d]; tanpa transformasi node" % mi), "model3d",
                               "%d vertex, %d segitiga" % (ob.nv, ob.faces))
        except Exception as e:
            out.errors.append("mesh[%d]: %s" % (mi, _as_clean(e, 100)))
    # animasi
    nodes = j.get("nodes", []) or []
    nname = lambda i: _as_clean((nodes[i].get("name") if 0 <= (i if i is not None else -1) < len(nodes) else None) or "node%s" % i, 60)
    for ai, an in enumerate(j.get("animations", []) or []):
        try:
            chans, rows, width = [], [], 1
            for c in an.get("channels", []):
                s = an["samplers"][c["sampler"]]
                times = [r[0] for r in _gltf_acc(j, bufs, s["input"])]
                vals = _gltf_acc(j, bufs, s["output"])
                tg = c.get("target", {})
                nm, path = nname(tg.get("node")), tg.get("path", "?")
                interp = s.get("interpolation", "LINEAR")
                chans.append({"node": nm, "node_index": tg.get("node"), "path": path, "interpolation": interp,
                              "times": times, "values": [list(v) for v in vals]})
                if vals:
                    width = max(width, len(vals[0]))
                per = (len(vals) // len(times)) if times else 1
                for k, v in enumerate(vals):
                    rows.append((times[k // per] if per and k // per < len(times) else "", nm, path, interp, *v))
            base = "animations/%s" % _obj_name(an.get("name") or "anim%d" % ai, "anim%d" % ai)
            out.write_text(base + ".json", json.dumps({"name": an.get("name"), "channels": chans}, ensure_ascii=False), "animation",
                           "%d channel" % len(chans))
            out.write_text(base + ".csv", _csv_text(rows, ["time", "node", "path", "interpolation"] + ["v%d" % i for i in range(width)]), "animation",
                           "CUBICSPLINE: tiap kunci = 3 baris (in-tangent, nilai, out-tangent)" if any(c["interpolation"] == "CUBICSPLINE" for c in chans) else "")
        except Exception as e:
            out.errors.append("animasi[%d]: %s" % (ai, _as_clean(e, 100)))


register("glTF/GLB", "model3d", lambda d, e: _is_glb(d, e) or _is_gltf(d, e), _gltf_inspect, _gltf_extract, 10,
         "model 3D + animasi + tekstur tertanam")


# ---------------------------------------------------------------------------
# OBJ / STL / PLY
# ---------------------------------------------------------------------------

def _is_obj(d, e):
    if e != ".obj":
        return False
    head = bytes(d[:4096])
    return bool(re.search(rb"^(v|vt|vn|f|o|g|mtllib)\s", head, re.M))


def _obj_inspect(d, p):
    cnt = collections.Counter()
    mtl, groups = [], []
    for ln in bytes(d[:256 * 1024 * 1024]).split(b"\n"):
        t = ln.split(None, 1)
        if not t:
            continue
        k = t[0]
        if k in (b"v", b"vt", b"vn", b"vp", b"f", b"l", b"p", b"o", b"g", b"usemtl", b"s"):
            cnt[k.decode()] += 1
        if k == b"mtllib" and len(t) > 1 and len(mtl) < 5:
            mtl.append(_as_clean(t[1], 60))
        if k in (b"o", b"g") and len(t) > 1 and len(groups) < 10:
            groups.append(_as_clean(t[1], 40))
    L = ["Wavefront OBJ: %d vertex, %d UV, %d normal, %d face, %d objek, %d grup, %d pemakaian material" % (
        cnt["v"], cnt["vt"], cnt["vn"], cnt["f"], cnt["o"], cnt["g"], cnt["usemtl"])]
    if mtl:
        L.append("pustaka material: " + ", ".join(mtl))
    if groups:
        L.append("objek / grup: " + ", ".join(groups))
    return {"lines": L, "extract": "(sudah berupa OBJ; tidak ada yang perlu dikonversi)"}


register("OBJ", "model3d", _is_obj, _obj_inspect, None, 20, "Wavefront OBJ (teks)")


def _stl_kind(d):
    n = len(d)
    if n >= 84 and 84 + 50 * _u32(d, 80) == n:
        return "binary"
    head = bytes(d[:2048]).lstrip().lower()
    if head.startswith(b"solid") and b"facet" in bytes(d[:4096]).lower():
        return "ascii"
    return None


def _stl_tris(d):
    k = _stl_kind(d)
    if k == "binary":
        n = _u32(d, 80)
        if n > 20_000_000:
            raise ValueError("STL terlalu besar")
        S = struct.Struct("<12fH")
        return [S.unpack_from(d, 84 + 50 * i)[3:12] for i in range(n)]
    txt = bytes(d[:512 * 1024 * 1024]).decode("latin-1")
    vs = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)
    vs = [(float(a), float(b), float(c)) for a, b, c in vs]
    return [tuple(x for v in vs[i:i + 3] for x in v) for i in range(0, len(vs) - 2, 3)]


def _stl_inspect(d, p):
    k = _stl_kind(d)
    tris = _stl_tris(d)
    if not tris:
        return {"lines": ["STL (%s): kosong" % k]}
    xs = [t[i] for t in tris for i in (0, 3, 6)]
    ys = [t[i] for t in tris for i in (1, 4, 7)]
    zs = [t[i] for t in tris for i in (2, 5, 8)]
    L = ["STL %s: %d segitiga" % (k, len(tris)),
         "kotak batas: x[%.4g..%.4g] y[%.4g..%.4g] z[%.4g..%.4g]" % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))]
    if k == "binary":
        hd = _as_clean(bytes(d[:80]).rstrip(b"\x00 "), 80)
        if hd:
            L.append("header: " + hd)
    return {"lines": L, "extract": "-> .obj (vertex kembar digabung)"}


def _stl_extract(d, p, out, opts):
    tris = _stl_tris(d)
    index, pos, faces = {}, [], []
    for t in tris:
        f = []
        for i in (0, 3, 6):
            v = (t[i], t[i + 1], t[i + 2])
            if v not in index:
                index[v] = len(pos)
                pos.append(v)
            f.append(index[v])
        faces.append(tuple(f))
    ob = _ObjBuilder()
    ob.group(p.stem)
    ob.add(pos, None, None, faces)
    out.write_text("%s.obj" % _obj_name(p.stem, "model"), ob.text("diekspor REA dari STL"), "model3d", "%d vertex, %d segitiga" % (len(pos), len(faces)))


register("STL", "model3d", lambda d, e: _stl_kind(d) is not None if len(d) >= 84 or e == ".stl" else False, _stl_inspect, _stl_extract, 25,
         "model 3D segitiga (cetak 3D)")


_PLY_T = {"char": "b", "int8": "b", "uchar": "B", "uint8": "B", "short": "h", "int16": "h", "ushort": "H", "uint16": "H",
          "int": "i", "int32": "i", "uint": "I", "uint32": "I", "float": "f", "float32": "f", "double": "d", "float64": "d"}


def _ply_header(d):
    end = bytes(d[:65536]).find(b"end_header")
    if end < 0:
        raise ValueError("header PLY tidak lengkap")
    nl = bytes(d[end:end + 20])
    m = re.match(rb"end_header\r?\n", nl)
    if not m:
        raise ValueError("end_header tidak diikuti baris baru")
    body = end + m.end()
    lines = bytes(d[:end]).decode("latin-1").splitlines()
    if not lines or lines[0].strip() != "ply":
        raise ValueError("bukan PLY")
    fmt, elems, comments = None, [], []
    for ln in lines[1:]:
        t = ln.split()
        if not t:
            continue
        if t[0] == "format":
            fmt = t[1]
        elif t[0] == "comment":
            comments.append(_as_clean(" ".join(t[1:]), 80))
        elif t[0] == "element":
            elems.append({"name": t[1], "count": int(t[2]), "props": []})
        elif t[0] == "property" and elems:
            if t[1] == "list":
                elems[-1]["props"].append((t[4], "list", t[2], t[3]))
            else:
                elems[-1]["props"].append((t[2], "scalar", t[1], None))
    if fmt not in ("ascii", "binary_little_endian", "binary_big_endian"):
        raise ValueError("format PLY tidak dikenal")
    return fmt, elems, body, comments


def _ply_read(d):
    fmt, elems, pos, _ = _ply_header(d)
    data = {}
    if fmt == "ascii":
        toks = bytes(d[pos:]).split()
        ti = 0
        for el in elems:
            if el["count"] > 20_000_000:
                raise ValueError("elemen PLY terlalu besar")
            rows = []
            for _ in range(el["count"]):
                row = {}
                for name, kind, t1, t2 in el["props"]:
                    if kind == "list":
                        n = int(toks[ti]); ti += 1
                        row[name] = [float(x) if _PLY_T[t2] in "fd" else int(x) for x in toks[ti:ti + n]]
                        ti += n
                    else:
                        x = toks[ti]; ti += 1
                        row[name] = float(x) if _PLY_T[t1] in "fd" else int(x)
                rows.append(row)
            data[el["name"]] = rows
        return data
    e = "<" if fmt == "binary_little_endian" else ">"
    for el in elems:
        if el["count"] > 20_000_000:
            raise ValueError("elemen PLY terlalu besar")
        rows = []
        if all(k == "scalar" for _, k, _, _ in el["props"]):
            S = struct.Struct(e + "".join(_PLY_T[t1] for _, _, t1, _ in el["props"]))
            names = [n for n, _, _, _ in el["props"]]
            need = S.size * el["count"]
            if pos + need > len(d):
                raise ValueError("data PLY terpotong")
            for tup in S.iter_unpack(bytes(d[pos:pos + need])):
                rows.append(dict(zip(names, tup)))
            pos += need
        else:
            for _ in range(el["count"]):
                row = {}
                for name, kind, t1, t2 in el["props"]:
                    if kind == "list":
                        c = struct.unpack_from(e + _PLY_T[t1], d, pos)[0]
                        pos += struct.calcsize(_PLY_T[t1])
                        fc = _PLY_T[t2]
                        row[name] = list(struct.unpack_from("%s%d%s" % (e, c, fc), d, pos))
                        pos += c * struct.calcsize(fc)
                    else:
                        fc = _PLY_T[t1]
                        row[name] = struct.unpack_from(e + fc, d, pos)[0]
                        pos += struct.calcsize(fc)
                rows.append(row)
        data[el["name"]] = rows
    return data


def _ply_inspect(d, p):
    fmt, elems, _, comments = _ply_header(d)
    L = ["PLY (%s): " % fmt + ", ".join("%s x%d [%s]" % (_as_clean(e["name"], 20), e["count"], ", ".join(_as_clean(x[0], 14) for x in e["props"][:8])) for e in elems)]
    if comments:
        L.append("komentar: " + "; ".join(comments[:3]))
    return {"lines": L, "extract": "-> .obj (vertex + face; warna per-vertex tidak ikut)"}


def _ply_extract(d, p, out, opts):
    data = _ply_read(d)
    vs = data.get("vertex", [])
    pos = [(v.get("x", 0.0), v.get("y", 0.0), v.get("z", 0.0)) for v in vs]
    nrm = [(v["nx"], v["ny"], v["nz"]) for v in vs] if vs and "nx" in vs[0] else None
    uv = None
    for a, b in (("s", "t"), ("u", "v"), ("texture_u", "texture_v")):
        if vs and a in vs[0] and b in vs[0]:
            uv = [(v[a], v[b]) for v in vs]
            break
    polys = []
    for f in data.get("face", []):
        ix = f.get("vertex_indices") or f.get("vertex_index") or []
        if len(ix) >= 3:
            polys.append([int(i) for i in ix])
    ob = _ObjBuilder()
    ob.group(p.stem)
    ob.add(pos, uv, nrm, (), polys)
    out.write_text("%s.obj" % _obj_name(p.stem, "model"), ob.text("diekspor REA dari PLY"), "model3d", "%d vertex, %d face" % (len(pos), len(polys)))


register("PLY", "model3d", lambda d, e: d[:4] == b"ply\n" or d[:5] == b"ply\r\n", _ply_inspect, _ply_extract, 25, "Stanford PLY (mesh / point cloud)")


# ---------------------------------------------------------------------------
# FBX (biner) - model, rangka, animasi, tekstur tertanam
# ---------------------------------------------------------------------------

_FBX_MAGIC = b"Kaydara FBX Binary  \x00\x1a\x00"
_FBX_TICKS = 46186158000.0          # tick FBX per detik
_ARR = {ord("f"): ("f", 4), ord("d"): ("d", 8), ord("l"): ("q", 8), ord("i"): ("i", 4), ord("b"): ("B", 1)}


def _fbx_props(d, pos, n):
    props = []
    for _ in range(n):
        t = d[pos]
        pos += 1
        if t == 0x59:   # Y
            v = struct.unpack_from("<h", d, pos)[0]; pos += 2
        elif t == 0x43:   # C
            v = d[pos]; pos += 1
        elif t == 0x49:   # I
            v = struct.unpack_from("<i", d, pos)[0]; pos += 4
        elif t == 0x46:   # F
            v = struct.unpack_from("<f", d, pos)[0]; pos += 4
        elif t == 0x44:   # D
            v = struct.unpack_from("<d", d, pos)[0]; pos += 8
        elif t == 0x4C:   # L
            v = struct.unpack_from("<q", d, pos)[0]; pos += 8
        elif t in _ARR:
            al, enc, cl = struct.unpack_from("<III", d, pos)
            pos += 12
            code, isz = _ARR[t]
            want = al * isz
            if want > MAX_OUT_FILE:
                raise ValueError("array FBX terlalu besar")
            raw = bytes(d[pos:pos + cl])
            pos += cl
            if enc == 1:
                raw = zlib.decompressobj().decompress(raw, want + 1)
            if len(raw) != want:
                raise ValueError("panjang array FBX tidak cocok")
            if code == "B":
                v = raw
            else:
                v = array.array(code)
                v.frombytes(raw)
                if sys.byteorder == "big":
                    v.byteswap()
        elif t in (0x53, 0x52):   # S / R
            ln = _u32(d, pos); pos += 4
            raw = bytes(d[pos:pos + ln]); pos += ln
            v = raw.decode("utf-8", "replace") if t == 0x53 else raw
        else:
            raise ValueError("tipe properti FBX tidak dikenal: %r" % t)
        props.append(v)
    return props


def _fbx_parse(d, node_cap=3_000_000):
    ver = _u32(d, 23)
    big = ver >= 7500
    cnt = [0]

    def node(pos, depth):
        if big:
            end, npr, pl = struct.unpack_from("<QQQ", d, pos); pos += 24
        else:
            end, npr, pl = struct.unpack_from("<III", d, pos); pos += 12
        nl = d[pos]; pos += 1
        if end == 0:
            return None, pos
        if depth > 48 or end > len(d):
            raise ValueError("struktur FBX tidak wajar")
        cnt[0] += 1
        if cnt[0] > node_cap:
            raise ValueError("terlalu banyak node FBX")
        name = bytes(d[pos:pos + nl]).decode("latin-1")
        pos += nl
        pstart = pos
        props = _fbx_props(d, pstart, npr)
        pos = pstart + pl      # panjang daftar properti dipercaya dari header
        kids = []
        while pos < end:
            ch, pos = node(pos, depth + 1)
            if ch is not None:
                kids.append(ch)
        return (name, props, kids), end

    tops, pos = [], 27
    while pos + (25 if big else 13) <= len(d):
        n, pos = node(pos, 0)
        if n is None:
            break
        tops.append(n)
    return ver, tops


def _fbx_child(n, name):
    for c in n[2]:
        if c[0] == name:
            return c
    return None


def _fbx_cname(n) -> str:
    s = n[1][1] if len(n[1]) > 1 and isinstance(n[1][1], str) else ""
    return _as_clean(s.split("\x00\x01")[0] or "unnamed", 60)


def _fbx_objects(tops):
    ob = next((t for t in tops if t[0] == "Objects"), None)
    return ob[2] if ob else []


def _is_fbx_bin(d, e): return d[:23] == _FBX_MAGIC


def _is_fbx_ascii(d, e): return d[:12] == b"; FBX " or (e == ".fbx" and b"FBXHeaderExtension" in bytes(d[:512]))


def _fbx_inspect(d, p):
    ver, tops = _fbx_parse(d)
    objs = _fbx_objects(tops)
    kinds = collections.Counter(o[0] for o in objs)
    models = collections.Counter((o[1][2] if len(o[1]) > 2 and isinstance(o[1][2], str) else "?") for o in objs if o[0] == "Model")
    L = ["FBX biner versi %d | objek: %s" % (ver, ", ".join("%s x%d" % kv for kv in kinds.most_common(14)))]
    if models:
        L.append("tipe Model: " + ", ".join("%s x%d" % (_as_clean(k, 20), v) for k, v in models.most_common(8)))
    nv = nf = 0
    for o in objs:
        if o[0] == "Geometry":
            v = _fbx_child(o, "Vertices")
            pv = _fbx_child(o, "PolygonVertexIndex")
            if v and v[1]:
                nv += len(v[1][0]) // 3
            if pv and pv[1]:
                nf += sum(1 for x in pv[1][0] if x < 0)
    if nv:
        L.append("geometri: %d vertex, %d poligon" % (nv, nf))
    bones = [_fbx_cname(o) for o in objs if o[0] == "Model" and len(o[1]) > 2 and o[1][2] == "LimbNode"]
    if bones:
        L.append("rangka: %d tulang (%s%s)" % (len(bones), ", ".join(bones[:8]), ", ..." if len(bones) > 8 else ""))
    curves = [o for o in objs if o[0] == "AnimationCurve"]
    if curves:
        keys, tmax = 0, 0
        for c in curves:
            kt = _fbx_child(c, "KeyTime")
            if kt and kt[1] and len(kt[1][0]):
                keys += len(kt[1][0]); tmax = max(tmax, max(kt[1][0]))
        L.append("animasi: %d stack, %d layer, %d curve, %d kunci, durasi ~%.2f dtk" % (
            kinds["AnimationStack"], kinds["AnimationLayer"], len(curves), keys, tmax / _FBX_TICKS))
    emb = 0
    for o in objs:
        if o[0] == "Video":
            c = _fbx_child(o, "Content")
            if c and c[1] and isinstance(c[1][0], (bytes, bytearray)) and len(c[1][0]) > 0:
                emb += 1
    if kinds["Texture"] or kinds["Video"]:
        L.append("tekstur: %d referensi, %d gambar tertanam" % (kinds["Texture"], emb))
    return {"lines": L, "extract": "geometri -> .obj (+UV / normal ByPolygonVertex), animasi -> .csv per curve, gambar tertanam"}


def _fbx_extract(d, p, out, opts):
    ver, tops = _fbx_parse(d)
    objs = _fbx_objects(tops)
    byid = {o[1][0]: o for o in objs if o[1] and isinstance(o[1][0], int)}
    for o in objs:
        if o[0] == "Geometry":
            try:
                vn, pv = _fbx_child(o, "Vertices"), _fbx_child(o, "PolygonVertexIndex")
                if not vn or not pv or not vn[1] or not pv[1]:
                    continue
                vv, pi = vn[1][0], pv[1][0]
                pos = [(vv[i], vv[i + 1], vv[i + 2]) for i in range(0, len(vv) - 2, 3)]
                polys, cur = [], []
                for k, ix in enumerate(pi):
                    cur.append((ix if ix >= 0 else ~ix, k))
                    if ix < 0:
                        polys.append(cur)
                        cur = []

                def layer(lname, dname, iname):
                    le = _fbx_child(o, lname)
                    if not le:
                        return None, None
                    mt = _fbx_child(le, "MappingInformationType")
                    dd = _fbx_child(le, dname)
                    ii = _fbx_child(le, iname)
                    if not dd or not dd[1] or not mt or "ByPolygonVertex" not in str(mt[1][:1]):
                        return None, None
                    return dd[1][0], (ii[1][0] if ii and ii[1] else None)
                uvd, uvi = layer("LayerElementUV", "UV", "UVIndex")
                nmd, _ = layer("LayerElementNormal", "Normals", "NormalsIndex")
                uvs = [(uvd[i], uvd[i + 1]) for i in range(0, len(uvd) - 1, 2)] if uvd is not None else []
                nms = [(nmd[i], nmd[i + 1], nmd[i + 2]) for i in range(0, len(nmd) - 2, 3)] if nmd is not None else []
                faces = []
                for pl in polys:
                    f = []
                    for vi, k in pl:
                        ti = (uvi[k] if uvi is not None and k < len(uvi) else k) if uvs else None
                        if ti is not None and ti >= len(uvs):
                            ti = None
                        ni = k if nms and k < len(nms) else None
                        f.append((vi, ti, ni))
                    if len(f) >= 3:
                        faces.append(f)
                ob = _ObjBuilder()
                ob.group(_fbx_cname(o))
                ob.add_raw(pos, uvs, nms, faces)
                out.write_text("models/%s.obj" % _obj_name(_fbx_cname(o), "geometry"), ob.text("diekspor REA dari FBX"), "model3d",
                               "%d vertex, %d poligon" % (len(pos), len(faces)))
            except Exception as e:
                out.errors.append("geometri %s: %s" % (_fbx_cname(o), _as_clean(e, 100)))
        elif o[0] == "Video":
            c = _fbx_child(o, "Content")
            if c and c[1] and isinstance(c[1][0], (bytes, bytearray)) and len(c[1][0]) > 0:
                fn = _fbx_child(o, "RelativeFilename") or _fbx_child(o, "Filename")
                nm = os.path.basename(str(fn[1][0]).replace("\\", "/")) if fn and fn[1] else _fbx_cname(o)
                out.write("images/" + (nm or "video"), bytes(c[1][0]), "image", "tekstur tertanam FBX")
    # animasi: curve -> curvenode -> model lewat tabel Connections
    conn = next((t for t in tops if t[0] == "Connections"), None)
    parent = collections.defaultdict(list)
    if conn:
        for c in conn[2]:
            if c[0] == "C" and len(c[1]) >= 3 and c[1][0] in ("OO", "OP"):
                parent[c[1][1]].append((c[1][2], c[1][3] if len(c[1]) > 3 else ""))
    rows_by_node = collections.defaultdict(list)
    for o in objs:
        if o[0] != "AnimationCurve":
            continue
        try:
            kt, kv = _fbx_child(o, "KeyTime"), _fbx_child(o, "KeyValueFloat")
            if not kt or not kv or not kt[1] or not kv[1]:
                continue
            axis, node_name, prop = "?", "?", "?"
            for pid, pname in parent.get(o[1][0], []):
                cn = byid.get(pid)
                if cn and cn[0] == "AnimationCurveNode":
                    axis = str(pname).replace("d|", "")
                    for mid, mprop in parent.get(pid, []):
                        m = byid.get(mid)
                        if m and m[0] == "Model":
                            node_name, prop = _fbx_cname(m), str(mprop)
            for t, v in zip(kt[1][0], kv[1][0]):
                rows_by_node[node_name].append((node_name, prop, axis, "%.6f" % (t / _FBX_TICKS), "%.7g" % v))
        except Exception as e:
            out.errors.append("curve: %s" % _as_clean(e, 100))
    for nm, rows in rows_by_node.items():
        out.write_text("animations/%s.csv" % _obj_name(nm, "node"), _csv_text(rows, ["node", "property", "axis", "time_s", "value"]), "animation",
                       "%d sampel" % len(rows))


register("FBX", "model3d", _is_fbx_bin, _fbx_inspect, _fbx_extract, 10, "Autodesk FBX biner: mesh, rangka, animasi, tekstur")


def _fbx_ascii_inspect(d, p):
    txt = bytes(d[:64 * 1024 * 1024]).decode("latin-1")
    c = {k: len(re.findall(r"^\s*%s:" % k, txt, re.M)) for k in ("Model", "Geometry", "Material", "Texture", "AnimationStack", "AnimationCurve", "Deformer")}
    return {"lines": ["FBX ASCII: " + ", ".join("%s x%d" % kv for kv in c.items() if kv[1]), "ekstraksi untuk FBX ASCII belum ada; konversi ke FBX biner / glTF dulu."]}


register("FBX-ASCII", "model3d", _is_fbx_ascii, _fbx_ascii_inspect, None, 11, "FBX teks (hanya ringkasan)")


# ---------------------------------------------------------------------------
# COLLADA (.dae)
# ---------------------------------------------------------------------------

def _tag(e): return e.tag.rsplit("}", 1)[-1]


def _is_dae(d, e):
    return e == ".dae" or (b"<COLLADA" in bytes(d[:2048]))


def _dae_root(d):
    if len(d) > MAX_XML:
        raise ValueError("XML terlalu besar")
    raw = bytes(d)
    if b"<!ENTITY" in raw or b"<!DOCTYPE" in raw[:4096] and b"[" in raw[:4096].split(b"<!DOCTYPE", 1)[1][:2000]:
        raise ValueError("XML berisi DTD / entity (ditolak demi keamanan)")
    return ET.fromstring(raw)


def _dae_floats(e):
    return [float(x) for x in (e.text or "").split()]


def _dae_inspect(d, p):
    r = _dae_root(d)
    c = collections.Counter(_tag(e) for e in r.iter())
    L = ["COLLADA: %d geometri, %d controller (skin), %d animasi, %d gambar, %d material, %d node" % (
        c["geometry"], c["controller"], c["animation"], c["image"], c["material"], c["node"])]
    ax = next((e.text for e in r.iter() if _tag(e) == "up_axis"), None)
    un = next((e for e in r.iter() if _tag(e) == "unit"), None)
    if ax or un is not None:
        L.append("sumbu atas: %s | unit: %s" % (_as_clean(ax or "?", 8), _as_clean(un.get("meter", "?") if un is not None else "?", 12)))
    imgs = [(e.text or "").strip() for e in r.iter() if _tag(e) == "init_from" and (e.text or "").strip()][:8]
    if imgs:
        L.append("gambar dirujuk: " + ", ".join(_as_clean(i, 50) for i in imgs))
    return {"lines": L, "extract": "geometri (triangles / polylist) -> .obj; kurva animasi (sampler / channel) -> animations/*.csv + animations.json"}


def _dae_extract(d, p, out, opts):
    r = _dae_root(d)
    for geom in [e for e in r.iter() if _tag(e) == "geometry"]:
        mesh = next((e for e in geom if _tag(e) == "mesh"), None)
        if mesh is None:
            continue
        try:
            src = {}
            for s in mesh:
                if _tag(s) == "source":
                    fa = next((e for e in s.iter() if _tag(e) == "float_array"), None)
                    ac = next((e for e in s.iter() if _tag(e) == "accessor"), None)
                    if fa is not None:
                        src[s.get("id")] = (_dae_floats(fa), int(ac.get("stride", 3)) if ac is not None else 3)
            vmap = {}
            for v in mesh:
                if _tag(v) == "vertices":
                    for i in v:
                        if _tag(i) == "input" and i.get("semantic") == "POSITION":
                            vmap[v.get("id")] = i.get("source", "")[1:]
            chunk = lambda fl, st: [tuple(fl[i:i + st]) for i in range(0, len(fl) - st + 1, st)]
            ob = _ObjBuilder()
            ob.group(geom.get("name") or geom.get("id"))
            pos = uvs = nrm = None
            faces = []
            for prim in mesh:
                if _tag(prim) not in ("triangles", "polylist", "polygons"):
                    continue
                inputs = [i for i in prim if _tag(i) == "input"]
                stride = max(int(i.get("offset", 0)) for i in inputs) + 1 if inputs else 0
                off = {}
                for i in inputs:
                    sem, o, sid = i.get("semantic"), int(i.get("offset", 0)), i.get("source", "")[1:]
                    if sem == "VERTEX":
                        fl, st = src[vmap[sid]]; pos = chunk(fl, st); off["v"] = o
                    elif sem == "NORMAL" and "n" not in off:
                        fl, st = src[sid]; nrm = chunk(fl, st); off["n"] = o
                    elif sem == "TEXCOORD" and "t" not in off:
                        fl, st = src[sid]; uvs = [(a[0], a[1]) for a in chunk(fl, st)]; off["t"] = o
                ps = [[int(x) for x in (e.text or "").split()] for e in prim if _tag(e) == "p"]
                if "v" not in off or not ps:
                    continue
                if _tag(prim) == "triangles":
                    vc = [3] * int(prim.get("count", 0)); flat = ps[0]
                elif _tag(prim) == "polylist":
                    vcn = next((e for e in prim if _tag(e) == "vcount"), None)
                    vc = [int(x) for x in (vcn.text or "").split()]; flat = ps[0]
                else:
                    vc, flat = [], []
                    for pp in ps:
                        vc.append(len(pp) // stride); flat += pp
                k = 0
                for n in vc:
                    f = []
                    for _ in range(n):
                        row = flat[k * stride:(k + 1) * stride]; k += 1
                        f.append((row[off["v"]], row[off["t"]] if "t" in off else None, row[off["n"]] if "n" in off else None))
                    if len(f) >= 3:
                        faces.append(f)
            if pos and faces:
                ob.add_raw(pos, uvs or [], nrm or [], faces)
                out.write_text("models/%s.obj" % _obj_name(geom.get("name") or geom.get("id"), "geometry"), ob.text("diekspor REA dari COLLADA"),
                               "model3d", "%d vertex, %d face" % (len(pos), len(faces)))
        except Exception as e:
            out.errors.append("geometri %s: %s" % (_as_clean(geom.get("id"), 40), _as_clean(e, 100)))
    try:
        _dae_anim_export(r, out)
    except Exception as e:
        out.errors.append("animasi: %s" % _as_clean(e, 100))


DAE_ANIM_MAX_VALUES = 2_000_000   # total angka kurva animasi yang diekspor per berkas
DAE_ANIM_MAX_CHANNELS = 2000


def _dae_anim_export(r, out) -> None:
    """v99.16: kurva animasi COLLADA (sampler / channel) -> animations/NNN_<target>.csv (satu per channel) + animations/animations.json (semua channel).
    Hanya kunci waktu + nilai mentah (stride 1 = skalar, 16 = matriks 4x4); interpolasi ikut jika ada. Tidak ada evaluasi / retargeting."""
    srcs = {}
    for e in r.iter():
        if _tag(e) != "source" or not e.get("id"):
            continue
        fa = next((x for x in e.iter() if _tag(x) in ("float_array", "Name_array", "IDREF_array")), None)
        if fa is None:
            continue
        ac = next((x for x in e.iter() if _tag(x) == "accessor"), None)
        try:
            st = max(1, int(ac.get("stride", 1))) if ac is not None else 1
        except ValueError:
            st = 1
        srcs[e.get("id")] = (_tag(fa), (fa.text or "").split(), st)
    chans = []
    for an in [e for e in r.iter() if _tag(e) == "animation"]:
        samp = {}
        for sm in [e for e in an if _tag(e) == "sampler"]:
            samp[sm.get("id")] = {i.get("semantic"): (i.get("source") or "")[1:] for i in sm if _tag(i) == "input"}
        for ch in [e for e in an if _tag(e) == "channel"]:
            sid = (ch.get("source") or "")[1:]
            if sid in samp:
                chans.append((ch.get("target") or "?", samp[sid], an.get("name") or an.get("id") or "anim"))
    if not chans:
        return
    total = 0
    js = []
    for i, (target, inp, an_name) in enumerate(chans[:DAE_ANIM_MAX_CHANNELS]):
        try:
            ti, vo = srcs.get(inp.get("INPUT")), srcs.get(inp.get("OUTPUT"))
            if not ti or not vo or ti[0] != "float_array" or vo[0] != "float_array":
                raise ValueError("sampler tanpa INPUT / OUTPUT float_array")
            times = [float(x) for x in ti[1]]
            st = vo[2]
            n = len(times)
            vals = [float(x) for x in vo[1]]
            if n == 0 or len(vals) < n * st:
                raise ValueError("jumlah nilai tidak cocok (%d kunci, stride %d, %d nilai)" % (n, st, len(vals)))
            total += n * (st + 1)
            if total > DAE_ANIM_MAX_VALUES:
                out.errors.append("animasi: batas %d angka tercapai; channel sisanya dilewati" % DAE_ANIM_MAX_VALUES)
                break
            it = srcs.get(inp.get("INTERPOLATION"))
            interp = it[1] if it and it[0] == "Name_array" and len(it[1]) == n else None
            cols = ["time_s"] + (["value"] if st == 1 else ["m%d" % k for k in range(st)] if st == 16 else ["v%d" % k for k in range(st)])
            rows = [("%.6g" % times[k],) + tuple("%.6g" % x for x in vals[k * st:(k + 1) * st]) + ((_as_clean(interp[k], 16),) if interp else ()) for k in range(n)]
            if interp:
                cols.append("interp")
            nm = _obj_name(target.replace("/", "_"), "channel")
            out.write_text("animations/%03d_%s.csv" % (i, nm), _csv_text(rows, cols), "animation", "%d kunci, stride %d" % (n, st))
            js.append({"animation": _as_clean(an_name, 60), "target": _as_clean(target, 120), "stride": st, "times": times[:n],
                       "values": [vals[k * st:(k + 1) * st] for k in range(n)], "interpolation": interp})
        except Exception as e:
            out.errors.append("animasi %s: %s" % (_as_clean(target, 50), _as_clean(e, 100)))
    if js:
        out.write_text("animations/animations.json", json.dumps({"source": "COLLADA", "channels": js}, separators=(",", ":")), "animation", "%d channel" % len(js))


register("COLLADA", "model3d", _is_dae, _dae_inspect, _dae_extract, 30, "COLLADA .dae (XML)")


# ---------------------------------------------------------------------------
# BVH (motion capture)
# ---------------------------------------------------------------------------

def _is_bvh(d, e): return bytes(d[:16]).lstrip().startswith(b"HIERARCHY")


def _bvh_parse(d):
    txt = bytes(d[:512 * 1024 * 1024]).decode("latin-1")
    hi, _, mo = txt.partition("MOTION")
    if not mo:
        raise ValueError("BVH tanpa bagian MOTION")
    cols, joints = [], []
    cur = None
    for ln in hi.splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] in ("ROOT", "JOINT") and len(t) > 1:
            cur = _as_clean(t[1], 40); joints.append(cur)
        elif t[0] == "End":
            cur = None
        elif t[0] == "CHANNELS" and cur:
            n = int(t[1])
            cols += ["%s.%s" % (cur, c) for c in t[2:2 + n]]
    lines = mo.strip().splitlines()
    frames = int(lines[0].split(":")[1])
    ft = float(lines[1].split(":")[1])
    data = [[float(x) for x in ln.split()] for ln in lines[2:2 + frames] if ln.strip()]
    return joints, cols, frames, ft, data


def _bvh_inspect(d, p):
    joints, cols, frames, ft, data = _bvh_parse(d)
    return {"lines": ["BVH: %d joint, %d kanal, %d frame @ %.1f fps (durasi %.2f dtk)" % (len(joints), len(cols), frames, 1 / ft if ft else 0, frames * ft),
                      "joint: " + ", ".join(joints[:12]) + (", ..." if len(joints) > 12 else "")], "extract": "-> .csv (satu kolom per kanal)"}


def _bvh_extract(d, p, out, opts):
    joints, cols, frames, ft, data = _bvh_parse(d)
    rows = [("%d" % i, "%.5f" % (i * ft)) + tuple("%.6g" % x for x in r) for i, r in enumerate(data)]
    out.write_text("%s.csv" % _obj_name(p.stem, "motion"), _csv_text(rows, ["frame", "time_s"] + cols), "animation", "%d frame" % len(rows))


register("BVH", "animation", _is_bvh, _bvh_inspect, _bvh_extract, 20, "motion capture BVH")


# ---------------------------------------------------------------------------
# Gambar
# ---------------------------------------------------------------------------

def _png_encode(w: int, h: int, rgba) -> bytes:
    """RGBA 8-bit -> PNG. rgba: bytes / bytearray panjang w*h*4."""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")


_PNG_CT = {0: "grayscale", 2: "RGB", 3: "palet", 4: "grayscale+alfa", 6: "RGBA"}


def _png_walk(d):
    pos, chunks = 8, []
    while pos + 12 <= len(d) and len(chunks) < 100_000:
        ln = _b32(d, pos)
        typ = bytes(d[pos + 4:pos + 8])
        chunks.append((typ, pos + 8, ln))
        pos += 12 + ln
        if typ == b"IEND":
            break
    return chunks, pos


def _png_inspect(d, p):
    w, h, bd, ct, _, _, il = struct.unpack_from(">IIBBBBB", d, 16)
    chunks, end = _png_walk(d)
    names = collections.Counter(c[0] for c in chunks)
    L = ["PNG %dx%d, %d-bit %s%s" % (w, h, bd, _PNG_CT.get(ct, "?"), ", interlaced" if il else "")]
    if names[b"acTL"]:
        o = next(c[1] for c in chunks if c[0] == b"acTL")
        L.append("APNG animasi: %d frame, ulang %s" % (_b32(d, o), _b32(d, o + 4) or "tanpa batas"))
    txt = []
    for t, o, ln in chunks:
        if t == b"tEXt" and len(txt) < 6:
            k = bytes(d[o:o + min(ln, 80)]).split(b"\x00")[0]
            txt.append(_as_clean(k, 30))
    if txt:
        L.append("teks metadata: " + ", ".join(txt))
    if names[b"eXIf"]:
        L.append("memuat EXIF")
    if end < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah IEND (kemungkinan data tersembunyi / arsip tertanam)" % (len(d) - end))
    return {"lines": L}


register("PNG", "image", lambda d, e: d[:8] == b"\x89PNG\r\n\x1a\n" and len(d) >= 33, _png_inspect, None, 15, "PNG / APNG")


def _jpeg_inspect(d, p):
    pos, L, info = 2, [], {}
    while pos + 4 <= len(d) and d[pos] == 0xFF:
        m = d[pos + 1]
        if m == 0xFF:
            pos += 1; continue
        if m == 0xD9 or m == 0xDA:
            break
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        ln = struct.unpack_from(">H", d, pos + 2)[0]
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            prec, h, w, nc = struct.unpack_from(">BHHB", d, pos + 4)
            info.update(w=w, h=h, comps=nc, prog=m in (0xC2, 0xC6, 0xCA, 0xCE), prec=prec)
        elif m == 0xE1 and bytes(d[pos + 4:pos + 10]) == b"Exif\x00\x00":
            info["exif"] = True
        elif m == 0xE0 and bytes(d[pos + 4:pos + 9]) == b"JFIF\x00":
            info["jfif"] = True
        elif m == 0xFE:
            info["comment"] = _as_clean(d[pos + 4:pos + 2 + ln], 80)
        pos += 2 + ln
    L.append("JPEG %sx%s, %s komponen, %s%s%s" % (info.get("w", "?"), info.get("h", "?"), info.get("comps", "?"), "progresif" if info.get("prog") else "baseline",
                                              ", EXIF" if info.get("exif") else "", ", JFIF" if info.get("jfif") else ""))
    if info.get("comment"):
        L.append("komentar: " + info["comment"])
    ln = _jpeg_len(d, 0)
    if ln and ln < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah EOI" % (len(d) - ln))
    return {"lines": L}


def _jpeg_len(d, start):
    pos, n = start + 2, len(d)
    while pos + 4 <= n:
        if d[pos] != 0xFF:
            return None
        m = d[pos + 1]
        if m == 0xD9:
            return pos + 2 - start
        if m == 0xFF:
            pos += 1; continue
        if m == 0x01 or 0xD0 <= m <= 0xD7:
            pos += 2; continue
        pos += 2 + struct.unpack_from(">H", d, pos + 2)[0]
        if m == 0xDA:
            p = pos
            while True:
                i = d.find(b"\xff", p)
                if i < 0 or i + 1 >= n:
                    return None
                nb = d[i + 1]
                if nb == 0 or 0xD0 <= nb <= 0xD7:
                    p = i + 2; continue
                pos = i
                break
    return None


register("JPEG", "image", lambda d, e: d[:3] == b"\xff\xd8\xff", _jpeg_inspect, None, 15, "JPEG")


def _gif_walk(d, start=0):
    if bytes(d[start:start + 4]) != b"GIF8" or bytes(d[start + 5:start + 6]) != b"a":
        raise ValueError("bukan GIF")
    w, h, fl = struct.unpack_from("<HHB", d, start + 6)
    pos = start + 13
    if fl & 0x80:
        pos += 3 * (2 << (fl & 7))
    frames = delay = 0
    loops = None
    n = len(d)

    def skip_sub(p):
        while p < n:
            ln = d[p]
            p += 1
            if ln == 0:
                return p
            p += ln
        raise ValueError("GIF terpotong")
    while pos < n:
        b = d[pos]
        if b == 0x3B:
            return {"w": w, "h": h, "frames": frames, "delay_cs": delay, "loops": loops, "end": pos + 1 - start}
        if b == 0x21:
            lab = d[pos + 1]
            if lab == 0xF9 and pos + 6 <= n:
                delay += _u16(d, pos + 4)
            if lab == 0xFF and bytes(d[pos + 3:pos + 14]) == b"NETSCAPE2.0" and pos + 18 <= n:
                loops = _u16(d, pos + 16)
            pos = skip_sub(pos + 2)
        elif b == 0x2C:
            fl2 = d[pos + 9]
            pos += 10
            if fl2 & 0x80:
                pos += 3 * (2 << (fl2 & 7))
            pos = skip_sub(pos + 1)
            frames += 1
        else:
            raise ValueError("blok GIF tidak dikenal")
    raise ValueError("GIF tanpa trailer")


def _gif_inspect(d, p):
    g = _gif_walk(d)
    L = ["GIF %dx%d, %d frame%s" % (g["w"], g["h"], g["frames"], ", durasi %.2f dtk" % (g["delay_cs"] / 100) if g["frames"] > 1 else "")]
    if g["loops"] is not None:
        L.append("ulang: %s" % (g["loops"] or "tanpa batas"))
    if g["end"] < len(d):
        L.append("PERHATIAN: %d byte data tambahan setelah trailer GIF" % (len(d) - g["end"]))
    return {"lines": L}


register("GIF", "image", lambda d, e: d[:4] == b"GIF8" and d[5:6] == b"a", _gif_inspect, None, 15, "GIF (animasi)")


def _webp_inspect(d, p):
    pos, L, flags = 12, [], 0
    w = h = frames = 0
    kind = "?"
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        b = pos + 8
        if t == b"VP8X":
            flags = d[b]; w = int.from_bytes(d[b + 4:b + 7], "little") + 1; h = int.from_bytes(d[b + 7:b + 10], "little") + 1; kind = "VP8X"
        elif t == b"VP8 " and not w:
            w, h = _u16(d, b + 6) & 0x3FFF, _u16(d, b + 8) & 0x3FFF; kind = "lossy"
        elif t == b"VP8L" and not w:
            v = _u32(d, b + 1); w, h = (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1; kind = "lossless"
        elif t == b"ANMF":
            frames += 1
        pos = b + ln + (ln & 1)
    L.append("WebP %dx%d (%s)%s%s" % (w, h, kind, ", animasi %d frame" % frames if flags & 2 else "", ", alfa" if flags & 0x10 else ""))
    return {"lines": L}


register("WebP", "image", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WEBP", _webp_inspect, None, 14, "WebP")


def _ico_inspect(d, p):
    n = _u16(d, 4)
    L = ["%s: %d gambar" % ("ICO" if _u16(d, 2) == 1 else "CUR", n)]
    for i in range(min(n, 12)):
        w, h = d[6 + 16 * i] or 256, d[7 + 16 * i] or 256
        L.append("  %dx%d, %d-bit, %s" % (w, h, _u16(d, 12 + 16 * i), _as_human(_u32(d, 14 + 16 * i))))
    return {"lines": L}


register("ICO", "image", lambda d, e: len(d) >= 22 and d[:2] == b"\x00\x00" and d[2:4] in (b"\x01\x00", b"\x02\x00") and 0 < _u16(d, 4) < 256 and e in (".ico", ".cur"),
         _ico_inspect, None, 40, "ikon Windows")


# --- BMP ---

def _bmp_decode(d):
    off = _u32(d, 10)
    hs = _u32(d, 14)
    if hs < 40:
        raise ValueError("BMP header lama tidak didukung")
    w, h, planes, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
    top = h < 0
    h = abs(h)
    if w <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran BMP tidak wajar")
    if comp not in (0, 3) or bpp not in (8, 24, 32):
        raise ValueError("BMP %d-bit / kompresi %d belum didukung" % (bpp, comp))
    out = bytearray(w * h * 4)
    pal = None
    if bpp == 8:
        nc = _u32(d, 46) or 256
        pal = [bytes(d[14 + hs + 4 * i:14 + hs + 4 * i + 3]) for i in range(nc)]
    rb = ((w * bpp + 31) // 32) * 4
    for y in range(h):
        row = bytes(d[off + y * rb:off + y * rb + w * bpp // 8])
        dy = y if top else h - 1 - y
        o = dy * w * 4
        for x in range(w):
            if bpp == 24:
                b, g, r = row[3 * x:3 * x + 3]; a = 255
            elif bpp == 32:
                b, g, r, a = row[4 * x:4 * x + 4]
            else:
                b, g, r = pal[row[x]] if row[x] < len(pal) else (0, 0, 0); a = 255
            out[o:o + 4] = bytes((r, g, b, a)); o += 4
    return w, h, out


def _bmp_inspect(d, p):
    hs = _u32(d, 14)
    if hs >= 40:
        w, h, _, bpp, comp = struct.unpack_from("<iiHHI", d, 18)
        return {"lines": ["BMP %dx%d, %d-bit, kompresi %d" % (w, abs(h), bpp, comp)], "extract": "-> .png (8 / 24 / 32-bit tak terkompresi)"}
    return {"lines": ["BMP header lama (OS/2)"]}


def _bmp_extract(d, p, out, opts):
    w, h, px = _bmp_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("BMP", "image", lambda d, e: d[:2] == b"BM" and len(d) > 30 and _u32(d, 10) < len(d) and _u32(d, 14) in (12, 40, 52, 56, 64, 108, 124),
         _bmp_inspect, _bmp_extract, 16, "bitmap Windows")


# --- TGA (tanpa magic: dideteksi dari ekstensi + header masuk akal) ---

def _tga_ok(d, e):
    if e != ".tga" or len(d) < 18:
        return False
    cm, it, bpp = d[1], d[2], d[16]
    return cm in (0, 1) and it in (1, 2, 3, 9, 10, 11) and bpp in (8, 15, 16, 24, 32)


def _tga_decode(d):
    idlen, cmt, it = d[0], d[1], d[2]
    cmstart, cmlen, cmbits = struct.unpack_from("<HHB", d, 3)
    w, h, bpp, desc = struct.unpack_from("<HHBB", d, 12)[0:2] + struct.unpack_from("<BB", d, 16)
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran TGA tidak wajar")
    pos = 18 + idlen
    pal = None
    if cmt:
        step = (cmbits + 7) // 8
        pal = [bytes(d[pos + i * step:pos + (i + 1) * step]) for i in range(cmlen)]
        pos += cmlen * step
    bytespp = (bpp + 7) // 8
    rle = it >= 9
    total = w * h * bytespp
    if rle:
        buf = bytearray()
        while len(buf) < total and pos < len(d):
            hd = d[pos]; pos += 1
            n = (hd & 0x7F) + 1
            if hd & 0x80:
                buf += bytes(d[pos:pos + bytespp]) * n; pos += bytespp
            else:
                buf += bytes(d[pos:pos + n * bytespp]); pos += n * bytespp
        raw = bytes(buf[:total])
    else:
        raw = bytes(d[pos:pos + total])
    if len(raw) < total:
        raise ValueError("data TGA terpotong")
    out = bytearray(w * h * 4)
    base = it & 7
    for i in range(w * h):
        px = raw[i * bytespp:(i + 1) * bytespp]
        if base == 1:
            c = pal[px[0] - cmstart] if cmt and 0 <= px[0] - cmstart < len(pal) else b"\0\0\0"
            b, g, r = c[0], c[1], c[2]; a = c[3] if len(c) > 3 else 255
        elif base == 3:
            r = g = b = px[0]; a = 255
        elif bpp == 24:
            b, g, r = px; a = 255
        elif bpp == 32:
            b, g, r, a = px
        else:   # 15 / 16-bit 5-5-5
            v = px[0] | (px[1] << 8)
            r, g, b = ((v >> 10) & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, (v & 31) * 255 // 31; a = 255
        out[i * 4:i * 4 + 4] = bytes((r, g, b, a))
    if not (desc & 0x20):   # asal kiri-bawah -> balik vertikal
        rows = [out[y * w * 4:(y + 1) * w * 4] for y in range(h)][::-1]
        out = bytearray().join(rows)
    if desc & 0x10:         # asal kanan -> balik horizontal
        out = bytearray().join(bytes(b"".join(bytes(r[x * 4:x * 4 + 4]) for x in range(w - 1, -1, -1))) for r in [out[y * w * 4:(y + 1) * w * 4] for y in range(h)])
    return w, h, out


def _tga_inspect(d, p):
    w, h = _u16(d, 12), _u16(d, 14)
    return {"lines": ["TGA %dx%d, %d-bit, tipe %d%s" % (w, h, d[16], d[2], " (RLE)" if d[2] >= 9 else "")], "extract": "-> .png"}


def _tga_extract(d, p, out, opts):
    w, h, px = _tga_decode(d)
    out.write("%s.png" % _obj_name(p.stem, "image"), _png_encode(w, h, px), "image", "%dx%d" % (w, h))


register("TGA", "image", _tga_ok, _tga_inspect, _tga_extract, 60, "Truevision TGA (dikenali dari ekstensi + header)")


# --- DDS ---

_DXGI = {71: "DXT1", 72: "DXT1", 74: "DXT3", 75: "DXT3", 77: "DXT5", 78: "DXT5"}
_DXGI_NAMES = {80: "BC4_UNORM", 81: "BC4_SNORM", 83: "BC5_UNORM", 84: "BC5_SNORM", 95: "BC6H_UF16", 96: "BC6H_SF16", 98: "BC7_UNORM", 99: "BC7_UNORM_SRGB",
               28: "R8G8B8A8_UNORM", 87: "B8G8R8A8_UNORM"}


def _dds_info(d):
    h, w = struct.unpack_from("<II", d, 12)
    depth, mips = struct.unpack_from("<II", d, 24)
    pfflags = _u32(d, 80)
    fcc = bytes(d[84:88])
    bits = _u32(d, 88)
    masks = struct.unpack_from("<IIII", d, 92)
    off, fmt = 128, None
    if pfflags & 4:
        fcc_s = fcc.decode("latin-1")
        if fcc_s == "DX10":
            dx = _u32(d, 128)
            off = 148
            fmt = _DXGI.get(dx) or _DXGI_NAMES.get(dx) or "DXGI_%d" % dx
        else:
            fmt = fcc_s
    else:
        fmt = "RGBA%d" % bits if pfflags & 0x41 or pfflags & 0x40 else "RGB%d" % bits
    caps2 = _u32(d, 112)
    return {"w": w, "h": h, "mips": max(1, mips), "fmt": fmt, "off": off, "bits": bits, "masks": masks, "pf": pfflags,
            "cube": bool(caps2 & 0x200), "volume": bool(caps2 & 0x200000)}


def _c565(v): return ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31


def _dxt_decode(d, off, w, h, kind):
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 8 if kind == "DXT1" else 16
    if off + bw * bh * bs > len(d):
        raise ValueError("data DDS terpotong")
    out = bytearray(w * h * 4)
    for by in range(bh):
        for bx in range(bw):
            b = bytes(d[off + (by * bw + bx) * bs:off + (by * bw + bx) * bs + bs])
            cb = b[-8:]
            c0, c1 = struct.unpack_from("<HH", cb, 0)
            r0, r1 = _c565(c0), _c565(c1)
            if c0 > c1 or kind != "DXT1":
                pal = [r0 + (255,), r1 + (255,),
                       tuple((2 * a + b2) // 3 for a, b2 in zip(r0, r1)) + (255,), tuple((a + 2 * b2) // 3 for a, b2 in zip(r0, r1)) + (255,)]
            else:
                pal = [r0 + (255,), r1 + (255,), tuple((a + b2) // 2 for a, b2 in zip(r0, r1)) + (255,), (0, 0, 0, 0)]
            idx = struct.unpack_from("<I", cb, 4)[0]
            alpha = None
            if kind == "DXT3":
                av = int.from_bytes(b[:8], "little")
                alpha = [((av >> (4 * i)) & 15) * 17 for i in range(16)]
            elif kind == "DXT5":
                a0, a1 = b[0], b[1]
                ab = int.from_bytes(b[2:8], "little")
                ap = [a0, a1] + ([(( 6 - i) * a0 + (1 + i) * a1) // 7 for i in range(6)] if a0 > a1 else [((4 - i) * a0 + (1 + i) * a1) // 5 for i in range(4)] + [0, 255])
                alpha = [ap[(ab >> (3 * i)) & 7] for i in range(16)]
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x < w and y < h:
                    r, g, bl, a = pal[(idx >> (2 * i)) & 3]
                    if alpha:
                        a = alpha[i]
                    o = (y * w + x) * 4
                    out[o:o + 4] = bytes((r, g, bl, a))
    return out


# v99.8 [A4]: BC4 (1 kanal) dan BC5 (2 kanal, umum untuk normal map). FourCC ATI1 / BC4U / BC4S dan ATI2 / BC5U / BC5S, atau DXGI 80-84.
_BC4_FMTS = {"ATI1": False, "BC4U": False, "BC4_UNORM": False, "BC4S": True, "BC4_SNORM": True}
_BC5_FMTS = {"ATI2": False, "BC5U": False, "BC5_UNORM": False, "BC5S": True, "BC5_SNORM": True}


def _bc4_block(b, signed: bool):
    """Satu blok 8-byte -> 16 nilai 0..255 (urutan baris). UNORM: 8 / 6+{0,255} nilai; SNORM: dipetakan -1..1 -> 0..255."""
    if signed:
        e0, e1 = struct.unpack_from("<bb", b, 0)
        e0, e1 = max(e0, -127), max(e1, -127)
        pal = [e0, e1] + ([((7 - k) * e0 + k * e1) / 7.0 for k in range(1, 7)] if e0 > e1 else [((5 - k) * e0 + k * e1) / 5.0 for k in range(1, 5)] + [-127, 127])
        pal = [max(0, min(255, int(round((v / 127.0 * 0.5 + 0.5) * 255)))) for v in pal]
    else:
        e0, e1 = b[0], b[1]
        pal = [e0, e1] + ([((7 - k) * e0 + k * e1 + 3) // 7 for k in range(1, 7)] if e0 > e1 else [((5 - k) * e0 + k * e1 + 2) // 5 for k in range(1, 5)] + [0, 255])
    bits = int.from_bytes(bytes(b[2:8]), "little")
    return [pal[(bits >> (3 * i)) & 7] for i in range(16)]


def _bc45_decode(d, off, w, h, two: bool, signed: bool):
    """BC4 -> abu-abu (R=G=B, A=255). BC5 -> R,G dari dua kanal; B direkonstruksi sebagai komponen Z peta normal (sqrt(1-x^2-y^2))."""
    bw, bh = (w + 3) // 4, (h + 3) // 4
    bs = 16 if two else 8
    if off + bw * bh * bs > len(d):
        raise ValueError("data DDS terpotong")
    out = bytearray(w * h * 4)
    for by in range(bh):
        for bx in range(bw):
            o = off + (by * bw + bx) * bs
            r = _bc4_block(d[o:o + 8], signed)
            g = _bc4_block(d[o + 8:o + 16], signed) if two else r
            for i in range(16):
                x, y = bx * 4 + (i & 3), by * 4 + (i >> 2)
                if x >= w or y >= h:
                    continue
                if two:
                    nx, ny = r[i] / 127.5 - 1.0, g[i] / 127.5 - 1.0
                    z = 1.0 - nx * nx - ny * ny
                    bl = int(round((math.sqrt(z) if z > 0 else 0.0) * 127.5 + 127.5))
                    px = (r[i], g[i], max(0, min(255, bl)), 255)
                else:
                    px = (r[i], r[i], r[i], 255)
                q = (y * w + x) * 4
                out[q:q + 4] = bytes(px)
    return out


def _dds_decode(d):
    i = _dds_info(d)
    w, h, off, fmt = i["w"], i["h"], i["off"], i["fmt"]
    if w == 0 or h == 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran DDS tidak wajar")
    if i["cube"] or i["volume"]:
        raise ValueError("cubemap / tekstur volume: hanya mip pertama bidang pertama yang bisa dibaca; belum didukung")
    if fmt in ("DXT1", "DXT3", "DXT5"):
        return w, h, _dxt_decode(d, off, w, h, fmt)
    if fmt in _BC4_FMTS:
        return w, h, _bc45_decode(d, off, w, h, False, _BC4_FMTS[fmt])
    if fmt in _BC5_FMTS:
        return w, h, _bc45_decode(d, off, w, h, True, _BC5_FMTS[fmt])
    if fmt in ("R8G8B8A8_UNORM", "B8G8R8A8_UNORM") or (not (i["pf"] & 4) and i["bits"] in (24, 32)):
        bpp = 3 if (not (i["pf"] & 4) and i["bits"] == 24) else 4
        raw = bytes(d[off:off + w * h * bpp])
        if len(raw) < w * h * bpp:
            raise ValueError("data DDS terpotong")
        rm, gm, bm, am = i["masks"]
        out = bytearray(w * h * 4)
        sh = lambda m: (m & -m).bit_length() - 1 if m else None
        for px in range(w * h):
            v = int.from_bytes(raw[px * bpp:(px + 1) * bpp], "little")
            if fmt == "R8G8B8A8_UNORM":
                out[px * 4:px * 4 + 4] = raw[px * 4:px * 4 + 4]
            elif fmt == "B8G8R8A8_UNORM":
                b_, g_, r_, a_ = raw[px * 4:px * 4 + 4]; out[px * 4:px * 4 + 4] = bytes((r_, g_, b_, a_))
            else:
                g = lambda m: ((v & m) >> sh(m)) if m else 255
                out[px * 4:px * 4 + 4] = bytes((g(rm), g(gm), g(bm), g(am) if am else 255))
        return w, h, out
    raise ValueError("format DDS %s belum didukung (BC6H / BC7 / ASTC / dll butuh dekoder tambahan)" % fmt)


def _dds_inspect(d, p):
    i = _dds_info(d)
    ok = i["fmt"] in ("DXT1", "DXT3", "DXT5") or i["fmt"] in _BC4_FMTS or i["fmt"] in _BC5_FMTS or i["fmt"].startswith(("RGB", "RGBA", "R8G8B8A8", "B8G8R8A8"))
    L = ["DDS %dx%d, format %s, %d mip%s%s" % (i["w"], i["h"], i["fmt"], i["mips"], ", cubemap" if i["cube"] else "", ", volume" if i["volume"] else "")]
    if i["fmt"] in _BC5_FMTS:
        L.append("BC5 (2 kanal): biasanya peta normal; saat dikonversi R,G = kanal asli, B direkonstruksi dari X,Y")
    elif i["fmt"] in _BC4_FMTS:
        L.append("BC4 (1 kanal): dikonversi ke PNG abu-abu")
    return {"lines": L, "extract": "-> .png (mip pertama)" if ok and not (i["cube"] or i["volume"]) else "format ini belum bisa didekode ke PNG"}


def _dds_extract(d, p, out, opts):
    w, h, px = _dds_decode(d)
    f_ = _dds_info(d)["fmt"]
    note = " (BC5: B = Z hasil rekonstruksi normal map)" if f_ in _BC5_FMTS else " (BC4: abu-abu)" if f_ in _BC4_FMTS else ""
    out.write("%s.png" % _obj_name(p.stem, "texture"), _png_encode(w, h, px), "image", "%dx%d dari DDS%s" % (w, h, note))


register("DDS", "image", lambda d, e: d[:4] == b"DDS " and len(d) >= 128 and _u32(d, 4) == 124, _dds_inspect, _dds_extract, 12, "tekstur DirectDraw (game)")


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

def _wav_inspect(d, p):
    pos, fmt, data_len, extra = 12, None, 0, []
    while pos + 8 <= len(d):
        t, ln = bytes(d[pos:pos + 4]), _u32(d, pos + 4)
        if t == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", d, pos + 8)
        elif t == b"data":
            data_len = min(ln, len(d) - pos - 8)
        elif t in (b"LIST", b"smpl", b"cue ", b"bext", b"id3 "):
            extra.append(t.decode("latin-1").strip())
        pos += 8 + ln + (ln & 1)
    if not fmt:
        return {"lines": ["WAV tanpa chunk fmt (rusak)"]}
    tag, ch, sr, br, ba, bits = fmt
    dur = data_len / br if br else 0
    names = {1: "PCM", 3: "float", 2: "MS-ADPCM", 17: "IMA-ADPCM", 85: "MP3", 0xFFFE: "extensible"}
    return {"lines": ["WAV %s, %d kanal, %d Hz, %d-bit, durasi %.2f dtk" % (names.get(tag, "tag %d" % tag), ch, sr, bits, dur)] + (["chunk lain: " + ", ".join(extra)] if extra else [])}


register("WAV", "audio", lambda d, e: d[:4] == b"RIFF" and d[8:12] == b"WAVE", _wav_inspect, None, 14, "WAV (RIFF)")


def _ogg_inspect(d, p):
    n = len(d)
    ln = d[26]
    first = bytes(d[27 + ln:27 + ln + 64])
    rate = ch = 0
    kind = "?"
    pre = 0
    if first[:7] == b"\x01vorbis":
        kind, ch, rate = "Vorbis", first[11], _u32(first, 12)
    elif first[:8] == b"OpusHead":
        kind, ch, rate, pre = "Opus", first[9], 48000, struct.unpack_from("<H", first, 10)[0]
    elif first[:5] == b"\x7fFLAC":
        kind = "FLAC-dalam-Ogg"
    elif first[:8] == b"\x80theora" or first[:7] == b"\x80theora":
        kind = "Theora (video)"
    last = bytes(d).rfind(b"OggS", max(0, n - 70000))
    dur = 0.0
    if last >= 0 and rate:
        gp = struct.unpack_from("<q", d, last + 6)[0]
        dur = max(0, gp - pre) / rate
    return {"lines": ["OGG %s, %d kanal, %d Hz, durasi ~%.2f dtk" % (kind, ch, rate, dur)]}


register("OGG", "audio", lambda d, e: d[:4] == b"OggS" and len(d) > 40, _ogg_inspect, None, 14, "Ogg (Vorbis / Opus)")


def _flac_inspect(d, p):
    v = int.from_bytes(d[18:26], "big")
    rate, ch, bps, total = v >> 44, ((v >> 41) & 7) + 1, ((v >> 36) & 31) + 1, v & ((1 << 36) - 1)
    return {"lines": ["FLAC %d Hz, %d kanal, %d-bit, durasi %.2f dtk" % (rate, ch, bps, total / rate if rate else 0)]}


register("FLAC", "audio", lambda d, e: d[:4] == b"fLaC" and len(d) > 42, _flac_inspect, None, 14, "FLAC")

_MP3_BR = {1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0], 2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]}
_MP3_SR = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}


def _mp3_start(d):
    pos = 0
    if d[:3] == b"ID3" and len(d) > 10:
        pos = 10 + ((d[6] & 0x7F) << 21 | (d[7] & 0x7F) << 14 | (d[8] & 0x7F) << 7 | (d[9] & 0x7F))
    for i in range(pos, min(len(d) - 4, pos + 65536)):
        if d[i] == 0xFF and (d[i + 1] & 0xE0) == 0xE0 and (d[i + 1] >> 1) & 3 == 1 and (d[i + 1] >> 3) & 3 != 1 and (d[i + 2] >> 4) != 15 and ((d[i + 2] >> 2) & 3) != 3:
            return pos, i
    return pos, -1


def _mp3_detect(d, e):
    if d[:3] == b"ID3":
        return True
    return e == ".mp3" and _mp3_start(d)[1] >= 0


def _mp3_inspect(d, p):
    tag, i = _mp3_start(d)
    if i < 0:
        return {"lines": ["MP3 (ID3 ada, frame audio tidak ditemukan)"]}
    ver = (d[i + 1] >> 3) & 3
    br = _MP3_BR[1 if ver == 3 else 2][d[i + 2] >> 4]
    sr = _MP3_SR[ver][(d[i + 2] >> 2) & 3]
    ch = 1 if (d[i + 3] >> 6) == 3 else 2
    dur = (len(d) - i) * 8 / (br * 1000) if br else 0
    return {"lines": ["MP3 MPEG%s Layer III, %d kbps, %d Hz, %d kanal, durasi ~%.1f dtk (perkiraan CBR)%s" % (
        "1" if ver == 3 else "2", br, sr, ch, dur, ", ID3v2 %d byte" % tag if tag else "")]}


register("MP3", "audio", _mp3_detect, _mp3_inspect, None, 45, "MP3")


def _midi_inspect(d, p):
    fmt, nt, div = struct.unpack_from(">HHH", d, 8)
    return {"lines": ["MIDI format %d, %d track, %s" % (fmt, nt, "%d tick/beat" % div if not div & 0x8000 else "waktu SMPTE")]}


register("MIDI", "audio", lambda d, e: d[:8] == b"MThd\x00\x00\x00\x06" and len(d) >= 14, _midi_inspect, None, 14, "Standard MIDI")


# ---------------------------------------------------------------------------
# Arsip / paket game (pola umum: daftar entri + pembaca)
# ---------------------------------------------------------------------------

class _Arc:
    def __init__(self, entries, read, notes=None, close=None, kind=""):
        self.entries, self.read, self.notes, self.close, self.kind = entries, read, notes or [], close, kind


def _arc_inspect_factory(lister):
    def inspect(d, p):
        a = lister(d, p)
        try:
            ents = a.entries
            tot = sum(e.get("size", 0) for e in ents)
            ext = collections.Counter((os.path.splitext(e["name"])[1].lower() or "(tanpa ekstensi)") for e in ents)
            L = ["%s: %d entri, total %s" % (a.kind, len(ents), _as_human(tot))]
            if ext:
                L.append("jenis: " + ", ".join("%s x%d" % kv for kv in ext.most_common(10)))
            L += a.notes
            for e in ents[:25]:
                L.append("  %s  %s%s" % (_as_clean(e["name"], 90), _as_human(e.get("size", 0)), "  [terenkripsi]" if e.get("enc") else ""))
            if len(ents) > 25:
                L.append("  ... +%d entri lagi (ekstrak untuk daftar lengkap di manifest)" % (len(ents) - 25))
            return {"lines": L, "extract": "semua entri (filter dengan pola, mis. *.dds); tekstur / model di dalamnya ikut dikonversi bila convert=True",
                    "entries": [{"name": e["name"], "size": e.get("size", 0)} for e in ents[:2000]]}
        finally:
            if a.close:
                a.close()
    return inspect


def _arc_extract_factory(lister):
    def extract(d, p, out, opts):
        a = lister(d, p)
        pat = (opts.get("pattern") or "").lower()
        try:
            for e in a.entries:
                nm = e["name"]
                if pat and not fnmatch.fnmatch(nm.lower(), pat) and not fnmatch.fnmatch(os.path.basename(nm).lower(), pat):
                    continue
                if e.get("enc"):
                    out.skipped.append({"path": nm, "reason": "terenkripsi (butuh kunci)"})
                    continue
                if e.get("size", 0) > MAX_OUT_FILE:
                    out.skipped.append({"path": nm, "reason": "terlalu besar"})
                    continue
                try:
                    data = a.read(e)
                except Exception as ex:
                    out.errors.append("%s: %s" % (_as_clean(nm, 80), _as_clean(ex, 100)))
                    continue
                out.write(nm, data, "archive-entry")
        finally:
            if a.close:
                a.close()
    return extract


def _add_archive(name, detect, lister, about, priority=30):
    register(name, "archive", detect, _arc_inspect_factory(lister), _arc_extract_factory(lister), priority, about)


def _cstr(b) -> str:
    return bytes(b).split(b"\x00")[0].decode("latin-1")


# --- Quake PAK ---
def _qpak(d, p):
    off, ln = struct.unpack_from("<II", d, 4)
    if ln % 64 or off + ln > len(d) or ln // 64 > MAX_ENTRIES:
        raise ValueError("direktori PAK tidak valid")
    ents = []
    for i in range(ln // 64):
        nm = _cstr(d[off + 64 * i:off + 64 * i + 56])
        o, s = struct.unpack_from("<II", d, off + 64 * i + 56)
        if o + s > len(d):
            continue
        ents.append({"name": nm, "off": o, "size": s})
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), kind="Quake PAK")


_add_archive("Quake-PAK", lambda d, e: d[:4] == b"PACK" and len(d) >= 12 and _u32(d, 8) % 64 == 0, _qpak, "paket Quake / Quake II (PACK)")


# --- WAD ---
def _wad(d, p):
    m = bytes(d[:4])
    n, off = struct.unpack_from("<II", d, 4)
    if n > MAX_ENTRIES:
        raise ValueError("terlalu banyak lump")
    ents, notes = [], []
    if m in (b"IWAD", b"PWAD"):
        for i in range(n):
            o, s = struct.unpack_from("<ii", d, off + 16 * i)
            ents.append({"name": _cstr(d[off + 16 * i + 8:off + 16 * i + 16]), "off": o, "size": s})
        kind = "Doom WAD (%s)" % m.decode()
    else:
        for i in range(n):
            o, ds, s, t, c = struct.unpack_from("<iiiBB", d, off + 32 * i)
            ents.append({"name": _cstr(d[off + 32 * i + 16:off + 32 * i + 32]), "off": o, "size": s, "dsize": ds, "type": t, "comp": c,
                         "enc": c != 0})
        kind = "%s (Quake / Half-Life)" % m.decode()
        notes.append("lump tekstur (type 0x43) belum dikonversi ke gambar" if any(e.get("type") == 0x43 for e in ents) else "")
        notes = [x for x in notes if x]
    ents = [e for e in ents if 0 <= e["off"] and e["size"] >= 0 and e["off"] + e.get("dsize", e["size"]) <= len(d)]
    seen = collections.Counter()
    for e in ents:     # nama lump boleh kembar: bedakan
        seen[e["name"]] += 1
        if seen[e["name"]] > 1:
            e["name"] = "%s_%d" % (e["name"], seen[e["name"]])
    return _Arc(ents, lambda e: bytes(d[e["off"]:e["off"] + e["size"]]), notes, kind=kind)


_add_archive("WAD", lambda d, e: len(d) >= 12 and bytes(d[:4]) in (b"IWAD", b"PWAD", b"WAD2", b"WAD3"), _wad, "WAD (Doom / Quake / Half-Life)")


# --- LZ4 (blok mentah, tanpa pembungkus frame) ---
def _lz4_block(src, usize: int) -> bytes:
    """Dekompresi satu blok LZ4 mentah ke paling banyak `usize` byte (hasil harus tepat usize). Murni Python; keluaran dibatasi
    (blok berbahaya tidak bisa mengembang melebihi usize). ValueError bila rusak / terpotong / melebihi ukuran."""
    if usize < 0 or usize > MAX_OUT_FILE:
        raise ValueError("ukuran keluaran LZ4 tidak wajar")
    s = bytes(src)
    n = len(s)
    out = bytearray()
    i = 0
    try:
        while i < n:
            tok = s[i]
            i += 1
            ll = tok >> 4
            if ll == 15:
                while True:
                    b = s[i]
                    i += 1
                    ll += b
                    if b != 255:
                        break
            if len(out) + ll > usize:
                raise ValueError("LZ4: literal melebihi ukuran")
            out += s[i:i + ll]
            if i + ll > n:
                raise ValueError("LZ4: literal terpotong")
            i += ll
            if i >= n:
                break
            off = s[i] | (s[i + 1] << 8)
            i += 2
            if off == 0 or off > len(out):
                raise ValueError("LZ4: offset tidak sah")
            ml = tok & 15
            if ml == 15:
                while True:
                    b = s[i]
                    i += 1
                    ml += b
                    if b != 255:
                        break
            ml += 4
            if len(out) + ml > usize:
                raise ValueError("LZ4: salinan melebihi ukuran")
            st = len(out) - off
            if off >= ml:
                out += out[st:st + ml]
            else:
                pat = bytes(out[st:])
                out += (pat * (ml // off + 1))[:ml]
    except IndexError:
        raise ValueError("LZ4: data terpotong") from None
    if len(out) != usize:
        raise ValueError("LZ4: ukuran hasil %d, diharapkan %d" % (len(out), usize))
    return bytes(out)


# --- Unreal .pak (v1-v11, tanpa enkripsi) ---
_UPAK_MAGIC = 0x5A6F12E1


def _fstr(d, pos):
    n = struct.unpack_from("<i", d, pos)[0]
    pos += 4
    if n < 0:
        n = -n
        s = bytes(d[pos:pos + 2 * n]).decode("utf-16-le", "replace").rstrip("\x00")
        return s, pos + 2 * n
    s = bytes(d[pos:pos + n]).decode("utf-8", "replace").rstrip("\x00")
    return s, pos + n


def _upak_entry(d, pos, ver):
    st = pos
    off, size, usize, comp = struct.unpack_from("<QQQI", d, pos)
    pos += 28
    if ver == 1:
        pos += 8
    pos += 20
    blocks, enc, bsize = [], 0, 0
    if ver >= 3:
        if comp:
            nb = _u32(d, pos)
            pos += 4
            if nb > 1_000_000:
                raise ValueError("jumlah blok kompresi tidak wajar")
            for _ in range(nb):
                blocks.append(struct.unpack_from("<QQ", d, pos))
                pos += 16
        enc, bsize = d[pos], _u32(d, pos + 1)
        pos += 5
    return {"off": off, "csize": size, "size": usize if comp else size, "usize": usize, "comp": comp, "blocks": blocks, "enc": bool(enc), "bsize": bsize,
            "hdr": pos - st}, pos


def _upak_decode(blob, p):
    """Entri terenkode (indeks UE 4.26+, v10 / v11) pada blob[p:] -> (entri, posisi_berikut). Offset blok relatif terhadap awal entri."""
    v = struct.unpack_from("<I", blob, p)[0]
    p += 4
    comp, enc, nb = (v >> 23) & 0x3F, bool(v & (1 << 22)), (v >> 6) & 0xFFFF
    bs = v & 0x3F
    if bs == 0x3F:
        bs = struct.unpack_from("<I", blob, p)[0]
        p += 4
    else:
        bs <<= 11

    def rd(flag):
        nonlocal p
        if v & flag:
            x = struct.unpack_from("<I", blob, p)[0]
            p += 4
        else:
            x = struct.unpack_from("<Q", blob, p)[0]
            p += 8
        return x
    off = rd(1 << 31)
    usize = rd(1 << 30)
    size = rd(1 << 29) if comp else usize
    hdr = 48 + 5 + ((4 + 16 * nb) if comp else 0)
    blocks = []
    if nb:
        if nb == 1 and not enc:
            blocks = [(hdr, hdr + size)]
        else:
            cur = hdr
            for _ in range(nb):
                sz = struct.unpack_from("<I", blob, p)[0]
                p += 4
                blocks.append((cur, cur + sz))
                cur += ((sz + 15) & ~15) if enc else sz
    return {"off": off, "csize": size, "size": usize, "usize": usize, "comp": comp, "blocks": blocks, "enc": enc, "bsize": bs, "hdr": hdr}, p


def _upak_v10(d, ioff, ver):
    """Indeks utama v10 / v11: mount point, entri terenkode + tak-terenkode, nama dari indeks direktori penuh (bila ada).
    Mengembalikan (mount, entri, catatan)."""
    pos = ioff
    mount, pos = _fstr(d, pos)
    cnt = _u32(d, pos)
    pos += 4
    if cnt > MAX_ENTRIES:
        raise ValueError("terlalu banyak entri PAK")
    pos += 8   # path hash seed
    has_ph = _u32(d, pos)
    pos += 4
    if has_ph:
        pos += 8 + 8 + 20
    has_fd = _u32(d, pos)
    pos += 4
    fd_off = fd_sz = 0
    if has_fd:
        fd_off, fd_sz = struct.unpack_from("<qq", d, pos)
        pos += 8 + 8 + 20
    en = _u32(d, pos)
    pos += 4
    if pos + en > len(d):
        raise ValueError("blob entri terenkode melewati batas berkas")
    blob = bytes(d[pos:pos + en])
    pos += en
    nn = _u32(d, pos)
    pos += 4
    nonenc = []
    for _ in range(min(nn, MAX_ENTRIES)):
        e, pos = _upak_entry(d, pos, ver)
        nonenc.append(e)
    pre = mount.replace("../../../", "")
    ents, notes = [], []
    if has_fd and 0 <= fd_off and fd_off + fd_sz <= len(d):
        p = fd_off
        nd = _u32(d, p)
        p += 4
        for _ in range(min(nd, MAX_ENTRIES)):
            dn, p = _fstr(d, p)
            nf = _u32(d, p)
            p += 4
            for _ in range(min(nf, MAX_ENTRIES)):
                fn, p = _fstr(d, p)
                eo = struct.unpack_from("<i", d, p)[0]
                p += 4
                try:
                    e = dict(_upak_decode(blob, eo)[0]) if eo >= 0 else dict(nonenc[-(eo + 1)])
                except (struct.error, IndexError):
                    continue
                e["name"] = pre + dn.lstrip("/") + fn
                ents.append(e)
                if len(ents) >= MAX_ENTRIES:
                    break
            if len(ents) >= MAX_ENTRIES:
                break
    else:
        notes.append("indeks direktori penuh tidak ada: nama berkas tidak bisa dipulihkan (hanya hash path); entri diberi nama entry_NNNNNN")
        p = 0
        while p < len(blob) and len(ents) < MAX_ENTRIES:
            try:
                e, p = _upak_decode(blob, p)
            except struct.error:
                break
            e["name"] = "%sentry_%06d" % (pre, len(ents))
            ents.append(e)
        for e in nonenc:
            e = dict(e)
            e["name"] = "%sentry_%06d" % (pre, len(ents))
            ents.append(e)
    return mount, ents, notes


def _upak(d, p):
    n = len(d)
    tail_start = max(0, n - 512)
    tail = bytes(d[tail_start:])
    magic = struct.pack("<I", _UPAK_MAGIC)
    k = tail.rfind(magic)
    found = None
    while k >= 0:
        a = tail_start + k
        if a + 44 <= n:
            ver, ioff, isz = _u32(d, a + 4), _u64(d, a + 8), _u64(d, a + 16)
            if 1 <= ver <= 11 and ioff + isz <= n:
                found = (a, ver, ioff, isz)
                break
        k = tail.rfind(magic, 0, k)
    if not found:
        raise ValueError("footer Unreal PAK tidak ditemukan")
    a, ver, ioff, isz = found
    if ver >= 4 and d[a - 1]:
        raise ValueError("indeks PAK terenkripsi (butuh kunci AES)")
    names = [""]
    rem = n - (a + 44) - (1 if ver == 9 else 0)
    if ver >= 8 and rem > 0:
        base = a + 44 + (1 if ver == 9 else 0)
        names += [_cstr(d[base + 32 * i:base + 32 * i + 32]) for i in range(rem // 32)]
    v10notes = []
    if ver >= 10:
        mount, ents, v10notes = _upak_v10(d, ioff, ver)
    else:
        pos = ioff
        mount, pos = _fstr(d, pos)
        cnt = _u32(d, pos)
        pos += 4
        if cnt > MAX_ENTRIES:
            raise ValueError("terlalu banyak entri PAK")
        ents = []
        for _ in range(cnt):
            nm, pos = _fstr(d, pos)
            e, pos = _upak_entry(d, pos, ver)
            e["name"] = (mount.replace("../../../", "") + nm) if mount else nm
            ents.append(e)

    def read(e):
        if e["enc"]:
            raise ValueError("terenkripsi (butuh kunci AES)")
        base = e["off"]
        if e["comp"] == 0:
            return bytes(d[base + e["hdr"]:base + e["hdr"] + e["csize"]])
        meth = names[e["comp"]] if ver >= 8 and e["comp"] < len(names) else ("Zlib" if e["comp"] == 1 else "kode %d" % e["comp"])
        ml_ = meth.lower()
        lz4 = ml_.startswith("lz4")
        if not (lz4 or ml_.startswith("zlib")):
            raise ValueError("kompresi %s belum didukung (zlib dan LZ4 saja)" % meth)
        out = bytearray()
        for s, en in e["blocks"]:
            lo, hi = (base + s, base + en) if ver >= 5 else (s, en)
            if lz4:
                chunk = _lz4_block(bytes(d[lo:hi]), min(e["bsize"] or e["usize"], e["usize"] - len(out)))
                if len(out) + len(chunk) > MAX_OUT_FILE:
                    raise ValueError("terlalu besar")
                out += chunk
                continue
            dobj = zlib.decompressobj()   # v103.2: dibatasi; zlib.decompress() tanpa batas bisa mengembang jadi GB dalam satu blok
            chunk = dobj.decompress(bytes(d[lo:hi]), MAX_OUT_FILE + 1 - len(out))
            if dobj.unconsumed_tail or len(out) + len(chunk) > MAX_OUT_FILE:
                raise ValueError("terlalu besar")
            if not dobj.eof:
                raise ValueError("blok zlib tidak lengkap")
            out += chunk
        return bytes(out[:e["usize"]])
    return _Arc(ents, read, ["PERHATIAN: parser Unreal PAK ini baru diuji dengan berkas sintetis; bila hasil aneh, kirim contoh .pak kecil untuk diverifikasi.",
                               "mount point: %s | versi PAK: %d" % (_as_clean(mount, 60), ver)] + v10notes, kind="Unreal PAK")


def _upak_detect(d, e):
    n = len(d)
    return n > 60 and struct.pack("<I", _UPAK_MAGIC) in bytes(d[max(0, n - 512):])


_add_archive("Unreal-PAK", _upak_detect, _upak, "Unreal Engine .pak (v1-v11, tanpa enkripsi; zlib dan LZ4)", 28)


# --- ZIP ---
def _zip(d, p):
    zf = zipfile.ZipFile(p)
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        zf.close()
        raise ValueError("terlalu banyak entri ZIP")
    ents = [{"name": i.filename, "size": i.file_size, "csize": i.compress_size, "info": i, "enc": bool(i.flag_bits & 1)} for i in infos if not i.is_dir()]
    names = {e["name"] for e in ents}
    kind = "ZIP"
    notes = []
    if "AndroidManifest.xml" in names:
        kind = "APK (Android)"
    elif "[Content_Types].xml" in names:
        kind = "OOXML (docx / xlsx / pptx)"
        notes.append("media tertanam ada di word/media/, xl/media/, ppt/media/")
    elif "META-INF/MANIFEST.MF" in names:
        kind = "JAR"
    elif "mimetype" in names:
        kind = "ODF / EPUB"
    elif "AndroidManifest.xml" not in names and any(n.endswith(".uasset") or n.endswith(".pak") for n in names):
        kind = "ZIP (berisi aset Unreal)"

    def read(e):
        with zf.open(e["info"]) as f:
            data = f.read(MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc(ents, read, notes, zf.close, kind)


_add_archive("ZIP", lambda d, e: d[:4] in (b"PK\x03\x04", b"PK\x05\x06") and len(d) >= 22, _zip, "ZIP, APK, JAR, OOXML, ODF, EPUB", 30)


# --- TAR / GZIP ---
def _is_tar_raw(d): return len(d) > 512 and bytes(d[257:262]) == b"ustar"


def _gz_head(d):
    try:
        return zlib.decompressobj(31).decompress(bytes(d[:4096]), 1024)
    except zlib.error:
        return b""


def _tar(d, p):
    tf = tarfile.open(p, "r:*")
    ents = []
    for m in tf:
        if m.isfile():
            ents.append({"name": m.name, "size": m.size, "m": m})
            if len(ents) > MAX_ENTRIES:
                tf.close()
                raise ValueError("terlalu banyak entri TAR")

    def read(e):
        if e["size"] > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return tf.extractfile(e["m"]).read(MAX_OUT_FILE + 1)
    return _Arc(ents, read, close=tf.close, kind="TAR")


_add_archive("TAR", lambda d, e: _is_tar_raw(d) or (d[:2] == b"\x1f\x8b" and bytes(_gz_head(d))[257:262] == b"ustar") or (d[:3] == b"BZh" and e in (".tbz", ".tbz2", ".bz2") and e != ".bz2") or (d[:6] == b"\xfd7zXZ\x00" and e == ".txz"),
             _tar, "TAR (+ .tar.gz / .tgz)", 29)


def _gzip(d, p):
    flg = d[3]
    pos = 10
    name = ""
    if flg & 4:
        pos += 2 + _u16(d, pos)
    if flg & 8:
        end = bytes(d[pos:pos + 300]).find(b"\x00")
        name = bytes(d[pos:pos + end]).decode("latin-1") if end >= 0 else ""
    isz = _u32(d, len(d) - 4)
    nm = name or (p.stem if p.suffix.lower() == ".gz" else p.name + ".out")

    def read(e):
        data = zlib.decompressobj(31).decompress(bytes(d), MAX_OUT_FILE + 1)
        if len(data) > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        return data
    return _Arc([{"name": nm, "size": isz}], read, ["ukuran asli dari trailer (modulo 4 GB)"], kind="GZIP")


_add_archive("GZIP", lambda d, e: d[:3] == b"\x1f\x8b\x08" and len(d) > 18, _gzip, "GZIP satu berkas", 35)


# --- Unity AssetBundle (UnityFS): daftar node + ekstraksi (LZMA / LZ4 / LZ4HC); isi SerializedFile TIDAK diurai ---
def _unity_decomp(src: bytes, ctype: int, usize: int) -> bytes:
    if usize > MAX_OUT_FILE:
        raise ValueError("ukuran blok Unity terlalu besar")
    if ctype == 0:
        out = bytes(src[:usize])
    elif ctype == 1:
        try:
            import lzma
        except ImportError:
            raise ValueError("modul lzma tidak tersedia di Python ini (blok LZMA tidak bisa dibuka)") from None
        if len(src) < 6:
            raise ValueError("blok LZMA terlalu pendek")
        pr = src[0]
        dsz = struct.unpack_from("<I", src, 1)[0]
        if pr >= 9 * 5 * 5 or dsz > 256 * 1024 * 1024:
            raise ValueError("properti LZMA tidak wajar")
        flt = [{"id": lzma.FILTER_LZMA1, "dict_size": max(dsz, 4096), "lc": pr % 9, "lp": (pr // 9) % 5, "pb": pr // 45}]
        try:
            out = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=flt).decompress(bytes(src[5:]), max_length=usize)
        except lzma.LZMAError as e:
            raise ValueError("LZMA rusak: %s" % e) from None
    elif ctype in (2, 3):
        out = _lz4_block(src, usize)
    else:
        raise ValueError("jenis kompresi Unity %d tidak dikenal" % ctype)
    if len(out) != usize:
        raise ValueError("ukuran hasil dekompresi tidak cocok (%d, diharapkan %d)" % (len(out), usize))
    return out


def _unityfs(d, p):
    if len(d) < 48:
        raise ValueError("berkas UnityFS terlalu pendek")
    pos = 8
    ver = _b32(d, pos)
    pos += 4

    def cs():
        nonlocal pos
        end = bytes(d[pos:pos + 256]).find(b"\x00")
        if end < 0:
            raise ValueError("header UnityFS rusak")
        s = bytes(d[pos:pos + end]).decode("latin-1")
        pos += end + 1
        return s
    uver, rev = cs(), cs()
    size, cbi, ubi, flags = struct.unpack_from(">qIII", d, pos)
    pos += 20
    if cbi > 64 * 1024 * 1024 or ubi > 64 * 1024 * 1024:
        raise ValueError("blok info UnityFS tidak wajar")
    m = re.match(r"(\d+)\.(\d+)", uver)
    if ver >= 7:
        pos = (pos + 15) & ~15
    elif m and (int(m[1]), int(m[2])) >= (2019, 4):   # format 6 pada Unity 2019.4+: padding opsional
        pad = (16 - pos % 16) % 16
        if not any(bytes(d[pos:pos + pad])):
            pos += pad
    if flags & 0x80:   # blok info di akhir berkas
        info_off, data_off = len(d) - cbi, pos
    else:
        info_off, data_off = pos, pos + cbi
    if flags & 0x200:
        data_off = (data_off + 15) & ~15
    if info_off < 0 or info_off + cbi > len(d):
        raise ValueError("blok info UnityFS di luar berkas")
    info = _unity_decomp(bytes(d[info_off:info_off + cbi]), flags & 0x3F, ubi)
    q = 16   # hash
    nb = struct.unpack_from(">I", info, q)[0]
    q += 4
    if nb > MAX_ENTRIES:
        raise ValueError("terlalu banyak blok Unity")
    blocks, cpos, upos = [], data_off, 0
    for _ in range(nb):
        us, cz, fl = struct.unpack_from(">IIH", info, q)
        q += 10
        if cpos + cz > len(d):
            raise ValueError("blok data Unity melewati batas berkas")
        blocks.append((upos, us, cpos, cz, fl & 0x3F))
        upos += us
        cpos += cz
    nn = struct.unpack_from(">I", info, q)[0]
    q += 4
    if nn > MAX_ENTRIES:
        raise ValueError("terlalu banyak node Unity")
    ents = []
    for _ in range(nn):
        off, sz, nf = struct.unpack_from(">qqI", info, q)
        q += 20
        end = info.index(b"\x00", q)
        nm = info[q:end].decode("utf-8", "replace")
        q = end + 1
        if off < 0 or sz < 0 or off + sz > upos:
            continue
        ents.append({"name": nm or "node_%d" % len(ents), "off": off, "size": sz, "nflags": nf})
    starts = [b[0] for b in blocks]
    cache: dict = {}

    def read(e):
        if e["size"] > MAX_OUT_FILE:
            raise ValueError("terlalu besar")
        buf = bytearray()
        lo, hi = e["off"], e["off"] + e["size"]
        i = max(0, bisect.bisect_right(starts, lo) - 1)
        while i < len(blocks) and blocks[i][0] < hi:
            us_, usz, cp, cz, ct = blocks[i]
            if i not in cache:
                if len(cache) >= 4:
                    cache.pop(next(iter(cache)))
                cache[i] = _unity_decomp(bytes(d[cp:cp + cz]), ct, usz)
            blk = cache[i]
            buf += blk[max(lo, us_) - us_:min(hi, us_ + usz) - us_]
            i += 1
        if len(buf) != e["size"]:
            raise ValueError("data node tidak lengkap")
        return bytes(buf)
    return _Arc(ents, read, ["Unity %s (revisi %s), format UnityFS v%d; node diekstrak apa adanya (SerializedFile 'CAB-*' dan aliran .resS)." % (_as_clean(uver, 30), _as_clean(rev, 30), ver),
                             ] + _unityfs_objects_note(p), kind="Unity AssetBundle")


register("UnityFS", "archive", lambda d, e: bytes(d[:8]) == b"UnityFS\x00", _arc_inspect_factory(_unityfs), lambda d, p, out, opts: _unityfs_extract(d, p, out, opts), 20,
         "Unity AssetBundle (UnityFS; LZMA / LZ4 / LZ4HC); objek Texture2D / Mesh / AnimationClip / TextAsset didekode (v99.21)")


# --- deteksi-saja: 7z, RAR ---
register("7z", "archive", lambda d, e: d[:6] == b"7z\xbc\xaf\x27\x1c",
         lambda d, p: {"lines": ["7-Zip, versi %d.%d. Ekstrak dengan 7-Zip lalu arahkan REA ke folder hasil." % (d[6], d[7])]}, None, 20, "7z (deteksi saja)")
register("RAR", "archive", lambda d, e: d[:6] == b"Rar!\x1a\x07",
         lambda d, p: {"lines": ["RAR %s. Ekstrak dengan unrar / 7-Zip lalu arahkan REA ke folder hasil." % ("v5" if d[6] == 1 else "v4")]}, None, 20, "RAR (deteksi saja)")


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

def _sql_open(p: Path):
    uri = "file:%s?mode=ro&immutable=1" % urllib.parse.quote(str(p.resolve()))
    con = sqlite3.connect(uri, uri=True)
    con.execute("PRAGMA query_only=ON")
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    return con


def _sql_tables(con):
    return [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 500")]


def _sql_inspect(d, p):
    ps = struct.unpack_from(">H", d, 16)[0] or 65536
    con = _sql_open(p)
    try:
        L = ["SQLite: halaman %d byte x %d" % (ps, _b32(d, 28))]
        for t in _sql_tables(con)[:60]:
            q = '"%s"' % t.replace('"', '""')
            n = con.execute("SELECT COUNT(*) FROM %s" % q).fetchone()[0]
            cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % q)]
            L.append("  tabel %s: %d baris [%s]" % (_as_clean(t, 40), n, ", ".join(_as_clean(c, 20) for c in cols[:10])))
        return {"lines": L, "extract": "tiap tabel -> .csv"}
    finally:
        con.close()


def _sql_extract(d, p, out, opts):
    con = _sql_open(p)
    try:
        for t in _sql_tables(con):
            q = '"%s"' % t.replace('"', '""')
            cur = con.execute("SELECT * FROM %s LIMIT 2000000" % q)
            cols = [c[0] for c in cur.description]
            rows = []
            for r in cur:
                rows.append(["base64:" + base64.b64encode(v).decode() if isinstance(v, (bytes, bytearray)) and len(v) <= 65536 else
                             "<blob %d byte>" % len(v) if isinstance(v, (bytes, bytearray)) else v for v in r])
            out.write_text("tables/%s.csv" % _obj_name(t, "table"), _csv_text(rows, cols), "table", "%d baris" % len(rows))
    finally:
        con.close()


register("SQLite", "database", lambda d, e: d[:16] == b"SQLite format 3\x00", _sql_inspect, _sql_extract, 12, "database SQLite")


# ---------------------------------------------------------------------------
# Carving: cari berkas tertanam di dalam berkas apa pun
# ---------------------------------------------------------------------------

def _len_png(d, o):
    pos, n = o + 8, len(d)
    while pos + 12 <= n:
        ln = _b32(d, pos)
        t = bytes(d[pos + 4:pos + 8])
        pos += 12 + ln
        if t == b"IEND":
            return pos - o
        if ln > n:
            return None
    return None


def _len_gif(d, o):
    try:
        return _gif_walk(d, o)["end"]
    except (ValueError, struct.error, IndexError):
        return None


def _len_riff(d, o):
    ln = _u32(d, o + 4) + 8
    return ln if 12 < ln <= len(d) - o else None


def _len_ogg(d, o):
    pos, n = o, len(d)
    while pos + 27 <= n and bytes(d[pos:pos + 4]) == b"OggS":
        ns = d[pos + 26]
        if pos + 27 + ns > n:
            return None
        size = 27 + ns + sum(d[pos + 27:pos + 27 + ns])
        eos = d[pos + 5] & 4
        pos += size
        if eos:
            return pos - o
    return None


def _len_glb(d, o):
    ln = _u32(d, o + 8)
    return ln if 20 <= ln <= len(d) - o else None


def _len_midi(d, o):
    pos, n = o + 14, len(d)
    for _ in range(_u16(d, o + 10)):
        if pos + 8 > n or bytes(d[pos:pos + 4]) != b"MTrk":
            return None
        pos += 8 + _b32(d, pos + 4)
    return pos - o if pos <= n else None


def _len_sqlite(d, o):
    ps = struct.unpack_from(">H", d, o + 16)[0] or 65536
    pg = _b32(d, o + 28)
    ln = ps * pg
    return ln if pg and ln <= len(d) - o else None


def _len_zip(d, o):
    k = bytes(d[o:o + 64 * 1024 * 1024]).find(b"PK\x05\x06")
    if k < 0 or o + k + 22 > len(d):
        return None
    return k + 22 + _u16(d, o + k + 20)


class _RX(bytes):
    """Penanda: isinya pola regex mentah (bukan literal) untuk tabel _SIGS; byte variabel boleh dipakai."""


def _leb_u32(d, pos, n):
    v = sh = 0
    for _ in range(5):
        if pos >= n:
            return None, pos
        b = d[pos]
        pos += 1
        v |= (b & 0x7F) << sh
        if not b & 0x80:
            return v, pos
        sh += 7
    return None, pos


_WASM_RANK = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 13: 6, 6: 7, 7: 8, 8: 9, 9: 10, 12: 11, 10: 12, 11: 13}   # urutan kanonik section non-custom


def _len_wasm(d, o):
    """Modul WebAssembly: telusuri section (id, ukuran LEB128) sampai urutan kanonik / batas berkas putus."""
    n, pos, secs, prev = len(d), o + 8, 0, 0
    while pos < n:
        sid = d[pos]
        if sid > 13:
            break
        sz, p2 = _leb_u32(d, pos + 1, n)
        if sz is None or p2 + sz > n:
            break
        if sid:
            if _WASM_RANK[sid] <= prev:
                break
            prev = _WASM_RANK[sid]
        pos = p2 + sz
        secs += 1
    return pos - o if secs else None


def _len_wal(d, o):
    """SQLite WAL: header 32 byte + frame (24 + ukuran halaman) selama salt frame sama dengan salt header."""
    n = len(d)
    if o + 32 > n:
        return None
    ps = _b32(d, o + 8)
    if ps < 512 or ps > 65536 or ps & (ps - 1):
        return None
    salt, fr, pos, k = bytes(d[o + 16:o + 24]), 24 + ps, o + 32, 0
    while pos + fr <= n and bytes(d[pos + 8:pos + 16]) == salt and _b32(d, pos) > 0:
        pos += fr
        k += 1
    return pos - o if k else None


def _len_pem(d, o):
    """Blok PEM: dari -----BEGIN X----- sampai -----END X----- (label harus sama), termasuk newline penutup."""
    seg = bytes(d[o:o + 262144])
    b = seg.find(b"-----", 11)
    k = seg.find(b"-----END ")
    if b < 0 or k < 0:
        return None
    e0 = seg.find(b"-----", k + 9)
    if e0 < 0 or seg[11:b] != seg[k + 9:e0]:
        return None
    e = e0 + 5
    if seg[e:e + 2] == b"\r\n":
        e += 2
    elif seg[e:e + 1] == b"\n":
        e += 1
    return e


def _len_der_cert(d, o):
    """Sertifikat X.509 DER: SEQUENCE { tbsCertificate SEQUENCE, signatureAlgorithm SEQUENCE { OID ...} ...}. Panjang dari header; strukturnya divalidasi."""
    n = len(d)
    if o + 12 > n:
        return None
    tot = 4 + ((d[o + 2] << 8) | d[o + 3])
    tbs = 4 + ((d[o + 6] << 8) | d[o + 7])
    alg = o + 4 + tbs
    if tot < 200 or o + tot > n or tbs > tot - 4 or alg + 3 > o + tot or d[alg] != 0x30 or d[alg + 2] != 0x06:
        return None
    return tot


def _len_zstd(d, o):
    """Frame Zstandard: panjang persis dari header frame + header block (raw / RLE / terkompresi), plus checksum 4 byte bila ada."""
    n, pos = len(d), o + 4
    if pos >= n:
        return None
    fd = d[pos]
    if fd & 0x08:
        return None   # bit cadangan harus 0
    single, dflag, csum = (fd >> 5) & 1, fd & 3, (fd >> 2) & 1
    pos += 1 + (0 if single else 1) + (0, 1, 2, 4)[dflag] + ((1 if single else 0), 2, 4, 8)[fd >> 6]
    for _ in range(2_000_000):
        if pos + 3 > n:
            return None
        bh = d[pos] | (d[pos + 1] << 8) | (d[pos + 2] << 16)
        typ, sz = (bh >> 1) & 3, bh >> 3
        if typ == 3 or sz > 131072:
            return None
        pos += 3 + (1 if typ == 1 else sz)
        if pos > n:
            return None
        if bh & 1:
            pos += 4 if csum else 0
            return pos - o if pos <= n else None
    return None


_CARVE_NEED_LEN = frozenset({"wasm", "sqlite-wal", "pem-cert", "pem-key", "der-cert", "zstd"})   # tanpa panjang yang valid = positif palsu, dibuang

_SIGS = [
    ("png", b"\x89PNG\r\n\x1a\n", ".png", _len_png),
    ("jpeg", b"\xff\xd8\xff", ".jpg", lambda d, o: _jpeg_len(d, o)),
    ("gif", b"GIF89a", ".gif", _len_gif), ("gif", b"GIF87a", ".gif", _len_gif),
    ("riff", b"RIFF", None, _len_riff),
    ("ogg", b"OggS\x00\x02", ".ogg", _len_ogg),
    ("glb", b"glTF\x02\x00\x00\x00", ".glb", _len_glb),
    ("midi", b"MThd\x00\x00\x00\x06", ".mid", _len_midi),
    ("sqlite", b"SQLite format 3\x00", ".sqlite", _len_sqlite),
    ("zip", b"PK\x03\x04", ".zip", _len_zip),
    ("dds", b"DDS \x7c\x00\x00\x00", ".dds", None),
    ("fbx", b"Kaydara FBX Binary  \x00\x1a\x00", ".fbx", None),
    ("flac", b"fLaC\x00\x00\x00\x22", ".flac", None),
    ("quake-pak", b"PACK", ".pak", None),
    ("unityfs", b"UnityFS\x00", ".unity3d", None),
    ("7z", b"7z\xbc\xaf\x27\x1c", ".7z", None),
    ("gzip", b"\x1f\x8b\x08", ".gz", None),
    # v99.10 [Tier C]: panjang selalu bisa dipastikan (struktur divalidasi); kandidat tanpa panjang valid dibuang (_CARVE_NEED_LEN)
    ("wasm", b"\x00asm\x01\x00\x00\x00", ".wasm", _len_wasm),
    ("sqlite-wal", b"\x37\x7f\x06\x82\x00\x2d\xe2\x18", ".sqlite-wal", _len_wal), ("sqlite-wal", b"\x37\x7f\x06\x83\x00\x2d\xe2\x18", ".sqlite-wal", _len_wal),
    ("pem-cert", b"-----BEGIN CERTIFICATE-----", ".pem", _len_pem), ("pem-cert", b"-----BEGIN X509 CERTIFICATE-----", ".pem", _len_pem),
    ("pem-key", b"-----BEGIN PRIVATE KEY-----", ".key", _len_pem), ("pem-key", b"-----BEGIN RSA PRIVATE KEY-----", ".key", _len_pem),
    ("pem-key", b"-----BEGIN EC PRIVATE KEY-----", ".key", _len_pem), ("pem-key", b"-----BEGIN OPENSSH PRIVATE KEY-----", ".key", _len_pem),
    ("pem-key", b"-----BEGIN ENCRYPTED PRIVATE KEY-----", ".key", _len_pem),
    ("der-cert", _RX(rb"\x30\x82[\x01-\x1f][\x00-\xff]\x30\x82[\x01-\x1f][\x00-\xff]\xa0\x03\x02\x01\x02\x02"), ".der", _len_der_cert),
    ("zstd", b"\x28\xb5\x2f\xfd", ".zst", _len_zstd),
]
_SIG_RE = re.compile(b"|".join(b"(%s)" % (s[1] if isinstance(s[1], _RX) else re.escape(s[1])) for s in _SIGS), re.S)
_SIG_RX = {i: re.compile(s[1], re.S) for i, s in enumerate(_SIGS) if isinstance(s[1], _RX)}


def _sig_next(d, pos: int, lim: int, cache: list):
    """Tanda tangan terdekat di [pos, lim): (offset, indeks _SIGS) atau None. Setara dengan _SIG_RE.search (yang paling awal menang;
    seri dimenangkan urutan tabel), tetapi memakai find() per tanda tangan dengan cache posisi berikutnya, jauh lebih cepat pada berkas besar."""
    best, bi = lim + 1, -1
    for i, s in enumerate(_SIGS):
        o = cache[i]
        if o < pos:
            if i in _SIG_RX:
                m = _SIG_RX[i].search(d, pos, lim)
                o = m.start() if m else lim + 1
            else:
                o = d.find(s[1], pos, lim)
                if o < 0:
                    o = lim + 1
            cache[i] = o
        if o < best:
            best, bi = o, i
    return (best, bi) if bi >= 0 else None


_RIFF_EXT = {b"WAVE": ".wav", b"WEBP": ".webp", b"AVI ": ".avi"}


def _as_carve(path, outdir=None, max_items: int = 200, min_size: int = 64) -> dict:
    """Cari tanda tangan berkas di dalam berkas apa pun. Yang panjangnya bisa dipastikan (PNG, JPEG, GIF, OGG, RIFF, GLB, MIDI, SQLite, ZIP)
    dipotong ke outdir/carved/ (v99.10: + WebAssembly, SQLite WAL, sertifikat PEM / DER, kunci PEM, Zstandard); yang lain (DDS, FBX, FLAC, PAK ...) hanya dilaporkan offsetnya."""
    try:
        out = _Out(outdir) if outdir else None
        hits = []
        with _map(path) as d:
            n = len(d)
            lim = min(n, MAX_CARVE_SCAN)
            pos = 0
            cache = [-1] * len(_SIGS)
            while len(hits) < max_items:
                nx = _sig_next(d, pos, lim, cache)
                if not nx:
                    break
                o = nx[0]
                sig = _SIGS[nx[1]]
                nm, ext, fn = sig[0], sig[2], sig[3]
                ln = None
                try:
                    ln = fn(d, o) if fn else None
                except (struct.error, IndexError, ValueError):
                    ln = None
                if nm == "riff" and ln:
                    ext = _RIFF_EXT.get(bytes(d[o + 8:o + 12]), ".riff")
                    nm = "riff/" + ext[1:]
                elif nm == "riff":
                    pos = o + 4
                    continue
                if (nm == "gzip" or nm in _CARVE_NEED_LEN) and ln is None:
                    pos = o + 3   # terlalu banyak positif palsu untuk dilaporkan tanpa panjang
                    continue
                if ln is not None and ln < min_size:
                    pos = o + 4
                    continue
                if nm == "quake-pak" and not (o + 12 <= n and _u32(d, o + 8) % 64 == 0 and 0 < _u32(d, o + 8) < n):
                    pos = o + 4
                    continue
                h = {"offset": o, "type": nm, "length": ln, "whole_file": bool(o == 0 and ln == n)}
                if out and ln and not h["whole_file"]:
                    t = out.write("carved/0x%08X%s" % (o, ext), bytes(d[o:o + ln]), "carved", nm)
                    h["file"] = out.files[-1]["path"] if t else None
                hits.append(h)
                pos = o + (ln if ln else (4 if isinstance(sig[1], _RX) else len(sig[1])))
        res = {"status": "success", "path": str(path), "hits": hits, "count": len(hits)}
        if out:
            res.update(outdir=str(out.root), skipped=out.skipped, errors=out.errors)
        return res
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def _carve_text(res: dict) -> str:
    if res.get("status") != "success":
        return "CARVE gagal: %s" % res.get("message")
    if not res["hits"]:
        return "CARVE: tidak ada tanda tangan berkas dikenal di dalam berkas ini."
    L = ["CARVE: %d tanda tangan ditemukan" % res["count"]]
    for h in res["hits"][:60]:
        L.append("  0x%08X  %-14s %s%s" % (h["offset"], h["type"], _as_human(h["length"]) if h["length"] else "(panjang tidak bisa dipastikan)",
                                          "  -> " + h["file"] if h.get("file") else ""))
    if res["count"] > 60:
        L.append("  ... +%d lagi" % (res["count"] - 60))
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Cadangan: berkas tak dikenal (teks / biner)
# ---------------------------------------------------------------------------

def _fallback_inspect(d, p):
    samp = bytes(d[:1024 * 1024])
    ent = _as_entropy(samp)
    printable = sum(1 for b in samp[:65536] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, len(samp[:65536]))
    L = []
    if printable > 0.95 and samp:
        txt = samp[:200000].decode("utf-8", "replace")
        first = _as_clean(txt.strip().split("\n", 1)[0], 100)
        kind = "teks"
        s = txt.lstrip()[:1]
        if s in "{[":
            try:
                json.loads(bytes(d[:8 * 1024 * 1024]).decode("utf-8-sig"))
                kind = "JSON"
            except Exception:
                pass
        elif s == "<":
            kind = "XML / HTML"
        L.append("%s, %d baris, baris pertama: %s" % (kind, bytes(d[:8 * 1024 * 1024]).count(b"\n") + 1, first))
    else:
        L.append("biner tanpa format dikenal: entropi %.2f/8%s" % (ent, " (kemungkinan terkompresi / terenkripsi)" if ent > 7.5 else ""))
        res = _as_carve(p, None, max_items=12)
        if res.get("hits"):
            L.append("berkas tertanam terdeteksi:")
            L += ["  0x%08X %s%s" % (h["offset"], h["type"], " (%s)" % _as_human(h["length"]) if h["length"] else "") for h in res["hits"][:12]]
            L.append("gunakan carve / --carve untuk memotongnya keluar.")
        else:
            L.append("tidak ada tanda tangan berkas dikenal. Jika ini format game, tulis plugin atau kirim contoh untuk dibuatkan parser.")
    return {"lines": L, "extract": "tidak ada (format tidak dikenal); coba carve"}


register("unknown", "unknown", lambda d, e: True, _fallback_inspect, None, 999, "cadangan")


# ---------------------------------------------------------------------------
# API publik
# ---------------------------------------------------------------------------

def _ext(path) -> str:
    return Path(str(path)).suffix.lower()


def identify(path) -> dict:
    try:
        with _map(path) as d:
            f = _detect(d, _ext(path))
            return {"status": "success", "format": f.name if f else "unknown", "category": f.category if f else "unknown", "size": len(d),
                    "can_extract": bool(f and f.extract)}
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def describe(path) -> dict:
    try:
        p = Path(str(path))
        with _map(p) as d:
            f = _detect(d, _ext(p))
            rep = {"status": "success", "path": str(p), "name": _as_clean(p.name, 120), "size": len(d), "sha256": _sha256(d),
                   "format": f.name if f else "unknown", "category": f.category if f else "unknown", "lines": [], "can_extract": bool(f and f.extract)}
            if f and f.inspect:
                try:
                    r = f.inspect(d, p) or {}
                    rep["lines"] = [_as_clean(x, 400) for x in r.get("lines", [])]
                    rep["extract_hint"] = r.get("extract", "")
                    if "entries" in r:
                        rep["entries"] = r["entries"]
                except Exception as e:
                    rep["lines"] = ["%s: gagal dibaca (%s: %s)" % (f.name, type(e).__name__, _as_clean(e, 150))]
                    rep["parse_error"] = True
            return rep
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def describe_text(path, max_chars: int = 0) -> str:
    r = describe(path)
    if r.get("status") != "success":
        return "ASSETS gagal: %s" % r.get("message")
    L = ["ASSET EXPLORER (REA v%s)" % _as_VERSION,
         "Berkas : %s | %s | SHA-256 %s..." % (r["name"], _as_human(r["size"]), r["sha256"][:16]),
         "Format : %s (%s)" % (r["format"], r["category"])] + r["lines"]
    if r.get("extract_hint"):
        L.append("Bisa diekstrak: %s" % r["extract_hint"])
    t = "\n".join(L)
    return t if not max_chars or len(t) <= max_chars else t[:max_chars - 30] + "\n[...dipangkas...]"


_CONVERTIBLE = {".dds", ".tga", ".bmp", ".glb", ".gltf", ".fbx", ".stl", ".ply", ".dae", ".bvh"}


def _convert_tree(out: _Out, t_budget: float = 120.0):
    import time
    t0 = time.time()
    todo = [f for f in list(out.files) if f.get("kind") == "archive-entry" and _ext(f["path"]) in _CONVERTIBLE][:2000]
    done = 0
    for f in todo:
        if time.time() - t0 > t_budget:
            out.errors.append("konversi dihentikan: melewati batas waktu %d dtk" % t_budget)
            break
        src = out.root / f["path"]
        sub = _Out(out.root / "_converted" / Path(f["path"]).with_suffix("").as_posix())
        try:
            with _map(src) as d:
                fm = _detect(d, _ext(src))
                if fm and fm.extract:
                    fm.extract(d, src, sub, {})
        except Exception as e:
            out.errors.append("konversi %s: %s" % (_as_clean(f["path"], 60), _as_clean(e, 90)))
        for sf in sub.files:
            sf = dict(sf)
            sf["path"] = (Path("_converted") / Path(f["path"]).with_suffix("") / sf["path"]).as_posix()
            sf["note"] = ("hasil konversi dari %s" % f["path"] + (" | " + sf["note"] if sf["note"] else ""))
            out.files.append(sf)
            out.total += sf["size"]
        out.errors += ["%s: %s" % (_as_clean(f["path"], 50), e) for e in sub.errors]
        done += 1
    return done


def extract(path, outdir, pattern=None, convert: bool = True) -> dict:
    """Keluarkan isi berkas ke outdir. Mengembalikan manifest; status 'success' | 'partial' | 'error'."""
    try:
        p = Path(str(path))
        with _map(p) as d:
            f = _detect(d, _ext(p))
            if not f or not f.extract:
                return {"status": "error", "code": "no_extractor", "format": f.name if f else "unknown",
                        "message": "tidak ada pengekstrak untuk format %s%s" % (f.name if f else "tak dikenal", "; coba carve()" if not f or f.category == "unknown" else "")}
            out = _Out(outdir)
            opts = {"pattern": pattern, "convert": bool(convert)}
            try:
                f.extract(d, p, out, opts)
            except Exception as e:
                out.errors.append("%s: %s" % (type(e).__name__, _as_clean(e, 160)))
            converted = _convert_tree(out) if convert and f.category == "archive" else 0
            ok = bool(out.files)
            man = {"status": ("partial" if out.errors or out.skipped else "success") if ok else "error", "format": f.name, "source": str(p), "outdir": str(out.root),
                   "entries_extracted": len(out.files), "entries_skipped": len(out.skipped), "entries_failed": len(out.errors), "converted_items": converted,
                   "files": out.files, "skipped": out.skipped, "errors": out.errors}
            if not ok:
                man["message"] = "tidak ada yang berhasil diekstrak" + (": " + out.errors[0] if out.errors else "")
            try:
                (out.root / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
                man["manifest_path"] = str(out.root / "manifest.json")
            except OSError:
                pass
            return man
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 150))}


def extract_text(path, outdir, pattern=None, convert: bool = True) -> str:
    m = extract(path, outdir, pattern, convert)
    if m.get("status") == "error":
        return "EKSTRAK gagal: %s" % m.get("message")
    L = ["EKSTRAK %s: %d berkas ke %s (dilewati %d, galat %d%s)" % (m["format"], m["entries_extracted"], m["outdir"], m["entries_skipped"], m["entries_failed"],
                                                                 ", %d hasil konversi" % m["converted_items"] if m["converted_items"] else "")]
    for f in m["files"][:30]:
        L.append("  %s  %s%s" % (f["path"], _as_human(f["size"]), "  (%s)" % f["note"] if f["note"] else ""))
    if m["entries_extracted"] > 30:
        L.append("  ... +%d lagi (lihat manifest.json)" % (m["entries_extracted"] - 30))
    L += ["  dilewati: %s (%s)" % (s["path"], s["reason"]) for s in m["skipped"][:5]]
    L += ["  galat: %s" % e for e in m["errors"][:5]]
    return "\n".join(L)


def _init_plugins():
    pf = os.environ.get("REA_PLUGINS", "")
    if pf:
        load_plugins(pf)


_AS_RENAMED = {'VERSION': '_as_VERSION', '_clean': '_as_clean', '_entropy': '_as_entropy', '_human': '_as_human', 'carve': '_as_carve'}
_AS_PUBLIC = frozenset(['MAX_ACCESSOR', 'MAX_CARVE_SCAN', 'MAX_ENTRIES', 'MAX_OUT_FILE', 'MAX_OUT_TOTAL', 'MAX_PIXELS', 'MAX_XML', 'VERSION', '_ARR', '_Arc', '_CONVERTIBLE', '_CT', '_DXGI', '_DXGI_NAMES', '_FBX_MAGIC', '_FBX_TICKS', '_FORMATS', '_Fmt', '_LOADED_PLUGINS', '_MP3_BR', '_MP3_SR', '_NT', '_ObjBuilder', '_Out', '_PLY_T', '_PNG_CT', '_RESERVED', '_RIFF_EXT', '_SIGS', '_SIG_RE', '_UPAK_MAGIC', '_add_archive', '_arc_extract_factory', '_arc_inspect_factory', '_b32', '_bmp_decode', '_bmp_extract', '_bmp_inspect', '_bvh_extract', '_bvh_inspect', '_bvh_parse', '_c565', '_carve_text', '_clean', '_convert_tree', '_cstr', '_csv_text', '_dae_extract', '_dae_floats', '_dae_inspect', '_dae_root', '_data_uri', '_dds_decode', '_dds_extract', '_dds_info', '_dds_inspect', '_detect', '_dxt_decode', '_entropy', '_ext', '_external', '_fallback_inspect', '_fbx_ascii_inspect', '_fbx_child', '_fbx_cname', '_fbx_extract', '_fbx_inspect', '_fbx_objects', '_fbx_parse', '_fbx_props', '_flac_inspect', '_fstr', '_gif_inspect', '_gif_walk', '_gltf_acc', '_gltf_bufs', '_gltf_extract', '_gltf_inspect', '_gltf_load', '_gltf_prim_tris', '_gz_head', '_gzip', '_human', '_ico_inspect', '_init_plugins', '_is_bvh', '_is_dae', '_is_fbx_ascii', '_is_fbx_bin', '_is_glb', '_is_gltf', '_is_obj', '_is_tar_raw', '_jpeg_inspect', '_jpeg_len', '_len_gif', '_len_glb', '_len_midi', '_len_ogg', '_len_png', '_len_riff', '_len_sqlite', '_len_zip', '_map', '_midi_inspect', '_mp3_detect', '_mp3_inspect', '_mp3_start', '_obj_inspect', '_obj_name', '_ogg_inspect', '_ply_extract', '_ply_header', '_ply_inspect', '_ply_read', '_png_encode', '_png_inspect', '_png_walk', '_qpak', '_safe_rel', '_sha256', '_sql_extract', '_sql_inspect', '_sql_open', '_sql_tables', '_stl_extract', '_stl_inspect', '_stl_kind', '_stl_tris', '_tag', '_tar', '_tga_decode', '_tga_extract', '_tga_inspect', '_tga_ok', '_u16', '_u32', '_u64', '_unity_inspect', '_upak', '_upak_detect', '_upak_entry', '_wad', '_wav_inspect', '_webp_inspect', '_zip', 'carve', 'describe', 'describe_text', 'extract', 'extract_text', 'formats', 'i', 'identify', 'load_plugins', 'register'])
_AS_API = None


class _AssetsAPI:
    """Fasad pengganti `import rea_assets`: hanya nama publik bagian Asset Explorer yang bisa diakses (nama bentrok dipetakan ke _as_*)."""
    __slots__ = ()

    def __getattr__(self, name):
        if name not in _AS_PUBLIC:
            raise AttributeError(name)
        return globals()[_AS_RENAMED.get(name, name)]


def _assets_mod():
    """Asset Explorer (dulu rea_assets.py). Plugin REA_PLUGINS dimuat malas di pemanggilan pertama, seperti saat modul itu diimpor."""
    global _AS_API
    if _AS_API is None:
        _init_plugins()
        _AS_API = _AssetsAPI()
    return _AS_API


def assets_text(path, max_chars: int = 0) -> str:
    """v99: ringkasan ISI berkas non-exe (model 3D, animasi, tekstur, audio, arsip, SQLite ...). Gagal -> pesan, tidak melempar."""
    mod = _assets_mod()
    if mod is None:
        return "Asset Explorer (rea_assets.py) tidak ditemukan di folder yang sama; fitur isi berkas tidak tersedia."
    try:
        return mod.describe_text(path, max_chars=max_chars)
    except Exception as e:
        return "ASSETS gagal (%s: %s)." % (type(e).__name__, str(e)[:120])


def assets_extract(path, outdir, pattern=None, convert: bool = True) -> dict:
    """v99: keluarkan isi berkas ke outdir (mesh -> .obj, animasi -> .json / .csv, tekstur -> .png, entri arsip, tabel -> .csv). Mengembalikan manifest."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    return mod.extract(path, outdir, pattern=pattern, convert=convert)


def assets_carve(path, outdir=None) -> dict:
    """v99: cari (dan bila outdir diberikan, potong) berkas yang tertanam di dalam berkas apa pun."""
    mod = _assets_mod()
    if mod is None:
        return {"status": "error", "code": "module_missing", "message": "rea_assets.py tidak ditemukan"}
    return mod.carve(path, outdir)


def hex_text(path, offset=0, length: int = 256, encoding: str = "ascii") -> str:
    """Tampilan hex hanya-baca (v96, rea_binary.py). Gagal -> pesan, tidak melempar."""
    rea_binary = _binary_mod()
    r = rea_binary.hex_view(path, offset, length, encoding=encoding)
    return r["text"] if r.get("status") == "success" else "HEX gagal: %s" % r.get("message", r.get("code"))


def compare_text(path_a, path_b) -> str:
    """Ringkasan perbandingan dua berkas / dua folder (v96)."""
    rea_binary = _binary_mod()
    pa, pb = Path(path_a), Path(path_b)
    r = rea_binary.compare_dirs(pa, pb) if pa.is_dir() else rea_binary.compare_files(pa, pb)
    if r.get("status") != "success":
        return "COMPARE gagal: %s" % r.get("message", r.get("code"))
    if "changed_ranges" in r:
        L = ["BANDINGKAN: %s vs %s" % (r["a"], r["b"]), "Ukuran : %s vs %s (selisih %+d)" % (_human(r["size_a"]), _human(r["size_b"]), r["size_delta"]),
             "Identik: %s" % ("ya" if r["identical"] else "tidak"), "SHA-256: %s... | %s..." % (r["sha256_a"][:16], r["sha256_b"][:16])]
        if not r["identical"]:
            L.append("Byte berbeda: %d dalam %d rentang%s; perbedaan pertama di offset %s" % (r["differing_bytes"], len(r["changed_ranges"]), " (dipotong)" if r["truncated"] else "", r["first_diff"]))
            L += ["   offset 0x%X panjang %d" % (x["offset"], x["length"]) for x in r["changed_ranges"][:10]]
            if r["extra_bytes"]:
                L.append("Sisa %d byte hanya ada di berkas %s" % (r["extra_bytes"]["length"], r["extra_bytes"]["in"]))
        return "\n".join(L)
    return "BANDINGKAN FOLDER: +%d baru, -%d hilang, ~%d berubah, %d sama" % (len(r["added"]), len(r["removed"]), len(r["changed"]), r["unchanged_count"])



# ======================================================================================================
# rea_binary.py (Binary Workbench v96) dan rea_extract.py (mesin ekstraksi container v95) DIGABUNG ke berkas ini pada 23 Nov 2026
# (tanpa ubah perilaku, VERSION tetap), sama seperti rea_assets.py. Nama yang bentrok diberi awalan _bn_ (rea_binary) atau _ex_ (rea_extract):
# VERSION, _clean, _err, main, dan (khusus rea_extract) MAX_ENTRIES, _RESERVED, _entropy, _human, _open_regular, _safe_rel, extract, formats.
# Akses dari bagian lain lewat _binary_mod() / _extract_mod() (fasad: nama aslinya tetap bisa dipakai, mis. mod.hex_view, mod.open_container).
# CLI asli tersedia lewat:  python rea_triage.py --bin <hex|inspect|search|compare|patch|undo|history|restore> ...
#                           python rea_triage.py --ex  <list|extract|formats> ...
# ======================================================================================================

# ---------------------------------------------------------------------------------------------------
# Binary Workbench (dulu rea_binary.py)
# ---------------------------------------------------------------------------------------------------
_BN_DOC = """rea_binary.py - Binary Workbench untuk REA (v96; jembatan tipis ada di rea_triage.py: hex_text, compare_text).

Hanya pustaka standar. TIDAK menjalankan apa pun dari berkas. Semua fungsi tidak melempar: galat dikembalikan sebagai
    {"status": "error", "code": "...", "message": "..."}
dan keberhasilan sebagai {"status": "success", ...}.

Kontrak yang dipakai rea_triage.py (jangan diubah tanpa mengubah pemanggilnya):
    hex_view(path, offset=0, length=256, encoding="ascii") -> {"status", "text", ...}
    compare_files(a, b) -> {"status", "a", "b", "size_a", "size_b", "size_delta", "identical", "sha256_a", "sha256_b",
                            "differing_bytes", "changed_ranges": [{"offset", "length"}], "truncated", "first_diff",
                            "extra_bytes": {"length", "in"} | None}
    compare_dirs(a, b)  -> {"status", "added", "removed", "changed", "unchanged_count", ...}

Tambahan (aditif):
    inspect_at(path, offset)  / inspect_text(...)   inspektor data: int / float / waktu / GUID / IPv4 di satu offset
    search(path, pattern, mode="auto", ...) / search_text(...)   cari hex (dengan ??), teks, UTF-16, regex
    patch(path, offset, data, expect=None, dry_run=False)        timpa byte di tempat (panjang tetap) + jurnal undo
    undo(path, id=None, force=False) / history(path) / restore_original(path)

Patch: HANYA menimpa (tidak menambah / menghapus byte). Sebelum patch pertama, salinan asli disimpan di `<berkas>.rea_orig`
(kecuali backup=False atau berkas > 1 GiB) dan tiap patch dicatat di `<berkas>.rea_undo.json`.

CLI:  python rea_binary.py hex FILE [OFFSET [LEN]] | inspect FILE OFFSET | search FILE PATTERN [--mode hex|text|utf16|regex] [-i]
      | compare A B | patch FILE OFFSET HEX [--expect HEX] [--dry-run] | undo FILE [ID] | history FILE | restore FILE
"""


import hashlib
import json
import math
import os
import re
import shutil
import stat
import struct
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_bn_VERSION = "96.0"

MAX_HEX = 1 << 20              # byte maksimum per tampilan hex
MAX_RANGES = 200               # rentang perbedaan yang dicatat saat compare
MAX_HITS = 500                 # hasil pencarian maksimum
SEARCH_CHUNK = 4 * 1024 * 1024
SEARCH_OVERLAP = 4096          # panjang kecocokan maksimum yang dijamin tidak terpotong antar-potongan
SEARCH_TIME = 30.0             # detik
COMPARE_CHUNK = 1024 * 1024
MAX_DIR_FILES = 100_000
MAX_PATCH = 1024 * 1024
MAX_BACKUP = 1024 ** 3
MAX_JOURNAL = 2000
HASH_LIMIT = 64 * 1024 * 1024  # hash seluruh berkas setelah patch hanya bila <= ini


# ---------------------------------------------------------------------------------------------------
# Dasar
# ---------------------------------------------------------------------------------------------------

def _bn_err(code: str, message, **kw) -> dict:
    d = {"status": "error", "code": code, "message": _bn_clean(message, 300)}
    d.update(kw)
    return d


def _bn_clean(s, n: int = 200) -> str:
    """Buang karakter kontrol / pemisah baris (anti injeksi ke laporan)."""
    return "".join(c if c.isprintable() else "?" for c in str(s))[:n]


class _NotRegular(OSError):
    pass


def _fail(e: BaseException) -> dict:
    if isinstance(e, FileNotFoundError):
        return _bn_err("not_found", "berkas tidak ditemukan: %s" % _bn_clean(getattr(e, "filename", "") or "", 120))
    if isinstance(e, IsADirectoryError):
        return _bn_err("is_directory", "path adalah folder, bukan berkas")
    if isinstance(e, PermissionError):
        return _bn_err("permission", "tidak punya izin: %s" % _bn_clean(getattr(e, "filename", "") or "", 120))
    if isinstance(e, _NotRegular):
        return _bn_err("not_regular", str(e))
    if isinstance(e, OSError):
        return _bn_err("io_error", "%s: %s" % (type(e).__name__, e))
    return _bn_err("failed", "%s: %s" % (type(e).__name__, e))


class _Src:
    """Berkas dibuka SEKALI, lalu fstat: hanya berkas biasa (tolak FIFO / perangkat / folder) tanpa celah TOCTOU."""

    def __init__(self, path, write: bool = False):
        flags = (os.O_RDWR if write else os.O_RDONLY) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(str(Path(str(path)).expanduser()), flags)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise _NotRegular("bukan berkas biasa (FIFO / perangkat / folder ditolak)")
            self.fh = os.fdopen(fd, "r+b" if write else "rb")
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        self.size = st.st_size

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0:
            return b""
        self.fh.seek(off)
        return self.fh.read(n)

    def close(self):
        try:
            self.fh.close()
        except OSError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def _to_int(v, name: str = "nilai") -> int:
    if isinstance(v, bool):
        raise ValueError("%s tidak valid" % name)
    if isinstance(v, int):
        return v
    try:
        return int(str(v).strip(), 0)
    except ValueError:
        raise ValueError("%s bukan bilangan bulat: %r" % (name, str(v)[:40]))


def _norm_offset(off, size: int) -> int:
    o = _to_int(off, "offset")
    return max(0, size + o) if o < 0 else o     # offset negatif = dihitung dari akhir berkas


def _parse_hex(s, allow_wild: bool = False):
    """'4D 5A 90', '4d5a90', '0x4D,0x5A', '4D ?? 00' -> list[int | None] (None = wildcard)."""
    t = re.sub(r"0x", " ", str(s), flags=re.I)
    toks = [x for x in re.split(r"[\s,;:-]+", t) if x]
    if len(toks) == 1 and re.fullmatch(r"(?:[0-9A-Fa-f]{2}|\?\?)+", toks[0]) and len(toks[0]) > 2:
        toks = re.findall(r"[0-9A-Fa-f]{2}|\?\?", toks[0])
    out = []
    for tk in toks:
        if tk in ("?", "??"):
            if not allow_wild:
                raise ValueError("wildcard ?? tidak boleh di sini")
            out.append(None)
        elif re.fullmatch(r"[0-9A-Fa-f]{1,2}", tk):
            out.append(int(tk, 16))
        else:
            raise ValueError("token hex tidak valid: %r" % tk[:20])
    if not out:
        raise ValueError("pola hex kosong")
    return out


def _as_bytes(data) -> bytes:
    """bytes apa adanya; str: 'text:...' / 'u16:...' atau hex ('90 90')."""
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    s = str(data)
    if s.startswith("text:"):
        return s[5:].encode("utf-8")
    if s.startswith("u16:"):
        return s[4:].encode("utf-16-le")
    return bytes(_parse_hex(s))


def _sha256_file(path) -> str:
    h = hashlib.sha256()
    with _Src(path) as s:
        pos = 0
        while True:
            b = s.read_at(pos, COMPARE_CHUNK)
            if not b:
                break
            h.update(b)
            pos += len(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------------
# Hex view
# ---------------------------------------------------------------------------------------------------

_LATIN1 = "".join(chr(i) if (0x20 <= i <= 0x7E or (0xA1 <= i <= 0xFF and i != 0xAD)) else "." for i in range(256))
_bn_ASCII = "".join(chr(i) if 0x20 <= i <= 0x7E else "." for i in range(256))


def _ebcdic_table() -> str:
    t = []
    for i in range(256):
        try:
            c = bytes([i]).decode("cp037")
        except UnicodeDecodeError:
            c = "."
        t.append(c if (0x20 <= ord(c) <= 0x7E) else ".")
    return "".join(t)


_EBCDIC = _ebcdic_table()
_ENC_ALIASES = {"ascii": "ascii", "latin1": "latin1", "latin-1": "latin1", "iso-8859-1": "latin1", "cp1252": "latin1",
                "ebcdic": "ebcdic", "cp037": "ebcdic", "utf16": "utf16", "utf-16": "utf16", "utf16le": "utf16", "utf-16le": "utf16"}


def _text_column(row: bytes, enc: str) -> str:
    if enc == "utf16":
        out = []
        for i in range(0, len(row) - 1, 2):
            u = row[i] | (row[i + 1] << 8)
            c = chr(u) if (0x20 <= u < 0xD800 or 0xE000 <= u < 0xFFFE) else "."
            out.append(c if c.isprintable() else ".")
        if len(row) % 2:
            out.append(".")
        return "".join(out)
    table = {"ascii": _bn_ASCII, "latin1": _LATIN1, "ebcdic": _EBCDIC}[enc]
    return "".join(table[b] for b in row)


def hex_view(path, offset=0, length: int = 256, encoding: str = "ascii", width: int = 16) -> dict:
    """Tampilan hex hanya-baca. offset negatif = dari akhir berkas. length dibatasi MAX_HEX."""
    try:
        enc = _ENC_ALIASES.get(str(encoding).lower())
        if enc is None:
            return _bn_err("bad_encoding", "encoding tidak didukung: %s (ascii, latin1, ebcdic, utf16)" % _bn_clean(encoding, 20))
        width = _to_int(width, "width")
        width = width if width in (8, 16, 32) else 16
        length = _to_int(length, "length")
        length = 256 if length <= 0 else min(length, MAX_HEX)
        with _Src(path) as s:
            size = s.size
            off = _norm_offset(offset, size)
            if size == 0:
                return {"status": "success", "path": str(path), "size": 0, "offset": 0, "length": 0, "eof": True, "next_offset": None,
                        "encoding": enc, "text": "HEX %s | berkas kosong (0 byte)" % _bn_clean(Path(str(path)).name, 80)}
            if off >= size:
                return _bn_err("offset_out_of_range", "offset 0x%X di luar berkas (ukuran %d byte = 0x%X)" % (off, size, size))
            data = s.read_at(off, length)
        aw = 16 if size > 0xFFFFFFFF else 8
        L = ["HEX %s | ukuran %d (0x%X) | offset 0x%X | %d byte | %s" % (_bn_clean(Path(str(path)).name, 80), size, size, off, len(data), enc)]
        for i in range(0, len(data), width):
            row = data[i:i + width]
            cells = []
            for j in range(width):
                cells.append("%02X" % row[j] if j < len(row) else "  ")
                if j % 8 == 7 and j != width - 1:
                    cells.append("")
            L.append("%0*X  %s  |%s|" % (aw, off + i, " ".join(cells), _text_column(row, enc)))
        end = off + len(data)
        return {"status": "success", "path": str(path), "size": size, "offset": off, "length": len(data), "eof": end >= size,
                "next_offset": None if end >= size else end, "encoding": enc, "text": "\n".join(L)}
    except Exception as e:
        return _fail(e)


# ---------------------------------------------------------------------------------------------------
# Inspektor data
# ---------------------------------------------------------------------------------------------------

def _fmt_time(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") + " UTC"


def _plausible(dt) -> bool:
    return 1990 <= dt.year <= 2100


def inspect_at(path, offset=0) -> dict:
    """Tafsirkan byte di `offset` sebagai berbagai tipe data (little / big endian), waktu, GUID, IPv4, karakter."""
    try:
        with _Src(path) as s:
            off = _norm_offset(offset, s.size)
            if off >= s.size:
                return _bn_err("offset_out_of_range", "offset 0x%X di luar berkas (ukuran %d)" % (off, s.size))
            b = s.read_at(off, 16)
        n = len(b)
        v: dict = {}
        v["byte"] = "0x%02X  u8=%d  i8=%d  bin=%s  char=%r" % (b[0], b[0], b[0] - 256 if b[0] > 127 else b[0], format(b[0], "08b"), chr(b[0]) if 0x20 <= b[0] < 0x7F else ".")
        for size, code in ((2, "H"), (4, "I"), (8, "Q")):
            if n >= size:
                for endian, tag in (("<", "LE"), (">", "BE")):
                    u = struct.unpack_from(endian + code, b)[0]
                    i = struct.unpack_from(endian + code.lower(), b)[0]
                    v["u%d %s" % (size * 8, tag)] = "%d (0x%X)  | i%d=%d" % (u, u, size * 8, i)
        for size, code in ((4, "f"), (8, "d")):
            if n >= size:
                for endian, tag in (("<", "LE"), (">", "BE")):
                    f = struct.unpack_from(endian + code, b)[0]
                    v["f%d %s" % (size * 8, tag)] = "nan" if math.isnan(f) else ("%r" % f)
        if n >= 4:
            v["IPv4"] = ".".join(str(x) for x in b[:4])
            t = struct.unpack_from("<I", b)[0]
            try:
                dt = datetime.fromtimestamp(t, timezone.utc)
                if _plausible(dt):
                    v["Unix time32 LE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
            tb = struct.unpack_from(">I", b)[0]
            try:
                dt = datetime.fromtimestamp(tb, timezone.utc)
                if _plausible(dt):
                    v["Unix time32 BE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
            tm, dd = struct.unpack_from("<HH", b)
            sec, mi, hh = (tm & 31) * 2, (tm >> 5) & 63, tm >> 11
            da, mo, yr = dd & 31, (dd >> 5) & 15, 1980 + (dd >> 9)
            if 1 <= da <= 31 and 1 <= mo <= 12 and hh < 24 and mi < 60 and sec < 60 and 1990 <= yr <= 2100:
                v["DOS date/time"] = "%04d-%02d-%02d %02d:%02d:%02d" % (yr, mo, da, hh, mi, sec)
        if n >= 8:
            ft = struct.unpack_from("<Q", b)[0]
            try:
                dt = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ft // 10)
                if _plausible(dt):
                    v["FILETIME LE"] = _fmt_time(dt)
            except OverflowError:
                pass
            t64 = struct.unpack_from("<Q", b)[0]
            try:
                dt = datetime.fromtimestamp(t64, timezone.utc)
                if _plausible(dt):
                    v["Unix time64 LE"] = _fmt_time(dt)
            except (OverflowError, OSError, ValueError):
                pass
        if n >= 16:
            d1, d2, d3 = struct.unpack_from("<IHH", b)
            v["GUID (mixed-endian)"] = "{%08X-%04X-%04X-%s-%s}" % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
        for ln in (4, 3, 2, 1):
            try:
                ch = b[:ln].decode("utf-8")
                if ch and ch.isprintable():
                    v["UTF-8"] = "%r (U+%04X)" % (ch[0], ord(ch[0]))
                    break
            except UnicodeDecodeError:
                continue
        if n >= 2:
            u = b[0] | (b[1] << 8)
            if 0x20 <= u < 0xD800:
                v["UTF-16 LE"] = "%r (U+%04X)" % (chr(u), u)
        return {"status": "success", "path": str(path), "offset": off, "bytes": b.hex(), "values": v}
    except Exception as e:
        return _fail(e)


def inspect_text(path, offset=0) -> str:
    r = inspect_at(path, offset)
    if r.get("status") != "success":
        return "INSPEKSI gagal: %s" % r.get("message", r.get("code"))
    L = ["INSPEKTOR DATA %s @ 0x%X | %s" % (_bn_clean(Path(str(path)).name, 80), r["offset"], " ".join(r["bytes"][i:i + 2] for i in range(0, len(r["bytes"]), 2)).upper())]
    L += ["  %-20s %s" % (k, x) for k, x in r["values"].items()]
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# Pencarian
# ---------------------------------------------------------------------------------------------------

def _compile_pattern(pattern, mode: str, ignore_case: bool):
    p = str(pattern)
    m = (mode or "auto").lower()
    if m == "auto":
        low = p.lower()
        if low.startswith("hex:"):
            m, p = "hex", p[4:]
        elif low.startswith("re:"):
            m, p = "regex", p[3:]
        elif low.startswith("u16:"):
            m, p = "utf16", p[4:]
        else:
            m = "text"
    if not p:
        raise ValueError("pola kosong")
    if len(p) > 2000:
        raise ValueError("pola terlalu panjang (maks 2000 karakter)")
    flags = re.DOTALL | (re.IGNORECASE if ignore_case else 0)
    if m == "hex":
        toks = _parse_hex(p, allow_wild=True)
        rx = b"".join(b"." if t is None else re.escape(bytes([t])) for t in toks)
        return m, re.compile(rx, re.DOTALL), len(toks)
    if m == "text":
        raw = p.encode("utf-8")
        return m, re.compile(re.escape(raw), flags), len(raw)
    if m == "utf16":
        raw = p.encode("utf-16-le")
        return m, re.compile(re.escape(raw), re.DOTALL), len(raw)    # huruf besar / kecil UTF-16 tidak dilipat
    if m == "regex":
        return m, re.compile(p.encode("latin-1", "replace"), flags), 0
    raise ValueError("mode pencarian tidak dikenal: %s (auto, hex, text, utf16, regex)" % m[:20])


def search(path, pattern, mode: str = "auto", ignore_case: bool = False, start=0, end=None, max_hits: int = 200, context: int = 8) -> dict:
    """Cari pola di berkas. mode: auto (awalan 'hex:' / 're:' / 'u16:' atau teks biasa) | hex (boleh ??) | text | utf16 | regex (bytes, latin-1).
    Mode regex memakai mesin `re` Python: pola yang sangat rumit bisa lambat; ada batas waktu antar-potongan (SEARCH_TIME)."""
    try:
        m, rx, _plen = _compile_pattern(pattern, mode, ignore_case)
        max_hits = max(1, min(_to_int(max_hits, "max_hits"), MAX_HITS))
        context = max(0, min(_to_int(context, "context"), 64))
        t0 = time.time()
        hits: list = []
        truncated = timeout = False
        with _Src(path) as s:
            lo = _norm_offset(start, s.size)
            hi = s.size if end is None else min(s.size, _norm_offset(end, s.size))
            pos = lo
            while pos < hi and not truncated:
                if time.time() - t0 > SEARCH_TIME:
                    timeout = truncated = True
                    break
                chunk = s.read_at(pos, min(SEARCH_CHUNK + SEARCH_OVERLAP, hi - pos))
                more = pos + SEARCH_CHUNK < hi
                for mt in rx.finditer(chunk):
                    a = mt.start()
                    if more and a >= SEARCH_CHUNK:
                        break
                    if mt.end() == a:
                        continue
                    hits.append((pos + a, mt.end() - a))
                    if len(hits) >= max_hits:
                        truncated = True
                        break
                pos += SEARCH_CHUNK
            out = []
            for off, ln in hits:
                ctx = s.read_at(max(0, off - context), ln + 2 * context) if context else b""
                body = s.read_at(off, min(ln, 48))
                out.append({"offset": off, "length": ln, "hex": body.hex(" ").upper(), "ascii": "".join(_bn_ASCII[x] for x in body),
                            "context_ascii": "".join(_bn_ASCII[x] for x in ctx) if context else ""})
        return {"status": "success", "path": str(path), "mode": m, "pattern": _bn_clean(pattern, 120), "count": len(out), "hits": out,
                "truncated": truncated, "timeout": timeout, "range": [lo, hi], "elapsed": round(time.time() - t0, 3)}
    except (ValueError, re.error) as e:
        return _bn_err("bad_pattern", "%s" % e)
    except Exception as e:
        return _fail(e)


def search_text(path, pattern, **kw) -> str:
    r = search(path, pattern, **kw)
    if r.get("status") != "success":
        return "CARI gagal: %s" % r.get("message", r.get("code"))
    L = ["CARI %s [%s] di %s: %d hasil%s" % (r["pattern"], r["mode"], _bn_clean(Path(str(path)).name, 80), r["count"],
                                           " (DIPOTONG%s)" % (", waktu habis" if r["timeout"] else "") if r["truncated"] else "")]
    for h in r["hits"][:50]:
        L.append("  0x%08X  +%d  %s  |%s|" % (h["offset"], h["length"], h["hex"][:48], h["ascii"][:24]))
    if r["count"] > 50:
        L.append("  ... +%d hasil lain" % (r["count"] - 50))
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------------------------------

def compare_files(a, b, max_ranges: int = MAX_RANGES) -> dict:
    """Bandingkan dua berkas byte demi byte (hash dihitung dalam satu lintasan). Rentang berbeda digabung bila bersebelahan."""
    try:
        max_ranges = max(1, min(_to_int(max_ranges, "max_ranges"), 5000))
        with _Src(a) as sa, _Src(b) as sb:
            size_a, size_b = sa.size, sb.size
            common = min(size_a, size_b)
            ha, hb = hashlib.sha256(), hashlib.sha256()
            ranges: list = []
            differing = 0
            first = None
            truncated = False
            pos = 0
            open_end = -1       # akhir rentang terakhir (untuk menggabungkan rentang yang menyambung antar-potongan)
            while pos < common:
                n = min(COMPARE_CHUNK, common - pos)
                ca, cb = sa.read_at(pos, n), sb.read_at(pos, n)
                if len(ca) != len(cb) or not ca:
                    break       # berkas berubah saat dibaca
                ha.update(ca)
                hb.update(cb)
                if ca != cb:
                    i, ln = 0, len(ca)
                    while i < ln:
                        if ca[i] == cb[i]:
                            i += 1
                            continue
                        j = i
                        while j < ln and ca[j] != cb[j]:
                            j += 1
                        absolute = pos + i
                        differing += j - i
                        if first is None:
                            first = absolute
                        if ranges and open_end == absolute:
                            ranges[-1]["length"] += j - i
                        elif len(ranges) < max_ranges:
                            ranges.append({"offset": absolute, "length": j - i})
                        else:
                            truncated = True
                        open_end = absolute + (j - i)
                        i = j
                pos += len(ca)
            extra = None
            if size_a != size_b:
                longer, sl, which = (sa, size_a, "A") if size_a > size_b else (sb, size_b, "B")
                hl = ha if which == "A" else hb
                p2 = common
                while p2 < sl:
                    c = longer.read_at(p2, COMPARE_CHUNK)
                    if not c:
                        break
                    hl.update(c)
                    p2 += len(c)
                extra = {"length": abs(size_a - size_b), "in": which}
                if first is None:
                    first = common
            return {"status": "success", "a": str(a), "b": str(b), "size_a": size_a, "size_b": size_b, "size_delta": size_b - size_a,
                    "identical": size_a == size_b and differing == 0, "sha256_a": ha.hexdigest(), "sha256_b": hb.hexdigest(),
                    "differing_bytes": differing, "changed_ranges": ranges, "truncated": truncated, "first_diff": first, "extra_bytes": extra}
    except Exception as e:
        return _fail(e)


def _walk_files(root: Path) -> dict:
    """{path relatif (posix): (path, ukuran)} untuk berkas biasa; tautan simbolik dan berkas khusus dilewati."""
    out: dict = {}
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            it = list(os.scandir(d))
        except OSError:
            continue
        for e in it:
            try:
                if e.is_symlink():
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(Path(e.path))
                elif e.is_file(follow_symlinks=False):
                    out[Path(e.path).relative_to(root).as_posix()] = (e.path, e.stat(follow_symlinks=False).st_size)
                    if len(out) > MAX_DIR_FILES:
                        raise OverflowError("terlalu banyak berkas (> %d)" % MAX_DIR_FILES)
            except OSError:
                continue
    return out


def _same_content(pa: str, pb: str) -> bool:
    with _Src(pa) as x, _Src(pb) as y:
        if x.size != y.size:
            return False
        pos = 0
        while pos < x.size:
            if x.read_at(pos, COMPARE_CHUNK) != y.read_at(pos, COMPARE_CHUNK):
                return False
            pos += COMPARE_CHUNK
    return True


def compare_dirs(a, b) -> dict:
    """Bandingkan dua folder (rekursif, isi berkas dibandingkan langsung). added = hanya di B, removed = hanya di A."""
    try:
        pa, pb = Path(str(a)).expanduser(), Path(str(b)).expanduser()
        for p in (pa, pb):
            if not p.is_dir():
                return _bn_err("not_directory", "bukan folder: %s" % _bn_clean(p, 120))
        fa, fb = _walk_files(pa), _walk_files(pb)
        added = sorted(set(fb) - set(fa))
        removed = sorted(set(fa) - set(fb))
        changed, same = [], 0
        for k in sorted(set(fa) & set(fb)):
            (xa, sza), (xb, szb) = fa[k], fb[k]
            try:
                eq = sza == szb and _same_content(xa, xb)
            except OSError:
                eq = False
            if eq:
                same += 1
            else:
                changed.append({"path": k, "size_a": sza, "size_b": szb})
        return {"status": "success", "a": str(a), "b": str(b), "added": added, "removed": removed, "changed": changed, "unchanged_count": same}
    except Exception as e:
        return _fail(e)


# ---------------------------------------------------------------------------------------------------
# Patch + undo
# ---------------------------------------------------------------------------------------------------

def _journal_path(path) -> Path:
    p = Path(str(path)).expanduser()
    return p.with_name(p.name + ".rea_undo.json")


def _orig_path(path) -> Path:
    p = Path(str(path)).expanduser()
    return p.with_name(p.name + ".rea_orig")


def _load_journal(path) -> dict:
    jp = _journal_path(path)
    if jp.exists():
        try:
            j = json.loads(jp.read_text(encoding="utf-8"))
            if isinstance(j, dict) and isinstance(j.get("entries"), list):
                return j
        except (OSError, ValueError):
            raise ValueError("jurnal undo rusak: %s" % jp.name)
    return {"version": 1, "target": Path(str(path)).name, "original_sha256": None, "original_size": None, "backup": None, "entries": []}


def _save_journal(path, j: dict):
    jp = _journal_path(path)
    tmp = jp.with_name(jp.name + ".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, jp)


def _fsync_write(s: _Src, off: int, data: bytes):
    s.fh.seek(off)
    s.fh.write(data)
    s.fh.flush()
    try:
        os.fsync(s.fh.fileno())
    except OSError:
        pass


def patch(path, offset, data, expect=None, dry_run: bool = False, note: str = "", backup: bool = True) -> dict:
    """Timpa byte di `offset` (panjang tetap; tidak menambah / menghapus). data: bytes, atau str hex ('90 90') / 'text:...' / 'u16:...'.
    expect (opsional): byte lama yang diharapkan; tidak cocok -> tidak ada yang ditulis. Setiap patch dicatat di jurnal untuk undo()."""
    try:
        new = _as_bytes(data)
        if not new:
            return _bn_err("empty_patch", "data patch kosong")
        if len(new) > MAX_PATCH:
            return _bn_err("patch_too_large", "patch %d byte melebihi batas %d" % (len(new), MAX_PATCH))
        exp = _as_bytes(expect) if expect not in (None, "") else None
        with _Src(path, write=not dry_run) as s:
            off = _norm_offset(offset, s.size)
            if off + len(new) > s.size:
                return _bn_err("out_of_range", "patch 0x%X..0x%X melewati akhir berkas (%d byte); patch hanya menimpa" % (off, off + len(new), s.size))
            old = s.read_at(off, len(new))
            if exp is not None and old != exp:
                return _bn_err("expect_mismatch", "byte lama di 0x%X adalah %s, bukan %s; tidak ada yang ditulis" % (off, old.hex(" ").upper()[:60], exp.hex(" ").upper()[:60]))
            res = {"status": "success", "path": str(path), "offset": off, "length": len(new), "old_hex": old.hex(" ").upper(), "new_hex": new.hex(" ").upper(),
                   "dry_run": bool(dry_run), "unchanged": old == new}
            if dry_run or old == new:
                return res
            j = _load_journal(path)
            if len(j["entries"]) >= MAX_JOURNAL:
                return _bn_err("journal_full", "jurnal undo penuh (%d entri); pulihkan atau buang jurnal dulu" % MAX_JOURNAL)
            if not j["entries"] and j.get("original_sha256") is None:
                if backup and s.size <= MAX_BACKUP and not _orig_path(path).exists():
                    shutil.copyfile(str(Path(str(path)).expanduser()), str(_orig_path(path)))
                    j["backup"] = _orig_path(path).name
                j["original_size"] = s.size
                j["original_sha256"] = _sha256_file(path) if s.size <= HASH_LIMIT else None
            nid = max([e["id"] for e in j["entries"]] + [0]) + 1
            entry = {"id": nid, "time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "offset": off, "old": old.hex(), "new": new.hex(),
                     "note": _bn_clean(note, 120), "undone": False}
            j["entries"].append(entry)
            _save_journal(path, j)          # jurnal lebih dulu: bila crash, perubahan tetap bisa dibalik
            try:
                _fsync_write(s, off, new)
            except BaseException:
                j["entries"].pop()
                _save_journal(path, j)
                raise
        res["id"] = nid
        res["sha256_after"] = _sha256_file(path) if Path(str(path)).stat().st_size <= HASH_LIMIT else None
        res["backup"] = j.get("backup")
        return res
    except ValueError as e:
        return _bn_err("bad_argument", e)
    except Exception as e:
        return _fail(e)


def history(path) -> dict:
    try:
        if not Path(str(path)).expanduser().is_file():
            return _bn_err("not_found", "berkas tidak ditemukan")
        j = _load_journal(path)
        return {"status": "success", "path": str(path), "original_sha256": j.get("original_sha256"), "original_size": j.get("original_size"),
                "backup": j.get("backup") if _orig_path(path).exists() else None, "entries": j["entries"]}
    except Exception as e:
        return _fail(e)


def undo(path, id=None, force: bool = False) -> dict:
    """Balikkan patch terakhir yang belum di-undo (atau `id`). Byte saat ini harus sama dengan byte hasil patch (kecuali force=True)."""
    try:
        j = _load_journal(path)
        live = [e for e in j["entries"] if not e.get("undone")]
        if not live:
            return _bn_err("nothing_to_undo", "tidak ada patch yang bisa di-undo")
        if id is None:
            e = live[-1]
        else:
            tid = _to_int(id, "id")
            e = next((x for x in live if x["id"] == tid), None)
            if e is None:
                return _bn_err("no_such_patch", "patch #%d tidak ada atau sudah di-undo" % tid)
        new, old = bytes.fromhex(e["new"]), bytes.fromhex(e["old"])
        with _Src(path, write=True) as s:
            cur = s.read_at(e["offset"], len(new))
            if cur != new and not force:
                return _bn_err("changed_since", "byte di 0x%X sudah berubah sejak patch #%d (sekarang %s); pakai force untuk tetap memulihkan" % (
                    e["offset"], e["id"], cur.hex(" ").upper()[:60]))
            _fsync_write(s, e["offset"], old)
        e["undone"] = True
        e["undone_time"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _save_journal(path, j)
        return {"status": "success", "path": str(path), "id": e["id"], "offset": e["offset"], "length": len(old), "restored_hex": old.hex(" ").upper(),
                "remaining": len([x for x in j["entries"] if not x.get("undone")])}
    except ValueError as e:
        return _bn_err("bad_argument", e)
    except Exception as e:
        return _fail(e)


def restore_original(path) -> dict:
    """Kembalikan berkas ke salinan asli (`.rea_orig`) dan tandai semua patch sebagai di-undo. Tidak jalan bila salinan tak ada."""
    try:
        op = _orig_path(path)
        if not op.is_file():
            return _bn_err("no_backup", "salinan asli (%s) tidak ada" % op.name)
        j = _load_journal(path)
        target = Path(str(path)).expanduser()
        tmp = target.with_name(target.name + ".rea_restore.tmp")
        shutil.copyfile(str(op), str(tmp))
        os.replace(tmp, target)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for e in j["entries"]:
            if not e.get("undone"):
                e["undone"], e["undone_time"] = True, now
        _save_journal(path, j)
        return {"status": "success", "path": str(path), "restored_from": op.name,
                "sha256": _sha256_file(path) if target.stat().st_size <= HASH_LIMIT else None, "original_sha256": j.get("original_sha256")}
    except Exception as e:
        return _fail(e)


def patch_text(r: dict) -> str:
    if r.get("status") != "success":
        return "PATCH gagal: %s" % r.get("message", r.get("code"))
    tag = "SIMULASI " if r.get("dry_run") else ""
    L = ["%sPATCH @ 0x%X (%d byte): %s -> %s%s" % (tag, r["offset"], r["length"], r["old_hex"][:60], r["new_hex"][:60], " (tidak ada perubahan)" if r.get("unchanged") else "")]
    if r.get("id"):
        L.append("  jurnal #%d | undo: undo(path)%s" % (r["id"], " | salinan asli: %s" % r["backup"] if r.get("backup") else ""))
    return "\n".join(L)


# ---------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------

def _opt(argv: list, name: str, default=None, flag: bool = False):
    if name in argv:
        i = argv.index(name)
        if flag:
            del argv[i]
            return True
        v = argv[i + 1] if i + 1 < len(argv) else default
        del argv[i:i + 2]
        return v
    return False if flag else default


def _bn_main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_BN_DOC.split("CLI:")[1].strip() if "CLI:" in _BN_DOC else "pemakaian: lihat dokumentasi modul")
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "hex" and rest:
        enc = _opt(rest, "--encoding", "ascii")
        r = hex_view(rest[0], rest[1] if len(rest) > 1 else 0, rest[2] if len(rest) > 2 else 256, encoding=enc)
        print(r["text"] if r["status"] == "success" else "HEX gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    if cmd == "inspect" and rest:
        print(inspect_text(rest[0], rest[1] if len(rest) > 1 else 0))
        return 0
    if cmd == "search" and len(rest) > 1:
        mode, ic = _opt(rest, "--mode", "auto"), _opt(rest, "-i", flag=True)
        print(search_text(rest[0], rest[1], mode=mode, ignore_case=ic))
        return 0
    if cmd == "compare" and len(rest) > 1:
        r = compare_files(rest[0], rest[1]) if not Path(rest[0]).is_dir() else compare_dirs(rest[0], rest[1])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["status"] == "success" else 1
    if cmd == "patch" and len(rest) > 2:
        exp, dry = _opt(rest, "--expect"), _opt(rest, "--dry-run", flag=True)
        r = patch(rest[0], rest[1], rest[2], expect=exp, dry_run=dry)
        print(patch_text(r))
        return 0 if r["status"] == "success" else 1
    if cmd == "undo" and rest:
        force = _opt(rest, "--force", flag=True)
        r = undo(rest[0], rest[1] if len(rest) > 1 else None, force=force)
        print("UNDO patch #%s @ 0x%X dipulihkan (%d byte); sisa %d" % (r["id"], r["offset"], r["length"], r["remaining"]) if r["status"] == "success" else "UNDO gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    if cmd == "history" and rest:
        print(json.dumps(history(rest[0]), ensure_ascii=False, indent=1))
        return 0
    if cmd == "restore" and rest:
        r = restore_original(rest[0])
        print("PULIH dari %s" % r["restored_from"] if r["status"] == "success" else "PULIH gagal: %s" % r["message"])
        return 0 if r["status"] == "success" else 1
    print("perintah tidak dikenal / argumen kurang; jalankan tanpa argumen untuk bantuan")
    return 1

# ---------------------------------------------------------------------------------------------------
# Mesin ekstraksi container (dulu rea_extract.py)
# ---------------------------------------------------------------------------------------------------
_EX_DOC = """rea_extract.py - mesin ekstraksi / penjelajahan container untuk REA (v95; dipanggil lewat jembatan tipis di rea_triage.py).

Hanya pustaka standar. TIDAK menjalankan apa pun dari berkas; container hanya dibaca, hasil selalu ditulis ke workspace terpisah.
Format: ZIP (termasuk APK / JAR / SFX), TAR (+ gz / bz2 / xz), GZIP / BZIP2 / XZ tunggal, ISO 9660 (Joliet / Rock Ridge, sektor 2048 / raw 2352),
ISO PSP (UMD: membaca PSP_GAME/PARAM.SFO) dan CSO PSP (zlib per blok) yang berisi ISO. ZSO (LZ4) dan 7z / RAR belum didukung (dilaporkan jelas).

Kontrak yang dipakai rea_triage.py (jangan diubah tanpa mengubah pemanggilnya):
    open_container(path)  -> {"status": "success", "container_id", "format", ...} | {"status": "error", "code", "message"}
    close_container(container_id)
    extract_selected(container_id, selector, outdir, scan=False) -> manifest dict
          selector: None | {"pattern": "*.dll;*.exe" | "re:...", "paths": [...], "exclude": "...", "max_size": N, "max_entries": N}
          pola TANPA wildcard (* ? [) dicocokkan sebagai potongan nama (huruf besar / kecil diabaikan)
          manifest: status success | partial | error, entries_extracted / entries_skipped / entries_failed, manifest_path, files, skipped, errors ...
    describe_container_text(path, max_chars=0) -> str

Tambahan (aditif): list_entries(cid), describe_container(path), extract(path, outdir, pattern=None, scan=False), formats().

Workspace keluaran (outdir): extracted/ (isi), manifests/manifest.json (tidak menimpa; manifest_2.json dst), logs/extract.log.

Pengerasan: path entri dinetralkan (zip-slip, '..', path absolut, huruf drive, nama perangkat Windows, karakter ilegal), tidak menimpa berkas,
tautan simbolik / berkas khusus TIDAK diekstrak, berkas terenkripsi dilewati, batas jumlah entri / ukuran per berkas / total / rasio kompresi (zip bomb),
berkas dibuka sekali dengan fstat (tolak FIFO / perangkat / folder), keluaran dibersihkan dari baris baru. Container di dalam container TIDAK diekstrak otomatis.

CLI:  python rea_extract.py list FILE | extract FILE OUTDIR [pola] [--scan] | formats
"""


import bz2
import fnmatch
import gzip
import hashlib
import io
import json
import lzma
import math
import os
import re
import secrets
import stat
import struct
import sys
import tarfile
import threading
import time
import zipfile
import zlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ex_VERSION = "95.0"

_ex_MAX_ENTRIES = 200_000
MAX_ENTRY_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 ** 3
MAX_RATIO = 200                       # byte keluar per byte terkompresi ...
RATIO_FLOOR = 64 * 1024 * 1024        # ... baru dianggap mencurigakan setelah melewati ini
COPY_CHUNK = 1024 * 1024
LIST_TIME = 60.0                      # detik untuk membuat daftar entri (tar.gz besar)
MAX_LIST_ROWS = 200
MAX_OPEN = 16
MAX_DIR_BYTES = 16 * 1024 * 1024      # satu direktori ISO
MAX_DEPTH = 64
SOURCE_HASH_LIMIT = 2 * 1024 ** 3

_EXEC_EXT = {".exe", ".dll", ".scr", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".hta", ".lnk", ".msi", ".jar",
             ".sh", ".elf", ".so", ".pif", ".cpl", ".sys", ".apk", ".dex", ".py", ".pyc"}
_ARCHIVE_TYPES = {"ZIP", "GZIP", "BZIP2", "XZ", "7z", "RAR", "TAR", "ISO 9660", "CAB", "OLE / Office lama"}
_ex_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}


class ContainerError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class _Limit(Exception):
    pass


# ---------------------------------------------------------------------------------------------------
# Utilitas
# ---------------------------------------------------------------------------------------------------

def _ex_clean(s, n: int = 200) -> str:
    """Buang karakter kontrol / pemisah baris (anti injeksi ke laporan)."""
    return "".join(c if c.isprintable() else "?" for c in str(s))[:n]


def _ex_human(n) -> str:
    if n is None or n < 0:
        return "?"
    n = float(n)
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%d %s" % (n, u) if u == "B" else "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f GB" % n


def _ex_err(code: str, message, **kw) -> dict:
    d = {"status": "error", "code": code, "message": _ex_clean(message, 300)}
    d.update(kw)
    return d


def _ts(t):
    try:
        return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds") if t else None
    except (OverflowError, OSError, ValueError):
        return None


def _ex_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values())


def _ex_safe_rel(path: str):
    """Netralkan path entri jadi path relatif aman. Mengembalikan (rel, unsafe: bool). unsafe = ada '..', path absolut, atau huruf drive."""
    raw = str(path).replace("\\", "/")
    unsafe = raw.startswith("/") or bool(re.match(r"^[A-Za-z]:", raw)) or any(p == ".." for p in raw.split("/"))
    parts = []
    for part in raw.split("/"):
        if part in ("", ".", ".."):
            continue
        part = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]", "_", part).rstrip(". ")
        if not part:
            part = "_"
        if part.split(".")[0].upper() in _ex_RESERVED:
            part = "_" + part
        if len(part) > 120:
            stem, dot, ext = part.rpartition(".")
            part = (stem[:100] + "." + ext[:15]) if dot and len(ext) <= 15 else part[:120]
        parts.append(part)
    parts = parts[-MAX_DEPTH:]
    rel = "/".join(parts) or "unnamed"
    return rel[-240:], unsafe


def _sniff(head: bytes) -> str:
    """Jenis berkas dari magic bytes (bukan ekstensi)."""
    h = head
    if h[:2] == b"MZ":
        if len(h) >= 0x40:
            pe = struct.unpack_from("<I", h, 0x3C)[0]
            if pe + 4 <= len(h) and h[pe:pe + 4] == b"PE\0\0":
                return "PE"
        return "PE" if len(h) < 0x40 else "DOS MZ"
    if h[:4] == b"\x7fELF":
        return "ELF"
    if h[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"):
        return "Mach-O / class"
    if h[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        return "ZIP"
    if h[:2] == b"\x1f\x8b":
        return "GZIP"
    if h[:3] == b"BZh":
        return "BZIP2"
    if h[:6] == b"\xfd7zXZ\x00":
        return "XZ"
    if h[:6] == b"7z\xbc\xaf\x27\x1c":
        return "7z"
    if h[:4] == b"Rar!":
        return "RAR"
    if h[:4] == b"MSCF":
        return "CAB"
    if h[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "OLE / Office lama"
    if h[:5] == b"%PDF-":
        return "PDF"
    if h[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if h[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF"
    if h[:4] == b"RIFF":
        return "RIFF"
    if h[:4] == b"OggS":
        return "OGG"
    if h[:16] == b"SQLite format 3\0":
        return "SQLite"
    if h[:4] == b"\x4c\x00\x00\x00" and h[4:20] == b"\x01\x14\x02\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x46":
        return "LNK"
    if h[:4] == b"\x00PBP":
        return "PSP PBP"
    if h[:4] == b"~PSP":
        return "PSP PRX terenkripsi"
    if h[:4] == b"\x00PSF":
        return "PSP SFO"
    if h[:4] == b"CISO":
        return "CSO"
    if h[:4] == b"\x7fSCE":
        return "SCE"
    if h[257:262] == b"ustar":
        return "TAR"
    if h[:2] == b"#!":
        return "skrip (shebang)"
    if len(h) > 32769 and h[32769:32774] == b"CD001":
        return "ISO 9660"
    if h and all(c in b"\t\r\n\x0b\x0c" or 0x20 <= c < 0x7F or c >= 0x80 for c in h[:512]) and b"\x00" not in h[:512]:
        return "teks"
    return "data"


# ---------------------------------------------------------------------------------------------------
# Entri dan pembaca citra
# ---------------------------------------------------------------------------------------------------

class Entry:
    __slots__ = ("index", "path", "size", "packed", "kind", "mtime", "encrypted", "ref", "note")

    def __init__(self, index, path, size=0, packed=0, kind="file", mtime=None, encrypted=False, ref=None, note=""):
        self.index, self.path, self.size, self.packed, self.kind = index, path, size, packed, kind
        self.mtime, self.encrypted, self.ref, self.note = mtime, encrypted, ref, note

    def as_dict(self) -> dict:
        return {"index": self.index, "path": _ex_clean(self.path, 300), "size": self.size, "packed": self.packed, "kind": self.kind,
                "mtime": _ts(self.mtime), "encrypted": self.encrypted, "note": self.note}


class _FileImg:
    """Akses acak ke berkas yang sudah dibuka (satu fh, dikunci)."""

    def __init__(self, fh, size):
        self.fh, self.size, self.lock = fh, size, threading.Lock()

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0:
            return b""
        with self.lock:
            self.fh.seek(off)
            return self.fh.read(n)


class _CsoImg:
    """CSO / CISO PSP: indeks u32 per blok (bit 31 = blok tidak terkompresi), blok = raw deflate. Menyajikan citra ISO penuh."""

    def __init__(self, base: _FileImg):
        self.base = base
        hdr = base.read_at(0, 24)
        if len(hdr) < 24:
            raise ContainerError("corrupt", "header CSO terpotong")
        _m, hsz, total, bsz, ver, align = struct.unpack("<4sIQIBB2x", hdr)
        if ver > 1 and ver != 2:
            raise ContainerError("unsupported_format", "versi CSO %d tidak dikenal" % ver)
        if bsz < 512 or bsz > (1 << 20) or (bsz & (bsz - 1)):
            raise ContainerError("corrupt", "ukuran blok CSO tidak valid: %d" % bsz)
        if total == 0 or total > (1 << 37):
            raise ContainerError("corrupt", "ukuran total CSO tidak valid: %d" % total)
        n = (total + bsz - 1) // bsz
        raw = base.read_at(24, (n + 1) * 4)
        if len(raw) < (n + 1) * 4:
            raise ContainerError("corrupt", "indeks CSO terpotong")
        self.index = struct.unpack("<%dI" % (n + 1), raw)
        self.bsz, self.align, self.size, self.nblocks = bsz, align, total, n
        self._cache: dict = {}
        self._lock = threading.Lock()

    def _block(self, i: int) -> bytes:
        with self._lock:
            b = self._cache.get(i)
        if b is not None:
            return b
        idx, nxt = self.index[i], self.index[i + 1]
        pos, end = (idx & 0x7FFFFFFF) << self.align, (nxt & 0x7FFFFFFF) << self.align
        if end < pos or end - pos > self.bsz * 2 + 1024 or pos >= self.base.size:
            raise ContainerError("corrupt", "indeks blok CSO %d tidak masuk akal" % i)
        data = self.base.read_at(pos, end - pos)
        if idx & 0x80000000:
            b = data[:self.bsz]
        else:
            try:
                b = zlib.decompressobj(-15).decompress(data, self.bsz)
            except zlib.error as e:
                raise ContainerError("corrupt", "blok CSO %d rusak: %s" % (i, e))
        with self._lock:
            if len(self._cache) > 16:
                self._cache.clear()
            self._cache[i] = b
        return b

    def read_at(self, off: int, n: int) -> bytes:
        if off < 0 or n <= 0 or off >= self.size:
            return b""
        n = min(n, self.size - off)
        out = []
        while n > 0:
            i, w = divmod(off, self.bsz)
            blk = self._block(i)[w:w + n]
            if not blk:
                break
            out.append(blk)
            off += len(blk)
            n -= len(blk)
        return b"".join(out)


# ---------------------------------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------------------------------

class _Handler:
    fmt = "?"
    label = "?"
    sequential = False      # True: data hanya bisa dibaca berurutan (tar terkompresi) -> iter_data()

    def __init__(self):
        self.entries: list[Entry] = []
        self.truncated = False
        self.info: dict = {}
        self.notes: list[str] = []

    def open_entry(self, e: Entry):
        raise NotImplementedError

    def iter_data(self, wanted: set):
        raise NotImplementedError

    def close(self):
        pass


class _ZipHandler(_Handler):
    fmt, label = "zip", "ZIP"

    def __init__(self, fh, size, name):
        super().__init__()
        try:
            self.zf = zipfile.ZipFile(fh)
        except (zipfile.BadZipFile, EOFError, OSError, ValueError) as e:
            raise ContainerError("corrupt", "ZIP rusak: %s" % e)
        t0 = time.time()
        for i, zi in enumerate(self.zf.infolist()):
            if i >= _ex_MAX_ENTRIES or (i % 2000 == 0 and time.time() - t0 > LIST_TIME):
                self.truncated = True
                break
            mode = (zi.external_attr >> 16) & 0xFFFF if zi.create_system == 3 else 0
            if zi.filename.endswith("/") or zi.is_dir():
                kind = "dir"
            elif stat.S_ISLNK(mode):
                kind = "symlink"
            elif mode and not stat.S_ISREG(mode) and stat.S_IFMT(mode):
                kind = "other"
            else:
                kind = "file"
            try:
                mt = datetime(*zi.date_time, tzinfo=timezone.utc).timestamp()
            except (ValueError, OverflowError):
                mt = None
            self.entries.append(Entry(i, zi.filename.rstrip("/") if kind == "dir" else zi.filename, zi.file_size, zi.compress_size, kind, mt, bool(zi.flag_bits & 0x1), zi))
        if self.zf.comment:
            self.info["comment"] = _ex_clean(self.zf.comment.decode("utf-8", "replace"), 200)
        if any(e.path.endswith(("classes.dex", "AndroidManifest.xml")) for e in self.entries):
            self.info["hint"] = "APK / paket Android: gunakan analisis APK di rea_triage untuk manifest dan DEX"
        elif any(e.path == "META-INF/MANIFEST.MF" for e in self.entries):
            self.info["hint"] = "JAR (Java)"

    def open_entry(self, e):
        return self.zf.open(e.ref)

    def close(self):
        try:
            self.zf.close()
        except Exception:
            pass


class _TarHandler(_Handler):
    fmt, label, sequential = "tar", "TAR", True

    def __init__(self, fh, size, name, mode: str = "r:*", comp: str = ""):
        super().__init__()
        self.fh = fh
        self.comp = comp
        fh.seek(0)
        try:
            tf = tarfile.open(fileobj=fh, mode=mode)
        except tarfile.TarError as e:
            raise ContainerError("not_tar", "bukan TAR: %s" % e)
        except (OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            raise ContainerError("corrupt", "arsip rusak: %s" % e)
        t0 = time.time()
        try:
            for i, m in enumerate(tf):
                if i >= _ex_MAX_ENTRIES or (i % 2000 == 0 and time.time() - t0 > LIST_TIME):
                    self.truncated = True
                    break
                kind = "dir" if m.isdir() else "file" if m.isreg() else "symlink" if (m.issym() or m.islnk()) else "other"
                self.entries.append(Entry(i, m.name, m.size if kind == "file" else 0, 0, kind, m.mtime, False, None,
                                          ("-> " + _ex_clean(m.linkname, 80)) if kind == "symlink" else ""))
        except (tarfile.TarError, OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            if not self.entries:
                raise ContainerError("corrupt", "arsip rusak: %s" % e)
            self.truncated = True
            self.notes.append("arsip terpotong / rusak setelah %d entri: %s" % (len(self.entries), _ex_clean(e, 100)))
        finally:
            tf.close()
        if comp:
            self.label = "TAR + %s" % comp
            self.fmt = "tar." + {"gzip": "gz", "bzip2": "bz2", "xz": "xz"}.get(comp, comp)
            self.packed_total = size

    def iter_data(self, wanted: set):
        self.fh.seek(0)
        tf = tarfile.open(fileobj=self.fh, mode="r:*")
        try:
            last = max(wanted) if wanted else -1
            for i, m in enumerate(tf):
                if i > last:
                    break
                if i in wanted:
                    yield self.entries[i], tf.extractfile(m)
        finally:
            tf.close()


class _SingleHandler(_Handler):
    """GZIP / BZIP2 / XZ yang bukan tar: satu berkas di dalamnya."""

    def __init__(self, fh, size, name, comp: str):
        super().__init__()
        self.fh, self.comp, self.size_c = fh, comp, size
        self.fmt, self.label = {"gzip": ("gzip", "GZIP"), "bzip2": ("bzip2", "BZIP2"), "xz": ("xz", "XZ")}[comp]
        inner, mt, usize = None, None, -1
        if comp == "gzip":
            hdr = self._gz_header()
            if hdr is None:
                raise ContainerError("corrupt", "header GZIP tidak valid")
            inner, mt = hdr
            if size > 22:
                fh.seek(size - 4)
                usize = struct.unpack("<I", fh.read(4))[0]
                self.notes.append("ukuran dari trailer gzip (modulo 2^32)")
        if not inner:
            stem = Path(name).name
            for suf in (".gz", ".bz2", ".xz", ".tgz", ".gzip", ".bzip2"):
                if stem.lower().endswith(suf):
                    stem = stem[:-len(suf)]
                    break
            inner = stem if stem and stem != Path(name).name else (stem or "data") + ".out"
        # uji bahwa aliran memang bisa didekompresi
        try:
            s = self.open_entry(None)
            s.read(16)
            s.close()
        except (OSError, EOFError, zlib.error, lzma.LZMAError) as e:
            raise ContainerError("corrupt", "aliran %s rusak: %s" % (self.label, e))
        self.entries.append(Entry(0, inner, usize, size, "file", mt))

    def _gz_header(self):
        fh = self.fh
        fh.seek(0)
        h = fh.read(10)
        if len(h) < 10 or h[:2] != b"\x1f\x8b":
            return None
        flg, mt = h[3], struct.unpack("<I", h[4:8])[0]
        if flg & 4:
            xl = fh.read(2)
            if len(xl) < 2:
                return None
            fh.read(struct.unpack("<H", xl)[0])
        name = None
        if flg & 8:
            buf = b""
            while len(buf) < 512:
                c = fh.read(1)
                if not c or c == b"\0":
                    break
                buf += c
            name = buf.decode("latin-1") if buf else None
        return name, (mt or None)

    def open_entry(self, e):
        self.fh.seek(0)
        return {"gzip": lambda: gzip.GzipFile(fileobj=self.fh, mode="rb"), "bzip2": lambda: bz2.BZ2File(self.fh, "rb"),
                "xz": lambda: lzma.LZMAFile(self.fh, "rb")}[self.comp]()


# --- ISO 9660 / PSP -------------------------------------------------------------------------------

_ISO_LAYOUTS = ((2048, 0), (2352, 16), (2352, 24), (2336, 8))


def _find_iso_layout(img):
    for ss, doff in _ISO_LAYOUTS:
        if img.read_at(16 * ss + doff, 6) == b"\x01CD001":
            return ss, doff
    return None


def _parse_sfo(b: bytes) -> dict:
    if b[:4] != b"\x00PSF" or len(b) < 20:
        return {}
    out: dict = {}
    try:
        _v, kt, dt, n = struct.unpack_from("<4I", b, 4)
        for i in range(min(n, 256)):
            ko, fmt, ln, _mx, do = struct.unpack_from("<HHIII", b, 20 + 16 * i)
            end = b.index(b"\0", kt + ko)
            key = b[kt + ko:end].decode("ascii", "replace")
            raw = b[dt + do:dt + do + ln]
            out[key] = struct.unpack("<I", raw[:4].ljust(4, b"\0"))[0] if fmt == 0x0404 else raw.split(b"\0")[0].decode("utf-8", "replace")
    except (struct.error, ValueError):
        pass
    return out


class _ExtentStream:
    def __init__(self, h, extents):
        self.h, self.ext, self.i, self.off = h, [x for x in extents if x[1] > 0], 0, 0

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = 1 << 30
        out = []
        while n > 0 and self.i < len(self.ext):
            lba, sz = self.ext[self.i]
            rem = sz - self.off
            if rem <= 0:
                self.i += 1
                self.off = 0
                continue
            b = self.h.lread(lba * self.h.lbs + self.off, min(n, rem))
            if not b:
                raise EOFError("citra ISO terpotong di LBA %d" % lba)
            out.append(b)
            n -= len(b)
            self.off += len(b)
        return b"".join(out)

    def close(self):
        pass


class _IsoHandler(_Handler):
    fmt, label = "iso9660", "ISO 9660"

    def __init__(self, img, ss: int, doff: int, wrapper: str = ""):
        super().__init__()
        self.img, self.ss, self.doff, self.lbs = img, ss, doff, 2048
        if wrapper:
            self.info["wrapper"] = wrapper
        self._parse()

    def lread(self, lo: int, n: int) -> bytes:
        if self.ss == 2048 and self.doff == 0:
            return self.img.read_at(lo, n)
        out = []
        while n > 0:
            sec, w = divmod(lo, 2048)
            take = min(n, 2048 - w)
            b = self.img.read_at(sec * self.ss + self.doff + w, take)
            if not b:
                break
            out.append(b)
            lo += len(b)
            n -= len(b)
        return b"".join(out)

    @staticmethod
    def _date7(b: bytes):
        try:
            tz = b[6] - 256 if b[6] > 127 else b[6]
            return datetime(1900 + b[0], b[1], b[2], b[3], b[4], b[5], tzinfo=timezone(timedelta(minutes=15 * tz))).timestamp()
        except (ValueError, OverflowError, IndexError):
            return None

    def _parse(self):
        pvd = joliet = None
        for sec in range(16, 16 + 32):
            d = self.lread(sec * 2048, 2048)
            if len(d) < 2048 or d[1:6] != b"CD001":
                break
            if d[0] == 1 and pvd is None:
                pvd = d
            elif d[0] == 2 and joliet is None and d[88:91] in (b"%/@", b"%/C", b"%/E"):
                joliet = d
            elif d[0] == 255:
                break
        if pvd is None and joliet is None:
            raise ContainerError("corrupt", "descriptor volume ISO 9660 tidak ditemukan")
        vd = joliet or pvd
        use_joliet = joliet is not None
        lbs = struct.unpack_from("<H", vd, 128)[0]
        self.lbs = lbs if lbs in (512, 1024, 2048, 4096) else 2048
        if pvd is not None:
            self.info["volume_id"] = _ex_clean(pvd[40:72].decode("latin-1").strip(), 40)
            self.info["system_id"] = _ex_clean(pvd[8:40].decode("latin-1").strip(), 40)
            vs = struct.unpack_from("<I", pvd, 80)[0]
            self.info["volume_size"] = vs * self.lbs
            cd = pvd[813:827].decode("ascii", "replace")
            if cd.isdigit() and cd != "0" * 14:
                self.info["created"] = "%s-%s-%s %s:%s:%s" % (cd[0:4], cd[4:6], cd[6:8], cd[8:10], cd[10:12], cd[12:14])
        self.info["names"] = "Joliet" if use_joliet else "ISO 9660"
        root = vd[156:190]
        stack = [(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "", 0)]
        seen = set()
        t0 = time.time()
        rr_seen = False
        while stack:
            lba, dsize, prefix, depth = stack.pop()
            if lba in seen or depth > MAX_DEPTH or dsize <= 0 or dsize > MAX_DIR_BYTES:
                continue
            seen.add(lba)
            data = self.lread(lba * self.lbs, dsize)
            pos, pend, pname = 0, None, None
            while pos < len(data):
                l = data[pos]
                if l == 0:
                    pos = (pos // 2048 + 1) * 2048
                    continue
                rec = data[pos:pos + l]
                pos += l
                if l < 34 or len(rec) < l:
                    continue
                nlen = rec[32]
                fi = rec[33:33 + nlen]
                if nlen == 0 or fi in (b"\x00", b"\x01"):
                    continue
                flags = rec[25]
                elba, esz = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
                mt = self._date7(rec[18:25])
                if use_joliet:
                    name = fi.decode("utf-16-be", "replace")
                else:
                    name = fi.decode("latin-1")
                su = rec[33 + nlen + (1 if nlen % 2 == 0 else 0):]
                rr_name, is_link = self._susp(su)
                if rr_name and not use_joliet:
                    name, rr_seen = rr_name, True
                else:
                    name = re.sub(r";\d+$", "", name)
                    if len(name) > 1 and name.endswith("."):
                        name = name[:-1]
                is_dir = bool(flags & 0x02)
                if not is_dir and (flags & 0x80):        # multi-extent: kumpulkan sampai rekaman terakhir
                    pend = (pend or []) + [(elba, esz)]
                    pname = pname or name
                    continue
                if pend is not None:
                    exts, name, pend, pname = pend + [(elba, esz)], pname or name, None, None
                else:
                    exts = [(elba, esz)]
                path = prefix + name
                if is_dir:
                    self.entries.append(Entry(len(self.entries), path, 0, 0, "dir", mt))
                    stack.append((elba, esz, path + "/", depth + 1))
                else:
                    self.entries.append(Entry(len(self.entries), path, sum(x[1] for x in exts), 0, "symlink" if is_link else "file", mt, False, exts))
                if len(self.entries) >= _ex_MAX_ENTRIES or time.time() - t0 > LIST_TIME:
                    self.truncated = True
                    stack.clear()
                    break
        if rr_seen:
            self.info["names"] = "ISO 9660 + Rock Ridge"
        if not self.entries:
            self.notes.append("ISO tanpa entri berkas yang terbaca")
        self._psp()

    @staticmethod
    def _susp(su: bytes):
        """Rock Ridge: NM (nama) dan PX/SL (deteksi tautan simbolik). Mengembalikan (nama | None, tautan?)."""
        name, link, p = b"", False, 0
        while p + 4 <= len(su):
            sig, ln = su[p:p + 2], su[p + 2]
            if ln < 4 or p + ln > len(su):
                break
            body = su[p + 4:p + ln]
            if sig == b"NM" and body:
                name += body[1:]
            elif sig == b"SL":
                link = True
            elif sig == b"PX" and len(body) >= 4 and stat.S_ISLNK(struct.unpack_from("<I", body, 0)[0]):
                link = True
            p += ln
        return (name.decode("utf-8", "replace") if name else None), link

    def _psp(self):
        up = {e.path.upper(): e for e in self.entries}
        if not any(k.startswith("PSP_GAME/") or k == "PSP_GAME" for k in up):
            return
        self.fmt, self.label = "iso-psp", "ISO PSP (UMD)"
        sfo = up.get("PSP_GAME/PARAM.SFO")
        if sfo is not None and sfo.kind == "file" and 0 < sfo.size <= 65536:
            try:
                kv = _parse_sfo(_ExtentStream(self, sfo.ref).read(sfo.size))
                for k in ("TITLE", "DISC_ID", "DISC_VERSION", "APP_VER", "CATEGORY", "PSP_SYSTEM_VER", "PARENTAL_LEVEL", "REGION"):
                    if k in kv:
                        self.info["psp_" + k.lower()] = _ex_clean(kv[k], 100)
            except (EOFError, OSError, ContainerError):
                self.notes.append("PARAM.SFO tidak terbaca")
        eb = up.get("PSP_GAME/SYSDIR/EBOOT.BIN")
        if eb is not None and eb.kind == "file" and eb.size >= 4:
            try:
                magic = _ExtentStream(self, eb.ref).read(4)
                self.info["eboot"] = "terenkripsi (~PSP): tidak bisa dianalisis statis tanpa dekripsi" if magic == b"~PSP" else (
                    "ELF / PRX tidak terenkripsi" if magic == b"\x7fELF" else "PBP" if magic == b"\x00PBP" else "magic %s" % magic.hex())
            except (EOFError, OSError):
                pass

    def open_entry(self, e):
        return _ExtentStream(self, e.ref)


# ---------------------------------------------------------------------------------------------------
# Deteksi format
# ---------------------------------------------------------------------------------------------------

def _ex_open_regular(path):
    """Buka SEKALI, lalu fstat: hanya berkas biasa (tolak FIFO / perangkat / folder) tanpa celah TOCTOU."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(str(Path(str(path)).expanduser()), flags)
    except FileNotFoundError:
        raise ContainerError("not_found", "berkas tidak ditemukan: %s" % _ex_clean(path, 120))
    except IsADirectoryError:
        raise ContainerError("is_directory", "path adalah folder, bukan berkas")
    except PermissionError:
        raise ContainerError("permission", "tidak punya izin membaca: %s" % _ex_clean(path, 120))
    except OSError as e:
        raise ContainerError("io_error", "%s: %s" % (type(e).__name__, e))
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ContainerError("not_regular", "bukan berkas biasa (FIFO / perangkat / folder ditolak)")
        return os.fdopen(fd, "rb"), st.st_size
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def _make_handler(fh, size: int, name: str) -> _Handler:
    if size == 0:
        raise ContainerError("empty", "berkas kosong (0 byte)")
    base = _FileImg(fh, size)
    head = base.read_at(0, 8)
    if head[:4] == b"CISO":
        cso = _CsoImg(base)
        lay = _find_iso_layout(cso)
        if lay is None:
            raise ContainerError("unsupported_format", "CSO tidak berisi ISO 9660 yang valid")
        h = _IsoHandler(cso, lay[0], lay[1], wrapper="CSO (zlib per blok, blok %d byte, ukuran asli %s)" % (cso.bsz, _ex_human(cso.size)))
        return h
    if head[:4] == b"ZISO":
        raise ContainerError("unsupported_format", "ZSO (LZ4 PSP) belum didukung; ubah ke ISO / CSO dengan ciso / maxcso")
    lay = _find_iso_layout(base)
    if lay:
        return _IsoHandler(base, lay[0], lay[1])
    for magic, comp, mode in ((b"\x1f\x8b", "gzip", "r:gz"), (b"BZh", "bzip2", "r:bz2"), (b"\xfd7zXZ\x00", "xz", "r:xz")):
        if head.startswith(magic):
            try:
                return _TarHandler(fh, size, name, mode, comp)
            except ContainerError as e:
                if e.code != "not_tar":
                    raise
            return _SingleHandler(fh, size, name, comp)
    if head[:2] == b"PK" or zipfile.is_zipfile(fh):
        return _ZipHandler(fh, size, name)
    try:
        return _TarHandler(fh, size, name, "r:", "")
    except ContainerError:
        pass
    if head[:6] == b"7z\xbc\xaf\x27\x1c" or head[:4] == b"Rar!":
        raise ContainerError("unsupported_format", "7z / RAR belum didukung di rea_extract (pakai `unpack7z` di rea_triage bila 7-Zip terpasang)")
    raise ContainerError("unsupported_format", "format container tidak dikenal (didukung: ZIP, TAR, GZIP, BZIP2, XZ, ISO 9660, ISO PSP, CSO)")


def _ex_formats() -> list:
    return [{"name": "zip", "about": "ZIP / APK / JAR / SFX, tanpa kata sandi"},
            {"name": "tar", "about": "TAR, TAR.GZ / .BZ2 / .XZ (sekuensial)"},
            {"name": "gzip / bzip2 / xz", "about": "aliran terkompresi tunggal"},
            {"name": "iso9660", "about": "ISO 9660 (Joliet, Rock Ridge, sektor 2048 / raw 2352 / 2336, multi-extent)"},
            {"name": "iso-psp", "about": "ISO UMD PSP: info PARAM.SFO / EBOOT"},
            {"name": "cso", "about": "CSO PSP (zlib per blok) berisi ISO"}]


# ---------------------------------------------------------------------------------------------------
# Registri container terbuka
# ---------------------------------------------------------------------------------------------------

class _Container:
    def __init__(self, cid, path, fh, size, handler):
        self.id, self.path, self.fh, self.size, self.h = cid, path, fh, size, handler
        self.lock = threading.RLock()
        self.t = time.time()

    def close(self):
        with self.lock:
            try:
                self.h.close()
            finally:
                try:
                    self.fh.close()
                except OSError:
                    pass


_OPEN: dict = {}
_OPEN_LOCK = threading.Lock()


def open_container(path) -> dict:
    """Buka container (hanya-baca) dan daftar isinya. Tutup dengan close_container()."""
    fh = None
    try:
        fh, size = _ex_open_regular(path)
        name = Path(str(path)).name
        h = _make_handler(fh, size, name)
        cid = "c" + secrets.token_hex(6)
        c = _Container(cid, Path(str(path)).expanduser(), fh, size, h)
        with _OPEN_LOCK:
            while len(_OPEN) >= MAX_OPEN:                      # buang yang tertua supaya tidak bocor
                old = min(_OPEN.values(), key=lambda x: x.t)
                _OPEN.pop(old.id, None)
                old.close()
            _OPEN[cid] = c
        files = sum(1 for e in h.entries if e.kind == "file")
        return {"status": "success", "container_id": cid, "format": h.fmt, "label": h.label, "path": str(c.path), "size": size,
                "entries": len(h.entries), "files": files, "truncated": h.truncated, "info": dict(h.info), "notes": list(h.notes)}
    except ContainerError as e:
        if fh:
            fh.close()
        return _ex_err(e.code, e)
    except Exception as e:
        if fh:
            try:
                fh.close()
            except OSError:
                pass
        return _ex_err("open_failed", "%s: %s" % (type(e).__name__, e))


def close_container(container_id) -> dict:
    with _OPEN_LOCK:
        c = _OPEN.pop(str(container_id), None)
    if c is None:
        return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
    c.close()
    return {"status": "success"}


def _get(cid):
    with _OPEN_LOCK:
        c = _OPEN.get(str(cid))
    if c:
        c.t = time.time()
    return c


def list_entries(container_id, limit: int = 0) -> dict:
    c = _get(container_id)
    if c is None:
        return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
    es = c.h.entries if limit <= 0 else c.h.entries[:limit]
    return {"status": "success", "format": c.h.fmt, "total": len(c.h.entries), "truncated": c.h.truncated, "entries": [e.as_dict() for e in es]}


# ---------------------------------------------------------------------------------------------------
# Pemilih entri
# ---------------------------------------------------------------------------------------------------

def _compile_selector(sel):
    """-> (predikat(Entry) -> bool, max_entries | None). selector: None | str (pola) | dict."""
    if sel in (None, "", {}):
        return (lambda e: True), None
    if isinstance(sel, str):
        sel = {"pattern": sel}
    if not isinstance(sel, dict):
        raise ValueError("selector harus dict / string / None")
    pats = []

    def add(spec, bucket):
        for s in re.split(r"[;,\n]", str(spec)) if not str(spec).startswith("re:") else [str(spec)]:
            s = s.strip()
            if not s:
                continue
            if s.startswith("re:"):
                if len(s) > 400:
                    raise ValueError("regex terlalu panjang")
                bucket.append(("re", re.compile(s[3:], re.I)))
            elif any(ch in s for ch in "*?["):
                bucket.append(("glob", s.lower()))
            else:
                bucket.append(("sub", s.lower()))

    inc, exc = [], []
    if sel.get("pattern"):
        add(sel["pattern"], inc)
    if sel.get("exclude"):
        add(sel["exclude"], exc)
    paths = {str(p).replace("\\", "/").strip("/").lower() for p in (sel.get("paths") or [])}
    max_size = sel.get("max_size")
    max_size = int(max_size) if max_size not in (None, "") else None
    max_entries = sel.get("max_entries")
    max_entries = int(max_entries) if max_entries not in (None, "") else None

    def hit(e, bucket):
        full = e.path.replace("\\", "/").lower()
        base = full.rsplit("/", 1)[-1]
        for kind, p in bucket:
            if kind == "re" and p.search(e.path):
                return True
            if kind == "glob" and (fnmatch.fnmatchcase(full, p) or fnmatch.fnmatchcase(base, p)):
                return True
            if kind == "sub" and p in full:
                return True
        return False

    def pred(e):
        full = e.path.replace("\\", "/").strip("/").lower()
        if paths and full not in paths:
            return False
        if inc and not hit(e, inc):
            return False
        if exc and hit(e, exc):
            return False
        if max_size is not None and e.size is not None and e.size > max_size:
            return False
        return True

    return pred, max_entries


# ---------------------------------------------------------------------------------------------------
# Ekstraksi
# ---------------------------------------------------------------------------------------------------

def _unique_path(root: Path, rel: str):
    target = (root / rel).resolve()
    if root != target and root not in target.parents:
        return None
    return target


def _sha256_stream(fh, size) -> str | None:
    if size > SOURCE_HASH_LIMIT:
        return None
    h = hashlib.sha256()
    fh.seek(0)
    while True:
        b = fh.read(COPY_CHUNK)
        if not b:
            break
        h.update(b)
    return h.hexdigest()


def _scan_flags(rel: str, typ: str, entropy: float, size: int) -> list:
    flags = []
    name = rel.rsplit("/", 1)[-1].lower()
    ext = os.path.splitext(name)[1]
    exe_type = typ in ("PE", "DOS MZ", "ELF", "Mach-O / class", "LNK", "skrip (shebang)", "PSP PRX terenkripsi")
    if exe_type:
        flags.append("berisi kode yang bisa dieksekusi (%s)" % typ)
    if exe_type and ext and ext not in _EXEC_EXT:
        flags.append("jenis %s menyamar dengan ekstensi %s" % (typ, ext))
    if re.search(r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|gif|txt|mp3|mp4|zip|rar)\.(exe|scr|com|bat|cmd|js|vbs|lnk|pif|hta)$", name):
        flags.append("ekstensi ganda menyesatkan")
    if typ in _ARCHIVE_TYPES and typ != "TAR":
        flags.append("container bersarang (%s): belum diekstrak otomatis" % typ)
    if entropy >= 7.5 and size >= 4096 and typ not in _ARCHIVE_TYPES and typ not in ("PNG", "JPEG", "GIF", "OGG", "RIFF", "PDF"):
        flags.append("entropi tinggi %.2f (terkompresi / terenkripsi / packed?)" % entropy)
    return flags


def extract_selected(container_id, selector=None, outdir=None, scan: bool = False) -> dict:
    """Ekstraksi selektif ke workspace `outdir`. Mengembalikan manifest (dict). Tidak pernah melempar."""
    try:
        c = _get(container_id)
        if c is None:
            return _ex_err("no_such_container", "container_id tidak dikenal / sudah ditutup")
        if not outdir:
            return _ex_err("no_outdir", "outdir wajib diisi")
        with c.lock:
            return _do_extract(c, selector, Path(str(outdir)).expanduser(), bool(scan))
    except ValueError as e:
        return _ex_err("bad_selector", e)
    except re.error as e:
        return _ex_err("bad_selector", "regex tidak valid: %s" % e)
    except Exception as e:
        return _ex_err("extract_failed", "%s: %s" % (type(e).__name__, e))


def _do_extract(c: _Container, selector, outdir: Path, scan: bool) -> dict:
    h = c.h
    pred, max_entries = _compile_selector(selector)
    outdir.mkdir(parents=True, exist_ok=True)
    root = outdir.resolve()
    ext_root, man_root, log_root = root / "extracted", root / "manifests", root / "logs"
    for d in (ext_root, man_root, log_root):
        d.mkdir(parents=True, exist_ok=True)
    ext_root = ext_root.resolve()
    log: list = []

    def L(msg):
        log.append("%s %s" % (datetime.now(timezone.utc).strftime("%H:%M:%S"), _ex_clean(msg, 300)))

    L("buka %s (%s, %d entri)" % (_ex_clean(c.path.name, 80), h.label, len(h.entries)))
    matched = [e for e in h.entries if e.kind != "dir" and pred(e)]
    notes: list = []
    if max_entries is not None and len(matched) > max_entries:
        notes.append("dibatasi max_entries=%d dari %d entri yang cocok" % (max_entries, len(matched)))
        matched = matched[:max_entries]
    files: list = []
    skipped: list = []
    errors: list = []
    warnings: list = []
    state = {"total": 0}
    todo: list = []
    for e in matched:
        if e.kind != "file":
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "%s tidak diekstrak (kebijakan keamanan)%s" % ("tautan simbolik" if e.kind == "symlink" else "berkas khusus", " " + e.note if e.note else ""), "benign": True})
        elif e.encrypted:
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "terenkripsi (kata sandi tidak didukung)", "benign": False})
        elif e.size is not None and e.size > MAX_ENTRY_BYTES:
            skipped.append({"path": _ex_clean(e.path, 200), "size": e.size, "reason": "melebihi batas ukuran per berkas (%s)" % _ex_human(MAX_ENTRY_BYTES), "benign": False})
        else:
            todo.append(e)

    used: set = set()

    def new_target(rel: str):
        t = _unique_path(ext_root, rel)
        if t is None:
            return None
        stem, suf, k = t.stem, t.suffix, 1
        while str(t).lower() in used or t.exists():
            k += 1
            t = t.with_name("%s_%d%s" % (stem, k, suf))
        used.add(str(t).lower())
        return t

    def write_one(e: Entry, stream):
        rel, unsafe = _ex_safe_rel(e.path)
        if unsafe:
            warnings.append("path berbahaya dinetralkan: %s -> %s" % (_ex_clean(e.path, 120), rel))
            L("netralkan path berbahaya: %s" % _ex_clean(e.path, 120))
        tgt = new_target(rel)
        if tgt is None:
            skipped.append({"path": _ex_clean(e.path, 200), "reason": "path di luar workspace", "benign": False})
            return
        try:
            tgt.parent.mkdir(parents=True, exist_ok=True)
        except (FileExistsError, NotADirectoryError):
            errors.append("%s: konflik nama (induk adalah berkas)" % _ex_clean(e.path, 120))
            return
        sha, written, head = hashlib.sha256(), 0, b""
        ratio_cap = max(RATIO_FLOOR, e.packed * MAX_RATIO) if e.packed and e.packed > 0 else None
        try:
            with open(tgt, "xb") as out:
                while True:
                    b = stream.read(COPY_CHUNK)
                    if not b:
                        break
                    written += len(b)
                    if written > MAX_ENTRY_BYTES:
                        raise _Limit("melebihi batas ukuran per berkas (%s)" % _ex_human(MAX_ENTRY_BYTES))
                    if state["total"] + written > MAX_TOTAL_BYTES:
                        raise _Limit("melebihi batas total ekstraksi (%s)" % _ex_human(MAX_TOTAL_BYTES))
                    if ratio_cap and written > ratio_cap:
                        raise _Limit("rasio kompresi mencurigakan (zip bomb?)")
                    if len(head) < 1 << 20:
                        head += b[:(1 << 20) - len(head)]
                    sha.update(b)
                    out.write(b)
        except _Limit as x:
            _rm(tgt)
            skipped.append({"path": _ex_clean(e.path, 200), "reason": str(x), "benign": False})
            L("lewati %s: %s" % (_ex_clean(e.path, 100), x))
            return
        except Exception as x:
            _rm(tgt)
            errors.append("%s: %s: %s" % (_ex_clean(e.path, 120), type(x).__name__, _ex_clean(x, 120)))
            L("gagal %s: %s" % (_ex_clean(e.path, 100), type(x).__name__))
            return
        state["total"] += written
        if e.mtime:
            try:
                os.utime(tgt, (e.mtime, e.mtime))
            except (OSError, OverflowError, ValueError):
                pass
        typ = _sniff(head[:2048] if written < 32774 else head[:32800])
        rec = {"path": tgt.relative_to(root).as_posix(), "source": _ex_clean(e.path, 300), "size": written, "sha256": sha.hexdigest(), "type": typ,
               "mtime": _ts(e.mtime), "note": "path dinetralkan" if (unsafe or rel != e.path.replace("\\", "/")) else ""}
        if scan:
            rec["entropy"] = round(_ex_entropy(head[:1 << 20]), 3)
            fl = _scan_flags(rel, typ, rec["entropy"], written)
            if unsafe:
                fl.insert(0, "path traversal / absolut di dalam arsip")
            if fl:
                rec["flags"] = fl
        files.append(rec)

    if todo:
        wanted = {e.index for e in todo}
        by_index = {e.index: e for e in todo}
        if h.sequential:
            try:
                for e, stream in h.iter_data(wanted):
                    if stream is None:
                        errors.append("%s: tidak bisa dibuka" % _ex_clean(e.path, 120))
                        continue
                    try:
                        write_one(e, stream)
                    finally:
                        _close(stream)
            except Exception as x:
                errors.append("arsip berhenti di tengah jalan: %s: %s" % (type(x).__name__, _ex_clean(x, 120)))
                L("arsip berhenti: %s" % type(x).__name__)
        else:
            for e in todo:
                try:
                    stream = h.open_entry(e)
                except Exception as x:
                    errors.append("%s: %s: %s" % (_ex_clean(e.path, 120), type(x).__name__, _ex_clean(x, 120)))
                    continue
                try:
                    write_one(by_index[e.index], stream)
                finally:
                    _close(stream)

    # ---- manifest
    benign_only = all(s.get("benign") for s in skipped)
    if not matched:
        status, code, msg = "error", "no_match", "tidak ada entri berkas yang cocok dengan selector (total %d entri)" % len(h.entries)
    elif not files:
        status, code, msg = "error", "nothing_extracted", "tidak ada yang berhasil diekstrak" + (": " + errors[0] if errors else (": " + skipped[0]["reason"] if skipped else ""))
    elif errors or not benign_only:
        status, code, msg = "partial", None, None
    else:
        status, code, msg = "success", None, None
    scan_info = None
    if scan:
        by_type = Counter(f["type"] for f in files)
        scan_info = {"files_scanned": len(files), "by_type": dict(by_type.most_common()),
                     "flagged": [{"path": f["path"], "reasons": f["flags"]} for f in files if f.get("flags")]}
    man = {"status": status, "version": _ex_VERSION, "format": h.fmt, "format_label": h.label, "source": str(c.path), "source_size": c.size,
           "source_sha256": _sha256_stream(c.fh, c.size), "outdir": str(root),
           "workspace": {"extracted": str(ext_root), "manifests": str(man_root), "logs": str(log_root)},
           "time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "selector": selector if isinstance(selector, (dict, str)) else None,
           "entries_total": len(h.entries), "entries_matched": len(matched), "entries_extracted": len(files), "entries_skipped": len(skipped),
           "entries_failed": len(errors), "bytes_extracted": state["total"], "container_truncated": h.truncated,
           "container_info": dict(h.info), "files": files, "skipped": skipped, "errors": errors, "warnings": warnings + notes + list(h.notes), "scan": scan_info}
    if code:
        man["code"], man["message"] = code, msg
    L("selesai: status=%s diekstrak=%d dilewati=%d gagal=%d" % (status, len(files), len(skipped), len(errors)))
    try:
        lp = _free_name(log_root, "extract", ".log")
        lp.write_text("\n".join(log) + "\n", encoding="utf-8")
        man["log_path"] = str(lp)
        mp = _free_name(man_root, "manifest", ".json")
        man["manifest_path"] = str(mp)
        mp.write_text(json.dumps(man, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    except OSError as x:
        man["warnings"].append("manifest / log tidak bisa ditulis: %s" % _ex_clean(x, 100))
        man.pop("manifest_path", None)
    return man


def _free_name(folder: Path, stem: str, suffix: str) -> Path:
    p, k = folder / (stem + suffix), 1
    while p.exists():
        k += 1
        p = folder / ("%s_%d%s" % (stem, k, suffix))
    return p


def _rm(p: Path):
    try:
        p.unlink()
    except OSError:
        pass


def _close(s):
    try:
        s.close()
    except Exception:
        pass


def _ex_extract(path, outdir, pattern=None, scan: bool = False) -> dict:
    """Pembungkus: buka -> ekstrak -> tutup."""
    r = open_container(path)
    if r.get("status") != "success":
        return r
    try:
        return extract_selected(r["container_id"], {"pattern": pattern} if pattern else None, outdir, scan=scan)
    finally:
        close_container(r["container_id"])


# ---------------------------------------------------------------------------------------------------
# Deskripsi
# ---------------------------------------------------------------------------------------------------

def _entry_flags(e: Entry) -> list:
    f = []
    rel, unsafe = _ex_safe_rel(e.path)
    if unsafe:
        f.append("PATH-BERBAHAYA")
    if e.encrypted:
        f.append("ENKRIPSI")
    if e.kind == "symlink":
        f.append("TAUTAN")
    elif e.kind == "other":
        f.append("KHUSUS")
    if e.kind == "file":
        ext = os.path.splitext(e.path.lower())[1]
        if ext in _EXEC_EXT:
            f.append("EKSEKUSI")
        if re.search(r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|gif|txt|mp3|mp4|zip|rar)\.(exe|scr|com|bat|cmd|js|vbs|lnk|pif|hta)$", e.path.lower()):
            f.append("EKSTENSI-GANDA")
        if e.packed and e.size and e.packed > 0 and e.size > 10 * 1024 * 1024 and e.size / e.packed > 1000:
            f.append("RASIO-TINGGI")
    return f


def describe_container(path) -> dict:
    r = open_container(path)
    if r.get("status") != "success":
        return r
    try:
        c = _get(r["container_id"])
        h = c.h
        files = [e for e in h.entries if e.kind == "file"]
        total = sum(e.size for e in files if e.size and e.size > 0)
        packed = sum(e.packed for e in files if e.packed)
        exts = Counter(os.path.splitext(e.path.lower())[1] or "(tanpa ekstensi)" for e in files)
        flagged = [(e, _entry_flags(e)) for e in h.entries]
        flagged = [(e, f) for e, f in flagged if f]
        return {"status": "success", "format": h.fmt, "label": h.label, "path": str(c.path), "size": c.size, "entries_total": len(h.entries),
                "files": len(files), "dirs": sum(1 for e in h.entries if e.kind == "dir"), "total_size": total, "packed_total": packed,
                "info": dict(h.info), "notes": list(h.notes), "truncated": h.truncated, "top_extensions": dict(exts.most_common(8)),
                "flagged": [{"path": _ex_clean(e.path, 200), "flags": f} for e, f in flagged[:100]],
                "entries": [e.as_dict() for e in h.entries[:MAX_LIST_ROWS]]}
    finally:
        close_container(r["container_id"])


def describe_container_text(path, max_chars: int = 0) -> str:
    """Daftar isi ringkas untuk laporan / Hermes. Tidak melempar."""
    try:
        d = describe_container(path)
        if d.get("status") != "success":
            return "CONTAINER gagal dibuka: %s" % d.get("message", d.get("code"))
        head = "CONTAINER: %s | %d entri (%d berkas, %d folder) | isi %s%s" % (
            d["label"], d["entries_total"], d["files"], d["dirs"], _ex_human(d["total_size"]),
            " (terkompresi %s, rasio %.1fx)" % (_ex_human(d["packed_total"]), d["total_size"] / d["packed_total"]) if d["packed_total"] else "")
        L = [head, "  Berkas: %s (%s)%s" % (_ex_clean(Path(str(path)).name, 100), _ex_human(d["size"]), " | DAFTAR DIPOTONG (batas entri / waktu)" if d["truncated"] else "")]
        info = d["info"]
        if info.get("wrapper"):
            L.append("  Pembungkus: %s" % info["wrapper"])
        if info.get("volume_id") or info.get("names"):
            L.append("  Volume: %s | sistem: %s | nama: %s%s" % (info.get("volume_id", "?") or "-", info.get("system_id", "?") or "-", info.get("names", "?"),
                                                                 " | dibuat %s" % info["created"] if info.get("created") else ""))
        if info.get("psp_title") or info.get("psp_disc_id"):
            L.append("  PSP: judul %s | ID %s | versi disc %s | app %s | kategori %s | firmware %s" % (
                info.get("psp_title", "?"), info.get("psp_disc_id", "?"), info.get("psp_disc_version", "?"), info.get("psp_app_ver", "?"),
                info.get("psp_category", "?"), info.get("psp_psp_system_ver", "?")))
        if info.get("eboot"):
            L.append("  EBOOT.BIN: %s" % info["eboot"])
        for k in ("hint", "comment"):
            if info.get(k):
                L.append("  %s: %s" % ("Petunjuk" if k == "hint" else "Komentar", info[k]))
        L += ["  Catatan: %s" % n for n in d["notes"]]
        if d["top_extensions"]:
            L.append("  Ekstensi: " + ", ".join("%s x%d" % (k, v) for k, v in d["top_extensions"].items()))
        if d["flagged"]:
            L.append("  PERHATIAN: %d entri mencurigakan" % len(d["flagged"]))
            L += ["    %s  [%s]" % (x["path"], ", ".join(x["flags"])) for x in d["flagged"][:12]]
            if len(d["flagged"]) > 12:
                L.append("    ... +%d lagi" % (len(d["flagged"]) - 12))
        L.append("  Isi:")
        for e in d["entries"][:80]:
            fl = _entry_flags_from_dict(e)
            L.append("   %s %10s  %s%s" % ("d" if e["kind"] == "dir" else "l" if e["kind"] == "symlink" else "-", "" if e["kind"] == "dir" else _ex_human(e["size"]),
                                          e["path"] + ("/" if e["kind"] == "dir" else ""), "  [%s]" % ", ".join(fl) if fl else ""))
        if d["entries_total"] > 80:
            L.append("   ... +%d entri lagi (gunakan extract / list_entries untuk daftar penuh)" % (d["entries_total"] - 80))
        text = "\n".join(L)
        if max_chars and len(text) > max_chars:
            text = text[:max_chars - 30] + "\n[...dipangkas supaya muat...]"
        return text
    except Exception as e:
        return "CONTAINER gagal dibaca (%s: %s)." % (type(e).__name__, _ex_clean(e, 120))


def _entry_flags_from_dict(e: dict) -> list:
    return _entry_flags(Entry(0, e["path"], e["size"], e["packed"], e["kind"], None, e["encrypted"]))


# ---------------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------------

def _ex_main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_EX_DOC.split("CLI:")[1].strip())
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "formats":
        for f in _ex_formats():
            print("%-18s %s" % (f["name"], f["about"]))
        return 0
    if cmd == "list" and rest:
        print(describe_container_text(rest[0]))
        return 0
    if cmd == "extract" and len(rest) >= 2:
        scan = "--scan" in rest
        pos = [x for x in rest if not x.startswith("--")]
        m = _ex_extract(pos[0], pos[1], pattern=pos[2] if len(pos) > 2 else None, scan=scan)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s | manifest: %s%s" % (m.get("status"), m.get("entries_extracted"), m.get("entries_skipped"),
                                                                            m.get("entries_failed"), m.get("manifest_path"), (" | " + m["message"]) if m.get("message") else ""))
        for f in (m.get("scan") or {}).get("flagged", [])[:20]:
            print("  PERHATIAN %s: %s" % (f["path"], "; ".join(f["reasons"])))
        return 0 if m.get("status") == "success" else 1
    print("pemakaian: python rea_extract.py list FILE | extract FILE OUTDIR [pola] [--scan] | formats")
    return 1

_BN_PUBLIC = frozenset(['COMPARE_CHUNK', 'HASH_LIMIT', 'MAX_BACKUP', 'MAX_DIR_FILES', 'MAX_HEX', 'MAX_HITS', 'MAX_JOURNAL', 'MAX_PATCH', 'MAX_RANGES', 'SEARCH_CHUNK', 'SEARCH_OVERLAP', 'SEARCH_TIME', 'VERSION', '_ASCII', '_EBCDIC', '_ENC_ALIASES', '_LATIN1', '_NotRegular', '_Src', '_as_bytes', '_clean', '_compile_pattern', '_ebcdic_table', '_err', '_fail', '_fmt_time', '_fsync_write', '_journal_path', '_load_journal', '_norm_offset', '_opt', '_orig_path', '_parse_hex', '_plausible', '_same_content', '_save_journal', '_sha256_file', '_text_column', '_to_int', '_walk_files', 'compare_dirs', 'compare_files', 'hex_view', 'history', 'inspect_at', 'inspect_text', 'main', 'patch', 'patch_text', 'restore_original', 'search', 'search_text', 'undo'])
_BN_RENAMED = {'_ASCII': '_bn_ASCII', 'VERSION': '_bn_VERSION', 'main': '_bn_main', '_err': '_bn_err', '_clean': '_bn_clean'}
_EX_PUBLIC = frozenset(['COPY_CHUNK', 'ContainerError', 'Entry', 'LIST_TIME', 'MAX_DEPTH', 'MAX_DIR_BYTES', 'MAX_ENTRIES', 'MAX_ENTRY_BYTES', 'MAX_LIST_ROWS', 'MAX_OPEN', 'MAX_RATIO', 'MAX_TOTAL_BYTES', 'RATIO_FLOOR', 'SOURCE_HASH_LIMIT', 'VERSION', '_ARCHIVE_TYPES', '_Container', '_CsoImg', '_EXEC_EXT', '_ExtentStream', '_FileImg', '_Handler', '_ISO_LAYOUTS', '_IsoHandler', '_Limit', '_OPEN', '_OPEN_LOCK', '_RESERVED', '_SingleHandler', '_TarHandler', '_ZipHandler', '_clean', '_close', '_compile_selector', '_do_extract', '_entropy', '_entry_flags', '_entry_flags_from_dict', '_err', '_find_iso_layout', '_free_name', '_get', '_human', '_make_handler', '_open_regular', '_parse_sfo', '_rm', '_safe_rel', '_scan_flags', '_sha256_stream', '_sniff', '_ts', '_unique_path', 'close_container', 'describe_container', 'describe_container_text', 'extract', 'extract_selected', 'formats', 'list_entries', 'main', 'open_container'])
_EX_RENAMED = {'extract': '_ex_extract', 'formats': '_ex_formats', '_human': '_ex_human', '_RESERVED': '_ex_RESERVED', 'main': '_ex_main', '_entropy': '_ex_entropy', '_err': '_ex_err', '_clean': '_ex_clean', 'VERSION': '_ex_VERSION', '_open_regular': '_ex_open_regular', 'MAX_ENTRIES': '_ex_MAX_ENTRIES', '_safe_rel': '_ex_safe_rel'}


class _ModAPI:
    """Fasad pengganti `import rea_binary` / `import rea_extract`: hanya nama publik modul asal yang bisa diakses (nama bentrok dipetakan ke _bn_* / _ex_*)."""
    __slots__ = ("_pub", "_ren")

    def __init__(self, pub, ren):
        object.__setattr__(self, "_pub", pub)
        object.__setattr__(self, "_ren", ren)

    def __getattr__(self, name):
        if name not in self._pub:
            raise AttributeError(name)
        return globals()[self._ren.get(name, name)]


_BN_API = _ModAPI(_BN_PUBLIC, _BN_RENAMED)
_EX_API = _ModAPI(_EX_PUBLIC, _EX_RENAMED)


def _binary_mod():
    """Binary Workbench (dulu rea_binary.py)."""
    return _BN_API



# ===================================================================================================
# GAMELAB (digabung dari gamelab.py): pak (UnrealPak) | re (ELF/Mach-O ARM) | unity (UnityFS/SerializedFile)
# Dependensi opsional dimuat lazy hanya saat grupnya dipakai: lief+capstone (re), lz4/pillow/texture2ddecoder/UnityPy (unity).
# ===================================================================================================
import argparse
import bisect
import collections
import json
import lzma
import math
import os
import re
import struct
import subprocess
import sys
import uuid
import base64

try:
    import lz4.block as lz4block
except ImportError:
    lz4block = None

lief = None   # dimuat lazy oleh _init_re()
cs = None


def _init_re():
    global lief, cs
    try:
        import lief as _lief
    except ImportError:
        sys.exit("Grup 're' butuh LIEF: pip install lief")
    lief = _lief
    try:
        import capstone as _cs
        cs = _cs
    except ImportError:
        cs = None
    try:
        lief.logging.set_level(lief.logging.LEVEL.ERROR)
    except Exception:
        pass


RE_DOC = '\nre_lab.py - RE Lab untuk ELF dan Mach-O (ARM / ARM64 / Thumb)\n\nDependensi:  pip install lief capstone\n\nSubcommand:\n  triage   ringkasan cepat: format, arsitektur, proteksi, lib, indikator anti-debug/hook\n  sections daftar section/segment + entropi (deteksi packed/encrypted)\n  symbols  daftar simbol (filter --grep, --imports, --exports)\n  strings  string ASCII/UTF-16LE + alamat virtual\n  funcs    penemuan fungsi (simbol + heuristik prolog untuk binary stripped)\n  disasm   disassemble per alamat / simbol (ARM, Thumb, ARM64)\n  xrefs    cross-reference BL/B ke alamat/simbol, dan ref string via ADRP+ADD (ARM64)\n  objc     (Mach-O) class/selector Objective-C dari section __objc_*\n  jni      (ELF) fungsi JNI: JNI_OnLoad dan Java_* + RegisterNatives\n  carve    dump byte dari range alamat virtual ke file\n\nContoh:\n  python re_lab.py triage libgame.so\n  python re_lab.py disasm libgame.so --sym Java_com_x_Native_init --count 40\n  python re_lab.py xrefs  libgame.so --str "license"\n  python re_lab.py funcs  GameApp --slice 0 --limit 50\n'
UNITY_DOC = '\nunity_parser.py - Parser UnityFS bundle + SerializedFile (mandiri, berbasis TypeTree)\n\nDependensi : pip install lz4\nOpsional   : pip install pillow texture2ddecoder   (ekspor PNG + dekode DXT/BC/ETC/ASTC/PVRTC)\n             pip install UnityPy                    (fallback TypeTree untuk file yang TypeTree-nya di-strip)\n\nFitur\n  - Bundle UnityFS (LZ4 / LZ4HC / LZMA / tanpa kompresi), blocks-info di awal atau di akhir\n  - SerializedFile v13-v22+ (header, TypeTree blob, object table, externals, ref types)\n  - Pembaca TypeTree generik -> dict Python (semua class yang TypeTree-nya ada)\n  - Ekstraktor: Texture2D -> PNG, Mesh -> OBJ, AnimationClip -> JSON, TextAsset -> file mentah\n  - Resource eksternal (.resS / StreamingInfo) di dalam bundle maupun sebelah file .assets\n\nPerintah\n  info     FILE                     ringkasan bundle / serialized file\n  ls       FILE [--type T]          daftar object (path_id, class, nama, ukuran)\n  dump     FILE --id PATH_ID        dump TypeTree object sebagai JSON\n  extract  FILE -o DIR [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX]\n  unpack   FILE -o DIR              tulis semua node bundle hasil dekompresi\n\nBatasan (jujur)\n  - Bundle terenkripsi/custom (UnityCN, header dimodifikasi) tidak didukung.\n  - Build rilis sering membuang TypeTree; pakai --fallback (butuh UnityPy) atau\n    cocokkan dengan TypeTree dari tooling lain.\n  - Mesh terkompresi (m_MeshCompression != 0) dan tekstur swizzle konsol belum didukung.\n  - Animasi mecanim di-dump sebagai keyframe mentah + binding (bukan retarget penuh).\n'
PAK_DOC = '\npakbuild.py - Pembuat pak Unreal (Oodle/Zstd + enkripsi AES-256) lewat UnrealPak\n\nSubcommand:\n  gen-key   buat key AES-256 + GUID -> Crypto.json dan Crypto.json.ini.snippet\n  filelist  buat filelist.txt dari folder Saved/Cooked/<Platform>/<Project>\n  build     jalankan UnrealPak: kompres + enkripsi\n  list      daftar isi pak (butuh Crypto.json bila terenkripsi)\n\nContoh:\n  python pakbuild.py gen-key --out Crypto.json\n  python pakbuild.py filelist --cooked D:/P/Saved/Cooked/Windows/MyGame --project MyGame\n  python pakbuild.py build --unrealpak "C:/UE_5.4/Engine/Binaries/Win64/UnrealPak.exe" \\\n        --out MyDLC.pak --format Oodle --keys Crypto.json\n'



# =========================================================================== #
# GRUP: pak (Unreal pak builder)
# =========================================================================== #

CPP_H = r'''#pragma once
#include "CoreMinimal.h"

class FPakKeyLoader
{
public:
    // Daftarkan key AES (base64) lalu mount pak. Mengembalikan true jika berhasil.
    static bool RegisterKeyAndMount(const FGuid& KeyGuid, const FString& Base64Key,
                                    const FString& PakPath, int32 PakOrder = 100);
};
'''

CPP_CPP = r'''#include "PakKeyLoader.h"
#include "Misc/CoreDelegates.h"
#include "Misc/AES.h"
#include "Misc/Base64.h"

bool FPakKeyLoader::RegisterKeyAndMount(const FGuid& KeyGuid, const FString& Base64Key,
                                        const FString& PakPath, int32 PakOrder)
{
    TArray<uint8> KeyBytes;
    if (!FBase64::Decode(Base64Key, KeyBytes) || KeyBytes.Num() != 32)
    {
        UE_LOG(LogTemp, Error, TEXT("Key AES tidak valid (harus 32 byte)."));
        return false;
    }

    FAES::FAESKey Key;
    FMemory::Memcpy(Key.Key, KeyBytes.GetData(), 32);
    FCoreDelegates::GetRegisterEncryptionKeyMulticastDelegate().Broadcast(KeyGuid, Key);

    if (!FCoreDelegates::MountPak.IsBound())
    {
        UE_LOG(LogTemp, Error, TEXT("Delegate MountPak belum terikat."));
        return false;
    }
    return FCoreDelegates::MountPak.Execute(PakPath, PakOrder) != nullptr;
}
'''


def cmd_emitcpp(a):
    os.makedirs(a.out, exist_ok=True)
    for name, txt in (("PakKeyLoader.h", CPP_H), ("PakKeyLoader.cpp", CPP_CPP)):
        with open(os.path.join(a.out, name), "w", newline="\n") as f:
            f.write(txt)
        print(os.path.join(a.out, name))


def cmd_genkey(a):
    key = base64.b64encode(os.urandom(32)).decode()
    guid = str(uuid.uuid4()).upper()
    with open(a.out, "w") as f:
        json.dump({"EncryptionKey": {"Name": a.name, "Guid": guid, "Key": key}}, f, indent=2)
    ini = a.out + ".ini.snippet"
    with open(ini, "w") as f:
        f.write("[/Script/CryptoKeys.CryptoKeysSettings]\n"
                "bEnablePakIndexEncryption=True\nbEnablePakIniEncryption=True\n"
                "bEnablePakUAssetEncryption=True\nbEnablePakFullAssetEncryption=False\n"
                f"bDataCryptoRequired=True\nEncryptionKey={key}\n")
    print(f"Guid: {guid}\nKey tersimpan di {a.out} dan {ini}")
    print("JANGAN commit file key ke repo publik.")


def cmd_filelist(a):
    root = os.path.abspath(a.cooked)
    exts = tuple(e.strip().lower() for e in a.ext.split(",")) if a.ext else None
    n = 0
    with open(a.out, "w") as f:
        for dp, _, files in os.walk(root):
            for fn in sorted(files):
                if exts and not fn.lower().endswith(exts):
                    continue
                full = os.path.join(dp, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                f.write(f'"{full}" "../../../{a.project}/{rel}"\n')
                n += 1
    print(f"{n} file -> {a.out}")


def _exe(a):
    exe = a.unrealpak or os.environ.get("UNREALPAK")
    if not exe:
        sys.exit("Tentukan --unrealpak atau set env UNREALPAK")
    return exe


def _run(cmd):
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    sys.exit(subprocess.call(cmd))


def cmd_build(a):
    cmd = [_exe(a), a.out, f"-create={a.filelist}"]
    if a.format.lower() != "none":
        cmd += ["-compress", f"-compressionformats={a.format}"]
    if not a.no_encrypt:
        if not a.keys:
            sys.exit("Enkripsi butuh --keys Crypto.json (atau pakai --no-encrypt)")
        cmd += [f"-cryptokeys={a.keys}", "-encrypt", "-encryptindex"]
    _run(cmd)


def cmd_list(a):
    cmd = [_exe(a), a.pak, "-List"]
    if a.keys:
        cmd.append(f"-cryptokeys={a.keys}")
    _run(cmd)


def main_pak():
    p = argparse.ArgumentParser(description="Unreal pak builder",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=PAK_DOC)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("gen-key"); s.set_defaults(fn=cmd_genkey)
    s.add_argument("--out", default="Crypto.json"); s.add_argument("--name", default="MyKey")
    s = sp.add_parser("filelist"); s.set_defaults(fn=cmd_filelist)
    s.add_argument("--cooked", required=True); s.add_argument("--project", required=True)
    s.add_argument("--out", default="filelist.txt")
    s.add_argument("--ext", help="filter ekstensi, mis. .uasset,.uexp,.umap,.ubulk")
    s = sp.add_parser("build"); s.set_defaults(fn=cmd_build)
    s.add_argument("--unrealpak"); s.add_argument("--out", required=True)
    s.add_argument("--filelist", default="filelist.txt")
    s.add_argument("--format", default="Oodle", help="Oodle | Zstd | Zlib | LZ4 | none")
    s.add_argument("--keys"); s.add_argument("--no-encrypt", action="store_true")
    s = sp.add_parser("emit-cpp"); s.set_defaults(fn=cmd_emitcpp)
    s.add_argument("--out", default="UnrealLoader")
    s = sp.add_parser("list"); s.set_defaults(fn=cmd_list)
    s.add_argument("pak"); s.add_argument("--unrealpak"); s.add_argument("--keys")
    a = p.parse_args()
    a.fn(a)




# =========================================================================== #
# GRUP: re (ELF / Mach-O ARM)
# =========================================================================== #
# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #
class Target:
    def __init__(self, path, slice_idx=None):
        self.path = path
        with open(path, "rb") as f:
            self.raw = f.read()
        self.fmt = None
        self.bin = None
        self.arch = "other"
        self.thumb_default = False
        self._load(slice_idx)
        self._sym_cache = None

    def _load(self, slice_idx):
        if lief.is_elf(self.path):
            self.fmt = "elf"
            self.bin = lief.ELF.parse(self.path)
            m = str(self.bin.header.machine_type).upper()
            if "AARCH64" in m:
                self.arch = "arm64"
            elif "ARM" in m:
                self.arch = "arm"
        elif lief.is_macho(self.path):
            self.fmt = "macho"
            fat = lief.MachO.parse(self.path)
            bins = list(fat)
            if not bins:
                sys.exit("Mach-O kosong")
            self.slices = bins
            if slice_idx is None:
                slice_idx = 0
                for i, b in enumerate(bins):  # prefer arm64
                    if "ARM64" in str(b.header.cpu_type).upper():
                        slice_idx = i
                        break
            if len(bins) > 1:
                print(f"[i] Fat binary: {len(bins)} slice, pakai slice {slice_idx}",
                      file=sys.stderr)
            self.bin = bins[slice_idx]
            c = str(self.bin.header.cpu_type).upper()
            if "ARM64" in c:
                self.arch = "arm64"
            elif "ARM" in c:
                self.arch = "arm"
            # raw offset slice -> hanya untuk strings; fat offset ditangani LIEF
        else:
            sys.exit("Bukan ELF atau Mach-O")

    # ----- sections -----
    def sections(self):
        out = []
        for s in self.bin.sections:
            if self.fmt == "macho":
                name = f"{s.segment_name},{s.name}"
            else:
                name = s.name
            out.append((name, s.virtual_address, s.offset, s.size, s))
        return out

    def is_exec(self, name, sec):
        if self.fmt == "macho":
            return name.endswith(("__text", "__stubs", "__stub_helper", "__auth_stubs"))
        try:
            return lief.ELF.Section.FLAGS.EXECINSTR in sec.flags_list
        except Exception:
            return name in (".text", ".plt", ".init", ".fini")

    def sec_bytes(self, sec):
        return bytes(sec.content)

    # ----- memory -----
    def read_va(self, va, size):
        try:
            return bytes(self.bin.get_content_from_virtual_address(va, size))
        except Exception:
            return b""

    def va_of_offset(self, off):
        try:
            return self.bin.offset_to_virtual_address(off)
        except Exception:
            return None

    # ----- symbols -----
    def symbols(self):
        """list of dict(name, addr, size, thumb, func, imported, exported)"""
        if self._sym_cache is not None:
            return self._sym_cache
        seen, out = set(), []
        for s in self.bin.symbols:
            name = s.name
            val = s.value
            if not name:
                continue
            thumb = False
            func = True
            imported = exported = False
            if self.fmt == "elf":
                func = str(s.type).upper().endswith("FUNC")
                imported = bool(getattr(s, "imported", False))
                exported = bool(getattr(s, "exported", False))
                if self.arch == "arm" and (val & 1) and func:
                    thumb, val = True, val & ~1
            else:
                imported = val == 0
                exported = bool(getattr(s, "is_external", False)) and val != 0
            key = (name, val)
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(name=name, addr=val, size=getattr(s, "size", 0) or 0,
                            thumb=thumb, func=func, imported=imported, exported=exported))
        self._sym_cache = out
        return out

    def sym_index(self):
        syms = sorted((s for s in self.symbols() if s["addr"] and s["func"]),
                      key=lambda x: x["addr"])
        return syms, [s["addr"] for s in syms]

    def name_at(self, addr):
        syms, addrs = self.sym_index()
        i = bisect.bisect_right(addrs, addr) - 1
        if i >= 0:
            s = syms[i]
            d = addr - s["addr"]
            if d == 0:
                return s["name"]
            if (s["size"] and d < s["size"]) or (not s["size"] and d < 0x400):
                return f"{s['name']}+0x{d:x}"
        return None

    def resolve(self, ref):
        """ref bisa nama simbol atau alamat hex. Return (addr, thumb)"""
        try:
            return int(ref, 0) & ~1 if self.arch == "arm" else int(ref, 0), \
                (self.arch == "arm" and bool(int(ref, 0) & 1))
        except ValueError:
            pass
        for s in self.symbols():
            if s["name"] == ref and s["addr"]:
                return s["addr"], s["thumb"]
        sys.exit(f"Simbol tidak ditemukan: {ref}")

    # ----- capstone -----
    def md(self, thumb=False):
        if cs is None:
            sys.exit("Butuh capstone: pip install capstone")
        if self.arch == "arm64":
            md = cs.Cs(cs.CS_ARCH_ARM64, cs.CS_MODE_ARM)
        elif self.arch == "arm":
            md = cs.Cs(cs.CS_ARCH_ARM, cs.CS_MODE_THUMB if thumb else cs.CS_MODE_ARM)
        else:
            sys.exit(f"Arsitektur non-ARM tidak didukung untuk disasm "
                     f"({self.arch})")
        md.detail = False
        return md


# --------------------------------------------------------------------------- #
# Util
# --------------------------------------------------------------------------- #
def entropy(data):
    if not data:
        return 0.0
    c = collections.Counter(data)
    n = len(data)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def hexs(n):
    return f"0x{n:x}"


def extract_strings(data, minlen=5, utf16=False):
    if utf16:
        pat = re.compile(rb"(?:[\x20-\x7e]\x00){%d,}" % minlen)
    else:
        pat = re.compile(rb"[\x20-\x7e]{%d,}" % minlen)
    for m in pat.finditer(data):
        txt = m.group().decode("utf-16le" if utf16 else "ascii", "replace")
        yield m.start(), txt


def target_of(insn_text):
    m = re.search(r"#(0x[0-9a-fA-F]+)", insn_text)
    return int(m.group(1), 16) if m else None


def disasm_range(t, addr, size, thumb=False):
    data = t.read_va(addr, size)
    if not data:
        return []
    return list(t.md(thumb).disasm(data, addr))


def exec_sections(t):
    return [(n, va, off, sz, s) for n, va, off, sz, s in t.sections()
            if sz and t.is_exec(n, s)]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
SUSPICIOUS_IMPORTS = {
    "ptrace": "anti-debug", "fork": "anti-debug/child", "prctl": "anti-debug/seccomp",
    "dlopen": "dynamic load", "dlsym": "dynamic resolve", "mprotect": "memory patch",
    "mmap": "memory map", "syscall": "raw syscall", "inotify_add_watch": "file watch",
    "sysctl": "anti-debug (macOS/iOS)", "task_get_exception_ports": "anti-debug (iOS)",
    "dladdr": "hook check", "_dyld_image_count": "dylib enumeration (jailbreak/hook check)",
    "_dyld_get_image_name": "dylib enumeration", "SecTaskCopyValueForEntitlement": "entitlement check",
    "RegisterNatives": "JNI dynamic registration", "__system_property_get": "device check",
}
SUSPICIOUS_STRINGS = [
    "frida", "xposed", "substrate", "cydia", "magisk", "/proc/self/maps",
    "TracerPid", "/system/bin/su", "libhook", "gum-js", "re.frida", "Jailbreak",
    "/Applications/Cydia.app", "/usr/sbin/sshd", "DYLD_INSERT_LIBRARIES",
]


def cmd_triage(t, a):
    b = t.bin
    print(f"File      : {t.path}")
    print(f"Format    : {t.fmt.upper()}   Arch: {t.arch}")
    imports = {s["name"] for s in t.symbols() if s["imported"]}
    flags = []

    if t.fmt == "elf":
        h = b.header
        print(f"Type      : {h.file_type}   Entry: {hexs(h.entrypoint)}")
        print(f"PIE       : {getattr(b, 'is_pie', '?')}   NX: {getattr(b, 'has_nx', '?')}")
        print(f"Stripped  : {b.get_section('.symtab') is None}")
        print(f"Canary    : {'__stack_chk_fail' in imports}")
        try:
            print(f"Needed    : {', '.join(b.libraries)}")
        except Exception:
            pass
        try:
            print(f"Interp    : {b.interpreter}")
        except Exception:
            pass
        has_text_rel = any("TEXTREL" in str(e.tag) for e in b.dynamic_entries)
        if has_text_rel:
            flags.append("TEXTREL (relokasi di code segment)")
    else:
        h = b.header
        print(f"Filetype  : {h.file_type}   Flags: {[str(f).split('.')[-1] for f in h.flags_list]}")
        print(f"PIE       : {getattr(b, 'is_pie', '?')}   NX: {getattr(b, 'has_nx', '?')}")
        print(f"Dylibs    : {', '.join(d.name for d in b.libraries)}")
        print(f"CodeSign  : {b.has_code_signature}")
        if getattr(b, "has_encryption_info", False):
            ei = b.encryption_info
            state = "TERENKRIPSI (FairPlay) - butuh dump terdekripsi" if ei.crypt_id else "tidak terenkripsi"
            print(f"CryptID   : {ei.crypt_id} -> {state}")
            if ei.crypt_id:
                flags.append("Binary FairPlay-encrypted; analisis statis terbatas")
        print(f"Canary    : {'___stack_chk_fail' in imports}")

    # entropi
    print("\nEntropi section (>7.2 = kemungkinan packed/encrypted):")
    for n, va, off, sz, s in t.sections():
        if sz < 256:
            continue
        e = entropy(t.sec_bytes(s))
        mark = "  <-- tinggi" if e > 7.2 else ""
        print(f"  {n:<28} {hexs(va):>12} {sz:>10}  H={e:.2f}{mark}")
        if e > 7.2 and t.is_exec(n, s):
            flags.append(f"Section kode {n} berentropi tinggi (packed/encrypted?)")

    # import mencurigakan
    hits = [(i, SUSPICIOUS_IMPORTS[i.lstrip('_')] if i.lstrip('_') in SUSPICIOUS_IMPORTS
             else SUSPICIOUS_IMPORTS[i]) for i in imports
            if i in SUSPICIOUS_IMPORTS or i.lstrip("_") in SUSPICIOUS_IMPORTS]
    if hits:
        print("\nImport menarik:")
        for n, why in sorted(hits):
            print(f"  {n:<36} {why}")

    # string indikator
    found = collections.defaultdict(list)
    for off, s in extract_strings(t.raw, 4):
        for k in SUSPICIOUS_STRINGS:
            if k.lower() in s.lower():
                found[k].append(s)
    if found:
        print("\nString indikator deteksi root/jailbreak/hook:")
        for k, v in found.items():
            print(f"  {k:<28} x{len(v)}  contoh: {v[0][:60]!r}")

    if t.fmt == "elf":
        jni = [s["name"] for s in t.symbols() if s["name"].startswith("Java_") or s["name"] == "JNI_OnLoad"]
        if jni:
            print(f"\nJNI: {len(jni)} entri (jalankan: jni)")
    if t.fmt == "macho":
        print("\nTip: jalankan 'objc' untuk class/selector Objective-C.")
    if flags:
        print("\nCatatan:")
        for f in flags:
            print(f"  - {f}")


def cmd_sections(t, a):
    print(f"{'NAMA':<30}{'VA':>14}{'OFFSET':>12}{'SIZE':>12}  {'ENT':>5}  X")
    for n, va, off, sz, s in t.sections():
        e = entropy(t.sec_bytes(s)) if sz else 0
        print(f"{n:<30}{hexs(va):>14}{hexs(off):>12}{hexs(sz):>12}  {e:5.2f}  "
              f"{'x' if t.is_exec(n, s) else ''}")
    if t.fmt == "elf":
        print("\nSegments:")
        for sg in t.bin.segments:
            print(f"  {str(sg.type).split('.')[-1]:<14} va={hexs(sg.virtual_address):<12} "
                  f"off={hexs(sg.file_offset):<10} filesz={hexs(sg.physical_size):<10} "
                  f"memsz={hexs(sg.virtual_size):<10} flags={sg.flags}")
    else:
        print("\nSegments:")
        for sg in t.bin.segments:
            print(f"  {sg.name:<14} va={hexs(sg.virtual_address):<12} "
                  f"off={hexs(sg.file_offset):<10} size={hexs(sg.virtual_size)}")


def cmd_symbols(t, a):
    n = 0
    for s in sorted(t.symbols(), key=lambda x: x["addr"]):
        if a.imports and not s["imported"]:
            continue
        if a.exports and not s["exported"]:
            continue
        if a.grep and not re.search(a.grep, s["name"], re.I):
            continue
        tag = "I" if s["imported"] else ("E" if s["exported"] else " ")
        th = "T" if s["thumb"] else " "
        print(f"{hexs(s['addr']):>12} {s['size']:>6} {tag}{th} {s['name']}")
        n += 1
        if a.limit and n >= a.limit:
            break
    print(f"-- {n} simbol", file=sys.stderr)


def cmd_strings(t, a):
    n = 0
    for off, s in extract_strings(t.raw if t.fmt == "elf" else t.raw, a.min, a.utf16):
        if a.grep and not re.search(a.grep, s, re.I):
            continue
        va = t.va_of_offset(off)
        print(f"{hexs(va) if va is not None else '-':>12}  {hexs(off):>10}  {s}")
        n += 1
        if a.limit and n >= a.limit:
            break


def find_prologues(t, sec_name, va, data):
    """Heuristik fungsi pada binary stripped."""
    md = t.md(thumb=False)
    funcs = []
    if t.arch == "arm64":
        prev = None
        for i in md.disasm(data, va):
            op = i.op_str.replace(" ", "")
            if i.mnemonic == "stp" and op.startswith("x29,x30,[sp"):
                funcs.append(i.address)
            elif i.mnemonic == "sub" and op.startswith("sp,sp,#") and prev is None:
                pass
            elif i.mnemonic in ("paciasp", "bti"):
                funcs.append(i.address)
            prev = i
    else:  # ARM32: push {..., lr}
        for i in md.disasm(data, va):
            if i.mnemonic in ("push", "stmdb") and "lr" in i.op_str:
                funcs.append(i.address)
    return funcs


def cmd_funcs(t, a):
    known = {}
    for s in t.symbols():
        if s["func"] and s["addr"] and not s["imported"]:
            known[s["addr"]] = s["name"]
    print(f"[i] {len(known)} fungsi dari simbol", file=sys.stderr)
    guessed = {}
    if a.heuristic or not known:
        for n, va, off, sz, s in exec_sections(t):
            if n.endswith(("stubs", "plt")) or "stub" in n:
                continue
            for f in find_prologues(t, n, va, t.sec_bytes(s)):
                if f not in known:
                    guessed[f] = f"sub_{f:x}"
        print(f"[i] {len(guessed)} kandidat dari heuristik prolog", file=sys.stderr)
    allf = sorted({**known, **guessed}.items())
    for k, (addr, name) in enumerate(allf):
        if a.limit and k >= a.limit:
            break
        print(f"{hexs(addr):>12}  {name}")


def pretty_insn(t, i):
    line = f"{i.mnemonic:<8}{i.op_str}"
    tgt = target_of(f"{i.op_str}")
    if tgt is not None and i.mnemonic in ("bl", "blx", "b", "cbz", "cbnz", "tbz", "tbnz") \
            or (tgt is not None and i.mnemonic.startswith("b")):
        nm = t.name_at(tgt)
        if nm:
            line += f"    ; {nm}"
    return line


def cmd_disasm(t, a):
    if a.sym:
        addr, thumb = t.resolve(a.sym)
    else:
        addr, thumb = t.resolve(a.addr)
    if a.thumb:
        thumb = True
    size = a.size
    if not size:
        size = 4 * a.count
    insns = disasm_range(t, addr, size, thumb)
    if not insns:
        sys.exit("Gagal baca bytes pada alamat itu")
    nm = t.name_at(addr)
    if nm:
        print(f"{nm}:")
    for k, i in enumerate(insns):
        if a.count and not a.size and k >= a.count:
            break
        print(f"  {hexs(i.address):>10}:  {i.bytes.hex():<10}  {pretty_insn(t, i)}")


def build_xref_maps(t):
    """Return (calls: target->[caller], strrefs: addr->[site]) dari semua section exec."""
    calls = collections.defaultdict(list)
    strrefs = collections.defaultdict(list)
    for n, va, off, sz, s in exec_sections(t):
        data = t.sec_bytes(s)
        modes = [False] if t.arch == "arm64" else [False, True]
        for thumb in modes:
            md = t.md(thumb)
            pages = {}
            for i in md.disasm(data, va):
                ops = i.op_str
                tg = target_of(ops)
                if i.mnemonic in ("bl", "blx", "b") and tg is not None:
                    calls[tg].append(i.address)
                if t.arch == "arm64":
                    mm = re.match(r"(x\d+), #(0x[0-9a-f]+)$", ops)
                    if i.mnemonic == "adrp" and mm:
                        pages[mm.group(1)] = int(mm.group(2), 16)
                    elif i.mnemonic == "add":
                        mm = re.match(r"(x\d+), (x\d+), #(0x[0-9a-f]+)$", ops)
                        if mm and mm.group(2) in pages:
                            strrefs[pages[mm.group(2)] + int(mm.group(3), 16)].append(i.address)
                    elif i.mnemonic in ("ldr", "ldrb"):
                        mm = re.match(r"\w+, \[(x\d+), #(0x[0-9a-f]+)\]$", ops)
                        if mm and mm.group(1) in pages:
                            strrefs[pages[mm.group(1)] + int(mm.group(2), 16)].append(i.address)
    return calls, strrefs


def cmd_xrefs(t, a):
    calls, strrefs = build_xref_maps(t)
    if a.str:
        rx = re.compile(a.str, re.I)
        found = 0
        for off, s in extract_strings(t.raw, 4):
            if not rx.search(s):
                continue
            va = t.va_of_offset(off)
            if va is None:
                continue
            refs = strrefs.get(va, [])
            print(f"{hexs(va)}  {s[:80]!r}")
            for r in refs:
                print(f"      <- {hexs(r)}  {t.name_at(r) or ''}")
            found += 1
        if not found:
            print("Tidak ada string cocok")
        elif t.arch != "arm64":
            print("[!] Xref string (ADRP) hanya didukung ARM64", file=sys.stderr)
        return
    addr, _ = t.resolve(a.addr or a.sym)
    callers = calls.get(addr, [])
    print(f"Call/branch ke {hexs(addr)} ({t.name_at(addr) or '?'}): {len(callers)}")
    for c in sorted(callers):
        print(f"  {hexs(c):>10}  dari {t.name_at(c) or '?'}")


def cstr_list(sec):
    return [x.decode("utf-8", "replace") for x in bytes(sec.content).split(b"\x00") if x]


def cmd_objc(t, a):
    if t.fmt != "macho":
        sys.exit("Perintah objc khusus Mach-O")
    for label, name in (("Classes", "__objc_classname"), ("Selectors", "__objc_methname"),
                        ("Method types", "__objc_methtype")):
        sec = t.bin.get_section(name)
        if not sec:
            continue
        items = cstr_list(sec)
        if a.grep:
            items = [x for x in items if re.search(a.grep, x, re.I)]
        if label == "Method types" and not a.types:
            continue
        print(f"== {label} ({len(items)}) ==")
        for x in items[: a.limit or None]:
            print("  " + x)
    if hasattr(t.bin, "objc_metadata") or True:
        try:
            md = t.bin.objc_metadata
            if md:
                print("\n== objc_metadata (LIEF) ==")
                for c in md.classes:
                    print(f"  @interface {c.name}")
                    for m in c.methods:
                        print(f"     {'+' if m.is_static else '-'}[{m.name}]  imp={hexs(m.address)}")
        except Exception:
            pass


def cmd_jni(t, a):
    if t.fmt != "elf":
        sys.exit("Perintah jni khusus ELF")
    syms = [s for s in t.symbols() if s["name"].startswith("Java_") or s["name"] == "JNI_OnLoad"]
    print(f"== Entri JNI statis ({len(syms)}) ==")
    for s in sorted(syms, key=lambda x: x["addr"]):
        print(f"  {hexs(s['addr']):>10}  {s['name']}")
    imports = {s["name"] for s in t.symbols() if s["imported"]}
    print("\nRegisterNatives diimpor:", "RegisterNatives" in imports or "ya (via JNIEnv vtable, offset 0x6B8 pada arm64)")
    print("Petunjuk: pada JNI_OnLoad, cari 'ldr xN, [xM, #0x6b8]' (arm64) / '#0x35c' (arm32) "
          "lalu 'blr' = panggilan RegisterNatives; tabel JNINativeMethod = {name, sig, fnPtr}.")
    rx = re.compile(rb"\(([\[BCDFIJSZL][\w/;\[]*)\)[\[BCDFIJSVZL][\w/;]*")
    sigs = {m.group().decode() for m in rx.finditer(t.raw)}
    if sigs:
        print(f"\nKandidat signature JNI di binary: {len(sigs)}")
        for s in sorted(sigs)[:40]:
            print("  " + s)


def cmd_carve(t, a):
    addr, _ = t.resolve(a.addr)
    data = t.read_va(addr, a.size)
    if not data:
        sys.exit("Gagal baca")
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"{len(data)} byte dari {hexs(addr)} -> {a.out}")


# --------------------------------------------------------------------------- #
def main_re():
    p = argparse.ArgumentParser(description="RE Lab ELF/Mach-O ARM & ARM64",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=RE_DOC)
    p.add_argument("binary")
    p.add_argument("--slice", type=int, default=None, help="indeks slice untuk fat Mach-O")
    sp = p.add_subparsers(dest="cmd", required=True)

    sp.add_parser("triage").set_defaults(fn=cmd_triage)
    sp.add_parser("sections").set_defaults(fn=cmd_sections)

    s = sp.add_parser("symbols"); s.set_defaults(fn=cmd_symbols)
    s.add_argument("--grep"); s.add_argument("--imports", action="store_true")
    s.add_argument("--exports", action="store_true"); s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("strings"); s.set_defaults(fn=cmd_strings)
    s.add_argument("--min", type=int, default=5); s.add_argument("--grep")
    s.add_argument("--utf16", action="store_true"); s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("funcs"); s.set_defaults(fn=cmd_funcs)
    s.add_argument("--heuristic", action="store_true", help="tambah deteksi prolog")
    s.add_argument("--limit", type=int, default=0)

    s = sp.add_parser("disasm"); s.set_defaults(fn=cmd_disasm)
    s.add_argument("addr", nargs="?"); s.add_argument("--sym")
    s.add_argument("--count", type=int, default=32); s.add_argument("--size", type=lambda x: int(x, 0), default=0)
    s.add_argument("--thumb", action="store_true")

    s = sp.add_parser("xrefs"); s.set_defaults(fn=cmd_xrefs)
    s.add_argument("addr", nargs="?"); s.add_argument("--sym"); s.add_argument("--str")

    s = sp.add_parser("objc"); s.set_defaults(fn=cmd_objc)
    s.add_argument("--grep"); s.add_argument("--types", action="store_true")
    s.add_argument("--limit", type=int, default=0)

    sp.add_parser("jni").set_defaults(fn=cmd_jni)

    s = sp.add_parser("carve"); s.set_defaults(fn=cmd_carve)
    s.add_argument("addr"); s.add_argument("size", type=lambda x: int(x, 0)); s.add_argument("out")

    a = p.parse_args()
    _init_re()
    t = Target(a.binary, a.slice)
    if a.cmd == "disasm" and not (a.addr or a.sym):
        sys.exit("disasm butuh alamat atau --sym")
    if a.cmd == "xrefs" and not (a.addr or a.sym or a.str):
        sys.exit("xrefs butuh alamat, --sym, atau --str")
    a.fn(t, a)




# =========================================================================== #
# GRUP: unity (UnityFS / SerializedFile)
# =========================================================================== #
# --------------------------------------------------------------------------- #
# Konstanta
# --------------------------------------------------------------------------- #
_COMMON_LIST = (
    "AABB AnimationClip AnimationCurve AnimationState Array Base BitField bitset bool char ColorRGBA "
    "Component data deque double dynamic_array FastPropertyName first float Font GameObject "
    "Generic_Mono GradientNEW GUID GUIStyle int list long_long map Matrix4x4f MdFour MonoBehaviour "
    "MonoScript m_ByteSize m_Curve m_EditorClassIdentifier m_EditorHideFlags m_Enabled m_ExtensionPtr "
    "m_GameObject m_Index m_IsArray m_IsStatic m_MetaFlag m_Name m_ObjectHideFlags m_PrefabInternal "
    "m_PrefabParentObject m_Script m_StaticEditorFlags m_Type m_Version Object pair PPtr<Component> "
    "PPtr<GameObject> PPtr<Material> PPtr<MonoBehaviour> PPtr<MonoScript> PPtr<Object> PPtr<Prefab> "
    "PPtr<Sprite> PPtr<TextAsset> PPtr<Texture> PPtr<Texture2D> PPtr<Transform> Prefab Quaternionf "
    "Rectf RectInt RectOffset second set short size SInt16 SInt32 SInt64 SInt8 staticvector string "
    "TextAsset TextMesh Texture Texture2D Transform TypelessData UInt16 UInt32 UInt64 UInt8 "
    "unsigned_int unsigned_long_long unsigned_short vector Vector2f Vector3f Vector4f "
    "m_ScriptingClassIdentifier Gradient Type* int2_storage int3_storage BoundsInt "
    "m_CorrespondingSourceObject m_PrefabInstance m_PrefabAsset FileSize Hash128"
).split()
COMMON = {}
_gl_o = 0
for _s in _COMMON_LIST:
    _s = _s.replace("_", " ") if _s in ("Generic_Mono", "long_long", "unsigned_int",
                                        "unsigned_long_long", "unsigned_short") else _s
    COMMON[_gl_o] = _s
    _gl_o += len(_s) + 1

CLASS_IDS = {
    1: "GameObject", 4: "Transform", 20: "Camera", 21: "Material", 23: "MeshRenderer",
    28: "Texture2D", 33: "MeshFilter", 43: "Mesh", 48: "Shader", 49: "TextAsset",
    74: "AnimationClip", 82: "AudioSource", 83: "AudioClip", 90: "Avatar",
    91: "AnimatorController", 95: "Animator", 111: "Animation", 114: "MonoBehaviour",
    115: "MonoScript", 128: "Font", 137: "SkinnedMeshRenderer", 142: "AssetBundle",
    150: "PreloadData", 198: "ParticleSystem", 213: "Sprite", 224: "RectTransform",
    687078895: "SpriteAtlas",
}

PRIMS = {
    "SInt8": "b", "UInt8": "B", "char": "B", "bool": "?", "short": "h", "SInt16": "h",
    "UInt16": "H", "unsigned short": "H", "int": "i", "SInt32": "i", "UInt32": "I",
    "unsigned int": "I", "Type*": "I", "long long": "q", "SInt64": "q", "UInt64": "Q",
    "unsigned long long": "Q", "FileSize": "Q", "float": "f", "double": "d",
}


# --------------------------------------------------------------------------- #
# Reader biner
# --------------------------------------------------------------------------- #
class Reader:
    def __init__(self, data, endian=">", pos=0):
        self.d = data
        self.e = endian
        self.pos = pos

    def _u(self, fmt, n):
        v = struct.unpack_from(self.e + fmt, self.d, self.pos)[0]
        self.pos += n
        return v

    def u8(self): return self._u("B", 1)
    def i8(self): return self._u("b", 1)
    def u16(self): return self._u("H", 2)
    def i16(self): return self._u("h", 2)
    def u32(self): return self._u("I", 4)
    def i32(self): return self._u("i", 4)
    def u64(self): return self._u("Q", 8)
    def i64(self): return self._u("q", 8)
    def f32(self): return self._u("f", 4)

    def bytes(self, n):
        b = self.d[self.pos:self.pos + n]
        if len(b) != n:
            raise EOFError("data kurang")
        self.pos += n
        return b

    def cstr(self):
        end = self.d.index(b"\x00", self.pos)
        s = self.d[self.pos:end].decode("utf-8", "replace")
        self.pos = end + 1
        return s

    def align(self, n=4):
        self.pos += (-self.pos) % n


# --------------------------------------------------------------------------- #
# Dekompresi
# --------------------------------------------------------------------------- #
def lzma_unity(data, usize):
    props = data[0]
    dict_size = struct.unpack_from("<I", data, 1)[0]
    lc = props % 9
    props //= 9
    lp, pb = props % 5, props // 5
    flt = [{"id": lzma.FILTER_LZMA1, "dict_size": dict_size, "lc": lc, "lp": lp, "pb": pb}]
    return lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=flt).decompress(data[5:], max_length=usize)


def decompress(data, mode, usize):
    # v99.21: memakai _unity_decomp (Asset Explorer): batas ukuran, LZ4 murni Python tanpa paket lz4, tanpa sys.exit di dalam pustaka.
    return _unity_decomp(data, mode, usize)


# --------------------------------------------------------------------------- #
# UnityFS
# --------------------------------------------------------------------------- #
class Bundle:
    def __init__(self, data):
        r = Reader(data, ">")
        self.signature = r.cstr()
        if self.signature != "UnityFS":
            raise ValueError(f"Signature {self.signature!r} tidak didukung (hanya UnityFS)")
        self.version = r.u32()
        self.player_version = r.cstr()
        self.revision = r.cstr()
        self.size = r.i64()
        csize, usize, self.flags = r.u32(), r.u32(), r.u32()
        if self.version >= 7:
            r.align(16)
        if self.flags & 0x80:  # blocks info di akhir file
            save = r.pos
            r.pos = len(data) - csize
            raw = r.bytes(csize)
            r.pos = save
        else:
            raw = r.bytes(csize)
        if csize > 64 * 1024 * 1024 or usize > 64 * 1024 * 1024:
            raise ValueError("blok info UnityFS tidak wajar")
        info = decompress(raw, self.flags & 0x3F, usize)
        if self.flags & 0x200:
            r.align(16)

        ir = Reader(info, ">")
        ir.bytes(16)  # hash
        nb = ir.i32()
        if nb < 0 or nb > MAX_ENTRIES:
            raise ValueError("jumlah blok Unity tidak wajar")
        blocks = [(ir.u32(), ir.u32(), ir.u16()) for _ in range(nb)]
        nn = ir.i32()
        if nn < 0 or nn > MAX_ENTRIES:
            raise ValueError("jumlah node Unity tidak wajar")
        nodes = []
        for _ in range(nn):
            off, sz, fl = ir.i64(), ir.i64(), ir.u32()
            nodes.append((off, sz, fl, ir.cstr()))
        if sum(b[0] for b in blocks) > UNITY_MAX_BLOB:
            raise ValueError("isi bundle Unity terlalu besar untuk dibuka di memori (batas %d MB)" % (UNITY_MAX_BLOB >> 20))

        out = bytearray()
        for u, c, fl in blocks:
            out += decompress(r.bytes(c), fl & 0x3F, u)
        self.blob = bytes(out)
        self.nodes = [dict(path=p, offset=o, size=s, flags=f) for o, s, f, p in nodes]

    def node_data(self, n):
        return self.blob[n["offset"]:n["offset"] + n["size"]]

    def find(self, basename):
        for n in self.nodes:
            if os.path.basename(n["path"]) == basename:
                return n
        return None


# --------------------------------------------------------------------------- #
# TypeTree
# --------------------------------------------------------------------------- #
class TNode:
    __slots__ = ("level", "type", "name", "is_array", "byte_size", "index", "meta", "ref_hash")


def parse_typetree_blob(r, version):
    count = r.i32()
    buf_size = r.i32()
    raw = []
    for _ in range(count):
        r.u16()  # node version
        level, flags = r.u8(), r.u8()
        t_off, n_off = r.u32(), r.u32()
        bsize, idx, meta = r.i32(), r.i32(), r.i32()
        ref = r.u64() if version >= 19 else 0
        raw.append((level, flags, t_off, n_off, bsize, idx, meta, ref))
    buf = r.bytes(buf_size)

    def gs(off):
        if off & 0x80000000:
            return COMMON.get(off & 0x7FFFFFFF, f"?{off & 0x7FFFFFFF}")
        end = buf.index(b"\x00", off)
        return buf[off:end].decode("utf-8", "replace")

    nodes = []
    for level, flags, t_off, n_off, bsize, idx, meta, ref in raw:
        n = TNode()
        n.level, n.is_array = level, bool(flags & 1)
        n.type, n.name = gs(t_off), gs(n_off)
        n.byte_size, n.index, n.meta, n.ref_hash = bsize, idx, meta, ref
        nodes.append(n)
    ends = [len(nodes)] * len(nodes)
    for i, n in enumerate(nodes):
        j = i + 1
        while j < len(nodes) and nodes[j].level > n.level:
            j += 1
        ends[i] = j
    return nodes, ends


def read_value(r, nodes, ends, i):
    """Baca satu node TypeTree (rekursif) menjadi nilai Python."""
    n = nodes[i]
    t = n.type
    e = r.e
    fmt = PRIMS.get(t)
    if fmt:
        sz = struct.calcsize(fmt)
        v = struct.unpack_from(e + fmt, r.d, r.pos)[0]
        r.pos += sz
    elif t == "string":
        ln = r.i32()
        v = r.bytes(ln).decode("utf-8", "surrogateescape")
    elif t == "TypelessData":
        ln = r.i32()
        v = r.bytes(ln)
    elif n.is_array and t == "Array":
        size = r.i32()
        if size < 0 or size > len(r.d):
            raise ValueError("ukuran array TypeTree tidak wajar")
        di = i + 2
        dn = nodes[di]
        pf = PRIMS.get(dn.type)
        if dn.type in ("UInt8", "char", "SInt8") and not (dn.meta & 0x4000):
            v = r.bytes(size)
        elif pf and not (dn.meta & 0x4000):
            sz = struct.calcsize(pf)
            v = list(struct.unpack_from(f"{e}{size}{pf}", r.d, r.pos))
            r.pos += sz * size
        else:
            v = [read_value(r, nodes, ends, di) for _ in range(size)]
    else:
        v = {}
        j = i + 1
        end = ends[i]
        kids = []
        while j < end:
            kids.append(j)
            j = ends[j]
        for k in kids:
            v[nodes[k].name] = read_value(r, nodes, ends, k)
        if len(kids) == 1 and nodes[kids[0]].type == "Array":
            v = v[nodes[kids[0]].name]
    if n.meta & 0x4000:
        r.align(4)
    return v


# --------------------------------------------------------------------------- #
# SerializedFile
# --------------------------------------------------------------------------- #
class TypeInfo:
    pass


class ObjInfo:
    def __init__(self):
        self.path_id = self.byte_start = self.byte_size = self.type_id = self.class_id = 0
        self.type = None


class SerializedFile:
    def __init__(self, data, name="", container=None):
        self.data, self.name, self.container = data, name, container
        r = Reader(data, ">")
        meta_size, file_size, self.version, data_offset = r.u32(), r.u32(), r.u32(), r.u32()
        self.endian = ">"
        if self.version >= 9:
            self.endian = ">" if r.u8() else "<"
            r.bytes(3)
        else:
            raise ValueError("SerializedFile < v9 tidak didukung")
        if self.version >= 22:
            meta_size, file_size, data_offset = r.u32(), r.i64(), r.i64()
            r.i64()
        self.data_offset = data_offset
        r.e = self.endian
        self.unity_version = r.cstr() if self.version >= 7 else ""
        self.platform = r.i32() if self.version >= 8 else 0
        self.has_typetree = bool(r.u8()) if self.version >= 13 else True
        if self.version < 13:
            raise ValueError("SerializedFile < v13 tidak didukung")

        self.types = [self._read_type(r, False) for _ in range(r.i32())]

        big_id = self.version >= 14
        self.objects = {}
        for _ in range(r.i32()):
            o = ObjInfo()
            if big_id:
                r.align(4)
                o.path_id = r.i64()
            else:
                o.path_id = r.i32()
            o.byte_start = r.i64() if self.version >= 22 else r.u32()
            o.byte_size = r.u32()
            o.type_id = r.i32()
            if self.version < 16:
                o.class_id = r.u16()
                o.type = next((t for t in self.types if t.class_id == o.type_id), None)
            else:
                o.type = self.types[o.type_id]
                o.class_id = o.type.class_id
            if self.version < 11:
                r.u16()
            if 11 <= self.version < 17:
                r.i16()
            if 15 <= self.version < 17:
                r.u8()
            self.objects[o.path_id] = o

        if self.version >= 11:
            for _ in range(r.i32()):
                r.i32()
                if self.version < 14:
                    r.i32()
                else:
                    r.align(4)
                    r.i64()
        self.externals = []
        for _ in range(r.i32()):
            if self.version >= 6:
                r.cstr()
            if self.version >= 5:
                r.bytes(16)
            r.i32()
            self.externals.append(r.cstr())
        if self.version >= 20:
            self.ref_types = [self._read_type(r, True) for _ in range(r.i32())]

    def _read_type(self, r, is_ref):
        t = TypeInfo()
        t.class_id = r.i32()
        if self.version >= 16:
            r.u8()  # stripped
        script_idx = r.i16() if self.version >= 17 else -1
        t.nodes = t.ends = None
        if self.version >= 13:
            if (is_ref and script_idx >= 0) or (self.version < 16 and t.class_id < 0) or \
                    (self.version >= 16 and t.class_id == 114):
                r.bytes(16)
            r.bytes(16)
        if self.has_typetree:
            if self.version < 12 and self.version != 10:
                raise ValueError("TypeTree legacy tidak didukung")
            t.nodes, t.ends = parse_typetree_blob(r, self.version)
            if self.version >= 21:
                if is_ref:
                    r.cstr(); r.cstr(); r.cstr()
                else:
                    for _ in range(r.i32()):
                        r.i32()
        return t

    # ---- akses object ----
    def class_name(self, o):
        if o.type and o.type.nodes:
            return o.type.nodes[0].type
        return CLASS_IDS.get(o.class_id, f"Class{o.class_id}")

    def read(self, o):
        """Baca object -> dict. Fallback ke UnityPy jika TypeTree tidak ada."""
        if o.type and o.type.nodes:
            r = Reader(self.data, self.endian, self.data_offset + o.byte_start)
            return read_value(r, o.type.nodes, o.type.ends, 0)
        if self.container and self.container.fallback:
            d = self.container.unitypy_tree(self, o)
            if d is not None:
                return d
        raise RuntimeError(f"TypeTree tidak ada untuk {self.class_name(o)} (path_id={o.path_id}); "
                           f"coba --fallback (butuh UnityPy)")

    def peek_name(self, o):
        if not (o.type and o.type.nodes):
            return ""
        try:
            nodes, ends = o.type.nodes, o.type.ends
            r = Reader(self.data, self.endian, self.data_offset + o.byte_start)
            j, end = 1, ends[0]
            while j < end:
                if nodes[j].name == "m_Name":
                    return read_value(r, nodes, ends, j)
                read_value(r, nodes, ends, j)
                j = ends[j]
        except Exception:
            pass
        return ""


# --------------------------------------------------------------------------- #
# Container: bundle atau file serialized tunggal
# --------------------------------------------------------------------------- #
class Container:
    def __init__(self, path, fallback=False):
        self.path = path
        self.fallback = fallback
        self._up = None
        with open(path, "rb") as f:
            data = f.read()
        self.bundle = None
        self.files = []
        if data[:7] == b"UnityFS":
            self.bundle = Bundle(data)
            for n in self.bundle.nodes:
                if n["flags"] & 4:
                    sf = SerializedFile(self.bundle.node_data(n), os.path.basename(n["path"]), self)
                    self.files.append(sf)
        elif data[:5] in (b"Unity", b"Unity") and data[:8] != b"UnityFS\x00":
            raise ValueError("Format UnityWeb/UnityRaw/UnityArchive tidak didukung")
        else:
            self.files.append(SerializedFile(data, os.path.basename(path), self))

    def resource(self, stream_path, offset, size):
        base = os.path.basename(stream_path)
        if self.bundle:
            n = self.bundle.find(base)
            if n:
                return self.bundle.node_data(n)[offset:offset + size]
        p = os.path.join(os.path.dirname(os.path.abspath(self.path)), base)
        if os.path.exists(p):
            with open(p, "rb") as f:
                f.seek(offset)
                return f.read(size)
        raise FileNotFoundError(f"Resource {stream_path} tidak ditemukan")

    def unitypy_tree(self, sf, o):
        try:
            import UnityPy
        except ImportError:
            return None
        if self._up is None:
            self._up = UnityPy.load(self.path)
        for ob in self._up.objects:
            if ob.path_id == o.path_id and getattr(ob.assets_file, "name", "") in (sf.name, ""):
                try:
                    return ob.read_typetree()
                except Exception:
                    return None
        return None

    def all_objects(self):
        for sf in self.files:
            for o in sf.objects.values():
                yield sf, o


def to_bytes(x):
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, list):
        return bytes(x)
    return b""


def safe_name(s, fallback):
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", s or "").strip()
    return s or fallback


# --------------------------------------------------------------------------- #
# Texture2D
# --------------------------------------------------------------------------- #
ASTC = {48: (4, 4), 49: (5, 5), 50: (6, 6), 51: (8, 8), 52: (10, 10), 53: (12, 12),
        54: (4, 4), 55: (5, 5), 56: (6, 6), 57: (8, 8), 58: (10, 10), 59: (12, 12)}
TEX_BLOCK8 = {10: "bc1", 26: "bc4", 34: "etc1", 45: "etc2", 41: "eac_r", 42: "eac_r_signed"}
TEX_BLOCK16 = {12: "bc3", 27: "bc5", 25: "bc7", 24: "bc6h", 47: "etc2a8", 43: "eac_rg",
               44: "eac_rg_signed"}
TEX_UNCOMP = {1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 7: 2, 13: 2, 14: 4, 62: 2, 63: 1}


def decode_texture(d, container):
    w, h, fmt = d["m_Width"], d["m_Height"], d["m_TextureFormat"]
    img = to_bytes(d.get("image data"))
    sd = d.get("m_StreamData") or {}
    if not img and sd.get("size"):
        img = container.resource(sd["path"], sd["offset"], sd["size"])
    if not img:
        raise ValueError("data gambar kosong")
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Butuh Pillow: pip install pillow")

    if fmt in TEX_UNCOMP:
        img = img[:w * h * TEX_UNCOMP[fmt]]
        if fmt == 1 or fmt == 63:
            im = Image.frombytes("L", (w, h), img)
        elif fmt == 3:
            im = Image.frombytes("RGB", (w, h), img, "raw", "RGB")
        elif fmt == 4:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "RGBA")
        elif fmt == 5:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "ARGB")
        elif fmt == 14:
            im = Image.frombytes("RGBA", (w, h), img, "raw", "BGRA")
        elif fmt == 7:
            px = struct.unpack(f"<{w * h}H", img)
            out = bytearray()
            for p in px:
                out += bytes(((p >> 11) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31))
            im = Image.frombytes("RGB", (w, h), bytes(out))
        elif fmt in (2, 13):
            px = struct.unpack(f"<{w * h}H", img)
            out = bytearray()
            for p in px:
                n = [(p >> s) & 15 for s in (12, 8, 4, 0)]
                a, r_, g, b = n if fmt == 2 else (n[3], n[0], n[1], n[2])
                out += bytes((r_ * 17, g * 17, b * 17, a * 17))
            im = Image.frombytes("RGBA", (w, h), bytes(out))
        elif fmt == 62:
            im = Image.frombytes("LA", (w, h), img)
        return im.transpose(Image.FLIP_TOP_BOTTOM)

    try:
        import texture2ddecoder as t2d
    except ImportError:
        raise RuntimeError("Format terkompresi butuh: pip install texture2ddecoder")
    if fmt in (28, 29, 64, 65):
        if not hasattr(t2d, "unpack_crunch"):
            raise RuntimeError("Crunch tidak didukung versi texture2ddecoder ini")
        raw = t2d.unpack_crunch(img)
        fmt = {28: 10, 29: 12, 64: 34, 65: 47}[fmt]
        img = raw
    if fmt in TEX_BLOCK8:
        img = img[:((w + 3) // 4) * ((h + 3) // 4) * 8]
        bgra = getattr(t2d, "decode_" + TEX_BLOCK8[fmt])(img, w, h)
    elif fmt in TEX_BLOCK16:
        img = img[:((w + 3) // 4) * ((h + 3) // 4) * 16]
        bgra = getattr(t2d, "decode_" + TEX_BLOCK16[fmt])(img, w, h)
    elif fmt in ASTC:
        bw, bh = ASTC[fmt]
        img = img[:((w + bw - 1) // bw) * ((h + bh - 1) // bh) * 16]
        bgra = t2d.decode_astc(img, w, h, bw, bh)
    elif fmt in (30, 31, 32, 33):
        bgra = t2d.decode_pvrtc(img, w, h, fmt in (30, 31))
    else:
        raise RuntimeError(f"TextureFormat {fmt} belum didukung")
    im = Image.frombytes("RGBA", (w, h), bytes(bgra), "raw", "BGRA")
    return im.transpose(Image.FLIP_TOP_BOTTOM)


# --------------------------------------------------------------------------- #
# Mesh
# --------------------------------------------------------------------------- #
# format channel (Unity 2019+): (ukuran, kode struct, pembagi normalisasi)
FMT_NEW = {0: (4, "f", 0), 1: (2, "e", 0), 2: (1, "B", 255.0), 3: (1, "b", 127.0),
           4: (2, "H", 65535.0), 5: (2, "h", 32767.0), 6: (1, "B", 0), 7: (1, "b", 0),
           8: (2, "H", 0), 9: (2, "h", 0), 10: (4, "I", 0), 11: (4, "i", 0)}
FMT_OLD = {0: (4, "f", 0), 1: (2, "e", 0), 2: (1, "B", 255.0), 3: (1, "B", 0), 4: (4, "i", 0)}


def version_tuple(s):
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def decode_mesh(d, uver):
    if d.get("m_MeshCompression", 0):
        raise RuntimeError("Mesh terkompresi belum didukung")
    vd = d.get("m_VertexData")
    if not vd or "m_Channels" not in vd:
        raise RuntimeError("Layout mesh pra-2017 belum didukung")
    count = vd["m_VertexCount"]
    chans = vd["m_Channels"]
    vdata = to_bytes(vd.get("m_DataSize"))
    new = uver >= (2018, 0, 0)
    fmts = FMT_NEW if uver >= (2017, 4, 0) else FMT_OLD
    names = {0: "pos", 1: "normal", 2: "tangent", 3: "color", 4: "uv0", 5: "uv1", 6: "uv2", 7: "uv3",
             8: "uv4", 9: "uv5", 10: "uv6", 11: "uv7", 12: "weights", 13: "bones"} if new else \
        {0: "pos", 1: "normal", 2: "color", 3: "uv0", 4: "uv1", 5: "tangent"}

    # stride & offset tiap stream
    streams = {}
    for c in chans:
        dim = c["dimension"] & 0xF
        if dim:
            streams.setdefault(c["stream"], []).append((c, dim))
    stride, soff, off = {}, {}, 0
    for s in sorted(streams):
        stride[s] = sum(dim * fmts[c["format"]][0] for c, dim in streams[s])
        soff[s] = off
        off += stride[s] * count
        off += (-off) % 16

    out = {}
    for ci, c in enumerate(chans):
        dim = c["dimension"] & 0xF
        if not dim:
            continue
        size, code, norm = fmts[c["format"]]
        fmtstr = "<" + code * dim
        base = soff[c["stream"]] + c["offset"]
        st = stride[c["stream"]]
        rows = []
        for v in range(count):
            vals = struct.unpack_from(fmtstr, vdata, base + v * st)
            if norm:
                vals = tuple(max(x / norm, -1.0) for x in vals)
            rows.append(vals)
        out[names.get(ci, f"ch{ci}")] = rows

    ib = to_bytes(d.get("m_IndexBuffer"))
    use32 = d.get("m_IndexFormat", 0 if d.get("m_Use16BitIndices", 1) else 1) == 1
    isz = 4 if use32 else 2
    idx = struct.unpack(f"<{len(ib) // isz}{'I' if use32 else 'H'}", ib[:len(ib) // isz * isz])

    subs = []
    for sm in d.get("m_SubMeshes", []):
        first = sm["firstByte"] // isz
        seg = idx[first:first + sm["indexCount"]]
        base = sm.get("baseVertex", 0)
        topo = sm.get("topology", 0)
        tris = []
        if topo == 0:
            tris = [(seg[i] + base, seg[i + 1] + base, seg[i + 2] + base)
                    for i in range(0, len(seg) - 2, 3)]
        elif topo == 1:
            for i in range(len(seg) - 2):
                a, b, c = seg[i], seg[i + 1], seg[i + 2]
                if a == b or b == c or a == c:
                    continue
                tris.append((a + base, b + base, c + base) if i % 2 == 0 else (a + base, c + base, b + base))
        elif topo == 2:
            for i in range(0, len(seg) - 3, 4):
                a, b, c, e = (x + base for x in seg[i:i + 4])
                tris += [(a, b, c), (a, c, e)]
        subs.append(tris)
    return out, subs


def mesh_to_obj(name, attrs, subs, flip=True):
    L = [f"# exported by unity_parser.py", f"o {name}"]
    sx = -1.0 if flip else 1.0
    for p in attrs.get("pos", []):
        L.append(f"v {sx * p[0]:.6f} {p[1]:.6f} {p[2]:.6f}")
    for uv in attrs.get("uv0", []):
        L.append(f"vt {uv[0]:.6f} {uv[1]:.6f}")
    for n in attrs.get("normal", []):
        L.append(f"vn {sx * n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
    has_uv, has_n = "uv0" in attrs, "normal" in attrs
    for si, tris in enumerate(subs):
        L.append(f"g submesh_{si}")
        for a, b, c in tris:
            if flip:
                b, c = c, b
            def ref(i):
                i += 1
                if has_uv and has_n:
                    return f"{i}/{i}/{i}"
                if has_uv:
                    return f"{i}/{i}"
                if has_n:
                    return f"{i}//{i}"
                return str(i)
            L.append(f"f {ref(a)} {ref(b)} {ref(c)}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# AnimationClip
# --------------------------------------------------------------------------- #
ATTR_TRANSFORM = {1: "position", 2: "rotation", 3: "scale", 4: "euler"}


def curve_keys(c):
    return [[k.get("time"), k.get("value"), k.get("inSlope"), k.get("outSlope")]
            for k in (c.get("m_Curve") or [])]


def avatar_paths(container):
    m = {}
    for sf, o in container.all_objects():
        if sf.class_name(o) == "Avatar":
            try:
                for pair in sf.read(o).get("m_TOS", []):
                    m[pair["first"]] = pair["second"]
            except Exception:
                pass
    return m


def decode_animation(d, tos):
    res = {"name": d.get("m_Name"), "sample_rate": d.get("m_SampleRate"),
           "legacy": d.get("m_Legacy"), "wrap_mode": d.get("m_WrapMode")}
    legacy = {}
    for key in ("m_RotationCurves", "m_PositionCurves", "m_ScaleCurves", "m_EulerCurves"):
        if d.get(key):
            legacy[key[2:-6].lower()] = [{"path": c.get("path"), "keys": curve_keys(c.get("curve", {}))}
                                         for c in d[key]]
    if d.get("m_FloatCurves"):
        legacy["float"] = [{"path": c.get("path"), "attribute": c.get("attribute"),
                            "class_id": c.get("classID"), "keys": curve_keys(c.get("curve", {}))}
                           for c in d["m_FloatCurves"]]
    if legacy:
        res["legacy_curves"] = legacy

    mc = d.get("m_MuscleClip")
    if mc:
        clip = mc.get("m_Clip", {})
        res["stop_time"] = mc.get("m_StopTime")
        binds = (d.get("m_ClipBindingConstant") or clip.get("m_Binding") or {}).get("genericBindings", [])
        labels, last, comp = [], None, 0
        for b in binds:
            key = (b.get("path"), b.get("attribute"), b.get("typeID"))
            comp = comp + 1 if key == last else 0
            last = key
            path = tos.get(b.get("path"), f"#{b.get('path')}")
            if b.get("typeID") == 4:
                an = ATTR_TRANSFORM.get(b.get("attribute"), f"attr{b.get('attribute')}")
                labels.append(f"{path}:{an}.{'xyzw'[comp % 4]}")
            else:
                labels.append(f"{path}:type{b.get('typeID')}/attr{b.get('attribute')}#{comp}")
        res["bindings"] = labels

        sc = clip.get("m_StreamedClip", {})
        data = sc.get("data") or []
        streamed = []
        if data:
            buf = struct.pack(f"<{len(data)}I", *data)
            pos = 0
            while pos + 8 <= len(buf):
                t, n = struct.unpack_from("<fi", buf, pos)
                pos += 8
                if math.isinf(t) or n < 0 or pos + n * 20 > len(buf):
                    break
                for _ in range(n):
                    idx, c0, c1, c2, c3 = struct.unpack_from("<i4f", buf, pos)
                    pos += 20
                    streamed.append({"time": t, "curve": idx,
                                     "label": labels[idx] if 0 <= idx < len(labels) else None,
                                     "value": c3, "out_slope": c2})
        res["streamed_keys"] = streamed
        sc_count = sc.get("curveCount", 0)

        dc = clip.get("m_DenseClip", {})
        if dc.get("m_CurveCount"):
            arr, cc = dc.get("m_SampleArray", []), dc["m_CurveCount"]
            res["dense"] = {"frames": dc.get("m_FrameCount"), "sample_rate": dc.get("m_SampleRate"),
                            "begin_time": dc.get("m_BeginTime"),
                            "curves": [{"curve": sc_count + k,
                                        "label": labels[sc_count + k] if sc_count + k < len(labels) else None,
                                        "samples": arr[k::cc]} for k in range(cc)]}
        cst = clip.get("m_ConstantClip", {}).get("data", [])
        if cst:
            base = sc_count + dc.get("m_CurveCount", 0)
            res["constant"] = [{"curve": base + k,
                                "label": labels[base + k] if base + k < len(labels) else None,
                                "value": v} for k, v in enumerate(cst)]
    return res


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def jdump(x, **kw):
    def default(o):
        if isinstance(o, (bytes, bytearray)):
            return f"<bytes {len(o)}>"
        return str(o)
    return json.dumps(x, indent=2, default=default, **kw)


def cmd_info(c, a):
    if c.bundle:
        b = c.bundle
        print(f"UnityFS v{b.version}  player={b.player_version}  revision={b.revision}")
        print(f"flags=0x{b.flags:x} compression={b.flags & 0x3F}  decompressed={len(b.blob)} bytes")
        for n in b.nodes:
            print(f"  node {n['path']:<48} size={n['size']:>10} flags={n['flags']}")
    for sf in c.files:
        print(f"\nSerializedFile {sf.name}: v{sf.version} unity={sf.unity_version} "
              f"platform={sf.platform} typetree={sf.has_typetree} objects={len(sf.objects)}")
        counts = {}
        for o in sf.objects.values():
            k = sf.class_name(o)
            counts[k] = counts.get(k, 0) + 1
        for k, v in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {k:<24} {v}")
        if sf.externals:
            print("  externals:", ", ".join(sf.externals))


def cmd_ls(c, a):
    for sf, o in c.all_objects():
        cn = sf.class_name(o)
        if a.type and cn != a.type:
            continue
        print(f"{sf.name[:20]:<20} {o.path_id:>20} {cn:<20} {o.byte_size:>10}  {sf.peek_name(o)}")


def cmd_dump(c, a):
    for sf, o in c.all_objects():
        if o.path_id == a.id:
            print(jdump(sf.read(o)))
            return
    sys.exit("path_id tidak ditemukan")


def cmd_unpack(c, a):
    if not c.bundle:
        sys.exit("Bukan bundle")
    os.makedirs(a.out, exist_ok=True)
    for n in c.bundle.nodes:
        p = os.path.join(a.out, safe_name(os.path.basename(n["path"]), "node"))
        with open(p, "wb") as f:
            f.write(c.bundle.node_data(n))
        print(p)


def cmd_extract(c, a):
    want = {t.strip() for t in a.types.split(",")}
    rx = re.compile(a.name, re.I) if a.name else None
    os.makedirs(a.out, exist_ok=True)
    tos = None
    n_ok = n_fail = 0
    for sf, o in c.all_objects():
        cn = sf.class_name(o)
        if cn not in want:
            continue
        name = sf.peek_name(o)
        if rx and not rx.search(name or ""):
            continue
        base = f"{safe_name(name, cn)}_{o.path_id}"
        try:
            d = sf.read(o)
            name = d.get("m_Name") or name
            base = f"{safe_name(name, cn)}_{o.path_id}"
            if cn == "Texture2D":
                p = os.path.join(a.out, base + ".png")
                decode_texture(d, c).save(p)
            elif cn == "Mesh":
                attrs, subs = decode_mesh(d, version_tuple(sf.unity_version))
                p = os.path.join(a.out, base + ".obj")
                with open(p, "w") as f:
                    f.write(mesh_to_obj(name, attrs, subs, not a.no_flip))
            elif cn == "AnimationClip":
                if tos is None:
                    tos = avatar_paths(c)
                p = os.path.join(a.out, base + ".anim.json")
                with open(p, "w") as f:
                    f.write(jdump(decode_animation(d, tos)))
            elif cn == "TextAsset":
                p = os.path.join(a.out, base + ".bytes")
                with open(p, "wb") as f:
                    f.write(d.get("m_Script", "").encode("utf-8", "surrogateescape"))
            else:
                p = os.path.join(a.out, base + ".json")
                with open(p, "w") as f:
                    f.write(jdump(d))
            print(f"[ok]   {cn:<14} {p}")
            n_ok += 1
        except Exception as e:
            print(f"[gagal] {cn:<14} {base}: {e}", file=sys.stderr)
            n_fail += 1
    print(f"selesai: {n_ok} ok, {n_fail} gagal", file=sys.stderr)


def main_unity():
    p = argparse.ArgumentParser(description="Parser Unity bundle/SerializedFile",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=UNITY_DOC)
    p.add_argument("file")
    p.add_argument("--fallback", action="store_true", help="pakai UnityPy bila TypeTree tidak ada")
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("info").set_defaults(fn=cmd_info)
    s = sp.add_parser("ls"); s.set_defaults(fn=cmd_ls); s.add_argument("--type")
    s = sp.add_parser("dump"); s.set_defaults(fn=cmd_dump); s.add_argument("--id", type=int, required=True)
    s = sp.add_parser("unpack"); s.set_defaults(fn=cmd_unpack); s.add_argument("-o", "--out", required=True)
    s = sp.add_parser("extract"); s.set_defaults(fn=cmd_extract)
    s.add_argument("-o", "--out", required=True)
    s.add_argument("--types", default="Texture2D,Mesh,AnimationClip,TextAsset")
    s.add_argument("--name"); s.add_argument("--no-flip", action="store_true")
    a = p.parse_args()
    c = Container(a.file, a.fallback)
    a.fn(c, a)




# =========================================================================== #
# Dispatcher
# =========================================================================== #


# =========================================================================== #
# Dispatcher gamelab (dulu gamelab.py; kini bagian rea_triage.py)
# =========================================================================== #
_GL_GROUPS = {"pak": main_pak, "re": main_re, "unity": main_unity}
_GL_USAGE = '\nrea_triage.py --gamelab - toolkit game dalam SATU file\n\n  python rea_triage.py --gamelab pak   <subcommand> ...   Unreal pak: Oodle/Zstd + AES-256 (UnrealPak)\n  python rea_triage.py --gamelab re    <binary> <cmd> ... analisis ELF/Mach-O ARM/ARM64\n  python rea_triage.py --gamelab unity <file> <cmd> ...   parser UnityFS / SerializedFile\n\nBantuan per grup:\n  python rea_triage.py --gamelab pak -h\n  python rea_triage.py --gamelab re x.so triage -h\n  python rea_triage.py --gamelab unity bundle -h\n\nDependensi (dimuat hanya saat grupnya dipakai):\n  pak    : tidak ada (butuh UnrealPak.exe dari Unreal Engine)\n  re     : pip install lief capstone\n  unity  : pip install lz4   (opsional: pillow texture2ddecoder UnityPy)\n'


def gamelab_main(argv=None) -> int:
    """Pintu masuk gamelab: gamelab_main(["pak"|"re"|"unity", ...]). CLI: rea_triage.py --gamelab GRUP ..."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(_GL_USAGE)
        return 0
    grp = argv[0]
    if grp not in _GL_GROUPS:
        sys.exit("Grup tidak dikenal: %s. Pilih: %s" % (grp, ", ".join(_GL_GROUPS)))
    _old = sys.argv
    sys.argv = ["rea_triage.py --gamelab " + grp] + argv[1:]
    try:
        _GL_GROUPS[grp]()
    finally:
        sys.argv = _old
    return 0



# ===================================================================================================
# v99.21 [roadmap v2, Tier A: SerializedFile Unity]: parser gamelab dihubungkan ke Asset Explorer, rea_api dan CLI (--unity / --unity-extract).
# Aditif. Dependensi opsional: Pillow (PNG cepat), texture2ddecoder (BC6H/BC7/ETC/ASTC/PVRTC/Crunch). Tanpa keduanya: PNG murni Python untuk
# format tak terkompresi dan DXT1 / DXT5 / BC4 / BC5. Batas: UNITY_MAX_FILE, UNITY_MAX_BLOB, UNITY_MAX_OBJECTS, UNITY_TIME, MAX_PIXELS.
# ===================================================================================================
UNITY_MAX_FILE = 1024 ** 3            # berkas bundle / serialized yang boleh dibaca
UNITY_MAX_BLOB = 1024 ** 3            # total isi bundle setelah dekompresi (disimpan di memori)
UNITY_MAX_OBJECTS = 20000             # objek yang didekode per ekstraksi
UNITY_TIME = 120.0                    # detik, seluruh dekode objek
_UNITY_DEFAULT_TYPES = ("Texture2D", "Mesh", "AnimationClip", "TextAsset")


def _unity_open(path):
    p = str(path)
    if os.path.getsize(p) > UNITY_MAX_FILE:
        raise ValueError("berkas Unity terlalu besar (batas %d MB)" % (UNITY_MAX_FILE >> 20))
    return Container(p)


def _unity_tex_fallback(d, c):
    """Tekstur -> PNG tanpa Pillow: format tak terkompresi + DXT1 / DXT5 / BC4 / BC5 (lewat dekoder DDS milik Asset Explorer)."""
    w, h, fmt = int(d["m_Width"]), int(d["m_Height"]), int(d["m_TextureFormat"])
    if w <= 0 or h <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran tekstur tidak wajar (%dx%d)" % (w, h))
    img = to_bytes(d.get("image data"))
    sd = d.get("m_StreamData") or {}
    if not img and sd.get("size"):
        img = c.resource(sd["path"], sd["offset"], sd["size"])
    if not img:
        raise ValueError("data gambar kosong")
    px = bytearray(w * h * 4)
    if fmt in TEX_UNCOMP:
        bpp = TEX_UNCOMP[fmt]
        img = bytes(img[:w * h * bpp])
        if len(img) < w * h * bpp:
            raise ValueError("data tekstur terpotong")
        for i in range(w * h):
            q = img[i * bpp:(i + 1) * bpp]
            if fmt in (1, 63):
                r_ = g = b = q[0]; a = 255
            elif fmt == 3:
                r_, g, b = q; a = 255
            elif fmt == 4:
                r_, g, b, a = q
            elif fmt == 5:
                a, r_, g, b = q
            elif fmt == 14:
                b, g, r_, a = q
            elif fmt == 62:
                r_ = g = b = q[0]; a = q[1]
            elif fmt == 7:
                v = q[0] | (q[1] << 8)
                r_, g, b, a = (v >> 11) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31, 255
            else:   # 2 = ARGB4444, 13 = RGBA4444
                v = q[0] | (q[1] << 8)
                n = [(v >> s) & 15 for s in (12, 8, 4, 0)]
                a, r_, g, b = n if fmt == 2 else (n[3], n[0], n[1], n[2])
                r_, g, b, a = r_ * 17, g * 17, b * 17, a * 17
            px[i * 4:i * 4 + 4] = bytes((r_, g, b, a))
    elif fmt in (10, 12, 26, 27):
        fcc = {10: b"DXT1", 12: b"DXT5", 26: b"ATI1", 27: b"ATI2"}[fmt]
        hdr = bytearray(128)
        hdr[0:4] = b"DDS "
        struct.pack_into("<IIII", hdr, 4, 124, 0x1007, h, w)
        struct.pack_into("<II", hdr, 76, 32, 4)
        hdr[84:88] = fcc
        struct.pack_into("<I", hdr, 108, 0x1000)
        w2, h2, px = _dds_decode(bytes(hdr) + bytes(img))
    else:
        raise RuntimeError("TextureFormat %d butuh Pillow + texture2ddecoder (pip install pillow texture2ddecoder)" % fmt)
    stride = w * 4
    flipped = bytearray()
    for y in range(h - 1, -1, -1):   # Unity menyimpan baris dari bawah
        flipped += px[y * stride:(y + 1) * stride]
    return _png_encode(w, h, flipped)


def _unity_texture_png(d, c):
    """-> (bytes PNG, catatan). Pillow bila ada; format yang tidak terjangkau jatuh ke jalur murni Python."""
    w, h = int(d.get("m_Width", 0)), int(d.get("m_Height", 0))
    if w <= 0 or h <= 0 or w * h > MAX_PIXELS:
        raise ValueError("ukuran tekstur tidak wajar (%dx%d)" % (w, h))
    try:
        import io
        from PIL import Image  # noqa: F401
    except ImportError:
        return _unity_tex_fallback(d, c), "PNG murni Python"
    try:
        im = decode_texture(d, c)
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue(), "Pillow"
    except RuntimeError:
        return _unity_tex_fallback(d, c), "PNG murni Python"


def _unity_extract_objects(c, out, types, rx=None, t_budget=UNITY_TIME, flip=True, prefix="unity_objects"):
    """Dekode objek SerializedFile ke `out` (_Out): Texture2D -> .png, Mesh -> .obj, AnimationClip -> .anim.json, TextAsset -> .bytes, lainnya -> .json."""
    import time
    t0 = time.time()
    tos = None
    seen = 0
    done = collections.Counter()
    for sf, o in c.all_objects():
        if time.time() - t0 > t_budget:
            out.errors.append("dekode objek Unity dihentikan: melewati batas waktu %d dtk" % t_budget)
            break
        cn = sf.class_name(o)
        if cn not in types:
            continue
        if seen >= UNITY_MAX_OBJECTS:
            out.errors.append("dekode objek Unity dihentikan: melewati batas %d objek" % UNITY_MAX_OBJECTS)
            break
        name = sf.peek_name(o)
        if rx and not rx.search(name or ""):
            continue
        seen += 1
        base = "%s_%s" % (safe_name(name, cn), o.path_id)
        sub = "%s/%s/" % (prefix, cn)
        try:
            d = sf.read(o)
            name = d.get("m_Name") or name
            base = "%s_%s" % (safe_name(name, cn), o.path_id)
            if cn == "Texture2D":
                png, how = _unity_texture_png(d, c)
                out.write(sub + base + ".png", png, "unity-object", "Texture2D %sx%s format %s (%s)" % (d.get("m_Width"), d.get("m_Height"), d.get("m_TextureFormat"), how))
            elif cn == "Mesh":
                attrs, subs = decode_mesh(d, version_tuple(sf.unity_version))
                out.write_text(sub + base + ".obj", mesh_to_obj(name, attrs, subs, flip), "unity-object", "Mesh -> OBJ")
            elif cn == "AnimationClip":
                if tos is None:
                    tos = avatar_paths(c)
                out.write_text(sub + base + ".anim.json", jdump(decode_animation(d, tos)), "unity-object", "AnimationClip (keyframe mentah + binding)")
            elif cn == "TextAsset":
                out.write(sub + base + ".bytes", d.get("m_Script", "").encode("utf-8", "surrogateescape"), "unity-object", "TextAsset")
            else:
                out.write_text(sub + base + ".json", jdump(d), "unity-object", "%s (dump TypeTree)" % cn)
            done[cn] += 1
        except Exception as e:
            out.errors.append("Unity %s %s: %s" % (cn, _as_clean(base, 50), _as_clean(e, 110)))
    return dict(done)


def unity_info(path) -> dict:
    """Ringkasan bundle / SerializedFile Unity: versi, node, jumlah objek per kelas, TypeTree ada / dibuang. Tidak melempar."""
    try:
        c = _unity_open(path)
        r = {"ok": True, "path": str(path), "kind": "UnityFS" if c.bundle else "SerializedFile", "files": []}
        if c.bundle:
            b = c.bundle
            r["bundle"] = {"format_version": b.version, "player": b.player_version, "revision": b.revision, "compression": b.flags & 0x3F,
                           "size_decompressed": len(b.blob), "nodes": [{"path": n["path"], "size": n["size"], "serialized": bool(n["flags"] & 4)} for n in b.nodes[:500]]}
        for sf in c.files:
            cnt = collections.Counter(sf.class_name(o) for o in sf.objects.values())
            nt = sum(1 for o in sf.objects.values() if o.type and o.type.nodes)
            r["files"].append({"name": sf.name, "serialized_version": sf.version, "unity_version": sf.unity_version, "platform": sf.platform,
                               "objects": len(sf.objects), "classes": dict(cnt.most_common(40)), "typetree": bool(sf.has_typetree and nt),
                               "externals": sf.externals[:20]})
        return r
    except Exception as e:
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, _as_clean(e, 160))}


def unity_text(path, max_chars: int = 0) -> str:
    r = unity_info(path)
    if not r.get("ok"):
        return "UNITY gagal: %s" % r.get("error")
    L = ["UNITY %s: %s" % (r["kind"], os.path.basename(str(path)))]
    b = r.get("bundle")
    if b:
        L.append("  UnityFS v%s, player %s, revisi %s, kompresi %s, isi %s byte, %d node" % (b["format_version"], b["player"], b["revision"], b["compression"], b["size_decompressed"], len(b["nodes"])))
    for f in r["files"]:
        L.append("  SerializedFile %s: v%s unity %s, %d objek, TypeTree %s" % (f["name"], f["serialized_version"], f["unity_version"], f["objects"], "ada" if f["typetree"] else "TIDAK ADA (objek tidak bisa didekode; build rilis membuangnya)"))
        L.append("    kelas: " + ", ".join("%s x%d" % kv for kv in f["classes"].items()))
        if f["externals"]:
            L.append("    externals: " + ", ".join(f["externals"]))
    if not r["files"]:
        L.append("  tidak ada SerializedFile di dalamnya (node hanya data mentah / aliran .resS)")
    L.append("Ekstrak objek: --unity-extract OUTDIR FILE [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX]")
    t = "\n".join(L)
    return t if not max_chars or len(t) <= max_chars else t[:max_chars - 30] + "\n[...dipangkas...]"


def unity_extract(path, outdir, types=None, name=None, flip: bool = True) -> dict:
    """Dekode objek Unity ke outdir. Mengembalikan manifest {status, files, errors, ...}. Tidak melempar."""
    try:
        want = {t.strip() for t in (types.split(",") if isinstance(types, str) else (types or _UNITY_DEFAULT_TYPES)) if t.strip()}
        rx = re.compile(name, re.I) if name else None
        out = _Out(outdir)
        c = _unity_open(path)
        done = _unity_extract_objects(c, out, want, rx, flip=flip)
        ok = bool(out.files)
        man = {"status": ("partial" if out.errors or out.skipped else "success") if ok else "error", "format": "Unity", "source": str(path), "outdir": str(out.root),
               "entries_extracted": len(out.files), "entries_skipped": len(out.skipped), "entries_failed": len(out.errors), "by_class": done,
               "files": out.files, "skipped": out.skipped, "errors": out.errors}
        if not ok:
            man["message"] = "tidak ada objek yang berhasil didekode" + (": " + out.errors[0] if out.errors else " (TypeTree dibuang, atau tidak ada kelas yang diminta)")
        try:
            (out.root / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            man["manifest_path"] = str(out.root / "manifest.json")
        except OSError:
            pass
        return man
    except Exception as e:
        return {"status": "error", "message": "%s: %s" % (type(e).__name__, _as_clean(e, 160))}


def _unityfs_objects_note(p):
    """Baris ringkasan isi SerializedFile untuk Asset Explorer (tanpa melempar; dilewati untuk berkas besar)."""
    try:
        if os.path.getsize(str(p)) > 200 * 1024 * 1024:
            return ["Ringkasan objek dilewati (berkas besar): pakai `--unity FILE`."]
        c = _unity_open(p)
        L = []
        for sf in c.files:
            cnt = collections.Counter(sf.class_name(o) for o in sf.objects.values())
            has = any(o.type and o.type.nodes for o in sf.objects.values())
            L.append("SerializedFile %s (v%s, Unity %s): %d objek [%s]%s" % (_as_clean(sf.name, 40), sf.version, _as_clean(sf.unity_version, 20), len(sf.objects),
                                                                          ", ".join("%s x%d" % kv for kv in cnt.most_common(8)), "" if has else "; TypeTree dibuang, objek tidak bisa didekode"))
        if L:
            L.append("Ekstrak (tanpa pola): Texture2D -> .png, Mesh -> .obj, AnimationClip -> .anim.json, TextAsset -> .bytes di unity_objects/. Detail: `--unity FILE`.")
        return L
    except Exception as e:
        return ["Isi SerializedFile tidak bisa diurai: %s" % _as_clean(e, 100)]


def _unityfs_extract(d, p, out, opts):
    _arc_extract_factory(_unityfs)(d, p, out, opts)
    if opts.get("convert", True) and not opts.get("pattern"):   # pola hanya memfilter node; objek didekode bila pola kosong
        try:
            c = _unity_open(p)
            _unity_extract_objects(c, out, set(_UNITY_DEFAULT_TYPES))
        except Exception as e:
            out.errors.append("Unity objek: %s" % _as_clean(e, 120))



if __name__ == "__main__":   # uji manual: python rea_triage.py <file|folder> [--compact] [--json] [--ioc] [--raw] [--yara] [--carve DIR]
    argv = sys.argv[1:]
    cdir = None
    if "--no-cache" in argv:   # satu kali jalan tanpa cache (sama dengan env REA_CACHE=0)
        os.environ["REA_CACHE"] = "0"
        argv = [x for x in argv if x != "--no-cache"]
    if "--cache-info" in argv:
        print(cache_text())
        raise SystemExit(0)
    if "--cache-clear" in argv:
        print("cache dihapus: %d berkas" % cache_clear())
        raise SystemExit(0)
    if "--api" in argv:      # --api '{"action": "triage", "path": "x.exe"}'  (JSON satu baris untuk agen)
        t = argv[argv.index("--api") + 1:]
        print(json.dumps(rea_api(t[0] if t else "{}"), ensure_ascii=False, indent=2, default=str))
        raise SystemExit(0)
    if "--gamelab" in argv:  # --gamelab pak|re|unity ...  (toolkit game: UnrealPak, RE ELF/Mach-O ARM, Unity bundle)
        raise SystemExit(gamelab_main(argv[argv.index("--gamelab") + 1:]))
    if "--re" in argv:       # --re FILE [--compact]
        t = [x for x in argv[argv.index("--re") + 1:] if not x.startswith("--")]
        print(re_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --re FILE")
        raise SystemExit(0)
    if "--xref" in argv:     # --xref FILE QUERY
        t = argv[argv.index("--xref") + 1:]
        print(xref_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --xref FILE QUERY (nama API, potongan string, atau VA fungsi)")
        raise SystemExit(0)
    if "--yarascan" in argv:   # --yarascan FILE RULES
        t = argv[argv.index("--yarascan") + 1:]
        print(yara_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --yarascan FILE RULES(.yar atau folder)")
        raise SystemExit(0)
    if "--sigcheck" in argv:   # --sigcheck FILE [--online]  (v99.14: tanda tangan Authenticode penuh)
        t = [x for x in argv[argv.index("--sigcheck") + 1:] if not x.startswith("--")]
        print(sig_text(t[0], online="--online" in argv) if t else "pemakaian: --sigcheck FILE [--online]")
        raise SystemExit(0)
    if "--vt" in argv:       # --vt FILE|SHA256 --online  (v99.14: reputasi hash VirusTotal; env REA_VT_KEY)
        t = [x for x in argv[argv.index("--vt") + 1:] if not x.startswith("--")]
        print(reputation_text(t[0], online="--online" in argv) if t else "pemakaian: --vt FILE|SHA256 --online")
        raise SystemExit(0)
    if "--unpack7z" in argv:   # --unpack7z FILE OUTDIR  (v99.14: NSIS / SFX 7-Zip / 7z lewat alat 7-Zip)
        t = [x for x in argv[argv.index("--unpack7z") + 1:] if not x.startswith("--")]
        print(unpack_7z_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --unpack7z FILE OUTDIR")
        raise SystemExit(0)
    if "--unpack" in argv:   # --unpack FILE OUTDIR
        t = argv[argv.index("--unpack") + 1:]
        print(unpack_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --unpack FILE OUTDIR")
        raise SystemExit(0)
    if "--disasm" in argv:   # --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N]
        t = argv[argv.index("--disasm") + 1:]
        print(disasm_text(t[0], t[1] if len(t) > 1 else "entry", int(t[2], 0) if len(t) > 2 else 40, t[3] if len(t) > 3 else None) if t else "pemakaian: --disasm FILE [entry|0xVA|rva:0x..|off:0x..] [N] [ARCH]")
        raise SystemExit(0)
    if "--bin" in argv:      # --bin hex|inspect|search|compare|patch|undo|history|restore ...  (CLI Binary Workbench, dulu rea_binary.py)
        raise SystemExit(_bn_main(argv[argv.index("--bin") + 1:]))
    if "--ex" in argv:       # --ex list|extract|formats ...  (CLI mesin ekstraksi container, dulu rea_extract.py)
        raise SystemExit(_ex_main(argv[argv.index("--ex") + 1:]))
    if "--similar" in argv:  # --similar A B
        t = argv[argv.index("--similar") + 1:]
        print(similar_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --similar A B")
        raise SystemExit(0)
    if "--export" in argv:   # --export FILE ghidra|ida|x64dbg [OUT]  -> skrip anotasi (v99.15)
        t = [x for x in argv[argv.index("--export") + 1:] if not x.startswith("--")]
        print(export_text(t[0], t[1], t[2] if len(t) > 2 else None) if len(t) > 1 else "pemakaian: --export FILE ghidra|ida|x64dbg [OUT]")
        raise SystemExit(0)
    if "--funcdiff" in argv:   # --funcdiff A B  -> diff fungsi antar-dua biner (v99.15)
        t = [x for x in argv[argv.index("--funcdiff") + 1:] if not x.startswith("--")]
        print(func_diff_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --funcdiff A B")
        raise SystemExit(0)
    if "--cfg" in argv:      # --cfg FILE [entry|0xVA]  -> CFG / kompleksitas fungsi (v99.13)
        t = [x for x in argv[argv.index("--cfg") + 1:] if not x.startswith("--")]
        print(cfg_text(t[0], t[1] if len(t) > 1 else None) if t else "pemakaian: --cfg FILE [entry|0xVA]")
        raise SystemExit(0)
    if "--deobf" in argv:    # --deobf FILE [--json] [--raw] [--full]  -> deobfuscation skrip berlapis PowerShell / VBS / JS (v99.20)
        t = [x for x in argv[argv.index("--deobf") + 1:argv.index("--deobf") + 2] if not x.startswith("--")]
        if not t:
            print("pemakaian: --deobf FILE [--json] [--raw] [--full]")
        elif "--json" in argv:
            _f, _sz = _open_regular(t[0])
            with _f:
                _r = deobfuscate(_f.read(DSO_MAX_TEXT * 2))
            print(json.dumps(_r, ensure_ascii=False, indent=2))
        else:
            print(deobf_text(t[0], defang="--raw" not in argv, full="--full" in argv))
        raise SystemExit(0)
    if "--config" in argv:   # --config FILE [--key STR ...] [--json] [--raw]  -> konfigurasi malware tertanam (v99.19)
        i_ = argv.index("--config")
        t = [x for x in argv[i_ + 1:i_ + 2] if not x.startswith("--")]
        ks = [argv[j + 1] for j in range(len(argv) - 1) if argv[j] == "--key"]
        if not t:
            print("pemakaian: --config FILE [--key STR ...] [--json] [--raw]")
        elif "--json" in argv:
            print(json.dumps(extract_config(t[0], keys=ks, reveal="--raw" in argv), ensure_ascii=False, indent=2))
        else:
            print(config_text(t[0], defang="--raw" not in argv, keys=ks))
        raise SystemExit(0)
    if "--emu" in argv:      # --emu FILE [entry|0xVA]  -> emulasi mikro: string / buffer tersembunyi (v99.18)
        t = [x for x in argv[argv.index("--emu") + 1:] if not x.startswith("--")]
        print(emu_text(t[0], t[1] if len(t) > 1 else None, defang="--raw" not in argv) if t else "pemakaian: --emu FILE [entry|0xVA] [--raw]")
        raise SystemExit(0)
    if "--net" in argv:      # --net FILE [--compact] [--raw]  -> tabel metadata .NET + IL (v99.12)
        t = [x for x in argv[argv.index("--net") + 1:] if not x.startswith("--")]
        print(net_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --net FILE [--compact] [--raw]")
        raise SystemExit(0)
    if "--dex" in argv:      # --dex FILE [--compact] [--raw]  -> bytecode Dalvik .dex / APK (v99.11)
        t = [x for x in argv[argv.index("--dex") + 1:] if not x.startswith("--")]
        print(dex_text(t[0], defang="--raw" not in argv, compact="--compact" in argv) if t else "pemakaian: --dex FILE [--compact] [--raw]")
        raise SystemExit(0)
    if "--html" in argv:     # --html FILE [OUT.html]  -> laporan HTML tunggal offline (v99.7)
        t = argv[argv.index("--html") + 1:]
        print(triage_html_file(t[0], t[1] if len(t) > 1 else None, defang="--raw" not in argv) if t else "pemakaian: --html FILE [OUT.html]")
        raise SystemExit(0)
    if "--md" in argv:       # --md FILE  -> laporan Markdown
        t = argv[argv.index("--md") + 1:]
        print(triage_md(t[0]) if t else "pemakaian: --md FILE")
        raise SystemExit(0)
    if "--ctph" in argv:     # --ctph FILE
        t = argv[argv.index("--ctph") + 1:]
        print(ctph(_read_sample(t[0])[0]) if t else "pemakaian: --ctph FILE")
        raise SystemExit(0)
    if "--hex" in argv:      # --hex FILE [OFFSET [LENGTH]]
        t = argv[argv.index("--hex") + 1:]
        print(hex_text(t[0], int(t[1], 0) if len(t) > 1 else 0, int(t[2], 0) if len(t) > 2 else 256) if t else "pemakaian: --hex FILE [OFFSET [LENGTH]]")
        raise SystemExit(0)
    if "--compare" in argv:  # --compare A B
        t = argv[argv.index("--compare") + 1:]
        print(compare_text(t[0], t[1]) if len(t) > 1 else "pemakaian: --compare A B")
        raise SystemExit(0)
    if "--plugins" in argv:  # --plugins FOLDER (muat parser buatan sendiri; menjalankan kode di folder itu)
        _k = argv.index("--plugins")
        _m = _assets_mod()
        if _m is not None and _k + 1 < len(argv):
            print("plugin:", ", ".join(_m.load_plugins(argv[_k + 1])) or "(tidak ada)", file=sys.stderr)
        argv = argv[:_k] + argv[_k + 2:]
    if "--formats" in argv:   # daftar parser Asset Explorer
        _m = _assets_mod()
        for _f in (_m.formats() if _m else []):
            print("%-12s %-10s inspect=%s extract=%s%s  %s" % (_f["name"], _f["category"], "ya" if _f["inspect"] else "-", "ya" if _f["extract"] else "-", " [plugin]" if _f["plugin"] else "", _f["about"]))
        raise SystemExit(0)
    if "--unity" in argv:   # --unity FILE  -> ringkasan bundle / SerializedFile Unity (v99.21)
        t = [x for x in argv[argv.index("--unity") + 1:] if not x.startswith("--")]
        print(unity_text(t[0]) if t else "pemakaian: --unity FILE")
        raise SystemExit(0)
    if "--unity-extract" in argv:   # --unity-extract OUTDIR FILE [--types T1,T2] [--name REGEX] [--no-flip]
        k = argv.index("--unity-extract")
        rest = argv[k + 1:]
        opt = {}
        for key in ("--types", "--name"):
            if key in rest:
                j = rest.index(key)
                opt[key] = rest[j + 1] if j + 1 < len(rest) else None
                del rest[j:j + 2]
        flip_ = "--no-flip" not in rest
        t = [x for x in rest if not x.startswith("--")]
        if len(t) < 2:
            print("pemakaian: --unity-extract OUTDIR FILE [--types Texture2D,Mesh,AnimationClip,TextAsset] [--name REGEX] [--no-flip]")
            raise SystemExit(2)
        m = unity_extract(t[1], t[0], types=opt.get("--types"), name=opt.get("--name"), flip=flip_)
        print(json.dumps({k_: v for k_, v in m.items() if k_ not in ("files",)}, ensure_ascii=False, indent=1, default=str))
        raise SystemExit(0 if m.get("status") in ("success", "partial") else 1)
    if "--assets" in argv:   # --assets FILE
        t = [x for x in argv[argv.index("--assets") + 1:] if not x.startswith("--")]
        print(assets_text(t[0]) if t else "pemakaian: --assets FILE")
        raise SystemExit(0)
    if "--assets-extract" in argv:   # --assets-extract OUTDIR FILE [pola] [--no-convert]
        k = argv.index("--assets-extract")
        _out = argv[k + 1] if k + 1 < len(argv) else "rea_assets_out"
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        if not _rest:
            print("pemakaian: --assets-extract OUTDIR FILE [pola] [--no-convert]")
            raise SystemExit(1)
        _m = assets_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, convert="--no-convert" not in argv)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s konversi=%s | manifest: %s%s" % (_m.get("status"), _m.get("entries_extracted"), _m.get("entries_skipped"), _m.get("entries_failed"),
              _m.get("converted_items"), _m.get("manifest_path"), (" | " + _m["message"]) if _m.get("message") else ""))
        raise SystemExit(0 if _m.get("status") in ("success", "partial") else 1)
    if "--assets-carve" in argv:   # --assets-carve FILE [OUTDIR]
        t = [x for x in argv[argv.index("--assets-carve") + 1:] if not x.startswith("--")]
        _m = _assets_mod()
        if not t or _m is None:
            print("pemakaian: --assets-carve FILE [OUTDIR]")
        else:
            print(getattr(_m, "_carve_text", lambda r: json.dumps(r, ensure_ascii=False, indent=2, default=str))(assets_carve(t[0], t[1] if len(t) > 1 else None)))
        raise SystemExit(0)
    if "--list" in argv:
        print(container_text(next((x for x in argv if not x.startswith("--")), "")))
        raise SystemExit(0)
    if "--extract" in argv:
        k = argv.index("--extract")
        _out = argv[k + 1] if k + 1 < len(argv) else "rea_workspace"
        _rest = [x for i, x in enumerate(argv) if i not in (k, k + 1) and not x.startswith("--")]
        _m = container_extract(_rest[0], _out, pattern=_rest[1] if len(_rest) > 1 else None, scan="--scan" in argv)
        print("status=%s diekstrak=%s dilewati=%s gagal=%s | manifest: %s" % (_m.get("status"), _m.get("entries_extracted"), _m.get("entries_skipped"), _m.get("entries_failed"), _m.get("manifest_path")))
        raise SystemExit(0 if _m.get("status") == "success" else 1)
    if "--carve" in argv:
        k = argv.index("--carve")
        cdir = argv[k + 1] if k + 1 < len(argv) else None
        argv = argv[:k] + argv[k + 2:]
    args = [x for x in argv if not x.startswith("--")]
    flags = {x for x in argv if x.startswith("--")}
    if not args:
        print("pemakaian: python rea_triage.py <file|folder> [--compact] [--card] [--json] [--ioc] [--raw (tanpa defang)] [--yara] [--carve DIR] | --config FILE [--key STR] | --deobf FILE [--json] [--full] | --hex FILE [OFFSET [LENGTH]] | --compare A B | --list <container> | --extract OUTDIR <container> [pola] [--scan] | --similar A B | --md FILE | --html FILE [OUT.html] | --gamelab pak|re|unity ... | --dex FILE [--compact] | --net FILE [--compact] | --cfg FILE [entry|0xVA] | --emu FILE [entry|0xVA] | --export FILE ghidra|ida|x64dbg [OUT] | --funcdiff A B | --ctph FILE | --re FILE | --xref FILE QUERY | --disasm FILE [AT [N [ARCH]]] | --unpack FILE OUTDIR | --unpack7z FILE OUTDIR | --sigcheck FILE [--online] | --vt FILE|SHA256 --online | --yarascan FILE RULES | --unity FILE | --unity-extract OUTDIR FILE [--types T1,T2] [--name REGEX] | --assets FILE | --assets-extract OUTDIR FILE [pola] [--no-convert] | --assets-carve FILE [OUTDIR] | --formats | --plugins FOLDER | --bin CMD ... | --ex CMD ... | --api JSON | --no-cache | --cache-info | --cache-clear")
    elif Path(args[0]).is_dir():
        print(triage_dir_text(args[0], defang="--raw" not in flags))
    elif "--card" in flags and not ({"--json", "--ioc", "--yara"} & flags):
        print(triage_text(args[0], defang="--raw" not in flags, card=True))
    elif "--json" in flags or "--ioc" in flags:
        print(triage_json(args[0], ioc_only="--ioc" in flags))
    elif "--yara" in flags:
        print(yara_draft(triage(args[0])))
    else:
        full, _note = triage_bundle(args[0], carve_dir=cdir) if cdir else (None, None)
        print(full if full is not None else triage_text(args[0], compact="--compact" in flags, defang="--raw" not in flags))
