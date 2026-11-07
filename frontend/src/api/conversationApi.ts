import type { ApiClient } from "./apiClient";
import type { ConversationDetail, ConversationSummary, SendResult } from "./types";

export type SendDecision = "check" | "send_anyway" | "hide_flagged";

/** Longest prompt the backend accepts, in characters (FR-001). */
export const MAX_PROMPT_LENGTH = 4000;

export class ConversationApi {
  private readonly client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  list(): Promise<ConversationSummary[]> {
    return this.client.get<ConversationSummary[]>("/api/conversations");
  }

  /** No title is sent: a title made from the prompt would store its text unencrypted. */
  create(): Promise<ConversationSummary> {
    return this.client.post<ConversationSummary>("/api/conversations", { channel: "webapp" });
  }

  get(conversationId: string): Promise<ConversationDetail> {
    return this.client.get<ConversationDetail>(`/api/conversations/${encodeURIComponent(conversationId)}`);
  }

  /** Permanently deletes the chat and its messages (FR-020). */
  remove(conversationId: string): Promise<void> {
    return this.client.delete(`/api/conversations/${encodeURIComponent(conversationId)}`);
  }

  /**
   * decision: "check" for a normal send; after a warning, "send_anyway" or
   * "hide_flagged" (every flagged detail is replaced before the AI sees it).
   */
  send(conversationId: string, text: string, decision: SendDecision): Promise<SendResult> {
    return this.client.post<SendResult>(`/api/conversations/${encodeURIComponent(conversationId)}/messages`, {
      text,
      sendAnyway: decision === "send_anyway",
      hideFlagged: decision === "hide_flagged",
    });
  }
}
