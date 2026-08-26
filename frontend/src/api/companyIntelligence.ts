import { apiClient, unwrap } from "./client";
import type {
  CompanyIntelligenceConfirmRequest,
  CompanyIntelligenceConfirmResponse,
  CompanyIntelligenceSearchResult,
} from "../types/companyIntelligence";

export async function searchCompanyIntelligence(
  companyName: string,
  forceRefresh = false,
  signal?: AbortSignal,
): Promise<CompanyIntelligenceSearchResult> {
  const payload = {
    company_name: companyName,
    force_refresh: forceRefresh,
  };
  return unwrap(signal
    ? apiClient.post("/company-intelligence/search", payload, { signal })
    : apiClient.post("/company-intelligence/search", payload));
}

export async function confirmCompanyIntelligence(
  payload: CompanyIntelligenceConfirmRequest,
): Promise<CompanyIntelligenceConfirmResponse> {
  return unwrap(apiClient.post("/company-intelligence/confirm", payload));
}
