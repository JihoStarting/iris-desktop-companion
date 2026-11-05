# by: KangJiho
"""Tes: apakah Hermes benar-benar BERHENTI mengerjakan tugas setelah koneksi dari server.py diputus (cancel)?

Cara kerja: Hermes disuruh 12 langkah terpisah, tiap langkah menulis satu baris ke file di folder Download Windows
(lalu tidur 4 detik). Setelah 14 detik koneksi diputus persis seperti tombol Stop. Kalau file TERUS bertambah,
agen tetap jalan; kalau berhenti, cancel bekerja. Dites dua mode: biasa dan stream (HERMES_STREAM=1).

Jalankan di PowerShell, dari folder server.py, SAAT TIDAK ADA tugas Hermes lain:
    .\\.venv\\Scripts\\python.exe cek-cancel-hermes.py
Tes memakai file dummy di Downloads (cancel-probe-*.txt). Tidak ada file lain yang disentuh.
"""
import asyncio, json, os, sys, time
from pathlib import Path
import httpx
from dotenv import dotenv_values

env = {**dotenv_values(Path.home() / ".env"), **dotenv_values(Path(__file__).parent / ".env"), **os.environ}
URL = (env.get("HERMES_URL") or "http://127.0.0.1:8642/v1").rstrip("/")
KEY = env.get("HERMES_API_KEY", "")
WIN_DIR = Path.home() / "Downloads"
p = WIN_DIR.as_posix()                       # C:/Users/Nama/Downloads
WSL_DIR = f"/mnt/{p[0].lower()}{p[2:]}"      # /mnt/c/Users/Nama/Downloads
CUT_AFTER, WATCH = 14, 60


def lines(f: Path) -> int:
    try:
        return len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
    except FileNotFoundError:
        return 0


async def run(mode: str) -> None:
    f = WIN_DIR / f"cancel-probe-{mode}.txt"
    f.unlink(missing_ok=True)
    wsl = f"{WSL_DIR}/cancel-probe-{mode}.txt"
    task = (f"Kerjakan 12 langkah TERPISAH, satu per satu, berurutan. Di langkah N panggil tool terminal SATU kali dengan "
            f"perintah: echo \"langkah N $(date +%T)\" >> \"{wsl}\" && sleep 4  (ganti N dengan nomor langkah). "
            f"Jangan memakai loop dan jangan menggabungkan langkah. Setelah langkah 12 balas satu kata: selesai.")
    payload = {"model": "hermes-agent", "stream": mode == "stream", "messages": [{"role": "user", "content": task}]}
    headers = {"Authorization": f"Bearer {KEY}"} if KEY else {}

    async def call() -> None:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as c:
            if mode == "stream":
                async with c.stream("POST", f"{URL}/chat/completions", json=payload, headers=headers) as r:
                    async for _ in r.aiter_lines():
                        pass
            else:
                await c.post(f"{URL}/chat/completions", json=payload, headers=headers)

    print(f"\n=== mode {mode} ===")
    t = asyncio.create_task(call())
    await asyncio.sleep(CUT_AFTER)
    before = lines(f)
    t.cancel()
    await asyncio.gather(t, return_exceptions=True)
    print(f"koneksi diputus setelah {CUT_AFTER} dtk; baris di file saat itu: {before}")
    hist = []
    for i in range(WATCH // 10):
        await asyncio.sleep(10)
        hist.append(lines(f))
        print(f"  +{(i + 1) * 10:>2} dtk: {hist[-1]} baris")
    if before == 0:
        print("HASIL: tidak ada baris sebelum diputus; Hermes belum sempat bekerja atau path salah. Ulangi / cek Hermes aktif.")
    elif hist[-1] > before + 1:
        print("HASIL: TETAP JALAN. Agen tidak berhenti setelah koneksi putus (cancel hanya memutus sisi Iris).")
    else:
        print("HASIL: BERHENTI. Agen berhenti setelah koneksi putus.")


async def main() -> None:
    if "--health" not in sys.argv:
        async with httpx.AsyncClient(timeout=5) as c:
            try:
                r = await c.get(f"{URL}/health")
                print("Hermes /health:", r.status_code)
            except Exception as e:
                sys.exit(f"Hermes tidak terjangkau di {URL}: {e!r}")
    for mode in ("biasa", "stream"):
        await run(mode)
        await asyncio.sleep(20)   # beri waktu langkah terakhir selesai sebelum mode berikutnya
    print("\nPakai mode yang HASIL-nya BERHENTI: set HERMES_STREAM=1 (stream) atau 0 (biasa) di .env, lalu restart server.")
    print("Kalau dua-duanya TETAP JALAN: butuh endpoint stop di api_server.py Hermes (kirim kode _handle_chat_completions).")


asyncio.run(main())
