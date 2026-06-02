"""
Secure Authentication Router
Handles login, signup, and session management
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone

from core.db import get_db
from services.auth_service import AuthService
from models.user_auth import USERS_COLLECTION, USER_SESSIONS_COLLECTION
from utils.rate_limiter import login_limiter, check_rate_limit


router = APIRouter()
security = HTTPBearer()


# Pydantic models
class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = "Delhi Police Cyber Cell"
    designation: Optional[str] = None
    phone_number: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: Optional[dict] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    
    payload = AuthService.verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    session_token = payload.get("session_token")
    user = AuthService.verify_session(db, session_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )

    return user


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow only admin users through. Use as a dependency on admin routes."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.post("/signup", response_model=LoginResponse)
async def signup(
    request: SignupRequest,
    req: Request,
    db=Depends(get_db)
):
    """Register new user account"""
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent", "")
    
    user, message = AuthService.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role="investigator",
    )
    
    if not user:
        raise HTTPException(status_code=400, detail=message)
    
    # Update additional fields
    extra_fields = {}
    if request.badge_number:
        extra_fields["badge_number"] = request.badge_number
    if request.department:
        extra_fields["department"] = request.department
    if request.designation:
        extra_fields["designation"] = request.designation
    if request.phone_number:
        extra_fields["phone_number"] = request.phone_number
    if extra_fields:
        db[USERS_COLLECTION].update_one({"_id": user["_id"]}, {"$set": extra_fields})
        user.update(extra_fields)
    
    AuthService.log_activity(
        db=db,
        user_id=str(user["_id"]),
        username=user["username"],
        activity_type="signup",
        activity_description="New user registered",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return LoginResponse(
        success=True,
        message="Account created successfully. Please wait for admin approval.",
        user={
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "investigator"),
        },
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    req: Request,
    response: Response,
    db=Depends(get_db)
):
    """Login user and create session"""
    await check_rate_limit(req, login_limiter, identifier_key="ip")
    
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent", "")
    
    user, session_token, message = AuthService.authenticate_user(
        db=db,
        username=request.username,
        password=request.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    
    access_token = AuthService.create_jwt_token(user, session_token)
    refresh_token = AuthService.create_refresh_token(user, session_token)
    
    if request.remember_me:
        db[USER_SESSIONS_COLLECTION].update_one(
            {"session_token": session_token},
            {"$set": {
                "expires_at": datetime.now(timezone.utc) + timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS),
            }},
        )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax",
        max_age=3600,
    )
    
    AuthService.log_activity(
        db=db,
        user_id=str(user["_id"]),
        username=user["username"],
        activity_type="login",
        activity_description="User logged in",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return LoginResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "investigator"),
            "department": user.get("department"),
            "badge_number": user.get("badge_number"),
        },
    )


@router.post("/logout")
async def logout(
    req: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Logout user and invalidate session"""
    auth_header = req.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = AuthService.verify_jwt_token(token)
        if payload:
            session_token = payload.get("session_token")
            AuthService.logout(db, session_token)
    
    response.delete_cookie("access_token")
    
    AuthService.log_activity(
        db=db,
        user_id=str(current_user["_id"]),
        username=current_user["username"],
        activity_type="logout",
        activity_description="User logged out",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", ""),
    )
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user.get("role", "investigator"),
        department=current_user.get("department"),
        is_active=current_user.get("is_active", True),
        created_at=current_user.get("created_at"),
        last_login=current_user.get("last_login"),
    )


@router.get("/verify")
async def verify_token(
    current_user: dict = Depends(get_current_user)
):
    """Verify if token is valid"""
    return {
        "valid": True,
        "user_id": str(current_user["_id"]),
        "username": current_user["username"],
        "role": current_user.get("role", "investigator"),
    }


@router.get("/admin/users")
async def admin_list_users(
    user_status: Optional[str] = None,
    admin: dict = Depends(get_current_admin),
    db=Depends(get_db),
):
    """List users for admin management. Query ?user_status=pending|approved to filter."""
    users = AuthService.list_users(db, status=user_status)
    return {"success": True, "users": users, "count": len(users)}


@router.post("/admin/users/{user_id}/approve")
async def admin_approve_user(
    user_id: str,
    req: Request,
    admin: dict = Depends(get_current_admin),
    db=Depends(get_db),
):
    """Approve a pending user so they can log in."""
    ok, message = AuthService.approve_user(db, user_id, str(admin["_id"]))
    if not ok:
        raise HTTPException(status_code=404, detail=message)

    AuthService.log_activity(
        db=db,
        user_id=str(admin["_id"]),
        username=admin["username"],
        activity_type="approve_user",
        activity_description=f"Approved user {user_id}",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", ""),
    )
    return {"success": True, "message": message}


@router.post("/admin/users/{user_id}/reject")
async def admin_reject_user(
    user_id: str,
    req: Request,
    admin: dict = Depends(get_current_admin),
    db=Depends(get_db),
):
    """Reject and remove a pending user account."""
    ok, message = AuthService.reject_user(db, user_id)
    if not ok:
        raise HTTPException(status_code=400, detail=message)

    AuthService.log_activity(
        db=db,
        user_id=str(admin["_id"]),
        username=admin["username"],
        activity_type="reject_user",
        activity_description=f"Rejected user {user_id}",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", ""),
    )
    return {"success": True, "message": message}


@router.post("/refresh-token")
async def refresh_token(
    request: RefreshTokenRequest,
    db=Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = AuthService.verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    from bson import ObjectId
    try:
        uid = ObjectId(payload["user_id"])
    except Exception:
        uid = payload["user_id"]
    
    user = db[USERS_COLLECTION].find_one({"_id": uid})
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    session_token = payload["session_token"]
    
    session_row = db[USER_SESSIONS_COLLECTION].find_one({"session_token": session_token})
    if not session_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found — please log in again",
        )
    
    now = datetime.now(timezone.utc)
    db[USER_SESSIONS_COLLECTION].update_one(
        {"_id": session_row["_id"]},
        {"$set": {
            "is_active": True,
            "last_activity": now,
            "expires_at": now + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
        }},
    )
    
    new_access_token = AuthService.create_jwt_token(user, session_token)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    req: Request,
    db=Depends(get_db)
):
    """Request password reset token"""
    user = db[USERS_COLLECTION].find_one({"email": request.email})
    
    if not user:
        return {
            "success": True,
            "message": "If account exists, password reset link will be sent to email",
        }
    
    reset_token = AuthService.create_password_reset_token(
        db=db,
        email=request.email,
        user_id=str(user["_id"]),
        request_ip=req.client.host,
    )
    
    if os.getenv("ENVIRONMENT") == "development":
        return {
            "success": True,
            "message": "Password reset token created",
            "token": reset_token,
        }
    
    return {
        "success": True,
        "message": "If account exists, password reset link will be sent to email",
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db=Depends(get_db)
):
    """Reset password using reset token"""
    success, message = AuthService.reset_password(
        db=db,
        reset_token=request.token,
        new_password=request.new_password,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": "Password reset successfully. You can now login with your new password.",
    }


@router.post("/track-activity")
async def track_activity(
    req: Request,
    activity_type: str,
    activity_description: str,
    page_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    """Track user activity"""
    AuthService.log_activity(
        db=db,
        user_id=str(current_user["_id"]),
        username=current_user["username"],
        activity_type=activity_type,
        activity_description=activity_description,
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", ""),
        page_url=page_url,
    )
    
    return {"success": True, "message": "Activity tracked"}
