import type { ApiClient } from "./apiClient";
import type { AdminUser, AuditLogEntry, StatusChange } from "./types";

export const ADMIN_PAGE_SIZE = 50;
/** Longest suspension reason the backend accepts. */
export const MAX_REASON_LENGTH = 500;

/** /api/admin: account management only. There is no call that reaches chats or messages (NFR-013). */
export class AdminApi {
  private readonly client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  listUsers(page: number): Promise<AdminUser[]> {
    const query = new URLSearchParams({ page: String(page), perPage: String(ADMIN_PAGE_SIZE) });
    return this.client.get<AdminUser[]>(`/api/admin/users?${query}`);
  }

  suspend(userId: string, reason: string): Promise<StatusChange> {
    return this.client.post<StatusChange>(`/api/admin/users/${encodeURIComponent(userId)}/suspend`, { reason });
  }

  reinstate(userId: string, reason: string): Promise<StatusChange> {
    return this.client.post<StatusChange>(`/api/admin/users/${encodeURIComponent(userId)}/reinstate`, { reason });
  }

  auditLog(offset: number): Promise<AuditLogEntry[]> {
    const query = new URLSearchParams({ limit: String(ADMIN_PAGE_SIZE), offset: String(offset) });
    return this.client.get<AuditLogEntry[]>(`/api/admin/audit-log?${query}`);
  }
}
