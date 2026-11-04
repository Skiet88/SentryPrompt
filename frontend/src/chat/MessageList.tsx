import { ShieldCheck } from "lucide-react";
import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/api/types";
import { Spinner } from "@/components/ui/spinner";
import { fullTime, messageTime } from "@/lib/dates";
import { cn } from "@/lib/utils";

import { RedactedText } from "./RedactedText";
import { SafeMarkdown } from "./SafeMarkdown";

function Timestamp({ iso, align }: { iso: string; align: "left" | "right" }) {
  const label = messageTime(iso);
  if (!label) return null;
  return (
    <time dateTime={iso} title={fullTime(iso)} className={cn("mt-1 block text-xs text-muted", align === "right" && "text-right")}>
      {label}
    </time>
  );
}

export interface PendingPrompt {
  text: string;
}

/** The conversation: your prompts on the right, the AI's replies on the left. */
export function MessageList({ messages, pending }: { messages: ChatMessage[]; pending: PendingPrompt | null }) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "end" });
  }, [messages.length, pending]);

  return (
    <div role="log" aria-label="Conversation" aria-live="polite" className="space-y-6">
      {messages.map((m) =>
        m.role === "user" ? (
          <div key={m.messageId} className="flex flex-col items-end">
            <div className="max-w-[85%] rounded-2xl bg-hover px-4 py-2.5 break-words whitespace-pre-wrap">
              <RedactedText text={m.content} />
            </div>
            <Timestamp iso={m.createdAt} align="right" />
          </div>
        ) : (
          <div key={m.messageId} className="break-words">
            <SafeMarkdown text={m.content} />
            <Timestamp iso={m.createdAt} align="left" />
          </div>
        ),
      )}
      {pending && (
        <>
          <div className="flex justify-end">
            <div className="max-w-[85%] rounded-2xl bg-hover px-4 py-2.5 break-words whitespace-pre-wrap opacity-70">
              {pending.text}
            </div>
          </div>
          <p className="flex items-center gap-2 text-sm text-muted">
            <Spinner className="size-4" label="" />
            <ShieldCheck className="size-4 text-primary" aria-hidden />
            Checking your prompt, then asking the AI…
          </p>
        </>
      )}
      <div ref={end} />
    </div>
  );
}
