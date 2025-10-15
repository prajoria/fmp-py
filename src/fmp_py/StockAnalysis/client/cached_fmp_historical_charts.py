#!/usr/bin/env python3
"""
Cached FMP Historical Charts API Client
Extends FmpHistoricalCharts with database caching capabilities
"""

import logging
from typing import List, Optional
import pandas as pd
from datetime import datetime

# Import base classes
from fmp_py.fmp_historical_charts import FmpHistoricalCharts
from fmp_py.models.historical_charts import (
    HistoricalPriceLight,
    HistoricalPriceFull,
    IntradayPrice,
)

# Import cache manager
from fmp_py.StockAnalysis.database.historical_charts_cache_manager import (
    get_historical_cache_manager
)

logger = logging.getLogger(__name__)


class CachedFmpHistoricalCharts(FmpHistoricalCharts):
    """
    Cached FMP Historical Charts API client.
    
    Extends FmpHistoricalCharts with database caching to:
    - Reduce API calls by serving cached data when available
    - Store historical data for offline analysis
    - Improve response times for frequently requested data
    - Track API usage and cache hit rates
    """
    
    def __init__(self, api_key: str = None, enable_cache: bool = True):
        """
        Initialize the cached historical charts client.
        
        Args:
            api_key (str, optional): FMP API key
            enable_cache (bool): Enable database caching (default: True)
        """
        super().__init__(api_key)
        self.enable_cache = enable_cache
        self.cache_manager = get_historical_cache_manager() if enable_cache else None
    
    def _convert_dict_to_light_model(self, data_dict: dict) -> HistoricalPriceLight:
        """Convert database dict to HistoricalPriceLight model"""
        return HistoricalPriceLight(
            date=data_dict.get('date'),
            open=data_dict.get('open'),
            high=data_dict.get('high'),
            low=data_dict.get('low'),
            close=data_dict.get('close'),
            volume=data_dict.get('volume'),
        )
    
    def _convert_dict_to_full_model(self, data_dict: dict) -> HistoricalPriceFull:
        """Convert database dict to HistoricalPriceFull model"""
        return HistoricalPriceFull(
            date=data_dict.get('date'),
            open=data_dict.get('open'),
            high=data_dict.get('high'),
            low=data_dict.get('low'),
            close=data_dict.get('close'),
            adjClose=data_dict.get('adj_close'),
            volume=data_dict.get('volume'),
            unadjustedVolume=data_dict.get('unadjusted_volume'),
            change=data_dict.get('change'),
            changePercent=data_dict.get('change_percent'),
            vwap=data_dict.get('vwap'),
            label=data_dict.get('label'),
            changeOverTime=data_dict.get('change_over_time'),
        )
    
    def _convert_dict_to_intraday_model(self, data_dict: dict) -> IntradayPrice:
        """Convert database dict to IntradayPrice model"""
        return IntradayPrice(
            date=data_dict.get('datetime'),
            open=data_dict.get('open'),
            high=data_dict.get('high'),
            low=data_dict.get('low'),
            close=data_dict.get('close'),
            volume=data_dict.get('volume'),
        )
    
    def _convert_models_to_dicts(self, models: List) -> List[dict]:
        """Convert model objects to dictionaries for caching"""
        dicts = []
        for model in models:
            if hasattr(model, '__dict__'):
                dicts.append(model.__dict__)
            else:
                # Handle dataclass objects
                import dataclasses
                if dataclasses.is_dataclass(model):
                    dicts.append(dataclasses.asdict(model))
                else:
                    # Fallback for other objects
                    dicts.append(vars(model))
        return dicts
    
    # ========================================================================
    # CACHED LIGHT HISTORICAL DATA METHODS
    # ========================================================================
    
    def get_historical_price_light(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceLight]:
        """
        Get simplified historical price data with caching.
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            list: Historical price data
        """
        if not self.enable_cache or not self.cache_manager:
            # Fall back to direct API call
            return super().get_historical_price_light(symbol, from_date, to_date)
        
        try:
            # Try to get from cache first
            cached_data = self.cache_manager.get_cached_historical_light(
                symbol, from_date, to_date
            )
            
            if cached_data:
                logger.info(f"Serving {len(cached_data)} light historical records from cache for {symbol}")
                return [self._convert_dict_to_light_model(d) for d in cached_data]
            
            # Cache miss - fetch from API
            logger.info(f"Cache miss for light historical data {symbol}, fetching from API")
            api_data = super().get_historical_price_light(symbol, from_date, to_date)
            
            # Cache the results
            if api_data:
                data_dicts = self._convert_models_to_dicts(api_data)
                success, cache_key = self.cache_manager.cache_historical_light(
                    symbol, data_dicts, from_date, to_date
                )
                
                if success:
                    logger.info(f"Cached {len(api_data)} light historical records for {symbol}")
                else:
                    logger.warning(f"Failed to cache light historical data for {symbol}")
            
            return api_data
        
        except Exception as e:
            logger.error(f"Error in cached get_historical_price_light for {symbol}: {e}")
            # Fall back to direct API call
            return super().get_historical_price_light(symbol, from_date, to_date)
    
    # ========================================================================
    # CACHED FULL HISTORICAL DATA METHODS
    # ========================================================================
    
    def get_historical_price_full(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceFull]:
        """
        Get comprehensive historical price data with caching.
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            list: Historical price data
        """
        if not self.enable_cache or not self.cache_manager:
            # Fall back to direct API call
            return super().get_historical_price_full(symbol, from_date, to_date)
        
        try:
            # Try to get from cache first
            cached_data = self.cache_manager.get_cached_historical_full(
                symbol, from_date, to_date
            )
            
            if cached_data:
                logger.info(f"Serving {len(cached_data)} full historical records from cache for {symbol}")
                return [self._convert_dict_to_full_model(d) for d in cached_data]
            
            # Cache miss - fetch from API
            logger.info(f"Cache miss for full historical data {symbol}, fetching from API")
            api_data = super().get_historical_price_full(symbol, from_date, to_date)
            
            # Cache the results
            if api_data:
                data_dicts = self._convert_models_to_dicts(api_data)
                success, cache_key = self.cache_manager.cache_historical_full(
                    symbol, data_dicts, from_date, to_date
                )
                
                if success:
                    logger.info(f"Cached {len(api_data)} full historical records for {symbol}")
                else:
                    logger.warning(f"Failed to cache full historical data for {symbol}")
            
            return api_data
        
        except Exception as e:
            logger.error(f"Error in cached get_historical_price_full for {symbol}: {e}")
            # Fall back to direct API call
            return super().get_historical_price_full(symbol, from_date, to_date)
    
    def get_historical_price_unadjusted(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceFull]:
        """
        Get unadjusted historical price data with caching.
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            list: Unadjusted historical price data
        """
        if not self.enable_cache or not self.cache_manager:
            # Fall back to direct API call
            return super().get_historical_price_unadjusted(symbol, from_date, to_date)
        
        try:
            # Try to get from cache first (using same full cache with unadjusted flag)
            cached_data = self.cache_manager.get_cached_historical_full(
                symbol, from_date, to_date, unadjusted=True
            )
            
            if cached_data:
                logger.info(f"Serving {len(cached_data)} unadjusted historical records from cache for {symbol}")
                return [self._convert_dict_to_full_model(d) for d in cached_data]
            
            # Cache miss - fetch from API
            logger.info(f"Cache miss for unadjusted historical data {symbol}, fetching from API")
            api_data = super().get_historical_price_unadjusted(symbol, from_date, to_date)
            
            # Cache the results
            if api_data:
                data_dicts = self._convert_models_to_dicts(api_data)
                success, cache_key = self.cache_manager.cache_historical_full(
                    symbol, data_dicts, from_date, to_date, unadjusted=True
                )
                
                if success:
                    logger.info(f"Cached {len(api_data)} unadjusted historical records for {symbol}")
                else:
                    logger.warning(f"Failed to cache unadjusted historical data for {symbol}")
            
            return api_data
        
        except Exception as e:
            logger.error(f"Error in cached get_historical_price_unadjusted for {symbol}: {e}")
            # Fall back to direct API call
            return super().get_historical_price_unadjusted(symbol, from_date, to_date)
    
    def get_historical_price_dividend_adjusted(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[HistoricalPriceFull]:
        """
        Get dividend-adjusted historical price data with caching.
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            
        Returns:
            list: Dividend-adjusted historical price data
        """
        if not self.enable_cache or not self.cache_manager:
            # Fall back to direct API call
            return super().get_historical_price_dividend_adjusted(symbol, from_date, to_date)
        
        try:
            # Try to get from cache first (using same full cache with dividend_adjusted flag)
            cached_data = self.cache_manager.get_cached_historical_full(
                symbol, from_date, to_date, dividend_adjusted=True
            )
            
            if cached_data:
                logger.info(f"Serving {len(cached_data)} dividend-adjusted historical records from cache for {symbol}")
                return [self._convert_dict_to_full_model(d) for d in cached_data]
            
            # Cache miss - fetch from API
            logger.info(f"Cache miss for dividend-adjusted historical data {symbol}, fetching from API")
            api_data = super().get_historical_price_dividend_adjusted(symbol, from_date, to_date)
            
            # Cache the results
            if api_data:
                data_dicts = self._convert_models_to_dicts(api_data)
                success, cache_key = self.cache_manager.cache_historical_full(
                    symbol, data_dicts, from_date, to_date, dividend_adjusted=True
                )
                
                if success:
                    logger.info(f"Cached {len(api_data)} dividend-adjusted historical records for {symbol}")
                else:
                    logger.warning(f"Failed to cache dividend-adjusted historical data for {symbol}")
            
            return api_data
        
        except Exception as e:
            logger.error(f"Error in cached get_historical_price_dividend_adjusted for {symbol}: {e}")
            # Fall back to direct API call
            return super().get_historical_price_dividend_adjusted(symbol, from_date, to_date)
    
    # ========================================================================
    # CACHED INTRADAY DATA METHODS
    # ========================================================================
    
    def _get_cached_intraday(self, symbol: str, interval: str,
                            from_date: Optional[str] = None,
                            to_date: Optional[str] = None) -> List[IntradayPrice]:
        """
        Common method for getting cached intraday data
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval
            from_date (str, optional): Start date
            to_date (str, optional): End date
            
        Returns:
            list: Intraday price data
        """
        # Map interval to API method
        interval_methods = {
            '1min': super().get_historical_price_1min,
            '5min': super().get_historical_price_5min,
            '15min': super().get_historical_price_15min,
            '30min': super().get_historical_price_30min,
            '1hour': super().get_historical_price_1hour,
            '4hour': super().get_historical_price_4hour,
        }
        
        api_method = interval_methods.get(interval)
        if not api_method:
            raise ValueError(f"Unsupported interval: {interval}")
        
        if not self.enable_cache or not self.cache_manager:
            # Fall back to direct API call
            return api_method(symbol, from_date, to_date)
        
        try:
            # Try to get from cache first
            cached_data = self.cache_manager.get_cached_intraday_data(
                symbol, interval, from_date, to_date
            )
            
            if cached_data:
                logger.info(f"Serving {len(cached_data)} {interval} intraday records from cache for {symbol}")
                return [self._convert_dict_to_intraday_model(d) for d in cached_data]
            
            # Cache miss - fetch from API
            logger.info(f"Cache miss for {interval} intraday data {symbol}, fetching from API")
            api_data = api_method(symbol, from_date, to_date)
            
            # Cache the results
            if api_data:
                data_dicts = self._convert_models_to_dicts(api_data)
                success, cache_key = self.cache_manager.cache_intraday_data(
                    symbol, interval, data_dicts, from_date, to_date
                )
                
                if success:
                    logger.info(f"Cached {len(api_data)} {interval} intraday records for {symbol}")
                else:
                    logger.warning(f"Failed to cache {interval} intraday data for {symbol}")
            
            return api_data
        
        except Exception as e:
            logger.error(f"Error in cached {interval} intraday data for {symbol}: {e}")
            # Fall back to direct API call
            return api_method(symbol, from_date, to_date)
    
    def get_historical_price_1min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 1-minute historical price data with caching."""
        return self._get_cached_intraday(symbol, '1min', from_date, to_date)
    
    def get_historical_price_5min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 5-minute historical price data with caching."""
        return self._get_cached_intraday(symbol, '5min', from_date, to_date)
    
    def get_historical_price_15min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 15-minute historical price data with caching."""
        return self._get_cached_intraday(symbol, '15min', from_date, to_date)
    
    def get_historical_price_30min(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 30-minute historical price data with caching."""
        return self._get_cached_intraday(symbol, '30min', from_date, to_date)
    
    def get_historical_price_1hour(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 1-hour historical price data with caching."""
        return self._get_cached_intraday(symbol, '1hour', from_date, to_date)
    
    def get_historical_price_4hour(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[IntradayPrice]:
        """Get 4-hour historical price data with caching."""
        return self._get_cached_intraday(symbol, '4hour', from_date, to_date)
    
    # ========================================================================
    # CACHE MANAGEMENT METHODS
    # ========================================================================
    
    def clear_cache_for_symbol(self, symbol: str) -> bool:
        """
        Clear all cached data for a specific symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            bool: Success status
        """
        if not self.enable_cache or not self.cache_manager:
            return False
        
        return self.cache_manager.invalidate_symbol_cache(symbol)
    
    def get_cache_statistics(self) -> List[dict]:
        """
        Get cache statistics
        
        Returns:
            list: Cache statistics
        """
        if not self.enable_cache or not self.cache_manager:
            return []
        
        return self.cache_manager.get_historical_cache_stats()
    
    def cleanup_expired_cache(self) -> dict:
        """
        Clean up expired cache entries
        
        Returns:
            dict: Cleanup statistics
        """
        if not self.enable_cache or not self.cache_manager:
            return {}
        
        return self.cache_manager.cleanup_historical_cache()
    
    def enable_caching(self) -> None:
        """Enable caching functionality"""
        self.enable_cache = True
        if not self.cache_manager:
            self.cache_manager = get_historical_cache_manager()
    
    def disable_caching(self) -> None:
        """Disable caching functionality"""
        self.enable_cache = False
        self.cache_manager = None