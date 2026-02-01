from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.db.supabase_client import supabase
from app.api.deps import get_current_user, verify_api_key
import uuid
import asyncio

router = APIRouter()

class ConversationCreate(BaseModel):
    title: str = "New Conversation"

class ConversationUpdate(BaseModel):
    title: str
    
class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation: ConversationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new conversation"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        print(f"DEBUG: Creating conversation for user {user_id}: '{conversation.title}'")
        
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations").insert({
                "title": conversation.title,
                "user_id": user_id
            }).execute()
        )
        
        print(f"DEBUG: Create result: {result.data if result.data else 'EMPTY'}")
        if result.data:
            conv = result.data[0]
            return ConversationResponse(
                id=conv["id"],
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            )
        raise HTTPException(status_code=500, detail="Failed to create conversation - No data returned")
    except Exception as e:
        print(f"ERROR in create_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(limit: int = 20, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """List all conversations"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        print(f"DEBUG: Listing conversations for user {user_id}")
        
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")\
                .select("*, messages(count)")\
                .eq("user_id", user_id)\
                .order("updated_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
        )
        
        print(f"DEBUG: list_conversations for {user_id} found {len(result.data)} items.")
        if result.data:
            print(f"DEBUG: First item raw data: {result.data[0]}")
        
        conversations = []
        for conv in result.data:
            # messages(count) returns as a list of one dict: [{'count': n}]
            msg_data = conv.get("messages", [])
            count = msg_data[0].get("count", 0) if msg_data else 0
            
            conversations.append(ConversationResponse(
                id=conv["id"],
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                message_count=count
            ))
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific conversation with its messages using joined query and ownership check."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        print(f"DEBUG: Fetching conversation {conversation_id} for user {user_id}")
        
        conv_result = await asyncio.to_thread(
            lambda: supabase.table("conversations")\
                .select("*, messages(*)")\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .order("created_at", foreign_table="messages", desc=False)\
                .execute()
        )
        
        print(f"DEBUG: Fetch result count: {len(conv_result.data) if conv_result.data else 0}")
        
        if not conv_result.data:
            print(f"WARNING: Conversation {conversation_id} not found or access denied for user {user_id}")
            # Check if it exists but belongs to someone else for better error message
            exists_check = await asyncio.to_thread(
                lambda: supabase.table("conversations").select("id").eq("id", conversation_id).execute()
            )
            if exists_check.data:
                raise HTTPException(status_code=403, detail="Access denied to this conversation")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv_data = conv_result.data[0]
        messages = conv_data.get("messages", [])
        
        return {
            "conversation": {k: v for k, v in conv_data.items() if k != "messages"},
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str, 
    update_data: ConversationUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update a conversation title"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")\
                .update({"title": update_data.title})\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .execute()
        )
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")
            
        conv = result.data[0]
        return ConversationResponse(
            id=conv["id"],
            title=conv["title"],
            created_at=conv["created_at"],
            updated_at=conv["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/clear")
async def clear_conversations(current_user: dict = Depends(get_current_user)):
    """Delete all conversations and messages for the current user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        print(f"DEBUG: Clearing all conversations for user {user_id}")
        
        # In Supabase, deleting conversations will Cascade to messages if configured, 
        # but let's be explicit if needed or rely on the query.
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")\
                .delete()\
                .eq("user_id", user_id)\
                .execute()
        )
        
        return {"message": "All conversations cleared successfully", "count": len(result.data) if result.data else 0}
    except Exception as e:
        print(f"ERROR in clear_conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation and all its messages"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        user_id = current_user["id"]
        print(f"DEBUG: Deleting conversation {conversation_id} for user {user_id}")
        result = await asyncio.to_thread(
            lambda: supabase.table("conversations")\
                .delete()\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .execute()
        )
        
        return {"message": "Conversation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
