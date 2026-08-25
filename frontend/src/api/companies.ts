import { apiClient, unwrap } from "./client";

export type Company = { id: string; full_name: string };

export async function searchLocalCompanies(keyword: string): Promise<Company[]> {
  return unwrap(apiClient.get("/companies/search", { params: { keyword } }));
}

export async function createCompany(fullName: string): Promise<Company> {
  return unwrap(apiClient.post("/companies", { full_name: fullName }));
}
