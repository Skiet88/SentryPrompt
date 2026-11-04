from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain import User


class IAuthService(ABC):
    @abstractmethod
    async def authenticate(self, access_token: str) -> User:
        """The logged-in user, or AuthenticationError / AuthUnavailableError."""

    @abstractmethod
    def require_active(self, user: User) -> User:
        """Verified and not suspended (FR-014, FR-021), else ForbiddenError."""

    @abstractmethod
    def require_admin(self, user: User) -> User:
        """An active admin (FR-021), else ForbiddenError."""

    @abstractmethod
    async def update_display_name(self, user: User, display_name: str) -> User: ...

    @abstractmethod
    async def delete_account(self, user: User) -> None: ...
