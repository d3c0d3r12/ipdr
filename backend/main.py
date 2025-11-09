from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, process, data, auth, tracking, ip_lookup, auth_secure, fir_management, cookie_manager, files
from core.config import ALLOWED_ORIGINS, ENVIRONMENT
from core.db import test_connection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IPDR Tracking Hub",
    description="IP Data Record Intelligence & Case Management System for Delhi Police Cyber Cell",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_secure.router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(fir_management.router, prefix="/api/fir", tags=["📁 FIR Management"])
app.include_router(upload.router, prefix="/api/upload", tags=["📤 Upload"])
app.include_router(process.router, prefix="/api/process", tags=["⚙️ Process"])
app.include_router(data.router, prefix="/api/data", tags=["📊 Data"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["👤 User Tracking"])
app.include_router(ip_lookup.router, prefix="/api", tags=["🔍 IP Lookup"])
app.include_router(cookie_manager.router, prefix="/api/cookies", tags=["🍪 Cookie Management"])
app.include_router(files.router, prefix="/api", tags=["📁 Secure File Serving"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Starting IPDR Tracking Hub...")
    logger.info(f"📍 Environment: {ENVIRONMENT}")
    
    # Test database connection
    if test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed - check your Neon configuration")
    
    # Cookie service disabled - using Selenium bypass instead
    logger.info("ℹ️ Using Selenium bypass for IP lookups (localhost mode)")
    logger.info("ℹ️ Cookie refresh service disabled (not needed with Selenium)")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 Shutting down IPDR Tracking Hub...")
    logger.info("✅ Shutdown complete")

@app.get("/", tags=["Root"])
def root():
    """Health check endpoint"""
    return {
        "status": "IPDR Tracking Hub API is running",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/health", tags=["Root"])
def health():
    """Detailed health check"""
    db_status = test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "environment": ENVIRONMENT
    }
