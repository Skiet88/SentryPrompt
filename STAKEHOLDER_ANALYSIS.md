# STAKEHOLDER_ANALYSIS.md

**Project:** SentryPrompt4
**Scope note:** This project is a research prototype, not a deployment for a named institution. Stakeholders below are therefore **representative roles** typical of any South African higher-education institution operating under POPIA, not individuals from a specific university. This is a deliberate scoping decision, not an oversight — see Limitations in SPECIFICATION.md §1.3.

---

## Stakeholder Table

| Stakeholder | Role | Key Concerns | Pain Points | Success Metrics |
|---|---|---|---|---|
| **Student** | Primary end user; submits prompts to AI tools for academic work | Wants AI assistance without legal/privacy risk; doesn't want workflow disrupted | Unaware which information counts as "sensitive"; no visibility into what leaves their device once a prompt is sent | Reduction in prompts containing flaggable sensitive data sent unmodified; screening adds negligible delay (<2s) |
| **University Data Protection / Information Officer** (POPIA-mandated role under South African law) | Institutional compliance owner for personal information processing | Institutional liability if students leak personal/institutional data via third-party AI tools; no current policy enforcement mechanism | No visibility or control over student AI tool usage; POPIA exposure is invisible until an incident occurs | A demonstrable, documented mitigation layer exists; audit trail of flagged (not necessarily blocked) events |
| **IT Security / Systems Administrator** *(now a literal system actor — see USE_CASES.md, the System Administrator role)* | Would be responsible for deploying/maintaining the system, and now has a dedicated admin panel role within it | Attack surface of any new tool; whether it introduces new data handling risk itself; account-management burden | Concerned that a "privacy tool" could itself become a new place sensitive data is logged/stored insecurely — sharpened by the platform expansion, since it now stores real account and conversation data, not just screening metadata | Screening logic runs locally/on-prem; admin panel is account-level only, with no path to conversation content (NFR-013) — this stakeholder's core concern is answered by a design boundary, not just a policy statement |
| **Academic Staff / Lecturers** | Set assignments; increasingly must account for student AI use | Want students using AI responsibly, not want to police it manually | No tooling exists to support responsible-use policy at the point of use, only after-the-fact plagiarism checks | Tool supports responsible-use policy without requiring staff intervention per incident |
| **Ollama / Local Model Maintainers** (external dependency, not institutional) | Provider of the underlying local LLM runtime the system depends on | Indirect stakeholder — API/behavior stability affects SentryPrompt4's context-aware detector | N/A (external project, not consulted) | System degrades gracefully if local model behavior changes between versions |
| **Project Supervisor / Assessor** | Evaluates the research and engineering quality of the deliverable | Wants evidence of rigorous design process, honest scoping, defensible research method | Common capstone failure mode: overclaiming scope or skipping evaluation rigor | Design phase artifacts show traceable requirements, justified trade-offs, and an honestly bounded evaluation plan |

---

## Board Note on Representativeness

A genuine stakeholder analysis is normally built from interviews. This project's stakeholders are inferred from domain knowledge (POPIA structure, typical HE institutional roles) rather than elicited from real people, because:
1. The project is explicitly scoped as an individual research prototype, not an institutional deployment (SPECIFICATION.md §1.3, §5).
2. No real user testing is planned (see Evaluation Approach, SPECIFICATION.md §6).

This is stated openly here so it can be cited directly in Design Phase Template §9.1 (Operational Feasibility) rather than surfacing later as an unaddressed gap.

## Links
- [SPECIFICATION.md](./SPECIFICATION.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)