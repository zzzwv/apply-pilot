# Phase 4 Codex 开发任务

## 1. 项目背景

你正在继续开发：

**秋招/实习投递状态管理 Web 网站**

项目目录：

```text
E:\qiuzhao
```

当前项目已经完成并真实复验通过：

```text
Phase 1
├── FastAPI
├── React + TypeScript + Vite
├── PostgreSQL
├── Redis
├── Alembic
├── Docker Compose
├── JWT Authentication
└── 基础工程设施

Phase 2
├── JobApplication CRUD
├── ApplicationStatus
├── ApplicationStatusLog
├── 用户数据隔离
├── 基础分页
└── 基础投递管理前端

Phase 3
├── Keyword Search
├── 多条件筛选
├── 排序
├── 分页增强
├── pg_trgm
├── 5 个 GIN 索引
├── 前端 300ms debounce
└── 搜索筛选 UI
```

Phase 3 最终验证：

```text
Backend tests: 38 passed

Frontend tests: 5 passed

Alembic:
20260825_0002 (head)

PostgreSQL:
pg_trgm ✅
5 个 trigram GIN indexes ✅

Docker Compose ✅

真实 HTTP 搜索/筛选/排序 ✅

数据持久化 ✅
```

Phase 3 关键提交：

```text
0db8bf1 feat: add application search filters and sorting

65bb551 fix: stabilize backend docker dependency build
```

因此：

**禁止重新实现 Phase 1 / Phase 2 / Phase 3。**

---

# 2. 开发依据

开始开发前必须完整阅读：

```text
docs/PRD.md
docs/TDD.md
```

如果文件名称不同，请从：

```text
docs/
```

中找到：

- 最新 PRD；
- 最新 TDD。

当前最新 TDD：

**Kimi 联网搜索增强版**

但是：

# Phase 4 不实现 Kimi

本阶段只完成：

```text
Dashboard
+
Analytics
+
Charts
+
筛选联动
```

禁止提前开发：

```text
Kimi 2.5
Company Intelligence
企业联网搜索
官网招聘入口发现
招聘 JD 抽取
```

---

# 3. 当前阶段

正式进入：

# Phase 4：Dashboard 数据看板

本阶段目标：

```text
用户投递数据
      ↓
后端统一筛选
      ↓
SQL Aggregate
      ↓
Analytics Service
      ↓
Dashboard APIs
      ↓
React Dashboard
      ↓
ECharts
      ↓
筛选联动
```

最终用户可以直观看到：

```text
总投递数

进行中数量

Offer 数量

面试通过率

Offer 获取率

淘汰率

投递状态分布

行业投递分布

企业性质分布

时间投递趋势
```

---

# 4. Phase 4 核心原则

本阶段必须遵守以下原则。

## 4.1 后端统计

禁止：

```text
GET 所有 applications
       ↓
前端 JavaScript reduce()
       ↓
计算 Dashboard
```

必须：

```text
PostgreSQL
    ↓
COUNT / GROUP BY / Aggregate
    ↓
Dashboard API
```

---

## 4.2 复用 Phase 3 Filter

Phase 3 已经完成：

```text
ApplicationFilterParams
```

或项目中对应的统一筛选 DTO。

Phase 4：

**不得重新创建另一套 DashboardFilterParams，除非现有 Filter DTO 确实无法扩展。**

优先：

```text
ApplicationFilterParams
        ↓
Application List

ApplicationFilterParams
        ↓
Dashboard Analytics
```

确保：

```text
列表统计口径
=
Dashboard统计口径
```

---

# 5. 当前阶段禁止实现

Phase 4 暂时不要开发：

```text
Kimi

Company Intelligence

企业自动抓取

官网识别

官方招聘入口发现

招聘信息抓取

Link Validator 完整业务

Celery

IndexedDB 云同步

多端同步

AI 推荐

岗位匹配

简历分析

Excel 导出

PDF 导出
```

不要扩大本阶段范围。

---

# 6. Git 检查

开始前执行：

```bash
git status
git branch --show-current
git log --oneline --decorate -5
```

当前应位于：

```text
phase4-dashboard
```

如果还在：

```text
phase3-search-filter
```

并且 Phase 3 已经完整提交，则：

```bash
git switch -c phase4-dashboard
```

不要删除旧分支。

---

# 7. 当前未跟踪 Prompt 文件

项目可能存在：

```text
Prompt/Phase 3 .md
```

等未跟踪任务说明文件。

不要擅自：

```text
删除
修改
提交
```

除非用户明确要求。

这些文件不是 Phase 4 产品代码。

---

# 8. 开发前阅读现有代码

重点检查：

```text
backend/app/models/
backend/app/repositories/
backend/app/services/
backend/app/api/
backend/app/schemas/

backend/tests/

frontend/src/api/
frontend/src/pages/
frontend/src/components/
frontend/src/types/
frontend/src/store/
frontend/src/hooks/
```

尤其分析：

```text
ApplicationFilterParams

ApplicationRepository

ApplicationService

JobApplication

Company

ApplicationStatus

StatusMetadata

现有 Application List API

现有前端 Filter Panel
```

Phase 4 必须复用 Phase 3 已经验证过的筛选规则。

---

# 9. Dashboard 核心指标

必须实现：

```text
total

in_progress

offer_count

interview_rate

offer_rate

rejection_rate
```

推荐 Response：

```json
{
  "total": 125,
  "in_progress": 22,
  "offer_count": 4,
  "interview_rate": 0.28,
  "offer_rate": 0.032,
  "rejection_rate": 0.41
}
```

具体统一 Response 外层继续复用现有项目格式。

---

# 10. 总投递数定义

`total`：

当前用户经过全部 Dashboard 筛选后：

```text
JobApplication
```

记录总数。

必须：

```text
WHERE user_id = current_user.id
```

然后再应用：

```text
keyword
status
company_nature
application_type
industry
date_from
date_to
company_size
```

等筛选条件。

---

# 11. 进行中数量定义

PRD 中进行中对应：

```text
简历通过/待面试
各轮面试
HR 面
谈薪
```

因此建议复用现有 StatusMetadata / StatusCategory。

如果 Phase 1~3 已经存在：

```text
IN_PROGRESS
```

状态分类：

直接复用。

不要新建：

```text
if status in [...]
```

第二套硬编码状态集合，除非当前项目不存在状态元数据。

---

# 12. Offer 数量

按照 TDD：

```text
offer_count =
OFFER_RECEIVED
+
SIGNED
```

注意：

如果：

```text
SIGNED
```

是 Offer 后进一步状态，则不能因当前状态变为 SIGNED 而从 Offer 成果中消失。

所以：

```text
OFFER_RECEIVED
SIGNED
```

均计入成功 Offer。

---

# 13. Offer 获取率

默认：

```text
offer_rate =
(OFFER_RECEIVED + SIGNED)
/
total
```

当：

```text
total = 0
```

必须返回：

```text
0
```

禁止：

```text
NaN
Infinity
数据库除零异常
```

---

# 14. 淘汰率

根据 PRD：

```text
RESUME_REJECTED

INTERVIEW_REJECTED

PROCESS_TERMINATED
```

计入失败结果。

推荐：

```text
rejection_rate =
failed_count
/
total
```

`OFFER_REJECTED`：

属于用户主动拒绝。

不要自动计入企业淘汰率。

应复用：

```text
USER_TERMINATED
```

与：

```text
FAILED
```

的现有状态分类。

---

# 15. 面试通过率

这是 Phase 4 最需要明确统计口径的指标之一。

PRD 中出现：

```text
面试通过率
```

但现有 TDD 没有完全确定公式。

因此：

开发前先检查当前 PRD/TDD 是否已有更明确口径。

如果仍没有：

不要擅自设计复杂业务统计。

Phase 4 推荐采用一个稳定且容易解释的 V1 口径：

```text
进入过面试后续有效阶段的记录数
/
进入面试流程的记录数
```

但由于当前数据库主要保存：

```text
current_status
+
status logs
```

不能仅依赖当前状态判断所有历史行为。

优先从：

```text
ApplicationStatusLog
```

统计。

如果该定义会显著增加复杂度或存在产品歧义：

在开始编码前明确报告这个唯一统计口径问题。

除该问题外，不要频繁向用户提问。

---

# 16. 推荐的面试统计方式

如果没有更明确产品定义，推荐：

`interview_started_count`：

状态历史中曾进入：

```text
FIRST_INTERVIEW
SECOND_INTERVIEW
FINAL_INTERVIEW
HR_INTERVIEW
SALARY_NEGOTIATION
OFFER_RECEIVED
OFFER_REJECTED
SIGNED
INTERVIEW_REJECTED
```

的 Application 数量。

`interview_passed_count`：

状态历史中曾进入：

```text
SECOND_INTERVIEW
FINAL_INTERVIEW
HR_INTERVIEW
SALARY_NEGOTIATION
OFFER_RECEIVED
OFFER_REJECTED
SIGNED
```

的 Application 数量。

然后：

```text
interview_rate =
interview_passed_count
/
interview_started_count
```

如果：

```text
interview_started_count = 0
```

返回：

```text
0
```

注意：

按：

```text
DISTINCT application_id
```

计算，不能因为一条 Application 有多个状态日志被重复统计。

---

# 17. Dashboard Summary API

实现：

```http
GET /api/v1/dashboard/summary
```

支持 Phase 3 相同筛选参数。

例如：

```http
GET /api/v1/dashboard/summary
?application_type=AUTUMN_FULLTIME
&industry=人工智能
&date_from=2026-08-01
&date_to=2026-08-31
```

---

# 18. 状态分布

实现：

```http
GET /api/v1/dashboard/status-distribution
```

返回示例：

```json
{
  "items": [
    {
      "status": "APPLIED",
      "count": 20,
      "percentage": 0.25
    },
    {
      "status": "FIRST_INTERVIEW",
      "count": 8,
      "percentage": 0.10
    }
  ]
}
```

必须基于：

```text
current_status
```

统计当前流程分布。

不是根据 Status Logs 所有历史状态统计。

---

# 19. 状态分布百分比

计算：

```text
status count
/
filtered total
```

如果：

```text
filtered total = 0
```

percentage：

```text
0
```

---

# 20. 行业分布

实现：

```http
GET /api/v1/dashboard/industry-distribution
```

基于：

```text
JobApplication
JOIN Company
```

统计：

```text
Company.industry
```

返回：

```json
{
  "items": [
    {
      "industry": "人工智能",
      "count": 18,
      "percentage": 0.30
    }
  ]
}
```

对于：

```text
NULL
空字符串
```

行业：

推荐统一归为：

```text
UNKNOWN
```

或者：

```text
未分类
```

前端展示文案可以是：

```text
未分类
```

但 API 是否返回 `null` 或特殊值，应保持项目整体规范。

不要擅自把缺失行业记录丢掉，导致 total 对不上。

---

# 21. 企业性质分布

实现：

```http
GET /api/v1/dashboard/company-nature-distribution
```

统计：

```text
Company.nature
```

返回：

```json
{
  "items": [
    {
      "company_nature": "STATE_OWNED",
      "count": 15,
      "percentage": 0.25
    }
  ]
}
```

前端负责将 Enum 转为中文。

后端不要直接返回：

```text
国企
私企
```

如果当前 API 架构一直使用稳定枚举值。

---

# 22. 时间投递趋势

实现：

```http
GET /api/v1/dashboard/application-trend
```

支持：

```text
day
week
```

聚合粒度。

建议参数：

```text
granularity=day
granularity=week
```

默认：

```text
day
```

---

# 23. Day Trend

使用：

```text
application_date
```

按日期聚合：

```text
2026-08-01  5
2026-08-02  3
2026-08-03  8
```

---

# 24. Week Trend

PostgreSQL：

优先使用：

```text
date_trunc('week', ...)
```

或 SQLAlchemy 对应表达式。

明确统一周起始规则。

建议：

```text
Monday
```

不要在 Python 拉回所有日期后再分组。

---

# 25. 时间趋势零值补齐

如果时间范围：

```text
2026-08-01 ~ 2026-08-07
```

其中某天：

```text
0 条
```

前端折线图最好仍然显示：

```text
0
```

因此可以：

### 方案 A

后端补齐时间序列。

### 方案 B

前端根据返回范围补齐。

推荐后端统一补齐，避免多个客户端重复逻辑。

但如果当前实现复杂度明显上升，V1 可返回有数据日期并由 Dashboard Adapter 补齐。

选择一种并保持测试。

---

# 26. Dashboard 统一 Filter

Dashboard API 必须支持与：

```http
GET /api/v1/applications
```

一致的业务筛选条件。

至少：

```text
keyword

status

company_nature

application_type

industry

date_from

date_to

company_size
```

Dashboard 不需要：

```text
sort

page

page_size
```

因为统计接口不分页。

---

# 27. 复用筛选构造逻辑

不要复制：

```text
ApplicationRepository
```

中 Phase 3 的所有 WHERE 条件。

推荐抽出：

```text
ApplicationQueryFilters
```

或现有：

```text
apply_application_filters()
```

能够复用：

```text
Application List Query

Dashboard Aggregate Query
```

但：

不要为了追求 100% DRY 造成过度抽象。

目标是：

```text
筛选语义一致
```

而不是：

```text
任何 SQL 都必须走同一个函数
```

---

# 28. User Scope 第一原则

所有 Dashboard Query 必须首先：

```sql
WHERE job_applications.user_id = :current_user_id
```

禁止：

```text
全局聚合
↓
再在 Python 过滤当前用户
```

Dashboard 属于用户私有数据。

---

# 29. Analytics Service

推荐新增：

```text
AnalyticsService
```

职责：

```text
get_summary()

get_status_distribution()

get_industry_distribution()

get_company_nature_distribution()

get_application_trend()
```

具体名称遵循现有代码风格。

---

# 30. Repository / Query Layer

推荐：

```text
AnalyticsRepository
```

或：

```text
ApplicationAnalyticsRepository
```

负责：

```text
SQL Aggregate

COUNT

GROUP BY

DISTINCT

date_trunc
```

不要把复杂 SQL 全塞：

```text
dashboard router
```

里。

---

# 31. Router

Dashboard Router 只负责：

```text
Depends(get_current_user)

解析 Filter Params

调用 AnalyticsService

返回 Response
```

不要在 Router：

```text
join
group_by
case
count
```

---

# 32. Pydantic Schemas

建议：

```text
DashboardSummaryRead

DistributionItem

StatusDistributionItem

IndustryDistributionItem

CompanyNatureDistributionItem

TrendPoint

DashboardTrendRead
```

不要返回无 Schema 的随意 Dict。

---

# 33. SQL Aggregate

尽可能使用：

```text
COUNT
COUNT DISTINCT
GROUP BY
CASE
FILTER
```

由 PostgreSQL 完成。

避免：

```text
SELECT 全部 applications
↓
Python for loop
↓
statistics
```

---

# 34. Dashboard 性能

TDD 目标：

```text
列表 / 图表响应 ≤ 0.8s
```

Phase 4 需要在本地真实 PostgreSQL 环境进行测量。

当前数据库已有约：

```text
360 条
```

投递记录。

另外准备：

```text
1000+
```

测试数据用于性能验证。

---

# 35. Dashboard Cache

TDD 中允许：

```text
Redis
```

短缓存：

```text
dashboard:{user_id}:{filter_hash}
```

TTL：

```text
30 ~ 60s
```

但是：

# Phase 4 不强制立即实现 Redis Dashboard Cache

优先先实现：

```text
正确 SQL Aggregate
+
正确筛选联动
+
性能验证
```

如果在：

```text
1000+
```

记录下响应已经远低于目标：

可以暂不引入缓存。

将其作为：

```text
Phase 6 / 性能增强
```

预留。

不要为了用 Redis 强行增加复杂度。

---

# 36. 如果实现 Dashboard Cache

如果实际性能测试证明需要缓存，则必须：

```text
user_id
+
filters
```

共同生成 Cache Key。

禁止：

```text
dashboard:summary
```

全用户共享。

必须防止用户数据串缓存。

---

# 37. Cache Invalidation

如果 Phase 4 使用 Redis Cache：

以下操作后必须失效：

```text
Application Create

Application Update

Application Delete

Batch Delete

Status Change
```

不要依赖 TTL 才更新 Dashboard。

---

# 38. 前端 Dashboard 页面

默认路由：

```text
/
```

作为数据看板首页。

如果当前 Router 已经定义：

遵循现有路由。

---

# 39. Dashboard 页面结构

基础布局：

```text
┌────────────────────────────────────┐
│ 求职投递数据看板                   │
├────────────────────────────────────┤
│ 总投递 │ 进行中 │ Offer │ Offer率 │
│ 面试通过率 │ 淘汰率                │
├────────────────────────────────────┤
│ Dashboard Filter                   │
├────────────────────────────────────┤
│ 状态分布       │ 行业分布          │
├────────────────────────────────────┤
│ 企业性质分布   │ 投递趋势          │
└────────────────────────────────────┘
```

保证：

```text
电脑端
+
平板端
```

自适应。

---

# 40. 指标卡

建议实现：

```text
MetricCard
```

复用组件。

字段：

```text
label

value

loading

optional suffix
```

例如：

```text
总投递：360

进行中：42

Offer：8

Offer获取率：2.22%
```

---

# 41. Percentage 显示

后端：

```text
0.032
```

前端：

```text
3.2%
```

不要后端有时：

```text
0.032
```

有时：

```text
3.2
```

保持统一。

---

# 42. ECharts

使用已有：

```text
ECharts
```

实现：

```text
状态分布饼图

行业分布柱状图

企业性质分布饼图

投递趋势折线图
```

---

# 43. 图表组件

建议拆分：

```text
StatusDistributionChart

IndustryDistributionChart

CompanyNatureChart

ApplicationTrendChart
```

不要把四张图全部写进：

```text
DashboardPage.tsx
```

形成超大文件。

---

# 44. 图表 Tooltip

必须支持 Hover：

展示：

```text
名称

数量

占比
```

例如：

```text
人工智能
18
30%
```

---

# 45. 状态分布图

采用：

```text
Pie Chart
```

状态颜色：

必须复用已有：

```text
StatusTag
StatusMetadata
StatusCategory
```

颜色配置。

不要 Dashboard 自己创建第二套状态颜色。

---

# 46. 企业性质分布

采用：

```text
Pie Chart
```

不要求所有性质都有固定颜色体系。

保持视觉清晰即可。

---

# 47. 行业分布

采用：

```text
Bar Chart
```

如果行业很多：

建议：

```text
按 count DESC
```

排序。

可以展示：

```text
Top N
```

但 PRD 未要求截断行业。

V1 优先显示全部实际分类，必要时滚动或 dataZoom。

不要悄悄丢弃长尾数据。

---

# 48. 投递趋势

采用：

```text
Line Chart
```

支持：

```text
按日
按周
```

切换。

前端：

```text
Day / Week
```

只是参数：

```text
granularity
```

改变。

---

# 49. Phase 3 Filter 联动

Dashboard 页面需要使用与 Application List 相同的筛选语义。

例如用户选择：

```text
秋招全职
+
人工智能
+
近30天
```

则 Dashboard：

```text
Summary
Status Distribution
Industry Distribution
Company Nature
Trend
```

全部基于同一过滤条件更新。

---

# 50. Filter State

不要为 Dashboard 再创建完全独立的筛选业务定义。

可以复用：

```text
ApplicationFilterParams
```

TypeScript 类型。

对于 Dashboard 不使用的：

```text
sort
page
page_size
```

提交请求时忽略。

---

# 51. Dashboard Filter UI

Phase 4 可以复用 Phase 3：

```text
FilterPanel
```

或者抽取：

```text
SharedApplicationFilters
```

避免：

```text
Applications 页面一个 Filter UI

Dashboard 页面另一个完全不同 Filter UI
```

造成逻辑漂移。

---

# 52. Dashboard 默认过滤

默认：

```text
无筛选
```

展示当前用户所有投递数据。

用户切换筛选：

```text
自动刷新
```

不需要手动点击：

```text
查询
```

除非当前 Phase 3 UX 已经采用显式 Apply。

保持现有产品交互一致。

---

# 53. Dashboard 手动刷新

PRD 要求：

```text
刷新按钮
```

支持手动触发重新统计。

前端使用：

```text
TanStack Query refetch
```

不要：

```text
window.location.reload()
```

---

# 54. TanStack Query

Dashboard Server State：

```text
TanStack Query
```

Query Key 必须包含：

```text
filters
+
granularity
```

例如：

```text
["dashboard", "summary", filters]

["dashboard", "status", filters]

["dashboard", "industry", filters]

["dashboard", "company-nature", filters]

["dashboard", "trend", filters, granularity]
```

---

# 55. Dashboard 数据并发请求

页面加载可以并行请求：

```text
summary
status distribution
industry distribution
company nature distribution
trend
```

不要：

```text
summary完成
↓
status
↓
industry
↓
...
```

串行加载。

---

# 56. API 失败隔离

如果：

```text
Industry Chart API
```

失败：

不应该让整个 Dashboard 白屏。

每个主要图表区块提供：

```text
Loading

Error

Empty
```

状态。

---

# 57. Empty State

用户没有任何投递：

Dashboard 应展示：

```text
总投递 = 0

其他指标 = 0

图表显示空状态
```

不能：

```text
JS error
ECharts error
NaN%
```

并提供：

```text
新增投递
```

引导入口。

---

# 58. Filter Empty State

如果用户筛选后没有记录：

显示：

```text
当前筛选条件下暂无投递数据
```

并提供：

```text
清空筛选
```

---

# 59. Loading

指标卡：

可以使用：

```text
Skeleton
```

图表：

使用适当：

```text
Spin
Skeleton
```

避免布局剧烈跳动。

---

# 60. ECharts 生命周期

确保：

```text
resize
dispose
```

正确处理。

推荐使用已有 React ECharts 封装，如果项目已经安装。

不要重复初始化导致：

```text
There is a chart instance already initialized on the dom
```

---

# 61. 前端性能

Phase 3 已知 bundle 约：

```text
1.28 MB
```

Phase 4 引入大量 ECharts 图表后，应开始考虑：

```text
Route Lazy Loading
+
ECharts 按需加载
+
Code Splitting
```

本阶段可以进行合理优化。

但：

不要更换 UI 框架。

---

# 62. Dashboard 路由懒加载

推荐：

```text
Dashboard
Applications
ApplicationDetail
```

使用：

```text
React.lazy
```

或现有 Router 支持的 Lazy API。

如果能够显著降低初始 bundle：

可以实施。

---

# 63. ECharts 按需加载

如果当前使用：

```text
import * as echarts from "echarts"
```

导致 bundle 较大：

优先考虑按需导入：

```text
PieChart

BarChart

LineChart

TooltipComponent

LegendComponent

GridComponent

CanvasRenderer
```

具体依据当前 ECharts 集成方式。

---

# 64. 不为了 Warning 过度优化

即使最终仍存在：

```text
500 KB+
```

warning：

只要：

```text
build success
功能正确
首屏可接受
```

可以记录 Technical Debt。

不要为了完全消灭警告：

```text
重写前端架构
更换 Ant Design
```

---

# 65. API 设计

实现：

```http
GET /api/v1/dashboard/summary

GET /api/v1/dashboard/status-distribution

GET /api/v1/dashboard/industry-distribution

GET /api/v1/dashboard/company-nature-distribution

GET /api/v1/dashboard/application-trend
```

保持：

```text
/api/v1
```

和项目统一 Response。

---

# 66. Dashboard API Auth

所有 Dashboard API：

必须：

```python
Depends(get_current_user)
```

未登录：

```text
401
```

User A：

不能统计 User B 数据。

---

# 67. User Isolation 测试

构造：

```text
User A

User B
```

分别创建不同 Applications。

验证：

```text
User A Dashboard
```

只统计：

```text
User A
```

记录。

包括：

```text
summary
status
industry
company nature
trend
```

全部测试。

---

# 68. Summary 后端测试

至少：

```text
test_dashboard_summary_empty

test_dashboard_summary_total

test_dashboard_summary_in_progress

test_dashboard_summary_offer_count

test_dashboard_offer_rate

test_dashboard_rejection_rate

test_dashboard_zero_division
```

---

# 69. 面试通过率测试

如果最终实现 interview_rate：

至少：

```text
test_interview_rate_no_interviews

test_interview_rate_with_progression

test_interview_rate_distinct_applications
```

特别验证：

一条 Application 多个 Status Logs：

不能重复计数。

---

# 70. 状态分布测试

至少：

```text
test_status_distribution

test_status_distribution_percentage

test_status_distribution_filtered

test_status_distribution_empty
```

---

# 71. 行业分布测试

至少：

```text
test_industry_distribution

test_industry_distribution_unknown

test_industry_distribution_filtered
```

---

# 72. 企业性质分布测试

至少：

```text
test_company_nature_distribution

test_company_nature_distribution_filtered
```

---

# 73. Trend 测试

至少：

```text
test_application_trend_day

test_application_trend_week

test_application_trend_date_filter

test_application_trend_empty
```

如果实现零值补齐：

增加：

```text
test_application_trend_fills_zero_dates
```

---

# 74. Filter 联动测试

这是 Phase 4 核心测试。

构造：

```text
10 条 Applications
```

其中：

```text
5 秋招
3 实习
2 春招
```

再加入：

```text
不同行业
不同企业性质
不同状态
不同日期
```

筛选：

```text
AUTUMN_FULLTIME
+
人工智能
+
FIRST_INTERVIEW
```

验证：

```text
summary
status distribution
industry distribution
company nature distribution
trend
```

全部只统计过滤后数据。

---

# 75. Dashboard 和 List 一致性测试

建议增加一个重要测试：

同一组：

```text
ApplicationFilterParams
```

请求：

```text
GET /applications
```

得到：

```text
total = X
```

请求：

```text
GET /dashboard/summary
```

必须：

```text
summary.total = X
```

这是防止统计口径漂移最重要的测试之一。

---

# 76. SQL Aggregate 性能测试

准备：

```text
1000+
```

Application。

测试：

```text
summary

status distribution

industry distribution

company nature distribution

trend
```

记录真实耗时。

不要伪造：

```text
<0.8s
```

实际是多少报告多少。

---

# 77. EXPLAIN

对于慢查询：

使用：

```text
EXPLAIN

EXPLAIN ANALYZE
```

检查。

不要一看到：

```text
Seq Scan
```

就立刻增加大量索引。

当前只有：

```text
1000+
```

记录时 PostgreSQL 可能认为 Seq Scan 更快。

---

# 78. 是否新增数据库索引

先测量。

如果 Analytics 查询确实需要，可以考虑现有 B-tree：

```text
user_id

current_status

application_type

application_date

company_id
```

是否已经覆盖。

不要未经性能证据增加大量新索引。

---

# 79. Alembic

如果 Phase 4：

```text
不新增 Schema
不新增 Index
```

则：

**不要创建空 Migration。**

Alembic 继续：

```text
20260825_0002 (head)
```

即可。

如果确实新增数据库结构：

才创建：

```text
20260825_0003_...
```

并真实升级验证。

---

# 80. Frontend Tests

至少测试：

```text
Dashboard Summary render

Dashboard empty state

Dashboard filter change

Dashboard manual refresh

Trend granularity switch

Chart API error state
```

---

# 81. Chart 测试原则

不需要测试 ECharts 内部绘图像素。

重点测试：

```text
正确 API Data
↓
正确转换为 Chart Option
```

以及：

```text
Component Render
Empty
Loading
Error
```

---

# 82. Chart Data Adapter

推荐将：

```text
API Response
```

转换为：

```text
ECharts Option
```

的逻辑单独写成：

```text
chart adapter
```

或 helper。

这样可以单元测试。

不要将大量转换逻辑直接写进 JSX。

---

# 83. Phase 1~3 回归

完成后执行：

```bash
pytest -v
```

必须保证：

```text
Phase 1 Auth / Health

Phase 2 CRUD / Status / Isolation

Phase 3 Search / Filter / Sort / pg_trgm

Phase 4 Analytics
```

全部通过。

---

# 84. Ruff

Phase 4：

所有新增 / 修改 Python 文件：

必须通过 Ruff。

不要在本阶段强行处理所有历史 Ruff 告警。

---

# 85. Frontend 全量测试

执行项目真实命令，例如：

```bash
npm test
```

或：

```bash
npm run test
```

全部通过。

---

# 86. Frontend Build

必须：

```bash
npm run build
```

通过。

报告：

```text
最大 JS chunk
gzip 大小
是否仍存在 warning
```

如果 Phase 4 做了 Code Splitting：

报告优化前后变化。

只报告实际数据。

---

# 87. Docker Compose

Phase 4 完成后：

使用当前已稳定的 Docker 构建方式。

执行：

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

不得：

```bash
docker compose down -v
```

不得删除：

```text
E:\qiuzhao\.runtime\postgres

E:\qiuzhao\.runtime\redis

E:\qiuzhao\.docker-data
```

---

# 88. Docker 内 Alembic

验证：

```text
Alembic head
```

如果 Phase 4 无 Migration：

应该仍是：

```text
20260825_0002 (head)
```

如果新增 Migration：

必须是新 revision head。

---

# 89. 真实 Docker HTTP 验证

在最新容器代码环境下：

登录测试用户。

然后请求：

```text
/dashboard/summary

/dashboard/status-distribution

/dashboard/industry-distribution

/dashboard/company-nature-distribution

/dashboard/application-trend
```

验证：

```text
无筛选

单筛选

组合筛选
```

结果。

---

# 90. 前端真实页面验证

实际访问：

```text
http://127.0.0.1:5173/
```

确认：

```text
指标卡正常

状态饼图正常

行业柱状图正常

企业性质饼图正常

趋势折线图正常

筛选正常

刷新正常

Loading正常

Empty正常
```

---

# 91. 不允许进入 Kimi

再次强调：

Phase 4 完成之前：

禁止：

```text
MOONSHOT_API_KEY

KimiClient

KimiSearchProvider

Kimi Web Search

Company Intelligence
```

本阶段 Dashboard 使用：

```text
用户自己的 PostgreSQL 数据
```

不是互联网数据。

---

# 92. 不允许修改 Phase 3 搜索语义

除非发现 Bug，否则：

禁止重写：

```text
ApplicationFilterParams

搜索

筛选

排序

分页
```

Phase 4 只复用。

如果发现 Bug：

修复后必须增加回归测试。

---

# 93. 开始编码之前必须输出

修改代码前先输出：

# 《Phase 4 实施计划》

包括：

## 1. Git 状态

```text
branch
commit
git status
```

## 2. 当前架构理解

说明：

```text
Phase 1
Phase 2
Phase 3
```

哪些能力可以直接复用。

## 3. Dashboard 指标口径

明确：

```text
total

in_progress

offer_count

offer_rate

rejection_rate

interview_rate
```

计算方式。

如果 `interview_rate` 存在产品歧义：

只对这一项提出说明。

## 4. Filter 复用方案

说明：

```text
ApplicationFilterParams
```

如何复用。

## 5. Backend 方案

说明：

```text
Router
Service
Repository
Schema
```

准备增加什么。

## 6. SQL Aggregate 方案

说明：

```text
Summary
Status Group
Industry Group
Nature Group
Trend
```

如何实现。

## 7. API 设计

列出所有 Dashboard API。

## 8. Frontend 方案

说明：

```text
Metric Cards
Filter
Charts
Refresh
Loading
Empty
```

## 9. ECharts 方案

说明：

```text
Pie
Bar
Line
按需加载 / Bundle处理
```

## 10. 测试计划

列出：

```text
Summary
Distribution
Trend
Filter Linkage
Isolation
Performance
Frontend
Docker
```

完成计划后：

