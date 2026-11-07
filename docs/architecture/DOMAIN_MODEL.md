# DOMAIN_MODEL.md — SentryPrompt4

**Traceability:** Entities below are derived directly from ../requirements/REQUIREMENTS.md (FR-001–FR-012) and the architecture consistency findings in Increment 2A. Two design constraints from board review are non-negotiable in this model and are called out wherever they apply:
1. **No entity persists raw prompt text.** (NFR-009)
2. **The evaluation path (FR-012) is structurally independent from the live screening path.** (Increment 2A finding)

---

## 1. Domain Entities

| Entity | Attributes | Methods | Relationships |
|---|---|---|---|
| **Prompt** | `promptId`, `rawText` *(in-memory only — never persisted, see NFR-009)*, `sourceChannel` (webapp / extension), `submittedAt`, `status` | `validate()`, `submit()` | Produces one `ScreeningResult` |
| **ScreeningResult** | `resultId`, `promptId`, `ruleBasedVerdict`, `contextAwareVerdict`, `aggregatedVerdict`, `decidedAt` | `aggregate()`, `isFlagged()` | Belongs to one `Prompt`; has 0..* `FlaggedSpan`; produces 0..1 `EvaluationLogEntry` |
| **FlaggedSpan** | `spanId`, `resultId`, `startIndex`, `endIndex`, `detectorSource` (rule / context), `categoryId` | `getExplanation()` | Belongs to one `ScreeningResult`; references one `DetectionCategory` |
| **DetectionCategory** | `categoryId`, `name`, `description`, `tier` (rule-based / context-aware) | — | Has 0..* `RulePattern` (only for rule-based tier) |
| **RulePattern** | `patternId`, `categoryId`, `regexPattern`, `description` | `matches(text)` | Belongs to one `DetectionCategory` (supports NFR-005, UC10) |
| **EvaluationLogEntry** | `logId`, `resultId`, `categoryId` (nullable), `outcome` (flagged / unflagged / override / redacted / unavailable), `timestampBucket` | — | Content-free by design — belongs to one `ScreeningResult`, but **does not** reference `Prompt.rawText` at all (NFR-009 enforced structurally, not just by convention) |
| **TestSetEntry** *(evaluation path — deliberately unconnected to the four entities above)* | `entryId`, `sampleText`, `groundTruthCategory`, `groundTruthLabel` | `runThroughDetectors()` | Standalone — consumed directly by the evaluation harness (UC8), never touches `Prompt` or `ScreeningResult` |

