# 秋招/实习投递状态管理 Web 网站技术设计文档

**项目名称：** 秋招/实习投递状态管理 Web 网站  
**文档类型：** Technical Design Document（TDD）  
**版本：** V1.1（Kimi 联网搜索增强版）  
**需求基线：**《秋招/实习投递状态管理Web网站产品需求文档（PRD V1.0定稿）》  
**适用对象：** 前端开发、后端开发、测试、运维、产品经理  
**产品形态：** Web 应用


## V1.1 变更说明：Kimi 联网搜索增强

本版本在 V1.0 基础上新增 Kimi 联网搜索能力，主要用于企业公开信息与招聘信息的辅助检索、候选链接发现和结构化抽取。

Kimi 不作为企业数据的唯一可信来源，而作为 Company Intelligence Pipeline 中的 AI Search Provider。所有由 Kimi 返回的企业官网、招聘页面、岗位信息均视为“候选信息”，需要经过确定性规则、官方域名校验、链接有效性检测和来源追踪后再进入正式数据。

核心原则：

```text
Kimi Web Search
      ↓
候选企业/官网/招聘链接/岗位信息
      ↓
规则校验 + 官方域名校验
      ↓
LinkValidator
      ↓
结构化标准数据
      ↓
用户可人工纠错
```

系统仍坚持：

- Official First：企业官网和官方招聘入口优先；
- Human Correctable：所有 AI 搜索结果允许用户修改；
- Source Traceability：AI 返回的重要字段必须保留来源；
- Graceful Degradation：Kimi 不可用时不得阻塞用户新增投递记录；
- Server-side Secret：Kimi API Key 只能保存在后端环境变量中。


---

# 1. 文档目的

本文档用于将产品 PRD 转化为研发团队可落地执行的技术方案，统一前端、后端、数据库、企业信息抓取、搜索、统计、安全和部署等模块的实现方式。

本系统主要解决以下技术问题：

1. 如何仅通过企业名称自动补全企业信息；
2. 如何优先获取企业官方招聘入口；
3. 如何管理同一家企业多个招聘渠道链接；
4. 如何保证外部企业信息来源可靠且可降级；
5. 如何设计完整的求职投递状态流转模型；
6. 如何记录每一次状态变化；
7. 如何支持 1000+ 投递记录实时搜索、筛选和排序；
8. 如何实时计算数据看板指标；
9. 如何实现未登录本地保存、登录后云端同步；
10. 如何保证不同用户之间的数据完全隔离；
11. 如何防止高频企业信息查询造成第三方 API 滥用。

---

# 2. 产品核心技术目标

系统核心数据链路：

```text
用户输入企业名称
        ↓
企业名称标准化
        ↓
企业搜索与候选匹配
        ↓
企业公开信息查询
        ↓
官方域名识别
        ↓
官方招聘链接发现
        ↓
第三方招聘渠道补充
        ↓
链接有效性检测
        ↓
生成企业标准数据
        ↓
用户补充岗位/投递信息
        ↓
保存投递记录
        ↓
状态持续更新
        ↓
状态日志记录
        ↓
搜索 / 筛选 / 看板统计
```

PRD 要求用户只输入企业名称即可自动补齐企业相关信息，并且投递入口必须采用“企业官网招聘链接优先”的策略。

---

# 3. 非目标范围

根据 V1.0 PRD，本版本暂不实现：

```text
简历附件上传
复杂简历版本管理
面试提醒
日程同步
投递数据导出 Excel
PDF 报告导出
求职题库
面试经验社区
复杂 AI 求职推荐
自动投递简历
自动填写招聘官网
```

这些能力属于后续版本预留。

---

# 4. 总体系统架构

推荐采用典型前后端分离架构：

```text
                    ┌──────────────────────┐
                    │      Web Client      │
                    │ React / TypeScript   │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                    ┌──────────────────────┐
                    │      API Gateway     │
                    │ FastAPI / REST API   │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
 ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
 │ Application     │ │ Company Info    │ │ Analytics       │
 │ Service         │ │ Service         │ │ Service         │
 │                 │ │                 │ │                 │
 │ 投递记录        │ │ 企业搜索        │ │ 看板统计        │
 │ 状态管理        │ │ 官网识别        │ │ 指标计算        │
 │ 搜索筛选        │ │ 招聘链接发现    │ │ 趋势统计        │
 └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                     ┌─────────────────┐
                     │ PostgreSQL      │
                     │ Redis           │
                     └─────────────────┘
                              │
                              ▼
                ┌──────────────────────────┐
                │ External Public Sources │
                │ 企业公开数据 API         │
                │ 企业官网                 │
                │ 招聘公开信息源           │
                │ Kimi Web Search / LLM    │
                └──────────────────────────┘
```

---

# 5. 推荐技术栈

## 5.1 前端

推荐：

```text
React 19
TypeScript
Vite
React Router
TanStack Query
Zustand
Ant Design
ECharts
Axios
Zod
```

### 选择理由

React：

- 适合中后台数据管理类产品；
- 表格、筛选、表单、详情页组件生态成熟。

TanStack Query：

用于管理：

```text
服务器状态
接口缓存
Loading
Error
Mutation
数据刷新
```

Zustand：

用于：

```text
用户状态
筛选条件
本地草稿
页面级共享状态
```

ECharts：

用于：

```text
饼图
柱状图
折线图
Tooltip
响应式图表
```

---

# 6. 后端技术栈

推荐：

```text
Python 3.12
FastAPI
SQLAlchemy 2.x
Pydantic
PostgreSQL
Redis
Alembic
Celery / RQ
HTTPX
```

如果项目目标同时兼顾：

```text
AI 应用开发
+
求职项目展示
```

FastAPI 比传统 Java 后端更加适合。

系统中的：

```text
企业数据聚合
网页文本处理
后续 AI 信息抽取
```

也更适合 Python 技术生态。

---

# 7. 基础项目结构

推荐后端：

```text
backend/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── companies.py
│   │   ├── applications.py
│   │   ├── dashboard.py
│   │   └── users.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── application.py
│   │   ├── application_status.py
│   │   └── recruitment_link.py
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── company_service.py
│   │   ├── recruitment_service.py
│   │   ├── application_service.py
│   │   └── analytics_service.py
│   │
│   ├── repositories/
│   │
│   ├── crawlers/
│   │   ├── official_site.py
│   │   ├── recruitment_page.py
│   │   └── link_validator.py
│   │
│   ├── workers/
│   │
│   ├── core/
│   │   ├── security.py
│   │   ├── config.py
│   │   └── database.py
│   │
│   └── main.py
│
└── tests/
```

前端：

