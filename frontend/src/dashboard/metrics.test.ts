import { describe, expect, it } from "vitest";

import { calculateDashboard } from "./metrics";
import type { LocalApplication, LocalStatusLog } from "../local-db/applicationRepository";

const application = (localId: string, status: LocalApplication["current_status"], industry: string | null, nature: string | null, date: string): LocalApplication => ({
  storage_key: `guest:${localId}`,
  local_id: localId,
  namespace: "guest",
  company: { full_name: `${localId} Corp`, short_name: null, industry, nature, size: null },
  job_title: "Engineer",
  application_type: "autumn_fulltime",
  application_date: date,
  channel: "official_campus",
  resume_version: null,
  salary: null,
  city: null,
  education_requirement: null,
  deadline: null,
  requirements: null,
  note: null,
  current_status: status,
  created_at: `${date}T00:00:00.000Z`,
  updated_at: `${date}T00:00:00.000Z`,
});

const log = (id: string, applicationLocalId: string, toStatus: LocalStatusLog["to_status"]): LocalStatusLog => ({
  storage_key: `guest:${id}`,
  id,
  namespace: "guest",
  application_local_id: applicationLocalId,
  sequence: 0,
  from_status: null,
  to_status: toStatus,
  remark: null,
  changed_at: "2026-08-26T00:00:00.000Z",
});

describe("calculateDashboard", () => {
  it("uses the backend dashboard status semantics for summary, distributions, and trend", () => {
    const applications = [
      application("interview", "FIRST_INTERVIEW", "人工智能", "PRIVATE", "2026-08-24"),
      application("offer", "OFFER_RECEIVED", null, null, "2026-08-25"),
      application("rejected", "RESUME_REJECTED", "人工智能", "PRIVATE", "2026-08-25"),
    ];
    const logs = [
      log("one", "interview", "FIRST_INTERVIEW"),
      log("two", "offer", "FIRST_INTERVIEW"),
      log("three", "offer", "OFFER_RECEIVED"),
    ];

    const result = calculateDashboard(applications, logs);

    expect(result.summary).toEqual({
      total: 3,
      in_progress: 1,
      offer_count: 1,
      interview_rate: 0.5,
      offer_rate: 1 / 3,
      rejection_rate: 1 / 3,
    });
    expect(result.statuses).toContainEqual({ status: "OFFER_RECEIVED", count: 1, percentage: 1 / 3 });
    expect(result.industries).toEqual(expect.arrayContaining([
      { industry: "人工智能", count: 2, percentage: 2 / 3 },
      { industry: "UNKNOWN", count: 1, percentage: 1 / 3 },
    ]));
    expect(result.natures).toEqual(expect.arrayContaining([
      { company_nature: "PRIVATE", count: 2, percentage: 2 / 3 },
      { company_nature: "UNKNOWN", count: 1, percentage: 1 / 3 },
    ]));
    expect(result.trend).toEqual([{ date: "2026-08-24", count: 1 }, { date: "2026-08-25", count: 2 }]);
  });
});
