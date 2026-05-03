from dataclasses import dataclass
from time import perf_counter

from ..adapters.base import LLMProvider, TTSProvider
from .prompt_builder import PromptBuilder
from .safety import SafetyCategory, SafetyService
from .session_store import Turn


@dataclass
class OrchestratedResponse:
    text: str
    blocked: bool
    llm_ms: int = 0
    block_source: str | None = None
    block_category: SafetyCategory | None = None


class STSOrchestrator:
    def __init__(
        self,
        llm: LLMProvider,
        tts: TTSProvider,
        safety: SafetyService,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.llm = llm
        self._tts_provider = tts
        self.safety = safety
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def respond(
        self,
        user_text: str,
        *,
        age_group: str | None = None,
        history: list[Turn] | None = None,
    ) -> OrchestratedResponse:
        check = self.safety.check(user_text)
        if not check.safe:
            return OrchestratedResponse(
                text=self.safety.safe_fallback_response(check.category),
                blocked=True,
                block_source="input",
                block_category=check.category,
            )

        messages = self.prompt_builder.build(
            user_text=user_text,
            age_group=age_group,
            history=history,
        )

        llm_start = perf_counter()
        text = await self.llm.generate(messages)
        llm_ms = int((perf_counter() - llm_start) * 1000)

        output_check = self.safety.check(text)
        if not output_check.safe:
            return OrchestratedResponse(
                text=self.safety.safe_fallback_response(output_check.category),
                blocked=True,
                llm_ms=llm_ms,
                block_source="output",
                block_category=output_check.category,
            )

        return OrchestratedResponse(text=text, blocked=False, llm_ms=llm_ms)

    async def tts(self, session_id: str, text: str) -> str:
        return await self._tts_provider.synthesize(session_id, text)
