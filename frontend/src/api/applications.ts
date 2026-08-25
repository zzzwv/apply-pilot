import { apiClient, unwrap } from "./client";
import type {
  Application,
  ApplicationInput,
  ApplicationList,
  ApplicationStatusLog,
  ApplicationStatus,
  ApplicationUpdate,
} from "../types/application";

export function toApplicationUpdate({ current_status: _, ...payload }: ApplicationInput): ApplicationUpdate {
  return payload;
}

export async function listApplications(page = 1, pageSize = 20): Promise<ApplicationList> {
  return unwrap(apiClient.get("/applications", { params: { page, page_size: pageSize } }));
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
