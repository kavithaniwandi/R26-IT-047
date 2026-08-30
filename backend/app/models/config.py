from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    MODEL_DIR: Path = Path("ml_models")
    DONATION_APPEAL_MODEL_DIR: Path = Path("ml_models") / "Donation Appeal"
    GEMINI_API_KEY: str | None = None
    GEMINI_API_KEY2: str | None = None
    GEMINI_API_KEY3: str | None = None
    GEMINI_API_KEY4: str | None = None
    GEMINI_API_KEY5: str | None = None
    GEMINI_API_KEY6: str | None = None
    GEMINI_API_KEY7: str | None = None
    GEMINI_API_KEY8: str | None = None
    GEMINI_API_KEY9: str | None = None
    GEMINI_API_KEY10: str | None = None
    GEMINI_API_KEY11: str | None = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    HF_API_KEY: str | None = None
    MONGODB_URI: str | None = None
    MONGODB_DB_NAME: str = "Research047"

    def model_path(self, filename: str) -> Path:
        model_dir = self.MODEL_DIR
        if not model_dir.is_absolute():
            model_dir = BASE_DIR / model_dir
        return model_dir / filename

    def donation_appeal_model_path(self, filename: str) -> Path:
        model_dir = self.DONATION_APPEAL_MODEL_DIR
        if not model_dir.is_absolute():
            model_dir = BASE_DIR / model_dir
        return model_dir / filename

    @property
    def REGRESSOR_PATH(self) -> Path:
        return self.donation_appeal_model_path("appeal_quality_regressor.joblib")

    @property
    def VECTORIZER_SCORE_PATH(self) -> Path:
        return self.donation_appeal_model_path("appeal_quality_vectorizer_score.joblib")

    @property
    def CLASSIFIER_PATH(self) -> Path:
        return self.donation_appeal_model_path("appeal_quality_classifier_balanced.joblib")

    @property
    def VECTORIZER_CLS_PATH(self) -> Path:
        return self.donation_appeal_model_path("appeal_quality_vectorizer_balanced.joblib")

    @property
    def LABEL_ENCODER_PATH(self) -> Path:
        return self.donation_appeal_model_path("appeal_quality_label_encoder.joblib")


settings = Settings()
