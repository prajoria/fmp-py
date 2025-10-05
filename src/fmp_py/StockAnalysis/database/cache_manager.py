#!/usr/bin/env python3
"""
Cache manager for FMP API responses
Handles caching logic and TTL management
"""

import json
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .connection import get_db

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages cache operations for FMP API responses
    """
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = {
        'quote': 300,  # 5 minutes
        'profile': 86400,  # 24 hours
        'historical': 3600,  # 1 hour
        'financials': 86400,  # 24 hours
        'news': 1800,  # 30 minutes
        'calendar': 3600,  # 1 hour
        'metrics': 86400,  # 24 hours
        'default': 3600  # 1 hour
    }
    
    def __init__(self):
        self.db = get_db()
    
    def _generate_cache_key(self, endpoint: str, symbol: Optional[str] = None, 
                           params: Optional[Dict] = None) -> str:
        """
        Generate a unique cache key
        
        Args:
            endpoint (str): API endpoint
            symbol (str, optional): Stock symbol
            params (dict, optional): Query parameters
            
        Returns:
            str: Cache key
        """
        key_parts = [endpoint]
        if symbol:
            key_parts.append(symbol.upper())
        if params:
            # Sort params for consistent key generation
            param_str = json.dumps(params, sort_keys=True)
            key_parts.append(param_str)
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_ttl(self, endpoint: str) -> int:
        """
        Get TTL for endpoint
        
        Args:
            endpoint (str): API endpoint
            
        Returns:
            int: TTL in seconds
        """
        # Determine cache type from endpoint
        endpoint_lower = endpoint.lower()
        
        if 'quote' in endpoint_lower:
            return self.DEFAULT_TTL['quote']
        elif 'profile' in endpoint_lower or 'executive' in endpoint_lower:
            return self.DEFAULT_TTL['profile']
        elif 'historical' in endpoint_lower or 'price' in endpoint_lower:
            return self.DEFAULT_TTL['historical']
        elif 'income-statement' in endpoint_lower or 'balance-sheet' in endpoint_lower or 'cash-flow' in endpoint_lower:
            return self.DEFAULT_TTL['financials']
        elif 'news' in endpoint_lower:
            return self.DEFAULT_TTL['news']
        elif 'calendar' in endpoint_lower or 'earning' in endpoint_lower or 'dividend' in endpoint_lower:
            return self.DEFAULT_TTL['calendar']
        elif 'ratio' in endpoint_lower or 'metric' in endpoint_lower or 'growth' in endpoint_lower:
            return self.DEFAULT_TTL['metrics']
        else:
            return self.DEFAULT_TTL['default']
    
    def get_cache_metadata(self, cache_key: str) -> Optional[Dict]:
        """
        Get cache metadata
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            dict: Cache metadata or None
        """
        query = """
        SELECT * FROM cache_metadata
        WHERE cache_key = %s
        """
        return self.db.execute_query(query, (cache_key,), fetch='one')
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cache is valid (not expired)
        
        Args:
            cache_key (str): Cache key
            
        Returns:
            bool: True if cache is valid
        """
        metadata = self.get_cache_metadata(cache_key)
        if not metadata:
            return False
        
        expires_at = metadata['expires_at']
        return datetime.now() < expires_at
    
    def update_cache_metadata(self, endpoint: str, symbol: Optional[str] = None,
                            params: Optional[Dict] = None) -> str:
        """
        Update or create cache metadata
        
        Args:
            endpoint (str): API endpoint
            symbol (str, optional): Stock symbol
            params (dict, optional): Query parameters
            
        Returns:
            str: Cache key
        """
        cache_key = self._generate_cache_key(endpoint, symbol, params)
        ttl = self._get_ttl(endpoint)
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        query = """
        INSERT INTO cache_metadata 
        (cache_key, endpoint, symbol, params, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        cached_at = CURRENT_TIMESTAMP,
        expires_at = %s,
        hit_count = hit_count + 1,
        last_hit_at = CURRENT_TIMESTAMP
        """
        
        params_json = json.dumps(params) if params else None
        self.db.execute_update(
            query, 
            (cache_key, endpoint, symbol, params_json, expires_at, expires_at)
        )
        
        return cache_key
    
    def log_api_request(self, endpoint: str, symbol: Optional[str] = None,
                       params: Optional[Dict] = None, from_cache: bool = False,
                       response_status: Optional[int] = None,
                       response_time_ms: Optional[int] = None,
                       error_message: Optional[str] = None):
        """
        Log API request for monitoring
        
        Args:
            endpoint (str): API endpoint
            symbol (str, optional): Stock symbol
            params (dict, optional): Query parameters
            from_cache (bool): Whether response came from cache
            response_status (int, optional): HTTP response status
            response_time_ms (int, optional): Response time in milliseconds
            error_message (str, optional): Error message if any
        """
        query = """
        INSERT INTO api_request_log
        (endpoint, symbol, params, from_cache, response_status, response_time_ms, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params_json = json.dumps(params) if params else None
        
        try:
            self.db.execute_update(
                query,
                (endpoint, symbol, params_json, from_cache, 
                 response_status, response_time_ms, error_message)
            )
        except Exception as e:
            logger.warning(f"Failed to log API request: {e}")
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        queries = [
            "DELETE FROM quotes WHERE expires_at < NOW()",
            "DELETE FROM company_profiles WHERE expires_at < NOW()",
            "DELETE FROM cache_metadata WHERE expires_at < NOW()"
        ]
        
        total_deleted = 0
        for query in queries:
            try:
                deleted = self.db.execute_update(query)
                total_deleted += deleted
                logger.info(f"Deleted {deleted} expired records: {query.split()[2]}")
            except Exception as e:
                logger.error(f"Error cleaning up cache: {e}")
        
        return total_deleted
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Remove old API request logs
        
        Args:
            days (int): Keep logs for this many days
        """
        query = """
        DELETE FROM api_request_log
        WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        
        try:
            deleted = self.db.execute_update(query, (days,))
            logger.info(f"Deleted {deleted} old log entries (>{days} days)")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        stats = {}
        
        # Count records in each table
        tables = [
            'companies', 'company_profiles', 'quotes',
            'historical_prices_daily', 'historical_prices_intraday',
            'income_statements', 'balance_sheets', 'cash_flow_statements',
            'financial_ratios', 'key_metrics', 'financial_growth',
            'stock_news', 'earnings_calendar', 'dividend_calendar'
        ]
        
        for table in tables:
            try:
                result = self.db.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}",
                    fetch='one'
                )
                stats[table] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Error getting count for {table}: {e}")
                stats[table] = 0
        
        # Get cache hit rate
        try:
            hit_rate = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(from_cache) as cache_hits,
                    ROUND(SUM(from_cache) / COUNT(*) * 100, 2) as hit_rate_percent
                FROM api_request_log
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """, fetch='one')
            
            if hit_rate:
                stats['cache_hit_rate_24h'] = hit_rate
        except Exception as e:
            logger.warning(f"Error getting cache hit rate: {e}")
        
        return stats


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
