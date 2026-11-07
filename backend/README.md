# SentryPrompt4 backend

Python (FastAPI) backend. The design rules every file follows are in the
repository's `CLAUDE.md` (SOLID, layered packages, factories, interfaces).

## Package layout

| Package | Responsibility |
|---|---|
| `app/domain/` | Immutable entities and value objects; no I/O, no framework imports |
| `app/factory/` | The only place entities are created; each factory validates its input |
| `app/util/` | Small stateless helpers (input validation) |
| `app/repository/` | Storage interfaces and implementations *(step 5)* |
| `app/service/` | Business rules, depending on repository interfaces *(step 3 onward)* |
| `app/screening/` | Research core: detectors, reply parsing, prompt templates, redaction |
| `app/llm/` | `LLMProvider` interface (Strategy), self-registering providers, provider factory, training-data policy |
| `app/api/` | FastAPI routers: HTTP in, service call, HTTP out |
| `app/schemas/` | Pydantic request/response models (DTOs) |
| `app/config/` | Settings and dependency providers |
| `app/exception/` | Exception hierarchy and the single HTTP error handler |
| `app/main.py` | Application factory; wires dependencies |

`tests/` mirrors `app/`.

## LLM provider

Chosen with the `LLM_PROVIDER` setting; switching needs no code changes.

| `LLM_PROVIDER` | Default model | Cost | Use it for |
|---|---|---|---|
| `groq` (default) | `openai/gpt-oss-20b` | Free tier | Everything, including deployment with real students |
| `gemini` | `gemini-flash-lite-latest` | Free tier | Development and demos with made-up data only* |
| `ollama` | `llama3.2` | Free, local | Offline evaluation on a PC with Ollama installed |

\* Gemini's free tier may use prompts to improve Google's models. With
`APP_ENV=production` the backend refuses to start with Gemini unless billing is
enabled and `GEMINI_PAID_TIER=true` is set (`TrainingDataPolicy`).

To add a provider, add a module in `app/llm/providers/` with a class that
extends `LLMProvider` and is decorated with `@provider_registry.register`.
No existing file needs to change.

Before anything is sent to the provider, values found by the rule-based
detector (ID, card and account numbers, phone numbers, emails, addresses) are
replaced with placeholders such as `[REDACTED_SA_ID]`.

## Detection rules (NFR-005)

The rule-based categories and their regex patterns are data, in
`app/screening/rules/detection_categories.json`. Categories are listed in
priority order: when two matches overlap, the category listed first wins. Each
category's `description` is the plain-language explanation shown to students
(FR-006), so write it for someone with no legal or privacy background.

- **Add a pattern:** add an entry to a category's `patterns` list (`id`,
  `regex`, `description`, optional `validator`).
- **Add a validator** (an extra check on a match, like `luhn`): add a class in
  `app/screening/rules/match_validators.py` decorated with
  `@validator_registry.register`.
- **Every regex must be safe from catastrophic backtracking (ReDoS):** bound
  repetitions (`{0,3}`, not `*`) wherever they can repeat. The test
  `tests/screening/rules/test_redos.py` times every pattern on attack input and
  fails the build if one is too slow.
- After changing rules, run `python run_rule_eval.py` from the repository root
  and update the published results if they change.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync                    # creates .venv and installs dependencies
