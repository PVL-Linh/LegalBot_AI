from langchain_core.tools import tool
from app.core.resources import resources

@tool
def lookup_legal_docs(query: str):
    """
    Search for legal documents, laws, and regulations based on a query.
    Use this tool when the user asks about laws, penalties, or legal procedures.
    """
    import time
    start_time = time.time()
    try:
        # 1. Get Singleton Resources (Fast)
        embeddings_model = resources.embeddings
        index = resources.get_index()
        
        if not index:
            return "Error: Pinecone is not configured correctly."
            
        # 2. Embed Query (Using cached model)
        print(f"DEBUG Tool: Embedding query: '{query}'")
        embed_start = time.time()
        query_vector = embeddings_model.embed_query(query)
        print(f"DEBUG Tool: Embedding took {time.time() - embed_start:.2f}s")
        
        # 3. Query Pinecone (V3 Syntax) - Increased top_k for better accuracy
        search_start = time.time()
        results = index.query(
            vector=query_vector,
            top_k=5,
            include_metadata=True
        )
        print(f"DEBUG Tool: Pinecone search took {time.time() - search_start:.2f}s")
        
        # 4. Format Results
        if not results or not results.get('matches'):
            return "Không tìm thấy văn bản pháp luật liên quan trực tiếp."
            
        formatted_docs = []
        for match in results['matches']:
            metadata = match.get('metadata', {})
            text = metadata.get('text', '')
            # Truncate text to avoid token limits (1000-1500 chars per doc is usually enough)
            if len(text) > 1500:
                text = text[:1500] + "... (đã cắt bớt)"
            
            source = metadata.get('source', 'Không rõ')
            score = match.get('score', 0)
            # Include confidence score to help AI prioritize
            formatted_docs.append(f"NGUỒN: {source} (Độ tin cậy: {score:.2f})\nNỘI DUNG: {text}")
            
        print(f"DEBUG Tool: lookup_legal_docs Total time: {time.time() - start_time:.2f}s")
        return "\n\n".join(formatted_docs)
        
    except Exception as e:
        print(f"ERROR in lookup_legal_docs: {e}")
        return f"Error searching documents: {str(e)}"
