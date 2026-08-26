# Phase 6：Local / Cloud Sync + Performance & Engineering Closure

当前项目已经完成：

```text
✅ Phase 1 Base / Auth / DB / Frontend
✅ Phase 2 Application CRUD / Status / Logs
✅ Phase 3 Search / Filter / Sort / Pagination
✅ Phase 4 Dashboard
✅ Phase 5 Company Intelligence + Kimi
```

Phase 5 已完成真实闭环验证：

```text
Kimi Web Search
→ SearchEvidence
→ Canonical Extraction
→ Reference Resolution
→ CompanyCandidate
→ Preview
→ Confirm
→ company_id
→ Application
```

当前进入：

```text
Phase 6
Local / Cloud Sync
+
Performance
+
Engineering Closure
```

这是当前 V1 最后一个开发阶段。

---

# 一、Phase 6 总目标

实现：

```text
未登录
→ 数据可以保存在浏览器本地
→ 可以正常管理自己的投递记录

登录
→ 本地数据可以安全迁移到云端账号
→ 云端数据成为登录态事实来源
→ 本地保存最近云端数据作为缓存

多设备
→ 登录同一账号
→ 从云端获得相同投递数据
```

同时完成：

```text
前端性能优化
后端性能复验
数据库查询复验
Bundle 优化
Docker / Secret / Migration / Tests 收尾
```

---

# 二、V1 产品边界

Phase 6 V1 **不是完整 Offline-First 系统**。

本阶段实现：

```text
Guest Local CRUD
+
Guest → Cloud Import
+
Cloud → Local Cache
+
Logged-in Cloud CRUD
+
Read Cache Fallback
```

本阶段不要实现：

```text
CRDT
WebSocket 实时同步
多端实时协同
Service Worker
PWA
完整离线写队列
离线 Mutation Replay
Celery / RQ
Kafka
Redis Stream
Background Sync API
```

如果发现这些能力是某个需求的必要前置条件，先报告，不得自行扩大架构。

---

# 三、进入 Phase 6 前先检查 Git

先执行：

```bash
git status
git branch --show-current
git log -5 --oneline
```

确认 Phase 5 已经完整提交。

不允许：

```text
丢弃 Phase 5 改动
reset Phase 5
reinitialize repository
```

如果 Phase 5 工作区仍有正式代码未提交：

先报告。

如果只剩明确不需要跟踪的：

```text
Prompt
临时报告
runtime 文件
```

不要误提交。

Phase 5 状态干净以后创建：

```bash
git switch -c phase6-sync-performance
```

如果分支已存在：

```text
不重复创建
```

---

# 四、第一步必须完整阅读现有实现

**不要直接写代码。**

阅读：

```text
README
PRD
TDD
Phase 1~5 文档
frontend package.json
backend pyproject.toml
docker-compose
Alembic migrations
auth store
application store/query hooks
application API client
Application list/create/edit/detail
company intelligence field
backend JobApplication model
Company model
status log model
repositories
services
API routes
tests
```

特别确认现有：

```text
JobApplication ID 类型
Company ID 类型
created_at / updated_at
JWT 登录态
logout 行为
TanStack Query cache
Zustand store
当前 LocalStorage 使用情况
IndexedDB 是否已经存在
```

不猜接口。

---

# 五、先输出《Phase 6 现状审计报告》

编码之前先报告：

```text
1. 当前未登录用户是否能进入 Application 页面
2. 当前 Application CRUD 是否全部依赖 JWT
3. 当前浏览器是否已有 IndexedDB
4. 当前 localStorage 保存哪些数据
5. JobApplication 主键类型
6. 是否有 updated_at
7. 当前 Company 创建需要哪些字段
8. 本地 Application 如何表达 Company
9. 当前 logout 是否清理 Query Cache
10. 当前前端 bundle 最大 chunk
11. 当前 1000 条 Application 查询性能
12. 当前 Dashboard 查询性能
```

如果现有代码与以下设计存在冲突：

**先报告冲突，再采用最小兼容设计，不允许强行套方案。**

---

# 六、Phase 6 数据所有权原则

