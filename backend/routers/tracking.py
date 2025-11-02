"""
User Tracking API Endpoints
Tracks user sessions, activities, and page views
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import httpx
from user_agents import parse

from core.db import get_db
from models.user_auth import UserSession, UserActivity

router = APIRouter()


# Pydantic Models
class SessionCreate(BaseModel):
    username: Optional[str] = None
    user_role: Optional[str] = None
    is_authenticated: bool = False
    user_agent: str
    screen_resolution: Optional[str] = None
    viewport_size: Optional[str] = None
    color_depth: Optional[int] = None
    referrer_url: Optional[str] = None
    entry_page: Optional[str] = None
    connection_type: Optional[str] = None
    effective_type: Optional[str] = None
    cookies_enabled: Optional[bool] = None
    language: Optional[str] = None
    languages: Optional[List[str]] = None
    do_not_track: Optional[bool] = None


class ActivityCreate(BaseModel):
    session_id: str
    activity_type: str
    activity_description: Optional[str] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    action_category: Optional[str] = None
    action_data: Optional[dict] = None
    load_time: Optional[int] = None
    status: str = "success"
    error_message: Optional[str] = None


class PageViewCreate(BaseModel):
    session_id: str
    page_url: str
    page_title: Optional[str] = None
    page_path: Optional[str] = None
    previous_page: Optional[str] = None


class SessionEnd(BaseModel):
    session_id: str
    exit_page: Optional[str] = None


# Helper Functions
async def get_ip_details(ip_address: str) -> dict:
    """Get IP geolocation details from external API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip_address}", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return {
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("isp")
                }
    except Exception as e:
        print(f"Error fetching IP details: {e}")
    return {}


def parse_user_agent(user_agent_string: str) -> dict:
    """Parse user agent string to extract device details"""
    user_agent = parse(user_agent_string)
    return {
        "browser": user_agent.browser.family,
        "browser_version": user_agent.browser.version_string,
        "os": user_agent.os.family,
        "os_version": user_agent.os.version_string,
        "device_type": "mobile" if user_agent.is_mobile else ("tablet" if user_agent.is_tablet else "desktop"),
        "device_vendor": user_agent.device.brand,
        "device_model": user_agent.device.model
    }


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


# API Endpoints

