from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class TokenDecryptError(Exception):
    pass


def encrypt_token(plain: str) -> str:
    key = settings.get_encryption_key()
    cipher = Fernet(key)
    encrypted = cipher.encrypt(plain.encode())
    return encrypted.decode()


def decrypt_token(blob: str) -> str:
    key = settings.get_encryption_key()
    cipher = Fernet(key)
    try:
        decrypted = cipher.decrypt(blob.encode())
        return decrypted.decode()
    except InvalidToken as e:
        raise TokenDecryptError(f"Failed to decrypt token: {e}") from e
