from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class TokenDecryptError(Exception):
    pass


def encrypt_token(plain: str) -> str:
    key_str = settings.token_encryption_key
    cipher = Fernet(key_str.encode())
    encrypted = cipher.encrypt(plain.encode())
    return encrypted.decode()


def decrypt_token(blob: str) -> str:
    key_str = settings.token_encryption_key
    cipher = Fernet(key_str.encode())
    try:
        decrypted = cipher.decrypt(blob.encode())
        return decrypted.decode()
    except InvalidToken as e:
        raise TokenDecryptError(f"Failed to decrypt token: {e}") from e
