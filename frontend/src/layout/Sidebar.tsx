import { MessageSquare, SquarePen } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router";

import type { ConversationSummary } from "@/api/types";
import { useServices } from "@/app/services";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";

import { UserMenu } from "./UserMenu";

type Load = { status: "loading" } | { status: "ready"; items: ConversationSummary[] } | { status: "failed" };

/** Left sidebar: new chat at the top, recent chats in the middle, your account at the bottom. */
export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { conversations } = useServices();
  const [load, setLoad] = useState<Load>({ status: "loading" });

  useEffect(() => {
    let active = true;
    conversations
      .list()
      .then((items) => active && setLoad({ status: "ready", items }))
      .catch(() => active && setLoad({ status: "failed" }));
    return () => {
      active = false;
    };
  }, [conversations]);

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
        {load.status === "failed" && <p className="px-2 py-1 text-sm text-muted">Couldn't load your chats.</p>}
        {load.status === "ready" && load.items.length === 0 && (
          <p className="px-2 py-1 text-sm text-muted">Your chats will appear here.</p>
        )}
        {load.status === "ready" && load.items.length > 0 && (
          <ul className="space-y-0.5">
            {load.items.map((c) => (
              <li key={c.conversationId}>
                <NavLink
                  to={`/c/${encodeURIComponent(c.conversationId)}`}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm hover:bg-hover",
                      isActive && "bg-hover font-medium",
                    )
                  }
                >
                  <MessageSquare className="size-4 shrink-0 text-muted" aria-hidden />
                  <span className="truncate">{c.title}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="border-t border-border p-2">
        <UserMenu onNavigate={onNavigate} />
      </div>
    </div>
  );
}
