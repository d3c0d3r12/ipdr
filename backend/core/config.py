import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# NEON DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://username:password@ep-xxx-xxx.ap-south-1.aws.neon.tech/police_data?sslmode=require"
)

# Alternative: Parse from individual variables
DB_HOST = os.getenv("DB_HOST", "ep-xxx-xxx.ap-south-1.aws.neon.tech")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "police_data")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "require")

# Construct DATABASE_URL if not provided
if not DATABASE_URL or DATABASE_URL.startswith("postgresql://username"):
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSL_MODE}"

# ============================================
# JWT CONFIGURATION
# ============================================
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "CHANGE_ME_IN_PRODUCTION")
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
DEBUG = os.getenv("DEBUG", "true").lower() == "true"



