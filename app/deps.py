"""FastAPI authorization dependency used by every academy route."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.iam import get_current_user
from app.models import AcademyPermission, IamRole, IamRolePermission, IamUser


@dataclass(frozen=True)
class AcademyPrincipal:
    user: IamUser
    role: IamRole
    permission: AcademyPermission
    scope: str


def require_academy_perm(code: str):
    """Build a dependency requiring one academy permission code.

    The role-to-permission mapping is read from the database; a missing row
    means 403. This is the only authorization entry point for academy routes.
    """
    if not code.startswith("academy."):
        raise ValueError(f"not an academy permission code: {code}")

    def dependency(
        user: IamUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> AcademyPrincipal:
        permission = db.scalar(
            select(AcademyPermission).where(
                AcademyPermission.code == code,
                AcademyPermission.deleted_at.is_(None),
            )
        )
        link = None
        if permission is not None:
            link = db.scalar(
                select(IamRolePermission).where(
                    IamRolePermission.role_id == user.role_id,
                    IamRolePermission.permission_id == permission.id,
                    IamRolePermission.deleted_at.is_(None),
                )
            )
        if permission is None or link is None or user.role is None or user.role.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "academy_permission_denied", "required": code, "actor": user.username},
            )
        return AcademyPrincipal(user=user, role=user.role, permission=permission, scope=link.scope)

    return dependency


def require_member_scope(principal: AcademyPrincipal | None, member) -> None:
    """Enforce the 'own' data scope on one roster member."""
    if principal is not None and principal.scope == "own" and member.manager_id != principal.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "member_scope_denied", "required": "manager_id=current_user"},
        )
