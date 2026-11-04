import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";

import { useServices } from "@/app/services";
import { linkErrorMessage } from "@/auth/authMessages";
import { readEmailLink } from "@/auth/emailLink";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FullPageSpinner } from "@/components/ui/spinner";
import { AuthLayout } from "@/layout/AuthLayout";

/** Where the email-verification link lands. */
export function AuthCallbackPage() {
  const { auth, landingUrl } = useServices();
  const navigate = useNavigate();
  const [link] = useState(() => readEmailLink(landingUrl, "/auth/callback"));
  const [failed, setFailed] = useState(link.errorCode !== null);

  useEffect(() => {
    if (link.errorCode !== null) return;
    let active = true;
    auth
      .currentSession()
      .then((session) => {
        if (!active) return;
        if (session) void navigate("/", { replace: true });
        else setFailed(true);
      })
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, [auth, link, navigate]);

  if (!failed) return <FullPageSpinner />;
  return (
    <AuthLayout title="We couldn't verify that link">
      <div className="space-y-5">
        {/* Fixed text chosen by error code: text inside a link is never displayed. */}
        <Alert tone="error">{linkErrorMessage(link.errorCode)}</Alert>
        <p className="text-sm text-muted">
          If you already verified your email, just log in. Otherwise, log in and we'll tell you how to get a new link.
        </p>
        <Button asChild>
          <Link to="/login">Go to log in</Link>
        </Button>
      </div>
    </AuthLayout>
  );
}
