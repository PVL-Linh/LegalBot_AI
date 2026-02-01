from dotenv import load_dotenv
import os

# Load .env from backend directory (parent of app)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from fastapi import FastAPI
from app.core.config import settings

from app.api.v1 import chat, conversations, admin, auth, history, generator

from contextlib import asynccontextmanager
import asyncio
from app.core.resources import resources

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Function to load resources in background
    def pre_load():
        print("🚀 [BACKGROUND] Loading Index...")
        try:
            resources.get_index()
            print("🚀 [BACKGROUND] Loading Embeddings (GPU/CPU heavy)...")
            _ = resources.embeddings
            print("✅ [BACKGROUND] All heavy resources are warm and ready.")
        except Exception as e:
            print(f"❌ [BACKGROUND] Error loading resources: {e}")

    # Launch in a separate thread to ensure zero impact on event loop
    import threading
    threading.Thread(target=pre_load, daemon=True).start()
    
    print("✨ [LIFESPAN] Server starting... (Resources loading in background)")
    yield
    # Shutdown logic (if any) here

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for development specific ports
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])
app.include_router(generator.router, prefix="/api/v1", tags=["generator"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "Welcome to LegalBot AI API"}

@app.get("/health")
async def health_check():
    """Comprehensive health check for all services"""
    from app.db.supabase_client import supabase
    from app.db.pinecone_client import pinecone_index
    import os
    
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check Supabase (just check if client exists, don't query with RLS)
    try:
        if supabase:
            health_status["services"]["supabase"] = {
                "status": "connected",
                "url": settings.SUPABASE_URL[:30] + "..." if settings.SUPABASE_URL else None
            }
        else:
            health_status["services"]["supabase"] = {"status": "not_configured"}
    except Exception as e:
        health_status["services"]["supabase"] = {"status": "error", "message": str(e)[:50]}
        health_status["status"] = "degraded"
    
    # Check Pinecone
    try:
        if pinecone_index:
            stats = pinecone_index.describe_index_stats()
            health_status["services"]["pinecone"] = {
                "status": "connected",
                "vector_count": stats.get("total_vector_count", 0)
            }
        else:
            health_status["services"]["pinecone"] = {"status": "not_configured"}
    except Exception as e:
        health_status["services"]["pinecone"] = {"status": "error", "message": str(e)[:50]}
        health_status["status"] = "degraded"
    
    # Check Groq API Key
    health_status["services"]["groq"] = {
        "status": "configured" if os.getenv("GROQ_API_KEY") else "not_configured"
    }
    
    # Check API Key
    health_status["services"]["api_security"] = {
        "status": "enabled" if settings.API_KEY else "disabled"
    }
    
    return health_status
