# AUTH_DESIGN.md — SentryPrompt4

**Increment:** 4B — Auth & Account Module Design
**Traces to:** FR-013–FR-018, FR-021, FR-022, NFR-011, NFR-012, NFR-013, NFR-014 (../requirements/REQUIREMENTS.md); `User`, `Session`, `EmailVerificationToken`, `PasswordResetToken` (DOMAIN_MODEL.md §5)

This document specifies the concrete flows behind the Auth Service container already present in ARCHITECTURE.md and the entities already defined in DOMAIN_MODEL.md. It does not introduce new scope — every decision below resolves an ambiguity that was already implied but not yet pinned down (e.g. DOMAIN_MODEL.md defines `EmailVerificationToken.expiresAt` as an attribute, but no document yet states what that expiry window actually is).

---


## 1. Concrete Parameters (previously undefined attributes, now fixed)

| Parameter | Value | Rationale |
|---|---|---|
| Email verification token lifetime | 24 hours | Long enough for a student to check email once, short enough to limit exposure if the email is somehow intercepted. |
| Password reset token lifetime | 1 hour | Shorter than verification — reset tokens grant password-change power, a higher-value target if leaked. |
| Session lifetime | 12 hours idle timeout, 7 days absolute maximum | Idle timeout limits exposure on a shared/lost device; absolute cap forces periodic re-authentication regardless of activity. |
| Password hashing algorithm | bcrypt, cost factor 12 | Satisfies NFR-012; bcrypt chosen over Argon2 for this prototype for library maturity and simpler local setup — acceptable trade-off for a solo capstone, documented rather than silently picked. |
| Failed login lockout | No hard lockout; generic error only | A lockout mechanism is itself a denial-of-service vector on a single-user-scale prototype and is out of scope (Product Manager note above) — generic error messaging (below) is the accepted mitigation instead. |

---

## 2. Registration & Verification Flow (FR-013, FR-014)

```mermaid
sequenceDiagram
    participant S as Student (browser)
    participant API as Backend API
    participant Auth as Auth Service
    participant DB as Database
    participant Mail as Email Service

    S->>API: POST /register {email, password}
    API->>Auth: validate(email, password)
    Auth->>DB: check existing User by email
    alt email already registered
        DB-->>Auth: User exists
        Auth-->>API: generic error
        API-->>S: "If this email can be registered, check your inbox." (no enumeration leak)
    else email available
        DB-->>Auth: no match
        Auth->>Auth: hash password (bcrypt, cost 12)
        Auth->>DB: create User (emailVerified=false, status=active)
        Auth->>DB: create EmailVerificationToken (expiresAt = now+24h, used=false)
        Auth->>Mail: send verification link (token)
        Auth-->>API: registration accepted
        API-->>S: "Check your email to verify your account."
    end

    Note over S,Mail: Student clicks verification link
    S->>API: GET /verify?token=...
    API->>Auth: verify(token)
    Auth->>DB: lookup EmailVerificationToken by token
    alt token missing, expired, or used
        Auth-->>API: verification failed
        API-->>S: "This link is invalid or expired. Request a new one."
    else token valid and unused
        Auth->>DB: set User.emailVerified = true
        Auth->>DB: set EmailVerificationToken.used = true
        Auth-->>API: verified
        API-->>S: "Account verified — you can now submit prompts."
    end
```

**Design note:** the response to registration is worded identically whether or not the email was already registered, per the Security Architect's note above — this closes the same enumeration gap FR-015 already requires for login.

---

## 3. Login & Session Flow (FR-015, FR-016)

```mermaid
sequenceDiagram
    participant S as Student (browser)
    participant API as Backend API
    participant Auth as Auth Service
    participant DB as Database

    S->>API: POST /login {email, password}
    API->>Auth: authenticate(email, password)
    Auth->>DB: lookup User by email
    alt no match, or password hash mismatch
        Auth-->>API: generic error
        API-->>S: "Incorrect email or password." (identical message either way)
    else credentials valid
        Auth->>DB: create Session (expiresAt = now+12h idle / hard cap now+7d)
        Auth-->>API: session token
        API-->>S: session cookie/token set
    end

    Note over S,DB: On logout
    S->>API: POST /logout
    API->>Auth: invalidate(sessionId)
    Auth->>DB: Session.invalidate() — server-side deletion/flag, not client-only
    Auth-->>API: confirmed
    API-->>S: session cleared
```

**Design note (Backend Architect):** every authenticated request re-checks `Session.expiresAt` server-side against both the idle window and the absolute cap — a session is never trusted merely because a client still holds the token.

---

## 4. Password Reset Flow (FR-017)

