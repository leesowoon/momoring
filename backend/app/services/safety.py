from dataclasses import dataclass

BANNED_KEYWORDS = {"죽고", "자해", "학대", "성적", "폭력"}


@dataclass
class SafetyResult:
    safe: bool
    reason: str | None = None


class SafetyService:
    def check(self, text: str) -> SafetyResult:
        lowered = text.lower()
        for word in BANNED_KEYWORDS:
            if word in lowered:
                return SafetyResult(False, f"blocked_keyword:{word}")
        return SafetyResult(True, None)

    def safe_fallback_response(self) -> str:
        return "이 주제는 안전하게 도와줄 수 있는 방식으로 이야기하자."
