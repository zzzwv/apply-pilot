# Phase 6 Local / Cloud Sync and Engineering Closure Design

## Scope and ownership

Phase 6 adds the V1 local/cloud data lifecycle without turning the product into an offline-first or real-time collaboration system.

- A guest user's IndexedDB data is the source of truth. Guest users can create, edit, delete, search, filter, sort, inspect status history, change status, and view dashboard metrics without backend access.
- For an authenticated user, PostgreSQL is the source of truth. IndexedDB holds only a namespaced snapshot cache of successful cloud reads and mutations.
- If an authenticated read fails, the list and detail views may show the last cloud snapshot with a visible stale/offline notice. Authenticated writes fail visibly while offline; no mutation queue or replay is implemented.
- IndexedDB never holds passwords, JWTs, API keys, or other secrets.

The Phase 6 authentication surface is deliberately small: register, log in, log out, fetch current user state, import detection after login, and user-scoped state cleanup at logout. Account settings, password recovery, email verification, OAuth, profiles, and MFA are out of scope.

## Frontend architecture

The existing Application list, form, detail, timeline, and dashboard pages remain shared UI. A small `ApplicationDataSource` interface selects the implementation from the current authentication state:

- `LocalApplicationRepository` persists guest applications and status logs in IndexedDB.
- `CloudApplicationRepository` wraps the existing HTTP API, updates the active user's IndexedDB snapshot after successful reads or writes, and never writes cloud data directly through IndexedDB.

The client adds a lightweight `idb` dependency and a versioned local database. Its records are partitioned by `namespace`, using `guest` and `cloud:<user_id>`. Guest applications have an immutable UUID `local_id`; cloud snapshots retain cloud IDs and are never available through another user's namespace. The guest data model reuses existing application field names and adds embedded local Company display fields where cloud `company_id` is unavailable.

An auth store owns only the access token, current user, initialization state, and login/logout transitions. It clears user-scoped TanStack Query entries and Zustand state before presenting another user's data. The shared header exposes register/login for guests, current-user identity and logout for authenticated users. The existing pages choose their repository after auth initialization, so they never make protected cloud requests on behalf of a guest.

Guest Company Intelligence is disabled. The shared company field provides manual company entry in guest mode and clearly states that intelligent company lookup is available after login.

## Guest data and dashboard semantics

Each guest create operation generates a stable `local_id`, stores the application, and creates an initial status log. Each guest status change writes an ordered `(old_status, new_status, timestamp, remark)` log and updates the current status atomically.

Guest list operations apply the existing Phase 3 filters, normalized substring keyword search, ordering, and pagination in the local repository. Guest dashboard metrics are calculated from the same status classifications and filter semantics used by the backend analytics repository. The frontend implementation uses shared, tested metric definitions rather than an unrelated second formula.

## Cloud import

The backend receives guest data through a dedicated JWT-protected batch endpoint, `POST /api/v1/sync/import-applications`. A request contains at most 200 applications; the current JWT subject, never client input, supplies `user_id`.

The schema validates all imported application fields, dates, enums, maximum text lengths, company values, and status history. Every application carries `client_sync_id`, the guest `local_id`. A nullable `client_sync_id` column is added to `job_applications`, with a PostgreSQL partial unique index on `(user_id, client_sync_id)` for non-null IDs. This permits legacy applications and permits the same local ID under different users while making retry idempotent per user.

An import service processes each item atomically. It first resolves an exact existing Company through existing normalized name/alias resolution; otherwise it creates the minimum valid Company from guest-provided manual fields. It neither invokes Kimi nor overwrites an existing company's trusted fields. It then creates the application and its supplied status history in one transaction, without calling the ordinary create service that would duplicate the initial status log. A previously imported `(user_id, client_sync_id)` record is returned as reused. One invalid item does not roll back valid items in the batch.

The response provides imported, reused, and failed counts plus exact `client_sync_id -> cloud_application_id` mappings. The client records mappings and sync metadata, refetches the cloud snapshot, and only then marks or removes the guest namespace. Failed and dismissed guest records remain available for later import. A login session uses dismissal metadata to avoid repeated modal prompts.

## Cache, mutation, and isolation rules

Successful cloud list and detail reads update the active cloud namespace. Successful create, update, status change, and delete operations invalidate the relevant application and dashboard query keys and update/remove cache entries. Cached data never overwrites a successful HTTP response.

On logout, the client removes the token, resets current user state and user-scoped UI state, cancels/removes application and dashboard queries, and routes only after cleanup. Cloud namespaces remain stored but are inaccessible without a matching authenticated user ID. Logging in as User B cannot render User A's cache during initialization.

## Performance and engineering closure

The initial production build baseline is two anonymous JS chunks, with the largest at 1,301.17 kB raw / 412.87 kB gzip. Dashboard is already route-lazy and ECharts is already registered from `echarts/core`; Phase 6 will therefore measure first and only make focused splitting or rendering changes supported by evidence.

A separate benchmark script/test user will generate 1,000 mixed applications. It will record environment, dataset size, warm runs, median and p95 (or min/average/max if necessary) for list, search, multi-filter, dashboard summary, distributions, and trend. Database query changes require `EXPLAIN ANALYZE` evidence first. The target remains 0.8 seconds per normal API/chart endpoint; first-load metrics are reported only when independently measurable.

The closeout includes backend tests and Ruff, frontend tests and production build, migration checks, Docker health, Redis ping, secret audit, documentation updates, and an explicit V1 limitations section. It excludes Kimi behavior changes unless a Phase 6 regression proves one is required.

## Test strategy

Every task follows RED -> GREEN -> targeted regression. Frontend tests use `fake-indexeddb` only if required to exercise the real local repository. Backend tests cover import ownership, validation, partial success, company behavior, status-history preservation, and idempotency. Frontend tests cover local CRUD/reload persistence, filtering, dashboard metrics, import UX, cache fallback, and logout/user isolation. Performance checks remain a dedicated benchmark, not a latency assertion in ordinary CI tests.

## Final acceptance evidence

The closure reruns full backend and frontend regressions, production build, Docker health, Redis PING, Alembic current/head/history, live PostgreSQL index inspection, and tracked-file secret hygiene. Security regression additionally verifies IDOR protection for application/detail/status-log read and mutation, strict import validation, per-user `client_sync_id` idempotency, and visibility after a second authenticated session refetches.

The only V1 non-goals are offline mutation queue/replay, PWA/service worker, WebSocket collaboration, and independently measured browser first-load time. These are recorded as V2 or non-blocking work rather than represented as Phase 6 behavior.
