import axios from "axios";

export const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1" });

type ApiEnvelope<T> = { code: number; message: string; data: T };

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("job_tracker_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function unwrap<T>(request: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const response = await request;
  return response.data.data;
}
