from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import ApplicationStatus
from app.models import Application, Interview, Offer


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, application: Application) -> Application:
        self.db.add(application)
        self.db.flush()
        return application

    def get(self, application_id: int) -> Optional[Application]:
        return self.db.get(Application, application_id)

    def get_by_student_and_job(self, student_id: int, job_id: int) -> Optional[Application]:
        stmt = select(Application).where(
            Application.student_id == student_id, Application.job_id == job_id
        )
        return self.db.scalar(stmt)

    def list_for_student(self, student_id: int) -> list[Application]:
        stmt = select(Application).where(Application.student_id == student_id).order_by(Application.id)
        return list(self.db.scalars(stmt))

    def list_for_job(self, job_id: int, status: Optional[ApplicationStatus] = None) -> list[Application]:
        stmt = select(Application).where(Application.job_id == job_id).order_by(Application.id)
        if status:
            stmt = stmt.where(Application.status == status)
        return list(self.db.scalars(stmt))

    def list_all(self) -> list[Application]:
        return list(self.db.scalars(select(Application)))

    # interviews
    def add_interview(self, interview: Interview) -> Interview:
        self.db.add(interview)
        self.db.flush()
        return interview

    # offers
    def add_offer(self, offer: Offer) -> Offer:
        self.db.add(offer)
        self.db.flush()
        return offer

    def get_offer(self, offer_id: int) -> Optional[Offer]:
        return self.db.get(Offer, offer_id)

    def list_offers_for_student(self, student_id: int) -> list[Offer]:
        stmt = (
            select(Offer)
            .join(Application, Offer.application_id == Application.id)
            .where(Application.student_id == student_id)
            .order_by(Offer.id)
        )
        return list(self.db.scalars(stmt))

    def list_all_offers(self) -> list[Offer]:
        return list(self.db.scalars(select(Offer)))
