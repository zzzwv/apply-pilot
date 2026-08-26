import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApplicationForm } from ".";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }),
});

afterEach(() => cleanup());

describe("ApplicationForm", () => {
  it("groups the guest form into semantic sections while preserving manual company fields", () => {
    render(<ApplicationForm guest open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    for (const heading of ["基本信息", "企业信息", "投递信息", "补充信息"]) {
      expect(screen.getByRole("heading", { name: heading })).toBeDefined();
    }
    expect(screen.getByLabelText("本地企业名称")).toBeDefined();
    expect(screen.queryByRole("button", { name: "联网获取" })).toBeNull();
    expect(screen.getByText("登录后可使用企业信息智能获取")).toBeDefined();
  });

  it("keeps the company intelligence field in the shared cloud form", () => {
    render(<ApplicationForm open saving={false} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "企业信息" })).toBeDefined();
    expect(screen.getByRole("region", { name: "企业智能信息" })).toBeDefined();
  });
});
