"""Tests for the local-only company/alias lookup used by the application form."""

import uuid
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.core.database import get_session


@pytest.fixture
def authenticated_client() -> Iterator[TestClient]:
    from app.main import create_app

    app = create_app(health_check=lambda: None)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="actor-123")

    async def empty_session() -> None:
        yield None

    app.dependency_overrides[get_session] = empty_session
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_local_company_search_returns_company_and_alias_matches_without_intelligence(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Breaks if debounced local lookup can invoke remote company intelligence."""
    from app.api import companies
    from app.schemas.company import CompanyRead

    class LocalOnlyCompanyService:
        received_keywords: list[str] = []

        def __init__(self, _: object) -> None:
            pass

        async def search_local(self, keyword: str) -> list[CompanyRead]:
            type(self).received_keywords.append(keyword)
            return [
                CompanyRead(
                    id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    full_name="腾讯科技",
                )
            ]

    monkeypatch.setattr(companies, "CompanyService", LocalOnlyCompanyService)

    response = authenticated_client.get("/api/v1/companies/search?keyword=%20%E8%85%BE%E8%AE%AF%20")

    assert response.status_code == 200
    assert response.json()["data"] == [
        {"id": "11111111-1111-1111-1111-111111111111", "full_name": "腾讯科技"}
    ]
    assert LocalOnlyCompanyService.received_keywords == ["腾讯"]
