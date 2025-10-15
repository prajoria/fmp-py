#!/usr/bin/env python3
"""
Generic Stock Data Fetcher
===========================
Fetches comprehensive stock data with intelligent caching and date range support.
Supports single stocks or batch processing from file input.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmp_py.StockAnalysis.database.connection import get_db
from utils.date_utils import parse_date_range, format_date


class StockDataFetcher:
    """
    Generic stock data fetcher with intelligent caching.
    
    Features:
    - Single stock or batch processing from file
    - Date range filtering
    - Smart cache checking to avoid unnecessary API calls
    - Comprehensive FMP data coverage
    - Rate limiting and error handling
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the fetcher with API key and database connection"""
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY not found in environment variables")
        
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.db = get_db()
        self.session = requests.Session()
        
        # Rate limiting
        self.requests_per_minute = 300  # FMP limit
        self.request_interval = 60 / self.requests_per_minute
        self.last_request_time = 0
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'symbols_processed': 0,
            'errors': 0
        }
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling and rate limiting"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        request_params = {'apikey': self.api_key}
        if params:
            request_params.update(params)
        
        try:
            print(f"📡 API Call: {endpoint}")
            response = self.session.get(url, params=request_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.stats['api_calls'] += 1
            
            # Log API request
            self._log_api_request(endpoint, response.status_code, 
                                len(data) if isinstance(data, list) else 1)
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API request failed: {e}")
            self.stats['errors'] += 1
            self._log_api_request(endpoint, getattr(e.response, 'status_code', 0), 0, str(e))
            return None
        except Exception as e:
            print(f"   ❌ Error processing response: {e}")
            self.stats['errors'] += 1
            return None
    
    def _log_api_request(self, endpoint: str, status_code: int, record_count: int, error_message: str = None):
        """Log API request for monitoring"""
        try:
            self.db.execute_update("""
                INSERT INTO api_request_log (endpoint, symbol, response_status, from_cache, 
                                           record_count, error_message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (endpoint, 'BATCH', status_code, False, record_count, error_message))
        except Exception as e:
            print(f"Warning: Could not log API request: {e}")
    
    def _check_cache_coverage(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict[str, bool]:
        """
        Check what data is already cached for the symbol within date range.
        Returns dict of data types and their cache status.
        """
        coverage = {
            'profile': False,
            'quote': False,
            'income_statements': False,
            'balance_sheets': False,
            'cash_flow_statements': False,
            'financial_ratios': False,
            'key_metrics': False,
            'historical_prices': False,
            'news': False
        }
        
        try:
            # Check profile (doesn't expire often)
            profile_cached = self.db.execute_query("""
                SELECT COUNT(*) as count FROM company_profiles 
                WHERE symbol = %s AND expires_at > NOW()
            """, (symbol,), fetch='one')
            coverage['profile'] = profile_cached['count'] > 0
            
            # Check quote (expires in 5 minutes)
            quote_cached = self.db.execute_query("""
                SELECT COUNT(*) as count FROM quotes 
                WHERE symbol = %s AND expires_at > NOW()
            """, (symbol,), fetch='one')
            coverage['quote'] = quote_cached['count'] > 0
            
            # Check financial statements (annual data)
            for statement_type in ['income_statements', 'balance_sheets', 'cash_flow_statements']:
                cached = self.db.execute_query(f"""
                    SELECT COUNT(*) as count FROM {statement_type} 
                    WHERE symbol = %s AND date >= %s AND date <= %s
                """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), fetch='one')
                coverage[statement_type] = cached['count'] > 0
            
            # Check historical prices
            price_cached = self.db.execute_query("""
                SELECT COUNT(*) as count FROM historical_prices_daily 
                WHERE symbol = %s AND date >= %s AND date <= %s
            """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), fetch='one')
            coverage['historical_prices'] = price_cached['count'] > 0
            
            # Check news (last 30 days)
            news_start = max(start_date, datetime.now() - timedelta(days=30))
            news_cached = self.db.execute_query("""
                SELECT COUNT(*) as count FROM stock_news 
                WHERE symbol = %s AND published_date >= %s
            """, (symbol, news_start.strftime('%Y-%m-%d')), fetch='one')
            coverage['news'] = news_cached['count'] > 0
            
        except Exception as e:
            print(f"Warning: Error checking cache coverage: {e}")
        
        return coverage
    
    def _get_symbols_list(self, input_source: Union[str, List[str]]) -> List[str]:
        """
        Parse input source to get list of symbols.
        Input can be:
        - Single symbol string
        - List of symbols
        - Path to file with symbols (one per line)
        """
        if isinstance(input_source, list):
            return [s.upper().strip() for s in input_source]
        
        if isinstance(input_source, str):
            # Check if it's a file path
            if os.path.isfile(input_source):
                try:
                    with open(input_source, 'r') as f:
                        symbols = []
                        for line in f:
                            line = line.strip().upper()
                            if line and not line.startswith('#'):
                                # Handle comma-separated or space-separated
                                if ',' in line:
                                    symbols.extend([s.strip() for s in line.split(',') if s.strip()])
                                else:
                                    symbols.append(line)
                        return symbols
                except Exception as e:
                    print(f"❌ Error reading symbols file: {e}")
                    return []
            else:
                # Single symbol
                return [input_source.upper().strip()]
        
        return []
    
    def fetch_company_profile(self, symbol: str) -> bool:
        """Fetch and store company profile"""
        if not symbol:
            return False
        
        data = self._make_request(f"profile/{symbol}")
        if not data or len(data) == 0:
            return False
        
        profile = data[0]
        
        try:
            # Insert/update company
            self.db.execute_update("""
                INSERT INTO companies (symbol, name, exchange, exchange_short_name, type, currency, country, is_etf, is_actively_trading)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name), exchange = VALUES(exchange), exchange_short_name = VALUES(exchange_short_name),
                type = VALUES(type), currency = VALUES(currency), country = VALUES(country),
                is_etf = VALUES(is_etf), is_actively_trading = VALUES(is_actively_trading), updated_at = NOW()
            """, (
                profile.get('symbol'),
                profile.get('companyName'),
                profile.get('exchangeShortName'),
                profile.get('exchangeShortName'),
                'stock',
                profile.get('currency'),
                profile.get('country'),
                False,
                True
            ))
            
            # Insert/update company profile
            self.db.execute_update("""
                INSERT INTO company_profiles (
                    symbol, company_name, price, beta, vol_avg, mkt_cap, last_div, `range`, changes,
                    cik, isin, cusip, industry, sector, website, description, ceo, full_time_employees,
                    address, city, state, zip, country, phone, image, ipo_date, default_image, is_adr,
                    dcf, dcf_diff, cached_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 24 HOUR))
                ON DUPLICATE KEY UPDATE
                company_name = VALUES(company_name), price = VALUES(price), beta = VALUES(beta),
                vol_avg = VALUES(vol_avg), mkt_cap = VALUES(mkt_cap), last_div = VALUES(last_div),
                `range` = VALUES(`range`), changes = VALUES(changes), industry = VALUES(industry),
                sector = VALUES(sector), website = VALUES(website), description = VALUES(description),
                ceo = VALUES(ceo), full_time_employees = VALUES(full_time_employees),
                cached_at = NOW(), expires_at = DATE_ADD(NOW(), INTERVAL 24 HOUR)
            """, (
                profile.get('symbol'),
                profile.get('companyName'),
                profile.get('price'),
                profile.get('beta'),
                profile.get('volAvg'),
                profile.get('mktCap'),
                profile.get('lastDiv'),
                profile.get('range'),
                profile.get('changes'),
                profile.get('cik'),
                profile.get('isin'),
                profile.get('cusip'),
                profile.get('industry'),
                profile.get('sector'),
                profile.get('website'),
                profile.get('description'),
                profile.get('ceo'),
                profile.get('fullTimeEmployees'),
                profile.get('address'),
                profile.get('city'),
                profile.get('state'),
                profile.get('zip'),
                profile.get('country'),
                profile.get('phone'),
                profile.get('image'),
                profile.get('ipoDate'),
                profile.get('defaultImage', False),
                profile.get('isAdr', False),
                profile.get('dcf'),
                profile.get('dcfDiff')
            ))
            
            print(f"   ✅ Stored profile for {profile.get('companyName')} ({profile.get('symbol')})")
            return True
            
        except Exception as e:
            print(f"   ❌ Error storing company profile: {e}")
            return False
    
    def fetch_historical_prices(self, symbol: str, start_date: datetime, end_date: datetime) -> bool:
        """Fetch and store historical prices for date range"""
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        data = self._make_request(f"historical-price-full/{symbol}", params)
        if not data or 'historical' not in data:
            return False
        
        historical_data = data['historical']
        stored_count = 0
        
        for price_data in historical_data:
            try:
                self.db.execute_update("""
                    INSERT INTO historical_prices_daily (
                        symbol, date, `open`, high, low, `close`, adj_close, volume, unadjusted_volume,
                        `change`, change_percent, vwap, label, change_over_time, cached_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    `close` = VALUES(`close`), volume = VALUES(volume), cached_at = NOW()
                """, (
                    symbol, price_data.get('date'), price_data.get('open'), price_data.get('high'),
                    price_data.get('low'), price_data.get('close'), price_data.get('adjClose'),
                    price_data.get('volume'), price_data.get('unadjustedVolume'), price_data.get('change'),
                    price_data.get('changePercent'), price_data.get('vwap'), price_data.get('label'),
                    price_data.get('changeOverTime')
                ))
                stored_count += 1
                
            except Exception as e:
                print(f"   ⚠️ Error storing historical price: {e}")
                continue
        
        print(f"   ✅ Stored {stored_count} historical price records")
        return stored_count > 0
    
    def fetch_symbol_data(self, symbol: str, start_date: datetime, end_date: datetime, 
                         force_refresh: bool = False) -> Dict[str, bool]:
        """
        Fetch comprehensive data for a single symbol.
        Returns dict of what was successfully fetched/cached.
        """
        print(f"\n🎯 Processing: {symbol}")
        print("=" * 50)
        
        # Check cache coverage unless force refresh
        coverage = {} if force_refresh else self._check_cache_coverage(symbol, start_date, end_date)
        results = {}
        
        # Fetch company profile if not cached
        if force_refresh or not coverage.get('profile', False):
            print("🏢 Fetching Company Profile...")
            results['profile'] = self.fetch_company_profile(symbol)
        else:
            print("🏢 Company Profile: ✅ Using cached data")
            results['profile'] = True
            self.stats['cache_hits'] += 1
        
        # Fetch historical prices if not cached
        if force_refresh or not coverage.get('historical_prices', False):
            print(f"📈 Fetching Historical Prices ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})...")
            results['historical_prices'] = self.fetch_historical_prices(symbol, start_date, end_date)
        else:
            print("📈 Historical Prices: ✅ Using cached data")
            results['historical_prices'] = True
            self.stats['cache_hits'] += 1
        
        # Add more data types as needed...
        
        self.stats['symbols_processed'] += 1
        success_count = sum(1 for v in results.values() if v)
        print(f"✅ {symbol}: {success_count}/{len(results)} data types successful")
        
        return results
    
    def fetch_batch(self, symbols: Union[str, List[str]], start_date: datetime, 
                   end_date: datetime, force_refresh: bool = False) -> Dict[str, Dict[str, bool]]:
        """
        Fetch data for multiple symbols.
        Returns dict of symbol -> results.
        """
        symbol_list = self._get_symbols_list(symbols)
        
        if not symbol_list:
            print("❌ No valid symbols found")
            return {}
        
        print(f"🚀 Starting batch fetch for {len(symbol_list)} symbols")
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🔄 Force refresh: {force_refresh}")
        print("=" * 70)
        
        results = {}
        start_time = time.time()
        
        for i, symbol in enumerate(symbol_list, 1):
            print(f"\n[{i}/{len(symbol_list)}] Processing {symbol}")
            try:
                results[symbol] = self.fetch_symbol_data(symbol, start_date, end_date, force_refresh)
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                results[symbol] = {}
                self.stats['errors'] += 1
            
            # Rate limiting between symbols
            if i < len(symbol_list):
                time.sleep(0.5)
        
        # Print summary
        elapsed_time = time.time() - start_time
        self._print_batch_summary(symbol_list, results, elapsed_time)
        
        return results
    
    def _print_batch_summary(self, symbols: List[str], results: Dict, elapsed_time: float):
        """Print batch processing summary"""
        print(f"\n{'='*70}")
        print("📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*70}")
        
        successful_symbols = [s for s, r in results.items() if any(r.values())]
        
        print(f"Total Symbols: {len(symbols)}")
        print(f"Successful: {len(successful_symbols)}")
        print(f"Failed: {len(symbols) - len(successful_symbols)}")
        print(f"Processing Time: {elapsed_time:.1f} seconds")
        print()
        
        print("📈 Statistics:")
        print(f"  API Calls Made: {self.stats['api_calls']}")
        print(f"  Cache Hits: {self.stats['cache_hits']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"  Symbols Processed: {self.stats['symbols_processed']}")
        
        if self.stats['api_calls'] > 0:
            cache_efficiency = (self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['api_calls'])) * 100
            print(f"  Cache Efficiency: {cache_efficiency:.1f}%")
        
        print(f"\n🎉 Batch processing complete!")


def main():
    """Command line interface for stock data fetcher"""
    parser = argparse.ArgumentParser(description="Fetch stock data with intelligent caching")
    parser.add_argument('symbols', help='Single symbol, comma-separated symbols, or path to file with symbols')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)', default=None)
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)', default=None)
    parser.add_argument('--days', type=int, help='Number of days back from today', default=365)
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh cached data')
    parser.add_argument('--api-key', type=str, help='FMP API key (or use FMP_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Parse date range
    if args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
    
    # Parse symbols
    if ',' in args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = args.symbols
    
    try:
        fetcher = StockDataFetcher(api_key=args.api_key)
        results = fetcher.fetch_batch(symbols, start_date, end_date, args.force_refresh)
        
        return 0 if results else 1
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())