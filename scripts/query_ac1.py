"""Run the AC1 SQL query and print/save the evidence rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import database_url  # noqa: E402
from scripts.pg_runtime import psycopg2_url  # noqa: E402

SQL = """
SELECT code, name, module
FROM academy_permissions
WHERE deleted_at IS NULL
ORDER BY code
"""


def query(url: str) -> dict:
    conn = psycopg2.connect(psycopg2_url(url))
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW server_version")
            server_version = cur.fetchone()[0]
            cur.execute(SQL)
            rows = [
                {"code": code, "name": name, "module": module}
                for code, name, module in cur.fetchall()
            ]
    finally:
        conn.close()
    return {"sql": SQL.strip(), "server_version": server_version, "count": len(rows), "rows": rows}


def main() -> int:
    result = query(database_url())
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts") / "ac1-query.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"PostgreSQL {result['server_version']} | {result['count']} academy permissions")
    for row in result["rows"]:
        print(f"{row['code']:32} {row['name']}")
    print(f"wrote {out}")
    return 0 if result["count"] == 11 else 1


if __name__ == "__main__":
    raise SystemExit(main())
