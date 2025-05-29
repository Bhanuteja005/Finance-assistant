#!/usr/bin/env python3
"""
Environment validation script for Finance Assistant
Checks if all required API keys and configurations are properly set.
"""

import os
import sys
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from typing import Dict, List, Tuple

def load_environment() -> bool:
    """Load environment variables from .env file."""
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please run setup_env.sh first.")
        return False
    
    load_dotenv()
    print("✅ .env file loaded successfully")
    return True

def validate_gemini_key() -> Tuple[bool, str]:
    """Validate Google Gemini API key."""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        return False, "Gemini API key not found in environment"
    
    try:
        # Test the API key
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available_models = [model.name for model in models]
        return True, f"Gemini API key is valid. Available models: {', '.join(available_models)}"
    except Exception as e:
        return False, f"Gemini API key validation failed: {str(e)}"

def validate_alpha_vantage_key() -> Tuple[bool, str]:
    """Validate Alpha Vantage API key."""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        return False, "Alpha Vantage API key not found in environment"
    
    try:
        # Test the API key with a simple request
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Error Message" in data:
            return False, f"Alpha Vantage API error: {data['Error Message']}"
        elif "Note" in data:
            return False, f"Alpha Vantage API limit reached: {data['Note']}"
        elif "Global Quote" in data:
            return True, "Alpha Vantage API key is valid and working"
        else:
            return False, "Alpha Vantage API returned unexpected response"
            
    except Exception as e:
        return False, f"Alpha Vantage API key validation failed: {str(e)}"

def validate_pinecone_key() -> Tuple[bool, str]:
    """Validate Pinecone API key (optional)."""
    api_key = os.getenv('PINECONE_API_KEY')
    vector_store_type = os.getenv('VECTOR_STORE_TYPE', 'faiss')
    
    if vector_store_type != 'pinecone':
        return True, "Pinecone not configured (using FAISS instead)"
    
    if not api_key:
        return False, "Pinecone API key not found but VECTOR_STORE_TYPE is set to 'pinecone'"
    
    try:
        import pinecone
        pinecone.init(
            api_key=api_key,
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')
        )
        indexes = pinecone.list_indexes()
        return True, f"Pinecone API key is valid. {len(indexes)} indexes available."
    except Exception as e:
        return False, f"Pinecone API key validation failed: {str(e)}"

def validate_ports() -> Tuple[bool, str]:
    """Validate that required ports are available."""
    import socket
    
    ports = {
        'Orchestrator': int(os.getenv('ORCHESTRATOR_PORT', 8000)),
        'API Agent': int(os.getenv('API_AGENT_PORT', 8001)),
        'Retriever Agent': int(os.getenv('RETRIEVER_AGENT_PORT', 8003)),
        'Language Agent': int(os.getenv('LANGUAGE_AGENT_PORT', 8005)),
        'Voice Agent': int(os.getenv('VOICE_AGENT_PORT', 8006)),
        'Streamlit': 8501
    }
    
    unavailable_ports = []
    
    for service, port in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:  # Port is in use
            unavailable_ports.append(f"{service} (port {port})")
    
    if unavailable_ports:
        return False, f"Ports already in use: {', '.join(unavailable_ports)}"
    else:
        return True, "All required ports are available"

def validate_dependencies() -> Tuple[bool, str]:
    """Validate that required Python packages are installed."""
    required_packages = [
        'streamlit', 'fastapi', 'uvicorn', 'google.generativeai', 'langchain', 
        'sentence_transformers', 'faiss-cpu', 'yfinance', 'requests',
        'vosk', 'gtts', 'pandas', 'numpy', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'google.generativeai':
                __import__('google.generativeai')
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        return False, f"Missing packages: {', '.join(missing_packages)}. Run: pip install -r requirements.txt"
    else:
        return True, "All required packages are installed"

def main():
    """Main validation function."""
    print("🔍 Finance Assistant Environment Validation")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    # Run all validations
    validations = [
        ("Dependencies", validate_dependencies),
        ("Gemini API Key", validate_gemini_key),
        ("Alpha Vantage API Key", validate_alpha_vantage_key),
        ("Pinecone API Key", validate_pinecone_key),
        ("Port Availability", validate_ports),
    ]
    
    all_passed = True
    
    for name, validator in validations:
        print(f"\n🔍 Validating {name}...")
        try:
            success, message = validator()
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
                all_passed = False
        except Exception as e:
            print(f"❌ Validation error: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All validations passed! You're ready to start the Finance Assistant.")
        print("\n🚀 Next steps:")
        print("1. Run: ./start_agents.sh")
        print("2. Open: http://localhost:8501")
    else:
        print("⚠️  Some validations failed. Please fix the issues above before starting.")
        print("\n📖 For help, check:")
        print("- README.md for setup instructions")
        print("- .env.example for configuration examples")
        sys.exit(1)

if __name__ == "__main__":
    main()
