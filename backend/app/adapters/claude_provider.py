import httpx
from .base import LLMProvider


class ClaudeLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(self, user_text: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 200,
            "messages": [{"role": "user", "content": user_text}],
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(f"{self.base_url}/messages", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        content = data.get("content", [])
        if content and isinstance(content, list):
            text = content[0].get("text")
            if text:
                return text

        return "모모링: 천천히 함께 이해해보자!"
