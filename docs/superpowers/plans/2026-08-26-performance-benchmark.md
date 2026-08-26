# Performance Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a reproducible local Docker benchmark for 1000+ user applications, optimize only measured failures, and report evidence.

**Architecture:** A backend-only benchmark module seeds a uniquely named user/company/application dataset with ORM bulk operations, obtains a JWT once, and repeatedly measures real HTTP endpoints. It prints JSON and Markdown-ready statistics, optionally records EXPLAIN evidence only for endpoints exceeding the 0.8s target, and cleans only its marker-scoped records.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL 16 Docker container, httpx, pytest, Vite.

**Spec:** User-provided Phase 6 Performance Benchmark & Evidence-Driven Optimization request (2026-08-26).

## Global Constraints

- Use Docker-based local results only; never label them production results.
- Seed 1000–1500 applications with a unique `phase6-perf-<run-id>` marker and delete only that user/data after measurement.
- Reuse one JWT for HTTP runs; warm up 1–3 times and record at least 10 measured warm runs.
- Do not call or modify Kimi, add a mutation queue, use Redis/Elasticsearch/materialized views, or run `docker compose down -v`.
- Perform SQL investigation and query changes only when measured median/p95 materially exceeds 0.8s.

---

### Task 1: Reproducible backend benchmark harness

**Files:**
- Create: `backend/scripts/benchmark_applications.py`
- Create: `backend/tests/test_benchmark_applications.py`

**Interfaces:**
- Produces: `BenchmarkDataset`, `measure_endpoint`, `summarize_runs`, and `cleanup_dataset` functions.
- Consumes: async SQLAlchemy session factory, existing password hashing/auth service, and HTTP endpoints on `http://localhost:8000/api/v1`.

- [ ] Write failing unit tests for p50/p95/min/max summary and marker-scoped cleanup selection.
- [ ] Run `pytest tests/test_benchmark_applications.py` to verify RED.
- [ ] Implement deterministic 1000-record fixture generation, batch ORM seed, one-token endpoint runner, and exact cleanup.
- [ ] Run the focused pytest test to verify GREEN.

### Task 2: Docker baseline and evidence collection

**Files:**
- Modify: `backend/scripts/benchmark_applications.py`
- Create: `benchmarks/phase6-performance-baseline.json`

**Interfaces:**
- Produces: cold and warm statistics for list/search/status/industry/type/date/multi-filter/sort and five dashboard endpoints.
- Consumes: running Docker services and the task-one harness.

- [ ] Run the benchmark with 1000+ records, 2 warm-ups, and 10 warm samples per endpoint.
- [ ] Record Docker services, PostgreSQL version, dataset company/application counts, host/runtime information, raw samples, and summary results.
- [ ] For every endpoint with median or p95 above 0.8s, capture `EXPLAIN (ANALYZE, BUFFERS)` and add evidence to the JSON report.

### Task 3: Evidence-driven backend optimization (conditional)

**Files:**
- Modify only files identified by Task 2 SQL evidence.
- Modify: `backend/tests/test_applications.py` or `backend/tests/test_dashboard.py` only if the existing correctness suite lacks protection for the changed query.

**Interfaces:**
- Consumes: actual slow SQL and EXPLAIN evidence from Task 2.
- Produces: minimal query/load/index change with unchanged filtering, sorting, pagination, ownership, and metrics semantics.

- [ ] If no endpoint exceeds the threshold, record “no backend query modification justified” and skip this task.
- [ ] If an endpoint exceeds the threshold, add/verify a correctness regression before modifying its query.
- [ ] Apply one minimal fix, rerun the full endpoint measurement set, and retain it only if the measured result improves.
- [ ] Run focused and full backend tests plus Ruff for changed backend code.

### Task 4: Frontend and IndexedDB evidence

**Files:**
- Create: `frontend/src/benchmarks/localApplicationSanity.test.ts`
- Modify: `benchmarks/phase6-performance-baseline.json`

**Interfaces:**
- Produces: latest production build raw/gzip chunk measurements and a 1000-record Guest IndexedDB list/filter/dashboard timing sanity result.
- Consumes: existing `LocalApplicationDataSource` and production build output.

- [ ] Write the IndexedDB sanity test first for 1000 marked Guest records and assert list/filter/dashboard return correct results without an O(n²) regression guard violation.
- [ ] Run the test to verify RED, add only benchmark helper code if required, then verify GREEN.
- [ ] Run production build, record actual chunks/raw/gzip, and inspect import patterns before considering any frontend change.
- [ ] Split or tune frontend chunks only with demonstrated first-load/bundle evidence; otherwise record no frontend modification justified.

### Task 5: Verification, cleanup, and report

**Files:**
- Modify: `benchmarks/phase6-performance-baseline.json`

- [ ] Run exact benchmark cleanup and verify no marker-scoped user/applications remain.
- [ ] Run backend targeted/full tests and Ruff if backend changes exist; run frontend full tests and production build.
- [ ] Run `git diff --check` and `git status --short`.
- [ ] Commit benchmark tooling/data independently using explicit paths: `test: add application performance benchmark`.
- [ ] Commit an actual proven optimization separately, if one exists.
