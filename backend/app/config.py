
import base64
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str

    google_client_id: str
    google_client_secret: str
    oauth_redirect_uri: str

    session_secret: str = Field(min_length=32)
    token_encryption_key: str

    frontend_origin: str
    mailbox_mode: Literal["real", "fake"] = "fake"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("token_encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        try:
            decoded = base64.b64decode(value, validate=True)

            if len(decoded) != 32:
                raise ValueError(
                    f"Token encryption key must decode to 32 bytes, got {len(decoded)}"
                )

        except Exception as e:
            raise ValueError(
                f"Invalid TOKEN_ENCRYPTION_KEY: {e}"
            ) from e

        return value

    def get_encryption_key(self) -> bytes:
        return base64.b64decode(self.token_encryption_key, validate=True)


settings = Settings()
