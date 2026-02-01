from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.core.config import settings
from jose import JWTError, jwt
import os

# Security schemes
security = HTTPBearer()

# Security constants from config
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def verify_api_key(x_api_key: str = Header(...)):
    """Verify API Key (for backward compatibility and admin endpoints)"""
    if not settings.API_KEY:
        return True
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

def get_user_from_token(token: str) -> Optional[dict]:
    """
    Helper to extract user info from a JWT token string.
    Useful for WebSockets or other manual verification.
    """
    try:
        # print(f"DEBUG: Decoding token with SECRET_KEY='{SECRET_KEY}' ALGO='{ALGORITHM}'")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id:
            return {"id": user_id, "email": email}
        else:
            print(f"DEBUG: Token decoded but 'sub' claim missing. Payload keys: {list(payload.keys())}")
    except JWTError as e:
        print(f"DEBUG: JWT Decode Error: {e}. Token starts with: {token[:10]}...")
    except Exception as e:
        print(f"DEBUG: General error in get_user_from_token: {e}")
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token and return current user info.
    Use this for protected endpoints that require user authentication.
    """
    token = credentials.credentials
    user = get_user_from_token(token)
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def verify_admin(current_user: dict = Depends(get_current_user)):
    """
    Verify that the current authenticated user has the 'admin' role.
    """
    from app.db.supabase_client import supabase
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        profile = supabase.table("user_profiles")\
            .select("role")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        if not profile.data or profile.data.get("role") != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Not enough permissions. Admin role required."
            )
        
        return current_user
    except Exception as e:
        raise HTTPException(status_code=403, detail="Forbidden")

# Optional auth - for endpoints that work with or without auth
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """Optional authentication - returns user if token provided, None otherwise"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id:
            return {"id": user_id, "email": email}
    except JWTError:
        pass
    
    return None
