from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, JobListing


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, job: JobListing) -> JobListing:
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: int) -> Optional[JobListing]:
        return self.db.get(JobListing, job_id)

    def list_open(self) -> list[JobListing]:
        stmt = select(JobListing).where(JobListing.is_open.is_(True)).order_by(JobListing.id)
        return list(self.db.scalars(stmt))

    def list_companies(self) -> list[Company]:
        return list(self.db.scalars(select(Company).order_by(Company.id)))

    def list_all(self) -> list[JobListing]:
        return list(self.db.scalars(select(JobListing)))
