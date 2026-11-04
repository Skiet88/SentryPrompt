# SERVICE_LAYER.md — SentryPrompt4

**Traces to:** REPOSITORY_DESIGN.md, ../requirements/REQUIREMENTS.md (all FRs), ARCHITECTURE.md (FastAPI)
**Feeds:** Design Phase Template §3.2.3 (Interface Specifications), §8.4.2 (API Specification cross-reference), prototype evidence (§5)

---

## 1. Service Classes

| Service | Responsibility | Uses Repositories | Key business rules enforced |
|---|---|---|---|
| `AuthService` | Verifies Supabase access tokens on every request; loads the caller's profile; profile updates and account deletion through Supabase's admin API | `UserRepository` (profiles) | Blocks unverified accounts from screening endpoints (FR-014) and suspended accounts from everything; rejects tokens whose session has ended (FR-016). Registration, login and reset themselves are done by Supabase Auth (AUTH_DESIGN.md §0), which also handles duplicate emails (FR-013) and generic login errors (FR-015) |
| `ScreeningService` | Runs both detectors on every prompt (context-aware on redacted text), aggregates the result and explains every flag | `ScreeningResultRepository`, `FlaggedSpanRepository`, `EvaluationLogEntryRepository` | Enforces FR-004 (both detectors always run, never short-circuited); enforces NFR-009 (log entry is content-free, structurally, not by convention — see below) |
| `ConversationService` | Persists approved messages, retrieves history, handles deletion | `ConversationRepository`, `MessageRepository` | A `Message` can only be created from a `Prompt` that has already passed through `ScreeningService` — enforced by requiring a `ScreeningResult` reference as a precondition, not just a code comment |
| `AdminService` | Account management, audit logging | `UserRepository`, `AdminAuditLogRepository` | **Structurally has no dependency on `MessageRepository` or `ConversationRepository` at all** — not just "won't call it," the class doesn't have access to it, enforcing NFR-013 at the dependency-injection level |

**Board note on `AdminService`:** this is the same enforcement pattern used for encryption in Increment 6 — a boundary that matters (admins never see message content) is made structurally impossible to violate by omitting the dependency entirely, rather than relying on a developer remembering not to call a method that exists. This is a deliberate, repeated design pattern across the codebase, not a one-off.

### `ScreeningService` (implemented: `backend/app/service/screening/screening_service.py`)

The service is a Facade: one call, `screen(raw_text, channel)`, runs the whole pipeline.

1. `build_prompt()` validates the text (not empty, at most 4,000 characters, FR-001).
2. The rule-based detector runs on the original text (local, always completes).
3. Everything it found is redacted (`redact_with_map`, NFR-008).
4. The context-aware detector runs on the **redacted** text, with a time limit; a timeout, provider error or unreadable reply gives `UNAVAILABLE` (fail closed, NFR-015).
5. `build_screening_result()` records both verdicts separately and computes the aggregate (FR-004).
6. Every span is mapped back to the student's original text (context-aware spans were found in the redacted text) and explained in plain language (FR-005, FR-006).
7. The result, its flagged spans and a content-free evaluation log entry are saved together through `ScreeningRecordWriter` (one transaction, REPOSITORY_DESIGN.md §3B). A storage failure is logged and never blocks the student's screening.

It depends only on interfaces (`Detector`, a category catalog, the explanation generator), injected by the composition root (`backend/app/config/composition.py`). It returns a `ScreeningOutcome` holding the `ScreeningResult`, the explained `FlaggedSpan`s and, when the context check could not complete, a notice for the student. The outcome contains no prompt text.

**Revision note:** an earlier design ran both detectors concurrently on the raw prompt text. That would send rule-detected values (ID numbers, card numbers) to the external LLM, contradicting NFR-008, so the context-aware detector now waits for redaction. Persistence (step 5) stores only positions, verdicts and categories, never prompt text (NFR-009).

---

## 2. REST API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| — | *Supabase Auth* | Register, verify email, log in, log out, reset password (FR-013–FR-017). Called from the frontend with `supabase-js`; not backend endpoints (AUTH_DESIGN.md §0) | — |
| GET | `/api/profile` | View own profile (FR-018) | Yes (also while suspended) |
| PUT | `/api/profile` | Edit own display name (FR-018); nothing else can be set | Yes, verified and active |
| DELETE | `/api/profile` | Delete own account + all data (FR-020, NFR-014) | Yes (also while suspended or unverified) |
| POST | `/api/prompts/screen` | Submit a prompt for screening (FR-001–FR-006); rate-limited per user and globally | Yes, verified and active |
| GET | `/api/conversations` | List own conversation history (FR-019) | Yes |
| GET | `/api/conversations/{id}` | View a specific conversation's messages | Yes, owner only |
| DELETE | `/api/conversations/{id}` | Delete a conversation (FR-020) | Yes, owner only |
| GET | `/api/admin/users` | List all accounts (FR-021) | Yes, admin role |
| POST | `/api/admin/users/{id}/suspend` | Suspend an account | Yes, admin role |
| POST | `/api/admin/users/{id}/reinstate` | Reinstate a suspended account | Yes, admin role |
| GET | `/api/admin/audit-log` | View admin action history (FR-022) | Yes, admin role |