必须明确三个状态。

## 6.1 Guest

未登录：

```text
IndexedDB = Source of Truth
```

用户可以：

```text
创建 Application
编辑 Application
删除 Application
修改 Status
查看 Status Timeline
搜索
筛选
排序
```

不要求联网。

## 6.2 Logged In + Online

登录并联网：

```text
PostgreSQL Cloud = Source of Truth
IndexedDB = Local Cache
```

所有正式写操作：

```text
Frontend
→ Backend API
→ PostgreSQL
```

Backend 成功后：

```text
更新 TanStack Query
+
更新 IndexedDB cache
```

不允许本地数据库绕过 Backend 修改云端事实。

## 6.3 Logged In + Network Failure

V1 至少支持：

```text
最近成功同步的数据仍可读取
```

即：

```text
Cloud request failed
↓
IndexedDB cached snapshot
↓
Read-only fallback
```

如果当前实现成本较高，可以只实现：

```text
List / Detail read fallback
```

不实现完整离线写入队列。

离线写操作应明确提示：

```text
当前网络不可用，请恢复网络后再修改
```

不伪装成已经成功同步。

---

# 七、IndexedDB 技术选择

优先检查项目现有依赖。

如果目前没有 IndexedDB abstraction：

可以引入一个**轻量级** IndexedDB wrapper。

推荐优先评估：

```text
idb
```

不要为了这一功能引入大型状态管理框架。

如果现有项目已经有合适 IndexedDB abstraction：

直接复用。

在修改依赖前先报告：

```text
current dependency
proposed dependency
package size / purpose
why needed
```

---

# 八、本地数据库 Schema

不要直接把 React Component state 当本地数据库。

建立独立：

```text
local-db
```

abstraction。

推荐至少：

```text
applications
status_logs
sync_metadata
```

是否单独缓存 companies：

根据现有 frontend domain model 判断。

## LocalApplication

必须拥有稳定：

```text
local_id: UUID
```

并保留：

```text
company
job_title
application_type
application_date
channel
resume_version
note
status
created_at
updated_at
```

具体字段名必须复用现有前端 Domain Type。

不创建第二套含义不同的 Application Model。

---

# 九、Guest StatusLog

Guest 模式也必须遵守 Phase 2 的业务原则：

```text
每次 status change
↓
old_status
new_status
timestamp
remark
```

初始 Application 创建也应该有初始状态记录。

不允许 Guest Mode 退化成：

```text
只有 current_status，没有 timeline
```

---

# 十、Guest CRUD 与 Cloud CRUD 共享 UI

不允许复制：

```text
GuestApplicationPage
CloudApplicationPage
```

两套页面。

UI 应继续使用当前：

```text
Application List
Create
Edit
Detail
Timeline
```

在 Data Access 层决定：

```text
guest
→ LocalApplicationRepository

logged in
→ CloudApplicationRepository
```

推荐抽象：

```text
ApplicationDataSource
```

或现有项目风格的等价接口。

不要过度设计 Repository Framework。

---

# 十一、Guest → Login 数据迁移

这是 Phase 6 核心。

当：

```text
Guest IndexedDB 存在 Application
+
用户完成登录
```

不能静默丢掉 Guest 数据。

登录后检测：

```text
guest application count > 0
```

给用户明确选择：

```text
将本地投递记录同步到当前账号
```

推荐 UI：

```text
检测到 X 条本地投递记录

[同步到账号]
[暂不同步]
```

不要自动无提示写入云端。

---

# 十二、Import 必须具备幂等性

用户可能：

```text
点击后网络重试
浏览器刷新
请求超时
重复登录
```

不能产生重复 Application。

每条 Guest Application 必须有稳定：

```text
local_id
```

Cloud Import 应保存等价：

```text
client_sync_id
```

名称可以根据当前项目命名规范调整。

Backend 唯一约束：

```text
(user_id, client_sync_id)
UNIQUE
```

如果数据库设计证明已有等价字段：

直接复用。

不重复创建。

---

# 十三、数据库 Migration

如果确实需要：

