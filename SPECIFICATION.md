# SPECIFICATION.md

## Project Title
**SentryPrompt4** — Context-Aware NLP Screening for Sensitive Information in Higher Education AI Prompts

*(Working title — rename to match your final repo name. Alternatives considered: SafePrompt, SentryPrompt, PromptGuard.)*

---

## 1. Introduction

### 1.1 Domain
**Higher Education Technology / Data Privacy & AI Safety**

Students at higher education institutions increasingly rely on generative AI tools (ChatGPT, Claude, Gemini, and others) for academic support — drafting assignments, explaining concepts, summarizing notes, and processing personal academic data. These tools are third-party platforms with no visibility into, or control over, the sensitivity of the data a student submits. This project sits at the intersection of **Natural Language Processing**, **data privacy law (POPIA)**, and **higher education tooling**.

### 1.2 Problem Statement

Students routinely and unknowingly submit sensitive personal and institutional information to AI models through ordinary prompts — student numbers, ID numbers, medical details, financial information, disciplinary records, or confidential institutional data. Kim, Park and Lee (2024) found that more than 70% of a sample of over one million real human–LLM conversations contained personally identifiable information — this is not an edge case, but the norm. A high-profile real-world instance made the risk concrete: employees at Samsung Electronics submitted confidential source code and internal meeting notes to ChatGPT, resulting in an irreversible leak of proprietary data to a third-party provider's servers, after which Samsung banned generative AI tools outright (Bloomberg, 2023) — an extreme response that forecloses the benefits students and staff genuinely gain from these tools, rather than addressing the underlying exposure.

No mechanism currently exists to intercept, flag, or mitigate this exposure **before** it leaves the student's device and reaches a third-party model, specifically within a higher-education context.

This is not merely a UX gap — it is a legal exposure point. Under South Africa's **Protection of Personal Information Act** (Republic of South Africa, 2013), institutions bear responsibility for how personal information is processed and disclosed, yet no technical standard currently governs how students interact with third-party AI tools in a manner compliant with this legislation (Roos, 2024). Existing technical solutions — Casper (Mireshghallah et al., 2024), a prompt-sanitization system for web-based LLMs, and Preempt (Chen et al., 2025), which applies encryption and differential privacy at inference time — are valuable contributions, but neither was designed with a student user in mind, and neither accounts for the academic and institutional context in which a prompt is written. Sharma, Das and Gupta (2024) and Contextual AI Lab (2025) demonstrate that sensitivity is often determined by surrounding context rather than content in isolation — a dimension current tools do not adequately address, and the dimension this project's context-aware detector is specifically built to test.

**The gap this project addresses, directly from the approved research proposal:** no existing system has been designed specifically to detect and mitigate sensitive information in student AI prompts within a higher-education environment, using context-aware NLP that understands the academic and institutional setting of the user.

**Core research question:** *Can a lightweight, context-aware NLP screening layer meaningfully detect and mitigate sensitive information in student-authored AI prompts before transmission, without materially disrupting the student's workflow?*

**Research aim (verbatim from the approved Research Methods proposal):** to develop a context-aware NLP system capable of detecting and mitigating sensitive information in student AI prompts within higher education institutions, in order to protect student data and promote responsible AI usage.

**Research objectives and how each is addressed by this project, stated honestly rather than assumed:**

| # | Objective (from the approved proposal) | Addressed by |
|---|---|---|
| 1 | Assess the level of awareness among higher-education students regarding the risks of sharing sensitive information through AI prompts | **Not addressed by this design-phase build** — this is a survey/awareness study, distinct from the system being designed here. Noted honestly as outside this project's individual technical scope, not silently dropped. |
| 2 | Investigate the types of sensitive information students commonly include in AI prompts | Directly informs the five-category taxonomy in §3 below, and the hand-labeled `TEST_SET.csv` (40 entries spanning exactly these categories) |
| 3 | Implement mitigation mechanisms that protect students from unintentional data exposure | The screening pipeline itself (FR-001–FR-009): highlight, explain, and the edit/send-anyway/cancel decision (AUTH_DESIGN.md, working frontend prototype) |
| 4 | Propose a context-aware NLP model capable of detecting sensitive information in student AI prompts in real time | MODEL_ARCHITECTURE.md — the LLM-as-judge context-aware detector, run in parallel with the rule-based detector |

**Honest scope note:** Objective 1 is a research-methods question (student awareness, likely requiring a survey instrument and ethics clearance) that sits outside what a solo, one-semester design-and-build project can also deliver alongside Objectives 2–4. This project's system design is built to serve Objectives 2–4 directly; Objective 1 is acknowledged here rather than quietly ignored, and would be genuine future work alongside this system, not a gap in this document.

### 1.3 Individual Scope & Feasibility Justification

