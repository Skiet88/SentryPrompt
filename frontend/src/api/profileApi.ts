import type { ApiClient } from "./apiClient";
import type { Profile } from "./types";

export class ProfileApi {
  private readonly client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  get(): Promise<Profile> {
    return this.client.get<Profile>("/api/profile");
  }
}
