import { useEffect, useMemo, useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, DatePicker, Input, Popconfirm, Select, Space, Table, message } from "antd";
import dayjs from "dayjs";
import { Link, useLocation } from "react-router-dom";

import { createApplication, deleteApplication, listApplications, toApplicationUpdate, updateApplication } from "../../api/applications";
import { ApplicationForm } from "../../components/ApplicationForm";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { StatusTag } from "../../components/StatusTag";
import { useUiStore } from "../../store/ui";
import { useAuthStore } from "../../store/auth";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";
import { CloudApplicationCache, writeCloudCacheSafely } from "../../data/cloudApplicationCache";
import { CloudApplicationDataSource, isRecoverableReadFailure } from "../../data/cloudApplicationDataSource";
import emptyApplications from "../../assets/illustrations/empty-applications.svg";
import type { GuestApplicationInput } from "../../local-db/applicationRepository";
import {
  applicationTypeLabels,
  statusLabels,
  type Application,
  type ApplicationInput,
  type ApplicationListParams,
  type ApplicationSort,
  type ApplicationStatus,
  type ApplicationType,
} from "../../types/application";

const applicationsKey = ["applications"] as const;
const natureOptions = [
  ["STATE_OWNED", "国企"],
  ["CENTRAL_OWNED", "央企"],
  ["PRIVATE", "私企"],
  ["FOREIGN", "外企"],
  ["JOINT_VENTURE", "合资"],
  ["STARTUP", "初创"],
];
const sizeOptions = ["50以下", "50-200", "200-500", "500-1000", "1000-5000", "5000以上"];
const sortOptions: { value: ApplicationSort; label: string }[] = [
  { value: "application_date_desc", label: "投递时间：最新优先" },
  { value: "application_date_asc", label: "投递时间：最早优先" },
  { value: "company_name_asc", label: "企业名称" },
  { value: "status_priority_desc", label: "状态优先级" },
];
const initialParams: ApplicationListParams = { sort: "application_date_desc", page: 1, page_size: 20 };
const guestDataSource = new LocalApplicationDataSource();

