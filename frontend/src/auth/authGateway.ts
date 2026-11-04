/**
 * What the app needs from the login provider. The pages depend on this
 * interface, not on Supabase, so tests can use a fake and the provider could
 * be swapped without touching the UI.
 */

export interface AuthSession {
  userId: string;
  email: string;
}

export type AuthEvent = "signed_in" | "signed_out" | "token_refreshed" | "password_recovery" | "user_updated";

export type AuthFailureKind =
  | "invalid_credentials"
  | "email_not_confirmed"
  | "rate_limited"
  | "weak_password"
  | "same_password"
  | "network"
  | "unknown";

export class AuthFailure extends Error {
  readonly kind: AuthFailureKind;

  constructor(kind: AuthFailureKind) {
    super(kind);
    this.name = "AuthFailure";
    this.kind = kind;
  }
}

export interface AuthGateway {
  currentSession(): Promise<AuthSession | null>;
  /** Returns an unsubscribe function. */
  onChange(listener: (event: AuthEvent, session: AuthSession | null) => void): () => void;
  /** A fresh access token for API calls, or null when logged out. */
  accessToken(): Promise<string | null>;
  signIn(email: string, password: string): Promise<void>;
  signUp(email: string, password: string): Promise<void>;
  resendVerification(email: string): Promise<void>;
  requestPasswordReset(email: string): Promise<void>;
  updatePassword(password: string): Promise<void>;
  /** "local" ends this device's session; "global" ends every session. */
  signOut(scope: "local" | "global"): Promise<void>;
}
