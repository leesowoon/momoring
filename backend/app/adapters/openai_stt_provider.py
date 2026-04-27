import base64

import httpx

from .base import STTProvider


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
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            "file": ("chunk.wav", audio_bytes, "audio/wav"),
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
