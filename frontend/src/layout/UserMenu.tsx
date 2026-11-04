import { ChevronsUpDown, LogOut, Settings, ShieldUser } from "lucide-react";
import { useNavigate } from "react-router";

import type { Profile } from "@/api/types";
import { useAuth, useProfile } from "@/auth/authState";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function displayNameOf(profile: Profile): string {
  return profile.displayName || profile.email.split("@")[0] || profile.email;
}

function initials(name: string): string {
  const parts = name.split(/[\s._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

/** The account button at the bottom of the sidebar, where people expect it. */
export function UserMenu({ onNavigate }: { onNavigate?: () => void }) {
  const profile = useProfile();
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const name = displayNameOf(profile);

  const go = (path: string) => {
    onNavigate?.();
    void navigate(path);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-hover data-[state=open]:bg-hover"
        aria-label="Account menu"
      >
        <span
          className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground"
          aria-hidden
        >
          {initials(name)}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium">{name}</span>
          <span className="block truncate text-xs text-muted">{profile.role === "admin" ? "Administrator" : "Student"}</span>
        </span>
        <ChevronsUpDown className="size-4 text-muted" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuContent side="top" align="start" className="w-[var(--radix-dropdown-menu-trigger-width)]">
        <DropdownMenuLabel className="truncate">{profile.email}</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => go("/settings")}>
          <Settings aria-hidden /> Settings
        </DropdownMenuItem>
        {profile.role === "admin" && (
          <DropdownMenuItem onSelect={() => go("/admin")}>
            <ShieldUser aria-hidden /> Admin panel
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void signOut()}>
          <LogOut aria-hidden /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
