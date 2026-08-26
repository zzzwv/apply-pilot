import { useState } from "react";
import { Button, Form, Input, Modal, Space, Typography, message } from "antd";
import type { QueryClient } from "@tanstack/react-query";

import { useAuthStore } from "../../store/auth";
import authCareer from "../../assets/illustrations/auth-career.svg";

type AuthFormValues = {
  username_or_email: string;
  password: string;
  username?: string;
};

type Props = {
  queryClient: QueryClient;
};

export function AuthControls({ queryClient }: Props) {
  const { initialized, user, login, register, logout } = useAuthStore();
  const [mode, setMode] = useState<"login" | "register">();
  const [submitting, setSubmitting] = useState(false);

  if (!initialized) return null;

  const submitLogin = async (values: AuthFormValues) => {
    setSubmitting(true);
    try {
      await login(values.username_or_email, values.password);
      message.success("登录成功");
      setMode(undefined);
    } catch {
      message.error("登录失败，请检查用户名、邮箱或密码");
    } finally {
      setSubmitting(false);
    }
  };

  const submitRegister = async (values: AuthFormValues) => {
    if (!values.username) return;
    setSubmitting(true);
    try {
      await register({ username: values.username, email: values.username_or_email, password: values.password });
      message.success("注册成功，请登录");
      setMode("login");
    } catch {
      message.error("注册失败，请检查输入或用户名是否已存在");
    } finally {
      setSubmitting(false);
    }
  };

  if (user) {
    return (
      <Space>
        <Typography.Text>{user.email}</Typography.Text>
        <Button onClick={() => logout(queryClient)}>退出登录</Button>
      </Space>
    );
  }

  return (
    <>
      <Space>
        <Button onClick={() => setMode("login")}>登录</Button>
        <Button type="primary" onClick={() => setMode("register")}>注册</Button>
      </Space>
      <Modal
        destroyOnHidden
        title={mode === "register" ? "注册" : "登录"}
        open={Boolean(mode)}
        footer={null}
        onCancel={() => setMode(undefined)}
      >
        <div className="auth-controls__intro">
          <div>
            <Typography.Text strong>{mode === "register" ? "建立你的投递工作台" : "继续你的求职进程"}</Typography.Text>
            <Typography.Paragraph type="secondary">{mode === "register" ? "集中管理每一次关键投递。" : "查看最新投递动态和数据。"}</Typography.Paragraph>
          </div>
          <img src={authCareer} alt="" aria-hidden="true" />
        </div>
        <Form<AuthFormValues> layout="vertical" onFinish={mode === "register" ? submitRegister : submitLogin}>
          {mode === "register" && (
            <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, max: 64 }]}>
              <Input autoComplete="username" />
            </Form.Item>
          )}
          <Form.Item name="username_or_email" label={mode === "register" ? "邮箱" : "用户名或邮箱"} rules={[{ required: true, min: 3, max: 255 }]}>
            <Input autoComplete={mode === "register" ? "email" : "username"} />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 8, max: 128 }]}>
            <Input.Password autoComplete={mode === "register" ? "new-password" : "current-password"} />
          </Form.Item>
          <Button htmlType="submit" type="primary" loading={submitting} block>
            {mode === "register" ? "注册" : "登录"}
          </Button>
        </Form>
      </Modal>
    </>
  );
}
