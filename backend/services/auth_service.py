"""
Authentication Service
Handles user authentication, session management, and security
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.user_auth import User, UserSession, LoginAttempt, UserActivity
from user_agents import parse as parse_user_agent
import re


class AuthService:
    """Authentication and authorization service"""
    
    # JWT settings
    SECRET_KEY = secrets.token_urlsafe(32)  # Change this in production!
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    
    # Security settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    PASSWORD_MIN_LENGTH = 8
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
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
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "investigator",
        created_by: Optional[str] = None
    ) -> tuple[Optional[User], str]:
        """Create new user account"""
        
        # Validate password
        is_valid, message = AuthService.validate_password_strength(password)
        if not is_valid:
            return None, message
        
        # Check if username exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return None, "Username already exists"
        
        # Check if email exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return None, "Email already exists"
        
        # Hash password
        password_hash, salt = AuthService.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            full_name=full_name,
            role=role,
            created_by=created_by,
            last_password_change=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user, "User created successfully"
    
    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> tuple[Optional[User], Optional[str], str]:
        """Authenticate user and create session"""
        
        # Parse user agent
        ua = parse_user_agent(user_agent)
        
        # Log login attempt
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=ua.device.family,
            browser=ua.browser.family,
            os=ua.os.family
        )
        
        # Find user
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            attempt.success = False
            attempt.failure_reason = "User not found"
            db.add(attempt)
            db.commit()
            return None, None, "Invalid username or password"
        
        # Check if account is locked
        if user.is_locked:
            attempt.success = False
            attempt.failure_reason = "Account locked"
            attempt.blocked = True
            db.add(attempt)
            db.commit()
            return None, None, "Account is locked. Contact administrator."
        
        # Check if account is active
        if not user.is_active:
            attempt.success = False
            attempt.failure_reason = "Account inactive"
            db.add(attempt)
            db.commit()
            return None, None, "Account is inactive. Contact administrator."
        
        # Verify password
        if not AuthService.verify_password(password, user.password_hash, user.salt):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= AuthService.MAX_FAILED_ATTEMPTS:
                user.is_locked = True
            
            attempt.success = False
            attempt.failure_reason = "Invalid password"
            db.add(attempt)
            db.commit()
            
            return None, None, "Invalid username or password"
        
        # Success! Reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        
        # Create session token
        session_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            username=user.username,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=ua.device.family,
            browser=ua.browser.family,
            os=ua.os.family,
            expires_at=datetime.utcnow() + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
            last_activity=datetime.utcnow()
        )
        
        # Log successful attempt
        attempt.success = True
        
        db.add(session)
        db.add(attempt)
        db.commit()
        db.refresh(session)
        
        return user, session_token, "Login successful"
    
    @staticmethod
    def create_jwt_token(user: User, session_token: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "session_token": session_token,
            "exp": datetime.utcnow() + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)
    
    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def verify_session(db: Session, session_token: str) -> Optional[User]:
        """Verify session token and return user"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None
        
        # Check if expired
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            db.commit()
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == session.user_id).first()
        return user
    
    @staticmethod
    def logout(db: Session, session_token: str) -> bool:
        """Logout user by invalidating session"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def log_activity(
        db: Session,
        user_id: int,
        username: str,
        activity_type: str,
        activity_description: str,
        ip_address: str,
        user_agent: str,
        page_url: str = None,
        activity_data: Dict = None,
        fir_number: str = None
    ):
        """Log user activity"""
        
        # Parse user agent
        ua = parse_user_agent(user_agent)
        
        activity = UserActivity(
            user_id=user_id,
            username=username,
            activity_type=activity_type,
            activity_description=activity_description,
            activity_data=activity_data,
            page_url=page_url,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=ua.device.family,
            browser=ua.browser.family,
            os=ua.os.family,
            fir_number=fir_number
        )
        
        db.add(activity)
        db.commit()
    
    @staticmethod
    def check_permission(user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        
        # Admin has all permissions
        if user.role == "admin":
            return True
        
        # Check role-based permissions
        role_permissions = {
            "senior_officer": ["view_all_fir", "create_fir", "update_fir", "view_reports", "export_data"],
            "investigator": ["view_own_fir", "create_fir", "update_own_fir", "upload_evidence"],
            "analyst": ["view_all_fir", "view_reports", "export_data"],
            "viewer": ["view_own_fir"]
        }
        
        allowed_permissions = role_permissions.get(user.role, [])
        return permission in allowed_permissions
