# ApplyPilot V1.1 前端 UI/UX 美化任务

你现在是一名资深 SaaS 产品设计师 + Senior Frontend Engineer。

项目名称：

ApplyPilot

项目定位：

AI 驱动的求职投递管理与企业情报平台。

项目目录：

E:\qiuzhao

当前稳定版本：

main
v1.0.0

当前 V1 已完成并通过验收：

- React 19 + TypeScript + Vite
- React Router
- TanStack Query
- Zustand
- Ant Design
- ECharts
- FastAPI
- PostgreSQL
- Redis
- JWT Authentication
- Application CRUD
- Status Timeline
- Search / Filter / Sort
- Dashboard
- Company Intelligence
- Kimi
- Guest IndexedDB
- Guest → Cloud Import
- Cloud Cache
- Offline Read Fallback
- Docker
- 完整测试和性能基准

本轮任务不是新增业务功能。

本轮目标：

# 只对 ApplyPilot 前端进行 UI / UX 视觉升级

使当前页面从：

“默认 Ant Design 管理后台”

升级为：

“现代、清爽、具有求职产品与 AI SaaS 感的正式产品界面”。

==================================================
一、最高优先级约束
==================================================

本轮必须严格遵守：

1. 不修改 Backend。

2. 不修改：

- FastAPI API
- PostgreSQL
- Redis
- Alembic
- Kimi
- Company Intelligence 后端 Pipeline
- JWT 认证机制
- Application CRUD 业务逻辑
- Status 状态机
- Status Logs
- Guest IndexedDB 数据模型
- Guest → Cloud Import
- client_sync_id
- Cloud Cache
- Offline Read Fallback
- TanStack Query 业务语义
- User Isolation
- API Contract

3. 不修改任何已经通过 V1 验收的业务规则。

4. 前端页面现有能力必须全部保留。

5. 不引入新的大型 UI Framework。

禁止新增：

- Material UI
- Chakra UI
- Tailwind CSS
- Bootstrap
- Shadcn 全套
- 其他大型 Design System

继续使用：

Ant Design

允许：

- CSS / CSS Modules
- Ant Design theme token
- 少量自定义 SVG
- Ant Design Icons
- 当前已有前端依赖

6. 不为了 UI 改造重构整个项目架构。

7. 不删除现有测试。

8. 不降低测试覆盖要求。

9. 不修改：

v1.0.0

Tag。

10. 不执行：

git reset --hard
git push --force
docker compose down -v
git add .

11. 不误提交：

Prompt/
计划文档
.env
runtime
node_modules
临时截图
测试临时文件

==================================================
二、Git 工作流
==================================================

首先检查：

git status --short
git branch --show-current
git rev-parse HEAD
git remote -v

确认 main 工作区安全。

然后基于最新 main 创建独立分支。

建议：

git switch main
git pull
git switch -c ui-polish-v1.1

如果 main 有未提交的正式代码：

停止并报告。

不要覆盖。

如果只有此前明确保留的未跟踪 Prompt / 计划文档：

保留它们，不删除、不提交。

==================================================
三、第一步先做 Frontend UI Audit
==================================================

开始修改代码前，完整阅读当前前端：

- package.json
- src/
- router
- App
- Layout
- Header
- Dashboard
- Application List
- Application Detail
- Application Form
- Login
- Register
- Company Search / Company Intelligence
- Empty State
- Loading State
- Theme / CSS
- Ant Design ConfigProvider
- ECharts config
- frontend tests

不要先凭经验重写。

输出：

《ApplyPilot Frontend UI Audit》

至少分析：

1. 当前 Layout 结构
2. 页面路由
3. Ant Design 使用方式
4. 全局主题
5. 当前 Header / Navigation
6. Dashboard 信息层级
7. Application 页面
8. Login / Register
9. Company Intelligence
10. Empty State
11. Loading State
12. Responsive
13. 当前视觉问题
14. 可复用组件
15. 哪些地方绝对不应该改

重点判断当前截图中类似的问题：

