import { QueryClient } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentUser } from "../api/auth";
import { useAuthStore } from "./auth";

vi.mock("../api/auth", () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}));

const mockedGetCurrentUser = vi.mocked(getCurrentUser);

describe("useAuthStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ user: undefined, initialized: false });
    vi.clearAllMocks();
  });

  afterEach(() => localStorage.clear());

  it("initializes the current user from an existing access token", async () => {
    localStorage.setItem("job_tracker_access_token", "token");
    mockedGetCurrentUser.mockResolvedValue({ id: "user-a", username: "alice", email: "a@example.com" });

    await useAuthStore.getState().initialize();

    expect(useAuthStore.getState()).toMatchObject({
      initialized: true,
      user: { id: "user-a", username: "alice", email: "a@example.com" },
    });
  });

  it("logout removes the token and user-scoped application and dashboard queries", () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(["applications", "cloud", "user-a"], { items: [] });
    queryClient.setQueryData(["dashboard", "cloud", "user-a", "summary"], { total: 1 });
    queryClient.setQueryData(["applications", "cloud", "user-b"], { items: ["other"] });
    localStorage.setItem("job_tracker_access_token", "token");
    useAuthStore.setState({
      user: { id: "user-a", username: "alice", email: "a@example.com" },
      initialized: true,
    });

    useAuthStore.getState().logout(queryClient);

    expect(localStorage.getItem("job_tracker_access_token")).toBeNull();
    expect(useAuthStore.getState()).toMatchObject({ initialized: true, user: undefined });
    expect(queryClient.getQueryData(["applications", "cloud", "user-a"])).toBeUndefined();
    expect(queryClient.getQueryData(["dashboard", "cloud", "user-a", "summary"])).toBeUndefined();
    expect(queryClient.getQueryData(["applications", "cloud", "user-b"])).toEqual({ items: ["other"] });
  });
});
