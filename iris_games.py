"""iris_games.py: game teka-teki (なぞなぞ) untuk Iris.

Modul ini hanya berisi logika permainan dan tidak tahu apa pun soal
WebSocket, bubble, atau VOICEVOX. server.py memanggil `GameTekaTeki.tangani(teks)`
lebih dulu; kalau hasilnya `None`, pesan diteruskan ke alur chat biasa.
Hanya memakai pustaka standar Python 3.11+. Penghubung LLM (bagian paling bawah,
`buat_pembuat` / `buat_pemeriksa`) memakai httpx, yang baru diimpor saat dipanggil.

Contoh di server.py:

    import iris_games as ig
    game = ig.GameTekaTeki(
        BASE / "data" / "tekateki.json", BASE / "data" / "tekateki_state.json",
        dinamis_path=BASE / "data" / "tekateki_dinamis.json",
        pembuat=ig.buat_pembuat(NINEROUTER_URL, NINEROUTER_KEY, GAME_MODEL),
        pemeriksa=ig.buat_pemeriksa(NINEROUTER_URL, NINEROUTER_KEY, GAME_MODEL),
    )

PENTING: `game.tangani(...)` itu sinkron dan menyentuh disk. Di handler async
panggil lewat `await asyncio.to_thread(game.tangani, teks)`.

Setiap `Balasan` membawa teks bubble, saran emosi, nama klip VRMA, dan teks
yang sebaiknya disuarakan. Penghubungnya (server.py) yang memetakan itu ke
overlay.
"""
from __future__ import annotations

import json
import os
import random
import re
import tempfile
import threading
import time
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional

POIN_DASAR = 3            # poin bila benar tanpa petunjuk
MAKS_PETUNJUK = 3         # petunjuk maksimal per teka-teki
RIWAYAT_MAKS = 30         # id teka-teki terakhir yang dihindari
KEDALUWARSA_DETIK = 600   # ronde dibatalkan bila diam selama ini
SALAH_SEBELUM_TAWAR = 3   # setelah sekian tebakan salah, Iris menawarkan petunjuk
DINAMIS_MAKS = 200        # teka-teki buatan LLM yang disimpan (yang lama dibuang)
ISI_ULANG_SISA = 2        # bila yang belum pernah muncul tinggal sekian, mulai membuat baru di latar
HINDARI_MAKS = 20         # pertanyaan terbaru yang dikirim ke LLM supaya tidak dibuat ulang
PERCOBAAN_BUAT = 2        # berapa kali LLM dicoba per permintaan sebelum menyerah

PERINTAH_UTAMA = {"/tekateki", "/riddle", "/nazonazo"}
PERINTAH_PINTAS = {
    "/petunjuk": "petunjuk", "/hint": "petunjuk", "/clue": "petunjuk",
    "/menyerah": "menyerah", "/nyerah": "menyerah", "/giveup": "menyerah",
    "/skip": "lewati",
}
# Kata biasa (tanpa garis miring) saat ronde berjalan. Tebakan yang benar selalu dicek lebih dulu.
_KATA_NYERAH = {"nyerah", "menyerah", "giveup", "nyerahh", "nyerahlah"}
_KATA_PETUNJUK = {"petunjuk", "hint", "clue", "bantuan", "petunjuknya"}
_KATA_LEWATI = {"skip", "lewati", "lewat"}

_SUB = {
    "petunjuk": "petunjuk", "hint": "petunjuk", "clue": "petunjuk",
    "menyerah": "menyerah", "nyerah": "menyerah", "giveup": "menyerah",
    "lewati": "lewati", "skip": "lewati",
    "stop": "stop", "selesai": "stop", "keluar": "stop",
    "skor": "skor", "statistik": "skor", "stat": "skor",
}
_MODE = {
    "": "campur", "campur": "campur", "acak": "campur",
    "id": "id", "indo": "id", "indonesia": "id",
    "ja": "ja", "jp": "ja", "jepang": "ja", "nihongo": "ja",
}

# Kata pengisi di awal/akhir tebakan yang diabaikan saat mencocokkan.
_FILLER = {
    "jawabannya", "jawaban", "mungkin", "itu", "adalah", "ya", "yaa",
    "kayaknya", "sepertinya", "deh", "kah",
}
_PUNCT = re.compile(r"[^\w\s\u30fc]", re.UNICODE)

