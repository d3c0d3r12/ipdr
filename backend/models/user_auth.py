"""
User Authentication and Access Control Models
Secure login system with role-based access
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from core.db import Base
import hashlib
import secrets


class User(Base):
    """User accounts with role-based access"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=False)
    
    # Profile
    full_name = Column(String(200))
    badge_number = Column(String(50))
    department = Column(String(200))
    designation = Column(String(200))
    phone_number = Column(String(20))
    
    # Role and permissions
    role = Column(String(50), default="investigator")  # admin, senior_officer, investigator, analyst, viewer
    permissions = Column(JSON)  # List of specific permissions
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    last_password_change = Column(DateTime(timezone=True))
    
    # Security
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(100))
    recovery_email = Column(String(200))
    
    # Metadata
    created_by = Column(String(100))  # Admin who created this account
    approved_by = Column(String(100))
    notes = Column(Text)


class UserSession(Base):
    """Active user sessions"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    username = Column(String(100), index=True)
    
    # Session details
    session_token = Column(String(256), unique=True, index=True, nullable=False)
    refresh_token = Column(String(256), unique=True)
    
    # Device information
    ip_address = Column(String(100))
    user_agent = Column(Text)
    device_type = Column(String(50))  # desktop, mobile, tablet
    browser = Column(String(100))
    os = Column(String(100))
    
    # Location
    country = Column(String(100))
    city = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))


class UserActivity(Base):
    """User interaction tracking - everything they do"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String(100), index=True)
    session_id = Column(Integer, index=True)
    
    # Activity details
    activity_type = Column(String(100), index=True)  # login, logout, view_fir, upload, download, search
    activity_description = Column(Text)
    activity_data = Column(JSON)  # Detailed activity data
    
    # Page/Resource accessed
    page_url = Column(String(1000))
    page_title = Column(String(500))
    http_method = Column(String(10))  # GET, POST, PUT, DELETE
    http_status = Column(Integer)
    
    # Request details
    ip_address = Column(String(100), index=True)
    ipv4 = Column(String(50))
    ipv6 = Column(String(100))
    user_agent = Column(Text)
    referer = Column(String(1000))
    
    # Device information
    device_type = Column(String(50))
    browser = Column(String(100))
    browser_version = Column(String(50))
    os = Column(String(100))
    os_version = Column(String(50))
    screen_resolution = Column(String(50))
    
    # Location
    country = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    duration_ms = Column(Integer)  # How long they spent on page
    
    # Cookies and tracking
    cookies = Column(JSON)
    session_data = Column(JSON)
    
    # FIR context (if applicable)
    fir_number = Column(String(100), index=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)
    notes = Column(Text)


class LoginAttempt(Base):
    """Track all login attempts (successful and failed)"""
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Attempt details
    username = Column(String(100), index=True)
    email = Column(String(200), index=True)
    success = Column(Boolean, default=False)
    failure_reason = Column(String(200))
    
    # Device and location
    ip_address = Column(String(100), index=True)
    user_agent = Column(Text)
    device_type = Column(String(50))
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(100))
    city = Column(String(100))
    
    # Timestamp
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Security
    is_suspicious = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
    notes = Column(Text)


class AccessLog(Base):
    """Detailed access logs for audit trail"""
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String(100), index=True)
    
    # Access details
    resource_type = Column(String(100))  # fir, evidence, report, user, settings
    resource_id = Column(String(200))
    action = Column(String(100))  # view, create, update, delete, download, export
    
    # Request details
    ip_address = Column(String(100))
    endpoint = Column(String(500))
    http_method = Column(String(10))
    http_status = Column(Integer)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    response_time_ms = Column(Integer)
    
    # Data
    request_data = Column(JSON)
    response_data = Column(JSON)
    
    # Security
    is_authorized = Column(Boolean, default=True)
    is_suspicious = Column(Boolean, default=False)
    notes = Column(Text)


class UserPermission(Base):
    """Granular permissions for users"""
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Permission details
    permission_name = Column(String(100), index=True)  # view_fir, create_fir, delete_fir, etc.
    resource_type = Column(String(100))  # fir, user, evidence, report
    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=True)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_export = Column(Boolean, default=False)
    
    # Scope
    scope = Column(String(50), default="own")  # own, department, all
    
    # Timestamps
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(String(100))
    expires_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
