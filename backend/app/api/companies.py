from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_session
from app.core.responses import success_response
from app.models import User
from app.schemas.company import CompanyCreate, CompanyRead
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]


@router.get("/search")
async def search_local_companies(
    keyword: Annotated[str, Query(min_length=1, max_length=255)],
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    del current_user
    companies = await CompanyService(session).search_local(keyword.strip())
    return success_response([company.model_dump(mode="json") for company in companies])


@router.post("")
async def create_company(
    payload: CompanyCreate, session: SessionDependency, current_user: CurrentUserDependency
):
    company = await CompanyService(session).create(payload)
    return success_response(
        CompanyRead.model_validate(company).model_dump(mode="json"), status_code=201
    )
