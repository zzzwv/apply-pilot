import { lazy, Suspense } from "react";
import { ConfigProvider, Layout, Spin, Typography } from "antd";
import { Link, Route, Routes } from "react-router-dom";

import { ApplicationDetailPage } from "./pages/ApplicationDetail";
import { ApplicationsPage } from "./pages/Applications";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));

export function App() {
  return <ConfigProvider><Layout style={{ minHeight: "100vh", padding: 32 }}><Typography.Title>秋招 / 实习投递管理</Typography.Title><nav><Link to="/">首页</Link>{" · "}<Link to="/applications">投递记录</Link></nav><Suspense fallback={<Spin />}><Routes><Route path="/" element={<DashboardPage />} /><Route path="/applications" element={<ApplicationsPage />} /><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></Suspense></Layout></ConfigProvider>;
}