**Business rules:**
- A `Prompt` never exists in a persisted table — only `ScreeningResult` and `EvaluationLogEntry` (metadata-only) survive past the request lifecycle.
- `FlaggedSpan.detectorSource` must record which detector produced each span individually — verdicts are never merged before this point (enforces FR-004's parallel-detection requirement at the data level, not just the process level).
- `TestSetEntry` has no foreign key into any live-path entity. This is intentional: it is what makes UC8 (Run Evaluation) genuinely independent of live usage, closing the gap Increment 2A identified in the architecture.

---

## 2. Class Diagram (Mermaid)

```mermaid
classDiagram
    class Prompt {
        -promptId: String
        -rawText: String
        -sourceChannel: String
        -submittedAt: DateTime
        -status: String
        +validate() bool
        +submit() ScreeningResult
    }

    class ScreeningResult {
        -resultId: String
        -promptId: String
        -ruleBasedVerdict: String
        -contextAwareVerdict: String
        -aggregatedVerdict: String
        -decidedAt: DateTime
        +aggregate() String
        +isFlagged() bool
    }

    class FlaggedSpan {
        -spanId: String
        -resultId: String
        -startIndex: int
        -endIndex: int
        -detectorSource: String
        -categoryId: String
        +getExplanation() String
    }

    class DetectionCategory {
        -categoryId: String
        -name: String
        -description: String
        -tier: String
    }

    class RulePattern {
        -patternId: String
        -categoryId: String
        -regexPattern: String
        -description: String
        +matches(text: String) bool
    }

    class EvaluationLogEntry {
        -logId: String
        -resultId: String
        -categoryId: String
        -outcome: String
        -timestampBucket: String
    }

    class TestSetEntry {
        -entryId: String
        -sampleText: String
        -groundTruthCategory: String
        -groundTruthLabel: String
        +runThroughDetectors() ScreeningResult
    }

    Prompt "1" --> "1" ScreeningResult : produces
    ScreeningResult "1" --> "0..*" FlaggedSpan : contains
    FlaggedSpan "0..*" --> "1" DetectionCategory : classified as
    DetectionCategory "1" --> "0..*" RulePattern : defined by
    ScreeningResult "1" --> "0..1" EvaluationLogEntry : summarized as
    TestSetEntry ..> ScreeningResult : produces (evaluation only, no persisted FK)

    note for TestSetEntry "Deliberately isolated: no foreign key\ninto Prompt or ScreeningResult tables.\nConsumed only by the offline evaluation\nharness (UC8), never by the live path."
    note for EvaluationLogEntry "Never references Prompt.rawText.\nContent-free by structural design, not\njust convention (NFR-009)."
```

---

## 3. Design Decisions (from board review, resolved)

| Concern raised | Resolution in this model |
|---|---|
| Software Architect: does `Prompt` persist raw text? | No — `rawText` is explicitly marked in-memory-only; only derived, content-free records persist. |
| Security Architect: transient vs. persisted boundary | Modeled as two separate entity families (`Prompt` = transient, `EvaluationLogEntry` = persisted metadata), not a flag on one entity. |
| Database Architect: no shared primary-key path | `EvaluationLogEntry` has no foreign key back to any field containing raw content — only `resultId`, `categoryId`, and bucketed metadata. |
| AI/ML Architect: evaluation-path independence | `TestSetEntry` has zero foreign keys into the live entities; connected only by a dependency arrow (`..>`) showing it *uses* the same detection logic, not the same data. |
| QA/Test Architect: per-detector verdict tracking | `FlaggedSpan.detectorSource` and `ScreeningResult`'s two separate verdict fields preserve which detector found what, supporting TC-004's precision/recall comparison. |
| Backend Architect: one repository per entity | Each of the 7 entities maps to exactly one planned repository interface in Increment 6 — none require splitting. |
| Product Manager: scope | 7 entities — at the upper bound of the 5–7 target for an individual project, justified by the transient/persisted split rather than padding. |

---

## 5. Scope Expansion: Full Platform (Account, Session, History, Admin)

**Board decision context:** the project scope was expanded from a single-user research prototype to a full account-based platform (registration, login, persistent conversation history, admin panel), per explicit instruction. This is additive to the original 7 research-domain entities, not a replacement — Assignment 4's brief permits Agile-driven scope updates as long as the project doesn't diverge from its Assignment 3 core, and this expansion keeps the screening research at the center.

**Resolved tension (must be understood before reading the entities below):** the original model enforced "no entity persists raw prompt text" (NFR-009) via the `EvaluationLogEntry` design. Persistent conversation history necessarily breaks that rule for a *different* entity (`Message`) — this is intentional and scoped: two data stores, two policies.
- `EvaluationLogEntry` (research artifact) → stays content-free, per NFR-009.
- `Message` (product feature) → legitimately stores content, but is now governed by NFR-011 (encryption at rest) and FR-020 (permanent deletion capability).

### New Entities

| Entity | Attributes | Methods | Relationships |
|---|---|---|---|
| **User** | `userId`, `email`, `passwordHash`, `displayName`, `role` (student / admin), `emailVerified`, `status` (active / suspended), `createdAt` | `register()`, `authenticate()`, `deleteAccount()` | Has 0..* `Session`; has 0..* `Conversation`; has 0..1 `EmailVerificationToken`; has 0..1 `PasswordResetToken` |
| **Session** | `sessionId`, `userId`, `token`, `createdAt`, `expiresAt` | `invalidate()` | Belongs to one `User` |
| **EmailVerificationToken** | `tokenId`, `userId`, `token`, `expiresAt`, `used` | `verify()` | Belongs to one `User` (FR-014) |
| **PasswordResetToken** | `tokenId`, `userId`, `token`, `expiresAt`, `used` | `resetPassword()` | Belongs to one `User` (FR-017) |
| **Conversation** | `conversationId`, `userId`, `title`, `channel` (webapp / extension), `createdAt`, `updatedAt` | `delete()` | Belongs to one `User`; has 1..* `Message` |
| **Message** | `messageId`, `conversationId`, `role` (user / assistant), `content` *(encrypted at rest — NFR-011)*, `createdAt` | — | Belongs to one `Conversation`; a user-role `Message` is created from an approved `Prompt` once screening clears it |
| **AdminAuditLog** | `logId`, `adminUserId`, `targetUserId`, `actionType`, `timestamp`, `details` | — | References `User` (admin) and `User` (target) — account-level only, never references `Message` content (FR-021, NFR-013) |

**Implementation note:** three of these entities (`Session`, `EmailVerificationToken`, `PasswordResetToken`) are managed by Supabase Auth rather than implemented in our code. See §6 for the full mapping from this model to the code.

### How the Product Layer Connects to the Research Layer

```
Prompt (transient, screened)
   │
   ├── if flagged & cancelled → discarded, never persisted, logged content-free in EvaluationLogEntry
   ├── if flagged & sent anyway → persisted as Message (encrypted), logged content-free in EvaluationLogEntry
   └── if clean → persisted as Message (encrypted), logged content-free in EvaluationLogEntry
```

This is the key design decision that keeps the expansion coherent rather than bolted-on: **every** message that ends up in a `Conversation` passed through the exact same screening pipeline already documented in ARCHITECTURE.md — there is no second, unscreened path into persisted chat history.

### Updated Class Diagram Addendum

```mermaid
classDiagram
    class User {
        -userId: String
        -email: String
        -passwordHash: String
        -displayName: String
        -role: String
        -emailVerified: bool
        -status: String
        -createdAt: DateTime
        +register() bool
        +authenticate(password: String) Session
        +deleteAccount() bool
    }

    class Session {
        -sessionId: String
        -userId: String
        -token: String
        -createdAt: DateTime
        -expiresAt: DateTime
        +invalidate() bool
    }

    class EmailVerificationToken {
        -tokenId: String
        -userId: String
        -token: String
        -expiresAt: DateTime
        -used: bool
        +verify() bool
    }

    class PasswordResetToken {
        -tokenId: String
        -userId: String
        -token: String
        -expiresAt: DateTime
        -used: bool
        +resetPassword(newPassword: String) bool
    }

    class Conversation {
        -conversationId: String
        -userId: String
        -title: String
        -channel: String
        -createdAt: DateTime
        -updatedAt: DateTime
        +delete() bool
    }

    class Message {
        -messageId: String
        -conversationId: String
        -role: String
        -content: String
        -createdAt: DateTime
    }

    class AdminAuditLog {
        -logId: String
        -adminUserId: String
        -targetUserId: String
        -actionType: String
        -timestamp: DateTime
        -details: String
    }

    User "1" --> "0..*" Session : has
    User "1" --> "0..1" EmailVerificationToken : has
    User "1" --> "0..1" PasswordResetToken : has
    User "1" --> "0..*" Conversation : owns
    Conversation "1" --> "1..*" Message : contains
    User "1" --> "0..*" AdminAuditLog : is target of
    User "1" --> "0..*" AdminAuditLog : performs (as admin)
    Message ..> Prompt : created from (post-screening only)

    note for Message "Encrypted at rest (NFR-011).\nEvery Message passed through the\nfull screening pipeline before creation\n— no unscreened path into history."
    note for AdminAuditLog "Account-level only.\nNever references Message content\n(NFR-013 — admin has no content access)."
```

**Total entity count: 14** (7 research-domain + 7 platform-domain), up from the originally scoped 7.

---

## 6. Implementation Mapping (model → code)

The 14 entities above are the logical model and remain the reference for the report. This section records how each one is implemented, so a reader can trace every entity to its code.

### 6.1 Where each entity lives

| # | Entity | Implemented by | Code |
|---|---|---|---|
| 1 | Prompt | Our code (in memory only, never persisted) | `backend/app/domain/prompt.py`, `factory/prompt_factory.py` |
| 2 | ScreeningResult | Our code | `domain/screening_result.py`, `factory/screening_result_factory.py` |
| 3 | FlaggedSpan | Our code | `domain/flagged_span.py`, `factory/flagged_span_factory.py` |
| 4 | DetectionCategory | Our code | `domain/detection_category.py`, `factory/detection_category_factory.py` |
| 5 | RulePattern | Our code | `domain/rule_pattern.py`, `factory/rule_pattern_factory.py` |
| 6 | EvaluationLogEntry | Our code | `domain/evaluation_log_entry.py`, `factory/evaluation_log_entry_factory.py` |
| 7 | TestSetEntry | Our code | `domain/test_set_entry.py`, `factory/test_set_entry_factory.py` |
| 8 | User | Our code (profile) + Supabase Auth (identity, password) | `domain/user.py`, `factory/user_factory.py` |
| 9 | Session | **Supabase Auth** | Supabase `auth` schema; checked by the backend on every request (AUTH_DESIGN.md §0) |
| 10 | EmailVerificationToken | **Supabase Auth** | Supabase `auth` schema |
| 11 | PasswordResetToken | **Supabase Auth** | Supabase `auth` schema |
| 12 | Conversation | Our code | `domain/conversation.py`, `factory/conversation_factory.py` |
| 13 | Message | Our code (content encrypted by the repository, NFR-011) | `domain/message.py`, `factory/message_factory.py` |
| 14 | AdminAuditLog | Our code | `domain/admin_audit_log.py`, `factory/admin_audit_log_factory.py` |

**11 entities are implemented in our code; 3 are handled by Supabase Auth.** All 11 are immutable (frozen dataclasses) and created only through their factory, which validates every field and raises a clear error naming the field.

### 6.2 Attribute differences

| Entity | Difference | Reason |
|---|---|---|
| User | No `passwordHash` | Passwords and hashes are held only by Supabase Auth; our code never sees them (NFR-012) |
| EvaluationLogEntry | `timestampBucket` is the UTC hour, e.g. `2026-11-03T14:00Z` | Coarse enough that a log entry cannot be matched to an individual request by exact time (NFR-009) |
| Prompt | `rawText` limited to 4,000 characters | FR-001's "defined max length"; well above a typical prompt (~200 words, NFR-010) |
| Message | A user-role `content` is the prompt **as sent to the AI**, with rule-detected values replaced by placeholders such as `[REDACTED_SA_ID]` | ID, card and account numbers and similar are never stored (NFR-008); content is encrypted at rest (NFR-011) |

Python naming is used in code (`prompt_id` for `promptId`, and so on); the attributes are otherwise as specified.

### 6.3 Allowed values for String attributes

Each String attribute that takes a fixed set of values is an enum in `backend/app/domain/enums.py`:

| Attribute | Values |
|---|---|
| `Prompt.sourceChannel`, `Conversation.channel` | webapp, extension |
| `Prompt.status` | draft, validating, rejected, screening, clean, flagged, edit_requested, overridden, cancelled, forwarded, response_received, discarded (STATE_DIAGRAMS.md §1) |
| `ScreeningResult` verdicts | FLAG, NO_FLAG, UNAVAILABLE (context check could not complete; the rule-based verdict is never UNAVAILABLE) |
| `TestSetEntry.groundTruthLabel` | FLAG, NO_FLAG |
| `FlaggedSpan.detectorSource` | rule, context |
| `DetectionCategory.tier` | rule-based, context-aware |
| `EvaluationLogEntry.outcome` | flagged, unflagged, override (sent anyway), redacted (sent with every flagged detail hidden), unavailable (context-aware check could not complete and nothing was flagged, NFR-015) |
| `TestSetEntry.groundTruthCategory` | ID_NUMBER, FINANCIAL, CONTACT_LOCATION, MEDICAL, INSTITUTIONAL, CLEAN |
| `User.role` | student, admin |
| `User.status` | active, suspended |
| `Message.role` | user, assistant |
| `AdminAuditLog.actionType` | suspend, reinstate |

### 6.4 Where each method is implemented

Entities are immutable data, so methods that only *read* an entity's own fields are on the entity; methods that change state, call other components, or touch storage are in the factory or service layer (single responsibility).

| Method in the class diagram | Implemented as |
|---|---|
| `Prompt.validate()` | `build_prompt()` rejects empty or over-long text (FR-001) |
| `Prompt.submit()` | `ScreeningService.screen()` |
| `ScreeningResult.aggregate()` | `ScreeningResult.aggregate()`; the factory always computes the aggregated verdict |
| `ScreeningResult.isFlagged()` | `ScreeningResult.is_flagged` |
| `FlaggedSpan.getExplanation()` | `ExplanationGenerator.explain()` (category descriptions from `detection_categories.json`) |
| `RulePattern.matches(text)` | `RulePattern.matches()`; `RulePattern.finditer()` added so the detector can locate every match |
| `TestSetEntry.runThroughDetectors()` | The evaluation harness (`run_rule_eval.py`, `run_context_eval.py`) |
| `User.register()`, `User.authenticate()` | Supabase Auth (AUTH_DESIGN.md §0) |
| `User.deleteAccount()` | Account deletion service (AUTH_DESIGN.md §8.2) |
| `Session.invalidate()`, `EmailVerificationToken.verify()`, `PasswordResetToken.resetPassword()` | Supabase Auth |
| `Conversation.delete()` | `ChatService.delete_conversation()` (FR-020) |

Two read-only helpers were added to `User`: `is_admin` and `can_submit_prompts` (verified and active, FR-014/FR-021), so the rule is defined once rather than repeated in every service.

## Links (updated)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [../requirements/USE_CASES.md](../requirements/../requirements/USE_CASES.md)