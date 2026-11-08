"""
Timeline Parser Service — extracts structured career events from raw text or PDF.

Uses the Groq API to parse resume/LinkedIn pastes into TimelineEvent objects.
Supports PDF resume uploads via PyMuPDF text extraction.
Includes retry logic, JSON validation, and token usage logging.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

import pymupdf
from groq import Groq

from app.config import get_settings
from app.models.timeline import EventType, TimelineEvent
from app.utils.logger import logger

# ── Groq model config ────────────────────────────────────────────────
# Primary: largest model for best structured extraction
# Fallback: lighter model if primary is overloaded
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"

# ── System prompt for structured extraction ───────────────────────────
EXTRACTION_SYSTEM_PROMPT = """You are a career timeline extraction engine.
Given raw text about someone's career or life, extract a JSON array of events.

Each event MUST have these fields:
- "year": integer (the year it happened)
- "month": integer or null (month 1-12 if known, null otherwise)
- "event_type": one of ["education", "job", "skill", "achievement", "failure", "relocation", "personal", "other"]
- "title": string (concise event title, max 100 chars)
- "organization": string or null (company, school, institution name)
- "description": string or null (1-2 sentence description)
- "self_rating": integer 1-10 (how much personal effort/skill contributed — infer from language cues: "worked hard", "competitive", "earned" = high 7-10; "got lucky", "randomly", "campus placement" = lower 3-6; neutral = 5)
- "duration_months": integer or null (approximate duration in months)

RULES:
1. Return ONLY a valid JSON array. No markdown, no preamble, no explanation.
2. Sort events chronologically by year, then month.
3. Extract EVERY distinct career/life event mentioned.
4. For campus placements, treat as "job" event_type.
5. For layoffs, treat as "failure" event_type.
6. For freelancing periods, treat as "job" event_type.
7. If year is ambiguous, make your best estimate from context.
8. self_rating reflects how much the PERSON controlled the outcome, not how good the outcome was.

