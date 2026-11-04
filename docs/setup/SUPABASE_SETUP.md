# SUPABASE_SETUP.md — Setting up Supabase for SentryPrompt4

Step-by-step setup of the Supabase project that provides the database and
authentication (ARCHITECTURE.md, Tech Stack Decision; AUTH_DESIGN.md §0).

Supabase occasionally renames dashboard menus. If a name below doesn't match
exactly, look for the closest equivalent; the settings themselves stay the same.

---

## Before you start: protect the dashboard

Anyone with access to the Supabase dashboard can read every table and promote
admins (AUTH_DESIGN.md §0.1), so the account itself must be protected:

- Use a unique, strong password (a password manager is ideal).
- Turn on **two-factor authentication** in your Supabase account settings.

---

## 1. Create the development project

1. Sign in at https://supabase.com and click **New project**.
2. Name it, e.g. `sentryprompt-dev`.
3. Generate a strong **database password** and store it in your password
   manager. It is needed in step 6; it is never pasted into chat or Git.
4. Choose the region closest to your users.

A second project for the **deployed** app is created later, before
deployment (the free tier allows two active projects).

Free-tier projects **pause after about a week without activity**. Open the
project before demos and presentations (EVALUATION_OF_DESIGN.md §9.4).

## 2. Require email confirmation (FR-014)

**Authentication → Sign In / Providers → Email**

- **Enable email provider:** on.
- **Confirm email:** on. Unverified accounts cannot log in (AUTH_DESIGN.md §0.1).
- **Minimum password length:** at least 10 characters.
- **Email OTP / link expiration:** 3600 seconds (1 hour) (AUTH_DESIGN.md §1).
- **Secure email change:** on (an email change must be confirmed).

## 3. Set the site and redirect URLs

**Authentication → URL Configuration**

- **Site URL:** `http://localhost:5173` for the development project; the real
  HTTPS frontend URL for the deployed project.
- **Redirect URLs:** leave empty until the frontend exists. Then add only the
  exact pages the verification and reset links may return to, e.g.
  `http://localhost:5173/auth/callback` and
  `http://localhost:5173/reset-password`. Never use wildcards that match other
  domains (SECURITY_RULES.md §4: redirects only to allow-listed URLs).

## 4. Bot protection — DEFERRED until before real users

Not needed during development. **Must be done before any real student uses
the app** (tracked in PROJECT_BACKLOG.md, Open Follow-ups).

**Authentication → Attack Protection** (or similar)

- Enable **CAPTCHA** for sign-up and login. Free options exist:
  **Cloudflare Turnstile** is free, and hCaptcha has a free plan. You create a
  site key/secret key there and paste them into Supabase.
- Review **Rate Limits** for sign-ups, logins and emails; keep the defaults or
  lower them.

## 5. Email sending — DEFERRED until before real users

Not needed during development, with one limitation: Supabase's built-in email
sender only delivers to the **email addresses of your Supabase team members**
and is heavily rate-limited. While developing, test sign-up with your own
email address.

**Must be done before any real student registers** (tracked in
PROJECT_BACKLOG.md, Open Follow-ups):

**Authentication → Emails → SMTP Settings**

- Enable custom SMTP and enter the details from an email provider.
  **Resend** has a free tier suitable for this project; it needs a sender
  address on a domain you control.
- Optionally edit the email templates so they are clearly from SentryPrompt4.

## 6. Find and save three values

In this step you only **find and save** values. Nothing goes into the project
yet: the backend starts using them in backend plan step 5 (database) and
step 6 (login), and `.env.example` will then say exactly which line gets which
value.

Save the two **secret** values in a password manager (Bitwarden is free), or
at least a private note **outside** the project folder. Never paste them into
chat, documents, screenshots, Git, or any file other than `backend/.env`.

### Value 1: Project URL (not secret)

1. Click the **gear icon (Project Settings)** at the bottom of the left menu.
2. Click **Data API** (called **API** on some projects).
3. Copy the **Project URL**, e.g. `https://abcdefgh.supabase.co`.

### Value 2: Secret key (SECRET)

1. In **Project Settings**, click **API Keys**.
2. Under **Secret keys** (`sb_secret_…`), click **Reveal**, or **Create a
   secret key** if none exists, and copy it. On older projects this is the
   **service_role** key.
3. Save it in your password manager.

This key bypasses every security rule in the database. It is only ever used
by the backend. If it leaks, delete it on the same page and create a new one.

The **Publishable key** (`sb_publishable_…`, or **anon** on older projects) on
the same page is not secret and is only needed later by the frontend; nothing
to do with it now.

### Value 3: Database connection string (SECRET)

1. Click the **Connect** button at the **top** of the project page.
2. Choose **Connection string**, then set the method to **Session pooler**.
   **Not "Direct connection":** that address (`db.<project>.supabase.co`)
   only works over IPv6, and most home and campus networks are IPv4, which
   fails with `getaddrinfo failed`. Not "Transaction pooler" either.
3. Copy the text. It must look like
   `postgresql://postgres.<project>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`:
   the user is `postgres.<project>` and the host ends in `.pooler.supabase.com`.
4. Replace `[YOUR-PASSWORD]` **including the square brackets** with the
   database password from step 1, so it reads `…:yourpassword@aws-0-…`.
   Forgotten it? **Project Settings → Database → Reset database password**.
5. Use a password of **letters and numbers only** (long, e.g. 24+
   characters). Characters such as `@ : / ? # [ ] %` must otherwise be
   URL-encoded (`@` becomes `%40`), which is easy to get wrong.
