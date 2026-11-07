import * as Dialog from "@radix-ui/react-dialog";
import { useId, useState } from "react";

import { MAX_REASON_LENGTH } from "@/api/adminApi";
import type { AdminUser } from "@/api/types";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export type StatusAction = "suspend" | "reinstate";

/** Confirms a suspension or reinstatement, with an optional reason for the audit log. */
export function StatusDialog({
  target,
  action,
  onCancel,
  onConfirm,
}: {
  target: AdminUser | null;
  action: StatusAction;
  onCancel: () => void;
  onConfirm: (reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const reasonId = useId();
  const tooLong = reason.trim().length > MAX_REASON_LENGTH;
  const suspend = action === "suspend";
  const name = target ? target.displayName || target.email : "";

  function close() {
    if (busy) return;
    setReason("");
    setError(undefined);
    onCancel();
  }

  async function confirm() {
    setBusy(true);
    setError(undefined);
    try {
      await onConfirm(reason.trim());
      setReason("");
    } catch (e) {
      setError(e instanceof Error && e.message ? e.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog.Root open={target !== null} onOpenChange={(open) => !open && close()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-surface p-5 shadow-2xl outline-none">
          <Dialog.Title className="text-lg font-semibold">
            {suspend ? "Suspend" : "Reinstate"} {name}?
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-muted">
            {suspend
              ? "They will be logged out and can't log in or send prompts until reinstated. They can still delete their account."
              : "They will be able to log in and use SentryPrompt again."}
          </Dialog.Description>
          <div className="mt-4 space-y-1.5">
            <label htmlFor={reasonId} className="text-sm font-medium">
              Reason <span className="font-normal text-muted">(optional, saved in the activity log)</span>
            </label>
            <textarea
              id={reasonId}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              aria-invalid={tooLong || undefined}
              className="w-full resize-none rounded-lg border border-border bg-surface px-3 py-2 text-[15px] focus-visible:border-primary aria-[invalid=true]:border-danger"
            />
            <p className={tooLong ? "text-xs text-danger" : "text-xs text-muted"}>
              {tooLong
                ? `Use at most ${MAX_REASON_LENGTH} characters.`
                : "Don't include personal details or anything from their chats."}
            </p>
          </div>
          {error && (
            <Alert tone="error" className="mt-4">
              {error}
            </Alert>
          )}
          <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Dialog.Close asChild>
              <Button variant="secondary" disabled={busy}>
                Cancel
              </Button>
            </Dialog.Close>
            <Button variant={suspend ? "danger" : "primary"} disabled={busy || tooLong} onClick={() => void confirm()}>
              {busy ? (suspend ? "Suspending…" : "Reinstating…") : suspend ? "Suspend" : "Reinstate"}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
