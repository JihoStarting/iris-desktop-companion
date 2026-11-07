"""
Tes gerbang persetujuan asli (v66): frame SSE `approval.request` dari Hermes -> kartu di overlay -> POST /runs/{id}/approval.

Jalankan dari folder proyek:
    python tests/test_approval_gate.py
(atau `python -m pytest tests/test_approval_gate.py`). Tidak butuh Hermes, 9Router, maupun VOICEVOX: Hermes dipalsukan
dengan httpx.MockTransport yang aliran SSE-nya benar-benar BERHENTI menunggu jawaban sebelum melanjutkan.
"""
import asyncio
import contextlib
import faulthandler
import json
import os
import sys
import traceback
from pathlib import Path

os.environ.setdefault("HERMES_STREAM", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
faulthandler.dump_traceback_later(120, exit=True)   # jaring pengaman: tes yang menggantung dimatikan, bukan ditunggu selamanya

import httpx  # noqa: E402
import server  # noqa: E402


@contextlib.contextmanager
def patched(**kw):
    old = {k: getattr(server, k) for k in kw}
    try:
        for k, v in kw.items():
            setattr(server, k, v)
        yield
    finally:
        for k, v in old.items():
            setattr(server, k, v)


# ----------------------------------------------------------------------------
# Hermes palsu
# ----------------------------------------------------------------------------
def sse(event: str | None, obj) -> bytes:
    head = f"event: {event}\n" if event else ""
    return (head + "data: " + (obj if isinstance(obj, str) else json.dumps(obj)) + "\n\n").encode()


def chunk(text: str = "", cid: str = "chatcmpl-1") -> bytes:
    delta = {"content": text} if text else {"role": "assistant"}
    return sse(None, {"id": cid, "choices": [{"delta": delta}]})


APPROVAL = {"run_id": "chatcmpl-1", "session_id": "s1", "request_id": "r1", "command": "rm -rf /mnt/z/tes/folder-uji",
            "smart_denied": False, "allow_session": True, "allow_permanent": True,
            "choices": ["once", "session", "always", "deny"]}


class FakeHermes:
    """Aliran: potongan awal, frame izin, LALU menunggu POST /approval (maks. 5 dtk), baru potongan akhir + [DONE]."""

    def __init__(self, approval_frames=(("approval.request", APPROVAL),), post_status=200, wait_forever=False):
        self.frames = list(approval_frames)
        self.posts: list[tuple[str, dict]] = []
        self.post_status = post_status
        self.wait_forever = wait_forever
        self.got_post = asyncio.Event()
        outer = self

        class _Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield chunk()
                for ev, obj in outer.frames:
                    yield sse(ev, obj)
                if outer.frames:
                    if outer.wait_forever:
                        await asyncio.Event().wait()
                    try:
                        await asyncio.wait_for(outer.got_post.wait(), 5)
                    except asyncio.TimeoutError:
                        yield chunk("TIDAK ADA JAWABAN IZIN")
                        yield b"data: [DONE]\n\n"
                        return
                yield chunk("selesai ")
                yield chunk("dikerjakan")
                yield b"data: [DONE]\n\n"

            async def aclose(self):
                pass

        self._stream = _Stream

    async def handler(self, request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/approval"):
            self.posts.append((request.url.path, json.loads(request.content)))
            self.got_post.set()
            return httpx.Response(self.post_status, json={"resolved": 1} if self.post_status == 200 else {"error": "x"})
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=self._stream())

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handler))


async def run_stream(fake: FakeHermes, approver):
    async with fake.client() as c:
        return await server._hermes_stream(c, {}, {"model": "hermes-agent", "messages": []}, approver)


def run(coro, batas: float = 20.0):
    """asyncio.run dengan batas waktu: tes yang menggantung GAGAL dengan pesan jelas, bukan membeku."""
    async def _w():
        try:
            return await asyncio.wait_for(coro, batas)
        except asyncio.TimeoutError:
            raise AssertionError(f"tes menggantung lebih dari {batas:g} detik")
    return asyncio.run(_w())