- 页面大面积纯白
- 视觉层级不足
- 默认 Ant Design 感明显
- Dashboard 顶部缺乏品牌区域
- 数据卡片缺乏焦点
- 图表 Empty State 大面积留白
- 筛选区域像传统后台
- 标题、辅助信息、CTA 层级弱
- 缺乏品牌图形/插画
- 页面缺乏统一 Design Token

完成 Audit 后再实施。

如果发现设计要求与现有代码结构明显冲突：

先报告。

不要强行大改。

==================================================
四、ApplyPilot Design Direction
==================================================

整体设计风格：

Modern SaaS
+
Career Product
+
Light AI Feeling
+
Clean Dashboard

参考气质：

Linear
Notion
现代 AI SaaS Dashboard

但不要直接复制任何产品。

不要做成：

- 政务后台
- ERP
- 传统 Admin Template
- 过度科技蓝
- 大量渐变
- 大量玻璃拟态
- 大量动画
- 游戏 UI
- 炫技页面

整体感觉应该：

专业
年轻
简洁
可信
适合大学生求职
适合秋招项目展示

==================================================
五、Design Tokens
==================================================

优先通过统一 Theme Token / CSS Variables 实现。

推荐设计基础：

Primary:
#4F6EF7

Primary Hover:
#435FE0

Secondary:
#7C5CFC

Page Background:
#F6F8FC

Card Background:
#FFFFFF

Main Text:
#1F2937

Secondary Text:
#6B7280

Muted Text:
#9CA3AF

Border:
#E8ECF4

Success:
#22C55E

Warning:
#F59E0B

Danger:
#EF4444

Info:
#3B82F6

可以根据 Ant Design 实际 token 体系进行小幅调整。

不要在几十个组件里散落 hardcode colors。

优先建立：

theme
tokens
CSS variables

统一：

color
spacing
border radius
shadow
typography

==================================================
六、Border / Radius / Shadow
==================================================

整体避免硬边框。

Card：

border-radius:
12px ～ 16px

Page card shadow：

非常轻。

例如视觉方向：

0 4px 20px rgba(15, 23, 42, 0.05)

不要所有 Card 都有明显阴影。

可以结合：

border
+
subtle shadow

Hover：

轻微上浮即可。

例如：

transform: translateY(-2px)

duration:

150 ～ 200ms

必须尊重：

prefers-reduced-motion

==================================================
七、Typography
==================================================

建立明确的信息层级。

Page Title：

28 ～ 32px

Section Title：

18 ～ 22px

Card Number：

28 ～ 36px

Body：

14 ～ 16px

辅助文字：

12 ～ 14px

中文页面不要过度使用超粗字体。

主要标题可以：

600 / 700

正文：

400 / 500

==================================================
八、Global Application Shell
==================================================

优化整个 ApplyPilot 的应用壳。

优先保留现有路由架构。

推荐：

Top Header
+
Page Content

如果目前没有必要，不要为了美化强制改成大型 Sidebar。

Header 建议：

左：

ApplyPilot Logo / Wordmark

中间：

数据看板
投递记录
企业搜索

根据当前真实页面决定，不新增不存在的业务模块。

右：

当前用户
登录 / 注册
退出

Header：

- sticky 可以考虑
- 白色 / 半透明白
- 底部细边框
- 适当高度
- 清晰 active state

Logo 可以使用简单本地 SVG 图标。

不要引入远程 Logo。

==================================================
九、ApplyPilot 品牌图形
==================================================

为 ApplyPilot 增加一个简洁 Logo Mark。

建议概念：

A
+
路线 / 导航
+
投递箭头

或者：

Paper
+
Arrow
+
Career Route

要求：

- 简单
- 可缩放
- SVG
- 不超过 2～3 个主要视觉元素
- 与 ApplyPilot 蓝紫色系一致

不要：

- 复杂 Logo
- 写实图
- 公司商标
- 网络随机 Logo

允许直接在 frontend assets 下创建：

SVG

==================================================
十、Dashboard Hero
==================================================

