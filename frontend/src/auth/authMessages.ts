import type { AuthFailureKind } from "./authGateway";

/** Plain-language messages. Login errors never say whether an email has an account. */
export const AUTH_MESSAGES: Record<AuthFailureKind, string> = {
  invalid_credentials: "Incorrect email or password.",
  email_not_confirmed: "Please verify your email first. We sent you a link when you signed up.",
  rate_limited: "Too many attempts. Please wait a minute and try again.",
  weak_password: "Please choose a stronger password (at least 8 characters, mixing letters and numbers).",
  same_password: "Your new password must be different from your old one.",
  network: "We can't reach the login service. Check your connection and try again.",
  unknown: "Something went wrong. Please try again.",
};

export const MIN_PASSWORD_LENGTH = 8;

/** Fixed messages for errors in email links, chosen by code only, so text in a link is never shown. */
export function linkErrorMessage(code: string | null): string {
  if (code === "otp_expired") return "This link has expired. Request a new one below.";
  return "This link is no longer valid. It may have been used already, or opened in a different browser.";
}
