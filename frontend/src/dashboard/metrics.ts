import type {
  CompanyNatureDistributionItem,
  DashboardSummary,
  IndustryDistributionItem,
  StatusDistributionItem,
  TrendPoint,
} from "../types/dashboard";
import type { ApplicationStatus } from "../types/application";
import type { LocalApplication, LocalStatusLog } from "../local-db/applicationRepository";

const inProgressStatuses = new Set<ApplicationStatus>([
  "RESUME_PASSED", "FIRST_INTERVIEW", "SECOND_INTERVIEW", "FINAL_INTERVIEW", "HR_INTERVIEW", "SALARY_NEGOTIATION",
]);
const offerStatuses = new Set<ApplicationStatus>(["OFFER_RECEIVED", "SIGNED"]);
const rejectionStatuses = new Set<ApplicationStatus>(["RESUME_REJECTED", "INTERVIEW_REJECTED", "PROCESS_TERMINATED"]);
const interviewStartedStatuses = new Set<ApplicationStatus>([
  "FIRST_INTERVIEW", "SECOND_INTERVIEW", "FINAL_INTERVIEW", "HR_INTERVIEW", "SALARY_NEGOTIATION", "OFFER_RECEIVED", "OFFER_REJECTED", "SIGNED", "INTERVIEW_REJECTED",
]);
const interviewPassedStatuses = new Set<ApplicationStatus>([
  "SECOND_INTERVIEW", "FINAL_INTERVIEW", "HR_INTERVIEW", "SALARY_NEGOTIATION", "OFFER_RECEIVED", "OFFER_REJECTED", "SIGNED",
]);

function countBy<T extends string>(values: T[]): Array<[T, number]> {
  const counts = new Map<T, number>();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return [...counts.entries()].sort(([firstName, firstCount], [secondName, secondCount]) => secondCount - firstCount || firstName.localeCompare(secondName));
}

export type GuestDashboard = {
  summary: DashboardSummary;
  statuses: StatusDistributionItem[];
  industries: IndustryDistributionItem[];
  natures: CompanyNatureDistributionItem[];
  trend: TrendPoint[];
};

export function calculateDashboard(applications: LocalApplication[], logs: LocalStatusLog[]): GuestDashboard {
  const total = applications.length;
  const started = new Set(logs.filter((log) => interviewStartedStatuses.has(log.to_status)).map((log) => log.application_local_id));
  const passed = new Set(logs.filter((log) => interviewPassedStatuses.has(log.to_status)).map((log) => log.application_local_id));
  const summary: DashboardSummary = {
    total,
    in_progress: applications.filter((application) => inProgressStatuses.has(application.current_status)).length,
    offer_count: applications.filter((application) => offerStatuses.has(application.current_status)).length,
    interview_rate: started.size ? passed.size / started.size : 0,
    offer_rate: total ? applications.filter((application) => offerStatuses.has(application.current_status)).length / total : 0,
    rejection_rate: total ? applications.filter((application) => rejectionStatuses.has(application.current_status)).length / total : 0,
  };
  const statuses = countBy(applications.map((application) => application.current_status)).map(([status, count]) => ({ status, count, percentage: total ? count / total : 0 }));
  const industries = countBy(applications.map((application) => application.company.industry || "UNKNOWN")).map(([industry, count]) => ({ industry, count, percentage: total ? count / total : 0 }));
  const natures = countBy(applications.map((application) => application.company.nature || "UNKNOWN")).map(([company_nature, count]) => ({ company_nature, count, percentage: total ? count / total : 0 }));
  const trend = countBy(applications.map((application) => application.application_date)).map(([date, count]) => ({ date, count })).sort((first, second) => first.date.localeCompare(second.date));
  return { summary, statuses, industries, natures, trend };
}
