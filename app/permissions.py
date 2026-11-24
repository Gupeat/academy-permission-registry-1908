"""Academy permission registry: configuration loader and task-level validator.

The JSON config is the single source used by the Alembic seed and the matrix
generator. REQUIRED_* below are an independent encoding of task #1908 so a
tampered config cannot silently become the new truth.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "academy_permissions.json"

REQUIRED_PERMISSIONS: tuple[str, ...] = (
    "academy.course.read",
    "academy.course.edit",
    "academy.course.publish",
    "academy.session.manage",
    "academy.instructor.manage",
    "academy.application.review",
    "academy.roster.read",
    "academy.learning.correct",
    "academy.review.moderate",
    "academy.stats.read",
    "academy.entitlement.config",
)

REQUIRED_ROLE_NAMES: dict[str, str] = {
    "operations_specialist": "运营专员",
    "operations_supervisor": "运营主管",
    "member_manager": "会员经理",
    "front_desk": "前台接待",
    "system_admin": "系统管理员",
    "auditor": "审计员",
}

REQUIRED_MAPPING: dict[str, dict[str, str]] = {
    "operations_specialist": {
        "academy.course.read": "all",
        "academy.course.edit": "all",
        "academy.session.manage": "all",
        "academy.instructor.manage": "all",
        "academy.application.review": "all",
        "academy.roster.read": "all",
        "academy.learning.correct": "all",
        "academy.review.moderate": "all",
    },
    "operations_supervisor": {code: "all" for code in REQUIRED_PERMISSIONS},
    "member_manager": {
        "academy.course.read": "all",
        "academy.roster.read": "own",
        "academy.stats.read": "all",
    },
    "front_desk": {
        "academy.course.read": "all",
        "academy.roster.read": "masked_phone",
    },
    "system_admin": {},
    "auditor": {},
}

SCOPE_VALUES = {"all", "own", "masked_phone"}
SCOPE_LABELS = {"all": "✓", "own": "✓（本人）", "masked_phone": "✓（脱敏）"}


@dataclass(frozen=True)
class Permission:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class Role:
    code: str
    name: str
    permissions: dict[str, str]


@dataclass(frozen=True)
class UserSeed:
    username: str
    display_name: str
    role_code: str


@dataclass(frozen=True)
class RosterSeed:
    course_id: str
    member_id: str
    member_name: str
    phone: str
    manager_username: str


@dataclass(frozen=True)
class Registry:
    org_id: str
    site_id: str
    permissions: tuple[Permission, ...]
    roles: tuple[Role, ...]
    users: tuple[UserSeed, ...]
    roster: tuple[RosterSeed, ...]

    @property
    def role_by_code(self) -> dict[str, Role]:
        return {role.code: role for role in self.roles}


def load_registry(path: Path | None = None) -> Registry:
    raw = json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))
    return Registry(
        org_id=str(raw["org_id"]),
        site_id=str(raw["site_id"]),
        permissions=tuple(
            Permission(code=str(item["code"]), name=str(item["name"]), description=str(item.get("description", "")))
            for item in raw["permissions"]
        ),
        roles=tuple(
            Role(code=str(item["code"]), name=str(item["name"]), permissions=dict(item["permissions"]))
            for item in raw["roles"]
        ),
        users=tuple(
            UserSeed(username=str(item["username"]), display_name=str(item["display_name"]), role_code=str(item["role_code"]))
            for item in raw["users"]
        ),
        roster=tuple(
            RosterSeed(
                course_id=str(item["course_id"]),
                member_id=str(item["member_id"]),
                member_name=str(item["member_name"]),
                phone=str(item["phone"]),
                manager_username=str(item["manager_username"]),
            )
            for item in raw["roster"]
        ),
    )


def validate_registry(reg: Registry) -> list[str]:
    """Return every mismatch against the task's literal requirements."""
    errors: list[str] = []
    if not reg.org_id or not reg.site_id:
        errors.append("org_id/site_id must be non-empty")

    codes = [item.code for item in reg.permissions]
    if len(codes) != len(set(codes)):
        errors.append(f"duplicate permission codes: {codes}")
    if set(codes) != set(REQUIRED_PERMISSIONS):
        errors.append(f"permission set mismatch: missing={sorted(set(REQUIRED_PERMISSIONS) - set(codes))} extra={sorted(set(codes) - set(REQUIRED_PERMISSIONS))}")
    for item in reg.permissions:
        if not item.name.strip():
            errors.append(f"permission {item.code} has empty name")

    role_codes = [role.code for role in reg.roles]
    if len(role_codes) != len(set(role_codes)):
        errors.append(f"duplicate role codes: {role_codes}")
    if set(role_codes) != set(REQUIRED_ROLE_NAMES):
        errors.append(f"role set mismatch: missing={sorted(set(REQUIRED_ROLE_NAMES) - set(role_codes))} extra={sorted(set(role_codes) - set(REQUIRED_ROLE_NAMES))}")
    for role in reg.roles:
        if role.name != REQUIRED_ROLE_NAMES.get(role.code):
            errors.append(f"role {role.code} name {role.name!r} != {REQUIRED_ROLE_NAMES.get(role.code)!r}")
        expected = REQUIRED_MAPPING.get(role.code, {})
        if role.permissions != expected:
            missing = sorted(set(expected) - set(role.permissions))
            extra = sorted(set(role.permissions) - set(expected))
            errors.append(f"role {role.code} mapping mismatch: missing={missing} extra={extra}")
        for code, scope in role.permissions.items():
            if code not in REQUIRED_PERMISSIONS:
                errors.append(f"role {role.code} references unknown permission {code}")
            if scope not in SCOPE_VALUES:
                errors.append(f"role {role.code} permission {code} has invalid scope {scope!r}")

    usernames = [user.username for user in reg.users]
    if len(usernames) != len(set(usernames)):
        errors.append(f"duplicate usernames: {usernames}")
    for user in reg.users:
        if user.role_code not in REQUIRED_ROLE_NAMES:
            errors.append(f"user {user.username} references unknown role {user.role_code}")
        if not user.display_name.strip():
            errors.append(f"user {user.username} has empty display_name")

    known_users = set(usernames)
    for member in reg.roster:
        if member.manager_username not in known_users:
            errors.append(f"roster member {member.member_id} references unknown manager {member.manager_username}")
        if not (len(member.phone) == 11 and member.phone.isdigit()):
            errors.append(f"roster member {member.member_id} phone is not an 11-digit fictional number")

    return errors


