"""Generate a new MESSAGE_ENCRYPTION_KEY (32 random bytes, base64).

Usage (from backend/):  uv run python scripts/generate_key.py

Put the output in backend/.env as MESSAGE_ENCRYPTION_KEY=... and store a copy
in your password manager. Losing the key makes stored messages unreadable;
leaking it lets anyone with database access read them. Never commit it.
"""

import base64
import secrets

print(base64.b64encode(secrets.token_bytes(32)).decode())
