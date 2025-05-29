from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import aiohttp
import asyncio
from datetime import datetime
from utils.logger import main_logger
from config import config
from data_ingestion.market_data_client import ASIA_TECH_STOCKS

app = FastAPI(title="Finance Assistant Orchestrator", description="Main orchestration service")

class QueryRequest(BaseModel):
    query: str
    query_type: Optional[str] = None
    voice_input: bool = False

class VoiceRequest(BaseModel):
    audio_data: str  # base64 encoded
    
class Orchestrator:
    """Main orchestrator that coordinates all agents."""
    
    def __init__(self):
        self.agent_urls = {
            "api": f"http://localhost:{config.API_AGENT_PORT}",
            "scraping": f"http://localhost:{config.SCRAPING_AGENT_PORT}",
            "retriever": f"http://localhost:{config.RETRIEVER_AGENT_PORT}",
            "analysis": f"http://localhost:{config.ANALYSIS_AGENT_PORT}",
            "language": f"http://localhost:{config.LANGUAGE_AGENT_PORT}",
            "voice": f"http://localhost:{config.VOICE_AGENT_PORT}"
        }
        main_logger.info("Orchestrator initialized")
    
    async def make_agent_request(self, agent: str, endpoint: str, data: dict = None, method: str = "POST") -> dict:
        """Make a request to a specific agent."""
        try:
            url = f"{self.agent_urls[agent]}/{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url) as response:
                        return await response.json()
                else:
                    async with session.post(url, json=data) as response:
                        return await response.json()
                        
        except Exception as e:
            main_logger.error(f"Error calling {agent} agent: {e}")
            return {"error": str(e)}
    
    async def process_morning_brief_query(self, query: str) -> Dict[str, Any]:
        """Process the morning market brief query."""
        try:
            # Step 1: Get portfolio exposure data
            portfolio_request = {
                "symbols": ASIA_TECH_STOCKS,
                "period": "1d"
            }
            
            portfolio_data = await self.make_agent_request(
                "api", "portfolio-exposure", portfolio_request
            )
            
            # Step 2: Get earnings data
            earnings_request = {
                "symbols": ASIA_TECH_STOCKS
            }
            
            earnings_data = await self.make_agent_request(
                "api", "earnings-data", earnings_request
            )
            
            # Step 3: Get market indices
            market_indices = await self.make_agent_request(
                "api", "market-indices", method="GET"
            )
            
            # Step 4: Get sector performance
            sector_request = {
                "sector_name": "Asia Tech",
                "symbols": ASIA_TECH_STOCKS
            }
            
            sector_data = await self.make_agent_request(
                "api", "sector-performance", sector_request
            )
            
            # Step 5: Search for relevant context
            context_request = {
                "query": query,
                "top_k": 5
            }
            
            context_data = await self.make_agent_request(
                "retriever", "get-context", context_request
            )
            
            # Step 6: Generate market brief
            brief_request = {
                "data": {
                    "market_data": {
                        "earnings": earnings_data,
                        "indices": market_indices,
                        "sector": sector_data
                    },
                    "portfolio_data": portfolio_data,
                    "context": context_data
                },
                "analysis_type": "morning_brief"
            }
            
            brief_response = await self.make_agent_request(
                "language", "market-brief", brief_request
            )
            
            return {
                "brief": brief_response.get("market_brief", ""),
                "data": {
                    "portfolio": portfolio_data,
                    "earnings": earnings_data,
                    "market": market_indices,
                    "sector": sector_data
                },
                "context_confidence": context_data.get("confidence", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            main_logger.error(f"Error processing morning brief: {e}")
            return {"error": str(e)}
    
    async def process_general_query(self, query: str) -> Dict[str, Any]:
        """Process a general financial query."""
        try:
            # Step 1: Search for relevant context
            context_request = {
                "query": query,
                "top_k": 10
            }
            
            context_data = await self.make_agent_request(
                "retriever", "get-context", context_request
            )
            
            # Step 2: Check if we have sufficient context
            confidence = context_data.get("confidence", 0)
            
            if confidence < config.RAG_CONFIDENCE_THRESHOLD:
                return {
                    "response": "I don't have sufficient information to answer your query accurately. Could you please provide more specific details or rephrase your question?",
                    "confidence": confidence,
                    "requires_clarification": True
                }
            
            # Step 3: Generate response using language agent
            generation_request = {
                "prompt": query,
                "context": context_data,
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = await self.make_agent_request(
                "language", "generate", generation_request
            )
            
            return {
                "response": response.get("generated_text", ""),
                "confidence": confidence,
                "context_used": len(context_data.get("context", {})),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            main_logger.error(f"Error processing general query: {e}")
            return {"error": str(e)}
    
    async def process_voice_query(self, audio_data: str) -> Dict[str, Any]:
        """Process a voice query."""
        try:
            # Step 1: Convert speech to text
            stt_request = {
                "audio_data": audio_data
            }
            
            # Note: In a real implementation, you'd send the audio file directly
            # This is simplified for the demo
            transcription_result = {
                "transcription": "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?",
                "intent": {"type": "morning_brief", "confidence": 0.9},
                "success": True
            }
            
            if not transcription_result.get("success"):
                return {
                    "error": "Could not transcribe audio",
                    "voice_response": None
                }
            
            query = transcription_result["transcription"]
            intent = transcription_result.get("intent", {})
            
            # Step 2: Process the query based on intent
            if intent.get("type") == "morning_brief":
                result = await self.process_morning_brief_query(query)
            else:
                result = await self.process_general_query(query)
            
            # Step 3: Generate voice response
            if "error" not in result:
                response_text = result.get("brief") or result.get("response", "")
                
                tts_request = {
                    "text": response_text,
                    "language": "en"
                }
                
                voice_response = await self.make_agent_request(
                    "voice", "voice-response", tts_request
                )
                
                result["voice_response"] = voice_response.get("audio_data")
                result["transcription"] = query
            
            return result
            
        except Exception as e:
            main_logger.error(f"Error processing voice query: {e}")
            return {"error": str(e)}

# Initialize orchestrator
orchestrator = Orchestrator()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Finance Assistant Orchestrator"}

@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a text query."""
    try:
        if request.query_type == "morning_brief" or "risk exposure" in request.query.lower():
            result = await orchestrator.process_morning_brief_query(request.query)
        else:
            result = await orchestrator.process_general_query(request.query)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-query")
async def process_voice_query(request: VoiceRequest):
    """Process a voice query."""
    try:
        result = await orchestrator.process_voice_query(request.audio_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    try:
        status = {}
        for agent_name, url in orchestrator.agent_urls.items():
            try:
                health_data = await orchestrator.make_agent_request(agent_name, "health", method="GET")
                status[agent_name] = health_data.get("status", "unknown")
            except:
                status[agent_name] = "offline"
        
        return {"agents_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.ORCHESTRATOR_PORT)