```text
frontend/
│
├── src/
│   ├── pages/
│   │   ├── Dashboard/
│   │   ├── Applications/
│   │   └── ApplicationDetail/
│   │
│   ├── components/
│   │   ├── CompanySearch/
│   │   ├── ApplicationForm/
│   │   ├── StatusTag/
│   │   ├── FilterPanel/
│   │   └── Charts/
│   │
│   ├── api/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   ├── utils/
│   └── router/
```

---

# 8. 核心领域模型

系统建议划分为：

```text
User
Company
RecruitmentLink
JobApplication
ApplicationStatusLog
```

---

# 9. User 用户模型

```typescript
interface User {
    id: string
    username: string
    email: string
    createdAt: string
    updatedAt: string
}
```

数据库：

```text
users
```

主要字段：

| 字段 | 类型 |
|---|---|
| id | UUID |
| username | varchar |
| email | varchar |
| password_hash | varchar |
| created_at | timestamp |
| updated_at | timestamp |

---

# 10. Company 企业模型

企业信息属于共享公共数据。

```typescript
interface Company {

    id: string

    fullName: string

    shortName?: string

    nature?: CompanyNature

    size?: CompanySize

    industry?: string

    headquartersCity?: string

    businessDescription?: string

    foundedDate?: string

    registeredCapital?: string

    officialWebsite?: string
}
```

PRD 要求自动获取企业全称、简称、企业性质、规模、行业、总部城市、业务简介、成立时间和注册资本。

---

# 11. RecruitmentLink 招聘链接模型

不能在 Company 表中只保存：

```text
recruitment_url
```

因为 PRD 明确要求一个企业支持多条不同渠道招聘链接，并且每条链接独立管理标签。

因此单独建表：

```text
recruitment_links
```

结构：

```typescript
interface RecruitmentLink {

    id: string

    companyId: string

    url: string

    channel: RecruitmentChannel

    linkType: RecruitmentLinkType

    priority: number

    validStatus: LinkStatus

    lastCheckedAt?: string

    source?: string
}
```

---

# 12. 招聘渠道枚举

```typescript
enum RecruitmentChannel {

    OFFICIAL_CAMPUS = "official_campus",

    OFFICIAL_INTERNSHIP = "official_internship",

    OFFICIAL_SOCIAL = "official_social",

    OFFICIAL_WECHAT = "official_wechat",

    BOSS = "boss",

    ZHILIAN = "zhilian",

    JOB51 = "51job",

    NOWCODER = "nowcoder",

    SHIXISENG = "shixiseng",

    SCHOOL = "school",

    OTHER = "other"
}
```

---

# 13. 招聘链接优先级

建议内部定义：

```text
100 企业官网-校招
95  企业官网-实习
90  企业官网-社招
85  官方招聘公告

50  学校就业网

40  BOSS
40  智联
40  前程无忧
40  牛客
40  实习僧
```

查询时：

```sql
ORDER BY priority DESC
```

从数据层保证：

```text
官网永远优先
```

而不是只依赖前端排序。

PRD 将官网投递入口定义为最高展示优先级。

---

# 14. JobApplication 投递记录模型

这是系统最核心的数据表。

```typescript
interface JobApplication {

    id: string

    userId: string

    companyId: string

    jobTitle: string

    applicationType: ApplicationType

    applicationDate: string

    channel: string

    resumeVersion?: string

    salary?: string

    city?: string

    educationRequirement?: string

    deadline?: string

    requirements?: string

    note?: string

    currentStatus: ApplicationStatus

    createdAt: string

    updatedAt: string
}
```

PRD 中要求用户手动补充岗位、投递类型、投递时间、投递渠道、简历版本和备注等信息。

---

# 15. 投递类型枚举

```typescript
enum ApplicationType {

    AUTUMN_FULLTIME = "autumn_fulltime",

    SPRING_FULLTIME = "spring_fulltime",

    SUMMER_INTERNSHIP = "summer_internship",

    DAILY_INTERNSHIP = "daily_internship"
}
```

---

# 16. 标准化投递状态

建议数据库直接定义稳定枚举值：

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

前端显示中文。

PRD 已给出完整的 14 个状态及其求职流程语义。

---

# 17. 状态分类

不要直接通过字符串判断：

```text
if status == "一面完成"
```

而应该建立状态元数据：

```typescript
interface StatusMetadata {

    code: ApplicationStatus

    name: string

    category: StatusCategory

    order: number
}
```

例如：

```json
{
  "code": "FIRST_INTERVIEW",
  "name": "一面完成",
  "category": "IN_PROGRESS",
  "order": 4
}
```

分类：

```text
WAITING
IN_PROGRESS
SUCCESS
USER_TERMINATED
FAILED
```

---

# 18. 状态颜色映射

按照 PRD：

```text
WAITING
→ 灰色

IN_PROGRESS
→ 蓝色

SUCCESS
→ 绿色

USER_TERMINATED
→ 橙色

FAILED
→ 红色
```

PRD 已明确各种状态标签的视觉分类。

颜色仅作为 UI 视觉层配置，不写入数据库。

---

# 19. 状态变更日志模型

单独建立：

```text
application_status_logs
```

```typescript
interface ApplicationStatusLog {

    id: string

    applicationId: string

    fromStatus?: ApplicationStatus

    toStatus: ApplicationStatus

    remark?: string

    changedAt: string
}
```

数据库禁止只保存：

```text
current_status
```

否则用户无法复盘历史求职流程。

PRD 明确要求每次状态修改永久保留变更前状态、变更后状态、时间和备注。

---

# 20. 状态更新事务

更新状态必须放在同一个事务中：

```text
BEGIN

UPDATE job_application
SET current_status = ...

INSERT application_status_log (...)

COMMIT
```

避免出现：

```text
current_status 已修改
但是
status_log 写入失败
```

---

# 21. 数据库关系设计

```text
users
  │
  │ 1:N
  ▼
job_applications
  │
  │ N:1
  ▼
companies
  │
  │ 1:N
  ▼
recruitment_links


job_applications
  │
  │ 1:N
  ▼
application_status_logs
```

其中：

```text
Company
```

可以作为公共企业数据。

而：

```text
JobApplication
ApplicationStatusLog
```

必须严格绑定：

```text
user_id
```

---

# 22. 企业信息抓取模块

这是系统第二个技术核心。

不能设计成：

```text
用户输入公司
→ 爬虫直接搜全网
```

PRD 已明确约束：

```text
仅使用公开合规数据接口
无违规爬虫行为
```



因此推荐采用：

```text
API Aggregation
+
Kimi Web Search
+
Official Website Discovery
+
Lightweight Public Page Parsing
+
Kimi Structured Extraction
```

其中 Kimi 主要负责：

```text
企业名称联网检索
官方域名候选发现
官方招聘入口候选发现
招聘公告/JD检索
网页文本语义理解
招聘信息结构化抽取
```

Kimi 返回结果只作为候选，不直接认定为最终事实。官网、招聘入口和岗位信息仍需要经过来源、域名、URL 和业务规则校验。

