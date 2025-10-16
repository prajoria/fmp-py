#!/usr/bin/env python3
"""
Simple Smart Gap Filler for Historical Data
===========================================
Lightweight version that directly connects to MySQL to analyze and fill data gaps.
Avoids complex import chains and uses minimal database connections.
"""

import os
import mysql.connector
import requests
import time
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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


class SimpleGapFiller:
    """Simple gap filler with direct database connections"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FMP_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set FMP_API_KEY environment variable or pass as parameter.")
        
        # Database config
        self.db_config = {
            'host': os.getenv('FMP_DB_HOST', 'localhost'),
            'port': int(os.getenv('FMP_DB_PORT', '3306')),
            'database': os.getenv('FMP_DB_NAME', 'fmp_cache'),
            'user': os.getenv('FMP_DB_USER', 'fmp_user'),
            'password': os.getenv('FMP_DB_PASSWORD', 'fmp_password'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        self.session_id = f"gap_fill_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Initialized SimpleGapFiller with session ID: {self.session_id}")
    
    def get_db_connection(self):
        """Get a direct database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def get_trading_days(self, start_date: date, end_date: date) -> Set[date]:
        """Generate expected trading days (excluding weekends)"""
        trading_days = set()
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                trading_days.add(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def analyze_symbol_gaps(self, symbol: str, start_date: date, end_date: date) -> GapAnalysis:
        """Analyze gaps in historical data for a symbol"""
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get existing dates from database
            cursor.execute("""
                SELECT DISTINCT date 
                FROM historical_prices_daily 
                WHERE symbol = %s AND date BETWEEN %s AND %s 
                ORDER BY date
            """, (symbol.upper(), start_date, end_date))
            
            existing_dates = {row['date'] for row in cursor.fetchall()}
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
            
        finally:
            cursor.close()
            conn.close()
    
    def fetch_historical_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch historical data from FMP API"""
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {
            'from': start_date,
            'to': end_date,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'historical' in data:
                return data['historical']
            else:
                logger.warning(f"No historical data found for {symbol}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []
    
    def store_historical_data(self, symbol: str, historical_data: List[Dict]) -> int:
        """Store historical data in database"""
        if not historical_data:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Prepare batch data
            batch_data = []
            for record in historical_data:
                try:
                    batch_data.append((
                        symbol.upper(),
                        datetime.strptime(record['date'], '%Y-%m-%d').date(),
                        float(record['open']) if record['open'] else None,
                        float(record['high']) if record['high'] else None,
                        float(record['low']) if record['low'] else None,
                        float(record['close']) if record['close'] else None,
                        float(record.get('adjClose', record['close'])) if record.get('adjClose') or record['close'] else None,
                        int(record['volume']) if record['volume'] else None,
                        int(record.get('unadjustedVolume', record['volume'])) if record.get('unadjustedVolume') or record['volume'] else None,
                        float(record.get('change', 0)) if record.get('change') else None,
                        float(record.get('changePercent', 0)) if record.get('changePercent') else None,
                        float(record.get('vwap')) if record.get('vwap') else None,
                        record.get('label', ''),
                        float(record.get('changeOverTime', 0)) if record.get('changeOverTime') else None
                    ))
                except Exception as e:
                    logger.error(f"Error preparing record for {symbol}: {e}")
                    continue
            
            if not batch_data:
                return 0
            
            # Batch insert
            cursor.executemany("""
                INSERT INTO historical_prices_daily (
                    symbol, date, `open`, high, low, `close`, adj_close, volume,
                    unadjusted_volume, `change`, change_percent, vwap, label, change_over_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                `open` = VALUES(`open`), high = VALUES(high), low = VALUES(low),
                `close` = VALUES(`close`), adj_close = VALUES(adj_close), volume = VALUES(volume),
                unadjusted_volume = VALUES(unadjusted_volume), `change` = VALUES(`change`),
                change_percent = VALUES(change_percent), vwap = VALUES(vwap),
                label = VALUES(label), change_over_time = VALUES(change_over_time)
            """, batch_data)
            
            conn.commit()
            return len(batch_data)
            
        except Exception as e:
            logger.error(f"Error storing data for {symbol}: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def fill_symbol_gaps(self, symbol: str, gaps: List[DateGap]) -> int:
        """Fill gaps for a specific symbol"""
        total_records = 0
        
        for gap in gaps:
            try:
                logger.info(f"Filling gap for {symbol}: {gap.start_date} to {gap.end_date}")
                
                # Fetch data for the gap period
                historical_data = self.fetch_historical_data(
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
                time.sleep(0.25)  # 4 calls per second
                
            except Exception as e:
                logger.error(f"❌ Error filling gap for {symbol} ({gap.start_date} to {gap.end_date}): {e}")
                continue
        
        return total_records
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols from database"""
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT symbol FROM sp500_constituents 
                WHERE is_active = 1 
                ORDER BY symbol
            """)
            return [row['symbol'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching S&P 500 symbols: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def analyze_gaps(self, symbols: List[str], start_date: date, end_date: date) -> List[GapAnalysis]:
        """Analyze gaps for multiple symbols"""
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
        """Fill gaps for multiple symbols"""
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
    parser = argparse.ArgumentParser(description='Simple Smart Gap Filler for Historical Data')
    
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
    
    # Initialize gap filler
    gap_filler = SimpleGapFiller(api_key=args.api_key)
    
    # Symbol setup
    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = args.symbols
    elif args.sp500_stocks:
        symbols = gap_filler.get_sp500_symbols()
        logger.info(f"Loaded {len(symbols)} S&P 500 symbols")
    
    if not symbols:
        logger.error("No symbols to process")
        return 1
    
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