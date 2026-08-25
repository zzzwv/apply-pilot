import { ConfigProvider, Layout, Typography } from "antd";
import { Link, Route, Routes } from "react-router-dom";

import { ApplicationDetailPage } from "./pages/ApplicationDetail";
import { ApplicationsPage } from "./pages/Applications";

const Placeholder = ({ title }: { title: string }) => <Typography.Paragraph>{title}将在后续阶段实现。</Typography.Paragraph>;

export function App() {
  return <ConfigProvider><Layout style={{ minHeight: "100vh", padding: 32 }}><Typography.Title>秋招 / 实习投递管理</Typography.Title><nav><Link to="/">首页</Link>{" · "}<Link to="/applications">投递记录</Link></nav><Routes><Route path="/" element={<Placeholder title="数据看板" />} /><Route path="/applications" element={<ApplicationsPage />} /><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></Layout></ConfigProvider>;
}
