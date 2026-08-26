import "fake-indexeddb/auto";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
});
