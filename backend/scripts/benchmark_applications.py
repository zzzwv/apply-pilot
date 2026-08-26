"""Docker-local Phase 6 application API benchmark with marker-scoped cleanup."""

import argparse
import asyncio
import json
import os
import platform
import statistics
import time
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import hash_password
from app.models import Company, JobApplication, User
from app.models.enums import ApplicationStatus, ApplicationType

API_BASE_URL = os.getenv("PHASE6_BENCHMARK_API_BASE_URL", "http://127.0.0.1:8000/api/v1")
BENCHMARK_PASSWORD = "phase6-benchmark-password"


@dataclass
class BenchmarkDataset:
    marker: str
    user: User
    companies: list[Company]
    applications: list[JobApplication]


def summarize_runs(samples: list[float]) -> dict[str, float]:
    if not samples:
        raise ValueError("At least one measurement is required")
    ordered = sorted(samples)
    position = (len(ordered) - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    p95 = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return {
        "median": round(statistics.median(ordered), 4),
        "p95": round(p95, 4),
        "min": round(ordered[0], 4),
        "max": round(ordered[-1], 4),
    }


def build_dataset(
    marker: str, application_count: int = 1_200, company_count: int = 30
) -> BenchmarkDataset:
    if application_count < 1_000:
        raise ValueError("application_count must be at least 1000")
    user = User(
        id=uuid.uuid4(),
        username=f"{marker}-user",
        email=f"{marker}-user@example.invalid",
        password_hash=hash_password(BENCHMARK_PASSWORD),
    )
    industries = ["AI", "互联网", "金融", "制造", "新能源", "教育"]
    natures = ["PRIVATE", "STATE_OWNED", "CENTRAL_OWNED", "FOREIGN", "STARTUP"]
    sizes = ["50以下", "50-200", "200-500", "500-1000", "1000-5000", "5000以上"]
    companies = [
        Company(
            id=uuid.uuid4(),
            full_name=f"{marker}-company-{index:03d}",
            short_name=f"P{index:03d}",
            industry=industries[index % len(industries)],
            nature=natures[index % len(natures)],
            size=sizes[index % len(sizes)],
        )
        for index in range(company_count)
    ]
    statuses = list(ApplicationStatus)
    application_types = list(ApplicationType)
    applications = [
        JobApplication(
            id=uuid.uuid4(),
            user_id=user.id,
            company_id=companies[index % company_count].id,
            job_title=f"Performance Engineer {index % 37}",
            application_type=application_types[index % len(application_types)],
            application_date=date(2026, 1, 1) + timedelta(days=index % 180),
            channel="official",
            note=f"{marker} searchable-keyword-{index % 11}",
            current_status=statuses[index % len(statuses)],
        )
        for index in range(application_count)
    ]
    return BenchmarkDataset(
        marker=marker,
        user=user,
        companies=companies,
        applications=applications,
    )


async def seed_dataset(session: AsyncSession, dataset: BenchmarkDataset) -> None:
    session.add(dataset.user)
    session.add_all(dataset.companies)
    session.add_all(dataset.applications)
    await session.commit()


async def cleanup_dataset(session: AsyncSession, marker: str) -> None:
    user_ids = select(User.id).where(User.username == f"{marker}-user")
    await session.execute(delete(User).where(User.id.in_(user_ids)))
    await session.execute(delete(Company).where(Company.full_name.like(f"{marker}-company-%")))
    await session.commit()


async def login(client: httpx.AsyncClient, username: str) -> str:
    response = await client.post(
        "/auth/login",
        json={"username_or_email": username, "password": BENCHMARK_PASSWORD},
    )
    response.raise_for_status()
    return response.json()["data"]["access_token"]


async def measure_endpoint(
    client: httpx.AsyncClient, path: str, headers: dict[str, str], warmups: int, runs: int
) -> dict[str, Any]:
    cold_started = time.perf_counter()
    cold_response = await client.get(path, headers=headers)
    cold_response.raise_for_status()
    cold = time.perf_counter() - cold_started
    for _ in range(warmups):
        response = await client.get(path, headers=headers)
        response.raise_for_status()
    samples: list[float] = []
    for _ in range(runs):
        started = time.perf_counter()
        response = await client.get(path, headers=headers)
        response.raise_for_status()
        samples.append(time.perf_counter() - started)
    return {"cold": round(cold, 4), "runs": runs, **summarize_runs(samples)}


def benchmark_endpoints() -> dict[str, str]:
    filters = "page=1&page_size=20"
    return {
        "application_list": f"/applications?{filters}",
        "application_search": f"/applications?{filters}&keyword=searchable-keyword-3",
        "application_status_filter": f"/applications?{filters}&status=APPLIED",
        "application_industry_filter": f"/applications?{filters}&industry=AI",
        "application_type_filter": f"/applications?{filters}&application_type=autumn_fulltime",
        "application_date_range": (
            f"/applications?{filters}&date_from=2026-02-01&date_to=2026-04-30"
        ),
        "application_multi_filter": (
            f"/applications?{filters}&status=APPLIED&industry=AI&company_nature=PRIVATE"
            "&application_type=autumn_fulltime"
        ),
        "application_sort": f"/applications?{filters}&sort=company_name_asc",
        "dashboard_summary": "/dashboard/summary",
        "dashboard_status_distribution": "/dashboard/status-distribution",
        "dashboard_industry_distribution": "/dashboard/industry-distribution",
        "dashboard_nature_distribution": "/dashboard/company-nature-distribution",
        "dashboard_trend": "/dashboard/application-trend?granularity=day",
    }


async def run_benchmark(
    application_count: int, company_count: int, warmups: int, runs: int
) -> dict[str, Any]:
    marker = f"phase6-perf-{uuid.uuid4().hex[:12]}"
    dataset = build_dataset(marker, application_count, company_count)
    async with async_session_factory() as session:
        await seed_dataset(session, dataset)
    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
            token = await login(client, dataset.user.username)
            headers = {"Authorization": f"Bearer {token}"}
            measurements = {
                name: await measure_endpoint(client, path, headers, warmups, runs)
                for name, path in benchmark_endpoints().items()
            }
        async with async_session_factory() as session:
            postgres_version = (await session.scalar(text("select version()"))) or "unknown"
        return {
            "environment": {
                "kind": "docker-local",
                "postgres": postgres_version,
                "platform": platform.platform(),
            },
            "dataset": {
                "marker": marker,
                "applications": len(dataset.applications),
                "companies": len(dataset.companies),
            },
            "methodology": {"warmups": warmups, "runs": runs, "target_seconds": 0.8},
            "endpoints": measurements,
        }
    finally:
        async with async_session_factory() as session:
            await cleanup_dataset(session, marker)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--applications", type=int, default=1_200)
    parser.add_argument("--companies", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    result = await run_benchmark(args.applications, args.companies, args.warmups, args.runs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
