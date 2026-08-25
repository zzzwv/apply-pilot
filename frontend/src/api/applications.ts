import { apiClient, unwrap } from "./client";
import type {
  Application,
  ApplicationInput,
  ApplicationList,
  ApplicationListParams,
  ApplicationStatusLog,
  ApplicationStatus,
  ApplicationUpdate,
} from "../types/application";

export function toApplicationUpdate({ current_status: _, ...payload }: ApplicationInput): ApplicationUpdate {
  return payload;
}

function serializeListParams(params: ApplicationListParams): Record<string, string | number> {
  const serialized: Record<string, string | number> = {
    page: params.page ?? 1,
    page_size: params.page_size ?? 20,
  };
  const listFields = ["status", "company_nature", "application_type", "industry", "company_size"] as const;
  for (const field of listFields) {
    if (params[field]?.length) serialized[field] = params[field].join(",");
  }
  for (const field of ["keyword", "date_from", "date_to", "sort"] as const) {
    if (params[field]) serialized[field] = params[field];
  }
  return serialized;
}

export async function listApplications(params: ApplicationListParams = {}): Promise<ApplicationList> {
  return unwrap(apiClient.get("/applications", { params: serializeListParams(params) }));
}

export async function getApplication(applicationId: string): Promise<Application> {
  return unwrap(apiClient.get(`/applications/${applicationId}`));
}

export async function createApplication(payload: ApplicationInput): Promise<Application> {
  return unwrap(apiClient.post("/applications", payload));
}

export async function updateApplication(applicationId: string, payload: ApplicationUpdate): Promise<Application> {
  return unwrap(apiClient.put(`/applications/${applicationId}`, payload));
}

export async function deleteApplication(applicationId: string): Promise<{ deleted_count: number }> {
  return unwrap(apiClient.delete(`/applications/${applicationId}`));
}

export async function changeApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
  remark?: string,
): Promise<Application> {
  return unwrap(apiClient.patch(`/applications/${applicationId}/status`, { status, remark: remark || null }));
}

export async function getApplicationStatusLogs(applicationId: string): Promise<ApplicationStatusLog[]> {
  const payload = await unwrap<{ items: ApplicationStatusLog[] }>(apiClient.get(`/applications/${applicationId}/status-logs`));
  return payload.items;
}
