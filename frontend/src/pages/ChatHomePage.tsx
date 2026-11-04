import { ArrowUp, ShieldCheck } from "lucide-react";

import { useProfile } from "@/auth/authState";
import { Button } from "@/components/ui/button";
import { displayNameOf } from "@/layout/UserMenu";

export function greeting(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/** A new chat: one greeting, one box to type in, and one line on what happens to your prompt. */
export function ChatHomePage() {
  const profile = useProfile();
  const name = displayNameOf(profile);

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-2xl">
        <h1 className="text-center text-3xl font-semibold tracking-tight">
          {greeting(new Date().getHours())}, {name}
        </h1>
        <p className="mt-2 text-center text-muted">What would you like to ask today?</p>

        <form className="mt-8" onSubmit={(e) => e.preventDefault()}>
          <div className="rounded-2xl border border-border bg-surface p-3 shadow-sm focus-within:border-primary">
            <label htmlFor="prompt" className="sr-only">
              Your prompt
            </label>
            <textarea
              id="prompt"
              rows={3}
              disabled
              placeholder="Chatting is coming in the next update…"
              className="w-full resize-none bg-transparent px-1.5 py-1 text-[15px] outline-none placeholder:text-muted"
            />
            <div className="flex justify-end">
              <Button type="submit" size="icon" className="rounded-full" disabled aria-label="Send">
                <ArrowUp aria-hidden />
              </Button>
            </div>
          </div>
        </form>

        <p className="mt-3 text-center text-xs text-balance text-muted">
          <ShieldCheck className="mr-1 inline size-3.5 align-[-2px] text-primary" aria-hidden />
          Your prompt is checked for personal information before it reaches the AI.
        </p>
      </div>
    </div>
  );
}
