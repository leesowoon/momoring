from dataclasses import dataclass
from ..adapters.base import LLMProvider
from ..adapters.mock import MockClaudeProvider, MockGPTProvider
from ..adapters.openai_provider import OpenAILLMProvider
from ..adapters.claude_provider import ClaudeLLMProvider


@dataclass(frozen=True)
class ProviderFactoryConfig:
    use_real_providers: bool
    openai_api_key: str | None
    anthropic_api_key: str | None
    openai_model: str
    anthropic_model: str
    openai_base_url: str
    anthropic_base_url: str


class ProviderFactory:
    @staticmethod
    def build_primary_llm(cfg: ProviderFactoryConfig) -> LLMProvider:
        if cfg.use_real_providers and cfg.openai_api_key:
            return OpenAILLMProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_model,
                base_url=cfg.openai_base_url,
            )
        return MockGPTProvider()

    @staticmethod
    def build_fallback_llm(cfg: ProviderFactoryConfig) -> LLMProvider:
        if cfg.use_real_providers and cfg.anthropic_api_key:
            return ClaudeLLMProvider(
                api_key=cfg.anthropic_api_key,
                model=cfg.anthropic_model,
                base_url=cfg.anthropic_base_url,
            )
        return MockClaudeProvider()
