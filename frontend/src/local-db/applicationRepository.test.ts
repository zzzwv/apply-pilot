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
});