**Deliberate omission, stated not hidden:** there is no `GET /api/admin/conversations/{userId}` endpoint — this is intentional, not an oversight, per NFR-013.

---

## 3. Example Request/Response Schema

### `POST /api/prompts/screen` (implemented: `backend/app/api/screening_router.py`)

**Request** (unknown fields are rejected, so a client can never set `userId`, `role` or similar):
```json
{
  "text": "My student number is 8402215, can you help me write a cover letter?",
  "channel": "webapp"
}
```
`text`: 1–4,000 characters (FR-001). `channel`: `webapp` (default) or `extension`.

**Response (flagged):**
```json
{
  "screeningResultId": "5f0c…",
  "aggregatedVerdict": "FLAG",
  "ruleBasedVerdict": "FLAG",
  "contextAwareVerdict": "NO_FLAG",
  "requiresDecision": true,
  "notice": null,
  "flags": [
    {
      "category": "STUDENT_NUMBER",
      "startIndex": 21,
      "endIndex": 28,
      "detectorSource": "rule",
      "explanation": "This looks like a student number. Your student number identifies you at your university, so it counts as personal information."
    }
  ]
}
```

**Response (context-aware check unavailable, fail closed, NFR-015):** `aggregatedVerdict` is `UNAVAILABLE` (unless a rule flagged something), `requiresDecision` is `true`, and `notice` is *"We couldn't fully check your prompt for sensitive information right now. Review it before sending."*

**Response (clean):** `aggregatedVerdict` `NO_FLAG`, `requiresDecision` `false`, `flags` empty.

**Design changes from the original draft:**
- Flags return **positions** (`startIndex`, `endIndex`) instead of the flagged text. The client already has the prompt and highlights it by position (FR-005); not repeating sensitive values in responses keeps them out of browser tools and proxy logs (data minimisation).
- Both detectors' verdicts are returned, along with `requiresDecision` and `notice`, so the UI can show the edit / send anyway / cancel choice for flagged *and* unchecked prompts (FR-007, NFR-015).

### Error Responses

| Status | Condition | Body |
|---|---|---|
| 400 | Prompt is only whitespace (FR-001) | `{"error": "invalid_argument", "message": "Prompt text cannot be empty"}` |
| 401 | No token, or a forged, expired or logged-out token. Includes `WWW-Authenticate: Bearer` | `{"error": "unauthenticated", "message": "Please log in."}` |
| 403 | Logged in but not allowed: `email_not_verified`, `account_suspended` or `admin_only` | `{"error": "account_suspended", "message": "..."}` |
| 503 | The login could not be checked (Supabase unreachable). **Fails closed:** the request is refused, never let through | `{"error": "auth_unavailable", ...}` |
| 413 | Request body over `MAX_REQUEST_BYTES` (64 KB) | `{"error": "payload_too_large", ...}` |
| 422 | Missing/invalid fields, unknown fields, text over 4,000 characters, malformed JSON. **The submitted values are never echoed back** | `{"error": "invalid_request", "message": "The request is not valid.", "details": [{"field": "text", "problem": "..."}]}` |
| 429 | Rate limit reached: 10 requests per minute per client, 25 per minute in total (protects the LLM quota). Includes a `Retry-After` header | `{"error": "rate_limited", "message": "Too many requests. Please wait a moment and try again."}` |
| 500 / 502 | Server or configuration error (e.g. missing LLM key) | Generic message only; details in the server log |

**Rate limiting** is in memory (`backend/app/config/rate_limiter.py`), so limits apply per server process; running several processes would need a shared store behind the same `RateLimiter` interface. Until login exists, clients are identified by their network address (never by a client-supplied forwarded-for header, which is trivially spoofed); step 6 limits per user.

---

## 4. OpenAPI/Swagger

FastAPI generates the OpenAPI schema automatically from the route definitions and Pydantic models above — this is one of the reasons FastAPI was chosen in ARCHITECTURE.md's Tech Stack Decision. At build time, `/docs` will serve the interactive Swagger UI directly from this same endpoint table; no separate YAML file needs to be hand-maintained, which keeps the documentation from drifting out of sync with the actual code — an explicit answer to the Maintainability NFR category (NFR-005, NFR-006).

## Links
- [REPOSITORY_DESIGN.md](REPOSITORY_DESIGN.md)
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