---

# 23. 企业搜索流程

```text
用户输入：
“字节”
     ↓
Query Normalize
     ↓
Search Company
     ↓
候选企业

字节跳动有限公司
北京字节跳动科技有限公司
……
     ↓
根据匹配分数排序
     ↓
用户确认 / 自动选择高置信候选
```

---

# 24. 企业名称标准化

处理：

```text
有限公司
有限责任公司
股份有限公司
集团有限公司
科技有限公司
```

搜索时不能直接删除，而应该：

```text
原始名称
+
标准化名称
+
简称
```

共同参与匹配。

例如：

```text
中国移动通信集团有限公司

中国移动
移动
```

均建立 Alias。

---

# 25. 企业搜索评分

推荐：

```text
Score =
0.50 × NameSimilarity
+
0.20 × AliasSimilarity
+
0.15 × IndustryConsistency
+
0.15 × CityConsistency
```

如果：

```text
Score >= 0.90
```

可直接返回。

如果：

```text
0.65 <= Score < 0.90
```

弹出候选列表。

如果：

```text
Score < 0.65
```

提示：

```text
未查询到确定企业，请手动补充。
```

---

# 26. 企业信息数据源 Adapter

不应把第三方 API 代码直接写进业务 Service。

设计：

```python
class CompanyProvider:

    async def search_company(self, name):
        ...

    async def get_company_detail(self, company_id):
        ...
```

例如：

```text
Provider A
Provider B
Provider C
```

上层：

```text
CompanyAggregationService
```

统一处理。

V1.1 新增：

```text
KimiSearchProvider
```

推荐接口：

```python
class KimiSearchProvider:

    async def search_company(self, company_name: str):
        ...

    async def search_official_site(self, company_name: str):
        ...

    async def search_recruitment_links(self, company_name: str):
        ...

    async def search_jobs(self, company_name: str):
        ...
```

业务层不得直接调用 Kimi HTTP API，必须通过 Provider / Client 抽象，以便未来更换模型或搜索服务。

这样未来替换数据源时不会影响业务逻辑。

---

# 27. 官网识别

获取企业信息后，从公开企业数据中优先获取：

```text
officialWebsite
```

若存在：

```text
https://www.example.com
```

则进入：

```text
RecruitmentDiscoveryService
```

---

# 28. 官方招聘页面识别

对企业官方域名进行有限范围页面发现。

候选 URL：

```text
/career
/careers
/job
/jobs
/join
/join-us
/recruit
/recruitment
/campus
/campus-recruitment
```

中文锚文本：

```text
加入我们
招聘
人才招聘
校园招聘
社会招聘
实习招聘
加入团队
```

英文：

```text
Career
Careers
Jobs
Join Us
Campus Recruitment
Internship
```

---

# 29. 官网招聘链接发现策略

推荐：

```text
企业官网首页
      ↓
提取所有 <a>
      ↓
只保留同主域名链接
      ↓
URL关键词评分
      ↓
Anchor Text评分
      ↓
页面Title评分
      ↓
招聘链接候选
```

评分示例：

```text
anchor = 校园招聘     +40
url contains career  +30
title contains 招聘   +30
```

超过阈值：

```text
>=60
```

认为是招聘页面候选。

---

# 30. 官网安全边界

只允许：

```text
企业公开官网
```

禁止：

```text
登录后页面
需要绕过验证码的页面
robots明确禁止页面
个人数据页面
```

并限制：

```text
最大请求页数
最大请求深度
请求频率
请求超时
```

V1 推荐只扫描：

```text
官网首页
+
最多一级跳转
```

防止变成通用网络爬虫。

---

# 31. 招聘信息抓取 Pipeline

```text
Company Name
     ↓
Query Normalization
     ↓
Cache / Local DB
     ↓
┌───────────────────────────────┐
│ Parallel Retrieval            │
│                               │
│ Company Data API              │
│ Kimi Web Search               │
└──────────────┬────────────────┘
               ↓
Company Candidate Information
               ↓
Official Domain Resolution
               ↓
Official Recruitment Discovery
               ↓
Kimi Recruitment Search
               ↓
Recruitment Page / Job Candidates
               ↓
Kimi Structured Extraction
               ↓
Deterministic Validation
               ↓
Link Ranking + LinkValidator
               ↓
Third-party Supplement
               ↓
Normalization
               ↓
Source Traceability
               ↓
Cache / PostgreSQL
```

---


# 31A. Kimi 联网搜索与结构化抽取设计

## 31A.1 接入目标

Kimi 用于增强企业信息和招聘信息搜索，不替代现有规则引擎、公开企业数据 API、官网发现和链接验证模块。

主要能力：

```text
Company Search
Official Site Search
Recruitment Link Search
Job Search
Recruitment Page Understanding
Structured Extraction
```

典型场景：

```text
用户输入：某公司简称
        ↓
传统企业 API 未命中 / 信息不完整
        ↓
Kimi 联网搜索
        ↓
返回企业全称、官网候选、招聘入口候选
        ↓
确定性校验
        ↓
返回用户
```

---

## 31A.2 Kimi API 接入方式

后端统一封装：

```text
KimiClient
```

推荐配置：

```text
MOONSHOT_API_KEY
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
KIMI_WEB_SEARCH_FORMULA=moonshot/web-search:latest
KIMI_SEARCH_ENABLED=true
```

模型名称和 Base URL 必须配置化，不允许散落硬编码在业务代码中。

API Key 只存在：

```text
Backend Environment
```

禁止：

```text
React Environment
Frontend Bundle
Git Repository
Application Logs
```

---

## 31A.3 联网搜索工具

Kimi 联网搜索使用官方 `web-search` 工具。

调用链路：

```text
GET /v1/formulas/moonshot/web-search:latest/tools
        ↓
POST /v1/chat/completions
        ↓
模型产生 tool_calls
        ↓
POST /v1/formulas/moonshot/web-search:latest/fibers
        ↓
工具结果回填 role=tool
        ↓
POST /v1/chat/completions
        ↓
最终结构化回答
```

建议单独实现：

```text
KimiFormulaClient
KimiWebSearchService
KimiStructuredExtractor
```

不要把 Formula 调用过程写进 `CompanyService`。

---

## 31A.4 Kimi 搜索 Query 设计

针对一个企业，建议生成有限数量的高价值 Query，而不是让模型无限自主搜索。

例如：

```text
{company_name} 官方网站
{company_name} 校园招聘 官网
{company_name} 实习招聘 官网
{company_name} 社会招聘 官网
{company_name} 招聘 岗位 官方
```

如果企业简称存在歧义：

```text
{company_name} {city} {industry} 官方网站
```

用于辅助实体消歧。

V1.1 建议：

```text
每次 enrich 最大 3~5 个搜索意图
```

避免：

