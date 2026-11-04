import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { ConversationSummary } from "@/api/types";
import { useServices } from "@/app/services";

export interface ConversationsStore {
  status: "loading" | "ready" | "failed";
  items: ConversationSummary[];
  refresh(): void;
  /** Adds or moves a conversation to the top (after it was created or used). */
  touch(conversation: ConversationSummary): void;
  /** Removes a deleted conversation from the list. */
  forget(conversationId: string): void;
}

const Context = createContext<ConversationsStore | null>(null);

/** The signed-in user's conversations, shared by the sidebar and the chat. */
export function ConversationsProvider({ children }: { children: ReactNode }) {
  const { conversations } = useServices();
  const [status, setStatus] = useState<ConversationsStore["status"]>("loading");
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    conversations
      .list()
      .then((list) => {
        if (!active) return;
        setItems(list);
        setStatus("ready");
      })
      .catch(() => active && setStatus("failed"));
    return () => {
      active = false;
    };
  }, [conversations, version]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);
  const touch = useCallback((conversation: ConversationSummary) => {
    setItems((current) => [conversation, ...current.filter((c) => c.conversationId !== conversation.conversationId)]);
  }, []);

  const forget = useCallback((conversationId: string) => {
    setItems((current) => current.filter((c) => c.conversationId !== conversationId));
  }, []);

  const value = useMemo(() => ({ status, items, refresh, touch, forget }), [status, items, refresh, touch, forget]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useConversations(): ConversationsStore {
  const store = useContext(Context);
  if (!store) throw new Error("useConversations must be used inside <ConversationsProvider>");
  return store;
}
