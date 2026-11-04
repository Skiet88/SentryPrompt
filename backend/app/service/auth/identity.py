from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """Who a valid token belongs to, as confirmed by the identity provider."""

    user_id: str
    email: str
    email_verified: bool
