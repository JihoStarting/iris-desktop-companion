r"""Tes v71: pemetaan path sandbox Docker dan verifikasi hasil agen. Jalankan: .\.venv\Scripts\python.exe tests\test_sandbox.py"""
import os, sys, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["HERMES_SANDBOX"] = "1"
os.environ["HERMES_SANDBOX_WIN"] = r"D:\praktek\_hermes"
os.environ["HERMES_SANDBOX_RO_WIN"] = r"D:\praktek-bot"
os.environ["HERMES_STREAM"] = "1"
import server as S

ok = fail = 0
def check(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  lulus ", name)
    else: fail += 1; print("  GAGAL ", name, extra)

def raises(fn, *a):
    try: fn(*a)
    except S.SandboxPathError as e: return str(e)
    return None

# --- tugas masuk
check("path sandbox dipetakan", S.sandbox_prepare_task(r"buat file D:\praktek\_hermes\a\b.txt isi halo") == "buat file /workspace/out/a/b.txt isi halo")
check("huruf besar kecil drive tidak masalah", "/workspace/out/x.txt" in S.sandbox_prepare_task(r"hapus d:\PRAKTEK\_Hermes\x.txt"))
check("read-only dipetakan", "/workspace/praktek/f.py" in S.sandbox_prepare_task(r"baca D:\praktek-bot\f.py"))
check("Z: ditolak", raises(S.sandbox_prepare_task, r"hapus file Z:\Projek AI waifu Dekstop\umpan.txt") is not None)
check("C: ditolak", raises(S.sandbox_prepare_task, r"buka C:\Users\x\a.txt") is not None)
check("/mnt/z ditolak", raises(S.sandbox_prepare_task, "hapus /mnt/z/proyek/a.txt") is not None)
check("D: lain ditolak", raises(S.sandbox_prepare_task, r"hapus D:\praktek\lain\a.txt") is not None)
check("awalan mirip ditolak (_hermes2)", raises(S.sandbox_prepare_task, r"hapus D:\praktek\_hermes2\a.txt") is not None)
check("URL tidak dianggap path", S.sandbox_prepare_task("cari berita di https://example.com/a") == "cari berita di https://example.com/a")
check("tanpa path tidak diubah", S.sandbox_prepare_task("siapa Solon") == "siapa Solon")

# --- hasil keluar
u = S.to_windows_paths
check("path inline", u("File ada di /workspace/out/laporan.txt.") == "File ada di D:\\praktek\\_hermes\\laporan.txt.")
check("path baris berspasi", u("Path:\n/workspace/out/Laporan KKN Final.docx") == "Path:\nD:\\praktek\\_hermes\\Laporan KKN Final.docx")
check("ro path", u("lihat /workspace/praktek/x/y.py") == "lihat D:\\praktek-bot\\x\\y.py")
check("folder root", u("isi di /workspace/out") == "isi di D:\\praktek\\_hermes")
check("awalan mirip tidak diubah", u("/workspace/outer/x") == "/workspace/outer/x")
check("mnt masih diubah", u("/mnt/c/Users/a/b.txt") == "C:\\Users\\a\\b.txt")

# --- verifikasi (os.path.exists dipalsukan)
real = S.os.path.exists
def fake(existing):
    S.os.path.exists = lambda p: p in existing
try:
    fake({r"D:\praktek\_hermes\a.txt"})
    check("buat: ada = catatan ada", "Ada di disk" in S.sandbox_verify_note("buat a.txt", "Selesai: /workspace/out/a.txt"))
    fake(set())
    n = S.sandbox_verify_note("buat a.txt", "Selesai: /workspace/out/a.txt")
    check("buat: tidak ada = peringatan", "TIDAK ditemukan" in n and r"D:\praktek\_hermes\a.txt" in n, n)
    fake({r"D:\praktek\_hermes\c.txt"})
    n = S.sandbox_verify_note(r"hapus D:\praktek\_hermes\c.txt", "File berhasil dihapus.")
    check("hapus: masih ada = peringatan walau agen tak sebut path", "MASIH ADA" in n and "c.txt" in n, n)
    fake(set())
    n = S.sandbox_verify_note(r"hapus D:\praktek\_hermes\c.txt", "File berhasil dihapus.")
    check("hapus: sudah tidak ada = konfirmasi", "sudah tidak ada" in n, n)
    check("tanpa path = kosong", S.sandbox_verify_note("siapa Solon", "Solon adalah negarawan Athena.") == "")
    fake(set())
    n = S.sandbox_verify_note("simpan", "Path:\n/workspace/out/Laporan KKN Final.docx")
    check("path berspasi diperiksa utuh", "Laporan KKN Final.docx" in n, n)
finally:
    S.os.path.exists = real

# --- prompt sistem
check("system prompt memuat sandbox", "LINGKUNGAN SANDBOX" in S.HERMES_SYSTEM and "/workspace/out" in S.HERMES_SYSTEM)
check("system prompt tidak lagi menyuruh /mnt/c", "SELALU pakai folder Windows" not in S.HERMES_SYSTEM)

# --- ask_hermes menolak sebelum menghubungi Hermes
import httpx
class Boom(httpx.AsyncBaseTransport):
    called = False
    async def handle_async_request(self, request):
        Boom.called = True
        raise AssertionError("tidak boleh menghubungi Hermes")
async def go():
    async with httpx.AsyncClient(transport=Boom()) as c:
        try:
            await S.ask_hermes(c, r"hapus file Z:\umpan.txt")
        except S.SandboxPathError:
            return True
    return False
check("ask_hermes menolak tanpa panggilan jaringan", asyncio.run(go()) and not Boom.called)
check("pesan galat Iris jelas", S.describe_hermes_error(S.SandboxPathError("x")).startswith("tidak dikirim ke Hermes"))

print(f"\n{ok} lulus, {fail} gagal")
sys.exit(1 if fail else 0)
