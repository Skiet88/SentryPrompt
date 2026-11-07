import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { useServices } from "@/app/services";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES } from "@/auth/authMessages";
import { emailError } from "@/auth/validation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { AuthLayout } from "@/layout/AuthLayout";

export function ForgotPasswordPage() {
  const { auth } = useServices();
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState<string>();
  const [error, setError] = useState<string>();
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const problem = emailError(email);
    setFieldError(problem);
    setError(undefined);
    if (problem) return;
    setBusy(true);
    try {
      await auth.requestPasswordReset(email.trim());
      setSent(true);
    } catch (failure) {
      setError(AUTH_MESSAGES[failure instanceof AuthFailure ? failure.kind : "unknown"]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Reset your password" subtitle="We'll email you a link to choose a new one.">
      {sent ? (
        <div className="space-y-5">
          {/* Same message whether or not the email has an account. */}
          <Alert tone="success">
            If an account uses {email.trim()}, a reset link is on its way. Open it in this browser within an hour.
          </Alert>
          <Button asChild variant="secondary">
            <Link to="/login">Back to log in</Link>
          </Button>
        </div>
      ) : (
        <form onSubmit={submit} noValidate className="space-y-4">
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
          <Button type="submit" size="lg" className="w-full" disabled={busy}>
            {busy ? "Sending…" : "Send reset link"}
          </Button>
          <p className="text-center text-sm">
            <Link to="/login" className="text-primary hover:underline">
              Back to log in
            </Link>
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
