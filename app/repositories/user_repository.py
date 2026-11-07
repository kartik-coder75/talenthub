from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, Student, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.username == username))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def add_student(self, student: Student) -> Student:
        self.db.add(student)
        self.db.flush()
        return student

    def add_company(self, company: Company) -> Company:
        self.db.add(company)
        self.db.flush()
        return company
