"""
Pydantic data models for the Chaos Budget pipeline.

All models use strict validation and sensible defaults.
UUIDs are auto-generated where appropriate.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """Categories of career/life timeline events."""
    EDUCATION = "education"
    JOB = "job"
    SKILL = "skill"
    ACHIEVEMENT = "achievement"
    FAILURE = "failure"
    RELOCATION = "relocation"
    PERSONAL = "personal"
    OTHER = "other"


class CareerLevel(str, Enum):
    """Ordinal career levels (0 → 5)."""
    STUDENT = "student"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

    @property
    def ordinal(self) -> int:
        """Numeric rank for comparison and simulation."""
        return list(CareerLevel).index(self)


# ═══════════════════════════════════════════════════════════════════════
# Core Models
# ═══════════════════════════════════════════════════════════════════════

class TimelineEvent(BaseModel):
    """A single event on a user's career/life timeline."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    year: int = Field(..., ge=1950, le=2030, description="Year the event occurred")
    month: Optional[int] = Field(
        default=None, ge=1, le=12, description="Month (1-12), optional"
    )
    event_type: EventType = Field(..., description="Category of the event")
    title: str = Field(..., min_length=1, max_length=300, description="Short title")
    organization: Optional[str] = Field(
        default=None, max_length=200, description="Company, school, etc."
    )
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Longer description"
    )
    self_rating: int = Field(
        ...,
        ge=1,
        le=10,
        description="1-10: how much was this the user's own doing?",
    )
    duration_months: Optional[int] = Field(
        default=None, ge=0, le=600, description="Duration in months"
    )

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be blank or whitespace-only")
        return v.strip()


class AlternatePath(BaseModel):
    """One counterfactual career trajectory from the Monte Carlo simulation."""

    path_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    events: List[dict] = Field(
        default_factory=list, description="Sequence of simulated events"
    )
    final_outcome: str = Field(
        ..., description="Where this path ends up (free-text summary)"
    )
    outcome_level: str = Field(
        ..., description="Career level at the end of this path"
    )
    divergence_point: str = Field(
        ..., description="The pivot event where this path diverged"
    )


class TimelineInput(BaseModel):
    """
    Full input payload — can come from the structured form,
    a raw text paste, or both.
    """

    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_text: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Pasted resume / LinkedIn / career story",
    )
    events: Optional[List[TimelineEvent]] = Field(
        default=None, description="Manually entered or parsed events"
    )
    current_role: str = Field(
        ..., min_length=1, max_length=200, description="User's current job title"
    )
    current_level: CareerLevel = Field(
        ..., description="Career seniority level"
    )
    field: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Professional field (e.g. 'software engineering')",
    )

    @field_validator("current_role", "field")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()


class SimulationResult(BaseModel):
    """Output of the Monte Carlo + causal inference pipeline."""

    user_id: str
    chaos_coefficient: float = Field(
        ..., ge=0.0, le=1.0, description="0 = pure skill, 1 = pure luck"
    )
    skill_percentage: float = Field(..., ge=0.0, le=100.0)
    luck_percentage: float = Field(..., ge=0.0, le=100.0)
    timing_percentage: float = Field(..., ge=0.0, le=100.0)
    alternate_paths: List[AlternatePath] = Field(default_factory=list)
    key_pivot_events: List[str] = Field(
        default_factory=list,
        description="Titles of events identified as major pivot points",
    )
    causal_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence from DoWhy causal estimate (added in Step 5)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("timing_percentage")
    @classmethod
    def percentages_sum_to_100(cls, v: float, info) -> float:
        """Ensure skill + luck + timing ≈ 100%."""
        skill = info.data.get("skill_percentage", 0.0)
        luck = info.data.get("luck_percentage", 0.0)
        total = skill + luck + v
        if abs(total - 100.0) > 1.0:
            raise ValueError(
                f"skill ({skill}) + luck ({luck}) + timing ({v}) = {total}, "
                f"expected ≈ 100.0"
            )
        return v
