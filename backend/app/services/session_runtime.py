"""Per-session ephemeral runtime state (last_seq, phase).

Lives in memory only. Survives WS reconnections within a process but not
restarts. For multi-instance deployments this would move to Redis (post-MVP).
"""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Literal

Phase = Literal["idle", "listening", "thinking", "speaking"]


@dataclass
class SessionRuntime:
    last_seq: int = -1
    phase: Phase = "idle"


class SessionRuntimeStore:
    def __init__(self) -> None:
        self._states: dict[str, SessionRuntime] = {}
        self._lock = Lock()

    def _state(self, session_id: str) -> SessionRuntime:
        if session_id not in self._states:
            self._states[session_id] = SessionRuntime()
        return self._states[session_id]

    def accept_seq(self, session_id: str, seq: int) -> bool:
        """Returns True if the seq is strictly greater than last seen and was
        accepted, False if it's a duplicate or out-of-order chunk to drop."""
        with self._lock:
            state = self._state(session_id)
            if seq <= state.last_seq:
                return False
            state.last_seq = seq
            return True

    def fast_forward_seq(self, session_id: str, seq: int) -> None:
        """Used by the resume event — bumps last_seq to at least the given
        value so the client can skip past chunks the server already saw."""
        with self._lock:
            state = self._state(session_id)
            if seq > state.last_seq:
                state.last_seq = seq

    def set_phase(self, session_id: str, phase: Phase) -> None:
        with self._lock:
            self._state(session_id).phase = phase

    def get_phase(self, session_id: str) -> Phase:
        with self._lock:
            return self._state(session_id).phase

    def get_last_seq(self, session_id: str) -> int:
        with self._lock:
            return self._state(session_id).last_seq

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._states.pop(session_id, None)
