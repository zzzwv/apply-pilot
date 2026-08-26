import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { getStatusVisual, StatusTag } from ".";
import { statusLabels } from "../../types/application";

describe("StatusTag", () => {
  afterEach(cleanup);

  it("provides a nonempty color and category for every application status", () => {
    Object.keys(statusLabels).forEach((status) => {
      const visual = getStatusVisual(status as keyof typeof statusLabels);

      expect(visual.color).not.toBe("");
      expect(visual.category).toMatch(/^(neutral|progress|success|warning|danger)$/);
    });
  });

  it("keeps the status label while exposing its visual category", () => {
    render(<StatusTag status="OFFER_RECEIVED" />);

    expect(screen.getByText("已获 Offer").className).toContain("status-tag--success");
  });
});
