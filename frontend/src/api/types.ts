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
