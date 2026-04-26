import asyncio
from app.adapters.mock import MockClaudeProvider, MockGPTProvider
from app.services.provider_router import LLMRouter


def test_router_primary() -> None:
    router = LLMRouter(
        primary_name="gpt-5.4",
        fallback_name="claude",
        primary=MockGPTProvider(),
        fallback=MockClaudeProvider(),
    )
    text = asyncio.run(router.generate("안녕"))
    assert text.startswith("[GPT]")


def test_router_force_fallback() -> None:
    router = LLMRouter(
        primary_name="gpt-5.4",
        fallback_name="claude",
        primary=MockGPTProvider(),
        fallback=MockClaudeProvider(),
        force_fallback=True,
    )
    text = asyncio.run(router.generate("안녕"))
    assert text.startswith("[Claude]")
