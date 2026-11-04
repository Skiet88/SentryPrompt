import { EyeOff } from "lucide-react";
import type { ReactNode } from "react";

import { categoryLabel } from "./categories";

const PLACEHOLDER = /\[REDACTED_([A-Z_]{1,40})\]/g;

/** The text with placeholders spelled out, e.g. for screen-reader labels. */
export function plainText(text: string): string {
  return text.replace(PLACEHOLDER, (_, category: string) => `(${categoryLabel(category).toLowerCase()} hidden)`);
}

/**
 * A sent prompt as stored: values the detector found were replaced before the
 * AI saw them. Each placeholder is shown as a small "hidden" badge so the
 * student can see exactly what was protected. Everything else is plain text.
 */
export function RedactedText({ text, compact = false }: { text: string; compact?: boolean }) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(PLACEHOLDER)) {
    const index = match.index;
    if (index > last) parts.push(text.slice(last, index));
    const label = categoryLabel(match[1] ?? "");
    parts.push(
      <span
        key={index}
        className={
          compact
            ? "mx-0.5 rounded bg-primary-soft px-1 text-xs font-medium text-primary"
            : "mx-0.5 inline-flex items-center gap-1 rounded-md bg-primary-soft px-1.5 py-px align-baseline text-[13px] font-medium text-primary"
        }
        title={`${label} hidden from the AI`}
      >
        {!compact && <EyeOff className="size-3" aria-hidden />}
        <span className="sr-only">Hidden: </span>
        {label}
      </span>,
    );
    last = index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}
