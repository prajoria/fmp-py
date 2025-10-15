#!/usr/bin/env python3
"""
Historical Charts Cache Manager
Extends base cache manager with specific caching for historical charts data
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from .cache_manager import CacheManager, get_cache_manager
from .historical_charts_dal import HistoricalChartsDAL

logger = logging.getLogger(__name__)


class HistoricalChartsCacheManager(CacheManager):
    """
    Cache manager specifically for historical charts data
    Extends base CacheManager with historical-specific functionality
    """
    
    # TTL values for different chart data types (in seconds)
    HISTORICAL_TTL = {
        'light': 3600,      # 1 hour - basic EOD data
        'full': 3600,       # 1 hour - full EOD data  
        'intraday_1min': 300,   # 5 minutes - 1-minute data
        'intraday_5min': 600,   # 10 minutes - 5-minute data
        'intraday_15min': 900,  # 15 minutes - 15-minute data
        'intraday_30min': 1800, # 30 minutes - 30-minute data
        'intraday_1hour': 3600, # 1 hour - 1-hour data
        'intraday_4hour': 7200, # 2 hours - 4-hour data
        'unadjusted': 86400,    # 24 hours - unadjusted data
        'dividend_adjusted': 86400, # 24 hours - dividend adjusted data
    }
    
    def __init__(self):
        super().__init__()
        self.historical_dal = HistoricalChartsDAL()
    
    def _get_historical_ttl(self, endpoint_type: str, interval: Optional[str] = None) -> int:
        """
        Get TTL for historical chart endpoints
        
        Args:
            endpoint_type (str): Type of endpoint (light, full, intraday)
            interval (str, optional): Time interval for intraday data
            
        Returns:
            int: TTL in seconds
        """
        if endpoint_type == 'intraday' and interval:
            key = f"intraday_{interval}"
            return self.HISTORICAL_TTL.get(key, self.HISTORICAL_TTL['intraday_1hour'])
        
        return self.HISTORICAL_TTL.get(endpoint_type, self.DEFAULT_TTL['historical'])
    
    def generate_historical_cache_key(self, endpoint_type: str, symbol: str,
                                     from_date: Optional[str] = None,
                                     to_date: Optional[str] = None,
                                     interval: Optional[str] = None,
                                     **kwargs) -> str:
        """
        Generate cache key for historical chart data
        
        Args:
            endpoint_type (str): Type of endpoint (light, full, intraday)
            symbol (str): Stock symbol
            from_date (str, optional): Start date
            to_date (str, optional): End date
            interval (str, optional): Time interval for intraday data
            **kwargs: Additional parameters
            
        Returns:
            str: Cache key
        """
        key_parts = [
            'historical_charts',
            endpoint_type,
            symbol.upper()
        ]
        
        if interval:
            key_parts.append(f"interval_{interval}")
        
        if from_date:
            key_parts.append(f"from_{from_date}")
        
        if to_date:
            key_parts.append(f"to_{to_date}")
        
        # Add any additional parameters
        if kwargs:
            param_str = json.dumps(kwargs, sort_keys=True)
            key_parts.append(param_str)
        
        key_string = '|'.join(key_parts)
        import hashlib
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_historical_light(self, symbol: str, data: List[Dict],
                              from_date: Optional[str] = None,
                              to_date: Optional[str] = None,
                              **kwargs) -> Tuple[bool, str]:
        """
        Cache light historical price data
        
        Args:
            symbol (str): Stock symbol
            data (list): Price data from API
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            tuple: (success, cache_key)
        """
        try:
            # Generate cache key
            cache_key = self.generate_historical_cache_key(
                'light', symbol, from_date, to_date, **kwargs
            )
            
            # Get TTL
            ttl = self._get_historical_ttl('light')
            
            # Cache the data
            records_inserted = self.historical_dal.upsert_historical_light(
                symbol, data, ttl
            )
            
            if records_inserted > 0:
                # Update cache metadata
                self.historical_dal.upsert_cache_metadata(
                    cache_key=cache_key,
                    endpoint_type='light',
                    symbol=symbol,
                    params={'from_date': from_date, 'to_date': to_date, **kwargs},
                    record_count=records_inserted,
                    ttl_seconds=ttl,
                    date_from=from_date,
                    date_to=to_date
                )
                
                # Log the request
                self.log_api_request(
                    endpoint='historical-price-light',
                    symbol=symbol,
                    params={'from_date': from_date, 'to_date': to_date, **kwargs},
                    from_cache=False,
                    response_status=200
                )
                
                logger.info(f"Cached {records_inserted} light historical records for {symbol}")
                return True, cache_key
        
        except Exception as e:
            logger.error(f"Error caching light historical data for {symbol}: {e}")
        
        return False, ""
    
    def cache_historical_full(self, symbol: str, data: List[Dict],
                             from_date: Optional[str] = None,
                             to_date: Optional[str] = None,
                             **kwargs) -> Tuple[bool, str]:
        """
        Cache full historical price data
        
        Args:
            symbol (str): Stock symbol
            data (list): Price data from API
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            tuple: (success, cache_key)
        """
        try:
            # Generate cache key
            cache_key = self.generate_historical_cache_key(
                'full', symbol, from_date, to_date, **kwargs
            )
            
            # Get TTL
            ttl = self._get_historical_ttl('full')
            
            # Cache the data
            records_inserted = self.historical_dal.upsert_historical_full(
                symbol, data, ttl
            )
            
            if records_inserted > 0:
                # Update cache metadata
                self.historical_dal.upsert_cache_metadata(
                    cache_key=cache_key,
                    endpoint_type='full',
                    symbol=symbol,
                    params={'from_date': from_date, 'to_date': to_date, **kwargs},
                    record_count=records_inserted,
                    ttl_seconds=ttl,
                    date_from=from_date,
                    date_to=to_date
                )
                
                # Log the request
                self.log_api_request(
                    endpoint='historical-price-full',
                    symbol=symbol,
                    params={'from_date': from_date, 'to_date': to_date, **kwargs},
                    from_cache=False,
                    response_status=200
                )
                
                logger.info(f"Cached {records_inserted} full historical records for {symbol}")
                return True, cache_key
        
        except Exception as e:
            logger.error(f"Error caching full historical data for {symbol}: {e}")
        
        return False, ""
    
    def cache_intraday_data(self, symbol: str, interval: str, data: List[Dict],
                           from_date: Optional[str] = None,
                           to_date: Optional[str] = None,
                           **kwargs) -> Tuple[bool, str]:
        """
        Cache intraday price data
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval
            data (list): Price data from API
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            tuple: (success, cache_key)
        """
        try:
            # Generate cache key
            cache_key = self.generate_historical_cache_key(
                'intraday', symbol, from_date, to_date, interval, **kwargs
            )
            
            # Get TTL
            ttl = self._get_historical_ttl('intraday', interval)
            
            # Cache the data
            records_inserted = self.historical_dal.upsert_intraday_data(
                symbol, interval, data, ttl
            )
            
            if records_inserted > 0:
                # Update cache metadata
                self.historical_dal.upsert_cache_metadata(
                    cache_key=cache_key,
                    endpoint_type='intraday',
                    symbol=symbol,
                    params={'interval': interval, 'from_date': from_date, 
                           'to_date': to_date, **kwargs},
                    record_count=records_inserted,
                    ttl_seconds=ttl,
                    interval=interval,
                    date_from=from_date,
                    date_to=to_date
                )
                
                # Log the request
                self.log_api_request(
                    endpoint=f'historical-price-intraday-{interval}',
                    symbol=symbol,
                    params={'interval': interval, 'from_date': from_date, 
                           'to_date': to_date, **kwargs},
                    from_cache=False,
                    response_status=200
                )
                
                logger.info(f"Cached {records_inserted} {interval} intraday records for {symbol}")
                return True, cache_key
        
        except Exception as e:
            logger.error(f"Error caching intraday data for {symbol} ({interval}): {e}")
        
        return False, ""
    
    def get_cached_historical_light(self, symbol: str,
                                   from_date: Optional[str] = None,
                                   to_date: Optional[str] = None,
                                   **kwargs) -> Optional[List[Dict]]:
        """
        Get cached light historical data
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            list: Cached data or None
        """
        try:
            # Check if we have data in cache
            has_data, count, last_cached = self.historical_dal.check_data_availability(
                symbol, 'light', from_date, to_date
            )
            
            if has_data:
                data = self.historical_dal.get_historical_light(
                    symbol, from_date, to_date, check_expiry=True
                )
                
                if data:
                    # Log cache hit
                    self.log_api_request(
                        endpoint='historical-price-light',
                        symbol=symbol,
                        params={'from_date': from_date, 'to_date': to_date, **kwargs},
                        from_cache=True,
                        response_status=200
                    )
                    
                    logger.info(f"Cache hit: {len(data)} light historical records for {symbol}")
                    return data
        
        except Exception as e:
            logger.error(f"Error getting cached light historical data for {symbol}: {e}")
        
        return None
    
    def get_cached_historical_full(self, symbol: str,
                                  from_date: Optional[str] = None,
                                  to_date: Optional[str] = None,
                                  **kwargs) -> Optional[List[Dict]]:
        """
        Get cached full historical data
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            list: Cached data or None
        """
        try:
            # Check if we have data in cache
            has_data, count, last_cached = self.historical_dal.check_data_availability(
                symbol, 'full', from_date, to_date
            )
            
            if has_data:
                data = self.historical_dal.get_historical_full(
                    symbol, from_date, to_date, check_expiry=True
                )
                
                if data:
                    # Log cache hit
                    self.log_api_request(
                        endpoint='historical-price-full',
                        symbol=symbol,
                        params={'from_date': from_date, 'to_date': to_date, **kwargs},
                        from_cache=True,
                        response_status=200
                    )
                    
                    logger.info(f"Cache hit: {len(data)} full historical records for {symbol}")
                    return data
        
        except Exception as e:
            logger.error(f"Error getting cached full historical data for {symbol}: {e}")
        
        return None
    
    def get_cached_intraday_data(self, symbol: str, interval: str,
                                from_date: Optional[str] = None,
                                to_date: Optional[str] = None,
                                **kwargs) -> Optional[List[Dict]]:
        """
        Get cached intraday data
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval
            from_date (str, optional): Start date
            to_date (str, optional): End date
            **kwargs: Additional parameters
            
        Returns:
            list: Cached data or None
        """
        try:
            # Check if we have data in cache
            has_data, count, last_cached = self.historical_dal.check_data_availability(
                symbol, 'intraday', from_date, to_date, interval
            )
            
            if has_data:
                data = self.historical_dal.get_intraday_data(
                    symbol, interval, from_date, to_date, check_expiry=True
                )
                
                if data:
                    # Log cache hit
                    self.log_api_request(
                        endpoint=f'historical-price-intraday-{interval}',
                        symbol=symbol,
                        params={'interval': interval, 'from_date': from_date,
                               'to_date': to_date, **kwargs},
                        from_cache=True,
                        response_status=200
                    )
                    
                    logger.info(f"Cache hit: {len(data)} {interval} intraday records for {symbol}")
                    return data
        
        except Exception as e:
            logger.error(f"Error getting cached intraday data for {symbol} ({interval}): {e}")
        
        return None
    
    def cleanup_historical_cache(self) -> Dict[str, int]:
        """
        Clean up expired historical charts cache
        
        Returns:
            dict: Cleanup statistics
        """
        try:
            return self.historical_dal.cleanup_expired_cache()
        except Exception as e:
            logger.error(f"Error cleaning up historical cache: {e}")
            return {}
    
    def get_historical_cache_stats(self) -> List[Dict]:
        """
        Get historical cache statistics
        
        Returns:
            list: Cache statistics
        """
        try:
            return self.historical_dal.get_cache_statistics()
        except Exception as e:
            logger.error(f"Error getting historical cache stats: {e}")
            return []
    
    def invalidate_symbol_cache(self, symbol: str) -> bool:
        """
        Invalidate all cache for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            bool: Success status
        """
        try:
            return self.historical_dal.delete_symbol_cache(symbol)
        except Exception as e:
            logger.error(f"Error invalidating cache for {symbol}: {e}")
            return False


# Global historical charts cache manager instance
_historical_cache_manager = None


def get_historical_cache_manager() -> HistoricalChartsCacheManager:
    """Get global historical charts cache manager instance"""
    global _historical_cache_manager
    if _historical_cache_manager is None:
        _historical_cache_manager = HistoricalChartsCacheManager()
    return _historical_cache_manager