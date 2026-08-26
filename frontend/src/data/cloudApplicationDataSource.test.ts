import "fake-indexeddb/auto";

import { AxiosError, type AxiosResponse } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CloudApplicationCache } from "./cloudApplicationCache";
import { CloudApplicationDataSource } from "./cloudApplicationDataSource";
import { deleteLocalDatabase } from "../local-db/applicationRepository";
import type { Application, ApplicationStatusLog } from "../types/application";
import { getApplication, getApplicationStatusLogs, listApplications } from "../api/applications";

const application = (id: string, userId: string, status: Application["current_status"] = "APPLIED"): Application => ({
  id, user_id: userId, company_id: `company-${id}`, job_title: `${id} role`, application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: status, created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: `company-${id}`, full_name: `${id} Corp`, short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
});
const logs: ApplicationStatusLog[] = [{ id: "log-a", application_id: "a", from_status: null, to_status: "APPLIED", remark: null, changed_at: "2026-08-26T00:00:00.000Z" }];

vi.mock("../api/applications", async (importOriginal) => ({
  ...await importOriginal<typeof import("../api/applications")>(),
  listApplications: vi.fn(), getApplication: vi.fn(), getApplicationStatusLogs: vi.fn(),
}));

const mockedList = vi.mocked(listApplications);
const mockedGet = vi.mocked(getApplication);
const mockedLogs = vi.mocked(getApplicationStatusLogs);

function responseError(status: number): AxiosError {
  return new AxiosError("request failed", "ERR_BAD_RESPONSE", undefined, undefined, { status } as AxiosResponse);
}

beforeEach(() => vi.clearAllMocks());
afterEach(async () => deleteLocalDatabase());

describe("CloudApplicationDataSource", () => {
  it("falls back to the current user's cached list with shared filters and stale metadata after a network failure", async () => {
    const cache = new CloudApplicationCache("user-a");
    await cache.upsertApplications([application("a", "user-a", "APPLIED"), application("b", "user-a", "OFFER_RECEIVED")]);
    mockedList.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));

    const result = await new CloudApplicationDataSource("user-a").list({ status: ["APPLIED"] });

    expect(result).toMatchObject({ source: "cache", stale: true, cached_at: expect.any(String), data: { total: 1, items: [{ id: "a" }] } });
  });

  it("falls back to cached detail and timeline after a network failure", async () => {
    const cache = new CloudApplicationCache("user-a");
    await cache.upsertApplication(application("a", "user-a"));
    await cache.replaceStatusLogs("a", logs);
    mockedGet.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));
    mockedLogs.mockRejectedValueOnce(new AxiosError("offline", "ECONNABORTED"));
    const source = new CloudApplicationDataSource("user-a");

    expect(await source.get("a")).toMatchObject({ source: "cache", stale: true, data: { id: "a" } });
    expect(await source.getStatusLogs("a")).toMatchObject({ source: "cache", stale: true, data: [{ id: "log-a" }] });
  });

  it.each([401, 403, 404])("does not fall back for HTTP %i", async (status) => {
    await new CloudApplicationCache("user-a").upsertApplication(application("a", "user-a"));
    mockedGet.mockRejectedValueOnce(responseError(status));

    await expect(new CloudApplicationDataSource("user-a").get("a")).rejects.toMatchObject({ response: { status } });
  });

  it("never reads another user's cached namespace and replaces fallback data with a successful cloud read", async () => {
    await new CloudApplicationCache("user-a").upsertApplication(application("a", "user-a"));
    mockedList.mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"));
    const userB = new CloudApplicationDataSource("user-b");

    await expect(userB.list()).resolves.toMatchObject({ source: "cache", stale: true, data: { items: [], total: 0 } });
    mockedList.mockResolvedValueOnce({ items: [application("fresh", "user-b")], total: 1, page: 1, page_size: 20 });
    await expect(userB.list()).resolves.toMatchObject({ source: "cloud", stale: false, data: { items: [{ id: "fresh" }] } });
  });
});
