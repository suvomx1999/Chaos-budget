"""
Tests for the TimelineParser service.

Tests cover:
  1. Parsing a realistic software engineer resume
  2. Parsing a student timeline
  3. Handling garbled/invalid input gracefully
"""

from __future__ import annotations

import pytest

from app.models.timeline import EventType, TimelineEvent
from app.services.parser import TimelineParser

# ── Shared fixture ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def parser() -> TimelineParser:
    """Create a single parser instance for the whole module (saves Groq calls)."""
    return TimelineParser()


# ── Test data ─────────────────────────────────────────────────────────

SOFTWARE_ENGINEER_RESUME = """
Rahul Sharma — Senior Software Engineer

Education:
- B.Tech in Computer Science from NIT Trichy, 2017-2021. CGPA: 8.7. 
  Active in competitive programming, won 2 college-level hackathons.

Experience:
- Software Engineer at Flipkart (Jul 2021 - Jun 2022): Worked on the 
  search ranking team. Optimised Elasticsearch queries reducing latency by 40%.
  Got selected through campus placement.
- Backend Engineer at a stealth startup (Aug 2022 - Mar 2023): Joined as 
  employee #5. Built the entire payment microservice from scratch. 
  Company ran out of funding and shut down.
- Freelance Developer (Apr 2023 - Sep 2023): Built 4 client projects 
  including an e-commerce platform and a healthcare dashboard.
- Senior SDE at Atlassian (Oct 2023 - Present): Cracked the interview 
  after 3 months of prep. Leading the Jira automation backend team.

Skills: Python, Go, PostgreSQL, Redis, Kubernetes, System Design
"""

STUDENT_TIMELINE = """
I'm a 3rd year student at BITS Pilani studying ECE. In my first year I 
joined the coding club and learned Python. In second year I did a summer 
internship at a local startup where I built their landing page — honestly 
got the role through my senior's referral. This year I'm doing research 
with a professor on ML for signal processing. I also randomly won a 
hackathon last month which got me noticed by some VCs. Currently applying 
for summer internships at FAANG companies.
"""

GARBLED_INPUT = """
asdkjhasd 12312 !! @#$% 
no real career info here
just random characters and gibberish 
🎃🎃🎃 lorem ipsum dolor sit amet
"""


# ── Test cases ────────────────────────────────────────────────────────

class TestParseSoftwareEngineerResume:
    """Test parsing a detailed SWE resume with multiple events."""

    def test_returns_multiple_events(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(SOFTWARE_ENGINEER_RESUME)
        assert len(events) >= 4, f"Expected ≥4 events, got {len(events)}"

    def test_all_events_are_valid(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(SOFTWARE_ENGINEER_RESUME)
        for evt in events:
            assert isinstance(evt, TimelineEvent)
            assert 1950 <= evt.year <= 2030
            assert 1 <= evt.self_rating <= 10
            assert evt.event_type in EventType

    def test_events_are_chronological(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(SOFTWARE_ENGINEER_RESUME)
        years = [(e.year, e.month or 0) for e in events]
        assert years == sorted(years), "Events should be sorted chronologically"

    def test_contains_education_event(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(SOFTWARE_ENGINEER_RESUME)
        edu_events = [e for e in events if e.event_type == EventType.EDUCATION]
        assert len(edu_events) >= 1, "Should have at least 1 education event"


class TestParseStudentTimeline:
    """Test parsing a casual student career narrative."""

    def test_returns_events(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(STUDENT_TIMELINE)
        assert len(events) >= 3, f"Expected ≥3 events, got {len(events)}"

    def test_events_valid_and_chronological(self, parser: TimelineParser) -> None:
        events = parser.parse_raw_text(STUDENT_TIMELINE)
        for evt in events:
            assert isinstance(evt, TimelineEvent)
        years = [(e.year, e.month or 0) for e in events]
        assert years == sorted(years)


class TestGarbledInput:
    """Test that garbled/nonsensical input is handled gracefully."""

    def test_garbled_does_not_crash(self, parser: TimelineParser) -> None:
        """Parser should either return few events or raise ValueError, never crash."""
        try:
            events = parser.parse_raw_text(GARBLED_INPUT)
            # If it returns, events should be a list (possibly empty-ish)
            assert isinstance(events, list)
        except ValueError:
            # ValueError is an acceptable graceful failure
            pass
        except Exception as exc:
            pytest.fail(
                f"Parser should raise ValueError or return a list, "
                f"but raised {type(exc).__name__}: {exc}"
            )
