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

  it("renders each exact status label with an accessible semantic treatment", () => {
    Object.entries(statusLabels).forEach(([status, label]) => {
      const { unmount } = render(<StatusTag status={status as keyof typeof statusLabels} />);
      expect(screen.getByText(label).className).toContain(`status-tag--${getStatusVisual(status as keyof typeof statusLabels).category}`);
      unmount();
    });

    render(<StatusTag status="OFFER_RECEIVED" />);
    expect(screen.getByText("已获 Offer").className).not.toContain("ant-tag-has-color");
  });
});
