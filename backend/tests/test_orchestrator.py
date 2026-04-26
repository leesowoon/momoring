import asyncio

from app.adapters.base import LLMProvider, TTSProvider
from app.services.orchestrator import STSOrchestrator
from app.services.safety import SafetyService


class UnsafeOutputLLM(LLMProvider):
    async def generate(self, user_text: str) -> str:
        _ = user_text
        return "자해를 시도해"  # banned keyword expected by SafetyService


class SafeOutputLLM(LLMProvider):
    async def generate(self, user_text: str) -> str:
        return f"안전한 답변: {user_text}"


class DummyTTS(TTSProvider):
    async def synthesize(self, session_id: str, text: str) -> str:
        _ = session_id, text
        return "/audio/dummy.mp3"


def test_orchestrator_blocks_unsafe_input() -> None:
    orchestrator = STSOrchestrator(llm=SafeOutputLLM(), tts=DummyTTS(), safety=SafetyService())
    result = asyncio.run(orchestrator.respond("자해 하고 싶어"))
    assert result.blocked is True
    assert "안전" in result.text


def test_orchestrator_blocks_unsafe_model_output() -> None:
    orchestrator = STSOrchestrator(llm=UnsafeOutputLLM(), tts=DummyTTS(), safety=SafetyService())
    result = asyncio.run(orchestrator.respond("오늘 날씨 알려줘"))
    assert result.blocked is True
    assert "안전" in result.text


def test_orchestrator_allows_safe_input_and_output() -> None:
    orchestrator = STSOrchestrator(llm=SafeOutputLLM(), tts=DummyTTS(), safety=SafetyService())
    result = asyncio.run(orchestrator.respond("오늘 뭐 배울까?"))
    assert result.blocked is False
    assert "안전한 답변" in result.text


def test_orchestrator_tts_method_uses_provider() -> None:
    orchestrator = STSOrchestrator(llm=SafeOutputLLM(), tts=DummyTTS(), safety=SafetyService())
    audio_url = asyncio.run(orchestrator.tts("session-1", "안녕"))
    assert audio_url == "/audio/dummy.mp3"
