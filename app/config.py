"""Runtime configuration.

Only environment variables are used for deployment-specific values.
"""
from __future__ import annotations

import os

DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres@127.0.0.1:5432/postgres"


def database_url() -> str:
    """Return the configured database URL, never a hard-coded password."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
