"""The UI is served by FastAPI, and the API returns what the UI needs to render."""
from tests.conftest import make_company, make_job, make_student


def test_root_redirects_to_ui_and_ui_assets_are_served(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "/ui/"
    assert "TalentHub" in client.get("/ui/").text
    assert client.get("/ui/app.js").status_code == 200
    assert client.get("/ui/style.css").status_code == 200


def test_api_docs_still_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_application_payload_includes_student_and_job_details(client):
    stu_h, _ = make_student(client)
    c = make_company(client)
    job = make_job(client, c)
    assert job["company_name"] == "ABC Technologies"
    client.post("/applications", json={"job_id": job["id"]}, headers=stu_h)

    row = client.get(f"/jobs/{job['id']}/applications", headers=c).json()[0]
    assert row["student"]["name"] == "Rahul" and row["student"]["cgpa"] == 8.2
    assert row["job"]["title"] == "Software Developer"
    assert row["interview"] is None and row["offer"] is None
