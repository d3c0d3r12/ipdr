from jose import jwt
from core.config import JWT_SECRET

def create_access_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm='HS256')

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.JWTError:
        return None
