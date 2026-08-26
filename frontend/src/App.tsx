import { lazy, Suspense, useEffect } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { ConfigProvider, Layout, Spin } from "antd";
import { Route, Routes } from "react-router-dom";

import { AppHeader } from "./components/AppHeader";
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
  return <ConfigProvider theme={{ token: { colorPrimary: "#4F6EF7", colorBgLayout: "#F6F8FC", colorText: "#1F2937", borderRadius: 12, controlHeight: 40 } }}><AuthBootstrap /><Layout className="applypilot-app" data-testid="app-shell"><AppHeader queryClient={queryClient} /><Layout.Content className="applypilot-content">{queryClient && <GuestImportPrompt queryClient={queryClient} />}<Suspense fallback={<Spin />}><Routes><Route path="/" element={<DashboardPage />} /><Route path="/applications" element={<ApplicationsPage />} /><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></Suspense></Layout.Content></Layout></ConfigProvider>;
}
