import { describe, expect, it } from "vitest";

import { safeReturnPath } from "./guards";
import { readEmailLink } from "./emailLink";
import { emailError, newPasswordError } from "./validation";

describe("safeReturnPath (no open redirects)", () => {
  it.each(["/", "/c/123", "/settings"])("keeps internal path %s", (path) => {
    expect(safeReturnPath(path)).toBe(path);
  });

  it.each(["https://evil.example", "//evil.example", "/\\evil.example", "javascript:alert(1)", 42, null])(
    "replaces %s with home",
    (value) => {
      expect(safeReturnPath(value)).toBe("/");
    },
  );
});

describe("readEmailLink", () => {
  it("finds the code only on the expected page", () => {
    expect(readEmailLink(new URL("http://x/reset-password?code=abc"), "/reset-password")).toEqual({
      hasCode: true,
      errorCode: null,
    });
    expect(readEmailLink(new URL("http://x/?code=abc"), "/reset-password").hasCode).toBe(false);
  });

  it("reads error codes from the query or the hash", () => {
    expect(readEmailLink(new URL("http://x/auth/callback?error_code=otp_expired"), "/auth/callback").errorCode).toBe(
      "otp_expired",
    );
    expect(readEmailLink(new URL("http://x/auth/callback#error=access_denied"), "/auth/callback").errorCode).toBe(
      "access_denied",
    );
  });
});

describe("validation", () => {
  it.each(["", "   ", "nope", "a@b", `${"a".repeat(250)}@uni.ac.za`])("rejects email %j", (email) => {
    expect(emailError(email)).toBeDefined();
  });

  it("accepts a normal email", () => {
    expect(emailError(" thabo@uni.ac.za ")).toBeUndefined();
  });

  it.each(["short1", "lettersonly", "12345678", "a1".repeat(40)])("rejects password %j", (password) => {
    expect(newPasswordError(password)).toBeDefined();
  });

  it("accepts a reasonable password", () => {
    expect(newPasswordError("campus2026")).toBeUndefined();
  });
});