def in_thread(fn, *args, batas: float = 30.0):
    """Jalankan fn di thread; kalau lewat batas (mis. receive_json menunggu pesan yang tidak pernah datang), gagal dengan jelas."""
    import threading
    box = {}
    def _t():
        try:
            box["ok"] = fn(*args)
        except BaseException as e:   # noqa: BLE001
            box["err"] = e
    th = threading.Thread(target=_t, daemon=True)
    th.start()
    th.join(batas)
    if th.is_alive():
        raise AssertionError(f"tes menggantung lebih dari {batas:g} detik (pesan yang ditunggu tidak datang)")
    if "err" in box:
        raise box["err"]
    return box["ok"]


def approver_returning(choice, seen: list | None = None):
    async def _a(req):
        if seen is not None:
            seen.append(req)
        return choice
    return _a


# ----------------------------------------------------------------------------
# parse_approval_event
# ----------------------------------------------------------------------------
def test_parse_datar():
    r = server.parse_approval_event(APPROVAL)
    assert r["command"] == "rm -rf /mnt/z/tes/folder-uji"
    assert r["request_id"] == "r1" and r["run_id"] == "chatcmpl-1"
    assert r["can_once"] is True and r["smart_denied"] is False


def test_parse_bersarang():
    r = server.parse_approval_event({"run_id": "x1", "approval": {"command": "find . -delete", "description": "hapus massal",
                                                                  "choices": ["once", "deny"], "smart_denied": True}})
    assert r["command"] == "find . -delete" and r["description"] == "hapus massal"
    assert r["run_id"] == "x1" and r["smart_denied"] is True


def test_parse_tanpa_perintah_atau_bukan_dict():
    for bad in ({}, {"command": "   "}, {"command": 5}, None, "teks", ["a"]):
        assert server.parse_approval_event(bad)["command"] == "", bad


def test_parse_tanpa_once_hanya_tolak():
    assert server.parse_approval_event({"command": "x", "choices": ["deny"]})["can_once"] is False
    assert server.parse_approval_event({"command": "x", "choices": []})["can_once"] is True   # tidak disebut = asumsi bawaan


def test_parse_request_id_bukan_bool():
    assert server.parse_approval_event({"command": "x", "request_id": True})["request_id"] == ""
    assert server.parse_approval_event({"command": "x", "request_id": 42})["request_id"] == "42"


# ----------------------------------------------------------------------------
# _hermes_stream: alur izin
# ----------------------------------------------------------------------------
def test_izinkan_sekali_diteruskan_dan_tugas_lanjut():
    async def main():
        fake, seen = FakeHermes(), []
        with patched(APPROVAL_ENABLED=True):
            out = await run_stream(fake, approver_returning("once", seen))
        assert out == "selesai dikerjakan", out   # aliran memang BERLANJUT setelah jawaban
        assert fake.posts == [("/v1/runs/chatcmpl-1/approval", {"choice": "once", "request_id": "r1"})], fake.posts
        assert seen[0]["command"] == "rm -rf /mnt/z/tes/folder-uji"
    run(main())


def test_tolak_diteruskan():
    async def main():
        fake = FakeHermes()
        with patched(APPROVAL_ENABLED=True):
            out = await run_stream(fake, approver_returning("deny"))
        assert out == "selesai dikerjakan"
        assert fake.posts[0][1] == {"choice": "deny", "request_id": "r1"}
    run(main())


def test_pilihan_session_dan_always_tidak_pernah_dikirim():
    async def main():
        for bad in ("session", "always", "yolo", "", None, "ONCE"):
            fake = FakeHermes()
            with patched(APPROVAL_ENABLED=True):
                await run_stream(fake, approver_returning(bad))
            assert fake.posts[0][1]["choice"] == "deny", (bad, fake.posts)
    run(main())


def test_tanpa_penjawab_ditolak():
    async def main():
        fake = FakeHermes()
        with patched(APPROVAL_ENABLED=True):
            await run_stream(fake, None)
        assert fake.posts[0][1]["choice"] == "deny"
    run(main())


