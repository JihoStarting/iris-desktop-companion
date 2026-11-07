# by: KangJiho
"""Tes: apakah endpoint stop Hermes (POST /v1/runs/{run_id}/stop) benar-benar menghentikan agen?

Latar: scripts/cek-cancel-hermes.py membuktikan bahwa memutus koneksi TIDAK menghentikan agen. Hermes punya endpoint
POST /v1/runs/{run_id}/stop. Tes ini mengukur dua jalur, memakai tugas dan file dummy yang sama dengan cek-cancel:

  A. stream : /chat/completions (stream) -> ambil "id" dari potongan SSE pertama -> stop lewat id itu.
              Kode Hermes menyebut id stream bisa dipakai sebagai run_id (untuk /approval); stop belum tentu.
  B. runs   : POST /v1/runs {"input": ...} -> run_id -> stop -> pantau status lewat GET /v1/runs/{run_id}.

Skrip juga MENCETAK balasan mentah (status HTTP + isi) supaya bentuk respons Hermes kelihatan.
Jalankan dari folder proyek, SAAT TIDAK ADA tugas Hermes lain:
    .\\.venv\\Scripts\\python.exe scripts\\cek-stop-hermes.py
Opsi: --skip-health, --hanya-stream, --hanya-runs. Tes memakai file dummy Downloads\\stop-probe-*.txt.
"""
import asyncio, json, os, sys
from pathlib import Path
import httpx
from dotenv import dotenv_values

env = {**dotenv_values(Path.home() / ".env"), **dotenv_values(Path(__file__).resolve().parent.parent / ".env"), **os.environ}
URL = (env.get("HERMES_URL") or "http://127.0.0.1:8642/v1").rstrip("/")
KEY = env.get("HERMES_API_KEY", "")
WIN_DIR = Path(env.get("PROBE_WIN_DIR") or (Path.home() / "Downloads"))
if env.get("PROBE_WSL_DIR"):
    WSL_DIR = env["PROBE_WSL_DIR"].rstrip("/")
else:
    _p = WIN_DIR.as_posix()                      # C:/Users/Nama/Downloads
    WSL_DIR = f"/mnt/{_p[0].lower()}{_p[2:]}"    # /mnt/c/Users/Nama/Downloads
CUT_AFTER = int(env.get("PROBE_CUT", 14))
WATCH = int(env.get("PROBE_WATCH", 60))
STEP = int(env.get("PROBE_STEP", 10))
TOTAL_STEPS = 12
HEAD = {"Authorization": f"Bearer {KEY}"} if KEY else {}


def lines(f: Path) -> int:
    try:
        return len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
    except FileNotFoundError:
        return 0


def task_text(wsl_file: str) -> str:
    return (f"Kerjakan {TOTAL_STEPS} langkah TERPISAH, satu per satu, berurutan. Di langkah N panggil tool terminal SATU kali dengan "
            f"perintah: echo \"langkah N $(date +%T)\" >> \"{wsl_file}\" && sleep 4  (ganti N dengan nomor langkah). "
            f"Jangan memakai loop dan jangan menggabungkan langkah. Setelah langkah {TOTAL_STEPS} balas satu kata: selesai.")


async def post_stop(c: httpx.AsyncClient, rid: str) -> int:
    try:
        r = await c.post(f"{URL}/runs/{rid}/stop", headers=HEAD, json={})
    except Exception as e:
        print(f"  stop GAGAL dikirim: {e!r}")
        return -1
    print(f"  POST /runs/{rid}/stop -> HTTP {r.status_code}: {r.text[:300]}")
    return r.status_code


