请开始开发这个项目。

项目名称：

**秋招/实习投递状态管理 Web 网站**

项目的产品需求以 `docs/PRD.md` 为准，技术实现以 `docs/TDD.md` 为主要参考。

请先完整阅读这两个文档，不要凭自己的理解擅自修改产品需求。

## 你的第一步

先检查当前项目仓库，包括：

- 当前目录结构
- 已有代码
- package.json / requirements / pyproject.toml
- Git 状态
- 已有配置文件
- 数据库相关文件
- Docker 相关文件
- README
- docs 下的 PRD 和 TDD

如果当前仓库为空，则按照 TDD 从零初始化。

---

## 技术栈

前端：

- React
- TypeScript
- Vite
- React Router
- TanStack Query
- Zustand
- Ant Design
- ECharts
- Axios

后端：

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic
- PostgreSQL
- Redis

工程化：

- Docker
- Docker Compose
- pytest
- Vitest
- Playwright

不要擅自替换核心技术栈。

---

## 架构原则

后端保持基本分层：

```text
API
↓
Service
↓
Repository
↓
Database
```

核心业务至少划分为：

```text
Auth
Application
Application Status
Company Intelligence
Analytics
```

不要把所有代码都写进 FastAPI Router。

也不要在 V1 阶段引入：

- Kubernetes
- Elasticsearch
- 微服务
- Kafka
- 复杂消息中间件
- 不必要的 LLM

优先保证项目简单、正确、可运行、可维护。

---

# 当前只执行 Phase 1

本次不要直接开发整个项目。

只完成：

## Phase 1：项目初始化和后端基础设施

需要完成：

1. 创建合理的前后端目录结构；
2. 初始化 FastAPI 后端；
3. 初始化 React + TypeScript + Vite 前端；
4. 配置 PostgreSQL；
5. 配置 Redis；
6. 配置 SQLAlchemy 2.x；
7. 配置 Alembic；
8. 建立统一配置管理；
9. 建立统一 API Response；
10. 建立统一异常处理；
11. 建立基础 Logger；
12. 添加 `/health` 健康检查接口；
13. 配置 Docker Compose；
14. 建立基础数据库 Model。

本阶段至少建立以下核心实体：

```text
User
Company
CompanyAlias
RecruitmentLink
JobApplication
ApplicationStatusLog
```

JobApplication 的状态枚举至少包括：

```text
NOT_APPLIED
APPLIED
RESUME_PASSED
FIRST_INTERVIEW
SECOND_INTERVIEW
FINAL_INTERVIEW
HR_INTERVIEW
SALARY_NEGOTIATION
OFFER_RECEIVED
OFFER_REJECTED
RESUME_REJECTED
INTERVIEW_REJECTED
PROCESS_TERMINATED
SIGNED
```

---

## 当前阶段不要实现

暂时不要实现：

- 企业官网抓取
- 招聘页面发现
- 第三方招聘平台抓取
- Dashboard 图表
- 完整搜索筛选
- IndexedDB 云同步
- Celery
- AI/LLM
- 完整 UI

这些后续阶段再做。

---

# 开始写代码之前

先输出一个简洁的实施计划，包含：

### 1. 你对项目的理解

说明这个系统解决什么问题。

### 2. 当前仓库状态

告诉我目前仓库里已经有什么、缺什么。

### 3. Phase 1 文件规划

列出准备创建或修改的核心文件。

### 4. 数据库设计

说明：

```text
User
Company
CompanyAlias
RecruitmentLink
JobApplication
ApplicationStatusLog
```

之间的关系。

### 5. Phase 1 实施顺序

说明准备按什么顺序执行。

然后**直接开始开发，不需要等待我再次确认。**

---

# 开发要求

不要只输出代码建议，必须实际修改仓库文件。

每完成一个关键步骤后进行必要验证。

至少执行：

- 后端依赖检查
- Python import / syntax 检查
- 数据库 Model 检查
- Alembic migration 检查
- FastAPI 启动检查
- 前端 build 检查
- Docker Compose 配置检查
- 基础测试

如果遇到错误：

先定位根因，再修复。

不要通过删除功能、注释代码或跳过测试来让测试“假通过”。

---

# 完成 Phase 1 后

向我报告：

## Phase 1 完成情况

使用：

```text
✅ 已完成
⚠️ 存在问题
❌ 未完成
```

说明每项状态。

同时给出：

1. 创建/修改了哪些重要文件；
2. 数据库表结构；
3. 已实现接口；
4. 执行了哪些测试；
5. 测试实际结果；
6. 如何启动项目；
7. 当前尚未完成的内容；
8. 下一阶段建议。

没有实际运行验证过的内容，不要声称已经完成。

现在开始：**先阅读 PRD、TDD 和当前仓库，然后输出 Phase 1 实施计划并直接开始执行。**