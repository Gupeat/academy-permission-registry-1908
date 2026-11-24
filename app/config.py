"""Runtime configuration.

Only environment variables are used for deployment-specific values.
"""
from __future__ import annotations

import os


def database_url() -> str:
    """Return DATABASE_URL, never a hard-coded host or password."""
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is required; set it to a PostgreSQL 16 URL")
    return value
