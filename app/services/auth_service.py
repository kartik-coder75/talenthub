from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import Role
from app.exceptions import AuthenticationError, ConflictError
from app.models import Company, Student, User
from app.repositories.user_repository import UserRepository
from app.schemas import CompanyRegister, StudentRegister
from app.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def _create_user(self, username: str, password: str, role: Role) -> User:
        if self.users.get_by_username(username):
            raise ConflictError("Username is already taken")
        return self.users.add(
            User(username=username, password_hash=hash_password(password), role=role)
        )

    def register_student(self, data: StudentRegister) -> Student:
        try:
            user = self._create_user(data.username, data.password, Role.STUDENT)
            student = self.users.add_student(
                Student(user_id=user.id, name=data.name, branch=data.branch,
                        cgpa=data.cgpa, active_backlogs=data.active_backlogs)
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Username is already taken")
        self.db.refresh(student)
        return student

    def register_company(self, data: CompanyRegister) -> Company:
        try:
            user = self._create_user(data.username, data.password, Role.COMPANY)
            company = self.users.add_company(
                Company(user_id=user.id, name=data.name, industry=data.industry)
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Username is already taken")
        self.db.refresh(company)
        return company

    def login(self, username: str, password: str) -> str:
        user = self.users.get_by_username(username)
        # Same error for unknown user / wrong password to avoid user enumeration.
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Incorrect username or password")
        return create_access_token(user.id, user.role.value)

    def ensure_coordinator(self) -> None:
        """Coordinators cannot self-register; one account is seeded from settings."""
        if self.users.get_by_username(settings.coordinator_username):
            return
        self.users.add(User(
            username=settings.coordinator_username,
            password_hash=hash_password(settings.coordinator_password),
            role=Role.COORDINATOR,
        ))
        self.db.commit()
