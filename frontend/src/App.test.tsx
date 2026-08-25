import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

vi.mock("./api/applications", () => ({
  listApplications: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 }),
  createApplication: vi.fn(),
  deleteApplication: vi.fn(),
  updateApplication: vi.fn(),
}));

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
});
