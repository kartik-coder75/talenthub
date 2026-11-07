"""Negative paths: invalid input, business-rule violations, authentication and authorization."""
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import (advance_to_selected, coordinator, future, make_company,
                            make_job, make_student)


# ---------- validation ----------
@pytest.mark.parametrize("cgpa", [-0.1, 10.1])
def test_cgpa_out_of_range_rejected(client, cgpa):
    r = client.post("/auth/register/student", json={
        "username": "bad", "password": "Password@123", "name": "X", "branch": "CSE", "cgpa": cgpa})
    assert r.status_code == 422


def test_short_password_and_negative_backlogs_rejected(client):
    base = {"username": "bad", "name": "X", "branch": "CSE", "cgpa": 7}
    assert client.post("/auth/register/student", json={**base, "password": "short"}).status_code == 422
    assert client.post("/auth/register/student",
                       json={**base, "password": "Password@123", "active_backlogs": -1}).status_code == 422


def test_invalid_job_payload_rejected(client):
    c = make_company(client)
    r = client.post("/jobs", json={"title": "x", "package_lpa": 0}, headers=c)
    assert r.status_code == 422


# ---------- authentication ----------
def test_duplicate_username_conflict(client):
    make_student(client)
    r = client.post("/auth/register/student", json={
        "username": "rahul", "password": "Password@123", "name": "Other", "branch": "CSE", "cgpa": 7})
    assert r.status_code == 409