```mermaid
sequenceDiagram
    participant S as Student (browser)
    participant API as Backend API
    participant Auth as Auth Service
    participant DB as Database
    participant Mail as Email Service

    S->>API: POST /reset-request {email}
    API->>Auth: requestReset(email)
    Auth->>DB: lookup User by email
    Auth->>DB: create PasswordResetToken (expiresAt = now+1h, used=false)
    Auth->>Mail: send reset link (token) — only if User exists
    Auth-->>API: accepted (generic response regardless)
    API-->>S: "If this email is registered, a reset link has been sent."

    Note over S,Mail: Student clicks reset link, submits new password
    S->>API: POST /reset-confirm {token, newPassword}
    API->>Auth: resetPassword(token, newPassword)
    Auth->>DB: lookup PasswordResetToken by token
    alt token missing, expired, or used
        Auth-->>API: reset failed
        API-->>S: "This link is invalid or expired. Request a new one."
    else token valid and unused
        Auth->>Auth: hash newPassword (bcrypt, cost 12)
        Auth->>DB: update User.passwordHash
        Auth->>DB: set PasswordResetToken.used = true
        Auth->>DB: invalidate all existing Sessions for this User
        Auth-->>API: reset confirmed
        API-->>S: "Password changed. Please log in again."
    end
```

**Design note (Database Architect):** invalidating all existing sessions on a successful password reset is a deliberate addition — if a reset was triggered because a password was compromised, an attacker's existing session should not survive the reset.

---

## 5. Account-Status Gate on Prompt Submission (FR-014 enforcement point)

Per the AI/ML Architect's note above, the unverified-account restriction is enforced at the same layer as authentication, not only in the UI:

```mermaid
flowchart TD
    A[Prompt submission request arrives at Backend API] --> B{Valid session?}
    B -- No --> C[401 — reject, redirect to login]
    B -- Yes --> D{User.emailVerified == true?}
    D -- No --> E[403 — "Verify your email before submitting prompts"]
    D -- Yes --> F{User.status == active?}
    F -- No, suspended --> G[403 — "Account suspended, contact admin"]
    F -- Yes --> H[Proceed to Screening Service]
```

This gate sits in front of the Screening Service entry point already documented in ARCHITECTURE.md's Component diagram — a direct API call cannot bypass it, since it is checked server-side before the request reaches the screening pipeline at all.

---

## 6. Admin-Panel Access Boundary (FR-021, NFR-013)

This is the module's most important non-negotiable rule, already stated in ../requirements/REQUIREMENTS.md and DOMAIN_MODEL.md — restated here as an enforceable design rule, not just a policy statement:

- Every admin-panel endpoint checks `User.role == 'admin'` server-side (never a client-side-only check).
- Admin endpoints operate exclusively on `User` fields (`status`, `emailVerified`) and `AdminAuditLog` — **no admin endpoint queries or returns `Conversation` or `Message` records, structurally.** This mirrors the DOMAIN_MODEL.md decision that `AdminAuditLog` never references `Message` content.
- Every admin action (suspend, reinstate) writes one `AdminAuditLog` entry before or atomically with the action itself — not as an afterthought log call that could silently fail and leave an unaudited action.

| Admin action | Reads/writes | Explicitly cannot touch |
|---|---|---|
| View user list | `User` (status, emailVerified, createdAt) | `Conversation`, `Message` |
| Suspend user | `User.status`, writes `AdminAuditLog` | `Conversation`, `Message` |
| Reinstate user | `User.status`, writes `AdminAuditLog` | `Conversation`, `Message` |
| View audit log | `AdminAuditLog` | `Conversation`, `Message` |

---

## 7. Summary Table — Requirement Coverage

| Requirement | Covered by |
|---|---|
| FR-013 (registration) | §2 |
| FR-014 (email verification) | §2, §5 |
| FR-015 (login) | §3 |
| FR-016 (logout) | §3 |
| FR-017 (password reset) | §4 |
| FR-021 (admin panel boundary) | §6 |
| FR-022 (audit log) | §6 |
| NFR-011 (encryption at rest) | Out of scope for this document — applies to `Message`, covered under Increment 5 (ERD/Data Pipeline) |
| NFR-012 (password hashing) | §1, §2, §4 |
| NFR-013 (admin no content access) | §6 |
| NFR-014 (right to erasure) | Not yet covered — account/conversation deletion flow (FR-020) is a separate flow, tracked for a follow-up addition to this document or Increment 5 |

**Known gap, not hidden:** FR-018 (profile view/edit/delete) and FR-020 (conversation/account deletion) are not diagrammed in this document — they're simpler CRUD-style flows without the token/session complexity of the flows above, and are deferred to keep this increment focused on the genuinely non-trivial auth mechanics. Tracked as a follow-up rather than silently dropped.

## Links
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [../requirements/PROJECT_BACKLOG.md](../requirements/../requirements/PROJECT_BACKLOG.md)
