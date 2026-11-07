from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_coordinator
from app.models import User
from app.schemas import PlacedStudentOut, PlacementStatistics
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Placement Reports"])


@router.get("/placement-statistics", response_model=PlacementStatistics)
def placement_statistics(_: User = Depends(require_coordinator), db: Session = Depends(get_db)):
    return ReportService(db).placement_statistics()


@router.get("/placed-students", response_model=list[PlacedStudentOut])
def placed_students(_: User = Depends(require_coordinator), db: Session = Depends(get_db)):
    return ReportService(db).placed_students()
