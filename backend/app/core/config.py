"""
app/core/config.py
------------------
Centralised settings loaded from the .env file via Pydantic-Settings.
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


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

    # MongoDB Atlas Settings (accepts MONGODB_URL or MONGODB_URI)
    MONGODB_URI: str | None = Field(default=None, validation_alias="MONGODB_URL")
    MONGODB_DB_NAME: str = Field(default="Research047", validation_alias="DATABASE_NAME")

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()