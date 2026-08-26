from sqlalchemy.ext.asyncio import AsyncSession

from app.company_intelligence.normalization import normalize_company_name
from app.core.errors import AppError, ErrorCode
from app.models import Company, CompanyAlias, RecruitmentLink
from app.models.enums import (
    LinkStatus,
    RecruitmentChannel,
    RecruitmentLinkType,
    VerificationStatus,
)
from app.repositories.company import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyIntelligenceConfirmRequest,
    CompanyIntelligenceConfirmResponse,
    CompanyRead,
    ConfirmedRecruitmentLinkRead,
)


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.companies = CompanyRepository(session)

    async def create(self, payload: CompanyCreate) -> Company:
        if await self.companies.get_by_full_name(payload.full_name):
            raise AppError(ErrorCode.APPLICATION_DUPLICATE, "Company already exists", 409)
        company = self.companies.add(Company(**payload.model_dump()))
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def search_local(self, keyword: str) -> list[CompanyRead]:
        """Find Company and CompanyAlias matches without involving company intelligence."""
        companies = await self.companies.search_by_name_or_alias(keyword)
        return [CompanyRead.model_validate(company) for company in companies]

    async def confirm(
        self, payload: CompanyIntelligenceConfirmRequest
    ) -> CompanyIntelligenceConfirmResponse:
        """Persist only explicitly selected candidate data, without trusting verification claims."""
        company = await self.companies.find_by_name_or_alias(payload.company.company_name)
        await self._ensure_aliases_are_unclaimed(company, payload.aliases)
        created = company is None
        if company is None:
            company = Company(
                full_name=payload.company.company_name,
                short_name=payload.company.short_name,
                nature=payload.company.company_nature,
                size=payload.company.company_size,
                industry=payload.company.industry,
                business_description=payload.company.description,
                official_website=payload.company.official_website,
            )
            self.companies.add(company)

        self._add_aliases(company, payload.aliases)
        self._add_selected_links(company, payload.selected_recruitment_links)
        await self.session.commit()
        await self.session.refresh(
            company,
            attribute_names=["aliases", "recruitment_links"],
        )
        return CompanyIntelligenceConfirmResponse(
            company=CompanyRead.model_validate(company),
            created=created,
            aliases=[alias.alias for alias in company.aliases],
            recruitment_links=[
                ConfirmedRecruitmentLinkRead(
                    url=link.url,
                    title=link.source_title or link.url,
                    channel_type=link.channel.value,
                    claimed_official=link.link_type is RecruitmentLinkType.OFFICIAL,
                )
                for link in company.recruitment_links
            ],
        )

    @staticmethod
    def _add_aliases(company: Company, aliases: list[str]) -> None:
        known_aliases = {normalize_company_name(company.full_name)}
        known_aliases.update(alias.normalized_alias for alias in company.aliases)
        for alias in aliases:
            normalized = normalize_company_name(alias)
            if normalized in known_aliases:
                continue
            company.aliases.append(CompanyAlias(alias=alias, normalized_alias=normalized))
            known_aliases.add(normalized)

    @staticmethod
    def _add_selected_links(company: Company, selected_links: list[object]) -> None:
        known_urls = {link.url for link in company.recruitment_links}
        for priority, candidate in enumerate(selected_links[::-1], start=1):
            if candidate.url in known_urls:
                continue
            try:
                channel = RecruitmentChannel(candidate.channel_type)
            except ValueError:
                channel = RecruitmentChannel.OTHER
            company.recruitment_links.append(
                RecruitmentLink(
                    url=candidate.url,
                    channel=channel,
                    link_type=(
                        RecruitmentLinkType.OFFICIAL
                        if candidate.claimed_official
                        else RecruitmentLinkType.THIRD_PARTY
                    ),
                    priority=priority,
                    valid_status=LinkStatus.UNKNOWN,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_url=candidate.source_url,
                    source_title=candidate.title,
                    source_type=candidate.channel_type,
                )
            )
            known_urls.add(candidate.url)

    async def _ensure_aliases_are_unclaimed(
        self, company: Company | None, aliases: list[str]
    ) -> None:
        for alias in aliases:
            owner = await self.companies.find_by_name_or_alias(normalize_company_name(alias))
            if owner is not None and not self._is_same_company(owner, company):
                raise AppError(
                    ErrorCode.COMPANY_AMBIGUOUS,
                    "Alias belongs to another company",
                    status_code=409,
                )

    @staticmethod
    def _is_same_company(first: Company, second: Company | None) -> bool:
        if second is None:
            return False
        if first is second:
            return True
        return first.id is not None and second.id is not None and first.id == second.id
