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

# Load environment variables
load_dotenv('/home/daaji/masterswork/git/fmp-py/.env')

# Add the StockAnalysis path
sys.path.append('/home/daaji/masterswork/git/fmp-py/src/fmp_py/StockAnalysis')

from database.connection import get_db

class AppleCacheViewer:
    """View Apple data from MySQL cache"""
    
    def __init__(self):
        self.db = get_db()
        self.symbol = "AAPL"
    
    def show_company_profile(self):
        """Show company profile"""
        print("\n🍎 APPLE INC. COMPANY PROFILE")
        print("=" * 60)
        
        profile = self.db.execute_query("""
            SELECT company_name, price, mkt_cap, industry, sector, website, 
                   description, ceo, full_time_employees, country, cached_at
            FROM company_profiles 
            WHERE symbol = %s
        """, (self.symbol,), fetch='one')
        
        if profile:
            print(f"Company: {profile['company_name']}")
            print(f"Current Price: ${profile['price']:,.2f}")
            print(f"Market Cap: ${profile['mkt_cap']:,.0f}")
            print(f"Industry: {profile['industry']}")
            print(f"Sector: {profile['sector']}")
            print(f"CEO: {profile['ceo']}")
            print(f"Employees: {profile['full_time_employees']:,}")
            print(f"Country: {profile['country']}")
            print(f"Website: {profile['website']}")
            print(f"\nDescription: {profile['description'][:200]}...")
            print(f"\nLast Updated: {profile['cached_at']}")
        else:
            print("No profile data found")
    
    def show_latest_quote(self):
        """Show latest quote"""
        print("\n💰 CURRENT QUOTE")
        print("=" * 60)
        
        quote = self.db.execute_query("""
            SELECT price, changes_percentage, `change`, day_low, day_high, 
                   year_high, year_low, market_cap, volume, pe, eps, cached_at
            FROM quotes 
            WHERE symbol = %s
            ORDER BY cached_at DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if quote:
            print(f"Price: ${quote['price']:,.2f}" if quote['price'] else "Price: N/A")
            print(f"Change: ${quote['change']:+,.2f} ({quote['changes_percentage']:+.2f}%)" if quote['change'] and quote['changes_percentage'] else "Change: N/A")
            print(f"Day Range: ${quote['day_low']:,.2f} - ${quote['day_high']:,.2f}" if quote['day_low'] and quote['day_high'] else "Day Range: N/A")
            print(f"52-Week Range: ${quote['year_low']:,.2f} - ${quote['year_high']:,.2f}" if quote['year_low'] and quote['year_high'] else "52-Week Range: N/A")
            print(f"Market Cap: ${quote['market_cap']:,.0f}" if quote['market_cap'] else "Market Cap: N/A")
            print(f"Volume: {quote['volume']:,}" if quote['volume'] else "Volume: N/A")
            print(f"P/E Ratio: {quote['pe']:.2f}" if quote['pe'] else "P/E Ratio: N/A")
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
            'companies', 'company_profiles', 'quotes', 'income_statements',
            'balance_sheets', 'cash_flow_statements', 'financial_ratios',
            'key_metrics', 'historical_prices_daily', 'stock_news'
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