
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Optional and used only by migrate_mongodb_to_sqlite.py
    MONGODB_URL: str | None = None
    DATABASE_NAME: str | None = None

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App metadata
    APP_ENV: str = "development"
    APP_TITLE: str = "Disaster Relief Medical Donation Module API"
    APP_VERSION: str = "1.0.0"

    # Legacy Twilio configuration retained for compatibility
    TWILIO_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_MESSAGING_SERVICE_SID: str = ""

    # SMSGo.lk SMS Gateway Configuration (retained for compatibility)
    SMSGO_ENABLED: bool = False
    SMSGO_API_KEY: str = ""
    SMSGO_MASK: str = ""
    SMSGO_API_URL: str = "https://api.smsgo.lk/api/v1/sms/send"
    SMSGO_TIMEOUT_SECONDS: int = 15

    # Text.lk SMS Gateway Configuration
    # API endpoint confirmed against https://text.lk/docs/ (v3 REST API)
    # Authentication: Bearer token in Authorization header
    # Payload fields: recipient (94XXXXXXXXX), sender_id, type ("plain"), message
    # Free trial: 10 SMS units; TextLKDemo sender ID (testing only, not for production)
    TEXTLK_ENABLED: bool = False
    TEXTLK_API_TOKEN: str = ""
    TEXTLK_API_URL: str = "https://app.text.lk/api/v3/sms/send"
    TEXTLK_SENDER_ID: str = "TextLKDemo"
    TEXTLK_TIMEOUT_SECONDS: int = 15

    # SMS identity strings
    SMS_EMERGENCY_SHORTCODE: str = "1919"
    SMS_SENDER_NAME: str = "DISASTER-RELIEF"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
