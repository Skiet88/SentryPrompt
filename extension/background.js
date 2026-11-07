// Background service worker (Manifest V3). The only place that holds the
// session token or talks to the network — content scripts never fetch
// directly, so a hostile page can never see the token or the backend
// response (SECURITY_RULES.md §3 "secrets only in ... never in code, logs
// or chat" extends here: the token lives only in chrome.storage.local,
// scoped to this extension, never passed to the page).

import { CONFIG } from "./config.js";

const STORAGE_KEY = "sentryprompt_session";

function looksLikeServiceRoleKey(key) {
  // Same guard as frontend/src/config/env.ts: a secret/service-role key
  // must never ship in a browser-side artifact.
  if (key.startsWith("sb_secret_")) return true;
  const payload = key.split(".")[1];
  if (!payload) return false;
  try {
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json).role === "service_role";
  } catch {
    return false;
  }
}

if (looksLikeServiceRoleKey(CONFIG.SUPABASE_PUBLISHABLE_KEY)) {
  throw new Error(
    "config.js: SUPABASE_PUBLISHABLE_KEY looks like a SECRET key. Use the publishable key only.",
  );
}

async function getSession() {
  const { [STORAGE_KEY]: session } = await chrome.storage.local.get(STORAGE_KEY);
  return session ?? null;
}

async function setSession(session) {
  await chrome.storage.local.set({ [STORAGE_KEY]: session });
}

async function clearSession() {
  await chrome.storage.local.remove(STORAGE_KEY);
}

async function login(email, password) {
  const res = await fetch(`${CONFIG.SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: CONFIG.SUPABASE_PUBLISHABLE_KEY },
    body: JSON.stringify({ email, password }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    return { ok: false, message: "Incorrect email or password." };
  }
  await setSession({
    accessToken: body.access_token,
    email: body.user?.email ?? email,
    expiresAt: body.expires_at ? body.expires_at * 1000 : null,
  });
  return { ok: true, email: body.user?.email ?? email };
}

async function logout() {
  const session = await getSession();
  if (session?.accessToken) {
    await fetch(`${CONFIG.SUPABASE_URL}/auth/v1/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.accessToken}`, apikey: CONFIG.SUPABASE_PUBLISHABLE_KEY },
    }).catch(() => {});
  }
  await clearSession();
}

async function screenPrompt(text) {
  const session = await getSession();
  if (!session?.accessToken) {
    return { kind: "not_logged_in" };
  }
  let res;
  try {
    res = await fetch(`${CONFIG.BACKEND_URL}/api/prompts/screen`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.accessToken}` },
      body: JSON.stringify({ text, channel: "extension" }),
    });
  } catch {
    return { kind: "unavailable" };
  }
  if (res.status === 401) {
    await clearSession();
    return { kind: "not_logged_in" };
  }
  if (res.status === 429) {
    return { kind: "rate_limited" };
  }
  if (!res.ok) {
    return { kind: "unavailable" };
  }
  const data = await res.json();
  return { kind: "ok", data };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  (async () => {
    switch (message?.type) {
      case "LOGIN":
        sendResponse(await login(message.email, message.password));
        break;
      case "LOGOUT":
        await logout();
        sendResponse({ ok: true });
        break;
      case "GET_SESSION":
        sendResponse(await getSession());
        break;
      case "SCREEN_PROMPT":
        sendResponse(await screenPrompt(message.text));
        break;
      default:
        sendResponse({ error: "unknown_message" });
    }
  })();
  return true; // keep the message channel open for the async response
});
