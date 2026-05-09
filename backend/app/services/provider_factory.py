from dataclasses import dataclass

from ..adapters.base import LLMProvider, STTProvider, TTSProvider
from ..adapters.claude_provider import ClaudeLLMProvider
from ..adapters.mock import MockClaudeProvider, MockGPTProvider, MockSTTProvider, MockTTSProvider
from ..adapters.openai_provider import OpenAILLMProvider
from ..adapters.openai_stt_provider import OpenAISTTProvider
from ..adapters.openai_tts_provider import OpenAITTSProvider
from .resilience import (
    CircuitBreaker,
    ResiliencePolicy,
    ResilientLLMProvider,
    ResilientSTTProvider,
    ResilientTTSProvider,
)


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

    llm_timeout_s: float = 6.0
    stt_timeout_s: float = 4.0
    tts_timeout_s: float = 4.0
    max_attempts: int = 2


def _llm_policy(name: str, cfg: ProviderFactoryConfig) -> ResiliencePolicy:
    return ResiliencePolicy(
        timeout_s=cfg.llm_timeout_s,
        max_attempts=cfg.max_attempts,
        breaker=CircuitBreaker(name=name),
    )


def _stt_policy(cfg: ProviderFactoryConfig) -> ResiliencePolicy:
    return ResiliencePolicy(
        timeout_s=cfg.stt_timeout_s,
        max_attempts=cfg.max_attempts,
        breaker=CircuitBreaker(name="stt"),
    )


def _tts_policy(cfg: ProviderFactoryConfig) -> ResiliencePolicy:
    return ResiliencePolicy(
        timeout_s=cfg.tts_timeout_s,
        max_attempts=cfg.max_attempts,
        breaker=CircuitBreaker(name="tts"),
    )


class ProviderFactory:
    @staticmethod
    def build_primary_llm(cfg: ProviderFactoryConfig) -> LLMProvider:
        inner: LLMProvider
        if cfg.use_real_providers and cfg.openai_api_key:
            inner = OpenAILLMProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_model,
                base_url=cfg.openai_base_url,
            )
        else:
            inner = MockGPTProvider()
        return ResilientLLMProvider(inner, _llm_policy("llm_primary", cfg))

    @staticmethod
    def build_fallback_llm(cfg: ProviderFactoryConfig) -> LLMProvider:
        inner: LLMProvider
        if cfg.use_real_providers and cfg.anthropic_api_key:
            inner = ClaudeLLMProvider(
                api_key=cfg.anthropic_api_key,
                model=cfg.anthropic_model,
                base_url=cfg.anthropic_base_url,
            )
        else:
            inner = MockClaudeProvider()
        return ResilientLLMProvider(inner, _llm_policy("llm_fallback", cfg))

    @staticmethod
    def build_stt(cfg: ProviderFactoryConfig) -> STTProvider:
        inner: STTProvider
        if cfg.use_real_stt and cfg.openai_api_key:
            inner = OpenAISTTProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_stt_model,
                base_url=cfg.openai_base_url,
            )
        else:
            inner = MockSTTProvider()
        return ResilientSTTProvider(inner, _stt_policy(cfg))

    @staticmethod
    def build_tts(cfg: ProviderFactoryConfig) -> TTSProvider:
        inner: TTSProvider
        if cfg.use_real_tts and cfg.openai_api_key:
            inner = OpenAITTSProvider(
                api_key=cfg.openai_api_key,
                model=cfg.openai_tts_model,
                voice=cfg.openai_tts_voice,
                output_dir=cfg.audio_output_dir,
                base_url=cfg.openai_base_url,
            )
        else:
            inner = MockTTSProvider()
        return ResilientTTSProvider(inner, _tts_policy(cfg))
