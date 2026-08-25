import { apiClient, unwrap } from "./client";
import type {
  CompanyNatureDistributionItem,
  DashboardFilters,
  DashboardSummary,
  IndustryDistributionItem,
  StatusDistributionItem,
  TrendGranularity,
  TrendPoint,
} from "../types/dashboard";

function serializeFilters(filters: DashboardFilters): Record<string, string> {
  const params: Record<string, string> = {};
  const listFields = ["status", "company_nature", "application_type", "industry", "company_size"] as const;
  for (const field of listFields) {
    if (filters[field]?.length) params[field] = filters[field].join(",");
  }
  for (const field of ["keyword", "date_from", "date_to"] as const) {
    if (filters[field]) params[field] = filters[field];
  }
  return params;
}

export function getDashboardSummary(filters: DashboardFilters): Promise<DashboardSummary> {
  return unwrap(apiClient.get("/dashboard/summary", { params: serializeFilters(filters) }));
}

export async function getStatusDistribution(filters: DashboardFilters): Promise<StatusDistributionItem[]> {
  return (await unwrap<{ items: StatusDistributionItem[] }>(
    apiClient.get("/dashboard/status-distribution", { params: serializeFilters(filters) }),
  )).items;
}

export async function getIndustryDistribution(filters: DashboardFilters): Promise<IndustryDistributionItem[]> {
  return (await unwrap<{ items: IndustryDistributionItem[] }>(
    apiClient.get("/dashboard/industry-distribution", { params: serializeFilters(filters) }),
  )).items;
}

export async function getCompanyNatureDistribution(filters: DashboardFilters): Promise<CompanyNatureDistributionItem[]> {
  return (await unwrap<{ items: CompanyNatureDistributionItem[] }>(
    apiClient.get("/dashboard/company-nature-distribution", { params: serializeFilters(filters) }),
  )).items;
}

export async function getApplicationTrend(
  filters: DashboardFilters,
  granularity: TrendGranularity,
): Promise<TrendPoint[]> {
  return (await unwrap<{ items: TrendPoint[] }>(
    apiClient.get("/dashboard/application-trend", {
      params: { ...serializeFilters(filters), granularity },
    }),
  )).items;
}
