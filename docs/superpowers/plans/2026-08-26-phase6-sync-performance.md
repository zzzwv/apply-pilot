# Phase 6 Sync and Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver guest local application management, explicit idempotent import to cloud, user-isolated cloud cache fallback, minimal authentication UI, and the Phase 6 engineering closeout.

**Architecture:** The existing pages use a small application data-source facade selected by authenticated state. IndexedDB stores `guest` records as the guest source of truth and `cloud:<user_id>` records as cache only. The backend owns import identity through the JWT subject and a partial unique `(user_id, client_sync_id)` index.

**Tech Stack:** React 19, TypeScript, TanStack Query 5, Zustand 5, Ant Design 5, `idb`, FastAPI, Pydantic 2, SQLAlchemy async 2, Alembic, PostgreSQL 16, pytest, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-26-phase6-sync-performance-design.md`

## Global Constraints

- Keep all dependency caches, `.venv`, runtime data, Docker data, and generated benchmarks under `E:\qiuzhao`; do not install tools or dependencies to C:.
- Do not stage or commit `Prompt/`, `.env`, `.runtime/`, `.venv/`, `node_modules/`, local IndexedDB dumps, or benchmark artifacts.
- Guest namespace is `guest`; cloud namespaces are `cloud:<user_id>`; IndexedDB contains no JWT, password, API key, or secret.
- Guest data uses immutable UUID `local_id`; cloud import requests contain no `user_id`.
- Cloud API responses remain authoritative. Offline writes must clearly fail; do not add a replay queue, service worker, PWA, WebSocket, or Kimi changes.
- Every production behavior begins with a focused failing test and is verified failing before implementation.

---

### Task 1: Auth state and minimal auth UI

**Files:**
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/store/auth.ts`
- Create: `frontend/src/components/AuthControls/index.tsx`
- Create: `frontend/src/store/auth.test.ts`
- Create: `frontend/src/components/AuthControls/index.test.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces `useAuthStore` with `initialize(): Promise<void>`, `login(usernameOrEmail, password): Promise<User>`, `register(username, email, password): Promise<void>`, and `logout(queryClient): void`.
- Produces `AuthControls` which renders login/register controls for guests and current email plus logout for an authenticated user.

- [ ] **Step 1: Write the failing auth-store tests**

```ts
it("initializes the current user from an existing access token", async () => {
  localStorage.setItem("job_tracker_access_token", "token");
  mockedGetCurrentUser.mockResolvedValue({ id: "user-a", email: "a@example.com" });
  await useAuthStore.getState().initialize();
  expect(useAuthStore.getState().user).toEqual({ id: "user-a", email: "a@example.com" });
});