```text
client_sync_id
```

新增 Alembic migration。

Migration 编号必须基于现有 Alembic 实际 head 自动确定，不要硬编码示例编号。

字段建议：

```text
nullable=true
```

因为已有云端 Application 没有 client sync id。

唯一索引：

```text
user_id + client_sync_id
```

只对非 null 值生效或使用 PostgreSQL 合适的唯一约束语义。

先确认 PostgreSQL 当前版本。

---

# 十四、Import API

优先使用专用 endpoint，不要循环调用几十次普通 Create API。

推荐：

```text
POST /api/v1/sync/import-applications
```

或遵循现有 router 命名。

Request：

```text
applications[]
```

每条必须携带：

```text
client_sync_id
application fields
status history
local company data
```

具体 schema 必须根据现有 Domain 定义。

---

# 十五、Import 不信任客户端身份信息

禁止客户端提交：

```text
user_id
```

Backend 永远：

```text
current_user.id
```

决定 Owner。

与 Phase 2 保持一致。

---

# 十六、Import Company 处理原则

Guest 本地数据可能只有：

```text
company name
```

或用户手工填写的 Company 信息。

Import 时：

1. 优先复用现有 Company；
2. 可根据当前 Company/Alias normalization 查询；
3. 没有则创建最小合法 Company；
4. 不调用 Kimi；
5. 不因为 Import 自动触发 Company Intelligence；
6. 不把用户本地数据标成 VERIFIED。

如果复用已有：

```text
不覆盖已有可靠 Company 字段
```

---

# 十七、Import StatusLog

Import 不能只导入 current status。

如果 Guest 存在：

```text
status history
```

应保留合理历史。

同时必须防止：

```text
Import
→ 自动创建一条初始状态日志
→ 再导入本地日志
→ 产生重复日志
```

请基于现有 Application create/status service 设计明确规则。

推荐：

```text
Import Service 作为独立业务流程
```

在单事务中：

```text
Application
+
StatusLogs
```

创建。

不要为了复用普通 Create API 制造重复 StatusLog。

---

# 十八、Import Transaction

单个 Application：

```text
Company resolve
→ Application
→ StatusLogs
```

必须事务一致。

Batch 是否：

```text
all-or-nothing
```

不强制。

V1 推荐：

```text
per-item atomic
+
batch result
```

即某一条失败：

```text
不影响其他合法记录导入
```

Response 返回：

```text
imported
reused
failed
mappings
```

---

# 十九、Import ID Mapping

Backend 成功后返回：

```text
client_sync_id
→ cloud_application_id
```

Frontend 使用 mapping 更新 IndexedDB。

不允许前端猜 cloud ID。

---

# 二十、成功迁移后的 Guest 数据

Import 全部成功后：

不建议立即物理删除所有本地数据。

应先：

```text
写入 sync metadata
↓
确认 cloud snapshot 拉取成功
↓
再清理 guest namespace
```

防止：

```text
Backend import 成功
↓
Browser 在本地清理过程中崩溃
```

导致状态不一致。

如果再次触发 Import：

后端依赖：

```text
client_sync_id
```

保证幂等。

---

# 二十一、暂不同步

用户点击：

```text
暂不同步
```

不删除 Guest 数据。

云端模式正常使用当前账号数据。

下次合理入口仍允许：

```text
导入本地记录
```

但不要每次页面刷新都弹窗骚扰用户。

可以保存：

```text
dismissed_at
```

或简单的 session-level dismissal。

不需要复杂通知系统。

---

# 二十二、Logout 行为

Logout 时：

必须避免上一用户的数据出现在下一用户界面。

至少：

```text
清除 JWT
清除当前用户 TanStack Query Cache
清除 Zustand user-scoped state
```

IndexedDB 中 cloud cache 应按：

```text
user_id namespace
```

隔离。

不允许：

```text
User A logout
↓
User B login
↓
短暂看到 User A Applications
```

---

# 二十三、本地数据命名空间

IndexedDB 至少区分：

```text
guest
cloud:<user_id>
```

如果出于隐私考虑不希望明文存 user id：

