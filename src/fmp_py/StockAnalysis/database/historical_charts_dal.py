#!/usr/bin/env python3
"""
Historical Charts Data Access Layer (DAL)
Provides CRUD operations for historical charts cache tables
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from .connection import get_db
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


class HistoricalChartsDAL:
    """Data access layer for historical charts data"""
    
    def __init__(self):
        self.db = get_db()
        self.cache_manager = get_cache_manager()
    
    # ========================================================================
    # LIGHT HISTORICAL DATA METHODS
    # ========================================================================
    
    def upsert_historical_light(self, symbol: str, prices_data: List[Dict],
                               ttl_seconds: int = 3600) -> int:
        """
        Insert or update light historical price data
        
        Args:
            symbol (str): Stock symbol
            prices_data (list): List of price dictionaries
            ttl_seconds (int): Time to live in seconds
            
        Returns:
            int: Number of records inserted/updated
        """
        if not prices_data:
            return 0
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO historical_charts_light
        (symbol, date, `open`, high, low, `close`, volume, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `open` = VALUES(`open`),
        high = VALUES(high),
        low = VALUES(low),
        `close` = VALUES(`close`),
        volume = VALUES(volume),
        cached_at = CURRENT_TIMESTAMP,
        expires_at = VALUES(expires_at)
        """
        
        try:
            params_list = [
                (
                    symbol.upper(),
                    price.get('date'),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume'),
                    expires_at
                )
                for price in prices_data
            ]
            
            return self.db.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"Error upserting light historical data for {symbol}: {e}")
            return 0
    
    def get_historical_light(self, symbol: str, from_date: Optional[str] = None,
                            to_date: Optional[str] = None, 
                            check_expiry: bool = True) -> List[Dict]:
        """
        Get light historical price data
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            check_expiry (bool): Check if cache is expired
            
        Returns:
            list: Historical price data
        """
        query = """
        SELECT symbol, date, `open`, high, low, `close`, volume, cached_at
        FROM historical_charts_light
        WHERE symbol = %s
        """
        params = [symbol.upper()]
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        if from_date:
            query += " AND date >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND date <= %s"
            params.append(to_date)
        
        query += " ORDER BY date DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    # ========================================================================
    # FULL HISTORICAL DATA METHODS
    # ========================================================================
    
    def upsert_historical_full(self, symbol: str, prices_data: List[Dict],
                              ttl_seconds: int = 3600) -> int:
        """
        Insert or update full historical price data
        
        Args:
            symbol (str): Stock symbol
            prices_data (list): List of price dictionaries
            ttl_seconds (int): Time to live in seconds
            
        Returns:
            int: Number of records inserted/updated
        """
        if not prices_data:
            return 0
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO historical_charts_full
        (symbol, date, `open`, high, low, `close`, adj_close, volume,
         unadjusted_volume, `change`, change_percent, vwap, label, 
         change_over_time, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `open` = VALUES(`open`),
        high = VALUES(high),
        low = VALUES(low),
        `close` = VALUES(`close`),
        adj_close = VALUES(adj_close),
        volume = VALUES(volume),
        unadjusted_volume = VALUES(unadjusted_volume),
        `change` = VALUES(`change`),
        change_percent = VALUES(change_percent),
        vwap = VALUES(vwap),
        label = VALUES(label),
        change_over_time = VALUES(change_over_time),
        cached_at = CURRENT_TIMESTAMP,
        expires_at = VALUES(expires_at)
        """
        
        try:
            params_list = [
                (
                    symbol.upper(),
                    price.get('date'),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('adjClose'),
                    price.get('volume'),
                    price.get('unadjustedVolume'),
                    price.get('change'),
                    price.get('changePercent'),
                    price.get('vwap'),
                    price.get('label'),
                    price.get('changeOverTime'),
                    expires_at
                )
                for price in prices_data
            ]
            
            return self.db.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"Error upserting full historical data for {symbol}: {e}")
            return 0
    
    def get_historical_full(self, symbol: str, from_date: Optional[str] = None,
                           to_date: Optional[str] = None,
                           check_expiry: bool = True) -> List[Dict]:
        """
        Get full historical price data
        
        Args:
            symbol (str): Stock symbol
            from_date (str, optional): Start date (YYYY-MM-DD)
            to_date (str, optional): End date (YYYY-MM-DD)
            check_expiry (bool): Check if cache is expired
            
        Returns:
            list: Historical price data
        """
        query = """
        SELECT symbol, date, `open`, high, low, `close`, adj_close, volume,
               unadjusted_volume, `change`, change_percent, vwap, label,
               change_over_time, cached_at
        FROM historical_charts_full
        WHERE symbol = %s
        """
        params = [symbol.upper()]
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        if from_date:
            query += " AND date >= %s"
            params.append(from_date)
        
        if to_date:
            query += " AND date <= %s"
            params.append(to_date)
        
        query += " ORDER BY date DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    # ========================================================================
    # INTRADAY DATA METHODS
    # ========================================================================
    
    def upsert_intraday_data(self, symbol: str, interval: str, 
                            prices_data: List[Dict],
                            ttl_seconds: int = 900) -> int:
        """
        Insert or update intraday price data
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval (1min, 5min, 15min, 30min, 1hour, 4hour)
            prices_data (list): List of price dictionaries
            ttl_seconds (int): Time to live in seconds
            
        Returns:
            int: Number of records inserted/updated
        """
        if not prices_data:
            return 0
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO historical_charts_intraday
        (symbol, datetime, `interval`, `open`, high, low, `close`, volume, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `open` = VALUES(`open`),
        high = VALUES(high),
        low = VALUES(low),
        `close` = VALUES(`close`),
        volume = VALUES(volume),
        cached_at = CURRENT_TIMESTAMP,
        expires_at = VALUES(expires_at)
        """
        
        try:
            params_list = [
                (
                    symbol.upper(),
                    price.get('date'),  # This contains datetime for intraday
                    interval,
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume'),
                    expires_at
                )
                for price in prices_data
            ]
            
            return self.db.execute_many(query, params_list)
        except Exception as e:
            logger.error(f"Error upserting intraday data for {symbol} ({interval}): {e}")
            return 0
    
    def get_intraday_data(self, symbol: str, interval: str,
                         from_datetime: Optional[str] = None,
                         to_datetime: Optional[str] = None,
                         check_expiry: bool = True) -> List[Dict]:
        """
        Get intraday price data
        
        Args:
            symbol (str): Stock symbol
            interval (str): Time interval
            from_datetime (str, optional): Start datetime (YYYY-MM-DD HH:MM:SS)
            to_datetime (str, optional): End datetime (YYYY-MM-DD HH:MM:SS)
            check_expiry (bool): Check if cache is expired
            
        Returns:
            list: Intraday price data
        """
        query = """
        SELECT symbol, datetime, `interval`, `open`, high, low, `close`, 
               volume, cached_at
        FROM historical_charts_intraday
        WHERE symbol = %s AND `interval` = %s
        """
        params = [symbol.upper(), interval]
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        if from_datetime:
            query += " AND datetime >= %s"
            params.append(from_datetime)
        
        if to_datetime:
            query += " AND datetime <= %s"
            params.append(to_datetime)
        
        query += " ORDER BY datetime DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    # ========================================================================
    # CACHE METADATA METHODS
    # ========================================================================
    
    def upsert_cache_metadata(self, cache_key: str, endpoint_type: str,
                             symbol: str, params: Dict, record_count: int,
                             ttl_seconds: int, interval: Optional[str] = None,
                             date_from: Optional[str] = None,
                             date_to: Optional[str] = None) -> bool:
        """
        Insert or update cache metadata
        
        Args:
            cache_key (str): Unique cache key
            endpoint_type (str): Type of endpoint (light, full, intraday)
            symbol (str): Stock symbol
            params (dict): Request parameters
            record_count (int): Number of records cached
            ttl_seconds (int): Time to live in seconds
            interval (str, optional): Time interval for intraday data
            date_from (str, optional): Start date
            date_to (str, optional): End date
            
        Returns:
            bool: Success status
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        query = """
        INSERT INTO historical_charts_cache_metadata
        (cache_key, endpoint_type, symbol, `interval`, date_from, date_to,
         params, record_count, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        endpoint_type = VALUES(endpoint_type),
        symbol = VALUES(symbol),
        `interval` = VALUES(`interval`),
        date_from = VALUES(date_from),
        date_to = VALUES(date_to),
        params = VALUES(params),
        record_count = VALUES(record_count),
        cached_at = CURRENT_TIMESTAMP,
        expires_at = VALUES(expires_at),
        hit_count = hit_count + 1,
        last_hit_at = CURRENT_TIMESTAMP
        """
        
        try:
            import json
            self.db.execute_update(query, (
                cache_key,
                endpoint_type,
                symbol.upper(),
                interval,
                date_from,
                date_to,
                json.dumps(params),
                record_count,
                expires_at
            ))
            return True
        except Exception as e:
            logger.error(f"Error upserting cache metadata for {cache_key}: {e}")
            return False
    
    def get_cache_metadata(self, cache_key: str, 
                          check_expiry: bool = True) -> Optional[Dict]:
        """
        Get cache metadata by key
        
        Args:
            cache_key (str): Cache key
            check_expiry (bool): Check if cache is expired
            
        Returns:
            dict: Cache metadata or None
        """
        query = """
        SELECT * FROM historical_charts_cache_metadata
        WHERE cache_key = %s
        """
        
        if check_expiry:
            query += " AND expires_at > NOW()"
        
        return self.db.execute_query(query, (cache_key,), fetch='one')
    
    def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        Clean up expired cache entries
        
        Returns:
            dict: Cleanup statistics
        """
        try:
            # Call the stored procedure
            result = self.db.execute_query("CALL CleanupExpiredHistoricalCharts()")
            
            # Convert result to dictionary
            stats = {}
            for row in result:
                stats[row['table_name']] = row['remaining_records']
            
            return stats
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return {}
    
    def get_cache_statistics(self) -> List[Dict]:
        """
        Get cache statistics
        
        Returns:
            list: Cache statistics
        """
        try:
            return self.db.execute_query("CALL GetHistoricalChartsCacheStats()")
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return []
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def check_data_availability(self, symbol: str, endpoint_type: str,
                               from_date: Optional[str] = None,
                               to_date: Optional[str] = None,
                               interval: Optional[str] = None) -> Tuple[bool, int, datetime]:
        """
        Check if data is available in cache
        
        Args:
            symbol (str): Stock symbol
            endpoint_type (str): Type of endpoint (light, full, intraday)
            from_date (str, optional): Start date
            to_date (str, optional): End date
            interval (str, optional): Time interval for intraday data
            
        Returns:
            tuple: (has_data, record_count, last_cached)
        """
        table_map = {
            'light': 'historical_charts_light',
            'full': 'historical_charts_full',
            'intraday': 'historical_charts_intraday'
        }
        
        table = table_map.get(endpoint_type)
        if not table:
            return False, 0, datetime.min
        
        query = f"""
        SELECT COUNT(*) as count, MAX(cached_at) as last_cached
        FROM {table}
        WHERE symbol = %s AND expires_at > NOW()
        """
        params = [symbol.upper()]
        
        if endpoint_type == 'intraday' and interval:
            query += " AND `interval` = %s"
            params.append(interval)
        
        if from_date:
            date_field = 'datetime' if endpoint_type == 'intraday' else 'date'
            query += f" AND {date_field} >= %s"
            params.append(from_date)
        
        if to_date:
            date_field = 'datetime' if endpoint_type == 'intraday' else 'date'
            query += f" AND {date_field} <= %s"
            params.append(to_date)
        
        try:
            result = self.db.execute_query(query, tuple(params), fetch='one')
            if result:
                return (
                    result['count'] > 0,
                    result['count'],
                    result['last_cached'] or datetime.min
                )
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
        
        return False, 0, datetime.min
    
    def delete_symbol_cache(self, symbol: str) -> bool:
        """
        Delete all cached data for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            bool: Success status
        """
        try:
            symbol_upper = symbol.upper()
            
            # Delete from all tables
            self.db.execute_update(
                "DELETE FROM historical_charts_light WHERE symbol = %s",
                (symbol_upper,)
            )
            self.db.execute_update(
                "DELETE FROM historical_charts_full WHERE symbol = %s",
                (symbol_upper,)
            )
            self.db.execute_update(
                "DELETE FROM historical_charts_intraday WHERE symbol = %s",
                (symbol_upper,)
            )
            self.db.execute_update(
                "DELETE FROM historical_charts_cache_metadata WHERE symbol = %s",
                (symbol_upper,)
            )
            
            return True
        except Exception as e:
            logger.error(f"Error deleting cache for symbol {symbol}: {e}")
            return False


# Create global instance
historical_charts_dal = HistoricalChartsDAL()