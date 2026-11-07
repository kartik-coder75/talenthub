from collections import defaultdict

from sqlalchemy.orm import Session

from app.enums import OfferStatus
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import BranchStat, CompanyStat, PlacedStudentOut, PlacementStatistics


def _pct(part: int, whole: int) -> float:
    return round(part * 100 / whole, 2) if whole else 0.0


class ReportService:
    def __init__(self, db: Session):
        self.students = StudentRepository(db)
        self.jobs = JobRepository(db)
        self.applications = ApplicationRepository(db)

    def placement_statistics(self) -> PlacementStatistics:
        students = self.students.list_all()
        companies = self.jobs.list_companies()
        jobs = self.jobs.list_all()
        offers = self.applications.list_all_offers()

        placed = [s for s in students if s.is_placed]
        accepted = [o for o in offers if o.status == OfferStatus.ACCEPTED]
        packages = [o.package_lpa for o in accepted]

        branches: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [total, placed]
        for s in students:
            branches[s.branch][0] += 1
            branches[s.branch][1] += int(s.is_placed)

        per_company: dict[str, list[int]] = {c.name: [0, 0] for c in companies}
        for o in offers:
            name = o.application.job.company.name
            per_company[name][0] += 1
            per_company[name][1] += int(o.status == OfferStatus.ACCEPTED)

        return PlacementStatistics(
            total_students=len(students),
            placed_students=len(placed),
            unplaced_students=len(students) - len(placed),
            placement_percentage=_pct(len(placed), len(students)),
            total_companies=len(companies),
            total_jobs=len(jobs),
            open_jobs=sum(1 for j in jobs if j.is_open),
            total_applications=len(self.applications.list_all()),
            offers_issued=len(offers),
            offers_accepted=len(accepted),
            offers_declined=sum(1 for o in offers if o.status == OfferStatus.DECLINED),
            offers_pending=sum(1 for o in offers if o.status == OfferStatus.ISSUED),
            average_package_lpa=round(sum(packages) / len(packages), 2) if packages else 0.0,
            highest_package_lpa=max(packages) if packages else 0.0,
            branch_wise=[
                BranchStat(branch=b, total_students=t, placed_students=p, placement_percentage=_pct(p, t))
                for b, (t, p) in sorted(branches.items())
            ],
            company_wise=[
                CompanyStat(company=c, offers_issued=i, offers_accepted=a)
                for c, (i, a) in sorted(per_company.items())
            ],
        )

    def placed_students(self) -> list[PlacedStudentOut]:
        rows = []
        for o in self.applications.list_all_offers():
            if o.status != OfferStatus.ACCEPTED:
                continue
            app = o.application
            rows.append(PlacedStudentOut(
                student_id=app.student.id, student_name=app.student.name, branch=app.student.branch,
                company=app.job.company.name, job_title=app.job.title, package_lpa=o.package_lpa,
            ))
        return rows
