"""Encrypts message content before it is stored (NFR-011).

AES-256-GCM with a random 96-bit nonce per message. Each ciphertext is bound
to its own message and conversation IDs (authenticated associated data), so
someone with database access cannot move an encrypted message into another
conversation: decryption would fail. Format:

    version (1 byte) | nonce (12 bytes) | ciphertext + tag

The version byte allows a later move to a new key without breaking old data.
"""

from __future__ import annotations

import base64
import binascii
import os
from abc import ABC, abstractmethod

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.exception import ConfigurationError

VERSION = b"\x01"
NONCE_BYTES = 12
KEY_BYTES = 32


class DecryptionError(Exception):
    """Stored content could not be decrypted: wrong key, tampering, or a
    ciphertext moved to another row."""


class MessageCipher(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str, *, message_id: str, conversation_id: str) -> bytes: ...

    @abstractmethod
    def decrypt(self, ciphertext: bytes, *, message_id: str, conversation_id: str) -> str: ...


def decode_key(encoded_key: str) -> bytes:
    """MESSAGE_ENCRYPTION_KEY (base64) as bytes."""
    try:
        return base64.b64decode(encoded_key.strip(), validate=True)
    except (binascii.Error, ValueError):
        raise ConfigurationError(
            "MESSAGE_ENCRYPTION_KEY must be base64 (see scripts/generate_key.py)"
        ) from None


def _associated_data(message_id: str, conversation_id: str) -> bytes:
    return f"sentryprompt.message.v1|{conversation_id}|{message_id}".encode()


class AesGcmMessageCipher(MessageCipher):
    def __init__(self, key: bytes):
        if len(key) != KEY_BYTES:
            raise ConfigurationError("The message encryption key must be 32 bytes (AES-256)")
        self._aead = AESGCM(key)

    @classmethod
    def from_base64(cls, encoded_key: str) -> AesGcmMessageCipher:
        return cls(decode_key(encoded_key))

    def encrypt(self, plaintext: str, *, message_id: str, conversation_id: str) -> bytes:
        nonce = os.urandom(NONCE_BYTES)
        sealed = self._aead.encrypt(nonce, plaintext.encode(), _associated_data(message_id, conversation_id))
        return VERSION + nonce + sealed

    def decrypt(self, ciphertext: bytes, *, message_id: str, conversation_id: str) -> str:
        if len(ciphertext) < 1 + NONCE_BYTES + 16 or ciphertext[:1] != VERSION:
            raise DecryptionError("Unsupported or damaged ciphertext")
        nonce = ciphertext[1 : 1 + NONCE_BYTES]
        try:
            plaintext = self._aead.decrypt(
                nonce, ciphertext[1 + NONCE_BYTES :], _associated_data(message_id, conversation_id)
            )
        except InvalidTag:
            raise DecryptionError("Message could not be decrypted") from None
        return plaintext.decode()
