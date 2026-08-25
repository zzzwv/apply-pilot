import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { listApplications } from "./api/applications";

vi.mock("./api/applications", () => ({
  listApplications: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 }),
  createApplication: vi.fn(),
  deleteApplication: vi.fn(),
  updateApplication: vi.fn(),
}));

afterEach(cleanup);

describe("App", () => {
  it("renders the Phase 1 application shell", () => {
    render(<BrowserRouter><App /></BrowserRouter>);
    expect(screen.getByRole("heading", { name: "秋招 / 实习投递管理" })).toBeDefined();
  });

  it("renders the Phase 2 application list entry point", () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/applications"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("button", { name: "新增投递" })).toBeDefined();
  });

  it("debounces a keyword search and resets pagination to the first page", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const list = listApplications as ReturnType<typeof vi.fn>;
    list.mockClear();
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/applications"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.change(screen.getByPlaceholderText("搜索公司、岗位、行业、企业性质或备注"), {
      target: { value: "AI" },
    });

    await waitFor(
      () => expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ keyword: "AI", page: 1 })),
      { timeout: 1000 },
    );
  });
});
