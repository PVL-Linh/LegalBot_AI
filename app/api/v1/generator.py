from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from app.api.deps import get_current_user
from app.services.generator import doc_generator

router = APIRouter()

@router.post("/generator/preview")
async def preview_document(
    doc_type: str = Body(..., embed=True),
    data: Dict[str, Any] = Body(...)
):
    """
    Returns a high-quality text-based preview of the document.
    """
    try:
        preview = doc_generator.generate_preview(doc_type, data)
        return {"preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generator/download")
async def download_document(
    doc_type: str = Body(..., embed=True),
    data: Dict[str, Any] = Body(...)
):
    """
    Generates and returns a .docx file for download.
    """
    try:
        file_stream = doc_generator.generate_docx(doc_type, data)
        headers = {
            'Content-Disposition': f'attachment; filename="{doc_type}.docx"'
        }
        return StreamingResponse(
            file_stream, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generator/ai-refine")
async def ai_refine_content(
    field_name: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    doc_type: str = Body(..., embed=True)
):
    """
    Refines rough content into professional legal text using AI.
    """
    try:
        refined_text = await doc_generator.refine_content(field_name, content, doc_type)
        return {"refined_text": refined_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
