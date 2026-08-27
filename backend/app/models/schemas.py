from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AppealQualityRequest(BaseModel):
    appeal_text: str = Field(..., min_length=1)

    @field_validator("appeal_text")
    @classmethod
    def validate_appeal_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("appeal_text must not be empty or whitespace only")
        return value


class AppealQualityResponse(BaseModel):
    score: float = Field(..., ge=1.0, le=5.0)
    label: Literal["low", "medium", "high"]
    probabilities: dict[Literal["low", "medium", "high"], float]


class QualityScoreRequest(BaseModel):
    appeal_text: str = Field(..., min_length=1)
    language: str = "English"

    @field_validator("appeal_text")
    @classmethod
    def validate_appeal_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("appeal_text must not be empty or whitespace only")
        return value


class QualityScoreResponse(BaseModel):
    score: float = Field(..., ge=1.0, le=5.0)
    status: Literal["low", "medium", "high"]
    method: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_normalised: float = Field(..., ge=0.0, le=1.0)
    confidence_display: str


class GenerateAppealRequest(BaseModel):
    language: str = "en"
    campaign_type: str
    location: str = ""
    verified_need: str = ""
    campaign_goal: str = ""
    tone: str = "hopeful"
    channel: str = "facebook"
    length_category: str = "short"


class GenerateAppealResponse(BaseModel):
    appeal_text: str


class AppealVariant(BaseModel):
    model: str
    temperature: float
    style: str | None = None
    appeal_text: str
    quality_label: str
    quality_score: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_normalised: float = Field(..., ge=0.0, le=1.0)
    confidence_display: str


class GenerateAppealVariantsResponse(BaseModel):
    variants: list[AppealVariant]


class SeverityClassifyRequest(BaseModel):
    clinical_note: str = Field(..., min_length=1)
    age: int | None = Field(default=None, ge=0, le=120)
    mode: Literal["rule_based", "ml"] = "rule_based"
    source: str = "TRIAGE"

    condition_group: str = "Unknown"
    vitals: dict | None = None
    has_red_flag: int = Field(default=0, ge=0, le=1)
    red_flag_count: int = Field(default=0, ge=0)
    rf_flags: dict | None = None
    symptoms: str = ""

    @field_validator("clinical_note")
    @classmethod
    def validate_clinical_note(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("clinical_note must not be empty or whitespace only")
        return value


class SeverityClassifyResponse(BaseModel):
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    priority_score: float = Field(..., ge=0.0, le=100.0)
    risk_score: int = Field(..., ge=0, le=100)
    method: Literal["rule_based", "ml"]
    scores: dict[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"], float]
    matched_rules: list[str]
    critical_trigger: str | None
    should_queue: bool
    queue_reason: Literal["auto_triage", "audit_sample", "rule_flag", "not_queued"]
    queue_title: str
    queue_description: str
    queue_reason_text: str
    recommended_action: str
    display_note: str


class ExtractRequest(BaseModel):
    clinical_note: str = Field(..., min_length=1)
    symptoms: str = ""

    @field_validator("clinical_note")
    @classmethod
    def validate_note(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("clinical_note must not be empty or whitespace only")
        return value


class ExtractResponse(BaseModel):
    condition_group: str
    specialty: str
    extracted_symptoms: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    valid: bool = True
