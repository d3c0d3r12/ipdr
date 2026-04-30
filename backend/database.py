"""
Async MongoDB connection using Motor
Replaces the previous SQLAlchemy async engine
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGODB_URL = os.getenv("MONGODB_URL", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ipdr_tracking")

# Lazy-init to avoid blocking DNS SRV resolution at import time
client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


def _ensure_client():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        db = client[MONGODB_DB_NAME]


async def get_session() -> AsyncIOMotorDatabase:
    """Dependency that provides the async Motor database handle."""
    _ensure_client()
    return db


async def close_client():
    """Close the Motor client (call on app shutdown)."""
    if client is not None:
        client.close()
