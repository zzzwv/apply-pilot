# Phase 5 Company Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, user-confirmed company-intelligence flow that enriches a company name without allowing LLM output to become database truth automatically.

**Architecture:** The API first resolves local Company/CompanyAlias records, then reads a Redis cache, and only then runs the Kimi provider. Candidate data is parsed with Pydantic, validated by deterministic URL/domain/link rules, returned as editable preview data, and persisted only by a confirm endpoint.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL/Alembic, Redis, HTTPX, Pydantic, React 19, Ant Design, Vitest.

**Spec:** `Prompt/Phase 5.md`; `docs/秋招_实习投递状态管理Web网站产品需求文档（PRD V1.0定稿）.md`; `docs/秋招-实习投递状态管理 Web 网站技术设计文档 V1.0.md`

## Global Constraints

- Keep virtual environments, caches, downloads and generated runtime assets beneath `E:\qiuzhao`; do not install project software on C:.
- Read Kimi configuration only through settings; default model is exactly `kimi-k2.5`.
- Kimi API keys remain backend-only and are never logged, returned, committed, or sent to the browser.
- Network candidate data remains editable and is never persisted before explicit confirmation.
- Only `http` and `https` URLs are allowed; validate every redirect hop against SSRF rules.
- Use bounded homepage plus one-hop discovery; no general crawler, login bypass, CAPTCHA bypass, or anti-bot bypass.
- Preserve Phase 1–4 behaviour and the user-owned untracked `Prompt/Phase 5.md`.

---

### Task 1: Project configuration and database provenance

**Files:**
- Modify: `backend/pyproject.toml`, `backend/app/core/config.py`, `.env.example`, `compose.yaml`
- Modify: `backend/app/models/enums.py`, `backend/app/models/company.py`, `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/20260825_0003_company_intelligence.py`
- Test: `backend/tests/test_company_intelligence_models.py`

- [ ] Write failing tests requiring recruitment-link validation metadata and the four candidate verification states.
- [ ] Run `backend/.venv/Scripts/python.exe -m pytest tests/test_company_intelligence_models.py -v` and observe model/schema failure.
- [ ] Add HTTPX dependency, non-secret Kimi/cache/rate-limit settings, verification enum and additive database columns (`verification_status`, `http_status`, `final_url`, `source_url`, `source_title`, `source_type`, `retrieved_at`).
- [ ] Generate upgrade/downgrade Alembic migration and run its targeted test.
- [ ] Commit `feat: add company intelligence configuration and provenance`.

### Task 2: Candidate schemas and deterministic utilities

**Files:**
- Create: `backend/app/company_intelligence/schemas.py`, `backend/app/company_intelligence/normalization.py`, `backend/app/company_intelligence/url_safety.py`
- Test: `backend/tests/test_company_intelligence_schemas.py`, `backend/tests/test_company_intelligence_url_safety.py`

- [ ] Write failing tests for whitespace/unicode normalization, structured candidate parsing, source traceability, unsafe hosts and invalid schemes.
- [ ] Run the two targeted test modules and observe the expected missing-module failures.
- [ ] Implement Pydantic request/result/candidate/source/link schemas with `extra="forbid"`, URL normalization, and DNS/IP SSRF blocking for loopback, private, link-local and unspecified targets.
- [ ] Re-run targeted tests until green.
- [ ] Commit `feat: add safe company intelligence candidate schemas`.

### Task 3: Kimi provider boundary

**Files:**
- Create: `backend/app/company_intelligence/providers.py`, `backend/app/company_intelligence/kimi.py`
- Test: `backend/tests/test_kimi_provider.py`

- [ ] Write mocked failing tests for success, missing configuration, 429 retry, timeout, invalid JSON and partial JSON candidates.
- [ ] Run `backend/.venv/Scripts/python.exe -m pytest tests/test_kimi_provider.py -v` and observe failure before provider implementation.
- [ ] Implement the provider protocol and HTTPX Kimi client with bounded timeout, one exponential retry for transient failures, explicit JSON response schema, and no request/response secret logging.
- [ ] Re-run Kimi provider tests until green.
- [ ] Commit `feat: add Kimi company search provider`.

