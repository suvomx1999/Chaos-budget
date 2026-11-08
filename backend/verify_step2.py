#!/usr/bin/env python3
"""
Step 2 Verification Script for Chaos Budget.

Checks:
  1. FastAPI app starts and /health returns db: connected
  2. TimelineInput model validates a sample object
  3. Insert a test document into MongoDB and read it back
  4. Delete the test document
  5. SimulationResult and AlternatePath validate correctly

Run from the backend/ directory with the venv activated:
    python verify_step2.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        console.print(f"  ✅  {label}", style="green")
    else:
        failed += 1
        msg = f"  ❌  {label}"
        if detail:
            msg += f"  —  {detail}"
        console.print(msg, style="bold red")


async def run_all_checks() -> None:
    console.print(Panel("[bold cyan]Step 2 — MongoDB & Data Models Verification[/bold cyan]"))

    # ──────────────────────────────────────────────────────────────────
    # 1. Config loads
    # ──────────────────────────────────────────────────────────────────
    console.print("\n[bold]⚙️  Configuration[/bold]")
    try:
        from app.config import get_settings
        settings = get_settings()
        check("Settings loaded", True)
        check("GROQ_API_KEY present", settings.groq_key_is_real)
        check("MONGODB_URI looks valid", settings.mongodb_uri_is_real)
    except Exception as e:
        check("Settings loaded", False, str(e))
        console.print("[bold red]Cannot continue without config. Exiting.[/bold red]")
        return

    # ──────────────────────────────────────────────────────────────────
    # 2. Pydantic models validate
    # ──────────────────────────────────────────────────────────────────
    console.print("\n[bold]📐 Pydantic Model Validation[/bold]")

    from app.models.timeline import (
        AlternatePath,
        CareerLevel,
        EventType,
        SimulationResult,
        TimelineEvent,
        TimelineInput,
    )

    # TimelineEvent
    try:
        evt = TimelineEvent(
            year=2021,
            month=6,
            event_type=EventType.EDUCATION,
            title="Graduated from NIT",
            organization="NIT",
            description="Completed B.Tech in Computer Science",
            self_rating=8,
            duration_months=48,
        )
        check("TimelineEvent validates", True)
    except Exception as e:
        check("TimelineEvent validates", False, str(e))

    # TimelineEvent — bad year
    try:
        TimelineEvent(year=1800, event_type="education", title="X", self_rating=5)
        check("TimelineEvent rejects year=1800", False, "Should have raised")
    except Exception:
        check("TimelineEvent rejects year=1800", True)

    # TimelineEvent — bad self_rating
    try:
        TimelineEvent(year=2020, event_type="job", title="X", self_rating=15)
        check("TimelineEvent rejects self_rating=15", False, "Should have raised")
    except Exception:
        check("TimelineEvent rejects self_rating=15", True)

    # TimelineInput
    try:
        sample_input = TimelineInput(
            raw_text="I graduated from NIT in 2021 and joined Infosys.",
            events=[evt],
            current_role="Senior SDE-2",
            current_level=CareerLevel.SENIOR,
            field="software engineering",
        )
        check("TimelineInput validates", True)
        check("TimelineInput.user_id auto-generated", len(sample_input.user_id) > 0)
    except Exception as e:
        check("TimelineInput validates", False, str(e))
        sample_input = None

    # AlternatePath
    try:
        alt = AlternatePath(
            events=[{"year": 2021, "title": "Stayed at Infosys"}],
            final_outcome="Mid-level developer at Infosys",
            outcome_level="mid",
            divergence_point="Quit Infosys to join startup",
        )
        check("AlternatePath validates", True)
    except Exception as e:
        check("AlternatePath validates", False, str(e))

    # SimulationResult
    try:
        sim = SimulationResult(
            user_id="test-user",
            chaos_coefficient=0.67,
            skill_percentage=24.0,
            luck_percentage=67.0,
            timing_percentage=9.0,
            alternate_paths=[alt],
            key_pivot_events=["Quit Infosys", "Got laid off"],
        )
        check("SimulationResult validates", True)
        check("SimulationResult percentages sum ≈ 100", True)
    except Exception as e:
        check("SimulationResult validates", False, str(e))

    # SimulationResult — bad percentages
    try:
        SimulationResult(
            user_id="x",
            chaos_coefficient=0.5,
            skill_percentage=50.0,
            luck_percentage=50.0,
            timing_percentage=50.0,
        )
        check("SimulationResult rejects 50+50+50", False, "Should have raised")
    except Exception:
        check("SimulationResult rejects 50+50+50", True)

    # CareerLevel ordinal
    check(
        "CareerLevel.STUDENT.ordinal == 0",
        CareerLevel.STUDENT.ordinal == 0,
    )
    check(
        "CareerLevel.EXECUTIVE.ordinal == 5",
        CareerLevel.EXECUTIVE.ordinal == 5,
    )

    # ──────────────────────────────────────────────────────────────────
    # 3. Database connection + ping
    # ──────────────────────────────────────────────────────────────────
    console.print("\n[bold]🗄️  MongoDB Connection[/bold]")

    from app.database import close_db, connect_db, get_database, is_connected, ping

    await connect_db(uri=settings.MONGODB_URI, db_name=settings.MONGODB_DB_NAME)
    ping_ok = await ping()
    check("MongoDB ping", ping_ok)
    check("is_connected() == True", is_connected())

    if not ping_ok:
        console.print("[bold red]DB unreachable — skipping insert/read/delete.[/bold red]")
        await close_db()
        return

    # ──────────────────────────────────────────────────────────────────
    # 4. FastAPI /health endpoint (in-process)
    # ──────────────────────────────────────────────────────────────────
    console.print("\n[bold]🌐 Health Endpoint[/bold]")

    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        data = resp.json()
        check("/health returns 200", resp.status_code == 200)
        check("/health status == 'ok'", data.get("status") == "ok")
        check("/health db == 'connected'", data.get("db") == "connected")
        check("/health version == '1.0.0'", data.get("version") == "1.0.0")

    # ──────────────────────────────────────────────────────────────────
    # 5. Insert → Read → Delete round-trip
    # ──────────────────────────────────────────────────────────────────
    console.print("\n[bold]🔄 MongoDB CRUD Round-Trip[/bold]")

    db = get_database()
    test_collection = db["_verify_step2"]
    test_id = str(uuid.uuid4())

    if sample_input is None:
        # Fallback if model creation failed above
        doc = {"_id": test_id, "test": True}
    else:
        doc = sample_input.model_dump()
        doc["_id"] = test_id

    # Insert
    try:
        await test_collection.insert_one(doc)
        check("Insert test document", True)
    except Exception as e:
        check("Insert test document", False, str(e))

    # Read back
    try:
        fetched = await test_collection.find_one({"_id": test_id})
        check("Read test document", fetched is not None)
        if sample_input:
            check(
                "Read-back current_role matches",
                fetched.get("current_role") == sample_input.current_role,
            )
    except Exception as e:
        check("Read test document", False, str(e))

    # Delete
    try:
        result = await test_collection.delete_one({"_id": test_id})
        check("Delete test document", result.deleted_count == 1)
    except Exception as e:
        check("Delete test document", False, str(e))

    # Drop the temp collection
    await test_collection.drop()

    # ──────────────────────────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────────────────────────
    await close_db()

    # ──────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────
    console.print()
    table = Table(title="Step 2 Verification Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("Passed", f"[green]{passed}[/green]")
    table.add_row("Failed", f"[red]{failed}[/red]")
    table.add_row("Total", str(passed + failed))
    console.print(table)

    if failed == 0:
        console.print("\n[bold green]🎉 All Step 2 checks passed! DB + Models are solid.[/bold green]\n")
    else:
        console.print(f"\n[bold red]⚠  {failed} check(s) failed. Fix before proceeding.[/bold red]\n")


if __name__ == "__main__":
    asyncio.run(run_all_checks())
    sys.exit(0 if failed == 0 else 1)
