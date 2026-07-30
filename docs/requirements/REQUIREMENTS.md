# REQUIREMENTS.md

**Project:** SentryPrompt4
**Traceability:** Each requirement maps to a stakeholder concern (STAKEHOLDER_ANALYSIS.md) and, where relevant, an existing architectural component (../architecture/ARCHITECTURE.md).

---

## 1. Functional Requirements

| ID | Requirement | Acceptance Criteria | Traces to |
|---|---|---|---|
| FR-001 | The system shall accept free-text prompt input from the student via the web chat application. | Text input accepted up to a defined max length; empty input rejected with a clear message. | Student |
| FR-002 | The system shall screen every submitted prompt using rule-based pattern detection before forwarding it to the model. | ID numbers, phone numbers, emails, and bank details are detected with documented regex/pattern rules. | Student, IT Security |
| FR-003 | The system shall screen every submitted prompt using a context-aware (semantic) detector for categories not caught by rules. | Medical and institutional-confidential language is classified via the Ollama-backed detector, independent of the rule-based result. | Student, Data Protection Officer |
| FR-004 | The system shall run rule-based and context-aware detection in parallel on every prompt, not as a fallback chain. | Both detectors execute and return results for every request; results are logged separately before aggregation. | Project Supervisor (research validity) |
| FR-005 | When a prompt is flagged, the system shall highlight the specific flagged span(s) of text to the student. | UI visibly marks the exact substring(s) triggering the flag, not just a generic warning. | Student |
| FR-006 | When a prompt is flagged, the system shall display a plain-language explanation of what was detected and why it is risky. | Explanation names the category (e.g. "medical information") and references the relevant risk (e.g. POPIA exposure) in non-technical language. | Student, Data Protection Officer |
| FR-007 | The system shall allow the student to choose one of three actions on a flagged prompt: edit, send anyway, or cancel. | All three actions are available and functional; no forced blocking occurs. | Student |
| FR-008 | The system shall forward only approved (unflagged, or explicitly "send anyway") prompts to the local Ollama model. | Flagged-and-cancelled prompts never reach the model; this is verifiable in logs. | Data Protection Officer |
| FR-009 | The system shall return the model's response to the student via the same interface the prompt was submitted through. | Response displayed in web app or injected into the third-party platform interface (via extension) as appropriate. | Student |
| FR-010 | The browser extension shall screen prompts typed into at least one third-party AI platform interface without requiring the student to leave that platform. | Extension detects and screens prompt text in the target platform's input field before submission. | Student |
| FR-011 | The system shall record an anonymized log entry for every screened prompt (flagged or not), for evaluation purposes only. | Log entries exclude raw sensitive content where flagged; record includes classification result and detector used. | Project Supervisor (evaluation) |
| FR-012 | The system shall support running the evaluation method (precision/recall/false-positive rate) against a hand-labeled test set independent of live usage. | A defined test set can be run through both detectors and scored without needing live student interaction. | Project Supervisor (evaluation) |
| FR-013 | The system shall allow a student to register an account using an email address and password. | Registration form validates email format and password strength; duplicate emails are rejected with a clear message. | Student |
| FR-014 | The system shall require email verification via a time-limited token before a new account can submit prompts. | Unverified accounts can log in but are blocked from prompt submission until the verification link is used; token expires after a defined window. | Student, Data Protection Officer |
| FR-015 | The system shall allow a registered, verified student to log in with email and password, creating a session. | Valid credentials produce an active session; invalid credentials are rejected without revealing whether the email or password was wrong (prevents account enumeration). | Student, IT Security |
| FR-016 | The system shall allow a logged-in student to log out, invalidating their session. | Session token is invalidated server-side on logout, not just cleared client-side. | Student |
| FR-017 | The system shall allow a student to reset a forgotten password via a time-limited emailed token. | Reset link expires after a defined window and can only be used once; password is never emailed in plaintext. | Student |
| FR-018 | The system shall allow a logged-in student to view, edit, and delete their own profile information. | Display name and email are editable; email change re-triggers verification (FR-014). | Student |
| FR-019 | The system shall persist a student's conversation history, viewable and navigable within the web application. | Conversations are listed per user, in reverse-chronological order, and can be reopened to view prior messages. | Student |
| FR-020 | The system shall allow a student to delete an individual conversation, or their entire account and all associated data. | Deletion is permanent and removes the underlying `Message` records, not just a visibility flag; account deletion satisfies POPIA's right-to-erasure expectation. | Student, Data Protection Officer |
| FR-021 | The system shall provide an administrator role with a dedicated panel to view and manage user accounts (view status, suspend, reinstate). | Admin panel is only reachable by users with the `admin` role; admin actions are restricted to account-level data (status, verification state) and explicitly **do not** grant access to the content of other users' conversations — this is a deliberate design boundary, not a missing feature. | System Administrator, Data Protection Officer |
| FR-022 | The system shall record every admin action to an immutable audit log. | Each admin action (suspend, reinstate, etc.) is logged with admin ID, target user ID, action type, and timestamp; log entries cannot be edited or deleted through the application. | System Administrator, Data Protection Officer |

---

## 2. Non-Functional Requirements

