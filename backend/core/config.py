import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# ENVIRONMENT VALIDATION
# ============================================
def validate_required_env():
    """Validate all required environment variables are set"""
    required_vars = [
        ("JWT_SECRET", "JWT secret key for token signing"),
    ]
    
    missing = []
    for var_name, description in required_vars:
        if not os.getenv(var_name):
            missing.append(f"  - {var_name}: {description}")
    
    if missing:
        error_msg = "❌ Missing required environment variables:\n" + "\n".join(missing)
        print(error_msg)
        raise RuntimeError(error_msg)

# Call validation on module load
validate_required_env()

# ============================================
# MONGODB CONFIGURATION
# ============================================
MONGODB_URL = os.getenv("MONGODB_URL", os.getenv("DATABASE_URL", "mongodb://localhost:27017"))
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ipdr_tracking")

# ============================================
# JWT CONFIGURATION
# ============================================
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "CHANGE_ME_IN_PRODUCTION":
    raise ValueError("❌ JWT_SECRET must be set to a secure random value in environment")

JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", JWT_SECRET)  # Use same as JWT_SECRET if not provided
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ============================================
# APPLICATION SETTINGS
# ============================================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "52428800"))  # 50MB default

# Directory settings
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
PROCESSED_DIR = os.getenv("PROCESSED_DIR", str(BASE_DIR / "processed"))
MASTER_DIR = os.getenv("MASTER_DIR", str(BASE_DIR / "master"))

# Create directories if they don't exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
Path(MASTER_DIR).mkdir(parents=True, exist_ok=True)

# ============================================
# EXTERNAL SERVICES
# ============================================
INFOBYIP_URL = os.getenv("INFOBYIP_URL", "https://www.infobyip.com/ipbulklookup.php")

# ============================================
# SECURITY SETTINGS
# ============================================
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "900"))  # 15 minutes
RATE_LIMIT_LOGIN = int(os.getenv("RATE_LIMIT_LOGIN", "5"))
RATE_LIMIT_UPLOAD = int(os.getenv("RATE_LIMIT_UPLOAD", "10"))
RATE_LIMIT_API = int(os.getenv("RATE_LIMIT_API", "30"))

# ============================================
# LOGGING
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", str(BASE_DIR / "logs"))
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"



