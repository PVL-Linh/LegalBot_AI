"""
Endpoint for grouped chat history (today, yesterday, last week, etc.)
"""
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.db.supabase_client import supabase
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter()

@router.get("/conversations/grouped")
async def get_grouped_conversations(current_user: dict = Depends(get_current_user)):
    """
    Get conversations grouped by time period:
    - Today
    - Yesterday  
    - Last 7 days
    - Older
    """
    if not supabase:
        return {"error": "Database not configured"}
    
    user_id = current_user["id"]
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    
    # Get all user's conversations
    result = supabase.table("conversations")\
        .select("id, title, created_at, updated_at")\
        .eq("user_id", user_id)\
        .order("updated_at", desc=True)\
        .execute()
    
    conversations = result.data if result.data else []
    
    grouped = {
        "today": [],
        "yesterday": [],
        "last_week": [],
        "older": []
    }
    
    for conv in conversations:
        updated_at = datetime.fromisoformat(conv["updated_at"].replace("Z", "+00:00"))
        
        if updated_at >= today_start:
            grouped["today"].append(conv)
        elif updated_at >= yesterday_start:
            grouped["yesterday"].append(conv)
        elif updated_at >= week_start:
            grouped["last_week"].append(conv)
        else:
            grouped["older"].append(conv)
    
    return grouped
