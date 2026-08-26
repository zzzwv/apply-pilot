import type { ApplicationStatus, ApplicationType } from "../types/application";
import { deleteLocalDatabase, getLocalDatabase } from "./database";

export type LocalCompany = {
  full_name: string;
  short_name: string | null;
  industry: string | null;
  nature: string | null;
  size: string | null;
};

export type GuestApplicationInput = {
  company: LocalCompany;
  job_title: string;
  application_type: ApplicationType;
  application_date: string;
  channel: string;
  resume_version: string | null;
  salary: string | null;
  city: string | null;
  education_requirement: string | null;
  deadline: string | null;
  requirements: string | null;
  note: string | null;
  current_status: ApplicationStatus;
};

export type LocalApplication = GuestApplicationInput & {
  storage_key: string;
  local_id: string;
  namespace: string;
  cloud_id?: string;
  created_at: string;
  updated_at: string;
};

export type LocalStatusLog = {
  storage_key: string;
  id: string;
  namespace: string;
  application_local_id: string;
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus;
  remark: string | null;
  changed_at: string;
};

export type SyncMetadata = {
  storage_key: string;
  namespace: string;
  dismissed_at?: string;
  imported_at?: string;
};

function createUuid(): string {
  return crypto.randomUUID();
}

function storageKey(namespace: string, id: string): string {
  return `${namespace}:${id}`;
}

export class LocalApplicationRepository {
  constructor(private readonly namespace: string) {}

  async create(input: GuestApplicationInput): Promise<LocalApplication> {
    const database = await getLocalDatabase();
    const now = new Date().toISOString();
    const localId = createUuid();
    const application: LocalApplication = {
      ...input,
      local_id: localId,
      namespace: this.namespace,
      storage_key: storageKey(this.namespace, localId),
      created_at: now,
      updated_at: now,
    };
    const logId = createUuid();
    const log: LocalStatusLog = {
      id: logId,
      storage_key: storageKey(this.namespace, logId),
      namespace: this.namespace,
      application_local_id: localId,
      from_status: null,
      to_status: application.current_status,
      remark: null,
      changed_at: now,
    };
    const transaction = database.transaction(["applications", "status_logs"], "readwrite");
    await Promise.all([transaction.objectStore("applications").put(application), transaction.objectStore("status_logs").put(log), transaction.done]);
    return application;
  }

  async list(): Promise<LocalApplication[]> {
    const database = await getLocalDatabase();
    return database.getAllFromIndex("applications", "by-namespace", this.namespace);
  }

  async listStatusLogs(applicationLocalId: string): Promise<LocalStatusLog[]> {
    const database = await getLocalDatabase();
    return database.getAllFromIndex("status_logs", "by-application", [this.namespace, applicationLocalId]);
  }
}

export { deleteLocalDatabase };
