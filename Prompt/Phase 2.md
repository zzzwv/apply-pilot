# Phase 2 Codex 开发任务

## 1. 项目背景

你正在继续开发：

**秋招/实习投递状态管理 Web 网站**

当前项目路径：

```text
E:\qiuzhao
```

Phase 1 已经开发并完成真实环境复验。

当前已经具备：

- React + TypeScript + Vite 前端基础工程
- FastAPI 后端基础工程
- PostgreSQL
- Redis
- SQLAlchemy 2.x
- Alembic
- Docker Compose
- JWT Authentication
- `/health`
- 用户注册
- 用户登录
- 当前用户接口
- User
- Company
- CompanyAlias
- RecruitmentLink
- JobApplication
- ApplicationStatusLog
- ApplicationStatus 14 状态枚举
- 基础 Repository
- 统一异常处理
- 统一 API Response
- 日志与 Request ID

Phase 1 已完成以下真实验证：

```text
Docker ✅
PostgreSQL ✅
Redis ✅
Alembic ✅
FastAPI ✅
JWT ✅
pytest 9 passed ✅
React Build ✅
Docker Compose ✅
数据持久化 ✅
```

因此：

**不要重新初始化项目，不要重建 Phase 1，不要覆盖已经验证通过的基础设施。**

---

# 2. 开发依据

开发前必须完整阅读：

```text
docs/PRD.md
docs/TDD.md
```

如果实际文件名不同，请在 `docs/` 中找到对应：

- 产品需求文档 PRD
- 最新技术设计文档 TDD

当前最新 TDD 为：

**Kimi 联网搜索增强版**

但是本阶段暂时不开发 Kimi。

规则：

```text
PRD = 产品需求事实来源
TDD = 技术实现主要依据
当前仓库代码 = 已完成工程事实
```

如果文档与当前已经通过 Phase 1 验证的工程结构存在细微实现差异：

不要为了机械匹配文档破坏已经稳定运行的基础设施。

在满足 PRD/TDD 目标的前提下优先保持现有架构一致性。

---

# 3. 当前阶段

现在正式进入：

# Phase 2：核心投递记录管理 + 投递状态管理

本阶段只完成：

```text
JobApplication CRUD
+
Application Status
+
ApplicationStatusLog
+
用户数据隔离
+
基础分页
```

目标是形成第一条完整业务闭环：

```text
用户注册 / 登录
        ↓
创建投递记录
        ↓
查看投递列表
        ↓
查看投递详情
        ↓
编辑投递记录
        ↓
更新投递状态
        ↓
自动生成状态日志
        ↓
查看状态历史
        ↓
删除投递记录
```

---

# 4. 本阶段禁止提前实现的内容

Phase 2 暂时不要开发：

- Kimi
- Kimi 2.5 API
- Company Intelligence
- 企业联网搜索
- 企业数据自动抓取
- 企业官网识别
- 官方招聘入口发现
- 招聘 JD 抽取
- LinkValidator 完整业务
- Redis 企业缓存
- Celery
- Dashboard
- ECharts Dashboard 页面
- pg_trgm
- 高级关键词搜索
- 多条件组合筛选
- 高级排序
- IndexedDB 云同步
- AI 推荐
- 简历匹配

这些属于后续 Phase。

禁止扩大本阶段开发范围。

---

# 5. Git 检查

开始修改代码之前：

```bash
git status
git branch --show-current
git log --oneline --decorate -5
```

确认：

1. Phase 1 已提交；
2. 当前代码不存在冲突；
3. 当前工作区没有未知脏文件；
4. 当前最好位于：

```text
phase2-application-core
```

分支。

如果仍位于 Phase 1 分支：

不要擅自删除任何内容。

创建新的 Phase 2 分支后继续。

---

# 6. 首先检查现有代码

开发前阅读当前：

```text
backend/app/models/
backend/app/schemas/
backend/app/repositories/
backend/app/services/
backend/app/api/
backend/app/core/
backend/tests/
```

重点确认：