# Suara: VOICEVOX hanya bisa bahasa Jepang, jadi reaksi berbahasa Indonesia disuarakan lewat kalimat Jepang pendek
# (teks bubble tetap Indonesia). Dipilih acak supaya tidak monoton.
_SUARA_JP = {
    "teka_id": ["なぞなぞだよ。わかるかな？", "なぞなぞいくよ。答えてみてね。"],
    "salah": ["うーん、ちがうよ。", "おしい、かな？もういっかい。", "ざんねん、ちがうなあ。", "ふふ、まだまだだね。"],
    "benar": ["せいかい！すごいね！", "あたり！やるじゃん。", "正解だよ！おめでとう。"],
    "petunjuk": ["ヒントをあげるね。", "しかたないなあ、ヒントだよ。"],
    "menyerah": ["ざんねん、こたえはこれだよ。", "あらら、ギブアップだね。"],
    "stop": ["うん、またあそぼうね。"],
    "skor": ["スコアだよ。がんばってるね。"],
}


def _jp(kunci: str) -> str:
    return random.choice(_SUARA_JP[kunci])


_KOMENTAR_SALAH = [
    "Hmm, bukan itu~",
    "Belum tepat, coba lagi!",
    "Dekat... atau mungkin jauh. Hehe.",
    "Bukan, tapi aku suka semangatmu.",
]


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------
@dataclass
class Balasan:
    teks: str                      # teks untuk bubble
    emosi: str = "netral"          # saran emosi; petakan ke tag emosi overlay
    klip: Optional[str] = None     # nama klip VRMA (angguk, geleng, tari_ceria, ...)
    ucapkan: Optional[str] = None  # teks untuk VOICEVOX; None = tidak disuarakan
    bahasa: str = "id"             # "id" atau "ja" (untuk label 日本語 dan pilihan suara)


@dataclass(frozen=True)
class Teka:
    id: str
    bahasa: str
    pertanyaan: str
    jawaban: tuple
    varian: tuple
    petunjuk: tuple
    penjelasan: str
    baca: str = ""       # bacaan untuk TTS (mis. kanji dijadikan hiragana)
    terjemah: str = ""   # terjemahan Indonesia untuk teka-teki Jepang

    @property
    def semua_jawaban(self) -> tuple:
        return self.jawaban + self.varian


@dataclass
class Ronde:
    teka: Teka
    mode: str = "campur"
    petunjuk_dipakai: int = 0
    salah: int = 0
    aktivitas: float = 0.0


# ----------------------------------------------------------------------
# Bank teka-teki
# ----------------------------------------------------------------------
def muat_bank(path) -> tuple[list[Teka], list[str]]:
    """Baca bank JSON. Entri rusak dilewati dan dicatat di daftar peringatan."""
    peringatan: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [], [f"Bank tidak bisa dibaca: {e}"]

    mentah = data.get("teka_teki") if isinstance(data, dict) else None
    if not isinstance(mentah, list):
        return [], ["Bank tidak punya daftar 'teka_teki'"]

    hasil: list[Teka] = []
    id_terpakai: set[str] = set()
    for i, e in enumerate(mentah):
        teka, masalah = _validasi(e, f"entri #{i + 1}", id_terpakai)
        if teka is None:
            peringatan.append(masalah)
            continue
        id_terpakai.add(teka.id)
        hasil.append(teka)
    return hasil, peringatan


def _validasi(e, label: str, id_terpakai: set) -> tuple[Optional[Teka], str]:
    """Ubah satu entri mentah jadi Teka. Mengembalikan (Teka, '') atau (None, alasan)."""
    if not isinstance(e, dict):
        return None, f"{label}: bukan objek"
    tid = e.get("id")
    label = f"{tid or label}"
    if not isinstance(tid, str) or not tid:
        return None, f"{label}: id kosong"
    if tid in id_terpakai:
        return None, f"{label}: id ganda"
    if e.get("bahasa") not in ("id", "ja"):
        return None, f"{label}: bahasa harus 'id' atau 'ja'"
    if not isinstance(e.get("pertanyaan"), str) or not e["pertanyaan"].strip():
        return None, f"{label}: pertanyaan kosong"
    jawaban = _daftar_str(e.get("jawaban"))
    if not jawaban:
        return None, f"{label}: jawaban kosong"
    return Teka(
        id=tid,
        bahasa=e["bahasa"],
        pertanyaan=e["pertanyaan"].strip(),
        jawaban=jawaban,
        varian=_daftar_str(e.get("varian")),
        petunjuk=_daftar_str(e.get("petunjuk")),
        penjelasan=str(e.get("penjelasan") or "").strip(),
        baca=str(e.get("baca") or "").strip(),
        terjemah=str(e.get("terjemah") or "").strip(),
    ), ""


