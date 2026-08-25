from collections.abc import Iterator
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from test_applications import (
    _create_application,
    _create_company,
    _register_and_headers,
)

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    async def healthy() -> None:
        return None

    with TestClient(create_app(health_check=healthy), raise_server_exceptions=False) as test_client:
        yield test_client


def test_dashboard_summary_uses_owned_records_and_status_history(client) -> None:
    """Dashboard aggregates are owner-scoped and use distinct status-log progression."""
    headers = _register_and_headers(client)
    other_headers = _register_and_headers(client)
    company_id = _create_company(
        client,
        headers,
        full_name=f"AI Company {uuid4().hex}",
        industry="人工智能",
        nature="STATE_OWNED",
    )
    _create_application(
        client,
        headers,
        company_id,
        current_status="FIRST_INTERVIEW",
        application_date="2026-08-10",
    )
    offer = _create_application(
        client,
        headers,
        company_id,
        current_status="APPLIED",
        application_date="2026-08-11",
    )
    assert client.patch(
        f"/api/v1/applications/{offer['id']}/status",
        headers=headers,
        json={"status": "FIRST_INTERVIEW"},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/applications/{offer['id']}/status",
        headers=headers,
        json={"status": "SECOND_INTERVIEW"},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/applications/{offer['id']}/status",
        headers=headers,
        json={"status": "OFFER_RECEIVED"},
    ).status_code == 200
    _create_application(
        client,
        headers,
        company_id,
        current_status="RESUME_REJECTED",
        application_date="2026-08-12",
    )
    _create_application(client, other_headers, company_id, current_status="OFFER_RECEIVED")

    response = client.get("/api/v1/dashboard/summary", headers=headers)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "total": 3,
        "in_progress": 1,
        "offer_count": 1,
        "interview_rate": 0.5,
        "offer_rate": 1 / 3,
        "rejection_rate": 1 / 3,
    }


def test_dashboard_distributions_trend_and_filters_match_application_list(client) -> None:
    """All dashboard datasets use the exact Phase 3 business filters, without dropping unknowns."""
    headers = _register_and_headers(client)
    ai_company = _create_company(
        client,
        headers,
        full_name=f"AI Corp {uuid4().hex}",
        industry="人工智能",
        nature="STATE_OWNED",
    )
    unknown_company = _create_company(client, headers, full_name=f"Unknown Corp {uuid4().hex}")
    expected = _create_application(
        client,
        headers,
        ai_company,
        current_status="FIRST_INTERVIEW",
        application_type="autumn_fulltime",
        application_date="2026-08-04",
    )
    _create_application(
        client,
        headers,
        unknown_company,
        current_status="APPLIED",
        application_type="summer_internship",
        application_date="2026-08-11",
    )
    query = (
        "application_type=autumn_fulltime&industry=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD"
        "&status=FIRST_INTERVIEW"
    )

    listed = client.get(f"/api/v1/applications?{query}", headers=headers)
    summary = client.get(f"/api/v1/dashboard/summary?{query}", headers=headers)
    statuses = client.get(f"/api/v1/dashboard/status-distribution?{query}", headers=headers)
    industries = client.get("/api/v1/dashboard/industry-distribution", headers=headers)
    natures = client.get("/api/v1/dashboard/company-nature-distribution", headers=headers)
    trend = client.get("/api/v1/dashboard/application-trend?granularity=week", headers=headers)

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]["items"]] == [expected["id"]]
    assert summary.json()["data"]["total"] == listed.json()["data"]["total"] == 1
    assert statuses.json()["data"]["items"] == [
        {"status": "FIRST_INTERVIEW", "count": 1, "percentage": 1.0}
    ]
    assert {tuple(item.items()) for item in industries.json()["data"]["items"]} == {
        (("industry", "人工智能"), ("count", 1), ("percentage", 0.5)),
        (("industry", "UNKNOWN"), ("count", 1), ("percentage", 0.5)),
    }
    assert {tuple(item.items()) for item in natures.json()["data"]["items"]} == {
        (("company_nature", "STATE_OWNED"), ("count", 1), ("percentage", 0.5)),
        (("company_nature", "UNKNOWN"), ("count", 1), ("percentage", 0.5)),
    }
    assert trend.json()["data"]["items"] == [
        {"date": "2026-08-03", "count": 1},
        {"date": "2026-08-10", "count": 1},
    ]


def test_dashboard_returns_zeroes_for_empty_filtered_result(client) -> None:
    """A filter with no records never exposes division-by-zero values."""
    headers = _register_and_headers(client)

    response = client.get(
        "/api/v1/dashboard/summary?date_from=" + date.today().replace(year=2030).isoformat(),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "total": 0,
        "in_progress": 0,
        "offer_count": 0,
        "interview_rate": 0.0,
        "offer_rate": 0.0,
        "rejection_rate": 0.0,
    }
