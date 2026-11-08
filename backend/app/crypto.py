import base64

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

KEY_VERSION = 1
NONCE_LEN = 12
TAG_LEN = 16


class CryptoError(Exception):
    pass


def encrypt(plaintext: str, aad: bytes) -> bytes:
    """
    Encrypt plaintext using AES-256-GCM with associated authenticated data.

    Args:
        plaintext: String to encrypt (e.g., refresh token)
        aad: Associated authenticated data (e.g., mailbox id as bytes)

    Returns:
        Encrypted blob: version (1 byte) + nonce (12 bytes) + ciphertext + tag

    Raises:
        CryptoError: If encryption fails
    """
    try:
        import os

        nonce = os.urandom(NONCE_LEN) 
        key = settings.get_encryption_key()
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), aad)
        return bytes([KEY_VERSION]) + nonce + ciphertext
    except Exception as e:
        raise CryptoError(f"Encryption failed: {e}") from e


def decrypt(blob: bytes, aad: bytes) -> str:
    try:
        if len(blob) < 1 + NONCE_LEN + TAG_LEN:
            raise CryptoError("Blob too short")

        if blob[0] != KEY_VERSION:
            raise CryptoError(f"Unknown key version: {blob[0]}")

        nonce = blob[1 : 1 + NONCE_LEN]
        ciphertext = blob[1 + NONCE_LEN :]

        key = settings.get_encryption_key()
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext, aad)
        return plaintext.decode("utf-8")
    except InvalidTag as e:
        raise CryptoError("Decryption failed (invalid tag or wrong AAD)") from e
    except CryptoError:
        raise
    except Exception as e:
        raise CryptoError(f"Decryption failed: {e}") from e
