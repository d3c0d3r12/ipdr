"""
User Tracking API Endpoints
Tracks user sessions, activities, and page views
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import uuid
import httpx
from user_agents import parse

from core.db import get_db
from models.user_auth import USER_SESSIONS_COLLECTION, USER_ACTIVITIES_COLLECTION

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
                    "isp": data.get("isp"),
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
        "device_model": user_agent.device.model,
    }


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


# API Endpoints

@router.post("/session/start")
async def start_session(
    session_data: SessionCreate,
    request: Request,
    db=Depends(get_db)
):
    """Start a new user session"""
    try:
        session_id = str(uuid.uuid4())
        ip_address = get_client_ip(request)
        ip_details = await get_ip_details(ip_address)
        device_details = parse_user_agent(session_data.user_agent)
        
        doc = {
            "session_id": session_id,
            "username": session_data.username,
            "user_role": session_data.user_role,
            "is_authenticated": session_data.is_authenticated,
            "ip_address": ip_address,
            "user_agent": session_data.user_agent,
            "screen_resolution": session_data.screen_resolution,
            "viewport_size": session_data.viewport_size,
            "color_depth": session_data.color_depth,
            "referrer_url": session_data.referrer_url,
            "entry_page": session_data.entry_page,
            "connection_type": session_data.connection_type,
            "effective_type": session_data.effective_type,
            "cookies_enabled": session_data.cookies_enabled,
            "language": session_data.language,
            "languages": session_data.languages,
            "do_not_track": session_data.do_not_track,
            "session_start": datetime.now(timezone.utc),
            "session_end": None,
            "session_duration": None,
            "exit_page": None,
            "last_activity": datetime.now(timezone.utc),
            "is_active": True,
            **ip_details,
            **device_details,
        }
        
        db[USER_SESSIONS_COLLECTION].insert_one(doc)
        
        return {
            "session_id": session_id,
            "ip_address": ip_address,
            "location": f"{ip_details.get('city', 'Unknown')}, {ip_details.get('country', 'Unknown')}",
            "device": device_details.get("device_type"),
            "browser": f"{device_details.get('browser')} {device_details.get('browser_version')}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@router.post("/session/end")
async def end_session(
    session_end: SessionEnd,
    db=Depends(get_db)
):
    """End a user session and calculate duration"""
    try:
        session = db[USER_SESSIONS_COLLECTION].find_one({"session_id": session_end.session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        now = datetime.now(timezone.utc)
        duration = None
        if session.get("session_start"):
            duration = int((now - session["session_start"]).total_seconds())
        
        db[USER_SESSIONS_COLLECTION].update_one(
            {"_id": session["_id"]},
            {"$set": {
                "session_end": now,
                "session_duration": duration,
                "exit_page": session_end.exit_page,
            }},
        )
        
        return {
            "message": "Session ended successfully",
            "duration_seconds": duration,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")


@router.post("/activity/log")
async def log_activity(
    activity: ActivityCreate,
    db=Depends(get_db)
):
    """Log a user activity"""
    try:
        db[USER_SESSIONS_COLLECTION].update_one(
            {"session_id": activity.session_id},
            {"$set": {"last_activity": datetime.now(timezone.utc)}},
        )
        
        doc = {
            "session_id": activity.session_id,
            "activity_type": activity.activity_type,
            "activity_description": activity.activity_description,
            "page_url": activity.page_url,
            "page_title": activity.page_title,
            "action_category": activity.action_category,
            "action_data": activity.action_data,
            "load_time": activity.load_time,
            "status": activity.status,
            "error_message": activity.error_message,
            "timestamp": datetime.now(timezone.utc),
        }
        
        db[USER_ACTIVITIES_COLLECTION].insert_one(doc)
        
        return {"message": "Activity logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging activity: {str(e)}")


@router.get("/sessions/active")
async def get_active_sessions(
    db=Depends(get_db)
):
    """Get all active sessions (not ended)"""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        sessions = list(
            db[USER_SESSIONS_COLLECTION]
            .find({
                "session_end": None,
                "last_activity": {"$gte": cutoff_time},
            })
            .sort("last_activity", -1)
        )
        
        return {
            "count": len(sessions),
            "sessions": [
                {
                    "session_id": s.get("session_id"),
                    "username": s.get("username"),
                    "ip_address": s.get("ip_address"),
                    "location": f"{s.get('city', 'Unknown')}, {s.get('country', 'Unknown')}",
                    "device": s.get("device_type"),
                    "browser": s.get("browser"),
                    "session_start": s["session_start"].isoformat() if s.get("session_start") else None,
                    "last_activity": s["last_activity"].isoformat() if s.get("last_activity") else None,
                    "idle_seconds": int((datetime.now(timezone.utc) - s["last_activity"]).total_seconds()) if s.get("last_activity") else None,
                }
                for s in sessions
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active sessions: {str(e)}")


@router.get("/sessions/stats")
async def get_session_stats(
    days: int = 7,
    db=Depends(get_db)
):
    """Get session statistics for the last N days"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        base_filter = {"session_start": {"$gte": cutoff_date}}
        
        total_sessions = db[USER_SESSIONS_COLLECTION].count_documents(base_filter)
        
        unique_visitors = len(
            db[USER_SESSIONS_COLLECTION].distinct("ip_address", base_filter)
        )
        
        authenticated = db[USER_SESSIONS_COLLECTION].count_documents(
            {**base_filter, "is_authenticated": True}
        )
        
        # Average session duration
        pipeline = [
            {"$match": {**base_filter, "session_duration": {"$ne": None}}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$session_duration"}}},
        ]
        avg_result = list(db[USER_SESSIONS_COLLECTION].aggregate(pipeline))
        avg_duration = int(avg_result[0]["avg_duration"]) if avg_result else 0
        
        # Device breakdown
        device_pipeline = [
            {"$match": base_filter},
            {"$group": {"_id": "$device_type", "count": {"$sum": 1}}},
        ]
        device_stats = {
            d["_id"]: d["count"]
            for d in db[USER_SESSIONS_COLLECTION].aggregate(device_pipeline)
            if d["_id"]
        }
        
        # Top countries
        country_pipeline = [
            {"$match": base_filter},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        country_stats = [
            {"country": c["_id"], "count": c["count"]}
            for c in db[USER_SESSIONS_COLLECTION].aggregate(country_pipeline)
            if c["_id"]
        ]
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "unique_visitors": unique_visitors,
            "authenticated_sessions": authenticated,
            "avg_duration_seconds": avg_duration,
            "device_breakdown": device_stats,
            "top_countries": country_stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/activities/recent")
async def get_recent_activities(
    limit: int = 50,
    db=Depends(get_db)
):
    """Get recent user activities"""
    try:
        activities = list(
            db[USER_ACTIVITIES_COLLECTION]
            .find()
            .sort("timestamp", -1)
            .limit(limit)
        )
        
        return {
            "count": len(activities),
            "activities": [
                {
                    "id": str(a["_id"]),
                    "session_id": a.get("session_id"),
                    "activity_type": a.get("activity_type"),
                    "description": a.get("activity_description"),
                    "page_url": a.get("page_url"),
                    "status": a.get("status"),
                    "timestamp": a["timestamp"].isoformat() if a.get("timestamp") else None,
                }
                for a in activities
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")
