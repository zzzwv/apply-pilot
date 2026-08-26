import "fake-indexeddb/auto";

import { afterEach, describe, expect, it, vi } from "vitest";

import { importGuestApplications } from "./guestImport";
import { LocalApplicationRepository, deleteLocalDatabase, type GuestApplicationInput } from "../local-db/applicationRepository";
import type { SyncImportApplication, SyncImportResult } from "../api/sync";

const input: GuestApplicationInput = {
  company: { full_name: "Guest Company", short_name: null, industry: "AI", nature: "PRIVATE", size: "200-500" },
  job_title: "Engineer", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official",
  resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED",
};

const result = (mappings: SyncImportResult["mappings"], failed = 0): SyncImportResult => ({ imported: mappings.length, reused: 0, failed, mappings, errors: [] });

afterEach(async () => deleteLocalDatabase());

describe("importGuestApplications", () => {
  it("sends local IDs, fields and timelines, stores returned mappings, then cleans mapped guest records after cloud refresh", async () => {
    const repository = new LocalApplicationRepository("guest");
    const application = await repository.create(input);
    await repository.changeStatus(application.local_id, "FIRST_INTERVIEW", "passed resume");
    const importBatch = vi.fn(async (payload: { applications: SyncImportApplication[] }) => result([{ client_sync_id: payload.applications[0]!.client_sync_id, cloud_application_id: "cloud-a" }]));
    const refreshCloud = vi.fn(async () => expect(await repository.count()).toBe(1));

    await importGuestApplications({ userId: "user-a", repository, importBatch, refreshCloud });

    expect(importBatch).toHaveBeenCalledWith({ applications: [expect.objectContaining({
      client_sync_id: application.local_id,
      company: input.company,
      job_title: input.job_title,
      status_logs: [
        expect.objectContaining({ from_status: null, to_status: "APPLIED" }),
        expect.objectContaining({ from_status: "APPLIED", to_status: "FIRST_INTERVIEW", remark: "passed resume" }),
      ],
    })] });
    expect(await repository.getCloudMapping("user-a", application.local_id)).toBe("cloud-a");
    expect(await repository.get(application.local_id)).toBeUndefined();
    expect(await repository.listStatusLogs(application.local_id)).toEqual([]);
  });

  it("splits imports into sequential batches of at most 200 applications", async () => {
    const applications = Array.from({ length: 201 }, (_, index) => ({
      application: { ...input, storage_key: `guest:${index}`, namespace: "guest", local_id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`, created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z" },
      status_logs: [{ storage_key: `guest:log-${index}`, id: `log-${index}`, namespace: "guest", application_local_id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`, sequence: 0, from_status: null, to_status: "APPLIED" as const, remark: null, changed_at: "2026-08-26T00:00:00.000Z" }],
    }));
    const repository = {
      listForImport: vi.fn(async () => applications), saveCloudMappings: vi.fn(), removeMany: vi.fn(),
    };
    const importBatch = vi.fn(async (payload: { applications: SyncImportApplication[] }) => result(payload.applications.map((item) => ({ client_sync_id: item.client_sync_id, cloud_application_id: `cloud-${item.client_sync_id}` }))));

    await importGuestApplications({ userId: "user-a", repository, importBatch, refreshCloud: vi.fn() });

    expect(importBatch.mock.calls.map(([payload]) => payload.applications.length)).toEqual([200, 1]);
    expect(repository.removeMany).toHaveBeenCalledWith(applications.map(({ application }) => application.local_id));
  });

  it("keeps failed guest records while cleaning imported and reused mappings after a successful cloud refresh", async () => {
    const repository = new LocalApplicationRepository("guest");
    const imported = await repository.create(input);
    const reused = await repository.create({ ...input, job_title: "Reused" });
    const failed = await repository.create({ ...input, job_title: "Failed" });
    const importBatch = async (): Promise<SyncImportResult> => ({
      imported: 1, reused: 1, failed: 1,
      mappings: [{ client_sync_id: imported.local_id, cloud_application_id: "cloud-imported" }, { client_sync_id: reused.local_id, cloud_application_id: "cloud-reused" }], errors: [],
    });

    const outcome = await importGuestApplications({ userId: "user-a", repository, importBatch, refreshCloud: vi.fn() });

    expect(outcome).toMatchObject({ imported: 1, reused: 1, failed: 1, migrated: 2 });
    expect(await repository.get(imported.local_id)).toBeUndefined();
    expect(await repository.get(reused.local_id)).toBeUndefined();
    expect(await repository.get(failed.local_id)).toMatchObject({ local_id: failed.local_id });
  });

  it("preserves all guest records on total failure or when cloud refresh fails, then can retry as reused without duplication", async () => {
    const repository = new LocalApplicationRepository("guest");
    const application = await repository.create(input);
    const failed = await importGuestApplications({ userId: "user-a", repository, importBatch: async () => ({ imported: 0, reused: 0, failed: 1, mappings: [], errors: [] }), refreshCloud: vi.fn() });
    expect(failed).toMatchObject({ failed: 1, migrated: 0 });
    expect(await repository.get(application.local_id)).toBeDefined();

    const first = await importGuestApplications({ userId: "user-a", repository, importBatch: async () => result([{ client_sync_id: application.local_id, cloud_application_id: "cloud-a" }]), refreshCloud: async () => { throw new Error("refresh interrupted"); } });
    expect(first).toMatchObject({ migrated: 1, cleaned: 0, cloud_snapshot_failed: true });
    expect(await repository.get(application.local_id)).toBeDefined();

    const retry = await importGuestApplications({ userId: "user-a", repository, importBatch: async () => ({ imported: 0, reused: 1, failed: 0, mappings: [{ client_sync_id: application.local_id, cloud_application_id: "cloud-a" }], errors: [] }), refreshCloud: vi.fn() });
    expect(retry).toMatchObject({ reused: 1, migrated: 1, cleaned: 1 });
    expect(await repository.get(application.local_id)).toBeUndefined();
  });
});
