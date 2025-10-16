#!/usr/bin/env python3
"""
FMP Historical Chart Fetcher
============================
Comprehensive historical price data fetcher with watermark tracking and crash recovery.

Features:
- Fetches full historical price data using FmpHistoricalCharts
- Stores data in historical_prices_daily table
- Maintains watermarks for crash recovery
- API rate limiting and retry logic
- Supports single stock or batch processing
- Popular stocks list included
- Progress tracking and monitoring
"""

import os
import sys
import time
import logging
import argparse
import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmp_py.fmp_historical_charts import FmpHistoricalCharts
from fmp_py.models.historical_charts import HistoricalPriceFull
from fmp_py.StockAnalysis.database.connection import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fmp_historical_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import SP500 constituents fetcher
try:
    from fmp_py.StockAnalysis.utils.sp500_constituents_fetcher import SP500ConstituentsFetcher
    SP500_AVAILABLE = True
except ImportError:
    SP500_AVAILABLE = False
    logger.warning("SP500ConstituentsFetcher not available. Install pandas to use --sp500-stocks option.")


@dataclass
class FetchWatermark:
    """Data class for fetch watermarks"""
    symbol: str
    fetch_type: str
    earliest_date: date
    latest_date: date
    last_fetch_date: date
    total_records: int
    fetch_status: str
    error_count: int
    last_error_message: Optional[str] = None


@dataclass
class FetchSession:
    """Data class for fetch sessions"""
    session_id: str
    fetch_type: str
    symbols_requested: List[str]
    symbols_processed: int = 0
    symbols_successful: int = 0
    symbols_failed: int = 0
    total_api_calls: int = 0
    total_records_fetched: int = 0
    status: str = 'running'


