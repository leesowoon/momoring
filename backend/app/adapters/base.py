from dataclasses import dataclass
from typing import Literal, Protocol


MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: MessageRole
    content: str


class STTProvider(Protocol):
    async def transcribe_chunk(self, chunk_base64: str) -> str: ...


class LLMProvider(Protocol):
    async def generate(self, messages: list[LLMMessage]) -> str: ...


class TTSProvider(Protocol):
    async def synthesize(self, session_id: str, text: str) -> str: ...
