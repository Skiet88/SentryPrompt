import type { AccountStatus } from "@/api/types";
import { cn } from "@/lib/utils";

export function StatusBadge({ status }: { status: AccountStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        status === "active" ? "bg-primary-soft text-primary" : "bg-warning-soft text-warning",
      )}
    >
      {status === "active" ? "Active" : "Suspended"}
    </span>
  );
}
