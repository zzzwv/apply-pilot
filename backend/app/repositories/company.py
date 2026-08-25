from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company
from app.repositories.base import Repository


class CompanyRepository(Repository[Company]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Company)

    async def get_by_id(self, company_id: object) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def get_by_full_name(self, full_name: str) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.full_name == full_name))
        return result.scalar_one_or_none()