def test_penjawab_galat_ditolak():
    async def main():
        async def boom(req):
            raise RuntimeError("kartu gagal")
        fake = FakeHermes()
        with patched(APPROVAL_ENABLED=True):
            out = await run_stream(fake, boom)
        assert out == "selesai dikerjakan" and fake.posts[0][1]["choice"] == "deny"
    run(main())


def test_perintah_tak_terbaca_ditolak_tanpa_bertanya():
    async def main():
        fake, seen = FakeHermes(approval_frames=(("approval.request", {"run_id": "chatcmpl-1", "choices": ["once", "deny"]}),)), []
        with patched(APPROVAL_ENABLED=True):
            await run_stream(fake, approver_returning("once", seen))
        assert seen == [], "penjawab tidak boleh ditanya untuk perintah yang tidak terbaca"
        assert fake.posts[0][1]["choice"] == "deny"
    run(main())


def test_hermes_tidak_menawarkan_once_maka_once_dipaksa_tolak():
    async def main():
        frame = dict(APPROVAL, choices=["deny"])
        fake = FakeHermes(approval_frames=(("approval.request", frame),))
        with patched(APPROVAL_ENABLED=True):
            await run_stream(fake, approver_returning("once"))
        assert fake.posts[0][1]["choice"] == "deny"
    run(main())


def test_gerbang_dimatikan_menolak_otomatis():
    async def main():
        fake, seen = FakeHermes(), []
        with patched(APPROVAL_ENABLED=False):
            await run_stream(fake, approver_returning("once", seen))
        assert seen == [] and fake.posts[0][1]["choice"] == "deny"
    run(main())


def test_frame_tanpa_baris_event_tapi_bertipe_dikenali():
    async def main():
        fake = FakeHermes(approval_frames=((None, dict(APPROVAL, type="approval.request")),))
        with patched(APPROVAL_ENABLED=True):
            out = await run_stream(fake, approver_returning("once"))
        assert out == "selesai dikerjakan" and fake.posts[0][1]["choice"] == "once"
    run(main())


def test_id_cadangan_dari_amplop_dicoba_kalau_id_pertama_ditolak():
    async def main():
        # id potongan biasa "chatcmpl-1" dijawab 404, id amplop "run-9" harus dicoba berikutnya
        posts = []
        got = asyncio.Event()

        async def handler(request):
            if request.url.path.endswith("/approval"):
                posts.append(request.url.path)
                got.set()
                return httpx.Response(404 if "chatcmpl-1" in request.url.path else 200, json={})
            class S(httpx.AsyncByteStream):
                async def __aiter__(self):
                    yield chunk()
                    yield sse("approval.request", dict(APPROVAL, run_id="run-9"))
                    await asyncio.wait_for(got.wait(), 5)
                    await asyncio.sleep(0.2)
                    yield chunk("ok")
                    yield b"data: [DONE]\n\n"
                async def aclose(self): pass
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=S())
        with patched(APPROVAL_ENABLED=True):
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
                out = await server._hermes_stream(c, {}, {}, approver_returning("deny"))
        assert out == "ok"
        assert posts == ["/v1/runs/chatcmpl-1/approval", "/v1/runs/run-9/approval"], posts
    run(main())


def test_post_409_tidak_membuat_tugas_galat():
    async def main():
        fake = FakeHermes(post_status=409)
        with patched(APPROVAL_ENABLED=True):
            out = await run_stream(fake, approver_returning("once"))
        assert out == "selesai dikerjakan" and len(fake.posts) == 1   # 409 = berhenti, tidak mengulang ke id lain
    run(main())


def test_tanpa_frame_izin_perilaku_lama_tidak_berubah():
    async def main():
        fake = FakeHermes(approval_frames=())
        out = await run_stream(fake, approver_returning("once"))
        assert out == "selesai dikerjakan" and fake.posts == []
    run(main())


