#!/usr/bin/env python3
"""
Portfolio Analysis Example

This example demonstrates how to analyze a stock portfolio using the FMP API.
It covers:
- Portfolio performance calculation
- Risk assessment and diversification analysis
- Asset allocation breakdown
- Individual stock performance within portfolio
- Correlation analysis between holdings
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Add the parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.fmp_client import FMPClient, FMPAPIError
from utils.helpers import (
    format_currency, format_percentage, calculate_returns,
    calculate_volatility, calculate_sharpe_ratio, calculate_beta
)


class PortfolioAnalyzer:
    """Portfolio analysis using FMP API"""
    
    def __init__(self, api_key: str):
        self.client = FMPClient(api_key)
        self.portfolio = {}
        self.portfolio_value = 0
        self.performance_data = {}
    
    def add_holding(self, symbol: str, shares: float, purchase_price: float = None):
        """Add a stock holding to the portfolio"""
        current_quote = self.client.get_quote(symbol)
        if current_quote:
            current_price = current_quote['price']
            
            holding = {
                'symbol': symbol,
                'shares': shares,
                'current_price': current_price,
                'purchase_price': purchase_price or current_price,
                'current_value': shares * current_price,
                'cost_basis': shares * (purchase_price or current_price),
                'quote_data': current_quote
            }
            
            self.portfolio[symbol] = holding
            print(f"✅ Added {shares} shares of {symbol} at {format_currency(current_price)}")
        else:
            print(f"❌ Could not add {symbol} - quote not found")
    
    def calculate_portfolio_metrics(self):
        """Calculate overall portfolio metrics"""
        if not self.portfolio:
            print("❌ Portfolio is empty")
            return
        
        # Calculate total values
        total_current_value = sum(holding['current_value'] for holding in self.portfolio.values())
        total_cost_basis = sum(holding['cost_basis'] for holding in self.portfolio.values())
        
        # Calculate overall return
        total_return = (total_current_value - total_cost_basis) / total_cost_basis
        total_gain_loss = total_current_value - total_cost_basis
        
        self.portfolio_value = total_current_value
        
        # Calculate position weights
        for holding in self.portfolio.values():
            holding['weight'] = holding['current_value'] / total_current_value
            holding['return'] = (holding['current_price'] - holding['purchase_price']) / holding['purchase_price']
        
        return {
            'total_value': total_current_value,
            'total_cost': total_cost_basis,
            'total_return': total_return,
            'total_gain_loss': total_gain_loss
        }
    
    def analyze_diversification(self):
        """Analyze portfolio diversification"""
        if not self.portfolio:
            return
        
        print("🎯 DIVERSIFICATION ANALYSIS")
        print("-" * 30)
        
        # Get sector information for each holding
        sector_allocation = {}
        industry_allocation = {}
        
        for symbol, holding in self.portfolio.items():
            profile = self.client.get_company_profile(symbol)
            if profile and profile[0]:
                sector = profile[0].get('sector', 'Unknown')
                industry = profile[0].get('industry', 'Unknown')
                weight = holding['weight']
                
                sector_allocation[sector] = sector_allocation.get(sector, 0) + weight
                industry_allocation[industry] = industry_allocation.get(industry, 0) + weight
        
        # Display sector allocation
        print("Sector Allocation:")
        for sector, weight in sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector}: {format_percentage(weight)}")
        
        print("\nTop Industry Allocations:")
        sorted_industries = sorted(industry_allocation.items(), key=lambda x: x[1], reverse=True)
        for industry, weight in sorted_industries[:5]:
            print(f"  {industry}: {format_percentage(weight)}")
        
        # Concentration risk assessment
        max_position = max(holding['weight'] for holding in self.portfolio.values())
        print(f"\nLargest Position: {format_percentage(max_position)}")
        
        if max_position > 0.3:
            print("⚠️  High concentration risk - largest position > 30%")
        elif max_position > 0.2:
            print("⚡ Moderate concentration risk - largest position > 20%")
        else:
            print("✅ Good diversification - no position > 20%")
    
    def analyze_performance(self, days: int = 30):
        """Analyze portfolio performance over specified period"""
        print(f"\n📊 PERFORMANCE ANALYSIS ({days} days)")
        print("-" * 35)
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        portfolio_returns = []
        individual_performance = {}
        
        for symbol, holding in self.portfolio.items():
            # Get historical data
            historical = self.client.get_historical_prices(symbol, start_date, end_date)
            if historical and 'historical' in historical:
                prices = [day['close'] for day in historical['historical']]
                if len(prices) > 1:
                    returns = calculate_returns(prices)
                    volatility = calculate_volatility(returns, annualize=False)
                    
                    # Weight the returns by portfolio weight
                    weighted_returns = [r * holding['weight'] for r in returns]
                    portfolio_returns.extend(weighted_returns)
                    
                    period_return = (prices[-1] - prices[0]) / prices[0]
                    individual_performance[symbol] = {
                        'period_return': period_return,
                        'volatility': volatility,
                        'weight': holding['weight'],
                        'contribution': period_return * holding['weight']
                    }
        
        # Calculate portfolio-level metrics
        if portfolio_returns:
            portfolio_volatility = np.std(portfolio_returns) if portfolio_returns else 0
            
            print("Individual Stock Performance:")
            sorted_performance = sorted(individual_performance.items(), 
                                      key=lambda x: x[1]['period_return'], reverse=True)
            
            for symbol, perf in sorted_performance:
                print(f"  {symbol}: {format_percentage(perf['period_return'])} "
                      f"(Weight: {format_percentage(perf['weight'])}, "
                      f"Contribution: {format_percentage(perf['contribution'])})")
            
            # Portfolio summary
            total_contribution = sum(perf['contribution'] for perf in individual_performance.values())
            print(f"\nPortfolio {days}-day return: {format_percentage(total_contribution)}")
            print(f"Portfolio volatility: {format_percentage(portfolio_volatility)}")
        
        return individual_performance
    
    def risk_assessment(self):
        """Assess portfolio risk metrics"""
        print("\n⚠️  RISK ASSESSMENT")
        print("-" * 18)
        
        # Beta calculation (using SPY as market benchmark)
        market_symbol = "SPY"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=252)).strftime('%Y-%m-%d')  # 1 year
        
        # Get market data
        market_data = self.client.get_historical_prices(market_symbol, start_date, end_date)
        if not market_data or 'historical' not in market_data:
            print("❌ Could not retrieve market data for beta calculation")
            return
        
        market_prices = [day['close'] for day in market_data['historical']]
        market_returns = calculate_returns(market_prices)
        
        portfolio_betas = []
        risk_metrics = {}
        
        for symbol, holding in self.portfolio.items():
            # Get stock historical data
            stock_data = self.client.get_historical_prices(symbol, start_date, end_date)
            if stock_data and 'historical' in stock_data:
                stock_prices = [day['close'] for day in stock_data['historical']]
                stock_returns = calculate_returns(stock_prices)
                
                # Calculate beta
                if len(stock_returns) == len(market_returns):
                    beta = calculate_beta(stock_returns, market_returns)
                    volatility = calculate_volatility(stock_returns)
                    
                    # Weight by position size
                    weighted_beta = beta * holding['weight']
                    portfolio_betas.append(weighted_beta)
                    
                    risk_metrics[symbol] = {
                        'beta': beta,
                        'volatility': volatility,
                        'weight': holding['weight'],
                        'weighted_beta': weighted_beta
                    }
        
        # Portfolio beta
        portfolio_beta = sum(portfolio_betas)
        
        print("Individual Stock Risk Metrics:")
        for symbol, metrics in risk_metrics.items():
            print(f"  {symbol}: Beta {metrics['beta']:.2f}, "
                  f"Volatility {format_percentage(metrics['volatility'])}")
        
        print(f"\nPortfolio Beta: {portfolio_beta:.2f}")
        
        if portfolio_beta > 1.2:
            risk_level = "High Risk (Beta > 1.2)"
        elif portfolio_beta > 0.8:
            risk_level = "Moderate Risk (0.8 < Beta < 1.2)"
        else:
            risk_level = "Low Risk (Beta < 0.8)"
        
        print(f"Risk Level: {risk_level}")
        
        return risk_metrics
    
    def generate_portfolio_report(self):
        """Generate comprehensive portfolio report"""
        if not self.portfolio:
            print("❌ Cannot generate report - portfolio is empty")
            return
        
        print("📋 COMPREHENSIVE PORTFOLIO REPORT")
        print("=" * 45)
        print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Number of Holdings: {len(self.portfolio)}")
        print()
        
        # 1. Portfolio Overview
        metrics = self.calculate_portfolio_metrics()
        if metrics:
            print("💰 PORTFOLIO OVERVIEW")
            print("-" * 20)
            print(f"Total Portfolio Value: {format_currency(metrics['total_value'])}")
            print(f"Total Cost Basis: {format_currency(metrics['total_cost'])}")
            print(f"Total Gain/Loss: {format_currency(metrics['total_gain_loss'])}")
            print(f"Total Return: {format_percentage(metrics['total_return'])}")
            print()
        
        # 2. Individual Holdings
        print("📊 INDIVIDUAL HOLDINGS")
        print("-" * 22)
        
        # Sort by current value (largest positions first)
        sorted_holdings = sorted(self.portfolio.items(), 
                               key=lambda x: x[1]['current_value'], reverse=True)
        
        for symbol, holding in sorted_holdings:
            print(f"🔸 {symbol}")
            print(f"   Shares: {holding['shares']:,.2f}")
            print(f"   Current Price: {format_currency(holding['current_price'])}")
            print(f"   Purchase Price: {format_currency(holding['purchase_price'])}")
            print(f"   Current Value: {format_currency(holding['current_value'])}")
            print(f"   Cost Basis: {format_currency(holding['cost_basis'])}")
            print(f"   Gain/Loss: {format_currency(holding['current_value'] - holding['cost_basis'])}")
            print(f"   Return: {format_percentage(holding['return'])}")
            print(f"   Weight: {format_percentage(holding['weight'])}")
            print()
        
        # 3. Diversification Analysis
        self.analyze_diversification()
        
        # 4. Performance Analysis
        self.analyze_performance(30)
        
        # 5. Risk Assessment
        self.risk_assessment()
        
        print("\n" + "=" * 45)
        print("✅ Portfolio report completed!")
        print("📊 This analysis is for informational purposes only.")
        print("💡 Consult with a financial advisor for investment guidance.")


def demo_portfolio_analysis():
    """Demonstrate portfolio analysis with sample portfolio"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        print("Please create a .env file with your API key:")
        print("FMP_API_KEY=your_api_key_here")
        return
    analyzer = PortfolioAnalyzer(api_key)
    
    print("🏗️  BUILDING SAMPLE PORTFOLIO")
    print("-" * 30)
    
    # Sample portfolio - diversified holdings
    sample_holdings = [
        ("AAPL", 50, 180.00),    # Apple - Tech
        ("MSFT", 30, 380.00),    # Microsoft - Tech
        ("JNJ", 25, 160.00),     # Johnson & Johnson - Healthcare
        ("WMT", 40, 145.00),     # Walmart - Consumer Staples
        ("JPM", 20, 150.00),     # JPMorgan Chase - Financial
        ("XOM", 35, 110.00),     # Exxon Mobil - Energy
        ("GOOGL", 15, 140.00),   # Google - Tech
        ("PG", 30, 155.00),      # Procter & Gamble - Consumer Goods
    ]
    
    # Add holdings to portfolio
    for symbol, shares, purchase_price in sample_holdings:
        analyzer.add_holding(symbol, shares, purchase_price)
    
    print()
    
    # Generate comprehensive report
    try:
        analyzer.generate_portfolio_report()
    except FMPAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def create_custom_portfolio():
    """Allow user to create custom portfolio"""
    
    print("\n🎯 CREATE CUSTOM PORTFOLIO")
    print("-" * 30)
    print("Enter your holdings (or use demo portfolio):")
    print("Format: SYMBOL SHARES PURCHASE_PRICE")
    print("Example: AAPL 100 150.00")
    print("Type 'done' to finish, 'demo' for sample portfolio")
    print()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ Error: FMP_API_KEY not found in environment variables")
        return
    analyzer = PortfolioAnalyzer(api_key)
    
    # For demo purposes, let's use a predefined portfolio
    print("Using demo portfolio with tech-heavy allocation...")
    
    tech_portfolio = [
        ("AAPL", 100, 175.00),
        ("MSFT", 50, 350.00),
        ("GOOGL", 25, 135.00),
        ("AMZN", 20, 145.00),
        ("META", 30, 350.00),
        ("TSLA", 15, 200.00),
    ]
    
    for symbol, shares, purchase_price in tech_portfolio:
        analyzer.add_holding(symbol, shares, purchase_price)
    
    print("\n📊 Tech Portfolio Analysis:")
    try:
        analyzer.generate_portfolio_report()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run demo portfolio analysis
    demo_portfolio_analysis()
    
    # Create custom portfolio example
    create_custom_portfolio()