当前 Dashboard 顶部视觉过于平。

增加一个 Hero Card。

结构建议：

-----------------------------------------
欢迎回来 👋

掌握每一次投递进度

让求职流程更清晰、更高效。

[新增投递] [智能搜索企业]

                         [Career SVG]
-----------------------------------------

CTA 必须连接现有真实功能。

例如：

新增投递
→ 当前 Application Create flow

智能搜索企业
→ 当前 Company Intelligence 页面

不要创建假按钮。

Hero Background：

非常淡的：

blue / purple gradient

例如：

#EEF2FF
→
#F5F3FF

不要高饱和渐变。

右侧添加：

Career / Resume / Interview / Dashboard

风格的本地 SVG Illustration。

==================================================
十一、Dashboard Illustration
==================================================

本轮允许增加前端图片，但遵守：

优先 SVG。

建议创建：

frontend/src/assets/illustrations/

具体路径根据真实 repo 调整。

可以包含：

dashboard-career.svg
empty-applications.svg
empty-dashboard.svg
auth-career.svg

SVG 应：

- 本地存储
- 自己生成
- 简洁
- 矢量
- 蓝紫色
- 无版权依赖
- 不请求第三方 CDN

禁止使用：

- Unsplash 热链
- 网络随机图片
- 大型 PNG
- 大型 JPEG
- 版权不明确插画
- Base64 巨型图片

==================================================
十二、Dashboard KPI Cards
==================================================

当前：

总投递
进行中
Offer
Offer 获取率
面试通过率
淘汰率

功能全部保留。

重新设计视觉。

每张卡包含：

Icon area
Label
Main Value
Optional secondary hint

例如：

📄
总投递

38

本月新增 12

但辅助数据只有当前 API / 数据模型确实支持时才展示。

禁止伪造：

本周 +12%
较上月 +20%

如果没有真实数据：

不显示。

Icon 建议：

总投递：
File / Send

进行中：
Rocket / Sync

Offer：
Trophy

Offer 获取率：
Rise / Target

面试通过率：
Message / Check

淘汰率：
Fall / Close

使用：

@ant-design/icons

按需 import。

禁止：

import * as Icons

==================================================
十三、Dashboard KPI Responsive
==================================================

Desktop：

6 cards 一行或合理 Grid。

Tablet：

3 × 2

Mobile：

1～2 columns

不要固定宽度导致横向滚动。

==================================================
十四、Dashboard Filter Panel
==================================================

保留全部现有筛选功能：

- search
- status
- company nature
- application type
- industry
- company size
- date range

重新设计筛选区域。

不要所有控件紧挤成一排。

建议：

Card Header：

筛选投递记录

Search 独立占更宽空间。

其他 filter：

responsive grid

Desktop：

4～6 columns

Tablet：

2～3 columns

Mobile：

1 column

适当显示 label。

增加：

重置筛选

但必须调用现有 reset 逻辑。

不要改变 filter semantics。

==================================================
十五、Dashboard Charts
==================================================

保留现有 ECharts。

不要换图表库。

优化：

- chart card header
- title
- subtitle
- spacing
- tooltip
- legend
- grid padding
- Empty State

统一蓝紫主色系。

不要直接使用杂乱的 ECharts 默认 palette。

不同状态仍应该保持可区分。

例如：

进行中：
blue

Offer：
green

Rejected：
red / muted red

Negotiation：
purple

具体根据现有状态枚举合理映射。

不要修改状态枚举。

==================================================
十六、Empty State
==================================================

当前类似：

暂无图表数据

并且存在大片空白。

统一设计 Empty State。

Dashboard Empty：

[SVG]

还没有投递数据

添加第一条投递记录后，
这里会自动生成你的求职数据分析。

[新增投递]

Application Empty：

[SVG]

还没有投递记录

记录你的第一次求职投递，
后续状态变化都会自动保留。

[新增投递]

Search Empty：

没有找到符合条件的投递记录

尝试修改筛选条件。

[清除筛选]

