"""Render AC1: SQL query against the migrated PostgreSQL 16 database."""
from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.pg_runtime import run_migrations, temporary_postgres  # noqa: E402
from scripts.query_ac1 import query  # noqa: E402

EDGE_CANDIDATES = [
    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
]


def _html(result: dict) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(row['code'])}</td><td>{html.escape(row['name'])}</td><td>{html.escape(row['module'])}</td></tr>"
        for row in result["rows"]
    )
    sql = html.escape(result["sql"])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>AC1 权限点注册证据</title>
<style>
body {{ font: 15px/1.55 'Segoe UI', 'Microsoft YaHei', sans-serif; color: #172033; margin: 0; background: #f4f7fb; }}
.page {{ width: 1320px; margin: 36px auto; background: #fff; border: 1px solid #dbe3ef; border-radius: 10px; padding: 30px 36px; box-sizing: border-box; }}
h1 {{ font-size: 28px; margin: 0 0 6px; }}
.sub {{ color: #5b6b82; margin: 0 0 22px; }}
.badge {{ display: inline-block; background: #e8f7ee; color: #126b39; border: 1px solid #b7e4c7; border-radius: 999px; padding: 4px 12px; font-weight: 600; margin-right: 8px; }}
.meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; margin: 18px 0; color: #334155; }}
.meta b {{ color: #0f172a; }}
pre {{ background: #0f172a; color: #dbeafe; padding: 16px 18px; border-radius: 8px; font: 14px/1.55 Consolas, monospace; overflow: hidden; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 14px; }}
th {{ text-align: left; background: #eef3fb; color: #334155; padding: 9px 10px; border-bottom: 2px solid #cbd8ea; }}
td {{ padding: 8px 10px; border-bottom: 1px solid #e5ecf5; font-family: Consolas, monospace; }}
tr:nth-child(even) td {{ background: #fafcff; }}
.count {{ font-size: 22px; font-weight: 700; color: #126b39; }}
.note {{ color: #64748b; font-size: 13px; margin-top: 16px; }}
</style></head><body><div class="page">
<h1>AC1 迁移执行后权限表 SQL 查询</h1>
<p class="sub">#1908 学院权限点注册与角色默认映射 · 虚构数据 · 2026-11-24</p>
<span class="badge">PostgreSQL {html.escape(result['server_version'])}</span>
<span class="badge">已执行 alembic upgrade head</span>
<div class="meta">
  <div><b>查询：</b>academy_permissions（未软删除）</div>
  <div><b>权限点数量：</b><span class="count">{result['count']}</span></div>
  <div><b>数据库：</b>真实 PostgreSQL 16 临时实例</div>
  <div><b>记录：</b>11 个 academy.* 权限点</div>
</div>
<pre>{sql}</pre>
<table><thead><tr><th>code</th><th>name</th><th>module</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">本图由 scripts/make_ac1_screenshot.py 生成：先启动 PostgreSQL 16 临时实例并执行 Alembic 迁移，再用上述 SQL 查询数据库。</p>
</div></body></html>"""


def _edge() -> Path:
    for candidate in EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Microsoft Edge not found; AC1 screenshot cannot be captured")


def capture(url: str, png: Path, html_path: Path | None = None) -> dict:
    result = query(url)
    html_path = html_path or png.with_suffix(".html")
    html_path.write_bytes(_html(result).encode("utf-8"))
    profile = Path(tempfile.mkdtemp(prefix="edge1908-"))
    try:
        proc = subprocess.run(
            [
                str(_edge()),
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile}",
                f"--window-size=1400,1000",
                "--hide-scrollbars",
                f"--screenshot={png}",
                html_path.as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if proc.returncode != 0 or not png.exists():
        raise RuntimeError(f"Edge screenshot failed rc={proc.returncode}: {proc.stderr[-800:]}")
    with Image.open(png) as image:
        size = image.size
    return {**result, "png": str(png), "png_bytes": png.stat().st_size, "png_size": size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="existing DATABASE_URL; default starts a temporary PostgreSQL 16")
    parser.add_argument("--out", default=str(REPO_ROOT / "artifacts" / "AC1-permissions.png"))
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.url:
        info = capture(args.url, out)
    else:
        with temporary_postgres() as url:
            run_migrations(url)
            info = capture(url, out)
    print(f"AC1 screenshot: {info['png']} ({info['png_bytes']} B, {info['png_size'][0]}x{info['png_size'][1]}), "
          f"PostgreSQL {info['server_version']}, {info['count']} permissions")
    return 0 if info["count"] == 11 and info["png_size"][0] >= 1200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
