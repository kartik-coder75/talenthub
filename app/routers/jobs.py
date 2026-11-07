from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_company, get_current_student, get_current_user
from app.enums import ApplicationStatus, Role
from app.models import Company, Student, User
from app.schemas import ApplicationOut, EligibilityOut, JobCreate, JobOut
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(data: JobCreate, company: Company = Depends(get_current_company),
               db: Session = Depends(get_db)):
    return JobService(db).create_job(company, data)


@router.get("", response_model=list[JobOut])
def list_open_jobs(eligible_only: bool = False, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """All open jobs. Students can pass `eligible_only=true` to see only jobs they qualify for."""
    student = user.student_profile if user.role == Role.STUDENT else None
    return JobService(db).list_open_jobs(student, eligible_only)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return JobService(db).get_job(job_id)


@router.get("/{job_id}/eligibility", response_model=EligibilityOut)
def check_my_eligibility(job_id: int, student: Student = Depends(get_current_student),
                         db: Session = Depends(get_db)):
    result = JobService(db).check_student_eligibility(student, job_id)
    return EligibilityOut(job_id=job_id, eligible=result.eligible, reasons=result.reasons)


@router.post("/{job_id}/close", response_model=JobOut)
def close_job(job_id: int, company: Company = Depends(get_current_company),
              db: Session = Depends(get_db)):
    return JobService(db).close_job(company, job_id)


@router.get("/{job_id}/applications", response_model=list[ApplicationOut])
def list_job_applications(job_id: int, status: Optional[ApplicationStatus] = None,
                          company: Company = Depends(get_current_company),
                          db: Session = Depends(get_db)):
    return JobService(db).list_applications(company, job_id, status)
