from app.core.resources import resources

# Reuse the centralized index from resources
pinecone_index = resources.get_index()
