import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { ApiError } from "@/api/apiClient";
import { useServices } from "@/app/services";

import { AuthContext, type AuthContextValue, type AuthState } from "./authState";

/**
 * Keeps track of who is logged in. Role and status always come from our
 * backend (GET /api/profile), never from the login token or the browser.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const { auth, profile } = useServices();
  const [state, setState] = useState<AuthState>({ status: "loading" });
  const loadedUser = useRef<string | null>(null);

  const loadProfile = useCallback(
    async (userId: string) => {
      loadedUser.current = userId;
      try {
        const loaded = await profile.get();
        if (loadedUser.current === userId) setState({ status: "signed_in", profile: loaded });
      } catch (error) {
        if (loadedUser.current !== userId) return;
        if (error instanceof ApiError && error.status === 401) {
          loadedUser.current = null;
          setState({ status: "signed_out" });
          return;
        }
        const message = error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
        setState({ status: "unavailable", message });
      }
    },
    [profile],
  );

  const start = useCallback(
    () =>
      auth
        .currentSession()
        .catch(() => null)
        .then((session) => {
          if (session) return loadProfile(session.userId);
          setState({ status: "signed_out" });
        }),
    [auth, loadProfile],
  );

  useEffect(() => {
    void start();
    return auth.onChange((event, session) => {
      if (event === "signed_out" || !session) {
        loadedUser.current = null;
        setState({ status: "signed_out" });
      } else if (event === "signed_in" && loadedUser.current !== session.userId) {
        setState({ status: "loading" });
        // Run outside the provider's callback (Supabase advises against awaiting inside it).
        setTimeout(() => void loadProfile(session.userId), 0);
      }
    });
  }, [auth, loadProfile, start]);

  const value = useMemo<AuthContextValue>(
    () => ({
      state,
      reload: () => {
        setState({ status: "loading" });
        void start();
      },
      signOut: async () => {
        loadedUser.current = null;
        await auth.signOut("local").catch(() => undefined);
        setState({ status: "signed_out" });
      },
    }),
    [auth, start, state],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
