"""Roster serialization and phone masking."""
from __future__ import annotations

from app.models import AcademyRosterMember


def mask_phone(phone: str) -> str:
    return "*******" + phone[-4:] if len(phone) >= 4 else "****"


def serialize_member(member: AcademyRosterMember, *, masked: bool) -> dict[str, object]:
    return {
        "member_id": member.member_id,
        "member_name": member.member_name,
        "phone": mask_phone(member.phone) if masked else member.phone,
        "masked": masked,
        "manager_id": str(member.manager_id),
    }
