from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Optional and used only by migrate_mongodb_to_sqlite.py.
    MONGODB_URL: str | None = None
    DATABASE_NAME: str | None = None
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App metadata
    APP_ENV: str = "development"
    APP_TITLE: str = "Disaster Relief Medical Donation Module API"
    APP_VERSION: str = "1.0.0"

    # -------------------------------------------------------
    # Twilio SMS Gateway Configuration
    # Set TWILIO_ENABLED=true in .env with real credentials
    # to activate real SMS dispatch. Defaults to simulation.
    # -------------------------------------------------------
    TWILIO_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_MESSAGING_SERVICE_SID: str = ""

    # SMS identity strings
    SMS_EMERGENCY_SHORTCODE: str = "1919"
    SMS_SENDER_NAME: str = "DISASTER-RELIEF"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
