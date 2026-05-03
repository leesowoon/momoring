from dataclasses import dataclass

from ..adapters.base import LLMMessage
from .session_store import Turn


SYSTEM_PERSONA = (
    "당신은 모모링이라는 친근하고 다정한 캐릭터입니다. "
    "아이/청소년 사용자와 대화하며 짧고 따뜻한 어투로 답합니다. "
    "어려운 단어는 쉽게 풀어 설명하고, 한 번에 너무 많은 정보를 주지 않습니다."
)

SAFETY_POLICY = (
    "안전이 최우선입니다. 자해, 자살, 폭력, 성, 학대, 약물, 타인의 개인정보 같은 위험한 주제는 "
    "직접 설명하지 않고, '거부 + 안전한 대안 제시 + 어른/전문가 도움 권고'의 3단 구성으로 답합니다. "
    "사용자가 위험 신호를 보이면 따뜻한 어투로 안전에 대해 이야기하고, 믿을 수 있는 어른과 함께 "
    "이야기하자고 권합니다."
)

AGE_GUIDANCE: dict[str, str] = {
    "7-9": (
        "지금 7-9세 아이와 대화하고 있습니다. "
        "한 문장은 짧고, 어휘는 초등 저학년 수준으로 사용합니다. "
        "한 답변은 1-2문장으로 짧게 유지합니다."
    ),
    "10-12": (
        "지금 10-12세 아이와 대화하고 있습니다. "
        "초등 고학년 수준 어휘를 사용하고, 한 답변은 2-3문장으로 명확하게 정리합니다."
    ),
    "13-15": (
        "지금 13-15세 청소년과 대화하고 있습니다. "
        "중학생 수준 어휘를 사용하고, 필요하면 3-5문장으로 구체적인 예시를 곁들여 설명합니다."
    ),
}

DEFAULT_AGE_GUIDANCE = AGE_GUIDANCE["10-12"]


@dataclass
class PromptBuilder:
    max_history_turns: int = 8

    def build(
        self,
        *,
        user_text: str,
        age_group: str | None = None,
        history: list[Turn] | None = None,
    ) -> list[LLMMessage]:
        messages: list[LLMMessage] = [LLMMessage(role="system", content=self._system(age_group))]

        for turn in (history or [])[-self.max_history_turns :]:
            messages.append(LLMMessage(role="user", content=turn.user_text))
            messages.append(LLMMessage(role="assistant", content=turn.bot_text))

        messages.append(LLMMessage(role="user", content=user_text))
        return messages

    def _system(self, age_group: str | None) -> str:
        guidance = AGE_GUIDANCE.get(age_group or "", DEFAULT_AGE_GUIDANCE)
        return "\n\n".join([SYSTEM_PERSONA, guidance, SAFETY_POLICY])
