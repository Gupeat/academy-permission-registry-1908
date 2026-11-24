# 学院权限点注册与角色默认映射（#1908）

在统一权限体系中注册 11 个 `academy.*` 权限点，给 6 个角色写默认映射，并用一个 FastAPI 依赖
`require_academy_perm(code)` 统一拦截学院业务接口。权限点、角色、映射都是数据库数据，不是散落在路由里的 if。

数据全部为虚构演示数据，不包含客户名称或真实个人信息。

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL 16（本仓库用 `pgserver` 内置的 PostgreSQL 16.2 跑本地迁移与验收）

本单不涉及 Redis 或 pgvector；S2-IAM 用接口桩（`X-User-Name`）代替，接入点见下文。

## 快速开始

```bash
python -m pip install -e ".[dev]"
export DATABASE_URL="postgresql+psycopg2://postgres@127.0.0.1:5432/postgres"
alembic upgrade head
uvicorn app.main:app --reload
```

PowerShell：

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://postgres@127.0.0.1:5432/postgres"
alembic upgrade head
```

所有部署相关值只从环境变量读取（`DATABASE_URL` 必填）；代码与 `alembic.ini` 中没有数据库地址或口令。

## 登录 / S2-IAM 对接点

本地演示用请求头 `X-User-Name` 选择种子用户，例如：

```bash
curl -H "X-User-Name: ops_specialist" http://127.0.0.1:8000/api/v1/academy/courses
```

真实接入 S2-IAM 时，只替换 `app/iam.py` 的 `get_current_user`（换成 SSO/JWT 解析并读取 `iam_users` 的
`role_id`），保留 `app/deps.py` 的 `require_academy_perm(code)` 签名不变。所有学院路由都通过这个依赖读取
`iam_role_permissions`，不在路由里判断角色名。

## 权限点与端点

权限点定义在 `config/academy_permissions.json`，由 `alembic/versions/0001_academy_permissions.py`
写入 `academy_permissions`、`iam_roles`、`iam_role_permissions`、`iam_users` 和 `academy_roster_members`。

| 端点 | 方法 | 权限点 | 说明 |
|---|---|---|---|
| `/api/v1/academy/courses` | GET | `academy.course.read` | 查看课程 |
| `/api/v1/academy/courses/{id}` | POST | `academy.course.edit` | 编辑课程 |
| `/api/v1/academy/courses/{id}/publish` | POST | `academy.course.publish` | 审批发布 |
| `/api/v1/academy/sessions` | POST | `academy.session.manage` | 管理课期 |
| `/api/v1/academy/instructors` | POST | `academy.instructor.manage` | 管理讲师 |
| `/api/v1/academy/applications/{id}/review` | POST | `academy.application.review` | 审核报名 |
| `/api/v1/academy/rosters/{course_id}` | GET | `academy.roster.read` | 查看报名名单；按 scope 过滤/脱敏 |
| `/api/v1/academy/rosters/{course_id}/members/{member_id}` | GET | `academy.roster.read` | 查看单个会员；`own` 越界 403 |
| `/api/v1/academy/learning-records/{id}/correct` | POST | `academy.learning.correct` | 补录/更正学习记录 |
| `/api/v1/academy/reviews/{id}/moderate` | POST | `academy.review.moderate` | 隐藏/回复评价 |
| `/api/v1/academy/stats` | GET | `academy.stats.read` | 学院统计 |
| `/api/v1/academy/entitlements/config` | PUT | `academy.entitlement.config` | 配置学院权益 |

默认映射（完整 6×11 矩阵见 `docs/PERMISSION-MATRIX.md`）：

| 角色 | 权限数 | 特殊 scope |
|---|---:|---|
| 运营专员 `operations_specialist` | 8 | — |
| 运营主管 `operations_supervisor` | 11 | — |
| 会员经理 `member_manager` | 3 | `academy.roster.read` = `own` |
| 前台接待 `front_desk` | 2 | `academy.roster.read` = `masked_phone` |
| 系统管理员 `system_admin` | 0 | — |
| 审计员 `auditor` | 0 | — |

- `own`：名单只返回 `manager_id = 当前用户` 的会员；单个会员越界返回 403 `member_scope_denied`。
- `masked_phone`：手机号只返回 `*******` + 后 4 位。
- 系统管理员、审计员没有学院业务权限：12 个学院接口全部返回 403 `academy_permission_denied`。

## 数据表

业务表统一带 `id UUID`、`org_id`、`site_id`、`created_at`、`created_by`、`updated_at`、`deleted_at`。
删除使用软删除；权限查询都会过滤 `deleted_at IS NULL`。

- `academy_permissions`：权限点（`code` 唯一）。
- `iam_roles`：角色。
- `iam_role_permissions`：角色-权限映射，`scope` 为 `all` / `own` / `masked_phone`。
- `iam_users`：演示用户与角色。
- `academy_roster_members`：课程名单与负责经理。

种子用户：`ops_specialist`、`ops_supervisor`、`manager_a`、`manager_b`、`front_desk`、`system_admin`、`auditor`；
课程 `course-001` 的 4 个会员均为虚构数据。

## 验证

```bash
pytest -q
python scripts/run_acceptance.py
```

当前结果：**49 passed**；`scripts/run_acceptance.py` 使用真实 PostgreSQL 16.2 临时实例执行
`alembic upgrade head`、pytest、`check_registry.py`、AC1 SQL 查询与 Edge 截图。

- AC1：`artifacts/AC1-permissions.png`（1400×1000，真实 PG16 查询 11 行权限点）。
- AC2：`tests/test_403_matrix.py`，12 个学院接口 × 系统管理员/审计员 = 24 个 403。
- AC3：`docs/PERMISSION-MATRIX.md`，6 个角色 × 11 个权限点，由 config 生成并由测试解析校验。
- 本地验收汇总：`artifacts/acceptance.json`、`artifacts/ACCEPTANCE.md`。

`scripts/check_registry.py` 会同时校验 config 和数据库；删除/新增权限点、改映射、改角色名都会让
check 失败（exit 1）。

## 目录

```text
app/                     FastAPI 应用、模型、权限依赖、IAM mock
alembic/                 Alembic 迁移（注册 11 个权限点、6 个角色、24 条映射）
config/                  权限/角色/映射/种子用户/名单的单一配置源
docs/PERMISSION-MATRIX.md  6×11 权限矩阵（生成物）
scripts/                 matrix 导出、registry 校验、AC1 查询/截图、验收
tests/                   registry、403 参数化、映射/数据范围、矩阵、schema
```

## 限制

- 学院端点只演示权限边界，不实现完整课程/名单 CRUD 或写入持久化。
- 没有真实 S2-IAM、Redis、pgvector 或前端；生产接入时替换 `app/iam.py` 并给 `DATABASE_URL` 指向客户 PG16。
- 本地验收依赖 `pgserver` 内置 PostgreSQL 16.2 和 Microsoft Edge（仅用于 AC1 截图）。
- 权限矩阵是生成物，修改 `config/academy_permissions.json` 后需重新运行 `python scripts/export_matrix.py`。
