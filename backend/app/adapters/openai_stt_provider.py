import base64

import httpx

from .base import STTProvider


def _detect_audio_format(audio_bytes: bytes) -> tuple[str, str]:
    """Return (filename, content_type) inferred from magic bytes.

    Whisper accepts webm / mp3 / wav / m4a / ogg / flac. Default to webm
    (browser MediaRecorder output) when magic doesn't match anything.
    """
    head = audio_bytes[:12] if len(audio_bytes) >= 12 else audio_bytes
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return ("utterance.webm", "audio/webm")
    if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] in (0xFA, 0xFB, 0xF2, 0xF3)):
        return ("utterance.mp3", "audio/mpeg")
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return ("utterance.wav", "audio/wav")
    if head[:4] == b"OggS":
        return ("utterance.ogg", "audio/ogg")
    if head[4:8] == b"ftyp":
        return ("utterance.m4a", "audio/mp4")
    if head[:4] == b"fLaC":
        return ("utterance.flac", "audio/flac")
    return ("utterance.webm", "audio/webm")


class OpenAISTTProvider(STTProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def transcribe_chunk(self, chunk_base64: str) -> str:
        if not chunk_base64:
            return ""

        audio_bytes = base64.b64decode(chunk_base64)
        filename, content_type = _detect_audio_format(audio_bytes)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            "file": (filename, audio_bytes, content_type),
            "model": (None, self.model),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            res = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers=headers,
                files=files,
            )
            res.raise_for_status()
            data = res.json()

        return data.get("text", "")
