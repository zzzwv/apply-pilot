"""Regression coverage for editing an existing shared company profile."""

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    async def healthy() -> None:
        return None

    with TestClient(create_app(health_check=healthy), raise_server_exceptions=False) as test_client:
        yield test_client


def _register_and_headers(client: TestClient) -> dict[str, str]:
    unique = uuid.uuid4().hex[:12]
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "username": f"company_edit_{unique}",
            "email": f"company_edit_{unique}@example.com",
            "password": "password-123",
        },
    )
    assert registered.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": f"company_edit_{unique}", "password": "password-123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def test_existing_company_profile_can_be_read_and_updated(client: TestClient) -> None:
    """Breaks if the form cannot preload and save a selected local company profile."""
    headers = _register_and_headers(client)
    original_name = f"Example Technology {uuid.uuid4().hex}"
    updated_name = f"Example AI {uuid.uuid4().hex}"
    created = client.post(
        "/api/v1/companies",
        headers=headers,
        json={
            "full_name": original_name,
            "short_name": "Example",
            "industry": "Internet",
            "nature": "PRIVATE",
            "size": "200-500",
            "official_website": "https://old.example.com",
            "business_description": "Old profile",
        },
    )
    assert created.status_code == 201
    company_id = created.json()["data"]["id"]

    detail = client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"] == {
        "id": company_id,
        "full_name": original_name,
        "short_name": "Example",
        "industry": "Internet",
        "nature": "PRIVATE",
        "size": "200-500",
        "official_website": "https://old.example.com",
        "business_description": "Old profile",
    }

    updated = client.patch(
        f"/api/v1/companies/{company_id}",
        headers=headers,
        json={
            "full_name": updated_name,
            "short_name": "Example AI",
            "industry": "Artificial Intelligence",
            "nature": "STATE_OWNED",
            "size": "1000-5000",
            "official_website": "https://ai.example.com",
            "business_description": "Updated profile",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["data"] == {
        "id": company_id,
        "full_name": updated_name,
        "short_name": "Example AI",
        "industry": "Artificial Intelligence",
        "nature": "STATE_OWNED",
        "size": "1000-5000",
        "official_website": "https://ai.example.com",
        "business_description": "Updated profile",
    }


def test_existing_company_profile_rejects_another_company_name(client: TestClient) -> None:
    """Breaks if editing one company can create duplicate canonical company names."""
    headers = _register_and_headers(client)
    first_name = f"First Company {uuid.uuid4().hex}"
    second_name = f"Second Company {uuid.uuid4().hex}"
    first = client.post("/api/v1/companies", headers=headers, json={"full_name": first_name})
    second = client.post("/api/v1/companies", headers=headers, json={"full_name": second_name})
    assert first.status_code == second.status_code == 201

    response = client.patch(
        f"/api/v1/companies/{first.json()['data']['id']}",
        headers=headers,
        json={"full_name": second_name},
    )

    assert response.status_code == 409
