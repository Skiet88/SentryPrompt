# SentryPrompt4 frontend

React + TypeScript (Vite), Tailwind CSS, shadcn/ui-style components, and
Supabase Auth through `supabase-js`. The backend (`../backend`) does all
screening and enforces every rule; the frontend never decides who may do what.

## Setup

Requires Node.js 22.12 or newer.

```bash
cd frontend
npm ci                          # installs the exact locked versions
cp .env.example .env.local      # then fill in the three values
npm run dev                     # http://localhost:5173
```

| Setting | Where to find it |
|---|---|
| `VITE_API_URL` | The backend, `http://localhost:8000` in development |
| `VITE_SUPABASE_URL` | Supabase -> Project Settings -> Data API -> Project URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase -> Project Settings -> API Keys -> **Publishable** key |

Everything in these settings is visible to anyone using the site. **Never put
the Supabase secret key here**: the app refuses to start if you do.

In Supabase, under **Authentication -> URL Configuration**, add these exact
redirect URLs (setup guide, step 3):
`http://localhost:5173/auth/callback` and `http://localhost:5173/reset-password`.
The backend must allow `http://localhost:5173` in `CORS_ORIGINS` (the default).

## Design principles

- **Familiar layout:** new chat at the top left, recent chats below it, your
  account (settings, admin panel, log out) at the bottom left. On phones the
  same sidebar opens from the menu button at the top left.
- **Few choices at a time:** one main action per screen; plain language;
  error messages say what to do next.
- **Accessible:** every field has a label, errors are announced to screen
  readers, everything works with the keyboard, there is a visible focus
  ring, and colours meet WCAG AA contrast in light and dark mode.

## Code layout

| Folder | Responsibility |
|---|---|
| `src/config/` | Reads and checks the public settings |
| `src/api/` | `ApiClient` (adds the login token, safe error messages) and one class per backend area |
| `src/auth/` | `AuthGateway` interface, its Supabase implementation, login state, route guards |
| `src/app/` | Routes and the services container (dependency injection, built in `main.tsx`) |
| `src/layout/` | Login layout and the signed-in app shell (sidebar, account menu) |
| `src/pages/` | One component per page |
| `src/components/ui/` | Reusable, accessible UI pieces |
| `src/test/` | Test setup and fakes |

Tests sit next to the code they test (`*.test.ts(x)`).

## Security

- **Login:** PKCE flow, so email links carry a one-time code (usable only in
  the browser that asked for it), never tokens. Error messages never reveal
  whether an email has an account. A password reset ends every session.
- **Role and status** come from the backend (`GET /api/profile`), never from
  the token or the browser. A 401 from the backend logs the user out.
- **No HTML from strings:** user and AI text is rendered by React as text.
  Lint rules forbid `dangerouslySetInnerHTML` and `innerHTML`. Text from email
  links is never displayed; only fixed messages chosen by error code.
- **Content-Security-Policy** is added to the built page: only our own
  scripts and styles, and network access only to our API and Supabase. At
  deployment the host must also send `frame-ancestors 'none'`, HSTS,
  `X-Content-Type-Options: nosniff` and `Referrer-Policy` as HTTP headers.
- **API calls** send no cookies, follow no redirects, and only go to `/api/` paths.
- **No open redirects:** after login, only internal paths are followed.

## Checks

The same checks run on GitHub on every push (`.github/workflows/frontend.yml`):

```bash
npm run typecheck
npm run lint
npm test
npm run build      # needs the three VITE_ settings
npm audit
```
