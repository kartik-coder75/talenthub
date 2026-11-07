from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums import ApplicationStatus, Role
from app.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.models import Application, Company, Student, User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.services.access import get_company_application
from app.services.eligibility import check_eligibility


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.applications = ApplicationRepository(db)
        self.jobs = JobRepository(db)

    def apply(self, student: Student, job_id: int) -> Application:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("Job not found")
        if not job.is_open:
            raise BusinessRuleError("This job is closed for applications")
        if student.is_placed:
            raise BusinessRuleError("You have already accepted an offer and cannot apply to more jobs")
        if self.applications.get_by_student_and_job(student.id, job.id):
            raise ConflictError("You have already applied for this job")

        result = check_eligibility(student, job)
        if not result.eligible:
            raise BusinessRuleError("Not eligible: " + "; ".join(result.reasons))

        try:
            application = self.applications.add(
                Application(student_id=student.id, job_id=job.id, status=ApplicationStatus.APPLIED)
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("You have already applied for this job")
        self.db.refresh(application)
        return application

    def list_for_student(self, student: Student) -> list[Application]:
        return self.applications.list_for_student(student.id)

    def get_for_user(self, user: User, application_id: int) -> Application:
        application = self.applications.get(application_id)
        if not application:
            raise NotFoundError("Application not found")
        allowed = (
            (user.role == Role.COORDINATOR)
            or (user.role == Role.STUDENT and user.student_profile
                and application.student_id == user.student_profile.id)
            or (user.role == Role.COMPANY and user.company_profile
                and application.job.company_id == user.company_profile.id)
        )
        if not allowed:
            raise ForbiddenError("You do not have access to this application")
        return application

    def shortlist(self, company: Company, application_id: int) -> Application:
        application = get_company_application(self.applications, company, application_id)
        if application.status != ApplicationStatus.APPLIED:
            raise BusinessRuleError(
                f"Only applications in APPLIED status can be shortlisted (current: {application.status.value})"
            )
        # Re-check eligibility: academic data may have been corrected since the student applied.
        result = check_eligibility(application.student, application.job)
        if not result.eligible:
            raise BusinessRuleError("Student no longer meets the job criteria: " + "; ".join(result.reasons))
        application.status = ApplicationStatus.SHORTLISTED
        self.db.commit()
        self.db.refresh(application)
        return application

    def reject(self, company: Company, application_id: int) -> Application:
        application = get_company_application(self.applications, company, application_id)
        if application.status not in (ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED):
            raise BusinessRuleError(
                f"Only APPLIED or SHORTLISTED applications can be rejected (current: {application.status.value})"
            )
        application.status = ApplicationStatus.REJECTED
        self.db.commit()
        self.db.refresh(application)
        return application
