import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApplicationsPage } from ".";
import { deleteLocalDatabase } from "../../local-db/database";
import { LocalApplicationDataSource } from "../../data/localApplicationDataSource";
import { ApplicationDetailPage } from "../ApplicationDetail";
import { useAuthStore } from "../../store/auth";
import { useUiStore } from "../../store/ui";
import type { Application } from "../../types/application";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

const browserGetComputedStyle = window.getComputedStyle.bind(window);
Object.defineProperty(window, "getComputedStyle", {
  writable: true,
  value: (element: Element) => browserGetComputedStyle(element),
});

const guestApplication: Application = {
  id: "guest-application",
  user_id: "guest",
  company_id: "guest-company",
  job_title: "前端工程师",
  application_type: "autumn_fulltime",
  application_date: "2026-08-26",
  channel: "official_campus",
  resume_version: null,
  salary: null,
  city: null,
  education_requirement: null,
  deadline: null,
  requirements: null,
  note: "本地备注",
  current_status: "APPLIED",
  created_at: "2026-08-26T00:00:00.000Z",
  updated_at: "2026-08-26T00:00:00.000Z",
  company: { id: "guest-company", full_name: "本地科技", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
};

afterEach(async () => {
  cleanup();
  useAuthStore.setState({ user: undefined, initialized: false });
  useUiStore.setState({ applicationDrawerOpen: false });
  await deleteLocalDatabase();
});

describe("ApplicationsPage guest workflow", () => {
  it("shows an initial loading skeleton instead of an actionable empty state", () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const list = vi.spyOn(LocalApplicationDataSource.prototype, "list").mockImplementation(() => new Promise(() => {}));

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ApplicationsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(container.querySelector(".ant-skeleton")).not.toBeNull();
    expect(screen.queryByRole("heading", { name: "正在加载投递记录" })).toBeNull();
    list.mockRestore();
  });

  it("gives every applications filter a programmatic name", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ApplicationsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByLabelText("关键词")).toBeDefined();
    for (const label of ["投递状态", "企业性质", "投递类型", "行业", "企业规模", "排序"]) {
      expect(await screen.findByRole("combobox", { name: label })).toBeDefined();
    }
    expect(screen.getAllByLabelText("投递日期").length).toBeGreaterThan(0);
  });

  it("opens the shared create drawer when the applications route receives openCreate state", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[{ pathname: "/applications", state: { openCreate: true } }]}>
          <Routes>
            <Route path="/applications" element={<ApplicationsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("新增投递", { selector: ".ant-drawer-title" })).toBeDefined();
    expect(screen.queryByText("编辑投递", { selector: ".ant-drawer-title" })).toBeNull();
  });

  it("opens the shared create drawer from the initial empty-state action", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ApplicationsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    const emptyState = (await screen.findByRole("heading", { name: "还没有投递记录" })).closest<HTMLElement>(".empty-state");
    fireEvent.click(within(emptyState!).getByRole("button", { name: "新增投递" }));

    expect(await screen.findByText("新增投递", { selector: ".ant-drawer-title" })).toBeDefined();
  });

  it("resets a keyword no-results query to the default list parameters from the filtered empty-state action", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const list = vi.spyOn(LocalApplicationDataSource.prototype, "list");
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <ApplicationsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.change(await screen.findByPlaceholderText("搜索公司、岗位、行业、企业性质或备注"), { target: { value: "不存在的职位" } });
    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ sort: "application_date_desc", page: 1, page_size: 20, keyword: "不存在的职位" }));
    expect(await screen.findByRole("heading", { name: "暂无匹配投递记录" })).toBeDefined();
    fireEvent.click(container.querySelector(".empty-state button")!);

    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ sort: "application_date_desc", page: 1, page_size: 20 }));
    list.mockRestore();
  });

  it("opens the shared edit form from the guest detail edit action", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const source = new LocalApplicationDataSource();
    const created = await source.create({
      company: guestApplication.company,
      job_title: guestApplication.job_title,
      application_type: guestApplication.application_type,
      application_date: guestApplication.application_date,
      channel: guestApplication.channel,
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: guestApplication.note,
      current_status: guestApplication.current_status,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/applications/${created.id}`]}>
          <Routes>
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole("link", { name: "编辑" }));
    expect(await screen.findByText("编辑投递")).toBeDefined();
    expect(screen.getByDisplayValue("本地科技")).toBeDefined();
  });

  it("links a company name to its HTTP(S) application channel", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const source = new LocalApplicationDataSource();
    await source.create({
      company: guestApplication.company,
      job_title: guestApplication.job_title,
      application_type: guestApplication.application_type,
      application_date: guestApplication.application_date,
      channel: "https://jobs.example.com/frontend",
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: null,
      current_status: guestApplication.current_status,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><ApplicationsPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect((await screen.findByRole("link", { name: "本地科技" })).getAttribute("href")).toBe("https://jobs.example.com/frontend");
  });

  it("offers existing industries in the applications industry filter", async () => {
    useAuthStore.setState({ user: undefined, initialized: true });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const source = new LocalApplicationDataSource();
    await source.create({
      company: { ...guestApplication.company, industry: "人工智能" },
      job_title: guestApplication.job_title,
      application_type: guestApplication.application_type,
      application_date: guestApplication.application_date,
      channel: guestApplication.channel,
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: null,
      current_status: guestApplication.current_status,
    });

    render(<QueryClientProvider client={queryClient}><MemoryRouter><ApplicationsPage /></MemoryRouter></QueryClientProvider>);

    await screen.findByText(guestApplication.job_title);
    fireEvent.mouseDown(screen.getByRole("combobox", { name: "行业" }));

    expect(await screen.findByRole("option", { name: "人工智能" })).toBeDefined();
  });
});
