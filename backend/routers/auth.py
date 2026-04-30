from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.security import create_access_token
from core.config import JWT_SECRET

router = APIRouter()

# Fake user database for demo purposes
fake_users = {
    "inspector": "secure@123",
    "analyst": "an@123"
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(credentials: LoginRequest):
    """Officer login & JWT authentication"""
    if credentials.username in fake_users and fake_users[credentials.username] == credentials.password:
        token = create_access_token({"user": credentials.username})
        return {"token": token, "user": credentials.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")
