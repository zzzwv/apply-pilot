import { useEffect, useMemo, useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, DatePicker, Empty, Input, Popconfirm, Select, Space, Table, Typography, message } from "antd";
import dayjs from "dayjs";
import { Link, useLocation } from "react-router-dom";

import { createApplication, deleteApplication, listApplications, toApplicationUpdate, updateApplication } from "../../api/applications";
import { ApplicationForm } from "../../components/ApplicationForm";
import { StatusTag } from "../../components/StatusTag";
import { useUiStore } from "../../store/ui";
import { useAuthStore } from "../../store/auth";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";
import { CloudApplicationCache, writeCloudCacheSafely } from "../../data/cloudApplicationCache";
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
  const { applicationDrawerOpen, setApplicationDrawerOpen } = useUiStore();
  const [editing, setEditing] = useState<Application>();
  const [keywordInput, setKeywordInput] = useState("");
  const [params, setParams] = useState<ApplicationListParams>(initialParams);
  const pendingEdit = (location.state as { editApplication?: Application } | null)?.editApplication;
  useEffect(() => {
    if (pendingEdit) {
      setEditing(pendingEdit);
      setApplicationDrawerOpen(true);
    }
  }, [pendingEdit, setApplicationDrawerOpen]);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setParams((current) => ({ ...current, keyword: keywordInput.trim() || undefined, page: 1 }));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [keywordInput]);
  const applications = useQuery({
    queryKey: [...applicationsKey, guest ? "guest" : "cloud", user?.id, params],
    queryFn: async () => {
      if (guest) return guestDataSource.list(params);
      const response = await listApplications(params);
      if (cloudCache) void writeCloudCacheSafely(() => cloudCache.upsertApplications(response.items));
      return response;
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
  });
  const items = applications.data?.items ?? [];
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

  const submit = async (payload: ApplicationInput | GuestApplicationInput) => {
    try {
      if (editing) await updateMutation.mutateAsync({ id: editing.id, payload: toApplicationUpdate(payload as ApplicationInput) });
      else await createMutation.mutateAsync(payload);
      message.success("投递记录已保存");
      closeDrawer();
    } catch {
      message.error("保存失败，请检查输入或登录状态");
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
    <section>
      <Space style={{ width: "100%", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={2}>投递记录</Typography.Title>
        <Button type="primary" onClick={() => setApplicationDrawerOpen(true)}>新增投递</Button>
      </Space>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input
          allowClear
          placeholder="搜索公司、岗位、行业、企业性质或备注"
          style={{ width: 320 }}
          value={keywordInput}
          onChange={(event) => setKeywordInput(event.target.value)}
        />
        <Select
          allowClear
          mode="multiple"
          placeholder="投递状态"
          style={{ minWidth: 160 }}
          options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))}
          value={params.status}
          onChange={(value: ApplicationStatus[]) => updateFilters({ status: value.length ? value : undefined })}
        />
        <Select
          allowClear
          mode="multiple"
          placeholder="企业性质"
          style={{ minWidth: 140 }}
          options={natureOptions.map(([value, label]) => ({ value, label }))}
          value={params.company_nature}
          onChange={(value: string[]) => updateFilters({ company_nature: value.length ? value : undefined })}
        />
        <Select
          allowClear
          mode="multiple"
          placeholder="投递类型"
          style={{ minWidth: 140 }}
          options={Object.entries(applicationTypeLabels).map(([value, label]) => ({ value, label }))}
          value={params.application_type}
          onChange={(value: ApplicationType[]) => updateFilters({ application_type: value.length ? value : undefined })}
        />
        <Select
          allowClear
          mode="tags"
          placeholder="行业"
          style={{ minWidth: 140 }}
          value={params.industry}
          onChange={(value: string[]) => updateFilters({ industry: value.length ? value : undefined })}
        />
        <Select
          allowClear
          mode="multiple"
          placeholder="企业规模"
          style={{ minWidth: 140 }}
          options={sizeOptions.map((value) => ({ value, label: value }))}
          value={params.company_size}
          onChange={(value: string[]) => updateFilters({ company_size: value.length ? value : undefined })}
        />
        <DatePicker.RangePicker
          value={params.date_from && params.date_to ? [dayjs(params.date_from), dayjs(params.date_to)] : undefined}
          onChange={(value) => updateFilters({
            date_from: value?.[0]?.format("YYYY-MM-DD"),
            date_to: value?.[1]?.format("YYYY-MM-DD"),
          })}
        />
        <Button onClick={() => updateFilters({ date_from: dayjs().subtract(6, "day").format("YYYY-MM-DD"), date_to: dayjs().format("YYYY-MM-DD") })}>近7天</Button>
        <Button onClick={() => updateFilters({ date_from: dayjs().subtract(29, "day").format("YYYY-MM-DD"), date_to: dayjs().format("YYYY-MM-DD") })}>近30天</Button>
        <Select
          aria-label="排序"
          style={{ minWidth: 190 }}
          options={sortOptions}
          value={params.sort}
          onChange={(value: ApplicationSort) => updateFilters({ sort: value })}
        />
        {hasActiveFilters && <Button onClick={clearFilters}>清空筛选</Button>}
      </Space>
      {items.length === 0 ? (
        <Empty description={applications.isLoading ? "正在加载投递记录" : hasActiveFilters ? "暂无匹配投递记录" : "暂无投递记录"}>
          {hasActiveFilters && <Button onClick={clearFilters}>清空筛选</Button>}
        </Empty>
      ) : (
        <Table<Application>
          rowKey="id"
          loading={applications.isLoading}
          dataSource={items}
          columns={columns}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total: applications.data?.total,
            showSizeChanger: true,
            onChange: (page, pageSize) => setParams((current) => ({ ...current, page, page_size: pageSize })),
          }}
        />
      )}
      <ApplicationForm guest={guest} application={editing} open={applicationDrawerOpen} saving={createMutation.isPending || updateMutation.isPending} onClose={closeDrawer} onSubmit={submit} />
    </section>
  );
}
