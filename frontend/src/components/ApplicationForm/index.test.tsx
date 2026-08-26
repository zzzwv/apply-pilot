import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApplicationForm } from ".";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

describe("ApplicationForm", () => {
  it("uses manual local company fields for a guest without exposing Kimi intelligence", () => {
    render(<ApplicationForm guest open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("本地企业名称")).toBeDefined();
    expect(screen.queryByRole("button", { name: "联网获取" })).toBeNull();
    expect(screen.getByText("登录后可使用企业信息智能获取")).toBeDefined();
  });
});