```text
JobApplication
Company
User
ApplicationStatus
ApplicationStatusLog
```

当前字段和关系。

不要因为 Prompt 中给出示例就重复创建已有 Model。

如果已有 Model 能满足需求：

直接复用。

只有确实缺字段、约束或关系时才修改。

修改 Model 后必须同步 Alembic。

---

# 7. Phase 2 核心领域关系

必须保持：

```text
User
 │
 │ 1:N
 ▼
JobApplication
 │
 ├──────── N:1 ──────── Company
 │
 └──────── 1:N ──────── ApplicationStatusLog
```

其中：

```text
Company
```

属于公共企业数据。

而：

```text
JobApplication
ApplicationStatusLog
```

属于用户私有数据。

---

# 8. ApplicationStatus

必须继续使用 Phase 1 已有 14 个状态：

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

不要重新设计另一套状态体系。

不要直接在数据库保存中文状态字符串。

---

# 9. JobApplication CRUD

实现以下 API：

```http
POST /api/v1/applications
```

创建投递记录。

```http
GET /api/v1/applications
```

查询当前用户投递列表。

```http
GET /api/v1/applications/{application_id}
```

查询当前用户单条投递详情。

```http
PUT /api/v1/applications/{application_id}
```

编辑投递记录。

```http
DELETE /api/v1/applications/{application_id}
```

删除单条投递记录。

```http
POST /api/v1/applications/batch-delete
```

批量删除。

---

# 10. Application 创建字段

根据当前 Model 和 PRD/TDD，至少支持：

```text
company_id

job_title

application_type

application_date

channel

resume_version

salary

city

education_requirement

deadline

requirements

note

current_status
```

如果现有 Model 字段名略有差异：

优先保持当前项目一致性，但 API Schema 应清晰。

---

# 11. user_id 强制后端生成

创建 Application 时：

客户端绝对不能决定：

```text
user_id
```

禁止：

```json
{
  "user_id": "xxx"
}
```

由后端：

```python
current_user.id
```

写入。

例如：

```text
JWT
 ↓
get_current_user
 ↓
current_user.id
 ↓
JobApplication.user_id
```

防止越权创建数据。

---

# 12. 用户数据隔离

这是 Phase 2 最重要的安全要求之一。

任何：

```text
GET
PUT
DELETE
PATCH
Status Logs
```

必须验证记录属于当前用户。

逻辑必须等价于：

```sql
SELECT *
FROM job_applications
WHERE id = :application_id
AND user_id = :current_user_id
```

禁止：

```sql
SELECT *
FROM job_applications
WHERE id = :application_id
```

然后再无条件返回。

---

# 13. IDOR 防护

构造：

```text
User A

User B
```

必须验证：

```text
User A
```

不能：

- 查看 B 的 Application
- 编辑 B 的 Application
- 删除 B 的 Application
- 修改 B 的状态
- 查看 B 的 Status Logs

建议对于不存在或不属于自己的资源统一返回：

```text
404
```

避免泄露资源是否存在。

如果当前全局异常规范使用 403，也可以遵循现有规范，但必须保证绝不泄露数据。

---

# 14. Company 在 Phase 2 的处理

Phase 2 不实现企业智能搜查。

但是创建 JobApplication 依赖：

```text
company_id
```

因此需要保证能够存在 Company 数据。

优先方案：

### 测试

通过 Fixture / Factory 创建 Company。

### 真实 API 手工联调

如果当前项目还不存在最小企业创建能力，可以增加：

```http
POST /api/v1/companies
```

用于手工创建基础企业。

但必须保持简单。

只实现 Phase 2 所需要的最小字段。

禁止借此提前实现：

```text
Company Intelligence
Kimi Search
Official Website Discovery
```

---

# 15. 同企业多岗位必须允许

不要增加：

```text
UNIQUE(user_id, company_id)
```

因为用户可能：

```text
腾讯
├── AI应用开发工程师
└── 后端开发工程师
```

同时投递。

甚至同岗位不同时间再次投递也可能存在。

重复企业提示属于业务提醒：

