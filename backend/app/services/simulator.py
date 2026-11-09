"""
Monte Carlo Chaos Simulator — the core engine of Chaos Budget.

Takes a user's real career timeline, identifies pivot points where luck
played a role, runs N counterfactual simulations by sampling alternate
outcomes at each pivot, and computes the Chaos Coefficient breakdown:
skill vs. luck vs. timing.
"""

from __future__ import annotations

import random
import uuid
from typing import List, Optional

import numpy as np

from app.models.timeline import (
    AlternatePath,
    CareerLevel,
    EventType,
    SimulationResult,
    TimelineEvent,
)
from app.services.field_profiles import get_profile
from app.utils.logger import logger

# ── Luck classification for event types ───────────────────────────────
# Maps event types and keyword cues to luck_weight ranges.

# HIGH luck dependency: outcome was largely outside user's control
HIGH_LUCK_KEYWORDS = frozenset({
    "campus placement", "referral", "layoff", "laid off", "fired",
    "recession", "funding winter", "economic", "downturn", "shutdown",
    "random", "lucky", "chance", "relocation", "visa", "lottery",
    "acqui-hire", "merger", "acquisition",
})

# MEDIUM luck dependency: mix of preparation and opportunity
MED_LUCK_KEYWORDS = frozenset({
    "startup", "competition", "hackathon", "scholarship", "grant",
    "fellowship", "award", "promotion", "transferred", "selected",
    "noticed", "spotted", "recommended",
})

CAREER_LEVELS = ["student", "junior", "mid", "senior", "lead", "executive"]

# Alternate outcome templates for when a lucky event doesn't happen
ALTERNATE_OUTCOMES: dict[str, list[str]] = {
    "job": [
        "Stayed at previous position",
        "Took a different role at a smaller company",
        "Went through a longer job search",
        "Pivoted to a different domain",
        "Accepted a lower-level role elsewhere",
    ],
    "failure": [
        "Company survived the downturn",
        "Stayed employed through the crisis",
        "Was retained despite layoffs",
        "Company pivoted successfully",
    ],
    "achievement": [
        "Did not win the competition",
        "Missed the selection cut-off",
        "Achievement went unrecognised",
        "Award went to someone else",
    ],
    "education": [
        "Attended a different institution",
        "Took a gap year",
        "Chose a different major",
        "Didn't get the scholarship",
    ],
    "relocation": [
        "Stayed in original city",
        "Moved to a different city",
        "Remote work instead of relocation",
    ],
    "default": [
        "Event did not occur",
        "Took a different path entirely",
        "Missed this opportunity",
    ],
}