@router.post("/session/start")
async def start_session(
    session_data: SessionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Start a new user session
    Captures device, location, and browser details
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Get IP geolocation details
        ip_details = await get_ip_details(ip_address)
        
        # Parse user agent
        device_details = parse_user_agent(session_data.user_agent)
        
        # Create session record
        new_session = UserSession(
            session_id=session_id,
            username=session_data.username,
            user_role=session_data.user_role,
            is_authenticated=session_data.is_authenticated,
            ip_address=ip_address,
            user_agent=session_data.user_agent,
            screen_resolution=session_data.screen_resolution,
            viewport_size=session_data.viewport_size,
            color_depth=session_data.color_depth,
            referrer_url=session_data.referrer_url,
            entry_page=session_data.entry_page,
            connection_type=session_data.connection_type,
            effective_type=session_data.effective_type,
            cookies_enabled=session_data.cookies_enabled,
            language=session_data.language,
            languages=session_data.languages,
            do_not_track=session_data.do_not_track,
            **ip_details,
            **device_details
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return {
            "session_id": session_id,
            "ip_address": ip_address,
            "location": f"{ip_details.get('city', 'Unknown')}, {ip_details.get('country', 'Unknown')}",
            "device": device_details.get('device_type'),
            "browser": f"{device_details.get('browser')} {device_details.get('browser_version')}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@router.post("/session/end")
async def end_session(
    session_end: SessionEnd,
    db: Session = Depends(get_db)
):
    """End a user session and calculate duration"""
    try:
        session = db.query(UserSession).filter(UserSession.session_id == session_end.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate session duration
        session.session_end = datetime.utcnow()
        if session.session_start:
            duration = (session.session_end - session.session_start).total_seconds()
            session.session_duration = int(duration)
        
        session.exit_page = session_end.exit_page
        
        db.commit()
        
        return {
            "message": "Session ended successfully",
            "duration_seconds": session.session_duration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")


@router.post("/activity/log")
async def log_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db)
):
    """Log a user activity"""
    try:
        # Update session last activity
        session = db.query(UserSession).filter(UserSession.session_id == activity.session_id).first()
        if session:
            session.last_activity = datetime.utcnow()
        
        # Create activity record
        new_activity = UserActivity(
            session_id=activity.session_id,
            activity_type=activity.activity_type,
            activity_description=activity.activity_description,
            page_url=activity.page_url,
            page_title=activity.page_title,
            action_category=activity.action_category,
            action_data=activity.action_data,
            load_time=activity.load_time,
            status=activity.status,
            error_message=activity.error_message
        )
        
        db.add(new_activity)
        db.commit()
        
        return {"message": "Activity logged successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging activity: {str(e)}")


# Commented out - PageView model not in new schema
# @router.post("/pageview/log")
# async def log_pageview(
#     pageview: PageViewCreate,
#     db: Session = Depends(get_db)
# ):
#     """Log a page view"""
#     # Use UserActivity instead for page tracking
#     return {"message": "Use /activity/log endpoint for page tracking"}


@router.get("/sessions/active")
async def get_active_sessions(
    db: Session = Depends(get_db)
):
    """Get all active sessions (not ended)"""
    try:
        # Sessions active in last 30 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        sessions = db.query(UserSession).filter(
            and_(
                UserSession.session_end.is_(None),
                UserSession.last_activity >= cutoff_time
            )
        ).order_by(desc(UserSession.last_activity)).all()
        
        return {
            "count": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "username": s.username,
                    "ip_address": s.ip_address,
                    "location": f"{s.city or 'Unknown'}, {s.country or 'Unknown'}",
                    "device": s.device_type,
                    "browser": s.browser,
                    "session_start": s.session_start.isoformat() if s.session_start else None,
                    "last_activity": s.last_activity.isoformat() if s.last_activity else None,
                    "idle_seconds": int((datetime.utcnow() - s.last_activity).total_seconds()) if s.last_activity else None
                }
                for s in sessions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active sessions: {str(e)}")


@router.get("/sessions/stats")
async def get_session_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get session statistics for the last N days"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total sessions
        total_sessions = db.query(func.count(UserSession.id)).filter(
            UserSession.session_start >= cutoff_date
        ).scalar()
        
        # Unique visitors (by IP)
        unique_visitors = db.query(func.count(func.distinct(UserSession.ip_address))).filter(
            UserSession.session_start >= cutoff_date
        ).scalar()
        
        # Authenticated sessions
        authenticated = db.query(func.count(UserSession.id)).filter(
            and_(
                UserSession.session_start >= cutoff_date,
                UserSession.is_authenticated == True
            )
        ).scalar()
        
        # Average session duration
        avg_duration = db.query(func.avg(UserSession.session_duration)).filter(
            and_(
                UserSession.session_start >= cutoff_date,
                UserSession.session_duration.isnot(None)
            )
        ).scalar()
        
        # Device breakdown
        device_stats = db.query(
            UserSession.device_type,
            func.count(UserSession.id).label('count')
        ).filter(
            UserSession.session_start >= cutoff_date
        ).group_by(UserSession.device_type).all()
        
        # Top countries
        country_stats = db.query(
            UserSession.country,
            func.count(UserSession.id).label('count')
        ).filter(
            UserSession.session_start >= cutoff_date
        ).group_by(UserSession.country).order_by(desc('count')).limit(10).all()
        
        return {
            "period_days": days,
            "total_sessions": total_sessions or 0,
            "unique_visitors": unique_visitors or 0,
            "authenticated_sessions": authenticated or 0,
            "avg_duration_seconds": int(avg_duration) if avg_duration else 0,
            "device_breakdown": {d.device_type: d.count for d in device_stats if d.device_type},
            "top_countries": [{"country": c.country, "count": c.count} for c in country_stats if c.country]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/activities/recent")
async def get_recent_activities(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent user activities"""
    try:
        activities = db.query(UserActivity).order_by(desc(UserActivity.timestamp)).limit(limit).all()
        
        return {
            "count": len(activities),
            "activities": [
                {
                    "id": a.id,
                    "session_id": a.session_id,
                    "activity_type": a.activity_type,
                    "description": a.activity_description,
                    "page_url": a.page_url,
                    "status": a.status,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else None
                }
                for a in activities
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")
