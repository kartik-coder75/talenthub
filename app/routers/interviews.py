from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_company, get_current_user
from app.models import Company, User
from app.schemas import InterviewCreate, InterviewOut, InterviewResultUpdate
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/applications/{application_id}/interview", tags=["Interviews"])


@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def schedule_interview(application_id: int, data: InterviewCreate,
                       company: Company = Depends(get_current_company), db: Session = Depends(get_db)):
    return InterviewService(db).schedule(company, application_id, data)


@router.get("", response_model=InterviewOut)
def get_interview(application_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return InterviewService(db).get_for_user(user, application_id)


@router.put("/result", response_model=InterviewOut)
def record_result(application_id: int, data: InterviewResultUpdate,
                  company: Company = Depends(get_current_company), db: Session = Depends(get_db)):
    return InterviewService(db).record_result(company, application_id, data)