Example output format:
[{"year": 2021, "month": 6, "event_type": "education", "title": "Graduated B.Tech CS", "organization": "NIT", "description": "Completed undergraduate degree in Computer Science", "self_rating": 7, "duration_months": 48}]"""


class TimelineParser:
    """Parses raw career text into structured TimelineEvent objects via Groq."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("TimelineParser initialised with Groq client")

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> str:
        """
        Extract plain text from a PDF file's raw bytes using PyMuPDF.

        Args:
            pdf_bytes: The raw bytes of the uploaded PDF file.

        Returns:
            Concatenated text from all pages.

        Raises:
            ValueError: If the PDF is empty, unreadable, or contains no text.
        """
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            logger.error(f"Failed to open PDF: {exc}")
            raise ValueError(
                "Could not open the uploaded file as a PDF. "
                "Please ensure it is a valid PDF document."
            ) from exc

        if doc.page_count == 0:
            raise ValueError("The PDF has no pages.")

        text_parts: list[str] = []
        num_pages = doc.page_count
        for page_num in range(num_pages):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise ValueError(
                "The PDF contains no extractable text. "
                "It may be a scanned image — try copy-pasting the text instead."
            )

        logger.info(f"Extracted {len(full_text)} chars from {num_pages}-page PDF")
        return full_text

    def parse_pdf(self, pdf_bytes: bytes, max_retries: int = 2) -> List[TimelineEvent]:
        """
        Extract text from a PDF resume and parse it into timeline events.

        Convenience method that chains extract_text_from_pdf → parse_raw_text.

        Args:
            pdf_bytes: Raw bytes of the uploaded PDF.
            max_retries: Retry count for the Groq parsing step.

        Returns:
            List of validated, chronologically sorted TimelineEvent objects.
        """
        text = self.extract_text_from_pdf(pdf_bytes)
        return self.parse_raw_text(text, max_retries=max_retries)

    def _call_groq(
        self,
        messages: list[dict],
        model: str = PRIMARY_MODEL,
        max_tokens: int = 2000,
        temperature: float = 0.1,
    ) -> str:
        """
        Make a chat completion call to Groq and return the content string.

        Logs model, token usage, and latency.
        """
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
                f"Groq call — model={model}, "
                f"prompt_tokens={usage.prompt_tokens}, "
                f"completion_tokens={usage.completion_tokens}, "
                f"total_tokens={usage.total_tokens}"
            )
            return content.strip()
        except Exception as exc:
            logger.error(f"Groq API call failed (model={model}): {exc}")
            raise

    def _extract_json_array(self, text: str) -> list:
        """
        Extract a JSON array from text that may contain markdown fences
        or other wrapper content.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.strip().rstrip("`")

        # Try parsing directly
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            # Some models wrap in {"events": [...]}
            if isinstance(parsed, dict):
                for key in ("events", "data", "results", "timeline"):
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
            raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
        except json.JSONDecodeError:
            pass

        # Try to find array within the text
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON array from response: {text[:200]}...")

    def _raw_event_to_timeline_event(self, raw: dict) -> Optional[TimelineEvent]:
        """
        Convert a raw dict from Groq into a validated TimelineEvent.
        Returns None if the event is malformed (logs a warning instead of crashing).
        """
        try:
            # Normalise event_type to lowercase
            event_type_raw = str(raw.get("event_type", "other")).lower().strip()
            valid_types = {e.value for e in EventType}
            if event_type_raw not in valid_types:
                event_type_raw = "other"

            # Clamp self_rating to 1-10
            self_rating = raw.get("self_rating", 5)
            if not isinstance(self_rating, (int, float)):
                self_rating = 5
            self_rating = max(1, min(10, int(self_rating)))

            # Clamp year
            year = int(raw.get("year", 2020))
            year = max(1950, min(2030, year))

            # Month
            month = raw.get("month")
            if month is not None:
                month = int(month)
                if month < 1 or month > 12:
                    month = None

            # Duration
            duration = raw.get("duration_months")
            if duration is not None:
                duration = max(0, int(duration))

            return TimelineEvent(
                year=year,
                month=month,
                event_type=EventType(event_type_raw),
                title=str(raw.get("title", "Untitled event"))[:300],
                organization=raw.get("organization"),
                description=raw.get("description"),
                self_rating=self_rating,
                duration_months=duration,
            )
        except Exception as exc:
            logger.warning(f"Skipping malformed event: {raw} — {exc}")
            return None

    def parse_raw_text(self, text: str, max_retries: int = 2) -> List[TimelineEvent]:
        """
        Parse raw resume/LinkedIn text into structured TimelineEvent objects.

        Uses Groq API with retry logic for malformed JSON responses.
        Falls back to the secondary model on primary failure.

        Args:
            text: The raw career description text.
            max_retries: Maximum number of retry attempts (default 2).

        Returns:
            List of validated TimelineEvent objects, sorted chronologically.

        Raises:
            ValueError: If all retries fail to produce valid events.
        """
        if not text or not text.strip():
            raise ValueError("Input text is empty — nothing to parse.")

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": text.strip()},
        ]

        last_error: Optional[Exception] = None
        models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

        for model in models_to_try:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(
                        f"Parsing raw text — model={model}, "
                        f"attempt={attempt}/{max_retries}, "
                        f"text_length={len(text)}"
                    )
                    raw_response = self._call_groq(messages, model=model)
                    raw_events = self._extract_json_array(raw_response)

                    # Convert each raw dict to a validated TimelineEvent
                    events = []
                    for raw_evt in raw_events:
                        evt = self._raw_event_to_timeline_event(raw_evt)
                        if evt is not None:
                            events.append(evt)

                    if not events:
                        raise ValueError(
                            "Groq returned JSON but no valid events could be extracted."
                        )

                    # Sort chronologically
                    events.sort(key=lambda e: (e.year, e.month or 0))

                    logger.info(
                        f"Successfully parsed {len(events)} events from raw text"
                    )
                    return events

                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        f"Parse attempt {attempt}/{max_retries} failed "
                        f"(model={model}): {exc}"
                    )

        raise ValueError(
            f"Failed to parse text after all retries. Last error: {last_error}"
        )

    def parse_form_events(self, events: List[dict]) -> List[TimelineEvent]:
        """
        Validate and normalise manually entered form events.

        Fills missing optional fields with sensible defaults and
        sorts events chronologically.

        Args:
            events: List of dicts from the frontend form.

        Returns:
            List of validated, sorted TimelineEvent objects.

        Raises:
            ValueError: If no valid events could be constructed.
        """
        if not events:
            raise ValueError("No events provided.")

        validated: List[TimelineEvent] = []
        for i, raw in enumerate(events):
            # Fill defaults for optional fields
            raw.setdefault("description", None)
            raw.setdefault("organization", None)
            raw.setdefault("month", None)
            raw.setdefault("duration_months", None)
            raw.setdefault("self_rating", 5)

            evt = self._raw_event_to_timeline_event(raw)
            if evt is not None:
                validated.append(evt)
            else:
                logger.warning(f"Form event at index {i} is invalid and was skipped.")

        if not validated:
            raise ValueError("No valid events could be constructed from the form data.")

        # Sort chronologically
        validated.sort(key=lambda e: (e.year, e.month or 0))

        logger.info(f"Validated {len(validated)} form events")
        return validated
