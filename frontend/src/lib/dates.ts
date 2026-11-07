/** How times are shown: short and familiar, in the student's own time zone. */

const DAY = 86_400_000;

function daysAgo(date: Date, now: Date): number {
  return Math.round((new Date(now.toDateString()).getTime() - new Date(date.toDateString()).getTime()) / DAY);
}

function valid(iso: string): Date | null {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? null : date;
}

const time = (date: Date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** Under a message: "14:05" today, "Yesterday 14:05", "3 Nov, 14:05", or with the year if not this year. */
export function messageTime(iso: string, now = new Date()): string {
  const date = valid(iso);
  if (!date) return "";
  const days = daysAgo(date, now);
  if (days === 0) return time(date);
  if (days === 1) return `Yesterday ${time(date)}`;
  const sameYear = date.getFullYear() === now.getFullYear();
  const day = date.toLocaleDateString([], { day: "numeric", month: "short", ...(sameYear ? {} : { year: "numeric" }) });
  return `${day}, ${time(date)}`;
}

/** The full date and time, for a tooltip and screen readers. */
export function fullTime(iso: string): string {
  const date = valid(iso);
  return date ? date.toLocaleString([], { dateStyle: "full", timeStyle: "short" }) : "";
}

export type ChatGroup = "Today" | "Yesterday" | "Previous 7 days" | "Previous 30 days" | "Older";
export const CHAT_GROUPS: ChatGroup[] = ["Today", "Yesterday", "Previous 7 days", "Previous 30 days", "Older"];

/** Which sidebar heading a chat goes under, by when it was last used. */
export function chatGroup(iso: string, now = new Date()): ChatGroup {
  const date = valid(iso);
  if (!date) return "Older";
  const days = daysAgo(date, now);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days <= 7) return "Previous 7 days";
  if (days <= 30) return "Previous 30 days";
  return "Older";
}
