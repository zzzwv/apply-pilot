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

  it("edits, changes status, and deletes guest records through the shared application contract", async () => {
    const source = new LocalApplicationDataSource();
    const created = await source.create({
      company: { full_name: "Guest AI", short_name: null, industry: null, nature: null, size: null },
      job_title: "Backend Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official_campus",
      resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED",
    });

    const edited = await source.update(created.id, { job_title: "Platform Engineer", note: "updated" });
    const statusChanged = await source.changeStatus(created.id, "FIRST_INTERVIEW", "passed resume");

    expect(edited).toMatchObject({ id: created.id, job_title: "Platform Engineer", note: "updated" });
    expect(statusChanged.current_status).toBe("FIRST_INTERVIEW");
    expect(await source.getStatusLogs(created.id)).toMatchObject([
      { from_status: null, to_status: "APPLIED" },
      { from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed resume" },
    ]);
    await source.remove(created.id);
    expect((await source.list()).total).toBe(0);
  });

  it("applies Phase 3 guest filters, sorting, and pagination", async () => {
    const source = new LocalApplicationDataSource();
    for (const [title, status, date] of [["Z role", "APPLIED", "2026-08-20"], ["A role", "FIRST_INTERVIEW", "2026-08-21"], ["B role", "APPLIED", "2026-08-22"]] as const) {
      await source.create({ company: { full_name: title, short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" }, job_title: title, application_type: "autumn_fulltime", application_date: date, channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: status });
    }
    const filtered = await source.list({ status: ["APPLIED"], company_nature: ["PRIVATE"], industry: ["AI"], sort: "application_date_asc", page: 2, page_size: 1 });
    expect(filtered).toMatchObject({ total: 2, page: 2, items: [{ job_title: "B role" }] });
  });
});
