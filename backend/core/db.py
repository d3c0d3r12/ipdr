"""
Sync MongoDB connection using PyMongo
Replaces the previous SQLAlchemy sync engine
"""
import os
import logging
from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ipdr_tracking")

# Lazy-init to avoid blocking DNS SRV resolution at import time
_client: MongoClient | None = None
sync_db: Database | None = None


def _ensure_client():
    global _client, sync_db
    if _client is None:
        _client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
        sync_db = _client[MONGODB_DB_NAME]


def get_db() -> Database:
    """FastAPI dependency that provides a sync PyMongo database handle."""
    _ensure_client()
    return sync_db


def test_connection() -> bool:
    """Test MongoDB connection."""
    try:
        _ensure_client()
        info = _client.server_info()
        logger.info(f"✅ Connected to MongoDB {info.get('version', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
