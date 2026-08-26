from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from test_applications import _register_and_headers

from app.main import create_app


@pytest.fixture
def client():
    async def healthy() -> None:
        return None

    with TestClient(create_app(health_check=healthy), raise_server_exceptions=False) as test_client:
        yield test_client


def _item(client_sync_id: str) -> dict:
    return {
        "client_sync_id": client_sync_id,
        "company": {
            "full_name": "Guest Import Company",
            "short_name": None,
            "industry": "AI",
            "nature": "PRIVATE",
            "size": None,
        },
        "job_title": "Backend Engineer",
        "application_type": "autumn_fulltime",
        "application_date": "2026-08-26",
        "channel": "official_campus",
        "resume_version": None,
        "salary": None,
        "city": None,
        "education_requirement": None,
        "deadline": None,
        "requirements": None,
        "note": None,
        "current_status": "APPLIED",
        "status_logs": [
            {
                "from_status": None,
                "to_status": "APPLIED",
                "remark": None,
                "changed_at": "2026-08-26T00:00:00Z",
            }
        ],
    }


def test_import_is_idempotent_and_returns_cloud_mapping(client: TestClient) -> None:
    headers = _register_and_headers(client)
    payload = {"applications": [_item(str(uuid4()))]}

    first = client.post("/api/v1/sync/import-applications", headers=headers, json=payload)
    second = client.post("/api/v1/sync/import-applications", headers=headers, json=payload)

    assert first.status_code == 200
    assert first.json()["data"]["imported"] == 1
    assert second.json()["data"]["reused"] == 1
    assert len(first.json()["data"]["mappings"]) == 1


def test_import_rejects_untrusted_nested_owner_fields(client: TestClient) -> None:
    """Breaks if browser-controlled nested payload data bypasses Pydantic validation."""
    headers = _register_and_headers(client)
    item = _item(str(uuid4()))
    item["status_logs"][0]["user_id"] = str(uuid4())

    response = client.post(
        "/api/v1/sync/import-applications",
        headers=headers,
        json={"applications": [item]},
    )

    assert response.status_code == 422
    assert response.json()["code"] == 40004


def test_import_rejects_malformed_status_history(client: TestClient) -> None:
    """Breaks if imported history does not form a continuous chain ending at current status."""
    headers = _register_and_headers(client)
    item = _item(str(uuid4()))
    item["status_logs"] = [
        {
            "from_status": "FIRST_INTERVIEW",
            "to_status": "OFFER_RECEIVED",
            "remark": None,
            "changed_at": "2026-08-26T00:00:00Z",
        }
    ]

    response = client.post(
        "/api/v1/sync/import-applications",
        headers=headers,
        json={"applications": [item]},
    )

    assert response.status_code == 422
    assert response.json()["code"] == 40004


@pytest.mark.parametrize(
    "mutation",
    [
        lambda item: item.update(application_type="INVALID_ENUM"),
        lambda item: item.update(application_date="not-a-date"),
        lambda item: item.update(job_title="x" * 256),
        lambda item: item["status_logs"][0].update(changed_at="not-a-timestamp"),
    ],
)
def test_import_rejects_invalid_fields(client: TestClient, mutation) -> None:
    headers = _register_and_headers(client)
    item = _item(str(uuid4()))
    mutation(item)

    response = client.post(
        "/api/v1/sync/import-applications",
        headers=headers,
        json={"applications": [item]},
    )

    assert response.status_code == 422


def test_import_requires_jwt_and_enforces_batch_limit(client: TestClient) -> None:
    unauthenticated = client.post(
        "/api/v1/sync/import-applications",
        json={"applications": [_item(str(uuid4()))]},
    )
    assert unauthenticated.status_code == 401

    headers = _register_and_headers(client)
    response = client.post(
        "/api/v1/sync/import-applications",
        headers=headers,
        json={"applications": [_item(str(uuid4())) for _ in range(201)]},
    )

    assert response.status_code == 422
