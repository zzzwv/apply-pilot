import { apiClient, unwrap } from "./client";
import type { ApplicationStatus, ApplicationType } from "../types/application";

export type SyncImportStatusLog = {
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus;
  remark: string | null;
  changed_at: string;
};

export type SyncImportApplication = {
  client_sync_id: string;
  company: { full_name: string; short_name: string | null; industry: string | null; nature: string | null; size: string | null };
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
  status_logs: SyncImportStatusLog[];
};

export type SyncImportResult = {
  imported: number;
  reused: number;
  failed: number;
  mappings: { client_sync_id: string; cloud_application_id: string }[];
  errors: unknown[];
};

export function importApplications(payload: { applications: SyncImportApplication[] }): Promise<SyncImportResult> {
  return unwrap(apiClient.post("/sync/import-applications", payload));
}