class ChaosSimulator:
    """
    Monte Carlo simulation engine for counterfactual career analysis.

    Given a user's real timeline, identifies pivot points, simulates
    N alternate career paths, and computes the Chaos Coefficient.

    Uses field-specific profiles (tech, medicine, finance, law, management,
    academia) to tune luck weights and career transition probabilities.
    """

    def __init__(self, seed: Optional[int] = None, field: str = "") -> None:
        """
        Args:
            seed: Optional RNG seed for reproducible simulations.
            field: User's field of work (e.g. "software engineering").
                   Loads a field-specific profile for tuned parameters.
        """
        self._rng = np.random.default_rng(seed)
        self._py_rng = random.Random(seed)

        # Load field-specific profile
        self._profile = get_profile(field)
        self._field = field
        self._event_luck_bias = {
            EventType(k): v
            for k, v in self._profile["event_luck_bias"].items()
        }
        self._career_transitions = self._profile["career_transitions"]
        self._negative_transitions = self._profile["negative_transitions"]
        self._keyword_multiplier = self._profile.get("keyword_boost_multiplier", 1.0)

        logger.info(
            f"ChaosSimulator initialised (seed={seed}, "
            f"field='{field}' → profile='{self._profile['description']}')"
        )

    def _compute_luck_weight(self, event: TimelineEvent) -> float:
        """
        Compute a luck_weight (0.0 = pure skill, 1.0 = pure luck)
        for a single event based on its type, description, self_rating,
        and the field-specific profile.
        """
        # Start with field-specific event type bias
        base_weight = self._event_luck_bias.get(event.event_type, 0.40)

        # Scan title + description for luck keywords
        text = f"{event.title} {event.description or ''}".lower()

        high_hits = sum(1 for kw in HIGH_LUCK_KEYWORDS if kw in text)
        med_hits = sum(1 for kw in MED_LUCK_KEYWORDS if kw in text)

        keyword_boost = min(
            (high_hits * 0.15 + med_hits * 0.08) * self._keyword_multiplier,
            0.40,
        )

        # Self-rating inversely correlates with luck
        # Rating 10 → luck_modifier = -0.25; Rating 1 → luck_modifier = +0.25
        self_rating_modifier = (5 - event.self_rating) * 0.05

        luck_weight = base_weight + keyword_boost + self_rating_modifier
        return max(0.05, min(0.95, luck_weight))  # Clamp to [0.05, 0.95]

    def identify_pivot_points(
        self, events: List[TimelineEvent]
    ) -> List[dict]:
        """
        Classify each event by its luck dependency and identify pivot points.

        A pivot point is any event with luck_weight ≥ 0.3 (i.e. luck played
        a meaningful role in the outcome).

        Args:
            events: The user's chronological timeline events.

        Returns:
            List of dicts with keys: event, luck_weight, luck_category.
        """
        if not events:
            return []

        pivots: List[dict] = []
        for event in events:
            luck_weight = self._compute_luck_weight(event)

            if luck_weight >= 0.6:
                category = "HIGH"
            elif luck_weight >= 0.35:
                category = "MEDIUM"
            else:
                category = "LOW"

            pivots.append({
                "event": event,
                "luck_weight": round(luck_weight, 3),
                "luck_category": category,
                "title": event.title,
                "year": event.year,
            })

        # Sort by luck_weight descending — most pivotal first
        pivots.sort(key=lambda p: p["luck_weight"], reverse=True)

        logger.info(
            f"Identified {len(pivots)} events as potential pivots: "
            f"HIGH={sum(1 for p in pivots if p['luck_category'] == 'HIGH')}, "
            f"MED={sum(1 for p in pivots if p['luck_category'] == 'MEDIUM')}, "
            f"LOW={sum(1 for p in pivots if p['luck_category'] == 'LOW')}"
        )
        return pivots

    def _sample_career_level(
        self, current_level: str, positive_event: bool
    ) -> str:
        """Sample the next career level from the field-specific Markov chain."""
        transitions = (
            self._career_transitions if positive_event
            else self._negative_transitions
        )
        probs_dict = transitions.get(current_level, self._career_transitions["junior"])
        levels = list(probs_dict.keys())
        probs = list(probs_dict.values())

        # Normalise (safety net)
        total = sum(probs)
        probs = [p / total for p in probs]

        return self._rng.choice(levels, p=probs)

    def _generate_alternate_event(
        self, original: TimelineEvent, lucky_event_happened: bool
    ) -> dict:
        """Create a description of what happened at this point in the alternate path."""
        if lucky_event_happened:
            return {
                "year": original.year,
                "title": original.title,
                "outcome": "Same as actual path",
                "diverged": False,
            }
        else:
            event_key = original.event_type.value
            options = ALTERNATE_OUTCOMES.get(event_key, ALTERNATE_OUTCOMES["default"])
            alt_outcome = self._py_rng.choice(options)
            return {
                "year": original.year,
                "title": original.title,
                "outcome": alt_outcome,
                "diverged": True,
            }

    def simulate_alternate_paths(
        self,
        events: List[TimelineEvent],
        pivot_points: List[dict],
        n_simulations: int = 1000,
    ) -> List[AlternatePath]:
        """
        Run N Monte Carlo simulations of alternate career trajectories.

        At each pivot point, we sample whether the lucky event occurred
        (probability = 1 - luck_weight). If not, we substitute an alternate
        outcome and propagate the career trajectory forward.

        Args:
            events: The user's real timeline events.
            pivot_points: Output from identify_pivot_points().
            n_simulations: Number of simulations to run (default 1000).

        Returns:
            The top 5 most divergent alternate paths as AlternatePath objects.
        """
        if not events or not pivot_points:
            logger.warning("No events or pivots — returning empty paths")
            return []

        # Build a lookup: event_id → pivot info
        pivot_map = {p["event"].id: p for p in pivot_points}

        # Track all simulation outcomes for chaos coefficient
        simulated_outcomes: List[str] = []
        all_paths: List[dict] = []

        for sim_idx in range(n_simulations):
            path_events: List[dict] = []
            current_level = "student"  # Start from student
            divergence_point: Optional[str] = None
            num_divergences = 0

            for event in events:
                pivot = pivot_map.get(event.id)

                if pivot:
                    luck_weight = pivot["luck_weight"]
                    # Did this lucky event happen in this simulation?
                    lucky_happened = self._rng.random() > luck_weight

                    alt_event = self._generate_alternate_event(event, lucky_happened)
                    path_events.append(alt_event)

                    if not lucky_happened:
                        num_divergences += 1
                        if divergence_point is None:
                            divergence_point = event.title
                        # Negative transition when a positive event doesn't happen
                        is_positive = event.event_type not in (
                            EventType.FAILURE, EventType.RELOCATION
                        )
                        current_level = self._sample_career_level(
                            current_level,
                            positive_event=not is_positive,  # Inverted: failure not happening is positive
                        )
                    else:
                        is_positive = event.event_type not in (
                            EventType.FAILURE,
                        )
                        current_level = self._sample_career_level(
                            current_level,
                            positive_event=is_positive,
                        )
                else:
                    # Non-pivot event: always happens, skill-driven progression
                    path_events.append({
                        "year": event.year,
                        "title": event.title,
                        "outcome": "Same as actual path",
                        "diverged": False,
                    })
                    current_level = self._sample_career_level(
                        current_level, positive_event=True
                    )

            simulated_outcomes.append(current_level)
            all_paths.append({
                "events": path_events,
                "final_level": current_level,
                "divergence_point": divergence_point or "No divergence",
                "num_divergences": num_divergences,
            })

        # Select top 5 most divergent paths (highest num_divergences, then variety)
        all_paths.sort(key=lambda p: p["num_divergences"], reverse=True)

        # Pick diverse final outcomes from the top divergent paths
        seen_levels = set()
        selected: List[dict] = []
        for path in all_paths:
            level = path["final_level"]
            if level not in seen_levels or len(selected) < 5:
                selected.append(path)
                seen_levels.add(level)
            if len(selected) >= 5:
                break

        # If we still don't have 5, fill from remaining
        if len(selected) < 5:
            for path in all_paths:
                if path not in selected:
                    selected.append(path)
                if len(selected) >= 5:
                    break

        # Convert to AlternatePath objects
        alternate_paths: List[AlternatePath] = []
        for path in selected[:5]:
            level_label = path["final_level"]
            # Generate a narrative outcome description
            outcome_narratives = {
                "student": "Still in education or early career exploration",
                "junior": "Entry-level position, building foundational skills",
                "mid": "Mid-level professional with solid experience",
                "senior": "Senior professional with deep expertise",
                "lead": "Team/tech lead driving major initiatives",
                "executive": "Executive leadership role",
            }
            alternate_paths.append(
                AlternatePath(
                    events=path["events"],
                    final_outcome=outcome_narratives.get(level_label, level_label),
                    outcome_level=level_label,
                    divergence_point=path["divergence_point"],
                )
            )

        # Store simulated outcomes for chaos computation
        self._last_simulated_outcomes = simulated_outcomes

        logger.info(
            f"Completed {n_simulations} simulations. "
            f"Outcome distribution: {self._outcome_distribution(simulated_outcomes)}"
        )
        return alternate_paths

    def _outcome_distribution(self, outcomes: List[str]) -> dict[str, str]:
        """Compute percentage distribution of simulated outcomes."""
        total = len(outcomes)
        if total == 0:
            return {}
        dist = {}
        for level in CAREER_LEVELS:
            count = outcomes.count(level)
            dist[level] = f"{count / total * 100:.1f}%"
        return dist

    def compute_chaos_coefficient(
        self,
        user_events: List[TimelineEvent],
        simulated_paths: List[AlternatePath],
        user_current_level: str,
        pivot_points: Optional[List[dict]] = None,
    ) -> dict:
        """
        Compute the Chaos Coefficient and skill/luck/timing breakdown.

        chaos_coefficient: how much of the user's position is luck.

        For mid/senior+ levels this is mostly "what fraction of simulated
        yous ended up BELOW your real level" (classic counterfactual luck).

        For students (floor of the ladder) that fraction is always 0 —
        nobody can finish below student — so we blend pivot-event luck
        weights with how much simulated outcomes fan out instead.

        skill_percentage: derived from self_ratings of LOW-luck events.
        luck_percentage: weighted sum of luck_weights at pivot points.
        timing_percentage: residual = 100 - skill - luck.

        Args:
            user_events: The user's real timeline.
            simulated_paths: From simulate_alternate_paths().
            user_current_level: The user's stated current career level.
            pivot_points: From identify_pivot_points() (optional, recomputed if None).

        Returns:
            Dict with chaos_coefficient, skill/luck/timing percentages,
            and key_pivot_events.
        """
        if pivot_points is None:
            pivot_points = self.identify_pivot_points(user_events)

        # ── Chaos coefficient from simulation outcomes ────────────────
        simulated_outcomes = getattr(self, "_last_simulated_outcomes", [])
        avg_luck = (
            float(np.mean([p["luck_weight"] for p in pivot_points]))
            if pivot_points else 0.4
        )

        if simulated_outcomes:
            user_ordinal = (
                CAREER_LEVELS.index(user_current_level)
                if user_current_level in CAREER_LEVELS else 2
            )
            ordinals = [CAREER_LEVELS.index(o) for o in simulated_outcomes]
            n = len(ordinals)
            below_frac = sum(1 for o in ordinals if o < user_ordinal) / n
            max_spread = float(len(CAREER_LEVELS) - 1)
            spread = float(np.std(ordinals) / max_spread) if max_spread else 0.0

            if user_ordinal <= 0:
                # Student / career floor: rank-vs-below is always 0.
                chaos_coefficient = 0.6 * avg_luck + 0.4 * spread
            else:
                chaos_coefficient = 0.7 * below_frac + 0.3 * avg_luck
        else:
            chaos_coefficient = avg_luck

        # ── Skill percentage (from LOW-luck self_ratings) ─────────────
        low_luck_events = [
            p["event"] for p in pivot_points
            if p["luck_category"] == "LOW"
        ]
        if low_luck_events:
            avg_skill_rating = np.mean([e.self_rating for e in low_luck_events])
        else:
            # Use all events' self_ratings as fallback
            avg_skill_rating = np.mean([e.self_rating for e in user_events]) if user_events else 5.0

        # Scale self_rating (1-10) to a percentage contribution
        raw_skill = (avg_skill_rating / 10.0) * 60  # Max ~60% from skill alone

        # ── Luck percentage (from pivot point luck_weights) ───────────
        if pivot_points:
            weighted_luck = np.mean([p["luck_weight"] for p in pivot_points])
        else:
            weighted_luck = 0.2

        raw_luck = weighted_luck * 60  # Max ~60% from luck alone

        # ── Timing (residual) ─────────────────────────────────────────
        raw_timing = max(10.0, 100.0 - raw_skill - raw_luck)

        # ── Normalise to sum to exactly 100% ──────────────────────────
        total = raw_skill + raw_luck + raw_timing
        skill_pct = round(raw_skill / total * 100, 1)
        luck_pct = round(raw_luck / total * 100, 1)
        timing_pct = round(100.0 - skill_pct - luck_pct, 1)

        # Safety: ensure non-negative
        if timing_pct < 0:
            timing_pct = 0.0
            total2 = skill_pct + luck_pct
            skill_pct = round(skill_pct / total2 * 100, 1)
            luck_pct = round(100.0 - skill_pct, 1)

        # ── Key pivot events (top luck-heavy events) ──────────────────
        key_pivots = [
            p["title"] for p in pivot_points
            if p["luck_category"] in ("HIGH", "MEDIUM")
        ][:5]

        chaos_coefficient = round(max(0.0, min(1.0, chaos_coefficient)), 3)

        logger.info(
            f"Chaos Coefficient: {chaos_coefficient} — "
            f"Skill: {skill_pct}%, Luck: {luck_pct}%, Timing: {timing_pct}%"
        )

        return {
            "chaos_coefficient": chaos_coefficient,
            "skill_percentage": skill_pct,
            "luck_percentage": luck_pct,
            "timing_percentage": timing_pct,
            "key_pivot_events": key_pivots,
        }

    def run_full_simulation(
        self,
        user_id: str,
        events: List[TimelineEvent],
        current_level: str,
        field: str = "",
        n_simulations: int = 1000,
    ) -> SimulationResult:
        """
        Run the complete simulation pipeline: identify pivots → simulate
        alternate paths → compute chaos coefficient → return SimulationResult.

        This is the main entry point for the simulation engine.

        Args:
            user_id: The user's ID.
            events: The user's timeline events.
            current_level: The user's current career level string.
            field: The user's field of work (used for logging).
            n_simulations: Number of Monte Carlo simulations (default 1000).

        Returns:
            A fully populated SimulationResult object.
        """
        logger.info(
            f"Starting full simulation for user={user_id}, "
            f"events={len(events)}, level={current_level}, "
            f"field='{field}' → {self._profile['description']}, N={n_simulations}"
        )

        # Step 1: Identify pivot points
        pivot_points = self.identify_pivot_points(events)

        # Step 2: Simulate alternate paths
        alternate_paths = self.simulate_alternate_paths(
            events, pivot_points, n_simulations
        )

        # Step 3: Compute chaos coefficient (simulation-based)
        breakdown = self.compute_chaos_coefficient(
            user_events=events,
            simulated_paths=alternate_paths,
            user_current_level=current_level,
            pivot_points=pivot_points,
        )

        # Step 4: Causal inference — blend with simulation
        causal_confidence: float | None = None
        try:
            from app.services.causal import CausalAnalyzer

            causal = CausalAnalyzer()
            causal_result = causal.estimate_luck_effect(events, current_level)
            ate = causal_result["ate"]
            causal_confidence = causal_result["confidence"]

            # Blend: 70% simulation luck + 30% causal ATE (scaled to %)
            sim_luck = breakdown["luck_percentage"]
            # ATE is on [-1, 1] scale; map to [0, 100] for blending
            causal_luck = (ate + 1.0) / 2.0 * 100.0  # -1→0%, 0→50%, 1→100%
            blended_luck = 0.70 * sim_luck + 0.30 * causal_luck

            # Re-normalise all three to sum to 100%
            raw_skill = breakdown["skill_percentage"]
            raw_timing = breakdown["timing_percentage"]
            total = raw_skill + blended_luck + raw_timing
            if total > 0:
                breakdown["skill_percentage"] = round(raw_skill / total * 100, 1)
                breakdown["luck_percentage"] = round(blended_luck / total * 100, 1)
                breakdown["timing_percentage"] = round(
                    100.0 - breakdown["skill_percentage"] - breakdown["luck_percentage"], 1
                )
                # Safety: clamp timing to non-negative
                if breakdown["timing_percentage"] < 0:
                    breakdown["timing_percentage"] = 0.0
                    s = breakdown["skill_percentage"] + breakdown["luck_percentage"]
                    breakdown["skill_percentage"] = round(breakdown["skill_percentage"] / s * 100, 1)
                    breakdown["luck_percentage"] = round(100.0 - breakdown["skill_percentage"], 1)

            logger.info(
                f"Causal blend applied — ATE={ate:.4f}, confidence={causal_confidence}, "
                f"blended luck={breakdown['luck_percentage']}%"
            )
        except Exception as exc:
            logger.warning(f"Causal integration skipped: {exc}")

        # Step 5: Build result
        result = SimulationResult(
            user_id=user_id,
            chaos_coefficient=breakdown["chaos_coefficient"],
            skill_percentage=breakdown["skill_percentage"],
            luck_percentage=breakdown["luck_percentage"],
            timing_percentage=breakdown["timing_percentage"],
            alternate_paths=alternate_paths,
            key_pivot_events=breakdown["key_pivot_events"],
            causal_confidence=causal_confidence,
        )

        logger.info(f"Simulation complete for user={user_id}")
        return result
