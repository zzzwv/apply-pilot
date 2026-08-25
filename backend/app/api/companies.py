from typing import Annotated

from fastapi import APIRouter, Depends
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


@router.post("")
async def create_company(
    payload: CompanyCreate, session: SessionDependency, current_user: CurrentUserDependency
):
    company = await CompanyService(session).create(payload)
    return success_response(
        CompanyRead.model_validate(company).model_dump(mode="json"), status_code=201
    )
