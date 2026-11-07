import base64
import os

import pytest

from app.exception import ConfigurationError
from app.repository.encryption.message_cipher import AesGcmMessageCipher, DecryptionError

KEY = os.urandom(32)
IDS = {"message_id": "m-1", "conversation_id": "c-1"}


def cipher(key: bytes = KEY) -> AesGcmMessageCipher:
    return AesGcmMessageCipher(key)


def test_round_trip():
    sealed = cipher().encrypt("I take sertraline", **IDS)
    assert cipher().decrypt(sealed, **IDS) == "I take sertraline"


def test_ciphertext_does_not_contain_plaintext_and_is_randomised():
    first = cipher().encrypt("I take sertraline", **IDS)
    second = cipher().encrypt("I take sertraline", **IDS)
    assert b"sertraline" not in first
    assert first != second  # fresh nonce each time


def test_wrong_key_fails():
    sealed = cipher().encrypt("secret", **IDS)
    with pytest.raises(DecryptionError):
        cipher(os.urandom(32)).decrypt(sealed, **IDS)


@pytest.mark.parametrize(
    "ids", [{"message_id": "m-2", "conversation_id": "c-1"}, {"message_id": "m-1", "conversation_id": "c-2"}]
)
def test_ciphertext_moved_to_another_row_fails(ids):
    sealed = cipher().encrypt("secret", **IDS)
    with pytest.raises(DecryptionError):
        cipher().decrypt(sealed, **ids)


def test_tampering_fails():
    sealed = bytearray(cipher().encrypt("secret", **IDS))
    sealed[-1] ^= 1
    with pytest.raises(DecryptionError):
        cipher().decrypt(bytes(sealed), **IDS)


@pytest.mark.parametrize("damaged", [b"", b"\x02" + b"\x00" * 40, b"\x01" + b"\x00" * 5])
def test_damaged_or_unknown_version_fails(damaged):
    with pytest.raises(DecryptionError):
        cipher().decrypt(damaged, **IDS)


def test_key_from_base64_and_validation():
    assert (
        AesGcmMessageCipher.from_base64(base64.b64encode(KEY).decode()).decrypt(
            cipher().encrypt("x", **IDS), **IDS
        )
        == "x"
    )
    with pytest.raises(ConfigurationError, match="base64"):
        AesGcmMessageCipher.from_base64("not base64!")
    with pytest.raises(ConfigurationError, match="32 bytes"):
        AesGcmMessageCipher.from_base64(base64.b64encode(b"short").decode())
