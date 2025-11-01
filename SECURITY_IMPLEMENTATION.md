# 🔐 Security Implementation Guide
## Police Intelligence System - VAPT & Cyber Security Hardening

---

## 📋 Table of Contents

1. [Security Objectives & Principles](#1-security-objectives--principles)
2. [Preventive Controls](#2-preventive-controls)
3. [Runtime Protections](#3-runtime-protections)
4. [Secure SDLC & CI/CD](#4-secure-sdlc--cicd)
5. [VAPT Plan](#5-vapt-plan)
6. [Incident Response](#6-incident-response)
7. [Implementation Checklist](#7-implementation-checklist)

---

## 1. Security Objectives & Principles

### Core Principles

✅ **Confidentiality** - Sensitive logs, IPs, timestamps, PII protected (at-rest & in-transit)  
✅ **Integrity** - No silent modification of evidence; full audit trail  
✅ **Availability** - System available to authorized officers; DoS protection  
✅ **Least Privilege** - Components get only what they need  
✅ **Defense in Depth** - Multiple overlapping controls  

### Compliance Requirements

- Evidence chain-of-custody preservation
- Audit logging for all critical operations
- Data retention policies
- Access control and authentication
- Encryption at rest and in transit

---

## 2. Preventive Controls (Implement Immediately)

### A. Network & TLS Configuration

#### Nginx TLS 1.3 Configuration

Create: `/etc/nginx/conf.d/police-intel-ssl.conf`

```nginx
# TLS 1.3 Only with Strong Ciphers
ssl_protocols TLSv1.3;
ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256;
ssl_prefer_server_ciphers on;

# HSTS (HTTP Strict Transport Security)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';" always;

# SSL Session Settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Rate Limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=upload:10m rate=10r/m;

server {
    listen 443 ssl http2;
    server_name police-intel.local;
    
    ssl_certificate /etc/ssl/certs/police-intel.crt;
    ssl_certificate_key /etc/ssl/private/police-intel.key;
    
    # Upload size limit
    client_max_body_size 50M;
    
    # Backend API
    location /api/auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/upload/ {
        limit_req zone=upload burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name police-intel.local;
    return 301 https://$server_name$request_uri;
}
```

### B. Authentication & Authorization Enhancement

#### Enhanced JWT with Refresh Tokens (Python)

Create: `backend/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Token generation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32),  # Unique token ID
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token verification
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        username: str = payload.get("user")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Role-based access control
ROLES = {
    "admin": ["read", "write", "delete", "admin"],
    "inspector": ["read", "write", "upload", "export"],
    "analyst": ["read", "export"],
    "readonly": ["read"]
}

def require_role(required_permissions: list):
    def role_checker(token_data: dict = Depends(verify_token)):
        user_role = token_data.get("role", "readonly")
        user_permissions = ROLES.get(user_role, [])
        
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        return token_data
    return role_checker
```

#### MFA Implementation (TOTP)

```python
import pyotp
import qrcode
from io import BytesIO
import base64

def generate_mfa_secret(username: str):
    """Generate TOTP secret for user"""
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="Police Intelligence System"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return secret, qr_code_base64

def verify_mfa_token(secret: str, token: str) -> bool:
    """Verify TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
```

### C. Input Validation & Safe File Handling

#### Enhanced Upload Controller

```python
import hashlib
import magic
from pathlib import Path
import uuid

ALLOWED_MIME_TYPES = ['text/html', 'application/xhtml+xml']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_QUARANTINE = Path("/var/police/quarantine")
UPLOAD_PROCESSED = Path("/var/police/uploads")

def validate_and_process_upload(file: UploadFile, user: str):
    """Secure file upload with validation"""
    
    # 1. Size check
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # 2. Read content
    content = file.file.read()
    file.file.seek(0)
    
    # 3. MIME type validation
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {mime}")
    
    # 4. Content validation - check for IP ACTIVITY table
    html_text = content.decode('utf-8', errors='replace')
    if 'ip activity' not in html_text.lower():
        raise HTTPException(status_code=400, detail="File does not contain IP ACTIVITY table")
    
    # 5. Generate secure filename
    file_uuid = str(uuid.uuid4())
    file_hash = hashlib.sha256(content).hexdigest()
    timestamp = datetime.utcnow().isoformat()
    
    # 6. Save to quarantine first
    UPLOAD_QUARANTINE.mkdir(parents=True, exist_ok=True)
    quarantine_path = UPLOAD_QUARANTINE / f"{file_uuid}.html"
    
    with open(quarantine_path, 'wb') as f:
        f.write(content)
    
    # Set restrictive permissions
    os.chmod(quarantine_path, 0o600)
    
    # 7. Log upload event
    log_upload_event(
        user=user,
        filename=file.filename,
        uuid=file_uuid,
        hash=file_hash,
        size=file_size,
        mime=mime,
        timestamp=timestamp
    )
    
    # 8. Move to processed after validation
    processed_path = UPLOAD_PROCESSED / f"{file_uuid}.html"
    UPLOAD_PROCESSED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(quarantine_path), str(processed_path))
    
    return {
        "uuid": file_uuid,
        "hash": file_hash,
        "path": str(processed_path),
        "size": file_size
    }
```

#### CSV Injection Prevention

```python
def sanitize_for_csv(value):
    """Prevent CSV injection attacks"""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value

def export_safe_csv(data, output_path):
    """Export CSV with injection prevention"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if not data:
            return
        
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        
        for row in data:
            sanitized_row = {k: sanitize_for_csv(v) for k, v in row.items()}
            writer.writerow(sanitized_row)
```

### D. Database Hardening

#### Create Least-Privilege DB User

```sql
-- Create limited application user
CREATE USER police_app WITH PASSWORD 'StrongAppPass_2024!';

-- Grant connection
GRANT CONNECT ON DATABASE police_data TO police_app;

-- Switch to database
\c police_data

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO police_app;

-- Grant specific table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ip_records TO police_app;
GRANT USAGE, SELECT ON SEQUENCE ip_records_id_seq TO police_app;

-- Revoke dangerous permissions
REVOKE CREATE ON SCHEMA public FROM police_app;
REVOKE ALL ON pg_catalog.pg_authid FROM police_app;

-- Enable SSL connections only
ALTER USER police_app SET ssl TO on;
```

#### PostgreSQL Configuration (`postgresql.conf`)

```ini
# Connection Security
ssl = on
ssl_cert_file = '/etc/ssl/certs/postgresql.crt'
ssl_key_file = '/etc/ssl/private/postgresql.key'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'

# Connection Limits
max_connections = 100
superuser_reserved_connections = 3

# Logging for Audit
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'mod'  # Log all modifications
log_connections = on
log_disconnections = on
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Security
password_encryption = scram-sha-256
```

#### pg_hba.conf (Access Control)

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer

# Application connections (SSL required)
hostssl police_data     police_app      10.0.0.0/8              scram-sha-256
hostssl police_data     police_app      172.16.0.0/12           scram-sha-256

# Reject all other connections
host    all             all             0.0.0.0/0               reject
```

### E. Secrets Management

#### HashiCorp Vault Integration

```python
import hvac

class SecretsManager:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_secret(self, path: str, key: str):
        """Retrieve secret from Vault"""
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            return secret['data']['data'][key]
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise
    
    def get_db_credentials(self):
        """Get database credentials"""
        return {
            'host': self.get_secret('police-intel/database', 'host'),
            'port': self.get_secret('police-intel/database', 'port'),
            'user': self.get_secret('police-intel/database', 'user'),
            'password': self.get_secret('police-intel/database', 'password'),
            'database': self.get_secret('police-intel/database', 'database')
        }
    
    def get_jwt_secret(self):
        """Get JWT signing key"""
        return self.get_secret('police-intel/auth', 'jwt_secret')

# Usage in config.py
secrets_manager = SecretsManager()
DB_CREDENTIALS = secrets_manager.get_db_credentials()
JWT_SECRET = secrets_manager.get_jwt_secret()
```

#### Environment Variables (Development Only)

```bash
# .env.example (never commit real .env)
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=police_data
DB_USER=police_app
DB_PASSWORD=CHANGE_ME_IN_PRODUCTION

# JWT
JWT_SECRET=CHANGE_ME_MINIMUM_32_CHARS_RANDOM
JWT_REFRESH_SECRET=DIFFERENT_SECRET_FOR_REFRESH

# Vault (Production)
VAULT_ADDR=https://vault.police.local:8200
VAULT_TOKEN=s.XXXXXXXXXXXX

# Security
ALLOWED_ORIGINS=https://police-intel.local
MAX_UPLOAD_SIZE=52428800
SESSION_TIMEOUT=900
```

---

## 3. Runtime Protections & Monitoring

### A. Web Application Firewall (ModSecurity)

#### ModSecurity Configuration

```nginx
# Load ModSecurity
load_module modules/ngx_http_modsecurity_module.so;

http {
    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsecurity/main.conf;
}
```

#### Custom WAF Rules (`/etc/nginx/modsecurity/custom-rules.conf`)

```conf
# Block SQL Injection
SecRule ARGS "@detectSQLi" \
    "id:1001,phase:2,deny,status:403,log,msg:'SQL Injection Detected'"

# Block XSS
SecRule ARGS "@detectXSS" \
    "id:1002,phase:2,deny,status:403,log,msg:'XSS Attack Detected'"

# Block Path Traversal
SecRule ARGS "@contains ../" \
    "id:1003,phase:2,deny,status:403,log,msg:'Path Traversal Attempt'"

# Block Command Injection
SecRule ARGS "@rx (?:;|\||`|>|<|&|\$\(|\$\{)" \
    "id:1004,phase:2,deny,status:403,log,msg:'Command Injection Attempt'"

# Rate limit uploads
SecRule IP:upload_count "@gt 10" \
    "id:1005,phase:1,deny,status:429,log,msg:'Upload rate limit exceeded'"

# Suspicious user agents
SecRule REQUEST_HEADERS:User-Agent "@rx (?:sqlmap|nikto|nmap|masscan)" \
    "id:1006,phase:1,deny,status:403,log,msg:'Malicious Scanner Detected'"
```

### B. Audit Logging System

```python
import logging
import json
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, log_dir="/var/log/police-intel"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Append-only audit log
        self.audit_file = self.log_dir / "audit.log"
        
        # Configure logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.audit_file,
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, user: str, details: dict, ip_address: str):
        """Log security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "ip_address": ip_address,
            "details": details
        }
        
        self.logger.info(json.dumps(event))
    
    def log_upload(self, user: str, filename: str, file_hash: str, ip: str):
        self.log_event("FILE_UPLOAD", user, {
            "filename": filename,
            "hash": file_hash
        }, ip)
    
    def log_login(self, user: str, success: bool, ip: str):
        self.log_event("LOGIN_ATTEMPT", user, {
            "success": success
        }, ip)
    
    def log_export(self, user: str, run_dir: str, ip: str):
        self.log_event("DATA_EXPORT", user, {
            "run_dir": run_dir
        }, ip)
    
    def log_access_denied(self, user: str, resource: str, ip: str):
        self.log_event("ACCESS_DENIED", user, {
            "resource": resource
        }, ip)

# Usage in endpoints
audit_logger = AuditLogger()

@router.post("/upload/")
async def upload_file(
    file: UploadFile,
    request: Request,
    user: dict = Depends(verify_token)
):
    client_ip = request.client.host
    
    # Process upload...
    
    audit_logger.log_upload(
        user=user['username'],
        filename=file.filename,
        file_hash=file_hash,
        ip=client_ip
    )
```

### C. SIEM Integration (ELK Stack)

#### Filebeat Configuration (`/etc/filebeat/filebeat.yml`)

```yaml
filebeat.inputs:
  # Application logs
  - type: log
    enabled: true
    paths:
      - /var/log/police-intel/audit.log
      - /var/log/police-intel/app.log
    fields:
      service: police-intel
      log_type: application
  
  # Nginx logs
  - type: log
    enabled: true
    paths:
      - /var/log/nginx/access.log
      - /var/log/nginx/error.log
    fields:
      service: nginx
      log_type: web
  
  # PostgreSQL logs
  - type: log
    enabled: true
    paths:
      - /var/log/postgresql/*.log
    fields:
      service: postgresql
      log_type: database

# Output to Elasticsearch
output.elasticsearch:
  hosts: ["https://elasticsearch.police.local:9200"]
  username: "filebeat"
  password: "${FILEBEAT_PASSWORD}"
  ssl.certificate_authorities: ["/etc/pki/root/ca.crt"]

# Kibana dashboard
setup.kibana:
  host: "https://kibana.police.local:5601"
```

#### Alert Rules (Elastalert)

```yaml
# /etc/elastalert/rules/failed_logins.yaml
name: Multiple Failed Login Attempts
type: frequency
index: filebeat-*
num_events: 5
timeframe:
  minutes: 5

filter:
  - term:
      event_type: "LOGIN_ATTEMPT"
  - term:
      details.success: false

alert:
  - email:
      email: "security@police.local"
  - slack:
      slack_webhook_url: "https://hooks.slack.com/services/XXX"

alert_text: |
  Multiple failed login attempts detected
  User: {user}
  IP: {ip_address}
  Count: {num_hits}
```

---

**(Continued in next message due to length...)**
