import { Button, DatePicker, Drawer, Form, Input, Select, Space } from "antd";
import dayjs from "dayjs";

import { CompanyIntelligenceField } from "../CompanyIntelligenceField";
import type { GuestApplicationInput } from "../../local-db/applicationRepository";

import {
  applicationTypeLabels,
  statusLabels,
  type Application,
  type ApplicationInput,
  type ApplicationStatus,
  type ApplicationType,
} from "../../types/application";

type FormValues = Omit<ApplicationInput, "application_date" | "deadline"> & {
  application_date: dayjs.Dayjs;
  deadline?: dayjs.Dayjs;
  local_company_name?: string;
  local_company_industry?: string;
  local_company_nature?: string;
  local_company_size?: string;
};

type Props = {
  application?: Application;
  guest?: boolean;
  open: boolean;
  saving: boolean;
  onClose: () => void;
  onSubmit: (payload: ApplicationInput | GuestApplicationInput) => Promise<void>;
};

const typeOptions = Object.entries(applicationTypeLabels).map(([value, label]) => ({ value, label }));
const statusOptions = Object.entries(statusLabels).map(([value, label]) => ({ value, label }));

export function ApplicationForm({ application, guest = false, open, saving, onClose, onSubmit }: Props) {
  const [form] = Form.useForm<FormValues>();

  const submit = async (values: FormValues) => {
    const { local_company_name, local_company_industry, local_company_nature, local_company_size, ...applicationValues } = values;
    const payload = {
      ...applicationValues,
      application_date: values.application_date.format("YYYY-MM-DD"),
      deadline: values.deadline?.format("YYYY-MM-DD") ?? null,
    };
    if (guest) {
      await onSubmit({
        ...payload,
        company: { full_name: local_company_name ?? "", short_name: null, industry: local_company_industry || null, nature: local_company_nature || null, size: local_company_size || null },
      } as GuestApplicationInput);
      return;
    }
    await onSubmit(payload as ApplicationInput);
  };

  const initialValues: Partial<FormValues> | undefined = application
    ? {
        ...application,
        application_date: dayjs(application.application_date),
        deadline: application.deadline ? dayjs(application.deadline) : undefined,
      }
    : { application_type: "autumn_fulltime", current_status: "APPLIED", application_date: dayjs() };

  return (
    <Drawer
      destroyOnHidden
      title={application ? "编辑投递" : "新增投递"}
      open={open}
      onClose={onClose}
      width={520}
      extra={<Button form="application-form" type="primary" htmlType="submit" loading={saving}>保存</Button>}
    >
      <Form<FormValues> id="application-form" layout="vertical" form={form} initialValues={initialValues} onFinish={submit}>
        {guest ? <><Form.Item name="local_company_name" label="本地企业名称" rules={[{ required: true, message: "请输入企业名称" }]}><Input /></Form.Item><Form.Item name="local_company_industry" label="行业"><Input /></Form.Item><Form.Item name="local_company_nature" label="企业性质"><Input /></Form.Item><Form.Item name="local_company_size" label="企业规模"><Input /></Form.Item><p>登录后可使用企业信息智能获取</p></> : <><Form.Item name="company_id" hidden rules={[{ required: true, message: "请先关联或创建企业" }]}><Input /></Form.Item><Form.Item label="企业" required><CompanyIntelligenceField value={form.getFieldValue("company_id")} initialCompany={application?.company} onChange={(companyId) => form.setFieldValue("company_id", companyId)} /></Form.Item></>}
        <Form.Item name="job_title" label="投递岗位" rules={[{ required: true, message: "请输入岗位名称" }]}><Input /></Form.Item>
        <Space size="large" style={{ display: "flex" }}>
          <Form.Item name="application_type" label="投递类型" rules={[{ required: true }]}><Select options={typeOptions} style={{ minWidth: 180 }} /></Form.Item>
          <Form.Item name="application_date" label="投递时间" rules={[{ required: true }]}><DatePicker /></Form.Item>
        </Space>
        <Form.Item name="channel" label="投递渠道" rules={[{ required: true, message: "请输入投递渠道" }]}><Input placeholder="official_campus / referral" /></Form.Item>
        {!application && <Form.Item name="current_status" label="初始状态" rules={[{ required: true }]}><Select options={statusOptions} /></Form.Item>}
        <Form.Item name="resume_version" label="简历版本"><Input /></Form.Item>
        <Form.Item name="salary" label="薪资"><Input /></Form.Item>
        <Form.Item name="city" label="城市"><Input /></Form.Item>
        <Form.Item name="education_requirement" label="学历要求"><Input /></Form.Item>
        <Form.Item name="deadline" label="截止日期"><DatePicker /></Form.Item>
        <Form.Item name="requirements" label="岗位要求"><Input.TextArea rows={3} /></Form.Item>
        <Form.Item name="note" label="备注"><Input.TextArea rows={3} /></Form.Item>
      </Form>
    </Drawer>
  );
}
