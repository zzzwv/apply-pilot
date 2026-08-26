import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { AppHeader } from ".";

describe("AppHeader", () => {
  afterEach(cleanup);

  it("marks 数据看板 as the current page on the dashboard route", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppHeader />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "数据看板" }).getAttribute("aria-current")).toBe("page");
  });

  it("marks 投递记录 as the current page on the applications route", () => {
    render(
      <MemoryRouter initialEntries={["/applications"]}>
        <AppHeader />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "投递记录" }).getAttribute("aria-current")).toBe("page");
  });

  it("exposes the ApplyPilot logo to assistive technology", () => {
    render(
      <MemoryRouter>
        <AppHeader />
      </MemoryRouter>,
    );

    expect(screen.getByRole("img", { name: "ApplyPilot" })).toBeDefined();
  });
});
