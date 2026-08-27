import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Input, Popconfirm, Select, Space, Timeline, Typography, message } from "antd";
import { Link, useParams } from "react-router-dom";

import { changeApplicationStatus } from "../../api/applications";
import { StatusTag } from "../../components/StatusTag";
import { applicationTypeLabels, statusLabels, type ApplicationStatus } from "../../types/application";
import { useAuthStore } from "../../store/auth";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";
import { CloudApplicationCache, writeCloudCacheSafely } from "../../data/cloudApplicationCache";
import { CloudApplicationDataSource, isRecoverableReadFailure } from "../../data/cloudApplicationDataSource";
import { toExternalHttpUrl } from "../../utils/externalUrl";

const guestDataSource = new LocalApplicationDataSource();

export function ApplicationDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const { user, initialized } = useAuthStore();
  const guest = initialized && !user;
  const cloudCache = useMemo(() => user ? new CloudApplicationCache(user.id) : undefined, [user?.id]);
  const cloudDataSource = useMemo(() => user ? new CloudApplicationDataSource(user.id) : undefined, [user?.id]);
  const [status, setStatus] = useState<ApplicationStatus>();
  const [remark, setRemark] = useState("");
  const applicationKey = ["application", guest ? "guest" : "cloud", user?.id, id];
  const logsKey = ["application-status-logs", guest ? "guest" : "cloud", user?.id, id];
  const application = useQuery({
    queryKey: applicationKey,
    queryFn: async () => {
      if (guest) return { data: await guestDataSource.get(id), source: "cloud" as const, stale: false };
      return cloudDataSource!.get(id);
    },
    enabled: initialized && Boolean(id),
  });
  const logs = useQuery({
    queryKey: logsKey,
    queryFn: async () => {
      if (guest) return { data: await guestDataSource.getStatusLogs(id), source: "cloud" as const, stale: false };
      return cloudDataSource!.getStatusLogs(id);
    },
    enabled: initialized && Boolean(id),
  });
  const changeStatus = useMutation({
    mutationFn: async () => {
      if (guest) return guestDataSource.changeStatus(id, status!, remark);
      const response = await changeApplicationStatus(id, status!, remark);
      if (cloudCache) void writeCloudCacheSafely(() => cloudCache.upsertApplication(response));
      return response;
    },
    onSuccess: () => Promise.all([
      queryClient.invalidateQueries({ queryKey: applicationKey }),
      queryClient.invalidateQueries({ queryKey: logsKey }),
      queryClient.invalidateQueries({ queryKey: ["applications"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    ]),
  });
  const remove = useMutation({
    mutationFn: () => guest ? guestDataSource.remove(id) : Promise.reject(new Error("Delete from the list")),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["applications"] }); window.location.assign("/applications"); },
  });

  if (application.isError) return <Typography.Paragraph>读取投递记录失败</Typography.Paragraph>;
  if (!application.data?.data) return <Typography.Paragraph>{application.isLoading ? "正在加载…" : "未找到投递记录"}</Typography.Paragraph>;
  const item = application.data.data;
  const channelUrl = toExternalHttpUrl(item.channel);
  const stale = application.data.stale || logs.data?.stale;
  const cachedAt = application.data.cached_at ?? logs.data?.cached_at;

  return (
    <section className="application-detail-page">
      <Space direction="vertical" size="large" className="application-detail-page__content">
        {stale && <Alert type="warning" showIcon message={cachedAt ? `当前网络不可用，正在显示 ${new Date(cachedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} 缓存的数据。` : "当前网络不可用，正在显示最近缓存的数据。"} />}
        <header className="application-detail-page__header">
          <Space><Link to="/applications">← 返回投递列表</Link>{guest && <Link to="/applications" state={{ editApplication: item }}>编辑</Link>}</Space>
          {guest && <Popconfirm title="确认删除这条本地投递记录？" onConfirm={() => remove.mutate()}><Button danger>删除本地投递</Button></Popconfirm>}
          <Typography.Title level={1} className="application-detail-page__title">{item.job_title}</Typography.Title>
        </header>
        <div className="application-detail-page__layout">
          <div className="application-detail-page__primary">
            <Card title="投递信息" className="application-detail-page__card">
              <Descriptions column={1}>
                <Descriptions.Item label="企业 ID">{item.company_id}</Descriptions.Item>
              </Descriptions>
            </Card>
            <Card title="更新状态" className="application-detail-page__card">
              <Space wrap>
                <Select placeholder="选择新状态" value={status} onChange={setStatus} style={{ minWidth: 180 }} options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} />
                <Input placeholder="状态备注（可选）" value={remark} onChange={(event) => setRemark(event.target.value)} style={{ width: 240 }} />
                <Button type="primary" disabled={!status} loading={changeStatus.isPending} onClick={() => changeStatus.mutate(undefined, { onSuccess: () => { message.success("状态已更新"); setRemark(""); }, onError: (error) => message.error(isRecoverableReadFailure(error) ? "当前网络不可用，请恢复网络后再修改" : "状态更新失败，请检查登录状态") })}>更新状态</Button>
              </Space>
            </Card>
            <Card title="状态历史" className="application-detail-page__card">
              <Timeline items={(logs.data?.data ?? []).map((log) => ({ children: <><StatusTag status={log.to_status} /> <span>{new Date(log.changed_at).toLocaleString()}</span>{log.remark && <Typography.Paragraph>{log.remark}</Typography.Paragraph>}</> }))} />
            </Card>
          </div>
          <aside className="application-detail-page__metadata">
            <Card className="application-detail-page__card">
              <section aria-label="当前状态" className="application-detail-page__current-status">
                <Typography.Text type="secondary">当前状态</Typography.Text>
                <StatusTag status={item.current_status} />
              </section>
            </Card>
            <Card title="投递数据" className="application-detail-page__card">
              <Descriptions column={1}>
                <Descriptions.Item label="投递类型">{applicationTypeLabels[item.application_type]}</Descriptions.Item>
                <Descriptions.Item label="投递时间">{item.application_date}</Descriptions.Item>
                <Descriptions.Item label="投递渠道">{channelUrl ? <a href={channelUrl} target="_blank" rel="noreferrer">{item.channel}</a> : item.channel}</Descriptions.Item>
                <Descriptions.Item label="备注">{item.note || "—"}</Descriptions.Item>
              </Descriptions>
            </Card>
          </aside>
        </div>
      </Space>
    </section>
  );
}
