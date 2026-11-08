"""
Explanation routes — generates and retrieves Groq-powered narrative explanations.

POST /explain        → generate explanation for a user's simulation result
GET  /explain/{user_id} → retrieve saved explanation
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.database import get_database
from app.models.timeline import SimulationResult, TimelineInput
from app.services.explainer import NarrativeExplainer
from app.utils.logger import logger

router = APIRouter()


class ExplainRequest(BaseModel):
    user_id: str


class ExplanationResponse(BaseModel):
    user_id: str
    chaos_story: str
    what_skill_built: str
    what_luck_shaped: str
    alternate_you: str
    surgery_suggestion: str


@router.post("", response_model=ExplanationResponse)
async def generate_explanation(
    body: ExplainRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Generate a narrative explanation of the user's Chaos Budget results.

    Requires both a saved timeline and a simulation result.
    """
    # Fetch timeline
    timeline_doc = await db["timelines"].find_one({"_id": body.user_id})
    if timeline_doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No timeline found for user_id={body.user_id}.",
        )

    # Fetch simulation result
    sim_doc = await db["simulations"].find_one({"_id": body.user_id})
    if sim_doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No simulation result found for user_id={body.user_id}. "
            f"Run a simulation first via POST /simulate.",
        )

    timeline_doc.pop("_id", None)
    sim_doc.pop("_id", None)

    try:
        timeline = TimelineInput(**timeline_doc)
        sim_result = SimulationResult(**sim_doc)
    except Exception as exc:
        logger.error(f"Failed to parse stored data: {exc}")
        raise HTTPException(status_code=500, detail="Stored data is corrupted.")

    if not timeline.events:
        raise HTTPException(status_code=422, detail="Timeline has no events.")

    # Generate explanation
    explainer = NarrativeExplainer()

    try:
        explanation = explainer.generate_explanation(timeline.events, sim_result)
    except ValueError as exc:
        logger.error(f"Explanation generation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate explanation. Please try again.",
        )

    # Generate surgery suggestion (never fails — has fallback)
    surgery = explainer.generate_surgery_suggestion(timeline.events, sim_result)

    # Build response
    response = ExplanationResponse(
        user_id=body.user_id,
        chaos_story=explanation["chaos_story"],
        what_skill_built=explanation["what_skill_built"],
        what_luck_shaped=explanation["what_luck_shaped"],
        alternate_you=explanation["alternate_you"],
        surgery_suggestion=surgery,
    )

    # Save to MongoDB
    try:
        doc = response.model_dump(mode="json")
        doc["_id"] = body.user_id
        await db["explanations"].replace_one(
            {"_id": body.user_id}, doc, upsert=True
        )
    except Exception as exc:
        logger.error(f"Failed to save explanation: {exc}")
        # Still return — don't block the response

    return response


@router.get("/{user_id}", response_model=ExplanationResponse)
async def get_explanation(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retrieve a previously saved explanation."""
    doc = await db["explanations"].find_one({"_id": user_id})

    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"No explanation found for user_id={user_id}. "
            f"Generate one first via POST /explain.",
        )

    doc.pop("_id", None)
    return ExplanationResponse(**doc)
