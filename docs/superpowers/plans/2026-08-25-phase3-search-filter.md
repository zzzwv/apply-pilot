# Phase 3 Search, Filter, Sort, and Pagination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an authenticated user accurately search, combine filters, sort, and page through their own job applications.

**Architecture:** A validated filter DTO passes from the FastAPI router through `ApplicationService` to a composable SQLAlchemy repository query. The React list owns URL-compatible query state; its exact shape drives both API parameters and its TanStack Query key.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, PostgreSQL `pg_trgm`, React 19, TypeScript, Ant Design, TanStack Query v5, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-25-phase3-search-filter-design.md`

## Global Constraints

- Preserve Phase 1/2 architecture and current-user isolation on every query.
- Use parameterized SQLAlchemy expressions only; never interpolate request values into SQL.
- Create no dependency, virtual environment, cache, or runtime data outside `E:\qiuzhao`.
- Implement only Phase 3; do not add Dashboard, Kimi, company intelligence, sync, Redis cache, or background workers.
- Keep `pg_trgm` installed on migration downgrade because it can be shared by other database objects.

---

### Task 1: Backend filter contract and composable query

**Files:**
- Modify: `backend/app/schemas/application.py`
- Modify: `backend/app/api/applications.py`
- Modify: `backend/app/services/application_service.py`
- Modify: `backend/app/repositories/application.py`
- Test: `backend/tests/test_applications.py`

**Interfaces:**
- Produces: `ApplicationFilterParams`, `ApplicationSort`, and `ApplicationRepository.list_for_user(user_id, filters)`.
- Consumes: `JobApplication`, `Company`, `ApplicationStatus`, and `ApplicationType`.

- [ ] **Step 1: Write failing API tests**

```python
def test_combined_filters_return_only_matching_owned_application(client: TestClient) -> None:
    response = client.get(
        "/api/v1/applications?keyword=AI&status=FIRST_INTERVIEW"
        "&company_nature=STATE_OWNED&application_type=autumn_fulltime",
        headers=headers,
    )
    assert [item["id"] for item in response.json()["data"]["items"]] == [matching_id]
```

- [ ] **Step 2: Run the targeted test and confirm it fails because filters are unsupported**

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m pytest tests/test_applications.py -k combined -v`

- [ ] **Step 3: Add the DTO and query helpers**

```python
async def list_for_user(
    self, user_id: UUID, filters: ApplicationFilterParams
) -> tuple[list[JobApplication], int]:
    statement = self._apply_filters(self._base_query(user_id), filters)
    total = await self.session.scalar(select(func.count()).select_from(statement.subquery()))
    result = await self.session.execute(self._apply_pagination(self._apply_sort(statement, filters.sort), filters))
    return list(result.scalars().all()), total or 0
```

- [ ] **Step 4: Run targeted and complete backend tests**

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m pytest tests/test_applications.py -v`

### Task 2: Search-index migration

**Files:**
- Create: `backend/alembic/versions/20260825_0002_search_indexes.py`
- Test: PostgreSQL migration introspection commands

**Interfaces:**
- Produces: revision `20260825_0002` with `down_revision = "20260824_0001"`.
- Consumes: PostgreSQL `pg_trgm` and the existing `companies` / `job_applications` tables.

- [ ] **Step 1: Add a failing migration-chain check**

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m alembic -c alembic.ini heads`

Expected: only the Phase 1 revision appears before the new migration is added.

- [ ] **Step 2: Add the Phase 3 migration**

```python
op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
op.execute("CREATE INDEX ix_companies_full_name_trgm ON companies USING gin (full_name gin_trgm_ops)")
```

Create the five indexes named in the spec. In downgrade, drop those index names only.

- [ ] **Step 3: Apply and verify the migration**

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head`

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m alembic -c alembic.ini current`

### Task 3: Query-aware frontend API and UI

**Files:**
- Modify: `frontend/src/types/application.ts`
- Modify: `frontend/src/api/applications.ts`
- Modify: `frontend/src/api/applications.test.ts`
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/App.test.tsx`

**Interfaces:**
- Produces: `ApplicationListParams` and `listApplications(params)`.
- Consumes: API query keys matching `ApplicationListParams` and Ant Design controls.

- [ ] **Step 1: Write failing frontend tests**

```tsx
it("resets the page when the debounced keyword changes", async () => {
  renderApplicationsAtPageTwo();
  await user.type(screen.getByPlaceholderText("搜索公司、岗位、行业、企业性质或备注"), "AI");
  await waitFor(() => expect(listApplications).toHaveBeenLastCalledWith(expect.objectContaining({ keyword: "AI", page: 1 })));
});
```

- [ ] **Step 2: Run the focused test and confirm it fails because the control is absent**

Run: `Set-Location E:\qiuzhao\frontend; npm test -- --run src/App.test.tsx`

- [ ] **Step 3: Implement query state and controls**

```tsx
const applications = useQuery({
  queryKey: ["applications", params],
  queryFn: () => listApplications(params),
  placeholderData: keepPreviousData,
});
```

Add query-state updates for keyword, filters, date range, sort, reset, and `Table` pagination.

- [ ] **Step 4: Run frontend tests and build**

Run: `Set-Location E:\qiuzhao\frontend; npm test`

Run: `Set-Location E:\qiuzhao\frontend; npm run build`

### Task 4: Full regression and real-service verification

**Files:**
- Modify only if a failing verification exposes a Phase 3 defect.

**Interfaces:**
- Consumes: completed API, migration, and UI.
- Produces: verified Phase 3 behavior and an evidence-based final report.

- [ ] **Step 1: Run complete backend and lint verification**

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m pytest -v`

Run: `E:\qiuzhao\backend\.venv\Scripts\python.exe -m ruff check app/api/applications.py app/repositories/application.py app/schemas/application.py app/services/application_service.py tests/test_applications.py`

- [ ] **Step 2: Verify containers without deleting persistent data**

Run: `docker compose config`

Run: `docker compose up --build -d`

Run: `docker compose ps`

- [ ] **Step 3: Verify PostgreSQL extension and indexes using the running database**

```sql
SELECT extname FROM pg_extension WHERE extname = 'pg_trgm';
SELECT indexname FROM pg_indexes WHERE tablename IN ('companies', 'job_applications');
```

- [ ] **Step 4: Commit verified Phase 3 changes**

```bash
git add backend frontend docs/superpowers
git commit -m "feat: add application search filters and sorting"
```
