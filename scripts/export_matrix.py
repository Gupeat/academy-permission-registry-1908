"""Generate docs/PERMISSION-MATRIX.md from config/academy_permissions.json."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.permissions import load_registry, render_matrix, validate_registry  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "docs" / "PERMISSION-MATRIX.md"


def main() -> int:
    registry = load_registry()
    errors = validate_registry(registry)
    if errors:
        print("registry config is invalid; refusing to export:")
        for error in errors:
            print("-", error)
        return 1
    text = render_matrix(registry)
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    print(f"wrote {out} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