不是数据库唯一约束。

---

# 16. Pydantic Schema

不要使用一个万能 Schema。

建议至少拆分：

```text
ApplicationCreate

ApplicationUpdate

ApplicationRead

ApplicationListItem

ApplicationListResponse

ApplicationStatusUpdate

ApplicationStatusLogRead

ApplicationBatchDeleteRequest
```

Create：

不包含：

```text
id
user_id
created_at
updated_at
```

Update：

所有可修改字段应根据业务合理设置为 optional。

Read：

包含服务端字段。

---

# 17. PUT 更新规则

`PUT /applications/{id}`：

只允许修改业务字段。

禁止用户通过 Update API 修改：

```text
id
user_id
created_at
updated_at
```

状态修改推荐：

```text
不要通过普通 PUT 修改 current_status
```

而统一使用专门 Status API。

这样才能保证每一次状态变化都留下日志。

如果 `ApplicationUpdate` 当前包含 `current_status`：

请调整设计。

---

# 18. 状态更新 API

实现：

```http
PATCH /api/v1/applications/{application_id}/status
```

Request：

```json
{
  "status": "FIRST_INTERVIEW",
  "remark": "一面完成"
}
```

---

# 19. 状态更新事务

状态修改必须保证：

```text
BEGIN
  ↓
查询 JobApplication
  ↓
验证 user_id
  ↓
old_status = current_status
  ↓
UPDATE current_status
  ↓
INSERT ApplicationStatusLog
  ↓
COMMIT
```

任何一步失败：

```text
ROLLBACK
```

绝对不能出现：

```text
Application 已变状态
但是
StatusLog 写入失败
```

或者反过来。

---

# 20. ApplicationStatusLog

每条日志至少包含：

```text
id

application_id

from_status

to_status

remark

changed_at
```

如果现有 Model 还额外包含：

```text
created_at
```

可以保持现有设计。

---

# 21. 初始状态日志

创建 JobApplication 时：

推荐同时生成一条初始状态日志：

```text
from_status = null

to_status = initial_status
```

例如：

```text
null
→
APPLIED
```

这样状态历史完整包含：

```text
创建记录
→ 后续全部状态变化
```

如果现有数据库字段：

```text
from_status
```

已经允许 NULL：

采用此方案。

如果 Phase 1 Model 有其他明确设计：

先分析现有代码，再选择最小改动方案。

无论采用什么方案：

必须增加测试。

---

# 22. 相同状态处理

如果：

```text
current_status = FIRST_INTERVIEW
```

用户再次提交：

```text
FIRST_INTERVIEW
```

不要无意义生成重复状态日志。

推荐返回：

```text
STATUS_NOT_CHANGED
```

或者按照项目统一响应返回当前状态。

核心原则：

```text
状态没有变化
→ 不生成新的 StatusLog
```

---

# 23. 状态流转限制

当前 PRD 允许：

```text
用户自主更新、回改状态
```

因此 Phase 2：

不要实现过于严格的状态机跳转限制。

例如：

```text
FIRST_INTERVIEW
```

用户可以因为纠错修改回：

```text
APPLIED
```

不要强制只能向前流转。

但每一次真实变化都必须留下日志。

---

# 24. 状态日志查询

实现：

```http
GET /api/v1/applications/{application_id}/status-logs
```

默认：

```sql
ORDER BY changed_at ASC
```

让前端按照时间线直接展示。

返回：

```json
{
  "items": [
    {
      "from_status": null,
      "to_status": "APPLIED",
      "remark": null,
      "changed_at": "..."
    },
    {
      "from_status": "APPLIED",
      "to_status": "RESUME_PASSED",
      "remark": "收到面试通知",
      "changed_at": "..."
    }
  ]
}
```

---

# 25. Application List 基础分页

Phase 2 只实现基础分页。

暂时不实现高级搜索和复杂筛选。

Query：

```text
page
page_size
```

默认：

```text
page = 1

page_size = 20
```

最大：

```text
page_size = 100
```

返回：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

按照：

```text
application_date DESC
```

