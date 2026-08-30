from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Optional and used only by migrate_mongodb_to_sqlite.py.
    MONGODB_URL: str | None = None
    DATABASE_NAME: str | None = None
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