```text
无限循环搜索
高 Token 消耗
高搜索调用成本
超过 10 秒交互预算
```

---

## 31A.5 Kimi Search Result Schema

Kimi 返回结果统一转换为：

```python
class KimiCompanySearchResult:
    canonical_name: str | None
    short_name: str | None
    official_website_candidates: list
    recruitment_links: list
    job_candidates: list
    summary: str | None
    confidence: float
    warnings: list[str]
```

链接候选：

```python
class KimiLinkCandidate:
    title: str
    url: str
    channel_type: str
    claimed_official: bool
    source_url: str | None
    evidence: str | None
    confidence: float
```

注意：

```text
claimed_official = true
```

只表示：

```text
模型认为它可能是官方链接
```

并不表示系统已经验证为官方链接。

---

## 31A.6 Structured Output

Kimi 最终输出必须使用结构化模式。

优先：

```text
JSON Schema Structured Output
```

其次：

```text
JSON Object Mode
```

最终结果进入 Pydantic 校验：

```text
Kimi Response
      ↓
JSON Parse
      ↓
Pydantic Validation
      ↓
Business Validation
```

如果：

```text
JSON解析失败
字段缺失
URL格式非法
枚举不合法
```

则：

```text
最多重试 1 次
```

仍失败：

```text
KIMI_PARSE_FAILED
```

并进入降级流程。

---

## 31A.7 System Prompt 设计

推荐固定系统 Prompt：

```text
你是求职企业公开信息检索 Agent。

你的任务是通过联网搜索寻找企业公开信息、企业官方网站、官方校招/实习/社招页面和公开招聘岗位。

规则：

1. 优先企业官方网站和企业官方招聘页面。
2. 不得把第三方招聘平台默认判断为企业官网。
3. 不确定的信息必须标记为 uncertain。
4. 不允许编造 URL、薪资、截止时间、岗位或联系方式。
5. 每个重要结论尽量提供来源 URL。
6. 官方招聘链接必须作为候选返回，最终是否官方由后端校验。
7. 仅搜索公开互联网信息，不尝试登录、不绕过验证码、不抓取个人隐私数据。
8. 输出必须严格符合指定 JSON Schema。
```

User Prompt 示例：

```text
搜索企业：{company_name}

重点查找：
- 企业正式全称
- 企业简称
- 官方网站
- 官方校园招聘入口
- 官方实习招聘入口
- 官方社会招聘入口
- 当前公开招聘岗位
- 工作城市
- 学历要求
- 薪资信息（若官方公开）
- 投递截止时间（若官方公开）

找不到时明确返回 null，不要猜测。
```

---

## 31A.8 AI 结果可信度分层

AI 结果不得直接写成正式企业事实。

建议：

```text
UNVERIFIED
CANDIDATE
VERIFIED
REJECTED
```

状态流：

```text
Kimi Search
   ↓
UNVERIFIED
   ↓
规则验证
   ↓
CANDIDATE
   ↓
官网域名/URL验证
   ↓
VERIFIED
```

如果：

```text
域名冲突
页面404
来源明显不可靠
```

则：

```text
REJECTED
```

---

## 31A.9 官方域名验证

Kimi 返回：

```text
https://career.example.com
```

不得直接标记：

```text
Official
```

需要执行：

```text
Company Official Website
       ↓
Registered Domain
       ↓
Candidate Recruitment URL
       ↓
Domain Relationship Check
```

允许：

```text
example.com
career.example.com
jobs.example.com
```

如果官方官网明确跳转到第三方 ATS：

```text
example.com/careers
      ↓
company.ats-provider.com
```

可认定：

```text
Official Redirected ATS
```

并记录：

```text
source_page
redirect_chain
verified_at
```

---

## 31A.10 Kimi 与直接网页发现的融合

不要采用：

```text
Kimi Search OR Direct Crawl
```

推荐：

```text
Kimi Search
+
Official Website Discovery
+
Direct Lightweight Fetch
```

其中：

Kimi：

```text
语义搜索
候选发现
页面理解
```

规则层：

```text
确定性验证
URL校验
域名关系
链接状态
```

两者组合。

---

## 31A.11 Enrich 并行执行

为了满足 10 秒限制：

```python
async with asyncio.TaskGroup() as tg:
    company_api_task = tg.create_task(...)
    kimi_task = tg.create_task(...)
```

推荐整体预算：

```text
企业数据 API      <= 4s
Kimi Search       <= 8s
整体 Enrich       <= 10s
```

两者并行，而不是：

```text
Company API
     ↓
等待完成
     ↓
Kimi Search
```

Kimi 超时：

```text
KIMI_SEARCH_TIMEOUT
```

不会导致：

```text
COMPANY_ENRICH_FAILED
```

系统继续返回已有信息。

---

## 31A.12 搜索降级链路

推荐：

```text
Redis Cache
    ↓ miss
PostgreSQL
    ↓ stale / missing
Company Public API + Kimi Search
    ↓ partial
Official Website Discovery
    ↓
Manual User Input
```

Kimi API 发生：

```text
401
429
5xx
Timeout
```

统一降级：

```text
warning
+
继续非 AI 路径
```

禁止因为 Kimi 不可用导致用户不能创建投递记录。

---

## 31A.13 缓存策略

Kimi 搜索结果需要缓存。

Key：

```text
kimi:company-search:{normalized_name}
kimi:recruitment:{company_id}
kimi:jobs:{company_id}
```

建议：

```text
企业搜索        24h
招聘入口        12~24h
岗位搜索        6~12h
```

正式写入数据库的 VERIFIED 数据仍按照企业数据更新时间策略刷新。

---

## 31A.14 成本控制

每个用户查询不能无限触发 Kimi。

控制：

```text
Search Intent Limit
Token Limit
Timeout
Redis Cache
Rate Limit
Single Flight
```

建议：

```text
同一企业短时间重复搜索
        ↓
优先命中缓存
```

不要重复调用 Kimi。

---

## 31A.15 Rate Limit

新增：

```text
Kimi Search
5~10 次 / 分钟 / 用户
```

并增加全局 API Provider Rate Limit。

发生：

```text
429
```

返回：

```text
KIMI_RATE_LIMITED
```

前端提示：

```text
智能搜索暂时繁忙，已返回其他可用企业信息，可稍后重试。
```

---

## 31A.16 数据来源追踪

所有 AI 得到的公开信息建议保存：

```text
source_type
source_url
retrieved_by
retrieved_at
verification_status
confidence
```

例如：

```json
{
  "value": "https://career.example.com",
  "source_type": "kimi_web_search",
  "source_url": "https://www.example.com/careers",
  "retrieved_by": "kimi-k2.5",
  "verification_status": "verified",
  "confidence": 0.94
}
```

如果没有可验证来源：

```text
不得升级为 VERIFIED
```

---

## 31A.17 Kimi 错误码

新增：

