import { CircleAlert, CircleCheck, Info } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const STYLES = {
  error: { box: "bg-danger-soft text-danger", Icon: CircleAlert, role: "alert" },
  success: { box: "bg-primary-soft text-foreground", Icon: CircleCheck, role: "status" },
  info: { box: "bg-hover text-foreground", Icon: Info, role: "status" },
  warning: { box: "bg-warning-soft text-warning", Icon: CircleAlert, role: "status" },
} as const;

export function Alert({
  tone = "info",
  children,
  className,
}: {
  tone?: keyof typeof STYLES;
  children: ReactNode;
  className?: string;
}) {
  const { box, Icon, role } = STYLES[tone];
  return (
    <div role={role} className={cn("flex gap-2.5 rounded-lg px-3.5 py-3 text-sm", box, className)}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0">{children}</div>
    </div>
  );
}
