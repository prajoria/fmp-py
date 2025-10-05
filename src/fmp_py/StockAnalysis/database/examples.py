#!/usr/bin/env python3
"""
Example usage of FMP cached client with MySQL database caching
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.cached_fmp_client import create_cached_client
from database import execute_query, company_dal, quote_dal, historical_price_dal


def example_basic_usage():
    """Example 1: Basic usage with automatic caching"""
    print("\n" + "="*60)
    print("Example 1: Basic Usage with Caching")
    print("="*60)
    
    # Create cached client
    client = create_cached_client(enable_cache=True)
    
    # First call - will hit API and cache result
    print("\n1. Fetching AAPL quote (first call - from API)...")
    quote1 = client.get_quote("AAPL")
    print(f"   Price: ${quote1['price']:.2f}")
    print(f"   Change: {quote1['changesPercentage']:.2f}%")
    
    # Second call - will use cache
    print("\n2. Fetching AAPL quote again (from cache)...")
    quote2 = client.get_quote("AAPL")
    print(f"   Price: ${quote2['price']:.2f}")
    print(f"   Change: {quote2['changesPercentage']:.2f}%")
    
    # Get company profile
    print("\n3. Fetching AAPL profile...")
    profile = client.get_company_profile("AAPL")
    if profile:
        print(f"   Company: {profile[0]['companyName']}")
        print(f"   Sector: {profile[0]['sector']}")
        print(f"   Industry: {profile[0]['industry']}")
        print(f"   Market Cap: ${profile[0]['mktCap']:,}")


def example_cache_statistics():
    """Example 2: View cache statistics"""
    print("\n" + "="*60)
    print("Example 2: Cache Statistics")
    print("="*60)
    
    client = create_cached_client(enable_cache=True)
    
    stats = client.get_cache_stats()
    
    print(f"\nCache Status: {'Enabled' if stats['cache_enabled'] else 'Disabled'}")
    print(f"Cached Companies: {stats.get('companies', 0):,}")
    print(f"Cached Quotes: {stats.get('quotes', 0):,}")
    print(f"Daily Price Records: {stats.get('historical_prices_daily', 0):,}")
    print(f"Income Statements: {stats.get('income_statements', 0):,}")
    print(f"Balance Sheets: {stats.get('balance_sheets', 0):,}")
    
    if 'cache_hit_rate_24h' in stats:
        hit_rate = stats['cache_hit_rate_24h']
        print(f"\nLast 24 Hours:")
        print(f"  Total Requests: {hit_rate['total_requests']}")
        print(f"  Cache Hits: {hit_rate['cache_hits']}")
        print(f"  Hit Rate: {hit_rate['hit_rate_percent']}%")


def example_direct_database_access():
    """Example 3: Direct database queries"""
    print("\n" + "="*60)
    print("Example 3: Direct Database Access")
    print("="*60)
    
    # Get company from cache
    print("\n1. Get company profile from database...")
    profile = company_dal.get_company_profile("AAPL")
    if profile:
        print(f"   Company: {profile.get('company_name')}")
        print(f"   Sector: {profile.get('sector')}")
        print(f"   Cached at: {profile.get('cached_at')}")
    
    # Get quote from cache
    print("\n2. Get quote from database...")
    quote = quote_dal.get_quote("AAPL")
    if quote:
        print(f"   Price: ${quote['price']:.2f}")
        print(f"   Volume: {quote['volume']:,}")
        print(f"   Cached at: {quote['cached_at']}")


def example_historical_data():
    """Example 4: Historical price data"""
    print("\n" + "="*60)
    print("Example 4: Historical Price Data")
    print("="*60)
    
    client = create_cached_client(enable_cache=True)
    
    # Get 30 days of historical data
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\nFetching AAPL historical prices from {start_date} to {end_date}...")
    historical = client.get_historical_prices(
        "AAPL", 
        from_date=start_date,
        to_date=end_date
    )
    
    if historical and 'historical' in historical:
        prices = historical['historical'][:5]  # Show first 5
        print(f"\nFound {len(historical['historical'])} days of data")
        print("\nFirst 5 records:")
        for price in prices:
            print(f"  {price['date']}: "
                  f"Open=${price['open']:.2f}, "
                  f"Close=${price['close']:.2f}, "
                  f"Volume={price['volume']:,}")


def example_advanced_queries():
    """Example 5: Advanced SQL queries"""
    print("\n" + "="*60)
    print("Example 5: Advanced SQL Queries")
    print("="*60)
    
    # Top tech companies by market cap
    print("\n1. Top 10 Technology Companies by Market Cap...")
    results = execute_query("""
        SELECT 
            c.symbol,
            c.name,
            cp.sector,
            q.price,
            q.market_cap
        FROM companies c
        JOIN company_profiles cp ON c.symbol = cp.symbol
        JOIN quotes q ON c.symbol = q.symbol
        WHERE cp.sector = 'Technology'
            AND q.expires_at > NOW()
        ORDER BY q.market_cap DESC
        LIMIT 10
    """)
    
    if results:
        for i, row in enumerate(results, 1):
            print(f"  {i}. {row['symbol']:6} - {row['name']:30} "
                  f"${row['price']:8.2f}  MCap: ${row['market_cap']:,}")
    
    # Companies with recent price changes
    print("\n2. Biggest Movers Today...")
    results = execute_query("""
        SELECT 
            symbol,
            price,
            `change`,
            changes_percentage
        FROM quotes
        WHERE expires_at > NOW()
        ORDER BY ABS(changes_percentage) DESC
        LIMIT 10
    """)
    
    if results:
        for row in results:
            direction = "🔺" if row['change'] > 0 else "🔻"
            print(f"  {direction} {row['symbol']:6} "
                  f"${row['price']:8.2f}  "
                  f"{row['changes_percentage']:+.2f}%")


def example_portfolio_analysis():
    """Example 6: Portfolio analysis"""
    print("\n" + "="*60)
    print("Example 6: Portfolio Analysis")
    print("="*60)
    
    portfolio_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    client = create_cached_client(enable_cache=True)
    
    print("\nFetching data for portfolio symbols...")
    total_value = 0
    total_change = 0
    
    for symbol in portfolio_symbols:
        quote = client.get_quote(symbol)
        if quote:
            shares = 10  # Example: 10 shares of each
            value = quote['price'] * shares
            change = quote['change'] * shares
            
            total_value += value
            total_change += change
            
            print(f"\n{symbol}:")
            print(f"  Price: ${quote['price']:.2f}")
            print(f"  Change: ${quote['change']:.2f} ({quote['changesPercentage']:.2f}%)")
            print(f"  Position Value: ${value:.2f}")
    
    print(f"\n{'='*40}")
    print(f"Total Portfolio Value: ${total_value:.2f}")
    print(f"Total Change: ${total_change:.2f}")
    print(f"Portfolio Change: {(total_change/total_value)*100:.2f}%")


def example_cache_maintenance():
    """Example 7: Cache maintenance"""
    print("\n" + "="*60)
    print("Example 7: Cache Maintenance")
    print("="*60)
    
    client = create_cached_client(enable_cache=True)
    
    # Cleanup expired cache
    print("\n1. Cleaning up expired cache entries...")
    deleted = client.cleanup_expired_cache()
    print(f"   Deleted {deleted} expired records")
    
    # Cleanup old logs
    print("\n2. Cleaning up old API request logs...")
    deleted = client.cleanup_old_logs(days=30)
    print(f"   Deleted {deleted} log entries older than 30 days")
    
    # Force refresh
    print("\n3. Forcing refresh of AAPL quote...")
    success = client.force_refresh("AAPL", "quote")
    if success:
        print("   Successfully cleared cached quote")
        # Now fetch fresh data
        quote = client.get_quote("AAPL")
        print(f"   Fresh quote fetched: ${quote['price']:.2f}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("FMP MySQL Cache - Usage Examples")
    print("="*60)
    
    try:
        # Check if API key is set
        api_key = os.getenv('FMP_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            print("\n⚠️  WARNING: FMP_API_KEY not set in .env file")
            print("   Please set your API key before running examples")
            return
        
        example_basic_usage()
        example_cache_statistics()
        example_direct_database_access()
        example_historical_data()
        example_advanced_queries()
        example_portfolio_analysis()
        example_cache_maintenance()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
