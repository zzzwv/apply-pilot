import { useEffect, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Button, Card, Col, DatePicker, Empty, Input, Row, Select, Space, Statistic, Typography } from "antd";
import dayjs from "dayjs";

import {
  getApplicationTrend,
  getCompanyNatureDistribution,
  getDashboardSummary,
  getIndustryDistribution,
  getStatusDistribution,
} from "../../api/dashboard";
import { DashboardChart } from "../../components/DashboardChart";
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

function MetricCard({ label, value, loading, percent }: { label: string; value: number; loading: boolean; percent?: boolean }) {
  return <Card size="small"><Statistic title={label} value={percent ? rate(value) : value} loading={loading} /></Card>;
}

function ChartCard({ title, error, children }: { title: string; error: boolean; children: React.ReactNode }) {
  return <Card title={title} style={{ height: "100%" }}>{error ? <Empty description="图表加载失败" /> : children}</Card>;
}

export function DashboardPage() {
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
  const queryOptions = { placeholderData: keepPreviousData };
  const guestDashboard = () => guestDataSource.dashboard(filters);
  const summary = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", "summary", filters], queryFn: () => guest ? guestDashboard().then((data) => data.summary) : getDashboardSummary(filters), ...queryOptions });
  const statuses = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", "status", filters], queryFn: () => guest ? guestDashboard().then((data) => data.statuses) : getStatusDistribution(filters), ...queryOptions });
  const industries = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", "industry", filters], queryFn: () => guest ? guestDashboard().then((data) => data.industries) : getIndustryDistribution(filters), ...queryOptions });
  const natures = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", "company-nature", filters], queryFn: () => guest ? guestDashboard().then((data) => data.natures) : getCompanyNatureDistribution(filters), ...queryOptions });
  const trend = useQuery({ queryKey: ["dashboard", guest ? "guest" : "cloud", "trend", filters, granularity], queryFn: () => guest ? guestDashboard().then((data) => data.trend) : getApplicationTrend(filters, granularity), ...queryOptions });
  const refetchAll = () => void Promise.all([summary.refetch(), statuses.refetch(), industries.refetch(), natures.refetch(), trend.refetch()]);
  const hasFilters = Object.values(filters).some((value) => Array.isArray(value) ? value.length : Boolean(value));
  const charts = useMemo(() => ({
    status: statusDistributionOption(statuses.data ?? []),
    industry: industryDistributionOption(industries.data ?? []),
    nature: companyNatureOption(natures.data ?? []),
    trend: trendOption(trend.data ?? []),
  }), [statuses.data, industries.data, natures.data, trend.data]);
  const data = summary.data;

  return <section>
    <Space style={{ width: "100%", justifyContent: "space-between", marginBottom: 16 }}>
      <Typography.Title level={2}>求职投递数据看板</Typography.Title>
      <Button onClick={refetchAll} loading={summary.isFetching} aria-label="刷新数据">刷新数据</Button>
    </Space>
    <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
      <Col xs={12} md={8} lg={4}><MetricCard label="总投递" value={data?.total ?? 0} loading={summary.isLoading} /></Col>
      <Col xs={12} md={8} lg={4}><MetricCard label="进行中" value={data?.in_progress ?? 0} loading={summary.isLoading} /></Col>
      <Col xs={12} md={8} lg={4}><MetricCard label="Offer" value={data?.offer_count ?? 0} loading={summary.isLoading} /></Col>
      <Col xs={12} md={8} lg={4}><MetricCard label="Offer 获取率" value={data?.offer_rate ?? 0} loading={summary.isLoading} percent /></Col>
      <Col xs={12} md={8} lg={4}><MetricCard label="面试通过率" value={data?.interview_rate ?? 0} loading={summary.isLoading} percent /></Col>
      <Col xs={12} md={8} lg={4}><MetricCard label="淘汰率" value={data?.rejection_rate ?? 0} loading={summary.isLoading} percent /></Col>
    </Row>
    <Card title="筛选条件" style={{ marginBottom: 16 }}>
      <Space wrap>
        <Input allowClear placeholder="搜索公司、岗位、行业、企业性质或备注" style={{ width: 280 }} value={keywordInput} onChange={(event) => setKeywordInput(event.target.value)} />
        <Select allowClear mode="multiple" placeholder="投递状态" style={{ minWidth: 150 }} options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} value={filters.status} onChange={(value: ApplicationStatus[]) => updateFilters({ status: value.length ? value : undefined })} />
        <Select allowClear mode="multiple" placeholder="企业性质" style={{ minWidth: 130 }} options={natureOptions.map(([value, label]) => ({ value, label }))} value={filters.company_nature} onChange={(value: string[]) => updateFilters({ company_nature: value.length ? value : undefined })} />
        <Select allowClear mode="multiple" placeholder="投递类型" style={{ minWidth: 130 }} options={Object.entries(applicationTypeLabels).map(([value, label]) => ({ value, label }))} value={filters.application_type} onChange={(value: ApplicationType[]) => updateFilters({ application_type: value.length ? value : undefined })} />
        <Select allowClear mode="tags" placeholder="行业" style={{ minWidth: 130 }} value={filters.industry} onChange={(value: string[]) => updateFilters({ industry: value.length ? value : undefined })} />
        <Select allowClear mode="multiple" placeholder="企业规模" style={{ minWidth: 130 }} options={sizeOptions.map((value) => ({ value, label: value }))} value={filters.company_size} onChange={(value: string[]) => updateFilters({ company_size: value.length ? value : undefined })} />
        <DatePicker.RangePicker value={filters.date_from && filters.date_to ? [dayjs(filters.date_from), dayjs(filters.date_to)] : undefined} onChange={(value) => updateFilters({ date_from: value?.[0]?.format("YYYY-MM-DD"), date_to: value?.[1]?.format("YYYY-MM-DD") })} />
        {hasFilters && <Button onClick={() => { setKeywordInput(""); setFilters(initialFilters); }}>清空筛选</Button>}
      </Space>
    </Card>
    {!summary.isLoading && data?.total === 0 ? <Empty description={hasFilters ? "暂无匹配投递记录" : "暂无投递记录"} /> : <Row gutter={[16, 16]}>
      <Col xs={24} lg={12}><ChartCard title="投递状态分布" error={statuses.isError}><DashboardChart ariaLabel="投递状态分布图" option={charts.status} isEmpty={!statuses.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="行业投递分布" error={industries.isError}><DashboardChart ariaLabel="行业投递分布图" option={charts.industry} isEmpty={!industries.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="企业性质分布" error={natures.isError}><DashboardChart ariaLabel="企业性质分布图" option={charts.nature} isEmpty={!natures.data?.length} /></ChartCard></Col>
      <Col xs={24} lg={12}><ChartCard title="投递趋势" error={trend.isError}>
        <Space style={{ marginBottom: 8 }}><Button type={granularity === "day" ? "primary" : "default"} onClick={() => setGranularity("day")}>按日</Button><Button type={granularity === "week" ? "primary" : "default"} onClick={() => setGranularity("week")}>按周</Button></Space>
        <DashboardChart ariaLabel="投递趋势图" option={charts.trend} isEmpty={!trend.data?.length} />
      </ChartCard></Col>
    </Row>}
  </section>;
}
