from uuid import UUID

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ApplicationStatusLog, Company, JobApplication
from app.models.enums import ApplicationStatus
from app.repositories.base import Repository
from app.schemas.application import ApplicationFilterParams, ApplicationSort


class ApplicationRepository(Repository[JobApplication]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, JobApplication)

    async def get_for_user(self, application_id: UUID, user_id: UUID) -> JobApplication | None:
        result = await self.session.execute(
            select(JobApplication)
            .options(selectinload(JobApplication.company))
            .where(JobApplication.id == application_id, JobApplication.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: UUID, filters: ApplicationFilterParams
    ) -> tuple[list[JobApplication], int]:
        statement = self._apply_filters(self._base_query(user_id), filters)
        total = await self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        result = await self.session.execute(
            self._apply_pagination(self._apply_sort(statement, filters.sort), filters)
        )
        return list(result.scalars().all()), total or 0

    @staticmethod
    def _base_query(user_id: UUID):
        return (
            select(JobApplication)
            .join(Company, JobApplication.company_id == Company.id)
            .options(selectinload(JobApplication.company))
            .where(JobApplication.user_id == user_id)
        )

    @staticmethod
    def _apply_filters(statement, filters: ApplicationFilterParams):
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            statement = statement.where(
                or_(
                    Company.full_name.ilike(pattern),
                    Company.short_name.ilike(pattern),
                    JobApplication.job_title.ilike(pattern),
                    Company.industry.ilike(pattern),
                    Company.nature.ilike(pattern),
                    JobApplication.note.ilike(pattern),
                )
            )
        if filters.statuses:
            statement = statement.where(JobApplication.current_status.in_(filters.statuses))
        if filters.company_natures:
            statement = statement.where(Company.nature.in_(filters.company_natures))
        if filters.application_types:
            statement = statement.where(
                JobApplication.application_type.in_(filters.application_types)
            )
        if filters.industries:
            statement = statement.where(Company.industry.in_(filters.industries))
        if filters.company_sizes:
            statement = statement.where(Company.size.in_(filters.company_sizes))
        if filters.date_from:
            statement = statement.where(JobApplication.application_date >= filters.date_from)
        if filters.date_to:
            statement = statement.where(JobApplication.application_date <= filters.date_to)
        return statement

    @staticmethod
    def _apply_sort(statement, sort: ApplicationSort):
        stable_order = (JobApplication.created_at.desc(), JobApplication.id.desc())
        if sort is ApplicationSort.APPLICATION_DATE_ASC:
            return statement.order_by(JobApplication.application_date.asc(), *stable_order)
        if sort is ApplicationSort.COMPANY_NAME_ASC:
            return statement.order_by(
                func.coalesce(Company.short_name, Company.full_name).asc(), *stable_order
            )
        if sort is ApplicationSort.STATUS_PRIORITY_DESC:
            status_priority = case(
                {
                    ApplicationStatus.RESUME_PASSED: 400,
                    ApplicationStatus.FIRST_INTERVIEW: 400,
                    ApplicationStatus.SECOND_INTERVIEW: 400,
                    ApplicationStatus.FINAL_INTERVIEW: 400,
                    ApplicationStatus.HR_INTERVIEW: 400,
                    ApplicationStatus.SALARY_NEGOTIATION: 400,
                    ApplicationStatus.NOT_APPLIED: 300,
                    ApplicationStatus.APPLIED: 300,
                    ApplicationStatus.OFFER_RECEIVED: 200,
                    ApplicationStatus.SIGNED: 200,
                    ApplicationStatus.OFFER_REJECTED: 100,
                    ApplicationStatus.RESUME_REJECTED: 100,
                    ApplicationStatus.INTERVIEW_REJECTED: 100,
                    ApplicationStatus.PROCESS_TERMINATED: 100,
                },
                value=JobApplication.current_status,
                else_=0,
            )
            return statement.order_by(status_priority.desc(), *stable_order)
        return statement.order_by(JobApplication.application_date.desc(), *stable_order)

    @staticmethod
    def _apply_pagination(statement, filters: ApplicationFilterParams):
        return statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    async def delete_many_for_user(self, application_ids: list[UUID], user_id: UUID) -> int:
        result = await self.session.execute(
            delete(JobApplication)
            .where(JobApplication.id.in_(application_ids), JobApplication.user_id == user_id)
            .returning(JobApplication.id)
        )
        return len(result.scalars().all())

    async def list_status_logs_for_user(
        self, application_id: UUID, user_id: UUID
    ) -> list[ApplicationStatusLog]:
        result = await self.session.execute(
            select(ApplicationStatusLog)
            .where(
                ApplicationStatusLog.application_id == application_id,
                ApplicationStatusLog.user_id == user_id,
            )
            .order_by(ApplicationStatusLog.changed_at.asc(), ApplicationStatusLog.id.asc())
        )
        return list(result.scalars().all())
