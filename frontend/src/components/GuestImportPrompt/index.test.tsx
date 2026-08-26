import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GuestImportPrompt } from ".";
import { listApplications } from "../../api/applications";
import { importGuestApplications } from "../../sync/guestImport";
import { LocalApplicationRepository, deleteLocalDatabase, type GuestApplicationInput } from "../../local-db/applicationRepository";
import { useAuthStore } from "../../store/auth";

vi.mock("../../sync/guestImport", () => ({ importGuestApplications: vi.fn() }));
vi.mock("../../api/applications", () => ({ listApplications: vi.fn() }));

const browserGetComputedStyle = window.getComputedStyle.bind(window);
Object.defineProperty(window, "getComputedStyle", {
  writable: true,
  value: (element: Element) => browserGetComputedStyle(element),
});

const input: GuestApplicationInput = {
  company: { full_name: "Guest Company", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
  job_title: "Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official",
  resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED",
};

const mockImport = vi.mocked(importGuestApplications);
const mockList = vi.mocked(listApplications);

beforeEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ user: undefined, initialized: false });
  mockList.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 });
});

afterEach(async () => {
  cleanup();
  await deleteLocalDatabase();
});

function renderPrompt(userId: string) {
  useAuthStore.setState({ user: { id: userId, username: userId, email: `${userId}@example.com` }, initialized: true });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><GuestImportPrompt queryClient={queryClient} /></QueryClientProvider>);
  return queryClient;
}

describe("GuestImportPrompt", () => {
  it("does not prompt after login when there are no guest records", async () => {
    renderPrompt("no-records");
    expect(screen.queryByText("是否同步到当前账号？")).toBeNull();
    await waitFor(() => expect(screen.queryByText(/检测到.*本地投递记录/)).toBeNull());
  });

  it("shows the authenticated guest record count and dismissing preserves data without importing", async () => {
    const repository = new LocalApplicationRepository("guest");
    await repository.create(input);
    await repository.create({ ...input, job_title: "Second" });
    renderPrompt("dismiss-user");

    expect(await screen.findByText("检测到 2 条本地投递记录")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "暂不同步" }));
    expect(mockImport).not.toHaveBeenCalled();
    expect(await repository.count()).toBe(2);
  });

  it("prevents duplicate import clicks and refreshes cloud applications plus dashboard before reporting partial success", async () => {
    const repository = new LocalApplicationRepository("guest");
    await repository.create(input);
    const queryClient = renderPrompt("import-user");
    queryClient.setQueryData(["applications", "cloud", "import-user"], { items: [] });
    queryClient.setQueryData(["dashboard", "cloud", "import-user", "summary"], { total: 0 });
    let resolveImport: (() => void) | undefined;
    mockImport.mockImplementationOnce(async ({ refreshCloud }) => {
      await new Promise<void>((resolve) => { resolveImport = resolve; });
      await refreshCloud();
      return { imported: 1, reused: 1, failed: 2, migrated: 2, cleaned: 2, cloud_snapshot_failed: false };
    });

    expect(await screen.findByText("检测到 1 条本地投递记录")).toBeDefined();
    const sync = screen.getByRole("button", { name: "同步到账号" });
    fireEvent.click(sync);
    await waitFor(() => expect(mockImport).toHaveBeenCalledTimes(1));
    fireEvent.click(sync);
    expect(mockImport).toHaveBeenCalledTimes(1);
    resolveImport?.();

    await waitFor(() => expect(mockList).toHaveBeenCalledWith({ page: 1, page_size: 20 }));
    await waitFor(() => expect(queryClient.getQueryState(["applications", "cloud", "import-user"])?.isInvalidated).toBe(true));
    expect(queryClient.getQueryState(["dashboard", "cloud", "import-user", "summary"])?.isInvalidated).toBe(true);
    expect(await screen.findByText("已同步 2 条投递记录，2 条未成功同步，可稍后重试。")).toBeDefined();
  });
});
