import "fake-indexeddb/auto";

import { AxiosError } from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationsPage } from ".";
import { CloudApplicationCache } from "../../data/cloudApplicationCache";
import { CloudApplicationDataSource } from "../../data/cloudApplicationDataSource";
import { deleteLocalDatabase } from "../../local-db/applicationRepository";
import { useAuthStore } from "../../store/auth";
import { useUiStore } from "../../store/ui";
import type { Application } from "../../types/application";
import { listApplications } from "../../api/applications";

Object.defineProperty(window, "matchMedia", { writable: true, value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) });
const browserGetComputedStyle = window.getComputedStyle.bind(window);
Object.defineProperty(window, "getComputedStyle", { writable: true, value: (element: Element) => browserGetComputedStyle(element) });

const cachedApplication: Application = { id: "cached", user_id: "user-a", company_id: "company-a", job_title: "Cached role", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED", created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: "company-a", full_name: "Cached Corp", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" } };

vi.mock("../../api/applications", async (importOriginal) => ({ ...await importOriginal<typeof import("../../api/applications")>(), listApplications: vi.fn() }));
vi.mock("../../components/ApplicationForm", () => ({ ApplicationForm: () => null }));

const mockedList = vi.mocked(listApplications);

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ user: { id: "user-a", username: "alice", email: "a@example.com" }, initialized: true });
  useUiStore.setState({ applicationDrawerOpen: false });
});
afterEach(async () => {
  cleanup();
  await deleteLocalDatabase();
});

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter><ApplicationsPage /></MemoryRouter></QueryClientProvider>);
  return queryClient;
}

describe("ApplicationsPage offline fallback", () => {
  it("shows the current user's cached list with a stale notice after a network failure, then clears it after refetch", async () => {
    await new CloudApplicationCache("user-a").upsertApplication(cachedApplication);
    mockedList.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));
    const queryClient = renderPage();

    expect(await screen.findByText("Cached role")).toBeDefined();
    expect(await screen.findByText(/当前网络不可用/)).toBeDefined();
    mockedList.mockResolvedValueOnce({ items: [{ ...cachedApplication, id: "fresh", job_title: "Fresh role" }], total: 1, page: 1, page_size: 20 });
    await queryClient.refetchQueries({ queryKey: ["applications"], type: "active" });
    expect(await screen.findByText("Fresh role")).toBeDefined();
    await waitFor(() => expect(screen.queryByText(/当前网络不可用/)).toBeNull());
  });

  it("does not read a cloud cache while authentication is initializing", async () => {
    const read = vi.spyOn(CloudApplicationDataSource.prototype, "list");
    useAuthStore.setState({ user: undefined, initialized: false });
    renderPage();

    await waitFor(() => expect(read).not.toHaveBeenCalled());
    read.mockRestore();
  });
});
