"""
Secure Authentication Router
Handles login, signup, and session management
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from core.db import get_db
from services.auth_service import AuthService
from models.user_auth import User


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


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    user: Optional[dict] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    department: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    
    token = credentials.credentials
    
    # Verify JWT token
    payload = AuthService.verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify session
    session_token = payload.get("session_token")
    user = AuthService.verify_session(db, session_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    return user


@router.post("/signup", response_model=LoginResponse)
async def signup(
    request: SignupRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Register new user account
    
    **Note:** In production, this should be restricted to admins only!
    For now, anyone can sign up but accounts need admin approval.
    """
    
    # Get client info
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent", "")
    
    # Create user
    user, message = AuthService.create_user(
        db=db,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role="investigator"  # Default role
    )
    
    if not user:
        raise HTTPException(status_code=400, detail=message)
    
    # Update additional fields
    if request.badge_number:
        user.badge_number = request.badge_number
    if request.department:
        user.department = request.department
    if request.designation:
        user.designation = request.designation
    if request.phone_number:
        user.phone_number = request.phone_number
    
    db.commit()
    
    # Log activity
    AuthService.log_activity(
        db=db,
        user_id=user.id,
        username=user.username,
        activity_type="signup",
        activity_description="New user registered",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return LoginResponse(
        success=True,
        message="Account created successfully. Please wait for admin approval.",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    req: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login user and create session
    
    Returns JWT access token for authentication
    """
    
    # Get client info
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent", "")
    
    # Authenticate user
    user, session_token, message = AuthService.authenticate_user(
        db=db,
        username=request.username,
        password=request.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Create JWT token
    access_token = AuthService.create_jwt_token(user, session_token)
    
    # Set cookie (optional, for web apps)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 hour
    )
    
    # Log activity
    AuthService.log_activity(
        db=db,
        user_id=user.id,
        username=user.username,
        activity_type="login",
        activity_description="User logged in",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return LoginResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "badge_number": user.badge_number
        }
    )


@router.post("/logout")
async def logout(
    req: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    
    # Get session token from request
    auth_header = req.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = AuthService.verify_jwt_token(token)
        if payload:
            session_token = payload.get("session_token")
            AuthService.logout(db, session_token)
    
    # Clear cookie
    response.delete_cookie("access_token")
    
    # Log activity
    AuthService.log_activity(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        activity_type="logout",
        activity_description="User logged out",
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", "")
    )
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify if token is valid"""
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }


@router.post("/track-activity")
async def track_activity(
    req: Request,
    activity_type: str,
    activity_description: str,
    page_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track user activity"""
    
    AuthService.log_activity(
        db=db,
        user_id=current_user.id,
        username=current_user.username,
        activity_type=activity_type,
        activity_description=activity_description,
        ip_address=req.client.host,
        user_agent=req.headers.get("user-agent", ""),
        page_url=page_url
    )
    
    return {"success": True, "message": "Activity tracked"}