可以使用稳定的内部 namespace key。

不需要加密数据库主键。

不把：

```text
access token
password
Kimi API Key
```

放入 IndexedDB。

---

# 二十四、Cloud → Local Cache

Logged-in 模式成功获取：

```text
Application List
```

后：

```text
更新对应 user namespace 的 IndexedDB snapshot
```

Detail / StatusLogs 根据当前数据模型决定是否：

```text
一并缓存
```

优先保证：

```text
Application List
Application Detail
```

可以读取最近缓存。

---

# 二十五、缓存不能污染云端事实

Cloud 模式：

```text
API Response
→ Cloud truth
```

IndexedDB 只能：

```text
cache / fallback
```

不能：

```text
IndexedDB 比 API 新
→ 自动覆盖 PostgreSQL
```

除了明确的：

```text
Guest Import
```

流程。

---

# 二十六、跨设备同步

V1 不需要 WebSocket。

多设备一致性通过：

```text
Device A
→ Backend PostgreSQL

Device B
→ refresh / refetch
→ Backend PostgreSQL
```

实现。

TanStack Query：

```text
staleTime
refetchOnWindowFocus
invalidation
```

根据现有项目设置合理配置。

不要设置极端：

```text
staleTime = Infinity
```

导致长期看不到另一设备更新。

---

# 二十七、云端 Mutation 后 Cache 一致性

创建：

```text
invalidate application list
invalidate dashboard
update local cache
```

修改：

```text
invalidate detail
invalidate list
invalidate dashboard
update local cache
```

状态修改：

```text
invalidate status logs
invalidate detail
invalidate list
invalidate dashboard
update local cache
```

删除：

```text
remove local cache record
invalidate list/dashboard
```

不允许：

```text
API 已成功
但 Dashboard 长期展示旧数据
```

---

# 二十八、Dashboard Guest Mode

Guest 本地数据也应该可以得到基础 Dashboard。

不调用后端聚合。

在前端对本地 Applications 计算：

```text
total
in_progress
offers
pass rate
offer rate
rejection rate
status distribution
industry distribution
nature distribution
trend
```

算法定义必须与 Phase 4 Backend Dashboard 尽可能保持一致。

**不要复制两套不同业务公式。**

推荐抽取共享：

```text
dashboard metric definitions
```

如果后端和前端无法共享代码：

用契约测试保证公式一致。

---

# 二十九、Guest Search / Filter / Sort

Guest Mode 要支持 Phase 3 已有：

```text
search
filters
sorting
pagination
```

行为语义应与 Cloud 尽量一致。

重点测试：

```text
company
job title
industry
company nature
note
```

过滤：

```text
status
nature
application type
industry
time
size
```

不需要在浏览器实现 pg_trgm。

普通 normalized substring search 即可。

---

# 三十、Guest Company Intelligence

未登录用户是否允许真实 Kimi 搜索：

**V1 默认不允许。**

原因：

```text
Kimi API Key 只能存在 Backend
Company Intelligence endpoint JWT Protected
Rate limit 按用户
```

Guest 用户可以：

```text
手工填写 Company
```

UI 明确提示：

```text
登录后可使用企业信息智能获取
```

不要为了 Guest Kimi 引入匿名 API 滥用风险。

---

# 三十一、前端性能优化：先测量

不允许看到：

```text
bundle warning
```

就盲目重构。

先记录：

```text
npm build 输出
chunk names
raw size
gzip size
```

输出：

```text
《Frontend Performance Baseline》
```

---

# 三十二、路由级 Code Splitting

检查：

```text
Dashboard
Company Intelligence
Application Detail
Auth Pages
```

是否已经 route lazy load。

对大型非首屏模块：

```text
React.lazy
dynamic import
```

优先。

不要把非常小的组件切成几十个 chunk。

---

# 三十三、ECharts 优化

当前存在 bundle-size warning。

检查是否：

```text
import * as echarts from "echarts"
```

导致全量 ECharts 进入 bundle。

如果是：

优先评估：

```text
echarts/core
```

按需注册实际使用的：

