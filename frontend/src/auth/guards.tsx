import { Navigate, Outlet, useLocation } from "react-router";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FullPageSpinner } from "@/components/ui/spinner";

import { useAuth } from "./authState";

/** Pages behind this need a login; everyone else is sent to the login page. */
export function RequireAuth() {
  const { state, reload, signOut } = useAuth();
  const location = useLocation();
  if (state.status === "loading") return <FullPageSpinner />;
  if (state.status === "signed_out") return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (state.status === "unavailable") {
    return (
      <div className="flex h-full items-center justify-center p-5">
        <div className="w-full max-w-sm space-y-4">
          <Alert tone="error">{state.message}</Alert>
          <div className="flex gap-2">
            <Button onClick={reload}>Try again</Button>
            <Button variant="ghost" onClick={() => void signOut()}>
              Log out
            </Button>
          </div>
        </div>
      </div>
    );
  }
  return <Outlet />;
}

/** Login and sign-up pages: someone already logged in goes straight to the app. */
export function PublicOnly() {
  const { state } = useAuth();
  if (state.status === "loading") return <FullPageSpinner />;
  if (state.status === "signed_in") return <Navigate to="/" replace />;
  return <Outlet />;
}

/** Only internal paths are followed after login (no open redirects). */
export function safeReturnPath(value: unknown): string {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return "/";
  }
  return value;
}
