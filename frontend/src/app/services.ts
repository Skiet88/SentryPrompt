import { createContext, useContext } from "react";

import type { ConversationApi } from "@/api/conversationApi";
import type { ProfileApi } from "@/api/profileApi";
import type { AuthGateway } from "@/auth/authGateway";

/** Everything the pages use to talk to the outside world, created once in main.tsx. */
export interface Services {
  auth: AuthGateway;
  profile: Pick<ProfileApi, "get">;
  conversations: Pick<ConversationApi, "list">;
  /**
   * The address the app was opened with, captured before Supabase reads (and
   * removes) the one-time code from an email link.
   */
  landingUrl: URL;
}

export const ServicesContext = createContext<Services | null>(null);

export function useServices(): Services {
  const services = useContext(ServicesContext);
  if (!services) throw new Error("useServices must be used inside <ServicesContext.Provider>");
  return services;
}
