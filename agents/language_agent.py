from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from crewai import Agent, Task, Crew
from utils.logger import agent_logger
from config import config
import asyncio

app = FastAPI(title="Language Agent", description="Handles LLM operations and text generation")

class GenerationRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: int = 1000
    temperature: float = 0.3

class AnalysisRequest(BaseModel):
    data: Dict[str, Any]
    analysis_type: str
    context: Optional[str] = None

class LanguageAgent:
    """Agent responsible for LLM operations and text generation."""
    
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Initialize LangChain with Gemini
        self.llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS,
            google_api_key=config.GEMINI_API_KEY
        )
        
        # Initialize CrewAI agents
        self.setup_crew_agents()
        agent_logger.info("Language Agent initialized with Gemini API")
    
    def setup_crew_agents(self):
        """Setup specialized CrewAI agents."""
        self.market_analyst = Agent(
            role='Market Analyst',
            goal='Analyze market data and provide insights',
            backstory='Expert financial analyst with deep knowledge of Asian tech markets',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.risk_analyst = Agent(
            role='Risk Analyst',
            goal='Assess portfolio risk and exposure',
            backstory='Specialized in portfolio risk management and exposure analysis',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.earnings_analyst = Agent(
            role='Earnings Analyst',
            goal='Analyze earnings data and surprises',
            backstory='Expert in earnings analysis and corporate performance',
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    async def generate_market_brief(self, market_data: Dict[str, Any], portfolio_data: Dict[str, Any]) -> str:
        """Generate a comprehensive market brief."""
        try:
            # Create tasks for different aspects of the brief
            risk_task = Task(
                description=f"""
                Analyze the portfolio risk exposure based on this data:
                {portfolio_data}
                
                Focus on:
                1. Asia tech allocation percentage
                2. Risk concentration
                3. Recent changes in exposure
                """,
                agent=self.risk_analyst,
                expected_output="A concise summary of portfolio risk exposure and Asia tech allocation."
            )
            
            earnings_task = Task(
                description=f"""
                Analyze earnings surprises and performance:
                {market_data.get('earnings', {})}
                
                Highlight:
                1. Significant beats or misses
                2. Impact on sector sentiment
                3. Key companies to watch
                """,
                agent=self.earnings_analyst,
                expected_output="A summary of earnings surprises, sector sentiment, and key companies."
            )
            
            market_task = Task(
                description=f"""
                Provide market overview and sentiment:
                {market_data.get('indices', {})}
                
                Include:
                1. Overall market direction
                2. Regional performance
                3. Key drivers and concerns
                """,
                agent=self.market_analyst,
                expected_output="A summary of market direction, regional performance, and key drivers."
            )
            
            # Execute tasks
            crew = Crew(
                agents=[self.risk_analyst, self.earnings_analyst, self.market_analyst],
                tasks=[risk_task, earnings_task, market_task],
                verbose=True
            )
            
            # Use asyncio.to_thread to run blocking crew.kickoff in a thread
            result = await asyncio.to_thread(crew.kickoff)
            
            # Synthesize the final brief
            synthesis_prompt = f"""
            Based on the following analysis, create a concise morning market brief:
            
            {result}
            
            Format the response as a spoken brief that answers:
            "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
            
            Keep it conversational and under 200 words.
            """
            
            brief = await self.generate_text(synthesis_prompt)
            return brief
            
        except Exception as e:
            agent_logger.error(f"Error generating market brief: {e}")
            return "I apologize, but I'm unable to generate the market brief at this time due to a technical issue."
    
    async def generate_text(self, prompt: str, context: Dict[str, Any] = None, max_tokens: int = 1000, temperature: float = 0.3) -> str:
        """Generate text using Gemini API."""
        try:
            # Prepare the prompt with context if provided
            if context:
                enhanced_prompt = f"""
                Context: {context}
                
                Request: {prompt}
                
                Please provide a comprehensive response based on the context provided.
                """
            else:
                enhanced_prompt = prompt
            
            # Generate content with Gemini
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            model = genai.GenerativeModel(
                model_name=config.LLM_MODEL,
                generation_config=generation_config
            )
            
            response = model.generate_content(enhanced_prompt)
            
            return response.text
            
        except Exception as e:
            agent_logger.error(f"Error generating text with Gemini: {e}")
            return "I apologize, but I'm unable to process your request at this time."
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of financial text."""
        try:
            prompt = f"""
            Analyze the sentiment of the following financial text and provide:
            1. Overall sentiment (positive, negative, neutral)
            2. Confidence score (0-1)
            3. Key sentiment drivers
            4. Market implications
            
            Text: {text}
            
            Respond in JSON format.
            """
            
            response = await self.generate_text(prompt, max_tokens=500)
            
            # Parse response (in production, you'd use a more robust parser)
            return {
                "sentiment_analysis": response,
                "text_analyzed": text[:100] + "..." if len(text) > 100 else text
            }
            
        except Exception as e:
            agent_logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}

# Initialize agent
language_agent = LanguageAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Language Agent"}

@app.post("/generate")
async def generate_text(request: GenerationRequest):
    """Generate text based on prompt and context."""
    try:
        result = await language_agent.generate_text(
            request.prompt,
            request.context,
            request.max_tokens,
            request.temperature
        )
        return {"generated_text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/market-brief")
async def generate_market_brief(request: AnalysisRequest):
    """Generate a market brief based on data."""
    try:
        market_data = request.data.get('market_data', {})
        portfolio_data = request.data.get('portfolio_data', {})
        
        brief = await language_agent.generate_market_brief(market_data, portfolio_data)
        return {"market_brief": brief}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-sentiment")
async def analyze_sentiment(request: GenerationRequest):
    """Analyze sentiment of financial text."""
    try:
        result = await language_agent.analyze_sentiment(request.prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.LANGUAGE_AGENT_PORT)