This project began as a single-semester, individually-built research prototype with a deliberately narrow scope. Following an Agile-driven scope review (permitted explicitly under the course's methodology, provided the project builds atop this original core rather than diverging from it), the scope was expanded to a full account-based platform: user registration, email verification, login, password reset, persistent conversation history, profile management, and an administrator panel.

**What did not change:** the research core — a rule-based detector and a context-aware detector running in parallel on every prompt, compared against a hand-labeled test set — remains the actual contribution of the project (§6). The platform expansion sits around that core, not in place of it.

**What changed, and the feasibility trade-off accepted with it:**

- **Multi-user accounts, now in scope** — registration, email verification, login/logout, password reset, and profile management are now required (see REQUIREMENTS.md FR-013–FR-018). This is a real, accepted increase in build time relative to the original single-persona design, taken on knowingly rather than underestimated.
- **Persistent conversation history, now in scope** — every approved (screened) prompt and its response are stored per-user as a `Conversation`/`Message` pair (REQUIREMENTS.md FR-019–FR-020), encrypted at rest (NFR-011). This is structurally distinct from the evaluation log, which remains content-free (NFR-009) — two data stores, two privacy postures, not a contradiction.
- **An administrator role and panel, now in scope** — account-level management (status, verification, suspension) and an immutable audit log (FR-021–FR-022), deliberately excluding admin access to the *content* of any user's conversations (NFR-013), preserving the project's own privacy principle even internally.
- **Local model backend (Ollama)** — unchanged; still removes dependency on paid API access and keeps model inference on-device.
- **Two thin client surfaces sharing one backend service** — unchanged in principle; the backend now also carries the auth/account/admin services, still as a single shared service rather than duplicated per client.
- **Screening method comparison, not a single black-box classifier** — unchanged; still the core research question and still achievable solo, independent of the account-layer work around it.

**Honest risk accepted:** the account/auth/admin layer is a materially larger build than the original scope, on the same solo timeline. This is stated here explicitly so it can be referenced directly in the Design Phase Template's Feasibility Assessment (§9.1) rather than surfacing later as an unaddressed gap — see PROJECT_BACKLOG.md's scope-change log for the full increment-by-increment breakdown of what this added.

---

## 2. System Overview

**Analogy:** Just as a web browser (Chrome) is not the internet but the interface that mediates access to it, SentryPrompt4 is not an AI model — it is the platform layer that mediates a student's access to one. The AI model (via Ollama) exists independently; SentryPrompt4's contribution is the screening and mitigation layer sitting between the student and the model.

### 2.1 Core Flow

```
Student types prompt
   → NLP screening layer analyses it
   → Classified: Safe / Sensitive
        Safe      → forward to model
        Sensitive → warn student, show flagged content + explanation,
                     student chooses: edit / send anyway / cancel
   → (If sent) request forwarded to Ollama
   → Response returned to student
```

### 2.2 Client Surfaces

1. **Web Application** — a self-contained chat interface (own frontend, own backend) used as the primary research testbed. Full control over the round-trip, easiest to instrument for evaluation.
2. **Browser Extension** — a lightweight layer that can screen prompts typed into third-party AI platforms (e.g. the actual ChatGPT or Claude web interfaces) without requiring the student to leave their preferred tool. This directly supports the "not chasing users away from their preferred platforms" goal.

Both surfaces call the same backend **Screening Service** — this is the single source of truth for detection logic and is the actual research artifact.

---

## 3. Sensitive Information Taxonomy (Scope Boundary)

To keep detection and evaluation tractable, the system targets the following categories only:

| Category | Examples | Detection tier |
|---|---|---|
| National/Student ID numbers | SA ID number, student number | Rule-based (pattern) |
| Financial information | Bank account numbers, card numbers | Rule-based (pattern) |
| Contact/location data | Phone numbers, home addresses, email addresses | Rule-based (pattern) |
| Medical/health information | Diagnoses, medication names, mental health disclosures | Context-aware (semantic) |
| Institutional confidential data | Disciplinary case details, staff performance info, unpublished exam content | Context-aware (semantic) |

Rule-based detection handles pattern-matchable categories (structured formats). Context-aware detection is reserved for categories that require understanding meaning, not just pattern — this is also where the research comparison is most meaningful, since pattern categories are "easy mode" for any method.

---

## 4. Intervention Behaviour

**Decision:** Warn-and-let-user-decide, not hard block.

When a prompt is flagged:
1. The flagged span(s) of text are highlighted to the student.
2. A plain-language explanation is shown (what was detected, and why it's risky under POPIA/institutional policy).
3. The student chooses: **edit the prompt**, **send anyway**, or **cancel**.

This preserves student agency (a hard-block system risks being disabled or bypassed, defeating the purpose) while still creating a meaningful friction point and an educational moment — satisfying the "teach the user about risks" goal without a separate feature.

---

## 5. Out of Scope (This Iteration)

- Multi-model support (only Ollama-backed local models)
- Institutional-level analytics/reporting dashboards (the admin panel covers account management and audit logging only, not usage analytics)
- Cloud deployment / multi-tenant scaling across institutions
- Training a custom model from scratch (context-aware detection may use an existing pretrained model or an LLM-as-judge call, not a model trained from zero)
- Third-party OAuth/SSO login (email/password only, per FR-013)
- Admin access to individual users' conversation content (deliberately excluded, not deferred — see NFR-013)

*(Revision note: "User accounts / authentication" and "Institutional admin dashboards" were removed from this list following the scope expansion documented in §1.3 — they are now in scope, not out of it.)*

---

## 6. Evaluation Approach (Research Requirement)

Since this is a research assignment, not only an engineering deliverable, the prototype must support measuring:

- **Detection accuracy** (precision/recall) of rule-based vs. context-aware methods, against a small hand-labeled test set of prompts (mix of safe and sensitive, across the taxonomy above)
- **False positive rate** — over-flagging harmless prompts, which directly affects usability
- **Qualitative comparison** — cases where rule-based fails but context-aware succeeds (and vice versa), which forms the core discussion section of the research write-up

---

## Links
- [README.md](./README.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)