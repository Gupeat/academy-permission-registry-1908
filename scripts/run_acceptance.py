"""End-to-end local acceptance for #1908 against a real PostgreSQL 16."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.make_ac1_screenshot import capture  # noqa: E402
from scripts.pg_runtime import run_migrations, temporary_postgres  # noqa: E402
from scripts.query_ac1 import query  # noqa: E402

ARTIFACTS = REPO_ROOT / "artifacts"
ACCEPTANCE_JSON = ARTIFACTS / "acceptance.json"
ACCEPTANCE_MD = ARTIFACTS / "ACCEPTANCE.md"
EXPECTED_TESTS = 49
MATRIX = REPO_ROOT / "docs" / "PERMISSION-MATRIX.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(status: str, checks: dict, tests_passed: int = 0, note: str = "") -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    all_passed = status == "PASS"
    payload = {
        "generated_at": _now(),
        "status": status,
        "all_passed": all_passed,
        "tests_expected": EXPECTED_TESTS,
        "tests_passed": tests_passed,
        "checks": checks,
        "note": note,
    }
    ACCEPTANCE_JSON.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    lines = [
        "# 本地验收结果（#1908）",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 结果：**{status}**",
        f"- 测试：{tests_passed}/{EXPECTED_TESTS} passed",
        "",
        "| 检查 | 结果 | 证据 |",
        "|---|---|---|",
    ]
    for name, detail in checks.items():
        ok = detail.get("ok") if isinstance(detail, dict) else bool(detail)
        evidence = detail.get("evidence", "") if isinstance(detail, dict) else str(detail)
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {evidence} |")
    if note:
        lines += ["", f"说明：{note}"]
    ACCEPTANCE_MD.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def _run(cmd: list[str], env: dict, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, text=True, capture_output=True, timeout=timeout)


def main() -> int:
    checks: dict = {}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for stale in (ACCEPTANCE_JSON, ACCEPTANCE_MD, ARTIFACTS / "ac1-query.json",
                  ARTIFACTS / "AC1-permissions.png", ARTIFACTS / "ac1.html"):
        if stale.exists():
            stale.unlink()
    _write("FAIL", {"started": {"ok": False, "evidence": "acceptance started; rewritten only after checks pass"}}, 0, "running")
    try:
        with temporary_postgres() as url:
            env = dict(os.environ)
            env["DATABASE_URL"] = url
            env["TEST_DATABASE_URL"] = url
            run_migrations(url)
            checks["migration"] = {"ok": True, "evidence": "alembic upgrade head exit 0"}

            pytest_proc = _run([sys.executable, "-m", "pytest", "-q"], env)
            match = re.search(r"(\d+) passed", pytest_proc.stdout)
            tests_passed = int(match.group(1)) if match else 0
            checks["pytest"] = {
                "ok": pytest_proc.returncode == 0 and tests_passed == EXPECTED_TESTS,
                "evidence": f"exit {pytest_proc.returncode}; {tests_passed} passed",
            }
            if not checks["pytest"]["ok"]:
                raise RuntimeError(f"pytest failed: {pytest_proc.stdout[-1200:]}{pytest_proc.stderr[-800:]}")

            matrix_rows = [
                line for line in MATRIX.read_text(encoding="utf-8").splitlines()
                if line.startswith("| `academy.")
            ]
            checks["matrix_doc"] = {
                "ok": len(matrix_rows) == 11,
                "evidence": f"{MATRIX.name}: {len(matrix_rows)} permission rows",
            }

            registry_proc = _run([sys.executable, "scripts/check_registry.py"], env)
            checks["registry"] = {
                "ok": registry_proc.returncode == 0,
                "evidence": (registry_proc.stdout.strip() or registry_proc.stderr.strip())[-300:],
            }

            ac1 = query(url)
            checks["ac1_query"] = {
                "ok": ac1["count"] == 11,
                "evidence": f"PostgreSQL {ac1['server_version']}; {ac1['count']} permissions",
            }
            (ARTIFACTS / "ac1-query.json").write_bytes(
                (json.dumps(ac1, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            )

            shot = capture(url, ARTIFACTS / "AC1-permissions.png", ARTIFACTS / "ac1.html")
            checks["ac1_screenshot"] = {
                "ok": shot["count"] == 11 and shot["png_size"][0] >= 1200,
                "evidence": f"{shot['png_size'][0]}x{shot['png_size'][1]}; {shot['png_bytes']} B",
            }

            passed = all(item["ok"] for item in checks.values())
            _write("PASS" if passed else "FAIL", checks, tests_passed,
                   "" if passed else "至少一项检查失败，见上表")
            print(json.dumps({"status": "PASS" if passed else "FAIL", "tests_passed": tests_passed,
                              "checks": {k: v["ok"] for k, v in checks.items()}}, ensure_ascii=False))
            return 0 if passed else 1
    except Exception as exc:  # noqa: BLE001 - acceptance must always leave a FAIL record
        checks.setdefault("fatal", {"ok": False, "evidence": str(exc)[-500:]})
        _write("FAIL", checks, 0, str(exc)[-500:])
        print(f"ACCEPTANCE FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
