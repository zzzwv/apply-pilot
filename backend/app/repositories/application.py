from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApplicationStatusLog, JobApplication
from app.repositories.base import Repository


class ApplicationRepository(Repository[JobApplication]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, JobApplication)

    async def get_for_user(self, application_id: UUID, user_id: UUID) -> JobApplication | None:
        result = await self.session.execute(
            select(JobApplication).where(
                JobApplication.id == application_id, JobApplication.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: UUID, page: int, page_size: int
    ) -> tuple[list[JobApplication], int]:
        statement = select(JobApplication).where(JobApplication.user_id == user_id)
        total = await self.session.scalar(select(func.count()).select_from(statement.subquery()))
        result = await self.session.execute(
            statement.order_by(JobApplication.application_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total or 0

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
