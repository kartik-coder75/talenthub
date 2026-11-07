"""End-to-end happy path: the ABC Technologies / Rahul scenario from the requirements."""
from tests.conftest import (advance_to_selected, coordinator, future, make_company,
                            make_job, make_student)


def test_full_placement_flow_and_statistics(client):
    rahul_h, _ = make_student(client)
    make_student(client, username="priya", name="Priya", cgpa=6.0, backlogs=0, branch="ECE")
    abc_h = make_company(client)
    job = make_job(client, abc_h)

    # Rahul sees the job as eligible; Priya (CGPA 6.0) does not.
    r = client.get("/jobs?eligible_only=true", headers=rahul_h)
    assert [j["id"] for j in r.json()] == [job["id"]]
    assert client.get(f"/jobs/{job['id']}/eligibility", headers=rahul_h).json()["eligible"] is True

    app_id = advance_to_selected(client, rahul_h, abc_h, job["id"])
    assert client.get(f"/applications/{app_id}", headers=rahul_h).json()["status"] == "SELECTED"

    offer = client.post(f"/applications/{app_id}/offer", headers=abc_h)
    assert offer.status_code == 201 and offer.json()["package_lpa"] == 8.0
    assert offer.json()["status"] == "ISSUED"

    accepted = client.post(f"/offers/{offer.json()['id']}/accept", headers=rahul_h)
    assert accepted.status_code == 200 and accepted.json()["status"] == "ACCEPTED"
    assert client.get("/students/me", headers=rahul_h).json()["is_placed"] is True
    assert client.get(f"/applications/{app_id}", headers=rahul_h).json()["status"] == "OFFER_ACCEPTED"

    coord = coordinator(client)
    stats = client.get("/reports/placement-statistics", headers=coord).json()
    assert stats["total_students"] == 2
    assert stats["placed_students"] == 1
    assert stats["placement_percentage"] == 50.0
    assert stats["offers_accepted"] == 1
    assert stats["highest_package_lpa"] == 8.0
    assert {b["branch"] for b in stats["branch_wise"]} == {"CSE", "ECE"}
    placed = client.get("/reports/placed-students", headers=coord).json()
    assert placed[0]["student_name"] == "Rahul" and placed[0]["company"] == "ABC Technologies"


def test_accepting_one_offer_withdraws_the_others(client):
    stu_h, _ = make_student(client)
    c1, c2 = make_company(client, "comp1", "Company One"), make_company(client, "comp2", "Company Two")
    j1, j2 = make_job(client, c1), make_job(client, c2)
    a1 = advance_to_selected(client, stu_h, c1, j1["id"])
    a2 = advance_to_selected(client, stu_h, c2, j2["id"])
    o1 = client.post(f"/applications/{a1}/offer", headers=c1).json()
    o2 = client.post(f"/applications/{a2}/offer", headers=c2).json()

    assert client.post(f"/offers/{o1['id']}/accept", headers=stu_h).status_code == 200
    offers = {o["id"]: o["status"] for o in client.get("/offers/me", headers=stu_h).json()}
    assert offers == {o1["id"]: "ACCEPTED", o2["id"]: "WITHDRAWN"}


def test_declined_offer_keeps_student_unplaced(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = advance_to_selected(client, stu_h, c, job["id"])
    offer = client.post(f"/applications/{app_id}/offer", headers=c).json()
    assert client.post(f"/offers/{offer['id']}/decline", headers=stu_h).json()["status"] == "DECLINED"
    assert client.get("/students/me", headers=stu_h).json()["is_placed"] is False


def test_custom_offer_package_and_job_closing(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    app_id = advance_to_selected(client, stu_h, c, job["id"])
    offer = client.post(f"/applications/{app_id}/offer", json={"package_lpa": 9.5}, headers=c)
    assert offer.json()["package_lpa"] == 9.5
    assert client.post(f"/jobs/{job['id']}/close", headers=c).json()["is_open"] is False
    assert client.get("/jobs", headers=stu_h).json() == []


def test_coordinator_corrects_academic_record(client):
    stu_h, stu = make_student(client, cgpa=6.5)
    c = make_company(client)
    job = make_job(client, c)
    assert client.get(f"/jobs/{job['id']}/eligibility", headers=stu_h).json()["eligible"] is False
    r = client.patch(f"/students/{stu['id']}/academic-record", json={"cgpa": 7.5}, headers=coordinator(client))
    assert r.status_code == 200 and r.json()["cgpa"] == 7.5
    assert client.get(f"/jobs/{job['id']}/eligibility", headers=stu_h).json()["eligible"] is True
