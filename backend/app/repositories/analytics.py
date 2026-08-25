from uuid import UUID

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationStatusLog, Company, JobApplication
from app.models.enums import ApplicationStatus
from app.repositories.application import ApplicationRepository
from app.schemas.application import ApplicationFilterParams
from app.schemas.dashboard import TrendGranularity

IN_PROGRESS_STATUSES = (
    ApplicationStatus.RESUME_PASSED,
    ApplicationStatus.FIRST_INTERVIEW,
    ApplicationStatus.SECOND_INTERVIEW,
    ApplicationStatus.FINAL_INTERVIEW,
    ApplicationStatus.HR_INTERVIEW,
    ApplicationStatus.SALARY_NEGOTIATION,
)
OFFER_STATUSES = (ApplicationStatus.OFFER_RECEIVED, ApplicationStatus.SIGNED)
REJECTION_STATUSES = (
    ApplicationStatus.RESUME_REJECTED,
    ApplicationStatus.INTERVIEW_REJECTED,
    ApplicationStatus.PROCESS_TERMINATED,
)
INTERVIEW_STARTED_STATUSES = (
    ApplicationStatus.FIRST_INTERVIEW,
    ApplicationStatus.SECOND_INTERVIEW,
    ApplicationStatus.FINAL_INTERVIEW,
    ApplicationStatus.HR_INTERVIEW,
    ApplicationStatus.SALARY_NEGOTIATION,
    ApplicationStatus.OFFER_RECEIVED,
    ApplicationStatus.OFFER_REJECTED,
    ApplicationStatus.SIGNED,
    ApplicationStatus.INTERVIEW_REJECTED,
)
INTERVIEW_PASSED_STATUSES = (
    ApplicationStatus.SECOND_INTERVIEW,
    ApplicationStatus.FINAL_INTERVIEW,
    ApplicationStatus.HR_INTERVIEW,
    ApplicationStatus.SALARY_NEGOTIATION,
    ApplicationStatus.OFFER_RECEIVED,
    ApplicationStatus.OFFER_REJECTED,
    ApplicationStatus.SIGNED,
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _filtered_applications(user_id: UUID, filters: ApplicationFilterParams):
        query = select(
            JobApplication.id,
            JobApplication.current_status,
            JobApplication.application_date,
            Company.industry,
            Company.nature,
        ).join(Company, JobApplication.company_id == Company.id).where(
            JobApplication.user_id == user_id
        )
        return ApplicationRepository.apply_filters(query, filters).subquery()

    async def get_summary(self, user_id: UUID, filters: ApplicationFilterParams) -> dict[str, int]:
        applications = self._filtered_applications(user_id, filters)
        result = await self.session.execute(
            select(
                func.count().label("total"),
                func.count().filter(applications.c.current_status.in_(IN_PROGRESS_STATUSES)).label("in_progress"),
                func.count().filter(applications.c.current_status.in_(OFFER_STATUSES)).label("offer_count"),
                func.count().filter(applications.c.current_status.in_(REJECTION_STATUSES)).label("rejected_count"),
            )
        )
        summary = result.mappings().one()
        interview_counts = await self.session.execute(
            select(
                func.count(func.distinct(ApplicationStatusLog.application_id))
                .filter(ApplicationStatusLog.to_status.in_(INTERVIEW_STARTED_STATUSES))
                .label("started"),
                func.count(func.distinct(ApplicationStatusLog.application_id))
                .filter(ApplicationStatusLog.to_status.in_(INTERVIEW_PASSED_STATUSES))
                .label("passed"),
            )
            .join(applications, ApplicationStatusLog.application_id == applications.c.id)
            .where(ApplicationStatusLog.user_id == user_id)
        )
        interviews = interview_counts.mappings().one()
        return {
            "total": summary["total"] or 0,
            "in_progress": summary["in_progress"] or 0,
            "offer_count": summary["offer_count"] or 0,
            "rejected_count": summary["rejected_count"] or 0,
            "interview_started": interviews["started"] or 0,
            "interview_passed": interviews["passed"] or 0,
        }

    async def get_status_distribution(
        self, user_id: UUID, filters: ApplicationFilterParams
    ) -> list[tuple[ApplicationStatus, int]]:
        applications = self._filtered_applications(user_id, filters)
        result = await self.session.execute(
            select(applications.c.current_status, func.count().label("count"))
            .group_by(applications.c.current_status)
            .order_by(func.count().desc(), applications.c.current_status.asc())
        )
        return [(row.current_status, row.count) for row in result]

    async def get_industry_distribution(
        self, user_id: UUID, filters: ApplicationFilterParams
    ) -> list[tuple[str, int]]:
        applications = self._filtered_applications(user_id, filters)
        industry = func.coalesce(
            func.nullif(applications.c.industry, ""), "UNKNOWN"
        ).label("industry")
        result = await self.session.execute(
            select(industry, func.count().label("count"))
            .group_by(industry)
            .order_by(func.count().desc(), industry.asc())
        )
        return [(row.industry, row.count) for row in result]

    async def get_company_nature_distribution(
        self, user_id: UUID, filters: ApplicationFilterParams
    ) -> list[tuple[str, int]]:
        applications = self._filtered_applications(user_id, filters)
        nature = func.coalesce(func.nullif(applications.c.nature, ""), "UNKNOWN").label("nature")
        result = await self.session.execute(
            select(nature, func.count().label("count"))
            .group_by(nature)
            .order_by(func.count().desc(), nature.asc())
        )
        return [(row.nature, row.count) for row in result]

    async def get_application_trend(
        self, user_id: UUID, filters: ApplicationFilterParams, granularity: TrendGranularity
    ) -> list[tuple[object, int]]:
        applications = self._filtered_applications(user_id, filters)
        period = applications.c.application_date
        if granularity is TrendGranularity.WEEK:
            period = cast(func.date_trunc("week", applications.c.application_date), Date)
        period = period.label("period")
        result = await self.session.execute(
            select(period, func.count().label("count"))
            .group_by(period)
            .order_by(period.asc())
        )
        return [(row.period, row.count) for row in result]
