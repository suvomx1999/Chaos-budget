"""
Tests for the ChaosSimulator Monte Carlo engine.

Covers:
  1. identify_pivot_points with various event lists
  2. simulate_alternate_paths always returns exactly 5 paths
  3. skill + luck + timing always sums to 100%
  4. Edge case: all self-initiated events (low chaos)
  5. Edge case: all lucky events (high chaos)
"""

from __future__ import annotations

import pytest

from app.models.timeline import CareerLevel, EventType, TimelineEvent
from app.services.simulator import ChaosSimulator


# ── Helpers ───────────────────────────────────────────────────────────

def make_event(
    year: int = 2022,
    event_type: str = "job",
    title: str = "Test event",
    self_rating: int = 5,
    description: str | None = None,
    organization: str | None = None,
    duration_months: int | None = 12,
) -> TimelineEvent:
    return TimelineEvent(
        year=year,
        event_type=EventType(event_type),
        title=title,
        self_rating=self_rating,
        description=description,
        organization=organization,
        duration_months=duration_months,
    )


# ── Sample timelines ─────────────────────────────────────────────────

MIXED_TIMELINE = [
    make_event(2019, "education", "Graduated B.Tech CS", 8, "Worked hard for 4 years", "NIT"),
    make_event(2019, "job", "Campus placement at Infosys", 3, "Got through campus placement randomly", "Infosys"),
    make_event(2020, "job", "Joined startup as backend engineer", 7, "Self-initiated job switch", "Startup"),
    make_event(2021, "failure", "Laid off during funding winter", 2, "Layoff due to economic downturn"),
    make_event(2021, "job", "Freelanced and built 3 projects", 9, "Self-motivated hustle"),
    make_event(2022, "achievement", "Cracked Atlassian interview", 8, "3 months of intense prep", "Atlassian"),
    make_event(2023, "job", "Senior SDE-2 at Atlassian", 8, "Promoted for strong performance", "Atlassian"),
]

ALL_SKILL_TIMELINE = [
    make_event(2019, "education", "Self-taught programming", 10, "Learned Python on my own"),
    make_event(2020, "skill", "Built personal project portfolio", 10, "Created 5 projects independently"),
    make_event(2021, "skill", "Completed advanced certifications", 9, "AWS + Kubernetes certs"),
    make_event(2022, "job", "Founded tech startup", 10, "Built company from scratch"),
    make_event(2023, "achievement", "Startup profitable in year 1", 9, "Earned through deliberate execution"),
]

ALL_LUCK_TIMELINE = [
    make_event(2019, "job", "Campus placement at random company", 2, "Got lucky in campus placement lottery"),
    make_event(2020, "relocation", "Relocated to new city for partner", 2, "Had to move for personal reasons"),
    make_event(2020, "job", "Got referral from stranger at meetup", 3, "Random referral led to job"),
    make_event(2021, "failure", "Laid off in recession", 1, "Economic downturn layoff"),
    make_event(2022, "job", "Acqui-hire from failing startup", 2, "Acquisition saved the team"),
]

SINGLE_EVENT_TIMELINE = [
    make_event(2022, "education", "Graduated", 7, "Completed degree"),
]

FIVE_EVENT_TIMELINE = [
    make_event(2018, "education", "Graduated high school", 6, "Got scholarship through competition"),
    make_event(2019, "education", "Started college", 5, "Selected through entrance exam"),
    make_event(2020, "job", "Summer internship via referral", 3, "Senior recommended me"),
    make_event(2021, "skill", "Open source contributions", 9, "Self-driven open source work"),
    make_event(2022, "job", "First full-time job", 6, "Applied and got selected"),
]


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def simulator() -> ChaosSimulator:
    """Seeded simulator for reproducible tests."""
    return ChaosSimulator(seed=42)


# ══════════════════════════════════════════════════════════════════════
# Test: identify_pivot_points
# ══════════════════════════════════════════════════════════════════════

