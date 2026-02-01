from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class UserProfileBase(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "user"
    metadata: Dict[str, Any] = {}

class UserProfileCreate(UserProfileBase):
    id: UUID

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
