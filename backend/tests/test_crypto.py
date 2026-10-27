import base64
import os
import uuid

import pytest
from app.crypto import DecryptError, decrypt, encrypt


def make_key() -> str:
    return base64.b64encode(os.urandom(32)).decode()


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", make_key())


AAD = uuid.uuid4().bytes
TOKEN = "1//example-refresh-token"


def test_round_trip():
    assert decrypt(encrypt(TOKEN, AAD), AAD) == TOKEN


def test_same_value_gives_different_blobs():
    assert encrypt(TOKEN, AAD) != encrypt(TOKEN, AAD)


def test_wrong_key_fails(monkeypatch):
    blob = encrypt(TOKEN, AAD)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", make_key())
    with pytest.raises(DecryptError):
        decrypt(blob, AAD)


def test_wrong_aad_fails():
    blob = encrypt(TOKEN, AAD)
    with pytest.raises(DecryptError):
        decrypt(blob, uuid.uuid4().bytes)


def test_flipped_byte_fails():
    blob = bytearray(encrypt(TOKEN, AAD))
    blob[-1] ^= 1
    with pytest.raises(DecryptError):
        decrypt(bytes(blob), AAD)


def test_truncated_blob_fails():
    with pytest.raises(DecryptError):
        decrypt(encrypt(TOKEN, AAD)[:10], AAD)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY")
    with pytest.raises(RuntimeError):
        encrypt(TOKEN, AAD)


def test_short_key_raises(monkeypatch):
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", base64.b64encode(b"short").decode())
    with pytest.raises(RuntimeError):
        encrypt(TOKEN, AAD)