def _daftar_str(v) -> tuple:
    if not isinstance(v, list):
        return ()
    return tuple(x.strip() for x in v if isinstance(x, str) and x.strip())


# ----------------------------------------------------------------------
# Pencocokan jawaban
# ----------------------------------------------------------------------
def _ke_hiragana(s: str) -> str:
    return "".join(
        chr(ord(c) - 0x60) if "\u30a1" <= c <= "\u30f6" else c for c in s
    )


def normalisasi(s: str) -> str:
    """Samakan bentuk teks: NFKC, huruf kecil, katakana jadi hiragana,
    tanda baca dan kata pengisi dibuang, spasi dihapus."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = _ke_hiragana(s)
    s = _PUNCT.sub(" ", s)
    kata = [k for k in s.split() if k not in _FILLER]
    return "".join(kata)


def _kata(s: str) -> list:
    """Pecah jadi kata-kata ternormalisasi (spasi dipertahankan), kata pengisi dibuang."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = _ke_hiragana(s)
    s = _PUNCT.sub(" ", s)
    return [k for k in s.split() if k not in _FILLER]


def _selisih_maks1(a: str, b: str) -> bool:
    """True kalau a dan b sama atau hanya beda satu huruf (ganti / sisip / hapus / tukar dua huruf berdekatan)."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        beda = [i for i in range(len(a)) if a[i] != b[i]]
        if len(beda) == 1:
            return True
        return (len(beda) == 2 and beda[1] == beda[0] + 1
                and a[beda[0]] == b[beda[1]] and a[beda[1]] == b[beda[0]])
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def _latin(s: str) -> bool:
    return bool(s) and all(ord(c) < 0x250 for c in s)


def cocok(tebakan: str, teka: Teka) -> bool:
    """Cocok bila (1) sama persis setelah dinormalisasi, atau untuk jawaban beraksara Latin: (2) semua kata jawaban
    ada berurutan di dalam tebakan pendek (mis. "koin logam" untuk "koin"), atau (3) salah ketik satu huruf pada
    jawaban satu kata sepanjang 4 huruf lebih (mis. "coin" untuk "koin"). Tidak butuh LLM."""
    t = normalisasi(tebakan)
    if not t:
        return False
    jaw = [normalisasi(a) for a in teka.semua_jawaban]
    if t in jaw:
        return True
    kt = _kata(tebakan)
    if not kt or len(kt) > 6:
        return False
    for a in teka.semua_jawaban:
        ka = _kata(a)
        if not ka or not all(_latin(k) for k in ka) or not all(_latin(k) for k in kt):
            continue
        n = len(ka)
        # (2) kata jawaban muncul berurutan di tebakan
        if len(kt) <= n + 3 and any(kt[i:i + n] == ka for i in range(len(kt) - n + 1)):
            return True
        # (3) salah ketik satu huruf (hanya jawaban satu kata, minimal 4 huruf)
        if n == 1 and len(ka[0]) >= 4 and len(kt) <= 3 and any(len(k) >= 4 and _selisih_maks1(k, ka[0]) for k in kt):
            return True
    return False


# ----------------------------------------------------------------------
# Pembuatan teka-teki oleh LLM
# ----------------------------------------------------------------------
_PROMPT_ID = (
    "Buat SATU teka-teki bahasa Indonesia yang orisinal, jawabannya pasti dan tidak ambigu, "
    "cocok untuk ngobrol santai. Jawaban berupa satu benda atau konsep umum (1-2 kata). "
    "Jangan membuat teka-teki yang jawabannya bergantung pada selera atau pendapat."
)
_PROMPT_JA = (
    "Buat SATU なぞなぞ bahasa Jepang yang orisinal dan umum dikenal (level SD-SMP), jawabannya "
    "pasti dan tidak ambigu. Pertanyaan hanya tulisan Jepang. Kalau jawabannya permainan kata, "
    "pastikan permainan kata itu benar-benar berlaku pada tulisan / bunyi jawabannya. "
    "Kalau tidak yakin, pilih teka-teki yang lebih sederhana."
)
_FORMAT = (
    '\nBalas HANYA satu objek JSON (tanpa teks lain, tanpa ```) dengan kunci: '
    '"pertanyaan", "jawaban" (daftar, jawaban utama pertama), "varian" (daftar ejaan / sinonim lain yang '
    'harus diterima), "petunjuk" (tepat 3, dari samar ke jelas; dua petunjuk pertama TIDAK boleh '
    'menyebut jawabannya), "penjelasan" (satu kalimat Indonesia kenapa itu jawabannya)'
)
_FORMAT_JA = (
    ', "baca" (pertanyaan ditulis hiragana / katakana saja untuk TTS), '
    '"terjemah" (terjemahan Indonesia)'
)


def prompt_buat(bahasa: str, hindari: list) -> str:
    """Prompt untuk meminta satu teka-teki baru. `hindari` = pertanyaan yang sudah ada."""
    dasar = _PROMPT_JA if bahasa == "ja" else _PROMPT_ID
    prompt = dasar + _FORMAT + (_FORMAT_JA if bahasa == "ja" else "") + "."
    if hindari:
        daftar = "\n".join(f"- {q}" for q in hindari[-HINDARI_MAKS:])
        prompt += f"\nJangan mengulang atau mirip dengan teka-teki ini:\n{daftar}"
    return prompt


_JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
_THINK = re.compile(r"<think>.*?</think>", re.S | re.I)


def _ekstrak_json(teks: str):
    """Ambil objek JSON pertama yang valid dari teks (abaikan blok <think>, pagar
    markdown, dan basa-basi yang mungkin memuat kurung kurawal)."""
    teks = _THINK.sub("", teks)
    dec = json.JSONDecoder()
    i = teks.find("{")
    while i >= 0:
        try:
            obj, _ = dec.raw_decode(teks, i)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
        i = teks.find("{", i + 1)
    return None


def parse_teka(raw, bahasa: str, id_baru: str) -> tuple[Optional[Teka], str]:
    """Ubah keluaran mentah LLM (str JSON atau dict) jadi Teka yang lolos
    pemeriksaan ketat. Mengembalikan (Teka, '') atau (None, alasan)."""
    if isinstance(raw, str):
        raw = _ekstrak_json(raw)
        if raw is None:
            return None, "tidak ada objek JSON"
    if not isinstance(raw, dict):
        return None, "bukan objek"

    e = dict(raw)
    for k in ("jawaban", "varian", "petunjuk"):   # LLM sering memberi string, bukan daftar
        if isinstance(e.get(k), str):
            e[k] = [e[k]]
    e["id"], e["bahasa"] = id_baru, bahasa
    teka, masalah = _validasi(e, id_baru, set())
    if teka is None:
        return None, masalah

    if len(teka.pertanyaan) > 200 or len(teka.jawaban[0]) > 40:
        return None, "terlalu panjang"
    if len(teka.petunjuk) < 2:
        return None, "petunjuk kurang dari 2"
    if not teka.penjelasan:
        return None, "penjelasan kosong"
    if bahasa == "ja":
        if not _JP_RE.search(teka.pertanyaan):
            return None, "pertanyaan bukan tulisan Jepang"
        if not teka.baca or not teka.terjemah:
            return None, "baca / terjemah kosong"
    jaw = normalisasi(teka.jawaban[0])
    if not jaw:
        return None, "jawaban kosong setelah normalisasi"
    if jaw in normalisasi(teka.pertanyaan):
        return None, "jawaban muncul di pertanyaan"
    if any(jaw in normalisasi(h) for h in teka.petunjuk[:2]):
        return None, "petunjuk membocorkan jawaban"
    return teka, ""


def _tulis_json(path: Path, data) -> None:
    """Tulis JSON secara atomik. Gagal tulis tidak boleh menjatuhkan server."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".iris_games_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError:
        pass


