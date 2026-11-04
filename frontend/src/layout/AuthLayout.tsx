import { EyeOff, ShieldCheck, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";

import { Logo } from "@/components/Logo";

const POINTS = [
  { Icon: ShieldCheck, text: "Every prompt is checked for personal information before it reaches the AI." },
  { Icon: EyeOff, text: "ID numbers, card numbers and contact details are hidden from the AI automatically." },
  { Icon: SlidersHorizontal, text: "You stay in control: edit your prompt, or send it anyway." },
];

/**
 * Login, sign-up and password pages. On wide screens the left half explains
 * what SentryPrompt is in one glance; on phones only the form is shown.
 */
export function AuthLayout({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="flex min-h-full">
      <aside className="hidden w-[44%] max-w-xl flex-col justify-between bg-sidebar p-10 lg:flex">
        <Logo />
        <div className="max-w-md space-y-8">
          <h2 className="text-4xl leading-tight font-semibold tracking-tight">
            Use AI for your studies, <span className="text-primary">without oversharing.</span>
          </h2>
          <ul className="space-y-5">
            {POINTS.map(({ Icon, text }) => (
              <li key={text} className="flex gap-3.5 text-[15px] text-muted">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary">
                  <Icon className="size-[18px]" aria-hidden />
                </span>
                <span className="pt-1.5">{text}</span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-muted">Built for students. Protects personal information under POPIA.</p>
      </aside>

      <main className="flex flex-1 items-center justify-center px-5 py-10">
        <div className="w-full max-w-sm">
          <Logo className="mb-10 lg:hidden" />
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {subtitle && <p className="mt-1.5 text-muted">{subtitle}</p>}
          <div className="mt-7">{children}</div>
        </div>
      </main>
    </div>
  );
}
