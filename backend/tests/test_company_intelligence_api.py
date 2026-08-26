import uuid
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.company_intelligence.schemas import (
    CompanyCandidate,
    CompanyIntelligenceSearchResult,
    RecruitmentLinkCandidate,
)
from app.core.database import get_session
from app.models import Company, RecruitmentLink
from app.models.enums import (
    LinkStatus,
    RecruitmentChannel,
    RecruitmentLinkType,
    VerificationStatus,
)


class EmptySession:
    async def commit(self) -> None:
        return None

    async def refresh(
        self, _: object, attribute_names: list[str] | None = None
    ) -> None:
        return None


def _candidate(**overrides: object) -> CompanyCandidate:
    values: dict[str, object] = {
        "company_name": "Acme Corporation",
        "short_name": "Acme",
        "industry": "Technology",
        "company_nature": "PRIVATE",
        "company_size": "1000-5000",
        "official_website": "https://www.acme.example",
        "description": "Candidate description",
    }
    values.update(overrides)
    return CompanyCandidate(**values)


@pytest.fixture
def authenticated_client() -> Iterator[TestClient]:
    from app.main import create_app

    app = create_app(health_check=lambda: None)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="actor-123")

    async def get_empty_session() -> EmptySession:
        yield EmptySession()

    app.dependency_overrides[get_session] = get_empty_session
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_company_intelligence_endpoints_require_authentication() -> None:
    """Breaks if preview or confirmation permits anonymous persistence/search."""
    from app.main import create_app

    app = create_app(health_check=lambda: None)
    with TestClient(app, raise_server_exceptions=False) as client:
        search = client.post("/api/v1/company-intelligence/search", json={"company_name": "Acme"})
        confirm = client.post(
            "/api/v1/company-intelligence/confirm",
            json={"company": _candidate().model_dump(mode="json")},
        )

    assert search.status_code == 401
    assert confirm.status_code == 401


