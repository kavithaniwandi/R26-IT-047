"""Central application settings loaded from ``backend/.env``."""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Existing research modules retain SQLAlchemy. The individual disaster
    # operations module uses the separately configured MongoDB collections.
    DATABASE_URL: str = "sqlite:///./disaster_relief.db"
    MONGODB_URI: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MONGODB_URI", "MONGODB_URL"),
    )
    MONGODB_DB_NAME: str = Field(
        default="Research047",
        validation_alias=AliasChoices("MONGODB_DB_NAME", "DATABASE_NAME"),
    )
    # Optional second connection for the imported disaster-operations
    # component. When omitted, it safely reuses the research Mongo database.
    COMPONENT_MONGODB_URI: str | None = None
    COMPONENT_MONGODB_DB_NAME: str | None = None

    APP_TITLE: str = "Disaster Relief Medical Donation Module API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    # Text.lk SMS Gateway (primary provider)
    # API: POST https://app.text.lk/api/v3/sms/send
    # Auth: Bearer token in Authorization header
    # Free trial: ~10 SMS units; TextLKDemo sender ID (testing only)
    TEXTLK_ENABLED: bool = False
    TEXTLK_API_TOKEN: str = ""
    TEXTLK_API_URL: str = "https://app.text.lk/api/v3/sms/send"
    TEXTLK_SENDER_ID: str = "TextLKDemo"
    TEXTLK_TIMEOUT_SECONDS: int = 15

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
