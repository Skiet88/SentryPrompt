import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ className, showName = true }: { className?: string; showName?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-semibold tracking-tight", className)}>
      <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <ShieldCheck className="size-[18px]" aria-hidden />
      </span>
      {showName && <span className="text-[17px]">SentryPrompt</span>}
    </span>
  );
}
