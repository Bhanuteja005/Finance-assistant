import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import os
from datetime import datetime
import pinecone
from utils.logger import data_logger
from config import config

class EmbeddingsManager:
    """Manages embeddings and vector store operations."""
    
    def __init__(self, store_type: str = "faiss"):
        self.store_type = store_type
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        if store_type == "faiss":
            self.setup_faiss()
        elif store_type == "pinecone":
            self.setup_pinecone()
        
        self.documents = []  # Store document metadata
        
    def setup_faiss(self):
        """Initialize FAISS vector store."""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.index_file = "vector_store/faiss_index.bin"
        self.metadata_file = "vector_store/metadata.pkl"
        
        # Load existing index if available
        if os.path.exists(self.index_file):
            self.load_faiss_index()
    
    def setup_pinecone(self):
        """Initialize Pinecone vector store."""
        if config.PINECONE_API_KEY:
            pinecone.init(
                api_key=config.PINECONE_API_KEY,
                environment=config.PINECONE_ENVIRONMENT
            )
            
            # Create index if it doesn't exist
            if config.PINECONE_INDEX_NAME not in pinecone.list_indexes():
                pinecone.create_index(
                    config.PINECONE_INDEX_NAME,
                    dimension=self.dimension,
                    metric="cosine"
                )
            
            self.index = pinecone.Index(config.PINECONE_INDEX_NAME)
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts."""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            # Normalize for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            return embeddings
        except Exception as e:
            data_logger.error(f"Error creating embeddings: {e}")
            return np.array([])
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store."""
        try:
            texts = [doc.get('content', '') for doc in documents]
            embeddings = self.create_embeddings(texts)
            
            if len(embeddings) == 0:
                return False
            
            if self.store_type == "faiss":
                return self._add_to_faiss(embeddings, documents)
            elif self.store_type == "pinecone":
                return self._add_to_pinecone(embeddings, documents)
            
            return False
            
        except Exception as e:
            data_logger.error(f"Error adding documents: {e}")
            return False
    
    def _add_to_faiss(self, embeddings: np.ndarray, documents: List[Dict[str, Any]]) -> bool:
        """Add embeddings to FAISS index."""
        try:
            # Add embeddings to index
            self.index.add(embeddings.astype('float32'))
            
            # Store document metadata
            start_id = len(self.documents)
            for i, doc in enumerate(documents):
                doc['id'] = start_id + i
                doc['added_at'] = datetime.now().isoformat()
                self.documents.append(doc)
            
            # Save index and metadata
            self.save_faiss_index()
            return True
            
        except Exception as e:
            data_logger.error(f"Error adding to FAISS: {e}")
            return False
    
    def _add_to_pinecone(self, embeddings: np.ndarray, documents: List[Dict[str, Any]]) -> bool:
        """Add embeddings to Pinecone index."""
        try:
            vectors = []
            for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
                vector_id = f"{doc.get('ticker', 'unknown')}_{datetime.now().timestamp()}_{i}"
                vectors.append({
                    "id": vector_id,
                    "values": embedding.tolist(),
                    "metadata": {
                        "content": doc.get('content', ''),
                        "ticker": doc.get('ticker', ''),
                        "type": doc.get('type', ''),
                        "timestamp": datetime.now().isoformat()
                    }
                })
            
            self.index.upsert(vectors)
            return True
            
        except Exception as e:
            data_logger.error(f"Error adding to Pinecone: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            query_embedding = self.create_embeddings([query])
            if len(query_embedding) == 0:
                return []
            
            if self.store_type == "faiss":
                return self._search_faiss(query_embedding[0], top_k)
            elif self.store_type == "pinecone":
                return self._search_pinecone(query_embedding[0], top_k)
            
            return []
            
        except Exception as e:
            data_logger.error(f"Error searching: {e}")
            return []
    
    def _search_faiss(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search FAISS index."""
        try:
            if self.index.ntotal == 0:
                return []
            
            scores, indices = self.index.search(
                query_embedding.reshape(1, -1).astype('float32'), 
                min(top_k, self.index.ntotal)
            )
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['similarity_score'] = float(score)
                    results.append(doc)
            
            return results
            
        except Exception as e:
            data_logger.error(f"Error searching FAISS: {e}")
            return []
    
    def _search_pinecone(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search Pinecone index."""
        try:
            response = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            results = []
            for match in response['matches']:
                result = {
                    'id': match['id'],
                    'similarity_score': match['score'],
                    **match['metadata']
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            data_logger.error(f"Error searching Pinecone: {e}")
            return []
    
    def save_faiss_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            os.makedirs("vector_store", exist_ok=True)
            faiss.write_index(self.index, self.index_file)
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.documents, f)
                
        except Exception as e:
            data_logger.error(f"Error saving FAISS index: {e}")
    
    def load_faiss_index(self):
        """Load FAISS index and metadata from disk."""
        try:
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'rb') as f:
                    self.documents = pickle.load(f)
                    
        except Exception as e:
            data_logger.error(f"Error loading FAISS index: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if self.store_type == "faiss":
            return {
                "total_documents": len(self.documents),
                "index_size": self.index.ntotal,
                "dimension": self.dimension,
                "store_type": self.store_type
            }
        elif self.store_type == "pinecone":
            stats = self.index.describe_index_stats()
            return {
                "total_documents": stats.get('total_vector_count', 0),
                "dimension": self.dimension,
                "store_type": self.store_type
            }
