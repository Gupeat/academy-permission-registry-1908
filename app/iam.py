"""Minimal S2-IAM stub.

Replace get_current_user with the real S2-IAM adapter; keep the
require_academy_perm(code) signature unchanged.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import IamUser


def get_current_user(
    x_user_name: str | None = Header(default=None, alias="X-User-Name"),
    db: Session = Depends(get_db),
) -> IamUser:
    if not x_user_name:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing X-User-Name (S2-IAM mock)")
    user = db.scalar(select(IamUser).where(IamUser.username == x_user_name, IamUser.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"unknown demo user {x_user_name!r}")
    return user