def test_stop_saat_kartu_terbuka_menghentikan_agen_dan_tidak_mengirim_jawaban():
    async def main():
        fake = FakeHermes(wait_forever=True)
        stops, state = [], {"cancelled": False, "asked": asyncio.Event()}

        async def waiting(req):
            state["asked"].set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                state["cancelled"] = True
                raise

        async def fake_stop(run_id, headers):
            stops.append(run_id)

        with patched(APPROVAL_ENABLED=True, _hermes_stop=fake_stop):
            async with fake.client() as c:
                t = asyncio.create_task(server._hermes_stream(c, {}, {}, waiting))
                await asyncio.wait_for(state["asked"].wait(), 5)
                t.cancel()
                selesai, _ = await asyncio.wait({t}, timeout=3)   # asyncio.wait tidak menelan pembatalan dan tidak melempar saat timeout
                assert selesai, "_hermes_stream tidak selesai dalam 3 dtk setelah dibatalkan (kartu izin tidak ikut ditutup?)"
        assert stops == ["chatcmpl-1"], stops          # Hermes diberi tahu berhenti
        assert state["cancelled"], "kartu harus ikut dibatalkan"
        assert fake.posts == [], "Stop tidak boleh berujung jawaban izin"
    run(main())


# ----------------------------------------------------------------------------
# ApprovalHub
# ----------------------------------------------------------------------------
class FakeWS:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    async def send_json(self, payload):
        if self.fail:
            raise RuntimeError("putus")
        self.sent.append(payload)

    def of(self, typ):
        return [m for m in self.sent if m["type"] == typ]


def _req(**kw):
    return {**server.parse_approval_event(APPROVAL), **kw}


def test_hub_kartu_dan_jawaban_once():
    async def main():
        ws = FakeWS()
        hub = server.ApprovalHub(ws)
        req = _req()
        t = asyncio.create_task(hub(req))
        await asyncio.sleep(0.05)
        card = ws.of("approval")[0]
        assert card["id"].startswith("ap-") and card["choices"] == ["once", "deny"]   # tanpa session/always
        assert card["command"] == "rm -rf /mnt/z/tes/folder-uji" and card["ttl"] == int(server.APPROVAL_TTL)
        assert "r1" not in json.dumps(card) and "chatcmpl" not in json.dumps(card), "id Hermes tidak boleh bocor ke overlay"
        assert hub.resolve(card["id"], "once") is True
        assert await asyncio.wait_for(t, 2) == "once"
        await hub.finish(req, True)   # v69: kartu ditutup sesudah POST ke Hermes
        assert ws.of("approval_end")[0] == {"type": "approval_end", "id": card["id"], "state": "approved"}
        assert hub.pending == {}
    run(main())


def test_hub_pilihan_selain_once_menjadi_tolak_dan_sekali_pakai():
    async def main():
        for choice in ("deny", "always", "session", "", None):
            ws = FakeWS()
            hub = server.ApprovalHub(ws)
            t = asyncio.create_task(hub(_req()))
            await asyncio.sleep(0.02)
            cid = ws.of("approval")[0]["id"]
            assert hub.resolve("ap-salah", "once") is False   # id asing ditolak
            assert hub.resolve(cid, choice) is True
            assert hub.resolve(cid, "once") is False           # sekali pakai
            assert await asyncio.wait_for(t, 2) == "deny", choice
    run(main())


def test_hub_kedaluwarsa_menolak():
    async def main():
        ws = FakeWS()
        with patched(APPROVAL_TTL=0.05):
            out = await server.ApprovalHub(ws)(_req())
        assert out == "deny" and ws.of("approval_end")[0]["state"] == "expired"
    run(main())


def test_hub_dibatalkan_menutup_kartu():
    async def main():
        ws = FakeWS()
        hub = server.ApprovalHub(ws)
        t = asyncio.create_task(hub(_req()))
        await asyncio.sleep(0.02)
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        assert ws.of("approval_end")[0]["state"] == "cancelled" and hub.pending == {}
    run(main())


def test_hub_koneksi_putus_menolak_tanpa_menunggu():
    async def main():
        out = await asyncio.wait_for(server.ApprovalHub(FakeWS(fail=True))(_req()), 2)
        assert out == "deny"
    run(main())


