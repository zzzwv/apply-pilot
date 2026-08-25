export type ApplicationType = "autumn_fulltime" | "spring_fulltime" | "summer_internship" | "daily_internship";

export type ApplicationSort =
  | "application_date_asc"
  | "application_date_desc"
  | "company_name_asc"
  | "status_priority_desc";

export type ApplicationStatus =
  | "NOT_APPLIED"
  | "APPLIED"
  | "RESUME_PASSED"
  | "FIRST_INTERVIEW"
  | "SECOND_INTERVIEW"
  | "FINAL_INTERVIEW"
  | "HR_INTERVIEW"
  | "SALARY_NEGOTIATION"
  | "OFFER_RECEIVED"
  | "OFFER_REJECTED"
  | "RESUME_REJECTED"
  | "INTERVIEW_REJECTED"
  | "PROCESS_TERMINATED"
  | "SIGNED";

export type ApplicationCompany = {
  id: string;
  full_name: string;
  short_name: string | null;
  industry: string | null;
  nature: string | null;
  size: string | null;
};

export type Application = {
  id: string;
  user_id: string;
  company_id: string;
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
  created_at: string;
  updated_at: string;
  company: ApplicationCompany;
};

export type ApplicationInput = Omit<Application, "id" | "user_id" | "created_at" | "updated_at" | "company">;
export type ApplicationUpdate = Partial<Omit<ApplicationInput, "current_status">>;

export type ApplicationList = {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
};

export type ApplicationListParams = {
  keyword?: string;
  status?: ApplicationStatus[];
  company_nature?: string[];
  application_type?: ApplicationType[];
  industry?: string[];
  date_from?: string;
  date_to?: string;
  company_size?: string[];
  sort?: ApplicationSort;
  page?: number;
  page_size?: number;
};

export type ApplicationStatusLog = {
  id: string;
  application_id: string;
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus;
  remark: string | null;
  changed_at: string;
};

export const statusLabels: Record<ApplicationStatus, string> = {
  NOT_APPLIED: "未投递",
  APPLIED: "已投简历",
  RESUME_PASSED: "简历通过",
  FIRST_INTERVIEW: "一面",
  SECOND_INTERVIEW: "二面",
  FINAL_INTERVIEW: "终面",
  HR_INTERVIEW: "HR 面",
  SALARY_NEGOTIATION: "谈薪",
  OFFER_RECEIVED: "已获 Offer",
  OFFER_REJECTED: "已拒绝 Offer",
  RESUME_REJECTED: "简历淘汰",
  INTERVIEW_REJECTED: "面试淘汰",
  PROCESS_TERMINATED: "流程终止",
  SIGNED: "已签约",
};

export const applicationTypeLabels: Record<ApplicationType, string> = {
  autumn_fulltime: "秋招全职",
  spring_fulltime: "春招全职",
  summer_internship: "暑期实习",
  daily_internship: "日常实习",
};
