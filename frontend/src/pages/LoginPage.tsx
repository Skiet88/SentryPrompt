import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { useServices } from "@/app/services";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES } from "@/auth/authMessages";
import { useAuth } from "@/auth/authState";
import { safeReturnPath } from "@/auth/guards";
import { emailError } from "@/auth/validation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { AuthLayout } from "@/layout/AuthLayout";

export function LoginPage() {
  const { auth } = useServices();
  const navigate = useNavigate();
  const location = useLocation();
  const { state } = useAuth();
  const notice =
    (location.state as { notice?: string } | null)?.notice ?? (state.status === "signed_out" ? state.notice : undefined);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string>();
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const problem = emailError(email);
    setFieldError(problem);
    setError(undefined);
    if (problem || !password) {
      if (!problem) setError("Enter your password.");
      return;
    }
    setBusy(true);
    try {
      await auth.signIn(email.trim(), password);
      void navigate(safeReturnPath((location.state as { from?: unknown } | null)?.from), { replace: true });
    } catch (failure) {
      setError(AUTH_MESSAGES[failure instanceof AuthFailure ? failure.kind : "unknown"]);
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue to SentryPrompt.">
      <form onSubmit={submit} noValidate className="space-y-4">
        {notice && <Alert tone="success">{notice}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        <FormField label="Email" error={fieldError}>
          <Input
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
        </FormField>
        <FormField
          label="Password"
          action={
            <Link to="/forgot-password" className="text-sm text-primary hover:underline">
              Forgot password?
            </Link>
          }
        >
          <PasswordInput autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </FormField>
        <Button type="submit" size="lg" className="w-full" disabled={busy}>
          {busy ? "Logging in…" : "Log in"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        New to SentryPrompt?{" "}
        <Link to="/register" className="font-medium text-primary hover:underline">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  );
}
