import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fridge_dev"
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwt_key: str = ""  # optional PEM public key for offline JWT verification (no JWKS network call)
    totp_encryption_key: str = ""  # Fernet 32-byte base64
    range_webhook_secret: str = ""
    rate_limit_per_minute: int = 10
    cors_origins: list[str] = ["http://localhost:3000"]
    credit_conversion_rate: int = 10  # points // rate = credits

    @model_validator(mode="after")
    def _check_required_secrets(self) -> "Settings":
        if os.getenv("SKIP_SECRET_VALIDATION"):
            return self
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY is required")
        if not self.totp_encryption_key:
            raise ValueError("TOTP_ENCRYPTION_KEY is required")
        if not self.range_webhook_secret:
            raise ValueError("RANGE_WEBHOOK_SECRET is required")
        return self


settings = Settings()
