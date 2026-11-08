"""
Narrative Explainer Service — generates Groq-powered career analysis narratives.

Produces a 4-section explanation of the user's Chaos Budget results plus
a practical "surgery suggestion" for reducing future chaos dependency.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from groq import Groq

from app.config import get_settings
from app.models.timeline import SimulationResult, TimelineEvent
from app.utils.logger import logger

# ── Model config (same as parser) ────────────────────────────────────
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"

# ── System prompts ────────────────────────────────────────────────────

EXPLANATION_SYSTEM_PROMPT = """You are a thoughtful career analyst. Be honest, nuanced, never preachy. Avoid toxic positivity. You speak directly and specifically — never in generic platitudes.

Given a person's career timeline events and their Chaos Budget simulation results, generate a JSON object with exactly these 4 keys:

1. "chaos_story": 2-3 paragraphs narrating their ACTUAL career path. Name specific pivot moments by title. Describe how luck and skill intertwined at each turn. Be vivid and specific, not generic.

2. "what_skill_built": A concrete paragraph about the specific skills, decisions, and deliberate actions that genuinely moved the needle in their career. Name the actual events and what made them high-skill.

3. "what_luck_shaped": A concrete paragraph about the specific lucky or unlucky events and their tangible impact on trajectory. Don't sugarcoat — if a layoff derailed them or a random referral made their career, say so.

4. "alternate_you": 1 paragraph describing the most divergent alternate path — paint a picture of that version of them. Where do they work? What's their life like? Make it feel real, not hypothetical.

RULES:
- Return ONLY valid JSON with those 4 keys. No markdown, no preamble.
- Each section should be 2-5 sentences. Total should be under 500 words.
- Reference specific events from the timeline by name.
- Be honest about what was luck and what was skill — people respect directness.
- Never use phrases like "everything happens for a reason" or "it all worked out"."""

SURGERY_SYSTEM_PROMPT = """You are a practical career strategist. Given someone's Chaos Budget results, write ONE paragraph (3-4 sentences) starting with: "If you wanted to reduce your chaos coefficient going forward..."

Be specific and actionable. Reference their actual field and skill gaps. Don't be generic — tailor to their situation. Max 100 words.

