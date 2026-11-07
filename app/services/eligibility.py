"""Pure eligibility rules - no database access, easy to unit test."""
from dataclasses import dataclass, field


@dataclass
class EligibilityResult:
    eligible: bool
    reasons: list[str] = field(default_factory=list)


def check_eligibility(student, job) -> EligibilityResult:
    """A student is eligible when ALL of these hold:
      * CGPA >= job.min_cgpa                      (boundary value is eligible)
      * active backlogs <= job.max_active_backlogs (boundary value is eligible)
      * branch is in job.allowed_branches, if the job restricts branches
    """
    reasons: list[str] = []
    if student.cgpa < job.min_cgpa:
        reasons.append(f"CGPA {student.cgpa} is below the required minimum of {job.min_cgpa}")
    if student.active_backlogs > job.max_active_backlogs:
        reasons.append(
            f"{student.active_backlogs} active backlog(s) exceeds the allowed maximum of "
            f"{job.max_active_backlogs}"
        )
    allowed = job.allowed_branches
    if allowed and student.branch.strip().upper() not in allowed:
        reasons.append(f"Branch {student.branch} is not eligible (allowed: {', '.join(allowed)})")
    return EligibilityResult(eligible=not reasons, reasons=reasons)
