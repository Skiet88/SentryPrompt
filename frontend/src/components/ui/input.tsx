import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-lg border border-border bg-surface px-3 text-[15px] text-foreground",
        "placeholder:text-muted focus-visible:border-primary aria-[invalid=true]:border-danger",
        className,
      )}
      {...props}
    />
  );
}
