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


settings = Settings()
