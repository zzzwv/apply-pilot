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


def _create_company(
    client: TestClient, headers: dict[str, str], **overrides: object
) -> str:
    payload: dict[str, object] = {"full_name": f"Phase 2 Test Company {uuid.uuid4().hex}"}
    payload.update(overrides)
    response = client.post(
        "/api/v1/companies",
        headers=headers,
        json=payload,
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


@pytest.mark.parametrize(
    ("keyword", "job_title", "note"),
    [
        ("Example Holdings", "Platform Engineer", "ordinary note"),
        ("Example", "Platform Engineer", "ordinary note"),
        ("Platform", "Platform Engineer", "ordinary note"),
        ("Artificial", "Platform Engineer", "ordinary note"),
        ("STATE_OWNED", "Platform Engineer", "ordinary note"),
        ("unique private note", "Platform Engineer", "unique private note"),
        ("example", "Platform Engineer", "ordinary note"),
    ],
)
def test_keyword_search_matches_every_required_field_case_insensitively(
    client: TestClient, keyword: str, job_title: str, note: str
) -> None:
    """Breaks if any required search field is omitted or ILIKE becomes case-sensitive."""
    headers = _register_and_headers(client)
    company_id = _create_company(
        client,
        headers,
        full_name=f"Example Holdings {uuid.uuid4().hex}",
        short_name="Example",
        industry="Artificial Intelligence",
        nature="STATE_OWNED",
    )
    expected = _create_application(client, headers, company_id, job_title=job_title, note=note)
    unrelated_company = _create_company(
        client, headers, full_name=f"Other Company {uuid.uuid4().hex}"
    )
    _create_application(
        client,
        headers,
        unrelated_company,
        job_title="Unrelated Role",
        note="unrelated",
    )

    response = client.get(f"/api/v1/applications?keyword={keyword}", headers=headers)

    assert response.status_code == 200
    assert {item["id"] for item in response.json()["data"]["items"]} == {expected["id"]}


def test_empty_keyword_returns_the_normal_owned_list(client: TestClient) -> None:
    """Breaks if whitespace adds a meaningless search predicate or changes list results."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    first = _create_application(client, headers, company_id, job_title="First")
    second = _create_application(client, headers, company_id, job_title="Second")

    response = client.get("/api/v1/applications?keyword=%20%20%20", headers=headers)

    assert response.status_code == 200
    assert {item["id"] for item in response.json()["data"]["items"]} == {first["id"], second["id"]}


def test_combined_filters_return_only_the_matching_owned_application(client: TestClient) -> None:
    """Breaks if any filter overwrites another instead of being AND-combined."""
    headers = _register_and_headers(client)
    matching_name = f"AI State Company {uuid.uuid4().hex}"
    matching_company = _create_company(
        client,
        headers,
        full_name=matching_name,
        industry="Artificial Intelligence",
        nature="STATE_OWNED",
        size="1000-5000",
    )
    other_company = _create_company(
        client,
        headers,
        full_name=f"Other Private Company {uuid.uuid4().hex}",
        industry="Internet",
        nature="PRIVATE",
        size="50-200",
    )
    matching = _create_application(
        client,
        headers,
        matching_company,
        job_title="AI Engineer",
        application_type="autumn_fulltime",
        application_date="2026-08-20",
        current_status="FIRST_INTERVIEW",
    )
    _create_application(
        client,
        headers,
        other_company,
        job_title="AI Engineer",
        application_type="autumn_fulltime",
        application_date="2026-08-20",
        current_status="FIRST_INTERVIEW",
    )

    response = client.get(
        "/api/v1/applications?keyword=AI&status=FIRST_INTERVIEW,SECOND_INTERVIEW"
        "&company_nature=STATE_OWNED&application_type=autumn_fulltime"
        "&industry=Artificial%20Intelligence&company_size=1000-5000"
        "&date_from=2026-08-01&date_to=2026-08-31",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert [item["id"] for item in data["items"]] == [matching["id"]]
    assert data["items"][0]["company"] == {
        "id": matching_company,
        "full_name": matching_name,
        "short_name": None,
        "industry": "Artificial Intelligence",
        "nature": "STATE_OWNED",
        "size": "1000-5000",
    }


def test_multiple_status_filter_and_filtered_pagination_count_results(client: TestClient) -> None:
    """Breaks if multi-value status filters or post-filter totals and offsets are wrong."""
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers)
    for status in ("APPLIED", "FIRST_INTERVIEW", "SECOND_INTERVIEW", "RESUME_REJECTED"):
        _create_application(client, headers, company_id, current_status=status)

    response = client.get(
        "/api/v1/applications?status=APPLIED,FIRST_INTERVIEW,SECOND_INTERVIEW&page=2&page_size=2",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["current_status"] in {"APPLIED", "FIRST_INTERVIEW", "SECOND_INTERVIEW"}


def test_sorts_by_date_company_name_and_business_status_priority(client: TestClient) -> None:
    """Breaks if sorting ignores dates/company display names or uses enum text for status order."""
    headers = _register_and_headers(client)
    zulu_company = _create_company(
        client, headers, full_name=f"Zulu {uuid.uuid4().hex}", short_name="Zulu"
    )
    alpha_company = _create_company(
        client, headers, full_name=f"Alpha {uuid.uuid4().hex}", short_name="Alpha"
    )
    newest = _create_application(
        client,
        headers,
        zulu_company,
        application_date="2026-08-20",
        current_status="OFFER_RECEIVED",
    )
    oldest = _create_application(
        client, headers, alpha_company, application_date="2026-08-01", current_status="APPLIED"
    )
    progressing = _create_application(
        client,
        headers,
        alpha_company,
        application_date="2026-08-10",
        current_status="FIRST_INTERVIEW",
    )

    date_asc = client.get("/api/v1/applications?sort=application_date_asc", headers=headers)
    company_asc = client.get("/api/v1/applications?sort=company_name_asc", headers=headers)
    status_priority = client.get("/api/v1/applications?sort=status_priority_desc", headers=headers)
    default = client.get("/api/v1/applications", headers=headers)

    assert [item["id"] for item in date_asc.json()["data"]["items"]] == [
        oldest["id"],
        progressing["id"],
        newest["id"],
    ]
    assert {item["id"] for item in company_asc.json()["data"]["items"][:2]} == {
        oldest["id"],
        progressing["id"],
    }
    assert status_priority.json()["data"]["items"][0]["id"] == progressing["id"]
    assert default.json()["data"]["items"][0]["id"] == newest["id"]


@pytest.mark.parametrize(
    "query",
    [
        "status=UNKNOWN_STATUS",
        "application_type=unknown_type",
        "sort=unknown_sort",
        "page=0",
        "page_size=0",
        "page_size=101",
        "date_from=2026-08-31&date_to=2026-08-01",
    ],
)
def test_invalid_list_filter_parameters_are_rejected(client: TestClient, query: str) -> None:
    """Breaks if malformed filters are silently ignored instead of returning validation errors."""
    headers = _register_and_headers(client)

    response = client.get(f"/api/v1/applications?{query}", headers=headers)

    assert response.status_code == 422
    assert response.json()["code"] == 40004


def test_search_input_is_parameterized_and_never_leaks_other_users_rows(client: TestClient) -> None:
    """Breaks if keyword matching interpolates SQL or searches before applying owner scope."""
    owner_headers = _register_and_headers(client)
    other_headers = _register_and_headers(client)
    company_id = _create_company(
        client, owner_headers, full_name=f"Shared Search Company {uuid.uuid4().hex}"
    )
    _create_application(client, owner_headers, company_id, note="shared secret")
    other = _create_application(client, other_headers, company_id, note="shared secret")

    injection = client.get(
        "/api/v1/applications?keyword=%27%20OR%201%3D1%20--", headers=owner_headers
    )
    shared = client.get("/api/v1/applications?keyword=shared%20secret", headers=owner_headers)

    assert injection.status_code == 200
    assert injection.json()["data"]["items"] == []
    assert {item["id"] for item in shared.json()["data"]["items"]}.isdisjoint({other["id"]})
