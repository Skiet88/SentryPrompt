"""Get a Supabase access token for testing the API in development.

Usage (from backend/):  uv run python scripts/dev_login.py

Signs in with your own test account (email + password, typed here and not
shown) and copies the access token to your clipboard, ready to paste into
the Swagger UI's Authorize button at http://localhost:8000/docs. The token is
not printed, so it doesn't end up in terminal history or screenshots. If no
clipboard tool is found, run with --print to show it instead.

The token works like a password for about an hour: don't share it, paste it
into chats, or save it in files. Refuses to run when APP_ENV=production.
"""

from __future__ import annotations

import getpass
import shutil
import subprocess
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import Settings

CLIPBOARD_COMMANDS = (
    ["clip"],  # Windows
    ["pbcopy"],  # macOS
    ["wl-copy"],  # Linux (Wayland)
    ["xclip", "-selection", "clipboard"],  # Linux (X11)
)


def copy_to_clipboard(value: str) -> bool:
    for command in CLIPBOARD_COMMANDS:
        if shutil.which(command[0]):
            # Fixed command from the list above; the token goes in via stdin.
            result = subprocess.run(command, input=value.encode(), check=False)  # noqa: S603
            return result.returncode == 0
    return False


def main() -> int:
    settings = Settings()
    if settings.is_production:
        print("Refusing to run with APP_ENV=production.")
        return 1
    if not settings.supabase_url or not settings.supabase_publishable_key:
        print("Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in backend/.env first.")
        return 1

    email = input("Test account email: ").strip()
    password = getpass.getpass("Password (not shown): ")
    try:
        response = httpx.post(
            f"{settings.supabase_url}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": settings.supabase_publishable_key},
            json={"email": email, "password": password},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        print(f"Could not reach Supabase ({type(exc).__name__}).")
        return 1
    finally:
        password = ""  # drop the reference as soon as possible

    if response.status_code != 200:
        # Supabase's error code only (e.g. invalid_credentials, email_not_confirmed).
        try:
            code = response.json().get("error_code") or response.json().get("error") or "unknown"
        except ValueError:
            code = "unknown"
        print(f"Sign-in failed: HTTP {response.status_code} ({code}).")
        return 1

    data = response.json()
    token, minutes = data["access_token"], data.get("expires_in", 3600) // 60
    if "--print" in sys.argv[1:]:
        print(f"\nAccess token (valid for about {minutes} minutes):\n\n{token}\n")
    elif copy_to_clipboard(token):
        print(f"\nToken copied to your clipboard (valid for about {minutes} minutes).")
    else:
        print("\nNo clipboard tool found. Run again with --print to show the token.")
        return 1
    print("In http://localhost:8000/docs click Authorize, paste with Ctrl+V, then Authorize.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
