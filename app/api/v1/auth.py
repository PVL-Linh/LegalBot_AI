"""
Authentication endpoints using Supabase Auth + user_profiles
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.supabase_client import supabase
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt  # Dùng trực tiếp bcrypt
import os
import uuid
import sys

router = APIRouter()

from app.core.config import settings
from app.api.deps import get_current_user

# JWT Configuration (Use centralized settings)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    created_at: datetime

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def my_custom_hash(password: str) -> str:
    """Hash password using bcrypt"""
    print(f"DEBUG CUSTOM HASH: processing password of len {len(password)}")
    # Truncate to 72 bytes (bcrypt limit)
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        print("DEBUG CUSTOM HASH: truncating password")
        pwd_bytes = pwd_bytes[:72]
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')  # Store as string

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    if not hashed_password:
        return False
    
    # Truncate plain password just like in hash
    pwd_bytes = plain_password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
        
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Verify error: {e}")
        return False

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user - Pure bypass mode"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Validate password length
        if len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")
            
        # Kiểm tra email đã tồn tại chưa
        existing = supabase.table("user_profiles").select("*").eq("email", user_data.email).execute()
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail="Email đã được đăng ký")
        
        # Bypass mode - user_profiles only
        user_id = str(uuid.uuid4())
        
        # Hash password direct with bcrypt
        hashed_password_str = my_custom_hash(user_data.password)
        
        # Determine role based on email prefix (for testing purposes)
        role = "admin" if user_data.email.startswith("admin_") else "user"
        
        # Create user profile
        profile_data = {
            "id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password_str,
            "full_name": user_data.full_name or user_data.email.split('@')[0],
            "role": role,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("user_profiles").insert(profile_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Không thể tạo user")
        
        # Create access token
        access_token = create_access_token({
            "sub": user_id, 
            "email": user_data.email
        })
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "bypass_mode": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Register error: {e}")
        # THAY ĐỔI ERROR MESSAGE ĐỂ CHỨNG MINH CODE MỚI
        raise HTTPException(status_code=400, detail=f"Lỗi đăng ký (Code Mới): {str(e)}")

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user - Using native bcrypt verification"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # 1. Thử Supabase Auth - NẾU CẦN (hiện tại bypass mode là chính)
        auth_user = None
        # Uncomment block dưới nếu muốn dùng Supabase Auth song song
        # try:
        #     response = supabase.auth.sign_in_with_password({...})
        #     if response.user: auth_user = response.user
        # except: pass
        
        user_id = None
        profile_data = None
        
        if auth_user:
            user_id = auth_user.id
            # Fetch profile...
        
        # 2. Bypass Check (Native Bcrypt)
        if not user_id:
            profile = supabase.table("user_profiles").select("*").eq("email", credentials.email).execute()
            
            if not profile.data or len(profile.data) == 0:
                raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
            
            profile_data = profile.data[0]
            
            # Verify using native bcrypt
            if not verify_password(credentials.password, profile_data.get("password_hash")):
                raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
                
            user_id = profile_data["id"]

        # Final check
        if not profile_data and user_id:
             profile = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
             profile_data = profile.data[0] if profile.data else {}

        # Token
        access_token = create_access_token({
            "sub": user_id, 
            "email": credentials.email
        })
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user_id,
                "email": credentials.email,
                "full_name": profile_data.get("full_name"),
                "role": profile_data.get("role", "user"),
                "bypass_mode": True
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(lambda: {"id": "test"})):
    # Placeholder for simple dependency
    # Production should implement get_current_user dependency properly
    raise HTTPException(status_code=501, detail="Not implemented completely")

@router.post("/logout")
async def logout():
    return {"message": "Logged out"}
