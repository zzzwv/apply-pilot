# ApplyPilot V1.1 UI/UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade ApplyPilot's existing frontend into a cohesive, responsive, modern career SaaS interface without changing business behavior or data semantics.

**Architecture:** Keep the existing React Router routes, Zustand auth state, TanStack Query data flow and Guest/Cloud data sources intact. Add a single tokenized CSS layer plus small presentation-only components; individual pages consume those components while retaining their existing queries, mutations and callbacks.

**Tech Stack:** React 19, TypeScript, Vite, Ant Design 5, ECharts 5, React Router 7, TanStack Query 5, Zustand 5, React Testing Library, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-26-applypilot-v1.1-ui-ux-design.md`

## Global Constraints

- Modify only `frontend/` production/test files and purpose-built local SVG assets; do not change backend, migrations, Docker, API contracts, Kimi, auth, data sources, cache, import or offline semantics.
- Preserve all three routes: `/`, `/applications`, `/applications/:id`; do not add login/register routes.
- Retain the one shared `ApplicationForm` for Guest and Cloud paths and all 14 `ApplicationStatus` values/labels.
- Use Ant Design, existing transitive `@ant-design/icons`, and handcrafted local SVG only; add no new dependency, CDN image, bitmap asset or UI framework.
- Keep existing Prompt files and existing `docs/superpowers/plans/` files untracked; never use `git add .`.
- Do not modify `v1.0.0`, rewrite history, force-push, or push/merge any branch.
- Every behavioral change begins with a focused RTL/Vitest test that fails for the missing behavior, then receives the smallest implementation needed to pass.

---

### Task 1: Establish visual tokens, global foundation, and local artwork

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/global.css`
- Create: `frontend/src/assets/brand/applypilot-mark.svg`
- Create: `frontend/src/assets/illustrations/dashboard-career.svg`
- Create: `frontend/src/assets/illustrations/empty-dashboard.svg`
- Create: `frontend/src/assets/illustrations/empty-applications.svg`
- Create: `frontend/src/assets/illustrations/auth-career.svg`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces CSS custom properties prefixed `--ap-` for all shared colors, spacing, radii, shadows, focus and motion behavior.
- Produces importable Vite asset URLs for the logo and illustrations.

- [ ] **Step 1: Write the failing theme bootstrap test**

Add an assertion in `frontend/src/App.test.tsx` that renders `App` and expects the root application shell to have `data-testid="app-shell"`, and that the document has the `applypilot-app` class. This fails because neither marker exists.

```tsx
expect(screen.getByTestId("app-shell").classList.contains("applypilot-app")).toBe(true);
```

- [ ] **Step 2: Run the focused test and confirm the expected missing-shell failure**

Run:

```powershell
npm test -- src/App.test.tsx
```

Expected: the new assertion fails because `data-testid="app-shell"` is absent.

- [ ] **Step 3: Add the minimal global styling system**

Create `tokens.css` with `:root` values for `--ap-primary: #4F6EF7`, `--ap-primary-hover: #435FE0`, `--ap-secondary: #7C5CFC`, `--ap-page-bg: #F6F8FC`, `--ap-surface: #FFFFFF`, `--ap-text: #1F2937`, `--ap-text-secondary: #6B7280`, `--ap-text-muted: #9CA3AF`, `--ap-border: #E8ECF4`, semantic status colors, radius 12/16px, and light shadow. Create `global.css` to reset body margins, set Chinese-friendly system font fallback, style `.applypilot-app`, visible `:focus-visible`, reusable `.ap-card`, and a reduced-motion media query that removes transitions.

Import both CSS files exactly once from `main.tsx` before rendering React. Do not introduce a second styling mechanism or component-level hardcoded palette.

- [ ] **Step 4: Add lightweight SVG assets**

Create the five named SVG files with only paths/shapes, `viewBox`, blue/purple fills/strokes, no embedded bitmap/Base64 data and no third-party trademark. Decorative artwork must be suitable for `aria-hidden`; semantic empty-state images must have meaningful `alt` supplied by their consuming `<img>` element.

- [ ] **Step 5: Add the shell marker and verify green**

