from typing import Protocol


class STTProvider(Protocol):
    async def transcribe_chunk(self, chunk_base64: str) -> str: ...


class LLMProvider(Protocol):
    async def generate(self, user_text: str) -> str: ...


class TTSProvider(Protocol):
    async def synthesize(self, session_id: str, text: str) -> str: ...