所有按钮必须连接已有逻辑。

==================================================
十七、Application List Page
==================================================

重新设计页面顶部：

投递记录

管理所有求职申请，
追踪从投递到 Offer 的完整流程。

右侧：

[新增投递]

Search / Filter 区域统一 Dashboard 风格。

Application item/card/table：

根据现有实现优化，不强行更换整个信息结构。

视觉层级建议：

Company Name
Job Title

Status Badge

Application Type
Industry
Application Date

Actions

突出：

Company
Job
Status

弱化：

secondary metadata

==================================================
十八、Application Status Badge
==================================================

现有所有 14 个状态业务语义必须保持不变。

只修改视觉。

建立统一：

getStatusVisual(status)

或者现有等价 mapping。

不同类别：

未投递
进行中
Offer
Rejected
Terminated
Signed

使用：

Tag / Badge

颜色体系保持一致。

不要让每个页面自己 hardcode 一套状态颜色。

必须共享。

==================================================
十九、Application Detail
==================================================

优化 Detail Page。

建议页面结构：

Page Header

Company
Job Title
Current Status

[编辑]
[更新状态]

下方：

左侧：

Application Information Card
Status Timeline

右侧：

Company Information
Recruitment Links
Metadata

具体根据当前已有字段实现。

不要创建不存在的 Company 数据。

Status Timeline：

增强视觉：

dot
line
status
timestamp
remark

Current Status 更突出。

==================================================
二十、Application Form
==================================================

保留共享 Application Form。

不要创建：

Guest Form
Cloud Form

两套 UI。

优化：

- field grouping
- label
- spacing
- help text
- section separation
- action buttons

建议分组：

基本信息

公司信息

投递信息

补充信息

但必须基于实际字段。

不要虚构字段。

==================================================
二十一、Login / Register
==================================================

这是重点美化页面。

Desktop 可以采用：

-----------------------------------------
|                     |                 |
| ApplyPilot          | 登录            |
|                     |                 |
| [Career SVG]        | 邮箱 / 用户名   |
|                     | 密码            |
| 让每一次投递        |                 |
| 都有迹可循          | [登录]          |
|                     |                 |
-----------------------------------------

左侧：

品牌区域
Illustration
Slogan

右侧：

Login / Register Card

Mobile：

只显示：

Logo
Title
Form

Illustration 可以隐藏或移动到顶部。

不要因为视觉设计改变认证逻辑。

==================================================
二十二、推荐品牌文案
==================================================

允许使用：

ApplyPilot

掌握每一次投递进度

让求职流程更清晰、更高效

记录投递，追踪进度，走向 Offer

但不要在页面塞过多营销文案。

保持简洁。

==================================================
二十三、Company Intelligence UI
==================================================

Company Intelligence 是项目的重要 AI 能力。

只优化前端表现。

建议：

顶部：

企业智能搜索

搜索企业公开招聘信息，
快速获取官网、招聘入口与企业资料。

Search bar：

明显突出。

搜索结果 Preview：

Company Name
Official Website
Industry
Nature
Size

Recruitment Links

Sources

Verification State

现有：

UNVERIFIED
CANDIDATE
VERIFIED
REJECTED

不得修改其业务含义。

视觉可以使用：

Badge
Tag
Tooltip

Sources 应保持可追溯。

不要隐藏来源。

==================================================
二十四、Company Link Cards
==================================================

招聘链接可以优化为：

校园招聘
官方

[访问招聘页面 ↗]

实习招聘
官方

[访问招聘页面 ↗]

第三方来源：

明确显示：

第三方

不要视觉上伪装成官方。

==================================================
二十五、Loading UX
==================================================

统一优化 Loading。

使用：

Skeleton
Spin
Card Skeleton

避免：

页面整个空白然后突然出现。

Dashboard：

KPI Skeleton
Chart Skeleton

List：

List Skeleton

Detail：

Detail Skeleton

Company Intelligence：

保留：

正在获取企业公开信息，
联网搜索可能需要几十秒...