```text
charts
components
renderer
```

必须保持 Dashboard 图表全部正常。

先写/保留测试。

不为了 bundle 大改 Dashboard UX。

---

# 三十四、Ant Design

检查当前 Vite tree shaking 实际结果。

不使用旧时代的：

```text
babel-plugin-import
```

除非当前版本确实需要。

不做没有测量证据的依赖替换。

---

# 三十五、TanStack Query

检查：

```text
duplicate requests
unnecessary refetch
staleTime
query keys
invalidation scope
```

尤其：

```text
Dashboard filters
Application List filters
```

不因为 key 不稳定导致重复请求。

Query Key 使用稳定 serializable params。

---

# 三十六、React Rendering

使用 React Profiler 或测试可观测数据定位：

```text
大列表
Filters
Dashboard
Company Intelligence Field
```

是否存在明显无意义 rerender。

只有存在证据时再使用：

```text
useMemo
useCallback
memo
```

不做“为了优化而优化”。

---

# 三十七、Application List

当前设计已有 Backend Pagination。

因此 1000+ records：

```text
不需要一次渲染 1000 条
```

不要无理由引入：

```text
react-window
virtualization
```

除非测量证明当前分页内部仍存在明显问题。

---

# 三十八、Backend Performance Baseline

使用专门测试用户创建至少：

```text
1000 Applications
```

覆盖：

```text
mixed statuses
industries
company natures
application types
dates
notes
```

测试：

```text
application list
search
multiple filters
sort
dashboard summary
status distribution
industry distribution
nature distribution
trend
```

---

# 三十九、性能指标

按原 PRD：

```text
Application List / Chart <= 0.8s
First Load target <= 1.5s
1000+ Applications / User
```

Company Intelligence 已单独调整为：

```text
<= 60s max synchronous budget
```

不允许把 Company Intelligence 的 60s 与普通 API 指标混在一起。

---

# 四十、性能测试要区分环境

必须记录：

```text
Docker / Host
cold / warm
DB data count
endpoint
latency
```

不允许仅凭一次：

```text
curl 120ms
```

就宣称全系统满足 0.8s。

每个核心接口至少进行：

```text
多次 warm measurement
```

报告：

```text
median
p95
```

如果工具成本太高：

至少：

```text
min / avg / max
```

---

# 四十一、数据库 SQL 优化

如果某 API 超标：

先：

```text
EXPLAIN ANALYZE
```

再决定是否：

```text
index
query rewrite
eager loading
aggregation optimization
```

不允许看到慢：

```text
→ 直接加 Redis
```

已有：

```text
pg_trgm
GIN
Phase 3 indexes
```

先确认是否实际命中。

---

# 四十二、N+1

特别检查：

```text
Application List → Company
Application Detail → StatusLogs
Company Confirm → Relationships
```

禁止 Async SQLAlchemy 隐式 lazy load。

Phase 5 已经发生过：

```text
MissingGreenlet
```

Phase 6 应顺带做一次 N+1 / implicit IO 审计。

但只修：

```text
实际发现的问题
```

不全局修改 relationship loading strategy。

---

# 四十三、Redis

Redis 保持用于：

```text
Company Intelligence Cache
Distributed Lock
Rate Limit
```

不要为了普通 Application List 强制引入 Redis Cache。

PostgreSQL 查询能满足：

```text
<= 0.8s
```

就不要增加缓存失效复杂度。

---

# 四十四、Auth / Security 回归

Phase 6 必须重新验证：

```text
User A cannot read User B Application
User A cannot update User B Application
User A cannot delete User B Application
User A cannot view User B sync data
User A client_sync_id does not conflict with User B
```

Import endpoint 同样：

```text
JWT protected
```

---

# 四十五、恶意 Import Payload

Backend 不信任 IndexedDB。

浏览器数据可能被人为修改。

Import 仍需：

```text
Pydantic validation
enum validation
max length
date validation
ownership isolation
```

不因为数据“来自自己的浏览器”就跳过校验。

---

# 四十六、Import 数量限制

防止一次请求几万条数据。

根据正常求职场景设置合理 batch size。

