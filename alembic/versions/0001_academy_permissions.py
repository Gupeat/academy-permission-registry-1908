"""register academy permissions and default role mapping

Revision ID: 0001_academy_permissions
Revises:
Create Date: 2026-11-24 00:00:00
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0001_academy_permissions"
down_revision = None
branch_labels = None
depends_on = None

NAMESPACE = uuid.UUID("9f1b7e2c-3a4d-5e6f-8a9b-0c1d2e3f4a5b")
CREATED_BY = "migration:1908"
ROOT = Path(__file__).resolve().parents[2]


def _permission_id(code: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, "permission:" + code)


def _role_id(code: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, "role:" + code)


def _user_id(username: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, "user:" + username)


def _roster_id(course_id: str, member_id: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, "roster:" + course_id + ":" + member_id)


def _config() -> dict:
    return json.loads((ROOT / "config" / "academy_permissions.json").read_text(encoding="utf-8"))


def upgrade() -> None:
    cfg = _config()
    org_id = cfg["org_id"]
    site_id = cfg["site_id"]

    permissions = op.create_table(
        "academy_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_academy_permissions_code"),
    )
    op.create_index("ix_academy_permissions_code", "academy_permissions", ["code"])

    roles = op.create_table(
        "iam_roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_iam_roles_code"),
    )
    op.create_index("ix_iam_roles_code", "iam_roles", ["code"])

    role_permissions = op.create_table(
        "iam_role_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("iam_roles.id"), nullable=False),
        sa.Column("permission_id", sa.Uuid(), sa.ForeignKey("academy_permissions.id"), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_iam_role_permissions_role_permission"),
    )
    op.create_index("ix_iam_role_permissions_role_id", "iam_role_permissions", ["role_id"])
    op.create_index("ix_iam_role_permissions_permission_id", "iam_role_permissions", ["permission_id"])

    users = op.create_table(
        "iam_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("iam_roles.id"), nullable=False),
        sa.UniqueConstraint("username", name="uq_iam_users_username"),
    )
    op.create_index("ix_iam_users_username", "iam_users", ["username"])
    op.create_index("ix_iam_users_role_id", "iam_users", ["role_id"])

    roster = op.create_table(
        "academy_roster_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("site_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("course_id", sa.String(length=50), nullable=False),
        sa.Column("member_id", sa.String(length=50), nullable=False),
        sa.Column("member_name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("manager_id", sa.Uuid(), sa.ForeignKey("iam_users.id"), nullable=False),
        sa.UniqueConstraint("course_id", "member_id", name="uq_academy_roster_course_member"),
    )
    op.create_index("ix_academy_roster_course_id", "academy_roster_members", ["course_id"])
    op.create_index("ix_academy_roster_member_id", "academy_roster_members", ["member_id"])
    op.create_index("ix_academy_roster_manager_id", "academy_roster_members", ["manager_id"])

    op.bulk_insert(
        permissions,
        [
            {
                "id": _permission_id(item["code"]),
                "org_id": org_id,
                "site_id": site_id,
                "created_by": CREATED_BY,
                "code": item["code"],
                "name": item["name"],
                "module": "academy",
                "description": item.get("description", ""),
            }
            for item in cfg["permissions"]
        ],
    )
    op.bulk_insert(
        roles,
        [
            {
                "id": _role_id(item["code"]),
                "org_id": org_id,
                "site_id": site_id,
                "created_by": CREATED_BY,
                "code": item["code"],
                "name": item["name"],
                "description": item.get("description", ""),
            }
            for item in cfg["roles"]
        ],
    )
    op.bulk_insert(
        role_permissions,
        [
            {
                "id": uuid.uuid5(NAMESPACE, "role-permission:" + role["code"] + ":" + code),
                "org_id": org_id,
                "site_id": site_id,
                "created_by": CREATED_BY,
                "role_id": _role_id(role["code"]),
                "permission_id": _permission_id(code),
                "scope": scope,
            }
            for role in cfg["roles"]
            for code, scope in role["permissions"].items()
        ],
    )
    op.bulk_insert(
        users,
        [
            {
                "id": _user_id(item["username"]),
                "org_id": org_id,
                "site_id": site_id,
                "created_by": CREATED_BY,
                "username": item["username"],
                "display_name": item["display_name"],
                "role_id": _role_id(item["role_code"]),
            }
            for item in cfg["users"]
        ],
    )
    op.bulk_insert(
        roster,
        [
            {
                "id": _roster_id(item["course_id"], item["member_id"]),
                "org_id": org_id,
                "site_id": site_id,
                "created_by": CREATED_BY,
                "course_id": item["course_id"],
                "member_id": item["member_id"],
                "member_name": item["member_name"],
                "phone": item["phone"],
                "manager_id": _user_id(item["manager_username"]),
            }
            for item in cfg["roster"]
        ],
    )


def downgrade() -> None:
    op.drop_table("academy_roster_members")
    op.drop_table("iam_users")
    op.drop_table("iam_role_permissions")
    op.drop_table("iam_roles")
    op.drop_table("academy_permissions")
