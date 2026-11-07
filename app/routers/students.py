from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_student, require_coordinator
from app.models import Student, User
from app.schemas import AcademicRecordUpdate, StudentNameUpdate, StudentOut
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentOut)
def my_profile(student: Student = Depends(get_current_student)):
    return student


@router.patch("/me", response_model=StudentOut)
def update_my_name(data: StudentNameUpdate, student: Student = Depends(get_current_student),
                   db: Session = Depends(get_db)):
    return StudentService(db).update_name(student, data.name)


@router.get("", response_model=list[StudentOut])
def list_students(branch: Optional[str] = None, placed: Optional[bool] = None,
                  _: User = Depends(require_coordinator), db: Session = Depends(get_db)):
    return StudentService(db).list_students(branch, placed)


@router.patch("/{student_id}/academic-record", response_model=StudentOut)
def update_academic_record(student_id: int, data: AcademicRecordUpdate,
                           _: User = Depends(require_coordinator), db: Session = Depends(get_db)):
    return StudentService(db).update_academic_record(student_id, data)
