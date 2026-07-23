# SentryPrompt4

**Context-Aware NLP Screening for Sensitive Information in Higher Education AI Prompts**

## Introduction

SentryPrompt4 is a research prototype that screens student-authored prompts for sensitive personal and institutional information *before* they reach an AI model. Students increasingly use tools like ChatGPT, Claude, and Gemini for academic work, often without realizing they've included personal identifiers, medical details, or confidential institutional data in a prompt. Under South Africa's POPIA legislation, this creates real legal exposure — and no lightweight, student-facing tool currently exists to prevent it.

SentryPrompt4 sits between the student and the AI model, the way a browser sits between a user and the internet: it does not replace the model, it mediates access to it. It screens each prompt using a combination of rule-based pattern detection and a context-aware NLP method, warns the student when something sensitive is detected, explains why, and lets the student decide how to proceed — edit, send anyway, or cancel.

Following an Agile-driven scope review, the project was expanded from a single-user research prototype to a full account-based platform — registration, email verification, login, password reset, persistent conversation history, and an administrator panel — built around the same screening core rather than in place of it. See [SPECIFICATION.md](./SPECIFICATION.md) §1.3 for the full justification and accepted feasibility trade-off.

Once complete, this project will provide:
- A working chat web application with built-in prompt screening, connected to a local Ollama model
- A companion browser extension that screens prompts typed into existing AI platforms, without requiring students to abandon their preferred tools
- A research comparison between rule-based and context-aware detection methods, evaluated on precision, recall, and false-positive rate

## Documentation

- [SPECIFICATION.md](./SPECIFICATION.md) — full problem statement, domain, scope, sensitive-information taxonomy, and evaluation approach
- [ARCHITECTURE.md](./ARCHITECTURE.md) — C4 architectural diagrams (Context, Container, Component) covering all end-to-end system components
- [STAKEHOLDER_ANALYSIS.md](./STAKEHOLDER_ANALYSIS.md) — stakeholder roles, concerns, and success metrics
- [REQUIREMENTS.md](./REQUIREMENTS.md) — functional and non-functional requirements, traced to stakeholders and architecture
- [DOMAIN_MODEL.md](./DOMAIN_MODEL.md) — domain entities and class diagram (research core + platform layer)
- [AUTH_DESIGN.md](./AUTH_DESIGN.md) — registration, verification, login, and password reset flows; session handling; admin-panel access boundary
- [ERD.md](./ERD.md) — entity-relationship diagram and schema notes for all 14 domain entities
- [DATA_PIPELINE.md](./DATA_PIPELINE.md) — live vs. offline-evaluation data flow, kept structurally independent
- [USE_CASES.md](./USE_CASES.md) — actors and use case specifications for the screening flow
- [TEST_CASES.md](./TEST_CASES.md) — functional and non-functional test cases, with a requirement coverage matrix
- [PROJECT_BACKLOG.md](./PROJECT_BACKLOG.md) — design-phase roadmap, increment status, and rubric coverage tracking

## Status

🚧 In active development — design phase in progress. See [PROJECT_BACKLOG.md](./PROJECT_BACKLOG.md) for current increment status.

**Known gaps (tracked, not hidden):**
- USE_CASES.md and TEST_CASES.md currently cover only the original screening-flow requirements (FR-001–FR-012). The platform-layer requirements added under the scope expansion (FR-013–FR-022 — registration, login, password reset, conversation history, admin actions) do not yet have corresponding use cases or test cases.
- AUTH_DESIGN.md covers registration, verification, login, logout, and password reset (FR-013–FR-017), plus the admin-panel access boundary (FR-021). Profile management (FR-018), conversation/account deletion (FR-020), and the right-to-erasure requirement (NFR-014) are simpler CRUD-style flows deferred to a short follow-up.
- ERD.md and DATA_PIPELINE.md cover the schema and data flow for all 14 entities, but the exact deletion/cascade behavior for account erasure (which rows get removed, in what order) is deferred alongside the same FR-018/FR-020/NFR-014 follow-up above.

Both are tracked in PROJECT_BACKLOG.md.