import asyncio

import pytest

from app.adapters.base import LLMMessage, LLMProvider
from app.services.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    ResiliencePolicy,
    ResilientLLMProvider,
)


class _CountingLLM(LLMProvider):
    def __init__(self, behaviors: list[str | Exception]) -> None:
        self.behaviors = list(behaviors)
        self.calls = 0

    async def generate(self, messages: list[LLMMessage]) -> str:
        self.calls += 1
        b = self.behaviors.pop(0)
        if isinstance(b, Exception):
            raise b
        if b == "timeout":
            await asyncio.sleep(10)
            return "should not reach"
        return b


def _policy(timeout_s: float = 0.05, max_attempts: int = 2, name: str = "test") -> ResiliencePolicy:
    return ResiliencePolicy(
        timeout_s=timeout_s,
        max_attempts=max_attempts,
        base_backoff_s=0.0,
        breaker=CircuitBreaker(name=name, failure_threshold=3),
    )


def test_passes_through_on_success() -> None:
    inner = _CountingLLM(["hi"])
    provider = ResilientLLMProvider(inner, _policy())
    assert asyncio.run(provider.generate([])) == "hi"
    assert inner.calls == 1


def test_retries_once_on_exception_then_succeeds() -> None:
    inner = _CountingLLM([RuntimeError("boom"), "ok"])
    provider = ResilientLLMProvider(inner, _policy())
    assert asyncio.run(provider.generate([])) == "ok"
    assert inner.calls == 2


def test_raises_after_max_attempts_exhausted() -> None:
    inner = _CountingLLM([RuntimeError("boom1"), RuntimeError("boom2")])
    provider = ResilientLLMProvider(inner, _policy(max_attempts=2))
    with pytest.raises(RuntimeError, match="boom2"):
        asyncio.run(provider.generate([]))
    assert inner.calls == 2


def test_timeout_is_treated_as_failure() -> None:
    inner = _CountingLLM(["timeout", "timeout"])
    provider = ResilientLLMProvider(inner, _policy(timeout_s=0.02, max_attempts=2))
    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(provider.generate([]))
    assert inner.calls == 2


def test_circuit_opens_after_threshold_consecutive_failures() -> None:
    breaker = CircuitBreaker(name="t", failure_threshold=3, cooldown_seconds=60.0)
    policy = ResiliencePolicy(timeout_s=0.05, max_attempts=1, base_backoff_s=0.0, breaker=breaker)
    inner = _CountingLLM([RuntimeError("e")] * 5)
    provider = ResilientLLMProvider(inner, policy)

    for _ in range(3):
        with pytest.raises(RuntimeError):
            asyncio.run(provider.generate([]))

    assert breaker.is_open()

    with pytest.raises(CircuitOpenError):
        asyncio.run(provider.generate([]))


def test_success_resets_failure_counter() -> None:
    breaker = CircuitBreaker(name="t", failure_threshold=3, cooldown_seconds=60.0)
    policy = ResiliencePolicy(timeout_s=0.05, max_attempts=1, base_backoff_s=0.0, breaker=breaker)
    inner = _CountingLLM([RuntimeError("e"), RuntimeError("e"), "ok"])
    provider = ResilientLLMProvider(inner, policy)

    for _ in range(2):
        with pytest.raises(RuntimeError):
            asyncio.run(provider.generate([]))

    assert breaker.failures == 2
    asyncio.run(provider.generate([]))
    assert breaker.failures == 0


def test_router_falls_back_when_primary_circuit_opens() -> None:
    """End-to-end: primary fails enough to open circuit, router falls back."""
    from app.adapters.mock import MockClaudeProvider
    from app.services.provider_router import LLMRouter

    breaker = CircuitBreaker(name="primary", failure_threshold=2, cooldown_seconds=60.0)
    primary_policy = ResiliencePolicy(
        timeout_s=0.05, max_attempts=1, base_backoff_s=0.0, breaker=breaker
    )
    primary_inner = _CountingLLM([RuntimeError("e")] * 10)
    primary = ResilientLLMProvider(primary_inner, primary_policy)

    router = LLMRouter(
        primary_name="primary",
        fallback_name="claude",
        primary=primary,
        fallback=MockClaudeProvider(),
    )

    # First two calls trip the breaker; router falls back to Claude each time.
    for _ in range(3):
        result = asyncio.run(router.generate([LLMMessage(role="user", content="hi")]))
        assert result.startswith("[Claude]")

    assert breaker.is_open()
