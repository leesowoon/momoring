import httpx

from .base import LLMMessage, LLMProvider


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(self, messages: list[LLMMessage]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": [{"role": m.role, "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(f"{self.base_url}/responses", headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()

        text = _extract_text(data)
        if text:
            return text

        return "모모링: 지금은 간단히 설명해줄게!"


def _extract_text(data: dict) -> str | None:
    """Walk a Responses API payload looking for the assistant's text.

    GPT-5 family responses can include a leading reasoning item before the
    actual message item, so we can't rely on output[0]. Iterate every
    item, skip non-message types, then pull the first text content.
    """
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text

    output = data.get("output")
    if not isinstance(output, list):
        return None

    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            text = c.get("text")
            if isinstance(text, str) and text:
                return text

    return None
