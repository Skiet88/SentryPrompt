# EVALUATION_OF_DESIGN.md — SentryPrompt4

**Feeds:** Design Phase Template §9 (Evaluation of Design)

---

## 9.1 Feasibility Assessment

**Technical feasibility:** the chosen stack (React/Vite/Tailwind, FastAPI, SQLite, local Ollama) supports every functional requirement designed so far — confirmed by TRACEABILITY_MATRIX.md, where every FR maps to a concrete artefact. The one open technical question is NFR-010 (2-second screening budget): the design is architecturally sound (parallel detection, no sequential bottleneck), but **has not been empirically measured**, since `llama3.2` local inference speed depends on hardware that hasn't been benchmarked yet. This is stated as an open risk (§9.4), not assumed to pass.

**Operational feasibility:** this project has **no real end users** — evaluation is self-tested only (confirmed early in this project's scope decisions) and stakeholders in STAKEHOLDER_ANALYSIS.md are representative roles, not interviewed individuals. This materially limits what can be claimed about usability (NFR-001, NFR-002) — those requirements are verified by design walkthrough, not user testing, and that limitation is stated here rather than implied to be more rigorous than it is.

**Economic feasibility:** all infrastructure is free and local (Ollama, SQLite) — no cloud costs, no paid API dependency. The only real cost is time, addressed directly below.

**Honest feasibility risk, stated plainly:** the project's scope expanded mid-semester from a single-user research prototype (7 entities) to a full account-based platform (14 entities) — documented in PROJECT_BACKLOG.md's scope-change log. This was a deliberate, informed decision (Assignment 4's Agile-update allowance was confirmed to permit it), but it is a genuinely larger build on the same solo timeline, and that trade-off is carried into the risk table below rather than hidden.

---

## 9.2 Scalability Considerations

This prototype explicitly targets **single-user local load** (NFR-007), not concurrent multi-user scale — stated directly in REQUIREMENTS.md rather than left ambiguous. That said, the architecture does not preclude scaling later:

- The **NLP Screening Service is its own Container** (ARCHITECTURE.md), separable from the Backend API — it could be deployed as an independent service without a redesign if concurrent load were ever required.
- The **Repository pattern's Factory abstraction** (REPOSITORY_DESIGN.md §4) means swapping SQLite for a production database requires no change to the Service Layer above it.
- **What would NOT scale as-is:** the Evaluation Log Store (SQLite/JSON file) and the local Ollama instance are both single-machine-appropriate choices; concurrent multi-user load would require both to move to shared infrastructure, which is explicitly out of scope for this iteration (SPECIFICATION.md §5).

---

## 9.3 Security Considerations

| Security Risk | Likelihood | Design-Level Mitigation |
|---|---|---|
| SQL injection against the application database | Low | FastAPI + parameterized queries/ORM (SQLAlchemy) by convention; no raw string-concatenated SQL designed anywhere in SERVICE_LAYER.md |
| Unauthorized access to another user's conversation history | Medium | `ConversationRepository`/`MessageRepository` calls scoped by `userId`; API endpoints marked "owner only" in SERVICE_LAYER.md §2 — **not yet verified by a dedicated test case**, flagged as a gap |
| Admin role escalation / privilege misuse | Low | `AdminService` structurally excludes any conversation-content dependency (NFR-013) — even a compromised admin session cannot read message content through this service, because the capability doesn't exist in the class |
| Data interception in transit | Medium | HTTPS assumed for all client-API traffic; **not yet explicitly documented as a build requirement** — flagged as a gap to close before implementation, not assumed |
| LLM-as-judge prompt injection (a student crafting a prompt to manipulate the context-aware detector's classification) | Medium | Not currently mitigated in MODEL_ARCHITECTURE.md — the fixed system prompt reduces but does not eliminate this risk; stated here as a known, unresolved limitation of the LLM-as-judge approach |
| Browser extension fails open on third-party platform DOM changes (UC2 known limitation) | Medium | Explicitly documented as unresolved in USE_CASES.md; no mitigation designed yet beyond awareness |
| Password/session compromise | Low | bcrypt/Argon2 hashing (NFR-012); session tokens invalidated server-side on logout (FR-016) |

---

## 9.4 Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| Solo timeline cannot absorb the full-platform scope expansion before submission | Medium | High | PROJECT_BACKLOG.md sequences work by dependency, not just supervisor-preferred order, and explicitly deprioritizes process-only increments (Agile backlog, Kanban board) that earn no rubric marks, to protect time for increments that do |
| NFR-010's 2-second performance budget is unverified and may fail on typical hardware | Medium | Medium | Benchmark `llama3.2` inference time as the first concrete step of implementation, before building further UI around an unconfirmed latency assumption |
| Extension fails open on third-party platform DOM changes, allowing an unscreened prompt through | Medium | High (defeats the extension's entire purpose for that session) | Documented as a known limitation now; a future mitigation (e.g. a "fail closed" fallback that blocks submission entirely if interception cannot be confirmed) is noted as future work, not designed yet — stated honestly as unresolved rather than assumed away |
| Self-tested-only evaluation limits how strongly usability and real-world detection accuracy claims can be made | High (already true) | Medium | Stated explicitly in §9.1 and in STAKEHOLDER_ANALYSIS.md rather than overclaimed; findings will be framed as "under self-testing conditions," not generalized to real student populations |
| LLM-as-judge output can fail to parse as valid JSON, silently degrading recall if not tracked separately | Medium | Medium | MODEL_ARCHITECTURE.md §4 already specifies that parse failures are logged and reported as their own metric, not folded into the recall number where they'd be invisible |

---

## Links
- [TRACEABILITY_MATRIX.md](./TRACEABILITY_MATRIX.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [MODEL_ARCHITECTURE.md](./MODEL_ARCHITECTURE.md)
- [PROJECT_BACKLOG.md](./PROJECT_BACKLOG.md)