import axios from "axios";

import { getApplication, getApplicationStatusLogs, listApplications } from "../api/applications";
import type { Application, ApplicationList, ApplicationListParams, ApplicationStatusLog } from "../types/application";
import { CloudApplicationCache, writeCloudCacheSafely } from "./cloudApplicationCache";
import { LocalApplicationDataSource } from "./localApplicationDataSource";

export type CloudReadResult<T> = {
  data: T;
  source: "cloud" | "cache";
  stale: boolean;
  cached_at?: string;
};

export function isRecoverableReadFailure(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  const status = error.response?.status;
  if (status !== undefined) return status >= 500 && status < 600;
  return true;
}

export class CloudApplicationDataSource {
  private readonly cache: CloudApplicationCache;
  private readonly localDataSource: LocalApplicationDataSource;

  constructor(private readonly userId: string) {
    this.cache = new CloudApplicationCache(userId);
    this.localDataSource = new LocalApplicationDataSource(`cloud:${userId}`, userId);
  }

  async list(params: ApplicationListParams = {}): Promise<CloudReadResult<ApplicationList>> {
    try {
      const data = await listApplications(params);
      void writeCloudCacheSafely(() => this.cache.upsertApplications(data.items));
      return { data, source: "cloud", stale: false };
    } catch (error) {
      if (!isRecoverableReadFailure(error)) throw error;
      const data = await this.localDataSource.list(params);
      return { data, source: "cache", stale: true, cached_at: await this.cache.getLatestCachedAt(data.items.map((application) => application.id)) };
    }
  }

  async get(applicationId: string): Promise<CloudReadResult<Application | undefined>> {
    try {
      const data = await getApplication(applicationId);
      void writeCloudCacheSafely(() => this.cache.upsertApplication(data));
      return { data, source: "cloud", stale: false };
    } catch (error) {
      if (!isRecoverableReadFailure(error)) throw error;
      const data = await this.localDataSource.get(applicationId);
      return { data, source: "cache", stale: true, cached_at: await this.cache.getLatestCachedAt(data ? [applicationId] : []) };
    }
  }

  async getStatusLogs(applicationId: string): Promise<CloudReadResult<ApplicationStatusLog[]>> {
    try {
      const data = await getApplicationStatusLogs(applicationId);
      void writeCloudCacheSafely(() => this.cache.replaceStatusLogs(applicationId, data));
      return { data, source: "cloud", stale: false };
    } catch (error) {
      if (!isRecoverableReadFailure(error)) throw error;
      const data = await this.localDataSource.getStatusLogs(applicationId);
      return { data, source: "cache", stale: true, cached_at: await this.cache.getLatestCachedAt([applicationId]) };
    }
  }
}
