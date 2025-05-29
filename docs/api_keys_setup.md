# API Keys Setup Guide 🔑

This guide will help you obtain and configure the required API keys for the Finance Assistant.

## 🎯 Required API Keys

### 1. Google Gemini API Key (REQUIRED)

The Gemini API key is essential for:
- Text generation and financial analysis
- Much more cost-effective than OpenAI
- High-quality responses for market briefs

#### How to get your Gemini API Key:

1. **Visit Google AI Studio**: Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

2. **Sign up or Log in**: Create a Google account or log in to your existing account

3. **Create API Key**: Click "Create API Key" button
   - Give it a descriptive name like "Finance Assistant"
   - Copy the key immediately

4. **Add to .env file**:
   \`\`\`env
   GEMINI_API_KEY=your_actual_key_here
   \`\`\`

#### Pricing Information:
- **Gemini Pro**: $0.0001 per 1K input tokens, $0.0002 per 1K output tokens (10x cheaper than GPT-3.5)
- **Free Usage**: 60 queries per minute, generous free tier
- **No Credit Card Required** for free tier

### 2. Alpha Vantage API Key (REQUIRED)

Alpha Vantage provides real-time and historical market data:
- Stock prices and market data
- Earnings information
- Financial indicators

#### How to get your Alpha Vantage API Key:

1. **Visit Alpha Vantage**: Go to [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)

2. **Sign up**: Fill out the form with:
   - Your email address
   - First and last name
   - Organization (can be "Personal" or "Individual")
   - Brief description of how you'll use the API

3. **Get Your Key**: After submitting, you'll receive your API key immediately

4. **Add to .env file**:
   \`\`\`env
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   \`\`\`

#### Free Tier Limits:
- **5 API requests per minute**
- **500 requests per day**
- No credit card required

#### Premium Options:
- **$49.99/month**: 75 requests/minute, 100,000/month
- **$149.99/month**: 300 requests/minute, 1.2M/month

### 3. Pinecone API Key (OPTIONAL)

Pinecone is a cloud vector database alternative to local FAISS storage:
- Managed vector search
- Scalable and fast
- Better for production deployments

#### How to get your Pinecone API Key:

1. **Visit Pinecone**: Go to [https://app.pinecone.io/](https://app.pinecone.io/)

2. **Sign up**: Create a free account

3. **Get API Key**: 
   - Go to "API Keys" in the dashboard
   - Copy your API key and environment

4. **Add to .env file**:
   \`\`\`env
   PINECONE_API_KEY=your_pinecone_key_here
   PINECONE_ENVIRONMENT=us-west1-gcp
   VECTOR_STORE_TYPE=pinecone
   \`\`\`

#### Free Tier:
- **1 index**
- **5M vector dimensions**
- **2 replicas**

## 🛠️ Configuration Steps

### Step 1: Copy Environment File
\`\`\`bash
cp .env.example .env
\`\`\`

### Step 2: Edit the .env File
Open the `.env` file in your favorite text editor and add your API keys:

\`\`\`env
# Required Keys
GEMINI_API_KEY=your_gemini_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Optional Keys
PINECONE_API_KEY=your_pinecone_key_here  # Leave empty to use FAISS
\`\`\`

### Step 3: Validate Configuration
Run the validation script to check your setup:

\`\`\`bash
python validate_env.py
\`\`\`

## 🔒 Security Best Practices

### 1. Keep API Keys Secret
- **Never commit** `.env` files to version control
- **Don't share** API keys in public forums or chat
- **Use environment variables** in production

### 2. Rotate Keys Regularly
- **Change keys** every 3-6 months
- **Monitor usage** in API dashboards
- **Revoke unused keys** immediately

### 3. Set Usage Limits
- **Monitor costs** in Google AI Studio dashboard
- **Set billing alerts** to avoid surprises
- **Use rate limiting** in production

## 💰 Cost Comparison: Gemini vs OpenAI

### Cost Per 1 Million Tokens:
- **Gemini Pro**: $0.10 input / $0.20 output
- **GPT-3.5**: $1.50 input / $2.00 output
- **Savings**: ~90-95% cost reduction!

### Typical Daily Usage (Development):
- **Gemini**: $0.05 - $0.20 per day
  - ~50 queries × $0.001-0.004 per query
- **Alpha Vantage**: Free (within limits)
- **Pinecone**: Free (starter tier)

### Production Usage:
- **Gemini**: $1 - $5 per day
- **Alpha Vantage**: $49.99/month (premium)
- **Pinecone**: $70/month (standard)

## 🚨 Troubleshooting

### Common Issues:

#### "Invalid API Key" Error
- Check that the key is copied correctly
- Ensure no extra spaces or characters
- Verify the key hasn't been revoked

#### "Rate Limit Exceeded"
- **Alpha Vantage**: Wait 1 minute between requests
- **Gemini**: Wait a few seconds between requests

#### "Model Not Available" Error
- Ensure you're using "gemini-pro" as the model name
- Check that your region has access to Gemini API

### Testing Your Setup:

\`\`\`bash
# Test Gemini connection
python -c "import google.generativeai as genai; genai.configure(api_key='your_key'); print([m.name for m in genai.list_models()])"

# Test Alpha Vantage connection
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=your_key"
\`\`\`

## 📞 Support

### Getting Help:
1. **Check the validation script**: `python validate_env.py`
2. **Review logs**: Check `logs/` directory for errors
3. **API Documentation**:
   - [Gemini API Docs](https://ai.google.dev/docs)
   - [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)
   - [Pinecone Docs](https://docs.pinecone.io/)

### Contact Support:
- **Google AI**: [ai.google.dev/contact](https://ai.google.dev/contact)
- **Alpha Vantage**: [support@alphavantage.co](mailto:support@alphavantage.co)
- **Pinecone**: [support@pinecone.io](mailto:support@pinecone.io)

---

**Ready to proceed?** Once you have your API keys configured, run:
\`\`\`bash
./start_agents.sh
