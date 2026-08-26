import { apiClient, unwrap } from "./client";

export type User = {
  id: string;
  username: string;
  email: string;
};

export type LoginRequest = {
  username_or_email: string;
  password: string;
};

export type RegisterRequest = {
  username: string;
  email: string;
  password: string;
};

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return unwrap(apiClient.post("/auth/login", payload));
}

export function register(payload: RegisterRequest): Promise<User> {
  return unwrap(apiClient.post("/auth/register", payload));
}

export function getCurrentUser(): Promise<User> {
  return unwrap(apiClient.get("/auth/me"));
}