```text
KIMI_DISABLED
KIMI_AUTH_FAILED
KIMI_SEARCH_TIMEOUT
KIMI_RATE_LIMITED
KIMI_PROVIDER_ERROR
KIMI_TOOL_CALL_FAILED
KIMI_PARSE_FAILED
KIMI_RESULT_UNVERIFIED
```

---

## 31A.18 Kimi 日志

允许记录：

```text
request_id
company_id
query_hash
model
latency_ms
tool_call_count
token_usage
result_count
error_code
```

禁止记录：

```text
MOONSHOT_API_KEY
完整Authorization Header
用户Token
非必要个人隐私信息
```

---

## 31A.19 测试要求

单元测试：

```text
KimiClient
KimiSearchProvider
Structured Output Parser
Candidate Validator
```

集成测试：

```text
Kimi Search Success
Kimi Timeout
Kimi 401
Kimi 429
Malformed JSON
No Search Result
Conflicting Company Candidates
```

必须 Mock Kimi API，避免普通 CI 每次真实调用产生费用。

真实联网测试：

```text
Manual / Staging Only
```

至少验证：

```text
华为
腾讯
字节跳动
中国移动
一家中小企业
```

测试维度：

```text
官方域名准确率
官方招聘入口命中率
错误官方链接率
Kimi Search P95
降级成功率
```

---

## 31A.20 Kimi 接入后的 Company Intelligence

最终结构：

```text
CompanyIntelligenceService
│
├── CompanySearchEngine
│
├── CompanyProviderAdapter
│
├── KimiSearchProvider
│   ├── KimiFormulaClient
│   ├── KimiWebSearchService
│   └── KimiStructuredExtractor
│
├── OfficialDomainResolver
├── RecruitmentPageDiscovery
├── RecruitmentLinkRanker
├── JobInformationExtractor
├── CandidateVerifier
├── LinkValidator
└── CompanyCache
```

原则：

```text
LLM负责“找”和“理解”
规则系统负责“验证”
数据库负责“保存事实”
用户负责“最终纠错”
```


# 32. 招聘岗位模型

为了避免 Company 表不断膨胀，推荐：

```text
company_jobs
```

```typescript
interface CompanyJob {

    id: string

    companyId: string

    title: string

    city?: string

    salary?: string

    education?: string

    description?: string

    deadline?: string

    sourceUrl?: string

    fetchedAt: string
}
```

---

# 33. Link Validator 链接检测

PRD 要求系统自动识别：

```text
404
无法访问
链接失效
```



推荐流程：

```text
URL
 ↓
HEAD Request
 ↓
如果服务器不支持 HEAD
 ↓
GET
 ↓
读取 HTTP Status
```

状态：

```typescript
enum LinkStatus {

    VALID = "valid",

    POSSIBLY_INVALID = "possibly_invalid",

    INVALID = "invalid",

    UNKNOWN = "unknown"
}
```

---

# 34. 链接判断规则

例如：

```text
200-399
→ VALID

404 / 410
→ INVALID

403
→ UNKNOWN

429
→ UNKNOWN

timeout
→ POSSIBLY_INVALID

DNS error
→ INVALID
```

不能把：

```text
403
```

直接判断为失效，因为很多招聘网站禁止服务端探测，但浏览器实际可以正常访问。

---

# 35. 链接检测异步化

不建议：

```text
新增企业
→ 等待所有URL探测
→ 才返回
```

否则可能超过 PRD 的 10 秒要求。

应该：

```text
企业信息返回
     ↓
先展示用户
     ↓
异步检测 URL
     ↓
更新 valid_status
```

---

# 36. Redis缓存

企业信息非常适合缓存。

缓存 Key：

```text
company:search:{query}
company:detail:{company_id}
company:recruitment:{company_id}
```

建议：

```text
企业基础数据 TTL = 7天

招聘链接 TTL = 24小时

链接有效性 TTL = 6小时
```

目的：

```text
降低外部API调用量
+
提升查询速度
+
防止高频抓取
```

---

# 37. 防重复抓取

实现：

```text
Redis Distributed Lock
```

例如：

```text
company:fetch:bytedance
```

当多个用户同时搜索：

```text
字节跳动
```

只允许一个请求真正查询外部源。

其他请求等待缓存。

---

# 38. 企业信息抓取超时

PRD 要求：

```text
10秒自动终止
```



推荐内部拆分：

```text
企业基础API 3s
官网发现     3s
招聘信息     3s
系统预留     1s
```

总 Timeout：

```text
10s
```

如果部分成功：

```json
{
  "status": "partial_success"
}
```

而不是：

```text
全部失败
```

---

# 39. API设计原则

REST API：

```text
/api/v1
```

统一响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

异常：

```json
{
  "code": 40001,
  "message": "company not found",
  "data": null
}
```

---

# 40. 企业搜索接口

```http
GET /api/v1/companies/search?q=华为
```

返回：

```json
{
  "items": [
    {
      "id": "uuid",
      "full_name": "华为技术有限公司",
      "short_name": "华为",
      "industry": "信息与通信技术",
      "headquarters_city": "深圳"
    }
  ]
}
```

---

# 41. 企业详情抓取接口

```http
POST /api/v1/companies/enrich
```

Request：

```json
{
  "company_name": "华为"
}
```

Response：

```json
{
  "company": {},
  "recruitment_links": [],
  "jobs": [],
  "warnings": []
}
```

---

# 42. 新增投递记录

```http
POST /api/v1/applications
```

```json
{
  "company_id": "uuid",
  "job_title": "AI应用开发工程师",
  "application_type": "autumn_fulltime",
  "application_date": "2026-08-20",
  "channel": "official",
  "resume_version": "v3",
  "current_status": "APPLIED",
  "note": ""
}
```

---

# 43. 修改投递记录

```http
PUT /api/v1/applications/{id}
```

---

# 44. 删除

```http
DELETE /api/v1/applications/{id}
```

批量：

```http
POST /api/v1/applications/batch-delete
```

---

# 45. 修改状态

状态单独接口：

```http
PATCH /api/v1/applications/{id}/status
```

Request：

```json
{
  "status": "FIRST_INTERVIEW",
  "remark": "一面完成，主要询问RAG项目"
}
```

Service：

```text
检查记录归属
↓
读取旧状态
↓
更新 current_status
↓
写 status_log
↓
Commit
```

---

# 46. 投递记录列表接口

```http
GET /api/v1/applications
```

支持：

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

```text
/api/v1/applications
?status=FIRST_INTERVIEW,SECOND_INTERVIEW
&industry=人工智能
&application_type=autumn_fulltime
&sort=application_date_desc
```

---

# 47. 搜索设计

PRD 要求搜索：

```text
企业名称
岗位
行业
企业性质
备注
```



V1 数据量：

```text
单用户约1000+
```

不需要 Elasticsearch。