it("logout removes the token and user-scoped application queries", () => {
  useAuthStore.setState({ user: { id: "user-a", email: "a@example.com" }, initialized: true });
  useAuthStore.getState().logout(queryClient);
  expect(localStorage.getItem("job_tracker_access_token")).toBeNull();
  expect(queryClient.getQueryData(["applications", "cloud", "user-a"])).toBeUndefined();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- src/store/auth.test.ts`

Expected: FAIL because `auth.ts` and `useAuthStore` do not exist.

- [ ] **Step 3: Implement the smallest auth API and store**

```ts
export type User = { id: string; email: string };
export type LoginRequest = { username_or_email: string; password: string };
export type RegisterRequest = { username: string; email: string; password: string };
export async function login(payload: LoginRequest): Promise<{ access_token: string; token_type: string }> {
  return unwrap(apiClient.post("/auth/login", payload));
}
export async function register(payload: LoginRequest): Promise<User> {
  return unwrap(apiClient.post("/auth/register", payload));
}
export async function getCurrentUser(): Promise<User> {
  return unwrap(apiClient.get("/auth/me"));
}
```

```ts
logout(queryClient) {
  const userId = get().user?.id;
  localStorage.removeItem("job_tracker_access_token");
  queryClient.removeQueries({ predicate: query => query.queryKey.includes(userId ?? "") });
  set({ user: undefined, initialized: true });
}
```

- [ ] **Step 4: Add the failing auth-controls test and verify it fails**

```tsx
it("shows login and registration for a guest, then identity and logout for a user", async () => {
  render(<AuthControls queryClient={queryClient} />);
  expect(screen.getByRole("button", { name: "登录" })).toBeDefined();
  useAuthStore.setState({ user: { id: "user-a", email: "a@example.com" }, initialized: true });
  expect(await screen.findByText("a@example.com")).toBeDefined();
});
```

Run: `npm test -- src/components/AuthControls/index.test.tsx`

Expected: FAIL because `AuthControls` does not exist.

- [ ] **Step 5: Implement the minimal header control and bootstrap initialization**

```tsx
<AuthControls queryClient={queryClient} />
```

Use an Ant Design modal with only email/password fields for login and registration. In `main.tsx`, call `initialize()` once before pages issue cloud queries; guests remain initialized with no user.

- [ ] **Step 6: Verify GREEN and commit**

Run: `npm test -- src/store/auth.test.ts src/components/AuthControls/index.test.tsx`

Run: `git add frontend/src/api/auth.ts frontend/src/store/auth.ts frontend/src/components/AuthControls/index.tsx frontend/src/store/auth.test.ts frontend/src/components/AuthControls/index.test.tsx frontend/src/main.tsx frontend/src/App.tsx && git commit -m "feat: add minimal authentication UI"`

Expected: PASS; commit excludes `Prompt/`.

### Task 2: Versioned IndexedDB and guest repository

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/local-db/database.ts`
- Create: `frontend/src/local-db/applicationRepository.ts`
- Create: `frontend/src/local-db/applicationRepository.test.ts`
- Modify: `frontend/src/types/application.ts`

**Interfaces:**
- Produces `LocalApplication`, `LocalStatusLog`, `LocalCompany`, and `LocalApplicationRepository` methods `create`, `get`, `list`, `update`, `remove`, `changeStatus`, `listStatusLogs`, `count`, `writeCloudSnapshot`, and `readCloudSnapshot`.
- `LocalApplication.local_id` is the permanent guest/import ID and `namespace` is always explicit.

- [ ] **Step 1: Add focused failing repository tests**

```ts
it("persists a guest application and its initial status log across repository instances", async () => {
  const first = new LocalApplicationRepository("guest");
  const created = await first.create(guestInput);
  const second = new LocalApplicationRepository("guest");
  expect((await second.list({})).items).toHaveLength(1);
  expect(await second.listStatusLogs(created.local_id)).toMatchObject([{ from_status: null, to_status: "APPLIED" }]);
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- src/local-db/applicationRepository.test.ts`

Expected: FAIL because the local DB module does not exist.

- [ ] **Step 3: Add lightweight dependencies and the versioned schema**

Run: `npm install idb fake-indexeddb --save`

Use `idb` with `DB_VERSION = 1` and object stores `applications`, `status_logs`, and `sync_metadata`. Configure Vitest setup to load `fake-indexeddb/auto`; use no third-party state framework.

```ts
export const DB_VERSION = 1;
export type LocalApplication = Omit<Application, "id" | "user_id" | "company_id"> & {
  local_id: string; namespace: string; cloud_id?: string; company: LocalCompany;
};
```

- [ ] **Step 4: Implement only create/read persistence and verify GREEN**

```ts
await db.put("applications", application);
await db.put("status_logs", { id: crypto.randomUUID(), application_local_id: application.local_id,
  namespace, from_status: null, to_status: application.current_status, changed_at: application.created_at, remark: null });
```

Run: `npm test -- src/local-db/applicationRepository.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add frontend/package.json frontend/package-lock.json frontend/src/local-db frontend/src/types/application.ts && git commit -m "feat: add versioned local application storage"`

### Task 3: Guest CRUD, timeline, search, filters, and dashboard metrics

**Files:**
- Create: `frontend/src/data/applicationDataSource.ts`
- Create: `frontend/src/data/localApplicationDataSource.ts`
- Create: `frontend/src/data/cloudApplicationDataSource.ts`
- Create: `frontend/src/dashboard/metrics.ts`
- Create: `frontend/src/dashboard/metrics.test.ts`
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`
- Modify: `frontend/src/pages/Dashboard/index.tsx`
- Modify: `frontend/src/components/ApplicationForm/index.tsx`
- Modify: `frontend/src/components/CompanyIntelligenceField/index.tsx`

**Interfaces:**
- Produces `ApplicationDataSource` with list/detail/create/update/delete/changeStatus/statusLogs/dashboard methods matching existing domain types.
- Produces `calculateDashboard(applications, filters)` returning `DashboardSummary` and chart distributions with backend status definitions.

- [ ] **Step 1: Write the failing local behavior tests**

```ts
it("filters a guest list by company, job title, industry, nature, and note", async () => {
  await local.create({ ...guestInput, job_title: "Backend", note: "referral", company: { full_name: "AI Corp", industry: "AI", nature: "PRIVATE" } });
  expect((await local.list({ keyword: "referral" })).total).toBe(1);
});

it("records each guest status change in the timeline", async () => {
  const item = await local.create(guestInput);
  await local.changeStatus(item.local_id, "FIRST_INTERVIEW", "passed resume");
  expect(await local.listStatusLogs(item.local_id)).toMatchObject([
    { from_status: null, to_status: "APPLIED" }, { from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed resume" },
  ]);
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- src/local-db/applicationRepository.test.ts src/dashboard/metrics.test.ts`

Expected: FAIL because filtering/status mutation/metrics are incomplete.

- [ ] **Step 3: Implement repository filtering and metrics, then verify GREEN**

```ts
const normalized = value.toLocaleLowerCase();
const matchesKeyword = [item.company.full_name, item.company.short_name, item.job_title, item.company.industry, item.company.nature, item.note]
  .filter(Boolean).some(value => String(value).toLocaleLowerCase().includes(normalized));
```

Keep status category sets identical to `backend/app/repositories/analytics.py`. Guest company entry uses a manual local company object; it hides Kimi lookup and displays “登录后可使用企业信息智能获取”.

Run: `npm test -- src/local-db/applicationRepository.test.ts src/dashboard/metrics.test.ts`

Expected: PASS.

- [ ] **Step 4: Add shared-UI integration tests and verify RED/GREEN**

```tsx
it("uses the guest source without sending an Application API request", async () => {
  renderGuestApplicationsPage();
  await userEvent.click(screen.getByRole("button", { name: "新增投递" }));
  await submitGuestApplication();
  expect(mockedCreateApplication).not.toHaveBeenCalled();
  expect(await screen.findByText("本地投递记录")).toBeDefined();
});
```

Run: `npm test -- src/pages/Applications/index.test.tsx src/pages/ApplicationDetail/index.test.tsx src/pages/Dashboard/index.test.tsx`

Expected: tests first fail, then pass after pages select the data source only after auth initialization.

- [ ] **Step 5: Commit**

Run: `git add frontend/src/data frontend/src/dashboard frontend/src/pages frontend/src/components/ApplicationForm frontend/src/components/CompanyIntelligenceField && git commit -m "feat: add guest application workflow"`

### Task 4: Idempotent backend import schema and migration

**Files:**
- Modify: `backend/app/models/application.py`
- Modify: `backend/app/schemas/application.py`
- Create: `backend/alembic/versions/20260826_0004_phase6_sync_import.py`
- Create: `backend/tests/test_sync_models.py`

**Interfaces:**
- Adds nullable `JobApplication.client_sync_id: UUID | None`.
- Produces `SyncImportApplication`, `SyncImportStatusLog`, `SyncImportRequest`, and batch response schemas with no `user_id` input.

- [ ] **Step 1: Write migration/model tests**

```py
def test_client_sync_id_is_nullable_and_unique_per_user(session):
    first = JobApplication(user_id=user_a.id, client_sync_id=sync_id, **fields)
    second_user = JobApplication(user_id=user_b.id, client_sync_id=sync_id, **fields)
    session.add_all([first, second_user])
    await session.commit()
    with pytest.raises(IntegrityError):
        session.add(JobApplication(user_id=user_a.id, client_sync_id=sync_id, **fields))
        await session.commit()
```

- [ ] **Step 2: Verify RED**

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_sync_models.py -q`

Expected: FAIL because `client_sync_id` and import schemas do not exist.

- [ ] **Step 3: Generate and implement the migration from the actual head**

Run: `backend/.venv/Scripts/alembic heads`

Create a revision whose `down_revision` equals the reported head. Add `client_sync_id` nullable and a PostgreSQL partial unique index:

```py
op.create_index("uq_job_applications_user_client_sync_id", "job_applications", ["user_id", "client_sync_id"], unique=True,
    postgresql_where=sa.text("client_sync_id IS NOT NULL"))
```

Set `SyncImportRequest.applications = Field(min_length=1, max_length=200)` and forbid extra fields throughout.

- [ ] **Step 4: Verify GREEN and commit**

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_sync_models.py -q`

Run: `git add backend/app/models/application.py backend/app/schemas/application.py backend/alembic/versions backend/tests/test_sync_models.py && git commit -m "feat: add idempotent import identity"`

### Task 5: Transactional, secure import API

**Files:**
- Create: `backend/app/services/sync_service.py`
- Create: `backend/app/api/sync.py`
- Modify: `backend/app/api/__init__.py`
- Create: `backend/tests/test_sync_import.py`

**Interfaces:**
- Produces `POST /api/v1/sync/import-applications`, JWT protected.
- Response has `{ imported, reused, failed, mappings, errors }`, where each mapping has `client_sync_id` and `cloud_application_id`.

- [ ] **Step 1: Write failing endpoint tests**

```py
def test_import_is_idempotent_and_returns_mapping(client):
    headers = _register_and_headers(client)
    payload = {"applications": [import_item(client_sync_id=str(uuid4()))]}
    first = client.post("/api/v1/sync/import-applications", headers=headers, json=payload)
    second = client.post("/api/v1/sync/import-applications", headers=headers, json=payload)
    assert first.json()["data"]["imported"] == 1
    assert second.json()["data"]["reused"] == 1
    assert owned_application_count(client, headers) == 1

def test_import_ignores_a_client_supplied_user_id(client):
    response = client.post("/api/v1/sync/import-applications", headers=_register_and_headers(client), json={"applications": [{**import_item(), "user_id": str(uuid4())}]})
    assert response.status_code == 422
```

- [ ] **Step 2: Verify RED**

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_sync_import.py -q`

Expected: FAIL with 404 or missing import service.

- [ ] **Step 3: Implement per-item transactions and company resolution**

```py
async with self.session.begin_nested():
    existing = await self.applications.get_by_client_sync_id(current_user.id, item.client_sync_id)
    if existing is not None:
        return ImportItemResult.reused(item.client_sync_id, existing.id)
    company = await self.companies.find_by_name_or_alias(item.company.full_name)
    if company is None:
        company = Company(full_name=item.company.full_name, short_name=item.company.short_name,
                          industry=item.company.industry, nature=item.company.nature, size=item.company.size)
        self.session.add(company)
        await self.session.flush()
    application = JobApplication(user_id=current_user.id, company_id=company.id, client_sync_id=item.client_sync_id, **item.application_fields())
    self.session.add(application)
    for log in item.status_logs:
        self.session.add(ApplicationStatusLog(application_id=application.id, user_id=current_user.id, **log.model_dump()))
```

Do not call Kimi, do not call ordinary create, and do not mutate a reused company. Convert individual validation/persistence errors to safe item errors while allowing the batch to continue.

- [ ] **Step 4: Add complete regression coverage and verify GREEN**

```py
def test_import_preserves_status_history_without_duplicate_initial_log(client):
    headers = _register_and_headers(client)
    response = client.post("/api/v1/sync/import-applications", headers=headers, json={"applications": [import_item(status_logs=[initial_log("APPLIED"), transition_log("APPLIED", "FIRST_INTERVIEW")])]})
    application_id = response.json()["data"]["mappings"][0]["cloud_application_id"]
    logs = client.get(f"/api/v1/applications/{application_id}/status-logs", headers=headers)
    assert [log["to_status"] for log in logs.json()["data"]["items"]] == ["APPLIED", "FIRST_INTERVIEW"]

def test_import_reuses_company_without_overwriting_it(client):
    headers = _register_and_headers(client)
    company_id = _create_company(client, headers, full_name="Existing Import Company", industry="Original")
    response = client.post("/api/v1/sync/import-applications", headers=headers, json={"applications": [import_item(company={"full_name": "Existing Import Company", "industry": "Changed"})]})
    assert response.status_code == 200
    assert client.get(f"/api/v1/applications/{response.json()['data']['mappings'][0]['cloud_application_id']}", headers=headers).json()["data"]["company_id"] == company_id

def test_partial_batch_failure_keeps_valid_item(client):
    headers = _register_and_headers(client)
    response = client.post("/api/v1/sync/import-applications", headers=headers, json={"applications": [import_item(), {"client_sync_id": str(uuid4()), "job_title": "", "company": {"full_name": "Bad"}}]})
    assert response.json()["data"]["imported"] == 1
    assert response.json()["data"]["failed"] == 1

def test_same_client_sync_id_is_allowed_for_another_user(client):
    client_sync_id = str(uuid4())
    first = client.post("/api/v1/sync/import-applications", headers=_register_and_headers(client), json={"applications": [import_item(client_sync_id=client_sync_id)]})
    second = client.post("/api/v1/sync/import-applications", headers=_register_and_headers(client), json={"applications": [import_item(client_sync_id=client_sync_id)]})
    assert first.json()["data"]["imported"] == second.json()["data"]["imported"] == 1

def test_import_user_cannot_read_another_users_mapping(client):
    owner_headers = _register_and_headers(client)
    other_headers = _register_and_headers(client)
    response = client.post("/api/v1/sync/import-applications", headers=owner_headers, json={"applications": [import_item()]})
    application_id = response.json()["data"]["mappings"][0]["cloud_application_id"]
    assert client.get(f"/api/v1/applications/{application_id}", headers=other_headers).status_code == 404
```

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_sync_import.py tests/test_applications.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add backend/app/services/sync_service.py backend/app/api/sync.py backend/app/api/__init__.py backend/tests/test_sync_import.py && git commit -m "feat: add idempotent guest data import"`

### Task 6: Login import transition and user-isolated cache

**Files:**
- Create: `frontend/src/api/sync.ts`
- Create: `frontend/src/components/GuestImportDialog/index.tsx`
- Create: `frontend/src/components/GuestImportDialog/index.test.tsx`
- Modify: `frontend/src/store/auth.ts`
- Modify: `frontend/src/data/cloudApplicationDataSource.ts`
- Modify: `frontend/src/local-db/applicationRepository.ts`

**Interfaces:**
- Produces `importApplications({ applications }): Promise<SyncImportResult>`.
- On post-login guest count, shows one explicit dialog with “同步到账号” and “暂不同步”.

- [ ] **Step 1: Write failing import-dialog tests**

```tsx
it("detects guest data after login and preserves it when dismissed", async () => {
  mockGuestCount.mockResolvedValue(3);
  renderLoggedIn();
  expect(await screen.findByText("检测到 3 条本地投递记录")).toBeDefined();
  await userEvent.click(screen.getByRole("button", { name: "暂不同步" }));
  expect(await guestRepository.count()).toBe(3);
});

it("writes mappings only after an import succeeds and cloud snapshot refreshes", async () => {
  mockedImportApplications.mockResolvedValue({ imported: 1, reused: 0, failed: 0, mappings: [{ client_sync_id: guest.local_id, cloud_application_id: "cloud-a" }], errors: [] });
  mockedCloudList.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 });
  await importGuestRecords();
  expect(await guestRepository.getMapping(guest.local_id)).toBe("cloud-a");
  expect(mockedCloudList).toHaveBeenCalled();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- src/components/GuestImportDialog/index.test.tsx`

Expected: FAIL because sync client/dialog are absent.

- [ ] **Step 3: Implement explicit import and safe cleanup order**

```ts
const result = await importApplications({ applications: await guestRepository.exportForImport() });
await guestRepository.storeMappings(result.mappings);
await cloudDataSource.list({ page: 1, page_size: 20 });
await guestRepository.markGuestImported();
```

Do not delete guest records until the refetched cloud snapshot succeeds. Surface full success, partial failure, and full failure with safe Chinese messages; failure always preserves guest data.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- src/components/GuestImportDialog/index.test.tsx src/store/auth.test.ts`

Run: `git add frontend/src/api/sync.ts frontend/src/components/GuestImportDialog frontend/src/store/auth.ts frontend/src/data/cloudApplicationDataSource.ts frontend/src/local-db/applicationRepository.ts && git commit -m "feat: add guest import transition"`

### Task 7: Cloud snapshot cache and offline read fallback

**Files:**
- Create: `frontend/src/data/cloudApplicationDataSource.test.ts`
- Modify: `frontend/src/data/cloudApplicationDataSource.ts`
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`

**Interfaces:**
- Cloud reads return `{ data, source: "cloud" | "cache", stale: boolean }`.
- Cloud mutations update the active namespace only after successful HTTP responses.

- [ ] **Step 1: Write failing cache tests**

```ts
it("writes the active user snapshot after a successful cloud list", async () => {
  mockedListApplications.mockResolvedValue(cloudList);
  await source.list({});
  expect(await cache.readCloudSnapshot("user-a", "list")).toEqual(cloudList);
});

it("returns a stale cache when the cloud list fails", async () => {
  mockedListApplications.mockRejectedValue(new Error("offline"));
  await cache.writeCloudSnapshot("user-a", "list", cloudList);
  await expect(source.list({})).resolves.toMatchObject({ data: cloudList, source: "cache", stale: true });
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts`

Expected: FAIL because cache behavior is not implemented.

- [ ] **Step 3: Implement cache updates, invalidations, and read-only fallback**

```ts
try { const data = await listApplications(params); await cache.writeCloudSnapshot(userId, listKey(params), data); return { data, source: "cloud", stale: false }; }
catch (error) { const cached = await cache.readCloudSnapshot<ApplicationList>(userId, listKey(params)); if (cached) return { data: cached, source: "cache", stale: true }; throw error; }
```

The pages display “当前显示最近同步的数据，网络恢复后可刷新” for `stale`. Mutations retain their existing API path and show “当前网络不可用，请恢复网络后再修改” on failure.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts src/pages/Applications/index.test.tsx src/pages/ApplicationDetail/index.test.tsx`

Run: `git add frontend/src/data/cloudApplicationDataSource.ts frontend/src/data/cloudApplicationDataSource.test.ts frontend/src/pages/Applications/index.tsx frontend/src/pages/ApplicationDetail/index.tsx && git commit -m "feat: add cloud application cache fallback"`

### Task 8: Query behavior and focused frontend bundle improvement

**Files:**
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/vite.config.ts`
- Modify: exactly one measured render hotspot selected after React Profiler evidence, if such evidence exists
- Create: `docs/phase6-frontend-performance.md`

**Interfaces:**
- Query defaults use a finite `staleTime`, keep window-focus refetch enabled for cloud data, and use stable serializable query keys.
- Route-level chunks retain a clear separation between app shell, dashboard, detail, and auth-dependent UI.

- [ ] **Step 1: Capture baseline and write failing query-key tests**

```ts
it("uses equal query keys for equal list parameter values", () => {
  expect(applicationListKey({ page: 1, status: ["APPLIED"] })).toEqual(applicationListKey({ status: ["APPLIED"], page: 1 }));
});
```

Run: `npm run build`

Record raw/gzip chunks in `docs/phase6-frontend-performance.md`; baseline is max 1,301.17 kB raw / 412.87 kB gzip. Run the test and confirm it fails before introducing the key helper.

- [ ] **Step 2: Implement stable keys and only evidenced code splitting**

```ts
export const applicationListKey = (params: ApplicationListParams) => ["applications", sourceKey, stableParams(params)] as const;
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: true } } });
```

Lazy-load only routes that are not needed for the current route; keep ECharts core registration unchanged unless the measured build identifies additional unnecessary imports.

- [ ] **Step 3: Verify and commit**

Run: `npm test -- src/data/applicationDataSource.test.ts src/data/cloudApplicationDataSource.test.ts && npm run build`

Update the before/after table with actual output or `N/A / not reliably measurable`. Run: `git add frontend/src/main.tsx frontend/src/App.tsx frontend/vite.config.ts frontend/src/data docs/phase6-frontend-performance.md && git commit -m "perf: stabilize frontend data loading"`

### Task 9: Backend query audit and benchmark

**Files:**
- Create: `backend/scripts/benchmark_phase6.py`
- Create: `backend/tests/test_phase6_query_counts.py`
- Create: `docs/phase6-backend-performance.md`
- Modify only query files proven slow by measurements.

**Interfaces:**
- Benchmark creates a unique, clearly named dedicated user, runs warm measurements, then deletes only that user's generated data.
- Report has endpoint, dataset size, run count, median, p95/max, target, environment, and result.

- [ ] **Step 1: Write failing query-count tests**

```py
async def test_list_loads_companies_without_per_row_queries(session, user, query_counter):
    await seed_applications(session, user, count=20)
    await ApplicationService(session).list_applications(user, ApplicationFilterParams())
    assert query_counter.count <= 2
```

- [ ] **Step 2: Verify RED or establish existing behavior**

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_phase6_query_counts.py -q`

Expected: If this fails, capture the SQL statement count and identify the exact relationship/query causing it. Do not optimize before that evidence.

- [ ] **Step 3: Add deterministic 1,000-record benchmark**

```py
for endpoint in ("list", "search", "multi_filter", "summary", "status_distribution", "industry_distribution", "nature_distribution", "trend"):
    durations = [await measure(endpoint) for _ in range(10)]
    report(endpoint, dataset_size=1000, median=median(durations), p95=quantiles(durations, n=20)[18])
```

Use a unique test account and `try/finally` cleanup. Before any SQL change that misses 0.8 seconds, capture `EXPLAIN ANALYZE` in the report.

- [ ] **Step 4: Verify and commit**

Run: `backend/.venv/Scripts/python.exe -m pytest tests/test_phase6_query_counts.py -q`

Run: `backend/.venv/Scripts/python.exe backend/scripts/benchmark_phase6.py`

Run: `git add backend/scripts/benchmark_phase6.py backend/tests/test_phase6_query_counts.py docs/phase6-backend-performance.md backend/app/repositories/application.py backend/app/repositories/analytics.py && git commit -m "perf: benchmark application queries"`

### Task 10: Documentation and final acceptance

**Files:**
- Modify: `README.md`
- Modify: `docs/秋招_实习投递状态管理Web网站产品需求文档（PRD V1.0定稿）.md`
- Modify: `docs/秋招-实习投递状态管理 Web 网站技术设计文档 V1.0.md`
- Create: `docs/phase6-implementation-notes.md`
- Create: `docs/phase6-final-acceptance.md`

**Interfaces:**
- Documents describe guest storage, explicit import, idempotency, cloud authority, cache fallback, user isolation, performance results, and V1 limitations.

- [ ] **Step 1: Add the required V1 limitations and acceptance scenarios**

```md
1. Guest records stay in the current browser until explicitly imported.
2. Authenticated data is authoritative in PostgreSQL; IndexedDB is a cache only.
3. Cached reads may be displayed as stale during network failures.
4. V1 has no offline mutation replay, PWA, WebSocket sync, or real-time collaboration.
```

- [ ] **Step 2: Run the complete automated verification**

Run: `backend/.venv/Scripts/python.exe -m pytest -q`

Run: `backend/.venv/Scripts/python.exe -m ruff check app tests`

Run: `npm test && npm run build`

Run: `git diff --check`

Run: `backend/.venv/Scripts/alembic current && backend/.venv/Scripts/alembic heads`

Run: `docker compose ps && docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').status)" && docker compose exec -T redis redis-cli ping`

- [ ] **Step 3: Run documented manual acceptance**

Execute and record: guest CRUD/reload/timeline/search/filter/dashboard; guest-to-login import; retry import; User A logout/User B isolation; two authenticated contexts with refetch; cached list failure fallback. Do not claim a first-content metric unless independently measured.

- [ ] **Step 4: Commit and final report**

Run: `git add README.md docs/秋招_实习投递状态管理Web网站产品需求文档（PRD V1.0定稿）.md docs/秋招-实习投递状态管理\ Web\ 网站技术设计文档\ V1.0.md docs/phase6-implementation-notes.md docs/phase6-final-acceptance.md && git commit -m "docs: complete Phase 6 acceptance"`

Report Phase 6 as passed only if all core sync scenarios and recorded verification evidence pass; otherwise report it as incomplete with exact remaining blockers.