或当前 TDD 默认规则排序。

---

# 26. Repository 设计

保持：

```text
Router
 ↓
Service
 ↓
Repository
 ↓
SQLAlchemy
```

Repository 负责：

```text
数据库查询
CRUD
分页查询
owner scoped query
```

不要在 Repository 处理：

```text
HTTPException
Toast
API Response
```

---

# 27. Service 设计

Service 负责：

```text
业务规则
权限语义
事务
状态更新
重复检查
异常转换
```

例如：

```text
ApplicationService
```

至少可以具有：

```text
create_application()

get_application()

list_applications()

update_application()

delete_application()

batch_delete()

change_status()

get_status_logs()
```

具体命名遵循当前项目代码风格。

---

# 28. Router 设计

Router 只负责：

```text
请求参数
Pydantic Validation
Depends(get_current_user)
调用 Service
返回统一 Response
```

不要出现几十行 SQLAlchemy 查询逻辑。

---

# 29. 删除策略

按照当前 PRD：

```text
用户可以删除数据
```

Phase 2 默认可以采用：

```text
Hard Delete
```

如果当前 Model 已经设计：

```text
deleted_at
```

再评估是否使用 Soft Delete。

不要为了所谓“企业级”擅自引入复杂软删除体系。

删除 Application 时：

对应：

```text
ApplicationStatusLog
```

必须按照已有 FK / cascade 设计正确处理。

不能留下孤儿数据。

---

# 30. 批量删除

Request 示例：

```json
{
  "ids": [
    "uuid-1",
    "uuid-2"
  ]
}
```

要求：

只能删除：

```text
current_user
```

自己的记录。

如果传入别人的 ID：

不能删除。

建议返回实际：

```text
deleted_count
```

---

# 31. 统一错误

复用 Phase 1 已有异常体系。

至少处理：

```text
APPLICATION_NOT_FOUND

APPLICATION_CREATE_FAILED

APPLICATION_DUPLICATE

STATUS_INVALID

PERMISSION_DENIED
```

如果已有错误码体系：

优先沿用现有设计。

不要再创建第二套异常结构。

---

# 32. API Response

复用 Phase 1 已有：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

不要出现：

```text
Auth API 一套 Response

Application API 另一套 Response
```

---

# 33. Alembic

开发前检查：

```bash
python -m alembic -c alembic.ini current
```

确认：

```text
head
```

如果本阶段没有修改数据库 Schema：

不要无意义创建 migration。

如果修改了：

```text
nullable
index
foreign key
column
```

必须创建新的 Phase 2 migration。

然后真实执行：

```bash
python -m alembic -c alembic.ini upgrade head
```

---

# 34. Phase 2 后端测试

必须增加 pytest。

至少包括：

## 创建

```text
test_create_application
```

验证：

- HTTP 成功
- user_id 正确
- company_id 正确
- 初始状态正确
- 初始 status log 正确

---

## List

```text
test_list_own_applications
```

验证：

只返回当前用户数据。

---

## Detail

```text
test_get_application
```

---

## Update

```text
test_update_application
```

验证：

业务字段成功更新。

---

## Delete

```text
test_delete_application
```

---

## Batch Delete

```text
test_batch_delete_applications
```

---

# 35. 权限测试

必须有：

```text
test_user_cannot_read_other_application

test_user_cannot_update_other_application

test_user_cannot_delete_other_application

test_user_cannot_change_other_application_status

test_user_cannot_read_other_application_status_logs
```

这些属于强制测试。

---

# 36. 状态测试

至少：

```text
test_change_application_status

test_status_change_creates_log

test_status_log_from_status_correct

test_status_log_to_status_correct

test_status_log_remark_correct

test_same_status_does_not_create_duplicate_log

test_invalid_status_rejected
```

---

# 37. 事务测试

必须尽可能验证：

```text
Status update failure
        ↓
Rollback
```

不能只测试 Happy Path。

确保不存在：

```text
current_status
```

和：

```text
ApplicationStatusLog
```

不一致。

---

# 38. Phase 1 回归测试

