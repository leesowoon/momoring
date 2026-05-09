from app.adapters.mock import MockClaudeProvider, MockGPTProvider, MockSTTProvider, MockTTSProvider
from app.adapters.openai_stt_provider import OpenAISTTProvider
from app.adapters.openai_tts_provider import OpenAITTSProvider
from app.services.provider_factory import ProviderFactory, ProviderFactoryConfig
from app.services.resilience import (
    ResilientLLMProvider,
    ResilientSTTProvider,
    ResilientTTSProvider,
)


def _cfg(**overrides: object) -> ProviderFactoryConfig:
    base: dict[str, object] = dict(
        use_real_providers=False,
        openai_api_key=None,
        anthropic_api_key=None,
        openai_model="gpt-5.4",
        anthropic_model="claude-sonnet-4",
        openai_base_url="https://api.openai.com/v1",
        anthropic_base_url="https://api.anthropic.com/v1",
        use_real_stt=False,
        openai_stt_model="whisper-1",
        use_real_tts=False,
        openai_tts_model="gpt-4o-mini-tts",
        openai_tts_voice="alloy",
        audio_output_dir=".data/audio",
    )
    base.update(overrides)
    return ProviderFactoryConfig(**base)


def test_factory_wraps_mocks_in_resilience_layer_when_real_disabled() -> None:
    cfg = _cfg()

    primary = ProviderFactory.build_primary_llm(cfg)
    fallback = ProviderFactory.build_fallback_llm(cfg)
    stt = ProviderFactory.build_stt(cfg)
    tts = ProviderFactory.build_tts(cfg)

    assert isinstance(primary, ResilientLLMProvider)
    assert isinstance(primary.inner, MockGPTProvider)
    assert isinstance(fallback, ResilientLLMProvider)
    assert isinstance(fallback.inner, MockClaudeProvider)
    assert isinstance(stt, ResilientSTTProvider)
    assert isinstance(stt.inner, MockSTTProvider)
    assert isinstance(tts, ResilientTTSProvider)
    assert isinstance(tts.inner, MockTTSProvider)


def test_factory_returns_real_stt_when_enabled_and_configured() -> None:
    cfg = _cfg(use_real_stt=True, openai_api_key="key")
    provider = ProviderFactory.build_stt(cfg)
    assert isinstance(provider, ResilientSTTProvider)
    assert isinstance(provider.inner, OpenAISTTProvider)


def test_factory_returns_real_tts_when_enabled_and_configured(tmp_path) -> None:
    cfg = _cfg(use_real_tts=True, openai_api_key="key", audio_output_dir=str(tmp_path))
    provider = ProviderFactory.build_tts(cfg)
    assert isinstance(provider, ResilientTTSProvider)
    assert isinstance(provider.inner, OpenAITTSProvider)


def test_factory_applies_configured_timeouts() -> None:
    cfg = _cfg(llm_timeout_s=2.5, stt_timeout_s=1.0, tts_timeout_s=3.0, max_attempts=4)
    primary = ProviderFactory.build_primary_llm(cfg)
    stt = ProviderFactory.build_stt(cfg)
    tts = ProviderFactory.build_tts(cfg)

    assert isinstance(primary, ResilientLLMProvider)
    assert isinstance(stt, ResilientSTTProvider)
    assert isinstance(tts, ResilientTTSProvider)
    assert primary.policy.timeout_s == 2.5
    assert stt.policy.timeout_s == 1.0
    assert tts.policy.timeout_s == 3.0
    assert primary.policy.max_attempts == 4