def test_wrong_password_and_unknown_user_get_same_401(client):
    make_student(client)
    bad = client.post("/auth/login", data={"username": "rahul", "password": "wrong-password"})
    unknown = client.post("/auth/login", data={"username": "ghost", "password": "wrong-password"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()


def test_missing_or_tampered_token_is_401(client):
    assert client.get("/jobs").status_code == 401
    assert client.get("/jobs", headers={"Authorization": "Bearer not.a.token"}).status_code == 401


# ---------- authorization ----------
def test_role_restrictions(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    assert client.post("/jobs", json={"title": "t", "package_lpa": 5}, headers=stu_h).status_code == 403
    assert client.post("/applications", json={"job_id": job["id"]}, headers=c).status_code == 403
    assert client.get("/reports/placement-statistics", headers=stu_h).status_code == 403
    assert client.get("/reports/placement-statistics", headers=c).status_code == 403
    assert client.get("/students", headers=stu_h).status_code == 403
    assert client.patch("/students/1/academic-record", json={"cgpa": 10}, headers=stu_h).status_code == 403


def test_company_cannot_touch_another_companys_data(client):
    stu_h, _ = make_student(client)
    owner, intruder = make_company(client, "owner", "Owner Co"), make_company(client, "intruder", "Intruder Co")
    job = make_job(client, owner)
    app_id = client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).json()["id"]

    assert client.get(f"/jobs/{job['id']}/applications", headers=intruder).status_code == 403
    assert client.post(f"/jobs/{job['id']}/close", headers=intruder).status_code == 403
    assert client.post(f"/applications/{app_id}/shortlist", headers=intruder).status_code == 403
    assert client.get(f"/applications/{app_id}", headers=intruder).status_code == 403


def test_student_cannot_see_or_accept_anothers_records(client):
    rahul_h, _ = make_student(client)
    other_h, _ = make_student(client, "other", name="Other")
    c = make_company(client)
    job = make_job(client, c)
    app_id = advance_to_selected(client, rahul_h, c, job["id"])
    offer = client.post(f"/applications/{app_id}/offer", headers=c).json()

    assert client.get(f"/applications/{app_id}", headers=other_h).status_code == 403
    assert client.post(f"/offers/{offer['id']}/accept", headers=other_h).status_code == 403


# ---------- eligibility / application rules ----------
def test_ineligible_student_cannot_apply(client):
    stu_h, _ = make_student(client, cgpa=6.99)
    c = make_company(client)
    job = make_job(client, c)
    r = client.post("/applications", json={"job_id": job["id"]}, headers=stu_h)
    assert r.status_code == 400 and "CGPA" in r.json()["detail"]


def test_too_many_backlogs_cannot_apply(client):
    stu_h, _ = make_student(client, backlogs=3)
    job = make_job(client, make_company(client))
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 400


def test_boundary_student_can_apply(client):
    stu_h, _ = make_student(client, cgpa=7.0, backlogs=2)
    job = make_job(client, make_company(client))
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 201


def test_wrong_branch_cannot_apply(client):
    stu_h, _ = make_student(client, branch="MECH")
    job = make_job(client, make_company(client), allowed_branches=["CSE", "IT"])
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 400


def test_duplicate_application_conflict(client):
    stu_h, _ = make_student(client)
    job = make_job(client, make_company(client))
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 201
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 409


def test_apply_to_closed_or_missing_job(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    client.post(f"/jobs/{job['id']}/close", headers=c)
    assert client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).status_code == 400
    assert client.post("/applications", json={"job_id": 9999}, headers=stu_h).status_code == 404


def test_placed_student_cannot_apply_again(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    j1, j2 = make_job(client, c), make_job(client, c, title="Second role")
    app_id = advance_to_selected(client, stu_h, c, j1["id"])
    offer = client.post(f"/applications/{app_id}/offer", headers=c).json()
    client.post(f"/offers/{offer['id']}/accept", headers=stu_h)
    assert client.post("/applications", json={"job_id": j2["id"]}, headers=stu_h).status_code == 400


# ---------- workflow ordering ----------
def test_cannot_skip_workflow_steps(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).json()["id"]

    # APPLIED -> cannot interview or offer yet
    assert client.post(f"/applications/{app_id}/interview", json={"scheduled_at": future()},
                       headers=c).status_code == 400
    assert client.post(f"/applications/{app_id}/offer", headers=c).status_code == 400
    assert client.put(f"/applications/{app_id}/interview/result", json={"result": "PASSED"},
                      headers=c).status_code == 400

    client.post(f"/applications/{app_id}/shortlist", headers=c)
    assert client.post(f"/applications/{app_id}/shortlist", headers=c).status_code == 400  # twice
    assert client.post(f"/applications/{app_id}/offer", headers=c).status_code == 400  # no interview


def test_interview_in_the_past_rejected(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).json()["id"]
    client.post(f"/applications/{app_id}/shortlist", headers=c)
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert client.post(f"/applications/{app_id}/interview", json={"scheduled_at": past},
                       headers=c).status_code == 400


def test_failed_interview_blocks_offer(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = client.post("/applications", json={"job_id": job["id"]}, headers=stu_h).json()["id"]
    client.post(f"/applications/{app_id}/shortlist", headers=c)
    client.post(f"/applications/{app_id}/interview", json={"scheduled_at": future()}, headers=c)
    r = client.put(f"/applications/{app_id}/interview/result", json={"result": "FAILED"}, headers=c)
    assert r.json()["result"] == "FAILED"
    assert client.post(f"/applications/{app_id}/offer", headers=c).status_code == 400
    # result cannot be recorded twice, and PENDING is not a valid result
    assert client.put(f"/applications/{app_id}/interview/result", json={"result": "PASSED"},
                      headers=c).status_code == 400
    assert client.put(f"/applications/{app_id}/interview/result", json={"result": "PENDING"},
                      headers=c).status_code == 422


def test_offer_cannot_be_answered_twice(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = advance_to_selected(client, stu_h, c, job["id"])
    offer = client.post(f"/applications/{app_id}/offer", headers=c).json()
    assert client.post(f"/applications/{app_id}/offer", headers=c).status_code == 400  # duplicate offer
    assert client.post(f"/offers/{offer['id']}/accept", headers=stu_h).status_code == 200
    assert client.post(f"/offers/{offer['id']}/accept", headers=stu_h).status_code == 400
    assert client.post(f"/offers/{offer['id']}/decline", headers=stu_h).status_code == 400
    assert client.post("/offers/9999/accept", headers=stu_h).status_code == 404


def test_statistics_with_no_students_has_no_division_error(client):
    stats = client.get("/reports/placement-statistics", headers=coordinator(client)).json()
    assert stats["placement_percentage"] == 0.0 and stats["average_package_lpa"] == 0.0
