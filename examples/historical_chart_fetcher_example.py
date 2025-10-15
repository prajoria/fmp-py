#!/usr/bin/env python3
"""
Example usage of FMP Historical Chart Fetcher
Demonstrates different ways to use the fetcher
"""

import sys
import os
from datetime import date, timedelta

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.fmp_historical_chart_fetcher import FmpHistoricalChartFetcher


def example_single_stock():
    """Example: Fetch data for a single stock"""
    print("=" * 60)
    print("EXAMPLE 1: Single Stock Fetch (AAPL)")
    print("=" * 60)
    
    fetcher = FmpHistoricalChartFetcher()
    
    # Fetch AAPL data for last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    success = fetcher.fetch_symbol_data(
        symbol='AAPL',
        start_date=start_date,
        end_date=end_date,
        resume_from_watermark=True
    )
    
    print(f"Fetch result: {'✅ Success' if success else '❌ Failed'}")


def example_popular_stocks():
    """Example: Fetch popular stocks"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Popular Stocks Batch Fetch")
    print("=" * 60)
    
    fetcher = FmpHistoricalChartFetcher()
    
    # Get first 5 popular stocks for demo
    popular_stocks = fetcher.POPULAR_STOCKS[:5]
    
    results = fetcher.fetch_batch(
        symbols=popular_stocks,
        resume_from_watermark=True
    )
    
    print(f"\nBatch results:")
    for symbol, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {symbol}: {status}")


def example_custom_symbols():
    """Example: Fetch custom list of symbols"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Symbols Fetch")
    print("=" * 60)
    
    fetcher = FmpHistoricalChartFetcher()
    
    # Custom list of tech stocks
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
    
    # Fetch data for last 90 days
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    results = fetcher.fetch_batch(
        symbols=tech_stocks,
        start_date=start_date,
        end_date=end_date,
        resume_from_watermark=False  # Force refresh for demo
    )
    
    print(f"\nTech stocks results:")
    for symbol, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {symbol}: {status}")


def example_progress_report():
    """Example: Show progress report"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Progress Report")
    print("=" * 60)
    
    fetcher = FmpHistoricalChartFetcher()
    
    # Show progress for first few popular stocks
    symbols_to_check = fetcher.POPULAR_STOCKS[:10]
    fetcher.print_progress_report(symbols_to_check)


def example_watermark_management():
    """Example: Working with watermarks"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Watermark Management")
    print("=" * 60)
    
    fetcher = FmpHistoricalChartFetcher()
    
    # Get watermark for AAPL
    watermark = fetcher.get_or_create_watermark('AAPL')
    
    print(f"AAPL Watermark Info:")
    print(f"  Symbol: {watermark.symbol}")
    print(f"  Earliest Date: {watermark.earliest_date}")
    print(f"  Latest Date: {watermark.latest_date}")
    print(f"  Total Records: {watermark.total_records}")
    print(f"  Status: {watermark.fetch_status}")
    print(f"  Error Count: {watermark.error_count}")


def main():
    """Run all examples"""
    print("🚀 FMP Historical Chart Fetcher Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_single_stock()
        example_popular_stocks()
        example_custom_symbols()
        example_progress_report()
        example_watermark_management()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())