"""
app/core/config.py
------------------
Centralised settings loaded from the .env file via Pydantic-Settings.
Centralised settings loaded from the .env2 file via Pydantic-Settings.
All other modules import from here — never call os.getenv() directly.
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # JWT
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./disaster_relief.db"

    # App meta
    APP_TITLE: str = "Disaster Relief Medical Donation Module API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    MONGODB_URI: str | None = None
    MONGODB_DB_NAME: str = "Research047"

    # MongoDB Atlas Settings (accepts MONGODB_URL or MONGODB_URI)
    MONGODB_URI: str | None = Field(default=None, validation_alias="MONGODB_URL")
    MONGODB_DB_NAME: str = Field(default="Research047", validation_alias="DATABASE_NAME")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()