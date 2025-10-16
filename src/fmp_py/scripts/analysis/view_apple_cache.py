#!/usr/bin/env python3
"""
Apple Cache Viewer
==================
View all Apple fundamental data stored in the FMP MySQL cache
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Use relative imports
from ...StockAnalysis.database.connection import get_db

class AppleCacheViewer:
    """View Apple data from MySQL cache"""
    
    def __init__(self):
        self.db = get_db()
        self.symbol = "AAPL"
    
    def show_company_profile(self):
        """Show company profile (using companies table)"""
        print("\n🍎 APPLE INC. COMPANY INFO")
        print("=" * 60)
        
        company = self.db.execute_query("""
            SELECT name, exchange, exchange_short_name, type, currency, 
                   country, is_etf, is_actively_trading, created_at, updated_at
            FROM companies 
            WHERE symbol = %s
        """, (self.symbol,), fetch='one')
        
        if company:
            print(f"Company: {company['name']}")
            print(f"Exchange: {company['exchange']} ({company['exchange_short_name']})")
            print(f"Type: {company['type']}")
            print(f"Currency: {company['currency']}")
            print(f"Country: {company['country']}")
            print(f"Is ETF: {company['is_etf']}")
            print(f"Actively Trading: {company['is_actively_trading']}")
            print(f"Created: {company['created_at']}")
            print(f"Last Updated: {company['updated_at']}")
        else:
            print("No company data found")
    
    def show_latest_quote(self):
        """Show latest quote (using historical prices)"""
        print("\n💰 CURRENT QUOTE")
        print("=" * 60)
        
        quote = self.db.execute_query("""
            SELECT `close` as price, `change`, change_percent, high, low, volume, date
            FROM historical_prices_daily 
            WHERE symbol = %s
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if quote:
            print(f"Latest Price: ${quote['price']:,.2f}" if quote['price'] else "Price: N/A")
            print(f"Change: ${quote['change']:+,.2f} ({quote['change_percent']:+.2f}%)" if quote['change'] and quote['change_percent'] else "Change: N/A")
            print(f"Day High: ${quote['high']:,.2f}" if quote['high'] else "High: N/A")
            print(f"Day Low: ${quote['low']:,.2f}" if quote['low'] else "Low: N/A")
            print(f"Volume: {quote['volume']:,}" if quote['volume'] else "Volume: N/A")
            print(f"Date: {quote['date']}" if quote['date'] else "Date: N/A")
            print(f"EPS: ${quote['eps']:.2f}" if quote['eps'] else "EPS: N/A")
            print(f"Last Updated: {quote['cached_at']}")
        else:
            print("No quote data found")
    
    def show_financial_statements(self):
        """Show latest financial statements"""
        print("\n📊 FINANCIAL STATEMENTS (Latest Annual)")
        print("=" * 60)
        
        # Income Statement
        income = self.db.execute_query("""
            SELECT date, revenue, gross_profit, operating_income, net_income, eps
            FROM income_statements 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if income:
            print(f"\n📈 Income Statement ({income['date']})")
            print(f"Revenue: ${income['revenue']:,.0f}")
            print(f"Gross Profit: ${income['gross_profit']:,.0f}")
            print(f"Operating Income: ${income['operating_income']:,.0f}")
            print(f"Net Income: ${income['net_income']:,.0f}")
            print(f"EPS: ${income['eps']:.2f}")
        
        # Balance Sheet
        balance = self.db.execute_query("""
            SELECT date, total_assets, total_liabilities, total_stockholders_equity, 
                   cash_and_cash_equivalents, total_debt
            FROM balance_sheets 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if balance:
            print(f"\n🏦 Balance Sheet ({balance['date']})")
            print(f"Total Assets: ${balance['total_assets']:,.0f}")
            print(f"Total Liabilities: ${balance['total_liabilities']:,.0f}")
            print(f"Stockholders' Equity: ${balance['total_stockholders_equity']:,.0f}")
            print(f"Cash & Equivalents: ${balance['cash_and_cash_equivalents']:,.0f}")
            print(f"Total Debt: ${balance['total_debt']:,.0f}")
        
        # Cash Flow
        cashflow = self.db.execute_query("""
            SELECT date, operating_cash_flow, free_cash_flow, capital_expenditure
            FROM cash_flow_statements 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if cashflow:
            print(f"\n💸 Cash Flow Statement ({cashflow['date']})")
            print(f"Operating Cash Flow: ${cashflow['operating_cash_flow']:,.0f}")
            print(f"Free Cash Flow: ${cashflow['free_cash_flow']:,.0f}")
            print(f"Capital Expenditure: ${cashflow['capital_expenditure']:,.0f}")
    
    def show_historical_performance(self):
        """Show historical price performance"""
        print("\n📈 HISTORICAL PERFORMANCE")
        print("=" * 60)
        
        # Get recent price data
        prices = self.db.execute_query("""
            SELECT date, `close`, volume
            FROM historical_prices_daily 
            WHERE symbol = %s
            ORDER BY date DESC LIMIT 10
        """, (self.symbol,), fetch='all')
        
        if prices:
            print("Recent Trading Days:")
            print("Date\t\tClose\t\tVolume")
            print("-" * 50)
            for price in prices:
                print(f"{price['date']}\t${price['close']:.2f}\t\t{price['volume']:,}")
        
        # Price statistics
        stats = self.db.execute_query("""
            SELECT 
                COUNT(*) as days_cached,
                MIN(`close`) as min_price,
                MAX(`close`) as max_price,
                AVG(`close`) as avg_price,
                AVG(volume) as avg_volume
            FROM historical_prices_daily 
            WHERE symbol = %s
        """, (self.symbol,), fetch='one')
        
        if stats:
            print(f"\nPrice Statistics ({stats['days_cached']} days cached):")
            print(f"Min Price: ${stats['min_price']:.2f}")
            print(f"Max Price: ${stats['max_price']:.2f}")
            print(f"Avg Price: ${stats['avg_price']:.2f}")
            print(f"Avg Volume: {stats['avg_volume']:,.0f}")
    
    def show_recent_news(self):
        """Show recent news"""
        print("\n📰 RECENT NEWS")
        print("=" * 60)
        
        news = self.db.execute_query("""
            SELECT published_date, title, site, url
            FROM stock_news 
            WHERE symbol = %s
            ORDER BY published_date DESC LIMIT 5
        """, (self.symbol,), fetch='all')
        
        if news:
            for article in news:
                print(f"\n📅 {article['published_date']}")
                print(f"🏢 {article['site']}")
                print(f"📰 {article['title']}")
                print(f"🔗 {article['url']}")
        else:
            print("No news data found")
    
    def show_cache_summary(self):
        """Show comprehensive cache summary"""
        print("\n📊 CACHE SUMMARY")
        print("=" * 60)
        
        tables = [
            'companies', 'company_executives', 'historical_prices_daily', 
            'sp500_constituents', 'api_request_log', 'fetch_sessions', 'fetch_watermarks'
        ]
        
        total_records = 0
        for table in tables:
            try:
                result = self.db.execute_query(
                    f"SELECT COUNT(*) as count FROM {table} WHERE symbol = %s",
                    (self.symbol,), fetch='one'
                )
                count = result['count']
                total_records += count
                print(f"{table.replace('_', ' ').title()}: {count:,} records")
            except Exception as e:
                print(f"{table.replace('_', ' ').title()}: Error - {e}")
        
        print(f"\nTotal Records: {total_records:,}")
        
        # Storage info
        print(f"\nDatabase: {os.getenv('FMP_DB_NAME')} @ {os.getenv('FMP_DB_HOST')}")
        print(f"Symbol: {self.symbol}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function to display Apple cache data"""
    print("🍎 APPLE (AAPL) FUNDAMENTAL DATA CACHE")
    print("=" * 70)
    
    try:
        viewer = AppleCacheViewer()
        
        # Show all sections
        viewer.show_company_profile()
        viewer.show_latest_quote()
        viewer.show_financial_statements()
        viewer.show_historical_performance()
        viewer.show_recent_news()
        viewer.show_cache_summary()
        
        print(f"\n🎉 Complete fundamental data for Apple Inc. ({viewer.symbol}) is cached!")
        print("Your FMP MySQL database is ready for high-performance analysis.")
        
    except Exception as e:
        print(f"❌ Error viewing cache: {e}")

if __name__ == "__main__":
    main()