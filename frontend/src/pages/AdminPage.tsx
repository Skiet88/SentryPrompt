import { ShieldCheck } from "lucide-react";
import { useCallback, useState } from "react";
import { Link } from "react-router";

import type { AdminUser } from "@/api/types";
import { AccountsSection } from "@/admin/AccountsSection";
import { AuditLogSection } from "@/admin/AuditLogSection";
import { useProfile } from "@/auth/authState";
import { Button } from "@/components/ui/button";

/**
 * The admin panel (FR-021, FR-022): accounts and the activity log, on one
 * page. Account-level only: nothing here can show or fetch chats (NFR-013).
 * The backend checks the admin role on every request; this page only hides
 * itself from students so they aren't shown a broken screen.
 */
export function AdminPage() {
  const profile = useProfile();
  const [names, setNames] = useState<Map<string, string>>(new Map());
  const [version, setVersion] = useState(0);

  const remember = useCallback((users: AdminUser[]) => {
    setNames((current) => {
      const next = new Map(current);
      for (const u of users) next.set(u.userId, u.displayName || u.email);
      return next;
    });
  }, []);
  const changed = useCallback(() => setVersion((v) => v + 1), []);

  if (profile.role !== "admin") {
    return (
      <div className="mx-auto max-w-2xl px-5 py-10">
        <h1 className="text-2xl font-semibold tracking-tight">Admin panel</h1>
        <p className="mt-2 text-muted">This page is for administrators.</p>
        <Button asChild className="mt-5">
          <Link to="/">Back to chat</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-5 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Admin panel</h1>
        <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-3 py-1 text-xs font-medium text-primary">
          <ShieldCheck className="size-3.5" aria-hidden />
          Account-level access only: admins can't see anyone's chats
        </p>
      </div>
      <AccountsSection onUsersLoaded={remember} onChanged={changed} />
      <AuditLogSection names={names} version={version} />
    </div>
  );
}
