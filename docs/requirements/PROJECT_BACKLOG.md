# PROJECT_BACKLOG.md — SentryPrompt4: Design Phase Roadmap

> **Scope change log:** on [this date], scope was deliberately expanded from a single-user research prototype (7 domain entities) to a full account-based platform — registration, login, email verification, password reset, persistent conversation history, and an admin panel (14 domain entities total). This is additive to the Assignment 3 core (still the same screening research), not a pivot, per Assignment 4's Agile-update allowance. Increments 4B, 4C, and revised versions of 6, 7, 9, and 13 below reflect this. REQUIREMENTS.md and ../architecture/DOMAIN_MODEL.md have already been updated; SPECIFICATION.md §1.3 (Individual Scope) still needs a short revision to match — tracked as Increment 1B below.

**Purpose:** This backlog exists because two things must be satisfied simultaneously and they are not the same document:
1. **The graded deliverable** — the Design Phase Template (12 sections, 100 marks: Design Documents 30 / Diagrams 25 / Prototypes 25 / Traceability 20), due first week of the September term.
2. **The process your supervisor expects to see**, based on his prior course's assignment sequence (PrevProjectAssignment.pdf, Assignments 3–12).

Every increment below is named in the supervisor's style, but its real purpose is stated as **which Template section(s) it produces evidence for**. Nothing is built "because the old assignment said so" without a corresponding line in the actual rubric — if it doesn't feed the Template, it's marked as *process-only* and de-prioritized.

---

## Phase Gate Model (Review Board)

Each increment below is tagged with which of the 10 board phases it primarily closes:

`P1` Understand the business · `P2` Stakeholders · `P3` Requirements · `P4` Constraints · `P5` Architecture · `P6` Security review · `P7` Scalability review · `P8` Maintainability review · `P9` Testing strategy · `P10` Implementation approval

Architecture (P5) was drafted early, out of sequence, because Assignment 3's brief required it first. It is **provisionally approved**, pending a consistency check once P2/P3 artifacts (now done) are cross-checked against it. This check is Increment 2A below and is not optional.

---

## Master Backlog

