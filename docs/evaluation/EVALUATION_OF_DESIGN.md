# EVALUATION_OF_DESIGN.md — SentryPrompt4

**Feeds:** Design Phase Template §9 (Evaluation of Design)

---

## 9.1 Feasibility Assessment

**Technical feasibility:** the chosen stack (React + TypeScript/Vite/Tailwind/shadcn, FastAPI, PostgreSQL and Auth on Supabase, Groq-hosted LLM via a provider interface) supports every functional requirement designed so far — confirmed by ../requirements/TRACEABILITY_MATRIX.md, where every FR maps to a concrete artefact. The one open technical question is NFR-010 (2-second screening budget): the design is architecturally sound (parallel detection, no sequential bottleneck), but **has not been empirically measured**, although moving inference to Groq's hosted API removes the dependency on local hardware speed; `run_context_eval.py` records median and maximum latency so this can be checked with real numbers. This is stated as an open risk (§9.4), not assumed to pass.

**Operational feasibility:** this project has **no real end users** — evaluation is self-tested only (confirmed early in this project's scope decisions) and stakeholders in ../requirements/STAKEHOLDER_ANALYSIS.md are representative roles, not interviewed individuals. This materially limits what can be claimed about usability (NFR-001, NFR-002) — those requirements are verified by design walkthrough, not user testing, and that limitation is stated here rather than implied to be more rigorous than it is.

**Economic feasibility:** all infrastructure is on free tiers: Supabase (2 projects, 500 MB database each), a free static host for the frontend, and Groq's free API tier for the LLM (about 30 requests per minute, well above a capstone's load). If usage ever outgrows the free tier, Groq's paid rate for Llama 3.1 8B is roughly US$0.03 per 1,000 screened messages. The only real cost is time, addressed directly below.

**Honest feasibility risk, stated plainly:** the project's scope expanded mid-semester from a single-user research prototype (7 entities) to a full account-based platform (14 entities) — documented in ../requirements/PROJECT_BACKLOG.md's scope-change log. This was a deliberate, informed decision (Assignment 4's Agile-update allowance was confirmed to permit it), but it is a genuinely larger build on the same solo timeline, and that trade-off is carried into the risk table below rather than hidden.

---

## 9.2 Scalability Considerations

The deployed system targets a **small multi-user pilot** such as a class or department (NFR-007), not institution-wide scale — stated directly in ../requirements/REQUIREMENTS.md rather than left ambiguous. That said, the architecture does not preclude scaling later:

- The **NLP Screening Service is its own Container** (../architecture/ARCHITECTURE.md), separable from the Backend API — it could be deployed as an independent service without a redesign if concurrent load were ever required.
- The **Repository pattern's Factory abstraction** (../architecture/REPOSITORY_DESIGN.md §4) means the Service Layer does not depend on where data is stored; because the database is standard PostgreSQL, it can move from Supabase to any other Postgres host by changing `DATABASE_URL`.
- **What would NOT scale as-is:** Supabase's free tier (500 MB database, projects pause after about a week without activity) and the LLM provider's free-tier rate limit (about 30 requests per minute on Groq) caps concurrent use; multi-user load would require shared log storage and a paid provider tier, which is explicitly out of scope for this iteration (../requirements/SPECIFICATION.md §5).

---

## 9.3 Security Considerations

| Security Risk | Likelihood | Design-Level Mitigation |
|---|---|---|
| SQL injection against the application database | Low | FastAPI + parameterized queries/ORM (SQLAlchemy) by convention; no raw string-concatenated SQL designed anywhere in ../architecture/SERVICE_LAYER.md |
| Unauthorized access to another user's conversation history | Medium | `ConversationRepository`/`MessageRepository` calls scoped by `userId`; API endpoints marked "owner only" in ../architecture/SERVICE_LAYER.md §2 — **not yet verified by a dedicated test case**, flagged as a gap |
| Admin role escalation / privilege misuse | Low | `AdminService` structurally excludes any conversation-content dependency (NFR-013) — even a compromised admin session cannot read message content through this service, because the capability doesn't exist in the class |
| Data interception in transit | Medium | HTTPS assumed for all client-API traffic; **not yet explicitly documented as a build requirement** — flagged as a gap to close before implementation, not assumed |
| LLM-as-judge prompt injection (a student crafting a prompt to manipulate the context-aware detector's classification) | Medium | Not currently mitigated in MODEL_../architecture/ARCHITECTURE.md — the fixed system prompt reduces but does not eliminate this risk; stated here as a known, unresolved limitation of the LLM-as-judge approach |
| Browser extension fails open on third-party platform DOM changes (UC2 known limitation) | Medium | Explicitly documented as unresolved in ../requirements/USE_CASES.md; no mitigation designed yet beyond awareness |
| Password/session compromise | Low | Password hashing and session handling delegated to Supabase Auth (NFR-012); the backend rejects tokens whose session has ended (FR-016); Row Level Security blocks direct browser access to tables (ERD.md §1A) |
| Abuse of the screening endpoint (LLM quota exhaustion, denial of service) | Medium | Medium | Per-client and global rate limits with `Retry-After` (10 and 25 requests per minute); request size limit; endpoint served only outside production until login exists |

---

## 9.4 Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|
| Solo timeline cannot absorb the full-platform scope expansion before submission | Medium | High | ../requirements/PROJECT_BACKLOG.md sequences work by dependency, not just supervisor-preferred order, and explicitly deprioritizes process-only increments (Agile backlog, Kanban board) that earn no rubric marks, to protect time for increments that do |
| NFR-010's 2-second performance budget is unverified | Medium | Medium | `run_context_eval.py` records median and maximum response time from the LLM provider; check these on the first real run, before building further UI around an unconfirmed latency assumption |
| Extension fails open on third-party platform DOM changes, allowing an unscreened prompt through | Medium | High (defeats the extension's entire purpose for that session) | Documented as a known limitation now; a future mitigation (e.g. a "fail closed" fallback that blocks submission entirely if interception cannot be confirmed) is noted as future work, not designed yet — stated honestly as unresolved rather than assumed away |
| Self-tested-only evaluation limits how strongly usability and real-world detection accuracy claims can be made | High (already true) | Medium | Stated explicitly in §9.1 and in ../requirements/STAKEHOLDER_ANALYSIS.md rather than overclaimed; findings will be framed as "under self-testing conditions," not generalized to real student populations |
| LLM-as-judge output can fail to parse as valid JSON, silently degrading recall if not tracked separately | Medium | Medium | MODEL_../architecture/ARCHITECTURE.md §4 already specifies that parse failures are logged and reported as their own metric, not folded into the recall number where they'd be invisible |
| Supabase free project pauses after about a week without activity | High | Medium | Open the project before demos and presentations; restore from the dashboard if paused; the paid tier removes pausing if the system goes into regular use |
| Supabase's built-in email sender is rate-limited and meant for testing | High | Medium | Configure a free-tier SMTP provider (e.g. Resend) in Supabase before real students register |
| Dependence on Supabase as a provider | Low | Medium | Data is standard PostgreSQL and auth tokens are standard JWTs; the database can be moved to another Postgres host, and only the auth layer would need replacing |

---

## Links
- [../requirements/TRACEABILITY_MATRIX.md](../requirements/../requirements/TRACEABILITY_MATRIX.md)
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [MODEL_../architecture/ARCHITECTURE.md](./MODEL_../architecture/ARCHITECTURE.md)
- [../requirements/PROJECT_BACKLOG.md](../requirements/../requirements/PROJECT_BACKLOG.md)