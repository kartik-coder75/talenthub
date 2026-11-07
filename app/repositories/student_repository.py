from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Student


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, student_id: int) -> Optional[Student]:
        return self.db.get(Student, student_id)

    def list_all(self, branch: Optional[str] = None, placed: Optional[bool] = None) -> list[Student]:
        stmt = select(Student).order_by(Student.id)
        if branch:
            stmt = stmt.where(Student.branch == branch)
        if placed is not None:
            stmt = stmt.where(Student.is_placed == placed)
        return list(self.db.scalars(stmt))