class TestIdentifyPivotPoints:

    def test_mixed_timeline_has_pivots(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        assert len(pivots) == len(MIXED_TIMELINE)
        high = [p for p in pivots if p["luck_category"] == "HIGH"]
        assert len(high) >= 1, "Mixed timeline should have at least 1 HIGH luck event"

    def test_all_skill_events_are_low_luck(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(ALL_SKILL_TIMELINE)
        for p in pivots:
            assert p["luck_weight"] < 0.5, f"Skill event '{p['title']}' has luck_weight {p['luck_weight']}"

    def test_all_luck_events_are_high_luck(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(ALL_LUCK_TIMELINE)
        high_or_med = [p for p in pivots if p["luck_category"] in ("HIGH", "MEDIUM")]
        assert len(high_or_med) >= 3, "Lucky timeline should have mostly HIGH/MED events"

    def test_empty_events(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points([])
        assert pivots == []

    def test_five_event_timeline(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(FIVE_EVENT_TIMELINE)
        assert len(pivots) == 5
        # The referral event should have higher luck
        referral = next(p for p in pivots if "referral" in p["title"].lower())
        assert referral["luck_weight"] >= 0.4


# ══════════════════════════════════════════════════════════════════════
# Test: simulate_alternate_paths
# ══════════════════════════════════════════════════════════════════════

class TestSimulateAlternatePaths:

    def test_returns_exactly_5_paths(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        assert len(paths) == 5, f"Expected 5 paths, got {len(paths)}"

    def test_five_event_returns_5_paths(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(FIVE_EVENT_TIMELINE)
        paths = simulator.simulate_alternate_paths(FIVE_EVENT_TIMELINE, pivots)
        assert len(paths) == 5

    def test_all_paths_have_valid_outcome_level(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        valid_levels = {l.value for l in CareerLevel}
        for path in paths:
            assert path.outcome_level in valid_levels, f"Invalid level: {path.outcome_level}"

    def test_all_paths_have_divergence_point(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        for path in paths:
            assert path.divergence_point, "Divergence point should not be empty"

    def test_empty_pivots_returns_empty(self, simulator: ChaosSimulator) -> None:
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, [])
        assert paths == []


# ══════════════════════════════════════════════════════════════════════
# Test: compute_chaos_coefficient
# ══════════════════════════════════════════════════════════════════════

class TestComputeChaosCoefficient:

    def test_percentages_sum_to_100(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        result = simulator.compute_chaos_coefficient(
            MIXED_TIMELINE, paths, "senior", pivots
        )
        total = result["skill_percentage"] + result["luck_percentage"] + result["timing_percentage"]
        assert abs(total - 100.0) <= 0.5, f"Sum is {total}, expected ~100"

    def test_all_skill_has_low_chaos(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(ALL_SKILL_TIMELINE)
        paths = simulator.simulate_alternate_paths(ALL_SKILL_TIMELINE, pivots)
        result = simulator.compute_chaos_coefficient(
            ALL_SKILL_TIMELINE, paths, "senior", pivots
        )
        assert result["skill_percentage"] > result["luck_percentage"], (
            f"Skill ({result['skill_percentage']}%) should exceed luck ({result['luck_percentage']}%) "
            f"for all-skill timeline"
        )

    def test_all_luck_has_high_chaos(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(ALL_LUCK_TIMELINE)
        paths = simulator.simulate_alternate_paths(ALL_LUCK_TIMELINE, pivots)
        result = simulator.compute_chaos_coefficient(
            ALL_LUCK_TIMELINE, paths, "senior", pivots
        )
        assert result["luck_percentage"] > result["skill_percentage"], (
            f"Luck ({result['luck_percentage']}%) should exceed skill ({result['skill_percentage']}%) "
            f"for all-luck timeline"
        )

    def test_chaos_coefficient_in_range(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        result = simulator.compute_chaos_coefficient(
            MIXED_TIMELINE, paths, "senior", pivots
        )
        assert 0.0 <= result["chaos_coefficient"] <= 1.0

    def test_key_pivot_events_populated(self, simulator: ChaosSimulator) -> None:
        pivots = simulator.identify_pivot_points(MIXED_TIMELINE)
        paths = simulator.simulate_alternate_paths(MIXED_TIMELINE, pivots)
        result = simulator.compute_chaos_coefficient(
            MIXED_TIMELINE, paths, "senior", pivots
        )
        assert len(result["key_pivot_events"]) >= 1


# ══════════════════════════════════════════════════════════════════════
# Test: full simulation pipeline
# ══════════════════════════════════════════════════════════════════════

class TestFullSimulation:

    def test_run_full_produces_valid_result(self, simulator: ChaosSimulator) -> None:
        result = simulator.run_full_simulation(
            user_id="test-user",
            events=MIXED_TIMELINE,
            current_level="senior",
        )
        assert result.user_id == "test-user"
        assert 0.0 <= result.chaos_coefficient <= 1.0
        assert len(result.alternate_paths) == 5
        total = result.skill_percentage + result.luck_percentage + result.timing_percentage
        assert abs(total - 100.0) <= 0.5

    def test_single_event_doesnt_crash(self, simulator: ChaosSimulator) -> None:
        result = simulator.run_full_simulation(
            user_id="single",
            events=SINGLE_EVENT_TIMELINE,
            current_level="student",
        )
        assert result.user_id == "single"
        total = result.skill_percentage + result.luck_percentage + result.timing_percentage
        assert abs(total - 100.0) <= 0.5
