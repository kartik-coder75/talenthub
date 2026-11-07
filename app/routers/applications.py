from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_company, get_current_student, get_current_user
from app.models import Company, Student, User
from app.schemas import ApplicationCreate, ApplicationDetailOut, ApplicationOut
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_for_job(data: ApplicationCreate, student: Student = Depends(get_current_student),
                  db: Session = Depends(get_db)):
    return ApplicationService(db).apply(student, data.job_id)


@router.get("/me", response_model=list[ApplicationOut])
def my_applications(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return ApplicationService(db).list_for_student(student)


@router.get("/{application_id}", response_model=ApplicationDetailOut)
def get_application(application_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return ApplicationService(db).get_for_user(user, application_id)


@router.post("/{application_id}/shortlist", response_model=ApplicationOut)
def shortlist(application_id: int, company: Company = Depends(get_current_company),
              db: Session = Depends(get_db)):
    return ApplicationService(db).shortlist(company, application_id)


@router.post("/{application_id}/reject", response_model=ApplicationOut)
def reject(application_id: int, company: Company = Depends(get_current_company),
           db: Session = Depends(get_db)):
    return ApplicationService(db).reject(company, application_id)
