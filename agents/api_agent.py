from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import numpy as np
from data_ingestion.market_data_client import MarketDataClient, ASIA_TECH_STOCKS
from utils.logger import agent_logger
from config import config

app = FastAPI(title="API Agent", description="Handles real-time market data")

class StockRequest(BaseModel):
    symbols: List[str]
    period: str = "1d"

class EarningsRequest(BaseModel):
    symbols: List[str]

class SectorRequest(BaseModel):
    sector_name: str
    symbols: Optional[List[str]] = None

class APIAgent:
    """Agent responsible for fetching real-time market data."""
    
    def __init__(self):
        self.market_client = MarketDataClient()
        agent_logger.info("API Agent initialized")
    
    async def get_portfolio_exposure(self, portfolio_symbols: List[str]) -> Dict[str, Any]:
        """Calculate portfolio exposure for given symbols."""
        try:
            portfolio_data = []
            total_value = 0
            
            for symbol in portfolio_symbols:
                stock_data = await self.market_client.get_stock_data(symbol)
                if "error" not in stock_data and stock_data.get('current_price'):
                    # Simulate position size (in production, this would come from portfolio management system)
                    position_size = 1000  # Assume 1000 shares for demo
                    position_value = stock_data['current_price'] * position_size
                    
                    stock_data['position_size'] = position_size
                    stock_data['position_value'] = position_value
                    portfolio_data.append(stock_data)
                    total_value += position_value
            
            # Calculate exposure percentages
            for stock in portfolio_data:
                stock['exposure_percent'] = (stock['position_value'] / total_value * 100) if total_value > 0 else 0
            
            return {
                "portfolio_data": portfolio_data,
                "total_value": total_value,
                "asia_tech_exposure": sum(stock['exposure_percent'] for stock in portfolio_data if stock['symbol'] in ASIA_TECH_STOCKS)
            }
            
        except Exception as e:
            agent_logger.error(f"Error calculating portfolio exposure: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_earnings_surprises(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get earnings surprises for given symbols."""
        try:
            earnings_data = []
            
            for symbol in symbols:
                earnings = await self.market_client.get_earnings_data(symbol)
                if "error" not in earnings and earnings.get('surprise_percent') is not None:
                    earnings_data.append(earnings)
            
            return earnings_data
            
        except Exception as e:
            agent_logger.error(f"Error fetching earnings surprises: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def to_native(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_native(v) for v in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    else:
        return obj

# Initialize agent
api_agent = APIAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "API Agent"}

@app.post("/stock-data")
async def get_stock_data(request: StockRequest):
    """Get stock data for multiple symbols."""
    try:
        tasks = [api_agent.market_client.get_stock_data(symbol, request.period) for symbol in request.symbols]
        results = await asyncio.gather(*tasks)
        return {"stocks": to_native(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/earnings-data")
async def get_earnings_data(request: EarningsRequest):
    """Get earnings data for multiple symbols."""
    try:
        earnings_data = await api_agent.get_earnings_surprises(request.symbols)
        return {"earnings": to_native(earnings_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio-exposure")
async def get_portfolio_exposure(request: StockRequest):
    """Get portfolio exposure analysis."""
    try:
        exposure_data = await api_agent.get_portfolio_exposure(request.symbols)
        return to_native(exposure_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market-indices")
async def get_market_indices():
    """Get major market indices."""
    try:
        indices_data = await api_agent.market_client.get_market_indices()
        return {"indices": to_native(indices_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sector-performance")
async def get_sector_performance(request: SectorRequest):
    """Get sector performance data."""
    try:
        symbols = request.symbols or ASIA_TECH_STOCKS
        sector_data = await api_agent.market_client.get_sector_performance(symbols)
        return to_native(sector_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.API_AGENT_PORT)