def _thread_latar(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, daemon=True, name="iris-isi-ulang").start()


# ----------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------
def _stat_awal() -> dict:
    return {
        "benar": 0, "menyerah": 0, "lewati": 0, "poin": 0,
        "streak": 0, "streak_terbaik": 0, "riwayat": [],
    }


class GameTekaTeki:
    """Satu sesi game. `hakim(pertanyaan, jawaban, tebakan) -> bool` opsional:
    dipanggil hanya bila tebakan tidak cocok, untuk menilai apakah artinya
    setara (mis. lewat LLM). Panggilannya harus sinkron dan tanpa riwayat chat.

    `pembuat(bahasa, hindari) -> str | dict` opsional: meminta LLM membuat satu
    teka-teki baru (lihat `prompt_buat`). Dipanggil di thread latar saat stok
    yang belum pernah muncul menipis, jadi `mulai()` tidak pernah menunggu LLM.
    Hasil divalidasi `parse_teka`, dibuang bila mirip yang sudah ada, lalu
    disimpan ke `dinamis_path`. `pemeriksa(teka) -> bool` opsional untuk
    verifikasi kedua oleh LLM; teka-teki Jepang HANYA dibuat bila pemeriksa ada.
    Callback harus aman dipanggil dari thread lain."""

    def __init__(
        self,
        bank_path,
        state_path=None,
        *,
        rng: Optional[random.Random] = None,
        hakim: Optional[Callable[[str, list, str], bool]] = None,
        sekarang: Callable[[], float] = time.time,
        dinamis_path=None,
        pembuat: Optional[Callable[[str, list], object]] = None,
        pemeriksa: Optional[Callable[[Teka], bool]] = None,
        latar: Callable[[Callable[[], None]], None] = _thread_latar,
    ):
        self.bank, self.peringatan = muat_bank(bank_path)
        self.dinamis_path = Path(dinamis_path) if dinamis_path else None
        self.pembuat = pembuat
        self.pemeriksa = pemeriksa
        self.latar = latar
        self._kunci = threading.RLock()
        self._sedang_isi: set[str] = set()
        if self.dinamis_path and self.dinamis_path.exists():
            tambahan, warn = muat_bank(self.dinamis_path)
            ada = {t.id for t in self.bank}
            self.bank += [t for t in tambahan if t.id not in ada]
            self.peringatan += warn
        self.state_path = Path(state_path) if state_path else None
        self.rng = rng or random.Random()
        self.hakim = hakim
        self.sekarang = sekarang
        self.aktif: Optional[Ronde] = None
        self.stat = self._muat_stat()

    # --- status -------------------------------------------------------
    def sedang_main(self) -> bool:
        self._cek_kedaluwarsa()
        return self.aktif is not None

    def _cek_kedaluwarsa(self) -> None:
        if self.aktif and self.sekarang() - self.aktif.aktivitas > KEDALUWARSA_DETIK:
            self.aktif = None

    # --- pintu masuk dari server.py -----------------------------------
    def tangani(self, teks: str) -> Optional[list[Balasan]]:
        """Kembalikan daftar Balasan bila pesan ini urusan game, selain itu None."""
        t = (teks or "").strip()
        if not t:
            return None
        self._cek_kedaluwarsa()

        if t.startswith("/"):
            bagian = t.split()
            cmd = bagian[0].casefold()
            if cmd in PERINTAH_UTAMA:
                arg = bagian[1].casefold() if len(bagian) > 1 else ""
                if arg in _SUB:
                    return self._sub(_SUB[arg])
                if arg in _MODE:
                    return self.mulai(_MODE[arg])
                return [Balasan(
                    "Pakai: /tekateki [id|jp|campur], /tekateki petunjuk, "
                    "/tekateki menyerah (atau /nyerah), /tekateki lewati, /tekateki stop, "
                    "/tekateki skor",
                    emosi="bingung", klip="miring")]
            if cmd in PERINTAH_PINTAS and self.aktif:
                return self._sub(PERINTAH_PINTAS[cmd])
            return None  # perintah lain lewat, ronde tetap hidup

        if self.aktif:
            if not cocok(t, self.aktif.teka):
                kt = set(_kata(t))
                n = len(_kata(t))
                if kt & _KATA_NYERAH and n <= 5:
                    return self.menyerah()
                if kt & _KATA_PETUNJUK and n <= 3:
                    return self.petunjuk()
                if kt & _KATA_LEWATI and n <= 2:
                    return self.lewati()
            return self.jawab(t)
        return None

    def _sub(self, nama: str) -> list[Balasan]:
        return {
            "petunjuk": self.petunjuk,
            "menyerah": self.menyerah,
            "lewati": self.lewati,
            "stop": self.stop,
            "skor": self.skor,
        }[nama]()

    # --- aksi ----------------------------------------------------------
    def mulai(self, mode: str = "campur", awalan: str = "") -> list[Balasan]:
        if not self.bank:
            return [Balasan("Bank teka-teki kosong atau gagal dibaca, "
                            "jadi aku belum bisa main.", emosi="sedih")]
        with self._kunci:
            pool = [t for t in self.bank if mode == "campur" or t.bahasa == mode]
            if not pool:
                return [Balasan("Belum ada teka-teki untuk mode itu.", emosi="sedih")]

            if self.aktif:
                awalan = awalan or "Oke, ganti teka-teki! "
            riwayat = self.stat["riwayat"]
            baru = [t for t in pool if t.id not in riwayat]
            if not baru:  # semua sudah pernah muncul: kosongkan riwayat pool ini
                ids = {t.id for t in pool}
                self.stat["riwayat"] = [i for i in riwayat if i not in ids]
                baru = pool

            teka = self.rng.choice(baru)
            self.stat["riwayat"].append(teka.id)
            self.stat["riwayat"] = self.stat["riwayat"][-RIWAYAT_MAKS:]
            self.aktif = Ronde(teka=teka, mode=mode, aktivitas=self.sekarang())
            self._simpan()
        self._picu_isi_ulang(mode)
        return [self._tampilkan(teka, awalan)]

    # --- pembuatan teka-teki baru ---------------------------------------
    def _bahasa_boleh(self) -> list[str]:
        return ["id", "ja"] if self.pemeriksa else ["id"]

    def _picu_isi_ulang(self, mode: str) -> None:
        """Mulai pembuatan di latar untuk bahasa yang stok barunya menipis."""
        if not self.pembuat:
            return
        with self._kunci:
            riwayat = set(self.stat["riwayat"])
            for b in self._bahasa_boleh():
                if mode not in ("campur", b) or b in self._sedang_isi:
                    continue
                sisa = sum(1 for t in self.bank if t.bahasa == b and t.id not in riwayat)
                if sisa <= ISI_ULANG_SISA:
                    self._sedang_isi.add(b)
                    try:
                        self.latar(lambda b=b: self.isi_ulang(b))
                    except Exception:
                        self._sedang_isi.discard(b)

    def isi_ulang(self, bahasa: str) -> Optional[Teka]:
        """Minta LLM membuat satu teka-teki, validasi, simpan. Sinkron (bisa lama);
        biasanya dipanggil lewat `latar`. Mengembalikan Teka baru atau None."""
        try:
            if not self.pembuat or bahasa not in self._bahasa_boleh():
                return None
            for _ in range(PERCOBAAN_BUAT):
                with self._kunci:
                    hindari = [t.pertanyaan for t in self.bank if t.bahasa == bahasa][-HINDARI_MAKS:]
                try:
                    raw = self.pembuat(bahasa, hindari)
                except Exception:
                    continue
                teka, _alasan = parse_teka(raw, bahasa, f"gen-{bahasa}-{uuid.uuid4().hex[:8]}")
                if teka is None or self._duplikat(teka):
                    continue
                if bahasa == "ja" or self.pemeriksa:
                    try:
                        if not (self.pemeriksa and self.pemeriksa(teka)):
                            continue
                    except Exception:
                        continue
                with self._kunci:
                    if self._duplikat(teka):
                        continue
                    self.bank.append(teka)
                    self._simpan_dinamis()
                return teka
            return None
        finally:
            with self._kunci:
                self._sedang_isi.discard(bahasa)

    def _duplikat(self, teka: Teka) -> bool:
        """Pertanyaan atau jawaban utama sudah ada di bank (bahasa yang sama)."""
        with self._kunci:
            q, j = normalisasi(teka.pertanyaan), normalisasi(teka.jawaban[0])
            for t in self.bank:
                if t.bahasa != teka.bahasa:
                    continue
                if normalisasi(t.pertanyaan) == q:
                    return True
                if j and j in {normalisasi(a) for a in t.semua_jawaban}:
                    return True
        return False

    def _simpan_dinamis(self) -> None:
        if not self.dinamis_path:
            return
        gen = [t for t in self.bank if t.id.startswith("gen-")][-DINAMIS_MAKS:]
        _tulis_json(self.dinamis_path, {"versi": 1, "teka_teki": [asdict(t) for t in gen]})

    def _tampilkan(self, teka: Teka, awalan: str = "") -> Balasan:
        if teka.bahasa == "ja":
            teks = f"{awalan}なぞなぞ: {teka.pertanyaan}"
            if teka.terjemah:
                teks += f"\n({teka.terjemah})"
        else:
            teks = f"{awalan}Teka-teki: {teka.pertanyaan}"
        teks += "\n(/petunjuk kalau buntu, /menyerah kalau nyerah)"
        return Balasan(
            teks, emosi="penasaran", klip="miring",
            ucapkan=(teka.baca or teka.pertanyaan) if teka.bahasa == "ja" else _jp("teka_id"),
            bahasa=teka.bahasa,
        )

    def jawab(self, tebakan: str) -> list[Balasan]:
        r = self.aktif
        if r is None:
            return [Balasan("Belum ada teka-teki. Ketik /tekateki untuk mulai!",
                            emosi="senang")]
        r.aktivitas = self.sekarang()

        benar = cocok(tebakan, r.teka)
        if not benar and self.hakim and 2 <= len(tebakan.strip()) <= 60:
            try:
                benar = bool(self.hakim(
                    r.teka.pertanyaan, list(r.teka.semua_jawaban), tebakan))
            except Exception:
                benar = False
        if benar:
            return self._benar()

        r.salah += 1
        teks = _KOMENTAR_SALAH[(r.salah - 1) % len(_KOMENTAR_SALAH)]
        sisa = min(len(r.teka.petunjuk), MAKS_PETUNJUK) - r.petunjuk_dipakai
        if r.salah % SALAH_SEBELUM_TAWAR == 0 and sisa > 0:
            teks += " Mau petunjuk? Ketik /petunjuk."
        return [Balasan(teks, emosi="menggoda",
                        klip="geleng" if r.salah == 1 else "miring",
                        ucapkan=_jp("salah"), bahasa="ja")]

    def _benar(self) -> list[Balasan]:
        r = self.aktif
        poin = max(1, POIN_DASAR - r.petunjuk_dipakai)
        s = self.stat
        s["benar"] += 1
        s["poin"] += poin
        s["streak"] += 1
        s["streak_terbaik"] = max(s["streak_terbaik"], s["streak"])
        teka = r.teka
        tanpa_petunjuk = r.petunjuk_dipakai == 0
        self.aktif = None
        self._simpan()

        teks = (f"Benar! Jawabannya {teka.jawaban[0]}. "
                f"+{poin} poin (beruntun: {s['streak']})")
        if teka.penjelasan:
            teks += f"\n{teka.penjelasan}"
        return [Balasan(teks, emosi="senang",
                        klip="tari_ceria" if tanpa_petunjuk else "angguk",
                        ucapkan=_jp("benar"), bahasa="ja")]

    def petunjuk(self) -> list[Balasan]:
        r = self.aktif
        if r is None:
            return [Balasan("Belum ada teka-teki. Ketik /tekateki untuk mulai!",
                            emosi="senang")]
        r.aktivitas = self.sekarang()
        total = min(len(r.teka.petunjuk), MAKS_PETUNJUK)
        if total == 0:
            return [Balasan("Teka-teki ini tidak punya petunjuk. Coba tebak dulu!",
                            emosi="menggoda", klip="miring")]
        if r.petunjuk_dipakai >= total:
            return [Balasan("Petunjuknya sudah habis. Tebak atau /menyerah ya.",
                            emosi="menggoda", klip="miring")]
        teks = f"Petunjuk {r.petunjuk_dipakai + 1}/{total}: {r.teka.petunjuk[r.petunjuk_dipakai]}"
        r.petunjuk_dipakai += 1
        poin = max(1, POIN_DASAR - r.petunjuk_dipakai)
        teks += f"\n(Kalau benar sekarang: {poin} poin)"
        return [Balasan(teks, emosi="berpikir", klip="dagu",
                        ucapkan=_jp("petunjuk"), bahasa="ja")]

    def menyerah(self) -> list[Balasan]:
        r = self.aktif
        if r is None:
            return [Balasan("Tidak ada teka-teki yang sedang jalan.", emosi="netral")]
        teka = r.teka
        self.aktif = None
        self.stat["streak"] = 0
        self.stat["menyerah"] += 1
        self._simpan()
        teks = f"Yah, menyerah ya~ Jawabannya: {teka.jawaban[0]}."
        if teka.penjelasan:
            teks += f"\n{teka.penjelasan}"
        return [Balasan(teks, emosi="menggoda", klip="dagu",
                        ucapkan=_jp("menyerah"), bahasa="ja")]

    def lewati(self) -> list[Balasan]:
        r = self.aktif
        if r is None:
            return [Balasan("Tidak ada teka-teki yang sedang jalan.", emosi="netral")]
        lama, mode = r.teka, r.mode
        self.aktif = None
        self.stat["lewati"] += 1
        return self.mulai(mode, awalan=f"Dilewati, jawabannya tadi {lama.jawaban[0]}. ")

    def stop(self) -> list[Balasan]:
        r = self.aktif
        if r is None:
            return [Balasan("Tidak ada teka-teki yang sedang jalan.", emosi="netral")]
        jawaban = r.teka.jawaban[0]
        self.aktif = None
        return [Balasan(f"Oke, selesai dulu. Jawaban yang tadi: {jawaban}.",
                        emosi="senang", klip="angguk",
                        ucapkan=_jp("stop"), bahasa="ja")]

    def skor(self) -> list[Balasan]:
        s = self.stat
        teks = (f"Benar: {s['benar']} | Menyerah: {s['menyerah']} | "
                f"Dilewati: {s['lewati']}\n"
                f"Poin: {s['poin']} | Beruntun: {s['streak']} "
                f"(terbaik {s['streak_terbaik']})")
        return [Balasan(teks, emosi="senang", ucapkan=_jp("skor"), bahasa="ja")]

    # --- penyimpanan ---------------------------------------------------
    def _muat_stat(self) -> dict:
        stat = _stat_awal()
        if not self.state_path or not self.state_path.exists():
            return stat
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return stat
        if not isinstance(data, dict):
            return stat
        for k, v in stat.items():
            if k == "riwayat":
                lama = data.get(k)
                if isinstance(lama, list):
                    stat[k] = [x for x in lama if isinstance(x, str)][-RIWAYAT_MAKS:]
            elif isinstance(data.get(k), int) and not isinstance(data.get(k), bool):
                stat[k] = max(0, data[k])
        return stat

    def _simpan(self) -> None:
        if self.state_path:
            _tulis_json(self.state_path, self.stat)


