from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models import Student
from app.repositories.student_repository import StudentRepository
from app.schemas import AcademicRecordUpdate


class StudentService:
    def __init__(self, db: Session):
        self.db = db
        self.students = StudentRepository(db)

    def update_name(self, student: Student, name: str) -> Student:
        student.name = name
        self.db.commit()
        self.db.refresh(student)
        return student

    def list_students(self, branch: Optional[str], placed: Optional[bool]) -> list[Student]:
        return self.students.list_all(branch=branch.strip().upper() if branch else None, placed=placed)

    def update_academic_record(self, student_id: int, data: AcademicRecordUpdate) -> Student:
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError("Student not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(student, field, value)
        self.db.commit()
        self.db.refresh(student)
        return student
