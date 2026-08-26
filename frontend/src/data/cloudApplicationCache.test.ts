import "fake-indexeddb/auto";

import { afterEach, describe, expect, it, vi } from "vitest";

import { CloudApplicationCache, writeCloudCacheSafely } from "./cloudApplicationCache";
import { deleteLocalDatabase } from "../local-db/applicationRepository";
import type { Application, ApplicationStatusLog } from "../types/application";

const application = (id: string, status: Application["current_status"] = "APPLIED"): Application => ({
  id, user_id: "server-owner", company_id: `company-${id}`, job_title: "Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official",
  resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: status,
  created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z",
  company: { id: `company-${id}`, full_name: `${id} Corp`, short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
});

const log: ApplicationStatusLog = { id: "log-a", application_id: "a", from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed", changed_at: "2026-08-26T01:00:00.000Z" };

afterEach(async () => deleteLocalDatabase());

describe("CloudApplicationCache", () => {
  it("upserts list and detail entities in the authenticated user's namespace without exposing them to another user", async () => {
    const userA = new CloudApplicationCache("user-a");
    const userB = new CloudApplicationCache("user-b");
    await userA.upsertApplications([application("a")]);
    await userA.upsertApplication(application("a", "OFFER_RECEIVED"));

    expect(await userA.getApplication("a")).toMatchObject({ local_id: "a", cloud_id: "a", namespace: "cloud:user-a", current_status: "OFFER_RECEIVED" });
    expect(await userB.getApplication("a")).toBeUndefined();
  });

  it("updates cloud status logs and removes only the deleted cloud entity with its related logs", async () => {
    const cache = new CloudApplicationCache("user-a");
    await cache.upsertApplications([application("a"), application("b")]);
    await cache.replaceStatusLogs("a", [log]);
    await cache.removeApplication("a");

    expect(await cache.getApplication("a")).toBeUndefined();
    expect(await cache.getStatusLogs("a")).toEqual([]);
    expect(await cache.getApplication("b")).toMatchObject({ local_id: "b" });
  });

  it("contains IndexedDB write failures so a successful cloud response remains usable", async () => {
    const warning = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    await expect(writeCloudCacheSafely(async () => { throw new Error("quota"); })).resolves.toBeUndefined();
    expect(warning).toHaveBeenCalled();
    warning.mockRestore();
  });
});