# ----------------------------------------------------------------------
# Penghubung LLM (9Router / OpenAI-compatible)
# ----------------------------------------------------------------------
# Semua fungsi sinkron dan tanpa riwayat chat, jadi aman dipanggil dari thread
# latar GameTekaTeki.
_SISTEM_BUAT = ("Kamu penulis teka-teki yang teliti. Jawaban teka-tekimu selalu pasti dan "
                "tidak ambigu, dan kamu tidak pernah membocorkan jawaban di pertanyaan.")
_SISTEM_CEK = ("Kamu juri teka-teki yang ketat dan jujur. Kamu lebih suka menolak "
               "teka-teki yang diragukan.")
_PROMPT_CEK = (
    "Periksa teka-teki berikut dengan teliti.\n"
    "Pertanyaan: {q}\nJawaban utama: {a}\nVarian diterima: {v}\n"
    "Balas HANYA satu baris. Tulis OK kalau (1) jawaban utamanya memang jawaban yang "
    "benar dan satu-satunya yang masuk akal, (2) permainan kata / logika teka-teki "
    "benar-benar berlaku (untuk bahasa Jepang periksa bunyi dan tulisannya), dan "
    "(3) bahasanya wajar. Kalau tidak, tulis: SALAH: <alasan singkat>. Ragu = SALAH."
)
_RE_CEK = re.compile(r"^\W*(?:(OK)\W*|(SALAH)\b.*)$", re.I)


