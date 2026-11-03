# SentryPrompt4 backend

## LLM provider

The context-aware detector and the chat responses use one LLM provider, chosen
with the `LLM_PROVIDER` setting. No code changes are needed to switch.

| `LLM_PROVIDER` | Default model | Cost | Use it for |
|---|---|---|---|
| `groq` (default) | `llama-3.1-8b-instant` | Free tier (~30 requests/min) | Everything, including deployment with real students |
| `gemini` | `gemini-flash-lite-latest` | Free tier | Development and demos with made-up data only* |
| `ollama` | `llama3.2` | Free, local | Offline evaluation on a PC with Ollama installed |

\* Gemini's free tier may use prompts to improve Google's models. With
`APP_ENV=production` the backend refuses to start with Gemini unless billing is
enabled and `GEMINI_PAID_TIER=true` is set.

Before anything is sent to the provider, values found by the rule-based
detector (ID, card and account numbers, phone numbers, emails, addresses) are
replaced with placeholders such as `[REDACTED_SA_ID]`.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your free Groq key in GROQ_API_KEY
```

Get a free Groq key at https://console.groq.com, and turn on Zero Data
Retention under Settings -> Data Controls.

To switch provider, change `LLM_PROVIDER` in `.env` (for example
`LLM_PROVIDER=gemini`) and set that provider's key.

## Tests

```bash
cd backend
python -m pytest
```

## Context-aware evaluation

From the repository root, with a key set:

```bash
python run_context_eval.py
```

Results are saved to `docs/evaluation/context_eval_results_<provider>.json`.
