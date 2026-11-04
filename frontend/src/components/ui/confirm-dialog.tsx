import * as Dialog from "@radix-ui/react-dialog";
import { useId, useState, type ReactNode } from "react";

import { Alert } from "./alert";
import { Button } from "./button";
import { Input } from "./input";

/**
 * Asks before something that can't be undone. Cancel has focus, so pressing
 * Enter by habit never deletes anything. With confirmWord, the person must
 * type that word first (for the most serious actions).
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  children,
  confirmLabel,
  busyLabel,
  confirmWord,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
  confirmLabel: string;
  busyLabel: string;
  confirmWord?: string;
  onConfirm: () => Promise<void>;
}) {
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const inputId = useId();
  const ready = !confirmWord || typed.trim().toLowerCase() === confirmWord.toLowerCase();

  function change(next: boolean) {
    if (busy) return;
    if (!next) {
      setTyped("");
      setError(undefined);
    }
    onOpenChange(next);
  }

  async function confirm() {
    setBusy(true);
    setError(undefined);
    try {
      await onConfirm();
      setTyped("");
    } catch (e) {
      setError(e instanceof Error && e.message ? e.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={change}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-50 w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-surface p-5 shadow-2xl outline-none">
          <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
          <Dialog.Description asChild>
            <div className="mt-2 space-y-2 text-sm text-muted">{children}</div>
          </Dialog.Description>
          {confirmWord && (
            <div className="mt-4 space-y-1.5">
              <label htmlFor={inputId} className="text-sm font-medium">
                Type <strong>{confirmWord}</strong> to confirm
              </label>
              <Input id={inputId} value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" />
            </div>
          )}
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
            <Button variant="danger" disabled={!ready || busy} onClick={() => void confirm()}>
              {busy ? busyLabel : confirmLabel}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
