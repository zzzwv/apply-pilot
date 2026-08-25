# Phase 3 Search, Filter, Sort, and Pagination Design

## Scope

Phase 3 enhances the existing authenticated application list. It adds no dashboard,
company-intelligence, Kimi, cache-sync, or background-job capability.

## API contract

`GET /api/v1/applications` remains the single list endpoint. It accepts `keyword`,
comma-separated `status`, `company_nature`, `application_type`, `industry`,
`date_from`, `date_to`, `company_size`, `sort`, `page`, and `page_size`.

Empty or whitespace-only keywords do not add a search condition. Repeated and
comma-separated filter values are normalized to enum/string lists by one
`ApplicationFilterParams` dependency. Validation rejects invalid enum values,
an inverted date range, pages below one, and page sizes outside 1–100.

## Query design

The repository owns list-query composition. Every query starts with
`JobApplication.user_id == current_user.id`, joins `Company` once, then applies:
keyword OR matching across company full/short name, job title, industry, company
nature, and note; AND-combined filters; one business sort; and offset/limit.
The count is derived from that fully filtered query before pagination.

The default sort is application date descending, then creation timestamp
descending and ID descending for stable pagination. Company-name sorting uses
`coalesce(Company.short_name, Company.full_name)`. Status-priority sorting uses a
SQL `CASE`: in-progress statuses first, pending next, successful next, and rejected
or terminated last; statuses within the same group retain a stable secondary order.

## Database design

A Phase 3 Alembic revision enables `pg_trgm` if absent and creates GIN trigram
indexes for `companies.full_name`, `companies.short_name`, `companies.industry`,
`job_applications.job_title`, and `job_applications.note`. Existing B-tree indexes
continue to serve ownership, date, status, and type filtering. Downgrade removes
only the newly owned indexes and leaves the potentially shared extension installed.

## Frontend design

The Applications page keeps query state locally and passes its exact normalized
object to both the API client and TanStack Query key. It has a debounced (300 ms)
keyword input, multi-select filters, preset/custom date ranges, an API-value sort
selector, table pagination, and a reset control. Any search/filter/sort change
resets the page to one. `placeholderData` preserves rows during a query refresh.
The empty view distinguishes a new account from an active query with no matches.

## Verification

Backend API tests cover every search field, case-insensitivity, filters and their
combination, all sorts, pagination totals, date validation, invalid values,
injection-shaped input, and ownership isolation. Frontend tests cover query
parameter serialization, debounce/query reset, clearing filters, sorting, and the
filtered empty state. Final verification runs the full Python suite, Ruff on
Phase-3 Python files, frontend tests/build, migration checks against PostgreSQL,
and Docker Compose configuration/startup without removing persistent volumes.
