from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.analytics import AnalyticsRepository
from app.schemas.application import ApplicationFilterParams
from app.schemas.dashboard import (
    CompanyNatureDistributionItem,
    CompanyNatureDistributionRead,
    DashboardSummaryRead,
    DashboardTrendRead,
    IndustryDistributionItem,
    IndustryDistributionRead,
    StatusDistributionItem,
    StatusDistributionRead,
    TrendGranularity,
    TrendPoint,
)


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.analytics = AnalyticsRepository(session)

    async def get_summary(
        self, current_user: User, filters: ApplicationFilterParams
    ) -> DashboardSummaryRead:
        values = await self.analytics.get_summary(current_user.id, filters)
        total = values["total"]
        interview_started = values["interview_started"]
        return DashboardSummaryRead(
            total=total,
            in_progress=values["in_progress"],
            offer_count=values["offer_count"],
            interview_rate=(
                values["interview_passed"] / interview_started if interview_started else 0.0
            ),
            offer_rate=values["offer_count"] / total if total else 0.0,
            rejection_rate=values["rejected_count"] / total if total else 0.0,
        )

    async def get_status_distribution(
        self, current_user: User, filters: ApplicationFilterParams
    ) -> StatusDistributionRead:
        items = await self.analytics.get_status_distribution(current_user.id, filters)
        total = sum(count for _, count in items)
        return StatusDistributionRead(
            items=[
                StatusDistributionItem(
                    status=status, count=count, percentage=count / total if total else 0.0
                )
                for status, count in items
            ]
        )

    async def get_industry_distribution(
        self, current_user: User, filters: ApplicationFilterParams
    ) -> IndustryDistributionRead:
        items = await self.analytics.get_industry_distribution(current_user.id, filters)
        total = sum(count for _, count in items)
        return IndustryDistributionRead(
            items=[
                IndustryDistributionItem(
                    industry=name, count=count, percentage=count / total if total else 0.0
                )
                for name, count in items
            ]
        )

    async def get_company_nature_distribution(
        self, current_user: User, filters: ApplicationFilterParams
    ) -> CompanyNatureDistributionRead:
        items = await self.analytics.get_company_nature_distribution(current_user.id, filters)
        total = sum(count for _, count in items)
        return CompanyNatureDistributionRead(
            items=[
                CompanyNatureDistributionItem(
                    company_nature=name, count=count, percentage=count / total if total else 0.0
                )
                for name, count in items
            ]
        )

    async def get_application_trend(
        self,
        current_user: User,
        filters: ApplicationFilterParams,
        granularity: TrendGranularity,
    ) -> DashboardTrendRead:
        items = await self.analytics.get_application_trend(current_user.id, filters, granularity)
        return DashboardTrendRead(
            items=[TrendPoint(date=period, count=count) for period, count in items]
        )