Apply `className="applypilot-app"` and `data-testid="app-shell"` on the outer visual shell in `App.tsx`, then rerun:

```powershell
npm test -- src/App.test.tsx
```

Expected: the new test and existing App tests pass.

- [ ] **Step 6: Commit only implementation files**

```powershell
git add frontend/src/main.tsx frontend/src/styles/tokens.css frontend/src/styles/global.css frontend/src/assets/brand/applypilot-mark.svg frontend/src/assets/illustrations/dashboard-career.svg frontend/src/assets/illustrations/empty-dashboard.svg frontend/src/assets/illustrations/empty-applications.svg frontend/src/assets/illustrations/auth-career.svg frontend/src/App.test.tsx
git commit -m "style: add applypilot visual foundation"
```

### Task 2: Build the branded application shell and preserve navigation/auth behavior

**Files:**
- Create: `frontend/src/components/AppHeader/index.tsx`
- Create: `frontend/src/components/AppHeader/index.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AuthControls/index.tsx`
- Modify: `frontend/src/components/AuthControls/index.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- `AppHeader({ queryClient?: QueryClient }): JSX.Element` renders the brand, the two existing route links and existing `AuthControls`.
- It derives route activity with `NavLink`; it does not own auth state or route state.

- [ ] **Step 1: Write failing header interaction tests**

Create `AppHeader` tests using `MemoryRouter`. Assert that `/` gives the “数据看板” link `aria-current="page"`, `/applications` gives the “投递记录” link `aria-current="page"`, and the visible brand name is “ApplyPilot”.

```tsx
expect(screen.getByRole("link", { name: "数据看板" }).getAttribute("aria-current")).toBe("page");
expect(screen.getByRole("img", { name: "ApplyPilot" })).toBeDefined();
```

- [ ] **Step 2: Run the header test and confirm it fails because the component is absent**

```powershell
npm test -- src/components/AppHeader/index.test.tsx
```

Expected: module-not-found failure for `AppHeader`.

- [ ] **Step 3: Implement the smallest shell replacement**

Create `AppHeader` using Ant Design `Layout.Header`, `NavLink`, the local mark and `AuthControls`. Give its `<img>` alt text `ApplyPilot`; use normal text buttons/links rather than unlabelled icon buttons. Replace the title/nav inline block in `App.tsx` with `AppHeader`, retain `AuthBootstrap`, `GuestImportPrompt`, `Routes`, lazy Dashboard import and all route elements unchanged.

Configure `ConfigProvider` with the spec's primary/background/text/radius/control-height tokens. Make the header sticky on desktop and wrap its content at narrow widths through CSS; keep auth as the existing Modal trigger, never a route.

- [ ] **Step 4: Brand the existing auth Modal without changing submissions**

Keep `mode`, `submitLogin`, `submitRegister`, error strings, form item names, validation and Zustand calls exactly intact. Add a noninteractive brand/illustration region within the Modal, a concise title/subtitle, and CSS classes; hide the illustration at small widths. Ensure form labels and submit buttons keep their accessible names.

- [ ] **Step 5: Verify focused tests and all existing auth tests**

```powershell
npm test -- src/components/AppHeader/index.test.tsx src/components/AuthControls/index.test.tsx src/App.test.tsx
```

Expected: header active-link, login/register/logout and App route tests pass.

- [ ] **Step 6: Commit only the shell/auth implementation**

```powershell
git add frontend/src/components/AppHeader frontend/src/App.tsx frontend/src/components/AuthControls frontend/src/styles/global.css
git commit -m "feat: polish application shell and authentication"
```

### Task 3: Centralize status visuals and reusable display primitives

**Files:**
- Create: `frontend/src/components/EmptyState/index.tsx`
- Create: `frontend/src/components/EmptyState/index.test.tsx`
- Create: `frontend/src/components/PageHeader/index.tsx`
- Modify: `frontend/src/components/StatusTag/index.tsx`
- Create: `frontend/src/components/StatusTag/index.test.tsx`
- Modify: `frontend/src/pages/Dashboard/chartOptions.ts`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- `getStatusVisual(status: ApplicationStatus): { color: string; category: "neutral" | "progress" | "success" | "warning" | "danger" }` is exported alongside `StatusTag`.
- `EmptyState({ image, title, description, action }: Props)` renders an accessible empty panel and optional real action.
- `PageHeader({ title, description, extra }: Props)` only controls presentation of existing page actions.

- [ ] **Step 1: Write failing status and empty-state tests**

Test every value in `statusLabels` against `getStatusVisual`, asserting it returns a nonempty color/category. Render `EmptyState` with a button action and assert both description and the passed action are reachable by role.

```tsx
for (const status of Object.keys(statusLabels) as ApplicationStatus[]) {
  expect(getStatusVisual(status).color).not.toBe("");
}
expect((screen.getByRole("button", { name: "新增投递" }) as HTMLButtonElement).disabled).toBe(false);
```

- [ ] **Step 2: Run the focused tests and confirm expected failures**

```powershell
npm test -- src/components/StatusTag/index.test.tsx src/components/EmptyState/index.test.tsx
```

Expected: missing export/component failures.

- [ ] **Step 3: Implement shared presentation components**

Map all fourteen statuses into the five named categories. Render `StatusTag` with category class plus Ant Design `Tag`, preserving `statusLabels[status]`. Update dashboard chart options to use `getStatusVisual(status).color`; set consistent blue/purple series colors for non-status charts. Implement `EmptyState` with an `<img>` alt, title, description and optional `action` node. Implement `PageHeader` with semantic title/description and existing `extra` action slot.

- [ ] **Step 4: Verify focused tests and chart compilation**

```powershell
npm test -- src/components/StatusTag/index.test.tsx src/components/EmptyState/index.test.tsx
npm run build
```

Expected: every status map is covered and TypeScript accepts ECharts options.

- [ ] **Step 5: Commit only these shared presentation files**

```powershell
git add frontend/src/components/EmptyState frontend/src/components/PageHeader frontend/src/components/StatusTag frontend/src/pages/Dashboard/chartOptions.ts frontend/src/styles/global.css
git commit -m "feat: add shared status and display primitives"
```

### Task 4: Redesign Dashboard while retaining all filters, queries and chart behavior

**Files:**
- Modify: `frontend/src/pages/Dashboard/index.tsx`
- Modify: `frontend/src/pages/Dashboard/index.test.tsx`
- Modify: `frontend/src/components/DashboardChart/index.tsx`
- Create: `frontend/src/components/DashboardChart/index.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- The Dashboard keeps `initialFilters`, `updateFilters`, `refetchAll`, query keys/query functions and granularity values unchanged.
- Hero “新增投递” navigates to `/applications` with an explicit `location.state.openCreate` presentation intent; ApplicationsPage consumes only that intent to open its existing shared Drawer.

