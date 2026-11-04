import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ApiError } from "@/api/apiClient";
import { MAX_PROMPT_LENGTH } from "@/api/conversationApi";
import type { Screening } from "@/api/types";
import { CLEAN, makeServices, renderApp, STUDENT } from "@/test/fakes";

function signedIn(...args: Parameters<typeof makeServices>) {
  const made = makeServices(...args);
  made.auth.session = { userId: STUDENT.userId, email: STUDENT.email };
  return made;
}

const FLAGGED: Screening = {
  ...CLEAN,
  aggregatedVerdict: "FLAG",
  ruleBasedVerdict: "FLAG",
  contextAwareVerdict: "FLAG",
  requiresDecision: true,
  flags: [
    { category: "SA_ID", startIndex: 9, endIndex: 22, detectorSource: "rule", explanation: "This looks like an ID number." },
    { category: "MEDICAL", startIndex: 34, endIndex: 44, detectorSource: "context", explanation: "This mentions health information." },
  ],
};
const PROMPT = "My ID is 9203105800089 and I take sertraline";

async function typeAndSend(text: string) {
  const user = userEvent.setup();
  const box = await screen.findByLabelText("Your prompt");
  await user.click(box);
  await user.paste(text);
  await user.keyboard("{Enter}");
  return user;
}

