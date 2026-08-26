import uuid

import pytest
from sqlalchemy import delete, select

from app.company_intelligence.schemas import CompanyCandidate, RecruitmentLinkCandidate
from app.core.database import async_session_factory, engine
from app.models import Company
from app.schemas.company import CompanyIntelligenceConfirmRequest
from app.services.company_service import CompanyService

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def _cleanup_company(full_name: str) -> None:
    try:
        async with async_session_factory() as session:
            await session.execute(delete(Company).where(Company.full_name == full_name))
            await session.commit()
    finally:
        await engine.dispose()


def _request(full_name: str, *, with_link: bool) -> CompanyIntelligenceConfirmRequest:
    selected_links = []
    if with_link:
        selected_links.append(
            RecruitmentLinkCandidate(
                title="Phase 5 async careers",
                url="https://jobs.example.test/phase5",
                channel_type="official_campus",
                claimed_official=True,
            )
        )
    return CompanyIntelligenceConfirmRequest(
        company=CompanyCandidate(
            company_name=full_name,
            official_website="https://www.example.test",
        ),
        aliases=[f"{full_name} alias"],
        selected_recruitment_links=selected_links,
    )


@pytest.mark.asyncio
async def test_confirm_company_with_recruitment_links_does_not_lazy_load() -> None:
    """A real AsyncSession must build Confirm output without implicit relationship IO."""
    full_name = f"Phase 5 Async Links {uuid.uuid4().hex}"
    try:
        async with async_session_factory() as session:
            confirmation = await CompanyService(session).confirm(
                _request(full_name, with_link=True)
            )

        assert confirmation.created is True
        assert confirmation.company.id is not None
        assert [link.url for link in confirmation.recruitment_links] == [
            "https://jobs.example.test/phase5"
        ]
    finally:
        await _cleanup_company(full_name)


@pytest.mark.asyncio
async def test_confirm_new_company_without_recruitment_links_does_not_lazy_load() -> None:
    """Confirm must return a new company even when its links collection is empty."""
    full_name = f"Phase 5 Async Empty {uuid.uuid4().hex}"
    try:
        async with async_session_factory() as session:
            confirmation = await CompanyService(session).confirm(
                _request(full_name, with_link=False)
            )

        assert confirmation.created is True
        assert confirmation.recruitment_links == []
    finally:
        await _cleanup_company(full_name)


@pytest.mark.asyncio
async def test_confirm_reuses_loaded_links_without_duplicate() -> None:
    """A second Confirm preserves existing links and does not insert a duplicate."""
    full_name = f"Phase 5 Async Reuse {uuid.uuid4().hex}"
    try:
        async with async_session_factory() as first_session:
            first = await CompanyService(first_session).confirm(
                _request(full_name, with_link=True)
            )
        async with async_session_factory() as second_session:
            second = await CompanyService(second_session).confirm(
                _request(full_name, with_link=True)
            )
            company = (
                await second_session.execute(
                    select(Company).where(Company.id == second.company.id)
                )
            ).scalar_one()
            await second_session.refresh(company, attribute_names=["recruitment_links"])

        assert first.created is True
        assert second.created is False
        assert len(second.recruitment_links) == 1
        assert len(company.recruitment_links) == 1
    finally:
        await _cleanup_company(full_name)
