import {
  createClient,
  isAuthError,
  type AuthChangeEvent,
  type Session,
  type SupabaseClient,
} from "@supabase/supabase-js";

import type { AppConfig } from "@/config/env";

import { AuthFailure, type AuthEvent, type AuthFailureKind, type AuthGateway, type AuthSession } from "./authGateway";

/**
 * Supabase Auth (AUTH_DESIGN.md §0). Uses the PKCE flow, so email links carry
 * a one-time code instead of tokens, and the code only works in the browser
 * that asked for it. Only the publishable key is used here.
 */
export class SupabaseAuthGateway implements AuthGateway {
  private readonly client: SupabaseClient;
  private readonly origin: string;

  constructor(client: SupabaseClient, origin: string) {
    this.client = client;
    this.origin = origin;
  }

  static create(config: AppConfig, origin: string): SupabaseAuthGateway {
    const client = createClient(config.supabaseUrl, config.supabasePublishableKey, {
      auth: { flowType: "pkce", persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
    });
    return new SupabaseAuthGateway(client, origin);
  }

  async currentSession(): Promise<AuthSession | null> {
    const { data } = await this.client.auth.getSession();
    return toSession(data.session);
  }

  onChange(listener: (event: AuthEvent, session: AuthSession | null) => void): () => void {
    const { data } = this.client.auth.onAuthStateChange((event, session) => {
      const mapped = mapEvent(event);
      if (mapped) listener(mapped, toSession(session));
    });
    return () => data.subscription.unsubscribe();
  }

  async accessToken(): Promise<string | null> {
    const { data } = await this.client.auth.getSession();
    return data.session?.access_token ?? null;
  }

  async signIn(email: string, password: string): Promise<void> {
    await this.run(() => this.client.auth.signInWithPassword({ email, password }));
  }

  async signUp(email: string, password: string): Promise<void> {
    await this.run(() =>
      this.client.auth.signUp({ email, password, options: { emailRedirectTo: `${this.origin}/auth/callback` } }),
    );
  }

  async resendVerification(email: string): Promise<void> {
    await this.run(() =>
      this.client.auth.resend({ type: "signup", email, options: { emailRedirectTo: `${this.origin}/auth/callback` } }),
    );
  }

  async requestPasswordReset(email: string): Promise<void> {
    await this.run(() =>
      this.client.auth.resetPasswordForEmail(email, { redirectTo: `${this.origin}/reset-password` }),
    );
  }

  async updatePassword(password: string): Promise<void> {
    await this.run(() => this.client.auth.updateUser({ password }));
  }

  async signOut(scope: "local" | "global"): Promise<void> {
    // Even if the server can't be reached, the session is removed from this browser.
    await this.client.auth.signOut({ scope });
  }

  private async run(call: () => Promise<{ error: unknown }>): Promise<void> {
    let error: unknown;
    try {
      ({ error } = await call());
    } catch {
      throw new AuthFailure("network");
    }
    if (error) throw new AuthFailure(failureKind(error));
  }
}

function toSession(session: Session | null): AuthSession | null {
  if (!session) return null;
  return { userId: session.user.id, email: session.user.email ?? "" };
}

function mapEvent(event: AuthChangeEvent): AuthEvent | null {
  switch (event) {
    case "SIGNED_IN":
      return "signed_in";
    case "SIGNED_OUT":
      return "signed_out";
    case "TOKEN_REFRESHED":
      return "token_refreshed";
    case "PASSWORD_RECOVERY":
      return "password_recovery";
    case "USER_UPDATED":
      return "user_updated";
    default:
      return null;
  }
}

export function failureKind(error: unknown): AuthFailureKind {
  if (!isAuthError(error)) return "unknown";
  switch (error.code) {
    case "invalid_credentials":
    case "user_not_found":
      return "invalid_credentials";
    case "email_not_confirmed":
      return "email_not_confirmed";
    case "over_request_rate_limit":
    case "over_email_send_rate_limit":
      return "rate_limited";
    case "weak_password":
      return "weak_password";
    case "same_password":
      return "same_password";
  }
  if (error.status === 429) return "rate_limited";
  if (error.name === "AuthRetryableFetchError") return "network";
  return "unknown";
}
