import type { Application, ApplicationList, ApplicationListParams, ApplicationStatus, ApplicationStatusLog, ApplicationUpdate } from "../types/application";
import {
  LocalApplicationRepository,
  type GuestApplicationInput,
  type LocalApplication,
} from "../local-db/applicationRepository";
import { calculateDashboard, type GuestDashboard } from "../dashboard/metrics";

function toApplication(application: LocalApplication): Application {
  return {
    id: application.local_id,
    user_id: "guest",
    company_id: application.local_id,
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
    created_at: application.created_at,
    updated_at: application.updated_at,
    company: {
      id: application.local_id,
      full_name: application.company.full_name,
      short_name: application.company.short_name,
      industry: application.company.industry,
      nature: application.company.nature,
      size: application.company.size,
    },
  };
}

export function applyLocalApplicationFilters(items: Application[], params: ApplicationListParams): Application[] {
  let filtered = items;
  if (params.status?.length) filtered = filtered.filter((item) => params.status!.includes(item.current_status));
  if (params.company_nature?.length) filtered = filtered.filter((item) => item.company.nature !== null && params.company_nature!.includes(item.company.nature));
  if (params.application_type?.length) filtered = filtered.filter((item) => params.application_type!.includes(item.application_type));
  if (params.industry?.length) filtered = filtered.filter((item) => item.company.industry !== null && params.industry!.includes(item.company.industry));
  if (params.company_size?.length) filtered = filtered.filter((item) => item.company.size !== null && params.company_size!.includes(item.company.size));
  if (params.date_from) filtered = filtered.filter((item) => item.application_date >= params.date_from!);
  if (params.date_to) filtered = filtered.filter((item) => item.application_date <= params.date_to!);
  return filtered;
}

export class LocalApplicationDataSource {
  private readonly repository = new LocalApplicationRepository("guest");

  async create(input: GuestApplicationInput): Promise<Application> {
    return toApplication(await this.repository.create(input));
  }

  async list(params: ApplicationListParams = {}): Promise<ApplicationList> {
    let items = applyLocalApplicationFilters((await this.repository.list({ keyword: params.keyword })).map(toApplication), params);
    if (params.sort === "application_date_asc") items.sort((a, b) => a.application_date.localeCompare(b.application_date));
    else if (params.sort === "company_name_asc") items.sort((a, b) => (a.company.short_name || a.company.full_name).localeCompare(b.company.short_name || b.company.full_name));
    else items.sort((a, b) => b.application_date.localeCompare(a.application_date));
    const page = params.page ?? 1;
    const pageSize = params.page_size ?? 20;
    return {
      items: items.slice((page - 1) * pageSize, page * pageSize),
      total: items.length,
      page,
      page_size: pageSize,
    };
  }

  async update(applicationId: string, values: ApplicationUpdate): Promise<Application> {
    return toApplication(await this.repository.update(applicationId, values));
  }

  async get(applicationId: string): Promise<Application | undefined> {
    const application = await this.repository.get(applicationId);
    return application ? toApplication(application) : undefined;
  }

  async changeStatus(applicationId: string, status: ApplicationStatus, remark?: string): Promise<Application> {
    return toApplication(await this.repository.changeStatus(applicationId, status, remark ?? null));
  }

  async getStatusLogs(applicationId: string): Promise<ApplicationStatusLog[]> {
    const logs = await this.repository.listStatusLogs(applicationId);
    return logs.map((log) => ({
      id: log.id,
      application_id: applicationId,
      from_status: log.from_status,
      to_status: log.to_status,
      remark: log.remark,
      changed_at: log.changed_at,
    }));
  }

  async remove(applicationId: string): Promise<void> {
    await this.repository.remove(applicationId);
  }

  async dashboard(params: ApplicationListParams = {}): Promise<GuestDashboard> {
    const allApplications = await this.repository.list({ keyword: params.keyword });
    const allowedIds = new Set(applyLocalApplicationFilters(allApplications.map(toApplication), params).map((application) => application.id));
    const applications = allApplications.filter((application) => allowedIds.has(application.local_id));
    const logs = (await Promise.all(applications.map((application) => this.repository.listStatusLogs(application.local_id)))).flat();
    return calculateDashboard(applications, logs);
  }
}
