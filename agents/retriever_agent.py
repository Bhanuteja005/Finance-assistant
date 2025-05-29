from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from vector_store.embeddings_manager import EmbeddingsManager
from utils.logger import agent_logger
from config import config

app = FastAPI(title="Retriever Agent", description="Handles RAG and document retrieval")

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_type: Optional[str] = None

class DocumentRequest(BaseModel):
    documents: List[Dict[str, Any]]

class RetrieverAgent:
    """Agent responsible for document retrieval and RAG operations."""
    
    def __init__(self):
        self.embeddings_manager = EmbeddingsManager(store_type=config.VECTOR_STORE_TYPE)
        agent_logger.info("Retriever Agent initialized")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store."""
        try:
            success = self.embeddings_manager.add_documents(documents)
            agent_logger.info(f"Added {len(documents)} documents to vector store")
            return success
        except Exception as e:
            agent_logger.error(f"Error adding documents: {e}")
            return False
    
    async def search_documents(self, query: str, top_k: int = 5, filter_type: str = None) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        try:
            results = self.embeddings_manager.search(query, top_k)
            
            # Apply filtering if specified
            if filter_type:
                results = [doc for doc in results if doc.get('type') == filter_type]
            
            # Calculate confidence score
            if results:
                max_score = max(doc.get('similarity_score', 0) for doc in results)
                confidence = max_score if max_score > config.RAG_CONFIDENCE_THRESHOLD else 0
            else:
                confidence = 0
            
            return {
                "results": results,
                "confidence": confidence,
                "query": query,
                "total_found": len(results)
            }
            
        except Exception as e:
            agent_logger.error(f"Error searching documents: {e}")
            return {"results": [], "confidence": 0, "query": query, "total_found": 0}
    
    async def get_context_for_query(self, query: str, context_types: List[str] = None) -> Dict[str, Any]:
        """Get contextual information for a query."""
        try:
            # Search for relevant documents
            search_results = await self.search_documents(query, top_k=10)
            
            # Organize results by type
            context = {
                "market_data": [],
                "earnings": [],
                "filings": [],
                "news": [],
                "general": []
            }
            
            for doc in search_results["results"]:
                doc_type = doc.get('type', 'general')
                if doc_type in context:
                    context[doc_type].append(doc)
                else:
                    context['general'].append(doc)
            
            # Filter by requested context types
            if context_types:
                filtered_context = {k: v for k, v in context.items() if k in context_types}
                context = filtered_context
            
            return {
                "context": context,
                "confidence": search_results["confidence"],
                "total_documents": search_results["total_found"]
            }
            
        except Exception as e:
            agent_logger.error(f"Error getting context: {e}")
            return {"context": {}, "confidence": 0, "total_documents": 0}

# Initialize agent
retriever_agent = RetrieverAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Retriever Agent"}

@app.post("/search")
async def search_documents(request: SearchRequest):
    """Search for documents based on query."""
    try:
        results = await retriever_agent.search_documents(
            request.query, 
            request.top_k, 
            request.filter_type
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-documents")
async def add_documents(request: DocumentRequest):
    """Add documents to the vector store."""
    try:
        success = await retriever_agent.add_documents(request.documents)
        return {"success": success, "documents_added": len(request.documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-context")
async def get_context(request: SearchRequest):
    """Get contextual information for a query."""
    try:
        context_types = request.filter_type.split(",") if request.filter_type else None
        context = await retriever_agent.get_context_for_query(request.query, context_types)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get vector store statistics."""
    try:
        stats = retriever_agent.embeddings_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.RETRIEVER_AGENT_PORT)
