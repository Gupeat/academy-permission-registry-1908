"""Relational model for the academy permission registry.

All business tables carry the project-wide columns: UUID id, org_id, site_id,
created_at, created_by, updated_at and deleted_at (soft delete).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StandardColumns:
    org_id: Mapped[str] = mapped_column(String(64), nullable=False)
    site_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AcademyPermission(StandardColumns, Base):
    __tablename__ = "academy_permissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False, default="academy")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class IamRole(StandardColumns, Base):
    __tablename__ = "iam_roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class IamRolePermission(StandardColumns, Base):
    __tablename__ = "iam_role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_iam_role_permissions_role_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("iam_roles.id"), nullable=False, index=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academy_permissions.id"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="all")

    role: Mapped[IamRole] = relationship()
    permission: Mapped[AcademyPermission] = relationship()


class IamUser(StandardColumns, Base):
    __tablename__ = "iam_users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("iam_roles.id"), nullable=False, index=True)

    role: Mapped[IamRole] = relationship()


class AcademyRosterMember(StandardColumns, Base):
    __tablename__ = "academy_roster_members"
    __table_args__ = (
        UniqueConstraint("course_id", "member_id", name="uq_academy_roster_course_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    course_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    member_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    member_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("iam_users.id"), nullable=False, index=True)

    manager: Mapped[IamUser] = relationship()
