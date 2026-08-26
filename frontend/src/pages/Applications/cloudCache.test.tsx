import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApplicationsPage } from ".";
import { CloudApplicationCache } from "../../data/cloudApplicationCache";
import { deleteLocalDatabase } from "../../local-db/applicationRepository";
import { useAuthStore } from "../../store/auth";
import { useUiStore } from "../../store/ui";
import type { Application, ApplicationInput } from "../../types/application";
import { createApplication, deleteApplication, listApplications, updateApplication } from "../../api/applications";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});
const browserGetComputedStyle = window.getComputedStyle.bind(window);
Object.defineProperty(window, "getComputedStyle", { writable: true, value: (element: Element) => browserGetComputedStyle(element) });

const payload: ApplicationInput = { company_id: "company-a", job_title: "Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" };
const application = (id: string, jobTitle = "Engineer"): Application => ({ ...payload, id, user_id: "user-a", company_id: "company-a", job_title: jobTitle, created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: "company-a", full_name: "Cloud Corp", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" } });

vi.mock("../../components/ApplicationForm", () => ({
  ApplicationForm: ({ open, application: editing, onSubmit }: { open: boolean; application?: Application; onSubmit: (value: ApplicationInput) => Promise<void> }) => open ? <button onClick={() => void onSubmit({ ...payload, job_title: editing ? "Updated" : "Created" })}>{editing ? "提交编辑" : "提交新增"}</button> : null,
}));

vi.mock("../../api/applications", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../api/applications")>(),
  listApplications: vi.fn(), createApplication: vi.fn(), updateApplication: vi.fn(), deleteApplication: vi.fn(),
}));

vi.mock("antd", async (importOriginal) => {
  const antd = await importOriginal<typeof import("antd")>();
  return {
    ...antd,
    Popconfirm: ({ children, onConfirm }: { children: ReactNode; onConfirm: () => void }) => <>{children}<button type="button" onClick={onConfirm}>确认删除</button></>,
  };
});

const mockedList = vi.mocked(listApplications);
const mockedCreate = vi.mocked(createApplication);
const mockedUpdate = vi.mocked(updateApplication);
const mockedDelete = vi.mocked(deleteApplication);

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ user: { id: "user-a", username: "alice", email: "a@example.com" }, initialized: true });
  useUiStore.setState({ applicationDrawerOpen: false });
  let listedExisting = application("existing");
  mockedList.mockImplementation(async () => ({ items: [listedExisting], total: 1, page: 1, page_size: 20 }));
  mockedUpdate.mockImplementation(async () => {
    listedExisting = application("existing", "Updated");
    return listedExisting;
  });
});

afterEach(async () => {
  cleanup();
  await deleteLocalDatabase();
});

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter><ApplicationsPage /></MemoryRouter></QueryClientProvider>);
}

describe("cloud application cache side effects", () => {
  it("caches successful cloud list responses under the current user", async () => {
    renderPage();

    await screen.findByText("Engineer");
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("existing")).toMatchObject({ job_title: "Engineer" }));
  });

  it("keeps the successful server list visible when IndexedDB cache writing fails", async () => {
    const warning = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const cacheFailure = vi.spyOn(CloudApplicationCache.prototype, "upsertApplications").mockRejectedValueOnce(new Error("quota"));
    renderPage();

    expect(await screen.findByText("Engineer")).toBeDefined();
    await waitFor(() => expect(warning).toHaveBeenCalled());
    cacheFailure.mockRestore();
    warning.mockRestore();
  });

  it("does not request cloud data before authentication initialization completes", async () => {
    useAuthStore.setState({ user: undefined, initialized: false });
    renderPage();

    await waitFor(() => expect(mockedList).not.toHaveBeenCalled());
  });

  it("does not display the previous user's list while the next user is loading", async () => {
    let resolveSecondUser!: (value: { items: Application[]; total: number; page: number; page_size: number }) => void;
    mockedList.mockReset();
    mockedList.mockResolvedValueOnce({ items: [application("application-a", "Alice role")], total: 1, page: 1, page_size: 20 });
    mockedList.mockImplementationOnce(() => new Promise((resolve) => { resolveSecondUser = resolve; }));
    renderPage();
    await screen.findByText("Alice role");

    act(() => useAuthStore.setState({ user: { id: "user-b", username: "bob", email: "b@example.com" }, initialized: true }));

    await waitFor(() => expect(screen.queryByText("Alice role")).toBeNull());
    act(() => resolveSecondUser({ items: [application("application-b", "Bob role")], total: 1, page: 1, page_size: 20 }));
    expect(await screen.findByText("Bob role")).toBeDefined();
  });

  it("caches successful cloud create and update responses, but not a failed mutation", async () => {
    mockedCreate.mockResolvedValueOnce(application("created", "Created"));
    renderPage();
    await screen.findByText("Engineer");

    fireEvent.click(screen.getByRole("button", { name: "新增投递" }));
    fireEvent.click(screen.getByRole("button", { name: "提交新增" }));
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("created")).toMatchObject({ job_title: "Created" }));

    fireEvent.click(screen.getByRole("button", { name: "编辑" }));
    fireEvent.click(screen.getByRole("button", { name: "提交编辑" }));
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("existing")).toMatchObject({ job_title: "Updated" }));

    mockedCreate.mockRejectedValueOnce(new Error("server failed"));
    fireEvent.click(screen.getByRole("button", { name: "新增投递" }));
    fireEvent.click(screen.getByRole("button", { name: "提交新增" }));
    await waitFor(() => expect(mockedCreate).toHaveBeenCalledTimes(2));
    expect(await new CloudApplicationCache("user-a").getApplication("failed")).toBeUndefined();
  });

  it("removes a cloud entity only after its delete API succeeds", async () => {
    mockedDelete.mockResolvedValueOnce({ deleted_count: 1 });
    renderPage();
    await screen.findByText("Engineer");
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("existing")).toBeDefined());

    fireEvent.click(screen.getByRole("button", { name: "确认删除" }));
    await waitFor(async () => expect(await new CloudApplicationCache("user-a").getApplication("existing")).toBeUndefined());
  });
});
