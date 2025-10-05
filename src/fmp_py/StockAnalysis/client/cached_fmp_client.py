#!/usr/bin/env python3
"""
Cached FMP Client - FMP API Client with MySQL database caching

This module extends the base FMP client with intelligent caching.
It checks the database cache before making API calls to reduce API usage
and improve response times.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Union
from datetime import datetime

from ..client.fmp_client import FMPClient, FMPAPIError
from ..database import (
    company_dal,
    quote_dal,
    historical_price_dal,
    get_cache_manager,
    get_db
)

logger = logging.getLogger(__name__)


class CachedFMPClient(FMPClient):
    """
    FMP Client with database caching support
    
    This client extends the base FMPClient to provide transparent caching
    of API responses in a MySQL database. It automatically checks the cache
    before making API calls and stores responses for future use.
    
    Usage:
        # Initialize with caching enabled
        client = CachedFMPClient(api_key="your_key", enable_cache=True)
        
        # Use like normal FMP client - caching is transparent
        quote = client.get_quote("AAPL")
        profile = client.get_company_profile("AAPL")
        
        # Get cache statistics
        stats = client.get_cache_stats()
    """
    
    def __init__(self, api_key: str, timeout: int = 30, enable_cache: bool = True):
        """
        Initialize the cached FMP client
        
        Args:
            api_key (str): Your Financial Modeling Prep API key
            timeout (int): Request timeout in seconds
            enable_cache (bool): Enable database caching
        """
        super().__init__(api_key, timeout)
        
        self.enable_cache = enable_cache
        
        if self.enable_cache:
            try:
                self.db = get_db()
                self.cache_manager = get_cache_manager()
                
                # Test database connection
                if self.db.test_connection():
                    logger.info("Database cache enabled and connected")
                else:
                    logger.warning("Database connection test failed, caching disabled")
                    self.enable_cache = False
            except Exception as e:
                logger.warning(f"Failed to initialize database cache: {e}")
                logger.warning("Falling back to non-cached mode")
                self.enable_cache = False
        else:
            logger.info("Database cache disabled")
    
    def _make_request_with_cache(self, endpoint: str, params: Optional[Dict] = None,
                                version: str = "v3", symbol: Optional[str] = None) -> Union[Dict, List]:
        """
        Make a request with cache support
        
        Args:
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            version (str): API version
            symbol (str, optional): Stock symbol for cache key
            
        Returns:
            API response data
        """
        start_time = time.time()
        from_cache = False
        error_message = None
        
        try:
            # Make API request (cache checking happens in specific methods)
            data = super()._make_request(endpoint, params, version)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log successful request
            if self.enable_cache:
                self.cache_manager.log_api_request(
                    endpoint=endpoint,
                    symbol=symbol,
                    params=params,
                    from_cache=from_cache,
                    response_status=200,
                    response_time_ms=response_time_ms
                )
            
            return data
            
        except Exception as e:
            error_message = str(e)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log failed request
            if self.enable_cache:
                self.cache_manager.log_api_request(
                    endpoint=endpoint,
                    symbol=symbol,
                    params=params,
                    from_cache=False,
                    response_status=None,
                    response_time_ms=response_time_ms,
                    error_message=error_message
                )
            
            raise
    
    # ========================================================================
    # CACHED METHODS - Override base class methods with caching
    # ========================================================================
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote with caching
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Dict: Quote data
        """
        if not self.enable_cache:
            return super().get_quote(symbol)
        
        # Check cache first
        cached_quote = quote_dal.get_quote(symbol, check_expiry=True)
        if cached_quote:
            logger.debug(f"Quote for {symbol} retrieved from cache")
            self.cache_manager.log_api_request(
                endpoint=f"quote/{symbol}",
                symbol=symbol,
                from_cache=True,
                response_status=200,
                response_time_ms=0
            )
            return cached_quote
        
        # Cache miss - fetch from API
        logger.debug(f"Quote for {symbol} not in cache, fetching from API")
        quote_data = super().get_quote(symbol)
        
        if quote_data:
            # Store in cache
            quote_dal.upsert_quote(symbol, quote_data)
            self.cache_manager.update_cache_metadata(
                endpoint=f"quote/{symbol}",
                symbol=symbol
            )
        
        return quote_data
    
    def get_company_profile(self, symbol: str) -> Optional[List[Dict]]:
        """
        Get company profile with caching
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            List[Dict]: Company profile data
        """
        if not self.enable_cache:
            return super().get_company_profile(symbol)
        
        # Check cache first
        cached_profile = company_dal.get_company_profile(symbol, check_expiry=True)
        if cached_profile:
            logger.debug(f"Profile for {symbol} retrieved from cache")
            self.cache_manager.log_api_request(
                endpoint=f"profile/{symbol}",
                symbol=symbol,
                from_cache=True,
                response_status=200,
                response_time_ms=0
            )
            return [cached_profile]
        
        # Cache miss - fetch from API
        logger.debug(f"Profile for {symbol} not in cache, fetching from API")
        profile_data = super().get_company_profile(symbol)
        
        if profile_data and len(profile_data) > 0:
            # Ensure company exists in companies table
            company_dal.upsert_company(
                symbol=symbol,
                name=profile_data[0].get('companyName', symbol),
                exchange=profile_data[0].get('exchange'),
                exchangeShortName=profile_data[0].get('exchangeShortName'),
                currency=profile_data[0].get('currency'),
                country=profile_data[0].get('country')
            )
            
            # Store profile in cache
            company_dal.upsert_company_profile(symbol, profile_data[0])
            self.cache_manager.update_cache_metadata(
                endpoint=f"profile/{symbol}",
                symbol=symbol
            )
        
        return profile_data
    
    def get_historical_prices(self, symbol: str, from_date: str = None,
                            to_date: str = None, period: str = "1day") -> Optional[Dict]:
        """
        Get historical prices with caching
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            period (str): Time period
            
        Returns:
            Dict: Historical price data
        """
        if not self.enable_cache:
            return super().get_historical_prices(symbol, from_date, to_date, period)
        
        # For daily prices, check cache
        if period == "1day":
            cached_prices = historical_price_dal.get_daily_prices(
                symbol, from_date, to_date
            )
            
            if cached_prices:
                logger.debug(f"Historical prices for {symbol} retrieved from cache ({len(cached_prices)} records)")
                self.cache_manager.log_api_request(
                    endpoint=f"historical-price-full/{symbol}",
                    symbol=symbol,
                    params={'from': from_date, 'to': to_date},
                    from_cache=True,
                    response_status=200,
                    response_time_ms=0
                )
                return {
                    'symbol': symbol.upper(),
                    'historical': cached_prices
                }
        
        # Cache miss or intraday data - fetch from API
        logger.debug(f"Historical prices for {symbol} not in cache, fetching from API")
        historical_data = super().get_historical_prices(symbol, from_date, to_date, period)
        
        if historical_data and 'historical' in historical_data:
            # Ensure company exists
            company_dal.upsert_company(
                symbol=symbol,
                name=symbol  # Minimal company record
            )
            
            # Store in cache
            if period == "1day":
                historical_price_dal.upsert_daily_prices(
                    symbol, historical_data['historical']
                )
            else:
                historical_price_dal.upsert_intraday_prices(
                    symbol, period, historical_data['historical']
                )
            
            self.cache_manager.update_cache_metadata(
                endpoint=f"historical-price-full/{symbol}",
                symbol=symbol,
                params={'from': from_date, 'to': to_date, 'period': period}
            )
        
        return historical_data
    
    def get_stock_list(self) -> Optional[List[Dict]]:
        """
        Get stock list with caching
        
        Returns:
            List[Dict]: List of stocks
        """
        if not self.enable_cache:
            return super().get_stock_list()
        
        # Check if we have companies in cache
        cached_companies = company_dal.get_all_companies(limit=10000)
        if cached_companies and len(cached_companies) > 1000:
            logger.debug(f"Stock list retrieved from cache ({len(cached_companies)} companies)")
            return cached_companies
        
        # Fetch from API
        logger.debug("Stock list not in cache, fetching from API")
        stock_list = super().get_stock_list()
        
        if stock_list:
            # Store in cache
            for stock in stock_list:
                company_dal.upsert_company(
                    symbol=stock.get('symbol', ''),
                    name=stock.get('name', ''),
                    exchange=stock.get('exchange'),
                    exchangeShortName=stock.get('exchangeShortName'),
                    type=stock.get('type'),
                    currency=stock.get('currency')
                )
            
            logger.info(f"Cached {len(stock_list)} companies")
        
        return stock_list
    
    # ========================================================================
    # CACHE MANAGEMENT METHODS
    # ========================================================================
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        if not self.enable_cache:
            return {'cache_enabled': False}
        
        return {
            'cache_enabled': True,
            **self.cache_manager.get_cache_stats()
        }
    
    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            int: Number of records deleted
        """
        if not self.enable_cache:
            return 0
        
        return self.cache_manager.cleanup_expired_cache()
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Clean up old API request logs
        
        Args:
            days (int): Keep logs for this many days
            
        Returns:
            int: Number of log entries deleted
        """
        if not self.enable_cache:
            return 0
        
        return self.cache_manager.cleanup_old_logs(days)
    
    def force_refresh(self, symbol: str, data_type: str) -> bool:
        """
        Force refresh of cached data for a symbol
        
        Args:
            symbol (str): Stock symbol
            data_type (str): Type of data ('quote', 'profile', 'historical')
            
        Returns:
            bool: Success status
        """
        if not self.enable_cache:
            return False
        
        try:
            if data_type == 'quote':
                # Delete cached quote
                query = "DELETE FROM quotes WHERE symbol = %s"
                self.db.execute_update(query, (symbol.upper(),))
            elif data_type == 'profile':
                # Delete cached profile
                query = "DELETE FROM company_profiles WHERE symbol = %s"
                self.db.execute_update(query, (symbol.upper(),))
            elif data_type == 'historical':
                # Delete cached historical prices
                query = "DELETE FROM historical_prices_daily WHERE symbol = %s"
                self.db.execute_update(query, (symbol.upper(),))
            
            logger.info(f"Forced refresh of {data_type} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error forcing refresh: {e}")
            return False


# Convenience function
def create_cached_client(api_key: str = None, enable_cache: bool = True) -> CachedFMPClient:
    """
    Create a cached FMP client
    
    Args:
        api_key (str, optional): API key, if not provided will check environment
        enable_cache (bool): Enable database caching
        
    Returns:
        CachedFMPClient: Initialized cached client
    """
    if not api_key:
        api_key = os.getenv('FMP_API_KEY')
    
    if not api_key:
        raise ValueError("API key must be provided or set in FMP_API_KEY environment variable")
    
    return CachedFMPClient(api_key, enable_cache=enable_cache)
