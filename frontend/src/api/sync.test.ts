import { describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";
import { importApplications } from "./sync";

vi.mock("./client", () => ({
  apiClient: { post: vi.fn() },
  unwrap: vi.fn((request) => request.then((response: { data: { data: unknown } }) => response.data.data)),
}));

describe("importApplications", () => {
  it("posts only the typed batch payload to the existing sync endpoint", async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { data: { imported: 1, reused: 0, failed: 0, mappings: [{ client_sync_id: "sync-id", cloud_application_id: "cloud-id" }], errors: [] } } } as never);

    await expect(importApplications({ applications: [] })).resolves.toMatchObject({ imported: 1, mappings: [{ client_sync_id: "sync-id", cloud_application_id: "cloud-id" }] });
    expect(apiClient.post).toHaveBeenCalledWith("/sync/import-applications", { applications: [] });
  });
});
