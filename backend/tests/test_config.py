
import pytest
from app.config import get_settings
from pydantic import ValidationError


def test_missing_encryption_key_fails(monkeypatch, tmp_path):
    # Avoid accidentally loading a developer's .env file.
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv(
        "DATABASE_URL_DIRECT",
        "postgresql://test:test@localhost/test",
    )
    monkeypatch.setenv("SESSION_SECRET", "s" * 40)
    monkeypatch.setenv(
        "OAUTH_REDIRECT_URI",
        "http://localhost:8000/auth/callback",
    )
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)

    # Clear cached settings before testing.
    get_settings.cache_clear()

    with pytest.raises(ValidationError) as exc_info:
        get_settings()

    assert "TOKEN_ENCRYPTION_KEY" in str(exc_info.value)

    # Avoid leaking cached test settings into other tests.
    get_settings.cache_clear()
