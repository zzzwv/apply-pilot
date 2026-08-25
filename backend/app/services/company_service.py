from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
from app.models import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanyCreate


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.companies = CompanyRepository(session)

    async def create(self, payload: CompanyCreate) -> Company:
        if await self.companies.get_by_full_name(payload.full_name):
            raise AppError(ErrorCode.APPLICATION_DUPLICATE, "Company already exists", 409)
        company = self.companies.add(Company(full_name=payload.full_name))
        await self.session.commit()
        await self.session.refresh(company)
        return company