### Task 4: Verification and bounded recruitment discovery

**Files:**
- Create: `backend/app/company_intelligence/links.py`, `backend/app/company_intelligence/verification.py`
- Test: `backend/tests/test_company_intelligence_links.py`

- [ ] Write failing tests for status mapping (200, 301, 404, 410, 403, 429, timeout), redirect-to-private-address blocking, title/name domain verification, one-hop careers discovery and official-first ranking.
- [ ] Run the link test module and observe failure.
- [ ] Implement a reusable HTTPX validator, redirect-hop validation, constrained HTML link extraction, explainable official-domain resolution, candidate verifier and deterministic link ranker.
- [ ] Re-run link tests until green.
- [ ] Commit `feat: validate and rank company recruitment links`.

### Task 5: Cache, lock, rate limit and service orchestration

**Files:**
- Create: `backend/app/company_intelligence/cache.py`, `backend/app/services/company_intelligence_service.py`
- Modify: `backend/app/repositories/company.py`
- Test: `backend/tests/test_company_intelligence_service.py`

- [ ] Write failing tests for exact local match, alias match, local match skipping Kimi, cache hit/miss, force refresh, lock coalescing, rate limiting, partial Kimi failure and candidate merge conflicts.
- [ ] Run the service test module and observe failure.
- [ ] Implement local-first repository lookup, Redis JSON cache/lock/rate limiter with safe in-memory-degradation behaviour for unavailable Redis, concurrent provider orchestration and per-stage timeout budget.
- [ ] Re-run service tests until green.
- [ ] Commit `feat: orchestrate safe company intelligence searches`.

### Task 6: Search and confirm APIs

**Files:**
- Create: `backend/app/api/company_intelligence.py`
- Modify: `backend/app/api/__init__.py`, `backend/app/services/company_service.py`, `backend/app/schemas/company.py`
- Test: `backend/tests/test_company_intelligence_api.py`

- [ ] Write failing API tests for unauthenticated access, search preview, failure fallback, confirmed new company, alias and selected-link persistence, deduplication and no automatic overwrite of conflicting fields.
- [ ] Run the API test module and observe failure.
- [ ] Add authenticated `/company-intelligence/search` and `/company-intelligence/confirm` endpoints with thin router composition and user-confirmed persistence only.
- [ ] Re-run API tests until green.
- [ ] Commit `feat: expose company intelligence preview and confirmation APIs`.

### Task 7: Application company-selection user experience

**Files:**
- Create: `frontend/src/types/companyIntelligence.ts`, `frontend/src/api/companyIntelligence.ts`, `frontend/src/components/CompanyIntelligenceField/index.tsx`
- Modify: `frontend/src/components/ApplicationForm/index.tsx`, `frontend/src/api/companies.ts`
- Test: `frontend/src/components/CompanyIntelligenceField/index.test.tsx`

- [ ] Write failing component tests for local/company-name search, loading, candidate preview, partial-state warning, editable fields, recruitment link order, confirmation and failed-search manual fallback.
- [ ] Run `npm test -- CompanyIntelligenceField` from `frontend` and observe failure.
- [ ] Implement backend-proxied candidate search and confirmation UI; retain a visible manual company-name field when intelligence is unavailable.
- [ ] Re-run component tests until green.
- [ ] Commit `feat: add editable company intelligence preview to application form`.

### Task 8: Full verification and deployment checks

**Files:**
- Modify: `README.md` only if a Phase 5 configuration note is needed

- [ ] Run Alembic current/upgrade/downgrade verification using project-local virtualenv.
- [ ] Run `python -m pytest -v`, `python -m ruff check app tests`, frontend tests and frontend production build.
- [ ] Run `docker compose config`; run Docker build/up only when the local Docker runtime is available without moving or deleting existing data.
- [ ] Inspect git diff and verify that no key, Prompt file, C-drive virtualenv, cache, or runtime data is tracked.
- [ ] Report real Kimi verification as not verified unless a configured key permits a deliberately limited call.

