from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ConversationBase(BaseModel):
    title: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ConversationCreate(ConversationBase):
    user_id: UUID

class ConversationUpdate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
