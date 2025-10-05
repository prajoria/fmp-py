#!/usr/bin/env python3
"""
Tech Giants P/E Ratio Comparison Analysis

This script demonstrates how to compare P/E ratios of major technology companies
using the FMP API. It answers the question: "Which tech giant appears most 
attractively valued based on P/E ratios?"

Companies analyzed: Apple (AAPL), Microsoft (MSFT), Google (GOOGL), Meta (META)
"""

import sys
import os
from datetime import datetime
import pandas as pd

# Add the parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.fmp_client import FMPClient, FMPAPIError
from utils.helpers import format_currency, format_percentage, clean_financial_data
from dotenv import load_dotenv


def analyze_tech_pe_ratios():
    """Comprehensive P/E ratio analysis of major tech companies"""
    
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        print("Please create a .env file with your API key:")
        print("FMP_API_KEY=your_api_key_here")
        return
    
    # Tech giants to analyze
    tech_companies = ['AAPL', 'MSFT', 'GOOGL', 'META']
    
    print("🚀 TECH GIANTS P/E RATIO ANALYSIS")
    print("=" * 50)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Companies: {', '.join(tech_companies)}")
    print()
    
    try:
        # Initialize client
        client = FMPClient(api_key)
        
        # Validate API key
        if not client.validate_api_key():
            print("❌ Invalid API key")
            return
        
        print("✅ API key validated successfully\n")
        
        # Get quotes for all companies
        print("📊 FETCHING REAL-TIME DATA")
        print("-" * 30)
        
        quotes = client.get_quotes(tech_companies)
        if not quotes:
            print("❌ Could not retrieve quotes")
            return
        
        # Organize data for analysis
        analysis_data = []
        
        for quote in quotes:
            symbol = quote['symbol']
            current_price = quote['price']
            pe_ratio = quote.get('pe', 0)
            market_cap = quote.get('marketCap', 0)
            eps = quote.get('eps', 0)
            daily_change_pct = quote.get('changesPercentage', 0)
            
            analysis_data.append({
                'Symbol': symbol,
                'Company': get_company_name(symbol),
                'Price': current_price,
                'P/E Ratio': pe_ratio,
                'Market Cap': market_cap,
                'EPS': eps,
                'Daily Change %': daily_change_pct
            })
            
            print(f"✅ {symbol}: P/E = {pe_ratio:.2f}, Price = {format_currency(current_price)}")
        
        # Create DataFrame for analysis
        df = pd.DataFrame(analysis_data)
        df = df.sort_values('P/E Ratio')
        
        print("\n📈 DETAILED P/E RATIO COMPARISON")
        print("-" * 40)
        
        # Display comprehensive table
        print("\n📊 Current Valuation Metrics:")
        print("=" * 80)
        
        for _, row in df.iterrows():
            symbol = row['Symbol']
            company = row['Company']
            price = row['Price']
            pe_ratio = row['P/E Ratio']
            market_cap = row['Market Cap']
            eps = row['EPS']
            daily_change = row['Daily Change %']
            
            print(f"\n🏢 {company} ({symbol})")
            print(f"   Current Price: {format_currency(price)}")
            print(f"   P/E Ratio: {pe_ratio:.2f}")
            print(f"   Market Cap: {format_currency(market_cap)}")
            print(f"   EPS (TTM): {format_currency(eps)}")
            print(f"   Daily Change: {format_percentage(daily_change/100)}")
        
        print("\n" + "=" * 80)
        
        # Valuation Analysis
        print("\n💰 VALUATION ANALYSIS")
        print("-" * 25)
        
        # Filter out companies with invalid P/E ratios
        valid_pe_df = df[df['P/E Ratio'] > 0]
        
        if len(valid_pe_df) == 0:
            print("❌ No companies with valid P/E ratios found")
            return
        
        # Find most and least attractive valuations
        most_attractive = valid_pe_df.iloc[0]  # Lowest P/E
        least_attractive = valid_pe_df.iloc[-1]  # Highest P/E
        
        print(f"🟢 MOST ATTRACTIVE VALUATION:")
        print(f"   {most_attractive['Company']} ({most_attractive['Symbol']})")
        print(f"   P/E Ratio: {most_attractive['P/E Ratio']:.2f}")
        print(f"   Price: {format_currency(most_attractive['Price'])}")
        
        print(f"\n🔴 LEAST ATTRACTIVE VALUATION:")
        print(f"   {least_attractive['Company']} ({least_attractive['Symbol']})")
        print(f"   P/E Ratio: {least_attractive['P/E Ratio']:.2f}")
        print(f"   Price: {format_currency(least_attractive['Price'])}")
        
        # Statistical analysis
        avg_pe = valid_pe_df['P/E Ratio'].mean()
        median_pe = valid_pe_df['P/E Ratio'].median()
        pe_range = valid_pe_df['P/E Ratio'].max() - valid_pe_df['P/E Ratio'].min()
        
        print(f"\n📊 P/E RATIO STATISTICS:")
        print(f"   Average P/E: {avg_pe:.2f}")
        print(f"   Median P/E: {median_pe:.2f}")
        print(f"   P/E Range: {pe_range:.2f}")
        
        # Relative valuation assessment
        print(f"\n🎯 RELATIVE VALUATION ASSESSMENT:")
        print("-" * 35)
        
        for _, row in valid_pe_df.iterrows():
            symbol = row['Symbol']
            company = row['Company']
            pe_ratio = row['P/E Ratio']
            
            if pe_ratio < avg_pe * 0.9:
                assessment = "🟢 UNDERVALUED (vs peers)"
            elif pe_ratio > avg_pe * 1.1:
                assessment = "🔴 OVERVALUED (vs peers)"
            else:
                assessment = "🟡 FAIRLY VALUED (vs peers)"
            
            print(f"   {symbol}: P/E {pe_ratio:.2f} - {assessment}")
        
        # Get additional fundamental data for context
        print(f"\n📋 FUNDAMENTAL CONTEXT")
        print("-" * 25)
        
        for symbol in tech_companies:
            try:
                # Get financial ratios for additional context
                ratios = client.get_financial_ratios(symbol, limit=1)
                if ratios and ratios[0]:
                    ratio_data = ratios[0]
                    roe = ratio_data.get('returnOnEquity', 0)
                    profit_margin = ratio_data.get('netProfitMargin', 0)
                    
                    print(f"\n🏢 {symbol} - Additional Metrics:")
                    print(f"   ROE: {format_percentage(roe)}")
                    print(f"   Net Profit Margin: {format_percentage(profit_margin)}")
                    
            except Exception as e:
                print(f"   {symbol}: Additional data not available")
        
        # Investment recommendation
        print(f"\n💡 INVESTMENT RECOMMENDATION")
        print("-" * 30)
        
        best_value = most_attractive['Symbol']
        best_pe = most_attractive['P/E Ratio']
        
        print(f"Based on P/E ratio analysis:")
        print(f"🎯 BEST VALUE: {most_attractive['Company']} ({best_value})")
        print(f"   P/E Ratio: {best_pe:.2f}")
        print(f"   Reasoning:")
        print(f"   • Lowest P/E ratio among tech giants")
        print(f"   • {(avg_pe - best_pe):.1f} points below peer average")
        print(f"   • Potentially undervalued relative to growth prospects")
        
        # Risk considerations
        print(f"\n⚠️ IMPORTANT CONSIDERATIONS:")
        print("   • P/E ratios are just one valuation metric")
        print("   • Consider growth rates, profitability, and business quality")
        print("   • Market conditions and future prospects matter")
        print("   • Diversification across multiple stocks recommended")
        
        print(f"\n🔍 NEXT STEPS FOR ANALYSIS:")
        print("   1. Compare PEG ratios (P/E to growth)")
        print("   2. Analyze revenue and earnings growth trends")
        print("   3. Review business segment performance")
        print("   4. Assess competitive positioning")
        print("   5. Consider forward P/E ratios")
        
        print("\n" + "=" * 50)
        print("✅ P/E Ratio Analysis Complete!")
        print("📊 Remember: This is educational analysis only.")
        print("💡 Always consult financial advisors for investment decisions.")
        
    except FMPAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def get_company_name(symbol):
    """Get full company name from symbol"""
    company_names = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc. (Google)',
        'META': 'Meta Platforms Inc.'
    }
    return company_names.get(symbol, symbol)


if __name__ == "__main__":
    analyze_tech_pe_ratios()