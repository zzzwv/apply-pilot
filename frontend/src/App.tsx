import { lazy, Suspense, useEffect } from "react";
import type { QueryClient } from "@tanstack/react-query";
import { ConfigProvider, Layout, Spin } from "antd";
import { Route, Routes } from "react-router-dom";

import { AppHeader } from "./components/AppHeader";
import { GuestImportPrompt } from "./components/GuestImportPrompt";
import { apiClient } from "./api/client";
import { useAuthStore } from "./store/auth";
import { ApplicationDetailPage } from "./pages/ApplicationDetail";
import { ApplicationsPage } from "./pages/Applications";

const DashboardPage = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.DashboardPage })));

type Props = { queryClient?: QueryClient };

function AuthBootstrap({ queryClient }: Props) {
  const initialize = useAuthStore((state) => state.initialize);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    void initialize();
  }, [initialize]);

  useEffect(() => {
    if (!queryClient) return undefined;
    const interceptor = apiClient.interceptors.response.use(
      (response) => response,
      (error: unknown) => {
        if ((error as { response?: { status?: number } }).response?.status === 401) {
          logout(queryClient);
        }
        return Promise.reject(error);
      },
    );
    return () => apiClient.interceptors.response.eject(interceptor);
  }, [logout, queryClient]);

  return null;
}

export function App({ queryClient }: Props) {
  return <ConfigProvider theme={{ token: { colorPrimary: "#4F6EF7", colorBgLayout: "#F6F8FC", colorText: "#1F2937", borderRadius: 12, controlHeight: 40 } }}><AuthBootstrap queryClient={queryClient} /><Layout className="applypilot-app" data-testid="app-shell"><AppHeader queryClient={queryClient} /><Layout.Content className="applypilot-content">{queryClient && <GuestImportPrompt queryClient={queryClient} />}<Suspense fallback={<Spin />}><Routes><Route path="/" element={<DashboardPage />} /><Route path="/applications" element={<ApplicationsPage />} /><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></Suspense></Layout.Content></Layout></ConfigProvider>;
}
