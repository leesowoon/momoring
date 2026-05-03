import asyncio

from app.adapters.base import LLMMessage, LLMProvider, TTSProvider
from app.services.orchestrator import STSOrchestrator
from app.services.safety import SafetyService


def _last_user(messages: list[LLMMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return ""


class UnsafeOutputLLM(LLMProvider):
    async def generate(self, messages: list[LLMMessage]) -> str:
        _ = messages
        return "자해를 시도해"


class SafeOutputLLM(LLMProvider):
    async def generate(self, messages: list[LLMMessage]) -> str:
        return f"안전한 답변: {_last_user(messages)}"


class CapturingLLM(LLMProvider):
    def __init__(self) -> None:
        self.last_messages: list[LLMMessage] = []

    async def generate(self, messages: list[LLMMessage]) -> str:
        self.last_messages = messages
        return "ok"


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


def test_orchestrator_passes_age_group_into_prompt() -> None:
    capturing = CapturingLLM()
    orchestrator = STSOrchestrator(llm=capturing, tts=DummyTTS(), safety=SafetyService())
    asyncio.run(orchestrator.respond("뭐해", age_group="7-9"))

    system_msg = capturing.last_messages[0]
    assert system_msg.role == "system"
    assert "7-9세" in system_msg.content


def test_orchestrator_tts_method_uses_provider() -> None:
    orchestrator = STSOrchestrator(llm=SafeOutputLLM(), tts=DummyTTS(), safety=SafetyService())
    audio = asyncio.run(orchestrator.tts("session-1", "hello"))
    assert audio == "/audio/dummy.mp3"