不要删除原有 Kimi 慢请求提示。

==================================================
二十六、Error UX
==================================================

不要直接显示原始：

AxiosError
stack trace
SQL error

保持现有 error abstraction。

视觉上统一：

Alert
Result
Empty/error state

Offline fallback：

必须继续显示明确：

正在显示最近缓存数据

不得因为视觉改造隐藏 stale 状态。

==================================================
二十七、Offline Notice
==================================================

登录用户读取缓存时：

保留现有：

source = cache
stale = true

或等价逻辑。

UI 可以优化成：

顶部轻量 Alert：

当前网络不可用，正在显示最近缓存的数据。

如果有 cached_at：

显示：

最近缓存：18:05

不要改数据逻辑。

==================================================
二十八、Responsive Design
==================================================

至少验证：

1440px
1024px
768px
375px

重点：

Header
Hero
KPI cards
Filter
Charts
Application List
Detail
Auth

不要求复杂 breakpoint system。

优先使用：

CSS Grid
Flex
Ant Design responsive props

禁止出现：

horizontal overflow
按钮溢出
表单被截断
chart width 0
Hero illustration 挤压文字

==================================================
二十九、Accessibility
==================================================

至少保证：

- Button 有明确 accessible name
- Icon-only button 有 aria-label
- Form label 正确
- Focus 可见
- 对比度合理
- 不仅依靠颜色表达状态
- prefers-reduced-motion
- 图片有合理 alt；纯装饰 SVG 使用 aria-hidden

==================================================
三十、图像资源控制
==================================================

为了避免 bundle 增长：

优先：

SVG

新图片总量保持轻量。

不要增加大型 bitmap。

任何单个 raster asset 如果超过约 300KB：

必须说明原因。

如果没有必要：

不要新增 raster。

SVG 不要包含复杂嵌入 Base64。

==================================================
三十一、Bundle Safety
==================================================

当前已知：

Vite large-chunk warning

Largest chunk 历史约：

1.3 MB raw
428 KB gzip

本轮不是性能阶段。

但 UI 美化不得造成明显恶化。

完成后重新记录：

largest chunk raw
largest chunk gzip
total major chunks

如果 gzip 最大 chunk 增长明显：

调查新增原因。

不要因为新增：

icons
illustrations
UI dependency

导致大幅膨胀。

禁止为了美化新增大型依赖。

==================================================
三十二、Component Strategy
==================================================

优先识别现有重复 UI。

允许抽取少量通用组件，例如：

PageHeader
StatCard
EmptyState
SectionCard
StatusTag
OfflineNotice

但只有存在明显重复时才抽。

不要建立一个新的复杂 Design System。

YAGNI。

==================================================
三十三、CSS Strategy
==================================================

检查当前项目风格后决定：

Global CSS
CSS Module
existing CSS architecture

优先遵循现有结构。

允许新增类似：

styles/tokens.css
styles/global.css
theme.ts

但不要同时建立三套 styling system。

不要在大量 JSX 内写：

style={{ ... }}

除非是动态值。

==================================================
三十四、Ant Design Theme
==================================================

优先利用：

ConfigProvider
theme.token

统一设置：

colorPrimary
colorBgLayout
colorText
colorTextSecondary
borderRadius
fontSize
controlHeight

不要修改 Ant Design 内部私有 class。

避免：

.ant-xxx > div > span:nth-child(...)

这种脆弱 CSS。

==================================================
三十五、动画
==================================================

只允许轻动画：

Card hover
button
page section appearance
skeleton

禁止：

大量 Framer Motion
粒子动画
背景漂浮图标
持续渐变动画
复杂转场

除非项目已经有 motion dependency。

不要为了本 Task 新增大型 animation library。

==================================================
三十六、不要伪造数据
==================================================

非常重要。

不要为了 UI 好看显示假的：

Offer +25%
本周新增 20
成功率提高 18%
AI Score 95
推荐指数
预测 Offer 率

所有数字必须来自真实数据。

没有数据：

使用 Empty State。

