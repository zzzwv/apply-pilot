from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.company_intelligence.schemas import CompanyIntelligenceSearchRequest
from app.core.database import get_session
from app.core.responses import success_response
from app.models import User
from app.schemas.company import CompanyIntelligenceConfirmRequest
from app.services.company_intelligence_service import CompanyIntelligenceService
from app.services.company_service import CompanyService

router = APIRouter(prefix="/company-intelligence", tags=["company-intelligence"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]


@router.post("/search")
async def search_company_intelligence(
    payload: CompanyIntelligenceSearchRequest,
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    result = await CompanyIntelligenceService(session).search_company(
        payload, actor_id=current_user.id
    )
    return success_response(result.model_dump(mode="json"))


@router.post("/confirm")
async def confirm_company_intelligence(
    payload: CompanyIntelligenceConfirmRequest,
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    confirmation = await CompanyService(session).confirm(payload)
    return success_response(confirmation.model_dump(mode="json"), status_code=201)
