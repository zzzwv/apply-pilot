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

  it("applies dashboard filters before calculating guest summary, distributions, and trend", async () => {
    const source = new LocalApplicationDataSource();
    await source.create({ company: { full_name: "AI", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" }, job_title: "A", application_type: "autumn_fulltime", application_date: "2026-08-20", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "OFFER_RECEIVED" });
    await source.create({ company: { full_name: "Web", short_name: null, industry: "Web", nature: "STATE_OWNED", size: "1000-5000" }, job_title: "B", application_type: "summer_internship", application_date: "2026-08-25", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" });
    const filtered = await source.dashboard({ status: ["OFFER_RECEIVED"], industry: ["AI"], application_type: ["autumn_fulltime"], date_from: "2026-08-20", date_to: "2026-08-21", company_nature: ["PRIVATE"], company_size: ["200-500"] });
    const restored = await source.dashboard({});
    expect(filtered.summary).toMatchObject({ total: 1, offer_count: 1, offer_rate: 1 });
    expect(filtered.industries).toEqual([{ industry: "AI", count: 1, percentage: 1 }]);
    expect(filtered.trend).toEqual([{ date: "2026-08-20", count: 1 }]);
    expect(restored.summary.total).toBe(2);
  });

  it("keeps the 1,000-record guest list, filters, and dashboard usable through IndexedDB", async () => {
    const source = new LocalApplicationDataSource();
    const start = performance.now();
    const records = Array.from({ length: 1000 }, (_, index) => source.create({
      company: {
        full_name: `Performance Company ${index}`,
        short_name: null,
        industry: index % 2 === 0 ? "AI" : "Web",
        nature: index % 3 === 0 ? "PRIVATE" : "STATE_OWNED",
        size: index % 2 === 0 ? "200-500" : "1000-5000",
      },
      job_title: `Performance Engineer ${index}`,
      application_type: index % 2 === 0 ? "autumn_fulltime" : "summer_internship",
      application_date: `2026-08-${String((index % 28) + 1).padStart(2, "0")}`,
      channel: "benchmark",
      resume_version: null,
      salary: null,
      city: null,
      education_requirement: null,
      deadline: null,
      requirements: null,
      note: `phase6-local-benchmark-${index}`,
      current_status: index % 2 === 0 ? "APPLIED" : "FIRST_INTERVIEW",
    }));
    await Promise.all(records);

    const list = await source.list({ keyword: "phase6-local-benchmark", page: 1, page_size: 20 });
    const filtered = await source.list({ industry: ["AI"], application_type: ["autumn_fulltime"] });
    const dashboard = await source.dashboard({ industry: ["AI"] });

    expect(list.total).toBe(1000);
    expect(filtered.total).toBe(500);
    expect(dashboard.summary.total).toBe(500);
    expect(performance.now() - start).toBeLessThan(15_000);
  }, 20_000);
});
