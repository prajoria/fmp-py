#!/usr/bin/env python3
"""
FMP Cache CLI
=============
Command line interface for the FMP cache system.

Usage Examples:
---------------
# Fetch single stock for last year
python fmp_cache_cli.py fetch AAPL --days 365

# Fetch multiple stocks from file
python fmp_cache_cli.py fetch stocks.txt --start-date 2023-01-01 --end-date 2024-01-01

# Query cached data
python fmp_cache_cli.py query AAPL profile
python fmp_cache_cli.py query AAPL quote
python fmp_cache_cli.py query AAPL historical --from 2024-01-01 --to 2025-10-05

# Cache management
python fmp_cache_cli.py status
python fmp_cache_cli.py cleanup --dry-run
python fmp_cache_cli.py stats AAPL

#cd /home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis
python fmp_cache_cli.py fetch MSFT GOOGL TSLA --days 365
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache.stock_data_fetcher import StockDataFetcher
from cache.cache_manager import CacheManager
from api.fmp_cache_api import FMPCacheAPI
from utils.date_utils import parse_date_range


class FMPCacheCLI:
    """Command line interface for FMP cache operations"""
    
    def __init__(self):
        self.fetcher = None
        self.cache_manager = CacheManager()
        self.api = FMPCacheAPI()
    
    def _parse_symbols_input(self, symbols_input):
        """
        Parse symbols input which can be:
        - Single symbol: 'AAPL'
        - Comma-separated symbols: 'AAPL,MSFT,GOOGL'
        - Space-separated symbols: 'AAPL MSFT GOOGL'
        - File path: 'stocks.txt'
        """
        if not symbols_input:
            return []
        
        # Check if it's a file path
        if os.path.isfile(symbols_input):
            try:
                with open(symbols_input, 'r') as f:
                    symbols = []
                    for line in f:
                        line = line.strip().upper()
                        if line and not line.startswith('#'):
                            # Handle comma-separated in file
                            if ',' in line:
                                symbols.extend([s.strip() for s in line.split(',') if s.strip()])
                            else:
                                symbols.append(line)
                    return symbols
            except Exception as e:
                print(f"❌ Error reading symbols file: {e}")
                return []
        else:
            # Parse as symbol string(s)
            symbols_input = symbols_input.upper().strip()
            
            # Handle comma-separated
            if ',' in symbols_input:
                return [s.strip() for s in symbols_input.split(',') if s.strip()]
            # Handle space-separated
            elif ' ' in symbols_input:
                return [s.strip() for s in symbols_input.split() if s.strip()]
            # Single symbol
            else:
                return [symbols_input]
    
    def fetch_command(self, args):
        """Handle fetch command"""
        print("🚀 FMP Cache Data Fetcher")
        print("=" * 50)
        
        # Initialize fetcher
        try:
            self.fetcher = StockDataFetcher(api_key=args.api_key)
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("Set FMP_API_KEY environment variable or use --api-key")
            return 1
        
        # Parse symbols input
        symbols = self._parse_symbols_input(args.symbols)
        if not symbols:
            print("❌ No valid symbols provided")
            return 1
        
        print(f"📊 Symbols to process: {', '.join(symbols)}")
        
        # Parse date range
        if args.start_date and args.end_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=args.days)
        
        print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"🔄 Force Refresh: {args.force_refresh}")
        
        # Fetch data
        results = self.fetcher.fetch_batch(
            symbols, start_date, end_date, args.force_refresh
        )
        
        if results:
            print("\n✅ Fetch completed successfully!")
            return 0
        else:
            print("\n❌ Fetch failed!")
            return 1
    
    def query_command(self, args):
        """Handle query command"""
        symbol = args.symbol.upper()
        data_type = args.data_type
        
        print(f"🔍 Querying {data_type} for {symbol}")
        print("=" * 50)
        
        try:
            if data_type == 'profile':
                data = self.api.profile(symbol)
            elif data_type == 'quote':
                data = self.api.quote(symbol)
            elif data_type == 'historical':
                kwargs = {}
                if args.from_date:
                    kwargs['from_date'] = args.from_date
                if args.to_date:
                    kwargs['to_date'] = args.to_date
                data = self.api.historical_price_full(symbol, **kwargs)
            elif data_type == 'income':
                data = self.api.income_statement(symbol, limit=args.limit)
            elif data_type == 'balance':
                data = self.api.balance_sheet_statement(symbol, limit=args.limit)
            elif data_type == 'cashflow':
                data = self.api.cash_flow_statement(symbol, limit=args.limit)
            elif data_type == 'ratios':
                data = self.api.ratios(symbol, limit=args.limit)
            elif data_type == 'metrics':
                data = self.api.key_metrics(symbol, limit=args.limit)
            elif data_type == 'news':
                data = self.api.stock_news(tickers=symbol, limit=args.limit)
            else:
                print(f"❌ Unknown data type: {data_type}")
                return 1
            
            if data:
                if args.output == 'json':
                    print(json.dumps(data, indent=2, default=str))
                else:
                    self._print_formatted_data(data_type, data)
                return 0
            else:
                print(f"❌ No {data_type} data found for {symbol}")
                return 1
                
        except Exception as e:
            print(f"❌ Error querying data: {e}")
            return 1
    
    def status_command(self, args):
        """Handle status command"""
        print("📊 FMP Cache Status")
        print("=" * 50)
        
        try:
            health = self.api.health_check()
            
            print(f"Status: {health['status'].upper()}")
            print(f"Database: {health.get('database', 'unknown')}")
            print(f"Timestamp: {health['timestamp']}")
            
            if 'cache_stats' in health:
                stats = health['cache_stats']
                print(f"\nCache Statistics:")
                print(f"  Total Symbols: {stats.get('total_symbols', 0):,}")
                print(f"  Total Records: {stats.get('total_records', 0):,}")
                
                if 'data_types' in stats:
                    print(f"\nData Types:")
                    for data_type, count in stats['data_types'].items():
                        if count > 0:
                            print(f"  {data_type.replace('_', ' ').title()}: {count:,}")
                
                if 'freshness_summary' in stats:
                    print(f"\nFreshness Summary:")
                    for data_type, freshness in stats['freshness_summary'].items():
                        fresh_pct = freshness.get('fresh_percentage', 0)
                        print(f"  {data_type}: {fresh_pct:.1f}% fresh")
            
            return 0 if health['status'] == 'healthy' else 1
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return 1
    
    def cleanup_command(self, args):
        """Handle cleanup command"""
        print("🧹 Cache Cleanup")
        print("=" * 50)
        
        try:
            deleted_counts = self.cache_manager.cleanup_expired_data(dry_run=args.dry_run)
            
            if deleted_counts:
                total_deleted = sum(deleted_counts.values())
                if args.dry_run:
                    print(f"Would delete {total_deleted:,} expired records:")
                else:
                    print(f"Deleted {total_deleted:,} expired records:")
                
                for table, count in deleted_counts.items():
                    print(f"  {table}: {count:,}")
            else:
                print("No expired records found.")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return 1
    
    def stats_command(self, args):
        """Handle stats command"""
        symbol = args.symbol.upper() if args.symbol else None
        
        if symbol:
            print(f"📈 Cache Statistics for {symbol}")
        else:
            print("📈 Overall Cache Statistics")
        print("=" * 50)
        
        try:
            stats = self.cache_manager.get_cache_statistics(symbol)
            
            print(f"Total Symbols: {stats.get('total_symbols', 0):,}")
            print(f"Total Records: {stats.get('total_records', 0):,}")
            
            if 'data_types' in stats:
                print(f"\nData Types:")
                for data_type, count in stats['data_types'].items():
                    if count > 0:
                        print(f"  {data_type.replace('_', ' ').title()}: {count:,}")
            
            if 'freshness_summary' in stats:
                print(f"\nFreshness Summary:")
                for data_type, freshness in stats['freshness_summary'].items():
                    total = freshness.get('total', 0)
                    fresh = freshness.get('fresh', 0)
                    fresh_pct = freshness.get('fresh_percentage', 0)
                    print(f"  {data_type}: {fresh:,}/{total:,} ({fresh_pct:.1f}%) fresh")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return 1
    
    def _print_formatted_data(self, data_type: str, data):
        """Print data in formatted way"""
        if data_type == 'profile' and data:
            profile = data[0]
            print(f"Company: {profile.get('companyName', 'N/A')}")
            print(f"Sector: {profile.get('sector', 'N/A')}")
            print(f"Industry: {profile.get('industry', 'N/A')}")
            print(f"Market Cap: ${profile.get('mktCap', 0):,.0f}")
            print(f"CEO: {profile.get('ceo', 'N/A')}")
            print(f"Website: {profile.get('website', 'N/A')}")
            
        elif data_type == 'quote' and data:
            quote = data[0]
            print(f"Price: ${quote.get('price', 0):.2f}")
            print(f"Change: {quote.get('change', 0):+.2f} ({quote.get('changesPercentage', 0):+.2f}%)")
            print(f"Volume: {quote.get('volume', 0):,}")
            print(f"Market Cap: ${quote.get('marketCap', 0):,.0f}")
            
        elif data_type == 'historical' and data:
            historical = data.get('historical', [])
            print(f"Symbol: {data.get('symbol')}")
            print(f"Records: {len(historical)}")
            if historical:
                print("\nRecent Prices:")
                for i, price in enumerate(historical[:5]):
                    print(f"  {price.get('date')}: ${price.get('close', 0):.2f}")
                    
        elif data_type in ['income', 'balance', 'cashflow'] and data:
            print(f"Records: {len(data)}")
            if data:
                latest = data[0]
                print(f"Latest Period: {latest.get('date', 'N/A')}")
                if data_type == 'income':
                    print(f"Revenue: ${latest.get('revenue', 0):,.0f}")
                    print(f"Net Income: ${latest.get('netIncome', 0):,.0f}")
                    
        elif data_type == 'news' and data:
            print(f"Articles: {len(data)}")
            for i, article in enumerate(data[:3]):
                print(f"\n{i+1}. {article.get('title', 'N/A')}")
                print(f"   {article.get('site', 'N/A')} - {article.get('publishedDate', 'N/A')}")
                
        else:
            print(json.dumps(data, indent=2, default=str))


def create_sample_stocks_file():
    """Create a sample stocks file for demonstration"""
    sample_stocks = [
        "AAPL",  # Apple Inc.
        "MSFT",  # Microsoft Corp.
        "GOOGL", # Alphabet Inc.
        "AMZN",  # Amazon.com Inc.
        "TSLA",  # Tesla Inc.
        "META",  # Meta Platforms Inc.
        "NVDA",  # NVIDIA Corp.
        "NFLX",  # Netflix Inc.
        "AMD",   # Advanced Micro Devices
        "CRM"    # Salesforce Inc.
    ]
    
    with open('sample_stocks.txt', 'w') as f:
        for stock in sample_stocks:
            f.write(f"{stock}\n")
    
    print("📝 Created sample_stocks.txt with popular tech stocks")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FMP Cache CLI - Intelligent financial data caching and querying",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s fetch AAPL --days 365
  %(prog)s fetch AAPL,MSFT,GOOGL --days 730
  %(prog)s fetch "SPY,VOO,QQQ" --start-date 2023-01-01 --end-date 2024-01-01
  %(prog)s fetch stocks.txt --start-date 2023-01-01 --end-date 2024-01-01
  %(prog)s query AAPL profile
  %(prog)s query AAPL historical --from 2024-01-01 --to 2024-12-31
  %(prog)s status
  %(prog)s cleanup --dry-run
  %(prog)s stats AAPL
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch stock data from FMP API')
    fetch_parser.add_argument('symbols', help='Single symbol (AAPL), comma-separated (AAPL,MSFT,GOOGL), or file path')
    fetch_parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    fetch_parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    fetch_parser.add_argument('--days', type=int, default=365, help='Days back from today (default: 365)')
    fetch_parser.add_argument('--force-refresh', action='store_true', help='Force refresh cached data')
    fetch_parser.add_argument('--api-key', type=str, help='FMP API key')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query cached data')
    query_parser.add_argument('symbol', help='Stock symbol')
    query_parser.add_argument('data_type', choices=[
        'profile', 'quote', 'historical', 'income', 'balance', 
        'cashflow', 'ratios', 'metrics', 'news'
    ], help='Type of data to query')
    query_parser.add_argument('--from', dest='from_date', help='From date (YYYY-MM-DD)')
    query_parser.add_argument('--to', dest='to_date', help='To date (YYYY-MM-DD)')
    query_parser.add_argument('--limit', type=int, default=10, help='Limit number of records')
    query_parser.add_argument('--output', choices=['table', 'json'], default='table', help='Output format')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show cache status')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up expired cache data')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    stats_parser.add_argument('symbol', nargs='?', help='Symbol to get stats for (optional)')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Create sample stocks file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = FMPCacheCLI()
    
    try:
        if args.command == 'fetch':
            return cli.fetch_command(args)
        elif args.command == 'query':
            return cli.query_command(args)
        elif args.command == 'status':
            return cli.status_command(args)
        elif args.command == 'cleanup':
            return cli.cleanup_command(args)
        elif args.command == 'stats':
            return cli.stats_command(args)
        elif args.command == 'sample':
            create_sample_stocks_file()
            return 0
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())