cp .env.example .env       # then put your free Groq key in GROQ_API_KEY
uv run fastapi dev app/main.py
```

Get a free Groq key at https://console.groq.com, and turn on Zero Data
Retention under Settings -> Data Controls. Check http://localhost:8000/health
and the interactive API docs at http://localhost:8000/docs.

## Database (Supabase PostgreSQL)

Set `DATABASE_URL`, `DATABASE_SSL` and `SUPABASE_URL` in `.env`
(`docs/setup/SUPABASE_SETUP.md`, steps 6 and 6B), then create or update the
tables:

```bash
uv run alembic upgrade head
```

Tables change only through migrations in `migrations/versions/`. Without
`DATABASE_URL`, development keeps screening records in memory (a warning is
logged); production refuses to start without a database.

**Database tests** (repositories, RLS on every table, append-only logs,
account-deletion cascade) need a PostgreSQL server you can create databases
on. They create and drop their own throwaway database, with stand-ins for
Supabase's `auth.users` and roles:

```bash
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres uv run pytest
```

Without `TEST_DATABASE_URL` they are skipped; GitHub Actions always runs them.
**Never point `TEST_DATABASE_URL` at your Supabase project.**

## Login (Supabase Auth)

Every endpoint except `/health` requires a login: `Authorization: Bearer
<access token>`. The backend asks Supabase to confirm each token, so a
logged-out token stops working immediately; if Supabase can't be reached the
request is refused (503), never let through. Role and status come only from
the `profiles` table.

| Endpoint | Needs |
|---|---|
| `POST /api/prompts/screen` | Verified, active account |
| `GET /api/profile` | Login (also while suspended) |
| `PUT /api/profile` | Verified, active account; only `displayName` can be changed |
| `DELETE /api/profile` | Login (also while suspended); deletes the account and all its data |

Set `SUPABASE_URL`, `SUPABASE_SECRET_KEY` and `SUPABASE_PUBLISHABLE_KEY` in
`.env` (`docs/setup/SUPABASE_SETUP.md`, step 6B).

## Chat (conversations with the AI)

| Endpoint | What it does | Needs |
|---|---|---|
| `POST /api/conversations` | Start a conversation | Verified, active account |
| `GET /api/conversations` | Your conversations, newest first | Login |
| `GET /api/conversations/{id}` | One conversation with its messages | Login, owner only |
| `DELETE /api/conversations/{id}` | Delete it and its messages | Login, owner only |
| `POST /api/conversations/{id}/messages` | Send a prompt | Verified, active account, owner only |

Sending screens the prompt on the server. If it's clean, it goes to the AI
and both messages are saved. If it's flagged or couldn't be fully checked,
the answer is `status: "needs_decision"` with the warnings, and nothing is
sent or saved. Then send it again with one of:

- `"hideFlagged": true`: every flagged detail (including health and university
  information, everywhere it appears) is replaced before the AI sees it;
  logged as `redacted`;
- `"sendAnyway": true`: override; logged as `override`;
- an edited text (screened again).

Not both flags at once (422). Values found by the rule-based detector
(ID, card and account numbers, phone numbers, emails, addresses) are always
replaced with placeholders before the AI sees the prompt, even when sent
anyway, and that redacted text is what gets stored.

A new chat is titled from its first sent prompt, after redaction (so a title
never contains a detected value); the send answer includes `conversationTitle`.

Message content and chat titles are encrypted (AES-256-GCM) before they reach the database,
with `MESSAGE_ENCRYPTION_KEY` from `.env` (generate one with
`uv run python scripts/generate_key.py`). Someone else's conversation always
answers 404, exactly like one that doesn't exist.

## Admin (account management)

| Endpoint | What it does | Needs |
|---|---|---|
| `GET /api/admin/users?page=1&perPage=50` | Accounts with role, status and verification | Admin |
| `POST /api/admin/users/{id}/suspend` | Suspend (optional `{"reason": "..."}`) | Admin; not yourself or another admin |
| `POST /api/admin/users/{id}/reinstate` | Reinstate | Admin; not yourself |
| `GET /api/admin/audit-log?limit=50&offset=0` | Admin actions, newest first | Admin |

"Admin" means a verified, active account with `role = 'admin'` in the
`profiles` table (set by hand, setup guide step 7); everyone else gets 403.
Each suspend or reinstate writes an audit entry in the same transaction as
the status change, then bans or unbans the login in Supabase. If Supabase
can't be reached, the answer has `loginBlockUpdated: false`: the backend
still blocks the account, and repeating the action retries the ban. There is
no admin route to conversations or messages (NFR-013).

## Trying the API (development)

1. Get a token for your test account (step 6C of the setup guide):

   ```bash
   uv run python scripts/dev_login.py
   ```

   The token is copied to the clipboard, not printed (`--print` shows it).

2. Open http://localhost:8000/docs, click **Authorize**, paste the token, and
   try `POST /api/prompts/screen` with
   `{"text": "My ID is 9203105800089 and I take sertraline"}`.

The token works like a password for about an hour; never share it.

## Troubleshooting

On startup (development only) the log says which model is used and whether
the provider still offers it, e.g.
`Screening: using groq model openai/gpt-oss-20b (available)`.

| Symptom | Cause | Fix |
|---|---|---|
| `contextAwareVerdict: "UNAVAILABLE"` and log `HTTP 404 model_not_found` | The provider retired the model | Set a current model in `.env` (`GROQ_MODEL`); list models in the Groq console |
| Log `HTTP 401 invalid_api_key` | Wrong or deleted key | Create a new key; put it in `.env` |
| Log `timed out after …s` | Model slower than `CONTEXT_DETECTOR_TIMEOUT_SECONDS` | Raise the timeout slightly, or use a faster model |
| `.env` change has no effect | Settings are read once at startup | Restart the server (Ctrl+C, then start again) |
| A setting has the wrong value | The same name appears twice in `.env`; the **last** one wins | Keep each setting once |
| `{"error": "configuration_error"}` | No API key set | Add the key to `.env` and restart |
| Startup error about `SUPABASE_URL` | Dashboard address or a path such as `/rest/v1` | Use only the Project URL, `https://<project>.supabase.co` |

A failed context check is never treated as clean: the prompt is marked
`UNAVAILABLE`, the student is warned, and rule-based flags still appear.

## Checks

The same checks run on GitHub on every push (`.github/workflows/backend.yml`):

```bash
cd backend
uv run pytest                    # tests
uv run ruff check .              # lint, including Bandit security rules
uv run ruff format --check .     # formatting
uv run mypy                      # strict type checking
uv run pip-audit                 # known vulnerabilities in dependencies
```

## Security behaviour

- **Fail closed:** if the context-aware check times out
  (`CONTEXT_DETECTOR_TIMEOUT_SECONDS`), errors, or returns an unreadable reply,
  its verdict is `UNAVAILABLE` and the prompt is never treated as clean.
- Security headers on every response; HSTS in production.
- Request bodies over `MAX_REQUEST_BYTES` are rejected with 413.
- Screening is rate-limited per client and in total (`SCREENING_RATE_LIMIT_*`); over the limit returns 429 with `Retry-After`.
- Validation errors (422) never echo the submitted prompt back.
- `/docs`, `/redoc` and `/openapi.json` are disabled in production.
- Every endpoint except `/health` requires a login; login checks fail closed (503) if Supabase is unreachable.
- Admin routes need an admin role from the database; every admin action is audited in the same transaction; admins have no route to conversation content.
- Message content is encrypted at rest; conversations are only reachable by their owner.
- Startup fails on unsafe settings (`*` in `CORS_ORIGINS`, non-HTTPS origins in production).
- Server errors return a generic message; details go only to the server log,
  which masks tokens and API keys.

See `../SECURITY_RULES.md` for the full rules.

## Context-aware evaluation

From the repository root, after `uv sync` and with a key in `backend/.env`:

```bash
backend/.venv/bin/python run_context_eval.py
```

Results are saved to `docs/evaluation/context_eval_results_<provider>.json`.
