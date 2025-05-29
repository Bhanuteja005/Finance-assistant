import yfinance as yf
import pandas as pd
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
from utils.logger import data_logger
from config import config

class MarketDataClient:
    """Unified client for fetching market data from multiple sources."""
    
    def __init__(self):
        self.alpha_vantage_key = config.ALPHA_VANTAGE_API_KEY
        self.base_url_av = "https://www.alphavantage.co/query"
        
    async def get_stock_data(self, symbol: str, period: str = "1d") -> Dict[str, Any]:
        """Get stock data using yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "current_price": hist['Close'].iloc[-1] if not hist.empty else None,
                "change": hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) > 1 else 0,
                "change_percent": ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else 0,
                "volume": hist['Volume'].iloc[-1] if not hist.empty else None,
                "market_cap": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "sector": info.get('sector'),
                "industry": info.get('industry'),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            data_logger.error(f"Error fetching stock data for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def get_earnings_data(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data for a stock."""
        try:
            ticker = yf.Ticker(symbol)
            earnings = ticker.earnings_dates
            
            if earnings is not None and not earnings.empty:
                latest_earnings = earnings.head(1)
                return {
                    "symbol": symbol,
                    "earnings_date": latest_earnings.index[0].isoformat() if not latest_earnings.empty else None,
                    "eps_estimate": latest_earnings['EPS Estimate'].iloc[0] if 'EPS Estimate' in latest_earnings.columns else None,
                    "eps_actual": latest_earnings['Reported EPS'].iloc[0] if 'Reported EPS' in latest_earnings.columns else None,
                    "surprise_percent": latest_earnings['Surprise(%)'].iloc[0] if 'Surprise(%)' in latest_earnings.columns else None
                }
            return {"symbol": symbol, "earnings_data": "No recent earnings data"}
        except Exception as e:
            data_logger.error(f"Error fetching earnings for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def get_sector_performance(self, sector_symbols: List[str]) -> Dict[str, Any]:
        """Get performance data for a sector."""
        sector_data = []
        
        for symbol in sector_symbols:
            stock_data = await self.get_stock_data(symbol)
            if "error" not in stock_data:
                sector_data.append(stock_data)
        
        if sector_data:
            avg_change = sum(stock['change_percent'] for stock in sector_data) / len(sector_data)
            return {
                "sector_performance": avg_change,
                "stocks": sector_data,
                "timestamp": datetime.now().isoformat()
            }
        
        return {"error": "No valid sector data found"}
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data."""
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow Jones": "^DJI",
            "VIX": "^VIX",
            "Nikkei": "^N225",
            "Hang Seng": "^HSI"
        }
        
        market_data = {}
        for name, symbol in indices.items():
            data = await self.get_stock_data(symbol)
            market_data[name] = data
        
        return market_data

# Asia Tech Stock Symbols for the use case
ASIA_TECH_STOCKS = [
    "TSM",    # Taiwan Semiconductor
    "ASML",   # ASML Holding
    "005930.KS",  # Samsung Electronics
    "6758.T", # Sony
    "9984.T", # SoftBank
    "BABA",   # Alibaba
    "TCEHY",  # Tencent
    "JD",     # JD.com
]
