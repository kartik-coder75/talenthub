# TalentHub – Campus Placement Management

Students apply for jobs, companies shortlist / interview / issue offers, and the placement
coordinator monitors placement statistics.

## Architecture 

```
app/
├── routers/        Router layer      – HTTP in/out, auth dependencies, no business logic
├── services/       Service layer     – business rules (eligibility, status flow, accepting offers)
├── repositories/   Repository layer  – all database reads/writes
├── models.py       Model/DB layer    – Student, Company, JobListing, Application, Interview, Offer, User
├── schemas.py      Pydantic request/response models + input validation
├── security.py     Password hashing (PBKDF2-SHA256) and JWT
├── static/         Front end: index.html, style.css, app.js (plain HTML/CSS/JS, no npm)
└── main.py         App factory, error handler, table creation, coordinator seeding
```

## Roles

| Role | Can do |
|---|---|
| Student | See open / eligible jobs, check eligibility, apply, track applications, accept or decline offers |
| Company | Post and close jobs, view applicants, shortlist / reject, schedule interviews, record results, issue offers |
| Coordinator | List students, correct academic records, view placement statistics and placed-students report |

## Business rules implemented

* **Eligibility**: `CGPA >= min_cgpa`, `active_backlogs <= max_active_backlogs`, and branch is in the job's
  allowed branches (empty list = all branches). Boundary values are eligible (CGPA 7.0 for min 7.0; 2 backlogs for max 2).
* **Apply**: job must be open, student not already placed, no duplicate application, student must be eligible.
* **Status flow**: `APPLIED → SHORTLISTED → INTERVIEW_SCHEDULED → SELECTED → OFFERED → OFFER_ACCEPTED`
  (side exits: `REJECTED`, `NOT_SELECTED`, `OFFER_DECLINED`, `OFFER_WITHDRAWN`). Steps cannot be skipped.
* **Interviews** must be scheduled in the future; a result (`PASSED` / `FAILED`) can be recorded once.
* **Accepting an offer** marks the student as placed and automatically withdraws their other outstanding offers.
  Placed students cannot apply to more jobs.
* **Statistics** count a student as placed only after an offer is accepted.

### Assumptions (the Word file says rules "must follow the approved requirements")
Some rules were left open, so these were chosen and are easy to change in `app/services/`:
branch restriction is optional per job; one placement per student; the coordinator account is seeded
(cannot self-register); students self-report CGPA/backlogs at registration but **only the coordinator can
change them afterwards**.

## Run the application

**Requirements:** Python 3.10+

```bash
# 1. unzip and enter the project
unzip talenthub.zip && cd talenthub

# 2. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. (recommended) set a secret key - see .env.example for all settings
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
#   Windows PowerShell:  $env:SECRET_KEY = "any-long-random-string"

# 5. start the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/** for the web application (redirects to `/ui/`), or
**http://127.0.0.1:8000/docs** for the Swagger API explorer. The SQLite file `talenthub.db` and all tables are
created automatically on first start.

Default coordinator login: `coordinator` / `Coordinator@123` (override with `COORDINATOR_USERNAME` /
`COORDINATOR_PASSWORD`).

### Using the web application
* **Student**: sign up, browse jobs (tick *Only jobs I'm eligible for*), check eligibility, apply, track
  applications, accept or decline offers.
* **Company**: sign up, post a job, then *My jobs -> View applicants* to shortlist, schedule interviews,
  record results and issue offers.
* **Coordinator**: log in with `coordinator` / `Coordinator@123` for statistics, the placed-students
  report, and to correct student academic records.

Tip: use a different browser (or a private window) per role so you can stay logged in as all three.

### Try it in Swagger UI
1. `POST /auth/register/student` and `POST /auth/register/company`.
2. Click **Authorize** (top right) and enter a username/password. Log in as the company first.
3. Company: `POST /jobs`, later `POST /applications/{id}/shortlist`, `/interview`, `/interview/result`, `/offer`.
4. Re-authorize as the student: `GET /jobs?eligible_only=true`, `POST /applications`, `POST /offers/{id}/accept`.
5. Re-authorize as `coordinator`: `GET /reports/placement-statistics`.

### Or run the scripted example scenario (ABC Technologies / Rahul)
With the server running, in a second terminal:
```bash
python scripts/demo_flow.py
```

## Run the tests
```bash
pytest -v
```
41 tests cover eligibility boundary values, the full happy path, validation errors, business-rule
violations, authentication, and role/ownership authorization. Tests use an in-memory database and
never touch `talenthub.db`.

## API summary

| Method & path | Who | Purpose |
|---|---|---|
| `POST /auth/register/student` · `/auth/register/company` | public | Register |
| `POST /auth/login` · `GET /auth/me` | any | Get JWT / current user |
| `GET /students/me` · `PATCH /students/me` | student | Own profile (name only) |
| `GET /students` · `PATCH /students/{id}/academic-record` | coordinator | List / correct student data |
| `POST /jobs` · `POST /jobs/{id}/close` · `GET /jobs/{id}/applications` | company | Manage own jobs |
| `GET /jobs[?eligible_only=true]` · `GET /jobs/{id}` | any | Browse open jobs |
| `GET /jobs/{id}/eligibility` | student | Eligibility check with reasons |
| `POST /applications` · `GET /applications/me` | student | Apply / list own applications |
| `GET /applications/{id}` | owner student, owning company, coordinator | Detail incl. interview & offer |
| `POST /applications/{id}/shortlist` · `/reject` | company | Shortlist / reject |
| `POST·GET /applications/{id}/interview` · `PUT …/interview/result` | company (GET: any with access) | Interviews |
| `POST /applications/{id}/offer` | company | Issue offer (optional custom package) |
| `GET /offers/me` · `POST /offers/{id}/accept` · `/decline` | student | Respond to offers |
| `GET /reports/placement-statistics` · `/reports/placed-students` | coordinator | Reports |

## Production notes
* Set a strong `SECRET_KEY` and change the coordinator password.
* For PostgreSQL/MySQL set `DATABASE_URL` (and install the driver); use Alembic for schema changes
  instead of the automatic `create_all`.
* Serve behind HTTPS and add rate limiting on `/auth/login`.
