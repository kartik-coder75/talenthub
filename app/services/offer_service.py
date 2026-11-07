from sqlalchemy.orm import Session

from app.enums import ApplicationStatus, OfferStatus
from app.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models import Company, Offer, Student
from app.repositories.application_repository import ApplicationRepository
from app.schemas import OfferCreate
from app.services.access import get_company_application
from app.utils import utcnow


class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.applications = ApplicationRepository(db)

    def issue(self, company: Company, application_id: int, data: OfferCreate) -> Offer:
        application = get_company_application(self.applications, company, application_id)
        if application.status != ApplicationStatus.SELECTED:
            raise BusinessRuleError(
                f"Offers can only be issued to students who cleared the interview "
                f"(current status: {application.status.value})"
            )
        if application.student.is_placed:
            raise BusinessRuleError("This student has already accepted another offer")

        package = data.package_lpa if data.package_lpa is not None else application.job.package_lpa
        offer = self.applications.add_offer(Offer(application_id=application.id, package_lpa=package))
        application.status = ApplicationStatus.OFFERED
        self.db.commit()
        self.db.refresh(offer)
        return offer

    def list_for_student(self, student: Student) -> list[Offer]:
        return self.applications.list_offers_for_student(student.id)

    def accept(self, student: Student, offer_id: int) -> Offer:
        offer = self._get_pending_offer(student, offer_id)
        if student.is_placed:
            raise BusinessRuleError("You have already accepted another offer")

        offer.status = OfferStatus.ACCEPTED
        offer.responded_at = utcnow()
        offer.application.status = ApplicationStatus.OFFER_ACCEPTED
        student.is_placed = True

        # One student, one placement: withdraw every other outstanding offer.
        for other in self.applications.list_offers_for_student(student.id):
            if other.id != offer.id and other.status == OfferStatus.ISSUED:
                other.status = OfferStatus.WITHDRAWN
                other.application.status = ApplicationStatus.OFFER_WITHDRAWN
        self.db.commit()
        self.db.refresh(offer)
        return offer

    def decline(self, student: Student, offer_id: int) -> Offer:
        offer = self._get_pending_offer(student, offer_id)
        offer.status = OfferStatus.DECLINED
        offer.responded_at = utcnow()
        offer.application.status = ApplicationStatus.OFFER_DECLINED
        self.db.commit()
        self.db.refresh(offer)
        return offer

    def _get_pending_offer(self, student: Student, offer_id: int) -> Offer:
        offer = self.applications.get_offer(offer_id)
        if not offer:
            raise NotFoundError("Offer not found")
        if offer.application.student_id != student.id:
            raise ForbiddenError("This offer was not issued to you")
        if offer.status != OfferStatus.ISSUED:
            raise BusinessRuleError(f"This offer is already {offer.status.value}")
        return offer