| Category | ID | Requirement |
|---|---|---|
| **Usability** | NFR-001 | The flagged-content explanation shall be understandable to a student with no data-privacy or legal background (plain language, no jargon). |
| **Usability** | NFR-002 | The warn-and-decide interaction (edit/send/cancel) shall require no more than one additional click/action beyond normal prompt submission when no sensitive content is detected. |
| **Deployability** | NFR-003 | The backend and screening service shall run entirely on a local development machine (no cloud dependency), consistent with the local-Ollama scope decision. |
| **Deployability** | NFR-004 | The web application and screening service shall be deployable via a documented single-command or scripted setup (e.g. `docker compose up` or an equivalent documented sequence). |
| **Maintainability** | NFR-005 | The rule-based detector's patterns shall be defined in a separate, editable configuration/data file, not hard-coded inline, so categories can be added without touching detection logic. |
| **Maintainability** | NFR-006 | The system shall include unit tests for the rule-based detector and the aggregation logic, covering at minimum the five taxonomy categories in SPECIFICATION.md §3. |
| **Scalability** | NFR-007 | The screening service shall be architected as a distinct component (per ../architecture/ARCHITECTURE.md Container diagram) so it could be scaled or replaced independently of the client surfaces, even though this prototype targets single-user local load. |
| **Security** | NFR-008 | SentryPrompt4's own screening and inference logic (rule-based detection, context-aware detection, and responses to approved prompts within the web app) shall run entirely via the local Ollama instance, with no prompt content sent to an external service *for the purpose of screening*. This does not apply to the student's own downstream choice to submit an approved prompt to a third-party AI platform via the extension — that transmission is the extension's intended function (FR-010), not a violation of this requirement. |
| **Security** | NFR-009 | Logged evaluation records shall not store the raw text of a prompt classified as sensitive; only the classification result, category, and anonymized metadata shall be retained. |
| **Performance** | NFR-010 | Combined rule-based and context-aware screening shall complete within 2 seconds for a typical prompt (under ~200 words) on standard development hardware, to avoid materially disrupting the student's workflow. |
| **Security** | NFR-011 | Persisted conversation content (`Message` records) shall be encrypted at rest (e.g. AES-256), distinct from the evaluation log's content-free storage policy (NFR-009) — these are two separate data stores with two separate rules, not a contradiction. |
| **Security** | NFR-012 | Passwords shall be hashed using a strong adaptive hashing algorithm (e.g. bcrypt or Argon2) and never stored or logged in plaintext. |
| **Security** | NFR-013 | Administrators shall have account-level visibility only (status, verification state, audit trail); the admin role shall have no access path to the content of another user's conversations, by design. |
| **Compliance** | NFR-014 | A student shall be able to permanently delete their account and all associated conversation data in a single action, satisfying POPIA's right-to-erasure expectation; deletion shall remove underlying records, not merely hide them. |

---

## 2A. Architecture Consistency Check (post-hoc, run against ../architecture/ARCHITECTURE.md)

- **NFR-008 corrected:** original wording banned all external transmission, which contradicted FR-010 (the extension's core purpose is to screen prompts *headed to* external third-party platforms). Reworded to scope the "local-only" constraint to SentryPrompt4's own screening/inference, not the student's downstream platform choice.
- **Gap identified, deferred to Increment 5/8:** ../architecture/ARCHITECTURE.md's Component diagram shows only one entry point into the Screening Service (via the live Backend API). FR-012 requires an evaluation path independent of live usage. ../architecture/ARCHITECTURE.md needs a documented offline evaluation harness (a script/component that calls the Screening Service directly against a labeled test set, bypassing the API/client layers). Not fixed yet — tracked for when Increment 8 (Model Architecture & Evaluation Run) is built.
- **Minor fix flagged:** response-path arrows (`api` → `webapp`/`extension`) are implied but not drawn in the Container diagram. Cosmetic; fix alongside the evaluation harness addition rather than as a separate pass.

## 3. Board Review Notes (challenges considered before finalizing)

- **Why parallel detection (FR-004) instead of fallback-only?** A fallback design (only run context-aware when rules miss) is simpler and faster, but destroys the research comparison that is the actual contribution of this project (SPECIFICATION.md §6). Parallel execution was kept as a requirement, not just a design choice, specifically so it can't be quietly simplified away later under implementation time pressure.
- **Why "send anyway" instead of a hard block (FR-007)?** A hard block is more protective on paper but has a known failure mode: users disable or route around tools that block them outright, which would defeat the purpose entirely. Warn-and-decide is the recommended trade-off, accepted with the risk noted.
- **Security NFR-009 exists because of a real conflict:** the evaluation requirement (FR-011, FR-012) needs data to measure detection accuracy, but a privacy tool that logs the sensitive content it detects would be self-defeating. NFR-009 resolves this: log the *classification*, not the *content*, for anything flagged.
- **Gap acknowledged, not solved here:** there is no NFR covering model drift or Ollama version changes (noted as a Stakeholder risk for the "Ollama Maintainers" row). This is deferred to the Risks section of the Design Phase Template (§9.4), not resolved as a requirement, since mitigating it is out of individual scope.

## Links
- [SPECIFICATION.md](SPECIFICATION.md)
- [STAKEHOLDER_ANALYSIS.md](STAKEHOLDER_ANALYSIS.md)
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)