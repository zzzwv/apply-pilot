import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { searchCompanyIntelligence } from "../../api/companyIntelligence";
import { searchLocalCompanies } from "../../api/companies";
import { ApplicationForm } from ".";
import type { CompanyCandidate } from "../../types/companyIntelligence";

vi.mock("../../api/companyIntelligence", () => ({
  searchCompanyIntelligence: vi.fn(),
  confirmCompanyIntelligence: vi.fn(),
}));

vi.mock("../../api/companies", () => ({
  createCompany: vi.fn(),
  searchLocalCompanies: vi.fn(),
}));

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const candidate: CompanyCandidate = {
  company_name: "小红书",
  recruitment_links: [
    {
      title: "小红书招聘",
      url: "https://job.xiaohongshu.com/",
      channel_type: "other",
      claimed_official: false,
    },
  ],
  sources: [],
};

describe("ApplicationForm", () => {
  it("groups the guest form into semantic sections while preserving manual company fields", () => {
    render(<ApplicationForm guest open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    for (const heading of ["基本信息", "企业信息", "投递信息", "补充信息"]) {
      expect(screen.getByRole("heading", { name: heading })).toBeDefined();
    }
    expect(screen.getByLabelText("本地企业名称")).toBeDefined();
    expect(screen.queryByRole("button", { name: "联网获取" })).toBeNull();
    expect(screen.getByText("登录后可使用企业信息智能获取")).toBeDefined();
  });

  it("keeps the company intelligence field in the shared cloud form", () => {
    render(<ApplicationForm open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    for (const heading of ["基本信息", "企业信息", "投递信息", "补充信息"]) {
      expect(screen.getByRole("heading", { name: heading })).toBeDefined();
    }
    expect(screen.getByRole("region", { name: "企业智能信息" })).toBeDefined();
  });

  it("fills the application channel with the selected recruitment link", async () => {
    vi.mocked(searchLocalCompanies).mockResolvedValue([]);
    vi.mocked(searchCompanyIntelligence).mockResolvedValue({
      company: candidate,
      recruitment_links: candidate.recruitment_links,
      sources: [],
      partial: false,
      warnings: [],
      allow_manual_input: true,
    });
    render(<ApplicationForm open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("企业名称"), { target: { value: "小红书" } });
    fireEvent.click(screen.getByRole("button", { name: "联网获取" }));

    await waitFor(() => expect(
      (screen.getByLabelText("投递渠道") as HTMLInputElement).value,
    ).toBe("https://job.xiaohongshu.com/"));
  });
});
