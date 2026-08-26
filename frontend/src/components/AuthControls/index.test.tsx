import { QueryClient } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "../../store/auth";
import { AuthControls } from ".";

describe("AuthControls", () => {
  afterEach(cleanup);

  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => undefined,
        removeListener: () => undefined,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        dispatchEvent: () => false,
      }),
    });
    useAuthStore.setState({ user: undefined, initialized: true });
  });

  it("shows login and registration for a guest, then identity and logout for a user", async () => {
    const queryClient = new QueryClient();
    render(<AuthControls queryClient={queryClient} />);

    expect(screen.getByRole("button", { name: /登\s*录/ })).toBeDefined();
    expect(screen.getByRole("button", { name: /注\s*册/ })).toBeDefined();

    await act(async () => {
      useAuthStore.setState({
        user: { id: "user-a", username: "alice", email: "a@example.com" },
        initialized: true,
      });
    });

    expect(await screen.findByText("a@example.com")).toBeDefined();
    expect(screen.getByRole("button", { name: /退\s*出\s*登\s*录/ })).toBeDefined();
  });

  it("keeps the login trigger and shows the branded login introduction", () => {
    const queryClient = new QueryClient();
    render(<AuthControls queryClient={queryClient} />);

    fireEvent.click(screen.getByRole("button", { name: /登\s*录/ }));

    expect(screen.getByText("继续你的求职进程")).toBeDefined();
    expect(screen.getByText("查看最新投递动态和数据。")).toBeDefined();
    const artwork = document.querySelector(".auth-controls__intro img");
    expect(artwork?.getAttribute("alt")).toBe("");
    expect(artwork?.getAttribute("aria-hidden")).toBe("true");
  });
});
