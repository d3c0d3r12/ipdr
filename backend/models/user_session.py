"""
User Session Tracking Models
Tracks user visits, activities, and page views
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, DECIMAL, ARRAY, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base

class UserSession(Base):
    """User Session Model - Tracks every user visit"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # User Information
    username = Column(String(100), index=True)
    user_role = Column(String(50))
    is_authenticated = Column(Boolean, default=False)
    
    # IP & Location Details
    ip_address = Column(String(45), nullable=False, index=True)
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    timezone = Column(String(50))
    isp = Column(String(255))
    
    # Device Information
    user_agent = Column(Text)
    browser = Column(String(100))
    browser_version = Column(String(50))
    os = Column(String(100))
    os_version = Column(String(50))
    device_type = Column(String(50))  # desktop, mobile, tablet
    device_vendor = Column(String(100))
    device_model = Column(String(100))
    
    # Screen & Display
    screen_resolution = Column(String(50))
    viewport_size = Column(String(50))
    color_depth = Column(Integer)
    
    # Session Timing
    session_start = Column(TIMESTAMP(timezone=True), server_default=func.now())
    session_end = Column(TIMESTAMP(timezone=True))
    last_activity = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    session_duration = Column(Integer)  # in seconds
    
    # Referrer & Entry
    referrer_url = Column(Text)
    entry_page = Column(String(500))
    exit_page = Column(String(500))
    
    # Network Details
    connection_type = Column(String(50))
    effective_type = Column(String(50))  # 4g, 3g, 2g, slow-2g
    downlink = Column(DECIMAL(5, 2))
    rtt = Column(Integer)
    
    # Browser Features
    cookies_enabled = Column(Boolean)
    javascript_enabled = Column(Boolean, default=True)
    language = Column(String(10))
    languages = Column(ARRAY(String))
    
    # Security & Privacy
    do_not_track = Column(Boolean)
    incognito_mode = Column(Boolean)
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    activities = relationship("UserActivity", back_populates="session", cascade="all, delete-orphan")
    page_views = relationship("PageView", back_populates="session", cascade="all, delete-orphan")


class UserActivity(Base):
    """User Activity Model - Tracks every action performed by users"""
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Activity Details
    activity_type = Column(String(100), nullable=False, index=True)  # page_view, upload, download, search, etc.
    activity_description = Column(Text)
    page_url = Column(String(500))
    page_title = Column(String(255))
    
    # Action Details
    action_category = Column(String(100))  # navigation, file_operation, data_query, etc.
    action_data = Column(JSON)  # Store additional data as JSON
    
    # Performance
    load_time = Column(Integer)  # milliseconds
    interaction_time = Column(Integer)  # time spent on action
    
    # Result
    status = Column(String(50))  # success, error, pending
    error_message = Column(Text)
    
    # Timestamp
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("UserSession", back_populates="activities")


class PageView(Base):
    """Page View Model - Detailed page navigation tracking"""
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Page Details
    page_url = Column(String(500), nullable=False, index=True)
    page_title = Column(String(255))
    page_path = Column(String(500))
    
    # Timing
    view_start = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    view_end = Column(TIMESTAMP(timezone=True))
    time_on_page = Column(Integer)  # seconds
    
    # Interaction
    scroll_depth = Column(Integer)  # percentage
    clicks_count = Column(Integer, default=0)
    
    # Navigation
    previous_page = Column(String(500))
    next_page = Column(String(500))
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("UserSession", back_populates="page_views")
