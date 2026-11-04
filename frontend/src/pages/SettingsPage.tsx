import { useState, type FormEvent } from "react";

import { ApiError } from "@/api/apiClient";
import { MAX_DISPLAY_NAME_LENGTH } from "@/api/profileApi";
import { useServices } from "@/app/services";
import { useAuth, useProfile } from "@/auth/authState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";

function message(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

/** Your name, your email, and deleting your account (FR-018, FR-020). */
export function SettingsPage() {
  const profile = useProfile();
  const { setProfile, signOut } = useAuth();
  const { profile: profileApi } = useServices();
  const [name, setName] = useState(profile.displayName);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<{ tone: "success" | "error"; text: string }>();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const suspended = profile.status === "suspended";
  const tooLong = name.trim().length > MAX_DISPLAY_NAME_LENGTH;
  const unchanged = name.trim() === profile.displayName;

  async function save(event: FormEvent) {
    event.preventDefault();
    if (tooLong || unchanged) return;
    setSaving(true);
    setResult(undefined);
    try {
      const updated = await profileApi.updateDisplayName(name.trim());
      setProfile(updated);
      setName(updated.displayName);
      setResult({ tone: "success", text: "Saved." });
    } catch (e) {
      setResult({ tone: "error", text: message(e) });
    } finally {
      setSaving(false);
    }
  }

  async function deleteAccount() {
    try {
      await profileApi.deleteAccount();
    } catch (e) {
      throw new Error(message(e), { cause: e });
    }
    // The login page shows this once the app has logged out.
    await signOut("Your account and all your chats have been deleted.");
  }

  return (
    <div className="mx-auto max-w-2xl px-5 py-10">
      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>

      <section aria-labelledby="profile-heading" className="mt-8 rounded-2xl border border-border bg-surface p-5">
        <h2 id="profile-heading" className="font-semibold">
          Profile
        </h2>
        <form onSubmit={save} noValidate className="mt-4 space-y-4">
          <FormField
            label="Display name"
            hint={suspended ? "You can't change your name while your account is suspended." : "Shown in the greeting and menu."}
            error={tooLong ? `Use at most ${MAX_DISPLAY_NAME_LENGTH} characters.` : undefined}
          >
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              disabled={suspended}
              placeholder={profile.email.split("@")[0]}
            />
          </FormField>
          <FormField label="Email" hint="Your login email can't be changed here.">
            <Input value={profile.email} readOnly disabled />
          </FormField>
          {result && <Alert tone={result.tone}>{result.text}</Alert>}
          <Button type="submit" disabled={suspended || saving || unchanged || tooLong}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </form>
      </section>

      <section aria-labelledby="danger-heading" className="mt-6 rounded-2xl border border-danger/30 bg-surface p-5">
        <h2 id="danger-heading" className="font-semibold">
          Delete account
        </h2>
        <p className="mt-1.5 text-sm text-muted">
          Permanently deletes your account and all your chats. This can't be undone.
        </p>
        <Button variant="danger" className="mt-4" onClick={() => setConfirmOpen(true)}>
          Delete my account
        </Button>
      </section>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Delete your account?"
        confirmLabel="Delete my account"
        busyLabel="Deleting…"
        confirmWord="delete"
        onConfirm={deleteAccount}
      >
        <p>Your account, profile and every chat will be deleted permanently. You'll be logged out.</p>
      </ConfirmDialog>
    </div>
  );
}
