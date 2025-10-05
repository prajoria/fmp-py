#!/usr/bin/env python3
"""
Apple (AAPL) Stock Analysis Example

This example demonstrates comprehensive stock analysis using the FMP API client.
It covers:
- Real-time quote data
- Company profile and fundamentals
- Historical price analysis
- Financial statement analysis
- Performance metrics and ratios
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Add the parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.fmp_client import FMPClient, FMPAPIError
from utils.helpers import (
    format_currency, format_percentage, calculate_ytd_performance,
    calculate_returns, calculate_volatility, clean_financial_data
)
from utils.config import Config


def analyze_apple_stock():
    """Comprehensive analysis of Apple (AAPL) stock"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configuration
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        print("Please create a .env file with your API key:")
        print("FMP_API_KEY=your_api_key_here")
        return
    
    symbol = "AAPL"
    
    print("🍎 Apple (AAPL) Stock Analysis")
    print("=" * 50)
    
    try:
        # Initialize client
        client = FMPClient(api_key)
        
        # Validate API key
        if not client.validate_api_key():
            print("❌ Invalid API key")
            return
        
        print("✅ API key validated successfully\n")
        
        # 1. Current Quote Analysis
        print("📈 CURRENT QUOTE ANALYSIS")
        print("-" * 30)
        
        quote = client.get_quote(symbol)
        if quote:
            current_price = quote['price']
            daily_change = quote['change']
            daily_change_pct = quote['changesPercentage']
            
            print(f"Current Price: {format_currency(current_price)}")
            print(f"Daily Change: {format_currency(daily_change)} ({format_percentage(daily_change_pct/100)})")
            print(f"Day Range: {format_currency(quote['dayLow'])} - {format_currency(quote['dayHigh'])}")
            print(f"52-Week Range: {format_currency(quote['yearLow'])} - {format_currency(quote['yearHigh'])}")
            print(f"Market Cap: {format_currency(quote['marketCap'])}")
            print(f"Volume: {quote['volume']:,}")
            print(f"Avg Volume: {quote['avgVolume']:,}")
            print(f"P/E Ratio: {quote['pe']:.2f}")
            print(f"EPS: {format_currency(quote['eps'])}")
            
            # Calculate YTD performance
            ytd_start_price = 243.85  # Jan 2, 2025 close
            ytd_performance = calculate_ytd_performance(current_price, ytd_start_price)
            print(f"YTD Performance: {format_percentage(ytd_performance)}")
            
            # Distance from 52-week high/low
            high_distance = (current_price - quote['yearHigh']) / quote['yearHigh']
            low_distance = (current_price - quote['yearLow']) / quote['yearLow']
            print(f"Distance from 52W High: {format_percentage(high_distance)}")
            print(f"Distance from 52W Low: {format_percentage(low_distance)}")
            
        print("\n")
        
        # 2. Company Profile Analysis
        print("🏢 COMPANY PROFILE")
        print("-" * 20)
        
        profile = client.get_company_profile(symbol)
        if profile and profile[0]:
            p = profile[0]
            print(f"Company: {p['companyName']}")
            print(f"Industry: {p['industry']}")
            print(f"Sector: {p['sector']}")
            print(f"Country: {p['country']}")
            print(f"Exchange: {p['exchangeShortName']}")
            
            if isinstance(p.get('fullTimeEmployees'), (int, float)):
                print(f"Employees: {p['fullTimeEmployees']:,}")
            else:
                print(f"Employees: {p.get('fullTimeEmployees', 'N/A')}")
            
            print(f"Website: {p['website']}")
            print(f"CEO: {p.get('ceo', 'N/A')}")
            print(f"Founded: {p.get('ipoDate', 'N/A')}")
            print(f"\nDescription: {p['description'][:300]}...")
        
        print("\n")
        
        # 3. Historical Price Analysis
        print("📊 HISTORICAL PRICE ANALYSIS (Last 30 Days)")
        print("-" * 45)
        
        # Get 30 days of data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        historical = client.get_historical_prices(symbol, start_date, end_date)
        if historical and 'historical' in historical:
            df = pd.DataFrame(historical['historical'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Calculate returns
            prices = df['close'].tolist()
            returns = calculate_returns(prices)
            volatility = calculate_volatility(returns, annualize=False)
            
            print(f"Number of trading days: {len(df)}")
            print(f"Starting price: {format_currency(df['close'].iloc[0])}")
            print(f"Ending price: {format_currency(df['close'].iloc[-1])}")
            
            period_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]
            print(f"30-day return: {format_percentage(period_return)}")
            print(f"Average daily volume: {df['volume'].mean():,.0f}")
            print(f"30-day volatility: {format_percentage(volatility)}")
            
            # High/low analysis
            period_high = df['high'].max()
            period_low = df['low'].min()
            print(f"30-day high: {format_currency(period_high)}")
            print(f"30-day low: {format_currency(period_low)}")
            
        print("\n")
        
        # 4. Financial Statements Analysis
        print("💰 FINANCIAL STATEMENTS (Latest Annual)")
        print("-" * 40)
        
        # Income Statement
        income = client.get_income_statement(symbol, limit=1)
        if income and income[0]:
            inc = income[0]
            print("INCOME STATEMENT:")
            print(f"  Revenue: {format_currency(inc.get('revenue', 0))}")
            print(f"  Gross Profit: {format_currency(inc.get('grossProfit', 0))}")
            print(f"  Operating Income: {format_currency(inc.get('operatingIncome', 0))}")
            print(f"  Net Income: {format_currency(inc.get('netIncome', 0))}")
            print(f"  EPS: {format_currency(inc.get('eps', 0))}")
            
            # Margins
            if inc.get('revenue', 0) > 0:
                gross_margin = inc.get('grossProfit', 0) / inc['revenue']
                operating_margin = inc.get('operatingIncome', 0) / inc['revenue']
                net_margin = inc.get('netIncome', 0) / inc['revenue']
                
                print(f"  Gross Margin: {format_percentage(gross_margin)}")
                print(f"  Operating Margin: {format_percentage(operating_margin)}")
                print(f"  Net Margin: {format_percentage(net_margin)}")
        
        # Balance Sheet
        balance = client.get_balance_sheet(symbol, limit=1)
        if balance and balance[0]:
            bal = balance[0]
            print("\nBALANCE SHEET:")
            print(f"  Total Assets: {format_currency(bal.get('totalAssets', 0))}")
            print(f"  Total Debt: {format_currency(bal.get('totalDebt', 0))}")
            print(f"  Total Equity: {format_currency(bal.get('totalStockholdersEquity', 0))}")
            print(f"  Cash: {format_currency(bal.get('cashAndCashEquivalents', 0))}")
            
            # Ratios
            if bal.get('totalAssets', 0) > 0:
                debt_to_assets = bal.get('totalDebt', 0) / bal['totalAssets']
                print(f"  Debt-to-Assets: {format_percentage(debt_to_assets)}")
        
        # Cash Flow
        cashflow = client.get_cash_flow_statement(symbol, limit=1)
        if cashflow and cashflow[0]:
            cf = cashflow[0]
            print("\nCASH FLOW:")
            print(f"  Operating Cash Flow: {format_currency(cf.get('netCashProvidedByOperatingActivities', 0))}")
            print(f"  Free Cash Flow: {format_currency(cf.get('freeCashFlow', 0))}")
            print(f"  Capital Expenditures: {format_currency(cf.get('capitalExpenditure', 0))}")
        
        print("\n")
        
        # 5. Financial Ratios
        print("📊 KEY FINANCIAL RATIOS")
        print("-" * 25)
        
        ratios = client.get_financial_ratios(symbol, limit=1)
        if ratios and ratios[0]:
            r = ratios[0]
            print("PROFITABILITY:")
            print(f"  ROE: {format_percentage(r.get('returnOnEquity', 0))}")
            print(f"  ROA: {format_percentage(r.get('returnOnAssets', 0))}")
            print(f"  ROIC: {format_percentage(r.get('returnOnCapitalEmployed', 0))}")
            
            print("\nVALUATION:")
            print(f"  P/E Ratio: {r.get('priceEarningsRatio', 0):.2f}")
            print(f"  P/B Ratio: {r.get('priceToBookRatio', 0):.2f}")
            print(f"  P/S Ratio: {r.get('priceToSalesRatio', 0):.2f}")
            
            print("\nLIQUIDITY:")
            print(f"  Current Ratio: {r.get('currentRatio', 0):.2f}")
            print(f"  Quick Ratio: {r.get('quickRatio', 0):.2f}")
            
            print("\nLEVERAGE:")
            print(f"  Debt-to-Equity: {r.get('debtEquityRatio', 0):.2f}")
            print(f"  Interest Coverage: {r.get('interestCoverageRatio', 0):.2f}")
        
        print("\n")
        
        # 6. Market Context
        print("🌍 MARKET CONTEXT")
        print("-" * 15)
        
        # Compare with tech peers
        tech_stocks = ['MSFT', 'GOOGL', 'META', 'AMZN']
        print("Tech Peer Comparison (P/E Ratios):")
        
        peer_quotes = client.get_quotes([symbol] + tech_stocks)
        if peer_quotes:
            for stock_quote in peer_quotes:
                if stock_quote.get('pe'):
                    print(f"  {stock_quote['symbol']}: {stock_quote['pe']:.2f}")
        
        # Sector performance
        sectors = client.get_sector_performance()
        if sectors:
            tech_sector = next((s for s in sectors if 'Technology' in s.get('sector', '')), None)
            if tech_sector:
                print(f"\nTechnology Sector Performance: {format_percentage(float(tech_sector['changesPercentage'])/100)}")
        
        print("\n")
        
        # 7. Investment Summary
        print("💡 INVESTMENT SUMMARY")
        print("-" * 20)
        
        if quote:
            # Calculate some key metrics
            current_price = quote['price']
            year_high = quote['yearHigh']
            year_low = quote['yearLow']
            
            # Position in 52-week range
            range_position = (current_price - year_low) / (year_high - year_low)
            
            print(f"Current Position in 52-week range: {format_percentage(range_position)}")
            
            # Simple momentum indicators
            if quote['changesPercentage'] > 0:
                print("📈 Positive daily momentum")
            else:
                print("📉 Negative daily momentum")
            
            # Valuation assessment (basic)
            if quote.get('pe'):
                pe_ratio = quote['pe']
                if pe_ratio < 15:
                    valuation = "Potentially undervalued"
                elif pe_ratio > 30:
                    valuation = "Potentially overvalued"
                else:
                    valuation = "Fairly valued"
                print(f"Valuation assessment: {valuation} (P/E: {pe_ratio:.2f})")
            
            # YTD performance assessment
            if ytd_performance > 0.10:
                ytd_assessment = "Strong YTD performance"
            elif ytd_performance > 0:
                ytd_assessment = "Positive YTD performance"
            else:
                ytd_assessment = "Negative YTD performance"
            print(f"YTD Assessment: {ytd_assessment}")
        
        print("\n" + "=" * 50)
        print("✅ Analysis completed successfully!")
        print("📊 This analysis is for educational purposes only.")
        print("💡 Always consult with a financial advisor for investment decisions.")
        
    except FMPAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    analyze_apple_stock()