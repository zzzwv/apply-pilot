# ApplyPilot V1.1 UI/UX Design

## Goal

在不改变任何业务规则、数据模型、API contract 或离线语义的前提下，将 ApplyPilot V1 的默认 Ant Design 管理界面升级为清爽、可信、适合求职场景演示的现代 AI SaaS 界面。

## Scope and non-goals

本次仅修改 `frontend/` 中的视觉层、展示组件和为展示行为增加的测试。后端、数据库、迁移、Docker、Kimi pipeline、JWT、TanStack Query 查询键与语义、Guest IndexedDB、Guest 导入、Cloud cache 和 offline fallback 均不修改。

不会新增业务页面、提醒、导出、日历、推荐、通知、PWA、WebSocket 或新的大型 UI 框架。继续使用 React、Ant Design、ECharts、React Router、现有图标包和本地 SVG；不使用远程图片或新增大型依赖。

## Design language

采用低饱和蓝紫色的现代 SaaS 视觉。页面底色为 `#F6F8FC`，内容卡为白色，主要文字为 `#1F2937`，次级文字为 `#6B7280`，边框为 `#E8ECF4`。主色为 `#4F6EF7`，hover 为 `#435FE0`，辅助紫为 `#7C5CFC`；成功、警告、错误和信息色分别为 `#22C55E`、`#F59E0B`、`#EF4444`、`#3B82F6`。

卡片使用 12--16px 圆角、细边框与极轻阴影；悬停仅允许 150--200ms 的轻微上移，且在 `prefers-reduced-motion: reduce` 下关闭。标题层级为页面 28--32px、区块 18--22px、指标 28--36px，避免过重字重。禁止大面积高饱和渐变、玻璃拟态、持续动画和伪造业务数据。

## Architecture

`main.tsx` 继续提供 QueryClient 与 BrowserRouter。`App.tsx` 继续持有路由、认证 bootstrap 和 Guest import prompt，但引入 Ant Design `ConfigProvider` token 配置及一个共享的应用壳。全局样式只建立一种体系：CSS Variables + 一个全局样式入口；动态尺寸仍通过组件 props 表达。

仅在重复视觉确实存在时抽取小型展示组件：品牌标识、应用 Header、页面标题、区块卡片、空状态、状态标签和离线提示。它们不得封装 API、数据源、认证或缓存逻辑。现有 `ApplicationForm` 仍是 Guest 与 Cloud 共用的唯一表单；现有 DataSource、mutation、query key、status enum 和所有回调保持不变。

## Application shell and navigation

新增本地 SVG Logo Mark，概念为字母 A、投递箭头和路径，不引用第三方品牌。桌面端 Header 左侧显示 ApplyPilot 标识，中部仅显示真实路由“数据看板”“投递记录”，右侧保留既有登录、注册、用户信息和退出能力。active state 由当前路由决定；Header 可粘性展示，并在小屏幕改为可换行/紧凑导航，不出现横向溢出。

登录与注册保留 Header 触发 Modal、字段、验证、错误文案与 Zustand 调用。Modal 内加入品牌文案和轻量 SVG 视觉区域；不新增 `/login` 或 `/register` 路由。

## Dashboard

Dashboard 顶部增加 Hero Card，文案为“欢迎回来”“掌握每一次投递进度”，CTA 只调用既有流程：新增投递跳转/开启现有创建入口，企业智能搜索只在现有 Cloud 表单能力可达时呈现，不创建假模块。Hero 使用淡蓝紫背景和本地 career SVG。

六项现有 KPI 原样使用真实 summary 数据，每张卡增加按需导入的 Ant Design icon、标签和数值，绝不添加增长率等虚构信息。筛选保留 keyword、status、nature、type、industry、size 和日期范围，改为带标签的响应式网格；重置只调用当前清空逻辑。图表继续使用 ECharts，统一 palette、tooltip、legend 和 padding，状态颜色从共享状态视觉映射获得。

无数据时 Dashboard 和图表使用本地 SVG 及明确说明；“新增投递”“清除筛选”按钮只连接现有行为。加载状态使用与布局相符的 Skeleton；错误继续通过现有 error abstraction 展示。

## Application management

列表页保留查询、筛选、排序、分页、创建、编辑、删除、Guest/Cloud source 与 stale alert。新增 Page Header、筛选 Card 与视觉更清晰的表格，但不替换数据结构。没有数据时，初始空状态提供现有“新增投递”动作；筛选无结果时只提供现有清空筛选动作。

详情页以突出岗位、企业和当前状态的 Header 开头，使用响应式两栏/单栏信息布局；状态更新控件、Guest 编辑/删除、Timeline、链接和离线提示均保持原有条件与回调。时间线仅改 dot、line、时间和备注的展示。

`ApplicationForm` 在同一个 Drawer 中按真实字段分为基本信息、企业信息、投递信息和补充信息；Guest 与 Cloud 仅使用既有条件渲染，不能形成两套表单逻辑。

共享 `StatusTag` 必须覆盖全部 14 个状态，按“未投递、进行中、Offer、淘汰/终止、已签约”等类别提供一致色彩与文字；页面和 ECharts 不再各自硬编码颜色，状态枚举与标签文本不变。

## Company intelligence, cache, loading and errors

企业智能字段保留联网搜索、慢请求提示、部分结果提示、手动企业创建、来源、招聘链接、验证状态以及确认流程。仅把预览、来源和链接改为信息卡，第三方来源保持可辨识且不伪装为官方。

Cloud stale fallback 的 `source = cache`、`stale = true` 和 `cached_at` 语义保持。列表和详情仍显示“当前网络不可用，正在显示最近缓存的数据”的明显 Alert；视觉改造不得隐藏它。Guest import Modal 的同步、取消、partial success 和删除本地记录时机完全不变。

## Assets and bundle budget

新资源仅为若干手写、本地、无 Base64 的简洁 SVG：Logo Mark、dashboard career、empty applications、empty dashboard、auth career。单个资源保持极小；不新增 raster 图片、CDN 资源或依赖。生产构建后记录最大 raw/gzip chunk 与 major chunk 数量，并与 V1 基线（最大约 1.35MB raw / 428KB gzip）比较；没有明显增长才通过。

## Responsiveness and accessibility

在 1440、1024、768、375px 验证 Header、Hero、KPI、筛选、图表、表格、Drawer、详情和认证 Modal。KPI 由 6 列过渡为 3x2 和 1--2 列；筛选由网格过渡为单列；图表始终有有效宽高。不得产生页面横向滚动、被截断按钮或 width 0 图表。

所有按钮有清晰文字或 `aria-label`，纯装饰 SVG 使用 `aria-hidden`，信息 SVG 有合理替代文本；表单保留 label；焦点可见；状态不只依赖颜色；色彩对比可读。

## Test and verification strategy

不删除现有测试。任何改变导航、CTA、条件渲染、空状态、状态标签或 loading/error 行为的组件，先写 React Testing Library 交互测试并观察其因缺少新行为失败，再写最小实现。至少覆盖 Header active navigation、Dashboard Hero CTA、Dashboard/列表空状态 CTA、所有状态视觉映射、Guest CRUD、登录/注册/登出、Company Intelligence、offline stale notice 与 Guest import prompt。

完成时执行 frontend full tests、production build、`git diff --check`、bundle 比较和 secret audit；确认本轮 diff 仅涉及 `frontend/` 及本设计/计划文档。若无可用自动化浏览器，报告“Visual Browser Verification: Not independently automated”，不可伪造截图验证。
