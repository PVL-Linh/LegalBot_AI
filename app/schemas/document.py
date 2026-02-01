from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID

class LegalDocumentBase(BaseModel):
    title: str
    document_number: Optional[str] = None
    category: Optional[str] = None
    issued_date: Optional[date] = None
    effective_date: Optional[date] = None
    status: str = "active"
    content: Optional[str] = None
    summary: Optional[str] = None
    file_url: Optional[str] = None

class LegalDocumentCreate(LegalDocumentBase):
    created_by: UUID

class LegalDocumentUpdate(LegalDocumentBase):
    pass

class LegalDocument(LegalDocumentBase):
    id: int
    pinecone_synced: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True

class DocumentChunk(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    pinecone_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True
