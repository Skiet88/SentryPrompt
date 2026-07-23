# ERD.md — SentryPrompt4

**Increment:** 5 — Data Model: ERD & AI Data Pipeline
**Traces to:** DOMAIN_MODEL.md (all 14 entities), REQUIREMENTS.md NFR-009, NFR-011, NFR-012, NFR-014
**Note on scope:** this document adds concrete database-level detail (types, keys, constraints) to entities already defined conceptually in DOMAIN_MODEL.md. No new entity or relationship is introduced here that DOMAIN_MODEL.md didn't already specify.

---

## 1. Entity-Relationship Diagram

Per the Database Architect's note above, **`Prompt` is deliberately excluded from this ERD** — it is a transient, in-memory-only object (DOMAIN_MODEL.md §1) and has no corresponding table. Its shape is documented in DOMAIN_MODEL.md and referenced here only as a conceptual source for `Message` and `EvaluationLogEntry`.

```mermaid
erDiagram
    SCREENING_RESULT ||--o{ FLAGGED_SPAN : contains
    FLAGGED_SPAN }o--|| DETECTION_CATEGORY : classified_as
    DETECTION_CATEGORY ||--o{ RULE_PATTERN : defined_by
    SCREENING_RESULT ||--o| EVALUATION_LOG_ENTRY : summarized_as
    DETECTION_CATEGORY |o--o{ EVALUATION_LOG_ENTRY : "categorizes (nullable)"

    USER ||--o{ SESSION : has
    USER ||--o| EMAIL_VERIFICATION_TOKEN : has
    USER ||--o| PASSWORD_RESET_TOKEN : has
    USER ||--o{ CONVERSATION : owns
    CONVERSATION ||--|{ MESSAGE : contains
    USER ||--o{ ADMIN_AUDIT_LOG : "is target of"
    USER ||--o{ ADMIN_AUDIT_LOG : "performs (as admin)"

    SCREENING_RESULT {
        string resultId PK
        string promptSourceChannel
        string ruleBasedVerdict
        string contextAwareVerdict
        string aggregatedVerdict
        datetime decidedAt
    }

    FLAGGED_SPAN {
        string spanId PK
        string resultId FK
        int startIndex
        int endIndex
        string detectorSource
        string categoryId FK
    }

    DETECTION_CATEGORY {
        string categoryId PK
        string name
        string description
        string tier
    }

    RULE_PATTERN {
        string patternId PK
        string categoryId FK
        string regexPattern
        string description
    }

    EVALUATION_LOG_ENTRY {
        string logId PK
        string resultId FK
        string categoryId FK "nullable"
        string outcome
        string timestampBucket
    }

    TEST_SET_ENTRY {
        string entryId PK
        string sampleText
        string groundTruthCategory
        string groundTruthLabel
    }

    USER {
        string userId PK
        string email UK
        string passwordHash
        string displayName
        string role
        bool emailVerified
        string status
        datetime createdAt
    }

    SESSION {
        string sessionId PK
        string userId FK
        string token UK
        datetime createdAt
        datetime expiresAt
    }

    EMAIL_VERIFICATION_TOKEN {
        string tokenId PK
        string userId FK
        string token UK
        datetime expiresAt
        bool used
    }

    PASSWORD_RESET_TOKEN {
        string tokenId PK
        string userId FK
        string token UK
        datetime expiresAt
        bool used
    }

    CONVERSATION {
        string conversationId PK
        string userId FK
        string title
        string channel
        datetime createdAt
        datetime updatedAt
    }

    MESSAGE {
        string messageId PK
        string conversationId FK
        string role
        string content "encrypted at rest, NFR-011"
        datetime createdAt
    }

    ADMIN_AUDIT_LOG {
        string logId PK
        string adminUserId FK
        string targetUserId FK
        string actionType
        datetime timestamp
        string details
    }
```

**Note:** `TEST_SET_ENTRY` is drawn with no relationship lines to any other entity — this is intentional and mirrors DOMAIN_MODEL.md exactly. It is consumed only by the offline evaluation harness (§3 below), never joined against live tables.

---

## 2. Schema Notes & Constraints

| Table | Key constraints | Rationale |
|---|---|---|
| `USER` | `email` UNIQUE | Prevents duplicate registration (FR-013); enforced at the database level, not just application logic. |
| `SESSION` | `token` UNIQUE, index on `expiresAt` | Fast lookup on every authenticated request; supports the idle-timeout check in AUTH_DESIGN.md §3. |
| `EMAIL_VERIFICATION_TOKEN` | `token` UNIQUE | Per Backend Architect's note — a duplicate active token is a defect class, not just an edge case. |
| `PASSWORD_RESET_TOKEN` | `token` UNIQUE | Same reasoning as above. |
| `EVALUATION_LOG_ENTRY` | `categoryId` FK is **nullable** | An "unflagged" outcome has no category to reference — this must be a valid, not a worked-around, state (Security Architect's note above). |
| `MESSAGE` | `content` stored encrypted (application-layer encryption before write, AES-256 per NFR-011) | The database itself stores ciphertext; the encryption key is managed by the Auth/Backend service, not the database layer, so a raw database dump alone does not expose conversation content. |
| `TEST_SET_ENTRY` | No foreign keys to any other table | Structural independence guarantee (DOMAIN_MODEL.md, AI/ML Architect's note above). |
| `ADMIN_AUDIT_LOG` | Two FKs to `USER` (`adminUserId`, `targetUserId`); **no FK to `MESSAGE` or `CONVERSATION`** | Enforces NFR-013 at the schema level — there is no column an admin query could join through to reach conversation content, even by mistake. |

---

## 3. Summary Table — Requirement Coverage

| Requirement | Covered by |
|---|---|
| NFR-009 (no raw content in evaluation logs) | §2 (`EVALUATION_LOG_ENTRY` schema note) |
| NFR-011 (encryption at rest) | §2 (`MESSAGE` schema note) |
| NFR-012 (password hashing) | Enforced at write-time by Auth Service (AUTH_DESIGN.md §1–§2); ERD stores only the resulting hash, never plaintext |
| NFR-014 (right to erasure) | Deletion mechanics (which rows get removed on account deletion) are **not yet specified here** — tracked as a follow-up alongside the deferred FR-020 flow noted in AUTH_DESIGN.md |
| FR-011, FR-012 (evaluation logging & independent test harness) | See [DATA_PIPELINE.md](./DATA_PIPELINE.md) — the data flow itself is documented there, this ERD only covers the schema it reads/writes |

**Known gap, not hidden:** the exact cascade behavior on account/conversation deletion (which rows in `CONVERSATION`, `MESSAGE`, `SESSION`, etc. get removed and in what order) is not specified in this document. This belongs with the FR-018/FR-020/NFR-014 follow-up already flagged as deferred in AUTH_DESIGN.md, rather than being guessed at here.

## Links
- [DOMAIN_MODEL.md](./DOMAIN_MODEL.md)
- [AUTH_DESIGN.md](./AUTH_DESIGN.md)
- [DATA_PIPELINE.md](./DATA_PIPELINE.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [PROJECT_BACKLOG.md](./PROJECT_BACKLOG.md)
