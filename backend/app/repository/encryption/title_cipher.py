"""Encrypts conversation titles before they are stored (NFR-011).

Titles are made from the (redacted) first prompt, so they are content and are
protected like messages: AES-256-GCM with a random nonce, the same key, and
associated data that binds each ciphertext to its conversation and marks it
as a title (so it can't be swapped with a message or another chat's title).
Format: version (1 byte) | nonce (12 bytes) | ciphertext + tag.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.exception import ConfigurationError

from .message_cipher import KEY_BYTES, NONCE_BYTES, VERSION, DecryptionError, decode_key


class TitleCipher(ABC):
    @abstractmethod
    def encrypt(self, title: str, *, conversation_id: str) -> bytes: ...

    @abstractmethod
    def decrypt(self, ciphertext: bytes, *, conversation_id: str) -> str: ...


def _associated_data(conversation_id: str) -> bytes:
    return f"sentryprompt.title.v1|{conversation_id}".encode()


class AesGcmTitleCipher(TitleCipher):
    def __init__(self, key: bytes):
        if len(key) != KEY_BYTES:
            raise ConfigurationError("The message encryption key must be 32 bytes (AES-256)")
        self._aead = AESGCM(key)

    @classmethod
    def from_base64(cls, encoded_key: str) -> AesGcmTitleCipher:
        return cls(decode_key(encoded_key))

    def encrypt(self, title: str, *, conversation_id: str) -> bytes:
        nonce = os.urandom(NONCE_BYTES)
        return VERSION + nonce + self._aead.encrypt(nonce, title.encode(), _associated_data(conversation_id))

    def decrypt(self, ciphertext: bytes, *, conversation_id: str) -> str:
        if len(ciphertext) < 1 + NONCE_BYTES + 16 or ciphertext[:1] != VERSION:
            raise DecryptionError("Unsupported or damaged ciphertext")
        nonce = ciphertext[1 : 1 + NONCE_BYTES]
        try:
            plaintext = self._aead.decrypt(
                nonce, ciphertext[1 + NONCE_BYTES :], _associated_data(conversation_id)
            )
        except InvalidTag:
            raise DecryptionError("Title could not be decrypted") from None
        return plaintext.decode()
