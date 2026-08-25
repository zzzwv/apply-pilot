import { apiClient, unwrap } from "./client";
import type {
  CompanyIntelligenceConfirmRequest,
  CompanyIntelligenceConfirmResponse,
  CompanyIntelligenceSearchResult,
} from "../types/companyIntelligence";

export async function searchCompanyIntelligence(
  companyName: string,
  forceRefresh = false,
): Promise<CompanyIntelligenceSearchResult> {
  return unwrap(apiClient.post("/company-intelligence/search", {
    company_name: companyName,
    force_refresh: forceRefresh,
  }));
}

export async function confirmCompanyIntelligence(
  payload: CompanyIntelligenceConfirmRequest,
): Promise<CompanyIntelligenceConfirmResponse> {
  return unwrap(apiClient.post("/company-intelligence/confirm", payload));
}
