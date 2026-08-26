import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

afterEach(async () => {
  cleanup();
  useAuthStore.setState({ user: undefined, initialized: false });
  await deleteLocalDatabase();
});

describe("Guest dashboard filters", () => {
  it("applies a dashboard status filter to the IndexedDB-backed summary and restores all data when cleared", async () => {
    const source = new LocalApplicationDataSource();
    await source.create({ company: { full_name: "AI", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" }, job_title: "A", application_type: "autumn_fulltime", application_date: "2026-08-20", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "OFFER_RECEIVED" });
    await source.create({ company: { full_name: "Web", short_name: null, industry: "Web", nature: "STATE_OWNED", size: "1000-5000" }, job_title: "B", application_type: "summer_internship", application_date: "2026-08-25", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" });
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(<QueryClientProvider client={queryClient}><DashboardPage /></QueryClientProvider>);

    await waitFor(() => expect(totalMetric()).toBe("2"));
    fireEvent.mouseDown(screen.getAllByRole("combobox")[0]);
    fireEvent.click(await screen.findByText("已获 Offer"));
    await waitFor(() => expect(totalMetric()).toBe("1"));
    fireEvent.click(screen.getByRole("button", { name: "清空筛选" }));
    await waitFor(() => expect(totalMetric()).toBe("2"));
  });
});
