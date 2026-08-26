# Task 7 report — Company Intelligence and guest import polish

## Scope

- Updated only `CompanyIntelligenceField`, `GuestImportPrompt`, their component tests, and global frontend CSS.
- Kept Company Intelligence search, debounce, cancellation, confirmation, manual creation, URLs, evidence, timestamps, verification data, and source data paths unchanged.
- Kept guest-import detection, mutation, duplicate-click guard, dismissal, query invalidation/refetch, button labels, and disabled/loading states unchanged.

## RED

1. Added a Company Intelligence preview test requiring an accessible `招聘链接` heading, a visible `验证状态：候选` label, a `第三方来源` marker, and original target URLs as links.
2. Added a guest-import regression assertion requiring the named `同步本地投递记录` dialog to contain the detected-record count and retain `同步到账号` and `暂不同步` buttons.
3. Initial focused test execution was blocked before Vitest loaded by sandbox process spawning (`esbuild` `EPERM`). Re-ran with the required process permission.
4. The corrected RED run produced the expected Company Intelligence failure: `Unable to find an accessible element with the role "heading" and name "招聘链接"`. The guest-import assertion passed because its required behavior already existed.

## GREEN

- Replaced the company preview's visual-only dividers with labelled semantic preview, recruitment, and source sections.
- Added a visible verification-status tag and explicit `官方招聘` / `第三方来源` provenance labels.
- Rendered original recruitment target URLs as safe external links while retaining source URLs, evidence, last-checked timestamps, source type, and `target="_blank" rel="noreferrer"`.
- Added scoped card, spacing, provenance, and responsive styles in `global.css`.
- Added scoped guest-import modal classes and presentation-only content wrappers; mutation and callback code was retained verbatim.

## Verification evidence

| Command | Result |
| --- | --- |
| `npm test -- src/components/CompanyIntelligenceField/index.test.tsx src/components/GuestImportPrompt/index.test.tsx` | PASS — 2 files, 9 tests |
| `npm test -- src/components/CompanyIntelligenceField/index.test.tsx src/components/GuestImportPrompt/index.test.tsx src/api/companyIntelligence.test.ts` | PASS — 3 files, 11 tests |
| `npm test` | PASS — 25 files, 79 tests |
| `npm run build` | PASS — `tsc -b && vite build` completed successfully |
| `git diff --check` | PASS — no whitespace errors |

The full suite emitted pre-existing JSDOM/Ant Design compatibility warnings, but exited successfully with all tests passing. The build emitted Vite's existing chunk-size advisory only; it completed successfully.

## Self-review

- Confirmed the diff contains no backend, API, auth, cache, offline, data, dependency, manifest, prompt, plan, or specification changes.
- Confirmed the guest-import mutation/dismiss/invalidation code and button strings/disabled state are unchanged.
- Confirmed Company Intelligence persistence payload shaping and async workflow code are unchanged.
- No independent reviewer was dispatched because the assigned task explicitly prohibits subagents.
