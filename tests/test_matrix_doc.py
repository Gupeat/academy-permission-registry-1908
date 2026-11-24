from __future__ import annotations

from pathlib import Path

from app.permissions import REQUIRED_ROLE_NAMES, load_registry, matrix_cell

DOC = Path(__file__).resolve().parents[1] / "docs" / "PERMISSION-MATRIX.md"


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def test_matrix_doc_has_six_roles_and_eleven_permissions():
    text = DOC.read_text(encoding="utf-8")
    assert "6 个角色 × 11 个权限点" in text
    lines = [line for line in text.splitlines() if line.startswith("| `academy.")]
    assert len(lines) == 11
    header = next(line for line in text.splitlines() if line.startswith("| 权限点 |"))
    names = _cells(header)[1:]
    assert names == [REQUIRED_ROLE_NAMES[code] for code in REQUIRED_ROLE_NAMES]


def test_matrix_doc_cells_match_config():
    registry = load_registry()
    roles = registry.role_by_code
    lines = [line for line in DOC.read_text(encoding="utf-8").splitlines() if line.startswith("| `academy.")]
    for line in lines:
        cells = _cells(line)
        code = cells[0].strip("`")
        expected = [matrix_cell(roles[role_code].permissions.get(code)) for role_code in REQUIRED_ROLE_NAMES]
        assert cells[1:] == expected, (code, cells[1:], expected)


def test_matrix_doc_has_no_placeholder_markers():
    text = DOC.read_text(encoding="utf-8")
    for marker in ("TODO", "TBD", "FIXME", "待补"):
        assert marker not in text
