"""Timeout, retry, and circuit-breaker wrappers for adapters.

Per mvp_technical_design.md sec 11.2:
- timeout: STT 4s / LLM 6s / TTS 4s (initial values)
- retry: idempotent requests, max 2 attempts, exponential backoff
- circuit breaker: provider-level failure threshold opens for 60s
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from time import perf_counter

from ..adapters.base import LLMMessage, LLMProvider, STTProvider, TTSProvider

logger = logging.getLogger("momoring.resilience")


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    """Simple consecutive-failure breaker. Opens after `failure_threshold`
    consecutive failures, stays open for `cooldown_seconds`, then half-opens
    on next call (which is allowed through; success closes, failure re-opens).
    """

    name: str
    failure_threshold: int = 5
    cooldown_seconds: float = 60.0
    failures: int = 0
    opened_at: float | None = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if perf_counter() - self.opened_at >= self.cooldown_seconds:
            self.opened_at = None
            self.failures = 0
            return False
        return True

    def record_success(self) -> None:
        if self.failures or self.opened_at:
            logger.info("circuit closed: %s", self.name)
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold and self.opened_at is None:
            self.opened_at = perf_counter()
            logger.warning(
                "circuit opened: %s (failures=%d, cooldown=%.1fs)",
                self.name,
                self.failures,
                self.cooldown_seconds,
            )


@dataclass
class ResiliencePolicy:
    timeout_s: float
    max_attempts: int = 2
    base_backoff_s: float = 0.2
    breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker(name="default"))


async def _run(policy: ResiliencePolicy, fn, *args, **kwargs):
    if policy.breaker.is_open():
        raise CircuitOpenError(f"circuit_open:{policy.breaker.name}")

    last_err: BaseException | None = None
    for attempt in range(policy.max_attempts):
        try:
            result = await asyncio.wait_for(fn(*args, **kwargs), timeout=policy.timeout_s)
            policy.breaker.record_success()
            return result
        except asyncio.TimeoutError as err:
            last_err = err
            logger.warning(
                "timeout %s attempt=%d/%d timeout_s=%.1f",
                policy.breaker.name,
                attempt + 1,
                policy.max_attempts,
                policy.timeout_s,
            )
        except Exception as err:
            last_err = err
            logger.warning(
                "provider_error %s attempt=%d/%d err=%r",
                policy.breaker.name,
                attempt + 1,
                policy.max_attempts,
                err,
            )

        if attempt + 1 < policy.max_attempts:
            await asyncio.sleep(policy.base_backoff_s * 2**attempt)

    policy.breaker.record_failure()
    assert last_err is not None
    raise last_err


class ResilientLLMProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, policy: ResiliencePolicy) -> None:
        self.inner = inner
        self.policy = policy

    async def generate(self, messages: list[LLMMessage]) -> str:
        return await _run(self.policy, self.inner.generate, messages)


class ResilientSTTProvider(STTProvider):
    def __init__(self, inner: STTProvider, policy: ResiliencePolicy) -> None:
        self.inner = inner
        self.policy = policy

    async def transcribe_chunk(self, chunk_base64: str) -> str:
        return await _run(self.policy, self.inner.transcribe_chunk, chunk_base64)


class ResilientTTSProvider(TTSProvider):
    def __init__(self, inner: TTSProvider, policy: ResiliencePolicy) -> None:
        self.inner = inner
        self.policy = policy

    async def synthesize(self, session_id: str, text: str) -> str:
        return await _run(self.policy, self.inner.synthesize, session_id, text)
