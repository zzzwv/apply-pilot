import "fake-indexeddb/auto";

import { AxiosError } from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationDetailPage } from ".";
import { CloudApplicationCache } from "../../data/cloudApplicationCache";
import { deleteLocalDatabase } from "../../local-db/applicationRepository";
import { useAuthStore } from "../../store/auth";
import type { Application, ApplicationStatusLog } from "../../types/application";
import { getApplication, getApplicationStatusLogs } from "../../api/applications";

Object.defineProperty(window, "matchMedia", { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) });

const cachedApplication: Application = { id: "cached", user_id: "user-a", company_id: "company-a", job_title: "Cached detail", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED", created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: "company-a", full_name: "Cached Corp", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" } };
const cachedLogs: ApplicationStatusLog[] = [{ id: "cached-log", application_id: "cached", from_status: null, to_status: "APPLIED", remark: "cached", changed_at: "2026-08-26T00:00:00.000Z" }];

vi.mock("../../api/applications", async (importOriginal) => ({ ...await importOriginal<typeof import("../../api/applications")>(), getApplication: vi.fn(), getApplicationStatusLogs: vi.fn() }));
const mockedGet = vi.mocked(getApplication);
const mockedLogs = vi.mocked(getApplicationStatusLogs);

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ user: { id: "user-a", username: "alice", email: "a@example.com" }, initialized: true });
});
afterEach(async () => {
  cleanup();
  await deleteLocalDatabase();
});

describe("ApplicationDetailPage offline fallback", () => {
  it("shows cached detail and timeline with a stale notice after network failures", async () => {
    const cache = new CloudApplicationCache("user-a");
    await cache.upsertApplication(cachedApplication);
    await cache.replaceStatusLogs("cached", cachedLogs);
    mockedGet.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));
    mockedLogs.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={["/applications/cached"]}><Routes><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></MemoryRouter></QueryClientProvider>);

    expect(await screen.findByText("Cached detail")).toBeDefined();
    expect(await screen.findByText(/当前网络不可用/)).toBeDefined();
    expect((await screen.findAllByText("cached")).length).toBeGreaterThan(1);
  });
});
