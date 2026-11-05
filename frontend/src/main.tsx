import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AdminApi } from "@/api/adminApi";
import { ApiClient } from "@/api/apiClient";
import { ConversationApi } from "@/api/conversationApi";
import { ProfileApi } from "@/api/profileApi";
import { App } from "@/app/App";
import type { Services } from "@/app/services";
import { SupabaseAuthGateway } from "@/auth/supabaseAuthGateway";
import { ConfigError, readConfig } from "@/config/env";

import "./index.css";

/** Builds the app's services once and hands them to the UI (dependency injection). */
function buildServices(): Services {
  const landingUrl = new URL(window.location.href);
  const config = readConfig(import.meta.env);
  const auth = SupabaseAuthGateway.create(config, window.location.origin);
  // A 401 from our backend means the login ended (logged out elsewhere, or suspended by ban).
  const api = new ApiClient(config.apiUrl, auth, () => void auth.signOut("local").catch(() => undefined));
  return {
    auth,
    profile: new ProfileApi(api),
    conversations: new ConversationApi(api),
    admin: new AdminApi(api),
    landingUrl,
  };
}

const container = document.getElementById("root");
if (!container) throw new Error("Missing #root element");
const root = createRoot(container);
try {
  const services = buildServices();
  root.render(
    <StrictMode>
      <App services={services} />
    </StrictMode>,
  );
} catch (error) {
  const message = error instanceof ConfigError ? error.message : "SentryPrompt could not start.";
  root.render(
    <div role="alert" style={{ padding: 24, fontFamily: "system-ui" }}>
      {message}
    </div>,
  );
}
