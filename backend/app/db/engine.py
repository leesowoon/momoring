"""Engine and session-factory builders for the DB layer.

The app currently defaults to the JSON SessionStore. Setting DATABASE_URL
opt-in switches future code paths to DBSessionStore (wiring lands in a
follow-up PR).
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def build_engine(url: str) -> Engine:
    return create_engine(url, future=True, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
