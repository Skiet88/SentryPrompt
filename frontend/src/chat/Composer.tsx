import { ArrowUp } from "lucide-react";
import { useEffect, useRef, type FormEvent, type KeyboardEvent } from "react";

import { MAX_PROMPT_LENGTH } from "@/api/conversationApi";
import { Button } from "@/components/ui/button";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { cn } from "@/lib/utils";

import { characterCount } from "./highlight";

const COUNTER_FROM = MAX_PROMPT_LENGTH - 500;

/** The prompt box. Enter sends on a keyboard; Shift+Enter (or Enter on a phone) adds a new line. */
export function Composer({
  value,
  onChange,
  onSend,
  busy,
  disabledReason,
  focusSignal,
}: {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  busy: boolean;
  disabledReason?: string;
  focusSignal?: number;
}) {
  const textarea = useRef<HTMLTextAreaElement>(null);
  const touch = useMediaQuery("(pointer: coarse)");
  const count = characterCount(value);
  const tooLong = count > MAX_PROMPT_LENGTH;
  const canSend = !busy && !disabledReason && value.trim().length > 0 && !tooLong;

  useEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
  }, [value]);

  useEffect(() => {
    if (focusSignal) textarea.current?.focus();
  }, [focusSignal]);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (canSend) onSend();
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !touch && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (canSend) onSend();
    }
  }

  return (
    <form onSubmit={submit}>
      <div
        className={cn(
          "rounded-2xl border border-border bg-surface p-2.5 shadow-sm focus-within:border-primary",
          tooLong && "border-danger focus-within:border-danger",
        )}
      >
        <label htmlFor="prompt" className="sr-only">
          Your prompt
        </label>
        <textarea
          id="prompt"
          ref={textarea}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={keyDown}
          disabled={Boolean(disabledReason)}
          placeholder={disabledReason ?? "Ask anything…"}
          aria-describedby={count >= COUNTER_FROM ? "prompt-count" : undefined}
          className="max-h-60 min-h-11 w-full resize-none bg-transparent px-2 py-2 text-[15px] outline-none placeholder:text-muted"
        />
        <div className="flex items-center justify-end gap-3">
          {count >= COUNTER_FROM && (
            <span id="prompt-count" className={cn("text-xs", tooLong ? "text-danger" : "text-muted")}>
              {count.toLocaleString()} / {MAX_PROMPT_LENGTH.toLocaleString()}
            </span>
          )}
          <Button type="submit" size="icon" className="rounded-full" disabled={!canSend} aria-label="Send">
            <ArrowUp aria-hidden />
          </Button>
        </div>
      </div>
    </form>
  );
}
