import { describe, expect, it, vi } from "vitest";

import { ApiClient, ApiError, NETWORK_MESSAGE, SERVER_MESSAGE } from "./apiClient";

function client(response: Response | Error, token: string | null = "tok") {
  const fetchFn = vi.fn(async () => {
    if (response instanceof Error) throw response;
    return response;
  });
  const onUnauthorized = vi.fn();
  const api = new ApiClient("http://api.test", { accessToken: async () => token }, onUnauthorized, fetchFn);
  return { api, fetchFn, onUnauthorized };
}

const json = (status: number, body: unknown, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });

async function failure(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
  }
  throw new Error("expected an ApiError");
}

describe("ApiClient", () => {
  it("sends the token as a bearer header, without cookies or redirects", async () => {
    const { api, fetchFn } = client(json(200, { ok: true }));
    await expect(api.post("/api/x", { a: 1 })).resolves.toEqual({ ok: true });
    expect(fetchFn).toHaveBeenCalledWith("http://api.test/api/x", {
      method: "POST",
      headers: { Authorization: "Bearer tok", "Content-Type": "application/json" },
      body: '{"a":1}',
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
    });
  });

  it("does not call the server when logged out", async () => {
    const { api, fetchFn, onUnauthorized } = client(json(200, {}), null);
    expect((await failure(api.get("/api/x"))).status).toBe(401);
    expect(fetchFn).not.toHaveBeenCalled();
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("only allows paths on our API", async () => {
    const { api } = client(json(200, {}));
    await expect(api.get("https://evil.example/steal")).rejects.toThrow(/\/api\//);
  });

  it("ends the login on 401", async () => {
    const { api, onUnauthorized } = client(json(401, { error: "unauthenticated", message: "Log in." }));
    expect((await failure(api.get("/api/x"))).code).toBe("unauthenticated");
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("shows the backend's message for 4xx", async () => {
    const { api } = client(json(403, { error: "account_suspended", message: "This account is suspended." }));
    const error = await failure(api.get("/api/x"));
    expect([error.status, error.code, error.message]).toEqual([403, "account_suspended", "This account is suspended."]);
  });

  it("never shows server error details", async () => {
    const { api } = client(json(500, { error: "internal_error", message: "Traceback: secret stuff" }));
    expect((await failure(api.get("/api/x"))).message).toBe(SERVER_MESSAGE);
  });

  it("explains rate limits with the wait time", async () => {
    const { api } = client(json(429, { error: "rate_limited", message: "x" }, { "Retry-After": "12" }));
    const error = await failure(api.get("/api/x"));
    expect(error.retryAfterSeconds).toBe(12);
    expect(error.message).toMatch(/12 seconds/);
  });

  it("turns network failures into a friendly message", async () => {
    const { api } = client(new TypeError("Failed to fetch"));
    const error = await failure(api.get("/api/x"));
    expect([error.status, error.message]).toEqual([0, NETWORK_MESSAGE]);
  });

  it("handles 204 and unreadable bodies", async () => {
    await expect(client(new Response(null, { status: 204 })).api.delete("/api/x")).resolves.toBeUndefined();
    const error = await failure(client(new Response("<html>", { status: 502 })).api.get("/api/x"));
    expect(error.message).toBe(SERVER_MESSAGE);
  });
});
