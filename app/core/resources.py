"""
Centralized heavy resources like embedding models and database clients.
Implements the Singleton pattern with granular locks to prevent deadlocks.
"""
import os
from threading import Lock
from pinecone import Pinecone
from app.core.config import settings

class Resources:
    def __init__(self):
        self._embeddings = None
        self._pinecone_client = None
        self._pinecone_index = None
        self._fast_llm = None
        
        # Granular locks to prevent one slow resource from blocking others
        self._emb_lock = Lock()
        self._pc_lock = Lock()
        self._idx_lock = Lock()
        self._llm_lock = Lock()

    @property
    def embeddings(self):
        if self._embeddings is None:
            print("DEBUG Resources: Waiting for embeddings lock...")
            with self._emb_lock:
                if self._embeddings is not None:
                    return self._embeddings
                
                from langchain_huggingface import HuggingFaceEmbeddings
                model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                print(f"DEBUG Resources: Starting to load embeddings '{model_name}' (this takes 10-15s)...")
                try:
                    self._embeddings = HuggingFaceEmbeddings(model_name=model_name)
                    print("DEBUG Resources: Embeddings loaded successfully.")
                except Exception as e:
                    print(f"ERROR Resources: Failed to load embeddings: {e}")
                    raise e
        return self._embeddings

    @property
    def pc(self):
        if self._pinecone_client is None:
            with self._pc_lock:
                if self._pinecone_client is not None:
                    return self._pinecone_client
                    
                api_key = settings.PINECONE_API_KEY
                if not api_key:
                    print("ERROR Resources: PINECONE_API_KEY is missing.")
                    return None
                print("DEBUG Resources: Initializing Pinecone client...")
                try:
                    self._pinecone_client = Pinecone(api_key=api_key)
                    print("DEBUG Resources: Pinecone client initialized.")
                except Exception as e:
                    print(f"ERROR Resources: Failed to init Pinecone client: {e}")
                    raise e
        return self._pinecone_client

    def get_index(self, index_name=None):
        if index_name is None:
            index_name = settings.PINECONE_INDEX_NAME or "chatall-chatbot"
            
        if self._pinecone_index is None:
            with self._idx_lock:
                if self._pinecone_index is not None:
                    return self._pinecone_index
                    
                client = self.pc
                if client:
                    print(f"DEBUG Resources: Connecting to index '{index_name}'...")
                    try:
                        self._pinecone_index = client.Index(index_name)
                        print(f"DEBUG Resources: Connected to index '{index_name}'.")
                    except Exception as e:
                        print(f"ERROR Resources: Failed to connect to index '{index_name}': {e}")
                        raise e
        return self._pinecone_index

    @property
    def fast_llm(self):
        if self._fast_llm is None:
            print("DEBUG Resources: Waiting for Fast LLM lock...")
            with self._llm_lock:
                if self._fast_llm is not None:
                    return self._fast_llm
                
                from langchain_groq import ChatGroq
                print("DEBUG Resources: Initializing Fast LLM (Groq) for tools...")
                try:
                    self._fast_llm = ChatGroq(
                        model="llama-3.3-70b-versatile",
                        temperature=0,
                        groq_api_key=os.getenv("GROQ_API_KEY")
                    )
                    print("DEBUG Resources: Fast LLM initialized.")
                except Exception as e:
                    print(f"ERROR Resources: Failed to init Fast LLM: {e}")
                    return None
        return self._fast_llm

# Global singleton instance
resources = Resources()
