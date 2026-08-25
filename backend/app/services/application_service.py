from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models import ApplicationStatusLog, JobApplication, User
from app.repositories.application import ApplicationRepository
from app.repositories.company import CompanyRepository
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate, ApplicationUpdate


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.applications = ApplicationRepository(session)
        self.companies = CompanyRepository(session)

    async def create_application(
        self, payload: ApplicationCreate, current_user: User
    ) -> JobApplication:
        if await self.companies.get_by_id(payload.company_id) is None:
            raise AppError(ErrorCode.COMPANY_NOT_FOUND, "Company not found", 404)
        try:
            application = self.applications.add(
                JobApplication(user_id=current_user.id, **payload.model_dump())
            )
            await self.session.flush()
            self.session.add(
                ApplicationStatusLog(
                    application_id=application.id,
                    user_id=current_user.id,
                    from_status=None,
                    to_status=application.current_status,
                )
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(application)
        return application

    async def get_application(self, application_id: UUID, current_user: User) -> JobApplication:
        application = await self.applications.get_for_user(application_id, current_user.id)
        if application is None:
            raise AppError(ErrorCode.APPLICATION_NOT_FOUND, "Application not found", 404)
        return application

    async def list_applications(
        self, current_user: User, page: int, page_size: int
    ) -> tuple[list[JobApplication], int]:
        return await self.applications.list_for_user(current_user.id, page, page_size)

    async def update_application(
        self, application_id: UUID, payload: ApplicationUpdate, current_user: User
    ) -> JobApplication:
        application = await self.get_application(application_id, current_user)
        values = payload.model_dump(exclude_unset=True)
        if "company_id" in values and await self.companies.get_by_id(values["company_id"]) is None:
            raise AppError(ErrorCode.COMPANY_NOT_FOUND, "Company not found", 404)
        for field, value in values.items():
            setattr(application, field, value)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def delete_application(self, application_id: UUID, current_user: User) -> int:
        application = await self.get_application(application_id, current_user)
        await self.session.delete(application)
        await self.session.commit()
        return 1

    async def batch_delete(self, application_ids: list[UUID], current_user: User) -> int:
        try:
            deleted_count = await self.applications.delete_many_for_user(
                application_ids, current_user.id
            )
            await self.session.commit()
            return deleted_count
        except Exception:
            await self.session.rollback()
            raise

    async def change_status(
        self, application_id: UUID, payload: ApplicationStatusUpdate, current_user: User
    ) -> JobApplication:
        try:
            application = await self.applications.get_for_user(application_id, current_user.id)
            if application is None:
                raise AppError(ErrorCode.APPLICATION_NOT_FOUND, "Application not found", 404)
            if application.current_status == payload.status:
                return application
            previous_status = application.current_status
            application.current_status = payload.status
            self.session.add(
                ApplicationStatusLog(
                    application_id=application.id,
                    user_id=current_user.id,
                    from_status=previous_status,
                    to_status=payload.status,
                    remark=payload.remark,
                )
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(application)
        return application

    async def get_status_logs(
        self, application_id: UUID, current_user: User
    ) -> list[ApplicationStatusLog]:
        await self.get_application(application_id, current_user)
        return await self.applications.list_status_logs_for_user(application_id, current_user.id)
