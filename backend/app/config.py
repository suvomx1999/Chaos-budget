"""
Configuration module for Chaos Budget backend.

Uses pydantic-settings to load and validate environment variables.
All config is accessed via the singleton `settings` object.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Known placeholder values that indicate the user hasn't configured yet
_PLACEHOLDER_VALUES = frozenset({
    "your_groq_api_key_here",
    "your_mongodb_atlas_connection_string",
    "",
})


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Required secrets ──────────────────────────────────────────────
    GROQ_API_KEY: str
    MONGODB_URI: str

    # ── Stripe ────────────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_PRICE_AMOUNT: int = 99       # in smallest currency unit (₹99)
    STRIPE_CURRENCY: str = "inr"

    # ── Defaults ──────────────────────────────────────────────────────
    MONGODB_DB_NAME: str = "chaos_budget"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    # ── Derived helpers ───────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def groq_key_is_real(self) -> bool:
        """True if the GROQ key looks like a real key, not a placeholder."""
        return self.GROQ_API_KEY not in _PLACEHOLDER_VALUES and len(self.GROQ_API_KEY) > 10

    @property
    def mongodb_uri_is_real(self) -> bool:
        """True if the MongoDB URI looks like a real connection string."""
        return (
            self.MONGODB_URI not in _PLACEHOLDER_VALUES
            and ("mongodb" in self.MONGODB_URI.lower())
        )

    # ── Validators ────────────────────────────────────────────────────
    @field_validator("GROQ_API_KEY")
    @classmethod
    def groq_key_not_empty(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError(
                "GROQ_API_KEY must be set. Get one at https://console.groq.com"
            )
        return v

    @field_validator("MONGODB_URI")
    @classmethod
    def mongodb_uri_not_empty(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError(
                "MONGODB_URI must be set to a valid MongoDB connection string."
            )
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def environment_valid(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v.lower()


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance. Call once at startup."""
    return Settings()