- [ ] **Step 1: Write failing Dashboard CTA and empty-state tests**

Extend the Dashboard test to render an empty Guest dashboard in a `MemoryRouter`, click “新增投递” in the dashboard Hero/empty state, and expect navigation to the existing applications route. Add a test asserting the reset button clears the keyword and restores all data when filters are active.

```tsx
await user.click(screen.getByRole("button", { name: "新增投递" }));
expect(screen.getByText("投递记录")).toBeDefined();
```

- [ ] **Step 2: Run the focused test and confirm it fails for the absent CTA/route behavior**

```powershell
npm test -- src/pages/Dashboard/index.test.tsx
```

Expected: the Hero/empty-state CTA is not found.

- [ ] **Step 3: Implement the dashboard visual hierarchy**

Use `PageHeader` and a Hero Card with the local career SVG. Keep `refetchAll`; place it as an accessible secondary action. Implement the primary CTA with `useNavigate` to `/applications` and `{ state: { openCreate: true } }`. In Task 5, ApplicationsPage reads this narrow presentation intent from `location.state` and calls its existing `setApplicationDrawerOpen(true)` callback. Render the six actual summary values in icon KPI cards without comparative claims. Convert the filter `Space` into labelled responsive grid fields and reuse current `setKeywordInput`, `updateFilters`, `hasFilters`, and clear callback unchanged.

