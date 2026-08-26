import "fake-indexeddb/auto";

import { afterEach, describe, expect, it } from "vitest";

import {
  LocalApplicationRepository,
  deleteLocalDatabase,
  type GuestApplicationInput,
} from "./applicationRepository";

const guestInput: GuestApplicationInput = {
  company: {
    full_name: "Example Holdings",
    short_name: "Example",
    industry: "人工智能",
    nature: "PRIVATE",
    size: "200-500",
  },
  job_title: "Backend Engineer",
  application_type: "autumn_fulltime",
  application_date: "2026-08-26",
  channel: "official_campus",
  resume_version: "v1",
  salary: null,
  city: "上海",
  education_requirement: "本科",
  deadline: null,
  requirements: null,
  note: "follow up",
  current_status: "APPLIED",
};

describe("LocalApplicationRepository", () => {
  afterEach(async () => {
    await deleteLocalDatabase();
  });

  it("persists a guest application and its initial status log across repository instances", async () => {
    const first = new LocalApplicationRepository("guest");
    const created = await first.create(guestInput);
    const second = new LocalApplicationRepository("guest");

    const applications = await second.list();
    const logs = await second.listStatusLogs(created.local_id);

    expect(created.local_id).toMatch(/^[\da-f-]{36}$/i);
    expect(applications).toMatchObject([{ local_id: created.local_id, job_title: "Backend Engineer" }]);
    expect(logs).toMatchObject([{ from_status: null, to_status: "APPLIED", remark: null }]);
  });

  it("filters guest records by company, job title, industry, nature, and note", async () => {
    const repository = new LocalApplicationRepository("guest");
    await repository.create(guestInput);
    await repository.create({
      ...guestInput,
      company: { full_name: "Other Corp", short_name: null, industry: "互联网", nature: "STATE_OWNED", size: null },
      job_title: "Frontend Engineer",
      note: "ordinary note",
    });

    for (const keyword of ["Example", "Backend", "人工智能", "PRIVATE", "follow up"]) {
      const items = await repository.list({ keyword });
      expect(items).toHaveLength(1);
      expect(items[0]?.job_title).toBe("Backend Engineer");
    }
  });

  it("records each guest status change in its ordered timeline", async () => {
    const repository = new LocalApplicationRepository("guest");
    const application = await repository.create(guestInput);

    await repository.changeStatus(application.local_id, "FIRST_INTERVIEW", "passed resume");

    expect(await repository.listStatusLogs(application.local_id)).toMatchObject([
      { from_status: null, to_status: "APPLIED", remark: null },
      { from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed resume" },
    ]);
  });

  it("persists user-scoped cloud mappings and removes only mapped guest applications with their logs", async () => {
    const repository = new LocalApplicationRepository("guest");
    const first = await repository.create(guestInput);
    const second = await repository.create({ ...guestInput, job_title: "Frontend Engineer" });
    await repository.changeStatus(first.local_id, "FIRST_INTERVIEW", "passed resume");

    await repository.saveCloudMappings("user-a", [{ client_sync_id: first.local_id, cloud_application_id: "cloud-a" }]);
    await repository.removeMany([first.local_id]);

    expect(await repository.count()).toBe(1);
    expect(await repository.get(first.local_id)).toBeUndefined();
    expect(await repository.listStatusLogs(first.local_id)).toEqual([]);
    expect(await repository.get(second.local_id)).toMatchObject({ local_id: second.local_id });
    expect(await repository.getCloudMapping("user-a", first.local_id)).toBe("cloud-a");
    expect(await repository.getCloudMapping("user-b", first.local_id)).toBeUndefined();
  });

  it("returns each guest application with its complete local status history for import", async () => {
    const repository = new LocalApplicationRepository("guest");
    const application = await repository.create(guestInput);
    await repository.changeStatus(application.local_id, "FIRST_INTERVIEW", "passed resume");

    expect(await repository.listForImport()).toMatchObject([{
      application: { local_id: application.local_id },
      status_logs: [
        { from_status: null, to_status: "APPLIED" },
        { from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed resume" },
      ],
    }]);
  });
});
