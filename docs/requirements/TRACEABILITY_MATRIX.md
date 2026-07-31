# TRACEABILITY_MATRIX.md — SentryPrompt4

**Feeds:** Design Phase Template §6 (Requirements Traceability, 20 marks) — "every row must be completed... traceable to a specific design artefact with a clear justification."
**Source:** every requirement below comes from REQUIREMENTS.md (22 FRs, 14 NFRs, 36 total). Nothing here is invented at this stage — this document only links what already exists across the other artefacts.

---

## Functional Requirements

| Requirement | Design Element / Artefact | Justification |
|---|---|---|
| **FR-001** — reject empty prompt input | `ScreeningService.screen_prompt()` (../architecture/SERVICE_LAYER.md §1); 400 error response (../architecture/SERVICE_LAYER.md §3) | Validation raised before either detector is invoked, so no wasted detection cycle occurs; verified by TC-011 |
| **FR-002** — rule-based detection | Rule-Based Detector component (../architecture/ARCHITECTURE.md Level 3); `RulePattern` entity (../architecture/DOMAIN_MODEL.md) | Pattern rules live in a separate, editable entity rather than inline code (also satisfies NFR-005); verified by TC-001, TC-002 |
| **FR-003** — context-aware detection | Context-Aware Detector component (../architecture/ARCHITECTURE.md); MODEL_../architecture/ARCHITECTURE.md (llama3.2 LLM-as-judge) | Model choice, prompt contract, and inference parameters fully specified; verified by TC-003 |
| **FR-004** — parallel, independent detection | `ScreeningService.screen_prompt()`'s `asyncio.gather()` call (../architecture/SERVICE_LAYER.md); `ScreeningResult` storing both verdicts as separate fields (../architecture/DOMAIN_MODEL.md) | Independence is structural (two fields, one concurrent call), not just described in prose; verified by TC-004 |
| **FR-005** — highlight flagged spans | `FlaggedSpan` entity; API response `flags[].span` field (../architecture/SERVICE_LAYER.md §3) | Exact substring returned, not a generic "flagged" flag; verified by TC-005 |
| **FR-006** — plain-language explanation | Explanation Generator component (../architecture/ARCHITECTURE.md); API response `explanation` field | Category-specific, non-technical wording; verified by TC-012 |
| **FR-007** — edit / send anyway / cancel | UC4, UC5, UC6 (USE_CASES.md); flag review dialog (working frontend prototype) | Three-way choice implemented and demoed, not just specified; verified by TC-006 |
| **FR-008** — cancelled prompts never reach Ollama | Container diagram `Rel(api, ollama)` gated on aggregator decision (../architecture/ARCHITECTURE.md); UC6 postcondition | Verified by TC-007 |
| **FR-009** — response returned via originating interface | Container diagram response-path relations, added during Increment 2A's fix of the original diagram gap | Verified by TC-013 |
| **FR-010** — extension screens third-party platform prompts | Browser Extension container (../architecture/ARCHITECTURE.md); UC2 | Verified by TC-008; known DOM-change fail-open limitation documented in UC2's alternative flow, not hidden |
| **FR-011** — content-free log entries | `EvaluationLogEntry` entity, structurally missing a `rawText` field (../architecture/DOMAIN_MODEL.md); `EvaluationLogEntryRepository` with no `delete()` method (../architecture/REPOSITORY_DESIGN.md) | Enforced at the schema/interface level, not by developer discipline; verified by TC-009 |
| **FR-012** — evaluation independent of live usage | ../evaluation/EVALUATION_HARNESS_DESIGN.md; `TestSetEntry` entity with no foreign key into live-path entities | Directly closes the gap identified in Increment 2A; verified by TC-010 |
| **FR-013** — account registration | `AuthService.register()`; `POST /api/auth/register`; `User` entity | ../architecture/AUTH_DESIGN.md |
| **FR-014** — email verification required before screening | `EmailVerificationToken` entity; `POST /api/auth/verify`; `AuthService` gate | Unverified accounts blocked from `/api/prompts/screen` (../architecture/SERVICE_LAYER.md §2, 403 response) |
| **FR-015** — login without account enumeration | `POST /api/auth/login`; `UserRepository.find_by_email()`; identical error response for bad email or bad password | Prevents an attacker from learning which emails are registered |
| **FR-016** — logout invalidates session server-side | `POST /api/auth/logout`; `SessionRepository` | Session removed from storage, not just cleared client-side |
| **FR-017** — password reset via time-limited token | `PasswordResetToken` entity; `POST /api/auth/reset-password/*` | Single-use, expiring token, per ../architecture/SERVICE_LAYER.md §2 |
| **FR-018** — profile view/edit/delete | `GET/PUT/DELETE /api/profile`; `User` entity; cascade/re-verification behavior specified in ../architecture/AUTH_DESIGN.md §8.1 | Email change re-triggers FR-014 verification |
| **FR-019** — persistent conversation history | `Conversation`/`Message` entities; `GET /api/conversations`; `ConversationRepository` | Reverse-chronological listing, per FR wording |
| **FR-020** — conversation/account deletion (right to erasure) | `DELETE /api/profile`, `DELETE /api/conversations/{id}`; concrete 6-step cascade order specified in ../architecture/AUTH_DESIGN.md §8.2, orchestrated in the service layer, not the repository (../architecture/REPOSITORY_DESIGN.md §3.1 comment) | Deletes underlying records, not a visibility flag; applies regardless of `emailVerified` state |
| **FR-021** — admin account management panel | Admin Panel container (../architecture/ARCHITECTURE.md); `AdminService`; `GET /api/admin/users` + suspend/reinstate endpoints | `AdminService` has no dependency on `MessageRepository` — the content-access boundary is structural |
| **FR-022** — immutable admin audit log | `AdminAuditLog` entity, with no `update()`/`delete()` exposed (../architecture/REPOSITORY_DESIGN.md); `GET /api/admin/audit-log` | Immutability enforced at the repository interface, not policy alone |

