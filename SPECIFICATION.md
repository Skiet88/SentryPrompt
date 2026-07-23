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

Students routinely and unknowingly submit sensitive personal and institutional information to AI models through ordinary prompts — student numbers, ID numbers, medical details, financial information, disciplinary records, or confidential institutional data. No mechanism currently exists to intercept, flag, or mitigate this exposure **before** it leaves the student's device and reaches a third-party model.

This is not merely a UX gap — it is a legal exposure point. Under South Africa's **Protection of Personal Information Act (POPIA)**, institutions and, in some cases, individuals bear responsibility for how personal information is processed and disclosed. Existing commercial solutions (e.g. Casper, Preempt) are designed for enterprise data-loss-prevention contexts and are not accessible, affordable, or appropriately scoped for individual students or academic institutions.

**Core research question:** *Can a lightweight, context-aware NLP screening layer meaningfully detect and mitigate sensitive information in student-authored AI prompts before transmission, without materially disrupting the student's workflow?*

### 1.3 Individual Scope & Feasibility Justification

This project is scoped for a single-semester, individually-built research prototype, not a production system. Feasibility is supported by the following deliberate scope boundaries:

- **Single user persona** (the student) — no multi-tenant accounts, institutional admin panels, or analytics dashboards.
- **Local model backend (Ollama)** — removes dependency on paid API access, rate limits, and external infrastructure, and keeps prompt data on-device during development, which is itself consistent with the privacy-first design goal.
- **Two thin client surfaces sharing one backend service** — a web chat interface and a browser extension — rather than two independently engineered systems. Both call the same screening API, so the added client surface is a UI concern, not a duplicated architecture.
- **Screening method comparison, not a single black-box classifier** — the research contribution is a comparison between a rule-based baseline and a context-aware method, which is achievable solo because rule-based detection can be built quickly, giving a working baseline early, with the context-aware method layered on top incrementally.
- **Bounded sensitive-information taxonomy** — the project targets a defined, documented set of categories (see §3) rather than open-ended "anything sensitive," which keeps both engineering scope and evaluation scope tractable.

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

- User accounts / authentication
- Multi-model support (only Ollama-backed local models)
- Institutional admin dashboards or reporting
- Cloud deployment / multi-tenant scaling
- Training a custom model from scratch (context-aware detection may use an existing pretrained model or an LLM-as-judge call, not a model trained from zero)

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
