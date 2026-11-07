import type { ApiClient } from "./apiClient";
import type { Profile } from "./types";

/** Longest display name the backend accepts (user_factory.MAX_DISPLAY_NAME_LENGTH). */
export const MAX_DISPLAY_NAME_LENGTH = 100;

export class ProfileApi {
  private readonly client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  get(): Promise<Profile> {
    return this.client.get<Profile>("/api/profile");
  }

  /** Only the display name can be changed (the backend rejects any other field). */
  updateDisplayName(displayName: string): Promise<Profile> {
    return this.client.put<Profile>("/api/profile", { displayName });
  }

  /** Permanently deletes the account and all its data (FR-020). */
  deleteAccount(): Promise<void> {
    return this.client.delete("/api/profile");
  }
}