describe("chat", () => {
  it("starts a chat with the first prompt, keeps the view, and lists it", async () => {
    const { services, chats } = signedIn();
    const router = renderApp("/", services);
    await typeAndSend("Explain recursion simply");

    expect(await screen.findByText("Here is my answer.")).toBeInTheDocument();
    expect(screen.getByText("Explain recursion simply")).toBeInTheDocument();
    const [created] = [...chats.chats.keys()];
    expect(router.state.location.pathname).toBe(`/c/${created}`);
    expect(chats.get).not.toHaveBeenCalled(); // same view: nothing reloaded
    expect(chats.sent).toEqual([{ conversationId: created, text: "Explain recursion simply", sendAnyway: false }]);
    const nav = screen.getByRole("navigation", { name: "Recent chats" });
    expect(within(nav).getByText("New conversation")).toBeInTheDocument();
    expect(screen.getByLabelText("Your prompt")).toHaveValue("");
  });

  it("asks before sending a flagged prompt and explains what the AI will see", async () => {
    const { services, chats } = signedIn();
    chats.nextResults.push({ status: "needs_decision", screening: FLAGGED, userMessage: null, assistantMessage: null });
    renderApp("/", services);
    await typeAndSend(PROMPT);

    const dialog = await screen.findByRole("dialog", { name: "Check before you send" });
    expect(within(dialog).getByText("9203105800089").tagName).toBe("MARK");
    expect(within(dialog).getByText("sertraline").tagName).toBe("MARK");
    expect(within(dialog).getByText("This looks like an ID number.")).toBeInTheDocument();
    expect(dialog).toHaveTextContent("the ID number will be hidden from the AI");
    expect(dialog).toHaveTextContent("The health information will be sent as you wrote it.");
    expect(within(dialog).getByRole("button", { name: "Edit my prompt" })).toHaveFocus();
    expect(screen.queryByText("Here is my answer.")).not.toBeInTheDocument();
  });

  it("puts the prompt back for editing", async () => {
    const { services, chats } = signedIn();
    chats.nextResults.push({ status: "needs_decision", screening: FLAGGED, userMessage: null, assistantMessage: null });
    renderApp("/", services);
    const user = await typeAndSend(PROMPT);
    await user.click(await screen.findByRole("button", { name: "Edit my prompt" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.getByLabelText("Your prompt")).toHaveValue(PROMPT);
    expect(chats.sent).toHaveLength(1);
  });

  it("sends anyway when the student chooses to", async () => {
    const { services, chats } = signedIn();
    chats.nextResults.push({ status: "needs_decision", screening: FLAGGED, userMessage: null, assistantMessage: null });
    chats.nextResults.push({
      status: "sent",
      screening: FLAGGED,
      userMessage: { messageId: "u1", role: "user", content: "My ID is [REDACTED_SA_ID] and I take sertraline", createdAt: "" },
      assistantMessage: { messageId: "a1", role: "assistant", content: "Noted.", createdAt: "" },
    });
    renderApp("/", services);
    const user = await typeAndSend(PROMPT);
    await user.click(await screen.findByRole("button", { name: "Send anyway" }));

    expect(await screen.findByText("Noted.")).toBeInTheDocument();
    expect(screen.getByTitle("ID number hidden from the AI")).toBeInTheDocument();
    expect(screen.queryByText(/9203105800089/)).not.toBeInTheDocument();
    expect(chats.sent.map((s) => s.sendAnyway)).toEqual([false, true]);
  });

  it("warns when the prompt couldn't be fully checked (fails closed)", async () => {
    const { services, chats } = signedIn();
    const unavailable: Screening = {
      ...CLEAN,
      aggregatedVerdict: "UNAVAILABLE",
      contextAwareVerdict: "UNAVAILABLE",
      requiresDecision: true,
      notice: "We couldn't fully check your prompt for sensitive information right now. Review it before sending.",
    };
    chats.nextResults.push({ status: "needs_decision", screening: unavailable, userMessage: null, assistantMessage: null });
    renderApp("/", services);
    await typeAndSend("Help with my essay");
    const dialog = await screen.findByRole("dialog", { name: "We couldn't fully check this prompt" });
    expect(dialog).toHaveTextContent("Review it before sending.");
  });

  it("keeps the prompt and explains errors, such as rate limits", async () => {
    const { services, chats } = signedIn();
    chats.nextResults.push(new ApiError(429, "rate_limited", "You're going a bit fast. Please try again in 30 seconds.", 30));
    renderApp("/", services);
    await typeAndSend("Hello there");
    expect(await screen.findByRole("alert")).toHaveTextContent("try again in 30 seconds");
    expect(screen.getByLabelText("Your prompt")).toHaveValue("Hello there");
  });

  it("opens a past chat with its messages", async () => {
    const chat = { conversationId: "c1", title: "New conversation", channel: "webapp", createdAt: "", updatedAt: "" };
    const { services, chats } = signedIn({ conversations: [chat] });
    chats.chats.get("c1")?.messages.push(
      { messageId: "u", role: "user", content: "Call me on [REDACTED_PHONE]", createdAt: "" },
      { messageId: "a", role: "assistant", content: "I can't call, but **here** is help.", createdAt: "" },
    );
    renderApp("/c/c1", services);
    expect(await screen.findByTitle("Phone number hidden from the AI")).toBeInTheDocument();
    expect(screen.getByText("here").tagName).toBe("STRONG");
  });

  it("shows a friendly page for a chat that doesn't exist (or isn't yours)", async () => {
    const { services } = signedIn();
    renderApp("/c/someone-elses", services);
    expect(await screen.findByRole("heading", { name: "Chat not found" })).toBeInTheDocument();
  });

  it("switches to another chat from the sidebar", async () => {
    const a = { conversationId: "c1", title: "New conversation", channel: "webapp", createdAt: "", updatedAt: "" };
    const b = { ...a, conversationId: "c2" };
    const { services, chats } = signedIn({ conversations: [a, b] });
    chats.chats.get("c2")?.messages.push({ messageId: "x", role: "assistant", content: "Second chat reply", createdAt: "" });
    const router = renderApp("/c/c1", services);
    const links = await within(await screen.findByRole("navigation", { name: "Recent chats" })).findAllByRole("link");
    const second = links[1];
    if (!second) throw new Error("expected two chats in the sidebar");
    await userEvent.setup().click(second);
    expect(await screen.findByText("Second chat reply")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/c/c2");
  });

  it("does not let a suspended student send", async () => {
    const { services } = signedIn({ profile: { ...STUDENT, status: "suspended" } });
    renderApp("/", services);
    expect(await screen.findByLabelText("Your prompt")).toBeDisabled();
  });

  it("uses Shift+Enter for a new line, and blocks prompts over the limit", async () => {
    const { services, chats } = signedIn();
    renderApp("/", services);
    const user = userEvent.setup();
    const box = await screen.findByLabelText("Your prompt");
    await user.type(box, "line one{Shift>}{Enter}{/Shift}line two");
    expect(box).toHaveValue("line one\nline two");
    expect(chats.sent).toHaveLength(0);

    fireEvent.change(box, { target: { value: "a".repeat(MAX_PROMPT_LENGTH + 1) } });
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByText(/4,001 \/ 4,000/)).toBeInTheDocument();
  });
});
