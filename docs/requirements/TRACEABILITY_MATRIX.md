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
| **FR-004** — both detectors always run, independently | `ScreeningService.screen()` (`backend/app/service/screening/screening_service.py`); `ScreeningResult` storing both verdicts as separate fields | Verified by `backend/tests/service/screening/test_screening_service.py` (rule-only, context-only, both, context failure) and TC-004 |
| **FR-005** — highlight flagged spans | `FlaggedSpan` entity; `RedactedText.to_original()` maps context-aware spans back to the original text; API response `flags[].span` field (../architecture/SERVICE_LAYER.md §3) | Exact positions in the student's text; verified by service tests (including spans after and over redacted values) and TC-005 |
| **FR-006** — plain-language explanation | `ExplanationGenerator` using each category's description in `detection_categories.json`; API response `explanation` field | Category-specific, non-technical wording maintained as data; verified by `test_explanation_generator.py` and TC-012 |
| **FR-007** — edit / send anyway / cancel | `POST /api/conversations/{id}/messages` returns `status: "needs_decision"` for flagged or unchecked prompts; `sendAnyway: true` overrides (logged as `override`); edit = sending a new text, screened again; cancel = not sending | `backend/tests/service/conversation/test_chat_service.py`, `backend/tests/api/test_conversation_router.py` |
| **FR-008** — only approved prompts reach the LLM provider | `ChatService.send()` screens on the server and sends nothing unless clean or sent anyway; rule-detected values always redacted | Tests assert the AI receives nothing for a flagged prompt and only redacted text after send anyway |
| **FR-009** — response returned via originating interface | `SendMessageResponse.assistantMessage`; the reply is also saved in the conversation | `test_conversation_router.py` |
| **FR-010** — extension screens third-party platform prompts | Browser Extension container (../architecture/ARCHITECTURE.md); UC2 | Verified by TC-008; known DOM-change fail-open limitation documented in UC2's alternative flow, not hidden |
| **FR-011** — content-free log entries | `ScreeningService` records one `EvaluationLogEntry` per screening (flagged / unflagged / unavailable) through `EvaluationLogEntryRepository`, which has no delete (`backend/app/repository/`) | Verified by service and API tests that the entry has no prompt text; logging failure never blocks screening |
| **FR-012** — evaluation independent of live usage | ../evaluation/EVALUATION_HARNESS_DESIGN.md; `TestSetEntry` entity with no foreign key into live-path entities | Directly closes the gap identified in Increment 2A; verified by TC-010 |
| **FR-013** — account registration | `AuthService.register()`; `POST /api/auth/register`; `User` entity | ../architecture/AUTH_DESIGN.md |
| **FR-014** — email verification required before screening | Supabase Auth email confirmation (unverified accounts cannot log in); backend re-checks on every request: `AuthService.require_active()` → 403 `email_not_verified` | `backend/tests/api/test_auth_security.py` |
| **FR-015** — login without account enumeration | Supabase Auth sign-in (generic error for wrong email or password); backend `get_current_user` verifies the token with Supabase on every request | `test_auth_security.py`, `test_supabase_identity_provider.py` |
| **FR-016** — logout invalidates session server-side | Supabase Auth sign-out ends the session; the backend asks Supabase on every request (option A, AUTH_DESIGN.md §0.2), so a logged-out token is refused immediately | `test_supabase_identity_provider.py` (logged-out token rejected), `test_auth_security.py` |
| **FR-017** — password reset via time-limited token | Supabase Auth password reset (../architecture/AUTH_DESIGN.md §0) | Single-use, expiring token, per ../architecture/SERVICE_LAYER.md §2 |
| **FR-018** — profile view/edit | `GET` and `PUT /api/profile` (`backend/app/api/profile_router.py`); only `displayName` can be changed (no mass assignment); email changes go through Supabase | `test_auth_security.py` (mass-assignment and validation tests) |
| **FR-019** — persistent conversation history | `GET /api/conversations` and `/{id}`; `ConversationRepository`/`MessageRepository` (PostgreSQL), owner-scoped | `test_conversation_router.py`, `backend/tests/repository/postgres/test_conversation_repository.py` |
| **FR-020** — account deletion (right to erasure) | `DELETE /api/profile` → Supabase admin API deletes the account → database cascade (migration 0001); allowed while suspended or unverified. Conversation deletion follows in the conversations step | `test_auth_security.py`, `test_schema_security.py::test_account_deletion_cascades_but_keeps_audit_log` |
| **FR-021** — admin account management panel | Admin Panel container (../architecture/ARCHITECTURE.md); `AdminService`; `GET /api/admin/users` + suspend/reinstate endpoints | `AdminService` has no dependency on `MessageRepository` — the content-access boundary is structural. Implemented in `app/service/admin/` and `app/api/admin_router.py`; students, unverified and suspended accounts get 403 on every admin route (`test_admin_router.py::test_non_admins_get_403_on_every_admin_route`); an admin cannot act on their own account or another admin. Suspending also bans the account in Supabase Auth. |
| **FR-022** — immutable admin audit log | `AdminAuditLog` entity, with no `update()`/`delete()` exposed (../architecture/REPOSITORY_DESIGN.md); `GET /api/admin/audit-log` | Immutability enforced at the repository interface, not policy alone. Also enforced in the database: `UPDATE`, `DELETE` and `TRUNCATE` on `admin_audit_log` are rejected by triggers (tested). The status change and its audit entry are written in one transaction (`test_failed_audit_insert_rolls_back_the_status_change`). |

