from app.services.prompt_builder import PromptBuilder
from app.services.session_store import Turn


def _turn(user: str, bot: str) -> Turn:
    return Turn(user_text=user, bot_text=bot, blocked=False, created_at="2025-01-01T00:00:00Z")


def test_builder_includes_system_persona_safety_and_age_guidance() -> None:
    messages = PromptBuilder().build(user_text="안녕", age_group="10-12")

    assert messages[0].role == "system"
    system = messages[0].content
    assert "모모링" in system
    assert "안전" in system
    assert "10-12세" in system

    assert messages[-1].role == "user"
    assert messages[-1].content == "안녕"


def test_builder_age_specific_guidance_changes_with_age_group() -> None:
    young = PromptBuilder().build(user_text="x", age_group="7-9")[0].content
    teen = PromptBuilder().build(user_text="x", age_group="13-15")[0].content
    assert "7-9세" in young
    assert "13-15세" in teen
    assert young != teen


def test_builder_falls_back_to_default_age_when_unknown() -> None:
    messages = PromptBuilder().build(user_text="x", age_group="999")
    # default guidance is 10-12
    assert "10-12세" in messages[0].content


def test_builder_includes_recent_history_in_order() -> None:
    history = [_turn("Q1", "A1"), _turn("Q2", "A2")]
    messages = PromptBuilder().build(user_text="Q3", age_group="10-12", history=history)

    roles = [m.role for m in messages]
    contents = [m.content for m in messages]

    assert roles == ["system", "user", "assistant", "user", "assistant", "user"]
    assert contents[1:] == ["Q1", "A1", "Q2", "A2", "Q3"]


def test_builder_truncates_history_to_max_turns() -> None:
    history = [_turn(f"Q{i}", f"A{i}") for i in range(20)]
    messages = PromptBuilder(max_history_turns=3).build(
        user_text="now",
        age_group="10-12",
        history=history,
    )

    history_messages = messages[1:-1]
    assert len(history_messages) == 6  # 3 turns x (user + assistant)
    assert history_messages[0].content == "Q17"
    assert history_messages[-1].content == "A19"
