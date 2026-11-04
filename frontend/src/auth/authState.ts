import { createContext, useContext } from "react";

import type { Profile } from "@/api/types";

export type AuthState =
  | { status: "loading" }
  /** notice: a message for the login page, e.g. after deleting the account. */
  | { status: "signed_out"; notice?: string }
  | { status: "signed_in"; profile: Profile }
  | { status: "unavailable"; message: string };

export interface AuthContextValue {
  state: AuthState;
  signOut(notice?: string): Promise<void>;
  reload(): void;
  /** Shows a profile the backend just returned (e.g. after changing the name). */
  setProfile(profile: Profile): void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}

/** The signed-in profile; only use inside pages protected by RequireAuth. */
export function useProfile(): Profile {
  const { state } = useAuth();
  if (state.status !== "signed_in") throw new Error("useProfile used outside a signed-in page");
  return state.profile;
}
