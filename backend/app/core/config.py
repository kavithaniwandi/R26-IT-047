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

    APP_TITLE: str = "Disaster Relief Medical Donation Module API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
