"""
Application configuration using Pydantic v2 settings.

All environment variables are validated at startup. The app refuses to boot
if required keys are missing or invalid.
"""

import base64
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: Literal["dev", "staging", "prod"] = "dev"

    # Database
    database_url: str  # Required: postgresql+asyncpg://...
    database_url_direct: str | None = None  # Optional: for direct connections

    # API Server
    api_host: str = "localhost"
    api_port: int = 8000
    api_workers: int = 1

    # Security (critical for Phase 0)
    secret_key: str  # Required: used for signing cookies/JWTs
    token_encryption_key: str  # Required: base64-encoded 32-byte key
    session_secret: str  # Required: min 32 chars for session signing

    # Session
    session_id_cookie_name: str = "inbox_session"
    session_cookie_secure: bool = False  # Set to True in production
    session_cookie_httponly: bool = True
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_expiry_days: int = 14

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["Content-Type", "Authorization", "X-CSRF-Token"]

    # CSRF
    csrf_header_name: str = "X-CSRF-Token"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_auth_per_minute: int = 5

    # OAuth
    oauth_redirect_uri: str  # Required
    google_client_id: str  # Required
    google_client_secret: str  # Required
    google_oauth_authorize_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_oauth_token_url: str = "https://oauth2.googleapis.com/token"
    google_oauth_revoke_url: str = "https://oauth2.googleapis.com/revoke"
    google_oauth_userinfo_url: str = "https://openidconnect.googleapis.com/v1/userinfo"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Sentry (optional, Phase 4)
    sentry_dsn: str | None = None

    # Feature flags
    demo_mode_enabled: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data):
        """Validate configuration at startup."""
        super().__init__(**data)
        self._validate_encryption_key()

    def _validate_encryption_key(self) -> None:
        """
        Validate and decode the token encryption key.

        Must be a base64-encoded 32-byte key.
        Raises ValueError if invalid.
        """
        try:
            decoded = base64.b64decode(self.token_encryption_key)
            if len(decoded) != 32:
                raise ValueError(
                    f"Token encryption key must decode to 32 bytes, got {len(decoded)}"
                )
        except Exception as e:
            raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY: {e}") from e

    def get_encryption_key(self) -> bytes:
        """Get the decoded encryption key."""
        return base64.b64decode(self.token_encryption_key)


# Global settings instance
settings = Settings()
