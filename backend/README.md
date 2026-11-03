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
| `groq` (default) | `llama-3.1-8b-instant` | Free tier (~30 requests/min) | Everything, including deployment with real students |
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
- `/docs`, `/redoc` and `/openapi.json` are disabled in production.
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
