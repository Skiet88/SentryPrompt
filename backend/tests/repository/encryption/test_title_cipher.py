import base64
import os

import pytest

from app.exception import ConfigurationError
from app.repository.encryption.message_cipher import AesGcmMessageCipher, DecryptionError
from app.repository.encryption.title_cipher import AesGcmTitleCipher

CONVERSATION = "00000000-0000-4000-8000-000000000001"
OTHER = "00000000-0000-4000-8000-000000000002"


def test_round_trip_and_random_nonce():
    cipher = AesGcmTitleCipher(os.urandom(32))
    first = cipher.encrypt("I take sertraline", conversation_id=CONVERSATION)
    second = cipher.encrypt("I take sertraline", conversation_id=CONVERSATION)
    assert first != second
    assert b"sertraline" not in first
    assert cipher.decrypt(first, conversation_id=CONVERSATION) == "I take sertraline"


def test_bound_to_its_conversation():
    cipher = AesGcmTitleCipher(os.urandom(32))
    sealed = cipher.encrypt("Title", conversation_id=CONVERSATION)
    with pytest.raises(DecryptionError):
        cipher.decrypt(sealed, conversation_id=OTHER)


def test_a_message_ciphertext_cannot_be_read_as_a_title():
    key = os.urandom(32)
    message = AesGcmMessageCipher(key).encrypt(
        "secret", message_id=CONVERSATION, conversation_id=CONVERSATION
    )
    with pytest.raises(DecryptionError):
        AesGcmTitleCipher(key).decrypt(message, conversation_id=CONVERSATION)


@pytest.mark.parametrize("damaged", [b"", b"\x02" + b"0" * 40, b"\x01" + b"0" * 10])
def test_damaged_ciphertext_rejected(damaged):
    with pytest.raises(DecryptionError):
        AesGcmTitleCipher(os.urandom(32)).decrypt(damaged, conversation_id=CONVERSATION)


def test_key_from_base64_and_bad_keys():
    key = os.urandom(32)
    cipher = AesGcmTitleCipher.from_base64(base64.b64encode(key).decode())
    assert (
        cipher.decrypt(
            AesGcmTitleCipher(key).encrypt("t", conversation_id=CONVERSATION), conversation_id=CONVERSATION
        )
        == "t"
    )
    with pytest.raises(ConfigurationError):
        AesGcmTitleCipher.from_base64("not base64!")
    with pytest.raises(ConfigurationError):
        AesGcmTitleCipher(os.urandom(16))
