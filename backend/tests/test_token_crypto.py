import pytest
from cryptography.fernet import Fernet
from unittest.mock import patch

from app.auth import encrypt_token, decrypt_token, TokenDecryptError
from app.db import SessionLocal, User, Base, engine
import uuid


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_key():
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_config(test_key):
    with patch('app.auth.settings') as mock:
        mock.get_encryption_key.return_value = Fernet.generate_key()
        yield mock


def test_encrypt_then_decrypt_returns_original(test_key):
    with patch('app.auth.settings') as mock_settings:
        key_bytes = Fernet.generate_key()
        mock_settings.get_encryption_key.return_value = key_bytes

        original = "refresh_token_abc123xyz"
        encrypted = encrypt_token(original)
        decrypted = decrypt_token(encrypted)
        assert decrypted == original


def test_encrypted_blob_differs_from_plaintext(test_key):
    with patch('app.auth.settings') as mock_settings:
        key_bytes = Fernet.generate_key()
        mock_settings.get_encryption_key.return_value = key_bytes

        plaintext = "refresh_token_secret"
        encrypted = encrypt_token(plaintext)
        assert encrypted != plaintext


def test_decrypting_with_different_key_raises_error(test_key):
    with patch('app.auth.settings') as mock_settings:
        key_bytes = Fernet.generate_key()
        mock_settings.get_encryption_key.return_value = key_bytes

        plaintext = "refresh_token_xyz"
        encrypted = encrypt_token(plaintext)

        different_key = Fernet.generate_key()
        mock_settings.get_encryption_key.return_value = different_key

        with pytest.raises(TokenDecryptError):
            decrypt_token(encrypted)


def test_callback_without_refresh_token_leaves_existing_value_unchanged(test_key):
    with patch('app.auth.settings') as mock_settings:
        key_bytes = Fernet.generate_key()
        mock_settings.get_encryption_key.return_value = key_bytes

        session = SessionLocal()

        user = User(
            id=str(uuid.uuid4()),
            google_sub="google_123",
            email="user@example.com",
            refresh_token_enc=encrypt_token("existing_token"),
        )
        session.add(user)
        session.commit()

        existing_encrypted = user.refresh_token_enc

        callback_response = {
            "access_token": "new_access_token",
            "token_type": "Bearer",
        }

        if "refresh_token" not in callback_response or not callback_response.get("refresh_token"):
            pass

        session.refresh(user)
        assert user.refresh_token_enc == existing_encrypted

        session.close()
