"""Get a Supabase access token for testing the API in development.

Usage (from backend/):  uv run python scripts/dev_login.py

Signs in with your own test account (email + password, typed here and not
shown) and prints an access token to paste into the Swagger UI's Authorize
button at http://localhost:8000/docs. The token works like a password for
about an hour: don't share it, paste it into chats, or save it in files.
Refuses to run when APP_ENV=production.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import Settings


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
    print("\nAccess token (valid for about", data.get("expires_in", 3600) // 60, "minutes):\n")
    print(data["access_token"])
    print("\nIn http://localhost:8000/docs click Authorize and paste the token above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
