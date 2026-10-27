"""Encrypt/decrypt secrets (like Gmail refresh tokens) with AES-GCM.

Blob layout: key_version (1 byte) || nonce (12 bytes) || ciphertext + tag
The `aad` (use the mailbox id bytes) ties a blob to one DB row, so a blob
copied into another row fails to decrypt.
"""

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_VERSION = 1
NONCE_LEN = 12
TAG_LEN = 16


class DecryptError(Exception):
    """Raised when a blob can't be decrypted. Treat as 'needs reconnect'."""


def _load_key() -> bytes:
    raw = os.environ.get("TOKEN_ENCRYPTION_KEY")
    if not raw:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not set")
    try:
        key = base64.b64decode(raw, validate=True)
    except ValueError as exc:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not valid base64") from exc
    if len(key) != 32:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt(plaintext: str, aad: bytes) -> bytes:
    nonce = os.urandom(NONCE_LEN)  # fresh every call, never reuse
    ciphertext = AESGCM(_load_key()).encrypt(nonce, plaintext.encode("utf-8"), aad)
    return bytes([KEY_VERSION]) + nonce + ciphertext


def decrypt(blob: bytes, aad: bytes) -> str:
    if len(blob) < 1 + NONCE_LEN + TAG_LEN:
        raise DecryptError("blob too short")
    if blob[0] != KEY_VERSION:
        raise DecryptError("unknown key version")

    nonce = blob[1 : 1 + NONCE_LEN]
    ciphertext = blob[1 + NONCE_LEN :]
    try:
        return AESGCM(_load_key()).decrypt(nonce, ciphertext, aad).decode("utf-8")
    except InvalidTag as exc:
        raise DecryptError("decryption failed") from exc