import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class Config:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    
    # Database Configuration
    VECTOR_STORE_TYPE: str = os.getenv("VECTOR_STORE_TYPE", "faiss")  # faiss or pinecone
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "finance-assistant")
    
    # Agent Configuration
    API_AGENT_PORT: int = int(os.getenv("API_AGENT_PORT", "8001"))
    SCRAPING_AGENT_PORT: int = int(os.getenv("SCRAPING_AGENT_PORT", "8002"))
    RETRIEVER_AGENT_PORT: int = int(os.getenv("RETRIEVER_AGENT_PORT", "8003"))
    ANALYSIS_AGENT_PORT: int = int(os.getenv("ANALYSIS_AGENT_PORT", "8004"))
    LANGUAGE_AGENT_PORT: int = int(os.getenv("LANGUAGE_AGENT_PORT", "8005"))
    VOICE_AGENT_PORT: int = int(os.getenv("VOICE_AGENT_PORT", "8006"))
    ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "8000"))
    
    # Model Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-pro")  # Changed to Gemini model
    VOSK_MODEL: str = os.getenv("VOSK_MODEL", "small")  # Vosk model for STT
    
    # Application Settings
    RAG_CONFIDENCE_THRESHOLD: float = float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    
    # Data Sources
    MARKET_DATA_REFRESH_INTERVAL: int = int(os.getenv("MARKET_DATA_REFRESH_INTERVAL", "300"))  # 5 minutes
    FILING_SCRAPE_INTERVAL: int = int(os.getenv("FILING_SCRAPE_INTERVAL", "3600"))  # 1 hour

config = Config()
