"""Validating the patterns_config.yaml file using Pydantic."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class PersonalInformationPatterns(BaseModel):
    """Patterns for personal information."""

    phone_number: str = r"\d{4}-\d{5}"
    date_dd_mm_yyyy: str = r"\d{2}-\d{2}-\d{4}"
    multi_4_digit_patt: str = r"\b\d{4}\b.*\b\d{4}\b"


class SensitiveInformationPatterns(BaseModel):
    """Patterns for sensitive information."""

    credit_card: str = r"\b(?:\d{4}[- ]?){3}\d{4}\b"
    atm_pin: str = r"\b\d{4}\b"
    account_password: str = (
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$" # noqa: S105
    )


class IntentPatterns(BaseModel):
    """Patterns for intents."""

    account_help: list[str]
    transaction_issue: list[str]
    card_help: list[str]
    payment_issue: list[str]


class IssuePatterns(BaseModel):
    """Patterns for issues."""

    fraud_concern: list[str]
    login_trouble: list[str]
    service_problem: list[str]


class SentimentBoosters(BaseModel):
    """Patterns for sentiment boosters."""

    positive: list[str]
    negative: list[str]


class PatternsConfigSchema(BaseModel):
    """Schema for the patterns configuration."""

    Greetings: list[str] = Field(alias="greetings")
    Disclaimers: list[str] = Field(alias="disclaimers")
    ProhibitedPhrases: list[str] = Field(alias="prohibited_phrases")
    ClosingStatements: list[str] = Field(alias="closing_statements")
    PersonalInformationPatterns: dict[str, str] = Field(alias="personal_info_patterns")
    SensitiveInformationPatterns: dict[str, str] = Field(
        alias="sensitive_info_patterns",
    )
    IntentPatterns: dict[str, list[str]] = Field(alias="intents")
    IssuePatterns: dict[str, list[str]] = Field(alias="issues")
    SentimentBoosters: dict[str, list[str]] = Field(alias="sentiment_boosters")

    model_config = {
        "validate_by_name": True,
        "extra": "forbid" }

def load_patterns_config(
    file_path: str | Path,
) -> PatternsConfigSchema | Exception:
    """Load and validate the patterns configuration file."""
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        config = PatternsConfigSchema(**yaml_data["patterns"])
    except ValueError as e:
        return e
    else:
        return config
