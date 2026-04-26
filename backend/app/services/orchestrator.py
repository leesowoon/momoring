from dataclasses import dataclass
from ..adapters.base import LLMProvider, TTSProvider
from .safety import SafetyService


@dataclass
class OrchestratedResponse:
    text: str
    blocked: bool


class STSOrchestrator:
    def __init__(self, llm: LLMProvider, tts: TTSProvider, safety: SafetyService) -> None:
        self.llm = llm
        self._tts_provider = tts
        self.safety = safety

    async def respond(self, user_text: str) -> OrchestratedResponse:
        check = self.safety.check(user_text)
        if not check.safe:
            return OrchestratedResponse(text=self.safety.safe_fallback_response(), blocked=True)

        text = await self.llm.generate(user_text)

        output_check = self.safety.check(text)
        if not output_check.safe:
            return OrchestratedResponse(text=self.safety.safe_fallback_response(), blocked=True)

        return OrchestratedResponse(text=text, blocked=False)

    async def tts(self, session_id: str, text: str) -> str:
        return await self._tts_provider.synthesize(session_id, text)
