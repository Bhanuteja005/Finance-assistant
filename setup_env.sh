#!/bin/bash

echo "🔧 Setting up Finance Assistant Environment"
echo "=========================================="

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Creating backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Copy example file
cp .env.example .env

echo ""
echo "📝 .env file created from template."
echo ""
echo "🔑 Please add your API keys to the .env file:"
echo ""
echo "1. Google Gemini API Key (REQUIRED):"
echo "   - Visit: https://aistudio.google.com/app/apikey"
echo "   - Create a new API key"
echo "   - Add it to GEMINI_API_KEY in .env"
echo ""
echo "2. Alpha Vantage API Key (REQUIRED):"
echo "   - Visit: https://www.alphavantage.co/support/#api-key"
echo "   - Sign up for a free account"
echo "   - Get your API key"
echo "   - Add it to ALPHA_VANTAGE_API_KEY in .env"
echo ""
echo "3. Pinecone API Key (OPTIONAL):"
echo "   - Visit: https://app.pinecone.io/"
echo "   - Sign up and get your API key"
echo "   - Add it to PINECONE_API_KEY in .env"
echo "   - Or leave VECTOR_STORE_TYPE=faiss for local storage"
echo ""

# Check if required tools are installed
echo "🔍 Checking system requirements..."

# Check Python version
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2)
if [ -z "$python_version" ]; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
else
    echo "✅ Python $python_version found"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 found"
else
    echo "❌ pip3 not found. Please install pip."
fi

# Check if requirements.txt exists
if [ -f requirements.txt ]; then
    echo "✅ requirements.txt found"
    echo ""
    echo "📦 To install dependencies, run:"
    echo "   pip3 install -r requirements.txt"
else
    echo "❌ requirements.txt not found"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Install dependencies: pip3 install -r requirements.txt"
echo "3. Start the application: ./start_agents.sh"
echo ""
echo "📖 For detailed setup instructions, see README.md"
