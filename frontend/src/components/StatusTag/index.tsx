import { Tag } from "antd";

import { statusLabels, type ApplicationStatus } from "../../types/application";

export const statusColors: Partial<Record<ApplicationStatus, string>> = {
  RESUME_PASSED: "blue",
  FIRST_INTERVIEW: "blue",
  SECOND_INTERVIEW: "blue",
  FINAL_INTERVIEW: "blue",
  HR_INTERVIEW: "blue",
  SALARY_NEGOTIATION: "blue",
  OFFER_RECEIVED: "green",
  SIGNED: "green",
  OFFER_REJECTED: "orange",
  RESUME_REJECTED: "red",
  INTERVIEW_REJECTED: "red",
  PROCESS_TERMINATED: "red",
};

export function StatusTag({ status }: { status: ApplicationStatus }) {
  return <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>;
}
