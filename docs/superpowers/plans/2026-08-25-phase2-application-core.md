# Phase 2 Application Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the authenticated job-application CRUD, status history, basic pagination, and minimal React workflow required for Phase 2.

**Architecture:** Keep the current FastAPI layering: router parses authenticated requests, `ApplicationService` owns permission and transaction semantics, and `ApplicationRepository` owns owner-scoped SQLAlchemy access. React uses TanStack Query for application data and Zustand only for drawer UI state.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, Pydantic, pytest, React 19, TypeScript, Vite, Ant Design, TanStack Query, Axios.

**Spec:** `Prompt/Phase 2.md`; `docs/秋招_实习投递状态管理Web网站产品需求文档（PRD V1.0定稿）.md`; `docs/秋招-实习投递状态管理 Web 网站技术设计文档 V1.0.md`

## Global Constraints

- Preserve the committed Phase 1 infrastructure and its public response envelope.
- Do not add third-party dependencies, external integrations, dashboards, search, caching, or AI features.
- Keep virtual environments, caches, and all downloaded artifacts under `E:\qiuzhao`; never install into a system directory.
- Query every private application or status log with the authenticated `user_id`; missing or foreign records return `APPLICATION_NOT_FOUND` / HTTP 404.
- Store the existing English `ApplicationStatus` enum values, allow user-driven backward status changes, and never emit a duplicate log for an unchanged status.

---

### Task 1: Branch, baseline, and application test contract

**Files:**
- Create: `backend/tests/test_applications.py`
- Modify: `backend/tests/conftest.py`
- Modify: `backend/requirements-dev.txt`

**Interfaces:**
- Consumes: `create_app`, `get_session`, existing JWT authentication APIs.
- Produces: reusable API client/SQLite fixtures and endpoint-level expected response contracts.

- [ ] **Step 1: Write failing API tests** for company creation, application creation/list/detail/update/delete/batch delete, pagination, owner isolation, initial log creation, status changes, duplicate status suppression, invalid status validation, log order, and transaction rollback.
- [ ] **Step 2: Run `backend\.venv\Scripts\python.exe -m pytest tests/test_applications.py -v`** and confirm collection/execution fails because the Phase 2 router and schemas do not exist.
- [ ] **Step 3: Add only test dependencies required by the existing project (`aiosqlite` for an async local test database) and test fixtures** that override the app session dependency with a fresh transaction-safe SQLite database.
- [ ] **Step 4: Re-run the focused tests**; they should still fail only for missing Phase 2 behavior.

### Task 2: Backend application core

**Files:**
- Create: `backend/app/schemas/application.py`
- Create: `backend/app/schemas/company.py`
- Create: `backend/app/repositories/application.py`
- Create: `backend/app/repositories/company.py`
- Create: `backend/app/services/application_service.py`
- Create: `backend/app/services/company_service.py`
- Create: `backend/app/api/applications.py`
- Create: `backend/app/api/companies.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/repositories/__init__.py`
- Modify: `backend/app/services/__init__.py`
- Modify: `backend/app/core/errors.py`

**Interfaces:**
- Consumes: `get_current_user`, `success_response`, `JobApplication`, `ApplicationStatusLog`, `Company`.
- Produces: `POST/GET/PUT/DELETE /api/v1/applications`, `POST /api/v1/applications/batch-delete`, `PATCH /api/v1/applications/{id}/status`, `GET /api/v1/applications/{id}/status-logs`, and minimal `POST /api/v1/companies`.

- [ ] **Step 1: Implement schemas from the failing tests.** `ApplicationCreate` accepts business fields but never `user_id`; `ApplicationUpdate` omits `current_status`; `ApplicationStatusUpdate` has `status` and optional `remark`; page defaults are 1/20 and page size caps at 100.
- [ ] **Step 2: Implement repositories using `WHERE id = :id AND user_id = :current_user_id`** for every single-record retrieval; list queries sort `application_date DESC` and return total plus page slice.
- [ ] **Step 3: Implement services with explicit `session.begin()` transactions.** Creation inserts the application plus `from_status=None` initial log. Status change updates the application and inserts one log in the same transaction; equal states return unchanged without inserting a log.
- [ ] **Step 4: Implement thin routers** using `Depends(get_current_user)` and the existing uniform response envelope. Return a 404 application error for absent and non-owned resources.
- [ ] **Step 5: Run the focused backend tests** and repair only behavior exposed by their failures until green.

### Task 3: Phase 2 test and migration verification

**Files:**
- Modify: `backend/tests/test_applications.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: completed real API endpoints and async SQLite fixture.
- Produces: regression coverage for CRUD, ownership, logs, pagination, and transaction atomicity.

- [ ] **Step 1: Add a database constraint failure test** that forces status-log insertion to fail and asserts both status and logs stay unchanged after rollback.
- [ ] **Step 2: Run the full backend test suite** with the project-local interpreter.
- [ ] **Step 3: Check `alembic current` and `alembic upgrade head` against the configured PostgreSQL service.** No migration is added because the Phase 1 schema already has all required columns, nullable `from_status`, indexes, and cascades.

### Task 4: Minimal application UI

**Files:**
- Create: `frontend/src/types/application.ts`
- Create: `frontend/src/api/applications.ts`
- Create: `frontend/src/api/companies.ts`
- Create: `frontend/src/pages/Applications/index.tsx`
- Create: `frontend/src/pages/ApplicationDetail/index.tsx`
- Create: `frontend/src/components/ApplicationForm/index.tsx`
- Create: `frontend/src/components/StatusTag/index.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/api/client.ts`

**Interfaces:**
- Consumes: Phase 2 HTTP envelope and endpoints.
- Produces: authenticated request helper, paginated application list, create/edit form, detail/status timeline, and cache invalidation for mutations.

- [ ] **Step 1: Write a failing React test for the applications route’s empty/list rendering.**
- [ ] **Step 2: Implement type-safe API unwrapping and bearer-token injection.**
- [ ] **Step 3: Implement the minimal table, drawer form, detail view, status change control, and chronological timeline.** Use TanStack Query keys `applications`, `application:{id}`, and `application-status-logs:{id}`; invalidate relevant keys after mutations.
- [ ] **Step 4: Run `npm test` and `npm run build` from `frontend`; resolve TypeScript or behavioral failures without adding dependencies.**

### Task 5: Full Phase 2 verification

**Files:**
- Modify only if a verification failure proves an implementation defect.

- [ ] **Step 1: Run backend pytest, Alembic current/upgrade, frontend tests/build, and `docker compose config`.**
- [ ] **Step 2: Start Compose using existing project-local runtime mounts; run the real User A/User B HTTP CRUD/status/log/delete flow against PostgreSQL.**
- [ ] **Step 3: Verify database rows and cascading status-log deletion, then stop no services unless they were started solely for this verification.**
- [ ] **Step 4: Record factual passed, failed, and unavailable checks in the Phase 2 final report.**
