import { describe, expect, it, vi } from "vitest";

import * as applications from "./applications";
import { apiClient } from "./client";
import type { ApplicationInput, ApplicationUpdate } from "../types/application";

describe("toApplicationUpdate", () => {
  it("removes current_status so normal edits cannot bypass status history", () => {
    const convert = (applications as { toApplicationUpdate?: (payload: ApplicationInput) => ApplicationUpdate }).toApplicationUpdate;
    const payload: ApplicationInput = {
      company_id: "123e4567-e89b-12d3-a456-426614174000",
      job_title: "Backend Engineer",
      application_type: "autumn_fulltime",
      application_date: "2026-08-25",
      channel: "official_campus",
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: "updated",
      current_status: "APPLIED",
    };

    const { current_status: _, ...expected } = payload;
    expect(convert).toBeTypeOf("function");
    expect(convert!(payload)).toEqual(expected);
  });
});

describe("listApplications", () => {
  it("sends the stable Phase 3 query parameters to the list endpoint", async () => {
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({
      data: { code: 0, message: "ok", data: { items: [], total: 0, page: 2, page_size: 50 } },
    });

    await applications.listApplications({
      keyword: "AI",
      status: ["FIRST_INTERVIEW", "SECOND_INTERVIEW"],
      company_nature: ["STATE_OWNED"],
      application_type: ["autumn_fulltime"],
      industry: ["人工智能"],
      date_from: "2026-08-01",
      date_to: "2026-08-31",
      company_size: ["1000-5000"],
      sort: "status_priority_desc",
      page: 2,
      page_size: 50,
    });

    expect(get).toHaveBeenCalledWith("/applications", {
      params: {
        keyword: "AI",
        status: "FIRST_INTERVIEW,SECOND_INTERVIEW",
        company_nature: "STATE_OWNED",
        application_type: "autumn_fulltime",
        industry: "人工智能",
        date_from: "2026-08-01",
        date_to: "2026-08-31",
        company_size: "1000-5000",
        sort: "status_priority_desc",
        page: 2,
        page_size: 50,
      },
    });
  });
});
