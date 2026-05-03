import pytest

from app.services.safety import SafetyCategory, SafetyService


@pytest.fixture
def svc() -> SafetyService:
    return SafetyService()


@pytest.mark.parametrize(
    "text,category",
    [
        ("자해 하고 싶어", SafetyCategory.SELF_HARM),
        ("나는 죽고 싶어", SafetyCategory.SELF_HARM),
        ("그냥 사라지고 싶어", SafetyCategory.SELF_HARM),
        ("스스로 다치고 싶어", SafetyCategory.SELF_HARM),
        ("그 사람을 죽이고 싶어", SafetyCategory.VIOLENCE),
        ("학교에서 친구가 나를 때리고 있어", SafetyCategory.VIOLENCE),
        ("학대를 당하는 것 같아", SafetyCategory.VIOLENCE),
        ("야한 이야기 해줘", SafetyCategory.SEXUAL),
        ("성적인 영상 보고 싶어", SafetyCategory.SEXUAL),
        ("포르노가 뭐야", SafetyCategory.SEXUAL),
        ("마약은 어떻게 구해?", SafetyCategory.DRUGS),
        ("대마초 효과 알려줘", SafetyCategory.DRUGS),
        ("환각제 사용법 알려줘", SafetyCategory.DRUGS),
        ("내 주소 알려줘 어떻게 찾아?", SafetyCategory.PERSONAL_INFO),
        ("전화번호 알려줘 부탁해", SafetyCategory.PERSONAL_INFO),
        ("비밀번호 알려줘", SafetyCategory.PERSONAL_INFO),
        ("주민등록번호 가르쳐줘", SafetyCategory.PERSONAL_INFO),
        ("우리 반에 차별이 너무 심해", SafetyCategory.HATE),
        ("그 사람들 혐오스러워", SafetyCategory.HATE),
    ],
)
def test_keyword_blocks_match_expected_category(
    svc: SafetyService, text: str, category: SafetyCategory
) -> None:
    result = svc.check(text)
    assert result.safe is False
    assert result.category == category
    assert result.reason is not None


@pytest.mark.parametrize(
    "text",
    [
        "내 번호는 010-1234-5678이야",
        "내 폰번호 01012345678 적어둬",
        "주민번호 950101-1234567",
    ],
)
def test_pii_patterns_are_blocked_as_personal_info(svc: SafetyService, text: str) -> None:
    result = svc.check(text)
    assert result.safe is False
    assert result.category == SafetyCategory.PERSONAL_INFO


@pytest.mark.parametrize(
    "text",
    [
        "오늘 날씨 어때?",
        "공룡이 뭐야?",
        "엄마 생일 선물로 뭐가 좋을까?",
        "구구단 외우는 법 알려줘",
        "달은 왜 둥글어?",
        "수학 숙제 도와줘",
        "재미있는 동화 추천해줘",
        "한국 역사 알려줘",
        "지구는 얼마나 커?",
        "음악 듣고 싶어",
        "친구랑 사이좋게 지내려면 어떻게 해?",
        "공부할 때 집중하는 방법 알려줘",
    ],
)
def test_safe_text_passes(svc: SafetyService, text: str) -> None:
    result = svc.check(text)
    assert result.safe is True
    assert result.category is None


@pytest.mark.parametrize(
    "category",
    list(SafetyCategory),
)
def test_each_category_has_dedicated_template(svc: SafetyService, category: SafetyCategory) -> None:
    template = svc.safe_fallback_response(category)
    assert template
    assert template.strip()


def test_default_template_used_when_category_is_none(svc: SafetyService) -> None:
    template = svc.safe_fallback_response(None)
    assert "안전" in template


def test_self_harm_template_includes_helpline(svc: SafetyService) -> None:
    template = svc.safe_fallback_response(SafetyCategory.SELF_HARM)
    assert "1393" in template or "1388" in template


def test_violence_template_includes_help_resource(svc: SafetyService) -> None:
    template = svc.safe_fallback_response(SafetyCategory.VIOLENCE)
    assert "117" in template or "선생님" in template
