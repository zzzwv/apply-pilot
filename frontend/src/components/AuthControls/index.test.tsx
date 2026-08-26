import { QueryClient } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "../../store/auth";
import { AuthControls } from ".";

describe("AuthControls", () => {
  beforeEach(() => {
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
});