Return ONLY the paragraph text. No JSON, no markdown."""


class NarrativeExplainer:
    """Generates Groq-powered narrative explanations of Chaos Budget results."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("NarrativeExplainer initialised")

    def _call_groq(
        self,
        messages: list[dict],
        model: str = PRIMARY_MODEL,
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> str:
        """Make a Groq chat completion call with logging."""
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage
            logger.info(
                f"Groq explainer call — model={model}, "
                f"prompt_tokens={usage.prompt_tokens}, "
                f"completion_tokens={usage.completion_tokens}"
            )
            return content.strip()
        except Exception as exc:
            logger.error(f"Groq explainer call failed (model={model}): {exc}")
            raise

    def _extract_json_object(self, text: str) -> dict:
        """Extract a JSON object from a response that may have markdown or preamble."""
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.strip().rstrip("`")

        # Try direct parse
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in text (greedy from first { to last })
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            candidate = cleaned[first_brace:last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try fixing common issues: trailing commas, unescaped newlines
                fixed = re.sub(r",\s*}", "}", candidate)
                fixed = re.sub(r",\s*]", "]", fixed)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass

        raise ValueError(f"Could not extract JSON object from response: {text[:300]}...")

    def _build_context(
        self,
        events: List[TimelineEvent],
        result: SimulationResult,
    ) -> str:
        """Build the user context string sent to Groq."""
        event_summaries = []
        for e in events:
            org = f" at {e.organization}" if e.organization else ""
            desc = f" — {e.description}" if e.description else ""
            event_summaries.append(
                f"- {e.year}: [{e.event_type.value}] {e.title}{org} "
                f"(self_rating: {e.self_rating}/10){desc}"
            )

        alt_paths = []
        for i, path in enumerate(result.alternate_paths[:3], 1):
            alt_paths.append(
                f"  Path {i}: Diverged at '{path.divergence_point}' → "
                f"ended at {path.outcome_level} level ({path.final_outcome})"
            )

        return f"""TIMELINE EVENTS:
{chr(10).join(event_summaries)}

SIMULATION RESULTS:
- Chaos Coefficient: {result.chaos_coefficient} ({result.chaos_coefficient * 100:.0f}% of simulated peers ended up below current level)
- Skill: {result.skill_percentage}%
- Luck: {result.luck_percentage}%
- Timing: {result.timing_percentage}%
- Key Pivot Events: {', '.join(result.key_pivot_events)}
- Causal Confidence: {result.causal_confidence or 'N/A'}

TOP ALTERNATE PATHS:
{chr(10).join(alt_paths)}"""

    def generate_explanation(
        self,
        events: List[TimelineEvent],
        result: SimulationResult,
        max_retries: int = 2,
    ) -> dict:
        """
        Generate a 4-section narrative explanation of the user's career analysis.

        Returns dict with keys: chaos_story, what_skill_built, what_luck_shaped, alternate_you

        Args:
            events: The user's timeline events.
            result: The simulation result.
            max_retries: Number of retry attempts.

        Returns:
            Dict with 4 narrative sections.

        Raises:
            ValueError: If all retries fail.
        """
        context = self._build_context(events, result)
        messages = [
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]

        required_keys = {"chaos_story", "what_skill_built", "what_luck_shaped", "alternate_you"}
        last_error: Optional[Exception] = None
        models = [PRIMARY_MODEL, FALLBACK_MODEL]

        for model in models:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Generating explanation — model={model}, attempt={attempt}")
                    raw = self._call_groq(messages, model=model, max_tokens=1200)
                    explanation = self._extract_json_object(raw)

                    # Validate all required keys are present
                    missing = required_keys - set(explanation.keys())
                    if missing:
                        raise ValueError(f"Missing keys in explanation: {missing}")

                    # Ensure all values are non-empty strings
                    for key in required_keys:
                        if not isinstance(explanation[key], str) or not explanation[key].strip():
                            raise ValueError(f"Key '{key}' is empty or not a string")

                    logger.info("Explanation generated successfully")
                    return explanation

                except Exception as exc:
                    last_error = exc
                    logger.warning(f"Explanation attempt {attempt} failed (model={model}): {exc}")

        raise ValueError(f"Failed to generate explanation after all retries. Last error: {last_error}")

    def generate_surgery_suggestion(
        self,
        events: List[TimelineEvent],
        result: SimulationResult,
        max_retries: int = 2,
    ) -> str:
        """
        Generate a practical suggestion for reducing future chaos coefficient.

        Args:
            events: The user's timeline events.
            result: The simulation result.
            max_retries: Number of retry attempts.

        Returns:
            A single paragraph string with actionable advice.
        """
        context = self._build_context(events, result)
        messages = [
            {"role": "system", "content": SURGERY_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]

        last_error: Optional[Exception] = None
        models = [PRIMARY_MODEL, FALLBACK_MODEL]

        for model in models:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Generating surgery suggestion — model={model}, attempt={attempt}")
                    raw = self._call_groq(messages, model=model, max_tokens=200, temperature=0.6)

                    # Clean up: strip markdown, quotes, etc.
                    suggestion = raw.strip().strip('"').strip("'").strip()
                    if len(suggestion) < 20:
                        raise ValueError("Surgery suggestion too short")

                    logger.info("Surgery suggestion generated successfully")
                    return suggestion

                except Exception as exc:
                    last_error = exc
                    logger.warning(f"Surgery suggestion attempt {attempt} failed (model={model}): {exc}")

        # Graceful fallback — never let this block the whole response
        logger.error(f"Surgery suggestion failed completely: {last_error}")
        return (
            "If you wanted to reduce your chaos coefficient going forward, "
            "focus on building skills and credentials that are portable across "
            "companies and economic conditions — things like certifications, "
            "open-source contributions, and a strong public portfolio."
        )