推荐初步评估：

```text
100~500 / batch
```

具体值结合 API payload 和测试确定。

如果超过：

```text
frontend chunk import
```

不需要后台 Worker。

---

# 四十七、数据同步错误 UX

必须区分：

```text
全部成功
部分成功
全部失败
```

示例：

```text
已同步 24 条投递记录
2 条记录需要手动处理
```

不展示：

```text
SQLAlchemy exception
stack trace
DB constraint
```

---

# 四十八、用户永远可以继续使用核心功能

如果 Guest Import：

```text
failed
```

不允许：

```text
锁死整个应用
```

用户仍然可以：

```text
进入云端账号
查看云端数据
稍后重新导入
```

Guest 数据继续保留。

---

# 四十九、本地数据库版本升级

IndexedDB schema 必须定义版本。

例如：

```text
DB_VERSION = 1
```

后续升级保留 migration path。

不要每次 schema 改动：

```text
deleteDatabase()
```

用户本地投递数据不能因前端升级丢失。

---

# 五十、IndexedDB Failure

如果：

```text
browser private mode
quota exceeded
IndexedDB unavailable
```

前端应安全提示：

```text
本地存储暂不可用
```

不崩整个应用。

登录用户仍然可以依赖云端。

Guest 无法持久化时必须明确提醒用户。

---

# 五十一、测试策略必须 TDD

每个业务修改：

```text
RED
→ failing test
→ minimal implementation
→ GREEN
→ regression
```

不允许：

```text
代码全写完
→ 最后补测试
```

---

# 五十二、Backend Sync Tests

至少：

```text
test_import_guest_application
test_import_preserves_owner
test_import_is_idempotent
test_same_client_sync_id_different_users_allowed
test_duplicate_import_does_not_duplicate_application
test_import_status_history
test_import_does_not_duplicate_initial_status_log
test_import_reuses_company
test_import_does_not_overwrite_existing_company
test_partial_batch_failure
test_import_user_isolation
test_import_rejects_client_user_id
test_import_invalid_payload
```

---

# 五十三、Frontend Local DB Tests

至少：

```text
guest create application
guest edit application
guest delete application
guest status update
guest status timeline
guest data survives repository reload
guest search/filter/sort
local DB error handling
```

测试环境可以使用：

```text
fake-indexeddb
```

如果确实需要。

引入前说明用途。

---

# 五十四、Frontend Sync Tests

至少：

```text
login detects guest data
import dialog shows correct count
cancel/dismiss preserves guest data
successful import stores cloud mappings
failed import preserves local records
retry import is idempotent
logout clears user-scoped query state
second user cannot see first user's cache
cloud fetch updates local snapshot
offline read uses cached snapshot
```

---

# 五十五、Dashboard Guest Tests

至少验证：

```text
total
in-progress
offer
rejection
status distribution
trend
filters
```

和 Backend Dashboard 语义保持一致。

---

# 五十六、Performance Regression Tests

不建议写：

```text
assert latency < 0.8s
```

到普通 CI unit test。

CI 环境不稳定。

使用：

```text
benchmark script
integration benchmark
```

单独输出报告。

Unit Test 关注：

```text
query correctness
query count
pagination
no N+1
```

---

# 五十七、Frontend 初始加载

PRD：

```text
first load <= 1.5s
```

这是环境相关指标。

不能仅根据 build success 宣称满足。

至少记录：

```text
production build
initial JS size
gzip size
route chunks
local Docker browser measurement（如果当前工具支持）
```

如果无法可靠测 First Content：

明确：

```text
Not independently verified
```

不造数字。

---

# 五十八、Phase 6 不修改 Kimi

Phase 5 已 Passed。

除非 Phase 6 regression 发现确定 bug：

不修改：

```text
Kimi Web Search
Stage A
Stage B
Reference Contract
Mapper
CandidateVerifier
60s SLA
```

更不能重新调用 Kimi 做无关测试。

Company Intelligence 只跑：

```text
Mock / Regression
```

即可。

---

# 五十九、环境与 Docker

保持：

