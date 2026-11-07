from enum import Enum


class Role(str, Enum):
    STUDENT = "STUDENT"
    COMPANY = "COMPANY"
    COORDINATOR = "COORDINATOR"


class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    SELECTED = "SELECTED"            # cleared the interview
    NOT_SELECTED = "NOT_SELECTED"    # failed the interview
    OFFERED = "OFFERED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    OFFER_DECLINED = "OFFER_DECLINED"
    OFFER_WITHDRAWN = "OFFER_WITHDRAWN"


class InterviewMode(str, Enum):
    ONLINE = "ONLINE"
    ONSITE = "ONSITE"


class InterviewResult(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class OfferStatus(str, Enum):
    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
