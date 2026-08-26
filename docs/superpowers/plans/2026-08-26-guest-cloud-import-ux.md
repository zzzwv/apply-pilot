# Guest to Cloud Import UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Safely import opted-in guest IndexedDB applications to the resolved authenticated user's cloud account.

**Architecture:** A focused import coordinator reads guest records and their timelines, sends sequential batches of at most 200 to the existing API, persists only returned client-sync mappings in `cloud:<user_id>` metadata, invalidates/refetches cloud queries, then precisely removes mapped guest records. An authenticated-only modal component owns the session dismissal and invokes that coordinator.

**Tech Stack:** React, TanStack Query, Zustand, Ant Design, idb, Vitest, existing Axios API client.

**Spec:** `Prompt/Phase 6.md`, narrowed by the user request “Login → Guest Import UX”.

## Global Constraints

- Do not change backend API contract, migrations, Kimi, cloud cache/fallback, or performance work.
- Import payloads contain only local application/company/status-log data and `client_sync_id = local_id`.
- Batch requests are sequential and no larger than 200 applications.
- Only successful `imported`/`reused` mappings are cleaned up, and only after cloud snapshot refetch succeeds.
- Mapping metadata is stored under `cloud:<user_id>`; guest data is never bulk-cleared for partial success.
- Do not commit `Prompt/`, plans, `.env`, or runtime artifacts.

---

### Task 1: Local repository and sync API contracts

**Files:**
- Modify: `frontend/src/local-db/applicationRepository.ts`
- Modify: `frontend/src/local-db/applicationRepository.test.ts`
- Create: `frontend/src/api/sync.ts`
- Test: `frontend/src/api/sync.test.ts`

- [ ] Write failing repository/API tests for guest count, exact mapped cleanup, user-namespaced metadata, and a typed import response.
- [ ] Run the focused tests and verify RED because these operations/API client do not exist.
- [ ] Add minimal repository methods for count/listing records with logs, saving mappings, and exact removals; add a typed API wrapper.
- [ ] Run focused tests and verify GREEN.

### Task 2: Import coordinator

**Files:**
- Create: `frontend/src/sync/guestImport.ts`
- Create: `frontend/src/sync/guestImport.test.ts`

- [ ] Write failing tests for payload shaping, 200-item chunking, imported/reused mapping consumption, partial/total failures, retry idempotency, and cleanup only after successful cloud snapshot.
- [ ] Run the coordinator test and verify RED because the coordinator does not exist.
- [ ] Implement sequential import, mapping persistence under `cloud:<user_id>`, cloud refetch gate, exact cleanup, and user-safe result counts.
- [ ] Run focused tests and verify GREEN.

### Task 3: Authenticated import prompt and query refresh

**Files:**
- Create: `frontend/src/components/GuestImportPrompt/index.tsx`
- Create: `frontend/src/components/GuestImportPrompt/index.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] Write failing UI tests for no-record suppression, correct count, session dismissal without API calls, loading duplicate-click guard, partial-success copy, and cloud list/dashboard refetch.
- [ ] Run the UI test and verify RED because no authenticated prompt exists.
- [ ] Render the prompt only after `initialized && user`; connect it to the coordinator through TanStack Query invalidation/refetch.
- [ ] Run focused frontend sync tests and verify GREEN.

### Task 4: Final verification and scoped commit

**Files:**
- Stage only Task 1–3 frontend source/tests.

- [ ] Run frontend targeted sync tests, frontend full tests, existing backend sync-import test, frontend production build, and `git diff --check`.
- [ ] Check `git status --short`, stage exact files, and commit with `feat: add guest data import workflow`.
