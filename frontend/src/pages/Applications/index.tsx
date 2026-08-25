import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Empty, Popconfirm, Space, Table, Typography, message } from "antd";
import { Link } from "react-router-dom";

import { createApplication, deleteApplication, listApplications, toApplicationUpdate, updateApplication } from "../../api/applications";
import { ApplicationForm } from "../../components/ApplicationForm";
import { StatusTag } from "../../components/StatusTag";
import { useUiStore } from "../../store/ui";
import { applicationTypeLabels, type Application, type ApplicationInput } from "../../types/application";

const applicationsKey = ["applications"] as const;

export function ApplicationsPage() {
  const queryClient = useQueryClient();
  const { applicationDrawerOpen, setApplicationDrawerOpen } = useUiStore();
  const [editing, setEditing] = useState<Application>();
  const applications = useQuery({ queryKey: [...applicationsKey, 1, 20], queryFn: () => listApplications() });
  const createMutation = useMutation({ mutationFn: createApplication, onSuccess: () => queryClient.invalidateQueries({ queryKey: applicationsKey }) });
  const updateMutation = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Partial<ApplicationInput> }) => updateApplication(id, payload), onSuccess: () => queryClient.invalidateQueries({ queryKey: applicationsKey }) });
  const deleteMutation = useMutation({ mutationFn: deleteApplication, onSuccess: () => queryClient.invalidateQueries({ queryKey: applicationsKey }) });
  const items = applications.data?.items ?? [];

  const closeDrawer = () => {
    setEditing(undefined);
    setApplicationDrawerOpen(false);
  };

  const submit = async (payload: ApplicationInput) => {
    try {
      if (editing) await updateMutation.mutateAsync({ id: editing.id, payload: toApplicationUpdate(payload) });
      else await createMutation.mutateAsync(payload);
      message.success("投递记录已保存");
      closeDrawer();
    } catch {
      message.error("保存失败，请检查输入或登录状态");
    }
  };

  const columns = [
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
      {items.length === 0 ? <Empty description={applications.isLoading ? "正在加载投递记录" : "暂无投递记录"} /> : <Table<Application> rowKey="id" loading={applications.isLoading} dataSource={items} columns={columns} pagination={false} />}
      <ApplicationForm application={editing} open={applicationDrawerOpen} saving={createMutation.isPending || updateMutation.isPending} onClose={closeDrawer} onSubmit={submit} />
    </section>
  );
}
