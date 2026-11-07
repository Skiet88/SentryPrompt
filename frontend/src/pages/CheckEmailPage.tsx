import { MailCheck } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router";

import { useServices } from "@/app/services";
import { AuthFailure } from "@/auth/authGateway";
import { AUTH_MESSAGES } from "@/auth/authMessages";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AuthLayout } from "@/layout/AuthLayout";

export function CheckEmailPage() {
  const { auth } = useServices();
  const email = (useLocation().state as { email?: string } | null)?.email;
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string }>();
  const [busy, setBusy] = useState(false);

  async function resend() {
    if (!email) return;
    setBusy(true);
    try {
      await auth.resendVerification(email);
      setMessage({ tone: "success", text: "We sent the link again." });
    } catch (failure) {
      setMessage({ tone: "error", text: AUTH_MESSAGES[failure instanceof AuthFailure ? failure.kind : "unknown"] });
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Check your email">
      <div className="space-y-5">
        <span className="flex size-12 items-center justify-center rounded-xl bg-primary-soft text-primary">
          <MailCheck className="size-6" aria-hidden />
        </span>
        <p className="text-muted">
          We sent a link to {email ? <strong className="text-foreground">{email}</strong> : "your email address"}.
          Open it <strong className="text-foreground">in this browser</strong> to verify your account, then you can
          start chatting.
        </p>
        <p className="text-sm text-muted">Not there? Check your spam folder.</p>
        {message && <Alert tone={message.tone}>{message.text}</Alert>}
        <div className="flex flex-wrap gap-2">
          {email && (
            <Button variant="secondary" onClick={() => void resend()} disabled={busy}>
              {busy ? "Sending…" : "Send the link again"}
            </Button>
          )}
          <Button asChild variant="ghost">
            <Link to="/login">Back to log in</Link>
          </Button>
        </div>
      </div>
    </AuthLayout>
  );
}
