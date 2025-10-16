#!/usr/bin/env python3
"""
Apple Data Analytics
====================
Demonstrate analytics capabilities using cached Apple data
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

# Use relative imports
from ...StockAnalysis.database.connection import get_db

class AppleAnalytics:
    """Analytics for Apple cached data"""
    
    def __init__(self):
        self.db = get_db()
        self.symbol = "AAPL"
    
    def revenue_growth_analysis(self):
        """Analyze revenue growth over years"""
        print("\n📈 REVENUE GROWTH ANALYSIS")
        print("=" * 60)
        
        revenues = self.db.execute_query("""
            SELECT calendar_year, revenue
            FROM income_statements 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY calendar_year DESC LIMIT 5
        """, (self.symbol,), fetch='all')
        
        if revenues and len(revenues) >= 2:
            print("Year\t\tRevenue\t\t\tGrowth")
            print("-" * 50)
            
            prev_revenue = None
            for i, year_data in enumerate(revenues):
                year = year_data['calendar_year']
                revenue = year_data['revenue']
                
                if prev_revenue and revenue:
                    growth = ((revenue - prev_revenue) / prev_revenue) * 100
                    print(f"{year}\t\t${revenue:,.0f}\t\t{growth:+.1f}%")
                else:
                    print(f"{year}\t\t${revenue:,.0f}\t\t--")
                
                prev_revenue = revenue
    
    def profitability_metrics(self):
        """Calculate profitability metrics"""
        print("\n💰 PROFITABILITY METRICS")
        print("=" * 60)
        
        latest = self.db.execute_query("""
            SELECT date, revenue, gross_profit, operating_income, net_income
            FROM income_statements 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if latest:
            revenue = latest['revenue']
            gross_profit = latest['gross_profit']
            operating_income = latest['operating_income']
            net_income = latest['net_income']
            
            if revenue and revenue > 0:
                gross_margin = (gross_profit / revenue) * 100
                operating_margin = (operating_income / revenue) * 100
                net_margin = (net_income / revenue) * 100
                
                print(f"Period: {latest['date']}")
                print(f"Revenue: ${revenue:,.0f}")
                print(f"Gross Margin: {gross_margin:.1f}%")
                print(f"Operating Margin: {operating_margin:.1f}%")
                print(f"Net Margin: {net_margin:.1f}%")
    
    def financial_strength(self):
        """Analyze financial strength"""
        print("\n💪 FINANCIAL STRENGTH")
        print("=" * 60)
        
        balance = self.db.execute_query("""
            SELECT date, total_assets, total_liabilities, total_stockholders_equity,
                   cash_and_cash_equivalents, total_debt
            FROM balance_sheets 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if balance:
            assets = balance['total_assets']
            liabilities = balance['total_liabilities']
            equity = balance['total_stockholders_equity']
            cash = balance['cash_and_cash_equivalents']
            debt = balance['total_debt']
            
            if assets and liabilities:
                debt_to_assets = (debt / assets) * 100 if debt else 0
                equity_ratio = (equity / assets) * 100 if equity else 0
                
                print(f"Period: {balance['date']}")
                print(f"Total Assets: ${assets:,.0f}")
                print(f"Cash & Equivalents: ${cash:,.0f}")
                print(f"Total Debt: ${debt:,.0f}")
                print(f"Debt-to-Assets: {debt_to_assets:.1f}%")
                print(f"Equity Ratio: {equity_ratio:.1f}%")
                print(f"Net Cash: ${cash - debt:,.0f}" if cash and debt else "Net Cash: N/A")
    
    def cash_flow_analysis(self):
        """Analyze cash flow"""
        print("\n💸 CASH FLOW ANALYSIS")
        print("=" * 60)
        
        cash_flows = self.db.execute_query("""
            SELECT calendar_year, operating_cash_flow, free_cash_flow, capital_expenditure
            FROM cash_flow_statements 
            WHERE symbol = %s AND period = 'FY'
            ORDER BY calendar_year DESC LIMIT 3
        """, (self.symbol,), fetch='all')
        
        if cash_flows:
            print("Year\t\tOp. Cash Flow\t\tFree Cash Flow\t\tCapEx")
            print("-" * 70)
            
            for cf in cash_flows:
                year = cf['calendar_year']
                ocf = cf['operating_cash_flow']
                fcf = cf['free_cash_flow']
                capex = cf['capital_expenditure']
                
                print(f"{year}\t\t${ocf:,.0f}\t\t${fcf:,.0f}\t\t${capex:,.0f}")
    
    def price_performance(self):
        """Analyze price performance"""
        print("\n📊 PRICE PERFORMANCE")
        print("=" * 60)
        
        # Get price stats for different periods
        periods = [
            ("1 Month", 30),
            ("3 Months", 90),
            ("6 Months", 180),
            ("1 Year", 365)
        ]
        
        current_price = self.db.execute_query("""
            SELECT `close` FROM historical_prices_daily 
            WHERE symbol = %s
            ORDER BY date DESC LIMIT 1
        """, (self.symbol,), fetch='one')
        
        if current_price:
            current = current_price['close']
            
            print("Period\t\tStart Price\tCurrent Price\tReturn")
            print("-" * 55)
            
            for period_name, days in periods:
                start_price = self.db.execute_query("""
                    SELECT `close` FROM historical_prices_daily 
                    WHERE symbol = %s AND date <= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                    ORDER BY date DESC LIMIT 1
                """, (self.symbol, days), fetch='one')
                
                if start_price:
                    start = start_price['close']
                    returns = ((current - start) / start) * 100
                    print(f"{period_name}\t\t${start:.2f}\t\t${current:.2f}\t\t{returns:+.1f}%")
    
    def news_sentiment_summary(self):
        """Summarize recent news"""
        print("\n📰 NEWS SUMMARY")
        print("=" * 60)
        
        news_count = self.db.execute_query("""
            SELECT COUNT(*) as total_articles,
                   COUNT(DISTINCT site) as sources,
                   MAX(published_date) as latest_news
            FROM stock_news 
            WHERE symbol = %s
        """, (self.symbol,), fetch='one')
        
        if news_count:
            print(f"Total Articles Cached: {news_count['total_articles']}")
            print(f"News Sources: {news_count['sources']}")
            print(f"Latest Article: {news_count['latest_news']}")
        
        # Top news sources
        top_sources = self.db.execute_query("""
            SELECT site, COUNT(*) as article_count
            FROM stock_news 
            WHERE symbol = %s
            GROUP BY site
            ORDER BY article_count DESC LIMIT 5
        """, (self.symbol,), fetch='all')
        
        if top_sources:
            print("\nTop News Sources:")
            for source in top_sources:
                print(f"  {source['site']}: {source['article_count']} articles")

def main():
    """Main analytics function"""
    print("🍎 APPLE (AAPL) FUNDAMENTAL ANALYTICS")
    print("Using Cached FMP Data")
    print("=" * 70)
    
    try:
        analytics = AppleAnalytics()
        
        # Run all analytics
        analytics.revenue_growth_analysis()
        analytics.profitability_metrics()
        analytics.financial_strength()
        analytics.cash_flow_analysis()
        analytics.price_performance()
        analytics.news_sentiment_summary()
        
        print(f"\n🎉 Analytics complete! All data served from MySQL cache.")
        print("This demonstrates the power of caching FMP data for instant analysis.")
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()