---

## Non-Functional Requirements

| Requirement | Design Element / Artefact | Justification |
|---|---|---|
| **NFR-001** — plain-language explanations | Explanation Generator component; UC3 spec | Qualitative — no dedicated automated test case, verified by design/content review instead (see TEST_CASES.md §3 coverage notes) |
| **NFR-002** — ≤1 extra click when clean | UI_MOCKUPS.md flag dialog flow | Verified by prototype walkthrough, not an automated test |
| **NFR-003** — fully local deployment | ../architecture/ARCHITECTURE.md — local Ollama, SQLite, no cloud dependency | Verified by TC-NF-002 (partially — see NFR-008) |
| **NFR-004** — single-command/documented setup | `setup.sh` design specified in ../architecture/ARCHITECTURE.md's "Setup Script Design" subsection | A single shell script chosen over Docker/Make deliberately — not yet end-to-end tested, stated honestly rather than assumed |
| **NFR-005** — configurable rule patterns | `RulePattern` entity, separate from detection logic code | Same artefact as FR-002 |
| **NFR-006** — unit test coverage of the five taxonomy categories | TEST_CASES.md's Requirement Coverage Matrix (§3) | Confirms all categories have at least one dedicated test case |
| **NFR-007** — screening service independently scalable | NLP Screening Service as its own Container (../architecture/ARCHITECTURE.md), separate from the Backend API | Architecturally separable even though NFR-007 explicitly targets single-user load for this prototype |
| **NFR-008** — no external transmission during PromptShield's own screening/inference | Corrected wording from Increment 2A; MODEL_../architecture/ARCHITECTURE.md's local `llama3.2` inference | Verified by TC-NF-002, deliberately scoped to exclude the extension's legitimate external forwarding (FR-010) |
| **NFR-009** — evaluation log is content-free | `EvaluationLogEntry` schema (../architecture/DOMAIN_MODEL.md); no `rawText` field exists on the entity | Verified by TC-009; enforced structurally, per FR-011 |
| **NFR-010** — screening completes within 2 seconds | `ScreeningService`'s parallel `asyncio.gather()` design | **Not yet empirically verified** — MODEL_../architecture/ARCHITECTURE.md §4 explicitly flags this as unbenchmarked; TC-NF-001 exists but has not been run |
| **NFR-011** — message content encrypted at rest | `MessageRepository.save()` encrypts before storage (../architecture/REPOSITORY_DESIGN.md §3.2) | Enforced inside the repository, not the service layer — cannot be bypassed by a careless caller |
| **NFR-012** — passwords hashed, never plaintext | `AuthService` (bcrypt/Argon2, per ../architecture/AUTH_DESIGN.md) | — |
| **NFR-013** — admin has no conversation-content access | `AdminService` has no `MessageRepository`/`ConversationRepository` dependency at all (../architecture/SERVICE_LAYER.md §1) | Structural, not a policy comment — the class cannot call what it was never given |
| **NFR-014** — right-to-erasure account deletion | Same artefact as FR-020 (../architecture/AUTH_DESIGN.md §8.2) | POPIA compliance framing stated explicitly in SPECIFICATION.md §1.3; precedence over `AdminAuditLog` retention (FR-022) stated explicitly in §8.2, not left ambiguous |

---

## Board Note on Gaps Surfaced by This Pass

Building this matrix exposed two things worth stating plainly rather than smoothing over:

1. **NFR-004 now has a design artefact** — a minimal `setup.sh` script is specified in ../architecture/ARCHITECTURE.md's "Setup Script Design" subsection, closing what was previously a named gap with no artefact at all. It is explicitly not yet end-to-end tested — that remains implementation-phase work, stated honestly rather than assumed.
2. **NFR-010's performance claim is architecturally plausible but empirically unverified** — the design supports it, but no real measurement exists yet. This should be reported as-is in the Design Phase Template's evaluation section (§9), not presented as already confirmed.

Both are carried forward into ../evaluation/EVALUATION_OF_DESIGN.md's risk table rather than fixed here — this document's job is to expose gaps accurately, not to quietly patch over them by inventing an artefact that doesn't exist.

## Links
- [REQUIREMENTS.md](REQUIREMENTS.md)
- [../architecture/DOMAIN_MODEL.md](../architecture/../architecture/DOMAIN_MODEL.md)
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)
- [../architecture/SERVICE_LAYER.md](../architecture/../architecture/SERVICE_LAYER.md)
- [../architecture/REPOSITORY_DESIGN.md](../architecture/../architecture/REPOSITORY_DESIGN.md)
- [TEST_CASES.md](TEST_CASES.md)