推荐 PostgreSQL：

```text
ILIKE
+
pg_trgm
```

创建 GIN trigram index。

例如：

```sql
CREATE INDEX idx_application_job_title_trgm
ON job_applications
USING gin (job_title gin_trgm_ops);
```

---

# 48. 为什么 V1 不使用 Elasticsearch

当前规模：

```text
1000条 / 用户
```

即使：

```text
10万用户
```

也可以通过 PostgreSQL：

```text
分页
索引
用户隔离
```

处理。

Elasticsearch 会额外增加：

```text
部署
同步
一致性
运维
```

成本。

因此：

```text
V1 PostgreSQL
```

即可。

---

# 49. 搜索防抖

前端实时搜索：

```text
debounce = 300ms
```

避免用户每输入一个字符就立即请求。

---

# 50. 排序

默认：

```sql
ORDER BY application_date DESC
```

企业名称：

```sql
ORDER BY company_name
```

状态优先级：

不能按字符串排序。

建立：

```text
status_priority
```

例如：

```text
进行中     400
待推进     300
成功       200
失败       100
```

---

# 51. 数据看板架构

不要让前端拉取全部记录后计算。

应该由后端：

```text
SQL Aggregate
```

完成。

接口：

```http
GET /api/v1/dashboard/summary
```

---

# 52. Dashboard Summary

返回：

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

PRD 要求看板展示总投递、进行中、Offer 数、通过率和淘汰率。

---

# 53. 图表接口

建议：

```text
GET /dashboard/status-distribution

GET /dashboard/industry-distribution

GET /dashboard/company-nature-distribution

GET /dashboard/application-trend
```

支持同样筛选参数：

```text
industry
status
type
date
```

确保：

```text
列表筛选
=
看板筛选
```

---

# 54. SQL实时统计

例如行业统计：

```sql
SELECT
    company.industry,
    COUNT(*)
FROM job_applications application
JOIN companies company
ON company.id = application.company_id
WHERE application.user_id = :user_id
GROUP BY company.industry;
```

---

# 55. Offer获取率

PRD 给出：

```text
Offer获取率 = 通过数 / 总投递数
```

技术实现前建议进一步在产品/研发评审时统一“通过数”的具体状态口径。

技术上可定义：

```text
OFFER_RECEIVED
+
SIGNED
```

即：

```text
offer_rate =
(OFFER_RECEIVED + SIGNED)
/ TOTAL
```

这里属于技术侧对统计口径的具体化，需要在上线前由产品最终确认。

---

# 56. 前端页面结构

按照 PRD 三大页面：

```text
/
Dashboard

/applications
投递列表

/applications/:id
投递详情
```

PRD 明确要求默认首页为数据看板，同时提供列表页和详情页。

---

# 57. Dashboard 页面

结构：

```text
┌─────────────────────────────────┐
│ 求职投递管理                    │
├─────────────────────────────────┤
│ 总投递 │ 进行中 │ Offer │ 淘汰率 │
├─────────────────────────────────┤
│ 投递状态分布 │ 行业分布          │
├─────────────────────────────────┤
│ 企业性质分布 │ 投递趋势          │
└─────────────────────────────────┘
```

---

# 58. 投递列表页

建议：

```text
┌─────────────────────────────────────────┐
│ 搜索框                   [+ 新增投递]   │
│                                         │
│ 状态 行业 类型 企业性质 时间 规模       │
├─────────────────────────────────────────┤
│ 公司 │ 岗位 │ 类型 │ 时间 │ 状态 │ 操作 │
├─────────────────────────────────────────┤
│ ...                                     │
└─────────────────────────────────────────┘
```

---

# 59. 新增投递流程

推荐使用 Drawer：

```text
点击新增
↓
Drawer打开
↓
输入企业名称
↓
自动查询企业
↓
展示自动补全结果
↓
用户修改
↓
填写岗位信息
↓
保存
```

相比跳转独立页面：

```text
操作路径更短
```

适合轻量记录产品。

---

# 60. 重复企业记录

PRD 要求：

```text
该企业已有投递记录
```

时弹窗确认。

技术实现：

```sql
SELECT EXISTS (
    SELECT 1
    FROM job_applications
    WHERE
      user_id = ?
      AND company_id = ?
)
```

如果存在：

```json
{
  "duplicate": true
}
```

前端：

```text
该企业已有投递记录

[继续新增]
[查看已有记录]
```

对于 PRD 中“覆盖原有记录”的能力，后端应显式调用更新逻辑，而不是自动覆盖。

---

# 61. 数据缓存与云同步

PRD 要求：

```text
未登录
→ 本地缓存

登录
→ 自动同步云端
```



推荐浏览器：

```text
IndexedDB
```

而不是只使用：

```text
localStorage
```

---

# 62. Local Application Model

本地记录必须生成：

```text
client_id
```

例如 UUID：

```text
9dcd...f1
```

登录同步后：

```text
client_id
+
server_id
```

建立映射。

---

# 63. 同步流程

```text
未登录
↓
IndexedDB
↓
用户登录
↓
读取Local Records
↓
调用Sync API
↓
服务端Merge
↓
返回Server ID
↓
客户端更新Mapping
```

---

# 64. Sync Record

建议所有数据带：

```text
created_at
updated_at
version
```

例如：

```json
{
  "client_id": "...",
  "version": 3,
  "updated_at": "2026-08-24T10:00:00Z"
}
```

---

# 65. 冲突策略

V1 推荐简单：

```text
Last Write Wins
```

依据：

```text
updated_at
```

如果本地：

```text
10:30
```

云端：

```text
10:00
```

则：

```text
本地覆盖
```

未来多端复杂同步再升级：

```text
version vector
```

---

# 66. 身份认证

推荐：

```text
JWT
+
Refresh Token
```

Access Token：

```text
15~30min
```

Refresh Token：

```text
7~30days
```

---

# 67. 数据隔离

所有用户数据查询必须包含：

```sql
WHERE user_id = current_user.id
```

不能：

```text
GET application by id
↓
直接返回
```

必须：

```sql
SELECT *
FROM job_applications
WHERE id = ?
AND user_id = ?
```

防止：

```text
IDOR
```

漏洞。

PRD 明确要求普通用户只能访问个人数据，且不同用户数据必须完全隔离。

---

# 68. 数据安全

HTTPS：

```text
TLS
```

必须全站启用。

数据库敏感字段：

如果存储：

```text
公开HR邮箱
公开联系电话
```

可以按照业务数据管理。

用户自己的：

```text
备注
求职记录
简历版本名称
投递历史
```

属于私有数据。

需要：

```text
数据库访问控制
用户行级隔离
备份加密
HTTPS
```

---

# 69. PostgreSQL Row Level Security

如果需要加强数据隔离，可进一步采用：

```text
PostgreSQL RLS
```

形成：

