import { Tag } from "antd";

import { statusLabels, type ApplicationStatus } from "../../types/application";

type StatusCategory = "neutral" | "progress" | "success" | "warning" | "danger";

type StatusVisual = {
  color: string;
  category: StatusCategory;
};

const statusVisuals: Record<ApplicationStatus, StatusVisual> = {
  NOT_APPLIED: { color: "#9CA3AF", category: "neutral" },
  APPLIED: { color: "#9CA3AF", category: "neutral" },
  RESUME_PASSED: { color: "#3B82F6", category: "progress" },
  FIRST_INTERVIEW: { color: "#3B82F6", category: "progress" },
  SECOND_INTERVIEW: { color: "#3B82F6", category: "progress" },
  FINAL_INTERVIEW: { color: "#3B82F6", category: "progress" },
  HR_INTERVIEW: { color: "#3B82F6", category: "progress" },
  SALARY_NEGOTIATION: { color: "#3B82F6", category: "progress" },
  OFFER_RECEIVED: { color: "#22C55E", category: "success" },
  OFFER_REJECTED: { color: "#F59E0B", category: "warning" },
  RESUME_REJECTED: { color: "#EF4444", category: "danger" },
  INTERVIEW_REJECTED: { color: "#EF4444", category: "danger" },
  PROCESS_TERMINATED: { color: "#EF4444", category: "danger" },
  SIGNED: { color: "#22C55E", category: "success" },
};

export function getStatusVisual(status: ApplicationStatus): StatusVisual {
  return statusVisuals[status];
}

export function StatusTag({ status }: { status: ApplicationStatus }) {
  const visual = getStatusVisual(status);

  return <Tag color={visual.color} className={`status-tag status-tag--${visual.category}`}>{statusLabels[status]}</Tag>;
}
