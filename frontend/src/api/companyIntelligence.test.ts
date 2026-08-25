import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";
import { confirmCompanyIntelligence, searchCompanyIntelligence } from "./companyIntelligence";

describe("company intelligence API", () => {
  it("posts an explicit web search request through the backend proxy", async () => {
    const post = vi.spyOn(apiClient, "post").mockResolvedValue({
      data: { code: 0, message: "success", data: { company: null, recruitment_links: [], sources: [], partial: false, warnings: [], allow_manual_input: true } },
    });

    await searchCompanyIntelligence("腾讯科技");

    expect(post).toHaveBeenCalledWith("/company-intelligence/search", {
      company_name: "腾讯科技",
      force_refresh: false,
    });
  });

  it("posts only user-editable persistence fields when confirming a candidate", async () => {
    const post = vi.spyOn(apiClient, "post").mockResolvedValue({
      data: { code: 0, message: "success", data: { company: { id: "11111111-1111-1111-1111-111111111111", full_name: "腾讯科技" }, created: true, aliases: [], recruitment_links: [] } },
    });

    await confirmCompanyIntelligence({
      company: { company_name: "腾讯科技", short_name: "腾讯", recruitment_links: [], sources: [] },
      aliases: ["腾讯"],
      selected_recruitment_links: [{ title: "校招官网", url: "https://join.qq.com", channel_type: "official_campus", claimed_official: true }],
    });

    expect(post).toHaveBeenCalledWith("/company-intelligence/confirm", {
      company: { company_name: "腾讯科技", short_name: "腾讯", recruitment_links: [], sources: [] },
      aliases: ["腾讯"],
      selected_recruitment_links: [{ title: "校招官网", url: "https://join.qq.com", channel_type: "official_campus", claimed_official: true }],
    });
  });
});