开发完成后：

执行全部测试：

```bash
pytest -v
```

不能只执行 Phase 2 新测试。

Phase 1：

```text
Auth
Health
Infrastructure
```

相关测试必须继续通过。

---

# 39. 前端 Phase 2

Phase 2 以核心后端业务闭环为优先。

如果 PRD/TDD 和当前开发计划允许：

实现基础投递列表页面和最小新增/编辑交互。

但不要在后端 CRUD 尚未稳定之前大量开发 UI。

推荐顺序：

```text
Backend CRUD
 ↓
Backend Tests
 ↓
真实 HTTP 验证
 ↓
Frontend API Client
 ↓
基础 Application UI
```

---

# 40. 前端至少需要准备

如果本阶段实现 UI：

```text
src/api/applications.ts

src/types/application.ts

src/pages/Applications/

src/pages/ApplicationDetail/

src/components/ApplicationForm/

src/components/StatusTag/
```

具体目录遵循当前项目已有结构。

---

# 41. Application List 页面

基础展示：

```text
公司

岗位

投递类型

投递时间

当前状态

操作
```

操作：

```text
查看
编辑
删除
```

暂时不用实现：

```text
复杂过滤器
行业筛选
高级搜索
```

这些属于 Phase 3。

---

# 42. 状态更新 UI

如果 Phase 2 做前端：

详情页提供：

```text
当前状态

[更新状态]
```

用户选择新状态并可以输入：

```text
状态备注
```

提交后：

```text
PATCH status
 ↓
invalidate application
 ↓
invalidate status logs
 ↓
invalidate application list
```

---

# 43. Status Timeline

详情页可以展示：

```text
APPLIED
2026-08-20

↓

RESUME_PASSED
2026-08-23
收到一面通知

↓

FIRST_INTERVIEW
2026-08-25
一面结束
```

只做基础时间线即可。

---

# 44. TanStack Query

所有 Application 服务端数据使用：

```text
TanStack Query
```

例如 Query Keys：

```text
applications

application:{id}

application-status-logs:{id}
```

Mutation 成功后 invalidate 对应 Query。

不要把这些 API 数据放入 Zustand。

---

# 45. Zustand

Zustand 本阶段只负责：

```text
Drawer 状态

Modal 状态

必要的 UI state
```

不要负责 Applications Server State。

---

# 46. 不要提前优化

当前已知：

```text
Vite chunk ≈ 530 KB
```

只是 Warning。

Phase 2 不要为了这个 Warning：

```text
大规模重构前端
更换 UI 库
删除 Ant Design
```

等 Phase 4 Dashboard 后统一做 Code Splitting。

---

# 47. npm audit

当前存在：

```text
1 moderate
```

风险。

本阶段：

先确认来源。

如果升级属于安全的 patch/minor：

可以处理。

禁止未经分析直接：

```bash
npm audit fix --force
```

导致依赖主版本升级或项目破坏。

---

# 48. Docker 回归

Phase 2 开发结束后：

必须验证：

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

确认：

```text
frontend
backend
postgres
redis
```

仍正常。

---

# 49. 真实 API 闭环测试

除 pytest 外：

必须在真实 Docker PostgreSQL 中完成一次实际 HTTP 流程。

流程：

```text
注册 User A
    ↓
登录
    ↓
获得 JWT
    ↓
创建 Company
    ↓
创建 Application
    ↓
GET List
    ↓
GET Detail
    ↓
PUT Update
    ↓
PATCH Status
    ↓
GET Status Logs
    ↓
DELETE Application
```

再创建：

```text
User B
```

验证：

```text
User A
```

无法读取：

```text
User B Application
```

---

# 50. 数据库验证

实际检查：

```text
job_applications

application_status_logs
```

确认：

- user_id 正确；
- company_id 正确；
- current_status 正确；
- status log 正确；
- 删除不存在孤儿日志。

---

# 51. 不要伪造成功

只有真正执行过：

```text
pytest
Alembic
Docker
HTTP API
```

才能报告成功。

