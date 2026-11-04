import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { ApiError } from "@/api/apiClient";
import type { ChatMessage, ConversationDetail, ConversationSummary, Profile, Screening, SendResult } from "@/api/types";
import { routes } from "@/app/routes";
import { ServicesContext, type Services } from "@/app/services";
import { AuthFailure, type AuthEvent, type AuthGateway, type AuthSession } from "@/auth/authGateway";
import { AuthProvider } from "@/auth/AuthProvider";

export const STUDENT: Profile = {
  userId: "00000000-0000-4000-8000-000000000001",
  email: "thabo.m@uni.ac.za",
  displayName: "Thabo",
  role: "student",
  status: "active",
  emailVerified: true,
  createdAt: "2026-11-01T08:00:00Z",
};

export const ADMIN: Profile = { ...STUDENT, userId: "00000000-0000-4000-8000-000000000002", role: "admin" };

/** Stands in for Supabase Auth. */
export class FakeAuthGateway implements AuthGateway {
  session: AuthSession | null = null;
  failWith: AuthFailure | null = null;
  calls: string[] = [];
  private listeners: ((event: AuthEvent, session: AuthSession | null) => void)[] = [];

  async currentSession() {
    return this.session;
  }

  onChange(listener: (event: AuthEvent, session: AuthSession | null) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  async accessToken() {
    return this.session ? "fake-access-token" : null;
  }

  async signIn(email: string) {
    this.record(`signIn:${email}`);
    this.session = { userId: STUDENT.userId, email };
    this.emit("signed_in");
  }

  async signUp(email: string) {
    this.record(`signUp:${email}`);
  }

  async resendVerification(email: string) {
    this.record(`resend:${email}`);
  }

  async requestPasswordReset(email: string) {
    this.record(`reset:${email}`);
  }

  async updatePassword() {
    this.record("updatePassword");
  }

  async signOut(scope: "local" | "global") {
    this.calls.push(`signOut:${scope}`);
    this.session = null;
    this.emit("signed_out");
  }

  private record(call: string) {
    this.calls.push(call);
    if (this.failWith) throw this.failWith;
  }

  private emit(event: AuthEvent) {
    for (const listener of this.listeners) listener(event, this.session);
  }
}

export const CLEAN: Screening = {
  screeningResultId: "s1",
  aggregatedVerdict: "NO_FLAG",
  ruleBasedVerdict: "NO_FLAG",
  contextAwareVerdict: "NO_FLAG",
  requiresDecision: false,
  notice: null,
  flags: [],
};

/** Stands in for the backend's conversation endpoints, keeping chats in memory. */
export class FakeConversations {
  chats = new Map<string, ConversationDetail>();
  sent: { conversationId: string; text: string; sendAnyway: boolean }[] = [];
  /** Answers for the next send calls, in order; by default every prompt is clean. */
  nextResults: (SendResult | Error)[] = [];
  reply = "Here is my answer.";
  private counter = 0;

  constructor(initial: ConversationSummary[] = []) {
    for (const c of initial) this.chats.set(c.conversationId, { ...c, messages: [] });
  }

  list = vi.fn(async (): Promise<ConversationSummary[]> =>
    [...this.chats.values()].map((c) => ({
      conversationId: c.conversationId,
      title: c.title,
      channel: c.channel,
      createdAt: c.createdAt,
      updatedAt: c.updatedAt,
    })),
  );

  create = vi.fn(async () => {
    const id = `00000000-0000-4000-8000-${String(++this.counter).padStart(12, "0")}`;
    const now = "2026-11-04T10:00:00Z";
    const chat = { conversationId: id, title: "New conversation", channel: "webapp", createdAt: now, updatedAt: now };
    this.chats.set(id, { ...chat, messages: [] });
    return chat;
  });

  get = vi.fn(async (id: string) => {
    const chat = this.chats.get(id);
    if (!chat) throw new ApiError(404, "not_found", "Conversation not found.");
    return chat;
  });

  remove = vi.fn(async (id: string) => {
    if (!this.chats.delete(id)) throw new ApiError(404, "not_found", "Conversation not found.");
  });

  send = vi.fn(async (conversationId: string, text: string, sendAnyway: boolean): Promise<SendResult> => {
    this.sent.push({ conversationId, text, sendAnyway });
    const next = this.nextResults.shift();
    if (next instanceof Error) throw next;
    if (next) return next;
    const user: ChatMessage = { messageId: `u${this.sent.length}`, role: "user", content: text, createdAt: "2026-11-04T10:00:01Z" };
    const assistant: ChatMessage = { messageId: `a${this.sent.length}`, role: "assistant", content: this.reply, createdAt: "2026-11-04T10:00:02Z" };
    const chat = this.chats.get(conversationId);
    if (chat && chat.messages.length === 0 && chat.title === "New conversation") chat.title = text.slice(0, 60);
    chat?.messages.push(user, assistant);
    return {
      status: "sent",
      screening: CLEAN,
      userMessage: user,
      assistantMessage: assistant,
      conversationTitle: chat?.title ?? "New conversation",
    };
  });
}

export function makeServices(
  overrides: { profile?: Profile | ApiError; conversations?: ConversationSummary[]; landingUrl?: string } = {},
) {
  const auth = new FakeAuthGateway();
  let current: Profile | ApiError = overrides.profile ?? STUDENT;
  const profile = {
    deleted: false,
    get: vi.fn(async () => {
      if (current instanceof ApiError) throw current;
      return current;
    }),
    updateDisplayName: vi.fn(async (displayName: string) => {
      if (current instanceof ApiError) throw current;
      if (current.status === "suspended") throw new ApiError(403, "account_suspended", "This account is suspended.");
      current = { ...current, displayName };
      return current;
    }),
    deleteAccount: vi.fn(async () => {
      profile.deleted = true;
    }),
  };
  const conversations = new FakeConversations(overrides.conversations);
  const services: Services = {
    auth,
    profile,
    conversations,
    landingUrl: new URL(overrides.landingUrl ?? "http://localhost:5173/"),
  };
  return { services, auth, chats: conversations, profile };
}

export function renderApp(path: string, services: Services, state?: unknown) {
  const router = createMemoryRouter(routes, { initialEntries: [{ pathname: path, state }] });
  render(
    <ServicesContext.Provider value={services}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ServicesContext.Provider>,
  );
  return router;
}
