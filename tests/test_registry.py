from __future__ import annotations

import dataclasses

from sqlalchemy import delete, func, select, update

from app.models import AcademyPermission, IamRole, IamRolePermission
from app.permissions import (
    REQUIRED_MAPPING,
    REQUIRED_PERMISSIONS,
    REQUIRED_ROLE_NAMES,
    load_registry,
    validate_registry,
)
from scripts.check_registry import database_errors


def test_config_has_exactly_eleven_task_permissions():
    registry = load_registry()
    assert [item.code for item in registry.permissions] == list(REQUIRED_PERMISSIONS)
    assert validate_registry(registry) == []


def test_config_has_six_roles_and_exact_default_mapping():
    registry = load_registry()
    assert [role.code for role in registry.roles] == list(REQUIRED_ROLE_NAMES)
    assert {role.code: role.permissions for role in registry.roles} == REQUIRED_MAPPING


def test_migration_seeds_eleven_permissions(session_factory):
    with session_factory() as session:
        active = session.scalar(
            select(func.count()).select_from(AcademyPermission).where(AcademyPermission.deleted_at.is_(None))
        )
        codes = session.scalars(select(AcademyPermission.code).order_by(AcademyPermission.code)).all()
    assert active == 11
    assert sorted(codes) == sorted(REQUIRED_PERMISSIONS)


def test_migration_seeds_six_roles_and_twenty_four_links(session_factory):
    with session_factory() as session:
        roles = session.scalar(select(func.count()).select_from(IamRole).where(IamRole.deleted_at.is_(None)))
        links = session.scalar(
            select(func.count()).select_from(IamRolePermission).where(IamRolePermission.deleted_at.is_(None))
        )
    assert roles == 6
    assert links == 24


def test_config_tamper_extra_permission_is_rejected():
    registry = load_registry()
    extra = dataclasses.replace(registry.permissions[0], code="academy.extra.permission", name="多余权限")
    tampered = dataclasses.replace(registry, permissions=registry.permissions + (extra,))
    errors = validate_registry(tampered)
    assert any("permission set mismatch" in error for error in errors)


def test_config_tamper_mapping_is_rejected():
    registry = load_registry()
    roles = list(registry.roles)
    specialist = roles[0]
    roles[0] = dataclasses.replace(specialist, permissions={**specialist.permissions, "academy.course.publish": "all"})
    errors = validate_registry(dataclasses.replace(registry, roles=tuple(roles)))
    assert any("operations_specialist mapping mismatch" in error for error in errors)


def test_database_tamper_is_detected_and_rolled_back(engine):
    registry = load_registry()
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            permission_id = connection.execute(
                select(AcademyPermission.id).where(AcademyPermission.code == "academy.stats.read")
            ).scalar_one()
            connection.execute(delete(IamRolePermission).where(IamRolePermission.permission_id == permission_id))
            connection.execute(delete(AcademyPermission).where(AcademyPermission.id == permission_id))
            errors = database_errors(registry, connection)
            assert any("database permission set mismatch" in error for error in errors)
        finally:
            transaction.rollback()
    with engine.connect() as connection:
        assert database_errors(registry, connection) == []
        assert connection.execute(
            select(func.count()).select_from(AcademyPermission).where(AcademyPermission.deleted_at.is_(None))
        ).scalar_one() == 11


def test_database_role_name_tamper_is_detected_and_rolled_back(engine):
    registry = load_registry()
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(update(IamRole).where(IamRole.code == "auditor").values(name="审计员改名"))
            errors = database_errors(registry, connection)
            assert any("database role auditor name" in error for error in errors)
        finally:
            transaction.rollback()
    with engine.connect() as connection:
        assert database_errors(registry, connection) == []
