import { ShieldCheck } from "lucide-react";

export function PrivacyNote() {
  return (
    <p className="mt-2.5 text-center text-xs text-balance text-muted">
      <ShieldCheck className="mr-1 inline size-3.5 align-[-2px] text-primary" aria-hidden />
      Your prompt is checked for personal information before it reaches the AI.
    </p>
  );
}
