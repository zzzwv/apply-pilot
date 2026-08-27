import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("application document", () => {
  it("uses the ApplyPilot mark as the browser favicon", () => {
    const document = readFileSync(resolve(import.meta.dirname, "index.html"), "utf8");

    expect(document).toContain('rel="icon" href="/src/assets/brand/applypilot-mark.svg"');
  });
});
