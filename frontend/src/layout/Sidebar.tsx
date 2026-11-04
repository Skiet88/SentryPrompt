import { MessageSquare, SquarePen, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, useMatch, useNavigate } from "react-router";

import { ApiError } from "@/api/apiClient";
import type { ConversationSummary } from "@/api/types";
import { useServices } from "@/app/services";

import { useConversations } from "@/chat/conversationsStore";
import { plainText, RedactedText } from "@/chat/RedactedText";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

import { UserMenu } from "./UserMenu";

/** "Today 14:05", "Yesterday", or "3 Nov": shown when hovering over a chat. */
export function chatDate(iso: string, now = new Date()): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const days = Math.round(
    (new Date(now.toDateString()).getTime() - new Date(date.toDateString()).getTime()) / 86_400_000,
  );
  if (days === 0) return `Today ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  if (days === 1) return "Yesterday";
  return date.toLocaleDateString([], { day: "numeric", month: "short" });
}

/** Left sidebar: new chat at the top, recent chats in the middle, your account at the bottom. */
export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const load = useConversations();
  const { conversations } = useServices();
  const navigate = useNavigate();
  const open = useMatch("/c/:conversationId")?.params.conversationId;
  const [toDelete, setToDelete] = useState<ConversationSummary | null>(null);

  async function deleteChat() {
    if (!toDelete) return;
    try {
      await conversations.remove(toDelete.conversationId);
    } catch (e) {
      // Already gone (404) counts as deleted; anything else is shown in the dialog.
      if (!(e instanceof ApiError && e.status === 404)) {
        throw new Error(e instanceof ApiError ? e.message : "Couldn't delete the chat. Please try again.", {
          cause: e,
        });
      }
    }
    load.forget(toDelete.conversationId);
    if (open === toDelete.conversationId) void navigate("/", { replace: true });
    setToDelete(null);
    onNavigate?.();
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center px-4 pt-4 pb-3">
        <Link to="/" onClick={onNavigate} aria-label="SentryPrompt home">
          <Logo />
        </Link>
      </div>

      <div className="px-3">
        <Button asChild variant="secondary" className="w-full justify-start">
          <Link to="/" onClick={onNavigate}>
            <SquarePen aria-hidden /> New chat
          </Link>
        </Button>
      </div>

      <nav aria-label="Recent chats" className="mt-5 min-h-0 flex-1 overflow-y-auto px-3">
        <h2 className="px-2 pb-1.5 text-xs font-medium text-muted">Recent</h2>
        {load.status === "loading" && (
          <div className="px-2 py-2">
            <Spinner className="size-4" label="Loading chats" />
          </div>
        )}
        {load.status === "failed" && (
          <p className="px-2 py-1 text-sm text-muted">
            Couldn't load your chats.{" "}
            <button type="button" onClick={load.refresh} className="text-primary hover:underline">
              Try again
            </button>
          </p>
        )}
        {load.status === "ready" && load.items.length === 0 && (
          <p className="px-2 py-1 text-sm text-muted">Your chats will appear here.</p>
        )}
        {load.status === "ready" && load.items.length > 0 && (
          <ul className="space-y-0.5">
            {load.items.map((c) => (
              <li key={c.conversationId} className="group relative">
                <NavLink
                  to={`/c/${encodeURIComponent(c.conversationId)}`}
                  title={chatDate(c.updatedAt) ? `Last used: ${chatDate(c.updatedAt)}` : undefined}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2.5 rounded-lg py-2 pr-9 pl-2 text-sm hover:bg-hover",
                      isActive && "bg-hover font-medium",
                    )
                  }
                >
                  <MessageSquare className="size-4 shrink-0 text-muted" aria-hidden />
                  <span className="min-w-0 flex-1 truncate">
                    <RedactedText text={c.title} compact />
                  </span>
                </NavLink>
                <button
                  type="button"
                  onClick={() => setToDelete(c)}
                  aria-label={`Delete chat: ${plainText(c.title)}`}
                  className="absolute top-1/2 right-1 flex size-7 -translate-y-1/2 items-center justify-center rounded-md text-muted opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-surface hover:text-danger focus-visible:opacity-100 [@media(pointer:coarse)]:opacity-100"
                >
                  <Trash2 className="size-4" aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <ConfirmDialog
        open={toDelete !== null}
        onOpenChange={(next) => !next && setToDelete(null)}
        title="Delete this chat?"
        confirmLabel="Delete"
        busyLabel="Deleting…"
        onConfirm={deleteChat}
      >
        <p>The chat and all its messages will be deleted permanently.</p>
      </ConfirmDialog>

      <div className="border-t border-border p-2">
        <UserMenu onNavigate={onNavigate} />
      </div>
    </div>
  );
}
