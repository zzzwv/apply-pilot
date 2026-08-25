from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.company_intelligence.normalization import normalize_company_name
from app.models import Company, CompanyAlias
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

    async def find_by_name_or_alias(self, normalized_name: str) -> Company | None:
        """Resolve an exact company name or deterministic alias before any remote lookup."""
        name = normalize_company_name(normalized_name)
        statement = (
            select(Company)
            .outerjoin(CompanyAlias)
            .options(selectinload(Company.aliases), selectinload(Company.recruitment_links))
            .where(
                or_(
                    func.lower(func.trim(Company.full_name)) == name,
                    CompanyAlias.normalized_alias == name,
                )
            )
        )
        result = await self.session.execute(statement)
        matched = result.scalars().first()
        if matched is not None:
            return matched

        fallback = await self.session.execute(
            select(Company).options(
                selectinload(Company.aliases), selectinload(Company.recruitment_links)
            )
        )
        for company in fallback.scalars().all():
            if normalize_company_name(company.full_name) == name:
                return company
            if any(
                normalize_company_name(alias.alias) == name
                or alias.normalized_alias == name
                for alias in company.aliases
            ):
                return company
        return None

    async def search_by_name_or_alias(self, keyword: str, *, limit: int = 8) -> list[Company]:
        """Return local Company/CompanyAlias matches only; this never triggers remote lookup."""
        normalized_keyword = normalize_company_name(keyword)
        if not normalized_keyword:
            return []
        pattern = f"%{normalized_keyword}%"
        statement = (
            select(Company)
            .outerjoin(CompanyAlias)
            .where(
                or_(
                    func.lower(func.trim(Company.full_name)).like(pattern),
                    func.lower(func.trim(CompanyAlias.alias)).like(pattern),
                    CompanyAlias.normalized_alias.like(pattern),
                )
            )
            .order_by(Company.full_name)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())