Use `EmptyState` for initial empty data and filtered empty data with only real CTA actions. Give each chart Card an explanatory subtitle, consistent spacing and responsive height. Update `DashboardChart` to render the shared empty presentation instead of the generic Ant Empty while preserving the no-init-on-empty guard and resize cleanup.

- [ ] **Step 4: Verify Dashboard, Guest filter and app tests**

```powershell
npm test -- src/pages/Dashboard/index.test.tsx src/App.test.tsx src/dashboard/metrics.test.ts
```

Expected: dashboard rendering, Guest IndexedDB filtering, CTA navigation and existing metric calculations pass.

- [ ] **Step 5: Commit only dashboard presentation changes**

```powershell
git add frontend/src/pages/Dashboard frontend/src/components/DashboardChart frontend/src/styles/global.css
git commit -m "feat: redesign dashboard experience"
```

### Task 5: Polish the application list without altering CRUD, filters, or cache behavior

**Files:**
- Modify: `frontend/src/pages/Applications/index.tsx`
- Modify: `frontend/src/pages/Applications/index.test.tsx`
- Modify: `frontend/src/pages/Applications/offlineFallback.test.tsx`
- Modify: `frontend/src/pages/Applications/cloudCache.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Existing `params`, `clearFilters`, mutation functions, `ApplicationForm` props and query keys remain unchanged.
- The page continues to render the exact stale cache message and uses `clearFilters` as the only reset action.
- When `location.state` contains `{ openCreate: true }`, the existing `setApplicationDrawerOpen(true)` callback opens the shared `ApplicationForm`; it must coexist with the existing `{ editApplication }` location state.

- [ ] **Step 1: Write failing empty-state CTA tests**

In `index.test.tsx`, render `/applications` with `initialEntries={[{ pathname: "/applications", state: { openCreate: true } }]}` and assert `applicationDrawerOpen` becomes true. Also render a Guest list with no items, click its “新增投递” empty-state action, and assert `applicationDrawerOpen` becomes true. Render an active filter with no rows, click “清空筛选”, and assert the existing list query eventually receives the default sort/page without keyword.

```tsx
await user.click(screen.getByRole("button", { name: "新增投递" }));
expect(useUiStore.getState().applicationDrawerOpen).toBe(true);
```

- [ ] **Step 2: Run tests and confirm failures are caused by missing empty-state actions**

```powershell
npm test -- src/pages/Applications/index.test.tsx
```

- [ ] **Step 3: Implement presentation-only list changes**

Read `location.state` as the existing edit-state shape plus an optional `openCreate` flag; when that flag is true, call the original `setApplicationDrawerOpen(true)` in an effect without setting `editing`. Preserve the existing edit-state effect. Replace the current title row with `PageHeader`, retaining the original “新增投递” callback. Wrap controls in a labelled filter Card and retain every current Input/Select/DatePicker value and handler. Replace generic initial/filter empty views with `EmptyState`; initial action calls `setApplicationDrawerOpen(true)`, filtered action calls `clearFilters`. Keep stale `Alert` text, Table columns, Link targets, mutations, pagination and cache writes unchanged.

- [ ] **Step 4: Verify behavior and offline/cache regressions**

```powershell
npm test -- src/pages/Applications/index.test.tsx src/pages/Applications/offlineFallback.test.tsx src/pages/Applications/cloudCache.test.tsx
```

Expected: create/edit/delete behavior, Guest data, stale fallback and user-isolated cloud cache tests pass.

- [ ] **Step 5: Commit only application-list implementation files**

```powershell
git add frontend/src/pages/Applications frontend/src/styles/global.css
git commit -m "feat: polish application management list"
```

### Task 6: Improve detail, timeline, and shared form structure

**Files:**
- Modify: `frontend/src/pages/ApplicationDetail/index.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/offlineFallback.test.tsx`
- Modify: `frontend/src/pages/ApplicationDetail/cloudCache.test.tsx`
- Modify: `frontend/src/components/ApplicationForm/index.tsx`
- Modify: `frontend/src/components/ApplicationForm/index.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- Detail query/mutation functions, stale computation, Guest-only actions and status update callback remain untouched.
- `ApplicationForm` keeps its `Props`, `submit` payload conversion and Guest/Cloud conditional logic exactly intact.