==================================================
三十七、不要添加未实现功能
==================================================

禁止增加：

提醒
消息中心
导出
AI 简历
岗位推荐
日历
收藏
PWA
WebSocket
聊天机器人
通知中心

如果 UI 中没有对应真实功能：

不要创建按钮。

==================================================
三十八、Guest Mode 必须保持完整
==================================================

Guest：

IndexedDB = Source of Truth

必须继续支持：

CRUD
Detail
Timeline
Search
Filter
Sort
Dashboard

UI 改造不能导致：

Guest 页面依赖 JWT API。

==================================================
三十九、Logged-in Mode 必须保持完整
==================================================

Logged-in：

PostgreSQL = Source of Truth

IndexedDB：

cache only

UI 改造不得改变。

==================================================
四十、Guest → Cloud Import UX
==================================================

现有：

检测到 X 条本地投递记录

[同步到账号]
[暂不同步]

可以美化 Modal。

但业务行为：

完全不变。

Partial success：

成功记录删除本地
失败记录保留

不得改变。

==================================================
四十一、TDD / Regression 原则
==================================================

这是 UI Task，不要求为每一个 CSS 像素写测试。

但是：

只要修改：

component behavior
navigation
buttons
conditional rendering
responsive logic
empty state actions
loading/error rendering

必须测试。

不要使用大量 brittle snapshot tests。

优先：

React Testing Library
role
text
user interaction

==================================================
四十二、必须保护的测试场景
==================================================

至少确保：

Dashboard renders
Dashboard filter still works
Application list works
Application create CTA works
Application edit works
Status change works
Detail timeline works

Guest mode works

Login works
Register works
Logout works

Company search works
Company preview works

Offline stale notice works

Guest import prompt works

Empty state CTA navigates correctly

Header navigation works

==================================================
四十三、建议新增的 UI Tests
==================================================

根据真实改动选择。

可以包括：

Dashboard hero CTA opens create application flow

Dashboard empty state CTA works

Application empty state clear filter works

Header active route works

StatusTag maps all statuses

OfflineNotice renders only when stale

Auth mobile layout 不需要用像素 snapshot 测试。

==================================================
四十四、Visual Verification
==================================================

如果环境可以运行浏览器 / Playwright：

在 production-like frontend 下截图检查：

Dashboard
Application List
Application Detail
Login
Register
Company Intelligence

至少：

Desktop
Mobile

如果当前没有浏览器自动化能力：

明确写：

Visual Browser Verification:
Not independently automated

不要伪造截图验证。

==================================================
四十五、重点 Dashboard 目标
==================================================

最终 Dashboard 应达到：

顶部：

ApplyPilot Header

Hero：

欢迎回来
掌握每一次投递进度
CTA
Illustration

然后：

KPI Cards

然后：

Filter Card

然后：

Charts Grid

然后：

Trend

整个页面应该：

有层级
有留白
有品牌
但不花哨

==================================================
四十六、建议页面顺序
==================================================

推荐：

Header

↓ 24px

Hero

↓ 24px

KPI Grid

↓ 24px

Filter

↓ 24px

Status / Industry Charts

↓ 24px

Nature / Trend

不要所有模块黏在一起。

==================================================
四十七、实施顺序
==================================================

建议按以下 Task 顺序：

Task 1
Global Theme + Design Tokens

Task 2
Application Shell / Header

Task 3
Dashboard Hero + KPI

Task 4
Dashboard Filters + Charts + Empty States

Task 5
Application List

Task 6
Application Detail + Status Timeline

Task 7
Shared Application Form

Task 8
Login / Register

Task 9
Company Intelligence

Task 10
Responsive + Accessibility

Task 11
Regression + Build + Visual Review

不要同时把所有页面一次性大改。

==================================================
四十八、每个 Task 工作方式
==================================================

每一个 Task：

1. 阅读当前实现
2. 明确最小视觉改动
3. 必要时先补 interaction test
4. 修改
5. targeted tests
6. 检查 UI
7. commit

不要：

