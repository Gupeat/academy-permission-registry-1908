from __future__ import annotations

from tests.test_403_matrix import ROUTES


def _status(client, actor, method, path):
    return client.request(method, path, headers={"X-User-Name": actor}).status_code


def test_operations_supervisor_can_call_every_academy_route(client):
    for method, path, _required in ROUTES:
        assert _status(client, "ops_supervisor", method, path) == 200, path


def test_operations_specialist_has_eight_permissions_and_three_denials(client):
    allowed = {
        "academy.course.read",
        "academy.course.edit",
        "academy.session.manage",
        "academy.instructor.manage",
        "academy.application.review",
        "academy.roster.read",
        "academy.learning.correct",
        "academy.review.moderate",
    }
    for method, path, required in ROUTES:
        expected = 200 if required in allowed else 403
        assert _status(client, "ops_specialist", method, path) == expected, (path, required)


def test_member_manager_has_three_permissions(client):
    allowed = {"academy.course.read", "academy.roster.read", "academy.stats.read"}
    for method, path, required in ROUTES:
        expected = 200 if required in allowed else 403
        assert _status(client, "manager_a", method, path) == expected, (path, required)


def test_front_desk_has_two_permissions_and_masked_phone(client):
    allowed = {"academy.course.read", "academy.roster.read"}
    for method, path, required in ROUTES:
        expected = 200 if required in allowed else 403
        assert _status(client, "front_desk", method, path) == expected, (path, required)
    response = client.get("/api/v1/academy/rosters/course-001", headers={"X-User-Name": "front_desk"})
    members = response.json()["members"]
    assert len(members) == 4
    assert {member["phone"] for member in members} == {"*******0001", "*******0002", "*******0003", "*******0004"}
    assert all(member["masked"] is True for member in members)


def test_member_manager_own_scope_filters_roster(client):
    expected = {
        "manager_a": {"m-001", "m-002"},
        "manager_b": {"m-003", "m-004"},
    }
    for actor, member_ids in expected.items():
        response = client.get("/api/v1/academy/rosters/course-001", headers={"X-User-Name": actor})
        assert response.status_code == 200
        assert {member["member_id"] for member in response.json()["members"]} == member_ids


def test_member_manager_cannot_read_out_of_scope_member(client):
    denied = client.get(
        "/api/v1/academy/rosters/course-001/members/m-003", headers={"X-User-Name": "manager_a"}
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "member_scope_denied"
    allowed = client.get(
        "/api/v1/academy/rosters/course-001/members/m-001", headers={"X-User-Name": "manager_a"}
    )
    assert allowed.status_code == 200
    assert allowed.json()["member"]["phone"] == "13800000001"


def test_operations_specialist_sees_full_phone_and_front_desk_does_not(client):
    full = client.get("/api/v1/academy/rosters/course-001", headers={"X-User-Name": "ops_specialist"})
    assert full.json()["members"][0]["phone"] == "13800000001"
    single = client.get(
        "/api/v1/academy/rosters/course-001/members/m-001", headers={"X-User-Name": "front_desk"}
    )
    assert single.status_code == 200
    assert single.json()["member"]["phone"] == "*******0001"
