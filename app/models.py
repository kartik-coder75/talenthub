from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, Enum as SAEnum, Float, ForeignKey,
                        Integer, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import (ApplicationStatus, InterviewMode, InterviewResult,
                       OfferStatus, Role)
from app.utils import utcnow


def _enum(e, length=30):
    return SAEnum(e, native_enum=False, length=length)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(_enum(Role, 20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    student_profile: Mapped[Optional["Student"]] = relationship(back_populates="user", uselist=False)
    company_profile: Mapped[Optional["Company"]] = relationship(back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    branch: Mapped[str] = mapped_column(String(50), index=True)
    cgpa: Mapped[float] = mapped_column(Float)
    active_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    is_placed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="student_profile")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    industry: Mapped[str] = mapped_column(String(100), default="")

    user: Mapped[User] = relationship(back_populates="company_profile")
    jobs: Mapped[list["JobListing"]] = relationship(back_populates="company")


class JobListing(Base):
    __tablename__ = "job_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(100), default="")
    package_lpa: Mapped[float] = mapped_column(Float)
    min_cgpa: Mapped[float] = mapped_column(Float, default=0.0)
    max_active_backlogs: Mapped[int] = mapped_column(Integer, default=0)
    allowed_branches_csv: Mapped[str] = mapped_column(String(500), default="")  # empty = all branches
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")

    @property
    def company_name(self) -> str:
        return self.company.name

    @property
    def allowed_branches(self) -> list[str]:
        return [b for b in self.allowed_branches_csv.split(",") if b]


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "job_id", name="uq_student_job"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_listings.id"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(_enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    student: Mapped[Student] = relationship(back_populates="applications")
    job: Mapped[JobListing] = relationship(back_populates="applications")
    interview: Mapped[Optional["Interview"]] = relationship(back_populates="application", uselist=False)
    offer: Mapped[Optional["Offer"]] = relationship(back_populates="application", uselist=False)


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    mode: Mapped[InterviewMode] = mapped_column(_enum(InterviewMode, 10), default=InterviewMode.ONLINE)
    location: Mapped[str] = mapped_column(String(200), default="")
    result: Mapped[InterviewResult] = mapped_column(_enum(InterviewResult, 10), default=InterviewResult.PENDING)
    remarks: Mapped[str] = mapped_column(Text, default="")

    application: Mapped[Application] = relationship(back_populates="interview")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    package_lpa: Mapped[float] = mapped_column(Float)
    status: Mapped[OfferStatus] = mapped_column(_enum(OfferStatus, 10), default=OfferStatus.ISSUED)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    application: Mapped[Application] = relationship(back_populates="offer")
