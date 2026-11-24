"""Local PostgreSQL 16 runtime for tests, evidence and acceptance."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def temporary_postgres() -> Iterator[str]:
    """Start the pgserver-bundled PostgreSQL 16 and yield a SQLAlchemy URL."""
    import pgserver

    pgdata = Path(tempfile.mkdtemp(prefix="pg1908-"))
    server = pgserver.get_server(pgdata, cleanup_mode="delete")
    try:
        server.ensure_postgres_running()
        url = server.get_uri().replace("postgresql://", "postgresql+psycopg2://", 1)
        yield url
    finally:
        server.cleanup()


def psycopg2_url(url: str) -> str:
    return url.replace("postgresql+psycopg2://", "postgresql://", 1)


def run_migrations(url: str) -> None:
    env = dict(os.environ)
    env["DATABASE_URL"] = url
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )
