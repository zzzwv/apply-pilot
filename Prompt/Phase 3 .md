# Phase 3 Codex 开发任务

## 1. 项目背景

你正在继续开发：

**秋招/实习投递状态管理 Web 网站**

项目目录：

```text
E:\qiuzhao
```

项目已经完成并通过：

```text
Phase 1
基础设施
Docker
PostgreSQL
Redis
Alembic
FastAPI
React
JWT Authentication

Phase 2
JobApplication CRUD
Application Status
ApplicationStatusLog
JWT 用户数据隔离
基础分页
基础 Application 前端页面
```

Phase 2 已完成真实：

```text
Docker Compose
PostgreSQL
Redis
HTTP API
JWT
CRUD
状态更新
状态日志
User A / User B 隔离
前端 Build
pytest
```

复验。

因此：

**不要重新实现 Phase 1 或 Phase 2。**

不要重建现有基础架构。

---

# 2. 开发依据

开始开发之前，必须完整阅读：

```text
docs/PRD.md
docs/TDD.md
```

如果文件名不同，请从 `docs/` 中找到：

```text
最新 PRD
最新 TDD
```

当前最新 TDD 为：

```text
Kimi 联网搜索增强版
```

但是：

# Phase 3 不实现 Kimi

本阶段不要开发：

```text
Kimi 2.5
Company Intelligence
企业联网搜查
官网招聘入口发现
招聘 JD 抽取
```

这些属于后续阶段。

执行优先级：

```text
PRD
↓
最新 TDD
↓
当前已经验证通过的代码架构
```

不得为了机械匹配文档而破坏 Phase 1 / Phase 2 已经稳定运行的工程。

---

# 3. 当前阶段目标

现在正式进入：

# Phase 3：搜索 + 筛选 + 排序 + 分页增强

核心目标：

```text
用户拥有大量投递记录
        ↓
输入关键词
        ↓
模糊搜索
        ↓
选择多个筛选条件
        ↓
组合查询
        ↓
选择排序方式
        ↓
分页浏览
        ↓
实时获得准确结果
```

本阶段完成：

```text
关键词模糊搜索

投递状态筛选

企业性质筛选

投递类型筛选

行业筛选

时间筛选

企业规模筛选

多条件组合筛选

投递时间排序

企业名称排序

状态优先级排序

分页 + 筛选组合

PostgreSQL pg_trgm

必要 GIN Index

前端实时搜索

300ms debounce

筛选 UI

排序 UI

URL/API 参数统一

测试与性能验证
```

---

# 4. 当前阶段禁止实现

Phase 3 不允许提前开发：

```text
Dashboard

ECharts Dashboard

Kimi

Kimi Web Search

Company Intelligence

企业自动抓取

官网发现

招聘链接发现

JD 抽取

Celery

企业 Redis Cache

IndexedDB 云同步

多端同步

AI 推荐

简历匹配

Elasticsearch
```

不要扩大开发范围。

---

# 5. 开始前检查 Git

首先执行：

```bash
git status
git branch --show-current
git log --oneline --decorate -5
```

确认：

1. Phase 2 已经提交；
2. 当前工作区没有未知修改；
3. 当前分支最好为：

```text
phase3-search-filter
```

如果仍在：

```text
phase2-application-core
```

并且 Phase 2 已经提交且工作区干净，则创建：

```bash
git switch -c phase3-search-filter
```

禁止删除 Phase 2 分支。

---

# 6. 先阅读当前实现

重点阅读：

```text
backend/app/models/

backend/app/schemas/

backend/app/repositories/

backend/app/services/

backend/app/api/

backend/app/models/application*

backend/app/models/company*

backend/tests/

frontend/src/api/

frontend/src/pages/Applications/

frontend/src/components/

frontend/src/types/
```

确认 Phase 2 当前真实实现后再修改。

尤其检查：

```text
JobApplication
Company
ApplicationStatus
ApplicationType
CompanyNature
CompanySize
Application List API
Application Repository
Application Service
Application List 前端
```

不要重新写已有 CRUD。

---

# 7. 搜索范围

关键词搜索必须覆盖：

```text
企业名称

投递岗位

所属行业

企业性质

备注内容
```

搜索逻辑：

```text
keyword
    ↓
OR
    ↓
Company.full_name
Company.short_name
JobApplication.job_title
Company.industry
Company.nature
JobApplication.note
```

具体字段名必须根据当前真实 Model 调整。

不要假设字段一定和 Prompt 示例完全相同。

---

# 8. 搜索原则

搜索采用：

```text
PostgreSQL
+
ILIKE
+
pg_trgm
+
GIN Index
```

V1 不引入：

```text
Elasticsearch
OpenSearch
Meilisearch
```

当前系统单用户目标：

```text
1000+ 投递记录
```

PostgreSQL 足够。

---

# 9. PostgreSQL pg_trgm

检查：

```text
pg_trgm
```

是否已经启用。

如果没有：

新增 Alembic migration：

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

然后针对高价值文本搜索字段建立合理 GIN trigram index。

候选字段包括：

```text
companies.full_name

companies.short_name

companies.industry

job_applications.job_title

job_applications.note
```

但：

**必须根据当前数据库真实字段决定。**

不要为了“索引越多越好”给所有字段无脑建立 GIN。

---

# 10. 企业性质搜索

如果：

```text
company.nature
```

当前是 Enum：

不要为了模糊搜索强行修改数据库类型。

请先检查现有：

```text
CompanyNature
```

定义。

如果数据库存储：

```text
STATE_OWNED
PRIVATE
FOREIGN
...
```

而前端展示：

```text
国企
私企
外企
```

应通过已有 enum metadata / 映射完成语义匹配。

不要通过危险字符串拼 SQL。

---

# 11. Keyword Normalize

后端对 keyword：

```text
trim
```

空字符串：

```text
""
"   "
```

视为：

```text
无关键词过滤
```

不要因为空 keyword 导致：

```text
WHERE field ILIKE '%%'
```

产生没有意义的条件和索引失效。

---

# 12. 多维筛选

必须支持：

## 状态

```text
status
```

支持多状态。

例如：

```text
FIRST_INTERVIEW
SECOND_INTERVIEW
HR_INTERVIEW
```

---

## 企业性质

```text
company_nature
```

例如：

```text
国企
央企
私企
外企
合资
初创
```

具体枚举使用项目现有定义。

---

## 投递类型

```text
application_type
```

至少包括现有：

```text
AUTUMN_FULLTIME
SPRING_FULLTIME
SUMMER_INTERNSHIP
DAILY_INTERNSHIP
```

---

## 行业

```text
industry
```

---

## 时间

```text
date_from
date_to
```

必须支持：

```text
近7天

近30天

自定义时间区间
```

前端：

```text
近7天
近30天
自定义
```

转换成统一：

```text
date_from
date_to
```

发送后端。

后端不要再建立：

```text
last_7_days=true
```

这种第二套时间过滤协议。

---

## 企业规模

```text
company_size
```

使用当前 Company Model 的规模字段。

---

# 13. 所有筛选条件必须支持组合

例如：

```text
keyword = AI
+
status = RESUME_PASSED,FIRST_INTERVIEW
+
company_nature = STATE_OWNED
+
application_type = AUTUMN_FULLTIME
+
industry = 人工智能
+
date_from = 2026-08-01
+
date_to = 2026-08-31
```

最终查询必须满足：

```text
keyword group
AND
status
AND
company nature
AND
application type
AND
industry
AND
date range
AND
company size
```

而不是互相覆盖。

---

# 14. Query Parameter 设计

扩展现有：

```http
GET /api/v1/applications
```

建议支持：

```text
keyword

status

company_nature

application_type

industry

date_from

date_to

company_size

sort

page

page_size
```

例如：

```http
GET /api/v1/applications
?keyword=AI
&status=FIRST_INTERVIEW,SECOND_INTERVIEW
&company_nature=STATE_OWNED
&application_type=AUTUMN_FULLTIME
&industry=人工智能
&date_from=2026-08-01
&date_to=2026-08-31
&sort=application_date_desc
&page=1
&page_size=20
```

保持一个稳定 API。

不要为每个筛选条件创建独立 endpoint。

---

# 15. Filter DTO

推荐定义统一：

```text
ApplicationFilterParams
```

或者当前项目风格对应 Schema。

包含：

```text
keyword

statuses

company_natures

application_types

industries

date_from

date_to

company_sizes

sort

page

page_size
```

这样未来：

```text
Dashboard
```

也可以复用同一筛选定义。

不要在：

```text
Application Router
Application Service
Repository
Dashboard
```

未来各写一套过滤逻辑。

---

# 16. 参数校验

必须校验：

```text
page >= 1

1 <= page_size <= 100

date_from <= date_to
```

非法 Enum：

返回统一参数错误。

例如：

```text
status=HELLO
```

必须拒绝。

不能静默忽略非法值。

---

# 17. List 查询必须只看当前用户

Phase 2 的安全规则继续严格保留。

所有查询基础条件必须首先包含：

```sql
job_applications.user_id = current_user.id
```

然后再追加：

```text
Search
Filter
Sort
Pagination
```

禁止：

```text
先全表搜索
↓
最后 Python 中过滤 user_id
```

---

# 18. Repository 设计

Phase 3 主要复杂度应该位于：

```text
ApplicationRepository
```

或独立 Query Builder。

建议结构：

```text
build_base_query(current_user)

apply_keyword_search(query, keyword)

apply_status_filter(query, statuses)

apply_company_filter(...)

apply_date_filter(...)

apply_sort(...)

apply_pagination(...)
```

具体函数拆分根据现有代码风格决定。

避免产生一个：

```text
300+ 行 list_applications()
```

---

# 19. SQLAlchemy 查询原则

优先使用：

```text
SQLAlchemy Expression API
```

避免用户输入进入：

```text
text(f"...{keyword}...")
```

等原始 SQL 拼接。

禁止 SQL Injection 风险。

---

# 20. Company Join

关键词搜索和企业筛选会涉及：

```text
JobApplication
JOIN
Company
```

请确保：

```text
JOIN
```

不会导致：

```text
重复 Application 行
```

如果未来 join 多个 one-to-many 表：

注意：

```text
DISTINCT
```

但当前不要无意义增加 DISTINCT。

---

# 21. Total Count

分页返回中的：

```text
total
```

必须是：

```text
应用全部搜索/筛选条件之后
```

的总数量。

例如：

数据库总共有：

```text
100 条
```

筛选后：

```text
12 条
```

则：

```json
{
  "total": 12
}
```

而不是：

```text
100
```

---

# 22. Pagination

继续使用 Phase 2：

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
100
```

计算：

```text
offset = (page - 1) * page_size
```

搜索 / 筛选 / 排序以后再分页。

顺序必须是：

```text
User Scope
↓
Search
↓
Filter
↓
Sort
↓
Pagination
```

---

# 23. 默认排序

PRD / TDD 要求默认：

```text
投递时间倒序
```

即：

```sql
ORDER BY application_date DESC
```

对于相同日期：

增加稳定 secondary sort，例如：

```text
created_at DESC
```

或：

```text
id
```

保证分页顺序稳定。

---

# 24. 排序选项

必须实现：

```text
application_date_asc

application_date_desc

company_name_asc

status_priority_desc
```

如果当前前端/后端命名规范不同，可以调整枚举名称，但保持语义一致。

---

# 25. 企业名称排序

企业名称排序需要：

```text
JOIN Company
```

优先使用：

```text
short_name
```

还是：

```text
full_name
```

应按照当前 TDD / Model 以及 UI 实际展示字段保持一致。

如果没有明确规则：

建议以：

```text
COALESCE(short_name, full_name)
```

或当前项目现有展示名称作为排序依据。

不要为排序修改企业数据模型。

---

# 26. 状态优先级排序

PRD 核心顺序：

```text
进行中
>
待推进
>
成功
>
失败
```

不要使用：

```text
ORDER BY current_status
```

因为数据库 Enum 字符串顺序没有业务意义。

应使用：

```text
CASE
```

或已有：

```text
StatusMetadata
```

映射生成排序权重。

优先复用项目当前已有的：

```text
StatusCategory
StatusMetadata
order
```

如果当前代码已经定义状态分类和顺序：

禁止重新维护第二套映射。

对于 PRD 未明确排序位置的特殊状态：

```text
OFFER_REJECTED / USER_TERMINATED
```

优先使用已有状态 metadata/order。

不要悄悄创造新的业务语义。

---

# 27. 搜索结果字段

List Item 至少继续返回：

```text
id

company

job_title

application_type

application_date

channel

current_status

created_at

updated_at
```

并提供前端列表需要的：

```text
company_name

industry

company_nature

company_size
```

如果当前 ApplicationRead 已通过：

```text
company
```

嵌套对象返回这些字段，则直接复用。

不要无意义重复：

```text
company
+
company_name
+
company_full_name
```

三套结构。

---

# 28. 防 N+1

Application List 需要企业信息。

检查当前 SQLAlchemy relationship loading。

避免：

```text
List 20 applications
↓
额外发送 20 条 company query
```

推荐：

```text
selectinload
```

或：

```text
joinedload
```

根据当前查询结构选择。

必须通过 SQL 日志或代码检查确认不会明显产生 N+1。

---

# 29. 前端搜索框

Application List 页面增加：

```text
关键词搜索
```

Placeholder 可以类似：

```text
搜索公司、岗位、行业、企业性质或备注
```

输入时使用：

```text
300ms debounce
```

不要每输入一个字符立即发请求。

---

# 30. Debounce 行为

例如：

```text
用户输入：
A
AI
AI应
AI应用
```

最终在用户停止输入约：

```text
300ms
```

后发一次搜索请求。

清空输入框：

应立即或在 debounce 后恢复全部记录。

避免：

```text
旧请求晚返回覆盖新请求
```

TanStack Query 应按 query key 管理。

---

# 31. 前端 Filter Panel

增加：

```text
状态

企业性质

投递类型

行业

时间范围

企业规模
```

状态建议支持：

```text
多选
```

其他筛选按照 PRD 合理支持单选或多选。

不要做过度复杂高级搜索 Builder。

---

# 32. 时间筛选 UI

至少支持快捷项：

```text
近7天

近30天

自定义时间
```

最终转换成：

```text
date_from
date_to
```

后端不感知：

```text
近7天
```

这样的 UI 文案。

---

# 33. 清空筛选

必须提供：

```text
清空筛选
```

执行后：

```text
keyword = ""

status = none

company_nature = none

application_type = none

industry = none

date = none

company_size = none

sort = default
```

并：

```text
page = 1
```

---

# 34. 筛选变化后分页处理

任何以下变化：

```text
keyword

filter

sort
```

都应该：

```text
page → 1
```

避免用户原来在：

```text
第 8 页
```

修改筛选后出现：

```text
无数据
```

但其实筛选结果只有 2 页。

---

# 35. TanStack Query

继续使用：

```text
TanStack Query
```

管理 Application Server State。

Query Key 必须包含：

```text
keyword
filters
sort
page
page_size
```

例如：

```text
[
  "applications",
  {
    keyword,
    status,
    companyNature,
    applicationType,
    industry,
    dateFrom,
    dateTo,
    companySize,
    sort,
    page,
    pageSize
  }
]
```

具体写法遵循项目风格。

---

# 36. Zustand

不要把查询结果放进 Zustand。

Zustand 仅管理：

```text
UI state
```

如果目前 Filter 状态已经适合放：

```text
local component state
```

也无需为了 Zustand 强行迁移。

---

# 37. Loading

搜索 / 筛选过程中：

保留上一次数据或展示：

```text
Loading
```

不要整个页面频繁闪白。

如果 TanStack Query 当前版本支持：

```text
placeholderData
```

或已有 keep previous data 方案，可以合理使用。

---

# 38. Empty State

需要区分：

```text
用户没有任何投递记录
```

和：

```text
有投递记录，但当前搜索/筛选无结果
```

无结果显示：

```text
暂无匹配投递记录
```

并提供：

```text
清空筛选
```

操作。

---

# 39. 前端排序

增加排序选择：

```text
投递时间：最新优先

投递时间：最早优先

企业名称

状态优先级
```

默认：

```text
投递时间最新优先
```

---

# 40. 前后端统一 Enum

禁止：

前端：

```text
"最新"
```

后端：

```text
"date_desc"
```

然后多个地方硬编码转换。

定义稳定 API 枚举，例如：

```text
application_date_desc
application_date_asc
company_name_asc
status_priority_desc
```

前端 Label 单独映射。

---

# 41. Alembic

Phase 3 很可能需要增加：

```text
pg_trgm extension

GIN indexes
```

因此应该：

```bash
python -m alembic -c alembic.ini current
```

确认当前：

```text
20260824_0001 (head)
```

然后创建新的 Phase 3 migration。

例如：

```text
20260825_0002_search_indexes
```

名称遵循当前项目迁移命名规范。

---

# 42. Migration 要求

Migration 必须：

```text
upgrade
```

可以创建：

```text
pg_trgm

必要 GIN indexes
```

同时：

```text
downgrade
```

能够删除：

```text
indexes
```

对于：

```text
DROP EXTENSION pg_trgm
```

必须谨慎。

如果系统未来可能存在其他依赖：

不要在 downgrade 无脑删除共享 Extension。

根据项目数据库生命周期做安全处理。

---

# 43. Migration 真实验证

在 Docker PostgreSQL 中执行：

```bash
python -m alembic -c alembic.ini upgrade head
```

然后：

```bash
python -m alembic -c alembic.ini current
```

确认新 revision：

```text
head
```

检查：

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'pg_trgm';
```

确认：

```text
pg_trgm
```

存在。

---

# 44. Index 验证

使用 PostgreSQL 查询实际确认索引存在。

同时可以使用：

```sql
EXPLAIN
```

或：

```sql
EXPLAIN ANALYZE
```

检查代表性搜索查询。

不要因为小数据集：

```text
Seq Scan
```

就错误认为索引无效。

PostgreSQL 在小表上选择 Seq Scan 是正常的。

重点验证：

```text
索引真实存在
查询正确
```

---

# 45. 后端测试：关键词搜索

至少测试：

```text
test_search_by_company_full_name

test_search_by_company_short_name

test_search_by_job_title

test_search_by_industry

test_search_by_company_nature

test_search_by_note

test_search_is_case_insensitive_when_applicable

test_empty_keyword_returns_normal_list
```

如果中文不存在大小写问题：

英文测试覆盖 case-insensitive 即可。

---

# 46. 后端测试：筛选

至少：

```text
test_filter_by_status

test_filter_by_multiple_statuses

test_filter_by_company_nature

test_filter_by_application_type

test_filter_by_industry

test_filter_by_company_size

test_filter_by_date_range
```

---

# 47. 组合筛选测试

必须测试真正组合条件：

例如数据：

```text
A：
AI岗位
国企
人工智能
秋招
FIRST_INTERVIEW

B：
Java岗位
私企
互联网
秋招
APPLIED
```

Query：

```text
AI
+
国企
+
FIRST_INTERVIEW
+
AUTUMN_FULLTIME
```

只能返回 A。

至少增加：

```text
test_combined_filters
```

---

# 48. 排序测试

至少：

```text
test_default_sort_application_date_desc

test_sort_application_date_asc

test_sort_company_name

test_sort_status_priority
```

确保：

```text
status_priority
```

测试的是业务权重，不是 Enum 字母顺序。

---

# 49. Pagination + Filter 测试

必须验证：

```text
搜索后 total 正确

筛选后 total 正确

page 正确

page_size 正确

最后一页正确

无结果正确
```

增加：

```text
test_filter_with_pagination

test_search_with_pagination
```

---

# 50. 权限回归测试

Phase 2 User Isolation 不允许回归。

必须验证：

```text
User A 搜索结果
```

永远不包含：

```text
User B Application
```

即使：

```text
两人的 Company
job_title
note
```

完全相同。

---

# 51. 非法参数测试

至少：

```text
invalid status

invalid application_type

invalid company_nature

invalid sort

page = 0

page_size = 0

page_size > 100

date_from > date_to
```

必须返回明确参数错误。

---

# 52. SQL Injection 测试

对 keyword 至少测试类似：

```text
'
%'; DROP TABLE users; --
```

确保：

```text
参数绑定
```

不会导致：

```text
SQL Error
数据损坏
```

不要自行构建原始 SQL 字符串。

---

# 53. 性能验证数据

准备至少：

```text
1000+
```

条单用户测试 Application 数据。

可以通过：

```text
测试 Fixture
seed script
临时测试数据生成器
```

生成。

不要手工调用 API 创建 1000 次导致测试极慢。

---

# 54. 性能验证

至少测试代表性：

```text
无筛选列表

keyword 搜索

单筛选

多条件组合

状态排序

企业名称排序
```

记录：

```text
query duration
```

PRD 目标：

```text
单用户 1000+记录流畅
```

如果本机时间受 Docker / Debug 环境影响：

报告真实测量值。

不要为了满足数字伪造性能结果。

---

# 55. Frontend Test

至少覆盖：

```text
搜索输入触发 debounce

筛选变化重新请求

筛选变化 page reset

清空筛选

排序变化

无结果状态
```

根据当前前端测试工具：

```text
Vitest
React Testing Library
```

执行。

---

# 56. Phase 1 / Phase 2 全量回归

完成后执行全部后端测试：

```bash
pytest -v
```

不能只运行 Phase 3 Test。

要求：

```text
Auth
Health
Models
Application CRUD
Application Status
Status Logs
User Isolation
Search
Filter
Sort
Pagination
```

全部通过。

---

# 57. Ruff

当前项目已知：

```text
Phase 1 存在历史 Ruff 告警
```

本阶段要求：

```text
Phase 3 新增 / 修改 Python 文件
```

至少通过 Ruff。

不要为了 Phase 3：

```text
顺手重构整个 Phase 1
```

71 个历史问题。

如果顺手修复很安全可以处理少量，但不要扩大范围。

---

# 58. 前端 Build

执行：

```bash
npm run build
```

当前已有：

```text
Vite 大 chunk warning
```

本阶段仍然不需要为了 Warning：

```text
更换 Ant Design
大规模重构
```

但如果新增 Filter Panel 后包体显著异常增长：

请报告。

---

# 59. Docker Compose

Phase 3 完成后真实执行：

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

遵循当前已经确定的 Docker 数据路径。

禁止：

```bash
docker compose down -v
```

禁止删除：

```text
E:\qiuzhao\.runtime\postgres
E:\qiuzhao\.runtime\redis
E:\qiuzhao\.docker-data
```

---

# 60. 真实 HTTP 复验

Docker 最新代码运行以后：

使用真实：

```text
PostgreSQL
FastAPI
```

完成至少：

```text
登录
↓
准备多条不同 Company / Application 数据
↓
keyword Search
↓
status Filter
↓
company nature Filter
↓
application type Filter
↓
industry Filter
↓
date Filter
↓
company size Filter
↓
combined Filter
↓
application_date Sort
↓
company_name Sort
↓
status_priority Sort
↓
Pagination
```

必须确认 API 返回真实正确结果。

---

# 61. 不允许修改 Phase 2 业务语义

本阶段不要：

```text
更改现有 14 状态定义

删除 Status Logs

修改 JWT 用户隔离

允许 PUT 修改 current_status

改变 Application 删除规则

重新设计 Company Model
```

除非发现明确 Bug。

如果发现 Phase 2 Bug：

先修复并增加回归测试。

---

# 62. 不允许 Kimi 提前进入 Phase 3

即使最新 TDD 中已经有：

```text
Kimi 2.5
```

本阶段：

不要安装 Kimi SDK。

不要增加：

```text
MOONSHOT_API_KEY
KimiClient
KimiSearchProvider
```

不要把关键词搜索理解成：

```text
LLM Search
```

这里的 Search 是：

```text
用户自己的 JobApplication 数据库搜索
```

不是互联网搜查。

---

# 63. 开始编码之前必须先输出

开始修改文件前，先输出：

# Phase 3 实施计划

必须包括：

## 1. 当前 Git 状态

```text
branch
commit
git status
```

## 2. Phase 3 需求理解

说明：

```text
Search
Filter
Sort
Pagination
```

各自职责。

## 3. 当前 List API 分析

说明 Phase 2：

```text
GET /applications
```

目前如何实现。

## 4. 数据库分析

说明：

```text
哪些字段需要 pg_trgm

哪些字段适合普通 B-tree

是否需要新 migration
```

## 5. Repository / Service 方案

说明如何避免：

```text
巨大 list_applications()
```

## 6. API Query 参数

列出最终参数协议。

## 7. Frontend 方案

说明：

```text
SearchInput
FilterPanel
SortSelect
Pagination
300ms debounce
TanStack Query
```

如何配合。

## 8. 测试计划

列出：

```text
Search
Filter
Combination
Sort
Pagination
Isolation
Performance
```

测试。

完成计划以后：

**直接开始开发，不需要等待我确认。**

---

# 64. 普通技术问题自行处理

遇到：

```text
SQLAlchemy Error

Alembic Error

PostgreSQL Extension Error

Pydantic Error

React Error

Test Failure

Docker Build Error
```

先：

```text
定位根因
↓
最小修改
↓
重新验证
```

不要每遇到普通 Bug 就停下来问用户。

---

# 65. 只有这些情况需要停下来询问

只有：

```text
需要不可逆数据库操作

需要删除真实数据

需要改变 PRD 业务规则

需要更换 PostgreSQL

需要引入 Elasticsearch

需要更换核心技术栈

发现 PRD 与 TDD 无法调和的重大冲突
```

才需要暂停并询问。

---

# 66. Phase 3 完成标准

只有以下全部通过：

```text
Keyword Search ✅

Company Name Search ✅

Job Title Search ✅

Industry Search ✅

Company Nature Search ✅

Note Search ✅

Status Filter ✅

Company Nature Filter ✅

Application Type Filter ✅

Industry Filter ✅

Date Filter ✅

Company Size Filter ✅

Combined Filters ✅

Application Date Sort ✅

Company Name Sort ✅

Status Priority Sort ✅

Pagination + Filters ✅

User Isolation ✅

pg_trgm ✅

GIN Indexes ✅

Alembic ✅

pytest Full Suite ✅

Frontend Tests ✅

Frontend Build ✅

Real HTTP Validation ✅

Docker Compose ✅

Phase 1 / Phase 2 No Regression ✅
```

才能宣布：

```text
✅ Phase 3 Passed
```

---

# 67. Phase 3 最终复验报告

完成后输出：

# 《Phase 3 最终复验报告》

格式：

## 1. Git / Branch

✅ / ⚠️ / ❌

## 2. Alembic

说明：

```text
old revision
new revision
head
```

## 3. pg_trgm

✅ / ⚠️ / ❌

## 4. Database Indexes

列出新增索引。

## 5. Keyword Search

分别报告：

```text
Company Name
Job Title
Industry
Company Nature
Note
```

## 6. Filters

分别报告：

```text
Status
Company Nature
Application Type
Industry
Date
Company Size
```

## 7. Combined Filters

✅ / ⚠️ / ❌

## 8. Sorting

分别报告：

```text
Application Date ASC
Application Date DESC
Company Name
Status Priority
```

## 9. Pagination

✅ / ⚠️ / ❌

## 10. User Isolation

✅ / ⚠️ / ❌

## 11. Performance

报告：

```text
测试数据规模

典型 List 时间

Keyword Search 时间

Combined Filter 时间
```

只写实际测量结果。

## 12. Backend Tests

真实输出：

```text
xx passed
xx failed
xx warnings
```

## 13. Phase 1 / Phase 2 Regression

✅ / ⚠️ / ❌

## 14. Frontend

说明：

```text
Search
Filter Panel
Sort
Pagination
Debounce
Empty State
```

## 15. Frontend Tests

真实：

```text
xx passed
```

## 16. Frontend Build

✅ / ⚠️ / ❌

同时记录 bundle warning。

## 17. Docker Compose

✅ / ⚠️ / ❌

## 18. Real HTTP Validation

✅ / ⚠️ / ❌

## 19. 已修复问题

列出实际开发期间解决的问题。

## 20. Technical Debt

只列真正剩余问题。

## 21. Phase 3 最终结论

核心验证全部通过才能写：

```text
✅ Phase 3 Passed
```

---

# 68. Phase 3 完成后停止

完成：

```text
Phase 3
```

并输出：

```text
《Phase 3 最终复验报告》
```

之后：

**停止开发。**

不要自动进入：

```text
Phase 4 Dashboard
```

不要开始：

```text
ECharts
Kimi
Company Intelligence
```

等待用户确认。

---

# 69. 现在开始

请按以下顺序执行：

```text
阅读 PRD
↓
阅读最新 TDD
↓
检查 Git
↓
检查 Phase 2 代码
↓
输出 Phase 3 实施计划
↓
实现后端 Search / Filter / Sort
↓
实现 pg_trgm / Index
↓
完善 Pagination
↓
实现前端 Search / Filter / Sort
↓
添加测试
↓
全量回归
↓
真实 PostgreSQL 验证
↓
Docker Compose 验证
↓
输出《Phase 3 最终复验报告》
↓
停止
```

现在开始 Phase 3。