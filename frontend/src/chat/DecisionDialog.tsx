import * as Dialog from "@radix-ui/react-dialog";
import { ShieldAlert } from "lucide-react";
import { useRef } from "react";

import type { Flag, Screening } from "@/api/types";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

import { categoryLabel } from "./categories";
import { highlightSegments } from "./highlight";

export interface PendingDecision {
  text: string;
  screening: Screening;
}

function uniqueByCategory(flags: Flag[]): Flag[] {
  const seen = new Set<string>();
  return flags.filter((f) => !seen.has(f.category) && seen.add(f.category));
}

function joinLabels(flags: Flag[]): string {
  // "ID number" keeps its capitals; "Health information" becomes "health information".
  const labels = flags.map((f) => categoryLabel(f.category).replace(/^[A-Z](?![A-Z])/, (c) => c.toLowerCase()));
  if (labels.length <= 1) return labels[0] ?? "";
  return `${labels.slice(0, -1).join(", ")} and ${labels.at(-1)}`;
}

/**
 * Shown when screening found something (FR-007, FR-008). The safe choice,
 * editing the prompt, is the main button and has focus; sending anyway is
 * possible, and the dialog says exactly what the AI will and won't see.
 */
export function DecisionDialog({
  decision,
  onEdit,
  onSendAnyway,
}: {
  decision: PendingDecision | null;
  onEdit: () => void;
  onSendAnyway: () => void;
}) {
  const editButton = useRef<HTMLButtonElement>(null);
  const flags = decision ? uniqueByCategory(decision.screening.flags) : [];
  const hidden = flags.filter((f) => f.detectorSource === "rule");
  const shown = flags.filter((f) => f.detectorSource === "context");
  const segments = decision ? highlightSegments(decision.text, decision.screening.flags) : [];

  return (
    <Dialog.Root open={decision !== null} onOpenChange={(open) => !open && onEdit()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
        <Dialog.Content
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            editButton.current?.focus();
          }}
          className="fixed top-1/2 left-1/2 z-50 flex max-h-[90vh] w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl bg-surface shadow-2xl outline-none"
        >
          <div className="flex gap-3 px-5 pt-5">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-warning-soft text-warning">
              <ShieldAlert className="size-5" aria-hidden />
            </span>
            <div>
              <Dialog.Title className="text-lg font-semibold">
                {flags.length > 0 ? "Check before you send" : "We couldn't fully check this prompt"}
              </Dialog.Title>
              <Dialog.Description className="mt-0.5 text-sm text-muted">
                {flags.length > 0
                  ? "Your prompt may contain personal information."
                  : "Please read it once more before sending."}
              </Dialog.Description>
            </div>
          </div>

          <div className="mt-4 min-h-0 flex-1 space-y-4 overflow-y-auto px-5">
            {segments.length > 0 && (
              <p className="max-h-36 overflow-y-auto rounded-lg border border-border bg-background p-3 text-sm break-words whitespace-pre-wrap">
                {segments.map((s, i) =>
                  s.flagged ? (
                    <mark key={i} className="rounded bg-warning-soft px-0.5 text-warning">
                      {s.text}
                    </mark>
                  ) : (
                    <span key={i}>{s.text}</span>
                  ),
                )}
              </p>
            )}

            {flags.length > 0 && (
              <ul className="space-y-3">
                {flags.map((f) => (
                  <li key={f.category} className="text-sm">
                    <span className="font-medium">{categoryLabel(f.category)}</span>
                    <p className="text-muted">{f.explanation}</p>
                  </li>
                ))}
              </ul>
            )}

            {decision?.screening.notice && <Alert tone="warning">{decision.screening.notice}</Alert>}

            {flags.length > 0 && (
              <p className="rounded-lg bg-hover px-3 py-2.5 text-sm">
                If you send anyway:{" "}
                {hidden.length > 0 && <>the {joinLabels(hidden)} will be hidden from the AI. </>}
                {shown.length > 0 && <>The {joinLabels(shown)} will be sent as you wrote it.</>}
              </p>
            )}
          </div>

          <div className="flex flex-col-reverse gap-2 p-5 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={onSendAnyway}>
              Send anyway
            </Button>
            <Button ref={editButton} onClick={onEdit}>
              Edit my prompt
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