export function ApplicationsPage() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const { user, initialized } = useAuthStore();
  const guest = initialized && !user;
  const cloudCache = useMemo(() => user ? new CloudApplicationCache(user.id) : undefined, [user?.id]);
  const cloudDataSource = useMemo(() => user ? new CloudApplicationDataSource(user.id) : undefined, [user?.id]);
  const { applicationDrawerOpen, setApplicationDrawerOpen } = useUiStore();
  const [editing, setEditing] = useState<Application>();
  const [keywordInput, setKeywordInput] = useState("");
  const [params, setParams] = useState<ApplicationListParams>(initialParams);
  const locationState = location.state as { editApplication?: Application; openCreate?: boolean } | null;
  const pendingEdit = locationState?.editApplication;
  const openCreate = locationState?.openCreate;
  useEffect(() => {
    if (pendingEdit) {
      setEditing(pendingEdit);
      setApplicationDrawerOpen(true);
    } else if (openCreate) {
      setApplicationDrawerOpen(true);
    }
  }, [openCreate, pendingEdit, setApplicationDrawerOpen]);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setParams((current) => ({ ...current, keyword: keywordInput.trim() || undefined, page: 1 }));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keywordInput]);
  const applications = useQuery({
    queryKey: [...applicationsKey, guest ? "guest" : "cloud", user?.id, params],
    queryFn: async () => {
      if (guest) return { data: await guestDataSource.list(params), source: "cloud" as const, stale: false };
      return cloudDataSource!.list(params);
    },
    enabled: initialized,
    placeholderData: guest ? keepPreviousData : undefined,
  });
  const invalidateAfterCloudMutation = () => Promise.all([
    queryClient.invalidateQueries({ queryKey: applicationsKey }),
    queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
  ]);
  const createMutation = useMutation({
    mutationFn: async (payload: ApplicationInput | GuestApplicationInput) => {
      if (guest) return guestDataSource.create(payload as GuestApplicationInput);
      const response = await createApplication(payload as ApplicationInput);
      if (cloudCache) void writeCloudCacheSafely(() => cloudCache.upsertApplication(response));
      return response;
    },
    onSuccess: () => invalidateAfterCloudMutation(),
  });
  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: Partial<ApplicationInput> }) => {
      if (guest) return guestDataSource.update(id, payload);
      const response = await updateApplication(id, payload);
      if (cloudCache) void writeCloudCacheSafely(() => cloudCache.upsertApplication(response));
      return response;
    },
    onSuccess: () => invalidateAfterCloudMutation(),
  });
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      if (guest) return guestDataSource.remove(id).then(() => ({ deleted_count: 1 }));
      const response = await deleteApplication(id);
      if (cloudCache) void writeCloudCacheSafely(() => cloudCache.removeApplication(id));
      return response;
    },
    onSuccess: () => invalidateAfterCloudMutation(),
    onError: (error) => message.error(isRecoverableReadFailure(error) ? "当前网络不可用，请恢复网络后再修改" : "删除失败，请检查登录状态"),
  });
  const items = applications.data?.data.items ?? [];
  const updateFilters = (updates: Partial<ApplicationListParams>) => {
    setParams((current) => ({ ...current, ...updates, page: 1 }));
  };
  const clearFilters = () => {
    setKeywordInput("");
    setParams(initialParams);
  };
  const hasActiveFilters = Boolean(
    params.keyword || params.status?.length || params.company_nature?.length ||
    params.application_type?.length || params.industry?.length || params.date_from ||
    params.date_to || params.company_size?.length || params.sort !== "application_date_desc",
  );

  const closeDrawer = () => {
    setEditing(undefined);
    setApplicationDrawerOpen(false);
  };

  const openCreateDrawer = () => setApplicationDrawerOpen(true);

  const submit = async (payload: ApplicationInput | GuestApplicationInput) => {
    try {
      if (editing) await updateMutation.mutateAsync({ id: editing.id, payload: toApplicationUpdate(payload as ApplicationInput) });
      else await createMutation.mutateAsync(payload);
      message.success("投递记录已保存");
      closeDrawer();
    } catch (error) {
      message.error(isRecoverableReadFailure(error) ? "当前网络不可用，请恢复网络后再修改" : "保存失败，请检查输入或登录状态");
    }
  };

  const columns = [
    { title: "企业", key: "company", render: (_: unknown, record: Application) => record.company.short_name || record.company.full_name },
    { title: "岗位", dataIndex: "job_title" },
    { title: "投递类型", dataIndex: "application_type", render: (value: Application["application_type"]) => applicationTypeLabels[value] },
    { title: "投递时间", dataIndex: "application_date" },
    { title: "当前状态", dataIndex: "current_status", render: (value: Application["current_status"]) => <StatusTag status={value} /> },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, record: Application) => (
        <Space>
          <Link to={`/applications/${record.id}`}>查看</Link>
          <Button type="link" onClick={() => { setEditing(record); setApplicationDrawerOpen(true); }}>编辑</Button>
          <Popconfirm title="确认删除这条投递记录？" onConfirm={() => deleteMutation.mutate(record.id)}><Button danger type="link">删除</Button></Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <section className="applications-page">
      <PageHeader
        title="投递记录"
        description="集中管理每一份投递，持续掌握求职进度。"
        extra={<Button type="primary" onClick={openCreateDrawer}>新增投递</Button>}
      />
      {applications.data?.stale && <Alert type="warning" showIcon message={applications.data.cached_at ? `当前网络不可用，正在显示 ${new Date(applications.data.cached_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} 缓存的数据。` : "当前网络不可用，正在显示最近缓存的数据。"} style={{ marginBottom: 16 }} />}
      <Card title="筛选条件" className="applications-filters">
        <div className="applications-filter-grid">
          <div className="applications-filter-field applications-filter-field--keyword">
            <label htmlFor="applications-keyword">关键词</label>
            <Input id="applications-keyword" allowClear placeholder="搜索公司、岗位、行业、企业性质或备注" value={keywordInput} onChange={(event) => setKeywordInput(event.target.value)} />
          </div>
          <div className="applications-filter-field"><span>投递状态</span><Select allowClear mode="multiple" placeholder="投递状态" options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} value={params.status} onChange={(value: ApplicationStatus[]) => updateFilters({ status: value.length ? value : undefined })} /></div>
          <div className="applications-filter-field"><span>企业性质</span><Select allowClear mode="multiple" placeholder="企业性质" options={natureOptions.map(([value, label]) => ({ value, label }))} value={params.company_nature} onChange={(value: string[]) => updateFilters({ company_nature: value.length ? value : undefined })} /></div>
          <div className="applications-filter-field"><span>投递类型</span><Select allowClear mode="multiple" placeholder="投递类型" options={Object.entries(applicationTypeLabels).map(([value, label]) => ({ value, label }))} value={params.application_type} onChange={(value: ApplicationType[]) => updateFilters({ application_type: value.length ? value : undefined })} /></div>
          <div className="applications-filter-field"><span>行业</span><Select allowClear mode="tags" placeholder="行业" value={params.industry} onChange={(value: string[]) => updateFilters({ industry: value.length ? value : undefined })} /></div>
          <div className="applications-filter-field"><span>企业规模</span><Select allowClear mode="multiple" placeholder="企业规模" options={sizeOptions.map((value) => ({ value, label: value }))} value={params.company_size} onChange={(value: string[]) => updateFilters({ company_size: value.length ? value : undefined })} /></div>
          <div className="applications-filter-field"><span>投递日期</span><DatePicker.RangePicker value={params.date_from && params.date_to ? [dayjs(params.date_from), dayjs(params.date_to)] : undefined} onChange={(value) => updateFilters({ date_from: value?.[0]?.format("YYYY-MM-DD"), date_to: value?.[1]?.format("YYYY-MM-DD") })} /></div>
          <div className="applications-filter-field applications-filter-field--quick-actions"><span>快捷日期</span><Space wrap><Button onClick={() => updateFilters({ date_from: dayjs().subtract(6, "day").format("YYYY-MM-DD"), date_to: dayjs().format("YYYY-MM-DD") })}>近7天</Button><Button onClick={() => updateFilters({ date_from: dayjs().subtract(29, "day").format("YYYY-MM-DD"), date_to: dayjs().format("YYYY-MM-DD") })}>近30天</Button></Space></div>
          <div className="applications-filter-field"><label htmlFor="applications-sort">排序</label><Select id="applications-sort" aria-label="排序" options={sortOptions} value={params.sort} onChange={(value: ApplicationSort) => updateFilters({ sort: value })} /></div>
          {hasActiveFilters && <div className="applications-filter-field applications-filter-field--action"><span>筛选操作</span><Button onClick={clearFilters}>清空筛选</Button></div>}
        </div>
      </Card>
      {items.length === 0 ? (
        <EmptyState
          image={{ src: emptyApplications, alt: hasActiveFilters ? "没有匹配的投递记录" : "还没有投递记录" }}
          title={applications.isLoading ? "正在加载投递记录" : hasActiveFilters ? "暂无匹配投递记录" : "还没有投递记录"}
          description={applications.isLoading ? "请稍候，正在获取你的投递记录。" : hasActiveFilters ? "试试调整筛选条件，或清空筛选查看全部记录。" : "从第一条投递记录开始，持续掌握求职进度。"}
          action={<Button type={hasActiveFilters ? "default" : "primary"} onClick={hasActiveFilters ? clearFilters : openCreateDrawer}>{hasActiveFilters ? "清空筛选" : "开始新增投递"}</Button>}
        />
      ) : (
        <Table<Application>
          rowKey="id"
          loading={applications.isLoading}
          dataSource={items}
          columns={columns}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total: applications.data?.data.total,
            showSizeChanger: true,
            onChange: (page, pageSize) => setParams((current) => ({ ...current, page, page_size: pageSize })),
          }}
        />
      )}
      <ApplicationForm guest={guest} application={editing} open={applicationDrawerOpen} saving={createMutation.isPending || updateMutation.isPending} onClose={closeDrawer} onSubmit={submit} />
    </section>
  );
}
