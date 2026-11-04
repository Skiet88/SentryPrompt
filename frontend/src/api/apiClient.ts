/**
 * Talks to the SentryPrompt backend. Adds the login token to each request,
 * never sends cookies, refuses redirects, and turns every failure into an
 * ApiError with a message that is safe to show.
 */

export interface TokenSource {
  accessToken(): Promise<string | null>;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryAfterSeconds: number | null;

  constructor(status: number, code: string, message: string, retryAfterSeconds: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

type Fetch = (input: string, init: RequestInit) => Promise<Response>;

export const NETWORK_MESSAGE = "We can't reach SentryPrompt right now. Check your connection and try again.";
export const SERVER_MESSAGE = "Something went wrong on our side. Please try again in a moment.";

export class ApiClient {
  private readonly baseUrl: string;
  private readonly tokens: TokenSource;
  private readonly onUnauthorized: () => void;
  private readonly fetchFn: Fetch;

  constructor(baseUrl: string, tokens: TokenSource, onUnauthorized: () => void, fetchFn?: Fetch) {
    this.baseUrl = baseUrl;
    this.tokens = tokens;
    this.onUnauthorized = onUnauthorized;
    this.fetchFn = fetchFn ?? ((input, init) => fetch(input, init));
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>("PUT", path, body);
  }

  delete<T = void>(path: string): Promise<T> {
    return this.request<T>("DELETE", path);
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    if (!path.startsWith("/api/")) throw new Error("API paths must start with /api/");
    const token = await this.tokens.accessToken();
    if (!token) {
      this.onUnauthorized();
      throw new ApiError(401, "unauthenticated", "Please log in again.");
    }

    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    if (body !== undefined) headers["Content-Type"] = "application/json";

    let response: Response;
    try {
      response = await this.fetchFn(`${this.baseUrl}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        credentials: "omit",
        redirect: "error",
        cache: "no-store",
      });
    } catch {
      throw new ApiError(0, "network", NETWORK_MESSAGE);
    }

    if (response.status === 204) return undefined as T;
    const data: unknown = await response.json().catch(() => null);
    if (response.ok) return data as T;

    if (response.status === 401) this.onUnauthorized();
    throw errorFrom(response, data);
  }
}

function errorFrom(response: Response, data: unknown): ApiError {
  const body = (typeof data === "object" && data !== null ? data : {}) as { error?: unknown; message?: unknown };
  const code = typeof body.error === "string" ? body.error : "error";
  if (response.status === 429) {
    const seconds = Number.parseInt(response.headers.get("Retry-After") ?? "", 10);
    const wait = Number.isFinite(seconds) && seconds > 0 ? seconds : null;
    const when = wait ? `in ${wait} seconds` : "in a moment";
    return new ApiError(429, code, `You're going a bit fast. Please try again ${when}.`, wait);
  }
  // 4xx messages from our backend are written for users; 5xx details stay on the server.
  const message =
    response.status < 500 && typeof body.message === "string" && body.message ? body.message : SERVER_MESSAGE;
  return new ApiError(response.status, code, message);
}
