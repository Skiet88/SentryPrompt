import type { ApiClient } from "./apiClient";
import type { ConversationDetail, ConversationSummary, SendResult } from "./types";

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

  send(conversationId: string, text: string, sendAnyway: boolean): Promise<SendResult> {
    return this.client.post<SendResult>(`/api/conversations/${encodeURIComponent(conversationId)}/messages`, {
      text,
      sendAnyway,
    });
  }
}
