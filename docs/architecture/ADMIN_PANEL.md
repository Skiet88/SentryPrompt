# ADMIN_PANEL.md — SentryPrompt4

**Increment:** 4C — Admin Panel Design (closes the item PROJECT_BACKLOG.md previously listed as ⬜ Not started)
**Traces to:** FR-021, FR-022, NFR-013 (../requirements/REQUIREMENTS.md); `AdminService` (SERVICE_LAYER.md §1); `AdminAuditLog` entity (DOMAIN_MODEL.md §5); the admin access-boundary table (AUTH_DESIGN.md §6); the suspend/reinstate activity diagram (../diagrams/ACTIVITY_DIAGRAMS.md §8)
**Feeds:** Design Phase Template §8.1.1 (UI Design — admin screens), §3.2.1 (Module Decomposition)

**Scope note:** this document does not introduce new architecture. Every decision below was already implied across AUTH_DESIGN.md, SERVICE_LAYER.md, DOMAIN_MODEL.md, and ACTIVITY_DIAGRAMS.md — this is the consolidated admin-panel-specific write-up those documents pointed to but never assembled in one place, closing the Increment 4C gap PROJECT_BACKLOG.md named explicitly.

---

## 1. Purpose and Scope

The Admin Panel is a **deliberately thin** account-management surface. It exists to satisfy FR-021 (account management panel) and FR-022 (immutable audit log) — nothing more. It is not an analytics dashboard, not a support/helpdesk tool, and structurally cannot view conversation content (NFR-013). This narrowness is a repeated design decision across the codebase (see SERVICE_LAYER.md's board note on `AdminService`), not an oversight here.

**In scope:** view account list (status, verification state), suspend an account, reinstate an account, view the audit log of those actions.
**Explicitly out of scope (per REQUIREMENTS.md §5 / NFR-013):** viewing any user's conversations or messages, usage analytics, institutional reporting dashboards.

---

## 2. Use Cases (admin-specific, extending USE_CASES.md's UC9/UC10)

| Use case | Actor | Traces to |
|---|---|---|
| View user accounts list | System Administrator | FR-021 |
| Suspend a user account | System Administrator | FR-021, FR-022 |
| Reinstate a suspended account | System Administrator | FR-021, FR-022 |
| View audit log | System Administrator | FR-022, UC9 |

These are deliberately simple CRUD-adjacent actions on a single entity (`User.status`) plus one append-only log read — consistent with why REPOSITORY_DESIGN.md didn't need a fully bespoke repository pattern for this layer beyond `UserRepository` and `AdminAuditLogRepository`, both already specified.

---

## 3. UI Design

The prototype (see Design Phase Template §5 screenshot evidence) implements this as two stacked sections on a single `/admin` route, gated to `User.role == 'admin'`:

1. **User accounts table** — columns: name, email, status (badge), action button (Suspend/Reinstate, context-sensitive on current status).
2. **Audit log table** — columns: timestamp, admin, target, action. Read-only, no edit/delete affordance rendered anywhere in the UI, matching `AdminAuditLogRepository`'s deliberate omission of `delete()`/`update()` (REPOSITORY_DESIGN.md §2).

**Design rationale for a single-page, two-table layout instead of a multi-page admin section:** the panel's entire functional surface is two entities (`User` status and `AdminAuditLog`) — a multi-page IA would add navigation overhead without adding capability, and would risk implying a broader feature set than FR-021/FR-022 actually specify.

A visible header badge (`ADMIN · ACCOUNT-LEVEL VISIBILITY ONLY (NFR-013)`) is rendered directly in the UI itself, not just in documentation — making the design boundary visible to anyone using the panel, not only to someone reading this document.

---

## 4. Access Boundary (restated as an enforceable UI-level rule, not just a backend one)

AUTH_DESIGN.md §6 already establishes that every admin endpoint checks `User.role == 'admin'` server-side. This document adds the corresponding UI-level rule: **no component, route, or state object in the Admin Panel ever holds a `Conversation` or `Message` value.** This isn't a rendering choice (e.g. "we just don't display it") — the admin panel's data-fetching layer only ever calls `GET /api/admin/users` and `GET /api/admin/audit-log` (SERVICE_LAYER.md §2), neither of which returns conversation content. There is no client-side object to accidentally expose, mirroring the same "the capability doesn't exist" pattern already used for `AdminService`'s dependency injection.

| Admin panel screen | Reads | Explicitly cannot fetch |
|---|---|---|
| User accounts table | `GET /api/admin/users` → `User.status`, `User.emailVerified` | `Conversation`, `Message` (no endpoint exists to request them) |
| Audit log table | `GET /api/admin/audit-log` → `AdminAuditLog` | `Conversation`, `Message` |

---

## 5. Suspend / Reinstate Flow (UI-level restatement of ACTIVITY_DIAGRAMS.md §8)

1. Admin selects a target user from the accounts table.
2. Admin clicks the context-sensitive action button (`Suspend` if currently active, `Reinstate` if currently suspended).
3. Request sent to the corresponding endpoint (`POST /api/admin/users/{id}/suspend` or `/reinstate`).
4. Backend sets `User.status` and writes one `AdminAuditLog` entry **atomically with** the status change (AUTH_DESIGN.md §6 — not a best-effort afterthought log call).
5. On suspend, all active `Session` rows for that user are invalidated server-side (STATE_DIAGRAMS.md §3 — a suspended account should not retain a live session).
6. Panel table refreshes to reflect the new status; audit log table gains one new row.

**Screenshot evidence:** the captured `/admin` prototype screenshot shows the account table (one seeded student account, status `ACTIVE`, with a `Suspend` action) and an empty audit log table (`No actions recorded yet`) — an honest reflection of a freshly seeded prototype where no admin action has been performed yet, not a missing feature.

---

## 6. What This Document Does Not Cover

- **Admin account creation/promotion** — how a `User.role` becomes `admin` in the first place is not specified here. At this design phase, the prototype assumes a seeded demo admin account (`admin@sentryprompt.dev`, visible on the landing page) rather than a self-service admin-promotion flow, which is out of scope for a solo capstone prototype.
- **Bulk actions** (e.g. suspend multiple accounts at once) — not required by FR-021 as written, not designed here.
- **Audit log filtering/search** — the current design is a flat, reverse-chronological table sufficient for FR-022's requirement; pagination/filtering would be a build-phase refinement once real usage volume exists, not a design-phase requirement.

## Links
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
- [AUTH_DESIGN.md](AUTH_DESIGN.md)
- [SERVICE_LAYER.md](SERVICE_LAYER.md)
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- [../diagrams/ACTIVITY_DIAGRAMS.md](../diagrams/../diagrams/ACTIVITY_DIAGRAMS.md)
- [../requirements/USE_CASES.md](../requirements/../requirements/USE_CASES.md)
- [../requirements/PROJECT_BACKLOG.md](../requirements/../requirements/PROJECT_BACKLOG.md)
