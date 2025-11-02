"""
FIR Case Management Models
Stores all investigation data per FIR number
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Boolean, Float
from sqlalchemy.sql import func
from core.db import Base


class FIRCase(Base):
    """Main FIR case table - stores investigation metadata"""
    __tablename__ = "fir_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(100), unique=True, index=True, nullable=False)
    case_title = Column(String(500))
    case_description = Column(Text)
    investigating_officer = Column(String(200))
    department = Column(String(200))
    status = Column(String(50), default="active")  # active, closed, pending
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_ips = Column(Integer, default=0)
    total_suspects = Column(Integer, default=0)
    total_evidence = Column(Integer, default=0)
    
    # Metadata
    tags = Column(JSON)  # ["cybercrime", "fraud", "harassment"]
    notes = Column(Text)


class FIRIPLookup(Base):
    """IP lookup results for each FIR"""
    __tablename__ = "fir_ip_lookups"
    
    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(100), index=True, nullable=False)
    
    # IP Information
    ip_address = Column(String(100), index=True)
    ip_version = Column(String(10))  # IPv4 or IPv6
    
    # Geolocation
    country = Column(String(100))
    country_code = Column(String(10))
    city = Column(String(100))
    region = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(100))
    postal_code = Column(String(20))
    
    # ISP Information
    isp = Column(String(200))
    organization = Column(String(200))
    asn = Column(String(50))
    
    # Activity
    timestamp = Column(DateTime(timezone=True))
    activity_type = Column(String(100))
    
    # Metadata
    lookup_date = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(50), default="infobyip")
    raw_data = Column(JSON)  # Store complete JSON response
    
    # Analysis flags
    is_suspicious = Column(Boolean, default=False)
    risk_score = Column(Integer, default=0)  # 0-100
    notes = Column(Text)


class FIREvidence(Base):
    """Evidence files and documents for each FIR"""
    __tablename__ = "fir_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(100), index=True, nullable=False)
    
    # File information
    file_name = Column(String(500))
    file_type = Column(String(50))  # html, csv, json, pdf, image
    file_size = Column(Integer)  # bytes
    file_path = Column(String(1000))
    file_hash = Column(String(64))  # SHA256
    
    # Metadata
    uploaded_by = Column(String(200))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text)
    tags = Column(JSON)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50))  # pending, processing, completed, failed
    processing_notes = Column(Text)


class FIRSuspect(Base):
    """Suspects/persons of interest for each FIR"""
    __tablename__ = "fir_suspects"
    
    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(100), index=True, nullable=False)
    
    # Suspect information
    name = Column(String(200))
    alias = Column(String(200))
    phone_numbers = Column(JSON)  # List of phone numbers
    email_addresses = Column(JSON)  # List of emails
    ip_addresses = Column(JSON)  # List of IPs
    social_media = Column(JSON)  # Social media handles
    
    # Details
    description = Column(Text)
    known_locations = Column(JSON)
    associates = Column(JSON)
    
    # Status
    status = Column(String(50), default="under_investigation")
    risk_level = Column(String(20), default="medium")
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Notes
    notes = Column(Text)


class FIRTimeline(Base):
    """Timeline of events for each FIR"""
    __tablename__ = "fir_timeline"
    
    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(100), index=True, nullable=False)
    
    # Event details
    event_type = Column(String(100))  # upload, analysis, evidence_added, suspect_added
    event_title = Column(String(500))
    event_description = Column(Text)
    event_data = Column(JSON)
    
    # Who and when
    performed_by = Column(String(200))
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    importance = Column(String(20), default="normal")  # low, normal, high, critical
    tags = Column(JSON)
