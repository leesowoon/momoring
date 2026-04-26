from app.adapters.mock import MockClaudeProvider, MockGPTProvider, MockSTTProvider, MockTTSProvider
from app.adapters.openai_stt_provider import OpenAISTTProvider
from app.adapters.openai_tts_provider import OpenAITTSProvider
from app.services.provider_factory import ProviderFactory, ProviderFactoryConfig


def _cfg(**overrides: object) -> ProviderFactoryConfig:
    base = dict(
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


def test_factory_returns_mock_when_real_disabled() -> None:
    cfg = _cfg()

    assert isinstance(ProviderFactory.build_primary_llm(cfg), MockGPTProvider)
    assert isinstance(ProviderFactory.build_fallback_llm(cfg), MockClaudeProvider)
    assert isinstance(ProviderFactory.build_stt(cfg), MockSTTProvider)
    assert isinstance(ProviderFactory.build_tts(cfg), MockTTSProvider)


def test_factory_returns_real_stt_when_enabled_and_configured() -> None:
    cfg = _cfg(use_real_stt=True, openai_api_key="key")
    provider = ProviderFactory.build_stt(cfg)
    assert isinstance(provider, OpenAISTTProvider)


def test_factory_returns_real_tts_when_enabled_and_configured(tmp_path) -> None:
    cfg = _cfg(use_real_tts=True, openai_api_key="key", audio_output_dir=str(tmp_path))
    provider = ProviderFactory.build_tts(cfg)
    assert isinstance(provider, OpenAITTSProvider)
