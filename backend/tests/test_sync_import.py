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
        "company": {"full_name": "Guest Import Company", "short_name": None, "industry": "AI", "nature": "PRIVATE", "size": None},
        "job_title": "Backend Engineer", "application_type": "autumn_fulltime", "application_date": "2026-08-26", "channel": "official_campus",
        "resume_version": None, "salary": None, "city": None, "education_requirement": None, "deadline": None, "requirements": None, "note": None,
        "current_status": "APPLIED", "status_logs": [{"from_status": None, "to_status": "APPLIED", "remark": None, "changed_at": "2026-08-26T00:00:00Z"}],
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
