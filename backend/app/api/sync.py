from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_session
from app.core.responses import success_response
from app.models import ApplicationStatusLog, Company, JobApplication, User
from app.schemas.application import SyncImportRequest

router = APIRouter(prefix="/sync", tags=["sync"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]


@router.post("/import-applications")
async def import_applications(payload: SyncImportRequest, session: SessionDependency, current_user: CurrentUserDependency):
    mappings = []
    imported = reused = failed = 0
    for item in payload.applications:
        existing = await session.scalar(select(JobApplication).where(JobApplication.user_id == current_user.id, JobApplication.client_sync_id == item.client_sync_id))
        if existing:
            reused += 1
            mappings.append({"client_sync_id": str(item.client_sync_id), "cloud_application_id": str(existing.id)})
            continue
        try:
            company = await session.scalar(select(Company).where(Company.full_name == item.company.full_name))
            if company is None:
                company = Company(**item.company.model_dump())
                session.add(company)
                await session.flush()
            values = item.model_dump(exclude={"company", "status_logs", "client_sync_id"})
            application = JobApplication(user_id=current_user.id, company_id=company.id, client_sync_id=item.client_sync_id, **values)
            session.add(application)
            await session.flush()
            for log in item.status_logs:
                session.add(ApplicationStatusLog(application_id=application.id, user_id=current_user.id, **log.model_dump()))
            await session.commit()
            imported += 1
            mappings.append({"client_sync_id": str(item.client_sync_id), "cloud_application_id": str(application.id)})
        except Exception:
            await session.rollback()
            failed += 1
    return success_response({"imported": imported, "reused": reused, "failed": failed, "mappings": mappings, "errors": []})