---

## Non-Functional Requirements

| Requirement | Design Element / Artefact | Justification |
|---|---|---|
| **NFR-001** — plain-language explanations | Explanation Generator component; UC3 spec | Qualitative — no dedicated automated test case, verified by design/content review instead (see TEST_CASES.md §3 coverage notes) |
| **NFR-002** — ≤1 extra click when clean | UI_MOCKUPS.md flag dialog flow | Verified by prototype walkthrough, not an automated test |
| **NFR-003** — provider selectable by configuration, deployable without Ollama | `backend/app/llm/registry.py` and `provider_factory.py` (`LLM_PROVIDER`), ../architecture/ARCHITECTURE.md Tech Stack | Verified by `backend/tests/llm/` (provider selection tests) |
| **NFR-004** — documented local setup and container-based deployment | ../architecture/ARCHITECTURE.md "Setup & Deployment" (local commands, `Dockerfile`, static frontend build) | Not yet tested end to end; build-phase work, stated rather than assumed |
| **NFR-005** — configurable rule patterns | `backend/app/screening/rules/detection_categories.json` (categories and regex patterns as data), loaded and validated by `JsonRuleSource` through the `DetectionCategory`/`RulePattern` factories | Adding a pattern or category is a data change, no code edit; `RuleSource` is an interface so a database-backed source (UC10) can replace the file |
| **NFR-006** — unit test coverage of the taxonomy categories | `backend/tests/screening/rules/` (each rule category, overlaps, Luhn, clean prompts, ReDoS timing, parity with the published evaluation) and TEST_CASES.md §3 | Run on every push by GitHub Actions |
| **NFR-007** — screening service independently scalable | NLP Screening Service as its own Container (../architecture/ARCHITECTURE.md), separate from the Backend API | Targets a small multi-user pilot; Supabase and Groq free-tier limits are the first ceilings (../evaluation/EVALUATION_OF_DESIGN.md §9.2) |
| **NFR-008** — prompt data minimised and only sent to no-training providers | `backend/app/screening/redaction.py` (local redaction), privacy check in `backend/app/llm/training_data_policy.py`, ../evaluation/MODEL_ARCHITECTURE.md §1 | Verified by TC-NF-002 and `backend/tests/llm/test_training_data_policy.py`, `backend/tests/screening/test_redaction.py` |
| **NFR-009** — evaluation log is content-free | `EvaluationLogEntry` has no text field; the `evaluation` schema has no column able to hold prompt text, coded columns have `CHECK` constraints, and the log is append-only in the database (`backend/migrations/versions/0001_initial_schema.py`) | Verified by `backend/tests/repository/postgres/test_schema_security.py` and API tests; TC-009 |
| **NFR-010** — screening completes within 2 seconds | Rule-based detector is local (~1 ms, ReDoS-tested); context-aware call has a 3 s worst-case cap and fails closed (../evaluation/MODEL_ARCHITECTURE.md, Failure handling) | Typical latency expected under 2 s; real figures from `run_context_eval.py`. The 3 s cap is a documented trade-off (EVALUATION_OF_DESIGN.md §9.4). TC-NF-001 not yet run |
| **NFR-011** — message content encrypted at rest | `AesGcmMessageCipher` (AES-256-GCM, per-message nonce, IDs bound as associated data) used by `PostgresMessageRepository`; key only in `MESSAGE_ENCRYPTION_KEY` | Tests: raw database rows contain no plaintext; wrong key, tampering and moved ciphertexts all fail to decrypt |
| **NFR-012** — passwords hashed, never plaintext | Supabase Auth (bcrypt), ../architecture/AUTH_DESIGN.md §0 | The application database never stores passwords or hashes |
| **NFR-013** — admin has no conversation-content access | No admin route touches conversations or messages; conversation queries are owner-scoped, so an admin is treated like any other user (404 on others' conversations); messages are ciphertext in the database | `test_conversation_router.py::test_other_students_conversation_looks_exactly_like_a_missing_one`; `test_admin_service.py::test_admin_package_has_no_access_to_conversations_or_messages` (no admin module imports anything about conversations or messages); `test_admin_router.py::test_admin_cannot_reach_other_peoples_conversations` |
| **NFR-014** — right-to-erasure account deletion | Same artefact as FR-020 (../architecture/AUTH_DESIGN.md §8.2) | POPIA compliance framing stated explicitly in SPECIFICATION.md §1.3; precedence over `AdminAuditLog` retention (FR-022) stated explicitly in §8.2, not left ambiguous. Implemented as `ON DELETE CASCADE` from `auth.users` (migration 0001); verified by `test_account_deletion_cascades_but_keeps_audit_log`. |
| **NFR-015** — screening fails closed | `Verdict.UNAVAILABLE`, `ScreeningResult.aggregate()`, `ContextAwareDetector` time limit (../evaluation/MODEL_ARCHITECTURE.md, Failure handling) | `backend/tests/screening/test_context_aware_detector.py` (timeout, provider error, unreadable reply), `backend/tests/factory/test_screening_result_factory.py` |

---

## Board Note on Gaps Surfaced by This Pass

Building this matrix exposed two things worth stating plainly rather than smoothing over:

1. **NFR-004 now has a design artefact** — local setup commands and a container-based deployment path are specified in ../architecture/ARCHITECTURE.md's "Setup & Deployment" subsection.
2. **NFR-010's performance claim is architecturally plausible but empirically unverified** — the design supports it, but no real measurement exists yet. This should be reported as-is in the Design Phase Template's evaluation section (§9), not presented as already confirmed.

Both are carried forward into ../evaluation/EVALUATION_OF_DESIGN.md's risk table rather than fixed here — this document's job is to expose gaps accurately, not to quietly patch over them by inventing an artefact that doesn't exist.

## Links
- [REQUIREMENTS.md](REQUIREMENTS.md)
- [../architecture/DOMAIN_MODEL.md](../architecture/../architecture/DOMAIN_MODEL.md)
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)
- [../architecture/SERVICE_LAYER.md](../architecture/../architecture/SERVICE_LAYER.md)
- [../architecture/REPOSITORY_DESIGN.md](../architecture/../architecture/REPOSITORY_DESIGN.md)
- [TEST_CASES.md](TEST_CASES.md)