"""Shared ownership / authorization checks used by several services."""
from app.exceptions import ForbiddenError, NotFoundError
from app.models import Application, Company
from app.repositories.application_repository import ApplicationRepository


def get_company_application(repo: ApplicationRepository, company: Company, application_id: int) -> Application:
    application = repo.get(application_id)
    if not application:
        raise NotFoundError("Application not found")
    if application.job.company_id != company.id:
        raise ForbiddenError("This application belongs to another company's job")
    return application