| # | Increment (supervisor-style name) | Board Phase(s) | Produces | Feeds Template Section(s) | Status | Priority |
|---|---|---|---|---|---|---|
| 0 | System Specification & C4 Architecture *("Assignment 3")* | P1, P5 | README.md, SPECIFICATION.md, ../architecture/ARCHITECTURE.md | §1 Introduction, §2 Design Overview, §3.1 HLD, §4.1 System/Architecture Diagram | ✅ Done | — |
| 1 | Stakeholder Analysis & Requirements *("Assignment 4")* | P2, P3 | STAKEHOLDER_ANALYSIS.md, REQUIREMENTS.md | §1.1–1.3, §6 Traceability Matrix (REQ-IDs), §9.1 (feasibility inputs) | ✅ Done | — |
| **1B** | **Revise SPECIFICATION.md Individual Scope** *(new — scope expansion)* | P1, P4 | Short revision to §1.3: acknowledge Agile-driven expansion to full platform, restate feasibility with the larger footprint (accept realistic timeline trade-offs) | §1.3 Project Scope, §2.2 Justification of Chosen Approach | ✅ Done | — |
| **2A** | **Architecture Consistency Check** *(board gate, not a supervisor assignment)* | P5 (re-review) | Found & fixed a real contradiction (NFR-008 vs. extension purpose); identified a real gap (no offline evaluation entry point, deferred to Inc. 8) | Strengthens §3.1, §4.1; prerequisite for trusting later diagrams | ✅ Done | — |
| 2 | Use Case Modeling & Test Case Development *("Assignment 5")* | P3, P9 | USE_CASES.md (diagram + specs), TEST_CASES.md | §4.3 Sequence/Interaction Diagram (required diagram type #2), §3.1.2 Component Interactions, seeds §9 testing strategy | ✅ Done for FR-001–FR-012 (screening flow) — **not yet extended to FR-013–FR-022** (platform layer: registration, login, password reset, conversation history, admin actions). Tracked as a follow-up under Increment 4B/9 rather than left silent. | — |
| 3 | Domain Model & Class Diagram *("Assignment 9")* | P3, P5 | ../architecture/DOMAIN_MODEL.md, CLASS_DIAGRAM.md (Mermaid) — now 14 entities (7 research-domain + 7 platform-domain) | §3.2.1 Module/Component Specifications, feeds ERD (Inc. 5) | ✅ Done (expanded) | — |
| 4 | State & Activity Diagrams *("Assignment 8")* | P3, P9 | ../diagrams/STATE_DIAGRAMS.md, ../diagrams/ACTIVITY_DIAGRAMS.md — now including account lifecycle (registration → verified → active → suspended) and message-persistence workflow | §4.2 Flowchart/Process Flow Diagram (required diagram type #3), §3.2.2 Algorithms and Logic | ✅ Done: ../diagrams/STATE_DIAGRAMS.md and ../diagrams/ACTIVITY_DIAGRAMS.md, including the account lifecycle and suspend/reinstate flows | — |
| 4B | **Auth & Account Module Design** *(new — scope expansion)* | P3, P5, P6 | ../architecture/AUTH_DESIGN.md — registration/verification/login/reset flows, session handling approach, admin-panel access boundary | §3.2.1 Module Specs, §8.1.3 Module Decomposition | ✅ Done: FR-018, FR-020 and NFR-014 are now closed in ../architecture/AUTH_DESIGN.md §8 | — |
| 4C | **Admin Panel Design** *(new — scope expansion)* | P2, P3, P5 | ADMIN_PANEL.md — admin use cases, account-level-only access boundary, audit log design | §8.1.1 UI Design (admin screens), §3.2.1 | ✅ Done: ../architecture/ADMIN_PANEL.md | — |
| 5 | Data Model: ERD & AI Data Pipeline *(merges App Dev §8.1.2 + AI/DS §8.3.2)* | P3, P5 | ../architecture/ERD.md/diagram (now covering all 14 entities, including User/Session/Conversation/Message relationships), ../architecture/DATA_PIPELINE.md | §4.4 Data/ERD Diagram (required diagram type #4), §8.1.2, §8.3.2 | ✅ Done: the deletion cascade (NFR-014) is now specified in ../architecture/AUTH_DESIGN.md §8.2 | — |
| 6 | Repository Layer Design *("Assignment 11")* | P5, P8 | ../architecture/REPOSITORY_DESIGN.md + interface stubs — now including UserRepository, SessionRepository, ConversationRepository, MessageRepository alongside the original research-domain repositories | §3.2.1 Module Specifications, §3.1.3 Tech Stack justification | ✅ Done: ../architecture/REPOSITORY_DESIGN.md | — |
| 7 | Service Layer & REST API *("Assignment 12")* | P5, P9 | ../architecture/SERVICE_LAYER.md, API design, OpenAPI/Swagger stub — now including AuthService (register/login/verify/reset), ConversationService, and AdminService endpoints | §3.2.3 Interface Specifications, §8.4.2 (optional, Web Tech cross-reference), prototype evidence (§5) | ✅ Done: ../architecture/SERVICE_LAYER.md (17 endpoints). The OpenAPI schema is generated by FastAPI at build time (§4) | — |
| 8 | Model Architecture & Evaluation Run *(AI/DS-specific, no direct supervisor-assignment analog)* | P3, P9 | Small hand-labeled test set + actual precision/recall/false-positive numbers; model architecture write-up | §8.3.1 Model Architecture, §8.3.2 (validates pipeline), real numbers for §9 | 🟡 Partly done: ../evaluation/TEST_SET.csv (40 entries), ../evaluation/MODEL_ARCHITECTURE.md, and real rule-based results (Revision 2: precision 87.5%, rule-tier recall 100%, FPR 3.85%). Context-aware results are still pending, and the model choice is under review (see Increment 16) | **High**: this is the actual research contribution |
| 9 | UI Mockups & Prototype Evidence | P1, P9 | Annotated wireframes/screenshots — now including registration, login, email verification, password reset, profile management, conversation history view, and the admin panel (account list, suspend/reinstate, audit log view) | §5 Prototypes and Mockups (25 marks), §8.1.1 UI Design, §8.3.3 Data Visualisation Mockups | ⬜ Not started | High |
| 10 | Agile Backlog & Sprint Plan *("Assignment 6")* | — | AGILE_BACKLOG.md, SPRINT_PLAN.md | *Process-only.* Not a Template section. Supervisor-facing evidence of method. | ⬜ Not started | Low |
| 11 | GitHub Kanban Board *("Assignment 7")* | — | Board screenshot, kanban_explanation.md | *Process-only.* Optionally referenced in §10.2 (Transition to Implementation). | ⬜ Not started | Low |
| 12 | Requirements Traceability Matrix (final pass) | P3, P10 | Completed §6 table linking every REQ-ID to a concrete design artefact from Increments 1–9 | §6 Requirements Traceability (20 marks) | ✅ Done: TRACEABILITY_MATRIX.md | — |
| 13 | Evaluation of Design | P6, P7, P8 | EVALUATION.md — feasibility, scalability, security risk table (now including auth/session security, encryption-at-rest, admin-boundary enforcement), project risk table | §9 Evaluation of Design | ✅ Done: ../evaluation/EVALUATION_OF_DESIGN.md | — |
| 14 | References & Appendices | — | Min. 5 academic/industry sources (Harvard/APA), Appendix A–C (diagrams, code snippets, tools table) | §11 References, §12 Appendices | 🟡 Partly done: REFERENCES.md exists; Appendices A–C have not been compiled yet | Medium |
| **16** | **Context-Aware Model Provider Switch** *(new: deployability)* | P4, P5, P7 | Replace the local Ollama/llama3.2 dependency with a hosted, low-cost LLM API so the app works once deployed and without Ollama installed. Behind a provider interface, so the screening code is not tied to a single vendor. Needs updates to ../architecture/ARCHITECTURE.md, ../evaluation/MODEL_ARCHITECTURE.md, NFR-003/NFR-008, and a privacy note: prompts now leave the machine | §3.1.3 Tech Stack, §8.3.1, §9.3 Security | ✅ Done (design and provider code): `backend/app/llm/` (Groq default, Gemini and Ollama selectable), local redaction (`backend/app/screening/redaction.py`), production privacy guard, 23 unit tests, `run_context_eval.py`. NFR-003/NFR-008 and the architecture, model, diagram and use-case docs updated. Remaining: run the context-aware evaluation with a Groq key | **High**: the evaluation run produces the research numbers |
| **17** | **Deployment-Ready Stack Revision** *(new: deployability)* | P4, P5, P6 | Replace SQLite with PostgreSQL on Supabase, custom auth with Supabase Auth, local setup script with a Docker-based deployment path; add TypeScript and shadcn/ui to the frontend. Updates to ARCHITECTURE, AUTH_DESIGN, ERD, REPOSITORY_DESIGN, SERVICE_LAYER, DOMAIN_MODEL, REQUIREMENTS (NFR-004/007/012), SPECIFICATION, EVALUATION_OF_DESIGN, TRACEABILITY_MATRIX | §3.1.3 Tech Stack, §8.1.2, §9 | ✅ Done (design) | — |
| 15 | Final Assembly & Self-Assessment | P10 | Single compiled Design Phase submission document; self-assessment checklist completed honestly | Whole document + rubric checklist (p.12 of template) | ⬜ Not started | Final gate |

---

## Open Follow-ups (tracked, not hidden)

- **Before real users (deferred Supabase settings):** the development Supabase project is set up without CAPTCHA (docs/setup/SUPABASE_SETUP.md step 4) and without custom email sending (step 5). Both can be set up for free (Cloudflare Turnstile; Resend free tier) and **must** be done before any real student registers, together with a rate-limit review, exact redirect URLs, and a separate deployed project. Until then, sign-up testing uses the developer's own email address (Supabase's built-in email only delivers to project team members).

- **Docker:** the backend `Dockerfile` (ARCHITECTURE.md, Setup & Deployment) is added only once the application runs end to end, so that any container problem is clearly separate from application problems during development.

- **Increment 2 extension:** USE_CASES.md and TEST_CASES.md still cover only FR-001 to FR-012. Use cases and test cases for FR-013 to FR-022 have not been written yet.
- **Increment 9:** the UI prototype (`src/lib/screening.ts` etc.) lives outside this repository. Its `RULE_PATTERNS` must be updated to match the Revision 2 rules in `run_rule_eval.py` (overlap priority, Luhn check, `bank_account` rule).
- **Increment 8 / 16:** get a free Groq API key, run `python run_context_eval.py`, and copy the context-aware and aggregated results into ../evaluation/EVALUATION_HARNESS_DESIGN.md §3.

## Sequencing Logic (why this order, not another)

1. **2A before 2** — no sequence diagram should be drawn (Increment 2) before we've confirmed the containers/components it depicts (Architecture) actually match the requirements we now have on paper. Drawing it first and fixing architecture later risks redoing the diagram.
2. **3 before 5** — the ERD (Increment 5) needs entities; the Domain Model/Class Diagram (Increment 3) is where entities get defined. Doing ERD first would mean inventing entities twice.
3. **8 (Model Architecture & Evaluation) is flagged High despite having no supervisor-assignment analog** — because it's the actual empirical contribution the SPECIFICATION.md research question depends on. A design phase document with a research question in §1 but no real evaluation numbers by §8.3/§9 is the single biggest credibility gap a marker would flag. This is a board override of the "mirror the supervisor's sequence" instinct, made deliberately.
4. **10 and 11 (Agile backlog, Kanban) are Low priority** — they matter for how the supervisor perceives process, and should still be done, but they earn no marks in the actual rubric (Design_Phase_Deliverables.pdf's four categories don't include agile ceremony evidence). They should not consume time that Increments 2–9 need.
5. **12 (Traceability) and 13 (Evaluation) are late** — both are cross-cutting and depend on almost everything else existing first. Attempting them early would produce a traceability matrix pointing at artefacts that don't exist yet.

---

## Rubric Coverage Check (does this backlog actually earn all 100 marks?)

| Rubric Category | Marks | Covered by |
|---|---|---|
| Design Documents (HLD + DDD) | 30 | Increments 0, 3, 6, 7 |
| Diagrams and Visual Aids (≥3 types) | 25 | Increments 0 (System/Architecture), 2 (Sequence), 4 (Flowchart), 5 (ERD) — four types produced, one more than the minimum required |
| Prototypes and Mockups | 25 | Increments 8 (model/evaluation prototype), 9 (UI mockups) |
| Requirements Traceability | 20 | Increments 1, 12 |

All four rubric categories have at least one increment producing direct evidence. No category is currently uncovered.

**Board re-check after scope expansion:** the four rubric categories above still hold — the platform expansion adds *depth* to existing categories (more entities in Design Documents, more mockups in Prototypes, more requirements in Traceability) rather than requiring a fifth category. The one real cost is **time**: Increments 4B, 4C, and the expanded versions of 5–7 and 9 are genuinely larger than originally scoped. This isn't flagged to argue against the decision already made — it's flagged so the sequencing below can be followed without quietly running out of time before September.

## Links
- [SPECIFICATION.md](SPECIFICATION.md)
- [STAKEHOLDER_ANALYSIS.md](STAKEHOLDER_ANALYSIS.md)
- [REQUIREMENTS.md](REQUIREMENTS.md)
- [../architecture/ARCHITECTURE.md](../architecture/../architecture/ARCHITECTURE.md)
- [../architecture/DOMAIN_MODEL.md](../architecture/../architecture/DOMAIN_MODEL.md)
- [../architecture/AUTH_DESIGN.md](../architecture/../architecture/AUTH_DESIGN.md)
- [../architecture/ERD.md](../architecture/../architecture/ERD.md)
- [../architecture/DATA_PIPELINE.md](../architecture/../architecture/DATA_PIPELINE.md)