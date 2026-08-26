// @vitest-environment node

import { describe, expect, it } from "vitest";

import viteConfig from "../vite.config";

describe("development API proxy", () => {
  it("forwards frontend API requests to the local backend", () => {
    expect(viteConfig.server?.proxy).toMatchObject({
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    });
  });
});
