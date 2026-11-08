"""
Causal Inference Layer — uses DoWhy to estimate the causal effect of
lucky events on career outcome.

Builds a causal graph, converts timeline events to a feature DataFrame,
and estimates the Average Treatment Effect (ATE) of luck on outcome.
Falls back to a heuristic when there's insufficient data for causal estimation.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd
from app.models.timeline import CareerLevel, EventType, TimelineEvent
from app.utils.logger import logger

# ── Career level ordinal mapping ──────────────────────────────────────
LEVEL_ORDINAL = {
    "student": 0, "junior": 1, "mid": 2,
    "senior": 3, "lead": 4, "executive": 5,
}

# Event types with high luck dependency
HIGH_LUCK_TYPES = frozenset({
    EventType.FAILURE, EventType.RELOCATION, EventType.PERSONAL,
})

# Keywords that signal luck involvement
LUCK_KEYWORDS = frozenset({
    "campus placement", "referral", "layoff", "laid off", "recession",
    "funding winter", "random", "lucky", "chance", "acqui-hire",
    "merger", "lottery", "visa", "relocation",
})


class CausalAnalyzer:
    """
    Estimates the causal effect of lucky events on career outcomes
    using DoWhy for causal inference with heuristic fallback.
    """

    def build_causal_graph(self, events: List[TimelineEvent]) -> str:
        """
        Build a GML causal graph string for DoWhy.

        The causal structure:
          - lucky_event → outcome
          - skill_level → outcome
          - timing → outcome
          - years_exp → outcome
          - years_exp → skill_level
          - field → outcome (confounder)
          - field → lucky_event (confounder)

        Args:
            events: The user's timeline events.

        Returns:
            GML string encoding the causal graph.
        """
        gml_graph = """graph [
  directed 1
  node [ id "lucky_event" label "lucky_event" ]
  node [ id "skill_level" label "skill_level" ]
  node [ id "timing" label "timing" ]
  node [ id "years_exp" label "years_exp" ]
  node [ id "field_type" label "field_type" ]
  node [ id "outcome" label "outcome" ]
  edge [ source "lucky_event" target "outcome" ]
  edge [ source "skill_level" target "outcome" ]
  edge [ source "timing" target "outcome" ]
  edge [ source "years_exp" target "outcome" ]
  edge [ source "years_exp" target "skill_level" ]
  edge [ source "field_type" target "outcome" ]
  edge [ source "field_type" target "lucky_event" ]
]"""
        return gml_graph

    def _events_to_dataframe(
        self,
        events: List[TimelineEvent],
        current_level: str,
        n_synthetic: int = 200,
    ) -> pd.DataFrame:
        """
        Convert timeline events into a feature DataFrame suitable for
        causal estimation. Since we have a single user, we generate
        synthetic counterfactual observations by perturbing the features.

        Features:
          - lucky_event (binary treatment): 1 if the event is high-luck
          - skill_level: average self_rating of skill/education events
          - timing: year normalised to [0, 1]
          - years_exp: approximate years of experience at each event
          - field_type: numeric hash of the field (confounder)
          - outcome: career level ordinal

        Args:
            events: Timeline events.
            current_level: User's current career level string.
            n_synthetic: Number of synthetic rows to generate.

        Returns:
            DataFrame with features for causal estimation.
        """
        if not events:
            return pd.DataFrame()

        rng = np.random.default_rng(42)
        rows: list[dict] = []

        # Extract features from real events
        min_year = min(e.year for e in events)
        max_year = max(e.year for e in events)
        year_range = max(max_year - min_year, 1)

        skill_ratings = [e.self_rating for e in events if e.event_type in (
            EventType.SKILL, EventType.EDUCATION, EventType.ACHIEVEMENT
        )]
        avg_skill = np.mean(skill_ratings) if skill_ratings else 5.0

        user_outcome = LEVEL_ORDINAL.get(current_level, 2)

        for event in events:
            text = f"{event.title} {event.description or ''}".lower()
            is_lucky = (
                event.event_type in HIGH_LUCK_TYPES
                or any(kw in text for kw in LUCK_KEYWORDS)
                or event.self_rating <= 3
            )
            rows.append({
                "lucky_event": int(is_lucky),
                "skill_level": event.self_rating / 10.0,
                "timing": (event.year - min_year) / year_range,
                "years_exp": (event.year - min_year),
                "field_type": 0,  # Single user, same field
                "outcome": user_outcome,
            })

        # Generate synthetic counterfactual observations
        for _ in range(n_synthetic):
            lucky = int(rng.random() < 0.5)
            skill = np.clip(rng.normal(avg_skill / 10.0, 0.15), 0.1, 1.0)
            timing = rng.random()
            years = rng.uniform(0, year_range)

            # Synthetic outcome: influenced by skill and luck
            base_outcome = skill * 3.0 + (1 - lucky) * 1.0 + timing * 0.5 + years * 0.2
            noise = rng.normal(0, 0.5)
            outcome = int(np.clip(round(base_outcome + noise), 0, 5))

            rows.append({
                "lucky_event": lucky,
                "skill_level": float(skill),
                "timing": float(timing),
                "years_exp": float(years),
                "field_type": 0,
                "outcome": outcome,
            })

        return pd.DataFrame(rows)

    def estimate_luck_effect(
        self,
        events: List[TimelineEvent],
        current_level: str,
    ) -> dict:
        """
        Estimate the Average Treatment Effect (ATE) of lucky events
        on career outcome using DoWhy.

        Treatment: presence of high-luck event (binary)
        Outcome: career level (ordinal 0-5)
        Confounders: skill_level, timing, years_exp, field_type

        Falls back to a heuristic when:
          - Too few events (< 3)
          - DoWhy estimation fails

        Args:
            events: The user's timeline events.
            current_level: User's current career level string.

        Returns:
            Dict with keys: ate, confidence, method
        """
        # Guard: need at least 3 events for meaningful estimation
        if len(events) < 3:
            logger.info(
                f"Only {len(events)} events — using heuristic fallback"
            )
            return self._heuristic_fallback(events, current_level)

        try:
            return self._dowhy_estimate(events, current_level)
        except Exception as exc:
            logger.warning(f"DoWhy estimation failed: {exc} — using heuristic fallback")
            return self._heuristic_fallback(events, current_level)

    def _dowhy_estimate(
        self,
        events: List[TimelineEvent],
        current_level: str,
    ) -> dict:
        """Run DoWhy causal estimation."""
        import dowhy
        from dowhy import CausalModel

        df = self._events_to_dataframe(events, current_level)
        gml_graph = self.build_causal_graph(events)

        logger.info(
            f"Running DoWhy estimation — {len(df)} observations, "
            f"treatment=lucky_event, outcome=outcome"
        )

        model = CausalModel(
            data=df,
            treatment="lucky_event",
            outcome="outcome",
            graph=gml_graph,
        )

        # Identify the causal effect
        identified_estimand = model.identify_effect(
            proceed_when_unidentifiable=True
        )

        # Estimate using linear regression (robust for small samples)
        estimate = model.estimate_effect(
            identified_estimand,
            method_name="backdoor.linear_regression",
        )

        ate = float(estimate.value)

        # Clamp ATE to [-1, 1] for interpretability
        ate = max(-1.0, min(1.0, ate))

        # Confidence: based on sample size and effect magnitude
        n_events = len(events)
        confidence = min(0.95, 0.3 + (n_events / 20.0) * 0.5 + abs(ate) * 0.2)
        confidence = round(confidence, 3)

        logger.info(
            f"DoWhy estimate — ATE={ate:.4f}, confidence={confidence}, "
            f"method=backdoor.linear_regression"
        )

        return {
            "ate": round(ate, 4),
            "confidence": confidence,
            "method": "dowhy_backdoor_linear_regression",
        }

    def _heuristic_fallback(
        self,
        events: List[TimelineEvent],
        current_level: str,
    ) -> dict:
        """
        Simple heuristic fallback when DoWhy can't run.
        Estimates luck effect from self_ratings and event types.
        """
        if not events:
            return {"ate": 0.0, "confidence": 0.1, "method": "heuristic_no_events"}

        luck_scores: list[float] = []
        for event in events:
            text = f"{event.title} {event.description or ''}".lower()
            is_lucky = (
                event.event_type in HIGH_LUCK_TYPES
                or any(kw in text for kw in LUCK_KEYWORDS)
                or event.self_rating <= 3
            )
            # Invert self_rating: low rating = high luck effect
            luck_effect = (10 - event.self_rating) / 10.0
            if is_lucky:
                luck_effect = min(1.0, luck_effect + 0.3)
            luck_scores.append(luck_effect)

        # ATE approximation: negative means luck REDUCES outcome
        # (lucky events are disruptive), positive means luck helps
        avg_luck = float(np.mean(luck_scores))

        # Translate to ATE scale: centered around 0
        ate = round(avg_luck - 0.5, 4)
        ate = max(-1.0, min(1.0, ate))

        confidence = round(min(0.6, 0.1 + len(events) * 0.05), 3)

        logger.info(
            f"Heuristic fallback — ATE={ate}, confidence={confidence}"
        )

        return {
            "ate": ate,
            "confidence": confidence,
            "method": "heuristic_fallback",
        }
