// Copy this file to config.js and fill in your own values.
// Only public values belong here: the Supabase key below MUST be the
// publishable key (sb_publishable_...), never the secret key. background.js
// refuses to start if a secret key is pasted in by mistake (same guard as
// frontend/src/config/env.ts).
//
// If BACKEND_URL or SUPABASE_URL point anywhere other than
// http://localhost:8000 / the Supabase project already declared in
// manifest.json's host_permissions, add the new origin there too and
// reload the unpacked extension — Chrome only allows an extension's
// background script to reach hosts it has explicitly declared.

export const CONFIG = {
  BACKEND_URL: "http://localhost:8000",
  SUPABASE_URL: "http://127.0.0.1:54321",
  SUPABASE_PUBLISHABLE_KEY: "sb_publishable_standin",
};
