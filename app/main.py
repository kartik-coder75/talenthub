from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (register tables on Base.metadata)
from app.database import Base, SessionLocal, engine
from app.exceptions import AppError
from app.routers import applications, auth, companies, interviews, jobs, offers, reports, students
from app.services.auth_service import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        AuthService(db).ensure_coordinator()
    yield


app = FastAPI(
    title="TalentHub",
    description="Campus placement management: eligibility, applications, interviews, offers and reports.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)


for r in (auth.router, students.router, companies.router, jobs.router,
          applications.router, interviews.router, offers.router, reports.router):
    app.include_router(r)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# ---------- Front end (plain HTML/CSS/JS) ----------
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")
