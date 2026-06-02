"""
User Authentication and Access Control - MongoDB Collections
Collection definitions and helper factories (no SQLAlchemy ORM)
"""
from datetime import datetime, timezone
import hashlib
import secrets

# ---------------------------------------------------------------------------
# Collection names
# ---------------------------------------------------------------------------
USERS_COLLECTION = "users"
USER_SESSIONS_COLLECTION = "user_sessions"
USER_ACTIVITIES_COLLECTION = "user_activities"
LOGIN_ATTEMPTS_COLLECTION = "login_attempts"
ACCESS_LOGS_COLLECTION = "access_logs"
USER_PERMISSIONS_COLLECTION = "user_permissions"
PASSWORD_RESET_TOKENS_COLLECTION = "password_reset_tokens"

# ---------------------------------------------------------------------------
# Index definitions  (applied at startup via ensure_indexes)
# ---------------------------------------------------------------------------
INDEXES = {
    USERS_COLLECTION: [
        {"keys": "username", "unique": True},
        {"keys": "email", "unique": True},
    ],
    USER_SESSIONS_COLLECTION: [
        {"keys": "session_token", "unique": True},
        {"keys": "refresh_token", "unique": True},
        {"keys": "user_id"},
    ],
    USER_ACTIVITIES_COLLECTION: [
        {"keys": "user_id"},
        {"keys": "username"},
        {"keys": "timestamp"},
        {"keys": "activity_type"},
    ],
    LOGIN_ATTEMPTS_COLLECTION: [
        {"keys": "username"},
        {"keys": "attempted_at"},
    ],
    ACCESS_LOGS_COLLECTION: [
        {"keys": "user_id"},
        {"keys": "timestamp"},
    ],
    USER_PERMISSIONS_COLLECTION: [
        {"keys": "user_id"},
    ],
    PASSWORD_RESET_TOKENS_COLLECTION: [
        {"keys": "token", "unique": True},
        {"keys": "user_id"},
    ],
}


# ---------------------------------------------------------------------------
# Document factories  (replace SQLAlchemy model constructors)
# ---------------------------------------------------------------------------
def new_user(*, username, email, password_hash, salt, full_name,
             role="investigator", created_by=None, **extra):
    doc = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "salt": salt,
        "full_name": full_name,
        "badge_number": extra.get("badge_number"),
        "department": extra.get("department"),
        "designation": extra.get("designation"),
        "phone_number": extra.get("phone_number"),
        "role": role,
        "permissions": extra.get("permissions"),
        "is_active": True,
        "is_approved": False,
        "approved_at": None,
        "is_verified": False,
        "is_locked": False,
        "failed_login_attempts": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
        "last_login": None,
        "last_password_change": extra.get("last_password_change"),
        "two_factor_enabled": False,
        "two_factor_secret": None,
        "recovery_email": None,
        "created_by": created_by,
        "approved_by": None,
        "notes": None,
    }
    return doc


def new_user_session(*, user_id, username, session_token, refresh_token,
                     ip_address=None, user_agent=None, device_type=None,
                     browser=None, os=None, expires_at=None, **extra):
    return {
        "user_id": user_id,
        "username": username,
        "session_token": session_token,
        "refresh_token": refresh_token,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "device_type": device_type,
        "browser": browser,
        "os": os,
        "country": extra.get("country"),
        "city": extra.get("city"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "last_activity": datetime.now(timezone.utc),
    }


def new_user_activity(*, user_id=None, username=None, session_id=None,
                      activity_type=None, activity_description=None,
                      ip_address=None, user_agent=None, page_url=None,
                      fir_number=None, **extra):
    return {
        "user_id": user_id,
        "username": username,
        "session_id": session_id,
        "activity_type": activity_type,
        "activity_description": activity_description,
        "activity_data": extra.get("activity_data"),
        "page_url": page_url,
        "page_title": extra.get("page_title"),
        "http_method": extra.get("http_method"),
        "http_status": extra.get("http_status"),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "device_type": extra.get("device_type"),
        "browser": extra.get("browser"),
        "os": extra.get("os"),
        "country": extra.get("country"),
        "city": extra.get("city"),
        "region": extra.get("region"),
        "timestamp": datetime.now(timezone.utc),
        "fir_number": fir_number,
        "is_suspicious": False,
        "risk_score": 0,
        "notes": None,
    }


def new_login_attempt(*, username=None, email=None, success=False,
                      failure_reason=None, ip_address=None,
                      user_agent=None, device_type=None,
                      browser=None, os=None, **extra):
    return {
        "username": username,
        "email": email,
        "success": success,
        "failure_reason": failure_reason,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "device_type": device_type,
        "browser": browser,
        "os": os,
        "country": extra.get("country"),
        "city": extra.get("city"),
        "attempted_at": datetime.now(timezone.utc),
        "is_suspicious": False,
        "blocked": extra.get("blocked", False),
        "notes": None,
    }


def new_password_reset_token(*, user_id, email, token, expires_at, request_ip=None):
    return {
        "user_id": user_id,
        "email": email,
        "token": token,
        "is_used": False,
        "used_at": None,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "request_ip": request_ip,
    }