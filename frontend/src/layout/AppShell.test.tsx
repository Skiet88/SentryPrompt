import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ADMIN, makeServices, renderApp, STUDENT } from "@/test/fakes";

function signedIn(...args: Parameters<typeof makeServices>) {
  const made = makeServices(...args);
  made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
  return made;
}

describe("app shell", () => {
  it("greets the student and explains what happens to prompts", async () => {
    const { services } = signedIn();
    renderApp("/", services);
    expect(await screen.findByRole("heading", { name: /, Thabo$/ })).toBeInTheDocument();
    expect(screen.getByText(/checked for personal information/)).toBeInTheDocument();
  });

  it("uses the start of the email when there is no display name", async () => {
    const { services } = signedIn({ profile: { ...STUDENT, displayName: "" } });
    renderApp("/", services);
    expect(await screen.findByRole("heading", { name: /, thabo\.m$/ })).toBeInTheDocument();
  });

  it("lists recent chats, with chat titles shown as text", async () => {
    const title = "<script>alert(1)</script>";
    const { services } = signedIn({
      conversations: [{ conversationId: "c1", title, channel: "webapp", createdAt: "", updatedAt: "" }],
    });
    renderApp("/", services);
    const nav = await screen.findByRole("navigation", { name: "Recent chats" });
    expect(await within(nav).findByText(title)).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });

  it("hides the admin panel from students", async () => {
    const { services } = signedIn();
    renderApp("/", services);
    await userEvent.setup().click(await screen.findByRole("button", { name: "Account menu" }));
    expect(await screen.findByRole("menuitem", { name: "Settings" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: "Admin panel" })).not.toBeInTheDocument();
  });

  it("shows the admin panel to admins", async () => {
    const { services } = signedIn({ profile: ADMIN });
    renderApp("/", services);
    await userEvent.setup().click(await screen.findByRole("button", { name: "Account menu" }));
    expect(await screen.findByRole("menuitem", { name: "Admin panel" })).toBeInTheDocument();
  });

  it("logs out from the account menu", async () => {
    const { services, auth } = signedIn();
    const router = renderApp("/", services);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Account menu" }));
    await user.click(await screen.findByRole("menuitem", { name: "Log out" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(auth.calls).toContain("signOut:local");
  });

  it("tells a suspended student why they can't chat", async () => {
    const { services } = signedIn({ profile: { ...STUDENT, status: "suspended" } });
    renderApp("/", services);
    expect(await screen.findByText(/Your account is suspended/)).toBeInTheDocument();
  });

  it("sends logged-in users away from the login page", async () => {
    const { services } = signedIn();
    const router = renderApp("/login", services);
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });
});
