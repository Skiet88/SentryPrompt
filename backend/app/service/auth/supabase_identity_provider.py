"""Supabase Auth as the identity provider (option A, AUTH_DESIGN.md §0).

Every token is checked by Supabase's Auth API (GET /auth/v1/user), which
confirms the signature, expiry and that the session has not been logged out,
so logout takes effect immediately (FR-016).
"""

from __future__ import annotations

import logging
import uuid

import httpx
from pydantic import SecretStr

from app.exception import AuthenticationError, AuthUnavailableError, ConfigurationError

from .identity import IdentityRecord, VerifiedIdentity
from .identity_provider import IdentityProvider

logger = logging.getLogger(__name__)

# Supabase answers 401/403 for invalid, expired or logged-out tokens.
_REJECTED = {400, 401, 403, 404}


class SupabaseIdentityProvider(IdentityProvider):
    def __init__(
        self,
        supabase_url: str,
        secret_key: SecretStr | None,
        timeout_seconds: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ):
        if not supabase_url or secret_key is None:
            raise ConfigurationError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set for login")
        self._auth_url = supabase_url.rstrip("/") + "/auth/v1"
        self._secret_key = secret_key
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    def _api_headers(self) -> dict[str, str]:
        return {"apikey": self._secret_key.get_secret_value()}

    async def verify_token(self, access_token: str) -> VerifiedIdentity:
        try:
            response = await self._client.get(
                f"{self._auth_url}/user",
                headers={**self._api_headers(), "Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as exc:
            logger.warning("Supabase Auth unreachable: %s", type(exc).__name__)
            raise AuthUnavailableError("Login could not be checked right now.") from None

        if response.status_code in _REJECTED:
            raise AuthenticationError()
        if response.status_code != 200:
            logger.warning("Supabase Auth returned HTTP %s", response.status_code)
            raise AuthUnavailableError("Login could not be checked right now.")
        return self._identity_from(response)

    @staticmethod
    def _identity_from(response: httpx.Response) -> VerifiedIdentity:
        try:
            data = response.json()
            user_id = str(uuid.UUID(str(data["id"])))
            email = data.get("email") or ""
        except (ValueError, KeyError, TypeError):
            logger.warning("Supabase Auth returned an unreadable user")
            raise AuthUnavailableError("Login could not be checked right now.") from None
        return VerifiedIdentity(
            user_id=user_id,
            email=str(email),
            email_verified=bool(data.get("email_confirmed_at")),
        )

    async def delete_user(self, user_id: str) -> None:
        safe_id = str(uuid.UUID(user_id))  # never put unchecked input in a URL
        try:
            response = await self._client.delete(
                f"{self._auth_url}/admin/users/{safe_id}", headers=self._api_headers()
            )
        except httpx.HTTPError as exc:
            logger.warning("Supabase Auth unreachable: %s", type(exc).__name__)
            raise AuthUnavailableError("The account could not be deleted right now.") from None
        if response.status_code == 404:
            return  # already gone
        if response.status_code not in (200, 204):
            logger.warning("Supabase Auth delete returned HTTP %s", response.status_code)
            raise AuthUnavailableError("The account could not be deleted right now.")

    async def list_users(self, page: int, per_page: int) -> list[IdentityRecord]:
        try:
            response = await self._client.get(
                f"{self._auth_url}/admin/users",
                params={"page": page, "per_page": per_page},
                headers=self._api_headers(),
            )
        except httpx.HTTPError as exc:
            logger.warning("Supabase Auth unreachable: %s", type(exc).__name__)
            raise AuthUnavailableError("Accounts could not be loaded right now.") from None
        if response.status_code != 200:
            logger.warning("Supabase Auth list users returned HTTP %s", response.status_code)
            raise AuthUnavailableError("Accounts could not be loaded right now.")
        try:
            users = response.json()["users"]
            return [
                IdentityRecord(
                    user_id=str(uuid.UUID(str(u["id"]))),
                    email=str(u.get("email") or ""),
                    email_verified=bool(u.get("email_confirmed_at")),
                )
                for u in users
            ]
        except (ValueError, KeyError, TypeError):
            logger.warning("Supabase Auth returned an unreadable user list")
            raise AuthUnavailableError("Accounts could not be loaded right now.") from None

    async def set_banned(self, user_id: str, banned: bool) -> None:
        safe_id = str(uuid.UUID(user_id))
        # About 100 years: effectively until an admin reinstates the account.
        body = {"ban_duration": "876000h" if banned else "none"}
        try:
            response = await self._client.put(
                f"{self._auth_url}/admin/users/{safe_id}", json=body, headers=self._api_headers()
            )
        except httpx.HTTPError as exc:
            logger.warning("Supabase Auth unreachable: %s", type(exc).__name__)
            raise AuthUnavailableError("The login block could not be updated right now.") from None
        if response.status_code != 200:
            logger.warning("Supabase Auth ban update returned HTTP %s", response.status_code)
            raise AuthUnavailableError("The login block could not be updated right now.")