async def pantau(f: Path, before: int, c: httpx.AsyncClient | None = None, rid: str = "") -> None:
    hist = []
    for i in range(max(1, WATCH // STEP)):
        await asyncio.sleep(STEP)
        hist.append(lines(f))
        extra = ""
        if c is not None and rid:
            try:
                st = (await c.get(f"{URL}/runs/{rid}", headers=HEAD)).json()
                extra = f"  status Hermes: {st.get('status')}"
            except Exception as e:
                extra = f"  (GET status gagal: {e!r})"
        print(f"  +{(i + 1) * STEP:>2} dtk: {hist[-1]} baris{extra}")
    if before == 0:
        print("HASIL: tidak ada baris sebelum stop; Hermes belum sempat bekerja atau path salah. Ulangi / cek Hermes aktif.")
    elif hist[-1] >= TOTAL_STEPS:
        print(f"HASIL: TIDAK MEYAKINKAN. Tugas sudah mencapai {TOTAL_STEPS} baris (selesai sendiri). Ulangi dengan CUT lebih awal.")
    elif len(hist) >= 3 and len(set(hist[-3:])) == 1:
        print("HASIL: BERHENTI. Jumlah baris tidak bertambah lagi setelah stop.")
    else:
        print("HASIL: TETAP JALAN. Baris terus bertambah setelah stop.")


async def uji_stream() -> None:
    print("\n=== A. stream: stop lewat completion id ===")
    f = WIN_DIR / "stop-probe-stream.txt"
    f.unlink(missing_ok=True)
    payload = {"model": "hermes-agent", "stream": True,
               "messages": [{"role": "user", "content": task_text(f"{WSL_DIR}/stop-probe-stream.txt")}]}
    got: dict = {}

    async def baca(c: httpx.AsyncClient) -> None:
        try:
            async with c.stream("POST", f"{URL}/chat/completions", json=payload, headers=HEAD) as r:
                got["http"] = r.status_code
                if r.status_code >= 400:
                    got["err"] = (await r.aread()).decode("utf-8", "replace")[:300]
                    return
                async for line in r.aiter_lines():
                    if line.startswith("data:") and "id" not in got:
                        try:
                            got["id"] = json.loads(line[5:].strip()).get("id") or ""
                        except Exception:
                            pass
        except Exception as e:
            got["exc"] = repr(e)

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=600.0)) as c:
        t = asyncio.create_task(baca(c))
        for _ in range(60):          # tunggu potongan SSE pertama (maks ~30 dtk)
            if got.get("id") or got.get("err") or got.get("exc"):
                break
            await asyncio.sleep(0.5)
        print(f"  id dari SSE pertama: {got.get('id')!r}" + (f"  (error: {got.get('err') or got.get('exc')})" if not got.get("id") else ""))
        if not got.get("id"):
            t.cancel()
            await asyncio.gather(t, return_exceptions=True)
            print("HASIL: TIDAK BISA DIUJI (tidak ada id di potongan SSE pertama).")
            return
        await asyncio.sleep(CUT_AFTER)
        before = lines(f)
        print(f"  stop dikirim setelah {CUT_AFTER} dtk; baris di file saat itu: {before}  (koneksi stream SENGAJA tetap terbuka)")
        await post_stop(c, got["id"])
        await pantau(f, before, c, got["id"])
        t.cancel()
        await asyncio.gather(t, return_exceptions=True)


async def uji_runs() -> None:
    print("\n=== B. runs: POST /v1/runs lalu stop ===")
    f = WIN_DIR / "stop-probe-runs.txt"
    f.unlink(missing_ok=True)
    body = {"input": task_text(f"{WSL_DIR}/stop-probe-runs.txt")}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=60.0)) as c:
        try:
            r = await c.post(f"{URL}/runs", json=body, headers=HEAD)
        except Exception as e:
            print(f"HASIL: TIDAK BISA DIUJI (POST /runs gagal: {e!r})")
            return
        print(f"  POST /runs -> HTTP {r.status_code}: {r.text[:400]}")
        try:
            j = r.json()
        except Exception:
            j = {}
        rid = j.get("run_id") or j.get("id")
        if r.status_code >= 400 or not rid:
            print("HASIL: TIDAK BISA DIUJI (tidak ada run_id di balasan; lihat isi balasan di atas).")
            return
        await asyncio.sleep(CUT_AFTER)
        before = lines(f)
        print(f"  stop dikirim setelah {CUT_AFTER} dtk; baris di file saat itu: {before}")
        await post_stop(c, rid)
        await pantau(f, before, c, rid)
        try:
            print("  status akhir (mentah):", (await c.get(f"{URL}/runs/{rid}", headers=HEAD)).text[:800])
        except Exception as e:
            print(f"  status akhir gagal dibaca: {e!r}")


async def main() -> None:
    if "--skip-health" not in sys.argv:
        async with httpx.AsyncClient(timeout=5) as c:
            try:
                r = await c.get(f"{URL}/health")
                print("Hermes /health:", r.status_code)
            except Exception as e:
                sys.exit(f"Hermes tidak terjangkau di {URL}: {e!r}")
    if "--hanya-runs" not in sys.argv:
        await uji_stream()
        if "--hanya-stream" not in sys.argv:
            await asyncio.sleep(int(env.get("PROBE_GAP", 20)))   # beri waktu langkah terakhir selesai
    if "--hanya-stream" not in sys.argv:
        await uji_runs()
    print("\nKirim seluruh keluaran ini ke Claude: balasan mentah di atas menentukan bentuk perubahan server.py.")


asyncio.run(main())
