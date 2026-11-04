/**
 * Public settings, read once at startup. Only public values are allowed here:
 * everything in a VITE_ variable is visible to anyone using the site.
 */

export interface AppConfig {
  apiUrl: string;
  supabaseUrl: string;
  supabasePublishableKey: string;
}

export class ConfigError extends Error {}

export function readConfig(env: Record<string, string | undefined>): AppConfig {
  const apiUrl = (env.VITE_API_URL ?? "").replace(/\/+$/, "");
  const supabaseUrl = (env.VITE_SUPABASE_URL ?? "").replace(/\/+$/, "");
  const supabasePublishableKey = env.VITE_SUPABASE_PUBLISHABLE_KEY ?? "";

  if (!apiUrl || !supabaseUrl || !supabasePublishableKey) {
    throw new ConfigError(
      "Missing settings: copy frontend/.env.example to frontend/.env.local and fill in all three values.",
    );
  }
  // A secret key in the browser would give anyone full control of the project.
  if (supabasePublishableKey.startsWith("sb_secret_") || looksLikeServiceRoleJwt(supabasePublishableKey)) {
    throw new ConfigError(
      "VITE_SUPABASE_PUBLISHABLE_KEY is a SECRET key. Use the publishable key, and reset the secret key in Supabase.",
    );
  }
  return { apiUrl, supabaseUrl, supabasePublishableKey };
}

function looksLikeServiceRoleJwt(key: string): boolean {
  const payload = key.split(".")[1];
  if (!payload) return false;
  try {
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))).role === "service_role";
  } catch {
    return false;
  }
}