def _chat(url: str, key: str, model: str, system: str, user: str, timeout: float) -> str:
    import httpx  # impor malas: modul ini tetap bisa dipakai tanpa httpx

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    r = httpx.post(
        f"{url.rstrip('/')}/chat/completions", headers=headers, timeout=timeout,
        json={"model": model, "stream": False,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]},
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"] or ""


def buat_pembuat(url: str, key: str, model: str, timeout: float = 60.0) -> Callable[[str, list], str]:
    def pembuat(bahasa: str, hindari: list) -> str:
        return _chat(url, key, model, _SISTEM_BUAT, prompt_buat(bahasa, hindari), timeout)
    return pembuat


def buat_pemeriksa(url: str, key: str, model: str, timeout: float = 45.0) -> Callable[[Teka], bool]:
    def pemeriksa(teka: Teka) -> bool:
        out = _chat(url, key, model, _SISTEM_CEK, _PROMPT_CEK.format(
            q=teka.pertanyaan, a=teka.jawaban[0], v=", ".join(teka.varian) or "-"), timeout)
        # Ambil baris putusan TERAKHIR (model penalar bisa menulis "OK, ..." di tengah
        # pikirannya). "OK" harus berdiri sendiri; "SALAH: alasan" boleh panjang.
        putusan = None
        for baris in _THINK.sub("", out).splitlines():
            m = _RE_CEK.match(baris.strip())
            if m:
                putusan = bool(m.group(1))
        if putusan is not None:
            return putusan
        return False   # format aneh = tolak
    return pemeriksa
