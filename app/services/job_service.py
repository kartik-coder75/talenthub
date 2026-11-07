from typing import Optional

from sqlalchemy.orm import Session

from app.enums import ApplicationStatus
from app.exceptions import ForbiddenError, NotFoundError
from app.models import Application, Company, JobListing, Student
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.schemas import JobCreate
from app.services.eligibility import EligibilityResult, check_eligibility


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.jobs = JobRepository(db)
        self.applications = ApplicationRepository(db)

    def create_job(self, company: Company, data: JobCreate) -> JobListing:
        job = self.jobs.add(JobListing(
            company_id=company.id,
            title=data.title,
            description=data.description,
            location=data.location,
            package_lpa=data.package_lpa,
            min_cgpa=data.min_cgpa,
            max_active_backlogs=data.max_active_backlogs,
            allowed_branches_csv=",".join(data.allowed_branches),
        ))
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> JobListing:
        job = self.jobs.get(job_id)
        if not job:
            raise NotFoundError("Job not found")
        return job

    def list_open_jobs(self, student: Optional[Student] = None, eligible_only: bool = False) -> list[JobListing]:
        jobs = self.jobs.list_open()
        if student is not None and eligible_only:
            jobs = [j for j in jobs if check_eligibility(student, j).eligible]
        return jobs

    def check_student_eligibility(self, student: Student, job_id: int) -> EligibilityResult:
        return check_eligibility(student, self.get_job(job_id))

    def close_job(self, company: Company, job_id: int) -> JobListing:
        job = self._get_owned_job(company, job_id)
        job.is_open = False
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_applications(self, company: Company, job_id: int,
                          status: Optional[ApplicationStatus] = None) -> list[Application]:
        self._get_owned_job(company, job_id)
        return self.applications.list_for_job(job_id, status)

    def _get_owned_job(self, company: Company, job_id: int) -> JobListing:
        job = self.get_job(job_id)
        if job.company_id != company.id:
            raise ForbiddenError("This job belongs to another company")
        return job
