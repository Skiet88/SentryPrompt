/** Shapes of the backend's JSON responses (backend/app/schemas). */

export type UserRole = "student" | "admin";
export type AccountStatus = "active" | "suspended";

export interface Profile {
  userId: string;
  email: string;
  displayName: string;
  role: UserRole;
  status: AccountStatus;
  emailVerified: boolean;
  createdAt: string;
}

export interface ConversationSummary {
  conversationId: string;
  title: string;
  channel: string;
  createdAt: string;
  updatedAt: string;
}

export type Verdict = "FLAG" | "NO_FLAG" | "UNAVAILABLE";

export interface Flag {
  category: string;
  /** Positions in the submitted text, counted in characters (code points). */
  startIndex: number;
  endIndex: number;
  detectorSource: "rule" | "context";
  explanation: string;
}

export interface Screening {
  screeningResultId: string;
  aggregatedVerdict: Verdict;
  ruleBasedVerdict: Verdict;
  contextAwareVerdict: Verdict;
  requiresDecision: boolean;
  notice: string | null;
  flags: Flag[];
}

export interface ChatMessage {
  messageId: string;
  role: "user" | "assistant";
  /** Plain text. User messages are stored with detected values replaced, e.g. [REDACTED_SA_ID]. */
  content: string;
  createdAt: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ChatMessage[];
}

export type SendResult =
  | {
      status: "sent";
      screening: Screening;
      userMessage: ChatMessage;
      assistantMessage: ChatMessage;
      /** The chat's title, made by the backend from the first (redacted) prompt. */
      conversationTitle: string;
    }
  | {
      status: "needs_decision";
      screening: Screening;
      userMessage: null;
      assistantMessage: null;
      conversationTitle: null;
    };

/** An account as an admin sees it: account-level fields only, never content (NFR-013). */
export interface AdminUser {
  userId: string;
  email: string;
  emailVerified: boolean;
  displayName: string;
  role: UserRole;
  status: AccountStatus;
  createdAt: string | null;
}

export interface StatusChange {
  userId: string;
  status: AccountStatus;
  /** Null when the account already had this status (nothing new to record). */
  auditLogId: string | null;
  /** False: blocked in SentryPrompt, but the Supabase login block still needs retrying. */
  loginBlockUpdated: boolean;
}

export interface AuditLogEntry {
  logId: string;
  adminUserId: string;
  targetUserId: string;
  actionType: "suspend" | "reinstate";
  timestamp: string;
  details: string;
}
