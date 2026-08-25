# 秋招 / 实习投递状态管理

## Phase 1

FastAPI、React/Vite、PostgreSQL、Redis、Alembic 与 JWT 认证基础设施。

## E 盘开发环境

在 PowerShell 执行 `./scripts/setup-dev.ps1`。它把 `.venv`、pip/npm 缓存、临时目录和数据库持久化数据都放在 `E:\qiuzhao`。Docker Desktop 的 disk image 必须先在其设置中迁移到 `E:\qiuzhao\.docker-data`，再执行 Docker 命令。

复制 `.env.example` 为 `.env` 并设置随机 JWT 密钥。随后执行 `docker compose up --build`；本地后端可用 `backend\.venv\Scripts\uvicorn app.main:app --reload` 启动，前端用 `npm run dev` 启动。

认证接口：`POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`；健康检查：`GET /health`。
