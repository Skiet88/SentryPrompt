import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/apiClient";
import { makeServices, renderApp, STUDENT } from "@/test/fakes";

const chat = (id: string, title: string) => ({
  conversationId: id,
  title,
  channel: "webapp",
  createdAt: "2026-11-04T09:00:00Z",
  updatedAt: "2026-11-04T09:00:00Z",
});

function setup(path: string) {
  const made = makeServices({ conversations: [chat("c1", "Essay plan"), chat("c2", "Stats help")] });
  made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
  const router = renderApp(path, made.services);
  return { ...made, router, user: userEvent.setup() };
}

/** The delete button of the first chat in the sidebar. */
async function firstDeleteButton() {
  const nav = await screen.findByRole("navigation", { name: "Recent chats" });
  await within(nav).findByText("Essay plan");
  const [first] = within(nav).getAllByRole("button", { name: /^Delete chat/ });
  if (!first) throw new Error("no delete button");
  return first;
}

describe("deleting a chat", () => {
  it("asks first, with Cancel focused", async () => {
    const { user, chats } = setup("/");
    await user.click(await firstDeleteButton());
    const dialog = await screen.findByRole("dialog", { name: "Delete this chat?" });
    expect(within(dialog).getByRole("button", { name: "Cancel" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "Cancel" }));
    expect(chats.remove).not.toHaveBeenCalled();
  });

  it("deletes the chat and removes it from the list", async () => {
    const { user, chats } = setup("/");
    await user.click(await firstDeleteButton());
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(screen.queryByText("Essay plan")).not.toBeInTheDocument());
    expect(chats.remove).toHaveBeenCalledWith("c1");
    expect(screen.getByText("Stats help")).toBeInTheDocument();
  });

  it("goes back to a new chat when the open chat is deleted", async () => {
    const { user, router } = setup("/c/c1");
    await user.click(await firstDeleteButton());
    await user.click(within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("shows an error and keeps the chat when deleting fails", async () => {
    const { user, chats } = setup("/");
    chats.remove.mockRejectedValueOnce(new ApiError(503, "unavailable", "Please try again in a moment."));
    await user.click(await firstDeleteButton());
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Please try again in a moment.");
    expect(screen.getAllByText("Essay plan").length).toBeGreaterThan(0);
  });
});


describe("sidebar groups", () => {
  it("puts chats under Today, Yesterday and older headings", async () => {
    const day = 86_400_000;
    const at = (daysAgo: number) => new Date(Date.now() - daysAgo * day).toISOString();
    const made = makeServices({
      conversations: [
        { ...chat("t", "Today chat"), updatedAt: at(0) },
        { ...chat("y", "Yesterday chat"), updatedAt: at(1) },
        { ...chat("o", "Old chat"), updatedAt: at(90) },
      ],
    });
    made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
    renderApp("/", made.services);
    const nav = await screen.findByRole("navigation", { name: "Recent chats" });
    expect(within(await within(nav).findByRole("region", { name: "Today" })).getByText("Today chat")).toBeInTheDocument();
    expect(within(within(nav).getByRole("region", { name: "Yesterday" })).getByText("Yesterday chat")).toBeInTheDocument();
    expect(within(within(nav).getByRole("region", { name: "Older" })).getByText("Old chat")).toBeInTheDocument();
  });
});
