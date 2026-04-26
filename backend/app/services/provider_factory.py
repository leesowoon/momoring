from dataclasses import dataclass

from ..adapters.base import LLMProvider, STTProvider, TTSProvider
from ..adapters.claude_provider import ClaudeLLMProvider
from ..adapters.mock import MockClaudeProvider, MockGPTProvider, MockSTTProvider, MockTTSProvider
from ..adapters.openai_provider import OpenAILLMProvider
from ..adapters.openai_stt_provider import OpenAISTTProvider
from ..adapters.openai_tts_provider import OpenAITTSProvider


@dataclass(frozen=True)
class ProviderFactoryConfig:
    use_real_providers: bool
    openai_api_key: str | None
    anthropic_api_key: str | None
    openai_model: str
    anthropic_model: str
    openai_base_url: str
    anthropic_base_url: str

    use_real_stt: bool
    openai_stt_model: str

    use_real_tts: bool
    openai_tts_model: str
    openai_tts_voice: str
    audio_output_dir: str


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

    @staticmethod
    def build_stt(cfg: ProviderFactoryConfig) -> STTProvider:
        if cfg.use_real_stt and cfg.openai_api_key:
            return OpenAISTTProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_stt_model,
                base_url=cfg.openai_base_url,
            )
        return MockSTTProvider()

    @staticmethod
    def build_tts(cfg: ProviderFactoryConfig) -> TTSProvider:
        if cfg.use_real_tts and cfg.openai_api_key:
            return OpenAITTSProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_tts_model,
                voice=cfg.openai_tts_voice,
                output_dir=cfg.audio_output_dir,
                base_url=cfg.openai_base_url,
            )
        return MockTTSProvider()