```text
Application Layer
+
Database Layer
```

双重保护。

V1 可根据部署复杂度决定是否启用。

---

# 70. 高频接口保护

PRD 要求防止：

```text
恶意刷新
高频抓取
重复请求
```



使用 Redis Rate Limit：

```text
企业搜索
60次 / 分钟 / 用户

企业抓取
10次 / 分钟 / 用户

普通查询
120次 / 分钟
```

实际阈值上线后根据监控调整。

---

# 71. 防重复请求

前端按钮：

```text
loading = true
```

期间禁用。

后端：

```text
Idempotency-Key
```

可用于新增记录。

避免用户双击：

```text
保存
```

造成重复记录。

---

# 72. 异步任务

以下适合异步：

```text
招聘链接有效性检测
企业公开信息轻量更新
招聘岗位信息刷新
```

采用：

```text
Celery
+
Redis
```

或者小型项目：

```text
RQ
```

---

# 73. 企业数据更新

PRD 要求企业公开信息支持轻量化定时更新。

推荐：

```text
Company Base Info
7天刷新

Recruitment Links
24小时刷新

Open Jobs
12~24小时刷新

Link Health
6~24小时检测
```

只更新：

```text
近期被用户访问的企业
```

避免对所有企业无差别抓取。

---

# 74. 性能指标

PRD：

```text
首次加载 ≤ 1.5s

列表/图表 ≤ 0.8s

企业抓取 ≤ 10s

单用户 1000+记录流畅
```



---

# 75. 前端性能优化

采用：

```text
路由懒加载
Code Splitting
React.memo
列表分页
查询缓存
图表按需加载
```

1000 条数据不建议一次全部渲染。

默认：

```text
page_size = 20
```

最大：

```text
100
```

---

# 76. 数据库索引

必须建立：

```text
user_id

company_id

current_status

application_type

application_date

created_at
```

复合索引：

```sql
(user_id, application_date DESC)

(user_id, current_status)

(user_id, application_type)
```

---

# 77. Dashboard缓存

统计查询可以 Redis 短缓存：

```text
dashboard:{user_id}:{filter_hash}
```

TTL：

```text
30~60s
```

新增、更新、删除时：

```text
invalidate
```

保证统计较实时。

---

# 78. 错误码设计

## 用户

```text
AUTH_REQUIRED
TOKEN_EXPIRED
PERMISSION_DENIED
```

## 企业

```text
COMPANY_NOT_FOUND
COMPANY_AMBIGUOUS
COMPANY_FETCH_TIMEOUT
COMPANY_PROVIDER_ERROR
```

## 招聘链接

```text
LINK_INVALID
LINK_CHECK_TIMEOUT
LINK_DISCOVERY_FAILED
```

## 投递

```text
APPLICATION_NOT_FOUND
APPLICATION_DUPLICATE
APPLICATION_CREATE_FAILED
STATUS_INVALID
```

## 系统

```text
RATE_LIMITED
DATABASE_ERROR
INTERNAL_ERROR
```

---

# 79. 企业抓取降级策略

企业信息抓取绝不能成为新增记录的强依赖。

流程：

```text
企业抓取成功
↓
自动填入


部分成功
↓
已有字段填入
+
缺失字段手动填写


完全失败
↓
手工填写
```

这符合 PRD：

```text
自动抓取
+
用户可全部修改
+
抓取失败允许手工录入
```

的要求。

---

# 80. 前端状态管理

分为两类：

### Server State

```text
Applications
Companies
Dashboard
Status Logs
```

使用：

```text
TanStack Query
```

### UI State

```text
当前筛选条件
Drawer
Modal
临时表单
```

使用：

```text
Zustand
```

不要将所有 API 数据塞进一个全局 Store。

---

# 81. 无刷新数据更新

新增成功：

```text
invalidate applications
invalidate dashboard
```

修改：

```text
invalidate application detail
invalidate applications
invalidate dashboard
```

状态变更：

```text
invalidate detail
invalidate status logs
invalidate applications
invalidate dashboard
```

从而实现 PRD 要求的页面无刷新实时联动。

---

# 82. 日志设计

系统日志禁止打印：

```text
完整用户备注
用户Token
密码
```

日志：

```json
{
  "request_id": "xxx",
  "user_id": "uuid",
  "module": "company_fetch",
  "event": "fetch_timeout",
  "duration_ms": 10000
}
```

---

# 83. 可观测性

建议：

```text
Sentry
+
Prometheus
+
Grafana
```

个人项目初期至少集成：

```text
Sentry
```

监控：

```text
前端异常
API异常
企业抓取异常
```

---

# 84. 核心监控指标

```text
API P95
API Error Rate

Company Fetch Success Rate
Company Fetch Duration

Official Link Discovery Rate
Official Link Valid Rate

Application Create Error Rate

Dashboard Query P95
```

其中最重要的产品技术指标建议增加：

```text
Official Recruitment Link Hit Rate
```

即：

```text
成功找到官网招聘入口企业数
/
查询企业总数
```

---

# 85. 测试策略

分为：

```text
Unit Test
Integration Test
API Test
E2E Test
Performance Test
Security Test
```

---

# 86. 企业搜索测试

覆盖：

```text
公司全称
公司简称
别名
同名企业
无企业
接口Timeout
数据源异常
```

例如：

```text
腾讯
腾讯科技
深圳市腾讯计算机系统有限公司
```

---

# 87. 招聘链接测试

测试：

```text
官网存在校园招聘
官网只有社招
官网无招聘入口
官网404
官网403
官网跳转外部ATS
第三方招聘链接
多个官网入口
```

---

# 88. 投递管理测试

必须验证：

```text
新增
修改
单删
批量删除
重复公司
不同岗位
多次投递同企业
```

---

# 89. 状态测试

至少测试完整链路：

```text
未投递
↓
已投简历
↓
简历通过
↓
一面
↓
二面
↓
终面
↓
HR面
↓
谈薪
↓
Offer
↓
签约
```

以及：

```text
简历淘汰
面试淘汰
主动拒绝Offer
流程终止
```

---

# 90. 数据权限测试

构造：

```text
User A
User B
```

A 访问：

```text
/api/applications/{B_application_id}
```

必须返回：

```text
404
```

或者：

```text
403
```

不能返回 B 的数据。

---

# 91. 性能测试

准备：

```text
1000
3000
5000
```

条单用户模拟数据。

测试：

```text
列表查询
搜索
组合筛选
Dashboard
状态更新
```

核心目标仍以 PRD 的 1000+ 单用户流畅使用为 V1 验收基线。

---

# 92. 推荐数据库表

最终建议：

```text
users

companies

company_aliases

recruitment_links

company_jobs

job_applications

application_status_logs
```

可选：

```text
sync_records

company_fetch_logs
```

---

# 93. V1 开发阶段

## Phase 1

