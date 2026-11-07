from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_company, get_current_student
from app.models import Company, Student
from app.schemas import OfferCreate, OfferOut
from app.services.offer_service import OfferService

router = APIRouter(tags=["Offers"])


@router.post("/applications/{application_id}/offer", response_model=OfferOut,
             status_code=status.HTTP_201_CREATED)
def issue_offer(application_id: int, data: OfferCreate = OfferCreate(),
                company: Company = Depends(get_current_company), db: Session = Depends(get_db)):
    return OfferService(db).issue(company, application_id, data)


@router.get("/offers/me", response_model=list[OfferOut])
def my_offers(student: Student = Depends(get_current_student), db: Session = Depends(get_db)):
    return OfferService(db).list_for_student(student)


@router.post("/offers/{offer_id}/accept", response_model=OfferOut)
def accept_offer(offer_id: int, student: Student = Depends(get_current_student),
                 db: Session = Depends(get_db)):
    return OfferService(db).accept(student, offer_id)


@router.post("/offers/{offer_id}/decline", response_model=OfferOut)
def decline_offer(offer_id: int, student: Student = Depends(get_current_student),
                  db: Session = Depends(get_db)):
    return OfferService(db).decline(student, offer_id)
