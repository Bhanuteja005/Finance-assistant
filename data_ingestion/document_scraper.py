import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from typing import List, Dict, Any, Optional
import time
from datetime import datetime
from sec_edgar_downloader import Downloader
import os
from utils.logger import data_logger

class DocumentScraper:
    """Scraper for financial documents and filings."""
    
    def __init__(self):
        self.setup_selenium()
        self.sec_downloader = Downloader("FinanceAssistant", "your-email@example.com")
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with headless Chrome."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            data_logger.warning(f"Chrome driver not available: {e}")
            self.driver = None
    
    async def scrape_sec_filings(self, ticker: str, filing_type: str = "10-K", limit: int = 5) -> List[Dict[str, Any]]:
        """Scrape SEC filings for a given ticker."""
        try:
            # Download filings
            self.sec_downloader.get(filing_type, ticker, limit=limit)
            
            filings = []
            filing_dir = f"sec-edgar-filings/{ticker}/{filing_type}"
            
            if os.path.exists(filing_dir):
                for filing_folder in os.listdir(filing_dir)[:limit]:
                    filing_path = os.path.join(filing_dir, filing_folder)
                    if os.path.isdir(filing_path):
                        # Find the main filing document
                        for file in os.listdir(filing_path):
                            if file.endswith('.txt') or file.endswith('.htm'):
                                file_path = os.path.join(filing_path, file)
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                filings.append({
                                    "ticker": ticker,
                                    "filing_type": filing_type,
                                    "file_name": file,
                                    "content": content[:10000],  # First 10k characters
                                    "filing_date": filing_folder,
                                    "scraped_at": datetime.now().isoformat()
                                })
                                break
            
            return filings
            
        except Exception as e:
            data_logger.error(f"Error scraping SEC filings for {ticker}: {e}")
            return []
    
    async def scrape_earnings_transcripts(self, ticker: str) -> List[Dict[str, Any]]:
        """Scrape earnings call transcripts (simplified version)."""
        try:
            # This is a simplified version - in production, you'd use APIs like Seeking Alpha
            url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
            
            if self.driver:
                self.driver.get(url)
                time.sleep(3)
                
                # Extract analyst estimates and commentary
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find earnings-related content
                earnings_data = []
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            earnings_data.append({
                                "ticker": ticker,
                                "data_type": "analyst_estimate",
                                "content": " ".join([cell.get_text().strip() for cell in cells]),
                                "scraped_at": datetime.now().isoformat()
                            })
                
                return earnings_data
            
            return []
            
        except Exception as e:
            data_logger.error(f"Error scraping earnings transcripts for {ticker}: {e}")
            return []
    
    async def scrape_news_sentiment(self, query: str) -> List[Dict[str, Any]]:
        """Scrape financial news for sentiment analysis."""
        try:
            # Using a simple news scraping approach
            url = f"https://finance.yahoo.com/news"
            
            if self.driver:
                self.driver.get(url)
                time.sleep(3)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                articles = soup.find_all('h3')
                
                news_data = []
                for article in articles[:10]:  # Limit to 10 articles
                    title = article.get_text().strip()
                    if query.lower() in title.lower():
                        news_data.append({
                            "title": title,
                            "query": query,
                            "source": "Yahoo Finance",
                            "scraped_at": datetime.now().isoformat()
                        })
                
                return news_data
            
            return []
            
        except Exception as e:
            data_logger.error(f"Error scraping news for {query}: {e}")
            return []
    
    def __del__(self):
        """Clean up Selenium driver."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
