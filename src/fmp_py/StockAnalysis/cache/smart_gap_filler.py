#!/usr/bin/env python3
"""
Smart Gap Filler for Historical Data
====================================
Analyzes existing historical price data to identify missing dates and fetches only those gaps,
instead of processing data sequentially. This is much more efficient for filling data gaps.

Features:
- Identifies missing trading days for each symbol
- Fetches only missing date ranges (gaps)
- Supports both individual symbols and bulk S&P 500 processing
- Optimizes API calls by combining adjacent missing dates
- Provides detailed gap analysis and reporting
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmp_py.fmp_historical_charts import FmpHistoricalCharts
from fmp_py.models import HistoricalPriceFull
from StockAnalysis.database.connection import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DateGap:
    """Represents a gap in historical data"""
    symbol: str
    start_date: date
    end_date: date
    missing_days: int
    
    def __str__(self):
        return f"{self.symbol}: {self.start_date} to {self.end_date} ({self.missing_days} days)"

@dataclass
class GapAnalysis:
    """Analysis results for data gaps"""
    symbol: str
    total_expected_days: int
    existing_days: int
    missing_days: int
    gaps: List[DateGap]
    coverage_percentage: float
    
    def __str__(self):
        return (f"{self.symbol}: {self.existing_days}/{self.total_expected_days} days "
                f"({self.coverage_percentage:.1f}% coverage, {len(self.gaps)} gaps)")


class SmartGapFiller:
    """
    Smart historical data gap filler that analyzes existing data and fetches only missing dates
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the gap filler
        
        Args:
            api_key: FMP API key (will use environment variable if not provided)
        """
        self.db = get_db()
        self.fmp_client = FmpHistoricalCharts(api_key=api_key)
        self.session_id = f"gap_fill_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Initialized SmartGapFiller with session ID: {self.session_id}")
    
    def get_trading_days(self, start_date: date, end_date: date) -> Set[date]:
        """
        Generate expected trading days (excluding weekends, basic holidays)
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Set of expected trading dates
        """
        trading_days = set()
        current_date = start_date
        
        # Basic US holidays (simplified - doesn't include all market holidays)
        holidays = {
            # New Year's Day
            date(2020, 1, 1), date(2021, 1, 1), date(2022, 1, 1), date(2023, 1, 1), 
            date(2024, 1, 1), date(2025, 1, 1),
            # Independence Day
            date(2020, 7, 4), date(2021, 7, 4), date(2022, 7, 4), date(2023, 7, 4), 
            date(2024, 7, 4), date(2025, 7, 4),
            # Christmas
            date(2020, 12, 25), date(2021, 12, 25), date(2022, 12, 25), date(2023, 12, 25), 
            date(2024, 12, 25), date(2025, 12, 25),
        }
        
        while current_date <= end_date:
            # Skip weekends and basic holidays
            if current_date.weekday() < 5 and current_date not in holidays:
                trading_days.add(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def analyze_symbol_gaps(self, symbol: str, start_date: date, end_date: date) -> GapAnalysis:
        """
        Analyze gaps in historical data for a symbol
        
        Args:
            symbol: Stock symbol
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            GapAnalysis object with detailed gap information
        """
        # Get existing dates from database
        existing_dates_result = self.db.execute_query("""
            SELECT DISTINCT date 
            FROM historical_prices_daily 
            WHERE symbol = %s AND date BETWEEN %s AND %s 
            ORDER BY date
        """, (symbol.upper(), start_date, end_date))
        
        existing_dates = {row['date'] for row in existing_dates_result}
        expected_dates = self.get_trading_days(start_date, end_date)
        missing_dates = sorted(expected_dates - existing_dates)
        
        # Group consecutive missing dates into gaps
        gaps = []
        if missing_dates:
            gap_start = missing_dates[0]
            gap_end = missing_dates[0]
            
            for i in range(1, len(missing_dates)):
                current_date = missing_dates[i]
                # If current date is not consecutive, end current gap and start new one
                if (current_date - gap_end).days > 1:
                    gaps.append(DateGap(
                        symbol=symbol,
                        start_date=gap_start,
                        end_date=gap_end,
                        missing_days=len([d for d in missing_dates if gap_start <= d <= gap_end])
                    ))
                    gap_start = current_date
                
                gap_end = current_date
            
            # Add the last gap
            gaps.append(DateGap(
                symbol=symbol,
                start_date=gap_start,
                end_date=gap_end,
                missing_days=len([d for d in missing_dates if gap_start <= d <= gap_end])
            ))
        
        coverage_percentage = (len(existing_dates) / len(expected_dates) * 100) if expected_dates else 100
        
        return GapAnalysis(
            symbol=symbol,
            total_expected_days=len(expected_dates),
            existing_days=len(existing_dates),
            missing_days=len(missing_dates),
            gaps=gaps,
            coverage_percentage=coverage_percentage
        )
    
    def fill_symbol_gaps(self, symbol: str, gaps: List[DateGap]) -> int:
        """
        Fill gaps for a specific symbol
        
        Args:
            symbol: Stock symbol
            gaps: List of date gaps to fill
            
        Returns:
            Number of records fetched and stored
        """
        total_records = 0
        
        for gap in gaps:
            try:
                logger.info(f"Filling gap for {symbol}: {gap.start_date} to {gap.end_date}")
                
                # Fetch data for the gap period
                historical_data = self.fmp_client.get_historical_price_full(
                    symbol=symbol,
                    start_date=gap.start_date.strftime('%Y-%m-%d'),
                    end_date=gap.end_date.strftime('%Y-%m-%d')
                )
                
                if historical_data:
                    # Store the data
                    records_stored = self.store_historical_data(symbol, historical_data)
                    total_records += records_stored
                    logger.info(f"✅ Filled {records_stored} records for {symbol} gap {gap.start_date} to {gap.end_date}")
                else:
                    logger.warning(f"⚠️ No data returned for {symbol} gap {gap.start_date} to {gap.end_date}")
                
                # Rate limiting
                time.sleep(0.25)  # 4 calls per second = 240 calls per minute (under 250 limit)
                
            except Exception as e:
                logger.error(f"❌ Error filling gap for {symbol} ({gap.start_date} to {gap.end_date}): {e}")
                continue
        
        return total_records
    
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
            self.db.execute_many("""
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
            
            stored_count = len(batch_data)
            return stored_count
            
        except Exception as e:
            logger.error(f"Error batch storing price data for {symbol}: {e}")
            return 0
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols from database"""
        try:
            result = self.db.execute_query("""
                SELECT symbol FROM sp500_constituents 
                WHERE is_active = 1 
                ORDER BY symbol
            """)
            return [row['symbol'] for row in result]
        except Exception as e:
            logger.error(f"Error fetching S&P 500 symbols: {e}")
            return []
    
    def analyze_gaps(self, symbols: List[str], start_date: date, end_date: date) -> List[GapAnalysis]:
        """
        Analyze gaps for multiple symbols
        
        Args:
            symbols: List of stock symbols
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            List of GapAnalysis objects
        """
        analyses = []
        
        logger.info(f"🔍 Analyzing gaps for {len(symbols)} symbols from {start_date} to {end_date}")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                analysis = self.analyze_symbol_gaps(symbol, start_date, end_date)
                analyses.append(analysis)
                
                if analysis.missing_days > 0:
                    logger.info(f"[{i}/{len(symbols)}] {analysis}")
                else:
                    logger.debug(f"[{i}/{len(symbols)}] {symbol}: Complete (100% coverage)")
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        return analyses
    
    def fill_gaps(self, symbols: List[str], start_date: date, end_date: date, 
                  min_gap_size: int = 1) -> Dict[str, Any]:
        """
        Fill gaps for multiple symbols
        
        Args:
            symbols: List of stock symbols
            start_date: Fill start date
            end_date: Fill end date
            min_gap_size: Minimum gap size to fill (skip smaller gaps)
            
        Returns:
            Summary statistics
        """
        start_time = datetime.now()
        
        # First analyze all gaps
        analyses = self.analyze_gaps(symbols, start_date, end_date)
        
        # Filter symbols that need gap filling
        symbols_with_gaps = [
            analysis for analysis in analyses 
            if analysis.missing_days >= min_gap_size
        ]
        
        logger.info(f"🎯 Found {len(symbols_with_gaps)} symbols with gaps >= {min_gap_size} days")
        
        if not symbols_with_gaps:
            logger.info("✅ No gaps to fill!")
            return {
                'total_symbols_analyzed': len(analyses),
                'symbols_with_gaps': 0,
                'total_records_filled': 0,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
        
        # Fill gaps
        total_records_filled = 0
        symbols_processed = 0
        
        for i, analysis in enumerate(symbols_with_gaps, 1):
            try:
                logger.info(f"🔧 [{i}/{len(symbols_with_gaps)}] Filling gaps for {analysis.symbol}")
                
                records_filled = self.fill_symbol_gaps(analysis.symbol, analysis.gaps)
                total_records_filled += records_filled
                symbols_processed += 1
                
                logger.info(f"✅ {analysis.symbol}: Filled {records_filled} records in {len(analysis.gaps)} gaps")
                
            except Exception as e:
                logger.error(f"❌ Error processing {analysis.symbol}: {e}")
                continue
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Summary
        summary = {
            'total_symbols_analyzed': len(analyses),
            'symbols_with_gaps': len(symbols_with_gaps),
            'symbols_processed': symbols_processed,
            'total_records_filled': total_records_filled,
            'processing_time': processing_time,
            'records_per_minute': (total_records_filled / (processing_time / 60)) if processing_time > 0 else 0
        }
        
        logger.info("="*70)
        logger.info("📊 GAP FILLING SUMMARY")
        logger.info("="*70)
        logger.info(f"Symbols analyzed: {summary['total_symbols_analyzed']}")
        logger.info(f"Symbols with gaps: {summary['symbols_with_gaps']}")
        logger.info(f"Symbols processed: {summary['symbols_processed']}")
        logger.info(f"Records filled: {summary['total_records_filled']}")
        logger.info(f"Processing time: {summary['processing_time']:.1f} seconds")
        logger.info(f"Records per minute: {summary['records_per_minute']:.1f}")
        logger.info("="*70)
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Smart Gap Filler for Historical Data')
    
    # Symbol selection
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument('--symbol', type=str, help='Single symbol to analyze/fill')
    symbol_group.add_argument('--symbols', type=str, nargs='+', help='List of symbols to analyze/fill')
    symbol_group.add_argument('--sp500-stocks', action='store_true', help='Process all S&P 500 stocks')
    
    # Date range
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD, default: 5 years ago)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD, default: today)')
    
    # Operations
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze gaps, do not fill')
    parser.add_argument('--min-gap-size', type=int, default=1, help='Minimum gap size to fill (default: 1)')
    
    # Configuration
    parser.add_argument('--api-key', type=str, help='FMP API key (uses environment variable if not provided)')
    
    args = parser.parse_args()
    
    # Date setup
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date() if args.end_date else date.today()
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date() if args.start_date else (end_date - timedelta(days=5*365))
    
    # Symbol setup
    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = args.symbols
    elif args.sp500_stocks:
        gap_filler = SmartGapFiller(api_key=args.api_key)
        symbols = gap_filler.get_sp500_symbols()
        logger.info(f"Loaded {len(symbols)} S&P 500 symbols")
    
    if not symbols:
        logger.error("No symbols to process")
        return 1
    
    # Initialize gap filler
    gap_filler = SmartGapFiller(api_key=args.api_key)
    
    if args.analyze_only:
        # Only analyze gaps
        analyses = gap_filler.analyze_gaps(symbols, start_date, end_date)
        
        # Print summary
        symbols_with_gaps = [a for a in analyses if a.missing_days > 0]
        total_missing = sum(a.missing_days for a in analyses)
        
        print("\n" + "="*70)
        print("📊 GAP ANALYSIS SUMMARY")
        print("="*70)
        print(f"Total symbols: {len(analyses)}")
        print(f"Symbols with gaps: {len(symbols_with_gaps)}")
        print(f"Total missing days: {total_missing}")
        print(f"Average coverage: {sum(a.coverage_percentage for a in analyses) / len(analyses):.1f}%")
        
        if symbols_with_gaps:
            print(f"\nTop 10 symbols with most missing data:")
            for analysis in sorted(symbols_with_gaps, key=lambda x: x.missing_days, reverse=True)[:10]:
                print(f"  {analysis}")
    else:
        # Analyze and fill gaps
        summary = gap_filler.fill_gaps(symbols, start_date, end_date, args.min_gap_size)
        return 0 if summary['symbols_processed'] > 0 else 1


if __name__ == "__main__":
    exit(main())