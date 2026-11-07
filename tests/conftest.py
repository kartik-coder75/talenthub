import os

os.environ["DATABASE_URL"] = "sqlite://"  # must be set before the app is imported

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services.auth_service import AuthService


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    with TestingSession() as db:
        AuthService(db).ensure_coordinator()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- helpers ----------
def login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_student(client, username="rahul", cgpa=8.2, backlogs=1, branch="CSE", name="Rahul"):
    r = client.post("/auth/register/student", json={
        "username": username, "password": "Password@123", "name": name,
        "branch": branch, "cgpa": cgpa, "active_backlogs": backlogs})
    assert r.status_code == 201, r.text
    return login(client, username, "Password@123"), r.json()


def make_company(client, username="abc", name="ABC Technologies"):
    r = client.post("/auth/register/company", json={
        "username": username, "password": "Password@123", "name": name, "industry": "IT"})
    assert r.status_code == 201, r.text
    return login(client, username, "Password@123")


def make_job(client, company_headers, **overrides):
    payload = {"title": "Software Developer", "package_lpa": 8.0, "min_cgpa": 7.0,
               "max_active_backlogs": 2, "allowed_branches": []}
    payload.update(overrides)
    r = client.post("/jobs", json=payload, headers=company_headers)
    assert r.status_code == 201, r.text
    return r.json()


def coordinator(client):
    return login(client, settings.coordinator_username, settings.coordinator_password)


def future(days=2):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def advance_to_selected(client, student_h, company_h, job_id):
    """Apply -> shortlist -> schedule -> pass. Returns the application id."""
    app_id = client.post("/applications", json={"job_id": job_id}, headers=student_h).json()["id"]
    assert client.post(f"/applications/{app_id}/shortlist", headers=company_h).status_code == 200
    assert client.post(f"/applications/{app_id}/interview", json={"scheduled_at": future()},
                       headers=company_h).status_code == 201
    r = client.put(f"/applications/{app_id}/interview/result",
                   json={"result": "PASSED", "remarks": "Good"}, headers=company_h)
    assert r.status_code == 200
    return app_id
