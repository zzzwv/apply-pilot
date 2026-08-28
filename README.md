# ApplyPilot

> AI 驱动的求职投递管理与企业情报平台，帮助求职者集中管理投递进度、复盘求职数据，并快速补全企业公开信息。

## 📖 Introduction 项目简介

ApplyPilot 是一个面向个人求职场景的全栈毕业设计项目，解决职位信息分散、投递进度难追踪、企业信息收集成本高的问题。项目将投递记录、状态时间线、数据看板、企业情报和账户数据同步整合到统一工作台。

系统支持两种使用模式：

- **Guest Mode**：无需登录，数据保存在浏览器 IndexedDB，适合快速开始与本地管理。
- **Cloud Mode**：登录后通过云端 API 管理数据，并提供按用户隔离的本地读取缓存与离线回退能力。

## ✨ Features 项目特性

- 投递记录管理：创建、编辑、删除、批量删除职位投递记录，维护岗位、公司、城市、渠道、截止日期与备注。
- 状态时间线：覆盖未投递、已投递、笔试、面试、Offer、已签约等状态，记录变更时间和说明。
- 数据看板：统计投递总量、进行中数量、面试与 Offer 等关键指标，并展示投递趋势及多维度分布图表。
- 高效检索：支持按关键词、状态、企业性质、投递类型、行业、规模和日期筛选、排序。
- 企业情报：在 Cloud Mode 中查询或补全企业公开信息、招聘链接及来源信息；保存前可人工确认和编辑。
- AI 能力集成：可选接入 Kimi API，完成企业情报处理与联网检索流程。
- 本地与云端协同：Guest 数据可在登录后批量导入云端，使用 `client_sync_id` 保证同步幂等，避免重复导入。
- 账户与安全：支持注册、登录、JWT 鉴权、会话初始化和失效登录态清理。

## 🛠️ Tech Stack 技术栈

| 分类 | 技术与库 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite、React Router、Axios |
| 前端状态与数据 | TanStack React Query、Zustand、IndexedDB、idb |
| UI 与可视化 | Ant Design、ECharts |
| 后端 | Python、FastAPI、Uvicorn、Pydantic Settings、HTTPX |
| 数据层 | PostgreSQL、SQLAlchemy Async、asyncpg、Alembic |
| 缓存 | Redis |
| AI 服务 | Kimi API（可选） |
| 部署 | Docker、Docker Compose、Nginx |
| 测试 | pytest、Vitest、Testing Library、jsdom、fake-indexeddb |

## ⚙️ Environment Requirements 环境要求

| 组件 | 版本要求 |
| --- | --- |
| Docker / Docker Compose | Docker Desktop 最新稳定版；支持 `docker compose` 命令 |
| Python | 3.12.x（独立运行后端时） |
| Node.js | 20 LTS 或更高版本（独立运行前端时） |
| PostgreSQL | 16（容器化部署自动提供） |
| Redis | 7（容器化部署自动提供） |
| Kimi API Key | 可选；仅企业情报 AI / 联网检索功能需要 |

## 🚀 Quick Start 快速部署运行

### 1. 仓库克隆

```bash
git clone git@github.com:zzzwv/apply-pilot.git
cd apply-pilot
```

### 2. 配置说明

从示例文件创建本地配置：

```bash
cp .env.example .env
```

至少为 `JOB_TRACKER_JWT_SECRET_KEY` 设置一个足够长的随机值。若不使用企业情报 AI 功能，可保持 `JOB_TRACKER_KIMI_API_KEY` 为空。

```dotenv
JOB_TRACKER_JWT_SECRET_KEY=replace-with-a-long-random-secret
JOB_TRACKER_KIMI_API_KEY=
```

> 请勿提交 `.env` 或任何真实密钥。

### 3. 依赖安装与启动

推荐使用 Docker Compose，一次启动 PostgreSQL、Redis、FastAPI 后端和前端 Nginx 服务：

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

服务启动后：

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:8000/health
- API 前缀：http://localhost:8000/api/v1

停止服务：

```bash
docker compose down
```

### 4. 本地开发模式（可选）

先启动数据库和缓存：

```bash
docker compose up -d postgres redis
```

启动后端：

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

另开一个终端启动前端：

```bash
cd frontend
npm ci
npm run dev
```

Vite 开发服务器会将 `/api` 请求代理至 `http://localhost:8000`。

## 📂 Project Structure 项目目录结构

```text
.
├── backend/
│   ├── alembic/                    # 数据库迁移脚本
│   ├── app/
│   │   ├── api/                    # FastAPI 路由：认证、投递、看板、同步
│   │   ├── company_intelligence/   # Kimi、企业信息处理与链接校验
│   │   ├── core/                   # 配置、数据库、Redis、安全、中间件
│   │   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── repositories/           # 数据访问层
│   │   ├── schemas/                # 请求与响应模型
│   │   ├── services/               # 业务服务层
│   │   └── main.py                 # 应用入口
│   ├── tests/                      # 后端测试
│   ├── requirements-dev.txt        # 开发依赖
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/                    # API 客户端
│   │   ├── components/             # 通用 UI 组件
│   │   ├── dashboard/              # 看板指标与图表逻辑
│   │   ├── data/                   # Guest / Cloud 数据源与缓存
│   │   ├── local-db/               # IndexedDB Repository
│   │   ├── pages/                  # Dashboard、投递列表、详情等页面
│   │   ├── store/                  # 前端状态管理
│   │   └── sync/                   # Guest 数据导入逻辑
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   └── setup-dev.ps1               # Windows 开发环境辅助脚本
├── compose.yaml                    # 容器编排配置
├── .env.example                    # 环境变量示例
└── README.md                       # 原项目说明文档
```

## 📋 Function Description 功能说明

| 模块 | 功能说明 |
| --- | --- |
| 投递管理 | 维护职位投递的完整信息，并支持新增、编辑、删除、批量操作与多条件筛选。 |
| 进度追踪 | 通过状态时间线记录每次流程变化，便于回顾笔试、面试、Offer 等关键节点。 |
| 求职看板 | 汇总关键数据，按状态、行业、企业性质和时间维度呈现求职进展。 |
| 企业情报 | 检索、归一化并展示企业公开信息与招聘入口，支持人工编辑确认后保存。 |
| 游客模式 | 未登录用户可在浏览器本地完成投递记录、状态日志和看板管理。 |
| 云端模式 | 已登录用户的数据由 PostgreSQL 持久化，并通过用户隔离缓存改善读取体验。 |
| 数据迁移 | 将本地 Guest 数据安全导入云端，导入过程支持幂等处理与状态日志保留。 |
| 身份认证 | 提供注册、登录及 JWT 鉴权，保障不同用户的数据隔离。 |

## 🖼️ Screenshots

<!-- 建议在此放置真实项目截图：
![Dashboard](docs/images/dashboard.png)
![Applications](docs/images/applications.png)
![Company Intelligence](docs/images/company-intelligence.png)
-->

## 📝 License 开源协议 MIT

本项目采用 [MIT License](https://opensource.org/license/mit/) 开源协议。

## 🤝 Star 鼓励，欢迎 fork

如果这个项目对你有帮助，欢迎点亮 Star，也欢迎 Fork 后基于自己的求职流程继续完善。Issue 和 Pull Request 同样欢迎！
