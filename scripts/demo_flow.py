"""Runs the ABC Technologies / Rahul scenario against a running server.

Usage:  python scripts/demo_flow.py [base_url]
Needs the server to be running (see README).  Uses only the standard library.
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SUFFIX = datetime.now().strftime("%H%M%S")  # makes usernames unique across runs


def call(method, path, body=None, token=None, form=False):
    data, headers = None, {}
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  !! {method} {path} -> {e.code} {e.read().decode()}")
        raise SystemExit(1)


def login(u, p):
    return call("POST", "/auth/login", {"username": u, "password": p}, form=True)["access_token"]


def step(msg):
    print(f"\n==> {msg}")


pw = "Password@123"
step("Register student Rahul (CGPA 8.2, 1 backlog) and company ABC Technologies")
call("POST", "/auth/register/student", {"username": f"rahul{SUFFIX}", "password": pw, "name": "Rahul",
                                         "branch": "CSE", "cgpa": 8.2, "active_backlogs": 1})
call("POST", "/auth/register/company", {"username": f"abc{SUFFIX}", "password": pw,
                                         "name": "ABC Technologies", "industry": "IT"})
stu, com = login(f"rahul{SUFFIX}", pw), login(f"abc{SUFFIX}", pw)

step("Company posts a job: min CGPA 7.0, max 2 active backlogs")
job = call("POST", "/jobs", {"title": "Software Developer", "package_lpa": 8, "min_cgpa": 7.0,
                              "max_active_backlogs": 2}, com)
print("  job id:", job["id"])

step("Rahul checks eligibility and applies")
print(" ", call("GET", f"/jobs/{job['id']}/eligibility", token=stu))
app = call("POST", "/applications", {"job_id": job["id"]}, stu)

step("Company shortlists, schedules interview, records PASSED")
call("POST", f"/applications/{app['id']}/shortlist", token=com)
when = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
call("POST", f"/applications/{app['id']}/interview", {"scheduled_at": when, "mode": "ONLINE"}, com)
call("PUT", f"/applications/{app['id']}/interview/result", {"result": "PASSED", "remarks": "Strong"}, com)

step("Company issues offer; Rahul accepts")
offer = call("POST", f"/applications/{app['id']}/offer", {}, com)
print(" ", call("POST", f"/offers/{offer['id']}/accept", token=stu))

step("Coordinator views placement statistics")
coord = login("coordinator", "Coordinator@123")
print(json.dumps(call("GET", "/reports/placement-statistics", token=coord), indent=2))
