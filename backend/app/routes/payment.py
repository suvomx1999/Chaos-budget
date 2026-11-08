"""
Payment routes — Stripe Checkout integration.

POST /payment/create-session  → create a Stripe Checkout session
GET  /payment/status/{user_id} → check if user has paid
POST /payment/webhook          → Stripe webhook (optional, for production)
"""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_database
from app.utils.logger import logger

router = APIRouter()


class CreateSessionRequest(BaseModel):
    user_id: str
    success_url: str  # frontend URL to redirect after payment
    cancel_url: str   # frontend URL if user cancels


class CreateSessionResponse(BaseModel):
    session_id: str
    checkout_url: str


class PaymentStatus(BaseModel):
    user_id: str
    paid: bool
    session_id: str | None = None


@router.post("/create-session", response_model=CreateSessionResponse)
async def create_checkout_session(
    body: CreateSessionRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a Stripe Checkout session for unlocking full analysis results.
    Returns the session ID and checkout URL.
    """
    settings = get_settings()

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Check if already paid
    existing = await db["payments"].find_one({"_id": body.user_id, "paid": True})
    if existing:
        return CreateSessionResponse(
            session_id=existing.get("session_id", ""),
            checkout_url="",  # already paid, no need to redirect
        )

    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "product_data": {
                            "name": "Chaos Budget — Full Analysis",
                            "description": "Unlock AI narrative, alternate paths, and chaos surgery suggestion",
                        },
                        "unit_amount": settings.STRIPE_PRICE_AMOUNT * 100,  # Stripe expects paise/cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{body.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=body.cancel_url,
            metadata={"user_id": body.user_id},
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=502, detail="Payment service unavailable.")

    # Save pending payment record
    await db["payments"].replace_one(
        {"_id": body.user_id},
        {
            "_id": body.user_id,
            "session_id": session.id,
            "paid": False,
        },
        upsert=True,
    )

    return CreateSessionResponse(
        session_id=session.id,
        checkout_url=session.url or "",
    )


@router.get("/status/{user_id}", response_model=PaymentStatus)
async def get_payment_status(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Check if a user has completed payment.
    If there's a pending session, verify it with Stripe.
    """
    settings = get_settings()
    doc = await db["payments"].find_one({"_id": user_id})

    if doc and doc.get("paid"):
        return PaymentStatus(user_id=user_id, paid=True, session_id=doc.get("session_id"))

    # No record or not yet paid — check Stripe if we have a session
    if doc and doc.get("session_id") and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(doc["session_id"])
            if session.payment_status == "paid":
                await db["payments"].update_one(
                    {"_id": user_id},
                    {"$set": {"paid": True}},
                )
                return PaymentStatus(
                    user_id=user_id, paid=True, session_id=doc["session_id"]
                )
        except stripe.StripeError as e:
            logger.warning(f"Stripe verify failed for {user_id}: {e}")

    return PaymentStatus(user_id=user_id, paid=False)


@router.post("/verify-session")
async def verify_session(
    body: dict,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Verify a Stripe Checkout session after redirect.
    Called by the frontend with the session_id from the URL.
    """
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    settings = get_settings()
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.StripeError as e:
        logger.error(f"Stripe session retrieve failed: {e}")
        raise HTTPException(status_code=502, detail="Could not verify payment.")

    user_id = session.metadata.get("user_id", "")
    paid = session.payment_status == "paid"

    if paid and user_id:
        await db["payments"].replace_one(
            {"_id": user_id},
            {"_id": user_id, "session_id": session_id, "paid": True},
            upsert=True,
        )

    return {"user_id": user_id, "paid": paid, "session_id": session_id}
