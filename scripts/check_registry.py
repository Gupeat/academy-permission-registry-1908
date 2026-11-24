"""Compare the database registry with config and the task's required mapping."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select  # noqa: E402

from app.config import database_url  # noqa: E402
from app.models import AcademyPermission, IamRole, IamRolePermission  # noqa: E402
from app.permissions import Registry, load_registry, validate_registry  # noqa: E402


def database_errors(registry: Registry, connection) -> list[str]:
    errors: list[str] = []
    permission_rows = connection.execute(
        select(AcademyPermission.code, AcademyPermission.name).where(AcademyPermission.deleted_at.is_(None))
    ).all()
    db_permissions = {row.code: row.name for row in permission_rows}
    expected_permissions = {item.code: item.name for item in registry.permissions}
    if set(db_permissions) != set(expected_permissions):
        errors.append(
            "database permission set mismatch: missing="
            f"{sorted(set(expected_permissions) - set(db_permissions))} extra="
            f"{sorted(set(db_permissions) - set(expected_permissions))}"
        )
    for code, name in expected_permissions.items():
        if db_permissions.get(code) not in (None, name):
            errors.append(f"database permission {code} name {db_permissions[code]!r} != {name!r}")

    role_rows = connection.execute(select(IamRole.code, IamRole.name).where(IamRole.deleted_at.is_(None))).all()
    db_roles = {row.code: row.name for row in role_rows}
    expected_roles = {item.code: item.name for item in registry.roles}
    if set(db_roles) != set(expected_roles):
        errors.append(
            "database role set mismatch: missing="
            f"{sorted(set(expected_roles) - set(db_roles))} extra="
            f"{sorted(set(db_roles) - set(expected_roles))}"
        )
    for code, name in expected_roles.items():
        if db_roles.get(code) not in (None, name):
            errors.append(f"database role {code} name {db_roles[code]!r} != {name!r}")

    links = connection.execute(
        select(IamRole.code, AcademyPermission.code, IamRolePermission.scope)
        .join(IamRole, IamRole.id == IamRolePermission.role_id)
        .join(AcademyPermission, AcademyPermission.id == IamRolePermission.permission_id)
        .where(IamRolePermission.deleted_at.is_(None))
    ).all()
    db_mapping: dict[str, dict[str, str]] = {code: {} for code in expected_roles}
    for role_code, permission_code, scope in links:
        db_mapping.setdefault(role_code, {})[permission_code] = scope
    expected_mapping = {role.code: dict(role.permissions) for role in registry.roles}
    if db_mapping != expected_mapping:
        for role_code in sorted(set(db_mapping) | set(expected_mapping)):
            if db_mapping.get(role_code) != expected_mapping.get(role_code):
                errors.append(
                    f"database role {role_code} mapping mismatch: "
                    f"db={db_mapping.get(role_code)!r} expected={expected_mapping.get(role_code)!r}"
                )
    return errors


def main() -> int:
    registry = load_registry()
    errors = validate_registry(registry)
    if errors:
        print("config check FAILED")
        for error in errors:
            print("-", error)
        return 1
    engine = create_engine(database_url(), future=True)
    with engine.connect() as connection:
        errors = database_errors(registry, connection)
    engine.dispose()
    if errors:
        print("database check FAILED")
        for error in errors:
            print("-", error)
        return 1
    print(f"registry OK: {len(registry.permissions)} permissions, {len(registry.roles)} roles, "
          f"{sum(len(role.permissions) for role in registry.roles)} role-permission links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
