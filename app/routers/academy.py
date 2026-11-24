"""Academy business endpoints, each protected by require_academy_perm(code)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AcademyPrincipal, require_academy_perm, require_member_scope
from app.models import AcademyRosterMember
from app.roster import serialize_member

router = APIRouter(prefix="/api/v1/academy", tags=["academy"])

ROSTER_READ = "academy.roster.read"


def _ok(principal: AcademyPrincipal) -> dict[str, object]:
    return {
        "ok": True,
        "required": principal.permission.code,
        "scope": principal.scope,
        "actor": principal.user.username,
        "role": principal.role.code,
    }


@router.get("/courses")
def list_courses(principal: AcademyPrincipal = Depends(require_academy_perm("academy.course.read"))):
    return {**_ok(principal), "items": [{"course_id": "course-001", "title": "学院运营实战（虚构）"}], "total": 1}


@router.post("/courses/{course_id}")
def edit_course(course_id: str, principal: AcademyPrincipal = Depends(require_academy_perm("academy.course.edit"))):
    return {**_ok(principal), "course_id": course_id, "action": "edit"}


@router.post("/courses/{course_id}/publish")
def publish_course(course_id: str, principal: AcademyPrincipal = Depends(require_academy_perm("academy.course.publish"))):
    return {**_ok(principal), "course_id": course_id, "action": "publish"}


@router.post("/sessions")
def manage_session(principal: AcademyPrincipal = Depends(require_academy_perm("academy.session.manage"))):
    return {**_ok(principal), "action": "manage_session"}


@router.post("/instructors")
def manage_instructor(principal: AcademyPrincipal = Depends(require_academy_perm("academy.instructor.manage"))):
    return {**_ok(principal), "action": "manage_instructor"}


@router.post("/applications/{application_id}/review")
def review_application(
    application_id: str,
    principal: AcademyPrincipal = Depends(require_academy_perm("academy.application.review")),
):
    return {**_ok(principal), "application_id": application_id, "action": "review"}


@router.get("/rosters/{course_id}")
def list_roster(
    course_id: str,
    principal: AcademyPrincipal = Depends(require_academy_perm(ROSTER_READ)),
    db: Session = Depends(get_db),
):
    stmt = select(AcademyRosterMember).where(
        AcademyRosterMember.course_id == course_id,
        AcademyRosterMember.deleted_at.is_(None),
    )
    if principal.scope == "own":
        stmt = stmt.where(AcademyRosterMember.manager_id == principal.user.id)
    rows = db.scalars(stmt.order_by(AcademyRosterMember.member_id)).all()
    masked = principal.scope == "masked_phone"
    return {**_ok(principal), "course_id": course_id, "members": [serialize_member(row, masked=masked) for row in rows]}


@router.get("/rosters/{course_id}/members/{member_id}")
def get_roster_member(
    course_id: str,
    member_id: str,
    principal: AcademyPrincipal = Depends(require_academy_perm(ROSTER_READ)),
    db: Session = Depends(get_db),
):
    member = db.scalar(
        select(AcademyRosterMember).where(
            AcademyRosterMember.course_id == course_id,
            AcademyRosterMember.member_id == member_id,
            AcademyRosterMember.deleted_at.is_(None),
        )
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="roster member not found")
    require_member_scope(principal, member)
    return {**_ok(principal), "member": serialize_member(member, masked=principal.scope == "masked_phone")}


@router.post("/learning-records/{record_id}/correct")
def correct_learning_record(
    record_id: str,
    principal: AcademyPrincipal = Depends(require_academy_perm("academy.learning.correct")),
):
    return {**_ok(principal), "record_id": record_id, "action": "correct"}


@router.post("/reviews/{review_id}/moderate")
def moderate_review(
    review_id: str,
    principal: AcademyPrincipal = Depends(require_academy_perm("academy.review.moderate")),
):
    return {**_ok(principal), "review_id": review_id, "action": "moderate"}


@router.get("/stats")
def stats(principal: AcademyPrincipal = Depends(require_academy_perm("academy.stats.read"))):
    return {
        **_ok(principal),
        "stats": {"courses": 1, "members": 4, "attendance_rate": 0.75},
        "notice": "fictional demo data",
    }


@router.put("/entitlements/config")
def configure_entitlement(principal: AcademyPrincipal = Depends(require_academy_perm("academy.entitlement.config"))):
    return {**_ok(principal), "action": "configure_entitlement"}
