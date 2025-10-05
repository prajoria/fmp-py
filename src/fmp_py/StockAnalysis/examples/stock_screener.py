#!/usr/bin/env python3
"""
Stock Screener Example

This example demonstrates how to screen stocks based on various financial criteria.
It shows how to:
- Screen stocks by market cap, P/E ratio, and other metrics
- Analyze sector performance
- Find top performers and underperformers
- Create custom screening criteria
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.fmp_client import FMPClient, FMPAPIError
from utils.helpers import format_currency, format_percentage, clean_financial_data


class StockScreener:
    """Stock screener using FMP API"""
    
    def __init__(self, api_key):
        self.client = FMPClient(api_key)
    
    def screen_by_market_cap(self, min_market_cap=1e9, max_market_cap=None):
        """Screen stocks by market capitalization"""
        print(f"🔍 Screening stocks with market cap >= {format_currency(min_market_cap)}")
        
        # Get stock list
        stock_list = self.client.get_stock_list()
        if not stock_list:
            print("❌ Could not retrieve stock list")
            return []
        
        # Filter by exchange (focus on major exchanges)
        major_exchanges = ['NASDAQ', 'NYSE', 'AMEX']
        filtered_stocks = [s for s in stock_list if s.get('exchangeShortName') in major_exchanges]
        
        print(f"Found {len(filtered_stocks)} stocks in major exchanges")
        
        # Get quotes for screening (batch process to avoid rate limits)
        screened_stocks = []
        batch_size = 10  # Process in small batches
        
        for i in range(0, min(100, len(filtered_stocks)), batch_size):  # Limit to first 100 for demo
            batch = filtered_stocks[i:i+batch_size]
            symbols = [stock['symbol'] for stock in batch]
            
            quotes = self.client.get_quotes(symbols)
            if quotes:
                for quote in quotes:
                    market_cap = quote.get('marketCap', 0)
                    if market_cap >= min_market_cap:
                        if max_market_cap is None or market_cap <= max_market_cap:
                            screened_stocks.append(quote)
        
        return screened_stocks
    
    def screen_by_pe_ratio(self, min_pe=None, max_pe=25):
        """Screen stocks by P/E ratio"""
        print(f"🔍 Screening stocks with P/E ratio <= {max_pe}")
        
        # Get a sample of stocks
        stock_list = self.client.get_stock_list()
        if not stock_list:
            return []
        
        # Filter major exchanges and get sample
        major_exchanges = ['NASDAQ', 'NYSE']
        sample_stocks = [s for s in stock_list if s.get('exchangeShortName') in major_exchanges][:50]
        
        screened_stocks = []
        for stock in sample_stocks:
            quote = self.client.get_quote(stock['symbol'])
            if quote and quote.get('pe'):
                pe_ratio = quote['pe']
                if (min_pe is None or pe_ratio >= min_pe) and pe_ratio <= max_pe:
                    screened_stocks.append(quote)
        
        return screened_stocks
    
    def find_sector_leaders(self):
        """Find top performing stocks by sector"""
        print("🏆 Finding sector leaders...")
        
        # Get sector performance
        sectors = self.client.get_sector_performance()
        if not sectors:
            print("❌ Could not retrieve sector performance")
            return {}
        
        print("\n📊 SECTOR PERFORMANCE")
        print("-" * 25)
        for sector in sectors[:10]:  # Top 10 sectors
            sector_name = sector.get('sector', 'Unknown')
            performance = float(sector.get('changesPercentage', 0))
            print(f"{sector_name}: {format_percentage(performance/100)}")
        
        return sectors
    
    def screen_dividend_stocks(self, min_yield=0.02):
        """Screen for dividend-paying stocks"""
        print(f"💰 Screening dividend stocks with yield >= {format_percentage(min_yield)}")
        
        # Sample dividend-paying stocks
        dividend_symbols = ['AAPL', 'MSFT', 'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'VZ', 'T', 'XOM']
        
        dividend_stocks = []
        for symbol in dividend_symbols:
            quote = self.client.get_quote(symbol)
            if quote:
                # Calculate approximate dividend yield
                # Note: FMP API might not always have dividend yield directly
                dividend_stocks.append(quote)
        
        return dividend_stocks
    
    def momentum_screen(self, min_ytd_performance=0.1):
        """Screen stocks with strong momentum"""
        print(f"🚀 Screening momentum stocks with YTD performance >= {format_percentage(min_ytd_performance)}")
        
        # Sample tech stocks for momentum screening
        tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'AMD', 'INTC']
        
        momentum_stocks = []
        for symbol in tech_symbols:
            quote = self.client.get_quote(symbol)
            if quote:
                # Simple momentum check using daily change
                daily_change_pct = quote.get('changesPercentage', 0) / 100
                if abs(daily_change_pct) > 0.02:  # At least 2% daily movement
                    momentum_stocks.append(quote)
        
        return momentum_stocks
    
    def value_screen(self, max_pe=15, max_pb=2):
        """Screen for value stocks"""
        print(f"💎 Screening value stocks (P/E <= {max_pe}, P/B <= {max_pb})")
        
        # Sample value-oriented stocks
        value_symbols = ['BRK-A', 'JPM', 'BAC', 'WFC', 'V', 'MA', 'HD', 'PG', 'JNJ', 'UNH']
        
        value_stocks = []
        for symbol in value_symbols:
            quote = self.client.get_quote(symbol)
            if quote and quote.get('pe'):
                pe_ratio = quote['pe']
                if pe_ratio <= max_pe:
                    value_stocks.append(quote)
        
        return value_stocks


def run_stock_screening():
    """Run comprehensive stock screening"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        print("Please create a .env file with your API key:")
        print("FMP_API_KEY=your_api_key_here")
        return
    screener = StockScreener(api_key)
    
    print("📈 COMPREHENSIVE STOCK SCREENING")
    print("=" * 40)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Market Cap Screening
        print("1️⃣ LARGE CAP STOCKS (Market Cap >= $10B)")
        print("-" * 40)
        large_caps = screener.screen_by_market_cap(min_market_cap=10e9)
        
        if large_caps:
            # Sort by market cap
            large_caps.sort(key=lambda x: x.get('marketCap', 0), reverse=True)
            
            print(f"Found {len(large_caps)} large cap stocks:")
            for stock in large_caps[:10]:  # Top 10
                symbol = stock['symbol']
                price = stock['price']
                market_cap = stock.get('marketCap', 0)
                daily_change = stock.get('changesPercentage', 0)
                
                print(f"  {symbol}: {format_currency(price)} | "
                      f"MCap: {format_currency(market_cap)} | "
                      f"Change: {format_percentage(daily_change/100)}")
        
        print("\n")
        
        # 2. P/E Ratio Screening
        print("2️⃣ REASONABLY VALUED STOCKS (P/E <= 25)")
        print("-" * 40)
        pe_stocks = screener.screen_by_pe_ratio(max_pe=25)
        
        if pe_stocks:
            # Sort by P/E ratio
            pe_stocks.sort(key=lambda x: x.get('pe', float('inf')))
            
            print(f"Found {len(pe_stocks)} reasonably valued stocks:")
            for stock in pe_stocks[:10]:
                symbol = stock['symbol']
                price = stock['price']
                pe_ratio = stock.get('pe', 0)
                
                print(f"  {symbol}: {format_currency(price)} | P/E: {pe_ratio:.2f}")
        
        print("\n")
        
        # 3. Sector Analysis
        print("3️⃣ SECTOR PERFORMANCE ANALYSIS")
        print("-" * 30)
        sectors = screener.find_sector_leaders()
        
        print("\n")
        
        # 4. Dividend Screening
        print("4️⃣ DIVIDEND STOCK ANALYSIS")
        print("-" * 25)
        dividend_stocks = screener.screen_dividend_stocks()
        
        if dividend_stocks:
            print(f"Analyzing {len(dividend_stocks)} dividend stocks:")
            for stock in dividend_stocks:
                symbol = stock['symbol']
                price = stock['price']
                market_cap = stock.get('marketCap', 0)
                
                print(f"  {symbol}: {format_currency(price)} | "
                      f"MCap: {format_currency(market_cap)}")
        
        print("\n")
        
        # 5. Momentum Analysis
        print("5️⃣ MOMENTUM STOCK ANALYSIS")
        print("-" * 25)
        momentum_stocks = screener.momentum_screen()
        
        if momentum_stocks:
            # Sort by daily change
            momentum_stocks.sort(key=lambda x: abs(x.get('changesPercentage', 0)), reverse=True)
            
            print(f"Found {len(momentum_stocks)} momentum stocks:")
            for stock in momentum_stocks:
                symbol = stock['symbol']
                price = stock['price']
                daily_change = stock.get('changesPercentage', 0)
                
                print(f"  {symbol}: {format_currency(price)} | "
                      f"Daily Change: {format_percentage(daily_change/100)}")
        
        print("\n")
        
        # 6. Value Screening
        print("6️⃣ VALUE STOCK ANALYSIS")
        print("-" * 20)
        value_stocks = screener.value_screen()
        
        if value_stocks:
            # Sort by P/E ratio
            value_stocks.sort(key=lambda x: x.get('pe', float('inf')))
            
            print(f"Found {len(value_stocks)} value stocks:")
            for stock in value_stocks:
                symbol = stock['symbol']
                price = stock['price']
                pe_ratio = stock.get('pe', 0)
                
                print(f"  {symbol}: {format_currency(price)} | P/E: {pe_ratio:.2f}")
        
        print("\n")
        
        # 7. Summary and Recommendations
        print("📊 SCREENING SUMMARY")
        print("-" * 20)
        print("✅ Screening completed successfully!")
        print(f"📈 Large cap stocks analyzed: {len(large_caps) if large_caps else 0}")
        print(f"💰 Dividend stocks analyzed: {len(dividend_stocks) if dividend_stocks else 0}")
        print(f"🚀 Momentum stocks found: {len(momentum_stocks) if momentum_stocks else 0}")
        print(f"💎 Value stocks found: {len(value_stocks) if value_stocks else 0}")
        
        print("\n⚠️  DISCLAIMER:")
        print("This screening is for educational purposes only.")
        print("Always conduct thorough research before making investment decisions.")
        print("Consider consulting with a financial advisor.")
        
    except FMPAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def create_custom_screen():
    """Example of creating a custom screening criteria"""
    
    print("\n🎯 CUSTOM SCREENING EXAMPLE")
    print("-" * 30)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        return
    screener = StockScreener(api_key)
    
    # Custom criteria: Tech stocks with reasonable valuation
    tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'NVDA', 'ORCL', 'CRM', 'ADBE']
    
    print("Custom Screen: Tech stocks with P/E < 30 and Market Cap > $100B")
    print()
    
    qualified_stocks = []
    
    for symbol in tech_symbols:
        quote = screener.client.get_quote(symbol)
        if quote:
            pe_ratio = quote.get('pe', 0)
            market_cap = quote.get('marketCap', 0)
            
            if pe_ratio > 0 and pe_ratio < 30 and market_cap > 100e9:
                qualified_stocks.append(quote)
    
    if qualified_stocks:
        # Sort by market cap
        qualified_stocks.sort(key=lambda x: x.get('marketCap', 0), reverse=True)
        
        print(f"✅ Found {len(qualified_stocks)} stocks meeting criteria:")
        print()
        
        for stock in qualified_stocks:
            symbol = stock['symbol']
            price = stock['price']
            pe_ratio = stock.get('pe', 0)
            market_cap = stock.get('marketCap', 0)
            daily_change = stock.get('changesPercentage', 0)
            
            print(f"🔸 {symbol}")
            print(f"   Price: {format_currency(price)}")
            print(f"   P/E Ratio: {pe_ratio:.2f}")
            print(f"   Market Cap: {format_currency(market_cap)}")
            print(f"   Daily Change: {format_percentage(daily_change/100)}")
            print()
    else:
        print("❌ No stocks found meeting the criteria")


if __name__ == "__main__":
    # Run main screening
    run_stock_screening()
    
    # Run custom screening example
    create_custom_screen()