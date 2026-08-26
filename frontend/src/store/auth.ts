import type { QueryClient } from "@tanstack/react-query";
import { create } from "zustand";

import { getCurrentUser, login, register, type RegisterRequest, type User } from "../api/auth";
import { useUiStore } from "./ui";

const accessTokenKey = "job_tracker_access_token";

type AuthState = {
  user?: User;
  initialized: boolean;
  initialize: () => Promise<void>;
  login: (usernameOrEmail: string, password: string) => Promise<User>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: (queryClient: QueryClient) => void;
};

function hasUserScopedKey(queryKey: readonly unknown[], userId: string): boolean {
  return queryKey.some((part) => part === userId);
}

export const useAuthStore = create<AuthState>((set) => ({
  initialized: false,
  async initialize() {
    if (!localStorage.getItem(accessTokenKey)) {
      set({ user: undefined, initialized: true });
      return;
    }
    try {
      set({ user: await getCurrentUser(), initialized: true });
    } catch {
      localStorage.removeItem(accessTokenKey);
      set({ user: undefined, initialized: true });
    }
  },
  async login(usernameOrEmail, password) {
    const token = await login({ username_or_email: usernameOrEmail, password });
    localStorage.setItem(accessTokenKey, token.access_token);
    try {
      const user = await getCurrentUser();
      set({ user, initialized: true });
      return user;
    } catch (error) {
      localStorage.removeItem(accessTokenKey);
      throw error;
    }
  },
  async register(payload) {
    await register(payload);
  },
  logout(queryClient) {
    const userId = useAuthStore.getState().user?.id;
    if (userId) {
      const predicate = (query: { queryKey: readonly unknown[] }) => hasUserScopedKey(query.queryKey, userId);
      void queryClient.cancelQueries({ predicate });
      queryClient.removeQueries({ predicate });
    }
    useUiStore.getState().setApplicationDrawerOpen(false);
    localStorage.removeItem(accessTokenKey);
    set({ user: undefined, initialized: true });
  },
}));
