"""
Service for processing PDF documents: extraction, chunking, and embedding.
"""
import os
from typing import List, Dict, Any
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.resources import resources
from app.db.supabase_client import supabase


class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    @property
    def embeddings_model(self):
        return resources.embeddings

    @property
    def index(self):
        return resources.get_index()

    async def process_and_ingest(self, file_path: str, document_id: int):
        """
        Extract text from PDF, chunk it, and upsert to Pinecone.
        """
        # 1. Extract text
        reader = PdfReader(file_path)
        all_text = ""
        for i, page in enumerate(reader.pages):
            all_text += page.extract_text() + "\n"
        
        # 2. Chunk text
        chunks = self.text_splitter.split_text(all_text)
        
        # 3. Generate Embeddings & Upsert to Pinecone
        batch_size = 100
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch_texts = chunks[i:i + batch_size]
            batch_embeddings = self.embeddings_model.embed_documents(batch_texts)
            
            batch_vectors = []
            for j, embedding in enumerate(batch_embeddings):
                # Unique ID: document_id_chunk_idx
                vector_id = f"doc_{document_id}_{i+j}"
                
                metadata = {
                    "text": batch_texts[j],
                    "document_id": document_id,
                    "source": os.path.basename(file_path)
                }
                
                batch_vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            self.index.upsert(vectors=batch_vectors)
        
        # 4. Update Supabase status
        if supabase:
            supabase.table("legal_documents").update({
                "pinecone_synced": True,
                "status": "active"
            }).eq("id", document_id).execute()
            
            # Save chunks metadata to supabase for faster retrieval if needed
            chunk_data = [
                {
                    "document_id": document_id,
                    "content": text,
                    "chunk_index": i
                }
                for i, text in enumerate(chunks)
            ]
            # Use small batches for supabase as well
            for k in range(0, len(chunk_data), 500):
                supabase.table("document_chunks").insert(chunk_data[k:k+500]).execute()

        return total_chunks

pdf_processor = PDFProcessor()
