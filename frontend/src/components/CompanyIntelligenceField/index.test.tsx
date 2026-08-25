import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { confirmCompanyIntelligence, searchCompanyIntelligence } from "../../api/companyIntelligence";
import { createCompany, searchLocalCompanies } from "../../api/companies";
import { CompanyIntelligenceField } from ".";
import type { CompanyCandidate, CompanyIntelligenceSearchResult } from "../../types/companyIntelligence";

vi.mock("../../api/companyIntelligence", () => ({
  searchCompanyIntelligence: vi.fn(),
  confirmCompanyIntelligence: vi.fn(),
}));

vi.mock("../../api/companies", () => ({
  createCompany: vi.fn(),
  searchLocalCompanies: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const localCompany = { id: "11111111-1111-1111-1111-111111111111", full_name: "腾讯科技" };
const candidate: CompanyCandidate = {
  company_name: "腾讯科技",
  short_name: "腾讯",
  industry: "互联网",
  company_nature: "PRIVATE",
  company_size: "5000以上",
  official_website: "https://www.tencent.com",
  description: "即时通信服务商",
  recruitment_links: [
    {
      title: "校招官网",
      url: "https://join.qq.com",
      channel_type: "official_campus",
      claimed_official: true,
      valid_status: "unknown",
      http_status: 403,
      verification_status: "candidate",
      confidence: 0.6,
    },
    {
      title: "实习招聘",
      url: "https://join.qq.com/intern",
      channel_type: "official_internship",
      claimed_official: true,
      valid_status: "valid",
      http_status: 200,
      verification_status: "verified",
      confidence: 0.9,
    },
  ],
  sources: [
    {
      url: "https://www.tencent.com/about",
      title: "腾讯关于我们",
      source_type: "official",
      retrieved_at: "2026-08-25T00:00:00Z",
    },
  ],
  verification_status: "candidate",
};

describe("CompanyIntelligenceField", () => {
  it("uses debounced local Company/Alias results without sending a web intelligence request", async () => {
    const localSearch = vi.mocked(searchLocalCompanies).mockResolvedValue([localCompany]);
    const onChange = vi.fn();
    render(<CompanyIntelligenceField value={undefined} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("企业名称"), { target: { value: "腾讯" } });

    await waitFor(() => expect(localSearch).toHaveBeenCalledWith("腾讯"));
    expect(searchCompanyIntelligence).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "腾讯科技（本地企业）" }));

    expect(onChange).toHaveBeenCalledWith(localCompany.id);
    expect(searchCompanyIntelligence).not.toHaveBeenCalled();
  });

  it("shows loading then an editable partial candidate preview with ordered recruitment links and sources", async () => {
    vi.mocked(searchLocalCompanies).mockResolvedValue([]);
    let resolveSearch: ((value: CompanyIntelligenceSearchResult) => void) | undefined;
    vi.mocked(searchCompanyIntelligence).mockImplementation(
      () => new Promise((resolve) => { resolveSearch = resolve; }),
    );
    render(<CompanyIntelligenceField value={undefined} onChange={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("企业名称"), { target: { value: "腾讯" } });
    fireEvent.click(screen.getByRole("button", { name: "联网获取" }));
    expect(screen.getByText("正在获取企业公开信息...")).toBeDefined();

    resolveSearch?.({ company: candidate, recruitment_links: candidate.recruitment_links, sources: candidate.sources, partial: true, warnings: ["招聘链接验证不完整"], allow_manual_input: true });

    await waitFor(() => expect(screen.getByText("部分信息暂未获取，可手动补充")).toBeDefined());
    expect((screen.getByLabelText("企业全称") as HTMLInputElement).value).toBe("腾讯科技");
    expect(screen.getByText(/暂无法验证/)).toBeDefined();
    expect(screen.getAllByText("校招官网")[0]).toBeDefined();
    expect(screen.getAllByText("实习招聘")[0]).toBeDefined();
    expect(screen.getByRole("link", { name: "腾讯关于我们" }).getAttribute("href")).toBe("https://www.tencent.com/about");
  });

  it("confirms an edited candidate and only sends persistence-safe fields before exposing its company ID", async () => {
    vi.mocked(searchLocalCompanies).mockResolvedValue([]);
    vi.mocked(searchCompanyIntelligence).mockResolvedValue({ company: candidate, recruitment_links: candidate.recruitment_links, sources: candidate.sources, partial: false, warnings: [], allow_manual_input: true });
    vi.mocked(confirmCompanyIntelligence).mockResolvedValue({ company: localCompany, created: false, aliases: ["腾讯"], recruitment_links: [] });
    const onChange = vi.fn();
    render(<CompanyIntelligenceField value={undefined} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("企业名称"), { target: { value: "腾讯" } });
    fireEvent.click(screen.getByRole("button", { name: "联网获取" }));
    await screen.findByLabelText("企业全称");
    fireEvent.change(screen.getByLabelText("企业全称"), { target: { value: "腾讯科技有限公司" } });
    fireEvent.click(screen.getByRole("button", { name: "确认企业信息" }));

    await waitFor(() => expect(confirmCompanyIntelligence).toHaveBeenCalledWith(expect.objectContaining({
      company: expect.objectContaining({ company_name: "腾讯科技有限公司" }),
    })));
    const submitted = vi.mocked(confirmCompanyIntelligence).mock.calls[0][0];
    expect(submitted.company).not.toHaveProperty("verification_status");
    expect(submitted.selected_recruitment_links[0]).not.toHaveProperty("confidence");
    expect(submitted.selected_recruitment_links[0]).not.toHaveProperty("verification_status");
    expect(onChange).toHaveBeenCalledWith(localCompany.id);
    expect(screen.getByText("已关联既有企业：腾讯科技")).toBeDefined();
  });

  it("keeps manual company creation available when intelligence search fails or is rate limited", async () => {
    vi.mocked(searchLocalCompanies).mockResolvedValue([]);
    vi.mocked(searchCompanyIntelligence).mockRejectedValue(new Error("rate limited"));
    vi.mocked(createCompany).mockResolvedValue(localCompany);
    const onChange = vi.fn();
    render(<CompanyIntelligenceField value={undefined} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("企业名称"), { target: { value: "手动企业" } });
    fireEvent.click(screen.getByRole("button", { name: "联网获取" }));
    await waitFor(() => expect(screen.getByText("联网获取失败或请求过于频繁，请手动创建企业。" )).toBeDefined());
    fireEvent.click(screen.getByRole("button", { name: "创建手动企业" }));

    await waitFor(() => expect(createCompany).toHaveBeenCalledWith("手动企业"));
    expect(onChange).toHaveBeenCalledWith(localCompany.id);
  });
});