- [ ] **Step 1: Write failing detail/form structural interaction tests**

Add an assertion that a loaded detail exposes the job title as the page heading and the current status label in a named “当前状态” region. Add assertions that the shared Drawer displays real section headings “基本信息”“企业信息”“投递信息”“补充信息” while Guest mode still has manual company inputs and Cloud mode still has the company intelligence field.

```tsx
expect(screen.getByRole("heading", { name: "测试岗位" })).toBeDefined();
expect(screen.getByRole("heading", { name: "基本信息" })).toBeDefined();
```

- [ ] **Step 2: Run focused tests and confirm missing visual landmarks**

```powershell
npm test -- src/pages/ApplicationDetail/offlineFallback.test.tsx src/components/ApplicationForm/index.test.tsx
```

- [ ] **Step 3: Implement semantic layout changes only**

Wrap detail in a responsive CSS grid: primary application/timeline column and secondary metadata column when space permits, collapsing to one column on tablet/mobile. Keep status selection, remark input, mutate call, navigation, Guest edit/delete, status logs and stale Alert exactly as they are. Group current form fields under the four semantic headings inside the same Drawer/Form; never split Guest/Cloud into distinct forms or alter `submit`.

- [ ] **Step 4: Verify detail, shared form, offline and cache behavior**

```powershell
npm test -- src/pages/ApplicationDetail/offlineFallback.test.tsx src/pages/ApplicationDetail/cloudCache.test.tsx src/components/ApplicationForm/index.test.tsx
```

Expected: timeline, stale fallback, cache side effects, Guest manual fields and Cloud intelligence flow remain green.

- [ ] **Step 5: Commit only detail/form files**

```powershell
git add frontend/src/pages/ApplicationDetail frontend/src/components/ApplicationForm frontend/src/styles/global.css
git commit -m "feat: polish application detail and form"
```

### Task 7: Refine Company Intelligence and import feedback without changing workflow

**Files:**
- Modify: `frontend/src/components/CompanyIntelligenceField/index.tsx`
- Modify: `frontend/src/components/CompanyIntelligenceField/index.test.tsx`
- Modify: `frontend/src/components/GuestImportPrompt/index.tsx`
- Modify: `frontend/src/components/GuestImportPrompt/index.test.tsx`
- Modify: `frontend/src/styles/global.css`

**Interfaces:**
- `CompanyIntelligenceField` retains its current props, debounce/search/confirm/manual callbacks, source URLs and verification labels.
- `GuestImportPrompt` retains its existing import outcome behavior, dismiss semantics and query invalidation.

- [ ] **Step 1: Write failing semantic-card tests**

Extend company tests to expect a labelled “招聘链接” section, source entries with their original URLs, and a visible verification label after preview. Extend import tests to expect the unchanged “同步到账号” and “暂不同步” actions inside a dialog with an accessible description of detected records.

```tsx
expect(screen.getByRole("heading", { name: "招聘链接" })).toBeDefined();
expect(screen.getByRole("dialog", { name: "同步本地投递记录" }).textContent).toContain("检测到 2 条本地投递记录");
```

- [ ] **Step 2: Run focused tests and confirm missing semantic landmarks**

```powershell
npm test -- src/components/CompanyIntelligenceField/index.test.tsx src/components/GuestImportPrompt/index.test.tsx
```

- [ ] **Step 3: Implement card hierarchy with no data-flow edits**

Add classes/semantic headings around existing preview, links, sources and verification Tag. Keep links target/rel, evidence, timestamps, source type and manual fallback unchanged; visually label third-party sources as third party. Update Guest import Modal classes and explanatory text only; retain `syncing`, mutation callbacks, button labels and disabling conditions.

- [ ] **Step 4: Verify Company Intelligence and import regressions**

```powershell
npm test -- src/components/CompanyIntelligenceField/index.test.tsx src/components/GuestImportPrompt/index.test.tsx src/api/companyIntelligence.test.ts src/api/sync.test.ts
```

Expected: search, candidate confirmation, manual fallback, sources, import retries and API request shapes pass.

- [ ] **Step 5: Commit only Company Intelligence/import presentation files**

