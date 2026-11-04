import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { useServices } from "@/app/services";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES, linkErrorMessage } from "@/auth/authMessages";
import { readEmailLink } from "@/auth/emailLink";
import { newPasswordError } from "@/auth/validation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { PasswordInput } from "@/components/ui/password-input";
import { FullPageSpinner } from "@/components/ui/spinner";
import { AuthLayout } from "@/layout/AuthLayout";

type Stage = "checking" | "ready" | "invalid";

/**
 * Where the password-reset link lands. The form only appears when the page
 * was opened from a valid reset link; afterwards every session is ended, so
 * anyone who knew the old password is logged out too (AUTH_DESIGN.md §4).
 */
export function ResetPasswordPage() {
  const { auth, landingUrl } = useServices();
  const navigate = useNavigate();
  const [link] = useState(() => readEmailLink(landingUrl, "/reset-password"));
  const [stage, setStage] = useState<Stage>(link.hasCode && !link.errorCode ? "checking" : "invalid");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string>();
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (stage !== "checking") return;
    let active = true;
    auth
      .currentSession()
      .then((session) => active && setStage(session ? "ready" : "invalid"))
      .catch(() => active && setStage("invalid"));
    return () => {
      active = false;
    };
  }, [auth, stage]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const problem = newPasswordError(password);
    setFieldError(problem);
    setError(undefined);
    if (problem) return;
    setBusy(true);
    try {
      await auth.updatePassword(password);
      await auth.signOut("global").catch(() => undefined);
      void navigate("/login", { replace: true, state: { notice: "Password changed. Please log in with your new password." } });
    } catch (failure) {
      setError(AUTH_MESSAGES[failure instanceof AuthFailure ? failure.kind : "unknown"]);
      setBusy(false);
    }
  }

  if (stage === "checking") return <FullPageSpinner />;
  if (stage === "invalid") {
    return (
      <AuthLayout title="This reset link doesn't work">
        <div className="space-y-5">
          <Alert tone="error">{linkErrorMessage(link.errorCode)}</Alert>
          <Button asChild>
            <Link to="/forgot-password">Request a new link</Link>
          </Button>
        </div>
      </AuthLayout>
    );
  }
  return (
    <AuthLayout title="Choose a new password">
      <form onSubmit={submit} noValidate className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <FormField label="New password" hint="At least 8 characters, with letters and numbers." error={fieldError}>
          <PasswordInput autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus />
        </FormField>
        <Button type="submit" size="lg" className="w-full" disabled={busy}>
          {busy ? "Saving…" : "Save new password"}
        </Button>
      </form>
    </AuthLayout>
  );
}
