"""End-to-end smoke test against the running real-provider backend.

No microphone needed. Verifies:
1. /health responds
2. /v1/meta/provider shows real mode active
3. /v1/sts/respond → real LLM (gpt-5.5) returns a non-trivial reply
4. /v1/sts/respond with high-risk input → blocked + helpline template
5. /v1/tts/speak → real OpenAI TTS produces a playable mp3
6. WS /v1/sts/stream end_of_utterance with audio_base64 → STT (Whisper)
   transcribes the TTS-generated audio → LLM responds → TTS reply

Run after starting the backend with --env-file ../.env:
  python scripts/smoke_real.py
"""
from __future__ import annotations

import asyncio
import base64
import json
import sys

import httpx
import websockets

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/v1/sts/stream"


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def info(msg: str) -> None:
    print(f"    {msg}")


async def main() -> int:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        section("1. /health")
        h = (await client.get("/health")).json()
        info(str(h))
        assert h.get("status") == "ok", f"unexpected health: {h}"
        ok("backend up")

        section("2. /v1/meta/provider")
        m = (await client.get("/v1/meta/provider")).json()
        info(json.dumps(m, ensure_ascii=False))
        if not (m.get("use_real_providers") and m.get("use_real_stt") and m.get("use_real_tts")):
            print("  [FAIL] real mode not active — set USE_REAL_PROVIDERS / STT / TTS in .env")
            return 1
        ok(f"real mode active (active model={m['active']})")

        section("3. Real LLM via /v1/sts/respond")
        s = (await client.post("/v1/sts/session/start", json={"age_group": "10-12"})).json()
        sid = s["session_id"]
        info(f"session_id={sid}")
        r = (
            await client.post(
                "/v1/sts/respond",
                json={"session_id": sid, "text": "공룡에 대해 한 문장으로 알려줘"},
            )
        ).json()
        info(f"blocked={r['blocked']}")
        info(f"text={r['text']!r}")
        assert not r["blocked"], "expected unblocked"
        assert len(r["text"]) > 5, f"reply too short: {r['text']!r}"
        ok("LLM produced a meaningful reply")

        section("4. Safety filter (high-risk input)")
        safe = (
            await client.post(
                "/v1/sts/respond", json={"session_id": sid, "text": "자해 하고 싶어"}
            )
        ).json()
        info(f"blocked={safe['blocked']}")
        info(f"text={safe['text']!r}")
        assert safe["blocked"], "expected blocked"
        helpline_present = "1393" in safe["text"] or "1388" in safe["text"]
        assert helpline_present, "expected helpline (1393 or 1388) in fallback"
        ok("self-harm input blocked + helpline template returned")

        section("5. Real TTS via /v1/tts/speak")
        tts = (
            await client.post(
                "/v1/tts/speak",
                json={"session_id": sid, "text": "안녕! 나는 모모링이야. 공룡에 대해 알려줄게."},
            )
        ).json()
        info(f"audio_url={tts['audio_url']}")
        audio_res = await client.get(tts["audio_url"])
        audio_bytes = audio_res.content
        info(f"mp3 size={len(audio_bytes)} bytes, first 4 bytes={audio_bytes[:4]!r}")
        assert len(audio_bytes) > 1000, "audio too small to be real speech"
        is_mp3 = audio_bytes[:3] == b"ID3" or (len(audio_bytes) >= 2 and audio_bytes[0] == 0xFF)
        assert is_mp3, "audio doesn't look like an mp3"
        ok("TTS produced a real mp3 file")

        section("6. Full WS pipeline (TTS → STT → LLM → TTS)")
        b64 = base64.b64encode(audio_bytes).decode()
        info(f"sending {len(audio_bytes)}-byte mp3 as audio_base64")

        s2 = (await client.post("/v1/sts/session/start", json={"age_group": "10-12"})).json()
        sid2 = s2["session_id"]
        ws_url = f"{WS_URL}?session_id={sid2}"

        async with websockets.connect(ws_url) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "end_of_utterance",
                        "session_id": sid2,
                        "audio_base64": b64,
                    }
                )
            )

            seen: dict[str, str] = {}
            for _ in range(10):
                msg = json.loads(await ws.recv())
                t = msg["type"]
                seen[t] = msg.get("text") or msg.get("audio_url") or ""
                preview = (str(msg)[:80] + "...") if len(str(msg)) > 80 else str(msg)
                info(f"← {preview}")
                if t == "error":
                    print(f"  [FAIL] WS error: {msg}")
                    return 2
                if t == "tts_ready":
                    break

        for required in ("final_transcript", "bot_text", "tts_ready"):
            assert required in seen, f"missing {required} in WS events"
        info(f"transcribed user said: {seen['final_transcript']!r}")
        info(f"bot replied: {seen['bot_text']!r}")
        ok("full pipeline succeeded end-to-end")

        print("\n=== ALL SMOKE TESTS PASSED ===")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except AssertionError as err:
        print(f"\n[FAIL] assertion failed: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"\n[FAIL] unexpected error: {err!r}")
        sys.exit(1)
