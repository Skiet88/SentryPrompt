import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { useServices } from "@/app/services";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES } from "@/auth/authMessages";
import { emailError, newPasswordError } from "@/auth/validation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { AuthLayout } from "@/layout/AuthLayout";

export function RegisterPage() {
  const { auth } = useServices();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = { email: emailError(email), password: newPasswordError(password) };
    setErrors(found);
    setError(undefined);
    if (found.email || found.password) return;
    setBusy(true);
    try {
      await auth.signUp(email.trim(), password);
      // The same answer whether or not the email already has an account (no account discovery).
      void navigate("/check-email", { state: { email: email.trim() } });
    } catch (failure) {
      setError(AUTH_MESSAGES[failure instanceof AuthFailure ? failure.kind : "unknown"]);
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="It takes less than a minute.">
      <form onSubmit={submit} noValidate className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <FormField label="Email" hint="Use your student email if you have one." error={errors.email}>
          <Input
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
        </FormField>
        <FormField label="Password" hint="At least 8 characters, with letters and numbers." error={errors.password}>
          <PasswordInput autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </FormField>
        <Button type="submit" size="lg" className="w-full" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
