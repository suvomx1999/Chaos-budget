"""
Logging configuration for Chaos Budget backend.

Uses loguru for structured, colorful console output and rotating file logs.
Import `logger` from this module everywhere instead of using stdlib logging.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

# Remove the default loguru handler so we can configure our own
logger.remove()

# ── Determine log level from environment ──────────────────────────────
# We read ENVIRONMENT directly here to avoid circular imports with config.py
_env = "development"
try:
    import os
    _env = os.getenv("ENVIRONMENT", "development").lower()
except Exception:
    pass

_log_level = "DEBUG" if _env != "production" else "INFO"

# ── Console handler (colorful, human-readable) ───────────────────────
logger.add(
    sys.stderr,
    level=_log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
    colorize=True,
    backtrace=True,
    diagnose=(_env != "production"),
)

# ── File handler (rotating, machine-parseable) ───────────────────────
_log_dir = Path("logs")
_log_dir.mkdir(exist_ok=True)

logger.add(
    _log_dir / "app.log",
    level=_log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
    rotation="10 MB",
    retention="7 days",
    compression="gz",
    enqueue=True,  # Thread-safe async writing
)

# Re-export so other modules do: from app.utils.logger import logger
__all__ = ["logger"]
