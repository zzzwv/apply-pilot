import { useEffect, useMemo, useState, type ReactNode } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Button, Card, Col, DatePicker, Input, Row, Select, Space, Statistic } from "antd";
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  ReloadOutlined,
  RiseOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";

import {
  getApplicationTrend,
  getCompanyNatureDistribution,
  getDashboardSummary,
  getIndustryDistribution,
  getStatusDistribution,
} from "../../api/dashboard";
import { DashboardChart } from "../../components/DashboardChart";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import dashboardCareer from "../../assets/illustrations/dashboard-career.svg";
import emptyDashboard from "../../assets/illustrations/empty-dashboard.svg";
import { applicationTypeLabels, statusLabels, type ApplicationStatus, type ApplicationType } from "../../types/application";
import type { DashboardFilters, TrendGranularity } from "../../types/dashboard";
import { companyNatureOption, industryDistributionOption, statusDistributionOption, trendOption } from "./chartOptions";
import { useAuthStore } from "../../store/auth";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";

const guestDataSource = new LocalApplicationDataSource();

const initialFilters: DashboardFilters = {};
const natureOptions = [["STATE_OWNED", "国企"], ["CENTRAL_OWNED", "央企"], ["PRIVATE", "私企"], ["FOREIGN", "外企"], ["JOINT_VENTURE", "合资"], ["STARTUP", "初创"]];
const sizeOptions = ["50以下", "50-200", "200-500", "500-1000", "1000-5000", "5000以上"];
const rate = (value: number) => `${(value * 100).toFixed(1)}%`;

function MetricCard({ label, value, loading, percent, icon }: { label: string; value: number; loading: boolean; percent?: boolean; icon: ReactNode }) {
  return <Card size="small" className="dashboard-metric-card"><Statistic title={label} value={percent ? rate(value) : value} loading={loading} prefix={<span className="dashboard-metric-card__icon" aria-hidden="true">{icon}</span>} /></Card>;
}