6. Save the complete string in your password manager.

### Nothing to do: JWKS URL

The backend checks login tokens using Supabase's public keys at
`https://<your-project>.supabase.co/auth/v1/.well-known/jwks.json`. It works
this address out from the Project URL; nothing needs copying.

### Where the values will go (later)

| Value | Used from | Goes into |
|---|---|---|
| Project URL | Backend plan step 5, and the frontend | `backend/.env`, later `frontend/.env` |
| Secret key | Backend plan step 6 | `backend/.env` only |
| Connection string | Backend plan step 5 | `backend/.env` only |
| Publishable key | Frontend | `frontend/.env` |

`.env` files are listed in `.gitignore`, so they are never committed. In
deployment, the same values go into the hosting platform's secret settings.

## 6B. Put the values in `backend/.env` and create the tables

Do this once the backend's database step is on your machine
(`git pull`). Only `backend/.env` receives secrets; it is never committed.

1. Open `backend/.env` (copy any new lines from `.env.example` first) and set:
   ```
   DATABASE_URL=              ← Value 3, the full connection string with your password
   DATABASE_SSL=require
   SUPABASE_URL=              ← Value 1, the Project URL
   SUPABASE_SECRET_KEY=       ← Value 2, the Secret key (sb_secret_...)
   SUPABASE_PUBLISHABLE_KEY=  ← the Publishable key (sb_publishable_...), not secret
   ```
   Also generate the key that encrypts stored messages (not a Supabase
   value) and put it in the same file:
   ```
   uv run python scripts/generate_key.py
   ```
   ```
   MESSAGE_ENCRYPTION_KEY=    ← the output of the command above (SECRET)
   ```
   Keep a copy of this key in your password manager.
   Keep each setting **once** in the file (if a name appears twice, the last
   one wins).
2. In a terminal in the `backend` folder, create the tables:
   ```
   uv run alembic upgrade head
   ```
   It prints `Running upgrade -> 0001, Initial schema` and finishes without
   errors. Running it again later is safe: it only applies new migrations.
3. Check in the Supabase dashboard: **Table Editor** now lists `profiles`,
   `conversations`, `messages` and `admin_audit_log` (schema `public`), and the
   `evaluation` tables. Each shows **RLS enabled**.
4. Restart the server. The startup log shows
   `Database: connected (schema version 0001)` and
   `Auth: Supabase reachable, secret key accepted`.

If `alembic upgrade head` fails:

| Error | Cause | Fix |
|---|---|---|
| "DATABASE_URL contains square brackets" | The `[ ]` around the password were kept | Remove them: `…:yourpassword@…` |
| `getaddrinfo failed` / host not found | Direct connection string (IPv6 only) | Use the **Session pooler** string (step 6, Value 3) |
| "password authentication failed" | Wrong password | Reset it (Project Settings → Database) and update `.env` |
| "auth.users not found" | URL points at a database that isn't your Supabase project | Copy the connection string again |

To check which server `.env` points at without showing the password, run
this in `backend`:

```
uv run python -c "from app.config.settings import Settings; from urllib.parse import urlsplit; u=urlsplit(Settings().database_url.get_secret_value()); print('host:', u.hostname, '| port:', u.port, '| user:', u.username)"
```

It should show a host ending in `.pooler.supabase.com`, port 5432 and user
`postgres.<project>`. Never paste the connection string itself anywhere: if
it is ever exposed, reset the database password.

## 6C. Test logging in (development)

The API now requires a login. Until the frontend exists, test with a token:

1. Create a test account in the dashboard: **Authentication → Users → Add
   user → Create new user**, with **your own email** and a password, and tick
   **Auto Confirm User** (so it counts as verified). Or sign up through the
   frontend later.
2. In `backend`, get a token (your password is typed but not shown):
   ```
   uv run python scripts/dev_login.py
   ```
3. Open http://localhost:8000/docs, click **Authorize**, paste the token,
   and try `GET /api/profile` and `POST /api/prompts/screen`.

The token works like a password for about an hour: don't share it, paste it
into chats or save it in files. Without a token, the API answers 401.

## 7. Create the first admin (after the database tables exist)

The `profiles` table is created in step 6B. After that:

1. Create or sign up the account that should become admin (step 6C), and
   make sure its email is verified.
2. Open **SQL Editor** in the Supabase dashboard and run, with that account's
   email:

   ```sql
   update public.profiles
   set role = 'admin'
   where id = (select id from auth.users where email = 'your-admin@example.com');
   ```

3. Check that exactly one row was updated.

There is deliberately no way to do this from inside the application
(AUTH_DESIGN.md §0.1).

## 8. Checklist

**Now (development):**
- [ ] Supabase account has 2FA on
- [ ] Development project created; database password in password manager
- [ ] Confirm email on; minimum password length ≥ 10; secure email change on
- [ ] Site URL set (redirect URLs added once the frontend exists)
- [ ] Project URL, secret key and connection string saved in password manager

**Later (backend plan step 5 onwards):**
- [ ] Values added to `backend/.env` and tables created (step 6B)
- [ ] First admin promoted (step 7 of this guide)

**Before any real student uses the app:**
- [ ] CAPTCHA enabled (step 4; Cloudflare Turnstile is free)
- [ ] Custom SMTP configured (step 5; Resend has a free tier)
- [ ] Rate limits reviewed
- [ ] Redirect URLs restricted to the real frontend
- [ ] Deployed project created (separate from development)
