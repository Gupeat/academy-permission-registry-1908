from __future__ import annotations

import pytest

ROUTES = [
    ("GET", "/api/v1/academy/courses", "academy.course.read"),
    ("POST", "/api/v1/academy/courses/course-001", "academy.course.edit"),
    ("POST", "/api/v1/academy/courses/course-001/publish", "academy.course.publish"),
    ("POST", "/api/v1/academy/sessions", "academy.session.manage"),
    ("POST", "/api/v1/academy/instructors", "academy.instructor.manage"),
    ("POST", "/api/v1/academy/applications/app-001/review", "academy.application.review"),
    ("GET", "/api/v1/academy/rosters/course-001", "academy.roster.read"),
    ("GET", "/api/v1/academy/rosters/course-001/members/m-001", "academy.roster.read"),
    ("POST", "/api/v1/academy/learning-records/lr-001/correct", "academy.learning.correct"),
    ("POST", "/api/v1/academy/reviews/rv-001/moderate", "academy.review.moderate"),
    ("GET", "/api/v1/academy/stats", "academy.stats.read"),
    ("PUT", "/api/v1/academy/entitlements/config", "academy.entitlement.config"),
]


@pytest.mark.parametrize("actor", ["system_admin", "auditor"])
@pytest.mark.parametrize("method,path,required", ROUTES)
def test_roles_without_academy_permissions_get_403(client, actor, method, path, required):
    response = client.request(method, path, headers={"X-User-Name": actor})
    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "academy_permission_denied"
    assert detail["required"] == required
    assert detail["actor"] == actor


def test_system_admin_has_no_academy_route_allowed(client):
    for method, path, _required in ROUTES:
        assert client.request(method, path, headers={"X-User-Name": "system_admin"}).status_code == 403


def test_missing_or_unknown_mock_identity_is_401(client):
    assert client.get("/api/v1/academy/courses").status_code == 401
    unknown = client.get("/api/v1/academy/courses", headers={"X-User-Name": "nobody"})
    assert unknown.status_code == 401
    assert "unknown demo user" in unknown.json()["detail"]