function ChartCard({ title, subtitle, error, children }: { title: string; subtitle: string; error: boolean; children: ReactNode }) {
  return <Card className="dashboard-chart-card" title={<div><div className="dashboard-chart-card__title">{title}</div><div className="dashboard-chart-card__subtitle">{subtitle}</div></div>} style={{ height: "100%" }}>{error ? <EmptyState image={{ src: emptyDashboard, alt: "图表加载失败" }} title="图表加载失败" description="请刷新数据后重试。" /> : children}</Card>;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, initialized } = useAuthStore();
  const guest = initialized && !user;
  const [keywordInput, setKeywordInput] = useState("");
  const [filters, setFilters] = useState<DashboardFilters>(initialFilters);
  const [granularity, setGranularity] = useState<TrendGranularity>("day");
  useEffect(() => {
    const timer = window.setTimeout(() => setFilters((current) => ({ ...current, keyword: keywordInput.trim() || undefined })), 300);
    return () => window.clearTimeout(timer);
  }, [keywordInput]);
  const updateFilters = (updates: Partial<DashboardFilters>) => setFilters((current) => ({ ...current, ...updates }));
  const queryOptions = { placeholderData: guest ? keepPreviousData : undefined, enabled: initialized };
  const guestDashboard = () => guestDataSource.dashboard(filters);
  const summary = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", user?.id, "summary", filters], queryFn: () => guest ? guestDashboard().then((data) => data.summary) : getDashboardSummary(filters), ...queryOptions });
  const statuses = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", user?.id, "status", filters], queryFn: () => guest ? guestDashboard().then((data) => data.statuses) : getStatusDistribution(filters), ...queryOptions });
  const industries = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", user?.id, "industry", filters], queryFn: () => guest ? guestDashboard().then((data) => data.industries) : getIndustryDistribution(filters), ...queryOptions });
  const natures = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", user?.id, "company-nature", filters], queryFn: () => guest ? guestDashboard().then((data) => data.natures) : getCompanyNatureDistribution(filters), ...queryOptions });
  const trend = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", user?.id, "trend", filters, granularity], queryFn: () => guest ? guestDashboard().then((data) => data.trend) : getApplicationTrend(filters, granularity), ...queryOptions });
  const refetchAll = () => void Promise.all([summary.refetch(), statuses.refetch(), industries.refetch(), natures.refetch(), trend.refetch()]);
  const clearFilters = () => {
    setKeywordInput("");
    setFilters(initialFilters);
  };
  const openCreate = () => navigate("/applications", { state: { openCreate: true } });
  const hasFilters = Object.values(filters).some((value) => Array.isArray(value) ? value.length : Boolean(value));
  const charts = useMemo(() => ({
    status: statusDistributionOption(statuses.data ?? []),
    industry: industryDistributionOption(industries.data ?? []),
    nature: companyNatureOption(natures.data ?? []),
    trend: trendOption(trend.data ?? []),
  }), [statuses.data, industries.data, natures.data, trend.data]);
  const industryOptions = useMemo(
    () => (industries.data ?? [])
      .filter((item) => item.industry !== "UNKNOWN")
      .map((item) => ({ value: item.industry, label: item.industry })),
    [industries.data],
  );
  const data = summary.data;

  return <section className="dashboard-page">
    <Card className="dashboard-hero" variant="borderless">
      <div className="dashboard-hero__content">
        <PageHeader
          title="欢迎回来"
          description="掌握每一次投递进度"
          extra={<div className="dashboard-hero__actions"><Button type="primary" onClick={openCreate}>新增投递</Button><Button icon={<ReloadOutlined />} onClick={refetchAll} loading={summary.isFetching} aria-label="刷新数据">刷新数据</Button></div>}
        />
      </div>
      <img className="dashboard-hero__image" src={dashboardCareer} alt="" aria-hidden="true" />
    </Card>
    <Row gutter={[16, 16]} className="dashboard-metrics">
      <Col xs={12} md={8} xl={4}><MetricCard label="总投递" value={data?.total ?? 0} loading={summary.isLoading} icon={<FileTextOutlined />} /></Col>
      <Col xs={12} md={8} xl={4}><MetricCard label="进行中" value={data?.in_progress ?? 0} loading={summary.isLoading} icon={<RiseOutlined />} /></Col>
      <Col xs={12} md={8} xl={4}><MetricCard label="Offer" value={data?.offer_count ?? 0} loading={summary.isLoading} icon={<TrophyOutlined />} /></Col>
      <Col xs={12} md={8} xl={4}><MetricCard label="Offer 获取率" value={data?.offer_rate ?? 0} loading={summary.isLoading} percent icon={<TrophyOutlined />} /></Col>
      <Col xs={12} md={8} xl={4}><MetricCard label="面试通过率" value={data?.interview_rate ?? 0} loading={summary.isLoading} percent icon={<CheckCircleOutlined />} /></Col>
      <Col xs={12} md={8} xl={4}><MetricCard label="淘汰率" value={data?.rejection_rate ?? 0} loading={summary.isLoading} percent icon={<CloseCircleOutlined />} /></Col>
    </Row>
    <Card title="筛选条件" className="dashboard-filters">
      <div className="dashboard-filter-grid">
        <div className="dashboard-filter-field dashboard-filter-field--keyword"><label htmlFor="dashboard-keyword">关键词</label><Input id="dashboard-keyword" allowClear placeholder="搜索公司、岗位、行业、企业性质或备注" value={keywordInput} onChange={(event) => setKeywordInput(event.target.value)} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-status">投递状态</label><Select id="dashboard-status" aria-label="投递状态" allowClear mode="multiple" placeholder="投递状态" options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} value={filters.status} onChange={(value: ApplicationStatus[]) => updateFilters({ status: value.length ? value : undefined })} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-company-nature">企业性质</label><Select id="dashboard-company-nature" aria-label="企业性质" allowClear mode="multiple" placeholder="企业性质" options={natureOptions.map(([value, label]) => ({ value, label }))} value={filters.company_nature} onChange={(value: string[]) => updateFilters({ company_nature: value.length ? value : undefined })} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-application-type">投递类型</label><Select id="dashboard-application-type" aria-label="投递类型" allowClear mode="multiple" placeholder="投递类型" options={Object.entries(applicationTypeLabels).map(([value, label]) => ({ value, label }))} value={filters.application_type} onChange={(value: ApplicationType[]) => updateFilters({ application_type: value.length ? value : undefined })} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-industry">行业</label><Select id="dashboard-industry" aria-label="行业" allowClear mode="tags" placeholder="行业" options={industryOptions} value={filters.industry} onChange={(value: string[]) => updateFilters({ industry: value.length ? value : undefined })} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-company-size">企业规模</label><Select id="dashboard-company-size" aria-label="企业规模" allowClear mode="multiple" placeholder="企业规模" options={sizeOptions.map((value) => ({ value, label: value }))} value={filters.company_size} onChange={(value: string[]) => updateFilters({ company_size: value.length ? value : undefined })} /></div>
        <div className="dashboard-filter-field"><label htmlFor="dashboard-date-range-start">投递日期</label><DatePicker.RangePicker id={{ start: "dashboard-date-range-start", end: "dashboard-date-range-end" }} aria-label="投递日期" value={filters.date_from && filters.date_to ? [dayjs(filters.date_from), dayjs(filters.date_to)] : undefined} onChange={(value) => updateFilters({ date_from: value?.[0]?.format("YYYY-MM-DD"), date_to: value?.[1]?.format("YYYY-MM-DD") })} /></div>
        {hasFilters && <div className="dashboard-filter-field dashboard-filter-field--action"><span>筛选操作</span><Button onClick={clearFilters}>清空筛选</Button></div>}
      </div>
    </Card>
    {!summary.isLoading && data?.total === 0 ? <EmptyState image={{ src: emptyDashboard, alt: hasFilters ? "没有匹配的投递记录" : "还没有投递记录" }} title={hasFilters ? "暂无匹配投递记录" : "还没有投递记录"} description={hasFilters ? "试试调整筛选条件，或清空筛选查看全部记录。" : "从第一条投递记录开始，持续掌握求职进度。"} action={<Button type="primary" onClick={hasFilters ? clearFilters : openCreate}>{hasFilters ? "清空筛选" : "新增投递"}</Button>} /> : <Row gutter={[16, 16]} className="dashboard-charts">
      <Col xs={24} lg={12}><ChartCard title="投递状态分布" subtitle="了解当前流程所处阶段" error={statuses.isError}><DashboardChart ariaLabel="投递状态分布图" option={charts.status} isEmpty={!statuses.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="行业投递分布" subtitle="查看机会集中在哪些领域" error={industries.isError}><DashboardChart ariaLabel="行业投递分布图" option={charts.industry} isEmpty={!industries.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="企业性质分布" subtitle="了解投递目标的企业类型" error={natures.isError}><DashboardChart ariaLabel="企业性质分布图" option={charts.nature} isEmpty={!natures.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="投递趋势" subtitle="按时间回顾投递节奏" error={trend.isError}>
        <Space className="dashboard-chart-card__controls"><Button type={granularity === "day" ? "primary" : "default"} onClick={() => setGranularity("day")}>按日</Button><Button type={granularity === "week" ? "primary" : "default"} onClick={() => setGranularity("week")}>按周</Button></Space>
        <DashboardChart ariaLabel="投递趋势图" option={charts.trend} isEmpty={!trend.data?.length} />
      </ChartCard></Col>
    </Row>}
  </section>;
}