一次改 50 个文件
然后最后统一测试。

==================================================
四十九、Commit 建议
==================================================

可以拆为：

style: add ApplyPilot visual theme

feat: polish application shell

feat: redesign dashboard experience

feat: polish application management pages

feat: redesign authentication experience

feat: polish company intelligence interface

fix: improve responsive application layout

不强制严格按这些名称。

保持：

一个 commit 一个清晰目的。

==================================================
五十、最终 Regression
==================================================

必须执行：

frontend full tests

frontend production build

git diff --check

记录：

test count

build result

Vite warning

bundle size

如果本轮完全没有 Backend 修改：

不要为了 UI Task 修改 Backend。

可以不重复真实 Kimi 网络调用。

==================================================
五十一、Backend 保护
==================================================

最后执行：

git diff --name-only

确认本轮主要只涉及：

frontend/

以及必要：

README screenshot / frontend docs

如果出现：

backend/
alembic/
docker database config

必须解释。

没有明确理由：

撤销这些修改。

==================================================
五十二、Secret Audit
==================================================

确认：

没有：

.env
API Key
JWT Secret
password
local runtime

被提交。

SVG 中也不得包含敏感信息。

==================================================
五十三、验收标准
==================================================

最终输出：

# 《ApplyPilot V1.1 UI/UX 美化验收报告》

至少包含：

Git Branch / HEAD

Global Theme                     ✅/❌
Application Shell                ✅/❌
Header Navigation                ✅/❌
Dashboard Hero                   ✅/❌
Dashboard KPI                    ✅/❌
Dashboard Filters                ✅/❌
Dashboard Charts                 ✅/❌
Dashboard Empty State            ✅/❌

Application List                 ✅/❌
Application Detail               ✅/❌
Status Timeline                  ✅/❌
Application Form                 ✅/❌

Login                            ✅/❌
Register                         ✅/❌

Company Intelligence             ✅/❌

Guest Mode Regression            ✅/❌
Cloud Mode Regression            ✅/❌
Offline Fallback UI              ✅/❌
Guest Import UX                  ✅/❌

Responsive Desktop               ✅/❌
Responsive Tablet                ✅/❌
Responsive Mobile                ✅/❌

Accessibility                    ✅/❌

Frontend Full Tests              ✅/❌
Production Build                 ✅/❌
git diff --check                 ✅/❌
Bundle Regression                ✅/❌
Secret Audit                     ✅/❌

==================================================
五十四、报告还必须给出
==================================================

Before：

当前主要视觉问题。

After：

具体完成：

- Theme
- Header
- Hero
- Cards
- Filters
- Charts
- Empty States
- Illustrations
- Auth
- Detail
- Company Intelligence
- Responsive

Assets：

列出新增：

SVG
Icons
Images

Bundle：

Before
After

说明是否明显增长。

Tests：

通过数量。

==================================================
五十五、最终判断
==================================================

只有：

所有核心业务流程无回归
+
Frontend full tests 通过
+
Build 通过
+
视觉改造完整
+
没有明显 bundle regression

才可以写：

✅ ApplyPilot V1.1 UI/UX Polish Passed

否则：

⚠️ UI/UX Polish 未完全通过

明确 Blocker。

==================================================
五十六、重要停止条件
==================================================

完成 UI/UX 美化后停止。

不要自行：

merge main
push main
创建 v1.1.0 tag
删除 branch
进入新功能开发

等待我验收。

==================================================
五十七、最终原则
==================================================

本轮的核心原则：

功能不变
数据不变
接口不变
架构不变

只提升：

视觉层级
品牌感
一致性
可读性
响应式
Empty State
Loading UX
展示效果

目标不是做一个“炫酷网页”。

目标是：

让 ApplyPilot 看起来像一个真正可以发布和演示的求职 SaaS 产品。

开始时：

先完成 Frontend UI Audit。

然后按 Task 顺序逐步实施。

任何时候如果 UI 改动需要修改 Backend Contract：

停止并报告，不要自行修改 Backend。