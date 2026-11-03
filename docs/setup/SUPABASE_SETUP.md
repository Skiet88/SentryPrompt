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

## 1. Create two projects

Create one project for **development** and, later, one for the **deployed** app
(the free tier allows two active projects).

1. Sign in at https://supabase.com and click **New project**.
2. Name it, e.g. `sentryprompt-dev`.
3. Generate a strong **database password** and store it in your password manager.
   It is not needed in chat or in Git.
4. Choose the region closest to your users (for South Africa, the nearest
   available region, e.g. an EU or `af-south` region if offered).

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
- **Redirect URLs:** add only the exact pages the verification and reset links
  may return to, e.g. `http://localhost:5173/auth/callback` and
  `http://localhost:5173/reset-password`. Never use wildcards that match other
  domains (SECURITY_RULES.md §4: redirects only to allow-listed URLs).

## 4. Turn on bot protection (before real users)

**Authentication → Attack Protection** (or similar)

- Enable **CAPTCHA** (hCaptcha or Cloudflare Turnstile) for sign-up and login.
- Review **Rate Limits** for sign-ups, logins and emails; keep the defaults or
  lower them.

## 5. Configure email sending (before real users)

Supabase's built-in email sender is for testing only and heavily rate-limited.
Before real students register:

**Authentication → Emails → SMTP Settings**

- Enable custom SMTP and enter the details from a free-tier provider such as
  Resend (sender address on a domain you control).
- Optionally edit the email templates so they are clearly from SentryPrompt4.

## 6. Collect the keys and URLs (never paste them in chat)

**Project Settings → API / API Keys** and **Project Settings → Database**

| Value | Where it goes | Secret? |
|---|---|---|
| Project URL | `backend/.env` and `frontend/.env` | No |
| Publishable (anon) key | `frontend/.env` only | No: designed to be public, safe because of Row Level Security |
| Secret (service-role) key | `backend/.env` only | **Yes**: full access, backend only, never in the frontend, Git or chat |
| Database connection string | `backend/.env` (`DATABASE_URL`) | **Yes**: contains the database password |
| JWT verification (JWKS) URL | Backend config | No: public keys used to check login tokens |

`.env` files are listed in `.gitignore`, so they are never committed. In
deployment, the same values go into the hosting platform's secret settings.

The backend settings for these values are added in steps 5 and 6 of the
backend plan; until then, keep them only in your password manager.

## 7. Create the first admin (after the database tables exist)

The `profiles` table is created by the backend's database migrations
(backend plan, step 5). After that:

1. Sign up through the app with the account that should become admin, and
   verify its email.
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

- [ ] Supabase account has 2FA on
- [ ] Development project created; database password in password manager
- [ ] Confirm email on; minimum password length ≥ 10; link expiry 1 hour
- [ ] Site URL and exact redirect URLs set
- [ ] CAPTCHA and rate limits reviewed (before real users)
- [ ] Custom SMTP configured (before real users)
- [ ] Keys stored only in `.env` files / password manager
- [ ] First admin promoted (after step 5 of the backend plan)
