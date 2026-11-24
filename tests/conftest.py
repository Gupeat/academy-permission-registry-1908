from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from scripts.pg_runtime import run_migrations, temporary_postgres  # noqa: E402


@pytest.fixture(scope="session")
def database_url():
    configured = os.environ.get("TEST_DATABASE_URL")
    if configured:
        run_migrations(configured)
        yield configured
        return
    with temporary_postgres() as url:
        run_migrations(url)
        yield url


@pytest.fixture(scope="session")
def engine(database_url):
    eng = create_engine(database_url, future=True)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