def test_search_returns_editable_preview_and_scopes_rate_limit_to_current_user(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Breaks if search hides candidate data or omits the authenticated rate-limit actor."""
    from app.api import company_intelligence as api

    class SearchService:
        actor_ids: list[object] = []

        def __init__(self, _: object) -> None:
            pass

        async def search_company(
            self, request: object, *, actor_id: object
        ) -> CompanyIntelligenceSearchResult:
            self.actor_ids.append(actor_id)
            assert getattr(request, "company_name") == "acme corporation"
            return CompanyIntelligenceSearchResult(company=_candidate())

    monkeypatch.setattr(api, "CompanyIntelligenceService", SearchService)

    response = authenticated_client.post(
        "/api/v1/company-intelligence/search", json={"company_name": "  Acme Corporation  "}
    )

    assert response.status_code == 200
    assert response.json()["data"]["company"]["company_name"] == "acme corporation"
    assert response.json()["data"]["allow_manual_input"] is True
    assert SearchService.actor_ids == ["actor-123"]


def test_search_returns_manual_fallback_without_persisting(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Breaks if a failed enrichment path becomes an error instead of a usable manual fallback."""
    from app.api import company_intelligence as api

    class FallbackService:
        def __init__(self, _: object) -> None:
            pass

        async def search_company(
            self, _: object, *, actor_id: object
        ) -> CompanyIntelligenceSearchResult:
            assert actor_id == "actor-123"
            return CompanyIntelligenceSearchResult(
                partial=True,
                warnings=["company intelligence provider is temporarily unavailable"],
            )

    monkeypatch.setattr(api, "CompanyIntelligenceService", FallbackService)

    response = authenticated_client.post(
        "/api/v1/company-intelligence/search", json={"company_name": "Unavailable Inc"}
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "company": None,
        "recruitment_links": [],
        "sources": [],
        "partial": True,
        "warnings": ["company intelligence provider is temporarily unavailable"],
        "allow_manual_input": True,
    }


def test_confirmation_returns_the_server_persisted_selection(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Breaks if confirm is absent or bypasses the server's persistence result."""
    from app.api import company_intelligence as api
    from app.schemas.company import (
        CompanyIntelligenceConfirmResponse,
        CompanyRead,
        ConfirmedRecruitmentLinkRead,
    )

    class ConfirmationService:
        received_aliases: list[str] = []

        def __init__(self, _: object) -> None:
            pass

        async def confirm(self, request: object) -> CompanyIntelligenceConfirmResponse:
            type(self).received_aliases = list(getattr(request, "aliases"))
            return CompanyIntelligenceConfirmResponse(
                company=CompanyRead(
                    id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    full_name="acme corporation",
                ),
                created=True,
                aliases=["acme"],
                recruitment_links=[
                    ConfirmedRecruitmentLinkRead(
                        url="https://jobs.acme.example/campus",
                        title="Acme campus careers",
                        channel_type="official_campus",
                        claimed_official=True,
                    )
                ],
            )

    monkeypatch.setattr(api, "CompanyService", ConfirmationService)
    response = authenticated_client.post(
        "/api/v1/company-intelligence/confirm",
        json={
            "company": _candidate().model_dump(mode="json"),
            "aliases": ["Acme"],
            "selected_recruitment_links": [
                {
                    "title": "Acme campus careers",
                    "url": "https://jobs.acme.example/campus",
                    "channel_type": "official_campus",
                    "claimed_official": True,
                    "verification_status": "verified",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["created"] is True
    assert response.json()["data"]["company"]["id"] == "11111111-1111-1111-1111-111111111111"
    assert ConfirmationService.received_aliases == ["acme"]


@pytest.mark.asyncio
async def test_confirmation_creates_company_aliases_and_only_selected_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Breaks if confirmation drops editable selections or persists unselected preview links."""
    from app.schemas.company import CompanyIntelligenceConfirmRequest
    from app.services import company_service

    class MemorySession:
        def __init__(self) -> None:
            self.added: list[object] = []
            self.commits = 0

        def add(self, entity: object) -> None:
            if isinstance(entity, Company) and entity.id is None:
                entity.id = uuid.uuid4()
            self.added.append(entity)

        async def commit(self) -> None:
            self.commits += 1

        async def refresh(
            self, _: object, attribute_names: list[str] | None = None
        ) -> None:
            return None

    class EmptyRepository:
        def __init__(self, session: MemorySession) -> None:
            self.session = session

        async def find_by_name_or_alias(self, _: str) -> Company | None:
            return None

        def add(self, company: Company) -> Company:
            self.session.add(company)
            return company

    monkeypatch.setattr(company_service, "CompanyRepository", EmptyRepository)
    session = MemorySession()
    request = CompanyIntelligenceConfirmRequest(
        company=_candidate(),
        aliases=["Acme", "ACME", "Acme China"],
        selected_recruitment_links=[
            RecruitmentLinkCandidate(
                title="Acme campus careers",
                url="https://jobs.acme.example/campus",
                channel_type="official_campus",
                claimed_official=True,
                verification_status=VerificationStatus.VERIFIED,
            )
        ],
    )

    confirmation = await company_service.CompanyService(session).confirm(request)

    company = next(item for item in session.added if isinstance(item, Company))
    assert confirmation.created is True
    assert company.full_name == "acme corporation"
    assert [alias.alias for alias in company.aliases] == ["acme", "acme china"]
    assert [link.url for link in company.recruitment_links] == ["https://jobs.acme.example/campus"]
    assert company.recruitment_links[0].verification_status is VerificationStatus.UNVERIFIED
    assert company.recruitment_links[0].valid_status is LinkStatus.UNKNOWN
    assert session.commits == 1


@pytest.mark.asyncio
async def test_confirmation_deduplicates_existing_data_without_overwriting_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Breaks if a second confirmation duplicates selections or overwrites established fields."""
    from app.schemas.company import CompanyIntelligenceConfirmRequest
    from app.services import company_service

    existing = Company(
        id=uuid.uuid4(),
        full_name="Acme Corporation",
        industry="Established industry",
        official_website="https://established.acme.example",
    )
    existing.recruitment_links.append(
        RecruitmentLink(
            company_id=existing.id,
            url="https://jobs.acme.example/campus",
            channel=RecruitmentChannel.OFFICIAL_CAMPUS,
            link_type=RecruitmentLinkType.OFFICIAL,
        )
    )

    class MemorySession:
        def __init__(self) -> None:
            self.commits = 0

        async def commit(self) -> None:
            self.commits += 1

        async def refresh(
            self, _: object, attribute_names: list[str] | None = None
        ) -> None:
            return None

    class ExistingRepository:
        def __init__(self, _: MemorySession) -> None:
            pass

        async def find_by_name_or_alias(self, _: str) -> Company:
            return existing

        def add(self, _: Company) -> Company:
            raise AssertionError("existing company must not be inserted again")

    monkeypatch.setattr(company_service, "CompanyRepository", ExistingRepository)
    request = CompanyIntelligenceConfirmRequest(
        company=_candidate(
            industry="Untrusted replacement industry",
            official_website="https://untrusted.acme.example",
        ),
        aliases=["Acme", "acme", "Acme China"],
        selected_recruitment_links=[
            RecruitmentLinkCandidate(
                title="duplicate",
                url="https://jobs.acme.example/campus",
                channel_type="official_campus",
            ),
            RecruitmentLinkCandidate(
                title="new",
                url="https://jobs.acme.example/social",
                channel_type="official_social",
                verification_status=VerificationStatus.VERIFIED,
            ),
        ],
    )

    confirmation = await company_service.CompanyService(MemorySession()).confirm(request)

    assert confirmation.created is False
    assert existing.industry == "Established industry"
    assert existing.official_website == "https://established.acme.example"
    assert [alias.alias for alias in existing.aliases] == ["acme", "acme china"]
    assert [link.url for link in existing.recruitment_links] == [
        "https://jobs.acme.example/campus",
        "https://jobs.acme.example/social",
    ]
    assert existing.recruitment_links[-1].verification_status is VerificationStatus.UNVERIFIED


@pytest.mark.asyncio
async def test_confirmation_rejects_alias_owned_by_another_company(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Breaks if confirming NewCo can claim an alias already resolved to ExistingCo."""
    from app.core.errors import AppError
    from app.schemas.company import CompanyIntelligenceConfirmRequest
    from app.services import company_service

    existing = Company(id=uuid.uuid4(), full_name="ExistingCo")

    class MemorySession:
        def __init__(self) -> None:
            self.added: list[Company] = []
            self.commits = 0

        def add(self, company: Company) -> None:
            if company.id is None:
                company.id = uuid.uuid4()
            self.added.append(company)

        async def commit(self) -> None:
            self.commits += 1

        async def refresh(
            self, _: object, attribute_names: list[str] | None = None
        ) -> None:
            return None

    class AliasOwnershipRepository:
        def __init__(self, session: MemorySession) -> None:
            self.session = session

        async def find_by_name_or_alias(self, name: str) -> Company | None:
            return existing if name == "existingco" else None

        def add(self, company: Company) -> Company:
            self.session.add(company)
            return company

    monkeypatch.setattr(company_service, "CompanyRepository", AliasOwnershipRepository)
    session = MemorySession()
    request = CompanyIntelligenceConfirmRequest(
        company=_candidate(company_name="NewCo"),
        aliases=["ExistingCo"],
    )

    with pytest.raises(AppError) as error:
        await company_service.CompanyService(session).confirm(request)

    assert error.value.status_code == 409
    assert session.added == []
    assert session.commits == 0
