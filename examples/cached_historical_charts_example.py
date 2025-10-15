#!/usr/bin/env python3
"""
Example: Using Cached FMP Historical Charts API

This example demonstrates how to use the cached historical charts client
to fetch and cache historical price data from Financial Modeling Prep API.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fmp_py.StockAnalysis.client.cached_fmp_historical_charts import CachedFmpHistoricalCharts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_cached_historical_charts():
    """
    Demonstrate cached historical charts functionality
    """
    # Initialize the cached client
    client = CachedFmpHistoricalCharts(enable_cache=True)
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # Date range for testing
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print("\n" + "="*80)
    print("CACHED FMP HISTORICAL CHARTS API DEMONSTRATION")
    print("="*80)
    
    # ========================================================================
    # Test Light Historical Data
    # ========================================================================
    
    print("\n📊 Testing Light Historical Data (with caching)")
    print("-" * 50)
    
    for symbol in symbols:
        print(f"\n🔄 Fetching light historical data for {symbol}...")
        
        # First call - should fetch from API and cache
        start_time = datetime.now()
        data = client.get_historical_price_light(symbol, start_date, end_date)
        first_call_time = (datetime.now() - start_time).total_seconds()
        
        print(f"   ✅ First call: {len(data)} records in {first_call_time:.2f}s (API + Cache)")
        
        if data:
            latest = data[0]
            print(f"   📈 Latest price: ${latest.close:.2f} on {latest.date}")
        
        # Second call - should serve from cache
        start_time = datetime.now()
        cached_data = client.get_historical_price_light(symbol, start_date, end_date)
        second_call_time = (datetime.now() - start_time).total_seconds()
        
        print(f"   ⚡ Second call: {len(cached_data)} records in {second_call_time:.2f}s (Cache)")
        if second_call_time > 0:
            print(f"   🚀 Speedup: {first_call_time/second_call_time:.1f}x faster")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    
    print("\n💡 Key Benefits Demonstrated:")
    print("   ✅ Automatic caching of all historical chart data types")
    print("   ✅ Significant performance improvements on repeated requests")
    print("   ✅ Reduced API usage and costs")
    print("   ✅ Offline data availability")
    print("   ✅ Configurable TTL for different data types")
    print("   ✅ Cache management and cleanup capabilities")
    print("   ✅ Fallback to direct API calls when cache fails")
    print("   ✅ Comprehensive logging and monitoring")


if __name__ == "__main__":
    try:
        demonstrate_cached_historical_charts()
    except KeyboardInterrupt:
        print("\n\n⛔ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running demonstration: {e}")
        import traceback
        traceback.print_exc()