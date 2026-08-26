import type { Application, ApplicationList, ApplicationListParams, ApplicationStatus, ApplicationStatusLog, ApplicationUpdate } from "../types/application";
import {
  LocalApplicationRepository,
  type GuestApplicationInput,
  type LocalApplication,
} from "../local-db/applicationRepository";

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

export class LocalApplicationDataSource {
  private readonly repository = new LocalApplicationRepository("guest");

  async create(input: GuestApplicationInput): Promise<Application> {
    return toApplication(await this.repository.create(input));
  }

  async list(params: ApplicationListParams = {}): Promise<ApplicationList> {
    const items = (await this.repository.list({ keyword: params.keyword })).map(toApplication);
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
}
