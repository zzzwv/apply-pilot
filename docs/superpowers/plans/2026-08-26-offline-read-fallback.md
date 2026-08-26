# Offline Read Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render user-scoped cached cloud application list and detail data only when recoverable cloud read failures occur.

**Architecture:** `CloudApplicationDataSource` owns cloud reads, Axios-error classification, cache writes, and fallback result metadata. React pages consume `{ data, source, stale, cached_at }`; mutations remain direct cloud API calls and are never queued or written optimistically.

**Tech Stack:** React, TanStack Query, Axios, Zustand, IndexedDB/idb, Vitest, fake-indexeddb.

**Spec:** User request in this task (2026-08-26).

## Global Constraints

- Use only `cloud:<authenticated current_user.id>` for cloud cache operations.
- Fall back only for network, timeout, connection, or 5xx read failures; never 401, 403, or 404 detail responses.
- Preserve existing Guest behavior and reuse `applyLocalApplicationFilters` for cached list semantics.
- No offline mutation queue, service worker, PWA, backend, Kimi, or performance changes.
- New tests follow RED → GREEN and use real IndexedDB where cache behavior is asserted.

---

### Task 1: Cache metadata and read-result data source

**Files:**
- Modify: `frontend/src/local-db/applicationRepository.ts`
- Modify: `frontend/src/data/cloudApplicationCache.ts`
- Create: `frontend/src/data/cloudApplicationDataSource.ts`
- Test: `frontend/src/data/cloudApplicationDataSource.test.ts`

**Interfaces:**
- Consumes: `CloudApplicationCache`, API list/detail functions, `applyLocalApplicationFilters` through the local data source.
- Produces: `CloudReadResult<T> = { data: T; source: "cloud" | "cache"; stale: boolean; cached_at?: string }` and `CloudApplicationDataSource.list/get/getStatusLogs`.

- [ ] **Step 1: Write failing cache/data-source tests**

```ts
expect(await source.list({ status: ["APPLIED"] })).toMatchObject({ source: "cache", stale: true });
expect(await source.get("a")).toMatchObject({ source: "cache", cached_at: expect.any(String) });
await expect(source.get("a")).rejects.toMatchObject({ response: { status: 404 } });
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts`

- [ ] **Step 3: Add the minimal cache metadata and data source**

```ts
if (!isRecoverableReadFailure(error)) throw error;
const cached = await this.localDataSource.list(params);
return { data: cached, source: "cache", stale: true, cached_at: await this.cache.latestCachedAt(...) };
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts`

### Task 2: List and detail page read integration

**Files:**
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`
- Test: `frontend/src/pages/Applications/offlineFallback.test.tsx`
- Test: `frontend/src/pages/ApplicationDetail/offlineFallback.test.tsx`

**Interfaces:**
- Consumes: authenticated `CloudApplicationDataSource` and `CloudReadResult`.
- Produces: stale cache notice and normal fresh-data replacement on refetch.

- [ ] **Step 1: Write failing UI tests**

```tsx
expect(await screen.findByText(/当前网络不可用/)).toBeDefined();
expect(await screen.findByText("Cached role")).toBeDefined();
```

- [ ] **Step 2: Run focused UI tests and verify RED**

Run: `npm test -- src/pages/Applications/offlineFallback.test.tsx src/pages/ApplicationDetail/offlineFallback.test.tsx`

- [ ] **Step 3: Consume the unified result and render a stale notice**

```tsx
const result = query.data;
const items = result?.data.items ?? [];
{result?.stale && <Alert type="warning" message={offlineNotice(result.cached_at)} />}
```

- [ ] **Step 4: Run focused UI tests and verify GREEN**

Run: `npm test -- src/pages/Applications/offlineFallback.test.tsx src/pages/ApplicationDetail/offlineFallback.test.tsx`

### Task 3: Mutation safety, user isolation, and regression checks

**Files:**
- Test: `frontend/src/pages/Applications/offlineFallback.test.tsx`
- Test: `frontend/src/pages/ApplicationDetail/offlineFallback.test.tsx`
- Test: `frontend/src/data/cloudApplicationDataSource.test.ts`

**Interfaces:**
- Consumes: current direct mutation calls and user-scoped cache repository.
- Produces: regression coverage proving failed mutations leave confirmed cache intact.

- [ ] **Step 1: Write failing safety tests**

```ts
await expect(sourceForB.list()).resolves.toMatchObject({ data: { items: [] }, source: "cache" });
await expect(failedUpdate()).rejects.toThrow();
expect(await cache.getApplication("a")).toMatchObject({ job_title: "server-confirmed" });
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts src/pages/Applications/offlineFallback.test.tsx src/pages/ApplicationDetail/offlineFallback.test.tsx`

- [ ] **Step 3: Keep mutations cloud-only and finalize query integration**

```ts
const response = await updateApplication(id, payload);
void writeCloudCacheSafely(() => cloudCache.upsertApplication(response));
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `npm test -- src/data/cloudApplicationDataSource.test.ts src/pages/Applications/offlineFallback.test.tsx src/pages/ApplicationDetail/offlineFallback.test.tsx`

- [ ] **Step 5: Verify and commit only Task files**

Run: `npm test`, `npm run build`, `git diff --check`, `git status --short`

```powershell
git add frontend/src/local-db/applicationRepository.ts frontend/src/data/cloudApplicationCache.ts frontend/src/data/cloudApplicationDataSource.ts frontend/src/data/cloudApplicationDataSource.test.ts frontend/src/pages/Applications/index.tsx frontend/src/pages/Applications/offlineFallback.test.tsx frontend/src/pages/ApplicationDetail/index.tsx frontend/src/pages/ApplicationDetail/offlineFallback.test.tsx
git commit -m "feat: add offline read fallback for cloud applications"
```
