from uuid import uuid4

from .base import LLMMessage, LLMProvider, STTProvider, TTSProvider


def _last_user_text(messages: list[LLMMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return ""


class MockSTTProvider(STTProvider):
    async def transcribe_chunk(self, chunk_base64: str) -> str:
        if chunk_base64:
            return "듣는 중..."
        return ""


class MockGPTProvider(LLMProvider):
    async def generate(self, messages: list[LLMMessage]) -> str:
        return f"[GPT] 모모링: {_last_user_text(messages)}에 대해 같이 알아보자!"


class MockClaudeProvider(LLMProvider):
    async def generate(self, messages: list[LLMMessage]) -> str:
        return f"[Claude] 모모링: {_last_user_text(messages)}를 차근차근 설명해줄게!"


class MockTTSProvider(TTSProvider):
    async def synthesize(self, session_id: str, text: str) -> str:
        _ = text
        return f"/audio/{session_id}/{uuid4()}.mp3"
