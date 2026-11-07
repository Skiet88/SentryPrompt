/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type Plugin } from "vite";

/**
 * Adds a strict Content-Security-Policy to the built page (SECURITY_RULES.md §4).
 * Only scripts and styles from our own origin run; the page may only talk to
 * our API and Supabase. Not applied in development, where Vite's hot reload
 * needs inline scripts. frame-ancestors and HSTS must be set as HTTP headers
 * by the static host at deployment (a <meta> tag can't set them).
 */
function contentSecurityPolicy(env: Record<string, string>): Plugin {
  return {
    name: "content-security-policy",
    apply: "build",
    transformIndexHtml(html) {
      const api = requiredOrigin(env, "VITE_API_URL");
      const supabase = requiredOrigin(env, "VITE_SUPABASE_URL");
      const realtime = supabase.replace(/^https:/, "wss:");
      const policy = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        `connect-src 'self' ${api} ${supabase} ${realtime}`,
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
      ].join("; ");
      return html.replace(
        "<head>",
        `<head>\n    <meta http-equiv="Content-Security-Policy" content="${policy}" />`,
      );
    },
  };
}

function requiredOrigin(env: Record<string, string>, name: string): string {
  const value = env[name];
  if (!value) throw new Error(`${name} must be set to build the frontend`);
  const url = new URL(value);
  const local = url.hostname === "localhost" || url.hostname === "127.0.0.1";
  if (url.protocol !== "https:" && !local) throw new Error(`${name} must use https`);
  return url.origin;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  return {
    plugins: [react(), tailwindcss(), contentSecurityPolicy(env)],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: { port: 5173, strictPort: true },
    build: { sourcemap: false },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      css: false,
      restoreMocks: true,
    },
  };
});
