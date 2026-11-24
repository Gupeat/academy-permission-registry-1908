"""SQLAlchemy engine and request-scoped session."""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.config import database_url


@lru_cache(maxsize=1)
def _engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True, future=True)


def get_db() -> Iterator[Session]:
    db = Session(bind=_engine())
    try:
        yield db
    finally:
        db.close()
