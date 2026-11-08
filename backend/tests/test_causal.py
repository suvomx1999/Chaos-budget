"""
Tests for the CausalAnalyzer service.

Covers:
  1. Timeline with clear lucky events → ATE in valid range
  2. Timeline with no lucky events → ATE in valid range
  3. ATE always between -1 and 1
  4. Graceful fallback when events < 3
"""

from __future__ import annotations

import pytest

from app.models.timeline import EventType, TimelineEvent
from app.services.causal import CausalAnalyzer


# ── Helpers ───────────────────────────────────────────────────────────

def make_event(
    year: int = 2022,
    event_type: str = "job",
    title: str = "Test event",
    self_rating: int = 5,
    description: str | None = None,
) -> TimelineEvent:
    return TimelineEvent(
        year=year,
        event_type=EventType(event_type),
        title=title,
        self_rating=self_rating,
        description=description,
    )


# ── Sample timelines ─────────────────────────────────────────────────

LUCKY_TIMELINE = [
    make_event(2019, "job", "Campus placement at MNC", 3, "Got through campus placement lottery"),
    make_event(2020, "relocation", "Relocated for partner's job", 2, "Had to relocate randomly"),
    make_event(2020, "job", "Got referral from stranger", 3, "Random referral led to this"),
    make_event(2021, "failure", "Laid off in recession", 1, "Economic downturn layoff"),
    make_event(2022, "job", "Acqui-hire saved my career", 2, "Lucky acquisition"),
]

NO_LUCK_TIMELINE = [
    make_event(2019, "education", "Self-taught programming", 10, "Learned everything independently"),
    make_event(2020, "skill", "Built open source projects", 9, "Dedicated 6 months to OSS"),
    make_event(2021, "skill", "Earned AWS certifications", 9, "Studied and passed 3 exams"),
    make_event(2022, "job", "Founded own company", 10, "Built from scratch with hard work"),
    make_event(2023, "achievement", "Company is profitable", 9, "Achieved through deliberate effort"),
]

MIXED_TIMELINE = [
    make_event(2019, "education", "Graduated from college", 7, "Worked hard for degree"),
    make_event(2020, "job", "First job via campus placement", 4, "Campus placement"),
    make_event(2021, "failure", "Laid off during funding winter", 2, "Layoff due to recession"),
    make_event(2021, "job", "Freelanced independently", 8, "Self-driven freelancing"),
    make_event(2022, "achievement", "Got into top company", 8, "Cracked interview after prep"),
]

TINY_TIMELINE = [
    make_event(2022, "education", "Graduated", 7),
]

TWO_EVENT_TIMELINE = [
    make_event(2021, "education", "Graduated", 7),
    make_event(2022, "job", "First job", 5),
]


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def analyzer() -> CausalAnalyzer:
    return CausalAnalyzer()


# ══════════════════════════════════════════════════════════════════════
# Tests
# ══════════════════════════════════════════════════════════════════════

class TestLuckyTimeline:
    """Timeline with clear lucky events."""

    def test_ate_in_range(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(LUCKY_TIMELINE, "senior")
        assert -1.0 <= result["ate"] <= 1.0, f"ATE={result['ate']} out of range"

    def test_has_confidence(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(LUCKY_TIMELINE, "senior")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_has_method(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(LUCKY_TIMELINE, "senior")
        assert result["method"] in (
            "dowhy_backdoor_linear_regression", "heuristic_fallback"
        )


class TestNoLuckTimeline:
    """Timeline with no lucky events — all self-driven."""

    def test_ate_in_range(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(NO_LUCK_TIMELINE, "senior")
        assert -1.0 <= result["ate"] <= 1.0

    def test_has_confidence(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(NO_LUCK_TIMELINE, "senior")
        assert 0.0 <= result["confidence"] <= 1.0


class TestMixedTimeline:
    """Mixed lucky and skill events."""

    def test_ate_in_range(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(MIXED_TIMELINE, "senior")
        assert -1.0 <= result["ate"] <= 1.0

    def test_confidence_in_range(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(MIXED_TIMELINE, "senior")
        assert 0.0 <= result["confidence"] <= 1.0


class TestGracefulFallback:
    """Fallback when events < 3."""

    def test_single_event_uses_heuristic(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(TINY_TIMELINE, "student")
        assert result["method"].startswith("heuristic")
        assert -1.0 <= result["ate"] <= 1.0

    def test_two_events_uses_heuristic(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect(TWO_EVENT_TIMELINE, "junior")
        assert result["method"].startswith("heuristic")

    def test_empty_events_uses_heuristic(self, analyzer: CausalAnalyzer) -> None:
        result = analyzer.estimate_luck_effect([], "student")
        assert result["method"] == "heuristic_no_events"
        assert result["ate"] == 0.0

    def test_no_crash_any_level(self, analyzer: CausalAnalyzer) -> None:
        """Ensure all career levels work without crashing."""
        for level in ["student", "junior", "mid", "senior", "lead", "executive"]:
            result = analyzer.estimate_luck_effect(MIXED_TIMELINE, level)
            assert -1.0 <= result["ate"] <= 1.0


class TestCausalGraph:
    """Test graph building."""

    def test_graph_is_valid_gml(self, analyzer: CausalAnalyzer) -> None:
        graph = analyzer.build_causal_graph(MIXED_TIMELINE)
        assert "graph" in graph
        assert "lucky_event" in graph
        assert "outcome" in graph
        assert "edge" in graph
