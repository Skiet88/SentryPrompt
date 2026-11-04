import { AuthApiError, AuthRetryableFetchError } from "@supabase/supabase-js";
import { describe, expect, it } from "vitest";

import { failureKind } from "./supabaseAuthGateway";

describe("failureKind", () => {
  it.each([
    ["invalid_credentials", 400, "invalid_credentials"],
    ["email_not_confirmed", 400, "email_not_confirmed"],
    ["over_email_send_rate_limit", 429, "rate_limited"],
    ["weak_password", 422, "weak_password"],
    ["same_password", 422, "same_password"],
    ["something_new", 429, "rate_limited"],
    ["something_new", 500, "unknown"],
  ])("maps %s (%i) to %s", (code, status, kind) => {
    expect(failureKind(new AuthApiError("server text", status, code))).toBe(kind);
  });

  it("treats fetch failures as network problems", () => {
    expect(failureKind(new AuthRetryableFetchError("down", 0))).toBe("network");
  });

  it("treats anything else as unknown", () => {
    expect(failureKind(new Error("x"))).toBe("unknown");
  });
});
