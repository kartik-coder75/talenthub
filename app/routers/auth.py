from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import CompanyOut, CompanyRegister, StudentOut, StudentRegister, Token, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/student", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def register_student(data: StudentRegister, db: Session = Depends(get_db)):
    return AuthService(db).register_student(data)


@router.post("/register/company", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def register_company(data: CompanyRegister, db: Session = Depends(get_db)):
    return AuthService(db).register_company(data)


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return Token(access_token=AuthService(db).login(form.username, form.password))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
