from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class MessageBase(BaseModel):
    role: str # 'user' or 'assistant'
    content: str
    metadata: Dict[str, Any] = {}

class MessageCreate(MessageBase):
    conversation_id: UUID

class Message(MessageBase):
    id: int
    conversation_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
