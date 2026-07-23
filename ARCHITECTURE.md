# ARCHITECTURE.md

## Project Title
**SentryPrompt4** — Context-Aware NLP Screening for Sensitive Information in Higher Education AI Prompts

## Domain
Higher Education Technology / Data Privacy & AI Safety — see [SPECIFICATION.md](./SPECIFICATION.md) for full domain description.

## Problem Statement
Students unknowingly expose sensitive personal and institutional data in AI prompts, with no interception mechanism in place before transmission to a third-party model. See [SPECIFICATION.md](./SPECIFICATION.md) for the complete problem statement and POPIA context.

## Individual Scope & Feasibility
Research prototype expanded to a full account-based platform (registration, login, persistent conversation history, admin panel) alongside the core screening research; one shared backend consumed by two thin client surfaces (web app, browser extension); local Ollama backend removes external infrastructure dependency. See [SPECIFICATION.md](./SPECIFICATION.md) §1.3 for full justification and the accepted feasibility trade-off.

---

## C4 Model

This project follows the [C4 model](https://c4model.com/): Context → Containers → Components, going from the broadest system view down to internal design.

### Level 1: System Context Diagram

Shows SentryPrompt4 as a single system in relation to its users and external dependencies.

```mermaid
C4Context
    title System Context Diagram — SentryPrompt4

    Person(student, "Student", "A higher education student using AI tools for academic support")

    System(promptshield, "SentryPrompt4", "Screens student prompts for sensitive information before they reach an AI model, and warns/mitigates as needed")

    System_Ext(ollama, "Ollama (Local LLM)", "Locally-hosted language model that generates responses to approved prompts")
    System_Ext(thirdparty, "Third-Party AI Platform", "e.g. ChatGPT / Claude / Gemini web interface — screened via the browser extension, not replaced by it")

    Rel(student, promptshield, "Types prompts into, reads warnings and responses from")
    Rel(promptshield, ollama, "Forwards approved prompts to, receives generated responses from")
    Rel(promptshield, thirdparty, "Screens prompts destined for, via browser extension injection")
```

**Key point for this diagram:** SentryPrompt4 does not replace the AI model or the student's preferred platform — it mediates access to them, consistent with the "browser vs. internet" analogy in the specification.

---

### Level 2: Container Diagram

Shows the major deployable/runnable units inside SentryPrompt4 and how they communicate. Both client surfaces are thin — all screening logic lives once, in the Screening Service.

```mermaid
C4Container
    title Container Diagram — SentryPrompt4

    Person(student, "Student", "End user")
    Person(admin, "System Administrator", "Manages accounts, does not access conversation content")

    System_Boundary(promptshield, "SentryPrompt4") {
        Container(webapp, "Web Chat Application", "React / HTML+JS", "Self-contained chat interface; also hosts login, registration, profile, and conversation history screens")
        Container(extension, "Browser Extension", "JavaScript, browser extension APIs", "Injects screening into existing AI platform interfaces (ChatGPT, Claude, etc.)")
        Container(adminui, "Admin Panel", "React / HTML+JS", "Account-level management UI: view/suspend/reinstate users, view audit log. No access to conversation content.")
        Container(api, "Backend API", "Node.js / Python (FastAPI or Express)", "Receives prompts and account requests, orchestrates screening and auth, forwards approved prompts to Ollama")
        Container(authsvc, "Auth Service", "Node.js / Python module", "Handles registration, email verification, login/session, password reset, and enforces the admin content-access boundary (NFR-013)")
        Container(screening, "NLP Screening Service", "Python", "Core research artifact: rule-based detector + context-aware detector, returns classification and flagged spans")
        ContainerDb(appdb, "Application Database", "PostgreSQL / SQLite", "Persists User, Session, Conversation, Message (encrypted), and AdminAuditLog records")
        ContainerDb(logstore, "Evaluation Log Store", "SQLite / JSON file", "Stores anonymized, content-free flagged/unflagged prompt records for accuracy evaluation — deliberately separate from appdb (NFR-009)")
    }

    System_Ext(ollama, "Ollama (Local LLM)", "Generates responses to approved prompts")
    System_Ext(thirdparty, "Third-Party AI Platform", "Existing AI chat interface in the browser")
    System_Ext(emailsvc, "Email Delivery", "SMTP/local mail relay for verification and password-reset emails")

    Rel(student, webapp, "Uses — chat, account, and history features")
    Rel(student, extension, "Uses, while browsing")
    Rel(admin, adminui, "Uses — account management only")
    Rel(extension, thirdparty, "Reads/intercepts prompt text typed into")

    Rel(webapp, api, "Sends prompt / account / history requests", "HTTPS/JSON")
    Rel(extension, api, "Sends prompt for screening", "HTTPS/JSON")
    Rel(adminui, api, "Sends account management requests", "HTTPS/JSON")

    Rel(api, authsvc, "Delegates registration/login/session/reset to", "internal call")
    Rel(authsvc, appdb, "Reads/writes User, Session, token records")
    Rel(authsvc, emailsvc, "Sends verification and reset emails via")

    Rel(api, screening, "Requests classification of prompt text", "internal call")
    Rel(api, ollama, "Forwards approved prompt to", "HTTP (local)")
    Rel(api, appdb, "Writes approved prompt/response as Message, within a Conversation")
    Rel(api, logstore, "Writes content-free screening result record to")
    Rel(api, webapp, "Returns response / account / history data to")
    Rel(api, extension, "Returns screening result to")
```

**Design note:** Because both client surfaces still call the same Backend API and Screening Service, the platform expansion adds two new containers (Auth Service, Admin Panel) and a database, but does not duplicate the research logic — the screening pipeline is unchanged and remains the single source of truth for detection, exactly as before.

---

### Level 3: Component Diagram — NLP Screening Service

Zooms into the Screening Service, which is the actual research contribution of the project.

```mermaid
C4Component
    title Component Diagram — NLP Screening Service

    Container_Boundary(screening, "NLP Screening Service") {
        Component(preprocessor, "Text Preprocessor", "Python", "Tokenizes and normalizes incoming prompt text")
        Component(ruleengine, "Rule-Based Detector", "Regex / pattern rules", "Detects structured PII: ID numbers, phone numbers, bank details, emails")
        Component(contextdetector, "Context-Aware Detector", "Pretrained NLP model or LLM-as-judge via Ollama", "Detects semantic categories: medical disclosures, institutional confidential content")
        Component(aggregator, "Decision Aggregator", "Python", "Combines rule-based + context-aware results into a single classification with confidence and flagged spans")
        Component(explainer, "Explanation Generator", "Python (template-based)", "Produces plain-language explanation of why a span was flagged, shown to the student")
    }

    Container(api, "Backend API", "Node.js / Python", "Calls the screening service and returns results to the client")
    System_Ext(ollama, "Ollama (Local LLM)", "Used by context-aware detector as an LLM-as-judge, and separately for approved-prompt responses")

    Rel(api, preprocessor, "Sends raw prompt text to")
    Rel(preprocessor, ruleengine, "Passes normalized text to")
    Rel(preprocessor, contextdetector, "Passes normalized text to")
    Rel(contextdetector, ollama, "May query for semantic classification", "local HTTP call")
    Rel(ruleengine, aggregator, "Sends pattern matches to")
    Rel(contextdetector, aggregator, "Sends semantic matches to")
    Rel(aggregator, explainer, "Sends flagged spans to")
    Rel(explainer, api, "Returns classification + explanation to")
```

**Research note:** The Rule-Based Detector and Context-Aware Detector run independently and both feed the Decision Aggregator. This is intentional — running both on every prompt (rather than only falling back to context-aware when rules miss) is what enables the precision/recall comparison described in SPECIFICATION.md §6.

**Gap closed from Increment 2A:** the original diagram had only one entry point into the Screening Service (via the live Backend API), but FR-012 requires evaluation to run independent of live usage. An **Evaluation Harness** (a standalone script, not shown as a separate C4 component since it is a research tool rather than a deployable service) calls the Screening Service's `preprocessor` directly using the same interface the Backend API uses, bypassing `api`, `webapp`, and `extension` entirely. This is the mechanism behind UC8 in USE_CASES.md.

---

## End-to-End Component Summary

| Layer | Component | Responsibility |
|---|---|---|
| Client | Web Chat Application | Primary UI — chat, login/registration, profile, conversation history |
| Client | Browser Extension | Screens prompts on third-party AI platforms in place |
| Client | Admin Panel | Account-level management UI; no conversation-content access |
| Service | Backend API | Orchestration, routing between clients, screening, auth, and Ollama |
| Service | Auth Service | Registration, verification, login/session, password reset |
| Service | NLP Screening Service | Core research logic — detection, aggregation, explanation |
| Data | Application Database | Persists User/Session/Conversation/Message (encrypted)/AdminAuditLog |
| Data | Evaluation Log Store | Content-free, supports accuracy/false-positive evaluation — deliberately separate from Application Database |
| External | Ollama | Local LLM — generates responses to approved prompts |
| External | Third-Party AI Platform | Existing tool the extension screens prompts for, without replacing it |
| External | Email Delivery | Sends verification and password-reset emails |

## Links
- [README.md](./README.md)
- [SPECIFICATION.md](./SPECIFICATION.md)