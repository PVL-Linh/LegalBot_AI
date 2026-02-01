from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    try:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

supabase: Optional[Client] = get_supabase()
