# SECURITY_RULES.md — standing security rules (apply to every change)

## 0. Ground rules
- Security over convenience. Never disable, weaken or bypass a security control
  (auth checks, RLS, validation, CSP/headers, TLS verification, rate limits)
  without my explicit consent. Flag any security trade-off before implementing it.
- For every change: identify the inputs, trust boundaries and who can call it;
  state the security impact in the summary.
- If you find or suspect a vulnerability, stop and report it before continuing.

## 1. Input and output
- Validate all input on the server (Pydantic schemas + factories): allow-lists,
  types, length limits. Never trust the frontend.
- Database access only through SQLAlchemy with bound parameters; never build SQL
  from strings. No eval/exec, no shell commands with user input.
- Rule-detector regexes must be checked for catastrophic backtracking (ReDoS).
- Frontend: rely on React escaping; never use dangerouslySetInnerHTML or render
  model/user content as HTML. Sanitize anything rendered as Markdown.

## 2. Authentication and authorization
- Deny by default: every endpoint requires a verified login unless explicitly
  marked public.
- Verify Supabase tokens fully: signature, expiry, issuer, audience, and that the
  session is still live.
- Role and status come only from our database, never from the request.
- Object-level checks on every resource (no IDOR/BOLA): a user can only reach
  their own conversations and messages; admins never reach message content.
- No mass assignment: request schemas list exactly the fields a client may set
  (never role, status, user_id, email_verified).

## 3. Data protection
- Secrets only in environment variables / host secret settings; never in code,
  Git, logs or chat. The Supabase service-role key exists only in the backend.
- Row Level Security on every table, checked by an automated test.
- Message content encrypted at rest (AES-GCM, NFR-011); evaluation logs
  content-free (NFR-009).
- Never log passwords, tokens, keys, prompt text or message content.

## 4. Web and API hardening
- CORS: explicit origin allow-list, never "*".
- Security headers: Content-Security-Policy, Strict-Transport-Security,
  X-Content-Type-Options, frame-ancestors 'none', Referrer-Policy.
- Rate limits on auth-related and screening endpoints (screening calls a paid/
  rate-limited LLM: abuse = denial of service and cost).
- Request body size limits. No fetching of user-supplied URLs (SSRF).
  Redirects only to allow-listed URLs.
- Swagger/OpenAPI docs disabled or protected in production.
- Errors: generic messages to clients, details only in server logs.

## 5. LLM-specific (OWASP LLM Top 10)
- Treat prompts as untrusted data; the system prompt must say so (prompt injection).
- Model output never triggers actions, queries or code; it is displayed as text only.
- Rule-detected values are redacted before any text reaches the LLM (NFR-008).
- Only no-training providers receive real student data (TrainingDataPolicy).

## 6. Dependencies
- Ask before adding any dependency; prefer maintained, widely used packages.
- Lock versions (uv.lock, package-lock.json); run pip-audit / npm audit before
  each commit and report findings.

## 7. Testing and review
- Every feature includes security tests: unauthenticated, wrong user (IDOR),
  forged/expired/logged-out token, suspended user, injection payloads (XSS, SQL),
  oversized input.
- Before each commit, run the checklist above against the change and report the
  result. Keep the API documented so it can be tested manually (e.g. Burp Suite).
