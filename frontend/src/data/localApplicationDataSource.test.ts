import "fake-indexeddb/auto";

import { afterEach, describe, expect, it } from "vitest";

import { LocalApplicationDataSource } from "./localApplicationDataSource";
import { deleteLocalDatabase } from "../local-db/applicationRepository";

describe("LocalApplicationDataSource", () => {
  afterEach(async () => deleteLocalDatabase());

  it("adapts guest records to the existing Application list contract without cloud requests", async () => {
    const source = new LocalApplicationDataSource();
    await source.create({
      company: { full_name: "Guest AI", short_name: null, industry: "人工智能", nature: "PRIVATE", size: null },
      job_title: "Backend Engineer",
      application_type: "autumn_fulltime",
      application_date: "2026-08-26",
      channel: "official_campus",
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: "local only",
      current_status: "APPLIED",
    });

    const result = await source.list({ keyword: "local only", page: 1, page_size: 20 });

    expect(result).toMatchObject({ total: 1, page: 1, page_size: 20 });
    expect(result.items[0]).toMatchObject({ user_id: "guest", job_title: "Backend Engineer", company: { full_name: "Guest AI" } });
  });
});
