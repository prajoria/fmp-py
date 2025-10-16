#!/usr/bin/env python3
"""
Smart Gap Filler for S&P 500 Historical Data
============================================
Analyzes existing data to find missing dates and fetches only those specific gaps,
avoiding redundant API calls and processing.
"""

import os
import sys
import mysql.connector
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple, Set, Any
import requests
from dotenv import load_dotenv
import time
import logging
from pathlib import Path

# Use relative imports from the fmp_py package
from pathlib import Path
from ...StockAnalysis.database.connection import get_connection

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

class SP500GapFiller:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.api_key = os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("FMP_API_KEY environment variable not set")
        
        self.db_config = {
            'host': os.getenv('FMP_DB_HOST', 'localhost'),
            'user': os.getenv('FMP_DB_USER', 'fmp_user'),
            'password': os.getenv('FMP_DB_PASSWORD', 'fmp_password'),
            'database': os.getenv('FMP_DB_NAME', 'fmp_cache'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # Date range for analysis (last 5 years)
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=5*365)
        
        self.logger.info(f"Initialized SP500GapFiller for date range: {self.start_date} to {self.end_date}")
    
    def get_sp500_symbols(self) -> List[str]:
        """Get all S&P 500 symbols from database"""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT symbol FROM sp500_constituents WHERE is_active = 1 ORDER BY symbol")
            symbols = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"Found {len(symbols)} active S&P 500 symbols")
            return symbols
        finally:
            cursor.close()
            conn.close()
    
    def get_us_market_holidays(self, year: int) -> Set[date]:
        """Get US stock market holidays for a given year"""
        holidays = set()
        
        # Fixed date holidays
        holidays.add(date(year, 1, 1))   # New Year's Day
        holidays.add(date(year, 7, 4))   # Independence Day
        holidays.add(date(year, 12, 25)) # Christmas Day
        
        # Martin Luther King Jr. Day (3rd Monday in January)
        jan_1 = date(year, 1, 1)
        days_to_first_monday = (7 - jan_1.weekday()) % 7
        first_monday = jan_1 + timedelta(days=days_to_first_monday)
        mlk_day = first_monday + timedelta(days=14)  # 3rd Monday
        holidays.add(mlk_day)
        
        # Presidents' Day (3rd Monday in February)
        feb_1 = date(year, 2, 1)
        days_to_first_monday = (7 - feb_1.weekday()) % 7
        first_monday = feb_1 + timedelta(days=days_to_first_monday)
        presidents_day = first_monday + timedelta(days=14)  # 3rd Monday
        holidays.add(presidents_day)
        
        # Good Friday (Friday before Easter) - approximate calculation
        # Using a simple approximation for Easter
        easter = self.get_easter_date(year)
        good_friday = easter - timedelta(days=2)
        holidays.add(good_friday)
        
        # Memorial Day (last Monday in May)
        may_31 = date(year, 5, 31)
        days_back_to_monday = (may_31.weekday() - 0) % 7
        memorial_day = may_31 - timedelta(days=days_back_to_monday)
        holidays.add(memorial_day)
        
        # Juneteenth (June 19) - federal holiday since 2021
        if year >= 2021:
            holidays.add(date(year, 6, 19))
        
        # Labor Day (1st Monday in September)
        sep_1 = date(year, 9, 1)
        days_to_first_monday = (7 - sep_1.weekday()) % 7
        labor_day = sep_1 + timedelta(days=days_to_first_monday)
        holidays.add(labor_day)
        
        # Columbus Day (2nd Monday in October) - market usually open
        # Thanksgiving (4th Thursday in November)
        nov_1 = date(year, 11, 1)
        days_to_first_thursday = (3 - nov_1.weekday()) % 7
        first_thursday = nov_1 + timedelta(days=days_to_first_thursday)
        thanksgiving = first_thursday + timedelta(days=21)  # 4th Thursday
        holidays.add(thanksgiving)
        
        # Black Friday (day after Thanksgiving) - market closed
        black_friday = thanksgiving + timedelta(days=1)
        holidays.add(black_friday)
        
        return holidays
    
    def get_easter_date(self, year: int) -> date:
        """Calculate Easter date using algorithm"""
        # Simple Easter calculation algorithm
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)
    
    def get_expected_trading_days(self, start_date: date, end_date: date) -> Set[date]:
        """Generate set of expected trading days (excluding weekends and holidays)"""
        trading_days = set()
        current_date = start_date
        
        # Get all holidays for the date range
        all_holidays = set()
        for year in range(start_date.year, end_date.year + 1):
            all_holidays.update(self.get_us_market_holidays(year))
        
        while current_date <= end_date:
            # Exclude weekends (Saturday=5, Sunday=6) and holidays
            if current_date.weekday() < 5 and current_date not in all_holidays:
                trading_days.add(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def is_next_trading_day(self, date1: date, date2: date) -> bool:
        """Check if date2 is the next trading day after date1"""
        # Get all trading days between the two dates
        trading_days = self.get_expected_trading_days(date1, date2)
        
        # Remove the start date from the set
        trading_days.discard(date1)
        
        # If date2 is in the remaining set and it's the first chronologically, they're consecutive
        if date2 in trading_days:
            sorted_days = sorted(trading_days)
            return len(sorted_days) == 1 or sorted_days[0] == date2
        
        return False
    
    def fetch_historical_data(self, symbol: str, start_date: date, end_date: date) -> bool:
        """Fetch and store historical data for a specific date range"""
        try:
            # Fetch the data
            historical_data = self.fetch_gap_data(symbol, start_date, end_date)
            
            if historical_data:
                # Store the data
                stored_count = self.store_gap_data(symbol, historical_data)
                return stored_count > 0
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error in fetch_historical_data for {symbol}: {e}")
            return False
    
    def analyze_symbol_gaps(self, symbol: str) -> Dict:
        """Analyze gaps for a single symbol"""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            # Get existing dates for this symbol
            cursor.execute("""
                SELECT DISTINCT date 
                FROM historical_prices_daily 
                WHERE symbol = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """, (symbol, self.start_date, self.end_date))
            
            existing_dates = {row[0] for row in cursor.fetchall()}
            expected_dates = self.get_expected_trading_days(self.start_date, self.end_date)
            missing_dates = expected_dates - existing_dates
            
            # Group consecutive missing dates into gaps (only for actual trading days)
            gaps = []
            if missing_dates:
                sorted_missing = sorted(missing_dates)
                gap_start = sorted_missing[0]
                gap_end = sorted_missing[0]
                
                for i in range(1, len(sorted_missing)):
                    current_date = sorted_missing[i]
                    # If more than 3 trading days apart, start new gap
                    days_between = (current_date - gap_end).days
                    if days_between > 5:  # Account for weekends and potential holidays
                        gaps.append((gap_start, gap_end))
                        gap_start = current_date
                    gap_end = current_date
                
                gaps.append((gap_start, gap_end))
            
            coverage_pct = (len(existing_dates) / len(expected_dates)) * 100 if expected_dates else 0
            
            return {
                'symbol': symbol,
                'expected_trading_days': len(expected_dates),
                'existing_days': len(existing_dates),
                'missing_days': len(missing_dates),
                'coverage_pct': coverage_pct,
                'gaps': gaps,
                'missing_dates': sorted(missing_dates)
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def fetch_gap_data(self, symbol: str, start_date: date, end_date: date) -> List[Dict]:
        """Fetch historical data for a specific date range"""
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'apikey': self.api_key,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'historical' in data and data['historical']:
                return data['historical']
            else:
                self.logger.warning(f"No historical data returned for {symbol} ({start_date} to {end_date})")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return []
    
    def store_gap_data(self, symbol: str, historical_data: List[Dict]) -> int:
        """Store fetched gap data in database"""
        if not historical_data:
            return 0
        
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            stored_count = 0
            
            for record in historical_data:
                try:
                    cursor.execute("""
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
                        symbol,
                        record['date'],
                        record.get('open'),
                        record.get('high'),
                        record.get('low'),
                        record.get('close'),
                        record.get('adjClose'),
                        record.get('volume'),
                        record.get('unadjustedVolume'),
                        record.get('change'),
                        record.get('changePercent'),
                        record.get('vwap'),
                        record.get('label'),
                        record.get('changeOverTime')
                    ))
                    stored_count += 1
                except Exception as e:
                    self.logger.error(f"Error storing record for {symbol} on {record.get('date')}: {e}")
                    continue
            
            return stored_count
            
        finally:
            cursor.close()
            conn.close()
    
    def fill_gaps_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Fill data gaps for a specific symbol"""
        result = {
            'symbol': symbol,
            'gaps': [],
            'missing_days': 0,
            'coverage_pct': 0.0,
            'filled_records': 0
        }
        
        try:
            self.logger.info(f"Analyzing gaps for {symbol}...")
            
            # Get existing data dates
            query = """
            SELECT DISTINCT DATE(date) as trade_date 
            FROM historical_prices_daily 
            WHERE symbol = %s 
            AND date >= %s AND date <= %s
            ORDER BY trade_date
            """
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (symbol, self.start_date, self.end_date))
                existing_dates = {row[0] for row in cursor.fetchall()}
            
            # Get expected trading days (excludes weekends and holidays)
            expected_dates = self.get_expected_trading_days(self.start_date, self.end_date)
            
            # Find missing dates (only among expected trading days)
            missing_dates = expected_dates - existing_dates
            
            if not missing_dates:
                self.logger.info(f"✅ {symbol}: No gaps found - data is complete!")
                result['coverage_pct'] = 100.0
                return result
            
            # Group consecutive missing dates into gaps
            sorted_missing = sorted(missing_dates)
            gaps = []
            if sorted_missing:
                current_gap = [sorted_missing[0]]
                
                for i in range(1, len(sorted_missing)):
                    current_date = sorted_missing[i]
                    prev_date = sorted_missing[i-1]
                    
                    # Check if dates are consecutive (within 1-3 days accounting for weekends)
                    days_diff = (current_date - prev_date).days
                    if days_diff <= 3:  # Allow for weekends
                        current_gap.append(current_date)
                    else:
                        gaps.append(current_gap)
                        current_gap = [current_date]
                
                gaps.append(current_gap)
            
            total_missing = len(missing_dates)
            total_expected = len(expected_dates)
            coverage = ((total_expected - total_missing) / total_expected) * 100
            
            result['gaps'] = gaps
            result['missing_days'] = total_missing
            result['coverage_pct'] = coverage
            
            self.logger.info(f"🔍 {symbol}: Found {total_missing} missing trading days in {len(gaps)} gaps ({coverage:.1f}% coverage)")
            self.logger.info(f"  📅 Pre-filtered out weekends/holidays - only requesting actual trading days from API")
            
            # Fill each gap (only for confirmed trading days)
            filled_records = 0
            for gap_num, gap in enumerate(gaps, 1):
                gap_start = gap[0]
                gap_end = gap[-1]
                gap_size = len(gap)
                
                self.logger.info(f"  Gap {gap_num}/{len(gaps)}: {gap_start} to {gap_end} ({gap_size} trading days)")
                
                # Fetch data for this gap (we already know these are trading days)
                success = self.fetch_historical_data(symbol, gap_start, gap_end)
                if success:
                    self.logger.info(f"    ✅ Successfully filled gap")
                    filled_records += gap_size
                else:
                    self.logger.info(f"    ⚠️  No data available for gap (unexpected - should be trading days)")
                
                # Small delay between API calls
                time.sleep(0.1)
            
            result['filled_records'] = filled_records
            return result
                
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {str(e)}")
            return result
    
    def run_sp500_gap_analysis(self) -> Dict:
        """Run gap analysis and filling for all S&P 500 symbols"""
        self.logger.info("🚀 Starting S&P 500 gap analysis and filling...")
        
        symbols = self.get_sp500_symbols()
        results = {
            'total_symbols': len(symbols),
            'processed': 0,
            'symbols_with_gaps': 0,
            'total_gaps_filled': 0,
            'symbol_results': []
        }
        
        for i, symbol in enumerate(symbols, 1):
            self.logger.info(f"\n[{i}/{len(symbols)}] Processing {symbol}")
            
            try:
                result = self.fill_gaps_for_symbol(symbol)
                if result:  # Check if result is not None
                    results['symbol_results'].append(result)
                    results['processed'] += 1
                    
                    if result.get('gaps'):
                        results['symbols_with_gaps'] += 1
                        results['total_gaps_filled'] += result.get('filled_records', 0)
                else:
                    # Create a default result if None was returned
                    default_result = {
                        'symbol': symbol,
                        'gaps': [],
                        'missing_days': 0,
                        'coverage_pct': 0.0,
                        'filled_records': 0
                    }
                    results['symbol_results'].append(default_result)
                    results['processed'] += 1
                
                # Progress report every 50 symbols
                if i % 50 == 0:
                    self.logger.info(f"📊 Progress: {i}/{len(symbols)} symbols processed")
                    self.logger.info(f"   Symbols with gaps: {results['symbols_with_gaps']}")
                    self.logger.info(f"   Total gaps filled: {results['total_gaps_filled']}")
                
            except Exception as e:
                self.logger.error(f"❌ Error processing {symbol}: {e}")
                # Add a failed result entry
                failed_result = {
                    'symbol': symbol,
                    'gaps': [],
                    'missing_days': 0,
                    'coverage_pct': 0.0,
                    'filled_records': 0
                }
                results['symbol_results'].append(failed_result)
                continue
        
        # Final summary
        self.logger.info("\n" + "="*70)
        self.logger.info("📊 S&P 500 GAP FILLING SUMMARY")
        self.logger.info("="*70)
        self.logger.info(f"Total symbols processed: {results['processed']}/{results['total_symbols']}")
        self.logger.info(f"Symbols with gaps: {results['symbols_with_gaps']}")
        self.logger.info(f"Total gaps filled: {results['total_gaps_filled']}")
        
        # Top symbols with most gaps
        symbols_with_gaps = [r for r in results['symbol_results'] if r and r.get('gaps')]
        symbols_with_gaps.sort(key=lambda x: x.get('missing_days', 0), reverse=True)
        
        self.logger.info("\n🔍 Symbols with most missing days:")
        for result in symbols_with_gaps[:10]:
            if result:
                self.logger.info(f"  {result.get('symbol', 'Unknown')}: {result.get('missing_days', 0)} missing days ({result.get('coverage_pct', 0):.1f}% coverage)")
        
        return results

if __name__ == "__main__":
    gap_filler = SP500GapFiller()
    results = gap_filler.run_sp500_gap_analysis()