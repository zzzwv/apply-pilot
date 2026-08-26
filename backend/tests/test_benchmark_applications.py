from scripts.benchmark_applications import build_dataset, summarize_runs


def test_summarize_runs_reports_median_p95_min_and_max() -> None:
    summary = summarize_runs([0.10, 0.20, 0.30, 0.40, 0.50])

    assert summary == {"median": 0.30, "p95": 0.48, "min": 0.10, "max": 0.50}


def test_build_dataset_creates_marked_diverse_applications() -> None:
    dataset = build_dataset("phase6-perf-unit", application_count=1_000, company_count=24)

    assert dataset.marker == "phase6-perf-unit"
    assert len(dataset.companies) == 24
    assert len(dataset.applications) == 1_000
    assert {application.current_status for application in dataset.applications}
    assert {application.application_type for application in dataset.applications}
    assert all(dataset.marker in company.full_name for company in dataset.companies)
