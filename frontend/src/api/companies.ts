import { apiClient, unwrap } from "./client";

export type Company = { id: string; full_name: string };

export type CompanyDetail = Company & {
  short_name: string | null;
  industry: string | null;
  nature: string | null;
  size: string | null;
  official_website: string | null;
  business_description: string | null;
};

export type CompanyUpdate = Omit<CompanyDetail, "id">;

export async function searchLocalCompanies(keyword: string): Promise<Company[]> {
  return unwrap(apiClient.get("/companies/search", { params: { keyword } }));
}

export async function createCompany(fullName: string): Promise<Company> {
  return unwrap(apiClient.post("/companies", { full_name: fullName }));
}

export async function getCompany(companyId: string): Promise<CompanyDetail> {
  return unwrap(apiClient.get(`/companies/${companyId}`));
}

export async function updateCompany(companyId: string, payload: Partial<CompanyUpdate>): Promise<CompanyDetail> {
  return unwrap(apiClient.patch(`/companies/${companyId}`, payload));
}
