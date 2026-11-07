from sqlalchemy.orm import Session

from app.enums import ApplicationStatus, InterviewResult
from app.exceptions import BusinessRuleError, NotFoundError
from app.models import Company, Interview, User
from app.repositories.application_repository import ApplicationRepository
from app.schemas import InterviewCreate, InterviewResultUpdate
from app.services.access import get_company_application
from app.services.application_service import ApplicationService
from app.utils import to_naive_utc, utcnow


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.applications = ApplicationRepository(db)

    def schedule(self, company: Company, application_id: int, data: InterviewCreate) -> Interview:
        application = get_company_application(self.applications, company, application_id)
        if application.status != ApplicationStatus.SHORTLISTED:
            raise BusinessRuleError(
                f"Interviews can only be scheduled for SHORTLISTED applications (current: {application.status.value})"
            )
        when = to_naive_utc(data.scheduled_at)
        if when <= utcnow():
            raise BusinessRuleError("Interview must be scheduled for a future date and time")

        interview = self.applications.add_interview(Interview(
            application_id=application.id, scheduled_at=when,
            mode=data.mode, location=data.location,
        ))
        application.status = ApplicationStatus.INTERVIEW_SCHEDULED
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def record_result(self, company: Company, application_id: int, data: InterviewResultUpdate) -> Interview:
        application = get_company_application(self.applications, company, application_id)
        interview = application.interview
        if not interview or application.status != ApplicationStatus.INTERVIEW_SCHEDULED:
            raise BusinessRuleError("There is no pending interview for this application")
        if interview.result != InterviewResult.PENDING:
            raise BusinessRuleError("The interview result has already been recorded")

        interview.result = data.result
        interview.remarks = data.remarks
        application.status = (
            ApplicationStatus.SELECTED if data.result == InterviewResult.PASSED
            else ApplicationStatus.NOT_SELECTED
        )
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def get_for_user(self, user: User, application_id: int) -> Interview:
        application = ApplicationService(self.db).get_for_user(user, application_id)
        if not application.interview:
            raise NotFoundError("No interview has been scheduled for this application")
        return application.interview
