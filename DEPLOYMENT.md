# Deploying SentryPrompt4 (Render + Vercel)

This satisfies NFR-004's container-based deployment path: the backend runs
from `backend/Dockerfile` on Render, the frontend is a static Vite build on
Vercel, and both talk to the Supabase project already created
(`https://dduqmzlxpglfblusgdsa.supabase.co`).

**Every step that touches a secret happens in the Render/Vercel/Supabase
dashboards directly, on your machine — never paste a secret value into a
chat with me.** The values below are the ones you'll be asked for; where to
find each one is in `docs/setup/SUPABASE_SETUP.md` and `backend/.env.example`.

Do the steps in this order — later steps need URLs produced by earlier ones.

## 0. Run migrations against the real database (once, from your machine)

This sandbox can't reach Supabase's database port, so this step has to run
on a machine with real network access (your laptop):

```bash
cd backend
uv sync
DATABASE_URL="<your Supabase pooler connection string, Settings -> Database -> Connection string -> Transaction pooler>" \
DATABASE_SSL=require \
uv run alembic upgrade head
```

Use the **pooler** host (ends in `.pooler.supabase.com`), not
`db.<project>.supabase.co` — see `docs/setup/SUPABASE_SETUP.md` for exactly
which connection string to copy.

## 1. Deploy the backend to Render

1. Push this branch to `main` on GitHub (or merge it) — Render deploys from
   a branch, and `render.yaml` at the repo root is what it reads.
2. In the Render dashboard: **New +** → **Blueprint** → connect
   `skiet88/sentryprompt` → Render finds `render.yaml` and proposes one
   service, `sentryprompt-backend`.
3. Before the first deploy, Render will prompt for every env var marked
   `sync: false` in `render.yaml`. Fill in:
   - `DATABASE_URL` — same pooler connection string as step 0
   - `SUPABASE_SECRET_KEY` — Supabase → Project Settings → API Keys → **Secret** key
   - `SUPABASE_PUBLISHABLE_KEY` — same page, **Publishable** key
   - `MESSAGE_ENCRYPTION_KEY` — generate with `uv run python scripts/generate_key.py` and save it somewhere durable; losing it makes stored messages unreadable
   - `GROQ_API_KEY` — from console.groq.com (turn on Zero Data Retention under Settings → Data Controls first)
   - `CORS_ORIGINS` — leave as a placeholder for now (e.g. `[]`); you'll come back and set this in step 3
4. Deploy. Once live, note the backend's URL, e.g.
   `https://sentryprompt-backend.onrender.com`. Confirm it's actually up:
   `curl https://sentryprompt-backend.onrender.com/health`.

## 2. Deploy the frontend to Vercel

1. Vercel dashboard → **Add New** → **Project** → import `skiet88/sentryprompt`.
2. **Root Directory**: set to `frontend` (this is a monorepo; Vercel needs
   to build from that subfolder, where `frontend/vercel.json` lives).
3. Framework preset should auto-detect Vite. Set these environment
   variables (Project Settings → Environment Variables):
   - `VITE_API_URL` = the Render URL from step 1 (no trailing slash)
   - `VITE_SUPABASE_URL` = `https://dduqmzlxpglfblusgdsa.supabase.co`
   - `VITE_SUPABASE_PUBLISHABLE_KEY` = the same Publishable key from step 1
4. Deploy. Note the resulting URL, e.g. `https://sentryprompt.vercel.app`
   (or whatever Vercel assigns, or a custom domain if you attach one).

## 3. Close the loop: CORS and Supabase redirect URLs

1. Back in Render, edit `CORS_ORIGINS` on `sentryprompt-backend` to the
   frontend's exact origin from step 2, as a JSON list of one string, e.g.
   `["https://sentryprompt.vercel.app"]` — must be `https://`, no trailing
   slash. Save, which triggers a redeploy.
2. In Supabase → Authentication → URL Configuration, add these redirect
   URLs (mirroring what's already there for localhost):
   - `https://sentryprompt.vercel.app/auth/callback`
   - `https://sentryprompt.vercel.app/reset-password`

## 4. Create the first admin account

Register a normal account through the live frontend, verify the email,
then in Supabase → Table Editor → `profiles`, find that row and set
`role` to `admin` (`backend/README.md`, Admin section). There is no UI path
to do this — it's a one-time manual step per the design in
`docs/architecture/ADMIN_PANEL.md`.

## 5. Before presenting

Render's free plan spins down a web service after ~15 minutes of no
traffic; the next request then takes 30–60 seconds to cold-start. A few
minutes before the demo starts, hit the backend once yourself
(`curl https://sentryprompt-backend.onrender.com/health` or just open the
frontend and log in) so it's already warm when the panel is watching.

## 6. Extension (FR-010), if demonstrating it live

The extension's `config.js` (copied from `extension/config.example.js`)
needs `BACKEND_URL` and `SUPABASE_URL` pointed at the real deployed values
instead of `localhost`, and the new origins added to
`extension/manifest.json`'s `host_permissions` if they aren't already
covered — see `extension/README.md`, "Setup", step 2.

## What's deliberately not automated here

- **No CI/CD auto-deploy wired up.** Render and Vercel both auto-deploy on
  push to the connected branch once set up above, which is enough for a
  single capstone deployment; a separate GitHub Actions deploy workflow
  wasn't added since it would duplicate what both platforms already do.
- **Migrations are a manual step (0), not run automatically on deploy.**
  Render's free plan doesn't support a pre-deploy/release command, and
  running schema migrations automatically on every deploy is a real risk
  on a shared database; running them by hand, once, before the first
  deploy and whenever `migrations/versions/` changes, is the safer default.