def matrix_cell(scope: str | None) -> str:
    if scope is None:
        return "—"
    return SCOPE_LABELS.get(scope, scope)


def render_matrix(reg: Registry) -> str:
    """Render the 6-role x 11-permission matrix from the config."""
    role_order = list(REQUIRED_ROLE_NAMES)
    roles = reg.role_by_code
    lines = [
        "# 学院权限矩阵（6 个角色 × 11 个权限点）",
        "",
        "> 由 `scripts/export_matrix.py` 从 `config/academy_permissions.json` 生成，不要手改。",
        "> 图例：✓ = 允许；— = 无权限；✓（本人）= 仅本人负责的会员；✓（脱敏）= 手机号后 4 位。",
        "",
        "| 权限点 | " + " | ".join(roles[code].name for code in role_order) + " |",
        "|---|" + "---|" * len(role_order),
    ]
    for permission in reg.permissions:
        cells = [matrix_cell(roles[code].permissions.get(permission.code)) for code in role_order]
        lines.append(f"| `{permission.code}` | " + " | ".join(cells) + " |")
    lines += [
        "",
        "统计：11 个权限点；运营专员 8 个、运营主管 11 个、会员经理 3 个、前台接待 2 个、系统管理员 0 个、审计员 0 个。",
        "",
        "数据范围：会员经理的 `academy.roster.read` 只返回 `manager_id = 当前用户` 的会员；前台接待返回的手机号只保留后 4 位。",
        "",
    ]
    return "\n".join(lines)
