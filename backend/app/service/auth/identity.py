from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """Who a valid token belongs to, as confirmed by the identity provider."""

    user_id: str
    email: str
    email_verified: bool


@dataclass(frozen=True, slots=True)
class IdentityRecord:
    """An account as the identity provider sees it (admin listing)."""

    user_id: str
    email: str
    email_verified: bool
