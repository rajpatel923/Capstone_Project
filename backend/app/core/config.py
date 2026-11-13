from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Try root-level .env first so a single file at the repo root works for everything.
# Falls back to a local .env in case the backend is run in isolation.
_root_env = str(Path(__file__).parent.parent.parent.parent / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[_root_env, ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fridge_dev"
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwt_key: str = ""  # optional PEM public key for offline JWT verification (no JWKS network call)
    totp_encryption_key: str = ""  # Fernet 32-byte base64
    range_webhook_secret: str = ""
    rate_limit_per_minute: int = 10
    cors_origins: list[str] = ["http://localhost:3000"]
    credit_conversion_rate: int = 10  # points // rate = credits

    # SMTP — all optional. If smtp_host is empty, enrollment emails are skipped silently.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    smtp_from_name: str = "FRZR BURN"
    smtp_starttls: bool = True


settings = Settings()