class FmpHistoricalChartFetcher:
    """
    Historical chart data fetcher with watermark tracking and crash recovery
    """
    
    # Popular stocks list - can be extended as needed
    POPULAR_STOCKS = [
        # Large Cap Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
        
        # Other Large Cap Stocks
        'BRK.B', 'JNJ', 'V', 'WMT', 'PG', 'UNH', 'HD', 'MA',
        
        # Financial Sector
        'JPM', 'BAC', 'WFC', 'GS',
        
        # Energy & Materials
        'XOM', 'CVX',
        
        # Healthcare & Pharma
        'PFE', 'ABBV', 'MRK',
        
        # Popular Growth Stocks
        'NFLX', 'CRM', 'AMD', 'INTC', 'ORCL',
        
        # Popular ETFs
        'SPY', 'QQQ', 'IWM', 'VTI'
    ]
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_per_minute: int = 250):
        """
        Initialize the fetcher
        
        Args:
            api_key: FMP API key (will use environment variable if not provided)
            rate_limit_per_minute: API calls per minute limit
        """
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY not found. Set environment variable or pass as parameter.")
        
        self.fmp_client = FmpHistoricalCharts(self.api_key)
        self.db = get_db()
        
        # Rate limiting
        self.rate_limit = rate_limit_per_minute
        self.request_interval = 60.0 / rate_limit_per_minute
        self.last_request_time = 0
        
        # Session tracking
        self.session_id = f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.session = None
        
        # Statistics
        self.stats = {
            'total_symbols': 0,
            'processed_symbols': 0,
            'successful_symbols': 0,
            'failed_symbols': 0,
            'api_calls': 0,
            'total_records': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"Initialized FmpHistoricalChartFetcher with session ID: {self.session_id}")
    
    def _rate_limit(self):
        """Implement rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_db_popular_stocks(self) -> List[str]:
        """Get popular stocks from database, fallback to hardcoded list"""
        try:
            result = self.db.execute_query("""
                SELECT symbol FROM popular_stocks 
                WHERE is_active = TRUE 
                ORDER BY priority ASC, symbol ASC
            """)
            
            if result:
                return [row['symbol'] for row in result]
            else:
                logger.warning("No popular stocks found in database, using hardcoded list")
                return self.POPULAR_STOCKS
        except Exception as e:
            logger.warning(f"Error fetching popular stocks from database: {e}, using hardcoded list")
            return self.POPULAR_STOCKS
    
    def _get_sp500_stocks(self) -> List[str]:
        """Get S&P 500 constituents using the SP500ConstituentsFetcher"""
        if not SP500_AVAILABLE:
            logger.error("SP500ConstituentsFetcher not available. Install pandas to use this feature.")
            return []
        
        try:
            logger.info("Fetching S&P 500 constituents...")
            fetcher = SP500ConstituentsFetcher(use_database=True)
            
            # Try to get from database first, then fall back to web fetch
            symbols = fetcher.get_symbols_list(from_database=True)
            
            if not symbols:
                logger.info("No S&P 500 data in database, fetching from web...")
                df = fetcher.fetch_constituents()
                symbols = fetcher.get_symbols_list(df)
                
                # Save to database for future use
                if fetcher.use_database:
                    fetcher.save_to_database(df)
                    logger.info("Saved S&P 500 data to database for future use")
            
            logger.info(f"Successfully fetched {len(symbols)} S&P 500 symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 constituents: {e}")
            return []
    
    def get_or_create_watermark(self, symbol: str, fetch_type: str = 'historical_full') -> FetchWatermark:
        """
        Get existing watermark or create new one for symbol
        
        Args:
            symbol: Stock symbol
            fetch_type: Type of fetch operation
            
        Returns:
            FetchWatermark object
        """
        try:
            # Try to get existing watermark
            result = self.db.execute_query("""
                CALL GetOrCreateWatermark(%s, %s)
            """, (symbol.upper(), fetch_type), fetch='one')
            
            if result:
                return FetchWatermark(
                    symbol=result['symbol'],
                    fetch_type=result['fetch_type'],
                    earliest_date=result['earliest_date'],
                    latest_date=result['latest_date'],
                    last_fetch_date=result['last_fetch_date'],
                    total_records=result['total_records'],
                    fetch_status=result['fetch_status'],
                    error_count=result['error_count'],
                    last_error_message=result.get('last_error_message')
                )
            else:
                raise Exception("Failed to get or create watermark")
                
        except Exception as e:
            logger.error(f"Error getting watermark for {symbol}: {e}")
            # Create a default watermark if database operation fails
            five_years_ago = date.today() - timedelta(days=5*365)
            return FetchWatermark(
                symbol=symbol.upper(),
                fetch_type=fetch_type,
                earliest_date=five_years_ago,
                latest_date=five_years_ago,
                last_fetch_date=five_years_ago,
                total_records=0,
                fetch_status='active',
                error_count=0
            )
    
    def update_watermark(self, symbol: str, latest_date: date, records_count: int, 
                        fetch_type: str = 'historical_full'):
        """
        Update watermark after successful fetch
        
        Args:
            symbol: Stock symbol
            latest_date: Latest date fetched
            records_count: Number of records fetched
            fetch_type: Type of fetch operation
        """
        try:
            self.db.execute_query("""
                CALL UpdateWatermark(%s, %s, %s, %s)
            """, (symbol.upper(), fetch_type, latest_date, records_count))
            
            logger.info(f"Updated watermark for {symbol}: latest_date={latest_date}, records={records_count}")
            
        except Exception as e:
            logger.error(f"Error updating watermark for {symbol}: {e}")
    
    def record_fetch_error(self, symbol: str, error_message: str, fetch_type: str = 'historical_full'):
        """
        Record fetch error in watermark
        
        Args:
            symbol: Stock symbol
            error_message: Error description
            fetch_type: Type of fetch operation
        """
        try:
            self.db.execute_query("""
                CALL RecordFetchError(%s, %s, %s)
            """, (symbol.upper(), fetch_type, error_message))
            
            logger.warning(f"Recorded error for {symbol}: {error_message}")
            
        except Exception as e:
            logger.error(f"Error recording fetch error for {symbol}: {e}")
    
    def create_fetch_session(self, symbols: List[str], fetch_type: str = 'historical_full') -> FetchSession:
        """Create and store a new fetch session"""
        session = FetchSession(
            session_id=self.session_id,
            fetch_type=fetch_type,
            symbols_requested=symbols
        )
        
        try:
            self.db.execute_update("""
                INSERT INTO fetch_sessions 
                (session_id, fetch_type, symbols_requested, status, start_time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (session.session_id, session.fetch_type, 
                  ','.join(session.symbols_requested), session.status))
            
            logger.info(f"Created fetch session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error creating fetch session: {e}")
        
        return session
    
    def update_session_progress(self, session: FetchSession):
        """Update session progress in database"""
        try:
            self.db.execute_update("""
                UPDATE fetch_sessions 
                SET symbols_processed = %s, symbols_successful = %s, symbols_failed = %s,
                    total_api_calls = %s, total_records_fetched = %s, status = %s
                WHERE session_id = %s
            """, (session.symbols_processed, session.symbols_successful, session.symbols_failed,
                  session.total_api_calls, session.total_records_fetched, session.status,
                  session.session_id))
            
        except Exception as e:
            logger.error(f"Error updating session progress: {e}")
    
    def complete_fetch_session(self, session: FetchSession, status: str = 'completed'):
        """Mark fetch session as completed"""
        try:
            self.db.execute_update("""
                UPDATE fetch_sessions 
                SET symbols_processed = %s, symbols_successful = %s, symbols_failed = %s,
                    total_api_calls = %s, total_records_fetched = %s, status = %s,
                    end_time = NOW()
                WHERE session_id = %s
            """, (session.symbols_processed, session.symbols_successful, session.symbols_failed,
                  session.total_api_calls, session.total_records_fetched, status,
                  session.session_id))
            
            logger.info(f"Completed fetch session: {session.session_id} with status: {status}")
            
        except Exception as e:
            logger.error(f"Error completing fetch session: {e}")
    
    def store_historical_data(self, symbol: str, historical_data: List[HistoricalPriceFull]) -> int:
        """
        Store historical price data in database using batch operations
        
        Args:
            symbol: Stock symbol
            historical_data: List of historical price data
            
        Returns:
            Number of records stored
        """
        if not historical_data:
            return 0
        
        # Prepare batch data for executemany
        batch_data = []
        for price_data in historical_data:
            try:
                batch_data.append((
                    symbol.upper(),
                    price_data.date,
                    price_data.open,
                    price_data.high,
                    price_data.low,
                    price_data.close,
                    price_data.adj_close,
                    price_data.volume,
                    price_data.unadjusted_volume,
                    price_data.change,
                    price_data.change_percent,
                    price_data.vwap,
                    price_data.label,
                    price_data.change_over_time
                ))
            except Exception as e:
                logger.error(f"Error preparing data for {symbol} on {price_data.date}: {e}")
                continue
        
        if not batch_data:
            return 0
        
        try:
            # Use batch insert with a single connection
            rows_affected = self.db.execute_many("""
                INSERT INTO historical_prices_daily (
                    symbol, date, `open`, high, low, `close`, adj_close, volume,
                    unadjusted_volume, `change`, change_percent, vwap, label, change_over_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                `open` = VALUES(`open`), high = VALUES(high), low = VALUES(low),
                `close` = VALUES(`close`), adj_close = VALUES(adj_close), volume = VALUES(volume),
                unadjusted_volume = VALUES(unadjusted_volume), `change` = VALUES(`change`),
                change_percent = VALUES(change_percent), vwap = VALUES(vwap),
                label = VALUES(label), change_over_time = VALUES(change_over_time),
                cached_at = NOW()
            """, batch_data)
            
            stored_count = len(batch_data)  # executemany doesn't return meaningful rowcount for ON DUPLICATE KEY
            logger.info(f"Stored {stored_count}/{len(historical_data)} records for {symbol}")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error batch storing price data for {symbol}: {e}")
            # Fallback to individual inserts on batch failure
            return self._store_historical_data_individual(symbol, historical_data)
    
    def _store_historical_data_individual(self, symbol: str, historical_data: List[HistoricalPriceFull]) -> int:
        """
        Fallback method: Store historical data one record at a time
        
        Args:
            symbol: Stock symbol
            historical_data: List of historical price data
            
        Returns:
            Number of records stored
        """
        stored_count = 0
        
        for price_data in historical_data:
            try:
                self.db.execute_update("""
                    INSERT INTO historical_prices_daily (
                        symbol, date, `open`, high, low, `close`, adj_close, volume,
                        unadjusted_volume, `change`, change_percent, vwap, label, change_over_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    `open` = VALUES(`open`), high = VALUES(high), low = VALUES(low),
                    `close` = VALUES(`close`), adj_close = VALUES(adj_close), volume = VALUES(volume),
                    unadjusted_volume = VALUES(unadjusted_volume), `change` = VALUES(`change`),
                    change_percent = VALUES(change_percent), vwap = VALUES(vwap),
                    label = VALUES(label), change_over_time = VALUES(change_over_time),
                    cached_at = NOW()
                """, (
                    symbol.upper(),
                    price_data.date,
                    price_data.open,
                    price_data.high,
                    price_data.low,
                    price_data.close,
                    price_data.adj_close,
                    price_data.volume,
                    price_data.unadjusted_volume,
                    price_data.change,
                    price_data.change_percent,
                    price_data.vwap,
                    price_data.label,
                    price_data.change_over_time
                ))
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing price data for {symbol} on {price_data.date}: {e}")
                continue
        
        logger.info(f"Stored {stored_count}/{len(historical_data)} records for {symbol} (individual mode)")
        return stored_count
    
    def fetch_symbol_data(self, symbol: str, start_date: Optional[date] = None, 
                         end_date: Optional[date] = None, resume_from_watermark: bool = True) -> bool:
        """
        Fetch historical data for a single symbol
        
        Args:
            symbol: Stock symbol
            start_date: Start date (default: 5 years ago)
            end_date: End date (default: today)
            resume_from_watermark: Whether to resume from watermark
            
        Returns:
            True if successful, False otherwise
        """
        symbol = symbol.upper()
        logger.info(f"🎯 Processing symbol: {symbol}")
        
        try:
            # Get watermark for crash recovery
            watermark = self.get_or_create_watermark(symbol) if resume_from_watermark else None
            
            # Determine date range
            if not start_date:
                if watermark and resume_from_watermark:
                    # Resume from where we left off
                    start_date = watermark.latest_date + timedelta(days=1)
                else:
                    # Start from 5 years ago
                    start_date = date.today() - timedelta(days=5*365)
            
            if not end_date:
                end_date = date.today()
            
            # Skip if already up to date
            if watermark and resume_from_watermark and watermark.latest_date >= end_date:
                logger.info(f"✅ {symbol} already up to date (latest: {watermark.latest_date})")
                return True
            
            # Skip if too many errors
            if watermark and watermark.error_count >= 5:
                logger.warning(f"⏭️ Skipping {symbol} due to too many errors ({watermark.error_count})")
                return False
            
            logger.info(f"📅 Fetching {symbol} from {start_date} to {end_date}")
            
            # Rate limiting
            self._rate_limit()
            
            # Fetch data from FMP API
            historical_data = self.fmp_client.get_historical_price_full(
                symbol=symbol,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            self.stats['api_calls'] += 1
            
            if not historical_data:
                error_msg = f"No data returned from API for {symbol}"
                logger.warning(f"⚠️ {error_msg}")
                self.record_fetch_error(symbol, error_msg)
                return False
            
            # Store data in database
            stored_count = self.store_historical_data(symbol, historical_data)
            
            if stored_count > 0:
                # Update watermark
                latest_data_date = max(datetime.strptime(str(data.date), '%Y-%m-%d').date() 
                                     for data in historical_data)
                self.update_watermark(symbol, latest_data_date, stored_count)
                
                # Update statistics
                self.stats['total_records'] += stored_count
                
                logger.info(f"✅ {symbol}: Fetched and stored {stored_count} records")
                return True
            else:
                error_msg = f"Failed to store data for {symbol}"
                logger.error(f"❌ {error_msg}")
                self.record_fetch_error(symbol, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error fetching data for {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.record_fetch_error(symbol, error_msg)
            return False
    
    def fetch_batch(self, symbols: List[str], start_date: Optional[date] = None,
                   end_date: Optional[date] = None, resume_from_watermark: bool = True) -> Dict[str, bool]:
        """
        Fetch historical data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (default: 5 years ago)
            end_date: End date (default: today)
            resume_from_watermark: Whether to resume from watermarks
            
        Returns:
            Dictionary of symbol -> success status
        """
        if not symbols:
            logger.warning("No symbols provided for batch fetch")
            return {}
        
        # Initialize statistics
        self.stats['start_time'] = datetime.now()
        self.stats['total_symbols'] = len(symbols)
        
        # Create fetch session
        session = self.create_fetch_session(symbols)
        self.session = session
        
        logger.info(f"🚀 Starting batch fetch for {len(symbols)} symbols")
        logger.info(f"📅 Date range: {start_date or 'watermark'} to {end_date or 'today'}")
        logger.info(f"🔄 Resume from watermark: {resume_from_watermark}")
        logger.info("=" * 70)
        
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            symbol = symbol.upper().strip()
            
            logger.info(f"\n[{i}/{len(symbols)}] Processing {symbol}")
            
            try:
                success = self.fetch_symbol_data(symbol, start_date, end_date, resume_from_watermark)
                results[symbol] = success
                
                # Update session statistics
                session.symbols_processed += 1
                if success:
                    session.symbols_successful += 1
                    self.stats['successful_symbols'] += 1
                else:
                    session.symbols_failed += 1
                    self.stats['failed_symbols'] += 1
                
                session.total_api_calls = self.stats['api_calls']
                session.total_records_fetched = self.stats['total_records']
                
                # Update session in database
                if i % 5 == 0:  # Update every 5 symbols
                    self.update_session_progress(session)
                
                # Brief pause between symbols
                if i < len(symbols):
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info(f"\n⛔ Fetch interrupted by user at symbol {i}/{len(symbols)}")
                session.status = 'interrupted'
                break
            except Exception as e:
                logger.error(f"❌ Fatal error processing {symbol}: {e}")
                results[symbol] = False
                session.symbols_failed += 1
                self.stats['failed_symbols'] += 1
                continue
        
        # Update final statistics
        self.stats['end_time'] = datetime.now()
        self.stats['processed_symbols'] = session.symbols_processed
        
        # Complete session
        self.complete_fetch_session(session, session.status)
        
        # Print summary
        self._print_batch_summary(results)
        
        return results
    
    def _print_batch_summary(self, results: Dict[str, bool]):
        """Print batch processing summary"""
        elapsed_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print(f"\n{'='*70}")
        print("📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*70}")
        
        print(f"Session ID: {self.session_id}")
        print(f"Total Symbols: {self.stats['total_symbols']}")
        print(f"Processed: {self.stats['processed_symbols']}")
        print(f"Successful: {self.stats['successful_symbols']}")
        print(f"Failed: {self.stats['failed_symbols']}")
        print(f"Processing Time: {elapsed_time:.1f} seconds")
        print()
        
        print("📈 API Statistics:")
        print(f"  API Calls Made: {self.stats['api_calls']}")
        print(f"  Total Records Fetched: {self.stats['total_records']}")
        print(f"  Average Records per Symbol: {self.stats['total_records'] / max(self.stats['successful_symbols'], 1):.0f}")
        
        if self.stats['api_calls'] > 0:
            api_rate = self.stats['api_calls'] / (elapsed_time / 60)
            print(f"  API Rate: {api_rate:.1f} calls/minute")
        
        # Show failed symbols
        failed_symbols = [symbol for symbol, success in results.items() if not success]
        if failed_symbols:
            print(f"\n❌ Failed Symbols ({len(failed_symbols)}):")
            for symbol in failed_symbols[:10]:  # Show first 10
                print(f"  - {symbol}")
            if len(failed_symbols) > 10:
                print(f"  ... and {len(failed_symbols) - 10} more")
        
        print(f"\n🎉 Batch processing complete!")
    
    def get_fetch_progress(self, symbols: Optional[List[str]] = None) -> List[Dict]:
        """
        Get fetch progress for symbols
        
        Args:
            symbols: List of symbols to check (default: all)
            
        Returns:
            List of progress dictionaries
        """
        try:
            if symbols:
                placeholders = ','.join(['%s'] * len(symbols))
                query = f"""
                    SELECT * FROM v_fetch_progress 
                    WHERE symbol IN ({placeholders})
                    ORDER BY symbol
                """
                result = self.db.execute_query(query, tuple(s.upper() for s in symbols))
            else:
                result = self.db.execute_query("SELECT * FROM v_fetch_progress ORDER BY symbol")
            
            return result or []
            
        except Exception as e:
            logger.error(f"Error getting fetch progress: {e}")
            return []
    
    def print_progress_report(self, symbols: Optional[List[str]] = None):
        """Print a progress report for symbols"""
        progress_data = self.get_fetch_progress(symbols)
        
        if not progress_data:
            print("No progress data available")
            return
        
        print(f"\n{'='*90}")
        print("📊 FETCH PROGRESS REPORT")
        print(f"{'='*90}")
        print(f"{'Symbol':<8} {'Status':<12} {'Latest Date':<12} {'Records':<8} {'Days Behind':<12} {'Errors':<6}")
        print("-" * 90)
        
        for row in progress_data:
            symbol = row['symbol']
            status = row['status_display']
            latest_date = str(row['latest_date'])
            records = row['total_records']
            days_behind = row['days_behind'] or 0
            errors = row['error_count']
            
            print(f"{symbol:<8} {status:<12} {latest_date:<12} {records:<8} {days_behind:<12} {errors:<6}")
        
        # Summary statistics
        total_symbols = len(progress_data)
        complete_symbols = sum(1 for row in progress_data if row['fetch_status'] == 'complete')
        failed_symbols = sum(1 for row in progress_data if row['fetch_status'] == 'failed')
        active_symbols = sum(1 for row in progress_data if row['fetch_status'] == 'active')
        
        print("-" * 90)
        print(f"Total: {total_symbols} | Complete: {complete_symbols} | Active: {active_symbols} | Failed: {failed_symbols}")
        print(f"{'='*90}")


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    """Command line interface for historical chart fetcher"""
    parser = argparse.ArgumentParser(
        description="Fetch historical chart data from FMP API with watermark tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch popular stocks
  python fmp_historical_chart_fetcher.py --popular-stocks
  
  # Fetch S&P 500 constituent stocks (requires pandas)
  python fmp_historical_chart_fetcher.py --sp500-stocks
  
  # Fetch specific symbols
  python fmp_historical_chart_fetcher.py --symbols AAPL,MSFT,GOOGL
  
  # Fetch from file
  python fmp_historical_chart_fetcher.py --symbols-file stocks.txt
  
  # Fetch with date range
  python fmp_historical_chart_fetcher.py --symbols AAPL --start-date 2020-01-01 --end-date 2023-12-31
  
  # Force refresh (ignore watermarks)
  python fmp_historical_chart_fetcher.py --symbols AAPL --force-refresh
  
  # Show progress report
  python fmp_historical_chart_fetcher.py --progress-report
        """
    )
    
    # Symbol selection (mutually exclusive)
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument('--symbols', type=str, help='Comma-separated list of symbols')
    symbol_group.add_argument('--symbols-file', type=str, help='File containing symbols (one per line)')
    symbol_group.add_argument('--popular-stocks', action='store_true', help='Fetch popular stocks')
    symbol_group.add_argument('--sp500-stocks', action='store_true', help='Fetch S&P 500 constituent stocks')
    symbol_group.add_argument('--progress-report', action='store_true', help='Show progress report only')
    
    # Date range options
    parser.add_argument('--start-date', type=parse_date, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=parse_date, help='End date (YYYY-MM-DD)')
    parser.add_argument('--days-back', type=int, default=1825, help='Days back from today (default: 5 years)')
    
    # Fetch options
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh, ignore watermarks')
    parser.add_argument('--rate-limit', type=int, default=250, help='API calls per minute (default: 250)')
    parser.add_argument('--api-key', type=str, help='FMP API key (or use FMP_API_KEY env var)')
    
    # Logging options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Initialize fetcher
        fetcher = FmpHistoricalChartFetcher(
            api_key=args.api_key,
            rate_limit_per_minute=args.rate_limit
        )
        
        # Handle progress report
        if args.progress_report:
            symbols = None
            if args.symbols:
                symbols = [s.strip() for s in args.symbols.split(',')]
            elif args.symbols_file and os.path.exists(args.symbols_file):
                with open(args.symbols_file, 'r') as f:
                    symbols = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            fetcher.print_progress_report(symbols)
            return 0
        
        # Determine symbols to fetch
        symbols = []
        if args.symbols:
            symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
        elif args.symbols_file:
            if not os.path.exists(args.symbols_file):
                print(f"❌ Symbols file not found: {args.symbols_file}")
                return 1
            with open(args.symbols_file, 'r') as f:
                symbols = [line.strip().upper() for line in f 
                          if line.strip() and not line.startswith('#')]
        elif args.popular_stocks:
            symbols = fetcher._get_db_popular_stocks()
        elif args.sp500_stocks:
            if not SP500_AVAILABLE:
                print("❌ S&P 500 fetcher not available. Install pandas with: pip install pandas")
                return 1
            symbols = fetcher._get_sp500_stocks()
            if not symbols:
                print("❌ Failed to fetch S&P 500 constituents")
                return 1
        
        if not symbols:
            print("❌ No symbols to fetch")
            return 1
        
        # Determine date range
        start_date = args.start_date
        end_date = args.end_date
        
        if not start_date and not args.force_refresh:
            # Will use watermarks for resume
            start_date = None
        elif not start_date:
            # Force refresh mode
            start_date = date.today() - timedelta(days=args.days_back)
        
        if not end_date:
            end_date = date.today()
        
        print(f"🚀 Starting fetch for {len(symbols)} symbols")
        print(f"📊 Rate limit: {args.rate_limit} calls/minute")
        print(f"🔄 Force refresh: {args.force_refresh}")
        
        # Execute batch fetch
        results = fetcher.fetch_batch(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            resume_from_watermark=not args.force_refresh
        )
        
        # Return appropriate exit code
        success_count = sum(1 for success in results.values() if success)
        if success_count == len(symbols):
            return 0  # All successful
        elif success_count > 0:
            return 2  # Partial success
        else:
            return 1  # All failed
        
    except KeyboardInterrupt:
        print("\n⛔ Fetch interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())