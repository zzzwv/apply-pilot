import { lazy, Suspense, useEffect } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { ConfigProvider, Layout, Space, Spin, Typography } from "antd";
import { Link, Route, Routes } from "react-router-dom";

import { AuthControls } from "./components/AuthControls";
import { GuestImportPrompt } from "./components/GuestImportPrompt";
import { useAuthStore } from "./store/auth";
import { ApplicationDetailPage } from "./pages/ApplicationDetail";
import { ApplicationsPage } from "./pages/Applications";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));

type Props = { queryClient?: QueryClient };

function AuthBootstrap() {
  const initialize = useAuthStore((state) => state.initialize);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  return null;
}

export function App({ queryClient }: Props) {
  return <ConfigProvider><AuthBootstrap /><Layout className="applypilot-app" data-testid="app-shell" style={{ minHeight: "100vh", padding: 32 }}><Space style={{ width: "100%", justifyContent: "space-between" }} align="start"><Typography.Title>秋招 / 实习投递管理</Typography.Title>{queryClient && <AuthControls queryClient={queryClient} />}</Space><nav><Link to="/">首页</Link>{" · "}<Link to="/applications">投递记录</Link></nav>{queryClient && <GuestImportPrompt queryClient={queryClient} />}<Suspense fallback={<Spin />}><Routes><Route path="/" element={<DashboardPage />} /><Route path="/applications" element={<ApplicationsPage />} /><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></Suspense></Layout></ConfigProvider>;
}
