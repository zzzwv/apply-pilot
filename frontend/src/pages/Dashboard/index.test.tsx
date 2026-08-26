import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";
import { deleteLocalDatabase } from "../../local-db/database";
import { useAuthStore } from "../../store/auth";
import { DashboardPage } from ".";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

function totalMetric(): string | undefined {
  return screen.getByText("总投递").closest(".ant-statistic")?.querySelector(".ant-statistic-content")?.textContent ?? undefined;
}

function CurrentLocation() {
  const location = useLocation();
  return <output data-testid="current-location">{JSON.stringify({ pathname: location.pathname, state: location.state })}</output>;
}

afterEach(async () => {
  cleanup();
  useAuthStore.setState({ user: undefined, initialized: false });
  await deleteLocalDatabase();
});

describe("Guest dashboard filters", () => {
  it("gives every dashboard filter a programmatic name and scopes the empty-state create action", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/"]}>
          <DashboardPage />
          <CurrentLocation />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByLabelText("关键词")).toBeDefined();
    for (const label of ["投递状态", "企业性质", "投递类型", "行业", "企业规模"]) {
      expect(await screen.findByRole("combobox", { name: label })).toBeDefined();
    }
    expect(screen.getAllByLabelText("投递日期").length).toBeGreaterThan(0);
    const emptyState = (await screen.findByRole("heading", { name: "还没有投递记录" })).closest<HTMLElement>(".empty-state");
    fireEvent.click(within(emptyState!).getByRole("button", { name: "新增投递" }));

    expect(screen.getByTestId("current-location").textContent).toContain('"openCreate":true');
  });

  it("opens the real application creation flow from the empty dashboard", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/"]}>
          <DashboardPage />
          <CurrentLocation />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await screen.findByRole("button", { name: "新增投递" });
    fireEvent.click(screen.getByRole("button", { name: "新增投递" }));

    expect(screen.getByTestId("current-location").textContent).toContain('"pathname":"/applications"');
    expect(screen.getByTestId("current-location").textContent).toContain('"openCreate":true');
  });

  it("applies a dashboard status filter to the IndexedDB-backed summary and restores all data when cleared", async () => {
    const source = new LocalApplicationDataSource();
    await source.create({ company: { full_name: "AI", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" }, job_title: "A", application_type: "autumn_fulltime", application_date: "2026-08-20", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "OFFER_RECEIVED" });
    await source.create({ company: { full_name: "Web", short_name: null, industry: "Web", nature: "STATE_OWNED", size: "1000-5000" }, job_title: "B", application_type: "summer_internship", application_date: "2026-08-25", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" });
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(<QueryClientProvider client={queryClient}><MemoryRouter><DashboardPage /></MemoryRouter></QueryClientProvider>);

    await waitFor(() => expect(totalMetric()).toBe("2"));
    fireEvent.mouseDown(screen.getAllByRole("combobox")[0]);
    fireEvent.click(await screen.findByText("已获 Offer"));
    await waitFor(() => expect(totalMetric()).toBe("1"));
    fireEvent.click(screen.getByRole("button", { name: "清空筛选" }));
    await waitFor(() => expect(totalMetric()).toBe("2"));
  });

  it("clears an active keyword and restores the unfiltered summary", async () => {
    const source = new LocalApplicationDataSource();
    await source.create({ company: { full_name: "AI", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" }, job_title: "A", application_type: "autumn_fulltime", application_date: "2026-08-20", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "OFFER_RECEIVED" });
    await source.create({ company: { full_name: "Web", short_name: null, industry: "Web", nature: "STATE_OWNED", size: "1000-5000" }, job_title: "B", application_type: "summer_internship", application_date: "2026-08-25", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" });
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(<QueryClientProvider client={queryClient}><MemoryRouter><DashboardPage /></MemoryRouter></QueryClientProvider>);

    await waitFor(() => expect(totalMetric()).toBe("2"));
    const keywordInput = screen.getByPlaceholderText("搜索公司、岗位、行业、企业性质或备注");
    fireEvent.change(keywordInput, { target: { value: "AI" } });
    await waitFor(() => expect(totalMetric()).toBe("1"));

    fireEvent.click(screen.getByRole("button", { name: "清空筛选" }));

    expect((keywordInput as HTMLInputElement).value).toBe("");
    await waitFor(() => expect(totalMetric()).toBe("2"));
  });
});
