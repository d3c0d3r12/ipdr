from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from core.config import DATABASE_URL, ENVIRONMENT
import logging

logger = logging.getLogger(__name__)

# Create metadata
metadata = MetaData()

# Create engine with Neon-optimized settings
engine = create_engine(
    DATABASE_URL,
    # Connection pool settings (optimized for Neon)
    pool_size=5,                    # Neon handles pooling well
    max_overflow=10,                # Allow some overflow
    pool_timeout=30,                # 30 second timeout
    pool_recycle=3600,              # Recycle connections after 1 hour
    pool_pre_ping=True,             # Verify connections before use
    
    # Connection arguments
    connect_args={
        "sslmode": "require",       # SSL required for Neon
        "connect_timeout": 10,      # 10 second connection timeout
        "application_name": "police-intel-backend",
        "options": "-c timezone=Asia/Kolkata"  # Set timezone
    },
    
    # Echo SQL queries in development
    echo=(ENVIRONMENT == "development")
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base(metadata=metadata)

# Dependency for FastAPI
def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection function
def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connected to Neon PostgreSQL: {version[:80]}...")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

# Initialize connection on import (optional)
if __name__ == "__main__":
    test_connection()
