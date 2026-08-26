import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Descriptions, Input, Popconfirm, Select, Space, Timeline, Typography, message } from "antd";
import { Link, useParams } from "react-router-dom";

import { changeApplicationStatus, getApplication, getApplicationStatusLogs } from "../../api/applications";
import { StatusTag } from "../../components/StatusTag";
import { applicationTypeLabels, statusLabels, type ApplicationStatus } from "../../types/application";
import { useAuthStore } from "../../store/auth";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";

const guestDataSource = new LocalApplicationDataSource();

export function ApplicationDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const { user, initialized } = useAuthStore();
  const guest = initialized && !user;
  const [status, setStatus] = useState<ApplicationStatus>();
  const [remark, setRemark] = useState("");
  const application = useQuery({ queryKey: ["application", guest ? "guest" : "cloud", id], queryFn: () => guest ? guestDataSource.get(id) : getApplication(id), enabled: Boolean(id) });
  const logs = useQuery({ queryKey: ["application-status-logs", guest ? "guest" : "cloud", id], queryFn: () => guest ? guestDataSource.getStatusLogs(id) : getApplicationStatusLogs(id), enabled: Boolean(id) });
  const changeStatus = useMutation({
    mutationFn: () => guest ? guestDataSource.changeStatus(id, status!, remark) : changeApplicationStatus(id, status!, remark),
    onSuccess: () => Promise.all([
      queryClient.invalidateQueries({ queryKey: ["application", id] }),
      queryClient.invalidateQueries({ queryKey: ["application-status-logs", id] }),
      queryClient.invalidateQueries({ queryKey: ["applications"] }),
    ]),
  });
  const remove = useMutation({
    mutationFn: () => guest ? guestDataSource.remove(id) : Promise.reject(new Error("Delete from the list")),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["applications"] }); window.location.assign("/applications"); },
  });

  if (!application.data) return <Typography.Paragraph>{application.isLoading ? "正在加载…" : "未找到投递记录"}</Typography.Paragraph>;
  const item = application.data;

  return (
    <section>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <Space><Link to="/applications">← 返回投递列表</Link>{guest && <Link to="/applications" state={{ editApplication: item }}>编辑</Link>}</Space>
        {guest && <Popconfirm title="确认删除这条本地投递记录？" onConfirm={() => remove.mutate()}><Button danger>删除本地投递</Button></Popconfirm>}
        <Typography.Title level={2}>{item.job_title}</Typography.Title>
        <Card title="投递信息">
          <Descriptions column={1}>
            <Descriptions.Item label="企业 ID">{item.company_id}</Descriptions.Item>
            <Descriptions.Item label="投递类型">{applicationTypeLabels[item.application_type]}</Descriptions.Item>
            <Descriptions.Item label="投递时间">{item.application_date}</Descriptions.Item>
            <Descriptions.Item label="投递渠道">{item.channel}</Descriptions.Item>
            <Descriptions.Item label="当前状态"><StatusTag status={item.current_status} /></Descriptions.Item>
            <Descriptions.Item label="备注">{item.note || "—"}</Descriptions.Item>
          </Descriptions>
        </Card>
        <Card title="更新状态">
          <Space wrap>
            <Select placeholder="选择新状态" value={status} onChange={setStatus} style={{ minWidth: 180 }} options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} />
            <Input placeholder="状态备注（可选）" value={remark} onChange={(event) => setRemark(event.target.value)} style={{ width: 240 }} />
            <Button type="primary" disabled={!status} loading={changeStatus.isPending} onClick={() => changeStatus.mutate(undefined, { onSuccess: () => { message.success("状态已更新"); setRemark(""); } })}>更新状态</Button>
          </Space>
        </Card>
        <Card title="状态历史">
          <Timeline items={(logs.data ?? []).map((log) => ({ children: <><StatusTag status={log.to_status} /> <span>{new Date(log.changed_at).toLocaleString()}</span>{log.remark && <Typography.Paragraph>{log.remark}</Typography.Paragraph>}</> }))} />
        </Card>
      </Space>
    </section>
  );
}
