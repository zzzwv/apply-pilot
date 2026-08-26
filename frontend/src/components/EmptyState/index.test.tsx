import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EmptyState } from ".";

describe("EmptyState", () => {
  afterEach(cleanup);

  it("renders the supplied image, semantic content, and enabled action", () => {
    render(
      <EmptyState
        image={{ src: "/empty.svg", alt: "空投递记录插图" }}
        title="还没有投递记录"
        description="从第一条投递开始管理进度。"
        action={<button type="button">新增投递</button>}
      />,
    );

    expect(screen.getByRole("img", { name: "空投递记录插图" })).toBeDefined();
    expect(screen.getByRole("heading", { name: "还没有投递记录" })).toBeDefined();
    expect(screen.getByText("从第一条投递开始管理进度。")).toBeDefined();
    expect(screen.getByRole("button", { name: "新增投递" })).toHaveProperty("disabled", false);
  });
});
