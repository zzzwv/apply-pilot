from fastapi import APIRouter, Query

from app.api.applications import CurrentUserDependency, FilterDependency, SessionDependency
from app.core.responses import success_response
from app.schemas.dashboard import TrendGranularity
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    session: SessionDependency, current_user: CurrentUserDependency, filters: FilterDependency
):
    payload = await AnalyticsService(session).get_summary(current_user, filters)
    return success_response(payload.model_dump(mode="json"))


@router.get("/status-distribution")
async def get_status_distribution(
    session: SessionDependency, current_user: CurrentUserDependency, filters: FilterDependency
):
    payload = await AnalyticsService(session).get_status_distribution(current_user, filters)
    return success_response(payload.model_dump(mode="json"))


@router.get("/industry-distribution")
async def get_industry_distribution(
    session: SessionDependency, current_user: CurrentUserDependency, filters: FilterDependency
):
    payload = await AnalyticsService(session).get_industry_distribution(current_user, filters)
    return success_response(payload.model_dump(mode="json"))


@router.get("/company-nature-distribution")
async def get_company_nature_distribution(
    session: SessionDependency, current_user: CurrentUserDependency, filters: FilterDependency
):
    payload = await AnalyticsService(session).get_company_nature_distribution(current_user, filters)
    return success_response(payload.model_dump(mode="json"))


@router.get("/application-trend")
async def get_application_trend(
    session: SessionDependency,
    current_user: CurrentUserDependency,
    filters: FilterDependency,
    granularity: TrendGranularity = Query(default=TrendGranularity.DAY),
):
    payload = await AnalyticsService(session).get_application_trend(
        current_user, filters, granularity
    )
    return success_response(payload.model_dump(mode="json"))
