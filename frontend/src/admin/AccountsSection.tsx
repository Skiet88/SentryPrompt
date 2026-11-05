import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { ApiError } from "@/api/apiClient";
import { ADMIN_PAGE_SIZE } from "@/api/adminApi";
import type { AdminUser, StatusChange } from "@/api/types";
import { useServices } from "@/app/services";
import { useProfile } from "@/auth/authState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { fullTime, messageTime } from "@/lib/dates";

import { StatusBadge } from "./StatusBadge";
import { StatusDialog, type StatusAction } from "./StatusDialog";

type Load = { status: "loading" } | { status: "ready"; users: AdminUser[] } | { status: "failed"; message: string };

function errorText(e: unknown): string {
  return e instanceof ApiError ? e.message : "Something went wrong. Please try again.";
}

/** Accounts, with suspend and reinstate (FR-021). Account-level fields only. */
export function AccountsSection({
  onUsersLoaded,
  onChanged,
}: {
  onUsersLoaded: (users: AdminUser[]) => void;
  onChanged: () => void;
}) {
  const { admin } = useServices();
  const me = useProfile();
  const [page, setPage] = useState(1);
  const [load, setLoad] = useState<Load>({ status: "loading" });
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<{ user: AdminUser; action: StatusAction } | null>(null);
  const [notice, setNotice] = useState<{ tone: "success" | "warning"; text: string }>();

  useEffect(() => {
    let active = true;
    admin
      .listUsers(page)
      .then((users) => {
        if (!active) return;
        setLoad({ status: "ready", users });
        onUsersLoaded(users);
      })
      .catch((e: unknown) => active && setLoad({ status: "failed", message: errorText(e) }));
    return () => {
      active = false;
    };
  }, [admin, page, onUsersLoaded]);

  const shown = useMemo(() => {
    if (load.status !== "ready") return [];
    const q = query.trim().toLowerCase();
    return q
      ? load.users.filter((u) => u.email.toLowerCase().includes(q) || u.displayName.toLowerCase().includes(q))
      : load.users;
  }, [load, query]);

  function goTo(next: number) {
    setLoad({ status: "loading" });
    setPage(next);
  }

  async function apply(reason: string) {
    if (!pending) return;
    const { user, action } = pending;
    let result: StatusChange;
    try {
      result = action === "suspend" ? await admin.suspend(user.userId, reason) : await admin.reinstate(user.userId, reason);
    } catch (e) {
      throw new Error(errorText(e), { cause: e });
    }
    setLoad((current) =>
      current.status === "ready"
        ? { ...current, users: current.users.map((u) => (u.userId === user.userId ? { ...u, status: result.status } : u)) }
        : current,
    );
    const name = user.displayName || user.email;
    setNotice(
      result.loginBlockUpdated
        ? { tone: "success", text: `${name} is now ${result.status === "suspended" ? "suspended" : "active"}.` }
        : {
            tone: "warning",
            text: `${name} is ${result.status === "suspended" ? "blocked" : "unblocked"} in SentryPrompt, but the login block couldn't be updated. Do it again to retry.`,
          },
    );
    setPending(null);
    onChanged();
  }

  return (
    <section aria-labelledby="accounts-heading" className="rounded-2xl border border-border bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 p-5 pb-3">
        <h2 id="accounts-heading" className="font-semibold">
          Accounts
        </h2>
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted" aria-hidden />
          <label htmlFor="account-search" className="sr-only">
            Search accounts on this page
          </label>
          <Input
            id="account-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search name or email"
            className="h-9 pl-9 text-sm"
          />
        </div>
      </div>

      {notice && (
        <div className="px-5 pb-3">
          <Alert tone={notice.tone}>{notice.text}</Alert>
        </div>
      )}

      {load.status === "loading" && (
        <div className="px-5 pb-5">
          <Spinner label="Loading accounts" />
        </div>
      )}
      {load.status === "failed" && (
        <div className="px-5 pb-5">
          <Alert tone="error">{load.message}</Alert>
        </div>
      )}
      {load.status === "ready" && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="border-y border-border text-left text-xs text-muted">
                <tr>
                  <th scope="col" className="px-5 py-2 font-medium">Name</th>
                  <th scope="col" className="px-3 py-2 font-medium">Email</th>
                  <th scope="col" className="px-3 py-2 font-medium">Joined</th>
                  <th scope="col" className="px-3 py-2 font-medium">Status</th>
                  <th scope="col" className="px-5 py-2 text-right font-medium">
                    <span className="sr-only">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.map((u) => {
                  const self = u.userId === me.userId;
                  const isAdmin = u.role === "admin";
                  return (
                    <tr key={u.userId} className="border-b border-border last:border-b-0">
                      <td className="px-5 py-3">
                        <span className="font-medium">{u.displayName || "—"}</span>
                        {isAdmin && <span className="ml-2 text-xs text-muted">Admin</span>}
                      </td>
                      <td className="px-3 py-3">
                        <span className="break-all">{u.email}</span>
                        {!u.emailVerified && <span className="block text-xs text-warning">Not verified</span>}
                      </td>
                      <td className="px-3 py-3 text-muted">
                        {u.createdAt ? <time dateTime={u.createdAt} title={fullTime(u.createdAt)}>{messageTime(u.createdAt)}</time> : "—"}
                      </td>
                      <td className="px-3 py-3">
                        <StatusBadge status={u.status} />
                      </td>
                      <td className="px-5 py-3 text-right">
                        {self ? (
                          <span className="text-xs text-muted">You</span>
                        ) : u.status === "active" ? (
                          !isAdmin && (
                            <Button size="sm" variant="secondary" onClick={() => setPending({ user: u, action: "suspend" })}>
                              Suspend
                            </Button>
                          )
                        ) : (
                          <Button size="sm" variant="secondary" onClick={() => setPending({ user: u, action: "reinstate" })}>
                            Reinstate
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {shown.length === 0 && (
            <p className="px-5 py-4 text-sm text-muted">{query ? "No accounts on this page match." : "No accounts yet."}</p>
          )}
          <div className="flex items-center justify-between gap-3 border-t border-border px-5 py-3 text-sm text-muted">
            <span>Page {page}</span>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" disabled={page === 1} onClick={() => goTo(page - 1)}>
                Previous
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={load.users.length < ADMIN_PAGE_SIZE}
                onClick={() => goTo(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      <StatusDialog
        target={pending?.user ?? null}
        action={pending?.action ?? "suspend"}
        onCancel={() => setPending(null)}
        onConfirm={apply}
      />
    </section>
  );
}
