# 本地验收结果（#1908）

- 生成时间：2026-11-24T05:33:23.477660+00:00
- 结果：**PASS**
- 测试：48/48 passed

| 检查 | 结果 | 证据 |
|---|---|---|
| migration | PASS | alembic upgrade head exit 0 |
| pytest | PASS | exit 0; 48 passed |
| matrix_doc | PASS | PERMISSION-MATRIX.md: 11 permission rows |
| registry | PASS | registry OK: 11 permissions, 6 roles, 24 role-permission links |
| ac1_query | PASS | PostgreSQL 16.2; 11 permissions |
| ac1_screenshot | PASS | 1400x1000; 72795 B |
