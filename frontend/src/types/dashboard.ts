import type { ApplicationListParams, ApplicationStatus } from "./application";

export type DashboardFilters = Omit<ApplicationListParams, "sort" | "page" | "page_size">;

export type DashboardSummary = {
  total: number;
  in_progress: number;
  offer_count: number;
  interview_rate: number;
  offer_rate: number;
  rejection_rate: number;
};

export type StatusDistributionItem = {
  status: ApplicationStatus;
  count: number;
  percentage: number;
};

export type IndustryDistributionItem = {
  industry: string;
  count: number;
  percentage: number;
};

export type CompanyNatureDistributionItem = {
  company_nature: string;
  count: number;
  percentage: number;
};

export type TrendGranularity = "day" | "week";

export type TrendPoint = { date: string; count: number };
