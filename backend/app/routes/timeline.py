"""
Timeline routes — text parsing, PDF upload, timeline submission, and retrieval.

POST /timeline/parse-text  → parse raw text into structured events
POST /timeline/parse-pdf   → upload a PDF resume and extract events
POST /timeline/submit      → save a full TimelineInput to MongoDB
GET  /timeline/{user_id}   → retrieve a saved timeline
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.database import get_database
from app.models.timeline import TimelineEvent, TimelineInput
from app.services.parser import TimelineParser
from app.utils.logger import logger

router = APIRouter()

# ── Lazy singleton for the parser (created on first use) ──────────────
_parser: TimelineParser | None = None


def _get_parser() -> TimelineParser:
    """Return a cached TimelineParser instance."""
    global _parser
    if _parser is None:
        _parser = TimelineParser()
    return _parser


# ── Request / response schemas ────────────────────────────────────────

class ParseTextRequest(BaseModel):
    raw_text: str


class ParseTextResponse(BaseModel):
    events: list[TimelineEvent]
    event_count: int


class SubmitResponse(BaseModel):
    user_id: str
    event_count: int
    status: str


# ── Routes ────────────────────────────────────────────────────────────

@router.post("/parse-text", response_model=ParseTextResponse)
async def parse_text(body: ParseTextRequest):
    """
    Accept raw resume/LinkedIn/career text and return extracted
    TimelineEvent objects using the Groq-powered parser.
    """
    if not body.raw_text.strip():
        raise HTTPException(status_code=422, detail="raw_text must not be empty.")

    parser = _get_parser()

    try:
        events = parser.parse_raw_text(body.raw_text)
    except ValueError as exc:
        logger.error(f"Text parsing failed: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error during text parsing: {exc}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while parsing your text. Please try again.",
        )

    return ParseTextResponse(events=events, event_count=len(events))


@router.post("/parse-pdf", response_model=ParseTextResponse)
async def parse_pdf(file: UploadFile = File(...)):
    """
    Accept a PDF resume upload, extract text, and return structured
    TimelineEvent objects. Max file size: 10 MB.
    """
    # Validate content type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=422,
            detail=f"Expected a PDF file, got content_type={file.content_type}",
        )

    # Read bytes with size limit (10 MB)
    MAX_PDF_SIZE = 10 * 1024 * 1024
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=422,
            detail="PDF file is too large. Maximum size is 10 MB.",
        )
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    parser = _get_parser()

    try:
        events = parser.parse_pdf(pdf_bytes)
    except ValueError as exc:
        logger.error(f"PDF parsing failed: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error during PDF parsing: {exc}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while parsing your PDF. Please try again.",
        )

    return ParseTextResponse(events=events, event_count=len(events))


@router.post("/submit", response_model=SubmitResponse)
async def submit_timeline(
    body: TimelineInput,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Save a complete TimelineInput (from form or post-parse review) to MongoDB.
    Returns the user_id and event count.
    """
    event_count = len(body.events) if body.events else 0
    logger.info(
        f"Saving timeline for user_id={body.user_id}, "
        f"events={event_count}, role={body.current_role}"
    )

    try:
        doc = body.model_dump(mode="json")
        # Use user_id as the document _id for easy lookup
        doc["_id"] = body.user_id

        # Upsert — allow resubmission with same user_id
        await db["timelines"].replace_one(
            {"_id": body.user_id}, doc, upsert=True
        )
    except Exception as exc:
        logger.error(f"Failed to save timeline: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save your timeline. Please try again.",
        )

    return SubmitResponse(
        user_id=body.user_id,
        event_count=event_count,
        status="saved",
    )


@router.get("/{user_id}", response_model=TimelineInput)
async def get_timeline(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Retrieve a previously saved timeline by user_id."""
    doc = await db["timelines"].find_one({"_id": user_id})

    if doc is None:
        raise HTTPException(
            status_code=404, detail=f"No timeline found for user_id={user_id}"
        )

    # Remove Mongo _id before returning as Pydantic model
    doc.pop("_id", None)
    return TimelineInput(**doc)
