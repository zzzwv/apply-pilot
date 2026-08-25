from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_session
from app.core.responses import success_response
from app.models import User
from app.schemas.application import (
    ApplicationBatchDeleteRequest,
    ApplicationCreate,
    ApplicationListResponse,
    ApplicationRead,
    ApplicationStatusLogListResponse,
    ApplicationStatusLogRead,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    DeletedCountResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]


@router.post("")
async def create_application(
    payload: ApplicationCreate, session: SessionDependency, current_user: CurrentUserDependency
):
    application = await ApplicationService(session).create_application(payload, current_user)
    return success_response(
        ApplicationRead.model_validate(application).model_dump(mode="json"), status_code=201
    )


@router.get("")
async def list_applications(
    session: SessionDependency,
    current_user: CurrentUserDependency,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    applications, total = await ApplicationService(session).list_applications(
        current_user, page, page_size
    )
    payload = ApplicationListResponse(
        items=[ApplicationRead.model_validate(application) for application in applications],
        total=total,
        page=page,
        page_size=page_size,
    )
    return success_response(payload.model_dump(mode="json"))


@router.post("/batch-delete")
async def batch_delete_applications(
    payload: ApplicationBatchDeleteRequest,
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    deleted_count = await ApplicationService(session).batch_delete(payload.ids, current_user)
    return success_response(DeletedCountResponse(deleted_count=deleted_count).model_dump())


@router.get("/{application_id}")
async def get_application(
    application_id: UUID, session: SessionDependency, current_user: CurrentUserDependency
):
    application = await ApplicationService(session).get_application(application_id, current_user)
    return success_response(ApplicationRead.model_validate(application).model_dump(mode="json"))


@router.put("/{application_id}")
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    application = await ApplicationService(session).update_application(
        application_id, payload, current_user
    )
    return success_response(ApplicationRead.model_validate(application).model_dump(mode="json"))


@router.delete("/{application_id}")
async def delete_application(
    application_id: UUID, session: SessionDependency, current_user: CurrentUserDependency
):
    deleted_count = await ApplicationService(session).delete_application(
        application_id, current_user
    )
    return success_response(DeletedCountResponse(deleted_count=deleted_count).model_dump())


@router.patch("/{application_id}/status")
async def change_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    session: SessionDependency,
    current_user: CurrentUserDependency,
):
    application = await ApplicationService(session).change_status(
        application_id, payload, current_user
    )
    return success_response(ApplicationRead.model_validate(application).model_dump(mode="json"))


@router.get("/{application_id}/status-logs")
async def get_application_status_logs(
    application_id: UUID, session: SessionDependency, current_user: CurrentUserDependency
):
    logs = await ApplicationService(session).get_status_logs(application_id, current_user)
    payload = ApplicationStatusLogListResponse(
        items=[ApplicationStatusLogRead.model_validate(log) for log in logs]
    )
    return success_response(payload.model_dump(mode="json"))
