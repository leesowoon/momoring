from app.services.safety import SafetyService


def test_safety_service_blocks_keyword() -> None:
    svc = SafetyService()
    result = svc.check("자해 하고 싶어")
    assert result.safe is False
    assert result.reason is not None


def test_safety_service_allows_safe_text() -> None:
    svc = SafetyService()
    result = svc.check("오늘 뭐 배울까?")
    assert result.safe is True