```powershell
git add frontend/src/components/CompanyIntelligenceField frontend/src/components/GuestImportPrompt frontend/src/styles/global.css
git commit -m "feat: polish company intelligence interface"
```

### Task 8: Complete responsive/accessibility styling and perform visual/browser checks

**Files:**
- Modify: `frontend/src/styles/global.css`
- Modify: only tests needing explicit accessibility assertions from Tasks 2--7

**Interfaces:**
- No API/data/state interface changes; CSS is responsible for breakpoints and reduced-motion only.

- [ ] **Step 1: Write failing accessibility assertions**

Add tests that the refresh action has `aria-label="刷新数据"`, AppHeader's logo has alt text, decorative illustration image is hidden from assistive technology, and no icon-only control lacks an accessible name.

- [ ] **Step 2: Run relevant tests and confirm the newly required accessibility hook fails where absent**

```powershell
npm test -- src/App.test.tsx src/pages/Dashboard/index.test.tsx src/components/AppHeader/index.test.tsx
```

- [ ] **Step 3: Add responsive and accessibility CSS**

Add breakpoints for 1024px, 768px and 480px: compact/wrapping Header; Hero stacking/hiding artwork; 3x2 then 1--2 KPI columns; filters collapsing to one column; tables retaining safe horizontal container only within the table region; details collapsing to one column; Drawer becoming viewport-safe. Ensure SVG `aria-hidden`/alt and explicit labels match tests. Add focus-visible and reduced-motion behavior only through the shared CSS.

- [ ] **Step 4: Verify focused accessibility tests and manually inspect the four required widths**

Run the focused test command from Step 2. If browser tooling is available, inspect Dashboard, applications, detail, login/register Modal and Company Intelligence at 1440, 1024, 768 and 375px. Record exact screenshots/observations; if no browser automation is available, record `Visual Browser Verification: Not independently automated` in the final report.

- [ ] **Step 5: Commit responsive/accessibility implementation only**

```powershell
git add frontend/src/styles/global.css frontend/src/App.test.tsx frontend/src/pages/Dashboard/index.test.tsx frontend/src/components/AppHeader/index.test.tsx
git commit -m "fix: improve responsive application layout"
```

### Task 9: Run the V1.1 regression, bundle, scope, and secret gates

**Files:**
- Modify: no source file unless a verified test/build regression requires a minimal fix.

**Interfaces:**
- The release gate accepts the existing V1 frontend behavior plus the approved UI changes; no backend verification is required because no backend file may be changed.

- [ ] **Step 1: Run the complete frontend test suite**

```powershell
npm test
```

Expected: all existing and newly added frontend tests pass; investigate any failure with the systematic debugging process before editing production code.

- [ ] **Step 2: Run production build and record bundle evidence**

```powershell
npm run build
```

Record the largest raw and gzip assets emitted by Vite and compare to the V1 baseline of approximately 1.35MB raw / 428KB gzip. Explain any material increase; do not add a dependency to solve a visual issue.

- [ ] **Step 3: Validate whitespace, scope, and protected files**

```powershell
git diff --check
git diff --name-only main...HEAD
git status --short
git diff -- frontend package.json package-lock.json
```

Expected: no whitespace errors; code diff stays under `frontend/` plus the committed design spec; no backend/alembic/Docker/API changes; no Prompt, existing plan, `.env`, runtime, node_modules or temporary asset is staged.

- [ ] **Step 4: Audit for secrets in changed, trackable content**

```powershell
git diff main...HEAD -- frontend | rg -n "(api[_-]?key|jwt|secret|password)\\s*[:=]\\s*['\"][^'\"]+"
```

Expected: no credential-like literal is introduced. Existing field labels/types and test placeholders are reviewed as non-secret context rather than credentials.

- [ ] **Step 5: Prepare the acceptance report without merging, pushing, tagging, or deleting branches**

Report branch/HEAD, global theme, shell, Dashboard, management pages, auth, Company Intelligence, Guest/Cloud/offline/import regression, responsive/accessibility results, test count, build output, bundle comparison, visual verification status, scope and secret audit. Stop for user acceptance; do not merge to main, push, create `v1.1.0`, or delete `ui-polish-v1.1`.