def test_hub_hanya_tolak_kalau_hermes_tidak_menawarkan_once():
    async def main():
        ws = FakeWS()
        hub = server.ApprovalHub(ws)
        t = asyncio.create_task(hub(_req(can_once=False)))
        await asyncio.sleep(0.02)
        assert ws.of("approval")[0]["choices"] == ["deny"]
        t.cancel()
        await asyncio.gather(t, return_exceptions=True)
    run(main())


def test_hub_perintah_panjang_dipotong():
    async def main():
        ws = FakeWS()
        hub = server.ApprovalHub(ws)
        t = asyncio.create_task(hub(_req(command="x" * 5000)))
        await asyncio.sleep(0.02)
        assert len(ws.of("approval")[0]["command"]) <= server.APPROVAL_CMD_MAX + 1
        t.cancel()
        await asyncio.gather(t, return_exceptions=True)
    run(main())


# ----------------------------------------------------------------------------
# Ujung ke ujung lewat /ws sungguhan (TestClient): memastikan kabel ws_endpoint benar
# ----------------------------------------------------------------------------
def _e2e(choice):
    from fastapi.testclient import TestClient

    async def fake_ask(client, task, context="", prev_note="", approver=None):
        req = server.parse_approval_event(dict(APPROVAL, command="rm -rf /mnt/z/tes-injeksi/folder-uji"))
        c = await approver(req)
        await approver.finish(req, True)   # v69: seperti _handle_approval
        return "SELESAI-" + c

    async def noop(*a, **k):
        return ""

    async def fake_user_text(ws, client, history, text, **k):
        await server.safe_send(ws, {"type": "done", "interrupted": False})

    async def fake_health():
        return {"voicevox": "0.25", "ninerouter": "HTTP 200", "hermes": "HTTP 200"}

    got, results = [], {}
    with patched(ask_hermes=fake_ask, process_line=noop, handle_user_text=fake_user_text, health_probe=fake_health,
                 HISTORY_ON=False, APPROVAL_ENABLED=True, COMPANION_TOKEN=""):
        with TestClient(server.app).websocket_connect("/ws") as ws:
            ws.send_json({"type": "user", "text": "/agen buat catatan kecil"})   # tanpa kata pemicu v34
            card = None
            while card is None:
                m = ws.receive_json()
                got.append(m)
                if m["type"] == "approval":
                    card = m
            assert card["choices"] == ["once", "deny"] and card["id"].startswith("ap-")
            ws.send_json({"type": "approval", "id": card["id"], "choice": choice})
            while True:
                m = ws.receive_json()
                got.append(m)
                if m["type"] == "approval_end":
                    results["end"] = m
                if m["type"] == "status" and not m.get("busy"):
                    results["status"] = m
                    break
            # jawaban kedua untuk id yang sama harus ditolak sebagai kedaluwarsa
            ws.send_json({"type": "approval", "id": card["id"], "choice": "once"})
            while True:
                m = ws.receive_json()
                if m["type"] == "approval_end" and m is not results["end"]:
                    results["second"] = m
                    break
    return card, results


def test_ujung_ke_ujung_izinkan_sekali():
    card, res = in_thread(_e2e, "once")
    assert res["end"]["state"] == "approved" and res["end"]["id"] == card["id"]
    assert res["status"]["state"] == "done"
    assert res["second"]["state"] == "expired"


def test_ujung_ke_ujung_tolak():
    card, res = in_thread(_e2e, "deny")
    assert res["end"]["state"] == "denied"


def test_ujung_ke_ujung_always_dari_klien_diperlakukan_tolak():
    card, res = in_thread(_e2e, "always")
    assert res["end"]["state"] == "denied", res


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    lulus = 0
    for name, fn in tests:
        try:
            fn()
            lulus += 1
            print(f"  lulus   {name}")
        except Exception:
            print(f"  GAGAL   {name}")
            traceback.print_exc()
    print(f"\n{lulus} dari {len(tests)} tes lulus")
    sys.exit(0 if lulus == len(tests) else 1)
