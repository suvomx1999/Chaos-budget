"""
Async MongoDB connection layer using Motor.

Provides lifecycle functions (connect/close), a FastAPI dependency
(get_database), and a ping() health-check. All connection errors are
handled gracefully with clear log messages.
"""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.utils.logger import logger

# ── Module-level state ────────────────────────────────────────────────
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None
_is_connected: bool = False


async def connect_db(uri: str, db_name: str) -> None:
    """
    Initialise the Motor client and select the database.

    Args:
        uri: MongoDB connection string (Atlas SRV or localhost).
        db_name: Name of the database to use.

    Raises:
        Nothing — errors are logged and _is_connected stays False.
    """
    global _client, _database, _is_connected

    try:
        logger.info("Connecting to MongoDB…")
        _client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,  # fail fast on bad URI
            connectTimeoutMS=5000,
            maxPoolSize=10,
        )
        _database = _client[db_name]
        _is_connected = True
        logger.info(f"MongoDB client initialised — database: {db_name}")
    except Exception as exc:
        _is_connected = False
        logger.error(f"Failed to initialise MongoDB client: {exc}")


async def close_db() -> None:
    """Gracefully close the Motor client."""
    global _client, _database, _is_connected

    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed.")
    _client = None
    _database = None
    _is_connected = False


async def ping() -> bool:
    """
    Send a ping command to verify the server is reachable.

    Returns:
        True if the server responded, False otherwise.
    """
    global _is_connected

    if _client is None:
        logger.warning("ping() called but no MongoDB client exists.")
        _is_connected = False
        return False

    try:
        await _client.admin.command("ping")
        _is_connected = True
        logger.info("MongoDB ping succeeded ✓")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        _is_connected = False
        logger.error(f"MongoDB ping failed: {exc}")
        return False
    except Exception as exc:
        _is_connected = False
        logger.error(f"MongoDB ping unexpected error: {exc}")
        return False


def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency — returns the active database handle.

    Usage in a route:
        @router.get("/items")
        async def list_items(db=Depends(get_database)):
            ...

    Raises:
        RuntimeError: if called before connect_db().
    """
    if _database is None:
        raise RuntimeError(
            "Database not initialised. Ensure connect_db() was called at startup."
        )
    return _database


def is_connected() -> bool:
    """Return the current connection status (set by ping / connect)."""
    return _is_connected
