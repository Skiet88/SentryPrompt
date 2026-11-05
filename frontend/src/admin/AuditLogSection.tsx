import { useEffect, useState } from "react";

import { ApiError } from "@/api/apiClient";
import { ADMIN_PAGE_SIZE } from "@/api/adminApi";
import type { AuditLogEntry } from "@/api/types";
import { useServices } from "@/app/services";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { fullTime, messageTime } from "@/lib/dates";

type Load = { status: "loading" } | { status: "ready"; entries: AuditLogEntry[] } | { status: "failed"; message: string };

/**
 * Every suspension and reinstatement, newest first (FR-022). Read-only: the
 * log can't be changed or deleted, here or in the database.
 */
export function AuditLogSection({ names, version }: { names: Map<string, string>; version: number }) {
  const { admin } = useServices();
  const [offset, setOffset] = useState(0);
  const [load, setLoad] = useState<Load>({ status: "loading" });

  useEffect(() => {
    let active = true;
    admin
      .auditLog(offset)
      .then((entries) => active && setLoad({ status: "ready", entries }))
      .catch(
        (e: unknown) =>
          active &&
          setLoad({ status: "failed", message: e instanceof ApiError ? e.message : "Couldn't load the activity log." }),
      );
    return () => {
      active = false;
    };
  }, [admin, offset, version]);

  // Accounts not on the loaded page (or deleted since) show a short ID instead of a name.
  const who = (id: string) => names.get(id) ?? `Account ${id.slice(0, 8)}`;

  return (
    <section aria-labelledby="audit-heading" className="rounded-2xl border border-border bg-surface">
      <div className="p-5 pb-3">
        <h2 id="audit-heading" className="font-semibold">
          Activity log
        </h2>
        <p className="mt-0.5 text-sm text-muted">Every suspension and reinstatement. Entries can't be changed or deleted.</p>
      </div>
      {load.status === "loading" && (
        <div className="px-5 pb-5">
          <Spinner label="Loading activity" />
        </div>
      )}
      {load.status === "failed" && (
        <div className="px-5 pb-5">
          <Alert tone="error">{load.message}</Alert>
        </div>
      )}
      {load.status === "ready" && load.entries.length === 0 && offset === 0 && (
        <p className="px-5 pb-5 text-sm text-muted">No actions recorded yet.</p>
      )}
      {load.status === "ready" && load.entries.length > 0 && (
        <ol className="border-t border-border">
          {load.entries.map((e) => (
            <li key={e.logId} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-border px-5 py-3 text-sm last:border-b-0">
              <time dateTime={e.timestamp} title={fullTime(e.timestamp)} className="w-36 shrink-0 text-xs text-muted">
                {messageTime(e.timestamp)}
              </time>
              <span className="min-w-0 flex-1">
                <strong className="font-medium">{who(e.adminUserId)}</strong>{" "}
                {e.actionType === "suspend" ? "suspended" : "reinstated"}{" "}
                <strong className="font-medium">{who(e.targetUserId)}</strong>
                {e.details && <span className="block text-muted break-words whitespace-pre-wrap">“{e.details}”</span>}
              </span>
            </li>
          ))}
        </ol>
      )}
      {load.status === "ready" && (offset > 0 || load.entries.length === ADMIN_PAGE_SIZE) && (
        <div className="flex justify-end gap-2 border-t border-border px-5 py-3">
          <Button size="sm" variant="secondary" disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - ADMIN_PAGE_SIZE))}>
            Newer
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={load.entries.length < ADMIN_PAGE_SIZE}
            onClick={() => setOffset((o) => o + ADMIN_PAGE_SIZE)}
          >
            Older
          </Button>
        </div>
      )}
    </section>
  );
}
