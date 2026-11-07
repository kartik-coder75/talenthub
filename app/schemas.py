from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import (ApplicationStatus, InterviewMode, InterviewResult,
                       OfferStatus, Role)
from app.utils import normalize_branch


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
USERNAME_PATTERN = r"^[A-Za-z0-9_.-]+$"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    username: str
    role: Role


class StudentRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    branch: str = Field(min_length=2, max_length=50)
    cgpa: float = Field(ge=0, le=10)
    active_backlogs: int = Field(default=0, ge=0, le=50)

    @field_validator("branch")
    @classmethod
    def _branch(cls, v: str) -> str:
        return normalize_branch(v)


class CompanyRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=150)
    industry: str = Field(default="", max_length=100)


# ---------- Students / Companies ----------
class StudentOut(ORMModel):
    id: int
    name: str
    branch: str
    cgpa: float
    active_backlogs: int
    is_placed: bool


class StudentNameUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class AcademicRecordUpdate(BaseModel):
    """Only the placement coordinator may change academic data."""
    branch: Optional[str] = Field(default=None, min_length=2, max_length=50)
    cgpa: Optional[float] = Field(default=None, ge=0, le=10)
    active_backlogs: Optional[int] = Field(default=None, ge=0, le=50)

    @field_validator("branch")
    @classmethod
    def _branch(cls, v):
        return normalize_branch(v) if v else v


class CompanyOut(ORMModel):
    id: int
    name: str
    industry: str


# ---------- Jobs ----------
class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=5000)
    location: str = Field(default="", max_length=100)
    package_lpa: float = Field(gt=0, le=1000)
    min_cgpa: float = Field(default=0.0, ge=0, le=10)
    max_active_backlogs: int = Field(default=0, ge=0, le=50)
    allowed_branches: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("allowed_branches")
    @classmethod
    def _branches(cls, v: list[str]) -> list[str]:
        return sorted({normalize_branch(b) for b in v if b.strip()})


class JobOut(ORMModel):
    id: int
    company_id: int
    company_name: str
    title: str
    description: str
    location: str
    package_lpa: float
    min_cgpa: float
    max_active_backlogs: int
    allowed_branches: list[str]
    is_open: bool
    created_at: datetime


class EligibilityOut(BaseModel):
    job_id: int
    eligible: bool
    reasons: list[str]


# ---------- Applications / Interviews / Offers ----------
class ApplicationCreate(BaseModel):
    job_id: int


class InterviewCreate(BaseModel):
    scheduled_at: datetime
    mode: InterviewMode = InterviewMode.ONLINE
    location: str = Field(default="", max_length=200)


class InterviewResultUpdate(BaseModel):
    result: InterviewResult
    remarks: str = Field(default="", max_length=2000)

    @field_validator("result")
    @classmethod
    def _not_pending(cls, v: InterviewResult) -> InterviewResult:
        if v == InterviewResult.PENDING:
            raise ValueError("result must be PASSED or FAILED")
        return v


class InterviewOut(ORMModel):
    id: int
    application_id: int
    scheduled_at: datetime
    mode: InterviewMode
    location: str
    result: InterviewResult
    remarks: str


class OfferCreate(BaseModel):
    package_lpa: Optional[float] = Field(default=None, gt=0, le=1000)


class OfferOut(ORMModel):
    id: int
    application_id: int
    package_lpa: float
    status: OfferStatus
    issued_at: datetime
    responded_at: Optional[datetime] = None


class ApplicationOut(ORMModel):
    id: int
    student_id: int
    job_id: int
    status: ApplicationStatus
    applied_at: datetime
    student: StudentOut
    job: JobOut
    interview: Optional[InterviewOut] = None
    offer: Optional[OfferOut] = None


class ApplicationDetailOut(ApplicationOut):
    pass


# ---------- Reports ----------
class BranchStat(BaseModel):
    branch: str
    total_students: int
    placed_students: int
    placement_percentage: float


class CompanyStat(BaseModel):
    company: str
    offers_issued: int
    offers_accepted: int


class PlacementStatistics(BaseModel):
    total_students: int
    placed_students: int
    unplaced_students: int
    placement_percentage: float
    total_companies: int
    total_jobs: int
    open_jobs: int
    total_applications: int
    offers_issued: int
    offers_accepted: int
    offers_declined: int
    offers_pending: int
    average_package_lpa: float
    highest_package_lpa: float
    branch_wise: list[BranchStat]
    company_wise: list[CompanyStat]


class PlacedStudentOut(BaseModel):
    student_id: int
    student_name: str
    branch: str
    company: str
    job_title: str
    package_lpa: float
