from pathlib import Path
from uuid import uuid4

import httpx

from .base import TTSProvider


class OpenAITTSProvider(TTSProvider):
    def __init__(
        self,
        api_key: str,
        model: str,
        voice: str,
        output_dir: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.voice = voice
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, session_id: str, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "response_format": "mp3",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            res = await client.post(
                f"{self.base_url}/audio/speech",
                headers=headers,
                json=payload,
            )
            res.raise_for_status()

        filename = f"{session_id}_{uuid4()}.mp3"
        file_path = self.output_dir / filename
        file_path.write_bytes(res.content)
        return f"/audio/{filename}"
