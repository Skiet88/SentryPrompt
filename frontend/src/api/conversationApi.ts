import type { ApiClient } from "./apiClient";
import type { ConversationSummary } from "./types";

export class ConversationApi {
  private readonly client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  list(): Promise<ConversationSummary[]> {
    return this.client.get<ConversationSummary[]>("/api/conversations");
  }
}
