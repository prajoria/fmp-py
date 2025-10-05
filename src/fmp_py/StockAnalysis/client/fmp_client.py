#!/usr/bin/env python3
"""
Financial Modeling Prep API Client
A comprehensive Python client for accessing FMP financial data.

This module provides a clean interface to the Financial Modeling Prep API
with support for real-time quotes, historical data, financial statements,
company profiles, and more.
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional, Union
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FMPAPIError(Exception):
    """Custom exception for FMP API errors"""
    pass


class FMPClient:
    """Financial Modeling Prep API Client
    
    A comprehensive client for interacting with the Financial Modeling Prep API.
    Provides methods for retrieving stock quotes, financial data, company information,
    and market analytics.
    
    Attributes:
        api_key (str): Your FMP API key
        base_url (str): Base URL for FMP API endpoints
        session (requests.Session): HTTP session for making requests
    """
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the FMP client
        
        Args:
            api_key (str): Your Financial Modeling Prep API key
            timeout (int): Request timeout in seconds (default: 30)
        """
        if not api_key:
            raise ValueError("API key is required")
            
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'FMP-Python-Client/1.0.0',
            'Accept': 'application/json'
        })
        
        logger.info(f"FMP Client initialized with API key: {api_key[:8]}...")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                     version: str = "v3") -> Union[Dict, List]:
        """
        Make a request to the FMP API
        
        Args:
            endpoint (str): API endpoint (without base URL)
            params (dict, optional): Additional query parameters
            version (str): API version (default: v3)
            
        Returns:
            Union[Dict, List]: API response data
            
        Raises:
            FMPAPIError: If the API request fails
        """
        if params is None:
            params = {}
        
        params['apikey'] = self.api_key
        
        url = f"https://financialmodelingprep.com/api/{version}/{endpoint}"
        
        try:
            logger.debug(f"Making request to: {url}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API-specific errors
            if isinstance(data, dict) and 'Error Message' in data:
                raise FMPAPIError(f"API Error: {data['Error Message']}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise FMPAPIError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise FMPAPIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise FMPAPIError(f"Invalid JSON response: {str(e)}")
    
    # Stock Data Methods
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote for a stock symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dict: Quote data including price, volume, market cap, etc.
        """
        data = self._make_request(f"quote/{symbol.upper()}")
        return data[0] if data and isinstance(data, list) else data
    
    def get_quotes(self, symbols: List[str]) -> Optional[List[Dict]]:
        """
        Get real-time quotes for multiple symbols
        
        Args:
            symbols (List[str]): List of stock symbols
            
        Returns:
            List[Dict]: List of quote data
        """
        symbols_str = ','.join([s.upper() for s in symbols])
        return self._make_request(f"quote/{symbols_str}")
    
    def get_historical_prices(self, symbol: str, from_date: str = None, 
                            to_date: str = None, period: str = "1day") -> Optional[Dict]:
        """
        Get historical price data
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            period (str): Time period ('1day', '1hour', '5min', etc.)
            
        Returns:
            Dict: Historical price data with symbol and historical array
        """
        params = {}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        endpoint = f"historical-price-full/{symbol.upper()}"
        if period != "1day":
            endpoint = f"historical-chart/{period}/{symbol.upper()}"
            
        return self._make_request(endpoint, params)
    
    # Company Information Methods
    def get_company_profile(self, symbol: str) -> Optional[List[Dict]]:
        """
        Get detailed company profile information
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            List[Dict]: Company profile data including business description,
                       industry, sector, financials, and key metrics
        """
        return self._make_request(f"profile/{symbol.upper()}")
    
    def get_company_executives(self, symbol: str) -> Optional[List[Dict]]:
        """
        Get company executive information
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            List[Dict]: Executive team information
        """
        return self._make_request(f"key-executives/{symbol.upper()}")
    
    # Financial Statements Methods
    def get_income_statement(self, symbol: str, period: str = "annual", 
                           limit: int = 5) -> Optional[List[Dict]]:
        """
        Get income statement data
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Income statement data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"income-statement/{symbol.upper()}", params)
    
    def get_balance_sheet(self, symbol: str, period: str = "annual", 
                         limit: int = 5) -> Optional[List[Dict]]:
        """
        Get balance sheet data
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Balance sheet data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"balance-sheet-statement/{symbol.upper()}", params)
    
    def get_cash_flow_statement(self, symbol: str, period: str = "annual", 
                               limit: int = 5) -> Optional[List[Dict]]:
        """
        Get cash flow statement data
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Cash flow statement data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"cash-flow-statement/{symbol.upper()}", params)
    
    # Market Data Methods
    def get_market_gainers(self) -> Optional[List[Dict]]:
        """Get today's market gainers"""
        return self._make_request("stock_market/gainers")
    
    def get_market_losers(self) -> Optional[List[Dict]]:
        """Get today's market losers"""
        return self._make_request("stock_market/losers")
    
    def get_market_most_active(self) -> Optional[List[Dict]]:
        """Get most active stocks"""
        return self._make_request("stock_market/actives")
    
    def get_sector_performance(self) -> Optional[List[Dict]]:
        """Get sector performance data"""
        return self._make_request("sector-performance")
    
    # Search and Discovery Methods
    def search_company(self, query: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Search for companies
        
        Args:
            query (str): Search query (company name or symbol)
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: Search results
        """
        params = {'query': query, 'limit': limit}
        return self._make_request("search", params)
    
    def get_stock_list(self) -> Optional[List[Dict]]:
        """Get list of all available stocks"""
        return self._make_request("stock/list")
    
    def get_etf_list(self) -> Optional[List[Dict]]:
        """Get list of all available ETFs"""
        return self._make_request("etf/list")
    
    # News and Calendar Methods
    def get_stock_news(self, symbol: str = None, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get financial news
        
        Args:
            symbol (str, optional): Stock symbol for company-specific news
            limit (int): Number of articles to retrieve
            
        Returns:
            List[Dict]: News articles
        """
        if symbol:
            params = {'tickers': symbol.upper(), 'limit': limit}
            return self._make_request("stock_news", params)
        else:
            params = {'size': limit}
            return self._make_request("fmp/articles", params)
    
    def get_earnings_calendar(self, from_date: str = None, 
                             to_date: str = None) -> Optional[List[Dict]]:
        """
        Get earnings calendar
        
        Args:
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            List[Dict]: Earnings calendar data
        """
        params = {}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        return self._make_request("earning_calendar", params)
    
    def get_dividend_calendar(self, from_date: str = None, 
                             to_date: str = None) -> Optional[List[Dict]]:
        """
        Get dividend calendar
        
        Args:
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            List[Dict]: Dividend calendar data
        """
        params = {}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        return self._make_request("stock_dividend_calendar", params)
    
    # Analysis and Metrics Methods
    def get_financial_ratios(self, symbol: str, period: str = "annual", 
                           limit: int = 5) -> Optional[List[Dict]]:
        """
        Get financial ratios
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Financial ratios data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"ratios/{symbol.upper()}", params)
    
    def get_key_metrics(self, symbol: str, period: str = "annual", 
                       limit: int = 5) -> Optional[List[Dict]]:
        """
        Get key financial metrics
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Key metrics data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"key-metrics/{symbol.upper()}", params)
    
    def get_financial_growth(self, symbol: str, period: str = "annual", 
                           limit: int = 5) -> Optional[List[Dict]]:
        """
        Get financial growth metrics
        
        Args:
            symbol (str): Stock symbol
            period (str): 'annual' or 'quarter'
            limit (int): Number of periods to retrieve
            
        Returns:
            List[Dict]: Financial growth data
        """
        params = {'period': period, 'limit': limit}
        return self._make_request(f"financial-growth/{symbol.upper()}", params)
    
    # Data Conversion Methods
    def to_dataframe(self, data: Union[Dict, List[Dict]], 
                    normalize: bool = True) -> pd.DataFrame:
        """
        Convert API response to pandas DataFrame
        
        Args:
            data: API response data
            normalize (bool): Whether to normalize nested JSON
            
        Returns:
            pd.DataFrame: Data as DataFrame
        """
        if not data:
            return pd.DataFrame()
        
        if isinstance(data, dict):
            if 'historical' in data:
                # Handle historical data format
                df = pd.DataFrame(data['historical'])
                df['symbol'] = data.get('symbol', '')
                return df
            else:
                # Convert single dict to list
                data = [data]
        
        if normalize:
            return pd.json_normalize(data)
        else:
            return pd.DataFrame(data)
    
    # Utility Methods
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a simple request
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            response = self._make_request("stock/list", {'limit': 1})
            return response is not None
        except FMPAPIError:
            return False
    
    def get_api_usage(self) -> Optional[Dict]:
        """
        Get API usage statistics (if available)
        
        Returns:
            Dict: API usage information
        """
        try:
            return self._make_request("api-usage")
        except FMPAPIError:
            return None


# Convenience function for quick initialization
def create_client(api_key: str = None) -> FMPClient:
    """
    Create an FMP client with API key from environment or parameter
    
    Args:
        api_key (str, optional): API key, if not provided will check environment
        
    Returns:
        FMPClient: Initialized client
    """
    if not api_key:
        api_key = os.getenv('FMP_API_KEY')
        
    if not api_key:
        raise ValueError("API key must be provided or set in FMP_API_KEY environment variable")
    
    return FMPClient(api_key)