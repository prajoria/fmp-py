#!/usr/bin/env python3
"""
Monitor S&P 500 Gap Filling Progress
"""

import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

def get_progress_stats():
    """Get current progress statistics"""
    db_config = {
        'host': os.getenv('FMP_DB_HOST', 'localhost'),
        'user': os.getenv('FMP_DB_USER', 'fmp_user'),
        'password': os.getenv('FMP_DB_PASSWORD', 'fmp_password'),
        'database': os.getenv('FMP_DB_NAME', 'fmp_cache'),
        'charset': 'utf8mb4'
    }
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Date range for last 5 years
        end_date = date.today()
        start_date = end_date - timedelta(days=5*365)
        
        # Total S&P 500 symbols
        cursor.execute("SELECT COUNT(*) FROM sp500_constituents WHERE is_active = 1")
        total_symbols = cursor.fetchone()[0]
        
        # Symbols with data in date range
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) 
            FROM historical_prices_daily 
            WHERE symbol IN (SELECT symbol FROM sp500_constituents WHERE is_active = 1)
            AND date BETWEEN %s AND %s
        """, (start_date, end_date))
        symbols_with_data = cursor.fetchone()[0]
        
        # Total records in date range
        cursor.execute("""
            SELECT COUNT(*) 
            FROM historical_prices_daily 
            WHERE symbol IN (SELECT symbol FROM sp500_constituents WHERE is_active = 1)
            AND date BETWEEN %s AND %s
        """, (start_date, end_date))
        total_records = cursor.fetchone()[0]
        
        # Expected trading days (approximately 252 per year * 5 years = 1260)
        expected_days_per_symbol = 1260  # Rough estimate
        expected_total_records = total_symbols * expected_days_per_symbol
        
        completion_pct = (total_records / expected_total_records) * 100 if expected_total_records > 0 else 0
        
        print(f"📊 S&P 500 Historical Data Progress")
        print(f"=" * 50)
        print(f"Total S&P 500 symbols: {total_symbols}")
        print(f"Symbols with data: {symbols_with_data}")
        print(f"Symbol coverage: {(symbols_with_data/total_symbols)*100:.1f}%")
        print(f"Total records stored: {total_records:,}")
        print(f"Expected records: ~{expected_total_records:,}")
        print(f"Data completion: ~{completion_pct:.1f}%")
        print(f"Date range: {start_date} to {end_date}")
        
        return {
            'total_symbols': total_symbols,
            'symbols_with_data': symbols_with_data,
            'total_records': total_records,
            'completion_pct': completion_pct
        }
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    get_progress_stats()