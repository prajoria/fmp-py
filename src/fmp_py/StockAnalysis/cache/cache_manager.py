"""
Cache Manager
=============
Intelligent cache validation and management for FMP data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from fmp_py.StockAnalysis.database.connection import get_db


class CacheManager:
    """
    Manages cache validation, expiration, and optimization.
    
    Features:
    - Intelligent cache checking by data type
    - Configurable expiration policies
    - Cache statistics and health monitoring
    - Bulk cache validation
    """
    
    # Default expiration policies (in hours) - Only for existing tables
    EXPIRATION_POLICIES = {
        'historical_prices_daily': 24,  # 1 day for historical prices
        'companies': 8760,  # 1 year for company info
        'company_executives': 8760,  # 1 year for executive info
        'sp500_constituents': 720,  # 1 month for S&P 500 list
        'api_request_log': 168,  # 1 week for API logs
        'fetch_sessions': 168,  # 1 week for fetch sessions
        'fetch_watermarks': 24,  # 1 day for watermarks
    }
    
    def __init__(self):
        self.db = get_db()
    
    def check_data_freshness(self, symbol: str, data_type: str, 
                           start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        Check if cached data is fresh and complete for the given parameters.
        
        Args:
            symbol: Stock symbol
            data_type: Type of data to check (e.g., 'historical_prices_daily', 'companies')
            start_date: Start date for date-range data
            end_date: End date for date-range data
        
        Returns:
            Dict with cache status information
        """
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'missing_dates': [],
            'last_updated': None,
            'expires_at': None,
            'needs_refresh': True
        }
        
        try:
            if data_type in ['companies', 'company_executives']:
                # Single record data types
                result = self._check_single_record_cache(symbol, data_type)
            
            elif data_type in ['historical_prices_daily']:
                # Date-range data types
                if start_date and end_date:
                    result = self._check_date_range_cache(symbol, data_type, start_date, end_date)
            
            elif data_type in ['sp500_constituents']:
                # S&P 500 constituents (symbol-based lookup)
                result = self._check_sp500_cache(symbol, data_type)
            
        except Exception as e:
            print(f"Warning: Error checking cache for {symbol} {data_type}: {e}")
        
        return result
    
    def _check_single_record_cache(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """Check cache for single-record data types (companies, executives)"""
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'last_updated': None,
            'expires_at': None,
            'needs_refresh': True
        }
        
        # Get expiration policy
        expiration_hours = self.EXPIRATION_POLICIES.get(data_type, 24)
        
        # For companies and executives, check updated_at instead of expires_at
        if data_type in ['companies', 'company_executives']:
            cached_data = self.db.execute_query(f"""
                SELECT updated_at, COUNT(*) as count
                FROM {data_type}
                WHERE symbol = %s
                GROUP BY updated_at
                ORDER BY updated_at DESC
                LIMIT 1
            """, (symbol,), fetch='one')
            
            if cached_data and cached_data['count'] > 0:
                result['cached_count'] = cached_data['count']
                result['last_updated'] = cached_data['updated_at']
                
                # Check if still fresh (based on expiration policy)
                expiry_time = cached_data['updated_at'] + timedelta(hours=expiration_hours)
                if expiry_time > datetime.now():
                    result['is_fresh'] = True
                    result['is_complete'] = True
                    result['needs_refresh'] = False
                    result['expires_at'] = expiry_time
        
        return result
    
    def _check_sp500_cache(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """Check cache for S&P 500 constituents data"""
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'last_updated': None,
            'expires_at': None,
            'needs_refresh': True
        }
        
        # Get expiration policy
        expiration_hours = self.EXPIRATION_POLICIES.get(data_type, 720)  # Default 1 month
        
        cached_data = self.db.execute_query(f"""
            SELECT updated_at, COUNT(*) as count
            FROM {data_type}
            WHERE symbol = %s AND is_active = TRUE
            GROUP BY updated_at
            ORDER BY updated_at DESC
            LIMIT 1
        """, (symbol,), fetch='one')
        
        if cached_data and cached_data['count'] > 0:
            result['cached_count'] = cached_data['count']
            result['last_updated'] = cached_data['updated_at']
            
            # Check if still fresh
            expiry_time = cached_data['updated_at'] + timedelta(hours=expiration_hours)
            if expiry_time > datetime.now():
                result['is_fresh'] = True
                result['is_complete'] = True
                result['needs_refresh'] = False
                result['expires_at'] = expiry_time
                result['is_complete'] = True
                result['needs_refresh'] = False
        
        return result
    
    def _check_date_range_cache(self, symbol: str, data_type: str, 
                               start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Check cache for date-range data types (historical prices)"""
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'missing_dates': [],
            'last_updated': None,
            'needs_refresh': True
        }
        
        # Get cached data count and date range
        cached_info = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as count,
                MIN(date) as min_date,
                MAX(date) as max_date,
                MAX(cached_at) as last_updated
            FROM {data_type}
            WHERE symbol = %s AND date >= %s AND date <= %s
        """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), fetch='one')
        
        if cached_info and cached_info['count'] > 0:
            result['cached_count'] = cached_info['count']
            result['last_updated'] = cached_info['last_updated']
            
            # Check completeness for trading days
            expected_days = self._estimate_trading_days(start_date, end_date)
            completeness_ratio = cached_info['count'] / expected_days if expected_days > 0 else 0
            
            # Consider complete if we have at least 90% of expected trading days
            result['is_complete'] = completeness_ratio >= 0.9
            
            # Check freshness (data should be updated daily)
            expiration_hours = self.EXPIRATION_POLICIES.get(data_type, 24)
            freshness_threshold = datetime.now() - timedelta(hours=expiration_hours)
            result['is_fresh'] = cached_info['last_updated'] > freshness_threshold
            
            result['needs_refresh'] = not (result['is_fresh'] and result['is_complete'])
            
            # Find missing dates if incomplete
            if not result['is_complete']:
                result['missing_dates'] = self._find_missing_dates(
                    symbol, data_type, start_date, end_date
                )
        
        return result
    
    def _check_annual_statements_cache(self, symbol: str, data_type: str,
                                     start_date: datetime = None, 
                                     end_date: datetime = None) -> Dict[str, Any]:
        """Check cache for annual financial statements"""
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'last_updated': None,
            'needs_refresh': True
        }
        
        # For annual statements, we typically want last 5-10 years
        if not start_date:
            start_date = datetime.now() - timedelta(days=365 * 10)  # 10 years back
        if not end_date:
            end_date = datetime.now()
        
        cached_info = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as count,
                MAX(cached_at) as last_updated,
                GROUP_CONCAT(DISTINCT calendar_year ORDER BY calendar_year) as years
            FROM {data_type}
            WHERE symbol = %s AND period = 'FY'
            AND date >= %s AND date <= %s
        """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), fetch='one')
        
        if cached_info and cached_info['count'] > 0:
            result['cached_count'] = cached_info['count']
            result['last_updated'] = cached_info['last_updated']
            
            # Annual statements don't change often, so 1 week freshness is ok
            freshness_threshold = datetime.now() - timedelta(hours=168)  # 1 week
            result['is_fresh'] = cached_info['last_updated'] > freshness_threshold
            
            # We expect at least 5 years of data for completeness
            result['is_complete'] = cached_info['count'] >= 5
            
            result['needs_refresh'] = not (result['is_fresh'] and result['is_complete'])
        
        return result
    
    def _check_news_cache(self, symbol: str, since_date: datetime) -> Dict[str, Any]:
        """Check cache for news data"""
        result = {
            'is_fresh': False,
            'is_complete': False,
            'cached_count': 0,
            'last_updated': None,
            'needs_refresh': True
        }
        
        cached_info = self.db.execute_query("""
            SELECT 
                COUNT(*) as count,
                MAX(cached_at) as last_updated,
                MAX(published_date) as latest_news
            FROM stock_news
            WHERE symbol = %s AND published_date >= %s
        """, (symbol, since_date.strftime('%Y-%m-%d')), fetch='one')
        
        if cached_info and cached_info['count'] > 0:
            result['cached_count'] = cached_info['count']
            result['last_updated'] = cached_info['last_updated']
            
            # News should be refreshed every 3 hours
            freshness_threshold = datetime.now() - timedelta(hours=3)
            result['is_fresh'] = cached_info['last_updated'] > freshness_threshold
            
            # Consider complete if we have any recent news
            result['is_complete'] = cached_info['count'] > 0
            
            result['needs_refresh'] = not result['is_fresh']
        
        return result
    
    def _estimate_trading_days(self, start_date: datetime, end_date: datetime) -> int:
        """Estimate number of trading days between dates"""
        total_days = (end_date - start_date).days + 1
        weeks = total_days // 7
        remaining_days = total_days % 7
        
        # Approximate: 5 trading days per week
        trading_days = weeks * 5
        
        # Add remaining days (max 5 for partial week)
        if remaining_days > 0:
            # Simple approximation: weekdays only
            trading_days += min(remaining_days, 5)
        
        return max(trading_days, 1)
    
    def _find_missing_dates(self, symbol: str, data_type: str, 
                           start_date: datetime, end_date: datetime) -> List[str]:
        """Find missing dates in cached data range"""
        try:
            cached_dates = self.db.execute_query(f"""
                SELECT DISTINCT date
                FROM {data_type}
                WHERE symbol = %s AND date >= %s AND date <= %s
                ORDER BY date
            """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), fetch='all')
            
            if not cached_dates:
                return []
            
            cached_set = set(row['date'].strftime('%Y-%m-%d') for row in cached_dates)
            
            # Generate expected dates (trading days only, rough estimate)
            missing_dates = []
            current = start_date
            while current <= end_date:
                # Skip weekends (simple approximation)
                if current.weekday() < 5:  # Monday=0, Sunday=6
                    date_str = current.strftime('%Y-%m-%d')
                    if date_str not in cached_set:
                        missing_dates.append(date_str)
                current += timedelta(days=1)
            
            return missing_dates[:10]  # Return first 10 missing dates
            
        except Exception as e:
            print(f"Warning: Error finding missing dates: {e}")
            return []
    
    def get_cache_statistics(self, symbol: str = None) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'total_symbols': 0,
            'total_records': 0,
            'data_types': {},
            'freshness_summary': {},
            'storage_info': {}
        }
        
        try:
            # Total symbols
            symbol_filter = f"WHERE symbol = '{symbol}'" if symbol else ""
            
            # Get counts by table
            for data_type in self.EXPIRATION_POLICIES.keys():
                try:
                    count_query = f"SELECT COUNT(*) as count FROM {data_type} {symbol_filter}"
                    result = self.db.execute_query(count_query, fetch='one')
                    if result:
                        stats['data_types'][data_type] = result['count']
                        stats['total_records'] += result['count']
                except Exception:
                    stats['data_types'][data_type] = 0
            
            # Get unique symbols count
            symbols_query = "SELECT COUNT(DISTINCT symbol) as count FROM companies"
            result = self.db.execute_query(symbols_query, fetch='one')
            if result:
                stats['total_symbols'] = result['count']
            
            # Get freshness summary
            for data_type in ['historical_prices_daily']:  # Only existing tables with cache expiry
                try:
                    expiration_hours = self.EXPIRATION_POLICIES.get(data_type, 24)
                    freshness_query = f"""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN cached_at > DATE_SUB(NOW(), INTERVAL {expiration_hours} HOUR) THEN 1 ELSE 0 END) as fresh
                        FROM {data_type} {symbol_filter}
                    """
                    result = self.db.execute_query(freshness_query, fetch='one')
                    if result and result['total'] > 0:
                        fresh_percentage = (result['fresh'] / result['total']) * 100
                        stats['freshness_summary'][data_type] = {
                            'total': result['total'],
                            'fresh': result['fresh'],
                            'fresh_percentage': fresh_percentage
                        }
                except Exception:
                    pass
            
        except Exception as e:
            print(f"Warning: Error getting cache statistics: {e}")
        
        return stats
    
    def cleanup_expired_data(self, dry_run: bool = True) -> Dict[str, int]:
        """
        Clean up expired cache data.
        
        Args:
            dry_run: If True, only count what would be deleted
        
        Returns:
            Dict with counts of deleted records by table
        """
        deleted_counts = {}
        
        for data_type, expiration_hours in self.EXPIRATION_POLICIES.items():
            try:
                # Check for expired records
                count_query = f"""
                    SELECT COUNT(*) as count FROM {data_type}
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """
                result = self.db.execute_query(count_query, fetch='one')
                expired_count = result['count'] if result else 0
                
                if expired_count > 0:
                    if not dry_run:
                        # Delete expired records
                        delete_query = f"""
                            DELETE FROM {data_type}
                            WHERE expires_at IS NOT NULL AND expires_at < NOW()
                        """
                        self.db.execute_update(delete_query)
                        print(f"Deleted {expired_count} expired records from {data_type}")
                    else:
                        print(f"Would delete {expired_count} expired records from {data_type}")
                    
                    deleted_counts[data_type] = expired_count
            
            except Exception as e:
                print(f"Warning: Error cleaning up {data_type}: {e}")
        
        return deleted_counts
    
    def bulk_validate_cache(self, symbols: List[str], data_types: List[str], 
                           start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Dict]]:
        """
        Validate cache for multiple symbols and data types in bulk.
        
        Returns:
            Nested dict: symbol -> data_type -> cache_status
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = {}
            for data_type in data_types:
                results[symbol][data_type] = self.check_data_freshness(
                    symbol, data_type, start_date, end_date
                )
        
        return results