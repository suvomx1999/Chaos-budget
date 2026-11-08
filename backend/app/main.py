"""
Chaos Budget — FastAPI application entry point.

Configures lifecycle events (DB connect/disconnect), CORS middleware,
global exception handling, request logging, route mounting, and the
health-check endpoint.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import close_db, connect_db, is_connected, ping
from app.routes import explain, payment, simulate, timeline
from app.utils.logger import logger


# ── Lifecycle ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the application."""
    settings = get_settings()
    logger.info(f"Starting Chaos Budget API (env={settings.ENVIRONMENT})")

    # Startup: connect to MongoDB and verify with a ping
    await connect_db(uri=settings.MONGODB_URI, db_name=settings.MONGODB_DB_NAME)
    await ping()

    yield  # ← app is running

    # Shutdown: close the database connection
    await close_db()
    logger.info("Chaos Budget API shut down.")


# ── App factory ───────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title="Chaos Budget API",
    description=(
        "Counterfactual Monte Carlo career simulation engine. "
        "Computes how much of your career trajectory is skill vs. luck vs. timing."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)


# ── Global exception handler ─────────────────────────────────────────
# Catches any unhandled exception so 500 responses never leak stack traces.

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return a safe 500 response; log the real traceback server-side only."""
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later."
        },
    )


# ── Request logging middleware ────────────────────────────────────────
# Logs method, path, status code, and duration for every request.

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({elapsed_ms:.0f}ms)"
    )
    return response


# ── CORS ──────────────────────────────────────────────────────────────
# In production, restrict to explicit origins; in dev, allow all methods/headers.

_cors_origins = settings.cors_origin_list
_cors_methods = ["GET", "POST", "OPTIONS"] if settings.is_production else ["*"]
_cors_headers = ["Content-Type", "Authorization"] if settings.is_production else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=_cors_methods,
    allow_headers=_cors_headers,
)

# ── Routers ───────────────────────────────────────────────────────────

app.include_router(timeline.router, prefix="/timeline", tags=["Timeline"])
app.include_router(simulate.router, prefix="/simulate", tags=["Simulate"])
app.include_router(explain.router, prefix="/explain", tags=["Explain"])
app.include_router(payment.router, prefix="/payment", tags=["Payment"])


# ── Health check ──────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """
    Returns service status and database connectivity.
    Used by deployment platforms for readiness probes.
    """
    db_status = "connected" if is_connected() else "disconnected"
    return {
        "status": "ok",
        "db": db_status,
        "version": "1.0.0",
    }
