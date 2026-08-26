# Cloud Cache and User Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cache successful authenticated application reads and writes in user-scoped IndexedDB namespaces while preventing any cross-user query or UI state exposure.

**Architecture:** A `CloudApplicationCache` converts existing `Application` and `ApplicationStatusLog` domain values into existing local-db records under `cloud:<authenticated-user-id>`. Page query/mutation success handlers call this cache as a non-blocking side effect only after API success; they never read it. Auth/query keys become user-scoped and initialization-gated, while logout cancels and removes only the departing user's queries and resets UI state without deleting IndexedDB namespaces.

**Tech Stack:** React, TanStack Query, Zustand, idb, fake-indexeddb, Vitest.

**Spec:** User-provided “Cloud → IndexedDB Cache + User Isolation” request in `pasted-text.txt`.

## Global Constraints

- Backend API remains the authenticated source of truth; IndexedDB is write-only cache in this task.
- Namespace always derives from resolved `useAuthStore().user.id`, as `cloud:<user_id>`.
- Cache failures never fail a successful HTTP read/mutation or render cached data.
- Do not implement offline fallback, cache-driven reads, mutation queues, Kimi, backend changes, or performance work.
- Logout preserves guest and cloud IndexedDB records but removes/cancels departing user query state and closes user-scoped UI state.
- Do not commit Prompt files, plans, `.env`, or runtime artifacts.

---

### Task 1: User-scoped cloud entity cache

**Files:**
- Create: `frontend/src/data/cloudApplicationCache.ts`
- Create: `frontend/src/data/cloudApplicationCache.test.ts`
- Modify: `frontend/src/local-db/applicationRepository.ts`
- Test: `frontend/src/local-db/applicationRepository.test.ts`

- [ ] Write failing fake-indexeddb tests that list/detail upserts land in `cloud:user-a`, user-b cannot read them, status logs are updated, and delete removes only the target entity/logs.
- [ ] Run focused tests and verify RED because cloud cache operations do not exist.
- [ ] Implement cache-only upsert/remove methods that reuse existing local-db entities and namespace keys; expose a safe `runCloudCacheWrite` wrapper that catches IndexedDB failures.
- [ ] Run focused tests and verify GREEN.

### Task 2: Cloud read/write cache side effects

**Files:**
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`
- Create: targeted page/cache tests.

- [ ] Write failing tests for list/detail/create/update/status/delete cache effects, mutation failure preservation, and cache-write failure not changing successful API outcomes.
- [ ] Run targeted tests and verify RED.
- [ ] Invoke cloud cache only after server response success, invalidate existing list/detail/log/dashboard queries, and retain API response as rendered data.
- [ ] Run targeted tests and verify GREEN.

### Task 3: Auth initialization and logout isolation

**Files:**
- Modify: `frontend/src/store/auth.ts`
- Modify: `frontend/src/store/auth.test.ts`
- Modify: `frontend/src/pages/Dashboard/index.tsx`
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`

- [ ] Write failing tests for initialization request gating, user-A-to-user-B query isolation, logout cancellation/removal/UI reset, and preservation of guest/cloud namespaces and user-scoped mappings.
- [ ] Run focused tests and verify RED.
- [ ] Add stable user keys, initialization gates, and logout cancellation/removal/reset with no IndexedDB deletion.
- [ ] Run focused tests and verify GREEN.

### Task 4: Verification and precise commit

- [ ] Run cloud-cache/auth targeted tests, frontend full tests, frontend production build, and `git diff --check`.
- [ ] Check `git status --short`, stage only Task 1–3 files, and commit `feat: add user-scoped cloud application cache`.
