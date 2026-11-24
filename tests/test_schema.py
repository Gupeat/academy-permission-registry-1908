from __future__ import annotations

import uuid

from sqlalchemy import inspect

STANDARD = {"id", "org_id", "site_id", "created_at", "created_by", "updated_at", "deleted_at"}
TABLES = {
    "academy_permissions",
    "iam_roles",
    "iam_role_permissions",
    "iam_users",
    "academy_roster_members",
}


def test_all_business_tables_have_standard_columns(engine):
    inspector = inspect(engine)
    for table in TABLES:
        columns = {column["name"] for column in inspector.get_columns(table)}
        assert STANDARD <= columns, (table, STANDARD - columns)


def test_uuid_primary_keys_and_soft_delete(engine):
    inspector = inspect(engine)
    for table in TABLES:
        columns = {column["name"]: column for column in inspector.get_columns(table)}
        assert columns["id"]["type"].python_type is uuid.UUID, table
        assert columns["deleted_at"]["nullable"] is True, table


def test_permission_and_role_mapping_columns(engine):
    inspector = inspect(engine)
    permission_columns = {column["name"] for column in inspector.get_columns("academy_permissions")}
    link_columns = {column["name"] for column in inspector.get_columns("iam_role_permissions")}
    roster_columns = {column["name"] for column in inspector.get_columns("academy_roster_members")}
    assert {"code", "name", "module"} <= permission_columns
    assert {"role_id", "permission_id", "scope"} <= link_columns
    assert {"course_id", "member_id", "phone", "manager_id"} <= roster_columns


def test_unique_constraints_for_registry_identity(engine):
    inspector = inspect(engine)
    permission_uniques = {item["name"] for item in inspector.get_unique_constraints("academy_permissions")}
    role_uniques = {item["name"] for item in inspector.get_unique_constraints("iam_roles")}
    link_uniques = {item["name"] for item in inspector.get_unique_constraints("iam_role_permissions")}
    assert "uq_academy_permissions_code" in permission_uniques
    assert "uq_iam_roles_code" in role_uniques
    assert "uq_iam_role_permissions_role_permission" in link_uniques
