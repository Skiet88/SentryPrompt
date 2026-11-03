"""Rejects request bodies above a size limit with 413 (SECURITY_RULES.md §4).

If the request declares Content-Length, that value is checked up front (the
server rejects bodies that don't match their declared length). If it doesn't
(chunked upload), the body is read here, stopping as soon as the limit is
passed, then replayed to the app. Memory use is bounded by the limit.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int):
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.app = app
        self._max = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = self._declared_length(scope)
        if declared is not None:
            if declared > self._max:
                await self._reject(send)
            else:
                await self.app(scope, receive, send)
            return

        body = await self._read_capped(receive)
        if body is None:
            await self._reject(send)
            return
        await self.app(scope, self._replay(body, receive), send)

    async def _read_capped(self, receive: Receive) -> bytes | None:
        """Read the whole body, or return None once it exceeds the limit."""
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break  # client disconnected
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self._max:
                return None
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        return b"".join(chunks)

    @staticmethod
    def _replay(body: bytes, receive: Receive) -> Receive:
        sent = False

        async def replay_receive() -> Message:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return replay_receive

    @staticmethod
    def _declared_length(scope: Scope) -> int | None:
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    length = int(value)
                except ValueError:
                    return None
                # Malformed or negative: don't trust it, count the bytes instead.
                return length if length >= 0 else None
        return None

    async def _reject(self, send: Send) -> None:
        body = json.dumps(
            {"error": "payload_too_large", "message": f"Request body exceeds {self._max} bytes."}
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
