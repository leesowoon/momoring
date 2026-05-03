from dataclasses import dataclass

from ..adapters.base import LLMMessage, LLMProvider


@dataclass
class LLMRouter:
    primary_name: str
    fallback_name: str
    primary: LLMProvider
    fallback: LLMProvider
    force_fallback: bool = False

    async def generate(self, messages: list[LLMMessage]) -> str:
        if self.force_fallback:
            return await self.fallback.generate(messages)

        try:
            return await self.primary.generate(messages)
        except Exception:
            return await self.fallback.generate(messages)

    def active_model_label(self) -> str:
        if self.force_fallback:
            return self.fallback_name
        return self.primary_name
