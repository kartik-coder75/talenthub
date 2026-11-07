from fastapi import APIRouter, Depends

from app.dependencies import get_current_company
from app.models import Company
from app.schemas import CompanyOut

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/me", response_model=CompanyOut)
def my_company(company: Company = Depends(get_current_company)):
    return company
