"""
Simulation routes — runs Monte Carlo engine and returns results.

POST /simulate        → run full simulation for a user
GET  /simulate/{user_id} → retrieve saved simulation result
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.database import get_database
from app.models.timeline import SimulationResult, TimelineInput
from app.services.simulator import ChaosSimulator
from app.utils.logger import logger

router = APIRouter()


class SimulateRequest(BaseModel):
    user_id: str


@router.post("", response_model=SimulationResult)
async def run_simulation(
    body: SimulateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Run the full Monte Carlo simulation for a user.

    Requires a saved timeline (from POST /timeline/submit).
    Saves the result to MongoDB and returns it.
    """
    # Fetch the user's timeline
    doc = await db["timelines"].find_one({"_id": body.user_id})
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No timeline found for user_id={body.user_id}. "
            f"Submit a timeline first via POST /timeline/submit.",
        )

    doc.pop("_id", None)
    try:
        timeline = TimelineInput(**doc)
    except Exception as exc:
        logger.error(f"Failed to parse stored timeline: {exc}")
        raise HTTPException(status_code=500, detail="Stored timeline data is corrupted.")

    if not timeline.events or len(timeline.events) == 0:
        raise HTTPException(
            status_code=422,
            detail="Timeline has no events. Add events before simulating.",
        )

    # Run simulation
    try:
        simulator = ChaosSimulator()
        result = simulator.run_full_simulation(
            user_id=body.user_id,
            events=timeline.events,
            current_level=timeline.current_level.value,
            n_simulations=1000,
        )
    except Exception as exc:
        logger.error(f"Simulation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Simulation engine encountered an error. Please try again.",
        )

    # Save result to MongoDB
    try:
        result_doc = result.model_dump(mode="json")
        result_doc["_id"] = body.user_id
        await db["simulations"].replace_one(
            {"_id": body.user_id}, result_doc, upsert=True
        )
    except Exception as exc:
        logger.error(f"Failed to save simulation result: {exc}")
        # Still return the result even if save fails
        logger.warning("Returning result without persisting to DB")

    return result


@router.get("/{user_id}", response_model=SimulationResult)
async def get_simulation(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retrieve a previously saved simulation result."""
    doc = await db["simulations"].find_one({"_id": user_id})

    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No simulation result found for user_id={user_id}. "
            f"Run a simulation first via POST /simulate.",
        )

    doc.pop("_id", None)
    return SimulationResult(**doc)
