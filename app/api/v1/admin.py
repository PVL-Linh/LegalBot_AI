from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import date, datetime
from app.db.supabase_client import supabase
from app.api.deps import verify_admin
from app.services.pdf_processor import pdf_processor
import os
import shutil
from pathlib import Path

router = APIRouter()

class DocumentResponse(BaseModel):
    id: Union[int, str]
    title: str
    document_number: Optional[str]
    category: Optional[str]
    status: str
    issued_date: Optional[date]
    effective_date: Optional[date]
    created_at: datetime
    created_by: Optional[str]
    pinecone_synced: bool

class DocumentCreate(BaseModel):
    title: str
    document_number: Optional[str] = None
    category: Optional[str] = None
    issued_date: Optional[date] = None
    effective_date: Optional[date] = None
    content: Optional[str] = None
    summary: Optional[str] = None

@router.get("/admin/stats", dependencies=[Depends(verify_admin)])
async def get_admin_stats():
    """Get system statistics for dashboard"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get counts using exact count
        users = supabase.table("user_profiles").select("id", count="exact").execute()
        convs = supabase.table("conversations").select("id", count="exact").execute()
        docs = supabase.table("legal_documents").select("id", count="exact").execute()
        
        return {
            "users": users.count if users.count is not None else 0,
            "conversations": convs.count if convs.count is not None else 0,
            "documents": docs.count if docs.count is not None else 0,
            "system_health": "online"
        }
    except Exception as e:
        print(f"ERROR in get_admin_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/analytics", dependencies=[Depends(verify_admin)])
async def get_admin_analytics():
    """Get top topics and user activity insights"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get category distribution
        cat_result = supabase.table("legal_documents")\
            .select("category")\
            .execute()
        
        from collections import Counter
        categories = [d["category"] for d in cat_result.data if d.get("category")]
        counts = Counter(categories)
        
        return [
            {"topic": cat, "count": count} 
            for cat, count in counts.most_common(5)
        ]
    except Exception:
        return []

@router.post("/admin/documents", response_model=DocumentResponse, dependencies=[Depends(verify_admin)])
async def create_document(document: DocumentCreate, current_user: dict = Depends(verify_admin)):
    """Create a new legal document record"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        
        result = supabase.table("legal_documents").insert({
            "title": document.title,
            "document_number": document.document_number,
            "category": document.category,
            "issued_date": str(document.issued_date) if document.issued_date else None,
            "effective_date": str(document.effective_date) if document.effective_date else None,
            "content": document.content,
            "summary": document.summary,
            "created_by": user_id,
            "status": "active",
            "pinecone_synced": False
        }).execute()
        
        if result.data:
            return DocumentResponse(**result.data[0])
        raise HTTPException(status_code=500, detail="Failed to create document")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/documents/upload", dependencies=[Depends(verify_admin)])
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    category: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_admin)
):
    """Upload a PDF, save record, and process in background"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # 1. Create document record
    user_id = current_user["id"]
    try:
        result = supabase.table("legal_documents").insert({
            "title": title,
            "category": category,
            "created_by": user_id,
            "status": "processing",
            "pinecone_synced": False
        }).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create record")
        
        document_id = result.data[0]["id"]
        
        # 2. Save file temporarily
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / f"{document_id}_{file.filename}"
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Trigger background processing
        background_tasks.add_task(
            process_file_and_cleanup, 
            str(file_path), 
            document_id
        )
        
        return {
            "message": "File uploaded and processing started",
            "document_id": document_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_and_cleanup(file_path: str, document_id: int):
    """Background task to process PDF and delete temp file"""
    try:
        await pdf_processor.process_and_ingest(file_path, document_id)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/admin/documents", response_model=List[DocumentResponse], dependencies=[Depends(verify_admin)])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """List all legal documents"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        query = supabase.table("legal_documents").select("*")
        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return [DocumentResponse(**doc) for doc in result.data]
    except Exception as e:
        import traceback
        print(f"ERROR in list_documents: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/documents/{document_id}", dependencies=[Depends(verify_admin)])
async def get_document(document_id: int):
    """Get a specific document with full content"""
    # Logic remains same but with verify_admin
    result = supabase.table("legal_documents").select("*").eq("id", document_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")
    return result.data[0]

@router.delete("/admin/documents/{document_id}", dependencies=[Depends(verify_admin)])
async def delete_document(document_id: int):
    """Delete a document"""
    supabase.table("legal_documents").delete().eq("id", document_id).execute()
    return {"message": "Document deleted successfully"}
