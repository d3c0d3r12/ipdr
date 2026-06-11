from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from routers import upload, process, ipdr_processing, data, auth, tracking, ip_lookup, auth_secure, fir_management, cookie_manager, files, multi_file_processor, letter_templates
from core.config import ALLOWED_ORIGINS, ENVIRONMENT
from core.db import test_connection
from database import close_client
import logging
import uuid

# Optional imports with fallback
try:
    from routers import cloud_storage
except Exception as e:
    logging.warning(f"Cloud storage module not available: {e}")
try:
    from routers import auto_steps_6_7
except Exception as e:
    logging.warning(f"Auto steps 6-7 module not available: {e}")

# Configure logging - Only show WARNING and above for cleaner logs
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Keep our app logger at INFO for important messages
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
    allow_origin_regex=r"^https?://((localhost|127\.0\.0\.1)(:\d+)?|(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
	request_id = str(uuid.uuid4())
	logger.warning(f"HTTPException {exc.status_code} {request.url.path} request_id={request_id} detail={exc.detail}")
	return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail, "request_id": request_id})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	request_id = str(uuid.uuid4())
	logger.warning(f"ValidationError {request.url.path} request_id={request_id}")
	return JSONResponse(status_code=422, content={"success": False, "error": "Validation error", "request_id": request_id})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
	request_id = str(uuid.uuid4())
	logger.exception(f"UnhandledError {request.url.path} request_id={request_id}")
	return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error", "request_id": request_id})

# Include routers
app.include_router(auth_secure.router, prefix="/api/auth", tags=["🔐 Authentication"])
app.include_router(fir_management.router, prefix="/api/fir", tags=["📁 FIR Management"])
app.include_router(letter_templates.router, prefix="/api/letter-templates", tags=["📝 Letter Templates"])
try:
    app.include_router(cloud_storage.router, prefix="/api/cloud", tags=["☁️ Cloud Storage"])
except NameError:
    logging.warning("Cloud Storage router not available")
app.include_router(multi_file_processor.router, prefix="/api/multi-file", tags=["📁 Multi-File Processor"])
try:
    app.include_router(auto_steps_6_7.router, prefix="/api/auto", tags=["🤖 Auto Steps 6-7"])
except NameError:
    logging.warning("Auto Steps 6-7 router not available")
app.include_router(upload.router, prefix="/api/upload", tags=["📤 Upload"])
app.include_router(process.router, prefix="/api/process", tags=["⚙️ Process"])
app.include_router(ipdr_processing.router, prefix="/api/process", tags=["🧾 IPDR"])
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
    
    # Test sync database connection
    if test_connection():
        logger.info("✅ MongoDB sync connection successful")
    else:
        logger.error("❌ MongoDB sync connection failed - check your configuration")
    
    # Test async database connection
    try:
        from database import get_session as _get_async_db
        async_db = await _get_async_db()
        await async_db.command("ping")
        logger.info("✅ MongoDB async connection successful")
    except Exception as e:
        logger.error(f"❌ MongoDB async connection failed: {e}")
    
    # Create indexes for all collections
    try:
        from database import get_session as _get_async_db2
        async_db = await _get_async_db2()
        from models.user_auth import INDEXES as USER_INDEXES
        from models.fir_case import INDEXES as FIR_INDEXES
        from models.investigation import INDEXES as INV_INDEXES
        from models.ip_record import INDEXES as IP_INDEXES
        
        for collection_name, index_list in {**USER_INDEXES, **FIR_INDEXES, **INV_INDEXES, **IP_INDEXES}.items():
            for index_spec in index_list:
                try:
                    if isinstance(index_spec, tuple):
                        await async_db[collection_name].create_index([index_spec])
                    elif isinstance(index_spec, list):
                        await async_db[collection_name].create_index(index_spec)
                except Exception:
                    pass  # Index may already exist
        logger.info("✅ MongoDB indexes ready")
    except Exception as e:
        logger.warning(f"⚠️ Index creation skipped: {e}")
    
    logger.info("ℹ️ Using Selenium bypass for IP lookups (localhost mode)")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 Shutting down IPDR Tracking Hub...")
    await close_client()
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