```text
PostgreSQL data:
E:\qiuzhao\.runtime\postgres

Redis data:
E:\qiuzhao\.runtime\redis

Docker Desktop data:
E:\qiuzhao\.docker-data\DockerDesktopWSL
```

不改变到 C 盘。

禁止：

```bash
docker compose down -v
```

不删除 volumes。

---

# 六十、Secret

Phase 6 最终检查：

```text
.env
API keys
JWT secrets
passwords
Docker runtime
IndexedDB dumps
benchmark credentials
```

不能进入 Git。

`.env.example`：

```text
只保留 placeholder
```

---

# 六十一、文档

更新：

```text
README
PRD
TDD
Phase 6 implementation notes
```

至少说明：

```text
Guest Mode
Local Storage
Login Sync
Import idempotency
Cloud source of truth
Offline read fallback
V1 limitations
Performance results
```

---

# 六十二、明确写 V1 Sync Limitations

文档写清：

```text
1. Guest 数据保存在当前浏览器。
2. 登录后可导入至云端。
3. 登录用户的正式数据以云端为准。
4. IndexedDB 是缓存，不是第二个云端事实源。
5. V1 支持缓存读取降级。
6. V1 不支持完整离线编辑后自动回放。
7. 多设备通过云端重新拉取同步，不是实时 WebSocket。
```

---

# 六十三、推荐实现顺序

严格按顺序：

```text
Task 1
Local DB abstraction

Task 2
Guest Application CRUD + StatusLog

Task 3
Guest Search / Filter / Dashboard

Task 4
Backend idempotent Import API

Task 5
Login transition + Import UX

Task 6
Cloud → IndexedDB Cache

Task 7
Logout/User Cache Isolation

Task 8
Offline Read Fallback

Task 9
Frontend Performance Optimization

Task 10
Backend / DB Performance Benchmark

Task 11
Security / Regression / Docker

Task 12
Documentation + Final Acceptance
```

不要同时大范围修改所有模块。

---

# 六十四、每个 Task 的执行规则

每个任务：

```text
阅读相关代码
↓
写 failing test
↓
确认 RED
↓
最小实现
↓
GREEN
↓
Targeted regression
↓
git diff --check
```

每个独立 Task 可以形成独立 commit。

Commit 示例：

```text
feat: add local application storage

feat: add guest application workflow

feat: add idempotent guest data import

feat: add cloud application cache

perf: reduce frontend initial bundle

perf: optimize application queries
```

不允许：

```text
一个 commit 混合全部 Phase 6
```

---

# 六十五、不要自动提交这些文件

不要使用：

```bash
git add .
```

在每次 commit 前：

```bash
git status --short
```

精确 `git add`。

不提交：

```text
Prompt/
.env
runtime/
node_modules/
.venv/
benchmark temp files
local DB dump
API response dump
```

除非仓库原本明确要求某文档被跟踪。

---

# 六十六、Phase 6 最终自动化验证

最终必须：

```text
Backend full pytest
Backend Ruff
Frontend full tests
Frontend production build
git diff --check
Alembic current
Alembic heads
Docker Compose
/health
Frontend HTTP
Redis PONG
```

如果全仓 Ruff 仍存在 Phase 6 之前已经存在的历史问题：

```text
区分 Existing vs New
```

Phase 6 新代码：

```text
0 new Ruff violations
```

不为了追求全仓 0 warning 做无关重构。

---

# 六十七、同步最终人工验收

至少执行以下真实本地流程。

## Scenario A：纯 Guest

```text
Logout
↓
Create 3 local Applications
↓
修改一个 Status
↓
Edit 一个
↓
Search / Filter
↓
Dashboard
↓
Refresh Browser
↓
3 条数据仍存在
```

## Scenario B：Guest → Login

```text
Guest 有 3 条
↓
Login
↓
检测 3 条本地数据
↓
Import
↓
Cloud 创建/复用
↓
返回 mappings
↓
再请求 Application List
↓
数据存在
```

## Scenario C：Import Retry

对同一批：

```text
client_sync_id
```

再 Import。

应：

