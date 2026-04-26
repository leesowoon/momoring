import httpx
from .base import LLMProvider


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(self, user_text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": [{"role": "user", "content": user_text}],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(f"{self.base_url}/responses", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        # Responses API output normalization (best-effort)
        if "output_text" in data and data["output_text"]:
            return data["output_text"]

        output = data.get("output", [])
        if output and isinstance(output, list):
            first = output[0]
            content = first.get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text")
                if text:
                    return text

        return "모모링: 지금은 간단히 설명해줄게!"
