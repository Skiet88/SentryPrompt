# REPOSITORY_DESIGN.md — SentryPrompt4

**Traces to:** DOMAIN_MODEL.md (14 entities), ARCHITECTURE.md (stack: Python/FastAPI, PostgreSQL on Supabase via SQLAlchemy)
**Feeds:** Design Phase Template §3.2.1 (Module Specifications), §3.1.3 (Tech Stack justification)
**Scope note:** per the supervisor's own prior brief (PrevProjectAssignment.pdf, Assignment 12), a minimum of 3 entities is sufficient to demonstrate the pattern for a solo project. Below, the **generic interface applies to all 14 entities** (table in §2), but only **3 representative repositories are fully specified** (§3) — one from each meaningful category (auth/platform, product, research) — since the remaining 11 are structurally identical, and writing all 14 out in full would be repetition, not additional design work.

---

## 1. Why a Repository Layer at All

**Board note:** before designing this, worth asking the review-board question directly — does a solo, single-database prototype actually need a storage-abstraction layer? Answer: yes, for one concrete reason specific to this project, not just "best practice." The Evaluation Log Store and the Application Database (per ARCHITECTURE.md) are **deliberately separate stores with different privacy rules** (NFR-009 vs NFR-011). A repository interface per entity, rather than raw SQL scattered through service code, is what makes that boundary enforceable in code — a `ScreeningResultRepository` and a `EvaluationLogEntryRepository` simply cannot be pointed at the same table by accident if they're separate typed interfaces from the start.

---

## 2. Generic Interface (applies to all 14 entities)

```python
from typing import Protocol, TypeVar, Generic, Optional, List

T = TypeVar("T")
ID = TypeVar("ID")

class Repository(Protocol, Generic[T, ID]):
    def save(self, entity: T) -> T: ...          # Create/Update
    def find_by_id(self, id: ID) -> Optional[T]: ...
    def find_all(self) -> List[T]: ...
    def delete(self, id: ID) -> None: ...
```

