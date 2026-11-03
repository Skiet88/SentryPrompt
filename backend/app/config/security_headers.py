"""Adds security headers to every HTTP response (SECURITY_RULES.md §4)."""

from __future__ import annotations

from collections.abc import Iterable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# The API only returns JSON, so the page-level policy can be as strict as possible.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}
HSTS = "max-age=63072000; includeSubDomains"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, enable_hsts: bool, csp_exempt_paths: Iterable[str] = ()):
        """csp_exempt_paths: paths whose page needs scripts (the Swagger docs,
        which are only served outside production)."""
        self.app = app
        self._enable_hsts = enable_hsts
        self._csp_exempt = frozenset(csp_exempt_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in BASE_HEADERS.items():
                    headers.setdefault(name, value)
                if path not in self._csp_exempt:
                    headers.setdefault("Content-Security-Policy", API_CSP)
                if self._enable_hsts:
                    headers.setdefault("Strict-Transport-Security", HSTS)
            await send(message)

        await self.app(scope, receive, send_with_headers)
