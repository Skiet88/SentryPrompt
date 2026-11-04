import { Menu, SquarePen } from "lucide-react";
import { useState } from "react";
import { Link, Outlet } from "react-router";

import { useProfile } from "@/auth/authState";
import { Logo } from "@/components/Logo";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Sheet } from "@/components/ui/sheet";
import { useMediaQuery } from "@/lib/useMediaQuery";

import { Sidebar } from "./Sidebar";

/** The signed-in layout: sidebar on the left (a slide-in menu on phones), page on the right. */
export function AppShell() {
  const profile = useProfile();
  const [menuOpen, setMenuOpen] = useState(false);
  const wide = useMediaQuery("(min-width: 768px)");
  const close = () => setMenuOpen(false);

  return (
    <div className="flex h-full">
      {wide ? (
        <aside className="w-72 shrink-0 border-r border-border bg-sidebar">
          <Sidebar />
        </aside>
      ) : (
        <Sheet open={menuOpen} onOpenChange={setMenuOpen} title="Menu">
          <Sidebar onNavigate={close} />
        </Sheet>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        {!wide && (
          <header className="flex h-14 items-center justify-between border-b border-border px-2">
            <Button variant="ghost" size="icon" onClick={() => setMenuOpen(true)} aria-label="Open menu">
              <Menu aria-hidden />
            </Button>
            <Link to="/" aria-label="SentryPrompt home">
              <Logo className="[&>span:last-child]:text-base" />
            </Link>
            <Button asChild variant="ghost" size="icon">
              <Link to="/" aria-label="New chat">
                <SquarePen aria-hidden />
              </Link>
            </Button>
          </header>
        )}

        {profile.status === "suspended" && (
          <Alert tone="warning" className="m-3 mb-0 rounded-lg">
            Your account is suspended, so you can't send prompts. You can still view and delete your chats. Contact
            your administrator if you think this is a mistake.
          </Alert>
        )}

        <main className="min-h-0 flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
