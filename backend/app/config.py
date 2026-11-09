import base64
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    google_client_id: str
    google_client_secret: str
    oauth_redirect_uri: str
    session_secret: str
    token_encryption_key: str
    frontend_origin: str
    mailbox_mode: Literal["real", "fake"] = "fake"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_encryption_key()

    def _validate_encryption_key(self) -> None:
        try:
            decoded = base64.b64decode(self.token_encryption_key)
            if len(decoded) != 32:
                raise ValueError(
                    f"Token encryption key must decode to 32 bytes, got {len(decoded)}"
                )
        except Exception as e:
            raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY: {e}") from e

    def get_encryption_key(self) -> bytes:
        return base64.b64decode(self.token_encryption_key)


settings = Settings()
