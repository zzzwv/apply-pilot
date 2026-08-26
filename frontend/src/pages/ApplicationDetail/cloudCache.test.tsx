import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationDetailPage } from ".";
import { CloudApplicationCache } from "../../data/cloudApplicationCache";
import { deleteLocalDatabase } from "../../local-db/applicationRepository";
import { useAuthStore } from "../../store/auth";
import type { Application, ApplicationStatusLog } from "../../types/application";
import { changeApplicationStatus, getApplication, getApplicationStatusLogs } from "../../api/applications";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

const application: Application = {
  id: "application-a", user_id: "user-a", company_id: "company-a", job_title: "Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED", created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: "company-a", full_name: "Cloud Corp", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
};
const logs: ApplicationStatusLog[] = [{ id: "log-a", application_id: "application-a", from_status: null, to_status: "APPLIED", remark: null, changed_at: "2026-08-26T00:00:00.000Z" }];

vi.mock("../../api/applications", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../api/applications")>(),
  getApplication: vi.fn(), getApplicationStatusLogs: vi.fn(), changeApplicationStatus: vi.fn(),
}));

const mockedGet = vi.mocked(getApplication);
const mockedLogs = vi.mocked(getApplicationStatusLogs);
const mockedChangeStatus = vi.mocked(changeApplicationStatus);

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ user: { id: "user-a", username: "alice", email: "a@example.com" }, initialized: true });
  mockedGet.mockResolvedValue(application);
  mockedLogs.mockResolvedValue(logs);
});

afterEach(async () => {
  cleanup();
  await deleteLocalDatabase();
});

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={["/applications/application-a"]}><Routes><Route path="/applications/:id" element={<ApplicationDetailPage />} /></Routes></MemoryRouter></QueryClientProvider>);
}

describe("cloud application detail cache side effects", () => {
  it("caches successful detail and status-history responses for the authenticated user", async () => {
    renderPage();

    await screen.findByText("Engineer");
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("application-a")).toMatchObject({ job_title: "Engineer" }));
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getStatusLogs("application-a")).toMatchObject([{ id: "log-a", to_status: "APPLIED" }]));
  });

  it("caches the server response after a successful cloud status update", async () => {
    const updated = { ...application, current_status: "FIRST_INTERVIEW" as const };
    mockedChangeStatus.mockImplementation(async () => {
      mockedGet.mockResolvedValue(updated);
      return updated;
    });
    renderPage();
    await screen.findByText("Engineer");

    fireEvent.mouseDown(screen.getByRole("combobox"));
    fireEvent.click(await screen.findByText("一面"));
    fireEvent.click(screen.getByRole("button", { name: "更新状态" }));

    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("application-a")).toMatchObject({ current_status: "FIRST_INTERVIEW" }));
  });
});
