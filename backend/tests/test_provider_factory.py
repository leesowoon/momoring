from app.adapters.mock import MockClaudeProvider, MockGPTProvider
from app.services.provider_factory import ProviderFactory, ProviderFactoryConfig


def test_factory_returns_mock_when_real_disabled() -> None:
    cfg = ProviderFactoryConfig(
        use_real_providers=False,
        openai_api_key=None,
        anthropic_api_key=None,
        openai_model="gpt-5.4",
        anthropic_model="claude-sonnet-4",
        openai_base_url="https://api.openai.com/v1",
        anthropic_base_url="https://api.anthropic.com/v1",
    )

    primary = ProviderFactory.build_primary_llm(cfg)
    fallback = ProviderFactory.build_fallback_llm(cfg)

    assert isinstance(primary, MockGPTProvider)
    assert isinstance(fallback, MockClaudeProvider)
