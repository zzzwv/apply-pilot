import uuid
from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import ApplicationStatusLog


@pytest.fixture
def client() -> Iterator[TestClient]:
    async def healthy() -> None:
        return None

    with TestClient(create_app(health_check=healthy), raise_server_exceptions=False) as test_client:
        yield test_client


def _register_and_headers(client: TestClient) -> dict[str, str]:
    unique = uuid.uuid4().hex[:12]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": f"phase2_{unique}",
            "email": f"phase2_{unique}@example.com",
            "password": "password-123",
        },
    )
    assert response.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": f"phase2_{unique}", "password": "password-123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _create_company(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/companies",
        headers=headers,
        json={"full_name": f"Phase 2 Test Company {uuid.uuid4().hex}"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _application_payload(company_id: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "company_id": company_id,
        "job_title": "Backend Engineer",
        "application_type": "autumn_fulltime",
        "application_date": date.today().isoformat(),
        "channel": "official_campus",
        "current_status": "APPLIED",
        "city": "Shanghai",
    }
    payload.update(overrides)
    return payload


def _create_application(
    client: TestClient, headers: dict[str, str], company_id: str, **overrides: object
) -> dict[str, object]:
    response = client.post(
        "/api/v1/applications", headers=headers, json=_application_payload(company_id, **overrides)
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_create_application_assigns_current_user_and_creates_initial_status_log(
    client: TestClient,
) -> None:
    """Breaks if creation trusts a client user_id or omits the initial history entry."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)

    application = _create_application(client, headers, company_id)
    logs = client.get(f"/api/v1/applications/{application['id']}/status-logs", headers=headers)
    current_user = client.get("/api/v1/auth/me", headers=headers)

    assert application["user_id"] == current_user.json()["data"]["id"]
    assert application["company_id"] == company_id
    assert application["current_status"] == "APPLIED"
    assert logs.status_code == 200
    assert len(logs.json()["data"]["items"]) == 1
    initial_log = logs.json()["data"]["items"][0]
    assert initial_log["application_id"] == application["id"]
    assert initial_log["from_status"] is None
    assert initial_log["to_status"] == "APPLIED"
    assert initial_log["remark"] is None


def test_application_list_is_paginated_and_scoped_to_current_user(client: TestClient) -> None:
    """Breaks if list pagination leaks another user's records or ignores its defaults."""
    owner_headers = _register_and_headers(client)
    other_headers = _register_and_headers(client)
    company_id = _create_company(client, owner_headers)
    _create_application(client, owner_headers, company_id, job_title="First role")
    _create_application(client, owner_headers, company_id, job_title="Second role")
    _create_application(client, other_headers, company_id, job_title="Private role")

    response = client.get("/api/v1/applications?page=1&page_size=1", headers=owner_headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["job_title"] in {"First role", "Second role"}


def test_user_cannot_read_update_delete_or_view_logs_for_other_application(
    client: TestClient,
) -> None:
    """Breaks if any owner-scoped endpoint fetches by application ID alone (IDOR)."""
    owner_headers = _register_and_headers(client)
    intruder_headers = _register_and_headers(client)
    company_id = _create_company(client, owner_headers)
    application = _create_application(client, owner_headers, company_id)
    application_url = f"/api/v1/applications/{application['id']}"

    for response in (
        client.get(application_url, headers=intruder_headers),
        client.put(application_url, headers=intruder_headers, json={"job_title": "stolen"}),
        client.delete(application_url, headers=intruder_headers),
        client.get(f"{application_url}/status-logs", headers=intruder_headers),
    ):
        assert response.status_code == 404
        assert response.json()["code"] == 40001


def test_user_cannot_change_other_application_status(client: TestClient) -> None:
    """Breaks if the status mutation bypasses the application's ownership check."""
    owner_headers = _register_and_headers(client)
    intruder_headers = _register_and_headers(client)
    company_id = _create_company(client, owner_headers)
    application = _create_application(client, owner_headers, company_id)

    response = client.patch(
        f"/api/v1/applications/{application['id']}/status",
        headers=intruder_headers,
        json={"status": "FIRST_INTERVIEW", "remark": "attempted access"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == 40001


def test_update_application_changes_business_fields_but_rejects_status(client: TestClient) -> None:
    """Breaks if regular updates can bypass the audited status-change endpoint."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    application = _create_application(client, headers, company_id)

    updated = client.put(
        f"/api/v1/applications/{application['id']}",
        headers=headers,
        json={"job_title": "Staff Backend Engineer", "note": "updated"},
    )
    forbidden_status = client.put(
        f"/api/v1/applications/{application['id']}",
        headers=headers,
        json={"current_status": "OFFER_RECEIVED"},
    )

    assert updated.status_code == 200
    assert updated.json()["data"]["job_title"] == "Staff Backend Engineer"
    assert updated.json()["data"]["note"] == "updated"
    assert forbidden_status.status_code == 422
    assert forbidden_status.json()["code"] == 40004


def test_status_change_creates_one_correct_log_and_same_status_does_not_duplicate(
    client: TestClient,
) -> None:
    """Breaks if changed logs have wrong endpoints, lose remarks, or repeat unchanged states."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    application = _create_application(client, headers, company_id)
    status_url = f"/api/v1/applications/{application['id']}/status"

    changed = client.patch(
        status_url,
        headers=headers,
        json={"status": "FIRST_INTERVIEW", "remark": "first round done"},
    )
    unchanged = client.patch(
        status_url, headers=headers, json={"status": "FIRST_INTERVIEW", "remark": "ignored"}
    )
    logs = client.get(f"/api/v1/applications/{application['id']}/status-logs", headers=headers)

    assert changed.status_code == 200
    assert changed.json()["data"]["current_status"] == "FIRST_INTERVIEW"
    assert unchanged.status_code == 200
    assert logs.status_code == 200
    assert [
        (item["from_status"], item["to_status"], item["remark"])
        for item in logs.json()["data"]["items"]
    ] == [
        (None, "APPLIED", None),
        ("APPLIED", "FIRST_INTERVIEW", "first round done"),
    ]


def test_invalid_status_is_rejected(client: TestClient) -> None:
    """Breaks if status values outside the established fourteen-state enum reach persistence."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    application = _create_application(client, headers, company_id)

    response = client.patch(
        f"/api/v1/applications/{application['id']}/status",
        headers=headers,
        json={"status": "MAGIC_STATUS"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == 40004


def test_status_change_rolls_back_when_status_log_insert_fails(client: TestClient) -> None:
    """Breaks if an application status commits even though its audit-log write fails."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    application = _create_application(client, headers, company_id)
    application_id = application["id"]

    def fail_status_log_insert(session: Session, *_: object) -> None:
        if any(isinstance(entity, ApplicationStatusLog) for entity in session.new):
            raise RuntimeError("forced status log failure")

    event.listen(Session, "before_flush", fail_status_log_insert)
    try:
        response = client.patch(
            f"/api/v1/applications/{application_id}/status",
            headers=headers,
            json={"status": "FIRST_INTERVIEW", "remark": "must roll back"},
        )
    finally:
        event.remove(Session, "before_flush", fail_status_log_insert)

    detail = client.get(f"/api/v1/applications/{application_id}", headers=headers)
    logs = client.get(f"/api/v1/applications/{application_id}/status-logs", headers=headers)
    assert response.status_code == 500
    assert detail.json()["data"]["current_status"] == "APPLIED"
    assert len(logs.json()["data"]["items"]) == 1


def test_batch_delete_only_deletes_current_users_applications(client: TestClient) -> None:
    """Breaks if batch deletion accepts an arbitrary UUID list without ownership scoping."""
    owner_headers = _register_and_headers(client)
    other_headers = _register_and_headers(client)
    company_id = _create_company(client, owner_headers)
    own_application = _create_application(client, owner_headers, company_id)
    other_application = _create_application(client, other_headers, company_id)

    response = client.post(
        "/api/v1/applications/batch-delete",
        headers=owner_headers,
        json={"ids": [own_application["id"], other_application["id"]]},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"deleted_count": 1}
    assert (
        client.get(
            f"/api/v1/applications/{own_application['id']}", headers=owner_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/applications/{other_application['id']}", headers=other_headers
        ).status_code
        == 200
    )


def test_delete_application_removes_its_status_logs(client: TestClient) -> None:
    """Breaks if hard deletion leaves audit logs orphaned instead of following the FK cascade."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    application = _create_application(client, headers, company_id)

    response = client.delete(f"/api/v1/applications/{application['id']}", headers=headers)
    logs = client.get(f"/api/v1/applications/{application['id']}/status-logs", headers=headers)

    assert response.status_code == 200
    assert response.json()["data"] == {"deleted_count": 1}
    assert logs.status_code == 404
