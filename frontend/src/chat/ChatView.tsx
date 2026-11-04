import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";

import { ApiError } from "@/api/apiClient";
import type { ChatMessage, ConversationSummary } from "@/api/types";
import { useServices } from "@/app/services";
import { useProfile } from "@/auth/authState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FullPageSpinner } from "@/components/ui/spinner";
import { displayNameOf } from "@/layout/UserMenu";

import { Composer } from "./Composer";
import { useConversations } from "./conversationsStore";
import { DecisionDialog, type PendingDecision } from "./DecisionDialog";
import { MessageList, type PendingPrompt } from "./MessageList";
import { PrivacyNote } from "./PrivacyNote";

export function greeting(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

type Load = "loading" | "ready" | "not_found" | "failed";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "This chat no longer exists. Start a new one.";
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

/**
 * One chat. With no conversationId it is a new chat: the conversation is
 * created when the first prompt is sent, and onCreated lets the page keep
 * this view (and the reply on its way) when the address changes to /c/<id>.
 */
export function ChatView({
  conversationId,
  onCreated,
}: {
  conversationId?: string;
  onCreated: (conversationId: string) => void;
}) {
  const { conversations } = useServices();
  const store = useConversations();
  const profile = useProfile();
  const navigate = useNavigate();
  const [initialId] = useState(conversationId);
  const [summary, setSummary] = useState<ConversationSummary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [load, setLoad] = useState<Load>(initialId ? "loading" : "ready");
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<PendingPrompt | null>(null);
  const [decision, setDecision] = useState<PendingDecision | null>(null);
  const [error, setError] = useState<string>();
  const [focusSignal, setFocusSignal] = useState(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!initialId) return;
    conversations
      .get(initialId)
      .then((detail) => {
        setSummary(detail);
        setMessages(detail.messages);
        setLoad("ready");
      })
      .catch((e: unknown) => setLoad(e instanceof ApiError && e.status === 404 ? "not_found" : "failed"));
  }, [conversations, initialId]);

  async function send(text: string, sendAnyway: boolean) {
    setError(undefined);
    setDecision(null);
    setDraft("");
    setPending({ text });
    try {
      let current = summary;
      if (!current) {
        current = await conversations.create();
        setSummary(current);
        store.touch(current);
        if (mounted.current) {
          onCreated(current.conversationId);
          void navigate(`/c/${encodeURIComponent(current.conversationId)}`);
        }
      }
      const result = await conversations.send(current.conversationId, text, sendAnyway);
      if (result.status === "needs_decision") {
        setDecision({ text, screening: result.screening });
      } else {
        setMessages((m) => [...m, result.userMessage, result.assistantMessage]);
        const updated = { ...current, title: result.conversationTitle, updatedAt: result.assistantMessage.createdAt };
        setSummary(updated);
        store.touch(updated);
      }
    } catch (e) {
      setDraft(text);
      setError(errorMessage(e));
    } finally {
      setPending(null);
    }
  }

  function editPrompt() {
    if (decision) setDraft(decision.text);
    setDecision(null);
    setFocusSignal((n) => n + 1);
  }

  if (load === "loading") return <FullPageSpinner />;
  if (load === "not_found" || load === "failed") {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-5 text-center">
        <h1 className="text-xl font-semibold">{load === "not_found" ? "Chat not found" : "Couldn't open this chat"}</h1>
        <p className="text-muted">
          {load === "not_found" ? "It may have been deleted." : "Check your connection and try again."}
        </p>
        <Button asChild>
          <Link to="/">Start a new chat</Link>
        </Button>
      </div>
    );
  }

  const disabledReason =
    profile.status === "suspended" ? "Your account is suspended, so you can't send prompts." : undefined;
  const composer = (
    <>
      {error && (
        <Alert tone="error" className="mb-3">
          {error}
        </Alert>
      )}
      <Composer
        value={draft}
        onChange={setDraft}
        onSend={() => void send(draft.trim(), false)}
        busy={pending !== null}
        disabledReason={disabledReason}
        focusSignal={focusSignal}
      />
    </>
  );
  const dialog = (
    <DecisionDialog
      decision={decision}
      onEdit={editPrompt}
      onSendAnyway={() => decision && void send(decision.text, true)}
    />
  );

  if (messages.length === 0 && !pending) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center px-4 py-10">
        <div className="w-full max-w-2xl">
          <h1 className="text-center text-3xl font-semibold tracking-tight">
            {greeting(new Date().getHours())}, {displayNameOf(profile)}
          </h1>
          <p className="mt-2 mb-8 text-center text-muted">What would you like to ask today?</p>
          {composer}
          <PrivacyNote />
        </div>
        {dialog}
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-col">
      <div className="mx-auto w-full max-w-3xl flex-1 px-4 pt-8 pb-4">
        <MessageList messages={messages} pending={pending} />
      </div>
      <div className="sticky bottom-0 bg-gradient-to-t from-background from-70% to-transparent px-4 pt-4 pb-3">
        <div className="mx-auto max-w-3xl">
          {composer}
          <PrivacyNote />
        </div>
      </div>
      {dialog}
    </div>
  );
}
