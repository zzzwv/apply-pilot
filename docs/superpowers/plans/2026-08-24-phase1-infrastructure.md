# Phase 1 Infrastructure Implementation Plan

**Goal:** Bootstrap the job-application tracker with a tested FastAPI backend, React frontend shell, PostgreSQL/Redis Compose environment, and initial schema.

**Global constraints:** Use React, TypeScript, Vite, React Router, TanStack Query, Zustand, Ant Design, ECharts, Axios, Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic, Alembic, PostgreSQL, Redis, Docker Compose, pytest, Vitest, and Playwright. Keep all project dependencies, caches, virtual environments, and bind-mounted data on `E:\qiuzhao`; do not pull Docker images before Docker Desktop data storage is confirmed on E:. Do not implement company crawling, dashboards, search, sync, Celery, or full UI.

### Task 1: Backend foundation

Create dependency/configuration files, FastAPI application, API response/error/logging infrastructure, and database/Redis clients. Add tests first for the response envelope, error mapping, and dependency-aware health endpoint.

### Task 2: Domain persistence and migration

Create the six SQLAlchemy models, enums, repositories, Alembic asynchronous configuration, and initial migration. Add model metadata and migration tests before implementation.

### Task 3: Authentication foundation

Create schemas, user service/repository methods, JWT/password utilities, auth router, and tests for register/login/current-user behavior.

### Task 4: Frontend shell

Bootstrap the Vite TypeScript app, providers, routes, Axios client, Zustand state, and a testable application shell. Write the route rendering test before the implementation.

### Task 5: Containerization and handoff

Create Compose/Docker configuration, E-drive setup script, environment examples, and README. Verify config without pulling images; run all local syntax/test/build checks that do not violate the Docker storage constraint.
