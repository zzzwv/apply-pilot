import { importApplications, type SyncImportApplication, type SyncImportResult } from "../api/sync";
import {
  LocalApplicationRepository,
  type CloudApplicationMapping,
  type LocalApplicationImportRecord,
} from "../local-db/applicationRepository";

const IMPORT_BATCH_SIZE = 200;

type GuestImportRepository = Pick<LocalApplicationRepository, "listForImport" | "saveCloudMappings" | "removeMany">;

type ImportGuestApplicationsOptions = {
  userId: string;
  repository?: GuestImportRepository;
  importBatch?: (payload: { applications: SyncImportApplication[] }) => Promise<SyncImportResult>;
  refreshCloud: () => Promise<void>;
};

export type GuestImportOutcome = {
  imported: number;
  reused: number;
  failed: number;
  migrated: number;
  cleaned: number;
  cloud_snapshot_failed: boolean;
};

function toSyncImportApplication({ application, status_logs }: LocalApplicationImportRecord): SyncImportApplication {
  return {
    client_sync_id: application.local_id,
    company: application.company,
    job_title: application.job_title,
    application_type: application.application_type,
    application_date: application.application_date,
    channel: application.channel,
    resume_version: application.resume_version,
    salary: application.salary,
    city: application.city,
    education_requirement: application.education_requirement,
    deadline: application.deadline,
    requirements: application.requirements,
    note: application.note,
    current_status: application.current_status,
    status_logs: status_logs.map(({ from_status, to_status, remark, changed_at }) => ({ from_status, to_status, remark, changed_at })),
  };
}

function chunks<T>(items: T[], size: number): T[][] {
  return Array.from({ length: Math.ceil(items.length / size) }, (_, index) => items.slice(index * size, (index + 1) * size));
}

export async function importGuestApplications({
  userId,
  repository = new LocalApplicationRepository("guest"),
  importBatch = importApplications,
  refreshCloud,
}: ImportGuestApplicationsOptions): Promise<GuestImportOutcome> {
  const records = await repository.listForImport();
  let imported = 0;
  let reused = 0;
  let failed = 0;
  const mappings: CloudApplicationMapping[] = [];

  for (const batch of chunks(records, IMPORT_BATCH_SIZE)) {
    const applications = batch.map(toSyncImportApplication);
    const acceptedIds = new Set(applications.map((application) => application.client_sync_id));
    try {
      const result = await importBatch({ applications });
      imported += result.imported;
      reused += result.reused;
      failed += result.failed;
      mappings.push(...result.mappings.filter((mapping) => acceptedIds.has(mapping.client_sync_id)));
    } catch {
      failed += batch.length;
    }
  }

  const successfulMappings = Array.from(new Map(mappings.map((mapping) => [mapping.client_sync_id, mapping])).values());
  if (successfulMappings.length === 0) return { imported, reused, failed, migrated: 0, cleaned: 0, cloud_snapshot_failed: false };

  await repository.saveCloudMappings(userId, successfulMappings);
  try {
    await refreshCloud();
  } catch {
    return { imported, reused, failed, migrated: successfulMappings.length, cleaned: 0, cloud_snapshot_failed: true };
  }

  const localIds = successfulMappings.map((mapping) => mapping.client_sync_id);
  await repository.removeMany(localIds);
  return { imported, reused, failed, migrated: successfulMappings.length, cleaned: localIds.length, cloud_snapshot_failed: false };
}
