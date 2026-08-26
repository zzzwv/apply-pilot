import { QueryClient } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentUser } from "../api/auth";
import { CloudApplicationCache } from "../data/cloudApplicationCache";
import { LocalApplicationRepository, deleteLocalDatabase } from "../local-db/applicationRepository";
import { useAuthStore } from "./auth";
import { useUiStore } from "./ui";

import "fake-indexeddb/auto";

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
    useUiStore.setState({ applicationDrawerOpen: false });
    vi.clearAllMocks();
  });

  afterEach(async () => {
    localStorage.clear();
    await deleteLocalDatabase();
  });

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

  it("cancels current-user queries, resets user UI state, and preserves guest and cloud IndexedDB namespaces", async () => {
    const queryClient = new QueryClient();
    const cancelQueries = vi.spyOn(queryClient, "cancelQueries");
    const guestRepository = new LocalApplicationRepository("guest");
    const guest = await guestRepository.create({ company: { full_name: "Guest Corp", short_name: null, industry: null, nature: null, size: null }, job_title: "Guest", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED" });
    await new CloudApplicationCache("user-a").upsertApplication({ id: "cloud-a", user_id: "user-a", company_id: "company-a", job_title: "Cloud", application_type: "autumn_fulltime", application_date: "2026-08-26", channel: "official", resume_version: null, salary: null, city: null, education_requirement: null, deadline: null, requirements: null, note: null, current_status: "APPLIED", created_at: "2026-08-26T00:00:00.000Z", updated_at: "2026-08-26T00:00:00.000Z", company: { id: "company-a", full_name: "Cloud Corp", short_name: null, industry: null, nature: null, size: null } });
    queryClient.setQueryData(["application", "cloud", "user-a", "cloud-a"], { id: "cloud-a" });
    useUiStore.setState({ applicationDrawerOpen: true });
    useAuthStore.setState({ user: { id: "user-a", username: "alice", email: "a@example.com" }, initialized: true });

    useAuthStore.getState().logout(queryClient);

    expect(cancelQueries).toHaveBeenCalled();
    expect(queryClient.getQueryData(["application", "cloud", "user-a", "cloud-a"])).toBeUndefined();
    expect(useUiStore.getState().applicationDrawerOpen).toBe(false);
    expect(await guestRepository.get(guest.local_id)).toBeDefined();
    expect(await new CloudApplicationCache("user-a").getApplication("cloud-a")).toBeDefined();
  });
});
