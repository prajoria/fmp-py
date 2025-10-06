#!/usr/bin/env python3
"""
FMP Cache System - Getting Started
==================================

A simple script to get you started with the FMP Cache System.
This script will:
1. Help you set up your API key
2. Fetch sample data for a few stocks
3. Show you how to query the cached data
4. Give you next steps for advanced usage

Run this script first to get familiar with the system.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from cache.stock_data_fetcher import StockDataFetcher
    from api.fmp_cache_api import FMPCacheAPI
    from utils.date_utils import parse_date_range
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the StockAnalysis directory")
    sys.exit(1)


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_step(step: int, title: str):
    """Print a step header"""
    print(f"\n📋 Step {step}: {title}")
    print("-" * 40)


def check_api_key():
    """Check if API key is configured"""
    api_key = os.getenv('FMP_API_KEY')
    
    if not api_key:
        print("❌ FMP_API_KEY environment variable not found!")
        print("\n🔧 To set up your API key:")
        print("1. Get a free API key from https://financialmodelingprep.com/")
        print("2. Set the environment variable:")
        print("   Linux/Mac: export FMP_API_KEY='your_api_key_here'")
        print("   Windows: set FMP_API_KEY=your_api_key_here")
        print("3. Or add it to your .bashrc/.profile for persistence")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    return True


def fetch_sample_data():
    """Fetch sample data for a few popular stocks"""
    print("Fetching sample data for popular stocks...")
    
    # Popular stocks to demonstrate with
    stocks = ["AAPL", "MSFT", "GOOGL"]
    
    try:
        fetcher = StockDataFetcher()
        
        # Get data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"📈 Stocks: {', '.join(stocks)}")
        
        results = fetcher.fetch_batch(stocks, start_date, end_date)
        
        print(f"\n📊 Fetching completed!")
        print(f"  API Calls: {fetcher.stats['api_calls']}")
        print(f"  Cache Hits: {fetcher.stats['cache_hits']}")
        print(f"  Symbols Processed: {fetcher.stats['symbols_processed']}")
        print(f"  Errors: {fetcher.stats['errors']}")
        
        if fetcher.stats['errors'] > 0:
            print(f"⚠️  Some errors occurred. Check your API key and internet connection.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return False


def query_sample_data():
    """Query the cached data using the FMP API"""
    print("Querying cached data using FMP-compatible API...")
    
    api = FMPCacheAPI()
    symbol = "AAPL"
    
    print(f"\n🍎 Getting data for {symbol}:")
    
    # Company profile
    print("\n📊 Company Profile:")
    profile = api.profile(symbol)
    if profile:
        p = profile[0]
        print(f"  Company: {p.get('companyName', 'N/A')}")
        print(f"  Sector: {p.get('sector', 'N/A')}")
        print(f"  CEO: {p.get('ceo', 'N/A')}")
        print(f"  Employees: {p.get('fullTimeEmployees', 0):,}")
    else:
        print("  ❌ No profile data found")
    
    # Current quote
    print("\n💰 Current Quote:")
    quote = api.quote(symbol)
    if quote:
        q = quote[0]
        print(f"  Price: ${q.get('price', 0):.2f}")
        print(f"  Change: {q.get('changesPercentage', 0):+.2f}%")
        print(f"  Volume: {q.get('volume', 0):,}")
        print(f"  Market Cap: ${q.get('marketCap', 0):,.0f}")
    else:
        print("  ❌ No quote data found")
    
    # Historical prices (last 5 days)
    print("\n📈 Recent Prices (Last 5 Days):")
    historical = api.historical_price_full(symbol)
    if historical and historical.get('historical'):
        prices = historical['historical'][:5]
        for price in prices:
            date = price.get('date', 'N/A')
            close = price.get('close', 0)
            change = price.get('changePercent', 0)
            print(f"  {date}: ${close:.2f} ({change:+.2f}%)")
    else:
        print("  ❌ No historical data found")


def show_cache_efficiency():
    """Demonstrate cache efficiency"""
    print("Demonstrating cache efficiency...")
    
    # Second fetch should be much faster
    stocks = ["AAPL", "MSFT"]
    
    try:
        fetcher = StockDataFetcher()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Fetching same data again (should use cache)...")
        
        import time
        start_time = time.time()
        results = fetcher.fetch_batch(stocks, start_date, end_date)
        end_time = time.time()
        
        print(f"\n⚡ Second fetch completed in {end_time - start_time:.2f} seconds!")
        print(f"  API Calls: {fetcher.stats['api_calls']} (should be 0 or very low)")
        print(f"  Cache Hits: {fetcher.stats['cache_hits']} (should be high)")
        
        if fetcher.stats['api_calls'] == 0:
            print("✅ Perfect! All data served from cache.")
        elif fetcher.stats['api_calls'] < 5:
            print("✅ Excellent! Most data served from cache.")
        else:
            print("⚠️  More API calls than expected. Data might not be cached yet.")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def show_next_steps():
    """Show next steps for using the system"""
    print("\n🎯 Next Steps:")
    print("1. 📝 Try the CLI interface:")
    print("   python fmp_cache_cli.py --help")
    print("   python fmp_cache_cli.py fetch TSLA --days 365")
    print("   python fmp_cache_cli.py query TSLA")
    
    print("\n2. 📊 Run the complete demo:")
    print("   python examples/complete_demo.py")
    
    print("\n3. 📁 Fetch multiple stocks from a file:")
    print("   python fmp_cache_cli.py sample  # Create sample file")
    print("   python fmp_cache_cli.py fetch --file stocks.txt")
    
    print("\n4. 🔍 Check cache status:")
    print("   python fmp_cache_cli.py status")
    print("   python fmp_cache_cli.py stats")
    
    print("\n5. 🧹 Manage cache:")
    print("   python fmp_cache_cli.py cleanup --older-than 30")
    
    print("\n6. 💻 Use in your Python code:")
    print("   from api.fmp_cache_api import FMPCacheAPI")
    print("   api = FMPCacheAPI()")
    print("   data = api.profile('AAPL')")
    
    print("\n📚 Documentation: docs/README.md")
    print("💡 Examples: examples/ directory")


def main():
    """Main getting started workflow"""
    print_header("FMP CACHE SYSTEM - GETTING STARTED")
    
    print("Welcome to the FMP Cache System! 🎉")
    print("This system helps you cache Financial Modeling Prep data locally")
    print("to reduce API calls and improve performance.")
    
    try:
        # Step 1: Check API key
        print_step(1, "Checking API Key Configuration")
        if not check_api_key():
            return 1
        
        # Step 2: Fetch sample data
        print_step(2, "Fetching Sample Data")
        if not fetch_sample_data():
            print("⚠️  Data fetching failed, but you can still explore the system")
        
        # Step 3: Query cached data
        print_step(3, "Querying Cached Data")
        query_sample_data()
        
        # Step 4: Demonstrate cache efficiency
        print_step(4, "Demonstrating Cache Efficiency")
        show_cache_efficiency()
        
        # Step 5: Show next steps
        print_step(5, "What's Next?")
        show_next_steps()
        
        print_header("GETTING STARTED COMPLETE")
        print("✅ You're all set up! The FMP Cache System is ready to use.")
        print("🚀 Start exploring with the CLI or run the complete demo.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Getting started interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())