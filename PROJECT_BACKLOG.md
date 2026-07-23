# PROJECT_BACKLOG.md — SentryPrompt4: Design Phase Roadmap

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
| 0 | System Specification & C4 Architecture *("Assignment 3")* | P1, P5 | README.md, SPECIFICATION.md, ARCHITECTURE.md | §1 Introduction, §2 Design Overview, §3.1 HLD, §4.1 System/Architecture Diagram | ✅ Done | — |
| 1 | Stakeholder Analysis & Requirements *("Assignment 4")* | P2, P3 | STAKEHOLDER_ANALYSIS.md, REQUIREMENTS.md | §1.1–1.3, §6 Traceability Matrix (REQ-IDs), §9.1 (feasibility inputs) | ✅ Done | — |
| **2A** | **Architecture Consistency Check** *(board gate, not a supervisor assignment)* | P5 (re-review) | Found & fixed a real contradiction (NFR-008 vs. extension purpose); identified a real gap (no offline evaluation entry point, deferred to Inc. 8) | Strengthens §3.1, §4.1; prerequisite for trusting later diagrams | ✅ Done | — |
| 2 | Use Case Modeling & Test Case Development *("Assignment 5")* | P3, P9 | USE_CASES.md (diagram + specs), TEST_CASES.md | §4.3 Sequence/Interaction Diagram (required diagram type #2), §3.1.2 Component Interactions, seeds §9 testing strategy | ⬜ Not started | High |
| 3 | Domain Model & Class Diagram *("Assignment 9")* | P3, P5 | DOMAIN_MODEL.md, CLASS_DIAGRAM.md (Mermaid) | §3.2.1 Module/Component Specifications, feeds ERD (Inc. 5) | ⬜ Not started | High |
| 4 | State & Activity Diagrams *("Assignment 8")* | P3, P9 | STATE_DIAGRAMS.md, ACTIVITY_DIAGRAMS.md | §4.2 Flowchart/Process Flow Diagram (required diagram type #3), §3.2.2 Algorithms and Logic | ⬜ Not started | Medium |
| 5 | Data Model: ERD & AI Data Pipeline *(merges App Dev §8.1.2 + AI/DS §8.3.2)* | P3, P5 | ERD.md/diagram, DATA_PIPELINE.md | §4.4 Data/ERD Diagram (required diagram type #4), §8.1.2, §8.3.2 | ⬜ Not started | High |
| 6 | Repository Layer Design *("Assignment 11")* | P5, P8 | REPOSITORY_DESIGN.md + interface stub code | §3.2.1 Module Specifications, §3.1.3 Tech Stack justification | ⬜ Not started | Medium |
| 7 | Service Layer & REST API *("Assignment 12")* | P5, P9 | SERVICE_LAYER.md, API design, OpenAPI/Swagger stub | §3.2.3 Interface Specifications, §8.4.2 (optional, Web Tech cross-reference), prototype evidence (§5) | ⬜ Not started | Medium |
| 8 | Model Architecture & Evaluation Run *(AI/DS-specific, no direct supervisor-assignment analog)* | P3, P9 | Small hand-labeled test set + actual precision/recall/false-positive numbers; model architecture write-up | §8.3.1 Model Architecture, §8.3.2 (validates pipeline), real numbers for §9 | ⬜ Not started | **High — this is the actual research contribution** |
| 9 | UI Mockups & Prototype Evidence | P1, P9 | Annotated wireframes/screenshots of web app + extension; dashboard mockup for evaluation results | §5 Prototypes and Mockups (25 marks), §8.1.1 UI Design, §8.3.3 Data Visualisation Mockups | ⬜ Not started | High |
| 10 | Agile Backlog & Sprint Plan *("Assignment 6")* | — | AGILE_BACKLOG.md, SPRINT_PLAN.md | *Process-only.* Not a Template section. Supervisor-facing evidence of method. | ⬜ Not started | Low |
| 11 | GitHub Kanban Board *("Assignment 7")* | — | Board screenshot, kanban_explanation.md | *Process-only.* Optionally referenced in §10.2 (Transition to Implementation). | ⬜ Not started | Low |
| 12 | Requirements Traceability Matrix (final pass) | P3, P10 | Completed §6 table linking every REQ-ID to a concrete design artefact from Increments 1–9 | §6 Requirements Traceability (20 marks) | ⬜ Not started | High — cannot start until 2–9 exist |
| 13 | Evaluation of Design | P6, P7, P8 | EVALUATION.md — feasibility, scalability, security risk table, project risk table | §9 Evaluation of Design | ⬜ Not started | High |
| 14 | References & Appendices | — | Min. 5 academic/industry sources (Harvard/APA), Appendix A–C (diagrams, code snippets, tools table) | §11 References, §12 Appendices | ⬜ Not started | Medium |
| 15 | Final Assembly & Self-Assessment | P10 | Single compiled Design Phase submission document; self-assessment checklist completed honestly | Whole document + rubric checklist (p.12 of template) | ⬜ Not started | Final gate |

---

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

## Links
- [SPECIFICATION.md](./SPECIFICATION.md)
- [STAKEHOLDER_ANALYSIS.md](./STAKEHOLDER_ANALYSIS.md)
- [REQUIREMENTS.md](./REQUIREMENTS.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
