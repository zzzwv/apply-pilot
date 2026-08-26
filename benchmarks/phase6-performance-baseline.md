# Phase 6 performance baseline

Local Docker benchmark, 2026-08-26. This is a reproducible local measurement, not a production capacity claim.

- Platform: `Linux-6.18.33.1-microsoft-standard-WSL2-x86_64-with-glibc2.41`
- PostgreSQL: `PostgreSQL 16.15 on x86_64-pc-linux-musl`
- Services: backend, frontend, PostgreSQL 16, Redis 7 via `docker compose`
- Dataset: 1,200 applications across 30 companies, one isolated marker-scoped performance user; mixed statuses, types, dates, industries, natures, sizes, and notes.
- Method: one cold request, two warmups, then ten timed warm requests per endpoint using one valid JWT. Target: 0.8 seconds.

| Endpoint | Median (s) | P95 (s) | Max (s) | Target | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Application list | 0.0198 | 0.0224 | 0.0227 | 0.8 | Pass |
| Application search | 0.0257 | 0.0280 | 0.0282 | 0.8 | Pass |
| Application status filter | 0.0139 | 0.0163 | 0.0164 | 0.8 | Pass |
| Application industry filter | 0.0150 | 0.0179 | 0.0184 | 0.8 | Pass |
| Application type filter | 0.0139 | 0.0161 | 0.0161 | 0.8 | Pass |
| Application date range | 0.0140 | 0.0174 | 0.0177 | 0.8 | Pass |
| Application multi-filter | 0.0108 | 0.0127 | 0.0129 | 0.8 | Pass |
| Application sort | 0.0174 | 0.0184 | 0.0185 | 0.8 | Pass |
| Dashboard summary | 0.0138 | 0.0155 | 0.0158 | 0.8 | Pass |
| Dashboard status distribution | 0.0111 | 0.0124 | 0.0126 | 0.8 | Pass |
| Dashboard industry distribution | 0.0109 | 0.0116 | 0.0119 | 0.8 | Pass |
| Dashboard company-nature distribution | 0.0113 | 0.0125 | 0.0127 | 0.8 | Pass |
| Dashboard trend | 0.0124 | 0.0131 | 0.0131 | 0.8 | Pass |

No endpoint exceeded the evidence threshold, so no SQL `EXPLAIN ANALYZE` or production-query optimization was warranted. The benchmark runner deletes only its own marker user and marker companies in a `finally` block.
