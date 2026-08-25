from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, ErrorCode
from app.core.responses import success_response
from app.models import User
from app.models.enums import ApplicationStatus, ApplicationType
from app.schemas.application import (
    ApplicationBatchDeleteRequest,
    ApplicationCreate,
    ApplicationFilterParams,
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


def _split_values(values: list[str] | None) -> list[str]:
    return [item.strip() for value in values or [] for item in value.split(",") if item.strip()]


def _parse_enum_values(
    values: list[str] | None, enum_type: type[ApplicationStatus | ApplicationType]
):
    try:
        return [enum_type(value) for value in _split_values(values)]
    except ValueError as exc:
        raise AppError(ErrorCode.STATUS_INVALID, "Invalid request", 422) from exc


def get_application_filter_params(
    keyword: str | None = Query(default=None, max_length=255),
    status: list[str] | None = Query(default=None),
    company_nature: list[str] | None = Query(default=None),
    application_type: list[str] | None = Query(default=None),
    industry: list[str] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    company_size: list[str] | None = Query(default=None),
    sort: str = Query(default="application_date_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApplicationFilterParams:
    try:
        filters = ApplicationFilterParams(
            keyword=keyword.strip() or None if keyword else None,
            statuses=_parse_enum_values(status, ApplicationStatus),
            company_natures=_split_values(company_nature),
            application_types=_parse_enum_values(application_type, ApplicationType),
            industries=_split_values(industry),
            date_from=date_from,
            date_to=date_to,
            company_sizes=_split_values(company_size),
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise AppError(ErrorCode.STATUS_INVALID, "Invalid request", 422) from exc
    if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
        raise AppError(ErrorCode.STATUS_INVALID, "Invalid request", 422)
    return filters


FilterDependency = Annotated[ApplicationFilterParams, Depends(get_application_filter_params)]


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
    filters: FilterDependency,
):
    applications, total = await ApplicationService(session).list_applications(
        current_user, filters
    )
    payload = ApplicationListResponse(
        items=[ApplicationRead.model_validate(application) for application in applications],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
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
