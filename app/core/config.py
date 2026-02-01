from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "LegalBot AI"
    DEBUG: bool = True
    
    # Groq
    GROQ_API_KEY: str = ""
    
    # Google Gemini
    GOOGLE_API_KEY: str = ""
    
    # Database
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = "5432"
    DB_NAME: str = "postgres"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # Add this for backend tasks that bypass RLS
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "legalbot-index"
    
    # Redis
    REDIS_URL: str = ""
    
    # Security
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY: str = ""

    class Config:
        env_file = ".env"

import os
print(f"DEBUG: Loading config from {os.getcwd()}...")
import dotenv
dotenv.load_dotenv() # Force load current dir .env
settings = Settings()
print(f"DEBUG: Config Loaded. SECRET_KEY: '{settings.SECRET_KEY[:4]}...' (len: {len(settings.SECRET_KEY)})")
print(f"DEBUG: SUPABASE_URL: {settings.SUPABASE_URL[:20]}...")
