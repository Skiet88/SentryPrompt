# SERVICE_LAYER.md — SentryPrompt4

**Traces to:** REPOSITORY_DESIGN.md, REQUIREMENTS.md (all FRs), ARCHITECTURE.md (FastAPI)
**Feeds:** Design Phase Template §3.2.3 (Interface Specifications), §8.4.2 (API Specification cross-reference), prototype evidence (§5)

---

## 1. Service Classes

| Service | Responsibility | Uses Repositories | Key business rules enforced |
|---|---|---|---|
| `AuthService` | Registration, verification, login/session, password reset | `UserRepository`, `SessionRepository`, `EmailVerificationTokenRepository`, `PasswordResetTokenRepository` | Rejects duplicate emails (FR-013); blocks unverified accounts from screening endpoints (FR-014); never reveals whether a failed login was a bad email or bad password (FR-015) |
| `ScreeningService` | Orchestrates rule-based + context-aware detection in parallel, aggregates result | `ScreeningResultRepository`, `FlaggedSpanRepository`, `EvaluationLogEntryRepository` | Enforces FR-004 (both detectors always run, never short-circuited); enforces NFR-009 (log entry is content-free, structurally, not by convention — see below) |
| `ConversationService` | Persists approved messages, retrieves history, handles deletion | `ConversationRepository`, `MessageRepository` | A `Message` can only be created from a `Prompt` that has already passed through `ScreeningService` — enforced by requiring a `ScreeningResult` reference as a precondition, not just a code comment |
| `AdminService` | Account management, audit logging | `UserRepository`, `AdminAuditLogRepository` | **Structurally has no dependency on `MessageRepository` or `ConversationRepository` at all** — not just "won't call it," the class doesn't have access to it, enforcing NFR-013 at the dependency-injection level |

**Board note on `AdminService`:** this is the same enforcement pattern used for encryption in Increment 6 — a boundary that matters (admins never see message content) is made structurally impossible to violate by omitting the dependency entirely, rather than relying on a developer remembering not to call a method that exists. This is a deliberate, repeated design pattern across the codebase, not a one-off.

### Example: `ScreeningService` (Python)

```python
class ScreeningService:
    def __init__(self, rule_detector, context_detector, result_repo, log_repo):
        self._rule_detector = rule_detector
        self._context_detector = context_detector
        self._result_repo = result_repo
        self._log_repo = log_repo

    async def screen_prompt(self, prompt: Prompt) -> ScreeningResult:
        if not prompt.rawText.strip():
            raise EmptyPromptError()  # FR-001

        # FR-004: run both detectors independently, in parallel — not a fallback chain
        rule_result, context_result = await asyncio.gather(
            self._rule_detector.detect(prompt.rawText),
            self._context_detector.detect(prompt.rawText),
        )

        result = ScreeningResult(
            promptId=prompt.promptId,
            ruleBasedVerdict=rule_result.verdict,
            contextAwareVerdict=context_result.verdict,
            aggregatedVerdict=rule_result.verdict or context_result.verdict,
        )
        self._result_repo.save(result)

        # NFR-009: log entry never receives prompt.rawText — the log method's signature
        # doesn't even accept it, so this isn't a runtime check, it's a compile-time one.
        self._log_repo.save(EvaluationLogEntry.from_result(result))  # no rawText parameter exists

        return result
```

---

## 2. REST API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/auth/register` | Create a new account (FR-013) | No |
| POST | `/api/auth/verify` | Verify email via token (FR-014) | No (token-based) |
| POST | `/api/auth/login` | Log in, returns session (FR-015) | No |
| POST | `/api/auth/logout` | Invalidate session (FR-016) | Yes |
| POST | `/api/auth/reset-password/request` | Request reset token (FR-017) | No |
| POST | `/api/auth/reset-password/confirm` | Set new password via token (FR-017) | No (token-based) |
| GET | `/api/profile` | View own profile (FR-018) | Yes |
| PUT | `/api/profile` | Edit own profile (FR-018) | Yes |
| DELETE | `/api/profile` | Delete own account + all data (FR-020) | Yes |
| POST | `/api/prompts/screen` | Submit a prompt for screening (FR-001–FR-008) | Yes, verified |
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

### `POST /api/prompts/screen`

**Request:**
```json
{
  "text": "My student number is 8402215, can you help me write a cover letter?"
}
```

**Response (flagged):**
```json
{
  "screeningResultId": "sr_a1b2c3",
  "aggregatedVerdict": "FLAG",
  "flags": [
    {
      "category": "ID_NUMBER",
      "span": "8402215",
      "detectorSource": "rule",
      "explanation": "This looks like a student or ID number, which could expose your identity if shared with a third-party AI platform."
    }
  ]
}
```

**Response (clean):**
```json
{
  "screeningResultId": "sr_d4e5f6",
  "aggregatedVerdict": "NO_FLAG",
  "flags": []
}
```

### Error Responses

| Status | Condition | Example |
|---|---|---|
| 400 | Empty prompt submitted (FR-001) | `{"error": "PROMPT_EMPTY", "message": "Prompt text cannot be empty."}` |
| 401 | Missing/invalid session | `{"error": "UNAUTHENTICATED", "message": "Please log in."}` |
| 403 | Verified-only or admin-only endpoint accessed without the right role/state | `{"error": "FORBIDDEN", "message": "Email verification required before screening prompts."}` |
| 404 | Conversation/user not found, or not owned by requester (same response for both, to avoid leaking existence — same principle as FR-015's login error handling) | `{"error": "NOT_FOUND"}` |
| 429 | *(future work, not required at this scope)* — noted here as a gap, not silently absent: no rate limiting is designed yet for `/api/prompts/screen`, which is a real risk against NFR-010's latency budget under repeated calls | — |

---

## 4. OpenAPI/Swagger

FastAPI generates the OpenAPI schema automatically from the route definitions and Pydantic models above — this is one of the reasons FastAPI was chosen in ARCHITECTURE.md's Tech Stack Decision. At build time, `/docs` will serve the interactive Swagger UI directly from this same endpoint table; no separate YAML file needs to be hand-maintained, which keeps the documentation from drifting out of sync with the actual code — an explicit answer to the Maintainability NFR category (NFR-005, NFR-006).

## Links
- [REPOSITORY_DESIGN.md](./REPOSITORY_DESIGN.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DOMAIN_MODEL.md](./DOMAIN_MODEL.md)
