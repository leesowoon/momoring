from app.services.session_runtime import SessionRuntimeStore


def test_first_seq_is_accepted_and_recorded() -> None:
    store = SessionRuntimeStore()
    assert store.accept_seq("s1", 0) is True
    assert store.get_last_seq("s1") == 0


def test_strictly_increasing_sequences_accepted() -> None:
    store = SessionRuntimeStore()
    for seq in [0, 1, 2, 5, 10]:
        assert store.accept_seq("s1", seq) is True
    assert store.get_last_seq("s1") == 10


def test_duplicate_or_lower_seq_rejected() -> None:
    store = SessionRuntimeStore()
    store.accept_seq("s1", 5)
    assert store.accept_seq("s1", 5) is False
    assert store.accept_seq("s1", 3) is False
    assert store.get_last_seq("s1") == 5


def test_per_session_isolation() -> None:
    store = SessionRuntimeStore()
    store.accept_seq("s1", 7)
    store.accept_seq("s2", 1)
    assert store.get_last_seq("s1") == 7
    assert store.get_last_seq("s2") == 1


def test_fast_forward_only_advances_never_rewinds() -> None:
    store = SessionRuntimeStore()
    store.accept_seq("s1", 10)
    store.fast_forward_seq("s1", 5)
    assert store.get_last_seq("s1") == 10
    store.fast_forward_seq("s1", 20)
    assert store.get_last_seq("s1") == 20


def test_default_phase_is_idle() -> None:
    store = SessionRuntimeStore()
    assert store.get_phase("s1") == "idle"


def test_phase_transitions_persist() -> None:
    store = SessionRuntimeStore()
    store.set_phase("s1", "listening")
    assert store.get_phase("s1") == "listening"
    store.set_phase("s1", "speaking")
    assert store.get_phase("s1") == "speaking"


def test_reset_drops_session_state() -> None:
    store = SessionRuntimeStore()
    store.accept_seq("s1", 7)
    store.set_phase("s1", "speaking")
    store.reset("s1")
    assert store.get_last_seq("s1") == -1
    assert store.get_phase("s1") == "idle"