Entity-specific repositories extend this with only the queries that entity actually needs — not every repository needs every generic method exposed (e.g. `EvaluationLogEntryRepository` never needs `delete()`, since NFR-009-compliant records are append-only by design; exposing delete on it would be a design smell, so it's deliberately omitted, not just unused).

| Entity | Repository | Notable deviation from generic interface |
|---|---|---|
| Prompt | *(none — transient, never persisted, see DOMAIN_MODEL.md §5)* | No repository exists for this entity, by design |
| ScreeningResult | `ScreeningResultRepository` | Adds `find_by_prompt_id()` |
| FlaggedSpan | `FlaggedSpanRepository` | Adds `find_by_result_id()` |
| DetectionCategory | `DetectionCategoryRepository` | Read-mostly; `save()` restricted to admin/config use (UC10) |
| RulePattern | `RulePatternRepository` | Adds `find_by_category_id()` |
| EvaluationLogEntry | `EvaluationLogEntryRepository` | **No `delete()` method exposed** — append-only, enforces NFR-009 at the interface level |
| TestSetEntry | `TestSetEntryRepository` | Used only by the evaluation harness (Increment 8), never by live-path services |
| User | `UserRepository` | Adds `find_by_email()` — needed for login (FR-015) |
| Session | *None (Supabase Auth)* | Stored and invalidated by Supabase Auth; no repository needed (DOMAIN_MODEL.md §6) |
| EmailVerificationToken | *None (Supabase Auth)* | As above |
| PasswordResetToken | *None (Supabase Auth)* | As above |
| Conversation | `ConversationRepository` | Adds `find_by_user_id()` |
| Message | `MessageRepository` | Adds `find_by_conversation_id()`; `save()` always writes encrypted content (NFR-011) |
| AdminAuditLog | `AdminAuditLogRepository` | **No `delete()` or `update()` — immutable by design** (FR-022) |

---

## 3. Representative Implementations (fully specified)

### 3.1 `UserRepository` (platform/auth-critical)

```python
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._storage: dict[str, User] = {}

    def save(self, user: User) -> User:
        self._storage[user.userId] = user
        return user

    def find_by_id(self, id: str) -> Optional[User]:
        return self._storage.get(id)

    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._storage.values() if u.email == email), None)

    def find_all(self) -> List[User]:
        return list(self._storage.values())

    def delete(self, id: str) -> None:
        # FR-020: account deletion. Must cascade — see Service Layer, not Repository,
        # for the cascade logic (Conversations/Messages/Sessions). A repository only
        # deletes its own table; orchestrating the cascade is a service concern.
        self._storage.pop(id, None)
```

### 3.2 `MessageRepository` (product/content-bearing — the NFR-011 encryption boundary)

```python
class InMemoryMessageRepository(MessageRepository):
    def __init__(self, encryptor: ContentEncryptor):
        self._storage: dict[str, Message] = {}
        self._encryptor = encryptor  # injected, not hardcoded — swappable for testing

    def save(self, message: Message) -> Message:
        # NFR-011 enforced here, at the repository boundary — content is encrypted
        # on the way in, never stored plaintext, regardless of what the service layer sends.
        message.content = self._encryptor.encrypt(message.content)
        self._storage[message.messageId] = message
        return message

    def find_by_conversation_id(self, conversation_id: str) -> List[Message]:
        results = [m for m in self._storage.values() if m.conversationId == conversation_id]
        return [self._decrypt_copy(m) for m in results]  # decrypt only on read, not in storage

    def _decrypt_copy(self, message: Message) -> Message:
        copy = message.model_copy()
        copy.content = self._encryptor.decrypt(copy.content)
        return copy
```

**Design decision worth stating explicitly:** encryption happens *inside* the repository, not in the service layer above it. This means it is structurally impossible for a future service method to accidentally call `save()` with unencrypted content reaching storage — the repository is the enforcement point, not a convention someone has to remember.

### 3.3 `ScreeningResultRepository` (research-critical)

```python
class InMemoryScreeningResultRepository(ScreeningResultRepository):
    def __init__(self):
        self._storage: dict[str, ScreeningResult] = {}

    def save(self, result: ScreeningResult) -> ScreeningResult:
        self._storage[result.resultId] = result
        return result

    def find_by_prompt_id(self, prompt_id: str) -> Optional[ScreeningResult]:
        return next((r for r in self._storage.values() if r.promptId == prompt_id), None)

    def find_all(self) -> List[ScreeningResult]:
        return list(self._storage.values())

    def delete(self, id: str) -> None:
        self._storage.pop(id, None)
```

---

## 3A. Implementation Note (backend plan, step 4)

The generic interface is implemented as three small capability interfaces in `backend/app/repository/base.py`: `ReadRepository` (`find_by_id`, `find_all`), `WriteRepository` (`save`) and `DeleteRepository` (`delete`). Each repository inherits only what its entity allows, so "append-only" and "immutable" are enforced by the type system: `EvaluationLogEntryRepository` inherits read and write but not delete. Methods are `async` so database-backed implementations never block the server.

`EvaluationLogEntryRepository` is the first one implemented, with an in-memory implementation (bounded to 10,000 entries) used until the database layer (step 5) adds the PostgreSQL implementation behind the same interface.

## 4. Storage Abstraction: Factory Pattern

**Choice: Factory, not raw Dependency Injection framework.** For a solo project with two backends (in-memory for tests, PostgreSQL via SQLAlchemy for real use), a full DI container (e.g. `dependency-injector`) is more machinery than the problem needs — a small factory function achieves the same swappability with a fraction of the setup.

```python
class RepositoryFactory:
    @staticmethod
    def get_user_repository(storage_type: str) -> UserRepository:
        match storage_type:
            case "MEMORY":
                return InMemoryUserRepository()
            case "POSTGRES":
                return PostgresUserRepository(database_url=settings.DATABASE_URL)  # see §5
            case _:
                raise ValueError(f"Unknown storage type: {storage_type}")
    # One factory method per repository, same pattern — omitted here for brevity,
    # not because the pattern changes per entity.
```

---

## 5. Future-Proofing Stub

**Note (stack revision):** in the implemented system, account identity lives in Supabase Auth (`auth.users`), so `UserRepository` reads and writes the `profiles` table (display name, role, status) and calls Supabase's admin API only where an auth record must change (email update, account deletion). The interface above is unchanged; only the storage behind it moved from SQLite to PostgreSQL.

```python
class PostgresUserRepository(UserRepository):
    """
    Stub only — no full implementation required at design phase.
    Demonstrates the interface is storage-agnostic: swapping InMemoryUserRepository
    for this requires no change anywhere in the Service Layer (Increment 7).
    """
    def __init__(self, database_url: str):
        self._database_url = database_url
        # real implementation creates a SQLAlchemy engine/session here

    def save(self, user: User) -> User:
        raise NotImplementedError("Implemented during build phase, not design phase")

    def find_by_id(self, id: str) -> Optional[User]:
        raise NotImplementedError("Implemented during build phase, not design phase")

    def find_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError("Implemented during build phase, not design phase")

    def find_all(self) -> List[User]:
        raise NotImplementedError("Implemented during build phase, not design phase")

    def delete(self, id: str) -> None:
        raise NotImplementedError("Implemented during build phase, not design phase")
```

## Links
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [../requirements/REQUIREMENTS.md](../requirements/../requirements/REQUIREMENTS.md)
