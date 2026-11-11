# SentryPrompt browser extension (FR-010, Increment 18 MVP)

Screens what you type into ChatGPT for personal information, before you send
it — without making you leave ChatGPT or use SentryPrompt's own chat. This
exists because not every student who wants their prompts screened wants to
switch AI tools: the extension meets you where you already are.

It is a minimal version of FR-010 (PROJECT_BACKLOG.md, Increment 18),
reusing the existing backend
exactly as it already is — `SourceChannel.EXTENSION` and
`POST /api/prompts/screen` needed no changes at all.

## How it works

```
content script (runs on chatgpt.com)
  -> watches the prompt box, debounces typing
  -> chrome.runtime.sendMessage("SCREEN_PROMPT", text)
       |
       v
background service worker (holds the session token; the only
part that ever talks to the network)
  -> POST {BACKEND_URL}/api/prompts/screen  (channel: "extension")
  -> POST {SUPABASE_URL}/auth/v1/token      (login, from the popup)
```

The content script never fetches anything itself and never sees the
session token — only the background service worker does. That also
sidesteps the host page's own Content-Security-Policy, which could
otherwise block a page-context fetch to a different origin even when the
extension itself is allowed to reach it.

While a flagged prompt is pending, pressing Enter or the send button is
blocked (capture-phase listeners) until the student picks **Edit my
prompt**, **Send anyway**, or **Hide details and send** — the same three
choices (plus the web app's fourth, "hide and send", which only shows when
there is something to hide) that `DecisionDialog.tsx` offers in the web
app. "Hide details and send" replaces each flagged span with
`[REDACTED_<CATEGORY>]` directly in the ChatGPT prompt box — the same
placeholder convention `backend/app/screening/redaction.py` uses — so the
redacted text is what actually gets sent to ChatGPT, not the original.

## Setup

1. `cp config.example.js config.js` and fill in `BACKEND_URL`,
   `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` (the publishable key only
   — never the secret key; `background.js` refuses to start if a
   secret/service-role key is pasted in, the same guard
   `frontend/src/config/env.ts` uses).
2. If `BACKEND_URL` or `SUPABASE_URL` point anywhere other than
   `http://localhost:8000`, add the new origin to `manifest.json`'s
   `host_permissions` too — Chrome only lets an extension's background
   script reach hosts it has explicitly declared, and it will not warn you
   at runtime if you forget; the fetch will just silently fail as
   `unavailable`.
3. In Chrome: `chrome://extensions` → Developer mode → **Load unpacked** →
   select this `extension/` folder.
4. Click the SentryPrompt icon and log in with your SentryPrompt account
   (the same login the web app uses).
5. Open chatgpt.com and start typing.

## Known limitations

- **Verified live on ChatGPT only.** `content.js` knows no site's markup:
  it listens on the page itself for Enter, send-button clicks and form
  submits, and treats whichever text box the student is typing in as the
  prompt. `manifest.json` therefore also lists Claude, Gemini and Copilot,
  and adding another site is only its URL in `content_scripts.matches` and
  `host_permissions`. Those three have not been tried in a real browser
  yet, so check each once before relying on it.
- **Logged-out students are not blocked.** If nobody is logged in, the
  extension does not screen and does not block sending — it simply does
  nothing, rather than stopping every message a brand-new visitor types
  before they even have an account. This is a deliberate choice, not an
  oversight: the web app can require login before any chat happens; an
  extension's default state right after installing is "not yet logged
  in," and blocking by default there would be a worse first experience for
  no security benefit (nothing sensitive has been screened or stored
  either way).
- **A failed or rate-limited check fails closed**, matching NFR-015: if
  the backend can't be reached, times out, or the student has hit the
  rate limit, sending is blocked with a "we couldn't fully check this
  prompt" banner (no flags shown, since none could be computed) — the
  same fail-closed stance the web app takes, not a silent pass-through.
- **No refresh-token flow.** The popup's login stores the access token's
  own expiry; once it expires the student logs in again from the popup.
  A real production build would add Supabase's refresh-token exchange.
- **Plain-text redaction only.** "Hide details and send" sets the prompt
  box's text content directly; it does not preserve any rich formatting
  ChatGPT's editor might otherwise support.
- **No extension icon pack beyond the three required sizes** (16/48/128),
  generated with Pillow to match the app's teal shield branding — not
  professionally designed artwork.

## Testing

`tests/run_e2e.cjs` loads the real unpacked extension in a real Chromium
instance (Playwright) against a local fixture page (`tests/fixture.html`)
that mimics the target site's element shape — **not a copy of ChatGPT's
code**, just a page using the same selectors `content.js` already looks
for, so the test doesn't depend on this environment having live internet
access to the real site. Nothing about the backend call is mocked: it logs
in for real against the harness's Supabase Auth stand-in and screens for
real against the live backend and Groq model, the same evidence
environment used for the Testing Phase submission (see that document's
Appendix A.1).

```bash
# from the repository root, with the backend + auth stand-in running
# (see docs/Project_Deliverable_Requirements/Testing Phase/Submission's
# Appendix A.1 for how that environment is built)
xvfb-run -a node extension/tests/run_e2e.cjs
```

It checks, end to end, against the real system:

1. Logging in through the popup against the real Supabase Auth stand-in.
2. A clean prompt shows no banner and submits normally on Enter.
3. A prompt with a South African ID number is flagged with the real
   category and the real plain-language explanation from the backend;
   Enter is blocked while the banner is pending.
4. "Hide details and send" replaces the ID number with
   `[REDACTED_SA_ID]` in the actual prompt box, and Enter then submits
   the redacted text.
5. Logged out, screening is skipped and sending is never blocked
   (the documented limitation above).

All 11 checks pass as of this writing; `extension/screenshot-banner.png` is
a real screenshot taken during that run.

### Send-gate test (mock backend)

`tests/run_generic_e2e.cjs` loads the same unpacked extension against
`tests/fixture_generic.html`, which has two composers built like real
ones: a contenteditable with no id whose send button only exists while
there is text, and a plain `<textarea>` form with an unlabeled submit
button. The backend here is a small in-process mock (it flags any
13-digit number), because this test is about the browser side: a prompt
sent the instant typing stops (Enter or click) must still be held and
screened, the three banner actions must each send exactly once, a failed
check must fail closed, and a logged-out student must not be blocked.

```bash
xvfb-run -a node extension/tests/run_generic_e2e.cjs
```

## What deliberately did not change

`backend/app/domain/enums.py`'s `SourceChannel.EXTENSION`, the
`channel` field on `POST /api/prompts/screen`, and
`CORS_ORIGINS` were **not touched** by this increment. Chrome does not
enforce CORS against an extension's background-script fetches to a host
the extension has declared in `host_permissions` — the backend's CORS
allow-list, which still only lists the web app's own origins, was
correctly scoped from the start and needed no change. (PROJECT_BACKLOG.md's
original Increment 18 entry assumed a CORS change would be needed; that
assumption did not hold once this was built, and the backlog entry has
been updated to match.)