基础框架：

```text
用户
数据库
登录
React
FastAPI
```

---

## Phase 2

核心投递管理：

```text
CRUD
状态管理
状态日志
```

---

## Phase 3

搜索：

```text
搜索
筛选
排序
分页
```

---

## Phase 4

Dashboard：

```text
指标
饼图
柱图
折线图
筛选联动
```

---

## Phase 5

企业信息：

```text
企业搜索
企业API聚合
官网识别
招聘链接发现
链接检测
```

该部分复杂度最高。

---

## Phase 6

同步与性能：

```text
IndexedDB
云同步
Redis
Rate Limit
缓存
```

---

# 94. 技术难度评估

## 一级：简单

```text
投递CRUD
列表
状态标签
基础筛选
```

## 二级：中等

```text
状态日志
组合筛选
Dashboard
云同步
数据隔离
```

## 三级：困难

```text
企业名称匹配
企业数据聚合
官网识别
招聘页面发现
招聘信息抽取
链接有效性检测
```

因此整个项目：

**真正体现技术含量的模块不是 CRUD，而是 Company Intelligence Service。**

---

# 95. 推荐形成独立的 Company Intelligence Service

建议内部模块：

```text
CompanyIntelligenceService
│
├── CompanySearchEngine
│
├── CompanyProviderAdapter
│
├── KimiSearchProvider
│   ├── KimiFormulaClient
│   ├── KimiWebSearchService
│   └── KimiStructuredExtractor
│
├── OfficialDomainResolver
├── RecruitmentPageDiscovery
├── RecruitmentLinkRanker
├── JobInformationExtractor
├── CandidateVerifier
├── LinkValidator
└── CompanyCache
```

这样后续可以自然扩展 AI 能力。

---

# 96. AI能力预留设计

V1 PRD 没有强制要求使用大模型，但 V1.1 技术方案明确将 Kimi 接入 Company Intelligence，用于联网搜索和公开招聘信息结构化抽取。

Kimi 的职责严格限定为：

```text
Search
Candidate Discovery
Semantic Understanding
Structured Extraction
```

不允许由大模型直接跳过规则验证后写入正式企业事实。

同时保留统一抽象：

```text
InformationExtractor
```

接口：

```python
class RecruitmentInformationExtractor:

    async def extract(
        self,
        page_text: str
    ) -> RecruitmentInformation:
        ...
```

V1.1：

```text
Regex
+
DOM
+
规则
+
Kimi Web Search
+
Kimi Structured Output
```

实现“AI 搜索 + 规则验证”的混合架构。

未来即使替换为其他 LLM，也只需要替换 Provider / Extractor，不修改业务 Service。

---

# 97. 后续适合引入 AI 的位置

未来可以引入：

```text
企业名称语义消歧

招聘页面识别

招聘JD结构化抽取

岗位技能抽取

岗位与简历匹配

求职数据智能复盘
```

其中：

```text
招聘JD结构化抽取
```

最适合优先引入 LLM。

---

# 98. 部署架构

个人项目 / 初期：

```text
Nginx
  │
  ├── React Static
  │
  └── /api
        ↓
      FastAPI
        ↓
 PostgreSQL + Redis
```

Docker Compose：

```text
frontend
backend
postgres
redis
nginx
worker
```

---

# 99. CI/CD

GitHub Actions：

```text
Push
 ↓
Lint
 ↓
Unit Test
 ↓
Build
 ↓
Docker Image
 ↓
Deploy
```

环境：

```text
dev
test
prod
```

配置全部通过：

```text
.env
```

管理。

新增 Kimi 配置：

```text
MOONSHOT_API_KEY=
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
KIMI_WEB_SEARCH_FORMULA=moonshot/web-search:latest
KIMI_SEARCH_ENABLED=true
KIMI_SEARCH_TIMEOUT_SECONDS=8
```

`.env.example` 只保留变量名和非敏感默认值，禁止提交真实 `MOONSHOT_API_KEY`。

---

# 100. 最终技术架构

```text
                      User Browser
                           │
                           ▼
                 React + TypeScript
                           │
                        HTTPS
                           │
                           ▼
                      FastAPI
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
ApplicationService CompanyIntelService AnalyticsService
       │                   │                   │
       │          ┌────────┼────────┐          │
       │          ▼        ▼        ▼          │
       │       Company   Kimi AI    Official   │
       │       Provider  Search     Website    │
       │                   │          │         │
       │                Link Validator          │
       │                                      │
       └───────────────────┬───────────────────┘
                           │
                 ┌─────────▼─────────┐
                 │ PostgreSQL       │
                 │ Redis            │
                 └─────────┬─────────┘
                           │
                           ▼
                    Background Worker
```

---

# 101. 核心技术设计原则

整个项目建议坚持以下原则。

## 1. Official First

```text
官网招聘入口
>
第三方招聘平台
```

该原则直接来自 PRD 的核心产品策略。

---

## 2. User Data Isolation

```text
所有私人投递数据
必须 user_id 隔离
```

---

## 3. Async External Data

外部企业信息：

```text
不阻塞核心用户操作
```

即使：

```text
企业接口挂了
```

用户依然能够：

```text
手动新增投递记录
```

---

## 4. Cache First

对于公共企业数据：

```text
先查缓存
→ 再查数据库
→ 最后请求外部源
```

降低：

```text
延迟
成本
Rate Limit风险
```

---

## 5. Source Traceability

每个自动抓取的数据建议记录：

```text
source
fetched_at
```

例如：

```json
{
  "salary": "20-30K",
  "source": "official",
  "fetched_at": "2026-08-24"
}
```

方便后续判断数据时效性。

---

# 102. 技术结论

这套系统表面上看是一个：

```text
求职版 Excel
```

但从技术设计角度，真正可以形成项目亮点的是：

```text
公开企业信息聚合
        +
企业实体匹配
        +
官方域名识别
        +
官方招聘入口发现
        +
招聘链接可信排序
        +
链接有效性校验
        +
求职流程状态机
        +
多维数据分析
```

其中建议将系统技术重点放在：

## Company Intelligence Pipeline

```text
Company Query
      ↓
Entity Resolution
      ↓
Company Enrichment
      ↓
Official Domain Resolution
      ↓
Recruitment Discovery
      ↓
Link Ranking
      ↓
Link Validation
      ↓
Structured Company Profile
```

这部分也是整个项目区别于：

```text
普通 CRUD 管理系统
```

的关键。

V1 开发时不建议一开始追求“全网所有企业都可以自动获取”。

更合理的技术目标是：

```text
常见企业高成功率
+
企业官网链接优先
+
抓取失败可靠降级
+
所有信息可人工纠错
+
投递管理流程稳定
```

这与 PRD 中对企业信息自动抓取、官网入口优先、手工纠错、状态管理、数据统计以及异常兜底的要求保持一致。