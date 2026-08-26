# 秋招 / 实习投递状态管理

FastAPI、React/Vite、PostgreSQL、Redis、Alembic 与 JWT 的投递管理应用。Phase 6 已完成 Guest 本地工作流、登录后导入、用户隔离缓存和只读离线回退。

## E 盘开发环境

在 PowerShell 执行 `./scripts/setup-dev.ps1`。它将 `.venv`、pip/npm 缓存、临时目录和 PostgreSQL/Redis 持久化数据保留在 `E:\qiuzhao`。Docker Desktop disk image 应配置在 `E:\qiuzhao\.docker-data`。

复制 `.env.example` 为 `.env`，并为 `JOB_TRACKER_JWT_SECRET_KEY` 设置随机值。`JOB_TRACKER_KIMI_API_KEY` 是可选的后端环境变量；不得把任何真实密钥提交到 Git。

```powershell
docker compose up --build
```

- Frontend：`http://localhost:5173`
- Backend health：`http://localhost:8000/health`
- 本地后端：`backend\.venv\Scripts\uvicorn app.main:app --reload`
- 本地前端：在 `frontend` 运行 `npm run dev`

## 使用方式与数据边界

### Guest Mode

未登录用户使用现有的 Application、Detail 和 Dashboard UI。应用、企业展示字段和状态历史保存到当前浏览器的 IndexedDB `guest` namespace；支持创建、编辑、删除、状态变更、搜索、筛选、排序、分页和 Dashboard。

### Authentication

认证范围保持最小：注册、登录、登出和当前用户状态。接口为 `POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`。登出会删除 token、当前用户状态及该用户的 TanStack Query 数据，但不会删除 Guest 数据或云端缓存。

### Cloud Sync 与幂等导入

登录完成且当前用户已解析后，如果当前浏览器有 Guest 数据，界面会提示用户选择是否导入，绝不静默上传。导入调用 JWT 保护的 `POST /api/v1/sync/import-applications`，每批最多 200 条。

每条 Guest application 使用其 `local_id` 作为 `client_sync_id`。后端以 `(user_id, client_sync_id)` 的 partial unique index 保证同一用户重试返回 `reused`，不同用户可独立使用相同 local ID。客户端只消费服务端返回的真实 mapping，在云端 refetch 成功后才删除本次 `imported` 或 `reused` 的 Guest 记录；失败记录保留以便重试。

### Cloud Cache 与离线读取

登录用户以 PostgreSQL 为唯一 source of truth。IndexedDB 中的 `cloud:<user_id>` 仅是成功云端读取/写入后的用户隔离缓存，绝不会主动覆盖后端。

当 list 或 detail 发生网络/可恢复读取失败时，界面仅可回退到当前用户 namespace 的最近缓存，并显示 stale/offline 提示和缓存时间。401、403 与 detail 404 不会回退缓存。离线 Create、Edit、Status Change、Delete 都会明确失败；V1 不实现 mutation queue 或 replay。

## V1 Sync Limitations

1. Guest 数据仅保存在当前浏览器。
2. Guest 数据只能在登录后由用户显式导入。
3. 登录后的正式数据以 PostgreSQL 为准。
4. IndexedDB cloud 数据仅是 cache。
5. 离线 cloud 模式仅支持 stale read fallback。
6. 离线写操作不排队、不重放。
7. 跨设备更新需要下一次 refetch。
8. 不提供 WebSocket 实时协作。

## Company Intelligence

Company Intelligence 仅在登录后的 cloud 表单中可用；Guest 表单保留手工企业录入。Kimi API Key 只应存在于后端环境变量中，且不参与 Guest 导入、缓存或离线流程。

## Tests

```powershell
# Backend
cd backend
.venv\Scripts\python.exe -m pytest
.venv\Scripts\ruff.exe check app/schemas/application.py tests/test_sync_import.py

# Frontend
cd ..\frontend
npm test
npm run build

# Docker / migrations
cd ..
docker compose ps
docker compose exec -T backend alembic current
```

## Performance Evidence

本机 Docker / WSL2 上用 1,200 条 applications、30 家 companies、每端点 10 次 warm measured run 得到：列表/Search 的最高 P95 为 28.0ms，Dashboard 的最高 P95 为 15.5ms；IndexedDB 1,000 条 list/filter/dashboard 健全性测试通过。完整原始口径和各端点 median/P95/max 见 [benchmark evidence](benchmarks/phase6-performance-baseline.md)。这些是本机基准，不代表生产容量。首次加载时间为 `Not independently verified`。
