import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/apiClient";
import { ADMIN, makeServices, renderApp, STUDENT } from "@/test/fakes";

function asAdmin() {
  const made = makeServices({ profile: ADMIN });
  made.auth.session = { userId: ADMIN.userId, email: ADMIN.email };
  return { ...made, router: renderApp("/admin", made.services), user: userEvent.setup() };
}

async function row(name: string) {
  const table = await screen.findByRole("table");
  const cell = await within(table).findByText(name);
  const tr = cell.closest("tr");
  if (!tr) throw new Error(`no row for ${name}`);
  return within(tr);
}

describe("admin panel", () => {
  it("is not shown to students, and loads nothing for them", async () => {
    const made = makeServices();
    made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    renderApp("/admin", made.services);
    expect(await screen.findByText("This page is for administrators.")).toBeInTheDocument();
    expect(made.admin.listUsers).not.toHaveBeenCalled();
    expect(made.admin.auditLog).not.toHaveBeenCalled();
  });

  it("lists accounts with their status, and says admins can't see chats", async () => {
    asAdmin();
    expect(await screen.findByText(/admins can't see anyone's chats/)).toBeInTheDocument();
    expect((await row("Thabo")).getByText("Active")).toBeInTheDocument();
    const suspended = await row("lerato@uni.ac.za");
    expect(suspended.getByText("Suspended")).toBeInTheDocument();
    expect(suspended.getByText("Not verified")).toBeInTheDocument();
  });

  it("offers no action on your own account or on other admins", async () => {
    asAdmin();
    const me = await row("admin@uni.ac.za");
    expect(me.getByText("You")).toBeInTheDocument();
    expect(me.queryByRole("button")).not.toBeInTheDocument();
  });

  it("suspends with a reason, updates the row and records it in the activity log", async () => {
    const { admin, user } = asAdmin();
    await user.click((await row("Thabo")).getByRole("button", { name: "Suspend" }));
    const dialog = await screen.findByRole("dialog", { name: "Suspend Thabo?" });
    await user.type(within(dialog).getByLabelText(/Reason/), "Repeated misuse");
    await user.click(within(dialog).getByRole("button", { name: "Suspend" }));

    expect(await screen.findByText("Thabo is now suspended.")).toBeInTheDocument();
    expect(admin.suspend).toHaveBeenCalledWith(STUDENT.userId, "Repeated misuse");
    expect((await row("Thabo")).getByText("Suspended")).toBeInTheDocument();
    const log = screen.getByRole("region", { name: "Activity log" });
    expect(await within(log).findByText("“Repeated misuse”")).toBeInTheDocument();
    expect(log).toHaveTextContent("Admin suspended Thabo");
  });

  it("reinstates a suspended account", async () => {
    const { admin, user } = asAdmin();
    await user.click((await row("lerato@uni.ac.za")).getByRole("button", { name: "Reinstate" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Reinstate" }));
    expect(await screen.findByText("lerato@uni.ac.za is now active.")).toBeInTheDocument();
    expect(admin.reinstate).toHaveBeenCalled();
  });

  it("warns when the login block couldn't be updated", async () => {
    const { admin, user } = asAdmin();
    admin.loginBlockFails = true;
    await user.click((await row("Thabo")).getByRole("button", { name: "Suspend" }));
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Suspend" }));
    expect(await screen.findByText(/blocked in SentryPrompt, but the login block couldn't be updated/)).toBeInTheDocument();
  });

  it("keeps the dialog open with the error when the action fails", async () => {
    const { admin, user } = asAdmin();
    admin.suspend.mockRejectedValueOnce(new ApiError(429, "rate_limited", "You're going a bit fast. Please try again in 20 seconds."));
    await user.click((await row("Thabo")).getByRole("button", { name: "Suspend" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Suspend" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("try again in 20 seconds");
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect((await row("Thabo")).getByText("Active")).toBeInTheDocument();
  });

  it("limits the reason to 500 characters", async () => {
    const { admin, user } = asAdmin();
    await user.click((await row("Thabo")).getByRole("button", { name: "Suspend" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByLabelText(/Reason/));
    await user.paste("x".repeat(501));
    expect(within(dialog).getByText("Use at most 500 characters.")).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Suspend" })).toBeDisabled();
    expect(admin.suspend).not.toHaveBeenCalled();
  });

  it("shows names and reasons as text, never HTML", async () => {
    const { admin, user } = asAdmin();
    const first = admin.users[0];
    if (first) first.displayName = "<img src=x onerror=alert(1)>";
    await user.click((await row("<img src=x onerror=alert(1)>")).getByRole("button", { name: "Suspend" }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText(/Reason/), "<script>alert(1)</script>");
    await user.click(within(dialog).getByRole("button", { name: "Suspend" }));
    const log = screen.getByRole("region", { name: "Activity log" });
    expect(await within(log).findByText("“<script>alert(1)</script>”")).toBeInTheDocument();
    expect(document.querySelector("img, script")).toBeNull();
  });

  it("filters the accounts on the page", async () => {
    const { user } = asAdmin();
    await row("Thabo");
    await user.type(screen.getByLabelText("Search accounts on this page"), "lerato");
    const table = screen.getByRole("table");
    expect(within(table).queryByText("Thabo")).not.toBeInTheDocument();
    expect(within(table).getByText("lerato@uni.ac.za")).toBeInTheDocument();
  });

  it("explains when the accounts can't be loaded", async () => {
    const made = makeServices({ profile: ADMIN });
    made.auth.session = { userId: ADMIN.userId, email: ADMIN.email };
    made.admin.listUsers.mockRejectedValueOnce(new ApiError(503, "auth_unavailable", "Accounts could not be loaded right now."));
    renderApp("/admin", made.services);
    expect(await screen.findByText("Accounts could not be loaded right now.")).toBeInTheDocument();
    await waitFor(() => expect(made.admin.auditLog).toHaveBeenCalled());
  });
});
