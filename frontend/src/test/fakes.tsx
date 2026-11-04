import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";

import { ApiError } from "@/api/apiClient";
import type { ConversationSummary, Profile } from "@/api/types";
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

export function makeServices(
  overrides: { profile?: Profile | ApiError; conversations?: ConversationSummary[]; landingUrl?: string } = {},
) {
  const auth = new FakeAuthGateway();
  const profileResult = overrides.profile ?? STUDENT;
  const services: Services = {
    auth,
    profile: {
      get: vi.fn(async () => {
        if (profileResult instanceof ApiError) throw profileResult;
        return profileResult;
      }),
    },
    conversations: { list: vi.fn(async () => overrides.conversations ?? []) },
    landingUrl: new URL(overrides.landingUrl ?? "http://localhost:5173/"),
  };
  return { services, auth };
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
