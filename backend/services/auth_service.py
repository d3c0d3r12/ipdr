"""
Authentication Service
Handles user authentication, session management, and security
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from models.user_auth import (
    USERS_COLLECTION, USER_SESSIONS_COLLECTION,
    LOGIN_ATTEMPTS_COLLECTION, USER_ACTIVITIES_COLLECTION,
    PASSWORD_RESET_TOKENS_COLLECTION,
    new_user, new_user_session, new_user_activity,
    new_login_attempt, new_password_reset_token,
)
from user_agents import parse as parse_user_agent
from core.config import JWT_SECRET, JWT_REFRESH_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import re


class AuthService:
    """Authentication and authorization service"""
    
    # JWT settings (loaded from config)
    SECRET_KEY = JWT_SECRET
    REFRESH_KEY = JWT_REFRESH_SECRET
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = REFRESH_TOKEN_EXPIRE_DAYS
    
    # Security settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    PASSWORD_MIN_LENGTH = 8
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = AuthService.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password meets security requirements"""
        if len(password) < AuthService.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {AuthService.PASSWORD_MIN_LENGTH} characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, "Password is strong"
    
    @staticmethod
    def create_user(db, username, email, password, full_name,
                    role="investigator", created_by=None):
        """Create new user account"""
        is_valid, message = AuthService.validate_password_strength(password)
        if not is_valid:
            return None, message
        
        if db[USERS_COLLECTION].find_one({"username": username}):
            return None, "Username already exists"
        if db[USERS_COLLECTION].find_one({"email": email}):
            return None, "Email already exists"
        
        password_hash, salt = AuthService.hash_password(password)
        
        user_doc = new_user(
            username=username, email=email,
            password_hash=password_hash, salt=salt,
            full_name=full_name, role=role, created_by=created_by,
        )
        user_doc["last_password_change"] = datetime.now(timezone.utc)
        
        result = db[USERS_COLLECTION].insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        return user_doc, "User created successfully"
    
    @staticmethod
    def authenticate_user(db, username, password, ip_address, user_agent):
        """Authenticate user and create session"""
        ua = parse_user_agent(user_agent)
        
        attempt_doc = new_login_attempt(
            username=username, ip_address=ip_address, user_agent=user_agent,
            device_type=ua.device.family, browser=ua.browser.family, os=ua.os.family,
        )
        
        user = db[USERS_COLLECTION].find_one({"username": username})
        
        if not user:
            attempt_doc["success"] = False
            attempt_doc["failure_reason"] = "User not found"
            db[LOGIN_ATTEMPTS_COLLECTION].insert_one(attempt_doc)
            return None, None, "Invalid username or password"
        
        if user.get("is_locked"):
            attempt_doc["success"] = False
            attempt_doc["failure_reason"] = "Account locked"
            attempt_doc["blocked"] = True
            db[LOGIN_ATTEMPTS_COLLECTION].insert_one(attempt_doc)
            return None, None, "Account is locked. Contact administrator."
        
        if not user.get("is_active", True):
            attempt_doc["success"] = False
            attempt_doc["failure_reason"] = "Account inactive"
            db[LOGIN_ATTEMPTS_COLLECTION].insert_one(attempt_doc)
            return None, None, "Account is inactive. Contact administrator."
        
        if not AuthService.verify_password(password, user["password_hash"], user["salt"]):
            failed = (user.get("failed_login_attempts") or 0) + 1
            update_fields = {"failed_login_attempts": failed}
            if failed >= AuthService.MAX_FAILED_ATTEMPTS:
                update_fields["is_locked"] = True
            db[USERS_COLLECTION].update_one({"_id": user["_id"]}, {"$set": update_fields})
            
            attempt_doc["success"] = False
            attempt_doc["failure_reason"] = "Invalid password"
            db[LOGIN_ATTEMPTS_COLLECTION].insert_one(attempt_doc)
            return None, None, "Invalid username or password"
        
        # Success - reset failed attempts
        db[USERS_COLLECTION].update_one({"_id": user["_id"]}, {"$set": {
            "failed_login_attempts": 0,
            "last_login": datetime.now(timezone.utc),
        }})
        user["failed_login_attempts"] = 0
        user["last_login"] = datetime.now(timezone.utc)
        
        session_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)
        
        session_doc = new_user_session(
            user_id=str(user["_id"]),
            username=user["username"],
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=ua.device.family,
            browser=ua.browser.family,
            os=ua.os.family,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        attempt_doc["success"] = True
        
        db[USER_SESSIONS_COLLECTION].insert_one(session_doc)
        db[LOGIN_ATTEMPTS_COLLECTION].insert_one(attempt_doc)
        
        return user, session_token, "Login successful"
    
    @staticmethod
    def create_jwt_token(user: dict, session_token: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", "investigator"),
            "session_token": session_token,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user: dict, session_token: str) -> str:
        """Create JWT refresh token (longer expiry)"""
        payload = {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "session_token": session_token,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, AuthService.REFRESH_KEY, algorithm=AuthService.ALGORITHM)
    
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode refresh token"""
        try:
            payload = jwt.decode(refresh_token, AuthService.REFRESH_KEY, algorithms=[AuthService.ALGORITHM])
            if payload.get("type") != "refresh":
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            return jwt.decode(token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @staticmethod
    def verify_session(db, session_token: str) -> Optional[dict]:
        """Verify session token and return user"""
        session = db[USER_SESSIONS_COLLECTION].find_one({
            "session_token": session_token,
            "is_active": True,
        })
        
        if not session:
            return None
        
        expires_at = session.get("expires_at")
        if not expires_at:
            db[USER_SESSIONS_COLLECTION].update_one(
                {"_id": session["_id"]}, {"$set": {"is_active": False}}
            )
            return None
        
        now = datetime.now(timezone.utc)
        exp_aware = expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at
        if exp_aware < now:
            db[USER_SESSIONS_COLLECTION].update_one(
                {"_id": session["_id"]}, {"$set": {"is_active": False}}
            )
            return None
        
        db[USER_SESSIONS_COLLECTION].update_one(
            {"_id": session["_id"]}, {"$set": {"last_activity": now}}
        )
        
        uid = session["user_id"]
        try:
            uid = ObjectId(uid) if not isinstance(uid, ObjectId) else uid
        except Exception:
            pass
        user = db[USERS_COLLECTION].find_one({"_id": uid})
        return user
    
    @staticmethod
    def logout(db, session_token: str) -> bool:
        """Logout user by invalidating session"""
        result = db[USER_SESSIONS_COLLECTION].update_one(
            {"session_token": session_token}, {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def log_activity(db, user_id, username, activity_type, activity_description,
                     ip_address, user_agent, page_url=None, activity_data=None,
                     fir_number=None):
        """Log user activity"""
        ua = parse_user_agent(user_agent)
        
        doc = new_user_activity(
            user_id=str(user_id) if not isinstance(user_id, str) else user_id,
            username=username,
            activity_type=activity_type,
            activity_description=activity_description,
            ip_address=ip_address,
            user_agent=user_agent,
            page_url=page_url,
            fir_number=fir_number,
            activity_data=activity_data,
            device_type=ua.device.family,
            browser=ua.browser.family,
            os=ua.os.family,
        )
        db[USER_ACTIVITIES_COLLECTION].insert_one(doc)
    
    @staticmethod
    def check_permission(user: dict, permission: str) -> bool:
        """Check if user has specific permission"""
        if user.get("role") == "admin":
            return True
        role_permissions = {
            "senior_officer": ["view_all_fir", "create_fir", "update_fir", "view_reports", "export_data"],
            "investigator": ["view_own_fir", "create_fir", "update_own_fir", "upload_evidence"],
            "analyst": ["view_all_fir", "view_reports", "export_data"],
            "viewer": ["view_own_fir"],
        }
        return permission in role_permissions.get(user.get("role", ""), [])

    @staticmethod
    def create_password_reset_token(db, email, user_id, request_ip):
        """Create a password reset token"""
        reset_token = secrets.token_urlsafe(32)
        doc = new_password_reset_token(
            user_id=str(user_id) if not isinstance(user_id, str) else user_id,
            email=email,
            token=reset_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            request_ip=request_ip,
        )
        db[PASSWORD_RESET_TOKENS_COLLECTION].insert_one(doc)
        return reset_token
    
    @staticmethod
    def verify_reset_token(db, token):
        """Verify reset token and return user_id, email"""
        doc = db[PASSWORD_RESET_TOKENS_COLLECTION].find_one({
            "token": token,
            "is_used": False,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        })
        if not doc:
            return None
        return doc["user_id"], doc["email"]
    
    @staticmethod
    def reset_password(db, reset_token, new_password):
        """Reset password using reset token"""
        result = AuthService.verify_reset_token(db, reset_token)
        if not result:
            return False, "Invalid or expired reset token"
        
        user_id, email = result
        try:
            uid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
        except Exception:
            uid = user_id
        user = db[USERS_COLLECTION].find_one({"_id": uid})
        if not user:
            return False, "User not found"
        
        is_valid, message = AuthService.validate_password_strength(new_password)
        if not is_valid:
            return False, message
        
        password_hash, salt = AuthService.hash_password(new_password)
        db[USERS_COLLECTION].update_one({"_id": user["_id"]}, {"$set": {
            "password_hash": password_hash,
            "salt": salt,
            "last_password_change": datetime.now(timezone.utc),
        }})
        
        db[PASSWORD_RESET_TOKENS_COLLECTION].update_one(
            {"token": reset_token},
            {"$set": {"is_used": True, "used_at": datetime.now(timezone.utc)}},
        )
        
        return True, "Password reset successfully"
