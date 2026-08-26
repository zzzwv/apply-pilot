import type { Application, ApplicationStatusLog } from "../types/application";
import {
  LocalApplicationRepository,
  type LocalApplication,
  type LocalStatusLog,
} from "../local-db/applicationRepository";

function toCachedApplication(application: Application): Omit<LocalApplication, "storage_key" | "namespace"> {
  return {
    local_id: application.id,
    cloud_id: application.id,
    company: {
      full_name: application.company.full_name,
      short_name: application.company.short_name,
      industry: application.company.industry,
      nature: application.company.nature,
      size: application.company.size,
    },
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
    cached_at: new Date().toISOString(),
  };
}

function toCachedStatusLog(applicationId: string, log: ApplicationStatusLog): Omit<LocalStatusLog, "storage_key" | "namespace" | "sequence"> {
  return {
    id: log.id,
    application_local_id: applicationId,
    from_status: log.from_status,
    to_status: log.to_status,
    remark: log.remark,
    changed_at: log.changed_at,
  };
}

export class CloudApplicationCache {
  private readonly repository: LocalApplicationRepository;

  constructor(userId: string) {
    this.repository = new LocalApplicationRepository(`cloud:${userId}`);
  }

  async upsertApplications(applications: Application[]): Promise<void> {
    await Promise.all(applications.map((application) => this.upsertApplication(application)));
  }

  async upsertApplication(application: Application): Promise<void> {
    await this.repository.upsertRemote(toCachedApplication(application));
  }

  async getApplication(applicationId: string): Promise<LocalApplication | undefined> {
    return this.repository.get(applicationId);
  }

  async getLatestCachedAt(applicationIds?: string[]): Promise<string | undefined> {
    const applications = applicationIds
      ? (await Promise.all(applicationIds.map((applicationId) => this.repository.get(applicationId)))).filter((application): application is LocalApplication => Boolean(application))
      : await this.repository.list();
    return applications.reduce<string | undefined>((latest, application) => !latest || (application.cached_at ?? "") > latest ? application.cached_at : latest, undefined);
  }

  async replaceStatusLogs(applicationId: string, logs: ApplicationStatusLog[]): Promise<void> {
    await this.repository.replaceRemoteStatusLogs(applicationId, logs.map((log) => toCachedStatusLog(applicationId, log)));
  }

  async getStatusLogs(applicationId: string): Promise<LocalStatusLog[]> {
    return this.repository.listStatusLogs(applicationId);
  }

  async removeApplication(applicationId: string): Promise<void> {
    await this.repository.remove(applicationId);
  }
}

export async function writeCloudCacheSafely(write: () => Promise<void>): Promise<void> {
  try {
    await write();
  } catch {
    console.warn("Cloud cache write failed");
  }
}
