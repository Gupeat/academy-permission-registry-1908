"""Negative probe: a tampered permission mapping must be rejected.

The submission gate runs this script and expects a non-zero exit.  Exit 1 is
the *desired* outcome: it proves that adding a permission to a role is caught
by the independent validator rather than silently accepted.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.permissions import load_registry, validate_registry  # noqa: E402

CONFIG = ROOT / "config" / "academy_permissions.json"


def main() -> int:
    raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    for role in raw["roles"]:
        if role["code"] == "operations_specialist":
            role["permissions"]["academy.course.publish"] = "all"
            break
    else:
        raise RuntimeError("operations_specialist role not found")
    with tempfile.TemporaryDirectory(prefix="1908-negative-") as tmp:
        tampered = Path(tmp) / "academy_permissions.json"
        tampered.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        errors = validate_registry(load_registry(tampered))
    if not errors:
        print("NEGATIVE_PROBE_FAILED: tampered mapping was accepted")
        return 0
    print("negative probe: tampered mapping rejected")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