没有实际运行：

不能写：

```text
✅ 已验证
```

应该写：

```text
⚠️ 尚未验证
```

---

# 52. 开始开发之前必须输出

修改代码前先给出：

## 1. 当前仓库状态

包括：

```text
branch
commit
git status
```

## 2. Phase 2 需求理解

用简短文字说明。

## 3. 当前模型检查

说明：

```text
User
Company
JobApplication
ApplicationStatusLog
```

是否已经足够。

## 4. API 规划

列出准备实现的 API。

## 5. Service / Repository 规划

说明准备新增或修改哪些层。

## 6. 文件修改清单

列出预计：

```text
新增文件
修改文件
```

## 7. 测试计划

说明计划新增哪些测试。

完成以上分析后：

**直接开始执行 Phase 2，无需等待我再次确认。**

---

# 53. 开发过程中遇到问题

如果出现普通工程问题，例如：

```text
Import Error
SQLAlchemy Error
Pydantic Error
Test Failure
Docker Error
```

请自行：

```text
定位
↓
修复
↓
重新测试
```

不要每发生一个普通错误就询问用户。

只有以下情况需要停下来询问：

```text
PRD 存在重大产品歧义

需要破坏 Phase 1 已确认架构

需要删除已有用户数据

需要重大数据库不可逆迁移

需要更换核心技术栈
```

---

# 54. Phase 2 完成后复验

完成代码后执行：

```text
Backend Full Tests
        ↓
Real PostgreSQL
        ↓
Alembic
        ↓
Real HTTP API
        ↓
Authorization Test
        ↓
Frontend Build
        ↓
Docker Compose
```

---

# 55. Phase 2 最终报告

完成后输出：

# 《Phase 2 最终复验报告》

按照以下格式：

## 1. Git / Branch

✅ / ⚠️ / ❌

## 2. Database

✅ / ⚠️ / ❌

## 3. Application CRUD

✅ / ⚠️ / ❌

分别说明：

```text
Create
List
Detail
Update
Delete
Batch Delete
```

## 4. 用户数据隔离

✅ / ⚠️ / ❌

说明 User A / User B 测试结果。

## 5. Application Status

✅ / ⚠️ / ❌

## 6. Status Logs

✅ / ⚠️ / ❌

## 7. Transaction

✅ / ⚠️ / ❌

## 8. Pagination

✅ / ⚠️ / ❌

## 9. Backend Tests

给出真实：

```text
xx passed
xx failed
xx warning
```

## 10. Phase 1 Regression

✅ / ⚠️ / ❌

## 11. Real HTTP Validation

✅ / ⚠️ / ❌

## 12. Frontend

✅ / ⚠️ / ❌

## 13. Docker Compose

✅ / ⚠️ / ❌

## 14. 已修复问题

列出开发期间实际解决的问题。

## 15. 剩余 Warning / Technical Debt

明确哪些不阻塞。

## 16. Phase 2 最终结论

只能在核心验证全部通过后写：

```text
✅ Phase 2 Passed
```

---

# 56. Phase 2 完成标准

只有以下全部满足，才能宣布 Phase 2 完成：

```text
Application Create ✅

Application List ✅

Application Detail ✅

Application Update ✅

Application Delete ✅

Batch Delete ✅

JWT User Isolation ✅

Application Status Update ✅

Status Log ✅

Status Transaction ✅

Pagination ✅

pytest Full Suite ✅

Phase 1 No Regression ✅

Real PostgreSQL Validation ✅

Real HTTP Validation ✅

Frontend Build ✅

Docker Compose ✅
```

---

# 57. 完成后停止

Phase 2 完成并输出最终复验报告之后：

**停止开发。**

不要自动进入：

```text
Phase 3
```

等待我确认后再继续。

现在开始：

1. 阅读 PRD；
2. 阅读最新 TDD；
3. 检查当前代码；
4. 检查 Git；
5. 输出 Phase 2 实施计划；
6. 直接开始开发；
7. 完成后进行完整复验；
8. 输出《Phase 2 最终复验报告》。