import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.enums import Role
from app.exceptions import AuthenticationError, ForbiddenError
from app.models import Company, Student, User
from app.repositories.user_repository import UserRepository
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AuthenticationError("Invalid or expired token")
    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive")
    return user


def require_role(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"This action requires one of the roles: {', '.join(r.value for r in roles)}")
        return user
    return checker


def get_current_student(user: User = Depends(require_role(Role.STUDENT))) -> Student:
    return user.student_profile


def get_current_company(user: User = Depends(require_role(Role.COMPANY))) -> Company:
    return user.company_profile


require_coordinator = require_role(Role.COORDINATOR)
