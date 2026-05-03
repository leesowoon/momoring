import json
import logging

from app.services.logging_config import JsonFormatter


def _make_record(msg: str, extra: dict | None = None) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if extra is not None:
        record.extra_fields = extra
    return record


def test_formatter_produces_valid_json_with_basic_fields() -> None:
    output = JsonFormatter().format(_make_record("hello"))
    parsed = json.loads(output)
    assert parsed["level"] == "info"
    assert parsed["logger"] == "test"
    assert parsed["msg"] == "hello"


def test_formatter_merges_extra_fields_at_top_level() -> None:
    output = JsonFormatter().format(
        _make_record("respond", extra={"trace_id": "abc-123", "total_ms": 42}),
    )
    parsed = json.loads(output)
    assert parsed["trace_id"] == "abc-123"
    assert parsed["total_ms"] == 42
    assert parsed["msg"] == "respond"


def test_formatter_includes_exception_info() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="failed",
            args=(),
            exc_info=logging.sys.exc_info(),
        )
    output = JsonFormatter().format(record)
    parsed = json.loads(output)
    assert "exc" in parsed
    assert "ValueError" in parsed["exc"]
