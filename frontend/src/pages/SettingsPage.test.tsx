import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { makeServices, renderApp, STUDENT } from "@/test/fakes";

function signedIn(...args: Parameters<typeof makeServices>) {
  const made = makeServices(...args);
  made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
  return made;
}

describe("settings", () => {
  it("changes the display name everywhere it is shown", async () => {
    const { services, profile } = signedIn();
    renderApp("/settings", services);
    const user = userEvent.setup();
    const name = await screen.findByLabelText("Display name");
    await user.clear(name);
    await user.type(name, "  Thabo M  ");
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("Saved.")).toBeInTheDocument();
    expect(profile.updateDisplayName).toHaveBeenCalledWith("Thabo M");
    expect(screen.getByRole("button", { name: "Account menu" })).toHaveTextContent("Thabo M");
  });

  it("only saves real changes within the length limit", async () => {
    const { services, profile } = signedIn();
    renderApp("/settings", services);
    const user = userEvent.setup();
    const save = await screen.findByRole("button", { name: "Save" });
    expect(save).toBeDisabled();
    const name = screen.getByLabelText("Display name");
    await user.clear(name);
    await user.paste("x".repeat(101));
    expect(screen.getByText("Use at most 100 characters.")).toBeInTheDocument();
    expect(save).toBeDisabled();
    expect(profile.updateDisplayName).not.toHaveBeenCalled();
  });

  it("shows the email but never lets it be edited here", async () => {
    const { services } = signedIn();
    renderApp("/settings", services);
    const email = await screen.findByLabelText("Email");
    expect(email).toHaveValue(STUDENT.email);
    expect(email).toBeDisabled();
  });

  it("does not let a suspended student change their name, but lets them delete their account", async () => {
    const { services } = signedIn({ profile: { ...STUDENT, status: "suspended" } });
    renderApp("/settings", services);
    expect(await screen.findByLabelText("Display name")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Delete my account" })).toBeEnabled();
  });

  it("deletes the account only after the word is typed, then logs out", async () => {
    const { services, profile, auth } = signedIn();
    const router = renderApp("/settings", services);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Delete my account" }));
    const dialog = await screen.findByRole("dialog", { name: "Delete your account?" });
    const confirm = within(dialog).getByRole("button", { name: "Delete my account" });
    expect(confirm).toBeDisabled();
    await user.type(within(dialog).getByLabelText(/to confirm/), "delete");
    await user.click(confirm);

    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(profile.deleted).toBe(true);
    expect(auth.calls).toContain("signOut:local");
    expect(await screen.findByText("Your account and all your chats have been deleted.")).toBeInTheDocument();
  });

  it("cancelling keeps the account", async () => {
    const { services, profile } = signedIn();
    renderApp("/settings", services);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Delete my account" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(profile.deleted).toBe(false);
  });
});