**直接开始开发，无需再次等待用户确认。**

---

# 94. 普通工程问题自行处理

遇到：

```text
SQLAlchemy Error

Aggregate SQL Error

Pydantic Error

ECharts Error

React Error

Test Failure

Docker Build Error
```

自行：

```text
定位
↓
修复
↓
重新验证
```

不要每个普通错误都向用户提问。

---

# 95. 只有这些情况需要暂停

只有：

```text
需要修改 PRD 统计口径

需要删除真实数据

需要不可逆数据库迁移

需要破坏 Phase 3 Filter API

需要更换核心技术栈

需要引入新的大型基础设施
```

才暂停询问。

---

# 96. Phase 4 完成标准

只有以下全部通过：

```text
Dashboard Summary ✅

Total ✅

In Progress ✅

Offer Count ✅

Offer Rate ✅

Interview Rate ✅

Rejection Rate ✅

Status Distribution ✅

Industry Distribution ✅

Company Nature Distribution ✅

Application Trend Day ✅

Application Trend Week ✅

Dashboard Filters ✅

Dashboard/List Filter Consistency ✅

User Isolation ✅

Empty State ✅

Zero Division ✅

Backend Full Tests ✅

Phase 1~3 Regression ✅

Frontend Tests ✅

ECharts Render ✅

Frontend Build ✅

Real PostgreSQL Validation ✅

Real HTTP Validation ✅

Docker Compose ✅

Data Persistence ✅
```

才能写：

```text
✅ Phase 4 Passed
```

---

# 97. Phase 4 最终复验报告

完成后输出：

# 《Phase 4 最终复验报告》

格式如下。

## 1. Git / Branch

✅ / ⚠️ / ❌

## 2. Alembic

说明：

```text
revision
head
是否新增 migration
```

## 3. Dashboard Summary

分别报告：

```text
Total
In Progress
Offer Count
Interview Rate
Offer Rate
Rejection Rate
```

## 4. Status Distribution

✅ / ⚠️ / ❌

## 5. Industry Distribution

✅ / ⚠️ / ❌

## 6. Company Nature Distribution

✅ / ⚠️ / ❌

## 7. Application Trend

```text
Day
Week
```

## 8. Filter Linkage

✅ / ⚠️ / ❌

## 9. Dashboard/List Consistency

报告：

```text
同 Filter 下
Application List total
Dashboard total
```

是否一致。

## 10. User Isolation

✅ / ⚠️ / ❌

## 11. Performance

报告实际：

```text
测试记录数

Summary latency

Status latency

Industry latency

Nature latency

Trend latency
```

不要伪造。

## 12. Backend Tests

真实：

```text
xx passed
xx failed
xx warnings
```

## 13. Phase 1~3 Regression

✅ / ⚠️ / ❌

## 14. Frontend Dashboard

分别说明：

```text
Metric Cards

Status Pie

Industry Bar

Company Nature Pie

Trend Line

Filter

Refresh

Loading

Empty
```

## 15. Frontend Tests

真实：

```text
xx passed
```

## 16. Frontend Build

报告：

```text
Build success

最大 chunk

gzip

是否做 code splitting
```

## 17. Docker Compose

✅ / ⚠️ / ❌

## 18. Real HTTP

✅ / ⚠️ / ❌

## 19. Data Persistence

✅ / ⚠️ / ❌

## 20. 已修复问题

列出开发期间真实问题。

## 21. Technical Debt

只列尚未解决且真实存在的问题。

## 22. 最终结论

只有核心验证全部成功才能：

```text
✅ Phase 4 Passed
```

---

# 98. Phase 4 完成后停止

完成：

```text
Phase 4
```

以及：

```text
《Phase 4 最终复验报告》
```

之后：

**停止开发。**

不要自动进入：

```text
Phase 5
```

尤其禁止开始：

```text
Kimi 2.5

Company Intelligence

企业联网搜索
```

等待用户明确确认。

---

# 99. 现在开始

严格按照：

```text
阅读 PRD
        ↓
阅读最新 TDD
        ↓
检查 Git
        ↓
检查 Phase 3 Filter
        ↓
输出《Phase 4 实施计划》
        ↓
实现 Analytics Repository
        ↓
实现 Analytics Service
        ↓
实现 Dashboard APIs
        ↓
后端测试
        ↓
实现 Dashboard React 页面
        ↓
实现 ECharts
        ↓
实现筛选联动
        ↓
前端测试
        ↓
性能验证
        ↓
Phase 1~3 回归
        ↓
Docker Compose
        ↓
真实 HTTP / 页面验证
        ↓
输出《Phase 4 最终复验报告》
        ↓
停止
```

现在开始 Phase 4。