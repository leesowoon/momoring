import re
from dataclasses import dataclass
from enum import Enum


class SafetyCategory(str, Enum):
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    DRUGS = "drugs"
    PERSONAL_INFO = "personal_info"
    HATE = "hate"


KEYWORDS: dict[SafetyCategory, tuple[str, ...]] = {
    SafetyCategory.SELF_HARM: (
        "자해",
        "자살",
        "죽고 싶",
        "죽고싶",
        "스스로 다치",
        "끝내고 싶",
        "사라지고 싶",
        "목숨 끊",
    ),
    SafetyCategory.VIOLENCE: (
        "폭력",
        "때리",
        "죽이",
        "흉기",
        "칼로",
        "학대",
        "괴롭히",
        "왕따",
    ),
    SafetyCategory.SEXUAL: (
        "성적",
        "성행위",
        "야한",
        "음란",
        "포르노",
        "성관계",
    ),
    SafetyCategory.DRUGS: (
        "마약",
        "필로폰",
        "대마",
        "약물 남용",
        "환각제",
    ),
    SafetyCategory.PERSONAL_INFO: (
        "주민등록번호",
        "주소 알려줘",
        "전화번호 알려줘",
        "비밀번호 알려줘",
        "계좌번호",
    ),
    SafetyCategory.HATE: (
        "혐오",
        "차별",
        "비하",
    ),
}

PHONE_PATTERN = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
RRN_PATTERN = re.compile(r"\d{6}-?[1-4]\d{6}")


TEMPLATES: dict[SafetyCategory, str] = {
    SafetyCategory.SELF_HARM: (
        "그런 마음을 이야기해줘서 고마워. 모모링은 안전을 위해 그 부분을 자세히 설명해줄 수는 없지만, "
        "혼자 견디지 말고 가까운 어른에게 꼭 말해보자. "
        "힘들 땐 자살예방상담 1393이나 청소년상담 1388에 전화하면 도와줄 어른이 있어."
    ),
    SafetyCategory.VIOLENCE: (
        "그건 모모링이 같이 이야기하기 어려운 주제야. "
        "혹시 누가 너를 다치게 한다면 곧바로 부모님이나 선생님께 알려줘. "
        "학교폭력 신고는 117번이야. 우리 다른 안전한 이야기를 해보자."
    ),
    SafetyCategory.SEXUAL: (
        "그 이야기는 모모링이 직접 설명하기 어려운 주제야. "
        "궁금한 게 있으면 부모님이나 선생님 같은 믿을 수 있는 어른과 이야기하면 좋아. "
        "모모링은 다른 안전하고 즐거운 이야기로 함께해줄게."
    ),
    SafetyCategory.DRUGS: (
        "그 주제는 안전을 위해 모모링이 자세히 알려주기는 어려워. "
        "위험할 수 있으니 보호자나 의사 선생님 같은 어른과 함께 이야기해야 해. "
        "다른 궁금한 게 있으면 같이 알아보자."
    ),
    SafetyCategory.PERSONAL_INFO: (
        "전화번호나 주소, 비밀번호 같은 개인정보는 안전을 위해 모모링에게 알려주지 않아도 돼. "
        "혹시 누가 알려달라고 하면 어른과 먼저 의논하자."
    ),
    SafetyCategory.HATE: (
        "사람을 미워하거나 무시하는 말은 누군가에게 큰 상처가 될 수 있어. "
        "서로 다른 점을 이해하고 존중하는 안전한 이야기를 함께 해보자."
    ),
}


DEFAULT_TEMPLATE = (
    "이 주제는 안전하게 도와줄 수 있는 방식으로 이야기하자. "
    "곁에 있는 어른과 함께 이야기해보면 더 좋을 거야."
)


@dataclass
class SafetyResult:
    safe: bool
    reason: str | None = None
    category: SafetyCategory | None = None


class SafetyService:
    def check(self, text: str) -> SafetyResult:
        lowered = text.lower()
        for category, words in KEYWORDS.items():
            for word in words:
                if word in lowered:
                    return SafetyResult(
                        safe=False,
                        reason=f"blocked_keyword:{word}",
                        category=category,
                    )

        if PHONE_PATTERN.search(text) or RRN_PATTERN.search(text):
            return SafetyResult(
                safe=False,
                reason="blocked_pii",
                category=SafetyCategory.PERSONAL_INFO,
            )

        return SafetyResult(safe=True)

    def safe_fallback_response(self, category: SafetyCategory | None = None) -> str:
        if category is None:
            return DEFAULT_TEMPLATE
        return TEMPLATES.get(category, DEFAULT_TEMPLATE)