```text
0 duplicate Applications
```

## Scenario D：User Isolation

```text
User A login
↓
cache data
↓
logout
↓
User B login
```

User B：

```text
不能看到 User A Cloud Cache
```

## Scenario E：Multi-device Semantics

不要求真实两台机器。

可以使用：

```text
两个独立 browser context / API session
```

User 在 Context A 创建 Application。

Context B refetch 后：

```text
能看到该 Application
```

## Scenario F：Network Failure

在已有 Cloud cache 后模拟：

```text
Application List request network failure
```

页面：

```text
显示最近缓存
+
明确 offline/stale 提示
```

不把 cache 伪装成刚从服务器获取的数据。

---

# 六十八、Performance Final Acceptance

使用 1000+ 测试记录。

输出表：

```text
Endpoint
Dataset Size
Runs
Median
P95 / Max
Target
Result
```

至少：

```text
Application list
Search
Multi-filter
Dashboard summary
Dashboard distributions
Trend
```

测试结束：

**只删除明确的性能测试数据。**

不删除用户真实数据。

---

# 六十九、Frontend Performance Final Report

输出 Before / After：

```text
Initial chunk
Dashboard chunk
ECharts-related chunk
Total production JS
gzip
```

如果无法可靠获得某项：

写：

```text
N/A / not reliably measurable
```

不猜。

---

# 七十、最终技术债务

Phase 6 不要求技术债务为 0。

分类：

```text
Blocker
Non-blocking
Future V2
```

例如：

```text
Full offline mutation queue → V2
PWA → V2
Real-time multi-device sync → V2
Company Intelligence async worker → V2
```

不把 Future V2 当 Phase 6 失败。

---

# 七十一、最终验收标准

必须达到：

```text
Guest Local CRUD                ✅
Guest Persistence               ✅
Guest Status Timeline           ✅
Guest Search / Filter           ✅
Guest Dashboard                 ✅

Guest → Cloud Import            ✅
Import Idempotency              ✅
Company Resolution              ✅
Status History Import           ✅
Partial Failure                 ✅

Cloud Source of Truth           ✅
Cloud → Local Cache             ✅
User Cache Isolation            ✅
Logout Isolation                ✅
Offline Read Fallback           ✅

Cross-device Refetch            ✅

1000+ Data Support              ✅
List Performance                ✅
Dashboard Performance           ✅

Backend Regression              ✅
Frontend Regression             ✅
Docker                          ✅
Migration                       ✅
Security                        ✅
Secret Check                    ✅
Documentation                   ✅
```

---

# 七十二、Phase 6 Passed 判定

只有完整验证后才能：

```text
✅ Phase 6 Passed
```

如果 Local/Cloud Sync 核心闭环没有通过：

```text
⚠️ Phase 6 implementation incomplete
```

如果只是：

```text
bundle warning
third-party deprecation warning
V2 offline mutation queue 未实现
```

且不影响 V1 验收：

记录为：

```text
Non-blocking Technical Debt
```

不阻塞 Phase 6 Passed。

---

# 七十三、最终输出

完成后输出：

# 《Phase 6 最终验收报告》

格式至少包括：

```text
1. Git / Branch / HEAD
2. Architecture
3. IndexedDB Schema
4. Guest CRUD
5. Guest Dashboard
6. Import API
7. Import Idempotency
8. Status History Migration
9. User Isolation
10. Cloud Cache
11. Offline Fallback
12. Multi-device Verification
13. Frontend Performance Before / After
14. Backend Benchmark
15. Tests
16. Ruff
17. Frontend Build
18. Docker
19. Alembic
20. Secret Check
21. Remaining Technical Debt
```

最后只能根据证据给出：

```text
✅ Phase 6 Passed
```

或：

```text
⚠️ Phase 6 未通过
```

不得虚报。

---

# 七十四、停止条件

Phase 6 Passed 后：

```text
停止开发
```

不自行继续：

```text
Phase 7
新功能
UI 重构
PWA
Export
Reminder
AI Resume
更多 Agent
```

Phase 6 是当前 V1 的工程封板阶段。
