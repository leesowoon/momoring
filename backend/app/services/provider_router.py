from dataclasses import dataclass
from ..adapters.base import LLMProvider


@dataclass
class LLMRouter:
    primary_name: str
    fallback_name: str
    primary: LLMProvider
    fallback: LLMProvider
    force_fallback: bool = False

    async def generate(self, user_text: str) -> str:
        if self.force_fallback:
            return await self.fallback.generate(user_text)

        try:
            return await self.primary.generate(user_text)
        except Exception:
            return await self.fallback.generate(user_text)

    def active_model_label(self) -> str:
        if self.force_fallback:
            return self.fallback_name
        return self.primary_name
